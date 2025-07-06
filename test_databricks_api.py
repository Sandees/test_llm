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
    
    # Test message format
    system_msg = {"role": "system", "content": "You are a helpful assistant."}
    user_msg = {"role": "user", "content": "Hello, can you tell me what 2+2 equals?"}
    
    print("\nTesting API call...")
    print(f"Model: databricks-meta-llama-3-3-70b-instruct")
    print(f"Messages: {[system_msg, user_msg]}")
    
    try:
        response = w.serving_endpoints.query(
            name="databricks-meta-llama-3-3-70b-instruct",
            messages=[system_msg, user_msg],
            temperature=0.1,
            max_tokens=100
        )
        
        print("✅ API call successful!")
        print(f"Response type: {type(response)}")
        print(f"Response: {response}")
        
        # Try to parse the response
        try:
            if hasattr(response, 'choices') and response.choices:
                content = response.choices[0].message.content
                print(f"✅ Parsed content: {content}")
            elif hasattr(response, 'predictions') and response.predictions:
                content = response.predictions[0]['candidates'][0]['message']['content']
                print(f"✅ Parsed content: {content}")
            elif isinstance(response, dict):
                if 'choices' in response:
                    content = response['choices'][0]['message']['content']
                    print(f"✅ Parsed content: {content}")
                else:
                    print(f"❌ Unknown dict structure: {response}")
            else:
                print(f"❌ Unknown response structure")
                print(f"Available attributes: {dir(response)}")
                
        except Exception as parse_error:
            print(f"❌ Failed to parse response: {parse_error}")
            print(f"Response attributes: {dir(response)}")
            
        return True
        
    except Exception as api_error:
        print(f"❌ API call failed: {api_error}")
        print(f"Error type: {type(api_error).__name__}")
        
        # Show more detailed error information
        if hasattr(api_error, 'response'):
            print(f"Response status: {api_error.response.status_code if hasattr(api_error.response, 'status_code') else 'Unknown'}")
            print(f"Response text: {api_error.response.text if hasattr(api_error.response, 'text') else 'No response text'}")
        
        return False

if __name__ == "__main__":
    success = test_databricks_api()
    if success:
        print("\n🎉 All tests passed!")
    else:
        print("\n💥 Tests failed!")