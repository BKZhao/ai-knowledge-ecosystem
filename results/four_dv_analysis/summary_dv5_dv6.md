# DV5 & DV6 Analysis Summary

## DV5: Answer Concentration
- **Gini coefficient**: measures answer inequality per language-month
- **Top-10% share**: fraction of answers from top 10% answerers
- **HHI**: Herfindahl-Hirschman concentration index
- Panel: 975 lang-months, 13 languages
- Controls: Language FE + Month FE, cluster SE by language

## Key DV5 Results
### gini
- did_gpt4: β=0.0189, p=0.0313
- did_llama2: β=-0.0920, p=0.0172
- did_code_llama: β=0.0560, p=0.0374

### top10_share
- No significant effects

### hhi
- did_copilot_ga: β=-0.0022, p=0.0148
- did_llama2: β=-0.0061, p=0.0000
- did_code_llama: β=0.0042, p=0.0001

## DV6: Question Complexity
- **log_body_len**: log median question body length
- **median_code_blocks**: median code blocks per question
- **frac_with_code**: fraction of questions with code
- Panel: 975 lang-months, 13 languages
- Controls: Language FE + Month FE, cluster SE by language

## Key DV6 Results
### log_body_len
- No significant effects

### median_code_blocks
- did_chatgpt: β=0.2724, p=0.0020
- did_llama2: β=-1.3940, p=0.0002
- did_code_llama: β=1.3835, p=0.0067

### frac_with_code
- did_copilot_ga: β=0.0127, p=0.0000
- did_chatgpt: β=-0.0214, p=0.0061
- did_devin: β=-0.1012, p=0.0000

