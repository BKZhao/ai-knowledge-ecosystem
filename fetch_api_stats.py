"""
用 Stack Overflow API 拉取2018-2026年每周统计数据
速度比解析XML快100倍
"""
import requests
import time
import json
import pandas as pd
from datetime import datetime, timedelta
import os

API_KEY = "rl_4L6CL2TNw1KLXeYnWRu3SQRt3"
OUT_DIR = "/home/node/.openclaw/workspaces/ou_061694b4b8257fa782c21a959956256d/stackoverflow_research/results"
os.makedirs(OUT_DIR, exist_ok=True)

CACHE_FILE = f"{OUT_DIR}/api_cache_weekly.json"

# 编程语言标签
LANGUAGES = ["python","javascript","java","c%23","php","typescript",
             "c%2B%2B","c","ruby","go","rust","r","swift","kotlin",
             "assembly","cobol","fortran","haskell"]

def get_weekly_stats(fromdate, todate, tag=None, retries=3):
    """获取指定时间段的问题统计"""
    params = {
        "site": "stackoverflow",
        "fromdate": int(fromdate.timestamp()),
        "todate": int(todate.timestamp()),
        "filter": "total",
        "key": API_KEY,
    }
    if tag:
        url = f"https://api.stackexchange.com/2.3/questions"
        params["tagged"] = tag
    else:
        url = f"https://api.stackexchange.com/2.3/questions"
    
    for attempt in range(retries):
        try:
            r = requests.get(url, params=params, timeout=10)
            data = r.json()
            if "backoff" in data:
                print(f"  API backoff: {data['backoff']}s")
                time.sleep(data["backoff"] + 1)
                continue
            if "quota_remaining" in data and data["quota_remaining"] < 10:
                print(f"  ⚠️  配额剩余: {data['quota_remaining']}")
            return data.get("total", 0)
        except Exception as e:
            print(f"  错误: {e}, 重试 {attempt+1}")
            time.sleep(2)
    return None

# 生成周列表：2018-01-01 到 2026-03-01
weeks = []
start = datetime(2018, 1, 1)
end = datetime(2026, 3, 1)
current = start
while current < end:
    next_week = current + timedelta(weeks=1)
    weeks.append((current, min(next_week, end)))
    current = next_week

print(f"共 {len(weeks)} 周需要查询")

# 加载缓存
cache = {}
if os.path.exists(CACHE_FILE):
    with open(CACHE_FILE) as f:
        cache = json.load(f)
    print(f"已加载缓存: {len(cache)} 条")

results = []
total_weeks = len(weeks)

for i, (week_start, week_end) in enumerate(weeks):
    week_key = week_start.strftime("%Y-W%V")
    
    if week_key in cache:
        results.append(cache[week_key])
        if i % 50 == 0:
            print(f"[{i+1}/{total_weeks}] {week_key} (缓存)")
        continue
    
    if i % 10 == 0:
        print(f"[{i+1}/{total_weeks}] 正在查询 {week_key}...")
    
    row = {"week": week_key, "week_dt": week_start.strftime("%Y-%m-%d")}
    
    # 总提问量
    total = get_weekly_stats(week_start, week_end)
    row["total_questions"] = total
    time.sleep(0.15)
    
    # 各语言提问量（选10个关键语言，节省配额）
    key_langs = ["python", "javascript", "java", "c%23", "typescript", 
                 "c%2B%2B", "c", "go", "rust", "assembly"]
    for lang in key_langs:
        count = get_weekly_stats(week_start, week_end, tag=lang)
        lang_name = lang.replace("%23","sharp").replace("%2B%2B","pp")
        row[f"lang_{lang_name}"] = count
        time.sleep(0.12)
    
    results.append(row)
    cache[week_key] = row
    
    # 每10周保存一次缓存
    if i % 10 == 0:
        with open(CACHE_FILE, "w") as f:
            json.dump(cache, f)

# 最终保存
with open(CACHE_FILE, "w") as f:
    json.dump(cache, f)

df = pd.DataFrame(results)
df.to_csv(f"{OUT_DIR}/weekly_api_stats.csv", index=False)
print(f"\n完成！共 {len(df)} 周数据")
print(df.head())
print(df.tail())
print(f"\n总提问量统计:")
print(df["total_questions"].describe())
