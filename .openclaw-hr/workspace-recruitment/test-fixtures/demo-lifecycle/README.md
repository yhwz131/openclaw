# 演示夹具（非生产）

- `planted-sensitive-员工1.json`：只种年龄/性别，短演示。
- `planted-sensitive-员工1-full.json`：**演示主夹具**。顶层 + `education` + `work_experience[0]` 多种敏感键（中英、婚育、户籍、民族、健康、政治面貌、院校层次）。当场跑：

```bash
cd /opt/openclaw-hr/.openclaw-hr/workspace-recruitment
node skills/filtering-sensitive-fields/scripts/filter_sensitive.js \
  test-fixtures/demo-lifecycle/planted-sensitive-员工1-full.json \
  /tmp/clean-员工1-demo.json
```

预期：日志列出约 30 个已剥离字段；`name` / `skills` / `graduation_year` 仍在；exit 0。不要写进 `scoring/clean-员工1-后端开发.json`（那是干净解析副本）。
- 禁止把本目录当人才库真源，禁止扩写成真人履历。
