# 物相识别规则（项目对齐版）

## 0. 核心原则

`phase` 回答的问题是：

> 这个具体数据测量的对象是什么物相？

不是“材料整体的基体是什么相”。

`material_name` 回答“材料叫什么”。

`composition` 回答“材料成分是什么”。

`phase` 回答“该数值属于哪个物相或结构对象”。

---

## 1. 归属推理三步法

填写 `phase` 前必须判断：

```text
第一步：这个数据在测什么？
  基体？析出相？氧化层？氢化物？整体材料？

第二步：测量对象是否有明确物相？
  有 → 填标准 phase
  没有 → phase = null

第三步：这个 phase 是原文明示，还是同段落/表格标题可推断？
  明示 → confidence 可为 high
  同段落/表格标题推断 → 可填 phase，但必要时在 context 说明
  跨段落推断 → 不允许
```

---

## 2. phase 与 material_name / composition 的区别

| 原文 | material_name | composition | phase |
|---|---|---|---|
| `Zircaloy-4 specimen` | `Zircaloy-4` | null，除非原文给成分 | null |
| `Zr-2.5Nb pressure tube` | `Zr-2.5Nb` | `Zr-2.5Nb` | null |
| `α-Zr matrix in Zircaloy-4` | `Zircaloy-4` | null | `alpha` |
| `oxide on Zr-2.5Nb` | `Zr-2.5Nb` | `Zr-2.5Nb` | `oxide` |
| `δ-hydride in Zircaloy-2` | `Zircaloy-2` | null | `delta-hydride` |
| `Zr(Fe,Cr)2 precipitate` | 当前材料名 | 当前材料成分 | `Zr(Fe,Cr)2` |

---

## 3. 标准 phase 映射

### 3.1 基体相

| 原文形式 | 标准输出 |
|---|---|
| `α`, `alpha`, `alpha phase`, `α-Zr` | `alpha` |
| `β`, `beta`, `beta phase`, `β-Zr` | `beta` |
| `α'`, `alpha-prime`, `martensite` | `alpha-prime` |
| `α+β`, `alpha+beta`, `two-phase region` | `alpha+beta` |
| `ω`, `omega` | `omega` |

---

### 3.2 氧化物相

| 原文形式 | 标准输出 |
|---|---|
| `oxide`, `oxide layer`, `ZrO2`, `zirconium oxide` | `oxide` |
| `monoclinic oxide`, `m-ZrO2` | `monoclinic-oxide` |
| `tetragonal oxide`, `t-ZrO2` | `tetragonal-oxide` |
| `oxygen-stabilized alpha`, `α(O)` | `alpha-O` |

---

### 3.3 氢化物相

| 原文形式 | 标准输出 |
|---|---|
| `δ-hydride`, `delta hydride`, `δ-ZrH`, `ZrH1.5-1.66` | `delta-hydride` |
| `γ-hydride`, `gamma hydride`, `γ-ZrH` | `gamma-hydride` |
| `ε-hydride`, `epsilon hydride`, `ε-ZrH2` | `epsilon-hydride` |
| `hydride rim`, `hydride layer`, `hydrides` | `hydride` |

---

### 3.4 第二相 / 析出相

| 原文形式 | 标准输出 |
|---|---|
| `Zr(Fe,Cr)2`, `Laves phase` | `Zr(Fe,Cr)2` |
| `Zr2(Fe,Ni)` | `Zr2(Fe,Ni)` |
| `β-Nb`, `Nb-rich precipitate` | `beta-Nb` |
| `SPP`, `second phase particle` | `SPP` |
| `ZrCr2` | `ZrCr2` |
| `Zr4Fe`, `Zr₄Fe` | `Zr4Fe` |
| `ZrFe2` | `ZrFe2` |

---

### 3.5 新相

当论文报道不在表中的相，使用论文中的相名，清洗 LaTeX 和下标后输出。

不要把未知相强行归入 alpha、beta 或 SPP。

---

## 4. 不是 phase 的情况

| 情况 | 示例 | 处理 |
|---|---|---|
| 单独材料名 | `Zircaloy-4 specimens` | `phase = null` |
| 工艺状态 | `beta-quenched`, `cold-worked` | 写入 `conditions.processing_state` 或 `context` |
| 测试环境 | `steam`, `iodine`, `water` | 写入 `conditions.atmosphere` 或 `element` |
| 相变温度 | `α/β transition at 865°C` | `property = 相变温度`，phase 视语境填写 |
| 晶体结构类型 | `hexagonal`, `cubic` | 定性词，不作为 phase 值 |

---

## 5. 表格归属规则

1. 表格标题中的 phase 信息适用于整张表。
2. 行标题中的 phase 信息优先于表格标题。
3. 列标题中的 phase 信息只适用于该列。
4. 如果表格测的是析出相晶格参数，phase 填析出相，不填基体相。
5. 如果表格测的是材料整体性能，phase = null。

---

## 6. 常见错误

| 错误 | 正确 | 原因 |
|---|---|---|
| `Zr4Fe d-spacing` → phase=`alpha` | phase=`Zr4Fe` | 测量对象是析出相 |
| `burnup` → phase=`alpha` | phase=null | 燃耗是材料/服役级属性 |
| `beta-quenched` → phase=`beta` | phase=null 或实际相 | beta-quenched 是工艺，不是当前相 |
| `oxide thickness` → phase=null | phase=`oxide` | 测量对象是氧化层 |

---

## 7. LaTeX 清洗

| LaTeX | 输出 |
|---|---|
| `$\alpha$`, `${\alpha}$` | `alpha` |
| `$\beta$` | `beta` |
| `$\alpha'$` | `alpha-prime` |
| `${Zr}_{4}{Fe}$` | `Zr4Fe` |
| `${ZrO}_{2}$` | `oxide` 或 context 中 `ZrO2` |
| `$\delta$` 氢化物语境 | `delta-hydride` |
| `$\delta$` 非氢化物语境 | `delta` |
