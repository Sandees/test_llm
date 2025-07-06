#!/usr/bin/env python3
"""
Direct HTTP API test - bypass SDK issues
"""

import os
import requests
import json

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

def direct_api_test():
    """Test using direct HTTP requests"""
    
    print("Testing with direct HTTP requests...")
    
    token = os.getenv("DATABRICKS_TOKEN")
    host = os.getenv("DATABRICKS_HOST")
    
    if not token or not host:
        print("❌ Missing DATABRICKS_TOKEN or DATABRICKS_HOST")
        return False
    
    # Clean up host URL
    host = host.rstrip('/')
    
    # API endpoint
    url = f"{host}/serving-endpoints/databricks-meta-llama-3-3-70b-instruct/invocations"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Try different payload formats
    payloads = [
        # Format 1: Standard OpenAI-like
        {
            "messages": [
                {"role": "user", "content": "What is 2+2? Answer in one word."}
            ],
            "max_tokens": 10,
            "temperature": 0.1
        },
        
        # Format 2: Databricks format
        {
            "inputs": {
                "messages": [
                    {"role": "user", "content": "What is 2+2? Answer in one word."}
                ],
                "max_tokens": 10,
                "temperature": 0.1
            }
        },
        
        # Format 3: Simple prompt
        {
            "inputs": {
                "prompt": "What is 2+2? Answer in one word."
            }
        },
        
        # Format 4: Dataframe format
        {
            "dataframe_records": [
                {
                    "messages": [
                        {"role": "user", "content": "What is 2+2? Answer in one word."}
                    ]
                }
            ]
        }
    ]
    
    for i, payload in enumerate(payloads, 1):
        print(f"\n--- Testing Format {i} ---")
        print(f"Payload: {json.dumps(payload, indent=2)}")
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                print("✅ SUCCESS!")
                try:
                    response_json = response.json()
                    print(f"Response: {json.dumps(response_json, indent=2)}")
                    
                    # Try to extract content
                    if 'choices' in response_json:
                        content = response_json['choices'][0]['message']['content']
                        print(f"🎉 CONTENT: {content}")
                        return True
                    elif 'predictions' in response_json:
                        print(f"🎉 PREDICTIONS: {response_json['predictions']}")
                        return True
                    else:
                        print("✅ Call successful but unknown response format")
                        
                except json.JSONDecodeError:
                    print(f"Response text: {response.text}")
                    
            else:
                print(f"❌ Failed: {response.status_code}")
                try:
                    error_json = response.json()
                    print(f"Error: {json.dumps(error_json, indent=2)}")
                except:
                    print(f"Error text: {response.text}")
                    
        except Exception as e:
            print(f"❌ Request failed: {e}")
    
    return False

if __name__ == "__main__":
    success = direct_api_test()
    if success:
        print("\n🎉 Found working HTTP format!")
    else:
        print("\n💥 All HTTP formats failed")