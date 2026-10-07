#!/usr/bin/env bash
# 现场核对入职流程记录：把 stub-state/<拼音>/workflow.json 里的事件逐条打印，最后一行是当前状态。
# 只读，不改任何状态。
#
# 用法: bash demo/show-workflow.sh <拼音>
set -uo pipefail

PINYIN="${1:?用法: bash demo/show-workflow.sh <拼音>}"
W="$(cd "$(dirname "$0")/.." && pwd)"

python3 - "$W/stub-state/$PINYIN/workflow.json" <<'PY'
import json, sys

try:
    d = json.load(open(sys.argv[1], encoding='utf-8'))
except (OSError, ValueError):
    print('还没有流程记录：入职流程尚未进入审批门（或拼音不对）。')
    sys.exit()
for e in d.get('events', []):
    print(f"  {e.get('at', '')[11:19]}  {e.get('step', ''):<14} {e.get('action', ''):<10} {e.get('note', '')[:40]}")
print(f"当前状态：{d.get('status')}    停在：{d.get('current_step')}")
PY
