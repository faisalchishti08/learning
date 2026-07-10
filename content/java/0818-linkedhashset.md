---
card: java
gi: 818
slug: linkedhashset
title: LinkedHashSet
---

## 1. What it is

`LinkedHashSet` is a [`HashSet`](0817-hashset.md) subclass that additionally maintains a **doubly-linked list running through all its entries**, recording the order elements were inserted. It offers the exact same O(1) average-case `add`/`contains`/`remove` performance as `HashSet` (since it's built on the same hashing mechanism underneath), but iteration — a for-each loop, `toString()`, `stream()` — always visits elements in **insertion order**, not the arbitrary bucket order plain `HashSet` produces. Re-inserting an element already present does not change its position in that order; only genuinely new elements are appended to the end of the linked chain.

## 2. Why & when

`HashSet`'s lack of any order guarantee is fine for pure membership testing, but plenty of real deduplication needs also want a *predictable, human-meaningful* display order — a list of unique tags shown in the order the user typed them, a set of distinct log event types in the order they were first seen. `LinkedHashSet` gives both properties at once: `HashSet`'s O(1) uniqueness guarantee, plus insertion-order iteration, at a small, constant memory overhead per entry (for the extra linked-list pointers) and a marginally higher constant-factor cost per operation (maintaining that linked list alongside the hash table). Reach for it whenever "unique, and shown in the order first encountered" is the actual requirement — which is common enough that it's worth defaulting to `LinkedHashSet` over plain `HashSet` whenever the output will ever be displayed to a person.

## 3. Core concept

```java
Set<String> tags = new LinkedHashSet<>();
tags.add("urgent");
tags.add("bug");
tags.add("urgent"); // duplicate -- rejected, and does NOT move to the end
tags.add("frontend");

System.out.println(tags); // [urgent, bug, frontend] -- insertion order preserved, re-add doesn't reorder
```

Compare this to a plain `HashSet` built from the same insertions, which could print `tags` in any order at all — possibly `[bug, urgent, frontend]`, possibly something else entirely, and that order isn't even guaranteed to stay the same across separate runs of the same program.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A LinkedHashSet maintains two structures simultaneously: a hash table for O(1) lookup, and a linked list preserving insertion order for iteration">
  <g font-family="sans-serif">
    <rect x="40" y="30" width="160" height="40" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
    <text x="120" y="55" fill="#e6edf3" font-size="11" text-anchor="middle">hash table (buckets)</text>
    <text x="320" y="55" fill="#8b949e" font-size="10" text-anchor="middle">used by add() / contains() — O(1)</text>

    <rect x="40" y="100" width="160" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
    <text x="120" y="125" fill="#e6edf3" font-size="11" text-anchor="middle">linked list (order)</text>
    <text x="320" y="125" fill="#8b949e" font-size="10" text-anchor="middle">used by iteration — insertion order</text>
  </g>
  <text x="320" y="165" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Both structures are kept in sync on every add() — the cost of the extra ordering guarantee</text>
</svg>

*A `LinkedHashSet` keeps both a hash table (for fast lookup) and a linked list (for ordered iteration) in sync at all times.*

## 5. Runnable example

Scenario: collecting unique tags applied to a support ticket in the order they were first added, growing from basic dedup-with-order to proving re-insertion doesn't reorder, to using this property to build a simple "first N distinct values seen" utility over a live event stream.

### Level 1 — Basic

```java
import java.util.*;

public class TagsBasic {
    public static void main(String[] args) {
        Set<String> tags = new LinkedHashSet<>();
        tags.add("urgent");
        tags.add("bug");
        tags.add("frontend");
        tags.add("urgent"); // duplicate, ignored

        System.out.println("tags in insertion order: " + tags);
        System.out.println("unique tag count: " + tags.size());
    }
}
```

**How to run:** `java TagsBasic.java` (JDK 17+).

Expected output:
```
tags in insertion order: [urgent, bug, frontend]
unique tag count: 3
```

Unlike plain `HashSet`, this order is guaranteed and reproducible across every run — `"urgent"` always prints first because it was added first, regardless of its hash code.

### Level 2 — Intermediate

```java
import java.util.*;

public class TagsReinsertionOrder {
    public static void main(String[] args) {
        Set<String> tags = new LinkedHashSet<>();
        tags.add("urgent");
        tags.add("bug");
        tags.add("frontend");

        boolean addedAgain = tags.add("urgent"); // re-add an existing element
        System.out.println("re-adding 'urgent' reported new: " + addedAgain);
        System.out.println("order after re-adding: " + tags); // "urgent" stays FIRST, not moved to the end

        // Removing and re-adding, by contrast, DOES change position -- it's a genuinely new insertion.
        tags.remove("urgent");
        tags.add("urgent");
        System.out.println("order after remove-then-re-add: " + tags); // now "urgent" is LAST
    }
}
```

**How to run:** `java TagsReinsertionOrder.java`.

Expected output:
```
re-adding 'urgent' reported new: false
order after re-adding: [urgent, bug, frontend]
order after remove-then-re-add: [bug, frontend, urgent]
```

The real-world concern added: distinguishing "re-adding an element that's already present" (a no-op that leaves position unchanged) from "removing then re-adding" (a genuine delete-and-reinsert, which does move the element to the end of the order) — a subtlety that matters if code relies on `LinkedHashSet`'s ordering to represent something like "most recently added," which requires the explicit remove-then-add pattern, not a plain `add()` call on an existing element.

### Level 3 — Advanced

```java
import java.util.*;

public class FirstNDistinctValues {

    // Returns the first `limit` DISTINCT values seen in `stream`, in the order first encountered.
    static <T> List<T> firstNDistinct(Iterable<T> stream, int limit) {
        Set<T> seen = new LinkedHashSet<>();
        for (T value : stream) {
            seen.add(value); // duplicates are ignored automatically; order is preserved
            if (seen.size() == limit) break; // stop as soon as we have enough DISTINCT values
        }
        return new ArrayList<>(seen);
    }

    public static void main(String[] args) {
        List<String> eventStream = List.of(
            "click", "click", "scroll", "click", "hover", "scroll", "submit", "click"
        );

        List<String> firstThreeDistinct = firstNDistinct(eventStream, 3);
        System.out.println("first 3 distinct event types seen: " + firstThreeDistinct);

        List<String> firstFiveDistinct = firstNDistinct(eventStream, 5);
        System.out.println("first 5 distinct event types seen: " + firstFiveDistinct);
    }
}
```

**How to run:** `java FirstNDistinctValues.java`.

Expected output:
```
first 3 distinct event types seen: [click, scroll, hover]
first 5 distinct event types seen: [click, scroll, hover, submit]
```

This adds the production-flavored hard case: a genuinely useful utility — "first N distinct values, in first-seen order" — that's almost trivial to write correctly *because* `LinkedHashSet` combines deduplication and order-preservation in one structure. Note the second call requests 5 distinct values but the stream only contains 4 distinct event types (`click`, `scroll`, `hover`, `submit`) — the loop simply runs out of input, `seen` tops out at 4, and the method returns what it found rather than looping forever or throwing.

## 6. Walkthrough

Tracing `FirstNDistinctValues.main`'s second call, `firstNDistinct(eventStream, 5)`:

1. `seen` starts empty. The for-each loop begins walking `eventStream` in its original order: `"click", "click", "scroll", "click", "hover", "scroll", "submit", "click"`.
2. `"click"` is added — new, `seen = [click]`, size 1, not yet 5.
3. The second `"click"` is added again — `LinkedHashSet.add` recognizes it's already present (via the same hash-bucket lookup `HashSet` would use) and does nothing; `seen` stays `[click]`, size still 1.
4. `"scroll"` is added — new, `seen = [click, scroll]`, size 2.
5. The third `"click"` is added — already present, ignored, size stays 2.
6. `"hover"` is added — new, `seen = [click, scroll, hover]`, size 3.
7. The second `"scroll"` is added — already present, ignored, size stays 3.
8. `"submit"` is added — new, `seen = [click, scroll, hover, submit]`, size 4. The check `seen.size() == limit` (4 == 5) is false, so the loop continues.
9. The final `"click"` is added — already present, ignored, size stays 4.
10. The for-each loop reaches the end of `eventStream` naturally (there's nothing left to iterate), so the loop exits without ever satisfying the `break` condition. `seen` is converted to an `ArrayList` and returned, correctly containing all 4 distinct event types that actually appeared, in the order each was first seen — even though the caller asked for 5.

## 7. Gotchas & takeaways

> **Gotcha:** re-adding an element that's already present does **not** move it to the end of a `LinkedHashSet`'s order — only a genuinely new insertion (including a fresh insertion right after an explicit `remove()`) changes position. Code that wants "most recently touched" ordering semantics (like a simple LRU-ish display) must explicitly call `remove()` before re-`add()`ing, not just call `add()` again.

- `LinkedHashSet` extends `HashSet`, adding a linked list that preserves insertion order for iteration, at the cost of a small constant memory and time overhead per entry.
- It offers the same O(1) average-case `add`/`contains`/`remove` as plain `HashSet` — the ordering guarantee doesn't change the underlying hashing performance.
- Re-inserting an already-present element is a no-op that leaves its position unchanged; only new elements are appended to the end of the order.
- Its combination of deduplication and stable order makes patterns like "first N distinct values seen" or "unique tags in the order the user entered them" simple to implement correctly.
- Reach for `LinkedHashSet` by default over plain [`HashSet`](0817-hashset.md) whenever the set's contents will ever be displayed or iterated in a way where order matters to a person.
