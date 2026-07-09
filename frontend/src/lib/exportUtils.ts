import { SemesterProfile } from "@/types";
import { toast } from "sonner";

export const handleDownloadJson = (semesterData: SemesterProfile | null) => {
  if (!semesterData) return;
  const blob = new Blob([JSON.stringify(semesterData, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = "Semester_Profile.json";
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
};

export const handleDownloadICS = (semesterData: SemesterProfile | null) => {
  if (!semesterData) return;
  let icsContent = "BEGIN:VCALENDAR\nVERSION:2.0\nPRODID:-//Handout2Calendar//EN\n";
  semesterData.courses.forEach(course => {
    course.evaluation_scheme.forEach((exam: any) => {
      if (!exam.Start_DateTime || !exam.End_DateTime || exam.Start_DateTime.includes("Time not found")) return;
      const start = exam.Start_DateTime.replace(/[-:]/g, "").replace(/\.\d{3}/, "");
      const end = exam.End_DateTime.replace(/[-:]/g, "").replace(/\.\d{3}/, "");
      icsContent += "BEGIN:VEVENT\n";
      icsContent += `SUMMARY:${exam.Subject || course.course_title} - ${exam.Event_Name}\n`;
      icsContent += `DTSTART;TZID=Asia/Kolkata:${start}\n`;
      icsContent += `DTEND;TZID=Asia/Kolkata:${end}\n`;
      icsContent += `DESCRIPTION:Format: ${exam.Format}\\nWeightage: ${exam.Weightage}\\nCourse: ${course.course_title}\n`;
      icsContent += "END:VEVENT\n";
    });
  });
  icsContent += "END:VCALENDAR";
  const blob = new Blob([icsContent], { type: "text/calendar" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = "Combined_Exam_Schedule.ics";
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
};

export const handleExportCSV = (courseTitle: string, topics: any[]) => {
  const csvContent = "data:text/csv;charset=utf-8," 
    + "Module Name,Lectures\n"
    + topics.map(e => `"${e.module_name.replace(/"/g, '""')}",${e.number_of_lectures}`).join("\n");
  const encodedUri = encodeURI(csvContent);
  const link = document.createElement("a");
  link.setAttribute("href", encodedUri);
  link.setAttribute("download", `${courseTitle}_Syllabus.csv`);
  document.body.appendChild(link);
  link.click();
  link.remove();
};

export const generateAIPrompt = (courseTitle: string, topics: any[]) => {
  const topicsStr = topics.map(t => `- ${t.module_name} (${t.number_of_lectures} lectures)`).join('\n');
  return encodeURIComponent(`I am studying ${courseTitle}. Here is my syllabus:\n${topicsStr}\n\nPlease generate a 7-day study plan and 10 practice questions for these topics.`);
};

export const handleCopyPrompt = (courseTitle: string, topics: any[]) => {
  const prompt = decodeURIComponent(generateAIPrompt(courseTitle, topics));
  navigator.clipboard.writeText(prompt);
  toast.success("Prompt copied to clipboard!", { description: "You can now paste it into Claude, Gemini, etc." });
};
