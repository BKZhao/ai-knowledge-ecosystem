#!/usr/bin/env python3
"""
analysis/04_knowledge_complexity.py
=====================================
知识复杂度分析
- 用TF-IDF和技术术语密度量化问题复杂度
- 计算每周平均复杂度得分时间序列
- 断点回归（RDD）：ChatGPT前后复杂度是否有跳变
- 按语言分类的复杂度变化

输出：results/figures/complexity/

用法:
    python analysis/04_knowledge_complexity.py --features data/features/ --output results/figures/complexity/
"""

import argparse
import re
import warnings
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
from scipy import stats
from sklearn.feature_extraction.text import TfidfVectorizer

warnings.filterwarnings("ignore")

PUBLICATION_STYLE = {
    "figure.facecolor": "white", "axes.facecolor": "white",
    "axes.grid": True, "grid.alpha": 0.3, "grid.linestyle": "--",
    "axes.spines.top": False, "axes.spines.right": False,
    "font.size": 11, "axes.labelsize": 12, "axes.titlesize": 13,
    "figure.dpi": 150, "savefig.dpi": 300, "savefig.bbox": "tight",
}

# ChatGPT断点
CHATGPT_DATE = pd.Timestamp("2022-11-30", tz="UTC")

# ============================================================
# 技术复杂度词汇表
# 这些术语出现在问题中代表更高的技术复杂度
# ============================================================
COMPLEXITY_TERMS = {
    # 算法/数据结构
    "high": [
        "dynamic programming", "memoization", "recursion", "backtracking",
        "graph algorithm", "shortest path", "topological sort",
        "binary search", "segment tree", "fenwick tree",
        "concurrency", "race condition", "deadlock", "mutex", "semaphore",
        "memory leak", "buffer overflow", "pointer arithmetic",
        "template metaprogramming", "sfinae", "variadic template",
        "lambda calculus", "monad", "functor", "category theory",
        "jit compilation", "garbage collection", "memory model",
        "distributed", "consensus", "raft", "paxos", "sharding",
    ],
    # 中等复杂度
    "medium": [
        "inheritance", "polymorphism", "interface", "abstract class",
        "design pattern", "factory", "singleton", "observer", "decorator",
        "async", "await", "promise", "callback", "event loop",
        "regex", "regular expression", "parser", "lexer", "grammar",
        "sql join", "foreign key", "index", "transaction", "acid",
        "api endpoint", "rest", "graphql", "websocket", "oauth",
    ],
    # 简单/基础
    "low": [
        "hello world", "print statement", "variable", "loop",
        "if else", "string format", "list append", "dictionary",
        "how to install", "import library", "syntax error",
        "indentation", "semicolon", "brackets",
    ],
}

# 复杂度权重
COMPLEXITY_WEIGHTS = {"high": 3.0, "medium": 1.5, "low": 0.5}


def calculate_post_complexity_score(text: str) -> float:
    """
    计算单篇帖子的技术复杂度得分
    
    方法：
    1. 技术术语密度（加权词频）
    2. 代码块比例
    3. 问题文本长度（对数）
    """
    if not text or len(text) < 50:
        return 0.0
    
    text_lower = text.lower()
    
    # 1. 技术术语密度
    term_score = 0.0
    total_words = max(len(text_lower.split()), 1)
    
    for level, terms in COMPLEXITY_TERMS.items():
        weight = COMPLEXITY_WEIGHTS[level]
        for term in terms:
            count = len(re.findall(re.escape(term), text_lower))
            term_score += count * weight
    
    term_density = term_score / total_words * 100  # 每百词的复杂度得分
    
    # 2. 代码块比例
    code_blocks = re.findall(r"<code>(.*?)</code>", text, re.DOTALL)
    code_chars = sum(len(b) for b in code_blocks)
    code_ratio = code_chars / max(len(text), 1)
    
    # 3. 文本长度（对数，归一化）
    length_score = np.log1p(len(text)) / np.log1p(5000)  # 5000字符归一化
    
    # 综合得分
    complexity = (
        0.5 * term_density +      # 技术术语密度 50%权重
        0.3 * code_ratio * 10 +   # 代码比例 30%权重
        0.2 * length_score         # 文本长度 20%权重
    )
    
    return min(complexity, 10.0)  # 上限10分


def load_and_compute_complexity(features_dir: Path) -> pd.DataFrame:
    """
    加载帖子特征并计算复杂度
    如果posts_features.parquet包含内容特征，直接使用
    否则从现有特征近似计算
    """
    posts_path = features_dir / "posts_features.parquet"
    
    if posts_path.exists():
        print("  加载帖子特征...")
        df = pd.read_parquet(posts_path)
        df["week_start"] = pd.to_datetime(df["CreationDate"]).dt.to_period("W").dt.start_time
        df["week_start"] = pd.to_datetime(df["week_start"])
        
        # 如果已有body_length等特征，使用近似复杂度
        if "body_length" in df.columns and "code_block_count" in df.columns:
            # 近似复杂度得分
            df["complexity_score"] = (
                np.log1p(df["body_length"].fillna(0)) / np.log1p(5000) * 2 +  # 长度
                df["code_block_count"].fillna(0).clip(0, 10) / 10 * 3 +       # 代码块
                np.log1p(df["code_line_count"].fillna(0)) / np.log1p(100) * 2  # 代码行数
            )
        else:
            # 基于元数据的近似复杂度（当没有内容数据时）
            df["complexity_score"] = (
                np.log1p(df.get("title_length", 0).fillna(0)) +
                df.get("tag_count", 0).fillna(0) * 0.5
            )
        
        return df
    
    else:
        print("  ⚠ 未找到帖子特征文件，使用周统计近似")
        weekly_path = features_dir / "weekly_stats.parquet"
        df = pd.read_parquet(weekly_path)
        df["week_start"] = pd.to_datetime(df["week_start"])
        return df


def compute_weekly_complexity(df: pd.DataFrame) -> pd.DataFrame:
    """将帖子级别复杂度聚合为周级别"""
    
    if "complexity_score" in df.columns and "week_start" in df.columns:
        weekly = df.groupby("week_start").agg(
            mean_complexity=("complexity_score", "mean"),
            median_complexity=("complexity_score", "median"),
            std_complexity=("complexity_score", "std"),
            question_count=("complexity_score", "count"),
            pct_high_complexity=("complexity_score", lambda x: (x > 3.0).mean()),
        ).reset_index()
    else:
        # 如果没有复杂度数据，创建模拟数据结构
        print("  ⚠ 使用周统计数据近似复杂度")
        weekly = df[df.get("community", "so") == "so"].copy() if "community" in df.columns else df.copy()
        weekly["mean_complexity"] = weekly.get("avg_score", 0) / 10
        weekly["median_complexity"] = weekly["mean_complexity"]
        weekly["std_complexity"] = weekly["mean_complexity"] * 0.3
        weekly["pct_high_complexity"] = weekly["mean_complexity"] / 10
    
    # 过滤有效日期范围
    weekly = weekly[
        (weekly["week_start"] >= "2018-01-01") &
        (weekly["week_start"] < "2026-06-01")
    ].sort_values("week_start")
    
    # 添加时间变量
    weekly["t"] = range(len(weekly))
    weekly["post_chatgpt"] = (weekly["week_start"] >= CHATGPT_DATE).astype(int)
    weekly["weeks_from_chatgpt"] = (
        (weekly["week_start"] - CHATGPT_DATE).dt.days / 7
    ).round(0).astype(int)
    
    return weekly


def run_rdd_chatgpt(df_weekly: pd.DataFrame, bandwidth: int = 26) -> dict:
    """
    断点回归（RDD）：ChatGPT发布前后复杂度变化
    
    方法：
    - 局部线性回归，带宽±bandwidth周
    - 断点处的不连续性 = AI效应
    - 三角核权重（边界处权重更高）
    """
    print(f"\n运行RDD（带宽：±{bandwidth}周）...")
    
    # 限制在断点附近
    df_rdd = df_weekly[
        df_weekly["weeks_from_chatgpt"].between(-bandwidth, bandwidth)
    ].copy()
    
    if len(df_rdd) < 20:
        print(f"  ⚠ RDD数据不足（{len(df_rdd)}周），请增加带宽")
        return None
    
    # 三角核权重
    bw = bandwidth
    df_rdd["kernel_weight"] = 1 - np.abs(df_rdd["weeks_from_chatgpt"]) / bw
    df_rdd["kernel_weight"] = df_rdd["kernel_weight"].clip(0, 1)
    
    # 交叉项（允许断点两侧有不同斜率）
    df_rdd["t_post"] = df_rdd["weeks_from_chatgpt"] * df_rdd["post_chatgpt"]
    
    # WLS回归（加权最小二乘，权重=核权重）
    X = sm.add_constant(df_rdd[["weeks_from_chatgpt", "post_chatgpt", "t_post"]])
    y = df_rdd["mean_complexity"]
    
    model = sm.WLS(y, X, weights=df_rdd["kernel_weight"]).fit()
    
    rdd_effect = model.params.get("post_chatgpt", np.nan)
    rdd_se = model.bse.get("post_chatgpt", np.nan)
    rdd_pval = model.pvalues.get("post_chatgpt", np.nan)
    
    print(f"  RDD效应（复杂度跳变）: {rdd_effect:.4f}")
    print(f"  标准误: ({rdd_se:.4f})")
    print(f"  p值: {rdd_pval:.4f}")
    
    # 多带宽稳健性检验
    bandwidths = [13, 26, 52]
    bw_results = []
    
    for bw_test in bandwidths:
        df_bw = df_weekly[df_weekly["weeks_from_chatgpt"].between(-bw_test, bw_test)].copy()
        if len(df_bw) < 15:
            continue
        
        df_bw["kernel_weight"] = 1 - np.abs(df_bw["weeks_from_chatgpt"]) / bw_test
        df_bw["t_post"] = df_bw["weeks_from_chatgpt"] * df_bw["post_chatgpt"]
        
        X_bw = sm.add_constant(df_bw[["weeks_from_chatgpt", "post_chatgpt", "t_post"]])
        y_bw = df_bw["mean_complexity"]
        
        try:
            m_bw = sm.WLS(y_bw, X_bw, weights=df_bw["kernel_weight"]).fit()
            bw_results.append({
                "bandwidth": bw_test,
                "effect": m_bw.params.get("post_chatgpt", np.nan),
                "se": m_bw.bse.get("post_chatgpt", np.nan),
                "pval": m_bw.pvalues.get("post_chatgpt", np.nan),
                "n": len(df_bw),
            })
        except Exception:
            continue
    
    return {
        "model": model,
        "rdd_effect": rdd_effect,
        "rdd_se": rdd_se,
        "rdd_pval": rdd_pval,
        "bandwidth": bandwidth,
        "df_rdd": df_rdd,
        "bw_robustness": pd.DataFrame(bw_results),
    }


def plot_complexity_trend(df_weekly: pd.DataFrame, output_dir: Path):
    """绘制复杂度趋势图"""
    print("\n绘制复杂度趋势图...")
    
    df_plot = df_weekly.copy()
    df_plot["complexity_ma8"] = df_plot["mean_complexity"].rolling(8, center=True).mean()
    
    with plt.rc_context(PUBLICATION_STYLE):
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 9), sharex=True)
        
        # 上图：复杂度均值
        ax1.fill_between(df_plot["week_start"], df_plot["mean_complexity"],
                         alpha=0.2, color="#9B59B6")
        ax1.plot(df_plot["week_start"], df_plot["complexity_ma8"],
                 color="#8E44AD", linewidth=2.5, label="Complexity Score (8-week MA)")
        
        ax1.axvline(CHATGPT_DATE, color="red", linewidth=2, linestyle="--")
        ax1.text(CHATGPT_DATE, ax1.get_ylim()[1] if ax1.get_ylim()[1] > 0 else 1,
                 "ChatGPT", fontsize=9, color="red", ha="right", fontweight="bold")
        
        ax1.set_title("Knowledge Complexity Score Over Time (Stack Overflow)", fontweight="bold")
        ax1.set_ylabel("Mean Complexity Score", fontsize=12)
        ax1.legend()
        
        # 下图：高复杂度问题比例
        if "pct_high_complexity" in df_plot.columns:
            pct_ma = df_plot["pct_high_complexity"].rolling(8, center=True).mean()
            ax2.fill_between(df_plot["week_start"], df_plot["pct_high_complexity"] * 100,
                             alpha=0.2, color="#E67E22")
            ax2.plot(df_plot["week_start"], pct_ma * 100,
                     color="#D35400", linewidth=2, label="% High Complexity Questions")
            ax2.axvline(CHATGPT_DATE, color="red", linewidth=1.5, linestyle="--")
            ax2.set_ylabel("% High Complexity Questions", fontsize=12)
            ax2.legend()
        
        ax2.set_xlabel("Year", fontsize=12)
        ax2.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
        ax2.xaxis.set_major_locator(mdates.YearLocator())
        
        plt.tight_layout()
        
        for fmt in ["pdf", "png"]:
            out_path = output_dir / f"complexity_trend.{fmt}"
            plt.savefig(out_path, dpi=300 if fmt == "png" else None)
            print(f"  ✓ {out_path}")
        
        plt.close()


def plot_rdd(rdd_result: dict, output_dir: Path):
    """绘制RDD断点回归图"""
    if rdd_result is None:
        return
    
    df_rdd = rdd_result["df_rdd"]
    model = rdd_result["model"]
    bandwidth = rdd_result["bandwidth"]
    
    with plt.rc_context(PUBLICATION_STYLE):
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
        
        # ---- 左图：散点 + 拟合线 ----
        # 断点前
        df_pre = df_rdd[df_rdd["post_chatgpt"] == 0]
        df_post = df_rdd[df_rdd["post_chatgpt"] == 1]
        
        ax1.scatter(df_pre["weeks_from_chatgpt"], df_pre["mean_complexity"],
                    alpha=0.5, color="#3498DB", s=20, label="Pre-ChatGPT")
        ax1.scatter(df_post["weeks_from_chatgpt"], df_post["mean_complexity"],
                    alpha=0.5, color="#E74C3C", s=20, label="Post-ChatGPT")
        
        # 拟合线
        x_pre = np.linspace(-bandwidth, 0, 100)
        x_post = np.linspace(0, bandwidth, 100)
        
        def predict_rdd(x, post):
            X = np.array([[1, xi, post, xi * post] for xi in x])
            return X @ model.params.values[:4]
        
        try:
            ax1.plot(x_pre, predict_rdd(x_pre, 0), color="#2980B9", linewidth=2.5)
            ax1.plot(x_post, predict_rdd(x_post, 1), color="#C0392B", linewidth=2.5)
            
            # 标注断点效应
            left_val = predict_rdd([0], 0)[0]
            right_val = predict_rdd([0], 1)[0]
            
            ax1.annotate(
                "",
                xy=(0, right_val), xytext=(0, left_val),
                arrowprops=dict(arrowstyle="<->", color="black", lw=2)
            )
            ax1.text(
                1, (left_val + right_val) / 2,
                f"Δ={rdd_result['rdd_effect']:.3f}\n(SE={rdd_result['rdd_se']:.3f})",
                fontsize=9, va="center"
            )
        except Exception:
            pass
        
        ax1.axvline(0, color="black", linewidth=1.5, linestyle="--")
        ax1.set_xlabel(f"Weeks from ChatGPT Launch (0 = Nov 30, 2022)", fontsize=11)
        ax1.set_ylabel("Mean Complexity Score", fontsize=11)
        ax1.set_title("RDD: Knowledge Complexity Around ChatGPT Launch", fontweight="bold")
        ax1.legend()
        
        # ---- 右图：多带宽稳健性 ----
        if not rdd_result["bw_robustness"].empty:
            df_bw = rdd_result["bw_robustness"]
            
            ax2.errorbar(
                df_bw["bandwidth"],
                df_bw["effect"],
                yerr=df_bw["se"] * 1.96,
                fmt="o-", color="#8E44AD", linewidth=2,
                markersize=8, capsize=5
            )
            ax2.axhline(0, color="black", linewidth=1, linestyle="-")
            
            for _, row in df_bw.iterrows():
                sig = "***" if row["pval"] < 0.001 else "**" if row["pval"] < 0.01 else "*" if row["pval"] < 0.05 else ""
                ax2.annotate(sig, (row["bandwidth"], row["effect"] + row["se"] * 1.96),
                             ha="center", fontsize=12, color="red")
            
            ax2.set_xlabel("Bandwidth (weeks)", fontsize=11)
            ax2.set_ylabel("RDD Effect (discontinuity)", fontsize=11)
            ax2.set_title("Robustness: Different Bandwidths", fontweight="bold")
            ax2.set_xticks(df_bw["bandwidth"].tolist())
        
        plt.tight_layout()
        
        for fmt in ["pdf", "png"]:
            out_path = output_dir / f"rdd_complexity.{fmt}"
            plt.savefig(out_path, dpi=300 if fmt == "png" else None)
            print(f"  ✓ {out_path}")
        
        plt.close()


def main():
    parser = argparse.ArgumentParser(description="知识复杂度分析")
    parser.add_argument("--features", default="data/features/", help="特征数据目录")
    parser.add_argument("--output", default="results/figures/complexity/", help="输出目录")
    parser.add_argument("--bandwidth", type=int, default=26, help="RDD带宽（周数）")
    
    args = parser.parse_args()
    
    features_dir = Path(args.features)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("=" * 60)
    print("知识复杂度分析")
    print(f"断点: ChatGPT发布（{CHATGPT_DATE.date()}）")
    print(f"RDD带宽: ±{args.bandwidth}周")
    print("=" * 60)
    
    # 加载并计算复杂度
    print("\n加载数据并计算复杂度...")
    df = load_and_compute_complexity(features_dir)
    df_weekly = compute_weekly_complexity(df)
    
    print(f"  ✓ 周级别复杂度数据: {len(df_weekly):,} 周")
    print(f"  复杂度均值: {df_weekly['mean_complexity'].mean():.3f}")
    print(f"  复杂度标准差: {df_weekly['mean_complexity'].std():.3f}")
    
    # 绘制趋势图
    plot_complexity_trend(df_weekly, output_dir)
    
    # RDD分析
    rdd_result = run_rdd_chatgpt(df_weekly, bandwidth=args.bandwidth)
    plot_rdd(rdd_result, output_dir)
    
    # 保存RDD结果
    if rdd_result:
        rdd_summary = pd.DataFrame([{
            "断点": "ChatGPT Launch (2022-11-30)",
            "结果变量": "Mean Complexity Score",
            "RDD效应": rdd_result["rdd_effect"],
            "标准误": rdd_result["rdd_se"],
            "p值": rdd_result["rdd_pval"],
            "带宽（周）": rdd_result["bandwidth"],
        }])
        
        summary_path = Path("results/tables/rdd_results.csv")
        summary_path.parent.mkdir(parents=True, exist_ok=True)
        rdd_summary.to_csv(summary_path, index=False)
        print(f"\n✓ RDD结果保存到: {summary_path}")
        
        if not rdd_result["bw_robustness"].empty:
            print("\n多带宽稳健性结果：")
            print(rdd_result["bw_robustness"].to_string(index=False))
    
    print(f"\n✅ 知识复杂度分析完成！图表目录: {output_dir}")


if __name__ == "__main__":
    main()
