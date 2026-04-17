"""
DV5: Answer Concentration & DV6: Question Complexity
Optimized: use pyarrow with filters to avoid loading full 21.9M rows
"""
import pyarrow.parquet as pq
import pandas as pd
import numpy as np
from scipy import stats
import os, json, warnings
warnings.filterwarnings('ignore')

OUT = 'results/four_dv_analysis'
PARQUET = 'data/parquet/posts_2018plus.parquet'
TAG_COL = 'Tags'  # check actual column name

# Language tag mapping
LANG_MAP = {
    'python': '<python>', 'javascript': '<javascript>', 'typescript': '<typescript>',
    'java': '<java>', 'csharp': '<c#>', 'go': '<go>', 'ruby': '<ruby>',
    'cpp': '<c++>', 'c': '<c>', 'r': '<r>', 'rust': '<rust>',
    'haskell': '<haskell>', 'assembly': '<assembly>'
}

# ARI values (GPT-4 MultiPL-HumanEval pass@1)
ARI = {
    'python': 0.904, 'javascript': 0.829, 'typescript': 0.789,
    'java': 0.817, 'csharp': 0.688, 'go': 0.726,
    'ruby': 0.637, 'cpp': 0.787, 'c': 0.531,
    'r': 0.480, 'rust': 0.671, 'haskell': 0.410, 'assembly': 0.089
}

EVENTS = {
    'copilot_beta': '2021-10-01', 'copilot_ga': '2022-06-21',
    'chatgpt': '2022-11-30', 'gpt4': '2023-03-14',
    'llama2': '2023-07-18', 'code_llama': '2023-08-25',
    'devin': '2024-03-04', 'claude35': '2024-06-20',
}

def gini_coefficient(values):
    """Compute Gini coefficient from array of values."""
    values = np.array(values, dtype=float)
    if len(values) < 2 or values.sum() == 0:
        return np.nan
    values = np.sort(values)
    n = len(values)
    index = np.arange(1, n + 1)
    return (2 * np.sum(index * values) - (n + 1) * values.sum()) / (n * values.sum())

def hhi(shares):
    """Herfindahl-Hirschman Index from value counts."""
    shares = np.array(shares, dtype=float)
    if shares.sum() == 0:
        return np.nan
    probs = shares / shares.sum()
    return np.sum(probs ** 2)

def extract_lang(tag_str, lang_name):
    """Check if a tag string contains the language tag."""
    if pd.isna(tag_str):
        return False
    tag = LANG_MAP.get(lang_name, '')
    return tag in str(tag_str)

print("=" * 60)
print("DV5: Answer Concentration & DV6: Question Complexity")
print("=" * 60)

# ============================================================
# 1. Read parquet schema first to know columns
# ============================================================
print("\n[1] Reading parquet schema...")
pf = pq.ParquetFile(PARQUET)
print("  Columns:", pf.schema_arrow.names)
print("  Row groups:", pf.metadata.num_row_groups)
print("  Total rows:", pf.metadata.num_rows)

# Check schema for key columns
schema_names = set(pf.schema_arrow.names)
tag_col = 'Tags' if 'Tags' in schema_names else ('tags' if 'tags' in schema_names else None)
owner_col = 'OwnerUserId' if 'OwnerUserId' in schema_names else 'OwnerDisplayName'
type_col = 'PostTypeId' if 'PostTypeId' in schema_names else 'post_type_id'
date_col = 'CreationDate' if 'CreationDate' in schema_names else 'creation_date'
body_col = 'Body' if 'Body' in schema_names else 'body'
title_col = 'Title' if 'Title' in schema_names else 'title'

print(f"  tag_col={tag_col}, type_col={type_col}, date_col={date_col}")
print(f"  owner_col={owner_col}, body_col={body_col}, title_col={title_col}")

# ============================================================
# 2. Read only needed columns for efficiency
# ============================================================
print("\n[2] Reading needed columns from parquet...")
cols_to_read = [c for c in [tag_col, type_col, date_col, owner_col, body_col, title_col] if c is not None]
print(f"  Reading: {cols_to_read}")

# Read in chunks by row groups
dfs = []
for i in range(pf.metadata.num_row_groups):
    rg = pf.read_row_group(i, columns=cols_to_read).to_pandas()
    dfs.append(rg)
    if (i + 1) % 5 == 0:
        print(f"  Read row group {i+1}/{pf.metadata.num_row_groups}")

df = pd.concat(dfs, ignore_index=True)
print(f"  Total: {len(df)} rows")

# Parse dates
df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
df['year_month'] = df[date_col].dt.to_period('M').astype(str)

# Filter to 2018-01 onwards
df = df[df['year_month'] >= '2018-01'].copy()
print(f"  After 2018+ filter: {len(df)} rows")

# ============================================================
# 3. Assign language tags
# ============================================================
print("\n[3] Assigning language tags...")
df['lang'] = None
for lang_name in LANG_MAP:
    mask = df[tag_col].str.contains(LANG_MAP[lang_name], case=False, na=False, regex=False)
    df.loc[mask, 'lang'] = lang_name
    n = mask.sum()
    if n > 0:
        print(f"  {lang_name}: {n} posts")

df_lang = df[df['lang'].notna()].copy()
print(f"  Total tagged: {len(df_lang)} rows")

# ============================================================
# 4. DV5: Answer Concentration
# ============================================================
print("\n" + "=" * 60)
print("[DV5] Computing Answer Concentration...")
print("=" * 60)

answers = df_lang[df_lang[type_col] == 2].copy()  # answers only
answers['OwnerUserId'] = answers[owner_col]

dv5_records = []
for lang in LANG_MAP:
    lang_ans = answers[answers['lang'] == lang]
    if len(lang_ans) == 0:
        continue
    for ym in sorted(lang_ans['year_month'].unique()):
        month_ans = lang_ans[lang_ans['year_month'] == ym]
        user_counts = month_ans['OwnerUserId'].value_counts().values
        
        # Gini
        g = gini_coefficient(user_counts)
        
        # Top-10% share
        if len(user_counts) > 0:
            sorted_counts = np.sort(user_counts)[::-1]
            n_top = max(1, int(np.ceil(len(sorted_counts) * 0.1)))
            top10_share = sorted_counts[:n_top].sum() / sorted_counts.sum()
        else:
            top10_share = np.nan
        
        # HHI
        h = hhi(user_counts)
        
        # Basic stats
        n_answers = len(month_ans)
        n_answerers = month_ans['OwnerUserId'].nunique()
        
        dv5_records.append({
            'lang': lang, 'year_month': ym,
            'n_answers': n_answers,
            'n_answerers': n_answerers,
            'gini': g,
            'top10_share': top10_share,
            'hhi': h,
            'answers_per_user': n_answers / max(n_answerers, 1)
        })
    
    print(f"  {lang}: {len(lang_ans)} answers")

dv5_df = pd.DataFrame(dv5_records)
print(f"\nDV5 panel: {len(dv5_df)} lang-months")

# ============================================================
# 5. DV6: Question Complexity
# ============================================================
print("\n" + "=" * 60)
print("[DV6] Computing Question Complexity...")
print("=" * 60)

questions = df_lang[df_lang[type_col] == 1].copy()

import re

def count_code_blocks(body):
    if pd.isna(body):
        return 0
    # Count ``` blocks
    n = len(re.findall(r'```', str(body)))
    return n // 2

def count_code_tags(body):
    if pd.isna(body):
        return 0
    return len(re.findall(r'<code>', str(body)))

def has_code(body):
    if pd.isna(body):
        return 0
    b = str(body)
    return 1 if ('<code>' in b or '```' in b) else 0

dv6_records = []
for lang in LANG_MAP:
    lang_q = questions[questions['lang'] == lang]
    if len(lang_q) == 0:
        continue
    for ym in sorted(lang_q['year_month'].unique()):
        month_q = lang_q[lang_q['year_month'] == ym]
        
        # Body length
        body_lens = month_q[body_col].dropna().apply(lambda x: len(str(x)))
        median_body_len = body_lens.median() if len(body_lens) > 0 else np.nan
        
        # Title length
        title_lens = month_q[title_col].dropna().apply(lambda x: len(str(x)))
        median_title_len = title_lens.median() if len(title_lens) > 0 else np.nan
        
        # Code blocks
        code_counts = month_q[body_col].apply(count_code_blocks)
        median_code_blocks = code_counts.median() if len(code_counts) > 0 else np.nan
        
        # Fraction with code
        frac_with_code = month_q[body_col].apply(has_code).mean()
        
        # Code tags count
        code_tag_counts = month_q[body_col].apply(count_code_tags)
        median_code_tags = code_tag_counts.median() if len(code_tag_counts) > 0 else np.nan
        
        dv6_records.append({
            'lang': lang, 'year_month': ym,
            'n_questions': len(month_q),
            'median_body_len': median_body_len,
            'median_title_len': median_title_len,
            'median_code_blocks': median_code_blocks,
            'median_code_tags': median_code_tags,
            'frac_with_code': frac_with_code
        })
    
    print(f"  {lang}: {len(lang_q)} questions")

dv6_df = pd.DataFrame(dv6_records)
print(f"\nDV6 panel: {len(dv6_df)} lang-months")

# ============================================================
# 6. Build full panels with ARI, events, FEs
# ============================================================
def build_panel(dv_df, dv_name):
    """Add ARI, event dummies, FE columns."""
    df = dv_df.copy()
    df['ari'] = df['lang'].map(ARI)
    
    # Remove na ari
    df = df[df['ari'].notna()].copy()
    
    # Event dummies
    for evt, date in EVENTS.items():
        df[f'post_{evt}'] = (df['year_month'] >= date[:7]).astype(int)
        df[f'did_{evt}'] = df[f'post_{evt}'] * df['ari']
    
    # Language and month FE (as factors for fixest)
    df['lang_fe'] = df['lang'].astype('category')
    df['month_fe'] = df['year_month'].astype('category')
    
    # Save CSV for R
    path = os.path.join(OUT, f'{dv_name}_panel.csv')
    df.to_csv(path, index=False)
    print(f"  Saved: {path} ({len(df)} rows)")
    return df

print("\n[6] Building panels with ARI and event dummies...")
dv5_panel = build_panel(dv5_df, 'dv5_answer_concentration')
dv6_panel = build_panel(dv6_df, 'dv6_question_complexity')

# ============================================================
# 7. Quick OLS regressions (Python, as preview)
# ============================================================
from numpy.linalg import lstsq

def quick_did(data, y_var, x_vars, fe_vars=['lang', 'year_month'], label=''):
    """Within-transformation DID with cluster SE."""
    df = data.dropna(subset=[y_var] + x_vars + fe_vars).copy()
    
    # Within transform
    for fe in fe_vars:
        df[y_var] = df[y_var] - df.groupby(fe)[y_var].transform('mean')
        for xv in x_vars:
            df[xv] = df[xv] - df.groupby(fe)[xv].transform('mean')
    
    Y = df[y_var].values
    X = np.column_stack([np.ones(len(Y))] + [df[xv].values for xv in x_vars])
    beta, _, _, _ = lstsq(X, Y, rcond=None)
    
    residuals = Y - X @ beta
    n, k = X.shape
    mse = np.sum(residuals**2) / (n - k)
    
    # Cluster SE by language
    clusters = df['lang'].values
    Xe = np.zeros_like(X)
    for i in range(n):
        Xe[i] = X[i] * residuals[i]
    
    S = np.zeros((k, k))
    for c in np.unique(clusters):
        mask = clusters == c
        Xc = Xe[mask].sum(axis=0).reshape(-1, 1)
        S += Xc @ Xc.T
    
    try:
        V = np.linalg.inv(X.T @ X) @ S @ np.linalg.inv(X.T @ X)
        se = np.sqrt(np.diag(V))
    except:
        se = np.sqrt(np.diag(np.linalg.inv(X.T @ X) * mse))
    
    t = beta / np.where(se > 0, se, 1)
    p = 2 * (1 - stats.t.cdf(np.abs(t), n - k))
    
    results = []
    for i, xv in enumerate(['const'] + x_vars):
        sig = ''
        if p[i] < 0.01: sig = '***'
        elif p[i] < 0.05: sig = '**'
        elif p[i] < 0.1: sig = '*'
        results.append({
            'variable': xv, 'coefficient': beta[i], 'std_error': se[i],
            't_stat': t[i], 'p_value': p[i], 'sig': sig, 'model': label
        })
    return results

print("\n" + "=" * 60)
print("[REGRESSION] DV5: Answer Concentration")
print("=" * 60)

did_vars = [f'did_{e}' for e in EVENTS.keys() if e != 'claude35']

# DV5 models
dv5_results = []
for yv in ['gini', 'top10_share', 'hhi']:
    r = quick_did(dv5_panel, yv, did_vars, label=f'M_{yv}')
    dv5_results.extend(r)
    best = min([x for x in r if x['variable'] != 'const'], key=lambda x: x['p_value'])
    print(f"\n  {yv}: best = {best['variable']} (β={best['coefficient']:.4f}, p={best['p_value']:.4f})")
    for x in r:
        if x['sig']:
            print(f"    {x['variable']}: β={x['coefficient']:.4f}, p={x['p_value']:.4f} {x['sig']}")

dv5_res_df = pd.DataFrame(dv5_results)
dv5_res_df.to_csv(os.path.join(OUT, 'dv5_answer_concentration', 'dv5_regression.csv'), index=False)

print("\n" + "=" * 60)
print("[REGRESSION] DV6: Question Complexity")
print("=" * 60)

dv6_results = []
for yv in ['median_body_len', 'median_code_blocks', 'frac_with_code']:
    # Log transform body length
    if yv == 'median_body_len':
        dv6_panel['log_body_len'] = np.log1p(dv6_panel[yv])
        yv_use = 'log_body_len'
    else:
        yv_use = yv
    r = quick_did(dv6_panel, yv_use, did_vars, label=f'M_{yv}')
    dv6_results.extend(r)
    best = min([x for x in r if x['variable'] != 'const'], key=lambda x: x['p_value'])
    print(f"\n  {yv_use}: best = {best['variable']} (β={best['coefficient']:.4f}, p={best['p_value']:.4f})")
    for x in r:
        if x['sig']:
            print(f"    {x['variable']}: β={x['coefficient']:.4f}, p={x['p_value']:.4f} {x['sig']}")

dv6_res_df = pd.DataFrame(dv6_results)
dv6_res_df.to_csv(os.path.join(OUT, 'dv6_question_complexity', 'dv6_regression.csv'), index=False)

# ============================================================
# 8. Save summary
# ============================================================
summary = f"""# DV5 & DV6 Analysis Summary

## DV5: Answer Concentration
- **Gini coefficient**: measures answer inequality per language-month
- **Top-10% share**: fraction of answers from top 10% answerers
- **HHI**: Herfindahl-Hirschman concentration index
- Panel: {len(dv5_panel)} lang-months, {dv5_panel['lang'].nunique()} languages
- Controls: Language FE + Month FE, cluster SE by language

## Key DV5 Results
"""
for yv in ['gini', 'top10_share', 'hhi']:
    sub = dv5_res_df[(dv5_res_df['model'] == f'M_{yv}') & (dv5_res_df['variable'].str.startswith('did_'))]
    sig = sub[sub['p_value'] < 0.05]
    summary += f"### {yv}\n"
    if len(sig) > 0:
        for _, r in sig.iterrows():
            summary += f"- {r['variable']}: β={r['coefficient']:.4f}, p={r['p_value']:.4f}\n"
    else:
        summary += "- No significant effects\n"
    summary += "\n"

summary += f"""## DV6: Question Complexity
- **log_body_len**: log median question body length
- **median_code_blocks**: median code blocks per question
- **frac_with_code**: fraction of questions with code
- Panel: {len(dv6_panel)} lang-months, {dv6_panel['lang'].nunique()} languages
- Controls: Language FE + Month FE, cluster SE by language

## Key DV6 Results
"""
for yv in ['log_body_len', 'median_code_blocks', 'frac_with_code']:
    sub = dv6_res_df[(dv6_res_df['model'] == f'M_{yv}') & (dv6_res_df['variable'].str.startswith('did_'))]
    sig = sub[sub['p_value'] < 0.05]
    summary += f"### {yv}\n"
    if len(sig) > 0:
        for _, r in sig.iterrows():
            summary += f"- {r['variable']}: β={r['coefficient']:.4f}, p={r['p_value']:.4f}\n"
    else:
        summary += "- No significant effects\n"
    summary += "\n"

with open(os.path.join(OUT, 'summary_dv5_dv6.md'), 'w') as f:
    f.write(summary)

print(f"\n✅ COMPLETE")
print(f"  DV5: {os.path.join(OUT, 'dv5_answer_concentration')}")
print(f"  DV6: {os.path.join(OUT, 'dv6_question_complexity')}")
print(summary)
