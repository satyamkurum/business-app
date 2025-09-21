import streamlit as st
from utils.api_client import get_all_orders
from datetime import datetime

st.set_page_config(layout="wide")
st.title("📦 View Customer Orders")

if not st.session_state.get("authentication_status"):
    st.warning("Please log in to access this page.")
    st.stop()

orders = get_all_orders()

if not orders:
    st.info("No orders found yet.")
else:
    st.success(f"Displaying {len(orders)} most recent orders.")
    
    for order in orders:
        order_time = datetime.fromisoformat(order['created_at'].replace('Z', '+00:00'))
        status_color = "green" if order['status'] == 'SUCCESS' else "orange" if order['status'] == 'PENDING' else "red"
        
        with st.expander(f"Order #{order['merchant_transaction_id'][:8]}... - Status: :{status_color}[{order['status']}]"):
            st.write(f"**Order Time:** {order_time.strftime('%Y-%m-%d %H:%M')}")
            st.write(f"**Customer User ID:** {order.get('user_id', 'N/A')}")
            st.write(f"**Total Amount:** ₹{order['total_amount'] / 100:.2f}")
            
            st.write("**Items:**")
            for item in order['items']:
                st.write(f"- {item['quantity']}x {item['name']} @ ₹{item['price']:.2f}")