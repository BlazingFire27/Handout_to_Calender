import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("OPENAI_API_KEY")
API_BASE_URL = os.getenv("OPENAI_API_BASE", "https://openrouter.ai/api/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "x-ai/grok-4.1-fast:free")

if not API_KEY:
    raise ValueError("OPENAI_API_KEY is not set in environment variables.")