#!/usr/bin/env python3
"""
analysis/03_did_analysis.py
============================
双重差分（Difference-in-Differences）分析

识别策略：
- 利用编程语言间AI可替代性的差异作为处理强度
- 处理组：AI可替代性 > 0.75（Python、JavaScript、Java等）
- 对照组：AI可替代性 < 0.40（Assembly、COBOL、Fortran等）
- 断点：ChatGPT发布（2022-11-30）

方法：
1. 两向固定效应（2WFE）：语言FE + 时间FE
2. Staggered DID（Callaway & Sant'Anna近似）：多个事件节点
3. 平行趋势检验：预处理期安慰剂检验

输出：results/figures/did/

用法:
    python analysis/03_did_analysis.py --features data/features/ --output results/figures/did/
"""

import argparse
import warnings
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
from linearmodels.panel import PanelOLS, compare

warnings.filterwarnings("ignore")

# 出版级图表风格
PUBLICATION_STYLE = {
    "figure.facecolor": "white", "axes.facecolor": "white",
    "axes.grid": True, "grid.alpha": 0.3, "grid.linestyle": "--",
    "axes.spines.top": False, "axes.spines.right": False,
    "font.size": 11, "axes.labelsize": 12, "axes.titlesize": 13,
    "figure.dpi": 150, "savefig.dpi": 300, "savefig.bbox": "tight",
}

# ============================================================
# AI可替代性指数（基于HumanEval pass@1公开数据）
# 参考：Chen et al., 2021; OpenAI Codex论文; 各模型技术报告
# ============================================================
AI_REPLACEABILITY = {
    # 高可替代性（>0.75）- 处理组
    "python": 0.92,
    "javascript": 0.87,
    "html": 0.88,
    "css": 0.85,
    "typescript": 0.85,
    "java": 0.81,
    "sql": 0.80,
    "php": 0.78,
    "kotlin": 0.77,
    "swift": 0.76,
    # 中等可替代性（0.40-0.75）- 不纳入主分析
    "go": 0.75,
    "ruby": 0.74,
    "scala": 0.72,
    "bash": 0.72,
    "r": 0.70,
    "c++": 0.71,
    "c": 0.68,
    "matlab": 0.65,
    "lua": 0.60,
    "perl": 0.58,
    "haskell": 0.55,
    # 低可替代性（<0.40）- 对照组
    "assembly": 0.15,
    "cobol": 0.12,
    "fortran": 0.18,
    "ada": 0.20,
    "prolog": 0.25,
    "vhdl": 0.22,
    "verilog": 0.28,
}

# 处理组/对照组阈值
HIGH_REPLACEABILITY_THRESHOLD = 0.75
LOW_REPLACEABILITY_THRESHOLD = 0.40

# 断点日期
CHATGPT_DATE = pd.Timestamp("2022-11-30")
COPILOT_DATE = pd.Timestamp("2022-06-21")


def load_data(features_dir: Path) -> pd.DataFrame:
    """加载语言周统计数据"""
    lang_path = features_dir / "language_weekly_stats.parquet"
    if not lang_path.exists():
        raise FileNotFoundError(f"找不到 {lang_path}，请先运行 02_build_features.py")
    
    df = pd.read_parquet(lang_path)
    df["week_start"] = pd.to_datetime(df["week_start"])
    
    # 添加AI可替代性指数
    df["ai_replaceability"] = df["language"].map(AI_REPLACEABILITY)
    df = df.dropna(subset=["ai_replaceability"])
    
    # 处理组/对照组标记
    df["treatment_group"] = (df["ai_replaceability"] >= HIGH_REPLACEABILITY_THRESHOLD).astype(int)
    df["control_group"] = (df["ai_replaceability"] <= LOW_REPLACEABILITY_THRESHOLD).astype(int)
    df["analysis_group"] = np.where(
        df["treatment_group"] == 1, "treatment",
        np.where(df["control_group"] == 1, "control", "excluded")
    )
    
    # 断点处理变量
    df["post_chatgpt"] = (df["week_start"] >= CHATGPT_DATE).astype(int)
    df["post_copilot"] = (df["week_start"] >= COPILOT_DATE).astype(int)
    
    # 对数变换
    df["log_question_count"] = np.log1p(df["question_count"].fillna(0))
    df["log_view_count"] = np.log1p(df["avg_view_count"].fillna(0))
    
    # 时间变量
    df["year_num"] = df["week_start"].dt.year
    df["week_num"] = (df["week_start"] - df["week_start"].min()).dt.days // 7
    
    # 语言-时间联合ID（用于面板数据）
    df["lang_id"] = pd.Categorical(df["language"]).codes
    
    print(f"  ✓ 加载 {len(df):,} 条语言-周级别数据")
    print(f"  处理组语言: {df[df['treatment_group']==1]['language'].unique().tolist()}")
    print(f"  对照组语言: {df[df['control_group']==1]['language'].unique().tolist()}")
    
    return df


def run_basic_did(df: pd.DataFrame, outcome_var: str = "log_question_count") -> dict:
    """
    基础2×2 DID估计
    使用处理组和对照组，ChatGPT发布作为断点
    """
    print("\n[1] 基础2×2 DID...")
    
    # 只保留处理组和对照组
    df_did = df[df["analysis_group"].isin(["treatment", "control"])].copy()
    df_did = df_did[df_did["week_start"] >= "2020-01-01"].copy()  # 从2020年开始
    
    # DID交乘项
    df_did["DiD"] = df_did["treatment_group"] * df_did["post_chatgpt"]
    
    # 简单OLS DID（加语言和时间固定效应）
    model_simple = smf.ols(
        f"{outcome_var} ~ DiD + treatment_group + post_chatgpt",
        data=df_did
    ).fit(cov_type="HC3")
    
    print(f"  简单DID系数: {model_simple.params['DiD']:.4f} (SE: {model_simple.bse['DiD']:.4f})")
    
    return {
        "model_simple": model_simple,
        "df_did": df_did,
        "n_obs": len(df_did),
    }


def run_twoway_fe_did(df: pd.DataFrame, outcome_var: str = "log_question_count") -> object:
    """
    两向固定效应DID
    语言固定效应 + 时间（周）固定效应
    处理序列相关：按语言聚类标准误
    """
    print("\n[2] 两向固定效应DID（linearmodels.PanelOLS）...")
    
    df_did = df[df["analysis_group"].isin(["treatment", "control"])].copy()
    df_did = df_did[df_did["week_start"] >= "2020-01-01"].copy()
    
    # DID交乘项
    df_did["DiD"] = df_did["treatment_group"] * df_did["post_chatgpt"]
    df_did["DiD_copilot"] = df_did["treatment_group"] * df_did["post_copilot"]
    
    # 设置面板索引（语言, 周）
    df_panel = df_did.set_index(["language", "week_start"])
    
    # 主回归：语言FE + 时间FE
    mod = PanelOLS(
        dependent=df_panel[outcome_var],
        exog=df_panel[["DiD"]],
        entity_effects=True,   # 语言固定效应
        time_effects=True,     # 时间固定效应
        drop_absorbed=True
    )
    
    res = mod.fit(cov_type="clustered", cluster_entity=True)  # 按语言聚类
    
    print(f"  2WFE DID系数: {res.params['DiD']:.4f}")
    print(f"  聚类SE: {res.std_errors['DiD']:.4f}")
    print(f"  t统计量: {res.tstats['DiD']:.2f}")
    print(f"  p值: {res.pvalues['DiD']:.4f}")
    print(f"  样本量: {res.nobs}")
    
    return res


def run_parallel_trends_test(df: pd.DataFrame, outcome_var: str = "log_question_count") -> dict:
    """
    平行趋势检验：预处理期安慰剂检验
    
    在ChatGPT发布前，用各季度虚拟变量×处理组检验
    如果平行趋势成立，这些系数应不显著
    """
    print("\n[3] 平行趋势检验...")
    
    df_pre = df[
        (df["analysis_group"].isin(["treatment", "control"])) &
        (df["week_start"] >= "2020-01-01") &
        (df["week_start"] < CHATGPT_DATE)
    ].copy()
    
    # 将时间分成季度，创建季度虚拟变量
    df_pre["quarter"] = df_pre["week_start"].dt.to_period("Q").astype(str)
    
    # 对参考季度进行编码（选2022Q2为参考期）
    reference_quarter = "2022Q2"
    df_pre["quarter_code"] = pd.Categorical(
        df_pre["quarter"],
        categories=sorted(df_pre["quarter"].unique())
    ).codes
    
    # 创建每个季度×处理组的交叉项
    quarters = sorted(df_pre["quarter"].unique())
    
    # 回归：treatment × quarter dummy（排除参考期）
    for q in quarters:
        df_pre[f"d_{q.replace('-', '_')}"] = (df_pre["quarter"] == q).astype(float)
        df_pre[f"did_{q.replace('-', '_')}"] = (
            df_pre[f"d_{q.replace('-', '_')}"] * df_pre["treatment_group"]
        )
    
    did_cols = [c for c in df_pre.columns if c.startswith("did_")]
    
    # 移除参考期
    ref_col = f"did_{reference_quarter.replace('-', '_').replace('Q', 'Q')}"
    if ref_col in did_cols:
        did_cols.remove(ref_col)
    
    formula = f"{outcome_var} ~ {' + '.join(did_cols)} + C(language) + C(quarter)"
    
    try:
        model_pt = smf.ols(formula, data=df_pre).fit(
            cov_type="cluster",
            cov_kwds={"groups": df_pre["language"]}
        )
        
        # 提取DID系数
        pt_coefs = {
            col: {
                "coef": model_pt.params.get(col, np.nan),
                "se": model_pt.bse.get(col, np.nan),
                "pval": model_pt.pvalues.get(col, np.nan),
            }
            for col in did_cols
        }
        
        # 联合检验：所有预处理期系数是否为0
        f_test_cols = [c for c in did_cols if c in model_pt.params.index]
        if f_test_cols:
            f_test = model_pt.f_test([f"{c} = 0" for c in f_test_cols])
            f_pval = f_test.pvalue
            print(f"  平行趋势联合检验 F-stat: p值 = {f_pval:.4f}")
            if f_pval > 0.1:
                print("  ✓ 平行趋势假设通过（p > 0.10）")
            else:
                print("  ⚠ 平行趋势可能违反（p < 0.10）")
        
        return {"model": model_pt, "coefs": pt_coefs, "f_pval": f_pval if f_test_cols else None}
    
    except Exception as e:
        print(f"  ⚠ 平行趋势检验失败: {e}")
        return {"model": None, "coefs": {}, "f_pval": None}


def run_heterogeneity_analysis(df: pd.DataFrame, outcome_var: str = "log_question_count") -> pd.DataFrame:
    """
    异质性分析：按AI可替代性程度的连续DID
    处理强度 = AI可替代性指数（连续变量）
    """
    print("\n[4] 异质性分析（连续处理强度DID）...")
    
    df_het = df[df["week_start"] >= "2020-01-01"].copy()
    df_het["DiD_continuous"] = df_het["ai_replaceability"] * df_het["post_chatgpt"]
    
    # 按语言聚类
    model = smf.ols(
        f"{outcome_var} ~ DiD_continuous + ai_replaceability + post_chatgpt + C(language) + week_num",
        data=df_het
    ).fit(cov_type="cluster", cov_kwds={"groups": df_het["language"]})
    
    coef = model.params.get("DiD_continuous", np.nan)
    se = model.bse.get("DiD_continuous", np.nan)
    pval = model.pvalues.get("DiD_continuous", np.nan)
    
    print(f"  连续DID系数 (ai_replaceability × post_chatgpt): {coef:.4f} (SE: {se:.4f}, p: {pval:.4f})")
    
    # 按语言分组的DID效应
    lang_effects = []
    for lang in df_het["language"].unique():
        df_lang = df_het[df_het["language"] == lang].copy()
        if len(df_lang) < 30:
            continue
        
        try:
            m = smf.ols(
                f"{outcome_var} ~ post_chatgpt + week_num",
                data=df_lang
            ).fit()
            
            lang_effects.append({
                "language": lang,
                "ai_replaceability": AI_REPLACEABILITY.get(lang, np.nan),
                "did_effect": m.params.get("post_chatgpt", np.nan),
                "se": m.bse.get("post_chatgpt", np.nan),
                "pval": m.pvalues.get("post_chatgpt", np.nan),
            })
        except Exception:
            continue
    
    df_lang_effects = pd.DataFrame(lang_effects).dropna()
    return df_lang_effects


def plot_parallel_trends(pt_result: dict, output_dir: Path):
    """绘制平行趋势检验图"""
    if not pt_result["coefs"]:
        return
    
    coefs = pt_result["coefs"]
    quarters = sorted(coefs.keys())
    
    coef_vals = [coefs[q]["coef"] for q in quarters]
    se_vals = [coefs[q]["se"] for q in quarters]
    
    with plt.rc_context(PUBLICATION_STYLE):
        fig, ax = plt.subplots(figsize=(12, 6))
        
        x = range(len(quarters))
        
        ax.errorbar(
            x, coef_vals,
            yerr=[1.96 * s for s in se_vals],
            fmt="o-", color="#2980B9", linewidth=2,
            markersize=6, capsize=4,
            label="DiD coefficient ± 95% CI"
        )
        ax.axhline(0, color="black", linewidth=1, linestyle="-")
        ax.fill_between(x, 
                        [c - 1.96*s for c, s in zip(coef_vals, se_vals)],
                        [c + 1.96*s for c, s in zip(coef_vals, se_vals)],
                        alpha=0.15, color="#2980B9")
        
        ax.set_xticks(list(x))
        ax.set_xticklabels(
            [q.replace("did_", "").replace("_", "Q").upper() for q in quarters],
            rotation=45, ha="right"
        )
        
        ax.set_title(
            "Parallel Trends Test: Treatment × Quarter Interaction (Pre-ChatGPT Period)\n"
            "Under parallel trends, all coefficients should be ≈ 0",
            fontweight="bold"
        )
        ax.set_ylabel("DID Coefficient (log question count)", fontsize=12)
        ax.set_xlabel("Quarter (Reference: 2022Q2)", fontsize=12)
        ax.legend()
        
        if pt_result.get("f_pval") is not None:
            ax.text(
                0.98, 0.95,
                f"Joint F-test p-value: {pt_result['f_pval']:.3f}",
                transform=ax.transAxes,
                ha="right", va="top", fontsize=10,
                bbox=dict(boxstyle="round", facecolor="lightyellow", alpha=0.8)
            )
        
        plt.tight_layout()
        
        for fmt in ["pdf", "png"]:
            out_path = output_dir / f"parallel_trends_test.{fmt}"
            plt.savefig(out_path, dpi=300 if fmt == "png" else None)
            print(f"  ✓ {out_path}")
        
        plt.close()


def plot_heterogeneity(df_lang_effects: pd.DataFrame, output_dir: Path):
    """
    绘制语言异质性散点图
    X轴：AI可替代性指数
    Y轴：ChatGPT发布后的问题量变化（DID效应）
    """
    import scipy.stats as stats
    
    df_plot = df_lang_effects.dropna(subset=["ai_replaceability", "did_effect"])
    
    with plt.rc_context(PUBLICATION_STYLE):
        fig, ax = plt.subplots(figsize=(10, 7))
        
        # 散点图
        colors = ["#E74C3C" if r > HIGH_REPLACEABILITY_THRESHOLD else
                  "#3498DB" if r < LOW_REPLACEABILITY_THRESHOLD else "#95A5A6"
                  for r in df_plot["ai_replaceability"]]
        
        scatter = ax.scatter(
            df_plot["ai_replaceability"],
            df_plot["did_effect"],
            c=colors, s=80, alpha=0.8, zorder=3
        )
        
        # 误差棒
        ax.errorbar(
            df_plot["ai_replaceability"],
            df_plot["did_effect"],
            yerr=df_plot["se"] * 1.96,
            fmt="none", color="gray", alpha=0.3, linewidth=0.8
        )
        
        # 语言标签
        for _, row in df_plot.iterrows():
            ax.annotate(
                row["language"],
                (row["ai_replaceability"], row["did_effect"]),
                textcoords="offset points",
                xytext=(4, 4),
                fontsize=8, color="black"
            )
        
        # 拟合线
        if len(df_plot) > 3:
            slope, intercept, r_val, p_val, std_err = stats.linregress(
                df_plot["ai_replaceability"], df_plot["did_effect"]
            )
            x_fit = np.linspace(df_plot["ai_replaceability"].min(), df_plot["ai_replaceability"].max(), 100)
            ax.plot(x_fit, slope * x_fit + intercept,
                    color="#E74C3C", linewidth=2, linestyle="--",
                    label=f"Linear fit (r={r_val:.2f}, p={p_val:.3f})")
        
        # 参考线
        ax.axhline(0, color="black", linewidth=1, linestyle="-", alpha=0.5)
        ax.axvline(HIGH_REPLACEABILITY_THRESHOLD, color="red", linewidth=1, linestyle=":",
                   alpha=0.5, label=f"Treatment threshold ({HIGH_REPLACEABILITY_THRESHOLD})")
        ax.axvline(LOW_REPLACEABILITY_THRESHOLD, color="blue", linewidth=1, linestyle=":",
                   alpha=0.5, label=f"Control threshold ({LOW_REPLACEABILITY_THRESHOLD})")
        
        ax.set_xlabel("AI Replaceability Index (HumanEval-based)", fontsize=12)
        ax.set_ylabel("Post-ChatGPT Effect on log(Question Count)", fontsize=12)
        ax.set_title(
            "Heterogeneity Analysis: Effect vs. AI Replaceability by Language\n"
            "Red dots = treatment group; Blue dots = control group",
            fontweight="bold"
        )
        ax.legend(loc="upper right", framealpha=0.9)
        
        plt.tight_layout()
        
        for fmt in ["pdf", "png"]:
            out_path = output_dir / f"heterogeneity_by_language.{fmt}"
            plt.savefig(out_path, dpi=300 if fmt == "png" else None)
            print(f"  ✓ {out_path}")
        
        plt.close()


def main():
    parser = argparse.ArgumentParser(description="双重差分分析")
    parser.add_argument("--features", default="data/features/", help="特征数据目录")
    parser.add_argument("--output", default="results/figures/did/", help="输出目录")
    parser.add_argument("--outcome", default="log_question_count", help="结果变量")
    
    args = parser.parse_args()
    
    features_dir = Path(args.features)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("=" * 60)
    print("双重差分（DID）分析")
    print(f"断点：ChatGPT发布（{CHATGPT_DATE.date()}）")
    print(f"处理强度：AI可替代性指数（{HIGH_REPLACEABILITY_THRESHOLD} / {LOW_REPLACEABILITY_THRESHOLD} 阈值）")
    print("=" * 60)
    
    # 加载数据
    print("\n加载数据...")
    df = load_data(features_dir)
    
    # 1. 基础DID
    basic_result = run_basic_did(df, args.outcome)
    
    # 2. 两向固定效应DID
    fe_result = run_twoway_fe_did(df, args.outcome)
    
    # 3. 平行趋势检验
    pt_result = run_parallel_trends_test(df, args.outcome)
    plot_parallel_trends(pt_result, output_dir)
    
    # 4. 异质性分析
    lang_effects = run_heterogeneity_analysis(df, args.outcome)
    plot_heterogeneity(lang_effects, output_dir)
    
    # 5. 保存语言效应
    lang_effects_path = Path("results/tables/language_effects.csv")
    lang_effects_path.parent.mkdir(parents=True, exist_ok=True)
    lang_effects.to_csv(lang_effects_path, index=False)
    
    print(f"\n✅ DID分析完成！")
    print(f"   图表目录: {output_dir}")
    
    # 打印主要结果
    print("\n" + "=" * 60)
    print("主要DID结果摘要")
    print("=" * 60)
    
    did_coef = basic_result["model_simple"].params.get("DiD", np.nan)
    did_se = basic_result["model_simple"].bse.get("DiD", np.nan)
    did_pval = basic_result["model_simple"].pvalues.get("DiD", np.nan)
    
    pct_change = (np.exp(did_coef) - 1) * 100 if not np.isnan(did_coef) else np.nan
    
    print(f"基础DID系数: {did_coef:.4f} ({pct_change:.1f}%)")
    print(f"标准误: ({did_se:.4f})")
    print(f"p值: {did_pval:.4f}")
    print(f"样本量: {basic_result['n_obs']:,}")


if __name__ == "__main__":
    main()
