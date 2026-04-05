# -*- coding: utf-8 -*-
import requests, time, json, csv, os
from datetime import datetime, timedelta

OUT = "/home/node/.openclaw/workspaces/ou_061694b4b8257fa782c21a959956256d/stackoverflow_research/results"
SE_KEY = "rl_yXrLKrxSPQzCqJai54e1Y3bHz"

def se_count(site, from_ts, to_ts):
    for _ in range(3):
        try:
            r = requests.get("https://api.stackexchange.com/2.3/questions",
                params={"site": site, "fromdate": from_ts, "todate": to_ts,
                        "filter": "total", "key": SE_KEY}, timeout=15)
            if r.status_code == 200:
                d = r.json()
                if "backoff" in d:
                    time.sleep(d["backoff"] + 1)
                    continue
                return d.get("total", 0)
            elif r.status_code == 429:
                print("    SE限速,等10s", flush=True)
                time.sleep(10)
            else:
                time.sleep(2)
        except Exception as e:
            print("    SE错误: " + str(e), flush=True)
            time.sleep(2)
    return None

SITES = [
    ("stackoverflow", "SO"), ("serverfault", "ServerFault"), ("superuser", "SuperUser"),
    ("unix", "Unix"), ("wordpress", "WordPress"), ("android", "Android"),
    ("math", "Math"), ("physics", "Physics"), ("chemistry", "Chemistry"),
    ("biology", "Biology"), ("astronomy", "Astronomy"),
    ("stats", "Stats"), ("datascience", "DataScience"), ("ai", "AI"),
    ("philosophy", "Philosophy"), ("history", "History"), ("politics", "Politics"),
    ("law", "Law"), ("economics", "Economics"), ("linguistics", "Linguistics"),
    ("psychology", "Psychology"), ("cogsci", "CogSci"), ("sociology", "Sociology"),
    ("english", "English"), ("literature", "Literature"), ("music", "Music"),
    ("movies", "Movies"), ("travel", "Travel"), ("cooking", "Cooking"),
    ("academia", "Academia"), ("scicomp", "SciComp"),
]

all_months = []
for y in range(2018, 2027):
    for m in range(1, 13):
        if y == 2026 and m > 3:
            break
        all_months.append("%04d-%02d" % (y, m))

panel_path = os.path.join(OUT, "se_panel_complete_2018_2026.csv")
existing = {}
fieldnames = []
if os.path.exists(panel_path):
    with open(panel_path) as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames) if reader.fieldnames else []
        for row in reader:
            mk = row.get("month", "")
            existing[mk] = dict(row)

print("已有面板: %d 个月, 列: %d" % (len(existing), len(fieldnames)), flush=True)

to_fetch = []
for mk in all_months:
    for site_key, label in SITES:
        col = label + "_questions"
        if mk in existing:
            val = existing[mk].get(col, "")
            if val != "" and val is not None:
                try:
                    float(val)
                    continue
                except:
                    pass
        to_fetch.append((mk, site_key, label))

print("需拉取: %d 组合, 预计: %.1f分钟" % (len(to_fetch), len(to_fetch)*0.3/60), flush=True)
print("开始拉取...", flush=True)

errs = 0
done = 0
for i, (mk, site_key, label) in enumerate(to_fetch):
    y, m = int(mk[:4]), int(mk[5:7])
    from_ts = int(datetime(y, m, 1).timestamp())
    if m == 12:
        to_ts = int(datetime(y+1, 1, 1).timestamp())
    else:
        to_ts = int(datetime(y, m+1, 1).timestamp())
    
    count = se_count(site_key, from_ts, to_ts)
    col = label + "_questions"
    
    if mk not in existing:
        existing[mk] = {"month": mk}
    existing[mk][col] = str(count) if count is not None else ""
    
    if count is None:
        errs += 1
    done += 1
    
    if done % 200 == 0 or done == len(to_fetch):
        print("  [%d/%d] %s %s=%s 错误:%d" % (done, len(to_fetch), mk, label, count, errs), flush=True)

col_order = ["month"] + [v + "_questions" for _, v in SITES]
for c in fieldnames:
    if c != "month" and c not in col_order:
        col_order.append(c)

with open(panel_path, "w") as f:
    w = csv.DictWriter(f, fieldnames=col_order, extrasaction="ignore")
    w.writeheader()
    for mk in all_months:
        if mk in existing:
            w.writerow(existing[mk])

print("面板保存: %d 个月 x %d 社区, 错误: %d" % (len(all_months), len(SITES), errs), flush=True)

# Part 2: control_data.json
print("\n补全control_data.json...", flush=True)
ctrl_path = os.path.join(OUT, "control_data.json")
with open(ctrl_path) as f:
    ctrl = json.load(f)

all_wks = set()
cur = datetime(2018, 1, 1)
while cur < datetime(2026, 4, 1):
    all_wks.add(cur.strftime("%Y-W%V"))
    cur += timedelta(weeks=1)

missing = sorted(all_wks - set(ctrl.keys()))
print("已有: %d 周, 缺失: %d" % (len(ctrl), len(missing)), flush=True)

if missing:
    for wk in missing:
        parts = wk.split("-W")
        y, wn = int(parts[0]), int(parts[1])
        jan4 = datetime(y, 1, 4)
        ws = jan4 - timedelta(days=jan4.weekday() + 1 - wn * 7)
        we = ws + timedelta(days=6, hours=23, minutes=59, seconds=59)
        math_c = se_count("math", int(ws.timestamp()), int(we.timestamp()))
        phys_c = se_count("physics", int(ws.timestamp()), int(we.timestamp()))
        ctrl[wk] = {"week": wk, "week_dt": ws.strftime("%Y-%m-%d"),
                     "math_se_questions": math_c, "physics_se_questions": phys_c}
        print("  %s: Math=%s, Physics=%s" % (wk, math_c, phys_c), flush=True)
        time.sleep(0.3)
    with open(ctrl_path, "w") as f:
        json.dump(ctrl, f)
    print("control_data.json: %d 周" % len(ctrl), flush=True)
else:
    print("已完整!", flush=True)

print("\n全部完成!", flush=True)
