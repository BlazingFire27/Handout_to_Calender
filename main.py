import time
import pdfplumber

from src import app

# def process_pdf(pdf_file):
#     if pdf_file is None:
#         return None, "Upload the PDF please"
    
#     all_events = []

#     try:
#         with pdfplumber.open(pdf1_path) as pdf1:
#             print(f"Total pages = {len(pdf1.pages)}")

#         for i in range(len(pdf1.pages)):
#             page = pdf1.pages[i]
#             raw_text = page.extract_text()

#             print("="*50)
#             print(f"We have page {i+1}")
#             print("="*50)

#             print(raw_text)
#             print("\n" + "="*50 + "\n")


test_cases = [
    {
        "id": 1,
        "desc": "Standard Midsem (Explicit Time)",
        "text": """
        BITS PILANI - HYDERABAD CAMPUS
        COURSE HANDOUT: DIGITAL DESIGN (CS F215)
        Evaluation Scheme:
        1. Mid-Sem Exam. 11/10/2025. 4-5:30 PM. Closed Book. 25%.
        """
    },
    {
        "id": 2,
        "desc": "Compre Exam (FN Code)",
        "text": """
        COURSE: OPERATING SYSTEMS
        Evaluation:
        Comprehensive Exam. 16/12/2025. FN. Open Book. 35%.
        """
    },
    {
        "id": 3,
        "desc": "Composite Key (Two Courses on One Page)",
        "text": """
        NOTICE BOARD - EXAM UPDATES
        1. Course: MICROPROCESSORS (CS F241)
           - Mid-Sem Exam. Date: 09/10/2025. Time: 9-10:30 AM. Weightage: 30%.
        2. Course: DATABASE SYSTEMS (CS F212)
           - Mid-Sem Exam. Date: 11/10/2025. Time: 2-3:30 PM. Weightage: 25%.
        """
    },
    {
        "id": 4,
        "desc": "Time TBA (ISO Date Fix Check)",
        "text": """
        COURSE: MACHINE LEARNING (CS F429)
        Evaluation:
        1. Project Presentation. Date: 20/11/2025. Time: To be announced later. Format: Open. 15%.
        """
    },
    {
        "id": 5,
        "desc": "Hyphenated Date & AN Code",
        "text": """
        COURSE: COMPILER CONSTRUCTION
        Evaluation:
        Comprehensive Exam. 15-12-2025. AN. Closed Book. 40 Marks.
        """
    },
    {
        "id": 6,
        "desc": "Late Evening Quiz",
        "text": """
        COURSE: COMPUTER ARCHITECTURE
        Quiz 1. Date: 05/09/2025. Time: 5:00 PM - 6:00 PM. Format: CB. Weight: 10%.
        """
    },
    {
        "id": 7,
        "desc": "Hidden Table in Noise",
        "text": """
        COURSE: GENERAL BIOLOGY
        Textbook: Campbell. Attendance: Mandatory.
        Evaluation Scheme: 
        Mid-Sem Exam. 10/10/2025. 11 AM. CB. 30%.
        Library Rules: Silence please.
        """
    },
    {
        "id": 8,
        "desc": "Exam Announced, Format Missing",
        "text": """
        COURSE: QUANTUM PHYSICS
        Mid-Sem Exam: 14/10/2025, 9:00 AM.
        (Details on weightage will be shared in class).
        """
    },
    {
        "id": 9,
        "desc": "Event Normalization ('Final Exam' -> 'Comprehensive')",
        "text": """
        COURSE: ECONOMICS (ECON F211)
        Assessment:
        Final Exam. Date: 20/12/2025. Time: FN. Format: OB. Weight: 35%.
        """
    },
    {
        "id": 10,
        "desc": "2-Digit Year & Footer Table",
        "text": """
        COURSE: CHEMISTRY
        ... content ...
        (Bottom of Page 4)
        | Midsem | 12/10/25 | 2 PM | CB | 25% |
        """
    }
]

# LOOP
def run_tests():
    print(f"🚀 STARTING LOGIC TEST SUITE ({len(test_cases)} CASES)...\n")
    
    for case in test_cases:
        print(f"🔹 CASE {case['id']}: {case['desc']}")
        start_time = time.time()
        
        try:
            result = app.invoke({"raw_text": case['text']})
            
            events = result.get("final_schedule", [])
            
            if not events:
                print("   ❌ No events found (Router skipped or Extraction failed)")
            else:
                for ev in events:
                    print(f"   ✅ Subject: {ev['Subject']}")
                    print(f"      Time:    {ev['Start_DateTime']} -> {ev['End_DateTime']}")
                    print(f"      Format:  {ev['Format']} | Weight: {ev['Weightage']}")
                    print(f"      Raw:     '{ev['Raw_Time_String']}'")
        
        except Exception as e:
            print(f"   🔥 CRASH: {e}")
            
        print(f"   ⏱️  Taken: {time.time() - start_time:.2f}s")
        print("-" * 50)

if __name__ == "__main__":
    run_tests()