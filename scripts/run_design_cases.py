"""Run a declared deterministic check on a real snapshot and modified controls."""
from pathlib import Path
import argparse,csv,json,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from rna_evidence_agent.design_review import review_design
p=argparse.ArgumentParser();p.add_argument('--snapshot',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
a.output.mkdir(parents=True,exist_ok=False)
counts=a.snapshot/'expression_counts.csv';meta=a.snapshot/'sample_metadata.csv'
with meta.open(newline='') as f:reader=csv.DictReader(f);fields=reader.fieldnames;rows=list(reader)
def write(name,records):
    dest=a.output/name
    with dest.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(records)
    return dest
results={}
results['original']=review_design(counts,meta,a.output/'original')
bad=[dict(r) for r in rows];bad[-1]['gsm']='DELIBERATELY_MISMATCHED_SAMPLE'
results['mismatched_id']=review_design(counts,write('mismatched_metadata.csv',bad),a.output/'mismatched_id')
results['row_order_changed']=review_design(counts,write('reordered_metadata.csv',list(reversed(rows))),a.output/'row_order_changed')
unbalanced=[dict(r) for r in rows];unbalanced[-1]['cell_line']=unbalanced[0]['cell_line']
results['unbalanced_pairing']=review_design(counts,write('unbalanced_metadata.csv',unbalanced),a.output/'unbalanced_pairing')
# No researcher confirmation is invented for the real dataset.
expected={'original':'needs-researcher-confirmation','mismatched_id':'blocked-input-alignment','row_order_changed':'needs-researcher-confirmation','unbalanced_pairing':'needs-design-review'}
for key,status in expected.items():assert results[key]['status']==status,(key,results[key]['status'])
summary={'kind':'controlled deterministic scenarios, not autonomous-agent reliability evaluation','source':'Checked public GSE52778 export through Zetaris','new_model_calls':0,'scenarios':results,'controls':'Only original uses unchanged metadata. Other cases are deliberately modified inputs, explicitly labeled.','biological_confirmation':'Not provided; no differential expression executed.'}
(a.output/'scenario_results.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps({k:r['status'] for k,r in results.items()},indent=2))
