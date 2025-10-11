import os
from psycopg import connect
from psycopg.rows import dict_row
from langgraph.checkpoint.postgres import PostgresSaver
from dotenv import load_dotenv
load_dotenv()

host = os.getenv("SUPABASE_DB_HOST")
port = os.getenv("SUPABASE_DB_PORT")
dbname = os.getenv("SUPABASE_DB_NAME")
user = os.getenv("SUPABASE_DB_USER")
password = os.getenv("SUPABASE_DB_PASSWORD")
conn = connect(
    host=host,
    port=port,
    dbname=dbname,
    user=user,
    password=password,
    sslmode="require",
    connect_timeout=60,
    row_factory=dict_row
)
conn.autocommit = True


CHECKPOINTER_POSTGRES = PostgresSaver(conn)
CHECKPOINTER_POSTGRES.setup()