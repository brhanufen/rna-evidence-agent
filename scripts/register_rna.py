"""Register explicit local RNA CSVs in an isolated Zetaris database.

Requires ZETARIS_USERNAME/PASSWORD, the RNA_EVIDENCE_2026 database and
the private rna-evidence-data source container. No arbitrary SQL input.
"""
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from rna_evidence_agent.zetaris import Zetaris

STATEMENTS = [
    'CREATE LIGHTNING REST TABLE counts FROM RNA_EVIDENCE_2026 REQUEST(endpoint "http://rna-evidence-data:8000/counts", method "get", response_type "json", http_encoding "URLENCODED") HEADER () BODY ()',
    'CREATE LIGHTNING REST TABLE metadata FROM RNA_EVIDENCE_2026 REQUEST(endpoint "http://rna-evidence-data:8000/metadata", method "get", response_type "json", http_encoding "URLENCODED") HEADER () BODY ()',
]

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--apply',action='store_true');a=p.parse_args()
    if not a.apply:
        print(json.dumps({'mode':'plan','statements':STATEMENTS},indent=2))
    else:
        client=Zetaris({});client.login()
        results=[]
        output=Path('runs/zetaris_registration.json');output.parent.mkdir(exist_ok=True)
        for sql in STATEMENTS:
            result=client._post('/api/proxy/sql-editor/sqls/run-query',{'sql':sql,'limit':100},True)
            results.append({'sql':sql,'response':result})
            output.write_text(json.dumps(results,indent=2)+'\n')
            print(json.dumps({'statement':sql.split(' OPTIONS')[0],'response':result}))
        output=Path('runs/zetaris_registration.json');output.parent.mkdir(exist_ok=True)
        output.write_text(json.dumps(results,indent=2)+'\n')
