import streamlit as st
from utils.api_client import get_restaurant_details, update_restaurant_details

st.set_page_config(layout="wide")
st.title("🖼️ Manage 'About Us' & Gallery Page")

# --- Security Gatekeeper ---
# This ensures only a logged-in owner can access this page.
if not st.session_state.get("authentication_status"):
    st.warning("Please log in from the main page to access this section.")
    st.stop()

# --- Fetch current details from the backend ---
details = get_restaurant_details()

if not details:
    st.error("Could not fetch restaurant details from the backend. Please ensure the server is running and a restaurant document exists in the database.")
else:
    with st.form("about_us_form"):
        st.header("Restaurant Information")
        st.info("This is the content that will appear on the public 'About Us' page for your customers.")

        # --- THIS IS A NEW, CRITICAL FEATURE ---
        # Field for the Restaurant Name
        restaurant_name = st.text_input(
            "Restaurant Name",
            value=details.get("name", "HFC Restaurant"),
            help="The official name of your restaurant."
        )
        
        # Field for the main "About Us" text
        about_text = st.text_area(
            "About Us Paragraph", 
            value=details.get("about_text", ""), 
            height=200,
            help="Write a short, engaging story about your restaurant's mission, history, or atmosphere."
        )
        
        st.divider()
        
        # Field for the photo gallery
        st.header("Photo Gallery")
        gallery_urls_text = st.text_area(
            "Gallery Image URLs",
            value="\n".join(details.get("gallery_image_urls", [])),
            height=250,
            help="Paste one public image URL per line. These will be displayed in a beautiful gallery on your 'About Us' page."
        )
        
        # Convert the text area back into a clean list of URLs for previewing
        gallery_urls_list = [url.strip() for url in gallery_urls_text.split("\n") if url.strip()]
        
        # --- NEW, PROFESSIONAL FEATURE: Image Preview ---
        if gallery_urls_list:
            st.subheader("Gallery Preview")
            # Use columns to create a visually appealing grid of preview images
            cols = st.columns(4) 
            for i, url in enumerate(gallery_urls_list):
                with cols[i % 4]:
                    st.image(url, use_column_width=True, caption=f"Image {i+1}")
        
        st.divider()

        # The final submit button for the form
        if st.form_submit_button("💾 Save All Changes", type="primary", use_container_width=True):
            
            # Construct the payload with all the updated details
            updated_details = {
                "name": restaurant_name, # Include the updated name
                "about_text": about_text,
                "gallery_image_urls": gallery_urls_list
            }
            
            # Call the API to save the changes
            if update_restaurant_details(updated_details):
                st.success("Your 'About Us' page has been updated successfully!")
                st.rerun()

