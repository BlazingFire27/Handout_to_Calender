import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.utils import predefined

def test_date_parser():
    print("Testing Date Bias Correction with dateparser...\n")

    # Test Case 1: Indian/British format (DMY)
    start, end = predefined("11/10/2025", "10:00 AM", "MidSem Exam", user_format="DMY")
    print(f"DMY Output (11/10/2025): {start}")
    assert start.startswith("2025-10-11"), "Failed DMY parsing! Should be Oct 11"

    # Test Case 2: American format (MDY)
    start, end = predefined("11/10/2025", "10:00 AM", "MidSem Exam", user_format="MDY")
    print(f"MDY Output (11/10/2025): {start}")
    assert start.startswith("2025-11-10"), "Failed MDY parsing! Should be Nov 10"
    
    # Test Case 3: Fuzzy Text
    start, end = predefined("15-Sept", "10:00 AM", "Quiz", user_format="DMY")
    print(f"Fuzzy Output (15-Sept): {start}")
    assert "-09-15" in start, "Failed Fuzzy Text parsing!"
    
    # Test Case 4: Another Fuzzy Case
    start, end = predefined("10th Nov 25", "10:00 AM", "Quiz", user_format="DMY")
    print(f"Fuzzy Output (10th Nov 25): {start}")
    assert "2025-11-10" in start, "Failed Fuzzy Text parsing!"

    print("\nAll Date Parser Tests Passed! Deterministic parser is mathematically sound.")

if __name__ == "__main__":
    test_date_parser()
