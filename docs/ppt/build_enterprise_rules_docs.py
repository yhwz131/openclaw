#!/usr/bin/env python3
"""生成“企业的规”示意制度文件（企业名称、文号已脱敏），并截取 PPT 用的局部图。"""
import subprocess
from pathlib import Path

OUT = Path("/opt/openclaw-hr/docs/PPT准备/企业规范示意")
SHOT = OUT / "截图"
CHROME = "/usr/bin/google-chrome"
COMPANY = "××科技有限公司"

DOCS = [
    {
        "key": "01-招聘管理制度",
        "no": "×科人〔2025〕3号",
        "title": "招聘管理制度",
        "date": "2025年3月10日",
        "dept": "人力资源部",
        "articles": [
            ("第一章 总则", None),
            ("第一条", "为满足公司业务发展需要，规范招聘流程，健全人才选用机制，根据《中华人民共和国劳动法》《中华人民共和国就业促进法》及相关法律法规，结合公司实际，制定本制度。"),
            ("第二条", "本制度适用于公司及下属分支机构全部岗位的招聘管理。"),
            ("第三条", "公司招聘坚持公开招聘、先内后外、平等竞争、人岗匹配的原则，不得设置与岗位无关的限制性条件。"),
            ("第二章 招聘职责", None),
            ("第四条", "人力资源部负责制定年度招聘计划、维护招聘渠道、组织简历筛选与面试，并为用人部门提供录用建议。"),
            ("第五条", "用人部门负责提出招聘需求、编制岗位说明书、参与专业面试，并对拟录用人选提出意见。"),
            ("第三章 招聘流程", None),
            ("第六条", "用人部门填写《人力资源需求申请表》，经部门负责人、人力资源部负责人、分管领导审批后，方可启动招聘。"),
            ("第八条", "招聘专员依据岗位说明书筛选简历，特殊岗位须与用人部门负责人共同确认初试名单。筛选记录应写明通过或不通过的原因。"),
            ("第十条", "对拟录用人员，人力资源部应在取得候选人书面同意后开展背景调查，核实证件与资料、工作经历、技能及业绩的真实性。背景调查不合格者不予录用。"),
            ("第四章 录用", None),
            ("第十二条", "录用决定以《面试评价及录用审批表》为依据，经用人部门负责人、人力资源部负责人及分管领导签批后生效，未经签批不得发放录用通知。"),
            ("第十三条", "应聘人员的简历及面试资料仅用于本次招聘。未录用人员资料保存期限为六个月，期满后予以删除。"),
            ("第五章 附则", None),
            ("第十五条", "本制度由人力资源部负责解释，自发布之日起施行。"),
        ],
        "highlight": ("第十条", "第十二条"),
    },
    {
        "key": "02-新员工入职管理办法",
        "no": "×科人〔2025〕9号",
        "title": "新员工入职管理办法",
        "date": "2025年6月18日",
        "dept": "人力资源部",
        "articles": [
            ("第一章 总则", None),
            ("第一条", "为规范新员工入职及试用期管理，帮助新员工尽快融入岗位，依据《中华人民共和国劳动合同法》及公司相关制度，制定本办法。"),
            ("第二章 职责分工", None),
            ("第三条", "人力资源部负责入职通知、资料核验、劳动合同签订、入职培训组织、档案建立及转正手续办理。"),
            ("第四条", "用人部门负责为新员工指定入职导师，制定试用期工作目标，开展试用期评估并提出转正意见。"),
            ("第五条", "信息部门负责办公账号与系统权限开通；行政部负责工位、工牌及办公设备准备。各部门应在新员工报到前完成准备。"),
            ("第三章 入职办理", None),
            ("第七条", "新员工报到当日，人力资源部应与其签订书面劳动合同及保密协议。劳动合同文本须经人力资源部负责人审核，由员工本人签字，不得代签。"),
            ("第八条", "系统账号及访问权限按岗位最小必要原则开通，须经用人部门负责人申请、信息部门审核后方可开通。"),
            ("第四章 试用期管理", None),
            ("第十一条", "试用期期限按劳动合同期限依法约定。人力资源部应在新员工入职第一周、第一个月及试用期中期开展跟进沟通，并做好记录。"),
            ("第十二条", "人力资源部应于试用期结束前十五个工作日提醒用人部门开展转正评估；转正、延长试用期或解除劳动合同的决定，由用人部门负责人、人力资源部负责人审批。"),
            ("第五章 附则", None),
            ("第十四条", "本办法自发布之日起施行。"),
        ],
        "highlight": ("第七条", "第十二条"),
    },
    {
        "key": "03-员工信息保密管理办法",
        "no": "×科人〔2025〕15号",
        "title": "员工信息保密管理办法",
        "date": "2025年9月1日",
        "dept": "人力资源部",
        "articles": [
            ("第一章 总则", None),
            ("第一条", "为保护员工个人信息与公司薪酬秘密，规范员工信息的收集、存储、查阅和使用，依据《中华人民共和国个人信息保护法》，制定本办法。"),
            ("第二条", "本办法所称员工信息，包括员工身份信息、人事档案、薪酬、考勤、绩效及健康等信息。"),
            ("第二章 信息分级", None),
            ("第四条", "员工信息分为共享信息、内部信息与保密信息三级。薪酬、绩效、健康及身份证件信息属于保密信息。"),
            ("第三章 查阅权限", None),
            ("第六条", "员工有权查阅本人信息；部门负责人可查阅本部门员工的内部信息；薪酬等保密信息仅限总经理、人力资源部负责人及薪酬专员查阅，其他查阅须经总经理授权。"),
            ("第七条", "因工作需要调用员工信息的，应填写《信息调用申请表》，说明用途，经审批后办理，并登记调用记录。"),
            ("第八条", "全体员工不得打听、传播他人薪酬信息。薪酬电子文档应加密存储，纸质资料专柜加锁保管。"),
            ("第四章 监督与责任", None),
            ("第十一条", "员工信息的查询、导出与调用记录保存不少于三年。违反本办法泄露员工信息的，按公司奖惩制度处理。"),
            ("第十二条", "本办法自发布之日起施行。"),
        ],
        "highlight": ("第六条", "第七条"),
    },
    {
        "key": "04-生成式人工智能工具使用管理规定（试行）",
        "no": "×科信〔2026〕2号",
        "title": "生成式人工智能工具使用管理规定（试行）",
        "date": "2026年4月20日",
        "dept": "信息部",
        "articles": [
            ("第一章 总则", None),
            ("第一条", "为规范员工在工作中使用生成式人工智能工具，防范数据泄露、侵权及错误输出风险，根据《中华人民共和国网络安全法》《中华人民共和国数据安全法》《中华人民共和国个人信息保护法》《生成式人工智能服务管理暂行办法》，结合公司实际，制定本规定。"),
            ("第二章 工具与数据", None),
            ("第四条", "员工仅可使用公司审批清单内的人工智能工具，工作账号由信息部统一开通，不得以个人账号处理工作内容。"),
            ("第五条", "禁止向人工智能工具输入公司保密信息、未公开的财务与合同信息、客户及员工个人信息；确需处理的，须先行去标识化并经部门负责人审批。"),
            ("第三章 输出与决策", None),
            ("第八条", "人工智能工具的输出仅作为工作参考，不得直接作为事实依据、审批意见或对外承诺；使用人应核对其准确性，并对最终使用结果负责。"),
            ("第九条", "涉及员工权益的事项，包括录用、劳动合同、绩效等级、薪酬调整等，不得由人工智能工具自动作出决定，须保留人工审核，审核人有权修改、否决或上报。"),
            ("第十条", "涉及员工权益的使用应留存记录，包括使用工具、时间、数据类别、复核人及最终处理结果。"),
            ("第四章 附则", None),
            ("第十三条", "本规定自发布之日起试行，由信息部会同人力资源部负责解释。"),
        ],
        "highlight": ("第八条", "第九条"),
    },
    {
        "key": "05-数字员工应用管理规定（试行）",
        "no": "×科信〔2026〕5号",
        "title": "数字员工应用管理规定（试行）",
        "date": "2026年6月8日",
        "dept": "信息部",
        "page_shot": True,
        "articles": [
            ("第一章 总则", None),
            ("第一条", "为规范数字员工（AI 智能体）在公司业务中的部署与使用，保障输出真实、决策可控、数据安全，依据《生成式人工智能服务管理暂行办法》及公司《生成式人工智能工具使用管理规定（试行）》，制定本规定。"),
            ("第二条", "本规定所称数字员工，是指经公司审批上线、可自主调用工具完成指定业务任务的人工智能智能体。"),
            ("第三条", "数字员工的上线、变更与下线由业务部门申请，信息部会同人力资源部审批，并指定业务责任人。"),
            ("第二章 授权与数据", None),
            ("第四条", "数字员工按岗位最小必要原则授权，仅可调用审批范围内的工具与数据，不得超出授权操作其他系统，不得自行扩大权限。"),
            ("第五条", "数字员工处理员工个人信息前应先行去标识化；薪酬、绩效等保密信息仅向经授权人员提供。"),
            ("第三章 输出与决策", None),
            ("第六条", "数字员工输出的数字、事实与结论应可追溯至原始材料；无法核实的内容不得作为业务依据。"),
            ("第七条", "数字员工任务失败、材料缺失或无法完成时，应如实报告，不得以推测内容补全，不得报告为已完成。"),
            ("第八条", "涉及录用、劳动合同、绩效等级、薪酬调整等员工权益的事项，由业务责任人审核决定，数字员工不得代为决定。"),
            ("第四章 监督与追溯", None),
            ("第九条", "业务责任人发现数字员工输出错误或越权操作的，有权立即暂停其运行，并报信息部处理。"),
            ("第十条", "数字员工的调用、数据访问及处理结果应留存记录，保存期限不少于三年，供审计查验。"),
            ("第五章 附则", None),
            ("第十二条", "本规定自发布之日起试行，由信息部会同人力资源部负责解释。"),
        ],
        "highlight": ("第四条", "第五条", "第六条", "第七条", "第八条", "第十条"),
    },
]

CSS = """
body{margin:0;background:#fff;font-family:"Noto Serif CJK SC","SimSun",serif;color:#1a1a1a}
.page{width:900px;margin:0 auto;padding:46px 90px 60px;box-sizing:border-box;background:#fff}
.red{color:#C8161D;text-align:center;font-size:44px;font-weight:700;letter-spacing:6px;margin:0}
.no{text-align:center;font-size:17px;margin:14px 0 8px;font-family:"Noto Sans CJK SC",sans-serif}
.line{border-top:3px solid #C8161D;margin:0 0 22px}
h1{text-align:center;font-size:27px;margin:0 0 6px;font-family:"Noto Sans CJK SC",sans-serif}
.date{text-align:center;font-size:15px;color:#555;margin-bottom:22px;font-family:"Noto Sans CJK SC",sans-serif}
h2{text-align:center;font-size:18px;margin:20px 0 10px;font-family:"Noto Sans CJK SC",sans-serif}
p{font-size:17px;line-height:1.85;text-indent:2em;margin:0 0 6px}
b{font-family:"Noto Sans CJK SC",sans-serif}
.hl{background:#FFF3B0}
.mask{display:inline-block;background:#222;color:#222;border-radius:2px}
"""


def body(doc, only=None):
    out = []
    for head, text in doc["articles"]:
        if text is None:
            if only is None:
                out.append(f"<h2>{head}</h2>")
            continue
        if only is not None and head not in only:
            continue
        cls = ' class="hl"' if head in doc.get("highlight", ()) else ""
        out.append(f"<p><span{cls}><b>{head}</b>　{text}</span></p>")
    return "\n".join(out)


def header(doc):
    return (
        f'<p class="red" style="text-indent:0">{COMPANY}文件</p>'
        f'<div class="no">{doc["no"]}</div><div class="line"></div>'
        f'<h1>{doc["title"]}</h1><div class="date">{doc["date"]}　{doc["dept"]}发布</div>'
    )


def html(inner, width=900):
    return f'<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8"><style>{CSS}</style></head><body><div class="page" style="width:{width}px">{inner}</div></body></html>'


def shoot(src: Path, png: Path, w: int, h: int):
    subprocess.run(
        [CHROME, "--headless=new", "--no-sandbox", "--disable-gpu", "--hide-scrollbars",
         "--force-device-scale-factor=2", f"--window-size={w},{h}", f"--screenshot={png}", src.as_uri()],
        check=True, capture_output=True,
    )


def trim(png: Path, pad: int = 24):
    from PIL import Image, ImageChops
    im = Image.open(png).convert("RGB")
    box = ImageChops.difference(im, Image.new("RGB", im.size, "white")).getbbox()
    if box:
        l, t, r, b = box
        im.crop((max(l - pad, 0), max(t - pad, 0), min(r + pad, im.width), min(b + pad, im.height))).save(png)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    SHOT.mkdir(exist_ok=True)
    for doc in DOCS:
        full = OUT / f"{doc['key']}.html"
        full.write_text(html(header(doc) + body(doc)), encoding="utf-8")
        subprocess.run(
            [CHROME, "--headless=new", "--no-sandbox", "--disable-gpu", "--no-pdf-header-footer",
             f"--print-to-pdf={OUT / (doc['key'] + '.pdf')}", full.as_uri()],
            check=True, capture_output=True,
        )
        if doc.get("page_shot"):
            tmp = SHOT / f"_{doc['key']}-全页.html"
            tmp.write_text(html(header(doc) + body(doc)), encoding="utf-8")
            shoot(tmp, SHOT / f"{doc['key']}-全页.png", 900, 1500)
            trim(SHOT / f"{doc['key']}-全页.png", 30)
            tmp.unlink()
        if doc.get("highlight"):
            tmp = SHOT / f"_{doc['key']}-条款.html"
            inner = f'<h1 style="font-size:24px">{doc["title"]}</h1>' + body(doc, only=doc["highlight"])
            tmp.write_text(html(inner, 1000).replace("padding:46px 90px 60px", "padding:22px 50px"), encoding="utf-8")
            shoot(tmp, SHOT / f"{doc['key']}-条款.png", 1000, 232)
            trim(SHOT / f"{doc['key']}-条款.png")
            tmp.unlink()
        tmp = SHOT / f"_{doc['key']}-抬头.html"
        tmp.write_text(html(header(doc)).replace("padding:46px 90px 60px", "padding:26px 90px"), encoding="utf-8")
        shoot(tmp, SHOT / f"{doc['key']}-抬头.png", 900, 262)
        tmp.unlink()
    print("ok", sorted(p.name for p in OUT.rglob("*") if p.is_file()))


if __name__ == "__main__":
    main()
