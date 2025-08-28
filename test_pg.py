import os
import psycopg

conn = psycopg.connect(
    host=os.getenv("PGHOST", "localhost"),
    port=os.getenv("PGPORT", "5432"),
    user=os.getenv("PGUSER", "postgres"),
    password=os.getenv("PGPASSWORD", ""),
    dbname=os.getenv("PGDATABASE", "pedidos"),
)
with conn.cursor() as cur:
    cur.execute("SELECT current_database(), current_user, version();")
    db, usr, ver = cur.fetchone()
    print("✅ Conectado a:", db, "| Usuario:", usr)
    print(ver.splitlines()[0])
conn.close()
