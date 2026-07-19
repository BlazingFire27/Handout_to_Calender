import os

# Optional: If you want to use a local .env file instead of system variables, 
# uncomment the two lines below (make sure you have installed python-dotenv).
# from dotenv import load_dotenv
# load_dotenv()

# Using os.environ.get() explicitly as requested, bypassing local .env files
AICREDITS_API_KEY = os.environ.get("AICREDITS_API_KEY")
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
GOOGLE_BOOK_API_KEY = os.environ.get("GOOGLE_BOOK_API_KEY")
AIGATEWAY_API_KEY = os.environ.get("AIGATEWAY_API_KEY")
ENVIRONMENT = os.environ.get("ENVIRONMENT", "development")