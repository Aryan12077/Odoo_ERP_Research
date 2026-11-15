import sys, os
sys.path.insert(0, os.path.abspath('.'))
import psycopg2
from config import get_target_db_config

cfg = get_target_db_config()
conn = psycopg2.connect(
    host=cfg.host,
    port=cfg.port,
    dbname=cfg.database,
    user=cfg.username,
    password=cfg.password
)
cur = conn.cursor()
schema = cfg.schema

cur.execute(f"""
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = '{schema}'
  AND table_name IN ('GEO_MASTER', 'GEO_MASTER_TEMP', 'FISCAL_CALENDAR', 'FISCAL_CALENDAR_TEMP', 'ANALYSIS_CRITERIA', 'ANALYSIS_CRITERIA_TEMP');
""")
tables = [r[0] for r in cur.fetchall()]
print(f"Target DB Schema '{schema}' has tables:", tables)

cur.execute(f"""
SELECT routine_name 
FROM information_schema.routines 
WHERE routine_schema = '{schema}'
  AND routine_name IN ('sp_update_geo_master', 'sp_update_fiscal_calendar', 'sp_update_analysis_criteria');
""")
procs = [r[0] for r in cur.fetchall()]
print(f"Target DB Schema '{schema}' has procedures:", procs)

cur.close()
conn.close()
