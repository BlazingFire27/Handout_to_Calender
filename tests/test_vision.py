import os
import sys
import base64
import fitz # PyMuPDF

# Add the parent directory to sys.path so we can import from src
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.graph import vision_eval_extractor_node
from src.schema import State

def run_vision_test():
    print("🚀 STARTING VISION NODE ISOLATION TEST...\n")
    
    # We will test using a known file that has a table!
    pdf_path = "Handouts/EM Handout.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"❌ Test PDF not found at {pdf_path}. Cannot perform test.")
        return
        
    print(f"📄 Loading {pdf_path}...")
    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        print(f"Failed to open PDF: {e}")
        return
    
    # Page 3 (index 2) usually has the evaluation table in this handout based on previous iterations
    page_num = min(2, len(doc) - 1)
    page = doc[page_num]
    
    pix = page.get_pixmap(dpi=150)
    img_bytes = pix.tobytes("png")
    b64_image = base64.b64encode(img_bytes).decode("utf-8")
    
    print(f"📸 Rendered Page {page_num+1} to image.")
    print("🤖 Sending to Vision Model... (This may take a few seconds)")
    
    state = State(
        raw_text="", # Text is ignored by vision node
        page_image_b64=b64_image,
        classification=["EVAL"],
        known_course_title="Electrical Machines",
        eval_data=[],
        final_schedule=[]
    )
    
    try:
        result = vision_eval_extractor_node(state)
        eval_data = result.get("eval_data", [])
        
        print("\n📤 Output from Vision Model:\n")
        import json
        print(json.dumps(eval_data, indent=2))
        
        if eval_data:
            print("\n✅ PASSED: Successfully extracted data via Vision!")
        else:
            print("\n❌ FAILED: No data extracted.")
            
    except Exception as e:
        print(f"\n🔥 ERROR: {e}")

if __name__ == "__main__":
    run_vision_test()
