# Shopping AI Web Application

## Overview

This project is a full-stack shopping web application that combines a traditional e-commerce flow with an AI-powered assistant.

The system allows users to browse products, manage a shopping cart, place orders, save favorites, and interact with an AI assistant for product recommendations and queries.

The application is built using a modern microservice-style architecture with FastAPI, Streamlit, MySQL, Redis, and OpenAI integration.

The project is fully self-contained – no external data sources are required.

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

On application startup, the backend checks if the items table is empty.
If empty, product data is loaded from:
backend/app/data/products_seed.json

This guarantees a fully reproducible environment.

---

## Bonus ML Feature (Explainable Spend Prediction)

A supervised ML model predicts user spending for the next 30 days.

# What makes it useful
This is not just a raw prediction model — it includes business interpretation:

Predicted spend (USD)
User segmentation:
High value
Medium value
Low value
At-risk users
Confidence level (based on user activity)
Explainability:
Key reasons behind the prediction
Recommended actions:
Upsell / cross-sell / retention suggestions

# API Endpoints
POST /ml/predict-spend – predict for a single user (owner only)
GET /ml/predict-spend/users – bulk prediction for multiple users

# ML Artifacts
Dataset: backend/app/ml/data/user_spend_training.csv
Training script:
python backend/app/ml/train.py
Model files:
model.joblib
metadata.json

# ML Frontend
Streamlit dashboard:
frontend/pages/5_Spend_Prediction.py

# Usage Flow
Train the model:
python backend/app/ml/train.py
Run the system:
docker compose up --build
Login as an owner (e.g., admin)
Open Spend Prediction page

---

## Tech Stack

# Backend
FastAPI
SQLAlchemy
MySQL
Redis
OpenAI API
Scikit-learn
# Frontend
Streamlit
# Infrastructure
Docker Compose

---

## Project Structure
backend/
  app/
    api/
    services/
    repositories/
    models/
    ml/
    data/

frontend/
  components/
  pages/
  features/

docker-compose.yml

---

## Running the Project

# Prerequisites
Docker
Docker Compose
# Run locally
docker compose up --build
# Services
Frontend: http://localhost:8501
Backend API: http://localhost:8000
Swagger: http://localhost:8000/docs

---

## Key Design Decisions

# Cart Model (TEMP Order)
Simplifies cart logic
Seamless transition to checkout

# Stock Handling
Stock reduced only at checkout
Prevents stock locking issues

# Search Architecture
Unified logic across all pages
Hebrew → English normalization
Avoids false matches

# AI Integration
Hybrid approach:
  Rule-based + GPT fallback
Retrieval-based context (no hallucinations)
Structured responses

# ML Design
Feature-based user behavior modeling
Snapshot-based training data
Explainable predictions (not black-box only)

---

## Testing
Manual test scenarios include:

Authentication flow
Cart lifecycle
Checkout validation
Favorites persistence
Chat assistant behavior
ML prediction endpoints
User deletion cascade

---

## Author
This project was developed as part of an AI + Python development course, focusing on practical system design, backend architecture, and AI integration.