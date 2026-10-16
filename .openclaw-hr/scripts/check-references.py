#!/usr/bin/env python3
"""检查各 Agent 的提示词、Skill、脚本、配置里引用的脚本文件是否真实存在。

用法：python3 scripts/check-references.py [--json]
缺失即退出码 1，可接在 pre-commit 和冒烟测试里。
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXT = r'(?:py|js|cjs|mjs|sh|lobster)'
TOKEN = re.compile(r'(?<![\w$<{*.-])((?:\.{1,2}/|/opt/)?[\w\-./\u4e00-\u9fff]*[\w\-]+\.' + EXT + r')(?![\w])')
SKIP_DIRS = {'node_modules', '.git', '__pycache__', 'memory', 'output', 'demo-backup', '.demo-backup', 'sessions', 'logs'}
TEXT_NAMES = {'AGENTS.md', 'SOUL.md', 'TOOLS.md', 'SKILL.md', 'HEARTBEAT.md'}


def sources():
    for ws in sorted(ROOT.glob('workspace*')):
        if not ws.is_dir():
            continue
        for p in ws.rglob('*'):
            if any(part in SKIP_DIRS for part in p.relative_to(ws).parts) or not p.is_file():
                continue
            if p.name in TEXT_NAMES or (p.suffix in {'.sh', '.lobster'} and 'scripts' in p.parts or p.suffix == '.lobster'):
                yield ws, p
    for p in [ROOT / 'config/openclaw.yaml', ROOT / 'exec-approvals.json', ROOT / 'cron/jobs.json']:
        if p.exists():
            yield None, p


def candidates(ws, src, ref):
    if ref.startswith('/'):
        return [Path(ref)]
    out = [src.parent / ref]
    if ws:
        out.append(ws / ref)
        for parent in src.parents:
            if parent == ws:
                break
            if (parent / 'SKILL.md').exists():
                out.append(parent / ref)
                out.append(parent / 'scripts' / ref)
    out.append(ROOT / ref)
    return out


ALLOW_FILE = Path(__file__).with_suffix('.allow')
ALLOW = [l.split('#')[0].strip() for l in ALLOW_FILE.read_text(encoding='utf-8').splitlines()
         if l.split('#')[0].strip()] if ALLOW_FILE.exists() else []

INDEX = {}


def indexed(base):
    if base not in INDEX:
        INDEX[base] = [str(p.relative_to(base)) for p in base.rglob('*')
                       if p.is_file() and not any(x in SKIP_DIRS - {'output'} for x in p.relative_to(base).parts)]
    return INDEX[base]


def found_by_suffix(ws, ref):
    ref = ref.lstrip('./').lstrip('/')
    for base in ([ws] if ws else []) + [ROOT / 'scripts']:
        for rel in indexed(base):
            if rel == ref or rel.endswith('/' + ref):
                return True
    return (ROOT / 'scripts' / Path(ref).name).exists() and ref.startswith('scripts/')


def main():
    missing = []
    checked = 0
    for ws, src in sources():
        text = src.read_text(encoding='utf-8', errors='ignore')
        for ln, line in enumerate(text.splitlines(), 1):
            for m in TOKEN.finditer(line):
                ref = m.group(1)
                if ref.startswith(('http', 'www.', '.claude/')) or '/tmp/' in ref or '/.../' in ref or 'example' in ref:
                    continue
                if any(ref.endswith(a) for a in ALLOW):
                    continue
                checked += 1
                if not any(c.exists() for c in candidates(ws, src, ref)) and not found_by_suffix(ws, ref):
                    missing.append({'file': str(src.relative_to(ROOT)), 'line': ln, 'ref': ref})
    if '--json' in sys.argv:
        print(json.dumps({'checked': checked, 'missing': missing}, ensure_ascii=False, indent=1))
    else:
        for m in missing:
            print(f"缺失  {m['ref']:<60} ← {m['file']}:{m['line']}")
        print(f'共检查 {checked} 处引用，缺失 {len(missing)} 处')
    return 1 if missing else 0


if __name__ == '__main__':
    sys.exit(main())
