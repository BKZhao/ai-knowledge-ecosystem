"""
任务2：构建所有虚拟控制变量
- COVID效应
- 科技行业裁员
- SO平台政策变化
- AI工具发布节点
"""
import pandas as pd
import json

# 生成2018-2026年周列表
weeks = pd.date_range("2018-01-01", "2026-03-01", freq="W-MON")
df = pd.DataFrame({"week_dt": weeks})
df["week"] = df["week_dt"].dt.strftime("%G-W%V")

# ====== COVID虚拟变量 ======
# COVID爆发期：2020Q1-2021Q2（居家学习编程热潮）
df["covid_peak"] = ((df["week_dt"] >= "2020-03-01") & (df["week_dt"] <= "2021-06-30")).astype(int)
# COVID后期/疫情结束
df["post_covid"] = ((df["week_dt"] >= "2021-07-01") & (df["week_dt"] <= "2022-06-30")).astype(int)

# ====== 科技行业裁员虚拟变量 ======
# 第一波裁员：2022年末（Meta/Twitter/Amazon）
df["tech_layoff_wave1"] = ((df["week_dt"] >= "2022-10-01") & (df["week_dt"] <= "2023-03-31")).astype(int)
# 第二波裁员：2023年初（Google/Microsoft/Salesforce）
df["tech_layoff_wave2"] = ((df["week_dt"] >= "2023-01-01") & (df["week_dt"] <= "2023-06-30")).astype(int)
# 合并裁员指标
df["tech_layoff"] = (df["tech_layoff_wave1"] | df["tech_layoff_wave2"]).astype(int)

# ====== SO平台政策变化 ======
# SO禁止AI生成内容（2022-12-05）
df["so_ai_ban"] = ((df["week_dt"] >= "2022-12-05") & (df["week_dt"] <= "2023-06-04")).astype(int)
# SO员工罢工（2023-05-01 到 2023-08-01）
df["so_strike"] = ((df["week_dt"] >= "2023-05-01") & (df["week_dt"] <= "2023-08-01")).astype(int)
# SO收费政策（2023-07起限制API访问）
df["so_api_restrict"] = (df["week_dt"] >= "2023-07-01").astype(int)

# ====== AI工具发布虚拟变量 ======
ai_events = {
    "post_copilot_beta":  "2021-10-01",
    "post_copilot_ga":    "2022-06-21",
    "post_chatgpt":       "2022-11-30",
    "post_gpt4":          "2023-03-14",
    "post_llama2":        "2023-07-18",
    "post_codelllama":    "2023-08-24",
    "post_claude3":       "2024-03-04",
    "post_gpt4o":         "2024-05-13",
    "post_cursor_boom":   "2024-10-01",
}
for var, date in ai_events.items():
    df[var] = (df["week_dt"] >= date).astype(int)

# ====== AI能力指数（连续变量，基于HumanEval分数插值）======
# 关键节点的HumanEval分数
capability_milestones = [
    ("2021-10-01", 0.27),  # Copilot/Codex
    ("2022-06-21", 0.37),  # Copilot GA
    ("2022-11-30", 0.48),  # ChatGPT
    ("2023-03-14", 0.67),  # GPT-4
    ("2023-07-18", 0.71),  # Claude 2
    ("2023-08-24", 0.65),  # Code Llama
    ("2024-05-13", 0.90),  # GPT-4o
    ("2024-09-12", 0.92),  # o1-preview
    ("2024-12-01", 0.94),  # Claude 3.5 updated
    ("2025-02-19", 0.97),  # Claude 3.7
]

milestone_df = pd.DataFrame(capability_milestones, columns=["date", "score"])
milestone_df["date"] = pd.to_datetime(milestone_df["date"])

# 对每周插值
df["ai_capability_index"] = 0.0
for i, row in df.iterrows():
    dt = row["week_dt"]
    past = milestone_df[milestone_df["date"] <= dt]
    if len(past) == 0:
        df.at[i, "ai_capability_index"] = 0.10  # 基准期
    else:
        df.at[i, "ai_capability_index"] = past.iloc[-1]["score"]

# 保存
out_path = "results/control_variables.csv"
df.to_csv(out_path, index=False)
print(f"✅ 控制变量文件已保存: {out_path}")
print(f"   字段数: {len(df.columns)}")
print(f"   周数: {len(df)}")
print(f"\n字段列表:")
for col in df.columns:
    print(f"  {col}")

# 打印几个关键时期的统计
print(f"\n关键事件验证:")
print(f"  COVID peak (2020-2021): {df['covid_peak'].sum()} 周")
print(f"  Tech layoffs: {df['tech_layoff'].sum()} 周")
print(f"  SO AI ban期间: {df['so_ai_ban'].sum()} 周")
print(f"  ChatGPT后: {df['post_chatgpt'].sum()} 周")
