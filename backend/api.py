import os
import asyncio
import shutil
import hashlib
import json
from contextlib import asynccontextmanager
from fastapi import FastAPI, UploadFile, File, Form, Request
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from main import process_pdf, process_pdf_stream
from upstash_redis.asyncio import Redis
from src.config import UPSTASH_REDIS_REST_URL, UPSTASH_REDIS_REST_TOKEN

# Initialize Redis client (Fail gracefully if keys are missing)
redis_client = None
if UPSTASH_REDIS_REST_URL and UPSTASH_REDIS_REST_TOKEN:
    try:
        redis_client = Redis(url=UPSTASH_REDIS_REST_URL, token=UPSTASH_REDIS_REST_TOKEN)
        print("✅ Connected to Upstash Redis Cache!")
    except Exception as e:
        print(f"⚠️ Failed to connect to Redis: {e}")
else:
    print("⚠️ Redis credentials not found. Caching will be disabled.")

# Initialize Rate Limiter using client IP
limiter = Limiter(key_func=get_remote_address)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # All LLM calls are now fully async (ainvoke) — no thread pool needed for API calls.
    # asyncio's default executor handles remaining sync file I/O (PyMuPDF).
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
@limiter.limit("3000/day", exempt_when=lambda: os.getenv("ENVIRONMENT") == "development")
async def generate_schedule(
    request: Request,
    file: UploadFile = File(...),
    date_format: str = Form("DMY"),
    force_refresh: bool = Form(False)
):
    if not file.filename.endswith(".pdf"):
        return JSONResponse(status_code=400, content={"error": "File must be a PDF."})

    # Generate SHA-256 hash for future caching
    file_content = await file.read()
    pdf_hash = hashlib.sha256(file_content).hexdigest()
    print(f"🔑 [CACHE] Generated Hash for {file.filename}: {pdf_hash}")
    
    # Reset file cursor so the file can be saved to disk correctly
    await file.seek(0)
    
    # ---------------- CACHE READ LOGIC ----------------
    if redis_client and not force_refresh:
        try:
            cached_data = await redis_client.get(pdf_hash)
            if cached_data:
                print(f"🎯 [CACHE HIT] Found {file.filename} in cache! Bypassing AI.")
                
                # Upstash Redis client might return a string or dict. 
                if isinstance(cached_data, str):
                    cached_data = json.loads(cached_data)

                # Return a StreamingResponse that instantly streams the cached JSON
                async def cached_generator():
                    yield json.dumps({"type": "init", "total_pages": 1}) + "\n"
                    yield json.dumps({"type": "progress", "message": "Cache Hit! Instantly loaded."}) + "\n"
                    yield json.dumps({"type": "done", "data": cached_data}) + "\n"
                
                return StreamingResponse(cached_generator(), media_type="application/x-ndjson")
        except Exception as e:
            print(f"⚠️ Redis read error: {e}")
    # ---------------------------------------------------

    # Save uploaded file temporarily
    temp_file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(temp_file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    async def event_generator():
        try:
            async for chunk in process_pdf_stream(temp_file_path, date_format):
                yield chunk
                # ---------------- CACHE WRITE LOGIC ----------------
                try:
                    chunk_data = json.loads(chunk.strip())
                    if chunk_data.get("type") == "done":
                        final_data = chunk_data.get("data")
                        if redis_client and final_data:
                            # Prevent caching if the AI failed (e.g., out of budget) or returned empty data
                            is_empty = (
                                not final_data.get("evaluation_scheme") and 
                                not final_data.get("syllabus_topics") and 
                                not final_data.get("references")
                            )
                            
                            if not is_empty:
                                await redis_client.set(pdf_hash, json.dumps(final_data))
                                print(f"💾 [CACHE WRITE] Saved {file.filename} to Redis!")
                            else:
                                print(f"⚠️ [CACHE SKIP] {file.filename} returned empty data. Not caching to allow future retries.")
                except Exception as cache_err:
                    print(f"⚠️ Redis write error: {cache_err}")
                # ----------------------------------------------------
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
