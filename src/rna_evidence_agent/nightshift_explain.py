"""Nightshift paraphrase of computed checks; never authorizes analysis."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
from .nightshift_backend import NightshiftBackend


def explain_design(design, run_dir, model=None):
    """Keep the computed report authoritative and model prose unreviewed."""
    backend = NightshiftBackend(model=model)
    backend.discover()
    facts = {'status': design['status'], 'factor': design['factor'],
             'checks': design['decision_trace'],
             'differential_expression_run': False}
    prompt = ('Explain the following computed checks in two short sentences. '
              'Matching IDs means alignment between files only; it does NOT prove biological pairing. '
              'Metadata balance does NOT prove biological pairing. Researcher confirmation is still required. '
              'Do not infer a treatment effect, significance or a confirmed paired design. '
              'Use only these facts: ' + json.dumps(facts, separators=(',', ':')))
    response = backend._request('/chat/completions', {
        'model': backend.model, 'stream': False, 'temperature': 0,
        'max_tokens': 220, 'messages': [{'role': 'user', 'content': prompt}]})
    text = response['choices'][0]['message']['content']
    if not isinstance(text, str) or not text.strip():
        raise ValueError('Nightshift did not return explanation text')
    result = {'kind': 'nightshift-design-explanation',
              'dataset_sha256': design['dataset_sha256'],
              'authoritative_decision': design['status'],
              'explanation': text, 'explanation_status': 'unreviewed model prose',
              'may_authorize_analysis': False, 'requested_route': backend.model,
              'reported_model': response.get('model'),
              'request_sha256': hashlib.sha256(prompt.encode()).hexdigest(),
              'response_sha256': hashlib.sha256(text.encode()).hexdigest(),
              'usage': response.get('usage'),
              'provider_receipt': response.get('meterless', {}).get('receipt')}
    Path(run_dir, 'nightshift_explanation.json').write_text(json.dumps(result, indent=2))
    return result
