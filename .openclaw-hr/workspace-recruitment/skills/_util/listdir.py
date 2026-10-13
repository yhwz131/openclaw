#!/usr/bin/env python3
"""Read-only directory lister for workspace-recruitment (helper, not a business skill).

Usage: bash scripts/recruitment-run.sh python3 skills/_util/listdir.py <相对目录> [glob]
只读列出本 workspace 内目录文件名，不做任何修改。
"""
import sys
import os
from pathlib import Path

WS = Path(__file__).resolve().parents[2]


def main() -> int:
    if len(sys.argv) < 2:
        print("用法: listdir.py <相对目录> [glob]", file=sys.stderr)
        return 2
    rel = sys.argv[1]
    pattern = sys.argv[2] if len(sys.argv) > 2 else "*"
    target = (WS / rel).resolve()
    if not str(target).startswith(str(WS)):
        print("拒绝: 路径超出本 workspace", file=sys.stderr)
        return 1
    if not target.exists():
        print(f"不存在: {target}")
        return 0
    if target.is_file():
        print(f"[file] {target.relative_to(WS)}")
        return 0
    entries = sorted(target.glob(pattern))
    for p in entries:
        kind = "dir " if p.is_dir() else "file"
        print(f"{kind} {p.relative_to(WS)}")
    print(f"({len(entries)} 项)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
