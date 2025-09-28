import streamlit as st
from utils.api_client import get_all_orders, update_order_status
from datetime import datetime

# --- Page Configuration ---
st.set_page_config(layout="wide")
st.title("📦 Order Fulfillment Center")

# --- 1. Security Gatekeeper ---
# This ensures that only a logged-in owner can see this page.
if not st.session_state.get("authentication_status"):
    st.warning("Please log in from the main 'app' page to access this section.")
    st.stop() # Stop the page from rendering any further

# --- 2. Main Page Logic ---
st.info("Manage the entire lifecycle of customer orders, from confirmation to shipment.")

if st.button("🔄 Refresh Orders"):
    st.rerun()

orders = get_all_orders()

if not orders:
    st.info("No orders found yet. Check back after a customer makes a purchase.")
else:
    st.success(f"Displaying {len(orders)} most recent orders.")
    
    # Sort orders to show actionable ones (SUCCESS, CONFIRMED, PREPARING) first.
    orders.sort(key=lambda x: (
        0 if x['status'] == 'SUCCESS' else
        1 if x['status'] == 'CONFIRMED' else
        2 if x['status'] == 'PREPARING' else
        3  # All other statuses
    ))
    
    for order in orders:
        # --- Visual Cues for Order Status ---
        status_color_map = {
            "SUCCESS": "green",
            "CONFIRMED": "blue",
            "PREPARING": "blue",
            "SHIPPED": "violet",
            "PENDING": "orange",
            "FAILED": "red"
        }
        status_color = status_color_map.get(order['status'], "gray")
        
        expander_title = f"Order #{order['merchant_transaction_id'][:8]}... - Status: :{status_color}[{order['status']}]"
        
        with st.expander(expander_title):
            
            # --- Display Order Details ---
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Customer User ID:** `{order.get('user_id', 'N/A')}`")
                order_time = datetime.fromisoformat(order['created_at'].replace('Z', '+00:00'))
                st.write(f"**Order Time:** {order_time.strftime('%Y-%m-%d %H:%M')}")
            with col2:
                st.write(f"**Total Amount:** ₹{order['total_amount'] / 100:.2f}")
                st.write(f"**Order ID:** `{order['_id']}`")
            
            st.write("**Items Ordered:**")
            for item in order['items']:
                st.write(f"- {item['quantity']}x {item['name']} @ ₹{item['price']:.2f} each")

            if order.get('delivery_info'):
                st.write("**Delivery Partner:**")
                st.write(f"  - Name: {order['delivery_info']['name']}")
                st.write(f"  - Phone: {order['delivery_info']['phone']}")
            
            st.divider()

            # --- Interactive Action Buttons for Order Lifecycle ---
            st.subheader("Order Actions")
            
            action_cols = st.columns(3)
            with action_cols[0]:
                # Owner can confirm a successfully paid order.
                if st.button("✅ Confirm Order", key=f"confirm_{order['_id']}", disabled=(order['status'] != 'SUCCESS')):
                    if update_order_status(order['_id'], "CONFIRMED"):
                        st.rerun()
            with action_cols[1]:
                # Owner can mark a confirmed order as being prepared.
                if st.button("🍳 Start Preparing", key=f"prepare_{order['_id']}", disabled=(order['status'] != 'CONFIRMED')):
                    if update_order_status(order['_id'], "PREPARING"):
                        st.rerun()
            with action_cols[2]:
                # Owner can ship a prepared order after entering delivery details.
                with st.popover("🚚 Ship Order", disabled=(order['status'] != 'PREPARING')):
                    st.write("Enter delivery partner details:")
                    name = st.text_input("Partner's Name", key=f"d_name_{order['_id']}")
                    phone = st.text_input("Partner's Phone", key=f"d_phone_{order['_id']}")
                    
                    if st.button("Confirm & Ship", key=f"ship_{order['_id']}"):
                        if name and phone:
                            delivery_info = {"name": name, "phone": phone}
                            if update_order_status(order['_id'], "SHIPPED", delivery_info):
                                st.rerun()
                        else:
                            st.warning("Please fill in both name and phone number.")

