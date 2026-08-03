---
card: data-structures
gi: 172
slug: count-min-sketch-overview
title: Count-min sketch (overview)
---

## 1. What it is

A **count-min sketch** estimates how many times each item has appeared in a stream, using a small fixed amount of memory instead of one counter per distinct item. Like a [Bloom filter](0171-bloom-filter-false-positives.md), it trades perfect accuracy for space — its counts can be **overestimates**, but never underestimates.

## 2. Why & when

Use a count-min sketch when you need approximate item frequencies over a huge or unbounded stream — counting how many times each URL was requested, tracking trending hashtags, or estimating query frequency for a search engine — and storing an exact `Map<Item, Count>` would need too much memory for the number of distinct items involved. A count-min sketch answers "roughly how many times has this appeared?" using a fixed-size grid of counters, regardless of how many distinct items exist.

## 3. Core concept

**The shape.** A 2D grid of counters, `depth` rows by `width` columns, all starting at `0`. Each row has its own independent hash function mapping any item to one of `width` columns.

**Adding an item.** For each row `r`, compute `col = hash_r(item) % width`, and increment `grid[r][col]` by `1`. One item, added once, increments exactly `depth` counters — one per row.

**Estimating a count.** For each row `r`, compute the same `col = hash_r(item) % width`, and read `grid[r][col]`. The estimate is the **minimum** across all `depth` rows: `min(grid[0][col_0], grid[1][col_1], ..., grid[depth-1][col_(depth-1)])`.

**Why the minimum, and why it only overestimates.** Because many different items can hash to the same column in any one row (a collision), a single row's counter for an item's column can be inflated by *other* items also landing there — it counts the true item plus whatever collided with it, so it is always `>= the true count`. Taking the **minimum** across all rows picks whichever row happened to have the fewest colliding items, giving the tightest (closest to true) overestimate available. This is why the structure can never underestimate: every row's counter, even the smallest one, still includes the true item's own increments.

**Why more rows and columns reduce error.** More columns (`width`) means fewer items collide into the same counter. More rows (`depth`) means more independent chances to find a row with little collision, and the minimum picks the best one. Both knobs trade memory for accuracy, the same tradeoff shape as a Bloom filter's bits and hash count.

## 4. Diagram

<svg viewBox="0 0 640 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A count-min sketch grid where one item increments one counter per row, and the estimate takes the minimum across rows">
  <g font-family="sans-serif" font-size="10" fill="#e6edf3">
    <text x="10" y="20">grid (depth=3, width=6), after adding "cat" x5 and some collisions:</text>
    <g transform="translate(10,30)">
      <text x="-5" y="17" font-size="8">row0</text>
      <rect x="20" y="0" width="30" height="24" fill="#0d1117" stroke="#8b949e"/><text x="35" y="16" text-anchor="middle">2</text>
      <rect x="50" y="0" width="30" height="24" fill="#f0883e" fill-opacity="0.3" stroke="#f0883e"/><text x="65" y="16" text-anchor="middle">7</text>
      <rect x="80" y="0" width="30" height="24" fill="#0d1117" stroke="#8b949e"/><text x="95" y="16" text-anchor="middle">1</text>

      <text x="-5" y="47" font-size="8">row1</text>
      <rect x="20" y="30" width="30" height="24" fill="#f0883e" fill-opacity="0.3" stroke="#f0883e"/><text x="35" y="46" text-anchor="middle">9</text>
      <rect x="50" y="30" width="30" height="24" fill="#0d1117" stroke="#8b949e"/><text x="65" y="46" text-anchor="middle">3</text>
      <rect x="80" y="30" width="30" height="24" fill="#0d1117" stroke="#8b949e"/><text x="95" y="46" text-anchor="middle">4</text>

      <text x="-5" y="77" font-size="8">row2</text>
      <rect x="20" y="60" width="30" height="24" fill="#0d1117" stroke="#8b949e"/><text x="35" y="76" text-anchor="middle">6</text>
      <rect x="50" y="60" width="30" height="24" fill="#0d1117" stroke="#8b949e"/><text x="65" y="76" text-anchor="middle">2</text>
      <rect x="80" y="60" width="30" height="24" fill="#3fb950" fill-opacity="0.3" stroke="#3fb950"/><text x="95" y="76" text-anchor="middle">5</text>
    </g>
    <text x="10" y="140" font-size="9" fill="#8b949e">"cat" hashes to: row0-&gt;col1(7), row1-&gt;col0(9), row2-&gt;col2(5, green, least collided)</text>
    <text x="10" y="160" font-size="9" fill="#3fb950">estimate("cat") = min(7, 9, 5) = 5 -- matches the true count exactly this time</text>
  </g>
</svg>

The minimum across rows picks the least-collided counter, giving the tightest overestimate.

## 5. Runnable example

```java
// CountMinSketch.java
import java.util.*;

public class CountMinSketch {

    // Basic: a count-min sketch supporting add and estimate.
    static class Sketch {
        int[][] grid;
        int depth, width;

        Sketch(int depth, int width) {
            this.depth = depth;
            this.width = width;
            grid = new int[depth][width];
        }

        int hash(String item, int row) {
            int h = item.hashCode() ^ (row * 0x9e3779b9);
            return Math.floorMod(h, width);
        }

        void add(String item) {
            for (int row = 0; row < depth; row++) {
                grid[row][hash(item, row)]++;
            }
        }

        long estimate(String item) {
            long min = Long.MAX_VALUE;
            for (int row = 0; row < depth; row++) {
                min = Math.min(min, grid[row][hash(item, row)]);
            }
            return min;
        }
    }

    static void basicLevel() {
        Sketch sketch = new Sketch(4, 100);
        for (int i = 0; i < 5; i++) sketch.add("cat");
        for (int i = 0; i < 2; i++) sketch.add("dog");

        System.out.println("basic: estimate(\"cat\") -> " + sketch.estimate("cat"));
        System.out.println("basic: estimate(\"dog\") -> " + sketch.estimate("dog"));
        System.out.println("basic: estimate(\"fish\", never added) -> " + sketch.estimate("fish"));
    }

    // Intermediate: compare estimated counts against exact counts (via a HashMap) to see the overestimation error.
    static void intermediateLevel() {
        Sketch sketch = new Sketch(4, 50); // small width to make collisions likely
        Map<String, Integer> exact = new HashMap<>();
        Random random = new Random(3);

        String[] items = {"alpha", "beta", "gamma", "delta", "epsilon"};
        for (int i = 0; i < 2000; i++) {
            String item = items[random.nextInt(items.length)];
            sketch.add(item);
            exact.merge(item, 1, Integer::sum);
        }

        for (String item : items) {
            System.out.println("intermediate: " + item + " exact=" + exact.get(item) + " estimate=" + sketch.estimate(item));
        }
    }

    // Advanced: widen the sketch to reduce error, comparing overestimation at two different widths.
    static void advancedLevel() {
        Random random = new Random(3);
        String[] items = {"alpha", "beta", "gamma", "delta", "epsilon"};

        Sketch narrow = new Sketch(4, 20);
        Sketch wide = new Sketch(4, 2000);
        Map<String, Integer> exact = new HashMap<>();

        for (int i = 0; i < 5000; i++) {
            String item = items[random.nextInt(items.length)];
            narrow.add(item);
            wide.add(item);
            exact.merge(item, 1, Integer::sum);
        }

        for (String item : items) {
            System.out.println("advanced: " + item + " exact=" + exact.get(item)
                + " narrow_estimate=" + narrow.estimate(item) + " wide_estimate=" + wide.estimate(item));
        }
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

How to run: `java CountMinSketch.java`

## 6. Walkthrough

Create a sketch with `depth = 4` rows and `width = 100` columns. Call `add("cat")` five times: each call increments one counter per row (4 counters total per call), so after 5 calls, those 4 counters each hold at least `5` (more, if other items collided into the same cells).

Call `estimate("cat")`: recompute the same 4 row-column positions used during `add`, read each counter, and return the **minimum** of the 4. Since every one of those 4 counters received exactly `cat`'s 5 increments plus possibly some collisions from other items, the minimum is the closest available estimate to the true value of `5` — and it can only be `>= 5`, never less.

The `intermediateLevel` example deliberately uses a small `width = 50` with 2000 total additions across only 5 distinct items, making collisions likely, then compares the sketch's estimate against an exact `HashMap` count for the same items — showing the overestimation directly. The `advancedLevel` example repeats this with a much wider sketch (`width = 2000`) alongside the narrow one, showing the wider sketch's estimates land much closer to the exact counts, because collisions become rarer as `width` grows relative to the number of distinct items.

**Complexity.** Add: `O(depth)`. Estimate: `O(depth)`. Space: `O(depth * width)`, fixed regardless of how many distinct items appear in the stream — the key advantage over an exact per-item counter map, whose space grows with the number of distinct items.

## 7. Gotchas & takeaways

> A count-min sketch answers "roughly how many times has this specific item appeared?" It is a different tool from a [Bloom filter](0171-bloom-filter-false-positives.md), which only answers "has this item possibly appeared at all?" — do not use one where the other is needed.

- Estimates only ever overestimate, never underestimate — if your use case needs a guaranteed lower bound instead (or cannot tolerate any overestimate), this structure is the wrong fit.
- Choosing `width` and `depth` follows a similar formula to Bloom filters: wider reduces the error margin, deeper increases the confidence that the minimum found is close to the truth, both at the cost of more memory.
- For counting **distinct** items (cardinality) rather than per-item frequency, use [HyperLogLog](0176-hyperloglog-for-cardinality-estimation.md) instead — a related structure solving a different counting problem.
