from pathlib import Path

B = Path('/opt/openclaw-hr/.openclaw-hr')
W = B / 'workspace-er-admin'


def line_of(path, needle):
    for i, line in enumerate(path.read_text(encoding='utf-8').splitlines(), 1):
        if needle in line:
            return i
    raise SystemExit(f'{path} 里找不到 {needle!r}')


CONF = B / 'config/openclaw.yaml'
BIND = line_of(CONF, '"bindings": [')
ERA = line_of(CONF, '"id": "er-admin",') - 1
OUT = Path('/opt/openclaw-hr/docs/PPT准备/行政-有据分权-原文摘录.md')

LANG = {'.md': 'markdown', '.sh': 'bash', '.py': 'python', '.cjs': 'javascript', '.json': 'json', '.yaml': 'json'}


def block(path, a, b, why):
    lines = path.read_text(encoding='utf-8').splitlines()
    b = min(b, len(lines))
    body = '\n'.join(f'{i:>4}  {lines[i - 1]}' for i in range(a, b + 1))
    rel = path.relative_to(B)
    whole = '（全文）' if a == 1 and b == len(lines) else f'第 {a}–{b} 行'
    return f'#### `{rel}` · {whole}\n\n{why}\n\n````{LANG.get(path.suffix, "")}\n{body}\n````\n'


YOUJU = [
    ('Agent', [
        (W / 'AGENTS.md', 124, 138, '行政业务工作流：政策答疑走 Skill，三步协议；“检索得到 ≠ 该回答”。'),
        (W / 'SOUL.md', 34, 55, 'HR Helpdesk 照 Skill 走；红线中与“有据”相关的条目（引原文、检索不到转人工、数字不改、政策原文不另存）。'),
    ]),
    ('Skill', [
        (W / 'skills/answering-hr-policy-questions/SKILL.md', 1, 92, '制度答疑 Skill 全文：description 里写明禁止用常识答、必须引出处、五类硬停；三步协议；关键规则。'),
        (W / 'skills/answering-hr-policy-questions/references/escalation-redlines.md', 1, 74, '五类红线细则全文。'),
    ]),
    ('Script', [
        (W / 'skills/answering-hr-policy-questions/scripts/search_ima_policies.cjs', 559, 587, '检索脚本收尾：无命中给出“禁止用通用知识硬答”的 warning，并以退出码 1 结束。'),
        (W / 'scripts/redline-check.py', 1, 80, '红线关键词硬过滤全文：检索之前运行，命中即 must_escalate，记 logs/redline.log（只记类别和命中词）。'),
        (W / 'scripts/er-admin-run.sh', 72, 75, '入口脚本里的 ima-search 分支：先跑红线硬过滤，再检索；制度检索不过身份闸门。'),
        (W / 'demo/acceptance/redline.py', 1, 50, '红线硬过滤验收用例：17 条，既测该命中的类别，也测常规政策问题不误报。'),
    ]),
]

FENQUAN = [
    ('Agent', [
        (W / 'AGENTS.md', 53, 61, 'Red Lines：业务 exec 只走 er-admin-run.sh；飞书必须把会话 ou_ 传给 --sender；禁止用 exec 绕过 write。'),
        (W / 'AGENTS.md', 138, 160, '花名册合同薪资、HR 月报：哪些身份能用，飞书非 HR 拒绝。'),
        (W / 'SOUL.md', 13, 32, '“谁能查敏感数据”：两类敏感数据、身份表；身份以网关会话记录为准。'),
        (W / 'SOUL.md', 56, 56, '红线：业务 exec 只走入口脚本。'),
    ]),
    ('配置（网关层，供核对）', [
        (CONF, BIND, BIND + 7, 'bindings：行政的飞书账号 admin 绑定到 er-admin。'),
        (CONF, ERA, ERA + 133, 'er-admin 的工具配置：默认 allow/deny、仅限 workspace、toolsBySender 按飞书发送人发工具、不允许调子 Agent。'),
        (B / 'exec-approvals.json', 39, 53, 'er-admin 的 exec 白名单：只放 er-admin-run.sh；ask off，askFallback deny。'),
    ]),
    ('Skill', [
        (W / 'skills/querying-employee-payroll/SKILL.md', 1, 49, '花名册查询 Skill 全文：只走壳脚本、ou_ 原样传、脚本以网关记录为准、不编数字、不写 HCM。'),
    ]),
    ('Script', [
        (W / 'scripts/er-admin-run.sh', 1, 100, '唯一 exec 入口全文：extract_sender → resolve_sender（认人，写 gate-verify.log）→ require_hr_data（判权，失败 exit 3）→ 才执行查询脚本。'),
        (W / 'scripts/resolve-sender.py', 1, 89, '认人全文：从网关会话记录反查这条命令是谁发起的，不信模型传的 --sender。'),
        (W / 'scripts/hr-data-access.sh', 1, 68, '判权全文：归一化发送人 → 分四类（demo / hr / denied / unknown）→ hr|demo 放行 exit 0，其余 exit 3。'),
        (W / 'skills/querying-employee-payroll/scripts/query_payroll.py', 1, 36, '过闸之后的读数据：只对 HCM 发 GET，不写。'),
    ]),
]

parts = ['''# 行政 · 有据与分权：原文摘录（未压缩）

用途：给导师逐条核对“有据”“分权”在代码里到底写了什么。所有片段由脚本按行号从原件原样摘出，左侧数字是原件行号，未改一个字。

根目录：`/opt/openclaw-hr/.openclaw-hr/`（下文路径均相对于它）。

结构：先“有据”，再“分权”；每部分按 Agent（AGENTS.md / SOUL.md）→ Skill（SKILL.md 及其 references）→ Script 排列。分权多一组网关配置，因为“按人发工具”“执行白名单”写在配置里，不在 .md 里。

''']
for title, groups in (('一、有据', YOUJU), ('二、分权', FENQUAN)):
    parts.append(f'## {title}\n')
    for g, items in groups:
        parts.append(f'### {g}\n')
        for it in items:
            parts.append(block(*it))
OUT.write_text('\n'.join(parts), encoding='utf-8')
print(OUT, OUT.stat().st_size)
