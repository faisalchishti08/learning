---
card: data-structures
gi: 176
slug: hyperloglog-for-cardinality-estimation
title: HyperLogLog for cardinality estimation
---

## 1. What it is

**HyperLogLog** estimates the number of **distinct** items in a huge stream — its **cardinality** — using a tiny, fixed amount of memory (a few kilobytes), regardless of whether the stream has a thousand or a billion distinct items. It trades exactness for a small, well-understood error margin (typically around 1-2%).

## 2. Why & when

Use HyperLogLog when you need "roughly how many distinct visitors, IP addresses, or search queries have we seen?" at massive scale — counting unique visitors to a website, unique values in a huge log stream — where an exact `HashSet<Item>` would need memory proportional to the number of distinct items, which can be gigabytes for billions of events. HyperLogLog answers the same question using a fixed handful of kilobytes, no matter how large the true count is.

## 3. Core concept

**The core insight.** Hash every item to a uniformly random bit string. In a truly random bit string, the probability of seeing a run of `k` leading zeros is `1 / 2^k` — rare runs of many leading zeros are a signal that you have hashed **many** distinct items, because you needed many tries to get unlucky enough to see that rare pattern. Track the **longest run of leading zeros** seen across all hashed items, and use it to estimate the count: roughly, if the longest run seen is `k` zeros, the estimated count is around `2^k`.

**Why a single estimate is too noisy, and how buckets fix it.** One item's hash could randomly happen to have many leading zeros purely by chance, giving a wildly wrong single estimate. HyperLogLog fixes this by splitting the hash space into many buckets (say, `m` buckets), using a few bits of each hash to pick a bucket, and tracking the longest leading-zero run **per bucket**. Averaging (technically, harmonic-mean-averaging, with a bias correction constant) across all `m` buckets smooths out the noise from any single unlucky or lucky item.

**The shape.** An array of `m` small counters (commonly `m = 2^b` for some `b`, e.g. `m = 16384`), each holding the longest leading-zero run observed for items that hashed into that bucket. Adding an item: hash it, use the first `b` bits to choose a bucket, use the remaining bits to compute the leading-zero-run length, and update that bucket's counter if this run is longer than what is already stored there.

**Why memory stays fixed regardless of true cardinality.** Each bucket only ever stores a small integer (the longest run length seen, which for realistic cardinalities never exceeds a few dozen — fitting easily in one byte). The total memory is `m` bytes, fixed by the chosen `m`, whether the true distinct count is a thousand or a trillion.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="HyperLogLog buckets, each tracking the longest run of leading zeros seen among hashed items routed to that bucket">
  <g font-family="sans-serif" font-size="10" fill="#e6edf3">
    <text x="10" y="20">item hash: [bucket bits][remaining bits with leading zeros]</text>
    <text x="10" y="40" font-family="monospace">e.g. hash("user42") = 0101 | 00011...  -&gt; bucket 5, run-length 3</text>

    <g transform="translate(20,60)">
      <text x="0" y="10" font-size="9">bucket:</text>
      <text x="60" y="10" font-size="9">0</text><text x="110" y="10" font-size="9">1</text><text x="160" y="10" font-size="9">2</text><text x="210" y="10" font-size="9">3</text><text x="260" y="10" font-size="9">4</text><text x="310" y="10" font-size="9">5</text>
      <text x="0" y="35" font-size="9">max run:</text>
      <rect x="45" y="20" width="35" height="24" fill="#0d1117" stroke="#8b949e"/><text x="62" y="36" text-anchor="middle" font-size="9">2</text>
      <rect x="95" y="20" width="35" height="24" fill="#0d1117" stroke="#8b949e"/><text x="112" y="36" text-anchor="middle" font-size="9">5</text>
      <rect x="145" y="20" width="35" height="24" fill="#0d1117" stroke="#8b949e"/><text x="162" y="36" text-anchor="middle" font-size="9">1</text>
      <rect x="195" y="20" width="35" height="24" fill="#0d1117" stroke="#8b949e"/><text x="212" y="36" text-anchor="middle" font-size="9">3</text>
      <rect x="245" y="20" width="35" height="24" fill="#0d1117" stroke="#8b949e"/><text x="262" y="36" text-anchor="middle" font-size="9">4</text>
      <rect x="295" y="20" width="35" height="24" fill="#f0883e" fill-opacity="0.3" stroke="#f0883e"/><text x="312" y="36" text-anchor="middle" font-size="9">3</text>
    </g>
    <text x="10" y="140" font-size="9" fill="#8b949e">estimate = harmonic-mean-based formula over all bucket values, times a bias-correction constant</text>
    <text x="10" y="160" font-size="9" fill="#8b949e">more buckets -&gt; smoother average -&gt; lower error, at a fixed small memory cost</text>
  </g>
</svg>

Each bucket records its own longest zero-run; combining all buckets smooths out per-item randomness.

## 5. Runnable example

```java
// HyperLogLog.java
import java.util.*;

public class HyperLogLog {

    // Basic: a simplified HyperLogLog estimator (teaching version, not production-tuned bias correction).
    static class Estimator {
        int[] buckets;
        int bucketBits;
        int m;

        Estimator(int bucketBits) {
            this.bucketBits = bucketBits;
            this.m = 1 << bucketBits;
            buckets = new int[m];
        }

        void add(String item) {
            long hash = hash64(item);
            int bucketIndex = (int) (hash >>> (64 - bucketBits));
            long remaining = hash << bucketBits; // shift out the bucket bits
            int runLength = Long.numberOfLeadingZeros(remaining) + 1;
            buckets[bucketIndex] = Math.max(buckets[bucketIndex], runLength);
        }

        long hash64(String item) {
            // A simple 64-bit hash mix (not cryptographic, sufficient for the demo).
            long h = item.hashCode();
            h ^= (h >>> 33);
            h *= 0xff51afd7ed558ccdL;
            h ^= (h >>> 33);
            return h;
        }

        double estimate() {
            double sumInverse = 0;
            for (int run : buckets) sumInverse += 1.0 / (1L << run);
            double alpha = 0.7213 / (1 + 1.079 / m); // standard bias-correction constant
            return alpha * m * m / sumInverse;
        }
    }

    static void basicLevel() {
        Estimator hll = new Estimator(10); // m = 1024 buckets
        for (int i = 0; i < 500; i++) hll.add("item-" + i);

        System.out.printf("basic: true distinct count = 500, estimate = %.0f%n", hll.estimate());
    }

    // Intermediate: adding duplicates should not change the estimate.
    static void intermediateLevel() {
        Estimator hll = new Estimator(10);
        for (int i = 0; i < 200; i++) hll.add("item-" + i);
        double firstEstimate = hll.estimate();

        for (int i = 0; i < 200; i++) hll.add("item-" + i); // add the exact same items again
        double secondEstimate = hll.estimate();

        System.out.printf("intermediate: estimate before duplicates = %.0f%n", firstEstimate);
        System.out.printf("intermediate: estimate after re-adding same items = %.0f (should be nearly unchanged)%n", secondEstimate);
    }

    // Advanced: compare HyperLogLog's memory-vs-accuracy tradeoff against an exact HashSet, at a larger scale.
    static void advancedLevel() {
        int trueDistinct = 100_000;
        Estimator hll = new Estimator(12); // m = 4096 buckets, ~4KB
        Set<String> exact = new HashSet<>();

        for (int i = 0; i < trueDistinct; i++) {
            String item = "user-" + i;
            hll.add(item);
            exact.add(item);
        }

        double estimate = hll.estimate();
        double errorPercent = 100.0 * Math.abs(estimate - trueDistinct) / trueDistinct;
        System.out.printf("advanced: true=%d, HLL estimate=%.0f, error=%.2f%%, HLL memory=%d ints%n",
            trueDistinct, estimate, errorPercent, hll.buckets.length);
        System.out.println("advanced: exact HashSet memory would need to store all " + exact.size() + " distinct strings");
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

How to run: `java HyperLogLog.java`

## 6. Walkthrough

Create an estimator with `bucketBits = 10`, giving `m = 1024` buckets. Add `500` distinct items. Each `add` call hashes the item to a 64-bit value, uses the top `10` bits to pick one of `1024` buckets, and computes the run of leading zeros in the remaining bits (`+1`, so a value of `0` leading zeros still counts as a run of `1`). If this run is longer than what that bucket already holds, update the bucket.

After all `500` adds, call `estimate()`. It computes the harmonic mean of `2^bucket_value` across all `1024` buckets (via the `sumInverse` accumulation), scales by `m^2` and a bias-correction constant `alpha`, and returns the result — which lands close to `500`, typically within a few percent, without ever having stored a single actual item.

The `intermediateLevel` example re-adds the exact same `200` items a second time. Because each bucket only ever keeps the **maximum** run length it has seen, re-adding an already-seen item can only match or fail to beat the existing maximum — it never changes the estimate, correctly reflecting that no *new* distinct item was added.

**Complexity.** Add: `O(1)` — one hash, one bucket update. Estimate: `O(m)` to sum over all buckets. Space: `O(m)`, fixed regardless of the true cardinality — the `advancedLevel` example shows `4096` small integers estimating `100,000` distinct items with a small error, versus an exact `HashSet` that must store all `100,000` actual strings.

## 7. Gotchas & takeaways

> HyperLogLog answers "how many **distinct** items?" It does **not** tell you *which* items were seen, or how many times each one appeared — for per-item frequency, use a [count-min sketch](0172-count-min-sketch-overview.md) instead; for membership testing, use a [Bloom filter](0171-bloom-filter-false-positives.md).

- Accuracy improves with more buckets (`m`) at the cost of more memory — the standard error is roughly `1.04 / sqrt(m)`, so quadrupling `m` roughly halves the error.
- A major real-world strength: two HyperLogLog estimators can be **merged** by taking the elementwise maximum of their buckets, giving the correct distinct count for the union of both streams — without ever re-processing the original data. This is why databases like Redis and Postgres extensions offer HyperLogLog natively for distributed unique-counting.
- The simplified estimator above skips small-range and large-range bias corrections that production implementations (like Redis's `PFCOUNT`) include for extra accuracy at the low and high ends of the cardinality range — treat this version as illustrative, not production-ready.
