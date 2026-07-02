export interface Event {
  title: string;
  date: string;
  time: string;
  duration: string;
  weightage: string;
  type: string;
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
}

export interface SemesterProfile {
  courses: CourseData[];
}
