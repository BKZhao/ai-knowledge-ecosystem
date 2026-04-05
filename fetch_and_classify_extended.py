"""
修复版：SO质量指标 + LLM分类，2024-04到2025-12
SO API fromdate/todate 需要Unix时间戳
"""
import requests, json, time, csv, re, os, random
from datetime import datetime
from collections import Counter, defaultdict

SO_KEY = "rl_yXrLKrxSPQzCqJai54e1Y3bHz"
LLM_URL = "https://api.siliconflow.cn/v1/chat/completions"
LLM_KEY = "sk-clbbhigzzvnledglcvvirgunqdgouvzlgbndsegsmaaonpgcs"
BASE = "/home/node/.openclaw/workspaces/ou_061694b4b8257fa782c21a959956256d/stackoverflow_research"
LOG = f"{BASE}/results/extended_fetch_log.txt"
LANGS = ['python','javascript','typescript','java','csharp','php','cpp','swift','kotlin','go','rust','scala','haskell','r']

def log(msg):
    ts = datetime.now().strftime('%H:%M:%S')
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    with open(LOG, 'a') as f: f.write(line + '\n')

def ts(year, month, day=1):
    return int(datetime(year, month, day).timestamp())

def fetch_so_questions(year, month, lang, pages=5):
    """Fetch questions via SO API with Unix timestamps"""
    fromdate = ts(year, month)
    if month == 12: todate = ts(year+1, 1)
    else: todate = ts(year, month+1)
    
    questions = []
    for page in range(1, pages+1):
        try:
            r = requests.get('https://api.stackexchange.com/2.3/questions', params={
                'order': 'desc', 'sort': 'activity', 'site': 'stackoverflow',
                'fromdate': fromdate, 'todate': todate,
                'tagged': lang, 'pagesize': 100, 'page': page,
                'filter': 'withbody', 'key': SO_KEY
            }, timeout=30)
            data = r.json()
            if 'error_message' in data:
                log(f"  API error {lang} {year}-{month:02d}: {data['error_message']}")
                break
            items = data.get('items', [])
            if not items: break
            for q in items:
                body = q.get('body','') or ''
                clean = re.sub('<[^>]+>', '', body)
                questions.append({
                    'post_id': str(q['question_id']),
                    'year': str(year), 'month': f'{month:02d}', 'lang': lang,
                    'tags': ','.join(q.get('tags',[])),
                    'title_len': len(q.get('title','')),
                    'body_len': len(clean),
                    'code_blocks': body.count('<code>'),
                    'score': q.get('score',0),
                    'view_count': q.get('view_count',0),
                    'answer_count': q.get('answer_count',0),
                    'is_answered': q.get('is_answered',False),
                    'comment_count': q.get('comment_count',0),
                })
            if not data.get('has_more'): break
            time.sleep(max(data.get('backoff',0)+0.5, 0.5))
        except Exception as e:
            log(f"  Error: {e}"); time.sleep(5)
    return questions

def classify_question(q):
    """Classify single question via DeepSeek-V3"""
    prompt = f"""Classify this Stack Overflow question into EXACTLY ONE:
- How-to: step-by-step, "how do I..."
- Debug: error diagnosis, bug fixing
- Conceptual: understanding, comparison, reasoning
- Architecture: design, best practices, patterns

Tag: {q['tags']}
Title len: {q['title_len']}, Body len: {q['body_len']}, Code blocks: {q['code_blocks']}
Reply ONLY the type name."""
    try:
        r = requests.post(LLM_URL, json={
            'model': 'deepseek-ai/DeepSeek-V3',
            'messages': [{'role':'user','content':prompt}],
            'max_tokens': 10, 'temperature': 0
        }, headers={'Authorization': f'Bearer {LLM_KEY}'}, timeout=15)
        text = r.json()['choices'][0]['message']['content'].strip()
        tl = text.lower()
        if 'how' in tl and 'to' in tl: return 'How-to'
        elif 'debug' in tl: return 'Debug'
        elif 'concept' in tl: return 'Conceptual'
        elif 'architect' in tl or 'design' in tl or 'pattern' in tl: return 'Architecture'
        elif text in ['How-to','Debug','Conceptual','Architecture']: return text
        else: return 'Conceptual'  # default
    except:
        return 'ERROR'

def main():
    log("=== Starting extended fetch + classify: 2024-04 to 2025-12 ===")
    
    months = []
    for y in [2024, 2025]:
        sm = 4 if y == 2024 else 1
        for m in range(sm, 13):
            months.append((y, m))
    
    SAMPLE = 300  # per month per lang
    all_qs = []
    
    # Phase 1: Fetch
    log("Phase 1: Fetching questions...")
    for y, m in months:
        for lang in LANGS:
            qs = fetch_so_questions(y, m, lang, pages=5)
            if qs:
                # Sample
                if len(qs) > SAMPLE:
                    random.seed(hash(f"{y}{m}{lang}"))
                    qs = random.sample(qs, SAMPLE)
                all_qs.extend(qs)
        log(f"  {y}-{m:02d}: cumulative {len(all_qs)} questions")
    
    log(f"Phase 1 complete: {len(all_qs)} questions fetched")
    
    # Phase 2: Quality aggregation
    log("Phase 2: Computing quality metrics...")
    quality_rows = []
    for y, m in months:
        m_qs = [q for q in all_qs if q['year']==str(y) and q['month']==f'{m:02d}']
        if not m_qs: continue
        n = len(m_qs)
        quality_rows.append({
            'month': f'{y}-{m:02d}-01',
            'n_questions': n,
            'avg_score': round(sum(q['score'] for q in m_qs)/n, 2),
            'avg_views': round(sum(q['view_count'] for q in m_qs)/n, 1),
            'pct_answered': round(sum(1 for q in m_qs if q['is_answered'])/n*100, 1),
            'avg_answer_count': round(sum(q['answer_count'] for q in m_qs)/n, 2),
            'avg_body_length': round(sum(q['body_len'] for q in m_qs)/n, 1),
            'avg_comment_count': round(sum(q['comment_count'] for q in m_qs)/n, 2),
        })
    
    # Append to existing quality file
    qfile = f"{BASE}/results/so_quality_monthly_extended.csv"
    with open(qfile, 'w', newline='') as f:
        if quality_rows:
            w = csv.DictWriter(f, fieldnames=quality_rows[0].keys())
            w.writeheader(); w.writerows(quality_rows)
    log(f"Quality metrics: {len(quality_rows)} months saved")
    
    # Phase 3: Classify
    log("Phase 3: LLM classification...")
    label_map = {'How-to':0, 'Debug':1, 'Conceptual':2, 'Architecture':3}
    classified = 0
    labels = Counter()
    errors = 0
    BATCH = 4
    
    # Append mode
    clfile = f"{BASE}/results/classification_extended.csv"
    existing_ids = set()
    if os.path.exists(clfile):
        with open(clfile) as f:
            for row in csv.DictReader(f):
                existing_ids.add(row['post_id'])
    
    new_qs = [q for q in all_qs if q['post_id'] not in existing_ids]
    log(f"Questions to classify: {len(new_qs)}")
    
    with open(clfile, 'a', newline='') as f:
        w = csv.DictWriter(f, fieldnames=['post_id','label_id','label'])
        if not existing_ids:
            w.writeheader()
        
        for i in range(0, len(new_qs), BATCH):
            batch = new_qs[i:i+BATCH]
            for q in batch:
                label = classify_question(q)
                lid = label_map.get(label, 4)
                w.writerow({'post_id': q['post_id'], 'label_id': str(lid), 'label': label})
                if label != 'ERROR':
                    labels[label] += 1
                else:
                    errors += 1
                classified += 1
            
            if classified % 200 == 0:
                log(f"  Classified: {classified}/{len(new_qs)} | labels: {dict(labels.most_common())} | errors: {errors}")
    
    log(f"Classification done: {classified} total, {errors} errors")
    log(f"Label distribution: {dict(labels.most_common())}")
    
    # Phase 4: Merge
    main_file = f"{BASE}/results/classification_results_combined.csv"
    all_rows = []
    seen = set()
    for csvfile in [main_file, clfile]:
        if not os.path.exists(csvfile): continue
        with open(csvfile) as f:
            for row in csv.DictReader(f):
                pid = row['post_id']
                if pid not in seen:
                    seen.add(pid)
                    all_rows.append(row)
    
    os.rename(main_file, main_file + '.bak2')
    with open(main_file, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=['post_id','label_id','label'])
        w.writeheader(); w.writerows(all_rows)
    
    log(f"Merged! Total: {len(all_rows)} in {main_file}")
    
    # Notify
    try:
        from notify import send_update
        send_update('Extended Data Complete',
            f'Quality: {len(quality_rows)} months\nClassification: {classified} new (total {len(all_rows)})\nLabels: {dict(labels.most_common())}')
    except: pass

if __name__ == '__main__':
    main()
