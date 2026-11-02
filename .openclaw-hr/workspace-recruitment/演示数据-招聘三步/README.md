# 招聘技能演示 · 测试数据

2026-10-20 从 git HEAD（3bbc45b）和备份包
`backup/recruitment-20261014-pre-router-test.tgz` 收回。
目录结构和工作区一致，下面的命令都在 `workspace-recruitment` 根目录执行。

## 一、字段回核（解析结果逐字段回溯原文）

脚本：`skills/auditing-extraction/scripts/audit_extraction.js`。硬提取字段必须能在简历原文里逐字找到，找不到就退出码 1。

1. 干净样本，应通过（实测 22/22，追溯率 100%，退出码 0）：

```bash
bash scripts/recruitment-run.sh node skills/auditing-extraction/scripts/audit_extraction.js \
  演示数据-招聘三步/parsed/员工1-后端开发.json \
  演示数据-招聘三步/inbox/resume-tech-员工1-后端开发.md
```

2. 篡改样本：`parsed/员工1-后端开发-学校被改.json` 只把 `education.school` 从「某某大学1」改成「清华大学」，其余与干净样本相同。应拦住（实测 21/22，退出码 1，点名 `education.school`）：

```bash
bash scripts/recruitment-run.sh node skills/auditing-extraction/scripts/audit_extraction.js \
  演示数据-招聘三步/parsed/员工1-后端开发-学校被改.json \
  演示数据-招聘三步/inbox/resume-tech-员工1-后端开发.md
```

核对报告落在 `演示数据-招聘三步/audited/`。

## 二、删除敏感字段

1. 看样本里的敏感字段：`演示数据-招聘三步/test-fixtures/demo-lifecycle/planted-sensitive-员工1-full.json`
2. 运行：

```bash
bash scripts/recruitment-run.sh node skills/filtering-sensitive-fields/scripts/filter_sensitive.js \
  演示数据-招聘三步/test-fixtures/demo-lifecycle/planted-sensitive-员工1-full.json \
  演示数据-招聘三步/scoring/demo-脱敏后-员工1.json
```

3. 看结果：`演示数据-招聘三步/scoring/demo-脱敏后-员工1.json`

## 三、数字回核

1. 看错误样本：
   - 原简历 `演示数据-招聘三步/inbox/resume-tech-员工1-后端开发.md`，搜「12.8」
   - 原 JD `演示数据-招聘三步/jds/jd-bigtech-后端开发工程师.md`，第 18 行「58 万笔/秒」
   - 错误评分 `演示数据-招聘三步/scoring/results/ranking-员工1-后端开发.json`
2. 先把 `演示数据-招聘三步/scoring/number_audit.py` 里的 `verify_in_resume`（约第 122 行）改成 `return True`，跑一遍看它放行：

```bash
bash scripts/recruitment-run.sh python3 演示数据-招聘三步/scoring/number_audit.py \
  演示数据-招聘三步/inbox/resume-tech-员工1-后端开发.md \
  演示数据-招聘三步/scoring/results/ranking-员工1-后端开发.json
```

3. 把函数改回正确实现再跑，结果写到 `ranking-员工1-后端开发.audited.json`：

```python
def verify_in_resume(token, resume_norm):
    token_norm = _norm(token)
    if token_norm in resume_norm:
        return True
    num_only = re.match(r"\d+(?:\.\d+)?", token_norm)
    if num_only and num_only.group() in resume_norm:
        return None
    return False
```

## 四、生成画像

```bash
bash scripts/recruitment-run.sh python3 skills/generating-candidate-profiles/scripts/generate_profile.py \
  演示数据-招聘三步/scoring/results/ranking-员工1-后端开发.audited.json \
  员工1 演示数据-招聘三步/profile/output/profile-员工1-回核后.html
```

`parsed/员工1-后端开发.json` 是画像脚本按姓名自动读取的候选人档案。

## 来源

| 文件 | 来源 |
|---|---|
| scoring/number_audit.py | git HEAD |
| scoring/results/ranking-员工1-后端开发.json | git HEAD |
| jds/jd-bigtech-后端开发工程师.md | git HEAD |
| test-fixtures/demo-lifecycle/planted-sensitive-员工1-full.json | git HEAD |
| skills 下两个脚本 | git HEAD |
| inbox/resume-tech-员工1-后端开发.md | 备份包（inbox 被 gitignore，git 里没有） |
| parsed/员工1-后端开发.json | 备份包 |
| parsed/员工1-后端开发-学校被改.json | 由上面那份改一个字段：education.school → 清华大学 |
| skills/auditing-extraction/scripts/audit_extraction.js | git HEAD |
| audited/*.audit.json | 2026-10-20 实跑产出 |
| recruitment-run.sh | 工作区现行版本 |
