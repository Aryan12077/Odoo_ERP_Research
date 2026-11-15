import sys, os
sys.path.insert(0, os.path.abspath('.'))
import psycopg2
from config import get_target_db_config

cfg = get_target_db_config()
conn = psycopg2.connect(
    host=cfg.host, port=cfg.port, dbname=cfg.database, user=cfg.username, password=cfg.password
)
cur = conn.cursor()
schema = cfg.schema

for t in ['GEO_MASTER_TEMP', 'FISCAL_CALENDAR_TEMP', 'ANALYSIS_CRITERIA_TEMP']:
    cur.execute(f"""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_schema = '{schema}' AND table_name = '{t}'
        ORDER BY ordinal_position;
    """)
    cols = cur.fetchall()
    print(f"=== {t} ({len(cols)} cols) ===")
    for c, dt in cols:
        print(f"  {c:30} | {dt}")
    print()

cur.close()
conn.close()

