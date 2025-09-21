import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useAuth } from '../contexts/AuthContext';
import { sendMessageToOwner, getMyMessages } from '../config/api';
import { Send, CheckCircle, Mail } from 'lucide-react';

const ContactPage = () => {
  const { user } = useAuth();
  const [message, setMessage] = useState('');
  const [status, setStatus] = useState('idle'); // Manages the form state
  const [error, setError] = useState('');
  const [chats, setChats] = useState([]); // Stores the conversation history
  const [loadingChats, setLoadingChats] = useState(true);

  // This effect runs when the page loads (or when the user logs in)
  // to fetch the user's entire message history with the owner.
  useEffect(() => {
    const fetchMessages = async () => {
      if (!user) return; // Don't run if the user is not logged in
      setLoadingChats(true);
      try {
        const token = await user.getIdToken();
        const userChats = await getMyMessages(token);
        setChats(userChats);
      } catch (error) {
        console.error("Error fetching messages:", error);
      } finally {
        setLoadingChats(false);
      }
    };
    fetchMessages();
  }, [user]); // The dependency on 'user' ensures this re-runs on login/logout.

  // This function handles the form submission for sending a new message.
  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!message.trim()) {
      setError("Your message can't be empty.");
      return;
    }
    
    setStatus('loading');
    setError('');
    
    try {
      const token = await user.getIdToken();
      await sendMessageToOwner(token, message);
      setStatus('success');
      setMessage('');
      // After successfully sending, immediately refresh the chat history
      // to show the new message in the conversation thread below.
      const updatedChats = await getMyMessages(token);
      setChats(updatedChats);
    } catch (err) {
      setStatus('error');
      setError(err.message || "An unexpected error occurred. Please try again.");
    }
  };

  return (
    <div className="page-container">
      {/* --- FORM SECTION --- */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="login-card" // Reusing our beautiful card style
      >
        <div className="text-center">
          <Mail size={48} className="mx-auto text-primary-vibrant" />
          <h1 className="page-title mt-4">Get in Touch</h1>
          <p className="page-subtitle" style={{ fontStyle: 'italic', maxWidth: '450px' }}>
            "Couldn't find the answer you were looking for with Lily? No problem at all! Drop us a message here for any important queries. We'll get back to you as soon as we can. Thank you for your support!"
          </p>
        </div>
        
        {status === 'success' ? (
          <motion.div 
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className="text-center p-8 bg-green-100 text-green-800 rounded-lg mt-6"
          >
            <CheckCircle size={48} className="mx-auto mb-4" />
            <h3 className="font-bold text-lg">Message Sent!</h3>
            <p>We've received your message. You can see it in your conversation history below.</p>
          </motion.div>
        ) : (
          <form onSubmit={handleSubmit} className="login-form mt-8">
            <textarea
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              placeholder="Hi there! As a logged-in user, your message will be sent with your account details..."
              rows={5}
              required
              className="w-full p-3 bg-background-light border border-border-color rounded-lg text-base outline-none transition-shadow focus:shadow-outline"
              style={{ resize: 'none' }}
            />
            
            {error && <p className="error-message">{error}</p>}
            
            <motion.button
              whileHover={{ y: -2 }}
              whileTap={{ scale: 0.98 }}
              type="submit"
              className="submit-button flex items-center justify-center gap-2"
              disabled={status === 'loading'}
            >
              {status === 'loading' ? 'Sending...' : <>Send Message <Send size={16} /></>}
            </motion.button>
          </form>
        )}
      </motion.div>

      {/* --- CONVERSATION HISTORY SECTION --- */}
      <div className="conversation-history">
        <h2 className="page-title" style={{textAlign: 'left', marginBottom: '1.5rem'}}>Your Conversations</h2>
        {loadingChats ? (
          <p className="text-center page-subtitle">Loading your message history...</p>
        ) : chats.length === 0 ? (
          <p className="text-center page-subtitle">You have no past conversations with the owner.</p>
        ) : (
          <AnimatePresence>
            {chats.map(chat => (
              <motion.div 
                key={chat._id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="conversation-card"
              >
                <div className="conversation-header">
                  <h3>
                    Conversation from {new Date(chat.created_at).toLocaleDateString()}
                  </h3>
                  <span className={`status-badge ${chat.status === 'closed' ? 'status-answered' : 'status-pending'}`}>
                    {chat.status === 'closed' ? 'Answered' : 'Pending Reply'}
                  </span>
                </div>
                <div className="message-thread">
                  {chat.messages.map((msg, index) => (
                    <div key={index} className={`message-container ${msg.sender}`}>
                      <div className="message-text">
                        <p>{msg.text}</p>
                        <p className="message-timestamp">
                          {new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              </motion.div>
            ))}
          </AnimatePresence>
        )}
      </div>
    </div>
  );
};

export default ContactPage;

