"""Local Zetaris query connector using the shipped UI proxy contract.

Only explicit catalog tables may be queried. No model-authored SQL is executed.
Credentials and tokens are never included in returned metadata or logs.
"""
from __future__ import annotations
import json
import os
import re
import urllib.request
import uuid


class Zetaris:
    def __init__(self, tables, base_url='http://127.0.0.1:3000'):
        if base_url not in ('http://127.0.0.1:3000', 'http://localhost:3000'):
            raise ValueError('This demo connector supports local Zetaris only')
        self.base_url = base_url
        self.tables = dict(tables)
        for table in self.tables.values():
            if not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*\.[A-Za-z_][A-Za-z0-9_]*', table):
                raise ValueError('Catalog entries require database.table identifiers')
        self.username = os.environ['ZETARIS_USERNAME']
        self.password = os.environ['ZETARIS_PASSWORD']
        self.token = self.org_id = None

    def _post(self, endpoint, payload, authenticated=False):
        headers = {'Content-Type': 'application/json'}
        if authenticated:
            headers.update({'Authorization': 'Bearer ' + self.token,
                            'X-Org-ID': str(self.org_id), 'X-Request-ID': str(uuid.uuid4())})
        request = urllib.request.Request(self.base_url + endpoint,
                  data=json.dumps(payload).encode(), headers=headers, method='POST')
        with urllib.request.urlopen(request, timeout=90) as response:
            return json.load(response)

    def login(self):
        response = self._post('/api/auth/login', {'username': self.username, 'password': self.password})
        # Find named access token fields; never mistake a refresh token for access.
        def find(value, keys):
            if isinstance(value, dict):
                for key in keys:
                    if key in value:
                        return value[key]
                for child in value.values():
                    found = find(child, keys)
                    if found is not None:
                        return found
            return None
        self.token = find(response, ('idToken', 'accessToken', 'access_token', 'token'))
        self.org_id = find(response, ('orgId',))
        if not isinstance(self.token, str) or self.org_id is None:
            raise RuntimeError('Zetaris login response lacks access token or organisation ID')

    def snapshot(self, dataset, limit=1000):
        if dataset not in self.tables:
            raise ValueError('Dataset is not in the explicit catalog')
        if not isinstance(limit, int) or not 1 <= limit <= 10000:
            raise ValueError('Snapshot limit must be 1..10000')
        if not self.token:
            self.login()
        sql = f'SELECT * FROM {self.tables[dataset]} LIMIT {limit}'
        result = self._post('/api/proxy/query/sql/start', {'select': sql, 'pageLimit': limit}, True)
        return {'source': 'zetaris', 'table': self.tables[dataset],
                'query': sql, 'requested_limit': limit, 'response': result,
                'completeness': 'bounded snapshot; not asserted to contain the complete table'}
