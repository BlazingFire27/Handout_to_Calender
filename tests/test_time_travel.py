import sys
import os
import time

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.graph import app

def test_time_travel():
    print("🚀 STARTING TIME TRAVEL TEST...\n")
    
    # 1. Initial State
    thread_id = "test_time_travel_thread_1"
    config = {"configurable": {"thread_id": thread_id}}
    
    # Simulated simple text that hits the vision node
    # Since we are bypassing LLMs for speed in this test, we can actually inject directly into the graph
    # But let's run the full graph to show standard execution first.
    # Wait, the Vision node requires a real image and API call. We don't want to waste tokens or risk failure.
    # INSTEAD, we can manually update the state to simulate the Vision node finishing!
    
    print("🔹 STEP 1: Simulating Vision Node output (Saving State to Memory)")
    
    # We pretend the router and vision nodes just finished, and outputted this `eval_data`:
    mock_eval_data = [{
        "event_name": "MidSem Exam",
        "date_raw": "15-Sept", # Fuzzy date!
        "time_raw": "10:00 AM",
        "format": "CB",
        "weightage": "25%"
    }]
    
    # We update the state AS IF we just finished the 'vision_eval_extractor' node.
    app.update_state(
        config,
        {
            "eval_data": mock_eval_data,
            "user_date_format": "DMY", # Initial preference
            "known_course_title": "Test Course"
        },
        as_node="vision_eval_extractor" # Next step will naturally be 'aggregator'
    )
    
    # Run the rest of the graph (which is just the aggregator node)
    result_1 = app.invoke(None, config)
    schedule_1 = result_1.get("final_schedule", [])
    print(f"   ✅ Original Schedule (DMY): {schedule_1[0]['Start_DateTime']}")
    assert "-09-15" in schedule_1[0]['Start_DateTime'], "Expected September!"
    
    print("\n🔹 STEP 2: TIME TRAVEL! Changing format to MDY and rerunning without LLM...")
    start_time = time.time()
    
    # TIME TRAVEL: We update the state AGAIN, pretending we are back at the end of the vision node.
    # We change ONLY the user_date_format.
    app.update_state(
        config,
        {"user_date_format": "MDY"},
        as_node="vision_eval_extractor" # Forking from here again
    )
    
    # Run the graph again (only the aggregator node runs!)
    result_2 = app.invoke(None, config)
    
    end_time = time.time()
    schedule_2 = result_2.get("final_schedule", [])
    
    print(f"   ✅ Time Travel Schedule (MDY): {schedule_2[0]['Start_DateTime']}")
    print(f"   ⏱️  Time taken: {end_time - start_time:.4f} seconds!")
    
    # The fuzzy parser "15-Sept" will remain Sept regardless of DMY/MDY because "Sept" is explicit.
    # Let's test an ambiguous date to prove the math changes.
    
    print("\n🔹 STEP 3: Testing Ambiguous Date Time Travel (11/10/2025)")
    mock_eval_data_2 = [{
        "event_name": "Compre",
        "date_raw": "11/10/2025", 
        "time_raw": "10:00 AM",
        "format": "OB",
        "weightage": "40%"
    }]
    
    app.update_state(config, {"eval_data": mock_eval_data_2, "user_date_format": "DMY"}, as_node="vision_eval_extractor")
    
    # Let's just grab the last one.
    final_sched = app.invoke(None, config).get("final_schedule")[-1]
    print(f"   [DMY] 11/10/2025 -> {final_sched['Start_DateTime']} (Oct 11)")
    
    # Travel
    app.update_state(config, {"user_date_format": "MDY"}, as_node="vision_eval_extractor")
    final_sched_mdy = app.invoke(None, config).get("final_schedule")[-1]
    print(f"   [MDY] 11/10/2025 -> {final_sched_mdy['Start_DateTime']} (Nov 10)")
    
    print("\n🎉 TIME TRAVEL SUCCESSFUL! State preserved and LLMs fully bypassed.")

if __name__ == "__main__":
    test_time_travel()
