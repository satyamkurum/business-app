# 🐰 Lily AI – Full-Stack Restaurant Platform

<p align="center">
  <img src="https://placehold.co/600x300/ff6b6b/ffffff?text=Lily+AI+Platform" alt="Lily AI Banner" style="border-radius: 12px;"/>
</p>

<p align="center">
  <strong>An end-to-end e-commerce and customer service solution for restaurants, featuring a stateful AI assistant, a customer-facing ordering system, and a comprehensive owner's dashboard.</strong>
</p>

<p align="center">
  <img alt="Python" src="https://img.shields.io/badge/Python-3.11-blue.svg"/>
  <img alt="React" src="https://img.shields.io/badge/React-18-blue.svg"/>
  <img alt="License" src="https://img.shields.io/badge/License-MIT-green.svg"/>
</p>

---

##  Table of Contents
- [ Overview](#-overview)
- [ Key Features](#-key-features)
  - [ Customer-Facing Application (React)](#-customer-facing-application-react)
  - [ Owner's Dashboard (Streamlit)](#-owners-dashboard-streamlit)
  - [ AI Backend (FastAPI)](#-ai-backend-fastapi)
- [🏛️ Architecture](#-architecture)
- [🛠️ Tech Stack](#️-tech-stack)
- [🚀 Getting Started](#-getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation & Setup](#-installation--setup)
  - [Running the Application](#-running-the-application)
- [🪪 License](#-license)
- [🌐 Repository](#-repository)

---

##  Overview
**Lily AI** is a complete, production-ready application designed to modernize the restaurant experience.  
It combines a powerful, multilingual AI assistant with a full-featured e-commerce platform, enabling customers to get intelligent answers, browse menus, and place orders with real payments.  
Simultaneously, restaurant owners manage everything through an intuitive dashboard with full control over orders, menu, and AI synchronization.

---

##  Key Features

###  Customer-Facing Application (React)
- **Intelligent AI Chat:** Beautiful chat interface powered by Lily — a stateful AI with conversational memory.  
- **Multilingual Support:** Handles both **English** and **Hindi** conversations seamlessly.  
- **Dynamic Menu & Ordering:** Interactive menu with category filters and a fully functional shopping cart.  
- **Secure Authentication:** Firebase Authentication (Email/Password & Google).  
- **Order Tracking:** “My Orders” page for real-time tracking.  
- **Direct Owner Messaging:** Secure channel for customers to contact the owner directly.

###  Owner's Dashboard (Streamlit)
- **Secure Admin Login:** Dedicated hardcoded login system for the owner.  
- **Full CRUD Control:** Manage menu items, categories, promotions, and FAQs.  
- **Live Order Fulfillment:** Update order status dynamically (Confirmed → Preparing → Shipped).  
- **AI Synchronization:** One-click button to sync database updates with Pinecone for the AI.  
- **Escalated Chats Inbox:** View and respond to customer messages forwarded from Lily.

### AI Backend (FastAPI)
- **Expert AI Agent:** Built using **LangGraph**, following a multi-step reasoning process (Router → Worker → Responder).  
- **Hybrid RAG Pipeline:**  
  - **Pinecone:** For fast semantic retrieval (menu descriptions, FAQs).  
  - **MongoDB Atlas Search:** For typo-tolerant factual lookups (prices, availability).  
- **Payment Integration:** End-to-end **PhonePe Gateway** integration (Sandbox + Production modes).

---

##  Architecture

A modern, decoupled, multi-component architecture enabling independent development and scaling:

| Component | Description | Deployment |
|------------|--------------|-------------|
| **FastAPI Backend** | Central AI brain handling REST API, reasoning, and payments | Render |
| **React Customer UI** | E-commerce and AI chat interface | Vercel |
| **Streamlit Owner Dashboard** | Admin panel for managing the restaurant | Streamlit Cloud |
| **MongoDB Atlas** | Primary database for structured data | Cloud |
| **Pinecone** | Vector database for semantic search | Cloud |

---

##  Tech Stack

| Category | Technologies |
|-----------|---------------|
| **Backend** | Python, FastAPI, Uvicorn, LangChain, LangGraph, Pydantic |
| **AI & ML** | Google Gemini (1.5 Flash & Embedding-001), Pinecone, Sentence-Transformers |
| **Customer UI** | React.js, JavaScript, HTML5, CSS3, React Router DOM, Firebase, Framer Motion |
| **Owner UI** | Streamlit, Streamlit Authenticator |
| **Databases** | MongoDB (with Atlas Search), Pinecone |
| **Deployment** | Docker, Render, Vercel, Streamlit Cloud, Git, GitHub |

---

##  Getting Started

### Prerequisites
- Python 3.9+
- Node.js & npm
- Docker & Docker Compose
- Git client

---

### 🔧 Installation & Setup

#### 1. Clone the Repository
```bash
git clone https://github.com/satyamkurum/business-app.git
cd business-app
```

#### 2. Configure Environment Files (CRITICAL)
Create the following configuration files and fill in credentials:

- **Backend:** `backend/.env` → use `backend/.env.example` as a template.  
- **Owner UI:** `frontend_owner/auth_config.yaml` → hardcoded owner login.  
- **Customer UI:** `frontend_customer/my-app/.env.local` → use `.env.example` as reference.

---

#### 3. Install Dependencies

**Backend**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cd ..
```

**Owner's Dashboard**
```bash
cd frontend_owner
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cd ..
```

**Customer Application**
```bash
cd frontend_customer/my-app
npm install
cd ../..
```

---

##  Running the Application

### The Professional Way (Recommended)
Run all components with a single command:
```bash
docker-compose up --build
```

- Customer UI → [[http://localhost:3000](http://localhost:3000](https://business-app-omega.vercel.app/))  
- Owner Dashboard → [[http://localhost:8501](http://localhost:8501](https://business-satyamkurum.streamlit.app/))

---

###  The Manual Way (3 Terminals)

**Terminal 1 – Backend**
```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload
```

**Terminal 2 – Customer UI**
```bash
cd frontend_customer/my-app
npm start
```

**Terminal 3 – Owner Dashboard**
```bash
cd frontend_owner
source venv/bin/activate
streamlit run app.py
```

---

##  License
This project is licensed under the [MIT License](LICENSE).

---

##  Repository
🔗 [GitHub Repository – satyamkurum/business-app](https://github.com/satyamkurum/business-app)

