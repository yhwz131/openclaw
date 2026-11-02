#!/usr/bin/env bash
# ============================================================
# run_360_pipeline.sh — 360 反馈聚合一键脚本（三层 Pipeline）
# 用法：bash run_360_pipeline.sh <slug>
#   <slug> 是 feedback-360/source_feedback/ 下的实际目录名（如 yuangong1 / yuangong2）
# 示例：bash run_360_pipeline.sh yuangong1
#
# 三层：
#   1. 校验 + 机械聚合   → aggregated-data.json
#   2. LLM 综合分析      → aggregated-report.md（缺则自动生成）
#   3. HTML 看板         → report.html + Canvas 发布
#
# LLM API 自动发现顺序（找到即用）：
#   0. 主节点同款火山方舟（VOLCANO_DEEPSEEK_API_KEY；base https://ark.cn-beijing.volces.com/api/plan/v3，model deepseek-v4.1-flash）
#   1. 脚本同目录 llm-config.json / ~/.openclaw-hr/llm-config.json
#   2. 环境变量 LLM_API_BASE / LLM_API_KEY / LLM_MODEL
#   3. 常见 LLM 环境变量（OPENAI_API_KEY / SILICONFLOW_API_KEY / DASHSCOPE_API_KEY）
#   4. OpenClaw 配置文件
#   5. OpenClaw gateway http://127.0.0.1:18999
# ============================================================
set -euo pipefail

SLUG="${1:?用法: bash run_360_pipeline.sh <slug>}"
BASE_DIR="$(cd "$(dirname "$0")" && pwd)"
PERSON_DIR="${BASE_DIR}/feedback-360/source_feedback/${SLUG}"
CONFIG_FILE="${HOME}/.openclaw-hr/llm-config.json"

echo "============================================"
echo "  360 反馈聚合 Pipeline · ${SLUG}"
echo "============================================"

# ---------- 前置检查 ----------
if [ ! -d "$PERSON_DIR" ]; then
  echo "❌ 目录不存在: $PERSON_DIR"
  exit 1
fi

# ---------- LLM API 自动发现 ----------
echo ""
echo "▶ 第零层 · LLM API 自动发现..."

LLM_BASE=""
LLM_KEY=""
LLM_KEY_BACKUP="${LLM_API_KEY_BACKUP:-}"
LLM_MODEL=""
LLM_FOUND=0

# 0) 项目默认：火山方舟 deepseek-v4.1-flash（与主节点 volcengine provider 一致）
#    base/model 固定为主节点标准值，密钥取 env.sh 的 VOLCANO_DEEPSEEK_API_KEY，不落盘
#    备 key 取 VOLCANO_DEEPSEEK_API_KEY_BACKUP，主 key 报错时由 synthesize_report.py 切换
#    若外部显式设了 LLM_API_BASE / LLM_API_KEY / LLM_MODEL，则以显式值为准
if [ -n "${VOLCANO_DEEPSEEK_API_KEY:-}" ]; then
  LLM_BASE="${LLM_API_BASE:-https://ark.cn-beijing.volces.com/api/plan/v3}"
  LLM_KEY="${LLM_API_KEY:-$VOLCANO_DEEPSEEK_API_KEY}"
  LLM_KEY_BACKUP="${LLM_KEY_BACKUP:-${VOLCANO_DEEPSEEK_API_KEY_BACKUP:-}}"
  LLM_MODEL="${LLM_MODEL:-deepseek-v4.1-flash}"
  LLM_FOUND=1
  echo "   ✅ 使用主节点同款火山方舟配置（deepseek-v4.1-flash）"
fi

# 1) 配置文件：脚本同目录优先，再 ~/.openclaw-hr/
for CFG in "${BASE_DIR}/llm-config.json" "$CONFIG_FILE"; do
  [ -f "$CFG" ] || continue
  [ "$LLM_FOUND" -eq 1 ] && break
  LLM_BASE=$(python3 -c "import json; d=json.load(open('$CFG')); print(d.get('api_base',''))" 2>/dev/null || true)
  LLM_KEY=$(python3 -c "import json; d=json.load(open('$CFG')); print(d.get('api_key',''))" 2>/dev/null || true)
  LLM_KEY_BACKUP=$(python3 -c "import json; d=json.load(open('$CFG')); print(d.get('api_key_backup',''))" 2>/dev/null || true)
  LLM_MODEL=$(python3 -c "import json; d=json.load(open('$CFG')); print(d.get('model',''))" 2>/dev/null || true)
  if [ -n "$LLM_BASE" ] && [ -n "$LLM_KEY" ]; then
    LLM_FOUND=1
    echo "   ✅ 从 ${CFG} 读到配置"
  fi
done

# 2) 环境变量
if [ "$LLM_FOUND" -eq 0 ] && [ -n "${LLM_API_BASE:-}" ]; then
  LLM_BASE="$LLM_API_BASE"
  LLM_KEY="${LLM_API_KEY:-}"
  LLM_MODEL="${LLM_MODEL:-gpt-4o}"
  LLM_FOUND=1
  echo "   ✅ 从环境变量 LLM_API_BASE 读到配置"
fi
if [ "$LLM_FOUND" -eq 0 ] && [ -n "${OPENAI_API_KEY:-}" ]; then
  LLM_BASE="${OPENAI_API_BASE:-https://api.openai.com/v1}"
  LLM_KEY="$OPENAI_API_KEY"
  LLM_MODEL="${OPENAI_MODEL:-gpt-4o}"
  LLM_FOUND=1
  echo "   ✅ 从 OPENAI_API_KEY 读到配置"
fi
if [ "$LLM_FOUND" -eq 0 ] && [ -n "${SILICONFLOW_API_KEY:-}" ]; then
  LLM_BASE="${SILICONFLOW_API_BASE:-https://api.siliconflow.cn/v1}"
  LLM_KEY="$SILICONFLOW_API_KEY"
  LLM_MODEL="${SILICONFLOW_MODEL:-Qwen/Qwen3-8B}"
  LLM_FOUND=1
  echo "   ✅ 从 SILICONFLOW_API_KEY 读到配置"
fi
if [ "$LLM_FOUND" -eq 0 ] && [ -n "${DASHSCOPE_API_KEY:-}" ]; then
  LLM_BASE="https://dashscope.aliyuncs.com/compatible-mode/v1"
  LLM_KEY="$DASHSCOPE_API_KEY"
  LLM_MODEL="${DASHSCOPE_MODEL:-qwen-plus}"
  LLM_FOUND=1
  echo "   ✅ 从 DASHSCOPE_API_KEY 读到配置"
fi

# 3) OpenClaw 配置文件
if [ "$LLM_FOUND" -eq 0 ]; then
  for OC in "${HOME}/.openclaw/openclaw.json" "/opt/openclaw-hr/.openclaw-hr/openclaw.json"; do
    [ -f "$OC" ] || continue
    [ "$LLM_FOUND" -eq 1 ] && break
    EXTRACTED=$(python3 - "$OC" << 'PYEOF'
import json, sys, re
try:
    raw = open(sys.argv[1]).read()
    try:
        cfg = json.loads(raw)
    except json.JSONDecodeError:
        cfg = json.loads(re.sub(r'//[^\n]*', '', raw))
    def find(obj, keys):
        r = {}
        if isinstance(obj, dict):
            for k, v in obj.items():
                for t in keys:
                    if t in k.lower() and isinstance(v, str) and len(v) > 3:
                        r.setdefault(t, v)
                if isinstance(v, (dict, list)):
                    for sk, sv in find(v, keys).items():
                        r.setdefault(sk, sv)
        elif isinstance(obj, list):
            for i in obj:
                for sk, sv in find(i, keys).items():
                    r.setdefault(sk, sv)
        return r
    r = find(cfg, ['api_base','base_url','api_key','apikey','endpoint'])
    b = r.get('api_base') or r.get('base_url') or r.get('endpoint') or ''
    k = r.get('api_key') or r.get('apikey') or ''
    m = cfg.get('model','') if isinstance(cfg, dict) else ''
    if b and k:
        print(f"{b}|{k}|{m}")
except Exception:
    pass
PYEOF
)
    if [ -n "$EXTRACTED" ]; then
      LLM_BASE=$(echo "$EXTRACTED" | cut -d'|' -f1)
      LLM_KEY=$(echo "$EXTRACTED" | cut -d'|' -f2)
      LLM_MODEL=$(echo "$EXTRACTED" | cut -d'|' -f3)
      LLM_FOUND=1
      echo "   ✅ 从 ${OC} 挖到 LLM 配置"
    fi
  done
fi

# 4) OpenClaw gateway
if [ "$LLM_FOUND" -eq 0 ]; then
  GW="http://127.0.0.1:18999"
  if curl -s --connect-timeout 2 "$GW/health" >/dev/null 2>&1; then
    LLM_BASE="$GW"
    LLM_KEY="gateway"
    LLM_MODEL="${LLM_MODEL:-deepseek-v4.1-flash}"
    LLM_FOUND=1
    echo "   ✅ OpenClaw gateway 在跑，用它做推理"
  fi
fi

# 5) 都没有 → 生成模板引导
if [ "$LLM_FOUND" -eq 0 ]; then
  mkdir -p "${HOME}/.openclaw-hr"
  cat > "$CONFIG_FILE" << 'EOF'
{
  "api_base": "https://ark.cn-beijing.volces.com/api/plan/v3",
  "api_key": "REPLACE_WITH_VOLCANO_DEEPSEEK_API_KEY",
  "api_key_backup": "REPLACE_WITH_VOLCANO_DEEPSEEK_API_KEY_BACKUP",
  "model": "deepseek-v4.1-flash"
}
EOF
  echo "   ⚠️  未找到任何 LLM API 配置（含主节点火山方舟 deepseek-v4.1-flash）"
  echo "   已生成模板: ${CONFIG_FILE}"
  echo "   请填入你的 API key 后重新运行："
  echo "     vim ${CONFIG_FILE}"
  echo "     bash run_360_pipeline.sh ${SLUG}"
  exit 1
fi

# 6) 导出环境变量供 synthesize_report.py 使用
export LLM_API_BASE="$LLM_BASE"
export LLM_API_KEY="$LLM_KEY"
export LLM_API_KEY_BACKUP="${LLM_KEY_BACKUP:-}"
export LLM_MODEL="${LLM_MODEL:-deepseek-v4.1-flash}"
echo "   API: ${LLM_BASE}  Model: ${LLM_MODEL}"
if [ -n "${LLM_API_KEY_BACKUP:-}" ]; then
  echo "   备用 key 已就绪（主 key 报错时自动切换）"
fi

# ---------- 第一层：校验 + 机械聚合 ----------
echo ""
echo "▶ 第一层 · 校验反馈数据..."
python3 "${BASE_DIR}/skills/aggregating-360-feedback/scripts/check_feedback.py" "$PERSON_DIR"

echo ""
echo "▶ 第一层 · 机械聚合..."
python3 "${BASE_DIR}/skills/aggregating-360-feedback/scripts/aggregate.py" "$PERSON_DIR"

if [ ! -f "${PERSON_DIR}/aggregated-data.json" ]; then
  echo "❌ 聚合失败：未生成 aggregated-data.json"
  exit 1
fi
echo "✅ aggregated-data.json 已生成"

# ---------- 第二层：LLM 综合分析 ----------
echo ""
REPORT="${PERSON_DIR}/aggregated-report.md"
SYNTHESIZE="${BASE_DIR}/skills/aggregating-360-feedback/scripts/synthesize_report.py"

if [ -f "$REPORT" ] && [ -s "$REPORT" ]; then
  echo "▶ 第二层 · aggregated-report.md 已就绪，跳过生成"
else
  echo "▶ 第二层 · 缺 aggregated-report.md，自动调用 LLM 生成..."
  if ! python3 "$SYNTHESIZE" "$PERSON_DIR" --out "$REPORT"; then
    echo "❌ LLM 综合分析失败，请检查 API 配置后重新运行"
    exit 1
  fi
  if [ ! -f "$REPORT" ] || [ ! -s "$REPORT" ]; then
    echo "❌ LLM 生成失败：报告文件缺失或为空"
    exit 1
  fi
  echo "✅ aggregated-report.md 已生成"
fi

# ---------- 第三层：生成看板 ----------
echo ""
echo "▶ 第三层 · 生成 HTML 看板..."
bash "${BASE_DIR}/skills/generating-360-dashboard/scripts/build_dashboard.sh" \
  "$PERSON_DIR" --publish --force

echo ""
echo "============================================"
echo "  ✅ Pipeline 完成！"
echo "  综合分析: ${REPORT}"
echo "  看板地址: http://127.0.0.1:18790/__openclaw__/canvas/documents/feedback-360-${SLUG}/index.html"
echo "============================================"