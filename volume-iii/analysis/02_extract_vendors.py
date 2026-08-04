#!/usr/bin/env python3
"""
Volume III, step 2: two-layer vendor extraction + citation classification.

Layer 1 (deterministic, authoritative for universe companies)
  Volume I / v4.6.1 matching rules, reimplemented exactly:
    - text normalised for NBSP, thin spaces, curly quotes and the dash family,
      then whitespace collapsed
    - word-boundary match
    - case-SENSITIVE when the brand is a single plain alphabetic word
      (so a company called Pitch does not match the ordinary verb)
    - case-insensitive when the brand carries a dot, digit, hyphen or space
    - hostname-level domain matching, multi-domain split on pipes and commas,
      subdomains count, near-misses do not

Layer 2 (LLM extractor) is run separately by 02b_llm_extract.py and merged here
if its output file exists. Layer 2 may only ADD out-of-universe vendors. Any
Layer 2 claim about a universe company is dropped unless Layer 1 also found the
string, so the LLM can never inflate a measured company's numbers.

Citation layer reuses Volume I's domain classification so the 77.4%
vendor-authored figure is comparable per engine.

Inputs   data/raw.csv, data/universe.csv, data/questions.csv,
         data/state-of-geo-2026/cited_source_domains_top100.csv,
         data/llm_vendors.json (optional)
Outputs  data/scored.csv, data/vendor_mentions.csv, data/citations.csv
"""
import csv, json, re, os, sys, collections

D = "data"
csv.field_size_limit(10_000_000)


# ------------------------------------------------------------------ matching
def norm(s):
    s = "" if s is None else str(s)
    s = re.sub(r"[     ]", " ", s)
    s = re.sub(r"[‘’‛]", "'", s)
    s = re.sub(r"[“”]", '"', s)
    s = re.sub(r"[‐‑‒–—―]", "-", s)
    return re.sub(r"\s+", " ", s).strip()


def name_re(brand, ignore_case):
    pat = "(^|[^A-Za-z0-9])" + re.escape(brand) + "([^A-Za-z0-9]|$)"
    return re.compile(pat, re.IGNORECASE if ignore_case else 0)


_RE_CACHE = {}


def named_in(text, brand):
    b = norm(brand)
    if not b:
        return False
    key = b
    if key not in _RE_CACHE:
        ambiguous = re.fullmatch(r"[A-Za-z]+", b) is not None
        _RE_CACHE[key] = name_re(b, not ambiguous)
    return _RE_CACHE[key].search(text) is not None


def host_of(u):
    m = re.match(r"^https?://([^/?#]+)", str(u or ""), re.I)
    if not m:
        return ""
    h = m.group(1).split("@")[-1].split(":")[0]
    return re.sub(r"^www\.", "", h, flags=re.I).lower()


# ------------------------------------------------------------------ universe
universe = list(csv.DictReader(open(f"{D}/universe.csv")))
questions = {q["question_id"]: q for q in csv.DictReader(open(f"{D}/questions.csv"))}

# canonical vendor name -> set of surface strings to match
surfaces = {}
company_domains = {}
measured = {}
for u in universe:
    co = norm(u["company"])
    if not co:
        continue
    s = surfaces.setdefault(co, set())
    s.add(co)
    for a in re.split(r"\s*,\s*", u.get("brand_aliases") or ""):
        a = norm(a)
        if a:
            s.add(a)
    hosts = [h for h in
             (re.sub(r"^https?://", "", x.strip(), flags=re.I).replace("www.", "").split("/")[0].lower()
              for x in re.split(r"[|,;\s]+", u.get("domain") or "") if x.strip())
             if h]
    company_domains.setdefault(co, set()).update(hosts)
    measured[co] = (u.get("measured_subject", "True") == "True")

# competitors named on any row are part of the matching universe
competitors_by_category = collections.defaultdict(set)
for u in universe:
    cat = norm(u["category"])
    for c in re.split(r"\s*,\s*", u.get("competitors") or ""):
        c = norm(c)
        if c:
            competitors_by_category[cat].add(c)
            surfaces.setdefault(c, set()).add(c)

UNIVERSE_NAMES = sorted(surfaces.keys(), key=len, reverse=True)


# ------------------------------------------------------------------ citations
# Volume I domain classification, reused verbatim where the domain appears in
# Volume I's top-100 table, then extended by rule.
vol1_type = {}
p = f"{D}/state-of-geo-2026/cited_source_domains_top100.csv"
if os.path.exists(p):
    for r in csv.DictReader(open(p)):
        vol1_type[r["domain"].lower()] = r["type"]

REVIEW = {"g2.com", "capterra.com", "trustradius.com", "getapp.com", "softwareadvice.com",
          "gartner.com", "peerspot.com", "trustpilot.com", "sourceforge.net", "slashdot.org",
          "producthunt.com", "saasworthy.com", "goodfirms.co", "crozdesk.com", "financesonline.com"}
COMMUNITY = {"reddit.com", "quora.com", "stackoverflow.com", "news.ycombinator.com",
             "stackexchange.com", "medium.com", "dev.to", "linkedin.com", "youtube.com",
             "x.com", "twitter.com", "facebook.com"}
EDITORIAL = {"forbes.com", "techcrunch.com", "cnet.com", "zdnet.com", "pcmag.com",
             "theverge.com", "businessinsider.com", "wired.com", "venturebeat.com",
             "nytimes.com", "wsj.com", "computerworld.com", "infoworld.com", "techradar.com"}
ANALYST = {"gartner.com", "forrester.com", "idc.com", "everestgrp.com", "isg-one.com"}


def registrable(host):
    """Second-level label, e.g. 'thoughtspot' from 'www.thoughtspot.com' or
    'help.thoughtspot.co.uk'. Good enough to match a hostname to a brand name."""
    parts = host.split(".")
    if len(parts) < 2:
        return host
    multi = {"co", "com", "net", "org", "ac", "gov"}
    if len(parts) >= 3 and parts[-2] in multi:
        return parts[-3]
    return parts[-2]


def brandkey(s):
    return re.sub(r"[^a-z0-9]", "", str(s or "").lower())


# Google AI Overviews responses carry thumbnail and favicon image URLs alongside
# the real source links. Left in, they were 62% of every "citation" attributed to
# that engine on the pilot data and would have destroyed the per-engine citation
# comparison. They are not citations and are dropped before anything is counted.
NOT_A_CITATION = ("gstatic.com", "googleusercontent.com", "ggpht.com",
                  "google.com/imgres", "schema.org", "w3.org")


def is_citation(host, url):
    if not host:
        return False
    if any(host == h or host.endswith("." + h) for h in
           ("gstatic.com", "googleusercontent.com", "ggpht.com")):
        return False
    if host.startswith("encrypted-tbn"):
        return False
    return True


def classify_domain(host, vendor_hosts, brand_keys):
    """Order matters. Volume I's own label wins wherever Volume I has one, which
    is what keeps the per-engine numbers comparable to Volume I. The well-known
    platform lists come next. The brand-name heuristic is ours and runs LAST, so
    it can never relabel a review platform or a community site as vendor-owned
    just because a vendor happens to share its name."""
    if not host:
        return "other"
    base = host
    # 1. an explicit domain belonging to a company in the study universe
    if any(base == h or base.endswith("." + h) for h in vendor_hosts):
        return "vendor_owned"
    # 2. Volume I's published classification, reused verbatim
    v1 = vol1_type.get(base)
    if v1:
        return {"vendor_authored": "vendor_owned", "review": "review_platform",
                "analyst": "analyst", "media": "editorial",
                "community": "community"}.get(v1, v1)
    # 3. well-known platforms
    for s, label in ((ANALYST, "analyst"), (REVIEW, "review_platform"),
                     (COMMUNITY, "community"), (EDITORIAL, "editorial")):
        if any(base == h or base.endswith("." + h) for h in s):
            return label
    # 4. the registrable label matches a vendor name in the study vocabulary.
    #    Volume I counts a citation as vendor-authored when the cited site belongs
    #    to a software vendor, not only to a company inside the measured universe.
    if brandkey(registrable(base)) in brand_keys:
        return "vendor_owned"
    return "other"


# all vendor-owned hosts across the whole study universe
ALL_VENDOR_HOSTS = set()
for hs in company_domains.values():
    ALL_VENDOR_HOSTS.update(hs)


# ------------------------------------------------------------------ layer 2
# surfaces already contains every universe company, its aliases and every
# competitor named on any row, so it is the full in-universe vocabulary.
BRAND_KEYS = {brandkey(n) for n in surfaces if len(brandkey(n)) >= 3}
BRAND_KEYS -= {"", "base", "pulse", "omni", "sigma", "fabric", "drip", "float",
               "concord", "juro", "robin", "envoy", "carta", "pulley"}
# short or dictionary-word brands are dropped from the DOMAIN test only: they
# would match unrelated sites. They are still matched in answer TEXT by the
# Layer 1 rules, which are case-sensitive for exactly this reason.

llm = {}
p = f"{D}/llm_vendors.json"
if os.path.exists(p):
    llm = json.load(open(p))
    print(f"Layer 2 present: {len(llm)} answers with LLM-extracted vendor lists")
else:
    print("Layer 2 absent (data/llm_vendors.json). Running Layer 1 only.")

for _vs in llm.values():
    for _v in _vs:
        k = brandkey(_v)
        if len(k) >= 5:
            BRAND_KEYS.add(k)
print(f"domain-test brand vocabulary: {len(BRAND_KEYS)} names")


# ------------------------------------------------------------------ main
rows = list(csv.DictReader(open(f"{D}/raw.csv")))
print(f"raw rows: {len(rows)}")

scored, mentions, citations = [], [], []
for r in rows:
    qid = r["question_id"]
    engine = r["engine"]
    rep = int(r.get("repeat_index") or 1)
    answer = norm(r.get("answer_text") or "")
    row_key = f"{qid}|{engine}|{rep}"

    l1 = set()
    if r.get("status") == "ok" and answer:
        for canon in UNIVERSE_NAMES:
            if any(named_in(answer, s) for s in surfaces[canon]):
                l1.add(canon)

    l2_extra = set()
    for v in llm.get(row_key, []):
        v = norm(v)
        if not v:
            continue
        canon = next((c for c in UNIVERSE_NAMES if c.lower() == v.lower()), None)
        if canon:
            # Layer 1 is authoritative for universe companies. Confirm by string.
            if canon in l1:
                continue
            if any(named_in(answer, s) for s in surfaces[canon]):
                l1.add(canon)
            continue
        l2_extra.add(v)

    raw_urls = [u.strip() for u in (r.get("cited_urls") or "").split("|") if u.strip()]
    urls, hosts = [], []
    dropped_assets = 0
    for u in raw_urls:
        h = host_of(u)
        if not is_citation(h, u):
            dropped_assets += 1
            continue
        urls.append(u)
        hosts.append(h)
    mix = collections.Counter()
    for h, u in zip(hosts, urls):
        if not h:
            continue
        t = classify_domain(h, ALL_VENDOR_HOSTS, BRAND_KEYS)
        mix[t] += 1
        citations.append({"question_id": qid, "engine": engine, "repeat_index": rep,
                          "url": u, "domain": h, "source_type": t})

    vendor_set = sorted(l1 | l2_extra)
    # Order vendors by where they first appear in the answer text. Engines list
    # their strongest recommendation first, so this makes a top-k truncation
    # meaningful and lets the length-matched control in the analysis compare
    # like with like when one engine names 5 vendors and another names 15.
    def _first_pos(v):
        best = len(answer) + 1
        for sfc in (surfaces.get(v) or {v}):
            b = norm(sfc)
            if not b:
                continue
            rx = _RE_CACHE.get(b)
            if rx is None:
                amb = re.fullmatch(r"[A-Za-z]+", b) is not None
                rx = _RE_CACHE[b] = name_re(b, not amb)
            m = rx.search(answer)
            if m and m.start() < best:
                best = m.start()
        return best
    vendor_order = sorted(vendor_set, key=lambda v: (_first_pos(v), v))
    scored.append({
        "run_id": r.get("run_id", ""),
        "ts": r.get("ts", ""),
        "category": r.get("category", ""),
        "question_id": qid,
        "question_shape": questions.get(qid, {}).get("question_shape", ""),
        "engine": engine,
        "model_id": r.get("model_id", ""),
        "repeat_index": rep,
        "status": r.get("status", ""),
        "answer_chars": len(answer),
        "n_vendors": len(vendor_set),
        "n_vendors_in_universe": len(l1),
        "layer2_present": row_key in llm,
        "vendor_set_json": json.dumps(vendor_set),
        "vendor_order_json": json.dumps(vendor_order),
        "n_citations": len(urls),
        "image_assets_dropped": dropped_assets,
        "cit_vendor_owned": mix.get("vendor_owned", 0),
        "cit_review_platform": mix.get("review_platform", 0),
        "cit_editorial": mix.get("editorial", 0),
        "cit_analyst": mix.get("analyst", 0),
        "cit_community": mix.get("community", 0),
        "cit_other": mix.get("other", 0),
        "serpapi_calls_used": r.get("serpapi_calls_used", 0),
        "latency_ms": r.get("latency_ms", 0),
    })
    for v in vendor_set:
        mentions.append({"question_id": qid, "category": r.get("category", ""),
                         "engine": engine, "repeat_index": rep, "vendor": v,
                         "in_universe": v in surfaces,
                         "measured_subject": measured.get(v, False)})

for name, data in (("scored.csv", scored), ("vendor_mentions.csv", mentions), ("citations.csv", citations)):
    if not data:
        print(f"WARNING: {name} is empty")
        continue
    with open(f"{D}/{name}", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(data[0].keys()))
        w.writeheader()
        w.writerows(data)
    print(f"{name}: {len(data)} rows")
