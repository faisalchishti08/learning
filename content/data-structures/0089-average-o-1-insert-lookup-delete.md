---
card: data-structures
gi: 89
slug: average-o-1-insert-lookup-delete
title: Average O(1) insert/lookup/delete
---

## 1. What it is

A well-implemented hash table gives **average O(1)** time for `insert`, `lookup`, and `delete` — meaning the typical cost does not grow as the table holds more entries. This is the headline reason hash tables (`HashMap`, `HashSet`) are the default choice for "store and retrieve by key" in almost every language, ahead of arrays or trees.

## 2. Why & when

Knowing exactly *why* it is O(1) on average — not just that it is — is what lets you reason correctly about an algorithm's overall complexity when it uses a hash table internally, and what lets you recognize when that guarantee breaks down (see [Worst-case degradation & mitigation](0090-worst-case-degradation-mitigation.md)). This is the single most load-bearing complexity fact in everyday coding interviews.

## 3. Core concept

**Why `insert` is average O(1).** Computing a key's hash code is O(1) for fixed-size keys (or O(k) for a key of length `k`, which is usually treated as a constant relative to the number of entries `n`). Finding the target bucket from the hash is O(1) arithmetic. Appending to that bucket's chain (or finding an open slot nearby, for open addressing) is O(1) *on average*, because a well-maintained load factor keeps each bucket's expected size small and constant, regardless of how large `n` grows.

**Why `lookup` and `delete` are the same.** Both start with the identical hash-then-locate-bucket steps as `insert`. `lookup` then walks the bucket's (short) chain checking `equals()`; `delete` does the same, then removes the matching entry. Since the expected chain length stays constant as `n` grows (as long as rehashing keeps load factor bounded), all three operations share the same average-case complexity.

**"Average," not "worst-case" — the crucial distinction.** The O(1) guarantee is a *statistical average* over random-ish key distributions, not a guarantee for every single call. A single unlucky lookup could still walk a longer-than-typical chain. The average holds because a good hash function makes long chains rare, and rehashing keeps the *expected* chain length bounded as the table grows — but no individual operation is mathematically guaranteed to be fast.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A graph comparing lookup cost versus number of entries for an array (linear growth) against a hash table (flat, constant on average)">
  <g font-family="sans-serif" font-size="11">
    <line x1="40" y1="140" x2="600" y2="140" stroke="#8b949e"/>
    <line x1="40" y1="140" x2="40" y2="20" stroke="#8b949e"/>
    <text x="320" y="160" fill="#8b949e" text-anchor="middle" font-size="9">number of entries (n)</text>
    <text x="20" y="80" fill="#8b949e" text-anchor="middle" font-size="9" transform="rotate(-90 20 80)">cost</text>
    <line x1="40" y1="140" x2="580" y2="30" stroke="#f0883e"/>
    <text x="500" y="55" fill="#f0883e" font-size="9">array linear scan: O(n)</text>
    <line x1="40" y1="125" x2="580" y2="125" stroke="#79c0ff"/>
    <text x="500" y="115" fill="#79c0ff" font-size="9">hash table lookup: average O(1)</text>
  </g>
</svg>

An array's linear-scan lookup cost grows with `n`; a well-tuned hash table's lookup cost stays flat, on average, regardless of `n`.

## 5. Runnable example

```java
// AverageO1Demo.java
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

public class AverageO1Demo {

    // Basic: confirm O(1)-average behavior by timing lookups at two very different table sizes.
    static void basicLevel() {
        Map<Integer, Integer> small = new HashMap<>();
        for (int i = 0; i < 100; i++) small.put(i, i * i);

        Map<Integer, Integer> large = new HashMap<>();
        for (int i = 0; i < 1_000_000; i++) large.put(i, i * i);

        long t0 = System.nanoTime();
        for (int i = 0; i < 100_000; i++) small.get(i % 100);
        long smallNs = System.nanoTime() - t0;

        long t1 = System.nanoTime();
        for (int i = 0; i < 100_000; i++) large.get(i % 1_000_000);
        long largeNs = System.nanoTime() - t1;

        System.out.println("basic: 100k lookups on a 100-entry map -> " + smallNs + " ns");
        System.out.println("basic: 100k lookups on a 1,000,000-entry map -> " + largeNs + " ns (roughly the same order of magnitude)");
    }

    // Intermediate: contrast against a List's linear-scan "lookup by value", which DOES grow with n.
    static void intermediateLevel() {
        List<Integer> smallList = new ArrayList<>();
        for (int i = 0; i < 1000; i++) smallList.add(i);

        List<Integer> largeList = new ArrayList<>();
        for (int i = 0; i < 100_000; i++) largeList.add(i);

        long t0 = System.nanoTime();
        smallList.contains(999); // worst case: scans the whole list
        long smallNs = System.nanoTime() - t0;

        long t1 = System.nanoTime();
        largeList.contains(99_999); // worst case: scans a MUCH longer list
        long largeNs = System.nanoTime() - t1;

        System.out.println("intermediate: List.contains on 1,000 entries -> " + smallNs + " ns");
        System.out.println("intermediate: List.contains on 100,000 entries -> " + largeNs + " ns (noticeably larger -- O(n) in action)");
    }

    // Advanced: insert, lookup, delete all on the same map, confirming each stays fast as size grows past a resize point.
    static void advancedLevel() {
        Map<Integer, String> map = new HashMap<>();
        int n = 500_000;

        long t0 = System.nanoTime();
        for (int i = 0; i < n; i++) map.put(i, "v" + i); // insert, including several internal rehashes along the way
        long insertMs = (System.nanoTime() - t0) / 1_000_000;

        long t1 = System.nanoTime();
        for (int i = 0; i < n; i++) map.get(i); // lookup, after the table has settled at its final size
        long lookupMs = (System.nanoTime() - t1) / 1_000_000;

        long t2 = System.nanoTime();
        for (int i = 0; i < n; i++) map.remove(i); // delete
        long deleteMs = (System.nanoTime() - t2) / 1_000_000;

        System.out.println("advanced: " + n + " inserts -> " + insertMs + " ms, lookups -> " + lookupMs + " ms, deletes -> " + deleteMs + " ms");
        System.out.println("advanced: all three average out to roughly linear TOTAL time -- i.e. O(1) PER operation");
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

**How to run:** save as `AverageO1Demo.java`, then run `java AverageO1Demo.java`.

## 6. Walkthrough

1. `basicLevel()` times 100,000 lookups on a 100-entry map versus a 1,000,000-entry map. Both finish in a comparable order of magnitude, since each individual `get` only walks one (short) bucket, regardless of how many *other* buckets exist elsewhere in the table.
2. `intermediateLevel()` contrasts this against `List.contains`, which must linearly scan — a 100,000-entry list's `contains` call does measurably more work than a 1,000-entry list's, since there is no bucket structure to jump directly to a small subset of candidates.
3. `advancedLevel()` runs 500,000 inserts, lookups, and deletes on one map, confirming all three operations' *total* time scales roughly linearly with `n` — which means the *per-operation* cost stays roughly constant, exactly the definition of average O(1). The insert phase includes several internal rehashes (each O(n) individually), but their amortized cost, spread across all 500,000 inserts, still nets out to an average O(1) per insert.

## 7. Gotchas & takeaways

> Gotcha: "average O(1)" is not a hard guarantee — a hash table with a poor hash function, or one under adversarial attack (an attacker deliberately choosing keys that all collide), can degrade every operation to O(n). See [Worst-case degradation & mitigation](0090-worst-case-degradation-mitigation.md) for how this happens and how Java's `HashMap` mitigates it.

- Hash table `insert`, `lookup`, and `delete` are all average O(1), because each only needs to hash the key (O(1)) and search one small, bounded-size bucket.
- The guarantee is statistical — it depends on a good hash function and a bounded load factor (maintained via rehashing), not a mathematical certainty for every call.
- This is why hash tables outperform arrays and lists for "find by key" workloads at any meaningful scale.
- Related concepts: [Load factor & rehashing](0086-load-factor-rehashing.md), [Worst-case degradation & mitigation](0090-worst-case-degradation-mitigation.md).
