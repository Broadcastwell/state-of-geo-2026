# The 2026 State of Generative Engine Optimization — Open Datasets

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.21537014.svg)](https://doi.org/10.5281/zenodo.21537014)

Supporting data for [The 2026 State of Generative Engine Optimization](https://broadcastwell.com/state-of-geo), published by Broadcastwell Research, v1.0, July 2026.

## What this is

Between 18 and 23 July 2026 we ran 10 standardized buyer questions through a frontier large language model with live web search enabled, for each of 85 B2B software companies across 61 categories. Each answer was scored on two binary outcomes: whether the company was named, and whether its domain was cited as a source. Every cited URL was logged.

| Metric | Value |
|---|---|
| Scored AI answers | 860 |
| Companies measured | 85 |
| Software categories | 61 |
| Source citations traced | 5,160 |
| Unique domains cited | 1,753 |
| Collection window | 2026-07-18 to 2026-07-23 |

## Headline findings

- The median company is named in 20% of AI answers for its own category. 35% are named in zero.

- AI answers are winner-take-most: the median category leader appears in 80% of its category's answers.

- Among the 100 most-cited domains, 77.4% of citations are vendor-authored content. Review platforms 10.2%, independent media 6.5%, analyst firms 5.9%. Community sources (Reddit, Quora, Stack Overflow) account for 0.0% of all 5,160 citations.

- The evidence layer is fragmented: the top 10 domains hold only 12% of citations, and 56% of cited domains appear exactly once.

- The average answer names just 2.05 vendors.

## Files

| File | Rows | Columns |
|---|---|---|
| most_named_brands_top50.csv | 50 | brand, mentions, category_sweeps_present, share_of_all_answers_pct |
| cited_source_domains_top100.csv | 100 | rank, domain, citations, type |
| company_visibility_anonymized.csv | 85 | company_id, segment, answers_sampled, named_pct, cited_pct |

### Data dictionary

most_named_brands_top50.csv — every brand named across the 860 answers, ranked by total mentions. category_sweeps_present is the number of distinct category sweeps in which the brand appeared at least once.

cited_source_domains_top100.csv — the 100 most-cited domains. type is a hand-assigned classification: vendor_authored, review_platform, analyst, independent_media, community, wikipedia, social.

company_visibility_anonymized.csv — per-company results. Company identities are withheld and replaced with C01–C85. named_pct is the share of that company's 10 answers in which it was named; cited_pct the share in which its domain was cited as a source.

## Methodology

Engine. One frontier large language model (Anthropic Claude Sonnet) with live web search enabled, so answers reflect real-time retrieval rather than training data alone.

Prompts. 10 standardized buyer questions per category: a mix of best-of, direct comparison, and use-case questions, phrased the way a buyer types them.

Sample. 85 B2B software companies across 61 categories, skewing toward challenger brands. Category leaders enter the data through mentions, not through selection.

Classification. The 100 most-cited domains (36% of all citations) were classified by hand.

## Limitations

- Single engine, single run per prompt. AI answers vary run to run; repeated runs of the same question can return different leaders. All figures are point-in-time estimates, not fixed rankings.

- The sample skews toward challenger brands, which lowers average named rates relative to a random sample of all vendors.

- Segment sizes vary. Percentages are rounded.

- Company identities are withheld. Aggregates and brand-level mentions of widely known market leaders are published; per-company results are anonymized.

## Citation

Broadcastwell Research (2026). The 2026 State of Generative Engine Optimization, v1.0. Zenodo. https://doi.org/10.5281/zenodo.21537014

```bibtex
@report{broadcastwell2026geo,
  title   = {The 2026 State of Generative Engine Optimization},
  author  = {{Broadcastwell Research}},
  year    = {2026},
  version = {1.0},
  doi     = {10.5281/zenodo.21537014},
  url     = {https://broadcastwell.com/state-of-geo}
```

## License

Data released under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Reuse freely with attribution.

## Roadmap

A Q4 2026 multi-engine edition will add ChatGPT, Perplexity, Gemini and Google AI Overviews. Watch this repository for the release.

---

Broadcastwell LLC · Indiana, USA · [hello@broadcastwell.com](mailto:hello@broadcastwell.com)
