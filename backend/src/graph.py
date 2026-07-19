import os
import asyncio
import time

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.messages import HumanMessage

from langgraph.graph import StateGraph, END, START

from src.schema import State, RouteDecision, EvalList, CourseTitle, SyllabusList, ReferenceList
from src.utils import normalize_event_name, clean_subject_key, predefined, enrich_refs_parallel

from src.config import AICREDITS_API_KEY
# from src.config import GOOGLE_API_KEY, AIGATEWAY_API_KEY
# from langchain_google_genai import ChatGoogleGenerativeAI

# ==============================================================================
# ARCHITECTURE CONFIGURATION (As defined in README.md)
# ==============================================================================

# ------------------------------------------------------------------------------
# CASE 1: Full Free Tier
# Text: gpt-oss-20b (OpenRouter Free)
# Vision: gemini-2.5-flash (Google AI Studio Free)
# ------------------------------------------------------------------------------
# llm = ChatOpenAI(
#     model_name="openai/gpt-oss-20b",
#     openai_api_base="https://openrouter.ai/api/v1",
#     openai_api_key=OPENAI_API_KEY,
#     temperature=0,
#     max_retries=3, 
# )
# 
# vision_llm = ChatGoogleGenerativeAI(
#     model="gemini-2.5-flash",
#     google_api_key=GOOGLE_API_KEY,
#     temperature=0,
#     max_retries=5 
# )

# ------------------------------------------------------------------------------
# CASE 2: Production (ACTIVE)
# Text: gpt-oss-20b (AICredits)
# Vision: google/gemini-2.5-flash-lite (AICredits ONLY)
# ------------------------------------------------------------------------------
llm = ChatOpenAI(
    model_name="openai/gpt-oss-20b",
    openai_api_base="https://api.aicredits.in/v1",
    openai_api_key=AICREDITS_API_KEY,
    temperature=0,
    max_retries=3, 
)

vision_llm = ChatOpenAI(
    model_name="google/gemini-2.5-flash-lite",
    openai_api_base="https://api.aicredits.in/v1",
    openai_api_key=AICREDITS_API_KEY,
    temperature=0,
    max_retries=3 
)

# ------------------------------------------------------------------------------
# CASE 3: Development / Testing (Archived)
# Text & Vision: google/gemma-4-26b-a4b-it (AIGateway ONLY Promo)
# ------------------------------------------------------------------------------
# llm = ChatOpenAI(
#     # model_name="google/gemma-4-26b-a4b-it",
#     model_name="moonshot/kimi-k2.6",
#     openai_api_base="https://api.aigateway.sh/v1",
#     openai_api_key=AIGATEWAY_API_KEY,
#     temperature=0,
#     max_retries=3, 
#     request_timeout=180.0,
# )
# 
# vision_llm = ChatOpenAI(
#     # model_name="google/gemma-4-26b-a4b-it",
#     model_name="moonshot/kimi-k2.6",
#     openai_api_base="https://api.aigateway.sh/v1",
#     openai_api_key=AIGATEWAY_API_KEY,
#     temperature=0,
#     max_retries=3 
# )

async def extract_course_title(text: str, image_b64: str = ""):
    parser = PydanticOutputParser(pydantic_object=CourseTitle)
    
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
    
    {format_instructions}
    '''

    # Vision Fallback for scanned PDFs
    if len(text.strip()) < 50 and image_b64 and vision_llm:
        formatted_sys = system_message.format(format_instructions=parser.get_format_instructions())
        message = HumanMessage(content=[
            {"type": "text", "text": formatted_sys}, 
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_b64}"}}
        ])
        try:
            response = await vision_llm.ainvoke([message])
            result = parser.invoke(response)
            return result.title
        except Exception as e:
            print(f"Vision Title Extraction error= {e}")
            return "Unknown Course"

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_message),
        ("human", "{text}"),
    ])

    chain = prompt | llm | parser

    try:
        result = await chain.ainvoke({
            "text": text[:3000],
            "format_instructions": parser.get_format_instructions()
        })
        return result.title
    
    except Exception as e:
        print(f"extracting course error= {e}")
        return "Unknown Course"
    # - 'SYLLABUS': Contains Course Plan, Topics, Lectures, Learning Objectives. (DISABLED: Uncomment when syllabus feature is needed)

async def router_node(state: State):
    parser = PydanticOutputParser(pydantic_object=RouteDecision)
    
    system_message = '''
    You are a document classifier for university handouts.
    Analyze the text and categorize it. It may belong to multiple categories.
    Categories:
    - 'EVAL': MUST contain an actual Evaluation Scheme, Exam Schedule, list of Quizzes, Mid-Sem dates, Comprehensive exam dates, or Weightage tables. Do NOT classify general grading notices or make-up policies as EVAL unless actual dates or weightages are present. Do NOT classify Course Plans, Lecture Schedules, or lists of academic topics as EVAL.
    - 'REFERENCES': Contains Textbooks, Reference Books, required reading materials.
    - 'SKIP': General introduction, textbook lists without schedules, or completely irrelevant.
    
    Return a list of the applicable categories. If none apply, return ['SKIP'].
    
    {format_instructions}
    '''
    
    raw_text = state.get("raw_text", "").strip()
    
    # Vision Fallback for scanned PDFs or images
    if len(raw_text) < 50:
        image_b64 = state.get("page_image_b64", "")
        if image_b64 and vision_llm:
            formatted_sys = system_message.format(format_instructions=parser.get_format_instructions())
            message = HumanMessage(content=[
                {"type": "text", "text": formatted_sys}, 
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_b64}"}}
            ])
            try:
                response = await vision_llm.ainvoke([message])
                result = parser.invoke(response)
                return {"classification": result.categories}
            except Exception as e:
                print(f"Vision Router error= {e}")
                return {"classification": ["SKIP"]}
        else:
            return {"classification": ["SKIP"]}
            
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_message),
        ("human", "{text}"),
    ])

    chain = prompt | llm | parser

    try:
        result = await chain.ainvoke({
            "text": raw_text[:3000],
            "format_instructions": parser.get_format_instructions()
        })
        categories = result.categories
    except Exception as e:
        print(f"Router error= {e}")
        categories = ["SKIP"]

    return {"classification": categories}

async def vision_eval_extractor_node(state: State):
    parser = PydanticOutputParser(pydantic_object=EvalList)
    
    system_text = f'''
    Extract Exam Dates, Times, Format, and Weightage from the provided image of a university syllabus.
    
    CRITICAL INSTRUCTION:
    1. You are analyzing an image from an INDIAN UNIVERSITY. 
    2. Dates are strictly DD/MM/YYYY.
    3. ONLY extract items from the official Evaluation/Grading Scheme table. IGNORE weekly lecture schedules and class plans.
    
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
        start_time = time.time()
        print(f"[DEBUG] >>> Sending EVAL Vision LLM request...")
        response = await vision_llm.ainvoke([message])
        print(f"[DEBUG] <<< Received EVAL Vision LLM response in {time.time() - start_time:.2f}s!")
        result = parser.invoke(response)
        return {"eval_data": [item.model_dump() for item in result.items]}
    except Exception as e:
        print(f"[DEBUG] !!! Vision extractor error= {e}")
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

async def vision_syllabus_extractor_node(state: State):
    parser = PydanticOutputParser(pydantic_object=SyllabusList)
    
    system_text = f'''
    Extract the Course Syllabus / Lecture Plan from the provided image.
    
    EXTRACTION RULES:
    1. Extract 'module_name' (the name of the topic or unit).
    2. Extract 'number_of_lectures' (the number of lectures allocated to this topic, e.g., '6', '12').
    3. If lecture counts are not present, estimate or put 'N/A'.
    
    {parser.get_format_instructions()}
    '''
    
    image_b64 = state.get("page_image_b64", "")
    if not image_b64 or not vision_llm: return {"syllabus_data": []}
    
    message = HumanMessage(content=[{"type": "text", "text": system_text}, {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_b64}"}}])
    try:
        start_time = time.time()
        print(f"[DEBUG] >>> Sending SYLLABUS Vision LLM request...")
        response = await vision_llm.ainvoke([message])
        print(f"[DEBUG] <<< Received SYLLABUS Vision LLM response in {time.time() - start_time:.2f}s!")
        result = parser.invoke(response)
        return {"syllabus_data": [item.model_dump() for item in result.items]}
    except Exception as e:
        print(f"[DEBUG] !!! Syllabus extractor error= {e}")
        return {"syllabus_data": []}

async def vision_reference_extractor_node(state: State):
    parser = PydanticOutputParser(pydantic_object=ReferenceList)
    
    system_text = f'''
    Extract the Textbooks and Reference Books from the provided image.
    
    EXTRACTION RULES:
    1. Extract the 'title' of the book.
    2. Extract the 'author' of the book.
    
    {parser.get_format_instructions()}
    '''
    
    image_b64 = state.get("page_image_b64", "")
    if not image_b64 or not vision_llm: return {"reference_data": []}
    
    message = HumanMessage(content=[{"type": "text", "text": system_text}, {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_b64}"}}])
    try:
        start_time = time.time()
        print(f"[DEBUG] >>> Sending REFERENCES Vision LLM request...")
        response = await vision_llm.ainvoke([message])
        print(f"[DEBUG] <<< Received REFERENCES Vision LLM response in {time.time() - start_time:.2f}s!")
        result = parser.invoke(response)
        return {"reference_data": [item.model_dump() for item in result.items]}
    except Exception as e:
        print(f"[DEBUG] !!! Reference extractor error= {e}")
        return {"reference_data": []}

async def vision_orchestrator_node(state: State):
    categories = state.get("classification", [])
    
    results = {
        "eval_data": [],
        "syllabus_data": [],
        "reference_data": []
    }
    
    if not categories or "SKIP" in categories:
        return results
    
    # Build async tasks for true concurrent fan-out (no threads needed)
    tasks = {}
    if "EVAL" in categories:
        tasks["EVAL"] = vision_eval_extractor_node(state)
    # DISABLED: Syllabus extraction commented out for cost/speed optimization.
    # Uncomment below (+ router prompt category) to re-enable when syllabus feature is ready.
    # if "SYLLABUS" in categories:
    #     tasks["SYLLABUS"] = vision_syllabus_extractor_node(state)
    if "REFERENCES" in categories:
        tasks["REFERENCES"] = vision_reference_extractor_node(state)
    
    if tasks:
        task_keys = list(tasks.keys())
        task_results = await asyncio.gather(*tasks.values(), return_exceptions=True)
        
        for cat, res in zip(task_keys, task_results):
            if isinstance(res, Exception):
                print(f"Orchestrator error in {cat}: {res}")
                continue
            if cat == "EVAL":
                results["eval_data"] = res.get("eval_data", [])
            # elif cat == "SYLLABUS":
            #     results["syllabus_data"] = res.get("syllabus_data", [])
            elif cat == "REFERENCES":
                results["reference_data"] = res.get("reference_data", [])
    
    return results

def route_decision(state: State) -> str:
    categories = state.get("classification", [])
    
    if "SKIP" in categories or not categories:
        return "end"
        
    if any(c in categories for c in ["EVAL", "REFERENCES"]):  # SYLLABUS removed — re-add when needed
        return "vision_orchestrator"
        
    return "end"

def post_process_node(state: State):
    refs = state.get("reference_data", [])
    if refs:
        enrich_refs_parallel(refs)
    return {"reference_data": refs}

# GRAPH NOW
workflow = StateGraph(State)

workflow.add_node("router", router_node)
workflow.add_node("vision_orchestrator", vision_orchestrator_node)
workflow.add_node("aggregator", aggregator_node)
workflow.add_node("post_process", post_process_node)

workflow.add_edge(START, "router")
workflow.add_conditional_edges(
    "router",
    route_decision,
    {
        "vision_orchestrator": "vision_orchestrator",
        "end": END
    }
)
workflow.add_edge("vision_orchestrator", "aggregator")
workflow.add_edge("aggregator", "post_process")
workflow.add_edge("post_process", END)

app = workflow.compile()
print("Graph Compiled Successfully without MemorySaver (Stateless)!")