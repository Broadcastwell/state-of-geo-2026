# Volume III — Cross-Engine Divergence

Supporting data for **The 2026 State of Generative Engine Optimization, v3.0**,
DOI `10.5281/zenodo.21789120`.

Between 05:28 and 16:29 UTC on 4 August 2026 we put 280 B2B software buyer
questions across 40 categories to four production AI search products (ChatGPT,
Claude, Perplexity, Google AI Overviews), extracted the set of vendors each
answer named, and measured agreement per question. A 25-question stratified
subsample was re-run three times so engine-to-engine difference could be read
against each engine's own run-to-run noise.

## Read this before using the data

Two of the four API accounts ran out of credit during collection and were not topped up. A third, Anthropic, ran out and was topped up, so Claude finished. This is a
billing event, not engine behaviour, and it is recorded row by row.

| Engine | Answers collected | Of 280 planned | Stopped |
|---|---|---|---|
| Google AI Overviews | 280 | 100% | ran to completion |
| Claude | 280 | 100% | ran out 09:15 UTC, topped up, finished |
| Perplexity | 175 | 63% | 08:04 UTC, quota |
| ChatGPT | 18 | 6% | ~06:20 UTC, no credits |

The four-engine intersection is therefore 18 questions. Every statistic in the
paper is reported with the engine set and sample size it was computed on.

## Headline findings

The decisive test is reported **per engine**. A pooled figure would be dominated by
whichever engine contributed the most repeat pairs, and would have hidden the result
below.

| Engine | Repeat pairs | Agrees with itself | Agrees with other engines | Gap (95% CI) |
|---|---|---|---|---|
| Google AI Overviews | 62 | 0.499 | 0.240 | +0.258 (0.178 to 0.338) |
| Claude | 74 | 0.442 | 0.277 | +0.165 (0.082 to 0.242) |

**Then the length control, which changed the answer.** Engines name very different
numbers of vendors per answer (Google AI Overviews 4.8, Claude 8.8, Perplexity 10.7),
and an engine compared with itself is length-matched by construction while two
different engines are not. The same comparison rerun two more ways:

| Engine | Raw Jaccard | Truncated to first 5 named | Overlap coefficient |
|---|---|---|---|
| Google AI Overviews | +0.258 holds | +0.167 holds | +0.193 holds |
| Claude | +0.165 holds | +0.075 not significant | +0.002 not significant |

On Google AI Overviews the separation survives every control. **On Claude it does not:
the length-normalised gap is +0.002.** What looks like cross-engine
divergence on Claude is not distinguishable from the two engines naming
different-length lists.

| Other metrics | Value |
|---|---|
| Mean pairwise Jaccard, all engine pairs | 0.313 (95% CI 0.295 to 0.331), 590 pair observations |
| Vendor mentions from exactly one engine (3-engine set, n=142) | 63.3% |
| Vendor mentions from all three engines | 17.5% |
| Google AI Overview trigger rate on these buyer questions | 92.1% |
| Companies visible on some engines and invisible on others | 14 of 32 tested on two or more engines |
| Volume 1 tie-back, Pearson r | 0.70 over 32 companies |

## Files

| File | Rows | What it is |
|---|---|---|
| `data/questions.csv` | 280 | the question set, with category, shape and shape-label provenance |
| `data/raw.csv` | 853 | one row per engine-answer: run id, timestamp, category, question, engine, model string, repeat index, status, full answer text, cited URLs, latency, SerpApi calls |
| `data/scored.csv` | 853 | one row per answer with the extracted vendor set as JSON and the citation mix |
| `data/vendor_mentions.csv` | 6,371 | long format: question, category, engine, repeat, vendor, in-universe flag |
| `data/citations.csv` | 10,797 | one row per cited URL with its hostname and source classification |
| `data/universe.csv` | 98 | the matching universe: companies, domains, competitors, aliases |
| `data/results.json` | — | every computed figure; the direct source of the paper text and all six figures |
| `data/sample_manifest.json` | — | how the sample was drawn, including shape-coverage shortfalls |

## Analysis

| Script | What it does |
|---|---|
| `analysis/01_build_sample.py` | draws the sample from the Volume 1 frame |
| `analysis/02_extract_vendors.py` | both extraction layers, reconciliation, citation classification |
| `analysis/03_analyze.py` | every statistic, bootstrap seed fixed at 20260804 |
| `analysis/04_figures.py` | all six figures, 300 dpi PNG plus SVG |
| `analysis/05_write_paper.py` | generates PAPER.md from results.json |
| `analysis/06_verify.py` | independent second implementation that re-derives every headline number and diffs it against the paper text |
| `analysis/07_build_pdf.py` | renders the PDF |
| `analysis/extractor_prompt.txt` | the exact Layer 2 extraction prompt |

Run in order. `06_verify.py` exits non-zero if any number in the paper cannot be
reproduced from the data.

## Status codes in raw.csv

- `ok` — the engine returned an answer
- `no_aio` — Google returned no AI Overview. This is engine behaviour and a finding, counted separately, never as an error
- `api_error` — the call failed. In this collection every such row is a billing failure on the account, not an engine failure, and these rows are excluded from every denominator

## Method notes that change how the numbers read

- **ChatGPT had to be forced to search.** With `tool_choice: auto` it returned zero citations on every pilot question at ~4s latency while the other three engines searched live. `tool_choice` was set to `required`. Our ChatGPT condition is the searched condition, not the default one.
- **Claude is on the Sonnet tier**, matching Volume 1, so the baseline tie-back stays like for like.
- **Google AI Overviews responses carry thumbnail image URLs** alongside real source links. 2,035 of them were dropped before any citation was counted; left in they would have been 62% of that engine's citations.
- **Layer 2 covers 100% of answers.** It shares the Anthropic key with the Claude engine, stopped when that account emptied, and completed after the top-up. Layer 1 also covers 100%. Layer 2 can only add out-of-universe names, so the gap can only narrow a vendor set. Every universe-only statistic is independent of it.

## Licence

CC BY 4.0. Cite as:

> Sivakumar, S. (2026). Divergence Survives a Length Control on Google AI Overviews and Vanishes on Claude. Measuring Vendor-Set Agreement Across Four AI Search Engines. The 2026 State of Generative Engine Optimization, v3.0. Zenodo. https://doi.org/10.5281/zenodo.21789120

Prior versions: v1.0 `10.5281/zenodo.21537014`, v2.0 `10.5281/zenodo.21586091`.
