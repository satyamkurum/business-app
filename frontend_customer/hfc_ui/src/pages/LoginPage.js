import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { auth } from '../config/firebase';
import {
  signInWithEmailAndPassword,
  createUserWithEmailAndPassword,
  signInWithPopup,
  GoogleAuthProvider
} from 'firebase/auth';
import { syncUserWithBackend } from '../config/api'; // Import the crucial sync function

const LoginPage = () => {
  // State for the form inputs
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  
  // State for the UI
  const [error, setError] = useState('');
  const [isLogin, setIsLogin] = useState(true); // Toggles between Login and Sign Up mode
  const [isLoading, setIsLoading] = useState(false);

  /**
   * This is the critical function that runs after a successful Firebase login.
   * It takes the user credential, gets the ID token, and sends it to our backend
   * to create or update the user in our MongoDB database.
   */
  const handleAuthSuccess = async (userCredential) => {
    try {
      const idToken = await userCredential.user.getIdToken(true);
      await syncUserWithBackend(idToken);
      console.log("Firebase login successful. Attempting to sync user with backend. Token starts with:", idToken.substring(0, 20));
      // and our App.js router will redirect to the main page.
    } catch (syncError) {
      setError("Login was successful, but we failed to sync with our server. Please try again.");
      console.error("Backend sync error:", syncError);
    }
  };

  // Handles Email/Password form submission
  const handleAuth = async (e) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);
    if (password.length < 6) {
      setError("Password must be at least 6 characters long.");
      setIsLoading(false);
      return;
    }
    try {
      let userCredential;
      if (isLogin) {
        userCredential = await signInWithEmailAndPassword(auth, email, password);
      } else {
        userCredential = await createUserWithEmailAndPassword(auth, email, password);
      }
      await handleAuthSuccess(userCredential);
    } catch (err) {
      setError(err.message.replace('Firebase: ', ''));
    } finally {
      setIsLoading(false);
    }
  };

  // Handles Google Sign-In button click
  const handleGoogleSignIn = async () => {
    setError('');
    setIsLoading(true);
    const provider = new GoogleAuthProvider();
    try {
      const userCredential = await signInWithPopup(auth, provider);
      await handleAuthSuccess(userCredential);
    } catch (err) {
      setError(err.message.replace('Firebase: ', ''));
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="page-container">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="login-card"
      >
        <h1 className="page-title">
          {isLogin ? 'Welcome Back!' : 'Create an Account'}
        </h1>
        <p className="page-subtitle">
          Access your order history and send direct messages to the owner.
        </p>
        
        {error && <p className="error-message">{error}</p>}

        <form onSubmit={handleAuth} className="login-form">
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="Email Address"
            required
            disabled={isLoading}
          />
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Password (6+ characters)"
            required
            disabled={isLoading}
          />
          <motion.button
            whileHover={{ y: -2 }}
            whileTap={{ scale: 0.98 }}
            type="submit"
            className="submit-button"
            disabled={isLoading}
          >
            {isLoading ? 'Processing...' : (isLogin ? 'Sign In' : 'Sign Up')}
          </motion.button>
        </form>

        <div className="separator">
          <span>OR</span>
        </div>

        <motion.button
          whileHover={{ y: -2 }}
          whileTap={{ scale: 0.98 }}
          onClick={handleGoogleSignIn}
          className="google-button"
          disabled={isLoading}
        >
          <svg className="google-icon" viewBox="0 0 48 48">
            {/* --- THIS IS THE FIX --- */}
            {/* Using self-closing tags for SVG path elements */}
            <path fill="#FFC107" d="M43.611 20.083H42V20H24v8h11.303c-1.649 4.657-6.08 8-11.303 8c-6.627 0-12-5.373-12-12s5.373-12 12-12c3.059 0 5.842 1.154 7.961 3.039l5.657-5.657C34.046 6.053 29.268 4 24 4C12.955 4 4 12.955 4 24s8.955 20 20 20s20-8.955 20-20c0-1.341-.138-2.65-.389-3.917z" />
            <path fill="#FF3D00" d="m6.306 14.691l6.571 4.819C14.655 15.108 18.961 12 24 12c3.059 0 5.842 1.154 7.961 3.039l5.657-5.657C34.046 6.053 29.268 4 24 4C16.318 4 9.656 8.337 6.306 14.691z" />
            <path fill="#4CAF50" d="m24 44c5.166 0 9.86-1.977 13.409-5.192l-6.19-5.238A11.91 11.91 0 0 1 24 36c-5.202 0-9.619-3.317-11.283-7.946l-6.522 5.025C9.505 39.556 16.227 44 24 44z" />
            <path fill="#1976D2" d="M43.611 20.083H42V20H24v8h11.303c-.792 2.237-2.231 4.166-4.087 5.571l6.19 5.238C44.593 35.122 48 29.833 48 24c0-1.341-.138-2.65-.389-3.917z" />
          </svg>
          Sign In with Google
        </motion.button>
        
        <p className="toggle-auth">
          {isLogin ? "Don't have an account?" : "Already have an account?"}
          <button onClick={() => setIsLogin(!isLogin)} className="toggle-link" disabled={isLoading}>
            {isLogin ? 'Sign Up' : 'Sign In'}
          </button>
        </p>
      </motion.div>
    </div>
  );
};

export default LoginPage;

