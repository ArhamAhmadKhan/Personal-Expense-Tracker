#
import os
import mysql.connector
from mysql.connector import Error

def get_db_connection():
    try:
        connection = mysql.connector.connect(
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME"),
            port=int(os.getenv("DB_PORT", "24794")),
            ssl_disabled=False,
            connection_timeout=10
        )

        return connection

    except Error as e:
        print("Database connection failed:", e)
        return None
