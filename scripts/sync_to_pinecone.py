# backend/app/services/sync_service.py
import os
import hashlib
import json
from pymongo import MongoClient
from sentence_transformers import SentenceTransformer
from pinecone import Pinecone
from app.core.config import settings

# --- INITIALIZATION ---
mongo_client = MongoClient(settings.MONGO_URI)
db = mongo_client["restaurantDB"]
menu_items_collection = db["menu_items"]
model = SentenceTransformer('all-MiniLM-L6-v2')
pc = Pinecone(api_key=settings.PINECONE_API_KEY)
index = pc.Index("restaurant-menu")

def generate_hash(data_dict):
    """Creates a unique hash for a dictionary."""
    # We sort the dictionary to ensure consistent hash generation
    sorted_dict_str = json.dumps(data_dict, sort_keys=True)
    return hashlib.md5(sorted_dict_str.encode()).hexdigest()

def run_sync():
    """
    Optimized sync logic. Compares data hashes to only update what's new or changed.
    """
    # 1. Get current state from MongoDB
    print("Fetching all items from MongoDB...")
    mongo_items = list(menu_items_collection.find({}))
    mongo_data = {}
    for item in mongo_items:
        # Create a dictionary of the data we care about for the hash
        relevant_data = {
            "name": item["name"],
            "description": item["description"],
            "price_full": next((p['price'] for p in item.get('pricing', []) if p.get('size') == 'Full'), 0)
        }
        mongo_data[str(item["_id"])] = {
            "hash": generate_hash(relevant_data),
            "full_doc": item # Keep the full document for embedding
        }

    # 2. Get current state from Pinecone (IDs and hashes)
    print("Fetching all vector IDs and metadata from Pinecone...")
    response = index.query(vector=[0]*384, top_k=10000, include_metadata=True, namespace="menu-items")
    pinecone_data = {res.id: res.metadata.get("data_hash") for res in response.matches}
    
    # 3. Compare and find what needs to be updated or added
    vectors_to_upsert = []
    mongo_ids = set(mongo_data.keys())
    pinecone_ids = set(pinecone_data.keys())

    # Find items in Mongo that are not in Pinecone
    new_ids = mongo_ids - pinecone_ids
    # Find items in both but with different hashes (updated items)
    common_ids = mongo_ids.intersection(pinecone_ids)
    changed_ids = {id_str for id_str in common_ids if mongo_data[id_str]["hash"] != pinecone_data[id_str]}
    
    ids_to_process = new_ids.union(changed_ids)

    if not ids_to_process:
        print("Pinecone is already in sync. Nothing to do.")
        return {"status": "success", "message": "Already in sync.", "added": 0, "updated": 0}

    print(f"Found {len(new_ids)} new items and {len(changed_ids)} updated items.")

    # 4. Process and upsert only the necessary items
    for item_id in ids_to_process:
        item = mongo_data[item_id]["full_doc"]
        data_hash = mongo_data[item_id]["hash"]

        text_to_embed = f"{item['name']}: {item['description']}"
        embedding = model.encode(text_to_embed).tolist()
        
        metadata = {
            "name": item["name"],
            "description": item["description"],
            "category_id": str(item["category_id"]),
            "price_full": next((p['price'] for p in item.get('pricing', []) if p.get('size') == 'Full'), 0),
            "data_hash": data_hash # Store the new hash
        }
        
        vectors_to_upsert.append({"id": str(item["_id"]), "values": embedding, "metadata": metadata})

    if vectors_to_upsert:
        print(f"Upserting {len(vectors_to_upsert)} vectors to Pinecone...")
        index.upsert(vectors=vectors_to_upsert, namespace="menu-items")
    
    message = f"Sync complete. Added: {len(new_ids)}. Updated: {len(changed_ids)}."
    print(message)
    return {"status": "success", "message": message, "added": len(new_ids), "updated": len(changed_ids)}