#!/usr/bin/env bash
# 清理入职测试的重复落盘物，只保留员工1、员工2（按落盘里记的姓名认人，不按拼音猜）。
# 清理范围：
#   stub-state/<拼音>/                     入职状态目录（Lobster 落盘）
#   pending-approvals/<拼音>-*.json        待审批快照
#   review-state/reviews.json              试用期跟进总表里其他人的 records / armed
#   cron 里 onboard-review-<拼音>-day*     7/30/60/90 提醒（要网关在运行）
#   /tmp/no-lobster-demo                   对照脚本输出
#   hcm/hcm.db                             花名册及其五个部门节点（接口没有删除，直接删库）
#
# 用法:
#   bash cleanup-test-outputs.sh          只列出要清理的内容，不删除
#   bash cleanup-test-outputs.sh --yes    实际清理（文件先移到 /tmp 备份）
# 保留名单可用环境变量覆盖：KEEP_NAMES="员工1 员工2"
set -uo pipefail

W="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STATE="$(cd "$W/.." && pwd)"
YES="${1:-}"
KEEP_NAMES="${KEEP_NAMES:-员工1 员工2}"

PLAN="$(python3 - "$W" "$STATE/cron/jobs.json" "$KEEP_NAMES" <<'PY'
import json, os, sqlite3, sys
w, jobs_path, keep_names = sys.argv[1], sys.argv[2], set(sys.argv[3].split())

def name_of(d):
    for f in ('workflow.json', 'contract.json'):
        try:
            j = json.load(open(os.path.join(d, f), encoding='utf-8'))
            n = j.get('candidate') or j.get('name')
            if n:
                return n
        except (OSError, ValueError):
            pass
    return None

stub = os.path.join(w, 'stub-state')
keep_py, drop_dirs = set(), []
for p in sorted(os.listdir(stub)):
    d = os.path.join(stub, p)
    if not os.path.isdir(d):
        continue
    if name_of(d) in keep_names:
        keep_py.add(p)
    else:
        drop_dirs.append((p, name_of(d) or '?'))

rv = json.load(open(os.path.join(w, 'review-state', 'reviews.json'), encoding='utf-8'))
for r in rv.get('records', []):
    if r.get('name') in keep_names and r.get('pinyin'):
        keep_py.add(r['pinyin'])

pa = os.path.join(w, 'pending-approvals')
drop_pa = [f for f in sorted(os.listdir(pa)) if f.endswith('.json') and f.rsplit('-', 1)[0] not in keep_py]

drop_rec = sorted({f"{r.get('name')}({r.get('pinyin')})" for r in rv.get('records', []) if r.get('name') not in keep_names})
drop_arm = sorted(k for k in rv.get('armed', {}) if k not in keep_py)

jobs = json.load(open(jobs_path, encoding='utf-8'))
jobs = jobs.get('jobs', jobs) if isinstance(jobs, dict) else jobs
drop_jobs = []
for j in jobs:
    n = j.get('name') or ''
    if n.startswith('onboard-review-') and '-day' in n:
        if n[len('onboard-review-'):].rsplit('-day', 1)[0] not in keep_py:
            drop_jobs.append((j['id'], n))

hcm_db = os.path.join(os.path.dirname(os.path.dirname(jobs_path)), 'hcm', 'hcm.db')
hcm = []
if os.path.exists(hcm_db):
    con = sqlite3.connect(hcm_db)
    hcm = [{'id': i, 'name': name, 'pinyin': py, 'status': status}
           for i, name, py, status in con.execute(
               'select id, name, pinyin, status from candidates order by id')
           if name not in keep_names]
    con.close()

print(json.dumps({'keep': sorted(keep_py), 'dirs': drop_dirs, 'pending': drop_pa,
                  'records': drop_rec, 'armed': drop_arm, 'jobs': drop_jobs, 'hcm': hcm},
                 ensure_ascii=False))
PY
)" || { echo "读取落盘失败，未做任何清理。" >&2; exit 1; }

show() { python3 -c "import json,sys; d=json.loads(sys.argv[1]); exec(sys.argv[2])" "$PLAN" "$1"; }

echo "保留：$KEEP_NAMES（拼音 $(show "print(' '.join(d['keep']))")）"
echo "状态目录：";      show "print('\n'.join(f'  stub-state/{p}/  ({n})' for p,n in d['dirs']) or '  （无）')"
echo "待审批记录：";    show "print('\n'.join(f'  pending-approvals/{f}' for f in d['pending']) or '  （无）')"
echo "跟进总表记录：";  show "print('\n'.join(f'  {x}' for x in d['records']) or '  （无）')"
echo "跟进总表 armed："; show "print('  '+' '.join(d['armed']) if d['armed'] else '  （无）')"
echo "定时提醒：";      show "print('\n'.join(f'  {n}' for i,n in d['jobs']) or '  （无）')"
echo "HCM 花名册：";    show "print('\n'.join(f\"  {x['name']} ({x['pinyin']})\" for x in d['hcm']) or '  （无）')"
echo "对照脚本输出：";  ls -d /tmp/no-lobster-demo 2>/dev/null | sed 's/^/  /' || echo "  （无）"

if [ "$YES" != "--yes" ]; then
  echo
  echo "以上只是列出。确认后加 --yes 实际清理。"
  exit 0
fi

BK="/tmp/onboarding-test-cleanup-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BK/stub-state" "$BK/pending-approvals"

show "print('\n'.join(p for p,n in d['dirs']))" | while read -r p; do
  [ -n "$p" ] && mv "$W/stub-state/$p" "$BK/stub-state/" && echo "已移走 stub-state/$p"
done
show "print('\n'.join(d['pending']))" | while read -r f; do
  [ -n "$f" ] && mv "$W/pending-approvals/$f" "$BK/pending-approvals/" && echo "已移走 pending-approvals/$f"
done

cp "$W/review-state/reviews.json" "$BK/reviews.json"
python3 - "$W/review-state/reviews.json" "$PLAN" "$KEEP_NAMES" <<'PY'
import json, sys
path, plan, keep_names = sys.argv[1], json.loads(sys.argv[2]), set(sys.argv[3].split())
rv = json.load(open(path, encoding='utf-8'))
rv['records'] = [r for r in rv.get('records', []) if r.get('name') in keep_names]
rv['armed'] = {k: v for k, v in rv.get('armed', {}).items() if k in plan['keep']}
tmp = path + '.tmp'
with open(tmp, 'w', encoding='utf-8') as fh:
    json.dump(rv, fh, ensure_ascii=False, indent=2)
    fh.write('\n')
import os; os.replace(tmp, path)
print(f"跟进总表已精简：保留 {len(rv['records'])} 条记录")
PY

if [ -n "$(show "print(' '.join(i for i,n in d['jobs']))")" ]; then
  set -a; . "$STATE/env.sh" >/dev/null 2>&1; set +a
  failed=0
  while read -r id name; do
    [ -z "$id" ] && continue
    if openclaw cron rm "$id" < /dev/null > /dev/null 2>&1; then
      echo "已删除提醒 $name"
    else
      echo "删除提醒失败 $name（网关没开？）" >&2
      failed=1
    fi
  done < <(show "print('\n'.join(f'{i} {n}' for i,n in d['jobs']))")
  [ "$failed" = 1 ] && echo "有提醒没删掉：开网关后重跑本脚本即可，已清的部分不会重复处理。" >&2
fi

python3 - "$BK" "$PLAN" "$KEEP_NAMES" "$STATE/hcm/hcm.db" <<'PY'
import json, sqlite3, sys
bk, plan, keep_names, db = sys.argv[1], json.loads(sys.argv[2]), set(sys.argv[3].split()), sys.argv[4]
ids = [x['id'] for x in plan['hcm']]
if not ids:
    print('HCM 花名册：没有要删的人')
    raise SystemExit
con = sqlite3.connect(db)
con.row_factory = sqlite3.Row
q = ','.join('?' * len(ids))
people = [dict(r) for r in con.execute(
    f'select * from candidates where id in ({q}) and name not in ({",".join("?" * len(keep_names))})',
    ids + sorted(keep_names))]
gone = [r['id'] for r in people]
if not gone:
    print('HCM 花名册：没有要删的人')
    raise SystemExit
nq = ','.join('?' * len(gone))
nodes = [dict(r) for r in con.execute(f'select * from prep_nodes where candidate_id in ({nq})', gone)]
with open(bk + '/hcm-removed.json', 'w', encoding='utf-8') as fh:
    json.dump({'candidates': people, 'prep_nodes': nodes}, fh, ensure_ascii=False, indent=2, default=str)
    fh.write('\n')
con.execute(f'delete from prep_nodes where candidate_id in ({nq})', gone)
con.execute(f'delete from candidates where id in ({nq})', gone)
con.commit()
left = [r['name'] for r in con.execute('select name from candidates order by id')]
print(f"HCM 花名册已删除 {len(gone)} 人，剩余：{' '.join(left)}")
PY

rm -rf /tmp/no-lobster-demo
echo "备份在 $BK。入职看板是生成的页面，下次生成时按 HCM 重画。"
