# 性能分类与单位规范（项目对齐版）

## 0. 功能

本文件负责两件事：

1. 判断一个数值是否是可抽取的核材料数据。
2. 将具体 `property` 映射到项目任务书要求的 `property_category`。

标准表不是穷举清单。表外有效数据可以抽取，但必须标注 `property_note: "目录外"`。

---

## 1. 可抽取性判断

### 1.1 第一性原理

可抽取数据必须满足：

1. 有明确材料对象或物相对象。
2. 有可量化数值，含单值、范围、约数、误差或科学计数法。
3. 描述材料性能、材料状态、组织特征、成分、模型参数或服役行为。
4. 来自实验测量、实验观察、实验拟合、正式报告的模拟结果，或经实验/模拟标定的模型参数。
5. 能独立理解，或可通过 `conditions` / `context` 补足语义。

---

### 1.2 四问判断

遇到每个数值时依次判断：

```text
Q1：这个数值描述的是材料、物相、成分、组织、性能或模型参数吗？
  是 → 继续
  否 → 跳过

Q2：它来自实验、观察、拟合、模拟结果或模型标定吗？
  是 → 继续
  纯假设、图号、编号、文献编号 → 跳过

Q3：它有单位，或是有明确物理意义的无量纲数吗？
  是 → 继续
  否 → 跳过

Q4：知道材料、条件和性能名后能否理解这个值？
  是 → 抽取
  否 → 跳过或写入 context 后抽取
```

---

## 2. 数据类型

| 类型 | 是否抽取 | 说明 |
|---|---:|---|
| 核心性能数据 | 是 | 计入项目 9 类核心性能 |
| 弹塑性/腐蚀/蠕变等模型参数 | 是 | 若来自实验拟合、模拟标定或论文正式报告 |
| 材料规格/组织信息 | 是 | 不计入核心性能计数，但可保留 |
| 成分数据 | 是 | 可作为材料成分信息，也可形成记录 |
| 实验条件/模拟条件 | 否 | 不独立抽取，写入 `conditions` |
| 纯系统结构参数 | 通常不抽 | 只有直接描述被测材料或构件时才抽 |

---

## 3. property_category 固定枚举

`property_category` 只能取以下值：

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
材料规格/组织信息
其他性能
```

前 9 类为项目核心性能类别。

---

## 4. 核心性能分类表

### 4.1 密度

| 标准 property | 标准单位 | 原文关键词 |
|---|---|---|
| 密度 | `g/cm³` | density |
| 理论密度 | `g/cm³` | theoretical density |
| 相对密度 | `%` | relative density |

`property_category`: `密度`

---

### 4.2 比热容

| 标准 property | 标准单位 | 原文关键词 |
|---|---|---|
| 比热容 | `J·kg⁻¹·K⁻¹` | specific heat, heat capacity |
| 定压比热容 | `J·kg⁻¹·K⁻¹` | Cp, heat capacity at constant pressure |

`property_category`: `比热容`

---

### 4.3 热传导率

| 标准 property | 标准单位 | 原文关键词 |
|---|---|---|
| 热导率 | `W·m⁻¹·K⁻¹` | thermal conductivity |
| 热扩散率 | `m²·s⁻¹` | thermal diffusivity |
| 热阻 | `K·W⁻¹` | thermal resistance |

`property_category`: `热传导率`

---

### 4.4 弹塑性模型

包括弹性参数、塑性参数、本构模型参数和应力-应变曲线数据。

| 标准 property | 标准单位 | 原文关键词 |
|---|---|---|
| 杨氏模量 | `GPa` | Young's modulus, elastic modulus |
| 剪切模量 | `GPa` | shear modulus |
| 体积模量 | `GPa` | bulk modulus |
| 泊松比 | `dimensionless` | Poisson's ratio |
| 弹性常数 | `GPa` | elastic constants, stiffness tensor, C11, C12, C44 |
| 屈服强度 | `MPa` | yield strength, yield stress, 0.2% offset |
| 抗拉强度 | `MPa` | tensile strength, UTS, ultimate strength |
| 流动应力 | `MPa` | flow stress |
| 断裂应变 | `%` | fracture strain, burst strain |
| 延伸率 | `%` | elongation, ductility |
| Ramberg-Osgood参数 | 原文单位 | Ramberg-Osgood |
| Johnson-Cook参数 | 原文单位 | Johnson-Cook |
| 屈服准则参数 | 原文单位 | yield criterion, Hill, von Mises parameter |
| 本构模型参数 | 原文单位 | constitutive parameter, material constant |

`property_category`: `弹塑性模型`

注意：若同一参数同时表示硬化行为，优先归入 `硬化性能`。

---

### 4.5 热膨胀

| 标准 property | 标准单位 | 原文关键词 |
|---|---|---|
| 平均线膨胀系数 | `10⁻⁶ K⁻¹` | mean thermal expansion, average CTE |
| 瞬时线膨胀系数 | `10⁻⁶ K⁻¹` | instantaneous thermal expansion, instantaneous CTE |
| 热膨胀应变 | `%` | thermal expansion strain |
| 体膨胀系数 | `K⁻¹` | volumetric thermal expansion |

`property_category`: `热膨胀`

---

### 4.6 辐照蠕变

| 标准 property | 标准单位 | 原文关键词 |
|---|---|---|
| 蠕变应变 | `%` | creep strain, irradiation creep strain, creepdown strain |
| 稳态蠕变速率 | `s⁻¹` | steady-state creep rate |
| 瞬态蠕变速率 | `s⁻¹` | transient creep rate |
| 辐照蠕变速率 | `s⁻¹` | irradiation creep rate |
| 蠕变柔量 | 原文单位 | creep compliance |
| 应力指数 | `dimensionless` | stress exponent, creep exponent |
| Norton蠕变参数 | 原文单位 | Norton creep, creep law parameter |
| 失效时间 | `s` 或 `h` | time-to-failure, rupture time under creep |

`property_category`: `辐照蠕变`

只有在辐照、服役或 cladding/pressure tube creep 语境下归为 `辐照蠕变`；普通高温蠕变若无辐照语境，可归入 `弹塑性模型` 或 `其他性能`。

---

### 4.7 辐照肿胀

| 标准 property | 标准单位 | 原文关键词 |
|---|---|---|
| 体积膨胀率 | `%` | volume swelling |
| 空洞肿胀率 | `%` | void swelling |
| 气泡肿胀率 | `%` | gas bubble swelling |
| 尺寸变化率 | `%` | dimensional change, irradiation growth |
| 平均空洞尺寸 | `nm` | average void size, mean void diameter |
| 空洞密度 | `m⁻³` | void density |
| 气泡密度 | `m⁻³` | bubble density, bubble number density |

`property_category`: `辐照肿胀`

---

### 4.8 腐蚀

包括腐蚀、氧化、吸氢、吸氘和应力腐蚀开裂。

| 标准 property | 标准单位 | 原文关键词 |
|---|---|---|
| 腐蚀速率 | `mm/a` | corrosion rate |
| 氧化速率 | 原文单位 | oxidation rate |
| 氧化膜厚度 | `μm` | oxide thickness, oxide layer thickness |
| 氧化增重 | `mg/dm²` | weight gain, mass gain |
| 吸氢率 | `%` | hydrogen pickup, H pickup fraction |
| 氢含量 | `ppm` | hydrogen content, H content |
| 吸氘率 | `%` | deuterium uptake, deuterium pickup |
| 氘含量 | `ppm` | deuterium content, D content |
| 应力腐蚀阈值 | `MPa` | SCC threshold, stress corrosion cracking threshold |
| 裂纹扩展速率 | `m/cycle` | crack growth rate |
| 腐蚀疲劳裂纹扩展速率 | `m/cycle` | corrosion fatigue crack growth rate |
| 点蚀密度 | `cm⁻²` | pitting density, pit density |

`property_category`: `腐蚀`

---

### 4.9 硬化性能

| 标准 property | 标准单位 | 原文关键词 |
|---|---|---|
| 硬度 | `HV` | hardness, Vickers hardness, microhardness |
| 硬化模量 | `MPa` | hardening modulus |
| 硬化指数 | `dimensionless` | strain hardening exponent |
| 辐照硬化量 | `MPa` | irradiation hardening, yield strength increase |
| 强度增量 | `MPa` | strength increment, increase in yield stress |
| 位错硬化参数 | 原文单位 | dislocation hardening parameter |

`property_category`: `硬化性能`

---

## 5. 支持性数据分类

### 5.1 材料规格/组织信息

该类可以抽取，但不计入项目核心性能数量。

| property 示例 | 原文关键词 |
|---|---|
| 样品外径 | outside diameter |
| 样品内径 | inside diameter |
| 壁厚 | wall thickness |
| 燃料段长度 | fuelled length, fuel segment length |
| 冷加工量 | cold work, cold reduction |
| 热处理温度 | annealing temperature, heat treatment temperature |
| 挤压温度 | extrusion temperature |
| 晶粒尺寸 | grain size |
| 相分数 | phase fraction, volume fraction |
| 析出相尺寸 | precipitate size, SPP size |
| 位错密度 | dislocation density |
| 晶格参数a | lattice parameter a |
| 晶格参数c | lattice parameter c |
| 晶面间距 | interplanar distance, d-spacing |
| 织构系数 | texture coefficient, Kearns factor |

`property_category`: `材料规格/组织信息`

规则：若制备温度、冷加工量、热处理参数只是样品制备信息，归入本类；不要归入核心性能。

---

### 5.2 其他性能

通过四问判断但无法归入上述类别的数据，归入：

`property_category`: `其他性能`

必须添加：

```json
"property_note": "目录外"
```

---

## 6. 模拟数据规则

正式报告的模拟/计算材料性能可以抽取。

可接受来源包括：

- DFT
- molecular dynamics / MD
- finite element / FEM
- phase-field
- CALPHAD
- cluster dynamics
- rate theory
- experimentally calibrated model

要求：

1. 有明确材料或物相。
2. 有明确模拟方法或模型。
3. 有数值和单位，或有物理意义的无量纲参数。
4. `conditions.condition_type = "simulation"`。
5. 模拟方法写入 `conditions.simulation_method`。

不抽取：

- 没有材料对象的纯模型假设参数。
- 仅用于示意的任意参数。
- 未标明来源的默认参数。

---

## 7. 单位规范

原则：保留原文单位，不换算。

常见标准化：

| 原文/OCR | 输出 |
|---|---|
| `um`, `µm` | `μm` |
| `Angstrom`, 晶格上下文中的 `A` | `Å` |
| `percent` | `%` |
| `deg C`, `degrees C` | `°C` |
| 无量纲参数 | `dimensionless` |
| `m2`, `m^2` | `m²` |
| `s-1`, `s^-1` | `s⁻¹` |

---

## 8. 分类优先级

若一个 property 可归入多个类别，按以下优先级：

1. 腐蚀
2. 辐照蠕变
3. 辐照肿胀
4. 硬化性能
5. 弹塑性模型
6. 热膨胀
7. 热传导率
8. 比热容
9. 密度
10. 材料规格/组织信息
11. 其他性能

例：`hydrogen pickup` 优先归入 `腐蚀`，不是成分。

例：`strain hardening exponent` 优先归入 `硬化性能`，不是普通弹塑性模型。
