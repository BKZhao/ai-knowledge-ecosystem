"""
训练本地分类模型 + 分类扩展数据
用112k已标注数据训练，目标90%+准确率
"""
import pandas as pd
import numpy as np
import csv, json, os, time, random, re
from datetime import datetime
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import classification_report
from collections import Counter

BASE = "/home/node/.openclaw/workspaces/ou_061694b4b8257fa782c21a959956256d/stackoverflow_research"
LOG = f"{BASE}/results/train_classify_log.txt"

def log(msg):
    ts = datetime.now().strftime('%H:%M:%S')
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    with open(LOG, 'a') as f: f.write(line + '\n')

def main():
    # Phase 1: Load existing classification with features
    log("Phase 1: Loading classification data...")
    
    # Load existing 112k results
    rows = []
    with open(f"{BASE}/results/classification_results_combined.csv") as f:
        for r in csv.DictReader(f):
            rows.append(r)
    log(f"  Loaded {len(rows)} classified questions")
    
    # We need features. Check if we have a feature file
    # The original classification used post_id from the parquet data dump
    # We need to reconstruct features from what we have
    
    # Check for any feature data we saved
    feat_files = [
        f"{BASE}/results/annotation_llm_labeled.csv",
        f"{BASE}/results/annotation_sample_1000.csv",
    ]
    
    # Load the full SO questions from parquet if available
    try:
        import pyarrow.parquet as pq
        parquet_dir = f"{BASE}/data"
        if os.path.exists(parquet_dir):
            parquet_files = []
            for root, dirs, files in os.walk(parquet_dir):
                for fn in files:
                    if fn.endswith('.parquet'):
                        parquet_files.append(os.path.join(root, fn))
            log(f"  Found {len(parquet_files)} parquet files")
    except:
        parquet_files = []
    
    # Load the cached extended questions (these have features!)
    log("  Loading cached questions from extended fetch...")
    cached_qs = {}
    for qfile in [f"{BASE}/results/extended_fetch_log.txt"]:
        pass  # parse from the script's internal data
    
    # Actually, we need to save the fetched questions. Check if they were saved.
    # The fetch_and_classify_extended.py stored questions in memory but didn't save to file
    # We need to re-fetch OR use a different approach
    
    # Better approach: use the annotation_llm_labeled.csv which has features
    ann_file = f"{BASE}/results/annotation_llm_labeled.csv"
    if os.path.exists(ann_file):
        df_ann = pd.read_csv(ann_file)
        log(f"  Annotation file: {len(df_ann)} rows with features")
        log(f"  Columns: {list(df_ann.columns)}")
    else:
        df_ann = pd.DataFrame()
    
    # The annotation file only has 700 rows. Not enough to train.
    # Better: load from parquet, merge with classification labels
    
    log("  Loading parquet data for features...")
    all_features = []
    
    if parquet_files:
        # Load parquet files
        for pf in parquet_files[:20]:  # limit to avoid OOM
            try:
                table = pq.read_table(pf, columns=['Id','CreationDate','Score','Tags','BodyLength','CodeBlockCount','TitleLength'])
                df = table.to_pandas()
                all_features.append(df)
            except Exception as e:
                log(f"  Error loading {pf}: {e}")
        
        if all_features:
            df_feat = pd.concat(all_features, ignore_index=True)
            df_feat.columns = ['Id','CreationDate','Score','Tags','BodyLength','CodeBlockCount','TitleLength']
            log(f"  Parquet features: {len(df_feat)} rows")
    else:
        log("  No parquet files found")
        df_feat = pd.DataFrame()
    
    # Alternative: re-fetch questions for training using API
    # Since we have 112k post_ids with labels, we can batch-fetch their features
    log("  Building training set from classified post_ids...")
    
    # For training, we need post features. Let's use the SO API to batch fetch.
    # But that would take too long for 112k posts.
    # 
    # BETTER APPROACH: Use the 62,749 cached questions (which we can re-fetch)
    # plus a sample of the 112k existing to train on.
    
    # Actually, the simplest approach: 
    # 1. Fetch a sample of questions (50k) from SO API with features
    # 2. Use existing 112k labels to train a model based on tags, body length, code blocks
    # 3. The model doesn't need body text - tags + length features should be sufficient
    
    # Check if we saved questions from the extended fetch
    # The script didn't save them to disk! Let me modify approach.
    
    # APPROACH: Save training data first, then train
    # Step 1: For each of the 112k classified posts, fetch their features via API (batch)
    # Step 2: Train model
    # Step 3: Classify 62k new questions
    
    # This is too slow for 112k posts. Better: sample 10k posts, fetch features, train.
    
    # FASTEST APPROACH: Train on annotation_llm_labeled.csv features + use tag-based features
    
    # Let me check what annotation_sample_1000.csv has
    sample_file = f"{BASE}/results/annotation_sample_1000.csv"
    if os.path.exists(sample_file):
        df_sample = pd.read_csv(sample_file)
        log(f"  Sample file: {len(df_sample)} rows, cols: {list(df_sample.columns)}")
    
    # Actually the best approach for fast results:
    # Use tags + numeric features as input, train a simple model
    # The key insight: we already have 112k post_ids with labels
    # We need to map post_ids back to their features
    
    # Check if there's a combined features file
    for fname in ['results/so_questions_features.csv', 'results/questions_features.parquet']:
        if os.path.exists(f"{BASE}/{fname}"):
            log(f"  Found features file: {fname}")
    
    log("  No pre-computed features file found for 112k posts")
    log("  Using annotation data + API fetch for training...")
    
    # REVISED STRATEGY: 
    # 1. Fetch 5000 questions from various years (already have tags/lengths)
    # 2. Train classifier on these features
    # 3. Use model to classify the 62k new questions
    
    # But wait - the 112k classification used the parquet data which has features
    # The parquet data has: Id, CreationDate, Tags, BodyLength, CodeBlockCount, TitleLength
    # The 112k classification maps post_id -> label
    # If we have parquet with these features, we can join!
    
    # Let me search more broadly for parquet files
    for root, dirs, files in os.walk(f"{BASE}/data"):
        for fn in files:
            if 'question' in fn.lower() or 'posts' in fn.lower():
                log(f"  Found: {os.path.join(root, fn)}")
    
    log("\n  Trying to load any parquet data...")
    for root, dirs, files in os.walk(f"{BASE}/data"):
        for fn in files:
            if fn.endswith('.parquet'):
                path = os.path.join(root, fn)
                try:
                    t = pq.read_table(path)
                    cols = t.column_names[:5]
                    nrows = t.num_rows
                    log(f"  {fn}: {nrows} rows, cols: {cols}")
                except:
                    pass

if __name__ == '__main__':
    main()
