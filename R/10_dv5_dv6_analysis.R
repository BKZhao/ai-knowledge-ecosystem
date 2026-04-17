# =============================================================================
# 10_dv5_dv6_analysis.R — DV5 Answer Concentration & DV6 Question Complexity
# =============================================================================
# DV5: Gini, Top-10% share, HHI of answer counts per language×month
# DV6: Median body length, code blocks, fraction with code per language×month
# =============================================================================

source("R/00_setup.R")

cat("=== DV5 Answer Concentration & DV6 Question Complexity ===\n\n")

# ---- 输出目录 ----
DV5_DIR <- file.path(RESULTS_DIR, "four_dv_analysis", "dv5_answer_concentration")
DV6_DIR <- file.path(RESULTS_DIR, "four_dv_analysis", "dv6_question_complexity")
dir_create(DV5_DIR, DV6_DIR)

# ---- ARI（与panel一致）----
ARI_CORRECTED <- c(
  python = 0.904, javascript = 0.829, typescript = 0.789,
  java = 0.817, csharp = 0.688, go = 0.726,
  ruby = 0.637, cpp = 0.787, c = 0.531,
  r = 0.480, rust = 0.671, haskell = 0.410, assembly = 0.089
)

# ---- 事件日期 ----
EVENTS <- tibble(
  date  = c("2021-10-01","2022-06-21","2022-11-30","2023-03-14",
            "2023-07-18","2023-08-25","2024-03-04","2024-06-20"),
  short = c("copilot_beta","copilot_ga","chatgpt","gpt4",
            "llama2","code_llama","devin","claude35")
) %>% mutate(date = as.Date(date))

# ---- 辅助函数 ----
stars <- function(p) {
  case_when(p < 0.001 ~ "***", p < 0.01 ~ "**", p < 0.05 ~ "*", p < 0.1 ~ "†", TRUE ~ "")
}

build_panel <- function(df_raw, dv_col) {
  df_raw %>%
    mutate(
      month_dt = as.Date(paste0(month, "-01")),
      ari = ARI_CORRECTED[lang],
      ari_c = ari - mean(ari, na.rm = TRUE),
      lang_fe = lang,
      time_fe = month,
    ) %>%
    # Add event dummies and interactions
    mutate(across(EVENTS$short, ~ as.integer(month_dt >= EVENTS$date[match(cur_column(), EVENTS$short)]),
                  .names = "post_{.col}")) %>%
    mutate(across(starts_with("post_"), ~ ari_c * ., .names = "did_{.col}")) %>%
    drop_na(all_of(dv_col))
}

run_multi_did <- function(panel, dv_col, out_dir, label) {
  cat(sprintf("\n--- %s: Multi-breakpoint DID ---\n", label))
  
  dv_vars <- panel[[dv_col]]
  if (all(is.na(dv_vars)) || var(dv_vars, na.rm = TRUE) == 0) {
    cat("  Skipping: no variance in DV\n")
    return(NULL)
  }
  
  # Build formula: DV ~ ari*post_event1 + ari*post_event2 + ... | lang_fe + time_fe
  did_cols <- grep("^did_", names(panel), value = TRUE)
  post_cols <- grep("^post_", names(panel), value = TRUE)
  
  rhs <- paste(c(post_cols, did_cols), collapse = " + ")
  fml <- as.formula(paste0(dv_col, " ~ ", rhs, " | lang_fe + time_fe"))
  
  cat(sprintf("  Formula: %s\n", deparse(fml, width.cutoff = 500)[1]))
  
  fit <- tryCatch(
    feols(fml, data = panel, cluster = ~lang_fe),
    error = function(e) {
      cat(sprintf("  feols error: %s, trying without cluster\n", e$message))
      feols(fml, data = panel)
    }
  )
  
  # Summary
  coefs <- broom::tidy(fit)
  print(coefs)
  
  # Save regression table
  write_csv(coefs, file.path(out_dir, paste0(label, "_regression.csv")))
  
  # LaTeX table
  did_rows <- coefs %>% filter(str_detect(term, "^did_"))
  post_rows <- coefs %>% filter(str_detect(term, "^post_"))
  
  latex_lines <- c(
    "\\begin{table}[htbp]\\centering",
    sprintf("\\caption{%s: Multi-breakpoint DID Regression}", label),
    "\\begin{tabular}{lcc}",
    "\\toprule",
    sprintf(" & %s \\\\", dv_col),
    "\\midrule"
  )
  for (i in seq_along(EVENTS$short)) {
    ev <- EVENTS$short[i]
    ev_label <- gsub("_", " ", toupper(ev))
    post_r <- post_rows %>% filter(term == paste0("post_", ev))
    did_r <- did_rows %>% filter(term == paste0("did_", ev))
    if (nrow(post_r) > 0) {
      latex_lines <- c(latex_lines,
        sprintf("Post %s & %.4f%s \\\\", ev_label,
                post_r$estimate[1], stars(post_r$p.value[1])),
        sprintf(" & (%.4f) \\\\", post_r$std.error[1])
      )
    }
    if (nrow(did_r) > 0) {
      latex_lines <- c(latex_lines,
        sprintf("ARI$\\times$Post %s & %.4f%s \\\\", ev_label,
                did_r$estimate[1], stars(did_r$p.value[1])),
        sprintf(" & (%.4f) \\\\", did_r$std.error[1])
      )
    }
  }
  latex_lines <- c(latex_lines,
    "\\midrule",
    "Language FE & Yes \\\\",
    "Month FE & Yes \\\\",
    sprintf("$R^2$ & %.4f \\\\", summary(fit)$r2),
    sprintf("$N$ & %d \\\\", nobs(fit)),
    "\\bottomrule",
    "\\end{tabular}",
    sprintf("\\par\\smallskip{\\footnotesize $^{***}p<0.001$, $^{**}p<0.01$, $^{*}p<0.05$. Clustered SE by language.}"),
    "\\end{table}"
  )
  writeLines(latex_lines, file.path(out_dir, paste0(label, "_regression.tex")))
  
  cat(sprintf("  R²=%.4f, N=%d\n", summary(fit)$r2, nobs(fit)))
  return(fit)
}

run_event_study <- function(panel, dv_col, out_dir, label) {
  cat(sprintf("\n--- %s: Event Study ---\n", label))
  
  panel <- panel %>% mutate(month_dt = as.Date(paste0(month, "-01")))
  
  # Event study relative to ChatGPT (main event)
  ref_date <- as.Date("2022-11-30")
  panel <- panel %>%
    mutate(rel_month = round((month_dt - ref_date) / 30.44),
           rel_month = as.integer(rel_month)) %>%
    filter(rel_month >= -12, rel_month <= 15)
  
  # Create relative month dummies × ARI interaction
  # Exclude -1 as reference
  ref_vars <- paste0("ari_c:factor(rel_month)", collapse = "")
  
  est <- tryCatch(
    feols(as.formula(paste0(dv_col, " ~ i(rel_month, ref = -1, keep = -12:-1, 0:15) | lang_fe + time_fe")),
          data = panel),
    error = function(e) {
      feols(as.formula(paste0(dv_col, " ~ i(rel_month, ref = -1) | lang_fe")), data = panel)
    }
  )
  
  coefs <- broom::tidy(est)
  ev_coefs <- coefs %>% filter(str_detect(term, "^rel_month"))
  
  # Create event study plot
  ev_df <- ev_coefs %>%
    mutate(
      rel_m = as.integer(gsub("rel_month::?", "", term)),
      lo = estimate - 1.96 * std.error,
      hi = estimate + 1.96 * std.error,
    ) %>%
    filter(!is.na(rel_m)) %>%
    filter(rel_m >= -12, rel_m <= 15)
  
  p <- ggplot(ev_df, aes(x = rel_m, y = estimate)) +
    geom_point(size = 2) +
    geom_errorbar(aes(ymin = lo, ymax = hi), width = 0.3) +
    geom_hline(yintercept = 0, linetype = "dashed", color = "gray50") +
    geom_vline(xintercept = -0.5, linetype = "solid", color = "red", alpha = 0.5) +
    labs(title = sprintf("Event Study: %s (ChatGPT)", label),
         x = "Months Relative to ChatGPT", y = "Coefficient") +
    theme_pub()
  
  ggsave(file.path(out_dir, paste0(label, "_event_study.png")), p, width = 10, height = 5, dpi = 300)
  cat("  Event study plot saved\n")
  
  return(est)
}

plot_trends <- function(panel, dv_col, out_dir, label, lang_subset = NULL) {
  if (!is.null(lang_subset)) {
    plot_df <- panel %>% filter(lang %in% lang_subset)
  } else {
    plot_df <- panel
  }
  
  # Group into high/low ARI
  plot_df <- plot_df %>%
    mutate(
      month_dt = as.Date(paste0(month, "-01")),
      ari_group = ifelse(ari >= 0.7, "High ARI (≥0.7)", "Low ARI (<0.7)"),
    )
  
  group_avg <- plot_df %>%
    group_by(month_dt, ari_group) %>%
    summarise(val = median(!!sym(dv_col), na.rm = TRUE), .groups = "drop")
  
  p <- ggplot(group_avg, aes(x = month_dt, y = val, color = ari_group)) +
    geom_line(linewidth = 1.2) +
    geom_smooth(method = "loess", span = 0.15, se = FALSE, linetype = "dashed", linewidth = 0.5) +
    geom_vline(xintercept = CHATGPT_DATE, linetype = "dashed", color = "red", alpha = 0.7) +
    annotate("text", x = CHATGPT_DATE, y = max(group_avg$val, na.rm = TRUE),
             label = "ChatGPT", hjust = 1.1, vjust = 1, size = 3, color = "red") +
    scale_color_manual(values = c("High ARI (≥0.7)" = "#E74C3C", "Low ARI (<0.7)" = "#3498DB")) +
    scale_x_date(date_labels = "%Y", date_breaks = "1 year") +
    labs(title = sprintf("%s: Trends by ARI Group", label),
         x = "", y = dv_col, color = "") +
    theme_pub() + theme(legend.position = "bottom")
  
  ggsave(file.path(out_dir, paste0(label, "_trends.png")), p, width = 12, height = 5, dpi = 300)
  cat("  Trends plot saved\n")
  
  return(p)
}

# =============================================================================
# Load data
# =============================================================================
cat("Loading data...\n")

dv5_raw <- read_csv(file.path(PROCESSED_DIR, "dv5_answer_concentration.csv"),
                    show_col_types = FALSE)
dv6_raw <- read_csv(file.path(PROCESSED_DIR, "dv6_question_complexity.csv"),
                    show_col_types = FALSE)

cat(sprintf("DV5: %d rows, %d languages\n", nrow(dv5_raw), dv5_raw$lang %>% nunique()))
cat(sprintf("DV6: %d rows, %d languages\n", nrow(dv6_raw), dv6_raw$lang %>% nunique()))

# =============================================================================
# DV5: Answer Concentration
# =============================================================================
cat("\n" , strrep("=", 60), "\n")
cat("DV5: ANSWER CONCENTRATION\n")
cat(strrep("=", 60), "\n")

dv5_metrics <- c("gini", "top10_share", "hhi")
dv5_fits <- list()

for (metric in dv5_metrics) {
  panel <- build_panel(dv5_raw, metric)
  
  # Multi-breakpoint DID
  fit <- run_multi_did(panel, metric, DV5_DIR, paste0("dv5_", metric))
  dv5_fits[[metric]] <- fit
  
  # Event study
  run_event_study(panel, metric, DV5_DIR, paste0("dv5_", metric))
  
  # Trends plot
  plot_trends(panel, metric, DV5_DIR, paste0("DV5 ", toupper(gsub("_", " ", metric))))
}

# =============================================================================
# DV6: Question Complexity
# =============================================================================
cat("\n", strrep("=", 60), "\n")
cat("DV6: QUESTION COMPLEXITY\n")
cat(strrep("=", 60), "\n")

dv6_metrics <- c("median_body_length", "median_code_blocks", "frac_with_code")
dv6_fits <- list()

for (metric in dv6_metrics) {
  panel <- build_panel(dv6_raw, metric)
  
  fit <- run_multi_did(panel, metric, DV6_DIR, paste0("dv6_", metric))
  dv6_fits[[metric]] <- fit
  
  run_event_study(panel, metric, DV6_DIR, paste0("dv6_", metric))
  
  plot_trends(panel, metric, DV6_DIR, paste0("DV6 ", toupper(gsub("_", " ", metric))))
}

# =============================================================================
# Heterogeneity: Does effect differ by ARI level?
# =============================================================================
cat("\n", strrep("=", 60), "\n")
cat("HETEROGENEITY ANALYSIS\n")
cat(strrep("=", 60), "\n")

hetero_results <- list()

for (dv_name in c("gini", "median_body_length", "frac_with_code")) {
  cat(sprintf("\n--- Heterogeneity: %s ---\n", dv_name))
  
  if (dv_name %in% dv5_metrics) {
    panel <- build_panel(dv5_raw, dv_name)
  } else {
    panel <- build_panel(dv6_raw, dv_name)
  }
  
  # Split into high/low ARI and run separate regressions
  panel <- panel %>%
    mutate(ari_tercile = ntile(ari, 3),
           ari_group = case_when(
             ari_tercile == 3 ~ "high",
             ari_tercile == 1 ~ "low",
             TRUE ~ "mid"
           ))
  
  post_cols <- grep("^post_", names(panel), value = TRUE)
  rhs <- paste(post_cols, collapse = " + ")
  
  for (grp in c("high", "low")) {
    sub_panel <- panel %>% filter(ari_group == grp)
    fml <- as.formula(paste0(dv_name, " ~ ", rhs, " | lang_fe + time_fe"))
    fit <- tryCatch(feols(fml, data = sub_panel), error = function(e) NULL)
    if (!is.null(fit)) {
      chatgpt_coef <- broom::tidy(fit) %>% filter(term == "post_chatgpt")
      if (nrow(chatgpt_coef) > 0) {
        cat(sprintf("  %s ARI, ChatGPT: β=%.4f (p=%.4f)\n", grp,
                    chatgpt_coef$estimate[1], chatgpt_coef$p.value[1]))
        hetero_results[[paste(dv_name, grp)]] <- chatgpt_coef
      }
    }
  }
}

# =============================================================================
# Summary
# =============================================================================
cat("\n", strrep("=", 60), "\n")
cat("GENERATING SUMMARY\n")
cat(strrep("=", 60), "\n")

summary_lines <- c(
  "# DV5 & DV6 Analysis Summary",
  "",
  paste0("Generated: ", Sys.time()),
  "",
  "## DV5: Answer Concentration",
  "",
  "| Metric | Languages | Months | N obs |",
  "|--------|-----------|--------|-------|",
  sprintf("| %s | %d | %d | %d |", dv5_metrics[1], dv5_raw$lang %>% nunique(),
          dv5_raw$month %>% nunique(), nrow(dv5_raw)),
  "",
  "### Key DID Results (ChatGPT interaction with ARI)",
  ""
)

for (metric in dv5_metrics) {
  fit <- dv5_fits[[metric]]
  if (!is.null(fit)) {
    coefs <- broom::tidy(fit)
    chatgpt_did <- coefs %>% filter(term == "did_chatgpt")
    if (nrow(chatgpt_did) > 0) {
      summary_lines <- c(summary_lines,
        sprintf("- **%s**: β = %.4f, p = %.4f %s",
                metric, chatgpt_did$estimate[1], chatgpt_did$p.value[1],
                stars(chatgpt_did$p.value[1]))
      )
    }
  }
}

summary_lines <- c(summary_lines, "", "## DV6: Question Complexity", "",
  sprintf("| Metric | Languages | Months | N obs |"),
  sprintf("|--------|-----------|--------|-------|"),
  sprintf("| %s | %d | %d | %d |", dv6_metrics[1], dv6_raw$lang %>% nunique(),
          dv6_raw$month %>% nunique(), nrow(dv6_raw)),
  "", "### Key DID Results (ChatGPT interaction with ARI)", ""
)

for (metric in dv6_metrics) {
  fit <- dv6_fits[[metric]]
  if (!is.null(fit)) {
    coefs <- broom::tidy(fit)
    chatgpt_did <- coefs %>% filter(term == "did_chatgpt")
    if (nrow(chatgpt_did) > 0) {
      summary_lines <- c(summary_lines,
        sprintf("- **%s**: β = %.4f, p = %.4f %s",
                metric, chatgpt_did$estimate[1], chatgpt_did$p.value[1],
                stars(chatgpt_did$p.value[1]))
      )
    }
  }
}

summary_lines <- c(summary_lines, "", "## Heterogeneity Analysis", "")

for (nm in names(hetero_results)) {
  r <- hetero_results[[nm]]
  summary_lines <- c(summary_lines,
    sprintf("- %s: β = %.4f, p = %.4f %s", nm, r$estimate[1], r$p.value[1], stars(r$p.value[1]))
  )
}

summary_lines <- c(summary_lines, "", "## Files Generated", "")

for (d in list(DV5_DIR, DV6_DIR)) {
  files <- list.files(d, pattern = "\\.(csv|tex|png)$", full.names = TRUE)
  for (f in files) summary_lines <- c(summary_lines, sprintf("- `%s`", f))
}

summary_lines <- c(summary_lines, "")
writeLines(summary_lines, file.path(RESULTS_DIR, "four_dv_analysis", "summary_dv5_dv6.md"))

cat("\n=== All DV5/DV6 analyses complete! ===\n")
