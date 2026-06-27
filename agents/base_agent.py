import os, requests, time
from dotenv import load_dotenv
load_dotenv()

QWEN_API_KEY = os.getenv("DASHSCOPE_API_KEY")
BASE_URL = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1/chat/completions"

def call_qwen(system_prompt: str, user_message: str, model: str = "qwen-plus", retries: int = 3) -> str:
    if not QWEN_API_KEY:
        raise ValueError("DASHSCOPE_API_KEY not set in environment")
    
    for attempt in range(retries):
        try:
            response = requests.post(
                BASE_URL,
                headers={
                    "Authorization": f"Bearer {QWEN_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_message}
                    ],
                    "temperature": 0.7
                },
                timeout=60
            )
            
            if response.status_code == 429:
                wait = 2 ** attempt
                print(f"  Rate limited, waiting {wait}s...")
                time.sleep(wait)
                continue
            
            if response.status_code != 200:
                raise Exception(f"API error {response.status_code}: {response.text}")
            
            data = response.json()
            
            if "choices" not in data:
                raise Exception(f"Unexpected response: {data}")
            
            return data["choices"][0]["message"]["content"]
        
        except requests.exceptions.Timeout:
            print(f"  Timeout on attempt {attempt + 1}/{retries}")
            if attempt == retries - 1:
                raise
            time.sleep(2)
        
        except requests.exceptions.ConnectionError:
            print(f"  Connection error on attempt {attempt + 1}/{retries}")
            if attempt == retries - 1:
                raise
            time.sleep(2)
    
    raise Exception(f"Failed after {retries} attempts")