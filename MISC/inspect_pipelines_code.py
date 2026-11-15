import os
import glob
import re

pipeline_files = glob.glob('pipelines/**/*.py', recursive=True)

for pf in sorted(pipeline_files):
    if '__init__' in pf or '__pycache__' in pf:
        continue
    with open(pf, 'r', encoding='utf-8') as f:
        code = f.read()
    
    # Extract model_name, target_table
    model_match = re.search(r'model_name\s*=\s*[\"\']([^\"\']+)[\"\']', code)
    table_match = re.search(r'target_table\s*=\s*[\"\']([^\"\']+)[\"\']', code)
    fields_match = re.search(r'fields\s*=\s*\[(.*?)\]', code, re.DOTALL)
    
    m_name = model_match.group(1) if model_match else "N/A"
    t_name = table_match.group(1) if table_match else "N/A"
    
    print(f"File: {pf}")
    print(f"  Target: {t_name} | Odoo Model: {m_name}")
    if fields_match:
        f_list = [x.strip().strip('\"\'') for x in fields_match.group(1).split(',') if x.strip()]
        print(f"  Fields extracted: {f_list[:8]}... ({len(f_list)} total)")
    print()

