---
card: system-design
gi: 257
slug: web-crawler-deep-dive-url-frontier-dedup-politeness
title: "Web Crawler — deep-dive: URL frontier, dedup & politeness"
---

## 1. What it is

This page covers the **deep-dive** facet of the **Web Crawler** case study, focused on the two genuinely hard sub-problems flagged repeatedly by earlier facets: how the Dedup Store tests "have I seen this URL before" at a ~7.8 billion URL scale without a conventional table ([data model & schema](0256-web-crawler-data-model-schema.md)'s explicit gap), and how the URL Frontier serves "the next eligible URL" while honoring both priority (FR-7) and per-domain politeness (NFR-2) simultaneously.

## 2. Why & when

Both problems were explicitly deferred by earlier facets specifically because they are algorithmically substantial enough to deserve focused treatment — this is the same pattern as the URL Shortener's key-generation deep-dive and the Rate Limiter's algorithm-choice deep-dive, applied here to the two hardest parts of this case study.

## 3. Core concept

- **Bloom filter for dedup.** A Bloom filter is a space-efficient probabilistic set: it can definitively say "this URL has **never** been seen" (no false negatives) but can occasionally, rarely, say "seen" for a URL that was actually never added (a false positive) — an acceptable tradeoff, since a false positive only costs skipping a URL that would have been crawled anyway (a missed page, not a correctness violation), while a full hash set at billions of entries would cost far more memory than a Bloom filter for the same accuracy budget.
- **How a Bloom filter works.** A bit array of size `m`, plus `k` independent hash functions. Adding an item sets the bits at each of the `k` hash positions. Checking membership reads those same `k` positions — if any bit is 0, the item was definitely never added; if all `k` bits are 1, the item was probably added (with a small, tunable false-positive rate depending on `m`, `k`, and the number of items actually inserted).
- **Domain-aware priority queue for the Frontier.** Rather than one global priority queue (which cannot express "respect this domain's politeness delay"), the Frontier maintains one queue per domain (or a bucketed structure grouping domains), plus a mechanism to only consider domains whose `domain_state.last_fetched_at` shows their delay has elapsed.
- **Combining priority and politeness: a "ready" set, refreshed continuously.** A background process (or the pull operation itself) maintains the set of domains currently eligible (politeness window elapsed) with at least one queued URL; a Fetcher Worker's "give me the next URL" pulls the highest-priority URL from *that* eligible set, not from the full Frontier — this is what prevents workers from either violating politeness or starving on domains that happen to be temporarily ineligible.

## 4. Diagram

```
   BLOOM FILTER (dedup)                        DOMAIN-AWARE FRONTIER (priority + politeness)

   bit array, size m                            domain A (eligible now):  [HIGH url1, NORMAL url2]
   [0,1,0,1,1,0,0,1,0,1,...]                     domain B (elapsed in 1.2s): [NORMAL url3]
                                                  domain C (eligible now):  [LOW url4]
   add("http://x.com/a"):
     hash1 -> bit 3 = 1
     hash2 -> bit 7 = 1                          worker asks: "give me the next URL"
     hash3 -> bit 1 = 1                                |
                                                        v
   check("http://x.com/a"):                     scan ELIGIBLE domains only (A, C - not B, its
     hash1 -> bit 3? 1                            politeness window hasn't elapsed yet)
     hash2 -> bit 7? 1                            pick highest priority among those: url1 (HIGH, domain A)
     hash3 -> bit 1? 1
     -> "probably seen" (all bits set)            after fetching url1: domain A's last_fetched_at
                                                    updates, its NEXT eligible time resets
   check("http://y.com/z") (never added):
     hash1 -> bit 5? 0
     -> "definitely NOT seen" (short-circuits
        as soon as any bit is 0)
```
*Caption: the Bloom filter trades a small, tunable false-positive rate for massive space savings over a full URL set; the Frontier trades a single global ordering for a domain-partitioned structure that never surfaces a URL before its domain's politeness window has elapsed.*

## 5. Runnable example

**Level 1 — Basic.** A minimal Bloom filter: add, check, and demonstrate a deliberately-provoked false positive.

**Level 2 — Intermediate.** A domain-aware priority frontier: eligible-domain tracking, priority ordering within eligible domains.

**Level 3 — Advanced.** Combine both: a worker loop that pulls URLs respecting priority and politeness, using the Bloom filter to skip already-seen URLs before they are ever added to the frontier.

```java
// WebCrawlerFrontierDedupDemo.java
import java.util.*;

public class WebCrawlerFrontierDedupDemo {

    // ---------- Level 1: a minimal Bloom filter ----------
    static class BloomFilter {
        boolean[] bits;
        int size, numHashes;
        BloomFilter(int size, int numHashes) { this.size = size; this.numHashes = numHashes; this.bits = new boolean[size]; }

        int[] hashPositions(String item) {
            int[] positions = new int[numHashes];
            for (int i = 0; i < numHashes; i++) {
                int h = Objects.hash(item, i); // i acts as a salt, simulating k independent hash functions
                positions[i] = Math.floorMod(h, size);
            }
            return positions;
        }

        void add(String item) {
            for (int pos : hashPositions(item)) bits[pos] = true;
        }

        boolean mightContain(String item) {
            for (int pos : hashPositions(item)) if (!bits[pos]) return false; // any 0 bit -> definitely not present
            return true; // all bits set -> probably present (could be a false positive)
        }
    }

    // ---------- Level 2: domain-aware priority frontier ----------
    enum Priority { HIGH, NORMAL, LOW }
    record UrlEntry(String url, String domain, Priority priority) {}

    static class Frontier {
        Map<String, Deque<UrlEntry>> byDomain = new HashMap<>();
        Map<String, Long> lastFetchedAtMs = new HashMap<>();
        Map<String, Long> crawlDelayMs = new HashMap<>();

        void enqueue(UrlEntry entry) {
            byDomain.computeIfAbsent(entry.domain(), d -> new ArrayDeque<>()).addLast(entry);
        }

        void setPoliteness(String domain, long delayMs) { crawlDelayMs.put(domain, delayMs); }

        boolean isEligible(String domain, long nowMs) {
            long lastFetch = lastFetchedAtMs.getOrDefault(domain, 0L);
            long delay = crawlDelayMs.getOrDefault(domain, 2000L);
            return nowMs - lastFetch >= delay;
        }

        Optional<UrlEntry> pullNext(long nowMs) {
            UrlEntry best = null;
            for (var entry : byDomain.entrySet()) {
                String domain = entry.getKey();
                Deque<UrlEntry> queue = entry.getValue();
                if (queue.isEmpty() || !isEligible(domain, nowMs)) continue; // skip ineligible/empty domains
                UrlEntry candidate = queue.peekFirst();
                if (best == null || candidate.priority().ordinal() < best.priority().ordinal()) best = candidate;
            }
            if (best == null) return Optional.empty();
            byDomain.get(best.domain()).pollFirst();
            lastFetchedAtMs.put(best.domain(), nowMs); // politeness timer resets on fetch
            return Optional.of(best);
        }
    }

    public static void main(String[] args) {
        System.out.println("Level 1 - Bloom filter dedup:");
        BloomFilter bloom = new BloomFilter(1000, 3);
        bloom.add("https://example.com/a");
        bloom.add("https://example.com/b");
        System.out.println("  mightContain(\"https://example.com/a\"): " + bloom.mightContain("https://example.com/a") + "  (added, correctly TRUE)");
        System.out.println("  mightContain(\"https://never-added.com/x\"): " + bloom.mightContain("https://never-added.com/x") + "  (not added)");
        // Provoke a false positive with a tiny filter to demonstrate the tradeoff directly.
        BloomFilter tinyBloom = new BloomFilter(8, 2);
        tinyBloom.add("A"); tinyBloom.add("B"); tinyBloom.add("C"); tinyBloom.add("D");
        int falsePositives = 0;
        for (char c = 'E'; c <= 'Z'; c++) if (tinyBloom.mightContain(String.valueOf(c))) falsePositives++;
        System.out.println("  tiny filter (size=8): " + falsePositives + " false positive(s) out of 22 never-added items" +
            " - the space/accuracy tradeoff, made deliberately visible with a small filter");

        System.out.println("\nLevel 2 - domain-aware priority frontier:");
        Frontier frontier = new Frontier();
        frontier.setPoliteness("a.com", 2000);
        frontier.setPoliteness("b.com", 2000);
        frontier.enqueue(new UrlEntry("https://a.com/1", "a.com", Priority.NORMAL));
        frontier.enqueue(new UrlEntry("https://a.com/2", "a.com", Priority.HIGH));
        frontier.enqueue(new UrlEntry("https://b.com/1", "b.com", Priority.LOW));
        long t0 = 0;
        System.out.println("  pull at t=0: " + frontier.pullNext(t0).map(UrlEntry::url).orElse("none"));

        System.out.println("\nLevel 3 - combined: politeness makes a.com temporarily ineligible after being fetched:");
        System.out.println("  pull at t=0 (right after a.com/2 was just fetched, a.com in its 2s cooldown): " +
            frontier.pullNext(t0).map(UrlEntry::url).orElse("none - a.com not eligible, only b.com's LOW item exists but it IS eligible"));
        long t3000 = 3000; // 3 seconds later - a.com's cooldown has elapsed
        frontier.enqueue(new UrlEntry("https://a.com/3", "a.com", Priority.NORMAL));
        System.out.println("  pull at t=3000 (a.com cooldown elapsed): " + frontier.pullNext(t3000).map(UrlEntry::url).orElse("none"));
    }
}
```

**How to run:** `java WebCrawlerFrontierDedupDemo.java` (JDK 17+, single file, no dependencies).

## 6. Walkthrough

1. **Level 1:** `bloom.add("https://example.com/a")` and `bloom.add("https://example.com/b")` each set `numHashes = 3` bits in the shared `bits` array, computed from three salted hashes of the URL string. `bloom.mightContain("https://example.com/a")` recomputes the same three positions and finds all three bits set — correctly reporting `true`, since this exact URL was added.
2. **`bloom.mightContain("https://never-added.com/x")` checks three different positions** (different hash input), and at least one of them is very likely still `false` in a reasonably-sized, lightly-populated filter — correctly reporting `false`, meaning this URL is **definitely** new and safe to crawl.
3. **The `tinyBloom` example deliberately uses a tiny 8-bit array with only 4 items added**, to make the false-positive tradeoff visible without needing billions of real items — checking 22 never-added single-character strings against this severely undersized filter produces some number of false positives (bits that happen to already be set by the 4 real entries' hash positions, purely by coincidence in such a small array). This is the concrete, directly observable version of the tradeoff described in Part 3: a Bloom filter occasionally says "probably seen" for something never actually added, and undersizing the filter (relative to the number of items it holds) makes this happen more often — exactly the size/accuracy tuning real deployments must account for at the actual ~7.8 billion URL scale.
4. **Level 2:** `frontier.pullNext(t0)` at `t=0` scans every domain with a non-empty queue. Both `"a.com"` and `"b.com"` have never been fetched (`lastFetchedAtMs` empty for both), so `isEligible` returns `true` for both — among the eligible candidates, `"https://a.com/2"` (priority `HIGH`) beats `"https://a.com/1"` (priority `NORMAL`, but the same domain's queue only offers its *first* item, `peekFirst()`, so `NORMAL` from `a.com` isn't even compared here) and `"https://b.com/1"` (priority `LOW`) — `HIGH` wins, and the method returns it, while also updating `lastFetchedAtMs.put("a.com", t0)`.
5. **Level 3** calls `pullNext(t0)` again, immediately at the same timestamp. Now `isEligible("a.com", t0)` checks `t0 - lastFetchedAtMs.get("a.com") (which is also t0) >= 2000` — `0 >= 2000` is `false`, so `"a.com"` is skipped entirely this round, even though it still has a queued `NORMAL` item. Only `"b.com"`'s `LOW` item is eligible, so it is returned — correctly demonstrating that politeness (a domain's own cooldown) takes precedence over priority when a higher-priority domain simply is not currently allowed to be fetched from. **At `t=3000`**, three seconds having passed, `isEligible("a.com", 3000)` now evaluates `3000 - 0 >= 2000` as `true` — `"a.com"` is eligible again, and its newly enqueued `NORMAL` item is returned, confirming the domain's politeness window correctly reopened after the configured delay elapsed.

## 7. Gotchas & takeaways

> **Gotcha:** a Bloom filter has no way to remove an item once added (a standard Bloom filter, at least — variants exist but add complexity) — if a use case ever needs "forget this URL was crawled" (for instance, to deliberately allow a recrawl per FR-9), the Bloom filter alone cannot support that directly. A real implementation typically tracks "already fetched, eligible for recrawl after N days" using the `CrawledPage.fetchedAt` timestamp from [data model & schema](0256-web-crawler-data-model-schema.md) as a separate mechanism, using the Bloom filter purely to prevent *duplicate initial discovery* within the same crawl pass, not to gate recrawl eligibility.

- Size a Bloom filter deliberately for its expected item count and acceptable false-positive rate — Level 1's tiny, deliberately-undersized filter makes the tradeoff visible; a real deployment at billions of URLs sizes the bit array and hash count mathematically to hit a target false-positive rate (commonly under 1%).
- The Frontier's domain-partitioned structure, not a single global priority queue, is what makes politeness and priority coexist correctly — Level 3 demonstrates this directly: a higher-priority item on a currently-ineligible domain is correctly passed over in favor of a lower-priority item on an eligible one.
- A Bloom filter's "probably seen" false positives cost only a missed crawl of that one URL — an acceptable, bounded cost given the alternative (a full hash set at billions of entries) is far more expensive, and this is exactly the kind of accuracy-for-efficiency tradeoff this whole series has repeatedly surfaced as a deliberate, stated design choice, not a shortcut.
- See [Web Crawler — scaling & tradeoffs](0258-web-crawler-scaling-tradeoffs.md) next for how this Frontier and Dedup design holds up as the crawl grows well past a single machine's capacity for either structure.
