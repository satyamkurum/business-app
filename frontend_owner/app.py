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

# --- THE DEFINITIVE, ENVIRONMENT-AWARE CONFIGURATION ---
config = None
try:
    # --- THIS IS THE FIX ---
    # We load the read-only secrets from Streamlit Cloud...
    creds = dict(st.secrets['credentials'])
    cook = dict(st.secrets['cookie'])
    preauth = dict(st.secrets['preauthorized'])
    
    # ...and then build a new, MUTABLE dictionary from them.
    # This is the dictionary we will pass to the authenticator.
    config = {
        'credentials': creds,
        'cookie': cook,
        'preauthorized': preauth
    }
    print("Loaded config from Streamlit Secrets into a mutable dictionary.")

except FileNotFoundError:
    # This is the fallback for local development
    print("Secrets not found on cloud, loading from local auth_config.yaml.")
    with open('auth_config.yaml') as file:
        config = yaml.load(file, Loader=SafeLoader)

# -------------------------------------------------------------

# Create the Authenticator object with the now-mutable config
authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days'],
)

st.title("😎 HFC Restaurant - Owner Login")
authenticator.login()

# --- Main App Logic (remains the same) ---
if st.session_state["authentication_status"]:
    
    with st.sidebar:
        st.write(f'Welcome, **{st.session_state["name"]}**!')
        authenticator.logout()
    
    st.info("Select a management page from the sidebar to continue.")
    
    st.divider()
    st.header("AI Synchronization")
    st.info("Click the button below to update the AI's knowledge base with the latest menu.")

    col1, col2, col3 = st.columns([2, 1, 2])
    with col2:
        if st.button("🔄 Sync Menu with AI", use_container_width=True, type="primary"):
            if trigger_sync_to_pinecone():
                st.success("Sync started! The AI is now learning. ✨")
                time.sleep(2)
                st.rerun()

elif st.session_state["authentication_status"] is False:
    st.error('Username/password is incorrect')
elif st.session_state["authentication_status"] is None:
    st.warning('Please enter your username and password')

