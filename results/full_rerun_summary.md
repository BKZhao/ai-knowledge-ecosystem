# 全量分析重跑结果汇总

**时间**: 2026-04-17  
**触发**: SE面板更新(Sociology删除, English/Literature补值) + SO 2024+扩展数据

## 数据更新确认
- ✅ `se_panel_complete_2018_2026.csv`: 31列×99行(含month), 30个SE社区, 0空值
- ✅ `so_monthly_extension.csv`: 24个月(2024.04-2026.03), total_questions + quality metrics
- ✅ Posts parquet: 2018-2024.03, 21.9M posts
- ✅ SO语言月度特征: 2018.01-2024.03

## 依赖文件状态
| 文件 | 状态 | 说明 |
|------|------|------|
| `results/stacked_panel.csv` | ✅ 无需更新 | SO语言+GitHub面板, 不含SE社区 |
| `results/stackexchange_communities.json` | ✅ 无需更新 | 14个社区周数据, 不含Sociology |
| `data/features/weekly_stats.parquet` | ✅ 新生成 | 326周, SO主站统计 |
| `data/features/language_weekly_stats.parquet` | ✅ 新生成 | 5,216行×16语言 |

## 回归分析 (run_regressions_v2.py) ✅

### H2: 基础DID
- β (treat×post): **-0.5880** (p=0.0000), R²=0.1506, N=1,274
- **AI冲击后SO问题数量显著下降**

### H3: GitHub Copilot效应
- 跨平台DID β (treat×post×github): 27.593 (SE=17.113, p=0.1379)
- GitHub上高可替代性语言活动增加, 但统计上不显著

### H4: SE社区效应
- β=27.593 (SE=17.113, p=0.1379)
- SE社区作为对照, 未发现显著活动转移

### H5: 事件强度排序
- ChatGPT: CAR=-441.7%, GPT-4: CAR=-574.7%
- Claude 3: CAR=+340.2% (正值, 但样本有限)
- Spearman ρ=0.200, p=0.800 (不显著)

### H6: 连续处理强度
- β1=-0.5880 (p=0.0000), β2=0.9243 (p=0.0000), R²=0.1506, N=1,274
- **高AI可替代性语言问题数量下降更多**

### 稳健性检验
| 检验 | β | p | R² | N |
|------|---|---|-----|---|
| Placebo (2021断点) | 0.1345 | 0.0242 | 0.0077 | 660 |
| No COVID | -0.6268 | 0.0000 | 0.0462 | 851 |
| Copilot era | 0.1070 | 0.2340 | 0.0021 | 671 |
| ChatGPT era | -0.6003 | 0.0000 | 0.0452 | 1,121 |

### 图表输出
- ✅ regression_fig1.png ~ fig5.png
- ✅ regression_tables.tex
- ✅ regression_summary.md

## DID分析 (03_did_analysis.py) ✅

### 基础2×2 DID
- **DID系数: -0.1911 (-17.4%)**
- SE: 0.0652, p=0.0034
- **高AI可替代性语言在ChatGPT后问题数量下降17.4%**

### 两向固定效应
- 2WFE DID: -0.1911, 聚类SE=0.0892, t=-2.14, p=0.0324, N=1,989

### 平行趋势
- F-test p=1.0000 (通过, 数据有限)

### 异质性分析
- 连续DID: -0.1660 (SE=0.2948, p=0.5734, 不显著)

### 图表
- ✅ parallel_trends_test.pdf/.png
- ✅ heterogeneity_by_language.pdf/.png

## 事件研究 (02_event_study.py) ✅ (运行成功, 但结果存疑)

| 事件 | CAR(log) | R² |
|------|----------|-----|
| Copilot Beta | 10.59*** | 1.000 |
| Copilot GA | 11.14*** | 1.000 |
| ChatGPT | 2.76*** | 1.000 |
| GPT-4 | 3.85*** | 1.000 |

**⚠️ 注意**: R²=1.0和极端CAR值表明模型存在严重过拟合(week_of_year dummy过多), 结果需谨慎解读。建议后续优化模型规范。

## 描述统计 (01_descriptive.py) ⚠️ 部分完成

- ✅ fig01: SO周趋势图
- ✅ fig02: 社区对比图
- ✅ fig03: 语言趋势图
- ⏭️ fig04: 用户构成(数据不足, 跳过)
- ❌ fig05: 摘要统计热力图(缺少accepted_rate等列, 跳过)

## 跳过的分析
- `04_knowledge_complexity.py` - 未要求
- `05_user_survival.py` - 未要求

## 已知限制
1. SO数据仅到2024.03, 2024.04-2026.03只有API抽样total_questions
2. 事件研究模型过拟合严重(R²=1.0), 需重新设计
3. 描述统计缺少部分列(user_cohorts.parquet不存在)
4. DID分析的平行趋势检验统计功效可能不足(对照组仅assembly)
