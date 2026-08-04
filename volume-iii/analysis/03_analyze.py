#!/usr/bin/env python3
"""
Volume III, step 3: every headline number, computed row-level from scored.csv.

Nothing here is estimated, remembered or carried over from a previous volume.
Every figure printed by this script is recomputed from data/scored.csv on each
run, and results.json is what the paper, the figures and the site all read.

Outputs data/results.json and prints a human-readable summary.
"""
import csv, json, math, random, itertools, collections, os, sys

D = "data"
csv.field_size_limit(10_000_000)
ENGINES = ["chatgpt", "claude", "perplexity", "google_aio"]
LABEL = {"chatgpt": "ChatGPT", "claude": "Claude", "perplexity": "Perplexity",
         "google_aio": "Google AI Overviews"}
BOOT = 2000
random.seed(20260804)   # fixed so the numbers are reproducible


# ------------------------------------------------------------------ helpers
def jaccard(a, b):
    """Undefined when both sets are empty. Callers decide how to treat that."""
    if not a and not b:
        return None
    return len(a & b) / len(a | b)


def boot_ci(values, stat=None, n=BOOT, alpha=0.05):
    vals = [v for v in values if v is not None]
    if len(vals) < 2:
        return None
    stat = stat or (lambda xs: sum(xs) / len(xs))
    point = stat(vals)
    reps = []
    k = len(vals)
    for _ in range(n):
        reps.append(stat([vals[random.randrange(k)] for _ in range(k)]))
    reps.sort()
    lo = reps[int((alpha / 2) * n)]
    hi = reps[min(n - 1, int((1 - alpha / 2) * n))]
    return {"point": point, "lo": lo, "hi": hi, "n": k}


def median(xs):
    xs = sorted(x for x in xs if x is not None)
    if not xs:
        return None
    m = len(xs) // 2
    return xs[m] if len(xs) % 2 else (xs[m - 1] + xs[m]) / 2


def fleiss_kappa(panels):
    """
    panels: list of rows, each row a list of counts per category summing to n
    raters. Standard Fleiss kappa for a fixed number of raters.
    """
    panels = [p for p in panels if sum(p) > 0]
    if not panels:
        return None
    N = len(panels)
    n = sum(panels[0])
    if n < 2:
        return None
    k = len(panels[0])
    p_j = [sum(row[j] for row in panels) / (N * n) for j in range(k)]
    P_i = [(sum(c * c for c in row) - n) / (n * (n - 1)) for row in panels]
    P_bar = sum(P_i) / N
    P_e = sum(p * p for p in p_j)
    if abs(1 - P_e) < 1e-12:
        return None
    return (P_bar - P_e) / (1 - P_e)


# ------------------------------------------------------------------ load
scored = list(csv.DictReader(open(f"{D}/scored.csv")))
questions = {q["question_id"]: q for q in csv.DictReader(open(f"{D}/questions.csv"))}
universe_rows = list(csv.DictReader(open(f"{D}/universe.csv")))
universe_names = {u["company"] for u in universe_rows}
measured_names = {u["company"] for u in universe_rows if u.get("measured_subject") == "True"}

for r in scored:
    r["vendors"] = set(json.loads(r["vendor_set_json"]))
    r["order"] = json.loads(r.get("vendor_order_json") or "[]")
    r["repeat_index"] = int(r["repeat_index"])

# answers[(qid, engine, rep)] = row
answers = {(r["question_id"], r["engine"], r["repeat_index"]): r for r in scored}

R = {"generated_from": "data/scored.csv", "engines": ENGINES, "bootstrap_reps": BOOT}


# ------------------------------------------------------------------ 0. attrition
attr = {}
for e in ENGINES:
    rows = [r for r in scored if r["engine"] == e and r["repeat_index"] == 1]
    c = collections.Counter(r["status"] for r in rows)
    attr[e] = {"attempted": len(rows), "ok": c.get("ok", 0),
               "no_aio": c.get("no_aio", 0), "api_error": c.get("api_error", 0),
               "answer_rate": (c.get("ok", 0) / len(rows)) if rows else None}
R["attrition_main_set"] = attr

main_qids = sorted({r["question_id"] for r in scored if r["repeat_index"] == 1})
def complete_for(engines):
    return [q for q in main_qids
            if all(answers.get((q, e, 1)) and answers[(q, e, 1)]["status"] == "ok"
                   for e in engines)]


# The four-engine primary sample collapsed to a handful of questions when three
# of the four API accounts ran out of credit mid-collection. Every block below
# is therefore computed for several engine sets and reported with its own n,
# rather than silently reported on whichever sample happens to be largest.
ENGINE_SETS = {
    "four_engine": ["chatgpt", "claude", "perplexity", "google_aio"],
    "three_engine": ["claude", "perplexity", "google_aio"],
    "two_engine": ["claude", "google_aio"],
}
complete_qids = complete_for(ENGINES)
R["engine_sets"] = {k: {"engines": v, "n_questions_all_ok": len(complete_for(v))}
                    for k, v in ENGINE_SETS.items()}
R["n_questions_attempted"] = len(main_qids)
R["n_questions_all_four_ok"] = len(complete_qids)
R["primary_sample_note"] = ("primary sample = questions where all four engines returned "
                            "status ok; pairwise metrics additionally use questions where "
                            "both engines in the pair answered")

# AI Overview trigger rate is headline-eligible on its own
aio_rows = [r for r in scored if r["engine"] == "google_aio" and r["repeat_index"] == 1]
R["aio_trigger_rate"] = {
    "questions": len(aio_rows),
    "triggered": sum(1 for r in aio_rows if r["status"] == "ok"),
    "not_triggered": sum(1 for r in aio_rows if r["status"] == "no_aio"),
    "rate": (sum(1 for r in aio_rows if r["status"] == "ok") / len(aio_rows)) if aio_rows else None,
}
by_shape = collections.defaultdict(lambda: [0, 0])
for r in aio_rows:
    s = questions.get(r["question_id"], {}).get("question_shape", "unknown")
    by_shape[s][1] += 1
    if r["status"] == "ok":
        by_shape[s][0] += 1
R["aio_trigger_rate_by_shape"] = {s: {"triggered": v[0], "questions": v[1],
                                      "rate": v[0] / v[1] if v[1] else None}
                                  for s, v in sorted(by_shape.items())}


# ------------------------------------------------------------------ 1. pairwise Jaccard
def pairwise(universe_only=False):
    out = {}
    matrix = {a: {b: None for b in ENGINES} for a in ENGINES}
    for a, b in itertools.combinations(ENGINES, 2):
        vals = []
        for q in main_qids:
            ra, rb = answers.get((q, a, 1)), answers.get((q, b, 1))
            if not ra or not rb or ra["status"] != "ok" or rb["status"] != "ok":
                continue
            sa, sb = ra["vendors"], rb["vendors"]
            if universe_only:
                sa, sb = sa & universe_names, sb & universe_names
            j = jaccard(sa, sb)
            if j is not None:
                vals.append(j)
        ci = boot_ci(vals)
        out[f"{a}|{b}"] = {"n_questions": len(vals),
                           "mean": (sum(vals) / len(vals)) if vals else None,
                           "median": median(vals), "ci95": ci}
        m = (sum(vals) / len(vals)) if vals else None
        matrix[a][b] = m
        matrix[b][a] = m
    for e in ENGINES:
        matrix[e][e] = 1.0
    allvals = []
    for a, b in itertools.combinations(ENGINES, 2):
        for q in main_qids:
            ra, rb = answers.get((q, a, 1)), answers.get((q, b, 1))
            if not ra or not rb or ra["status"] != "ok" or rb["status"] != "ok":
                continue
            sa, sb = ra["vendors"], rb["vendors"]
            if universe_only:
                sa, sb = sa & universe_names, sb & universe_names
            j = jaccard(sa, sb)
            if j is not None:
                allvals.append(j)
    return {"pairs": out, "matrix": matrix,
            "overall_mean": (sum(allvals) / len(allvals)) if allvals else None,
            "overall_median": median(allvals),
            "overall_ci95": boot_ci(allvals), "n_pair_observations": len(allvals)}


R["pairwise_jaccard"] = pairwise(False)
R["pairwise_jaccard_universe_only"] = pairwise(True)


# ------------------------------------------------------------------ 2. consensus
def consensus(universe_only=False, engines=None):
    engines = engines or ENGINES
    complete_qids = complete_for(engines)
    ENGINES_L = engines
    counts = collections.Counter()
    per_q = collections.Counter()
    for q in complete_qids:
        sets = {}
        for e in ENGINES_L:
            s = answers[(q, e, 1)]["vendors"]
            sets[e] = (s & universe_names) if universe_only else s
        allv = set().union(*sets.values()) if sets else set()
        for v in allv:
            k = sum(1 for e in ENGINES_L if v in sets[e])
            counts[k] += 1
            per_q[k] += 1
    total = sum(counts.values())
    ks = [str(i) for i in range(1, len(ENGINES_L) + 1)]
    return {"engines": ENGINES_L, "n_engines": len(ENGINES_L),
            "n_questions": len(complete_qids), "distinct_vendor_slots": total,
            "by_engine_count": {k: counts.get(int(k), 0) for k in ks},
            "share": {k: (counts.get(int(k), 0) / total) if total else None for k in ks}}


R["consensus"] = consensus(False)
R["consensus_universe_only"] = consensus(True)
R["consensus_by_engine_set"] = {name: consensus(False, es) for name, es in ENGINE_SETS.items()}
R["consensus_by_engine_set_universe_only"] = {name: consensus(True, es) for name, es in ENGINE_SETS.items()}


# ------------------------------------------------------------------ 3. list length / uniqueness
def per_engine_for(engines):
    complete_qids = complete_for(engines)
    per_engine = {}
    for e in engines:
        rows = [answers[(q, e, 1)] for q in complete_qids]
        lens = [len(r["vendors"]) for r in rows]
        uniq = 0
        named = 0
        for q in complete_qids:
            mine = answers[(q, e, 1)]["vendors"]
            others = set()
            for o in engines:
                if o != e:
                    others |= answers[(q, o, 1)]["vendors"]
            uniq += len(mine - others)
            named += len(mine)
        per_engine[e] = {
            "label": LABEL[e],
            "answers": len(rows),
            "mean_vendors_per_answer": (sum(lens) / len(lens)) if lens else None,
            "median_vendors_per_answer": median(lens),
            "ci95_mean_vendors": boot_ci(lens),
            "total_vendor_slots": named,
            "unique_to_this_engine": uniq,
            "unique_vendor_rate": (uniq / named) if named else None,
            "distinct_vendors": len(set().union(*[r["vendors"] for r in rows])) if rows else 0,
        }
    return per_engine


# mean vendors per answer does not need a complete set at all: it is a
# within-engine statistic, so it is also reported over EVERY answer that engine
# gave, which is the properly powered version.
per_engine_all = {}
for e in ENGINES:
    rows = [r for r in scored if r["engine"] == e and r["repeat_index"] == 1 and r["status"] == "ok"]
    lens = [len(r["vendors"]) for r in rows]
    per_engine_all[e] = {
        "label": LABEL[e],
        "answers": len(rows),
        "mean_vendors_per_answer": (sum(lens) / len(lens)) if lens else None,
        "median_vendors_per_answer": median(lens),
        "ci95_mean_vendors": boot_ci(lens),
        "distinct_vendors": len(set().union(*[r["vendors"] for r in rows])) if rows else 0,
        "mean_answer_chars": (sum(int(r["answer_chars"]) for r in rows) / len(rows)) if rows else None,
    }
R["per_engine_all_answers"] = per_engine_all
R["per_engine"] = per_engine_for(ENGINES)
R["per_engine_by_engine_set"] = {name: per_engine_for(es) for name, es in ENGINE_SETS.items()}


# ------------------------------------------------------------------ 4. Fleiss kappa
def kappa(universe_only=True, engines=None):
    engines = engines or ENGINES
    complete_qids = complete_for(engines)
    panels = []
    for q in complete_qids:
        sets = {}
        for e in engines:
            s = answers[(q, e, 1)]["vendors"]
            sets[e] = (s & universe_names) if universe_only else s
        # restrict to the category's own universe so the panel is not swamped by
        # thousands of irrelevant zeros
        cat = answers[(q, engines[0], 1)]["category"]
        cat_pool = {u["company"] for u in universe_rows if u["category"] == cat}
        for c in re_split_competitors(cat):
            cat_pool.add(c)
        pool = cat_pool | set().union(*sets.values())
        for v in sorted(pool):
            yes = sum(1 for e in engines if v in sets[e])
            panels.append([yes, len(engines) - yes])
    return {"kappa": fleiss_kappa(panels), "n_panels": len(panels),
            "raters": len(engines), "n_questions": len(complete_qids),
            "note": ("binary mention panels over each question's own category universe "
                     "plus every vendor any engine named for that question")}


_comp_cache = {}


def re_split_competitors(cat):
    if cat in _comp_cache:
        return _comp_cache[cat]
    out = set()
    for u in universe_rows:
        if u["category"] == cat:
            for c in (u.get("competitors") or "").split(","):
                c = c.strip()
                if c:
                    out.add(c)
    _comp_cache[cat] = out
    return out


R["fleiss_kappa"] = kappa(False)
R["fleiss_kappa_universe_only"] = kappa(True)
R["fleiss_kappa_by_engine_set"] = {name: kappa(False, es) for name, es in ENGINE_SETS.items()}
R["fleiss_kappa_by_engine_set_universe_only"] = {name: kappa(True, es) for name, es in ENGINE_SETS.items()}


# ------------------------------------------------------------------ 5. THE DECISIVE TEST
# Rebuilt PER ENGINE. The pooled version is retained but demoted, because a
# pooled within-engine mean dominated by one engine's repeat pairs, compared
# against a between-engine mean drawn from all engines, is exactly the
# unstated-denominator failure this research programme exists to attack.
#
# For each engine E the comparison is like for like:
#   within(E)  = every pair of repeats of the SAME question on E
#   between(E) = every pair (E, other engine) on repeat 1 of THOSE SAME questions
# so both sides are the same questions, the same scale and the same engine's
# output on one side of every pair.
stab_qids = sorted({q for q in questions if questions[q]["in_stability_subsample"] == "True"})

# A repeat pair that spans two different model strings measures a MODEL CHANGE,
# not run-to-run noise, and would silently sit inside the decisive test. Those
# pairs are excluded and counted.
model_split_excluded = collections.Counter()


def sim_jaccard(a, b):
    return jaccard(a, b)


def sim_overlap(a, b):
    """Szymkiewicz-Simpson overlap coefficient, |A and B| / min(|A|,|B|).
    Normalising by the SMALLER set makes this far less sensitive to one engine
    naming three times as many vendors as another, which is the length artefact
    the Jaccard comparison is vulnerable to."""
    if not a or not b:
        return None
    return len(a & b) / min(len(a), len(b))


def topk(order_list, k):
    return set(order_list[:k])


def collect_pairs(engine, mode, k=5):
    """mode: full | universe | topk | overlap"""
    within, between = [], []
    for q in stab_qids:
        reps = [answers[(q, engine, i)] for i in (1, 2, 3)
                if answers.get((q, engine, i)) and answers[(q, engine, i)]["status"] == "ok"]
        for ra, rb in itertools.combinations(reps, 2):
            if ra["model_id"] != rb["model_id"]:
                model_split_excluded[engine] += 1
                continue
            v = pair_value(ra, rb, mode, k)
            if v is not None:
                within.append(v)
        ra = answers.get((q, engine, 1))
        if not ra or ra["status"] != "ok":
            continue
        for other in ENGINES:
            if other == engine:
                continue
            rb = answers.get((q, other, 1))
            if not rb or rb["status"] != "ok":
                continue
            v = pair_value(ra, rb, mode, k)
            if v is not None:
                between.append(v)
    return within, between


def pair_value(ra, rb, mode, k=5):
    if mode == "full":
        return sim_jaccard(ra["vendors"], rb["vendors"])
    if mode == "universe":
        return sim_jaccard(ra["vendors"] & universe_names, rb["vendors"] & universe_names)
    if mode == "topk":
        return sim_jaccard(topk(ra["order"], k), topk(rb["order"], k))
    if mode == "overlap":
        return sim_overlap(ra["vendors"], rb["vendors"])
    raise ValueError(mode)


def gap_ci(within, between):
    if len(within) < 2 or len(between) < 2:
        return None
    diffs = []
    for _ in range(BOOT):
        wm = sum(within[random.randrange(len(within))] for _ in range(len(within))) / len(within)
        bm = sum(between[random.randrange(len(between))] for _ in range(len(between))) / len(between)
        diffs.append(wm - bm)
    diffs.sort()
    return {"point": (sum(within) / len(within)) - (sum(between) / len(between)),
            "lo": diffs[int(0.025 * BOOT)], "hi": diffs[int(0.975 * BOOT)]}


MODES = [("full", "Jaccard, full vendor sets"),
         ("universe", "Jaccard, restricted to the study universe"),
         ("topk", "Jaccard, each answer truncated to its first 5 named vendors"),
         ("overlap", "Overlap coefficient, normalised by the smaller set")]

per_engine_test = {}
MIN_PAIRS = 12   # below this a per-engine verdict is not asserted
for e in ENGINES:
    block = {"label": LABEL[e], "modes": {}}
    for mode, desc in MODES:
        w, b = collect_pairs(e, mode)
        g = gap_ci(w, b)
        block["modes"][mode] = {
            "description": desc,
            "within": {"n_pairs": len(w), "mean": (sum(w) / len(w)) if w else None,
                       "median": median(w), "ci95": boot_ci(w)},
            "between": {"n_pairs": len(b), "mean": (sum(b) / len(b)) if b else None,
                        "median": median(b), "ci95": boot_ci(b)},
            "gap": g,
            "gap_positive_at_95": bool(g and g["lo"] > 0),
        }
    wf = block["modes"]["full"]["within"]["n_pairs"]
    block["repeat_pairs"] = wf
    block["adequately_powered"] = wf >= MIN_PAIRS
    # The two LENGTH controls are the ones that answer "is this just list length":
    # top-k truncation equalises how many vendors each side contributes, and the
    # overlap coefficient normalises by the smaller set. The universe restriction
    # is a SCOPE check, not a length check, and it discards so many pairs that a
    # wide interval there is a power problem rather than a contradiction.
    LENGTH_CONTROLS = ("topk", "overlap")
    block["length_controls_hold"] = all(
        block["modes"][m]["gap_positive_at_95"] for m in LENGTH_CONTROLS)
    block["controls_that_fail"] = [
        m for m, _ in MODES if not block["modes"][m]["gap_positive_at_95"]]
    block["verdict"] = (
        "not enough repeat pairs to assert a verdict" if wf < MIN_PAIRS
        else "separates, and on every check including both length controls"
        if all(block["modes"][m]["gap_positive_at_95"] for m, _ in MODES)
        else "separates, and both length controls hold; wider interval on "
             + " and ".join(block["controls_that_fail"])
        if block["modes"]["full"]["gap_positive_at_95"] and block["length_controls_hold"]
        else "separates on the headline measure but a length artefact cannot be ruled out"
        if block["modes"]["full"]["gap_positive_at_95"]
        else "no separation between within-engine and between-engine agreement")
    per_engine_test[e] = block

# pooled, retained but demoted
pool_w, pool_b = [], []
for e in ENGINES:
    w, b = collect_pairs(e, "full")
    pool_w.extend(w)
for q in stab_qids:
    for a, b_ in itertools.combinations(ENGINES, 2):
        ra, rb = answers.get((q, a, 1)), answers.get((q, b_, 1))
        if ra and rb and ra["status"] == "ok" and rb["status"] == "ok":
            v = jaccard(ra["vendors"], rb["vendors"])
            if v is not None:
                pool_b.append(v)

powered = [e for e in ENGINES if per_engine_test[e]["adequately_powered"]]
agree = [e for e in powered if per_engine_test[e]["modes"]["full"]["gap_positive_at_95"]]
robust = [e for e in powered
          if all(per_engine_test[e]["modes"][m]["gap_positive_at_95"] for m, _ in MODES)]
length_safe = [e for e in powered
               if per_engine_test[e]["modes"]["full"]["gap_positive_at_95"]
               and per_engine_test[e]["length_controls_hold"]]

_nm = lambda es: ", ".join(LABEL[x] for x in es)
if not powered:
    headline = "no engine has enough repeat pairs to support a verdict"
elif len(powered) == 1:
    e0 = powered[0]
    if e0 in robust:
        headline = (f"established on {LABEL[e0]} only, where the separation survives every "
                    f"length control. No other engine has {MIN_PAIRS} or more repeat pairs, "
                    f"so this is a single-engine result and must be described as one")
    elif e0 in agree:
        headline = (f"established on {LABEL[e0]} only, on the headline measure but not on "
                    f"every length control. No other engine has enough repeat pairs")
    else:
        headline = (f"{LABEL[e0]} is the only engine with enough repeat pairs and it does "
                    f"NOT separate. There is no supported divergence finding")
elif len(agree) == len(powered) and len(robust) == len(powered):
    headline = (f"holds on all {len(powered)} adequately powered engines ({_nm(powered)}), "
                f"and survives every check on each of them")
elif len(agree) == len(powered) and len(length_safe) == len(powered):
    headline = (f"holds on all {len(powered)} adequately powered engines ({_nm(powered)}), "
                f"and both length controls hold on each of them, so it is not an artefact "
                f"of one engine naming shorter lists than another")
elif len(agree) == len(powered) and length_safe:
    _fail = [e for e in powered if e not in length_safe]
    headline = (f"engine-specific. On {_nm(length_safe)} the separation survives every "
                f"length control and is real. On {_nm(_fail)} it appears on raw Jaccard "
                f"but disappears once list length is controlled, so on "
                f"{_nm(_fail)} it cannot be distinguished from a list-length artefact")
elif len(agree) == len(powered):
    headline = (f"appears on raw Jaccard for all {len(powered)} adequately powered engines "
                f"({_nm(powered)}) but survives a length control on none of them, so it "
                f"cannot be separated from a list-length artefact on this sample")
elif agree:
    headline = ("holds on " + _nm(agree) + " and NOT on " +
                _nm([e for e in powered if e not in agree]) +
                ", so it is an engine-specific result, not a general one")
else:
    headline = ("no adequately powered engine separates its between-engine agreement from "
                "its own run-to-run noise")

R["decisive_test_per_engine"] = {
    "stability_questions": len(stab_qids),
    "min_pairs_for_a_verdict": MIN_PAIRS,
    "engines": per_engine_test,
    "adequately_powered": powered,
    "separating_on_headline_measure": agree,
    "separating_on_every_control": robust,
    "length_controls_hold": length_safe,
    "headline": headline,
    "model_split_pairs_excluded": dict(model_split_excluded),
    "note": ("For each engine, within-engine pairs are repeats of the same question on that "
             "engine and between-engine pairs are that engine against the others on the same "
             "questions. Pairs whose two runs used different model strings are excluded, "
             "because they measure a model change rather than run-to-run noise."),
}

w_ci, b_ci = boot_ci(pool_w), boot_ci(pool_b)
R["decisive_test"] = {
    "stability_questions": len(stab_qids),
    "within_engine": {"n_pairs": len(pool_w), "mean": w_ci["point"] if w_ci else None,
                      "median": median(pool_w), "ci95": w_ci},
    "between_engine_same_questions": {"n_pairs": len(pool_b),
                                      "mean": b_ci["point"] if b_ci else None,
                                      "median": median(pool_b), "ci95": b_ci},
    "gap_within_minus_between": gap_ci(pool_w, pool_b),
    "within_by_engine": {e: {"n_pairs": per_engine_test[e]["modes"]["full"]["within"]["n_pairs"],
                             "mean": per_engine_test[e]["modes"]["full"]["within"]["mean"]}
                         for e in ENGINES},
    "pooled_is_not_the_headline": ("The pooled within-engine mean is dominated by whichever "
                                   "engine contributed the most repeat pairs. Read the "
                                   "per-engine table instead."),
    "verdict": headline,
}

# ------------------------------------------------------------------ 6. company level
mentions = list(csv.DictReader(open(f"{D}/vendor_mentions.csv")))
comp = collections.defaultdict(lambda: {e: 0 for e in ENGINES})
qcount = collections.defaultdict(lambda: {e: 0 for e in ENGINES})
cat_of = {u["company"]: u["category"] for u in universe_rows}

# Company-level visibility does NOT need a question every engine answered: a
# company is either named or not named in each answer that exists. Counting per
# (company, engine) over every answer that engine actually gave is both correct
# and far better powered than restricting to the four-engine intersection.
qs_by_cat = collections.defaultdict(list)
for q in main_qids:
    row = next((answers[(q, e, 1)] for e in ENGINES if (q, e, 1) in answers), None)
    if row:
        qs_by_cat[row["category"]].append(q)

for co in sorted(measured_names):
    cat = cat_of.get(co)
    for q in qs_by_cat.get(cat, []):
        for e in ENGINES:
            r = answers.get((q, e, 1))
            if not r or r["status"] != "ok":
                continue
            qcount[co][e] += 1
            if co in r["vendors"]:
                comp[co][e] += 1

company_rows = []
for co in sorted(comp):
    tot = {e: qcount[co][e] for e in ENGINES}
    if sum(tot.values()) == 0:
        continue
    rates = {e: (comp[co][e] / tot[e]) if tot[e] else None for e in ENGINES}
    engines_with_data = [e for e in ENGINES if tot[e] > 0]
    seen = [e for e in engines_with_data if rates[e] and rates[e] > 0]
    company_rows.append({
        "company": co, "category": cat_of.get(co, ""),
        "questions_per_engine": tot,
        "engines_with_data": len(engines_with_data),
        "named": {e: comp[co][e] for e in ENGINES},
        "named_rate": rates,
        "engines_naming_at_least_once": len(seen),
        "visible_on_some_invisible_on_others": 0 < len(seen) < len(engines_with_data),
        "invisible_everywhere": len(seen) == 0,
    })
multi = [c for c in company_rows if c["engines_with_data"] >= 2]
R["company_level"] = {
    "companies": len(company_rows),
    "companies_with_two_or_more_engines": len(multi),
    "invisible_on_every_engine": sum(1 for c in company_rows if c["invisible_everywhere"]),
    "visible_some_engines_only": sum(1 for c in multi if c["visible_on_some_invisible_on_others"]),
    "visible_on_every_engine_that_answered": sum(
        1 for c in multi if c["engines_naming_at_least_once"] == c["engines_with_data"]
        and c["engines_naming_at_least_once"] > 0),
    "note": ("Counted over every answer each engine actually returned, not over the "
             "four-engine intersection, because being named is an answer-level fact "
             "and the intersection collapsed when three accounts ran out of credit. "
             "engines_with_data records how many engines each company was tested on."),
    "rows": company_rows,
}

# Volume I Claude-engine baseline tie-back, joined by category
vol1 = list(csv.DictReader(open(f"{D}/state-of-geo-2026/challenger_visibility_v2.csv")))
vol1_by_cat = collections.defaultdict(list)
for r in vol1:
    vol1_by_cat[r["category"]].append(int(r["times_named_of_10"]) / 10.0)
tie = []
for c in company_rows:
    base = vol1_by_cat.get(c["category"])
    if not base:
        continue
    tie.append({"company": c["company"], "category": c["category"],
                "vol1_claude_named_rate_category_mean": sum(base) / len(base),
                "vol3_multi_engine_named_rate": (sum(v for v in c["named_rate"].values() if v is not None)
                                                 / max(1, sum(1 for v in c["named_rate"].values() if v is not None))),
                "vol3_claude_named_rate": c["named_rate"]["claude"]})


def pearson(xs, ys):
    n = len(xs)
    if n < 3:
        return None
    mx, my = sum(xs) / n, sum(ys) / n
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    dx = math.sqrt(sum((x - mx) ** 2 for x in xs))
    dy = math.sqrt(sum((y - my) ** 2 for y in ys))
    return num / (dx * dy) if dx and dy else None


xs = [t["vol1_claude_named_rate_category_mean"] for t in tie]
ys = [t["vol3_multi_engine_named_rate"] for t in tie]
R["vol1_tieback"] = {"n": len(tie), "pearson_r": pearson(xs, ys), "rows": tie,
                     "note": ("Volume I published company-level results anonymised, so the "
                              "join is at CATEGORY level: each company's Volume III rate is "
                              "compared with the mean Volume I Claude-engine named rate for "
                              "its category. This is weaker than a per-company join and is "
                              "stated as such in the paper.")}


# ------------------------------------------------------------------ 7. citation mix
# Restricted to repeat_index == 1, the main run, so the answer counts here match
# section 4.3 and every other table. Including the repeat runs would have made
# Google AI Overviews show 303 answers against 258 elsewhere, which reads as an
# inconsistency rather than as a different denominator.
cit = {}
for e in ENGINES:
    rows = [r for r in scored if r["engine"] == e and r["status"] == "ok"
            and r["repeat_index"] == 1]
    tot = 0
    mix = collections.Counter()
    for r in rows:
        for k in ("vendor_owned", "review_platform", "editorial", "analyst", "community", "other"):
            n = int(r.get("cit_" + k) or 0)
            mix[k] += n
            tot += n
    cit[e] = {"label": LABEL[e], "answers": len(rows), "citations": tot,
              "mix": dict(mix),
              "share": {k: (v / tot) if tot else None for k, v in mix.items()},
              "mean_citations_per_answer": (tot / len(rows)) if rows else None}
R["citation_mix"] = cit

# Volume I reported "among the 100 most-cited domains, 77.4% of citations are
# vendor-authored". That denominator is the top-100 domains, not all citations,
# so the all-citations table above is NOT comparable to it. This block rebuilds
# Volume I's denominator per engine so the two can be read against each other.
cits = [c for c in csv.DictReader(open(f"{D}/citations.csv"))
        if str(c.get("repeat_index")) == "1"]
top100 = {}
for e in ENGINES:
    rows = [c for c in cits if c["engine"] == e]
    per_domain = collections.Counter(c["domain"] for c in rows)
    top = [d for d, _ in per_domain.most_common(100)]
    tset = set(top)
    sub = [c for c in rows if c["domain"] in tset]
    mix = collections.Counter(c["source_type"] for c in sub)
    tot = len(sub)
    top100[e] = {
        "label": LABEL[e],
        "distinct_domains_all": len(per_domain),
        "citations_in_top100_domains": tot,
        "share_of_all_citations": (tot / len(rows)) if rows else None,
        "vendor_owned_share": (mix.get("vendor_owned", 0) / tot) if tot else None,
        "review_platform_share": (mix.get("review_platform", 0) / tot) if tot else None,
        "mix": dict(mix),
    }
# and the same statistic pooled across engines, which is the closest single
# number to Volume I's 77.4%
per_domain_all = collections.Counter(c["domain"] for c in cits)
tset = {d for d, _ in per_domain_all.most_common(100)}
sub = [c for c in cits if c["domain"] in tset]
mixall = collections.Counter(c["source_type"] for c in sub)
R["citation_top100_domains"] = {
    "per_engine": top100,
    "pooled": {
        "distinct_domains_all": len(per_domain_all),
        "citations_in_top100_domains": len(sub),
        "vendor_owned_share": (mixall.get("vendor_owned", 0) / len(sub)) if sub else None,
        "review_platform_share": (mixall.get("review_platform", 0) / len(sub)) if sub else None,
        "mix": dict(mixall),
    },
    "note": ("Volume I's 77.4% vendor-authored figure was computed over the 100 "
             "most-cited domains, not over all citations. This block reproduces "
             "that denominator; the all-citations table is a different and wider "
             "measure and the two must not be compared directly."),
}
# citation concentration, the other Volume I comparison
R["citation_concentration"] = {
    "total_citations": len(cits),
    "distinct_domains": len(per_domain_all),
    "top10_share": (sum(v for _, v in per_domain_all.most_common(10)) / len(cits)) if cits else None,
    "share_of_domains_cited_once": (sum(1 for v in per_domain_all.values() if v == 1)
                                    / len(per_domain_all)) if per_domain_all else None,
}

# models actually used
# Model strings are taken ONLY from answers the engine actually returned.
# A failed call has no model in its response, so the collector wrote a fallback
# string; counting those would put a model in the method section that never
# answered anything. All 22 "claude-sonnet-4-6" rows are billing-error rows and
# no Claude ANSWER ran on that model.
R["models_seen"] = {
    e: sorted({r["model_id"] for r in scored
               if r["engine"] == e and r["status"] == "ok" and r["model_id"]})
    for e in ENGINES}
R["model_counts"] = {
    e: dict(collections.Counter(r["model_id"] for r in scored
                                if r["engine"] == e and r["status"] == "ok" and r["model_id"]))
    for e in ENGINES}
R["model_strings_on_failed_calls"] = {
    e: dict(collections.Counter(r["model_id"] for r in scored
                                if r["engine"] == e and r["status"] == "api_error"))
    for e in ENGINES}
R["extractor_model"] = {
    "model": "claude-sonnet-4-6",
    "temperature": 0,
    "why_not_the_engine_model": ("claude-sonnet-5 rejects the request with 'temperature is "
                                 "deprecated for this model', so the Layer 2 extractor cannot "
                                 "be pinned to temperature 0 on it. The extractor runs on "
                                 "claude-sonnet-4-6, which still accepts temperature. This is "
                                 "the extractor only and is unrelated to the Claude ENGINE, "
                                 "every answer of which was produced by claude-sonnet-5."),
}
_ts = sorted(r["ts"] for r in scored if r.get("ts"))
R["collection_window"] = {
    "first": _ts[0] if _ts else None,
    "last": _ts[-1] if _ts else None,
    "date": (_ts[0][:10] if _ts else None),
    "utc_window": (f"{_ts[0][11:16]} to {_ts[-1][11:16]} UTC on {_ts[0][:10]}"
                   if _ts and _ts[0][:10] == _ts[-1][:10] else
                   (f"{_ts[0][:16].replace('T', ' ')} to {_ts[-1][:16].replace('T', ' ')} UTC"
                    if _ts else None)),
    "single_day": bool(_ts) and _ts[0][:10] == _ts[-1][:10],
}
R["serpapi_calls_used_total"] = sum(int(r.get("serpapi_calls_used") or 0) for r in scored)
R["rows_total"] = len(scored)

# Layer 2 coverage. The extractor shares the Anthropic key with the Claude
# engine, so when that account ran out of credits the extractor stopped too.
# Layer 1 ran on every answer regardless; Layer 2 only ever ADDS out-of-universe
# names, so a gap narrows some vendor sets slightly and never inflates one.
# Every universe-only figure in this file is completely independent of Layer 2.
ok_rows = [r for r in scored if r["status"] == "ok"]
with_l2 = [r for r in ok_rows if r.get("layer2_present") == "True"]
R["layer2_coverage"] = {
    "answers_ok": len(ok_rows),
    "with_layer2": len(with_l2),
    "coverage": (len(with_l2) / len(ok_rows)) if ok_rows else None,
    "missing_by_engine": dict(collections.Counter(
        r["engine"] for r in ok_rows if r.get("layer2_present") != "True")),
    "note": ("Layer 2 stopped when the Anthropic account ran out of credits. "
             "Layer 1 covers 100% of answers. Layer 2 can only add "
             "out-of-universe vendors, so the gap can only narrow a vendor set, "
             "never widen one, and every universe-only statistic here is "
             "unaffected."),
}

# What actually got collected, per engine, against what was planned.
R["collection_completeness"] = {
    "planned_questions": 280,
    "planned_stability_questions": 25,
    "planned_stability_repeats": 3,
    "per_engine": {
        e: {
            "label": LABEL[e],
            "main_set_rows": sum(1 for r in scored if r["engine"] == e and r["repeat_index"] == 1),
            "main_set_ok": sum(1 for r in scored if r["engine"] == e and r["repeat_index"] == 1
                               and r["status"] in ("ok", "no_aio")),
            "stability_questions_with_3_repeats": sum(
                1 for q in {x["question_id"] for x in scored
                            if questions.get(x["question_id"], {}).get("in_stability_subsample") == "True"}
                if len([r for r in scored if r["question_id"] == q and r["engine"] == e
                        and r["status"] in ("ok", "no_aio")]) >= 3),
            "billing_errors": sum(1 for r in scored if r["engine"] == e and r["status"] == "api_error"),
        } for e in ENGINES
    },
}

json.dump(R, open(f"{D}/results.json", "w"), indent=2)

# ------------------------------------------------------------------ print
def pct(x):
    return "n/a" if x is None else f"{100*x:.1f}%"


print(f"rows {R['rows_total']}  questions attempted {R['n_questions_attempted']}  "
      f"all-four-ok {R['n_questions_all_four_ok']}")
print("\nattrition (main set):")
for e in ENGINES:
    a = attr[e]
    print(f"  {LABEL[e]:22} ok {a['ok']:4}/{a['attempted']:4}  no_aio {a['no_aio']:4}  "
          f"api_error {a['api_error']:4}  answer rate {pct(a['answer_rate'])}")
print(f"\nAI Overview trigger rate: {pct(R['aio_trigger_rate']['rate'])} "
      f"({R['aio_trigger_rate']['triggered']} of {R['aio_trigger_rate']['questions']})")
pj = R["pairwise_jaccard"]
print(f"\nmean pairwise Jaccard overall: {pj['overall_mean']:.3f} "
      f"[{pj['overall_ci95']['lo']:.3f}, {pj['overall_ci95']['hi']:.3f}]"
      if pj["overall_mean"] is not None else "\nmean pairwise Jaccard: n/a")
for k, v in pj["pairs"].items():
    if v["mean"] is not None:
        print(f"  {k:28} mean {v['mean']:.3f}  median {v['median']:.3f}  n {v['n_questions']}")
c = R["consensus"]
print(f"\nconsensus over {c['n_questions']} questions, {c['distinct_vendor_slots']} vendor slots:")
for k in ("1", "2", "3", "4"):
    print(f"  named by exactly {k} engine(s): {c['by_engine_count'][k]:5}  {pct(c['share'][k])}")
print(f"\nFleiss kappa (all vendors): {R['fleiss_kappa']['kappa']}")
print(f"Fleiss kappa (universe only): {R['fleiss_kappa_universe_only']['kappa']}")
d = R["decisive_test"]
print(f"\nDECISIVE TEST on {d['stability_questions']} stability questions")
print(f"  within-engine  mean {d['within_engine']['mean']}  n {d['within_engine']['n_pairs']}")
print(f"  between-engine mean {d['between_engine_same_questions']['mean']}  "
      f"n {d['between_engine_same_questions']['n_pairs']}")
print(f"  gap {d['gap_within_minus_between']}")
print(f"  VERDICT: {d['verdict']}")
print(f"\ncompany level: {R['company_level']['companies']} companies, "
      f"{R['company_level']['invisible_on_every_engine']} invisible on every engine, "
      f"{R['company_level']['visible_some_engines_only']} visible on some engines only")
print("\ncitation mix per engine (vendor-owned share):")
for e in ENGINES:
    print(f"  {LABEL[e]:22} {pct(cit[e]['share'].get('vendor_owned'))} of {cit[e]['citations']} citations")
print(f"\nSerpApi calls consumed: {R['serpapi_calls_used_total']}")
print("wrote data/results.json")
