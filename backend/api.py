import os
import shutil
from fastapi import FastAPI, UploadFile, File, Form, Request
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from main import process_pdf

# Initialize Rate Limiter using client IP
limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title="Handout to Calendar API")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.post("/generate")
@limiter.limit("20/day", exempt_when=lambda: os.getenv("ENVIRONMENT") == "development")
async def generate_schedule(
    request: Request,
    file: UploadFile = File(...),
    date_format: str = Form("DMY")
):
    if not file.filename.endswith(".pdf"):
        return JSONResponse(status_code=400, content={"error": "File must be a PDF."})

    # Save uploaded file temporarily
    temp_file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(temp_file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        # Process the PDF using existing LangGraph logic
        course_title, events, syllabus, refs = process_pdf(
            pdf_file=temp_file_path,
            user_date_format=date_format
        )

        response_data = {
            "course_title": course_title,
            "evaluation_scheme": events,
            "syllabus_topics": syllabus,
            "references": refs
        }

        return JSONResponse(status_code=200, content=response_data)

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

    finally:
        # Clean up temporary file to prevent disk bloat
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
