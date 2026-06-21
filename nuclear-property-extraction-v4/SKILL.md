---
name: nuclear-property-extraction-v4
description: "项目任务书对齐版核材料性能数据抽取系统。从 md_output/ 下 Markdown 文献中抽取核材料性能数据,输出带源文件溯源、材料名称/成分、实验或模拟条件、任务性能大类、具体性能值和文献来源的结构化 JSON。"
---

# 核材料性能数据抽取系统(项目对齐版 v4.0)

## 项目目标

从 `md_output/` 目录下的 Markdown 核材料文献中抽取尽可能多的核材料性能数据。

每条数据必须能够对应项目任务书中的字段:

| 项目任务书字段 | 本 skill 输出字段 |
|---|---|
| 材料名称 | `material_name` |
| 成分 | `composition` |
| 实验条件 / 模拟条件 | `conditions` |
| 性能数据 | `property_category` + `property` + `value` + `unit` |
| 文献来源 | `reference` + `source_file` |

任务书中的 `/` 表示"或者"。例如"密度/比热容/热传导率/......"表示每条记录属于其中一种性能大类,而不是要求每条记录同时包含所有性能。


## 0. 执行模式：LLM语义抽取，不是规则脚本抽取

本 skill 的目标不是编写一个基于正则、关键词或表格模板的批量抽取脚本。

执行者必须使用 LLM 的语言理解能力，逐篇阅读 Markdown 文献内容，并根据本文档及 references 下规则进行语义判断、归属推理和结构化输出。

禁止将本 skill 简化为以下形式：

- 仅用正则表达式匹配"数字 + 单位"
- 仅用关键词表判断 property
- 仅解析表格而忽略正文、图注、Discussion 和 Appendix
- 用固定规则脚本自动决定 phase、property_category、conditions、confidence
- 不阅读上下文就批量生成 JSON

允许使用脚本的范围仅限于：

- 遍历 md 文件
- 读取文件内容
- 创建输出目录
- 保存 LLM 已完成抽取的 JSON 结果
- 做 JSON 格式校验

核心抽取行为必须由 LLM 完成，包括：

- 判断某个数值是否属于核材料性能数据
- 判断材料名称和成分
- 判断实验条件或模拟条件
- 判断 property 与 property_category
- 判断 phase 是否适用
- 判断 context 和 confidence
- 排除二手引用、纯实验条件、孤立无归属数值

换言之，脚本可以负责"搬运文件和保存结果"，但不能负责"理解论文和决定抽取内容"。

### 批量抽取前确认

🔴 **CHECKPOINT · 开始抽取前**
- 展示待处理的 md 文件列表和总数
- 抽取第 1 个文件作为样板，展示给用户确认
- 等用户确认样板格式后再批量处理剩余文件

### 常见失败模式与处理

| 触发条件 | 一线修复 | 仍失败兜底 |
|---------|---------|------------|
| LLM 输出非法 JSON（字段缺失、语法错误）| 用 `python3 -m json.tool` 校验，定位错误位置，重试一次 | 记录失败文件，跳过继续处理其他文件 |
| 无法判断 material_name | 检查 ABSTRACT 和 REFERENCE 行；若全文无明确材料名则填 null | 若也无 composition 则该数据点不抽取 |
| property_category 无法对齐固定枚举 | 优先选"其他性能"并标注 `property_note: "目录外"` | 该数据点不抽取 |
| phase 判断不确定 | 按 phase_rules.md 三步法推理；不确定时填 null 并在 context 说明 | phase 填 null，不要猜测 |
| conditions 无法确定 | 检查同句/同行/同表标题；无条件时填 null | 不要跨段落推断条件 |
| 一个 md 文件中有多篇论文 | 按 REFERENCE 行分篇处理，每篇独立抽取 | 若无法区分论文边界，全文作为一篇处理并在 context 说明 |

---

## 1. 数据源

**抽取目录**:`md_output/`

该目录下有若干 Markdown 文件或子文件夹。每个 Markdown 文件可能包含一篇或多篇论文。

每条输出记录必须包含 `source_file` 字段,填写当前数据点所在 Markdown 文件的相对路径。

---

## 2. 执行前必读

开始抽取前必须读取并遵守:

```text
references/phase_rules.md      → 物相归属与标准化
references/property_catalog.md → 性能可抽取性、任务性能大类、单位规范
references/extraction_rules.md → 全文扫描、数值格式、条件、reference、输出格式
```

这些文件提供推理规则,不是简单查表。

---

## 3. 核心抽取对象

本 skill 抽取的是:

> 某个核材料或物相,在某个实验条件、模拟条件、服役条件或制备状态下,某一项性能或材料状态参数的数值。

核心性能优先抽取,支持信息可抽取但必须标记清楚。

---

## 4. 性能大类

`property_category` 必须从以下固定枚举中选择:

| property_category | 是否计入项目核心性能数据 | 说明 |
|---|---:|---|
| `密度` | 是 | density |
| `比热容` | 是 | specific heat / heat capacity |
| `热传导率` | 是 | thermal conductivity / thermal diffusivity 等 |
| `弹塑性模型` | 是 | 弹性、塑性、本构、流动曲线、模型参数 |
| `热膨胀` | 是 | 线膨胀系数、热膨胀应变等 |
| `辐照蠕变` | 是 | irradiation creep / creepdown / creep strain / creep rate |
| `辐照肿胀` | 是 | swelling / void swelling / gas bubble swelling |
| `腐蚀` | 是 | oxidation, corrosion, hydriding, deuterium uptake, SCC 等 |
| `硬化性能` | 是 | hardening modulus, hardening exponent, irradiation hardening, strength increase 等 |
| `材料规格/组织信息` | 否 | 尺寸、壁厚、冷加工量、相分数、晶粒尺寸、析出相尺寸等 |
| `其他性能` | 否 | 通过可抽取性判断但不属于上述类别的数据 |

优先提取前 9 类核心性能数据。`材料规格/组织信息` 和 `其他性能` 可以保留,但不应混入核心性能计数

---

## 5. 输出字段

每条记录输出为一个固定字段对象,不再称为十元组或十一元组。

字段顺序固定:

```text
source_file → material_name → composition → phase → element → property_category → property → value → unit → conditions → context → confidence → reference
```

可选追加字段:

```text
property_note
```

当 `property` 不在 `property_catalog.md` 标准表中但通过可抽取性判断时,添加:

```json
"property_note": "目录外"
```

---

## 6. 字段说明

| 字段 | 类型 | 说明 |
|---|---|---|
| `source_file` | string | Markdown 源文件相对路径,例如 `md_output/volume_015/paper.md` |
| `material_name` | string/null | 材料名称、合金牌号或样品材料,例如 `Zircaloy-4`, `Zr-2.5Nb` |
| `composition` | string/null | 成分、化学式、名义成分或实测成分。不得凭常识补全原文未给出的成分 |
| `phase` | string/null | 数据测量对象所属物相,按 `phase_rules.md` 标准化 |
| `element` | string/null | 该性能直接相关的元素,如 `oxygen`, `hydrogen`, `iodine`;无直接元素对象则为 null |
| `property_category` | string | 固定枚举,见第 4 节 |
| `property` | string | 具体性能名称,优先用 `property_catalog.md` 标准名称 |
| `value` | string | 数值,必须保留原文精度、范围、约数和科学计数法格式 |
| `unit` | string/null | 单位。无量纲但有物理意义的参数可填 `dimensionless` |
| `conditions` | object/null | 实验条件、模拟条件、服役条件或制备状态;只填与该数据点直接相关的条件 |
| `context` | string/null | 其他字段不足以理解时补充说明 |
| `confidence` | string | `high` / `medium` / `low` |
| `reference` | string | 文献来源,格式为 `作者, 文章标题` |

---

## 7. material_name 与 composition 规则

1. `material_name` 填材料名称、合金牌号或样品名称。
2. `composition` 填原文明确给出的化学组成、名义成分、实测成分或能直接从材料名读取的成分。
3. `Zr-2.5Nb` 这类名称本身包含成分信息时:
   - `material_name`: `Zr-2.5Nb`
   - `composition`: `Zr-2.5Nb`
4. `Zircaloy-2` 这类牌号如果原文未给具体成分:
   - `material_name`: `Zircaloy-2`
   - `composition`: `null`
5. 不得用外部常识补全未在当前论文中出现的成分。

---

## 8. conditions 规则

`conditions` 可表示实验、模拟、服役或制备状态。

必须优先填入:

```json
{
  "condition_type": "experimental | simulation | service | processing | mixed | unknown"
}
```

常见字段包括:

| 字段 | 说明 |
|---|---|
| `condition_type` | 条件类型 |
| `temp_C` / `temp_K` | 温度 |
| `pressure_MPa` | 压力 |
| `stress_MPa` | 应力 |
| `strain_rate_s-1` | 应变率 |
| `time_h` | 时间 |
| `dpa` | 辐照剂量 |
| `fluence_n/m2` | 中子注量 |
| `flux_n/m2/s` | 中子通量 |
| `burnup_GWd/t` | 燃耗 |
| `atmosphere` | 气氛/介质 |
| `simulation_method` | DFT / MD / FEM / phase-field / CALPHAD 等 |
| `model_name` | Johnson-Cook / Ramberg-Osgood / Norton creep 等 |
| `processing_state` | annealed / cold-worked / beta-quenched / extruded 等 |

实验条件和模拟条件都可以进入 `conditions`。不要把纯测试环境作为独立性能数据。

---

## 9. 全文完整扫描

必须扫描论文每个部分:

1. `REFERENCE:` 和标题信息
2. Abstract
3. 正文段落
4. 所有表格
5. 图注
6. Discussion / Q&A
7. Appendix / Supplementary data

表格、正文、图注和 Discussion 中的有效数值都要判断,不得只抽表格。

---

## 10. 多论文文件处理

一个 Markdown 文件可能包含多篇论文。

处理规则:

1. 先扫描全文,识别所有 `REFERENCE:` 行。
2. 每个 `REFERENCE:` 行通常标志一篇新论文开始。
3. 逐篇独立抽取,每篇使用各自的 `reference`。
4. 同一个 Markdown 文件内不同论文的记录使用相同 `source_file`。
5. 不得只处理第一篇论文。

---

## 11. 抽取优先级

优先级从高到低:

1. 项目核心性能数据:9 个核心 `property_category`。
2. 与核心性能直接相关的模型参数、拟合参数、曲线参数。
3. 支持性材料状态信息:成分、冷加工、热处理、尺寸、相分数、晶粒尺寸等。
4. 其他通过可抽取性判断的材料数据。

若同一处数据既可作为条件又可作为材料状态,优先作为 `conditions` 或 `context`,不要强行作为核心性能。

---

## 12. 不抽取

不抽取以下内容:

- 无具体数字的趋势或定性描述
- 图号、表号、样品编号、文献编号
- 无材料对象也无物相对象的孤立数值
- 二手引用数据,除非任务明确要求文献汇总型抽取
- 没有明确材料对象、条件或单位的模型假设值
- 纯测试条件作为独立记录
- 反应堆系统几何参数,除非它直接描述被测材料样品或材料构件

---

## 13. 输出示例

```json
[
  {
    "source_file": "md_output/volume_015/paper.md",
    "material_name": "Zr-2.5Nb",
    "composition": "Zr-2.5Nb",
    "phase": "oxide",
    "element": null,
    "property_category": "腐蚀",
    "property": "氧化膜厚度",
    "value": "3 to 4",
    "unit": "μm",
    "conditions": {
      "condition_type": "service",
      "temp_C": 300,
      "time_h": 1000
    },
    "context": null,
    "confidence": "high",
    "reference": "Author, Paper Title"
  }
]
```

---

## 14. 输出路径与文件命名

JSON 文件写入:

```text
extraction_results/project_v4/
```

输出规则:

- **一个源 Markdown 文件对应一个 JSON 文件**。
- 每个 JSON 文件中可以包含该 md 文件抽取出的多条数据记录。
- JSON 文件名必须与源 md 文件名一致,仅将扩展名改为 `.json`。
- 不再使用 `volume_NNN.json` 这种统一编号命名方式。

示例:

```text
md_output/volume_015/paper_A.md
→ extraction_results/project_v4/paper_A.json

md_output/volume_016/Urbanic_CANDU_pressure_tubes.md
→ extraction_results/project_v4/Urbanic_CANDU_pressure_tubes.json
```

注意:如果一个 md 文件中包含多篇独立论文,仍然只输出一个同名 JSON 文件;不同论文的数据通过 `reference` 字段区分。

---

## 15. 自检门控

输出前必须检查:

1. `source_file` 是否存在。
2. `material_name` 是否尽可能填写。
3. `composition` 是否只来自原文或材料名本身,不凭外部常识补全。
4. `property_category` 是否属于固定枚举。
5. 核心性能是否正确归入 9 个项目类别。
6. 制备温度、冷加工量、样品尺寸等是否误归为核心性能。
7. `phase` 是否跟测量对象走。
8. `value` 是否保留原文精度和范围。
9. `conditions` 是否只填与该数据点直接相关的条件。
10. `reference` 是否为当前论文,而不是 Discussion 讨论者或被引用文献。
