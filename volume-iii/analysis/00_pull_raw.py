#!/usr/bin/env python3
"""
Pull vol3_raw out of an oversized n8n get_execution tool-result file and write
data/raw.csv. Usage: 00_pull_raw.py <tool-result-file.json>

Why this exists: this container's network egress is allowlisted and does not
reach the n8n instance or Google Drive, and the device bridge has no connected
folder. The one path that carries the whole dataset across is n8n's execution
data, which the harness persists to disk when it is too large to inline.
"""
import json, sys, csv, os

FIELDS = ["run_id", "ts", "category", "question_id", "question_text", "engine",
          "model_id", "repeat_index", "status", "answer_text", "cited_urls",
          "latency_ms", "serpapi_calls_used", "dedup_key"]

src = sys.argv[1]
d = json.load(open(src))
run = d["data"]["resultData"]["runData"]
node = sys.argv[2] if len(sys.argv) > 2 else "Read vol3_raw"
items = run[node][0]["data"]["main"][0]
rows = [i["json"] for i in items]
print(f"{len(rows)} rows from {node}")

os.makedirs("data", exist_ok=True)

# Deduplicate on the collection key, keeping the EARLIEST answer.
# Concurrent scheduled runs briefly collided on the same batch before the
# slicing fix, so a small number of triples were collected twice. Keeping the
# first observation is the only rule that does not let a later, luckier answer
# be chosen after the fact.
def rank(r):
    """Lower sorts first and wins. A real answer always beats a billing error for
    the same triple, because an api_error row is a failed attempt that was later
    retried, not an observation. Among rows of equal standing the EARLIEST is
    kept, so a later luckier answer can never be cherry-picked after the fact."""
    return (0 if r.get("status") in ("ok", "no_aio") else 1, str(r.get("ts", "")))


best = {}
for r in rows:
    k = (r.get("question_id"), r.get("engine"), str(r.get("repeat_index")))
    prev = best.get(k)
    if prev is None or rank(r) < rank(prev):
        best[k] = r
out = [{f: best[k].get(f, "") for f in FIELDS} for k in sorted(best)]

with open("data/raw.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=FIELDS)
    w.writeheader()
    w.writerows(out)
print(f"wrote data/raw.csv with {len(out)} rows")

import collections
print("status:", collections.Counter(r["status"] for r in out))
print("engine:", collections.Counter(r["engine"] for r in out))
print("repeat:", collections.Counter(str(r["repeat_index"]) for r in out))
blank = sum(1 for r in out if r["status"] == "ok" and not str(r["answer_text"]).strip())
print("ok rows with EMPTY answer_text:", blank)
nocite = sum(1 for r in out if r["status"] == "ok" and not str(r["cited_urls"]).strip())
print("ok rows with NO citations:", nocite)
dups = len(rows) - len(out)
print("duplicate rows dropped:", dups)
