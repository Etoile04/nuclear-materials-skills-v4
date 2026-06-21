# 抽取判断规则（项目对齐版）

## 0. 全文完整扫描

必须扫描论文所有部分：

| 位置 | 常见数据 |
|---|---|
| Abstract | 关键性能范围、材料状态、实验/模拟结果 |
| 正文 | 材料、成分、条件、性能值、模型参数 |
| 表格 | 高密度结构化数据 |
| 图注 | 标尺、测量值、条件说明 |
| Discussion/Q&A | 讨论者提供的一手实验数据 |
| Appendix | 补充表、模型参数、拟合参数 |

不得只处理表格。

---

## 1. 源文件溯源

每条记录必须包含：

```json
"source_file": "md_output/.../xxx.md"
```

规则：

1. 填当前正在处理的 Markdown 源文件相对路径。
2. 不填输出 JSON 文件名。
3. 不填论文标题。
4. 一个 Markdown 文件包含多篇论文时，所有记录使用同一个 `source_file`。
5. 具体论文来源由 `reference` 区分。

---

## 2. 多论文文件处理

一个 MD 文件可能包含多篇论文。

识别信号：

| 信号 | 说明 |
|---|---|
| `REFERENCE:` | 通常标志一篇新论文开始 |
| 新标题 + 作者 | 可能是新论文 |
| 新 ABSTRACT | 可能是新论文 |

处理规则：

1. 先扫描全文，标记所有论文起止位置。
2. 逐篇独立抽取。
3. 每篇使用自己的 `reference`。
4. 不得只处理第一篇。

---

## 3. 单条数据抽取推理链

遇到一个候选数值时按顺序判断：

```text
1. 是否可抽？
   用 property_catalog.md 的四问判断。

2. 属于哪个性能大类？
   填 property_category。

3. 属于哪个材料？
   填 material_name 和 composition。

4. 属于哪个物相？
   用 phase_rules.md 判断 phase。

5. 是否直接关联某元素？
   填 element。

6. 条件是什么？
   填 conditions。

7. 其他字段是否足以理解？
   不足则填 context。

8. 置信度是多少？
   填 confidence。
```

---

## 4. material_name / composition 提取

### 4.1 material_name

填材料名、合金牌号、样品材料或构件材料。

示例：

```json
"material_name": "Zircaloy-4"
"material_name": "Zr-2.5Nb"
"material_name": "UO2"
```

### 4.2 composition

填原文明确给出的成分、化学式、名义成分或材料名中直接包含的成分。

规则：

| 情况 | composition |
|---|---|
| `Zr-2.5Nb` | `Zr-2.5Nb` |
| `UO2` | `UO2` |
| `Zircaloy-4`，原文无成分 | null |
| 表格给出 Sn 1.5 wt%, Fe 0.2 wt% | 按原文组合为字符串 |
| 仅凭常识知道成分 | 不填 |

不得外推补全。

---

## 5. element 推理

`element` 只在性能与特定元素直接相关时填写。

| 情况 | element |
|---|---|
| oxygen content | `oxygen` |
| hydrogen pickup | `hydrogen` |
| deuterium uptake | `deuterium` |
| iodine SCC threshold | `iodine` |
| Sn content | `tin` |
| 普通屈服强度 | null |
| 普通热导率 | null |

元素名称用英文小写。

---

## 6. conditions 提取

`conditions` 只填与该数据点直接相关的条件。

必须优先包含：

```json
"condition_type": "experimental | simulation | service | processing | mixed | unknown"
```

### 6.1 常见字段

| 字段 | 类型 | 说明 |
|---|---|---|
| `condition_type` | string | 条件类型 |
| `temp_C` | number/string | 摄氏温度 |
| `temp_K` | number/string | 开尔文温度 |
| `pressure_MPa` | number/string | 压力 |
| `stress_MPa` | number/string | 应力 |
| `strain_rate_s-1` | number/string | 应变率 |
| `time_h` | number/string | 时间 |
| `dpa` | number/string | 辐照剂量 |
| `fluence_n/m2` | string | 中子注量 |
| `flux_n/m2/s` | string | 中子通量 |
| `burnup_GWd/t` | number/string | 燃耗 |
| `atmosphere` | string | 气氛、介质、环境 |
| `simulation_method` | string | DFT / MD / FEM / phase-field 等 |
| `model_name` | string | 本构或模拟模型名 |
| `processing_state` | string | 热处理、冷加工、挤压等 |

### 6.2 条件来源限制

1. 优先使用同句、同一表格行、同一图注中的条件。
2. 表格标题或章节标题中的全局条件可用于该表或该节数据。
3. 不跨段落推断条件，除非该条件是明确的全局实验设置。
4. 无条件时写 `null`。

---

## 7. 数值格式

### 7.1 value

`value` 始终为字符串。

| 原文 | value |
|---|---|
| `150 ppm` | `"150"` |
| `3 to 4 μm` | `"3 to 4"` |
| `~200 MPa` | `"~200"` |
| `approximately 8 GWd/t` | `"~8"` |
| `200 ± 10 MPa` | `"200 ± 10"` |
| `1.5 × 10⁻³` | `"1.5×10^-3"` |

### 7.2 保留精度

不得删除尾零。

| 原文 | 正确 | 错误 |
|---|---|---|
| `7.90 Å` | `"7.90"` | `"7.9"` |
| `10.0 nm` | `"10.0"` | `"10"` |
| `0.20 %` | `"0.20"` | `"0.2"` |

### 7.3 范围值

同一量的上下限合并为一条记录。

| 原文 | value |
|---|---|
| `from 3 to 4 μm` | `"3 to 4"` |
| `between 10 and 20 MPa` | `"10 to 20"` |
| `ranged from 5 to 15 μm` | `"5 to 15"` |

如果是不同条件下的两个值，拆成两条。

示例：

```text
200 MPa at 25°C and 150 MPa at 300°C
```

输出两条记录。

---

## 8. LaTeX 清洗

输出字段不得残留 `$`, `\`, `{}`, LaTeX 下标或上标。

| LaTeX | 输出 |
|---|---|
| `${ZrO}_{2}$` | `ZrO2` |
| `$7\times10^{25}$` | `7×10^25` |
| `$m^{2}$` | `m²` |
| `$\mu{m}$` | `μm` |
| `$325{{\circ}}_{{C}}$` | `325°C` |
| `$\alpha$` | `alpha` |

---

## 9. 表格处理

先判断表格类型。

| 表格类型 | 处理方式 |
|---|---|
| 性能数据表 | 逐行逐列抽取，每个有效数值独立一条记录 |
| 材料规格表 | 可抽取，但通常归入 `材料规格/组织信息` |
| 晶体结构/组织表 | 可抽取，通常归入 `材料规格/组织信息` |
| 实验条件表 | 不作为独立记录，作为 conditions 使用 |
| 模拟参数表 | 若为正式模型参数或模拟结果，则抽取；若为任意输入参数，则只作 conditions 或跳过 |

跳过：样品编号、图号、文献编号、空值、N/A、定性状态。

---

## 10. Discussion / Q&A 处理

抽取：

- 讨论者提供的一手实验数据。
- 作者回复中新给出的定量数据。

不抽取：

- 讨论者引用别人文献的数据。
- 纯提问或定性评论。

Discussion 数据：

1. `reference` 使用主论文 reference。
2. `context` 写明 `Discussion部分，[讨论者姓名]提供的数据：...`。

---

## 11. reference 提取

格式：

```text
作者, 文章标题
```

去掉期刊、会议、年份、页码、DOI。

示例：

```text
REFERENCE: Pawel, R. E. and Campbell, J. J., "A Comparison of the High-Temperature Oxidation Behavior of Zircaloy-4 and Pure Zirconium," Zirconium in the Nuclear Industry; Fifth Conference, ASTM STP 754, 1982, pp. 370-389.
```

输出：

```json
"reference": "Pawel, R. E. and Campbell, J. J., A Comparison of the High-Temperature Oxidation Behavior of Zircaloy-4 and Pure Zirconium"
```

---

## 12. 输出格式

输出 JSON 数组。

字段顺序固定：

```text
source_file → material_name → composition → phase → element → property_category → property → value → unit → conditions → context → confidence → reference
```

表外性能可选追加：

```json
"property_note": "目录外"
```

### 示例

```json
[
  {
    "source_file": "md_output/volume_015/paper.md",
    "material_name": "Zr-2.5Nb",
    "composition": "Zr-2.5Nb",
    "phase": "beta",
    "element": null,
    "property_category": "材料规格/组织信息",
    "property": "相分数",
    "value": "~80",
    "unit": "%",
    "conditions": {
      "condition_type": "processing",
      "temp_K": 1090
    },
    "context": "挤压温度下 beta 锆相的体积分数",
    "confidence": "high",
    "reference": "Urbanic, V. F., Warr, B. D., Manolescu, A., Chow, C. K., and Shanahan, M. W., Oxidation and Deuterium Uptake of Zr-2.5Nb Pressure Tubes in CANDU-PHW Reactors",
    "property_note": "目录外"
  }
]
```

---

## 13. confidence 规则

| 条件 | confidence |
|---|---|
| source_file + material_name + property_category + property + value + unit + reference 齐全，且 phase/conditions 明确 | `high` |
| material_name + property + value + unit + reference 齐全，但 phase 或 conditions 不明确 | `medium` |
| 只有 property + value + unit，可定位材料但上下文不足 | `low` |

无材料对象的数据不抽取。

---

## 14. 不抽取

| 类型 | 示例 | 原因 |
|---|---|---|
| 趋势 | increases with temperature | 无具体数字 |
| 定性比较 | higher than control | 无绝对值 |
| 图号/表号 | Fig. 3, Table 2 | 编号 |
| 样品编号 | 165F | 标识符 |
| 文献引用编号 | [12], Ref. 5 | 不是性能 |
| 纯测试条件 | test temperature 300°C | 写入 conditions，不独立抽取 |
| 纯模型假设 | assumed parameter = 1 | 非实验/模拟结果 |
| 二手引用 | Smith reported 400 MPa | 非当前论文数据 |

---

## 15. 自检

输出前逐条检查：

1. 是否有 `source_file`。
2. 是否有 `reference`。
3. 是否有 `material_name`。
4. `composition` 是否来自原文或材料名本身。
5. `property_category` 是否是固定枚举。
6. `property`、`value`、`unit` 是否完整。
7. `value` 是否保留原文精度。
8. `phase` 是否跟测量对象走。
9. 实验/模拟/服役/制备条件是否进入 `conditions`。
10. 制备参数是否误归入核心性能。
