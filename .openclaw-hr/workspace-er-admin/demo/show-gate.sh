#!/usr/bin/env bash
# 现场核对分权：从 er-admin 真实会话记录里取最近几次查薪资 / 出月报，
# 打印「网关给出的发送人 → 调用的命令 → 闸门结果 → HCM 是否读取」，再列出飞书待配对请求。
# 只读，不改任何状态。
#
# 用法: bash demo/show-gate.sh [条数，默认 3]
set -uo pipefail

HERE="$(cd "$(dirname "$0")/.." && pwd)"
STATE="$(cd "$HERE/.." && pwd)"
N="${1:-3}"

python3 - "$STATE/agents/er-admin/sessions" "$HERE/scripts/hr-data-access.sh" "$N" <<'PY'
import glob, json, os, re, subprocess, sys

sess_dir, gate, n = sys.argv[1], sys.argv[2], int(sys.argv[3])
short = lambda s: re.sub(r'ou_([0-9a-f]{4})[0-9a-f]+', r'ou_\1…', s or '')
LABEL = {'hr': 'HR', 'denied': '已登记 · 非 HR', 'unknown': '未登记', 'demo': '无发送人'}


def role(sender):
    out = subprocess.run(['bash', gate, 'role', sender], capture_output=True, text=True)
    return LABEL.get(out.stdout.strip(), out.stdout.strip())


events = []
files = sorted((f for f in glob.glob(os.path.join(sess_dir, '*.jsonl')) if '.trajectory.' not in f),
               key=os.path.getmtime)[-20:]
for f in files:
    sender, calls = '', {}
    for line in open(f, encoding='utf-8'):
        try:
            o = json.loads(line)
        except ValueError:
            continue
        m = o.get('message') or {}
        r = m.get('role')
        if r == 'user':
            text = ''.join(c.get('text', '') for c in m.get('content', []) if isinstance(c, dict))
            hit = re.search(r'"sender_id":\s*"([^"]+)"', text)
            sender = hit.group(1) if hit else ''
        elif r == 'assistant':
            for c in m.get('content', []):
                if c.get('type') != 'toolCall' or c.get('name') != 'exec':
                    continue
                cmd = (c.get('arguments') or {}).get('command', '')
                if 'payroll-query' in cmd or 'monthly-report' in cmd:
                    calls[c['id']] = (o.get('timestamp', ''), sender, cmd)
        elif r == 'toolResult' and m.get('toolCallId') in calls:
            ts, snd, cmd = calls.pop(m['toolCallId'])
            d = m.get('details') or {}
            if snd:
                events.append((ts, snd, cmd, d.get('exitCode'), d.get('aggregated', '')))

events.sort()
if not events:
    print('还没有飞书上查薪资 / 出月报的记录。')
for ts, snd, cmd, code, out in events[-n:]:
    passed = re.search(r'--sender\s+(\S+)', cmd)
    passed = passed.group(1) if passed else ''
    first = out.strip().splitlines()[0] if out.strip() else ''
    denied = first.startswith('{"allowed":false')
    gate_line = first if denied else '{"allowed":true}'
    print(f'[{ts[5:10]} {ts[11:19]}] 网关给出的发送人：{short(snd)}  →  {role(snd)}')
    print(f'  调用命令：{short(cmd.replace("bash scripts/", ""))}')
    if passed and passed != snd:
        print('  ⚠ 命令里的 --sender 与网关给出的发送人不一致')
    print(f'  闸门结果：{gate_line}    退出码 {code}')
    if denied:
        print('  数据：未读取（闸门之后的查询脚本没有运行）')
    elif code == 0:
        try:
            res = json.loads(out[out.index('{'):out.rindex('}') + 1])
            hit = '；'.join(f"{p.get('name')} · {p.get('role')} · {p.get('salary')}"
                           for p in res.get('people', [])[:3]) + f"（来源 {res.get('source')}）"
        except ValueError:
            hit = out.strip().splitlines()[-1][:60]
        print(f'  数据：已读取  {hit}')
    else:
        print(f'  数据：闸门放行，查询出错')
    print()
PY

echo "飞书待配对请求（未登记账号的消息停在这里，没交给 Agent）："
openclaw pairing list feishu --json 2>/dev/null \
  | python3 -c '
import json, re, sys
raw = sys.stdin.read()
try:
    reqs = json.loads(raw[raw.index("{"):]).get("requests", [])
except ValueError:
    reqs = []
short = lambda s: re.sub(r"ou_([0-9a-f]{4})[0-9a-f]+", r"ou_\1…", str(s))
if not reqs:
    print("  （无）")
for r in reqs:
    print("  " + short(r.get("id") or r.get("senderId") or r) + "  配对码 " + str(r.get("code", "")))
'
