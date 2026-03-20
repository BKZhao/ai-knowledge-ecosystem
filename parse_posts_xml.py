"""
SO Posts.xml 流式解析
提取核心字段，存成Parquet，完成后删XML
"""
import xml.etree.ElementTree as ET
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import os, gc
from datetime import datetime

XML_PATH = "/home/node/.openclaw/workspaces/ou_061694b4b8257fa782c21a959956256d/stackoverflow_research/data/raw/extracted/Posts.xml"
OUT_DIR  = "/home/node/.openclaw/workspaces/ou_061694b4b8257fa782c21a959956256d/stackoverflow_research/data/parquet"
os.makedirs(OUT_DIR, exist_ok=True)

# 只保留2018年之后的数据，只要这些字段
KEEP_FIELDS = ["Id","PostTypeId","CreationDate","Score","ViewCount",
               "Tags","AnswerCount","AcceptedAnswerId","OwnerUserId","Body"]

BATCH_SIZE = 200_000
batch = []
total_q = 0  # 问题数
total_a = 0  # 回答数
file_idx = 0
start_time = datetime.now()

print(f"开始解析 {XML_PATH}")
print(f"文件大小: {os.path.getsize(XML_PATH)/1024/1024/1024:.1f} GB")

writer = None
schema = None

for event, elem in ET.iterparse(XML_PATH, events=("end",)):
    if elem.tag != "row":
        continue

    date_str = elem.get("CreationDate","")[:10]
    if not date_str or date_str < "2018-01-01":
        elem.clear()
        continue

    post_type = elem.get("PostTypeId","")
    row = {
        "Id":               int(elem.get("Id",0)),
        "PostTypeId":       int(post_type) if post_type else 0,
        "CreationDate":     date_str,
        "Score":            int(elem.get("Score",0)),
        "ViewCount":        int(elem.get("ViewCount",0) or 0),
        "Tags":             elem.get("Tags",""),
        "AnswerCount":      int(elem.get("AnswerCount",0) or 0),
        "HasAccepted":      1 if elem.get("AcceptedAnswerId") else 0,
        "OwnerUserId":      int(elem.get("OwnerUserId",0) or 0),
        "BodyLength":       len(elem.get("Body","") or ""),
        "CodeBlockCount":   (elem.get("Body","") or "").count("<code>"),
    }
    batch.append(row)
    if post_type == "1": total_q += 1
    elif post_type == "2": total_a += 1
    elem.clear()

    if len(batch) >= BATCH_SIZE:
        df = pd.DataFrame(batch)
        table = pa.Table.from_pandas(df)
        if writer is None:
            schema = table.schema
            writer = pq.ParquetWriter(f"{OUT_DIR}/posts_2018plus.parquet", schema, compression='snappy')
        writer.write_table(table)
        elapsed = (datetime.now()-start_time).seconds
        print(f"  已处理 {total_q+total_a:,} 条 | 问题:{total_q:,} 回答:{total_a:,} | 耗时:{elapsed}s")
        batch = []
        gc.collect()

# 写最后一批
if batch:
    df = pd.DataFrame(batch)
    table = pa.Table.from_pandas(df)
    if writer is None:
        writer = pq.ParquetWriter(f"{OUT_DIR}/posts_2018plus.parquet", table.schema, compression='snappy')
    writer.write_table(table)

if writer:
    writer.close()

elapsed = (datetime.now()-start_time).seconds
print(f"\n✅ 解析完成！耗时 {elapsed}s")
print(f"   问题数: {total_q:,}")
print(f"   回答数: {total_a:,}")
out_size = os.path.getsize(f"{OUT_DIR}/posts_2018plus.parquet")/1024/1024/1024
print(f"   Parquet大小: {out_size:.2f} GB")

# 删除XML释放空间
print("\n正在删除原始XML（97GB）...")
os.remove(XML_PATH)
print("✅ XML已删除，空间释放！")

import subprocess
result = subprocess.run(["df","-h","/home/node"], capture_output=True, text=True)
print(result.stdout)
