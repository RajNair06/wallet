# Wallet Payment Backend

A backend service for a wallet payment system built with FastAPI. This project is a work in progress and provides user authentication, wallet management, deposits, withdrawals, and transfers using JWT-based security and SQLite persistence.

## Key Features

- User registration and login with secure password hashing
- JWT access token authentication
- Per-user wallet creation and retrieval
- Deposit, withdrawal, and transfer transaction handlers
- Transaction history endpoint scaffolded for future implementation
- SQLModel + SQLAlchemy async database layer

## Tech Stack

- Python 3.11+
- FastAPI
- Uvicorn
- SQLModel
- SQLAlchemy (async)
- SQLite (`aiosqlite`)
- python-dotenv
- passlib (bcrypt)
- python-jose

## Project Structure

- `main.py` — FastAPI application entry point
- `config.py` — environment variable loader and configuration
- `db/session.py` — async database initialization and session provider
- `db/models.py` — SQLModel table definitions for users, wallets, and transactions
- `routers/` — API route definitions for auth, users, wallets, and transactions
- `schemas/` — request and response models for validation
- `dependencies/auth.py` — bearer token authentication dependency
- `core/security.py` — password hashing and JWT creation utilities


## API Reference

### Authentication

- `POST /signup`
  - Register a new user
  - Request body: `first_name`, `last_name`, `email`, `password`
  - Response: created user details

- `POST /token`
  - Authenticate user and receive JWT access token
  - Request form fields: `username` (email), `password`
  - Response: `access_token`, `token_type`

### Users

- `GET /users/me`
  - Get the current authenticated user
  - Requires `Authorization: Bearer <token>`

- `GET /users/{user_id}`
  - Retrieve a user by ID

### Wallets

- `POST /wallet`
  - Create a wallet for the authenticated user
  - Request body: `balance`, `currency`
  - One wallet per user is enforced

- `GET /wallet`
  - Retrieve the authenticated user's wallet

- `DELETE /wallet`
  - Delete the authenticated user's wallet

### Transactions

- `PATCH /transaction/deposit`
  - Add funds to the authenticated user's wallet
  - Request body: `amount`, `currency`

- `PATCH /transaction/withdraw`
  - Withdraw funds from the authenticated user's wallet
  - Request body: `amount`, `currency`

- `PATCH /transaction/transfer`
  - Transfer funds from the authenticated user to another wallet
  - Request body: `to_account_id`, `amount`, `currency`

- `GET /transaction/history`
  - Endpoint exists but is not implemented yet

## Validation and Rules

- Wallet balance must be non-negative
- Currency codes must be exactly 3 characters
- Passwords must be at least 8 characters
- Withdrawals and transfers require sufficient balance
- Currency must match the wallet currency for deposit, withdrawal, and transfer operations
- Transfers cannot be made to the same wallet

## Notes

- Database tables are created automatically on startup via the `lifespan` event in `main.py`
- The current persistence layer uses `sqlite+aiosqlite:///database.db`
- `transaction/history` is planned but not implemented yet



## License

This repository is currently a work in progress and does not include a license file.
