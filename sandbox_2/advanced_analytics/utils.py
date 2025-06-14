import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()


def get_esg_scores_for_portfolio(symbols):
    try:
        connection = psycopg2.connect(
            user=os.getenv("SUPBASE_user"),
            password=os.getenv("SUPABASE_password"),
            host=os.getenv("SUPABASE_host"),
            port=os.getenv("SUPABASE_port"),
            dbname=os.getenv("SUPABASE_dbname")
        )
        cursor = connection.cursor()
        print("✅ Connected to database")

        # If a single symbol string is passed, convert it to a tuple
        if isinstance(symbols, str):
            symbols = (symbols,)
        elif isinstance(symbols, list):
            symbols = tuple(symbols)

        query = f"""
            SELECT "Symbol", "Total_ESG_Risk_score", "Environment_Risk_Score",
                   "Governance_Risk_Score", "Social_Risk_Score",
                   "Controversy_Level", "Controversy_Score",  "ESG_Risk_Level"
            FROM "ESG_Risk_rating"
            WHERE "Symbol" IN %s;
        """
        cursor.execute(query, (symbols,))
        results = cursor.fetchall()

        cursor.close()
        connection.close()
        print("🔌 Connection closed")
        return results

    except Exception as e:
        print(f"❌ Error fetching ESG scores: {e}")
        return []
