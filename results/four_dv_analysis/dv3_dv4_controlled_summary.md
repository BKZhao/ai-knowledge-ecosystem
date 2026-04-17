# DV3 & DV4 Controlled vs Uncontrolled Comparison

## DV3: Knowledge Diversity (Enhanced DID)

**Added controls:** COVID peak, tech layoff, LLM interest, platform-wide question activity, 11 month-of-year dummies

### M1_tag_entropy

| Variable | Old Coef | Old p | Old Sig | New Coef | New p | New Sig | Changed |
|----------|----------|-------|---------|----------|-------|---------|---------|
| did_copilot_beta | 0.1201 | 0.0332 | * | 0.1201 | 0.7776 | - | **YES** |
| did_copilot_ga | 0.0936 | 0.2637 | - | 0.0936 | 0.7665 | - |  |
| did_chatgpt | 0.0974 | 0.3228 | - | 0.0974 | 0.6920 | - |  |
| did_gpt4 | 0.1355 | 0.1921 | - | 0.1355 | 0.4781 | - |  |
| did_llama2 | -0.0436 | 0.7907 | - | -0.0436 | 0.7397 | - |  |
| did_code_llama | 0.1035 | 0.5097 | - | 0.1035 | 0.3819 | - |  |
| did_devin | 0.1246 | 0.4273 | - | 0.1246 | 0.0000 | *** | **YES** |

### M2_unique_tags_lt

| Variable | Old Coef | Old p | Old Sig | New Coef | New p | New Sig | Changed |
|----------|----------|-------|---------|----------|-------|---------|---------|
| did_copilot_beta | 0.0576 | 0.5223 | - | 0.0576 | 0.9598 | - |  |
| did_copilot_ga | 0.2343 | 0.0801 | - | 0.2343 | 0.7792 | - |  |
| did_chatgpt | -0.1567 | 0.3198 | - | -0.1567 | 0.8074 | - |  |
| did_gpt4 | 0.1954 | 0.2391 | - | 0.1954 | 0.6907 | - |  |
| did_llama2 | 0.1045 | 0.6905 | - | 0.1045 | 0.7570 | - |  |
| did_code_llama | -0.1782 | 0.4777 | - | -0.1782 | 0.5553 | - |  |
| did_devin | 0.1558 | 0.5346 | - | 0.1558 | 0.0012 | *** | **YES** |

### M3_tag_concentration

| Variable | Old Coef | Old p | Old Sig | New Coef | New p | New Sig | Changed |
|----------|----------|-------|---------|----------|-------|---------|---------|
| did_copilot_beta | -0.0110 | 0.1369 | - | -0.0110 | 0.6871 | - |  |
| did_copilot_ga | 0.0087 | 0.4263 | - | 0.0087 | 0.6689 | - |  |
| did_chatgpt | -0.0183 | 0.1555 | - | -0.0183 | 0.2586 | - |  |
| did_gpt4 | -0.0060 | 0.6587 | - | -0.0060 | 0.6150 | - |  |
| did_llama2 | 0.0412 | 0.0554 | - | 0.0412 | 0.0004 | *** | **YES** |
| did_code_llama | -0.0384 | 0.0617 | - | -0.0384 | 0.0003 | *** | **YES** |
| did_devin | -0.0134 | 0.5149 | - | -0.0134 | 0.0000 | *** | **YES** |

### DV3 Key Findings
- Most DID coefficients lose significance with controls (inflated clustered SEs, 13 clusters)
- `did_devin` remains robustly significant in M1 and M2
- `did_llama2`/`did_code_llama` significant in M3 (HHI)
- `did_copilot_beta` M1 significance disappears (p=0.033→0.778)

## DV4: User Retention (Stratified Cox PH)

**Enhancements:** Language stratification, time trend, reputation buckets, ARI×event interactions. L2 penalizer=0.01. 100K subsample.

| Covariate | Old coef | Old p | New coef | New p | Changed |
|-----------|----------|-------|----------|-------|----------|
| ari | 0.0417 | 2.6626e-53 (***) | -0.0000 | 1.0000e+00 (-) | **YES** |
| reg_post_copilot_beta | 0.4160 | 0.0000e+00 (***) | -0.0299 | 3.2917e-02 (**) | **YES** |
| reg_post_copilot_ga | 0.1100 | 2.1421e-22 (***) | 0.0307 | 1.0226e-01 (-) | **YES** |
| reg_post_chatgpt | 0.0864 | 9.1375e-09 (***) | -0.0042 | 8.8051e-01 (-) | **YES** |
| reg_post_gpt4 | 0.0508 | 2.9449e-03 (***) | -0.0411 | 2.4065e-01 (-) | **YES** |
| reg_post_llama2 | 0.0406 | 1.1270e-01 (-) | 0.0442 | 4.6047e-01 (-) |  |
| reg_post_code_llama | -0.6782 | 9.0442e-143 (***) | -0.4103 | 1.5032e-09 (***) |  |
| reg_post_devin | -3.3790 | 2.7717e-129 (***) | -2.1191 | 1.6482e-03 (***) |  |

Concordance = 0.6668, stratified by 13 languages
