#!/usr/bin/env python3
"""红线关键词硬过滤：政策检索之前先跑，命中即必须转人工，不靠模型判断。

用法: redline-check.py <员工原话...>
输出一行 JSON（在检索结果之前）:
  {"redline": {"hit": false}}
  {"redline": {"hit": true, "must_escalate": true, "categories": [{"id": 3, "name": "…", "terms": ["…"]}], "note": "…"}}
退出码恒为 0；本脚本出错时 er-admin-run.sh 会中止，检索不运行，模型拿不到原文只能转人工。
命中记录写 logs/redline.log（只记类别和命中词，不记原话）。
"""
import json
import os
import re
import sys
import time
import unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

RULES = [
    (1, '涉及个人具体金额/数据', [
        r'我(的|这个月|上个月|本月|今年|去年).{0,6}(工资|薪资|薪水|工资条|奖金|个税|社保|公积金|考勤|扣款)',
        r'(工资|薪资|奖金|社保|公积金).{0,4}(少了|少发|没发|扣了)',
        r'扣了?我',
        r'年假.{0,2}(还剩|剩余|余额|剩几)',
        r'我.{0,4}(还剩|剩余).{0,4}(年假|假期|调休)',
    ]),
    (2, '个案争议', [
        r'不服', r'不合理', r'不公平', r'有异议', r'偏见', r'针对我', r'凭什么', r'冤枉',
    ]),
    (3, '法律纠纷/劳动仲裁', [
        r'劳动仲裁', r'仲裁', r'违法', r'合法', r'起诉', r'律师', r'法院', r'劳动监察',
        r'工伤认定', r'经济补偿', r'赔偿', r'n\+1', r'2n', r'维权', r'克扣',
    ]),
    (5, '需要决策审批', [
        r'特批', r'破例', r'通融', r'能不能批', r'能否批', r'可以批', r'提前转正', r'特殊安排', r'例外处理',
    ]),
]
COMPILED = [(cid, name, [re.compile(p) for p in pats]) for cid, name, pats in RULES]


def normalize(text):
    text = unicodedata.normalize('NFKC', text)
    return re.sub(r'\s+', '', text).lower()


def check(text):
    t = normalize(text)
    cats = []
    for cid, name, pats in COMPILED:
        terms = sorted({m.group(0) for p in pats for m in [p.search(t)] if m})
        if terms:
            cats.append({'id': cid, 'name': name, 'terms': terms})
    if not cats:
        return {'hit': False}
    return {
        'hit': True,
        'must_escalate': True,
        'categories': cats,
        'note': '关键词硬命中：上面这几类必须明确转人工，不论语义判断结果；政策能答的通用部分照常答并标出处。',
    }


def log(res):
    if not res['hit']:
        return
    os.makedirs(os.path.join(ROOT, 'logs'), exist_ok=True)
    cats = ';'.join(f"{c['id']}:{','.join(c['terms'])}" for c in res['categories'])
    with open(os.path.join(ROOT, 'logs', 'redline.log'), 'a', encoding='utf-8') as f:
        f.write(f"{time.strftime('%Y-%m-%dT%H:%M:%S%z')}\tredline\t{cats}\n")


if __name__ == '__main__':
    res = check(' '.join(sys.argv[1:]))
    log(res)
    print(json.dumps({'redline': res}, ensure_ascii=False))
