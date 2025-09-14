import os
import requests

# نجيب المفتاح من الـ Secrets بدل ما يكون مكتوب داخل الكود
HF_API_KEY = os.getenv("HF_API_KEY")

API_URL = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2"
headers = {"Authorization": f"Bearer {HF_API_KEY}"}

def query(payload):
    response = requests.post(API_URL, headers=headers, json=payload)
    return response.json()

# تجربة
output = query({"inputs": "السلام عليكم، كيف حالك؟"})
print(output)
