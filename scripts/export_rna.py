"""Export the two fixed RNA tables through Zetaris, with exact row-count checks."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from rna_evidence_agent.zetaris import Zetaris


def export(destination):
    destination=Path(destination);destination.mkdir(parents=True,exist_ok=False)
    client=Zetaris({});client.login()
    manifest={'source':'Zetaris RNA_EVIDENCE_2026 REST tables','tables':[]}
    for table,filename,cap in [('counts','expression_counts.csv',30000),('metadata','sample_metadata.csv',1000)]:
        count_sql=f'SELECT COUNT(*) AS n FROM RNA_EVIDENCE_2026.{table}'
        count=client._post('/api/proxy/sql-editor/sqls/run-query',{'sql':count_sql,'limit':1},True)
        expected=int(count['data'][0][0])
        if not 0<expected<=cap:raise ValueError('Unexpected source row count or export cap exceeded')
        sql=f'SELECT * FROM RNA_EVIDENCE_2026.{table} LIMIT {cap}'
        response=client._post('/api/proxy/sql-editor/sqls/run-query',{'sql':sql,'limit':cap},True)
        headers=response['headers'];rows=response['data']
        if len(rows)!=expected or len(headers)!=len(set(headers)):
            raise ValueError('Export incomplete or ambiguous headers')
        if any(len(row)!=len(headers) for row in rows):raise ValueError('Ragged export')
        records=[dict(zip(headers,row)) for row in rows]
        if table=='counts':
            columns=['GeneID','symbol']+sorted(k for k in headers if k not in ('GeneID','symbol'))
            records.sort(key=lambda r:r['GeneID'])
        else:
            columns=['gsm','cell_line','treatment','group'];records.sort(key=lambda r:r['gsm'])
        path=destination/filename
        with path.open('w',newline='') as stream:
            writer=csv.DictWriter(stream,fieldnames=columns);writer.writeheader();writer.writerows(records)
        manifest['tables'].append({'table':table,'row_count':expected,'exported_rows':len(rows),
                    'query':sql,'file':filename,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
        (destination/'source_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    return manifest

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    print(json.dumps(export(a.output),indent=2))
