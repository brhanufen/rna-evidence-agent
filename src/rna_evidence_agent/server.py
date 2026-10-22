"""Read-only local demo viewer. No HTTP route executes generated code."""
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
import html
import json

ROOT=Path(__file__).resolve().parents[2]
RUNS={'codex_live_01':'Dataset inventory','codex_live_02':'Sequencing-depth QC','codex_live_03':'Paired design and clarification'}


def render():
    cards=''
    design_path=ROOT/'output_examples/design_cases.json'
    if design_path.exists():
        cases=json.loads(design_path.read_text())['scenarios']
        cards+='<section id="design-review"><h2>Should these samples be paired?</h2><p>Recorded deterministic design checks. No new model calls or differential expression.</p>'
        for case,label in [('original','Original public data'),('mismatched_id','Deliberately mismatched sample ID'),('row_order_changed','Reordered metadata rows'),('unbalanced_pairing','Deliberately unbalanced pairing')]:
            item=cases[case]
            cards+='<details><summary>'+html.escape(label)+' — '+html.escape(item['status'])+'</summary>'
            cards+='<p>'+html.escape(item.get('question',item.get('reason','')))+'</p>'
            cards+='<pre>'+html.escape(json.dumps(item['decision_trace'],indent=2))+'</pre></details>'
        cards+='</section>'
    nav='<a href="#design-review">Paired-design decision</a>'+''.join('<a href="#'+html.escape(run_id,quote=True)+'">'+html.escape(title)+'</a>' for run_id,title in RUNS.items())
    for run_id,title in RUNS.items():
        folder=ROOT/'runs'/run_id;path=folder/'transcript.json'
        public=ROOT/'output_examples'/(run_id+'.json')
        recorded=None
        if not path.exists() and public.exists():
            recorded=json.loads(public.read_text())
        if not path.exists() and recorded is None:
            cards+='<section id="'+html.escape(run_id,quote=True)+'"><h2>'+html.escape(title)+'</h2><p>Run pending.</p></section>';continue
        if recorded is not None:
            summary_data=recorded['summary']
            result={'n_steps':summary_data['steps'],'n_errors':summary_data['errors'],
                    'wall_s':summary_data['seconds'],'final_answer':recorded['answer'],'figures':[]}
            review=recorded.get('claim_review',{})
        else:
            result=json.loads(path.read_text());review_path=folder/'claim_review.json'
            review=json.loads(review_path.read_text()) if review_path.exists() else {}
        summary=f"{result['n_steps']} steps · {result['n_errors']} execution errors · {result['wall_s']:.1f} seconds"
        images=''.join('<img alt="Computed analysis figure" src="/figure/'+run_id+'/'+html.escape(name,quote=True)+'">' for name in result.get('figures',[]) if Path(name).name==name)
        rows=''.join('<tr><td>'+html.escape(str(c.get('claim','')))+'</td><td>'+html.escape(str(c.get('stdout_excerpt','')))+'</td><td>'+html.escape(str(c.get('status','')))+'</td></tr>' for c in review.get('claims',[]))
        cards+='<section id="'+html.escape(run_id,quote=True)+'"><h2>'+html.escape(title)+'</h2><p class="meta">'+summary+'</p><p class="answer">'+html.escape(result['final_answer'])+'</p>'+images+'<details><summary>Inspect evidence references</summary><p>Output linkage does not establish scientific correctness.</p><table><thead><tr><th>Claim</th><th>Printed evidence</th><th>Reference status</th></tr></thead><tbody>'+rows+'</tbody></table></details></section>'
    return '''<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Recorded execution viewer</title><style>
body{font:16px system-ui;background:#101c29;color:#e8eef5;max-width:1100px;margin:44px auto;padding:24px}h1{font-size:44px;margin:8px 0}header p,.meta,footer{color:#a6c1cf}section{background:#1c2d3d;padding:26px;border-radius:14px;margin:20px 0}h2{color:#64d4be}p{line-height:1.65}.answer{white-space:pre-wrap}img{display:block;width:100%;max-width:900px;background:white;border-radius:8px;margin:20px 0}details{margin-top:22px}summary{cursor:pointer;color:#64d4be}table{border-collapse:collapse;width:100%;font-size:14px}td,th{padding:12px;border-bottom:1px solid #3b5368;text-align:left;overflow-wrap:anywhere}footer{line-height:1.6;margin:30px 0}.banner{padding:14px;border:1px solid #3b5368;border-radius:10px}nav{display:flex;gap:18px;flex-wrap:wrap;margin:18px 0}nav a{color:#64d4be}
</style></head><body><header><p>OPEN AGENT HACKATHON · SOLO PROJECT</p><h1>Recorded execution viewer</h1><p>Recompute results. Keep the evidence. Inspect the assumptions.</p></header><nav>'''+nav+'''</nav><p class="banner">Recorded Codex-backed examples on public RNA data exported through Zetaris. This viewer is read-only. It does not trigger analysis or expose a model account.</p>'''+cards+'''<footer>Pre-existing RNA-seq Agent declared. New work connects Zetaris data, Meterless H-MEM, evidence manifests and this viewer. Research prototype; no clinical conclusions. One-off demonstrations are not a reliability benchmark. Cursor contributed the viewer labeling and navigation. Final submission remains pending.</footer></body></html>'''

class Dashboard(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path=='/':
            body=render().encode();kind='text/html; charset=utf-8'
        elif self.path.startswith('/figure/'):
            parts=self.path.split('/')
            if len(parts)!=4 or parts[2] not in RUNS or Path(parts[3]).name!=parts[3] or not parts[3].endswith('.png'):
                self.send_error(404);return
            file=ROOT/'runs'/parts[2]/parts[3]
            if not file.is_file():self.send_error(404);return
            body=file.read_bytes();kind='image/png'
        else:self.send_error(404);return
        self.send_response(200);self.send_header('Content-Type',kind)
        self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)

if __name__=='__main__':HTTPServer(('127.0.0.1',8787),Dashboard).serve_forever()
