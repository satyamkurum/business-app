# backend/app/services/sync_service.py
from pymongo import MongoClient
from pinecone import Pinecone
from langchain.storage import InMemoryStore
from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.retrievers import ParentDocumentRetriever
from langchain_core.documents import Document
from app.core.config import settings

def run_sync():
    """Clears and syncs all data types to their respective retrievers in Pinecone."""
    print("Starting full data synchronization with Pinecone...")
    mongo_client = MongoClient(settings.MONGO_URI)
    db = mongo_client["restaurantDB"]
    embeddings_model = SentenceTransformerEmbeddings(model_name='all-MiniLM-L6-v2')
    pc = Pinecone(api_key=settings.PINECONE_API_KEY)
    index = pc.Index("restaurant-menu")

    # --- 1. Sync Menu Items ---
    print("\n--- Syncing Menu Items ---")
    index.delete(delete_all=True, namespace="menu-items")
    
    menu_vectorstore = PineconeVectorStore(index_name="restaurant-menu", embedding=embeddings_model, namespace="menu-items")
    menu_retriever = ParentDocumentRetriever(
        vectorstore=menu_vectorstore,
        docstore=InMemoryStore(),
        child_splitter=RecursiveCharacterTextSplitter(chunk_size=400)
    )
    
    menu_items = list(db.menu_items.find({"is_available": True}))
    menu_docs = [
        Document(
            page_content=f"{item['name']}: {item['description']}",
            metadata={"doc_id": str(item["_id"]), "name": item["name"], "description": item["description"], "price_full": next((p['price'] for p in item.get('pricing', []) if p.get('size') == 'Full'), 0)}
        ) for item in menu_items
    ]
    if menu_docs:
        menu_retriever.add_documents(menu_docs, ids=None)
        print(f"Synced {len(menu_docs)} menu items.")

    # --- 2. Sync FAQs ---
    print("\n--- Syncing FAQs ---")
    index.delete(delete_all=True, namespace="faqs")

    faq_vectorstore = PineconeVectorStore(index_name="restaurant-menu", embedding=embeddings_model, namespace="faqs")
    faq_retriever = ParentDocumentRetriever(
        vectorstore=faq_vectorstore,
        docstore=InMemoryStore(),
        child_splitter=RecursiveCharacterTextSplitter(chunk_size=200) # Smaller chunks for FAQs
    )

    restaurant = db.restaurants.find_one()
    faqs = restaurant.get("faqs", []) if restaurant else []
    faq_docs = [
        Document(
            page_content=f"Question: {faq['question']} Answer: {faq['answer']}",
            metadata={"question": faq["question"], "answer": faq["answer"]}
        ) for faq in faqs
    ]
    if faq_docs:
        faq_retriever.add_documents(faq_docs, ids=None)
        print(f"Synced {len(faq_docs)} FAQs.")
        
    mongo_client.close()
    message = "Sync complete."
    print(message)
    return {"status": "success", "message": message}