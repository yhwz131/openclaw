#!/usr/bin/env bash
# 对照组：不用 Lobster 的一次性入职脚本。审批门只是一句“请等待”，后台照样往下跑。
# 只写 /tmp/no-lobster-demo，不碰真实入职记录。
DIR=/tmp/no-lobster-demo/yuangong1
LOG=$DIR/events.log
rm -rf "$DIR"; mkdir -p "$DIR"

log() { echo "$(date +%H:%M:%S)  $1" >> "$LOG"; }

log "prep            材料准备 完成"
echo "[入职] 材料准备完成。"
echo "[入职] 已暂停：请等待 HR 主管审批合同，批准后再继续。"

(
  sleep 3
  log "contract_gate   （无人审批）直接通过"
  echo '{"contract":"signed"}' > "$DIR/contract.json"
  sleep 1
  log "account_gate    （无人审批）直接通过"
  echo '{"account":"XQ5453","email":"yuangong1@xingqiao-tech.com"}' > "$DIR/account.json"
  sleep 1
  log "buddy           导师已分配"
  echo '{"buddy":"导师1"}' > "$DIR/buddy.json"
  log "complete        入职归档"
) > /dev/null 2>&1 &
disown
exit 0
