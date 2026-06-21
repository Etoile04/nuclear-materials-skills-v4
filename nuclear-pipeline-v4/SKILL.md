---
name: nuclear-pipeline-v4
description: "核材料性能数据端到端流程。将 PDF 文献批量转换为 Markdown，经 LLM 语义抽取生成 v4 JSON，再导入 Supabase 的 nuclear_properties_v4 表。当用户提到'批量处理论文'、'端到端抽取'、'PDF 转 Supabase'、'核材料数据流水线'、'从文献到数据库'时触发。"
---

# 核材料性能数据端到端流程 v4

## 目标

从 PDF 文献目录开始，完成以下完整流程：

```text
PDF → Markdown → v4 结构化 JSON → Supabase nuclear_properties_v4
````

本 skill 只负责数据生产链路，不负责查询。查询使用单独的 `nuclear-query-v4`。

---

## 核心原则

本流程由三段组成，执行方式不同：

1. **PDF → Markdown**：允许使用脚本自动完成
2. **Markdown → JSON**：**必须由 LLM 按抽取规则逐篇语义抽取**
3. **JSON → Supabase**：允许使用导入脚本自动完成

**禁止**将 Markdown → JSON 抽取步骤改写成正则、关键词表、表格模板或批量规则脚本。

脚本只允许负责：

* 遍历文件
* 调用 PDF 转 Markdown 脚本
* 创建输出目录
* 保存 JSON 文件
* 调用 Supabase 导入脚本

核心抽取判断必须由 LLM 完成，包括但不限于：

* 判断某个数值是否属于核材料性能数据
* 判断 `material_name`、`composition`
* 判断 `property_category`、`property`
* 判断 `phase`、`element`
* 判断 `conditions`、`context`、`confidence`
* 排除二手引用、纯实验条件、孤立无归属数值

---

## 输入与默认路径

### 输入

用户应提供 PDF 目录路径。

### 默认路径

若用户未指定，默认使用：

```text
PDF 输入目录：pdf/
Markdown 输出目录：md_output/
JSON 输出目录：extraction_results/project_v4/
```

---

## 依赖组件

本流程依赖以下已有组件：

### 1. PDF 转 Markdown 脚本

路径优先使用环境变量 `PDF_TO_MD_SCRIPT`，未设置时回退到默认路径：

```text
${PDF_TO_MD_SCRIPT:-/home/zuozhuo/info-extract/info-extract-with-skills/pdf_to_md_v2.py}
```

### 2. v4 抽取规则

应遵循已有的核材料抽取 skill 规则，包括：

* `SKILL.md`
* `references/extraction_rules.md`
* `references/property_catalog.md`
* `references/phase_rules.md`

### 3. v4 Supabase 导入脚本

应调用已有 importer，路径优先使用环境变量 `IMPORTER_SCRIPT`：

```text
${IMPORTER_SCRIPT:-.opencode/skills/supabase-importer-v4/import_to_supabase_v4.py}
```

目标表：

```text
nuclear_properties_v4
```

---

## Step 1：PDF 转 Markdown

使用脚本：

```bash
python3 /home/zuozhuo/info-extract/info-extract-with-skills/pdf_to_md_v2.py --help
```

**执行前必须先查看 `--help`，确认真实参数名，不得猜测参数。**

然后根据脚本实际参数，将 PDF 目录转换为 Markdown 目录。

### 要求

* 必须显式指定输入 PDF 目录
* 若用户指定了 Markdown 输出目录，也必须显式传入
* 转换完成后检查 Markdown 输出目录是否存在
* 统计生成的 `.md` 文件数量
* 若没有生成任何 md 文件，立即停止流程并报告错误
* 不得跳过此检查

---

## Step 2：Markdown → v4 JSON 抽取

对 Markdown 输出目录中的**每个 md 文件**，使用 v4 抽取规则进行 **LLM 语义抽取**。

### 抽取要求

* 一个 md 文件对应一个同名 JSON 文件
* JSON 文件输出到：

```text
extraction_results/project_v4/
```

* JSON 文件名必须与 md 文件主文件名一致
* 一个 md 文件中可包含多条数据记录
* 一个 md 文件中即使包含多篇论文，也仍只输出一个同名 JSON，具体论文由 `reference` 区分

### 每条记录必须包含以下字段

```text
source_file
material_name
composition
phase
element
property_category
property
value
unit
conditions
context
confidence
reference
```

### 可选字段

```text
property_note
```

### 抽取规则要求

必须遵循已有抽取规则，包括：

* 全文扫描：Abstract、正文、表格、图注、Discussion、Appendix
* 不得只抽表格
* 不得只抽数字+单位
* 不得把实验条件误当作独立性能数据
* 必须保留原始数值精度
* `phase` 必须跟随测量对象归属
* `source_file` 必须保存原始 md 文件路径
* `property_category` 必须尽量对齐 v4 分类体系
* 不得写脚本替代抽取判断

### v4 分类体系

优先使用以下类别：

```text
密度
比热容
热传导率
弹塑性模型
热膨胀
辐照蠕变
辐照肿胀
腐蚀
硬化性能
材料成分/杂质含量
材料规格/加工状态
组织信息
其他性能
```

---

## Step 3：JSON → Supabase 导入

使用已有 v4 importer：

```bash
python3 .opencode/skills/supabase-importer-v4/import_to_supabase_v4.py -d /home/zuozhuo/info-extract/info-extract-with-skills/extraction_results/project_v4
```

### 导入要求

* 目标表固定为：

```text
nuclear_properties_v4
```

* 默认采用增量导入
* 当用户明确要求“重新导入”“覆盖”“同步更新”“有改动”时，必须加：

```bash
--force
```

### 导入前检查

必须确认：

* JSON 输出目录存在
* `nuclear_properties_v4` 表已存在
* 已配置 `SUPABASE_SERVICE_ROLE_KEY` 或 `SUPABASE_KEY`
* importer 脚本路径正确

### 导入前建议先 dry-run

```bash
python3 .opencode/skills/supabase-importer-v4/import_to_supabase_v4.py -d /home/zuozhuo/info-extract/info-extract-with-skills/extraction_results/project_v4 --dry-run
```

无异常后再正式导入。

---

## 执行顺序

严格按以下顺序执行：

```text
1. 确认 PDF 输入目录
2. 调用 pdf_to_md_v2.py 生成 Markdown
3. 检查 md 输出目录及文件数量
```

🔴 **CHECKPOINT · STOP：Step 2→3 之间**
- 展示生成的 md 文件列表和总数
- 等用户确认后再进入抽取阶段
- 若 md 文件数为 0，立即停止并报告错误

```text
4. 对每个 md 文件执行 LLM 语义抽取
5. 输出同名 JSON 到 extraction_results/project_v4/
6. 检查 JSON 文件数量及总记录数
```

🔴 **CHECKPOINT · STOP：Step 6→7 之间**
- 展示抽取统计：每个 md 的记录数、总记录数、失败文件
- 等用户确认后再进入导入阶段
- 若总记录数为 0，停止并报告错误

```text
7. 先 dry-run 导入预览
```

🔴 **CHECKPOINT · STOP：dry-run 后**
- 展示 dry-run 结果（将导入 N 条，跳过 M 条）
- 等用户确认后正式导入

```text
8. 正式导入 nuclear_properties_v4
9. 输出最终报告
```

不得跳步。

---

## 输出要求

流程结束后，必须输出一份简明报告，至少包括：

* PDF 文件数量
* 成功生成的 Markdown 文件数量
* 成功生成的 JSON 文件数量
* 抽取出的总记录数
* 成功导入数据库的记录数
* 失败数
* 目标表名

建议格式：

```text
流程完成：
- PDF 文件数：N
- Markdown 文件数：N
- JSON 文件数：N
- 抽取记录总数：N
- 成功导入：N
- 失败：N
- 目标表：nuclear_properties_v4
```

---

## 失败模式编码

| 触发条件 | 一线修复 | 仍失败兜底 |
|---------|---------|-----------|
| PDF→Markdown 失败或返回 0 个 md 文件 | 检查 PDF 目录路径是否正确；检查 pdf_to_md_v2.py 是否可执行 | 停止流程，报告错误，不得继续抽取 |
| 单个 md 文件 LLM 抽取输出非法 JSON | 重试一次（可能是 LLM 输出截断）；检查是否因上下文过长导致截断，若是则分段抽取 | 记录失败文件名，跳过该文件，继续处理其他 md；在报告中标记 `extraction_failed` |
| 抽取结果字段缺失（如无 material_name） | 检查 md 原文是否有明确材料信息；若确实无信息则 `material_name: null` 可接受 | 若缺 `source_file` 或 `reference` 则该条无效，丢弃并记录 |
| property_category 无法归类 | 优先对齐 v4 分类体系中的 13 类；若仍不匹配则归入 `其他性能` 并标注 `property_note: "目录外"` | 若连"其他性能"都不适用，则该数据点不抽取 |
| JSON 文件格式错误（解析失败） | 用 `python3 -m json.tool <file>.json` 校验，定位语法错误 | 重新从 md 文件抽取该 JSON |
| Supabase 导入连接超时 | 检查网络连接；检查 SUPABASE_KEY 是否有效 | 保留已生成 JSON，下次重试导入 |
| 导入后记录数与 JSON 记录数不一致 | 用 dry-run 对比；检查 source_file 是否重复导致增量跳过 | 加 `--force` 重新导入该批次 |

---

## 禁止事项

* 禁止将 Markdown → JSON 步骤改写为解析脚本
* 禁止只根据表格内容抽取
* 禁止跳过全文扫描
* 禁止忽略 `source_file`
* 禁止把 v4 数据写入旧表 `nuclear_properties`
* 禁止未经用户要求自动执行查询步骤
* 禁止将查询 skill 混入本流程

---

## 本 skill 的职责边界

本 skill 只负责：

```text
PDF → Markdown → 抽取 JSON → 导入数据库
```

本 skill 不负责：

```text
数据库查询
统计分析解释
问答式检索
```

这些由单独的 `nuclear-query-v4` 负责。

---

## 一句话说明

这是一个**端到端总控 skill**，用于把预处理前的 PDF 文献批量转换为可导入 Supabase v4 表的核材料结构化数据；其中 PDF 转换和数据库导入可脚本化，但核心抽取必须由 LLM 按既有规则完成。

```