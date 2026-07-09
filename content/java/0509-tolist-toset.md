---
card: java
gi: 509
slug: tolist-toset
title: toList() / toSet()
---

## 1. What it is

`.toList()` (added in Java 16) is a terminal operation that collects a stream directly into an unmodifiable `List<T>` — a shorthand for `.collect(Collectors.toList())` (which by contrast returns a mutable `ArrayList`). There's no dedicated `.toSet()` method on `Stream` itself; the equivalent is `.collect(Collectors.toSet())`, which collects into a `Set<T>` (backed by a `HashSet` by default), automatically discarding duplicates and giving up any ordering guarantee.

## 2. Why & when

`.toList()` is the simplest, most common way to materialize a stream's results when you just need a `List` — it's shorter than `.collect(Collectors.toList())` and, being unmodifiable, communicates that the result isn't meant to be mutated further, catching accidental modification bugs at runtime rather than silently allowing them. `Collectors.toSet()` is what you reach for instead when you specifically want duplicates removed and don't care about (or actively don't want) a particular order — turning a stream of possibly-repeated values into a collection of only the distinct ones.

## 3. Core concept

```java
import java.util.*;
import java.util.stream.*;

List<String> names = Stream.of("Alice", "Bob", "Carol")
        .toList(); // unmodifiable List<String>

Set<Integer> uniqueScores = Stream.of(85, 92, 85, 78, 92)
        .collect(Collectors.toSet()); // {85, 92, 78} -- duplicates gone, order not guaranteed
```

`.toList()` preserves encounter order and rejects duplicates; `Collectors.toSet()` removes duplicates via `equals()`/`hashCode()` but makes no promise about iteration order.

## 4. Diagram

<svg viewBox="0 0 640 130" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="toList preserves order and duplicates; toSet removes duplicates with no order guarantee">
  <rect x="8" y="8" width="624" height="114" rx="8" fill="#0d1117"/>
  <text x="20" y="30" fill="#8b949e" font-size="11" font-family="sans-serif">.toList():</text>
  <rect x="120" y="15" width="40" height="28" fill="#1c2430" stroke="#6db33f"/><text x="140" y="34" fill="#6db33f" font-size="11" text-anchor="middle" font-family="monospace">85</text>
  <rect x="165" y="15" width="40" height="28" fill="#1c2430" stroke="#6db33f"/><text x="185" y="34" fill="#6db33f" font-size="11" text-anchor="middle" font-family="monospace">92</text>
  <rect x="210" y="15" width="40" height="28" fill="#1c2430" stroke="#6db33f"/><text x="230" y="34" fill="#6db33f" font-size="11" text-anchor="middle" font-family="monospace">85</text>
  <text x="290" y="34" fill="#8b949e" font-size="10" font-family="sans-serif">order + duplicates preserved</text>

  <text x="20" y="80" fill="#8b949e" font-size="11" font-family="sans-serif">.collect(toSet()):</text>
  <rect x="120" y="65" width="40" height="28" fill="#1c2430" stroke="#79c0ff"/><text x="140" y="84" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="monospace">85</text>
  <rect x="165" y="65" width="40" height="28" fill="#1c2430" stroke="#79c0ff"/><text x="185" y="84" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="monospace">92</text>
  <text x="270" y="84" fill="#8b949e" font-size="10" font-family="sans-serif">duplicates removed, order not guaranteed</text>
</svg>

`.toList()` keeps every element (including duplicates) in encounter order; `Collectors.toSet()` collapses duplicates and drops the ordering guarantee.

## 5. Runnable example

Scenario: processing a batch of quiz submissions to produce both an ordered record and a set of distinct participants — evolved from a plain `toList()`, through `Collectors.toSet()` for deduplication, to a version comparing the two side by side to highlight when each is the right choice.

### Level 1 — Basic

```java
import java.util.*;
import java.util.stream.*;

public class ToListBasic {
    public static void main(String[] args) {
        List<String> submissionOrder = List.of("alice", "bob", "alice", "carol").stream()
                .toList();

        System.out.println("Submission order: " + submissionOrder);
    }
}
```

**How to run:** `java ToListBasic.java`

Expected output:
```
Submission order: [alice, bob, alice, carol]
```

`.toList()` collects the stream into a `List<String>` that preserves both the original order and the duplicate `"alice"` entry — exactly matching the source, unmodified.

### Level 2 — Intermediate

```java
import java.util.*;
import java.util.stream.*;

public class ToSetBasic {
    public static void main(String[] args) {
        Set<String> uniqueParticipants = List.of("alice", "bob", "alice", "carol").stream()
                .collect(Collectors.toSet());

        System.out.println("Unique count: " + uniqueParticipants.size());
        System.out.println("Contains alice: " + uniqueParticipants.contains("alice"));
    }
}
```

**How to run:** `java ToSetBasic.java`

Expected output:
```
Unique count: 3
Contains alice: true
```

The real-world concern this adds: knowing *how many distinct* participants submitted, not the raw ordered submission log. `.collect(Collectors.toSet())` collapses the duplicate `"alice"` entries down to one, leaving three unique names — `alice`, `bob`, `carol` — with `.size()` confirming the count and `.contains(...)` confirming membership (checking, not printing, since the `Set`'s iteration order isn't guaranteed to be predictable).

### Level 3 — Advanced

```java
import java.util.*;
import java.util.stream.*;

public class ToListVsToSet {
    record Submission(String participant, int attemptNumber) {}

    public static void main(String[] args) {
        List<Submission> submissions = List.of(
                new Submission("alice", 1),
                new Submission("bob", 1),
                new Submission("alice", 2), // alice's second attempt -- a genuinely new event
                new Submission("carol", 1)
        );

        // toList: keep the full, ordered submission history -- every attempt matters here.
        List<String> attemptLog = submissions.stream()
                .map(s -> s.participant() + " (attempt " + s.attemptNumber() + ")")
                .toList();
        System.out.println("Full log: " + attemptLog);

        // toSet: just who participated at all, deduplicated -- attempt number doesn't matter here.
        Set<String> distinctParticipants = submissions.stream()
                .map(Submission::participant)
                .collect(Collectors.toSet());
        System.out.println("Distinct participants: " + distinctParticipants.size());
    }
}
```

**How to run:** `java ToListVsToSet.java`

Expected output:
```
Full log: [alice (attempt 1), bob (attempt 1), alice (attempt 2), carol (attempt 1)]
Distinct participants: 3
```

This shows the two collectors serving genuinely different purposes on the *same* source data: `.toList()` preserves every submission, including `alice`'s two separate attempts, since a full audit log needs every event. `.collect(Collectors.toSet())`, applied after `.map(Submission::participant)` reduces each submission down to just the participant's name, then deduplicates — `alice`'s two attempts collapse into one entry, correctly reporting `3` distinct participants (`alice`, `bob`, `carol`) rather than `4` submissions.

## 6. Walkthrough

Execution starts in `main` of the Level 3 example. `submissions` holds four entries, including two from `alice` (attempts `1` and `2`).

For the first output, `submissions.stream().map(s -> s.participant() + " (attempt " + s.attemptNumber() + ")")` transforms each `Submission` into a formatted string: `"alice (attempt 1)"`, `"bob (attempt 1)"`, `"alice (attempt 2)"`, `"carol (attempt 1)"`. `.toList()` collects these four distinct *strings* (they're all different strings, even though two share the same participant name) into an unmodifiable `List<String>`, preserving order — `attemptLog` has all four entries.

For the second output, `submissions.stream().map(Submission::participant)` transforms each `Submission` into just its `participant` field: `"alice"`, `"bob"`, `"alice"`, `"carol"` — note `"alice"` now appears twice as an *identical* string (unlike the first mapping, where the attempt number made each string unique). `.collect(Collectors.toSet())` processes these: `"alice"` is added (new), `"bob"` is added (new), the second `"alice"` is attempted but already present in the set (via `equals()`), so it's silently not added again, `"carol"` is added (new). The resulting `Set<String>` has exactly three elements: `{"alice", "bob", "carol"}`.

```
map to "name (attempt N)":  4 distinct strings -> toList() keeps all 4
map to just "name":         "alice","bob","alice","carol" -> toSet() dedupes "alice" -> 3 elements
```

`attemptLog` prints as `"[alice (attempt 1), bob (attempt 1), alice (attempt 2), carol (attempt 1)]"` — all four entries, in order. `distinctParticipants.size()` is `3`, printed as `"Distinct participants: 3"` — demonstrating that whether duplicates matter depends entirely on *what* you mapped each element to before collecting: including the attempt number kept every submission unique, while dropping it revealed the underlying repetition.

## 7. Gotchas & takeaways

> `.toList()`'s result is genuinely **unmodifiable** — calling `.add(...)`, `.remove(...)`, or `.set(...)` on it throws `UnsupportedOperationException`. This differs from `.collect(Collectors.toList())`, which (as an implementation detail, not a documented guarantee) typically returns a mutable `ArrayList`. If you need a mutable result, use `.collect(Collectors.toCollection(ArrayList::new))` (see [[tocollection]]) or explicitly wrap `.toList()`'s result in `new ArrayList<>(...)`.

- `.toList()` is a concise shorthand for collecting into an unmodifiable `List<T>`, preserving encounter order and all duplicates.
- `Collectors.toSet()` (there's no `.toSet()` shorthand directly on `Stream`) collects into a `Set<T>`, removing duplicates via `equals()`/`hashCode()`, with no guaranteed iteration order.
- Whether duplicates "exist" depends on what you mapped elements to before collecting — mapping to a more detailed value (like including an attempt number) can make otherwise-identical source records appear distinct.
- `.toList()`'s result is unmodifiable and will throw if mutated; don't assume it behaves like a plain `ArrayList`.
- For a `Set` with a specific ordering (insertion order, sorted order), use `Collectors.toCollection(LinkedHashSet::new)` or `Collectors.toCollection(TreeSet::new)` instead of the default, order-agnostic `Collectors.toSet()`.
