---
card: data-structures
gi: 180
slug: list-implementations-arraylist-linkedlist-vector
title: List implementations (ArrayList, LinkedList, Vector)
---

## 1. What it is

`ArrayList`, `LinkedList`, and `Vector` are the three main `List` implementations in `java.util`. All three guarantee insertion order and allow duplicates, matching the `List` contract, but they store data completely differently, giving very different performance for the same operations.

## 2. Why & when

Choosing between them is about matching the backing structure to your access pattern. `ArrayList` backs its data with a resizable array, so index-based reads (`get(i)`) are `O(1)`, but inserting in the middle requires shifting elements (`O(n)`). `LinkedList` backs its data with a [doubly linked list](0046-doubly-linked-list.md), so inserting or removing at a known position is `O(1)`, but `get(i)` must walk from an end (`O(n)`). `Vector` is functionally almost identical to `ArrayList`, but every method is `synchronized` — a legacy design from before Java's modern concurrency utilities, rarely the right choice today.

## 3. Core concept

**What backs each one.** `ArrayList`: a plain `Object[]` array that doubles in capacity when it fills up (see [amortized array doubling](0004-amortized-analysis-dynamic-array-doubling.md)). `LinkedList`: a chain of nodes, each holding a value plus `prev` and `next` references. `Vector`: the same array-backed design as `ArrayList`, but with `synchronized` on every mutating method.

**Ordering and complexity guarantees.** `ArrayList`: `get(i)`/`set(i, v)` are `O(1)`; `add`/`remove` at the end are amortized `O(1)`; `add`/`remove` in the middle are `O(n)` (must shift elements). `LinkedList`: `get(i)` is `O(n)` (must walk from the nearer end); `addFirst`/`addLast`/`removeFirst`/`removeLast` are `O(1)`; inserting at a position you already hold an iterator for is `O(1)`.

**When to choose which.** Choose `ArrayList` for anything that reads by index frequently — the vast majority of everyday code. Choose `LinkedList` specifically when you repeatedly insert or remove at the front, the back, or a position reached via iteration, and rarely need random index access — or, more commonly today, just use `ArrayDeque` for queue/stack behavior instead, since `LinkedList` carries extra per-node object overhead. Avoid `Vector` in new code; use `Collections.synchronizedList(new ArrayList<>())` or a `java.util.concurrent` structure if thread safety is genuinely needed.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="ArrayList backed by a contiguous array with O(1) index access, versus LinkedList backed by nodes with O(1) insertion at known positions">
  <g font-family="sans-serif" font-size="10" fill="#e6edf3">
    <text x="10" y="20">ArrayList: contiguous array</text>
    <rect x="20" y="30" width="40" height="30" fill="#161b22" stroke="#79c0ff"/><text x="40" y="50" text-anchor="middle">A</text>
    <rect x="60" y="30" width="40" height="30" fill="#161b22" stroke="#79c0ff"/><text x="80" y="50" text-anchor="middle">B</text>
    <rect x="100" y="30" width="40" height="30" fill="#161b22" stroke="#79c0ff"/><text x="120" y="50" text-anchor="middle">C</text>
    <text x="80" y="80" text-anchor="middle" font-size="8">get(1) -&gt; direct offset -&gt; O(1)</text>

    <text x="10" y="130">LinkedList: nodes with prev/next pointers</text>
    <circle cx="40" cy="160" r="16" fill="#161b22" stroke="#f0883e"/><text x="40" y="164" text-anchor="middle" font-size="8">A</text>
    <circle cx="120" cy="160" r="16" fill="#161b22" stroke="#f0883e"/><text x="120" y="164" text-anchor="middle" font-size="8">B</text>
    <circle cx="200" cy="160" r="16" fill="#161b22" stroke="#f0883e"/><text x="200" y="164" text-anchor="middle" font-size="8">C</text>
    <line x1="56" y1="160" x2="104" y2="160" stroke="#f0883e"/>
    <line x1="136" y1="160" x2="184" y2="160" stroke="#f0883e"/>
    <text x="400" y="164" font-size="8">insert after B (with a reference to B) -&gt; O(1)</text>
    <text x="400" y="180" font-size="8" fill="#8b949e">but get(2) must walk A-&gt;B-&gt;C -&gt; O(n)</text>
  </g>
</svg>

`ArrayList` computes any index directly; `LinkedList` must walk pointer by pointer to reach a position.

## 5. Runnable example

```java
// ListImplementations.java
import java.util.*;

public class ListImplementations {

    // Basic: common List operations working identically through the List interface.
    static void basicLevel() {
        List<String> arrayList = new ArrayList<>(List.of("a", "b", "c"));
        List<String> linkedList = new LinkedList<>(List.of("a", "b", "c"));

        arrayList.add(1, "x");
        linkedList.add(1, "x");

        System.out.println("basic: ArrayList after insert -> " + arrayList);
        System.out.println("basic: LinkedList after insert -> " + linkedList);
    }

    // Intermediate: measure the real performance gap for repeated front-insertion.
    static void intermediateLevel() {
        int n = 20_000;

        long startArray = System.nanoTime();
        List<Integer> arrayList = new ArrayList<>();
        for (int i = 0; i < n; i++) arrayList.add(0, i); // insert at front -- O(n) each time for ArrayList
        long arrayTime = System.nanoTime() - startArray;

        long startLinked = System.nanoTime();
        List<Integer> linkedList = new LinkedList<>();
        for (int i = 0; i < n; i++) linkedList.add(0, i); // insert at front -- O(1) each time for LinkedList
        long linkedTime = System.nanoTime() - startLinked;

        System.out.printf("intermediate: ArrayList front-insert x%d -> %.1f ms%n", n, arrayTime / 1_000_000.0);
        System.out.printf("intermediate: LinkedList front-insert x%d -> %.1f ms%n", n, linkedTime / 1_000_000.0);
    }

    // Advanced: use LinkedList as a Deque (stack + queue) versus ArrayDeque, the modern preferred choice.
    static void advancedLevel() {
        Deque<Integer> linkedDeque = new LinkedList<>();
        linkedDeque.addFirst(1);
        linkedDeque.addLast(2);
        linkedDeque.addFirst(0);
        System.out.println("advanced: LinkedList as Deque -> " + linkedDeque);

        Deque<Integer> arrayDeque = new ArrayDeque<>();
        arrayDeque.addFirst(1);
        arrayDeque.addLast(2);
        arrayDeque.addFirst(0);
        System.out.println("advanced: ArrayDeque (preferred today) -> " + arrayDeque);
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

How to run: `java ListImplementations.java`

## 6. Walkthrough

`arrayList.add(1, "x")` on `["a","b","c"]`: `ArrayList` shifts `"b"` and `"c"` one slot to the right to make room at index `1`, then places `"x"` there — an `O(n)` operation because of the shift. `linkedList.add(1, "x")` on the same logical content: `LinkedList` walks from the head to position `1` (two hops for a 3-element list), then splices in a new node by rewriting a few `prev`/`next` pointers — no shifting of other elements' storage, but the *walk* to find position `1` still costs `O(n)` in the worst case for an arbitrary index.

The real difference shows up in the `intermediateLevel` benchmark: repeatedly inserting at index `0`. For `ArrayList`, every single insert at the front must shift **all** existing elements right by one, making `n` insertions cost `O(n^2)` total. For `LinkedList`, `add(0, ...)` is a direct `addFirst`-equivalent operation — no walk needed, no shifting needed — making `n` insertions cost `O(n)` total. Running both and comparing the printed times shows this gap directly, and it grows dramatically as `n` increases.

The `advancedLevel` example shows `LinkedList` used through the `Deque` interface for stack/queue-like access at both ends — legitimate, but `ArrayDeque` typically outperforms it for this exact use case, since `ArrayDeque` avoids the per-element node allocation overhead that every `LinkedList` node carries.

**Complexity.** `ArrayList`: `get`/`set` `O(1)`; end `add` amortized `O(1)`; middle `add`/`remove` `O(n)`. `LinkedList`: `get`/`set` `O(n)`; `addFirst`/`addLast`/`removeFirst`/`removeLast` `O(1)`; middle `add`/`remove` `O(n)` to locate, `O(1)` to splice once located. `Vector`: same as `ArrayList`, plus synchronization overhead on every call.

## 7. Gotchas & takeaways

> Calling `get(i)` in a loop over a `LinkedList` (`for (int i = 0; i < list.size(); i++) list.get(i)`) silently turns an `O(n)` traversal into `O(n^2)`, because each `get(i)` re-walks from an end. Always use an iterator (`for (String s : list)`) or `ListIterator` for sequential access to a `LinkedList`.

- `ArrayList` is the correct default choice for almost all everyday code — reach for `LinkedList` only when you have a proven, specific need for `O(1)` insertion/removal at known positions and rarely need index access.
- `Vector` predates the Collections Framework and is functionally redundant with `ArrayList` plus external synchronization — avoid it in new code.
- For pure stack or queue behavior (push/pop, offer/poll at the ends only), prefer [ArrayDeque over LinkedList](0183-queue-deque-implementations.md) — it is faster and uses less memory per element.
