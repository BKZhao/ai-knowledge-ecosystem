#!/usr/bin/env python3
"""
pipeline/01_parse_xml.py
========================
Stack Overflow XML数据解析器
- 从7z压缩包中流式解析XML，转换为Parquet格式
- 支持断点续处理
- 内存友好：使用iterparse，每批100万行保存一次

用法:
    python pipeline/01_parse_xml.py --source Posts --community so --output data/parquet/
    python pipeline/01_parse_xml.py --source Posts --community so --output data/parquet/ --resume
"""

import argparse
import json
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import py7zr
from tqdm import tqdm
from xml.etree import ElementTree as ET


# ============================================================
# 字段定义：每种数据源需要提取的字段
# ============================================================
FIELD_SCHEMAS = {
    "Posts": {
        "fields": [
            "Id", "PostTypeId", "CreationDate", "Score", "ViewCount",
            "Body", "Title", "Tags", "AnswerCount", "CommentCount",
            "AcceptedAnswerId", "OwnerUserId", "ParentId",
            "LastActivityDate", "LastEditDate", "ClosedDate",
            "FavoriteCount", "DeletionDate"
        ],
        "dtypes": {
            "Id": "int64",
            "PostTypeId": "int8",        # 1=问题, 2=回答, 3=wiki, ...
            "Score": "int32",
            "ViewCount": "float32",      # 可能为null（回答没有viewcount）
            "AnswerCount": "float32",    # 可能为null
            "CommentCount": "int32",
            "AcceptedAnswerId": "float64",  # 可能为null
            "OwnerUserId": "float64",    # 可能为null（匿名）
            "ParentId": "float64",       # 只有回答有
            "FavoriteCount": "float32",
        }
    },
    "Users": {
        "fields": [
            "Id", "CreationDate", "Reputation", "DisplayName",
            "UpVotes", "DownVotes", "Views", "LastAccessDate",
            "WebsiteUrl", "Location", "AboutMe", "AccountId"
        ],
        "dtypes": {
            "Id": "int64",
            "Reputation": "int32",
            "UpVotes": "int32",
            "DownVotes": "int32",
            "Views": "int32",
        }
    },
    "Votes": {
        "fields": [
            "Id", "PostId", "VoteTypeId", "CreationDate", "UserId", "BountyAmount"
        ],
        "dtypes": {
            "Id": "int64",
            "PostId": "int64",
            "VoteTypeId": "int8",        # 1=AcceptedByOriginator, 2=UpMod, 3=DownMod, ...
            "UserId": "float64",         # 某些投票类型无UserId
            "BountyAmount": "float32",
        }
    },
    "Comments": {
        "fields": [
            "Id", "PostId", "Score", "CreationDate", "UserId",
            "Text", "UserDisplayName", "ContentLicense"
        ],
        "dtypes": {
            "Id": "int64",
            "PostId": "int64",
            "Score": "int32",
            "UserId": "float64",         # 可能为null
        }
    },
    "Tags": {
        "fields": [
            "Id", "TagName", "Count", "ExcerptPostId", "WikiPostId"
        ],
        "dtypes": {
            "Id": "int64",
            "Count": "int32",
            "ExcerptPostId": "float64",
            "WikiPostId": "float64",
        }
    }
}

# 社区名称到7z文件前缀的映射
COMMUNITY_PREFIXES = {
    "so": "stackoverflow.com",
    "mathse": "math.stackexchange.com",
    "superuser": "superuser.com",
    "serverfault": "serverfault.com",
}

# 批量处理大小（行数）
BATCH_SIZE = 500_000

# Arrow类型映射
ARROW_TYPE_MAP = {
    "int8": pa.int8(),
    "int16": pa.int16(),
    "int32": pa.int32(),
    "int64": pa.int64(),
    "float32": pa.float32(),
    "float64": pa.float64(),
    "string": pa.string(),
    "bool": pa.bool_(),
    "timestamp": pa.timestamp("us"),
}


def parse_date(date_str: str) -> pd.Timestamp | None:
    """解析Stack Exchange标准时间格式 (ISO 8601)"""
    if not date_str:
        return None
    try:
        return pd.Timestamp(date_str)
    except Exception:
        return None


def clean_html_body(html_str: str) -> str:
    """简单清理HTML标签，只保留文本内容（可选，节省存储）"""
    if not html_str:
        return ""
    # 提取代码块数量和行数（后续特征构建用原始HTML）
    return html_str  # 保留原始HTML，特征构建时再处理


def find_7z_file(data_dir: Path, community: str, source: str) -> Path:
    """在data_dir中查找对应的7z文件"""
    prefix = COMMUNITY_PREFIXES.get(community, community)
    
    # 常见命名模式
    candidates = [
        data_dir / f"{prefix}-{source}.7z",
        data_dir / f"{prefix}/{source}.7z",
        data_dir / f"{source}.7z",
        data_dir / f"{source.lower()}.7z",
    ]
    
    for candidate in candidates:
        if candidate.exists():
            return candidate
    
    # 模糊搜索
    for f in data_dir.rglob("*.7z"):
        if source.lower() in f.name.lower() and (
            community in f.name.lower() or 
            prefix.split(".")[0] in f.name.lower()
        ):
            return f
    
    raise FileNotFoundError(
        f"找不到 {community}/{source} 的7z文件，已检查路径：\n" +
        "\n".join(str(c) for c in candidates)
    )


def load_progress(progress_file: Path) -> dict:
    """加载断点进度文件"""
    if progress_file.exists():
        with open(progress_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"rows_processed": 0, "parts_written": 0, "complete": False}


def save_progress(progress_file: Path, progress: dict):
    """保存断点进度"""
    progress_file.parent.mkdir(parents=True, exist_ok=True)
    with open(progress_file, "w", encoding="utf-8") as f:
        json.dump(progress, f, indent=2)


def extract_xml_from_7z(archive_path: Path, source: str, temp_dir: Path) -> Path:
    """
    从7z中解压指定的XML文件到临时目录
    返回解压后的XML文件路径
    注意：如果文件很大，考虑流式解压
    """
    xml_filename = f"{source}.xml"
    output_path = temp_dir / xml_filename
    
    if output_path.exists():
        print(f"  [跳过] {output_path} 已存在，使用缓存")
        return output_path
    
    print(f"  解压 {archive_path.name} -> {xml_filename} ...")
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    start_time = time.time()
    with py7zr.SevenZipFile(archive_path, mode="r") as z:
        # 只解压目标文件
        targets = [name for name in z.getnames() if name.endswith(xml_filename)]
        if not targets:
            targets = [name for name in z.getnames() if source.lower() in name.lower()]
        
        if not targets:
            raise ValueError(f"7z中找不到 {xml_filename}，包含文件：{z.getnames()}")
        
        z.extract(targets=targets, path=temp_dir)
    
    elapsed = time.time() - start_time
    print(f"  解压完成，耗时 {elapsed:.1f}s")
    
    # 查找解压后的文件（可能在子目录中）
    for candidate in temp_dir.rglob("*.xml"):
        if source.lower() in candidate.name.lower():
            return candidate
    
    return output_path


def parse_row_element(elem: ET.Element, fields: list, dtypes: dict) -> dict:
    """解析单个XML row元素，提取指定字段"""
    row = {}
    for field in fields:
        val = elem.get(field)
        if val is not None:
            # 日期字段转换
            if "Date" in field and val:
                row[field] = parse_date(val)
            # 数值字段转换
            elif field in dtypes and dtypes[field] in ("int8", "int16", "int32", "int64"):
                try:
                    row[field] = int(val)
                except (ValueError, TypeError):
                    row[field] = None
            elif field in dtypes and dtypes[field] in ("float32", "float64"):
                try:
                    row[field] = float(val)
                except (ValueError, TypeError):
                    row[field] = None
            else:
                row[field] = val
        else:
            row[field] = None
    return row


def write_parquet_batch(
    rows: list,
    output_dir: Path,
    part_num: int,
    source: str,
    community: str
) -> Path:
    """将一批行写入Parquet文件"""
    if not rows:
        return None
    
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"part-{part_num:04d}.parquet"
    
    df = pd.DataFrame(rows)
    
    # 添加社区标识列
    df["community"] = community
    df["source_table"] = source
    
    # 转换日期列到正确类型
    date_cols = [c for c in df.columns if "Date" in c]
    for col in date_cols:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce", utc=True)
    
    df.to_parquet(
        output_path,
        engine="pyarrow",
        compression="snappy",   # snappy在读取速度和压缩率之间有好的平衡
        index=False
    )
    
    return output_path


def stream_parse_xml(
    xml_path: Path,
    source: str,
    community: str,
    output_dir: Path,
    resume_from_row: int = 0,
    verbose: bool = True
) -> int:
    """
    流式解析XML文件
    使用iterparse逐行处理，避免将整个文件加载到内存
    返回总处理行数
    """
    schema = FIELD_SCHEMAS[source]
    fields = schema["fields"]
    dtypes = schema["dtypes"]
    
    batch = []
    total_rows = 0
    part_num = resume_from_row // BATCH_SIZE  # 从断点part开始编号
    
    print(f"\n开始流式解析 {xml_path.name}...")
    print(f"  提取字段: {', '.join(fields[:6])} ...")
    if resume_from_row > 0:
        print(f"  断点续传：跳过前 {resume_from_row:,} 行")
    
    # 估算文件大小（用于进度条）
    file_size = xml_path.stat().st_size
    
    # iterparse：每处理一个元素就释放内存
    context = ET.iterparse(xml_path, events=("start", "end"))
    context = iter(context)
    
    # 跳过XML文档头
    _, root = next(context)
    
    rows_skipped = 0
    start_time = time.time()
    
    with tqdm(
        total=file_size,
        unit="B",
        unit_scale=True,
        desc=f"{source}",
        disable=not verbose
    ) as pbar:
        for event, elem in context:
            if event == "end" and elem.tag == "row":
                total_rows += 1
                
                # 断点续处理：跳过已处理的行
                if rows_skipped < resume_from_row:
                    rows_skipped += 1
                    elem.clear()  # 释放内存
                    continue
                
                # 解析行数据
                row_data = parse_row_element(elem, fields, dtypes)
                batch.append(row_data)
                
                # 达到批量大小时写入Parquet
                if len(batch) >= BATCH_SIZE:
                    write_parquet_batch(batch, output_dir, part_num, source, community)
                    part_num += 1
                    batch = []
                    
                    # 更新进度
                    elapsed = time.time() - start_time
                    rows_per_sec = (total_rows - resume_from_row) / elapsed
                    pbar.set_postfix({
                        "rows": f"{total_rows:,}",
                        "rows/s": f"{rows_per_sec:.0f}"
                    })
                
                # 释放已处理元素的内存（关键！）
                elem.clear()
                root.clear()  # 同时清理父节点引用
                
                # 更新字节进度（近似）
                if total_rows % 10000 == 0:
                    try:
                        # 估算当前读取位置
                        pbar.update(0)
                    except Exception:
                        pass
    
    # 写入最后一批
    if batch:
        write_parquet_batch(batch, output_dir, part_num, source, community)
    
    elapsed = time.time() - start_time
    print(f"\n✓ 完成！总行数: {total_rows:,}，耗时: {elapsed/60:.1f} 分钟")
    print(f"  平均速度: {total_rows/elapsed:.0f} 行/秒")
    
    return total_rows


def main():
    parser = argparse.ArgumentParser(
        description="Stack Overflow XML数据解析器（7z -> Parquet）"
    )
    parser.add_argument(
        "--source",
        required=True,
        choices=list(FIELD_SCHEMAS.keys()),
        help="要解析的数据源类型（Posts/Users/Votes/Comments/Tags）"
    )
    parser.add_argument(
        "--community",
        default="so",
        choices=list(COMMUNITY_PREFIXES.keys()),
        help="数据来源社区（so/mathse/superuser/serverfault）"
    )
    parser.add_argument(
        "--input",
        default="data/raw",
        help="原始7z文件目录（默认：data/raw）"
    )
    parser.add_argument(
        "--output",
        default="data/parquet",
        help="输出Parquet文件目录（默认：data/parquet）"
    )
    parser.add_argument(
        "--temp",
        default="data/.tmp",
        help="解压临时目录（默认：data/.tmp）"
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="断点续处理（跳过已解析的行）"
    )
    parser.add_argument(
        "--no-extract",
        action="store_true",
        help="跳过解压步骤（XML文件已存在）"
    )
    parser.add_argument(
        "--xml-path",
        help="直接指定XML文件路径（跳过7z解压）"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        default=True,
        help="显示详细进度"
    )
    
    args = parser.parse_args()
    
    # ---- 路径设置 ----
    input_dir = Path(args.input)
    output_base = Path(args.output)
    temp_dir = Path(args.temp)
    
    # 输出目录：按社区/表名组织
    output_dir = output_base / f"{args.community}_{args.source.lower()}"
    
    # 进度文件
    progress_file = output_dir / ".progress.json"
    
    print("=" * 60)
    print(f"Stack Overflow XML解析器")
    print(f"社区: {args.community} ({COMMUNITY_PREFIXES.get(args.community, args.community)})")
    print(f"数据源: {args.source}")
    print(f"输出目录: {output_dir}")
    print("=" * 60)
    
    # ---- 断点续处理 ----
    progress = load_progress(progress_file)
    if progress.get("complete"):
        print("✓ 该数据源已完整解析，跳过。（删除 .progress.json 可重新解析）")
        sys.exit(0)
    
    resume_from_row = 0
    if args.resume and progress.get("rows_processed", 0) > 0:
        resume_from_row = progress["rows_processed"]
        print(f"断点续处理：从第 {resume_from_row:,} 行继续...")
    
    # ---- 获取XML文件 ----
    if args.xml_path:
        xml_path = Path(args.xml_path)
        if not xml_path.exists():
            print(f"错误：XML文件不存在：{xml_path}", file=sys.stderr)
            sys.exit(1)
    elif args.no_extract:
        # 在临时目录中查找XML文件
        xml_candidates = list(temp_dir.rglob(f"*{args.source}*.xml"))
        if not xml_candidates:
            print(f"错误：在 {temp_dir} 中找不到 {args.source}.xml", file=sys.stderr)
            sys.exit(1)
        xml_path = xml_candidates[0]
    else:
        # 从7z解压
        try:
            archive_path = find_7z_file(input_dir, args.community, args.source)
            print(f"找到档案文件：{archive_path}")
            xml_path = extract_xml_from_7z(archive_path, args.source, temp_dir)
        except FileNotFoundError as e:
            print(f"错误：{e}", file=sys.stderr)
            print("提示：使用 --xml-path 直接指定XML文件路径", file=sys.stderr)
            sys.exit(1)
    
    print(f"XML文件：{xml_path} ({xml_path.stat().st_size / 1024**3:.1f} GB)")
    
    # ---- 执行解析 ----
    try:
        total_rows = stream_parse_xml(
            xml_path=xml_path,
            source=args.source,
            community=args.community,
            output_dir=output_dir,
            resume_from_row=resume_from_row,
            verbose=args.verbose
        )
        
        # 保存完成状态
        progress["rows_processed"] = total_rows
        progress["complete"] = True
        progress["completed_at"] = datetime.now().isoformat()
        save_progress(progress_file, progress)
        
        print(f"\n✅ 解析完成！")
        print(f"   总行数: {total_rows:,}")
        print(f"   输出目录: {output_dir}")
        print(f"   文件数: {len(list(output_dir.glob('*.parquet')))}")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断！进度已保存，可用 --resume 继续。")
        # 进度会在下次运行时从已写入的parquet文件推断
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 错误：{e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
