# =============================================================================
# 02_event_study.R — 事件研究分析
# =============================================================================
# 对应Python: src/analysis/02_event_study.py
# 方法：OLS基准趋势拟合 + 异常值计算 + CAR累积 + Newey-West标准误
# =============================================================================

source("R/00_setup.R")

cat("=== 事件研究分析 ===\n\n")

ESTIMATION_WINDOW <- 52  # 事件前52周
EVENT_WINDOW <- 12       # 事件前后各12周

# ---- 构建SO周数据 ----
# 从api_cache_weekly.json构建时间序列
so_df <- bind_rows(lapply(names(so_cache), function(k) {
  v <- so_cache[[k]]
  if (!is.null(v$total_questions) && v$total_questions > 0) {
    tibble(week_dt = as.Date(v$week_dt), total_questions = v$total_questions)
  }
})) %>% arrange(week_dt) %>% distinct(week_dt, .keep_all = TRUE)

if (nrow(so_df) < 10) {
  stop("SO周数据不足，请检查api_cache_weekly.json")
}

cat(sprintf("数据范围: %s 到 %s, 共 %d 周\n", min(so_df$week_dt), max(so_df$week_dt), nrow(so_df)))

so_df <- so_df %>%
  mutate(
    t = row_number() - 1,
    log_q = log1p(total_questions),
    week_of_year = as.integer(format(week_dt, "%U"))
  )

# =====================================================================
# 事件研究核心函数
# =====================================================================

run_event_study <- function(df, event_date, outcome_var = "log_q",
                            est_window = ESTIMATION_WINDOW, evt_window = EVENT_WINDOW) {
  
  df_sorted <- df %>% arrange(week_dt)
  
  # 找事件周索引
  date_diffs <- abs(as.numeric(df_sorted$week_dt - event_date))
  event_idx <- which.min(date_diffs)
  
  # 定义窗口边界
  est_start <- max(1, event_idx - est_window - evt_window)
  est_end   <- event_idx - evt_window
  evt_start <- max(1, event_idx - evt_window)
  evt_end   <- min(nrow(df_sorted), event_idx + evt_window)
  
  if (est_start >= est_end || est_end <= 0) {
    cat(sprintf("    ⚠ 估计窗口不足，跳过\n"))
    return(NULL)
  }
  
  # 估计窗口数据
  df_est <- df_sorted[est_start:est_end, ]
  if (nrow(df_est) < 20) {
    cat(sprintf("    ⚠ 估计窗口数据不足 (%d 周)，跳过\n", nrow(df_est)))
    return(NULL)
  }
  
  # 基准OLS模型：log_q ~ t + t^2 + 周季节性
  # 使用week_of_year作为因子
  fit_est <- lm(as.formula(paste(outcome_var, "~ t + I(t^2) + factor(week_of_year)")), data = df_est)
  
  # 事件窗口数据
  df_evt <- df_sorted[evt_start:evt_end, ]
  
  # 对齐因子水平
  df_evt$week_of_year <- factor(df_evt$week_of_year, levels = levels(df_est$week_of_year))
  
  # 预测事件窗口的期望值
  y_pred <- predict(fit_est, newdata = df_evt)
  y_actual <- df_evt[[outcome_var]]
  
  # 异常值和CAR
  ar <- y_actual - y_pred
  car <- cumsum(ar)
  relative_weeks <- seq(-evt_window, length(ar) - evt_window - 1)
  
  # Newey-West标准误
  resid_est <- residuals(fit_est)
  lags_nw <- min(4, nrow(df_est) %/% 5)
  ar_var <- var(resid_est, na.rm = TRUE)
  ar_se <- sqrt(ar_var)
  car_se <- ar_se * sqrt(seq_along(ar))
  
  # 95% CI
  car_lower <- car - 1.96 * car_se
  car_upper <- car + 1.96 * car_se
  
  list(
    ar = ar, car = car, car_lower = car_lower, car_upper = car_upper,
    car_se = car_se, relative_weeks = relative_weeks,
    actual = y_actual, predicted = y_pred,
    event_dates = df_evt$week_dt,
    car_final = car[length(car)],
    car_final_se = car_se[length(car_se)],
    car_final_t = if (car_se[length(car_se)] > 0) car[length(car)] / car_se[length(car_se)] else NA_real_,
    r_squared = summary(fit_est)$r.squared,
    est_window_size = nrow(df_est),
    event_date = event_date
  )
}

# =====================================================================
# 对所有事件运行分析
# =====================================================================

cat("\n逐事件分析:\n")
all_results <- list()

for (i in seq_len(nrow(EVENT_LIST))) {
  event <- EVENT_LIST[i, ]
  cat(sprintf("  %s (%s)...\n", event$name, event$date))
  
  result <- run_event_study(so_df, event$date)
  
  if (!is.null(result)) {
    car_pct <- (exp(result$car_final) - 1) * 100
    cat(sprintf("    CAR: %.4f (%.1f%%), t=%.2f, R²=%.3f\n",
                result$car_final, car_pct, result$car_final_t, result$r_squared))
    all_results[[event$short]] <- result
  }
}

# =====================================================================
# 汇总表
# =====================================================================
cat("\n事件研究汇总表:\n")

summary_table <- tibble(
  Event = EVENT_LIST$name,
  Date  = as.character(EVENT_LIST$date),
  CAR_log = NA_real_,
  CAR_pct = NA_real_,
  SE = NA_real_,
  t_stat = NA_real_,
  R2 = NA_real_,
  Est_weeks = NA_integer_
)

for (j in seq_along(all_results)) {
  nm <- names(all_results)[j]
  idx <- which(EVENT_LIST$short == nm)
  if (length(idx) > 0) {
    r <- all_results[[j]]
    summary_table$CAR_log[idx]  <- r$car_final
    summary_table$CAR_pct[idx]  <- (exp(r$car_final) - 1) * 100
    summary_table$SE[idx]       <- r$car_final_se
    summary_table$t_stat[idx]   <- r$car_final_t
    summary_table$R2[idx]       <- r$r_squared
    summary_table$Est_weeks[idx] <- r$est_window_size
    
    # 显著性标注
    sig <- stars(r$car_final_t)
    if (sig != "") summary_table$Event[idx] <- paste0(summary_table$Event[idx], sig)
  }
}

print(summary_table)
write_csv(summary_table, file.path(TABLES_DIR, "event_study_results.csv"))
cat("  ✓ event_study_results.csv\n")

# =====================================================================
# 汇总图：所有事件CAR
# =====================================================================
cat("\n生成汇总图...\n")

if (length(all_results) > 0) {
  plot_data <- bind_rows(lapply(names(all_results), function(nm) {
    r <- all_results[[nm]]
    tibble(
      event = nm, week = r$relative_weeks,
      car = r$car, lower = r$car_lower, upper = r$car_upper
    )
  })) %>%
    mutate(event = factor(event, levels = names(all_results)))
  
  # 多面板CAR图
  n_events <- length(all_results)
  ncol <- min(4, n_events)
  nrow <- ceiling(n_events / ncol)
  
  p_car <- ggplot(plot_data, aes(x = week, y = car)) +
    geom_ribbon(aes(ymin = lower, ymax = upper), alpha = 0.2, fill = "#3498DB") +
    geom_line(color = "#2980B9", linewidth = 1.2) +
    geom_hline(yintercept = 0, color = "black", linewidth = 0.5) +
    geom_vline(xintercept = 0, color = "red", linetype = "dashed", linewidth = 1) +
    facet_wrap(~event, scales = "free_y", ncol = ncol) +
    labs(title = "Cumulative Abnormal Returns Around AI Tool Releases",
         subtitle = "Baseline: OLS trend from pre-event 52 weeks; Shaded = 95% CI",
         x = "Weeks Relative to Event (0 = event)", y = "Cumulative Abnormal Effect") +
    theme_pub() + theme(strip.text = element_text(face = "bold", size = 9))
  
  ggsave(file.path(FIG_DIR, "car_all_events_summary.png"), p_car, width = 16, height = 4 * nrow, dpi = 300)
  ggsave(file.path(FIG_DIR, "car_all_events_summary.pdf"), p_car, width = 16, height = 4 * nrow)
  cat("  ✓ car_all_events_summary\n")
  
  # 单事件图（ChatGPT为例）
  if ("ChatGPT" %in% names(all_results)) {
    r_cg <- all_results[["ChatGPT"]]
    single_df <- tibble(week = r_cg$relative_weeks, car = r_cg$car,
                        lower = r_cg$car_lower, upper = r_cg$car_upper,
                        actual = r_cg$actual, predicted = r_cg$predicted)
    
    p_single1 <- ggplot(single_df, aes(x = week, y = car)) +
      geom_ribbon(aes(ymin = lower, ymax = upper), alpha = 0.2, fill = "#3498DB") +
      geom_line(color = "#2980B9", linewidth = 1.5) +
      geom_hline(yintercept = 0) +
      geom_vline(xintercept = 0, color = "red", linetype = "dashed", linewidth = 1.5) +
      labs(title = paste0("CAR: ChatGPT Launch (Final CAR = ", round(r_cg$car_final, 3), ")"),
           x = "Weeks Relative to Event", y = "Cumulative Abnormal Effect (log scale)") +
      theme_pub()
    
    p_single2 <- ggplot(single_df, aes(x = week)) +
      geom_line(aes(y = actual), color = "#E74C3C", linewidth = 1.5) +
      geom_line(aes(y = predicted), color = "#2ECC71", linewidth = 1.5, linetype = "dashed") +
      geom_vline(xintercept = 0, color = "red", linetype = "dashed", linewidth = 1.2) +
      labs(title = "Actual vs. Counterfactual (log question count)",
           x = "Weeks Relative to Event", y = "Log(Questions + 1)") +
      theme_pub()
    
    p_single <- p_single1 / p_single2 + plot_layout(heights = c(1, 1))
    ggsave(file.path(FIG_DIR, "car_chatgpt.png"), p_single, width = 10, height = 10, dpi = 300)
    ggsave(file.path(FIG_DIR, "car_chatgpt.pdf"), p_single, width = 10, height = 10)
    cat("  ✓ car_chatgpt\n")
  }
}

cat("\n✅ 事件研究完成！\n")
