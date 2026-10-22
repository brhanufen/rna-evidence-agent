"""Verify explicit output references without claiming statistical correctness."""
from __future__ import annotations
import json
from pathlib import Path


def verify_claims(claims, result):
    steps={step.index:step for step in result.steps}
    records=[]
    for claim in claims:
        index=claim.get('step')
        step=steps.get(index) if type(index) is int and index>=0 else None
        excerpt=claim.get('stdout_excerpt')
        # Exact output excerpts provide traceability, not validation of a method.
        supported=bool(isinstance(claim.get('claim'),str) and claim['claim'].strip() and
                       step and step.code is not None and step.ok and
                       isinstance(excerpt,str) and len(excerpt.strip())>=8 and
                       excerpt in step.stdout)
        records.append({'claim':str(claim.get('claim','')),
                        'step':claim.get('step'),'stdout_excerpt':excerpt,
                        'status':'output-linked' if supported else 'unsupported-reference',
                        'method_validity':'not assessed'})
    return {'claims':records,'claim_count':len(records),
            'unsupported_count':sum(r['status']!='output-linked' for r in records),
            'coverage':'Only explicitly registered claims are checked; free-text answer coverage is unknown',
            'scientific_correctness':'Not established by matching printed output'}


def review_run(run_dir, result):
    path=Path(run_dir)/'claims.json'
    if not path.exists():
        report={'status':'needs-review','reason':'No explicit claims.json supplied',
                'scientific_correctness':'unreviewed'}
    else:
        try:
            claims=json.loads(path.read_text())
            if not isinstance(claims,list) or not all(isinstance(c,dict) for c in claims):
                raise ValueError('claims.json requires an array of objects')
            report=verify_claims(claims,result)
            report['status']='needs-review' if not report['claim_count'] or report['unsupported_count'] else 'references-linked; method review still required'
        except (ValueError, TypeError) as exc:
            report={'status':'needs-review','reason':'Malformed claim registry',
                    'error_type':type(exc).__name__,'scientific_correctness':'unreviewed'}
    (Path(run_dir)/'claim_review.json').write_text(json.dumps(report,indent=2)+'\n')
    return report
