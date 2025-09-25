import streamlit as st
import streamlit_authenticator as stauth
import time

# Optional: A placeholder for your API client if the file doesn't exist yet
# You can create a utils/api_client.py file with this function
def trigger_sync_to_pinecone():
    """Placeholder function to simulate an API call."""
    print("API call triggered to sync with Pinecone.")
    # In a real app, this would make an HTTP request to your backend
    # For example: requests.post("http://backend-url/api/sync")
    return True

# --------------------------------------------------------------------------------
# 1. PAGE CONFIGURATION
# --------------------------------------------------------------------------------
# Set the page configuration. This must be the first Streamlit command.
st.set_page_config(
    page_title="HFC Restaurant - Admin",
    page_icon="😎",
    layout="wide"
)

# --------------------------------------------------------------------------------
# 2. AUTHENTICATION SETUP
# --------------------------------------------------------------------------------
# This section handles loading secrets and initializing the authenticator.
# A try-except block is used to catch KeyErrors if secrets are not configured correctly.
try:
    # Load config from secrets and convert it to a mutable dictionary
    config = dict(st.secrets)

    # Initialize the authenticator
    authenticator = stauth.Authenticate(
        config['credentials'],
        config['cookie']['name'],
        config['cookie']['key'],
        config['cookie']['expiry_days']
    )

except KeyError as e:
    st.error(f"❌ Configuration error in secrets.toml: Missing key {e}")
    st.info("Please make sure your secrets file has 'credentials', 'cookie', 'name', 'key', and 'expiry_days'.")
    st.stop() # Stop the app if config is invalid

# --------------------------------------------------------------------------------
# 3. RENDER LOGIN FORM
# --------------------------------------------------------------------------------
# The authenticator.login() method will render the login form
# and handle the authentication logic. It reads user input,
# checks credentials, and updates st.session_state upon form submission.
authenticator.login()

# --------------------------------------------------------------------------------
# 4. PAGE CONTENT (Based on Authentication Status)
# --------------------------------------------------------------------------------
# The content of the page is determined by the value of
# st.session_state["authentication_status"].

# CASE 1: User is successfully authenticated
if st.session_state["authentication_status"]:

    # --- SIDEBAR ---
    with st.sidebar:
        st.write(f'Welcome, **{st.session_state["name"]}**!')
        # The logout method renders the logout button
        authenticator.logout()

    # --- MAIN PAGE CONTENT ---
    st.title("Admin Dashboard")
    st.info("Select a management page from the sidebar to continue.")
    st.divider()

    st.header("🤖 AI Synchronization")
    st.markdown("Click the button below to update the AI's knowledge base with the latest menu data. This ensures the chat assistant provides the most current information to customers.")

    # Center the button
    col1, col2, col3 = st.columns([2, 1.5, 2])
    with col2:
        if st.button("🔄 Sync Menu with AI", use_container_width=True, type="primary"):
            with st.spinner("Syncing in progress... Please wait."):
                if trigger_sync_to_pinecone():
                    st.success("Sync started successfully! The AI is now learning. ✨")
                    time.sleep(2) # Give user time to read the message
                    # st.rerun() # Optional: uncomment to refresh the page after sync
                else:
                    st.error("Failed to start sync. Please check backend logs.")

# CASE 2: User entered incorrect credentials
elif st.session_state["authentication_status"] is False:
    st.error('Username or password is incorrect. Please try again.')

# CASE 3: User has not logged in yet (initial page load)
elif st.session_state["authentication_status"] is None:
    st.warning('Please enter your username and password to log in.')
