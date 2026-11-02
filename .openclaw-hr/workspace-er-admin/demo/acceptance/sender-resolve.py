#!/usr/bin/env python3
"""身份反查验收：在临时目录里造会话记录，验证闸门取的是网关记录的发送人，不是模型传的 --sender。
用法: python3 demo/acceptance/sender-resolve.py
"""
import importlib.util, json, os, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location('rs', os.path.join(HERE, '..', '..', 'scripts', 'resolve-sender.py'))
rs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rs)

EMP = 'ou_' + 'e' * 32
HR = 'ou_' + 'a' * 32
RUN = 'bash scripts/er-admin-run.sh '

d = tempfile.mkdtemp(prefix='sender-resolve-')
rs.SESS_DIR = d
json.dump({
    f'agent:er-admin:feishu:direct:{EMP}': {'sessionId': 'emp', 'origin': {'provider': 'feishu', 'from': f'feishu:{EMP}'}},
    f'agent:er-admin:feishu:direct:{HR}': {'sessionId': 'hr', 'origin': {'provider': 'feishu', 'from': f'feishu:{HR}'}},
    'agent:er-admin:explicit:local': {'sessionId': 'local', 'origin': None},
}, open(os.path.join(d, 'sessions.json'), 'w'))


def sessions(emp=(), hr=(), local=(), hr_done=False):
    for sid, cmds in (('emp', emp), ('hr', hr), ('local', local)):
        with open(os.path.join(d, f'{sid}.jsonl'), 'w') as f:
            for i, c in enumerate(cmds):
                f.write(json.dumps({'message': {'role': 'assistant', 'content': [
                    {'type': 'toolCall', 'id': f'{sid}{i}', 'name': 'exec', 'arguments': {'command': RUN + c}}]}}) + '\n')
                if sid == 'hr' and hr_done:
                    f.write(json.dumps({'message': {'role': 'toolResult', 'toolCallId': f'{sid}{i}'}}) + '\n')


def argv(c):
    return c.split()


forged = f'payroll-query --sender {HR} --name 员工1'
CASES = [
    ('员工伪造 HR 的 --sender', dict(emp=[forged]), forged, {'status': 'feishu', 'sender': EMP}),
    ('员工让模型不传 --sender', dict(emp=['payroll-query --name 员工1']), 'payroll-query --name 员工1', {'status': 'feishu', 'sender': EMP}),
    ('HR 正常查询', dict(hr=[forged]), forged, {'status': 'feishu', 'sender': HR}),
    ('员工伪造时 HR 恰好同句在查', dict(emp=[forged], hr=[forged]), forged, {'status': 'ambiguous'}),
    ('本地会话（WebChat / CLI）', dict(local=['payroll-query --name 员工1'], hr=['payroll-query --name 员工1'], hr_done=True),
     'payroll-query --name 员工1', {'status': 'local'}),
    ('会话记录里找不到这条命令', dict(), 'payroll-query --name 员工1', {'status': 'notfound'}),
]

ok = 0
for name, sess, cmd, expect in CASES:
    sessions(**sess)
    got = rs.main(argv(cmd))
    pass_ = all(got.get(k) == v for k, v in expect.items())
    ok += pass_
    who = {EMP: '员工', HR: 'HR'}.get(got.get('sender'), '')
    print(f"{'✓' if pass_ else '✗'}  {got['status']}{(' · ' + who) if who else ''}  {name}")
print(f'\n身份反查：{len(CASES)} 条，符合预期 {ok} 条')
raise SystemExit(0 if ok == len(CASES) else 1)
