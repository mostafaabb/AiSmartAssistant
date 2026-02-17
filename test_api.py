"""
Test script to diagnose OpenRouter API connectivity issues
"""
import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv('OPENROUTER_API_KEY')
print(f"API Key loaded: {API_KEY[:20]}..." if API_KEY else "❌ No API key found!")

# Models to test
models_to_test = [
    "deepseek/deepseek-r1-0528:free",
    "google/gemini-2.0-flash-exp:free",
    "meta-llama/llama-3.1-8b-instruct:free",
    "mistralai/mistral-7b-instruct:free",
    "qwen/qwen-2-7b-instruct:free"
]

url = "https://openrouter.ai/api/v1/chat/completions"
headers = {
    "Authorization": f"Bearer {API_KEY}",
    "HTTP-Referer": "http://localhost:5000",
    "X-Title": "AI Smart Assistant Test",
    "Content-Type": "application/json"
}

print("\n" + "="*60)
print("TESTING OPENROUTER API MODELS")
print("="*60 + "\n")

for model in models_to_test:
    print(f"Testing: {model}")
    print("-" * 60)
    
    data = {
        "model": model,
        "messages": [{"role": "user", "content": "Say 'Hello' in one word."}],
        "stream": False,
        "max_tokens": 10
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=15)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            content = result['choices'][0]['message']['content']
            print(f"✅ SUCCESS! Response: {content}")
        else:
            print(f"❌ FAILED!")
            try:
                error_data = response.json()
                print(f"Error: {json.dumps(error_data, indent=2)}")
            except:
                print(f"Raw response: {response.text}")
    
    except requests.exceptions.Timeout:
        print("❌ TIMEOUT - Request took too long")
    except requests.exceptions.ConnectionError:
        print("❌ CONNECTION ERROR - Cannot reach OpenRouter")
    except Exception as e:
        print(f"❌ EXCEPTION: {str(e)}")
    
    print()

print("="*60)
print("TEST COMPLETE")
print("="*60)
