import time
import base64
import fitz # PyMuPDF
from src.utils import save_ics
from src import app, extract_course_title

import json
import os
import asyncio
import uuid

# from langchain_core.globals import set_debug
# set_debug(True)

OUTPUT_DIR = "output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

OUTPUT_ICS = f"{OUTPUT_DIR}/Combined_Exam_Schedule.ics"
OUTPUT_JSON = f"{OUTPUT_DIR}/Semester_Profile.json"

file1_path = "Handouts/EM Handout.pdf"
file2_path = "Handouts/DD Handout_2025_2026.pdf"
file3_path = "Handouts/EEPE18-Digital Signal Processing.pdf"

async def process_pdf(pdf_file, user_date_format="DMY"):
    if pdf_file is None:
        return "", [], [], []
    
    print(f"Processing PDF: {pdf_file}")
    raw_pages = []

    try:
        doc = fitz.open(pdf_file)
        print(f"Total pages = {len(doc)}")

        for i in range(len(doc)):
            page = doc[i]
            text = page.get_text()
            
            # Extract Image Base64
            pix = page.get_pixmap(dpi=150) # Moderate DPI for API speed
            img_bytes = pix.tobytes("png")
            b64_image = base64.b64encode(img_bytes).decode("utf-8")
            
            raw_pages.append((i+1, text, b64_image))

    except Exception as e:
        print(f"PDF Processing error: {e}")
        return "", [], [], []

    course_title_final = ""
    if raw_pages:
        try:
            # Pass text and image for the first page to support Vision Fallback on scanned PDFs
            title = await extract_course_title(text=raw_pages[0][1], image_b64=raw_pages[0][2])
            if title:
                course_title_final = title
                print(f"Extracted Course Title: {course_title_final}")
            else:
                print("No Course Title extracted.")
                course_title_final = "Unknown Course"

        except Exception as e:
            print(f"Course Title Extraction error: {e}")

    all_events = []
    all_syllabus = []
    all_refs = []

    for page_num, text, b64_image in raw_pages:
        print(f"Processing Page {page_num}...")
        start_time = time.time()
        try:
            initial_state = {
                'raw_text': text,
                'page_image_b64': b64_image,
                'known_course_title': course_title_final,
                'user_date_format': user_date_format
            }

            result = await app.ainvoke(initial_state)
            
            events = result.get("final_schedule", [])
            syllabus = result.get("syllabus_data", [])
            refs = result.get("reference_data", [])
            
            all_events.extend(events)
            all_syllabus.extend(syllabus)
            
            if refs:
                all_refs.extend(refs)
            
            if events:
                print(f"  ✅ Extracted {len(events)} Evaluation events from Page {page_num}.")
            if syllabus:
                print(f"  ✅ Extracted {len(syllabus)} Syllabus topics from Page {page_num}.")
            if refs:
                print(f"  ✅ Extracted {len(refs)} Reference Books from Page {page_num}.")
                
            if not events and not syllabus and not refs:
                print(f"  ⏭️ Skipped Page {page_num} (No relevant data found).")

        except Exception as e:
            print(f"  🔥 Error on Page {page_num}: {e}")
        
        end_time = time.time()
        print(f"Time taken: {end_time - start_time:.2f} seconds.\n")
        
        # Rate limit prevention (Free Gemini Tier allows 15 RPM)
        # Since we run 3 parallel vision nodes, we must sleep to prevent 429 Too Many Requests
        # UNCOMMENT THE FOLLOWING LINE IF RUNNING ON FREE GOOGLE AI STUDIO TIER
        # time.sleep(4)

    return course_title_final, all_events, all_syllabus, all_refs

async def process_pdf_stream(pdf_file, user_date_format="DMY"):
    if pdf_file is None:
        yield json.dumps({"type": "error", "message": "No file provided"}) + "\n"
        return
    
    try:
        base_name = os.path.basename(pdf_file)
        print(f"\n🚀 [{base_name}] Processing PDF: {pdf_file}")
        doc = await asyncio.to_thread(fitz.open, pdf_file)
        total_pages = len(doc)
        print(f"📄 [{base_name}] Total pages = {total_pages}")
    except Exception as e:
        yield json.dumps({"type": "error", "message": f"PDF Processing error: {e}"}) + "\n"
        return

    yield json.dumps({"type": "init", "total_pages": total_pages}) + "\n"

    # Extract pages concurrently or in a thread to avoid blocking
    def extract_pages():
        pages = []
        for i in range(total_pages):
            page = doc[i]
            text = page.get_text()
            pix = page.get_pixmap(dpi=150)
            img_bytes = pix.tobytes("png")
            b64_image = base64.b64encode(img_bytes).decode("utf-8")
            pages.append((i+1, text, b64_image))
        doc.close() # Crucial: Release file lock so Windows can delete it later
        return pages

    raw_pages = await asyncio.to_thread(extract_pages)

    course_title_final = "Unknown Course"
    if raw_pages:
        try:
            title = await extract_course_title(raw_pages[0][1], raw_pages[0][2])
            if title:
                course_title_final = title
                print(f"🎓 [{base_name}] Extracted Course Title: {course_title_final}")
            else:
                print(f"⚠️ [{base_name}] No Course Title extracted.")
        except Exception as e:
            print(f"🔥 [{base_name}] Course Title Extraction error: {e}")

    yield json.dumps({"type": "progress", "message": f"Extracted Title: {course_title_final}"}) + "\n"

    all_events = []
    all_syllabus = []
    all_refs = []

    run_id = str(uuid.uuid4())[:8]

    for page_num, text, b64_image in raw_pages:
        start_time = time.time()
        print(f"🔄 [{base_name}] Processing Page {page_num}...")
        yield json.dumps({"type": "progress", "message": f"Processing Page {page_num}/{total_pages}..."}) + "\n"
        
        try:
            initial_state = {
                'raw_text': text,
                'page_image_b64': b64_image,
                'known_course_title': course_title_final,
                'user_date_format': user_date_format
            }
            
            # Run langgraph natively async — no thread wrapper needed
            result = await app.ainvoke(initial_state)
            
            events = result.get("final_schedule", [])
            syllabus = result.get("syllabus_data", [])
            refs = result.get("reference_data", [])
            
            all_events.extend(events)
            all_syllabus.extend(syllabus)
            if refs:
                all_refs.extend(refs)
                
            if events:
                print(f"  ✅ [{base_name}] Extracted {len(events)} Evaluation events from Page {page_num}.")
            if syllabus:
                print(f"  ✅ [{base_name}] Extracted {len(syllabus)} Syllabus topics from Page {page_num}.")
            if refs:
                print(f"  ✅ [{base_name}] Extracted {len(refs)} Reference Books from Page {page_num}.")
                
            if not events and not syllabus and not refs:
                print(f"  ⏭️ [{base_name}] Skipped Page {page_num} (No relevant data found).")
            
            end_time = time.time()
            print(f"⏱️ [{base_name}] Time taken for Page {page_num}: {end_time - start_time:.2f} seconds.\n")

            yield json.dumps({
                "type": "page_done", 
                "page": page_num, 
                "events_found": len(events),
                "syllabus_found": len(syllabus),
                "refs_found": len(refs)
            }) + "\n"
            
        except Exception as e:
            print(f"  🔥 [{base_name}] Error on Page {page_num}: {e}")
            yield json.dumps({"type": "error", "message": f"Error on Page {page_num}: {str(e)}"}) + "\n"

    final_data = {
        "course_title": course_title_final,
        "evaluation_scheme": all_events,
        "syllabus_topics": all_syllabus,
        "references": all_refs
    }
    
    yield json.dumps({"type": "done", "data": final_data}) + "\n"

async def main(pdf_files):
    all_pdf_events = []
    semester_profile = {"courses": []}

    for pdf_file in pdf_files:
        course_title, events, syllabus, refs = await process_pdf(pdf_file)
        
        course_data = {
            "course_title": course_title,
            "evaluation_scheme": events,
            "syllabus_topics": syllabus,
            "references": refs
        }
        semester_profile["courses"].append(course_data)
        
        if events:
            all_pdf_events.extend(events)

    # Save JSON Profile
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(semester_profile, f, indent=4)
    print(f"\n🎉 Successfully created {OUTPUT_JSON} with {len(semester_profile['courses'])} courses!")

    # Save ICS Calendar
    if all_pdf_events:
        save_ics(all_pdf_events, OUTPUT_ICS)
        print(f"🎉 Successfully created {OUTPUT_ICS} with {len(all_pdf_events)} events!")
    else:
        print("\n❌ No events extracted from any document.")

if __name__ == "__main__":
    files = [file3_path]
    asyncio.run(main(files))


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

