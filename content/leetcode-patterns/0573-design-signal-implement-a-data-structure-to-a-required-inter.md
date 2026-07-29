---
card: leetcode-patterns
gi: 573
slug: design-signal-implement-a-data-structure-to-a-required-inter
title: Design — signal: implement a data structure to a required interface
---

## 1. What it is

"Design" problems ask you to build a class that exposes a specific public interface — a fixed set of methods with fixed signatures, like `get(key)` and `put(key, value)` for a cache, or `push`, `pop`, and `top` for a stack. There is no single algorithm to apply; instead you pick and combine existing data structures (hash maps, linked lists, heaps, arrays) so every required method runs within its stated time limit.

## 2. Why & when

Recognize a Design problem by its shape: the prompt names a class (`LRUCache`, `MyHashMap`, `Trie`), lists the methods it must support, and states a complexity requirement for each one (usually "O(1) average" or "O(log n)"). This differs from a normal LeetCode problem, which asks for one function that returns one answer — a Design problem asks for a small, stateful *system* that answers a sequence of calls, where earlier calls affect the state seen by later calls.

Signals to watch for in the problem statement:

- **"Implement a class `X` with the following methods..."** — the direct definition of a Design problem.
- **Multiple methods sharing state** — a `get` that must see the effects of a prior `put`, or a `pop` that must undo the most recent `push`. If methods were independent, this would just be a set of separate problems.
- **A stated complexity per method** — "each operation should run in O(1) average time" tells you which structures are even viable (an array with linear scans is disqualified; a hash map is a candidate).
- **The class re-implements a familiar structure "from scratch"** ("Design HashMap", "Design Linked List") — the problem wants you to reproduce, by hand, behavior a language's standard library normally gives you for free, without using that library type directly.

The alternative — solving each method call independently with no shared state — does not apply here; every Design problem's whole point is maintaining state correctly and efficiently across a sequence of calls.

## 3. Core concept

**Key idea:** treat the required interface as a set of constraints, then work backward to the combination of structures that satisfies all of them at once. A single structure rarely satisfies every method's complexity requirement alone — the skill is *composing* two or three structures so each one's strength covers the others' weakness.

**A repeatable process:**
1. List every method in the interface and its required complexity.
2. For each method, ask which structure gives that complexity: O(1) lookup by key → hash map; O(1) insert/remove at both ends → doubly linked list or array deque; O(log n) min/max → heap; O(1) access by index → array.
3. Find the overlap: if `get` needs O(1) lookup **and** `put` needs to evict the least-recently-used entry in O(1), no single structure does both — but a hash map (for lookup) plus a doubly linked list (for O(1) reordering) together do.
4. Keep the structures in sync: every mutation must update all of them consistently, or the composed structure breaks its own invariants.

**Why composition, not one clever structure:** each base structure is optimized for one access pattern. A hash map is fast to look up by key but has no notion of order. A linked list has fast reordering but no fast lookup by key. Pairing them lets each cover the other's blind spot.

## 4. Diagram

<svg viewBox="0 0 700 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A hash map and a doubly linked list composed together, each covering the other's weakness">
  <g font-family="sans-serif" font-size="12">
    <rect x="30" y="30" width="260" height="60" rx="6" fill="#161b22" stroke="#3fb950"/>
    <text x="160" y="55" fill="#e6edf3" text-anchor="middle">HashMap&lt;key, node&gt;</text>
    <text x="160" y="75" fill="#8b949e" text-anchor="middle" font-size="11">O(1) lookup by key</text>
    <rect x="410" y="30" width="260" height="60" rx="6" fill="#161b22" stroke="#f0883e"/>
    <text x="540" y="55" fill="#e6edf3" text-anchor="middle">Doubly linked list</text>
    <text x="540" y="75" fill="#8b949e" text-anchor="middle" font-size="11">O(1) move/remove given a node</text>
    <line x1="290" y1="60" x2="410" y2="60" stroke="#79c0ff" stroke-width="2" marker-end="url(#arrow)"/>
    <defs>
      <marker id="arrow" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
        <path d="M0,0 L6,3 L0,6 Z" fill="#79c0ff"/>
      </marker>
    </defs>
    <text x="350" y="45" fill="#79c0ff" text-anchor="middle" font-size="11">map value is a node reference</text>
    <text x="350" y="140" fill="#e6edf3" text-anchor="middle">get(key): map finds the node in O(1); list moves it to the front in O(1)</text>
    <text x="350" y="165" fill="#8b949e" text-anchor="middle" font-size="11">neither structure alone satisfies both requirements</text>
  </g>
</svg>

The hash map answers "where is this key" instantly; the linked list answers "what should be evicted next" instantly. Together they satisfy an interface neither could satisfy alone.

## 5. Runnable example

### Signal-checker

The artifact below shows the decision in code: a naive single-array approach fails the O(1) requirement for random-key lookup, while a hash-map-plus-array combination meets it.

```java
// DesignSignal.java
import java.util.*;

public class DesignSignal {

    // Naive: linear scan to find a key - O(n) per get, violates an O(1) requirement.
    static class NaiveStore {
        List<int[]> entries = new ArrayList<>(); // [key, value]
        int get(int key) {
            for (int[] e : entries) {
                if (e[0] == key) return e[1];
            }
            return -1;
        }
        void put(int key, int value) {
            for (int[] e : entries) {
                if (e[0] == key) { e[1] = value; return; }
            }
            entries.add(new int[]{key, value});
        }
    }

    // Composed: HashMap gives O(1) average lookup, satisfying the interface's stated bound.
    static class ComposedStore {
        Map<Integer, Integer> map = new HashMap<>();
        int get(int key) {
            return map.getOrDefault(key, -1);
        }
        void put(int key, int value) {
            map.put(key, value);
        }
    }

    public static void main(String[] args) {
        NaiveStore naive = new NaiveStore();
        naive.put(1, 100);
        naive.put(2, 200);
        System.out.println("naive.get(2): " + naive.get(2)); // 200, but O(n) scan

        ComposedStore composed = new ComposedStore();
        composed.put(1, 100);
        composed.put(2, 200);
        System.out.println("composed.get(2): " + composed.get(2)); // 200, O(1) average
    }
}
```

**How to run:** save as `DesignSignal.java`, then run `java DesignSignal.java`.

## 6. Walkthrough

1. You read a problem naming a class and a list of methods, each with a stated complexity (for example, "get and put should each run in O(1) average time").
2. You check whether one structure satisfies every method. Here, a plain list satisfies neither `get` nor `put` in O(1), because both require scanning to find a matching key.
3. You swap in a hash map, which gives O(1) average lookup and insertion by key — matching the interface's requirement directly.
4. Both stores return the same answer (`200`) for `get(2)`, but only the hash-map version meets the stated time bound; the naive version is functionally correct yet fails the problem's actual requirement.
5. This is the general Design-problem loop: read the interface, read the complexity bound per method, and pick (or combine) structures until every bound is met.

## 7. Gotchas & takeaways

> Gotcha: getting the *correct answer* is not the same as solving a Design problem — if your structure returns right values but a required method runs in O(n) instead of the stated O(1), the solution is incomplete, even though it "works" on small inputs.

- Signal words: "implement a class," "design a data structure," "each operation should run in O(_)," a list of method signatures with shared state.
- The core skill is composition: pick one structure per requirement, then keep them in sync on every mutation.
- Related pattern-meta pages: [Design — template: compose maps, heaps, and linked lists for O(1)/O(log n) ops](0574-design-template-compose-maps-heaps-and-linked-lists-for-o-1.md), [Design — complexity: per-operation complexity is the goal](0575-design-complexity-per-operation-complexity-is-the-goal.md).
