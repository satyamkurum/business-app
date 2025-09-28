import streamlit as st
from utils.api_client import get_promotions, create_promotion, update_promotion, delete_promotion
from datetime import datetime

st.set_page_config(layout="wide")
st.title("Promotions Management")

# --- Security Gatekeeper ---
# This ensures only a logged-in owner can access this page.
if not st.session_state.get("authentication_status"):
    st.warning("Please log in from the main page to access this section.")
    st.stop()

# --- Fetch Data ---
# Get all current promotions from the backend.
promotions = get_promotions()

# --- UI FORMS ---

# Expander to Add a New Promotion
with st.expander("➕ Add a New Promotion", expanded=True):
    with st.form("new_promo_form", clear_on_submit=True):
        st.subheader("Create a New Offer")
        title = st.text_input("Promotion Title", placeholder="e.g., Monsoon Magic")
        description = st.text_area("Description", placeholder="e.g., Enjoy a flat 20% discount on all main courses.")
        image_url = st.text_input("Image URL (Optional)", placeholder="https://example.com/promo_banner.jpg")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            start_date = st.date_input("Start Date", value=datetime.today())
        with col2:
            end_date = st.date_input("End Date", value=datetime.today())
        with col3:
            discount = st.number_input("Discount Percentage (%)", min_value=0, max_value=100, step=5)

        if st.form_submit_button("Add Promotion", type="primary"):
            promo_data = {
                "title": title,
                "description": description,
                "image_url": image_url,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "discount_percentage": discount
            }
            if create_promotion(promo_data):
                st.rerun()

# --- THIS IS THE NEW, MISSING SECTION ---
# Expander to Edit or Delete an Existing Promotion
with st.expander("✏️ Edit or Delete a Promotion"):
    if not promotions:
        st.info("No promotions to edit. Use the form above to add one.")
    else:
        # Create a mapping of promotion titles to their full object for easy lookup
        promo_map = {promo['title']: promo for promo in promotions}
        
        # Dropdown to select a promotion to manage
        selected_promo_title = st.selectbox("Select a promotion to edit", options=list(promo_map.keys()))
        
        if selected_promo_title:
            selected_promo = promo_map[selected_promo_title]

            with st.form("edit_promo_form"):
                st.subheader(f"Editing: {selected_promo['title']}")
                
                # Pre-populate the form with the selected promotion's data
                edit_title = st.text_input("Promotion Title", value=selected_promo['title'])
                edit_description = st.text_area("Description", value=selected_promo.get('description', ''))
                edit_image_url = st.text_input("Image URL", value=selected_promo.get('image_url', ''))

                # Convert date strings from the API back to date objects for the widget
                edit_start_date = datetime.fromisoformat(selected_promo['start_date']).date()
                edit_end_date = datetime.fromisoformat(selected_promo['end_date']).date()

                col1, col2, col3 = st.columns(3)
                with col1:
                    edit_start = st.date_input("Start Date", value=edit_start_date)
                with col2:
                    edit_end = st.date_input("End Date", value=edit_end_date)
                with col3:
                    edit_discount = st.number_input("Discount Percentage (%)", value=selected_promo.get('discount_percentage', 0))

                # Create two buttons for updating or deleting
                update_button = st.form_submit_button("Update Promotion")
                delete_button = st.form_submit_button("Delete Promotion", type="primary")

                if update_button:
                    updated_data = {
                        "title": edit_title, "description": edit_description,
                        "image_url": edit_image_url, "start_date": edit_start.isoformat(),
                        "end_date": edit_end.isoformat(), "discount_percentage": edit_discount
                    }
                    if update_promotion(selected_promo['_id'], updated_data):
                        st.rerun()
                
                if delete_button:
                    if delete_promotion(selected_promo['_id']):
                        st.rerun()

st.divider()

# --- Display All Promotions ---
st.subheader("Current & Upcoming Promotions")
if promotions:
    st.dataframe(promotions, use_container_width=True, hide_index=True)
else:
    st.info("No promotions found in the database.")
