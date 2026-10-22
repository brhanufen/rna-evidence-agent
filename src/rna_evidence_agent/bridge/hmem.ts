import fs from 'node:fs';
import path from 'node:path';
import { pathToFileURL } from 'node:url';

// JSON stdin/stdout keeps the sponsor implementation separate from Python.
const req = JSON.parse(fs.readFileSync(0, 'utf8'));
if (!/^[a-f0-9]{64}$/.test(req.dataset)) throw new Error('Dataset must be a SHA-256 fingerprint');
const root = process.env.HMEM_REFERENCE;
if (!root) throw new Error('Set HMEM_REFERENCE to the pinned Meterless reference');
const { HMEM } = await import(pathToFileURL(path.join(root, 'src/index.ts')).href);
const memory = new HMEM({persistDir: path.join(req.state_dir, req.dataset), actor: 'rna-evidence-agent'});
let result;
switch (req.action) {
  case 'add':
    result = memory.add({content: req.content, source: req.source,
      type: 'factual', layer: 'working', confidence: req.confidence ?? 0.7,
      tags: ['rna-analysis', ...(req.tags ?? [])], chatId: req.dataset});
    break;
  case 'query':
    result = memory.query(req.query, {chatId: req.dataset, topN: 5});
    break;
  case 'feedback':
    if (!['helpful', 'not_helpful', 'wrong'].includes(req.kind)) throw new Error('Invalid feedback');
    memory.feedback(req.memory_id, req.kind); result = {recorded: true}; break;
  case 'audit': result = memory.ledger.all(); break;
  default: throw new Error('Unsupported operation');
}
console.log(JSON.stringify(result));
