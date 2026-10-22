"""Deterministic paired-design review gate; no LLM or differential expression.

Metadata structure can suggest a paired design. Only a researcher can confirm
whether the matching factor represents the experimental unit.
"""
from __future__ import annotations
import csv
import json
from pathlib import Path
from .inspect_data import inspect_dataset
from .memory import dataset_fingerprint


def review_design(counts, metadata, output_dir, *, factor='cell_line',
                  group='group', control='control', treated='treated',
                  confirmation=None):
    out=Path(output_dir)
    out.mkdir(parents=True,exist_ok=False)
    paths={'expression_counts.csv':str(counts),'sample_metadata.csv':str(metadata)}
    fingerprint=dataset_fingerprint(paths)
    report={'kind':'deterministic-design-review','dataset_sha256':fingerprint,
            'model_used':False,'differential_expression_run':False,
            'factor':factor,'group_column':group,'contrast':[treated,control],
            'decision_trace':[]}
    try:
        inventory=inspect_dataset(counts,metadata,out/'inventory.json')
    except (ValueError,KeyError,TypeError) as exc:
        report.update(status='blocked-input-alignment',reason=str(exc))
        report['decision_trace'].append({'check':'exact sample identifier match','result':'failed',
            'consequence':'Stop before proposing or fitting an analysis; do not join by row position.'})
        return _save(out,report)
    report['decision_trace'].append({'check':'exact sample identifier match','result':'passed',
        'evidence':{'samples':inventory['samples'],'sample_id_column':inventory['sample_id_column']}})
    with Path(metadata).open(newline='') as stream:rows=list(csv.DictReader(stream))
    required={factor,group}
    if not required.issubset(inventory['metadata_columns']):
        report.update(status='needs-design-information',reason='Required factor or group column is absent')
        return _save(out,report)
    pairs={}
    for row in rows:
        key=row[factor];level=row[group]
        if not key or level not in (control,treated):
            report.update(status='needs-design-information',reason='Missing factor or unexpected group value')
            return _save(out,report)
        pairs.setdefault(key,{control:0,treated:0})[level]+=1
    report['pairs']=[{factor:key,'control_samples':v[control],'treated_samples':v[treated],
                      'complete_pair':v[control]==v[treated]==1} for key,v in sorted(pairs.items())]
    complete=bool(pairs) and all(v[control]==v[treated]==1 for v in pairs.values())
    report['decision_trace'].append({'check':'one sample per condition within each factor level',
        'result':'passed' if complete else 'failed','evidence':report['pairs']})
    if not complete or len(pairs)<2:
        report.update(status='needs-design-review',reason='Not enough complete one-to-one pairs for this simple candidate design')
        return _save(out,report)
    report['candidate_design']=f'~ {factor} + {group}'
    report['alternative']='An unpaired model omits the matching factor; it may ignore within-unit dependence. No performance difference has been estimated here.'
    report['question']=f'Does {factor} identify the same biological experimental unit measured in both conditions, with no unresolved confounding?'
    report['decision_trace'].append({'check':'biological pairing confirmed by researcher','result':'pending',
        'consequence':'Metadata structure alone does not establish biological pairing. Do not fit differential expression yet.'})
    if confirmation is not None:
        required_confirmation={'dataset_sha256':fingerprint,'factor':factor,'contrast':[treated,control],
                               'biological_pairing_confirmed':True}
        if any(confirmation.get(k)!=v for k,v in required_confirmation.items()):
            report.update(status='blocked-confirmation',reason='Confirmation does not match this dataset, factor and contrast')
            return _save(out,report)
        report['decision_trace'][-1]={'check':'biological pairing confirmed by researcher','result':'confirmed',
            'consequence':'Candidate design can proceed to statistical method review; no model has been fitted.'}
        report.update(status='ready-for-method-review',confirmation_source='explicit supplied confirmation')
    else:report['status']='needs-researcher-confirmation'
    return _save(out,report)


def _save(out,report):
    (out/'design_review.json').write_text(json.dumps(report,indent=2)+'\n')
    return report


if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--counts',type=Path,required=True);p.add_argument('--metadata',type=Path,required=True)
    p.add_argument('--output-dir',type=Path,required=True);p.add_argument('--factor',default='cell_line')
    a=p.parse_args();print(json.dumps(review_design(a.counts,a.metadata,a.output_dir,factor=a.factor),indent=2))
