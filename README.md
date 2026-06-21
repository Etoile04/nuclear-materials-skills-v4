# Nuclear Materials Property Data Skills (v4)

核材料性能数据采集技能套件——从 PDF 文献到结构化数据库的端到端流水线。

## 技能组成

| 技能 | 功能 | 类型 |
|------|------|------|
| `nuclear-pipeline-v4` | 端到端总控：PDF → Markdown → JSON → Supabase | 编排层 |
| `nuclear-property-extraction-v4` | LLM 语义抽取核心规则 | 核心逻辑 |
| `nuclear-query-v4` | 数据库查询 | 查询层 |
| `supabase-importer-v4` | 数据导入 Supabase | 导入层 |

## 数据流水线

```
PDF 文献目录
    ↓  [pdf_to_md_v2.py]
Markdown 文件
    ↓  [LLM 语义抽取] ← nuclear-property-extraction-v4 规则
v4 结构化 JSON
    ↓  [import_to_supabase_v4.py]
Supabase nuclear_properties_v4 表
    ↓  [query_v4.py]
用户查询结果
```

## 数据 schema

每条记录包含 13 个标准字段 + 1 个可选字段：

| 字段 | 说明 | 示例 |
|------|------|------|
| `source_file` | 原始 md 源文件路径 | `md_output/volume_015/paper.md` |
| `material_name` | 材料名称 | `Zircaloy-4`, `Zr-2.5Nb` |
| `composition` | 成分 | `Zr-2.5Nb`, `UO2` |
| `phase` | 测量对象所属物相 | `alpha`, `beta`, `oxide` |
| `element` | 直接相关元素 | `hydrogen`, `oxygen` |
| `property_category` | 性能大类（13 类固定枚举） | `腐蚀`, `密度`, `弹塑性模型` |
| `property` | 具体性能名 | `屈服强度`, `氧化膜厚度` |
| `value` | 数值（保留原文精度） | `450`, `3 to 4` |
| `unit` | 单位 | `MPa`, `μm` |
| `conditions` | 实验/模拟条件 (JSONB) | `{"temp_C": 350, "dpa": 1.2}` |
| `context` | 上下文补充说明 | — |
| `confidence` | 置信度 | `high` / `medium` / `low` |
| `reference` | 文献来源 | `Author, Title` |
| `property_note` *(可选)* | 目录外标注 | `目录外` |

### 性能大类（property_category）

| 类别 | 是否核心 | 说明 |
|------|---------|------|
| 密度 | ✅ | density |
| 比热容 | ✅ | specific heat |
| 热传导率 | ✅ | thermal conductivity |
| 弹塑性模型 | ✅ | 弹性、塑性、本构、流动曲线 |
| 热膨胀 | ✅ | 线膨胀系数等 |
| 辐照蠕变 | ✅ | irradiation creep |
| 辐照肿胀 | ✅ | swelling / void swelling |
| 腐蚀 | ✅ | oxidation, corrosion, SCC 等 |
| 硬化性能 | ✅ | irradiation hardening 等 |
| 材料规格/组织信息 | ➖ | 尺寸、晶粒尺寸、相分数等 |
| 其他性能 | ➖ | 目录外但可抽取的数据 |

## 使用方法

### 前置条件

1. **Python 3.10+** 安装
2. **Supabase** 账号 + 已创建 `nuclear_properties_v4` 表
3. **PDF 转 Markdown 脚本**（`pdf_to_md_v2.py`）
4. **LLM**（用于语义抽取步骤）

### 安装

将技能目录复制到你的 Agent skills 路径下：

```bash
# Claude Code
cp -r nuclear-*-v4 ~/.claude/skills/

# OpenClaw
cp -r nuclear-*-v4 ~/.openclaw/skills/

# OpenCode
cp -r nuclear-*-v4 .opencode/skills/

# Cursor / Codex / 其他 Agent
# 放到对应 skills 目录即可
```

### 配置环境变量

```bash
# Supabase 连接（导入和查询都需要）
export SUPABASE_URL="https://your-project.supabase.co"
export SUPABASE_KEY="your-service-role-or-anon-key"

# 可选：自定义脚本路径
export PDF_TO_MD_SCRIPT="/path/to/pdf_to_md_v2.py"
export IMPORTER_SCRIPT="/path/to/import_to_supabase_v4.py"
```

### 创建数据库表

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

### 端到端使用

在任意 Agent（Claude Code / OpenClaw / Codex / Cursor 等）中直接说：

> "把 `pdf/` 目录下的论文批量处理成 Supabase 数据"

Agent 会自动按以下流程执行：

1. **PDF → Markdown**：调用 `pdf_to_md_v2.py` 转换
2. 🔴 **CHECKPOINT**：确认生成的 md 文件列表
3. **Markdown → JSON**：LLM 逐篇语义抽取
4. 🔴 **CHECKPOINT**：确认抽取统计
5. **dry-run 导入预览**
6. 🔴 **CHECKPOINT**：确认后正式导入

### 单独使用各技能

#### 只做语义抽取

> "抽取 `md_output/volume_015/paper_A.md` 的核材料性能数据"

使用 `nuclear-property-extraction-v4` 的规则，逐篇 LLM 抽取。

#### 查询数据

> "查一下 Zr-2.5Nb 的腐蚀数据"

使用 `nuclear-query-v4` 查询 Supabase。

#### 导入已有 JSON

> "导入 `extraction_results/project_v4/` 目录下的 JSON 到 Supabase"

使用 `supabase-importer-v4`。

## 核心设计原则

1. **LLM 语义抽取，不是正则脚本**：Markdown → JSON 的核心判断必须由 LLM 完成，不能简化为正则/关键词/表格模板
2. **全文扫描**：Abstract、正文、表格、图注、Discussion、Appendix 全覆盖
3. **溯源**：每条记录都有 `source_file` 和 `reference`
4. **精度保留**：不删除尾零，保留范围值和科学计数法
5. **人在回路**：关键步骤有 🔴 CHECKPOINT 暂停确认

## Runtime 兼容性

本技能套件使用 Agent Skills Standard 格式，兼容：

- Claude Code
- OpenClaw
- Codex
- Cursor
- OpenCode
- Hermes Agent
- Gemini CLI
- 任何支持 SKILL.md 格式的 Agent

## 技术评估

经 Darwin Skill 2.0 九维 rubric 评估（基于 SkillLens arXiv 2605.23899）：

| 维度 | 说明 |
|------|------|
| 工作流清晰度 | Step 1/2/3 分段 + 8 步执行顺序 |
| 失败模式编码 | 三段式 fallback 表（触发/一线修复/兜底） |
| 检查点设计 | 🔴 CHECKPOINT 关键步骤暂停 |
| 可执行具体性 | 环境变量参数化 + 具体 JSON schema |
| 反例黑名单 | "不抽取"清单 + "禁止"清单 |

## License

MIT

## 相关项目

- [Darwin Skill 2.0](https://github.com/alchaincyf/darwin-skill) — 本套件经 Darwin Skill 评估优化
- [Supabase](https://supabase.com) — 数据存储后端
