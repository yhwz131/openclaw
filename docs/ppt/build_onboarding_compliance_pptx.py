#!/usr/bin/env python3
"""生成入职模块五页“机制 + 合规”增强版 PPT。"""
from __future__ import annotations

from pathlib import Path

from pptx import Presentation
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches

import build_onboarding_pptx as deck


OUT = Path("/opt/openclaw-hr/docs/PPT准备/入职模块技能演示-5页机制合规版.pptx")
TOTAL = 5


def mechanism_slide(prs: Presentation) -> None:
    slide = deck.base.new_slide(prs)
    deck.base.add_tech_background(slide)
    deck.header(
        slide,
        1,
        "03  ONBOARDING AGENT · STATE MODEL",
        "机制本质：把跨部门入职建模为受约束状态机",
        "不是让模型根据对话猜进度，而是读取真相源、校验条件、执行合法迁移",
    )

    deck.card(
        slide,
        Inches(0.48),
        Inches(2.42),
        Inches(3.2),
        Inches(2.64),
        "为什么不能只做任务清单",
        "状态分散在多个责任主体\n旧快照可能落后于 HCM\n审批通过 ≠ 部门准备完成\n提醒发出 ≠ 跟进已经完成",
        accent=deck.RED,
        fill=deck.RED_DARK,
        body_size=12.3,
    )

    deck.base.rect(slide, Inches(4.05), Inches(2.42), Inches(4.1), Inches(2.64), deck.base.NAVY_3, line=deck.base.CYAN, radius=True)
    deck.base.text(slide, Inches(4.28), Inches(2.57), Inches(3.64), Inches(0.3), "状态机如何运行", 13, bold=True, color=deck.base.CYAN, align=PP_ALIGN.CENTER)
    steps = [
        ("01", "读取三个真相源"),
        ("02", "校验前置条件"),
        ("03", "执行合法状态迁移"),
        ("04", "暂停 / 催办 / 归档"),
    ]
    for i, (num, label) in enumerate(steps):
        y = Inches(3.03 + i * 0.45)
        deck.base.rect(slide, Inches(4.34), y, Inches(3.52), Inches(0.34), deck.base.NAVY_2, line=deck.base.LINE, radius=True)
        deck.base.text(slide, Inches(4.47), y + Inches(0.04), Inches(0.34), Inches(0.2), num, 9.5, bold=True, color=deck.base.CYAN)
        deck.base.text(slide, Inches(4.89), y + Inches(0.03), Inches(2.72), Inches(0.22), label, 10.5, bold=True, color=deck.base.PALE)

    deck.card(
        slide,
        Inches(8.52),
        Inches(2.42),
        Inches(4.32),
        Inches(2.64),
        "四项技术约束",
        "真相源分离｜缺数据不补全\n守卫条件｜条件不足不迁移\n失败关闭｜异常不默认成功\n事件留痕｜每次变化可追溯",
        accent=deck.GREEN,
        fill=deck.GREEN_DARK,
        body_size=12.3,
    )

    deck.base.rect(slide, Inches(0.48), Inches(5.36), Inches(12.36), Inches(1.08), deck.base.NAVY_2, line=deck.base.LINE, radius=True)
    sources = [
        ("HCM", "员工 + 五节点", deck.base.CYAN),
        ("Lobster", "审批门 + token", deck.base.ORANGE),
        ("reviews.json", "7/30/60/90", deck.GREEN),
    ]
    for i, (name, body, accent) in enumerate(sources):
        x = Inches(0.83 + i * 4.0)
        deck.base.text(slide, x, Inches(5.58), Inches(1.62), Inches(0.26), name, 11.7, bold=True, color=accent)
        deck.base.text(slide, x + Inches(1.58), Inches(5.58), Inches(2.0), Inches(0.26), body, 10.8, color=deck.base.PALE)
    deck.base.text(
        slide,
        Inches(0.5),
        Inches(6.63),
        Inches(12.2),
        Inches(0.2),
        "同一个“完成”被拆成审批完成、业务准备完成和跟进完成，避免模型把不同状态混为一谈。",
        10,
        bold=True,
        color=deck.base.CYAN,
        align=PP_ALIGN.CENTER,
    )
    deck.base.add_notes(
        slide,
        "约1分钟。入职模块不是任务清单，而是一台受约束状态机。"
        "HCM、Lobster和reviews.json承担不同真相源，小慧不能用对话记忆补全缺失状态。"
        "每次事件先经过守卫条件，再执行合法迁移；外部系统或凭证异常时失败关闭。"
        "审批完成、业务准备完成和跟进完成被分别记录，所有迁移都有事件留痕。",
    )


def lobster_slide(
    prs: Presentation,
    page: int = 1,
    eyebrow: str = "03  LOBSTER · WORKFLOW ORCHESTRATION",
    title: str = "Lobster：把入职规则固化为可暂停、可恢复的工作流",
    subtitle: str = "模型理解任务，启动器统一调用，Lobster 控制顺序、审批暂停与条件执行",
) -> None:
    slide = deck.base.new_slide(prs)
    deck.base.add_tech_background(slide)
    deck.header(
        slide,
        page,
        eyebrow,
        title,
        subtitle,
    )

    layers = [
        ("01", "HR 自然语言", "提出入职任务", deck.base.CYAN),
        ("02", "入职 Skill", "判断调用时机", deck.base.CYAN),
        ("03", "run-onboarding.sh", "固定参数与路径", deck.base.ORANGE),
        ("04", "Lobster 引擎", "执行工作流定义", deck.GREEN),
    ]
    for i, (num, title, sub, accent) in enumerate(layers):
        x = Inches(0.48 + i * 3.08)
        deck.base.rect(slide, x, Inches(2.4), Inches(2.78), Inches(0.82), deck.base.NAVY_2, line=accent, radius=True)
        deck.base.text(slide, x + Inches(0.14), Inches(2.53), Inches(0.38), Inches(0.22), num, 9.5, bold=True, color=accent)
        deck.base.text(slide, x + Inches(0.5), Inches(2.48), Inches(2.06), Inches(0.28), title, 12.3, bold=True, color=deck.base.PALE)
        deck.base.text(slide, x + Inches(0.18), Inches(2.84), Inches(2.4), Inches(0.2), sub, 9.3, color=deck.base.MUTED, align=PP_ALIGN.CENTER)
        if i < 3:
            deck.connector(slide, x + Inches(2.78), Inches(2.81), x + Inches(3.02), Inches(2.81), accent, 1.0)

    deck.base.text(slide, Inches(0.48), Inches(3.46), Inches(1.36), Inches(0.24), "工作流节点", 10.5, bold=True, color=deck.base.MUTED)
    nodes = [
        ("prep", deck.base.CYAN),
        ("contract_gate", deck.base.ORANGE),
        ("account_gate", deck.base.ORANGE),
        ("buddy", deck.base.CYAN),
        ("complete", deck.GREEN),
    ]
    for i, (label, accent) in enumerate(nodes):
        x = Inches(1.7 + i * 2.18)
        deck.base.rect(slide, x, Inches(3.39), Inches(1.87), Inches(0.39), deck.base.NAVY_3, line=accent, radius=True)
        deck.base.text(slide, x, Inches(3.39), Inches(1.87), Inches(0.39), label, 10.2, bold=True, color=accent, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
        if i < 4:
            deck.connector(slide, x + Inches(1.87), Inches(3.59), x + Inches(2.12), Inches(3.59), deck.base.LINE, 0.9)

    deck.base.rect(slide, Inches(0.48), Inches(4.08), Inches(6.0), Inches(2.22), deck.CODE_BG, line=deck.base.LINE, radius=True)
    deck.base.text(slide, Inches(0.7), Inches(4.22), Inches(5.56), Inches(0.27), "hr-onboarding.lobster｜核心定义节选", 11.5, bold=True, color=deck.base.CYAN)
    code = (
        "- id: contract_gate\n"
        "  run: build-approval-prompt.py contract\n"
        "  approval: true          # 自动 halt\n\n"
        "- id: complete\n"
        "  when: contract.approved && account.approved"
    )
    deck.base.text(slide, Inches(0.7), Inches(4.61), Inches(5.54), Inches(1.46), code, 10.7, color=deck.base.PALE, font="Courier New", line_spacing=0.86)

    deck.card(
        slide,
        Inches(6.76),
        Inches(4.08),
        Inches(6.08),
        Inches(2.22),
        "项目对 Lobster 的二次封装",
        "start｜运行到第一道门并暂停\nresume｜凭当次 token 从暂停点恢复\n"
        "dry｜只预览执行计划\n候选人状态按 pinyin 隔离；token 回填 workflow.json\n"
        "approval 不替换参数 → 由 run 动态生成专属 prompt",
        accent=deck.GREEN,
        body_size=10.6,
    )

    deck.base.rect(slide, Inches(0.48), Inches(6.49), Inches(12.36), Inches(0.31), deck.base.NAVY_3, line=deck.base.CYAN, radius=True)
    deck.base.text(
        slide,
        Inches(0.68),
        Inches(6.49),
        Inches(11.96),
        Inches(0.31),
        "关键价值：流程状态不依赖模型记忆｜审批节点不能跳过｜暂停后无需重跑整条链路",
        10.3,
        bold=True,
        color=deck.base.CYAN,
        align=PP_ALIGN.CENTER,
        anchor=MSO_ANCHOR.MIDDLE,
    )
    deck.base.add_notes(
        slide,
        "约1分20秒。HR自然语言进入入职Skill，再由run-onboarding启动器调用Lobster。"
        "Lobster读取hr-onboarding.lobster，依次执行prep、合同门、账号门、Buddy和归档。"
        "run调用脚本，approval true触发halt，when限制后续节点。人做决定后使用当次resumeToken从暂停点恢复。"
        "项目还固定了CLI、路径和参数，按员工隔离状态并把token回填workflow.json。"
        "由于Lobster的approval字段不做参数模板替换，项目让run先生成含员工信息的JSON prompt，再触发审批暂停。"
        "因此Lobster不是页面上的流程图，而是真正控制流程能否继续的执行引擎。",
    )


def law_row(slide, y, law: str, requirement: str, risk: str, mechanism: str, accent) -> None:
    deck.base.rect(slide, Inches(0.48), y, Inches(12.36), Inches(1.17), deck.base.NAVY_2, line=deck.base.LINE, radius=True)
    deck.base.rect(slide, Inches(0.48), y, Inches(0.09), Inches(1.17), accent)
    deck.base.text(slide, Inches(0.72), y + Inches(0.14), Inches(2.18), Inches(0.32), law, 12.5, bold=True, color=accent)
    deck.base.text(slide, Inches(3.02), y + Inches(0.13), Inches(2.7), Inches(0.8), requirement, 10.7, color=deck.base.PALE)
    deck.base.text(slide, Inches(5.95), y + Inches(0.13), Inches(2.52), Inches(0.8), risk, 10.7, color=deck.base.PALE)
    deck.base.text(slide, Inches(8.72), y + Inches(0.13), Inches(3.82), Inches(0.8), mechanism, 10.7, bold=True, color=accent)


def compliance_slide(prs: Presentation) -> None:
    slide = deck.base.new_slide(prs)
    deck.base.add_tech_background(slide)
    deck.header(
        slide,
        2,
        "03  COMPLIANCE BY DESIGN",
        "合规不是页脚里的法规，而是流程中的控制点",
        "法律要求 → 业务风险 → 项目机制，每一项都能在后续现场操作中验证",
    )

    labels = [("法律依据", 0.72, 2.18), ("核心要求", 3.02, 2.7), ("入职风险", 5.95, 2.52), ("落地机制", 8.72, 3.82)]
    for label, x, w in labels:
        deck.base.text(slide, Inches(x), Inches(2.36), Inches(w), Inches(0.25), label, 10.5, bold=True, color=deck.base.MUTED)

    law_row(
        slide,
        Inches(2.72),
        "《个人信息保护法》\n第六条、第十三条",
        "目的明确、直接相关、\n最小范围；合同与依法\n实施HR管理的处理基础",
        "读取无关员工数据；\n整库复制给模型；\n旧快照冒充实时状态",
        "HCM 只 GET、按人按节点读取；\n本地快照仅供当次流程运行；\nHCM 不可用即停止",
        deck.base.CYAN,
    )
    law_row(
        slide,
        Inches(4.02),
        "《劳动合同法》\n第八条、第十条",
        "依法履行告知与如实\n说明义务；建立劳动关系\n应订立书面劳动合同",
        "合同尚未开始，系统却\n直接宣布已进入入职\n或已经完成",
        "合同节点作为启动守卫；\n合同正文进入人工审批门；\nAI 不代替责任人确认",
        deck.base.ORANGE,
    )
    law_row(
        slide,
        Inches(5.32),
        "现行《网络安全法》\n第二十三条",
        "采取安全保护措施，\n防止未经授权访问及\n数据泄露、窃取、篡改",
        "账号权限未经核准即\n开通，形成真实系统\n访问风险",
        "账号权限设置第二道人工门；\n材料不足不建议批准；\n拒绝后立即 cancelled",
        deck.GREEN,
    )

    deck.base.rect(slide, Inches(0.48), Inches(6.63), Inches(12.36), Inches(0.2), deck.base.NAVY_3, line=deck.base.LINE, radius=True)
    deck.base.text(
        slide,
        Inches(0.68),
        Inches(6.63),
        Inches(11.96),
        Inches(0.2),
        "准确口径：两道人工门是项目依据业务与法律风险设计的控制机制，并非法律条文原句。",
        8.8,
        bold=True,
        color=deck.base.CYAN,
        align=PP_ALIGN.CENTER,
        anchor=MSO_ANCHOR.MIDDLE,
    )
    deck.base.add_notes(
        slide,
        "约1分15秒。个人信息保护法第六条、第十三条对应最小必要和入职HR管理的数据处理边界，"
        "所以HCM只GET、按人按节点读取。劳动合同法第八条、第十条对应真实信息和书面劳动合同，"
        "所以合同节点成为启动守卫，并由HR主管审核。现行网络安全法第二十三条要求防止未经授权访问，"
        "所以账号权限设置第二道人工门。必须说明：两道门是项目的风险控制设计，不是法律原文规定。"
        "\n官方来源：https://www.cac.gov.cn/2021-08/20/c_1631050028355286.htm"
        "\nhttp://www.npc.gov.cn/zgrdw/npc/zt/qt/ldhtfsslzn/2010-03/02/content_1546876.htm"
        "\nhttps://www.cac.gov.cn/2025-12/29/c_1768735112911946.htm",
    )


def main() -> None:
    prs = Presentation()
    prs.slide_width, prs.slide_height = deck.base.W, deck.base.H
    deck.base.TOTAL = TOTAL
    lobster_slide(prs)
    compliance_slide(prs)
    deck.start_and_halt(prs, page=3)
    deck.gates_and_completion(prs, page=4)
    deck.query_and_dashboard(prs, page=5)
    prs.core_properties.title = "小慧 · 入职模块技能演示机制合规版"
    prs.core_properties.subject = "受约束状态机、合规控制点、人工审批与可追溯看板"
    prs.core_properties.author = "小慧项目团队"
    prs.save(str(OUT))
    print(f"wrote {OUT} slides={len(prs.slides)}")


if __name__ == "__main__":
    main()
