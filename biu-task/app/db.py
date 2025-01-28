import psycopg2
from psycopg2 import OperationalError

def create_connection():
    try:
        connection = psycopg2.connect(
            user="postgres.koepkwhgtyjeoqmzsmmy",
            password="Rafif123.",
            host="aws-0-ap-southeast-1.pooler.supabase.com",
            port="6543",
            database="postgres"
        )
        print("Connection to PostgreSQL DB successful")
         # Create a cursor to execute SQL queries
        cursor = connection.cursor()
        
        # Example query
        # Menjalankan query untuk memilih username dan password dari tabel user
        cursor.execute("SELECT username, password FROM \"user\";")
        result = cursor.fetchall()

        # Menampilkan hasil query
        for row in result:
            print("Username:", row[0], "Password:", row[1])

        connection.close()
    except OperationalError as e:
        print(f"The error '{e}' occurred")

if __name__ == "__main__":
    create_connection()