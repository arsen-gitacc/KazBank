import os
import psycopg
from dotenv import load_dotenv

load_dotenv()
conn_str = os.getenv("DATABASE_URL")

with psycopg.connect(conn_str) as conn:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            customer_id SERIAL PRIMARY KEY,
            full_name TEXT NOT NULL,
            city TEXT DEFAULT 'Almaty'
        );
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS accounts (
            account_id SERIAL PRIMARY KEY,
            customer_id INTEGER REFERENCES customers(customer_id),
            account_number TEXT UNIQUE NOT NULL,
            balance NUMERIC(15,2) DEFAULT 0
        );
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            transaction_id SERIAL PRIMARY KEY,
            account_id INTEGER REFERENCES accounts(account_id),
            amount NUMERIC(15,2) NOT NULL,
            tx_type TEXT NOT NULL
        );
    """)

    conn.commit()
    print("All 3 tables created successfully!")