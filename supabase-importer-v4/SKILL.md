---
name: supabase-importer-v4
description: "核材料性能数据 v4 导入系统。将 v4 抽取 JSON 批量导入 Supabase 的 nuclear_properties_v4 表。基于 v3 importer 做最小改动，保留增量导入、dry-run、force 覆盖、多文件批处理等原有功能。"
---

## 执行前必读

开始操作前，先读取：

```text
config.md   → Supabase 连接信息、表名、脚本路径
```

# Supabase 核材料 v4 数据导入系统

## 核心定位

本 skill 是 `supabase-importer` 的 v4 适配版。

只做最小改动：

1. 目标表从 `nuclear_properties` 改为 `nuclear_properties_v4`
2. 适配 v4 JSON 字段
3. 保留 v4 抽取结果内部的 `source_file`
4. 保留原 v3 importer 的导入流程：跳过已存在、`--force` 覆盖、`--dry-run` 预览、批量插入、排除 combined 文件

不做自动建表。用户已在 Supabase 网页端手动创建 `nuclear_properties_v4` 表。

---

## 数据库配置

| 项目 | 值 |
|------|-----|
| Project URL | `https://qffltopymihbndyrwhvj.supabase.co` |
| 目标表 | `nuclear_properties_v4` |
| 默认数据目录 | `/home/zuozhuo/info-extract/info-extract-with-skills/extraction_results/project_v4` |
| 导入脚本 | `.opencode/skills/supabase-importer-v4/import_to_supabase_v4.py` |

---

## 表结构（nuclear_properties_v4）

Supabase 中应已存在以下字段：

```sql
CREATE TABLE nuclear_properties_v4 (
  id BIGSERIAL PRIMARY KEY,
  source_file TEXT,
  material_name TEXT,
  composition TEXT,
  phase TEXT,
  element TEXT,
  property_category TEXT,
  property TEXT,
  value TEXT,
  unit TEXT,
  conditions JSONB,
  context TEXT,
  confidence TEXT,
  reference TEXT,
  property_note TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```

字段含义：

| 字段 | 说明 |
|------|------|
| `source_file` | v4 抽取记录中的原始 md 源路径 |
| `material_name` | 材料名称，如 `Zr-2.5Nb`、`Zircaloy-4` |
| `composition` | 成分或材料牌号 |
| `phase` | 物相 |
| `element` | 相关元素 |
| `property_category` | v4 性能大类，如 `腐蚀`、`弹塑性模型` |
| `property` | 具体性能名称 |
| `value` | 数值，字符串，保留原始精度 |
| `unit` | 单位 |
| `conditions` | 实验/模拟条件，JSONB |
| `context` | 上下文说明 |
| `confidence` | `high` / `medium` / `low` |
| `reference` | 文献来源 |
| `property_note` | 可选字段，如 `目录外` |

---

## 触发场景

当用户说以下任何一种时，执行导入：

- “导入 v4 数据”
- “把 project_v4 写入 Supabase”
- “同步 nuclear_properties_v4”
- “导入这个 JSON 目录”
- “重新导入 / 强制覆盖 / 数据有改动” → 加 `--force`

关键规则：

- 用户给了目录路径时，必须用 `-d` 传入。
- 用户提到“强制、覆盖、同步、重新导入、有改动”时，必须加 `--force`。
- 不要写入旧表 `nuclear_properties`。
- 不要自动建表。

---

## 执行前检查

1. 检查目录存在：

```bash
ls <用户指定目录>
```

2. 检查 supabase 库：

```bash
python3 -c "import supabase"
```

3. 如果未安装：

```bash
pip install supabase
```

4. 🔴 **CHECKPOINT · 导入前确认**：
   - 展示待导入的 JSON 文件列表和总记录数
   - 先执行 `--dry-run` 预览
   - 等用户确认后再正式导入

## 常见失败模式与处理

| 触发条件 | 一线修复 | 仍失败兜底 |
|---------|---------|------------|
| Supabase 连接超时 | 检查网络连接；检查 SUPABASE_KEY 是否有效 | 保留 JSON 文件，下次重试导入 |
| JSON 文件格式错误 | 用 `python3 -m json.tool <file>.json` 校验 | 跳过该文件，记录错误，继续导入其他文件 |
| 导入后记录数与 JSON 记录数不一致 | 检查 source_file 是否重复导致增量跳过 | 加 `--force` 重新导入该批次 |
| service_role key 权限不足 | 检查 key 是否为 service_role 而非 anon | 提示用户在 Supabase Dashboard 获取 service_role key |
| 表 nuclear_properties_v4 不存在 | 提示用户先创建表 | 不自动建表，给出建表 SQL 供参考 |

---

## 标准用法

```bash
# 导入默认 v4 目录，已存在 source_file 自动跳过
python3 /home/zuozhuo/info-extract/info-extract-with-skills/.opencode/skills/supabase-importer-v4/import_to_supabase_v4.py

# 导入用户指定目录
python3 /home/zuozhuo/info-extract/info-extract-with-skills/.opencode/skills/supabase-importer-v4/import_to_supabase_v4.py   -d /home/zuozhuo/info-extract/info-extract-with-skills/extraction_results/project_v4

# 强制覆盖
python3 /home/zuozhuo/info-extract/info-extract-with-skills/.opencode/skills/supabase-importer-v4/import_to_supabase_v4.py   -d /home/zuozhuo/info-extract/info-extract-with-skills/extraction_results/project_v4   --force

# dry-run 预览，不写库
python3 /home/zuozhuo/info-extract/info-extract-with-skills/.opencode/skills/supabase-importer-v4/import_to_supabase_v4.py   -d /home/zuozhuo/info-extract/info-extract-with-skills/extraction_results/project_v4   --dry-run

# 自定义文件匹配
python3 /home/zuozhuo/info-extract/info-extract-with-skills/.opencode/skills/supabase-importer-v4/import_to_supabase_v4.py   -d /path/to/project_v4 -p "*.json"
```

---

## 参数说明

| 参数 | 简写 | 说明 | 默认值 |
|------|------|------|--------|
| `--data-dir` | `-d` | JSON 文件目录 | `extraction_results/project_v4/` |
| `--pattern` | `-p` | 文件匹配模式 | `*.json` |
| `--dry-run` | — | 只扫描统计，不写库 | 关闭 |
| `--force` | `-f` | 删除同 `source_file` 旧记录后重导 | 关闭 |

---

## 同步策略

脚本默认采用 v3 importer 的安全策略：

- 新 `source_file` → 插入
- 已存在 `source_file` → 跳过
- `--force` → 删除该 `source_file` 旧记录，再插入新记录
- 自动排除文件名含 `combined` 的聚合文件

v4 重要差异：

- `source_file` 优先使用 JSON 记录内部字段。
- JSON 文件名只作为 fallback，不覆盖 v4 抽取结果里的 md 源路径。

---

## 验证导入结果

```sql
-- 查总数
SELECT COUNT(*) FROM nuclear_properties_v4;

-- 按 md 源文件统计
SELECT source_file, COUNT(*) AS count
FROM nuclear_properties_v4
GROUP BY source_file
ORDER BY source_file;

-- 按性能大类统计
SELECT property_category, COUNT(*) AS count
FROM nuclear_properties_v4
GROUP BY property_category
ORDER BY count DESC;

-- 查最新导入
SELECT * FROM nuclear_properties_v4
ORDER BY created_at DESC
LIMIT 10;
```
