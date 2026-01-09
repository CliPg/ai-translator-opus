"""测试通义千问API"""
import os
import httpx
from dotenv import load_dotenv

load_dotenv()

DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY")
DASHSCOPE_API_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"

print(f"API Key: {DASHSCOPE_API_KEY[:20]}...")

headers = {
    "Authorization": f"Bearer {DASHSCOPE_API_KEY}",
    "Content-Type": "application/json"
}

payload = {
    "model": "glm-4.7",
    "messages": [
        {
            "role": "user",
            "content": "你好"
        }
    ]
}

print(f"\n测试API调用...")
print(f"URL: {DASHSCOPE_API_URL}")
print(f"Model: qwen3-max")

with httpx.Client(timeout=30.0) as client:
    try:
        response = client.post(DASHSCOPE_API_URL, headers=headers, json=payload)
        print(f"\n状态码: {response.status_code}")
        print(f"响应头: {dict(response.headers)}")
        print(f"\n响应内容:\n{response.text}")
    except Exception as e:
        print(f"\n错误: {e}")
