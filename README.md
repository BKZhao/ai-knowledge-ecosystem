# AI Knowledge Ecosystem Research

**Asymmetric Impact of Generative AI on Knowledge Consumption vs. Knowledge Production (2018–2026)**

## Research Question
Does generative AI create asymmetric disruption between knowledge consumption (Stack Overflow) and knowledge production (GitHub)?

## Key Findings
- SO knowledge consumption: **-75.3%** post-ChatGPT
- GitHub knowledge production: **+121.1%** post-ChatGPT
- Asymmetry coefficient β₂ = **+3.82** (p<0.001, two-way FE)

## Data Sources
| Dataset | Size | Coverage |
|---------|------|---------|
| SO API (14 languages) | 424 weeks | 2018-2026 |
| GitHub API (13 languages) | 98 months | 2018-2026 |
| SO Posts (full text) | 21.9M rows | 2018-2026 |
| Control variables | 20 vars | 2018-2026 |
| 12 SE communities | 350 weeks | 2018-2026 |

## Repository Structure
```
├── data/              # Data files (large files excluded)
│   └── parquet/       # Processed Parquet files
├── results/           # Analysis outputs (CSV, JSON)
├── pipeline/          # Data collection scripts
├── analysis/          # Analysis scripts
├── RESEARCH_DESIGN_V2.md  # Research design document
└── README.md
```

## Author
Bingkun Zhao | City University of Hong Kong
