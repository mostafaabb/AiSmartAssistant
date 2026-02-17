import requests
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("OPENROUTER_API_KEY")

url = "https://openrouter.ai/api/v1/models"
headers = {"Authorization": f"Bearer {api_key}"}

try:
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        models = response.json().get('data', [])
        free_models = [m['id'] for m in models if ':free' in m['id']]
        print("Free Models:")
        for m in sorted(free_models):
            print(m)
    else:
        print(f"Error {response.status_code}: {response.text}")
except Exception as e:
    print(f"Failed: {e}")
