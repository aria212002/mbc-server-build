#!/usr/bin/env python3
"""MBC 테스트 서버 (제안 규약). python mbs_server.py --host 0.0.0.0 --port 8081

POST /api/scenes/change: request_id, scene_id, sound_id (문자열).
--mode error / --delay 35 으로 오류 및 무응답 상황을 모사한다.
메모리에서 request_id별 중복을 제거하며 프로세스 재시작 시 기록은 사라진다.
"""
import argparse
import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


class Handler(BaseHTTPRequestHandler):
    seen = {}
    lock = threading.Lock()
    mode = 'ok'
    delay = 0.0

    def post_json(self, status, body):
        raw = json.dumps(body, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(raw)))
        self.end_headers()
        try:
            self.wfile.write(raw)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def do_POST(self):
        if self.path != '/api/scenes/change':
            return self.post_json(404, {'error': 'not found'})
        try:
            size = int(self.headers.get('Content-Length', '0'))
            if not 0 < size <= 65536:
                raise ValueError('invalid length')
            data = json.loads(self.rfile.read(size))
            if not isinstance(data, dict) or not isinstance(data.get('request_id'), str) or not data['request_id'].strip():
                raise ValueError('request_id required')
            if any(k in data and not isinstance(data[k], str) for k in ('scene_id', 'sound_id')):
                raise ValueError('scene_id and sound_id must be strings')
            if not any(data.get(k, '').strip() for k in ('scene_id', 'sound_id')):
                raise ValueError('scene_id or sound_id required')
        except (ValueError, UnicodeError):
            return self.post_json(400, {'error': 'invalid request'})
        if self.delay:
            time.sleep(self.delay)
        if self.mode == 'error':
            return self.post_json(503, {'error': 'mock error'})
        with self.lock:
            old = self.seen.get(data['request_id'])
            if old is not None and old != data:
                return self.post_json(409, {'error': 'request_id conflict'})
            self.seen[data['request_id']] = data
        print(json.dumps(data, ensure_ascii=False), flush=True)
        return self.post_json(200, {'accepted': True, 'request_id': data['request_id']})


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--host', default='127.0.0.1')
    parser.add_argument('--port', type=int, default=8081)
    parser.add_argument('--mode', choices=['ok', 'error'], default='ok')
    parser.add_argument('--delay', type=float, default=0)
    args = parser.parse_args()
    Handler.mode, Handler.delay = args.mode, args.delay
    print(f'MBC mock http://{args.host}:{args.port}', flush=True)
    ThreadingHTTPServer((args.host, args.port), Handler).serve_forever()
