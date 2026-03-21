#!/usr/bin/env python3
"""
results/paper_tables.py
========================
论文表格自动生成器
输出符合经济学期刊标准的LaTeX格式统计表

生成表格：
- Table 1: 描述统计表
- Table 2: 事件研究结果汇总
- Table 3: DID主回归结果
- Table 4: 异质性分析（语言×AI可替代性）

输出：results/tables/*.tex

用法:
    python results/paper_tables.py --features data/features/ --output results/tables/
"""

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


def sig_stars(pval: float) -> str:
    """根据p值返回显著性星号"""
    if pd.isna(pval):
        return ""
    if pval < 0.001:
        return "***"
    elif pval < 0.01:
        return "**"
    elif pval < 0.05:
        return "*"
    elif pval < 0.10:
        return "†"
    return ""


def format_coef(coef: float, se: float, pval: float = None, digits: int = 4) -> tuple:
    """返回（系数字符串, 标准误字符串）符合论文格式"""
    if pd.isna(coef):
        return ("", "")
    
    stars = sig_stars(pval) if pval is not None else ""
    coef_str = f"{coef:.{digits}f}{stars}"
    se_str = f"({se:.{digits}f})" if not pd.isna(se) else ""
    
    return coef_str, se_str


def latex_table_header(caption: str, label: str, columns: list, col_spec: str = None) -> str:
    """生成LaTeX表格头"""
    n_cols = len(columns)
    if col_spec is None:
        col_spec = "l" + "c" * (n_cols - 1)
    
    header = f"""\\begin{{table}}[htbp]
\\centering
\\caption{{{caption}}}
\\label{{{label}}}
\\begin{{threeparttable}}
\\begin{{tabular}}{{{col_spec}}}
\\hline\\hline
"""
    header += " & ".join(columns) + " \\\\\n"
    header += "\\hline\n"
    return header


def latex_table_footer(notes: str = "") -> str:
    """生成LaTeX表格尾"""
    footer = "\\hline\\hline\n"
    footer += "\\end{tabular}\n"
    if notes:
        footer += "\\begin{tablenotes}[flushleft]\n"
        footer += f"\\small\n\\item {notes}\n"
        footer += "\\end{tablenotes}\n"
    footer += "\\end{threeparttable}\n"
    footer += "\\end{table}\n"
    return footer


def generate_table1_descriptive(features_dir: Path, output_dir: Path):
    """
    Table 1: 描述统计
    Panel A: Stack Overflow
    Panel B: 对照社区比较
    """
    print("生成 Table 1: 描述统计...")
    
    weekly_path = features_dir / "weekly_stats.parquet"
    
    if not weekly_path.exists():
        print("  ⚠ 数据不足，生成占位表格")
        # 生成占位表格
        tex = latex_table_header(
            "Descriptive Statistics",
            "tab:descriptive",
            ["Variable", "Pre-AI\\n(2018-2021)", "Copilot Era\\n(2021-2022)",
             "Post-ChatGPT\\n(2022-2024)", "Diff (Post-Pre)"]
        )
        tex += "\\multicolumn{5}{l}{\\textit{Panel A: Stack Overflow}} \\\\\n"
        tex += "\\hline\n"
        
        variables = [
            ("Weekly questions (mean)", "", "", "", ""),
            ("\\quad Std. Dev.", "", "", "", ""),
            ("Question score (mean)", "", "", "", ""),
            ("Acceptance rate (\\%)", "", "", "", ""),
            ("Avg. answers per question", "", "", "", ""),
            ("Unique askers per week", "", "", "", ""),
            ("\\hline", "", "", "", ""),
            ("\\multicolumn{5}{l}{\\textit{Panel B: Control Communities}} \\\\", "", "", "", ""),
            ("\\hline", "", "", "", ""),
            ("Math SE: Weekly questions", "", "", "", ""),
            ("Super User: Weekly questions", "", "", "", ""),
            ("Server Fault: Weekly questions", "", "", "", ""),
        ]
        
        for row in variables:
            if row[0].startswith("\\"):
                tex += row[0] + "\n"
            else:
                tex += " & ".join(row) + " \\\\\n"
        
        notes = (
            "Notes: All statistics are weekly means unless noted. "
            "Pre-AI period: Jan 2018 -- Sep 2021. "
            "Copilot era: Oct 2021 -- Nov 2022. "
            "Post-ChatGPT: Dec 2022 -- Dec 2024. "
            "Diff column shows mean difference between Post-ChatGPT and Pre-AI periods. "
            "*** p$<$0.001, ** p$<$0.01, * p$<$0.05, †~p$<$0.10 (t-test for difference in means)."
        )
        tex += latex_table_footer(notes)
        
        output_path = output_dir / "table1_descriptive.tex"
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(tex)
        print(f"  ✓ 保存占位表格到 {output_path}")
        return
    
    # 如果有数据，生成真实表格
    df = pd.read_parquet(weekly_path)
    df["week_start"] = pd.to_datetime(df["week_start"])
    
    periods = {
        "Pre-AI (2018--2021)": ("2018-01-01", "2021-09-30"),
        "Copilot (2021--2022)": ("2021-10-01", "2022-11-29"),
        "Post-ChatGPT (2022+)": ("2022-11-30", "2025-01-01"),
    }
    
    # 统计变量
    stat_vars = {
        "Weekly questions": "question_count",
        "Question score": "avg_score",
        "Acceptance rate (\\%)": "accepted_rate",
        "Avg answers/question": "avg_answer_count",
        "Unique askers/week": "unique_askers",
    }
    
    rows = []
    
    for comm_label, comm_id in [("\\textit{Panel A: Stack Overflow}", "so"),
                                  ("\\textit{Panel B: Math Stack Exchange}", "mathse"),
                                  ("\\textit{Panel C: Super User}", "superuser")]:
        df_comm = df[df["community"] == comm_id] if "community" in df.columns else df
        
        rows.append([f"\\multicolumn{{5}}{{l}}{{{comm_label}}} \\\\ \\hline"])
        
        for var_label, var_col in stat_vars.items():
            if var_col not in df_comm.columns:
                continue
            
            period_stats = []
            pre_mean = None
            
            for period_name, (start, end) in periods.items():
                mask = (df_comm["week_start"] >= start) & (df_comm["week_start"] < end)
                vals = df_comm.loc[mask, var_col].dropna()
                
                if len(vals) == 0:
                    period_stats.append("--")
                    continue
                
                mean = vals.mean()
                
                if "\\%" in var_label:
                    period_stats.append(f"{mean*100:.1f}")
                else:
                    period_stats.append(f"{mean:.1f}")
                
                if pre_mean is None:
                    pre_mean = mean
            
            # 计算差值（Post vs Pre）
            if len(period_stats) >= 3:
                try:
                    post_mean = float(period_stats[-1].replace(",", ""))
                    pre_mean_val = float(period_stats[0].replace(",", ""))
                    diff = post_mean - pre_mean_val
                    pct_change = diff / pre_mean_val * 100 if pre_mean_val != 0 else 0
                    diff_str = f"{diff:+.1f} ({pct_change:+.1f}\\%)"
                except Exception:
                    diff_str = "--"
            else:
                diff_str = "--"
            
            rows.append([var_label] + period_stats + [diff_str])
    
    # 生成LaTeX
    columns = ["Variable"] + list(periods.keys()) + ["$\\Delta$ (Post$-$Pre)"]
    col_spec = "l" + "c" * (len(columns) - 1)
    
    tex = latex_table_header(
        "Descriptive Statistics: Stack Overflow and Control Communities",
        "tab:descriptive",
        columns,
        col_spec
    )
    
    for row in rows:
        if len(row) == 1 and row[0].startswith("\\multi"):
            tex += row[0] + "\n"
        else:
            tex += " & ".join(row) + " \\\\\n"
    
    notes = (
        "Notes: Weekly means for each period. "
        "Pre-AI: Jan 2018 -- Sep 2021. Copilot era: Oct 2021 -- Nov 2022. "
        "Post-ChatGPT: Dec 2022 -- Dec 2024. "
        "$\\Delta$ is Post-ChatGPT minus Pre-AI mean (percent change in parentheses)."
    )
    tex += latex_table_footer(notes)
    
    output_path = output_dir / "table1_descriptive.tex"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(tex)
    print(f"  ✓ 保存到 {output_path}")


def generate_table2_event_study(output_dir: Path):
    """
    Table 2: 事件研究结果汇总
    每个AI事件的CAR及显著性
    """
    print("生成 Table 2: 事件研究结果...")
    
    # 尝试加载已计算的结果
    result_path = Path("results/tables/event_study_results.csv")
    
    if result_path.exists():
        df_results = pd.read_csv(result_path)
    else:
        # 创建占位数据
        df_results = pd.DataFrame({
            "Event": [
                "GitHub Copilot Beta", "GitHub Copilot GA",
                "ChatGPT Launch", "GPT-4 Release",
                "Llama 2 Open Source", "Code Llama Release",
                "Devin Public Release", "Claude 3.5 Sonnet",
            ],
            "Date": [
                "2021-10", "2022-06", "2022-11", "2023-03",
                "2023-07", "2023-08", "2024-03", "2024-06",
            ],
            "CAR (log)": [""] * 8,
            "CAR (%)": [""] * 8,
            "SE": [""] * 8,
            "t-stat": [""] * 8,
        })
    
    columns = [
        "Event", "Date", "CAR (log scale)", "CAR (\\% change)", "Std. Error", "$t$-statistic"
    ]
    col_spec = "llcccc"
    
    tex = latex_table_header(
        "Event Study: Cumulative Abnormal Effects of AI Tool Releases on Stack Overflow Question Volume",
        "tab:event_study",
        columns,
        col_spec
    )
    
    # Panel headers
    tex += "\\multicolumn{6}{l}{\\textit{Estimation window: 52 weeks before event; Event window: ±12 weeks}} \\\\\n"
    tex += "\\hline\n"
    
    for _, row in df_results.iterrows():
        vals = [
            str(row.get("Event", "")),
            str(row.get("Date", "")),
            str(row.get("CAR (log)", "")),
            str(row.get("CAR (%)", "")),
            str(row.get("SE", "")),
            str(row.get("t-stat", "")),
        ]
        tex += " & ".join(vals) + " \\\\\n"
    
    notes = (
        "Notes: The dependent variable is log weekly question count. "
        "The estimation window uses OLS with time trend and seasonal controls (week-of-year dummies) "
        "to forecast the counterfactual. "
        "Standard errors use Newey-West correction (4 lags). "
        "CAR = Cumulative Abnormal Return over the 12-week post-event window. "
        "Percent change computed as $\\exp(\\text{CAR})-1$. "
        "*** $p<0.001$, ** $p<0.01$, * $p<0.05$, \\dag~$p<0.10$."
    )
    tex += latex_table_footer(notes)
    
    output_path = output_dir / "table2_event_study.tex"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(tex)
    print(f"  ✓ 保存到 {output_path}")


def generate_table3_did_main(output_dir: Path):
    """
    Table 3: DID主回归结果
    多列规格（逐步加控制变量和固定效应）
    """
    print("生成 Table 3: DID主回归结果...")
    
    columns = [
        "Dep. Var.: log(Questions)",
        "(1) OLS",
        "(2) +Language FE",
        "(3) +Time FE",
        "(4) 2WFE",
        "(5) Continuous",
    ]
    col_spec = "lccccc"
    
    tex = latex_table_header(
        "Effect of AI Tools on Stack Overflow Question Volume: Difference-in-Differences",
        "tab:did_main",
        columns,
        col_spec
    )
    
    # 占位回归结果行
    rows = [
        ("\\textbf{Main estimates}", "", "", "", "", ""),
        ("Treatment $\\times$ Post-ChatGPT", "", "", "", "", ""),
        ("\\quad (DiD coefficient)", "(--)", "(--)", "(--)", "(--)", ""),
        ("\\quad S.E.", "", "", "", "", ""),
        ("\\hline", "", "", "", "", ""),
        ("Treatment $\\times$ Post-Copilot", "", "", "", "", ""),
        ("\\quad (DiD coefficient)", "(--)", "(--)", "(--)", "(--)", ""),
        ("\\quad S.E.", "", "", "", "", ""),
        ("\\hline", "", "", "", "", ""),
        ("AI Replaceability $\\times$ Post-ChatGPT", "", "", "", "", ""),
        ("\\quad (continuous treatment)", "", "", "", "", "(--)",),
        ("\\quad S.E.", "", "", "", "", ""),
        ("\\hline", "", "", "", "", ""),
        ("\\textit{Controls}", "", "", "", "", ""),
        ("Language FE", "No", "Yes", "Yes", "Yes", "Yes"),
        ("Time (week) FE", "No", "No", "Yes", "Yes", "Yes"),
        ("Language-specific trend", "No", "No", "No", "Yes", "Yes"),
        ("\\hline", "", "", "", "", ""),
        ("Observations", "--", "--", "--", "--", "--"),
        ("$R^2$", "--", "--", "--", "--", "--"),
        ("Clusters (languages)", "--", "--", "--", "--", "--"),
    ]
    
    for row in rows:
        if row[0].startswith("\\hline"):
            tex += "\\hline\n"
        elif row[0].startswith("\\textbf") or row[0].startswith("\\textit"):
            tex += " & ".join(row) + " \\\\\n"
        else:
            tex += " & ".join(row) + " \\\\\n"
    
    notes = (
        "Notes: The dependent variable is the natural log of weekly question count per language. "
        "Treatment group: languages with AI replaceability index $>0.75$ (Python, JavaScript, Java, etc.). "
        "Control group: AI replaceability $<0.40$ (Assembly, COBOL, Fortran, etc.). "
        "Post-ChatGPT: 1 if week is after November 30, 2022. "
        "Standard errors clustered by programming language in parentheses. "
        "Column (5) uses AI replaceability index as continuous treatment intensity. "
        "*** $p<0.001$, ** $p<0.01$, * $p<0.05$, \\dag~$p<0.10$."
    )
    tex += latex_table_footer(notes)
    
    output_path = output_dir / "table3_did_main.tex"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(tex)
    print(f"  ✓ 保存到 {output_path}")


def generate_table4_heterogeneity(output_dir: Path):
    """
    Table 4: 异质性分析
    Panel A: 按语言类型
    Panel B: 按用户类型
    Panel C: 稳健性检验
    """
    print("生成 Table 4: 异质性分析...")
    
    columns = [
        "Subgroup",
        "DID Estimate",
        "Std. Error",
        "$t$-stat",
        "$N$",
        "Notes",
    ]
    col_spec = "lccccp{4cm}"
    
    tex = latex_table_header(
        "Heterogeneity Analysis: Effects by Language Type, User Type, and Robustness",
        "tab:heterogeneity",
        columns,
        col_spec
    )
    
    # Panel A
    tex += "\\multicolumn{6}{l}{\\textit{Panel A: By Programming Language Category}} \\\\ \\hline\n"
    
    panel_a_rows = [
        ("High AI replaceability ($>0.75$)", "--", "--", "--", "--", "Python, JS, Java, C\\#, etc."),
        ("Medium replaceability (0.40-0.75)", "--", "--", "--", "--", "C++, C, Rust, etc."),
        ("Low AI replaceability ($<0.40$)", "--", "--", "--", "--", "Assembly, COBOL, etc."),
        ("Coding-focused languages", "--", "--", "--", "--", "Top 5 by volume"),
        ("Web development languages", "--", "--", "--", "--", "HTML, CSS, JS, TS"),
        ("Systems languages", "--", "--", "--", "--", "C, C++, Rust, Go"),
    ]
    
    for row in panel_a_rows:
        tex += " & ".join(row) + " \\\\\n"
    
    tex += "\\hline\n"
    tex += "\\multicolumn{6}{l}{\\textit{Panel B: By User Reputation Tier}} \\\\ \\hline\n"
    
    panel_b_rows = [
        ("Questions by novice users ($<$100 rep.)", "--", "--", "--", "--", "Churn after 12 weeks"),
        ("Questions by regular users (100-1K rep.)", "--", "--", "--", "--", ""),
        ("Questions by experienced (1K-10K rep.)", "--", "--", "--", "--", ""),
        ("Questions by experts ($>$10K rep.)", "--", "--", "--", "--", ""),
    ]
    
    for row in panel_b_rows:
        tex += " & ".join(row) + " \\\\\n"
    
    tex += "\\hline\n"
    tex += "\\multicolumn{6}{l}{\\textit{Panel C: Robustness Checks}} \\\\ \\hline\n"
    
    panel_c_rows = [
        ("Placebo: Random event date (mean)", "--", "--", "--", "--", "500 permutations"),
        ("Exclude COVID period (2020-2021)", "--", "--", "--", "--", ""),
        ("Balanced panel only", "--", "--", "--", "--", "Languages active all years"),
        ("Math SE as outcome (falsification)", "--", "--", "--", "--", "Should be $\\approx 0$"),
        ("Server Fault as outcome (falsification)", "--", "--", "--", "--", "Should be $\\approx 0$"),
    ]
    
    for row in panel_c_rows:
        tex += " & ".join(row) + " \\\\\n"
    
    notes = (
        "Notes: All estimates from 2WFE DID specification (Column 4 of Table \\ref{tab:did_main}). "
        "Dependent variable: log weekly question count. "
        "Standard errors clustered by language. "
        "Placebo test uses 500 random draw dates from 2019-2022 as fake treatment dates; "
        "reported estimate is the mean across placebo estimates. "
        "*** $p<0.001$, ** $p<0.01$, * $p<0.05$."
    )
    tex += latex_table_footer(notes)
    
    output_path = output_dir / "table4_heterogeneity.tex"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(tex)
    print(f"  ✓ 保存到 {output_path}")


def generate_table5_survival(output_dir: Path):
    """
    Table 5: 用户生存分析（Cox模型）
    """
    print("生成 Table 5: 用户生存分析...")
    
    # 尝试加载Cox结果
    cox_path = Path("results/tables/cox_results.csv")
    survival_path = Path("results/tables/survival_summary.csv")
    
    columns = [
        "Variable",
        "Hazard Ratio",
        "95\\% CI",
        "Std. Error",
        "$z$-stat",
        "$p$-value",
    ]
    col_spec = "lccccc"
    
    tex = latex_table_header(
        "User Churn Analysis: Cox Proportional Hazards Model",
        "tab:cox_survival",
        columns,
        col_spec
    )
    
    tex += "\\multicolumn{6}{l}{\\textit{Panel A: Cox Model Coefficients}} \\\\ \\hline\n"
    
    if cox_path.exists():
        df_cox = pd.read_csv(cox_path, index_col=0)
        for var, row in df_cox.iterrows():
            hr = row.get("exp(coef)", np.nan)
            se = row.get("se(coef)", np.nan)
            pval = row.get("p", np.nan)
            stars = sig_stars(pval)
            
            hr_str = f"{hr:.3f}{stars}" if not pd.isna(hr) else "--"
            ci_low = row.get("exp(coef) lower 95%", np.nan)
            ci_high = row.get("exp(coef) upper 95%", np.nan)
            ci_str = f"[{ci_low:.3f}, {ci_high:.3f}]" if not pd.isna(ci_low) else "--"
            se_str = f"({se:.3f})" if not pd.isna(se) else "--"
            z_str = f"{row.get('z', np.nan):.2f}" if not pd.isna(row.get("z", np.nan)) else "--"
            p_str = f"{pval:.4f}" if not pd.isna(pval) else "--"
            
            tex += f"{var} & {hr_str} & {ci_str} & {se_str} & {z_str} & {p_str} \\\\\n"
    else:
        # 占位变量
        placeholder_vars = [
            "Post-ChatGPT cohort (0/1)",
            "Post-Copilot cohort (0/1)",
            "Log reputation",
            "Asker-only user (0/1)",
            "Answerer-only user (0/1)",
            "Tier: Novice (ref: Expert)",
            "Tier: Regular (ref: Expert)",
            "Tier: Experienced (ref: Expert)",
        ]
        for var in placeholder_vars:
            tex += f"{var} & -- & [--,--] & (--) & -- & -- \\\\\n"
    
    tex += "\\hline\n"
    tex += "\\multicolumn{6}{l}{\\textit{Panel B: Retention Rates by Reputation Tier}} \\\\ \\hline\n"
    tex += "Group & N & Churn Rate & 12-week ret. & 26-week ret. & 52-week ret. \\\\\n"
    tex += "\\hline\n"
    
    if survival_path.exists():
        df_surv = pd.read_csv(survival_path)
        for _, row in df_surv.iterrows():
            tex += (
                f"{row.get('Group', '--')} & {row.get('N', '--')} & "
                f"{row.get('Churn Rate (%)', '--')} & "
                f"{row.get('12-week Retention', '--')} & "
                f"{row.get('26-week Retention', '--')} & "
                f"{row.get('52-week Retention', '--')} \\\\\n"
            )
    else:
        for tier in ["Novice ($<$100)", "Regular (100-1K)", "Experienced (1K-10K)", "Expert ($>$10K)"]:
            tex += f"{tier} & -- & -- & -- & -- & -- \\\\\n"
    
    notes = (
        "Notes: Cox proportional hazards model. "
        "Outcome is time (weeks) until user churn, defined as 12+ consecutive weeks of inactivity. "
        "Hazard ratio $>1$ indicates higher churn risk. "
        "Post-ChatGPT cohort: registered on or after November 30, 2022. "
        "Concordance index reported in the text. "
        "*** $p<0.001$, ** $p<0.01$, * $p<0.05$."
    )
    tex += latex_table_footer(notes)
    
    output_path = output_dir / "table5_survival.tex"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(tex)
    print(f"  ✓ 保存到 {output_path}")


def generate_master_tex(output_dir: Path):
    """生成可直接编译的主.tex文件"""
    tex = r"""\documentclass[12pt]{article}
\usepackage{booktabs}
\usepackage{threeparttable}
\usepackage{geometry}
\usepackage{longtable}
\geometry{margin=1in}

\title{Generative AI Tools and the Stack Overflow Knowledge Ecosystem:\\
       Evidence from 2018--2026}
\author{[Authors]}
\date{\today}

\begin{document}
\maketitle

\listoftables

% Table 1: Descriptive Statistics
\input{table1_descriptive}
\clearpage

% Table 2: Event Study
\input{table2_event_study}
\clearpage

% Table 3: DID Main Results
\input{table3_did_main}
\clearpage

% Table 4: Heterogeneity
\input{table4_heterogeneity}
\clearpage

% Table 5: Survival Analysis
\input{table5_survival}
\clearpage

\end{document}
"""
    
    output_path = output_dir / "paper_tables_main.tex"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(tex)
    print(f"  ✓ 主LaTeX文件: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="生成论文表格")
    parser.add_argument("--features", default="data/features/", help="特征数据目录")
    parser.add_argument("--output", default="results/tables/", help="输出目录")
    
    args = parser.parse_args()
    
    features_dir = Path(args.features)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("=" * 60)
    print("论文表格生成器")
    print(f"输出目录: {output_dir}")
    print("=" * 60)
    
    generate_table1_descriptive(features_dir, output_dir)
    generate_table2_event_study(output_dir)
    generate_table3_did_main(output_dir)
    generate_table4_heterogeneity(output_dir)
    generate_table5_survival(output_dir)
    generate_master_tex(output_dir)
    
    print("\n" + "=" * 60)
    print("✅ 所有表格生成完成！")
    print(f"   输出目录: {output_dir}")
    print("   文件列表:")
    for f in sorted(output_dir.glob("*.tex")):
        print(f"     {f.name}")
    
    print("\n编译方式:")
    print(f"  cd {output_dir}")
    print("  pdflatex paper_tables_main.tex")


if __name__ == "__main__":
    main()
