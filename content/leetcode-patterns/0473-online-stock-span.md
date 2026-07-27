---
card: leetcode-patterns
gi: 473
slug: online-stock-span
title: Online Stock Span
---

## 1. What it is

You design a class `StockSpanner` that gets called once per day with that day's stock price. Each call returns the "span" — the number of consecutive days (ending today, counting today) where the price was less than or equal to today's price. Example: prices arrive as `100, 80, 60, 70, 60, 75, 85` → spans `1, 1, 1, 2, 1, 4, 6`.

## 2. Why & when

This is "next smaller element to the left," applied **online** (one call at a time, no full array available up front). It belongs to the [monotonic-stack signal](0466-monotonic-stack-signal-next-greater-smaller-element-or-histo.md) family: "consecutive days behind me were smaller or equal" is the span signal. Constraints: up to 10,000 calls to `next`.

## 3. Core concept

**Key idea:** maintain a decreasing stack of `(price, span)` pairs. When today's price arrives, pop every stacked entry whose price is less than or equal to today's, folding each popped entry's span into today's running span — those days are all "absorbed" because today's price also covers everything they covered.

**Steps:**
1. Maintain a stack of `(price, span)` pairs, decreasing by price from bottom to top.
2. On each new price: start `span = 1` (today counts itself).
3. While the stack is not empty and the top's price is less than or equal to today's price, pop it and add its span to today's running span.
4. Push `(todayPrice, span)`.
5. Return `span` as today's answer.

**Why folding spans works:** if an earlier day's price was less than or equal to today's, then every day *that* earlier day's span already covered also has a price less than or equal to today's (transitively, since today's price is at least as big as that earlier day's price, which was at least as big as everything in its span). So today's span can simply absorb the whole earlier span in O(1), instead of re-counting those days one by one.

## 4. Diagram

<svg viewBox="0 0 700 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Stack of price/span pairs folding into a running span as higher prices arrive">
  <g font-family="sans-serif" font-size="13">
    <text x="20" y="20" fill="#e6edf3" font-weight="bold">prices arrive: 100, 80, 60, 70, 60, 75, 85</text>
    <text x="20" y="45" fill="#8b949e">100: stack=[] -&gt; span=1. push (100,1). stack=[(100,1)]</text>
    <text x="20" y="65" fill="#8b949e">80: top(100,1), 100&gt;80 no pop -&gt; span=1. push (80,1)</text>
    <text x="20" y="85" fill="#8b949e">60: top(80,1), 80&gt;60 no pop -&gt; span=1. push (60,1)</text>
    <text x="20" y="105" fill="#8b949e">70: pop (60,1) since 60&lt;=70 -&gt; span=1+1=2. push (70,2)</text>
    <text x="20" y="125" fill="#8b949e">60: top(70,2), 70&gt;60 no pop -&gt; span=1. push (60,1)</text>
    <text x="20" y="145" fill="#8b949e">75: pop(60,1)->span=2; pop(70,2)->span=4 -&gt; push (75,4)</text>
    <text x="20" y="170" fill="#3fb950">85: pop(75,4)->span=5; pop(80,1)->span=6 -&gt; push (85,6). spans: 1,1,1,2,1,4,6</text>
  </g>
</svg>

Each pop folds a whole earlier span into today's, because today's price covers everything that earlier price already covered.

## 5. Runnable example

**Level 1 — Brute force.** On each call, scan backward from today counting consecutive days with price less than or equal to today's. O(n) per call, O(n²) total.

**KEY INSIGHT:** an earlier day's span can be folded into today's in O(1) once you know today's price is at least as big as that earlier day's price — you never need to re-examine the individual days inside that earlier span.

**Level 2 — Optimal.** Stack of `(price, span)` pairs, amortized O(1) per call.

**Level 3 — Hardened.** Handles a strictly decreasing sequence of prices (every span stays `1`) and a strictly increasing sequence (spans grow to cover the whole history).

```java
// StockSpanner.java
import java.util.*;

public class StockSpanner {

    private final Deque<int[]> stack = new ArrayDeque<>(); // each entry: {price, span}

    // Level 2 & 3: monotonic stack of (price, span), amortized O(1)
    public int next(int price) {
        int span = 1;
        while (!stack.isEmpty() && stack.peek()[0] <= price) {
            span += stack.pop()[1];
        }
        stack.push(new int[]{price, span});
        return span;
    }

    // Level 1: brute force reference, O(n) per call, using the full history
    static int bruteForceSpan(List<Integer> history) {
        int today = history.size() - 1;
        int span = 1;
        for (int i = today - 1; i >= 0 && history.get(i) <= history.get(today); i--) {
            span++;
        }
        return span;
    }

    public static void main(String[] args) {
        int[] prices = {100, 80, 60, 70, 60, 75, 85};
        StockSpanner spanner = new StockSpanner();
        List<Integer> history = new ArrayList<>();

        System.out.print("optimal spans:      ");
        for (int p : prices) System.out.print(spanner.next(p) + " ");
        System.out.println();

        System.out.print("brute force spans:  ");
        for (int p : prices) {
            history.add(p);
            System.out.print(bruteForceSpan(history) + " ");
        }
        System.out.println();

        StockSpanner decreasing = new StockSpanner();
        System.out.println("strictly decreasing prices, spans: "
            + decreasing.next(50) + " " + decreasing.next(40) + " " + decreasing.next(30));
    }
}
```

**How to run:** save as `StockSpanner.java`, then run `java StockSpanner.java`.

## 6. Walkthrough

Trace calls to `next` on `100, 80, 60, 70, 60, 75, 85`:

| call | price | stack before | action | stack after | span returned |
|---|---|---|---|---|---|
| 1 | 100 | [] | push (100,1) | [(100,1)] | 1 |
| 2 | 80 | [(100,1)] | 100>80, no pop; push (80,1) | [(100,1),(80,1)] | 1 |
| 3 | 60 | [...,(80,1)] | 80>60, no pop; push (60,1) | [...,(60,1)] | 1 |
| 4 | 70 | [...,(60,1)] | pop (60,1), span=2; 80>70, stop; push (70,2) | [(100,1),(80,1),(70,2)] | 2 |
| 5 | 60 | [...,(70,2)] | 70>60, no pop; push (60,1) | [...,(70,2),(60,1)] | 1 |
| 6 | 75 | [...,(60,1)] | pop(60,1) span=2; pop(70,2) span=4; 80>75, stop; push (75,4) | [(100,1),(80,1),(75,4)] | 4 |
| 7 | 85 | [(100,1),(80,1),(75,4)] | pop(75,4) span=5; pop(80,1) span=6; 100>85, stop; push (85,6) | [(100,1),(85,6)] | 6 |

Spans returned across all seven calls: `1, 1, 1, 2, 1, 4, 6`, matching the expected output.

## 7. Gotchas & takeaways

> Gotcha: forgetting to include today itself in the span (starting `span` at `0` instead of `1`) undercounts every answer by one — today's own day always counts toward its own span.

- "Consecutive days behind me that were smaller or equal" is the span signal — a next-smaller-to-the-left query answered by folding spans, not by re-scanning history.
- The stack must store both price and span together, since a fold needs the earlier span's size, not just its price.
- Time: amortized O(1) per call, O(n) total across n calls, because each entry is pushed once and popped at most once.
