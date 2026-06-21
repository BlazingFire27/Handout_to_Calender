import sys
import os
import time

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.graph import router_node

test_cases = [
    {
        "id": 1,
        "desc": "Classic Eval Only",
        "expected": ["EVAL"],
        "text": """
        EVALUATION SCHEME
        1. Mid-Semester Test: 10/10/2025, 2:00 PM. Open Book. Weightage: 30%
        2. Comprehensive Exam: 15/12/2025. Closed Book. Weightage: 40%
        """
    },
    {
        "id": 2,
        "desc": "Classic Syllabus Only",
        "expected": ["SYLLABUS"],
        "text": """
        COURSE PLAN
        Module 1: Introduction to Operating Systems. (Lectures: 4)
        Module 2: Process Management and Threads. (Lectures: 8)
        Module 3: Memory Management and Virtual Memory. (Lectures: 6)
        """
    },
    {
        "id": 3,
        "desc": "Classic References Only",
        "expected": ["REFERENCES"],
        "text": """
        READING MATERIALS
        Textbooks:
        T1. Silberschatz, Galvin, and Gagne, "Operating System Concepts", 10th Edition.
        Reference Books:
        R1. W. Stallings, "Operating Systems: Internals and Design Principles".
        """
    },
    {
        "id": 4,
        "desc": "Hybrid (Eval + Syllabus)",
        "expected": ["EVAL", "SYLLABUS"],
        "text": """
        COURSE PLAN
        Module 1: Intro to AI (4 Lectures)
        Module 2: Neural Networks (8 Lectures)

        EVALUATION COMPONENTS
        Mid-Sem Exam - 15/10/2025 - 30%
        """
    },
    {
        "id": 5,
        "desc": "Hybrid (Syllabus + References)",
        "expected": ["SYLLABUS", "REFERENCES"],
        "text": """
        Module 5: Advanced Topics (4 Lectures)
        End of Course Plan.

        TEXTBOOKS:
        1. Artificial Intelligence: A Modern Approach by Stuart Russell
        """
    },
    {
        "id": 6,
        "desc": "Pure Noise / Skip",
        "expected": ["SKIP"],
        "text": """
        ACADEMIC HONESTY POLICY
        Students are expected to abide by the university's honor code.
        Any form of cheating or plagiarism will result in strict disciplinary action.
        Make-up policy: Medical emergencies require a doctor's certificate within 48 hours.
        """
    },
    {
        "id": 7,
        "desc": "False Positive Eval (No Dates/Tables)",
        "expected": ["SKIP"],
        "text": """
        GRADING PHILOSOPHY
        Students will be evaluated throughout the semester based on their participation, 
        understanding of the core concepts, and overall dedication. 
        Note: The actual evaluation scheme and dates will be decided later.
        """
    },
    {
        "id": 8,
        "desc": "False Positive References (No Book Titles)",
        "expected": ["SKIP"],
        "text": """
        ADDITIONAL RESOURCES
        Please refer to the course portal on Canvas for more references and notes.
        The library also has several good reference materials you can borrow.
        """
    },
    {
        "id": 9,
        "desc": "The 'All-in-One' Dense Page",
        "expected": ["EVAL", "SYLLABUS", "REFERENCES"],
        "text": """
        COURSE SUMMARY
        Module 1: Basic Physics (5 Lectures)
        Module 2: Quantum Mechanics (10 Lectures)

        Textbooks:
        T1. Fundamentals of Physics by Halliday & Resnick

        Assessment:
        Quiz 1: 10/09/2025 (10%)
        Mid-Sem: 15/10/2025 (30%)
        """
    },
    {
        "id": 10,
        "desc": "Syllabus with Dates Trap (No Exams)",
        "expected": ["SYLLABUS"],
        "text": """
        LECTURE SCHEDULE
        Lecture 1 (01/08/2025): Introduction to Databases
        Lecture 2 (03/08/2025): Relational Algebra
        Lecture 3 (05/08/2025): SQL Queries
        (Note: No exams are listed here, just the daily schedule)
        """
    }
]

def run_router_tests():
    print(f"🚀 STARTING MULTI-DOMAIN ROUTER TEST SUITE ({len(test_cases)} CASES)...\n")
    
    passed = 0
    
    for case in test_cases:
        print(f"🔹 CASE {case['id']}: {case['desc']}")
        start_time = time.time()
        
        try:
            # We directly invoke the router node to test classification logic
            result = router_node({"raw_text": case['text']})
            output_categories = set(result.get("classification", []))
            expected_categories = set(case['expected'])
            
            if output_categories == expected_categories:
                print(f"   ✅ PASS: Correctly classified as {list(output_categories)}")
                passed += 1
            else:
                print(f"   ❌ FAIL: Expected {list(expected_categories)}, but got {list(output_categories)}")
                
        except Exception as e:
            print(f"   🔥 CRASH: {e}")
            
        print(f"   ⏱️  Taken: {time.time() - start_time:.2f}s")
        print("-" * 50)
        
    print(f"\n🎯 FINAL SCORE: {passed}/{len(test_cases)} Passed!")

if __name__ == "__main__":
    run_router_tests()
