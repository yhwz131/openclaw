#!/usr/bin/env python3
"""项目背景里的亮点页：模型写不稳，所以脚本核、人来定。单独成稿。"""
from __future__ import annotations

from pathlib import Path

from pptx import Presentation
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches

import build_opening_template_pptx as base


OUT = Path("/opt/openclaw-hr/docs/PPT准备/小慧-亮点页.pptx")


def build(prs: Presentation) -> None:
    slide = base.new_slide(prs)
    base.add_tech_background(slide)
    base.TOTAL = 27
    base.add_navigation(slide, 0, 5)
    base.add_title(
        slide,
        "01  PROJECT BACKGROUND",
        "让模型去写，让脚本去核，让人去定",
        "用确定的脚本，框住不确定的生成；把会影响人的决定，交还给人",
    )

    cards = [
        (
            "01",
            "模型：能写，也会错",
            "读得懂简历，写得出评语，\n也会把岗位里的数字\n安到候选人头上。\n写得越快，越需要有人把关。",
        ),
        (
            "02",
            "脚本：不认说法，只认原件",
            "数字对原简历，\n回答对制度原文，\n查询先对权限。\n对不上就拦下，模型改不了。",
        ),
        (
            "03",
            "人：关键一步，亲自拍板",
            "录用、合同、账号、争议，\n关系到一个人的去留和权益。\n小慧递材料、给建议，\n签字的始终是人。",
        ),
    ]
    for i, (num, title, body) in enumerate(cards):
        x = Inches(0.42 + i * 4.22)
        base.rect(slide, x, Inches(2.16), Inches(4.04), Inches(3.98), base.NAVY_2, line=base.LINE, radius=True)
        base.rect(slide, x, Inches(2.16), Inches(0.08), Inches(3.98), base.CYAN)
        base.text(slide, x + Inches(0.28), Inches(2.34), Inches(3.5), Inches(0.34), num, 15, bold=True, color=base.CYAN)
        base.text(slide, x + Inches(0.28), Inches(2.76), Inches(3.62), Inches(0.5), title, 19, bold=True)
        base.text(
            slide,
            x + Inches(0.28),
            Inches(3.48),
            Inches(3.56),
            Inches(2.5),
            body,
            15.5,
            color=base.PALE,
            line_spacing=1.2,
        )

    base.rect(slide, Inches(0.42), Inches(6.3), Inches(12.48), Inches(0.56), base.NAVY_3, line=base.CYAN, radius=True)
    base.text(
        slide,
        Inches(0.42),
        Inches(6.3),
        Inches(12.48),
        Inches(0.56),
        "写得快  ·  核得准  ·  定得稳",
        18,
        bold=True,
        color=base.CYAN,
        align=PP_ALIGN.CENTER,
        anchor=MSO_ANCHOR.MIDDLE,
    )

    base.add_notes(
        slide,
        "约40秒。先念标题：让模型去写，让脚本去核，让人去定。"
        "第一格是原因：模型读得懂、写得快，但也会把岗位里的数字安到候选人头上。"
        "所以第二格，脚本不认说法只认原件，对不上就拦下，模型改不了。"
        "第三格，录用、合同、账号、争议关系到人，签字的始终是人。"
        "最后一句收住：写得快，核得准，定得稳。"
        "本页不展开具体演示，后面技能段逐个兑现。",
    )


def main() -> None:
    prs = Presentation(str(base.TEMPLATE))
    base.clear_slides(prs)
    prs.slide_width, prs.slide_height = base.W, base.H
    build(prs)
    prs.core_properties.title = "让模型去写，让脚本去核，让人去定"
    prs.core_properties.subject = "亮点页：三条设计"
    prs.core_properties.author = "小慧项目团队"
    prs.save(str(OUT))
    print(f"wrote {OUT} slides={len(prs.slides)}")


if __name__ == "__main__":
    main()
