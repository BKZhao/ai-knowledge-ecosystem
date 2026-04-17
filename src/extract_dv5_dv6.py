# =============================================================================
# extract_dv5_dv6.py — Efficient extraction using parquet + tag filtering
# =============================================================================

import pandas as pd
import numpy as np
import pyarrow.parquet as pq
import os, sys

WORKDIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PARQUET = os.path.join(WORKDIR, "data/parquet/posts_2018plus.parquet")
TITLES_CSV = os.path.join(WORKDIR, "data/parquet/post_titles.csv")
OUT_DV5 = os.path.join(WORKDIR, "data/processed/dv5_answer_concentration.csv")
OUT_DV6 = os.path.join(WORKDIR, "data/processed/dv6_question_complexity.csv")
os.makedirs(os.path.join(WORKDIR, "data/processed"), exist_ok=True)

# Language -> tag patterns for post_titles.csv (space-separated)
LANG_TAG_MAP = {
    'python': ['python'],
    'javascript': ['javascript'],  # check before java
    'typescript': ['typescript'],
    'java': ['java'],
    'csharp': ['c#'],
    'go': ['go'],
    'ruby': ['ruby'],
    'cpp': ['c++'],
    'c': ['c'],
    'r': ['r'],
    # Note: single-letter tags are real SO tags. 'c' won't match 'css' etc
    # because we split into individual tags first.
    'rust': ['rust'],
    'haskell': ['haskell'],
    'assembly': ['assembly'],
}

def build_id_lang_map():
    """Build Id -> language map from post_titles.csv."""
    print("Building Id->language map from post_titles.csv...")
    id_lang = {}
    
    # Read in chunks, filter for target language tags
    for chunk in pd.read_csv(TITLES_CSV, sep='\t', usecols=['Id', 'Tags'], chunksize=5_000_000):
        chunk = chunk.dropna(subset=['Tags'])
        chunk['Tags'] = chunk['Tags'].str.lower().str.split()
        
        for lang, tags in LANG_TAG_MAP.items():
            mask = chunk['Tags'].apply(lambda ts: any(t in tags for t in (ts or [])))
            matched = chunk.loc[mask, 'Id']
            for pid in matched:
                id_lang[int(pid)] = lang
    
    print(f"  Found {len(id_lang)} posts with target language tags")
    return id_lang

def gini(values):
    values = np.array(values, dtype=float)
    values = values[values > 0]
    if len(values) <= 1:
        return 0.0
    values = np.sort(values)
    n = len(values)
    index = np.arange(1, n + 1)
    return (2 * np.sum(index * values) - (n + 1) * np.sum(values)) / (n * np.sum(values))

def main():
    id_lang = build_id_lang_map()
    
    # Filter parquet for target post IDs
    target_ids_arr = np.array(list(id_lang.keys()), dtype=np.int64)
    id_lang_arr = np.array([id_lang[k] for k in id_lang.keys()], dtype=object)
    # Build lookup: sort and binary search
    sort_idx = np.argsort(target_ids_arr)
    sorted_ids = target_ids_arr[sort_idx]
    sorted_langs = id_lang_arr[sort_idx]
    
    def lookup_langs(ids):
        idx = np.searchsorted(sorted_ids, ids)
        idx = np.clip(idx, 0, len(sorted_ids) - 1)
        found = sorted_ids[idx] == ids
        result = np.empty(len(ids), dtype=object)
        result[found] = sorted_langs[idx[found]]
        result[~found] = None
        return result
    
    pf = pq.ParquetFile(PARQUET)
    cols = ['PostTypeId', 'Id', 'OwnerUserId', 'CreationDate', 'BodyLength', 'CodeBlockCount']
    
    # DV5: answer concentration
    print("\nExtracting DV5: Answer Concentration...")
    dv5_agg = {}
    
    for batch in pf.iter_batches(columns=cols, batch_size=2_000_000):
        df = batch.to_pandas()
        
        ids = df['Id'].values.astype(np.int64)
        mask = np.isin(ids, sorted_ids)
        if not mask.any():
            continue
        df = df[mask].copy()
        df['lang'] = lookup_langs(df['Id'].values.astype(np.int64))
        df = df[df['lang'].notna()]
        if len(df) == 0:
            continue
        
        # Answers only
        answers = df[(df['PostTypeId'] == 2) & (df['OwnerUserId'] > 0)]
        if len(answers) == 0:
            continue
        answers['month'] = pd.to_datetime(answers['CreationDate']).dt.to_period('M').astype(str)
        
        for (lang, month), grp in answers.groupby(['lang', 'month']):
            user_counts = grp['OwnerUserId'].value_counts()
            key = (lang, month)
            if key not in dv5_agg:
                dv5_agg[key] = {}
            for uid, cnt in user_counts.items():
                dv5_agg[key][uid] = dv5_agg[key].get(uid, 0) + cnt
    
    dv5_rows = []
    for (lang, month), user_map in dv5_agg.items():
        counts = np.array(list(user_map.values()))
        total = counts.sum()
        if total == 0:
            continue
        shares = counts / total
        g = gini(counts)
        hhi = float((shares ** 2).sum())
        n_top = max(1, int(np.ceil(len(counts) * 0.1)))
        top10 = float(np.sort(shares)[::-1][:n_top].sum())
        dv5_rows.append({
            'lang': lang, 'month': month,
            'n_answerers': len(counts), 'total_answers': int(total),
            'gini': round(g, 6), 'hhi': round(hhi, 6), 'top10_share': round(top10, 6),
        })
    
    df5 = pd.DataFrame(dv5_rows).sort_values(['lang', 'month']).reset_index(drop=True)
    df5.to_csv(OUT_DV5, index=False)
    print(f"  DV5: {len(df5)} rows, {df5['lang'].nunique()} languages")
    
    # DV6: question complexity
    print("\nExtracting DV6: Question Complexity...")
    dv6_agg = {}
    
    for batch in pf.iter_batches(columns=cols, batch_size=2_000_000):
        df = batch.to_pandas()
        ids = df['Id'].values.astype(np.int64)
        mask = np.isin(ids, sorted_ids)
        if not mask.any():
            continue
        df = df[mask].copy()
        df['lang'] = lookup_langs(df['Id'].values.astype(np.int64))
        df = df[df['lang'].notna()]
        if len(df) == 0:
            continue
        
        questions = df[df['PostTypeId'] == 1]
        questions['month'] = pd.to_datetime(questions['CreationDate']).dt.to_period('M').astype(str)
        
        for (lang, month), grp in questions.groupby(['lang', 'month']):
            key = (lang, month)
            if key not in dv6_agg:
                dv6_agg[key] = {'body': [], 'code': []}
            dv6_agg[key]['body'].extend(grp['BodyLength'].tolist())
            dv6_agg[key]['code'].extend(grp['CodeBlockCount'].tolist())
    
    dv6_rows = []
    for (lang, month), vals in dv6_agg.items():
        body = np.array(vals['body'])
        code = np.array(vals['code'])
        dv6_rows.append({
            'lang': lang, 'month': month,
            'n_questions': len(body),
            'median_body_length': float(np.median(body)),
            'median_code_blocks': float(np.median(code)),
            'frac_with_code': round(float(np.mean(code > 0)), 6),
        })
    
    df6 = pd.DataFrame(dv6_rows).sort_values(['lang', 'month']).reset_index(drop=True)
    df6.to_csv(OUT_DV6, index=False)
    print(f"  DV6: {len(df6)} rows, {df6['lang'].nunique()} languages")
    
    print("\nDone!")

if __name__ == '__main__':
    main()
