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

if __name__=="__main__":
    conn=get_connection()
    print("PostgreSQL 连接成功")

    print("当前数据库：", conn.info.dbname)
    print("当前用户：", conn.info.user)
    print("服务器地址：", conn.info.host)
    print("端口：", conn.info.port)
    conn.close()