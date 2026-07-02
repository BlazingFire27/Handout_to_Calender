import os

# Using os.environ.get() explicitly as requested, bypassing local .env files
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
GOOGLE_BOOK_API_KEY = os.environ.get("GOOGLE_BOOK_API_KEY")
AIGATEWAY_API_KEY = os.environ.get("AIGATEWAY_API_KEY")
ENVIRONMENT = os.environ.get("ENVIRONMENT", "development")