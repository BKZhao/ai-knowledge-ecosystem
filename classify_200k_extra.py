"""
额外20万条SO问题分类 - 使用DeepSeek-V3
在已有98k基础上，再抽20万条（按年份均匀）
"""
import pandas as pd
import pyarrow.parquet as pq
import requests
import json
import time
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import Counter

API_URL = "https://api.siliconflow.cn/v1/chat/completions"
API_KEY = "sk-clbbhigzzvnledglcvvirgunqdgouvzlgbndsegsmaonpgcs"
BASE = "/home/node/.openclaw/workspaces/ou_061694b4b8257fa782c21a959956256d/stackoverflow_research"
CACHE_FILE_OLD = f"{BASE}/results/classification_100k_progress.json"
CACHE_FILE_NEW = f"{BASE}/results/classification_200k_extra_progress.json"
LOG_FILE = f"{BASE}/results/classify_200k_log.txt"

TARGET_TOTAL = 200000
TARGET_PER_YEAR = TARGET_TOTAL // 7  # ~28571 per year

PROMPT = """Stack Overflow问题分类（只回答数字1/2/3/4）：
1=How-to（如何做某事，有标准答案）
2=Debug（调试错误，有具体报错）
3=Conceptual（概念理解，解释/比较）
4=Architecture（架构设计，最佳实践）

标签：{tags}
正文长度：{body_len}字符
代码块：{code_blocks}个

只回答1个数字。"""

def classify_one(row):
    prompt = PROMPT.format(
        tags=row.get('Tags', ''),
        body_len=row.get('BodyLength', 0),
        code_blocks=row.get('CodeBlockCount', 0)
    )
    for attempt in range(3):
        try:
            resp = requests.post(API_URL, json={
                "model": "deepseek-ai/DeepSeek-V3",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 5,
                "temperature": 0
            }, headers={"Authorization": f"Bearer {API_KEY}"}, timeout=15)
            text = resp.json()['choices'][0]['message']['content'].strip()
            digit = ''.join(c for c in text if c.isdigit())
            if digit and digit[0] in '1234':
                return int(digit[0])
        except Exception:
            time.sleep(1 * (attempt + 1))
    return None

def log(msg):
    print(msg)
    with open(LOG_FILE, 'a') as f:
        f.write(msg + '\n')

# 加载已完成的ID
print("加载已完成ID...")
with open(CACHE_FILE_OLD) as f:
    old_done = json.load(f)
done_ids = set(old_done.keys())
print(f"已有: {len(done_ids)}条")

# 加载新进度（断点续传）
if os.path.exists(CACHE_FILE_NEW):
    with open(CACHE_FILE_NEW) as f:
        new_results = json.load(f)
    done_ids.update(new_results.keys())
    print(f"本轮已完成: {len(new_results)}条")
else:
    new_results = {}

# 抽样
print("从Parquet读取数据并抽样...")
df = pq.read_table(
    f"{BASE}/data/parquet/posts_2018plus.parquet",
    columns=["Id","PostTypeId","CreationDate","Tags","BodyLength","CodeBlockCount"]
).to_pandas()

questions = df[df['PostTypeId'] == 1].copy()
questions['year'] = pd.to_datetime(questions['CreationDate']).dt.year
questions['Id'] = questions['Id'].astype(str)
questions = questions[~questions['Id'].isin(done_ids)]

sampled = []
for year in range(2018, 2025):
    year_df = questions[questions['year'] == year]
    n = min(TARGET_PER_YEAR, len(year_df))
    if n > 0:
        sampled.append(year_df.sample(n, random_state=100 + year))

sample_df = pd.concat(sampled).sample(frac=1, random_state=999).reset_index(drop=True)
print(f"本轮目标: {len(sample_df)}条")
print("年份分布:")
print(sample_df['year'].value_counts().sort_index().to_string())

# 去掉已在new_results里的
sample_df = sample_df[~sample_df['Id'].isin(new_results.keys())]
print(f"待分类: {len(sample_df)}条")

rows = sample_df.to_dict('records')
total = len(rows)
start_time = time.time()
error_count = 0
THREADS = 8
SAVE_EVERY = 500

log(f"开始分类，目标{total}条，{THREADS}线程")

def process_batch(batch):
    results = {}
    for row in batch:
        label = classify_one(row)
        if label:
            results[str(row['Id'])] = label
    return results

processed = 0
batch_size = 50

for i in range(0, total, batch_size):
    batch = rows[i:i+batch_size]
    with ThreadPoolExecutor(max_workers=THREADS) as ex:
        futures = {ex.submit(classify_one, row): row for row in batch}
        for fut in as_completed(futures):
            row = futures[fut]
            label = fut.result()
            if label:
                new_results[str(row['Id'])] = label
            else:
                error_count += 1

    processed = min(i + batch_size, total)

    if processed % SAVE_EVERY == 0 or processed >= total:
        with open(CACHE_FILE_NEW, 'w') as f:
            json.dump(new_results, f)
        elapsed = time.time() - start_time
        rate = len(new_results) / (elapsed / 3600)
        remaining = (total - processed) / max(rate, 1)
        log(f"[{processed}/{total}] 已分类{len(new_results)} | {rate:.0f}条/h | 剩余~{remaining:.1f}h | 错误:{error_count}")

# 最终保存
with open(CACHE_FILE_NEW, 'w') as f:
    json.dump(new_results, f)

log(f"\n✅ 完成！共{len(new_results)}条，错误{error_count}条")
dist = Counter(new_results.values())
for k in sorted(dist):
    labels = {1:'How-to', 2:'Debug', 3:'Conceptual', 4:'Arch'}
    log(f"  {labels[k]}: {dist[k]} ({dist[k]/len(new_results)*100:.1f}%)")
