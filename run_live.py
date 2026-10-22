"""Bound the live CLI process and every child analysis process to ten minutes.

Pass the same arguments as rna-evidence-agent. Credentials stay in environment.
"""
import json
import os
from pathlib import Path
import signal
import subprocess
import sys

root=Path(__file__).resolve().parent
env=os.environ.copy()
env['PYTHONPATH']=str(root/'src')+os.pathsep+env.get('PYTHONPATH','')
process=subprocess.Popen([sys.executable,'-m','rna_evidence_agent.cli',*sys.argv[1:]],
                         env=env,start_new_session=True)
try:
    code=process.wait(timeout=600)
except subprocess.TimeoutExpired:
    os.killpg(process.pid,signal.SIGTERM)
    try:process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        os.killpg(process.pid,signal.SIGKILL);process.wait()
    print(json.dumps({'status':'incomplete','error':{'type':'RunDeadline','message':'Ten-minute live-run deadline reached; child analysis processes stopped'}}),file=sys.stderr)
    code=124
raise SystemExit(code)
