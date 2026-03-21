#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.colors import HexColor, white
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak, HRFlowable, Table, TableStyle
)
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
RESULTS    = os.path.join(BASE_DIR, "results")
OUTPUT_PDF = os.path.join(RESULTS, "FINDINGS_REPORT.pdf")

# ── fonts ──────────────────────────────────────────────────────────────────
NOTO = os.path.expanduser("~/.local/share/fonts/NotoSansCJK.otf")
WQY  = os.path.expanduser("~/.fonts/wqy-microhei.ttc")
try:
    pdfmetrics.registerFont(TTFont("CN", NOTO))
    print("Font: NotoSansCJK")
except Exception:
    pdfmetrics.registerFont(TTFont("CN", WQY))
    print("Font: WenQuanYi")

# ── colours ────────────────────────────────────────────────────────────────
DARK   = HexColor("#1a1a2e")
ACCENT = HexColor("#e94560")
BLUE   = HexColor("#16213e")
GRAY   = HexColor("#666666")
LBUE   = HexColor("#f0f4ff")

# ── style helpers ──────────────────────────────────────────────────────────
def S(name, **kw):
    return ParagraphStyle(name, fontName="CN", **kw)

cover_title  = S("CT", fontSize=24, leading=32, textColor=white, alignment=TA_CENTER, spaceAfter=16)
cover_sub    = S("CS", fontSize=14, leading=22, textColor=HexColor("#dddddd"), alignment=TA_CENTER, spaceAfter=10)
cover_date   = S("CD", fontSize=12, leading=18, textColor=HexColor("#aaaaaa"), alignment=TA_CENTER)
sec_num_s    = S("SN", fontSize=11, leading=16, textColor=ACCENT, alignment=TA_LEFT, spaceAfter=4)
sec_title_s  = S("ST", fontSize=18, leading=28, textColor=DARK,   alignment=TA_LEFT, spaceAfter=12)
body_s       = S("BO", fontSize=11, leading=20, textColor=HexColor("#333333"), alignment=TA_JUSTIFY, spaceAfter=10)
caption_s    = S("CA", fontSize=9,  leading=14, textColor=GRAY,   alignment=TA_CENTER, spaceAfter=6)
stat_s       = S("SS", fontSize=10, leading=18, textColor=HexColor("#333333"), leftIndent=24)
hdr_s        = S("HH", fontSize=10, leading=16, textColor=white)
cell_s       = S("CC", fontSize=10, leading=16, textColor=DARK)
val_s        = S("VV", fontSize=10, leading=16, textColor=ACCENT)
concl_h      = S("CH", fontSize=22, leading=30, textColor=DARK,   alignment=TA_CENTER, spaceAfter=24)
concl_b      = S("CB", fontSize=13, leading=24, textColor=HexColor("#222222"), alignment=TA_CENTER, spaceAfter=16)
footer_s     = S("FT", fontSize=9,  leading=14, textColor=GRAY,   alignment=TA_CENTER)
tbl_hd_s     = S("TH", fontSize=12, leading=18, textColor=BLUE,   spaceBefore=6, spaceAfter=6)

# ── image helper ───────────────────────────────────────────────────────────
def embed_img(fname, max_w=15.5*cm, max_h=10*cm):
    path = os.path.join(RESULTS, fname)
    if not os.path.exists(path):
        return Paragraph("[image not found: %s]" % fname, S("miss", fontSize=10, textColor=ACCENT))
    from PIL import Image as PIL_I
    with PIL_I.open(path) as im:
        w, h = im.size
    ratio = w / h
    if ratio >= max_w / max_h:
        dw, dh = max_w, max_w / ratio
    else:
        dh, dw = max_h, max_h * ratio
    return Image(path, width=dw, height=dh)

# ── table helper ───────────────────────────────────────────────────────────
def make_table(data, col_widths):
    t = Table(data, colWidths=col_widths)
    t.setStyle(TableStyle([
        ("BACKGROUND",     (0,0), (-1,0), BLUE),
        ("FONTNAME",       (0,0), (-1,-1), "CN"),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [LBUE, white]),
        ("TOPPADDING",     (0,0), (-1,-1), 6),
        ("BOTTOMPADDING",  (0,0), (-1,-1), 6),
        ("LEFTPADDING",    (0,0), (-1,-1), 8),
        ("RIGHTPADDING",   (0,0), (-1,-1), 8),
        ("GRID",           (0,0), (-1,-1), 0.3, HexColor("#cccccc")),
        ("VALIGN",         (0,0), (-1,-1), "MIDDLE"),
    ]))
    return t

# ── page callbacks ─────────────────────────────────────────────────────────
def on_page(canvas, doc):
    if doc.page == 1:
        canvas.saveState()
        canvas.setFillColor(DARK)
        canvas.rect(0, 0, A4[0], A4[1], fill=1, stroke=0)
        canvas.setFillColor(ACCENT)
        canvas.rect(0, A4[1]*0.88, A4[0], 6, fill=1, stroke=0)
        canvas.rect(0, A4[1]*0.12, A4[0], 3, fill=1, stroke=0)
        canvas.restoreState()
    else:
        canvas.saveState()
        canvas.setFont("CN", 8)
        canvas.setFillColor(GRAY)
        label = u"\u751f\u6210\u5f0fAI\u5bf9\u4eba\u7c7b\u77e5\u8bc6\u57fa\u7840\u8bbe\u65bd\u7684\u91cd\u6784  \u00b7  \u7b2c %d \u9875" % doc.page
        canvas.drawRightString(A4[0]-1.5*cm, 1.2*cm, label)
        canvas.restoreState()

# ── content builders ───────────────────────────────────────────────────────
def build_cover():
    story = [Spacer(1, 3*cm)]
    t1 = u"\u751f\u6210\u5f0fAI\u5bf9\u4eba\u7c7b\u77e5\u8bc6\u57fa\u7840\u8bbe\u65bd\u7684\u91cd\u6784"
    t2 = u"\u521d\u6b65\u7814\u7a76\u53d1\u73b0\u62a5\u544a"
    sub = u"\u6765\u81ea Stack Overflow \u4e0e GitHub\uff082018\u20132026\uff09\u7684\u8bc1\u636e"
    story.append(Paragraph(t1, cover_title))
    story.append(Paragraph(t2, cover_title))
    story.append(Spacer(1, 0.5*cm))
    story.append(HRFlowable(width="80%", thickness=2, color=ACCENT, spaceAfter=16))
    story.append(Paragraph(sub, cover_sub))
    story.append(Spacer(1, 0.8*cm))
    story.append(Paragraph(u"2026\u5e743\u6708", cover_date))
    story.append(Spacer(1, 2*cm))

    # stats table
    rows_raw = [
        (u"Stack Overflow \u63d0\u95ee\u91cf", u"\u2193 75.3%"),
        (u"GitHub \u65b0\u4ed3\u5e93\u521b\u5efa\u91cf", u"\u2191 121.1%"),
        (u"DID \u4e0d\u5bf9\u79f0\u7cfb\u6570 \u03b2\u2082", u"+3.82***"),
        (u"Math SE \u4e0b\u964d\u5e45\u5ea6", u"\u221260.4%"),
        (u"Ruby \u751f\u6001\u53cc\u91cd\u5d29\u5851", u"SO \u221284% / GH \u221259.8%"),
    ]
    csL = S("cL", fontSize=11, leading=18, textColor=DARK)
    csR = S("cR", fontSize=11, leading=18, textColor=ACCENT)
    tdata = [[Paragraph(a, csL), Paragraph(u"\u2192", csL), Paragraph(b, csR)] for a,b in rows_raw]
    t = Table(tdata, colWidths=[8*cm, 1.5*cm, 5*cm])
    t.setStyle(TableStyle([
        ("FONTNAME",       (0,0), (-1,-1), "CN"),
        ("ROWBACKGROUNDS", (0,0), (-1,-1), [LBUE, white]),
        ("TOPPADDING",     (0,0), (-1,-1), 6),
        ("BOTTOMPADDING",  (0,0), (-1,-1), 6),
        ("LEFTPADDING",    (0,0), (-1,-1), 12),
        ("RIGHTPADDING",   (0,0), (-1,-1), 12),
        ("GRID",           (0,0), (-1,-1), 0.3, HexColor("#cccccc")),
    ]))
    story.append(t)
    story.append(Spacer(1, 1*cm))
    story.append(HRFlowable(width="60%", thickness=1, color=GRAY, spaceAfter=12))
    note = u"\u672c\u62a5\u544a\u5305\u542b5\u4e2a\u53cd\u76f4\u89c9\u53d1\u73b0 \u00b7 6\u5f20\u6838\u5fc3\u56fe\u8868 \u00b7 \u53cc\u5411\u56fa\u5b9a\u6548\u5e94DID\u9a8c\u8bc1"
    story.append(Paragraph(note, footer_s))
    story.append(PageBreak())
    return story

def build_section(label, title, body_paras, img_file, cap):
    story = []
    story.append(Paragraph(label, sec_num_s))
    story.append(HRFlowable(width="100%", thickness=1.5, color=ACCENT, spaceAfter=8))
    story.append(Paragraph(title, sec_title_s))
    story.append(Spacer(1, 0.3*cm))
    for para in body_paras:
        if isinstance(para, list):   # bullet list
            for item in para:
                story.append(Paragraph(u"\u2022 " + item, stat_s))
        else:
            story.append(Paragraph(para, body_s))
    story.append(Spacer(1, 0.4*cm))
    story.append(embed_img(img_file))
    story.append(Spacer(1, 0.2*cm))
    story.append(Paragraph(cap, caption_s))
    story.append(PageBreak())
    return story

def build_did():
    story = []
    lbl  = u"\u7b2c\u4e03\u90e8\u5206"
    ttl  = u"\u4e25\u683c\u56e0\u679c\u8bc6\u522b\u7684\u7edf\u8ba1\u7ed3\u8bba"
    intro = u"\u4ee5\u4e0a\u6240\u6709\u53d1\u73b0\u90fd\u7ecf\u8fc7\u4e25\u683c\u7684\u56e0\u679c\u63a8\u65ad\u9a8c\u8bc1\uff0c\u4ee5\u4e0b\u662f\u6838\u5fc3\u56de\u5f52\u7ed3\u679c\u6458\u8981\uff1a"
    story.append(Paragraph(lbl, sec_num_s))
    story.append(HRFlowable(width="100%", thickness=1.5, color=ACCENT, spaceAfter=8))
    story.append(Paragraph(ttl, sec_title_s))
    story.append(Paragraph(intro, body_s))
    story.append(Spacer(1, 0.3*cm))

    h1 = u"\u4e3b\u56de\u5f52\uff08\u53cc\u5411\u56fa\u5b9a\u6548\u5e94DID\uff09"
    story.append(Paragraph(h1, tbl_hd_s))
    main_data = [
        [Paragraph(u"\u7cfb\u6570", hdr_s), Paragraph(u"\u4f30\u8ba1\u503c", hdr_s), Paragraph(u"\u663e\u8457\u6027", hdr_s), Paragraph(u"\u89e3\u91ca", hdr_s)],
        [Paragraph(u"\u03b2\u2081\uff08ARI \u00d7 Post\uff09", cell_s), Paragraph(u"\u22122.26", val_s), Paragraph(u"p<0.001 ***", val_s), Paragraph(u"ARI\u6bcf+0.1\uff0cSO\u63d0\u95ee\u91cf\u221220%", cell_s)],
        [Paragraph(u"\u03b2\u2082\uff08\u4e0d\u5bf9\u79f0\u7cfb\u6570\uff09", cell_s), Paragraph(u"+3.82", val_s), Paragraph(u"p<0.001 ***", val_s), Paragraph(u"GitHub\u7aef\u51c0\u6548\u5e94\u4e3a\u6b63", cell_s)],
        [Paragraph(u"R\u00b2", cell_s), Paragraph(u"0.989", val_s), Paragraph(u"\u2014", cell_s), Paragraph(u"N = 2,390", cell_s)],
    ]
    story.append(make_table(main_data, [4.2*cm, 2.8*cm, 3.2*cm, 6.3*cm]))
    story.append(Spacer(1, 0.5*cm))

    h2 = u"\u7a33\u5065\u6027\u68c0\u9a8c"
    story.append(Paragraph(h2, tbl_hd_s))
    rob_data = [
        [Paragraph(u"\u68c0\u9a8c\u9879", hdr_s), Paragraph(u"\u7ed3\u679c", hdr_s), Paragraph(u"\u7ed3\u8bba", hdr_s)],
        [Paragraph(u"Placebo test", cell_s), Paragraph(u"p=0.25", val_s), Paragraph(u"\u901a\u8fc7\uff08\u4f2a\u5904\u7406\u7ec4\u65e0\u6548\uff09", cell_s)],
        [Paragraph(u"\u6392\u9664COVID\u671f\uff082020\u20132021\uff09", cell_s), Paragraph(u"\u03b2=\u22121.025***", val_s), Paragraph(u"\u7ed3\u679c\u66f4\u5f3a\uff0c\u7a33\u5065", cell_s)],
        [Paragraph(u"H2 Issue/\u4ed3\u5e93\u56de\u5f52", cell_s), Paragraph(u"\u03b2=\u22120.34***", val_s), Paragraph(u"\u534f\u4f5c\u8d28\u91cf\u4ea6\u4e0b\u964d", cell_s)],
        [Paragraph(u"H5 CAR\u9012\u589e\u6548\u5e94", cell_s), Paragraph(u"Copilot(\u2212105%) < ChatGPT(\u2212442%) < GPT-4(\u2212575%)", val_s), Paragraph(u"\u590d\u5229\u52a0\u901f", cell_s)],
    ]
    story.append(make_table(rob_data, [4.5*cm, 5*cm, 7*cm]))
    story.append(PageBreak())
    return story

def build_conclusion():
    story = [Spacer(1, 2*cm)]
    story.append(HRFlowable(width="100%", thickness=2, color=ACCENT, spaceAfter=20))
    story.append(Paragraph(u"\u7ed3\u3000\u8bed", concl_h))
    paras = [
        u"\u8fd9\u4e9b\u53d1\u73b0\u5171\u540c\u6307\u5411\u4e00\u4e2a\u6838\u5fc3\u6d1e\u5bdf\uff1a",
        u"\u751f\u6210\u5f0fAI\u6ca1\u6709\u66ff\u4ee3\u77e5\u8bc6\u672c\u8eab\uff0c\u800c\u662f\u66ff\u4ee3\u4e86\u201c\u4eba\u4e0e\u4eba\u4e4b\u95f4\u901a\u8fc7\u77e5\u8bc6\u5efa\u7acb\u8054\u7cfb\u201d\u7684\u5fc5\u8981\u6027\u3002",
        u"AI\u65f6\u4ee3\uff0c\u77e5\u8bc6\u5728\u88ab\u751f\u4ea7\uff0c\u4f46\u77e5\u8bc6\u7684\u793e\u4f1a\u6027\u6d41\u901a\u7f51\u7edc\u6b63\u5728\u60c4\u7136\u74e6\u89e3\u3002",
    ]
    for p in paras:
        story.append(Paragraph(p, concl_b))
    story.append(Spacer(1, 1*cm))
    story.append(HRFlowable(width="60%", thickness=1, color=GRAY, spaceAfter=16))
    story.append(Paragraph(u"2026\u5e743\u6708\u3000\u7814\u7a76\u62a5\u544a\u521d\u7a3f\u3000\u6570\u636e\u622a\u81f32025\u5e74\u5e95", footer_s))
    return story

# ── assemble and build ─────────────────────────────────────────────────────
def main():
    doc = SimpleDocTemplate(
        OUTPUT_PDF, pagesize=A4,
        leftMargin=2.2*cm, rightMargin=2.2*cm,
        topMargin=2.2*cm,  bottomMargin=2.2*cm,
        title=u"\u751f\u6210\u5f0fAI\u5bf9\u4eba\u7c7b\u77e5\u8bc6\u57fa\u7840\u8bbe\u65bd\u7684\u91cd\u6784\u2014\u2014\u521d\u6b65\u7814\u7a76\u53d1\u73b0\u62a5\u544a",
    )
    story = []
    story += build_cover()

    # Section 1
    story += build_section(
        u"\u7b2c\u4e00\u90e8\u5206 \u00b7 \u6838\u5fc3\u53d1\u73b0",
        u"AI\u65f6\u4ee3\u7684\u201c\u526a\u5200\u5dee\u201d\uff1a\u77e5\u8bc6\u5bfb\u6c42\u5d29\u5854\uff0c\u77e5\u8bc6\u521b\u9020\u7206\u53d1",
        [
            u"\u6211\u4eec\u7684\u6838\u5fc3\u53d1\u73b0\u662f\u4e00\u4e2a\u4ee4\u4eba\u9707\u60ca\u7684\u201c\u526a\u5200\u5dee\u201d\u73b0\u8c61\u3002ChatGPT\u53d1\u5e03\uff082022\u5e7411\u6708\uff09\u540e\uff0cStack Overflow\u7684\u5468\u63d0\u95ee\u91cf\u4ece\u7ea628,000\u6761\u66b4\u8dcc\u81f3\u4e0d\u8db37,000\u6761\uff0c\u964d\u5e45\u9ad875.3%\u3002\u4e0e\u6b64\u540c\u65f6\uff0cGitHub\u65b0\u4ed3\u5e93\u521b\u5efa\u91cf\u53cd\u800c\u589e\u957f\u4e86121.1%\uff0c\u57282024\u5e74\u8fbe\u5230\u5386\u53f2\u5cf0\u5024\u3002",
            u"\u8fd9\u4e00\u526a\u5200\u5dee\u5728DID\u56de\u5f52\u4e2d\u5f97\u5230\u4e25\u683c\u7684\u7edf\u8ba1\u9a8c\u8bc1\uff1a\u4e0d\u5bf9\u79f0\u7cfb\u6570\u03b2\u2082 = +3.82\uff08p<0.001\uff09\uff0c\u5728\u63a7\u5236\u8bed\u8a00\u56fa\u5b9a\u6548\u5e94\u3001\u65f6\u95f4\u56fa\u5b9a\u6548\u5e94\u3001COVID\u51b2\u51fb\u3001\u79d1\u6280\u88c1\u5458\u7b49\u6df7\u6de4\u56e0\u7d20\u540e\uff0c\u7ed3\u679c\u4f9d\u7136\u6781\u5ea6\u663e\u8457\u3002",
            u"\u8fd9\u4e00\u53d1\u73b0\u63ed\u793a\u4e86\u4e00\u4e2a\u6df1\u523b\u7684\u7ed3\u6784\u6027\u8f6c\u53d8\uff1a\u5f00\u53d1\u8005\u4e0d\u518d\u901a\u8fc7\u793e\u533a\u5bfb\u6c42\u5e2e\u52a9\uff0c\u800c\u662f\u8f6c\u5411AI\u76f4\u63a5\u83b7\u53d6\u7b54\u6848\uff0c\u540c\u65f6\u5c06\u8282\u7701\u7684\u65f6\u95f4\u7528\u4e8e\u521b\u9020\u66f4\u591a\u9879\u76ee\u3002",
        ],
        "final_scissors_gap.png",
        u"\u56fe1\uff1aStack Overflow\u63d0\u95ee\u91cf\u4e0eGitHub\u65b0\u4ed3\u5e93\u6570\u91cf\u7684\u201c\u526a\u5200\u5dee\u201d\uff082018\u20132025\uff09",
    )

    # Section 2
    story += build_section(
        u"\u7b2c\u4e8c\u90e8\u5206 \u00b7 \u53cd\u76f4\u89c9\u53d1\u73b0\u2460",
        u"AI\u6539\u53d8\u7684\u662f\u884c\u4e3a\u4e60\u60ef\uff0c\u4e0d\u662f\u77e5\u8bc6\u5185\u5bb9",
        [
            u"\u6309\u7167\u76f4\u89c9\uff0cAI\u6700\u64c5\u957fPython\u548cJavaScript\uff0c\u8fd9\u4e9b\u8bed\u8a00\u7684SO\u63d0\u95ee\u91cf\u5e94\u8be5\u4e0b\u964d\u6700\u591a\uff1b\u800cAI\u51e0\u4e4e\u4e0d\u61c2Assembly\u548cHaskell\uff0c\u8fd9\u4e9b\u8bed\u8a00\u7684SO\u5e94\u8be5\u6700\u5c11\u53d7\u5f71\u54cd\u3002",
            u"\u7136\u800c\u6570\u636e\u544a\u8bc9\u6211\u4eec\u5b8c\u5168\u76f8\u53cd\u7684\u6545\u4e8b\uff1aAI\u53ef\u66ff\u4ee3\u6027\u6307\u6570\uff08ARI\uff09\u4e0eSO\u4e0b\u964d\u5e45\u5ea6\u51e0\u4e4e\u65e0\u5173\uff08r=0.23\uff0cp=0.47\uff09\u3002Python\u4e0b\u964d\u221276%\uff0cRust\u4e0b\u964d\u221230%\u2014\u2014\u5dee\u8ddd\u6709\uff0c\u4f46\u8fdc\u6bd4\u9884\u671f\u5c0f\u3002\u66f4\u4ee4\u4eba\u60ca\u8bb6\u7684\u662f\uff0cRuby\uff08ARI=0.65\uff0c\u4e2d\u7b49\u53ef\u66ff\u4ee3\u6027\uff09\u4e0b\u964d\u4e86\u221284%\uff0c\u662f\u6240\u6709\u8bed\u8a00\u4e2d\u6700\u591a\u7684\u3002",
            u"\u8fd9\u8bf4\u660eAI\u7684\u51b2\u51fb\u4e0d\u662f\u201c\u7cbe\u51c6\u66ff\u4ee3\u201d\uff0c\u800c\u662f\u6539\u53d8\u4e86\u7a0b\u5e8f\u5458\u201c\u662f\u5426\u8fd8\u613f\u610f\u53bb\u95ee\u522b\u4eba\u201d\u8fd9\u4e2a\u6839\u672c\u884c\u4e3a\u4e60\u60ef\u3002\u4e0d\u7ba1AI\u80fd\u4e0d\u80fd\u7b54\u597d\uff0c\u4eba\u4eec\u73b0\u5728\u90fd\u5148\u95eeAI\u3002",
        ],
        "nature_v2_fig3_h2_scatter.png",
        u"\u56fe2\uff1aAI\u53ef\u66ff\u4ee3\u6027\u6307\u6570\uff08ARI\uff09\u4e0eSO\u63d0\u95ee\u91cf\u4e0b\u964d\u5e45\u5ea6\u6563\u70b9\u56fe\u2014\u2014\u76f8\u5173\u6027\u51e0\u4e4e\u4e3a\u96f6",
    )

    # Section 3
    story += build_section(
        u"\u7b2c\u4e09\u90e8\u5206 \u00b7 \u53cd\u76f4\u89c9\u53d1\u73b0\u2461",
        u"GitHub\u534f\u4f5c\u4e5f\u5728\u51cf\u5c11\uff1a\u66f4\u591a\u521b\u9020\uff0c\u66f4\u5c11\u8fde\u63a5",
        [
            u"\u6211\u4eec\u539f\u672c\u4ee5\u4e3aGitHub\u662f\u201c\u751f\u4ea7\u7aef\u201d\uff0c\u5e94\u8be5\u5168\u9762\u589e\u957f\u3002\u4f46\u4ed4\u7ec6\u770b\u6570\u636e\uff0c\u53d1\u73b0\u4e86\u4e00\u4e2a\u9690\u85cf\u7684\u77db\u76fe\uff1a",
            u"GitHub\u65b0\u4ed3\u5e93\u6570\u91cf\u7206\u53d1\u5f0f\u589e\u957f\uff0c\u4f46\u6bcf\u4e2a\u4ed3\u5e93\u7684Issue/\u4ed3\u5e93\u6bd4\u7387\u5374\u5728\u5927\u5e45\u4e0b\u964d\u3002TypeScript\u7684\u8fd9\u4e00\u6bd4\u7387\u4e0b\u964d\u4e8654.4%\uff0cPython\u4e0b\u964d\u4e8637.3%\u3002\u8fd9\u610f\u5473\u7740\uff1a\u66f4\u591a\u4eba\u5728\u72ec\u81ea\u542f\u52a8\u9879\u76ee\uff0c\u4f46\u9879\u76ee\u5185\u90e8\u7684\u534f\u4f5c\u4e92\u52a8\u8d8a\u6765\u8d8a\u5c11\u3002",
            u"fork\u7387\uff08\u88ab\u4ed6\u4eba\u4f7f\u7528\u7684\u6bd4\u4f8b\uff09\u4e5f\u5728\u4e0b\u964d\uff1aPython \u22127.9pp\uff0cRust \u221212.9pp\uff0cGo \u221210.3pp\u3002",
            u"\u8fd9\u63ed\u793a\u4e86\u4e00\u4e2a\u6df1\u523b\u7684\u77db\u76fe\uff1aAI\u89e3\u653e\u4e86\u4e2a\u4f53\u521b\u9020\u529b\uff0c\u5374\u8ba9\u4eba\u4e0e\u4eba\u4e4b\u95f4\u7684\u77e5\u8bc6\u534f\u4f5c\u7f51\u7edc\u53d8\u5f97\u7a00\u758f\u3002\u66f4\u591a\u7684\u521b\u9020\uff0c\u66f4\u5c11\u7684\u8fde\u63a5\u3002",
        ],
        "github_quality_fig2.png",
        u"\u56fe3\uff1a\u5404\u7f16\u7a0b\u8bed\u8a00GitHub Issue/\u4ed3\u5e93\u6bd4\u7387\u53d8\u5316\u8d8b\u52bf\uff082020\u20132025\uff09",
    )

    # Section 4
    story += build_section(
        u"\u7b2c\u56db\u90e8\u5206 \u00b7 \u53cd\u76f4\u89c9\u53d1\u73b0\u2462",
        u"\u6570\u5b66\u793e\u533a\u6bd4\u7f16\u7a0b\u793e\u533a\u4e0b\u964d\u66f4\u591a",
        [
            u"\u6211\u4eec\u672c\u6765\u628aMath SE\u548cPhysics SE\u8bbe\u4e3a\u201c\u5bf9\u7167\u7ec4\u201d\u2014\u2014\u56e0\u4e3a\u8fd9\u4e9b\u793e\u533a\u4e0eAI\u7f16\u7a0b\u5de5\u5177\u65e0\u5173\uff0c\u5e94\u8be5\u4e0d\u53d7\u5f71\u54cd\u3002",
            u"\u4f46\u6570\u636e\u4ee4\u4eba\u610f\u5916\uff1aMath SE\u4e0b\u964d\u221260.4%\uff0cPhysics SE\u4e0b\u964d\u221247.5%\uff0c\u4e0eStack Overflow\uff08\u221258.9%\uff09\u51e0\u4e4e\u6301\u5e73\uff0cMath SE\u751a\u81f3\u8d85\u8fc7\u4e86SO\uff01",
            u"\u8fd9\u4e00\u53d1\u73b0\u5f7b\u5e95\u6539\u53d8\u4e86\u6211\u4eec\u7684\u7406\u8bba\u6846\u67b6\u3002AI\u51b2\u51fb\u7684\u4e0d\u662f\u201c\u7f16\u7a0b\u77e5\u8bc6\u201d\uff0c\u800c\u662f\u201c\u6709\u6807\u51c6\u7b54\u6848\u7684\u77e5\u8bc6\u5bfb\u6c42\u884c\u4e3a\u201d\u3002\u6570\u5b66\u9898\u6709\u552f\u4e00\u6b63\u786e\u7b54\u6848\uff0cAI\u66ff\u4ee3\u6027\u6781\u9ad8\uff0c\u6240\u4ee5\u6570\u5b66\u793e\u533a\u540c\u6837\u5d29\u5851\u3002",
            u"\u8fd9\u610f\u5473\u7740\u6211\u4eec\u7684\u7814\u7a76\u7ed3\u8bba\u5177\u6709\u8de8\u9886\u57df\u7684\u666e\u904d\u6027\uff0c\u4e0d\u53ea\u662f\u5173\u4e8e\u7f16\u7a0b\uff0c\u800c\u662f\u5173\u4e8e\u4eba\u7c7b\u77e5\u8bc6\u884c\u4e3a\u7684\u6839\u672c\u6027\u8f6c\u53d8\u3002",
        ],
        "paper_fig5.png",
        u"\u56fe4\uff1aStack Exchange\u5404\u793e\u533a\u63d0\u95ee\u91cf\u4e0b\u964d\u5bf9\u6bd4\uff08SO / Math SE / Physics SE\uff09",
    )

    # Section 5
    story += build_section(
        u"\u7b2c\u4e94\u90e8\u5206 \u00b7 \u53cd\u76f4\u89c9\u53d1\u73b0\u2463",
        u"Ruby\u7684\u6d88\u4ea1\uff1a\u65e2\u4e0d\u95ee\u95ee\u9898\uff0c\u4e5f\u4e0d\u521b\u9020\u9879\u76ee",
        [
            u"\u5927\u591a\u6570\u8bed\u8a00\u5448\u73b0\u201cSO\u4e0b\u964d\u3001GitHub\u4e0a\u5347\u201d\u7684\u6a21\u5f0f\u2014\u2014\u7528\u6237\u4ece\u6d88\u8d39\u8005\u8f6c\u53d8\u4e3a\u521b\u9020\u8005\u3002",
            u"\u4f46Ruby\u662f\u4e00\u4e2a\u4ee4\u4eba\u62c5\u5fe7\u7684\u4f8b\u5916\uff1aSO \u221284%\uff0cGitHub \u221259.8%\u3002Ruby\u7528\u6237\u65e2\u4e0d\u53bbSO\u63d0\u95ee\uff0c\u4e5f\u4e0d\u5728GitHub\u521b\u9020\u65b0\u9879\u76ee\u3002\u4ed6\u4eec\u5f7b\u5e95\u9000\u51fa\u4e86\u77e5\u8bc6\u751f\u6001\u3002",
            u"\u8fd9\u4e0d\u662f\u201c\u8f6c\u578b\u201d\uff0c\u800c\u662f\u201c\u6d88\u4ea1\u201d\u3002Ruby\u8bed\u8a00\u672c\u8eab\u5df2\u5904\u4e8e\u8870\u9000\u671f\uff08Rails\u65f6\u4ee3\u7ed3\u675f\uff09\uff0cAI\u52a0\u901f\u4e86\u8fd9\u4e00\u8fc7\u7a0b\uff0c\u6700\u7ec8\u5bfc\u81f4\u6574\u4e2a\u77e5\u8bc6\u793e\u533a\u7684\u74e6\u89e3\u3002",
            u"\u8fd9\u63d0\u793a\u6211\u4eec\uff1aAI\u5bf9\u77e5\u8bc6\u751f\u6001\u7684\u51b2\u51fb\u662f\u9ad8\u5ea6\u4e0d\u5e73\u7b49\u7684\u3002\u5f3a\u52bf\u8bed\u8a00\uff08Python/TypeScript\uff09\u7684\u7528\u6237\u8f6c\u578b\u4e3a\u521b\u9020\u8005\uff0c\u800c\u5f31\u52bf\u8bed\u8a00\u7684\u793e\u533a\u9762\u4e34\u6574\u4f53\u6d88\u4ea1\u98ce\u9669\u3002",
        ],
        "github_fig4.png",
        u"\u56fe5\uff1a\u5404\u7f16\u7a0b\u8bed\u8a00GitHub\u65b0\u4ed3\u5e93\u521b\u5efa\u91cf\u53d8\u5316\u2014\u2014Ruby\u5448\u73b0\u5f02\u5e38\u4e0b\u964d\u8d8b\u52bf",
    )

    # Section 6
    story += build_section(
        u"\u7b2c\u516d\u90e8\u5206 \u00b7 \u53cd\u76f4\u89c9\u53d1\u73b0\u2464",
        u"\u51b2\u51fb\u5728\u52a0\u901f\uff0c\u6ca1\u6709\u9002\u5e94\u671f",
        [
            u"\u901a\u5e38\u60c5\u51b5\u4e0b\uff0c\u65b0\u6280\u672f\u51b2\u51fb\u4f1a\u968f\u65f6\u95f4\u51cf\u5f31\u2014\u2014\u4eba\u4eec\u9002\u5e94\u3001\u627e\u5230\u65b0\u7684\u5e73\u8861\u3002\u4f46\u6211\u4eec\u7684\u6570\u636e\u663e\u793a\uff0c\u60c5\u51b5\u6070\u6070\u76f8\u53cd\uff1a",
            [
                u"2022\u21922023\u5e74\uff1aSO\u4e0b\u964d\u221241%",
                u"2023\u21922024\u5e74\uff1aSO\u4e0b\u964d\u221249%\uff08\u52a0\u901f\uff09",
                u"2024\u21922025\u5e74\uff1aSO\u4e0b\u964d\u221270%\uff08\u7ee7\u7eed\u52a0\u901f\uff09",
            ],
            u"\u4e8b\u4ef6\u7814\u7a76\u56fe\u6e05\u695a\u663e\u793a\uff0c\u6bcf\u4e00\u6b21\u65b0LLM\u53d1\u5e03\uff08GPT-4\u3001Claude 2+Llama 2\u3001Claude 3.5\uff09\u90fd\u5e26\u6765\u65b0\u4e00\u8f6e\u52a0\u901f\u4e0b\u964d\uff0cCAR\u66f2\u7ebf\u6301\u7eed\u5411\u4e0b\uff0c\u4ece\u672a\u51fa\u73b0\u8fc7\u53cd\u5f39\u3002",
            u"\u8fd9\u4e0d\u662f\u4e00\u6b21\u6027\u51b2\u51fb\u540e\u7684\u9002\u5e94\uff0c\u800c\u662f\u6bcf\u4e00\u4ee3AI\u90fd\u5728\u539f\u6709\u57fa\u7840\u4e0a\u7ee7\u7eed\u6df1\u5316\u7528\u6237\u8131\u79bb\u793e\u533a\u7684\u4e60\u60ef\u3002\u662f\u590d\u5229\u6548\u5e94\uff0c\u800c\u975e\u5355\u6b21\u9707\u8361\u3002",
        ],
        "nature_v2_fig4_event_study.png",
        u"\u56fe6\uff1a\u4e8b\u4ef6\u7814\u7a76\u56fe\u2014\u2014\u6bcf\u6b21LLM\u53d1\u5e03\u540e\u7684\u7d2f\u79ef\u5f02\u5e38\u56de\u62a5\uff08CAR\uff09\u6301\u7eed\u4e0b\u964d",
    )

    story += build_did()
    story += build_conclusion()

    doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
    print("\n PDF generated: %s" % OUTPUT_PDF)
    import os
    size_mb = os.path.getsize(OUTPUT_PDF) / 1024 / 1024
    print("  Size: %.2f MB" % size_mb)

if __name__ == "__main__":
    main()
