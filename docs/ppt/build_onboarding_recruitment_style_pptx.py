#!/usr/bin/env python3
"""按招聘 Agent 的“全景—问题—机制—验证—闭环”结构生成入职 PPT。"""
from __future__ import annotations

from pathlib import Path

from pptx import Presentation
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches

import build_onboarding_compliance_pptx as compliance
import build_onboarding_pptx as deck


OUT = Path("/opt/openclaw-hr/docs/PPT准备/入职模块技能演示-5页招聘同构版.pptx")
PREVIEW = Path("/opt/openclaw-hr/docs/PPT准备/入职模块技能演示-5页招聘同构版-预览.png")
TOTAL = 5


def chain_box(slide, x, y, w, label: str, *, accent=deck.base.CYAN, hot=False) -> None:
    fill = deck.base.NAVY_3 if hot else deck.base.NAVY_2
    deck.base.rect(slide, x, y, w, Inches(0.46), fill, line=accent if hot else deck.base.LINE, radius=True)
    deck.base.text(
        slide,
        x,
        y,
        w,
        Inches(0.46),
        label,
        9.7,
        bold=hot,
        color=accent if hot else deck.base.PALE,
        align=PP_ALIGN.CENTER,
        anchor=MSO_ANCHOR.MIDDLE,
    )


def module_map(prs: Presentation) -> None:
    slide = deck.base.new_slide(prs)
    deck.base.add_tech_background(slide)
    deck.header(
        slide,
        1,
        "03  ONBOARDING AGENT · SKILL MAP",
        "入职 Agent：一条审批主链，三条支撑链",
        "四项 Skill 共享三类真相源，本场重点验证 Lobster 审批门和双重完成机制",
    )

    deck.base.text(slide, Inches(0.48), Inches(2.39), Inches(1.52), Inches(0.25), "主链｜入职审批", 11.7, bold=True, color=deck.base.CYAN)
    main = [
        ("HCM 校验", False),
        ("只读五节点", False),
        ("合同审批门", True),
        ("账号权限门", True),
        ("审批归档", False),
        ("双重完成校验", True),
        ("开通跟进", False),
    ]
    widths = [1.33, 1.42, 1.48, 1.48, 1.3, 1.55, 1.3]
    x = 2.05
    for i, ((label, hot), width) in enumerate(zip(main, widths)):
        chain_box(slide, Inches(x), Inches(2.31), Inches(width), label, accent=deck.base.ORANGE if i in (2, 3) else deck.base.CYAN, hot=hot)
        if i < len(main) - 1:
            deck.connector(slide, Inches(x + width), Inches(2.54), Inches(x + width + 0.13), Inches(2.54), deck.base.LINE, 0.8)
        x += width + 0.16

    support = [
        ("支撑链 A｜进度查询", "HCM + workflow.json + reviews.json", "当前卡点＋下一责任部门", deck.base.CYAN),
        ("支撑链 B｜试用期跟进", "五节点全绿 → 一次性 Cron", "7/30/60/90 到期提醒＋HR回填", deck.GREEN),
        ("支撑链 C｜入职看板", "三类状态汇总 → HTML → Canvas", "全员准备、审批与跟进总览", compliance.PURPLE if hasattr(compliance, "PURPLE") else deck.PURPLE),
    ]
    for i, (name, flow, result, accent) in enumerate(support):
        y = Inches(3.13 + i * 0.88)
        deck.base.rect(slide, Inches(0.48), y, Inches(12.36), Inches(0.67), deck.base.NAVY_2, line=deck.base.LINE, radius=True)
        deck.base.rect(slide, Inches(0.48), y, Inches(0.08), Inches(0.67), accent)
        deck.base.text(slide, Inches(0.72), y + Inches(0.13), Inches(2.18), Inches(0.27), name, 11.5, bold=True, color=accent)
        deck.base.text(slide, Inches(3.08), y + Inches(0.13), Inches(4.0), Inches(0.27), flow, 10.8, color=deck.base.PALE)
        deck.base.text(slide, Inches(7.42), y + Inches(0.13), Inches(5.0), Inches(0.27), result, 10.8, bold=True, color=accent, align=PP_ALIGN.RIGHT)

    deck.base.rect(slide, Inches(0.48), Inches(6.12), Inches(12.36), Inches(0.65), deck.base.NAVY_3, line=deck.base.CYAN, radius=True)
    deck.base.text(slide, Inches(0.72), Inches(6.25), Inches(11.88), Inches(0.3), "HCM 管业务事实｜Lobster 管审批状态｜reviews.json 管跟进｜小慧不补全、不代批", 11.5, bold=True, color=deck.base.CYAN, align=PP_ALIGN.CENTER)
    deck.base.add_notes(
        slide,
        "约1分钟。入职Agent由一条审批主链和三条支撑链组成。"
        "主链先核验HCM，再由Lobster依次控制合同门和账号权限门；两门通过后仍要做双重完成校验。"
        "三条支撑链分别负责自然语言查询、7/30/60/90跟进和全员看板。"
        "四条链共享同一原则：HCM管业务事实，Lobster管审批状态，本地表管跟进，小慧只读取、推进和提醒。",
    )


def issue_card(slide, x, y, title: str, problem: str, mechanism: str, law: str, accent) -> None:
    deck.base.rect(slide, x, y, Inches(5.92), Inches(1.76), deck.base.NAVY_2, line=deck.base.LINE, radius=True)
    deck.base.rect(slide, x, y, Inches(0.09), Inches(1.76), accent)
    deck.base.text(slide, x + Inches(0.2), y + Inches(0.13), Inches(5.5), Inches(0.29), title, 12.5, bold=True, color=accent)
    deck.base.text(slide, x + Inches(0.2), y + Inches(0.53), Inches(2.57), Inches(0.72), problem, 10.5, color=deck.base.PALE)
    deck.base.text(slide, x + Inches(2.88), y + Inches(0.53), Inches(2.82), Inches(0.72), mechanism, 10.5, bold=True, color=accent)
    deck.base.rect(slide, x + Inches(0.2), y + Inches(1.4), Inches(5.5), Inches(0.22), deck.base.NAVY_3, line=accent, radius=True)
    deck.base.text(slide, x + Inches(0.2), y + Inches(1.4), Inches(5.5), Inches(0.22), law, 8.5, color=accent, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)


def problems_and_mechanisms(prs: Presentation) -> None:
    slide = deck.base.new_slide(prs)
    deck.base.add_tech_background(slide)
    deck.header(
        slide,
        2,
        "03  PROBLEMS → MECHANISMS",
        "从四类开发问题，沉淀为四道流程约束",
        "法律不单独罗列，而是解释风险边界；机制必须能在后续现场操作中验证",
    )
    issue_card(
        slide,
        Inches(0.48),
        Inches(2.41),
        "问题 A｜把“应该完成”说成“已经完成”",
        "早期本地脚本模拟合同、设备、Buddy等部门产出，形成假进度。",
        "HCM 成为五节点唯一真相源；只 GET；不可用就失败关闭。",
        "《个人信息保护法》第六条、第十三条｜目的限定、最小必要",
        deck.base.CYAN,
    )
    issue_card(
        slide,
        Inches(6.42),
        Inches(2.41),
        "问题 B｜自然语言可能越过责任人",
        "一句“继续办理”可能混淆展示材料与代替审批，带来责任风险。",
        "Lobster 两道 approval 门强制 halt；正文原样；人决定后 resume。",
        "《劳动合同法》第八、十条｜现行《网络安全法》第二十三条",
        deck.base.ORANGE,
    )
    issue_card(
        slide,
        Inches(0.48),
        Inches(4.43),
        "问题 C｜多人多门容易恢复错状态",
        "只靠对话上下文，可能拿错员工、旧审批门或错误凭证继续。",
        "按 pinyin 隔离状态；每门新 token；approvalId 不可替代。",
        "工程控制｜状态隔离、一次性恢复凭证、事件留痕",
        deck.GREEN,
    )
    issue_card(
        slide,
        Inches(6.42),
        Inches(4.43),
        "问题 D｜审批完成被误认为业务完成",
        "两门通过时，账号、设备、Buddy或培训仍可能待办。",
        "审批与准备双阈值；五节点全绿才挂跟进；HR回填才完成。",
        "业务控制｜审批完成 ≠ 部门完成 ≠ 跟进完成",
        deck.PURPLE,
    )
    deck.base.text(slide, Inches(0.5), Inches(6.55), Inches(12.2), Inches(0.24), "本场重点验证：机制一 Lobster 人工审批门｜机制二 三类真相源与双重完成", 10.5, bold=True, color=deck.base.CYAN, align=PP_ALIGN.CENTER)
    deck.base.add_notes(
        slide,
        "约1分20秒。开发中发现四类问题：模拟部门产出、自然语言越权、多人状态混用、审批与业务完成混淆。"
        "对应形成HCM唯一真相源、Lobster人工门、按员工隔离token以及双重完成四项机制。"
        "法律只用于解释风险边界：个人信息保护法对应最小必要，劳动合同法对应合同事项，网络安全法对应未授权访问。"
        "两道门是项目基于这些风险设计的控制机制，不是法律条文原句。",
    )


def truth_and_reviews(prs: Presentation) -> None:
    slide = deck.base.new_slide(prs)
    deck.base.add_tech_background(slide)
    deck.header(
        slide,
        4,
        "03  MECHANISM 2 · DUAL THRESHOLD",
        "机制二：三路读取、双重完成，拦住状态“假成功”",
        "审批完成、部门准备完成和跟进完成分别判断，模型不能合并口径",
    )

    sources = [
        ("HCM", "花名册＋五节点", "只读 GET", deck.base.CYAN),
        ("Lobster", "审批门＋事件＋token", "halt / resume", deck.base.ORANGE),
        ("reviews.json", "7/30/60/90", "HR 回填", deck.GREEN),
    ]
    for i, (name, body, access, accent) in enumerate(sources):
        x = Inches(0.48 + i * 4.18)
        deck.card(slide, x, Inches(2.42), Inches(3.9), Inches(1.36), name, f"{body}\n权限：{access}", accent=accent, body_size=11.3)

    deck.base.text(slide, Inches(0.48), Inches(4.07), Inches(12.0), Inches(0.25), "双重完成门槛｜两项同时满足，才调用 sync-reviews-if-ready", 11.8, bold=True, color=deck.base.CYAN)
    deck.base.rect(slide, Inches(0.48), Inches(4.45), Inches(3.45), Inches(1.15), deck.base.NAVY_3, line=deck.base.ORANGE, radius=True)
    deck.base.text(slide, Inches(0.68), Inches(4.62), Inches(3.05), Inches(0.28), "Lobster 两门批准", 13.5, bold=True, color=deck.base.ORANGE, align=PP_ALIGN.CENTER)
    deck.base.text(slide, Inches(0.68), Inches(5.04), Inches(3.05), Inches(0.23), "workflow = complete", 10.5, color=deck.base.PALE, align=PP_ALIGN.CENTER)
    deck.base.text(slide, Inches(4.03), Inches(4.76), Inches(0.42), Inches(0.3), "＋", 20, bold=True, color=deck.base.PALE, align=PP_ALIGN.CENTER)
    deck.base.rect(slide, Inches(4.55), Inches(4.45), Inches(3.45), Inches(1.15), deck.base.NAVY_3, line=deck.base.CYAN, radius=True)
    deck.base.text(slide, Inches(4.75), Inches(4.62), Inches(3.05), Inches(0.28), "HCM 五节点全绿", 13.5, bold=True, color=deck.base.CYAN, align=PP_ALIGN.CENTER)
    deck.base.text(slide, Inches(4.75), Inches(5.04), Inches(3.05), Inches(0.23), "all nodes = completed", 10.5, color=deck.base.PALE, align=PP_ALIGN.CENTER)
    deck.base.text(slide, Inches(8.08), Inches(4.76), Inches(0.42), Inches(0.3), "→", 20, bold=True, color=deck.base.PALE, align=PP_ALIGN.CENTER)
    deck.base.rect(slide, Inches(8.62), Inches(4.45), Inches(4.22), Inches(1.15), deck.GREEN_DARK, line=deck.GREEN, radius=True)
    deck.base.text(slide, Inches(8.82), Inches(4.62), Inches(3.82), Inches(0.28), "开通 7 / 30 / 60 / 90", 13.5, bold=True, color=deck.GREEN, align=PP_ALIGN.CENTER)
    deck.base.text(slide, Inches(8.82), Inches(5.04), Inches(3.82), Inches(0.23), "注册一次性 Cron", 10.5, color=deck.base.PALE, align=PP_ALIGN.CENTER)

    deck.base.rect(slide, Inches(0.48), Inches(5.88), Inches(12.36), Inches(0.78), deck.base.NAVY_2, line=deck.GREEN, radius=True)
    deck.base.text(slide, Inches(0.72), Inches(6.02), Inches(2.1), Inches(0.25), "到期后的第二道边界", 10.5, bold=True, color=deck.GREEN)
    deck.base.text(slide, Inches(2.85), Inches(6.0), Inches(9.65), Inches(0.31), "Cron 只产生 needs_review → HR 完成真实沟通 → CLI record 后才标记完成", 11.5, bold=True, color=deck.base.PALE)
    deck.base.add_notes(
        slide,
        "约1分20秒。三类状态分别从HCM、Lobster和reviews.json读取。"
        "两道审批门通过只代表workflow complete；HCM五节点全绿才代表部门准备完成。"
        "两项同时满足后才调用sync-reviews-if-ready并注册一次性Cron。"
        "现场可展示任一节点未完成时脚本跳过挂载。到期后也只产生needs_review，HR回填后才完成。",
    )


def close_loop(prs: Presentation) -> None:
    slide = deck.base.new_slide(prs)
    deck.base.add_tech_background(slide)
    deck.header(
        slide,
        5,
        "03  ONBOARDING · CLOSED LOOP",
        "入职实操闭环：从真实状态到持续跟进",
        "现场证据对应每一道机制，不重复讲原理",
    )

    steps = ["HCM建档", "前置校验", "合同门暂停", "HR决定", "账号门暂停", "IT决定", "双阈值", "查询看板"]
    for i, label in enumerate(steps):
        x = Inches(0.48 + i * 1.54)
        hot = i in (2, 3, 4, 5, 6)
        deck.base.rect(slide, x, Inches(2.4), Inches(1.35), Inches(0.68), deck.base.NAVY_3 if hot else deck.base.NAVY_2, line=deck.base.ORANGE if i in (2, 4) else deck.base.CYAN if hot else deck.base.LINE, radius=True)
        deck.base.text(slide, x + Inches(0.1), Inches(2.49), Inches(0.28), Inches(0.2), f"{i+1:02}", 8.8, bold=True, color=deck.base.CYAN)
        deck.base.text(slide, x + Inches(0.12), Inches(2.76), Inches(1.11), Inches(0.2), label, 9.3, bold=True, color=deck.base.PALE, align=PP_ALIGN.CENTER)
        if i < len(steps) - 1:
            deck.connector(slide, x + Inches(1.35), Inches(2.74), x + Inches(1.49), Inches(2.74), deck.base.LINE, 0.7)

    deck.base.rect(slide, Inches(0.48), Inches(3.39), Inches(5.02), Inches(2.79), deck.base.NAVY_2, line=deck.base.LINE, radius=True)
    deck.base.text(slide, Inches(0.72), Inches(3.56), Inches(4.54), Inches(0.27), "机制加入前 → 机制加入后", 13, bold=True, color=deck.base.CYAN)
    pairs = [
        ("模拟部门产出", "五节点只读 HCM"),
        ("模型根据对话推进", "Lobster 强制 halt"),
        ("多人状态可能混用", "员工隔离＋每门新 token"),
        ("审批完成＝入职完成", "审批与准备双阈值"),
        ("提醒发出＝跟进完成", "HR 回填后才完成"),
    ]
    for i, (before, after) in enumerate(pairs):
        y = Inches(4.04 + i * 0.4)
        deck.base.text(slide, Inches(0.74), y, Inches(1.76), Inches(0.22), f"× {before}", 9.7, color=deck.RED)
        deck.base.text(slide, Inches(2.5), y, Inches(0.32), Inches(0.22), "→", 10.5, bold=True, color=deck.base.MUTED, align=PP_ALIGN.CENTER)
        deck.base.text(slide, Inches(2.88), y, Inches(2.34), Inches(0.22), f"✓ {after}", 9.7, bold=True, color=deck.GREEN)

    deck.base.rect(slide, Inches(5.78), Inches(3.39), Inches(7.06), Inches(2.79), deck.base.NAVY_2, line=deck.GREEN, radius=True)
    deck.base.text(slide, Inches(6.02), Inches(3.56), Inches(6.58), Inches(0.27), "真实证据｜workflow.json ＋ 入职看板", 13, bold=True, color=deck.GREEN)
    dashboard = deck.crop_dashboard()
    slide.shapes.add_picture(str(dashboard), Inches(6.02), Inches(3.97), width=Inches(4.35), height=Inches(1.72))
    events = "contract_gate  halted\ncontract_gate  approved\naccount_gate   halted\naccount_gate   approved\ncomplete       completed"
    deck.base.text(slide, Inches(10.55), Inches(4.0), Inches(2.03), Inches(1.58), events, 8.8, color=deck.base.PALE, font="Courier New", line_spacing=0.84)

    deck.base.rect(slide, Inches(0.48), Inches(6.39), Inches(12.36), Inches(0.4), deck.base.NAVY_3, line=deck.base.CYAN, radius=True)
    deck.base.text(slide, Inches(0.68), Inches(6.39), Inches(11.96), Inches(0.4), "状态来自真实系统｜流程由 Lobster 推进｜关键决定由人完成｜所有结果可以追溯", 11, bold=True, color=deck.base.CYAN, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    deck.base.add_notes(
        slide,
        "约50秒。按八个动作快速回顾，不再重复原理。"
        "左侧对比机制加入前后：从模拟状态变为HCM真相源，从模型推进变为Lobster强制暂停，"
        "从单一完成口径变为双阈值，从自动标记变为HR回填。"
        "右侧展示当前真实看板和workflow事件。收口：状态来自真实系统，流程由Lobster推进，关键决定由人完成。",
    )


def main() -> None:
    prs = Presentation()
    prs.slide_width, prs.slide_height = deck.base.W, deck.base.H
    deck.base.TOTAL = TOTAL
    module_map(prs)
    problems_and_mechanisms(prs)
    compliance.lobster_slide(
        prs,
        page=3,
        eyebrow="03  MECHANISM 1 · LOBSTER HITL",
        title="机制一：Lobster 把人工决策固化成不可跳过的节点",
        subtitle="现场验证 start → contract_gate halt → resume → account_gate halt",
    )
    truth_and_reviews(prs)
    close_loop(prs)
    prs.core_properties.title = "小慧 · 入职模块技能演示招聘同构版"
    prs.core_properties.subject = "模块全景、问题机制、Lobster审批、双重完成与闭环证据"
    prs.core_properties.author = "小慧项目团队"
    prs.save(str(OUT))
    print(f"wrote {OUT} slides={len(prs.slides)}")


if __name__ == "__main__":
    main()
