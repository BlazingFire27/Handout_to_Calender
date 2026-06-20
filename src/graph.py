import os

from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.messages import HumanMessage

from langgraph.graph import StateGraph, END, START

from src.schema import State, RouteDecision, EvalList, CourseTitle
from src.utils import normalize_event_name, clean_subject_key, predefined

try:
    from src.config import API_KEY, API_BASE_URL, MODEL_NAME, GOOGLE_API_KEY
except ImportError:
    API_KEY = os.getenv("OPENAI_API_KEY")
    API_BASE_URL = os.getenv("OPENAI_API_BASE", "https://openrouter.ai/api/v1")
    MODEL_NAME = os.getenv("MODEL_NAME", "google/gemini-2.0-flash-exp:free")
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Text LLM for routing (fast, cheap)
llm = ChatOpenAI(
    model_name=MODEL_NAME,
    openai_api_base=API_BASE_URL,
    temperature=0,
    max_retries=0, 
)

# Vision LLM for table extraction (heavy, multimodal natively)
if GOOGLE_API_KEY:
    vision_llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=GOOGLE_API_KEY,
        temperature=0,
        max_retries=3 
    )
else:
    vision_llm = None

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
    parser = PydanticOutputParser(pydantic_object=RouteDecision)
    
    system_message = '''
    You are a document classifier for university handouts.
    Analyze the text and categorize it. It may belong to multiple categories.
    Categories:
    - 'EVAL': MUST contain an actual Evaluation Scheme, Exam Schedule, list of Quizzes, Mid-Sem dates, Comprehensive exam dates, or Weightage tables. Do NOT classify general grading notices or make-up policies as EVAL unless actual dates or weightages are present.
    - 'SYLLABUS': Contains Course Plan, Topics, Lectures, Learning Objectives.
    - 'ADMIN': Contains Instructor details, Chamber consultation hours, Office hours, Make-up policies.
    - 'SKIP': General introduction, textbook lists without schedules, or completely irrelevant.
    
    Return a list of the applicable categories. If none apply, return ['SKIP'].
    
    {format_instructions}
    '''
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_message),
        ("human", "{text}"),
    ])

    chain = prompt | llm | parser

    try:
        result = chain.invoke({
            "text": state["raw_text"],
            "format_instructions": parser.get_format_instructions()
        })
        categories = result.categories
    except Exception as e:
        print(f"Router error= {e}")
        categories = ["SKIP"]

    return {"classification": categories}

def vision_eval_extractor_node(state: State):
    parser = PydanticOutputParser(pydantic_object=EvalList)
    
    system_text = f'''
    Extract Exam Dates, Times, Format, and Weightage from the provided image of a university syllabus.
    
    CRITICAL INSTRUCTION:
    1. You are analyzing an image from an INDIAN UNIVERSITY. 
    2. Dates are strictly DD/MM/YYYY.
    
    EXTRACTION RULES:
    1. Extract 'event_name' (e.g. "Quiz 1", "Mid-Sem Exam", "Comprehensive Exam").
    2. Output 'date_raw' exactly as it is written in the document. Do not reformat.
    3. If an event has multiple dates, create TWO separate items in the list.
    4. Extract 'time_raw'. Output exactly what is written (e.g. '4-5:30 PM', 'FN', 'AN').
    5. Extract 'format'. Look for 'OB' or 'CB'. If missing, return 'TBA'.
    6. Extract 'weightage'. If missing, return 'N/A'.
    
    {parser.get_format_instructions()}
    '''
    
    image_b64 = state.get("page_image_b64", "")
    
    if not image_b64:
        print("Vision Extractor: No image provided!")
        return {"eval_data": []}
        
    if not vision_llm:
        print("Vision Extractor: GOOGLE_API_KEY is missing! Cannot run vision model.")
        return {"eval_data": []}

    message = HumanMessage(
        content=[
            {"type": "text", "text": system_text},
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_b64}"}},
        ]
    )

    try:
        response = vision_llm.invoke([message])
        result = parser.invoke(response)
        return {"eval_data": [item.model_dump() for item in result.items]}
    except Exception as e:
        print(f"Vision extractor error= {e}")
        return {"eval_data": []}

def aggregator_node(state: State):
    eval_data = state.get("eval_data", [])
    title = state.get("known_course_title", "Unknown").strip()

    final_schedule = []

    for item in eval_data:
        t_event = item["event_name"]
        final_event_name = normalize_event_name(t_event)
                
        date_raw = item["date_raw"]
        time_raw = item["time_raw"]
        user_format = state.get("user_date_format", "DMY")

        start, end = predefined(date_raw, time_raw, final_event_name, user_format)

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
            
        entry = {
            "Subject": full_title,
            "Event_Name": final_event_name,
            "Start_DateTime": final_start,
            "End_DateTime": final_end,
            "Format": item.get("format", "TBA"),
            "Weightage": item.get("weightage", "N/A"),
            "Raw_Time_String": item["time_raw"]
        }
        final_schedule.append(entry)

    return {"final_schedule": final_schedule}

def route_decision(state: State):
    categories = state.get("classification", [])
    
    if "EVAL" in categories:
        return "vision_eval_extractor"
    else:
        return "end"

# GRAPH NOW
workflow = StateGraph(State)

workflow.add_node("router", router_node)
workflow.add_node("vision_eval_extractor", vision_eval_extractor_node)
workflow.add_node("aggregator", aggregator_node)

workflow.add_edge(START, "router")
workflow.add_conditional_edges(
    "router",
    route_decision,
    {
        "vision_eval_extractor": "vision_eval_extractor",
        "end": END
    }
)
workflow.add_edge("vision_eval_extractor", "aggregator")
workflow.add_edge("aggregator", END)

app = workflow.compile()
print("Graph Compiled Successfully!")