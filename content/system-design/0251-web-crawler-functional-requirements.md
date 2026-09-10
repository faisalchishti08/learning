---
card: system-design
gi: 251
slug: web-crawler-functional-requirements
title: Web Crawler — functional requirements
---

## 1. What it is

This page covers the **functional requirements** facet of the **Web Crawler** system-design case study — a system that starts from a set of seed URLs, downloads each page, extracts links from it, and repeats the process on those newly discovered links, building a large collection of crawled pages. Functional requirements are the concrete things the system must do, as opposed to how fast or reliable it must do them (a separate facet, [non-functional requirements](0252-web-crawler-non-functional-requirements.md)).

## 2. Why & when

Unlike the [URL Shortener](0224-url-shortener-functional-requirements.md), [Rate Limiter](0233-rate-limiter-functional-requirements.md), and [Pastebin](0242-pastebin-functional-requirements.md) case studies, a web crawler's "clients" are not external users making requests to the system — the system itself is the active agent, continuously discovering and fetching content from the wider internet. This changes what "functional requirements" even means here: the requirements describe the crawler's own behavior and the rules it must follow while operating, not an API contract for outside callers.

## 3. Core concept

Prioritize using **MoSCoW** (Must / Should / Could):

- **Must have:**
  - Given a set of seed URLs, fetch each page's content and extract every hyperlink it contains.
  - Add newly discovered links to a queue of URLs to crawl next, and continue the process across those links.
  - Avoid re-crawling the same URL repeatedly in an unbounded loop (deduplication).
  - Respect a target site's `robots.txt` rules — which paths the site's owner has disallowed crawlers from accessing.
- **Should have:**
  - Respect **politeness**: limit how frequently the crawler hits any single domain, to avoid overloading a target site's own servers.
  - Store crawled page content in a form other systems (like a search index) can later consume.
  - Support **prioritization**: crawl some URLs (e.g. from a high-value domain) before others.
- **Could have:**
  - Detect and skip **duplicate content** across different URLs (the same page reachable at multiple addresses).
  - Support recrawling a previously-crawled page after some time, to detect content changes.
  - Extract and follow links only within a configured scope (e.g. a specific set of domains, for a focused crawl).
- **Explicitly out of scope for this case study:**
  - Parsing or indexing the *meaning* of crawled content (that is a search-indexing system's job, consuming this crawler's output).
  - Rendering JavaScript-heavy pages that require a full browser engine to see their final content (a real, common crawler concern, but a distinct sub-problem kept out of scope here for focus).
  - Handling adversarial anti-crawling defenses (CAPTCHAs, IP-based blocking countermeasures).

## 4. Diagram

```
      +-----------------+
      |   Seed URLs       |
      +--------+---------+
               |
               v
      +------------------------------------------------------------+
      |                       Web Crawler System                     |
      |                                                                |
      |  fetch page -> extract links -> add new links to queue         |
      |       ^                                    |                    |
      |       |                                    v                    |
      |       +------------- crawl next URL from queue -----------------+
      |                                                                |
      |  "respect robots.txt" (must)                                    |
      |  "respect politeness / rate per domain" (should)                 |
      |  "avoid re-crawling the same URL" (must)                          |
      +------------------------------------------------------------+
               |
               v
      +-----------------+
      |  Crawled Page     |
      |  Storage           |
      |  (should)           |
      +-----------------+
```
*Caption: unlike the earlier case studies, there is no external "client" driving requests — the crawler itself is the active loop, continuously feeding its own queue from what it discovers.*

## 5. Runnable example

### Requirements list

```text
MUST HAVE
  FR-1: Given seed URLs, fetch each page and extract every hyperlink found
        in it.
  FR-2: Add newly discovered URLs to a crawl queue, and continue crawling
        from that queue.
  FR-3: Deduplicate - never crawl the same normalized URL more than once
        (within a given crawl run/policy).
  FR-4: Respect robots.txt - never fetch a path the target site has
        disallowed for crawlers.

SHOULD HAVE
  FR-5: Respect politeness - limit request rate to any single domain, so
        the crawler does not overload a target site's servers.
  FR-6: Store fetched page content in a form a downstream system (e.g. a
        search indexer) can consume.
  FR-7: Support URL prioritization - crawl some URLs ahead of others based
        on a configurable priority signal.

COULD HAVE
  FR-8: Detect duplicate content across different URLs (e.g. via a content
        hash) and avoid storing/processing true duplicates twice.
  FR-9: Support scheduled recrawling of previously-crawled pages to detect
        content changes over time.
  FR-10: Support scope restriction - only follow links within a configured
         set of domains, for a focused (not open-web) crawl.

OUT OF SCOPE
  - Parsing/indexing crawled content's meaning (a downstream system's job).
  - Rendering JavaScript-heavy pages via a full browser engine.
  - Handling adversarial anti-crawling defenses (CAPTCHAs, IP blocking).
```

## 6. Walkthrough

1. **FR-1 and FR-2 together define the crawler's fundamental self-feeding loop**: fetch a page, extract links, add those links back into the same queue the crawler is consuming from. This loop, not a create-then-retrieve pattern like the earlier three case studies, is the structural heart of this system — every other requirement modifies or constrains how this loop behaves.
2. **FR-3 (deduplication) exists because the self-feeding nature of FR-1/FR-2 makes infinite, wasteful re-crawling the default outcome without it** — two different pages linking to the same third page would otherwise queue that third page twice, and a cyclical link structure (page A links to B, B links back to A) could loop forever. This requirement is what makes the loop actually terminate (or at minimum, make bounded, useful progress) rather than spin indefinitely on already-seen content.
3. **FR-4 (respect robots.txt) is a hard requirement for a fundamentally different reason than any requirement in the earlier three case studies**: it is not about this system's own correctness or performance, but about **not overstepping the target sites' own stated boundaries** — a web crawler that ignores `robots.txt` is behaving as an unwelcome, potentially abusive actor toward every site it visits, which is why this sits in "must have," not "should have."
4. **FR-5 (politeness) has a similar external-courtesy motivation to FR-4**, but concerns *rate* rather than *scope* — a crawler that respects `robots.txt`'s disallowed paths but still hammers a small site's server with hundreds of requests per second can still effectively cause harm (a self-inflicted denial-of-service on the target), which is exactly what this requirement guards against.
5. **FR-7 (prioritization) directly affects the [deep-dive facet](0257-web-crawler-deep-dive-url-frontier-dedup-politeness.md)'s design of the crawl queue** — a plain FIFO queue treats every discovered URL equally, but a prioritized queue (a URL frontier, in crawler terminology) lets the system crawl higher-value or more time-sensitive content sooner, a meaningful architectural difference this requirement drives directly.

## 7. Gotchas & takeaways

> **Gotcha:** FR-4 (robots.txt) is easy to treat as a minor technical checkbox, but it carries real legal and ethical weight — many jurisdictions and site operators treat `robots.txt` violations, combined with server overload from FR-5 violations, as grounds for legal action or IP-level blocking. Treat this requirement with the same seriousness as a hard security or compliance requirement, not as an optional nicety.

- FR-1 through FR-4 define the non-negotiable core: a self-feeding fetch-and-extract loop that terminates sensibly (FR-3) and respects the target sites it visits (FR-4) — every other requirement builds on top of this working, well-behaved core.
- This case study's requirements describe the crawler's own operational behavior, not an external API contract — a structural difference from the [URL Shortener](0224-url-shortener-functional-requirements.md), [Rate Limiter](0233-rate-limiter-functional-requirements.md), and [Pastebin](0242-pastebin-functional-requirements.md) case studies worth remembering as you read the rest of this case study's facets.
- Explicitly listing JavaScript rendering and anti-crawling countermeasures as out of scope keeps this case study focused on the crawl-loop, deduplication, and politeness problems that are genuinely central to "how does a web crawler work," without ballooning into a much larger, less focused system.
- See [Web Crawler — non-functional requirements](0252-web-crawler-non-functional-requirements.md) next for the scale, latency, and politeness-related quality targets these functional requirements must be delivered under.
