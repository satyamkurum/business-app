import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useCart } from '../contexts/CartContext';
import { useAuth } from '../contexts/AuthContext';
import { Link } from 'react-router-dom';
import { Plus, Minus, Trash2, ShoppingCart } from 'lucide-react';
import { initiatePayment } from '../config/api'; // Import our new payment function

const OrdersPage = () => {
  const { cartItems, updateQuantity, removeFromCart, cartTotal } = useCart();
  const { user } = useAuth();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  /**
   * This function is the core of the checkout process.
   * It securely initiates the payment with the backend and redirects the user.
   */
  const handleBuyNow = async () => {
    // This is a safeguard; the ProtectedRoute in App.js should prevent this.
    if (!user) {
      setError("Please log in to proceed with your order.");
      return;
    }
    
    setIsLoading(true);
    setError('');
    
    try {
      // 1. Get the user's secure Firebase ID token.
      const token = await user.getIdToken();
      
      // 2. Call our backend API to create the order and get the PhonePe URL.
      const response = await initiatePayment(token, cartItems);
      
      if (response && response.redirectUrl) {
        // 3. CRITICAL STEP: Redirect the user's browser to the PhonePe payment page.
        window.location.href = response.redirectUrl;
      } else {
        setError("Could not retrieve the payment link. Please try again.");
      }
    } catch (err) {
      setError("Something went wrong while setting up your payment. Please try again.");
      console.error("Payment initiation failed:", err);
    } finally {
      setIsLoading(false);
    }
  };

  // This is the beautiful view shown when the cart is empty.
  if (cartItems.length === 0) {
    return (
      <motion.div 
        initial={{ opacity: 0, scale: 0.95 }} 
        animate={{ opacity: 1, scale: 1 }}
        className="empty-cart"
      >
        <ShoppingCart size={64} className="icon" />
        <h1 className="page-title">Your Cart is Empty</h1>
        <p className="page-subtitle">Let's find something delicious to add!</p>
        <Link to="/menu" className="auth-button" style={{marginTop: '1.5rem'}}>
          Browse Our Menu
        </Link>
      </motion.div>
    );
  }

  // This is the main view when the cart has items.
  return (
    <div className="orders-page">
      <motion.h1 
        initial={{ opacity: 0, y: -20 }} 
        animate={{ opacity: 1, y: 0 }}
        className="page-title text-center mb-8 color"
      >
        Your Order
      </motion.h1>
      
      <div className="space-y-4">
        <AnimatePresence>
          {cartItems.map(item => (
            <motion.div 
              layout key={item._id} 
              initial={{ opacity: 0, x: -50 }} 
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 50, transition: { duration: 0.2 } }}
              className="cart-item"
            >
              <img 
                src={item.image_url || 'https://placehold.co/100x100/f8f9fa/6c757d?text=No+Image'} 
                alt={item.name} 
                className="cart-item-image" 
              />
              <div className="cart-item-details">
                <h3>{item.name}</h3>
                <p>₹{item.pricing[0].price.toFixed(2)}</p>
              </div>
              <div className="quantity-control">
                <button onClick={() => updateQuantity(item._id, item.quantity - 1)} aria-label="Decrease quantity">
                  <Minus size={16} />
                </button>
                <span>{item.quantity}</span>
                <button onClick={() => updateQuantity(item._id, item.quantity + 1)} aria-label="Increase quantity">
                  <Plus size={16} />
                </button>
              </div>
              <button onClick={() => removeFromCart(item._id)} className="remove-button" aria-label="Remove item">
                <Trash2 size={20} />
              </button>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>

      {/* Order Summary Card */}
      <motion.div 
        initial={{ opacity: 0, y: 20 }} 
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="summary-card"
      >
        <div className="summary-row">
          <span>Subtotal</span>
          <span>₹{cartTotal.toFixed(2)}</span>
        </div>
        <div className="summary-row">
          <span>Taxes & Charges (18%)</span>
          <span>₹{(cartTotal * 0.18).toFixed(2)}</span>
        </div>
        <div className="summary-divider"></div>
        <div className="summary-total">
          <span>To Pay</span>
          <span>₹{(cartTotal * 1.18).toFixed(2)}</span>
        </div>
        
        {error && <p className="error-message" style={{marginTop: '1rem'}}>{error}</p>}
        
        <button 
          onClick={handleBuyNow} 
          disabled={isLoading} 
          className="buy-button"
        >
          {isLoading ? "Processing..." : `Proceed to Pay ₹${(cartTotal * 1.18).toFixed(2)}`}
        </button>
      </motion.div>
    </div>
  );
};

export default OrdersPage;

