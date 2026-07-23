export interface Event {
  Subject: string;
  Event_Name: string;
  Start_DateTime: string;
  End_DateTime: string;
  Format: string;
  Weightage: string;
  Raw_Time_String?: string;
  course_title?: string;
}

export interface SyllabusTopic {
  module: string;
  topics: string;
  course_title?: string;
}

export interface Reference {
  type: string;
  details: string;
  course_title?: string;
}

export interface CourseData {
  course_title: string;
  evaluation_scheme: Event[];
  syllabus_topics: SyllabusTopic[];
  references: Reference[];
  original_pdf_index?: number;
}

export interface SemesterProfile {
  courses: CourseData[];
}
