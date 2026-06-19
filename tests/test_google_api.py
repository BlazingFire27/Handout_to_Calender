# from google import genai

# # Explicitly pass the key directly into the client initializer
# client = genai.Client(api_key="PASTE YOUR API KEY HERE")

# try:
#     response = client.models.generate_content(
#         model='gemini-2.5-flash',
#         contents='Hello, say test!',
#     )
#     print("SUCCESS! Output:", response.text)
# except Exception as e:
#     print("FAILED! Error details:")
#     print(e)

import os
from langchain_google_genai import ChatGoogleGenerativeAI

# 1. Force safety defaults directly into the system environment block
os.environ["GOOGLE_API_KEY"] = "PASTE YOUR API KEY HERE"

# 2. Strict model definition with safety/telemetry constraints disabled
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash", # Explicitly map 1.5 flash to avoid fallback loops
    temperature=0.7,
    max_retries=2,            # Prevent infinite 429 loops if a retry errors out
)

# Test it inside your LangChain chain setup
try:
    response = llm.invoke("Hello, say test!")
    print("LANGCHAIN SUCCESS:", response.content)
except Exception as e:
    print("LANGCHAIN STILL FAILING:", e)
