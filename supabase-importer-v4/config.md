# Supabase v4 连接配置

## 项目信息

| 项目 | 值 |
|------|-----|
| Project ID | `qffltopymihbndyrwhvj` |
| Project URL | `https://qffltopymihbndyrwhvj.supabase.co` |

## API Keys

| Key 类型 | 用途 |
|---------|------|
| `service_role` | 脚本写入用（完整权限） |
| `anon` | 前端查询用（只读） |

> 当前 v4 importer 按 v3 importer 的方式保留脚本内 `SUPABASE_URL` 和 `SUPABASE_KEY` 配置。
> 如需更换项目，修改 `import_to_supabase_v4.py` 顶部的 `SUPABASE_URL` 和 `SUPABASE_KEY`。

## 表信息

| 表名 | 用途 |
|------|------|
| `nuclear_properties` | v3 历史数据表，不写入 |
| `nuclear_properties_v4` | v4 抽取数据表，当前 importer 写入目标 |

## 默认数据目录

```text
/home/zuozhuo/info-extract/info-extract-with-skills/extraction_results/project_v4
```

## 注意

- 本 skill 不负责自动建表。
- 用户已在 Supabase 网页端创建 `nuclear_properties_v4`。
- v4 导入时不要写入旧表 `nuclear_properties`。
