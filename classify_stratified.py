"""
分层抽样LLM分类 - 续跑版
策略：按语言×年份分层均匀抽样，每层抽固定数量
目标：在已有112k基础上，用分层方式补充高质量样本

分层设计：
- 14语言 × 7年（2018-2024） = 98个层
- 每层抽 ~1,500条 = 约147,000条目标
- 已有样本已覆盖部分，优先补充覆盖不足的层
"""
import pandas as pd
import pyarrow.parquet as pq
import requests
import json
import time
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import Counter, defaultdict

API_URL = "https://api.siliconflow.cn/v1/chat/completions"
API_KEY = "sk-clbbhigzzvnledglcvvirgunqdgouvzlgbndsegsmaonpgcs"
BASE = "/home/node/.openclaw/workspaces/ou_061694b4b8257fa782c21a959956256d/stackoverflow_research"
CACHE_FILE = f"{BASE}/results/classification_stratified_progress.json"
LOG_FILE   = f"{BASE}/results/classify_stratified_log.txt"

TARGET_PER_STRATUM = 1000  # 每个语言×年份层抽1000条
THREADS = 8

LANG_TAGS = {
    'python':     ['python'],
    'javascript': ['javascript'],
    'typescript': ['typescript'],
    'java':       ['java'],
    'csharp':     ['c#'],
    'php':        ['php'],
    'cpp':        ['c++'],
    'swift':      ['swift'],
    'kotlin':     ['kotlin'],
    'go':         ['go'],
    'rust':       ['rust'],
    'r':          ['r'],
    'scala':      ['scala'],
    'haskell':    ['haskell'],
}

PROMPT = """Classify this Stack Overflow question into ONE category (reply with digit only):
1=How-to (how to do something, step-by-step)
2=Debug (fixing errors, bugs, exceptions)
3=Conceptual (explain/compare/understand concepts)
4=Architecture (design decisions, best practices)

Tags: {tags}
Body length: {body_len} chars
Code blocks: {code_blocks}

Reply with ONLY 1, 2, 3, or 4."""

def classify_one(row):
    prompt = PROMPT.format(
        tags=row.get('Tags',''),
        body_len=row.get('BodyLength',0),
        code_blocks=row.get('CodeBlockCount',0)
    )
    for attempt in range(3):
        try:
            resp = requests.post(API_URL, json={
                "model": "deepseek-ai/DeepSeek-V3",
                "messages": [{"role":"user","content":prompt}],
                "max_tokens": 5, "temperature": 0
            }, headers={"Authorization":f"Bearer {API_KEY}"}, timeout=15)
            text = resp.json()['choices'][0]['message']['content'].strip()
            digit = ''.join(c for c in text if c.isdigit())
            if digit and digit[0] in '1234':
                return int(digit[0])
        except Exception as e:
            if 'insufficient' in str(e).lower():
                print("⚠️ 余额不足，停止")
                return None
            time.sleep(1*(attempt+1))
    return None

def log(msg):
    ts = time.strftime('%H:%M:%S')
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG_FILE,'a') as f: f.write(line+'\n')

# 加载已完成ID
log("加载已完成ID...")
done_ids = set()
for fname in ['classification_100k_progress.json',
              'classification_200k_extra_progress.json',
              'classification_stratified_progress.json']:
    fpath = f"{BASE}/results/{fname}"
    if os.path.exists(fpath):
        with open(fpath) as f:
            d = json.load(f)
        done_ids.update(d.keys())
        log(f"  {fname}: {len(d)}条")

# 加载新进度
if os.path.exists(CACHE_FILE):
    with open(CACHE_FILE) as f:
        new_results = json.load(f)
else:
    new_results = {}

log(f"总已完成: {len(done_ids)}条，本轮已有: {len(new_results)}条")

# 读取parquet
log("读取parquet数据...")
df = pq.read_table(
    f"{BASE}/data/parquet/posts_2018plus.parquet",
    columns=['Id','PostTypeId','CreationDate','Tags','BodyLength','CodeBlockCount']
).to_pandas()
df['Id'] = df['Id'].astype(str)
questions = df[df['PostTypeId']==1].copy()
questions['year'] = pd.to_datetime(questions['CreationDate']).dt.year
questions = questions[~questions['Id'].isin(done_ids)]
log(f"可用未分类问题: {len(questions):,}条")

# 分层抽样
log("分层抽样...")
sampled_list = []
strata_stats = {}

for lang, tags in LANG_TAGS.items():
    # 筛选含该语言tag的问题
    mask = questions['Tags'].str.contains('|'.join(tags), case=False, na=False)
    lang_df = questions[mask]

    for year in range(2018, 2025):
        year_df = lang_df[lang_df['year']==year]
        n = min(TARGET_PER_STRATUM, len(year_df))
        if n > 0:
            sample = year_df.sample(n, random_state=hash(f"{lang}_{year}")%10000)
            sampled_list.append(sample)
            strata_stats[f"{lang}_{year}"] = n

sample_df = pd.concat(sampled_list, ignore_index=True).drop_duplicates('Id')
# 去掉已在本轮缓存中的
sample_df = sample_df[~sample_df['Id'].isin(new_results.keys())]
sample_df = sample_df.sample(frac=1, random_state=42).reset_index(drop=True)

log(f"分层抽样目标: {len(sample_df):,}条")
log(f"层数: {len(strata_stats)}")

# 打印各层分布
lang_counts = Counter()
for k,v in strata_stats.items():
    lang_counts[k.split('_')[0]] += v
log("各语言抽样量:")
for lang, cnt in sorted(lang_counts.items(), key=lambda x:-x[1]):
    log(f"  {lang:12s}: {cnt}")

rows = sample_df.to_dict('records')
total = len(rows)
start = time.time()
error_count = 0
SAVE_EVERY = 200

log(f"\n开始分类，目标{total:,}条，{THREADS}线程")

for i in range(0, total, 50):
    batch = rows[i:i+50]
    with ThreadPoolExecutor(max_workers=THREADS) as ex:
        futures = {ex.submit(classify_one, row): row for row in batch}
        for fut in as_completed(futures):
            row = futures[fut]
            label = fut.result()
            if label:
                new_results[str(row['Id'])] = label
            else:
                error_count += 1

    processed = min(i+50, total)
    if processed % SAVE_EVERY == 0 or processed >= total:
        with open(CACHE_FILE, 'w') as f:
            json.dump(new_results, f)
        elapsed = time.time()-start
        rate = len(new_results)/(elapsed/3600) if elapsed > 0 else 0
        remaining_h = (total-processed)/max(rate,1)
        log(f"[{processed:,}/{total:,}] 已分类{len(new_results):,} | {rate:.0f}条/h | 剩余~{remaining_h:.1f}h | 错误:{error_count}")

# 最终保存
with open(CACHE_FILE,'w') as f:
    json.dump(new_results, f)

dist = Counter(new_results.values())
lm = {1:'How-to',2:'Debug',3:'Conceptual',4:'Architecture'}
log(f"\n✅ 分层抽样分类完成！共{len(new_results):,}条，错误{error_count}条")
for k in sorted(dist):
    log(f"  {lm[k]}: {dist[k]} ({dist[k]/len(new_results)*100:.1f}%)")
