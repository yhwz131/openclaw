#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""synthesize_report.py — 360 反馈第二层 · LLM 综合分析

用途：aggregating-360-feedback Skill 第二层。读同目录 aggregated-data.json
      （第一层 aggregate.py 的机械聚合，唯一评分基准）+ 各单份反馈 JSON 的评语，
      调 LLM 读评语，把机械层的「疑似分歧」坐实为共识 / 分歧，给分歧归因与面谈建议，
      产出 aggregated-report.md。

设计原则（与 aggregate.py 一致）：
  - 分数确定性：评分概览表由本脚本用 aggregated-data.json 原样拼出，LLM 不碰任何
    数字，报告里的评分不允许漂移。
  - 判断交给 LLM：共识 / 分歧的综合判定、评语对照、归因假设、面谈建议由 LLM 写。
  - 结构可解析：落盘前按 generating-360-dashboard 的 parse_aggregated_report()
    同口径校验（五维度分节 + **判定：**/**分歧归因分析：** 标签）；不通过则带
    错误信息重试一次，仍失败则非零退出，不写坏文件。
  - 合规红线：不输出 S/A/B/C/D 绩效等级；评价人只出角色代号。

CLI：python3 synthesize_report.py <person_dir> [--out PATH]
       person_dir —— source_feedback/<slug>/，须含 aggregated-data.json
       --out      —— 缺省 <person_dir>/aggregated-report.md
环境变量（run_360_pipeline.sh 第零层会导出）：
       LLM_API_BASE / LLM_API_KEY / LLM_MODEL
       缺省回退：XIAOMI_API_KEY + 小米 mimo（token-plan-cn.xiaomimimo.com）
退出码：0 成功；1 数据/API/结构问题；2 用法错误
"""

import argparse
import json
import os
import re
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

DIMENSIONS = ["goal_achievement", "professional_skill",
              "collaboration", "responsibility", "growth"]
DIM_CN = {
    "goal_achievement": "目标达成", "professional_skill": "专业能力",
    "collaboration": "协作沟通", "responsibility": "责任心", "growth": "学习成长",
}
PERSPECTIVE_ORDER = ["manager", "peer", "report", "self"]
PERSPECTIVE_SHORT = {
    "manager": "上级（直接主管）", "peer": "平级",
    "report": "下属", "self": "自评",
}

SYSTEM_PROMPT = """你是资深 HRBP，正在为一场 360 度绩效反馈面谈准备**输入材料**。
你会拿到某员工一个考核周期内全部 360 反馈的结构化数据（各视角评分与逐维评语），
以及第一层脚本机械算出的视角平均分、极差与「疑似分歧」信号。

你的任务：通读全部评语，逐维度判断各方叙事究竟是「共识」还是「分歧」，
摆出各方说法、给出分歧归因假设与面谈建议。

硬规则：
1. 评分概览表由系统用脚本数据拼接，你**不要输出任何评分表格、不要重算或改写分数**。
2. 所有引文、事实只能来自给你的评语 JSON，可以压缩改写但不得编造人物、事件、数字。
3. 评价人一律用角色代号（领导1 / 同事1 / 下属1 / 自评），**禁止出现真实姓名**。
4. 极差 ≥ 1.0 的「疑似分歧」只是机械触发信号：若评语方向一致（如仅打分尺度不同），
   综合判定仍应是「共识」并说明理由；只有评语叙事实质对立才判「分歧」。
5. 分歧维度的归因是**供面谈验证的假设，不是结论**；措辞发展性、非评判式。
6. 本报告**绝不含 S/A/B/C/D 或任何形式的绩效等级、排序、淘汰/晋升建议**；
   报告定位是面谈与校准会的输入材料，定级由三级人工流程完成。
7. 全程中文，只输出 Markdown 正文，不要用 ``` 代码围栏包裹全文。

输出结构（标题文字必须照用）：

# {subject} · {period} 360 反馈综合分析（面谈输入材料）

> 一段话声明：本报告是供绩效面谈与校准会 review 的输入材料，不是绩效结论、不构成
> 任何绩效定级；全部评分以同目录 aggregated-data.json 为唯一基准；评价人使用角色代号。

- **评估对象**：{subject}（{subject_role}）
- **周期**：{period}
- **反馈份数**：{count_desc}

## 二、分维度分析

然后依次输出五节，顺序固定为：目标达成、专业能力、协作沟通、责任心、学习成长，
标题格式严格为 `### N. 维度名 —— 不超过20字的短语`，例如 `### 1. 目标达成 —— 各方叙事一致`。

每个维度一节：

- 判为**共识**的维度，正文第一行必须是：
  `**判定：**` 后接至少 30 字说明（各方评语为何方向一致；若属尺度差异要写明）。
  随后用 `**各方说法：**` 起头，逐条以 `- **别名（N 分）**：……` 引用各方评语要点，
  可再加 `**面谈提示：**` 一段。
- 判为**分歧**的维度，正文第一行必须是：
  `**分歧归因分析：**` 后接至少 30 字的归因概述。
  随后依次给出：
  `**各方说法：**`（- **别名（N 分）**：……，高分方与低分方都要摆全）
  `**归因假设（供面谈验证，非结论）：**`（编号列出 2-3 条）
  `**面谈建议：**`（编号列出 2-3 条具体、可操作的建议）

五节写完后，再给两个二级标题章节：

## 三、跨维度共同模式
（200-400 字：把多个维度串起来看，指出共同底色与共同的发展性话题；不得重复堆引文）

## 四、面谈建议路线
（按「先确认共识、再进入分歧」的顺序给一份面谈展开顺序，6 步以内）

注意：
- 加粗标签只能用上面规定的两个：共识维度用 `**判定：**`，分歧维度用
  `**分歧归因分析：**`；不要自造 `**归因分析：**` 等其它标签。
- 五节之外不要再出现包含维度名的 `###` 标题。
"""


def die(msg, code=1):
    print(f"❌ {msg}", file=sys.stderr)
    sys.exit(code)


def resolve_llm():
    base = (
        os.environ.get("LLM_API_BASE")
        or os.environ.get("LLM_BASE_URL")
        or "https://token-plan-cn.xiaomimimo.com/v1"
    ).rstrip("/")
    key = os.environ.get("LLM_API_KEY") or os.environ.get("XIAOMI_API_KEY") or ""
    model = os.environ.get("LLM_MODEL") or "mimo-v2.5-pro"
    if not key:
        die("未找到 LLM 密钥：请设置 LLM_API_KEY（或 XIAOMI_API_KEY）后重试。")
    return base + "/chat/completions", key, model


def load_context(person_dir: Path):
    agg_path = person_dir / "aggregated-data.json"
    if not agg_path.is_file():
        die(f"未找到聚合数据：{agg_path}\n请先运行第一层 aggregate.py。", 2)
    agg = json.loads(agg_path.read_text(encoding="utf-8"))

    # 单份反馈：优先按 aggregated-data.json 里 reviewers[].file 的映射读，
    # 映射缺失时退回目录扫描（跳过聚合产物与下划线临时文件）。
    feedback = {}
    for pkey, pdata in agg.get("perspectives", {}).items():
        for rev in pdata.get("reviewers", []):
            fname = rev.get("file")
            if not fname:
                continue
            fpath = person_dir / fname
            if fpath.is_file():
                try:
                    feedback[fname] = json.loads(fpath.read_text(encoding="utf-8"))
                except json.JSONDecodeError:
                    pass
    if not feedback:
        for fpath in sorted(person_dir.glob("*.json")):
            if fpath.name.startswith(("_", "aggregated-")):
                continue
            try:
                obj = json.loads(fpath.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                continue
            if obj.get("reviewer_relation") in PERSPECTIVE_ORDER:
                feedback[fpath.name] = obj
    if not feedback:
        die(f"{person_dir} 下没有可用的单份反馈 JSON（评语是综合分析的输入）。")
    return agg, feedback


def build_data_block(agg: dict, feedback: dict) -> str:
    lines = []
    lines.append(
        f"## 机械聚合数据（aggregated-data.json 原文，评分引用以此为准，禁止改动）\n"
    )
    lines.append(
        f"- 评估对象：{agg.get('subject', '')}"
        f"（{agg.get('subject_role', '')}）；周期：{agg.get('period', '')}"
    )
    dist = "、".join(
        f"{PERSPECTIVE_SHORT[k]}{agg['perspectives'][k]['count']} 份"
        for k in PERSPECTIVE_ORDER
        if k in agg.get("perspectives", {})
    )
    lines.append(
        f"- 反馈份数：共 {agg.get('total_feedback_count', '')} 份 —— {dist}"
    )

    lines.append("\n### 各视角逐维度平均分")
    header = "| 维度 | " + " | ".join(
        PERSPECTIVE_SHORT[k] for k in PERSPECTIVE_ORDER
        if k in agg.get("perspectives", {})
    ) + " | 全体平均 | 视角极差 | 机械信号 |"
    lines.append(header)
    present = [k for k in PERSPECTIVE_ORDER if k in agg.get("perspectives", {})]
    # 列数 = 维度1 + 视角N + 全体平均/视角极差/机械信号3
    lines.append("|" + "---|" * (4 + len(present)))
    for dk in DIMENSIONS:
        cells = [DIM_CN[dk]]
        for pk in present:
            cells.append(f"{agg['perspectives'][pk]['dimensions'][dk]['average']:.2f}")
        ov = agg["overall"][dk]
        dv = agg["divergence"][dk]
        cells.append(f"{ov['average']:.2f}")
        cells.append(f"{dv['perspective_range']:.2f}")
        cells.append("疑似分歧" if dv["suspected_split"] else "共识")
        lines.append("| " + " | ".join(cells) + " |")

    lines.append("\n### 每份反馈的评分与评语")
    for pk in PERSPECTIVE_ORDER:
        pdata = agg.get("perspectives", {}).get(pk)
        if not pdata:
            continue
        lines.append(f"\n【视角：{pdata.get('label', PERSPECTIVE_SHORT[pk])}】")
        for rev in pdata.get("reviewers", []):
            obj = feedback.get(rev.get("file", ""))
            if not obj:
                continue
            alias = obj.get("reviewer_alias") or rev.get("alias")
            scores = obj.get("scores", {})
            score_str = "，".join(
                f"{DIM_CN[dk]}{scores.get(dk, '?')}" for dk in DIMENSIONS
            )
            lines.append(f"\n- {alias}（评分：{score_str}）")
            comments = obj.get("comments", {})
            for dk in DIMENSIONS:
                text = (comments.get(dk) or "").strip()
                if text:
                    lines.append(f"  · {DIM_CN[dk]}评语：{text}")
            if obj.get("strengths"):
                lines.append(f"  · 总体亮点：{obj['strengths'].strip()}")
            if obj.get("improvements"):
                lines.append(f"  · 改进建议：{obj['improvements'].strip()}")
    return "\n".join(lines)


def call_llm(url, key, model, system_prompt, user_prompt, timeout=300):
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.3,
        "max_tokens": 8000,
    }
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }
    data = json.dumps(payload).encode("utf-8")

    last_err = None
    for attempt in (1, 2):
        try:
            req = urllib.request.Request(
                url, data=data, headers=headers, method="POST"
            )
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                body = json.loads(resp.read().decode("utf-8"))
            return body["choices"][0]["message"]["content"].strip()
        except urllib.error.HTTPError as e:
            snippet = e.read().decode("utf-8", "replace")[:500]
            last_err = f"HTTP {e.code}：{snippet}"
            if 400 <= e.code < 500:
                die(f"LLM API 请求被拒（{last_err}）\n请检查 LLM_API_KEY / 模型名 / API base。")
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, KeyError) as e:
            last_err = f"{type(e).__name__}: {e}"
        if attempt == 1:
            print("   …首次请求失败，3 秒后重试一次", file=sys.stderr)
            time.sleep(3)
    die(f"LLM API 两次请求均失败：{last_err}")


SECTION_RE = re.compile(
    r"^###\s+(?:\d+\.\s*)?"
    r"(目标达成|专业能力|协作沟通|责任心|学习成长)"
    r"(?:\s*[（(][^）)\n]*[）)])?"
    r"(?:\s*[—\-–]+\s*(.+?))?\s*$",
    re.M,
)
LABEL_RE = re.compile(r"\*\*(判定|分歧归因分析|归因分析)[：:]?\*\*[：:]*\s*")


def validate_sections(md: str):
    """只校验 LLM 负责的叙事部分；评分表由脚本拼接、不需模型产出。

    返回 (verdicts, errors)。verdicts: dim_key -> 'consensus'|'split'。
    """
    matches = list(SECTION_RE.finditer(md))
    errors = []
    found = [m.group(1) for m in matches]
    if found != [DIM_CN[d] for d in DIMENSIONS]:
        errors.append(
            "五维度分节缺失或顺序/标题不符，应为 ### 1.~5. 且标题严格形如"
            "「### 1. 目标达成 —— 短语」；实际匹配到："
            + ("、".join(found) if found else "无")
        )
        return {}, errors

    verdicts = {}
    for i, m in enumerate(matches):
        cn = m.group(1)
        dk = next(k for k, v in DIM_CN.items() if v == cn)
        block = md[m.end():matches[i + 1].start()] if i + 1 < len(matches) \
            else md[m.end():]
        lab = LABEL_RE.search(block)
        if not lab:
            errors.append(f"「{cn}」节缺少加粗标签 **判定：** 或 **分歧归因分析：**")
            continue
        label = lab.group(1)
        if label == "归因分析":
            errors.append(f"「{cn}」节用了不允许的 **归因分析：**，请按规则改用"
                          "**判定：**（共识）或 **分歧归因分析：**（分歧）")
            continue
        tail = block[lab.end():].strip()
        tail = re.sub(r"\s+", "", tail)
        if len(tail) < 8:
            errors.append(f"「{cn}」节 {label} 后的说明不足 8 个字")
            continue
        verdicts[dk] = "split" if label == "分歧归因分析" else "consensus"

    if not re.search(r"^#\s+\S+", md, re.M):
        errors.append("缺少报告一级标题（# 评估对象 · 周期 …）")
    if not re.search(r"^##\s+二、分维度分析", md, re.M):
        errors.append("缺少「## 二、分维度分析」章节标题")
    return verdicts, errors


def strip_fences(md: str) -> str:
    md = md.strip()
    if md.startswith("```"):
        md = re.sub(r"^```[a-zA-Z]*\n", "", md)
        md = re.sub(r"\n```\s*$", "", md)
    return md.strip() + "\n"


def build_overview_table(agg: dict, verdicts: dict) -> str:
    present = [k for k in PERSPECTIVE_ORDER if k in agg.get("perspectives", {})]
    out = ["## 一、评分概览（取自 aggregated-data.json，视角平均分）", ""]
    out.append(
        "| 维度 | " + " | ".join(PERSPECTIVE_SHORT[k] for k in present)
        + " | 全体平均 | 视角极差 | 机械信号 | 综合判定 |"
    )
    # 列数 = 维度1 + 视角N + 全体平均/视角极差/机械信号/综合判定4
    out.append("|" + "---|" * (5 + len(present)))
    for dk in DIMENSIONS:
        cells = [DIM_CN[dk]]
        for pk in present:
            cells.append(f"{agg['perspectives'][pk]['dimensions'][dk]['average']:.2f}")
        ov = agg["overall"][dk]
        dv = agg["divergence"][dk]
        cells.append(f"{ov['average']:.2f}")
        cells.append(f"{dv['perspective_range']:.2f}")
        cells.append("疑似分歧" if dv["suspected_split"] else "共识")
        cells.append("分歧" if verdicts.get(dk) == "split" else "共识")
        out.append("| " + " | ".join(cells) + " |")
    out.append("")
    out.append(
        "> 视角平均分极差 ≥ 1.0 只是「触发关注」的机械信号；"
        "「综合判定」是通读全部评语后得出的结论——评分尺度差异但叙事一致的，"
        "仍判共识。所有分数以同目录 `aggregated-data.json` 为唯一基准。"
    )
    out.append("")
    return "\n".join(out)


def assemble_report(md: str, agg: dict, verdicts: dict) -> str:
    table = build_overview_table(agg, verdicts)

    # 若模型自行输出了「评分概览/总览」类第一节，整体替换；否则插到「二、」之前。
    h2_iter = list(re.finditer(r"^##\s+.+$", md, re.M))
    first_h2 = h2_iter[0] if h2_iter else None
    second_h2 = next(
        (h for h in h2_iter if re.match(r"^##\s*二、", h.group(0))), None
    )
    if first_h2 and ("评分概览" in first_h2.group(0) or "总览" in first_h2.group(0)):
        end = second_h2.start() if second_h2 else (
            h2_iter[1].start() if len(h2_iter) > 1 else len(md)
        )
        md = md[:first_h2.start()] + table + "\n" + md[end:]
    elif second_h2:
        md = md[:second_h2.start()] + table + "\n" + md[second_h2.start():]
    else:
        die("内部错误：已通过分节校验却找不到插入评分概览的位置。")

    subject = agg.get("subject", "被评估人")
    if "绩效定级" not in md or "三级人工" not in md:
        md = md.rstrip() + "\n\n---\n\n" + (
            "> **结尾声明**：本报告仅聚合多方反馈并区分共识与分歧，"
            "所有归因均为供面谈验证的假设，最终结论由直接主管在绩效面谈中与"
            f"{subject}对齐后，进入「直接主管初评 → 隔级主管复核 → 校准会确认」"
            "三级人工流程。本报告不含、也不得被引用为任何绩效等级评定；"
            "全部评分以同目录 `aggregated-data.json` 为唯一基准。\n"
        )
    return md


def atomic_write(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(
        prefix=".aggregated-report.", suffix=".md", dir=str(path.parent)
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(content)
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def main():
    ap = argparse.ArgumentParser(
        description="360 反馈第二层：LLM 综合分析 → aggregated-report.md"
    )
    ap.add_argument("person_dir", help="含 aggregated-data.json 的人员目录")
    ap.add_argument("--out", help="输出路径（缺省 <person_dir>/aggregated-report.md）")
    args = ap.parse_args()

    person_dir = Path(args.person_dir).resolve()
    if not person_dir.is_dir():
        die(f"目录不存在: {person_dir}", 2)
    out_path = Path(args.out).resolve() if args.out \
        else person_dir / "aggregated-report.md"

    agg, feedback = load_context(person_dir)
    url, key, model = resolve_llm()

    print(f"   LLM: {url}  model={model}")
    dist = "、".join(
        f"{PERSPECTIVE_SHORT[k]}{agg['perspectives'][k]['count']}份"
        for k in PERSPECTIVE_ORDER if k in agg.get("perspectives", {})
    )
    system_prompt = SYSTEM_PROMPT.format(
        subject=agg.get("subject", "被评估人"),
        subject_role=agg.get("subject_role", ""),
        period=agg.get("period", ""),
        count_desc=f"{agg.get('total_feedback_count', '')} 份（{dist}）",
    )

    user_prompt = (
        "请依据下面的数据完成 360 反馈综合分析报告。"
        "再次提醒：不要输出评分表格（评分概览由系统拼接），"
        "五维度分节标题与加粗标签必须严格按规则书写。\n\n"
        + build_data_block(agg, feedback)
    )

    verdicts, errors = {}, []
    md = ""
    for attempt in (1, 2):
        print(f"   第 {attempt} 次请求 LLM 生成综合分析…", file=sys.stderr)
        prompt = user_prompt
        if attempt == 2 and errors:
            prompt += (
                "\n\n你上一版输出未通过结构校验，请只修正以下问题后重新输出"
                "完整 Markdown（其余内容保留）：\n- "
                + "\n- ".join(errors)
            )
        md = strip_fences(call_llm(url, key, model, system_prompt, prompt))
        verdicts, errors = validate_sections(md)
        if not errors:
            break
        print("   结构校验未通过：" + "；".join(errors), file=sys.stderr)

    if errors:
        die("LLM 两次生成均未通过结构校验（五维度分节/判定标签不合规），"
            "未写入报告。问题：" + "；".join(errors))

    report = assemble_report(md, agg, verdicts)
    atomic_write(out_path, report)

    verdict_cn = {k: ("分歧" if v == "split" else "共识") for k, v in verdicts.items()}
    print(
        "✅ 综合分析完成："
        + "，".join(f"{DIM_CN[k]}{verdict_cn[k]}" for k in DIMENSIONS if k in verdict_cn)
    )
    print(f"   报告已写入: {out_path}")


if __name__ == "__main__":
    main()
