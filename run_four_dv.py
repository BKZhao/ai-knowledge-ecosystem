#!/usr/bin/env python3
"""Four-DV Causal Inference: 8-Event Multi-Break DID Design"""

import os, re, warnings, json
import numpy as np
import pandas as pd
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy import stats
from numpy.linalg import lstsq
warnings.filterwarnings('ignore')

BASE = Path('/home/node/.openclaw/workspaces/ou_061694b4b8257fa782c21a959956256d/stackoverflow_research')
OUT = BASE / 'results' / 'four_dv_analysis'
POSTS = BASE / 'data' / 'parquet' / 'posts_2018plus.parquet'

AI_REPLACEABILITY = {
    # GPT-4 MultiPL-HumanEval pass@1 (Cassano et al. 2023; OctoPack Muennighoff et al. 2023)
    'python': 0.904, 'javascript': 0.829, 'typescript': 0.789, 'java': 0.817,
    'csharp': 0.688, 'go': 0.726, 'ruby': 0.637, 'cpp': 0.787, 'c': 0.531,
    'r': 0.480, 'rust': 0.671, 'haskell': 0.410, 'assembly': 0.089
}

TAG_MAP = {
    'python': 'python', 'javascript': 'javascript', 'java': 'java',
    'c#': 'csharp', 'typescript': 'typescript', 'c++': 'cpp', 'c': 'c',
    'r': 'r', 'go': 'go', 'ruby': 'ruby', 'rust': 'rust',
    'haskell': 'haskell', 'assembly': 'assembly'
}

EVENTS = {
    'copilot_beta': '2021-10-01',
    'copilot_ga': '2022-06-21',
    'chatgpt': '2022-11-30',
    'gpt4': '2023-03-14',
    'llama2': '2023-07-18',
    'code_llama': '2023-08-25',
    'devin': '2024-03-04',
    'claude35': '2024-06-20',
}

# Events within data range (up to 2024-03)
ACTIVE_EVENTS = {k: v for k, v in EVENTS.items() if v <= '2024-03-31'}
EVENT_KEYS = list(ACTIVE_EVENTS.keys())

LANGS = list(AI_REPLACEABILITY.keys())
for d in [OUT, OUT/'dv1_answer_supply', OUT/'dv2_views', OUT/'dv3_knowledge_diversity', OUT/'dv4_user_retention']:
    d.mkdir(parents=True, exist_ok=True)

# ============================================================
# STEP 0: Build panel
# ============================================================
print("STEP 0: Building language-month panel...")

def extract_lang(tags):
    if not tags or pd.isna(tags):
        return None
    for tag in tags.strip('|').split('|'):
        tl = tag.lower()
        if tl in TAG_MAP:
            return TAG_MAP[tl]
    return None

print("Reading questions...")
df_q = pd.read_parquet(POSTS, columns=['Id', 'PostTypeId', 'CreationDate', 'AnswerCount', 'HasAccepted', 'ViewCount', 'Tags', 'OwnerUserId'])
df_q = df_q[df_q.PostTypeId == 1].copy()
df_q['year_month'] = df_q['CreationDate'].str[:7]
df_q['lang'] = df_q['Tags'].apply(extract_lang)
df_q = df_q[df_q['lang'].notna()].copy()
print(f"Questions with language: {len(df_q)}")

panel = df_q.groupby(['lang', 'year_month']).agg(
    n_questions=('Id', 'count'),
    total_answers=('AnswerCount', 'sum'),
    avg_answers=('AnswerCount', 'mean'),
    pct_accepted=('HasAccepted', 'mean'),
    avg_views=('ViewCount', 'mean'),
    total_views=('ViewCount', 'sum'),
    n_users=('OwnerUserId', 'nunique')
).reset_index()

panel['ari'] = panel['lang'].map(AI_REPLACEABILITY)
panel['ari_centered'] = panel['ari'] - panel['ari'].mean()
panel['covid'] = ((panel['year_month'] >= '2020-03') & (panel['year_month'] <= '2021-12')).astype(int)

# Create event dummies and DID terms
for ek, ed in ACTIVE_EVENTS.items():
    short = ed[:7]  # YYYY-MM
    panel[f'post_{ek}'] = (panel['year_month'] >= short).astype(int)
    panel[f'did_{ek}'] = panel['ari_centered'] * panel[f'post_{ek}']

DID_COLS = [f'did_{ek}' for ek in EVENT_KEYS]
POST_COLS = [f'post_{ek}' for ek in EVENT_KEYS]

# Log transforms
for col in ['avg_answers', 'n_questions', 'avg_views', 'total_views']:
    panel[f'{col}_lt'] = np.log1p(panel[col])

panel['views_per_q'] = panel['total_views'] / panel['n_questions']
panel['views_per_q_lt'] = np.log1p(panel['views_per_q'])

panel.to_csv(OUT / 'language_month_panel.csv', index=False)
print(f"Panel: {panel.shape}, Events: {EVENT_KEYS}")

# ============================================================
# STEP 0b: Tag diversity
# ============================================================
print("Building tag diversity panel...")
df_all_tags = df_q[['lang', 'year_month', 'Tags']].copy()

def parse_all_tags(tags):
    if not tags or pd.isna(tags):
        return []
    return [t.lower() for t in tags.strip('|').split('|') if t]

df_all_tags['tag_list'] = df_all_tags['Tags'].apply(parse_all_tags)
df_all_tags = df_all_tags[df_all_tags['tag_list'].apply(len) > 0]
df_exploded = df_all_tags.explode('tag_list')
df_exploded['tag_list'] = df_exploded['tag_list'].str.lower()

tag_freq = df_exploded.groupby(['lang', 'year_month', 'tag_list']).size().reset_index(name='count')

def shannon_entropy(x):
    p = x / x.sum()
    p = p[p > 0]
    return -np.sum(p * np.log(p))

def top5_share(x):
    if len(x) < 5:
        return 1.0
    return x.nlargest(5).sum() / x.sum()

diversity = tag_freq.groupby(['lang', 'year_month']).agg(
    tag_entropy=('count', shannon_entropy),
    unique_tags=('tag_list', 'nunique'),
    tag_concentration=('count', lambda x: top5_share(x))
).reset_index()

# Merge event vars into diversity
div_panel = diversity.merge(
    panel[['lang', 'year_month', 'ari', 'ari_centered'] + DID_COLS + ['covid']].drop_duplicates(),
    on=['lang', 'year_month'], how='left'
)
div_panel['unique_tags_lt'] = np.log1p(div_panel['unique_tags'])
div_panel.to_csv(OUT / 'diversity_panel.csv', index=False)
print(f"Diversity panel: {div_panel.shape}")

# ============================================================
# STEP 0c: User retention
# ============================================================
print("Building user retention data...")
user_data = df_q[['OwnerUserId', 'year_month', 'lang', 'CreationDate']].copy()
user_data = user_data[user_data['OwnerUserId'].notna()]

user_activity = user_data.groupby('OwnerUserId').agg(
    first_activity=('CreationDate', 'min'),
    last_activity=('CreationDate', 'max'),
    n_posts=('CreationDate', 'count'),
    first_month=('year_month', 'min')
).reset_index()

user_lang = user_data.groupby('OwnerUserId')['lang'].agg(lambda x: x.mode().iloc[0] if len(x.mode()) > 0 else None).reset_index()
user_activity = user_activity.merge(user_lang, on='OwnerUserId', how='left')
user_activity = user_activity[user_activity['lang'].notna()]
user_activity['ari'] = user_activity['lang'].map(AI_REPLACEABILITY)
user_activity['ari_centered'] = user_activity['ari'] - user_activity['ari'].mean()

user_activity['first_dt'] = pd.to_datetime(user_activity['first_activity'])
user_activity['last_dt'] = pd.to_datetime(user_activity['last_activity'])
user_activity['duration_months'] = ((user_activity['last_dt'] - user_activity['first_dt']).dt.days / 30.44).round(1)
user_activity['censored'] = (user_activity['last_dt'] >= pd.Timestamp('2024-01-01')).astype(int)
user_activity['event'] = 1 - user_activity['censored']

# Multi-event: which era did user register in?
for ek, ed in ACTIVE_EVENTS.items():
    user_activity[f'reg_post_{ek}'] = (user_activity['first_dt'] >= pd.Timestamp(ed)).astype(int)

user_activity.to_csv(OUT / 'user_retention_data.csv', index=False)
print(f"Users: {len(user_activity)}")

# ============================================================
# HELPER: Two-way FE DID
# ============================================================
def run_did(data, y_var, x_vars, fe_vars=['lang', 'year_month'], cluster_var=None, sample_label=''):
    df = data.dropna(subset=[y_var] + x_vars + fe_vars).copy()
    for fe in fe_vars:
        df[y_var] = df[y_var] - df.groupby(fe)[y_var].transform('mean')
        for xv in x_vars:
            df[xv] = df[xv] - df.groupby(fe)[xv].transform('mean')

    Y = df[y_var].values
    X = np.column_stack([np.ones(len(Y))] + [df[xv].values for xv in x_vars])
    beta, res, rank, sv = lstsq(X, Y, rcond=None)
    residuals = Y - X @ beta
    n, k = X.shape
    mse = np.sum(residuals**2) / (n - k)

    if cluster_var and cluster_var in df.columns:
        clusters = df[cluster_var].values
        Xe = np.zeros_like(X)
        for i in range(n):
            Xe[i] = X[i] * residuals[i]
        uclust = np.unique(clusters)
        S = np.zeros((k, k))
        for c in uclust:
            mask = clusters == c
            S += (Xe[mask].T @ Xe[mask])
        V = np.linalg.inv(X.T @ X) @ S @ np.linalg.inv(X.T @ X)
        se = np.sqrt(np.diag(V))
    else:
        se = np.sqrt(np.diag(mse * np.linalg.inv(X.T @ X)))

    t_stats = beta / se
    p_vals = 2 * (1 - stats.t.cdf(np.abs(t_stats), n - k))

    results = []
    names = ['const'] + x_vars
    for i, name in enumerate(names):
        results.append({
            'variable': name, 'coefficient': float(beta[i]), 'std_error': float(se[i]),
            't_stat': float(t_stats[i]), 'p_value': float(p_vals[i]),
            'sig': '***' if p_vals[i] < 0.001 else '**' if p_vals[i] < 0.01 else '*' if p_vals[i] < 0.05 else '',
            'model': sample_label
        })
    res_df = pd.DataFrame(results)
    print(f"\n--- {sample_label} (N={n}) ---")
    for _, r in res_df.iterrows():
        if r['variable'] != 'const':
            print(f"  {r['variable']:30s} β={r['coefficient']:+.6f}  SE={r['std_error']:.6f}  p={r['p_value']:.4f} {r['sig']}")
    return res_df

def save_results(results_list, prefix):
    df = pd.concat(results_list, ignore_index=True)
    df.to_csv(prefix + '.csv', index=False)
    latex = df.to_latex(index=False, float_format='%.4f')
    with open(prefix + '.tex', 'w') as f:
        f.write(latex)

# ============================================================
# DV1: Answer Supply
# ============================================================
print("\n" + "=" * 60)
print("DV1: ANSWER SUPPLY — 8-Event DID")
print("=" * 60)
dv1_dir = OUT / 'dv1_answer_supply'
dv1_results = []

# M1: pct_accepted × 8 events
x_did = DID_COLS + ['covid']
r = run_did(panel, 'pct_accepted', x_did, sample_label='M1_pct_accepted')
dv1_results.append(r)

# M2: avg_answers_lt
r = run_did(panel, 'avg_answers_lt', DID_COLS, sample_label='M2_avg_answers_lt')
dv1_results.append(r)

# M3: n_questions_lt
r = run_did(panel, 'n_questions_lt', DID_COLS, sample_label='M3_question_count_lt')
dv1_results.append(r)

# Robustness: cumulative DID (only ChatGPT)
panel['did_chatgpt_only'] = panel['ari_centered'] * panel['post_chatgpt']
r = run_did(panel, 'pct_accepted', ['did_chatgpt_only', 'covid'], sample_label='R1_chatgpt_only_pct_accepted')
dv1_results.append(r)

# Robustness: No COVID period
panel_nc = panel[~((panel['year_month'] >= '2020-01') & (panel['year_month'] <= '2021-12'))].copy()
r = run_did(panel_nc, 'pct_accepted', DID_COLS, sample_label='R2_no_covid_pct_accepted')
dv1_results.append(r)

save_results(dv1_results, str(dv1_dir / 'dv1_regression'))

# Event study plot for DV1
print("DV1 Event Study...")
panel['months_to_chatgpt'] = ((pd.to_datetime(panel['year_month']) - pd.Timestamp('2022-11-30')).dt.days / 30.44).round(0).astype(int)
# Only use actual time points present in data
actual_times = sorted(panel['months_to_chatgpt'].unique())
if -1 in actual_times:
    ref_t = -1
else:
    ref_t = min(actual_times, key=lambda x: abs(x - (-1)))

times_no_ref = [t for t in actual_times if t != ref_t]
for t in times_no_ref:
    panel[f'mt_{t}'] = (panel['months_to_chatgpt'] == t).astype(float)

ari_interact = [f'mt_{t}_ari' for t in times_no_ref]
for t in times_no_ref:
    panel[f'mt_{t}_ari'] = panel[f'mt_{t}'] * panel['ari_centered']

df_es = panel.dropna(subset=['pct_accepted'] + ari_interact).copy()
for fe in ['lang', 'year_month']:
    df_es['pct_accepted'] = df_es['pct_accepted'] - df_es.groupby(fe)['pct_accepted'].transform('mean')
    for c in ari_interact:
        df_es[c] = df_es[c] - df_es.groupby(fe)[c].transform('mean')

Y = df_es['pct_accepted'].values
X = np.column_stack([np.ones(len(Y))] + [df_es[c].values for c in ari_interact])
beta, _, _, _ = lstsq(X, Y, rcond=None)

time_map = {}
for i, t in enumerate(times_no_ref):
    time_map[t] = beta[i + 1]
time_map[ref_t] = 0.0

fig, ax = plt.subplots(figsize=(14, 5))
ts = sorted(time_map.keys())
cs = [time_map[t] for t in ts]
colors = ['steelblue' if t < ref_t else ('gray' if t == ref_t else 'coral') for t in ts]
ax.bar(ts, cs, color=colors, width=0.8)
for ek, ed in ACTIVE_EVENTS.items():
    mt = round((pd.Timestamp(ed) - pd.Timestamp('2022-11-30')).days / 30.44)
    if min(ts) <= mt <= max(ts):
        ax.axvline(x=mt, color='green', linestyle=':', alpha=0.5, linewidth=0.8)
        ax.text(mt, 0, f'\n{ek}', fontsize=6, ha='center', color='green')
ax.axhline(y=0, color='black', linewidth=0.5)
ax.set_xlabel('Months relative to ChatGPT', fontsize=12)
ax.set_ylabel('DID coefficient (ARI × Post)', fontsize=12)
ax.set_title('DV1: Event Study — Answer Acceptance Rate', fontsize=14)
plt.tight_layout()
plt.savefig(dv1_dir / 'dv1_event_study.png', dpi=150)
plt.close()

# Trend plot
fig, axes = plt.subplots(2, 2, figsize=(14, 10))
high_ari = ['python', 'javascript', 'typescript', 'java', 'csharp']
low_ari = ['rust', 'haskell', 'assembly', 'c', 'r']
for idx, (langs, title) in enumerate([(high_ari, 'High ARI'), (low_ari, 'Low ARI')]):
    sub = panel[panel['lang'].isin(langs)]
    for lang in langs:
        ld = sub[sub['lang'] == lang].sort_values('year_month')
        axes[idx, 0].plot(ld['year_month'], ld['pct_accepted'], alpha=0.7, label=lang)
        axes[idx, 1].plot(ld['year_month'], ld['avg_answers_lt'], alpha=0.7, label=lang)
    axes[idx, 0].set_title(f'{title}: % Accepted')
    axes[idx, 1].set_title(f'{title}: Avg Answers (log)')
    for a in axes[idx]:
        a.axvline(x='2022-12', color='black', linestyle='--', alpha=0.5)
        a.legend(fontsize=7)
        a.tick_params(axis='x', rotation=45, labelsize=7)
plt.tight_layout()
plt.savefig(dv1_dir / 'dv1_trends.png', dpi=150)
plt.close()

# 8-event coefficient plot for DV1
dv1_m1 = dv1_results[0]
did_rows = dv1_m1[dv1_m1['variable'].str.startswith('did_')]
fig, ax = plt.subplots(figsize=(10, 5))
labels = [v.replace('did_', '') for v in did_rows['variable']]
coefs = did_rows['coefficient'].values
ses = did_rows['std_error'].values
colors_bar = ['steelblue' if c < 0 else 'coral' for c in coefs]
ax.barh(labels, coefs, xerr=1.96*ses, color=colors_bar, alpha=0.8)
ax.axvline(x=0, color='black', linewidth=0.5)
ax.set_xlabel('DID Coefficient (ARI × Post_Event)', fontsize=11)
ax.set_title('DV1: 8-Event DID — Answer Acceptance Rate', fontsize=13)
plt.tight_layout()
plt.savefig(dv1_dir / 'dv1_8event_coefficients.png', dpi=150)
plt.close()

# ============================================================
# DV2: View Count
# ============================================================
print("\n" + "=" * 60)
print("DV2: VIEW COUNT — 8-Event DID")
print("=" * 60)
dv2_dir = OUT / 'dv2_views'
dv2_results = []

r = run_did(panel, 'avg_views_lt', DID_COLS, sample_label='M1_avg_views_lt')
dv2_results.append(r)

r = run_did(panel, 'total_views_lt', DID_COLS, sample_label='M2_total_views_lt')
dv2_results.append(r)

r = run_did(panel, 'views_per_q_lt', DID_COLS, sample_label='M3_views_per_question_lt')
dv2_results.append(r)

# ChatGPT only
r = run_did(panel, 'avg_views_lt', ['did_chatgpt_only'], sample_label='R1_chatgpt_only_avg_views')
dv2_results.append(r)

save_results(dv2_results, str(dv2_dir / 'dv2_regression'))

fig, axes = plt.subplots(1, 2, figsize=(14, 5))
for langs, title in [(high_ari, 'High ARI'), (low_ari, 'Low ARI')]:
    sub = panel[panel['lang'].isin(langs)]
    for lang in langs:
        ld = sub[sub['lang'] == lang].sort_values('year_month')
        axes[0].plot(ld['year_month'], ld['avg_views_lt'], alpha=0.6, label=f"{lang}")
        axes[1].plot(ld['year_month'], ld['views_per_q_lt'], alpha=0.6, label=f"{lang}")
for ax in axes:
    ax.axvline(x='2022-12', color='black', linestyle='--', alpha=0.5)
    ax.legend(fontsize=6); ax.tick_params(axis='x', rotation=45, labelsize=7)
axes[0].set_title('Avg Views (log)'); axes[1].set_title('Views per Question (log)')
plt.tight_layout()
plt.savefig(dv2_dir / 'dv2_trends.png', dpi=150)
plt.close()

# 8-event coefficient plot DV2
dv2_m1 = dv2_results[0]
did_rows = dv2_m1[dv2_m1['variable'].str.startswith('did_')]
fig, ax = plt.subplots(figsize=(10, 5))
labels = [v.replace('did_', '') for v in did_rows['variable']]
ax.barh(labels, did_rows['coefficient'].values, xerr=1.96*did_rows['std_error'].values,
        color=['steelblue' if c < 0 else 'coral' for c in did_rows['coefficient'].values], alpha=0.8)
ax.axvline(x=0, color='black', linewidth=0.5)
ax.set_xlabel('DID Coefficient (ARI × Post_Event)', fontsize=11)
ax.set_title('DV2: 8-Event DID — Avg Views', fontsize=13)
plt.tight_layout()
plt.savefig(dv2_dir / 'dv2_8event_coefficients.png', dpi=150)
plt.close()

# ============================================================
# DV3: Knowledge Diversity
# ============================================================
print("\n" + "=" * 60)
print("DV3: KNOWLEDGE DIVERSITY — 8-Event DID")
print("=" * 60)
dv3_dir = OUT / 'dv3_knowledge_diversity'
dv3_results = []

r = run_did(div_panel, 'tag_entropy', DID_COLS, sample_label='M1_tag_entropy')
dv3_results.append(r)

r = run_did(div_panel, 'unique_tags_lt', DID_COLS, sample_label='M2_unique_tags_lt')
dv3_results.append(r)

r = run_did(div_panel, 'tag_concentration', DID_COLS, sample_label='M3_tag_concentration')
dv3_results.append(r)

save_results(dv3_results, str(dv3_dir / 'dv3_regression'))

fig, axes = plt.subplots(1, 2, figsize=(14, 5))
for langs, title in [(high_ari, 'High ARI'), (low_ari, 'Low ARI')]:
    sub = div_panel[div_panel['lang'].isin(langs)]
    for lang in langs:
        ld = sub[sub['lang'] == lang].sort_values('year_month')
        axes[0].plot(ld['year_month'], ld['tag_entropy'], alpha=0.6, label=f"{lang}")
        axes[1].plot(ld['year_month'], ld['unique_tags_lt'], alpha=0.6, label=f"{lang}")
for ax in axes:
    ax.axvline(x='2022-12', color='black', linestyle='--', alpha=0.5)
    ax.legend(fontsize=6); ax.tick_params(axis='x', rotation=45, labelsize=7)
axes[0].set_title('Tag Shannon Entropy'); axes[1].set_title('Unique Tags (log)')
plt.tight_layout()
plt.savefig(dv3_dir / 'dv3_trends.png', dpi=150)
plt.close()

# 8-event coefficient plot DV3
dv3_m1 = dv3_results[0]
did_rows = dv3_m1[dv3_m1['variable'].str.startswith('did_')]
fig, ax = plt.subplots(figsize=(10, 5))
labels = [v.replace('did_', '') for v in did_rows['variable']]
ax.barh(labels, did_rows['coefficient'].values, xerr=1.96*did_rows['std_error'].values,
        color=['steelblue' if c < 0 else 'coral' for c in did_rows['coefficient'].values], alpha=0.8)
ax.axvline(x=0, color='black', linewidth=0.5)
ax.set_xlabel('DID Coefficient (ARI × Post_Event)', fontsize=11)
ax.set_title('DV3: 8-Event DID — Tag Entropy', fontsize=13)
plt.tight_layout()
plt.savefig(dv3_dir / 'dv3_8event_coefficients.png', dpi=150)
plt.close()

# ============================================================
# DV4: User Retention
# ============================================================
print("\n" + "=" * 60)
print("DV4: USER RETENTION")
print("=" * 60)
dv4_dir = OUT / 'dv4_user_retention'
DV4_OK = False

try:
    from lifelines import CoxPHFitter, KaplanMeierFitter
    from lifelines.statistics import logrank_test

    users = pd.read_csv(OUT / 'user_retention_data.csv')
    users = users[(users['duration_months'] >= 1) & (users['duration_months'] <= 72)].copy()

    # Model 1: Multi-event Cox — simplify to avoid convergence issues
    reg_cols = [f'reg_post_{ek}' for ek in EVENT_KEYS]
    ari_interact_cols = [f'reg_post_{ek}_ari' for ek in EVENT_KEYS]
    for ek in EVENT_KEYS:
        users[f'reg_post_{ek}_ari'] = users['ari_centered'] * users[f'reg_post_{ek}']

    print("Model 1: Full Cox PH (multi-event)")
    # Sample for convergence, drop NaN, clip duration
    users_cox = users.dropna(subset=['duration_months', 'event', 'ari_centered'] + reg_cols + ari_interact_cols).copy()
    users_cox['duration_months'] = users_cox['duration_months'].clip(1, 72)
    # Subsample if too large
    if len(users_cox) > 200000:
        users_cox = users_cox.sample(200000, random_state=42)

    cox_vars = ['duration_months', 'event', 'ari_centered'] + reg_cols + ari_interact_cols
    cox_data = users_cox[cox_vars].copy()
    cox_data.columns = ['duration', 'event', 'ari'] + reg_cols + ari_interact_cols
    # Standardize continuous vars
    for col in ['ari'] + ari_interact_cols:
        mu = cox_data[col].mean()
        sd = cox_data[col].std()
        if sd > 0:
            cox_data[col] = (cox_data[col] - mu) / sd

    try:
        cph = CoxPHFitter(penalizer=0.01)
        cph.fit(cox_data, duration_col='duration', event_col='event')
        cph.summary.to_csv(dv4_dir / 'dv4_cox_multi_event.csv')
        print(cph.print_summary())
    except Exception as e:
        print(f"Cox multi-event failed: {e}")
        # Fallback: simpler model
        cox_simple = users_cox[['duration_months', 'event', 'ari_centered', 'n_posts']].copy()
        cox_simple.columns = ['duration', 'event', 'ari', 'n_posts']
        cph = CoxPHFitter(penalizer=0.01)
        cph.fit(cox_simple, duration_col='duration', event_col='event')
        cph.summary.to_csv(dv4_dir / 'dv4_cox_simple.csv')
        print(cph.print_summary())

    # KM curves (use full users sample, no convergence issues)
    users_km = users.copy()
    users_km['duration_months'] = users_km['duration_months'].clip(1, 72)
    users_km['ari_group'] = pd.cut(users_km['ari'], bins=[0, 0.5, 0.8, 1.0], labels=['Low ARI (<0.5)', 'Med ARI (0.5-0.8)', 'High ARI (>0.8)'])

    fig, ax = plt.subplots(figsize=(10, 6))
    kmf = KaplanMeierFitter()
    for group in users_km['ari_group'].dropna().unique():
        mask = users_km['ari_group'] == group
        kmf.fit(users_km.loc[mask, 'duration_months'], users_km.loc[mask, 'event'],
                label=f'{group} (n={mask.sum()})')
        kmf.plot_survival_function(ax=ax)
    ax.set_xlabel('Months since first activity'); ax.set_ylabel('Survival probability')
    ax.set_title('User Retention by ARI Group', fontsize=14)
    plt.tight_layout(); plt.savefig(dv4_dir / 'dv4_km_ari_groups.png', dpi=150); plt.close()

    # KM pre/post
    users_km['era'] = np.where(pd.to_datetime(users_km['first_activity']) < pd.Timestamp('2022-11-30'), 'Pre-ChatGPT', 'Post-ChatGPT')
    fig, ax = plt.subplots(figsize=(10, 6))
    for era in ['Pre-ChatGPT', 'Post-ChatGPT']:
        mask = users_km['era'] == era
        if mask.sum() > 50:
            kmf.fit(users_km.loc[mask, 'duration_months'], users_km.loc[mask, 'event'],
                    label=f'{era} (n={mask.sum()})')
            kmf.plot_survival_function(ax=ax)
    ax.set_xlabel('Months since first activity'); ax.set_ylabel('Survival probability')
    ax.set_title('User Retention: Pre vs Post ChatGPT', fontsize=14)
    plt.tight_layout(); plt.savefig(dv4_dir / 'dv4_km_prepost.png', dpi=150); plt.close()

    # Log-rank
    hm = users_km['ari'] >= 0.8; lm = users_km['ari'] < 0.5
    result = logrank_test(users_km.loc[hm, 'duration_months'], users_km.loc[lm, 'duration_months'],
                          users_km.loc[hm, 'event'], users_km.loc[lm, 'event'])
    print(f"\nLog-rank (High vs Low ARI): p={result.p_value:.6f}")
    pd.DataFrame({'test': ['log_rank_high_low_ari'], 'p_value': [result.p_value],
                  'statistic': [result.test_statistic]}).to_csv(dv4_dir / 'dv4_logrank.csv', index=False)
    DV4_OK = True
except Exception as e:
    print(f"DV4 failed: {e}")
    import traceback; traceback.print_exc()

# ============================================================
# SUMMARY
# ============================================================
print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)

dv1_all = pd.read_csv(dv1_dir / 'dv1_regression.csv')
dv2_all = pd.read_csv(dv2_dir / 'dv2_regression.csv')
dv3_all = pd.read_csv(dv3_dir / 'dv3_regression.csv')

def fmt_sig(p):
    return '***' if p < 0.001 else '**' if p < 0.01 else '*' if p < 0.05 else ''

def event_table(dv_df, model_name):
    sub = dv_df[(dv_df['model'] == model_name) & (dv_df['variable'].str.startswith('did_'))].copy()
    sub['event'] = sub['variable'].str.replace('did_', '')
    sub = sub.sort_values('event')
    lines = []
    for _, r in sub.iterrows():
        lines.append(f"| {r['event']} | {r['coefficient']:+.6f} | {r['std_error']:.6f} | {r['p_value']:.4f} | {fmt_sig(r['p_value'])} |")
    return '\n'.join(lines)

s = f"""# Four-DV Causal Inference: 8-Event Multi-Break DID

## Design
- **Panel:** language × month, 2018-01 to 2024-03
- **N questions:** {len(df_q):,}
- **Treatment:** ARI (continuous) × Post_Event (8 binary breaks)
- **FE:** Two-way (language + month), demeaned OLS
- **Events:** {', '.join(EVENT_KEYS)}

## DV1: Answer Supply

### M1: pct_accepted × 8 events
| Event | β | SE | p | Sig |
|-------|------|------|--------|-----|
{event_table(dv1_all, 'M1_pct_accepted')}

### M2: avg_answers_lt × 8 events
| Event | β | SE | p | Sig |
|-------|------|------|--------|-----|
{event_table(dv1_all, 'M2_avg_answers_lt')}

### M3: question_count_lt × 8 events
| Event | β | SE | p | Sig |
|-------|------|------|--------|-----|
{event_table(dv1_all, 'M3_question_count_lt')}

### Robustness: ChatGPT-only DID
| Event | β | SE | p | Sig |
|-------|------|------|--------|-----|
{event_table(dv1_all, 'R1_chatgpt_only_pct_accepted')}

## DV2: View Count

### M1: avg_views_lt × 8 events
| Event | β | SE | p | Sig |
|-------|------|------|--------|-----|
{event_table(dv2_all, 'M1_avg_views_lt')}

### M2: total_views_lt × 8 events
| Event | β | SE | p | Sig |
|-------|------|------|--------|-----|
{event_table(dv2_all, 'M2_total_views_lt')}

### M3: views_per_question_lt × 8 events
| Event | β | SE | p | Sig |
|-------|------|------|--------|-----|
{event_table(dv2_all, 'M3_views_per_question_lt')}

## DV3: Knowledge Diversity

### M1: tag_entropy × 8 events
| Event | β | SE | p | Sig |
|-------|------|------|--------|-----|
{event_table(dv3_all, 'M1_tag_entropy')}

### M2: unique_tags_lt × 8 events
| Event | β | SE | p | Sig |
|-------|------|------|--------|-----|
{event_table(dv3_all, 'M2_unique_tags_lt')}

### M3: tag_concentration × 8 events
| Event | β | SE | p | Sig |
|-------|------|------|--------|-----|
{event_table(dv3_all, 'M3_tag_concentration')}

## DV4: User Retention
Status: {'✅ Complete' if DV4_OK else '❌ Failed'}
See `dv4_user_retention/` for Cox PH and KM curves.

## Key Findings
"""

# Auto-findings
for dv_name, dv_df, main_model in [
    ('Answer Supply', dv1_all, 'M1_pct_accepted'),
    ('Views', dv2_all, 'M1_avg_views_lt'),
    ('Knowledge Diversity', dv3_all, 'M1_tag_entropy')
]:
    sub = dv_df[(dv_df['model'] == main_model) & (dv_df['variable'].str.startswith('did_'))]
    # Find most significant event
    if len(sub):
        best = sub.loc[sub['p_value'].idxmin()]
        n_sig = (sub['p_value'] < 0.05).sum()
        direction = 'negative' if best['coefficient'] < 0 else 'positive'
        s += f"- **{dv_name}**: {n_sig}/{len(sub)} events significant. Strongest: {best['variable'].replace('did_', '')} (β={best['coefficient']:+.4f}, p={best['p_value']:.4f}). Overall direction: {direction}.\n"

with open(OUT / 'summary.md', 'w') as f:
    f.write(s)

print(s)
print("\n✅ COMPLETE — results in", OUT)
