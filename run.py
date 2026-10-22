"""Machine-readable, offline sample entry point. Live analysis uses the CLI.

Sample mode runs deterministic analysis and explicitly does not call an LLM.
"""
from __future__ import annotations
import argparse
import csv
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import sys
import time

ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'src'))
from rna_evidence_agent.inspect_data import inspect_dataset


def run(request):
    start=time.monotonic()
    run_id=request.get('run_id','')
    if not isinstance(run_id,str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,64}',run_id):
        raise ValueError('run_id must be 1..64 letters, digits, underscores or hyphens')
    log_dir=ROOT/'logs';log_dir.mkdir(exist_ok=True)
    log_path=log_dir/('trace-'+run_id+'.jsonl')
    if log_path.exists():raise ValueError('Run ID already exists; choose a fresh ID')
    def emit(action,status,summary):
        event={'timestamp':datetime.now(timezone.utc).isoformat(),'run_id':run_id,
               'component':'offline-sample','action':action,'status':status,'summary':summary}
        with log_path.open('a') as stream:stream.write(json.dumps(event)+'\n')
        print(json.dumps(event),file=sys.stderr)
    emit('start','running','Deterministic sample mode; no model or sponsor service calls')
    try:
        if request.get('options',{}).get('sample_mode') is not True:
            raise ValueError('This entry point currently supports explicit sample_mode=true only; use rna-evidence-agent CLI for live model analysis')
        task=request.get('input',{}).get('task')
        data=ROOT/'data/sample'
        artifacts=ROOT/'runs'/run_id;artifacts.mkdir(parents=True,exist_ok=False)
        inventory=inspect_dataset(data/'expression_counts.csv',data/'sample_metadata.csv',artifacts/'inventory.json')
        emit('inventory','success','Synthetic count values and sample identifiers inventoried')
        if task=='inventory':
            output={'genes':inventory['genes'],'samples':inventory['samples'],
                    'dataset_sha256':inventory['dataset_sha256']}
        elif task=='group_counts':
            with (data/'sample_metadata.csv').open() as stream:
                records=list(csv.DictReader(stream))
            counts={}
            for record in records:counts[record['group']]=counts.get(record['group'],0)+1
            output={'samples_per_group':counts,'method':'Exact metadata row counts, after sample-ID match'}
        elif task=='review_claim':
            claim=request['input'].get('claim','')
            output={'claim':claim,'decision':'unsupported',
                    'reason':'Synthetic count data and group labels cannot establish clinical effectiveness or a causal effect.',
                    'scope':'This is a fixed demonstration guardrail, not a general claim classifier or LLM review'}
            emit('review','success','Unsupported clinical conclusion declined in fixed sample scenario')
        else:raise ValueError('Unknown sample task')
        output.update({'data_kind':'synthetic','model_used':False,'sponsor_services_used':False})
        result={'run_id':run_id,'status':'success','mode':'offline-deterministic-sample',
                'output':output,'artifacts':[str((artifacts/'inventory.json').relative_to(ROOT))],
                'log_file':str(log_path.relative_to(ROOT)),
                'execution_time_seconds':round(time.monotonic()-start,4)}
        emit('complete','success','Sample operation completed; not a live agent benchmark')
        return result
    except Exception as exc:
        emit('error','failed',type(exc).__name__)
        return {'run_id':run_id,'status':'error','error':{'type':type(exc).__name__,'message':str(exc),'recoverable':True},'log_file':str(log_path.relative_to(ROOT))}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--input',type=Path,required=True);a=p.parse_args()
    print(json.dumps(run(json.loads(a.input.read_text())),indent=2))
