#!/usr/bin/env python3
"""反查这条命令是哪个会话发起的，身份以网关会话记录为准，不信模型传的 --sender。

用法: resolve-sender.py <er-admin-run.sh 收到的参数...>
输出一行 JSON:
  {"status": "feishu", "sender": "ou_…"}   飞书私聊，发送人取自会话
  {"status": "local"}                      WebChat / CLI 等非飞书会话
  {"status": "ambiguous", "senders": [...]} 同一命令同时挂在多个飞书发送人名下
  {"status": "notfound"}                   会话记录里找不到这条待执行的命令
"""
import json
import os
import re
import shlex
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SESS_DIR = os.path.join(os.path.dirname(ROOT), 'agents', 'er-admin', 'sessions')
WINDOW_S = 180
PEER = re.compile(r'feishu:(?:[^:]+:)?(?:direct:|group:oc_[0-9a-f]{32}:sender:)(ou_[0-9a-f]{32})$')
FROM = re.compile(r'^(?:feishu:)?(ou_[0-9a-f]{32})$')


def argv_after_runner(command):
    try:
        tokens = shlex.split(command)
    except ValueError:
        return None
    for i, t in enumerate(tokens):
        if t.endswith('er-admin-run.sh'):
            return tokens[i + 1:]
    return None


def pending_exec_commands(path):
    calls, done = {}, set()
    with open(path, encoding='utf-8', errors='ignore') as fh:
        for line in fh:
            try:
                m = (json.loads(line).get('message') or {})
            except ValueError:
                continue
            if m.get('role') == 'assistant':
                for c in m.get('content') or []:
                    if isinstance(c, dict) and c.get('type') == 'toolCall' and c.get('name') == 'exec':
                        calls[c.get('id')] = (c.get('arguments') or {}).get('command', '')
            elif m.get('role') == 'toolResult':
                done.add(m.get('toolCallId'))
    return [cmd for cid, cmd in calls.items() if cid not in done]


def session_peer(key, entry):
    origin = entry.get('origin') or {}
    if origin.get('provider') == 'feishu' or origin.get('surface') == 'feishu':
        hit = FROM.match(origin.get('from') or '')
        if hit:
            return hit.group(1)
    hit = PEER.search(key)
    return hit.group(1) if hit else None


def main(argv):
    try:
        index = json.load(open(os.path.join(SESS_DIR, 'sessions.json'), encoding='utf-8'))
    except (OSError, ValueError):
        index = {}
    now = time.time()
    matches = []
    for key, entry in index.items():
        sid = entry.get('sessionId')
        path = os.path.join(SESS_DIR, f'{sid}.jsonl') if sid else ''
        if not path or not os.path.exists(path) or now - os.path.getmtime(path) > WINDOW_S:
            continue
        for cmd in pending_exec_commands(path):
            if argv_after_runner(cmd) == argv:
                matches.append(session_peer(key, entry))
    if not matches:
        return {'status': 'notfound'}
    feishu = sorted({m for m in matches if m})
    if not feishu:
        return {'status': 'local'}
    if len(feishu) > 1 or None in matches:
        return {'status': 'ambiguous', 'senders': feishu}
    return {'status': 'feishu', 'sender': feishu[0]}


if __name__ == '__main__':
    print(json.dumps(main(sys.argv[1:]), ensure_ascii=False))
