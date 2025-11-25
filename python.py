from ics import Calendar, Event
import json

def convert_json_to_ics(exam_schedule_json, output_filename="university_schedule.ics"):
    c = Calendar()

    for item in exam_schedule_json:
        e = Event()
        
        e.name = f"{item['Subject']} - {item['Event_Name']}"
        
        e.begin = item['Start_DateTime'] 
        e.end = item['End_DateTime']
        
        description_text = (
            f"Format: {item['Format']}\n"
            f"Weightage: {item['Weightage']}\n"
            f"Note: Check handout for room allocation."
        )
        e.description = description_text
        
        c.events.add(e)

    with open(output_filename, 'w') as f:
        f.writelines(c.serialize())
    
    print(f"Success! {output_filename} created.")

# Test case data
final_output = [
  {
    "Subject": "Digital Design",
    "Event_Name": "Mid-Sem Exam",
    "Start_DateTime": "2025-10-11T16:00:00",
    "End_DateTime": "2025-10-11T17:30:00",
    "Format": "CB",
    "Weightage": "25%"
  },
  {
    "Subject": "Digital Design",
    "Event_Name": "Comprehensive Examination",
    "Start_DateTime": "2025-12-16T10:00:00", 
    "End_DateTime": "2025-12-16T13:00:00",
    "Format": "CB",
    "Weightage": "35%"
  }
]

convert_json_to_ics(final_output)