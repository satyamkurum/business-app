import streamlit as st
import streamlit_authenticator as stauth
from utils.api_client import trigger_sync_to_pinecone
import time

st.set_page_config(
    page_title="HFC Restaurant - Admin",
    page_icon="😎",
    layout="wide"
)

# --- AUTHENTICATION SETUP ---
# Load config from secrets and convert to a mutable dictionary
config = dict(st.secrets)

# Initialize the authenticator
authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days']
)

# --- LOGIN & PAGE LOGIC ---
# Render the login module
authenticator.login()

# Case 1: User is successfully authenticated
if st.session_state["authentication_status"]:
    # --- SIDEBAR ---
    with st.sidebar:
        st.write(f'Welcome, **{st.session_state["name"]}**!')
        authenticator.logout() # Renders the logout button in the sidebar

    # --- MAIN PAGE CONTENT ---
    st.info("Select a management page from the sidebar to continue.")
    st.divider()
    st.header("🤖 AI Synchronization")
    st.info("Click the button below to update the AI's knowledge base with the latest menu data.")

    col1, col2, col3 = st.columns([2, 1, 2])
    with col2:
        if st.button("🔄 Sync Menu with AI", use_container_width=True, type="primary"):
            with st.spinner("Syncing in progress... Please wait."):
                if trigger_sync_to_pinecone():
                    st.success("Sync started! The AI is now learning. ✨")
                    time.sleep(2) # Give user time to read the message
                    st.rerun()
                else:
                    st.error("Failed to start sync. Please check backend logs.")

# Case 2: User entered incorrect credentials
elif st.session_state["authentication_status"] is False:
    st.error('Username/password is incorrect')

# Case 3: User has not logged in yet
elif st.session_state["authentication_status"] is None:
    st.warning('Please enter your username and password')
