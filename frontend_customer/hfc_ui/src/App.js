import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from './contexts/AuthContext';
import Navbar from './components/Navbar';
import ChatbotPage from './pages/ChatbotPage';
import MenuPage from './pages/MenuPage';
import OrdersPage from './pages/OrdersPage';
import ContactPage from './pages/ContactPage';
import LoginPage from './pages/LoginPage';
import PaymentStatusPage from './pages/PaymentStatusPage';
import './App.css'; // This correctly imports your stylesheet

// A simple component to protect routes
const ProtectedRoute = ({ children }) => {
  const { user } = useAuth();
  if (!user) {
    return <Navigate to="/login" />;
  }
  return children;
};

function App() {
  const { user } = useAuth();

  return (
    // THIS IS THE FIX:
    // We've replaced all the Tailwind classes with our single, custom class.
    // The styles for the background image and layout are now correctly
    // loaded from your App.css file.
    <div className="app-container">
      <Navbar />
      <main className="main-content">
        <Routes>
          <Route path="/" element={<ChatbotPage />} />
          <Route path="/menu" element={<MenuPage />} />
          <Route path="/orders" element={<ProtectedRoute><OrdersPage /></ProtectedRoute>} />
          <Route path="/contact" element={<ProtectedRoute><ContactPage /></ProtectedRoute>} />
          <Route path="/login" element={!user ? <LoginPage /> : <Navigate to="/" />} />
          <Route path="/payment-status" element={<PaymentStatusPage />} />
          <Route path="*" element={<Navigate to="/" />} />
        </Routes>
      </main>
    </div>
  );
}

export default App;

