// 读 stdin {allowlist, cwd, commands[]}，用网关自己的判定函数逐条判断能否执行，输出 [true|false...]
import fs from 'node:fs';
import path from 'node:path';
import { pathToFileURL } from 'node:url';

const DIST = '/opt/openclaw-hr/.openclaw-hr/install/node_modules/openclaw/dist';
const modFile = fs.readdirSync(DIST).find((f) => /^exec-approvals-allowlist-.*\.js$/.test(f));
const { n: evaluateShellAllowlist } = await import(pathToFileURL(path.join(DIST, modFile)).href);

const { allowlist, cwd, commands } = JSON.parse(fs.readFileSync(0, 'utf8'));
const out = commands.map((command) => evaluateShellAllowlist({
  command, allowlist, cwd, env: process.env, platform: 'linux',
  safeBins: new Set(), skillBins: new Set(), autoAllowSkills: false,
}).allowlistSatisfied);
process.stdout.write(JSON.stringify(out));
