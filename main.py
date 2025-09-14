import os
import requests
import sys

# رابط الموديل
API_URL = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2"

# قراءة التوكن من Secrets
hf_token = os.environ.get("HF_TOKEN")
if not hf_token:
    print("ERROR: متغير البيئة HF_TOKEN مفقود. خزّنه في GitHub Secrets.")
    sys.exit(1)

headers = {"Authorization": f"Bearer {hf_token}"}

def query(payload: dict):
    resp = requests.post(API_URL, headers=headers, json=payload)
    return resp.json()

if __name__ == "__main__":
    data = query({"inputs": "مرحبا، كيف حالك؟"})
    print(data)
