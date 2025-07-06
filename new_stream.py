import os
import json
import streamlit as st
import requests
from datetime import datetime

# Load environment variables from .env file if it exists
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not installed, use system environment variables

# Set page config for wider layout
st.set_page_config(page_title="Usecase Review Assistant", layout="wide")

def init_databricks_config():
    """Initialize Databricks configuration for HTTP requests"""
    token = os.getenv("DATABRICKS_TOKEN")
    host = os.getenv("DATABRICKS_HOST")
    
    if not token or not host:
        st.error("Missing DATABRICKS_TOKEN or DATABRICKS_HOST environment variables")
        return None
    
    return {
        "token": token,
        "host": host.rstrip('/'),
        "headers": {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
    }

def call_databricks_llm(config, messages, temperature=0.1, max_tokens=2048):
    """Call Databricks LLM using direct HTTP requests"""
    if not config:
        return None
    
    url = f"{config['host']}/serving-endpoints/databricks-meta-llama-3-3-70b-instruct/invocations"
    
    payload = {
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature
    }
    
    try:
        response = requests.post(url, headers=config["headers"], json=payload, timeout=60)
        
        if response.status_code == 200:
            response_json = response.json()
            if 'choices' in response_json:
                return response_json['choices'][0]['message']['content']
            elif 'predictions' in response_json:
                return str(response_json['predictions'][0])
            else:
                return str(response_json)
        else:
            st.error(f"API call failed with status {response.status_code}: {response.text}")
            return None
            
    except Exception as e:
        st.error(f"API request failed: {e}")
        return None

config = init_databricks_config()

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
                if not config:
                    st.error("Databricks configuration not initialized. Please check your environment variables.")
                else:
                    with st.spinner("Analyzing..."):
                        messages = [
                            {
                                "role": "system", 
                                "content": (
                                    "You are a security-focused assistant. "
                                    "Review the provided SPL and drill-down SPL queries against the MITRE ATT&CK techniques."
                                )
                            },
                            {"role": "user", "content": user_prompt}
                        ]
                        
                        st.write("Making API call...")
                        analysis_result = call_databricks_llm(config, messages, temperature=0.1, max_tokens=2048)
                        
                        if analysis_result:
                            # Store the analysis result in session state FIRST
                            if 'conversation_history' not in st.session_state:
                                st.session_state.conversation_history = []
                            
                            # Mark that we have a current analysis
                            st.session_state.has_current_analysis = True
                            st.session_state.current_usecase = selected
                            
                            # Only add to conversation if it's not already there (prevent duplicates)
                            if not st.session_state.conversation_history or st.session_state.conversation_history[-1]["content"] != analysis_result:
                                st.session_state.conversation_history = [{
                                    "role": "assistant",
                                    "content": analysis_result
                                }]
                            
                            st.session_state.current_analysis = {
                                "usecase": selected,
                                "analysis": analysis_result
                            }
            
            # Show analysis and follow-up section if we have a current analysis
            if st.session_state.get('has_current_analysis', False) and st.session_state.get('current_usecase') == selected:
                # Display the main analysis
                st.subheader("LLM Analysis")
                if st.session_state.conversation_history:
                    st.write(st.session_state.conversation_history[0]["content"])
                
                # Show follow-up conversation using chat interface
                if len(st.session_state.conversation_history) > 1:  # More than just the initial response
                    st.subheader("Follow-up Conversation")
                    
                    # Display conversation in chat format
                    for msg in st.session_state.conversation_history[1:]:  # Skip the first response
                        with st.chat_message(msg["role"]):
                            st.write(msg["content"])
                
                # Chat input for follow-up questions
                st.subheader("Ask Follow-up Question")
                
                # Initialize pending question state
                if 'pending_followup' not in st.session_state:
                    st.session_state.pending_followup = None
                
                # Process any pending follow-up question
                if st.session_state.pending_followup:
                    question = st.session_state.pending_followup
                    st.session_state.pending_followup = None  # Clear it
                    
                    # Add user question to conversation
                    st.session_state.conversation_history.append({
                        "role": "user",
                        "content": question
                    })
                    
                    # Get LLM response
                    with st.spinner("Getting response..."):
                        try:
                            # Build properly formatted message history
                            system_msg = {
                                "role": "system", 
                                "content": (
                                    "You are a security-focused assistant. "
                                    "Review the provided SPL and drill-down SPL queries against the MITRE ATT&CK techniques. "
                                    f"Original analysis: {st.session_state.conversation_history[0]['content']}"
                                )
                            }
                            
                            # Only include user/assistant pairs, skip the initial assistant message
                            follow_up_messages = [system_msg]
                            for msg in st.session_state.conversation_history[1:]:  # Skip first assistant message
                                follow_up_messages.append(msg)
                            
                            follow_up_result = call_databricks_llm(
                                config, 
                                follow_up_messages, 
                                temperature=0.1, 
                                max_tokens=2048
                            )
                            
                            if follow_up_result:
                                # Add assistant response to conversation
                                st.session_state.conversation_history.append({
                                    "role": "assistant",
                                    "content": follow_up_result
                                })
                                st.rerun()
                            else:
                                st.error("Follow-up request failed")
                            
                        except Exception as e:
                            st.error(f"Follow-up error: {e}")
                
                # Chat input - store question in session state instead of processing immediately
                def handle_followup():
                    follow_up_question = st.session_state.get("followup_input", "")
                    if follow_up_question.strip():
                        st.session_state.pending_followup = follow_up_question
                        st.rerun()
                
                st.text_input(
                    "Type your follow-up question and press Enter:",
                    key="followup_input",
                    on_change=handle_followup,
                    placeholder="Ask a follow-up question..."
                )
                
                # Final review section
                st.subheader("Final Review")
                final_review = st.text_area("Add your final review/notes:", height=100, placeholder="Enter your final thoughts, conclusions, or additional notes about this use case...")
                
                # Save Analysis button below Final Review
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
                    # Clear the current analysis after saving
                    st.session_state.has_current_analysis = False
