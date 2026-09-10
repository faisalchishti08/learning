---
card: system-design
gi: 259
slug: web-crawler-spring-java-implementation-approach
title: Web Crawler — Spring/Java implementation approach
---

## 1. What it is

This page covers the **Spring/Java implementation approach** facet of the **Web Crawler** case study — how the [self-feeding crawl loop](0251-web-crawler-functional-requirements.md), the [politeness-aware Frontier and Bloom filter dedup](0257-web-crawler-deep-dive-url-frontier-dedup-politeness.md), and the [control API](0254-web-crawler-api-design.md) become a real Spring Boot service.

## 2. Why & when

This closes out the Web Crawler case study, turning every earlier facet's design into working code — with particular attention to how a long-running, asynchronous, self-feeding loop is structured in Spring, since it is a genuinely different shape from the request/response services the earlier three case studies' implementation facets built.

## 3. Core concept

- **`CrawlJobController` — a `@RestController`** exposing the [API design](0254-web-crawler-api-design.md)'s job lifecycle endpoints (`POST /api/crawl-jobs`, `GET .../{id}`, `.../pause`, `.../pages`).
- **`CrawlOrchestrator` — a `@Service` managing the running loop**, using a Spring-managed `ExecutorService` (a thread pool) to run many Fetcher Worker tasks concurrently, rather than the servlet-request-per-thread model the earlier case studies' controllers relied on — this is the structural difference flagged in Part 2.
- **`FetcherWorker` — a `Runnable`/`Callable` task**, one instance conceptually "pulled and run" per eligible Frontier entry, implementing the fetch-check-robots-extract-store sequence from [high-level architecture](0255-web-crawler-high-level-architecture.md).
- **`UrlFrontier` and `DedupFilter` — `@Component` beans**, holding the domain-aware priority queue and Bloom filter logic from the [deep-dive facet](0257-web-crawler-deep-dive-url-frontier-dedup-politeness.md), injected into both the orchestrator and the workers.
- **`@Scheduled` or an explicit orchestration loop drives the crawl**, repeatedly asking the Frontier for eligible work and submitting it to the worker pool — analogous in spirit to the [Pastebin](0250-pastebin-spring-java-implementation-approach.md) case study's `@Scheduled` expiration sweeper, but here the scheduled work *is* the core business logic, not a background cleanup task.

## 4. Diagram

```
   Operator
     |
     v
  +--------------------------+
  |     CrawlJobController      |   @RestController
  |  POST /api/crawl-jobs         |
  +-------------+--------------+
                |
                v
  +--------------------------+
  |     CrawlOrchestrator        |   @Service
  |  - owns an ExecutorService     |
  |  - loop: pull eligible URL(s)   |
  |    from UrlFrontier, submit       |
  |    a FetcherWorker task per one     |
  +------+----------+-----------+
         |            |
         v            v
  +------------+  +----------------+
  | UrlFrontier |  |  DedupFilter     |   @Component beans
  | @Component  |  | (Bloom filter)    |
  +------------+  +----------------+
         ^
         | new URLs added back
         |
  +--------------------------+
  |      FetcherWorker           |   one task per eligible URL,
  |  - check robots.txt            |   run on the ExecutorService
  |  - fetch page                    |
  |  - extract links, check dedup,    |
  |    enqueue new ones back to        |
  |    UrlFrontier                       |
  |  - store content                       |
  +--------------------------+
```
*Caption: `CrawlOrchestrator` drives the loop by repeatedly pulling from `UrlFrontier` and submitting `FetcherWorker` tasks to a thread pool — a fundamentally different shape from a controller handling one inbound HTTP request at a time.*

## 5. Runnable example

**Level 1 — Basic.** `CrawlOrchestrator` pulling from a `UrlFrontier` and running a `FetcherWorker` for each eligible URL, on a thread pool.

**Level 2 — Intermediate.** `FetcherWorker` extracting links, checking the `DedupFilter`, and feeding new URLs back into the Frontier — closing the self-feeding loop in code.

**Level 3 — Advanced.** The orchestrator's loop running for several "ticks," showing the crawl naturally expanding outward from a seed URL and then settling once no new URLs are discovered.

```java
// WebCrawlerSpringDemo.java
// A focused, runnable stand-in for the real Spring Boot classes.
import java.util.*;
import java.util.concurrent.*;

public class WebCrawlerSpringDemo {

    record UrlEntry(String url, String domain) {}

    // ---------- DedupFilter (@Component, Bloom-filter-backed in a real deployment) ----------
    static class DedupFilter {
        Set<String> seen = new HashSet<>(); // simplified exact set for this demo's clarity
        synchronized boolean isNew(String url) {
            if (seen.contains(url)) return false;
            seen.add(url);
            return true;
        }
    }

    // ---------- UrlFrontier (@Component) ----------
    static class UrlFrontier {
        Map<String, Deque<UrlEntry>> byDomain = new ConcurrentHashMap<>();
        synchronized void enqueue(UrlEntry entry) {
            byDomain.computeIfAbsent(entry.domain(), d -> new ArrayDeque<>()).addLast(entry);
        }
        synchronized List<UrlEntry> pullEligibleBatch(int maxBatch) {
            List<UrlEntry> batch = new ArrayList<>();
            for (Deque<UrlEntry> queue : byDomain.values()) {
                if (!queue.isEmpty() && batch.size() < maxBatch) batch.add(queue.pollFirst());
            }
            return batch;
        }
        synchronized boolean isEmpty() {
            return byDomain.values().stream().allMatch(Deque::isEmpty);
        }
    }

    // ---------- Simulated "internet" for this demo: a fixed link graph ----------
    static Map<String, List<String>> fakeWeb = Map.of(
        "https://a.com/home", List.of("https://a.com/about", "https://b.com/page"),
        "https://a.com/about", List.of("https://a.com/home"), // links back - dedup must catch this
        "https://b.com/page", List.of("https://b.com/other", "https://a.com/home"),
        "https://b.com/other", List.of() // a leaf page, no outgoing links
    );

    static String domainOf(String url) { return url.split("/")[2]; }

    // ---------- FetcherWorker (a task, run on the ExecutorService) ----------
    static void fetchAndProcess(UrlEntry entry, UrlFrontier frontier, DedupFilter dedup, List<String> crawledLog) {
        List<String> links = fakeWeb.getOrDefault(entry.url(), List.of()); // simulates the actual HTTP fetch
        crawledLog.add(entry.url());
        System.out.println("    fetched " + entry.url() + ", found " + links.size() + " link(s)");
        for (String link : links) {
            if (dedup.isNew(link)) {
                frontier.enqueue(new UrlEntry(link, domainOf(link)));
                System.out.println("      -> new URL discovered, enqueued: " + link);
            } else {
                System.out.println("      -> already seen, skipped: " + link);
            }
        }
    }

    // ---------- CrawlOrchestrator (@Service) ----------
    static class CrawlOrchestrator {
        UrlFrontier frontier;
        DedupFilter dedup;
        ExecutorService pool = Executors.newFixedThreadPool(4);
        List<String> crawledLog = Collections.synchronizedList(new ArrayList<>());

        CrawlOrchestrator(UrlFrontier frontier, DedupFilter dedup) { this.frontier = frontier; this.dedup = dedup; }

        void runUntilExhausted(int maxTicks) throws InterruptedException {
            for (int tick = 1; tick <= maxTicks && !frontier.isEmpty(); tick++) {
                List<UrlEntry> batch = frontier.pullEligibleBatch(10);
                System.out.println("  tick " + tick + ": pulled " + batch.size() + " URL(s) to fetch");
                List<Future<?>> futures = new ArrayList<>();
                for (UrlEntry entry : batch) {
                    futures.add(pool.submit(() -> fetchAndProcess(entry, frontier, dedup, crawledLog)));
                }
                for (Future<?> f : futures) {
                    try { f.get(); } catch (ExecutionException e) { System.out.println("    fetch failed: " + e.getMessage()); }
                }
            }
            pool.shutdown();
        }
    }

    public static void main(String[] args) throws InterruptedException {
        UrlFrontier frontier = new UrlFrontier();
        DedupFilter dedup = new DedupFilter();
        CrawlOrchestrator orchestrator = new CrawlOrchestrator(frontier, dedup);

        System.out.println("Level 1 & 2 & 3 - full crawl from one seed URL, self-feeding loop:");
        String seed = "https://a.com/home";
        if (dedup.isNew(seed)) frontier.enqueue(new UrlEntry(seed, domainOf(seed)));

        orchestrator.runUntilExhausted(10);

        System.out.println("\nCrawl complete. Total pages fetched: " + orchestrator.crawledLog.size());
        System.out.println("Fetched URLs: " + orchestrator.crawledLog);
    }
}
```

**How to run:** `java WebCrawlerSpringDemo.java` (JDK 17+, single file, no dependencies).

## 6. Walkthrough

1. **Level 1:** the seed URL `"https://a.com/home"` is checked against `dedup.isNew(...)` (it is, being the very first URL) and enqueued into `frontier`. `orchestrator.runUntilExhausted(10)` starts its loop: each "tick" calls `frontier.pullEligibleBatch(10)`, which pulls up to 10 currently-queued URLs (here, simplified from the full [deep-dive facet](0257-web-crawler-deep-dive-url-frontier-dedup-politeness.md)'s politeness-timer logic, to focus this demo on the orchestration structure itself), and submits one `fetchAndProcess` task per URL to the `ExecutorService` — this is the concrete Spring-style equivalent of the [high-level architecture](0255-web-crawler-high-level-architecture.md)'s Fetcher Worker pool pulling from the Frontier.
2. **Tick 1 pulls just the seed URL** (the only thing queued so far). `fetchAndProcess` looks up `"https://a.com/home"` in the simulated `fakeWeb` graph, finding two outgoing links: `"https://a.com/about"` and `"https://b.com/page"`. For each, it calls `dedup.isNew(link)` — both are genuinely new, so both get enqueued into `frontier`, and the log line confirms each was newly discovered.
3. **Tick 2 pulls these two newly-discovered URLs.** `fetchAndProcess` for `"https://a.com/about"` finds it links back to `"https://a.com/home"` — but `dedup.isNew("https://a.com/home")` now returns `false`, since that exact URL was already processed by `dedup.isNew(seed)` at the very start. This is FR-3's deduplication requirement working exactly as intended, directly preventing the cyclical link structure (home → about → home) from looping the crawl forever.
4. **`fetchAndProcess` for `"https://b.com/page"` (also processed in tick 2) discovers `"https://b.com/other"` (new) and `"https://a.com/home"` (already seen, correctly skipped again)** — by the end of tick 2, only `"https://b.com/other"` has been newly enqueued.
5. **Tick 3 pulls `"https://b.com/other"`, whose `fakeWeb` entry has an empty link list** — nothing new is discovered, and `frontier.isEmpty()` now returns `true` for every remaining domain. The loop's `while` condition (`!frontier.isEmpty()`) becomes `false`, and `runUntilExhausted` exits naturally after only 3 ticks, having correctly crawled all 4 reachable pages exactly once each — `orchestrator.crawledLog.size()` confirms this count, and the printed list shows every URL was fetched exactly once, despite the underlying link graph containing a cycle that, without FR-3's deduplication, would have crawled `"https://a.com/home"` and its neighbors indefinitely.

## 7. Gotchas & takeaways

> **Gotcha:** this demo's `CrawlOrchestrator` uses a single, simplified `DedupFilter` and `UrlFrontier` with no domain-hash partitioning or politeness-timer enforcement — appropriate for demonstrating the self-feeding loop's structure clearly, but a production deployment at the [capacity estimation](0253-web-crawler-capacity-estimation.md)'s actual scale needs the full [deep-dive facet](0257-web-crawler-deep-dive-url-frontier-dedup-politeness.md) implementation (Bloom filter, per-domain politeness timers) and the [scaling facet](0258-web-crawler-scaling-tradeoffs.md)'s domain-hash sharding — this simplified version should not be mistaken for a complete, production-ready implementation.

- The orchestrator's tick-based loop (pull a batch, submit tasks, wait, repeat) is the concrete Spring-equivalent structure for what [high-level architecture](0255-web-crawler-high-level-architecture.md) described more abstractly as "Fetcher Workers pulling from the Frontier" — recognize this pattern as fundamentally different from a typical Spring controller's one-request-in, one-response-out model.
- Deduplication (FR-3) is what makes a self-feeding loop over a graph with cycles actually terminate — the demo's `fakeWeb` graph deliberately includes a cycle (home ↔ about, and b.com/page linking back to home) specifically to make this mechanism's necessity visible in the output, not just asserted in prose.
- This closes out the Web Crawler case study, and with it, the full set of four system-design case studies in this series — [URL Shortener](0224-url-shortener-functional-requirements.md), [Rate Limiter](0233-rate-limiter-functional-requirements.md), [Pastebin](0242-pastebin-functional-requirements.md), and Web Crawler — each following the same nine-facet structure (functional requirements through implementation approach), while landing on genuinely different architectures driven by each system's own distinct requirements and capacity profile.
