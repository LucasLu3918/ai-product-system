"""Reference issuer for a separate administrator-controlled host, never an Agent tool.

The administrator performs Human authentication/approval before calling issue().
Deploy behind authenticated approval UI; the public TLS API exposes status/consume
only and cannot issue grants. Private key and database must be inaccessible to Agents.
"""
from __future__ import annotations

import argparse
import base64
import copy
import json
import sqlite3
import ssl
import stat
import uuid
from datetime import UTC, datetime, timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

import yaml
from publication_authority import PublicationError, _timestamp, canonical, digest


class Issuer:
    def __init__(self, database: Path, private_key: Any, key_id: str):
        self.database, self.key, self.key_id = database, private_key, key_id
        with sqlite3.connect(database, timeout=10) as db:
            db.execute('CREATE TABLE IF NOT EXISTS grants (id TEXT PRIMARY KEY, digest TEXT NOT NULL, consumed INTEGER NOT NULL DEFAULT 0)')

    def sign(self, document: dict[str, Any]) -> dict[str, Any]:
        doc = copy.deepcopy(document)
        doc.pop('signature', None)
        raw = self.key.sign(canonical(doc))
        doc['signature'] = {'algorithm': 'ed25519', 'issuer_key_id': self.key_id,
                            'value_b64': base64.b64encode(raw).decode()}
        return doc

    def issue(self, proposal: dict[str, Any], human_id: str, ttl: int = 900) -> dict[str, Any]:
        """Call only after independent Human approval of this exact proposal and evidence."""
        if not human_id or not 0 < ttl <= 3600 or proposal.get('version') != 2:
            raise PublicationError('invalid grant request')
        if proposal.get('approval', {}).get('status') != 'PENDING' or proposal.get('signature'):
            raise PublicationError('only pending proposals can be issued')
        if proposal.get('proposal', {}).get('fingerprint') != digest(proposal.get('scope')):
            raise PublicationError('proposal scope mismatch')
        if not proposal.get('evidence', {}).get('validation') or proposal['evidence'].get('unresolved'):
            raise PublicationError('complete validation evidence required')
        now = datetime.now(UTC)
        grant = copy.deepcopy(proposal)
        grant['approval'] = {'id': uuid.uuid4().hex, 'status': 'APPROVED', 'approved_by': human_id,
                             'approved_at': now.isoformat(), 'expires_at': (now + timedelta(seconds=ttl)).isoformat()}
        grant = self.sign(grant)
        with sqlite3.connect(self.database, timeout=10) as db:
            db.execute('INSERT INTO grants (id,digest) VALUES (?,?)', (grant['approval']['id'], digest(grant)))
        return grant

    def check(self, request: dict[str, Any], consume: bool) -> dict[str, Any]:
        record = request['record']
        grant_id = record['approval']['id']
        now = datetime.now(UTC)
        response = {'version': 1, 'nonce': request['nonce'], 'grant_id': grant_id,
                    'record_digest': request['record_digest'], 'action_digest': request['action_digest'],
                    'expires_at': (now + timedelta(seconds=30)).isoformat(), 'result': 'DENIED'}
        if not isinstance(request['nonce'], str) or not request['nonce'] or len(request['nonce']) > 128:
            raise PublicationError('invalid nonce')
        if request.get('version') != 1 or digest(record) != request['record_digest'] or digest(record['scope']) != request['action_digest']:
            return self.sign(response)
        if _timestamp(record['approval']['expires_at']) <= now:
            return self.sign(response)
        with sqlite3.connect(self.database, timeout=10) as db:
            db.execute('BEGIN IMMEDIATE')
            row = db.execute('SELECT digest,consumed FROM grants WHERE id=?', (grant_id,)).fetchone()
            if row and row == (digest(record), 0):
                if consume:
                    db.execute('UPDATE grants SET consumed=1 WHERE id=? AND consumed=0', (grant_id,))
                response['result'] = 'CONSUMED' if consume else 'AVAILABLE'
        return self.sign(response)


def handler(issuer: Issuer):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass  # Avoid recording signed records, argv, identity or receipt payloads.

        def do_POST(self):
            try:
                size = int(self.headers.get('Content-Length', '0'))
                if self.path not in {'/status', '/consume'} or not 0 < size <= 1024 * 1024:
                    raise PublicationError('invalid request')
                payload = json.loads(self.rfile.read(size))
                response = canonical(issuer.check(payload, self.path == '/consume'))
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', str(len(response)))
                self.end_headers()
                self.wfile.write(response)
            except (ValueError, KeyError, TypeError, sqlite3.Error):
                self.send_error(400, 'Invalid publication request')
    return Handler


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, required=True, help='Issuer host configuration; never configured by an Agent')
    sub = parser.add_subparsers(dest='command', required=True)
    grant = sub.add_parser('grant', help='Administrator-only: issue after independently authenticated Human approval')
    grant.add_argument('--proposal', type=Path, required=True)
    grant.add_argument('--approved-by', required=True)
    grant.add_argument('--ttl', type=int, default=900)
    sub.add_parser('serve')
    args = parser.parse_args()
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    from cryptography.hazmat.primitives.serialization import load_pem_private_key
    from publication_authority import protected_file
    config = yaml.safe_load(protected_file(args.config).read_text())
    key_path = protected_file(Path(config['private_key']))
    if stat.S_IMODE(key_path.stat().st_mode) & 0o077:
        raise PublicationError('issuer private key must have mode 0600')
    database = Path(config['database']).resolve()
    protected_file(database.parent)
    if database.exists():
        protected_file(database)
    key = load_pem_private_key(key_path.read_bytes(), password=None)
    if not isinstance(key, Ed25519PrivateKey):
        raise PublicationError('Ed25519 issuer key required')
    issuer = Issuer(database, key, config['key_id'])
    if args.command == 'grant':
        proposal = yaml.safe_load(args.proposal.read_text())
        print(yaml.safe_dump(issuer.issue(proposal, args.approved_by, args.ttl), sort_keys=False))
        return 0
    server = ThreadingHTTPServer((config.get('bind', '127.0.0.1'), int(config.get('port', 8443))), handler(issuer))
    server.daemon_threads = True
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.minimum_version = ssl.TLSVersion.TLSv1_2
    context.load_cert_chain(protected_file(Path(config['tls_certificate'])), protected_file(Path(config['tls_private_key'])))
    server.socket = context.wrap_socket(server.socket, server_side=True)
    server.serve_forever()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
