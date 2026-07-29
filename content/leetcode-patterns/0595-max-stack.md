---
card: leetcode-patterns
gi: 595
slug: max-stack
title: Max Stack
---

## 1. What it is

Design a `MaxStack` class supporting the usual stack operations — `push(val)`, `pop()`, `top()` — plus `peekMax()` (return the current maximum without removing it) and `popMax()` (remove **and return** the current maximum, even if it is not at the top of the stack). Example: `push(5)`, `push(1)`, `push(5)`, `top()` → `5`, `popMax()` → `5` (removes the top `5`, since it is the topmost of the tied maximums), `top()` → `1`, `peekMax()` → `5` (the remaining `5`, still in the stack below).

## 2. Why & when

[Min Stack](0581-min-stack.md)'s parallel-shadow-stack trick gives O(1) `peekMax`, but `popMax` breaks that trick: removing the maximum might mean removing an element from the **middle** of the stack (not the top), which a plain stack cannot do in O(1). This needs a structure that supports "remove an arbitrary element" fast — a balanced ordered structure like a `TreeMap`, paired with a way to still support normal `push`/`pop`/`top` stack order.

## 3. Core concept

**Key idea:** assign every pushed value a unique, increasing sequence ID (to break ties and to know push order, since normal `pop` must respect insertion order — the most recently pushed element, not the smallest ID). Maintain a `TreeMap<value, TreeSet<id>>` — a sorted map from value to the set of IDs currently holding that value — alongside a `TreeMap<id, value>` sorted by ID, which behaves like the stack itself (its largest key is the top).

**Steps:**
1. `push(val)`: assign a new `id = idCounter++`. Insert `(id, val)` into `idToVal` (a `TreeMap`, so its largest key is always the current top). Insert `id` into `valToIds[val]` (a `TreeMap<value, TreeSet<id>>`).
2. `pop()`: find the largest `id` in `idToVal` (its `lastKey()`), remove it from `idToVal`, and remove that `id` from `valToIds[value]` (removing the value's whole entry from `valToIds` if its ID set becomes empty). Return the removed value.
3. `top()`: return `idToVal.lastEntry().getValue()` without removing anything.
4. `peekMax()`: return `valToIds.lastKey()` — the largest value currently present.
5. `popMax()`: find the max value, `valToIds.lastKey()`. Among IDs holding that value, take the largest one (`valToIds.get(maxValue).last()`) — this is the topmost occurrence of the max value, matching "remove the max that is closest to the top when tied." Remove that `id` from both `idToVal` and `valToIds`. Return the max value.

**Why two `TreeMap`s, keyed oppositely, are both needed:** `idToVal` (keyed by insertion order) answers "what is on top" — required for normal stack behavior. `valToIds` (keyed by value) answers "what is the maximum, and which occurrence of it is topmost" — required for `popMax`. Neither structure alone answers both questions in O(log n); together, kept in sync on every mutation, they do.

## 4. Diagram

<svg viewBox="0 0 700 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Two TreeMaps: one by insertion id giving stack order, one by value giving max order, both updated together">
  <g font-family="sans-serif" font-size="12">
    <text x="150" y="20" fill="#8b949e" text-anchor="middle">idToVal (stack order)</text>
    <rect x="30" y="30" width="70" height="30" fill="#161b22" stroke="#30363d"/><text x="65" y="50" fill="#e6edf3" text-anchor="middle" font-size="10">id0:5</text>
    <rect x="110" y="30" width="70" height="30" fill="#161b22" stroke="#30363d"/><text x="145" y="50" fill="#e6edf3" text-anchor="middle" font-size="10">id1:1</text>
    <rect x="190" y="30" width="70" height="30" fill="#161b22" stroke="#3fb950"/><text x="225" y="50" fill="#e6edf3" text-anchor="middle" font-size="10">id2:5 (top)</text>
    <text x="530" y="20" fill="#8b949e" text-anchor="middle">valToIds (by value)</text>
    <rect x="410" y="30" width="240" height="30" fill="#161b22" stroke="#f0883e"/><text x="530" y="50" fill="#e6edf3" text-anchor="middle" font-size="11">5 -&gt; {id0, id2}, 1 -&gt; {id1}</text>
    <text x="350" y="110" fill="#79c0ff" text-anchor="middle">popMax(): maxValue=5, topmost id among {id0,id2} is id2 -&gt; remove id2 from both maps</text>
    <text x="350" y="140" fill="#8b949e" text-anchor="middle" font-size="11">after popMax: idToVal={id0:5, id1:1}; top() now returns 1</text>
  </g>
</svg>

`valToIds`'s per-value ID set picks out exactly which occurrence to remove when values tie — the one with the largest ID, since IDs increase with insertion order.

## 5. Runnable example

**Level 1 — Brute force.** A plain stack (`ArrayDeque`) plus, for `popMax`, a linear scan to find the maximum's position, then pop-and-hold every element above it, remove the max, and push the held elements back. O(n) per `popMax`.

**KEY INSIGHT:** removing an arbitrary element from the "middle" of a stack in less than O(n) requires a structure with fast arbitrary removal — pairing a value-sorted `TreeMap` (to find the max, and which occurrence of it) with an ID-sorted `TreeMap` (to preserve stack order) gives O(log n) removal from anywhere, not just the top.

**Level 2 — Optimal.** Two `TreeMap`s as described, O(log n) for every method.

**Level 3 — Hardened.** Correctly picks the *largest ID* among tied maximum values for `popMax` (the topmost occurrence, matching stack semantics for ties), and correctly removes a value's entire `valToIds` entry when its ID set becomes empty (avoiding a stale, empty entry from being read as still present).

```java
// MaxStack.java
import java.util.*;

public class MaxStack {

    private int idCounter = 0;
    private final TreeMap<Integer, Integer> idToVal = new TreeMap<>();      // id -> value, stack order
    private final TreeMap<Integer, TreeSet<Integer>> valToIds = new TreeMap<>(); // value -> ids holding it

    public void push(int val) {
        int id = idCounter++;
        idToVal.put(id, val);
        valToIds.computeIfAbsent(val, k -> new TreeSet<>()).add(id);
    }

    public int pop() {
        int id = idToVal.lastKey();
        int val = idToVal.remove(id);
        removeId(val, id);
        return val;
    }

    public int top() {
        return idToVal.lastEntry().getValue();
    }

    public int peekMax() {
        return valToIds.lastKey();
    }

    public int popMax() {
        int maxVal = valToIds.lastKey();
        int id = valToIds.get(maxVal).last(); // topmost occurrence of the max
        idToVal.remove(id);
        removeId(maxVal, id);
        return maxVal;
    }

    private void removeId(int val, int id) {
        TreeSet<Integer> ids = valToIds.get(val);
        ids.remove(id);
        if (ids.isEmpty()) valToIds.remove(val);
    }

    public static void main(String[] args) {
        MaxStack stack = new MaxStack();
        stack.push(5);
        stack.push(1);
        stack.push(5);
        System.out.println(stack.top());     // 5
        System.out.println(stack.popMax());  // 5, removes the top 5
        System.out.println(stack.top());     // 1
        System.out.println(stack.peekMax()); // 5, the remaining 5 below
    }
}
```

**How to run:** save as `MaxStack.java`, then run `java MaxStack.java`.

## 6. Walkthrough

Trace `push(5)`, `push(1)`, `push(5)`, `popMax()`, `top()`:

| call | idToVal | valToIds | return |
|---|---|---|---|
| push(5) | {0:5} | {5:{0}} | — |
| push(1) | {0:5, 1:1} | {5:{0}, 1:{1}} | — |
| push(5) | {0:5, 1:1, 2:5} | {5:{0,2}, 1:{1}} | — |
| popMax() | maxVal=5; topmost id among {0,2} is 2; remove id 2 -> {0:5, 1:1} | {5:{0}, 1:{1}} | 5 |
| top() | (unchanged) | (unchanged) | 1 |

`popMax` correctly removes the `id=2` occurrence of `5` (the top one), not `id=0`'s occurrence, because `valToIds.get(5).last()` picks the largest (most recently pushed) ID among the tied values.

## 7. Gotchas & takeaways

> Gotcha: implementing `popMax` by taking `valToIds.get(maxVal).first()` instead of `.last()` removes the *oldest* occurrence of the max value instead of the topmost one — for tied maximum values, the problem expects the one closest to the top of the stack (the most recently pushed) to be removed, matching normal stack-like behavior for ties.

- Signal: "stack behavior, plus fast access to and removal of the current maximum from anywhere in the stack" is the two-TreeMap (by-id and by-value) signal — beyond what a single shadow stack (as in Min Stack) can do.
- Every mutation (`push`, `pop`, `popMax`) must update both `TreeMap`s together, or they desync and later queries return stale answers.
- Related problems: Min Stack (the simpler O(1)-peek-only version, with no removal-from-the-middle requirement).
