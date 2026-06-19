import time
import base64
import fitz # PyMuPDF
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
        return None, "Error processing PDF"

    course_title_final = ""
    if raw_pages:
        try:
            title = extract_course_title(raw_pages[0][1]) # Text-based title extraction
            if title:
                course_title_final = title
                print(f"Extracted Course Title: {course_title_final}")
            else:
                print("No Course Title extracted.")
                course_title_final = "Unknown Course"

        except Exception as e:
            print(f"Course Title Extraction error: {e}")

    all_events = []

    for page_num, text, b64_image in raw_pages:
        print(f"Processing Page {page_num}...")
        start_time = time.time()
        try:
            initial_state = {
                'raw_text': text,
                'page_image_b64': b64_image,
                'known_course_title': course_title_final
            }

            result = app.invoke(initial_state)
            events = result.get("final_schedule", [])
            all_events.extend(events)
            if events:
                print(f"  ✅ Extracted {len(events)} events from Page {page_num}.")
            else:
                print(f"  ⏭️ Skipped Page {page_num}.")

        except Exception as e:
            print(f"  🔥 Error on Page {page_num}: {e}")
        
        end_time = time.time()
        print(f"Time taken: {end_time - start_time:.2f} seconds.\n")

    return all_events

def main(pdf_files):
    all_pdf_events = []

    for pdf_file in pdf_files:
        events = process_pdf(pdf_file)
        if events:
            all_pdf_events.extend(events)

    if all_pdf_events:
        save_ics(all_pdf_events, OUTPUT_ICS)
        print(f"\n🎉 Successfully created {OUTPUT_ICS} with {len(all_pdf_events)} events!")
    else:
        print("\n❌ No events extracted from any document.")

if __name__ == "__main__":
    files = [file1_path, file2_path]
    main(files)
