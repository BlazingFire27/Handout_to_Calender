import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
import json
from src.utils import enrich_refs_parallel

def run_test():
    dummy_refs = [
        {"title": "Digital Signal Processing", "author": "John G Proakis"},
        {"title": "Discrete Time Signal processing", "author": "Oppenheim and Schaffer"},
        {"title": "Theory and Applications of Digital Signal Processing", "author": "Rabiner & Gold"},
        {"title": "Obscure Book That Doesnt Exist 123", "author": "John Doe"}
    ]
    
    print("Fetching books in parallel...")
    start_time = time.time()
        
    enrich_refs_parallel(dummy_refs)
    
    end_time = time.time()
    
    print(f"\nFinished in {end_time - start_time:.2f} seconds!")
    print(json.dumps(dummy_refs, indent=4))

if __name__ == "__main__":
    run_test()
