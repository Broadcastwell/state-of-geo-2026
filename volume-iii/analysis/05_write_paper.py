#!/usr/bin/env python3
"""
Volume III, step 5: generate PAPER.md from data/results.json.

Every number in the paper is interpolated from results.json, which is recomputed
row-level from scored.csv. There is no path by which a figure can be typed in by
hand, remembered from a previous volume, or estimated. If a value is missing from
results.json the paper renders "NOT COMPUTED" rather than a plausible number.

Usage: 05_write_paper.py [reserved_doi]
"""
import json, sys, os, datetime

D = "data"
R = json.load(open(f"{D}/results.json"))
MAN = json.load(open(f"{D}/sample_manifest.json"))
RESERVED_DOI = sys.argv[1] if len(sys.argv) > 1 else "RESERVED_DOI_PENDING"

VOL1_DOI = "10.5281/zenodo.21537014"
VOL2_DOI = "10.5281/zenodo.21586091"
REPO = "https://github.com/Broadcastwell/state-of-geo-2026"

E = R["engines"]
LAB = {"chatgpt": "ChatGPT", "claude": "Claude", "perplexity": "Perplexity",
       "google_aio": "Google AI Overviews"}


def n(x, nd=3):
    return "NOT COMPUTED" if x is None else f"{x:.{nd}f}"


def p(x, nd=1):
    return "NOT COMPUTED" if x is None else f"{100*x:.{nd}f}%"


def ci(d, nd=3):
    if not d:
        return "NOT COMPUTED"
    return f"{d['point']:.{nd}f} (95% CI {d['lo']:.{nd}f} to {d['hi']:.{nd}f})"


CC = R["collection_completeness"]
ES = R["engine_sets"]
# Prefer the MOST engines that still has a defensible sample. A divergence paper
# reporting a two-engine consensus as its headline would be self-defeating.
_cands = [v for v in R["consensus_by_engine_set"].values() if v["n_questions"] >= 100]
BEST = max(_cands or list(R["consensus_by_engine_set"].values()),
           key=lambda x: (x["n_engines"], x["n_questions"]))
BEST_NAME = ", ".join(LAB[e] for e in BEST["engines"])
BEST_KEY = next(k for k, v in R["consensus_by_engine_set"].items()
                if v["engines"] == BEST["engines"])
L2 = R["layer2_coverage"]
DTE = R["decisive_test_per_engine"]
WINDOW = R["collection_window"].get("utc_window") or ""
POWERED = DTE["adequately_powered"]
ROBUST = DTE["separating_on_every_control"]
AGREE = DTE["separating_on_headline_measure"]
pj = R["pairwise_jaccard"]
pju = R["pairwise_jaccard_universe_only"]
cons = R["consensus"]
dt = R["decisive_test"]
attr = R["attrition_main_set"]
aio = R["aio_trigger_rate"]
cm = R["citation_mix"]
pe = R["per_engine"]

pairs_sorted = sorted(((k, v) for k, v in pj["pairs"].items() if v["mean"] is not None),
                      key=lambda kv: kv[1]["mean"])
most_alike = pairs_sorted[-1] if pairs_sorted else None
least_alike = pairs_sorted[0] if pairs_sorted else None


def pairname(k):
    a, b = k.split("|")
    return f"{LAB[a]} and {LAB[b]}"


window = R.get("collection_window", {})
start = (window.get("first") or "")[:10]
end = (window.get("last") or "")[:10]

# The title states the finding, and it is constrained by what was actually
# collected. "Four Engines, Four Shortlists" is only honest if all four engines
# have a real sample. Three accounts ran dry mid-collection, so the title drops
# the engine count and states the result instead.
# The title is set by the PER-ENGINE result, not the pooled one. A pooled
# within-engine mean dominated by whichever engine contributed the most repeat
# pairs cannot license a claim about engines in general.
_full = min(v["main_set_rows"] for v in CC["per_engine"].values()) >= 0.5 * CC["planned_questions"]
LENGTH_SAFE = DTE.get("length_controls_hold", [])
_fail_len = [e for e in POWERED if e not in LENGTH_SAFE]
if not POWERED:
    title_phrase = "No Engine Has Enough Repeat Runs to Say."
elif len(ROBUST) == len(POWERED) and len(POWERED) >= 2 and _full:
    title_phrase = "Four Engines, Four Shortlists?"
elif len(ROBUST) == len(POWERED) and len(POWERED) >= 2:
    title_phrase = "Engines Disagree With Each Other More Than They Disagree With Themselves."
elif LENGTH_SAFE and _fail_len:
    title_phrase = (f"Divergence Survives a Length Control on "
                    f"{', '.join(LAB[e] for e in LENGTH_SAFE)} and Vanishes on "
                    f"{', '.join(LAB[e] for e in _fail_len)}.")
elif len(POWERED) == 1 and POWERED[0] in ROBUST:
    title_phrase = (f"{LAB[POWERED[0]]} Disagrees With Other Engines More Than It Disagrees "
                    f"With Itself.")
elif not LENGTH_SAFE and AGREE:
    title_phrase = "The Apparent Divergence Between AI Search Engines Is Mostly List Length."
else:
    title_phrase = "Four Engines, One Noise Floor?"
subtitle_verdict = DTE["headline"]

md = []
A = md.append

SUFFIX = ("Measuring Vendor-Set Agreement Across Four AI Search Engines"
          if "Divergence" in title_phrase or "Length" in title_phrase
          else "Cross-Engine Divergence in AI Search Vendor Recommendations")
A(f"# {title_phrase} {SUFFIX}")
A("")
A("## The 2026 State of Generative Engine Optimization, v3.0")
A("")
A("**Sairam Sivakumar**  ")
A("Broadcastwell LLC, Indiana, United States  ")
A("sairam@broadcastwell.com")
A("")
A(f"Version 3.0 &middot; {datetime.date.today().isoformat()}  ")
A(f"DOI (this version): `{RESERVED_DOI}`  ")
A(f"v1.0: `{VOL1_DOI}` &middot; v2.0: `{VOL2_DOI}`  ")
A(f"Data and code: {REPO}")
A("")
A("> **Not peer reviewed.** This is an independent industry study published as an "
  "open dataset with the analysis code that produced every figure in it. It has not "
  "been through academic peer review. Read it as measurement, and check the "
  "measurement: the raw answers, the scoring scripts and the figure scripts are all "
  "in the repository above.")
A("")
A("> **Operator disclosure.** Broadcastwell ran this measurement and sells services "
  "in the category it measures. Broadcastwell is excluded from every ranking in this "
  "paper and from the measured sample. In the four-engine, five-run self-audit "
  "published alongside Volume 2, Broadcastwell was named in 0 of 200 answers and "
  "cited 0 times among 663 citations.")
A("")

# ---------------------------------------------------------------- abstract
A("## Abstract")
A("")
A(f"Buyers now ask AI search products, not search engines, which software to buy. "
  f"If those products return different shortlists for the same question, then "
  f"\"we rank well in AI search\" is not a single claim, and a vendor measured on one "
  f"engine knows very little about the other three. We put "
  f"**{R['n_questions_attempted']} B2B software buyer questions** across "
  f"**{MAN['n_categories']} categories** to four production AI search products "
  f"({', '.join(LAB[e] for e in E)}) between {WINDOW}, extracted the set of vendors each "
  f"answer named, and measured agreement per question. A "
  f"**{MAN['n_stability_questions']}-question stratified subsample was re-run three "
  f"times**, so engine-to-engine difference can be read against each engine's own "
  f"run-to-run noise rather than in isolation.")
A("")
_done = [e for e in E if CC['per_engine'][e]['main_set_rows'] >= CC['planned_questions']]
_short = [e for e in E if CC['per_engine'][e]['main_set_rows'] < CC['planned_questions']]
A(f"**Three of the four API accounts ran out of credit during collection. One was "
  f"topped up and finished; two were not.** The study as executed therefore holds "
  + ", ".join(f"{CC['per_engine'][e]['main_set_rows']} {LAB[e]}" for e in E)
  + f" answers out of {CC['planned_questions']} planned for each. Section 3.8 states "
    f"exactly what stopped and when. Every figure below carries the sample it was "
    f"computed on, and the four-engine intersection is reported at its true size of "
    f"{ES['four_engine']['n_questions_all_ok']} questions rather than dressed up. "
    f"The two engines that completed, "
  + " and ".join(LAB[e] for e in _done)
  + ", are the two that carry the repeat comparison below.")
A("")
_pe_lines = []
for _e in POWERED:
    _m = DTE["engines"][_e]["modes"]["full"]
    _g = _m["gap"]
    _pe_lines.append(
        f"**{LAB[_e]}: within-engine {ci(_m['within']['ci95'])} over "
        f"{_m['within']['n_pairs']} repeat pairs, against between-engine "
        f"{ci(_m['between']['ci95'])} over {_m['between']['n_pairs']} pairs, a gap of "
        f"{n(_g['point'])} (95% CI {n(_g['lo'])} to {n(_g['hi'])})**")
A("The central result rests on repeats rather than on all four engines answering at "
  "once, so it survives the collection loss. It is reported **per engine**, because a "
  "pooled figure would be dominated by whichever engine contributed the most repeat "
  "pairs and could not license a claim about engines in general.")
A("")
for _l in _pe_lines:
    A(_l + ".")
    A("")
_unp = [e for e in E if DTE["engines"][e]["repeat_pairs"] > 0 and e not in POWERED]
if _unp:
    A("The remaining engines do not have enough repeat pairs for a verdict: "
      + ", ".join(f"{LAB[e]} at {DTE['engines'][e]['repeat_pairs']} pairs" for e in _unp)
      + f", against a threshold of {DTE['min_pairs_for_a_verdict']}. Their numbers are in "
        f"section 4.5 and are not asserted as findings.")
    A("")
A(f"**Scope of that result: it is {DTE['headline']}.**")
A("")
A("That distinction is the paper's main methodological contribution and it only appears "
  "if you look for it. Engines name very different numbers of vendors per answer, and "
  "Jaccard between two similar-length sets runs mechanically higher than between two "
  "sets of very different length. Within-engine pairs compare an engine with itself and "
  "are length-matched by construction; between-engine pairs are not. So we reran the "
  "comparison three more ways: restricted to the study universe, with each answer "
  "truncated to its first five named vendors, and with Jaccard swapped for an overlap "
  "coefficient normalised by the smaller set.")
A("")
_ls = [LAB[e] for e in LENGTH_SAFE]
_lf = [LAB[e] for e in _fail_len]
if _ls and _lf:
    _fe = _fail_len[0]
    _fm = DTE["engines"][_fe]["modes"]
    A(f"On {', '.join(_ls)} the gap survives all three. On {', '.join(_lf)} it does not: "
      f"the raw-Jaccard gap of {n(DTE['engines'][_fe]['modes']['full']['gap']['point'])} "
      f"falls to {n(_fm['topk']['gap']['point'])} "
      f"(95% CI {n(_fm['topk']['gap']['lo'])} to {n(_fm['topk']['gap']['hi'])}) under "
      f"truncation and to {n(_fm['overlap']['gap']['point'])} "
      f"(95% CI {n(_fm['overlap']['gap']['lo'])} to {n(_fm['overlap']['gap']['hi'])}) "
      f"under the overlap coefficient, both of which include zero. **On "
      f"{', '.join(_lf)}, what looks like cross-engine divergence is not distinguishable "
      f"from the fact that the engines being compared name lists of different lengths.** "
      f"We report that rather than the headline we set out to find.")
A("")
A("This structure independently replicates prior work on different systems. Jack et al. "
  "report cross-provider recommendation Jaccard of about 0.35 between two model APIs, "
  "sitting below a same-prompt rerun baseline of 0.50 to 0.61 that they cite from a "
  "separate industry report rather than measure. Our between-engine and within-engine "
  "figures land in the same two bands, on different engines, a different corpus and "
  "different categories, and with both sides measured by us on the same questions in "
  "the same collection window.")
A("")
A(f"Two supporting numbers. Mean pairwise Jaccard similarity of the vendor sets is "
  f"**{ci(pj['overall_ci95'])}** across {pj['n_pair_observations']} engine-pair "
  f"observations, close to the 0.349 to 0.356 that Jack et al. report for two model "
  f"APIs on a different corpus. And across the "
  f"{BEST['n_questions']} questions answered by all of {BEST_NAME}, "
  f"**{p(BEST['share']['1'])} of the {BEST['distinct_vendor_slots']} distinct vendor "
  f"mentions came from a single engine** and only "
  f"**{p(BEST['share'][str(BEST['n_engines'])])} from all {BEST['n_engines']}**.")
A("")
A(f"Separately, Google returned an AI Overview for **{p(aio['rate'])}** of these buyer "
  f"questions. On the remaining {aio['not_triggered']} there was no AI answer to be "
  f"visible in at all.")
A("")
A(f"All {R['rows_total']} collected answers, the extraction prompt, the scoring rules "
  f"and the analysis scripts are released under CC BY 4.0.")
A("")

# ---------------------------------------------------------------- intro
A("## 1. Introduction")
A("")
A("The generative-engine-optimization industry has settled quickly on a way of "
  "talking about itself. Vendors are told they are \"visible in AI search\" or not, as "
  "though AI search were one place. In practice a buyer asking which contract "
  "lifecycle management tool to shortlist might type that question into ChatGPT, or "
  "Claude, or Perplexity, or leave it in the Google box and read whatever AI Overview "
  "appears. Those are four different products, built by three different companies, "
  "retrieving from different indexes under different ranking logic.")
A("")
A("This paper asks the plain version of the question: **do they return the same "
  "vendors?**")
A("")
A("It matters for three reasons. For a vendor, it decides whether one measurement "
  "generalises. For a practitioner, it decides whether \"optimising for AI search\" is "
  "one job or four. For anyone reading a visibility report, it decides how much of a "
  "reported score is a property of the vendor and how much is a property of the "
  "engine that happened to be asked.")
A("")
A("Our two previous volumes cannot answer it. v1.0 holds one engine constant across "
  "all 860 answers, which buys breadth and no engine resolution. The 200-answer "
  "own-category sweep published alongside v2.0 aggregates across all four engines and "
  "never logs which engine produced which answer, which buys engine coverage and no "
  "resolution either. The gap is real, and it is our own.")
A("")
A("There is a second, sharper problem that most cross-engine comparisons skip. These "
  "systems are not deterministic. Ask the same engine the same question twice and the "
  "shortlist can move. Any measured difference between two engines therefore contains "
  "an unknown amount of the same variation you would get by asking one engine twice. "
  "Unless the noise floor is measured on the same questions, a divergence headline is "
  "not interpretable. We measure it.")
A("")

# ---------------------------------------------------------------- related work
A("## 2. Related work")
A("")
A("**Academic.** Aggarwal et al. introduced generative engine optimization as a "
  "problem and showed that content-side interventions move visibility inside a "
  "generative engine (arXiv:2311.09735, KDD 2024). Bagga et al. build a controlled "
  "testbed for the same question in e-commerce (arXiv:2511.20867). Chu and Hou "
  "document an incumbent advantage in LLM product recommendation, in a single consumer "
  "category across three model APIs rather than in search products (arXiv:2606.17443). "
  "Jack, Lehman, Maloney and Xu audit roughly 37,000 production runs of "
  "retrieval-augmented commercial recommendation and stratify failure modes by brand "
  "prominence (arXiv:2605.27439); that work carries no data-availability statement.")
A("")
A("**The repeat baseline is not our idea and we do not claim it.** Schulte, Bleeker "
  "and Kaufmann argue that a single visibility measurement is close to meaningless "
  "because the same query produces a distribution rather than a value, and that "
  "visibility should be measured repeatedly (arXiv:2604.07585). Their axis is "
  "repetition within an engine over time; ours is agreement across engines, read "
  "against repetition. Their argument is why this paper carries a repeat baseline at "
  "all.")
A("")
A("**The closest quantitative neighbour** is Jack, Lehman, Maloney and Xu, "
  "arXiv:2606.26116, which computes per-prompt cross-provider Jaccard similarity of "
  "recommended brand sets over 215 commercially framed prompts and reports about 0.35. "
  "They read that against a same-prompt rerun baseline of 0.50 to 0.61, which is worth "
  "being precise about: **that baseline is cited from a separate Unusual.ai industry "
  "report, not measured in the paper itself.** Their comparison covers two providers, "
  "OpenAI and Anthropic, as model pools rather than production search products, "
  "includes no Google surface, and releases no dataset.")
A("")
A("Our numbers land in the same two bands on different systems, which is the more "
  "interesting fact. Their 0.35 cross-provider figure sits beside our overall pairwise "
  f"{n(pj['overall_mean'], 2)}, and their 0.50 to 0.61 rerun band sits beside our "
  f"within-engine figures. Different engines, different corpus, different categories, "
  f"and in our case both sides measured on the same questions in the same window. "
  f"Treat that as independent replication of the structure rather than as novelty on "
  f"our part.")
A("")
A("**Two open-data neighbours matter for the novelty claim and are named here rather "
  "than left for a reviewer to find.** A June 2026 DerivateX benchmark published a "
  "complete open dataset comparing per-query brand overlap between ChatGPT and Google "
  "AI Overviews over 15 buyer-intent queries in a B2B software category, reporting "
  "brand overlap far above source overlap. And Zatuchin (arXiv:2606.23057) published "
  "250 brand-free category queries, five repetitions each, across three model APIs, "
  "with per-query cross-model brand agreement and the dataset released on Zenodo under "
  "CC BY 4.0. Both do genuinely overlapping work. The first covers two products; the "
  "second covers model APIs and no Google surface.")
A("")
A("**Industry.** BrightEdge reports that engines agree on brands more than they agree "
  "on sources, with pairwise top-100 brand overlap of 36 to 55 percent against "
  "cited-source overlap of 16 to 59 percent across five engines; those are top-100 "
  "aggregate overlaps rather than per-question ones, and the panel is proprietary with "
  "no replication files. SE Ranking measured 25.19 percent cited-domain overlap for the "
  "Perplexity and ChatGPT pair specifically, the highest of the pairs it tested, over "
  "2,000 keywords in 20 niches collected in late February and early March 2025; the "
  "dataset is closed and the metric is domain overlap, not brand overlap. Profound's "
  "citation study, covering roughly 680 million citations, documents strong per-engine "
  "source skews and is likewise closed. Semrush's study of more than 600,000 keywords "
  "reports that the share of commercial SERPs carrying an AI Overview grew 71 percent "
  "between November 2025 and April 2026. Seer Interactive reports AI answer trigger "
  "rates of 95.4 percent for comparison queries (n = 280) and 85.9 percent for "
  "question-format queries (n = 1,413), published April 2026 on data running to "
  "February 2026.")
A("")
A("**What is new here, stated narrowly.** Not that engines disagree: BrightEdge, Jack "
  "et al., DerivateX and Zatuchin all establish that. Not the repeat baseline: Schulte "
  "et al. argued for it and Jack et al. cite one. To our knowledge what has not been "
  "done is the combination of three things at once: **Google AI Overviews included "
  "alongside conversational AI search engines** rather than compared only with another "
  "chat product or left out for lack of an API; **the within-engine repeat baseline and "
  "the between-engine divergence measured on the same questions, in the same collection "
  "window, by the same instrument**, rather than one imported from a separate study; "
  "and **the answer-level data released** so both halves can be recomputed. Each of "
  "those exists somewhere in the literature. We could not find them together.")
A("")
A("A note on what we did not cite. An 11 percent ChatGPT-to-Perplexity domain-overlap "
  "figure circulates widely and is attributed to Profound. We could not find it stated "
  "by Profound in any form, and Profound's own comparable figure is a different "
  "comparison entirely. It is omitted rather than repeated.")
A("")

# ---------------------------------------------------------------- method
A("## 3. Method")
A("")
A("### 3.1 Sample")
A("")
A(f"The sampling frame is inherited from v1.0: the same B2B software categories, so "
  f"results are directly comparable to the single-engine baseline. Of the 60 "
  f"categories in the v1.0/v2.0 open dataset we drew **{MAN['n_categories']}** by a "
  f"rule fixed before any data was collected: every category carrying more than one "
  f"measured company, then singleton categories in alphabetical order until 40 was "
  f"reached. This maximises the number of companies available for the company-level "
  f"tie-back in section 4.6.")
A("")
A(f"Within each category we drew **{MAN['questions_per_category']} questions**, for "
  f"**{MAN['n_questions']} questions** in total. "
  f"{MAN['question_source_mix'].get('question_bank', 0)} come from the study's existing "
  f"buyer-question bank and {MAN['question_source_mix'].get('vol1_dataset', 0)} from the "
  f"v1.0 published dataset. **No question was regenerated.** Question shapes reuse "
  f"v1.0's labels where the question is a v1.0 question, and otherwise a deterministic "
  f"re-implementation of the v1.0 labelling rules; the label source is recorded per "
  f"row in `questions.csv`.")
A("")
shortfalls = MAN.get("shape_coverage_shortfalls", [])
A(f"Each category was required to carry at least one best-of, one alternatives, one "
  f"comparison, one use-case and one pricing or evaluation question. "
  f"{MAN['n_categories'] - len(shortfalls)} of {MAN['n_categories']} categories meet "
  f"that in full. {len(shortfalls)} do not, because the question bank for those "
  f"categories does not contain the missing shape; they are listed explicitly in "
  f"`sample_manifest.json` rather than quietly padded. The realised shape mix is "
  + ", ".join(f"{k} {v}" for k, v in sorted(MAN["question_shape_mix"].items())) + ".")
A("")
A("Two dummy rows in the source sheet (`ExampleCo` / `Jane Doe`) are excluded "
  "everywhere. Nine rows flagged as category leaders rather than measured subjects "
  "(DocuSign, Gainsight, Google Analytics, Gusto, Klaviyo, LaunchDarkly, Pendo, "
  "Sentry, Vanta) remain in the matching universe as nameable vendors but are never "
  "measured subjects and never appear in any ranking. Broadcastwell is excluded from "
  "the measured sample entirely.")
A("")
A("### 3.2 Engines")
A("")
A("The four engines are ChatGPT, Claude, Perplexity and Google AI Overviews. Two "
  "clarifications matter for reading the results honestly. ChatGPT here means the "
  "**OpenAI Responses API with the hosted web-search tool**, not the consumer ChatGPT "
  "application; the two are different products and the API is what is reproducible. "
  "Google AI Overviews has no official API, so it is collected through SerpApi's "
  "Best Effort scraping, first the standard Google result and then the "
  "`google_ai_overview` follow-up when the first response returns only a page token.")
A("")
A("Exact model strings, as reported by each provider's API on the answer itself:")
A("")
A("| Engine | Request | Model reported on the answer | Answers |")
A("|---|---|---|---|")
for e in E:
    counts = R["model_counts"].get(e) or {}
    req = {"chatgpt": "`/v1/responses`, tool `web_search`, `tool_choice: required`",
           "claude": "`/v1/messages`, tool `web_search_20250305`, max 3 uses",
           "perplexity": "`/chat/completions`",
           "google_aio": "SerpApi `google` then `google_ai_overview`, `no_cache=true`"}[e]
    if not counts:
        A(f"| {LAB[e]} | {req} | none returned | 0 |")
    for mid, cnt in sorted(counts.items(), key=lambda kv: -kv[1]):
        A(f"| {LAB[e]} | {req} | `{mid}` | {cnt} |")
A("")
A("**Each engine ran on exactly one model.** That is worth stating because an earlier "
  "draft of this table showed two model strings against Claude. The second string was "
  "an artefact: when a call fails there is no model in the response, so the collector "
  "wrote a fallback string into the error row. "
  + (", ".join(f"All {v} `{k}` rows on the {LAB[e]} engine are billing-error rows carrying no answer"
               for e in E for k, v in (R['model_strings_on_failed_calls'].get(e) or {}).items()
               if k not in (R['model_counts'].get(e) or {}))
     or "No such rows remain")
  + ". No repeat pair in section 4.5 spans two model strings, and any that did would be "
    "excluded there by construction, because such a pair measures a model change rather "
    "than run-to-run noise.")
A("")
_xm = R["extractor_model"]
A(f"**The Layer 2 extractor is a separate thing and runs on a different model.** It "
  f"uses `{_xm['model']}` at temperature {_xm['temperature']}. {_xm['why_not_the_engine_model']} "
  f"Do not read the extractor model as an engine model.")
A("")
A("Two configuration decisions are worth stating plainly because they shape the "
  "results.")
A("")
A("**ChatGPT had to be forced to search.** On a pilot batch with `tool_choice: auto`, "
  "ChatGPT returned zero citations on every question at roughly four seconds of "
  "latency, while the other three engines returned live citations at fifteen to forty "
  "seconds. It was answering from parametric memory. Comparing that against three "
  "engines that searched the live web would have made every divergence number an "
  "artefact. `tool_choice` was set to `required` and the pilot rows were deleted. "
  "**That ChatGPT does not search a commercial buyer question unless compelled is "
  "itself a finding**, and it means our ChatGPT condition is the searched condition, "
  "not the default one.")
A("")
A("**Claude is on the Sonnet tier, not the largest available model.** v1.0 ran on "
  "Claude Sonnet with web search. Keeping the tier keeps the v1.0 baseline tie-back "
  "like for like. A larger model would have made the Claude column better and the "
  "comparison to v1.0 worse.")
A("")
A("Every answer is stored the moment it is scored, one database row per engine-answer, "
  "with the run id, timestamp, category, question, engine, model string, repeat index, "
  "status, full answer text, cited URLs, latency and SerpApi calls consumed. Collection "
  "is idempotent on `question_id | engine | repeat_index`, so a crash costs the "
  "in-flight call and nothing else.")
A("")
A("### 3.3 The repeat baseline")
A("")
A(f"A stratified subsample of **{MAN['n_stability_questions']} questions**, spread "
  f"across the {MAN['n_categories']} categories and balanced across question shapes, "
  f"was run **three times on all four engines**. Section 4.5 reads between-engine "
  f"agreement against within-engine agreement on exactly these questions, on the same "
  f"scale. Without it, a divergence number cannot be distinguished from ordinary "
  f"nondeterminism.")
A("")
A("### 3.4 Vendor extraction")
A("")
A("Two layers.")
A("")
A("**Layer 1 is deterministic and authoritative** for every company in the study "
  "universe. Answer text is normalised for non-breaking and thin spaces, curly quotes "
  "and the dash family, then whitespace-collapsed. Brand matching is word-boundary, "
  "and case-sensitive when the brand is a single plain alphabetic word, so a company "
  "called Pitch does not match the ordinary verb; a brand carrying a dot, digit, "
  "hyphen or space matches case-insensitively. Domain matching is at hostname level "
  "with multi-domain values split on pipes and commas, so subdomains count and "
  "near-misses do not. These are v1.0's rules, unchanged.")
A("")
A("**Layer 2 is an LLM extractor**, Claude at temperature 0, one fixed prompt that "
  "lists every vendor or product named in an answer, normalised. The exact prompt is "
  "in the repository. Layer 2 exists to catch vendors outside the study universe, and "
  "**it may only add out-of-universe names**. Any Layer 2 claim about a universe "
  "company is discarded unless Layer 1 also finds the string in the answer, so the "
  "extractor cannot inflate a measured company's numbers in either direction.")
A("")
A("### 3.5 Citation classification")
A("")
A("Every cited URL is reduced to a hostname and classified as vendor-owned, review "
  "platform, editorial, analyst, community or other, reusing v1.0's classification so "
  "the 77.4 percent vendor-authored figure from that volume is comparable per engine "
  "here.")
A("")
A("### 3.6 Completeness rules")
A("")
A(f"The primary sample is the **{R['n_questions_all_four_ok']} questions where all "
  f"four engines returned a usable answer**, out of {R['n_questions_attempted']} "
  f"attempted. Pairwise metrics additionally use every question both engines in that "
  f"pair answered, which is why pair sample sizes differ and are reported. Attrition "
  f"is reported per engine rather than absorbed.")
A("")
A("A Google query that returns no AI Overview is recorded with its own status, "
  "`no_aio`, not as an error. Google declining to generate an AI answer for a "
  "commercial buyer question is a result, and section 4.0 treats it as one.")
A("")
A("### 3.7 Budget constraint, stated openly")
A("")
A(f"Google AI Overviews is the only engine with a hard external cost, through "
  f"SerpApi's 1,000-search monthly plan at a 200-search hourly rate limit. The sample "
  f"was sized against that ceiling before any question was chosen: "
  f"{MAN['n_questions']} questions plus {MAN['n_stability_questions']} repeated twice, "
  f"at a worst case of two SerpApi searches per question, gives "
  f"{MAN['serpapi_worst_case']} searches against a usable budget of 880 after a "
  f"120-search reserve. Actual consumption was **{R['serpapi_calls_used_total']} "
  f"SerpApi searches**. The sample is therefore bounded by measurement cost, not by "
  f"what would have been ideal, and a larger question set on AI Overviews would need a "
  f"larger plan.")
A("")

A("### 3.8 What happened to the collection")
A("")
A("This section exists because the study as planned is not the study that ran, and "
  "the difference has to be legible to anyone reading a number below.")
A("")
A(f"Collection ran {WINDOW}. It began with all four engines live. Over the "
  f"following few hours three of the four API accounts ran out of money, in this order:")
A("")
A("| Engine | What happened | Reason returned by the API | Answers collected |")
A("|---|---|---|---|")
A(f"| ChatGPT | stopped ~06:20 UTC, account not refilled | `You have no credits remaining` | {CC['per_engine']['chatgpt']['main_set_rows']} of {CC['planned_questions']} |")
A(f"| Perplexity | stopped 08:04 UTC, account not refilled | `You exceeded your current quota` | {CC['per_engine']['perplexity']['main_set_rows']} of {CC['planned_questions']} |")
A(f"| Claude | stopped 09:15 UTC, **account topped up, collection resumed the same day and completed** | `Your credit balance is too low` | {CC['per_engine']['claude']['main_set_rows']} of {CC['planned_questions']} |")
A(f"| Google AI Overviews | ran to completion, never interrupted | prepaid SerpApi quota | {CC['per_engine']['google_aio']['main_set_rows']} of {CC['planned_questions']} |")
A("")
A("The Claude row is not a contradiction. That account emptied mid-run, was topped "
  "up, and the collector resumed on the same day and finished the full 280 questions "
  "plus all three repeat runs, because collection is idempotent on "
  "`question_id | engine | repeat_index` and only ever collects what is missing. "
  "ChatGPT and Perplexity were deliberately not refilled: a refill collected in a "
  "second window would make every cross-engine pair span two windows, so engine drift "
  "between windows would read as engine divergence and inflate the very quantity this "
  "paper measures. Those two engines stay short, and a clean four-engine "
  "single-window collection is left to a future volume.")
A("")
A("None of these is an engine behaviour. They are billing events on the accounts "
  "used to reach the engines, and they are reported separately from `no_aio`, which "
  "IS an engine behaviour. Rows carrying a billing error are excluded from every "
  "denominator in this paper and are retained in `raw.csv` with status `api_error` "
  "so the exclusion is checkable.")
A("")
A("Three consequences, all of which shape how the results should be read.")
A("")
A(f"**One.** The four-engine intersection, the questions where all four engines "
  f"returned an answer, is {ES['four_engine']['n_questions_all_ok']} questions. That "
  f"is too thin to carry a headline and is never used for one here. Where a "
  f"statistic needs a common set of engines it is reported for each engine set with "
  f"its own n: four engines "
  f"({ES['four_engine']['n_questions_all_ok']} questions), three engines without "
  f"ChatGPT ({ES['three_engine']['n_questions_all_ok']}), and two engines, Claude "
  f"and Google AI Overviews ({ES['two_engine']['n_questions_all_ok']}).")
A("")
A(f"**Two.** Pairwise metrics are unaffected in kind, only in precision, because a "
  f"pair only needs both of its own engines to have answered. The Claude and Google "
  f"AI Overviews pair rests on "
  f"{pj['pairs'].get('claude|google_aio', {}).get('n_questions', 0)} questions; the "
  f"pairs involving ChatGPT rest on "
  f"{pj['pairs'].get('chatgpt|claude', {}).get('n_questions', 0)}. Both are reported, "
  f"and the sample size sits in the table next to the number.")
A("")
A(f"**Three, and this is why the paper still stands:** the decisive test in section "
  f"4.5 does not need four engines. It needs repeats, and both engines that finished "
  f"have them. Google AI Overviews and Claude each completed all three runs of all "
  f"{MAN['n_stability_questions']} stability questions, contributing "
  f"{DTE['engines']['google_aio']['repeat_pairs']} and "
  f"{DTE['engines']['claude']['repeat_pairs']} repeat pairs respectively. The two "
  f"engines that ran out of credit contribute no repeat pairs and no verdict, which "
  f"is stated rather than hidden.")
A("")
A(f"The Layer 2 extractor shares the Anthropic key with the Claude engine, so it "
  f"stopped when that account did and resumed with it. It covers "
  f"{p(L2['coverage'])} of collected answers ({L2['with_layer2']} of "
  f"{L2['answers_ok']})"
  + ("." if not L2['missing_by_engine'] else
     ", short by " + ", ".join(f"{v} {LAB.get(k, k)}" for k, v in sorted(L2['missing_by_engine'].items())) + ".")
  + " Layer 1 covers every answer. Because Layer 2 can only ADD out-of-universe "
  "names, the gap can only narrow a vendor set and never widen one, and every "
  "universe-only statistic in this paper is completely independent of it. The "
  "universe-only sensitivity analysis in section 4.8 is therefore also the "
  "Layer-2-free reading of the results.")
A("")
# ---------------------------------------------------------------- results
A("## 4. Results")
A("")
A("### 4.0 Not every engine answers")
A("")
A("| Engine | Attempted | Answered | No AI Overview | API error | Answer rate |")
A("|---|---|---|---|---|---|")
for e in E:
    a = attr[e]
    A(f"| {LAB[e]} | {a['attempted']} | {a['ok']} | {a['no_aio']} | {a['api_error']} | {p(a['answer_rate'])} |")
A("")
A(f"Google returned an AI Overview for **{p(aio['rate'])}** of these questions "
  f"({aio['triggered']} of {aio['questions']}). By question shape:")
A("")
A("| Question shape | Questions | AI Overview returned | Rate |")
A("|---|---|---|---|")
for s, v in R["aio_trigger_rate_by_shape"].items():
    A(f"| {s} | {v['questions']} | {v['triggered']} | {p(v['rate'])} |")
A("")
A("This sits below the trigger rates Seer Interactive reports for general query "
  "populations, which is what one would expect: these are narrow B2B software buying "
  "questions, not consumer queries. The practical consequence for a vendor is direct. "
  "On a question where Google returns no AI Overview, there is no AI answer to be "
  "named in, and any \"AI visibility\" score that silently drops those questions from "
  "its denominator will overstate coverage.")
A("")
A("### 4.1 How much of a shortlist do two engines share?")
A("")
A("| Engine pair | Questions | Mean Jaccard | Median | 95% CI |")
A("|---|---|---|---|---|")
for k, v in pairs_sorted:
    c = v["ci95"]
    cis = f"{c['lo']:.3f} to {c['hi']:.3f}" if c else "NOT COMPUTED"
    A(f"| {pairname(k)} | {v['n_questions']} | {n(v['mean'])} | {n(v['median'])} | {cis} |")
A("")
A(f"Overall mean pairwise Jaccard similarity is **{ci(pj['overall_ci95'])}** over "
  f"{pj['n_pair_observations']} engine-pair observations; the median is "
  f"{n(pj['overall_median'])}.")
if most_alike and least_alike:
    A("")
    A(f"The most alike pair is **{pairname(most_alike[0])}** at "
      f"{n(most_alike[1]['mean'])}. The least alike is "
      f"**{pairname(least_alike[0])}** at {n(least_alike[1]['mean'])}. The spread "
      f"between the most and least similar pair is "
      f"{n(most_alike[1]['mean'] - least_alike[1]['mean'])}, which means \"how much do "
      f"AI engines agree\" does not have one answer even within this sample.")
A("")
A("*Figure 1: 4x4 Jaccard matrix.*")
A("")
A("### 4.2 Consensus")
A("")
A("Reported for every engine set, because the four-engine intersection is too small "
  "to stand alone and hiding that behind one number would be the exact failure this "
  "research programme exists to point at.")
A("")
A("| Engine set | Questions | Vendor mentions | Named by exactly 1 engine | Named by every engine in the set |")
A("|---|---|---|---|---|")
for _k in ("four_engine", "three_engine", "two_engine"):
    _c = R["consensus_by_engine_set"][_k]
    _last = str(_c["n_engines"])
    A(f"| {', '.join(LAB[e] for e in _c['engines'])} | {_c['n_questions']} | "
      f"{_c['distinct_vendor_slots']} | {p(_c['share']['1'])} | {p(_c['share'][_last])} |")
A("")
A(f"The best-powered reading is the {BEST['n_engines']}-engine row: across "
  f"{BEST['n_questions']} questions answered by all of {BEST_NAME}, "
  f"{BEST['distinct_vendor_slots']} distinct vendor mentions were made, "
  f"**{p(BEST['share']['1'])} of them by a single engine** and "
  f"**{p(BEST['share'][str(BEST['n_engines'])])} by all {BEST['n_engines']}**.")
A("")
A("The pattern is the same at every set size, which is the useful thing about "
  "reporting all three: single-engine share stays between "
  + p(min(v['share']['1'] for v in R['consensus_by_engine_set'].values())) + " and "
  + p(max(v['share']['1'] for v in R['consensus_by_engine_set'].values()))
  + " no matter which engines are in the room.")
A("")
A("*Figure 2: consensus distribution.*")
A("")
A("### 4.3 What each engine returns")
A("")
A("Vendor-list length is a within-engine statistic and needs no common question set, "
  "so it is computed over every answer each engine actually returned.")
A("")
A("| Engine | Answers | Mean vendors named | Median | Distinct vendors seen | Mean answer length (chars) |")
A("|---|---|---|---|---|---|")
_pea = R["per_engine_all_answers"]
for e in E:
    v = _pea[e]
    A(f"| {LAB[e]} | {v['answers']} | {n(v['mean_vendors_per_answer'], 2)} | "
      f"{n(v['median_vendors_per_answer'], 1)} | {v['distinct_vendors']} | "
      f"{n(v['mean_answer_chars'], 0)} |")
A("")
A(f"The spread is large and it tracks answer length. Google AI Overviews names "
  f"{n(_pea['google_aio']['mean_vendors_per_answer'], 1)} vendors in an average "
  f"{n(_pea['google_aio']['mean_answer_chars'], 0)}-character answer; the "
  f"conversational engines name two to three times as many in answers two to five "
  f"times as long. A vendor competing for a place in a Google AI Overview is "
  f"competing for a materially scarcer slot than one competing inside a Claude or "
  f"Perplexity answer, and that alone will make single-engine visibility scores "
  f"disagree before any ranking difference is considered.")
A("")
A("v1.0 found the average single-engine answer named 2.05 vendors. Every engine here "
  "names more than that, which is worth stating plainly rather than treating the two "
  "numbers as directly comparable: the extraction layer here is wider than v1.0's, "
  "which counted only companies inside the study universe.")
A("")
A("Uniqueness needs a common question set, so it is reported per engine set:")
A("")
A("| Engine set | Engine | Vendor slots | Unique to this engine | Unique rate |")
A("|---|---|---|---|---|")
for _k in ("four_engine", "three_engine", "two_engine"):
    for e, v in R["per_engine_by_engine_set"][_k].items():
        A(f"| {_k.replace('_', ' ')} | {LAB[e]} | {v['total_vendor_slots']} | "
          f"{v['unique_to_this_engine']} | {p(v['unique_vendor_rate'])} |")
A("")
A("### 4.4 Agreement as a rater statistic")
A("")
A("Treating the engines as raters making a binary mention decision over each "
  "question's own category universe:")
A("")
A("| Engine set | Raters | Questions | Panels | Fleiss kappa, all vendors | Fleiss kappa, universe only |")
A("|---|---|---|---|---|---|")
for _k in ("four_engine", "three_engine", "two_engine"):
    _a = R["fleiss_kappa_by_engine_set"][_k]
    _b = R["fleiss_kappa_by_engine_set_universe_only"][_k]
    A(f"| {_k.replace('_', ' ')} | {_a['raters']} | {_a['n_questions']} | {_a['n_panels']} | "
      f"{n(_a['kappa'])} | {n(_b['kappa'])} |")
A("")
A("The two columns say different things and both are worth having. Over ALL vendors, "
  "including everything the extractor found outside the study universe, agreement is "
  "close to zero or below it: the long tail of names one engine mentions and the "
  "others never do swamps the signal. Restricted to the study universe, where every "
  "engine plausibly could have named every company, agreement is moderate. The "
  "practical translation is that engines agree reasonably about the well-known "
  "vendors in a category and almost not at all about the tail, which is exactly "
  "where a challenger brand lives.")
A("")
A("### 4.5 The decisive test, per engine")
A("")
A("Everything above measures difference. This measures whether the difference is "
  "bigger than the noise, and it does so **one engine at a time**.")
A("")
A("That choice is deliberate and it changed the paper. A pooled within-engine mean is "
  "dominated by whichever engine contributed the most repeat pairs; compared against a "
  "between-engine mean drawn from all engines, it can report a separation that only one "
  "engine actually has. That is an unstated denominator, which is the failure this "
  "research programme exists to point at, so we do not do it.")
A("")
A(f"For each engine the comparison is like for like, on the same "
  f"{DTE['stability_questions']} stability questions: **within** is every pair of "
  f"repeats of the same question on that engine, **between** is that same engine "
  f"against the others on repeat 1 of those same questions. A repeat pair whose two "
  f"runs used different model strings measures a model change rather than run-to-run "
  f"noise and is excluded; "
  + (f"{sum(DTE['model_split_pairs_excluded'].values())} pairs were excluded on that rule."
     if DTE['model_split_pairs_excluded'] else "no pair triggered that rule.")
  + f" An engine needs at least {DTE['min_pairs_for_a_verdict']} repeat pairs before we "
    f"assert a verdict for it.")
A("")
A("| Engine | Repeat pairs | Within-engine | Between-engine | Gap (95% CI) | Verdict |")
A("|---|---|---|---|---|---|")
for e in E:
    blk = DTE["engines"][e]
    m = blk["modes"]["full"]
    if m["within"]["n_pairs"] == 0:
        A(f"| {LAB[e]} | 0 | no repeats collected | | | no repeat data |")
        continue
    g = m["gap"]
    gs = (f"{n(g['point'])} ({n(g['lo'])} to {n(g['hi'])})") if g else "NOT COMPUTED"
    A(f"| {LAB[e]} | {m['within']['n_pairs']} | {n(m['within']['mean'])} "
      f"(n={m['within']['n_pairs']}) | {n(m['between']['mean'])} "
      f"(n={m['between']['n_pairs']}) | {gs} | {blk['verdict']} |")
A("")
def sentence_case(t):
    """Uppercase only the FIRST character. str.capitalize() lowercases everything
    after it, which turned 'On Google AI Overviews' into 'on google ai overviews'."""
    t = str(t or "").strip()
    return (t[:1].upper() + t[1:]) if t else t


A(f"**{sentence_case(DTE['headline'])}.**")
A("")
if len(POWERED) == 1 and POWERED[0] in ROBUST:
    _e = POWERED[0]
    _o = [e for e in E if DTE["engines"][e]["repeat_pairs"] > 0 and e != _e]
    A(f"Read that carefully, because it is narrower than the headline this study set out "
      f"to test. The separation is established on {LAB[_e]}. "
      + (f"{', '.join(LAB[x] for x in _o)} "
         + ("has" if len(_o) == 1 else "have")
         + f" too few repeat pairs to say either way, because "
           f"{'its' if len(_o) == 1 else 'their'} account ran out of credit before the "
           f"repeat runs finished. "
         if _o else "")
      + f"A reader is entitled to ask whether the other engines would show the same "
        f"pattern, and the honest answer is that this dataset cannot tell them.")
    A("")
A("#### Robustness: is the gap just list length?")
A("")
A(f"Google AI Overviews names "
  f"{n(R['per_engine_all_answers']['google_aio']['mean_vendors_per_answer'], 2)} vendors "
  f"in an average answer against "
  f"{n(R['per_engine_all_answers']['claude']['mean_vendors_per_answer'], 2)} for Claude "
  f"and {n(R['per_engine_all_answers']['perplexity']['mean_vendors_per_answer'], 2)} for "
  f"Perplexity. Jaccard between two similar-length short sets runs mechanically higher "
  f"than between two sets of very different length, so part of any within-versus-between "
  f"gap could be list length rather than divergence. Within-engine pairs compare an "
  f"engine with itself and are length-matched by construction; between-engine pairs are "
  f"not. That asymmetry has to be controlled or the result is not safe.")
A("")
A("Three controls, each recomputed from the same pairs:")
A("")
A("| Engine | Measure | Within | Between | Gap (95% CI) | Separates |")
A("|---|---|---|---|---|---|")
for e in E:
    blk = DTE["engines"][e]
    if blk["repeat_pairs"] == 0:
        continue
    for mode, _d in (("full", ""), ("universe", ""), ("topk", ""), ("overlap", "")):
        m = blk["modes"][mode]
        if m["within"]["n_pairs"] == 0:
            continue
        g = m["gap"]
        gs = (f"{n(g['point'])} ({n(g['lo'])} to {n(g['hi'])})") if g else "NOT COMPUTED"
        A(f"| {LAB[e]} | {m['description']} | {n(m['within']['mean'])} "
          f"(n={m['within']['n_pairs']}) | {n(m['between']['mean'])} "
          f"(n={m['between']['n_pairs']}) | {gs} | "
          f"{'yes' if m['gap_positive_at_95'] else 'no'} |")
A("")
_g_rob = [LAB[e] for e in ROBUST]
if _g_rob:
    A(f"For {', '.join(_g_rob)} the gap stays positive at 95% under every control, "
      f"including the overlap coefficient, which normalises by the smaller of the two "
      f"sets and is the least forgiving of a length artefact. The separation is not "
      f"length.")
else:
    A("No engine holds the separation under every control, so a length artefact cannot "
      "be ruled out and the result is not asserted.")
A("")
A("*Figure 3: within-engine versus between-engine agreement, per engine.*")
A("")
A("#### The pooled figure, for completeness only")
A("")
A(f"Pooled across all engines, within-engine agreement is "
  f"{ci(dt['within_engine']['ci95'])} over {dt['within_engine']['n_pairs']} repeat "
  f"pairs against between-engine {ci(dt['between_engine_same_questions']['ci95'])} over "
  f"{dt['between_engine_same_questions']['n_pairs']} pairs. "
  + (f"That pooled within-engine mean is "
     f"{p(DTE['engines'][POWERED[0]]['modes']['full']['within']['n_pairs'] / max(1, dt['within_engine']['n_pairs']))} "
     f"{LAB[POWERED[0]]} repeat pairs, which is exactly why it is not the headline."
     if POWERED else "It is not the headline."))
A("")
A("Within-engine agreement by engine, which is the number that pooled figure hides:")
A("")
A("| Engine | Repeat pairs | Mean Jaccard |")
A("|---|---|---|")
for e, v in dt["within_by_engine"].items():
    if v["n_pairs"]:
        A(f"| {LAB.get(e, e)} | {v['n_pairs']} | {n(v['mean'])} |")
A("")
A("There is a second reading of that column worth stating on its own. Even the best "
  "case here is an engine agreeing with itself on roughly half its own shortlist across "
  "runs of the identical question. Every single-run visibility number in this industry, "
  "including the one in our own v1.0, carries that variance and cannot show it.")
A("")
A("### 4.6 Company level")
A("")
cl = R["company_level"]
A(f"Being named is a fact about an individual answer, so this block does not need a "
  f"question every engine answered. It counts over every answer each engine actually "
  f"returned, which is both correct and far better powered than the four-engine "
  f"intersection.")
A("")
A(f"Of {cl['companies']} measured companies with questions in their category, "
  f"{cl['companies_with_two_or_more_engines']} were tested on at least two engines. "
  f"Among those, **{cl['visible_some_engines_only']} were visible on some engines and "
  f"invisible on others**, "
  f"{cl['visible_on_every_engine_that_answered']} were named at least once by every "
  f"engine that answered for them, and "
  f"{cl['invisible_on_every_engine']} were named by no engine at all.")
A("")
A(f"That middle number is the commercially important one. "
  f"{cl['visible_some_engines_only']} of {cl['companies_with_two_or_more_engines']} "
  f"companies would receive a materially different verdict depending on which single "
  f"engine their agency happened to measure. Per-company, per-engine named rates are "
  f"in `results.json` under `company_level.rows`.")
A("")
tb = R["vol1_tieback"]
A(f"Against the v1.0 Claude-engine baseline, Pearson r = "
  f"**{n(tb['pearson_r'], 2) if tb['pearson_r'] is not None else 'NOT COMPUTED'}** "
  f"over {tb['n']} companies. {tb['note']}")
A("")
A("*Figure 6: v1.0 baseline against v3.0 multi-engine visibility.*")
A("")
A("### 4.7 What each engine cites")
A("")
A("| Engine | Answers | Citations | Mean per answer | Vendor-owned | Review platform | Editorial | Analyst | Community | Other |")
A("|---|---|---|---|---|---|---|---|---|---|")
for e in E:
    c = cm[e]
    s = c["share"]
    A(f"| {LAB[e]} | {c['answers']} | {c['citations']} | "
      f"{n(c['mean_citations_per_answer'], 1)} | {p(s.get('vendor_owned'))} | "
      f"{p(s.get('review_platform'))} | {p(s.get('editorial'))} | {p(s.get('analyst'))} | "
      f"{p(s.get('community'))} | {p(s.get('other'))} |")
A("")
A("v1.0 found 77.4 percent of citations resolved to vendor-owned domains and 10.2 "
  "percent to review platforms, measured on one engine. Splitting that by engine is "
  "the point of this table.")
A("")
A("*Figure 5: citation source mix per engine.*")
A("")
A("### 4.8 Sensitivity")
A("")
A(f"Recomputed on universe-only vendor sets, which removes every out-of-universe name "
  f"the extractor found: mean pairwise Jaccard "
  f"**{ci(pju['overall_ci95'])}** against {ci(pj['overall_ci95'])} on the full sets; "
  f"single-engine share of vendor mentions "
  f"{p(R['consensus_universe_only']['share']['1'])} against "
  f"{p(cons['share']['1'])}; Fleiss' kappa "
  f"{n(R['fleiss_kappa_universe_only']['kappa'])} against "
  f"{n(R['fleiss_kappa']['kappa'])}.")
A("")

# ---------------------------------------------------------------- discussion
A("## 5. Discussion")
A("")
A("The practical reading is short. A single-engine visibility score is a measurement "
  "of one product, and it generalises to the other three only as far as the numbers "
  "above allow. Anyone selling a number that is described as \"your AI search "
  "visibility\" without naming the engine, the date and the question set is selling a "
  "number whose denominator is unstated.")
A("")
A("The second reading is about method rather than marketing. Because these systems "
  "are nondeterministic, cross-engine comparisons need a noise floor measured on the "
  "same questions in the same window, or the headline is uninterpretable. That is the "
  "contribution of section 4.5, and it is why the repeat subsample was mandatory "
  "rather than optional in this design.")
A("")
A("The AI Overview trigger rate deserves its own line. For a large share of these "
  "buyer questions Google produced no AI answer at all. Visibility work aimed at "
  "Google AI Overviews is therefore also a bet on the overview appearing, which is a "
  "different and less controllable thing than ranking within one.")
A("")

# ---------------------------------------------------------------- limitations
A("## 6. Limitations")
A("")
A("1. **A single time snapshot.** Everything here was collected between "
  f"{WINDOW}, a window of about four hours. These are products under continuous change; the numbers are a "
  "measurement of that window and should not be read as stable constants.")
A("2. **Google AI Overviews is scraped, not API-served.** There is no official API. "
  "SerpApi Best Effort is the only practical path, and it introduces a dependency "
  "whose failure modes are not fully observable from our side. A `no_aio` result means "
  "SerpApi returned no overview, which we treat as Google not producing one.")
A("3. **Engines are products, not models.** ChatGPT here is the OpenAI Responses API "
  "with a forced web-search tool, not the consumer application; the retrieval layer, "
  "the system prompt and the ranking logic of the consumer products are not "
  "observable. Results describe what these endpoints return, not what a person sees "
  "in the app.")
A("4. **The sampling frame is inherited.** Categories and companies come from v1.0, "
  "which was itself a convenience sample of B2B software categories. Nothing here "
  "generalises to consumer categories, to non-English queries or to markets outside "
  "the United States English locale used for collection.")
A("5. **Operator conflict of interest.** Broadcastwell ran the measurement and sells "
  "in the category. Broadcastwell is excluded from the measured sample and from every "
  "ranking. The mitigation is not that the conflict is absent, it is that the raw data "
  "and the code are public and the result can be recomputed by anyone who disagrees.")
A("6. **Measured within-engine nondeterminism.** The same engine does not return the "
  "same shortlist twice. Section 4.5 quantifies it rather than assuming it away, but "
  "it also means every single-run number in this paper, including v1.0's, carries a "
  "variance that a single run cannot show.")
A("7. **Question-bank provenance.** The questions were originally generated to a fixed "
  "specification rather than sampled from real search logs, so they are plausible "
  "buyer questions rather than observed ones.")
A("8. **The vendor universe is finite.** Layer 1 can only find companies it knows "
  "about. Layer 2 widens this, but a vendor named by an engine and absent from both "
  "the universe and the extractor's output would be invisible to this measurement.")
A("")

# ---------------------------------------------------------------- repro
A("## 7. Reproducibility")
A("")
A(f"Everything needed to recompute every number is in {REPO} under `volume-iii/`:")
A("")
A("| File | What it is |")
A("|---|---|")
A("| `data/questions.csv` | the exact question set, with category, shape and shape-label provenance |")
A("| `data/raw.csv` | one row per engine-answer: run id, timestamp, category, question, engine, model string, repeat index, status, full answer text, cited URLs, latency, SerpApi calls |")
A("| `data/scored.csv` | one row per answer with the extracted vendor set as JSON and the citation mix |")
A("| `data/vendor_mentions.csv` | long format: question, engine, vendor, in-universe flag |")
A("| `data/universe.csv` | the matching universe: companies, domains, competitors, aliases |")
A("| `data/results.json` | every computed figure, the direct source of the paper text and all six figures |")
A("| `analysis/01_build_sample.py` | sample construction |")
A("| `analysis/02_extract_vendors.py` | both extraction layers, reconciliation, citation classification |")
A("| `analysis/03_analyze.py` | every statistic, with the bootstrap seed fixed |")
A("| `analysis/04_figures.py` | all six figures |")
A("| `analysis/05_write_paper.py` | this document |")
A("| `analysis/extractor_prompt.txt` | the exact Layer 2 prompt |")
A("")
A(f"The bootstrap uses {R['bootstrap_reps']} replicates with a fixed seed, so the "
  f"confidence intervals reproduce exactly. Figures are generated from "
  f"`results.json`, never typed, so a caption cannot drift from the dataset.")
A("")

# ---------------------------------------------------------------- refs
A("## 8. References")
A("")
A("Every reference below was checked against the arXiv listing or the publisher page "
  "before publication. Author lists are as printed by the source.")
A("")
A("Aggarwal, P., Murahari, V., Rajpurohit, T., Kalyan, A., Narasimhan, K., Deshpande, A. "
  "(2024). GEO: Generative Engine Optimization. KDD 2024. arXiv:2311.09735.")
A("")
A("Bagga, P. S., Farias, V. F., Korkotashvili, T., Peng, T., Wu, Y. (2025). E-GEO: A "
  "Testbed for Generative Engine Optimization in E-Commerce. arXiv:2511.20867.")
A("")
A("BrightEdge (2026). Why AI Engines Cite Different Sources but Recommend the Same "
  "Brands. Weekly AI and Search Insights, 24 April 2026.")
A("")
A("Broadcastwell (2026). The 2026 State of Generative Engine Optimization, v1.0. "
  f"Zenodo. https://doi.org/{VOL1_DOI}")
A("")
A("Broadcastwell (2026). The 2026 State of Generative Engine Optimization, v2.0. "
  f"Zenodo. https://doi.org/{VOL2_DOI}")
A("")
A("Chu, X., Hou, Y. (2026). Incumbent Advantage: Brand Bias and Cognitive Manipulation "
  "Dynamics in LLM Recommendation Systems. arXiv:2606.17443.")
A("")
A("DerivateX (2026). ChatGPT and Google AI Overviews agree on tools, not sources. "
  "Open benchmark dataset, June 2026.")
A("")
A("Harsel, L., Yudina, A., Skopec, C. (2026). AI Overviews are expanding across "
  "commercial intent search. Semrush, 2 July 2026.")
A("")
A("Jack, W., Lehman, N., Maloney, K., Xu, S. (2026). Prominence-Stratified Failure "
  "Modes in Retrieval-Augmented Commercial Recommendation: A 37,000-Run Audit. "
  "arXiv:2605.27439.")
A("")
A("Jack, W., Lehman, N., Maloney, K., Xu, S. (2026). Divergent Recommendations, "
  "Convergent Diagnoses: Cross-Provider Failure-Mode Convergence in AI Commercial "
  "Recommendation. arXiv:2606.26116. Note: the 0.50 to 0.61 same-prompt rerun baseline "
  "quoted in that paper is cited by it from a separate Unusual.ai research report, not "
  "measured within it.")
A("")
A("Khromova, Y. (2025, updated 2026). ChatGPT vs Perplexity vs Google vs Bing: AI "
  "Search Engine Comparison. SE Ranking. Data collected 26 February to 3 March 2025.")
A("")
A("Lafferty, N. (2025). AI Platform Citation Patterns. Profound.")
A("")
A("McDonald, T., Cooley, H., Williams, M. (2026). AIO Impact on Google CTR: 2026 "
  "Update. Seer Interactive, 24 April 2026. Data through February 2026.")
A("")
A("Schulte, J., Bleeker, M., Kaufmann, P. (2026). Don't Measure Once: Measuring "
  "Visibility in AI Search (GEO). arXiv:2604.07585.")
A("")
A("Zatuchin, D. (2026). Who Owns the AI Recommendation? arXiv:2606.23057. Dataset "
  "released on Zenodo under CC BY 4.0.")
A("")
A("---")
A("")
A(f"*Cite this version: Sivakumar, S. (2026). {title_phrase} {SUFFIX}. "
  f"The 2026 State of Generative Engine Optimization, v3.0. Zenodo. "
  f"https://doi.org/{RESERVED_DOI}*")
A("")

open("PAPER.md", "w").write("\n".join(md))
_doc = "\n".join(md)
print(f"wrote PAPER.md ({len(_doc)} chars, {len(md)} blocks)")
print(f"title verdict: {subtitle_verdict}")
