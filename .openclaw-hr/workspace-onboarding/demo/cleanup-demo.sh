#!/usr/bin/env bash
# 入职演示赛后清理：按拼音删掉演示中挂上的 7/30/60/90 四个提醒、入职状态目录和待审批记录，
# 以及对照脚本写的 /tmp/no-lobster-demo。HCM 没有删除接口，花名册里的记录保留。
#
# 用法:
#   bash demo/cleanup-demo.sh <拼音>          只列出要清理的内容，不删除
#   bash demo/cleanup-demo.sh <拼音> --yes    实际清理（状态目录先备份到 /tmp）
set -uo pipefail

PINYIN="${1:-}"
YES="${2:-}"
if [ -z "$PINYIN" ] || [ "$PINYIN" = "yuangong1" ]; then
  echo "用法: bash demo/cleanup-demo.sh <演示用的拼音> [--yes]（不清理 yuangong1）" >&2
  exit 2
fi

W="$(cd "$(dirname "$0")/.." && pwd)"
STATE="$(cd "$W/.." && pwd)"
set -a; . "$STATE/env.sh" >/dev/null 2>&1; set +a

JOBS=$(python3 - "$STATE/cron/jobs.json" "$PINYIN" <<'PY'
import json, sys
d = json.load(open(sys.argv[1], encoding='utf-8'))
jobs = d.get('jobs', d) if isinstance(d, dict) else d
for j in jobs:
    if (j.get('name') or '').startswith(f'onboard-review-{sys.argv[2]}-day'):
        print(j['id'], j['name'])
PY
)

echo "提醒："; [ -n "$JOBS" ] && echo "$JOBS" | sed 's/^/  /' || echo "  （无）"
echo "状态目录："; ls -d "$W/stub-state/$PINYIN" 2>/dev/null | sed 's/^/  /' || echo "  （无）"
echo "待审批记录："; ls "$W/pending-approvals/$PINYIN"-*.json 2>/dev/null | sed 's/^/  /' || echo "  （无）"
echo "对照脚本输出："; ls -d /tmp/no-lobster-demo 2>/dev/null | sed 's/^/  /' || echo "  （无）"

if [ "$YES" != "--yes" ]; then
  echo
  echo "以上只是列出。确认后加 --yes 实际清理。"
  exit 0
fi

BK="/tmp/onboarding-demo-cleanup-$PINYIN-$(date +%H%M%S)"
mkdir -p "$BK"
echo "$JOBS" | while read -r id name; do
  [ -n "$id" ] && openclaw cron rm "$id" < /dev/null > /dev/null 2>&1 && echo "已删除提醒 $name"
done
[ -d "$W/stub-state/$PINYIN" ] && mv "$W/stub-state/$PINYIN" "$BK/" && echo "状态目录已移到 $BK"
for f in "$W/pending-approvals/$PINYIN"-*.json; do
  [ -e "$f" ] && mv "$f" "$BK/" && echo "待审批记录已移到 $BK"
done
rm -rf /tmp/no-lobster-demo && echo "已清理 /tmp/no-lobster-demo"
echo "HCM 花名册里的「$PINYIN」没有删除接口，保留；下一场换一个新拼音。"
