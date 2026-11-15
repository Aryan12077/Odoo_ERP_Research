import os
import psycopg2
from dotenv import load_dotenv, find_dotenv

# Automatically locate .env in current or parent directories
dotenv_path = find_dotenv(usecwd=True)
if not dotenv_path:
    # Fallback to parent directory if running from inside MISC/
    dotenv_path = os.path.join(os.path.dirname(__file__), "..", ".env")

load_dotenv(dotenv_path, override=True)

host = os.getenv("TARGET_DB_HOST")
dbname = os.getenv("TARGET_DB_NAME")
user = os.getenv("TARGET_DB_USER")
pwd = os.getenv("TARGET_DB_PASSWORD")
schema = os.getenv("TARGET_DB_SCHEMA")

print(f"Loaded .env from: {os.path.abspath(dotenv_path)}")
print(f"Target DB: Host={host}, DB={dbname}, User={user}, Schema={schema}")
print(f"Password length: {len(pwd) if pwd else 0}, starts with: {repr(pwd[:3]) if pwd else None}")

for port in [5433, 5432]:
    print(f"\nTesting port {port}...")
    try:
        conn = psycopg2.connect(
            host=host,
            port=port,
            dbname=dbname,
            user=user,
            password=pwd,
            connect_timeout=5
        )
        print(f"  [SUCCESS] Connected to port {port}!")
        with conn.cursor() as cur:
            cur.execute("SELECT version();")
            print("  Version:", cur.fetchone()[0][:45])
            cur.execute(f"SELECT schema_name FROM information_schema.schemata WHERE schema_name = '{schema}';")
            sch = cur.fetchone()
            print(f"  Schema '{schema}' exists: {sch is not None}")
        conn.close()
        break
    except Exception as e:
        print(f"  [FAILED] Port {port}: {e}")
