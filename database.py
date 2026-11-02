
import mysql.connector
from mysql.connector import Error


def get_db_connection():
    try:
        connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password="123456",
            database="expense_tracker",
            port=3306
        )

        return connection

    except Error as e:
        print("Database connection failed:", e)
        return None
