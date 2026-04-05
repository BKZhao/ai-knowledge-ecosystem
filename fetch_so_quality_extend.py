"""Fetch SO quality metrics for 2024-04 to 2025-12 via Stack Exchange API"""
import requests, time, csv, json, os
from datetime import datetime

API_KEY = 'rl_yXrLKrxSPQzCqJai54e1Y3bHz'
OUT = 'results/so_quality_monthly_extended.csv'
LOG = 'results/so_quality_extend_log.txt'
LANGUAGES = ['python','javascript','typescript','java','csharp','php','cpp','swift','kotlin','go','rust','scala','haskell','r']

SITE = 'stackoverflow'

def fetch_month(year, month):
    """Fetch questions for a given month with quality metrics"""
    from_date = f'{year}-{month:02d}-01'
    if month == 12:
        to_date = f'{year+1}-01-01'
    else:
        to_date = f'{year}-{month+1:02d}-01'
    
    all_questions = []
    page = 1
    has_more = True
    
    while has_more:
        params = {
            'order': 'desc', 'sort': 'activity', 'site': SITE,
            'fromdate': from_date, 'todate': to_date,
            'pagesize': 100, 'page': page,
            'filter': 'withbody',  # get body for length calc
            'key': API_KEY
        }
        
        try:
            r = requests.get('https://api.stackexchange.com/2.3/questions', params=params, timeout=30)
            data = r.json()
            
            if 'error_message' in data:
                log(f"API Error: {data['error_message']}")
                return None
            
            items = data.get('items', [])
            if not items:
                has_more = False
                break
            
            for q in items:
                tags = q.get('tags', [])
                # Check if question has any of our target language tags
                matched_langs = [t for t in tags if t in LANGUAGES]
                if not matched_langs:
                    continue
                
                body = q.get('body', '') or ''
                # Strip HTML tags for length calculation
                import re
                clean_body = re.sub('<[^>]+>', '', body)
                
                all_questions.append({
                    'lang': matched_langs[0],
                    'score': q.get('score', 0),
                    'view_count': q.get('view_count', 0),
                    'answer_count': q.get('answer_count', 0),
                    'is_answered': q.get('is_answered', False),
                    'title_length': len(q.get('title', '')),
                    'body_length': len(clean_body),
                    'comment_count': q.get('comment_count', 0),
                })
            
            has_more = data.get('has_more', False)
            page += 1
            
            if data.get('backoff', 0):
                time.sleep(data['backoff'] + 1)
            else:
                time.sleep(0.1)
                
        except Exception as e:
            log(f"Error fetching page {page}: {e}")
            time.sleep(5)
            continue
    
    if not all_questions:
        return None
    
    # Aggregate
    n = len(all_questions)
    return {
        'month': from_date,
        'n_questions': n,
        'avg_score': sum(q['score'] for q in all_questions) / n,
        'avg_views': sum(q['view_count'] for q in all_questions) / n,
        'pct_answered': sum(1 for q in all_questions if q['is_answered']) / n * 100,
        'avg_answer_count': sum(q['answer_count'] for q in all_questions) / n,
        'avg_body_length': sum(q['body_length'] for q in all_questions) / n,
        'avg_comment_count': sum(q['comment_count'] for q in all_questions) / n,
    }

def log(msg):
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG, 'a') as f:
        f.write(line + '\n')

def main():
    log("Starting SO quality data fetch: 2024-04 to 2025-12")
    
    months = []
    for year in [2024, 2025]:
        start_m = 4 if year == 2024 else 1
        end_m = 12 if year == 2025 else 12
        for m in range(start_m, end_m + 1):
            months.append((year, m))
    
    results = []
    for year, month in months:
        log(f"Fetching {year}-{month:02d}...")
        row = fetch_month(year, month)
        if row:
            results.append(row)
            log(f"  -> {row['n_questions']} questions")
        else:
            log(f"  -> No data")
        time.sleep(1)
    
    # Save
    with open(OUT, 'w', newline='') as f:
        if results:
            writer = csv.DictWriter(f, fieldnames=results[0].keys())
            writer.writeheader()
            writer.writerows(results)
    
    log(f"Done! Saved {len(results)} months to {OUT}")
    
    # Try to send notification
    try:
        from notify import send_update
        send_update('SO Quality Data Extended', f'Fetched {len(results)}/21 months for 2024-04 to 2025-12')
    except:
        pass

if __name__ == '__main__':
    main()
