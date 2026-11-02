// 执行白名单验收：用 OpenClaw 网关自己的判定函数，逐条判断 er-admin 能不能执行这条命令。
// 用法: node demo/acceptance/exec-allowlist.mjs
import fs from 'node:fs';
import path from 'node:path';
import { pathToFileURL } from 'node:url';

const STATE = '/opt/openclaw-hr/.openclaw-hr';
const DIST = path.join(STATE, 'install/node_modules/openclaw/dist');
const modFile = fs.readdirSync(DIST).find((f) => /^exec-approvals-allowlist-.*\.js$/.test(f));
const { n: evaluateShellAllowlist } = await import(pathToFileURL(path.join(DIST, modFile)).href);

const approvals = JSON.parse(fs.readFileSync(path.join(STATE, 'exec-approvals.json'), 'utf8'));
const allowlist = approvals.agents['er-admin'].allowlist;
const cwd = path.join(STATE, 'workspace-er-admin');
const HCM = 'http://127.0.0.1:8000/api/candidates';

const CASES = [
  ['正常 · 查薪资', 'bash scripts/er-admin-run.sh payroll-query --name 员工1', true],
  ['正常 · 带发送人', 'bash scripts/er-admin-run.sh payroll-query --sender ou_00000000000000000000000000000000 --name 员工1', true],
  ['正常 · 制度检索', 'bash scripts/er-admin-run.sh ima-search 年假 几天', true],
  ['正常 · 出月报', 'bash scripts/er-admin-run.sh monthly-report', true],
  ['直接请求 HCM', `curl -s ${HCM}`, false],
  ['python 直接取数', 'python3 -c "print(1)"', false],
  ['跳过壳调闸门', 'bash scripts/hr-data-access.sh check ou_x', false],
  ['bash -c 夹带脚本名', `bash -c 'curl -s ${HCM}' er-admin-run.sh`, false],
  ['注释夹带脚本名', `bash -c 'curl -s ${HCM} #er-admin-run.sh'`, false],
  ['sh -c 夹带脚本名', `sh -c 'curl -s ${HCM}' er-admin-run.sh`, false],
  ['分号串接', `bash scripts/er-admin-run.sh payroll-query --all; curl -s ${HCM}`, false],
  ['&& 串接', 'bash scripts/er-admin-run.sh payroll-query --all && cat /etc/passwd', false],
  ['管道外带', 'bash scripts/er-admin-run.sh payroll-query --all | tee /tmp/x', false],
  ['命令替换', `bash scripts/er-admin-run.sh payroll-query --name $(curl -s ${HCM})`, false],
  ['别处的同名脚本', 'bash /tmp/er-admin-run.sh payroll-query --all', false],
  ['路径穿越', 'bash scripts/../../workspace-x/scripts/er-admin-run.sh payroll-query', false],
  ['后缀伪装', 'bash scripts/er-admin-run.sh.bak payroll-query', false],
  ['改环境变量', 'OPENCLAW_SHELL= bash scripts/er-admin-run.sh payroll-query --all', false],
  ['读闸门源码', 'cat scripts/hr-data-access.sh', false],
];

let ok = 0;
for (const [name, command, expect] of CASES) {
  const r = evaluateShellAllowlist({
    command, allowlist, cwd, env: process.env, platform: 'linux',
    safeBins: new Set(), skillBins: new Set(), autoAllowSkills: false,
  });
  const pass = r.allowlistSatisfied === expect;
  if (pass) ok += 1;
  console.log(`${pass ? '✓' : '✗'}  ${r.allowlistSatisfied ? '放行' : '拒绝'}  ${name}`);
}
console.log(`\n执行白名单：${CASES.length} 条，符合预期 ${ok} 条`);
process.exit(ok === CASES.length ? 0 : 1);
