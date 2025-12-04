import time
import pdfplumber
from src.utils import save_ics
from src import app, extract_course_title

OUTPUT_ICS = "Combined_Exam_Schedule.ics"
file1_path = "Handouts/EM Handout.pdf"
file2_path = "Handouts/DD Handout_2025_2026.pdf"

def process_pdf(pdf_file):
    if pdf_file is None:
        return []
    
    print(f"Processing PDF: {pdf_file}")
    raw_pages = []

    try:
        with pdfplumber.open(pdf_file) as pdf:
            print(f"Total pages = {len(pdf.pages)}")

            for i in range(len(pdf.pages)):
                page = pdf.pages[i]
                text = page.extract_text()
                raw_pages.append((i+1, text))

    except Exception as e:
        print(f"PDF Processing error: {e}")
        return None, "Error processing PDF"

    course_title_final = ""
    if raw_pages:
        try:
            title = extract_course_title(raw_pages[0][1])
            if title:
                course_title_final = title
                print(f"Extracted Course Title: {course_title_final}")
            else:
                print("No Course Title extracted.")
                course_title_final = "Unknown Course"

        except Exception as e:
            print(f"Course Title Extraction error: {e}")

    all_events = []

    for page_num, text in raw_pages:
        print(f"Processing Page {page_num}...")
        start_time = time.time()
        try:
            initial_state = {
                'raw_text': text,
                'known_course_title': course_title_final
            }

            result = app.invoke(initial_state)
            events = result.get("final_schedule", [])
            all_events.extend(events)
            print(f"  Extracted {len(events)} events from Page {page_num}.")

        except Exception as e:
            print(f"  Error on Page {page_num}: {e}")
        
        end_time = time.time()
        print(f"Time taken: {end_time - start_time:.2f} seconds.\n")

    return all_events

def main(pdf_files):
    all_pdf_events = []

    for pdf_file in pdf_files:
        events = process_pdf(pdf_file)
        all_pdf_events.extend(events)

    if all_pdf_events:
        save_ics(all_pdf_events, OUTPUT_ICS)
    else:
        print("No events extracted from any document.")

if __name__ == "__main__":
    files = [file1_path, file2_path]
    main(files)


####
####
####
#### FOLLOWING ARE TEST CASES WHICH I USED TO TEST THE FIRST MINIMUM VIABLE LOGIC
#### THANK YOU GEMINI FOR PROVIDING THE TEST CASES
####
####
####

#test_cases = [
#     {
#         "id": 1,
#         "desc": "Standard Midsem (Explicit Time)",
#         "text": """
#         BITS PILANI - HYDERABAD CAMPUS
#         COURSE HANDOUT: DIGITAL DESIGN (CS F215)
#         Evaluation Scheme:
#         1. Mid-Sem Exam. 11/10/2025. 4-5:30 PM. Closed Book. 25%.
#         """
#     },
#     {
#         "id": 2,
#         "desc": "Compre Exam (FN Code)",
#         "text": """
#         COURSE: OPERATING SYSTEMS
#         Evaluation:
#         Comprehensive Exam. 16/12/2025. FN. Open Book. 35%.
#         """
#     },
#     {
#         "id": 3,
#         "desc": "Composite Key (Two Courses on One Page)",
#         "text": """
#         NOTICE BOARD - EXAM UPDATES
#         1. Course: MICROPROCESSORS (CS F241)
#            - Mid-Sem Exam. Date: 09/10/2025. Time: 9-10:30 AM. Weightage: 30%.
#         2. Course: DATABASE SYSTEMS (CS F212)
#            - Mid-Sem Exam. Date: 11/10/2025. Time: 2-3:30 PM. Weightage: 25%.
#         """
#     },
#     {
#         "id": 4,
#         "desc": "Time TBA (ISO Date Fix Check)",
#         "text": """
#         COURSE: MACHINE LEARNING (CS F429)
#         Evaluation:
#         1. Project Presentation. Date: 20/11/2025. Time: To be announced later. Format: Open. 15%.
#         """
#     },
#     {
#         "id": 5,
#         "desc": "Hyphenated Date & AN Code",
#         "text": """
#         COURSE: COMPILER CONSTRUCTION
#         Evaluation:
#         Comprehensive Exam. 15-12-2025. AN. Closed Book. 40 Marks.
#         """
#     },
#     {
#         "id": 6,
#         "desc": "Late Evening Quiz",
#         "text": """
#         COURSE: COMPUTER ARCHITECTURE
#         Quiz 1. Date: 05/09/2025. Time: 5:00 PM - 6:00 PM. Format: CB. Weight: 10%.
#         """
#     },
#     {
#         "id": 7,
#         "desc": "Hidden Table in Noise",
#         "text": """
#         COURSE: GENERAL BIOLOGY
#         Textbook: Campbell. Attendance: Mandatory.
#         Evaluation Scheme: 
#         Mid-Sem Exam. 10/10/2025. 11 AM. CB. 30%.
#         Library Rules: Silence please.
#         """
#     },
#     {
#         "id": 8,
#         "desc": "Exam Announced, Format Missing",
#         "text": """
#         COURSE: QUANTUM PHYSICS
#         Mid-Sem Exam: 14/10/2025, 9:00 AM.
#         (Details on weightage will be shared in class).
#         """
#     },
#     {
#         "id": 9,
#         "desc": "Event Normalization ('Final Exam' -> 'Comprehensive')",
#         "text": """
#         COURSE: ECONOMICS (ECON F211)
#         Assessment:
#         Final Exam. Date: 20/12/2025. Time: FN. Format: OB. Weight: 35%.
#         """
#     },
#     {
#         "id": 10,
#         "desc": "2-Digit Year & Footer Table",
#         "text": """
#         COURSE: CHEMISTRY
#         ... content ...
#         (Bottom of Page 4)
#         | Midsem | 12/10/25 | 2 PM | CB | 25% |
#         """
#     }
# ]

# # LOOP
# def run_tests():
#     print(f"🚀 STARTING LOGIC TEST SUITE ({len(test_cases)} CASES)...\n")
    
#     for case in test_cases:
#         print(f"🔹 CASE {case['id']}: {case['desc']}")
#         start_time = time.time()
        
#         try:
#             result = app.invoke({"raw_text": case['text']})
            
#             events = result.get("final_schedule", [])
            
#             if not events:
#                 print("   ❌ No events found (Router skipped or Extraction failed)")
#             else:
#                 for ev in events:
#                     print(f"   ✅ Subject: {ev['Subject']}")
#                     print(f"      Time:    {ev['Start_DateTime']} -> {ev['End_DateTime']}")
#                     print(f"      Format:  {ev['Format']} | Weight: {ev['Weightage']}")
#                     print(f"      Raw:     '{ev['Raw_Time_String']}'")
        
#         except Exception as e:
#             print(f"   🔥 CRASH: {e}")
            
#         print(f"   ⏱️  Taken: {time.time() - start_time:.2f}s")
#         print("-" * 50)

