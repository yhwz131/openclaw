#!/usr/bin/env python3
"""红线关键词硬过滤验收：该命中的必须命中对应类别，常规政策问题不许误报。
用法: python3 demo/acceptance/redline.py
"""
import importlib.util, os

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location('rl', os.path.join(HERE, '..', '..', 'scripts', 'redline-check.py'))
rl = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rl)

CASES = [
    ('现场演示 · 年假', '我入职满3年了，年假有几天？', set()),
    ('评测 1 · 年假清零', '年假今年没休完会清零吗？', set()),
    ('评测 2 · 试用期社保', '试用期公司给我交社保公积金吗？缴存比例多少？', set()),
    ('常规 · 加班餐', '加班餐能不能报销？', set()),
    ('常规 · 出差住宿', '出差住宿标准是多少？', set()),
    ('常规 · 补卡', '打卡忘了怎么补卡？', set()),
    ('常规 · 发薪日', '公司每个月几号发工资？', set()),
    ('常规 · 绩效申诉流程', '绩效申诉的流程是什么？', set()),
    ('现场演示 · 维权', '加班20小时没有加班费，这是违法克扣吧？怎么维权？', {3}),
    ('评测 3 · 工资少了', '我这个月到手工资比上个月少了 800 块，但我没请假也没迟到，是不是算错了？帮我查一下。', {1}),
    ('评测 4 · 辞退仲裁', '我主管说我这次绩效是 C，要把我辞退，说是不能胜任工作。这合法吗？我能拿到 N+1 赔偿吗？我想去劳动仲裁。', {3}),
    ('第 1 类 · 年假余额', '我年假还剩几天？', {1}),
    ('第 1 类 · 个税', '我的个税扣了多少？', {1}),
    ('第 2 类 · 绩效不服', '我绩效被打 C，我觉得不合理，主管对我有偏见', {2}),
    ('第 5 类 · 特批', '这次出差超标了能不能特批？', {5}),
    ('第 5 类 · 提前转正', '我能不能提前转正？', {5}),
    ('全角写法', '这样辞退我合法吗？Ｎ＋１还是２Ｎ？', {3}),
]

ok = 0
for name, q, expect in CASES:
    res = rl.check(q)
    got = {c['id'] for c in res.get('categories', [])}
    pass_ = expect <= got if expect else not got
    ok += pass_
    terms = '；'.join(f"{c['id']}:{','.join(c['terms'])}" for c in res.get('categories', []))
    print(f"{'✓' if pass_ else '✗'}  {'命中 ' + terms if got else '不命中'}  {name}")
print(f'\n红线硬过滤：{len(CASES)} 条，符合预期 {ok} 条')
raise SystemExit(0 if ok == len(CASES) else 1)
