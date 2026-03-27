"""
LLM分类 - 扩展版：对2024-04到2025-12的SO问题进行API抓取+分类
策略：
1. 通过SO API抓取每月问题（抽样，每月每语言500条）
2. 用DeepSeek-V3进行四分类
3. 结果合并到classification_results_combined.csv
"""
import requests, json, time, csv, re, os, random
from datetime import datetime
from collections import defaultdict

API_URL = "https://api.siliconflow.cn/v1/chat/completions"
API_KEY = "sk-clbbhigzzvnledglcvvirgunqdgouvzlgbndsegsmaaonpgcs"
SO_KEY = "rl_yXrLKrxSPQzCqJai54e1Y3bHz"
BASE = "/home/node/.openclaw/workspaces/ou_061694b4b8257fa782c21a959956256d/stackoverflow_research"
LOG_FILE = f"{BASE}/results/classify_extended_log.txt"
OUT_FILE = f"{BASE}/results/classification_extended.csv"
PROGRESS_FILE = f"{BASE}/results/classify_extended_progress.json"

LANGUAGES = ['python','javascript','typescript','java','csharp','php','cpp','swift','kotlin','go','rust','scala','haskell','r']
SITE = 'stackoverflow'

MONTHS = []
for y in [2024, 2025]:
    sm = 4 if y == 2024 else 1
    em = 12 if y == 2025 else 12
    for m in range(sm, em+1):
        MONTHS.append((y, m))

SAMPLE_PER_MONTH_LANG = 300  # 每月每语言抽300条
THREADS = 8

def log(msg):
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    with open(LOG_FILE, 'a') as f:
        f.write(line + '\n')

def load_progress():
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE) as f:
            return json.load(f)
    return {'classified': 0, 'total': 0, 'results': []}

def save_progress(p):
    # Only save metadata, results go to CSV
    meta = {k: v for k, v in p.items() if k != 'results'}
    with open(PROGRESS_FILE, 'w') as f:
        json.dump(meta, f)

def classify_batch(questions_batch):
    """Classify a batch of questions using DeepSeek-V3"""
    if not questions_batch:
        return []
    
    prompts = []
    for q in questions_batch:
        prompt = f"""Classify this Stack Overflow question into EXACTLY ONE of these 4 types:
- How-to: step-by-step operational guidance, "how do I..."
- Debug: error diagnosis, bug fixing, "why does this error occur"
- Conceptual: understanding, comparison, reasoning, "what is the difference"
- Architecture: design decisions, best practices, patterns

Tag: {q['tags']}
Title length: {q['title_len']}
Body length: {q['body_len']}
Code blocks: {q['code_blocks']}

Reply with ONLY the type name, nothing else."""
        prompts.append(prompt)
    
    results = []
    for i, prompt in enumerate(prompts):
        try:
            resp = requests.post(API_URL, json={
                'model': 'deepseek-ai/DeepSeek-V3',
                'messages': [{'role': 'user', 'content': prompt}],
                'max_tokens': 10,
                'temperature': 0
            }, headers={'Authorization': f'Bearer {API_KEY}'}, timeout=15)
            
            text = resp.json()['choices'][0]['message']['content'].strip()
            
            # Normalize label
            if 'how' in text.lower() and 'to' in text.lower():
                label = 'How-to'
            elif 'debug' in text.lower():
                label = 'Debug'
            elif 'concept' in text.lower():
                label = 'Conceptual'
            elif 'architect' in text.lower():
                label = 'Architecture'
            elif 'design' in text.lower() or 'pattern' in text.lower() or 'best' in text.lower():
                label = 'Architecture'
            else:
                label = text  # Keep as-is, might be one of the 4
            
            results.append({'post_id': questions_batch[i]['post_id'], 'label': label})
            
        except Exception as e:
            results.append({'post_id': questions_batch[i]['post_id'], 'label': 'ERROR'})
        
        time.sleep(0.05)
    
    return results

def fetch_questions_for_month(year, month, lang, max_pages=5):
    """Fetch sample questions for a month+language"""
    from_date = f'{year}-{month:02d}-01'
    if month == 12:
        to_date = f'{year+1}-01-01'
    else:
        to_date = f'{year}-{month+1:02d}-01'
    
    questions = []
    all_ids = set()
    
    # Use tagged endpoint for specific language
    for page in range(1, max_pages+1):
        try:
            r = requests.get('https://api.stackexchange.com/2.3/questions', params={
                'order': 'desc', 'sort': 'activity', 'site': SITE,
                'fromdate': from_date, 'todate': to_date,
                'tagged': lang, 'pagesize': 100, 'page': page,
                'key': SO_KEY
            }, timeout=30)
            
            data = r.json()
            if 'error_message' in data:
                log(f"  API error for {lang} {from_date} page {page}: {data['error_message']}")
                break
            
            items = data.get('items', [])
            if not items:
                break
            
            for q in items:
                qid = q['question_id']
                if qid in all_ids:
                    continue
                all_ids.add(qid)
                
                body = q.get('body', '') or ''
                clean = re.sub('<[^>]+>', '', body)
                code_blocks = body.count('<code>')
                
                questions.append({
                    'post_id': str(qid),
                    'tags': ','.join(q.get('tags', [])),
                    'title_len': len(q.get('title', '')),
                    'body_len': len(clean),
                    'code_blocks': code_blocks,
                    'year': str(year),
                    'lang': lang,
                })
            
            if not data.get('has_more', False):
                break
            
            if data.get('backoff', 0):
                time.sleep(data['backoff'] + 1)
            else:
                time.sleep(0.15)
                
        except Exception as e:
            log(f"  Error: {e}")
            time.sleep(5)
    
    # Sample down
    if len(questions) > SAMPLE_PER_MONTH_LANG:
        random.seed(42)
        questions = random.sample(questions, SAMPLE_PER_MONTH_LANG)
    
    return questions

def main():
    log(f"Starting extended classification: {len(MONTHS)} months × {len(LANGUAGES)} languages")
    total_strata = len(MONTHS) * len(LANGUAGES)
    log(f"Total strata: {total_strata}, target: ~{total_strata * SAMPLE_PER_MONTH_LANG} questions")
    
    progress = load_progress()
    
    # Collect all questions first
    all_questions = []
    
    for year, month in MONTHS:
        for lang in LANGUAGES:
            log(f"Fetching {year}-{month:02d} / {lang}...")
            qs = fetch_questions_for_month(year, month, lang)
            if qs:
                all_questions.extend(qs)
                log(f"  -> {len(qs)} questions")
            time.sleep(0.5)
    
    log(f"Total questions to classify: {len(all_questions)}")
    
    # Remove already classified
    existing_ids = set()
    if os.path.exists(OUT_FILE):
        with open(OUT_FILE) as f:
            for row in csv.DictReader(f):
                existing_ids.add(row['post_id'])
    
    new_qs = [q for q in all_questions if q['post_id'] not in existing_ids]
    log(f"After dedup: {len(new_qs)} questions to classify")
    
    # Classify in batches
    BATCH = 8
    classified = 0
    
    # Open CSV for append
    with open(OUT_FILE, 'a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['post_id', 'label_id', 'label'])
        if not existing_ids:
            writer.writeheader()
        
        for i in range(0, len(new_qs), BATCH):
            batch = new_qs[i:i+BATCH]
            results = classify_batch(batch)
            
            label_map = {'How-to': 0, 'Debug': 1, 'Conceptual': 2, 'Architecture': 3}
            for r in results:
                lid = label_map.get(r['label'], 4)
                writer.writerow({'post_id': r['post_id'], 'label_id': str(lid), 'label': r['label']})
            
            classified += len(results)
            progress['classified'] = classified
            progress['total'] = len(new_qs)
            save_progress(progress)
            
            if classified % 200 == 0:
                log(f"Progress: {classified}/{len(new_qs)}")
    
    log(f"DONE! Classified {classified} questions -> {OUT_FILE}")
    
    # Merge with main file
    main_file = f"{BASE}/results/classification_results_combined.csv"
    if os.path.exists(main_file) and os.path.exists(OUT_FILE):
        log("Merging with main classification file...")
        all_rows = []
        seen = set()
        
        for csvfile in [main_file, OUT_FILE]:
            with open(csvfile) as f:
                for row in csv.DictReader(f):
                    pid = row['post_id']
                    if pid not in seen:
                        seen.add(pid)
                        all_rows.append(row)
        
        # Backup main
        os.rename(main_file, main_file + '.bak')
        
        with open(main_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['post_id', 'label_id', 'label'])
            writer.writeheader()
            writer.writerows(all_rows)
        
        log(f"Merged! Total: {len(all_rows)} rows in {main_file}")
    
    # Notify
    try:
        from notify import send_update
        send_update('Extended Classification Complete', 
            f'Classified {classified} new questions (2024-04 to 2025-12)\nMerged into main file. Total: {len(all_rows)}')
    except:
        pass

if __name__ == '__main__':
    main()
