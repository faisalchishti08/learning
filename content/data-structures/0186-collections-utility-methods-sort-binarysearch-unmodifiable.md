---
card: data-structures
gi: 186
slug: collections-utility-methods-sort-binarysearch-unmodifiable
title: Collections utility methods (sort, binarySearch, unmodifiable)
---

## 1. What it is

`java.util.Collections` is a utility class full of `static` helper methods that operate on any `Collection` or `List` — sorting, searching, reversing, shuffling, and wrapping collections to change their mutability. None of these methods are instance methods on the collections themselves; they are standalone functions that take a collection as an argument.

## 2. Why & when

These methods exist so common operations do not need to be reimplemented on every project. `Collections.sort` and `Collections.binarySearch` give you tested, correct implementations of two of the most common list operations. `Collections.unmodifiableList` (and its `Set`/`Map` counterparts) let you hand out a collection that looks read-only to callers, without copying the data — useful for protecting internal state from external mutation.

## 3. Core concept

**Sorting.** `Collections.sort(list)` sorts using the elements' natural [Comparable](0185-comparable-vs-comparator.md) order. `Collections.sort(list, comparator)` sorts using a supplied `Comparator` instead. Both use a stable, `O(n log n)` sort (Timsort for objects) — "stable" meaning elements that compare as equal keep their original relative order.

**Searching.** `Collections.binarySearch(list, key)` finds `key`'s index in `O(log n)`, but **only works correctly if the list is already sorted** in the same order the search assumes. Searching an unsorted list gives an undefined, meaningless result — no exception is thrown, just a wrong answer.

**Making a collection unmodifiable.** `Collections.unmodifiableList(list)` (and `unmodifiableSet`, `unmodifiableMap`) returns a **view** wrapping the original list — the same underlying data, but any mutating call (`add`, `remove`, `set`) on the wrapper throws `UnsupportedOperationException`. Critically, this view is **not a defensive copy**: if code still holds a reference to the original, mutable list and modifies it directly, those changes are visible through the "unmodifiable" wrapper too, since it is the same backing data.

**Other common utilities.** `Collections.reverse(list)` reverses in place, `O(n)`. `Collections.max(collection)`/`min(collection)` find the extreme element using natural order or a comparator, `O(n)`. `Collections.emptyList()`/`singletonList(x)` return small, memory-efficient immutable collections for common special cases.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="An unmodifiable view wrapping a mutable list, where mutating the original list still changes what the view sees">
  <g font-family="sans-serif" font-size="10" fill="#e6edf3">
    <rect x="40" y="30" width="200" height="50" fill="#161b22" stroke="#79c0ff"/>
    <text x="140" y="50" text-anchor="middle">original ArrayList</text>
    <text x="140" y="68" text-anchor="middle" font-size="9">[1, 2, 3]</text>

    <rect x="340" y="30" width="240" height="50" fill="#0d1117" stroke="#f0883e"/>
    <text x="460" y="50" text-anchor="middle">Collections.unmodifiableList(...)</text>
    <text x="460" y="68" text-anchor="middle" font-size="9">read-only VIEW, same backing data</text>

    <line x1="240" y1="55" x2="340" y2="55" stroke="#f0883e" marker-end="url(#arrow)"/>

    <text x="10" y="130" fill="#8b949e">wrapper.add(4) -&gt; throws UnsupportedOperationException</text>
    <text x="10" y="150" fill="#f0883e">original.add(4) -&gt; succeeds, AND wrapper now also shows [1,2,3,4]</text>
    <text x="10" y="180" fill="#8b949e">the wrapper only blocks mutation THROUGH ITSELF -- it is not a copy</text>
  </g>
</svg>

An unmodifiable view blocks writes through itself, but the underlying data can still change from elsewhere.

## 5. Runnable example

```java
// CollectionsUtility.java
import java.util.*;

public class CollectionsUtility {

    // Basic: sort and binarySearch, showing the requirement that the list be sorted first.
    static void basicLevel() {
        List<Integer> numbers = new ArrayList<>(List.of(5, 2, 8, 1, 9));
        Collections.sort(numbers);
        System.out.println("basic: sorted -> " + numbers);

        int index = Collections.binarySearch(numbers, 8);
        System.out.println("basic: binarySearch(8) -> index " + index);
    }

    // Intermediate: unmodifiableList is a VIEW, not a copy -- changes to the original are visible through it.
    static void intermediateLevel() {
        List<Integer> original = new ArrayList<>(List.of(1, 2, 3));
        List<Integer> readOnlyView = Collections.unmodifiableList(original);

        try {
            readOnlyView.add(4);
        } catch (UnsupportedOperationException e) {
            System.out.println("intermediate: mutating the view threw -> " + e.getClass().getSimpleName());
        }

        original.add(4); // mutate the ORIGINAL, not the view
        System.out.println("intermediate: view reflects the original's change -> " + readOnlyView);
    }

    // Advanced: reverse, max/min, and a Comparator-based sort combined in one realistic sequence.
    static void advancedLevel() {
        List<String> names = new ArrayList<>(List.of("Charlie", "alice", "Bob"));

        names.sort(String.CASE_INSENSITIVE_ORDER);
        System.out.println("advanced: case-insensitive sorted -> " + names);

        Collections.reverse(names);
        System.out.println("advanced: reversed -> " + names);

        String longest = Collections.max(names, Comparator.comparingInt(String::length));
        System.out.println("advanced: longest name -> " + longest);
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

How to run: `java CollectionsUtility.java`

## 6. Walkthrough

Start with `[5, 2, 8, 1, 9]`. `Collections.sort(numbers)` sorts it in place, using `Integer`'s natural ordering, producing `[1, 2, 5, 8, 9]`. Now `Collections.binarySearch(numbers, 8)` runs binary search assuming this sorted order — it correctly finds `8` at index `3`. If the list had **not** been sorted first, `binarySearch` would still return *some* index without any error, but that index could easily be wrong, since binary search's correctness fundamentally depends on the sortedness precondition.

For the unmodifiable view: `Collections.unmodifiableList(original)` wraps `original` — no copying happens. Calling `readOnlyView.add(4)` throws `UnsupportedOperationException`, since the wrapper blocks all mutating calls made **through itself**. But calling `original.add(4)` directly succeeds, because `original` is still a perfectly normal, mutable `ArrayList` — and because `readOnlyView` shares the same backing array, printing it afterward shows `[1, 2, 3, 4]`, including the change made through the other reference.

For the advanced example: `String.CASE_INSENSITIVE_ORDER` is a built-in `Comparator<String>` constant, used here via `list.sort(comparator)` to sort ignoring case: `[alice, Bob, Charlie]`. `Collections.reverse` flips this in place: `[Charlie, Bob, alice]`. `Collections.max` with a length-based `Comparator` finds `"Charlie"`, the longest of the three names.

**Complexity.** `Collections.sort`: `O(n log n)`. `Collections.binarySearch`: `O(log n)`, assuming the list is already sorted (and assuming random access — for a `LinkedList`, the actual traversal cost can make this effectively `O(n)` despite the `O(log n)` comparison count). `Collections.reverse`/`max`/`min`: `O(n)`. `Collections.unmodifiableList`: `O(1)` to create the wrapper.

## 7. Gotchas & takeaways

> `Collections.unmodifiableList` (and its `Set`/`Map` equivalents) does **not** protect against mutation through a reference to the original collection — treat it as a way to prevent a specific caller from mutating your data through the reference you hand them, not as a way to freeze the data entirely. For a true, disconnected snapshot, copy the collection first: `List.copyOf(original)` or `new ArrayList<>(original)` wrapped in `unmodifiableList`.

- Always confirm a list is sorted (in the same order `binarySearch` assumes) before calling `Collections.binarySearch` — there is no runtime check, and a wrong answer on an unsorted list fails silently.
- `Collections.sort` and `List.sort` are equivalent since Java 8 (`List.sort` was added as a default method); prefer `list.sort(comparator)` in new code for readability, falling back to `Collections.sort(list)` only for pre-Java-8 style code or when sorting via the static utility reads more clearly in context.
- For truly immutable collections created fresh (not wrapping existing mutable data), prefer the factory methods covered in [Arrays.asList & List.of](0189-arrays-aslist-list-of-factory-methods.md), which have simpler, stronger immutability guarantees than wrapping with `Collections.unmodifiableList`.
