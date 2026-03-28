# Shopping AI Web Application

## Overview

This project is a full-stack shopping web application that combines a traditional e-commerce flow with an AI-powered assistant.

The system allows users to browse products, manage a shopping cart, place orders, save favorites, and interact with an AI assistant for product recommendations and queries.

The application is built using a modern microservice-style architecture with FastAPI, Streamlit, MySQL, Redis, and OpenAI integration.

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

## Future Improvements (Bonus)

* Machine learning model for user behavior prediction
* Personalized recommendations
* Spend prediction per user
* Advanced analytics

---

## Author

This project was developed as part of an AI + Python development course, focusing on practical system design, backend architecture, and AI integration.
