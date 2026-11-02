#!/usr/bin/env python3
"""链路追踪：把飞书私聊进来的每一句，拆成「飞书 → 网关 → 模型 → 执行白名单 → 身份反查 → 闸门 → HCM」逐跳展示。
只读网关会话记录和 logs/gate-verify.log，不改任何东西。

用法（在 workspace-er-admin 下）: python3 demo/trace/serve.py [端口，默认 18890]
默认监听 0.0.0.0，公网访问须带口令：http://<公网IP>:18890/?k=<TRACE_TOKEN>，之后由 cookie 记住。
口令取环境变量 TRACE_TOKEN，未设置时读 .openclaw-hr/env.sh；本机 127.0.0.1 访问免口令。
TRACE_HOST=127.0.0.1 可改回仅本机。/ablation 为消融矩阵。
"""
import hmac, http.server, json, os, re, subprocess, sys, threading
from datetime import datetime, timezone
from urllib.parse import parse_qsl, urlencode, urlsplit

WS = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
STATE = os.path.dirname(WS)
SESS = os.path.join(STATE, 'agents', 'er-admin', 'sessions')
GATE_LOG = os.path.join(WS, 'logs', 'gate-verify.log')
GATE = os.path.join(WS, 'scripts', 'hr-data-access.sh')
CONF = os.path.join(STATE, 'config', 'openclaw.yaml')
APPROVALS = os.path.join(STATE, 'exec-approvals.json')
HERE = os.path.dirname(os.path.abspath(__file__))
TAIL = re.compile(r'\]\s*\n(?:[^\n:]+):\s*(.*)$', re.S)
OU = re.compile(r'ou_[0-9a-f]{32}')
ABLATION_LOCK = threading.Lock()


def load_token():
    tok = os.environ.get('TRACE_TOKEN', '').strip()
    if tok:
        return tok
    try:
        for line in open(os.path.join(STATE, 'env.sh'), encoding='utf-8'):
            m = re.match(r'\s*(?:export\s+)?TRACE_TOKEN=["\']?([^"\'\s]+)', line)
            if m:
                return m.group(1)
    except OSError:
        pass
    return ''


TOKEN = load_token()


def ts(s):
    return datetime.fromisoformat(s.replace('Z', '+00:00')).timestamp()


def role_of(sender):
    if not sender:
        return 'demo'
    r = subprocess.run(['bash', GATE, 'role', sender], capture_output=True, text=True)
    return (r.stdout.strip() or 'unknown')


def tool_tier(sender):
    try:
        conf = json.load(open(CONF, encoding='utf-8'))
        for a in conf['agents']['list']:
            if a['id'] == 'er-admin':
                tbs = (a.get('tools') or {}).get('toolsBySender') or a.get('toolsBySender') or {}
                hit = tbs.get(f'channel:feishu:{sender}') or tbs.get('*') or {}
                return hit.get('allow', [])
    except Exception:
        pass
    return []


def allowlisted(cmds):
    if not cmds:
        return []
    al = json.load(open(APPROVALS, encoding='utf-8'))['agents']['er-admin']['allowlist']
    r = subprocess.run(['node', os.path.join(WS, 'demo', 'acceptance', 'lib-allowlist.mjs')],
                       input=json.dumps({'allowlist': al, 'cwd': WS, 'commands': cmds}),
                       capture_output=True, text=True)
    try:
        return json.loads(r.stdout)
    except ValueError:
        return [None] * len(cmds)


def gate_lines():
    out = []
    if not os.path.exists(GATE_LOG):
        return out
    for line in open(GATE_LOG, encoding='utf-8'):
        parts = line.rstrip('\n').split('\t')
        if len(parts) < 4:
            continue
        try:
            res = json.loads(parts[3])
        except ValueError:
            res = {}
        out.append({'t': datetime.fromisoformat(parts[0]).timestamp(), 'cmd': parts[1],
                    'given': parts[2].removeprefix('given='), 'res': res})
    return out


def text_of(content):
    if isinstance(content, str):
        return content
    return ''.join(c.get('text', '') for c in content or [] if isinstance(c, dict) and c.get('type') == 'text')


def turns(limit):
    idx = json.load(open(os.path.join(SESS, 'sessions.json'), encoding='utf-8'))
    gates = gate_lines()
    all_turns = []
    for key, entry in idx.items():
        origin = entry.get('origin') or {}
        if origin.get('provider') != 'feishu':
            continue
        m = OU.search(origin.get('from') or '')
        sender = m.group(0) if m else ''
        path = os.path.join(SESS, f"{entry.get('sessionId')}.jsonl")
        if not os.path.exists(path):
            continue
        cur = None
        for line in open(path, encoding='utf-8', errors='ignore'):
            try:
                o = json.loads(line)
            except ValueError:
                continue
            msg = o.get('message') or {}
            r = msg.get('role')
            if r == 'user':
                raw = text_of(msg.get('content'))
                hit = TAIL.search(raw)
                cur = {'t': ts(o['timestamp']), 'sender': sender, 'account': origin.get('accountId') or 'default',
                       'text': (hit.group(1) if hit else raw).strip(), 'calls': [], 'reply': ''}
                all_turns.append(cur)
            elif cur and r == 'assistant':
                for c in msg.get('content') or []:
                    if isinstance(c, dict) and c.get('type') == 'toolCall':
                        args = c.get('arguments') or {}
                        cur['calls'].append({'id': c.get('id'), 'tool': c.get('name'),
                                             'command': args.get('command') or args.get('path') or ''})
                t = text_of(msg.get('content')).strip()
                if t:
                    cur['reply'] = t
            elif cur and r == 'toolResult':
                for c in cur['calls']:
                    if c['id'] == msg.get('toolCallId'):
                        d = msg.get('details') or {}
                        c['exit'] = d.get('exitCode')
                        c['out'] = (d.get('aggregated') or text_of(msg.get('content')))[:600]
                        c['t'] = ts(o['timestamp'])
    all_turns.sort(key=lambda x: x['t'])
    all_turns = all_turns[-limit:]
    for turn in all_turns:
        turn['role'] = role_of(turn['sender'])
        turn['tools'] = tool_tier(turn['sender'])
        execs = [c for c in turn['calls'] if c['tool'] == 'exec']
        for c, ok in zip(execs, allowlisted([c['command'] for c in execs])):
            c['allowlisted'] = ok
            near = [g for g in gates if 'er-admin-run.sh' in c['command'] and g['cmd'] in c['command']
                    and abs(g['t'] - c.get('t', turn['t'])) < 20]
            if near:
                g = min(near, key=lambda g: abs(g['t'] - c.get('t', turn['t'])))
                c['given'] = g['given']
                c['resolved'] = g['res'].get('sender') or g['res'].get('status')
                c['resolvedRole'] = role_of(g['res'].get('sender', '')) if g['res'].get('sender') else g['res'].get('status')
                c['givenRole'] = role_of(g['given']) if g['given'].startswith('ou_') else '未传'
    return all_turns


class H(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def authorized(self):
        if self.client_address[0] in ('127.0.0.1', '::1'):
            return True
        if not TOKEN:
            return False
        cookies = dict(c.strip().split('=', 1) for c in (self.headers.get('Cookie') or '').split(';') if '=' in c)
        return hmac.compare_digest(cookies.get('trace_k', ''), TOKEN)

    def reply(self, code, body, ctype='text/plain; charset=utf-8', headers=()):
        self.send_response(code)
        self.send_header('Content-Type', ctype)
        self.send_header('Cache-Control', 'no-store')
        for k, v in headers:
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body.encode() if isinstance(body, str) else body)

    def do_GET(self):
        url = urlsplit(self.path)
        query = parse_qsl(url.query, keep_blank_values=True)
        given = next((v for k, v in query if k == 'k'), None)
        if given is not None and TOKEN and hmac.compare_digest(given, TOKEN):
            rest = urlencode([(k, v) for k, v in query if k != 'k'])
            return self.reply(302, '', headers=[
                ('Set-Cookie', f'trace_k={TOKEN}; Path=/; HttpOnly; SameSite=Lax; Max-Age=2592000'),
                ('Location', url.path + (f'?{rest}' if rest else ''))])
        if not self.authorized():
            return self.reply(401, '需要口令：在地址后加 ?k=口令（口令见服务器 .openclaw-hr/env.sh 的 TRACE_TOKEN）')
        if self.path.startswith('/api/ablation') and not ABLATION_LOCK.acquire(blocking=False):
            return self.reply(429, json.dumps({'error': '消融正在运行，请稍候再试'}, ensure_ascii=False),
                              'application/json; charset=utf-8')
        try:
            self.route()
        finally:
            if self.path.startswith('/api/ablation'):
                ABLATION_LOCK.release()

    def route(self):
        if self.path.startswith('/api/ablation-stream'):
            self.send_response(200)
            self.send_header('Content-Type', 'application/x-ndjson; charset=utf-8')
            self.send_header('Cache-Control', 'no-store')
            self.end_headers()
            p = subprocess.Popen(['python3', os.path.join(WS, 'demo', 'acceptance', 'ablation.py'), '--jsonl'],
                                 cwd=WS, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            try:
                for line in p.stdout:
                    self.wfile.write(line.encode())
                    self.wfile.flush()
                if p.wait(timeout=120) != 0:
                    self.wfile.write((json.dumps({'error': p.stderr.read()[-800:]}, ensure_ascii=False) + '\n').encode())
            except (BrokenPipeError, ConnectionResetError):
                p.kill()
            return
        if self.path.startswith('/api/ablation'):
            out = '/tmp/er-admin-ablation.json'
            r = subprocess.run(['python3', os.path.join(WS, 'demo', 'acceptance', 'ablation.py'), '--json', out],
                               cwd=WS, capture_output=True, text=True, timeout=120)
            body = open(out, encoding='utf-8').read() if r.returncode == 0 else json.dumps({'error': r.stderr[-800:]})
            data, ctype, code = body.encode(), 'application/json; charset=utf-8', 200 if r.returncode == 0 else 500
        elif self.path.startswith('/ablation'):
            data, ctype, code = open(os.path.join(HERE, 'ablation.html'), 'rb').read(), 'text/html; charset=utf-8', 200
        elif self.path.startswith('/api/trace'):
            try:
                body = json.dumps({'now': datetime.now(timezone.utc).timestamp(), 'turns': turns(6)}, ensure_ascii=False)
                code = 200
            except Exception as e:
                body, code = json.dumps({'error': str(e)}), 500
            data, ctype = body.encode(), 'application/json; charset=utf-8'
        else:
            data, ctype, code = open(os.path.join(HERE, 'index.html'), 'rb').read(), 'text/html; charset=utf-8', 200
        self.send_response(code)
        self.send_header('Content-Type', ctype)
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(data)


if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 18890
    host = os.environ.get('TRACE_HOST', '0.0.0.0')
    if host not in ('127.0.0.1', 'localhost') and not TOKEN:
        sys.exit('未找到 TRACE_TOKEN（环境变量或 .openclaw-hr/env.sh），拒绝对外监听；或用 TRACE_HOST=127.0.0.1 仅本机运行')
    print(f'链路追踪：http://127.0.0.1:{port}/  （本机免口令）')
    if host not in ('127.0.0.1', 'localhost'):
        print(f'公网访问：http://<公网IP>:{port}/?k=<env.sh 里的 TRACE_TOKEN>  · 消融 /ablation?k=…')
    http.server.ThreadingHTTPServer((host, port), H).serve_forever()
