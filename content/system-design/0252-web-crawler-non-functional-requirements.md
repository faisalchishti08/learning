---
card: system-design
gi: 252
slug: web-crawler-non-functional-requirements
title: Web Crawler — non-functional requirements
---

## 1. What it is

This page covers the **non-functional requirements (NFRs)** facet of the **Web Crawler** case study — the quality targets (scale, throughput, politeness limits, fault tolerance) the system must meet, as opposed to what it must do functionally (see [functional requirements](0251-web-crawler-functional-requirements.md)).

## 2. Why & when

The earlier three case studies' NFRs centered on serving external client requests quickly and reliably. A web crawler's NFRs center on something different: how much of the web it can process in a given time, how considerately it treats the millions of independent servers it interacts with, and how it tolerates the inherent unreliability of the open internet (slow sites, broken links, servers that never respond). Define these right after functional requirements, since they directly shape the crawl-queue and fetching architecture.

## 3. Core concept

- **Throughput, not latency, is the primary scale metric.** Unlike a user waiting on a single request, nobody is waiting synchronously on any single page fetch — what matters is the crawler's aggregate throughput: how many pages it can fetch and process per second, system-wide.
- **Per-domain rate limits (politeness), not a single system-wide rate.** The crawler's own total throughput can be very high, but its request rate to any *one* domain must stay low and considerate — this is a fundamentally different shape of rate limit than the [Rate Limiter](0234-rate-limiter-non-functional-requirements.md) case study's per-client limits, since here the crawler is the single client being limited against many different targets, rather than many clients being limited against one system.
- **Fault tolerance against an unreliable, adversarial-by-default internet.** Target servers will time out, return malformed HTML, redirect in loops, or serve enormous unexpected payloads — the crawler must tolerate all of this gracefully for any single URL without that URL's failure affecting the crawl of any other URL.
- **Freshness, for recrawled content.** If FR-9 (scheduled recrawling) is in scope, there is an implicit staleness tolerance — how out of date can the crawler's stored copy of a page be before it needs to be refetched — that trades off directly against total crawl capacity, since recrawling existing pages competes with discovering new ones for the same fetch budget.
- **Storage scale for crawled content**, similar in spirit to Pastebin's storage-volume concern, but at a scale several orders of magnitude larger — a broad crawl can accumulate a very large volume of page content over time.

## 4. Diagram

```
                    STRICT <-----------------------------> RELAXED

   THROUGHPUT   |  aggregate pages/sec must be high      |
                |  across the WHOLE crawl                   |

   POLITENESS   |  request rate to any SINGLE domain        |
                |  must stay low, regardless of overall        |
                |  system throughput (strict per-domain,         |
                |  relaxed in aggregate)                           |

   FAULT        |  one bad/slow/malicious target server           |
   TOLERANCE    |  must never block or slow the crawl of ANY        |
                |  other, unrelated URL                               |

   FRESHNESS    |                                    | a page being
                |                                    | somewhat stale
                |                                    | before recrawl is
                |                                    | acceptable (relaxed,
                |                                    | if FR-9 in scope)
```
*Caption: throughput is strict in aggregate but deliberately capped per-domain — this dual nature (fast overall, gentle per-target) is the defining tension this whole case study's architecture must resolve.*

## 5. Runnable example

### Measurable NFR targets

```text
THROUGHPUT (aggregate)
  NFR-1: Sustain at least 1,000 pages fetched per second, system-wide,
         across all domains combined.

POLITENESS (per-domain)
  NFR-2: No more than 1 request per domain every 2 seconds, by default
         (configurable per domain, and overridden by that domain's own
         robots.txt crawl-delay directive if it specifies a stricter one).

FAULT TOLERANCE
  NFR-3: A single URL fetch that times out, errors, or returns malformed
         content must fail in isolation - within 1-2 seconds of added
         latency for that URL specifically - with zero impact on the
         crawl progress of any other URL.
  NFR-4: The crawler must survive and continue crawling through individual
         worker process/machine failures - no single machine's failure
         should halt the overall crawl.

FRESHNESS (if FR-9 in scope)
  NFR-5: A previously-crawled page should be recrawled within 7 days by
         default for a "regular" priority page (shorter for high-priority
         pages, longer or never for low-priority ones).

STORAGE
  NFR-6: Design for accumulating crawled content at a rate proportional
         to NFR-1's throughput - see capacity estimation for the
         resulting concrete storage projection.
```

## 6. Walkthrough

1. **NFR-1 (1,000 pages/sec aggregate) is a genuinely large number that immediately rules out a single-machine, sequential fetch-one-page-at-a-time design** — this is the number that most directly justifies a horizontally distributed architecture with many parallel fetcher workers, covered in [high-level architecture](0255-web-crawler-high-level-architecture.md).
2. **NFR-2 (politeness, per-domain) is in direct tension with NFR-1** — the crawler must be fast in aggregate while being deliberately slow against any single target. This tension is precisely why a crawler cannot simply be "many parallel workers pulling from one shared queue" without additional coordination: without per-domain rate awareness, many workers could easily overwhelm one domain simultaneously purely by chance, even while overall throughput stays reasonable.
3. **NFR-3 (per-URL fault isolation) reflects that the internet is fundamentally unreliable and only partially cooperative** — unlike the earlier three case studies, where "the database" or "the cache" was infrastructure the system's own operators controlled and could reasonably assume was mostly healthy, a web crawler's dependencies are millions of independent servers with no such assumption possible. A slow or hanging server for one URL must never block worker capacity meant for every other URL — this pushes the design toward strict, short timeouts and fully asynchronous, per-URL failure handling.
4. **NFR-4 (worker fault tolerance) matters more here than in the earlier case studies specifically because a crawl can run for a very long time (hours to days) and process an enormous number of URLs** — losing a worker machine partway through should lose, at most, the in-flight work that specific machine was doing, not derail the entire multi-day crawl.
5. **NFR-5 (freshness, if recrawling is in scope) introduces a genuine resource-allocation tradeoff** that did not exist in any earlier case study: every fetch spent recrawling a known page is a fetch not spent discovering a new one, within the same NFR-1 throughput budget — this tradeoff becomes a real, explicit design decision in [scaling & tradeoffs](0258-web-crawler-scaling-tradeoffs.md).

## 7. Gotchas & takeaways

> **Gotcha:** it is tempting to treat NFR-1 (aggregate throughput) as the headline number and NFR-2 (per-domain politeness) as a secondary constraint to fit in afterward — but designing the architecture around NFR-1 first, and then trying to retrofit politeness, tends to produce a system where many parallel workers accidentally converge on the same popular domain simultaneously. Treat per-domain politeness as a first-class architectural constraint from the start, not an afterthought layered on top.

- Throughput here is an aggregate, system-wide number — very different in character from the per-request latency targets that dominated the earlier three case studies' NFRs.
- The tension between high aggregate throughput (NFR-1) and strict per-domain politeness (NFR-2) is the single most important relationship on this page — it is what the [deep-dive facet](0257-web-crawler-deep-dive-url-frontier-dedup-politeness.md)'s URL frontier design exists specifically to resolve.
- Fault tolerance here is about isolating failures from an inherently unreliable, uncooperative internet (NFR-3), not just about the crawler's own infrastructure staying up (NFR-4) — both matter, but for different reasons.
- See [Web Crawler — capacity estimation](0253-web-crawler-capacity-estimation.md) next, where NFR-1's throughput target and NFR-6's storage implication get turned into concrete numbers for workers, bandwidth, and storage.
