#!/usr/bin/env python3
"""
Minimal Databricks API test - find the exact working format
"""

import os
from databricks.sdk import WorkspaceClient
import json

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

def minimal_test():
    """Minimal test to find working format"""
    
    print("Minimal Databricks API test...")
    
    try:
        w = WorkspaceClient()
        print("✅ Client initialized")
        
        # Try the most basic call possible
        print("\n--- Test 1: Minimal call ---")
        try:
            response = w.serving_endpoints.query(
                name="databricks-meta-llama-3-3-70b-instruct",
                messages=[{"role": "user", "content": "Hi"}]
            )
            print("✅ Test 1 worked!")
            print(f"Type: {type(response)}")
            # Don't try to access content, just see if call works
        except Exception as e:
            print(f"❌ Test 1 failed: {e}")
        
        # Try with dataframe_records (correct parameter name)
        print("\n--- Test 2: Dataframe format ---")
        try:
            response = w.serving_endpoints.query(
                name="databricks-meta-llama-3-3-70b-instruct",
                dataframe_records=[{"messages": [{"role": "user", "content": "Hi"}]}]
            )
            print("✅ Test 2 worked!")
            print(f"Type: {type(response)}")
        except Exception as e:
            print(f"❌ Test 2 failed: {e}")
        
        # Try different parameter names
        print("\n--- Test 3: Input parameter ---")
        try:
            response = w.serving_endpoints.query(
                name="databricks-meta-llama-3-3-70b-instruct",
                input={"messages": [{"role": "user", "content": "Hi"}]}
            )
            print("✅ Test 3 worked!")
            print(f"Type: {type(response)}")
        except Exception as e:
            print(f"❌ Test 3 failed: {e}")
        
        # Check the actual method signature
        print("\n--- Method signature ---")
        import inspect
        sig = inspect.signature(w.serving_endpoints.query)
        print(f"Parameters: {list(sig.parameters.keys())}")
        
        return False
        
    except Exception as e:
        print(f"❌ Client error: {e}")
        return False

if __name__ == "__main__":
    minimal_test()