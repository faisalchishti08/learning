---
card: data-structures
gi: 61
slug: linkedlist-vs-arraylist-tradeoffs
title: LinkedList vs ArrayList tradeoffs
---

## 1. What it is

`ArrayList` and `LinkedList` both implement Java's `List` interface, so they support the same methods — but they store elements completely differently. `ArrayList` backs its elements with a resizable array; `LinkedList` backs them with a chain of separately allocated nodes. Choosing between them means matching the structure to the access pattern your code actually uses.

## 2. Why & when

Picking the wrong one silently costs performance: using `ArrayList` where you constantly insert at the front means shifting every element on every insert; using `LinkedList` where you constantly read by index means walking half the chain on every read. This decision comes up any time you design a class around a list field, and in interviews as a direct "which would you use and why" question.

## 3. Core concept

**The decision criteria.**
- **Random access by index (`get(i)`)?** `ArrayList` is O(1); `LinkedList` is O(n).
- **Insert/remove at the front or middle, often?** `ArrayList` shifts every following element, O(n); `LinkedList` splices a node in O(1) once you are positioned there (e.g. via an iterator).
- **Insert/remove at the end, often?** Both are effectively O(1) amortized — `ArrayList.add` is O(1) amortized (occasional resize), `LinkedList.addLast` is O(1) always.
- **Memory overhead?** `ArrayList` stores values contiguously, with lower per-element overhead and better cache locality. `LinkedList` allocates a separate `Node` object per element, with extra pointer fields, and its nodes are scattered in memory — worse cache locality.
- **Iteration?** Both are O(n) total, but `ArrayList`'s contiguous memory makes iteration faster in practice, due to CPU cache effects.

**Rule of thumb.** Default to `ArrayList`. Reach for `LinkedList` only when you specifically need cheap insertion/removal at both ends combined with `List` semantics (or use `ArrayDeque` if you don't need `List` at all — it is usually faster than `LinkedList` for pure stack/queue use).

## 4. Diagram

<svg viewBox="0 0 640 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Decision tree: does the code need frequent indexed access, or frequent insertion at the ends or middle, choosing between ArrayList and LinkedList">
  <g font-family="sans-serif" font-size="11">
    <rect x="250" y="10" width="140" height="34" fill="#161b22" stroke="#8b949e" rx="4"/>
    <text x="320" y="31" fill="#e6edf3" text-anchor="middle" font-size="9">frequent get(i)?</text>
    <line x1="290" y1="44" x2="150" y2="90" stroke="#79c0ff" marker-end="url(#dt)"/>
    <text x="200" y="70" fill="#79c0ff" font-size="9">yes</text>
    <line x1="350" y1="44" x2="480" y2="90" stroke="#f0883e" marker-end="url(#dt)"/>
    <text x="430" y="70" fill="#f0883e" font-size="9">no</text>
    <defs><marker id="dt" markerWidth="8" markerHeight="8" refX="4" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#8b949e"/></marker></defs>
    <rect x="60" y="90" width="160" height="34" fill="#0d1117" stroke="#79c0ff" rx="4"/>
    <text x="140" y="111" fill="#e6edf3" text-anchor="middle" font-size="9">ArrayList</text>
    <rect x="400" y="90" width="180" height="34" fill="#0d1117" stroke="#f0883e" rx="4"/>
    <text x="490" y="111" fill="#e6edf3" text-anchor="middle" font-size="9">frequent insert at ends/middle?</text>
    <line x1="440" y1="124" x2="320" y2="170" stroke="#79c0ff" marker-end="url(#dt)"/>
    <text x="360" y="150" fill="#79c0ff" font-size="9">yes</text>
    <line x1="540" y1="124" x2="580" y2="170" stroke="#f0883e" marker-end="url(#dt)"/>
    <text x="565" y="150" fill="#f0883e" font-size="9">no</text>
    <rect x="240" y="170" width="160" height="34" fill="#0d1117" stroke="#79c0ff" rx="4"/>
    <text x="320" y="191" fill="#e6edf3" text-anchor="middle" font-size="9">LinkedList</text>
    <rect x="500" y="170" width="130" height="34" fill="#0d1117" stroke="#79c0ff" rx="4"/>
    <text x="565" y="191" fill="#e6edf3" text-anchor="middle" font-size="9">ArrayList (still fine)</text>
  </g>
</svg>

Random-access reads push you toward `ArrayList`; frequent insertion away from the end pushes you toward `LinkedList` — otherwise `ArrayList` is the safe default.

## 5. Runnable example

```java
// ListTradeoffsDemo.java
import java.util.ArrayList;
import java.util.LinkedList;
import java.util.List;

public class ListTradeoffsDemo {

    public static void main(String[] args) {
        int n = 50_000;

        // Scenario 1: insert 50,000 elements at the FRONT.
        long t0 = System.nanoTime();
        List<Integer> arrayList = new ArrayList<>();
        for (int i = 0; i < n; i++) arrayList.add(0, i); // shifts every existing element right, each time
        long arrayFrontMs = (System.nanoTime() - t0) / 1_000_000;

        t0 = System.nanoTime();
        List<Integer> linkedList = new LinkedList<>();
        for (int i = 0; i < n; i++) linkedList.add(0, i); // splices at head in O(1), no shifting
        long linkedFrontMs = (System.nanoTime() - t0) / 1_000_000;

        System.out.println("insert " + n + " at front -> ArrayList: " + arrayFrontMs + " ms, LinkedList: " + linkedFrontMs + " ms");

        // Scenario 2: read by index 50,000 times.
        t0 = System.nanoTime();
        long sum1 = 0;
        for (int i = 0; i < arrayList.size(); i++) sum1 += arrayList.get(i); // O(1) per get
        long arrayGetMs = (System.nanoTime() - t0) / 1_000_000;

        t0 = System.nanoTime();
        long sum2 = 0;
        for (int i = 0; i < linkedList.size(); i++) sum2 += linkedList.get(i); // O(n) per get -> O(n^2) total
        long linkedGetMs = (System.nanoTime() - t0) / 1_000_000;

        System.out.println("get(i) over " + n + " elements -> ArrayList: " + arrayGetMs + " ms, LinkedList: " + linkedGetMs + " ms");
        System.out.println("(checksum, ignore) " + sum1 + " " + sum2);
    }
}
```

**How to run:** save as `ListTradeoffsDemo.java`, then run `java ListTradeoffsDemo.java`. Timings vary by machine, but the pattern below is consistent.

## 6. Walkthrough

- **"Pick ArrayList because it's a read-heavy cache of user IDs, indexed by position."** Reads dominate, so O(1) `get(i)` on `ArrayList` wins; `LinkedList` would make every lookup O(n).
- **"Pick LinkedList because it's an undo history, where you push/pop only at one end."** Actually — reconsider. `ArrayDeque` is the better fit here: it supports push/pop at one end in O(1) like `LinkedList`, with none of the per-node object overhead. `LinkedList` is worth it specifically when you need both `List` behaviour (indexed access sometimes, iteration) *and* frequent front insertion in the same structure.
- **"Pick LinkedList because you're implementing an LRU cache's internal doubly linked list yourself."** Here you are not choosing the standard `LinkedList` at all — you would write your own node-based doubly linked list (see [Building a custom Node class](0060-building-a-custom-node-class.md)), because you need direct access to specific nodes (via a companion `HashMap<Key, Node>`) to unlink and relink them in O(1), which `java.util.LinkedList`'s public API does not expose.

In `main`, the front-insertion loop shows `LinkedList` finishing far faster than `ArrayList`, since each `ArrayList.add(0, ...)` shifts every prior element one slot right. The `get(i)` loop flips the result: `ArrayList` finishes fast at O(n) total, while `LinkedList` degrades to O(n²) total, since each `get(i)` walks from the nearer end.

## 7. Gotchas & takeaways

> Gotcha: `LinkedList.get(i)` silently costs O(n), and calling it in a loop turns an apparently O(n) algorithm into O(n²) — this is one of the most common accidental performance bugs with `LinkedList`. Always iterate with a `for-each` loop or an `Iterator` instead of indexed access when using `LinkedList`.

- `ArrayList`: O(1) indexed access, O(n) insert/remove at front or middle, better cache locality, less memory per element.
- `LinkedList`: O(1) insert/remove at either end (or mid-list via an iterator), O(n) indexed access, more memory per element (node objects + pointers).
- Default to `ArrayList` unless you specifically need cheap front/middle insertion combined with `List` semantics.
- For pure stack or queue behaviour without `List` semantics, prefer `ArrayDeque` over `LinkedList`.
- Related concepts: [java.util.LinkedList (List + Deque)](0059-java-util-linkedlist-list-deque.md), [Building a custom Node class](0060-building-a-custom-node-class.md).
