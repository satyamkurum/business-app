import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { getCategories, getMenuItems } from '../config/api';
import { useCart } from '../contexts/CartContext';
import { Plus } from 'lucide-react';

// --- Reusable, Intelligent Item Card Component ---
const MenuItemCard = ({ item }) => {
  const { addToCart } = useCart();
  const price = item.pricing && item.pricing.length > 0 ? item.pricing[0].price : 'N/A';

  const handleAddToCart = () => {
    // Only add to cart if the item is available
    if (item.is_available) {
      addToCart(item);
    }
  };

  return (
    <motion.div
      layout
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.9 }}
      transition={{ duration: 0.3 }}
      // --- THIS IS THE FIX ---
      // Conditionally adds the 'unavailable-card' class
      className={`menu-item-card ${!item.is_available ? 'unavailable-card' : ''}`}
    >
      <div className="menu-item-card-image-wrapper">
        <img 
          src={item.image_url || 'https://placehold.co/400x300/f8f9fa/6c757d?text=No+Image'} 
          alt={item.name} 
          className="menu-item-card-image"
        />
      </div>
      <div className="p-5 flex flex-col flex-grow">
        <h3 className="text-lg font-bold text-gray-800">{item.name}</h3>
        <p className="text-sm text-gray-500 mt-1 flex-grow">{item.description}</p>
        
        {/* --- THIS IS THE FIX --- */}
        {/* Conditionally render either the price/button OR the "Unavailable" tag */}
        <div className="flex justify-between items-center mt-4">
          {item.is_available ? (
            <>
              <span className="text-2xl font-semibold text-gray-900">₹{price}</span>
              <motion.button
                whileHover={{ scale: 1.1, rotate: 90 }}
                whileTap={{ scale: 0.9 }}
                onClick={handleAddToCart}
                className="auth-button"
                style={{ padding: '0.5rem' }}
                aria-label={`Add ${item.name} to cart`}
              >
                <Plus size={20} />
              </motion.button>
            </>
          ) : (
            <div className="not-available-tag w-full">
              Currently Unavailable
            </div>
          )}
        </div>
      </div>
    </motion.div>
  );
};


// --- Main Menu Page (No other changes needed here) ---
const MenuPage = () => {
  const [categories, setCategories] = useState([]);
  const [menuItems, setMenuItems] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState(null);
  const [loading, setLoading] = useState(true);

  const categoryImages = {
  
    "Burger": "https://images.unsplash.com/photo-1571091718767-18b5b1457add?q=80&w=2072",
    "Noodles": "https://images.unsplash.com/photo-1585032226651-759b368d7246?q=80&w=1892",
    "Starters": "https://images.unsplash.com/photo-1541592106381-b58e7c136103?q=80&w=1887",
    "Pasta": "https://images.unsplash.com/photo-1585032226651-759b368d7246?q=80&w=1892",
    "Pizza": "https://images.unsplash.com/photo-1585032226651-759b368d7246?q=80&w=1892"
  };

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      const [fetchedCategories, fetchedItems] = await Promise.all([ getCategories(), getMenuItems() ]);
      fetchedCategories.sort((a, b) => a.display_order - b.display_order);
      setCategories(fetchedCategories);
      setMenuItems(fetchedItems);
      if (fetchedCategories.length > 0) {
        setSelectedCategory(fetchedCategories[0]._id);
      }
      setLoading(false);
    };
    fetchData();
  }, []);

  const filteredItems = selectedCategory
    ? menuItems.filter(item => item.category_id === selectedCategory)
    : menuItems;

  return (
    <div className="menu-page">
      <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }} className="menu-hero">
        <h1>Explore Our Culinary Creations</h1>
        <p>Crafted with the freshest ingredients and a passion for flavor. Select a category to begin your journey.</p>
      </motion.div>

      {loading ? <p className="text-center">Loading categories...</p> : (
        <div className="category-grid">
          {categories.map(cat => (
            <motion.div
              key={cat._id}
              onClick={() => setSelectedCategory(cat._id)}
              className={`category-card ${selectedCategory === cat._id ? 'active' : ''}`}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              <img src={categoryImages[cat.name] || 'https://images.unsplash.com/photo-1546069901-ba9599a7e63c?q=80&w=2080'} alt={cat.name} className="category-card-image" />
              <h3 className="category-card-title">{cat.name}</h3>
            </motion.div>
          ))}
        </div>
      )}
      
      <motion.div layout className="menu-item-grid">
        <AnimatePresence>
          {filteredItems.map(item => <MenuItemCard key={item._id} item={item} />)}
        </AnimatePresence>
      </motion.div>
    </div>
  );
};

export default MenuPage;

