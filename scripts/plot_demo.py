"""Presentation figure from the same Zetaris export; separate from agent output."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

p=argparse.ArgumentParser();p.add_argument('--snapshot',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
a.output.mkdir(parents=True,exist_ok=False)
with (a.snapshot/'sample_metadata.csv').open() as f:metadata=list(csv.DictReader(f))
samples=[r['gsm'] for r in metadata];totals={s:0 for s in samples}
with (a.snapshot/'expression_counts.csv').open() as f:
    for row in csv.DictReader(f):
        for sample in samples:totals[sample]+=int(row[sample])
fig,ax=plt.subplots(figsize=(11,5.4),layout='constrained')
colors=['#267b83' if r['group']=='control' else '#bd7357' for r in metadata]
bars=ax.bar(samples,[totals[s]/1e6 for s in samples],color=colors,width=.68)
ax.bar_label(bars,labels=[f'{totals[s]/1e6:.2f}' for s in samples],padding=4,fontsize=10)
ax.set(ylabel='Counts in supplied matrix (millions)',xlabel='Sample',title='Raw library size across the supplied gene-count matrix',ylim=(0,45))
ax.spines[['top','right']].set_visible(False);ax.grid(axis='y',alpha=.17);ax.set_axisbelow(True)
ax.tick_params(axis='x',labelsize=9)
from matplotlib.patches import Patch
ax.legend(handles=[Patch(color='#267b83',label='Control'),Patch(color='#bd7357',label='Dex treated')],frameon=False,loc='upper left')
fig.savefig(a.output/'library_sizes.png',dpi=180)
fig.savefig(a.output/'library_sizes.svg')
manifest={'purpose':'Presentation figure recomputed from Zetaris export; original agent figure preserved separately',
          'counts_sha256':hashlib.sha256((a.snapshot/'expression_counts.csv').read_bytes()).hexdigest(),
          'sample_totals':totals,'limitations':'Raw count depth does not establish read quality or differential expression'}
(a.output/'provenance.json').write_text(json.dumps(manifest,indent=2)+'\n')
