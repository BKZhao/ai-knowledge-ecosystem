"""
SE社区补数据脚本 — 在本机运行
补充 2024-04 至 2026-02 的月度提问量
运行方法：python3 fetch_se_2024_2026.py
输出：se_supplement_2024_2026.csv
"""
import requests, time, csv
from datetime import datetime

API_KEY = "rl_yXrLKrxSPQzCqJai54e1Y3bHz"

SITES = [
    "stackoverflow", "math", "physics", "stats", "biology", "chemistry",
    "astronomy", "cogsci", "datascience", "ai",
    "english", "linguistics", "literature",
    "economics", "law", "politics", "academia",
    "history", "philosophy", "cooking", "music", "movies", "travel",
    "serverfault", "superuser"
]

# 补充时间段：2024-04 到 2026-02
months = []
for year in [2024, 2025, 2026]:
    for month in range(1, 13):
        if year == 2024 and month < 4: continue
        if year == 2026 and month > 2: break
        months.append((year, month))

print(f"目标：{len(months)}个月 × {len(SITES)}个社区 = {len(months)*len(SITES)}次请求")
print(f"时间范围：{months[0][0]}-{months[0][1]:02d} 至 {months[-1][0]}-{months[-1][1]:02d}")
print("开始拉取...\n")

results = {}
errors = 0

for year, month in months:
    from_dt = int(datetime(year, month, 1).timestamp())
    if month == 12:
        to_dt = int(datetime(year+1, 1, 1).timestamp())
    else:
        to_dt = int(datetime(year, month+1, 1).timestamp())
    
    month_key = f"{year}-{month:02d}"
    results[month_key] = {}
    
    for site in SITES:
        for attempt in range(3):
            try:
                r = requests.get(
                    "https://api.stackexchange.com/2.3/questions",
                    params={
                        "site": site,
                        "fromdate": from_dt,
                        "todate": to_dt,
                        "filter": "total",
                        "key": API_KEY
                    },
                    timeout=15
                )
                if r.status_code == 200:
                    data = r.json()
                    results[month_key][site] = data.get("total", 0)
                    quota = data.get("quota_remaining", "?")
                    break
                elif r.status_code == 429:
                    print(f"  限速，等10秒...")
                    time.sleep(10)
                else:
                    errors += 1
                    break
            except Exception as e:
                if attempt == 2:
                    errors += 1
                time.sleep(2)
        
        time.sleep(0.15)
    
    so_val = results[month_key].get("stackoverflow", "?")
    print(f"  {month_key}: SO={so_val}, quota剩余={quota}, 错误累计={errors}")

# 保存CSV
with open("se_supplement_2024_2026.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["month"] + SITES)
    for month_key in sorted(results.keys()):
        row = [month_key] + [results[month_key].get(s, "") for s in SITES]
        writer.writerow(row)

print(f"\n✅ 完成！已保存到 se_supplement_2024_2026.csv")
print(f"总月数: {len(results)}, 错误: {errors}")
