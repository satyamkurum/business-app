import React from 'react';
import { NavLink } from 'react-router-dom';
import { signOut } from 'firebase/auth';
import { MessageSquare, UtensilsCrossed, ShoppingCart, User } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { useCart } from '../contexts/CartContext'; // <-- 1. Import the useCart hook
import { auth } from '../config/firebase';
import '../App.css'; // Assuming styles are in App.css

const Navbar = () => {
  const { user } = useAuth();
  const { cartCount } = useCart(); // <-- 2. Get the cartCount from the context

  const getNavLinkClass = ({ isActive }) => {
    return `nav-link ${isActive ? 'active' : ''}`;
  };

  return (
    <nav className="navbar">
      <NavLink to="/" className="navbar-logo">
        <span className="icon">🐰</span>
        <span className="text">HFC Restaurant</span>
      </NavLink>
      
      <div className="nav-links">
        <NavLink to="/" className={getNavLinkClass}><MessageSquare size={16} /> Chat</NavLink>
        <NavLink to="/menu" className={getNavLinkClass}><UtensilsCrossed size={16} /> Menu</NavLink>
        
        {/* --- THIS IS THE UPDATED LINK --- */}
        <NavLink to="/orders" className={getNavLinkClass}>
          <div style={{ position: 'relative', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <ShoppingCart size={16} />
            <span>My Orders</span>
            {cartCount > 0 && (
              <span style={{
                position: 'absolute',
                top: '-8px',
                right: '-8px',
                backgroundColor: 'var(--primary-vibrant)',
                color: 'white',
                borderRadius: '50%',
                width: '20px',
                height: '20px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '12px',
                fontWeight: 'bold',
                border: '2px solid white'
              }}>
                {cartCount}
              </span>
            )}
          </div>
        </NavLink>
        
        <NavLink to="/contact" className={getNavLinkClass}><User size={16} /> Contact Owner</NavLink>
      </div>
      
      <div>
        {user ? (
          <button onClick={() => signOut(auth)} className="auth-button">
            Logout
          </button>
        ) : (
          <NavLink to="/login" className="auth-button">
            Login / Sign Up
          </NavLink>
        )}
      </div>
    </nav>
  );
};

export default Navbar;