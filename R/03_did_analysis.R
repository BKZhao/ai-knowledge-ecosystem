# =============================================================================
# 03_did_analysis.R — 双重差分（DID）分析
# =============================================================================
# 对应Python: src/analysis/03_did_analysis.py
# 识别策略：编程语言AI可替代性差异 → 处理强度
# 方法：基础DID + 两向固定效应 + 平行趋势 + 异质性分析
# =============================================================================

source("R/00_setup.R")

cat("=== 双重差分（DID）分析 ===\n")
cat(sprintf("断点：ChatGPT发布（%s）\n", CHATGPT_DATE))
cat(sprintf("处理组阈值：ARI >= %.2f, 对照组阈值：ARI <= %.2f\n\n", HIGH_ARI_THRESHOLD, LOW_ARI_THRESHOLD))

if (nrow(panel_df) == 0) stop("panel_df 为空，请先运行Python pipeline")

# ---- 准备DID数据 ----
did_df <- panel_df %>%
  filter(platform %in% c("SO", "GitHub")) %>%
  mutate(
    lang_fe = language,
    time_fe = format(month, "%Y-%m"),
    # 处理组/对照组标记
    treatment_group = as.integer(ari >= HIGH_ARI_THRESHOLD),
    control_group   = as.integer(ari <= LOW_ARI_THRESHOLD),
    # 只保留处理组和对照组的数据
    analysis_group = case_when(
      treatment_group == 1 ~ "treatment",
      control_group == 1   ~ "control",
      TRUE ~ "excluded"
    )
  )

# =====================================================================
# 1. 基础2×2 DID（处理组 vs 对照组）
# =====================================================================
cat("[1] 基础2×2 DID...\n")

did_2x2 <- did_df %>%
  filter(analysis_group %in% c("treatment", "control")) %>%
  filter(month >= as.Date("2020-01-01")) %>%
  mutate(DiD = treatment_group * post_chatgpt)

# 简单OLS DID
fit_simple <- lm(ln_activity ~ DiD + treatment_group + post_chatgpt, data = did_2x2)
s_simple <- summary(fit_simple)
cat(sprintf("  简单DID系数: %.4f (SE: %.4f)\n", coef(fit_simple)["DiD"], s_simple$coefficients["DiD", "Std. Error"]))

# HC3稳健标准误
fit_simple_robust <- coeftest(fit_simple, vcov = vcovHC(fit_simple, type = "HC3"))
cat(sprintf("  HC3稳健SE: %.4f, p=%.4f\n", fit_simple_robust["DiD", "Std. Error"], fit_simple_robust["DiD", "Pr(>|t|)"]))

# =====================================================================
# 2. 两向固定效应DID（fixest::feols）
# =====================================================================
cat("\n[2] 两向固定效应DID（feols）...\n")

did_2wfe <- did_df %>%
  filter(analysis_group %in% c("treatment", "control")) %>%
  filter(month >= as.Date("2020-01-01")) %>%
  mutate(
    DiD = treatment_group * post_chatgpt,
    DiD_copilot = treatment_group * post_copilot_ga
  )

# 语言FE + 月FE
fit_2wfe <- feols(ln_activity ~ DiD | language + month, data = did_2wfe, cluster = ~language)
cat(sprintf("  2WFE DID系数: %.4f\n", coef(fit_2wfe)["DiD"]))
cat(sprintf("  聚类SE: %.4f\n", se(fit_2wfe)["DiD"]))
cat(sprintf("  t统计量: %.2f\n", t_stat(fit_2wfe)["DiD"]))
cat(sprintf("  p值: %.4f\n", pvalue(fit_2wfe)["DiD"]))
cat(sprintf("  样本量: %d\n", nobs(fit_2wfe)))

# Copilot时代DID
fit_copilot <- feols(ln_activity ~ DiD_copilot | language + month, data = did_2wfe, cluster = ~language)
cat(sprintf("  Copilot DID系数: %.4f (p=%.4f)\n", coef(fit_copilot)["DiD_copilot"], pvalue(fit_copilot)["DiD_copilot"]))

# =====================================================================
# 3. 连续处理强度DID（全语言，ARI×Post_ChatGPT）
# =====================================================================
cat("\n[3] 连续处理强度DID...\n")

did_continuous <- did_df %>%
  filter(month >= as.Date("2020-01-01")) %>%
  mutate(DiD_continuous = ari * post_chatgpt)

fit_cont <- feols(ln_activity ~ DiD_continuous | language + month, data = did_continuous, cluster = ~language)
cat(sprintf("  连续DID系数 (ARI × Post_ChatGPT): %.4f\n", coef(fit_cont)["DiD_continuous"]))
cat(sprintf("  SE: %.4f, p: %.4f\n", se(fit_cont)["DiD_continuous"], pvalue(fit_cont)["DiD_continuous"]))

# =====================================================================
# 4. 平行趋势检验（预处理期季度DID）
# =====================================================================
cat("\n[4] 平行趋势检验...\n")

pre_period <- did_df %>%
  filter(analysis_group %in% c("treatment", "control")) %>%
  filter(month >= as.Date("2020-01-01"), month < CHATGPT_DATE) %>%
  mutate(quarter = floor_date(month, "quarter")) %>%
  filter(n() > 0)

if (nrow(pre_period) > 0) {
  quarters <- sort(unique(pre_period$quarter))
  ref_q <- quarters[length(quarters) - 2]  # 倒数第二个季度为参照期
  
  # 创建季度DID交乘项
  for (q in quarters) {
    q_name <- as.character(q)
    col_name <- gsub("-", "_", gsub(" ", "_", q_name))
    pre_period[[paste0("d_", col_name)]] <- as.integer(pre_period$quarter == q)
    pre_period[[paste0("did_", col_name)]] <- pre_period[[paste0("d_", col_name)]] * pre_period$treatment_group
  }
  
  did_cols <- grep("^did_", names(pre_period), value = TRUE)
  ref_col <- paste0("did_", gsub("-", "_", gsub(" ", "_", as.character(ref_q))))
  did_cols <- setdiff(did_cols, ref_col)
  
  if (length(did_cols) > 0) {
    formula_pt <- as.formula(paste("ln_activity ~", paste(did_cols, collapse = " + "),
                                   "+ language + quarter"))
    fit_pt <- lm(formula_pt, data = pre_period)
    # 简单F检验
    f_test <- linearHypothesis(fit_pt, paste0(did_cols, " = 0"))
    f_pval <- f_test$`Pr(>F)`[2]
    cat(sprintf("  平行趋势联合F检验 p值: %.4f\n", f_pval))
    if (f_pval > 0.1) cat("  ✓ 平行趋势假设通过（p > 0.10）\n") else cat("  ⚠ 平行趋势可能违反\n")
    
    # 平行趋势图
    pt_coefs <- tibble(
      quarter = did_cols,
      coef = sapply(did_cols, function(c) coef(fit_pt)[c]),
      se = sapply(did_cols, function(c) summary(fit_pt)$coefficients[c, "Std. Error"])
    ) %>%
      mutate(q_label = gsub("did_", "", quarter))
    
    p_pt <- ggplot(pt_coefs, aes(x = seq_along(quarter), y = coef)) +
      geom_point(size = 3) +
      geom_errorbar(aes(ymin = coef - 1.96 * se, ymax = coef + 1.96 * se), width = 0.2) +
      geom_hline(yintercept = 0, color = "black") +
      labs(title = "Parallel Trends Test: Treatment × Quarter (Pre-ChatGPT)",
           subtitle = sprintf("Joint F-test p = %.3f", f_pval),
           x = "Quarter", y = "DID Coefficient") +
      theme_pub() +
      theme(axis.text.x = element_text(angle = 45, hjust = 1, size = 8))
    
    ggsave(file.path(FIG_DIR, "parallel_trends_test.png"), p_pt, width = 12, height = 6, dpi = 300)
    ggsave(file.path(FIG_DIR, "parallel_trends_test.pdf"), p_pt, width = 12, height = 6)
    cat("  ✓ parallel_trends_test\n")
  }
}

# =====================================================================
# 5. 异质性分析：按语言分组
# =====================================================================
cat("\n[5] 语言异质性分析...\n")

lang_effects <- did_df %>%
  filter(month >= as.Date("2020-01-01")) %>%
  group_by(language) %>%
  filter(n() >= 30) %>%
  group_modify(~ {
    fit <- lm(ln_activity ~ post_chatgpt, data = .x)
    s <- summary(fit)
    tibble(
      language = unique(.x$language),
      ari = unique(.x$ari),
      did_effect = coef(fit)["post_chatgpt"],
      se = s$coefficients["post_chatgpt", "Std. Error"],
      pval = s$coefficients["post_chatgpt", "Pr(>|t|)"]
    )
  }, .keep = FALSE) %>%
  drop_na()

if (nrow(lang_effects) > 3) {
  # 散点图 + 拟合线
  p_het <- ggplot(lang_effects, aes(x = ari, y = did_effect)) +
    geom_pointrange(aes(ymin = did_effect - 1.96 * se, ymax = did_effect + 1.96 * se),
                    color = "gray40", linewidth = 0.5, fatten = 2) +
    geom_point(aes(color = ari >= HIGH_ARI_THRESHOLD), size = 3) +
    geom_text(aes(label = language), vjust = -1, hjust = 0.5, size = 3) +
    geom_smooth(method = "lm", se = TRUE, color = "#E74C3C", linetype = "dashed") +
    geom_vline(xintercept = HIGH_ARI_THRESHOLD, color = "red", linetype = ":", alpha = 0.5) +
    geom_vline(xintercept = LOW_ARI_THRESHOLD, color = "blue", linetype = ":", alpha = 0.5) +
    geom_hline(yintercept = 0, color = "black", linewidth = 0.5) +
    scale_color_manual(values = c("TRUE" = "#E74C3C", "FALSE" = "#3498DB"), guide = "none") +
    labs(title = "Heterogeneity: Post-ChatGPT Effect vs. AI Replaceability",
         x = "AI Replaceability Index", y = "DID Effect on ln(Activity)") +
    theme_pub()
  
  ggsave(file.path(FIG_DIR, "heterogeneity_by_language.png"), p_het, width = 10, height = 7, dpi = 300)
  ggsave(file.path(FIG_DIR, "heterogeneity_by_language.pdf"), p_het, width = 10, height = 7)
  cat("  ✓ heterogeneity_by_language\n")
  
  # OLS: effect ~ ari
  het_ols <- simple_ols(lang_effects$did_effect, lang_effects$ari)
  cat(sprintf("  异质性OLS: slope=%.4f (SE=%.4f, p=%.4f), R²=%.4f\n",
              het_ols$betas["slope"], het_ols$se["slope"], het_ols$p["slope"], het_ols$r2))
}

write_csv(lang_effects, file.path(TABLES_DIR, "language_effects.csv"))
cat("  ✓ language_effects.csv\n")

# =====================================================================
# 结果汇总
# =====================================================================
cat("\n" paste(rep("=", 60), collapse = ""), "\n")
cat("DID分析主要结果汇总\n")
cat(paste(rep("=", 60), collapse = ""), "\n")

did_pct <- (exp(coef(fit_simple)["DiD"]) - 1) * 100
cat(sprintf("基础DID: β=%.4f (%.1f%%)\n", coef(fit_simple)["DiD"], did_pct))
cat(sprintf("2WFE DID: β=%.4f (p=%.4f)\n", coef(fit_2wfe)["DiD"], pvalue(fit_2wfe)["DiD"]))
cat(sprintf("连续DID: β=%.4f (p=%.4f)\n", coef(fit_cont)["DiD_continuous"], pvalue(fit_cont)["DiD_continuous"]))
cat(sprintf("样本量: %d\n", nobs(fit_2wfe)))

cat("\n✅ DID分析完成！\n")
