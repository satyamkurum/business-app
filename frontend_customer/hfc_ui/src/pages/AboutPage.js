import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { getRestaurantDetails } from '../config/api';
import { Building, Phone, Mail, Camera } from 'lucide-react';

const AboutPage = () => {
  const [details, setDetails] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      const fetchedDetails = await getRestaurantDetails();
      setDetails(fetchedDetails);
      setLoading(false);
    };
    fetchData();
  }, []);

  if (loading) return <div className="page-container"><p>Loading restaurant details...</p></div>;
  if (!details) return <div className="page-container"><p>Could not load restaurant details.</p></div>;

  return (
    <div className="page-container" style={{justifyContent: 'flex-start'}}>
      {/* --- THIS IS THE FIX --- */}
      {/* This new wrapper div uses our centering class */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="about-page-content"
      >
        {/* Hero Section */}
        <div className="login-card text-center">
          <h1 className="page-title">{details.name}</h1>
          <p className="page-subtitle mt-4">{details.about_text}</p>
        </div>
        
        {/* Photo Gallery */}
        {details.gallery_image_urls && details.gallery_image_urls.length > 0 && (
          <div className="photo-gallery">
            <h2 className="page-title mb-6 flex items-center justify-center gap-3">
              <Camera size={32} /> Gallery
            </h2>
            <div className="gallery-grid">
              <AnimatePresence>
                {details.gallery_image_urls.map((url, index) => (
                  <motion.div 
                    key={index}
                    initial={{ opacity: 0, scale: 0.8 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ delay: index * 0.1 }}
                    className="gallery-image-wrapper"
                  >
                    <img src={url} alt={`Gallery image ${index + 1}`} className="gallery-image" />
                  </motion.div>
                ))}
              </AnimatePresence>
            </div>
          </div>
        )}
        
        {/* Visit Us Section */}
        <div className="login-card">
           <h2 className="page-title mb-6">Visit Us</h2>
           <div className="flex flex-wrap justify-center gap-8 text-lg">
                <div className="flex items-center gap-3"><Building size={24} className="text-primary-vibrant" /><span>123 Foodie Lane, Jabalpur</span></div>
                <div className="flex items-center gap-3"><Phone size={24} className="text-primary-vibrant" /><span>+91 98765 43210</span></div>
                <div className="flex items-center gap-3"><Mail size={24} className="text-primary-vibrant" /><span>contact@hfc.com</span></div>
           </div>
        </div>
      </motion.div>
    </div>
  );
};

export default AboutPage;
