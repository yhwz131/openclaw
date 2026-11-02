#!/usr/bin/env bash
# 行政上线前验收：执行白名单、身份反查、闸门名单、红线硬过滤四组，一条命令全跑。
# 用法（在 workspace-er-admin 下）: bash demo/acceptance/run.sh
set -uo pipefail
cd "$(dirname "$0")/../.."

echo '== 1 执行白名单：能执行什么'
node demo/acceptance/exec-allowlist.mjs; r1=$?

echo; echo '== 2 身份反查：认谁'
python3 demo/acceptance/sender-resolve.py; r2=$?

echo; echo '== 3 闸门名单：谁能看'
GATE=scripts/hr-data-access.sh
HR=$(sed -n 's/^HR_IDS=\$'"'"'\([^\\'"'"']*\).*/\1/p' "$GATE")
EMP=$(sed -n 's/^DENY_IDS=\$'"'"'\([^\\'"'"']*\).*/\1/p' "$GATE")
total=0; ok=0
check() {        # 名称 发送人 期望退出码
  local got
  bash "$GATE" check "$2" >/dev/null 2>&1; got=$?
  total=$((total + 1))
  if [ "$got" = "$3" ]; then ok=$((ok + 1)); echo "✓  exit=$got  $1"; else echo "✗  exit=$got（期望 $3）  $1"; fi
}
check 'HR' "$HR" 0
check 'HR · channel:feishu: 前缀' "channel:feishu:$HR" 0
check '员工' "$EMP" 3
check '员工 · user: 前缀' "user:$EMP" 3
check '员工 · 前后带空格' " $EMP " 3
check '没登记过的飞书 ID' 'ou_ffffffffffffffffffffffffffffffff' 3
check 'HR 的 ID 少一位' "${HR%?}" 3
check '无发送人（WebChat / CLI）' '' 0
echo; echo "闸门名单：$total 条，符合预期 $ok 条"
r3=$([ "$ok" = "$total" ] && echo 0 || echo 1)

echo; echo '== 4 红线硬过滤：哪些必须转人工'
python3 demo/acceptance/redline.py; r4=$?

echo
if [ "$r1$r2$r3$r4" = "0000" ]; then echo '全部符合预期'; else echo '有不符合预期的条目，见上'; exit 1; fi
