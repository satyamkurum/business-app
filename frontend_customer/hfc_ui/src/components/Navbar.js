import React from 'react';
import { NavLink } from 'react-router-dom';
import { signOut } from 'firebase/auth';
import { MessageSquare, UtensilsCrossed, ShoppingCart, User, Bell, Info } from 'lucide-react'; // <-- 1. Import the new icons
import { useAuth } from '../contexts/AuthContext';
import { useCart } from '../contexts/CartContext';
import { auth } from '../config/firebase';

const Navbar = () => {
  const { user } = useAuth();
  const { cartCount } = useCart();

  const getNavLinkClass = ({ isActive }) => {
    // This is your existing style function, we will reuse it
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
        
        {/* --- ADDING THE NEW LINKS HERE --- */}
        <NavLink to="/notifications" className={getNavLinkClass}><Bell size={16} /> Notifications</NavLink>
        <NavLink to="/about" className={getNavLinkClass}><Info size={16} /> About Us</NavLink>
        {/* ---------------------------------- */}
        
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

