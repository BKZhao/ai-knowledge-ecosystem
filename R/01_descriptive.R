# =============================================================================
# 01_descriptive.R — 描述统计分析与可视化
# =============================================================================
# 对应Python: src/analysis/01_descriptive.py
# 功能：SO整体趋势、社区对比、语言分布、用户构成
# =============================================================================

source("R/00_setup.R")

cat("=== 描述统计分析 ===\n\n")

# =====================================================================
# 1. SO周趋势图 + AI事件标注
# =====================================================================
cat("图1: SO周趋势...\n")

if (nrow(monthly_features) > 0) {
  p1 <- ggplot(monthly_features, aes(x = year_month, y = total_questions / 1000)) +
    geom_line(color = SO_COLOR, linewidth = 0.8) +
    geom_smooth(method = "loess", span = 0.2, se = FALSE, color = "gray40", linewidth = 0.5) +
    geom_vline(xintercept = CHATGPT_DATE, linetype = "dashed", color = "red", linewidth = 0.8) +
    annotate("text", x = CHATGPT_DATE, y = max(monthly_features$total_questions/1000, na.rm=TRUE) * 0.98,
             label = "ChatGPT", hjust = 1.1, size = 3, color = "red") +
    geom_vline(xintercept = COPILOT_DATE, linetype = "dashed", color = "blue", linewidth = 0.6) +
    labs(title = "Stack Overflow Monthly Question Volume (2018-2026)",
         x = "", y = "Questions (thousands)") +
    scale_x_date(date_labels = "%Y", date_breaks = "1 year") +
    theme_pub()
  
  ggsave(file.path(FIG_DIR, "fig01_so_monthly_trend.png"), p1, width = 12, height = 5, dpi = 300)
  ggsave(file.path(FIG_DIR, "fig01_so_monthly_trend.pdf"), p1, width = 12, height = 5)
  cat("  ✓ fig01_so_monthly_trend\n")
}

# =====================================================================
# 2. 社区对比图（归一化，验证H4）
# =====================================================================
cat("图2: 社区对比...\n")

if (nrow(se_panel_df) > 0) {
  # 选择四个社区做对比
  comm_cols <- c("SO_questions", "Math_questions", "SuperUser_questions", "ServerFault_questions")
  comm_names <- c("Stack Overflow", "Math SE", "Super User", "Server Fault")
  comm_colors <- c(SO_COLOR, "#2E86AB", "#3DAA35", "#C0392B")
  
  # 2021年均值作为基线
  baseline_mask <- se_panel_df$month >= as.Date("2021-01-01") & se_panel_df$month < as.Date("2022-01-01")
  baselines <- se_panel_df[baseline_mask, lapply(.SD, mean, na.rm = TRUE), .SDcols = comm_cols]
  
  plot_df <- se_panel_df %>%
    select(month, any_of(comm_cols)) %>%
    pivot_longer(cols = any_of(comm_cols), names_to = "community", values_to = "questions") %>%
    mutate(community = factor(community, comm_cols, comm_names))
  
  for (cc in comm_cols) {
    bl <- baselines[[cc]]
    plot_df$ratio[plot_df$community == names(baselines)[match(cc, comm_cols)]] <- 
      plot_df$questions[plot_df$community == names(baselines)[match(cc, comm_cols)]] / bl
  }
  
  # 更简洁的方法
  plot_df2 <- se_panel_df %>%
    select(month, all_of(comm_cols)) %>%
    mutate(across(all_of(comm_cols), ~ .x / mean(.[baseline_mask], na.rm = TRUE))) %>%
    pivot_longer(cols = all_of(comm_cols), names_to = "community", values_to = "ratio") %>%
    mutate(community = factor(community, comm_cols, comm_names)) %>%
    filter(!is.na(ratio)) %>%
    group_by(community) %>%
    mutate(ratio_ma = zoo::rollmean(ratio, k = 3, fill = NA)) %>%
    ungroup()
  
  p2 <- ggplot(plot_df2, aes(x = month, y = ratio_ma, color = community)) +
    geom_line(linewidth = 1.2) +
    geom_vline(xintercept = CHATGPT_DATE, color = "red", linewidth = 1) +
    geom_hline(yintercept = 1, linetype = "dotted", alpha = 0.5) +
    scale_color_manual(values = comm_colors) +
    labs(title = "Normalized Question Volume: Four Communities (2018-2026)",
         subtitle = "Baseline = 2021 annual average (= 1.0)",
         x = "", y = "Normalized Question Count", color = "") +
    scale_x_date(date_labels = "%Y", date_breaks = "1 year") +
    theme_pub() + theme(legend.position = "bottom")
  
  ggsave(file.path(FIG_DIR, "fig02_community_comparison.png"), p2, width = 12, height = 6, dpi = 300)
  ggsave(file.path(FIG_DIR, "fig02_community_comparison.pdf"), p2, width = 12, height = 6)
  cat("  ✓ fig02_community_comparison\n")
}

# =====================================================================
# 3. 月度指标热力图
# =====================================================================
cat("图3: 月度指标热力图...\n")

if (nrow(monthly_features) > 0) {
  heatmap_df <- monthly_features %>%
    mutate(year = format(year_month, "%Y")) %>%
    group_by(year) %>%
    summarise(
      total_q    = sum(total_questions, na.rm = TRUE),
      avg_score  = mean(avg_score, na.rm = TRUE),
      pct_acc    = mean(pct_accepted, na.rm = TRUE) * 100,
      avg_ans    = mean(avg_answers, na.rm = TRUE),
      unique_u   = mean(unique_users, na.rm = TRUE),
      .groups = "drop"
    ) %>%
    mutate(across(where(is.numeric), ~scale(.) %>% as.numeric())) %>%
    pivot_longer(cols = -year, names_to = "metric", values_to = "z_score") %>%
    mutate(metric = recode(metric,
      total_q = "Total Questions", avg_score = "Avg Score",
      pct_acc = "Acceptance Rate (%)", avg_ans = "Avg Answers/Q",
      unique_u = "Unique Users"))
  
  p3 <- ggplot(heatmap_df, aes(x = year, y = metric, fill = z_score)) +
    geom_tile(color = "white") +
    scale_fill_gradient2(low = "#D6604D", mid = "white", high = "#4393C3", midpoint = 0) +
    labs(title = "Stack Overflow Key Metrics by Year (Standardized)",
         x = "", y = "", fill = "Z-score") +
    theme_pub() + theme(axis.text.x = element_text(angle = 45, hjust = 1))
  
  ggsave(file.path(FIG_DIR, "fig03_metrics_heatmap.png"), p3, width = 10, height = 5, dpi = 300)
  ggsave(file.path(FIG_DIR, "fig03_metrics_heatmap.pdf"), p3, width = 10, height = 5)
  cat("  ✓ fig03_metrics_heatmap\n")
}

# =====================================================================
# 4. 回答质量趋势
# =====================================================================
cat("图4: 回答质量趋势...\n")

if (nrow(monthly_features) > 0) {
  q_df <- monthly_features %>%
    mutate(
      acc_ma = zoo::rollmean(pct_accepted * 100, k = 3, fill = NA),
      ans_ma = zoo::rollmean(avg_answers, k = 3, fill = NA)
    )
  
  p4a <- ggplot(q_df, aes(x = year_month)) +
    geom_line(aes(y = pct_accepted * 100), color = "#27AE60", alpha = 0.3) +
    geom_line(aes(y = acc_ma), color = "#27AE60", linewidth = 1.2) +
    geom_vline(xintercept = CHATGPT_DATE, color = "red", linetype = "dashed") +
    labs(title = "Acceptance Rate Over Time", x = "", y = "Acceptance Rate (%)") +
    scale_x_date(date_labels = "%Y", date_breaks = "1 year") +
    theme_pub()
  
  p4b <- ggplot(q_df, aes(x = year_month)) +
    geom_line(aes(y = avg_answers), color = "#2980B9", alpha = 0.3) +
    geom_line(aes(y = ans_ma), color = "#2980B9", linewidth = 1.2) +
    geom_vline(xintercept = CHATGPT_DATE, color = "red", linetype = "dashed") +
    labs(title = "Avg Answers per Question", x = "", y = "Answers") +
    scale_x_date(date_labels = "%Y", date_breaks = "1 year") +
    theme_pub()
  
  p4 <- p4a / p4b + plot_layout(heights = c(1, 1))
  ggsave(file.path(FIG_DIR, "fig04_answer_quality.png"), p4, width = 12, height = 8, dpi = 300)
  ggsave(file.path(FIG_DIR, "fig04_answer_quality.pdf"), p4, width = 12, height = 8)
  cat("  ✓ fig04_answer_quality\n")
}

# =====================================================================
# 5. 描述统计摘要表（Table 1）
# =====================================================================
cat("\n描述统计摘要表...\n")

if (nrow(monthly_features) > 0) {
  desc_table <- monthly_features %>%
    mutate(phase = case_when(
      year_month < as.Date("2021-10-01") ~ "Pre-AI (2018-Q3 2021)",
      year_month < CHATGPT_DATE         ~ "Copilot Era (Q4 2021)",
      year_month < as.Date("2024-01-01") ~ "Post-ChatGPT (2022-2023)",
      TRUE                              ~ "AI Agent Era (2024+)"
    )) %>%
    group_by(phase) %>%
    summarise(
      avg_questions = mean(total_questions, na.rm = TRUE),
      avg_score     = mean(avg_score, na.rm = TRUE),
      pct_accepted  = mean(pct_accepted, na.rm = TRUE) * 100,
      avg_answers   = mean(avg_answers, na.rm = TRUE),
      avg_users     = mean(unique_users, na.rm = TRUE),
      n_months      = n(),
      .groups = "drop"
    )
  
  print(desc_table)
  write_csv(desc_table, file.path(TABLES_DIR, "table1_descriptive_stats.csv"))
  cat("  ✓ table1_descriptive_stats.csv\n")
}

cat("\n✅ 描述统计完成！\n")
