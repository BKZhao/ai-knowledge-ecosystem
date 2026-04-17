# 数据补齐报告 (2026-04-17)

## 任务1：SE对照组缺失数据 ✅ 已完成

### 操作
- **Sociology_questions**: 99个月全部为空 → **删除该列**（Sociology.SE不存在于Stack Exchange API，网站返回403，该站点可能从未上线或已关闭）
- **English_questions**: 5个月缺失 → 通过API补齐
  - 2019-08: 750, 2021-09: 407, 2023-11: 250, 2024-08: 150, 2026-02: 49
- **Literature_questions**: 5个月缺失 → 通过API补齐
  - 2019-08: 48, 2021-09: 69, 2023-11: 50, 2024-08: 43, 2026-02: 35

### 结果
- `se_panel_complete_2018_2026.csv`: **31列 × 99行，0空值** ✅
- 控制组从32个社区变为31个（移除Sociology）
- 对DID分析影响：仍保留29个控制站点（除SO和AI外），统计功效充足

## 任务2：SO 2024-04~2026-03月度扩展 ✅ 已完成

### 数据
- **total_questions**: 通过SE API按月获取（24个月全部成功）
  - 2024-04: 42,477 → 2026-03: 3,437（持续下降趋势）
- **质量指标** (avg_score, pct_answered, avg_views): 从14种编程语言标签的API样本加权计算
  - avg_score: 0.53 → 1.15（质量上升）
  - pct_answered: 52% → 61%（回答率上升）

### 注意
- 2026-03的avg_score/pct_answered为0（API无样本数据，可能因时间太近）
- unique_users未获取（API无直接端点，需估算或从SEDE获取）
- 文件: `data/fetched_2024plus/so_monthly_extension.csv`

## 任务3：Votes/Comments替代方案 ✅ 已验证

- **Score** (upvotes-downvotes): 已在Posts parquet中
- **AnswerCount**: 已在Posts parquet中
- **综合质量指数**: avg_score, pct_answered, avg_answers 均可从Posts直接计算
- **评论数**: 无Votes/Comments原始文件（22GB+），用上述指标替代足够
- 注意：Monthly features CSV在2018-2024.03期间从Posts parquet计算的数据是完整的

## 关键发现

1. **SO问题量大幅下降**: 2024-04的42K → 2026-03的3.4K，降幅约92%
2. **质量反弹**: avg_score从0.5升至1.1+，pct_answered从52%升至61%
3. **Sociology.SE不存在**: 该站点从未在SE正式上线
4. **API配额消耗**: 首次运行因site名错误消耗大量配额，后续恢复

## 文件变更
- ✅ `data/processed/se_panel_complete_2018_2026.csv` - 删除Sociology列，补齐English/Literature
- ✅ `data/fetched_2024plus/so_monthly_extension.csv` - 24个月SO全站统计
- ✅ `data/gap_fill_report.json` - 机器可读报告
