# =============================================================================
# extract_dv5_dv6.py — Extract DV5 and DV6 from parquet (pipe-separated Tags)
# =============================================================================
# DV5: Questioner concentration (Gini, Top10%, HHI of question counts per user)
#       per language × month  [Note: using questioner concentration since
#       the parquet lacks ParentId to link answerers to language tags]
# DV6: Question complexity (body length, code blocks, frac with code)
# =============================================================================

import pandas as pd
import numpy as np
import pyarrow.parquet as pq
import os

WORKDIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PARQUET = os.path.join(WORKDIR, "data/parquet/posts_2018plus.parquet")
OUT_DV5 = os.path.join(WORKDIR, "data/processed/dv5_answer_concentration.csv")
OUT_DV6 = os.path.join(WORKDIR, "data/processed/dv6_question_complexity.csv")
os.makedirs(os.path.join(WORKDIR, "data/processed"), exist_ok=True)

# Language tag patterns (pipe-delimited in parquet: |python|ctypes|)
LANG_TAG_MAP = {
    'python':     '|python|',
    'javascript': '|javascript|',
    'typescript': '|typescript|',
    'java':       '|java|',
    'csharp':     '|c#|',
    'go':         '|go|',
    'ruby':       '|ruby|',
    'cpp':        '|c++|',
    'c':          '|c|',
    'r':          '|r|',
    'rust':       '|rust|',
    'haskell':    '|haskell|',
    'assembly':   '|assembly|',
}

def assign_language(tags_series):
    """Vectorized language assignment from pipe-delimited tags."""
    result = pd.Series(['other'] * len(tags_series), index=tags_series.index, dtype=str)
    for lang, pattern in LANG_TAG_MAP.items():
        mask = tags_series.str.contains(pattern, regex=False, na=False)
        result[mask] = lang
    # Priority: typescript > javascript > java, cpp > c > csharp
    # Re-apply higher priority ones last to overwrite lower priority
    priority_order = ['assembly','haskell','r','c','cpp','csharp','go','ruby','rust',
                      'java','javascript','typescript','python']
    for lang in priority_order:
        pattern = LANG_TAG_MAP[lang]
        mask = tags_series.str.contains(pattern, regex=False, na=False)
        result[mask] = lang
    return result

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
    pf = pq.ParquetFile(PARQUET)
    cols = ['PostTypeId', 'Id', 'OwnerUserId', 'CreationDate', 'Tags', 'BodyLength', 'CodeBlockCount']
    
    # Accumulators
    dv5_agg = {}   # (lang, month) -> {user_id: count}
    dv6_agg = {}   # (lang, month) -> {body: [], code: []}
    
    batch_num = 0
    for batch in pf.iter_batches(columns=cols, batch_size=2_000_000):
        df = batch.to_pandas()
        batch_num += 1
        
        # Only process questions (PostTypeId=1), which have Tags
        questions = df[df['PostTypeId'] == 1].copy()
        if len(questions) == 0:
            continue
        
        # Assign language from pipe-delimited Tags
        questions['lang'] = assign_language(questions['Tags'])
        questions = questions[questions['lang'] != 'other']
        if len(questions) == 0:
            continue
        
        questions['month'] = pd.to_datetime(questions['CreationDate']).dt.to_period('M').astype(str)
        
        print(f"Batch {batch_num}: {len(questions)} target-language questions")
        
        # DV5: user contribution concentration
        for (lang, month), grp in questions.groupby(['lang', 'month']):
            valid = grp[grp['OwnerUserId'] > 0]
            user_counts = valid['OwnerUserId'].value_counts()
            key = (lang, month)
            if key not in dv5_agg:
                dv5_agg[key] = {}
            for uid, cnt in user_counts.items():
                dv5_agg[key][uid] = dv5_agg[key].get(uid, 0) + cnt
        
        # DV6: question complexity
        for (lang, month), grp in questions.groupby(['lang', 'month']):
            key = (lang, month)
            if key not in dv6_agg:
                dv6_agg[key] = {'body': [], 'code': []}
            dv6_agg[key]['body'].extend(grp['BodyLength'].tolist())
            dv6_agg[key]['code'].extend(grp['CodeBlockCount'].tolist())
    
    # Compute DV5 metrics
    print(f"\nComputing DV5 metrics from {len(dv5_agg)} lang-month cells...")
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
            'n_active_users': len(counts), 'total_questions': int(total),
            'gini': round(g, 6), 'hhi': round(hhi, 6), 'top10_share': round(top10, 6),
        })
    
    df5 = pd.DataFrame(dv5_rows).sort_values(['lang', 'month']).reset_index(drop=True)
    df5.to_csv(OUT_DV5, index=False)
    print(f"DV5 saved: {len(df5)} rows, {df5['lang'].nunique()} languages")
    
    # Compute DV6 metrics
    print(f"\nComputing DV6 metrics from {len(dv6_agg)} lang-month cells...")
    dv6_rows = []
    for (lang, month), vals in dv6_agg.items():
        body = np.array(vals['body'])
        code = np.array(vals['code'])
        dv6_rows.append({
            'lang': lang, 'month': month,
            'n_questions': len(body),
            'median_body_length': round(float(np.median(body)), 2),
            'median_code_blocks': round(float(np.median(code)), 4),
            'frac_with_code': round(float(np.mean(code > 0)), 6),
        })
    
    df6 = pd.DataFrame(dv6_rows).sort_values(['lang', 'month']).reset_index(drop=True)
    df6.to_csv(OUT_DV6, index=False)
    print(f"DV6 saved: {len(df6)} rows, {df6['lang'].nunique()} languages")
    print("\nDone!")

if __name__ == '__main__':
    main()
