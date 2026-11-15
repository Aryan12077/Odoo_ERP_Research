import sys
import os
import re
import json

file_path = 'odoo_roshni_bkp_local_2.sql'
out_path = 'MISC/backup_analysis_summary.json'

tables_data = {}
current_table = None
current_cols = []
current_rows = []

copy_regex = re.compile(r'COPY\s+[\"\w\.]+\.\"(\w+)\"\s*\((.*?)\)\s+FROM\s+stdin;', re.IGNORECASE)

with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
    for line in f:
        if line.startswith('COPY '):
            m = copy_regex.search(line)
            if m:
                table_name = m.group(1)
                cols_str = m.group(2)
                cols = [c.strip().strip('"') for c in cols_str.split(',')]
                # Skip _TEMP tables to avoid duplication
                if not table_name.endswith('_TEMP'):
                    current_table = table_name
                    current_cols = cols
                    current_rows = []
                else:
                    current_table = None
            else:
                current_table = None
            continue
        
        if current_table:
            if line.strip() == r'\.':
                # end of copy block
                tables_data[current_table] = {'cols': current_cols, 'row_count': len(current_rows), 'rows': current_rows}
                current_table = None
            else:
                # data line
                row = line.rstrip('\r\n').split('\t')
                current_rows.append(row)

print(f"Found {len(tables_data)} non-temp tables:")
summary = {}
for t, d in tables_data.items():
    cols = d['cols']
    rows = d['rows']
    n_rows = len(rows)
    col_stats = {}
    for i, col in enumerate(cols):
        null_cnt = 0
        na_cnt = 0
        zero_cnt = 0
        empty_cnt = 0
        val_cnt = 0
        sample_vals = []
        for r in rows:
            val = r[i] if i < len(r) else r'\N'
            
            if val == r'\N':
                null_cnt += 1
            elif val.upper() in ('NA', 'N/A'):
                na_cnt += 1
            elif val == '':
                empty_cnt += 1
            elif val in ('0', '0.0', '0.00', '0.0000'):
                zero_cnt += 1
            else:
                val_cnt += 1
                if len(sample_vals) < 3 and val not in sample_vals:
                    sample_vals.append(val)
        col_stats[col] = {
            'total': n_rows,
            'null': null_cnt,
            'na': na_cnt,
            'empty': empty_cnt,
            'zero': zero_cnt,
            'valid': val_cnt,
            'pct_missing': round(((null_cnt + na_cnt + empty_cnt) / n_rows * 100), 1) if n_rows > 0 else 0,
            'sample': sample_vals[:3]
        }
    summary[t] = {
        'total_rows': n_rows,
        'cols': col_stats
    }

with open(out_path, 'w', encoding='utf-8') as out_f:
    json.dump(summary, out_f, indent=2)

print(f"Analysis written to {out_path}")
for t, d in summary.items():
    print(f"- {t}: {d['total_rows']} rows, {len(d['cols'])} columns")

