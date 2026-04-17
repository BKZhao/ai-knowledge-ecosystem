# =============================================================================
# 04_regression.R — 完整回归分析 H2-H6 + 稳健性检验
# =============================================================================
# 对应Python: src/regression/run_regressions_v2.py
# 功能：
#   H2: Issue/Repo Ratio DID
#   H3: Fork/Star Quality Dilution
#   H4: Cross-domain OLS (SE communities)
#   H5: Multi-node Event Study (CAR)
#   H6: Divergent Language Paths
#   Robustness: Placebo, No COVID, Copilot era, ChatGPT era
#   生成6张图 + LaTeX表格
# =============================================================================

source("R/00_setup.R")

cat("=== 完整回归分析 (H2-H6 + Robustness) ===\n\n")

# =============================================================================
# 构建分析数据集
# =============================================================================

# ---- H2: Issue/Repo Ratio 面板 ----
cat("构建H2数据...\n")
gh_issue_rows <- lapply(names(gh_cache), function(month_key) {
  v <- gh_cache[[month_key]]
  month_dt <- as.Date(v$month_dt %||% paste0(month_key, "-01"))
  lapply(names(AI_REP), function(lang) {
    repos <- v[[paste0("repos_", lang)]] %||% 0
    issues <- v[[paste0("issues_", lang)]] %||% 0
    if (repos > 0) {
      tibble(
        month = month_dt, language = lang, repos = repos, issues = issues,
        issue_repo_ratio = issues / repos,
        ari = AI_REP[lang],
        post_chatgpt = as.integer(month_dt >= CHATGPT_DATE)
      )
    }
  })
}) %>% bind_rows()

issue_panel <- gh_issue_rows %>%
  left_join(ctrl_monthly, by = "month") %>%
  mutate(
    across(c(covid_peak, tech_layoff), ~replace_na(., 0)),
    treat_chatgpt = ari * post_chatgpt,
    lang_fe = language,
    time_fe = format(month, "%Y-%m")
  )

# ---- H3: Quality Dilution 面板 ----
cat("构建H3数据...\n")
gh_qual_rows <- lapply(names(gh_quality), function(month_key) {
  v <- gh_quality[[month_key]]
  month_dt <- as.Date(paste0(month_key, "-01"))
  lapply(names(AI_REP), function(lang) {
    total <- v[[paste0("total_", lang)]] %||% 0
    forked <- v[[paste0("forked_", lang)]] %||% 0
    starred <- v[[paste0("starred_", lang)]] %||% 0
    if (total > 0) {
      tibble(
        month = month_dt, language = lang, ari = AI_REP[lang],
        fork_rate = forked / total, star_rate = starred / total,
        post_chatgpt = as.integer(month_dt >= CHATGPT_DATE)
      )
    }
  })
}) %>% bind_rows()

qual_panel <- gh_qual_rows %>%
  mutate(
    treat_chatgpt = ari * post_chatgpt,
    lang_fe = language,
    time_fe = format(month, "%Y-%m")
  )

# ---- H4: SE跨域数据 ----
cat("构建H4数据...\n")
se_df <- bind_rows(lapply(names(se_cache), function(k) {
  v <- se_cache[[k]]
  v$week_dt <- as.Date(v$week_dt)
  as_tibble(v)
})) %>% arrange(week_dt) %>% filter(!is.na(stackoverflow_questions))

baseline_se <- se_df %>% filter(year(week_dt) %in% 2019:2021)
recent_se <- se_df %>% filter(year(week_dt) == 2022, month(week_dt) <= 6)

cross_rows <- lapply(names(DOMAIN_AI_REP), function(comm) {
  col <- paste0(comm, "_questions")
  if (!col %in% names(se_df)) return(NULL)
  pre <- mean(baseline_se[[col]], na.rm = TRUE)
  post <- mean(recent_se[[col]], na.rm = TRUE)
  if (pre > 0 && post > 0) {
    tibble(community = comm, ari = DOMAIN_AI_REP[comm],
           pre_avg = pre, post_avg = post,
           decline_pct = (post - pre) / pre * 100)
  }
}) %>% bind_rows()

# ---- H5: SO事件研究（用api_cache_weekly）----
cat("构建H5数据...\n")
so_df <- bind_rows(lapply(names(so_cache), function(k) {
  v <- so_cache[[k]]
  if (!is.null(v$total_questions) && v$total_questions > 0) {
    tibble(week_dt = as.Date(v$week_dt), total_questions = v$total_questions)
  }
})) %>% arrange(week_dt) %>% distinct(week_dt, .keep_all = TRUE)

h5_events <- list(
  "Copilot GA" = COPILOT_DATE,
  "ChatGPT"    = CHATGPT_DATE,
  "GPT-4"      = GPT4_DATE,
  "Claude 3"   = CLAUDE3_DATE
)

# ---- H6: Repo growth 面板 ----
cat("构建H6数据...\n")
repo_rows <- lapply(names(gh_cache), function(month_key) {
  v <- gh_cache[[month_key]]
  month_dt <- as.Date(v$month_dt %||% paste0(month_key, "-01"))
  lapply(names(AI_REP), function(lang) {
    repos <- v[[paste0("repos_", lang)]]
    if (!is.null(repos) && repos > 0) {
      tibble(
        month = month_dt, language = lang, repos = repos,
        ln_repos = log(repos), ari = AI_REP[lang],
        high_ari = as.integer(AI_REP[lang] >= 0.72),
        post_chatgpt = as.integer(month_dt >= CHATGPT_DATE)
      )
    }
  })
}) %>% bind_rows()

repo_panel <- repo_rows %>%
  mutate(
    treat = ari * post_chatgpt,
    treat_high = ari * post_chatgpt * high_ari,
    lang_fe = language,
    time_fe = format(month, "%Y-%m")
  )

# ---- Robustness: SO面板 ----
so_panel <- panel_df %>%
  filter(platform == "SO") %>%
  mutate(
    lang_fe = language,
    time_fe = format(month, "%Y-%m"),
    treat_interaction = ari * post_chatgpt
  )

cat("数据构建完成！\n\n")

# =============================================================================
# H2: Issue/Repo Ratio DID
# =============================================================================
cat("=== H2 ===\n")

h2_result <- panel_feols(issue_panel, "issue_repo_ratio",
                         c("treat_chatgpt", "covid_peak", "tech_layoff"),
                         c("lang_fe", "time_fe"))
cat(sprintf("H2: β=%.4f, p=%.4f, R²=%.4f, N=%d\n",
            h2_result$betas["treat_chatgpt"], h2_result$p["treat_chatgpt"],
            h2_result$r2, h2_result$n))

# =============================================================================
# H3: Fork/Star Rate Dilution
# =============================================================================
cat("\n=== H3 ===\n")

h3_fork <- panel_feols(qual_panel, "fork_rate", c("post_chatgpt", "treat_chatgpt"),
                       c("lang_fe", "time_fe"))
h3_star <- panel_feols(qual_panel, "star_rate", c("post_chatgpt", "treat_chatgpt"),
                       c("lang_fe", "time_fe"))

cat(sprintf("H3 Fork: β1=%.4f(p=%.3f), β2=%.4f(p=%.4f)\n",
            h3_fork$betas["post_chatgpt"], h3_fork$p["post_chatgpt"],
            h3_fork$betas["treat_chatgpt"], h3_fork$p["treat_chatgpt"]))
cat(sprintf("H3 Star: β1=%.4f(p=%.3f), β2=%.4f(p=%.4f)\n",
            h3_star$betas["post_chatgpt"], h3_star$p["post_chatgpt"],
            h3_star$betas["treat_chatgpt"], h3_star$p["treat_chatgpt"]))

# =============================================================================
# H4: Cross-domain OLS
# =============================================================================
cat("\n=== H4 ===\n")
print(cross_rows %>% select(community, ari, decline_pct))

h4_ols <- simple_ols(cross_df$decline_pct, cross_df$ari)
cat(sprintf("\nH4 OLS: α=%.3f, β=%.3f(SE=%.3f, p=%.4f), R²=%.4f, N=%d\n",
            h4_ols$betas["intercept"], h4_ols$betas["slope"],
            h4_ols$se["slope"], h4_ols$p["slope"], h4_ols$r2, h4_ols$n))

# 修正：使用cross_rows而非cross_df
h4_ols <- simple_ols(cross_rows$decline_pct, cross_rows$ari)
cat(sprintf("H4 OLS (修正): β=%.3f(SE=%.3f, p=%.4f), R²=%.4f, N=%d\n",
            h4_ols$betas["slope"], h4_ols$se["slope"], h4_ols$p["slope"], h4_ols$r2, h4_ols$n))

# =============================================================================
# H5: Multi-node Event Study
# =============================================================================
cat("\n=== H5 ===\n")

car_results <- list()

for (event_name in names(h5_events)) {
  event_date <- h5_events[[event_name]]
  est_start <- event_date - weeks(52)
  est_end   <- event_date - weeks(1)
  evt_end   <- event_date + weeks(24)
  
  est_data <- so_df %>% filter(week_dt >= est_start, week_dt <= est_end) %>% pull(total_questions)
  evt_data <- so_df %>% filter(week_dt > event_date, week_dt <= evt_end) %>% pull(total_questions)
  
  if (length(est_data) < 5) {
    cat(sprintf("  %s: 估计窗口数据不足 (%d)\n", event_name, length(est_data)))
    car_results[[event_name]] <- list(car_24 = 0, n_est = length(est_data), n_evt = 0)
    next
  }
  
  # OLS趋势拟合
  fit_trend <- lm(est_data ~ seq_along(est_data))
  n_evt <- min(24, length(evt_data))
  x_evt <- (length(est_data) + 1):(length(est_data) + n_evt)
  expected <- predict(fit_trend, newdata = data.frame(x = x_evt))
  actual <- head(evt_data, n_evt)
  
  abnormal <- (actual - expected) / pmax(expected, 1) * 100
  car_24 <- sum(abnormal)
  
  car_results[[event_name]] <- list(
    car_24 = car_24, est_mean = mean(est_data),
    n_est = length(est_data), n_evt = n_evt, abnormal = abnormal
  )
  cat(sprintf("  %s: CAR(24)=%.2f%%, est_mean=%.0f\n", event_name, car_24, mean(est_data)))
}

car_values <- sapply(names(h5_events), function(e) car_results[[e]]$car_24)
cat(sprintf("\nCAR values: %s\n", paste(sprintf("%.1f%%", car_values), collapse = ", ")))

# Spearman单调性检验
rho_test <- cor.test(seq_along(car_values), car_values, method = "spearman")
cat(sprintf("Spearman ρ = %.3f, p = %.3f\n", rho_test$estimate, rho_test$p.value))

# =============================================================================
# H6: Divergent Language Paths
# =============================================================================
cat("\n=== H6 ===\n")

h6_result <- panel_feols(repo_panel, "ln_repos", c("treat", "treat_high"),
                         c("lang_fe", "time_fe"))
cat(sprintf("H6: β1=%.4f(p=%.4f), β2=%.4f(p=%.4f), R²=%.4f, N=%d\n",
            h6_result$betas["treat"], h6_result$p["treat"],
            h6_result$betas["treat_high"], h6_result$p["treat_high"],
            h6_result$r2, h6_result$n))

# =============================================================================
# Robustness Checks
# =============================================================================
cat("\n=== Robustness ===\n")

# Placebo
so_pre <- so_panel %>% filter(month < CHATGPT_DATE) %>%
  mutate(
    post_placebo = as.integer(month >= as.Date("2021-06-01")),
    treat_placebo = ari * post_placebo
  )
rob1 <- panel_feols(so_pre, "ln_activity", "treat_placebo", c("lang_fe", "time_fe"))
cat(sprintf("Placebo: β=%.4f, p=%.4f, R²=%.4f, N=%d\n",
            rob1$betas["treat_placebo"], rob1$p["treat_placebo"], rob1$r2, rob1$n))

# No COVID
no_covid <- so_panel %>% filter(!year(month) %in% c(2020, 2021))
rob2 <- panel_feols(no_covid, "ln_activity", "treat_interaction", c("lang_fe", "time_fe"))
cat(sprintf("No COVID: β=%.4f, p=%.4f, R²=%.4f, N=%d\n",
            rob2$betas["treat_interaction"], rob2$p["treat_interaction"], rob2$r2, rob2$n))

# Copilot era
copilot_data <- so_panel %>% filter(year(month) <= 2022) %>%
  mutate(treat_copilot = ari * post_copilot_ga)
rob3 <- panel_feols(copilot_data, "ln_activity", "treat_copilot", c("lang_fe", "time_fe"))
cat(sprintf("Copilot era: β=%.4f, p=%.4f, R²=%.4f, N=%d\n",
            rob3$betas["treat_copilot"], rob3$p["treat_copilot"], rob3$r2, rob3$n))

# ChatGPT era (full)
rob4 <- panel_feols(so_panel, "ln_activity", "treat_interaction", c("lang_fe", "time_fe"))
cat(sprintf("ChatGPT era: β=%.4f, p=%.4f, R²=%.4f, N=%d\n",
            rob4$betas["treat_interaction"], rob4$p["treat_interaction"], rob4$r2, rob4$n))

cat("\n回归分析完成！开始绘图...\n")

# =============================================================================
# FIGURE 1: H2
# =============================================================================
cat("Fig 1...\n")

high_ari_langs <- names(AI_REP)[AI_REP >= 0.72]
low_ari_langs <- names(AI_REP)[AI_REP < 0.72]

high_monthly <- issue_panel %>% filter(language %in% high_ari_langs) %>%
  group_by(month) %>% summarise(ratio = mean(issue_repo_ratio, na.rm = TRUE), .groups = "drop")
low_monthly <- issue_panel %>% filter(language %in% low_ari_langs) %>%
  group_by(month) %>% summarise(ratio = mean(issue_repo_ratio, na.rm = TRUE), .groups = "drop")

p1a <- ggplot() +
  geom_line(data = high_monthly, aes(x = month, y = ratio), color = CB_COLORS[2], linewidth = 1.2) +
  geom_line(data = low_monthly, aes(x = month, y = ratio), color = CB_COLORS[1], linewidth = 1.2) +
  geom_vline(xintercept = CHATGPT_DATE, linetype = "dashed", color = "gray50") +
  labs(title = "(a) Issue Activity by AI Replaceability Group",
       x = "", y = "Issue/Repo Ratio") +
  theme_pub() +
  scale_x_date(date_labels = "%Y", date_breaks = "1 year") +
  theme(axis.text.x = element_text(angle = 30, hjust = 1))

lang_change <- issue_panel %>%
  group_by(language) %>%
  summarise(ari = unique(ari),
            pre_mean = mean(issue_repo_ratio[post_chatgpt == 0], na.rm = TRUE),
            post_mean = mean(issue_repo_ratio[post_chatgpt == 1], na.rm = TRUE),
            .groups = "drop") %>%
  mutate(change_pct = (post_mean - pre_mean) / pre_mean * 100) %>%
  drop_na()

p1b <- ggplot(lang_change, aes(x = ari, y = change_pct)) +
  geom_point(color = CB_COLORS[1], size = 3) +
  geom_text(aes(label = language), vjust = -0.5, size = 3) +
  geom_smooth(method = "lm", se = FALSE, color = CB_COLORS[2], linewidth = 1) +
  geom_hline(yintercept = 0, color = "gray50", linewidth = 0.5) +
  labs(title = "(b) ARI vs Issue Activity Change",
       x = "AI Replaceability Index", y = "Change in Issue/Repo Ratio (%)") +
  theme_pub()

p_fig1 <- p1a + p1b + plot_layout(widths = c(1, 1))
ggsave(file.path(FIG_DIR, "regression_fig1.png"), p_fig1, width = 12, height = 5, dpi = 300)
ggsave(file.path(FIG_DIR, "regression_fig1.pdf"), p_fig1, width = 12, height = 5)
cat("  ✓ regression_fig1\n")

# =============================================================================
# FIGURE 2: H3
# =============================================================================
cat("Fig 2...\n")

high_q <- qual_panel %>% filter(ari >= 0.72) %>%
  group_by(month) %>% summarise(fork = mean(fork_rate), star = mean(star_rate), .groups = "drop")
low_q <- qual_panel %>% filter(ari < 0.72) %>%
  group_by(month) %>% summarise(fork = mean(fork_rate), star = mean(star_rate), .groups = "drop")

p2a <- ggplot() +
  geom_line(data = high_q, aes(x = month, y = fork), color = CB_COLORS[2], linewidth = 1.2) +
  geom_line(data = low_q, aes(x = month, y = fork), color = CB_COLORS[1], linewidth = 1.2) +
  geom_vline(xintercept = CHATGPT_DATE, linetype = "dashed", color = "gray50") +
  labs(title = "Fork Rate by ARI Group", x = "", y = "Fork Rate") + theme_pub()

p2b <- ggplot() +
  geom_line(data = high_q, aes(x = month, y = star), color = CB_COLORS[2], linewidth = 1.2) +
  geom_line(data = low_q, aes(x = month, y = star), color = CB_COLORS[1], linewidth = 1.2) +
  geom_vline(xintercept = CHATGPT_DATE, linetype = "dashed", color = "gray50") +
  labs(title = "Star Rate by ARI Group", x = "", y = "Star Rate") + theme_pub()

p_fig2 <- (p2a + p2b) + plot_annotation(title = "H3: Repository Quality Dilution Effect", theme = theme(plot.title = element_text(face = "bold", size = 12)))
ggsave(file.path(FIG_DIR, "regression_fig2.png"), p_fig2, width = 12, height = 5, dpi = 300)
ggsave(file.path(FIG_DIR, "regression_fig2.pdf"), p_fig2, width = 12, height = 5)
cat("  ✓ regression_fig2\n")

# =============================================================================
# FIGURE 3: H4
# =============================================================================
cat("Fig 3...\n")

p_fig3 <- ggplot(cross_rows, aes(x = ari, y = decline_pct)) +
  geom_point(aes(color = ari >= 0.65), size = 4, shape = 21, stroke = 1.5) +
  geom_text(aes(label = community), vjust = -0.8, hjust = 0.5, size = 3.5) +
  geom_abline(intercept = h4_ols$betas["intercept"], slope = h4_ols$betas["slope"],
              linetype = "dashed", color = "#333333", linewidth = 1) +
  geom_hline(yintercept = 0, color = "gray50", linewidth = 0.5) +
  scale_color_manual(values = c("TRUE" = CB_COLORS[2], "FALSE" = CB_COLORS[1]), guide = "none") +
  annotate("text", x = 0.05, y = 0.05, hjust = 0, vjust = 0,
           label = sprintf("beta = %.2f%s\nR2 = %.3f\nN = %d",
                           h4_ols$betas["slope"], stars(h4_ols$p["slope"]),
                           h4_ols$r2, h4_ols$n),
           size = 3, family = "mono",
           geom = "label", label.size = 0.3, alpha = 0.8) +
  labs(title = "H4: Cross-domain AI Displacement (OLS)",
       x = "Domain AI Replaceability Index", y = "Question Volume Change (%)") +
  theme_pub()

ggsave(file.path(FIG_DIR, "regression_fig3.png"), p_fig3, width = 8, height = 6, dpi = 300)
ggsave(file.path(FIG_DIR, "regression_fig3.pdf"), p_fig3, width = 8, height = 6)
cat("  ✓ regression_fig3\n")

# =============================================================================
# FIGURE 4: H5
# =============================================================================
cat("Fig 4...\n")

car_df <- tibble(
  event = names(h5_events),
  date = as.character(h5_events),
  car_24 = car_values
) %>% mutate(date_label = sub("-", "\n", date))

# 柱状图
p4a <- ggplot(car_df, aes(x = event, y = car_24, fill = car_24 < 0)) +
  geom_col(width = 0.6, color = "white") +
  scale_fill_manual(values = c("TRUE" = CB_COLORS[2], "FALSE" = CB_COLORS[1]), guide = "none") +
  geom_text(aes(label = sprintf("%.1f%%", car_24)), vjust = ifelse(car_df$car_24 >= 0, -0.5, 1.2), size = 3) +
  geom_hline(yintercept = 0, linewidth = 0.8) +
  labs(title = "(a) CAR(24) by AI Event", x = "", y = "Cumulative Abnormal Return (24-week, %)") +
  theme_pub() + theme(axis.text.x = element_text(size = 7))

# 趋势线图
p4b <- ggplot(car_df, aes(x = seq_along(event), y = car_24)) +
  geom_point(color = CB_COLORS[1], size = 4) +
  geom_line(color = CB_COLORS[1], linewidth = 1.5) +
  geom_text(aes(label = sprintf("%.1f%%", car_24)), vjust = -1.5, size = 3) +
  geom_smooth(method = "lm", se = FALSE, color = CB_COLORS[2], linetype = "dashed") +
  geom_hline(yintercept = 0, color = "gray50", linetype = "dashed", linewidth = 0.5) +
  scale_x_continuous(breaks = seq_along(car_df$event), labels = car_df$event) +
  labs(title = sprintf("(b) Monotonicity (rho=%.2f, p=%.3f)", rho_test$estimate, rho_test$p.value),
       x = "", y = "CAR(24) %") + theme_pub()

p_fig4 <- (p4a + p4b) + plot_annotation(title = "H5: Escalating AI Impact -- Multi-node Event Study", theme = theme(plot.title = element_text(face = "bold", size = 12)))
ggsave(file.path(FIG_DIR, "regression_fig4.png"), p_fig4, width = 12, height = 5, dpi = 300)
ggsave(file.path(FIG_DIR, "regression_fig4.pdf"), p_fig4, width = 12, height = 5)
cat("  ✓ regression_fig4\n")

# =============================================================================
# FIGURE 5: H6
# =============================================================================
cat("Fig 5...\n")

repo_monthly <- repo_panel %>%
  group_by(month, language) %>% summarise(ln_repos = first(ln_repos), ari = first(ari), high_ari = first(high_ari), .groups = "drop")

high_repos <- repo_monthly %>% filter(high_ari == 1) %>%
  group_by(month) %>% summarise(ln_repos = mean(ln_repos), .groups = "drop")
low_repos <- repo_monthly %>% filter(high_ari == 0) %>%
  group_by(month) %>% summarise(ln_repos = mean(ln_repos), .groups = "drop")

high_pre <- mean(high_repos$ln_repos[high_repos$month < CHATGPT_DATE])
low_pre <- mean(low_repos$ln_repos[low_repos$month < CHATGPT_DATE])

p5a <- ggplot() +
  geom_line(data = high_repos %>% mutate(dev = ln_repos - high_pre), aes(x = month, y = dev),
            color = CB_COLORS[2], linewidth = 1.2, label = "High ARI") +
  geom_line(data = low_repos %>% mutate(dev = ln_repos - low_pre), aes(x = month, y = dev),
            color = CB_COLORS[1], linewidth = 1.2, label = "Low ARI") +
  geom_vline(xintercept = CHATGPT_DATE, linetype = "dashed", color = "gray50") +
  geom_hline(yintercept = 0, color = "gray50", linewidth = 0.5) +
  labs(title = "(a) Divergent Repository Growth Paths",
       x = "", y = "ln(Repos) - Baseline") + theme_pub()

# 单语言轨迹
lang_styles <- c("python" = CB_COLORS[2], "javascript" = CB_COLORS[2],
                 "ruby" = CB_COLORS[1], "haskell" = CB_COLORS[1])
lang_labels <- c("python" = "Python (KCB+)", "javascript" = "JS (KCB+)",
                 "ruby" = "Ruby (KCB-)", "haskell" = "Haskell (KCB-)")
show_langs <- c("python", "javascript", "ruby", "haskell")

p5b_data <- repo_monthly %>%
  filter(language %in% show_langs) %>%
  left_join(tibble(language = show_langs, pre_mean = sapply(show_langs, function(l) {
    mean(repo_monthly$ln_repos[repo_monthly$language == l & repo_monthly$month < CHATGPT_DATE])
  })), by = "language") %>%
  mutate(dev = ln_repos - pre_mean,
         label = lang_labels[language])

p5b <- ggplot(p5b_data, aes(x = month, y = dev, color = label, linetype = label)) +
  geom_line(linewidth = 1.2) +
  geom_vline(xintercept = CHATGPT_DATE, linetype = "dashed", color = "gray50") +
  geom_hline(yintercept = 0, color = "gray50", linewidth = 0.5) +
  scale_color_manual(values = c(CB_COLORS[2], CB_COLORS[2], CB_COLORS[1], CB_COLORS[1])) +
  scale_linetype_manual(values = c("solid", "dashed", "solid", "dashed")) +
  labs(title = "(b) Individual Language Trajectories",
       x = "", y = "ln(Repos) - Baseline", color = "", linetype = "") +
  theme_pub() + theme(legend.position = "bottom")

p_fig5 <- (p5a + p5b) + plot_annotation(title = "H6: Divergent Language Paths Post-ChatGPT", theme = theme(plot.title = element_text(face = "bold", size = 12)))
ggsave(file.path(FIG_DIR, "regression_fig5.png"), p_fig5, width = 12, height = 5, dpi = 300)
ggsave(file.path(FIG_DIR, "regression_fig5.pdf"), p_fig5, width = 12, height = 5)
cat("  ✓ regression_fig5\n")

# =============================================================================
# FIGURE 6: Robustness
# =============================================================================
cat("Fig 6...\n")

rob_df <- tibble(
  check = c("Placebo\n(2021-06)", "No COVID\n(Excl 2020-21)", "Copilot Era\n(2018-22)", "ChatGPT Era\n(Full)"),
  beta = c(rob1$betas["treat_placebo"], rob2$betas["treat_interaction"],
           rob3$betas["treat_copilot"], rob4$betas["treat_interaction"]),
  se = c(rob1$se["treat_placebo"], rob2$se["treat_interaction"],
         rob3$se["treat_copilot"], rob4$se["treat_interaction"]),
  p = c(rob1$p["treat_placebo"], rob2$p["treat_interaction"],
        rob3$p["treat_copilot"], rob4$p["treat_interaction"]),
  n = c(rob1$n, rob2$n, rob3$n, rob4$n),
  r2 = c(rob1$r2, rob2$r2, rob3$r2, rob4$r2)
)

p_fig6 <- ggplot(rob_df, aes(x = check, y = beta, fill = p < 0.05)) +
  geom_col(width = 0.6, color = "white") +
  geom_errorbar(aes(ymin = beta - se, ymax = beta + se), width = 0.2) +
  geom_text(aes(label = sprintf("%.4f%s", beta, stars(p))), vjust = -0.5, size = 3) +
  geom_hline(yintercept = 0, linewidth = 0.8) +
  scale_fill_manual(values = c("TRUE" = CB_COLORS[2], "FALSE" = "gray70"), guide = "none") +
  labs(title = "Robustness Checks (Dependent Variable: ln(SO Activity))",
       x = "", y = "Coefficient (ARI × Post_Break)") +
  theme_pub() + theme(axis.text.x = element_text(size = 9))

ggsave(file.path(FIG_DIR, "regression_fig6.png"), p_fig6, width = 10, height = 5, dpi = 300)
ggsave(file.path(FIG_DIR, "regression_fig6.pdf"), p_fig6, width = 10, height = 5)
cat("  ✓ regression_fig6\n")

# =============================================================================
# LaTeX表格
# =============================================================================
cat("\n生成LaTeX表格...\n")

fmt_latex <- function(beta, se, p) {
  sprintf("%.4f%s", beta, latex_stars(p))
}

# 这里将回归结果保存为CSV供LaTeX引用，同时生成简单表格
results_table <- tibble(
  hypothesis = c("H2", "H3-Fork", "H3-Star", "H4", "H6-β1", "H6-β2",
                 "Rob:Placebo", "Rob:NoCOVID", "Rob:Copilot", "Rob:ChatGPT"),
  variable = c("treat_chatgpt", "treat_chatgpt", "treat_chatgpt", "ari",
               "treat", "treat_high",
               "treat_placebo", "treat_interaction", "treat_copilot", "treat_interaction"),
  beta = c(h2_result$betas["treat_chatgpt"],
           h3_fork$betas["treat_chatgpt"], h3_star$betas["treat_chatgpt"],
           h4_ols$betas["slope"],
           h6_result$betas["treat"], h6_result$betas["treat_high"],
           rob1$betas["treat_placebo"], rob2$betas["treat_interaction"],
           rob3$betas["treat_copilot"], rob4$betas["treat_interaction"]),
  se = c(h2_result$se["treat_chatgpt"],
         h3_fork$se["treat_chatgpt"], h3_star$se["treat_chatgpt"],
         h4_ols$se["slope"],
         h6_result$se["treat"], h6_result$se["treat_high"],
         rob1$se["treat_placebo"], rob2$se["treat_interaction"],
         rob3$se["treat_copilot"], rob4$se["treat_interaction"]),
  p = c(h2_result$p["treat_chatgpt"],
        h3_fork$p["treat_chatgpt"], h3_star$p["treat_chatgpt"],
        h4_ols$p["slope"],
        h6_result$p["treat"], h6_result$p["treat_high"],
        rob1$p["treat_placebo"], rob2$p["treat_interaction"],
        rob3$p["treat_copilot"], rob4$p["treat_interaction"]),
  r2 = c(h2_result$r2, h3_fork$r2, h3_star$r2, h4_ols$r2,
         h6_result$r2, h6_result$r2,
         rob1$r2, rob2$r2, rob3$r2, rob4$r2),
  n = c(h2_result$n, h3_fork$n, h3_star$n, h4_ols$n,
        h6_result$n, h6_result$n,
        rob1$n, rob2$n, rob3$n, rob4$n)
) %>%
  mutate(sig = stars(p))

print(results_table)
write_csv(results_table, file.path(TABLES_DIR, "regression_results.csv"))

# ---- 生成LaTeX格式表格（与Python版本等价）----
# 由于完整LaTeX生成需要did_results.json，这里生成核心回归表
latex_content <- sprintf(r"""
\documentclass[12pt]{article}
\usepackage{booktabs,multirow,geometry,caption}
\geometry{margin=1in}
\begin{document}
\title{AI Knowledge Ecosystem: Regression Results H2--H6 (R Replication)}
\date{}\maketitle

\begin{table}[htbp]
\centering
\caption{Table 2: H2 --- Issue Collaboration De-socialization}
\begin{tabular}{lc}
\toprule
 & Issue/Repo Ratio \\
\midrule
ARI $\times$ Post\_ChatGPT & %s \\
 & (%s) \\
COVID Peak & %s \\
 & (%s) \\
Tech Layoff & %s \\
 & (%s) \\
\midrule
Language FE & Yes \\
Time FE & Yes \\
$R^2$ & %.4f \\
$N$ & %d \\
\bottomrule
\end{tabular}
\par\smallskip
{\footnotesize $^{***}p<0.001$, $^{**}p<0.01$, $^{*}p<0.05$, $^{\dagger}p<0.10$.}
\end{table}

\begin{table}[htbp]
\centering
\caption{Table 3: H3 --- Repository Quality Dilution}
\begin{tabular}{lcc}
\toprule
 & Fork Rate & Star Rate \\
\midrule
Post\_ChatGPT & %s & %s \\
 & (%s) & (%s) \\
ARI $\times$ Post\_ChatGPT & %s & %s \\
 & (%s) & (%s) \\
\midrule
Language FE & Yes & Yes \\
Time FE & Yes & Yes \\
$R^2$ & %.4f & %.4f \\
$N$ & %d & %d \\
\bottomrule
\end{tabular}
\end{table}

\begin{table}[htbp]
\centering
\caption{Table 6: H6 --- Divergent Language Paths}
\begin{tabular}{lc}
\toprule
 & $\ln$(GitHub Repos) \\
\midrule
ARI $\times$ Post\_ChatGPT & %s \\
 & (%s) \\
ARI $\times$ Post\_ChatGPT $\times$ High\_ARI & %s \\
 & (%s) \\
\midrule
Language FE & Yes \\
Time FE & Yes \\
$R^2$ & %.4f \\
$N$ & %d \\
\bottomrule
\end{tabular}
\end{table}

\begin{table}[htbp]
\centering
\caption{Table 7: Robustness Checks}
\begin{tabular}{lcccc}
\toprule
 & Placebo & No COVID & Copilot & ChatGPT \\
\midrule
ARI $\times$ Post\_Break & %s & %s & %s & %s \\
 & (%s) & (%s) & (%s) & (%s) \\
\midrule
$R^2$ & %.4f & %.4f & %.4f & %.4f \\
$N$ & %d & %d & %d & %d \\
\bottomrule
\end{tabular}
\end{table}

\end{document}
""",
# H2
fmt_latex(h2_result$betas["treat_chatgpt"], h2_result$se["treat_chatgpt"], h2_result$p["treat_chatgpt"]),
h2_result$se["treat_chatgpt"],
fmt_latex(h2_result$betas["covid_peak"], h2_result$se["covid_peak"], h2_result$p["covid_peak"]),
h2_result$se["covid_peak"],
fmt_latex(h2_result$betas["tech_layoff"], h2_result$se["tech_layoff"], h2_result$p["tech_layoff"]),
h2_result$se["tech_layoff"],
h2_result$r2, h2_result$n,
# H3
fmt_latex(h3_fork$betas["post_chatgpt"], h3_fork$se["post_chatgpt"], h3_fork$p["post_chatgpt"]),
fmt_latex(h3_star$betas["post_chatgpt"], h3_star$se["post_chatgpt"], h3_star$p["post_chatgpt"]),
h3_fork$se["post_chatgpt"], h3_star$se["post_chatgpt"],
fmt_latex(h3_fork$betas["treat_chatgpt"], h3_fork$se["treat_chatgpt"], h3_fork$p["treat_chatgpt"]),
fmt_latex(h3_star$betas["treat_chatgpt"], h3_star$se["treat_chatgpt"], h3_star$p["treat_chatgpt"]),
h3_fork$se["treat_chatgpt"], h3_star$se["treat_chatgpt"],
h3_fork$r2, h3_star$r2, h3_fork$n, h3_star$n,
# H6
fmt_latex(h6_result$betas["treat"], h6_result$se["treat"], h6_result$p["treat"]),
h6_result$se["treat"],
fmt_latex(h6_result$betas["treat_high"], h6_result$se["treat_high"], h6_result$p["treat_high"]),
h6_result$se["treat_high"],
h6_result$r2, h6_result$n,
# Robustness
fmt_latex(rob1$betas["treat_placebo"], rob1$se["treat_placebo"], rob1$p["treat_placebo"]),
fmt_latex(rob2$betas["treat_interaction"], rob2$se["treat_interaction"], rob2$p["treat_interaction"]),
fmt_latex(rob3$betas["treat_copilot"], rob3$se["treat_copilot"], rob3$p["treat_copilot"]),
fmt_latex(rob4$betas["treat_interaction"], rob4$se["treat_interaction"], rob4$p["treat_interaction"]),
rob1$se["treat_placebo"], rob2$se["treat_interaction"],
rob3$se["treat_copilot"], rob4$se["treat_interaction"],
rob1$r2, rob2$r2, rob3$r2, rob4$r2,
rob1$n, rob2$n, rob3$n, rob4$n
)

writeLines(latex_content, file.path(RESULTS_DIR, "regression_tables.tex"))
cat("  ✓ regression_tables.tex\n")

cat("\n=== All regression analyses complete! ===\n")
