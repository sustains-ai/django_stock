import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()


def test_supabase_connection():
    try:
        connection = psycopg2.connect(
            user=os.getenv("SUPBASE_user"),
            password=os.getenv("SUPABASE_password"),
            host=os.getenv("SUPABASE_host"),
            port=os.getenv("SUPABASE_port"),
            dbname=os.getenv("SUPABASE_dbname")
        )
        print("✅ Connection successful")

        cursor = connection.cursor()
        cursor.execute('SELECT * FROM "ESG_Risk_rating" LIMIT 5;')
        rows = cursor.fetchall()
        for row in rows:
            print(row)

        cursor.close()
        connection.close()
        print("🔌 Connection closed")
    except Exception as e:
        print(f"❌ Failed to connect: {e}")


if __name__ == "__main__":
    test_supabase_connection()
