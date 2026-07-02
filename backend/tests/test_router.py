import os
import sys
import time

# Add the parent directory to sys.path so we can import from src
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.graph import router_node
from src.schema import State

# Define edge-case test scenarios
test_cases = [
    {
        "name": "1. Clear Evaluation Schedule",
        "text": """
        Evaluation Scheme:
        1. Mid-Sem Exam. 11/10/2025. 4-5:30 PM. Closed Book. 25%.
        2. Comprehensive Examination. 16/12/2025. FN. Open Book. 35%.
        """,
        "expected_in": ["EVAL"],
        "must_not_have": []
    },
    {
        "name": "2. Clear Course Plan (Syllabus)",
        "text": """
        Course Plan:
        Lect. No. | Topic | Learning objectives | Book reference
        1 | Introduction to Digital systems | Binary logic | 1.1, 1.9
        2-3 | Boolean Algebra | Canonical forms | 2.2-2.7
        """,
        "expected_in": ["SYLLABUS"],
        "must_not_have": ["EVAL"]
    },
    {
        "name": "3. Clear Admin Information",
        "text": """
        Instructor-in-charge: Sarang Dhongdi
        Team of Instructors: Tushar, Akshay, Debasis
        Chamber consultation hours: To be announced in class.
        Make-up Policy: Application for Make-up will be considered only in Genuine cases.
        """,
        "expected_in": ["ADMIN"],
        "must_not_have": ["EVAL"]
    },
    {
        "name": "4. Mixed Page (EVAL + ADMIN)",
        "text": """
        Evaluation Scheme:
        Mid-Sem Exam | 25% | 11/10/2025
        Comprehensive Examination | 35% | 16/12/2025

        Make-up Policy:
        No make-up will be given for quizzes.

        Chamber consultation hours:
        Wednesdays 4 PM to 5 PM.
        """,
        "expected_in": ["EVAL", "ADMIN"],
        "must_not_have": []
    },
    {
        "name": "5. Irrelevant / Introductory (SKIP)",
        "text": """
        Course Description: Boolean Algebra & logic minimization; combinational logic circuits.
        Scope and Objective: This is a foundation course that provides students with a fundamental knowledge.
        Textbook: M.Morris Mano, "Digital Design", Pearson.
        """,
        "expected_in": ["SKIP"],
        "must_not_have": ["EVAL", "ADMIN"]
    },
    {
        "name": "6. False Positive Policy Check (No Schedule)",
        "text": """
        Grading notice:
        All students registered in the course are expected to appear for all evaluation components. 
        Absence in any evaluation components without prior consent may present grounds for awarding NC.
        """,
        "expected_in": ["ADMIN", "SKIP"], 
        "must_not_have": ["EVAL"] # Crucial: Should NOT classify as EVAL just because the word "evaluation" is there
    }
]

def run_tests():
    print("🚀 STARTING ROUTER NODE ISOLATION TESTS...\n")
    
    for case in test_cases:
        print(f"🔹 Test: {case['name']}")
        
        # Mock LangGraph state
        state = State(
            raw_text=case["text"],
            classification=[],
            known_course_title="Test Course",
            time_data=[],
            details_data=[],
            final_schedule=[]
        )
        
        try:
            # Run ONLY the router node
            result = router_node(state)
            categories = result.get("classification", [])
            
            print(f"   📥 Input snippet: '{case['text'].strip()[:55]}...'")
            print(f"   📤 Output:        {categories}")
            
            # Validation logic
            has_expected = any(expected in categories for expected in case['expected_in'])
            has_forbidden = any(forbidden in categories for forbidden in case['must_not_have'])
            
            if has_forbidden:
                print(f"   ❌ FAILED: Output contained forbidden category from {case['must_not_have']}")
            elif has_expected:
                print("   ✅ PASSED")
            else:
                # If a completely irrelevant page is classified as syllabus instead of skip, we might warn
                print(f"   ⚠️ WARNING/FAILED: Expected one of {case['expected_in']} but got {categories}")
                
        except Exception as e:
            print(f"   🔥 ERROR: {e}")
            
        print("-" * 60)
        
        # Add a delay between tests to prevent hitting Free Tier burst rate limits
        time.sleep(4)

if __name__ == "__main__":
    run_tests()
