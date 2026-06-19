from typing import List, TypedDict
from pydantic import BaseModel, Field

class TimeEntry(TypedDict):
    # subject_name: str
    event_name: str
    date_raw: str
    time_raw: str
class DetailsEntry(TypedDict):
    # subject_name: str
    event_name: str
    format: str
    weightage: str
class State(TypedDict):
    raw_text: str
    page_image_b64: str  # Added for Vision Extractor
    classification: List[str]
    known_course_title: str
    eval_data: List[dict] # Replaces time_data and details_data
    final_schedule: List[dict]
class RouteDecision(BaseModel):
    categories: List[str] = Field(
        description="A list of categories this page belongs to. Can be multiple. Choose from: ['EVAL', 'SYLLABUS', 'ADMIN', 'SKIP']. Return 'EVAL' if it contains exam/evaluation details. Return 'SKIP' if irrelevant."
    )

class CourseTitle(BaseModel):
    title: str = Field(
        description="The descriptive Course Title"
    )

# Single unified schema for Vision-based Eval Extraction
class EvalExtraction(BaseModel):
    event_name: str = Field(
        description = "Name of the exam (e.g., 'Mid-Sem Exam', 'Comprehensive Exam', 'Quiz 1')"
    )
    date_logic: str = Field(
        description="Briefly explain the date extraction logic. Example: 'Found 09/10/2025. In DD/MM format, Day is 09, Month is 10 (October).'"
    )
    date_iso: str = Field(
        description="The date converted strictly to YYYY-MM-DD format (e.g., 2025-10-15). "
                    "CRITICAL RULES: "
                    "1. CONTEXT: The document uses Indian/British format (DD/MM/YYYY). "
                    "2. The FIRST number is ALWAYS the DAY. The SECOND number is the MONTH. "
                    "Example: '09/10/2025' -> Day=09, Month=10 -> Output: '2025-10-09'. "
                    "If multiple dates exist for one event (e.g. '15-Sept and 10-Nov'), create separate entries."
    )
    time_raw: str = Field(
        description = "The time exactly as written. Look for specific times (e.g., '4-5:30 PM') or codes like 'FN' or 'AN'."
    )
    format: str = Field(
        description = "The format of the exam, Look for 'OB' (Open Book), 'CB' (Closed Book). If missing, return 'TBA'."
    )
    weightage: str = Field(
        description = "The weightage or marks percentage (e.g., '25%', '35%'). If missing, return 'N/A'."
    )

class EvalList(BaseModel):
    items: List[EvalExtraction]
