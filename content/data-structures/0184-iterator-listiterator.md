---
card: data-structures
gi: 184
slug: iterator-listiterator
title: Iterator & ListIterator
---

## 1. What it is

An `Iterator` is an object that walks through a collection one element at a time, without exposing the collection's internal structure. `ListIterator` extends `Iterator` specifically for `List`s, adding backward traversal, index tracking, and in-place modification (`set`, `add`) during iteration.

## 2. Why & when

Use an `Iterator` (usually implicitly, via a for-each loop) whenever you need to walk a collection's elements without caring how they are stored. Use an explicit `Iterator` when you need to **remove** elements safely while iterating — a for-each loop cannot do this without throwing an exception. Use `ListIterator` specifically when you need to walk backward, know the current index, or replace/insert elements mid-traversal.

## 3. Core concept

**The contract.** `Iterator<T>` defines three methods: `hasNext()` (is there another element?), `next()` (return the next element, advancing the cursor), and `remove()` (remove the last element returned by `next()`). A for-each loop (`for (T item : collection)`) is compiler sugar that calls exactly these methods behind the scenes.

**Why `iterator.remove()` is safe but `collection.remove()` during iteration is not.** Removing directly from the underlying collection while an iterator is active changes the collection's internal state (size, structure) without informing the iterator, which then detects the mismatch and throws `ConcurrentModificationException` on the next `hasNext()`/`next()` call. `iterator.remove()` is the *only* safe way to remove during iteration, because the iterator updates its own internal bookkeeping at the same time.

**What `ListIterator` adds.** `hasPrevious()`/`previous()` (walk backward), `nextIndex()`/`previousIndex()` (know the current position), `set(element)` (replace the last element returned by `next()`/`previous()`), and `add(element)` (insert a new element at the current cursor position, before the element that would be returned by a subsequent `next()`).

**Why plain `Iterator` cannot modify elements.** `Iterator`'s contract only supports reading and removing. Replacing or inserting during traversal needs the extra position awareness `ListIterator` provides — which only makes sense for `List` (an ordered, indexable structure), not for `Set` or general `Collection`, where "insert before the current position" has no clear meaning.

## 4. Diagram

<svg viewBox="0 0 640 180" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="An iterator's cursor sitting between elements, with next() moving forward and previous() (ListIterator only) moving backward">
  <g font-family="sans-serif" font-size="10" fill="#e6edf3">
    <rect x="60" y="40" width="60" height="36" fill="#161b22" stroke="#79c0ff"/><text x="90" y="62" text-anchor="middle">A</text>
    <rect x="160" y="40" width="60" height="36" fill="#161b22" stroke="#79c0ff"/><text x="190" y="62" text-anchor="middle">B</text>
    <rect x="260" y="40" width="60" height="36" fill="#161b22" stroke="#79c0ff"/><text x="290" y="62" text-anchor="middle">C</text>

    <line x1="220" y1="30" x2="220" y2="86" stroke="#f0883e" stroke-width="2"/>
    <text x="220" y="20" text-anchor="middle" font-size="9" fill="#f0883e">cursor (after A, B returned)</text>

    <text x="120" y="120" font-size="9" fill="#3fb950">next() -&gt; returns C, cursor moves right</text>
    <text x="120" y="140" font-size="9" fill="#8b949e">previous() (ListIterator only) -&gt; returns B, cursor moves left</text>
    <text x="120" y="160" font-size="9" fill="#8b949e">set(X) replaces the element last returned; add(X) inserts at the cursor</text>
  </g>
</svg>

The cursor sits *between* elements; `next()`/`previous()` decide which neighbor to return and which way to move.

## 5. Runnable example

```java
// IteratorListIterator.java
import java.util.*;

public class IteratorListIterator {

    // Basic: safely remove elements during iteration using Iterator.remove().
    static void basicLevel() {
        List<Integer> numbers = new ArrayList<>(List.of(1, 2, 3, 4, 5, 6));
        Iterator<Integer> it = numbers.iterator();
        while (it.hasNext()) {
            if (it.next() % 2 == 0) {
                it.remove(); // safe: informs the iterator of the removal
            }
        }
        System.out.println("basic: after removing evens -> " + numbers);
    }

    // Intermediate: ListIterator walking backward and replacing elements in place.
    static void intermediateLevel() {
        List<String> words = new ArrayList<>(List.of("apple", "banana", "cherry"));
        ListIterator<String> it = words.listIterator(words.size()); // start at the end

        while (it.hasPrevious()) {
            String word = it.previous();
            System.out.println("intermediate: walking backward -> " + word);
            if (word.equals("banana")) {
                it.set("BANANA"); // replace in place
            }
        }
        System.out.println("intermediate: after set() -> " + words);
    }

    // Advanced: ListIterator inserting a new element mid-traversal, demonstrating add()'s cursor semantics.
    static void advancedLevel() {
        List<Integer> numbers = new ArrayList<>(List.of(1, 2, 4, 5));
        ListIterator<Integer> it = numbers.listIterator();

        while (it.hasNext()) {
            int value = it.next();
            if (value == 2) {
                it.add(3); // inserts 3 right after 2, before the next() that would return 4
            }
        }
        System.out.println("advanced: after mid-traversal insert -> " + numbers);
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

How to run: `java IteratorListIterator.java`

## 6. Walkthrough

Start with `[1, 2, 3, 4, 5, 6]`. The explicit `Iterator` loop calls `hasNext()` then `next()` repeatedly. Each time `next()` returns an even number (`2, 4, 6`), call `it.remove()` — this removes that specific element from the underlying list **and** updates the iterator's internal cursor and expected-modification-count so the next `hasNext()`/`next()` call remains consistent. The result is `[1, 3, 5]`, with no `ConcurrentModificationException`, because every removal went through the iterator itself.

For `ListIterator` walking backward: start at `words.listIterator(words.size())`, positioning the cursor **after** the last element. `hasPrevious()` is true, so `previous()` returns `"cherry"` and moves the cursor left. Next, `previous()` returns `"banana"` — since this matches the target, `it.set("BANANA")` replaces the element **most recently returned** (`"banana"`) with `"BANANA"`, without disturbing the cursor position. Continuing, `previous()` returns `"apple"`. Final list: `["apple", "BANANA", "cherry"]`.

For mid-traversal insertion: starting fresh at the beginning, `next()` returns `1`, then `2`. Right after `2` is returned, call `it.add(3)` — this inserts `3` at the cursor's current position, which is **between** `2` and `4` (the element that would be returned by the *next* `next()` call). The iteration continues, and `next()` now correctly returns `4` (not `3` again — `add` does not make the added element "current"). Final list: `[1, 2, 3, 4, 5]`.

**Complexity.** `hasNext()`/`next()`/`hasPrevious()`/`previous()`: `O(1)` for `ArrayList`-backed and `LinkedList`-backed iterators alike (an `ArrayList` iterator just tracks an index; a `LinkedList` iterator holds a direct node reference, avoiding the `O(n)` cost that indexed `get(i)` calls would have). `remove()`/`set()`/`add()`: `O(1)` for `LinkedList`; `O(n)` worst case for `ArrayList` (due to the underlying array shift), though the traversal itself remains `O(n)` total either way.

## 7. Gotchas & takeaways

> Calling the collection's own `remove()` method (not the iterator's) while a for-each loop or an active iterator is mid-traversal throws `ConcurrentModificationException` on the next `hasNext()`/`next()` call — this is Java's **fail-fast** behavior, catching a likely bug rather than silently producing wrong results. See [fail-fast vs fail-safe iterators](0187-fail-fast-vs-fail-safe-iterators.md) for the full picture.

- A for-each loop (`for (T item : collection)`) cannot call `remove()` at all — reach for an explicit `Iterator` whenever conditional removal during traversal is needed.
- `ListIterator.add()` inserts **before** the element that the next `next()` call would return, and it does **not** update what `previous()` would return next in the same way — read the Javadoc's exact cursor semantics carefully before relying on this in a loop with mixed forward/backward calls.
- Only `List` (via `listIterator()`) exposes `ListIterator`; `Set` and `Queue` only expose the plain `Iterator`, since backward traversal and indexed insertion have no natural meaning for an unordered or FIFO-only structure.
