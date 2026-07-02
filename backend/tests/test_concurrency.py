import os
import concurrent.futures
import requests
import time

# Keys must be set in the environment before running
AIGATEWAY_KEY = os.environ.get("AIGATEWAY_API_KEY")
OPENROUTER_KEY = os.environ.get("OPENAI_API_KEY")

def test_api(name, url, key, model, concurrency):
    if not key:
        print(f"⏭️  Skipping {name} test (No API key found in os.environ)")
        return

    print(f"\n--- Testing {name} ---")
    print(f"Firing {concurrency} simultaneous requests to {model}...")
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": "Reply with exactly one word: 'Ready'."}]
    }

    def fetch(i):
        start = time.time()
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=30)
            elapsed = time.time() - start
            return i, resp.status_code, elapsed, resp.text
        except Exception as e:
            return i, "ERROR", time.time() - start, str(e)

    success_count = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = [executor.submit(fetch, i) for i in range(1, concurrency + 1)]
        for future in concurrent.futures.as_completed(futures):
            i, status, elapsed, text = future.result()
            if status == 200:
                success_count += 1
                print(f"✅ Request {i}: SUCCESS ({elapsed:.2f}s)")
            elif status == 429:
                print(f"⚠️ Request {i}: RATE LIMITED (429 Too Many Requests)")
            else:
                print(f"❌ Request {i}: FAILED (Status {status}) - {text[:100]}")

    print(f"🏁 Result: {success_count}/{concurrency} successful on {name}.\n")

if __name__ == "__main__":
    print("========================================")
    print("   CONCURRENCY LIMIT TESTING SCRIPT     ")
    print("========================================\n")
    
    # 1. Test AIGateway Promo Tier (2 Simultaneous)
    test_api(
        name="AIGateway Promo (Level 1: 2 Concurrent)", 
        url="https://api.aigateway.sh/v1/chat/completions", 
        key=AIGATEWAY_KEY, 
        model="google/gemma-4-26b-a4b-it", 
        concurrency=2
    )

    # 2. Test AIGateway Promo Tier (5 Simultaneous)
    test_api(
        name="AIGateway Promo (Level 2: 5 Concurrent)", 
        url="https://api.aigateway.sh/v1/chat/completions", 
        key=AIGATEWAY_KEY, 
        model="google/gemma-4-26b-a4b-it", 
        concurrency=5
    )

    # # 3. Test OpenRouter Production (5 Simultaneous)
    # test_api(
    #     name="OpenRouter Production (5 Concurrent)", 
    #     url="https://openrouter.ai/api/v1/chat/completions", 
    #     key=OPENROUTER_KEY, 
    #     # Using a standard free model on OpenRouter for testing
    #     model="google/gemma-2-9b-it:free", 
    #     concurrency=5
    # )

    # 4. Test AIGateway Promo Tier (20 Simultaneous)
    test_api(
        name="AIGateway Promo (Level 3: 20 Concurrent)", 
        url="https://api.aigateway.sh/v1/chat/completions", 
        key=AIGATEWAY_KEY, 
        model="google/gemma-4-26b-a4b-it", 
        concurrency=20
    )

