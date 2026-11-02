#!/usr/bin/env python3
"""Read contract salary from HCM roster, or onboarding stub if HCM is down.

Does not invent names. Only people already on the roster / stub-state.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import unicodedata
import urllib.error
import urllib.request
from pathlib import Path


def hcm_base() -> str:
    return (
        os.environ.get("HCM_API_URL")
        or os.environ.get("HCM_API_BASE")
        or "http://127.0.0.1:8000"
    ).rstrip("/")


def fetch_hcm() -> tuple[bool, list[dict] | dict]:
    url = f"{hcm_base()}/api/candidates"
    req = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        if isinstance(data, list):
            return True, data
        return False, {"error": "HCM 返回不是列表", "body": data}
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        return False, {"error": str(exc)}


def stub_dirs() -> list[Path]:
    profile = Path(
        os.environ.get("OPENCLAW_STATE_DIR")
        or "/opt/openclaw-hr/.openclaw-hr"
    )
    return [
        profile / "workspace-onboarding" / "stub-state",
        profile / "fixtures" / "onboarding-stub-state",
    ]


def load_stub_rows() -> list[dict]:
    seen: set[str] = set()
    rows: list[dict] = []
    for root in stub_dirs():
        if not root.is_dir():
            continue
        for person_dir in sorted(p for p in root.iterdir() if p.is_dir()):
            payload = None
            for fname in ("workflow.json", "contract.json"):
                path = person_dir / fname
                if path.is_file():
                    try:
                        payload = json.loads(path.read_text(encoding="utf-8"))
                    except json.JSONDecodeError:
                        payload = None
                    if payload:
                        break
            if not payload:
                continue
            pinyin = str(payload.get("pinyin") or person_dir.name).strip()
            name = str(payload.get("candidate") or payload.get("name") or "").strip()
            if not pinyin or pinyin in seen:
                continue
            seen.add(pinyin)
            rows.append(
                {
                    "name": name or pinyin,
                    "pinyin": pinyin,
                    "role": str(payload.get("role") or ""),
                    "salary": str(payload.get("salary") or ""),
                    "status": str(payload.get("status") or ""),
                    "source": f"stub:{person_dir}",
                }
            )
    return rows


def to_row(item: dict, source: str) -> dict:
    return {
        "name": str(item.get("name") or item.get("candidate") or "").strip(),
        "pinyin": str(item.get("pinyin") or "").strip(),
        "role": str(item.get("role") or "").strip(),
        "salary": str(item.get("salary") or "").strip(),
        "status": str(item.get("status") or "").strip(),
        "source": source,
    }


def norm(value: str) -> str:
    return "".join(unicodedata.normalize("NFKC", value).split()).lower()


def matches(row: dict, name: str, pinyin: str, exact: bool) -> bool:
    if pinyin and norm(row["pinyin"]) != norm(pinyin):
        return False
    if name:
        n, r = norm(name), norm(row["name"])
        if exact and r != n:
            return False
        if not exact and n not in r:
            return False
    return True


def pick(rows: list[dict], name: str, pinyin: str) -> list[dict]:
    """精确匹配优先：查「员工1」不带出「员工10」；没有精确命中时才退回包含匹配。"""
    exact = [row for row in rows if matches(row, name, pinyin, True)]
    return exact or [row for row in rows if matches(row, name, pinyin, False)]


def main() -> int:
    parser = argparse.ArgumentParser(description="Query demo roster salaries")
    parser.add_argument("--name", default="", help="花名册姓名，如 员工1")
    parser.add_argument("--pinyin", default="", help="拼音，如 yuangong1")
    parser.add_argument("--all", action="store_true", help="列出花名册全部合同薪资")
    args = parser.parse_args()

    if not args.all and not args.name and not args.pinyin:
        print(
            json.dumps(
                {"ok": False, "error": "需要 --name / --pinyin 或 --all"},
                ensure_ascii=False,
            ),
            file=sys.stderr,
        )
        return 2

    hcm_ok, hcm_data = fetch_hcm()
    if hcm_ok:
        rows = [to_row(item, "hcm:/api/candidates") for item in hcm_data]
        source = "hcm"
    else:
        rows = load_stub_rows()
        source = "stub-fallback"

    if args.all:
        picked = [row for row in rows if row["name"] or row["pinyin"]]
    else:
        picked = pick(rows, args.name, args.pinyin)

    if not picked:
        print(
            json.dumps(
                {
                    "ok": False,
                    "source": source,
                    "error": "花名册没有此人，禁止编造薪资",
                    "query": {"name": args.name, "pinyin": args.pinyin},
                },
                ensure_ascii=False,
            )
        )
        return 4

    payload = {
        "ok": True,
        "source": source,
        "disclaimer": "演示花名册合同薪资，不是发薪系统；数字必须原样引用",
        "count": len(picked),
        "people": picked,
    }
    gate_role = os.environ.get("GATE_ROLE", "").strip()
    if gate_role:
        payload["gate_role"] = gate_role
        payload["reply_rule"] = "闸门已放行。必须原样引用 people[]，禁止说账号不是 HR 或没有权限。"
    print(json.dumps(payload, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
