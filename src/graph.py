import os

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from langgraph.graph import StateGraph, END, START

from src.schema import State, RouteDecision, TimeList, DetailsList, CourseTitle
from src.utils import normalize_event_name, clean_subject_key, predefined

try:
    from src.config import API_KEY, API_BASE_URL, MODEL_NAME
except ImportError:
    API_KEY = os.getenv("OPENAI_API_KEY")
    API_BASE_URL = os.getenv("OPENAI_API_BASE", "https://openrouter.ai/api/v1")
    MODEL_NAME = os.getenv("MODEL_NAME", "x-ai/grok-4.1-fast:free")

llm = ChatOpenAI(
    model_name=MODEL_NAME,
    openai_api_key=API_KEY,
    openai_api_base=API_BASE_URL,
    temperature=0,
    max_retries=3,
)

def extract_course_title(text: str):
    system_message = '''
    Analyze the text to identify the Main Subject or Course Name of this document.
    
    CONTEXT: This is a university course handout.
    
    INSTRUCTIONS:
    1. Find the descriptive English name (e.g. "Digital Design", "Microprocessors", "General Biology").
    2. Ignore alphanumeric codes (like "CS F215", "EEE F111") if a descriptive name is present.
    3. Ignore labels like "Course Title:", "Course No:", "Part II" - just extract the name itself.
    
    Examples:
    - Text: "EEE F211 Electrical Machines" -> Output: "Electrical Machines"
    - Text: "BITS PILANI ... GENERAL BIOLOGY" -> Output: "General Biology"
    '''

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_message),
        ("human", "{text}"),
    ])

    chain = prompt | llm.with_structured_output(CourseTitle)

    try:
        result = chain.invoke({
            "text": text[:3000],
        })
        return result.title
    
    except Exception as e:
        print(f"extracting course error= {e}")
        return "Unknown Course"

def router_node(state: State):
    # structured_llm = llm.with_strcutured_output(RouteDecision)
    
    system_message = '''
    You are a document classifier.
    Analyze the text. Does it contain keywords like:
    'Evaluation Scheme', 'Exam Schedule', 'Mid-Sem', 'Comprehensive exam', 'Final Exam', 'Compre', 'Assignment', 'Test Dates'?
    If YES -> return 'extract'.
    If NO (just syllabus, outcomes, textbooks, intro) -> return 'skip'.
    '''
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_message),
        ("human", "{text}"),
    ])
    # prompt = ChatPromptTemplate.from_template(system_message)

    chain = prompt | llm.with_structured_output(RouteDecision)

    try:
        result = chain.invoke({
            "text": state["raw_text"],
        })
        decision = result.decision.lower()

    except Exception as e:
        print(f"Router error= {e}")
        decision = "skip"

    return {"classification": decision}

def time_extractor_node(state: State):

    system_message = '''
    Extract Exam Dates/Times.
    
    CRITICAL INSTRUCTION:
    1. You are analyzing text from an INDIAN UNIVERSITY. 
    2. Dates are strictly DD/MM/YYYY. (e.g., 09/10 is 9th October, NOT September 10th).

    EXTRACTION RULES:
    1. Extract 'Event Name' (e.g. "Quiz 1", "MidSem Exam", "Comprehensive Exam").
    2. 2. FILL 'date_logic' FIRST: Explicitly write down your reasoning. 
       - Example: "Text says 09/10. Indian format means Day=09, Month=10 (Oct)."
    3. Output 'date_iso' STRICTLY in 'YYYY-MM-DD' format. If year is missing, assume academic year 2025.
    4. If an event has multiple dates (e.g. "Quizzes: 21-Sep and 12-Dec"), split them into TWO separate items in the list.
    5. Extract 'Time'. If text says 'FN' or 'AN', output 'FN' or 'AN'. 
       If text says '4-5:30 PM', output exactly '4-5:30 PM'.
    '''
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_message),
        ("human", "{text}"),
    ])
    # prompt = ChatPromptTemplate.from_template(system_message)

    chain = prompt | llm.with_structured_output(TimeList)

    try:
        result = chain.invoke({
            "text": state["raw_text"]
        })
        return {"time_data": [item.model_dump() for item in result.items]}

    except Exception as e:
        print(f"Time extractor error= {e}")
        return {"time_data": []}
    
def details_extractor_node(state: State):

    system_message = '''
    Extract evaluation metadata (Format and Weightage).
    
    RULES:
    1. Extract 'Event Name' (Must match the exam names).
    2. Extract 'Format':
       - If Open Book/Open/OB -> Output ONLY 'OB'.
       - If Closed Book/Closed/CB -> Output ONLY 'CB'.
    3. Extract 'Weightage' (e.g., 25%, 15 Marks).
    4. IGNORE Dates and Times.
    '''
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_message),
        ("human", "{text}"),
    ])
    # prompt = ChatPromptTemplate.from_template(system_message)
    
    chain = prompt | llm.with_structured_output(DetailsList)

    try:
        result = chain.invoke({
            "text": state["raw_text"]
        })
        return {"details_data": [item.model_dump() for item in result.items]}
        
    except Exception as e:
        print(f"Details extract error= {e}")
        return {"details_data": []}

def aggregator_node(state: State):
    time_data = state.get("time_data", [])
    details_data = state.get("details_data", [])
    title = state.get("known_course_title", "Unknown").strip()

    details_map = {}
    for d in details_data:
        key = normalize_event_name(d["event_name"]).lower()
        clean_event = key.replace("exam", "").replace("ination", "").replace("-", "").strip()
        details_map[clean_event] = d
        details_map[key] = d
        
    final_schedule = []

    for t in time_data:
        t_event = t["event_name"]
        final_event_name = normalize_event_name(t_event)
        key = final_event_name.lower()        

        matched_detail = details_map.get(key, {})

        if not matched_detail:
            for k, v in details_map.items():
                if k in key or key in k:
                    matched_detail = v
                    break
                
        date_from_llm = t["date_iso"]
        time_raw = t["time_raw"]

        start, end = predefined(date_from_llm, time_raw, final_event_name)

        if title:
            full_title = f"{title.title()} + {final_event_name}"
        else:
            full_title = final_event_name

        if start == "Time not found":
            final_start = f"{end}T00:00:00"
            final_end = f"{end}T23:59:59"
            full_title = f"⚠️ TIME TBA: {full_title}"

        else:
            final_start = start
            final_end = end
            
        fmt = matched_detail.get("format", "")
        wgt = matched_detail.get("weightage", "")
        if not fmt or fmt == "TBA": fmt = "TBA"
        if not wgt or wgt == "N/A": wgt = "N/A"
            
        entry = {
            "Subject": full_title,
            "Event_Name": final_event_name,
            "Start_DateTime": final_start,
            "End_DateTime": final_end,
            "Format": fmt,
            "Weightage": wgt,
            "Raw_Time_String": t["time_raw"]
        }

        final_schedule.append(entry)

    return {"final_schedule": final_schedule}

def route_decision(state: State):
    decision = state["classification"]
    
    if decision == "extract":
        return ["time_extractor", "details_extractor"]
    else:
        return "end"
    
# GRAPH NOW
workflow = StateGraph(State)

workflow.add_node("router", router_node)
workflow.add_node("time_extractor", time_extractor_node)
workflow.add_node("details_extractor", details_extractor_node)
workflow.add_node("aggregator", aggregator_node)

workflow.add_edge(START, "router")
workflow.add_conditional_edges(
    "router",
    route_decision,
    {
        "time_extractor": "time_extractor",
        "details_extractor": "details_extractor",
        "end": END
    }
)
workflow.add_edge("time_extractor", "aggregator")
workflow.add_edge("details_extractor", "aggregator")
workflow.add_edge("aggregator", END)

app = workflow.compile()
print("Graph Compiled Successfully!")