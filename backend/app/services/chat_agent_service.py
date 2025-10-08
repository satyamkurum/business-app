# backend/app/services/chat_agent_service.py

from pymongo import MongoClient
from typing import List, Dict, Any, Optional
from langchain_core.messages import HumanMessage, AIMessage
from langchain.tools import tool
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain_core.documents import Document
import traceback
import re
import time
import logging
from functools import lru_cache
from datetime import datetime, timedelta
import json

from langchain_google_genai import ChatGoogleGenerativeAI
from app.core.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Session Memory Store ---
class SessionMemory:
    def __init__(self):
        self.sessions = {}
        self.cleanup_interval = 3600  # 1 hour
        self.last_cleanup = time.time()
    
    def get_session(self, session_id: str) -> Dict:
        self._cleanup_old_sessions()
        if session_id not in self.sessions:
            self.sessions[session_id] = {
                'created_at': time.time(),
                'last_active': time.time(),
                'context': {},
                'preferences': {},
                'recent_queries': [],
                'conversation_stage': 'greeting'
            }
        
        self.sessions[session_id]['last_active'] = time.time()
        return self.sessions[session_id]
    
    def update_session(self, session_id: str, key: str, value: Any):
        session = self.get_session(session_id)
        session[key] = value
    
    def add_to_context(self, session_id: str, key: str, value: Any):
        session = self.get_session(session_id)
        session['context'][key] = value
    
    def _cleanup_old_sessions(self):
        current_time = time.time()
        if current_time - self.last_cleanup > self.cleanup_interval:
            expired_sessions = [
                sid for sid, data in self.sessions.items()
                if current_time - data['last_active'] > 7200  # 2 hours
            ]
            for sid in expired_sessions:
                del self.sessions[sid]
            self.last_cleanup = current_time
            logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")

# Global session memory
session_memory = SessionMemory()

# --- Fast Query Classifier ---
class QueryClassifier:
    def __init__(self):
        self.patterns = {
            'greeting': [
                r'\b(hi|hello|hey|good\s*(morning|afternoon|evening)|greetings?)\b',
                r'^(hi|hello|hey)[\s\W]*$'
            ],
            'goodbye': [
                r'\b(bye|goodbye|see\s*you|thanks?\s*(bye|goodbye)|have\s*a\s*good\s*(day|night))\b',
                r'\b(exit|quit|done|finished?)\b'
            ],
            'how_are_you': [
                r'\b(how\s*are\s*you|how\s*do\s*you\s*do|how\s*is\s*it\s*going)\b'
            ],
            'menu_query': [
                r'\b(menu|food|dish|eat|hungry|meal|cuisine|spicy|vegetarian|vegan|price|cost)\b',
                r'\b(what.*available|show.*menu|recommend|suggest.*food)\b',
                r'\b(pizza|burger|chicken|rice|bread|dessert|drink|beverage|starter|appetizer)\b',
                r'\b(under|below|less than|within).*(\d+).*rupees?\b'
            ],
            'restaurant_info': [
                r'\b(hours?|time|open|close|location|address|phone|contact|delivery|takeout)\b',
                r'\b(where.*located|how.*reach|reservation|book.*table)\b'
            ],
            'promotion_query': [
                r'\b(deal|discount|offer|promotion|special|coupon|cheap)\b',
                r'\b(any.*offer|save.*money|best.*deal)\b'
            ]
        }
        
        # Compile patterns for speed
        self.compiled_patterns = {
            category: [re.compile(pattern, re.IGNORECASE) 
                      for pattern in patterns]
            for category, patterns in self.patterns.items()
        }
    
    def classify(self, query: str) -> str:
        query_lower = query.lower().strip()
        
        # Quick length check for simple greetings
        if len(query_lower) <= 10 and any(word in query_lower for word in ['hi', 'hello', 'hey']):
            return 'greeting'
        
        # Check each category
        for category, compiled_patterns in self.compiled_patterns.items():
            if any(pattern.search(query_lower) for pattern in compiled_patterns):
                return category
        
        return 'general'

query_classifier = QueryClassifier()

# --- Response Templates for Fast Replies ---
class ResponseTemplates:
    @staticmethod
    def greeting_response(session_id: str) -> str:
        session = session_memory.get_session(session_id)
        user_name = session['context'].get('user_name', '')
        
        greetings = [
            f"Hello{' ' + user_name if user_name else ''}! 😊 Welcome to our restaurant! I'm Lily, your AI assistant.",
            f"Hi there{' ' + user_name if user_name else ''}! 👋 I'm Lily and I'm here to help you explore our delicious menu!",
            f"Hey{' ' + user_name if user_name else ''}! 🍽️ Ready to discover some amazing food? I'm Lily, your personal food guide!"
        ]
        
        import random
        base_greeting = random.choice(greetings)
        
        help_text = "\n\nI can help you with:\n- 🍕 Menu items and recommendations\n- 💰 Prices and deals\n- 📍 Restaurant info and hours\n- 🎉 Current promotions"
        
        session_memory.update_session(session_id, 'conversation_stage', 'active')
        return base_greeting + help_text
    
    @staticmethod
    def how_are_you_response() -> str:
        responses = [
            "I'm doing great, thank you! 😊 Ready to help you find some delicious food. What are you in the mood for today?",
            "I'm fantastic! 🌟 Just excited to help you discover our amazing menu. Any particular cuisine you're craving?",
            "I'm wonderful, thanks for asking! 💫 I'm here and ready to make your food ordering experience amazing!"
        ]
        import random
        return random.choice(responses)
    
    @staticmethod
    def goodbye_response(session_id: str) -> str:
        session = session_memory.get_session(session_id)
        responses = [
            "Thank you for visiting! 👋 Come back soon for more delicious food!",
            "Goodbye! 🌟 Hope to see you again soon. Enjoy your meal if you ordered!",
            "Take care! 💫 We're always here when you need great food recommendations!"
        ]
        import random
        session_memory.update_session(session_id, 'conversation_stage', 'ended')
        return random.choice(responses)

response_templates = ResponseTemplates()

# --- Enhanced Cache System ---
class QueryCache:
    def __init__(self, max_size=500, ttl=1800):  # 30 minutes TTL
        self.cache = {}
        self.access_times = {}
        self.max_size = max_size
        self.ttl = ttl
    
    def _is_valid(self, key: str) -> bool:
        if key not in self.cache:
            return False
        return time.time() - self.access_times[key] < self.ttl
    
    def get(self, key: str) -> Optional[str]:
        if self._is_valid(key):
            self.access_times[key] = time.time()
            logger.info(f"Cache hit for query: {key[:50]}...")
            return self.cache[key]
        elif key in self.cache:
            del self.cache[key]
            del self.access_times[key]
        return None
    
    def set(self, key: str, value: str):
        # Clean old entries if cache is full
        if len(self.cache) >= self.max_size:
            oldest_key = min(self.access_times, key=self.access_times.get)
            del self.cache[oldest_key]
            del self.access_times[oldest_key]
        
        self.cache[key] = value
        self.access_times[key] = time.time()
        logger.info(f"Cached response for query: {key[:50]}...")

query_cache = QueryCache()

# --- Connection Pool for MongoDB ---
class MongoConnectionPool:
    def __init__(self):
        self._client = None
        self._db = None
    
    @property
    def client(self):
        if self._client is None:
            self._client = MongoClient(
                settings.MONGO_URI,
                maxPoolSize=20,
                minPoolSize=5,
                maxIdleTimeMS=30000,
                serverSelectionTimeoutMS=5000
            )
        return self._client
    
    @property
    def db(self):
        if self._db is None:
            self._db = self.client["restaurentDB"]
        return self._db

mongo_pool = MongoConnectionPool()

# --- Initialize Embeddings and Vectorstores ---
logger.info("=== Initializing Optimized Chat Agent Service (with Gemini Embeddings) ===")

try:
    # --- THIS IS THE CHANGE ---
    # Import the correct library at the top of your file:
    # from langchain_google_genai import GoogleGenerativeAIEmbeddings

    # Initialize embeddings using the Google Gemini API model.
    # This offloads all heavy computation from our server.
    embedding_model = GoogleGenerativeAIEmbeddings(
        google_api_key=settings.GOOGLE_API_KEY, 
        model="gemini-embedding-001"
    )
    logger.info("✅ Google Gemini Embeddings model initialized successfully")
    
    # The rest of the logic remains the same as it's a drop-in replacement.
    menu_vectorstore = PineconeVectorStore(
        index_name="restaurant-menu", 
        embedding=embedding_model, 
        namespace="menu-items"
    )
    
    faq_vectorstore = PineconeVectorStore(
        index_name="restaurant-menu", 
        embedding=embedding_model, 
        namespace="faqs"
    )
    logger.info("✅ Pinecone vectorstores initialized successfully")
    
except Exception as e:
    logger.error(f"❌ Error initializing vectorstores: {e}")
    raise
# --- Enhanced Tools with Structured Responses ---

@tool
def category_filter_search(category: str, max_price: Optional[int] = None) -> str:
    """
    Search for menu items by specific category (starters, mains, desserts, etc.) with optional price filtering.
    Use this when customers ask for specific categories like "starters under 150" or "desserts below 200".
    
    Args:
        category: The menu category to search (e.g., "starters", "appetizers", "mains", "desserts", "paneer")
        max_price: Maximum price filter in rupees (optional, use None for no price limit)
    """
    logger.info(f"🔧 TOOL CALLED: category_filter_search - Category: {category}, Max Price: {max_price}")
    
    # Check cache first
    cache_key = f"category:{category.lower()}:{max_price}"
    cached_result = query_cache.get(cache_key)
    if cached_result:
        return cached_result
    
    try:
        start_time = time.time()
        db = mongo_pool.db
        
        # Enhanced category patterns for matching
        category_patterns = {
            'starter': ['starter', 'appetizer', 'snack', 'chaat'],
            'appetizer': ['starter', 'appetizer', 'snack', 'chaat'],
            'main': ['main', 'curry', 'rice', 'biryani', 'bread', 'dal', 'sabzi'],
            'dessert': ['dessert', 'sweet', 'ice cream', 'kulfi'],
            'drink': ['drink', 'beverage', 'juice', 'tea', 'coffee', 'lassi'],
            'pizza': ['pizza'],
            'chinese': ['chinese', 'noodles', 'fried rice', 'manchurian'],
            'paneer': ['paneer']
        }
        
        category_lower = category.lower()
        matching_patterns = []
        
        # Find matching patterns
        for key, patterns in category_patterns.items():
            if key in category_lower or any(pattern in category_lower for pattern in patterns):
                matching_patterns.extend(patterns)
        
        # If no specific patterns found, use the original category
        if not matching_patterns:
            matching_patterns = [category_lower]
        
        # Method 1: Use MongoDB aggregation with $lookup to join categories
        try:
            # Build the aggregation pipeline
            pipeline = [
                # Join with categories collection
                {
                    "$lookup": {
                        "from": "categories",
                        "localField": "category_id", 
                        "foreignField": "_id",
                        "as": "category_info"
                    }
                },
                # Unwind the category array
                {
                    "$unwind": {
                        "path": "$category_info",
                        "preserveNullAndEmptyArrays": True
                    }
                },
                # Match based on category name, item name, or tags
                {
                    "$match": {
                        "$or": [
                            # Match category name
                            {"category_info.name": {"$regex": "|".join(matching_patterns), "$options": "i"}},
                            # Match item name for specific items like paneer
                            {"name": {"$regex": "|".join(matching_patterns), "$options": "i"}},
                            # Match tags
                            {"tags": {"$in": [pattern.title() for pattern in matching_patterns] + 
                                             [pattern.upper() for pattern in matching_patterns] + 
                                             [pattern.lower() for pattern in matching_patterns]}}
                        ]
                    }
                }
            ]
            
            logger.info(f"📊 MongoDB Aggregation Pipeline: {pipeline}")
            items_cursor = db.menu_items.aggregate(pipeline)
            items = list(items_cursor)
            
            logger.info(f"📊 Found {len(items)} items using aggregation for category '{category}'")
            
        except Exception as e:
            logger.error(f"❌ Aggregation failed: {e}")
            # Fallback to simple search
            items = []
        
        # Method 2: Fallback - Search by item name and tags only
        if not items:
            logger.info("🔄 Using fallback method - searching by name and tags only")
            fallback_query = {
                "$or": [
                    {"name": {"$regex": "|".join(matching_patterns), "$options": "i"}},
                    {"tags": {"$in": [pattern.title() for pattern in matching_patterns] + 
                                     [pattern.upper() for pattern in matching_patterns] + 
                                     [pattern.lower() for pattern in matching_patterns]}}
                ]
            }
            
            items_cursor = db.menu_items.find(fallback_query, {'_id': 0})
            items = list(items_cursor)
            logger.info(f"📊 Found {len(items)} items using fallback method")
        
        if not items:
            result = f"I couldn't find any items in the '{category}' category. Try asking about 'starters', 'mains', 'desserts', 'drinks', or specific items like 'paneer'."
            query_cache.set(cache_key, result)
            return result
        
        # Process items and filter by price
        processed_items = []
        for item in items:
            name = item.get('name', 'Unknown')
            description = item.get('description', 'Delicious item')
            pricing = item.get('pricing', [])
            is_available = item.get('is_available', True)
            
            # Extract minimum price for filtering
            min_price = None
            price_display = "Price not available"
            
            if pricing and isinstance(pricing, list):
                valid_prices = []
                for p in pricing:
                    price_val = p.get('price')
                    if price_val and isinstance(price_val, (int, float)):
                        valid_prices.append({
                            'size': p.get('size', 'Regular'),
                            'price': price_val
                        })
                        if min_price is None or price_val < min_price:
                            min_price = price_val
                
                if valid_prices:
                    if len(valid_prices) == 1:
                        price_display = f"₹{valid_prices[0]['price']}"
                    else:
                        price_parts = [f"{p['size']}: ₹{p['price']}" for p in valid_prices]
                        price_display = " | ".join(price_parts)
            
            # Apply price filter if specified (only if max_price is not None)
            if max_price is not None and min_price is not None and min_price > max_price:
                continue
            
            # Get dietary information
            dietary_notes = []
            dietary_info = item.get("dietary_info", {})
            tags = item.get("tags", [])
            
            if dietary_info.get("is_vegan_available"):
                dietary_notes.append("🌱 Vegan")
            if dietary_info.get("is_gluten_free"):
                dietary_notes.append("🌾 Gluten-free")
            
            # Check tags for dietary info
            if tags:
                tag_lower_set = {str(tag).lower() for tag in tags}
                if any(veg_tag in tag_lower_set for veg_tag in ["vegetarian", "veg"]):
                    dietary_notes.append("🥬 Vegetarian")
                if "non-veg" in tag_lower_set or "nonveg" in tag_lower_set:
                    dietary_notes.append("🍖 Non-Veg")
                if "spicy" in tag_lower_set:
                    dietary_notes.append("🌶️ Spicy")
                if "popular" in tag_lower_set:
                    dietary_notes.append("⭐ Popular")
            
            # Get category name if available from aggregation
            category_name = ""
            if 'category_info' in item:
                category_name = item['category_info'].get('name', '')
            
            processed_items.append({
                'name': name,
                'description': description,
                'price_display': price_display,
                'min_price': min_price or 0,
                'is_available': is_available,
                'dietary_notes': dietary_notes,
                'category_name': category_name,
                'prep_time': item.get('prep_time_minutes', 0)
            })
        
        if not processed_items and max_price is not None:
            result = f"I couldn't find any {category} items under ₹{max_price}. Try increasing your budget or check other categories!"
            query_cache.set(cache_key, result)
            return result
        
        # Sort by price (lowest first)
        processed_items.sort(key=lambda x: x['min_price'])
        
        # Format structured response
        if max_price is not None:
            result = f"🍽️ **{category.title()} items under ₹{max_price}:**\n\n"
        else:
            result = f"🍽️ **{category.title()} items:**\n\n"
        
        # Create bullet list of items (limit to 10 for readability)
        displayed_items = 0
        for item in processed_items[:10]:
            if displayed_items >= 10:
                break
                
            availability = "✅ Available" if item['is_available'] else "❌ Unavailable"
            dietary_str = " | ".join(item['dietary_notes'][:3]) if item['dietary_notes'] else "ℹ️ No dietary info"
            
            result += f"- **{item['name']}**\n"
            result += f"  📝 {item['description']}\n"
            result += f"  💰 {item['price_display']}\n"
            result += f"  {availability}\n"
            
            # Add category name if available
            if item['category_name']:
                result += f"  📂 Category: {item['category_name']}\n"
            
            # Add prep time if available
            if item['prep_time'] > 0:
                result += f"  ⏱️ Prep time: {item['prep_time']} minutes\n"
                
            result += f"  🏷️ {dietary_str}\n\n"
            
            displayed_items += 1
        
        # Add summary
        if len(processed_items) > 10:
            result += f"💡 And {len(processed_items) - 10} more {category} items available!\n\n"
        
        result += "❓ Want details about any specific item? Just ask!"
        
        # Cache the result
        query_cache.set(cache_key, result)
        
        logger.info(f"✅ Category search completed in {time.time() - start_time:.2f}s")
        return result
        
    except Exception as e:
        logger.error(f"❌ Category search error: {e}")
        logger.error(f"❌ Full error traceback: {traceback.format_exc()}")
        return f"I'm having trouble searching {category} items right now. Please try again or ask about specific items!"


# UPDATED: Enhanced menu_search to better handle price queries and use structured format
@tool
def menu_search(query: str) -> str:
    """
    Search the restaurant menu for food items, dishes, ingredients, or menu categories.
    Use this tool when customers ask about:
    - What food is available
    - Specific cuisines or dish types
    - Spicy, vegetarian, or other dietary options
    - Menu categories or sections
    - General food searches (NOT for category + price combinations)
    """
    logger.info(f"🔧 TOOL CALLED: menu_search - Query: {query}")
    
    # Check if this should use category_filter_search instead
    category_price_pattern = r'(starter|appetizer|main|dessert|drink|beverage|paneer).*?(under|below|less than|within)\s*(\d+)'
    if re.search(category_price_pattern, query.lower()):
        logger.info("🔄 Redirecting to category_filter_search for better results")
        # Extract category and price
        match = re.search(r'(starter|appetizer|main|dessert|drink|beverage|paneer)', query.lower())
        price_match = re.search(r'(under|below|less than|within)\s*(\d+)', query.lower())
        
        if match and price_match:
            category = match.group(1)
            max_price = int(price_match.group(2))
            return category_filter_search(category, max_price)
    
    # Check cache first
    cache_key = f"menu:{query.lower().strip()}"
    cached_result = query_cache.get(cache_key)
    if cached_result:
        return cached_result
    
    try:
        start_time = time.time()
        
        # Direct similarity search with timeout
        results = menu_vectorstore.similarity_search(
            query, 
            k=6,  # Reasonable number for general searches
            namespace="menu-items"
        )
        
        search_time = time.time() - start_time
        logger.info(f"📊 Pinecone search took {search_time:.2f}s, returned {len(results)} results")
        
        if not results:
            result = "I couldn't find any menu items matching your query. Try asking about our popular categories like 'pizza', 'indian food', 'starters', or 'vegetarian options'."
            query_cache.set(cache_key, result)
            return result
        
        # Format results with structured bullet points
        result = "🍽️ **Here are our menu items:**\n\n"
        
        for doc in results[:6]:  # Limit to 6 items
            name = doc.metadata.get('name', 'Unknown')
            description = doc.page_content if doc.page_content else doc.metadata.get('description', 'Delicious item')
            
            # Get price information
            pricing = doc.metadata.get('pricing', [])
            price_display = "Price not available"
            
            if pricing and isinstance(pricing, list):
                valid_prices = []
                for p in pricing:
                    if p.get('price'):
                        valid_prices.append(f"{p.get('size', 'Regular')}: ₹{p['price']}")
                
                if valid_prices:
                    price_display = " | ".join(valid_prices)
            
            # Availability
            is_available = doc.metadata.get('is_available', True)
            availability = "✅ Available" if is_available else "❌ Currently unavailable"
            
            # Category
            category = doc.metadata.get('category', 'Menu Item')
            
            result += f"- **{name}**\n"
            result += f"  📝 {description}\n"
            result += f"  💰 {price_display}\n"
            result += f"  📂 Category: {category}\n"
            result += f"  {availability}\n\n"
        
        result += "💡 Want more details about any item? Just ask!"
        
        # Cache the result
        query_cache.set(cache_key, result)
        
        logger.info(f"✅ Menu search completed in {time.time() - start_time:.2f}s")
        return result
        
    except Exception as e:
        error_msg = f"Sorry, I'm having trouble searching our menu right now. Please try again or ask me about specific food categories."
        logger.error(f"❌ Menu search error: {e}")
        return error_msg

@tool  
def faq_search(query: str) -> str:
    """
    Search restaurant FAQs for information about policies, hours, location, delivery, etc.
    Use this tool when customers ask about:
    - Restaurant hours/timings
    - Location and contact info
    - Delivery or takeout policies
    - Reservations
    - General restaurant policies
    """
    logger.info(f"🔧 TOOL CALLED: faq_search - Query: {query}")
    
    # Check cache first
    cache_key = f"faq:{query.lower().strip()}"
    cached_result = query_cache.get(cache_key)
    if cached_result:
        return cached_result
    
    try:
        start_time = time.time()
        
        results = faq_vectorstore.similarity_search(
            query,
            k=3,
            namespace="faqs"
        )
        
        logger.info(f"📊 FAQ search took {time.time() - start_time:.2f}s, returned {len(results)} results")
        
        if not results:
            result = "I couldn't find specific information about that. Please contact our restaurant directly, or ask me about hours, location, or delivery."
            query_cache.set(cache_key, result)
            return result
        
        # Format FAQ results with bullet points
        result = "ℹ️ **Restaurant Information:**\n\n"
        
        for doc in results:
            question = doc.metadata.get('question', 'Restaurant Info')
            answer = doc.page_content
            
            result += f"- **{question}**\n"
            result += f"  ✅ {answer}\n\n"
        
        # Cache the result
        query_cache.set(cache_key, result)
        
        logger.info(f"✅ FAQ search completed in {time.time() - start_time:.2f}s")
        return result
        
    except Exception as e:
        error_msg = f"I'm having trouble accessing restaurant information right now. Please try again or contact us directly."
        logger.error(f"❌ FAQ search error: {e}")
        return error_msg

@tool
def exact_lookup(item_name: str) -> dict:
    """
    Performs a direct, typo-tolerant database lookup for a specific menu item's full details.
     
    Use this for precise factual questions (like price, ingredients, availability, portion sizes, etc.) about a SPECIFICALLY NAMED item.
    """
    logger.info(f"🔧 TOOL CALLED: exact_lookup - Item: {item_name}")
    
    # Check cache first
    cache_key = f"item:{item_name.lower().strip()}"
    cached_result = query_cache.get(cache_key)
    if cached_result and isinstance(cached_result, str):
        try:
            return json.loads(cached_result)
        except:
            pass
    
    try:
        start_time = time.time()
        db = mongo_pool.db
        
        # Strategy 1: Atlas Search (primary method)
        try:
            pipeline = [
                {
                    "$search": {
                        "index": "default",
                        "autocomplete": {
                            "query": item_name,
                            "path": "name",
                            "fuzzy": { "maxEdits": 1, "prefixLength": 3 }
                        }
                    }
                },
                {"$limit": 1}
            ]
            results = list(db.menu_items.aggregate(pipeline))
            
            if results:
                result = _format_item_response(results[0])
                query_cache.set(cache_key, json.dumps(result))
                logger.info(f"✅ Exact lookup completed in {time.time() - start_time:.2f}s")
                return result
        except Exception:
            pass
        
        # Strategy 2: Regex search (fallback)
        result = db.menu_items.find_one(
            {"name": {"$regex": f".*{item_name}.*", "$options": "i"}}
        )
        
        if result:
            formatted_result = _format_item_response(result)
            query_cache.set(cache_key, json.dumps(formatted_result))
            logger.info(f"✅ Exact lookup completed in {time.time() - start_time:.2f}s")
            return formatted_result
        
        # No results found
        error_result = {
            "error": f"I couldn't find '{item_name}' on our menu. Try asking about similar items or browse our menu categories!",
            "success": False
        }
        return error_result
            
    except Exception as e:
        logger.error(f"❌ Exact lookup error: {e}")
        return {"error": "I'm having trouble looking up that item. Please try again!", "success": False}

def _format_item_response(item: dict) -> dict:
    """Helper function to format the item response consistently."""
    # Same implementation as before but with emojis for better UX
    name = item.get("name", "Unknown Item")
    description = item.get("description", "No description available")
    
    # Format pricing efficiently
    price_str = "Not available"
    pricing = item.get("pricing", [])
    if pricing and isinstance(pricing, list):
        price_parts = [f"{p.get('size', '')}: ₹{p.get('price', '')}" 
                      for p in pricing if p.get('size') and p.get('price')]
        if price_parts:
            price_str = ", ".join(price_parts)
    
    # Availability with emoji
    is_available = item.get("is_available", True)
    availability_str = "✅ Available" if is_available else "❌ Currently unavailable"
    
    # Preparation time
    prep_time = item.get("prep_time_minutes")
    prep_time_str = f"⏱️ {prep_time} minutes" if prep_time else "⏱️ Standard timing"
    
    # Build response with emojis
    return {
        "name": f"🍽️ {name}",
        "description": description,
        "price": f"💰 {price_str}",
        "is_available": availability_str,
        "preparation_time": prep_time_str,
        "key_ingredients": item.get("key_ingredients", []),
        "tags": item.get("tags", []),
        "dietary_notes": _get_dietary_notes(item),
        "image_url": item.get("image_url"),
        "customization_options": item.get("customization_options", []),
        "success": True
    }

def _get_dietary_notes(item: dict) -> List[str]:
    """Extract dietary information with emojis."""
    dietary_notes = []
    dietary_info = item.get("dietary_info", {})
    tags = item.get("tags", [])
    
    if dietary_info.get("is_vegan_available"):
        dietary_notes.append("🌱 Vegan option available")
    if dietary_info.get("is_gluten_free"):
        dietary_notes.append("🌾 Gluten-free")
    if dietary_info.get("is_jain_available"):
        dietary_notes.append("🙏 Jain option available")
    
    # Check tags
    tag_lower_set = {tag.lower() for tag in tags}
    if any(tag in tag_lower_set for tag in ["vegetarian", "veg"]):
        dietary_notes.append("🥬 Vegetarian")
    if "non-veg" in tag_lower_set:
        dietary_notes.append("🍖 Non-Vegetarian")
    if "spicy" in tag_lower_set:
        dietary_notes.append("🌶️ Spicy")
    
    return dietary_notes if dietary_notes else ["ℹ️ No special dietary options"]

@tool
def promotion_lookup() -> str:
    """
    Get current promotions, deals, and special offers.
    Use this when customers ask about discounts, deals, or special offers.
    """
    logger.info("🔧 TOOL CALLED: promotion_lookup")
    
    # Check cache first
    cache_key = "promotions:current"
    cached_result = query_cache.get(cache_key)
    if cached_result:
        return cached_result
    
    try:
        start_time = time.time()
        db = mongo_pool.db
        
        promos = list(db.promotions.find({}, {"_id": 0}))
        
        if promos:
            result = "🎉 **Current Promotions:**\n\n"
            for promo in promos:
                result += f"- **{promo.get('title', 'Special Offer')}**\n"
                result += f"  📝 {promo.get('description', 'Amazing deal!')}\n"
                if 'discount' in promo:
                    result += f"  💰 Discount: {promo['discount']}\n"
                if 'valid_until' in promo:
                    result += f"  ⏰ Valid until: {promo['valid_until']}\n"
                result += "\n"
            
            # Cache for shorter time since promotions change
            short_cache = QueryCache(ttl=900)  # 15 minutes
            short_cache.set(cache_key, result)
            
            logger.info(f"✅ Promotion lookup completed in {time.time() - start_time:.2f}s")
            return result
        else:
            result = "We don't have any active promotions right now, but our regular menu offers great value! 🍽️✨"
            query_cache.set(cache_key, result)
            return result
            
    except Exception as e:
        logger.error(f"❌ Promotion lookup error: {e}")
        return "I'm having trouble getting current promotions. Please check back later or ask about our regular menu!"

# --- Enhanced Agent Setup ---
tools = [menu_search, category_filter_search, faq_search, exact_lookup, promotion_lookup]

# Optimized LLM configuration
llm = ChatGoogleGenerativeAI(
    google_api_key=settings.GOOGLE_API_KEY, 
    model="gemini-1.5-flash",
    temperature=0.0,
    convert_system_message_to_human=True,
    request_timeout=10  # Add timeout
)

# Enhanced prompt with better structuring instructions
prompt = ChatPromptTemplate.from_messages([
    ("system", """You are Lily, a friendly AI restaurant assistant. You're intelligent, efficient, and provide well-structured responses.

    🧠 TOOL SELECTION RULES - VERY IMPORTANT:
    - For simple greetings → respond naturally WITHOUT using tools
    - For CATEGORY + PRICE queries (e.g., "starters under 150", "paneer items below 200") → ALWAYS use category_filter_search tool
    - For general food searches (e.g., "show me spicy food", "vegetarian options") → use menu_search tool
    - For restaurant info → use faq_search tool  
    - For specific item details → use exact_lookup tool
    - For deals/promotions → use promotion_lookup tool
    - Never give factual data that doesn't come from tool usage.

    📋 RESPONSE STRUCTURE RULES - CRITICAL:
    1. ALWAYS use bullet points (`- `) when listing multiple items -- MUST.
    2. You MUST use Markdown for all responses that contain data.
    3. Use bullet points (`-`) for lists of items -- MUST.
    4. Make dish names and key info **bold** (`**Dish Name**`).
    5. Include ALL available information: name, description, price, availability
    6. Format prices clearly with currency symbol (₹)
    7. Use emojis to make responses engaging and organized but not too much.
    8. NEVER say "price not available" if you can get pricing data
    9. Complete the full request - don't give partial answers
    10. If user asks in Hinglish, give answer in same language.

    🎯 SPECIFIC QUERY HANDLING:
    - "starters under 150" → category_filter_search("starter", 150)
    - "paneer items with prices" → category_filter_search("paneer", None)
    - "list five paneer items" → category_filter_search("paneer", None)
    - "cheap appetizers" → category_filter_search("appetizer", 200)
    - "desserts below 100" → category_filter_search("dessert", 100)

    💡 INTELLIGENCE RULES:
    1. Always choose the RIGHT tool for the query type
    2. Be proactive - suggest related items or actions
    3. Keep responses conversational yet complete
    4. Remember context from conversation
    5. End with helpful suggestions but not always.
    NEVER use tools for: greetings, thanks, how are you, goodbye, general chat
    ALWAYS use category_filter_search for: category + price combinations, specific category requests
    ALWAYS use menu_search for: general food searches without specific categories
    
    CRITICAL: When users ask for items by category (with or without price), use category_filter_search tool for accurate database results."""),
    MessagesPlaceholder(variable_name="chat_history"),
    ("user", "{input}"),
     MessagesPlaceholder(variable_name="agent_scratchpad"),
])

logger.info("=== Creating Enhanced Agent ===")
try:
    agent = create_tool_calling_agent(llm, tools, prompt)
    agent_executor = AgentExecutor(
        agent=agent, 
        tools=tools, 
        verbose=False,  # Reduce verbosity for speed
        handle_parsing_errors=True,
        max_iterations=3,  # Reduce iterations
        early_stopping_method="generate",
        return_intermediate_steps=False  # Disable for speed
    )
    logger.info("✅ Enhanced Agent created successfully")
except Exception as e:
    logger.error(f"❌ Agent creation failed: {e}")
    raise

# --- Main Service Function with Enhanced Intelligence ---

async def get_ai_response(session_id: str, question: str, chat_history: List[Dict[str, Any]]):
    """
    Enhanced service function with smart routing, memory, and structured responses
    """
    start_time = time.time()
    logger.info(f"🔄 Processing query for session {session_id}: {question[:50]}...")
    
    # Get session memory
    session = session_memory.get_session(session_id)
    session_memory.add_to_context(session_id, 'last_query', question)
    
    # Smart classification for fast responses
    query_type = query_classifier.classify(question)
    logger.info(f"🎯 Classified as: {query_type}")
    
    # Handle simple queries without tools
    if query_type == 'greeting':
        response = response_templates.greeting_response(session_id)
        logger.info(f"✅ Fast greeting response in {time.time() - start_time:.2f}s")
        return response
    
    elif query_type == 'how_are_you':
        response = response_templates.how_are_you_response()
        logger.info(f"✅ Fast how-are-you response in {time.time() - start_time:.2f}s")
        return response
    
    elif query_type == 'goodbye':
        response = response_templates.goodbye_response(session_id)
        logger.info(f"✅ Fast goodbye response in {time.time() - start_time:.2f}s")
        return response
    
    # For complex queries, use agent with context
    try:
        # Convert recent chat history (keep memory light)
        history_messages = []
        for message in chat_history[-3:]:  # Only last 3 for speed
            if message["sender"] == "user":
                history_messages.append(HumanMessage(content=message["text"]))
            else:
                history_messages.append(AIMessage(content=message["text"]))
        
        # Add session context to input
        context_info = ""
        if session['context']:
            if 'user_preferences' in session['context']:
                context_info = f"User preferences: {session['context']['user_preferences']}. "
        
        # Enhanced input processing for better tool selection
        enhanced_input = f"{context_info}{question}"
        
        # Check for category + price patterns to guide tool selection
        category_price_pattern = r'(starter|appetizer|main|dessert|drink|beverage).*?(under|below|less than|within)\s*(\d+)'
        if re.search(category_price_pattern, question.lower()):
            logger.info("🎯 Detected category + price query - will use category_filter_search")
        
        # Invoke agent
        response = await agent_executor.ainvoke({
            "input": enhanced_input,
            "chat_history": history_messages
        })
        
        output = response.get("output", "").strip()
        
        if not output:
            output = "I apologize, I couldn't process that properly. Could you please rephrase your question?"
        
        # Update session context based on query type
        if query_type == 'menu_query':
            session_memory.add_to_context(session_id, 'looking_for_food', True)
            # Extract any mentioned price range for future context
            price_match = re.search(r'(\d+)', question)
            if price_match:
                session_memory.add_to_context(session_id, 'budget_mentioned', int(price_match.group(1)))
        
        total_time = time.time() - start_time
        logger.info(f"✅ Complex query response in {total_time:.2f}s")
        
        return output
        
    except Exception as e:
        logger.error(f"❌ Error in get_ai_response: {e}")
        fallback_responses = {
            'menu_query': "I'm having trouble accessing our menu right now. Please try asking about specific food items or categories like 'pizza' or 'vegetarian options'.",
            'restaurant_info': "I'm having trouble getting restaurant information. Please call us directly or visit our website for current hours and location details.",
            'promotion_query': "I can't access current promotions right now. Please check our website or ask our staff about current deals!",
            'general': "I'm experiencing some technical difficulties. Please try rephrasing your question or contact our restaurant directly for assistance."
        }
        
        return fallback_responses.get(query_type, fallback_responses['general'])

logger.info("=== Enhanced Chat Agent Service Ready! ===")
