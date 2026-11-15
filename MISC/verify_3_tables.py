import sys, os
sys.path.insert(0, os.path.abspath('.'))
import psycopg2
from config import get_target_db_config

cfg = get_target_db_config()
conn = psycopg2.connect(host=cfg.host, port=cfg.port, dbname=cfg.database, user=cfg.username, password=cfg.password)
cur = conn.cursor()
for t in ['GEO_MASTER', 'FISCAL_CALENDAR', 'ANALYSIS_CRITERIA']:
    cur.execute(f'SELECT COUNT(*) FROM "{cfg.schema}"."{t}"')
    print(f"{t}: {cur.fetchone()[0]} rows in {cfg.schema}")
cur.close()
conn.close()

