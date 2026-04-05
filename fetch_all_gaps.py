"""
数据补全脚本 v2 — 不依赖pandas，纯原生Python
1. GitHub: 补R语言 + 2026-03
2. SE对照社区: 扩展到30个 + 补全NaN + 补到2026-03
3. control_data.json周度补全
"""
import requests, time, json, csv, os
from datetime import datetime, timedelta

OUT = "/home/node/.openclaw/workspaces/ou_061694b4b8257fa782c21a959956256d/stackoverflow_research/results"
SE_KEY = "rl_yXrLKrxSPQzCqJai54e1Y3bHz"

# === GitHub helpers ===
GH_TOKENS = [
    "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",
    "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",
    "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",
    "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",
    "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",
]
_tidx = 0

def gh_headers():
    global _tidx
    t = GH_TOKENS[_tidx % len(GH_TOKENS)]; _tidx += 1
    return {"Authorization": f"token {t}", "Accept": "application/vnd.github.v3+json"}

def gh_count(lang, fd, td, kind="repos"):
    for _ in range(3):
        try:
            if kind == "repos":
                url = "https://api.github.com/search/repositories"
                q = f"language:{lang} created:{fd}..{td}"
            else:
                url = "https://api.github.com/search/issues"
                q = f"language:{lang} created:{fd}..{td} is:issue"
            r = requests.get(url, headers=gh_headers(), params={"q": q, "per_page": 1}, timeout=10)
            if r.status_code == 200:
                rem = int(r.headers.get("X-RateLimit-Remaining", 100))
                if rem < 5:
                    wt = max(int(r.headers.get("X-RateLimit-Reset", time.time()+60)) - time.time(), 0) + 2
                    print(f"      GH配额低({rem}), 等待{wt:.0f}s"); time.sleep(wt)
                return r.json().get("total_count", 0)
            elif r.status_code == 403:
                wt = max(int(r.headers.get("X-RateLimit-Reset", time.time()+60)) - time.time(), 0) + 5
                print(f"      Rate limit, 等{wt:.0f}s"); time.sleep(wt); continue
            time.sleep(2)
        except Exception as e:
            print(f"      错误: {e}"); time.sleep(3)
    return None

# === SE helper ===
def se_count(site, from_ts, to_ts):
    for _ in range(3):
        try:
            r = requests.get("https://api.stackexchange.com/2.3/questions",
                params={"site": site, "fromdate": from_ts, "todate": to_ts,
                        "filter": "total", "key": SE_KEY}, timeout=15)
            if r.status_code == 200:
                d = r.json()
                if "backoff" in d: time.sleep(d["backoff"] + 1); continue
                return d.get("total", 0)
            elif r.status_code == 429: print("    SE限速,等10s"); time.sleep(10)
            else: time.sleep(2)
        except Exception as e: print(f"    SE错误: {e}"); time.sleep(2)
    return None

def month_range(y, m):
    """返回 (from_date_str, to_date_str)"""
    fd = f"{y:04d}-{m:02d}-01"
    if m == 12:
        td = f"{y+1:04d}-01-01"
    else:
        td = f"{y:04d}-{m+1:02d}-01"
    return fd, td

flush = lambda: [time.sleep(0), None][1]

# ============================================================
print("=" * 60)
print("PART 1: GitHub数据补全 (R语言 + 2026-03)")
print("=" * 60)

gh_path = f"{OUT}/github_cache_weekly.json"
with open(gh_path) as f:
    gh = json.load(f)
print(f"已有: {len(gh)} 个月")

# 补R语言
print("\n补R语言...")
r_fixed = 0
for mk in sorted(gh.keys()):
    row = gh[mk]
    if row.get("repos_r") is not None and row.get("repos_r") != "":
        continue
    fd = row.get("month_dt", mk + "-01")
    y, m = int(fd[:4]), int(fd[5:7])
    fd2, td2 = month_range(y, m)
    repos = gh_count("R", fd2, td2, "repos")
    time.sleep(1)
    issues = gh_count("R", fd2, td2, "issues")
    row["repos_r"] = repos
    row["issues_r"] = issues
    r_fixed += 1
    print(f"  {mk}: repos={repos}, issues={issues}")
print(f"R语言补全: {r_fixed}个月")

# 补2026-03
if "2026-03" not in gh:
    print("\n补2026-03...")
    row = {"month": "2026-03", "month_dt": "2026-03-01"}
    for lang in ["Python","JavaScript","TypeScript","Java","C#","Go","Rust","C++","C","Ruby","Assembly","Haskell","R"]:
        lk = lang.lower().replace("#","sharp").replace("+","p")
        repos = gh_count(lang, "2026-03-01", "2026-03-31", "repos")
        time.sleep(1)
        issues = gh_count(lang, "2026-03-01", "2026-03-31", "issues")
        row[f"repos_{lk}"] = repos
        row[f"issues_{lk}"] = issues
        print(f"  {lang}: repos={repos}, issues={issues}")
    gh["2026-03"] = row
else:
    print("\n2026-03已存在")

with open(gh_path, "w") as f:
    json.dump(gh, f)
print(f"\nGitHub保存: {len(gh)}个月")

# 导出CSV
langs_cols = sorted([k for k in list(gh.values())[0].keys() if k.startswith("repos_") or k.startswith("issues_")])
all_cols = ["month", "month_dt"] + langs_cols
with open(f"{OUT}/github_monthly_stats.csv", "w") as f:
    w = csv.writer(f)
    w.writerow(all_cols)
    for mk in sorted(gh.keys()):
        w.writerow([gh[mk].get(c, "") for c in all_cols])
print(f"GitHub CSV导出完成")

# ============================================================
print("\n" + "=" * 60)
print("PART 2: SE对照社区扩展 (30个社区)")
print("=" * 60)

SITES = {
    "stackoverflow": "SO", "serverfault": "ServerFault", "superuser": "SuperUser",
    "unix": "Unix", "wordpress": "WordPress", "android": "Android",
    "math": "Math", "physics": "Physics", "chemistry": "Chemistry",
    "biology": "Biology", "astronomy": "Astronomy",
    "stats": "Stats", "datascience": "DataScience", "ai": "AI",
    "philosophy": "Philosophy", "history": "History", "politics": "Politics",
    "law": "Law", "economics": "Economics", "linguistics": "Linguistics",
    "psychology": "Psychology", "cogsci": "CogSci", "sociology": "Sociology",
    "english": "English", "literature": "Literature", "music": "Music",
    "movies": "Movies", "travel": "Travel", "cooking": "Cooking",
    "academia": "Academia", "scicomp": "SciComp",
}

# 生成月份列表
all_months = []
for y in range(2018, 2027):
    for m in range(1, 13):
        if y == 2026 and m > 3: break
        all_months.append(f"{y}-{m:02d}")

# 加载已有数据
panel_path = f"{OUT}/se_panel_complete_2018_2026.csv"
existing = {}  # {month: {col: val}}
if os.path.exists(panel_path):
    with open(panel_path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            mk = row.get("month", "")
            existing[mk] = row

print(f"已有面板: {len(existing)} 个月")
print(f"目标: {len(all_months)} 个月 × {len(SITES)} 社区")

# 确定需要拉取的组合
to_fetch = []
for mk in all_months:
    for site_key, label in SITES.items():
        col = f"{label}_questions"
        if mk in existing:
            val = existing[mk].get(col, "")
            if val != "" and val is not None:
                try:
                    float(val)  # 有效数字
                    continue
                except:
                    pass
        to_fetch.append((mk, site_key, label))

print(f"需拉取: {len(to_fetch)} 组合 ({len(to_fetch)*0.25/60:.1f}分钟)")
print("开始...\n")

errs = 0
for i, (mk, site_key, label) in enumerate(to_fetch):
    y, m = int(mk[:4]), int(mk[5:7])
    from_ts = int(datetime(y, m, 1).timestamp())
    if m == 12:
        to_ts = int(datetime(y+1, 1, 1).timestamp())
    else:
        to_ts = int(datetime(y, m+1, 1).timestamp())
    
    count = se_count(site_key, from_ts, to_ts)
    col = f"{label}_questions"
    
    if mk not in existing:
        existing[mk] = {"month": mk}
    existing[mk][col] = count if count is not None else ""
    
    if count is None: errs += 1
    if (i+1) % 100 == 0 or i == len(to_fetch) - 1:
        print(f"  [{i+1}/{len(to_fetch)}] {mk} {label}={count} 错误:{errs}")

# 保存面板
col_order = ["month"] + [f"{v}_questions" for v in SITES.values()]
with open(panel_path, "w") as f:
    w = csv.DictWriter(f, fieldnames=col_order, extrasaction="ignore")
    w.writeheader()
    for mk in all_months:
        if mk in existing:
            w.writerow(existing[mk])

print(f"\n✅ 面板保存: {len(all_months)} 个月 × {len(SITES)} 社区, 错误: {errs}")

# ============================================================
print("\n" + "=" * 60)
print("PART 3: 补全control_data.json (Math/Physics周度)")
print("=" * 60)

ctrl_path = f"{OUT}/control_data.json"
with open(ctrl_path) as f:
    ctrl = json.load(f)

# 生成所有ISO周
all_wks = set()
cur = datetime(2018, 1, 1)
while cur < datetime(2026, 4, 1):
    all_wks.add(cur.strftime("%Y-W%V"))
    cur += timedelta(weeks=1)

missing = sorted(all_wks - set(ctrl.keys()))
print(f"已有: {len(ctrl)} 周, 缺失: {len(missing)}")

if missing:
    for wk in missing:
        y, wn = int(wk.split("-W")[0]), int(wk.split("-W")[1])
        jan4 = datetime(y, 1, 4)
        ws = jan4 - timedelta(days=jan4.weekday() + 1 - wn * 7)
        we = ws + timedelta(days=6, hours=23, minutes=59, seconds=59)
        math_c = se_count("math", int(ws.timestamp()), int(we.timestamp()))
        phys_c = se_count("physics", int(ws.timestamp()), int(we.timestamp()))
        ctrl[wk] = {"week": wk, "week_dt": ws.strftime("%Y-%m-%d"),
                     "math_se_questions": math_c, "physics_se_questions": phys_c}
        print(f"  {wk}: Math={math_c}, Physics={phys_c}")
        time.sleep(0.3)
    with open(ctrl_path, "w") as f:
        json.dump(ctrl, f)
    print(f"control_data.json: {len(ctrl)} 周")
else:
    print("已完整!")

print("\n" + "=" * 60)
print("🎉 全部补全完成!")
print("=" * 60)
