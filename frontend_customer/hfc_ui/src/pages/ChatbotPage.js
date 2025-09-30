import React, { useState, useEffect, useRef } from 'react';
import { v4 as uuidv4 } from 'uuid';
import { motion, AnimatePresence } from 'framer-motion';
import { postToChatApi } from '../config/api';
import MessageBubble from '../components/MessageBubble';
import ChatInput from '../components/ChatInput';

const ChatbotPage = () => {
  // --- STATE MANAGEMENT ---
  // Stores the entire conversation history
  const [messages, setMessages] = useState([
    { sender: 'agent', text: " Welcome Home 😊 Please wait 50 Seconds while I am Connecting with my Server. I'm Lily 🐰, ready to find your perfect match 😉... on our menu, of course! What are you craving today? I can assist you with Food finding, Query about Business, Please Explore..👻" }
  ]);
  // Tracks when the agent is "thinking" to show a loading indicator
  const [isLoading, setIsLoading] = useState(false);
  // A unique ID for this specific chat session
  const [sessionId] = useState(uuidv4());
  // A reference to the end of the chat history for auto-scrolling
  const messagesEndRef = useRef(null);

  // --- EFFECTS ---
  // This effect automatically scrolls to the latest message
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  // --- CORE LOGIC ---
  const handleSendMessage = async (text) => {
    // 1. Instantly add the user's message to the UI for a responsive feel
    const userMessage = { sender: 'user', text };
    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);

    // 2. Prepare the history for the backend API call
    const apiHistory = messages.map(msg => ({
      sender: msg.sender,
      // Ensure history contains only text, not complex objects
      text: typeof msg.text === 'object' ? msg.text.answer : msg.text,
    }));

    // 3. Call the backend and get the agent's response
    const agentResponse = await postToChatApi(sessionId, text, apiHistory);
    
    let agentMessageContent;
    try {
        // 4. Try to parse the response as JSON in case it includes an image
        //    CORRECTED: Use JavaScript's built-in JSON.parse
        agentMessageContent = JSON.parse(agentResponse);
    } catch (e) {
        // If parsing fails, treat it as a plain text response
        agentMessageContent = agentResponse;
    }
    
    const agentMessage = { sender: 'agent', text: agentMessageContent };
    
    // 5. Add the agent's message to the UI and stop the loading indicator
    setMessages(prev => [...prev, agentMessage]);
    setIsLoading(false);
  };

  // --- RENDER ---
  return (
    <div className="chat-page">
      <div className="chat-history">
        {/* AnimatePresence makes new messages fade in smoothly */}
        <AnimatePresence>
          {messages.map((msg, index) => <MessageBubble key={index} msg={msg} />)}
        </AnimatePresence>
        
        {/* Display the animated "typing" indicator when loading */}
        {isLoading && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="typing-indicator">
            <span className="icon">🐰</span>
            <div className="typing-dots">
              <motion.div animate={{y: [0,-4,0]}} transition={{duration: 0.8, repeat: Infinity, delay: 0.0}} />
              <motion.div animate={{y: [0,-4,0]}} transition={{duration: 0.8, repeat: Infinity, delay: 0.1}} />
              <motion.div animate={{y: [0,-4,0]}} transition={{duration: 0.8, repeat: Infinity, delay: 0.2}} />
            </div>
          </motion.div>
        )}
        {/* This empty div is the target for our auto-scroll */}
        <div ref={messagesEndRef} />
      </div>
      
      <ChatInput onSendMessage={handleSendMessage} isLoading={isLoading} />
    </div>
  );
};

export default ChatbotPage;

