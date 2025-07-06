#!/usr/bin/env python3
"""
Fixed Databricks API test - proper response handling
"""

import os
from databricks.sdk import WorkspaceClient

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

def test_working_api():
    """Test with proper response handling"""
    
    print("Testing Databricks API with proper response handling...")
    
    try:
        w = WorkspaceClient()
        print("✅ Client initialized")
        
        # Simple API call
        print("\nMaking API call...")
        response = w.serving_endpoints.query(
            name="databricks-meta-llama-3-3-70b-instruct",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "What is 2+2? Answer briefly."}
            ],
            max_tokens=50
        )
        
        print("✅ API call successful!")
        print(f"Response type: {type(response)}")
        
        # Handle response as dictionary (which it appears to be)
        if isinstance(response, dict):
            print("Response is a dictionary")
            print("Available keys:", list(response.keys()))
            
            # Try different ways to access content
            if 'choices' in response:
                try:
                    content = response['choices'][0]['message']['content']
                    print(f"✅ SUCCESS! Content: {content}")
                    return True
                except (KeyError, IndexError) as e:
                    print(f"❌ Failed to access choices: {e}")
                    print(f"Choices structure: {response['choices']}")
            
            if 'predictions' in response:
                try:
                    content = response['predictions'][0]
                    print(f"✅ SUCCESS! Content: {content}")
                    return True
                except (KeyError, IndexError) as e:
                    print(f"❌ Failed to access predictions: {e}")
            
            # Print the full response to understand structure
            print("Full response:")
            import json
            print(json.dumps(response, indent=2))
            
        else:
            # Handle as object
            print("Response is an object")
            print("Available attributes:", [attr for attr in dir(response) if not attr.startswith('_')])
            
            try:
                content = response.choices[0].message.content
                print(f"✅ SUCCESS! Content: {content}")
                return True
            except Exception as e:
                print(f"❌ Object access failed: {e}")
        
        return False
        
    except Exception as e:
        print(f"❌ API call failed: {e}")
        print(f"Error type: {type(e).__name__}")
        return False

if __name__ == "__main__":
    success = test_working_api()
    if success:
        print("\n🎉 API is working!")
    else:
        print("\n💥 Still having issues")