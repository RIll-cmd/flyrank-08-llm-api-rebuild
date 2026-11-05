"""Optional real-network failure proof: 4 x 30 s timeouts plus bounded backoff.

Uses a local delayed HTTP fixture, not a claim of a real Ollama outage.
Run separately from the fast unit tests: python verify_timeout.py
"""
import json
import os
from pathlib import Path
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from fastapi.testclient import TestClient
import app


class SlowProvider(BaseHTTPRequestHandler):
    calls = 0

    def do_POST(self):
        SlowProvider.calls += 1
        self.rfile.read(int(self.headers.get('Content-Length', '0')))
        time.sleep(35)
        try:
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(b'{}')
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            pass

    def log_message(self, *args):
        pass


if __name__ == '__main__':
    root = Path(__file__).resolve().parent
    os.chdir(root)
    os.environ.update(LLM_BASE_URL='http://127.0.0.1:8198/v1', LLM_API_KEY='local-timeout-fixture',
                      LLM_MODEL='timeout-fixture', LLM_ENABLED='true', LLM_STUB='0')
    path = root/'logs/model-calls.jsonl'
    before = len(path.read_text().splitlines()) if path.exists() else 0
    server = ThreadingHTTPServer(('127.0.0.1', 8198), SlowProvider)
    server.daemon_threads = True
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        started = time.monotonic()
        response = TestClient(app.app).post('/triage', json={'text': 'Timeout verification'})
        rows = [json.loads(line) for line in path.read_text().splitlines()[before:]]
        proof = {'status':response.status_code, 'response':response.json(),
                 'seconds':round(time.monotonic()-started, 2), 'provider_calls':SlowProvider.calls,
                 'new_log_outcomes':[row['outcome'] for row in rows],
                 'note':'Real delayed local HTTP fixture; unchanged 30-second SDK timeout, three own retries; no model/GPU calls.'}
        assert response.status_code == 504 and SlowProvider.calls == 4
        assert len(rows) == 4 and all(row['outcome'] == 'timeout' for row in rows)
        (root/'timeout-proof.json').write_text(json.dumps(proof, indent=2), encoding='utf-8')
        print(json.dumps(proof, indent=2), flush=True)
    finally:
        server.shutdown()
        server.server_close()
