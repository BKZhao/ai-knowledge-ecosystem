# =============================================================================
# 00_setup.R — 数据加载与全局配置
# =============================================================================
# 所有分析R脚本统一 source("R/00_setup.R")
# 工作目录设为项目根目录：stackoverflow_research/
# =============================================================================

# ---- 安装并加载依赖包 ----
if (!require("pacman")) install.packages("pacman")
pacman::p_load(
  tidyverse,     # ggplot2, dplyr, tidyr, readr, purrr, tibble
  fixest,        # 高速固定效应回归 (feols)
  sandwich,      # 稳健标准误
  lmtest,        # 系数检验 (coeftest)
  jsonlite,      # JSON读写
  data.table,    # 快速数据读取
  scales,        # 图表美化
  patchwork,     # 图表拼接
  broom,         # tidy模型输出
  ggpubr,        # 出版级图表
  here,          # 项目路径管理
  knitr          # LaTeX表格 (kable)
)

# ---- 项目路径 ----
PROJ_ROOT <- here::here("stackoverflow_research")
RESULTS_DIR <- file.path(PROJ_ROOT, "results")
FIG_DIR <- file.path(RESULTS_DIR, "figures")
DATA_DIR <- file.path(PROJ_ROOT, "data")
FEATURES_DIR <- file.path(DATA_DIR, "features")
PROCESSED_DIR <- file.path(DATA_DIR, "processed")
TABLES_DIR <- file.path(RESULTS_DIR, "tables")

# 确保输出目录存在
dir_create <- function(...) {
  for (d in list(...)) if (!dir.exists(d)) dir.create(d, recursive = TRUE)
}
dir_create(FIG_DIR, TABLES_DIR)

# ---- AI可替代性指数（HumanEval pass@1 基准）----
AI_REPLACEABILITY <- c(
  # 高可替代性 (>0.75) — 处理组
  python     = 0.92, javascript = 0.87, html = 0.88, css = 0.85,
  typescript = 0.85, java       = 0.81, sql  = 0.80, php = 0.78,
  kotlin     = 0.77, swift      = 0.76,
  # 中等可替代性 (0.40-0.75)
  go = 0.75, ruby = 0.74, scala = 0.72, bash = 0.72, r = 0.70,
  cpp = 0.71, c = 0.68, matlab = 0.65, lua = 0.60, perl = 0.58,
  haskell = 0.55,
  # 低可替代性 (<0.40) — 对照组
  assembly = 0.15, cobol = 0.12, fortran = 0.18, ada = 0.20,
  prolog = 0.25, vhdl = 0.22, verilog = 0.28
)

# 回归中使用的语言子集（有GitHub数据的语言）
AI_REP <- c(
  python = 0.92, javascript = 0.88, typescript = 0.85, java = 0.81,
  csharp = 0.79, go = 0.72, ruby = 0.65, cpp = 0.63, c = 0.60,
  r = 0.58, rust = 0.35, haskell = 0.25, assembly = 0.10
)

# SE社区AI可替代性指数（用于H4跨域分析）
DOMAIN_AI_REP <- c(
  stackoverflow = 0.88, serverfault = 0.75, superuser = 0.70,
  math = 0.78, physics = 0.65, stats = 0.72, biology = 0.55,
  history = 0.40, philosophy = 0.35, economics = 0.60,
  cooking = 0.20, travel = 0.25
)

# ---- 关键日期 ----
CHATGPT_DATE  <- as.Date("2022-11-30")
COPILOT_DATE  <- as.Date("2022-06-21")
GPT4_DATE     <- as.Date("2023-03-14")
CLAUDE3_DATE  <- as.Date("2024-03-04")
COPILOT_BETA  <- as.Date("2021-10-01")

# 处理组/对照组阈值
HIGH_ARI_THRESHOLD <- 0.75
LOW_ARI_THRESHOLD  <- 0.40

# ---- AI事件列表 ----
EVENT_LIST <- tibble(
  date  = c("2021-10-01","2022-06-21","2022-11-30","2023-03-14",
            "2023-07-18","2023-08-25","2024-03-04","2024-06-20"),
  name  = c("GitHub Copilot Beta","GitHub Copilot GA","ChatGPT Launch",
            "GPT-4 Release","Llama 2 Open Source","Code Llama Release",
            "Devin Public Release","Claude 3.5 Sonnet"),
  short = c("Copilot β","Copilot GA","ChatGPT","GPT-4",
            "Llama 2","Code Llama","Devin","Claude 3.5")
) %>% mutate(date = as.Date(date))

# ---- ggplot2 全局主题 ----
theme_pub <- function() {
  theme_minimal(base_size = 11) +
    theme(
      plot.title = element_text(face = "bold", size = 13),
      axis.title = element_text(size = 12),
      axis.text = element_text(size = 10),
      legend.position = "top",
      legend.text = element_text(size = 9),
      panel.grid.minor = element_blank(),
      panel.grid.major = element_line(linewidth = 0.3, linetype = "dashed", alpha = 0.3),
      plot.margin = margin(10, 10, 10, 10)
    )
}

# 出版友好调色板
CB_COLORS <- c("#2166AC", "#D6604D", "#4DAC26", "#762A83", "#F4A582", "#92C5DE")
SO_COLOR <- "#F48024"

# ---- 辅助函数 ----

#' 生成显著性星号
stars <- function(p) {
  case_when(
    p < 0.001 ~ "***",
    p < 0.01  ~ "**",
    p < 0.05  ~ "*",
    p < 0.10  ~ "\u2020",
    TRUE ~ ""
  )
}

#' LaTeX格式显著性星号
latex_stars <- function(p) {
  s <- stars(p)
  if (s == "") "" else paste0("$^{", s, "}$")
}

#' p值中文描述
p_desc_cn <- function(p) {
  case_when(
    p < 0.001 ~ "极显著 (p<0.001)",
    p < 0.01  ~ "高度显著 (p<0.01)",
    p < 0.05  ~ "显著 (p<0.05)",
    p < 0.10  ~ "弱显著 (p<0.10)",
    TRUE ~ sprintf("不显著 (p=%.3f)", p)
  )
}

#' 面板OLS回归（手动去均值 + lm，等价于Python的panel_ols_demean）
#' 用途：当 fixest 不可用时的备选方案
panel_ols_manual <- function(df, y_col, x_cols, fe_cols) {
  cols <- c(y_col, x_cols, fe_cols)
  df2 <- df %>% select(all_of(cols)) %>% drop_na()
  df2[[y_col]] <- as.numeric(df2[[y_col]])
  for (xc in x_cols) df2[[xc]] <- as.numeric(df2[[xc]])
  
  # 手动去均值（within transformation）
  for (fe in fe_cols) {
    group_means <- df2 %>% group_by(!!sym(fe)) %>%
      summarise(across(all_of(c(y_col, x_cols)), mean, na.rm = TRUE), .groups = "drop")
    for (col in c(y_col, x_cols)) {
      gm <- setNames(group_means[[col]], group_means[[fe]])
      df2[[col]] <- df2[[col]] - gm[as.character(df2[[fe]])]
    }
  }
  
  formula <- as.formula(paste(y_col, "~", paste(x_cols, collapse = " + "), "- 1"))
  fit <- lm(formula, data = df2)
  summary_fit <- summary(fit)
  
  list(
    betas   = setNames(coef(fit), x_cols),
    se      = setNames(summary_fit$coefficients[, "Std. Error"], x_cols),
    t       = setNames(summary_fit$coefficients[, "t value"], x_cols),
    p       = setNames(summary_fit$coefficients[, "Pr(>|t|)"], x_cols),
    r2      = summary_fit$r.squared,
    n       = nrow(df2),
    df_resid = fit$df.residual
  )
}

#' 使用 fixest 进行面板固定效应回归（推荐）
panel_feols <- function(df, y_col, x_cols, fe_cols, cluster = NULL) {
  formula <- as.formula(paste(
    y_col, "~", paste(x_cols, collapse = " + "),
    "|", paste(fe_cols, collapse = " + ")
  ))
  if (!is.null(cluster)) {
    fit <- feols(formula, data = df, cluster = !!sym(cluster))
  } else {
    fit <- feols(formula, data = df)
  }
  tidy_fit <- broom::tidy(fit)
  
  list(
    betas    = setNames(tidy_fit$estimate, tidy_fit$term),
    se       = setNames(tidy_fit$std.error, tidy_fit$term),
    t        = setNames(tidy_fit$statistic, tidy_fit$term),
    p        = setNames(tidy_fit$p.value, tidy_fit$term),
    r2       = summary(fit)$r2,
    n        = nobs(fit),
    df_resid = fit$df.residual,
    fit      = fit
  )
}

#' 简单OLS（等价于Python的simple_ols）
simple_ols <- function(y, x) {
  fit <- lm(y ~ x)
  s <- summary(fit)
  coefs <- s$coefficients
  list(
    betas = c(intercept = coefs["(Intercept)", "Estimate"],
              slope     = coefs["x", "Estimate"]),
    se    = c(intercept = coefs["(Intercept)", "Std. Error"],
              slope     = coefs["x", "Std. Error"]),
    t     = c(intercept = coefs["(Intercept)", "t value"],
              slope     = coefs["x", "t value"]),
    p     = c(intercept = coefs["(Intercept)", "Pr(>|t|)"],
              slope     = coefs["x", "Pr(>|t|)"]),
    r2    = s$r.squared,
    n     = nobs(fit)
  )
}

# =============================================================================
# 数据加载
# =============================================================================
cat("正在加载数据...\n")

# ---- 面板数据（主分析数据）----
panel_path <- file.path(RESULTS_DIR, "stacked_panel.csv")
if (file.exists(panel_path)) {
  panel_df <- fread(panel_path) %>%
    mutate(month = as.Date(month))
  cat(sprintf("  ✓ stacked_panel.csv: %s 行\n", format(nrow(panel_df), big.mark = ",")))
} else {
  warning("未找到 stacked_panel.csv，请先运行Python pipeline生成数据")
  panel_df <- tibble()
}

# ---- SE面板数据（跨域分析用）----
se_panel_path <- file.path(PROCESSED_DIR, "se_panel_complete_2018_2026.csv")
if (file.exists(se_panel_path)) {
  se_panel_df <- fread(se_panel_path) %>%
    mutate(month = as.Date(paste0(month, "-01")))
  cat(sprintf("  ✓ se_panel_complete: %s 行\n", format(nrow(se_panel_df), big.mark = ",")))
} else {
  se_panel_df <- tibble()
}

# ---- 控制变量 ----
ctrl_path <- file.path(RESULTS_DIR, "control_variables.csv")
if (file.exists(ctrl_path)) {
  ctrl_df <- fread(ctrl_path) %>%
    mutate(week_dt = as.Date(week_dt))
  ctrl_monthly <- ctrl_df %>%
    mutate(month = floor_date(week_dt, "month")) %>%
    group_by(month) %>%
    summarise(covid_peak = max(covid_peak, na.rm = TRUE),
              tech_layoff = max(tech_layoff, na.rm = TRUE), .groups = "drop") %>%
    mutate(across(c(covid_peak, tech_layoff), ~replace_na(., 0)))
  cat("  ✓ control_variables.csv\n")
} else {
  ctrl_monthly <- tibble(month = as.Date(character()), covid_peak = 0, tech_layoff = 0)
}

# ---- GitHub周缓存（H2/H3/H6用）----
gh_cache_path <- file.path(RESULTS_DIR, "github_cache_weekly.json")
if (file.exists(gh_cache_path)) {
  gh_cache <- fromJSON(gh_cache_path)
  cat("  ✓ github_cache_weekly.json\n")
} else {
  gh_cache <- list()
}

# ---- GitHub质量指标（H3用）----
gh_quality_path <- file.path(RESULTS_DIR, "github_quality_metrics.json")
if (file.exists(gh_quality_path)) {
  gh_quality <- fromJSON(gh_quality_path)
  cat("  ✓ github_quality_metrics.json\n")
} else {
  gh_quality <- list()
}

# ---- SO API周缓存（H5事件研究用）----
so_cache_path <- file.path(RESULTS_DIR, "api_cache_weekly.json")
if (file.exists(so_cache_path)) {
  so_cache <- fromJSON(so_cache_path)
  cat("  ✓ api_cache_weekly.json\n")
} else {
  so_cache <- list()
}

# ---- SE社区数据（H4用）----
se_cache_path <- file.path(RESULTS_DIR, "stackexchange_communities.json")
if (file.exists(se_cache_path)) {
  se_cache <- fromJSON(se_cache_path)
  cat("  ✓ stackexchange_communities.json\n")
} else {
  se_cache <- list()
}

# ---- 月度特征 ----
features_path <- file.path(FEATURES_DIR, "monthly_features.csv")
if (file.exists(features_path)) {
  monthly_features <- fread(features_path) %>%
    mutate(year_month = as.Date(paste0(year_month, "-01")))
  cat(sprintf("  ✓ monthly_features.csv: %s 行\n", nrow(monthly_features)))
} else {
  monthly_features <- tibble()
}

# ---- DID结果（用于表格生成）----
did_path <- file.path(RESULTS_DIR, "did_results.json")
if (file.exists(did_path)) {
  did_results <- fromJSON(did_path)
  cat("  ✓ did_results.json\n")
} else {
  did_results <- list()
}

cat("数据加载完成！\n")
