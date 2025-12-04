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
    classification: str
    known_course_title: str
    time_data: List[TimeEntry]
    details_data: List[DetailsEntry]
    final_schedule: List[dict]
class RouteDecision(BaseModel):
    decision: str = Field(
        description = "Return 'extract' if the text contains an exam/evaluation schedule table. Return 'skip' if it is syllabus, textbook or introduction."
    )

class CourseTitle(BaseModel):
    title: str = Field(
        description="The descriptive Course Title"
    )

#This is for branch A related to time of the examination
class TimeExtraction(BaseModel):
    # subject_name: str = Field(
    #     description="The Name of the Course (e.g., 'Digital Design', 'Microprocessors') usually found in the header or title."
    # )
    event_name: str = Field(
        description = "Name of the exam (e.g., 'Mid-Sem Exam', 'Comprehensive Exam', 'Quiz 1', 'Quiz 2', 'Assignment', 'Lab')"
    )
    date_iso: str = Field(
        description="The date converted strictly to YYYY-MM-DD format (e.g., 2025-10-15). "
                    "If the text says '15-Sept', output '2025-09-15'. "
                    "If multiple dates exist for one event (e.g. '15-Sept and 10-Nov'), create separate entries."
    )
    time_raw: str = Field(
        description = "The time exactly as written. Look for specific times (e.g., '4-5:30 PM') or codes like 'FN' or 'AN'."
    )

class TimeList(BaseModel):
    items: List[TimeExtraction]

#This is for branch B related to other details of the examination
class DetailsExtraction(BaseModel):
    # subject_name: str = Field(
    #     description="The Name of the Course (e.g., 'Digital Design') (Must match the name extracted in the Time Branch)."
    # )
    event_name: str = Field(
        description = "Name of the exam (Must match the name extracted in the Time Branch)"
    )
    format: str = Field(
        description = "The format of the exam, Look for 'OB' (Open Book), 'CB' (Closed Book), or explicit text."
    )
    weightage: str = Field(
        description = "The weightage or marks percentage (e.g., '25%', '35%')."
    )

class DetailsList(BaseModel):
    items: List[DetailsExtraction]
