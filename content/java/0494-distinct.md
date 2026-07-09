---
card: java
gi: 494
slug: distinct
title: distinct()
---

## 1. What it is

`Stream.distinct()` returns a stream containing only the unique elements of the source stream, removing duplicates. Uniqueness is determined by each element's `equals()` method (as used by `Object.equals`, or an overridden version). For an ordered stream, `distinct()` preserves the order of first occurrence — the first copy of a duplicate is kept, later copies are dropped.

## 2. Why & when

Deduplicating a collection used to mean funneling it through a `Set` (losing the original order unless you used a `LinkedHashSet`) or manually tracking seen elements in a loop. `distinct()` does this as one step in a stream pipeline, and — since Java's `Stream` implementation for ordered sources typically preserves encounter order — it's often simpler than reaching for a `Set` when you also care about the original ordering of first occurrences.

You reach for `distinct()` whenever a stream might contain repeated values you want counted or processed only once: unique customer IDs from a log of repeated visits, unique tags across many articles, unique words in a body of text. Because uniqueness relies on `equals()`, it works correctly on custom types as long as `equals()` (and `hashCode()`, for internal efficiency) are properly overridden — which is automatic for `record` types.

## 3. Core concept

```java
import java.util.stream.*;

List<Integer> unique = Stream.of(1, 2, 2, 3, 1, 4)
        .distinct()
        .toList(); // [1, 2, 3, 4] -- first occurrence of each kept, in original order
```

`distinct()` uses `equals()` to decide what counts as "the same element" — for custom objects, that means their `equals()` implementation determines what gets deduplicated.

## 4. Diagram

<svg viewBox="0 0 640 130" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="distinct removes duplicate elements, keeping the first occurrence of each unique value">
  <rect x="8" y="8" width="624" height="114" rx="8" fill="#0d1117"/>
  <rect x="30" y="20" width="45" height="30" fill="#1c2430" stroke="#79c0ff"/><text x="52" y="40" fill="#79c0ff" font-size="12" text-anchor="middle" font-family="monospace">1</text>
  <rect x="85" y="20" width="45" height="30" fill="#1c2430" stroke="#79c0ff"/><text x="107" y="40" fill="#79c0ff" font-size="12" text-anchor="middle" font-family="monospace">2</text>
  <rect x="140" y="20" width="45" height="30" fill="#1c2430" stroke="#79c0ff"/><text x="162" y="40" fill="#79c0ff" font-size="12" text-anchor="middle" font-family="monospace">2</text>
  <rect x="195" y="20" width="45" height="30" fill="#1c2430" stroke="#79c0ff"/><text x="217" y="40" fill="#79c0ff" font-size="12" text-anchor="middle" font-family="monospace">3</text>
  <rect x="250" y="20" width="45" height="30" fill="#1c2430" stroke="#79c0ff"/><text x="272" y="40" fill="#79c0ff" font-size="12" text-anchor="middle" font-family="monospace">1</text>
  <text x="160" y="70" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">distinct()</text>
  <line x1="160" y1="52" x2="160" y2="85" stroke="#8b949e" stroke-width="1.5" marker-end="url(#arrowD)"/>
  <rect x="30" y="90" width="45" height="30" fill="#1c2430" stroke="#6db33f"/><text x="52" y="110" fill="#6db33f" font-size="12" text-anchor="middle" font-family="monospace">1</text>
  <rect x="85" y="90" width="45" height="30" fill="#1c2430" stroke="#6db33f"/><text x="107" y="110" fill="#6db33f" font-size="12" text-anchor="middle" font-family="monospace">2</text>
  <rect x="140" y="90" width="45" height="30" fill="#1c2430" stroke="#6db33f"/><text x="162" y="110" fill="#6db33f" font-size="12" text-anchor="middle" font-family="monospace">3</text>
  <defs><marker id="arrowD" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

The second `2` and the second `1` are dropped as duplicates; the first occurrence of each value survives, in its original position.

## 5. Runnable example

Scenario: collecting unique visitor IDs from a website's raw access log — evolved from deduplicating simple values, through deduplicating custom objects via `equals()`/`hashCode()`, to a version that deduplicates by a *derived* key rather than full object equality.

### Level 1 — Basic

```java
import java.util.*;
import java.util.stream.*;

public class DistinctBasic {
    public static void main(String[] args) {
        List<String> visitorLog = List.of("u1", "u2", "u1", "u3", "u2", "u1");

        List<String> uniqueVisitors = visitorLog.stream()
                .distinct()
                .toList();

        System.out.println("Unique visitors: " + uniqueVisitors);
    }
}
```

**How to run:** `java DistinctBasic.java`

Expected output:
```
Unique visitors: [u1, u2, u3]
```

`.distinct()` compares each `String` using `equals()`, keeping the first occurrence of each unique value and dropping later repeats — `"u1"` appears three times in the log but only once in the result, in the position of its first appearance.

### Level 2 — Intermediate

```java
import java.util.*;
import java.util.stream.*;

public class DistinctRecords {
    record Visit(String userId, String page) {} // record auto-generates equals()/hashCode() from all fields

    public static void main(String[] args) {
        List<Visit> visits = List.of(
                new Visit("u1", "/home"),
                new Visit("u2", "/home"),
                new Visit("u1", "/home"), // exact duplicate of the first visit
                new Visit("u1", "/cart")  // same user, different page -- NOT a duplicate
        );

        List<Visit> uniqueVisits = visits.stream()
                .distinct()
                .toList();

        uniqueVisits.forEach(v -> System.out.println(v.userId() + " visited " + v.page()));
    }
}
```

**How to run:** `java DistinctRecords.java`

Expected output:
```
u1 visited /home
u2 visited /home
u1 visited /cart
```

The real-world concern this adds: deduplicating custom objects, not just primitives/strings. Because `Visit` is a `record`, its `equals()` (auto-generated from all fields) considers two visits equal only if *both* `userId` and `page` match — so `Visit("u1", "/home")` appearing twice collapses to one, but `Visit("u1", "/cart")` is a distinct visit from `Visit("u1", "/home")` even though the user is the same, and survives.

### Level 3 — Advanced

```java
import java.util.*;
import java.util.stream.*;

public class DistinctByKey {
    record Visit(String userId, String page) {}

    public static void main(String[] args) {
        List<Visit> visits = List.of(
                new Visit("u1", "/home"),
                new Visit("u2", "/home"),
                new Visit("u1", "/cart"), // same user as first visit, but distinct() by full object wouldn't merge these
                new Visit("u3", "/home")
        );

        // distinct() alone can't dedupe "by userId only" -- it compares whole objects.
        // Track seen keys manually via filter() for a "first visit per user" result.
        Set<String> seenUsers = new HashSet<>();
        List<Visit> firstVisitPerUser = visits.stream()
                .filter(v -> seenUsers.add(v.userId())) // add() returns false if already present
                .toList();

        firstVisitPerUser.forEach(v -> System.out.println(v.userId() + "'s first visit: " + v.page()));
    }
}
```

**How to run:** `java DistinctByKey.java`

Expected output:
```
u1's first visit: /home
u2's first visit: /home
u3's first visit: /home
```

This adds a real limitation of `distinct()`: it can only compare *whole* objects via `equals()`, but here the goal is deduplication by *one field* (`userId`) while keeping the rest of the object — `distinct()` alone cannot express "unique by this one field." The workaround uses `filter()` with a mutable `HashSet` that tracks seen user IDs: `seenUsers.add(v.userId())` returns `true` the first time a given `userId` is seen (keeping that visit) and `false` on every subsequent visit from the same user (dropping it) — an idiomatic, if slightly stateful, pattern for "distinct by key" filtering.

## 6. Walkthrough

Execution starts in `main` of the Level 3 example. `visits` holds four `Visit` records: `u1` visits `/home`, `u2` visits `/home`, `u1` visits `/cart` (a *different* visit from `u1`'s first, since the page differs), and `u3` visits `/home`.

`seenUsers` starts as an empty `HashSet<String>`. `visits.stream().filter(v -> seenUsers.add(v.userId()))` processes each visit in order, evaluating the predicate as a side effect: for the first visit, `Visit("u1", "/home")`, `seenUsers.add("u1")` attempts to add `"u1"` to the (currently empty) set; since it wasn't present, `add` returns `true`, the set becomes `{"u1"}`, and the predicate is `true` — this visit is kept.

For the second visit, `Visit("u2", "/home")`, `seenUsers.add("u2")` adds `"u2"` (not previously present), returns `true`, set becomes `{"u1", "u2"}` — kept.

For the third visit, `Visit("u1", "/cart")`, `seenUsers.add("u1")` attempts to add `"u1"` again — but it's *already* in the set from the first visit, so `add` returns `false` without modifying the set, and the predicate is `false` — this visit is **dropped**, even though its `page` (`/cart`) differs from `u1`'s first visit's page (`/home`); only the `userId` matters to this filter.

For the fourth visit, `Visit("u3", "/home")`, `seenUsers.add("u3")` adds `"u3"` (not previously present), returns `true`, set becomes `{"u1", "u2", "u3"}` — kept.

```
Visit(u1,/home) -> seenUsers.add("u1") -> true (new)  -> KEPT
Visit(u2,/home) -> seenUsers.add("u2") -> true (new)  -> KEPT
Visit(u1,/cart) -> seenUsers.add("u1") -> false (dup) -> DROPPED
Visit(u3,/home) -> seenUsers.add("u3") -> true (new)  -> KEPT
```

`.toList()` collects the three kept visits into `firstVisitPerUser`, and each is printed showing that user's *first* recorded page — `u1`'s later `/cart` visit never appears, since only the first occurrence per `userId` survives this "distinct by key" filter.

## 7. Gotchas & takeaways

> `distinct()` relies entirely on `equals()` (and `hashCode()` for efficient internal deduplication) — for custom classes that don't override these, it falls back to reference identity, so two objects with identical field values but separate instances would **not** be considered duplicates. `record` types are safe by default since they auto-generate both methods from all their fields.

- `distinct()` removes duplicate elements based on `equals()`, keeping the first occurrence of each unique value in an ordered stream.
- For `record` types, `equals()` (auto-generated from every field) means two records are duplicates only if *all* their fields match — not just one field of interest.
- `distinct()` cannot express "unique by one field while keeping the rest of the object" — for that, use `filter()` with a mutable seen-set (as in Level 3), or map to the key first and deduplicate that.
- Since `distinct()` must track every element seen so far to detect duplicates, it needs memory proportional to the number of unique elements — a concern for very large or infinite streams.
- Always confirm a custom type's `equals()`/`hashCode()` are correctly implemented before relying on `distinct()` — without them, deduplication silently does nothing useful.
