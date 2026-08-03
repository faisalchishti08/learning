---
card: data-structures
gi: 188
slug: immutable-unmodifiable-collections
title: Immutable / unmodifiable collections
---

## 1. What it is

An **unmodifiable** collection (from `Collections.unmodifiableList` and similar) is a read-only **view** wrapping mutable data that can still change from elsewhere. A genuinely **immutable** collection (from `List.of`, `Set.of`, `Map.of`, added in Java 9) holds its own fixed data that can never change, by anyone, through any reference.

## 2. Why & when

The distinction matters because these two give different safety guarantees. Use an unmodifiable view when you want to hand out read-only access to data that legitimately still changes elsewhere in your program — for example, exposing an internal list as read-only to callers while your own code keeps mutating the original. Use a truly immutable collection when you want a fixed, safe-to-share, thread-safe-by-construction set of values that will never change — configuration constants, a fixed set of valid states, or data passed to another thread.

## 3. Core concept

**Unmodifiable views (`Collections.unmodifiableList`, etc.).** These wrap an existing mutable collection. The wrapper itself rejects mutating calls (`add`, `remove`, `set` all throw `UnsupportedOperationException`), but it holds a live reference to the original backing data — any change made directly to the original collection is immediately visible through the wrapper, since they share the same underlying storage.

**True immutable factories (`List.of`, `Set.of`, `Map.of`).** These create a brand-new collection with a fixed, independent backing structure. There is no "original mutable collection" anywhere for anyone else to hold a reference to and change — the immutability is structural, not just a wrapper's restriction.

**Extra guarantees `List.of`/`Set.of`/`Map.of` add beyond "cannot be mutated."** They reject `null` elements (throwing `NullPointerException` immediately at creation, not silently accepting `null` the way `ArrayList` would). `Set.of` and `Map.of` throw `IllegalArgumentException` if you pass duplicate elements or duplicate keys — a mutable `HashSet` would silently just keep one copy.

**Why the difference matters for defensive copying.** If you need to protect internal state from external mutation *and* guard against the internal state itself changing later, wrap a genuine copy: `List.copyOf(internalList)` (or the older `List.of(new ArrayList<>(internalList).toArray(...))` pattern) — this copies the data into a new, truly immutable structure, breaking any live connection to the original.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Unmodifiable view sharing backing data with a mutable original, versus List.of creating an independent, truly immutable structure">
  <g font-family="sans-serif" font-size="10" fill="#e6edf3">
    <text x="10" y="20">Collections.unmodifiableList(original):</text>
    <rect x="20" y="30" width="140" height="30" fill="#161b22" stroke="#f0883e"/><text x="90" y="50" text-anchor="middle" font-size="9">mutable original</text>
    <rect x="220" y="30" width="140" height="30" fill="#0d1117" stroke="#f0883e"/><text x="290" y="50" text-anchor="middle" font-size="9">read-only view</text>
    <line x1="160" y1="45" x2="220" y2="45" stroke="#f0883e"/>
    <text x="20" y="80" font-size="9" fill="#f0883e">original still mutable elsewhere -&gt; view sees every change</text>

    <text x="10" y="130">List.of(1, 2, 3):</text>
    <rect x="20" y="140" width="200" height="30" fill="#161b22" stroke="#3fb950"/>
    <text x="120" y="160" text-anchor="middle" font-size="9">independent, fixed, truly immutable</text>
    <text x="20" y="185" font-size="9" fill="#3fb950">no mutable original exists anywhere -- nothing to change it</text>
  </g>
</svg>

A view shares live data with a mutable source; `List.of` owns its own fixed, disconnected data.

## 5. Runnable example

```java
// ImmutableUnmodifiable.java
import java.util.*;

public class ImmutableUnmodifiable {

    // Basic: List.of rejects nulls and mutation immediately, unlike a plain unmodifiable wrapper.
    static void basicLevel() {
        List<String> trueImmutable = List.of("a", "b", "c");
        try {
            trueImmutable.add("d");
        } catch (UnsupportedOperationException e) {
            System.out.println("basic: List.of blocks mutation -> " + e.getClass().getSimpleName());
        }

        try {
            List.of("a", null, "c");
        } catch (NullPointerException e) {
            System.out.println("basic: List.of rejects null elements -> " + e.getClass().getSimpleName());
        }
    }

    // Intermediate: an unmodifiable VIEW still reflects changes to its backing mutable list.
    static void intermediateLevel() {
        List<String> mutableOriginal = new ArrayList<>(List.of("x", "y"));
        List<String> view = Collections.unmodifiableList(mutableOriginal);

        mutableOriginal.add("z"); // change the original, not the view
        System.out.println("intermediate: view reflects the mutation -> " + view);

        List<String> trueImmutableCopy = List.copyOf(mutableOriginal); // snapshot, disconnected
        mutableOriginal.add("w"); // mutate the original again
        System.out.println("intermediate: List.copyOf snapshot is unaffected -> " + trueImmutableCopy);
    }

    // Advanced: Set.of and Map.of reject duplicates outright, catching a bug that HashSet/HashMap would hide silently.
    static void advancedLevel() {
        try {
            Set.of("a", "b", "a"); // duplicate "a"
        } catch (IllegalArgumentException e) {
            System.out.println("advanced: Set.of rejects duplicates -> " + e.getClass().getSimpleName());
        }

        // Compare: a HashSet would silently accept this and just keep one "a", hiding the bug.
        Set<String> hashSet = new HashSet<>(List.of("a", "b"));
        hashSet.add("a"); // no error, no signal that this was likely a mistake
        System.out.println("advanced: HashSet silently deduplicates -> " + hashSet);
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

How to run: `java ImmutableUnmodifiable.java`

## 6. Walkthrough

`List.of("a", "b", "c")` creates a genuinely fixed list. Calling `.add("d")` on it throws `UnsupportedOperationException` immediately — there is no backing mutable structure anywhere that could accept the addition. Attempting `List.of("a", null, "c")` throws `NullPointerException` right at creation, catching a likely bug (a missing value where one was expected) far earlier than an `ArrayList` would, which happily stores `null`.

For the unmodifiable view: `mutableOriginal` starts as `["x", "y"]`, and `view` wraps it. Calling `mutableOriginal.add("z")` (on the **original**, not the view) succeeds, because `mutableOriginal` is a completely normal `ArrayList`. Printing `view` afterward shows `["x", "y", "z"]` — the addition is visible through the view, because the view was never a copy, only a restriction on one particular reference to the same shared data.

Contrast this with `List.copyOf(mutableOriginal)`, which creates `trueImmutableCopy` as an actual, independent snapshot at the moment it is called. Mutating `mutableOriginal` again afterward (`.add("w")`) has no effect on `trueImmutableCopy`, which stays frozen at whatever it captured — `["x", "y", "z"]`.

For `Set.of`: passing a duplicate element (`"a"` twice) throws `IllegalArgumentException` at creation — an explicit, loud signal that something about the caller's intent is likely wrong. A `HashSet` given the same duplicate input would simply keep one copy silently, with no indication that a duplicate was ever passed — which can mask real bugs where a duplicate was never supposed to occur.

**Complexity.** `List.of`/`Set.of`/`Map.of`: `O(n)` to build, `O(1)` for element access afterward — comparable cost to their mutable counterparts, since the immutability guarantee costs nothing extra at runtime beyond rejecting mutating calls. `Collections.unmodifiableList` and friends: `O(1)` to wrap, since no copying occurs. `List.copyOf`: `O(n)` to copy.

## 7. Gotchas & takeaways

> `Collections.unmodifiableList` is not a defensive copy — treat it strictly as "this specific reference cannot mutate the data," never as "this data can never change." If you need the stronger guarantee, use `List.copyOf(...)` or one of the `List.of`/`Set.of`/`Map.of` factories to build genuinely independent, immutable data.

- `List.of`, `Set.of`, and `Map.of` reject `null` — if you need an immutable collection that can hold `null`, you must fall back to `Collections.unmodifiableList(Arrays.asList(...))`, accepting its weaker (view-only) guarantee.
- `Arrays.asList(...)` (covered on the [next page](0189-arrays-aslist-list-of-factory-methods.md)) is neither a mutable `ArrayList` nor a true `List.of`-style immutable list — it sits in a distinct middle ground, and confusing the three is a common source of bugs.
- Prefer returning truly immutable collections (`List.of`/`Set.of`/`Map.of`, or `List.copyOf`) from public API methods whenever the data should never change — it documents the contract in the type itself and fails loudly (an exception) rather than silently if a caller tries to mutate it.
