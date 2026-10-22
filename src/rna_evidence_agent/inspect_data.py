"""Deterministic input inventory; not differential expression or an LLM run."""
import csv
import hashlib
import json
from pathlib import Path
from .memory import dataset_fingerprint


def inspect_dataset(counts_path, metadata_path, output):
    paths={'expression_counts.csv':str(counts_path),'sample_metadata.csv':str(metadata_path)}
    with Path(counts_path).open(newline='') as stream:
        rows=csv.reader(stream); header=next(rows,None)
        if not header or len(header)<2: raise ValueError('Empty or invalid count matrix')
        offset=2 if header[:2]==['GeneID','symbol'] else 1
        samples=header[offset:]
        if not samples or len(samples)!=len(set(samples)):
            raise ValueError('Count matrix requires unique sample names')
        genes=set(); total_rows=0
        for row in rows:
            if len(row)!=len(header): raise ValueError('Ragged count matrix')
            if not row[0].strip(): raise ValueError('Empty gene identifier')
            if row[0] in genes: raise ValueError('Duplicate gene identifiers')
            genes.add(row[0]); total_rows+=1
            for value in row[offset:]:
                number=float(value)
                if not number>=0 or not number.is_integer():
                    raise ValueError('Expected finite nonnegative integer counts')
    if not total_rows: raise ValueError('Count matrix has no genes')
    with Path(metadata_path).open(newline='') as stream:
        reader=csv.DictReader(stream); fields=reader.fieldnames
        records=list(reader)
    if not fields or not records: raise ValueError('Empty sample metadata')
    # Discover only an exact sample-ID column. Never infer a sample join by row order.
    candidates=[key for key in fields if len({r[key] for r in records})==len(records)
                and {r[key] for r in records}==set(samples)]
    if len(candidates)!=1: raise ValueError('No unique exact sample-ID column in metadata')
    result={'dataset_sha256':dataset_fingerprint(paths),'genes':total_rows,
            'samples':len(samples),'sample_id_column':candidates[0],
            'metadata_columns':fields,'sample_alignment':'exact identifier set match',
            'analysis':'deterministic inventory only; no differential expression performed',
            'files':{name:{'sha256':hashlib.sha256(Path(path).read_bytes()).hexdigest()}
                     for name,path in paths.items()}}
    destination=Path(output); destination.parent.mkdir(parents=True,exist_ok=True)
    destination.write_text(json.dumps(result,indent=2)+'\n')
    return result

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--counts',required=True);p.add_argument('--metadata',required=True);p.add_argument('--output',required=True)
    a=p.parse_args();print(json.dumps(inspect_dataset(a.counts,a.metadata,a.output),indent=2))
