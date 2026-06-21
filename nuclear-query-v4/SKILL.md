---
name: nuclear-query-v4
description: "核材料性能数据查询系统 v4。从 Supabase nuclear_properties_v4 表中检索 v4 抽取的核材料性能数据。当用户输入性能类别、具体性能名、材料名、物相或元素时触发。支持组合查询。"
---

# 核材料性能数据查询系统 v4

## 数据库配置

| 项目 | 值 |
|------|-----|
| Project ID | `qffltopymihbndyrwhvj` |
| 表名 | `nuclear_properties_v4` |
| 查询方式 | 使用 `query_v4.py` 脚本查询 |

---

## 这个 skill 是做什么的

本 skill 只负责**查询已经导入 Supabase 的 v4 抽取结果**，不负责抽取论文，也不负责导入 JSON。

典型问题：

- `Zr-2.5Nb 的腐蚀数据有哪些？`
- `查一下 Zircaloy-4 的屈服强度`
- `beta 相的相分数有哪些？`
- `查询氢含量相关数据`
- `统计热膨胀数据`

---

## v4 表字段

查询表：`nuclear_properties_v4`

核心字段：

| 字段 | 含义 |
|------|------|
| `source_file` | 原始 md 源文件路径 |
| `material_name` | 材料名称，如 `Zr-2.5Nb` |
| `composition` | 成分或材料组成 |
| `phase` | 物相 |
| `element` | 元素 |
| `property_category` | v4 性能大类 |
| `property` | 具体性能名 |
| `value` | 数值 |
| `unit` | 单位 |
| `conditions` | 实验/模拟条件 JSONB |
| `context` | 上下文说明 |
| `confidence` | 置信度 |
| `reference` | 文献来源 |
| `property_note` | 可选，目录外性能说明 |

---

## 工作流

```
Step 1: 解析用户输入
  → 识别性能类别 / 具体性能 / 材料 / 物相 / 元素

Step 2: 映射到 v4 字段
  → 性能类别优先映射到 property_category
  → 具体性能映射到 property
  → 材料名映射到 material_name，同时可兼容 composition
  → 物相映射到 phase
  → 元素映射到 element

Step 3: 执行 Supabase SQL 查询
  → 必须先 COUNT，再 SELECT

Step 4: 格式化输出
  → 显示材料、类别、性能、数值、单位、条件/背景、来源
```

---

## Step 1 — 解析输入

将用户输入拆成以下查询维度：

| 维度 | v4 数据库字段 | 示例输入 |
|------|--------------|----------|
| 性能大类 | `property_category` | 密度、比热容、热传导率、弹塑性模型、热膨胀、辐照蠕变、辐照肿胀、腐蚀、硬化性能 |
| 具体性能 | `property` | 屈服强度、抗拉强度、氧化膜厚度、氢含量 |
| 材料名 | `material_name`，必要时兼容 `composition` | Zircaloy-4、Zr-2.5Nb |
| 成分 | `composition` | Zr-2.5Nb、Zr-Sn-Fe-Cr |
| 物相 | `phase` | alpha、beta、oxide、hydride |
| 元素 | `element` | hydrogen、oxygen、phosphorus |

---

## Step 2 — 性能类别映射

v4 已经有 `property_category` 字段。用户输入以下类别时，优先查 `property_category`，不要再只靠 property 关键词展开。

| 用户输入 | 查询条件 |
|---------|----------|
| 密度 | `property_category ILIKE '%密度%'` |
| 比热容 | `property_category ILIKE '%比热容%'` |
| 热传导率、热导率 | `property_category ILIKE '%热传导率%'` |
| 弹塑性、弹塑性模型、力学、强度 | `property_category ILIKE '%弹塑性模型%'` |
| 热膨胀 | `property_category ILIKE '%热膨胀%'` |
| 辐照蠕变、蠕变 | `property_category ILIKE '%辐照蠕变%'` |
| 辐照肿胀、肿胀 | `property_category ILIKE '%辐照肿胀%'` |
| 腐蚀、腐蚀性能 | `property_category ILIKE '%腐蚀%'` |
| 硬化、硬化性能 | `property_category ILIKE '%硬化性能%'` |
| 材料规格、组织、微观 | `property_category ILIKE '%材料规格/组织信息%'` |

若用户输入的是具体性能名，则查 `property ILIKE '%关键词%'`。

---

## Step 3 — 执行查询

每次查询必须两步：

### 1. COUNT 查询

```sql
SELECT COUNT(*) AS total
FROM nuclear_properties_v4
WHERE <同样的 WHERE 条件>;
```

### 2. 数据查询

```sql
SELECT
  id,
  source_file,
  material_name,
  composition,
  phase,
  element,
  property_category,
  property,
  value,
  unit,
  conditions,
  context,
  confidence,
  reference,
  property_note
FROM nuclear_properties_v4
WHERE <同样的 WHERE 条件>
ORDER BY material_name ASC, property_category ASC, property ASC
LIMIT 500;
```

若 COUNT > 500，输出时必须说明结果被截断。

---

## 常用 WHERE 写法

### 按材料名

```sql
(material_name ILIKE '%Zr-2.5Nb%' OR composition ILIKE '%Zr-2.5Nb%')
```

### 按性能大类

```sql
property_category ILIKE '%腐蚀%'
```

### 按具体性能

```sql
property ILIKE '%氧化膜厚度%'
```

### 按物相

```sql
phase ILIKE '%beta%'
```

### 按元素

```sql
element ILIKE '%hydrogen%'
```

### 组合查询示例

```sql
SELECT COUNT(*) AS total
FROM nuclear_properties_v4
WHERE (material_name ILIKE '%Zr-2.5Nb%' OR composition ILIKE '%Zr-2.5Nb%')
  AND property_category ILIKE '%腐蚀%';
```

```sql
SELECT
  id, source_file, material_name, composition, phase, element,
  property_category, property, value, unit, conditions, context,
  confidence, reference, property_note
FROM nuclear_properties_v4
WHERE (material_name ILIKE '%Zr-2.5Nb%' OR composition ILIKE '%Zr-2.5Nb%')
  AND property_category ILIKE '%腐蚀%'
ORDER BY material_name ASC, property_category ASC, property ASC
LIMIT 500;
```

---

## Step 4 — 输出格式

### 输出头部

```
查询：<查询描述>
数据库总匹配：N 条 | 当前展示：M 条（LIMIT 500）
```

若 N > 500，追加：

```
⚠️ 数据已截断，仅展示前 500 条，还有 N-500 条未显示。建议增加材料名、性能名、物相或元素条件。
```

### 展示格式

按 `material_name + source_file` 分块；块内按 `property_category` 分组。

模板：

```
1. <property_category>（<material_name>, <source_file>）[phase]

| 属性 | 值 | 单位 | 条件/背景 | 文献 |
|------|----|------|-----------|------|
| 屈服强度 | 450 | MPa | temp_C=350 | Author, Title |
```

规则：

- 材料优先显示 `material_name`；为空时显示 `composition`。
- 属性显示 `property`；若 `element` 非空，写成 `property [element]`。
- 条件/背景优先显示 `context`；若为空，显示 `conditions` 的简要键值；均为空显示 `—`。
- `confidence` 非 high 时，在值后追加 `⚠️medium` 或 `⚠️low`。
- `property_note` 非空时，可在属性后补充 `[目录外]`。
- 每条结果必须保留 `source_file` 和 `reference`，用于溯源。

---

## query_v4.py 说明

使用随 skill 附带的 `query_v4.py` 脚本查询。脚本是 v3 `query.py` 的最小适配版：

- 表名改为 `nuclear_properties_v4`
- 材料名参数 `--composition/-c` 保留，但实际优先查询 `material_name`
- 支持 v4 `property_category`
- 输出中增加 `性能类别`

示例：

```bash
python3 query_v4.py -p 腐蚀 -c Zr-2.5Nb
python3 query_v4.py -p 屈服强度 -c Zircaloy-4
python3 query_v4.py -ph beta -p 材料规格
```

---

## 注意事项

- 本 skill 只查 v4 表：`nuclear_properties_v4`。
- 不查询旧表 `nuclear_properties`，避免 v3/v4 数据混淆。
- 不执行建表、不导入数据；建表和导入由 `supabase-importer-v4` 完成。

## 常见失败模式与处理

| 触发条件 | 一线修复 | 仍失败兜底 |
|---------|---------|------------|
| Supabase 连接超时 | 检查网络；检查 SUPABASE_KEY 是否过期 | 报告连接错误，建议用户检查网络后重试 |
| 查询结果为 0 条 | 检查 WHERE 条件是否过严；尝试去掉 material_name 只查 property_category | 若确认数据应存在，提示用户检查 property_category 拼写 |
| COUNT > 500 但只展示 500 条 | 正常截断，输出警告提示用户增加筛选条件 | 建议 "增加材料名或物相条件缩小范围" |
| 用户输入的性能名在数据库中用词不同 | 尝试 ILIKE 模糊匹配 | 提示用户尝试 property_category 而非具体 property 名 |
| conditions JSONB 无法查询 | 不直接查 JSONB 内部字段；用 context 做 ILIKE 匹配 | 告知用户 conditions 是 JSONB 格式，不支持精确字段查询 |

## 查询前的检查点

🔴 **CHECKPOINT**：执行查询前，先向用户确认查询意图：
- 重复用户的查询条件（材料名 + 性能类别 + 物相等）
- 展示将要执行的 SQL WHERE 条件
- 用户确认后再执行
