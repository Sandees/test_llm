import os
import json
import streamlit as st
from databricks.sdk import WorkspaceClient
from datetime import datetime

# Load environment variables from .env file if it exists
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not installed, use system environment variables

# Set page config for wider layout
st.set_page_config(page_title="Usecase Review Assistant", layout="wide")

def init_databricks_client():
    """Initialize Databricks workspace client"""
    try:
        # This will use DATABRICKS_HOST and DATABRICKS_TOKEN from environment
        return WorkspaceClient()
    except Exception as e:
        st.error(f"Failed to initialize Databricks client: {e}")
        return None

w = init_databricks_client()

@st.cache_data
def load_data(path="mitre_enriched_with_files.json"):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        st.error(f"Error loading data: {e}")
        return {}

data = load_data()

st.title("Usecase Review Assistant")

# Load and save reviewed usecases to persistent file
def load_reviewed_usecases():
    try:
        with open("reviewed_usecases.json", "r") as f:
            return set(json.load(f))
    except FileNotFoundError:
        return set()

def save_reviewed_usecases(reviewed_set):
    with open("reviewed_usecases.json", "w") as f:
        json.dump(list(reviewed_set), f)

def save_analysis(usecase_name, analysis_text):
    """Save analysis result to JSON file with usecase name as key"""
    try:
        # Load existing analyses
        try:
            with open("usecase_analyses.json", "r") as f:
                analyses = json.load(f)
        except FileNotFoundError:
            analyses = {}
        
        # Add new analysis
        analyses[usecase_name] = {
            "analysis": analysis_text,
            "timestamp": datetime.now().isoformat()
        }
        
        # Save back to file
        with open("usecase_analyses.json", "w") as f:
            json.dump(analyses, f, indent=2)
            
    except Exception as e:
        st.error(f"Error saving analysis: {e}")

# Initialize reviewed usecases in session state
if 'reviewed_usecases' not in st.session_state:
    st.session_state.reviewed_usecases = load_reviewed_usecases()

usecases = list(data.keys())
if not usecases:
    st.warning("No use cases found.")
else:
    # Format usecase names to show reviewed status
    usecase_options = []
    for usecase in usecases:
        if usecase in st.session_state.reviewed_usecases:
            usecase_options.append(f"✅ {usecase}")
        else:
            usecase_options.append(usecase)
    
    selected_display = st.selectbox("Select a Use Case:", usecase_options)
    # Extract the actual usecase name (remove the ✅ prefix if present)
    selected = selected_display.replace("✅ ", "")

    if selected:
        tech = data[selected]
        files = tech.get("files", {})
        spl_query = files.get("search.spl") or "No SPL available"
        drilldown_query = files.get("drilldown.spl") or "No drill down query available"
        readme = files.get("README.md") or "No README available"

        techniques = tech.get("techniques", [])
        if not techniques:
            st.error("No technique data available.")
        else:
            techniques_info = ""
            for idx, t in enumerate(techniques, 1):
                techniques_info += (
                    f"### Technique {idx}\n"
                    f"ID: {t.get('ID','')}\n"
                    f"Name: {t.get('name','')}\n"
                    f"Description: {t.get('description','')}\n"
                    f"Tactics: {t.get('tactics','')}\n"
                    f"Platforms: {t.get('platforms','')}\n\n"
                )

            files_info = (
                f"### SPL Query\n{spl_query}\n\n"
                f"### Drill-down SPL Query\n{drilldown_query}\n\n"
                f"### README Context\n{readme}\n\n"
            )

            default_prompt = (
                "You are a security-focused assistant. "
                "Review the following SPL against each MITRE technique and describe any coverage gaps.\n\n"
                f"{techniques_info}"
                f"{files_info}"
                "Please analyze and for each technique:\n"
                "1. What is not covered by the SPL query for detecting this technique?\n"
                "2. Identify any mistakes or gaps.\n"
                "3. Suggest specific changes needed.\n"
                "4. Provide recommendations for improving detection coverage."
            )

            st.subheader("Custom Prompt")
            user_prompt = st.text_area("Edit the prompt to LLM:", value=default_prompt, height=400)

            if st.button("Analyze Use Case"):
                if not w:
                    st.error("Databricks client not initialized. Please check your environment variables.")
                else:
                    with st.spinner("Analyzing..."):
                        system_msg = {
                            "role": "system", 
                            "content": (
                                "You are a security-focused assistant. "
                                "Review the provided SPL and drill-down SPL queries against the MITRE ATT&CK techniques."
                            )
                        }
                        user_msg = {"role": "user", "content": user_prompt}
                        
                        try:
                            st.write("About to make API call...")
                            
                            # Call the LLM using correct Databricks SDK format
                            response = w.serving_endpoints.query(
                                name="databricks-meta-llama-3-70b-instruct",
                                messages=[system_msg, user_msg],
                                temperature=0.1,
                                max_tokens=2048
                            )
                            
                            st.write("API call completed successfully!")
                            st.subheader("LLM Analysis")
                            
                            # Handle the response properly
                            if isinstance(response, dict):
                                # If it's a dict, try to access directly
                                analysis_result = response['choices'][0]['message']['content']
                            else:
                                # If it's an object, try standard attribute access
                                analysis_result = response.choices[0].message.content
                            
                            st.write(analysis_result)
                            
                            # Store the analysis result in session state
                            if 'conversation_history' not in st.session_state:
                                st.session_state.conversation_history = []
                            
                            st.session_state.conversation_history.append({
                                "role": "assistant",
                                "content": analysis_result
                            })
                            
                            st.session_state.current_analysis = {
                                "usecase": selected,
                                "analysis": analysis_result
                            }
                            
                            # Show follow-up question section
                            st.subheader("Follow-up Questions")
                            follow_up_question = st.text_input("Ask a follow-up question about this analysis:")
                            
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                if st.button("Ask Follow-up") and follow_up_question:
                                    with st.spinner("Getting follow-up response..."):
                                        # Add user's follow-up question to conversation
                                        st.session_state.conversation_history.append({
                                            "role": "user",
                                            "content": follow_up_question
                                        })
                                        
                                        try:
                                            # Send entire conversation history for context
                                            follow_up_response = w.serving_endpoints.query(
                                                name="databricks-meta-llama-3-70b-instruct",
                                                messages=[system_msg] + st.session_state.conversation_history,
                                                temperature=0.1,
                                                max_tokens=2048
                                            )
                                            
                                            # Handle different response formats for follow-up
                                            if hasattr(follow_up_response, 'choices') and follow_up_response.choices:
                                                follow_up_result = follow_up_response.choices[0].message.content
                                            elif hasattr(follow_up_response, 'content'):
                                                follow_up_result = follow_up_response.content
                                            elif isinstance(follow_up_response, dict):
                                                follow_up_result = follow_up_response.get('content', str(follow_up_response))
                                            else:
                                                follow_up_result = str(follow_up_response)
                                            st.session_state.conversation_history.append({
                                                "role": "assistant",
                                                "content": follow_up_result
                                            })
                                            
                                            st.subheader("Follow-up Response")
                                            st.write(follow_up_result)
                                            
                                        except Exception as e:
                                            st.error(f"Follow-up error: {e}")
                            
                            # Final review section
                            st.subheader("Final Review")
                            final_review = st.text_area("Add your final review/notes:", height=100, placeholder="Enter your final thoughts, conclusions, or additional notes about this use case...")
                            
                            with col2:
                                if st.button("Save Analysis"):
                                    # Save the full conversation, not just initial analysis
                                    full_conversation = "\n\n".join([
                                        f"**{msg['role'].title()}:** {msg['content']}" 
                                        for msg in st.session_state.conversation_history
                                    ])
                                    
                                    # Add final review if provided
                                    if final_review.strip():
                                        full_conversation += f"\n\n**Final Review:**\n{final_review}"
                                    
                                    save_analysis(selected, full_conversation)
                                    # Mark this usecase as reviewed
                                    st.session_state.reviewed_usecases.add(selected)
                                    save_reviewed_usecases(st.session_state.reviewed_usecases)
                                    st.success(f"✅ Analysis saved and use case '{selected}' marked as reviewed!")
                        except Exception as e:
                            st.error(f"Inference error: {e}")
