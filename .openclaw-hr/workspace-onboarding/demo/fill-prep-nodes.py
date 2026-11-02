#!/usr/bin/env python3
"""按部门身份，把一名候选人的 HCM 准备节点标成已完成并回填内容。

给现场配合用：1 号在 HCM 里逐个部门点的事，这条命令一次做完。
每个节点仍带对应的 X-Department-Role，和页面上切换部门后保存是同一条接口。

用法（在本目录，或任意目录）:
  python3 fill-prep-nodes.py                  # 看员工10现在五节点
  python3 fill-prep-nodes.py fill             # 五节点全部：完成 + 回填
  python3 fill-prep-nodes.py fill contract    # 只做合同（hr）
  python3 fill-prep-nodes.py show 员工2

节点名可用: contract/hr/合同  account/it/账号  device/admin/设备
            training/培训  buddy/用人部门
只替换空值、以及占位的「1」「未填」。已有正式内容时不覆盖，除非加 --force。
"""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timedelta

BASE = (
    os.environ.get("HCM_API_URL")
    or os.environ.get("HCM_API_BASE")
    or "http://127.0.0.1:8000"
).rstrip("/")

# 节点 → 部门角色（与 HCM ROLE_TO_NODE 一致）
NODES = (
    ("contract", "hr", "合同签署"),
    ("account", "it", "IT账号"),
    ("device", "admin", "行政设备"),
    ("training", "training", "入职培训"),
    ("buddy", "buddy", "Buddy匹配"),
)
ALIAS = {
    "contract": "contract", "hr": "contract", "合同": "contract", "合同签署": "contract",
    "account": "account", "it": "account", "账号": "account", "it账号": "account",
    "device": "device", "admin": "device", "设备": "device", "行政": "device", "行政设备": "device",
    "training": "training", "培训": "training", "入职培训": "training",
    "buddy": "buddy", "用人部门": "buddy", "导师": "buddy",
}
PLACEHOLDERS = {"", "1", "未填", "待填", "无", "暂无"}
LABELS = {
    "role": "岗位", "salary": "薪资", "contract": "合同", "files": "配套文件", "probation": "试用期",
    "workno": "工号", "email": "邮箱", "wecom": "企业微信", "vpn": "VPN",
    "laptop": "电脑", "badge": "门禁", "desk": "工位",
    "course": "课程", "date": "时间", "content": "内容",
    "buddy": "Buddy", "mentor": "导师",
}


def request(method: str, path: str, body=None, role: str | None = None):
    data = None if body is None else json.dumps(body, ensure_ascii=False).encode()
    req = urllib.request.Request(BASE + path, data=data, method=method)
    req.add_header("Accept", "application/json")
    if body is not None:
        req.add_header("Content-Type", "application/json")
    if role:
        req.add_header("X-Department-Role", role)
    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            raw = resp.read().decode()
            return json.loads(raw) if raw else None
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode(errors="replace")
        raise SystemExit(f"HCM {method} {path} 失败：HTTP {exc.code} {detail}") from exc
    except urllib.error.URLError as exc:
        raise SystemExit(f"连不上 HCM（{BASE}）。先确认后端在 8000。{exc.reason}") from exc


def load_candidates():
    data = request("GET", "/api/candidates")
    if not isinstance(data, list):
        raise SystemExit("HCM 花名册返回异常")
    return data


def find_candidate(items, key: str):
    key = key.strip()
    for item in items:
        if item.get("name") == key or item.get("pinyin") == key:
            return item
    names = "、".join(f"{c.get('name')}({c.get('pinyin')})" for c in items) or "（空）"
    raise SystemExit(f"花名册里没有「{key}」。现在有：{names}")


def training_when(candidate) -> str:
    raw = candidate.get("started_at") or ""
    try:
        day = datetime.fromisoformat(raw.replace("Z", "+00:00")) + timedelta(days=1)
        return day.strftime("%Y-%m-%d 09:30")
    except ValueError:
        return "入职次日 09:30"


def payload_for(node_type: str, candidate) -> dict:
    pinyin = candidate.get("pinyin") or "yuangong10"
    role = candidate.get("role") or ""
    salary = candidate.get("salary") or ""
    if node_type == "contract":
        return {
            "role": role,
            "salary": salary,
            "probation": "3个月",
            "contract": "劳动合同已起草",
            "files": "岗位说明书/保密协议/员工手册确认书 已备齐",
        }
    if node_type == "account":
        return {
            "workno": workno_for(pinyin),
            "email": f"{pinyin}@xxx.com",
            "wecom": "已创建",
            "vpn": "已开通",
        }
    if node_type == "device":
        return {
            "laptop": "ThinkPad 14 资产号 TP010",
            "badge": "门禁卡已制",
            "desk": "3F-B08 工位已分配",
        }
    if node_type == "training":
        return {
            "course": "公司级 Onboarding 第一课",
            "date": training_when(candidate),
            "content": "公司介绍/文化/核心制度/安全合规",
        }
    if node_type == "buddy":
        return {"buddy": "后端组", "mentor": "导师2"}
    raise SystemExit(f"未知节点 {node_type}")


def node_of(candidate, node_type: str):
    for node in candidate.get("nodes") or []:
        if node.get("node_type") == node_type:
            return node
    raise SystemExit(f"{candidate.get('name')} 没有节点 {node_type}")


def is_placeholder(value) -> bool:
    text = str(value or "").strip()
    if text in PLACEHOLDERS:
        return True
    low = text.lower()
    # 旧演示数据里的企业名，按脱敏规则换成占位
    if "xingqiao" in low or "星桥" in text or text.upper().startswith("XQ"):
        return True
    # 公司级第一课的旧套话，读起来像要学 IT 部、HR 部的内部系统
    if "IT与HR系统使用" in text:
        return True
    return False


def workno_for(pinyin: str) -> str:
    digits = "".join(ch for ch in (pinyin or "") if ch.isdigit()) or "1"
    return f"YG{int(digits):04d}"


def show(candidate):
    print(f"{candidate.get('name')}  {candidate.get('pinyin')}  {candidate.get('role')}  {candidate.get('salary')}")
    for node_type, role, label in NODES:
        node = node_of(candidate, node_type)
        data = node.get("data") or {}
        bits = []
        for key, value in data.items():
            if key in ("system", "candidate", "status", "hcm_status", "source", "prepared_at", "updated_at"):
                continue
            if value in (None, ""):
                continue
            bits.append(f"{LABELS.get(key, key)}={value}")
        detail = "；".join(bits) if bits else "（未填）"
        print(f"  [{role:8}] {label:8} {node.get('status'):12} {detail}")


def fill_one(candidate, node_type: str, role: str, force: bool):
    node = node_of(candidate, node_type)
    current = dict(node.get("data") or {})
    incoming = payload_for(node_type, candidate)
    patch = {}
    for key, value in incoming.items():
        if force or is_placeholder(current.get(key)):
            patch[key] = value
    body = {"status": "completed", "data": patch}
    updated = request(
        "PUT",
        f"/api/candidates/{candidate['id']}/prep/{node_type}",
        body,
        role=role,
    )
    return updated, patch


def main(argv: list[str]) -> None:
    args = [a for a in argv if a != "--force"]
    force = "--force" in argv
    action = "show"
    who = "员工10"
    which = None
    rest = args[1:]
    if rest and rest[0] in ("show", "fill"):
        action = rest.pop(0)
    if rest and rest[0] not in ALIAS:
        who = rest.pop(0)
    if rest:
        which = ALIAS.get(rest[0])
        if which is None:
            raise SystemExit("节点只能是 contract / account / device / training / buddy")

    candidate = find_candidate(load_candidates(), who)
    if action == "show":
        show(candidate)
        return

    targets = [row for row in NODES if which is None or row[0] == which]
    for node_type, role, label in targets:
        updated, patch = fill_one(candidate, node_type, role, force)
        wrote = "、".join(f"{LABELS.get(k, k)}={v}" for k, v in patch.items()) or "内容已有，只确认状态"
        print(f"已写 {label}（部门 {role}）→ {updated.get('status')}  {wrote}")
    print("---")
    show(find_candidate(load_candidates(), who))


if __name__ == "__main__":
    main(sys.argv)
