# DV5 & DV6 Analysis Summary

Generated: 2026-04-17 15:48:40

## DV5: Questioner Concentration (回答集中度代理)

> Note: Since the parquet data lacks ParentId to link answerers to language tags,
> DV5 uses **questioner concentration** (Gini/HHI/Top10% of question-asking activity
> per user per language per month) as a proxy for community contribution inequality.

- Languages: 13
- Months: 75 (2018-01 to 2024-03)
- Observations: 975

### Regression Results (ChatGPT DID: ARI × Post-ChatGPT)

| Metric | β (DID) | SE | p | Sig |
|--------|---------|-----|---|-----|
| gini | -0.0030 | 0.0256 | 0.9075 |  |
| top10_share | 0.0004 | 0.0208 | 0.9865 |  |
| hhi | -0.0000 | 0.0018 | 0.9905 |  |

### Descriptive Statistics

**gini**: mean=0.1810, sd=0.0493, min=0.0539, max=0.4104
**top10_share**: mean=0.2441, sd=0.0309, min=0.1549, max=0.4358
**hhi**: mean=0.0030, sd=0.0049, min=0.0001, max=0.0436

## DV6: Question Complexity (问题复杂度)

- Languages: 13
- Months: 75 (2018-01 to 2024-03)
- Observations: 975

### Regression Results (ChatGPT DID: ARI × Post-ChatGPT)

| Metric | β (DID) | SE | p | Sig |
|--------|---------|-----|---|-----|
| median_body_length | -33.2308 | 54.0015 | 0.5383 |  |
| median_code_blocks | 0.0390 | 0.3936 | 0.9211 |  |
| frac_with_code | -0.0118 | 0.0260 | 0.6500 |  |

### Descriptive Statistics

**median_body_length**: mean=1276.54, sd=182.54, min=823.00, max=1774.00
**median_code_blocks**: mean=2.58, sd=0.85, min=1.00, max=6.00
**frac_with_code**: mean=0.92, sd=0.04, min=0.78, max=1.00

## Heterogeneity Analysis (High vs Low ARI languages)

**dv5_gini**:
  - low ARI: β=0.0000, p=nan 
  - high ARI: β=0.0000, p=nan 
**dv5_top10_share**:
  - low ARI: β=0.0000, p=nan 
  - high ARI: β=0.0000, p=nan 
**dv5_hhi**:
  - low ARI: β=0.0000, p=nan 
  - high ARI: β=0.0000, p=nan 
**dv6_median_body_length**:
  - low ARI: β=0.0000, p=nan 
  - high ARI: β=0.0000, p=nan 
**dv6_median_code_blocks**:
  - low ARI: β=0.0000, p=nan 
  - high ARI: β=0.0000, p=nan 
**dv6_frac_with_code**:
  - low ARI: β=0.0000, p=nan 
  - high ARI: β=0.0000, p=nan 

## Files Generated

### DV5 Output
- `dv5_gini_event_study.png`
- `dv5_gini_regression.csv`
- `dv5_gini_regression.tex`
- `dv5_gini_trends.png`
- `dv5_hhi_event_study.png`
- `dv5_hhi_regression.csv`
- `dv5_hhi_regression.tex`
- `dv5_hhi_trends.png`
- `dv5_top10_share_event_study.png`
- `dv5_top10_share_regression.csv`
- `dv5_top10_share_regression.tex`
- `dv5_top10_share_trends.png`

### DV6 Output
- `dv6_frac_with_code_event_study.png`
- `dv6_frac_with_code_regression.csv`
- `dv6_frac_with_code_regression.tex`
- `dv6_frac_with_code_trends.png`
- `dv6_median_body_length_event_study.png`
- `dv6_median_body_length_regression.csv`
- `dv6_median_body_length_regression.tex`
- `dv6_median_body_length_trends.png`
- `dv6_median_code_blocks_event_study.png`
- `dv6_median_code_blocks_regression.csv`
- `dv6_median_code_blocks_regression.tex`
- `dv6_median_code_blocks_trends.png`