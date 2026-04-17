# Four-DV Causal Inference: 8-Event Multi-Break DID

## Design
- **Panel:** language × month, 2018-01 to 2024-03
- **N questions:** 4,395,952
- **Treatment:** ARI (continuous) × Post_Event (8 binary breaks)
- **FE:** Two-way (language + month), demeaned OLS
- **Events:** copilot_beta, copilot_ga, chatgpt, gpt4, llama2, code_llama, devin

## DV1: Answer Supply

### M1: pct_accepted × 8 events
| Event | β | SE | p | Sig |
|-------|------|------|--------|-----|
| chatgpt | +0.004380 | 0.026060 | 0.8666 |  |
| code_llama | -0.023441 | 0.041530 | 0.5726 |  |
| copilot_beta | +0.003267 | 0.014906 | 0.8266 |  |
| copilot_ga | -0.003417 | 0.022147 | 0.8774 |  |
| devin | +0.066701 | 0.041530 | 0.1086 |  |
| gpt4 | -0.060350 | 0.027470 | 0.0283 | * |
| llama2 | -0.020250 | 0.043433 | 0.6412 |  |

### M2: avg_answers_lt × 8 events
| Event | β | SE | p | Sig |
|-------|------|------|--------|-----|
| chatgpt | +0.012767 | 0.026055 | 0.6242 |  |
| code_llama | -0.051659 | 0.041523 | 0.2138 |  |
| copilot_beta | -0.028991 | 0.014903 | 0.0520 |  |
| copilot_ga | -0.041859 | 0.022143 | 0.0590 |  |
| devin | -0.004355 | 0.041523 | 0.9165 |  |
| gpt4 | -0.105476 | 0.027465 | 0.0001 | *** |
| llama2 | -0.003510 | 0.043425 | 0.9356 |  |

### M3: question_count_lt × 8 events
| Event | β | SE | p | Sig |
|-------|------|------|--------|-----|
| chatgpt | -0.391111 | 0.209642 | 0.0624 |  |
| code_llama | -0.463162 | 0.334094 | 0.1660 |  |
| copilot_beta | -0.010122 | 0.119911 | 0.9327 |  |
| copilot_ga | +0.260032 | 0.178162 | 0.1447 |  |
| devin | +0.147696 | 0.334094 | 0.6585 |  |
| gpt4 | +0.216990 | 0.220983 | 0.3264 |  |
| llama2 | +0.239985 | 0.349404 | 0.4923 |  |

### Robustness: ChatGPT-only DID
| Event | β | SE | p | Sig |
|-------|------|------|--------|-----|
| chatgpt_only | -0.060186 | 0.010786 | 0.0000 | *** |

## DV2: View Count

### M1: avg_views_lt × 8 events
| Event | β | SE | p | Sig |
|-------|------|------|--------|-----|
| chatgpt | +0.272139 | 0.180195 | 0.1313 |  |
| code_llama | -0.575469 | 0.287166 | 0.0454 | * |
| copilot_beta | +0.249250 | 0.103068 | 0.0158 | * |
| copilot_ga | -0.263296 | 0.153136 | 0.0859 |  |
| devin | -0.889126 | 0.287166 | 0.0020 | ** |
| gpt4 | -0.076125 | 0.189942 | 0.6887 |  |
| llama2 | -0.147820 | 0.300325 | 0.6227 |  |

### M2: total_views_lt × 8 events
| Event | β | SE | p | Sig |
|-------|------|------|--------|-----|
| chatgpt | -0.117264 | 0.182777 | 0.5213 |  |
| code_llama | -1.040770 | 0.291280 | 0.0004 | *** |
| copilot_beta | +0.241173 | 0.104545 | 0.0213 | * |
| copilot_ga | -0.000869 | 0.155331 | 0.9955 |  |
| devin | -0.749741 | 0.291280 | 0.0102 | * |
| gpt4 | +0.145290 | 0.192664 | 0.4510 |  |
| llama2 | +0.095341 | 0.304628 | 0.7544 |  |

### M3: views_per_question_lt × 8 events
| Event | β | SE | p | Sig |
|-------|------|------|--------|-----|
| chatgpt | +0.272139 | 0.180195 | 0.1313 |  |
| code_llama | -0.575469 | 0.287166 | 0.0454 | * |
| copilot_beta | +0.249250 | 0.103068 | 0.0158 | * |
| copilot_ga | -0.263296 | 0.153136 | 0.0859 |  |
| devin | -0.889126 | 0.287166 | 0.0020 | ** |
| gpt4 | -0.076125 | 0.189942 | 0.6887 |  |
| llama2 | -0.147820 | 0.300325 | 0.6227 |  |

## DV3: Knowledge Diversity

### M1: tag_entropy × 8 events
| Event | β | SE | p | Sig |
|-------|------|------|--------|-----|
| chatgpt | +0.097392 | 0.098459 | 0.3228 |  |
| code_llama | +0.103488 | 0.156908 | 0.5097 |  |
| copilot_beta | +0.120089 | 0.056317 | 0.0332 | * |
| copilot_ga | +0.093566 | 0.083674 | 0.2637 |  |
| devin | +0.124618 | 0.156908 | 0.4273 |  |
| gpt4 | +0.135477 | 0.103785 | 0.1921 |  |
| llama2 | -0.043558 | 0.164099 | 0.7907 |  |

### M2: unique_tags_lt × 8 events
| Event | β | SE | p | Sig |
|-------|------|------|--------|-----|
| chatgpt | -0.156665 | 0.157380 | 0.3198 |  |
| code_llama | -0.178161 | 0.250807 | 0.4777 |  |
| copilot_beta | +0.057614 | 0.090018 | 0.5223 |  |
| copilot_ga | +0.234327 | 0.133748 | 0.0801 |  |
| devin | +0.155826 | 0.250807 | 0.5346 |  |
| gpt4 | +0.195421 | 0.165894 | 0.2391 |  |
| llama2 | +0.104467 | 0.262301 | 0.6905 |  |

### M3: tag_concentration × 8 events
| Event | β | SE | p | Sig |
|-------|------|------|--------|-----|
| chatgpt | -0.018304 | 0.012877 | 0.1555 |  |
| code_llama | -0.038392 | 0.020522 | 0.0617 |  |
| copilot_beta | -0.010964 | 0.007366 | 0.1369 |  |
| copilot_ga | +0.008710 | 0.010944 | 0.4263 |  |
| devin | -0.013368 | 0.020522 | 0.5149 |  |
| gpt4 | -0.005998 | 0.013574 | 0.6587 |  |
| llama2 | +0.041166 | 0.021462 | 0.0554 |  |

## DV4: User Retention
Status: ✅ Complete
See `dv4_user_retention/` for Cox PH and KM curves.

## Key Findings
- **Answer Supply**: 1/7 events significant. Strongest: gpt4 (β=-0.0604, p=0.0283). Overall direction: negative.
- **Views**: 3/7 events significant. Strongest: devin (β=-0.8891, p=0.0020). Overall direction: negative.
- **Knowledge Diversity**: 1/7 events significant. Strongest: copilot_beta (β=+0.1201, p=0.0332). Overall direction: positive.
