#!/usr/bin/env python3
"""
Volume III, step 7: render PAPER.md to PDF.

Markdown to HTML to PDF via wkhtmltopdf, so the tables and the figure images
survive. Styling uses the Broadcastwell blues: accent text #1D4ED8, rules and
bars #3B82F6, light blue panel tints. Figures are inserted at the points the
paper refers to them.
"""
import re, os, subprocess, base64, sys
import markdown

SRC = "PAPER.md"
OUT = "State-of-GEO-Volume-III.pdf"
FIGDIR = "figures"

FIGMAP = {
    "*Figure 1: 4x4 Jaccard matrix.*": ("fig1_jaccard_matrix.png",
        "Figure 1. Mean Jaccard similarity of the vendor set, per engine pair, over the "
        "questions both engines answered."),
    "*Figure 2: consensus distribution.*": ("fig2_consensus.png",
        "Figure 2. How many engines named each vendor."),
    "*Figure 3: within-engine versus between-engine agreement.*": ("fig3_within_vs_between.png",
        "Figure 3. The decisive test. Bars are mean Jaccard similarity, whiskers are "
        "bootstrap 95% confidence intervals, both on the same stability questions."),
    "*Figure 5: citation source mix per engine.*": ("fig5_citation_mix.png",
        "Figure 5. Share of citations by source type, per engine."),
    "*Figure 6: v1.0 baseline against v3.0 multi-engine visibility.*": ("fig6_vol1_vs_vol3.png",
        "Figure 6. Volume 1 single-engine baseline against Volume 3 multi-engine visibility."),
}
FIG4 = ("fig4_answer_rate.png",
        "Figure 4. Questions attempted and answered per engine. Bar heights differ "
        "because three API accounts ran out of credit during collection.")

md_text = open(SRC).read()


def img_tag(fn, caption):
    p = os.path.join(FIGDIR, fn)
    if not os.path.exists(p):
        return f'<p class="missing">[missing figure: {fn}]</p>'
    b64 = base64.b64encode(open(p, "rb").read()).decode()
    return (f'<figure><img src="data:image/png;base64,{b64}"/>'
            f'<figcaption>{caption}</figcaption></figure>')


for marker, (fn, cap) in FIGMAP.items():
    md_text = md_text.replace(marker, f"@@FIG:{fn}@@{cap}@@")

# figure 4 belongs with the answer-rate table in 4.0
md_text = md_text.replace(
    "This sits below the trigger rates Seer Interactive reports",
    f"@@FIG:{FIG4[0]}@@{FIG4[1]}@@\n\nThis sits below the trigger rates Seer Interactive reports")

html_body = markdown.markdown(md_text, extensions=["tables", "sane_lists", "attr_list"])

def sub_fig(m):
    return img_tag(m.group(1), m.group(2))

html_body = re.sub(r"@@FIG:([^@]+)@@([^@]+)@@", sub_fig, html_body)

CSS = """
@page { size: A4; margin: 20mm 18mm 18mm 18mm; }
body { font-family: "DejaVu Sans", Helvetica, Arial, sans-serif; font-size: 10.2pt;
       line-height: 1.5; color: #1f2937; }
h1 { font-size: 20pt; color: #111827; line-height: 1.25; margin: 0 0 4pt 0;
     border-bottom: 3px solid #3B82F6; padding-bottom: 8pt; }
h2 { font-size: 13.5pt; color: #1D4ED8; margin: 20pt 0 6pt 0;
     border-bottom: 1px solid #DBEAFE; padding-bottom: 3pt; page-break-after: avoid; }
h3 { font-size: 11.4pt; color: #1f2937; margin: 14pt 0 4pt 0; page-break-after: avoid; }
p { margin: 0 0 8pt 0; text-align: justify; }
strong { color: #111827; }
a { color: #1D4ED8; text-decoration: none; word-break: break-all; }
code { background: #EFF6FF; color: #1D4ED8; padding: 1px 4px; border-radius: 3px;
       font-family: "DejaVu Sans Mono", monospace; font-size: 8.8pt; }
blockquote { background: #EFF6FF; border-left: 4px solid #3B82F6; margin: 10pt 0;
             padding: 8pt 12pt; font-size: 9.6pt; color: #1e3a5f; }
blockquote p { margin: 0 0 4pt 0; text-align: left; }
blockquote p:last-child { margin-bottom: 0; }
table { border-collapse: collapse; width: 100%; margin: 10pt 0 12pt 0;
        font-size: 8.8pt; page-break-inside: avoid; }
th { background: #1D4ED8; color: #fff; text-align: left; padding: 5pt 7pt;
     font-weight: 600; }
td { border-bottom: 1px solid #E5E7EB; padding: 4.5pt 7pt; vertical-align: top; }
tr:nth-child(even) td { background: #F8FAFC; }
figure { margin: 12pt 0 14pt 0; page-break-inside: avoid; text-align: center; }
figure img { max-width: 100%; }
figcaption { font-size: 8.6pt; color: #6B7280; margin-top: 5pt; text-align: left;
             line-height: 1.4; }
ol, ul { margin: 0 0 8pt 0; padding-left: 18pt; }
li { margin-bottom: 4pt; text-align: justify; }
hr { border: none; border-top: 1px solid #DBEAFE; margin: 16pt 0; }
em { color: #4b5563; }
.missing { color: #b91c1c; }
"""

html = f"""<!doctype html><html><head><meta charset="utf-8">
<title>The 2026 State of Generative Engine Optimization, v3.0</title>
<style>{CSS}</style></head><body>{html_body}</body></html>"""

open("PAPER.html", "w").write(html)

cmd = ["wkhtmltopdf", "--enable-local-file-access", "--encoding", "utf-8",
       "--print-media-type", "--page-size", "A4",
       "--margin-top", "18mm", "--margin-bottom", "18mm",
       "--margin-left", "16mm", "--margin-right", "16mm",
       "--footer-font-size", "8", "--footer-font-name", "DejaVu Sans",
       "--footer-left", "The 2026 State of Generative Engine Optimization, v3.0",
       "--footer-right", "[page] of [topage]", "--footer-spacing", "6",
       "--quiet", "PAPER.html", OUT]
subprocess.run(cmd, check=True)

size = os.path.getsize(OUT)
try:
    from pypdf import PdfReader
    pages = len(PdfReader(OUT).pages)
except Exception:
    pages = "?"
print(f"wrote {OUT}: {size:,} bytes, {pages} pages")
