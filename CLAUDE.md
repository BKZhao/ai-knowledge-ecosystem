# CLAUDE.md — Claude Code 工作指令

> 本文件是给 Claude Code（claude.ai/code 或 CLI）的项目工作手册。
> 每次开始工作前请读这个文件。

---

## 项目背景

**研究课题：** 生成式AI工具（2020-2026）对Stack Overflow知识生态的系统性影响

**核心问题：** ChatGPT等AI工具的普及是否系统性地降低了SO的问题量、问题质量、用户留存率？

**方法论：** 事件研究法（Event Study）+ 双重差分（DID）+ 断点回归（RDD）+ 生存分析（Cox）

详细研究设计见 `RESEARCH.md`。

---

## 数据位置和格式

### 原始数据
```
data/raw/
├── stackoverflow.com-Posts.7z         # ~20GB压缩，解压后~100GB
├── stackoverflow.com-Users.7z         # ~2GB压缩
├── stackoverflow.com-Votes.7z         # ~4GB压缩
├── stackoverflow.com-Comments.7z      # ~6GB压缩
├── stackoverflow.com-Tags.7z          # ~50MB
├── math.stackexchange.com-Posts.7z    # 对照社区
├── superuser.com-Posts.7z             # 对照社区
└── serverfault.com-Posts.7z           # 对照社区
```

### 解析后数据（Parquet格式）
```
data/parquet/
├── so_posts/          # 分片，每片~500MB
│   ├── part-0000.parquet
│   ├── part-0001.parquet
│   └── ...
├── so_users.parquet
├── so_votes/          # 分片
├── so_comments/       # 分片
├── mathse_posts/
├── superuser_posts/
└── serverfault_posts/
```

### 特征数据
```
data/features/
├── weekly_stats.parquet      # 周级别聚合统计（核心分析数据）
├── posts_features.parquet    # 帖子级别特征
├── user_cohorts.parquet      # 用户队列特征
└── ai_timeline.csv           # AI工具能力指数时间序列
```

---

## 各模块调用方式

### 第一步：XML解析（必须先运行）
```bash
# 解析Stack Overflow Posts（最大，约需2-4小时）
python pipeline/01_parse_xml.py --source Posts --community so --output data/parquet/

# 解析其他表
python pipeline/01_parse_xml.py --source Users --community so --output data/parquet/
python pipeline/01_parse_xml.py --source Votes --community so --output data/parquet/
python pipeline/01_parse_xml.py --source Comments --community so --output data/parquet/

# 解析对照社区
python pipeline/01_parse_xml.py --source Posts --community mathse --output data/parquet/
python pipeline/01_parse_xml.py --source Posts --community superuser --output data/parquet/
python pipeline/01_parse_xml.py --source Posts --community serverfault --output data/parquet/

# 断点续处理（如果中途中断）
python pipeline/01_parse_xml.py --source Posts --community so --output data/parquet/ --resume
```

### 第二步：特征构建
```bash
python pipeline/02_build_features.py --input data/parquet/ --output data/features/

# 只重建某类特征
python pipeline/02_build_features.py --feature-type time --output data/features/
python pipeline/02_build_features.py --feature-type content --output data/features/
python pipeline/02_build_features.py --feature-type user --output data/features/
```

### 第三步：AI时间线
```bash
python pipeline/03_ai_timeline.py --output data/features/ai_timeline.csv
```

### 第四步：运行分析（可独立运行）
```bash
# 描述统计（先运行，验证数据正确性）
python analysis/01_descriptive.py --features data/features/ --output results/figures/descriptive/

# 事件研究
python analysis/02_event_study.py --features data/features/ --output results/figures/event_study/

# 双重差分
python analysis/03_did_analysis.py --features data/features/ --output results/figures/did/

# 知识复杂度
python analysis/04_knowledge_complexity.py --features data/features/ --output results/figures/complexity/

# 用户生存分析
python analysis/05_user_survival.py --features data/features/ --output results/figures/survival/

# 生成论文表格
python results/paper_tables.py --features data/features/ --output results/tables/
```

---

## 输出规范

### 图表标准
- **格式：** PDF（矢量，用于论文）+ PNG（1200dpi，用于预览）
- **风格：** 白底，无网格线或浅灰网格，Nature/Science期刊风格
- **字体：** Times New Roman（英文正文）/ Source Han Serif（中文注释）
- **尺寸：** 单栏图 3.5×2.5 英寸；双栏图 7×4 英寸
- **颜色：** 使用 `seaborn.color_palette("deep")` 或定制调色板
- **AI事件标注：** 垂直虚线 + 文字标注，颜色按generation区分

### 回归结果标准
- 必须报告：系数、标准误（括号内）、95% CI、p值
- 显著性星号：`***` p<0.001, `**` p<0.01, `*` p<0.05
- 标准误类型必须注明（OLS/Newey-West/聚类）
- 样本量 N 和 R² 必须报告

### 文件命名规范
```
results/figures/descriptive/fig01_so_weekly_trend.pdf
results/figures/descriptive/fig02_community_comparison.pdf
results/figures/event_study/fig03_car_chatgpt.pdf
results/tables/table1_descriptive.tex
results/tables/table3_did_main.tex
```

---

## ⚠️ 注意事项

### 大文件处理（最重要！）
1. **绝对不要** `pd.read_csv()` 或 `pd.read_xml()` 读取整个Posts.xml（会OOM崩溃）
2. 使用 `xml.etree.ElementTree.iterparse()` 流式解析
3. Parquet分片读取用 `pyarrow.dataset.dataset()` 或 `dask.dataframe.read_parquet()`
4. 对于特征构建，用 `chunksize` 参数分批处理

### 内存限制
- 假设可用内存：32GB（保守估计）
- Posts数据：每次处理不超过500万行（约4GB内存）
- 聚合操作：优先在数据库层（DuckDB）完成，不要全量加载

### 推荐工具链
```python
# 大数据处理优先使用
import duckdb           # SQL查询，比pandas快10-100倍，内存效率高
import pyarrow.dataset  # 大型Parquet文件
import polars           # 如果需要比pandas更快的DataFrame操作

# 可视化
import matplotlib.pyplot as plt
import seaborn as sns

# 计量分析
import statsmodels.api as sm
from linearmodels.panel import PanelOLS  # 面板数据
from lifelines import KaplanMeierFitter, CoxPHFitter  # 生存分析
```

### DuckDB 推荐查询模式
```python
import duckdb

# 直接查询Parquet文件，无需加载到内存
conn = duckdb.connect()
df = conn.execute("""
    SELECT 
        date_trunc('week', CreationDate) as week,
        COUNT(*) as question_count
    FROM read_parquet('data/parquet/so_posts/part-*.parquet')
    WHERE PostTypeId = 1
    GROUP BY 1
    ORDER BY 1
""").df()
```

### 断点续处理
- 所有pipeline脚本支持 `--resume` 参数
- 进度保存到 `data/.progress/` 目录
- 每处理100万行保存一次checkpoint

### 随机种子
- 所有涉及随机性的地方设置 `random_state=42`
- Bootstrap / 置换检验：`np.random.seed(42)`

---

## 常见问题

**Q: Posts.7z解压失败怎么办？**
A: 确认py7zr版本 >= 0.20.0；如果内存不足，改用系统7z命令行 `7z x`

**Q: Parquet文件损坏怎么办？**
A: 删除对应分片，从断点重新运行 `--resume`

**Q: 某个分析模块报KeyError？**
A: 先运行 `analysis/01_descriptive.py`，它会验证数据完整性

**Q: DID结果不显著？**
A: 检查平行趋势（运行预处理期安慰剂检验），可能需要控制更多固定效应

---

*本文件由项目设计文档自动生成，如有修改请同步更新 RESEARCH.md*
