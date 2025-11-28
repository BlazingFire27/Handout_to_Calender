from datetime import datetime
import os

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from langgraph.graph import StateGraph, END, START

from src.schema import State, RouteDecision, TimeList, DetailsList
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
    
    system_msg = """
    Extract all exam dates and times from the text.
    
    RULES:
    1. Extract 'Subject Name' from the Course Title and other Course information.
    2. Extract 'Event Name' exactly as written.
    3. Output 'date_iso' STRICTLY in 'YYYY-MM-DD' format. If year is missing, assume academic year 2025.
    4. If an event has multiple dates (e.g. "Quizzes: 21-Sep and 12-Dec"), split them into TWO separate items in the list.
    5. Extract 'Time'. If text says 'FN' or 'AN', output 'FN' or 'AN'. 
       If text says '4-5:30 PM', output exactly '4-5:30 PM'.
    """
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_msg),
        ("human", "{text}"),
    ])
    
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
    
    system_msg = """
    Extract evaluation metadata (Format and Weightage).
    
    CRITICAL INSTRUCTIONS:
    1. Extract 'Subject Name' from the Course Title and other Course information.
    2. Extract 'Event Name' (Must match the exam names).
    3. Extract 'Format':
       - If Open Book/Open/OB -> Output ONLY 'OB'.
       - If Closed Book/Closed/CB -> Output ONLY 'CB'.
    4. Extract 'Weightage' (e.g., 25%, 15 Marks).
    5. IGNORE Dates and Times.
    """
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_msg),
        ("human", "{text}"),
    ])
    
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

    strict_map = {}
    simple_map = {}

    for item in details_data:
        subject = item.get("subject_name", "").lower().strip()
        event = item["event_name"].lower().strip()

        sub_key = clean_subject_key(subject)
        event_key = normalize_event_name(event).lower()
        
        strict_composition = f"{sub_key}|{event_key}"
        strict_map[strict_composition] = item

        clean_event = event_key.replace("exam", "").replace("ination", "").replace("-", "").strip()
        simple_map[clean_event] = item
        simple_map[event_key] = item
        
    final_schedule = []

    for t in time_data:
        t_subject = t.get("subject_name", "").strip().lower()
        t_event = t["event_name"].strip().lower()

        final_event_name = normalize_event_name(t_event)
        search_sub = clean_subject_key(t_subject)
        search_evt = final_event_name.lower()        

        strict_composition = f"{search_sub}|{search_evt}"
        matched_detail = strict_map.get(strict_composition)

        if not matched_detail:
            matched_detail = simple_map.get(search_evt)

        if not matched_detail:
            clean_search = search_evt.replace("exam", "").replace("ination", "").replace("-", "").strip()
            matched_detail = simple_map.get(clean_search, {})
        
        if t_subject:
            full_title = f"{search_sub.title()} + {final_event_name}"
        else:
            full_title = final_event_name
        
        date_from_llm = t.get("date_iso", "")
        time_raw = t["time_raw"]

        start, end = predefined(date_from_llm, time_raw, final_event_name)

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