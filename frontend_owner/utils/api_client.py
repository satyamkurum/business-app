# frontend_owner/utils/api_client.py

import requests
import streamlit as st

# The base URL for our FastAPI backend
API_BASE_URL = "https://business-app-seg7.onrender.com/api/v1"

ADMIN_API_KEY = "154658972498424897934762345" 

HEADERS = {"X-API-Key": ADMIN_API_KEY}

def get_categories():
    """Fetches all categories from the API."""
    try:
        response = requests.get(f"{API_BASE_URL}/menu/categories/")
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Failed to fetch categories. Status code: {response.status_code}")
            return []
    except requests.exceptions.ConnectionError:
        st.error("Connection Error: Could not connect to the API. Is the backend server running?")
        return []
    

def create_category(name: str, description: str, display_order: int):
    """Posts a new category to the API."""
    url = f"{API_BASE_URL}/menu/categories/"
    payload = {
        "name": name,
        "description": description,
        "display_order": display_order
    }
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 201: # 201 Created
            st.success("Category added successfully!")
            return True
        else:
            st.error(f"Failed to add category. Error: {response.text}")
            return False
    except requests.exceptions.ConnectionError:
        st.error("Connection Error: Could not connect to the API.")
        return False
    
def update_category(category_id: str, name: str, description: str, display_order: int):
    """Puts an update to a category via the API."""
    url = f"{API_BASE_URL}/menu/categories/{category_id}"
    payload = {
        "name": name,
        "description": description,
        "display_order": display_order
    }
    try:
        response = requests.put(url, json=payload)
        if response.status_code == 200:
            st.success("Category updated successfully!")
            return True
        else:
            st.error(f"Failed to update category. Error: {response.text}")
            return False
    except requests.exceptions.ConnectionError:
        st.error("Connection Error: Could not connect to the API.")
        return False

def delete_category(category_id: str):
    """Deletes a category via the API."""
    url = f"{API_BASE_URL}/menu/categories/{category_id}"
    try:
        response = requests.delete(url)
        if response.status_code == 204: # 204 No Content
            st.success("Category deleted successfully!")
            return True
        else:
            st.error(f"Failed to delete category. Error: {response.text}")
            return False
    except requests.exceptions.ConnectionError:
        st.error("Connection Error: Could not connect to the API.")
        return False    
    

# === MENU ITEM FUNCTIONS ===

def get_menu_items():
    """Fetches all menu items from the API."""
    try:
        response = requests.get(f"{API_BASE_URL}/menu/items/")
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Failed to fetch menu items. Status code: {response.status_code}")
            return []
    except requests.exceptions.ConnectionError:
        st.error("Connection Error: Could not connect to the API.")
        return []

def create_menu_item(item_data: dict):
    """Posts a new menu item to the API."""
    url = f"{API_BASE_URL}/menu/items/"
    try:
        response = requests.post(url, json=item_data)
        if response.status_code == 201:
            st.success("Menu item added successfully!")
            return True
        else:
            st.error(f"Failed to add menu item. Error: {response.text}")
            return False
    except requests.exceptions.ConnectionError:
        st.error("Connection Error: Could not connect to the API.")
        return False

def update_menu_item(item_id: str, item_data: dict):
    """Puts an update to a menu item via the API."""
    url = f"{API_BASE_URL}/menu/items/{item_id}"
    try:
        response = requests.put(url, json=item_data)
        if response.status_code == 200:
            st.success("Menu item updated successfully!")
            return True
        else:
            st.error(f"Failed to update menu item. Error: {response.text}")
            return False
    except requests.exceptions.ConnectionError:
        st.error("Connection Error: Could not connect to the API.")
        return False

def delete_menu_item(item_id: str):
    """Deletes a menu item via the API."""
    url = f"{API_BASE_URL}/menu/items/{item_id}"
    try:
        response = requests.delete(url)
        if response.status_code == 204:
            st.success("Menu item deleted successfully!")
            return True
        else:
            st.error(f"Failed to delete menu item. Error: {response.text}")
            return False
    except requests.exceptions.ConnectionError:
        st.error("Connection Error: Could not connect to the API.")
        return False    
    
def get_promotions():
    """Fetches all promotions from the API using the admin API key."""
    try:
        # We add the secure header to this call.
        response = requests.get(f"{API_BASE_URL}/promotions/", headers=HEADERS)
        if response.status_code == 200:
            return response.json()
        st.error(f"Failed to fetch promotions: {response.text}")
        return []
    except requests.exceptions.RequestException as e:
        st.error(f"Connection Error: {e}")
        return []

def create_promotion(promo_data: dict):
    """Posts a new promotion to the API using the admin API key."""
    try:
        # We add the secure header to this call.
        response = requests.post(f"{API_BASE_URL}/promotions/", json=promo_data, headers=HEADERS)
        if response.status_code == 201:
            st.success("Promotion created successfully!")
            return True
        st.error(f"Failed to create promotion: {response.text}")
        return False
    except requests.exceptions.RequestException as e:
        st.error(f"Connection Error: {e}")
        return False

def update_promotion(promo_id: str, promo_data: dict):
    """Puts an update to a promotion via the API using the admin API key."""
    try:
        # We add the secure header to this call.
        response = requests.put(f"{API_BASE_URL}/promotions/{promo_id}", json=promo_data, headers=HEADERS)
        if response.status_code == 200:
            st.success("Promotion updated successfully!")
            return True
        st.error(f"Failed to update promotion: {response.text}")
        return False
    except requests.exceptions.RequestException as e:
        st.error(f"Connection Error: {e}")
        return False

def delete_promotion(promo_id: str):
    """Deletes a promotion via the API using the admin API key."""
    try:
        # We add the secure header to this call.
        response = requests.delete(f"{API_BASE_URL}/promotions/{promo_id}", headers=HEADERS)
        if response.status_code == 204: # 204 No Content
            st.success("Promotion deleted successfully!")
            return True
        st.error(f"Failed to delete promotion: {response.text}")
        return False
    except requests.exceptions.RequestException as e:
        st.error(f"Connection Error: {e}")
        return False


def get_faqs():
    try:
        response = requests.get(f"{API_BASE_URL}/restaurant/faqs/")
        if response.status_code == 200:
            return response.json()
        return []
    except: return []

def update_faqs(faqs: list):
    try:
        response = requests.put(f"{API_BASE_URL}/restaurant/faqs/", json={"faqs": faqs})
        if response.status_code == 200:
            st.success("FAQs updated successfully!")
            return True
        st.error(f"Failed to update FAQs: {response.text}")
        return False
    except: return False    


def get_escalated_chats():
    """
    Fetches all chats with 'escalated' status from the backend.
    Sends the required admin API key for authentication.
    """
    try:
        response = requests.get(f"{API_BASE_URL}/chats/escalated", headers=HEADERS)
        
        if response.status_code == 200:
            return response.json()
        else:
            # Display a detailed error in the Streamlit UI for easy debugging.
            st.error(f"Failed to fetch chats. Status: {response.status_code}, Details: {response.text}")
            return []
            
    except requests.exceptions.RequestException as e:
        st.error(f"Connection Error: Could not connect to the backend to fetch chats. Error: {e}")
        return []

def post_human_reply(chat_id: str, reply_text: str):
    """
    Sends the owner's reply to a specific escalated chat.
    The backend will add this message to the chat log and mark it as 'closed'.
    """
    # This is the JSON payload the backend endpoint expects.
    payload = {
        "chat_id": chat_id,
        "reply_text": reply_text
    }
    
    try:
        response = requests.post(f"{API_BASE_URL}/chats/escalated/reply", json=payload, headers=HEADERS)
        
        if response.status_code == 200:
            st.success("Reply sent successfully!")
            return True
        else:
            st.error(f"Failed to send reply. Status: {response.status_code}, Details: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        st.error(f"Connection Error: Could not connect to the backend to send reply. Error: {e}")
        return False

def trigger_sync_to_pinecone():
    """Triggers the backend sync process."""
    url = f"{API_BASE_URL}/sync/run-sync"
    try:
        response = requests.post(url)
        if response.status_code == 202:
            st.toast("🚀 Sync with AI has started in the background!", icon="✅")
            return True
        st.error(f"Failed to start sync: {response.text}")
        return False
    except:
        st.error("Connection Error: Could not trigger sync.")
        return False    


def get_all_orders():
    """
    Fetches all orders from the backend for the owner's dashboard.
    Requires the admin API key for authentication.
    """
    try:
        response = requests.get(f"{API_BASE_URL}/payments/orders", headers=HEADERS)
        if response.status_code == 200:
            return response.json()
        st.error(f"Failed to fetch orders: {response.text}")
        return []
    except requests.exceptions.RequestException as e:
        st.error(f"Connection Error while fetching orders: {e}")
        return []

def update_order_status(order_id: str, status: str, delivery_info: dict = None):
    """
    Updates an order's status. This is a secure action that requires the admin API key.
    
    Args:
        order_id: The MongoDB ID of the order to update.
        status: The new status (e.g., "CONFIRMED", "PREPARING", "SHIPPED").
        delivery_info: An optional dictionary with 'name' and 'phone' for the delivery partner.
    """
    url = f"{API_BASE_URL}/payments/orders/{order_id}/status"
    
    # This payload matches the structure your backend endpoint expects.
    payload = {
        "status": status,
        "delivery_info": delivery_info
    }
    
    try:
        response = requests.put(url, json=payload, headers=HEADERS)
        if response.status_code == 200:
            # Using st.toast provides a clean, temporary notification
            st.toast(f"Order status successfully updated to {status}!", icon="✅")
            return True
        else:
            st.error(f"Failed to update status: {response.text}")
            return False
    except requests.exceptions.RequestException as e:
        st.error(f"Connection Error while updating status: {e}")
        return False




def get_restaurant_details():
    """
    Fetches the core restaurant details (like 'About Us' text and gallery URLs).
    This endpoint is public, so no auth headers are needed.
    """
    try:
        response = requests.get(f"{API_BASE_URL}/restaurant/details")
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Failed to fetch restaurant details: {response.text}")
            return None
    except requests.exceptions.RequestException as e:
        st.error(f"Connection Error while fetching details: {e}")
        return None

def update_restaurant_details(details_data: dict):
    """
    Updates the restaurant's core details.
    This is a secure action and requires the admin API key.
    """
    try:
        response = requests.put(f"{API_BASE_URL}/restaurant/details", json=details_data, headers=HEADERS)
        if response.status_code == 200:
            st.success("'About Us' page details were updated successfully!")
            return True
        else:
            st.error(f"Failed to update details: {response.text}")
            return False
    except requests.exceptions.RequestException as e:
        st.error(f"Connection Error while updating details: {e}")
        return False

