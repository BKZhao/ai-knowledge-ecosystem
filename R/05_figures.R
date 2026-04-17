# =============================================================================
# 05_figures.R — 汇总出图（运行所有图表格子的汇总入口）
# =============================================================================
# 用法：在R控制台运行 source("R/05_figures.R")
# 此脚本生成一张汇总大图 + 所有独立图的索引
# =============================================================================

source("R/00_setup.R")

cat("=== 汇总出图 ===\n\n")

# 如果所有分析已完成，此处可以重新加载结果
# 否则提示用户先运行分析脚本

# ---- 检查分析结果文件是否存在 ----
results_exist <- file.exists(file.path(TABLES_DIR, "regression_results.csv")) &&
  file.exists(file.path(TABLES_DIR, "event_study_results.csv"))

if (!results_exist) {
  cat("⚠ 尚未运行分析脚本，请先运行：\n")
  cat("  source('R/01_descriptive.R')\n")
  cat("  source('R/02_event_study.R')\n")
  cat("  source('R/03_did_analysis.R')\n")
  cat("  source('R/04_regression.R')\n")
  
  # 如果面板数据存在，直接运行全部分析
  if (nrow(panel_df) > 0) {
    cat("\n面板数据已加载，自动运行全部分析...\n")
    source("R/01_descriptive.R")
    source("R/02_event_study.R")
    source("R/03_did_analysis.R")
    source("R/04_regression.R")
  }
}

# ---- 生成六假设汇总图 ----
cat("\n生成六假设汇总图...\n")

if (results_exist || file.exists(file.path(TABLES_DIR, "regression_results.csv"))) {
  res <- read_csv(file.path(TABLES_DIR, "regression_results.csv"), show_col_types = FALSE)
  
  p_summary <- ggplot(res, aes(x = hypothesis, y = beta, fill = p < 0.05)) +
    geom_col(width = 0.7, color = "white") +
    geom_errorbar(aes(ymin = beta - se, ymax = beta + se), width = 0.2) +
    geom_text(aes(label = sprintf("%.4f%s", beta, sig)), vjust = -0.5, size = 3) +
    geom_hline(yintercept = 0, linewidth = 0.8) +
    scale_fill_manual(values = c("TRUE" = CB_COLORS[2], "FALSE" = "gray70"), guide = "none") +
    labs(title = "Summary: Key Coefficients Across All Hypotheses",
         subtitle = "Red = significant (p < 0.05)",
         x = "", y = "Coefficient") +
    theme_pub() + theme(axis.text.x = element_text(angle = 30, hjust = 1))
  
  ggsave(file.path(FIG_DIR, "summary_all_hypotheses.png"), p_summary, width = 12, height = 6, dpi = 300)
  ggsave(file.path(FIG_DIR, "summary_all_hypotheses.pdf"), p_summary, width = 12, height = 6)
  cat("  ✓ summary_all_hypotheses\n")
}

# ---- 生成图表清单 ----
cat("\n已生成图表清单:\n")
fig_files <- list.files(FIG_DIR, pattern = "\\.(png|pdf)$", full.names = TRUE)
for (f in fig_files) {
  cat(sprintf("  %s\n", f))
}

cat(sprintf("\n共 %d 张图表\n", length(fig_files)))
cat("\n✅ 汇总出图完成！\n")
