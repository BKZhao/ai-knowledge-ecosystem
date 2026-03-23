import requests
import pandas as pd
import time
from datetime import datetime, timedelta
from pathlib import Path
import sys

API_KEY = "rl_yXrLKrxSPQzCqJai54e1Y3bHz"
LANGUAGES = ['python', 'javascript', 'typescript', 'java', 'c#', 'php', 'c++',
             'swift', 'kotlin', 'go', 'rust', 'scala', 'haskell', 'r']

BASE = '/home/node/.openclaw/workspaces/ou_061694b4b8257fa782c21a959956256d/stackoverflow_research'
Path(f"{BASE}/data/fetched_2024plus").mkdir(parents=True, exist_ok=True)

def fetch_page(tag, from_ts, to_ts, page=1):
    resp = requests.get("https://api.stackexchange.com/2.3/questions", params={
        'order':'asc','sort':'creation','tagged':tag,
        'fromdate':from_ts,'todate':to_ts,
        'page':page,'pagesize':100,'site':'stackoverflow',
        'key':API_KEY,'filter':'!9_bDDxJY5'
    }, timeout=30)
    return resp.json() if resp.status_code == 200 else None

months = pd.date_range('2024-04-01', '2026-02-28', freq='MS')
all_q, stats = [], []

for lang in LANGUAGES:
    for month in months:
        from_ts = int(month.timestamp())
        to_ts   = int(((month + timedelta(days=32)).replace(day=1) - timedelta(days=1)).timestamp())
        items, page, has_more = [], 1, True
        while has_more and page <= 10:
            data = fetch_page(lang, from_ts, to_ts, page)
            if data and 'items' in data:
                items.extend(data['items']); has_more = data.get('has_more', False); page += 1
                time.sleep(0.05)
            else:
                has_more = False
        n = len(items)
        if n > 0:
            stats.append({'month': month.strftime('%Y-%m-%d'), 'language': lang, 'n_questions': n,
                'avg_score': round(sum(q.get('score',0) for q in items)/n, 2),
                'avg_views': round(sum(q.get('view_count',0) for q in items)/n, 1),
                'pct_answered': round(sum(1 for q in items if q.get('is_answered'))/n*100, 1)})
            for q in items[:50]:
                all_q.append({'id':q['question_id'],'month':month.strftime('%Y-%m'),'language':lang,
                    'title':q.get('title',''),'body':q.get('body','')[:500],
                    'tags':';'.join(q.get('tags',[])),'score':q.get('score',0),
                    'view_count':q.get('view_count',0),'answer_count':q.get('answer_count',0),
                    'is_answered':q.get('is_answered',False)})

pd.DataFrame(stats).to_csv(f"{BASE}/data/fetched_2024plus/monthly_stats.csv", index=False)
pd.DataFrame(all_q).to_csv(f"{BASE}/data/fetched_2024plus/questions_sample.csv", index=False)

# 发邮件通知
sys.path.insert(0, BASE)
from notify import send_update
send_update(
    'SO 2024-2025数据抓取完成',
    f'炳坤，2024-04至2025-12的SO数据已抓取完成。\n共{len(stats)}条月度统计，{len(all_q)}条问题样本。\n下一步：LLM分类 + 更新质量指标图表。\n\nBingkun的牛马 🐂',
    []
)
print("DONE")
