#!/usr/bin/env bash
# R-EXC 实等探针：睡满 1900 秒。用来验证 agents.defaults.subagents.runTimeoutSeconds=1800
# 会在满超时后杀掉子 Agent，而不是让本脚本跑完。
set -euo pipefail
echo "R-EXC-PROBE start $(date -Is) pid=$$"
sleep 1900
echo "R-EXC-PROBE done $(date -Is) (unexpected: should have been killed at 1800s)"
exit 0
