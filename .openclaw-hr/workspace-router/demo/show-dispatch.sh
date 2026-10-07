#!/usr/bin/env bash
# 现场核对总控派发：从总控真实会话记录里取最近几次派单，
# 打印「消息从哪个入口来 → 说了什么 → 派给了谁 → 子会话是否接收」，再列出总控能用的工具。
# 只读，不改任何状态。
#
# 用法: bash demo/show-dispatch.sh [条数，默认 2]
set -uo pipefail

HERE="$(cd "$(dirname "$0")/.." && pwd)"
STATE="$(cd "$HERE/.." && pwd)"

python3 - "$STATE" "${1:-2}" <<'PY'
import json, os, re, sys

state, n = sys.argv[1], int(sys.argv[2])
sess_dir = os.path.join(state, 'agents/router/sessions')
SECRET = re.compile(r'(?i)(secret|token|password|api[_-]?key|linkcode)(["\'\s:：=]+)[^\s,，"\']+')
red = lambda s: SECRET.sub(r'\1\2***', s or '')

origin = {}
try:
    index = json.load(open(os.path.join(sess_dir, 'sessions.json'), encoding='utf-8'))
    for v in index.values():
        o = v.get('origin') or {}
        origin[v.get('sessionId')] = o.get('surface') or o.get('provider') or ''
except (OSError, ValueError):
    pass

events = []
files = sorted((f for f in os.listdir(sess_dir) if f.endswith('.jsonl') and '.trajectory.' not in f),
               key=lambda f: os.path.getmtime(os.path.join(sess_dir, f)))[-15:]
for f in files:
    sid = f[:-6]
    said, calls = '', {}
    for line in open(os.path.join(sess_dir, f), encoding='utf-8'):
        try:
            o = json.loads(line)
        except ValueError:
            continue
        m = o.get('message') or {}
        r = m.get('role')
        if r == 'user':
            text = ''.join(c.get('text', '') for c in m.get('content', []) if isinstance(c, dict))
            text = re.sub(r'(?s)^.*?```\s*\n', '', text) if '```' in text else text
            said = re.sub(r'^\[[^\]]+\]\s*', '', text.strip().splitlines()[-1] if text.strip() else '')
        elif r == 'assistant':
            for c in m.get('content', []):
                if c.get('type') == 'toolCall' and c.get('name') == 'sessions_spawn':
                    a = c.get('arguments') or {}
                    calls[c['id']] = (o.get('timestamp', ''), said, a.get('agentId'), a.get('taskName'), a.get('task', ''))
        elif r == 'toolResult' and m.get('toolCallId') in calls:
            ts, s, agent, name, task = calls.pop(m['toolCallId'])
            body = ''.join(c.get('text', '') for c in m.get('content', []) if isinstance(c, dict))
            status = re.search(r'"status":\s*"([^"]+)"', body)
            events.append((ts, origin.get(sid, ''), s, agent, name, task, status.group(1) if status else '?'))

events.sort()
if not events:
    print('还没有派单记录。')
for ts, ch, s, agent, name, task, status in events[-n:]:
    print(f'[{ts[5:10]} {ts[11:19]}] 入口：{ch or "未记录"}')
    print(f'  用户说：{red(s)[:70]}')
    print(f'  总控派给：{agent}    任务名：{name}    子会话：{status}')
    print(f'  派单内容：{red(task)[:90]}')
    print()

cfg = json.load(open(os.path.join(state, 'config/openclaw.yaml'), encoding='utf-8'))
router = next(a for a in cfg['agents']['list'] if a['id'] == 'router')
print('总控能用的工具：' + '、'.join(router.get('tools', {}).get('allow', [])))
print('（没有 exec、write、edit：想自己动手也没有工具）')
PY
