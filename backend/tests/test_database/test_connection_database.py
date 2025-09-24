import psycopg
import os
from dotenv import load_dotenv

load_dotenv()
host = os.getenv("SUPABASE_DB_HOST")
port = os.getenv("SUPABASE_DB_PORT")
dbname = os.getenv("SUPABASE_DB_NAME")
user = os.getenv("SUPABASE_DB_USER")
password = os.getenv("SUPABASE_DB_PASSWORD")
conn = psycopg.connect(
    host=f"{host}",  # adapte la région
    port=f"{port}",
    dbname=f"{dbname}",
    user=f"{user}",
    password=f"{password}",
    sslmode="require",
    connect_timeout=60,
)
print(conn)
with conn.cursor() as cur:
    cur.execute("select version(), current_user, inet_server_addr(), inet_server_port()")
    print(cur.fetchone())

