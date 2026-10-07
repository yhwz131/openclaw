#!/usr/bin/env bash
# 绩效演示准备：员工1 的自评先收起来（第 1 轮缺自评），第 2 轮前“员工补交”，赛后恢复原状。
#
# 用法:
#   bash demo/perf-demo.sh prep      赛前：自评和旧的聚合、报告、看板移到备份区
#   bash demo/perf-demo.sh submit    第 2 轮前：员工补交自评（只放回自评两份文件）
#   bash demo/perf-demo.sh restore   赛后：演示中新生成的文件另存，原文件全部放回
#   bash demo/perf-demo.sh status    看当前目录里有哪些文件
set -euo pipefail

W="$(cd "$(dirname "$0")/.." && pwd)"
D="$W/feedback-360/source_feedback/yuangong1"
BKROOT="$W/.demo-backup"
LAST="$BKROOT/LAST"
SELF=(self.json "360-反馈表-员工1-自评.docx")
OUTPUTS=(aggregated-data.json aggregated-report.md report.html)

status() {
  echo "员工1 目录：$D"
  for f in "${SELF[@]}" "${OUTPUTS[@]}"; do
    [ -e "$D/$f" ] && echo "  有    $f" || echo "  没有  $f"
  done
  echo "  反馈 JSON：$(ls "$D"/*.json 2>/dev/null | grep -vc -e aggregated -e self) 份（不含自评）"
}

case "${1:-status}" in
  prep)
    if [ ! -e "$D/self.json" ]; then
      echo "自评已经不在目录里，像是已经 prep 过；先 restore 再 prep。" >&2
      exit 1
    fi
    BK="$BKROOT/live-$(date +%Y%m%d-%H%M%S)"
    mkdir -p "$BK"
    for f in "${SELF[@]}" "${OUTPUTS[@]}"; do
      [ -e "$D/$f" ] && mv "$D/$f" "$BK/"
    done
    echo "$BK" > "$LAST"
    echo "已移到 $BK"
    status
    ;;
  submit)
    BK="$(cat "$LAST")"
    for f in "${SELF[@]}"; do cp -p "$BK/$f" "$D/"; done
    echo "员工1 已补交自评。"
    status
    ;;
  restore)
    BK="$(cat "$LAST")"
    GEN="$BK/演示中生成"
    mkdir -p "$GEN"
    for f in "${OUTPUTS[@]}"; do
      [ -e "$D/$f" ] && mv "$D/$f" "$GEN/"
    done
    for f in "${SELF[@]}" "${OUTPUTS[@]}"; do
      [ -e "$BK/$f" ] && cp -p "$BK/$f" "$D/"
    done
    echo "已恢复原状；演示中生成的文件留在 $GEN"
    status
    ;;
  status)
    status
    ;;
  *)
    echo "用法: bash demo/perf-demo.sh prep|submit|restore|status" >&2
    exit 2
    ;;
esac
