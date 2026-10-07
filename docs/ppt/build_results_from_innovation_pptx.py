#!/usr/bin/env python3
"""原项目创新四宫格页：只改二级导航和高标题，改为成果页。"""
from __future__ import annotations

from pathlib import Path

from pptx import Presentation
from pptx.util import Inches

import build_closing_pptx as closing
import build_opening_template_pptx as base


OUT = Path("/opt/openclaw-hr/docs/PPT准备/成果-流程建设结果页.pptx")
GREEN = closing.GREEN
PURPLE = closing.PURPLE


def build(prs: Presentation) -> None:
    slide = base.new_slide(prs)
    base.add_tech_background(slide)
    base.TOTAL = 4
    closing.closing_header(
        slide,
        1,
        0,
        "05  PHASE I DELIVERABLES",
        "一期成果：不是新名词，而是落到流程里的改造",
        "四类结果都能回到前面的系统结构、现场操作与结果证据",
    )
    closing.innovation_card(
        slide,
        Inches(0.48),
        Inches(2.4),
        "01",
        "场景建设",
        "从政策场景到HR业务",
        "将OPC的人机协作思路应用到HR部门，形成OPD项目方案；从6个模块、30多个岗位子项中规划一期范围。",
        base.CYAN,
    )
    closing.innovation_card(
        slide,
        Inches(6.43),
        Inches(2.4),
        "02",
        "架构建设",
        "集中调度，业务隔离",
        "Router统一接收任务，五个业务Agent按HR边界分工；不同入口、数据和工具交给对应模块，结果统一返回HR。",
        PURPLE,
    )
    closing.innovation_card(
        slide,
        Inches(0.48),
        Inches(4.43),
        "03",
        "机制建设",
        "非确定产出，可确定把关",
        "招聘脱敏与数字回核；入职暂停审批；培训按需生成与自检；绩效缺数据不聚合；行政校身份、无依据不回答。",
        base.ORANGE,
    )
    closing.innovation_card(
        slide,
        Inches(6.43),
        Inches(4.43),
        "04",
        "决策边界",
        "把“人在回路”落实到节点",
        "招聘不决定录用；入职不代审批；培训资料由讲师审核；绩效不定最终等级；行政个案与争议转人工。",
        GREEN,
    )
    base.rect(slide, Inches(0.48), Inches(6.5), Inches(11.85), Inches(0.3), base.NAVY_3, line=base.CYAN, radius=True)
    base.text(
        slide,
        Inches(0.68),
        Inches(6.5),
        Inches(11.45),
        Inches(0.3),
        "以上机制均已在前面的技能演示中通过实际操作验证，本页只总结，不重复讲解。",
        10.5,
        bold=True,
        color=base.CYAN,
        align=base.PP_ALIGN.CENTER,
        anchor=base.MSO_ANCHOR.MIDDLE,
    )
    base.add_notes(
        slide,
        "本页从项目创新改为成果补充。口播按建设结果讲，不称创新。"
        "四张卡片内容暂不改，只调整导航和标题。",
    )


def main() -> None:
    prs = Presentation(str(base.TEMPLATE))
    base.clear_slides(prs)
    prs.slide_width, prs.slide_height = base.W, base.H
    build(prs)
    prs.core_properties.title = "小慧 · 一期成果（原项目创新页改标）"
    prs.core_properties.subject = "仅改二级导航与介绍标题"
    prs.core_properties.author = "小慧项目团队"
    prs.save(str(OUT))
    print(f"wrote {OUT} slides={len(prs.slides)}")


if __name__ == "__main__":
    main()
