import os, requests
from dotenv import load_dotenv
load_dotenv()

QWEN_API_KEY = os.getenv("DASHSCOPE_API_KEY")
BASE_URL = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1/chat/completions"

def call_qwen(system_prompt: str, user_message: str, model: str = "qwen-plus") -> str:
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
        }
    )
    data = response.json()
    if "choices" not in data:
        raise Exception(f"Qwen API error: {data}")
    return data["choices"][0]["message"]["content"]