# frontend_owner/pages/2_Promotions.py

import streamlit as st
from utils.api_client import get_promotions, create_promotion
from datetime import datetime

st.set_page_config(layout="wide")
st.title("Promotions Management")

if not st.session_state.get("authentication_status"):
    st.warning("Please log in to access this page.")
    st.stop() # Stop the page from rendering further
    
# --- Form to Add Promotion ---
with st.expander("➕ Add a New Promotion"):
    with st.form("new_promo_form", clear_on_submit=True):
        title = st.text_input("Title")
        description = st.text_area("Description")
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Start Date", value=datetime.today())
        with col2:
            end_date = st.date_input("End Date", value=datetime.today())
        
        discount = st.number_input("Discount Percentage (%)", min_value=0, max_value=100, step=5)

        if st.form_submit_button("Add Promotion"):
            promo_data = {
                "title": title,
                "description": description,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "discount_percentage": discount
            }
            if create_promotion(promo_data):
                st.rerun()

# --- Display Promotions ---
st.subheader("Current & Upcoming Promotions")
promotions = get_promotions()
if promotions:
    st.dataframe(promotions, use_container_width=True, hide_index=True)
else:
    st.info("No promotions found.")