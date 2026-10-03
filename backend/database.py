import mysql.connector
from mysql.connector import Error


# ============================================================
# MYSQL DATABASE CONFIGURATION
# ============================================================

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "Prajakta@2005",
    "database": "sae_prediction_system"
}


# ============================================================
# DATABASE CONNECTION FUNCTION
# ============================================================

def get_db_connection():

    try:

        connection = mysql.connector.connect(
            host=DB_CONFIG["host"],
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"],
            database=DB_CONFIG["database"]
        )

        if connection.is_connected():

            print("✅ MySQL connected successfully")

            return connection

    except Error as error:

        print("❌ MySQL connection error:", error)

    return None


# ============================================================
# TEST DATABASE CONNECTION
# ============================================================

if __name__ == "__main__":

    connection = get_db_connection()

    if connection:

        print("✅ Database connection test successful")

        cursor = connection.cursor()

        cursor.execute("SELECT DATABASE()")

        database_name = cursor.fetchone()[0]

        print("Database:", database_name)

        cursor.execute(
            "SELECT COUNT(*) FROM icu_patients"
        )

        total_records = cursor.fetchone()[0]

        print("Total ICU patient records:", total_records)

        cursor.close()
        connection.close()

        print("✅ Connection closed")

    else:

        print("❌ Could not connect to MySQL")