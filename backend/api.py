import os
import asyncio
import shutil
import concurrent.futures
from contextlib import asynccontextmanager
from fastapi import FastAPI, UploadFile, File, Form, Request
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from main import process_pdf, process_pdf_stream

# Initialize Rate Limiter using client IP
limiter = Limiter(key_func=get_remote_address)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Overrides the default OS thread limit to 100 to prevent ThreadPool Starvation during heavy parallel PDF processing
    loop = asyncio.get_running_loop()
    loop.set_default_executor(concurrent.futures.ThreadPoolExecutor(max_workers=100))
    yield

app = FastAPI(title="Handout to Calendar API", lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Secure CORS Policy: Only allow the Next.js frontend to talk to this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://handout2calendar.vercel.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

    async def event_generator():
        try:
            async for chunk in process_pdf_stream(temp_file_path, date_format):
                yield chunk
        except asyncio.CancelledError:
            # Client disconnected mid-stream
            pass
        finally:
            # Clean up temporary file to prevent disk bloat
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)

    return StreamingResponse(event_generator(), media_type="application/x-ndjson")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
