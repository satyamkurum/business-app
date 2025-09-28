// --- CONFIGURATION ---
const API_BASE_URL = process.env.REACT_APP_API_BASE_URL;


// --- CHATBOT FUNCTIONS ---

/**
 * Sends a chat message to the backend AI agent and retrieves a response.
 * @param {string} sessionId - The unique ID for the current chat session.
 * @param {string} question - The user's latest question.
 * @param {Array<Object>} chatHistory - The history of the conversation.
 * @returns {Promise<string>} The agent's response.
 */
export async function postToChatApi(sessionId, question, chatHistory) {
  const url = `${API_BASE_URL}/chats/`;
  const payload = {
    session_id: sessionId,
    question: question,
    chat_history: chatHistory
  };

  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (!response.ok) {
      console.error(`API Error: Received status code ${response.status}`);
      return `Sorry, there was an error communicating with the server.`;
    }
    
    const data = await response.json();
    return data.answer;

  } catch (error) {
    console.error("API Connection Error:", error);
    return "I'm having trouble connecting right now. Please check if the server is running.";
  }
}


// --- MENU & CATEGORY FUNCTIONS ---

/**
 * Fetches all menu categories from the backend.
 * @returns {Promise<Array>} A list of category objects.
 */
export async function getCategories() {
  const url = `${API_BASE_URL}/menu/categories/`;
  try {
    const response = await fetch(url);
    if (!response.ok) throw new Error(`Network response was not ok.`);
    return await response.json();
  } catch (error) {
    console.error("Failed to fetch categories:", error);
    return []; 
  }
}

/**
 * Fetches all available menu items from the backend.
 * @returns {Promise<Array>} A list of menu item objects.
 */
export async function getMenuItems() {
  const url = `${API_BASE_URL}/menu/items/`;
  try {
    const response = await fetch(url);
    if (!response.ok) throw new Error(`Network response was not ok.`);
    return await response.json();
  } catch (error) {
    console.error("Failed to fetch menu items:", error);
    return [];
  }
}

export async function syncUserWithBackend(token) {
  const url = `${API_BASE_URL}/owner/sync-user`; // This MUST match your endpoint in owner.py
  
  // This payload creates a JSON object: {"token": "the-actual-token-string"}
  // This is the correct "envelope" that your backend expects.
  const payload = { token: token };

  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (!response.ok) {
      console.error("Failed to sync user with backend.", await response.text());
      return null;
    }
    
    return await response.json();
  } catch (error) {
    console.error("Connection error during user sync:", error);
    return null;
  }
}


// --- USER MESSAGING FUNCTIONS ---

/**
 * Sends a direct message from a logged-in user to the owner.
 * @param {string} token - The user's Firebase ID token for authentication.
 * @param {string} message - The message text to send.
 * @returns {Promise<Object>} The response from the server.
 */
export async function sendMessageToOwner(token, message) {
  const url = `${API_BASE_URL}/chats/contact-owner`;
  const payload = { message: message };

  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        // This Authorization header is critical for the secure endpoint
        'Authorization': `Bearer ${token}` 
      },
      body: JSON.stringify(payload)
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || "Failed to send message.");
    }
    
    return await response.json();

  } catch (error) {
    console.error("Failed to send message:", error);
    // Re-throw the error so the component can catch it and display a message
    throw error; 
  }
}

export async function getMyMessages(token) {
  const url = `${API_BASE_URL}/chats/my-messages`;
  try {
    const response = await fetch(url, {
      headers: {
        'Authorization': `Bearer ${token}` // Send the auth token for this secure endpoint
      }
    });
    if (!response.ok) {
      throw new Error(`Network response was not ok. Status: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error("Failed to fetch user messages:", error);
    return []; // Return an empty array on error to prevent the UI from crashing
  }
}

export async function initiatePayment(token, cartItems) {
  const url = `${API_BASE_URL}/payments/initiate-payment`;
  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        // This Authorization header is critical for the secure endpoint
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify(cartItems) // Send the full cart items array
    });

    if (!response.ok) {
      throw new Error(`Failed to initiate payment. Status: ${response.status}`);
    }
    
    return await response.json();

  } catch (error) {
    console.error("Payment initiation error:", error);
    // Re-throw the error to be handled by the component
    throw error;
  }
}

export async function getPromotions() {
  const url = `${API_BASE_URL}/promotions/`;
  try {
    const response = await fetch(url);
    if (!response.ok) throw new Error("Network response was not ok");
    return await response.json();
  } catch (error) {
    console.error("Failed to fetch promotions:", error);
    return [];
  }
}

export async function getRestaurantDetails() {
  const url = `${API_BASE_URL}/restaurant/details`;
  try {
    const response = await fetch(url);
    if (!response.ok) throw new Error("Network response was not ok");
    return await response.json();
  } catch (error) {
    console.error("Failed to fetch restaurant details:", error);
    return null;
  }
}

/**
 * Checks the final status of a payment with our backend.
 * This is the secure way to confirm a transaction.
 * @param {string} transactionId - The merchantTransactionId of the order.
 * @returns {Promise<Object|null>} The status response from the server.
 */
export async function checkPaymentStatus(transactionId) {
  // This URL must match the status check endpoint in your payments.py file
  const url = `${API_BASE_URL}/payments/status/${transactionId}`;
  try {
    const response = await fetch(url); // This is a GET request
    if (!response.ok) {
      throw new Error(`Network response was not ok. Status: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error("Failed to check payment status:", error);
    return null;
  }
}

export async function getMyOrders(token) {
  const url = `${API_BASE_URL}/payments/my-orders`; // You will create this backend endpoint
  try {
    const response = await fetch(url, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
    if (!response.ok) {
      throw new Error(`Network response was not ok. Status: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error("Failed to fetch user orders:", error);
    return []; // Return an empty array on error to prevent UI crashes
  }
}