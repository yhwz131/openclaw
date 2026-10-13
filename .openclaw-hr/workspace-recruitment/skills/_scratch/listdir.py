#!/usr/bin/env python3
# 临时目录查看工具（用完自删）：python3 skills/_scratch/listdir.py [root] [--deep]
# python3 skills/_scratch/listdir.py --purge  # 删除本脚本
import os
import sys

SELF = os.path.abspath(__file__)


def main():
    args = [a for a in sys.argv[1:]]
    if "--purge" in args:
        os.remove(SELF)
        try:
            os.rmdir(os.path.dirname(SELF))
        except OSError:
            pass
        print("purged")
        return 0
    deep = "--deep" in args
    roots = [a for a in args if not a.startswith("--")] or ["."]
    skip = {".git", "node_modules", "models", "__pycache__", ".venv"}
    for root in roots:
        for dirpath, dirnames, filenames in os.walk(root):
            rel = os.path.relpath(dirpath, ".")
            depth = 0 if rel == "." else rel.count(os.sep) + 1
            dirnames[:] = [d for d in sorted(dirnames) if d not in skip]
            if not deep and depth >= 2:
                dirnames[:] = []
            for f in sorted(filenames):
                p = os.path.join(rel, f) if rel != "." else f
                try:
                    size = os.path.getsize(p)
                except OSError:
                    size = -1
                print(f"{size:>10}  {p}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
