#!/usr/bin/env python3
"""
Simple test script to check Databricks LLM API connectivity
"""

import os
from databricks.sdk import WorkspaceClient

# Load environment variables from .env file if it exists
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

def test_databricks_api():
    """Test the Databricks serving endpoints API"""
    
    print("Testing Databricks API connectivity...")
    
    # Check environment variables
    token = os.getenv("DATABRICKS_TOKEN")
    host = os.getenv("DATABRICKS_HOST")
    
    if not token:
        print("❌ DATABRICKS_TOKEN not found in environment")
        return False
    
    if not host:
        print("❌ DATABRICKS_HOST not found in environment")
        return False
    
    print(f"✅ Token found: {token[:10]}...")
    print(f"✅ Host found: {host}")
    
    # Initialize client
    try:
        w = WorkspaceClient()
        print("✅ Databricks client initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize client: {e}")
        return False
    
    # Test different API call formats
    print("\nTesting different API call formats...")
    
    # Method 1: Standard messages format
    print("\n--- Method 1: Standard messages format ---")
    try:
        response = w.serving_endpoints.query(
            name="databricks-meta-llama-3-3-70b-instruct",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Hello, what is 2+2?"}
            ],
            temperature=0.1,
            max_tokens=100
        )
        print("✅ Method 1 successful!")
        print(f"Response: {response}")
    except Exception as e:
        print(f"❌ Method 1 failed: {e}")
    
    # Method 2: Dataframe format
    print("\n--- Method 2: Dataframe format ---")
    try:
        import pandas as pd
        df = pd.DataFrame({
            "messages": [
                [
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": "Hello, what is 2+2?"}
                ]
            ]
        })
        response = w.serving_endpoints.query(
            name="databricks-meta-llama-3-3-70b-instruct",
            dataframe_records=df.to_dict(orient="records")
        )
        print("✅ Method 2 successful!")
        print(f"Response: {response}")
    except Exception as e:
        print(f"❌ Method 2 failed: {e}")
    
    # Method 3: Raw JSON format
    print("\n--- Method 3: Raw JSON format ---")
    try:
        response = w.serving_endpoints.query(
            name="databricks-meta-llama-3-3-70b-instruct",
            inputs={
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": "Hello, what is 2+2?"}
                ],
                "temperature": 0.1,
                "max_tokens": 100
            }
        )
        print("✅ Method 3 successful!")
        print(f"Response: {response}")
    except Exception as e:
        print(f"❌ Method 3 failed: {e}")
    
    # Method 4: Simple prompt format
    print("\n--- Method 4: Simple prompt format ---")
    try:
        response = w.serving_endpoints.query(
            name="databricks-meta-llama-3-3-70b-instruct",
            inputs={"prompt": "Hello, what is 2+2?"}
        )
        print("✅ Method 4 successful!")
        print(f"Response: {response}")
    except Exception as e:
        print(f"❌ Method 4 failed: {e}")
    
    # Let's also try to list available endpoints
    print("\n--- Available serving endpoints ---")
    try:
        endpoints = w.serving_endpoints.list()
        for endpoint in endpoints:
            print(f"Endpoint: {endpoint.name}")
    except Exception as e:
        print(f"❌ Failed to list endpoints: {e}")
    
    return False  # We'll return True only if one of the methods works

if __name__ == "__main__":
    success = test_databricks_api()
    if success:
        print("\n🎉 All tests passed!")
    else:
        print("\n💥 Tests failed!")