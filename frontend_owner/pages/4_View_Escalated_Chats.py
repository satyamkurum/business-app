import streamlit as st
from utils.api_client import get_escalated_chats, post_human_reply
from datetime import datetime

st.set_page_config(layout="wide")
st.title("👑 Owner's Inbox: Escalated Chats")

# --- 1. Security Gatekeeper ---
# This is the most critical part. It ensures that only a logged-in owner
# can see this page. It checks the session state set by streamlit-authenticator.
if not st.session_state.get("authentication_status"):
    st.warning("Please log in from the main 'app' page to access this section.")
    st.stop() # Stop the page from rendering any further

# --- 2. Main Page Logic (runs only if logged in) ---
st.info("Here are the conversations that require your direct attention. Your reply will be sent to the user (if they are registered) and will close the ticket.")

# Fetch the escalated chats from the secure backend endpoint.
chats = get_escalated_chats()

if not chats:
    st.success("✅ Your inbox is clear! No chats require attention right now.")
else:
    # Sort chats by creation date, showing the most recent ones first for priority.
    try:
        chats.sort(key=lambda x: x.get('created_at', {}).get('$date', '0'), reverse=True)
    except Exception as e:
        st.error(f"Could not sort chats by date: {e}")

    # Display each escalated chat in its own section.
    for chat in chats:
        # --- Safely extract user's name for a more personal touch ---
        first_message = chat['messages'][0]['text'] if chat.get('messages') else "Message"
        user_name = "Unknown User"
        if 'from ' in first_message and ':' in first_message:
            try:
                user_name = first_message.split('from ')[1].split(':')[0]
            except IndexError:
                user_name = f"Session {chat.get('session_id')}"
        
        # --- Display each chat in a collapsible expander ---
        expander_title = f"Message from **{user_name}** (Session: {chat.get('session_id')})"
        with st.expander(expander_title):
            
            # Display the full conversation history for context.
            st.write("--- Conversation History ---")
            for message in chat['messages']:
                sender = message.get('sender', 'unknown')
                # Use different avatars for clarity
                icon = "👑" if sender == 'human' else "👤" if sender == 'user' else "🤖"
                with st.chat_message(name=sender, avatar=icon):
                    st.write(message.get('text', '...'))
                    # Display timestamp if available, formatted nicely.
                    if 'timestamp' in message and '$date' in message.get('timestamp', {}):
                       try:
                           ts = datetime.fromisoformat(message['timestamp']['$date'].replace('Z', '+00:00'))
                           st.caption(f"{ts.strftime('%b %d, %Y at %I:%M %p')} UTC")
                       except ValueError:
                           st.caption("Invalid timestamp")
            
            st.divider()

            # The reply form for the owner. Each form is unique.
            st.write("--- Your Reply ---")
            with st.form(key=f"form_{chat['_id']}"):
                reply = st.text_area(
                    "Write your response here:", 
                    key=f"reply_{chat['_id']}",
                    help="Your reply will be added to the chat history and the status will be set to 'closed'."
                )
                
                # The submit button for the form.
                if st.form_submit_button("Send Reply & Close Chat", type="primary"):
                    if reply.strip(): # Ensure reply is not just empty spaces
                        # Call the secure API endpoint to post the reply
                        if post_human_reply(chat['_id'], reply):
                            st.success("Reply sent successfully! Refreshing list...")
                            st.rerun()
                    else:
                        st.warning("Your reply cannot be empty.")

