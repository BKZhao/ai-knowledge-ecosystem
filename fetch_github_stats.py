"""
GitHub API 数据拉取
按语言×周统计知识生产活动
使用 Search API 按时间范围统计
"""
import requests
import time
import json
import os
from datetime import datetime, timedelta

GH_TOKENS = [
    "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",
    "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",
    "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",
    "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",
    "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",
]
_token_idx = 0

def get_headers():
    global _token_idx
    token = GH_TOKENS[_token_idx % len(GH_TOKENS)]
    _token_idx += 1
    return {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }

OUT_DIR = "/home/node/.openclaw/workspaces/ou_061694b4b8257fa782c21a959956256d/stackoverflow_research/results"
CACHE_FILE = f"{OUT_DIR}/github_cache_weekly.json"
os.makedirs(OUT_DIR, exist_ok=True)

# 核心编程语言（与SO对齐）
LANGUAGES = [
    "Python", "JavaScript", "TypeScript", "Java",
    "C#", "Go", "Rust", "C++", "C",
    "Ruby", "Assembly", "Haskell", "Ruby", "R"
]

def search_count(query, retries=3):
    """用Search API获取计数"""
    url = "https://api.github.com/search/repositories"
    # 实际用commits搜索
    for attempt in range(retries):
        try:
            r = requests.get(
                "https://api.github.com/search/commits",
                headers={**get_headers(), "Accept": "application/vnd.github.cloak-preview+json"},
                params={"q": query, "per_page": 1},
                timeout=10
            )
            if r.status_code == 200:
                return r.json().get("total_count", 0)
            elif r.status_code == 422:
                return 0
            elif r.status_code == 403:
                reset = int(r.headers.get("X-RateLimit-Reset", time.time()+60))
                wait = max(reset - time.time(), 0) + 5
                print(f"  Rate limit, 等待 {wait:.0f}s")
                time.sleep(wait)
            else:
                time.sleep(2)
        except Exception as e:
            print(f"  错误: {e}")
            time.sleep(3)
    return None

def get_repo_count(lang, from_date, to_date):
    """获取指定语言在时间段内新创建的仓库数"""
    query = f"language:{lang} created:{from_date}..{to_date}"
    url = "https://api.github.com/search/repositories"
    try:
        r = requests.get(url, headers=get_headers(),
                        params={"q": query, "per_page": 1}, timeout=10)
        if r.status_code == 200:
            remaining = int(r.headers.get("X-RateLimit-Remaining", 100))
            if remaining < 20:
                reset = int(r.headers.get("X-RateLimit-Reset", time.time()+60))
                wait = max(reset - time.time(), 0) + 2
                print(f"  配额低({remaining})，等待 {wait:.0f}s")
                time.sleep(wait)
            return r.json().get("total_count", 0)
        elif r.status_code == 403:
            reset = int(r.headers.get("X-RateLimit-Reset", time.time()+60))
            wait = max(reset - time.time(), 0) + 5
            print(f"  Rate limit, 等待 {wait:.0f}s")
            time.sleep(wait)
            return get_repo_count(lang, from_date, to_date)
        else:
            return 0
    except Exception as e:
        print(f"  错误: {e}")
        return 0

def get_issue_pr_count(lang, from_date, to_date, item_type="issue"):
    """获取Issue或PR数量"""
    query = f"language:{lang} created:{from_date}..{to_date} is:{item_type}"
    url = "https://api.github.com/search/issues"
    try:
        r = requests.get(url, headers=get_headers(),
                        params={"q": query, "per_page": 1}, timeout=10)
        if r.status_code == 200:
            remaining = int(r.headers.get("X-RateLimit-Remaining", 100))
            if remaining < 20:
                reset = int(r.headers.get("X-RateLimit-Reset", time.time()+60))
                wait = max(reset - time.time(), 0) + 2
                time.sleep(wait)
            return r.json().get("total_count", 0)
        elif r.status_code == 403:
            reset = int(r.headers.get("X-RateLimit-Reset", time.time()+60))
            wait = max(reset - time.time(), 0) + 5
            time.sleep(wait)
            return get_issue_pr_count(lang, from_date, to_date, item_type)
        return 0
    except:
        return 0

# 生成月度列表（用月度代替周度，节省API配额，2018-2026）
months = []
start = datetime(2018, 1, 1)
end = datetime(2026, 3, 1)
current = start
while current < end:
    if current.month == 12:
        next_month = datetime(current.year + 1, 1, 1)
    else:
        next_month = datetime(current.year, current.month + 1, 1)
    months.append((current, min(next_month - timedelta(days=1), end)))
    current = next_month

print(f"共 {len(months)} 个月需要查询")
print(f"语言数: {len(LANGUAGES)}")
print(f"预计API请求: {len(months) * len(LANGUAGES) * 2} 次")
print(f"预计耗时: {len(months) * len(LANGUAGES) * 2 / 30:.0f} 分钟\n")

# 加载缓存
cache = {}
if os.path.exists(CACHE_FILE):
    with open(CACHE_FILE) as f:
        cache = json.load(f)
    print(f"已加载缓存: {len(cache)} 条")

results = []
total = len(months)

for i, (month_start, month_end) in enumerate(months):
    month_key = month_start.strftime("%Y-%m")
    from_date = month_start.strftime("%Y-%m-%d")
    to_date = month_end.strftime("%Y-%m-%d")

    if month_key in cache:
        results.append(cache[month_key])
        if i % 12 == 0:
            print(f"[{i+1}/{total}] {month_key} (缓存)")
        continue

    print(f"[{i+1}/{total}] 查询 {month_key}...")
    row = {"month": month_key, "month_dt": from_date}

    for lang in LANGUAGES:
        lang_key = lang.lower().replace("#","sharp").replace("+","p")
        # 新仓库数（知识生产）
        repos = get_repo_count(lang, from_date, to_date)
        row[f"repos_{lang_key}"] = repos
        time.sleep(0.8)

        # Issue数（对比SO消费行为）
        issues = get_issue_pr_count(lang, from_date, to_date, "issue")
        row[f"issues_{lang_key}"] = issues
        time.sleep(0.8)

    results.append(row)
    cache[month_key] = row

    # 每月保存缓存
    with open(CACHE_FILE, "w") as f:
        json.dump(cache, f)

    # 打印进度
    python_repos = row.get("repos_python", 0)
    python_issues = row.get("issues_python", 0)
    print(f"  Python新仓库: {python_repos}, Issues: {python_issues}")

print(f"\n完成！共 {len(results)} 月数据")

import pandas as pd
df = pd.DataFrame(results)
df.to_csv(f"{OUT_DIR}/github_monthly_stats.csv", index=False)
print(f"已保存: {OUT_DIR}/github_monthly_stats.csv")
print(df.head())
