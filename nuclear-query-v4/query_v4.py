#!/usr/bin/env python3
"""
核材料性能数据查询脚本（v4）
用法: python3 query_v4.py --property 屈服强度 --composition Zircaloy-4 --phase alpha
说明: 适配 nuclear_properties_v4 表；优先按 material_name 查询材料，支持 property_category。
"""

import argparse
import json
import sys
import urllib.request
import urllib.parse

# ── 连接配置 ────────────────────────────────────────────────────────────────
SUPABASE_URL = "https://qffltopymihbndyrwhvj.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFmZmx0b3B5bWloYm5keXJ3aHZqIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzIzMjMxNzksImV4cCI6MjA4Nzg5OTE3OX0.ja_YPw3qTr94RbYb9vAldSpExliSwg2uvolDlFamBiM"
TABLE = "nuclear_properties_v4"

# ── 性能类别 → property 关键词映射 ──────────────────────────────────────────
CATEGORY_MAP = {
    "热学":   ["密度", "比热容", "热导率", "热扩散率", "热阻", "absolute entropy", "挤压最高温度", "脆-韧转变温度", "Gibbs free energy change", "淬火温度", "aged temperature"],
    "热学性能": ["密度", "比热容", "热导率", "热扩散率", "热阻", "absolute entropy", "挤压最高温度", "脆-韧转变温度", "Gibbs free energy change", "淬火温度", "aged temperature"],
    "弹性":   ["杨氏模量", "剪切模量", "泊松比", "弹性张量"],
    "弹性性能": ["杨氏模量", "剪切模量", "泊松比", "弹性张量"],
    "强度":   ["屈服强度", "抗拉强度", "硬化模量", "硬化指数", "延伸率", "断裂应变", "流动应力", "临界裂纹长度", "最大载荷与塑性极限载荷之比", "最大应力强度因子", "J-R曲线斜率", "维氏硬度", "均匀延伸率", "最终环向抗拉强度", "总环向延伸率", "爆破强度", "爆破延伸率", "周向延伸率", "操作应力", "辐照伸长应变速率", "yield strength", "tensile strength", "uniform elongation", "断面收缩率", "爆破强度", "屈服强度增量", "应力释放温度"],
    "力学":   ["屈服强度", "抗拉强度", "硬化模量", "硬化指数", "延伸率", "断裂应变", "流动应力", "临界裂纹长度", "最大载荷与塑性极限载荷之比", "最大应力强度因子", "J-R曲线斜率", "维氏硬度", "均匀延伸率", "最终环向抗拉强度", "总环向延伸率", "爆破强度", "爆破延伸率", "周向延伸率", "操作应力", "辐照伸长应变速率", "yield strength", "tensile strength", "uniform elongation", "断面收缩率", "爆破强度", "屈服强度增量", "应力释放温度"],
    "力学性能": ["屈服强度", "抗拉强度", "硬化模量", "硬化指数", "延伸率", "断裂应变", "流动应力", "临界裂纹长度", "最大载荷与塑性极限载荷之比", "最大应力强度因子", "J-R曲线斜率", "维氏硬度", "均匀延伸率", "最终环向抗拉强度", "总环向延伸率", "爆破强度", "爆破延伸率", "周向延伸率", "操作应力", "辐照伸长应变速率", "yield strength", "tensile strength", "uniform elongation", "断面收缩率", "爆破强度", "屈服强度增量", "应力释放温度"],
    "蠕变":   ["蠕变应变", "瞬态蠕变速率", "稳态蠕变速率", "应力指数", "应变速率敏感性", "平均线膨胀系数", "瞬时线膨胀系数"],
    "蠕变性能": ["蠕变应变", "瞬态蠕变速率", "稳态蠕变速率", "应力指数", "应变速率敏感性", "平均线膨胀系数", "瞬时线膨胀系数"],
    "辐照":   ["体积膨胀率", "空洞肿胀率", "尺寸变化率", "中子注量", "辐照剂量", "燃耗", "快中子通量", "裂变气体释放率", "气泡肿胀率", "气泡密度", "平均空洞尺寸", "峰值中子注量", "管道辐照量", "有效满功率天数"],
    "辐照性能": ["体积膨胀率", "空洞肿胀率", "尺寸变化率", "中子注量", "辐照剂量", "燃耗", "快中子通量", "裂变气体释放率", "气泡肿胀率", "气泡密度", "平均空洞尺寸", "峰值中子注量", "管道辐照量", "有效满功率天数"],
    "腐蚀":   ["均匀腐蚀速率", "应力腐蚀阈值", "氧化膜厚度", "氧化膜开裂应变", "裂纹扩展速率", "点蚀深度密度分布", "腐蚀疲劳裂纹扩展速率", "腐蚀增重", "后转变腐蚀速率", "腐蚀转变时间", "腐蚀转变时增重", "14-day weight gain", "α/β淬火腐蚀速率比", "14-day weight gain (volume fraction effect)", "氧化层厚度", "氧化膜增重", "氧化物体积", "氧化膜重量增益", "腐蚀增重最小值对应冷却速率"],
    "腐蚀性能": ["均匀腐蚀速率", "应力腐蚀阈值", "氧化膜厚度", "氧化膜开裂应变", "裂纹扩展速率", "点蚀深度密度分布", "腐蚀疲劳裂纹扩展速率", "腐蚀增重", "后转变腐蚀速率", "腐蚀转变时间", "腐蚀转变时增重", "14-day weight gain", "α/β淬火腐蚀速率比", "14-day weight gain (volume fraction effect)", "氧化层厚度", "氧化膜增重", "氧化物体积", "氧化膜重量增益", "腐蚀增重最小值对应冷却速率"],
    "氢":     ["氢含量", "吸氢率", "氘含量", "氢化物连续性系数", "理论氢pickup百分比", "延迟氢致裂纹扩展速率", "等效氢吸收速率", "径向取向氢化物比例", "等效氢含量", "氘吸收速率"],
    "氢含量":  ["氢含量", "吸氢率", "氘含量", "氢化物连续性系数", "理论氢pickup百分比", "延迟氢致裂纹扩展速率", "等效氢吸收速率", "径向取向氢化物比例", "等效氢含量", "氘吸收速率"],
    "扩散":   ["氢含量", "吸氢率", "氧含量", "扩散系数", "活化能"],
    "晶体":   ["晶格参数a", "晶格参数c", "晶面间距", "晶粒尺寸", "位错密度", "织构系数", "第二相分布", "织构系数fr", "第二相粒子体积分数", "相分数", "c/a晶格常数比", "孪晶旋转角", "织构参数fr(轧态)"],
    "微观":   ["晶格参数a", "晶格参数c", "晶面间距", "晶粒尺寸", "位错密度", "织构系数", "第二相分布", "织构系数fr", "第二相粒子体积分数", "相分数", "c/a晶格常数比", "孪晶旋转角", "织构参数fr(轧态)"],
    "组织":   ["晶格参数a", "晶格参数c", "晶面间距", "晶粒尺寸", "位错密度", "织构系数", "第二相分布", "织构系数fr", "第二相粒子体积分数", "相分数", "c/a晶格常数比", "孪晶旋转角", "织构参数fr(轧态)"],
    "失效":   ["爆破温度", "爆破压力", "失效应力", "失效时间", "外压", "相变温度"],
    "爆破":   ["爆破温度", "爆破压力", "失效应力", "失效时间", "外压", "相变温度"],
    "成分":   ["铁含量", "锡含量", "铬含量", "铝含量", "铜含量", "碳含量", "氧含量", "formation enthalpy", "Al含量", "Cr含量", "Cu含量", "C含量", "O含量", "氮含量", "铌含量", "镍含量", "合金元素含量范围", "Sn含量", "硅含量", "锡含量范围", "hydrogen content", "Nb content", "Sn content", "Fe content", "O content", "N content", "C content", "H content", "Fe含量", "Ni含量", "Hf含量", "H含量", "N含量", "Si含量"],
    "元素":   ["铁含量", "锡含量", "铬含量", "铝含量", "铜含量", "碳含量", "氧含量", "formation enthalpy", "Al含量", "Cr含量", "Cu含量", "C含量", "O含量", "氮含量", "铌含量", "镍含量", "合金元素含量范围", "Sn含量", "硅含量", "锡含量范围", "hydrogen content", "Nb content", "Sn content", "Fe content", "O content", "N content", "C content", "H content", "Fe含量", "Ni含量", "Hf含量", "H含量", "N含量", "Si含量"],
    "尺寸":   ["DHC初始条纹间距", "第二相粒子几何平均直径", "第二相粒子平均间距", "样品尺寸", "析出相尺寸", "样品厚度", "孔隙尺寸", "样品壁厚", "样品外径", "压力管长度", "样品内径", "燃料元件长度", "DHC条纹间距", "铸锭直径", "吸附层厚度"],
    "几何":   ["DHC初始条纹间距", "第二相粒子几何平均直径", "第二相粒子平均间距", "样品尺寸", "析出相尺寸", "样品厚度", "孔隙尺寸", "样品壁厚", "样品外径", "压力管长度", "样品内径", "燃料元件长度", "DHC条纹间距", "铸锭直径", "吸附层厚度"],
    "工艺":   ["冷加工比例", "冷加工量"],
    "处理":   ["冷加工比例", "冷加工量"],
    "时间":   ["DHC孕育时间", "aging time", "stress-relief time"],
    "寿命":   ["DHC孕育时间", "aging time", "stress-relief time"],
    "表面":   ["表面粗糙因子", "孔隙表面积"],
}

# v4 新增：项目任务书性能大类 → property_category
# 这些关键词直接查询 property_category；其余关键词仍按旧逻辑展开到 property。
PROPERTY_CATEGORY_ALIASES = {
    "密度": "密度",
    "比热容": "比热容",
    "热传导率": "热传导率",
    "热导率": "热传导率",
    "弹塑性": "弹塑性模型",
    "弹塑性模型": "弹塑性模型",
    "力学": "弹塑性模型",
    "力学性能": "弹塑性模型",
    "强度": "弹塑性模型",
    "热膨胀": "热膨胀",
    "辐照蠕变": "辐照蠕变",
    "蠕变": "辐照蠕变",
    "辐照肿胀": "辐照肿胀",
    "肿胀": "辐照肿胀",
    "腐蚀": "腐蚀",
    "腐蚀性能": "腐蚀",
    "硬化": "硬化性能",
    "硬化性能": "硬化性能",
    "材料规格": "材料规格/组织信息",
    "组织": "材料规格/组织信息",
    "微观": "材料规格/组织信息",
    "材料规格/组织信息": "材料规格/组织信息",
    "其他性能": "其他性能",
}


def supabase_request(params: dict, limit: int) -> list:
    """通过 Supabase REST API 查询数据"""
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
    }

    query_parts = []
    for k, v in params.items():
        query_parts.append(f"{k}=ilike.{urllib.parse.quote('*' + v + '*')}")

    query_string = "&".join(query_parts)
    url = f"{SUPABASE_URL}/rest/v1/{TABLE}?{query_string}&limit={limit}&order=material_name.asc,property_category.asc,property.asc"

    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode())


def fetch_by_properties(property_keywords: list, extra_params: dict, limit: int) -> list:
    """对多个 property 关键词分别查询，合并结果（去重）"""
    all_rows = []
    seen_ids = set()
    for kw in property_keywords:
        params = {"property": kw, **extra_params}
        rows = supabase_request(params, limit)
        for row in rows:
            rid = row.get("id")
            if rid not in seen_ids:
                seen_ids.add(rid)
                all_rows.append(row)
    return all_rows


def fetch_by_categories(categories: list, extra_params: dict, limit: int) -> list:
    """对多个 v4 property_category 分别查询，合并结果（去重）"""
    all_rows = []
    seen_ids = set()
    for cat in categories:
        params = {"property_category": cat, **extra_params}
        rows = supabase_request(params, limit)
        for row in rows:
            rid = row.get("id")
            if rid not in seen_ids:
                seen_ids.add(rid)
                all_rows.append(row)
    return all_rows


def fmt_conditions(cond) -> str:
    """将 conditions JSONB 转为简短字符串"""
    if not cond:
        return "—"
    if isinstance(cond, str):
        try:
            cond = json.loads(cond)
        except Exception:
            return str(cond)
    parts = []
    priority = ["condition_type", "temp_C", "temp_K", "temperature", "温度", "pressure_MPa", "pressure", "压力", "fluence_n/m2", "fluence", "burnup_GWd/t", "burnup", "dpa", "simulation_method"]
    for key in priority:
        if key in cond:
            parts.append(f"{key}={cond[key]}")
    for key, val in cond.items():
        if key not in priority:
            parts.append(f"{key}={val}")
    return "; ".join(parts[:3]) if parts else "—"


def print_table(rows: list):
    """以 Markdown 表格格式输出"""
    if not rows:
        print("\n❌ 未找到匹配数据，请尝试更宽泛的关键词。\n")
        return

    print(f"\n✅ 共找到 **{len(rows)}** 条记录\n")
    print("| 物相 | 材料 | 性能类别 | 性能 | 数值 | 单位 | 条件 | 置信度 | 来源文件 |")
    print("|------|------|----------|------|------|------|------|--------|----------|")
    for r in rows:
        phase       = r.get("phase") or "—"
        composition = r.get("material_name") or r.get("composition") or "—"
        category    = r.get("property_category") or "—"
        property_   = r.get("property") or "—"
        value       = r.get("value") or "—"
        unit        = r.get("unit") or "—"
        conditions  = fmt_conditions(r.get("conditions"))
        confidence  = r.get("confidence") or "—"
        source      = r.get("source_file") or "—"
        print(f"| {phase} | {composition} | {category} | {property_} | {value} | {unit} | {conditions} | {confidence} | {source} |")
    print()


def print_statistics(rows: list):
    """输出查询结果的统计信息"""
    if not rows or len(rows) < 2:
        return  # 数据太少时不显示统计信息
    
    print("\n📊 统计摘要")
    print("=" * 70)
    
    # 按性能分组统计
    property_groups = {}
    for r in rows:
        prop = r.get("property")
        if not prop:
            continue
        if prop not in property_groups:
            property_groups[prop] = []
        property_groups[prop].append(r)
    
    print(f"📈 共找到 {len(property_groups)} 种不同性能")
    
    # 对每种性能进行数值统计
    for prop, records in property_groups.items():
        if len(records) < 2:
            continue  # 至少需要2条记录才有统计意义
        
        numeric_values = []
        units = set()
        
        for r in records:
            value_str = r.get("value")
            unit = r.get("unit") or "—"
            if unit != "—":
                units.add(unit)
            
            # 尝试解析数值
            if value_str:
                try:
                    # 移除可能的分隔符
                    clean_val = str(value_str).replace(',', '').strip()
                    # 尝试解析为浮点数
                    val = float(clean_val)
                    numeric_values.append((val, unit))
                except (ValueError, TypeError):
                    pass
        
        if numeric_values:
            values = [v[0] for v in numeric_values]
            avg = sum(values) / len(values)
            min_val = min(values)
            max_val = max(values)
            
            # 单位统计
            if len(units) == 1:
                unit_str = next(iter(units))
            elif len(units) > 1:
                unit_str = f"混合单位 ({', '.join(sorted(units))})"
            else:
                unit_str = "无单位"
            
            print(f"\n📋 **{prop}** ({len(numeric_values)} 个数值)")
            print(f"   📐 范围: {min_val:.4g} - {max_val:.4g} {unit_str}")
            print(f"   📊 平均值: {avg:.4g} {unit_str}")
            
            # 如果数据点足够多，显示更多统计信息
            if len(values) >= 5:
                sorted_vals = sorted(values)
                median = sorted_vals[len(sorted_vals) // 2]
                print(f"   📈 中位数: {median:.4g} {unit_str}")
                
                # 简单标准差
                variance = sum((x - avg) ** 2 for x in values) / len(values)
                std_dev = variance ** 0.5
                print(f"   📉 标准差: ±{std_dev:.4g} {unit_str}")
    
    # 材料分布统计
    material_counts = {}
    phase_counts = {}
    
    for r in rows:
        material = r.get("material_name") or r.get("composition") or "未知"
        phase = r.get("phase") or "未知"
        
        material_counts[material] = material_counts.get(material, 0) + 1
        phase_counts[phase] = phase_counts.get(phase, 0) + 1
    
    if material_counts:
        print("\n🏗️  **材料分布**")
        for material, count in sorted(material_counts.items(), key=lambda x: x[1], reverse=True)[:5]:
            percentage = (count / len(rows)) * 100
            print(f"   - {material}: {count} 条 ({percentage:.1f}%)")
    
    if phase_counts and len(phase_counts) > 1:  # 不止"未知"
        print("\n🔬 **物相分布**")
        for phase, count in sorted(phase_counts.items(), key=lambda x: x[1], reverse=True):
            if phase != "未知" and phase != "—":
                percentage = (count / len(rows)) * 100
                print(f"   - {phase}: {count} 条 ({percentage:.1f}%)")


def main():
    parser = argparse.ArgumentParser(description="核材料性能数据查询")
    parser.add_argument("--property",     "-p", help="性能名或类别关键词（支持逗号分隔多个；v4 类别优先匹配 property_category）")
    parser.add_argument("--composition",  "-c", help="材料名（模糊匹配 v4 material_name，如 Zircaloy-4；参数名为兼容 v3 保留）")
    parser.add_argument("--phase",        "-ph", help="物相（如 alpha / beta）")
    parser.add_argument("--element",      "-e", help="元素（如 hydrogen）")
    parser.add_argument("--limit",        "-l", type=int, default=50, help="返回条数上限，默认 50")
    args = parser.parse_args()

    if not any([args.property, args.composition, args.phase, args.element]):
        parser.print_help()
        sys.exit(1)

    # 构造非 property 的过滤参数
    extra_params = {}
    if args.composition:
        # v4 使用 material_name 表示材料名；参数名 --composition 为兼容旧用法保留。
        extra_params["material_name"] = args.composition
    if args.phase:
        extra_params["phase"] = args.phase
    if args.element:
        extra_params["element"] = args.element

    # 处理 property 参数
    if args.property:
        keywords_input = [k.strip() for k in args.property.split(",") if k.strip()]
        property_keywords = []
        property_categories = []

        for kw in keywords_input:
            if kw in PROPERTY_CATEGORY_ALIASES:
                cat = PROPERTY_CATEGORY_ALIASES[kw]
                property_categories.append(cat)
                print(f"📂 v4 类别「{kw}」→ property_category = {cat}")
            elif kw in CATEGORY_MAP:
                property_keywords.extend(CATEGORY_MAP[kw])
                print(f"📂 类别「{kw}」展开为 property：{', '.join(CATEGORY_MAP[kw])}")
            else:
                property_keywords.append(kw)

        rows = []
        seen_ids = set()
        for group in (fetch_by_categories(property_categories, extra_params, args.limit),
                      fetch_by_properties(property_keywords, extra_params, args.limit)):
            for row in group:
                rid = row.get("id")
                if rid not in seen_ids:
                    seen_ids.add(rid)
                    rows.append(row)
    else:
        # 无 property 参数，只按其他维度查询
        rows = supabase_request(extra_params, args.limit)

    print_table(rows)
    print_statistics(rows)


if __name__ == "__main__":
    main()
