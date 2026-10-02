import mysql.connector
from mysql.connector import Error


def get_db_connection():

    try:

        connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password="Prajakta@2005",
            database="sae_prediction_system"
        )

        if connection.is_connected():

            print("MySQL database connected successfully!")

            return connection

    except Error as e:

        print("MySQL connection error:", e)

        return None