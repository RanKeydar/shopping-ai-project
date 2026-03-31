# Shopping AI Web Application

## Overview

This project is a full-stack shopping web application that combines a traditional e-commerce flow with an AI-powered assistant.

The system allows users to browse products, manage a shopping cart, place orders, save favorites, and interact with an AI assistant for product recommendations and queries.

The application is built using a modern microservice-style architecture with FastAPI, Streamlit, MySQL, Redis, and OpenAI integration.

> ✅ The project is fully self-contained – no external data sources are required.

---

## Main Features

### Authentication

* User registration and login (JWT-based authentication)
* Persistent user sessions
* Protected pages for authenticated users
* Account deletion (with full data cascade)

---

### Product Catalog

* Browse products with category and description
* Search functionality (Hebrew + English support)
* Smart tokenization and matching
* Stock indication (including out-of-stock items)

---

### Orders & Cart System

* Each user has exactly one active cart (TEMP order)
* Add / update / remove items from cart
* Automatic cart creation when needed
* Cart is deleted automatically when empty
* Checkout process:

  * Validates stock
  * Reduces inventory only on checkout
  * Converts TEMP → CLOSED order
* Closed orders are read-only

---

### Favorites

* Add/remove items to favorites
* Favorites are stored per user
* Favorites reflect stock status

---

### Chat Assistant (AI)

* AI-powered assistant for shopping queries
* Supports Hebrew and English
* Smart product retrieval and recommendations
* Price-aware responses (cheap / premium)
* Session-based usage limit (5 prompts per session)
* Rate limiting handled via Redis

---

### Data Integrity

* Prevent ordering beyond available stock
* Cascade deletion:

  * Deleting a user removes:

    * Orders
    * Order items
    * Favorites

---

## Data Initialization

The application includes a preloaded product catalog (193 items) that is automatically initialized on startup.

### How it works

* On application startup, the backend checks if the `items` table is empty.
* If empty, product data is loaded from a local JSON file:

```
backend/app/data/products_seed.json
```

* This guarantees that every run starts with the same dataset.

### Why this approach?

* No dependency on external APIs (e.g., DummyJSON)
* Fully deterministic and reproducible environment
* Faster startup and reliable evaluation/demo

---

## Tech Stack

### Backend

* FastAPI
* SQLAlchemy
* MySQL
* Redis (caching + rate limiting)
* OpenAI API

### Frontend

* Streamlit

### Infrastructure

* Docker Compose
* Multi-service architecture

---

## Project Structure

```
backend/
  app/
    api/
    services/
    repositories/
    models/
    data/

frontend/
  components/
  pages/
  features/

docker-compose.yml
```

---

## Running the Project

### Prerequisites

* Docker
* Docker Compose

### Run locally

```bash
docker compose up --build
```

### Services

* Frontend: http://localhost:8501
* Backend API: http://localhost:8000
* Swagger: http://localhost:8000/docs

The database will be automatically initialized with product data if empty.

---

## Optional: Product Import (Development Only)

The system includes endpoints for importing products from an external API (DummyJSON):

* `POST /product-import/seed` – import a single page
* `POST /product-import/seed-all` – import all products

These endpoints are intended for development and are not required for normal usage.

---

## Key Design Decisions

### 1. Cart Model (TEMP Order)

Instead of a separate cart entity, the system uses an order with status `TEMP`.

Advantages:

* Simpler data model
* Natural transition to checkout
* Easier history tracking

---

### 2. Stock Handling

* Stock is NOT reduced when adding to cart
* Stock is reduced ONLY on checkout

This follows real-world e-commerce behavior and prevents stock locking.

---

### 3. Search Architecture

* Unified search logic across pages
* Tokenization and normalization
* Hebrew → English matching
* Avoids false matches (e.g., "hair" ≠ "chair")

---

### 4. AI Integration

* Hybrid approach:

  * Rule-based intents
  * GPT-based fallback
* Retrieval-based context (no hallucinations)
* Structured responses:

  * Recommendation
  * Alternatives

---

### 5. Rate Limiting

* Redis-based session tracking
* 5 prompts per session
* Consistent across refreshes

---

## Testing

Manual test scenarios include:

* Authentication flow
* Cart lifecycle (create / update / delete)
* Checkout behavior
* Stock validation
* Favorites persistence
* Chat assistant limits
* User deletion cascade

---

 ## Bonus ML Feature (Implemented)

diff --git a/README.md b/README.md
index 31cd784b4b3659df4b593736bc6a74a36d66bd04..251a6d169e64dc45fff012590e777b3ba90cf83d 100644
--- a/README.md
+++ b/README.md
@@ -224,37 +224,46 @@ This follows real-world e-commerce behavior and prevents stock locking.
 
 ---
 
 ### 5. Rate Limiting
 
 * Redis-based session tracking
 * 5 prompts per session
 * Consistent across refreshes
 
 ---
 
 ## Testing
 
 Manual test scenarios include:
 
 * Authentication flow
 * Cart lifecycle (create / update / delete)
 * Checkout behavior
 * Stock validation
 * Favorites persistence
 * Chat assistant limits
 * User deletion cascade
 
 ---
 
+## Bonus ML Feature (Implemented)
 

A supervised ML bonus feature is now included:

* Training dataset: `backend/app/ml/data/user_spend_training.csv`
* Training script: `python backend/app/ml/train.py`
* Artifacts: `backend/app/ml/model.joblib` + `backend/app/ml/metadata.json`
* Prediction API: `POST /ml/predict-spend` (authenticated)
* Streamlit page: `frontend/pages/5_Bonus_Prediction.py`

Use this flow:

1. Train model locally (`python backend/app/ml/train.py`).
2. Run the stack (`docker compose up --build`).
3. Login and open **Bonus Prediction** page.
 
 ---
 
 ## Author
 
 This project was developed as part of an AI + Python development course, focusing on practical system design, backend architecture, and AI integration.
