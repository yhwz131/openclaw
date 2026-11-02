#!/usr/bin/env bash
# 闸2 · 敏感字段删除：递归删掉身份类字段，删完自检，有残留就不许评分。
# 用法：bash 演示数据-招聘三步/闸2-敏感字段删除.sh
set -u
WS="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$WS"
D=演示数据-招聘三步
IN="$D/test-fixtures/demo-lifecycle/planted-sensitive-员工1-full.json"
OUT="$D/scoring/demo-脱敏后-员工1.json"
KEYS='"(年龄|性别|婚育|户籍|民族|政治面貌|school_tier)"'

echo "== 闸2 敏感字段删除：$(basename "$IN")"
echo "-- 删除前，抽查样本里埋的敏感字段："
grep -oE "$KEYS *: *[^,}]*" "$IN" | sed 's/^/   /'
echo
bash scripts/recruitment-run.sh node skills/filtering-sensitive-fields/scripts/filter_sensitive.js "$IN" "$OUT"
rc=$?
echo
echo "-- 删除后，在 $(basename "$OUT") 里搜同样几项："
left=$(grep -cE "$KEYS *:" "$OUT" 2>/dev/null || true)
echo "   残留 ${left:-0} 处"
echo
[[ $rc -eq 0 ]] && echo "== 退出码 0：删干净，放行进入评分" || echo "== 退出码 $rc：有残留，不许评分"
exit $rc
