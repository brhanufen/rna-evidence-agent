"""Run the new wrapper with an explicitly configured real model backend."""
from __future__ import annotations
import argparse
import os
from pathlib import Path
import sys


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--counts',type=Path,required=True)
    parser.add_argument('--metadata',type=Path,required=True)
    parser.add_argument('--run-dir',type=Path,required=True)
    parser.add_argument('--memory-dir',type=Path,default=Path('state'))
    parser.add_argument('--baseline',type=Path,required=True,help='Declared pre-existing RNA-seq Agent checkout')
    parser.add_argument('--source-manifest',type=Path,help='Optional Zetaris provenance manifest to copy into the run')
    parser.add_argument('--backend',choices=['codex','anthropic'],default='codex')
    parser.add_argument('--model',help='Required only for an explicitly selected Anthropic backend')
    parser.add_argument('--question',required=True)
    parser.add_argument('--review-pairing',action='store_true',help='Inspect paired design and stop for unresolved researcher confirmation before model calls')
    parser.add_argument('--design-factor',default='cell_line')
    args=parser.parse_args()
    if args.backend=='anthropic' and (not args.model or not os.environ.get('ANTHROPIC_API_KEY')):
        parser.error('Configure ANTHROPIC_API_KEY securely in the environment; do not paste it into chat or files')
    if args.review_pairing:
        import json
        from .design_review import review_design
        design=review_design(args.counts,args.metadata,args.run_dir,factor=args.design_factor)
        print(json.dumps(design,indent=2))
        return
    baseline=args.baseline.resolve()
    if not (baseline/'src/rnaseq_agent/agent.py').is_file():
        parser.error('Baseline checkout is missing the expected agent module')
    sys.path.insert(0,str(baseline/'src'))
    if args.backend=='codex':
        from .codex_backend import CodexBackend
        backend=CodexBackend()
    else:
        from rnaseq_agent.llm import AnthropicBackend
        backend=AnthropicBackend(model=args.model)
    from .workflow import run_analysis
    from .inspect_data import inspect_dataset
    # Input validation occurs before model calls. Keep its record beside, not inside,
    # the fresh run directory so wrapper refuses accidental output overwrites.
    inventory=args.run_dir.parent/(args.run_dir.name+'-input-inventory.json')
    if inventory.exists() or args.run_dir.exists():
        parser.error('Choose a fresh run directory and inventory path')
    inspect_dataset(args.counts,args.metadata,inventory)
    files={'expression_counts.csv':str(args.counts.resolve()),'sample_metadata.csv':str(args.metadata.resolve())}
    if args.source_manifest:
        files['source_manifest.json']=str(args.source_manifest.resolve())
    result,evidence=run_analysis(args.question,
        files,
        args.run_dir,backend,args.memory_dir)
    print(result.final_answer)
    print('Evidence manifest:',args.run_dir/'evidence_manifest.json')

if __name__=='__main__':main()
