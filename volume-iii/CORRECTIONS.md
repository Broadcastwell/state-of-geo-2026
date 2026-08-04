# Corrections to Volume III

**No number changed.** Every statistic, confidence interval, sample size and
conclusion in the corrected copy is identical to the one deposited on Zenodo.
The four items below are a presentation defect, a cross-reference defect, a
capitalisation defect and a rounding defect in one figure label.

The archived Zenodo record `10.5281/zenodo.21789120` (v3.0) carries the
**pre-correction** `PAPER.md`, PDF and figure 3. Zenodo files are immutable once
published and this version is frozen, so the record was deliberately not
re-uploaded. **This repository is the corrected copy.** Where the two differ,
the repository is authoritative for wording and for figure 3; the two are
identical on every number.

Corrected 4 August 2026, at source in `analysis/04_figures.py` and
`analysis/05_write_paper.py`, then regenerated. The verification gate
(`analysis/06_verify.py`, 22 checks) passes on the corrected text.

---

## 1. Three cross-references pointed at a section numbering that no longer exists

The results chapter was renumbered from 5 to 4 when the paper was restructured
around the per-engine analysis. Three prose references were left behind.

| Location | Was | Now |
|---|---|---|
| Sample construction | "the company-level tie-back in section 5.6" | section 4.6 |
| Stability subsample | "Section 5.5 reads between-engine…" | Section 4.5 |
| Question-shape note | "section 5.0 treats it as one" | section 4.0 |

Fixed in `05_write_paper.py`. `grep -c "section 5\.\|Section 5\."` on the
corrected `PAPER.md` returns 0.

## 2. The collection table in section 3.8 read as a contradiction

The table's second column was headed "Stopped" and the Claude row read
"09:15 UTC" next to an answer count of "280 of 280". A reader had no way to
reconcile a stop with a complete collection, and nothing on the page explained
why the other two short engines were not simply refilled.

The column is now "What happened", the Claude row states that the account was
topped up and that collection resumed the same day and completed, and a
paragraph follows the table explaining that the collector is idempotent on
`question_id | engine | repeat_index`, and that ChatGPT and Perplexity were
deliberately **not** refilled because a second collection window would make
every cross-engine pair span two windows, letting engine drift between windows
read as engine divergence and inflate the exact quantity the paper measures.

Fixed in `05_write_paper.py`.

## 3. The headline sentence lowercased the engine names

`str.capitalize()` uppercases the first character and lowercases everything
after it, so the decisive-test headline rendered as "on google ai overviews the
separation survives… on claude it appears on raw jaccard". Replaced with a
`sentence_case()` helper that touches only the first character. The sentence
now reads "**On Google AI Overviews… On Claude… raw Jaccard…**".

Fixed in `05_write_paper.py`.

## 4. Figure 3 rounded a real gap to an exact-looking zero

The per-engine gap labels in `fig3_within_vs_between` were formatted to two
decimal places. Claude's length-normalised overlap-coefficient gap of **+0.002**
therefore printed as "+0.00" directly beside the words "not significant",
which reads as an exact zero rather than as a small measured value that the
confidence interval cannot separate from zero. Labels are now three decimal
places throughout the figure.

Fixed in `04_figures.py`. The underlying value is unchanged: +0.002, not
significant. Figure 3 in the Zenodo PDF shows "+0.00" for this cell; the
repository copy shows "+0.002".

## 5. A rounding typo in this README's summary table

The hand-written summary table in the repository README gave the mean pairwise
Jaccard CI upper bound as 0.331. `data/results.json` gives 0.33014, so the
correct rounding is **0.330**, which is what `PAPER.md` has always said because
it is generated from `results.json`. The README now reads 0.330. This defect
existed only in the README; no paper, figure or deposited file was affected.

---

## What was regenerated

`PAPER.md`, `State-of-GEO-Volume-III.pdf`, `figures/fig3_within_vs_between.png`
and `.svg`. `data/results.json` was **not** regenerated and did not need to be:
no correction touched the analysis. `analysis/03_analyze.py` is byte-identical
to the version that produced the deposited results.
