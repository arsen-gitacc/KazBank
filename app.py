
import os
import time
import psycopg
from psycopg import errors as pg_errors
from psycopg_pool import ConnectionPool, PoolTimeout
from decimal import Decimal, InvalidOperation
from flask import Flask, jsonify, request
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

pool = ConnectionPool(
    conninfo=os.environ["DATABASE_URL"],
    min_size=2,
    max_size=8,
    timeout=5.0,
    open=True
)


def get_conn():
    return pool.connection()


@app.route("/customers", methods=["GET"])
def list_customers():
    city = request.args.get("city")

    if city:
        sql = "SELECT customer_id, full_name, city FROM customers WHERE city = %s ORDER BY customer_id"
        params = (city,)
    else:
        sql = "SELECT customer_id, full_name, city FROM customers ORDER BY customer_id"
        params = ()

    try:
        with get_conn() as conn:
            rows = conn.execute(sql, params).fetchall()

        return jsonify([
            {"id": r[0], "name": r[1], "city": r[2]}
            for r in rows
        ]), 200

    except (psycopg.OperationalError, PoolTimeout):
        return jsonify({"error": "Database unavailable"}), 503


@app.route("/customers", methods=["POST"])
def create_customer():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"error": "Invalid JSON"}), 400

    full_name = data.get("full_name")
    email = data.get("email")
    city = data.get("city", "Almaty")

    if not isinstance(full_name, str) or not full_name.strip():
        return jsonify({"error": "Missing required field: full_name"}), 400

    if not isinstance(email, str) or not email.strip():
        return jsonify({"error": "Missing required field: email"}), 400

    if not isinstance(city, str) or not city.strip():
        return jsonify({"error": "Invalid city"}), 400

    try:
        with get_conn() as conn:
            row = conn.execute(
                "INSERT INTO customers (full_name, city, email) VALUES (%s, %s, %s) RETURNING customer_id",
                (full_name.strip(), city.strip(), email.strip())
            ).fetchone()

            conn.commit()

        return jsonify({"customer_id": row[0]}), 201

    except pg_errors.UniqueViolation:
        return jsonify({"error": "Email already registered"}), 409

    except pg_errors.NotNullViolation:
        return jsonify({"error": "Missing required database field"}), 400

    except (psycopg.OperationalError, PoolTimeout):
        return jsonify({"error": "Database unavailable"}), 503


@app.route("/accounts", methods=["GET"])
def list_accounts():
    customer_id = request.args.get("customer_id")

    if customer_id is None or not customer_id.isdigit():
        return jsonify({"error": "Invalid customer_id"}), 400

    try:
        with get_conn() as conn:
            rows = conn.execute(
                "SELECT account_id, customer_id, account_number, balance FROM accounts WHERE customer_id = %s ORDER BY account_id",
                (int(customer_id),)
            ).fetchall()

        return jsonify([
            {
                "account_id": r[0],
                "customer_id": r[1],
                "account_number": r[2],
                "balance": float(r[3])
            }
            for r in rows
        ]), 200

    except (psycopg.OperationalError, PoolTimeout):
        return jsonify({"error": "Database unavailable"}), 503


@app.route("/transactions", methods=["GET"])
def list_transactions():
    account_id = request.args.get("account_id")

    if account_id is None or not account_id.isdigit():
        return jsonify({"error": "Invalid account_id"}), 400

    try:
        with get_conn() as conn:
            rows = conn.execute(
                "SELECT transaction_id, account_id, amount, tx_type FROM transactions WHERE account_id = %s ORDER BY transaction_id",
                (int(account_id),)
            ).fetchall()

        return jsonify([
            {
                "transaction_id": r[0],
                "account_id": r[1],
                "amount": float(r[2]),
                "tx_type": r[3]
            }
            for r in rows
        ]), 200

    except (psycopg.OperationalError, PoolTimeout):
        return jsonify({"error": "Database unavailable"}), 503


@app.route("/transactions", methods=["POST"])
def create_transaction():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"error": "Invalid JSON"}), 400

    try:
        account_id = int(data["account_id"])
        amount = Decimal(str(data["amount"]))
        tx_type = data["tx_type"]
    except (KeyError, ValueError, TypeError, InvalidOperation):
        return jsonify({"error": "Invalid transaction data"}), 400

    if account_id <= 0 or not amount.is_finite() or amount <= 0:
        return jsonify({"error": "Invalid account or amount"}), 400

    if amount.as_tuple().exponent < -2:
        return jsonify({"error": "Amount supports at most 2 decimal places"}), 400

    if tx_type not in ("credit", "debit"):
        return jsonify({"error": "Invalid transaction type"}), 400

    try:
        with get_conn() as conn:
            row = conn.execute(
                "SELECT balance FROM accounts WHERE account_id = %s FOR UPDATE",
                (account_id,)
            ).fetchone()

            if row is None:
                return jsonify({"error": "Account not found"}), 404

            new_balance = row[0] + amount if tx_type == "credit" else row[0] - amount

            if new_balance < 0:
                return jsonify({"error": "Insufficient balance"}), 400

            conn.execute(
                "UPDATE accounts SET balance = %s WHERE account_id = %s",
                (new_balance, account_id)
            )

            conn.execute(
                "INSERT INTO transactions (account_id, amount, tx_type) VALUES (%s, %s, %s)",
                (account_id, amount, tx_type)
            )

            conn.commit()

        return jsonify({
            "message": "Transaction successful",
            "account_id": account_id,
            "new_balance": float(new_balance)
        }), 201

    except (psycopg.OperationalError, PoolTimeout):
        return jsonify({"error": "Database unavailable"}), 503

    except psycopg.Error:
        return jsonify({"error": "Database transaction failed"}), 500


@app.route("/transfer", methods=["POST"])
def transfer():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"error": "Invalid JSON"}), 400

    try:
        from_acc = int(data["from_account"])
        to_acc = int(data["to_account"])
        amount = Decimal(str(data["amount"]))
    except (KeyError, ValueError, TypeError, InvalidOperation):
        return jsonify({"error": "Invalid transfer data"}), 400

    if (
        from_acc <= 0
        or to_acc <= 0
        or from_acc == to_acc
        or not amount.is_finite()
        or amount <= 0
    ):
        return jsonify({"error": "Invalid transfer"}), 400

    if amount.as_tuple().exponent < -2:
        return jsonify({"error": "Amount supports at most 2 decimal places"}), 400

    for attempt in range(3):
        try:
            with get_conn() as conn:
                conn.execute("SET TRANSACTION ISOLATION LEVEL SERIALIZABLE")

                first, second = sorted([from_acc, to_acc])
                balances = {}

                for account_id in (first, second):
                    row = conn.execute(
                        "SELECT balance FROM accounts WHERE account_id = %s FOR UPDATE",
                        (account_id,)
                    ).fetchone()

                    if row is None:
                        return jsonify({"error": "Account not found"}), 404

                    balances[account_id] = row[0]

                if balances[from_acc] < amount:
                    return jsonify({"error": "Insufficient balance"}), 400

                conn.execute("SAVEPOINT transfer_sp")

                try:
                    conn.execute(
                        "UPDATE accounts SET balance = balance - %s WHERE account_id = %s",
                        (amount, from_acc)
                    )

                    conn.execute(
                        "UPDATE accounts SET balance = balance + %s WHERE account_id = %s",
                        (amount, to_acc)
                    )

                except psycopg.Error:
                    conn.execute("ROLLBACK TO SAVEPOINT transfer_sp")
                    raise

                conn.commit()

            return jsonify({
                "message": "Transfer successful",
                "from_account": from_acc,
                "to_account": to_acc,
                "amount": float(amount)
            }), 200

        except pg_errors.SerializationFailure:
            if attempt == 2:
                return jsonify({"error": "Transaction conflict"}), 409

            time.sleep(0.05 * (attempt + 1))

        except (psycopg.OperationalError, PoolTimeout):
            return jsonify({"error": "Database unavailable"}), 503

        except psycopg.Error:
            return jsonify({"error": "Database transfer failed"}), 500

    return jsonify({"error": "Transfer failed"}), 500


@app.route("/health", methods=["GET"])
def health():
    try:
        pool.check()
        stats = pool.get_stats()

        return jsonify({
            "status": "ok",
            "pool_stats": stats
        }), 200

    except (psycopg.Error, PoolTimeout):
        return jsonify({"status": "error"}), 503


if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)
