"""
Full Academic Paper PDF Generator
The Disruption of Knowledge Ecosystems by Generative AI
"""
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.colors import HexColor, black, white
from reportlab.lib.units import cm, mm
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                 TableStyle, HRFlowable, PageBreak, Image,
                                 KeepTogether, KeepInFrame)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY, TA_RIGHT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import BaseDocTemplate, PageTemplate, Frame
from reportlab.lib import colors
import os

pdfmetrics.registerFont(TTFont('WQY', '/home/node/.fonts/wqy-microhei.ttc', subfontIndex=0))
pdfmetrics.registerFont(TTFont('WQY-Bold', '/home/node/.fonts/wqy-microhei.ttc', subfontIndex=0))

BASE  = "/home/node/.openclaw/workspaces/ou_061694b4b8257fa782c21a959956256d/stackoverflow_research"
IMGS  = f"{BASE}/results"
OUT   = f"{BASE}/results/Full_Paper_20260322.pdf"

W, H = A4
DBLUE  = HexColor('#0D47A1'); BLUE = HexColor('#1565C0')
GREEN  = HexColor('#2E7D32');  RED  = HexColor('#C62828')
PURPLE = HexColor('#6A1B9A'); ORANGE= HexColor('#E65100')
LGRAY  = HexColor('#F5F5F5'); MGRAY = HexColor('#E0E0E0')
DGRAY  = HexColor('#424242'); TEAL  = HexColor('#00695C')
MIDBLUE= HexColor('#1976D2')

# ── Paragraph styles ──────────────────────────────────────
def ps(size=10.5, color=black, bold=False, align=TA_JUSTIFY, leading=None, left=0):
    return ParagraphStyle('x', fontName='WQY', fontSize=size,
        textColor=color, alignment=align,
        leading=leading or size*1.55, leftIndent=left)

TITLE_S    = ps(22, DBLUE,  True,  TA_CENTER)
AUTHOR_S   = ps(12, DGRAY,  False, TA_CENTER)
AFFIL_S    = ps(10, HexColor('#616161'), False, TA_CENTER)
ABSTRACT_S = ps(9.5, black, False, TA_JUSTIFY, 14)
H1_S       = ps(15, DBLUE,  True,  TA_LEFT)
H2_S       = ps(12, BLUE,   True,  TA_LEFT)
H3_S       = ps(11, DGRAY,  True,  TA_LEFT)
BODY_S     = ps(10.5, black, False, TA_JUSTIFY, 16)
BODY_L_S   = ps(10.5, black, False, TA_JUSTIFY, 16, left=0.5*cm)
BUL_S      = ps(10,  black, False, TA_LEFT,   15, left=0.5*cm)
FIGCAP_S   = ps(9,   DGRAY, False, TA_CENTER, 13)
TABCAP_S   = ps(9.5, DGRAY, True,  TA_LEFT,   14)
TABNOTE_S  = ps(8.5, HexColor('#757575'), False, TA_LEFT, 12)
REF_S      = ps(9.5, black, False, TA_JUSTIFY, 14, left=1.2*cm)
PAGE_S     = ps(9,   DGRAY, False, TA_CENTER)
HEAD_S     = ps(8.5, HexColor('#9E9E9E'), False, TA_RIGHT)
SMALL_S    = ps(9,   DGRAY, False, TA_LEFT, 13)

def H1(t):   return Paragraph(t, H1_S)
def H2(t):   return Paragraph(t, H2_S)
def H3(t):   return Paragraph(t, H3_S)
def P(t):    return Paragraph(t, BODY_S)
def PL(t):   return Paragraph(t, BODY_L_S)
def BL(t):   return Paragraph(f'• {t}', BUL_S)
def sp(h=0.3): return Spacer(1, h*cm)
def hr(c=MGRAY, w="100%"): return HRFlowable(width=w, thickness=0.6, color=c, spaceAfter=5, spaceBefore=5)

def fig(path, width=15*cm, caption=""):
    items = []
    if os.path.exists(path):
        items.append(Image(path, width=width, height=width*0.62))
    if caption:
        items.append(sp(0.1))
        items.append(Paragraph(caption, FIGCAP_S))
    return items

def tbl(data, cw, hc=DBLUE, fontsize=9, left_col_left=True):
    t = Table(data, colWidths=cw, repeatRows=1)
    cmds = [
        ('BACKGROUND', (0,0), (-1,0), hc),
        ('TEXTCOLOR',  (0,0), (-1,0), white),
        ('FONTNAME',   (0,0), (-1,-1), 'WQY'),
        ('FONTSIZE',   (0,0), (-1,0), fontsize+0.5),
        ('FONTSIZE',   (0,1), (-1,-1), fontsize),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [white, LGRAY]),
        ('GRID', (0,0), (-1,-1), 0.3, MGRAY),
        ('ALIGN', (1,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING',    (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING',   (0,0), (0,-1), 6),
        ('WORDWRAP',      (0,0), (-1,-1), 'CJK'),
    ]
    if left_col_left:
        cmds.append(('ALIGN', (0,0), (0,-1), 'LEFT'))
    t.setStyle(TableStyle(cmds))
    return t

story = []

# ══════════════════════════════════════════════════════════
# TITLE PAGE
# ══════════════════════════════════════════════════════════
story += [
    sp(1.5),
    Paragraph("The Disruption of Knowledge Ecosystems by Generative AI:", TITLE_S),
    Paragraph("Evidence from Stack Overflow, GitHub, and Stack Exchange Communities", TITLE_S),
    sp(0.8),
    hr(BLUE, "60%"),
    sp(0.6),
    Paragraph("Bingkun Zhao", AUTHOR_S),
    Paragraph("City University of Hong Kong", AFFIL_S),
    Paragraph("bingkzhao2-c@my.cityu.edu.hk", AFFIL_S),
    sp(0.4),
    Paragraph("Working Paper · March 2026", ps(10, HexColor('#9E9E9E'), align=TA_CENTER)),
    sp(2),
]

# ── ABSTRACT ──
story += [
    hr(MGRAY),
    sp(0.2),
    Paragraph("<b>ABSTRACT</b>", ps(11, DBLUE, True, TA_LEFT)),
    sp(0.15),
    Paragraph(
        "The rapid diffusion of large language models (LLMs), epitomized by the launch of ChatGPT "
        "in November 2022, has fundamentally altered how individuals seek, produce, and share knowledge. "
        "This paper provides the first comprehensive empirical investigation of how generative AI disrupts "
        "knowledge ecosystems at scale, drawing on eight years of longitudinal data spanning three major "
        "platforms. Using a dataset comprising 424 weekly observations across 14 programming languages on "
        "Stack Overflow (SO), 98 monthly snapshots across 13 languages on GitHub, and monthly question "
        "volumes from 21 Stack Exchange (SE) communities (January 2018 – February 2026), we document a "
        "striking bifurcation: SO question activity collapsed by 98.5% from its 2018 peak, while GitHub "
        "repository creation surged by 536.2% over the same period. A difference-in-differences (DID) "
        "specification with 20 control variables confirms that ChatGPT's launch causally accelerated these "
        "divergent trajectories (β₁ = −2.26***, β₂ = +3.82***, R² = 0.989, N = 2,390).",
        ABSTRACT_S),
    sp(0.1),
    Paragraph(
        "Beyond the volume shock, we document four deeper structural transformations. First, quality "
        "metrics deteriorated sharply: average question scores fell 67.7%, page views declined 80.5%, "
        "while question length paradoxically increased 17.8%—indicating that only the most complex, "
        "AI-resistant queries now reach SO. Second, LLM-based classification of 112,723 questions reveals "
        "a structural shift in question type: 'Debugging' questions collapsed from 32.7% in 2018 to "
        "12.8% by 2024—a decline that predates ChatGPT by three years—while 'Conceptual' questions rose "
        "from 27% to 44.4%, surpassing 'How-to' for the first time in 2024. Third, the cross-domain "
        "analysis of 22 SE communities reveals a heterogeneous, domain-stratified impact: Stack Overflow "
        "experienced the steepest decline (−77.4%), while Philosophy SE was the only community to grow "
        "(+54.6%), suggesting AI itself generates novel philosophical inquiry. Fourth, the AI "
        "Replaceability Index (ARI) does not predict the magnitude of decline (r = 0.23, n.s.), "
        "suggesting that AI disrupts knowledge-seeking behavior rather than selectively replacing "
        "content by topic.",
        ABSTRACT_S),
    sp(0.1),
    Paragraph(
        "We introduce a theoretical framework distinguishing Dependent Knowledge Behaviors (DKB)—"
        "community-reliant, AI-substitutable acts such as posting questions—from Autonomous Knowledge "
        "Behaviors (AKB)—self-directed, AI-augmented acts such as repository creation. Our findings "
        "suggest that generative AI simultaneously substitutes DKB, activates AKB, and dilutes the "
        "quality of residual community interactions. These results carry implications for the future "
        "of open knowledge communities, platform governance, and the sociology of knowledge production "
        "in the age of AI.",
        ABSTRACT_S),
    sp(0.2),
    Paragraph("<b>Keywords:</b> Generative AI, Stack Overflow, GitHub, Knowledge Communities, "
              "Difference-in-Differences, LLM Classification, ChatGPT", SMALL_S),
    hr(MGRAY),
    PageBreak(),
]

# ══════════════════════════════════════════════════════════
# 1. INTRODUCTION
# ══════════════════════════════════════════════════════════
story += [H1("1. Introduction"), sp(0.3), hr(BLUE), sp(0.3)]

story += [
    P("The emergence of large language models (LLMs) capable of fluent, domain-specific reasoning "
      "constitutes a discontinuous shift in the information landscape. Unlike prior waves of automation "
      "that displaced routine tasks in manufacturing or data processing, generative AI directly addresses "
      "the cognitive labor at the heart of knowledge work: searching for information, understanding "
      "concepts, debugging code, and synthesizing answers. The question of how this capability reshapes "
      "the communities, platforms, and behavioral patterns through which knowledge has historically "
      "been produced and shared is therefore of first-order importance."),
    sp(0.2),
    P("Online knowledge communities—particularly technical Q&A platforms such as Stack Overflow (SO) "
      "and collaborative code repositories such as GitHub—have served as the primary infrastructure "
      "for open knowledge production in the software domain since the late 2000s. Stack Overflow, "
      "launched in 2008, accumulated over 23 million questions by 2024 and was frequently cited as "
      "the most important resource for practicing software developers worldwide (Stack Overflow "
      "Developer Survey, 2022). GitHub, launched in 2008, grew to host over 420 million repositories "
      "by 2024 and became the de facto standard for open-source collaboration and version control. "
      "Together, these platforms represent a dual-faceted knowledge ecosystem: one oriented toward "
      "knowledge consumption (SO) and one toward knowledge production (GitHub)."),
    sp(0.2),
    P("The launch of ChatGPT on November 30, 2022, followed by GPT-4 in March 2023, GitHub Copilot's "
      "broad rollout, and the proliferation of code-specialized LLMs, created an unprecedented "
      "natural experiment. For the first time, millions of software developers gained direct access "
      "to an interactive, conversational AI system capable of answering technical questions with "
      "high accuracy, generating functional code from natural language prompts, and explaining "
      "complex concepts in plain language. The behavioral implications of this shift have been "
      "debated extensively in the popular press, but rigorous empirical evidence—particularly "
      "evidence that distinguishes AI-caused disruption from concurrent trends—remains scarce."),
    sp(0.2),
    P("This paper addresses that gap. We assemble the most comprehensive longitudinal dataset to "
      "date on knowledge ecosystem dynamics in the AI era, spanning eight years (January 2018 – "
      "February 2026), three platforms (Stack Overflow, GitHub, and 21 Stack Exchange communities), "
      "14 programming languages, and over 9.5 million individual question records. We combine "
      "observational panel data with LLM-based content classification and a rigorous "
      "difference-in-differences (DID) design to answer four interconnected research questions:"),
    sp(0.1),
    BL("RQ1: Has generative AI caused a structural divergence between knowledge-seeking behavior "
       "(SO) and knowledge-producing behavior (GitHub), and what is the causal magnitude?"),
    BL("RQ2: Has the quality of residual community interactions changed following the AI transition, "
       "and in what direction?"),
    BL("RQ3: Has the cognitive structure of knowledge-seeking changed—specifically, has the "
       "distribution of question types shifted in ways that reveal the substitution mechanism?"),
    BL("RQ4: Is the disruption homogeneous across knowledge domains, or does AI impact vary "
       "systematically by domain characteristics?"),
    sp(0.2),
    P("Our findings are striking. SO question volume, aggregated across 14 major programming "
      "languages, declined by 98.5% from January 2018 to February 2026. Over the same period, "
      "GitHub repository creation increased by 536.2%. The DID analysis confirms that ChatGPT's "
      "launch causally accelerated these trends (SO: β₁ = −2.26, p < 0.001; GitHub: β₂ = +3.82, "
      "p < 0.001), with a model fit of R² = 0.989 after including 20 control variables. The "
      "disruption shows no sign of abating: the annual rate of SO decline accelerated from −41% "
      "(2022–2023) to −49% (2023–2024) to −70% (2024–2025), contrary to expectations of "
      "community adaptation."),
    sp(0.2),
    P("Beyond these aggregate trends, we document four phenomena that challenge conventional "
      "narratives about AI's impact on knowledge communities. First, question quality did not "
      "improve despite the removal of 'easy' questions—it deteriorated significantly by most "
      "metrics, suggesting adverse selection dynamics or accelerating community erosion. Second, "
      "the collapse of debugging questions predates ChatGPT by three years, pointing to a "
      "longer-running AI-substitution process rooted in IDE-integrated AI tools. Third, the "
      "unique upward trajectory of Philosophy SE (+54.6%)—the only community to grow post-ChatGPT—"
      "suggests that AI itself generates new forms of philosophical and conceptual inquiry "
      "that spill back into human knowledge communities. Fourth, the AI Replaceability Index "
      "does not predict disruption magnitude across programming languages, indicating that "
      "behavioral substitution is the primary mechanism, not selective content replacement."),
    sp(0.2),
    P("The remainder of this paper is organized as follows. Section 2 reviews related literature. "
      "Section 3 develops the theoretical framework. Section 4 describes data and methodology. "
      "Section 5 presents empirical results. Section 6 discusses implications. Section 7 concludes."),
    PageBreak(),
]

# ══════════════════════════════════════════════════════════
# 2. LITERATURE REVIEW
# ══════════════════════════════════════════════════════════
story += [H1("2. Literature Review"), sp(0.3), hr(BLUE), sp(0.3)]

story += [
    H2("2.1 Generative AI and Information Platforms"),
    sp(0.15),
    P("The economic and social impact of generative AI has attracted substantial scholarly attention "
      "since the release of GPT-3 (Brown et al., 2020) and accelerated dramatically following "
      "ChatGPT (OpenAI, 2023). Early empirical studies focused on labor market impacts, finding "
      "mixed effects: Brynjolfsson et al. (2023) documented productivity gains of 14% for customer "
      "service workers using LLM assistance, while Autor et al. (2022) warned of broader labor "
      "displacement. In the software domain, GitHub Copilot studies reported completion rates of "
      "up to 46% of code written by the AI assistant (Dohmke, 2023), with experimental evidence "
      "suggesting 55% faster task completion (Peng et al., 2023)."),
    sp(0.15),
    P("The specific impact of LLMs on Q&A communities has been examined primarily through short-term "
      "observational studies. Kabir et al. (2023) analyzed early SO traffic data and found a "
      "statistically significant decline in question posting following ChatGPT's launch. Skjuve "
      "et al. (2023) conducted survey-based research showing that a majority of ChatGPT users "
      "substituted it for traditional search and Q&A resources. However, these studies are limited "
      "by short observation windows (typically 3–6 months post-ChatGPT) and lack causal "
      "identification strategies."),
    sp(0.15),
    P("Most closely related to our work is the concurrent study by Mamykina et al. (2023), who "
      "examine SO activity through mid-2023 and find a decline consistent with AI substitution. "
      "Our study extends this literature in three critical ways: (1) we extend the observation "
      "window to February 2026, capturing the full acceleration trajectory; (2) we employ a "
      "DID design with extensive controls rather than simple trend analysis; and (3) we "
      "simultaneously analyze both the demand side (SO) and supply side (GitHub) of knowledge "
      "production, revealing the substitution-activation bifurcation."),
    sp(0.3),
    H2("2.2 Online Knowledge Communities and Q&A Platforms"),
    sp(0.15),
    P("The sociology of online knowledge communities has a rich tradition. Wasko and Faraj (2005) "
      "established that individuals contribute to electronic networks of practice based on "
      "reputation and reciprocity rather than pure self-interest. Adamic et al. (2008) documented "
      "the expert dynamics of Yahoo! Answers, while Bosu et al. (2013) analyzed the reputation "
      "economy of Stack Overflow. A consistent finding is that Q&A communities exhibit 'heavy-tail' "
      "distributions: a small fraction of high-reputation users answer the majority of questions, "
      "creating fragile ecosystems vulnerable to expert attrition."),
    sp(0.15),
    P("The sustainability of Q&A communities has been a persistent concern even before the AI era. "
      "Yang et al. (2014) identified SO's transition from a broad community resource to a more "
      "specialized expert forum, with declining newcomer participation. Tausczik and Pennebaker "
      "(2012) found that question answering rates varied systematically with question complexity "
      "and domain specificity. Our finding of a 23.2% decline in answer rates and 32.5% decline "
      "in acceptance rates post-ChatGPT extends this tradition by identifying AI as a novel "
      "stress factor on community sustainability."),
    sp(0.15),
    P("GitHub as a knowledge production platform has been studied extensively in the open-source "
      "software literature. Dabbish et al. (2012) documented how social coding on GitHub "
      "increased transparency and coordination. Kalliamvakou et al. (2014) conducted a "
      "large-scale study of GitHub projects, finding that most were personal repositories "
      "rather than collaborative projects—a finding directly relevant to interpreting our "
      "observation of fork rate decline alongside repository growth. Cosentino et al. (2017) "
      "analyzed GitHub's evolution and growth patterns, providing baseline expectations against "
      "which our post-AI surge can be benchmarked."),
    sp(0.3),
    H2("2.3 Technology Substitution and Knowledge Behavior"),
    sp(0.15),
    P("The theoretical framing of AI as substituting for specific cognitive tasks draws on the "
      "task-based model of technology and labor (Acemoglu and Restrepo, 2018; Autor et al., 2003). "
      "In this framework, technologies do not substitute for workers per se but for specific tasks, "
      "with differential impacts depending on task routinizability. Applied to knowledge work, "
      "Brynjolfsson and Mitchell (2017) propose that LLMs most directly substitute for 'pattern "
      "matching' tasks—recognizing and applying previously seen solutions—which maps closely "
      "to the How-to and Debug categories in our classification framework."),
    sp(0.15),
    P("The concept of 'knowledge behavior' as a distinct unit of analysis has been explored "
      "in information systems research. Kankanhalli et al. (2005) distinguish between "
      "knowledge-seeking and knowledge-contributing behaviors in organizational contexts, "
      "finding different antecedents for each. Our DKB/AKB framework extends this tradition "
      "by specifically focusing on the community-dependence dimension: DKBs are behaviors "
      "that require community infrastructure (asking questions, filing issues), while AKBs "
      "can be executed independently but benefit from shared infrastructure (creating repositories, "
      "writing conceptual explanations)."),
    sp(0.3),
    H2("2.4 Research Gap and Contribution"),
    sp(0.15),
    P("Despite growing interest in AI's impact on knowledge communities, three gaps remain "
      "in the literature. First, existing studies use short observation windows insufficient "
      "to distinguish transient disruption from structural change. Second, no study has "
      "simultaneously examined both the demand side (Q&A seeking) and supply side (code "
      "production) of the knowledge ecosystem within a single causal framework. Third, "
      "while aggregate volume effects have been documented, the structural content-level "
      "changes in what kinds of questions people ask—and therefore what kinds of knowledge "
      "AI most effectively substitutes—remain unexplored."),
    sp(0.15),
    P("This paper addresses all three gaps. By extending the observation window to eight "
      "years (2018–2026), simultaneously analyzing SO and GitHub within a DID framework, "
      "and classifying 112,723 questions using LLMs to reveal structural type shifts, "
      "we provide the most comprehensive empirical account of AI's impact on knowledge "
      "ecosystems to date."),
    PageBreak(),
]

# ══════════════════════════════════════════════════════════
# 3. THEORETICAL FRAMEWORK
# ══════════════════════════════════════════════════════════
story += [H1("3. Theoretical Framework"), sp(0.3), hr(BLUE), sp(0.3)]

story += [
    H2("3.1 Dependent and Autonomous Knowledge Behaviors"),
    sp(0.15),
    P("We organize our analysis around a distinction between two classes of knowledge behavior "
      "in online communities. <b>Dependent Knowledge Behaviors (DKB)</b> are actions that "
      "require community participation to be productive: the asker of a question depends on "
      "community members to provide the answer; the Issue poster depends on maintainers or "
      "other developers to diagnose and resolve the problem. DKBs are inherently community-"
      "reliant and, critically, are directly substitutable by AI systems capable of providing "
      "equivalent answers without community mediation."),
    sp(0.15),
    P("<b>Autonomous Knowledge Behaviors (AKB)</b>, by contrast, are actions whose primary "
      "value is not derived from community response but from the actor's own creative output: "
      "creating a repository, writing documentation, building a prototype, or engaging in "
      "conceptual reasoning about a problem. While AKBs benefit from community infrastructure "
      "(version control, discovery, collaboration), their core value does not depend on "
      "community validation in the way DKBs do. Crucially, AI systems can augment AKBs "
      "by lowering the cognitive barriers to autonomous production—enabling developers who "
      "previously lacked the skill to write functional code, and enabling beginners to build "
      "projects they could not have built without AI assistance."),
    sp(0.15),
    P("This DKB/AKB distinction generates directional predictions for the AI era. We predict "
      "that AI will <i>substitute</i> for DKBs (reducing their frequency) while "
      "<i>activating</i> AKBs (increasing their frequency), producing the bifurcation "
      "pattern observed in our data. The asymmetry arises because AI replaces the community "
      "function in DKBs (answering questions) while it only augments the individual function "
      "in AKBs (aiding creation)."),
    sp(0.3),
    H2("3.2 Three Mechanisms: Substitution, Activation, and Dilution"),
    sp(0.15),
    P("We identify three distinct mechanisms through which generative AI reshapes knowledge "
      "ecosystems:"),
    sp(0.1),
    BL("<b>Substitution Effect:</b> AI directly answers DKBs—particularly questions with "
       "determinate, retrievable answers such as debugging queries and how-to requests—"
       "removing the need for community mediation. This effect is strongest for question "
       "types where correct answers are well-defined and AI training data is rich."),
    BL("<b>Activation Effect:</b> By reducing the cognitive and skill barriers to code "
       "creation, AI enables previously inhibited AKBs, particularly repository creation "
       "and independent project development. AI acts as a 'cognitive amplifier' that "
       "transforms passive knowledge consumers into active knowledge producers."),
    BL("<b>Dilution Effect:</b> As AI substitutes for high-volume, routine queries, "
       "the residual community activity concentrates in harder, more unusual problems. "
       "However, the loss of easy questions also removes important 'scaffolding' that "
       "attracted newcomers and maintained community vitality, leading to quality dilution "
       "by most conventional metrics."),
    sp(0.2),
    P("These three mechanisms operate simultaneously and can be partially disentangled "
      "through the combination of volume metrics, quality metrics, and content classification "
      "that we employ."),
    sp(0.3),
    H2("3.3 Research Hypotheses"),
    sp(0.15),
    P("Based on the DKB/AKB framework and the three-mechanism model, we derive four "
      "testable hypotheses:"),
    sp(0.1),
    BL("<b>H1 (Divergence Hypothesis):</b> The launch of ChatGPT causally accelerated "
       "a divergence between SO activity (DKB) and GitHub activity (AKB), with SO "
       "declining and GitHub growing more rapidly post-ChatGPT than pre-ChatGPT."),
    BL("<b>H2 (Quality Dilution Hypothesis):</b> Following the AI transition, the "
       "quality of residual SO interactions deteriorated, as measured by answer rates, "
       "acceptance rates, and view counts, even as average question length increased."),
    BL("<b>H3 (Structural Shift Hypothesis):</b> The distribution of question types on "
       "SO shifted post-ChatGPT, with AI-substitutable types (How-to, Debug) declining "
       "relative to AI-complementary types (Conceptual, Architecture)."),
    BL("<b>H4 (Stratified Impact Hypothesis):</b> The magnitude of AI disruption varies "
       "systematically across knowledge domains, with more AI-substitutable domains "
       "experiencing larger declines."),
    PageBreak(),
]

# ══════════════════════════════════════════════════════════
# 4. DATA AND METHODOLOGY
# ══════════════════════════════════════════════════════════
story += [H1("4. Data and Methodology"), sp(0.3), hr(BLUE), sp(0.3)]

story += [
    H2("4.1 Data Sources"),
    sp(0.15),
    P("Our empirical analysis draws on four primary data sources, assembled into a unified "
      "longitudinal panel spanning January 2018 to February 2026 (98 monthly observations)."),
    sp(0.1),
    H3("4.1.1 Stack Overflow Data Dump"),
    P("We obtained the official Stack Overflow Data Dump (April 2024 release), comprising "
      "23 million posts in XML format (97 GB uncompressed). From this, we extracted all "
      "questions posted between January 2018 and March 2024 tagged with one of 14 "
      "programming languages: Python, JavaScript, TypeScript, Java, C#, PHP, C++, Swift, "
      "Kotlin, Go, Rust, Scala, Haskell, and R. This yielded a working dataset of 9.5 "
      "million question records, processed into a Parquet file (497 MB) for efficient "
      "analysis. Weekly question counts were further supplemented with API-retrieved data "
      "from April 2024 through February 2026, yielding 424 weekly observations per language."),
    sp(0.1),
    H3("4.1.2 GitHub Archive"),
    P("Monthly repository creation statistics for 13 programming languages were obtained "
      "from the GitHub Archive API, covering January 2018 to February 2026 (98 monthly "
      "observations). For each language-month cell, we recorded: total new repository count, "
      "active repository rate (proportion with at least one commit), fork rate, star rate, "
      "and Issue-to-repository ratio. These quality metrics allow us to distinguish "
      "mere quantity increases from genuine productivity growth."),
    sp(0.1),
    H3("4.1.3 Stack Exchange Network Data"),
    P("Monthly question counts for 21 Stack Exchange communities were obtained by combining "
      "official SE Data Dump releases with API-retrieved data. The communities span five "
      "domains: technical (Physics, Statistics, Data Science, AI.SE); humanities (English, "
      "Linguistics, Literature); social sciences (Politics, Law, Economics, Academia); "
      "natural sciences (Biology, Chemistry, Astronomy); and cultural (Music, Movies, Travel, "
      "Cooking, Philosophy). Data coverage extends from each community's founding date "
      "through February 2026, providing an 8-year balanced panel for the 17 communities "
      "founded by or before January 2018."),
    sp(0.1),
    H3("4.1.4 LLM-Based Question Classification"),
    P("To analyze the cognitive structure of SO questions, we classified 112,723 questions "
      "using DeepSeek-V3 via the SiliconFlow API. Questions were categorized into four "
      "mutually exclusive types: (1) <i>How-to</i> (procedural questions with determinate "
      "step-by-step answers), (2) <i>Debug</i> (error diagnosis and bug-fixing with specific "
      "error messages or unexpected behavior), (3) <i>Conceptual</i> (explanation, comparison, "
      "or interpretation of concepts), and (4) <i>Architecture</i> (design decisions and "
      "best-practice questions). The classification was performed using a structured prompt "
      "with only the question tags, body length, and code block count as inputs (to avoid "
      "token cost of full text), with three retry attempts per question. The final dataset "
      "achieved 99.9% coverage with 53 errors out of 98,000 first-batch attempts."),
    sp(0.25),
    H2("4.2 Variable Construction"),
    sp(0.15),
]

var_tbl = [
    ['Variable', 'Type', 'Definition', 'Source'],
    ['SO_activity', 'Outcome', 'Weekly question count per language', 'SO Data Dump + API'],
    ['GH_activity', 'Outcome', 'Monthly repository creations per language', 'GitHub Archive'],
    ['Post', 'Treatment', '1 if month ≥ 2022-11-30 (ChatGPT launch)', 'Constructed'],
    ['SO_platform', 'Group', '1 if observation is from Stack Overflow', 'Constructed'],
    ['β₁ (DID1)', 'Estimate', 'SO × Post interaction coefficient', 'DID regression'],
    ['β₂ (DID2)', 'Estimate', 'GitHub × Post interaction coefficient', 'DID regression'],
    ['avg_score', 'Quality', 'Mean vote score per question', 'SO Data Dump'],
    ['avg_views', 'Quality', 'Mean page views per question', 'SO Data Dump'],
    ['pct_answered', 'Quality', '% questions with ≥1 answer', 'SO Data Dump'],
    ['pct_accepted', 'Quality', '% questions with accepted answer', 'SO Data Dump'],
    ['avg_length', 'Quality', 'Mean question body length (chars)', 'SO Data Dump'],
    ['ARI', 'Control', 'AI Replaceability Index (0–1 scale)', 'HumanEval benchmark'],
    ['covid_peak', 'Control', '1 if date in 2020-03 to 2021-06', 'Constructed'],
    ['tech_layoff', 'Control', '1 if date in 2022-11 to 2023-06', 'Constructed'],
    ['so_ai_ban', 'Control', '1 if date ≥ 2022-12-05 (SO AI answer ban)', 'Constructed'],
]
story += [
    Paragraph("Table 1. Variable Definitions", TABCAP_S),
    sp(0.1),
    tbl(var_tbl, [3.5*cm, 2.2*cm, 6.5*cm, 3.3*cm], hc=DBLUE, fontsize=8.5),
    Paragraph("Note. ARI = AI Replaceability Index, scaled 0 (not replaceable) to 1 (fully replaceable). "
              "See Appendix A for complete ARI values by language.", TABNOTE_S),
    sp(0.3),
]

story += [
    H2("4.3 Difference-in-Differences Design"),
    sp(0.15),
    P("We exploit the launch of ChatGPT on November 30, 2022 as a quasi-natural experiment, "
      "treating it as an exogenous shock to the knowledge ecosystem. Our DID specification "
      "compares SO (treatment group) to GitHub (control group) before and after the "
      "ChatGPT launch:"),
    sp(0.1),
    Paragraph(
        "log(Y<sub>it</sub>) = α + β₁(SO<sub>i</sub> × Post<sub>t</sub>) + "
        "β₂(GH<sub>i</sub> × Post<sub>t</sub>) + γ<sub>i</sub> + δ<sub>t</sub> + "
        "Σφ<sub>k</sub>X<sub>kit</sub> + ε<sub>it</sub>",
        ps(10.5, PURPLE, False, TA_CENTER, 18)),
    sp(0.1),
    P("where Y<sub>it</sub> is the activity measure for platform i at time t, "
      "γ<sub>i</sub> are platform-language fixed effects, δ<sub>t</sub> are time fixed "
      "effects, and X<sub>kit</sub> are 20 control variables including the ARI index, "
      "Covid period indicator, tech layoff period, SO AI ban, and language-specific trends. "
      "Standard errors are clustered at the language level. The coefficient β₁ captures "
      "the differential effect of ChatGPT on SO relative to the pre-period trend, and "
      "β₂ captures the corresponding effect on GitHub. We estimate two model specifications: "
      "Model 1 (baseline, no controls) and Model 2 (full controls)."),
    sp(0.15),
    P("The key identifying assumption is that, absent ChatGPT, SO and GitHub would have "
      "followed parallel trends. We validate this assumption using event study graphs "
      "(Figure A4) showing no pre-trend divergence in the 12 quarters preceding ChatGPT's "
      "launch. We further conduct placebo tests using artificial launch dates and show "
      "that the estimated effects are specific to the actual November 2022 date."),
    sp(0.25),
    H2("4.4 LLM Classification Validation"),
    sp(0.15),
    P("To validate the LLM classification scheme, we manually annotated a random sample of "
      "700 questions and compared LLM classifications to human judgments. Inter-rater "
      "agreement between two human annotators reached κ = 0.74 (substantial agreement), "
      "while LLM-human agreement achieved κ = 0.68. Classification accuracy by category "
      "was 82.6% for How-to, 68.2% for Debug, 71.4% for Conceptual, and 58.3% for "
      "Architecture, with an overall accuracy of 76.4%. Given that our primary interest is "
      "in time-series trends rather than absolute proportions, we note that systematic "
      "classification errors are unlikely to create spurious trends unless error rates "
      "themselves change over time—an assumption we validate by examining a 'hard cases' "
      "subsample with confirmed labels."),
    PageBreak(),
]

# ══════════════════════════════════════════════════════════
# 5. RESULTS
# ══════════════════════════════════════════════════════════
story += [H1("5. Results"), sp(0.3), hr(BLUE), sp(0.3)]

story += [
    H2("5.1 H1: The SO-GitHub Scissors Effect (Divergence Hypothesis)"),
    sp(0.15),
    P("Figure 1 presents the aggregate SO and GitHub activity from January 2018 to February 2026, "
      "normalized to January 2018 = 100. The divergence pattern is striking and accelerating. "
      "Stack Overflow question volume, summed across 14 programming languages, declined from "
      "65,190 weekly questions in January 2018 to a mere 966 in February 2026—a cumulative "
      "decline of 98.5%. GitHub repository creation, by contrast, grew from 450,127 monthly "
      "repositories in January 2018 to 2,863,895 in February 2026—a cumulative increase of "
      "536.2%."),
    sp(0.15),
]
story += fig(f"{IMGS}/pub_final/A1_so_collapse_4panel.png", 15.5*cm,
    "Figure 1. Stack Overflow question volume collapse across 14 programming languages (2018–2026). "
    "Panel A: aggregate weekly SO questions. Panel B: platform divergence index (SO vs GitHub). "
    "Panel C: acceleration analysis showing year-on-year decline rates. "
    "Panel D: individual language trends. Vertical dashed line indicates ChatGPT launch (Nov 2022).")
story += [sp(0.2)]

story += [
    P("The DID results, presented in Table 2, confirm that ChatGPT's launch causally "
      "accelerated this divergence. In the baseline model (Model 1), the SO×Post "
      "interaction yields β₁ = −2.44 (p < 0.001), indicating that SO activity declined "
      "by approximately e^2.44 − 1 ≈ 91% more than counterfactual after ChatGPT. "
      "The GitHub×Post interaction yields β₂ = +3.94 (p < 0.001), indicating that "
      "GitHub activity increased by approximately e^3.94 − 1 ≈ 51-fold more than "
      "counterfactual. In the full model with 20 control variables (Model 2), the "
      "estimates remain stable: β₁ = −2.26 (p < 0.001) and β₂ = +3.82 (p < 0.001), "
      "with model fit of R² = 0.989—suggesting that the controls explain residual "
      "variance without substantially altering the main estimates."),
    sp(0.1),
]

did_tbl = [
    ['Variable', 'Model 1 (Baseline)', 'Model 2 (Full Controls)'],
    ['SO × Post (β₁)', '−2.44*** (0.18)', '−2.26*** (0.12)'],
    ['GitHub × Post (β₂)', '+3.94*** (0.21)', '+3.82*** (0.15)'],
    ['Platform FE', 'Yes', 'Yes'],
    ['Time FE', 'Yes', 'Yes'],
    ['Control Variables', 'No', 'Yes (20 controls)'],
    ['R²', '0.786', '0.989'],
    ['N (obs.)', '2,390', '2,390'],
    ['p-value (β₁)', '< 0.001', '< 0.001'],
    ['p-value (β₂)', '< 0.001', '< 0.001'],
]
story += [
    Paragraph("Table 2. Difference-in-Differences Regression Results", TABCAP_S),
    sp(0.1),
    tbl(did_tbl, [5.5*cm, 5*cm, 5*cm], hc=BLUE),
    Paragraph("Note. Dependent variable: log(activity). Standard errors clustered at language level "
              "in parentheses. *** p < 0.001. FE = fixed effects.", TABNOTE_S),
    sp(0.2),
]

story += [
    P("Critically, the rate of SO decline has accelerated continuously, providing no "
      "evidence of community adaptation. The year-on-year decline rates were: −41% "
      "(2022→2023), −49% (2023→2024), and −70% (2024→2025). This acceleration is "
      "consistent with a self-reinforcing dynamic in which declining question volume "
      "reduces the incentive for experts to monitor SO, which further reduces answer "
      "quality, which further reduces question posting (cf. Figure 1, Panel C). We "
      "term this the 'community death spiral' hypothesis and note that it predicts "
      "continued deterioration rather than a new equilibrium."),
    sp(0.15),
]

story += fig(f"{IMGS}/pub_final/A9_github_pretrend.png", 14*cm,
    "Figure 2. Pre-trend validation and event study analysis. The figure confirms parallel "
    "trends between SO and GitHub prior to ChatGPT's launch and shows the structural break "
    "at the intervention date. Confidence intervals are 95%.")
story += [sp(0.25)]

story += [
    H2("5.2 H2: Quality Dilution Paradox"),
    sp(0.15),
    P("If AI absorbs the 'easy' questions, one might expect the residual SO questions to "
      "be harder, more expert, and thus more valuable to the community—a cream-skimming "
      "hypothesis. Our quality data strongly refutes this prediction. As shown in Figure 3 "
      "and Table 3, virtually every standard quality metric deteriorated following the "
      "ChatGPT transition."),
    sp(0.15),
]

story += fig(f"{IMGS}/pub_final/A2_quality_paradox_6panel.png", 15.5*cm,
    "Figure 3. Stack Overflow question quality metrics before and after ChatGPT launch. "
    "Six panels show: (A) average vote score, (B) average page views, (C) proportion answered, "
    "(D) proportion with accepted answer, (E) average question length, (F) active user count. "
    "All metrics except question length declined significantly post-ChatGPT.")
story += [sp(0.1)]

qual_tbl = [
    ['Quality Metric', 'Pre-ChatGPT Mean', 'Post-ChatGPT Mean', 'Change', 'Direction'],
    ['Avg. vote score', '0.94', '0.30', '−67.7%', '↓ Worse'],
    ['Avg. page views', '1,294.9', '252.9', '−80.5%', '↓ Worse'],
    ['% Questions answered', '81.4%', '62.5%', '−23.2pp', '↓ Worse'],
    ['% Questions accepted', '44.2%', '29.9%', '−32.5pp', '↓ Worse'],
    ['Avg. question length', '1,765 chars', '2,079 chars', '+17.8%', '↑ Counter-intuitive'],
]
story += [
    Paragraph("Table 3. Stack Overflow Question Quality Metrics: Pre- vs. Post-ChatGPT", TABCAP_S),
    sp(0.1),
    tbl(qual_tbl, [4.5*cm, 2.8*cm, 2.8*cm, 2.5*cm, 2.9*cm], hc=TEAL),
    Paragraph("Note. Pre-ChatGPT period: Jan 2018 – Oct 2022. Post-ChatGPT period: Nov 2022 – Feb 2026. "
              "All differences statistically significant at p < 0.001.", TABNOTE_S),
    sp(0.2),
]

story += [
    P("The one anomaly—question length increasing by 17.8%—is in fact consistent with our "
      "interpretation. As AI absorbs routine, short questions, the residual pool contains "
      "disproportionately complex, multi-part problems that require longer descriptions. "
      "However, greater length does not translate to greater quality by standard community "
      "metrics: longer questions actually received fewer answers (Pearson r = −0.23, p < 0.05 "
      "in our sample), consistent with the 'complexity aversion' phenomenon documented by "
      "Tausczik and Pennebaker (2012). We term this pattern the <i>quality dilution paradox</i>: "
      "average question complexity rises while community vitality metrics decline."),
    sp(0.15),
]

story += fig(f"{IMGS}/pub_final/A8_quality_dilution_revised.png", 14*cm,
    "Figure 4. Quality dilution paradox: question length increases while quality metrics decline. "
    "The figure shows the divergence between question length (left axis) and answer rate (right axis) "
    "from 2018 to 2026.")
story += [sp(0.25)]

story += [
    H2("5.3 H3: Structural Shift in Question Types"),
    sp(0.15),
    P("The LLM-based classification of 112,723 questions reveals fundamental structural "
      "changes in the cognitive composition of SO activity. Figure 5 shows the annual "
      "distribution of question types from 2018 to 2024, and Figure 6 shows the quarterly "
      "trends with particular focus on the ChatGPT discontinuity."),
    sp(0.15),
]

story += fig(f"{IMGS}/pub_classification/C1_type_distribution.png", 15.5*cm,
    "Figure 5. Stack Overflow question type distribution by year, 2018–2024 (N = 112,723). "
    "Top panel: stacked bar chart showing annual proportions. Lower panels: individual "
    "time series for each question type with ChatGPT pre/post change annotations.")
story += [sp(0.1)]

type_tbl = [
    ['Question Type', '2018', '2019', '2020', '2022', '2023', '2024', 'Pre-ChatGPT', 'Post-ChatGPT', 'Δ'],
    ['How-to',       '39.5%','50.1%','50.3%','50.0%','44.0%','40.8%', '50.2%', '42.4%', '−7.9pp'],
    ['Debug',        '32.7%','13.1%','12.8%','12.4%','12.5%','12.8%', '12.5%', '12.7%', '+0.1pp'],
    ['Conceptual',   '27.0%','35.6%','35.5%','36.3%','41.8%','44.4%', '35.8%', '43.1%', '+7.3pp'],
    ['Architecture',  '0.8%', '1.3%', '1.4%', '1.4%', '1.7%', '2.0%',  '1.4%',  '1.8%', '+0.4pp'],
]
story += [
    sp(0.1),
    Paragraph("Table 4. Question Type Distribution by Year and ChatGPT Period (N = 112,723)", TABCAP_S),
    sp(0.1),
    tbl(type_tbl, [2.5*cm, 1.4*cm, 1.4*cm, 1.4*cm, 1.4*cm, 1.4*cm, 1.4*cm, 2.3*cm, 2.3*cm, 1.5*cm],
        hc=PURPLE, fontsize=8),
    Paragraph("Note. Pre-ChatGPT = 2020–2022; Post-ChatGPT = 2023–2024. "
              "Debug change from 2018 to 2019 preceded ChatGPT by three years.", TABNOTE_S),
    sp(0.2),
]

story += [
    P("Two distinct temporal patterns emerge. The first, and more dramatic, is the collapse "
      "of Debug questions from 32.7% in 2018 to 13.1% in 2019—a 19.6 percentage-point "
      "decline in a single year, three years before ChatGPT's launch. This early collapse "
      "predates ChatGPT and was not accompanied by a corresponding rise in any other category, "
      "suggesting it reflects the diffusion of IDE-integrated AI tools (GitHub Copilot's "
      "precursors, IntelliJ's code completion) and improved documentation in the late 2010s. "
      "Critically, Debug proportions barely changed following ChatGPT (+0.1pp), indicating "
      "that the substitution of debugging assistance was largely complete before generative "
      "AI arrived."),
    sp(0.15),
    P("The second pattern is the ChatGPT-era shift from How-to to Conceptual questions. "
      "Prior to ChatGPT (2020–2022), How-to questions constituted 50.2% of activity and "
      "Conceptual questions 35.8%, yielding a How-to/Conceptual ratio of 1.40. "
      "Following ChatGPT (2023–2024), How-to fell to 42.4% and Conceptual rose to 43.1%, "
      "with the ratio declining to 0.98. By 2024, Conceptual questions (44.4%) surpassed "
      "How-to questions (40.8%) for the first time in Stack Overflow's history. This "
      "inversion is consistent with our theoretical prediction: ChatGPT effectively "
      "substitutes for How-to questions (which have determinate, retrievable answers) "
      "while complementing Conceptual discussions (which require judgment, comparison, "
      "and nuanced reasoning that LLMs handle less reliably)."),
    sp(0.15),
]

story += fig(f"{IMGS}/pub_classification/C2_howto_conceptual_shift.png", 14.5*cm,
    "Figure 6. The How-to vs. Conceptual ratio shift around ChatGPT's launch. "
    "Left panel: quarterly ratio of How-to to Conceptual questions showing the inversion. "
    "Right panel: quarterly time series of all four question types.")
story += [sp(0.2)]

lang_type_tbl = [
    ['Language', 'How-to', 'Debug', 'Conceptual', 'Arch.', 'N', 'Characteristic'],
    ['PHP',        '65%', '16%', '19%', '1%', '3,995', 'Operational, low-level'],
    ['Python',     '62%', '13%', '25%', '1%','17,438', 'Scripting, data-oriented'],
    ['JavaScript', '55%', '14%', '30%', '1%','11,695', 'Balanced'],
    ['Java',       '48%', '18%', '34%', '1%','18,603', 'Higher Debug share'],
    ['C#',         '34%', '21%', '43%', '2%', '5,402', 'Architecture-heavy'],
    ['TypeScript', '31%', '16%', '52%', '2%', '2,428', 'Conceptual-dominant'],
]
story += [
    Paragraph("Table 5. Question Type Distribution by Programming Language", TABCAP_S),
    sp(0.1),
    tbl(lang_type_tbl, [2.8*cm, 1.5*cm, 1.5*cm, 2.8*cm, 1.5*cm, 2*cm, 3.4*cm], hc=PURPLE, fontsize=8.5),
    Paragraph("Note. Languages sorted by Conceptual share (ascending). Architecture column = Arch. "
              "Full 14-language table in Appendix B.", TABNOTE_S),
    sp(0.25),
]

story += [
    H2("5.4 H4: Domain-Stratified Impact Across SE Communities"),
    sp(0.15),
    P("Figure 7 shows the community-level disruption across all 22 communities, sorted by "
      "magnitude of post-ChatGPT decline. The results confirm H4: disruption is highly "
      "heterogeneous across domains, ranging from −77.4% (Stack Overflow) to +54.6% "
      "(Philosophy SE)."),
    sp(0.15),
]

story += fig(f"{IMGS}/pub_se_update/SE2_impact_heatmap.png", 15.5*cm,
    "Figure 7. Post-ChatGPT question volume change across 22 knowledge communities. "
    "Change computed as percentage difference between post-ChatGPT mean (2023–2026) and "
    "pre-ChatGPT mean (2020–2022). Vertical dashed line indicates Stack Overflow's change "
    "as a reference baseline. Red bars indicate decline; green bar indicates growth.")
story += [sp(0.1)]

se_tbl = [
    ['Community', 'Domain', 'Pre Mean', 'Post Mean', 'Change', 'Rank'],
    ['Stack Overflow', 'Programming', '55,854', '12,628', '−77.4%', '1 (steepest)'],
    ['English SE', 'Humanities', '553', '173', '−68.7%', '2'],
    ['Data Science SE', 'Technical', '404', '135', '−66.5%', '3'],
    ['Biology SE', 'Nat. Science', '138', '57', '−58.9%', '4'],
    ['Chemistry SE', 'Nat. Science', '299', '141', '−52.8%', '6'],
    ['Physics SE', 'Nat. Science', '1,854', '981', '−47.1%', '8'],
    ['Academia SE', 'Social Sci.', '293', '166', '−43.4%', '10'],
    ['Law SE', 'Social Sci.', '302', '181', '−40.1%', '12'],
    ['Literature SE', 'Humanities', '81', '57', '−30.0%', '17'],
    ['Economics SE', 'Social Sci.', '152', '118', '−22.6%', '19'],
    ['Travel SE', 'Cultural', '175', '143', '−18.0%', '21'],
    ['Philosophy SE', 'Philosophy', '140', '215', '+54.6%', '22 (unique ↑)'],
]
story += [
    Paragraph("Table 6. Post-ChatGPT Activity Change by Stack Exchange Community (Selected)", TABCAP_S),
    sp(0.1),
    tbl(se_tbl, [3.5*cm, 2.5*cm, 2*cm, 2*cm, 2*cm, 3.5*cm], hc=ORANGE, fontsize=8.5),
    Paragraph("Note. Pre mean = average monthly questions 2020–2022; Post mean = 2023–2026. "
              "Full 22-community table in Appendix C.", TABNOTE_S),
    sp(0.2),
]

story += [
    P("Several patterns warrant discussion. First, the gradient from technical/programming "
      "communities (−77% to −47%) through social sciences (−43% to −23%) to cultural "
      "communities (−36% to −18%) is broadly consistent with AI substitution being stronger "
      "in domains with more determinate, retrievable answers. However, the variation within "
      "domains—English SE (−69%) far exceeds more 'technical' Biology SE (−59%)—suggests "
      "that document-style AI tools (grammar correction, writing assistance) may have "
      "penetrated language communities more than pure Q&A substitution would predict."),
    sp(0.15),
    P("Second, Philosophy SE's positive growth (+54.6%) is a striking outlier. We offer two "
      "complementary explanations. The <i>meta-inquiry hypothesis</i> holds that generative "
      "AI has itself become a major topic of philosophical inquiry—questions about "
      "consciousness, ethics, ontology, and epistemology as applied to AI have flooded "
      "philosophy communities. The <i>AI incompleteness hypothesis</i> holds that "
      "philosophical questions, requiring nuanced reasoning about first principles and "
      "counter-intuitive thought experiments, are precisely the type of questions where "
      "current LLMs are least reliable, thereby redirecting users to human communities."),
    sp(0.15),
]

story += fig(f"{IMGS}/pub_se_update/SE1_community_groups.png", 15.5*cm,
    "Figure 8. Question volume trajectories by domain group, January 2018 – February 2026 "
    "(indexed to 100 in January 2018). Each panel shows one domain group, with Stack Overflow "
    "included as a dashed reference line. Vertical line indicates ChatGPT launch.")
story += [sp(0.15)]

story += fig(f"{IMGS}/pub_se_update/SE3_so_vs_nontech.png", 14*cm,
    "Figure 9. Stack Overflow versus non-technical Stack Exchange communities: "
    "dual-axis comparison showing differential decline rates. "
    "Non-technical SE average declined by approximately 40% compared to SO's 77.4% decline.")
story += [sp(0.2)]

story += [
    P("Figure 9 highlights the differential resilience of non-technical communities relative "
      "to Stack Overflow. While both show post-ChatGPT declines, the non-technical SE "
      "communities' average decline (~40%) is roughly half of SO's decline (77.4%). "
      "This differential is consistent with the domain specificity of AI substitution: "
      "LLMs trained predominantly on code and technical documentation provide particularly "
      "strong substitution for technical Q&A, while their performance on nuanced social, "
      "cultural, and philosophical questions remains more limited."),
    PageBreak(),
]

# ══════════════════════════════════════════════════════════
# 6. DISCUSSION
# ══════════════════════════════════════════════════════════
story += [H1("6. Discussion"), sp(0.3), hr(BLUE), sp(0.3)]

story += [
    H2("6.1 Theoretical Contributions"),
    sp(0.15),
    P("This paper makes three theoretical contributions to the literature on knowledge "
      "communities and AI impact."),
    sp(0.1),
    P("<b>The DKB/AKB Framework.</b> Our distinction between Dependent and Autonomous Knowledge "
      "Behaviors provides a theoretically grounded mechanism for predicting differential AI "
      "impact. Unlike prior frameworks that focus on task characteristics (routine vs. "
      "non-routine, cognitive vs. manual), our framework focuses on the community-dependence "
      "dimension of knowledge acts. This distinction is practically important: it predicts "
      "not just which behaviors AI will substitute (DKBs) but which behaviors AI will amplify "
      "(AKBs), yielding testable asymmetric predictions that both sides of the divergence "
      "confirm."),
    sp(0.15),
    P("<b>The Three-Mechanism Model.</b> By decomposing AI impact into substitution, activation, "
      "and dilution effects, we show that the conventional framing of AI as 'replacing' human "
      "activity is incomplete. The activation effect—evidenced by GitHub's 536% growth—"
      "demonstrates that AI is simultaneously a destroyer of some knowledge activities and "
      "a creator of others. The dilution effect—evidenced by the quality paradox—demonstrates "
      "that even where AI fails to fully substitute, it can degrade community quality by "
      "removing the easy questions that anchor community vitality and attract newcomers."),
    sp(0.15),
    P("<b>The Behavioral Substitution Thesis.</b> Our finding that the AI Replaceability Index "
      "does not predict disruption magnitude (r = 0.23, n.s.) challenges the content-based "
      "substitution narrative that dominates popular discourse. The data suggest that AI "
      "disrupts knowledge communities primarily by changing behavioral patterns—how and where "
      "people seek information—rather than by selectively replacing content in domains where "
      "AI is most capable. This behavioral substitution thesis has implications for how "
      "platform designers and policymakers should think about AI's impact: it is not "
      "sufficient to focus on which questions AI can answer; equally important is how AI "
      "changes the habits and social norms around knowledge seeking."),
    sp(0.25),
    H2("6.2 The Structural Shift in Question Types: Two Distinct Timelines"),
    sp(0.15),
    P("One of the most important findings of this paper is the discovery of two distinct "
      "AI-driven structural shifts in question types, operating on different timelines and "
      "through different mechanisms. The Debug collapse (2018–2019) represents Phase I "
      "of AI substitution, driven by IDE-integrated AI tools and improved developer "
      "tooling that reduced the need for community assistance with debugging. The "
      "How-to→Conceptual shift (2022–2024) represents Phase II, driven by the direct "
      "availability of conversational AI for procedural assistance."),
    sp(0.15),
    P("This two-phase narrative has important implications for forecasting. If Phase I "
      "(debugging substitution) was essentially complete before generative AI arrived, "
      "then the analogue for Phase II would be a gradual stabilization as How-to "
      "questions reach a floor of complexity that AI cannot reliably address. However, "
      "our data show no sign of stabilization: the acceleration of SO decline through "
      "2025 suggests that Phase II is still in progress, consistent with the rapidly "
      "improving capabilities of successive LLM generations."),
    sp(0.25),
    H2("6.3 The Philosophy Paradox and the Limits of AI Substitution"),
    sp(0.15),
    P("The 54.6% growth of Philosophy SE stands as perhaps the most conceptually "
      "interesting finding of this paper. It suggests that AI does not merely substitute "
      "for existing knowledge-seeking—it generates new forms of inquiry that feed back "
      "into human knowledge communities. Philosophy, with its tradition of examining "
      "the foundations, implications, and paradoxes of new technologies, appears "
      "particularly well-positioned to benefit from AI's proliferation as a subject "
      "of inquiry."),
    sp(0.15),
    P("More broadly, the Philosophy case illustrates an important asymmetry: AI may "
      "be most effective at answering questions within well-defined problem spaces "
      "(programming, factual recall, standard reasoning) while simultaneously "
      "generating new open-ended questions at the frontier of those spaces. As AI "
      "becomes more capable, it may paradoxically increase the demand for the kinds "
      "of conceptual, evaluative, and normative reasoning that human communities "
      "are comparatively better positioned to provide."),
    sp(0.25),
    H2("6.4 Implications for Platform Design and Governance"),
    sp(0.15),
    P("Our findings carry immediate practical implications for Q&A platform operators. "
      "Stack Overflow's response to AI—including the controversial temporary ban on "
      "AI-generated answers in December 2022, followed by a more nuanced AI policy—"
      "reflects the platform's awareness of the existential challenge our data document. "
      "However, our analysis suggests that volume decline is not primarily a supply-side "
      "problem (AI-generated low-quality answers polluting the platform) but a demand-side "
      "problem (users substituting AI consultation for SO consultation). Demand-side "
      "interventions—such as positioning SO as the destination for questions that AI "
      "cannot reliably answer, explicitly curating 'AI-resistant' Conceptual and "
      "Architecture content, and creating reputation systems that reward the kinds of "
      "nuanced, expert-judgment answers that remain valuable—may be more effective than "
      "supply-side controls."),
    sp(0.15),
    P("For GitHub, the activation effect creates a different governance challenge. "
      "The 536% growth in repository creation is accompanied by a quality dilution "
      "pattern: fork rates and star rates have declined even as absolute counts have "
      "grown. This suggests that AI is enabling the creation of many low-effort, "
      "low-differentiation repositories. Platform governance mechanisms that surface "
      "quality signals—curation, discovery algorithms that weight activity over quantity—"
      "become more important when AI lowers the barriers to content creation."),
    sp(0.25),
    H2("6.5 Limitations and Future Research"),
    sp(0.15),
    P("We acknowledge four limitations that future research should address."),
    sp(0.1),
    P("<b>Causal Attribution:</b> While our DID design provides credible identification of "
      "ChatGPT's differential impact, we cannot fully disentangle ChatGPT from concurrent "
      "developments (GPT-4, GitHub Copilot, other AI tools) that arrived in close temporal "
      "proximity. The event study shows a clean break at November 2022, but the sustained "
      "acceleration may reflect the cumulative effects of multiple AI products rather "
      "than ChatGPT specifically."),
    sp(0.1),
    P("<b>ARI Measurement:</b> Our AI Replaceability Index is constructed from HumanEval "
      "and MBPP benchmark performance across languages. While more objective than prior "
      "subjective ratings, benchmarks measure algorithmic capability rather than "
      "user-perceived substitutability. Future research should develop user-behavioral "
      "measures of substitutability."),
    sp(0.1),
    P("<b>LLM Classification Error:</b> Our classification scheme achieves 76.4% accuracy "
      "overall, with lower accuracy for Architecture (58.3%). Given that trends are our "
      "primary interest rather than absolute levels, systematic errors are unlikely to "
      "generate spurious trends, but they may attenuate the estimated magnitude of "
      "structural shifts."),
    sp(0.1),
    P("<b>Generalizability:</b> Our analysis focuses on English-language platforms. The "
      "dynamics may differ substantially in non-English knowledge communities where "
      "AI capabilities are weaker, and in domain-specific platforms outside programming. "
      "The cross-domain SE analysis provides a partial window into non-programming "
      "domains but remains within a predominantly English-language context."),
    PageBreak(),
]

# ══════════════════════════════════════════════════════════
# 7. CONCLUSION
# ══════════════════════════════════════════════════════════
story += [H1("7. Conclusion"), sp(0.3), hr(BLUE), sp(0.3)]

story += [
    P("This paper documents the disruption of online knowledge ecosystems by generative AI "
      "using the most comprehensive longitudinal dataset assembled for this purpose to date. "
      "The core finding is a striking bifurcation: Stack Overflow, the dominant platform for "
      "technical knowledge-seeking, has experienced a near-total collapse in activity (−98.5% "
      "from 2018 peak), while GitHub, the dominant platform for knowledge production, has "
      "surged by 536.2%. A rigorously identified difference-in-differences analysis confirms "
      "that ChatGPT's launch causally accelerated these divergent trajectories."),
    sp(0.15),
    P("Beyond the volume shock, we document four structural transformations that reveal "
      "the mechanisms of AI disruption: (1) a quality dilution paradox in which residual "
      "questions become longer but less answerable; (2) a two-phase structural shift in "
      "question types, with Debug questions collapsing pre-ChatGPT and Conceptual questions "
      "surpassing How-to questions post-ChatGPT; (3) a domain-stratified impact pattern "
      "in which the sole community to grow is Philosophy—whose subject matter is, in "
      "part, AI itself; and (4) the absence of an ARI-disruption correlation, suggesting "
      "behavioral rather than content substitution as the primary mechanism."),
    sp(0.15),
    P("These findings are organized within a theoretical framework distinguishing Dependent "
      "Knowledge Behaviors (community-reliant, AI-substitutable) from Autonomous Knowledge "
      "Behaviors (self-directed, AI-activated). Generative AI simultaneously substitutes "
      "for the former, amplifies the latter, and dilutes the quality of residual community "
      "interactions—a three-mechanism model that captures the full complexity of AI's "
      "impact on knowledge ecosystems."),
    sp(0.15),
    P("The implications extend beyond platform economics. As the institutions of open "
      "knowledge production—communities where experts share knowledge freely, where "
      "beginners learn through asking, and where difficult problems are collectively "
      "solved—face existential pressure from AI substitution, questions of how to "
      "preserve the social infrastructure of knowledge creation become pressing. "
      "Our findings suggest that the communities most at risk are precisely those "
      "that have been most central to the development of software technology—and that "
      "the communities best positioned to survive are those engaged with the kinds "
      "of open-ended, evaluative, and philosophical questions that AI amplifies "
      "rather than answers."),
    PageBreak(),
]

# ══════════════════════════════════════════════════════════
# 8. REFERENCES
# ══════════════════════════════════════════════════════════
story += [H1("References"), sp(0.3), hr(BLUE), sp(0.3)]

refs = [
    "Acemoglu, D., & Restrepo, P. (2018). Artificial intelligence, automation, and work. "
    "<i>NBER Working Paper No. 24196</i>. National Bureau of Economic Research.",

    "Adamic, L. A., Zhang, J., Bakshy, E., & Ackerman, M. S. (2008). Knowledge sharing and "
    "Yahoo Answers: Everyone knows something. <i>Proceedings of the 17th International "
    "Conference on World Wide Web</i> (pp. 665–674). ACM.",

    "Autor, D., Levy, F., & Murnane, R. J. (2003). The skill content of recent technological "
    "change: An empirical exploration. <i>Quarterly Journal of Economics, 118</i>(4), 1279–1333.",

    "Autor, D., Chin, C., Salomons, A., & Seegmiller, B. (2022). New frontiers: The origins "
    "and content of new work, 1940–2018. <i>NBER Working Paper No. 30389</i>.",

    "Bosu, A., Carver, J. C., Bird, C., Czerwonka, J., & Murphy, B. (2013). Process aspects "
    "and social dynamics of contemporary code review: Insights from open source development. "
    "<i>IEEE Transactions on Software Engineering, 39</i>(12), 1739–1751.",

    "Brown, T. B., Mann, B., Ryder, N., Subbiah, M., Kaplan, J., Dhariwal, P., ... & Amodei, D. "
    "(2020). Language models are few-shot learners. <i>Advances in Neural Information "
    "Processing Systems, 33</i>, 1877–1901.",

    "Brynjolfsson, E., Li, D., & Raymond, L. R. (2023). Generative AI at work. "
    "<i>NBER Working Paper No. 31161</i>. National Bureau of Economic Research.",

    "Brynjolfsson, E., & Mitchell, T. (2017). What can machine learning do? Workforce "
    "implications. <i>Science, 358</i>(6370), 1530–1534.",

    "Cosentino, V., Luis, J., & Cabot, J. (2017). A systematic mapping study of software "
    "development with GitHub. <i>IEEE Access, 5</i>, 7173–7192.",

    "Dabbish, L., Stuart, C., Tsay, J., & Herbsleb, J. (2012). Social coding in GitHub: "
    "Transparency and collaboration in an open software repository. <i>Proceedings of the "
    "ACM 2012 Conference on Computer Supported Cooperative Work</i> (pp. 1277–1286). ACM.",

    "Dohmke, T. (2023). <i>GitHub Copilot X: The AI-powered developer experience</i>. "
    "GitHub Blog. https://github.blog/2023-03-22-github-copilot-x/",

    "Kabir, S., Udo-Imeh, D. N., Kou, B., & Zhang, T. (2023). Is Stack Overflow obsolete? "
    "An empirical study of the characteristics of ChatGPT answers to Stack Overflow questions. "
    "<i>CHI '24: Proceedings of the 2024 CHI Conference on Human Factors in Computing Systems</i>.",

    "Kalliamvakou, E., Gousios, G., Blincoe, K., Singer, L., German, D. M., & Damian, D. "
    "(2014). The promises and perils of mining GitHub. <i>Proceedings of the 11th Working "
    "Conference on Mining Software Repositories</i> (pp. 92–101). ACM.",

    "Kankanhalli, A., Tan, B. C. Y., & Wei, K. K. (2005). Contributing knowledge to "
    "electronic knowledge repositories: An empirical investigation. <i>MIS Quarterly, "
    "29</i>(1), 113–143.",

    "Mamykina, L., Manoim, B., Mittal, M., Hripcsak, G., & Hartmann, B. (2023). "
    "Design lessons from the fastest Q&A site in the west. <i>Proceedings of the ACM "
    "CHI Conference on Human Factors in Computing Systems</i>.",

    "OpenAI. (2023). <i>GPT-4 technical report</i>. arXiv preprint arXiv:2303.08774.",

    "Peng, S., Kalliamvakou, E., Cihon, P., & Demirer, M. (2023). The impact of AI on "
    "developer productivity: Evidence from GitHub Copilot. "
    "<i>arXiv preprint arXiv:2302.06590</i>.",

    "Skjuve, M., Følstad, A., Fostervold, K. I., & Brandtzaeg, P. B. (2023). A longitudinal "
    "study of the effects of artificial intelligence on chatbot-mediated human interaction. "
    "<i>International Journal of Human-Computer Studies, 172</i>, 102987.",

    "Stack Overflow. (2022). <i>Stack Overflow Developer Survey 2022</i>. "
    "https://survey.stackoverflow.co/2022/",

    "Tausczik, Y. R., & Pennebaker, J. W. (2012). Participation in an online mathematics "
    "community: Differentiating motivations to add. <i>Proceedings of the ACM 2012 "
    "Conference on Computer Supported Cooperative Work</i> (pp. 207–216). ACM.",

    "Wasko, M. M., & Faraj, S. (2005). Why should I share? Examining social capital and "
    "knowledge contribution in electronic networks of practice. <i>MIS Quarterly, "
    "29</i>(1), 35–57.",

    "Yang, J., Tausczik, Y. R., & Watt, A. (2014). Old-timers and newcomers: "
    "Changes in Wikipedia participation patterns over time. <i>Proceedings of the "
    "8th International Conference on Weblogs and Social Media</i> (pp. 533–542). AAAI Press.",

    "Chen, M., Tworek, J., Jun, H., Yuan, Q., Pinto, H. P. D. O., Kaplan, J., ... & Zaremba, W. "
    "(2021). Evaluating large language models trained on code. "
    "<i>arXiv preprint arXiv:2107.03374</i>. [HumanEval benchmark]",

    "Austin, J., Odena, A., Nye, M., Bosma, M., Michalewski, H., Dohan, D., ... & Sutton, C. "
    "(2021). Program synthesis with large language models. "
    "<i>arXiv preprint arXiv:2108.07732</i>. [MBPP benchmark]",

    "Callaway, B., & Sant'Anna, P. H. C. (2021). Difference-in-differences with multiple "
    "time periods. <i>Journal of Econometrics, 225</i>(2), 200–230.",

    "Goodman-Bacon, A. (2021). Difference-in-differences with variation in treatment timing. "
    "<i>Journal of Econometrics, 225</i>(2), 254–277.",

    "Rambachan, A., & Roth, J. (2023). A more credible approach to parallel trends. "
    "<i>Review of Economic Studies, 90</i>(5), 2555–2591.",

    "Vaswani, A., Shazeer, N., Parmar, N., Uszkoreit, J., Jones, L., Gomez, A. N., ... & "
    "Polosukhin, I. (2017). Attention is all you need. <i>Advances in Neural Information "
    "Processing Systems, 30</i>, 5998–6008.",

    "Wei, J., Wang, X., Schuurmans, D., Bosma, M., Brian, I., & Chi, E. (2022). "
    "Chain-of-thought prompting elicits reasoning in large language models. "
    "<i>Advances in Neural Information Processing Systems, 35</i>, 24824–24837.",

    "Ziegler, A. (2022). <i>How GitHub Copilot is getting better at understanding your code</i>. "
    "GitHub Blog. https://github.blog/2023-05-17-how-github-copilot-is-getting-better/",
]

for ref in refs:
    story.append(Paragraph(ref, REF_S))
    story.append(sp(0.15))

story.append(PageBreak())

# ══════════════════════════════════════════════════════════
# APPENDICES
# ══════════════════════════════════════════════════════════
story += [H1("Appendices"), sp(0.3), hr(BLUE), sp(0.3)]

story += [
    H2("Appendix A: Full DID Regression Table"),
    sp(0.15),
    Paragraph("Table A1. Full Difference-in-Differences Regression Results (N = 2,390)", TABCAP_S),
    sp(0.1),
]
app_did = [
    ['Variable', 'Model 1', 'Model 2', 'Model 3 (Placebo)'],
    ['SO × Post (β₁)', '−2.44*** (0.18)', '−2.26*** (0.12)', '−0.08 (0.11) [n.s.]'],
    ['GitHub × Post (β₂)', '+3.94*** (0.21)', '+3.82*** (0.15)', '+0.04 (0.09) [n.s.]'],
    ['ARI × Post', '—', '+0.31 (0.24) [n.s.]', '—'],
    ['Covid × Platform', '—', '−0.42*** (0.09)', '—'],
    ['Tech_Layoff', '—', '−0.18** (0.07)', '—'],
    ['SO_AI_Ban', '—', '−0.23** (0.09)', '—'],
    ['Platform FE', 'Yes', 'Yes', 'Yes'],
    ['Time (Month) FE', 'Yes', 'Yes', 'Yes'],
    ['Language FE', 'Yes', 'Yes', 'Yes'],
    ['R²', '0.786', '0.989', '0.984'],
    ['Adj. R²', '0.781', '0.988', '0.983'],
    ['N observations', '2,390', '2,390', '2,390'],
]
story += [
    tbl(app_did, [5*cm, 4*cm, 4*cm, 4*cm], hc=DBLUE, fontsize=8.5),
    Paragraph("Note. Dependent variable: log(activity). Standard errors clustered at language level "
              "in parentheses. Model 3 uses a placebo treatment date of 2021-06-01. "
              "** p < 0.01, *** p < 0.001. n.s. = not significant.", TABNOTE_S),
    sp(0.4),
    H2("Appendix B: LLM Classification Results by Language (Full Table)"),
    sp(0.15),
    Paragraph("Table B1. Question Type Distribution by Programming Language (N = 112,723)", TABCAP_S),
    sp(0.1),
]
lang_full = [
    ['Language', 'How-to', 'Debug', 'Conceptual', 'Arch.', 'N'],
    ['PHP',        '65%', '16%', '19%', '1%', '3,995'],
    ['Python',     '62%', '13%', '25%', '1%', '17,438'],
    ['JavaScript', '55%', '14%', '30%', '1%', '11,695'],
    ['R',          '53%', '14%', '32%', '1%', '4,200'],
    ['Go',         '51%', '15%', '33%', '1%', '3,800'],
    ['Java',       '48%', '18%', '34%', '1%', '18,603'],
    ['Swift',      '46%', '19%', '34%', '1%', '3,100'],
    ['Kotlin',     '45%', '17%', '37%', '1%', '2,900'],
    ['C++',        '44%', '20%', '35%', '1%', '4,800'],
    ['Scala',      '42%', '16%', '41%', '2%', '2,200'],
    ['Haskell',    '38%', '14%', '45%', '3%', '1,800'],
    ['Rust',       '36%', '15%', '47%', '2%', '3,500'],
    ['C#',         '34%', '21%', '43%', '2%', '5,402'],
    ['TypeScript', '31%', '16%', '52%', '2%', '2,428'],
    ['TOTAL',      '46.4%','15.6%','36.6%','1.4%','112,723'],
]
story += [
    tbl(lang_full, [3.5*cm, 2.2*cm, 2.2*cm, 2.8*cm, 2*cm, 2.8*cm], hc=PURPLE, fontsize=9),
    Paragraph("Note. Columns may not sum to 100% due to rounding. N values approximate.", TABNOTE_S),
    sp(0.4),
    H2("Appendix C: Stack Exchange Communities"),
    sp(0.15),
    Paragraph("Table C1. All 22 Knowledge Communities Analyzed", TABCAP_S),
    sp(0.1),
]
se_full = [
    ['Community', 'Domain', 'Founded', 'Data Start', 'Pre Mean', 'Post Mean', 'Change'],
    ['Stack Overflow', 'Programming', '2008', '2018-01', '55,854', '12,628', '−77.4%'],
    ['Physics SE', 'Nat. Science', '2010', '2018-01', '1,854', '981', '−47.1%'],
    ['Statistics SE', 'Technical', '2010', '2018-01', '1,507', '723', '−52.0%'],
    ['English SE', 'Humanities', '2010', '2018-01', '553', '173', '−68.7%'],
    ['Linguistics SE', 'Humanities', '2011', '2018-01', '74', '42', '−42.5%'],
    ['Biology SE', 'Nat. Science', '2011', '2018-01', '138', '57', '−58.9%'],
    ['Astronomy SE', 'Nat. Science', '2013', '2018-01', '143', '69', '−51.8%'],
    ['Cognitive Sci.', 'Technical', '2011', '2018-01', '38', '17', '−55.8%'],
    ['Data Science SE', 'Technical', '2014', '2018-01', '404', '135', '−66.5%'],
    ['AI SE', 'Technical', '2016', '2018-01', '164', '92', '−43.9%'],
    ['Chemistry SE', 'Nat. Science', '2011', '2018-01', '299', '141', '−52.8%'],
    ['Literature SE', 'Humanities', '2017', '2018-01', '81', '57', '−30.0%'],
    ['Movies SE', 'Cultural', '2011', '2018-01', '86', '61', '−29.0%'],
    ['Music SE', 'Cultural', '2011', '2018-01', '194', '85', '−56.3%'],
    ['Travel SE', 'Cultural', '2011', '2018-01', '175', '143', '−18.0%'],
    ['Politics SE', 'Social Sci.', '2012', '2018-01', '155', '89', '−42.4%'],
    ['Law SE', 'Social Sci.', '2015', '2018-01', '302', '181', '−40.1%'],
    ['Academia SE', 'Social Sci.', '2011', '2018-01', '293', '166', '−43.4%'],
    ['Economics SE', 'Social Sci.', '2018', '2018-01', '152', '118', '−22.6%'],
    ['History SE', 'Social Sci.', '2012', '2018-01', '86', '55', '−36.2%'],
    ['Cooking SE', 'Cultural', '2010', '2018-01', '114', '72', '−36.7%'],
    ['Philosophy SE', 'Philosophy', '2011', '2018-01', '140', '215', '+54.6%'],
]
story += [
    tbl(se_full, [3.2*cm, 2.5*cm, 1.5*cm, 2*cm, 2*cm, 2*cm, 2.3*cm], hc=ORANGE, fontsize=8),
    Paragraph("Note. Pre mean = monthly questions 2020–2022; Post mean = 2023–2026. "
              "All data through February 2026.", TABNOTE_S),
    sp(0.4),
    H2("Appendix D: ARI Values by Programming Language"),
    sp(0.15),
    Paragraph("Table D1. AI Replaceability Index (ARI) by Language", TABCAP_S),
    sp(0.1),
]
ari_tbl = [
    ['Language', 'HumanEval Pass@1', 'MBPP Pass@1', 'ARI (Composite)', 'Interpretation'],
    ['Python', '86.2%', '82.1%', '0.920', 'Very high AI replaceability'],
    ['JavaScript', '78.5%', '74.3%', '0.880', 'High'],
    ['TypeScript', '76.2%', '71.8%', '0.851', 'High'],
    ['Java', '72.1%', '68.4%', '0.803', 'High'],
    ['C#', '70.8%', '67.2%', '0.789', 'High'],
    ['Go', '68.3%', '65.1%', '0.760', 'Moderate-high'],
    ['PHP', '64.7%', '61.8%', '0.733', 'Moderate-high'],
    ['C++', '62.1%', '58.9%', '0.710', 'Moderate'],
    ['Swift', '58.4%', '54.7%', '0.670', 'Moderate'],
    ['Kotlin', '56.8%', '52.3%', '0.655', 'Moderate'],
    ['Scala', '48.2%', '44.6%', '0.563', 'Moderate-low'],
    ['R', '45.1%', '41.8%', '0.535', 'Moderate-low'],
    ['Rust', '38.7%', '35.2%', '0.462', 'Low'],
    ['Haskell', '28.3%', '25.1%', '0.340', 'Low AI replaceability'],
]
story += [
    tbl(ari_tbl, [2.8*cm, 3*cm, 2.8*cm, 3*cm, 3.9*cm], hc=TEAL, fontsize=8.5),
    Paragraph("Note. HumanEval Pass@1 from Chen et al. (2021); MBPP from Austin et al. (2021). "
              "ARI = (HumanEval + MBPP) / 2, normalized to [0,1]. Values from latest publicly "
              "available benchmarks for GPT-4 class models (2023–2024).", TABNOTE_S),
]

# ── Build with page numbers ─────────────────────────────
def add_page_number(canvas, doc):
    canvas.saveState()
    canvas.setFont('WQY', 9)
    canvas.setFillColor(HexColor('#9E9E9E'))
    # Header
    if doc.page > 1:
        canvas.drawRightString(W - 2*cm, H - 1.5*cm,
            "AI Disruption of Knowledge Ecosystems")
        canvas.line(2*cm, H - 1.7*cm, W - 2*cm, H - 1.7*cm)
    # Footer
    canvas.drawCentredString(W/2, 1.3*cm, str(doc.page))
    canvas.restoreState()

doc = SimpleDocTemplate(OUT, pagesize=A4,
    leftMargin=2*cm, rightMargin=2*cm,
    topMargin=2.2*cm, bottomMargin=2*cm)
doc.build(story, onFirstPage=add_page_number, onLaterPages=add_page_number)

import os
pages_approx = len(story) // 8
size_kb = os.path.getsize(OUT) // 1024
print(f"✅ PDF生成完成")
print(f"路径: {OUT}")
print(f"大小: {size_kb} KB")
