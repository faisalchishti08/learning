---
card: leetcode-patterns
gi: 570
slug: my-calendar-iii
title: My Calendar III
---

## 1. What it is

Like [My Calendar I](0565-my-calendar-i.md) and [My Calendar II](0566-my-calendar-ii.md), but every booking is always accepted — there is no rejection. Instead, `book(start, end)` returns the **maximum number of events overlapping at any single point in time**, considering all bookings made so far (a "k-booking," where `k` is that maximum overlap count). Example: `book(10,20)` → `1`; `book(50,60)` → `1`; `book(10,40)` → `2`; `book(5,15)` → `3` (three events now all cover the point `10`).

## 2. Why & when

This needs the actual running **maximum overlap depth**, updated after every insertion — not just a yes/no overlap check. That is exactly what a [segment tree](0561-segment-tree-bit-template-segment-tree-or-fenwick-tree-over.md) with **range-add, range-max** support (using lazy propagation) computes directly. Since the coordinate range can be up to `10^9` but the number of bookings is small (up to 400), a **dynamic segment tree** — one that creates its nodes only where needed, instead of pre-allocating an array over the full range — is the right implementation. Constraints: up to 400 calls to `book`.

## 3. Core concept

**Key idea:** build a segment tree over the value range `[0, 10^9]`, where each node stores `max` (the maximum overlap count anywhere in its range, **including** any pending lazy add) and `lazy` (a pending "add 1 to this entire range" not yet pushed to children). A `book(start, end)` call is a single range-add of `+1` over `[start, end-1]`; after applying it, the tree's root `max` value is the answer.

**Steps:**
1. Represent each tree node with `left`, `right` child pointers (created lazily, only when recursion actually needs them), plus `max` and `lazy` fields, both starting at `0`.
2. To apply a booking `[start, end)`: call `update(root, 0, 1e9, start, end - 1)` (converting the half-open interval to an inclusive one).
3. In `update`: if the current node's range is fully outside `[left, right]`, return immediately. If fully inside, increment both `max` and `lazy` by `1` and return (deferring the update to children).
4. Otherwise, ensure both children exist (create them if not), recurse into each, then recompute `node.max = node.lazy + Math.max(leftChild.max, rightChild.max)` — the node's own pending lazy amount, plus whichever child currently has the higher max.
5. After the call, return `root.max` — the current global maximum overlap depth.

**Why `node.max = node.lazy + max(children)` is correct without a separate "push down" step for queries:** every node's `max` value already accounts for its own pending lazy add, combined with the best its children can offer (which themselves already account for *their* lazy adds, recursively). Since the only thing ever read is the root's `max` (there is no need to query an arbitrary sub-range separately), a full push-down to leaves is never required — the recursive recombination on the way back up keeps the root's value correct after every update.

## 4. Diagram

<svg viewBox="0 0 700 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Range-add of +1 applied recursively; nodes fully inside the target range increment their own max and lazy without descending further">
  <g font-family="sans-serif" font-size="12">
    <rect x="250" y="10" width="200" height="35" rx="4" fill="#161b22" stroke="#3fb950"/>
    <text x="350" y="32" fill="#e6edf3" text-anchor="middle">root [0, 1e9]: max = lazy + max(children)</text>
    <rect x="80" y="70" width="200" height="35" rx="4" fill="#161b22" stroke="#f0883e"/>
    <text x="180" y="92" fill="#e6edf3" text-anchor="middle">fully inside target: max++, lazy++</text>
    <rect x="420" y="70" width="200" height="35" rx="4" fill="#161b22" stroke="#30363d"/>
    <text x="520" y="92" fill="#e6edf3" text-anchor="middle">outside target: unchanged, return</text>
    <line x1="350" y1="45" x2="180" y2="70" stroke="#8b949e"/>
    <line x1="350" y1="45" x2="520" y2="70" stroke="#8b949e"/>
    <text x="350" y="150" fill="#79c0ff" text-anchor="middle">nodes are created on demand, only along paths the updates actually touch</text>
  </g>
</svg>

Only nodes along the path of an actual update are ever created, keeping the tree's real size proportional to the number of bookings, not the coordinate range.

## 5. Runnable example

**Level 1 — Brute force.** Maintain a `TreeMap` of `+1`/`-1` deltas at each event's start/end (a sweep line), and after every booking, re-scan the entire map from the beginning, tracking a running sum and its maximum. O(n) per call, O(n²) total.

**KEY INSIGHT:** a dynamic segment tree with lazy propagation for range-add and range-max avoids the full rescan on every call, updating and re-querying the maximum in O(log(coordinate range)) instead.

**Level 2 — Optimal.** Dynamic segment tree, O(log(coordinate range)) per call (roughly `30` levels for a `10^9` range).

**Level 3 — Hardened.** Handles overlapping bookings that do not increase the global maximum (still correctly updates local counts), and bookings far apart in coordinate space (nodes for unrelated regions are never created).

```java
// MyCalendarIII.java
public class MyCalendarIII {

    static class Node {
        Node left, right;
        int max = 0;
        int lazy = 0;
    }

    Node root = new Node();
    static final int RANGE_END = 1_000_000_000;

    public int book(int start, int end) {
        update(root, 0, RANGE_END, start, end - 1);
        return root.max;
    }

    void update(Node node, int nodeStart, int nodeEnd, int left, int right) {
        if (right < nodeStart || nodeEnd < left) return; // fully outside
        if (left <= nodeStart && nodeEnd <= right) {      // fully inside
            node.max++;
            node.lazy++;
            return;
        }
        int mid = nodeStart + (nodeEnd - nodeStart) / 2;
        if (node.left == null) node.left = new Node();
        if (node.right == null) node.right = new Node();
        update(node.left, nodeStart, mid, left, right);
        update(node.right, mid + 1, nodeEnd, left, right);
        node.max = node.lazy + Math.max(node.left.max, node.right.max);
    }

    public static void main(String[] args) {
        MyCalendarIII cal = new MyCalendarIII();
        System.out.println(cal.book(10, 20)); // 1
        System.out.println(cal.book(50, 60)); // 1
        System.out.println(cal.book(10, 40)); // 2
        System.out.println(cal.book(5, 15));  // 3
        System.out.println(cal.book(5, 10));  // 3
        System.out.println(cal.book(25, 55)); // 3
    }
}
```

**How to run:** save as `MyCalendarIII.java`, then run `java MyCalendarIII.java`.

## 6. Walkthrough

Trace `book(10,20)`, `book(50,60)`, `book(10,40)`:

1. `book(10,20)`: `update(root, 0, 1e9, 10, 19)`. Recursion splits the huge range down until it reaches sub-ranges fully inside `[10,19]`; each of those increments its own `max` and `lazy` to `1`. Recombining back up, `root.max = 1`. Return `1`.
2. `book(50,60)`: `update(root, 0, 1e9, 50, 59)`. This touches a disjoint set of nodes from the first call (different region of the coordinate space). Those nodes' `max` becomes `1`. Recombining, `root.max = max(1, 1) = 1`. Return `1`.
3. `book(10,40)`: `update(root, 0, 1e9, 10, 39)`. This range overlaps `[10,19]` (pushing those nodes' `max` to `2`) and also covers new territory `[20,39]` (those nodes' `max` becomes `1`). Recombining up through the tree, the highest value found is `2` (from the `[10,19]` region). `root.max = 2`. Return `2`.

## 7. Gotchas & takeaways

> Gotcha: pre-allocating a segment tree as a fixed array sized to the full coordinate range (`10^9`) would need billions of array slots — infeasible. The dynamic (node-on-demand) approach keeps actual memory usage proportional to the number of bookings times the tree depth, not the coordinate range itself.

- Signal: "return the current maximum overlap/depth after every update," on a huge coordinate range but with few actual updates, is the classic use case for a dynamic (pointer-based) segment tree with lazy propagation.
- `node.max = node.lazy + max(children.max)`, recomputed on the way back up after every update, keeps the root's value correct without a separate query pass.
- Related problems: My Calendar I and II (the simpler boolean/limited-overlap versions), Falling Squares (a similar range-update, range-max problem in a different framing).
