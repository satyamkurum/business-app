import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useCart } from '../contexts/CartContext';
import { useAuth } from '../contexts/AuthContext';
import { Link } from 'react-router-dom';
import { Plus, Minus, Trash2, ShoppingCart, Check, Truck, ChefHat, Package } from 'lucide-react';
import { initiatePayment, getMyOrders } from '../config/api';

// --- Reusable, Visual Order Status Timeline Component ---
// This component visually tracks the order's progress for the customer.
const OrderStatusTimeline = ({ status }) => {
    const steps = [
        { name: 'Confirmed', status: 'CONFIRMED', icon: <Package size={20}/> },
        { name: 'Preparing', status: 'PREPARING', icon: <ChefHat size={20}/> },
        { name: 'Shipped', status: 'SHIPPED', icon: <Truck size={20}/> },
    ];

    const getStatusIndex = (currentStatus) => {
        const order = ['CONFIRMED', 'PREPARING', 'SHIPPED'];
        // The 'SUCCESS' status from payment is the pre-step to 'CONFIRMED'.
        if (currentStatus === 'SUCCESS') return -1; 
        return order.indexOf(currentStatus);
    };

    const currentStepIndex = getStatusIndex(status);

    return (
        <div className="flex items-center justify-between w-full mt-4">
            {steps.map((step, index) => (
                <React.Fragment key={step.status}>
                    <div className="flex flex-col items-center text-center">
                        <div className={`w-10 h-10 rounded-full flex items-center justify-center transition-colors duration-500 ${index <= currentStepIndex ? 'bg-green-500 text-white' : 'bg-gray-200 text-gray-500'}`}>
                            {index <= currentStepIndex ? <Check size={24} /> : step.icon}
                        </div>
                        <p className={`mt-2 text-xs font-semibold transition-colors duration-500 ${index <= currentStepIndex ? 'text-gray-800' : 'text-gray-400'}`}>{step.name}</p>
                    </div>
                    {index < steps.length - 1 && (
                        <div className={`flex-1 h-1 mx-2 transition-colors duration-500 ${index < currentStepIndex ? 'bg-green-500' : 'bg-gray-200'}`}></div>
                    )}
                </React.Fragment>
            ))}
        </div>
    );
};


const OrdersPage = () => {
    // --- STATE MANAGEMENT ---
    const { cartItems, updateQuantity, removeFromCart, cartTotal } = useCart();
    const { user } = useAuth();
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState('');
    const [orders, setOrders] = useState([]);
    const [loadingOrders, setLoadingOrders] = useState(true);

    // --- DATA FETCHING ---
    // Fetches the user's past and current orders when they log in.
    useEffect(() => {
        const fetchOrders = async () => {
            if (!user) return; // Only run if the user is logged in
            setLoadingOrders(true);
            try {
                const token = await user.getIdToken();
                const userOrders = await getMyOrders(token);
                // Sort by date to show the most recent orders first
                userOrders.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
                setOrders(userOrders);
            } catch (err) {
                console.error("Failed to fetch orders:", err);
            } finally {
                setLoadingOrders(false);
            }
        };
        fetchOrders();
    }, [user]); // Re-runs whenever the user's login state changes.

    // --- EVENT HANDLERS ---
    const handleBuyNow = async () => {
        setIsLoading(true);
        setError('');
        try {
            const token = await user.getIdToken();
            const response = await initiatePayment(token, cartItems);
            if (response && response.redirectUrl) {
                window.location.href = response.redirectUrl; // Redirect to PhonePe
            }
        } catch (err) {
            setError("Something went wrong while initiating your payment. Please try again.");
        } finally {
            setIsLoading(false);
        }
    };

    // --- RENDER LOGIC ---
    // If the cart has items, it renders the shopping cart view.
    if (cartItems.length > 0) {
        return (
            <div className="orders-page">
                <motion.h1 initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }} className="page-title text-center mb-8">Your Cart</motion.h1>
                <div className="space-y-4">
                    <AnimatePresence>
                        {cartItems.map(item => (
                            <motion.div layout key={item._id} initial={{ opacity: 0, x: -50 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: 50 }} className="cart-item">
                                <img src={item.image_url || 'https://placehold.co/100x100/f8f9fa/6c757d?text=No+Image'} alt={item.name} className="cart-item-image" />
                                <div className="cart-item-details">
                                    <h3>{item.name}</h3>
                                    <p>₹{item.pricing[0].price.toFixed(2)}</p>
                                </div>
                                <div className="quantity-control">
                                    <button onClick={() => updateQuantity(item._id, item.quantity - 1)}><Minus size={16} /></button>
                                    <span>{item.quantity}</span>
                                    <button onClick={() => updateQuantity(item._id, item.quantity + 1)}><Plus size={16} /></button>
                                </div>
                                <button onClick={() => removeFromCart(item._id)} className="remove-button"><Trash2 size={20} /></button>
                            </motion.div>
                        ))}
                    </AnimatePresence>
                </div>
                <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }} className="summary-card">
                    <div className="summary-row"><span>Subtotal</span><span>₹{cartTotal.toFixed(2)}</span></div>
                    <div className="summary-row"><span>Taxes & Charges (18%)</span><span>₹{(cartTotal * 0.18).toFixed(2)}</span></div>
                    <div className="summary-divider"></div>
                    <div className="summary-total"><span>To Pay</span><span>₹{(cartTotal * 1.18).toFixed(2)}</span></div>
                    {error && <p className="error-message" style={{marginTop: '1rem'}}>{error}</p>}
                    <button onClick={handleBuyNow} disabled={isLoading} className="buy-button">
                        {isLoading ? "Processing..." : `Proceed to Pay ₹${(cartTotal * 1.18).toFixed(2)}`}
                    </button>
                </motion.div>
            </div>
        );
    }
    
    // If the cart is empty, it renders the order history view.
    return (
        <div className="orders-page">
            <motion.h1 initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }} className="page-title text-center mb-8">My Order History</motion.h1>
            {loadingOrders ? (
                <p className="text-center page-subtitle">Loading your order history...</p>
            ) : orders.length === 0 ? (
                <div className="empty-cart">
                    <ShoppingCart size={64} className="icon" />
                    <h1 className="page-title">No Past Orders Found</h1>
                    <p className="page-subtitle">When you place an order, you'll be able to track it here.</p>
                    <Link to="/menu" className="auth-button" style={{marginTop: '1.5rem'}}>Start Your First Order</Link>
                </div>
            ) : (
                <div className="space-y-6">
                    {orders.map(order => (
                        <motion.div key={order._id} initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="bg-white p-6 rounded-xl shadow-md">
                            <div className="flex justify-between items-center border-b pb-3 mb-4">
                                <div>
                                    <p className="text-sm text-gray-500">Order ID: #{order.merchant_transaction_id.substring(0, 8)}...</p>
                                    <p className="font-bold text-lg text-gray-800">Total: ₹{(order.total_amount / 100).toFixed(2)}</p>
                                </div>
                                <span className={`status-badge ${order.status.includes('SUCCESS') || order.status.includes('CONFIRM') ? 'status-answered' : 'status-pending'}`}>{order.status}</span>
                            </div>
                            {['CONFIRMED', 'PREPARING', 'SHIPPED', 'SUCCESS'].includes(order.status) && (
                                <OrderStatusTimeline status={order.status} />
                            )}
                            {order.status === 'SHIPPED' && order.delivery_info && (
                                <div className="mt-4 p-3 bg-blue-50 rounded-lg text-center">
                                    <p className="font-semibold text-blue-800">Your order is on its way!</p>
                                    <p className="text-sm text-blue-600">Contact Delivery Partner {order.delivery_info.name}: {order.delivery_info.phone}</p>
                                </div>
                            )}
                        </motion.div>
                    ))}
                </div>
            )}
        </div>
    );
};

export default OrdersPage;

