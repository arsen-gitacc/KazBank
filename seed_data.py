
import os
import psycopg
from dotenv import load_dotenv

load_dotenv()
conn_str = os.getenv("DATABASE_URL")

customers = [
    ("Aruzhan Saparova", "Almaty"),
    ("Dias Nurlanov", "Astana"),
    ("Aigerim Bekova", "Shymkent"),
    ("Alikhan Serikov", "Almaty"),
    ("Madina Askarova", "Aktobe"),
    ("Nursultan Omarov", "Taraz"),
    ("Amina Tulegenova", "Almaty"),
    ("Daniyar Karimov", "Astana"),
    ("Kamila Yesenova", "Atyrau"),
    ("Arman Zhaksylykov", "Kostanay")
]

accounts = [
    (1, "KZ001", 150000),
    (1, "KZ002", 75000),
    (2, "KZ003", 200000),
    (2, "KZ004", 95000),
    (3, "KZ005", 120000),
    (3, "KZ006", 50000),
    (4, "KZ007", 300000),
    (5, "KZ008", 45000),
    (5, "KZ009", 85000),
    (6, "KZ010", 110000),
    (7, "KZ011", 65000),
    (7, "KZ012", 175000),
    (8, "KZ013", 90000),
    (9, "KZ014", 140000),
    (10, "KZ015", 220000)
]

with psycopg.connect(conn_str) as conn:
    with conn.cursor() as cur:
        cur.executemany(
            "INSERT INTO customers (full_name, city) VALUES (%s, %s)",
            customers
        )

        cur.executemany(
            "INSERT INTO accounts (customer_id, account_number, balance) VALUES (%s, %s, %s)",
            accounts
        )

    conn.commit()
    print("10 customers and 15 accounts inserted successfully!")
