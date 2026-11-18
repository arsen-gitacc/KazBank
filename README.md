
# KazBank Transaction API

## Project Information

Course: CSCI2204 Database Management Systems  
University: KBTU  
Student ID: 25B031209

## Description

This project is a simple banking REST API built with Python, Flask, and PostgreSQL.

Users can view customers, create customers, check bank accounts, make money transfers, and view transactions.

## Technologies

- Python 3.15
- PostgreSQL 18
- Flask
- psycopg3
- psycopg-pool
- python-dotenv

## Installation

1. Create a PostgreSQL database named `kazbank`.

2. Create a virtual environment:

   python -m venv venv

3. Activate the environment on Windows:

   venv\Scripts\activate

4. Install dependencies:

   pip install -r requirements.txt

5. Copy `.env.example` to `.env` and set your PostgreSQL password.

6. Create database tables:

   python create_tables.py

7. Insert sample data into a new, empty database:

   python seed_data.py

8. Start the Flask server:

   python app.py

## API Endpoints

GET /customers

GET /customers?city=Almaty

POST /customers

GET /accounts?customer_id=1

POST /transactions

GET /transactions?account_id=1

POST /transfer

GET /health

## Sample API Requests

Get all customers:

curl http://127.0.0.1:5000/customers

Get accounts:

curl "http://127.0.0.1:5000/accounts?customer_id=1"

Get transactions:

curl "http://127.0.0.1:5000/transactions?account_id=1"

Check connection pool:

curl http://127.0.0.1:5000/health

Create a customer:

curl -X POST http://127.0.0.1:5000/customers -H "Content-Type: application/json" -d '{"full_name":"New Student","city":"Almaty","email":"newstudent@example.com"}'

Transfer money:

curl -X POST http://127.0.0.1:5000/transfer -H "Content-Type: application/json" -d '{"from_account":1,"to_account":2,"amount":5000}'

## Database Tables

- customers
- accounts
- transactions

## Database Features

- Primary Key and Foreign Key
- UNIQUE constraints
- Transactions with COMMIT and ROLLBACK
- SAVEPOINT
- SERIALIZABLE isolation
- Deadlock prevention with sorted lock order
- Connection pooling
- Error handling
- SQL injection protection

## HTTP Status Codes

200 - OK  
201 - Created  
400 - Bad Request  
404 - Not Found  
409 - Conflict  
503 - Service Unavailable

## Connection Pool

Minimum connections: 2  
Maximum connections: 8

The `/health` endpoint displays connection pool statistics.

## Security

Database credentials are stored in the `.env` file.

SQL queries use parameterized statements to help prevent SQL injection.

## Testing

The project was tested with Flask, PowerShell, and pgAdmin.

A load test with 20 concurrent requests completed successfully.
