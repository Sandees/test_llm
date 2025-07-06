#!/usr/bin/env python3
"""
Working Databricks API test with proper error handling
"""

import os
from databricks.sdk import WorkspaceClient

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

def working_test():
    """Test with all the right parameters"""
    
    print("Testing with correct parameters...")
    
    try:
        w = WorkspaceClient()
        print("✅ Client initialized")
        
        # Use the correct parameters from the signature
        print("\nMaking API call with messages parameter...")
        
        try:
            response = w.serving_endpoints.query(
                name="databricks-meta-llama-3-3-70b-instruct",
                messages=[
                    {"role": "user", "content": "What is 2+2? Answer in one word."}
                ],
                max_tokens=10,
                temperature=0.1
            )
            
            print("✅ API call successful!")
            print(f"Response type: {type(response)}")
            
            # The response is likely a generator or iterator due to the 'as_dict' error
            # Let's try to consume it properly
            try:
                # Try to convert response to dict/list
                if hasattr(response, '__iter__') and not isinstance(response, (str, dict)):
                    print("Response appears to be iterable")
                    response_list = list(response)
                    print(f"Response list: {response_list}")
                    
                    if response_list:
                        first_item = response_list[0]
                        print(f"First item: {first_item}")
                        print(f"First item type: {type(first_item)}")
                        
                        # Try to access content from first item
                        if isinstance(first_item, dict):
                            if 'choices' in first_item:
                                content = first_item['choices'][0]['message']['content']
                                print(f"✅ SUCCESS! Content: {content}")
                                return True
                
                elif isinstance(response, dict):
                    print("Response is a dictionary")
                    print(f"Keys: {list(response.keys())}")
                    
                    if 'choices' in response:
                        content = response['choices'][0]['message']['content']
                        print(f"✅ SUCCESS! Content: {content}")
                        return True
                        
                else:
                    # Try direct attribute access
                    print(f"Response attributes: {[attr for attr in dir(response) if not attr.startswith('_')]}")
                    
                    if hasattr(response, 'choices'):
                        content = response.choices[0].message.content
                        print(f"✅ SUCCESS! Content: {content}")
                        return True
                        
            except Exception as parse_error:
                print(f"❌ Parsing failed: {parse_error}")
                print(f"Raw response: {response}")
                
                # Try different approaches
                try:
                    print("Trying str() conversion...")
                    print(f"String response: {str(response)}")
                except:
                    print("Cannot convert to string")
                
                return False
                
        except Exception as api_error:
            print(f"❌ API call failed: {api_error}")
            print(f"Error type: {type(api_error).__name__}")
            
            # Show detailed error info
            if hasattr(api_error, 'response'):
                print(f"HTTP status: {getattr(api_error.response, 'status_code', 'Unknown')}")
                print(f"Response text: {getattr(api_error.response, 'text', 'No text')}")
            
            return False
        
    except Exception as e:
        print(f"❌ Setup error: {e}")
        return False

if __name__ == "__main__":
    success = working_test()
    if success:
        print("\n🎉 Found working format!")
    else:
        print("\n💥 Still debugging...")