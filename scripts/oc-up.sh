#!/usr/bin/env bash
# 可选启动 OpenClaw HR。
# 档案目录是 /opt/openclaw-hr/.openclaw-hr（本机没有 /opt/openclaw/.openclaw）。
#
# 直接执行时，进入目录和 source 只作用在这次脚本里。
# 要留在当前终端里，用短命令：oc
#   oc            菜单，可多选
#   oc 1 3        只做第 1、3 步
#   oc all        1→5 全做
#   oc gateway    只启动网关
#   oc stop       关闭网关、HCM、Canvas
#   oc restart    先全部关闭，再启动这三项
#
# 步骤：
#   1 进入档案目录
#   2 先切到 conda 环境 openclaw-hr，清掉 OPENCLAW_HOME，再 source env.sh
#   3 启动网关（已在跑则跳过，不用 --force）
#   4 启动 HCM 后端 8000 和前端 5173
#   5 启动 Canvas 反代 18999
#   6 全部关闭
#   7 全部重启
#
# 换机器拉取后改这几处再使用：
#   PROFILE、CONDA_ACTIVATE、CONDA_ENV
#   step_hcm 里的 Node 目录 /opt/node/node-22/bin
# env.sh 不在仓库里，从 .openclaw-hr/env.sh.example 复制后填写。
# 终端里要留住目录和环境时：oc() { source /你的克隆目录/scripts/oc-up.sh "$@"; }

PROFILE="/opt/openclaw-hr/.openclaw-hr"
ENV_FILE="$PROFILE/env.sh"
LOG_DIR="$PROFILE/logs"
CONDA_ACTIVATE="/usr/local/miniconda3/bin/activate"
CONDA_ENV="openclaw-hr"

if [[ "${BASH_SOURCE[0]}" != "$0" ]]; then
  OC_SOURCED=1
else
  OC_SOURCED=0
fi

oc_finish() {
  local code="${1:-0}"
  if [[ "$OC_SOURCED" -eq 1 ]]; then
    return "$code"
  fi
  exit "$code"
}

port_open() {
  python3 - "$1" <<'PY'
import socket, sys
s = socket.socket()
s.settimeout(0.4)
try:
    sys.exit(0 if s.connect_ex(("127.0.0.1", int(sys.argv[1]))) == 0 else 1)
except OSError:
    sys.exit(1)
PY
}

listener_pids() {
  python3 - "$1" <<'PY'
import os, sys
from pathlib import Path
port = int(sys.argv[1])
want = set()
for path in ("/proc/net/tcp", "/proc/net/tcp6"):
    try:
        lines = open(path).read().splitlines()[1:]
    except OSError:
        continue
    for line in lines:
        parts = line.split()
        local = parts[1]
        if int(local.rsplit(":", 1)[1], 16) == port and parts[3] == "0A":
            want.add(parts[9])
found = []
for pid in os.listdir("/proc"):
    if not pid.isdigit():
        continue
    fd_dir = Path(f"/proc/{pid}/fd")
    try:
        names = list(fd_dir.iterdir())
    except OSError:
        continue
    for name in names:
        try:
            target = os.readlink(name)
        except OSError:
            continue
        if target.startswith("socket:[") and target[8:-1] in want:
            found.append(pid)
            break
print("\n".join(found))
PY
}

proc_cmd() {
  tr '\0' ' ' < "/proc/$1/cmdline" 2>/dev/null || true
}

proc_cwd() {
  readlink "/proc/$1/cwd" 2>/dev/null || true
}

proc_ppid() {
  awk '/^PPid:/ {print $2}' "/proc/$1/status" 2>/dev/null || true
}

# 只认本档案自己的进程，避免关掉同端口上的其他程序。
owns_service() {
  local pid="$1" kind="$2" cmd cwd
  cmd="$(proc_cmd "$pid")"
  cwd="$(proc_cwd "$pid")"
  case "$kind" in
    gateway)
      [[ "$cwd" == "$PROFILE" && "$cmd" == openclaw* ]]
      ;;
    hcm-api)
      [[ "$cwd" == "$PROFILE/hcm/backend" && "$cmd" == *uvicorn* && "$cmd" == *main:app* ]]
      ;;
    hcm-ui)
      [[ "$cwd" == "$PROFILE/hcm/frontend" && ( "$cmd" == *vite* || "$cmd" == *"npm run dev"* ) ]]
      ;;
    canvas)
      [[ "$cmd" == *canvas_proxy.py* || ( "$cmd" == *nginx* && "$cmd" == *"nginx/conf/nginx.conf"* ) ]]
      ;;
    *) return 1 ;;
  esac
}

service_root() {
  local pid="$1" kind="$2" parent
  while parent="$(proc_ppid "$pid")" && [[ -n "$parent" && "$parent" != "1" && "$parent" != "0" ]]; do
    owns_service "$parent" "$kind" || break
    pid="$parent"
  done
  printf '%s\n' "$pid"
}

kill_tree() {
  local pid="$1" child
  [[ -n "$pid" && -d "/proc/$pid" ]] || return 0
  for child in $(ps -o pid= --ppid "$pid" 2>/dev/null); do
    kill_tree "$child"
  done
  kill -TERM "$pid" 2>/dev/null || true
}

stop_listeners() {
  local port="$1" kind="$2" pid root
  local -a roots=()
  for pid in $(listener_pids "$port"); do
    if ! owns_service "$pid" "$kind"; then
      echo "$kind 端口 $port 上的进程 $pid 不是本档案的服务，未关闭" >&2
      continue
    fi
    root="$(service_root "$pid" "$kind")"
    roots+=("$root")
  done
  if [[ ${#roots[@]} -eq 0 ]]; then
    echo "$kind 未在运行"
    return 0
  fi
  for root in "${roots[@]}"; do
    echo "关闭 $kind pid=$root"
    kill_tree "$root"
  done
  local i
  for i in 1 2 3 4 5 6 7 8; do
    port_open "$port" || return 0
    sleep 0.4
  done
  for root in "${roots[@]}"; do
    if [[ -d "/proc/$root" ]]; then
      kill -KILL "$root" 2>/dev/null || true
    fi
  done
  sleep 0.4
  if port_open "$port"; then
    echo "$kind 端口 $port 仍未放开" >&2
    return 1
  fi
}

step_stop() {
  local rc=0
  stop_listeners 18999 canvas || rc=1
  if [[ -f "$PROFILE/nginx/canvas-proxy-python.pid" ]]; then
    local cpid
    cpid="$(cat "$PROFILE/nginx/canvas-proxy-python.pid" 2>/dev/null || true)"
    if [[ -n "$cpid" && -d "/proc/$cpid" ]] && owns_service "$cpid" canvas; then
      kill_tree "$cpid"
    fi
    rm -f "$PROFILE/nginx/canvas-proxy-python.pid"
  fi
  stop_listeners 5173 hcm-ui || rc=1
  stop_listeners 8000 hcm-api || rc=1
  stop_listeners 18790 gateway || rc=1
  return "$rc"
}

step_restart() {
  step_stop || return 1
  step_gateway && step_hcm && step_canvas
}

load_env() {
  if [[ ! -f "$ENV_FILE" ]]; then
    echo "找不到 $ENV_FILE" >&2
    return 1
  fi
  set +u
  if [[ -f "$CONDA_ACTIVATE" ]]; then
    # shellcheck disable=SC1090
    source "$CONDA_ACTIVATE" "$CONDA_ENV" || echo "conda 环境 $CONDA_ENV 激活失败" >&2
  else
    echo "找不到 $CONDA_ACTIVATE，跳过 conda 激活" >&2
  fi
  # 别的实验 profile 会设 OPENCLAW_HOME，残留时网关会读错 exec-approvals.json
  unset OPENCLAW_HOME
  # shellcheck disable=SC1090
  source "$ENV_FILE"
  set -u
  export OPENCLAW_STATE_DIR="$PROFILE"
  export OPENCLAW_CONFIG_PATH="$PROFILE/config/openclaw.yaml"
}

step_dir() {
  cd "$PROFILE" || return 1
  if [[ "$OC_SOURCED" -eq 1 ]]; then
    echo "已进入 $PROFILE"
  else
    echo "脚本内已进入 $PROFILE。当前终端要跟着过去，请用 oc，不要直接执行本文件。"
  fi
}

step_env() {
  load_env || return 1
  if [[ "$OC_SOURCED" -eq 1 ]]; then
    echo "已 source $ENV_FILE"
  else
    echo "已在本次脚本中 source $ENV_FILE。要写进当前终端，请用 oc。"
  fi
}

step_gateway() {
  mkdir -p "$LOG_DIR"
  if port_open 18790; then
    echo "网关已在运行（18790），跳过"
    return 0
  fi
  load_env || return 1
  cd "$PROFILE" || return 1
  nohup openclaw gateway run >>"$LOG_DIR/gateway.nohup.log" 2>&1 &
  local pid=$!
  sleep 2
  if kill -0 "$pid" 2>/dev/null; then
    echo "网关已启动 pid=$pid，日志 $LOG_DIR/gateway.nohup.log"
  else
    echo "网关启动后马上退出，看 $LOG_DIR/gateway.nohup.log" >&2
    return 1
  fi
}

step_hcm() {
  local conda_bin="/usr/local/miniconda3/envs/openclaw-hr/bin"
  local python="python3"
  mkdir -p "$LOG_DIR"
  if [[ -x "$conda_bin/python3" ]]; then
    python="$conda_bin/python3"
    export PATH="$conda_bin:$PATH"
  fi
  if [[ -d /opt/node/node-22/bin ]]; then
    export PATH="/opt/node/node-22/bin:$PATH"
  fi

  if port_open 8000; then
    echo "HCM 后端已在 8000，跳过"
  else
    cd "$PROFILE/hcm/backend" || return 1
    nohup "$python" -m uvicorn main:app --host 0.0.0.0 --port 8000 >>"$LOG_DIR/hcm-backend.log" 2>&1 &
    echo "HCM 后端已启动 pid=$!"
  fi

  if port_open 5173; then
    echo "HCM 前端已在 5173，跳过"
  else
    cd "$PROFILE/hcm/frontend" || return 1
    nohup npm run dev >>"$LOG_DIR/hcm-frontend.log" 2>&1 &
    echo "HCM 前端已启动 pid=$!"
  fi
}

step_canvas() {
  if [[ ! -x "$PROFILE/nginx/start-canvas-proxy.sh" ]]; then
    echo "找不到 canvas 启动脚本" >&2
    return 1
  fi
  bash "$PROFILE/nginx/start-canvas-proxy.sh"
}

run_choice() {
  case "$1" in
    1|dir|cd) step_dir ;;
    2|env) step_env ;;
    3|gateway|gw) step_gateway ;;
    4|hcm) step_hcm ;;
    5|canvas) step_canvas ;;
    6|stop|down|off) step_stop ;;
    7|restart) step_restart ;;
    a|all)
      step_dir && step_env && step_gateway && step_hcm && step_canvas
      ;;
    q|quit|"") return 0 ;;
    *)
      echo "不认识的选项：$1" >&2
      return 1
      ;;
  esac
}

print_menu() {
  cat <<EOF
选择要执行的步骤，可多选，用空格分开。
  1  进入 $PROFILE
  2  conda 切到 openclaw-hr + source env.sh
  3  启动网关
  4  启动 HCM
  5  启动 Canvas
  6  全部关闭
  7  全部重启（先关再开网关、HCM、Canvas）
  a  全部按 1→5 启动
  q  退出
EOF
}

main() {
  local raw choice rc=0
  if [[ $# -eq 0 ]]; then
    if [[ ! -t 0 ]]; then
      echo "没有参数。示例：oc 1 3    或    oc stop    或    oc restart" >&2
      oc_finish 1
      return $?
    fi
    print_menu
    read -r -p "选择: " raw
    # shellcheck disable=SC2086
    set -- $raw
  fi
  for choice in "$@"; do
    choice="${choice%,}"
    run_choice "$choice" || rc=1
  done
  oc_finish "$rc"
}

main "$@"
