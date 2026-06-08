# 🚆 AI-Based Railway Reservation System

> **Flask · SQLite · REST API · Heuristic ML · Session Wallet · Tatkal Booking**

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python)
![Flask](https://img.shields.io/badge/Flask-2.x-lightgrey?logo=flask)
![SQLite](https://img.shields.io/badge/Database-SQLite-003B57?logo=sqlite)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow)

---

## 📌 Project Overview

A full-stack web application simulating an intelligent railway reservation system. Built with Flask and SQLite, it covers the complete booking lifecycle — train search, seat allocation, waiting-list management, Tatkal quota booking, cancellation with automatic seat restoration, and a session-backed wallet system.

A heuristic confirmation-probability engine predicts waiting-list confirmation chances based on route popularity and waiting position — with a clear upgrade path to a real ML model using historical cancellation data.

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🔍 Train Search | Fuzzy source/destination matching across 15 routes |
| 🎫 Seat Booking | Real-time seat allocation with automatic waiting-list fallback |
| ⏳ Waiting List | Position tracking with confirmation probability prediction |
| ⚡ Tatkal Booking | Separate quota with dynamic fare (1.5x base + handling charge) |
| ❌ Cancellation | Automatic seat restoration and waiting-list adjustment |
| 💰 Wallet System | Session-backed digital wallet with transaction history |
| 🤖 AI Prediction | Heuristic engine returning confirmation probability (%) via JSON endpoint |
| 🔀 Alternate Routes | Stub routes wired for BFS graph traversal upgrade |

---

## 🏗️ System Architecture

```
Browser (HTML/CSS/Jinja2 Templates)
              │
              ▼
     Flask Application (app.py)
              │
    ┌─────────┼──────────┐
    ▼         ▼          ▼
 Routes    Session    Heuristic
 (REST)    Wallet     ML Engine
    │
    ▼
SQLite Database (railway.db)
    ├── trains
    ├── bookings
    └── wallet_transactions
```

---

## 🗄️ Database Schema

### `trains`
| Column | Type | Description |
|--------|------|-------------|
| train_no | TEXT (PK) | Unique train number |
| train_name | TEXT | Train name |
| source | TEXT | Departure station |
| destination | TEXT | Arrival station |
| available_seats | INTEGER | Current available seats |
| waiting_list_count | INTEGER | Current waiting list size |
| base_fare | INTEGER | Base ticket price (₹) |
| tatkal_quota | INTEGER | Tatkal seats available |
| popularity_score | REAL | Route demand score (0–1) |

### `bookings`
| Column | Type | Description |
|--------|------|-------------|
| booking_id | INTEGER (PK) | Auto-increment booking ID |
| train_no | TEXT (FK) | References trains |
| passenger_name | TEXT | Passenger name |
| passenger_age | INTEGER | Passenger age |
| booking_date | TEXT | ISO timestamp |
| status | TEXT | confirmed / waiting / cancelled |
| waiting_number | INTEGER | Waiting list position |
| wallet_txn_id | TEXT | Linked wallet transaction |

### `wallet_transactions`
| Column | Type | Description |
|--------|------|-------------|
| txn_id | INTEGER (PK) | Transaction ID |
| session_id | TEXT | User session |
| amount | INTEGER | Amount (+ credit / - debit) |
| txn_type | TEXT | recharge / booking / tatkal_booking |
| timestamp | TEXT | ISO timestamp |

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Home page |
| POST | `/search` | Search trains by source/destination |
| GET | `/train/<train_no>` | Train details |
| GET/POST | `/book/<train_no>` | Booking form + process booking |
| POST | `/predict` | Returns confirmation probability (JSON) |
| GET | `/cancel/<booking_id>` | Cancel booking + restore seat |
| GET | `/my-bookings` | View recent bookings |
| GET | `/wallet` | Wallet balance + transaction history |
| POST | `/add-money` | Add funds to wallet |
| GET | `/tatkal/<train_no>` | Tatkal booking |
| GET | `/alternate-routes` | Alternate route suggestions |

### `/predict` — Sample Response
```json
{
  "probability": 67,
  "advice": "High chance! Go for it!",
  "model_used": "Heuristic v1.0"
}
```

---

## 📁 Repository Structure

```
Hackathon-idea-AI-Based-Reservation-System/
│
├── app.py                        # Main Flask application
├── requirements.txt
├── README.md
├── design.md                     # System architecture & design document
│
├── templates/                    # Jinja2 HTML templates
│   ├── base.html
│   ├── index.html
│   ├── search_results.html
│   ├── train_details.html
│   ├── booking_form.html
│   ├── booking_success.html
│   ├── cancel_success.html
│   ├── tatkal_success.html
│   ├── my_bookings.html
│   ├── alternate_routes.html
│   ├── wallet.html
│   ├── wallet_success.html
│   └── error.html
│
└── railway.db                    # Auto-generated SQLite database
```

---

## 🚀 How to Run

### Prerequisites
- Python 3.10+
- pip

### Setup

```bash
git clone https://github.com/Dushdeva/Hackathon-idea-AI-Based-Reservation-System.git
cd Hackathon-idea-AI-Based-Reservation-System
pip install -r requirements.txt
python app.py
```

Open browser at **http://127.0.0.1:5000**

> The SQLite database (`railway.db`) is auto-created on first run with 15 pre-loaded train routes. Default wallet balance: ₹2,500.

---

## 🤖 Confirmation Probability Engine

The `/predict` endpoint returns a waiting-list confirmation probability calculated from:

- **Base score** — decreases with waiting list position
- **Popularity penalty** — high-demand routes have more competition
- **Seat factor** — remaining seats signal upcoming availability

```python
probability = base - popularity_penalty + seat_factor + chaos_factor
# Clamped between 5% and 98%
```

**Identified ML upgrade path:** Train a LightGBM model on historical cancellation data using features — train type, booking lead time, ticket class, waiting list category — to replace the heuristic engine with a data-driven prediction.

---

## 🔮 Identified Improvements

- [ ] **Graph traversal (BFS)** — implement real alternate route finding via C++ or NetworkX; stub routes already wired at `/alternate-routes`
- [ ] **LightGBM model** — replace heuristic probability engine with trained model on historical cancellation data
- [ ] **User authentication** — add Flask-Login or JWT; currently session-based with no login
- [ ] **PostgreSQL migration** — replace SQLite for production concurrency support
- [ ] **Deploy to Render/Railway.app** — make live with a public URL
- [ ] **Concurrency fix** — add row-level locking for seat allocation under simultaneous bookings

---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|-----------|
| Backend framework | Flask (Python) |
| Database | SQLite via `sqlite3` |
| Frontend | Jinja2 templates, HTML/CSS |
| Session management | Flask sessions |
| Wallet | Session-backed + SQLite transaction log |
| Prediction engine | Custom heuristic (LightGBM upgrade planned) |

---

*Built by [Devang Yadav](https://github.com/Dushdeva) — B.Tech CSE (AI), SKIT Jaipur*
