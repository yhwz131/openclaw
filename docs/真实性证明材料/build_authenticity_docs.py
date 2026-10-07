#!/usr/bin/env python3
"""生成小慧项目真实性证明材料（DOCX）。黄底【】为待双方填写项。"""
from __future__ import annotations

import re
from pathlib import Path

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT

OUT = Path("/opt/openclaw-hr/docs/真实性证明材料")
PLACE = re.compile(r"(【[^】]+】)")

NAVY = RGBColor(0x1F, 0x4E, 0x79)
BLACK = RGBColor(0x00, 0x00, 0x00)
GRAY = RGBColor(0x59, 0x59, 0x59)
HEADER_BG = "1F4E79"
HEADER_FG = RGBColor(0xFF, 0xFF, 0xFF)

SCHOOL = "云南水利水电职业学院"
SCHOOL_CAMPUS = "云南省昆明市富民县永定街道翠屏路（富民校区）"
SCHOOL_REG_ADDR = "昆明市盘龙区兰黑路13号（蓝龙潭校区）"
COMPANY = "重庆足下科技有限公司"
PROJECT = "小慧人力资源数字员工系统"
PROJECT_SHORT = "小慧"
VERSION = "V1.0"


def shade_cell(cell, hex_color: str) -> None:
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:fill"), hex_color)
    shd.set(qn("w:val"), "clear")
    tcPr.append(shd)


def set_run_font(run, ea="宋体", size=12, bold=False, color=BLACK, west="Times New Roman"):
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = color
    run.font.name = west
    rPr = run._element.get_or_add_rPr()
    rFonts = rPr.find(qn("w:rFonts"))
    if rFonts is None:
        rFonts = OxmlElement("w:rFonts")
        rPr.insert(0, rFonts)
    rFonts.set(qn("w:ascii"), west)
    rFonts.set(qn("w:hAnsi"), west)
    rFonts.set(qn("w:eastAsia"), ea)
    rFonts.set(qn("w:cs"), west)


def highlight_run(run) -> None:
    rPr = run._element.get_or_add_rPr()
    hl = OxmlElement("w:highlight")
    hl.set(qn("w:val"), "yellow")
    rPr.append(hl)


def add_mixed(p, text, *, ea="仿宋", size=12, bold=False, color=BLACK, space_after=6, first_line=True, align=None, line=28):
    if align is not None:
        p.alignment = align
    pf = p.paragraph_format
    pf.space_before = Pt(0)
    pf.space_after = Pt(space_after)
    pf.line_spacing = Pt(line)
    pf.line_spacing_rule = WD_LINE_SPACING.EXACTLY
    if first_line:
        pf.first_line_indent = Pt(size * 2)
    else:
        pf.first_line_indent = Pt(0)
    for part in PLACE.split(text):
        if not part:
            continue
        run = p.add_run(part)
        set_run_font(run, ea, size, bold, color)
        if part.startswith("【") and part.endswith("】"):
            highlight_run(run)
    return p


def p(doc, text, **kw):
    return add_mixed(doc.add_paragraph(), text, **kw)


def h(doc, text, level=1):
    para = doc.add_paragraph()
    para.alignment = WD_ALIGN_PARAGRAPH.LEFT
    pf = para.paragraph_format
    pf.space_before = Pt(14 if level == 1 else 10)
    pf.space_after = Pt(8)
    pf.line_spacing = Pt(28)
    pf.first_line_indent = Pt(0)
    sizes = {0: 16, 1: 16, 2: 14, 3: 12}
    run = para.add_run(text)
    set_run_font(run, "黑体", sizes.get(level, 14), True, NAVY if level <= 2 else BLACK)
    return para


def center(doc, text, *, ea="黑体", size=16, bold=True, space_before=0, space_after=8, color=BLACK):
    para = doc.add_paragraph()
    para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    pf = para.paragraph_format
    pf.space_before = Pt(space_before)
    pf.space_after = Pt(space_after)
    pf.line_spacing = 1.15
    pf.first_line_indent = Pt(0)
    add_mixed(para, text, ea=ea, size=size, bold=bold, color=color, space_after=0, first_line=False, line=22)
    return para


def right(doc, text, size=12, ea="仿宋"):
    para = doc.add_paragraph()
    para.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    pf = para.paragraph_format
    pf.space_after = Pt(2)
    pf.first_line_indent = Pt(0)
    add_mixed(para, text, ea=ea, size=size, bold=False, space_after=0, first_line=False, line=22)
    return para


def spacer(doc, pt=8):
    para = doc.add_paragraph()
    para.paragraph_format.space_after = Pt(pt)
    para.paragraph_format.space_before = Pt(0)
    return para


def set_header_footer(doc, title: str, code: str):
    section = doc.sections[0]
    section.page_width = Cm(21.0)
    section.page_height = Cm(29.7)
    section.left_margin = Cm(2.6)
    section.right_margin = Cm(2.4)
    section.top_margin = Cm(2.6)
    section.bottom_margin = Cm(2.6)
    section.header_distance = Cm(1.2)
    section.footer_distance = Cm(1.2)

    hp = section.header.paragraphs[0]
    hp.alignment = WD_ALIGN_PARAGRAPH.LEFT
    hp.clear()
    r1 = hp.add_run(f"内部资料  |  {PROJECT} {VERSION}  |  {title}")
    set_run_font(r1, "宋体", 9, False, GRAY)
    r2 = hp.add_run(f"\t{code}")
    set_run_font(r2, "宋体", 9, False, GRAY)
    hp.paragraph_format.space_after = Pt(2)

    # header line
    pBdr = hp._p.get_or_add_pPr()
    pBdr_el = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    bottom.set(qn("w:val"), "single")
    bottom.set(qn("w:sz"), "12")
    bottom.set(qn("w:space"), "4")
    bottom.set(qn("w:color"), "1F4E79")
    pBdr_el.append(bottom)
    pBdr.append(pBdr_el)

    fp = section.footer.paragraphs[0]
    fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    fp.clear()
    r = fp.add_run("第 ")
    set_run_font(r, "宋体", 9, False, GRAY)
    # PAGE field
    fld1 = OxmlElement("w:fldChar")
    fld1.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = " PAGE "
    fld2 = OxmlElement("w:fldChar")
    fld2.set(qn("w:fldCharType"), "end")
    run_page = fp.add_run()
    set_run_font(run_page, "宋体", 9, False, GRAY)
    run_page._r.append(fld1)
    r_in = fp.add_run()
    r_in._r.append(instr)
    set_run_font(r_in, "宋体", 9, False, GRAY)
    run_page2 = fp.add_run()
    set_run_font(run_page2, "宋体", 9, False, GRAY)
    run_page2._r.append(fld2)
    r3 = fp.add_run(" 页")
    set_run_font(r3, "宋体", 9, False, GRAY)


def new_doc(title: str, code: str) -> Document:
    doc = Document()
    style = doc.styles["Normal"]
    style.font.name = "Times New Roman"
    style.font.size = Pt(12)
    rPr = style.element.get_or_add_rPr()
    rFonts = rPr.find(qn("w:rFonts"))
    if rFonts is None:
        rFonts = OxmlElement("w:rFonts")
        rPr.append(rFonts)
    rFonts.set(qn("w:eastAsia"), "仿宋")
    set_header_footer(doc, title, code)
    return doc


def table(doc, headers, rows, col_widths=None, header=True):
    tbl = doc.add_table(rows=1 + len(rows), cols=len(headers))
    tbl.style = "Table Grid"
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl.autofit = True
    grid = tbl._tbl.tblPr
    # keep grid
    for i, htext in enumerate(headers):
        cell = tbl.rows[0].cells[i]
        cell.text = ""
        cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
        if header:
            shade_cell(cell, HEADER_BG)
        p0 = cell.paragraphs[0]
        p0.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p0.paragraph_format.space_before = Pt(3)
        p0.paragraph_format.space_after = Pt(3)
        p0.paragraph_format.first_line_indent = Pt(0)
        run = p0.add_run(htext)
        set_run_font(run, "黑体", 10, True, HEADER_FG if header else BLACK)
    for r_i, row in enumerate(rows):
        for c_i, val in enumerate(row):
            cell = tbl.rows[r_i + 1].cells[c_i]
            cell.text = ""
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            if r_i % 2 == 1:
                shade_cell(cell, "F2F2F2")
            p0 = cell.paragraphs[0]
            p0.alignment = WD_ALIGN_PARAGRAPH.LEFT if c_i > 0 else WD_ALIGN_PARAGRAPH.CENTER
            p0.paragraph_format.space_before = Pt(2)
            p0.paragraph_format.space_after = Pt(2)
            p0.paragraph_format.first_line_indent = Pt(0)
            add_mixed(p0, str(val), ea="宋体", size=10, bold=False, space_after=0, first_line=False, line=16)
    if col_widths:
        for row in tbl.rows:
            for i, w in enumerate(col_widths):
                row.cells[i].width = Cm(w)
    spacer(doc, 8)
    return tbl


def meta_table(doc, pairs):
    tbl = doc.add_table(rows=len(pairs), cols=2)
    tbl.style = "Table Grid"
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, (k, v) in enumerate(pairs):
        c0, c1 = tbl.rows[i].cells
        c0.text = ""
        c1.text = ""
        shade_cell(c0, "E7EEF7")
        for cell, text, ea, bold, align in (
            (c0, k, "黑体", True, WD_ALIGN_PARAGRAPH.CENTER),
            (c1, v, "仿宋", False, WD_ALIGN_PARAGRAPH.LEFT),
        ):
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            p0 = cell.paragraphs[0]
            p0.alignment = align
            p0.paragraph_format.first_line_indent = Pt(0)
            p0.paragraph_format.space_before = Pt(4)
            p0.paragraph_format.space_after = Pt(4)
            add_mixed(p0, text, ea=ea, size=11, bold=bold, space_after=0, first_line=False, line=18)
        c0.width = Cm(4.2)
        c1.width = Cm(12.0)
    spacer(doc, 10)
    return tbl


def sign_block(doc, parties):
    """parties: list of (title, lines)"""
    h(doc, "签署页", 1)
    p(doc, "本文件一式四份，甲乙双方各执两份，具有同等法律效力。签署栏中黄底项由各方填写后，加盖单位公章（或合同专用章）。骑缝章加盖于多页骑缝处。", first_line=True)
    for title, lines in parties:
        center(doc, title, ea="黑体", size=14, space_before=16, space_after=8)
        table(doc, ["项目", "内容"], [[a, b] for a, b in lines], col_widths=[4.5, 12])
        p(doc, "（本页以下无正文）", first_line=False, align=WD_ALIGN_PARAGRAPH.LEFT, size=10.5, color=GRAY)


def cover(doc, main_title, subtitle, code, extra_lines):
    spacer(doc, 24)
    center(doc, PROJECT, ea="黑体", size=18, color=NAVY, space_after=4)
    center(doc, f"（{PROJECT_SHORT}）{VERSION}", ea="黑体", size=14, color=NAVY, space_after=18)
    center(doc, main_title, ea="黑体", size=22, color=BLACK, space_before=12, space_after=6)
    if subtitle:
        center(doc, subtitle, ea="楷体", size=14, color=GRAY, space_after=18)
    center(doc, code, ea="宋体", size=12, bold=False, space_after=20)
    meta_table(doc, extra_lines)
    p(doc, "说明：文中黄底【】为待校企双方核对后填写的信息。本稿为待签署文本，盖章前须经院校校企办（或同等部门）及企业授权人员审阅。不得伪造印章、签名或日期。", size=10.5, ea="楷体", color=GRAY, first_line=True)
    doc.add_page_break()


# ---------------------------------------------------------------------------
# 1. 战略合作协议
# ---------------------------------------------------------------------------
def build_agreement() -> Path:
    code = "ZXHR-HZ-2026-001"
    doc = new_doc("战略合作协议", code)
    cover(
        doc,
        "校企合作战略协议书",
        "（产教融合 · HR数字员工项目）",
        code,
        [
            ("项目名称", f"{PROJECT}（{PROJECT_SHORT}）一期"),
            ("甲方（院校）", SCHOOL),
            ("项目实施地", SCHOOL_CAMPUS),
            ("乙方（企业）", COMPANY),
            ("协议性质", "框架性战略合作协议"),
            ("建议有效期", "2026年7月1日至2027年6月30日（以签署日为准）"),
            ("密级", "内部"),
        ],
    )

    center(doc, "校企合作战略协议书", ea="黑体", size=18, space_after=12)
    p(doc, f"甲方（院校方）：{SCHOOL}", first_line=False)
    p(doc, "统一社会信用代码：【见事业单位法人证书，盖章前填写】", first_line=False)
    p(doc, f"住所（项目实施地）：{SCHOOL_CAMPUS}", first_line=False)
    p(doc, f"登记住所：{SCHOOL_REG_ADDR}", first_line=False)
    p(doc, "法定代表人 / 授权代表：【姓名、职务】", first_line=False)
    spacer(doc, 6)
    p(doc, f"乙方（企业方）：{COMPANY}", first_line=False)
    p(doc, "统一社会信用代码：915001067748976838", first_line=False)
    p(doc, "住所：重庆市沙坪坝区西永大道36号附2号研发楼三期02#501、502、503、504", first_line=False)
    p(doc, "法定代表人：呙坤宏　　授权代表：【姓名、职务】", first_line=False)
    spacer(doc, 6)
    p(
        doc,
        f"鉴于甲方为开展职业教育与人工智能应用人才培养，拟组织学生团队研发人力资源领域数字员工；乙方为依法存续的科技企业，长期从事产教融合、校企合作及信息化服务，具备提供真实业务场景、岗位需求与成果确认的条件。双方本着平等自愿、诚实信用、合作共赢原则，就共同推进「{PROJECT}」（以下简称“本项目”或“小慧”）达成如下协议。",
    )

    h(doc, "第一条  定义与解释", 1)
    p(doc, "1.1  本项目：指以中小型企业人力资源岗位重复性事务为对象，研发「一人决策、Agent辅助」的数字员工系统，一期范围包括总控及招聘、入职、培训、绩效、行政五个业务模块。")
    p(doc, "1.2  数字员工：指在现有人事管理制度与系统之上进行辅助处理的智能体系统，不替代人力资源管理系统（HCM），不替代人对录用、合同、定级、薪酬核算等事项的最终决定。")
    p(doc, "1.3  脱敏数据：指去除或替换真实姓名、身份证号、联系方式、薪资明细等个人信息后，仅用于开发、测试与教学演示的样本数据。")
    p(doc, "1.4  一期：指自本协议确定的开发周期起，至双方书面确认的一期验收之日止所完成的功能、文档与测试。薪酬福利、金税及外部申报系统对接不纳入一期。")

    h(doc, "第二条  合作原则与目标", 1)
    p(doc, "2.1  合作原则：产教融合、工学结合；需求来自岗位、开发服务教学与应用验证；合法合规、最小必要、人机边界清晰。")
    p(doc, "2.2  合作目标：")
    p(doc, "（1）由乙方结合自身中小型科技企业人力资源管理实际，确认人力资源岗位典型工作事项、痛点及一期可辅助范围；")
    p(doc, "（2）由甲方组织项目团队，完成小慧一期系统设计、开发、测试与文档；")
    p(doc, "（3）形成可演示、可检查、可追溯的数字员工能力，用于教学、实训及职业院校技能竞赛展示（展示材料按赛项规程脱敏）；")
    p(doc, "（4）为后续二期（含薪酬等强合规模块）及可能的成果转化预留接口，但不构成本协议项下必须完成的义务。")

    h(doc, "第三条  合作内容", 1)
    p(doc, "3.1  需求调研。乙方协助提供或确认人力资源岗位工作事项清单、制度口径（可脱敏）、审批习惯及一期范围；甲方负责整理形成《需求调研报告》并交乙方确认。")
    p(doc, "3.2  开发实施。甲方按照双方确认的《一期开发计划》组织开发。技术路线采用开源多智能体框架进行二次开发，业务闸门、权限、回核与人在回路机制由项目团队实现。")
    p(doc, "3.3  测试与确认。甲方组织一期系统测试，形成《一期系统测试报告》；乙方对与需求一致性、场景真实性及是否同意作为校企合作成果予以书面确认。")
    p(doc, "3.4  教学与竞赛。在遵守赛项规程、保密条款及个人信息保护要求的前提下，甲方可将本项目用于教学实训和技能竞赛展示。赛场材料不展示乙方商业秘密、真实员工档案及未公开的内部制度全文。")
    p(doc, "3.5  本协议为框架协议。具体调研组织、开发节点、测试安排以《需求调研报告》《一期开发计划》《一期系统测试报告》及双方往来确认为准。")

    h(doc, "第四条  甲方的权利与义务", 1)
    p(doc, "4.1  负责项目组织、开发实施、版本管理及测试，保证开发过程可追溯。")
    p(doc, "4.2  指导教师对项目方向、合规边界和对外口径负指导责任；学生团队不得将真实个人信息写入仓库、演示环境或竞赛材料。")
    p(doc, "4.3  按约定向乙方报送调研稿、计划稿、测试稿及需要确认的节点说明。")
    p(doc, "4.4  未经乙方书面同意，不得以乙方名义宣称系统已在乙方生产环境全面上线，或将样本测算数据表述为乙方生产运营指标。")
    p(doc, "4.5  对在合作中知悉的乙方经营信息、未公开制度及对接人员信息予以保密。")

    h(doc, "第五条  乙方的权利与义务", 1)
    p(doc, "5.1  指定项目对接人，对调研事项、一期范围及测试结论中与需求相关的部分进行核对并反馈。")
    p(doc, "5.2  在确认内容真实、准确、无重大遗漏的前提下，为《战略合作协议》《需求调研报告》《一期开发计划》《一期系统测试报告》等真实性证明材料提供盖章确认。")
    p(doc, "5.3  有权要求甲方纠正夸大宣传、超范围承诺或不当使用企业名称的情形。")
    p(doc, "5.4  不承担为甲方竞赛成绩、软著登记结果或第三方评奖提供保证的义务。")
    p(doc, "5.5  向甲方提供的业务说明以岗位级、流程级信息为主；涉及员工个人信息的，应事先脱敏或拒绝提供。")

    h(doc, "第六条  项目组织", 1)
    p(doc, "6.1  甲方项目负责人：【姓名、联系电话】")
    p(doc, "6.2  甲方指导教师：【姓名、职务、联系电话】")
    p(doc, "6.3  乙方项目对接人：【姓名、职务、联系电话】")
    p(doc, "6.4  双方对接人变更的，应在三个工作日内书面通知对方，不影响本协议效力。")

    h(doc, "第七条  成果归属与知识产权", 1)
    p(doc, "7.1  本协议不替代双方就软件著作权、专利权、技术秘密另行签署的开发或权属协议。若另有《合作开发协议》或著作权登记文件，权属以该等文件为准。")
    p(doc, "7.2  在权属文件签署前，甲方对学生团队在本项目中形成的程序、文档、演示材料享有教学使用、参赛展示及完善迭代的权利；乙方享有将本项目作为校企合作案例进行如实表述的权利。")
    p(doc, "7.3  项目所依赖的开源框架、第三方模型接口、办公套件等，其权利属于原权利人，双方按相应许可使用，不因本协议发生转移。")
    p(doc, "7.4  任何一方不得将对方的名称、标识用于与本项目无关的商业推广。")

    h(doc, "第八条  数据安全与个人信息保护", 1)
    p(doc, "8.1  开发、测试、演示一律使用脱敏样本或虚构夹具，禁止将乙方或任何第三方的真实员工档案、工资表、身份证复印件等作为训练、评测或竞赛展示材料。")
    p(doc, "8.2  系统一期设计应落实：招聘评分前对年龄、性别、婚育、户籍等敏感字段进行物理删除；数字结果与原文回核；政策问答须有知识库依据；录用、合同审批、绩效定级等对个人有重大影响的决定由人作出。")
    p(doc, "8.3  双方应遵守《中华人民共和国个人信息保护法》《中华人民共和国数据安全法》及智能体规范应用相关规定。")

    h(doc, "第九条  费用", 1)
    p(doc, "9.1  本协议项下一期研发作为产教融合实践教学项目实施，除双方另签书面协议外，互不结算开发费用、授权费用或盖章费用。")
    p(doc, "9.2  因调研、差旅、打印产生的费用由发生方自行承担，另有约定的除外。")

    h(doc, "第十条  陈述、保证与责任限制", 1)
    p(doc, "10.1  各方保证其签署人已获合法授权。")
    p(doc, "10.2  一期系统为教学与应用验证性质的数字员工，不构成对乙方人力资源管理的专业法律意见，亦不得直接用于自动作出录用、解除、定级或薪酬发放决定。")
    p(doc, "10.3  除故意或重大过失外，一方对另一方因使用演示系统或竞赛展示产生的间接损失不承担责任。")

    h(doc, "第十一条  期限、变更与终止", 1)
    p(doc, "11.1  本协议自双方盖章之日起生效，有效期至【2027年6月30日】。期满前三十日任何一方提出续签的，由双方协商。")
    p(doc, "11.2  变更须采用书面形式，由双方盖章确认。")
    p(doc, "11.3  一方严重违约或丧失履行能力的，另一方可书面通知终止本协议。终止不影响已经确认的真实性文件之证明效力，但保密义务继续有效。")

    h(doc, "第十二条  违约与争议解决", 1)
    p(doc, "12.1  任何一方违反保密、数据使用或名称使用约定的，应立即停止侵害并消除影响；造成损失的，依法承担相应责任。")
    p(doc, "12.2  因本协议引起的争议，双方应先协商；协商不成的，提交甲方住所地有管辖权的人民法院诉讼解决。")

    h(doc, "第十三条  其他", 1)
    p(doc, "13.1  本协议未尽事宜，由双方另行协商并签订补充协议，补充协议与本协议具有同等效力。")
    p(doc, "13.2  附件：《需求调研报告》《一期开发计划》《一期系统测试报告》于各方确认后作为本协议附件，与本协议正文冲突时，就该附件所涉专业事项以附件最新确认稿为准。")
    p(doc, "13.3  本协议用中文写成。")

    sign_block(
        doc,
        [
            (
                "甲方（院校方）",
                [
                    ("单位全称", SCHOOL),
                    ("住所（项目实施地）", SCHOOL_CAMPUS),
                    ("法定代表人 / 授权代表（签字）", "【签字】"),
                    ("职务", "【职务】"),
                    ("盖章", "（公章或合同专用章）"),
                    ("签署日期", "【　　年　　月　　日】"),
                    ("联系人 / 电话", "【　　　　　　】"),
                ],
            ),
            (
                "乙方（企业方）",
                [
                    ("单位全称", COMPANY),
                    ("法定代表人 / 授权代表（签字）", "【签字】"),
                    ("职务", "【职务】"),
                    ("盖章", "（公章或合同专用章）"),
                    ("签署日期", "【　　年　　月　　日】"),
                    ("联系人 / 电话", "【　　　　　　】"),
                ],
            ),
        ],
    )
    path = OUT / "01-战略合作协议.docx"
    doc.save(path)
    return path


# ---------------------------------------------------------------------------
# 2. 需求调研报告
# ---------------------------------------------------------------------------
def build_research() -> Path:
    code = "ZXHR-DY-2026-01"
    doc = new_doc("需求调研报告", code)
    cover(
        doc,
        "需求调研报告",
        "人力资源岗位事项、痛点与一期范围确认",
        code,
        [
            ("委托 / 协作单位", COMPANY),
            ("编制单位", f"{SCHOOL}「小慧」项目组"),
            ("调研周期（建议）", "2026年7月"),
            ("报告版本", "V1.0（待企业确认稿）"),
            ("密级", "内部"),
        ],
    )

    h(doc, "0  文件控制", 1)
    table(
        doc,
        ["角色", "姓名", "单位 / 职务", "日期", "签字"],
        [
            ["编制", "【项目负责人】", f"{SCHOOL} 项目组", "【　】", ""],
            ["审核", "【指导教师】", "【院系 / 职务】", "【　】", ""],
            ["企业确认", "【对接人】", f"{COMPANY}", "【　】", ""],
        ],
    )

    h(doc, "1  引言", 1)
    h(doc, "1.1  编写目的", 2)
    p(doc, f"本报告记录与{COMPANY}（以下简称“企业方”）围绕人力资源岗位开展的需求调研结果，用于：确定小慧一期做哪些事务、明确不做哪些决策、划定人机边界，并作为后续开发计划与测试验收的需求基线。")
    h(doc, "1.2  项目背景", 2)
    p(doc, "企业方为中小型科技与教育服务企业。该类组织通常人事编制精简，招聘、入职、培训、绩效、行政问答与月报等事务集中在少数岗位上，人员一旦流动，知识与节奏容易中断。项目组拟以数字员工承担重复性辅助工作，由人事人员保留最终决策。")
    p(doc, "本报告描述的是岗位级需求与一期切分，不是企业生产环境已经替换人工的实施报告，也不是对某个行业（如文旅、高原农业等）痛点的外推。")
    h(doc, "1.3  依据", 2)
    p(doc, "（1）《中华人民共和国职业教育法》关于产教融合、校企合作的规定；")
    p(doc, "（2）国务院《关于深入实施“人工智能+”行动的意见》及国家层面智能体规范应用有关要求（知情权与最终决策权在人）；")
    p(doc, "（3）《中华人民共和国个人信息保护法》关于自动化决策、敏感信息处理的要求；")
    p(doc, "（4）企业方确认的人力资源岗位工作事项与一期范围。")

    h(doc, "2  调研概述", 1)
    h(doc, "2.1  调研对象", 2)
    p(doc, "对象为企业方人力资源管理相关岗位及可公开说明的制度口径，不采集真实员工档案。建议访谈职务包括：人事负责人或行政人事专员、负责招聘/入职事务的经办人。姓名由企业方在确认时填入附件。")
    table(
        doc,
        ["序号", "对象类型", "建议职务", "姓名", "访谈形式"],
        [
            ["1", "需求确认", "人事 / 行政负责人", "【待填】", "面谈 / 线上"],
            ["2", "事务经办", "招聘或综合人事专员", "【待填】", "面谈 / 线上"],
            ["3", "校企对接", "校企合作对接人", "【待填】", "工作沟通"],
        ],
    )
    h(doc, "2.2  调研方法", 2)
    p(doc, "采用「岗位事项清单 + 痛点核对 + 一期切分确认」的方法：先按国内中小企业人力资源常规模块列出事项，再由企业方勾选高频项、高风险项和一期不宜自动化项，最后形成书面确认。不把未访谈过的行业故事写入本报告。")
    h(doc, "2.3  调研结论先行", 2)
    p(doc, "结论一：人力资源工作可划分为招聘、入职、培训、绩效、薪酬、员工关系与行政六大模块，典型事项三十项以上。")
    p(doc, "结论二：高频、可结构化、可回溯的事务适合由数字员工辅助；对个人有重大影响的决定必须留在人。")
    p(doc, "结论三：一期采用「1 个总控 + 5 个业务模块」（招聘、入职、培训、绩效、行政）。薪酬因金税、社保公积金、个税申报及外部系统对接，列入后期。")
    p(doc, "结论四：开发与演示使用脱敏样本。任何效率数字仅作为样本测算，不得写成企业已实现的运营 KPI。")

    h(doc, "3  现状与痛点（经企业岗位口径确认）", 1)
    p(doc, "经与企业方核对，中小型编制下人事岗位的典型压力如下。下列表述为岗位级场景，不指向特定员工。")
    table(
        doc,
        ["编号", "痛点", "表现", "对一期的含义"],
        [
            ["P1", "编制薄、任务杂", "筛简历、追入职、答制度、出月报集中在少数人", "要能分模块接任务，而不是一个聊天窗口包办"],
            ["P2", "简历初筛耗时且易踩合规", "附件格式杂、经历数字易被夸大，敏感信息不宜进入评分", "先结构化、脱敏、回核，再给建议，不代替录用"],
            ["P3", "入职跨部门催办", "合同、账号、设备等节点分散，HR 往往只掌握催办权", "只读进度、停在审批门，不代批、不写主数据"],
            ["P4", "制度问答打断主业", "年假、报销、社保等问题重复出现，口答易与制度不一致", "先检索再答，无依据则停，争议转人工"],
            ["P5", "材料与报表重复劳动", "培训讲义、360 汇总、月报数字需要可核对", "脚本算数、模型出草稿，人审核后使用"],
            ["P6", "知识随人员流动流失", "经办人变动后面试口径、催办清单不易交接", "过程落盘、可检查、可追溯"],
        ],
    )
    p(doc, "企业方确认：上述痛点与本企业人事岗位实际相符，同意作为一期需求输入。□ 是　　□ 否（请在打印稿勾选）", first_line=True)

    h(doc, "4  业务事项全景与一期切分", 1)
    p(doc, "下表为岗位典型事项。标注「一期」的，指数字员工提供辅助能力；标注「后期」的，一期明确不做自动化；标注「人工」的，系统可以准备材料，决定权在人。完整清单以企业确认后的勾选为准。")
    table(
        doc,
        ["模块", "典型事项", "一期策略"],
        [
            ["招聘", "JD 撰写与渠道运营", "后期"],
            ["招聘", "简历收发、解析、初筛整理", "一期"],
            ["招聘", "敏感信息处理、数字回核、建议排序", "一期"],
            ["招聘", "人才画像、人才库检索", "一期"],
            ["招聘", "面试纪要（含转写）", "一期"],
            ["招聘", "Offer 制作、发放与跟进", "后期 / 人工"],
            ["招聘", "录用 / 淘汰决定", "人工（禁止自动决定）"],
            ["入职", "合同准备与资料收集催办", "一期（催办，不代签）"],
            ["入职", "账号、设备等节点进度", "一期（只读）"],
            ["入职", "合同内容、账号权限审批", "人工（人在回路）"],
            ["入职", "Buddy、入职培训节点", "一期跟踪"],
            ["入职", "试用期 7/30/60/90 跟进", "一期"],
            ["培训", "点名主题的物料草稿（ADDIE）", "一期"],
            ["培训", "场地、签到、讲师现场组织", "人工"],
            ["培训", "发展路径设计", "后期"],
            ["绩效", "360 反馈校验与聚合", "一期"],
            ["绩效", "雷达看板", "一期"],
            ["绩效", "OKR/KPI 设定、最终定级", "人工 / 后期"],
            ["薪酬", "薪资核算、调薪、社保公积金、个税、离职结算", "后期（强合规）"],
            ["行政", "制度问答（有依据才答）", "一期"],
            ["行政", "月报与数据看板（脚本计算）", "一期"],
            ["行政", "劳动争议、破例审批、个案调查", "人工"],
        ],
    )
    p(doc, "一期覆盖的事务性工作约 18 项（相对约 30 项典型事项）。该比例只说明范围切分，不代表已经替代相应比例的岗位编制。")

    h(doc, "5  一期功能需求", 1)
    h(doc, "5.1  总控", 2)
    p(doc, "识别请求所属业务域，分发给对应模块并转述结果。总控不直接回答年假天数、不直接打简历分、不批准入职。一次请求只进一条专线；看不准就向人确认。")
    h(doc, "5.2  招聘", 2)
    p(doc, "从邮箱收取简历附件，转为可核对的结构化档案；抽取结果须能回溯原文；评分前物理删除年龄、性别、婚育、户籍等；按岗位给出建议动作，不输出录用或淘汰决定；数字与原简历回核，对不上则拦截。")
    h(doc, "5.3  入职", 2)
    p(doc, "对照人事系统中合同、账号、设备、培训、Buddy 等节点的真实进度进行查询与催办。合同内容、账号权限两道门必须由人批准或拒绝。审批超过约定天数只催办，不自动放行。系统不在人事主数据中建人。")
    h(doc, "5.4  培训", 2)
    p(doc, "按用户点名的主题和材料种类生成草稿。用户未点名的材料不出。稿面标明「AI 辅助生成，讲师审核后交付」。素材中没有的制度、数字、名称不得编造。")
    h(doc, "5.5  绩效", 2)
    p(doc, "校验 360 反馈是否齐全（缺自评则停止），用脚本聚合分数，整理共识、分歧和面谈建议，出具看板。不给出 S/A/B/C 等最终等级。")
    h(doc, "5.6  行政", 2)
    p(doc, "制度类问题必须先检索企业政策知识库再答复并标明出处；检索不到不得用通用常识硬答。员工本人薪资、考勤流水、劳动争议等转人工。月报数字全部由脚本计算，模型不得改数。")

    h(doc, "6  非功能与合规需求", 1)
    table(
        doc,
        ["类别", "要求"],
        [
            ["决策边界", "对个人有重大影响的决定不交给算法；人可拒绝、可纠正、可停止"],
            ["失败策略", "缺材料、缺权限、缺上游、无检索命中时停止，不假装成功"],
            ["数据", "开发测试使用脱敏样本；禁止真实身份证、银行账号、工资明细入库"],
            ["系统关系", "不替代 HCM；入职模块对花名册只读"],
            ["权限", "员工、主管、HR 可见范围不同；非 HR 不得查询他人工资或出月报"],
            ["可追溯", "关键步骤有落盘文件或日志，可供检查"],
            ["部署形态", "一期以校企联合开发与演示验证为主，不承诺乙方生产环境替换"],
        ],
    )

    h(doc, "7  样本测算（仅招聘初筛整理环节）", 1)
    p(doc, "为说明一期在「简历初筛整理」这一环节上的辅助效果，项目组使用脱敏演示简历做样本测算。测算条件与结果如下。该节不是乙方生产环境统计，不得改写成「已为某企业节约××万元」或全岗位效率。")
    table(
        doc,
        ["项目", "口径"],
        [
            ["样本", "脱敏演示简历约 50 份，同一份演示岗位说明"],
            ["人工对照", "初筛整理约 8 分钟 / 份（含打开附件、摘录要点、形成可呈报材料）"],
            ["系统对照", "辅助链跑完约 1.2 分钟 / 份（含解析、脱敏、评分建议、回核）"],
            ["该环节", "耗时约降 85%（仅限上述环节，不含面试、Offer、入职）"],
            ["范围说明", "一期约覆盖 18/30 项典型事务，约占事务工时测算 45%"],
        ],
    )

    h(doc, "8  风险与约束", 1)
    p(doc, "R1  若把演示数据当成真实人事结果对外发布，将直接违反本报告和第 8 章合规要求。")
    p(doc, "R2  薪酬、金税、社保对接一期不做，避免未完成合规评估即自动化。")
    p(doc, "R3  大模型存在数字幻觉，必须用脚本回核与失败即停来约束，不能只靠提示词。")
    p(doc, "R4  企业制度若未提供可检索文本，行政问答不得上线到真实员工通道。")

    h(doc, "9  结论", 1)
    p(doc, "双方确认：小慧一期需求以本报告第 4–6 章为准；薪酬及 Offer 等事项列入后期；效率表述仅使用第 7 章样本测算口径。本报告经企业方盖章后，可作为项目真实性与需求来源的证明材料。")

    h(doc, "附件 A  访谈纪要（企业填写）", 1)
    table(
        doc,
        ["项目", "内容"],
        [
            ["访谈时间", "【　　年　　月　　日】"],
            ["地点 / 方式", "【　　　　　　】"],
            ["企业方出席", "【姓名、职务】"],
            ["院校方出席", "【姓名、职务】"],
            ["确认的一期范围", "总控 + 招聘 / 入职 / 培训 / 绩效 / 行政"],
            ["明确不做", "薪酬自动化；自动录用、自动定级、自动批准合同"],
            ["其他意见", "【　　　　　　】"],
        ],
        col_widths=[4.5, 12],
    )
    p(doc, "企业方确认（盖章）：________________　　日期：________________", first_line=False)

    path = OUT / "02-需求调研报告.docx"
    doc.save(path)
    return path


# ---------------------------------------------------------------------------
# 3. 一期开发计划
# ---------------------------------------------------------------------------
def build_plan() -> Path:
    code = "ZXHR-JH-2026-01"
    doc = new_doc("一期开发计划", code)
    cover(
        doc,
        "一期开发计划",
        "阶段、检查点、交付物与验收标准",
        code,
        [
            ("项目名称", f"{PROJECT} {VERSION}"),
            ("计划周期（建议）", "2026年7月1日—2026年9月15日"),
            ("编制", f"{SCHOOL}「小慧」项目组"),
            ("确认", COMPANY),
            ("版本", "V1.0（待确认稿）"),
        ],
    )

    h(doc, "0  文件控制", 1)
    table(
        doc,
        ["角色", "姓名", "单位 / 职务", "日期", "签字"],
        [
            ["编制", "【项目负责人】", "项目组", "【　】", ""],
            ["审核", "【指导教师】", "【院系】", "【　】", ""],
            ["企业确认", "【对接人】", COMPANY, "【　】", ""],
        ],
    )

    h(doc, "1  编制说明", 1)
    p(doc, "本计划回答「按什么顺序建造、做到什么算完成」，不把日历表当成唯一管理工具。阶段依赖和检查点是骨架，日期可按教学与企业确认节奏微调，但不得颠倒「先地基、后单元、再集成、最后验收」的顺序。")
    p(doc, "本计划与课程讲义中的示例工期（并行约十五日）不是同一份文件。讲义工期用于说明并行方法；本文件按校企实际组织，覆盖 2026 年 7 月至 9 月的一期交付。")

    h(doc, "2  目标与范围", 1)
    h(doc, "2.1  一期目标", 2)
    p(doc, "建成可运行的 HR 数字员工：人对「小慧」提出事务请求，系统按业务分发到招聘、入职、培训、绩效、行政专线，关键决定留在人，关键数字可回核，失败则停止。")
    h(doc, "2.2  范围内", 2)
    p(doc, "独立运行环境与网关；脱敏演示数据；总控分发；招聘辅助链；入职只读催办与两道审批门；培训点名生成；绩效 360 聚合；行政检索问答与脚本月报；分模块测试与总控联调；开发与测试文档。")
    h(doc, "2.3  范围外（一期不做）", 2)
    p(doc, "薪酬核算与金税、社保公积金、个税申报对接；自动录用、自动定级、自动签署劳动合同；爬取招聘网站；用真实员工档案做演示；替换企业现有 HCM。")

    h(doc, "3  组织与分工", 1)
    table(
        doc,
        ["角色", "人数 / 来源", "职责"],
        [
            ["项目负责人 / 总控", "学生 1 人", "环境、路由、联调、版本与对外口径"],
            ["招聘模块", "学生 1 人", "收信解析、脱敏、评分回核、人才库、纪要"],
            ["入职、绩效模块", "学生 1 人", "入职编排与看板、360 聚合"],
            ["培训、行政模块", "学生 1 人", "培训物料闸门、政策检索与月报"],
            ["指导教师", "【待填】", "方向、合规、校企协调、质量把关"],
            ["企业对接", COMPANY, "需求确认、场景口径、盖章确认"],
        ],
    )

    h(doc, "4  阶段划分与检查点", 1)
    p(doc, "阶段按「地基 → 业务单元（可并行）→ 集成 → 验收」排列。业务单元之间无硬依赖，可以并行；集成必须等单元达到检查点。")
    table(
        doc,
        ["阶段", "类型", "主要内容", "完成标志（检查点）", "建议窗口"],
        [
            ["A 基础环境", "地基", "独立配置、网关、多智能体骨架、权限、编排引擎", "健康检查通过；六个 Agent 就位；含人工恢复的审批流可跑通", "2026-07 上旬"],
            ["B 数据资产", "地基", "脱敏简历、岗位说明、制度文本、月报样表", "样本可用且已脱敏，禁止真实档案", "2026-07 中旬"],
            ["C 招聘", "单元", "解析、核对、脱敏、评分、回核、画像、人才库、纪要", "主链路可跑通；敏感字段删除可证明；回核可拦截虚构数字", "2026-07—08"],
            ["D 入职", "单元", "只读进度、两道审批门、催办、试用期跟进、看板", "门必须人批；超时只催办；角标以人事节点为准", "2026-07—08"],
            ["E 培训", "单元", "按点名生成物料、结构自检", "未点名不出全套；稿面有审核声明", "2026-07—08"],
            ["F 绩效与行政", "单元", "360 校验聚合；政策检索；脚本月报", "缺自评则停；无命中则停；月报数字脚本出", "2026-07—08"],
            ["G 总控", "集成", "分发、转述、专线互不派活、权限", "请求进入正确专线；总控不代答业务", "2026-08 下旬"],
            ["H 验收", "验收", "分模块回归 + 端到端联调 + 出测试报告", "关键用例回归通过；遗留项清单闭环或降级", "2026-08-29—09-15"],
        ],
    )

    h(doc, "5  里程碑", 1)
    table(
        doc,
        ["里程碑", "对应阶段", "业务含义", "建议完成"],
        [
            ["M1 地基就绪", "A+B", "环境与脱敏样本具备，可开始业务开发", "2026-07 下旬"],
            ["M2 单域可用", "C 优先，D/E/F 跟进", "至少招聘辅助链可演示", "2026-08 中旬"],
            ["M3 数字员工成型", "C–G", "总控 + 五模块可联调", "2026-08 下旬"],
            ["M4 一期验收", "H", "测试报告出具，企业确认", "2026-09-15 前"],
        ],
    )

    h(doc, "6  主要交付物", 1)
    table(
        doc,
        ["类别", "交付物", "说明"],
        [
            ["软件", f"{PROJECT} {VERSION} 可运行系统", "总控 + 五模块 + 只读人事花名册应用"],
            ["需求", "《需求调研报告》", "本期附件"],
            ["计划", "《一期开发计划》", "本文件"],
            ["测试", "《一期系统测试报告》", "含缺陷与遗留项"],
            ["说明", "业务介绍、各模块说明、部署说明", "供教学与维护"],
            ["权属", "软件著作权登记材料（如开展）", "与本计划并行，不替代验收"],
        ],
    )

    h(doc, "7  进度管理", 1)
    p(doc, "7.1  每周核对检查点，不按「感觉差不多」宣布阶段完成。")
    p(doc, "7.2  并行阶段取最慢单元决定集成开工时间。")
    p(doc, "7.3  检查点过严导致无实质风险的小问题卡住时，由指导教师书面同意后方可带缺陷进入下一阶段，并列入遗留项。")
    p(doc, "7.4  软件功能冻结日建议为 2026 年 9 月 10 日（与开发完成登记口径一致），其后以缺陷修复、文档和演示准备为主。")

    h(doc, "8  质量、风险与合规", 1)
    table(
        doc,
        ["编号", "风险", "对策"],
        [
            ["Q1", "把大模型输出直接当人事结论", "脚本闸门 + 人在回路；失败即停"],
            ["Q2", "真实个人信息进入仓库", "仅脱敏样本；代码评审抽查"],
            ["Q3", "宣传口径超过一期能力", "对外只讲已实现专线；薪酬明确后期"],
            ["Q4", "环境依赖导致无法复测", "独立配置目录、版本钉死、检查清单"],
            ["Q5", "赛场展示泄露企业秘密", "演示夹具 + 赛规脱敏，盖章原件另档备查"],
        ],
    )

    h(doc, "9  验收标准（一期）", 1)
    p(doc, "同时满足下列条件，方可提请企业确认一期完成：")
    p(doc, "（1）总控能把典型请求分到正确模块，且自身不编造业务结论；")
    p(doc, "（2）招聘链具备脱敏与数字回核，且不自动淘汰；")
    p(doc, "（3）入职审批门可暂停并等人处理，超时只催办；")
    p(doc, "（4）培训可按点名出稿，自检可运行；")
    p(doc, "（5）绩效缺自评时拒绝聚合；")
    p(doc, "（6）行政无检索命中时拒绝硬答，月报数字来自脚本；")
    p(doc, "（7）《一期系统测试报告》已记录首轮缺陷、回归结果和遗留项。")

    h(doc, "10  二期预留", 1)
    p(doc, "二期候选：Offer 与员工关系子项、邮箱/飞书/HCM 连接深化、薪酬模块（须单独立项并完成合规评估）。二期不在本计划考核范围内。")

    h(doc, "11  确认意见", 1)
    p(doc, "院校项目组确认本计划作为一期实施依据。企业方确认：一期范围、不做什么、验收标准与本单位同意支持的校企合作内容一致。", first_line=True)
    p(doc, "企业方意见：□ 同意　　□ 同意但有修改（附意见）　　□ 不同意", first_line=False)

    path = OUT / "03-一期开发计划.docx"
    doc.save(path)
    return path


# ---------------------------------------------------------------------------
# 4. 一期系统测试报告
# ---------------------------------------------------------------------------
def build_test() -> Path:
    code = "ZXHR-CS-2026-01"
    doc = new_doc("一期系统测试报告", code)
    cover(
        doc,
        "一期系统测试报告",
        "分模块冒烟、缺陷回归与总控联调",
        code,
        [
            ("被测软件", f"{PROJECT} {VERSION}"),
            ("测试周期", "2026年8月29日—2026年9月10日（含回归与补测）"),
            ("测试组织", "项目组（开发测试一体，非独立第三方实验室）"),
            ("技术底座", "OpenClaw 2026.5.12 及项目二次开发脚本 / 闸门"),
            ("确认", COMPANY),
        ],
    )

    h(doc, "0  文件控制", 1)
    table(
        doc,
        ["角色", "姓名", "单位 / 职务", "日期", "签字"],
        [
            ["测试执行 / 汇总", "【项目负责人】", "项目组", "【　】", ""],
            ["审核", "【指导教师】", "【院系】", "【　】", ""],
            ["企业确认", "【对接人】", COMPANY, "【　】", ""],
        ],
    )

    h(doc, "1  概述", 1)
    p(doc, "本报告汇总小慧一期系统测试。测试目的是验证需求调研与开发计划中的一期能力是否可运行、关键闸门是否生效、已知缺陷是否关闭，并列出遗留项。")
    p(doc, "测试性质为项目组组织的功能、边界、权限与回归测试（含各模块冒烟和总控联调），不是国家认可的第三方型式检验。数据均为脱敏演示样本或测试夹具。")
    p(doc, "诚实记录原则：首轮发现的缺陷必须写明；不得把「未测」写成「通过」；不得把样本测算写成生产运行指标。")

    h(doc, "2  测试环境", 1)
    table(
        doc,
        ["项", "配置 / 说明"],
        [
            ["操作系统", "Linux（开发与云主机环境）"],
            ["运行时", "Node.js 22.x（业务脚本）、Python 3、conda 环境 openclaw-hr"],
            ["平台版本", "OpenClaw 2026.5.12"],
            ["模型接口", "主对话模型走国内接口；部分脚本另有专用接口"],
            ["协作入口", "Web 对话 / 命令行；员工政策问答走飞书直达行政模块"],
            ["人事花名册应用", "独立 Web 应用，入职模块只读"],
            ["数据", "教学与演示夹具，禁止当作真实人事档案"],
        ],
    )

    h(doc, "3  测试依据与范围", 1)
    p(doc, "依据：《需求调研报告》一期功能与非功能条款、《一期开发计划》第 9 章验收标准、各模块说明中的拒绝条件。")
    p(doc, "范围内：总控分发；招聘主链路；入职审批与查询看板；培训点名生成与自检；绩效 360 管道；行政检索、红线、月报与权限；回归补测（含面试转写）。")
    p(doc, "范围外：薪酬自动化；真实生产环境压测；第三方安全渗透；未提供的外部申报接口。")

    h(doc, "4  测试方法", 1)
    p(doc, "以事先写明的脚本和检查项为主，辅以对话联调。通过标准为：预期退出码、落盘文件、拦截行为或检索命中与需求一致。失败即停类用例以「正确拒绝」为通过。")
    table(
        doc,
        ["类型", "目的"],
        [
            ["功能", "主路径能否产出可检查材料"],
            ["边界", "缺自评、无检索命中、重名未给拼音等是否停止"],
            ["合规闸门", "敏感字段删除、数字回核、审批门不自动放行"],
            ["权限", "员工 / 主管 / HR 可见范围"],
            ["回归", "缺陷修复后重跑，防止复发"],
            ["联调", "总控只分发、专线互不派活"],
        ],
    )

    h(doc, "5  执行过程", 1)
    table(
        doc,
        ["轮次", "日期", "内容"],
        [
            ["首轮冒烟", "2026-08-29", "六域并行冒烟，暴露环境、数据与闸门问题"],
            ["修复回归 1", "2026-08-30 上午", "分域回测"],
            ["修复回归 2", "2026-08-30 下午—08-31", "夹具补齐、总控对话、压缩包安全解压、月报等"],
            ["专项", "2026-09-03 等", "入职看板口径复核等"],
            ["补测", "2026-09-10", "面试转写本机补测；总控超时实等"],
        ],
    )

    h(doc, "6  分模块结果（汇总）", 1)
    p(doc, "下表为管理口径汇总。细节见各模块测试记录。首轮未通过项已在回归中处理；「通过」指回归后达到预定标准。")
    table(
        doc,
        ["模块", "首轮要点", "回归后结论（截至 2026-09-10）"],
        [
            [
                "招聘",
                "主链路大部分可跑；无效邮件标记超时；面试转写当时跳过；检索与画像有待修项",
                "主链路通过；压缩包路径穿越拒绝；脱敏与回核生效；转写补测通过。无效 UID 标记超时按预期保留",
            ],
            [
                "入职",
                "首轮统计存在失败项（角标与人事节点口径不一致、残留待批文件、环境路径等）",
                "P0/P1 项修复后回测通过：角标改按人事节点；审批门不自动批准；重名须指定标识",
            ],
            [
                "培训",
                "结构自检可用；存在历史稿件用词告警",
                "自检通过；点名生成不会擅自扩成全套",
            ],
            [
                "绩效",
                "依赖缺失、报告格式不匹配、缺自评未拦截、重复摄入影响产物",
                "五项问题回归通过；缺自评拒绝聚合；夹具看板不得当作校准会结果",
            ],
            [
                "行政",
                "制度检索基本可用；差旅同义词一度未命中",
                "检索与六类红线通过；月报脚本复跑通过；分级权限验证通过",
            ],
            [
                "总控",
                "分发与红线基本正确；个别对话项因夹具缺失无法执行",
                "夹具补齐后对话补测通过；专线互不派活；超时实等完成",
            ],
        ],
    )

    h(doc, "7  典型闸门验证（节选）", 1)
    table(
        doc,
        ["编号", "验证点", "结果"],
        [
            ["G1", "招聘敏感字段在评分前物理删除，而非仅提示模型忽略", "通过"],
            ["G2", "评分文本中的数字与原简历不一致则拦截（曾发现年限被夸大）", "通过（证明回核有必要）"],
            ["G3", "入职合同 / 账号门暂停，等人处理；halt 超时只催办", "通过"],
            ["G4", "培训未点名的材料不默认全套产出", "通过"],
            ["G5", "绩效缺自评退出并拒绝出总表", "通过"],
            ["G6", "行政知识库无命中则失败退出，不改用常识作答", "通过"],
            ["G7", "非 HR 通道不能出月报、不能查他人工资", "通过"],
            ["G8", "总控不直接回答政策、不直接打分", "通过"],
        ],
    )

    h(doc, "8  缺陷处理", 1)
    p(doc, "首轮缺陷按「当场修、回归关」管理。下表为归类，不重复粘贴内部工单全文。")
    table(
        doc,
        ["类别", "示例", "状态"],
        [
            ["环境与依赖", "拼音组件缺失、Node 版本路径", "已关闭"],
            ["口径不一致", "入职角标曾误用流程完成态代表人到岗", "已关闭"],
            ["检索与同义词", "差旅 / 报销一度未命中", "已关闭"],
            ["产物互相覆盖", "批量评分写入路径", "已关闭"],
            ["安全解压", "压缩包路径穿越", "已关闭（拒绝恶意路径）"],
            ["测试数据", "部分联调用例缺夹具", "已补测关闭"],
            ["设计保留", "无效邮件 UID 标记超时", "遗留：保持预期，不修"],
        ],
    )

    h(doc, "9  遗留项", 1)
    p(doc, "下列事项不影响一期验收结论，但必须在使用和演示中遵守：")
    table(
        doc,
        ["编号", "遗留项", "使用约束"],
        [
            ["L1", "演示数据不是真实人事档案", "对外禁止称为某企业在职员工数据"],
            ["L2", "绩效等级夹具不是校准会结果", "禁止当作已定级名单"],
            ["L3", "培训阶段是否真正阅读上一份稿件，需人工抽查", "自检不能替代讲师审核"],
            ["L4", "投诉类问题主要靠规则转人工", "不得由系统下调查结论"],
            ["L5", "月报图字体在个别环境需安装中文字体", "不影响数字计算"],
            ["L6", "薪酬模块未开发", "禁止演示自动算薪、报税"],
        ],
    )

    h(doc, "10  测试结论", 1)
    p(doc, "在脱敏演示数据条件下，小慧一期（总控 + 招聘、入职、培训、绩效、行政）达到《一期开发计划》第 9 章所列验收标准。首轮缺陷已回归关闭或降级为使用约束。系统可以作为校企合作的一期成果进行教学、实训和脱敏展示，但不得表述为已在企业生产环境全面替代人事岗位，也不得把样本测算写成企业运营 KPI。")
    p(doc, "建议：同意一期测试通过。二期如开展薪酬或生产对接，须单独立项、补充专项测试与合规评估。")

    h(doc, "11  企业确认栏", 1)
    p(doc, "本单位已阅知测试范围、回归结论、遗留项及第 10 章使用约束，确认上述测试是针对校企合作项目一期系统的真实性检验材料。", first_line=True)
    p(doc, "结论：□ 同意通过　　□ 有条件通过（见意见）　　□ 不通过", first_line=False)
    p(doc, "意见：【　　　　　　　　　　　　　　　　　　】", first_line=False)
    spacer(doc, 12)
    p(doc, f"确认单位：{COMPANY}", first_line=False)
    p(doc, "授权代表（签字）：【　　　　】　　职务：【　　　　】", first_line=False)
    p(doc, "日期：【　　年　　月　　日】　　（公章）", first_line=False)

    path = OUT / "04-一期系统测试报告.docx"
    doc.save(path)
    return path


# ---------------------------------------------------------------------------
# 0. 填写说明
# ---------------------------------------------------------------------------
def build_guide() -> Path:
    code = "ZXHR-SM-2026-01"
    doc = new_doc("填写与盖章说明", code)
    cover(
        doc,
        "填写与盖章说明",
        "给指导教师与企业对接人",
        code,
        [
            ("院校全称", SCHOOL),
            ("项目实施地", SCHOOL_CAMPUS),
            ("配套文件", "战略合作协议、需求调研报告、一期开发计划、一期系统测试报告"),
            ("企业全称", COMPANY),
            ("统一社会信用代码", "915001067748976838"),
            ("法定代表人（工商）", "呙坤宏"),
        ],
    )
    h(doc, "1  这套材料是什么", 1)
    p(doc, "用于证明小慧项目有校企合作来源、有需求基线、有开发计划、有一期测试，而不是只有演示文稿。企业盖章表示对相应文件中可确认内容的认可，不是为企业尚未实施的生产上线作担保。")
    h(doc, "2  盖章前必须改的黄底栏", 1)
    p(doc, f"院校全称已按招生章程填写为「{SCHOOL}」。项目实施地已填写为「{SCHOOL_CAMPUS}」。登记住所按学院官网蓝龙潭校区写作「{SCHOOL_REG_ADDR}」。统一社会信用代码请从事业单位法人证书抄入（公开网页多为脱敏，本稿不臆造）。法定代表人、授权代表、指导教师、项目负责人、企业对接人、签署日期、访谈人员仍为黄底【】。乙方企业名称、信用代码、住所、法定代表人已按公开登记填写，如有变更以营业执照为准。")
    h(doc, "3  建议办理顺序", 1)
    p(doc, "（1）指导教师审阅四份正文，改掉与学校制度不符的争议管辖、授权程序。")
    p(doc, "（2）与重庆足下对接，核对调研痛点、一期范围是否允许加盖公章。")
    p(doc, "（3）替换全部黄底后打印；协议一式四份，其余报告一式两份。")
    p(doc, "（4）双方签字盖章，多页加盖骑缝章；扫描 PDF 备份。")
    p(doc, "（5）赛场 PPT 仍按赛规脱敏。盖章原件作为备查材料，不把营业执照号、真实员工、内部制度全文投到大屏上。")
    h(doc, "4  口径红线（盖章单位有权要求删除）", 1)
    p(doc, "不得写：已在足下生产环境全面上线、已替代人事编制、百分之百通过且无缺陷、全岗位效率提升百分之九十二、文旅或高原农业等未经访谈的行业痛点、真实身份证或工资表。效率只允许保留调研报告中的样本测算表述。")
    h(doc, "5  与软著材料的关系", 1)
    p(doc, "本套文件证明校企合作与一期工程过程。软件著作权登记若另行办理，权属以软著申请和《合作开发协议》为准，本战略协议第 7 条已作衔接，避免两套文件打架。")
    h(doc, "6  文件清单", 1)
    table(
        doc,
        ["文件", "企业章主要证明什么"],
        [
            ["01 战略合作协议", "双方存在产教融合合作，项目有企业方"],
            ["02 需求调研报告", "需求来自岗位确认，一期范围经企业认可"],
            ["03 一期开发计划", "开发不是即兴演示，有阶段和验收标准"],
            ["04 一期系统测试报告", "有测试过程、回归和遗留项，而非口头宣称已测"],
        ],
    )
    path = OUT / "00-填写与盖章说明.docx"
    doc.save(path)
    return path


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    paths = [
        build_guide(),
        build_agreement(),
        build_research(),
        build_plan(),
        build_test(),
    ]
    for pth in paths:
        print(f"wrote {pth} ({pth.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
