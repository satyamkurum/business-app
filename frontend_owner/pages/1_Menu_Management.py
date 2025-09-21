# frontend_owner/pages/1_Menu_Management.py

import streamlit as st
from utils.api_client import *



st.set_page_config(layout="wide")
st.title("Menu Management")
st.subheader("Manage your menu categories and items.")

if not st.session_state.get("authentication_status"):
    st.warning("Please log in to access this page.")
    st.stop() # Stop the page from rendering further
# --- Create a tabbed interface ---
tab1, tab2 = st.tabs(["Manage Categories", "Manage Menu Items"])

# === CATEGORIES TAB ===
with tab1:
    st.header("Manage Categories")
    categories = get_categories()
    
    with st.expander("➕ Add a New Category"):
        with st.form("new_category_form", clear_on_submit=True):
            col1, col2 = st.columns([2, 1])
            with col1:
                new_cat_name = st.text_input("Category Name")
            with col2:
                new_cat_order = st.number_input("Display Order", min_value=1, step=1, value=len(categories) + 1 if categories else 1)
            new_cat_desc = st.text_area("Description")
            if st.form_submit_button("Add Category"):
                if create_category(new_cat_name, new_cat_desc, new_cat_order):
                    st.rerun()

    with st.expander("✏️ Edit or Delete a Category"):
        if categories:
            category_map = {cat['name']: cat for cat in categories}
            selected_cat_name = st.selectbox("Select a category", options=list(category_map.keys()))
            if selected_cat_name:
                selected_category = category_map[selected_cat_name]
                with st.form("edit_category_form"):
                    edit_cat_name = st.text_input("Category Name", value=selected_category['name'])
                    edit_cat_order = st.number_input("Display Order", value=selected_category['display_order'])
                    edit_cat_desc = st.text_area("Description", value=selected_category.get('description', ''))
                    
                    update_button = st.form_submit_button("Update")
                    delete_button = st.form_submit_button("Delete", type="primary")

                    if update_button and update_category(selected_category['_id'], edit_cat_name, edit_cat_desc, edit_cat_order):
                        st.rerun()
                    if delete_button and delete_category(selected_category['_id']):
                        st.rerun()
        else:
            st.info("No categories to edit.")

    st.subheader("All Categories")
    if categories:
        st.dataframe(
            categories,
            column_config={
                "_id": st.column_config.TextColumn("Category ID", width="medium"), 
                "name": "Category Name",
                "description": "Description",
                "display_order": "Order"
            },
            use_container_width=True,
            hide_index=True
        )

# === MENU ITEMS TAB ===
with tab2:
    st.header("Manage Menu Items")
    menu_items = get_menu_items()
    categories = get_categories() # Also needed here for the forms
    
    with st.expander("➕ Add a New Menu Item"):
        if not categories:
            st.warning("You must create a category before you can add a menu item.")
        else:
            with st.form("new_item_form", clear_on_submit=True):
                category_map = {cat['name']: cat['_id'] for cat in categories}
                
                st.subheader("Item Details")
                new_item_name = st.text_input("Item Name")
                selected_cat_name = st.selectbox("Category", options=category_map.keys())
                new_item_desc = st.text_area("Description")
                new_item_img_url = st.text_input("Image URL")
                
                st.subheader("Pricing")
                col1, col2 = st.columns(2)
                with col1:
                    new_item_price_full = st.number_input("Price (Full)", min_value=0.0, format="%.2f")
                with col2:
                    new_item_price_half = st.number_input("Price (Half) (0 if not applicable)", min_value=0.0, format="%.2f")
                
                st.subheader("Additional Info")
                col1, col2 = st.columns(2)
                with col1:
                    new_item_tags = st.text_input("Tags (comma-separated)", help="e.g., Bestseller, Spicy, Vegan")
                    new_item_ingredients = st.text_input("Key Ingredients (comma-separated)")
                with col2:
                    new_item_prep_time = st.number_input("Prep Time (minutes)", min_value=0, step=5)
                    is_available = st.toggle("Is Available?", value=True)
                
                st.subheader("Dietary Flags")
                col1, col2, col3 = st.columns(3)
                with col1:
                    is_vegan = st.checkbox("Vegan Available")
                with col2:
                    is_gluten_free = st.checkbox("Gluten-Free")
                with col3:
                    is_jain = st.checkbox("Jain Available")
                
                if st.form_submit_button("Add Item"):
                    pricing = [{"size": "Full", "price": new_item_price_full}]
                    if new_item_price_half > 0:
                        pricing.append({"size": "Half", "price": new_item_price_half})

                    item_data = {
                        "name": new_item_name,
                        "description": new_item_desc,
                        "category_id": category_map[selected_cat_name],
                        "pricing": pricing,
                        "image_url": new_item_img_url,
                        "tags": [tag.strip() for tag in new_item_tags.split(",")] if new_item_tags else [],
                        "key_ingredients": [ing.strip() for ing in new_item_ingredients.split(",")] if new_item_ingredients else [],
                        "prep_time_minutes": new_item_prep_time,
                        "is_available": is_available,
                        "dietary_info": { "is_vegan_available": is_vegan, "is_gluten_free": is_gluten_free, "is_jain_available": is_jain }
                    }
                    if create_menu_item(item_data):
                        st.rerun()

    with st.expander("✏️ Edit or Delete a Menu Item"):
        if not menu_items:
            st.info("No menu items to edit.")
        else:
            item_map = {f"{item['name']} ({item['_id']})": item for item in menu_items}
            selected_item_key = st.selectbox("Select an item to edit", options=list(item_map.keys()))
            
            if selected_item_key:
                selected_item = item_map[selected_item_key]
                
                def get_price(size, default=0.0):
                    for p in selected_item.get('pricing', []):
                        if p.get('size') == size:
                            return p.get('price', default)
                    return default

                with st.form("edit_item_form"):
                    st.subheader(f"Editing: {selected_item['name']}")
                    
                    category_map = {cat['name']: cat['_id'] for cat in categories}
                    id_to_name_map = {v: k for k, v in category_map.items()}
                    category_names = list(category_map.keys())
                    try:
                        current_cat_index = category_names.index(id_to_name_map.get(selected_item['category_id']))
                    except (ValueError, TypeError):
                        current_cat_index = 0
                    
                    edit_item_name = st.text_input("Item Name", value=selected_item['name'])
                    edit_cat_name = st.selectbox("Category", options=category_names, index=current_cat_index)
                    edit_item_desc = st.text_area("Description", value=selected_item.get('description', ''))
                    edit_item_img_url = st.text_input("Image URL", value=selected_item.get('image_url', ''))
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        edit_item_price_full = st.number_input("Price (Full)", min_value=0.0, format="%.2f", value=get_price("Full"))
                    with col2:
                        edit_item_price_half = st.number_input("Price (Half)", min_value=0.0, format="%.2f", value=get_price("Half"))
                        
                    edit_item_tags = st.text_input("Tags (comma-separated)", value=", ".join(selected_item.get('tags', [])))
                    edit_item_ingredients = st.text_input("Key Ingredients (comma-separated)", value=", ".join(selected_item.get('key_ingredients', [])))
                    edit_item_prep_time = st.number_input("Prep Time (minutes)", min_value=0, step=5, value=selected_item.get('prep_time_minutes', 0))
                    edit_is_available = st.toggle("Is Available?", value=selected_item.get('is_available', True))

                    dietary_info = selected_item.get('dietary_info', {})
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        edit_is_vegan = st.checkbox("Vegan Available", value=dietary_info.get('is_vegan_available', False))
                    with col2:
                        edit_is_gluten_free = st.checkbox("Gluten-Free", value=dietary_info.get('is_gluten_free', False))
                    with col3:
                        edit_is_jain = st.checkbox("Jain Available", value=dietary_info.get('is_jain_available', False))

                    update_item_button = st.form_submit_button("Update Item")
                    delete_item_button = st.form_submit_button("Delete Item", type="primary")

                    if update_item_button:
                        pricing = [{"size": "Full", "price": edit_item_price_full}]
                        if edit_item_price_half > 0:
                            pricing.append({"size": "Half", "price": edit_item_price_half})
                        
                        updated_data = {
                            "name": edit_item_name, "description": edit_item_desc,
                            "category_id": category_map[edit_cat_name], "pricing": pricing,
                            "image_url": edit_item_img_url,
                            "tags": [tag.strip() for tag in edit_item_tags.split(",")] if edit_item_tags else [],
                            "key_ingredients": [ing.strip() for ing in edit_item_ingredients.split(",")] if edit_item_ingredients else [],
                            "prep_time_minutes": edit_item_prep_time, "is_available": edit_is_available,
                            "dietary_info": {"is_vegan_available": edit_is_vegan, "is_gluten_free": edit_is_gluten_free, "is_jain_available": edit_is_jain}
                        }
                        if update_menu_item(selected_item['_id'], updated_data):
                            st.rerun()
                    
                    if delete_item_button and delete_menu_item(selected_item['_id']):
                        st.rerun()
    
    st.subheader("All Menu Items")
    if menu_items:
        st.dataframe(
            menu_items, 
            use_container_width=True, 
            hide_index=True,
            column_config={
                "pricing": st.column_config.TextColumn("Pricing")
            }
        )