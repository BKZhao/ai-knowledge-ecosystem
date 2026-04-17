# DV5 & DV6 Summary

## DV5: User (Asker) Concentration
Panel: 975 lang-months
Controls: Language FE + Month FE, cluster SE by language
Note: SO answers lack Tags in this dataset; concentration computed from question askers.

### gini
- No significant effects

### top10_share
- did_gpt4: β=0.0171, p=0.0382

### hhi
- did_copilot_ga: β=-0.0026, p=0.0005
- did_llama2: β=-0.0067, p=0.0000
- did_code_llama: β=0.0044, p=0.0001

## DV6: Question Complexity
Panel: 975 lang-months
Controls: Language FE + Month FE, cluster SE by language

### log_body_len
- No significant effects

### median_code_blocks
- did_chatgpt: β=0.3006, p=0.0117

### frac_with_code
- did_copilot_ga: β=0.0176, p=0.0000
- did_chatgpt: β=-0.0238, p=0.0127
- did_devin: β=-0.0949, p=0.0001

