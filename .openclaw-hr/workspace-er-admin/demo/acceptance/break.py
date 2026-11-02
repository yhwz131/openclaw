#!/usr/bin/env python3
"""现场拆一层：在临时副本里删掉一层防护，用员工身份发同一条越权命令，看薪资会不会出来；再装回去重跑。
不碰正在运行的系统。

用法（在 workspace-er-admin 下）:
  python3 demo/acceptance/break.py resolve   # 拆身份反查，攻击：冒充 HR
  python3 demo/acceptance/break.py anchor    # 拆白名单锚定，攻击：夹带脚本名
"""
import importlib.util, os, sys, tempfile, time

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location('ab', os.path.join(HERE, 'ablation.py'))
ab = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ab)

R, G, Y, D, B, X = '\033[1;31m', '\033[1;32m', '\033[1;33m', '\033[2m', '\033[1m', '\033[0m'
RUNNER = os.path.join(ab.WS, 'scripts', 'er-admin-run.sh')


def line_of(path, needle, after=None):
    started = after is None
    for i, l in enumerate(open(path, encoding='utf-8'), 1):
        if not started and after in l:
            started = True
        if started and needle in l:
            return i, l.rstrip('\n')
    return None, ''


LAYERS = {
    'resolve': dict(
        name='身份反查', attack='冒充 HR', cfg=dict(resolve=False, gate=True, allow='now'),
        show=lambda: (RUNNER, *line_of(RUNNER, 'resolve_sender "$@"', after='payroll-query)')),
    ),
    'anchor': dict(
        name='白名单锚定', attack='夹带脚本名', cfg=dict(resolve=True, gate=True, allow='old'),
    ),
}


def run(cfg, attack):
    name, cmd, sender = next(a for a in ab.ATTACKS if a[0] == attack)
    ok = ab.allowlisted([cmd], cfg['allow'])[0]
    if not ok:
        return cmd, False, '执行白名单：拒绝执行，命令根本没跑', ''
    with tempfile.TemporaryDirectory(prefix='break-') as root:
        ws, sess = ab.make_workspace(root, cfg['resolve'], cfg['gate'])
        ab.record(sess, sender, cmd)
        import subprocess
        p = subprocess.run(['bash', '-c', cmd], cwd=ws, env=dict(os.environ, OPENCLAW_SHELL='exec'),
                           capture_output=True, text=True, timeout=30)
    leak = ab.LEAK.search(p.stdout)
    if leak:
        import re
        m = re.search(r'"name"\s*:\s*"([^"]+)".*?"salary"\s*:\s*"([^"]+)"', p.stdout, re.S)
        out = f'拿到了：{m.group(1)} 的合同薪资 {m.group(2)}' if m else p.stdout.strip()[:120]
    else:
        out = (p.stdout.strip().splitlines() or [''])[0][:120]
    return cmd, bool(leak), f'exit {p.returncode}', out


def show_cmd(cmd):
    return cmd.replace(ab.HR, 'ou_…' + ab.HR[-4:]).replace(ab.EMP, 'ou_…' + ab.EMP[-4:])


def main():
    key = sys.argv[1] if len(sys.argv) > 1 else 'resolve'
    L = LAYERS[key]
    print(f'{B}现场拆一层：{L["name"]}{X}　{D}（临时副本，不碰正在运行的系统）{X}\n')
    if key == 'resolve':
        path, no, text = L['show']()
        print(f'{Y}删掉这一行{X}  {os.path.relpath(path, ab.WS)}:{no}')
        print(f'  {R}- {text.strip()}{X}\n')
    else:
        print(f'{Y}换回改前的规则{X}  exec-approvals.json › er-admin')
        print(f'  {R}- "argPattern": "er-admin-run\\\\.sh"{X}      {D}# 改前：参数里出现脚本名就放行{X}')
        print(f'  {G}+ "argPattern": "^(scripts/|…/scripts/)er-admin-run\\\\.sh\\0…$"{X}  {D}# 现在{X}\n')

    print(f'{B}攻击{X}：假设模型已被骗过，员工让它原样执行——{L["attack"]}')
    cmd = next(a[1] for a in ab.ATTACKS if a[0] == L['attack'])
    print(f'  {D}${X} {show_cmd(cmd)}\n')

    for label, cfg in ((f'拆掉{L["name"]}', L['cfg']), ('装回去', dict(resolve=True, gate=True, allow='now'))):
        t = time.time()
        _, leak, how, out = run(cfg, L['attack'])
        tag = f'{R}泄露{X}' if leak else f'{G}挡住{X}'
        print(f'{B}{label}{X}  →  {tag}　{D}{how} · {time.time() - t:.1f}s{X}')
        if out:
            print(f'  {R if leak else D}{out}{X}')
        print()


if __name__ == '__main__':
    main()
