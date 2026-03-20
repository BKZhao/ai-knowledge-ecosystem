"""
10万条SO问题分类 - 使用DeepSeek-V3
按年份均匀抽样，覆盖2018-2024
完成后训练ML分类器对全量950万条分类
"""
import pandas as pd
import pyarrow.parquet as pq
import requests
import json
import time
import os
from collections import Counter

API_URL = "https://api.siliconflow.cn/v1/chat/completions"
API_KEY = "sk-clbbhigzzvnledglcvvirgunqdgouvzlgbndsegsmaonpgcs"
BASE = "/home/node/.openclaw/workspaces/ou_061694b4b8257fa782c21a959956256d/stackoverflow_research"
CACHE_FILE = f"{BASE}/results/classification_100k_progress.json"
OUT_FILE = f"{BASE}/results/classification_100k_results.csv"

PROMPT = """Stack Overflow问题分类（只回答数字1/2/3/4）：
1=How-to（如何做某事，有标准答案）
2=Debug（调试错误，有具体报错）
3=Conceptual（概念理解，解释/比较）
4=Architecture（架构设计，最佳实践）

标签：{tags}
正文长度：{body_len}字符
代码块：{code_blocks}个

只回答1个数字。"""

# 加载完整标注作为训练集
with open(f"{BASE}/results/annotation_llm_progress.json") as f:
    train_labels = json.load(f)
print(f"训练集: {len(train_labels)}条已标注")

# 从Parquet抽取10万条（按年份均匀抽样）
print("从Parquet读取数据...")
df = pq.read_table(
    f"{BASE}/data/parquet/posts_2018plus.parquet",
    columns=["Id","PostTypeId","CreationDate","Tags","BodyLength","CodeBlockCount"]
).to_pandas()

questions = df[df['PostTypeId'] == 1].copy()
questions['year'] = pd.to_datetime(questions['CreationDate']).dt.year
questions['Id'] = questions['Id'].astype(str)

# 排除已标注的700条
already_labeled = set(train_labels.keys())
questions = questions[~questions['Id'].isin(already_labeled)]

# 按年份均匀抽样：每年约14000条，共7年≈98000条
TARGET_PER_YEAR = 14000
sampled = []
for year in range(2018, 2025):
    year_df = questions[questions['year'] == year]
    n = min(TARGET_PER_YEAR, len(year_df))
    if n > 0:
        sampled.append(year_df.sample(n, random_state=42+year))

sample_df = pd.concat(sampled).reset_index(drop=True)
print(f"抽样: {len(sample_df):,}条")
print(f"年份分布:\n{sample_df['year'].value_counts().sort_index()}")

# 加载已有进度
progress = {}
if os.path.exists(CACHE_FILE):
    with open(CACHE_FILE) as f:
        progress = json.load(f)
    print(f"已有进度: {len(progress):,}条")

# 开始分类
errors = 0
for i, row in sample_df.iterrows():
    row_id = str(row['Id'])
    if row_id in progress:
        continue
    
    prompt = PROMPT.format(
        tags=str(row.get('Tags',''))[:150],
        body_len=int(row.get('BodyLength',0)),
        code_blocks=int(row.get('CodeBlockCount',0))
    )
    
    try:
        r = requests.post(API_URL,
            headers={"Authorization":f"Bearer {API_KEY}","Content-Type":"application/json"},
            json={"model":"deepseek-ai/DeepSeek-V3",
                  "messages":[{"role":"user","content":prompt}],
                  "max_tokens":5,"temperature":0.1},
            timeout=15)
        
        if r.status_code == 200:
            answer = r.json()['choices'][0]['message']['content'].strip()
            for c in answer:
                if c in '1234':
                    progress[row_id] = int(c)
                    break
        elif r.status_code == 429:
            time.sleep(5)
            continue
        else:
            errors += 1
            time.sleep(1)
        
        time.sleep(0.25)
        
    except Exception as e:
        errors += 1
        time.sleep(1)
    
    # 每1000条保存一次并打印进度
    if len(progress) % 1000 == 0 and len(progress) > 0:
        with open(CACHE_FILE, "w") as f: json.dump(progress, f)
        c = Counter(progress.values())
        pct = len(progress)/len(sample_df)*100
        print(f"[{len(progress):,}/{len(sample_df):,}] {pct:.1f}% | How-to:{c[1]} Debug:{c[2]} Conceptual:{c[3]} Arch:{c[4]} | 错误:{errors}")

# 最终保存
with open(CACHE_FILE, "w") as f: json.dump(progress, f)
print(f"\n✅ 分类完成！{len(progress):,}条")

# 合并结果
sample_df['question_type'] = sample_df['Id'].map(progress)
sample_df['type_label'] = sample_df['question_type'].map(
    {1:'How-to',2:'Debug',3:'Conceptual',4:'Architecture'})
sample_df.to_csv(OUT_FILE, index=False)
print(f"✅ 结果已保存: {OUT_FILE}")

# 统计各年份分布
print("\n各年份问题类型分布:")
print(pd.crosstab(sample_df['year'], sample_df['type_label'], normalize='index').round(3)*100)
