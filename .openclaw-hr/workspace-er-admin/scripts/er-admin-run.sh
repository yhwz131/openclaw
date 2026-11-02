#!/usr/bin/env bash
# er-admin 唯一允许的 exec 入口：政策检索 / 花名册薪资 / 月报。
set -euo pipefail        # -e 任一命令非零即退出；-u 引用未定义变量报错；-o pipefail 管道任一段失败即整体失败
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"        # 本脚本所在目录的上一级 = 行政工作区根目录
ACCESS="$ROOT/scripts/hr-data-access.sh"        # 闸门脚本的路径，下面 require_hr_data 用

extract_sender() {        # 把模型写的 --sender 挑出来，其余参数原样留给真脚本
  SENDER=""        # 模型声称的发送人，先置空
  FORWARD=()        # 要转交给真脚本的参数列表（不含 --sender）
  while [ "$#" -gt 0 ]; do        # $# 是剩余参数个数；还有参数就继续
    case "$1" in        # 看当前这个参数是什么
      --sender)        # 写法一：--sender ou_xxx（两个词）
        SENDER="${2:-}"        # 下一个词就是 ID
        shift 2        # 一次扔掉两个词
        ;;
      --sender=*)        # 写法二：--sender=ou_xxx（一个词）
        SENDER="${1#--sender=}"        # 去掉前缀 "--sender="，剩下的就是 ID
        shift        # 扔掉这一个词
        ;;
      *)        # 其它参数，如 --name 张三
        FORWARD+=("$1")        # 追加到转交列表
        shift
        ;;
    esac
  done
}

# 身份以网关会话记录为准：反查是哪个会话发起了这条命令，模型传的 --sender 只作对照。
# 由 Agent 执行（OPENCLAW_SHELL=exec）却查不到来源、或同时挂在多个飞书发送人名下，一律拒绝。
resolve_sender() {
  local res status resolved        # 局部变量，只在本函数内有效
  res="$(python3 "$ROOT/scripts/resolve-sender.py" "$cmd" "$@")"        # 拿整条命令去会话记录里反查，返回一行 JSON
  status="$(printf '%s' "$res" | python3 -c 'import json,sys; print(json.load(sys.stdin)["status"])')"        # 取出 status：feishu / local / ambiguous / notfound
  resolved="$(printf '%s' "$res" | python3 -c 'import json,sys; print(json.load(sys.stdin).get("sender",""))')"        # 取出网关记录的真实发送人 ou_
  mkdir -p "$ROOT/logs"        # 确保日志目录存在
  printf '%s\t%s\tgiven=%s\t%s\n' "$(date -Iseconds)" "$cmd" "${SENDER:-<空>}" "$res" >> "$ROOT/logs/gate-verify.log"        # 留痕：时间、命令、模型声称的身份、反查结果
  case "$status" in
    feishu)        # 飞书会话，查到了真实发送人
      if [ -n "$SENDER" ] && [ "${SENDER#*ou_}" != "${resolved#ou_}" ]; then        # 模型写了身份，且和网关记录对不上
        echo "注意：命令里的 --sender 与网关记录的发送人不一致，以网关记录为准。" >&2        # 只提示，不采信模型
      fi
      SENDER="$resolved"        # 关键一行：用网关记录覆盖模型写的身份
      ;;
    local)        # WebChat / CLI 等非飞书会话
      SENDER=""        # 置空，闸门会按"演示 / 本地"处理
      ;;
    ambiguous)        # 同一条命令同时出现在多个飞书发送人的会话里
      echo '{"allowed":false,"role":"unknown","reason":"同一命令同时来自多个飞书发送人，无法确定身份"}'
      exit 3        # 认不清是谁 → 拒绝
      ;;
    *)        # notfound：会话记录里找不到这条命令
      if [ "${OPENCLAW_SHELL:-}" = "exec" ]; then        # 网关的 exec 工具会设这个环境变量，说明是 Agent 在执行
        echo '{"allowed":false,"role":"unknown","reason":"会话记录里找不到这条命令的来源，无法确认身份"}'
        exit 3        # Agent 发的却查不到来源 → 拒绝
      fi
      ;;        # 不是 Agent 执行（人在终端手动跑），放过，交给后面的闸门判
  esac
}

require_hr_data() {        # 调闸门：不是 HR 就在这里结束整个脚本
  local out
  if ! out="$(bash "$ACCESS" check "$SENDER")"; then        # 闸门退出码非 0（即 3）就进入拒绝分支
    printf '%s\n' "$out"        # 把闸门给出的拒绝 JSON 原样输出，模型据此回复
    echo "拒绝：非 HR 不能查询个人敏感数据（花名册、HR 月报）。飞书仅 HR 可以；WebChat / CLI 不传 --sender。" >&2
    exit 3        # 3 = 被闸门拒绝，后面的真脚本不会执行
  fi
  GATE_ROLE="$(printf '%s' "$out" | python3 -c 'import json,sys; print(json.load(sys.stdin).get("role",""))')"        # hr 或 demo；放进查询 JSON，避免模型按飞书显示名改口
  export GATE_ROLE
}

cmd="${1:-}"        # 第一个词是子命令，如 payroll-query；没传就是空串
shift || true        # 扔掉第一个词，之后 "$@" 只剩子命令的参数；没参数时 shift 失败也不中断
case "$cmd" in        # 按子命令分流，只认下面四种
  ima-search)        # 政策问答（不涉个人数据，不过身份闸门）
    python3 "$ROOT/scripts/redline-check.py" "$@"        # 先做红线检查；因 set -e，这一步失败就不会往下检索
    exec node "$ROOT/skills/answering-hr-policy-questions/scripts/search_ima_policies.cjs" "$@"        # 再检索知识库；exec = 换成该程序运行，它的输出即结果
    ;;
  payroll-query)        # 花名册 / 薪资查询（敏感数据，三道关）
    extract_sender "$@"        # 第 1 关：取出模型声称的身份
    resolve_sender "$@"        # 第 2 关：按网关会话记录核实真实身份
    require_hr_data        # 第 3 关：比对 HR 名单，不是 HR 就 exit 3
    exec python3 "$ROOT/skills/querying-employee-payroll/scripts/query_payroll.py" "${FORWARD[@]+"${FORWARD[@]}"}"        # 三关都过才执行查询；只转交 FORWARD，--sender 不传下去
    ;;
  monthly-report)        # 对话里出月报，同样三道关
    extract_sender "$@"
    resolve_sender "$@"
    require_hr_data
    exec bash "$ROOT/skills/generating-monthly-report/scripts/run_monthly_report.sh" "${FORWARD[@]+"${FORWARD[@]}"}"
    ;;
  monthly-report-push)
    # 定时/演示推送入口：生成 + 回核，stdout 即飞书推送正文（取自 notify 脚本）
    extract_sender "$@"
    resolve_sender "$@"
    require_hr_data
    exec bash "$ROOT/skills/generating-monthly-report/scripts/notify_monthly_report.sh" "${FORWARD[@]+"${FORWARD[@]}"}"
    ;;
  *)        # 不认识的子命令：只打印用法，什么都不执行
    echo "usage: scripts/er-admin-run.sh ima-search <问题> | payroll-query [--sender ou_…] --name|--all | monthly-report|monthly-report-push [--sender ou_…] [args]" >&2
    echo "禁止用 exec 把政策写入 md /tmp 或其它路径。政策只检索、口头发。" >&2
    exit 2        # 2 = 命令写错，与"被拒绝(3)"区分开
    ;;
esac
