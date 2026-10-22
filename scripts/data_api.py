"""Read-only RNA CSV-to-JSON source, reachable only inside Docker network."""
import csv
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
from pathlib import Path

DATA=Path('/data')
ENDPOINTS={'/counts':'expression_counts.csv','/metadata':'sample_metadata.csv'}
CACHE={}
for endpoint,name in ENDPOINTS.items():
    with (DATA/name).open(newline='') as stream:
        records=list(csv.DictReader(stream))
    if endpoint=='/counts':
        for record in records:
            for key,value in record.items():
                if key not in ('GeneID','symbol'):record[key]=int(value)
    CACHE[endpoint]=json.dumps(records,separators=(',',':')).encode()

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path not in CACHE:self.send_error(404);return
        body=CACHE[self.path]
        self.send_response(200);self.send_header('Content-Type','application/json')
        self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)

HTTPServer(('0.0.0.0',8000),Handler).serve_forever()
