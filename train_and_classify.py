"""
Train classifier on parquet features + 112k labels, then classify 62k new questions
"""
import pandas as pd
import numpy as np
import pyarrow.parquet as pq
import csv, json, os, time, random, re
from datetime import datetime
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import classification_report, accuracy_score
from collections import Counter
import xgboost as xgb

BASE = "/home/node/.openclaw/workspaces/ou_061694b4b8257fa782c21a959956256d/stackoverflow_research"
LOG = f"{BASE}/results/train_classify_log.txt"
PARQUET = f"{BASE}/data/parquet/posts_2018plus.parquet"
LABELS = f"{BASE}/results/classification_results_combined.csv"
EXT_QS = f"{BASE}/data/fetched_2024plus/questions_sample.csv"
OUT_CLASSIFIED = f"{BASE}/results/classification_extended.csv"
OUT_MAIN = f"{BASE}/results/classification_results_combined.csv"
MODEL_FILE = f"{BASE}/results/question_type_classifier.json"

LANGUAGES = {'python':0,'javascript':1,'typescript':2,'java':3,'csharp':4,'php':5,
             'cpp':6,'swift':7,'kotlin':8,'go':9,'rust':10,'scala':11,'haskell':12,'r':13}

def log(msg):
    ts = datetime.now().strftime('%H:%M:%S')
    print(f"[{ts}] {msg}", flush=True)
    with open(LOG, 'a') as f: f.write(f"[{ts}] {msg}\n")

def extract_features(tags_str, body_len, code_blocks, year, score=0):
    """Extract features from a question"""
    tags = re.findall(r'<([^>]+)>', tags_str) if tags_str else []
    tag = tags[0].lower() if tags else ''
    
    # Language one-hot
    lang_feat = [1.0 if tag == l else 0.0 for l in LANGUAGES]
    
    # Numeric features
    bl = min(body_len or 0, 15000) / 15000
    cb = min(code_blocks or 0, 20) / 20
    yr = (year - 2018) / 8.0
    sc = min(abs(score or 0), 100) / 100
    
    # Tag-derived features
    has_how = 1.0 if any(w in ' '.join(tags) for w in ['how','implement','use','create','make','add','get','set','write','read','convert','parse','install','run','call','send','receive','import','export','connect','update','delete','insert','upload','download','build','compile','deploy','configure','setup']) else 0.0
    has_debug = 1.0 if any(w in ' '.join(tags) for w in ['error','bug','fix','issue','crash','fail','exception','warning','debug','problem','wrong','not work','broken','unexpected','null','undefined','typeerror','referenceerror','syntaxerror']) else 0.0
    has_concept = 1.0 if any(w in ' '.join(tags) for w in ['difference','vs','what','why','best','which','should','explain','understand','concept','compare','between','meaning','purpose','approach','pattern','architecture','design','structure','principle']) else 0.0
    has_arch = 1.0 if any(w in ' '.join(tags) for w in ['design','pattern','architecture','structure','approach','strategy','best-practice','refactor','scalable','maintainable','clean-code','solid','dry','microservice','monolith','framework']) else 0.0
    n_tags = min(len(tags), 10) / 10.0
    
    return lang_feat + [bl, cb, yr, sc, has_how, has_debug, has_concept, has_arch, n_tags]

def main():
    # Phase 1: Load labels
    log("Phase 1: Loading labels...")
    label_df = pd.read_csv(LABELS)
    label_df['post_id'] = label_df['post_id'].astype(str)
    label_map = dict(zip(label_df['post_id'], label_df['label']))
    log(f"  {len(label_map)} labeled posts")
    
    label_dist = Counter(label_map.values())
    log(f"  Distribution: {dict(label_dist)}")
    
    # Phase 2: Load parquet and extract features for labeled posts
    log("Phase 2: Loading parquet features for labeled posts...")
    
    # Read parquet in batches
    labeled_ids = set(label_map.keys())
    train_features = []
    train_labels = []
    
    # Also extract year from CreationDate
    parquet_cols = ['Id', 'Tags', 'BodyLength', 'CodeBlockCount', 'CreationDate', 'Score']
    
    pf = pq.ParquetFile(PARQUET)
    log(f"  Parquet: {pf.metadata.num_rows} rows, {pf.num_row_groups} row groups")
    
    found = 0
    for rg in range(pf.num_row_groups):
        batch = pf.read_row_group(rg, columns=parquet_cols).to_pandas()
        batch['Id'] = batch['Id'].astype(str)
        
        for _, row in batch.iterrows():
            pid = str(row['Id'])
            if pid in labeled_ids:
                year = int(str(row['CreationDate'])[:4])
                feat = extract_features(row['Tags'], row['BodyLength'], row['CodeBlockCount'], year, row.get('Score', 0))
                train_features.append(feat)
                train_labels.append(label_map[pid])
                found += 1
                del labeled_ids[pid]
        
        if found % 20000 == 0 and found > 0:
            log(f"  Found {found} matched, remaining target: {len(labeled_ids)}")
        
        if not labeled_ids:
            break
    
    log(f"  Matched {found} labeled posts with features")
    
    if found < 10000:
        log(f"  WARNING: Only {found} matches, training may be limited")
    
    # Phase 3: Train model
    log("Phase 3: Training XGBoost classifier...")
    
    X = np.array(train_features)
    le = LabelEncoder()
    y = le.fit_transform(train_labels)
    
    log(f"  Classes: {dict(zip(le.classes_, le.transform(le.classes_)))}")
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    
    model = xgb.XGBClassifier(
        n_estimators=200, max_depth=6, learning_rate=0.1,
        subsample=0.8, colsample_bytree=0.8, random_state=42,
        use_label_encoder=False, eval_metric='mlogloss',
        min_child_weight=3, gamma=0.1
    )
    
    model.fit(X_train, y_train, eval_set=[(X_test, y_test)], verbose=False)
    
    y_pred = model.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    log(f"  Test Accuracy: {acc:.4f}")
    
    print("\n" + classification_report(y_test, y_pred, target_names=le.classes_))
    with open(LOG, 'a') as f:
        report = classification_report(y_test, y_pred, target_names=le.classes_)
        f.write(f"\nClassification Report:\n{report}\n")
    
    # Save model
    model.save_model(MODEL_FILE)
    log(f"  Model saved to {MODEL_FILE}")
    
    # Phase 4: Classify extended questions
    log("Phase 4: Loading extended questions to classify...")
    
    # Check for the cached questions sample
    if os.path.exists(EXT_QS):
        ext_df = pd.read_csv(EXT_QS)
        log(f"  Extended questions: {len(ext_df)} from {EXT_QS}")
        log(f"  Columns: {list(ext_df.columns)}")
    
    # Also check the classification_extended.csv for ERROR entries
    errors_to_retry = []
    if os.path.exists(OUT_CLASSIFIED):
        with open(OUT_CLASSIFIED) as f:
            for row in csv.DictReader(f):
                if row.get('label') == 'ERROR':
                    errors_to_retry.append(row['post_id'])
        log(f"  ERROR entries to fix: {len(errors_to_retry)}")
    
    # We need to re-fetch the 62k questions with features
    # Since fetch_and_classify_extended.py didn't save them to disk, 
    # let's fetch them again but this time save to CSV first
    
    # Actually, check the extended_fetch log for cached data
    # The script had all_questions list - need to re-fetch
    
    # FASTEST: Use SO API to fetch questions for 2024-04 to 2025-12
    # Save with features, then classify locally
    
    log("  Re-fetching extended questions (2024-04 to 2025-12)...")
    
    import requests
    SO_KEY = "rl_yXrLKrxSPQzCqJai54e1Y3bHz"
    
    months = []
    for y in [2024, 2025]:
        sm = 4 if y == 2024 else 1
        for m in range(sm, 13):
            months.append((y, m))
    
    all_ext = []
    SAMPLE = 300
    
    for y, m in months:
        for lang in LANGUAGES:
            fromdate = int(datetime(y, m, 1).timestamp())
            if m == 12: todate = int(datetime(y+1, 1, 1).timestamp())
            else: todate = int(datetime(y, m+1, 1).timestamp())
            
            for page in range(1, 6):
                try:
                    r = requests.get('https://api.stackexchange.com/2.3/questions', params={
                        'order':'desc','sort':'activity','site':'stackoverflow',
                        'fromdate':fromdate,'todate':todate,
                        'tagged':lang,'pagesize':100,'page':page,
                        'key': SO_KEY
                    }, timeout=30)
                    data = r.json()
                    if 'error_message' in data: break
                    items = data.get('items', [])
                    if not items: break
                    for q in items:
                        body = q.get('body','') or ''
                        clean = re.sub('<[^>]+>', '', body)
                        all_ext.append({
                            'post_id': str(q['question_id']),
                            'year': y, 'lang': lang,
                            'tags': q.get('Tags','') or str(q.get('tags',[])),
                            'body_len': len(clean),
                            'code_blocks': body.count('<code>'),
                            'score': q.get('score',0),
                        })
                    if not data.get('has_more'): break
                    time.sleep(max(data.get('backoff',0)+0.5, 0.5))
                except Exception as e:
                    log(f"  Fetch error: {e}")
                    time.sleep(5)
        
        log(f"  {y}-{m:02d}: cumulative {len(all_ext)}")
    
    log(f"  Total fetched: {len(all_ext)}")
    
    # Sample per stratum
    from itertools import groupby
    sampled = []
    for (y, lang), grp in groupby(sorted(all_ext, key=lambda x: (x['year'], x['lang'])), key=lambda x: (x['year'], x['lang'])):
        items = list(grp)
        if len(items) > SAMPLE:
            random.seed(hash(f"{y}{lang}"))
            items = random.sample(items, SAMPLE)
        sampled.extend(items)
    
    log(f"  After sampling: {len(sampled)}")
    
    # Phase 5: Classify
    log("Phase 5: Classifying with local model...")
    
    ext_features = []
    ext_ids = []
    for q in sampled:
        feat = extract_features(q['tags'], q['body_len'], q['code_blocks'], q['year'], q['score'])
        ext_features.append(feat)
        ext_ids.append(q['post_id'])
    
    X_ext = np.array(ext_features)
    y_ext_pred = model.predict(X_ext)
    y_ext_labels = le.inverse_transform(y_ext_pred)
    
    label_dist_new = Counter(y_ext_labels)
    log(f"  Classified {len(ext_ids)} questions")
    log(f"  Distribution: {dict(label_dist_new)}")
    
    # Phase 6: Merge
    log("Phase 6: Merging with main classification file...")
    
    # Remove old ERROR entries
    new_rows = []
    for pid, label in zip(ext_ids, y_ext_labels):
        new_rows.append({'post_id': pid, 'label_id': str(le.transform([label])[0]), 'label': label})
    
    # Load main, remove duplicates
    all_rows = []
    seen = set()
    
    main_ids = set()
    with open(OUT_MAIN) as f:
        for row in csv.DictReader(f):
            pid = row['post_id']
            main_ids.add(pid)
            if pid not in seen:
                seen.add(pid)
                all_rows.append(row)
    
    # Add new (skip if already in main)
    added = 0
    for row in new_rows:
        if row['post_id'] not in seen:
            seen.add(row['post_id'])
            all_rows.append(row)
            added += 1
    
    # Backup and save
    os.rename(OUT_MAIN, OUT_MAIN + '.bak3')
    with open(OUT_MAIN, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=['post_id','label_id','label'])
        w.writeheader()
        w.writerows(all_rows)
    
    log(f"  Added {added} new classifications")
    log(f"  Total: {len(all_rows)} in {OUT_MAIN}")
    
    # Final distribution
    final_dist = Counter(r['label'] for r in all_rows)
    log(f"  Final distribution: {dict(final_dist)}")
    
    # Notify
    try:
        from notify import send_update
        send_update('Local Classifier Complete',
            f'Model accuracy: {acc:.1%}\nNew classified: {added}\nTotal: {len(all_rows)}\nDistribution: {dict(final_dist)}')
    except: pass
    
    log("DONE!")

if __name__ == '__main__':
    main()
