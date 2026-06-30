# Multi Agent for Handout to Calender
This repository contains a Gen AI project focused on an AI agent for automating the process of adding to Calender from University Course Handouts. 
The project leverages the LangGraph, OpenAI wrapper etc to create the bot.

## Technologies
Modules used:
1. LangGraph (for StateGraph)
2. langchain_openai (for OpenRouter wrapper)
3. langchain_google_genai (for Google Gemini native wrapper)
4. PyMuPDF (fitz) for PDF-to-Image rendering
5. Datetime and Pydantic (BaseModel and Field)
4. _Gradio User Interface (SOON...)_

## Folder Structure
```text
📦 Handout To Calender
 ┣ 📂 backend/
 ┃ ┣ 📂 Handouts/        # Test PDFs
 ┃ ┣ 📂 src/             # LangGraph Core Logic
 ┃ ┣ 📂 tests/           # Pytest API & Unit Tests
 ┃ ┣ 📜 api.py           # FastAPI Server Entrypoint
 ┃ ┣ 📜 main.py          # Legacy PDF Processor
 ┃ ┗ 📜 requirements.txt # Python Dependencies
 ┣ 📂 frontend/          # (Planned) Next.js Dashboard
 ┣ 📂 Images/            # Documentation Assets
 ┣ 📜 .env               # API Keys
 ┗ 📜 README.md
```

## Future ideas:
1. Gradio UI implementation
2. Hosting in Huggingface
3. Api cost management

## .env contents:
Steps:
1. The `.env` file must be placed in the root directory of this project like shown below

   <p align="center">
     <img src="Images/.env_placing.png" alt=".env placing">
   </p>
2. The file contains two keywords required for the unified AIgateway architecture:
- AIGATEWAY_API_KEY (Your AIgateway API Key)
- GOOGLE_BOOK_API_KEY (Dedicated Google Cloud key for parallel metadata fetching) </br> </br>
NOTE that we use **aigateway.sh** with **openai/gpt-oss-20b** for routing, and **google/gemini-2.5-flash-lite** for multimodal vision extraction.

*If you are running this locally on the free tier without an AIgateway account, you can use the commented out fallback block in `src/graph.py` which requires `GOOGLE_API_KEY` and `OPENAI_API_KEY`.*

## NOTE (VERY IMPORTANT):
- Make sure to use virtual environment so that the modules used in this particular project doesn't affect other projects
1. TO CREATE THE ENVIRONMENT: </br>
`python3 -m venv venv` </br>
2. TO ACTIVATE THE ENVIRONMENT: </br>
Windows_POWERSHELL BASED TERMINAL = `venv\Scripts\activate.ps1` </br>
Windows_CMD BASED TERMINAL = `venv\Scripts\activate.bat` </br>
MAC = `source venv/bin/activate`

NOW,
ONCE ENVIRONMENT is ACTIVATED </br>
- RUN THE **REQUIREMENTS.TXT** FILE TO DOWNLOAD ALL THE REQUIRED MODULES using `pip install -r requirements.txt`

## Project Overview
- The core of the project is to automate the process of finding the exam dates, convert into ics file which can be used in adding them to calender. </br>
- The python file is included in this repository provides a detailed walkthrough of the model implementation. </br>
- The multimodal graph takes multiple handout pdfs as input, processing them page by page. It simultaneously extracts the raw text and renders the page as a Base64 Image. </br>

- The **Router Node** (Text-based) analyzes the page text and outputs a command to either "extract" the contents of this page or "skip" it.
- This is because the evaluation components of the course will be provided in any one of the pages and we don't need to waste compute power by checking for all the pages.
- The **Vision Eval Extractor Node** (Multimodal-based) takes over if an evaluation scheme is detected. It takes the *Image* of the page and natively extracts complex tables, fetching the Date, Time, Format (Open/Closed Book), and Weightage simultaneously.
- The **Aggregator Node** combines the perfect JSON results obtained from the vision model and processes complex date logic into ISO formats before merging them.

### Planned Upgraded Architecture
This flowchart represents the finalized architecture that is actively being built. It introduces parallel vision extraction (for handling syllabus and admin data simultaneously) and a robust `MemorySaver` checkpointer for state persistence and fallback capabilities.

```mermaid
flowchart TD
    Checkpointer[(MemorySaver State Persistence)]
    GoogleBooks((Google Books API))
    JSONOut[[Semester_Profile.json]]

    START([START]) --> RouterNode["router_node (Classifies text)"]

    RouterNode --> RouteDecision{"route_decision()"}

    RouteDecision -- "EVAL" --> VisionEval["eval_extractor_node (Dates & Weights)"]
    RouteDecision -- "SYLLABUS" --> VisionSyllabus["syllabus_extractor_node (Course Topics)"]
    RouteDecision -- "REFERENCES" --> VisionReference["reference_extractor_node (Textbooks)"]
    RouteDecision -- "SKIP" --> END([END])

    VisionEval --> AggregatorNode["aggregator_node (Merges Data)"]
    VisionSyllabus --> AggregatorNode
    VisionReference --> AggregatorNode

    AggregatorNode --> PostProcess{"enrich_refs_parallel()"}
    PostProcess -. "Fetches Covers & Links" .-> GoogleBooks
    PostProcess --> JSONOut
    JSONOut --> END

    %% Checkpointer connections to show state saving
    RouterNode -. "Saves State" .-> Checkpointer
    VisionEval -. "Saves State" .-> Checkpointer
    VisionSyllabus -. "Saves State" .-> Checkpointer
    VisionReference -. "Saves State" .-> Checkpointer
    AggregatorNode -. "Saves Final State" .-> Checkpointer
```

## Testing & Validation
To ensure high accuracy in classifying document pages and routing them efficiently, we have implemented a dedicated test suite for the **Router Node**. By utilizing `PydanticOutputParser`, the pipeline enforces strict JSON formatting. The model successfully analyzes various edge cases—including syllabus pages, administrative info, and tricky false-positive grading policies—correctly assigning the required action.

![Router Tests Passed](Images/test_router_passed.png)

### Vision Extractor Testing
We implemented a secondary dedicated test script (`test_vision.py`) specifically for the newly introduced **Vision Eval Extractor Node**. This ensures that the native Gemini Multimodal API perfectly transcribes complex tables containing spanned/merged cells and confusing date formats from the image without breaking existing text logic.

![Vision Node Tests Passed](Images/test_vision-text_hybrid_passed.png)

### AIGateway Multimodal Verification
To validate the **Zero-Cost Hybrid Architecture** for the current development phase, we rigorously tested `google/gemma-4-26b-a4b-it` via AIGateway. The script successfully extracted Base64 image payloads from PDFs, proving the model's multimodal capabilities on the free tier.

![AIGateway Vision Test](Images/test_aigateway.png)

### Deterministic Date Parsing (Bias Correction)
To eliminate LLM date hallucination (e.g., American models confusing DD/MM formats), the extraction and formatting steps have been entirely decoupled. The Vision Node now only extracts the raw text snippet (e.g., `'11/10/25'`). The Aggregator Node then utilizes the deterministic Python `dateparser` library, anchored to the current academic year, to calculate the correct ISO timestamp mathematically based on a global user preference (`user_date_format: "DMY"` vs `"MDY"`).

![Date Parser Tests Passed](Images/test_date_parser.png)

### State Persistence and Time Travel (MemorySaver)
To optimize API costs and performance, the LangGraph pipeline is integrated with a `MemorySaver` checkpointer. Every processed PDF page is assigned a unique `thread_id`. By persisting the graph's internal state, we enable LangGraph "Time Travel." This powerful feature allows the application to jump back to the state immediately following the expensive Vision LLM extraction, modify a user preference (e.g., changing the global date format from "DMY" to "MDY"), and mathematically regenerate the exact ICS schedule in **~0.01 seconds**—bypassing LLM API calls entirely.

![Time Travel Tests Passed](Images/test_memory_saver.png)

### Parallel Multi-Domain Routing (Fan-Out Architecture)
To support a rich interactive dashboard, the system now features **Multi-Domain Extraction**. Instead of just extracting exam dates, the LangGraph Text Router categorizes each PDF page into multiple domains simultaneously (`EVAL`, `SYLLABUS`, `REFERENCES`). The workflow then uses LangGraph's dynamic list-based routing to seamlessly trigger parallel Vision LLM nodes. This "fan-out" architecture allows us to rapidly extract Course Outlines (for Bunk Limit calculation) and Textbook titles (for Google Books API linking) all at the exact same time!

![Multi-Domain Routing Tests Passed](Images/test_multi_domain_router.png)

### Stateless Semester Profile Export (Zero-Database Architecture)
To maintain a strict privacy-first, zero-database backend, the Aggregator now compiles all the extracted data (Evaluation Events, Syllabus Topics with lecture hours, and Reference Books) across all PDFs into a single, structured `Semester_Profile.json` file inside the `output/` directory. This acts as a portable "Stateless Profile". The user can simply upload this tiny JSON file on their next visit to instantly restore their full dashboard and bunk calculators without needing any expensive LLM API calls.

![Stateless Semester Profile Tests Passed](Images/test_json_output.png)

### Parallel Metadata Enrichment (Google Books API)
To provide a rich academic experience, the pipeline automatically fetches high-resolution book covers and purchase links for all extracted reference materials. To bypass sequential bottlenecks, this is handled via a `ThreadPoolExecutor` that queries the **Google Books API** concurrently for all books. To prevent impacting the Gemini Vision quota, this feature is completely isolated, using a dedicated `GOOGLE_BOOK_API_KEY` authenticated via Google Cloud Console, effortlessly bypassing the standard unauthenticated IP limit for high-volume stateless usage.

![Parallel Book Fetching Tests Passed](Images/test_google_books.png)

## Procedure to building the model
### Data processing
Get the pdfs as input, extract both the pdf text and render the page as an image using PyMuPDF (fitz), returning them simultaneously for the Graph.
```python
import fitz # PyMuPDF
import base64

raw_pages = []
doc = fitz.open(pdf_file)
for i in range(len(doc)):
    page = doc[i]
    text = page.get_text()
    
    pix = page.get_pixmap(dpi=150)
    img_bytes = pix.tobytes("png")
    b64_image = base64.b64encode(img_bytes).decode("utf-8")
    
    raw_pages.append((i+1, text, b64_image))
```
Code Credits = Thank you [https://github.com/jsvine/pdfplumber](https://github.com/jsvine/pdfplumber)

### Data extraction
- From the first page, always extract the **course title** and have it as global variable until the entire pdf is processed
- Each page contents enters **router node** and is either skipped: if no contents related to exams are present or extracted: the contents of evaluation components

### Data Collection
- The **Vision Eval Extractor Node** processes the image using `gemini-2.5-flash` to extract Event Name, Date, Time, Format, and Weightage in a single cohesive pass. This eliminates misalignments from text-based parsers.

### Aggregating
To bring together all the collected data and aggregate in a particular json format
```
entry = {
    "Subject": full_title,
    "Event_Name": final_event_name,
    "Start_DateTime": final_start,
    "End_DateTime": final_end,
    "Format": fmt,
    "Weightage": wgt,
    "Raw_Time_String": t["time_raw"]
}
```

## Note: 
User can input multiple pdfs at once

## OUTPUT CLI
![CLI OUTPUT](Images/output.png)

- We can clearly see that for page 3 of both Electrical Machines and Digital Design Courses took longer time clearly shows that those are the two pages with the contents of exams

## TO ADD TO GOOGLE CALENDER
- Import the Combined_Exam_Schedule.ics file into the calender and **BOOM** there you go all the events are now PRESENT

---

## 🗄️ Archive: Old Architecture (Scrapped)
*Note: This was the original V1 architecture that used brittle, parallel text-extraction LLMs. It has officially been deprecated and replaced by the native Multimodal Vision Graph shown above.*

![Old Graph Structure (Scrapped)](Images/graph_structure.png)

### Why it was scrapped:
1. **Brittle Aggregation:** Splitting the "Time" and "Details" into two completely separate LLM calls required fuzzy string matching in the Aggregator to stitch them back together. If one node called an event "Mid-Sem" and the other called it "Mid Semester", the merge would fail entirely.
2. **Tabular Hallucinations:** Text-based parsers like `pdfplumber` destroy the visual layout of complex tables (merged cells, wrapped text, and column alignments). Feeding this scrambled text to an LLM caused massive hallucinations when trying to figure out which weightage belonged to which assignment. Switching to the Vision Graph solved this instantly.
