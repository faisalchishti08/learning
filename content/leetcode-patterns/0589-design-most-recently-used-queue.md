---
card: leetcode-patterns
gi: 589
slug: design-most-recently-used-queue
title: Design Most Recently Used Queue
---

## 1. What it is

Design a `MRUQueue` (Most Recently Used Queue) initialized with `n` elements valued `1..n` in order. `fetch(k)` returns the `k`-th element (1-indexed) of the current queue, then **moves that element to the end** of the queue (marking it as most recently used). Example: `n=8`; `fetch(3)` → `3`, and the queue becomes `[1,2,4,5,6,7,8,3]`; `fetch(5)` → now the 5th element is `6` (since `3` moved out of position 3), and the queue becomes `[1,2,4,5,7,8,3,6]`.

## 2. Why & when

A plain `ArrayList` gives O(1) access by index, but removing an element from the middle and appending it at the end both require shifting every element after the removed position — O(n) per `fetch`. Given the constraints (n up to 2,000, up to 2,000 calls), an O(n) `ArrayList` approach — shift-then-append, or equivalently `remove` then `add` — is fast enough (about 4 million total operations), so the "hardened" solution here is really about correctly implementing that O(n)-per-call approach rather than needing a fancier structure like a balanced BST-based order-statistics tree (which exists for stricter constraints, but adds complexity this problem's limits do not require).

## 3. Core concept

**Key idea:** back the queue with an `ArrayList<Integer>`, initialized to `1..n`. Each `fetch(k)` removes the element at index `k-1` (converting 1-indexed `k` to 0-indexed) and appends it to the end — `ArrayList.remove(index)` and `ArrayList.add(value)` do exactly this, with the JDK handling the internal shifting.

**Steps:**
1. Initialize `list = [1, 2, ..., n]`.
2. `fetch(k)`: read `value = list.remove(k - 1)` (removes and returns the element at 0-indexed position `k-1`, shifting later elements left).
3. Append it: `list.add(value)` (adds to the end).
4. Return `value`.

**Why removal must happen before re-insertion, not the reverse:** if you appended the value to the end first and then tried to remove it "from position `k-1`," the list's indices would have already shifted (the new element at the end changes nothing about earlier indices, but reasoning gets easier and less error-prone by always removing first, then appending the removed value — matching the problem's own description of the operation as "remove, then place at the end").

## 4. Diagram

<svg viewBox="0 0 700 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="fetch(3) removes the element at index 2 and appends it to the end, shifting later elements left">
  <g font-family="sans-serif" font-size="12">
    <text x="20" y="20" fill="#8b949e" font-size="11">before fetch(3):</text>
    <rect x="20" y="30" width="50" height="30" fill="#161b22" stroke="#30363d"/><text x="45" y="50" fill="#e6edf3" text-anchor="middle" font-size="10">1</text>
    <rect x="70" y="30" width="50" height="30" fill="#161b22" stroke="#30363d"/><text x="95" y="50" fill="#e6edf3" text-anchor="middle" font-size="10">2</text>
    <rect x="120" y="30" width="50" height="30" fill="#161b22" stroke="#f0883e"/><text x="145" y="50" fill="#e6edf3" text-anchor="middle" font-size="10">3</text>
    <rect x="170" y="30" width="50" height="30" fill="#161b22" stroke="#30363d"/><text x="195" y="50" fill="#e6edf3" text-anchor="middle" font-size="10">4</text>
    <text x="20" y="90" fill="#8b949e" font-size="11">after fetch(3):</text>
    <rect x="20" y="100" width="50" height="30" fill="#161b22" stroke="#30363d"/><text x="45" y="120" fill="#e6edf3" text-anchor="middle" font-size="10">1</text>
    <rect x="70" y="100" width="50" height="30" fill="#161b22" stroke="#30363d"/><text x="95" y="120" fill="#e6edf3" text-anchor="middle" font-size="10">2</text>
    <rect x="120" y="100" width="50" height="30" fill="#161b22" stroke="#30363d"/><text x="145" y="120" fill="#e6edf3" text-anchor="middle" font-size="10">4</text>
    <rect x="400" y="100" width="50" height="30" fill="#161b22" stroke="#f0883e"/><text x="425" y="120" fill="#e6edf3" text-anchor="middle" font-size="10">3</text>
    <text x="425" y="145" fill="#f0883e" text-anchor="middle" font-size="10">moved to the end</text>
  </g>
</svg>

`ArrayList.remove(index)` and `.add(value)` handle the shift and append directly — every later element moves one position left to fill the gap.

## 5. Runnable example

**Level 1 — Brute force.** Manually shift array elements with a raw loop instead of using `ArrayList`'s built-in `remove`/`add` — functionally the same O(n) cost, just more code to get right (off-by-one errors in the shift loop are a common mistake).

**KEY INSIGHT:** the problem's constraints (n, calls both up to 2,000) make an O(n)-per-call approach fast enough — there is no need for a fancier order-statistics structure; the real task is using the right built-in operations (`remove`, `add`) correctly and efficiently.

**Level 2 — Optimal (for these constraints).** `ArrayList<Integer>`, using `remove(index)` then `add(value)` directly.

**Level 3 — Hardened.** Correctly converts the 1-indexed `k` to a 0-indexed list position (`k - 1`) on every call, and correctly appends the *removed value*, not a stale reference or the original index.

```java
// MRUQueue.java
import java.util.*;

public class MRUQueue {

    private final List<Integer> list = new ArrayList<>();

    public MRUQueue(int n) {
        for (int i = 1; i <= n; i++) list.add(i);
    }

    public int fetch(int k) {
        int value = list.remove(k - 1); // 1-indexed k -> 0-indexed position
        list.add(value);
        return value;
    }

    public static void main(String[] args) {
        MRUQueue queue = new MRUQueue(8);
        System.out.println(queue.fetch(3)); // 3, list becomes [1,2,4,5,6,7,8,3]
        System.out.println(queue.fetch(5)); // 6, list becomes [1,2,4,5,7,8,3,6]
    }
}
```

**How to run:** save as `MRUQueue.java`, then run `java MRUQueue.java`.

## 6. Walkthrough

Trace `n=8`; `fetch(3)`, `fetch(5)`:

1. Initial list: `[1,2,3,4,5,6,7,8]`.
2. `fetch(3)`: `list.remove(3-1=2)` removes and returns `3` (the element at index `2`), shifting `4,5,6,7,8` left by one. List is now `[1,2,4,5,6,7,8]`. `list.add(3)` appends it. List: `[1,2,4,5,6,7,8,3]`. Return `3`.
3. `fetch(5)`: `list.remove(5-1=4)` — index `4` in `[1,2,4,5,6,7,8,3]` is `6`. Remove it, shifting `7,8,3` left. List is now `[1,2,4,5,7,8,3]`. `list.add(6)` appends it. List: `[1,2,4,5,7,8,3,6]`. Return `6`.

## 7. Gotchas & takeaways

> Gotcha: forgetting the 1-indexed-to-0-indexed conversion (calling `list.remove(k)` instead of `list.remove(k - 1)`) fetches and moves the wrong element — always subtract `1` before indexing into the 0-indexed `ArrayList`.

- Signal: "repeatedly access by rank/position, then move that element to a recency-tracked end" with modest constraints is the direct `ArrayList.remove`-then-`add` signal.
- For larger constraints than this problem's (n, calls each in the low thousands), the same operation would need an order-statistics data structure (like a Fenwick-tree-indexed balanced structure) to beat O(n) per call — not required here.
- Related problems: LRU Cache (a similar "move to the recent end" idea, but keyed by lookup rather than by positional rank).
