import React from 'react';
import { motion } from 'framer-motion';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

const MessageBubble = ({ msg }) => {
  const isUser = msg.sender === 'user';
  const isAgent = msg.sender === 'agent';

  let textContent = msg.text;
  let imageUrl = null;
  if (typeof msg.text === 'object' && msg.text !== null) {
    textContent = msg.text.answer;
    imageUrl = msg.text.image_url;
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className={`message-bubble ${isUser ? 'user' : 'agent'}`}
    >
      {isAgent && <span className="icon">🐰</span>}
      <div className="text-content">
        {/* The FIX: Use ReactMarkdown to render the text */}
        <ReactMarkdown remarkPlugins={[remarkGfm]}>
          {textContent}
        </ReactMarkdown>
        
        {imageUrl && (
          <motion.img
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            transition={{ delay: 0.2, duration: 0.3 }}
            src={imageUrl}
            alt="Dish from the menu"
            className="image-attachment"
          />
        )}
      </div>
    </motion.div>
  );
};

export default MessageBubble;