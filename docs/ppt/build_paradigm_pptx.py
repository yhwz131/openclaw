#!/usr/bin/env python3
"""生成“基于部门SOP的OPD开发范式”两页稿（调研钩子页已弃用）。"""
from __future__ import annotations

from pathlib import Path

from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches

import build_closing_pptx as closing
import build_opening_template_pptx as base


OUT = Path("/opt/openclaw-hr/docs/PPT准备/开发范式-部门SOP-OPD两页稿.pptx")
GREEN = base.RGBColor(0x26, 0xD0, 0x98)
PURPLE = base.RGBColor(0x8C, 0x7C, 0xFF)


def header(slide, nav: int, page: int, eyebrow: str, title: str, subtitle: str) -> None:
    base.TOTAL = 2
    base.add_navigation(slide, nav, page)
    base.add_title(slide, eyebrow, title, subtitle)


def research_slide(prs: Presentation) -> None:
    slide = base.new_slide(prs)
    base.add_tech_background(slide)
    header(
        slide,
        0,
        1,
        "01  RESEARCH FINDINGS",
        "HR部门调研：6大模块，30+业务子项",
        "从部门SOP出发，拆出事项清单，再决定一期做什么",
    )

    modules = [
        ("01", "招聘", ["JD撰写发布", "简历收发初筛", "人才画像比对", "面试调度纪要", "Offer制作跟进"]),
        ("02", "入职", ["合同与资料准备", "账号设备申请", "政策介绍", "入职培训", "试用期跟进"]),
        ("03", "培训发展", ["需求调研", "计划制定", "内容生成", "实施记录", "效果测评"]),
        ("04", "绩效管理", ["OKR/KPI设定", "周期评估", "360反馈", "面谈纪要", "改进跟踪"]),
        ("05", "薪酬福利", ["薪资核算", "调薪审批", "社保公积金", "个税申报", "离职结算"]),
        ("06", "员工关系与行政", ["会议与内部通知", "HR Helpdesk", "考勤异常", "档案管理", "数据看板"]),
    ]
    positions = [
        (Inches(0.48), Inches(2.02)),
        (Inches(4.73), Inches(2.02)),
        (Inches(8.98), Inches(2.02)),
        (Inches(0.48), Inches(4.08)),
        (Inches(4.73), Inches(4.08)),
        (Inches(8.98), Inches(4.08)),
    ]
    for (code, name, items), (x, y) in zip(modules, positions):
        accent = base.ORANGE if code == "05" else base.CYAN
        base.rect(slide, x, y, Inches(3.88), Inches(1.88), base.NAVY_2, line=base.LINE, radius=True, transparency=5)
        base.rect(slide, x, y, Inches(0.1), Inches(1.88), accent)
        base.text(slide, x + Inches(0.22), y + Inches(0.1), Inches(0.55), Inches(0.26), code, 10, bold=True, color=accent)
        base.text(slide, x + Inches(0.78), y + Inches(0.06), Inches(2.9), Inches(0.34), name, 14, bold=True)
        base.text(
            slide,
            x + Inches(0.22),
            y + Inches(0.46),
            Inches(3.46),
            Inches(1.28),
            "\n".join(f"· {item}" for item in items),
            12,
            color=base.PALE,
            line_spacing=0.82,
        )

    base.rect(slide, Inches(0.48), Inches(6.14), Inches(12.36), Inches(0.66), base.NAVY_3, line=base.CYAN, radius=True)
    base.text(
        slide,
        Inches(0.7),
        Inches(6.2),
        Inches(11.92),
        Inches(0.24),
        "部门事项按SOP拆出后，按同一套方法决定一期做什么",
        11,
        bold=True,
        color=base.CYAN,
    )
    base.text(
        slide,
        Inches(0.7),
        Inches(6.44),
        Inches(11.92),
        Inches(0.26),
        "这条路径，称为  基于部门SOP的OPD开发范式",
        14,
        bold=True,
        color=base.PALE,
    )
    base.add_notes(
        slide,
        "约40秒。先按部门SOP摊开六大模块、三十多项事项，说明一期范围不是按手头工具拼出来的。"
        "最后只点名：这条路径称为基于部门SOP的OPD开发范式。四步方法放到下一页再讲，本页不展开。",
    )


def step_card(slide, x, number: str, title: str, input_label: str, body: str, output: str, accent) -> None:
    base.rect(slide, x, Inches(2.84), Inches(2.94), Inches(2.78), base.NAVY_2, line=base.LINE, radius=True)
    base.rect(slide, x, Inches(2.84), Inches(2.94), Inches(0.08), accent)
    badge = slide.shapes.add_shape(MSO_SHAPE.OVAL, x + Inches(0.16), Inches(3.02), Inches(0.36), Inches(0.36))
    base.set_fill(badge, accent)
    badge.line.fill.background()
    base.text(
        slide,
        x + Inches(0.16),
        Inches(3.02),
        Inches(0.36),
        Inches(0.36),
        number,
        11,
        bold=True,
        color=base.NAVY,
        align=PP_ALIGN.CENTER,
        anchor=MSO_ANCHOR.MIDDLE,
    )
    base.text(slide, x + Inches(0.58), Inches(3.04), Inches(2.2), Inches(0.32), title, 14, bold=True)
    base.text(slide, x + Inches(0.16), Inches(3.46), Inches(2.62), Inches(0.22), input_label, 9.5, color=base.MUTED)
    base.text(slide, x + Inches(0.16), Inches(3.7), Inches(2.62), Inches(1.12), body, 11.2, color=base.PALE, line_spacing=0.9)
    base.rect(slide, x + Inches(0.16), Inches(5.16), Inches(2.62), Inches(0.3), base.NAVY_3, line=accent, radius=True)
    base.text(
        slide,
        x + Inches(0.16),
        Inches(5.16),
        Inches(2.62),
        Inches(0.3),
        output,
        10,
        bold=True,
        color=accent,
        align=PP_ALIGN.CENTER,
        anchor=MSO_ANCHOR.MIDDLE,
    )


def scheme_slide(prs: Presentation) -> None:
    slide = base.new_slide(prs)
    base.add_tech_background(slide)
    header(
        slide,
        1,
        1,
        "02  OPD PARADIGM",
        "基于部门SOP的OPD开发范式",
        "先看HR部门日常作业，再决定系统做什么、人做什么",
    )

    base.rect(slide, Inches(0.48), Inches(2.0), Inches(12.36), Inches(0.42), base.NAVY_3, line=base.CYAN, radius=True)
    base.text(
        slide,
        Inches(0.7),
        Inches(2.0),
        Inches(11.92),
        Inches(0.42),
        "一人部门：一个人调度数字员工处理重复事务，录用、批准、定级仍由人决定",
        13.5,
        bold=True,
        color=base.CYAN,
        align=PP_ALIGN.CENTER,
        anchor=MSO_ANCHOR.MIDDLE,
    )

    rows = [
        (
            "01",
            "能力盘点",
            "先问这个部门能交给系统办哪些事",
            "本项目用到：生成画像和培训稿、检索制度原文、走入职审批流、用脚本校验数字和权限、对接飞书与花名册。",
            base.CYAN,
        ),
        (
            "02",
            "业务分析",
            "按部门作业拆事项，标出人和系统各做哪一步",
            "对照6大模块、30余项后，一期做招聘、入职、培训、绩效、行政；录用、合同批准、绩效定级仍由人做。薪酬仍在原流程由人处理。",
            GREEN,
        ),
        (
            "03",
            "系统架构",
            "把事项合成专线，而不是一项功能一个入口",
            "1个总控只负责识别和分发；5条业务专线分开运行、互不派活。人面对的是小慧，不是五个分散的工具。",
            PURPLE,
        ),
        (
            "04",
            "开发计划",
            "按阶段验收，过不了检查点就停",
            "缺自评不聚合、无权限不读数、缺上游不生成。前面的技能演示，就是把这些检查点当场跑给评委看。",
            base.ORANGE,
        ),
    ]
    for i, (num, title, lead, body, accent) in enumerate(rows):
        y = Inches(2.54 + i * 0.9)
        base.rect(slide, Inches(0.48), y, Inches(12.36), Inches(0.82), base.NAVY_2, line=base.LINE, radius=True)
        base.rect(slide, Inches(0.48), y, Inches(0.1), Inches(0.82), accent)
        base.text(slide, Inches(0.72), y + Inches(0.08), Inches(0.5), Inches(0.28), num, 12, bold=True, color=accent)
        base.text(slide, Inches(1.22), y + Inches(0.06), Inches(3.35), Inches(0.3), title, 16, bold=True)
        base.text(slide, Inches(4.6), y + Inches(0.08), Inches(7.95), Inches(0.26), lead, 12, bold=True, color=accent)
        base.text(slide, Inches(1.22), y + Inches(0.4), Inches(11.3), Inches(0.32), body, 12.5, color=base.PALE)

    base.add_notes(
        slide,
        "约50秒。用HR把四步讲成人话，不报对位表、六要素、hooks、落盘物这些内部词。"
        "第一句先解释一人部门。然后按盘点、拆事项、合成专线、设检查点的顺序，每步都落到本项目已经演示过的事。"
        "薪酬只说仍由人在原流程处理，不在本页展开去向以外的解释。",
    )


def innovation_slide(prs: Presentation) -> None:
    slide = base.new_slide(prs)
    base.add_tech_background(slide)
    if not getattr(base, "COMPOSE_TOTAL", None):
        base.TOTAL = 4
    closing.closing_header(
        slide,
        2,
        1,
        "05  METHOD INNOVATION",
        "方法创新：基于部门SOP的OPD开发范式",
        "小慧是这套范式在HR部门跑通的一期实例，方法可迁移到其他部门",
    )

    base.rect(slide, Inches(0.48), Inches(2.4), Inches(7.55), Inches(3.92), base.NAVY_2, line=base.LINE, radius=True)
    base.text(slide, Inches(0.74), Inches(2.52), Inches(7.05), Inches(0.28), "四步路径｜从部门SOP到可运行系统", 14, bold=True, color=base.CYAN)
    rows = [
        ("01", "能力盘点", "本项目落到", "生成画像和培训稿、检索制度、入职审批流、脚本校验、飞书与花名册"),
        ("02", "业务分析", "本项目落到", "6模块30余项里，一期做五条业务；录用、批准、定级仍由人做"),
        ("03", "系统架构", "本项目落到", "1个总控只分发，5条专线分开跑，人只对小慧说话"),
        ("04", "开发计划", "本项目落到", "缺自评、无权限、缺上游就停止；技能演示就是这些检查点"),
    ]
    accents = [base.CYAN, GREEN, PURPLE, base.ORANGE]
    for i, ((num, title, out, body), accent) in enumerate(zip(rows, accents)):
        y = Inches(2.9 + i * 0.8)
        base.rect(slide, Inches(0.74), y, Inches(7.05), Inches(0.7), base.NAVY_3, line=base.LINE, radius=True)
        base.rect(slide, Inches(0.74), y, Inches(0.08), Inches(0.7), accent)
        base.text(slide, Inches(0.96), y + Inches(0.06), Inches(0.42), Inches(0.22), num, 11, bold=True, color=accent)
        base.text(slide, Inches(1.4), y + Inches(0.04), Inches(2.4), Inches(0.26), title, 13.5, bold=True)
        base.text(slide, Inches(3.9), y + Inches(0.06), Inches(1.5), Inches(0.22), out, 10.5, bold=True, color=accent)
        base.text(slide, Inches(1.4), y + Inches(0.34), Inches(6.1), Inches(0.26), body, 11.2, color=base.PALE)

    base.rect(slide, Inches(8.22), Inches(2.4), Inches(4.62), Inches(1.86), base.NAVY_2, line=base.CYAN, radius=True)
    base.text(slide, Inches(8.46), Inches(2.52), Inches(4.16), Inches(0.28), "HR部门一期实例", 13.5, bold=True, color=base.CYAN)
    base.text(
        slide,
        Inches(8.46),
        Inches(2.86),
        Inches(4.16),
        Inches(1.2),
        "1个协调Agent + 5个业务Agent\n招聘 · 入职 · 培训 · 绩效 · 行政\n前面技能演示，就是这套方法的验证。",
        12.5,
        color=base.PALE,
        line_spacing=1.02,
    )

    base.rect(slide, Inches(8.22), Inches(4.46), Inches(4.62), Inches(1.86), base.NAVY_2, line=GREEN, radius=True)
    base.text(slide, Inches(8.46), Inches(4.58), Inches(4.16), Inches(0.28), "可迁移到其他部门", 13.5, bold=True, color=GREEN)
    base.text(
        slide,
        Inches(8.46),
        Inches(4.92),
        Inches(4.16),
        Inches(1.2),
        "同一四步：换部门SOP，再盘点、分析、定架构、排计划。\n下一步用同一范式试点第二个部门。",
        12.5,
        color=base.PALE,
        line_spacing=1.02,
    )

    base.rect(slide, Inches(0.48), Inches(6.5), Inches(12.36), Inches(0.32), base.NAVY_3, line=base.CYAN, radius=True)
    base.text(
        slide,
        Inches(0.68),
        Inches(6.5),
        Inches(11.96),
        Inches(0.32),
        "小慧不是从工具反推出来的功能集合，而是部门SOP经四步方法落地后的一期数字员工。",
        12,
        bold=True,
        color=base.CYAN,
        align=PP_ALIGN.CENTER,
        anchor=MSO_ANCHOR.MIDDLE,
    )
    base.add_notes(
        slide,
        "约35秒。本页给方法命名。左侧用上一页已经讲过的四步，改成评委能对上的本项目结果。"
        "右侧只强调：HR是一期实例，同一方法可以换到其他部门。"
        "不要说国内首创，也不要把OPD讲成政策词。",
    )


def main() -> None:
    prs = Presentation(str(base.TEMPLATE))
    base.clear_slides(prs)
    prs.slide_width, prs.slide_height = base.W, base.H
    scheme_slide(prs)
    innovation_slide(prs)
    prs.core_properties.title = "小慧 · 基于部门SOP的OPD开发范式"
    prs.core_properties.subject = "开发范式两页稿（调研钩子页已弃用）"
    prs.core_properties.author = "小慧项目团队"
    prs.save(str(OUT))
    print(f"wrote {OUT} slides={len(prs.slides)}")


if __name__ == "__main__":
    main()
