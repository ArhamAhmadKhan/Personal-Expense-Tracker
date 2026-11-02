
from flask import Flask, render_template, request, redirect, url_for
from database import get_db_connection

app = Flask(__name__)


# ==========================================
# 1. DASHBOARD
# ==========================================

@app.route("/")
def home():

    connection = get_db_connection()

    if connection is None:
        return "Database connection failed!"

    try:
        cursor = connection.cursor(dictionary=True)

        # Calculate total income and expenses
        cursor.execute("""
            SELECT
                COALESCE(SUM(
                    CASE WHEN c.type = 'income'
                    THEN t.amount ELSE 0 END
                ), 0) AS total_income,

                COALESCE(SUM(
                    CASE WHEN c.type = 'expense'
                    THEN t.amount ELSE 0 END
                ), 0) AS total_expenses

            FROM transactions t
            JOIN categories c
                ON t.category_id = c.category_id
            WHERE t.user_id = 1
        """)

        summary = cursor.fetchone()

        # Get all categories
        cursor.execute("""
            SELECT category_name, category_id, type
            FROM categories
            ORDER BY category_name
        """)

        categories = cursor.fetchall()

        # Get expenses grouped by category
        cursor.execute("""
            SELECT
                c.category_name,
                SUM(t.amount) AS total

            FROM transactions t
            JOIN categories c
                ON t.category_id = c.category_id

            WHERE c.type = 'expense'
              AND t.user_id = 1

            GROUP BY c.category_name
        """)

        category_data = cursor.fetchall()

        # Get recent transactions
        # IMPORTANT: transaction_id is included for Edit/Delete buttons
        cursor.execute("""
            SELECT
                t.transaction_id,
                c.category_name,
                c.type,
                t.amount,
                t.transaction_date,
                t.description

            FROM transactions t
            JOIN categories c
                ON t.category_id = c.category_id

            WHERE t.user_id = 1

            ORDER BY t.transaction_date DESC,
                     t.transaction_id DESC

            LIMIT 10
        """)

        transactions = cursor.fetchall()

        # Calculate available balance
        balance = (
            summary["total_income"]
            - summary["total_expenses"]
        )

        return render_template(
            "index.html",
            summary=summary,
            balance=balance,
            categories=categories,
            category_data=category_data,
            transactions=transactions
        )

    except Exception as e:
        return f"Dashboard error: {e}"

    finally:
        connection.close()


# ==========================================
# 2. ADD TRANSACTION
# ==========================================

@app.route("/add-transaction", methods=["POST"])
def add_transaction():

    transaction_type = request.form.get("type")
    category_id = request.form.get("category_id")
    amount = request.form.get("amount")
    transaction_date = request.form.get("transaction_date")
    description = request.form.get("description", "")

    # Validate transaction type
    if transaction_type not in ("income", "expense"):
        return "Invalid transaction type!", 400

    # Validate amount and category
    try:
        amount = float(amount)
        category_id = int(category_id)

        if amount <= 0:
            return "Amount must be greater than zero!", 400

    except (ValueError, TypeError):
        return "Please enter a valid amount and category!", 400

    connection = get_db_connection()

    if connection is None:
        return "Database connection failed!"

    try:
        cursor = connection.cursor()

        # Check whether category matches transaction type
        cursor.execute("""
            SELECT category_id
            FROM categories
            WHERE category_id = %s
              AND type = %s
        """, (category_id, transaction_type))

        if cursor.fetchone() is None:
            return "Invalid category selected!", 400

        # Insert transaction
        cursor.execute("""
            INSERT INTO transactions
            (
                user_id,
                category_id,
                amount,
                transaction_date,
                description
            )
            VALUES (%s, %s, %s, %s, %s)
        """, (
            1,
            category_id,
            amount,
            transaction_date,
            description
        ))

        connection.commit()

        return redirect(url_for("home"))

    except Exception as e:
        connection.rollback()
        return f"Could not save transaction: {e}"

    finally:
        connection.close()


# ==========================================
# 3. EDIT TRANSACTION
# ==========================================

@app.route("/edit/<int:transaction_id>", methods=["GET", "POST"])
def edit_transaction(transaction_id):

    connection = get_db_connection()

    if connection is None:
        return "Database connection failed!"

    try:
        cursor = connection.cursor(dictionary=True)

        if request.method == "POST":

            category_id = int(request.form["category_id"])
            amount = float(request.form["amount"])
            transaction_date = request.form["transaction_date"]
            description = request.form.get("description", "")

            if amount <= 0:
                return "Amount must be greater than zero!", 400

            # Check that the transaction exists
            cursor.execute("""
                SELECT transaction_id
                FROM transactions
                WHERE transaction_id = %s
                  AND user_id = 1
            """, (transaction_id,))

            if cursor.fetchone() is None:
                return "transactions not found!", 404

            # Update transaction
            cursor.execute("""
                UPDATE transactions
                SET
                    category_id = %s,
                    amount = %s,
                    transaction_date = %s,
                    description = %s
                WHERE transaction_id = %s
                  AND user_id = 1
            """, (
                category_id,
                amount,
                transaction_date,
                description,
                transaction_id
            ))

            connection.commit()

            return redirect(url_for("home"))

        # Get transaction details
        cursor.execute("""
            SELECT *
            FROM transactions
            WHERE transaction_id = %s
              AND user_id = 1
        """, (transaction_id,))

        transaction = cursor.fetchone()

        if transaction is None:
            return "transactions not found!", 404

        # Get categories for edit page
        cursor.execute("""
            SELECT category_id, category_name, type
            FROM categories
            ORDER BY category_name
        """)

        categories = cursor.fetchall()

        return render_template(
            "edit.html",
            transaction=transaction,
            categories=categories
        )

    except Exception as e:
        connection.rollback()
        return f"Edit error: {e}"

    finally:
        connection.close()


# ==========================================
# 4. DELETE TRANSACTION
# ==========================================

@app.route("/delete/<int:transaction_id>", methods=["POST"])
def delete_transaction(transaction_id):

    connection = get_db_connection()

    if connection is None:
        return "Database connection failed!"

    try:
        cursor = connection.cursor()

        cursor.execute("""
            DELETE FROM transactions
            WHERE transaction_id = %s
              AND user_id = 1
        """, (transaction_id,))

        if cursor.rowcount == 0:
            connection.rollback()
            return "transactions not found!", 404

        connection.commit()

        return redirect(url_for("home"))

    except Exception as e:
        connection.rollback()
        return f"Delete error: {e}"

    finally:
        connection.close()


# ==========================================
# 5. RUN FLASK APPLICATION
# ==========================================

if __name__ == "__main__":
    app.run(debug=True)
