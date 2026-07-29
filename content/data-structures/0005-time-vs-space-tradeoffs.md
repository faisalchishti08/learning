---
card: data-structures
gi: 5
slug: time-vs-space-tradeoffs
title: Time vs space tradeoffs
---

## 1. What it is

A **time-space tradeoff** is a design choice where using more memory reduces running time, or vice versa. The same problem can often be solved with a fast, memory-hungry approach or a slow, memory-lean approach — recognizing which resource is scarcer in your situation determines the right choice.

## 2. Why & when

Reach for this framing whenever you have already found a correct solution and are asking "can this be faster?" or "can this use less memory?" — the two questions usually pull in opposite directions, and there is rarely a solution that is simultaneously optimal on both axes. Constrained environments (embedded systems, mobile apps, tight memory limits) favor space efficiency; latency-sensitive systems (real-time systems, hot loops called millions of times) favor time efficiency, even at a real memory cost.

## 3. Core concept

**Decision criteria:** ask which resource is the actual bottleneck for your situation. If memory is abundant but the operation runs in a hot path called constantly, spend memory to cache or precompute results. If memory is the constraint (or the extra memory cost outweighs the time saved for your actual workload), accept slower running time to stay within budget.

**Classic examples of the tradeoff:**
- **Caching / memoization:** storing previously computed results in a hash map trades O(n) or more extra memory for turning repeated expensive computations into O(1) lookups (the foundation of dynamic programming's speedup over naive recursion).
- **Hash tables vs. sorted arrays:** a hash table gives O(1) average lookup but uses more memory (buckets, load factor overhead) than a compact sorted array, which gives O(log n) lookup (via binary search) in tighter memory.
- **Precomputed lookup tables:** replacing a repeated expensive calculation (like trigonometric functions, or checking primality) with a precomputed table trades memory (storing every possible answer) for O(1) retrieval instead of recomputation.
- **Bloom filters:** trade a small, controlled false-positive rate for using far less memory than storing the full exact set — an explicit, deliberate tradeoff of *correctness precision* for *space*, on top of the usual time/space axis.

**Why there is rarely a solution that wins on both axes simultaneously:** most algorithmic speedups come from *remembering* something (a cache, an index, a precomputed table) so that future work can be skipped — but remembering something costs memory. An algorithm using strictly less time *and* strictly less memory than another correct algorithm for the same problem, with no other tradeoff, usually means the second algorithm was simply worse in both respects, not that such an algorithm doesn't need to make a genuine choice at all.

## 4. Diagram

<svg viewBox="0 0 700 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A tradeoff curve: as memory usage increases, running time decreases, illustrated with memoization moving a point from slow-lean to fast-heavy">
  <g font-family="sans-serif" font-size="12">
    <line x1="60" y1="150" x2="60" y2="20" stroke="#8b949e"/>
    <text x="30" y="90" fill="#8b949e" text-anchor="middle" transform="rotate(-90 30 90)">time</text>
    <line x1="60" y1="150" x2="650" y2="150" stroke="#8b949e"/>
    <text x="350" y="170" fill="#8b949e" text-anchor="middle">memory</text>
    <path d="M80,30 Q200,40 350,90 T620,140" fill="none" stroke="#79c0ff" stroke-width="2"/>
    <circle cx="90" cy="35" r="6" fill="#f0883e"/><text x="90" y="20" fill="#f0883e" text-anchor="middle" font-size="10">naive recursion</text>
    <circle cx="600" cy="140" r="6" fill="#3fb950"/><text x="600" y="160" fill="#3fb950" text-anchor="middle" font-size="10">memoized</text>
  </g>
</svg>

Moving along the curve from "slow, memory-lean" to "fast, memory-heavy" — memoization is a concrete instance of spending memory to buy speed.

## 5. Runnable example

The artifact below compares naive recursive Fibonacci (exponential time, minimal memory) against a memoized version (linear time, linear memory), demonstrating the tradeoff directly.

```java
// TimeVsSpaceTradeoffs.java
import java.util.*;

public class TimeVsSpaceTradeoffs {

    // Time-lean on memory, but exponential time: recomputes overlapping subproblems repeatedly.
    static long fibNaive(int n) {
        if (n <= 1) return n;
        return fibNaive(n - 1) + fibNaive(n - 2);
    }

    // Spends O(n) memory (the cache) to achieve O(n) time instead of exponential.
    static long fibMemoized(int n, Map<Integer, Long> cache) {
        if (n <= 1) return n;
        if (cache.containsKey(n)) return cache.get(n);
        long result = fibMemoized(n - 1, cache) + fibMemoized(n - 2, cache);
        cache.put(n, result);
        return result;
    }

    public static void main(String[] args) {
        int n = 35;

        long start = System.nanoTime();
        long naiveResult = fibNaive(n);
        long naiveTime = System.nanoTime() - start;

        start = System.nanoTime();
        long memoResult = fibMemoized(n, new HashMap<>());
        long memoTime = System.nanoTime() - start;

        System.out.println("naive: result=" + naiveResult + ", time=" + naiveTime + "ns");
        System.out.println("memoized: result=" + memoResult + ", time=" + memoTime + "ns");
        System.out.println("memoized was faster: " + (memoTime < naiveTime));
    }
}
```

**How to run:** save as `TimeVsSpaceTradeoffs.java`, then run `java TimeVsSpaceTradeoffs.java`.

## 6. Walkthrough

1. `fibNaive(35)` recomputes the same subproblems repeatedly — `fibNaive(30)`, for example, gets called many separate times as part of computing `fibNaive(35)`, since each call branches into two fresh recursive calls with no memory of prior work. Total work grows exponentially with `n`.
2. `fibMemoized(35, cache)` computes each distinct `fib(k)` value exactly once, storing it in `cache` the first time. Every subsequent request for that same `k` is an O(1) map lookup instead of a recomputation.
3. Both approaches compute the identical mathematical result (`fibNaive(35) == fibMemoized(35, ...)`), but the memoized version finishes dramatically faster for `n=35`, at the cost of using O(n) extra memory for the cache — memory the naive version never allocates.
4. This is the tradeoff made concrete: identical correctness, different resource spent (time for the naive version, memory for the memoized version) to achieve very different running times.

## 7. Gotchas & takeaways

> Gotcha: reflexively adding a cache "for speed" without checking whether the memory cost is actually justified can backfire — if a computation is called only once, or if the cache itself becomes large enough to cause memory pressure (garbage collection pauses, cache eviction thrashing), the "faster" memoized version can end up slower or less reliable in practice than the simple, memory-lean original.

- The tradeoff: spend memory (caching, precomputed tables, indexes) to save time, or spend time (recomputation, scanning) to save memory — pick based on which resource is actually the bottleneck for your situation.
- Memoization/dynamic programming is the most common instance of this tradeoff in algorithm design.
- Related concepts: [Amortized analysis (dynamic-array doubling)](0004-amortized-analysis-dynamic-array-doubling.md) (a related idea, though about spreading cost over time rather than trading one resource for another), [In-place vs auxiliary-space algorithms](0009-in-place-vs-auxiliary-space-algorithms.md) (a specific, common instance of this same tradeoff for sorting and array algorithms).
