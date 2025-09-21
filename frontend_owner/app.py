import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
from utils.api_client import trigger_sync_to_pinecone
import time


st.set_page_config(
    page_title="HFC Restaurant - Admin",
    page_icon="😎",
    layout="wide"
)

# --- 1. Load the hardcoded credentials ---
with open('auth_config.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)

# --- 2. Create the Authenticator object ---
authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days'],
)

# --- 3. Render the login form ---
st.title("😎 HFC Restaurant - Owner Login")
authenticator.login()

# --- 4. Main App Logic ---
# This code only runs AFTER a successful login
if st.session_state["authentication_status"]:
    
    # Display the logout button in the sidebar
    with st.sidebar:
        st.write(f'Welcome, **{st.session_state["name"]}**!')
        authenticator.logout()
    
    # --- The Main Dashboard App ---
    st.info("Select a management page from the sidebar to continue.")
    
    st.divider()
    st.header("AI Synchronization")
    st.info("Click the button below to update the AI's knowledge base with the latest menu. This is crucial after adding new items or changing descriptions/prices.")

    # Center the button for better visual appeal
    col1, col2, col3 = st.columns([2, 1, 2])
    with col2:
        if st.button("🔄 Sync Menu with AI", use_container_width=True, type="primary"):
            if trigger_sync_to_pinecone():
                st.success("Sync started! The AI is now learning. ✨")
                time.sleep(2) # Brief pause to let the user read the message
                st.rerun()


elif st.session_state["authentication_status"] is False:
    st.error('Username/password is incorrect')
elif st.session_state["authentication_status"] is None:
    st.warning('Please enter your username and password')