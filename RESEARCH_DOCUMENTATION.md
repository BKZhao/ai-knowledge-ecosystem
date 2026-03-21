# AI与知识生态系统：研究文档

**Research Documentation: AI and the Knowledge Ecosystem**

赵炳坤 | 香港城市大学 | 2026年3月

---

## 一、研究问题（Research Question）

### 1.1 核心问题

**主要研究问题：**
生成式AI工具的大规模普及，如何因果性地改变了开发者在知识平台上的行为？这种变化是AI对"内容"的精准替代，还是对"行为习惯"的系统性重塑？

**三个子问题：**
1. ChatGPT发布后，Stack Overflow与GitHub的平台活跃度发生了怎样的变化？变化幅度、方向、速度各是什么？
2. 这种变化在不同编程语言社区之间是否存在异质性？AI的内容可替代能力（ARI）是否能解释这种异质性？
3. GitHub数量爆增的背后，知识质量是否同步变化？社区参与指标呈现何种模式？

### 1.2 研究贡献

1. **实证贡献**：提供迄今最系统的跨平台、长时序、多语言AI冲击证据（2018-2026年）
2. **理论贡献**：提出DKB/AKB框架，区分依赖性与自主性知识行为，识别三种机制（替代/激活/稀释）
3. **反直觉发现**：Benchmark-ARI与SO下降无显著相关（r=0.109, p=0.736），颠覆"AI精准替代容易问题"的常识假设

---

## 二、研究设计（Research Design）

### 2.1 总体框架

本研究采用**自然实验（Natural Experiment）**框架，以ChatGPT发布（2022年11月）作为准外生冲击（quasi-exogenous shock），通过多种因果识别策略估计AI工具对知识平台行为的净因果效应。

**识别策略层级：**
```
Level 1: 跨平台DID（SO vs GitHub，处理组 vs 控制组）
Level 2: 跨社区DID（编程技术社区 vs 非技术SE社区）
Level 3: 事件研究（逐月动态效应，检验平行趋势）
Level 4: 安慰剂检验（全时间线假处理期）
Level 5: ARI异质性分析（Benchmark-ARI稳健性）
```

### 2.2 处理变量设定

**主处理变量（Treatment）：**
- `treat = 1` 当 `month ≥ 2022-11` 且 `platform = SO`
  - 捕捉ChatGPT对SO活跃度的抑制效应（β₁）
- `treat_x_github = 1` 当 `month ≥ 2022-11` 且 `platform = GitHub`
  - 捕捉ChatGPT对GitHub活跃度的激活效应（β₂）

**ChatGPT选择依据：**
- 2022年11月30日是ChatGPT公开发布日期（t=0基准点）
- 此前：GitHub Copilot Beta（2021年10月）、Copilot GA（2022年6月）
- 此后：GPT-4（2023年3月）、Copilot GA企业版（2023年9月）、GPT-4o（2024年5月）
- ChatGPT是首个面向大众的通用AI编程助手，构成最清晰的处理节点

### 2.3 结果变量

**主要结果变量：**
- `ln_activity = log(1 + 月度平台活跃量)`
  - SO：月均周提问量（来自SO API，原始单位：题/周）
  - GitHub：月新建仓库数（来自GitHub REST API）
  - 对数变换：减少异方差，使系数可解读为百分比效应

**辅助结果变量（机制验证）：**
- SO问题平均得分（avg_score）
- SO平均浏览量（avg_views）
- SO回答率（pct_answered）
- SO接受率（pct_accepted）
- SO平均问题长度（avg_length）
- GitHub Fork率（forked/total）
- GitHub Star率（starred/total）
- GitHub Issue/Repo比率

---

## 三、数据来源（Data Sources）

### 3.1 Stack Overflow 周度数据

| 属性 | 内容 |
|------|------|
| 来源 | Stack Exchange API v2.3 |
| 端点 | `/questions?site=stackoverflow&fromdate=&todate=&filter=total` |
| 时间跨度 | 2018年1月1日 — 2026年2月23日（424周） |
| 覆盖语言 | 14种（Python/JavaScript/TypeScript/Java/C#/Go/Rust/C++/C/R/Ruby/Haskell/Assembly等） |
| 采集方式 | 按语言Tag筛选，每周滚动采集 |
| API Key | rl_4L6CL2TNw1KLXeYnWRu3SQRt3（已达配额上限，后备使用代理）|
| 文件 | `results/weekly_api_stats.csv`（426行×13列）|

### 3.2 GitHub 月度数据

| 属性 | 内容 |
|------|------|
| 来源 | GitHub REST API v3 |
| 端点 | `/search/repositories?q=language:{lang}&sort=updated&per_page=100` |
| 时间跨度 | 2018年1月 — 2026年2月（98个月） |
| 覆盖语言 | 13种 |
| 指标 | 月新建仓库数、月新Issue数 |
| 文件 | `results/github_monthly_stats.csv`（98行×28列）|

### 3.3 GitHub 质量指标数据

| 属性 | 内容 |
|------|------|
| 来源 | GitHub REST API（fork/star/activity端点）|
| 时间跨度 | 2018年1月 — 2026年2月 |
| 指标 | 每月：total/forked/starred/active仓库数量 |
| 覆盖语言 | 10种 |
| 文件 | `results/github_quality_metrics.csv` |

### 3.4 Stack Overflow 原始帖子数据（Parquet）

| 属性 | 内容 |
|------|------|
| 来源 | Stack Exchange Data Dump（XML）解析后入库 |
| 时间跨度 | 2018年1月 — 2024年3月 |
| 规模 | 9,554,774条问题帖（PostTypeId=1）|
| 字段 | Id/PostTypeId/CreationDate/Score/ViewCount/Tags/AnswerCount/HasAccepted/OwnerUserId/BodyLength/CodeBlockCount |
| 文件 | `data/parquet/posts_2018plus.parquet` |
| 用途 | 质量指标提取、LLM问题类型分类 |

### 3.5 SE社区对照数据（21个社区）

| 属性 | 内容 |
|------|------|
| 来源 | SE官方数据转储（archive.org，截至2024年3月）|
| 社区数量 | 21个（含SO、Math、Physics、Stats、English、Law等）|
| 时间跨度 | 各社区建立时间 — 2024年3月 |
| 格式 | 解压XML → 月度聚合CSV |
| 文件 | `results/{site}_monthly.csv` |
| 用途 | 非技术社区作为自然对照组 |

**21个社区分类：**
- **编程技术**：Stack Overflow（主处理组）
- **技术周边**：Data Science SE、AI SE
- **硬科学**：Physics、Chemistry、Biology、Astronomy、Statistics、Cognitive Science
- **人文语言**：English、Linguistics、Literature
- **社会科学**：Economics、Law、Politics、Academia
- **文化娱乐**：History、Philosophy、Cooking、Music、Movies、Travel（最佳对照组）

### 3.6 Google Trends 数据

| 属性 | 内容 |
|------|------|
| 关键词 | ChatGPT/GitHub Copilot/GPT-4/AI coding/Claude AI/Cursor IDE等7词 |
| 时间跨度 | 2018年1月 — 2026年2月 |
| 用途 | AI工具采用度控制变量；因果链条验证 |
| 文件 | `results/google_trends.csv` |

### 3.7 LLM问题类型标注数据

| 属性 | 内容 |
|------|------|
| 标注模型 | DeepSeek-V3（硅基流动代理，HumanEval-grade）|
| 标注规模 | 98,000条（每年14,000条，2018-2024均匀抽样）|
| 类型体系 | 4类：How-to/Debug/Conceptual/Architecture |
| 并发方式 | 5线程并行，速率~7,800条/h |
| 当前进度 | ~50,000/98,000（截至2026-03-21上午）|
| 文件 | `results/classification_100k_progress.json` |

### 3.8 Benchmark-ARI 数据

| 属性 | 内容 |
|------|------|
| 来源1 | HumanEvalPack（Muennighoff et al., NeurIPS 2023）|
| 来源2 | MultiPL-E（Cassano et al., TMLR 2022）|
| 模型 | GPT-4 / DeepSeek-Coder-33B / StarCoder2-15B 三模型平均 |
| 覆盖语言 | 13种 |
| 计算方式 | 三模型pass@1均值 → min-max归一化到[0,1] |
| 文件 | `results/benchmark_ari.json` |

---

## 四、控制变量（Control Variables）

### 4.1 事件类控制变量

| 变量 | 含义 | 构造方式 |
|------|------|---------|
| `covid_peak` | COVID-19居家办公峰期 | 2020-03至2021-06 = 1 |
| `tech_layoff` | 科技裁员浪潮 | 2022-Q4至2023-Q2 = 1 |
| `so_ai_ban` | SO宣布限制AI内容 | 2023-05后 = 1 |
| `so_strike` | SO版主罢工事件 | 2023-06至2023-08 = 1 |
| `post_chatgpt` | ChatGPT发布后 | 2022-12后 = 1 |
| `post_copilot_ga` | Copilot正式发布后 | 2022-07后 = 1 |
| `post_gpt4` | GPT-4发布后 | 2023-04后 = 1 |

### 4.2 语言特征控制变量

| 变量 | 含义 |
|------|------|
| `ari` | Benchmark-ARI（LLM代码生成能力，0-1）|
| `high_ari` | ARI ≥ 0.75（二值，Python/JS/TS/Java/C#/Go）|
| `lang_fe` | 语言固定效应（13个语言虚拟变量）|

### 4.3 平台与时间控制

| 变量 | 含义 |
|------|------|
| `github_dummy` | GitHub平台标识（=1）|
| `platform_fe` | 平台固定效应 |
| `time_fe` | 时间固定效应（月份虚拟变量，98个）|
| `ai_capability_index` | AI能力综合指数（Google Trends 7词均值）|

---

## 五、模型设定（Model Specification）

### 5.1 主模型（M3：完整固定效应DID）

$$\ln Y_{l,p,t} = \alpha + \beta_1 \cdot \text{treat}_{l,p,t} + \beta_2 \cdot \text{treat\_x\_github}_{l,p,t} + \gamma_l + \delta_t + \theta_p + \varepsilon_{l,p,t}$$

**符号说明：**
- $Y_{l,p,t}$：语言 $l$、平台 $p$、月份 $t$ 的活跃量
- $\text{treat}_{l,p,t} = \mathbb{1}[t \geq 2022\text{-}11] \times \mathbb{1}[p = \text{SO}]$
- $\text{treat\_x\_github}_{l,p,t} = \mathbb{1}[t \geq 2022\text{-}11] \times \mathbb{1}[p = \text{GitHub}]$
- $\gamma_l$：语言固定效应（13个）
- $\delta_t$：时间固定效应（98个月）
- $\theta_p$：平台固定效应（2个）
- 标准误：HC1异方差稳健标准误（按语言聚类）

**解释：**
- $\beta_1$：SO平台ChatGPT后的活跃度变化（对数单位）
- $\beta_2$：GitHub平台ChatGPT后相对于SO的额外变化（DID差中差估计量）
- 以非技术内容（对照：无ChatGPT前GitHub增长）作为基准

### 5.2 各模型规格对比

| 模型 | 规格 | β₁ | β₂ | R² |
|------|------|-----|-----|-----|
| M1 基础DID | 仅语言FE | −4.718*** | +7.311*** | 0.726 |
| M2 时间FE | +月份FE | −4.168*** | +7.313*** | 0.737 |
| M3 完整FE（主） | +平台FE | **−2.258*** | **+3.823*** | **0.888** |
| M4 ARI交互 | +ARI异质性 | −2.363*** | +2.841*** | 0.891 |
| M5 仅SO | SO子样本 | −0.796*** | — | 0.968 |
| M6 仅GitHub | GitHub子样本 | — | +0.654*** | 0.962 |

### 5.3 ARI异质性模型（M4）

$$\ln Y_{l,p,t} = \alpha + \beta_1 \text{treat} + \beta_2 \text{treat\_gh} + \beta_3 (\text{treat} \times \text{high\_ari}) + \beta_4 (\text{treat\_gh} \times \text{high\_ari}) + \gamma_l + \delta_t + \theta_p + \varepsilon$$

**M4结果（Benchmark-ARI）：**
- $\beta_3 = -0.188$（p=0.347，**不显著**）→ 高ARI语言SO下降幅度与低ARI语言无统计差异
- 这是反直觉①的正式计量检验证明

### 5.4 事件研究模型

$$\ln Y_{l,t} = \sum_{\tau=-24}^{+28} \beta_\tau \cdot \mathbb{1}[t - t_0 = \tau] + \gamma_l + \varepsilon_{l,t}$$

- $t_0$：ChatGPT发布月（2022-11，$\tau=-1$为基准期）
- $\beta_\tau$：相对于基准期的处理效应
- 验证：$\tau < 0$ 期间 $\beta_\tau \approx 0$（平行趋势）

### 5.5 SE跨社区DID（第二识别策略）

$$\text{Activity}_{c,t} = \alpha + \beta \cdot \text{treat}_c \times \text{post}_t + \gamma_c + \delta_t + \varepsilon_{c,t}$$

- $c$：社区（SO=处理组；非技术SE社区=对照组）
- DID估计：$\hat{\beta} = -39.2\text{pp}$（SO比非技术社区多下降39.2个百分点）

---

## 六、因果识别策略（Causal Identification）

### 6.1 平行趋势检验（Parallel Trends）

**方法：** 事件研究图，检验 $t < 0$ 期间系数是否平坦

**结果：** $\tau = -24$ 至 $\tau = -1$ 期间，系数在0附近随机波动，无显著预处理趋势（F检验通过）

**意义：** 验证了DID的核心识别假设——若无ChatGPT，SO与GitHub的活跃度趋势会保持平行

### 6.2 全时间线安慰剂检验（Placebo Test）

**方法：** 将所有季度节点（2019-2025年，每季度一个）作为假处理期，估计对应的"处理效应"

**结果：** 非ChatGPT节点的效应均在±2σ范围内波动（均值≈0，标准差≈小）；真实ChatGPT节点效应为>3σ的显著离群值

**意义：** 排除了"随机时间节点也能产生类似效应"的竞争假说

### 6.3 非技术SE社区对照（Control Group DID）

**设计：** 21个SE社区中，非技术类（哲学/旅游/烹饪等）作为天然对照组——不受AI编程工具直接冲击

**结果：**
- SO下降：−53.6%
- 非技术SE均值：−14.4%
- DID净效应：**−39.2pp**（ChatGPT对编程社区的净因果冲击）

**意义：** 即便控制了"整体平台疲软"的共同趋势，SO仍有额外的39pp下降

### 6.4 加速模式验证（Acceleration Pattern）

**设计：** 如果ChatGPT效应是一次性冲击后平台适应，应该看到下降减速或反弹；如果是持续行为替代，应该看到持续加速

**结果：**
- 2023年同比：−41%
- 2024年同比：−49%
- 2025年同比：−70%
- 无任何季度出现反弹

**意义：** 支持"结构性行为替代"假说，排除"一次性冲击后适应"假说

---

## 七、理论框架（Theoretical Framework）

### 7.1 DKB/AKB框架

**依赖性知识行为（DKB, Dependent Knowledge Behaviors）**
- 定义：依赖外部验证的知识求助活动
- 特征：被动反应式，由外部问题触发
- 典型行为：SO提问（"我不会，问别人"）、GitHub Issue（"这个bug我解决不了"）
- AI机制：**替代（Substitution）** — AI直接满足求助需求，DKB消失

**自主性知识行为（AKB, Autonomous Knowledge Behaviors）**
- 定义：由内在动机驱动的知识创造活动
- 特征：主动创造式，由目标驱动
- 典型行为：GitHub仓库创建（"我要做一个项目"）
- AI机制：**激活（Activation）** — AI降低创作门槛，AKB增强

**质量稀释机制（Quality Dilution）**
- 来源：AKB激活导致低参与度项目涌入
- 表现：GitHub数量+139%，但Fork率−8pp，Star率−8pp，Issue/Repo比率−35%
- 含义：AI激活的AKB在量上增加，但社区参与密度（质量）下降

### 7.2 行为替代 vs 内容替代

**传统假说（内容替代论）：**
> AI替代了"容易被AI回答"的内容 → 高ARI语言/类型下降更多

**本研究发现（行为替代论）：**
> AI改变了"遇到问题就去提问"这一行为模式本身 → 与内容可替代性无关

**证据：**
1. Benchmark-ARI与SO下降：r=0.109，p=0.736（不显著）
2. M4模型交互项：β₃=−0.188，p=0.347（不显著）
3. How-to类型下降幅度与Conceptual类型无显著差异（待全量数据验证）

---

## 八、主要结论（Main Findings）

### 8.1 核心数量结果

| 指标 | 数值 | 置信度 |
|------|------|--------|
| SO提问量变化（ChatGPT后）| −75.4% | N=424周 |
| GitHub仓库增长（ChatGPT后）| +138.7% | N=98月 |
| DID β₁（SO效应） | −2.258 | p<0.001*** |
| DID β₂（GitHub效应）| +3.823 | p<0.001*** |
| 模型拟合R² | 0.888 | N=2,390 |
| DID净效应（跨社区）| −39.2pp | 21个社区 |

### 8.2 五个反直觉发现

**① ARI无关性（最重要）**
> Benchmark-ARI与SO下降幅度不相关（r=0.109, p=0.736）
> 含义：AI改变行为习惯，而非精准替代某类内容

**② 问题变长（质量筛选）**
> ChatGPT后SO问题平均长度+16%（1,590→1,850字符）
> 含义：简单问题被AI吸走，留在SO的是AI无法解决的复杂问题

**③ 哲学/旅游逆势增长（选择性冲击）**
> Philosophy SE +53.6%，Travel SE +13.3%
> 含义：AI的冲击精准针对"工具性/程序性"求助，对"思辨性/体验性"内容几乎无影响

**④ SE社区分层梯度（梯度替代）**
> 编程−53.6% > 硬科学−32.1% > 人文−31.0% > 社会科学−16.0% > 文化−12.7%
> 含义：下降幅度与该领域的"程序性/可执行性"正相关

**⑤ GitHub"虚假繁荣"（质量稀释）**
> 仓库+139%，但Fork率−8pp，Star率−8pp，Issue/Repo−35%
> 含义：数量增加不等于生态繁荣，AI激活了低参与度的"幽灵仓库"

### 8.3 机制验证小结

| 机制 | 测量 | 方向 | 量级 |
|------|------|------|------|
| 替代（DKB消失）| SO提问量 | ↓ | −75.4% |
| 替代（DKB消失）| GitHub Issue/Repo | ↓ | −35% |
| 激活（AKB增强）| GitHub仓库数 | ↑ | +139% |
| 稀释（质量下降）| Fork率 | ↓ | −8pp |
| 稀释（质量下降）| Star率 | ↓ | −8pp |
| 稀释（质量下降）| SO浏览量 | ↓ | −77% |

---

## 九、局限性与待完成工作

### 9.1 现有局限

1. **GitHub增长的识别问题**：GitHub可能在ChatGPT前就有增长趋势，β₂的识别需要更强的控制组（已用SE社区DID部分解决）

2. **SE对照数据时间缺口**：非技术SE社区数据截至2024年3月（archive.org数据转储周期），2024-2026年缺失。解决方案：本机运行补数据脚本（fetch_se_2024_2026.py）

3. **LLM分类未完成**：10万条问题类型分类仍在进行中（当前50%），How-to vs Conceptual的跨期对比尚未完成

4. **GitHub的另一维度**：Issue数量作为DKB的第二测量维度，虽然趋势数据已有，但未纳入主回归

### 9.2 已规划的后续分析

- [ ] SE 2024-2026数据补充（需本机运行脚本）
- [ ] LLM分类完成后的类型比例变化分析（验证反直觉①的机制）
- [ ] 合成控制法（Synthetic Control Method）作为DID的补充
- [ ] 平台逃离路径分析：用户去了哪里（创作者转型 vs 完全退出）

---

## 十、数据和代码可用性

**GitHub仓库：** https://github.com/BKZhao/ai-knowledge-ecosystem（Private）

**主要代码文件：**
- `classify_100k.py` / `classify_parallel.py`：LLM分类
- `run_regressions.py` / `run_regressions_v2.py`：DID回归
- `generate_final_figs.py`：主结果图
- `generate_paper_figures.py`：论文图

**主要数据文件：**
- `results/stacked_panel.csv`：DID主分析面板（2390行×21列）
- `results/weekly_api_stats.csv`：SO周度数据
- `results/github_monthly_stats.csv`：GitHub月度数据
- `results/benchmark_ari.json`：Benchmark-ARI数据（含来源说明）
- `results/so_quality_monthly.csv`：SO质量指标月度数据

---

*文档更新时间：2026年3月21日*
*研究者：赵炳坤（bingkzhao2-c@my.cityu.edu.hk）*
