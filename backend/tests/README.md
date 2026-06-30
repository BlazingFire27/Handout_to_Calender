# Testing & Validation

To ensure high accuracy in classifying document pages and routing them efficiently, we have implemented a dedicated test suite for the **Router Node**. By utilizing `PydanticOutputParser`, the pipeline enforces strict JSON formatting. The model successfully analyzes various edge cases—including syllabus pages, administrative info, and tricky false-positive grading policies—correctly assigning the required action.

![Router Tests Passed](../../Images/test_router_passed.png)

### Vision Extractor Testing
We implemented a secondary dedicated test script (`test_vision.py`) specifically for the newly introduced **Vision Eval Extractor Node**. This ensures that the native Gemini Multimodal API perfectly transcribes complex tables containing spanned/merged cells and confusing date formats from the image without breaking existing text logic.

![Vision Node Tests Passed](../../Images/test_vision-text_hybrid_passed.png)

### AIGateway Multimodal Verification
To validate the **Zero-Cost Hybrid Architecture** for the current development phase, we rigorously tested `google/gemma-4-26b-a4b-it` via AIGateway. The script successfully extracted Base64 image payloads from PDFs, proving the model's multimodal capabilities on the free tier.

![AIGateway Vision Test](../../Images/test_aigateway.png)

### Deterministic Date Parsing (Bias Correction)
To eliminate LLM date hallucination (e.g., American models confusing DD/MM formats), the extraction and formatting steps have been entirely decoupled. The Vision Node now only extracts the raw text snippet (e.g., `'11/10/25'`). The Aggregator Node then utilizes the deterministic Python `dateparser` library, anchored to the current academic year, to calculate the correct ISO timestamp mathematically based on a global user preference (`user_date_format: "DMY"` vs `"MDY"`).

![Date Parser Tests Passed](../../Images/test_date_parser.png)

### State Persistence and Time Travel (MemorySaver)
To optimize API costs and performance, the LangGraph pipeline is integrated with a `MemorySaver` checkpointer. Every processed PDF page is assigned a unique `thread_id`. By persisting the graph's internal state, we enable LangGraph "Time Travel." This powerful feature allows the application to jump back to the state immediately following the expensive Vision LLM extraction, modify a user preference (e.g., changing the global date format from "DMY" to "MDY"), and mathematically regenerate the exact ICS schedule in **~0.01 seconds**—bypassing LLM API calls entirely.

![Time Travel Tests Passed](../../Images/test_memory_saver.png)

### Parallel Multi-Domain Routing (Fan-Out Architecture)
To support a rich interactive dashboard, the system now features **Multi-Domain Extraction**. Instead of just extracting exam dates, the LangGraph Text Router categorizes each PDF page into multiple domains simultaneously (`EVAL`, `SYLLABUS`, `REFERENCES`). The workflow then uses LangGraph's dynamic list-based routing to seamlessly trigger parallel Vision LLM nodes. This "fan-out" architecture allows us to rapidly extract Course Outlines (for Bunk Limit calculation) and Textbook titles (for Google Books API linking) all at the exact same time!

![Multi-Domain Routing Tests Passed](../../Images/test_multi_domain_router.png)

### Stateless Semester Profile Export (Zero-Database Architecture)
To maintain a strict privacy-first, zero-database backend, the Aggregator now compiles all the extracted data (Evaluation Events, Syllabus Topics with lecture hours, and Reference Books) across all PDFs into a single, structured `Semester_Profile.json` file inside the `output/` directory. This acts as a portable "Stateless Profile". The user can simply upload this tiny JSON file on their next visit to instantly restore their full dashboard and bunk calculators without needing any expensive LLM API calls.

![Stateless Semester Profile Tests Passed](../../Images/test_json_output.png)

### Parallel Metadata Enrichment (Google Books API)
To provide a rich academic experience, the pipeline automatically fetches high-resolution book covers and purchase links for all extracted reference materials. To bypass sequential bottlenecks, this is handled via a `ThreadPoolExecutor` that queries the **Google Books API** concurrently for all books. To prevent impacting the Gemini Vision quota, this feature is completely isolated, using a dedicated `GOOGLE_BOOK_API_KEY` authenticated via Google Cloud Console, effortlessly bypassing the standard unauthenticated IP limit for high-volume stateless usage.

![Parallel Book Fetching Tests Passed](../../Images/test_google_books.png)
