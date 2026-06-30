import os
import requests
import base64
import fitz  # PyMuPDF
from dotenv import load_dotenv

# 1. Load env vars safely
load_dotenv()

API_KEY = os.getenv("AIGATEWAY_API_KEY")

if not API_KEY:
    print("❌ ERROR: AIGATEWAY_API_KEY not found in .env")
    exit(1)

# 2. Extract a real image from one of your Handouts dynamically
base_dir = os.path.dirname(os.path.abspath(__file__))
pdf_path = os.path.join(base_dir, "..", "Handouts", "DD Handout_2025_2026.pdf")
print(f"📖 Reading PDF: {pdf_path}")

doc = fitz.open(pdf_path)
page = doc[0]  # Get first page
pix = page.get_pixmap(dpi=150) # Render page to an image
image_bytes = pix.tobytes("png")
real_image_b64 = base64.b64encode(image_bytes).decode("utf-8")
doc.close()

print("✅ Successfully extracted PDF page as an image.")

# 3. Build the payload using a model explicitly allowed on the Free Tier
headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

payload = {
    "model": "google/gemma-4-26b-a4b-it",
    "messages": [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "Extract all course titles and dates from this image."},
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{real_image_b64}"}}
            ]
        }
    ]
}

print(f"🚀 Sending multimodal request using Free-Tier Model: {payload['model']}...")

response = requests.post(
    "https://api.aigateway.sh/v1/chat/completions",
    headers=headers,
    json=payload
)

print(f"\nStatus Code: {response.status_code}")
if response.status_code == 200:
    print("✅ HUGE SUCCESS! The free tier model accepted the real image!")
    print("\n--- AI Response ---")
    print(response.json()["choices"][0]["message"]["content"])
else:
    print("❌ FAILED: The model or gateway rejected the image input.")
    print(response.text)
