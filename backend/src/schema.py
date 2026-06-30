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
    syllabus_data: List[dict] # New for Issue 8
    reference_data: List[dict] # New for Issue 8
    final_schedule: List[dict]
    user_date_format: str
class RouteDecision(BaseModel):
    categories: List[str] = Field(
        description="A list of categories this page belongs to. Can be multiple. Choose from: ['EVAL', 'SYLLABUS', 'REFERENCES', 'SKIP']. Return 'EVAL' if it contains exam/evaluation details. Return 'SYLLABUS' if it contains course plan or lecture counts. Return 'REFERENCES' if it lists textbooks. Return 'SKIP' if irrelevant."
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
    date_raw: str = Field(
        description="The exact text snippet where the date is mentioned (e.g., '09/10/2025', '15-Sept', '10th Nov'). "
                    "DO NOT attempt to format it into ISO or translate it. Extract it precisely as it appears on the page. "
                    "If multiple dates exist for one event, create separate entries."
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

# Syllabus Schema
class SyllabusExtraction(BaseModel):
    module_name: str = Field(description="Name of the module or topic")
    number_of_lectures: str = Field(description="Number of lectures allocated to this topic")

class SyllabusList(BaseModel):
    items: List[SyllabusExtraction]

# References Schema
class ReferenceExtraction(BaseModel):
    title: str = Field(description="Title of the textbook or reference material")
    author: str = Field(description="Author(s) of the textbook")

class ReferenceList(BaseModel):
    items: List[ReferenceExtraction]
