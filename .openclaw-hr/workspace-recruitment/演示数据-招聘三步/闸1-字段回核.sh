#!/usr/bin/env bash
# 闸1 · 字段回核：解析结果逐字段回到简历原文找出处。
# 用法：bash 演示数据-招聘三步/闸1-字段回核.sh          原样解析结果，应通过
#       bash 演示数据-招聘三步/闸1-字段回核.sh 改学校   只把学校改成「清华大学」，应拦下
set -u
WS="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$WS"
D=演示数据-招聘三步
case "${1:-原样}" in
  原样)   IN="$D/parsed/员工1-后端开发.json" ;;
  改学校) IN="$D/parsed/员工1-后端开发-学校被改.json" ;;
  *) echo "用法：$0 [原样|改学校]" >&2; exit 2 ;;
esac
echo "== 闸1 字段回核：$(basename "$IN")  对照  简历原文"
echo
bash scripts/recruitment-run.sh node skills/auditing-extraction/scripts/audit_extraction.js \
  "$IN" "$D/inbox/resume-tech-员工1-后端开发.md"
rc=$?
echo
case $rc in
  0) echo "== 退出码 0：通过" ;;
  1) echo "== 退出码 1：拦下，不进入下一步" ;;
  *) echo "== 退出码 $rc：运行出错" ;;
esac
exit $rc
