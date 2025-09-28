import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { getPromotions } from '../config/api';
import { Megaphone, Calendar } from 'lucide-react';

const NotificationsPage = () => {
  const [promotions, setPromotions] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      const fetchedPromos = await getPromotions();
      // Sort promotions by start date, newest first
      fetchedPromos.sort((a, b) => new Date(b.start_date) - new Date(a.start_date));
      setPromotions(fetchedPromos);
      setLoading(false);
    };
    fetchData();
  }, []);

  return (
    <div className="notifications-page">
      <motion.div 
        initial={{ opacity: 0, y: -20 }} 
        animate={{ opacity: 1, y: 0 }} 
        className="text-center mb-8"
      >
        <Megaphone size={48} className="mx-auto text-primary-vibrant" />
        <h1 className="page-title mt-4">Latest News & Promotions</h1>
        <p className="page-subtitle">Stay updated with our special offers and events.</p>
      </motion.div>

      {loading ? (
        <p className="text-center page-subtitle">Loading latest offers...</p>
      ) : promotions.length === 0 ? (
        <p className="text-center page-subtitle">There are no active promotions right now. Please check back soon!</p>
      ) : (
        <div className="w-full space-y-8">
          <AnimatePresence>
            {promotions.map((promo, index) => (
              <motion.div
                key={promo._id || index}
                initial={{ opacity: 0, y: 50 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1, duration: 0.5 }}
                className="notification-card"
              >
                <img 
                  className="notification-image" 
                  src={promo.image_url || 'https://placehold.co/800x450/ff6b6b/ffffff?text=Special+Offer!'} 
                  alt={promo.title} 
                />
                <div className="notification-content">
                  <h2>{promo.title}</h2>
                  <p>{promo.description}</p>
                  <div className="date-range flex items-center gap-2">
                    <Calendar size={16} />
                    <span>
                      Valid from {new Date(promo.start_date).toLocaleDateString()} to {new Date(promo.end_date).toLocaleDateString()}
                    </span>
                  </div>
                </div>
              </motion.div>
            ))}
          </AnimatePresence>
        </div>
      )}
    </div>
  );
};

export default NotificationsPage;
