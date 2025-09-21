# frontend_owner/pages/3_FAQ_Management.py
import streamlit as st
from utils.api_client import get_faqs, update_faqs

st.set_page_config(layout="wide")
st.title("FAQ Management")
st.info("Manage the Questions and Answers for your chatbot.")

if not st.session_state.get("authentication_status"):
    st.warning("Please log in to access this page.")
    st.stop() # Stop the page from rendering further

    
# --- Fetch existing FAQs ---
# Initialize session state if it doesn't exist
if 'faqs' not in st.session_state:
    st.session_state.faqs = get_faqs()

# --- Refresh button is now OUTSIDE the form ---
if st.button("🔄 Refresh FAQs from Database"):
    st.session_state.faqs = get_faqs()
    st.rerun()

# --- Display editable form for all FAQs ---
with st.form("faq_form"):
    st.subheader("Edit Your FAQs")
    
    # Display text areas for each FAQ
    for i, faq in enumerate(st.session_state.faqs):
        st.text_input(f"Question {i+1}", key=f"q_{i}", value=faq['question'])
        st.text_area(f"Answer {i+1}", key=f"a_{i}", value=faq['answer'], height=100)
        st.divider()

    # --- Form-specific buttons ---
    col1, col2 = st.columns([1, 5])
    with col1:
        if st.form_submit_button("➕ Add New FAQ"):
            # Add a new blank FAQ to the list in the session state
            st.session_state.faqs.append({"question": "", "answer": ""})
            st.rerun()
    with col2:
        if st.form_submit_button("💾 Save All Changes", type="primary"):
            updated_faqs = []
            # Loop through the items in session state to get the current values from the form widgets
            for i, _ in enumerate(st.session_state.faqs):
                question = st.session_state[f"q_{i}"]
                answer = st.session_state[f"a_{i}"]
                if question and answer: # Only save if both fields are filled
                    updated_faqs.append({"question": question, "answer": answer})
            
            if update_faqs(updated_faqs):
                st.session_state.faqs = updated_faqs # Update state with the successfully saved data
                st.rerun()