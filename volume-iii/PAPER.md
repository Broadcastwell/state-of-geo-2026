# Divergence Survives a Length Control on Google AI Overviews and Vanishes on Claude. Measuring Vendor-Set Agreement Across Four AI Search Engines

## The 2026 State of Generative Engine Optimization, v3.0

**Sairam Sivakumar**  
Broadcastwell LLC, Indiana, United States  
sairam@broadcastwell.com

Version 3.0 &middot; 2026-08-04  
DOI (this version): `10.5281/zenodo.21789120`  
v1.0: `10.5281/zenodo.21537014` &middot; v2.0: `10.5281/zenodo.21586091`  
Data and code: https://github.com/Broadcastwell/state-of-geo-2026

> **Not peer reviewed.** This is an independent industry study published as an open dataset with the analysis code that produced every figure in it. It has not been through academic peer review. Read it as measurement, and check the measurement: the raw answers, the scoring scripts and the figure scripts are all in the repository above.

> **Operator disclosure.** Broadcastwell ran this measurement and sells services in the category it measures. Broadcastwell is excluded from every ranking in this paper and from the measured sample. In the four-engine, five-run self-audit published alongside Volume 2, Broadcastwell was named in 0 of 200 answers and cited 0 times among 663 citations.

## Abstract

Buyers now ask AI search products, not search engines, which software to buy. If those products return different shortlists for the same question, then "we rank well in AI search" is not a single claim, and a vendor measured on one engine knows very little about the other three. We put **280 B2B software buyer questions** across **40 categories** to four production AI search products (ChatGPT, Claude, Perplexity, Google AI Overviews) between 05:28 to 16:29 UTC on 2026-08-04, extracted the set of vendors each answer named, and measured agreement per question. A **25-question stratified subsample was re-run three times**, so engine-to-engine difference can be read against each engine's own run-to-run noise rather than in isolation.

**Three of the four API accounts ran out of credit during collection.** The study as executed therefore holds 280 Google AI Overviews answers, 280 Claude, 175 Perplexity and 18 ChatGPT, out of 280 planned for each. Section 3.8 states exactly what died and when. Every figure below carries the sample it was computed on, and the four-engine intersection is reported at its true size of 18 questions rather than dressed up.

The central result rests on repeats rather than on all four engines answering at once, so it survives the collection loss. It is reported **per engine**, because a pooled figure would be dominated by whichever engine contributed the most repeat pairs and could not license a claim about engines in general.

**Claude: within-engine 0.442 (95% CI 0.389 to 0.494) over 74 repeat pairs, against between-engine 0.277 (95% CI 0.222 to 0.333) over 37 pairs, a gap of 0.165 (95% CI 0.082 to 0.242)**.

**Google AI Overviews: within-engine 0.499 (95% CI 0.441 to 0.556) over 62 repeat pairs, against between-engine 0.240 (95% CI 0.186 to 0.295) over 35 pairs, a gap of 0.258 (95% CI 0.178 to 0.338)**.

**Scope of that result: it is engine-specific. On Google AI Overviews the separation survives every length control and is real. On Claude it appears on raw Jaccard but disappears once list length is controlled, so on Claude it cannot be distinguished from a list-length artefact.**

That distinction is the paper's main methodological contribution and it only appears if you look for it. Engines name very different numbers of vendors per answer, and Jaccard between two similar-length sets runs mechanically higher than between two sets of very different length. Within-engine pairs compare an engine with itself and are length-matched by construction; between-engine pairs are not. So we reran the comparison three more ways: restricted to the study universe, with each answer truncated to its first five named vendors, and with Jaccard swapped for an overlap coefficient normalised by the smaller set.

On Google AI Overviews the gap survives all three. On Claude it does not: the raw-Jaccard gap of 0.165 falls to 0.075 (95% CI -0.014 to 0.177) under truncation and to 0.002 (95% CI -0.112 to 0.113) under the overlap coefficient, both of which include zero. **On Claude, what looks like cross-engine divergence is not distinguishable from the fact that the engines being compared name lists of different lengths.** We report that rather than the headline we set out to find.

This structure independently replicates prior work on different systems. Jack et al. report cross-provider recommendation Jaccard of about 0.35 between two model APIs, sitting below a same-prompt rerun baseline of 0.50 to 0.61 that they cite from a separate industry report rather than measure. Our between-engine and within-engine figures land in the same two bands, on different engines, a different corpus and different categories, and with both sides measured by us on the same questions in the same collection window.

Two supporting numbers. Mean pairwise Jaccard similarity of the vendor sets is **0.313 (95% CI 0.295 to 0.330)** across 590 engine-pair observations, close to the 0.349 to 0.356 that Jack et al. report for two model APIs on a different corpus. And across the 142 questions answered by all of Claude, Perplexity, Google AI Overviews, **63.3% of the 2238 distinct vendor mentions came from a single engine** and only **17.5% from all 3**.

Separately, Google returned an AI Overview for **92.1%** of these buyer questions. On the remaining 22 there was no AI answer to be visible in at all.

All 853 collected answers, the extraction prompt, the scoring rules and the analysis scripts are released under CC BY 4.0.

## 1. Introduction

The generative-engine-optimization industry has settled quickly on a way of talking about itself. Vendors are told they are "visible in AI search" or not, as though AI search were one place. In practice a buyer asking which contract lifecycle management tool to shortlist might type that question into ChatGPT, or Claude, or Perplexity, or leave it in the Google box and read whatever AI Overview appears. Those are four different products, built by three different companies, retrieving from different indexes under different ranking logic.

This paper asks the plain version of the question: **do they return the same vendors?**

It matters for three reasons. For a vendor, it decides whether one measurement generalises. For a practitioner, it decides whether "optimising for AI search" is one job or four. For anyone reading a visibility report, it decides how much of a reported score is a property of the vendor and how much is a property of the engine that happened to be asked.

Our two previous volumes cannot answer it. v1.0 holds one engine constant across all 860 answers, which buys breadth and no engine resolution. The 200-answer own-category sweep published alongside v2.0 aggregates across all four engines and never logs which engine produced which answer, which buys engine coverage and no resolution either. The gap is real, and it is our own.

There is a second, sharper problem that most cross-engine comparisons skip. These systems are not deterministic. Ask the same engine the same question twice and the shortlist can move. Any measured difference between two engines therefore contains an unknown amount of the same variation you would get by asking one engine twice. Unless the noise floor is measured on the same questions, a divergence headline is not interpretable. We measure it.

## 2. Related work

**Academic.** Aggarwal et al. introduced generative engine optimization as a problem and showed that content-side interventions move visibility inside a generative engine (arXiv:2311.09735, KDD 2024). Bagga et al. build a controlled testbed for the same question in e-commerce (arXiv:2511.20867). Chu and Hou document an incumbent advantage in LLM product recommendation, in a single consumer category across three model APIs rather than in search products (arXiv:2606.17443). Jack, Lehman, Maloney and Xu audit roughly 37,000 production runs of retrieval-augmented commercial recommendation and stratify failure modes by brand prominence (arXiv:2605.27439); that work carries no data-availability statement.

**The repeat baseline is not our idea and we do not claim it.** Schulte, Bleeker and Kaufmann argue that a single visibility measurement is close to meaningless because the same query produces a distribution rather than a value, and that visibility should be measured repeatedly (arXiv:2604.07585). Their axis is repetition within an engine over time; ours is agreement across engines, read against repetition. Their argument is why this paper carries a repeat baseline at all.

**The closest quantitative neighbour** is Jack, Lehman, Maloney and Xu, arXiv:2606.26116, which computes per-prompt cross-provider Jaccard similarity of recommended brand sets over 215 commercially framed prompts and reports about 0.35. They read that against a same-prompt rerun baseline of 0.50 to 0.61, which is worth being precise about: **that baseline is cited from a separate Unusual.ai industry report, not measured in the paper itself.** Their comparison covers two providers, OpenAI and Anthropic, as model pools rather than production search products, includes no Google surface, and releases no dataset.

Our numbers land in the same two bands on different systems, which is the more interesting fact. Their 0.35 cross-provider figure sits beside our overall pairwise 0.31, and their 0.50 to 0.61 rerun band sits beside our within-engine figures. Different engines, different corpus, different categories, and in our case both sides measured on the same questions in the same window. Treat that as independent replication of the structure rather than as novelty on our part.

**Two open-data neighbours matter for the novelty claim and are named here rather than left for a reviewer to find.** A June 2026 DerivateX benchmark published a complete open dataset comparing per-query brand overlap between ChatGPT and Google AI Overviews over 15 buyer-intent queries in a B2B software category, reporting brand overlap far above source overlap. And Zatuchin (arXiv:2606.23057) published 250 brand-free category queries, five repetitions each, across three model APIs, with per-query cross-model brand agreement and the dataset released on Zenodo under CC BY 4.0. Both do genuinely overlapping work. The first covers two products; the second covers model APIs and no Google surface.

**Industry.** BrightEdge reports that engines agree on brands more than they agree on sources, with pairwise top-100 brand overlap of 36 to 55 percent against cited-source overlap of 16 to 59 percent across five engines; those are top-100 aggregate overlaps rather than per-question ones, and the panel is proprietary with no replication files. SE Ranking measured 25.19 percent cited-domain overlap for the Perplexity and ChatGPT pair specifically, the highest of the pairs it tested, over 2,000 keywords in 20 niches collected in late February and early March 2025; the dataset is closed and the metric is domain overlap, not brand overlap. Profound's citation study, covering roughly 680 million citations, documents strong per-engine source skews and is likewise closed. Semrush's study of more than 600,000 keywords reports that the share of commercial SERPs carrying an AI Overview grew 71 percent between November 2025 and April 2026. Seer Interactive reports AI answer trigger rates of 95.4 percent for comparison queries (n = 280) and 85.9 percent for question-format queries (n = 1,413), published April 2026 on data running to February 2026.

**What is new here, stated narrowly.** Not that engines disagree: BrightEdge, Jack et al., DerivateX and Zatuchin all establish that. Not the repeat baseline: Schulte et al. argued for it and Jack et al. cite one. To our knowledge what has not been done is the combination of three things at once: **Google AI Overviews included alongside conversational AI search engines** rather than compared only with another chat product or left out for lack of an API; **the within-engine repeat baseline and the between-engine divergence measured on the same questions, in the same collection window, by the same instrument**, rather than one imported from a separate study; and **the answer-level data released** so both halves can be recomputed. Each of those exists somewhere in the literature. We could not find them together.

A note on what we did not cite. An 11 percent ChatGPT-to-Perplexity domain-overlap figure circulates widely and is attributed to Profound. We could not find it stated by Profound in any form, and Profound's own comparable figure is a different comparison entirely. It is omitted rather than repeated.

## 3. Method

### 3.1 Sample

The sampling frame is inherited from v1.0: the same B2B software categories, so results are directly comparable to the single-engine baseline. Of the 60 categories in the v1.0/v2.0 open dataset we drew **40** by a rule fixed before any data was collected: every category carrying more than one measured company, then singleton categories in alphabetical order until 40 was reached. This maximises the number of companies available for the company-level tie-back in section 5.6.

Within each category we drew **7 questions**, for **280 questions** in total. 276 come from the study's existing buyer-question bank and 4 from the v1.0 published dataset. **No question was regenerated.** Question shapes reuse v1.0's labels where the question is a v1.0 question, and otherwise a deterministic re-implementation of the v1.0 labelling rules; the label source is recorded per row in `questions.csv`.

Each category was required to carry at least one best-of, one alternatives, one comparison, one use-case and one pricing or evaluation question. 33 of 40 categories meet that in full. 7 do not, because the question bank for those categories does not contain the missing shape; they are listed explicitly in `sample_manifest.json` rather than quietly padded. The realised shape mix is alternatives 80, best-of 80, comparison 47, evaluation 38, other 2, use-case 33.

Two dummy rows in the source sheet (`ExampleCo` / `Jane Doe`) are excluded everywhere. Nine rows flagged as category leaders rather than measured subjects (DocuSign, Gainsight, Google Analytics, Gusto, Klaviyo, LaunchDarkly, Pendo, Sentry, Vanta) remain in the matching universe as nameable vendors but are never measured subjects and never appear in any ranking. Broadcastwell is excluded from the measured sample entirely.

### 3.2 Engines

The four engines are ChatGPT, Claude, Perplexity and Google AI Overviews. Two clarifications matter for reading the results honestly. ChatGPT here means the **OpenAI Responses API with the hosted web-search tool**, not the consumer ChatGPT application; the two are different products and the API is what is reproducible. Google AI Overviews has no official API, so it is collected through SerpApi's Best Effort scraping, first the standard Google result and then the `google_ai_overview` follow-up when the first response returns only a page token.

Exact model strings, as reported by each provider's API on the answer itself:

| Engine | Request | Model reported on the answer | Answers |
|---|---|---|---|
| ChatGPT | `/v1/responses`, tool `web_search`, `tool_choice: required` | `gpt-5.5-2026-04-23` | 18 |
| Claude | `/v1/messages`, tool `web_search_20250305`, max 3 uses | `claude-sonnet-5` | 330 |
| Perplexity | `/chat/completions` | `sonar-pro` | 157 |
| Google AI Overviews | SerpApi `google` then `google_ai_overview`, `no_cache=true` | `google_ai_overview (SerpApi Best Effort)` | 303 |

**Each engine ran on exactly one model.** That is worth stating because an earlier draft of this table showed two model strings against Claude. The second string was an artefact: when a call fails there is no model in the response, so the collector wrote a fallback string into the error row. No such rows remain. No repeat pair in section 4.5 spans two model strings, and any that did would be excluded there by construction, because such a pair measures a model change rather than run-to-run noise.

**The Layer 2 extractor is a separate thing and runs on a different model.** It uses `claude-sonnet-4-6` at temperature 0. claude-sonnet-5 rejects the request with 'temperature is deprecated for this model', so the Layer 2 extractor cannot be pinned to temperature 0 on it. The extractor runs on claude-sonnet-4-6, which still accepts temperature. This is the extractor only and is unrelated to the Claude ENGINE, every answer of which was produced by claude-sonnet-5. Do not read the extractor model as an engine model.

Two configuration decisions are worth stating plainly because they shape the results.

**ChatGPT had to be forced to search.** On a pilot batch with `tool_choice: auto`, ChatGPT returned zero citations on every question at roughly four seconds of latency, while the other three engines returned live citations at fifteen to forty seconds. It was answering from parametric memory. Comparing that against three engines that searched the live web would have made every divergence number an artefact. `tool_choice` was set to `required` and the pilot rows were deleted. **That ChatGPT does not search a commercial buyer question unless compelled is itself a finding**, and it means our ChatGPT condition is the searched condition, not the default one.

**Claude is on the Sonnet tier, not the largest available model.** v1.0 ran on Claude Sonnet with web search. Keeping the tier keeps the v1.0 baseline tie-back like for like. A larger model would have made the Claude column better and the comparison to v1.0 worse.

Every answer is stored the moment it is scored, one database row per engine-answer, with the run id, timestamp, category, question, engine, model string, repeat index, status, full answer text, cited URLs, latency and SerpApi calls consumed. Collection is idempotent on `question_id | engine | repeat_index`, so a crash costs the in-flight call and nothing else.

### 3.3 The repeat baseline

A stratified subsample of **25 questions**, spread across the 40 categories and balanced across question shapes, was run **three times on all four engines**. Section 5.5 reads between-engine agreement against within-engine agreement on exactly these questions, on the same scale. Without it, a divergence number cannot be distinguished from ordinary nondeterminism.

### 3.4 Vendor extraction

Two layers.

**Layer 1 is deterministic and authoritative** for every company in the study universe. Answer text is normalised for non-breaking and thin spaces, curly quotes and the dash family, then whitespace-collapsed. Brand matching is word-boundary, and case-sensitive when the brand is a single plain alphabetic word, so a company called Pitch does not match the ordinary verb; a brand carrying a dot, digit, hyphen or space matches case-insensitively. Domain matching is at hostname level with multi-domain values split on pipes and commas, so subdomains count and near-misses do not. These are v1.0's rules, unchanged.

**Layer 2 is an LLM extractor**, Claude at temperature 0, one fixed prompt that lists every vendor or product named in an answer, normalised. The exact prompt is in the repository. Layer 2 exists to catch vendors outside the study universe, and **it may only add out-of-universe names**. Any Layer 2 claim about a universe company is discarded unless Layer 1 also finds the string in the answer, so the extractor cannot inflate a measured company's numbers in either direction.

### 3.5 Citation classification

Every cited URL is reduced to a hostname and classified as vendor-owned, review platform, editorial, analyst, community or other, reusing v1.0's classification so the 77.4 percent vendor-authored figure from that volume is comparable per engine here.

### 3.6 Completeness rules

The primary sample is the **18 questions where all four engines returned a usable answer**, out of 280 attempted. Pairwise metrics additionally use every question both engines in that pair answered, which is why pair sample sizes differ and are reported. Attrition is reported per engine rather than absorbed.

A Google query that returns no AI Overview is recorded with its own status, `no_aio`, not as an error. Google declining to generate an AI answer for a commercial buyer question is a result, and section 5.0 treats it as one.

### 3.7 Budget constraint, stated openly

Google AI Overviews is the only engine with a hard external cost, through SerpApi's 1,000-search monthly plan at a 200-search hourly rate limit. The sample was sized against that ceiling before any question was chosen: 280 questions plus 25 repeated twice, at a worst case of two SerpApi searches per question, gives 660 searches against a usable budget of 880 after a 120-search reserve. Actual consumption was **631 SerpApi searches**. The sample is therefore bounded by measurement cost, not by what would have been ideal, and a larger question set on AI Overviews would need a larger plan.

### 3.8 What happened to the collection

This section exists because the study as planned is not the study that ran, and the difference has to be legible to anyone reading a number below.

Collection ran 05:28 to 16:29 UTC on 2026-08-04. It began with all four engines live. Over the following few hours three of the four API accounts ran out of money, in this order:

| Engine | Stopped | Reason returned by the API | Answers collected |
|---|---|---|---|
| ChatGPT | ~06:20 UTC | `You have no credits remaining` | 18 of 280 |
| Perplexity | 08:04 UTC | `You exceeded your current quota` | 175 of 280 |
| Claude | 09:15 UTC | `Your credit balance is too low` | 280 of 280 |
| Google AI Overviews | ran to completion | prepaid SerpApi quota | 280 of 280 |

None of these is an engine behaviour. They are billing events on the accounts used to reach the engines, and they are reported separately from `no_aio`, which IS an engine behaviour. Rows carrying a billing error are excluded from every denominator in this paper and are retained in `raw.csv` with status `api_error` so the exclusion is checkable.

Three consequences, all of which shape how the results should be read.

**One.** The four-engine intersection, the questions where all four engines returned an answer, is 18 questions. That is too thin to carry a headline and is never used for one here. Where a statistic needs a common set of engines it is reported for each engine set with its own n: four engines (18 questions), three engines without ChatGPT (142), and two engines, Claude and Google AI Overviews (258).

**Two.** Pairwise metrics are unaffected in kind, only in precision, because a pair only needs both of its own engines to have answered. The Claude and Google AI Overviews pair rests on 247 questions; the pairs involving ChatGPT rest on 18. Both are reported, and the sample size sits in the table next to the number.

**Three, and this is why the paper still stands:** the decisive test in section 4.5 does not need four engines. It needs repeats, and the repeats survived. Google AI Overviews completed all three runs of all 25 stability questions, and Claude completed enough to contribute 74 repeat pairs before its account emptied. The within-engine baseline rests on 136 repeat pairs.

The Layer 2 extractor shares the Anthropic key with the Claude engine, so it stopped when that account did. It covers 100.0% of collected answers (808 of 808), short by . Layer 1 covers every answer. Because Layer 2 can only ADD out-of-universe names, the gap can only narrow a vendor set and never widen one, and every universe-only statistic in this paper is completely independent of it. The universe-only sensitivity analysis in section 4.8 is therefore also the Layer-2-free reading of the results.

## 4. Results

### 4.0 Not every engine answers

| Engine | Attempted | Answered | No AI Overview | API error | Answer rate |
|---|---|---|---|---|---|
| ChatGPT | 18 | 18 | 0 | 0 | 100.0% |
| Claude | 280 | 280 | 0 | 0 | 100.0% |
| Perplexity | 175 | 157 | 0 | 18 | 89.7% |
| Google AI Overviews | 280 | 258 | 22 | 0 | 92.1% |

Google returned an AI Overview for **92.1%** of these questions (258 of 280). By question shape:

| Question shape | Questions | AI Overview returned | Rate |
|---|---|---|---|
| alternatives | 80 | 72 | 90.0% |
| best-of | 80 | 71 | 88.8% |
| comparison | 47 | 47 | 100.0% |
| evaluation | 38 | 34 | 89.5% |
| other | 2 | 2 | 100.0% |
| use-case | 33 | 32 | 97.0% |

This sits below the trigger rates Seer Interactive reports for general query populations, which is what one would expect: these are narrow B2B software buying questions, not consumer queries. The practical consequence for a vendor is direct. On a question where Google returns no AI Overview, there is no AI answer to be named in, and any "AI visibility" score that silently drops those questions from its denominator will overstate coverage.

### 4.1 How much of a shortlist do two engines share?

| Engine pair | Questions | Mean Jaccard | Median | 95% CI |
|---|---|---|---|---|
| ChatGPT and Google AI Overviews | 18 | 0.223 | 0.195 | 0.150 to 0.299 |
| ChatGPT and Claude | 18 | 0.233 | 0.207 | 0.156 to 0.319 |
| ChatGPT and Perplexity | 18 | 0.252 | 0.240 | 0.185 to 0.328 |
| Claude and Google AI Overviews | 247 | 0.314 | 0.294 | 0.287 to 0.343 |
| Perplexity and Google AI Overviews | 136 | 0.325 | 0.294 | 0.283 to 0.366 |
| Claude and Perplexity | 153 | 0.327 | 0.318 | 0.298 to 0.357 |

Overall mean pairwise Jaccard similarity is **0.313 (95% CI 0.295 to 0.330)** over 590 engine-pair observations; the median is 0.294.

The most alike pair is **Claude and Perplexity** at 0.327. The least alike is **ChatGPT and Google AI Overviews** at 0.223. The spread between the most and least similar pair is 0.104, which means "how much do AI engines agree" does not have one answer even within this sample.

*Figure 1: 4x4 Jaccard matrix.*

### 4.2 Consensus

Reported for every engine set, because the four-engine intersection is too small to stand alone and hiding that behind one number would be the exact failure this research programme exists to point at.

| Engine set | Questions | Vendor mentions | Named by exactly 1 engine | Named by every engine in the set |
|---|---|---|---|---|
| ChatGPT, Claude, Perplexity, Google AI Overviews | 18 | 471 | 67.3% | 8.7% |
| Claude, Perplexity, Google AI Overviews | 142 | 2238 | 63.3% | 17.5% |
| Claude, Google AI Overviews | 258 | 2664 | 69.8% | 30.2% |

The best-powered reading is the 3-engine row: across 142 questions answered by all of Claude, Perplexity, Google AI Overviews, 2238 distinct vendor mentions were made, **63.3% of them by a single engine** and **17.5% by all 3**.

The pattern is the same at every set size, which is the useful thing about reporting all three: single-engine share stays between 63.3% and 69.8% no matter which engines are in the room.

*Figure 2: consensus distribution.*

### 4.3 What each engine returns

Vendor-list length is a within-engine statistic and needs no common question set, so it is computed over every answer each engine actually returned.

| Engine | Answers | Mean vendors named | Median | Distinct vendors seen | Mean answer length (chars) |
|---|---|---|---|---|---|
| ChatGPT | 18 | 14.72 | 14.5 | 131 | 7627 |
| Claude | 280 | 8.83 | 9.0 | 1057 | 3478 |
| Perplexity | 157 | 10.69 | 9.0 | 800 | 6217 |
| Google AI Overviews | 258 | 4.77 | 5.0 | 512 | 1344 |

The spread is large and it tracks answer length. Google AI Overviews names 4.8 vendors in an average 1344-character answer; the conversational engines name two to three times as many in answers two to five times as long. A vendor competing for a place in a Google AI Overview is competing for a materially scarcer slot than one competing inside a Claude or Perplexity answer, and that alone will make single-engine visibility scores disagree before any ranking difference is considered.

v1.0 found the average single-engine answer named 2.05 vendors. Every engine here names more than that, which is worth stating plainly rather than treating the two numbers as directly comparable: the extraction layer here is wider than v1.0's, which counted only companies inside the study universe.

Uniqueness needs a common question set, so it is reported per engine set:

| Engine set | Engine | Vendor slots | Unique to this engine | Unique rate |
|---|---|---|---|---|
| four engine | ChatGPT | 265 | 156 | 58.9% |
| four engine | Claude | 162 | 55 | 34.0% |
| four engine | Perplexity | 209 | 80 | 38.3% |
| four engine | Google AI Overviews | 114 | 26 | 22.8% |
| three engine | Claude | 1249 | 507 | 40.6% |
| three engine | Perplexity | 1506 | 747 | 49.6% |
| three engine | Google AI Overviews | 697 | 162 | 23.2% |
| two engine | Claude | 2237 | 1433 | 64.1% |
| two engine | Google AI Overviews | 1231 | 427 | 34.7% |

### 4.4 Agreement as a rater statistic

Treating the engines as raters making a binary mention decision over each question's own category universe:

| Engine set | Raters | Questions | Panels | Fleiss kappa, all vendors | Fleiss kappa, universe only |
|---|---|---|---|---|---|
| four engine | 4 | 18 | 504 | 0.037 | 0.534 |
| three engine | 3 | 142 | 2516 | 0.015 | 0.609 |
| two engine | 2 | 258 | 3303 | -0.129 | 0.548 |

The two columns say different things and both are worth having. Over ALL vendors, including everything the extractor found outside the study universe, agreement is close to zero or below it: the long tail of names one engine mentions and the others never do swamps the signal. Restricted to the study universe, where every engine plausibly could have named every company, agreement is moderate. The practical translation is that engines agree reasonably about the well-known vendors in a category and almost not at all about the tail, which is exactly where a challenger brand lives.

### 4.5 The decisive test, per engine

Everything above measures difference. This measures whether the difference is bigger than the noise, and it does so **one engine at a time**.

That choice is deliberate and it changed the paper. A pooled within-engine mean is dominated by whichever engine contributed the most repeat pairs; compared against a between-engine mean drawn from all engines, it can report a separation that only one engine actually has. That is an unstated denominator, which is the failure this research programme exists to point at, so we do not do it.

For each engine the comparison is like for like, on the same 25 stability questions: **within** is every pair of repeats of the same question on that engine, **between** is that same engine against the others on repeat 1 of those same questions. A repeat pair whose two runs used different model strings measures a model change rather than run-to-run noise and is excluded; no pair triggered that rule. An engine needs at least 12 repeat pairs before we assert a verdict for it.

| Engine | Repeat pairs | Within-engine | Between-engine | Gap (95% CI) | Verdict |
|---|---|---|---|---|---|
| ChatGPT | 0 | no repeats collected | | | no repeat data |
| Claude | 74 | 0.442 (n=74) | 0.277 (n=37) | 0.165 (0.082 to 0.242) | separates on the headline measure but a length artefact cannot be ruled out |
| Perplexity | 0 | no repeats collected | | | no repeat data |
| Google AI Overviews | 62 | 0.499 (n=62) | 0.240 (n=35) | 0.258 (0.178 to 0.338) | separates, and on every check including both length controls |

**Engine-specific. on google ai overviews the separation survives every length control and is real. on claude it appears on raw jaccard but disappears once list length is controlled, so on claude it cannot be distinguished from a list-length artefact.**

#### Robustness: is the gap just list length?

Google AI Overviews names 4.77 vendors in an average answer against 8.83 for Claude and 10.69 for Perplexity. Jaccard between two similar-length short sets runs mechanically higher than between two sets of very different length, so part of any within-versus-between gap could be list length rather than divergence. Within-engine pairs compare an engine with itself and are length-matched by construction; between-engine pairs are not. That asymmetry has to be controlled or the result is not safe.

Three controls, each recomputed from the same pairs:

| Engine | Measure | Within | Between | Gap (95% CI) | Separates |
|---|---|---|---|---|---|
| Claude | Jaccard, full vendor sets | 0.442 (n=74) | 0.277 (n=37) | 0.165 (0.082 to 0.242) | yes |
| Claude | Jaccard, restricted to the study universe | 0.648 (n=44) | 0.458 (n=24) | 0.189 (-0.030 to 0.403) | no |
| Claude | Jaccard, each answer truncated to its first 5 named vendors | 0.440 (n=74) | 0.365 (n=37) | 0.075 (-0.014 to 0.177) | no |
| Claude | Overlap coefficient, normalised by the smaller set | 0.675 (n=70) | 0.673 (n=33) | 0.002 (-0.112 to 0.113) | no |
| Google AI Overviews | Jaccard, full vendor sets | 0.499 (n=62) | 0.240 (n=35) | 0.258 (0.178 to 0.338) | yes |
| Google AI Overviews | Jaccard, restricted to the study universe | 0.625 (n=20) | 0.300 (n=20) | 0.325 (0.050 to 0.575) | yes |
| Google AI Overviews | Jaccard, each answer truncated to its first 5 named vendors | 0.507 (n=62) | 0.340 (n=35) | 0.167 (0.066 to 0.262) | yes |
| Google AI Overviews | Overlap coefficient, normalised by the smaller set | 0.834 (n=58) | 0.641 (n=32) | 0.193 (0.075 to 0.317) | yes |

For Google AI Overviews the gap stays positive at 95% under every control, including the overlap coefficient, which normalises by the smaller of the two sets and is the least forgiving of a length artefact. The separation is not length.

*Figure 3: within-engine versus between-engine agreement, per engine.*

#### The pooled figure, for completeness only

Pooled across all engines, within-engine agreement is 0.468 (95% CI 0.427 to 0.505) over 136 repeat pairs against between-engine 0.247 (95% CI 0.201 to 0.298) over 51 pairs. That pooled within-engine mean is 54.4% Claude repeat pairs, which is exactly why it is not the headline.

Within-engine agreement by engine, which is the number that pooled figure hides:

| Engine | Repeat pairs | Mean Jaccard |
|---|---|---|
| Claude | 74 | 0.442 |
| Google AI Overviews | 62 | 0.499 |

There is a second reading of that column worth stating on its own. Even the best case here is an engine agreeing with itself on roughly half its own shortlist across runs of the identical question. Every single-run visibility number in this industry, including the one in our own v1.0, carries that variance and cannot show it.

### 4.6 Company level

Being named is a fact about an individual answer, so this block does not need a question every engine answered. It counts over every answer each engine actually returned, which is both correct and far better powered than the four-engine intersection.

Of 32 measured companies with questions in their category, 32 were tested on at least two engines. Among those, **14 were visible on some engines and invisible on others**, 18 were named at least once by every engine that answered for them, and 0 were named by no engine at all.

That middle number is the commercially important one. 14 of 32 companies would receive a materially different verdict depending on which single engine their agency happened to measure. Per-company, per-engine named rates are in `results.json` under `company_level.rows`.

Against the v1.0 Claude-engine baseline, Pearson r = **0.70** over 32 companies. Volume I published company-level results anonymised, so the join is at CATEGORY level: each company's Volume III rate is compared with the mean Volume I Claude-engine named rate for its category. This is weaker than a per-company join and is stated as such in the paper.

*Figure 6: v1.0 baseline against v3.0 multi-engine visibility.*

### 4.7 What each engine cites

| Engine | Answers | Citations | Mean per answer | Vendor-owned | Review platform | Editorial | Analyst | Community | Other |
|---|---|---|---|---|---|---|---|---|---|
| ChatGPT | 18 | 125 | 6.9 | 85.6% | 4.0% | 0.0% | 1.6% | 0.0% | 8.8% |
| Claude | 280 | 3563 | 12.7 | 44.0% | 6.3% | 0.2% | 1.5% | 0.6% | 47.4% |
| Perplexity | 157 | 3016 | 19.2 | 39.2% | 6.4% | 0.7% | 1.2% | 9.0% | 43.7% |
| Google AI Overviews | 258 | 2849 | 11.0 | 38.3% | 2.6% | 0.3% | 0.9% | 7.0% | 50.9% |

v1.0 found 77.4 percent of citations resolved to vendor-owned domains and 10.2 percent to review platforms, measured on one engine. Splitting that by engine is the point of this table.

*Figure 5: citation source mix per engine.*

### 4.8 Sensitivity

Recomputed on universe-only vendor sets, which removes every out-of-universe name the extractor found: mean pairwise Jaccard **0.506 (95% CI 0.456 to 0.551)** against 0.313 (95% CI 0.295 to 0.330) on the full sets; single-engine share of vendor mentions 41.7% against 67.3%; Fleiss' kappa 0.534 against 0.037.

## 5. Discussion

The practical reading is short. A single-engine visibility score is a measurement of one product, and it generalises to the other three only as far as the numbers above allow. Anyone selling a number that is described as "your AI search visibility" without naming the engine, the date and the question set is selling a number whose denominator is unstated.

The second reading is about method rather than marketing. Because these systems are nondeterministic, cross-engine comparisons need a noise floor measured on the same questions in the same window, or the headline is uninterpretable. That is the contribution of section 4.5, and it is why the repeat subsample was mandatory rather than optional in this design.

The AI Overview trigger rate deserves its own line. For a large share of these buyer questions Google produced no AI answer at all. Visibility work aimed at Google AI Overviews is therefore also a bet on the overview appearing, which is a different and less controllable thing than ranking within one.

## 6. Limitations

1. **A single time snapshot.** Everything here was collected between 05:28 to 16:29 UTC on 2026-08-04, a window of about four hours. These are products under continuous change; the numbers are a measurement of that window and should not be read as stable constants.
2. **Google AI Overviews is scraped, not API-served.** There is no official API. SerpApi Best Effort is the only practical path, and it introduces a dependency whose failure modes are not fully observable from our side. A `no_aio` result means SerpApi returned no overview, which we treat as Google not producing one.
3. **Engines are products, not models.** ChatGPT here is the OpenAI Responses API with a forced web-search tool, not the consumer application; the retrieval layer, the system prompt and the ranking logic of the consumer products are not observable. Results describe what these endpoints return, not what a person sees in the app.
4. **The sampling frame is inherited.** Categories and companies come from v1.0, which was itself a convenience sample of B2B software categories. Nothing here generalises to consumer categories, to non-English queries or to markets outside the United States English locale used for collection.
5. **Operator conflict of interest.** Broadcastwell ran the measurement and sells in the category. Broadcastwell is excluded from the measured sample and from every ranking. The mitigation is not that the conflict is absent, it is that the raw data and the code are public and the result can be recomputed by anyone who disagrees.
6. **Measured within-engine nondeterminism.** The same engine does not return the same shortlist twice. Section 4.5 quantifies it rather than assuming it away, but it also means every single-run number in this paper, including v1.0's, carries a variance that a single run cannot show.
7. **Question-bank provenance.** The questions were originally generated to a fixed specification rather than sampled from real search logs, so they are plausible buyer questions rather than observed ones.
8. **The vendor universe is finite.** Layer 1 can only find companies it knows about. Layer 2 widens this, but a vendor named by an engine and absent from both the universe and the extractor's output would be invisible to this measurement.

## 7. Reproducibility

Everything needed to recompute every number is in https://github.com/Broadcastwell/state-of-geo-2026 under `volume-iii/`:

| File | What it is |
|---|---|
| `data/questions.csv` | the exact question set, with category, shape and shape-label provenance |
| `data/raw.csv` | one row per engine-answer: run id, timestamp, category, question, engine, model string, repeat index, status, full answer text, cited URLs, latency, SerpApi calls |
| `data/scored.csv` | one row per answer with the extracted vendor set as JSON and the citation mix |
| `data/vendor_mentions.csv` | long format: question, engine, vendor, in-universe flag |
| `data/universe.csv` | the matching universe: companies, domains, competitors, aliases |
| `data/results.json` | every computed figure, the direct source of the paper text and all six figures |
| `analysis/01_build_sample.py` | sample construction |
| `analysis/02_extract_vendors.py` | both extraction layers, reconciliation, citation classification |
| `analysis/03_analyze.py` | every statistic, with the bootstrap seed fixed |
| `analysis/04_figures.py` | all six figures |
| `analysis/05_write_paper.py` | this document |
| `analysis/extractor_prompt.txt` | the exact Layer 2 prompt |

The bootstrap uses 2000 replicates with a fixed seed, so the confidence intervals reproduce exactly. Figures are generated from `results.json`, never typed, so a caption cannot drift from the dataset.

## 8. References

Every reference below was checked against the arXiv listing or the publisher page before publication. Author lists are as printed by the source.

Aggarwal, P., Murahari, V., Rajpurohit, T., Kalyan, A., Narasimhan, K., Deshpande, A. (2024). GEO: Generative Engine Optimization. KDD 2024. arXiv:2311.09735.

Bagga, P. S., Farias, V. F., Korkotashvili, T., Peng, T., Wu, Y. (2025). E-GEO: A Testbed for Generative Engine Optimization in E-Commerce. arXiv:2511.20867.

BrightEdge (2026). Why AI Engines Cite Different Sources but Recommend the Same Brands. Weekly AI and Search Insights, 24 April 2026.

Broadcastwell (2026). The 2026 State of Generative Engine Optimization, v1.0. Zenodo. https://doi.org/10.5281/zenodo.21537014

Broadcastwell (2026). The 2026 State of Generative Engine Optimization, v2.0. Zenodo. https://doi.org/10.5281/zenodo.21586091

Chu, X., Hou, Y. (2026). Incumbent Advantage: Brand Bias and Cognitive Manipulation Dynamics in LLM Recommendation Systems. arXiv:2606.17443.

DerivateX (2026). ChatGPT and Google AI Overviews agree on tools, not sources. Open benchmark dataset, June 2026.

Harsel, L., Yudina, A., Skopec, C. (2026). AI Overviews are expanding across commercial intent search. Semrush, 2 July 2026.

Jack, W., Lehman, N., Maloney, K., Xu, S. (2026). Prominence-Stratified Failure Modes in Retrieval-Augmented Commercial Recommendation: A 37,000-Run Audit. arXiv:2605.27439.

Jack, W., Lehman, N., Maloney, K., Xu, S. (2026). Divergent Recommendations, Convergent Diagnoses: Cross-Provider Failure-Mode Convergence in AI Commercial Recommendation. arXiv:2606.26116. Note: the 0.50 to 0.61 same-prompt rerun baseline quoted in that paper is cited by it from a separate Unusual.ai research report, not measured within it.

Khromova, Y. (2025, updated 2026). ChatGPT vs Perplexity vs Google vs Bing: AI Search Engine Comparison. SE Ranking. Data collected 26 February to 3 March 2025.

Lafferty, N. (2025). AI Platform Citation Patterns. Profound.

McDonald, T., Cooley, H., Williams, M. (2026). AIO Impact on Google CTR: 2026 Update. Seer Interactive, 24 April 2026. Data through February 2026.

Schulte, J., Bleeker, M., Kaufmann, P. (2026). Don't Measure Once: Measuring Visibility in AI Search (GEO). arXiv:2604.07585.

Zatuchin, D. (2026). Who Owns the AI Recommendation? arXiv:2606.23057. Dataset released on Zenodo under CC BY 4.0.

---

*Cite this version: Sivakumar, S. (2026). Divergence Survives a Length Control on Google AI Overviews and Vanishes on Claude. Measuring Vendor-Set Agreement Across Four AI Search Engines. The 2026 State of Generative Engine Optimization, v3.0. Zenodo. https://doi.org/10.5281/zenodo.21789120*
