import { initializeApp } from 'firebase/app';
import { getAuth, GoogleAuthProvider, EmailAuthProvider } from 'firebase/auth';

// IMPORTANT: Replace with your actual Firebase configuration
const firebaseConfig = {
  apiKey: "AIzaSyDQzE5fDeq4zTdluryYn3hp2Z6cQk-8lu8",
  authDomain: "satyam-firebase.firebaseapp.com",
  projectId: "satyam-firebase",
  storageBucket: "satyam-firebase.firebasestorage.app",
  messagingSenderId: "894582416608",
  appId: "1:894582416608:web:cb0df257582244e4281c85",
  measurementId: "G-6155B1BHTY"
};

const app = initializeApp(firebaseConfig);
const auth = getAuth(app);

const uiConfig = {
  signInFlow: 'popup',
  signInOptions: [
    EmailAuthProvider.PROVIDER_ID,
    GoogleAuthProvider.PROVIDER_ID,
  ],
  callbacks: {
    signInSuccessWithAuthResult: () => false, // We handle redirects in our app logic
  },
};

export { auth, uiConfig };