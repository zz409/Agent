import os
import dotenv
import psycopg
from pgvector.psycopg import register_vector

dotenv.load_dotenv()

def get_connection():
    conn=psycopg.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD")
    )
    register_vector(conn)
    return conn