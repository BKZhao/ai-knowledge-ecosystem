# The Disruption of Knowledge Ecosystems by Generative AI

**Evidence from Stack Overflow, GitHub, and 31 Stack Exchange Communities (2018–2026)**

Bingkun Zhao, Maolin Wang  
Hong Kong Institute of AI for Science (HKAI-Sci), City University of Hong Kong

---

## 📊 Key Findings

| Metric | Value |
|--------|-------|
| Stack Overflow decline | **−75.9%** |
| GitHub repo growth | **+138.7%** |
| Communities analyzed | **31** (30 declined, 1 grew) |
| Questions classified | **112,431** |
| AI tool milestones tracked | **12** |
| Data coverage | **99 months** (Jan 2018 – Mar 2026) |

### Notable Discoveries
- **The Scissors Effect**: SO collapsed while GitHub exploded post-ChatGPT
- **The Historic Inversion**: Conceptual questions surpassed How-to for the first time in 2024
- **The Philosophy Paradox**: Only Philosophy SE grew (+16.1%) among 31 communities
- **ARI Irrelevance**: AI capability (ARI) does NOT predict decline magnitude (r = −0.02, p = 0.74)
- **Multi-Agent Cascade**: Each successive AI tool (Copilot → ChatGPT → GPT-4 → Claude → Cursor → DeepSeek) deepened the decline

---

## 📁 Repository Structure

```
├── latex/                    # LaTeX source code
│   └── main.tex              # Complete paper (compile with pdflatex)
├── src/
│   ├── analysis/             # Analysis scripts
│   │   ├── 01_descriptive.py
│   │   ├── 02_event_study.py
│   │   ├── 03_did_analysis.py
│   │   ├── 04_knowledge_complexity.py
│   │   └── 05_user_survival.py
│   ├── regression/           # Regression scripts
│   │   └── run_regressions_v2.py
│   └── data_collection/      # Data collection scripts
│       ├── build_control_vars.py
│       └── classify_extended.py
├── data/
│   ├── processed/            # Processed datasets (CSV, JSON)
│   └── features/             # Feature engineering outputs
├── output/
│   ├── figures/              # All publication-quality figures (22 PNG, 200 DPI)
│   ├── papers/               # Generated PDF papers
│   └── tables/               # Formatted tables
├── RESEARCH_DESIGN_V2.md     # Full research design document
└── results/                  # Intermediate analysis results
```

---

## 🔬 Methodology

- **Primary method**: Stacked panel Difference-in-Differences (DID)
- **Treatment**: ChatGPT launch (Nov 30, 2022) + multi-agent timeline
- **Controls**: COVID-19, tech layoffs, SO policy changes, AI capability index
- **Classification**: LLM-based (How-to / Conceptual / Debug / Architecture)
- **Robustness**: 7 model specifications, placebo tests, staggered adoption

---

## 📈 Main Regression Results (M3: Preferred)

| Variable | Coefficient | Std. Error | p-value | R² |
|----------|------------|-----------|---------|-----|
| β_SO (ChatGPT × SO) | −2.258 | 0.187 | < 0.001 | 0.888 |
| β_GH (ChatGPT × GitHub) | +3.823 | 0.289 | < 0.001 | |

---

## 🚀 Reproduction

1. Clone the repository
2. Install dependencies: `pip install pandas numpy matplotlib scipy statsmodels`
3. Run regressions: `python src/regression/run_regressions_v2.py`
4. Generate figures: `python src/analysis/01_descriptive.py` (etc.)
5. Compile paper: `cd latex && pdflatex main.tex`

---

## 📧 Contact

- **Bingkun Zhao**: bingkzhao2-c@my.cityu.edu.hk
- **Affiliation**: Hong Kong Institute of AI for Science (HKAI-Sci), City University of Hong Kong

---

## License

Research use only. Data from Stack Exchange and GitHub APIs used under their respective terms of service.
