import React, { createContext, useState, useEffect, useContext } from 'react';
import { onAuthStateChanged } from 'firebase/auth';
import { auth } from '../config/firebase';
import { syncUserWithBackend } from '../config/api'; // Import our crucial sync function

// 1. Create the context
// This will be the "pipe" that provides authentication data to our app.
const AuthContext = createContext();

// 2. Create a custom hook for easy access
// Any component can call useAuth() to get the current user's info.
export const useAuth = () => useContext(AuthContext);

// 3. Create the Provider component
// This is the component that does all the heavy lifting. We will wrap our entire
// application with this provider in index.js.
export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null); // This will hold our user data from MongoDB
  const [loading, setLoading] = useState(true); // Manages the initial loading state

  useEffect(() => {
    // onAuthStateChanged is a Firebase listener that runs whenever
    // a user logs in or logs out.
    const unsubscribe = onAuthStateChanged(auth, async (firebaseUser) => {
      if (firebaseUser) {
        // --- THIS IS THE CRITICAL LOGIC ---
        // The user is successfully authenticated with Firebase.
        // Now, we must sync their data with our backend.
        
        console.log("Firebase user detected. Getting ID token...");
        const idToken = await firebaseUser.getIdToken(true);
        
        // Call our API to create/update the user in our MongoDB.
        const backendUser = await syncUserWithBackend(idToken);
        
        // Set our application's user state with the data from OUR backend.
        // This is important because it will contain our application-specific data, like the user's role.
        setUser(backendUser);

      } else {
        // The user is signed out.
        setUser(null);
      }
      
      // We're done with the initial auth check.
      setLoading(false);
    });

    // This is a cleanup function that runs when the component unmounts
    // to prevent memory leaks.
    return () => unsubscribe();
  }, []); // The empty array ensures this effect runs only once on startup.

  const value = { user, loading };

  // We only render the rest of the application once we know for sure
  // if the user is logged in or not. This prevents UI flickering.
  return (
    <AuthContext.Provider value={value}>
      {!loading && children}
    </AuthContext.Provider>
  );
};

