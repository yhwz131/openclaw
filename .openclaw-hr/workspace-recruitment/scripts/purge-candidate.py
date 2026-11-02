#!/usr/bin/env python3
"""清理招聘主链 1（收简历 → 解析 → 回核 → 脱敏 → 评分 → 画像）的落盘物。

用法：
  python3 scripts/purge-candidate.py 员工10            # 只列出会删什么
  python3 scripts/purge-candidate.py 员工10 员工3 --yes
  python3 scripts/purge-candidate.py --all --yes        # 主链全部落盘物，含 ranking

按人匹配规则：简历名 stem 等于「姓名」或以「姓名-」开头，所以 员工1 不会误删 员工10。
不碰：人才库 talent-pool/、面试纪要、jds/、邮箱里的邮件（已标 \\Seen 的不会恢复未读）。
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROFILE = ROOT.parent
INBOX = ROOT / "inbox"
CANVAS_DOCS = PROFILE / "canvas" / "documents"
LEDGERS = (".fetched-mail.jsonl", "needs-hr.jsonl", "needs-pipeline.jsonl")


def belongs(stem: str, name: str) -> bool:
    return stem == name or stem.startswith(name + "-")


def inbox_stems(name: str) -> set[str]:
    stems = set()
    if INBOX.is_dir():
        for p in INBOX.iterdir():
            if p.name.startswith(".") or not p.is_file():
                continue
            stem = p.name.split(".", 1)[0]
            if belongs(stem, name):
                stems.add(stem)
    return stems


def files_for(name: str) -> list[Path]:
    stems = inbox_stems(name)
    out: list[Path] = []

    def add_matching(d: Path, prefix: str = "") -> None:
        if not d.is_dir():
            return
        for p in d.iterdir():
            if not p.is_file() or not p.name.startswith(prefix):
                continue
            stem = p.name[len(prefix):].split(".", 1)[0]
            if belongs(stem, name) or stem in stems:
                out.append(p)

    add_matching(INBOX)
    add_matching(ROOT / "parsed")
    add_matching(ROOT / "audited")
    for prefix in ("clean-", "score-", "audit-numbers-"):
        add_matching(ROOT / "scoring", prefix)
    add_matching(ROOT / "profile" / "output", "profile-")
    return sorted(set(out))


def canvas_dirs_for(name: str) -> list[Path]:
    hits = []
    marker = f"<title>候选人画像 · {name}</title>"
    if CANVAS_DOCS.is_dir():
        for d in CANVAS_DOCS.glob("profile-*"):
            idx = d / "index.html"
            if idx.is_file() and marker in idx.read_text(encoding="utf-8", errors="ignore"):
                hits.append(d)
    return sorted(hits)


def all_names() -> set[str]:
    names = set()
    if INBOX.is_dir():
        for p in INBOX.iterdir():
            if p.is_file() and not p.name.startswith("."):
                names.add(p.name.split(".", 1)[0].split("-", 1)[0])
    for p in (ROOT / "profile" / "output").glob("profile-*.html"):
        names.add(p.stem[len("profile-"):].split("-", 1)[0])
    return names


def ledger_mentions(saved_names: set[str], names: list[str], path: Path) -> tuple[list[str], int]:
    if not path.is_file():
        return [], 0
    keep, dropped = [], 0
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            keep.append(line)
            continue
        files = {f.get("saved_name") for f in rec.get("saved_files", []) if isinstance(f, dict)}
        for key in ("saved_name", "file", "name"):
            if isinstance(rec.get(key), str):
                files.add(rec[key])
        hit = bool(files & saved_names) or any(
            isinstance(f, str) and belongs(f.split(".", 1)[0], n) for f in files for n in names
        )
        if hit:
            dropped += 1
        else:
            keep.append(line)
    return keep, dropped


def main() -> int:
    ap = argparse.ArgumentParser(description="清理招聘主链落盘物（默认只预览）")
    ap.add_argument("names", nargs="*", help="候选人姓名，如 员工10")
    ap.add_argument("--all", action="store_true", help="清理主链全部候选人，并删 scoring/results 下的 ranking")
    ap.add_argument("--yes", action="store_true", help="真的删除；不加只列清单")
    args = ap.parse_args()

    if not args.names and not args.all:
        ap.error("给出候选人姓名，或用 --all")
    names = sorted(all_names()) if args.all else args.names

    files: list[Path] = []
    canvas: list[Path] = []
    for n in names:
        files += files_for(n)
        canvas += canvas_dirs_for(n)
    if args.all:
        results = ROOT / "scoring" / "results"
        if results.is_dir():
            files += [p for p in results.iterdir() if p.is_file()]
    files = sorted(set(files))
    canvas = sorted(set(canvas))

    ident_path = INBOX / ".identity.json"
    ident = json.loads(ident_path.read_text(encoding="utf-8")) if ident_path.is_file() else {}
    saved_names = {p.name for p in files if p.parent == INBOX}
    ident_drop = [k for k in ident if k in saved_names or any(belongs(k.split(".", 1)[0], n) for n in names)]

    ledger_plan = {}
    for lname in LEDGERS:
        keep, dropped = ledger_mentions(saved_names, names, INBOX / lname)
        if dropped:
            ledger_plan[lname] = (keep, dropped)

    print(f"候选人：{'、'.join(names) if names else '（无）'}")
    for p in files:
        print(f"  删除文件  {p.relative_to(PROFILE)}")
    for d in canvas:
        print(f"  删除目录  {d.relative_to(PROFILE)}/")
    for k in ident_drop:
        print(f"  登记移除  inbox/.identity.json → {k}")
    for lname, (_, dropped) in ledger_plan.items():
        print(f"  记录移除  inbox/{lname} → {dropped} 行")
    if not (files or canvas or ident_drop or ledger_plan):
        print("  没有找到主链落盘物")
        return 0

    if not args.yes:
        print("\n预览模式，未删除。确认后加 --yes。")
        return 0

    for p in files:
        p.unlink(missing_ok=True)
    for d in canvas:
        shutil.rmtree(d, ignore_errors=True)
    if ident_drop:
        for k in ident_drop:
            ident.pop(k, None)
        ident_path.write_text(json.dumps(ident, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for lname, (keep, _) in ledger_plan.items():
        (INBOX / lname).write_text("".join(l + "\n" for l in keep), encoding="utf-8")
    print("\n已删除。邮箱里的原邮件仍是已读；要重跑收信，需在邮箱里把它标回未读。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
