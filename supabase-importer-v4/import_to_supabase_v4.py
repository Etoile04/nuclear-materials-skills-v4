#!/usr/bin/env python3
"""
核材料性能数据 v4 → Supabase 同步脚本

基于 v3 importer 做最小改动：
- 目标表改为 nuclear_properties_v4
- 适配 v4 JSON 字段：source_file、material_name、property_category、property_note
- 保留 v4 记录内部的 source_file，不再用 JSON 文件名覆盖 md 源文件路径
- 保留原有功能：批量导入、dry-run、force 覆盖、跳过已存在、排除 combined 文件

用法：
  python3 import_to_supabase_v4.py
  python3 import_to_supabase_v4.py -d /path/to/project_v4
  python3 import_to_supabase_v4.py -d /path/to/project_v4 --dry-run
  python3 import_to_supabase_v4.py -d /path/to/project_v4 -p "*.json"
  python3 import_to_supabase_v4.py -d /path/to/project_v4 --force
"""

import argparse
import json
import sys
from pathlib import Path

from supabase import create_client

# ── 配置 ────────────────────────────────────────────────
SUPABASE_URL = "https://qffltopymihbndyrwhvj.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFmZmx0b3B5bWloYm5keXJ3aHZqIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MjMyMzE3OSwiZXhwIjoyMDg3ODk5MTc5fQ.2fZpSG6qJVZUzfB3Z1uQVY_trgFy_NUNlM1Gf_ygouo"
DEFAULT_DIR = Path("/home/zuozhuo/info-extract/info-extract-with-skills/extraction_results/project_v4")
TABLE      = "nuclear_properties_v4"
BATCH_SIZE = 500
# ────────────────────────────────────────────────────────


# 为了保持 v3 版本“开箱即用”的使用方式，这里仍保留脚本内 SUPABASE_KEY。
# 如果你希望沿用 v3 脚本中硬编码的 key，请把原 import_to_supabase.py 顶部的 SUPABASE_KEY 复制到上面。
# 不建议把 service_role key 提交到公开仓库。


def parse_args():
    parser = argparse.ArgumentParser(description="核材料 v4 JSON → Supabase 同步工具")
    parser.add_argument(
        "--data-dir", "-d",
        type=Path,
        default=DEFAULT_DIR,
        help=f"JSON 文件所在目录（默认：{DEFAULT_DIR}）",
    )
    parser.add_argument(
        "--pattern", "-p",
        default="*.json",
        help="文件匹配模式（默认：*.json，匹配目录下所有 JSON）",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="只扫描文件并统计条数，不写入数据库",
    )
    parser.add_argument(
        "--force", "-f",
        action="store_true",
        help="强制覆盖：即使该 md 源文件已有数据也重新导入（默认跳过已存在的 source_file）",
    )
    return parser.parse_args()


def transform(record: dict, fallback_source_file: str) -> dict:
    """
    v4 字段映射。

    注意：v4 抽取结果中的 source_file 是原始 md 路径，必须优先保留；
    fallback_source_file 只用于旧数据或异常数据缺少 source_file 的情况。
    """
    return {
        "source_file":       record.get("source_file") or fallback_source_file,
        "material_name":     record.get("material_name"),
        "composition":       record.get("composition"),
        "phase":             record.get("phase"),
        "element":           record.get("element"),
        "property_category": record.get("property_category"),
        "property":          record.get("property"),
        "value":             record.get("value"),
        "unit":              record.get("unit"),
        "conditions":        record.get("conditions") or None,
        "context":           record.get("context"),
        "confidence":        record.get("confidence"),
        "reference":         record.get("reference"),
        "property_note":     record.get("property_note"),
    }


def count_existing_for_sources(supabase, source_files: list[str]) -> int:
    """统计这些 source_file 在目标表中已有多少条记录。"""
    total = 0
    for source_file in source_files:
        result = supabase.table(TABLE).select("id", count="exact").eq("source_file", source_file).execute()
        total += result.count or 0
    return total


def delete_existing_for_sources(supabase, source_files: list[str]):
    """删除这些 source_file 对应的旧记录。"""
    for source_file in source_files:
        supabase.table(TABLE).delete().eq("source_file", source_file).execute()


def sync_file(supabase, filepath: Path, fallback_source_file: str, dry_run: bool, force: bool) -> tuple:
    """
    同步单个 JSON 文件。
    - 默认：该 JSON 中任一 source_file 已存在则跳过
    - --force：删除该 JSON 中所有 source_file 的旧记录再插入
    返回 (成功数, 失败数, 状态描述)
    """
    with open(filepath, "r", encoding="utf-8") as f:
        try:
            records = json.load(f)
        except json.JSONDecodeError as e:
            return 0, 0, f"JSON 解析失败: {e}"

    if not isinstance(records, list):
        return 0, 0, "JSON 顶层不是数组，跳过"

    if not records:
        if not dry_run:
            try:
                supabase.table(TABLE).delete().eq("source_file", fallback_source_file).execute()
            except Exception as e:
                return 0, 0, f"清除旧记录失败: {e}"
        return 0, 0, "空文件（已尝试清除 fallback source_file 旧记录）"

    rows = [transform(r, fallback_source_file) for r in records]
    source_files = sorted({row["source_file"] for row in rows if row.get("source_file")})

    if dry_run:
        return len(rows), 0, f"dry-run，共 {len(rows)} 条，source_file={len(source_files)} 个，跳过写入"

    # ★ 检查数据库中是否已存在该 md 源文件的数据
    existing_count = count_existing_for_sources(supabase, source_files)
    if existing_count > 0 and not force:
        return 0, 0, f"已存在 {existing_count} 条，跳过（用 --force 强制覆盖）"

    # 强制覆盖时：先删除旧记录
    if force:
        try:
            delete_existing_for_sources(supabase, source_files)
        except Exception as e:
            return 0, len(rows), f"删除旧记录失败，已中止插入: {e}"

    # 分批插入新记录
    success, failed = 0, 0
    for i in range(0, len(rows), BATCH_SIZE):
        batch = rows[i:i + BATCH_SIZE]
        try:
            supabase.table(TABLE).insert(batch).execute()
            success += len(batch)
        except Exception as e:
            print(f"    ❌ 批次 {i // BATCH_SIZE + 1} 失败: {e}")
            failed += len(batch)

    return success, failed, "导入完成"


def main():
    args = parse_args()
    data_dir = args.data_dir.resolve()

    if not data_dir.exists():
        print(f"❌ 目录不存在: {data_dir}")
        sys.exit(1)

    # 扫描文件，排除 combined 聚合文件防止重复
    files = sorted(data_dir.glob(args.pattern))
    files = [f for f in files if "combined" not in f.name and f.is_file()]

    print("=" * 60)
    print("Nuclear Properties v4 → Supabase 同步（跳过已存在 / --force 强制覆盖）")
    print("=" * 60)
    print(f"📁 数据目录: {data_dir}")
    print(f"🔍 文件模式: {args.pattern}")
    print(f"🗄️  目标表: {TABLE}")
    if args.dry_run:
        print("⚠️  DRY-RUN 模式，不写入数据库")
    if args.force:
        print("⚡ FORCE 模式，已存在的 source_file 将强制覆盖")
    print("=" * 60)

    if not files:
        print(f"❌ 未在目录中找到匹配 '{args.pattern}' 的文件")
        sys.exit(1)

    print(f"找到 {len(files)} 个文件，开始同步...\n")

    if not args.dry_run:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        print(f"✅ 已连接: {SUPABASE_URL}\n")
    else:
        supabase = None

    total_success, total_failed = 0, 0

    for filepath in files:
        # fallback 仅在记录缺少 source_file 时使用。
        # v4 正常情况下会保留记录内部的 md 源路径。
        fallback_source_file = f"{data_dir.name}/{filepath.name}"

        success, failed, status = sync_file(supabase, filepath, fallback_source_file, args.dry_run, args.force)
        total_success += success
        total_failed += failed
        icon = "✅" if failed == 0 else "⚠️"
        print(f"  {icon} {filepath.name}: {success} 条  [{status}]")

    print("\n" + "=" * 60)
    print(f"同步完成！成功 {total_success} 条 / 失败 {total_failed} 条")

    if not args.dry_run and supabase:
        result = supabase.table(TABLE).select("id", count="exact").execute()
        print(f"📊 {TABLE} 当前总行数: {result.count}")

    print("=" * 60)


if __name__ == "__main__":
    main()
