# AI Blockchain Voting System

A secure, AI-powered, blockchain-based digital voting platform.

This system combines:

- Biometric Facial Recognition
- Artificial Intelligence
- Blockchain Integration
- Role-based Election Management
- Admin Control Panel

Built using FastAPI, PostgreSQL, SQLAlchemy, and modern frontend design.

---

# PROJECT OVERVIEW

This platform allows secure digital elections where:

- Voters authenticate using facial recognition
- Votes are securely recorded
- Candidates submit manifestos
- Admin manages users and elections
- Blockchain wallet addresses are generated

The system ensures:

- Transparency
- Security
- Immutability
- Role-based access control

---

# SYSTEM ARCHITECTURE

Frontend:
- HTML (Jinja2 Templates)
- CSS (Modern UI)
- JavaScript (Modals & UI logic)

Backend:
- FastAPI
- SQLAlchemy ORM
- JWT Authentication
- AI Face Embedding Service

Database:
- PostgreSQL

Blockchain:
- Wallet generation service

---

# USER ROLES

# 1️⃣ Voter
- Register with facial image
- Authenticate
- Vote in elections
- View vote history

# 2️⃣ Candidate
- Become candidate for an election
- Submit manifesto
- Participate in elections

# 3️⃣ Admin
- Create users
- Assign roles
- Verify users
- Create elections
- Add candidates to elections
- Edit / Delete users
- Edit / Delete elections

---

# FEATURES

# Authentication
- JWT token-based authentication
- Secure password hashing (Argon2)

# AI Integration
- Facial recognition embedding
- Biometric authentication

# Election System
- Create elections
- Add candidates
- Vote percentage calculation
- Election activation

# Admin Dashboard
- Full CRUD for users
- Full CRUD for elections
- Verification system

# Security
- Role-based route protection
- Cookie-based JWT
- Database integrity

---

# TECHNOLOGIES USED

# Backend
- Python 3.11
- FastAPI
- SQLAlchemy
- PostgreSQL
- Uvicorn

# AI
- Face embedding service
- NumPy
- OpenCV (if used)
- Face recognition model

# Security
- JWT
- Argon2 Password Hashing

# Frontend
- Jinja2
- Modern CSS
- Feather Icons

---

# Démarrer PostgreSQL
> brew services start postgresql

# Vérifier qu’il tourne
> brew services list

# Connexion au serveur PostgreSQL
> psql postgres -U ai_user -d ai_voting

# Activer l'environnement virtuel
> source .venv/bin/activate

# Lancer le serveur
> python -m uvicorn app.main:app --reload

# Application disponible sur :
http://127.0.0.1:8000

---


# PYTHON PACKAGES

Install dependencies:

```bash
pip install fastapi
pip install uvicorn
pip install sqlalchemy
pip install psycopg2-binary
pip install python-multipart
pip install passlib[argon2]
pip install python-jose
pip install numpy
pip install opencv-python

