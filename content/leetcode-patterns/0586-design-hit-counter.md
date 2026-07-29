---
card: leetcode-patterns
gi: 586
slug: design-hit-counter
title: Design Hit Counter
---

## 1. What it is

Design a `HitCounter` class that records timestamped "hits" and reports how many occurred in the last 300 seconds. `hit(timestamp)` records a hit at `timestamp` (seconds, monotonically non-decreasing across calls). `getHits(timestamp)` returns the number of hits with a recorded timestamp in the inclusive range `[timestamp - 299, timestamp]`. Example: `hit(1)`, `hit(2)`, `hit(3)`, `getHits(4)` → `3`, `hit(300)`, `getHits(300)` → `4`, `getHits(301)` → `3` (the hit at timestamp `1` has fallen out of the 300-second window).

## 2. Why & when

This is a **sliding time window** problem: as `timestamp` advances, old hits outside the trailing 300-second window must stop being counted, without rescanning every hit ever recorded. Storing all hits in a queue, ordered by timestamp (since calls arrive in non-decreasing timestamp order), lets you discard expired hits from the front in O(1) each, instead of filtering the entire history on every query.

## 3. Core concept

**Key idea:** store hits in a `Queue<Integer>` of timestamps, in arrival order. Because `hit` calls arrive with non-decreasing timestamps, the queue is always sorted — the oldest hits are always at the front. Before answering `getHits`, pop every timestamp from the front that has fallen outside the window `[timestamp - 299, timestamp]`; whatever remains in the queue is exactly the answer, so its size is the count.

**Steps:**
1. `hit(timestamp)`: add `timestamp` to the back of the queue.
2. `getHits(timestamp)`: while the queue is non-empty and its front element is `< timestamp - 299`, remove it (it is outside the window). Return the queue's current size.

**Why popping expired entries lazily (only on `getHits`, not eagerly on every `hit`) is correct and efficient:** an expired hit does no harm sitting in the queue between calls — it only needs to be gone *before* it would be counted. Cleaning up lazily, right before counting, means each timestamp is added once and removed at most once across the object's entire lifetime, so the *total* work across all calls stays O(total hits), not O(hits x queries).

## 4. Diagram

<svg viewBox="0 0 700 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A queue of hit timestamps; entries older than 300 seconds before the current timestamp are popped from the front before counting">
  <g font-family="sans-serif" font-size="12">
    <rect x="30" y="40" width="70" height="35" fill="#161b22" stroke="#f85149" stroke-dasharray="3,2"/><text x="65" y="62" fill="#e6edf3" text-anchor="middle" font-size="11">t=1</text>
    <rect x="110" y="40" width="70" height="35" fill="#161b22" stroke="#3fb950"/><text x="145" y="62" fill="#e6edf3" text-anchor="middle" font-size="11">t=2</text>
    <rect x="190" y="40" width="70" height="35" fill="#161b22" stroke="#3fb950"/><text x="225" y="62" fill="#e6edf3" text-anchor="middle" font-size="11">t=3</text>
    <rect x="270" y="40" width="70" height="35" fill="#161b22" stroke="#3fb950"/><text x="305" y="62" fill="#e6edf3" text-anchor="middle" font-size="11">t=300</text>
    <text x="65" y="100" fill="#f85149" text-anchor="middle" font-size="11">expired at getHits(301):</text>
    <text x="65" y="118" fill="#f85149" text-anchor="middle" font-size="11">301-299=2, so t=1 &lt; 2</text>
    <text x="450" y="70" fill="#79c0ff" text-anchor="middle">getHits(301): pop t=1, remaining size=3</text>
  </g>
</svg>

Only the front of the queue is ever checked for expiry — since timestamps arrive in order, anything still in the queue after popping the front is guaranteed to be within the window.

## 5. Runnable example

**Level 1 — Brute force.** Store every hit timestamp in a list; on each `getHits`, scan the entire list, counting entries within `[timestamp - 299, timestamp]`. O(total hits ever recorded) per query.

**KEY INSIGHT:** because hits arrive in non-decreasing timestamp order, a queue's front is always the oldest hit — expired entries can be discarded from the front in O(1) each, and each hit is discarded at most once across the whole run, so the *total* work stays proportional to the number of hits, not hits times queries.

**Level 2 — Optimal.** `Queue<Integer>` (an `ArrayDeque`), popping expired entries lazily before counting.

**Level 3 — Hardened.** Correctly handles multiple hits at the exact same timestamp (each is a separate queue entry, all counted), and a window boundary check using `< timestamp - 299` (not `<=`), matching the inclusive `[timestamp-299, timestamp]` range.

```java
// HitCounter.java
import java.util.*;

public class HitCounter {

    private final Queue<Integer> hits = new ArrayDeque<>();

    public void hit(int timestamp) {
        hits.offer(timestamp);
    }

    public int getHits(int timestamp) {
        while (!hits.isEmpty() && hits.peek() < timestamp - 299) {
            hits.poll();
        }
        return hits.size();
    }

    public static void main(String[] args) {
        HitCounter counter = new HitCounter();
        counter.hit(1);
        counter.hit(2);
        counter.hit(3);
        System.out.println(counter.getHits(4));   // 3
        counter.hit(300);
        System.out.println(counter.getHits(300)); // 4
        System.out.println(counter.getHits(301)); // 3, hit at t=1 expired
    }
}
```

**How to run:** save as `HitCounter.java`, then run `java HitCounter.java`.

## 6. Walkthrough

Trace `hit(1)`, `hit(2)`, `hit(3)`, `getHits(4)`, `hit(300)`, `getHits(300)`, `getHits(301)`:

| call | queue after call | popped (expired) | return |
|---|---|---|---|
| hit(1) | [1] | — | — |
| hit(2) | [1,2] | — | — |
| hit(3) | [1,2,3] | — | — |
| getHits(4) | [1,2,3] | none (`1 >= 4-299=-295`) | 3 |
| hit(300) | [1,2,3,300] | — | — |
| getHits(300) | [1,2,3,300] | none (`1 >= 300-299=1`) | 4 |
| getHits(301) | [2,3,300] | 1 (`1 < 301-299=2`) | 3 |

`getHits(301)` is the first call where the window's lower bound (`2`) exceeds the oldest recorded hit (`1`), so it is popped before counting — matching the expected drop from `4` to `3`.

## 7. Gotchas & takeaways

> Gotcha: using `<=` instead of `<` when checking `hits.peek() < timestamp - 299` would incorrectly discard a hit sitting exactly on the window's lower boundary — the window is inclusive of `timestamp - 299`, so that exact timestamp must still count.

- Signal: "count events within a trailing time/size window as new events arrive" is a sliding-window-over-a-queue signal, especially when arrivals are guaranteed to be in order.
- Lazy expiry (clean up only when queried, not on every insert) keeps total work proportional to total hits, not hits times queries.
- Related problems: Moving Average from Data Stream (a fixed-size sliding window instead of a fixed-time window), Number of Recent Calls (nearly identical, fixed 3000 ms window).
