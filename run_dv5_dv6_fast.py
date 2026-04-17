"""DV5/DV6 - Optimized: stream by row groups, avoid loading all 21.9M into memory at once for processing."""
import pyarrow.parquet as pq
import pandas as pd
import numpy as np
from collections import defaultdict
from scipy import stats
import re, os, time, json, warnings
warnings.filterwarnings('ignore')

OUT = 'results/four_dv_analysis'
PARQUET = 'data/parquet/posts_2018plus.parquet'
os.makedirs(f'{OUT}/dv5_answer_concentration', exist_ok=True)
os.makedirs(f'{OUT}/dv6_question_complexity', exist_ok=True)

# Pipe-delimited tag matching (fast)
LANG_PATTERNS = {
    'python': 'python', 'javascript': 'javascript', 'typescript': 'typescript',
    'java': 'java', 'csharp': 'c#', 'go': 'go', 'ruby': 'ruby',
    'cpp': 'c++', 'c': '<c>', 'r': '<r>', 'rust': 'rust',
    'haskell': 'haskell', 'assembly': 'assembly'
}

ARI = {'python':0.904,'javascript':0.829,'typescript':0.789,'java':0.817,'csharp':0.688,
       'go':0.726,'ruby':0.637,'cpp':0.787,'c':0.531,'r':0.480,'rust':0.671,'haskell':0.410,'assembly':0.089}

EVENTS = {'copilot_beta':'2021-10','copilot_ga':'2022-06','chatgpt':'2022-11','gpt4':'2023-03',
           'llama2':'2023-07','code_llama':'2023-08','devin':'2024-03','claude35':'2024-06'}

COLS = ['Tags','PostTypeId','CreationDate','OwnerUserId','BodyLength','CodeBlockCount']

def assign_lang(tags_str):
    if not tags_str or tags_str == '':
        return None
    tags = set(tags_str.strip('|').split('|'))
    # Priority: check less ambiguous first (c, r have short tags)
    if 'c++' in tags: return 'cpp'
    if 'c#' in tags: return 'csharp'
    if 'python' in tags: return 'python'
    if 'javascript' in tags: return 'javascript'
    if 'typescript' in tags: return 'typescript'
    if 'java' in tags: return 'java'
    if 'go' in tags: return 'go'
    if 'ruby' in tags: return 'ruby'
    if 'rust' in tags: return 'rust'
    if 'haskell' in tags: return 'haskell'
    if 'assembly' in tags: return 'assembly'
    # 'c' and 'r' are ambiguous - check they are exact single-letter tags
    if tags == {'c'}: return 'c'
    if tags == {'r'}: return 'r'
    return None

print("=" * 60)
print("DV5 & DV6 - Stream Processing")
print("=" * 60)
t0 = time.time()

pf = pq.ParquetFile(PARQUET)

# Accumulators: {lang: {ym: {metric: values}}}
dv5_acc = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))  # lang->ym->metric->values
dv6_acc = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))

# Month filter
MIN_MONTH = '2018-01'
MAX_MONTH = '2024-03' if pf.metadata.num_rows < 30000000 else None

for i in range(pf.metadata.num_row_groups):
    t1 = time.time()
    rg = pf.read_row_group(i, columns=COLS).to_pandas()
    rg['CreationDate'] = pd.to_datetime(rg['CreationDate'], errors='coerce')
    rg = rg[(rg['CreationDate'] >= MIN_MONTH)]
    if MAX_MONTH:
        rg = rg[rg['CreationDate'] <= MAX_MONTH + '-31']
    rg['ym'] = rg['CreationDate'].dt.strftime('%Y-%m')
    rg['lang'] = rg['Tags'].apply(assign_lang)
    rg = rg[rg['lang'].notna()]
    
    if len(rg) == 0:
        continue
    
    # DV5: answers
    ans = rg[rg['PostTypeId'] == 2]
    for _, row in ans.iterrows():
        dv5_acc[row['lang']][row['ym']]['owner'].append(row['OwnerUserId'])
    
    # DV6: questions
    qs = rg[rg['PostTypeId'] == 1]
    for _, row in qs.iterrows():
        dv6_acc[row['lang']][row['ym']]['body_len'].append(row.get('BodyLength', 0) or 0)
        dv6_acc[row['lang']][row['ym']]['code_blocks'].append(row.get('CodeBlockCount', 0) or 0)
    
    if (i+1) % 20 == 0:
        n_lang = sum(len(v) for v in dv5_acc.values())
        print(f"  RG {i+1}/{pf.metadata.num_row_groups}: {len(rg)} tagged rows, {n_lang} lang-months, {time.time()-t1:.1f}s/rg")

print(f"\nScan complete in {time.time()-t0:.0f}s")

# ============================================================
# Aggregate DV5
# ============================================================
print("\nAggregating DV5...")
dv5_records = []
for lang in dv5_acc:
    for ym in dv5_acc[lang]:
        owners = dv5_acc[lang][ym]['owner']
        if len(owners) < 2:
            continue
        counts = pd.Series(owners).value_counts().values
        n = len(counts)
        total = counts.sum()
        
        # Gini
        sorted_c = np.sort(counts)
        idx = np.arange(1, n+1)
        gini = (2*np.sum(idx*sorted_c) - (n+1)*total) / (n*total) if total > 0 else 0
        
        # Top-10%
        n_top = max(1, int(np.ceil(n*0.1)))
        top10 = np.sort(counts)[::-1][:n_top].sum() / total if total > 0 else 0
        
        # HHI
        probs = counts / total
        hhi = np.sum(probs**2)
        
        dv5_records.append({
            'lang': lang, 'year_month': ym, 'n_answers': total,
            'n_answerers': n, 'gini': gini, 'top10_share': top10, 'hhi': hhi,
            'answers_per_user': total/n
        })

dv5_df = pd.DataFrame(dv5_records)
print(f"  DV5: {len(dv5_df)} lang-months, {dv5_df['lang'].nunique()} languages")

# ============================================================
# Aggregate DV6
# ============================================================
print("Aggregating DV6...")
dv6_records = []
for lang in dv6_acc:
    for ym in dv6_acc[lang]:
        bl = np.array(dv6_acc[lang][ym]['body_len'], dtype=float)
        cb = np.array(dv6_acc[lang][ym]['code_blocks'], dtype=float)
        if len(bl) < 5:
            continue
        dv6_records.append({
            'lang': lang, 'year_month': ym, 'n_questions': len(bl),
            'median_body_len': np.median(bl),
            'log_body_len': np.log1p(np.median(bl)),
            'median_code_blocks': np.median(cb),
            'frac_with_code': np.mean(cb > 0)
        })

dv6_df = pd.DataFrame(dv6_records)
print(f"  DV6: {len(dv6_df)} lang-months, {dv6_df['lang'].nunique()} languages")

# ============================================================
# Build panels & regressions
# ============================================================
from numpy.linalg import lstsq

def build_panel(df, name):
    df = df.copy()
    df['ari'] = df['lang'].map(ARI)
    df = df[df['ari'].notna()].copy()
    for evt, date in EVENTS.items():
        df[f'post_{evt}'] = (df['year_month'] >= date).astype(int)
        df[f'did_{evt}'] = df[f'post_{evt}'] * df['ari']
    path = f'{OUT}/{name}_panel.csv'
    df.to_csv(path, index=False)
    return df

def run_did(data, y_var, x_vars, fe_vars=['lang','year_month'], label=''):
    df = data.dropna(subset=[y_var]+x_vars+fe_vars).copy()
    for fe in fe_vars:
        df[y_var] = df[y_var] - df.groupby(fe)[y_var].transform('mean')
        for xv in x_vars:
            df[xv] = df[xv] - df.groupby(fe)[xv].transform('mean')
    Y = df[y_var].values
    X = np.column_stack([np.ones(len(Y))]+[df[xv].values for xv in x_vars])
    beta, _, _, _ = lstsq(X, Y, rcond=None)
    res = Y - X@beta
    n, k = X.shape
    mse = np.sum(res**2)/(n-k)
    # Cluster SE
    clusters = df['lang'].values
    S = np.zeros((k,k))
    for c in np.unique(clusters):
        m = clusters==c
        Xc = (X[m]*res[m,None]).sum(axis=0).reshape(-1,1)
        S += Xc@Xc.T
    try: V = np.linalg.inv(X.T@X)@S@np.linalg.inv(X.T@X)
    except: V = np.linalg.inv(X.T@X)*mse
    se = np.sqrt(np.diag(V))
    t = beta/np.where(se>0,se,1)
    p = 2*(1-stats.t.cdf(np.abs(t),n-k))
    results = []
    for i,xv in enumerate(['const']+x_vars):
        sig = '***' if p[i]<0.01 else ('**' if p[i]<0.05 else ('*' if p[i]<0.1 else ''))
        results.append({'variable':xv,'coefficient':beta[i],'std_error':se[i],'t_stat':t[i],'p_value':p[i],'sig':sig,'model':label})
    return pd.DataFrame(results)

did_vars = [f'did_{e}' for e in EVENTS if e != 'claude35']

print("\n--- DV5 Regressions ---")
dv5_panel = build_panel(dv5_df, 'dv5_answer_concentration')
dv5_all = []
for yv in ['gini','top10_share','hhi']:
    r = run_did(dv5_panel, yv, did_vars, label=f'M_{yv}')
    dv5_all.append(r)
    sig_rows = r[(r['variable']!='const') & (r['p_value']<0.1)]
    print(f"\n  {yv}:")
    for _,x in sig_rows.iterrows():
        print(f"    {x['variable']}: β={x['coefficient']:.4f}, p={x['p_value']:.4f} {x['sig']}")
    if len(sig_rows)==0: print(f"    No significant effects")
dv5_all = pd.concat(dv5_all)
dv5_all.to_csv(f'{OUT}/dv5_answer_concentration/dv5_regression.csv', index=False)

print("\n--- DV6 Regressions ---")
dv6_panel = build_panel(dv6_df, 'dv6_question_complexity')
dv6_all = []
for yv in ['log_body_len','median_code_blocks','frac_with_code']:
    r = run_did(dv6_panel, yv, did_vars, label=f'M_{yv}')
    dv6_all.append(r)
    sig_rows = r[(r['variable']!='const') & (r['p_value']<0.1)]
    print(f"\n  {yv}:")
    for _,x in sig_rows.iterrows():
        print(f"    {x['variable']}: β={x['coefficient']:.4f}, p={x['p_value']:.4f} {x['sig']}")
    if len(sig_rows)==0: print(f"    No significant effects")
dv6_all = pd.concat(dv6_all)
dv6_all.to_csv(f'{OUT}/dv6_question_complexity/dv6_regression.csv', index=False)

# TeX output
def to_tex(res_df, path):
    tex = "\\begin{tabular}{lrrrrll}\n\\toprule\nvariable & coefficient & std_error & t_stat & p_value & sig & model \\\\\n\\midrule\n"
    for _,r in res_df.iterrows():
        tex += f"{r['variable']} & {r['coefficient']:.4f} & {r['std_error']:.4f} & {r['t_stat']:.4f} & {r['p_value']:.4f} & {r['sig']} & {r['model']} \\\\\n"
    tex += "\\bottomrule\n\\end{tabular}\n"
    with open(path,'w') as f: f.write(tex)

to_tex(dv5_all, f'{OUT}/dv5_answer_concentration/dv5_regression.tex')
to_tex(dv6_all, f'{OUT}/dv6_question_complexity/dv6_regression.tex')

# Summary
s = "# DV5 & DV6 Summary\n\n## DV5: Answer Concentration\n"
s += f"Panel: {len(dv5_panel)} lang-months\nControls: Language FE + Month FE, cluster SE by language\n\n"
for yv in ['gini','top10_share','hhi']:
    sub = dv5_all[(dv5_all['model']==f'M_{yv}')&(dv5_all['variable'].str.startswith('did_'))]
    sig = sub[sub['p_value']<0.05]
    s += f"### {yv}\n"
    if len(sig)>0:
        for _,r in sig.iterrows(): s += f"- {r['variable']}: β={r['coefficient']:.4f}, p={r['p_value']:.4f}\n"
    else: s += "- No significant effects\n"
    s += "\n"

s += "## DV6: Question Complexity\n"
s += f"Panel: {len(dv6_panel)} lang-months\nControls: Language FE + Month FE, cluster SE by language\n\n"
for yv in ['log_body_len','median_code_blocks','frac_with_code']:
    sub = dv6_all[(dv6_all['model']==f'M_{yv}')&(dv6_all['variable'].str.startswith('did_'))]
    sig = sub[sub['p_value']<0.05]
    s += f"### {yv}\n"
    if len(sig)>0:
        for _,r in sig.iterrows(): s += f"- {r['variable']}: β={r['coefficient']:.4f}, p={r['p_value']:.4f}\n"
    else: s += "- No significant effects\n"
    s += "\n"

with open(f'{OUT}/summary_dv5_dv6.md','w') as f: f.write(s)

print(f"\n✅ DONE in {time.time()-t0:.0f}s")
print(s)
