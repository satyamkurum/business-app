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

# 1. Load config from secrets and convert to a mutable dictionary
config = dict(st.secrets)

# 2. Initialize the authenticator with the mutable config dictionary
authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days']
)

# 3. Proceed with login
authenticator.login()

if st.session_state["authentication_status"]:
    authenticator.logout()
    st.write(f'Welcome *{st.session_state["name"]}*')
    st.title('Some content')
elif st.session_state["authentication_status"] is False:
    st.error('Username/password is incorrect')
elif st.session_state["authentication_status"] is None:
    st.warning('Please enter your username and password')

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

