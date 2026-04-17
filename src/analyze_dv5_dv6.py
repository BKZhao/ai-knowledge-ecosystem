#!/usr/bin/env python3
# =============================================================================
# analyze_dv5_dv6.py — Panel regression & visualization for DV5/DV6
# =============================================================================
# Uses linearmodels.PanelOLS for two-way fixed effects (language + month)
# Produces: regression CSVs, LaTeX tables, event study plots, trend plots
# =============================================================================

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

try:
    from linearmodels.panel import PanelOLS, PooledOLS
    from linearmodels.iv.model import IV2SLS
    HAS_LINEARMODELS = True
except ImportError:
    HAS_LINEARMODELS = False
    print("linearmodels not available, using statsmodels OLS")

from statsmodels.formula.api import ols
import statsmodels.api as sm

# ─── Paths ────────────────────────────────────────────────────────────────────
PROJ = Path("/home/node/.openclaw/workspaces/ou_061694b4b8257fa782c21a959956256d/stackoverflow_research")
DV5_DIR = PROJ / "results/four_dv_analysis/dv5_answer_concentration"
DV6_DIR = PROJ / "results/four_dv_analysis/dv6_question_complexity"
PROC = PROJ / "data/processed"
DV5_DIR.mkdir(parents=True, exist_ok=True)
DV6_DIR.mkdir(parents=True, exist_ok=True)

# ─── Constants ────────────────────────────────────────────────────────────────
ARI = {
    'python': 0.904, 'javascript': 0.829, 'typescript': 0.789,
    'java': 0.817, 'csharp': 0.688, 'go': 0.726,
    'ruby': 0.637, 'cpp': 0.787, 'c': 0.531,
    'r': 0.480, 'rust': 0.671, 'haskell': 0.410, 'assembly': 0.089
}

EVENTS = [
    ('copilot_beta', '2021-10-01', 'Copilot β'),
    ('copilot_ga',   '2022-06-21', 'Copilot GA'),
    ('chatgpt',      '2022-11-30', 'ChatGPT'),
    ('gpt4',         '2023-03-14', 'GPT-4'),
    ('llama2',       '2023-07-18', 'Llama 2'),
    ('code_llama',   '2023-08-25', 'Code Llama'),
    ('devin',        '2024-03-04', 'Devin'),
    ('claude35',     '2024-06-20', 'Claude 3.5'),
]

COLORS = {'high': '#E74C3C', 'low': '#3498DB', 'chatgpt': '#E74C3C'}

def stars(p):
    if p < 0.001: return '***'
    if p < 0.01:  return '**'
    if p < 0.05:  return '*'
    if p < 0.1:   return '†'
    return ''

def build_panel(df_raw, dv_col):
    """Build panel dataframe with ARI, event dummies, and interactions."""
    df = df_raw.copy()
    df['month_dt'] = pd.to_datetime(df['month'] + '-01')
    df['ari'] = df['lang'].map(ARI)
    df['ari_c'] = df['ari'] - np.mean(list(ARI.values()))
    df = df.dropna(subset=[dv_col, 'ari'])
    
    # Event dummies and DID interactions
    for ev_short, ev_date, _ in EVENTS:
        dt = pd.to_datetime(ev_date)
        df[f'post_{ev_short}'] = (df['month_dt'] >= dt).astype(float)
        df[f'did_{ev_short}'] = df['ari_c'] * df[f'post_{ev_short}']
    
    return df

def run_twfe_regression(panel, dv_col, label, out_dir):
    """Two-way FE regression: DV ~ post_event*ARI + lang_FE + month_FE."""
    print(f"\n{'='*60}")
    print(f"  Regression: {label} ~ {dv_col}")
    print(f"{'='*60}")
    
    # Build dummies for FE manually (absorb via demeaning)
    post_cols = [f'post_{e[0]}' for e in EVENTS]
    did_cols  = [f'did_{e[0]}' for e in EVENTS]
    
    # Demean by language and month (within estimator)
    df = panel.copy()
    df = df.set_index(['lang', 'month'])
    all_vars = [dv_col] + post_cols + did_cols
    df_vars = df[all_vars].copy()
    
    # Language mean
    lang_means = df_vars.groupby(level='lang').transform('mean')
    # Month mean
    month_means = df_vars.groupby(level='month').transform('mean')
    # Overall mean
    overall_means = df_vars.mean()
    
    # Demeaned (two-way within transformation)
    df_dm = df_vars - lang_means - month_means + overall_means
    
    y = df_dm[dv_col]
    X = df_dm[post_cols + did_cols]
    X = sm.add_constant(X)
    
    model = sm.OLS(y, X).fit(cov_type='HC3')
    
    # Extract results
    coefs = pd.DataFrame({
        'term': model.params.index,
        'estimate': model.params.values,
        'std_error': model.bse.values,
        'statistic': model.tvalues.values,
        'p_value': model.pvalues.values,
    })
    coefs['stars'] = coefs['p_value'].apply(stars)
    coefs['ci_lo'] = coefs['estimate'] - 1.96 * coefs['std_error']
    coefs['ci_hi'] = coefs['estimate'] + 1.96 * coefs['std_error']
    
    print(f"  R² = {model.rsquared:.4f}, N = {model.nobs:.0f}")
    did_rows = coefs[coefs['term'].str.startswith('did_')]
    for _, row in did_rows.iterrows():
        print(f"  {row['term']}: β={row['estimate']:.4f} ({row['std_error']:.4f}) {row['stars']}")
    
    # Save CSV
    coefs.to_csv(out_dir / f"{label}_regression.csv", index=False)
    
    # LaTeX table
    _write_latex(coefs, model, dv_col, label, out_dir)
    
    return model, coefs

def _write_latex(coefs, model, dv_col, label, out_dir):
    lines = [
        r"\begin{table}[htbp]\centering",
        rf"\caption{{{label}: Multi-breakpoint DID (Two-Way FE)}}",
        r"\begin{tabular}{lcc}",
        r"\toprule",
        rf" & \multicolumn{{2}}{{c}}{{{dv_col}}} \\",
        r"\cmidrule(l){2-3}",
        r" & Post Event & ARI $\times$ Post \\",
        r"\midrule",
    ]
    for ev_short, ev_date, ev_label in EVENTS:
        post_r = coefs[coefs['term'] == f'post_{ev_short}']
        did_r  = coefs[coefs['term'] == f'did_{ev_short}']
        if len(post_r) == 0 and len(did_r) == 0:
            continue
        ev_name = ev_label.replace('β', r'$\beta$')
        lines.append(rf"\textit{{{ev_name}}} & & \\")
        
        if len(post_r) > 0:
            b, se, st = post_r.iloc[0][['estimate','std_error','stars']]
            lines.append(rf" & {b:.4f}{st} & \\")
            lines.append(rf" & ({se:.4f}) & \\")
        
        if len(did_r) > 0:
            b, se, st = did_r.iloc[0][['estimate','std_error','stars']]
            lines.append(rf" &  & {b:.4f}{st} \\")
            lines.append(rf" &  & ({se:.4f}) \\")
    
    lines += [
        r"\midrule",
        r"Language FE & \multicolumn{2}{c}{Yes} \\",
        r"Month FE    & \multicolumn{2}{c}{Yes} \\",
        rf"$R^2$ & \multicolumn{{2}}{{c}}{{{model.rsquared:.4f}}} \\",
        rf"$N$   & \multicolumn{{2}}{{c}}{{{int(model.nobs)}}} \\",
        r"\bottomrule",
        r"\end{tabular}",
        r"{\footnotesize $^{***}p<0.001$, $^{**}p<0.01$, $^{*}p<0.05$, $^{\dagger}p<0.10$. HC3 robust SE.}",
        r"\end{table}",
    ]
    (out_dir / f"{label}_regression.tex").write_text('\n'.join(lines))

def plot_event_study(panel, coefs, dv_col, label, out_dir):
    """Event study: DV relative to ChatGPT launch."""
    ref_date = pd.to_datetime('2022-11-30')
    df = panel.copy()
    df['rel_month'] = ((df['month_dt'] - ref_date) / pd.Timedelta(days=30.44)).round().astype(int)
    df = df[(df['rel_month'] >= -12) & (df['rel_month'] <= 15)]
    
    # Simple group means by relative month × ARI group
    df['ari_group'] = np.where(df['ari'] >= 0.7, 'High ARI', 'Low ARI')
    
    group_avg = df.groupby(['rel_month', 'ari_group'])[dv_col].median().reset_index()
    group_avg.columns = ['rel_month', 'ari_group', 'val']
    
    # Normalize to -1 month
    for grp in group_avg['ari_group'].unique():
        mask = group_avg['ari_group'] == grp
        ref_val = group_avg.loc[mask & (group_avg['rel_month'] == -1), 'val']
        if len(ref_val) > 0:
            group_avg.loc[mask, 'val'] = group_avg.loc[mask, 'val'] - ref_val.iloc[0]
    
    fig, ax = plt.subplots(figsize=(10, 5))
    for grp, color in [('High ARI', COLORS['high']), ('Low ARI', COLORS['low'])]:
        sub = group_avg[group_avg['ari_group'] == grp].sort_values('rel_month')
        ax.plot(sub['rel_month'], sub['val'], color=color, linewidth=2, label=grp, marker='o', markersize=4)
    
    ax.axvline(x=0, color='red', linestyle='--', alpha=0.7, linewidth=1.5)
    ax.axvline(x=-0.5, color='red', linestyle='-', alpha=0.3, linewidth=0.5)
    ax.axhline(y=0, color='gray', linestyle='--', alpha=0.5, linewidth=1)
    ax.set_xlabel('Months Relative to ChatGPT Launch', fontsize=12)
    ax.set_ylabel(f'Change in {dv_col} (vs t=-1)', fontsize=12)
    ax.set_title(f'Event Study: {label}\n(ChatGPT, Nov 2022)', fontsize=13, fontweight='bold')
    ax.legend(loc='upper left', fontsize=10)
    ax.set_xticks(range(-12, 16, 3))
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    fig.savefig(out_dir / f"{label}_event_study.png", dpi=200, bbox_inches='tight')
    plt.close()
    print(f"  Saved event study plot")

def plot_trends(panel, dv_col, label, out_dir):
    """Monthly trend lines by ARI group."""
    df = panel.copy()
    df['ari_group'] = np.where(df['ari'] >= 0.7, 'High ARI (≥0.7)', 'Low ARI (<0.7)')
    
    group_avg = df.groupby(['month_dt', 'ari_group'])[dv_col].median().reset_index()
    
    chatgpt_date = pd.to_datetime('2022-11-30')
    
    fig, ax = plt.subplots(figsize=(12, 5))
    for grp, color in [('High ARI (≥0.7)', COLORS['high']), ('Low ARI (<0.7)', COLORS['low'])]:
        sub = group_avg[group_avg['ari_group'] == grp].sort_values('month_dt')
        ax.plot(sub['month_dt'], sub[dv_col], color=color, linewidth=2, label=grp, alpha=0.9)
        # Smoothed
        ax.plot(sub['month_dt'], sub[dv_col].rolling(3, center=True).mean(),
                color=color, linewidth=1, linestyle='--', alpha=0.5)
    
    ax.axvline(x=chatgpt_date, color='red', linestyle='--', alpha=0.7, linewidth=1.5)
    ax.text(chatgpt_date, ax.get_ylim()[1] * 0.95, ' ChatGPT', color='red', fontsize=9, va='top')
    
    # Add other event lines (lighter)
    for ev_short, ev_date, ev_label in EVENTS:
        dt = pd.to_datetime(ev_date)
        if ev_short != 'chatgpt':
            ax.axvline(x=dt, color='gray', linestyle=':', alpha=0.4, linewidth=0.8)
    
    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    ax.set_xlabel('', fontsize=11)
    ax.set_ylabel(dv_col, fontsize=11)
    ax.set_title(f'{label}: Trends by ARI Group (2018–2024)', fontsize=13, fontweight='bold')
    ax.legend(loc='best', fontsize=10)
    ax.grid(True, alpha=0.25)
    plt.tight_layout()
    fig.savefig(out_dir / f"{label}_trends.png", dpi=200, bbox_inches='tight')
    plt.close()
    print(f"  Saved trends plot")

def heterogeneity_analysis(panel, dv_col, label):
    """Does the ChatGPT effect differ by ARI quartile?"""
    df = panel.copy()
    df['ari_q'] = pd.qcut(df['ari'], q=3, labels=['low', 'mid', 'high'])
    
    results = {}
    for grp in ['low', 'high']:
        sub = df[df['ari_q'] == grp].copy()
        post_cols = [f'post_{e[0]}' for e in EVENTS]
        
        # Demean within lang and month
        sub = sub.set_index(['lang', 'month'])
        vars_dm = sub[[dv_col] + post_cols]
        lang_m = vars_dm.groupby(level='lang').transform('mean')
        month_m = vars_dm.groupby(level='month').transform('mean')
        dm = vars_dm - lang_m - month_m + vars_dm.mean()
        
        y = dm[dv_col]
        X = sm.add_constant(dm[post_cols])
        try:
            fit = sm.OLS(y, X).fit(cov_type='HC3')
            chatgpt_idx = [i for i, c in enumerate(fit.params.index) if c == 'post_chatgpt']
            if chatgpt_idx:
                b = fit.params.iloc[chatgpt_idx[0]]
                p = fit.pvalues.iloc[chatgpt_idx[0]]
                results[grp] = (b, p)
                print(f"  Hetero {label} [{grp} ARI]: ChatGPT β={b:.4f} (p={p:.4f}) {stars(p)}")
        except Exception as e:
            print(f"  Hetero {label} [{grp}]: failed - {e}")
    
    return results

# =============================================================================
# Main Analysis
# =============================================================================

def main():
    print("Loading data...")
    dv5_raw = pd.read_csv(PROC / "dv5_answer_concentration.csv")
    dv6_raw = pd.read_csv(PROC / "dv6_question_complexity.csv")
    
    print(f"DV5: {len(dv5_raw)} rows, {dv5_raw['lang'].nunique()} languages")
    print(f"DV6: {len(dv6_raw)} rows, {dv6_raw['lang'].nunique()} languages")
    
    all_results = {}
    
    # ── DV5: Questioner Concentration ─────────────────────────────────────────
    print("\n" + "="*60)
    print("DV5: QUESTIONER CONCENTRATION")
    print("="*60)
    
    dv5_metrics = ['gini', 'top10_share', 'hhi']
    dv5_fits = {}
    
    for metric in dv5_metrics:
        panel = build_panel(dv5_raw, metric)
        label = f"dv5_{metric}"
        
        model, coefs = run_twfe_regression(panel, metric, label, DV5_DIR)
        dv5_fits[metric] = (model, coefs)
        all_results[label] = {'model': model, 'coefs': coefs}
        
        plot_event_study(panel, coefs, metric, label, DV5_DIR)
        plot_trends(panel, metric, label, DV5_DIR)
        
        hetero = heterogeneity_analysis(panel, metric, label)
        all_results[label]['hetero'] = hetero
    
    # ── DV6: Question Complexity ───────────────────────────────────────────────
    print("\n" + "="*60)
    print("DV6: QUESTION COMPLEXITY")
    print("="*60)
    
    dv6_metrics = ['median_body_length', 'median_code_blocks', 'frac_with_code']
    dv6_fits = {}
    
    for metric in dv6_metrics:
        panel = build_panel(dv6_raw, metric)
        label = f"dv6_{metric}"
        
        model, coefs = run_twfe_regression(panel, metric, label, DV6_DIR)
        dv6_fits[metric] = (model, coefs)
        all_results[label] = {'model': model, 'coefs': coefs}
        
        plot_event_study(panel, coefs, metric, label, DV6_DIR)
        plot_trends(panel, metric, label, DV6_DIR)
        
        hetero = heterogeneity_analysis(panel, metric, label)
        all_results[label]['hetero'] = hetero
    
    # ── Summary Report ─────────────────────────────────────────────────────────
    print("\nWriting summary...")
    _write_summary(dv5_raw, dv6_raw, dv5_fits, dv6_fits, all_results)
    
    print("\n=== All DV5/DV6 analyses complete! ===")
    print(f"DV5 results: {DV5_DIR}")
    print(f"DV6 results: {DV6_DIR}")

def _write_summary(dv5_raw, dv6_raw, dv5_fits, dv6_fits, all_results):
    from datetime import datetime
    
    lines = [
        "# DV5 & DV6 Analysis Summary",
        "",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "## DV5: Questioner Concentration (回答集中度代理)",
        "",
        "> Note: Since the parquet data lacks ParentId to link answerers to language tags,",
        "> DV5 uses **questioner concentration** (Gini/HHI/Top10% of question-asking activity",
        "> per user per language per month) as a proxy for community contribution inequality.",
        "",
        f"- Languages: {dv5_raw['lang'].nunique()}",
        f"- Months: {dv5_raw['month'].nunique()} ({dv5_raw['month'].min()} to {dv5_raw['month'].max()})",
        f"- Observations: {len(dv5_raw)}",
        "",
        "### Regression Results (ChatGPT DID: ARI × Post-ChatGPT)",
        "",
        "| Metric | β (DID) | SE | p | Sig |",
        "|--------|---------|-----|---|-----|",
    ]
    
    for metric, (model, coefs) in dv5_fits.items():
        did_r = coefs[coefs['term'] == 'did_chatgpt']
        if len(did_r) > 0:
            row = did_r.iloc[0]
            lines.append(f"| {metric} | {row['estimate']:.4f} | {row['std_error']:.4f} | {row['p_value']:.4f} | {row['stars']} |")
    
    lines += [
        "",
        "### Descriptive Statistics",
        "",
    ]
    
    # Add descriptive stats
    for metric in ['gini', 'top10_share', 'hhi']:
        if metric in dv5_raw.columns:
            m = dv5_raw[metric].describe()
            lines.append(f"**{metric}**: mean={m['mean']:.4f}, sd={m['std']:.4f}, min={m['min']:.4f}, max={m['max']:.4f}")
    
    lines += [
        "",
        "## DV6: Question Complexity (问题复杂度)",
        "",
        f"- Languages: {dv6_raw['lang'].nunique()}",
        f"- Months: {dv6_raw['month'].nunique()} ({dv6_raw['month'].min()} to {dv6_raw['month'].max()})",
        f"- Observations: {len(dv6_raw)}",
        "",
        "### Regression Results (ChatGPT DID: ARI × Post-ChatGPT)",
        "",
        "| Metric | β (DID) | SE | p | Sig |",
        "|--------|---------|-----|---|-----|",
    ]
    
    for metric, (model, coefs) in dv6_fits.items():
        did_r = coefs[coefs['term'] == 'did_chatgpt']
        if len(did_r) > 0:
            row = did_r.iloc[0]
            lines.append(f"| {metric} | {row['estimate']:.4f} | {row['std_error']:.4f} | {row['p_value']:.4f} | {row['stars']} |")
    
    lines += [
        "",
        "### Descriptive Statistics",
        "",
    ]
    for metric in ['median_body_length', 'median_code_blocks', 'frac_with_code']:
        if metric in dv6_raw.columns:
            m = dv6_raw[metric].describe()
            lines.append(f"**{metric}**: mean={m['mean']:.2f}, sd={m['std']:.2f}, min={m['min']:.2f}, max={m['max']:.2f}")
    
    lines += [
        "",
        "## Heterogeneity Analysis (High vs Low ARI languages)",
        "",
    ]
    for key, res in all_results.items():
        if 'hetero' in res:
            lines.append(f"**{key}**:")
            for grp, (b, p) in res['hetero'].items():
                lines.append(f"  - {grp} ARI: β={b:.4f}, p={p:.4f} {stars(p)}")
    
    lines += [
        "",
        "## Files Generated",
        "",
        "### DV5 Output",
    ]
    for f in sorted(DV5_DIR.glob("*")):
        lines.append(f"- `{f.name}`")
    
    lines += ["", "### DV6 Output"]
    for f in sorted(DV6_DIR.glob("*")):
        lines.append(f"- `{f.name}`")
    
    summary_path = PROJ / "results/four_dv_analysis/summary_dv5_dv6.md"
    summary_path.write_text('\n'.join(lines))
    print(f"  Summary written to {summary_path}")

if __name__ == '__main__':
    main()
