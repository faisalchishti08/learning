---
card: java
gi: 495
slug: sorted-sorted-comparator
title: sorted() / sorted(Comparator)
---

## 1. What it is

`Stream.sorted()` returns a stream with the same elements as the source, arranged in their **natural order** — which requires the elements to implement `Comparable` (like `String`, `Integer`, or any custom class that defines `compareTo`). `Stream.sorted(Comparator<T>)` instead uses an explicit `Comparator` you supply, so it works on types without natural ordering, or to sort by a different rule (descending, by a specific field, by multiple criteria). Both are intermediate operations that must see every element before producing output — sorting can't happen element by element.

## 2. Why & when

Any time a stream's output needs to be in a specific order rather than whatever order the source happened to provide — alphabetical names, prices low to high, most recent first — `sorted()` handles it as one pipeline step instead of collecting to a `List` and calling `Collections.sort` separately. The no-argument form is for simple, natural comparisons; the `Comparator` form is for everything else: custom objects, reversed order, or sorting by one field while breaking ties with another.

`Comparator.comparing(keyExtractor)` is the most common way to build a comparator from a field, and it chains with `.reversed()` (to flip direction) and `.thenComparing(...)` (to add a tiebreaker) to build up more complex ordering rules without writing a manual `compareTo` implementation.

## 3. Core concept

```java
import java.util.*;
import java.util.stream.*;

record Person(String name, int age) {}

List<String> names = Stream.of("Carol", "Alice", "Bob")
        .sorted() // natural order -- String implements Comparable
        .toList(); // [Alice, Bob, Carol]

List<Person> people = Stream.of(new Person("Bob", 30), new Person("Alice", 25))
        .sorted(Comparator.comparing(Person::age)) // explicit comparator: Person has no natural order
        .toList(); // [Person(Alice,25), Person(Bob,30)]
```

`sorted()` needs `Comparable` elements; `sorted(comparator)` works on anything, using whatever ordering rule the comparator defines.

## 4. Diagram

<svg viewBox="0 0 640 130" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="sorted arranges stream elements according to natural order or a supplied comparator">
  <rect x="8" y="8" width="624" height="114" rx="8" fill="#0d1117"/>
  <rect x="30" y="20" width="70" height="30" fill="#1c2430" stroke="#79c0ff"/><text x="65" y="40" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="monospace">Carol</text>
  <rect x="110" y="20" width="70" height="30" fill="#1c2430" stroke="#79c0ff"/><text x="145" y="40" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="monospace">Alice</text>
  <rect x="190" y="20" width="70" height="30" fill="#1c2430" stroke="#79c0ff"/><text x="225" y="40" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="monospace">Bob</text>
  <text x="140" y="70" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">sorted()</text>
  <line x1="140" y1="52" x2="140" y2="85" stroke="#8b949e" stroke-width="1.5" marker-end="url(#arrowS)"/>
  <rect x="30" y="90" width="70" height="30" fill="#1c2430" stroke="#6db33f"/><text x="65" y="110" fill="#6db33f" font-size="11" text-anchor="middle" font-family="monospace">Alice</text>
  <rect x="110" y="90" width="70" height="30" fill="#1c2430" stroke="#6db33f"/><text x="145" y="110" fill="#6db33f" font-size="11" text-anchor="middle" font-family="monospace">Bob</text>
  <rect x="190" y="90" width="70" height="30" fill="#1c2430" stroke="#6db33f"/><text x="225" y="110" fill="#6db33f" font-size="11" text-anchor="middle" font-family="monospace">Carol</text>
  <defs><marker id="arrowS" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

`sorted()` rearranges every element into order — unlike `filter`/`map`, it must buffer the whole stream before it can emit anything.

## 5. Runnable example

Scenario: ranking a leaderboard of players by score — evolved from natural-order sorting of plain numbers, through comparator-based sorting by a custom object's field with reversed (highest-first) order, to a version with multi-level sorting that breaks ties with a secondary key.

### Level 1 — Basic

```java
import java.util.*;
import java.util.stream.*;

public class SortedBasic {
    public static void main(String[] args) {
        List<Integer> scores = List.of(42, 17, 99, 3, 56);

        List<Integer> ascending = scores.stream()
                .sorted()
                .toList();

        System.out.println("Ascending: " + ascending);
    }
}
```

**How to run:** `java SortedBasic.java`

Expected output:
```
Ascending: [3, 17, 42, 56, 99]
```

`.sorted()` with no argument uses `Integer`'s natural ordering (numeric, ascending), since `Integer` implements `Comparable<Integer>`. The five scores come out arranged from lowest to highest.

### Level 2 — Intermediate

```java
import java.util.*;
import java.util.stream.*;

public class SortedComparator {
    record Player(String name, int score) {}

    public static void main(String[] args) {
        List<Player> players = List.of(
                new Player("Alice", 42),
                new Player("Bob", 99),
                new Player("Carol", 17)
        );

        List<Player> leaderboard = players.stream()
                .sorted(Comparator.comparing(Player::score).reversed()) // highest score first
                .toList();

        leaderboard.forEach(p -> System.out.println(p.name() + ": " + p.score()));
    }
}
```

**How to run:** `java SortedComparator.java`

Expected output:
```
Bob: 99
Alice: 42
Carol: 17
```

The real-world concern this adds: `Player` has no natural order (it's a `record` without `Comparable`), so `sorted()` alone wouldn't compile — `Comparator.comparing(Player::score)` builds a comparator that orders by the `score` field, and `.reversed()` flips it so the *highest* score comes first, matching how leaderboards are normally displayed.

### Level 3 — Advanced

```java
import java.util.*;
import java.util.stream.*;

public class SortedMultiLevel {
    record Player(String name, int score, long submittedAtMillis) {}

    public static void main(String[] args) {
        List<Player> players = List.of(
                new Player("Alice", 99, 2000),
                new Player("Bob", 99, 1000), // same score as Alice, but submitted earlier
                new Player("Carol", 42, 500),
                new Player("Dave", 99, 1500)
        );

        // Primary: highest score first. Tiebreaker: earlier submission time first (rewards speed).
        List<Player> leaderboard = players.stream()
                .sorted(Comparator.comparing(Player::score).reversed()
                        .thenComparing(Player::submittedAtMillis))
                .toList();

        leaderboard.forEach(p -> System.out.println(p.name() + ": score=" + p.score() + ", at=" + p.submittedAtMillis()));
    }
}
```

**How to run:** `java SortedMultiLevel.java`

Expected output:
```
Bob: score=99, at=1000
Dave: score=99, at=1500
Alice: score=99, at=2000
Carol: score=42, at=500
```

This adds a real leaderboard concern: ties. Three players share the top score of `99`, so a single-key sort by score alone would leave their relative order unspecified (implementation-dependent for a non-stable-guaranteed comparison, though Java's sort is actually stable — but relying on insertion order for a tie isn't a real ranking rule). `.thenComparing(Player::submittedAtMillis)` adds an explicit tiebreaker: among equal scores, the player who submitted *earliest* ranks higher — `Bob` (`1000`) beats `Dave` (`1500`) beats `Alice` (`2000`), all before the lower-scoring `Carol`.

## 6. Walkthrough

Execution starts in `main` of the Level 3 example. Four players are defined; three (`Alice`, `Bob`, `Dave`) share a score of `99`, while `Carol` has `42`.

`Comparator.comparing(Player::score).reversed()` builds a comparator that first compares two players by `score` (ascending, natural `Integer` order), then `.reversed()` flips the comparison result so higher scores sort first. `.thenComparing(Player::submittedAtMillis)` chains a second comparator: whenever the first comparator reports two players as *equal* (same score), this second one breaks the tie by comparing `submittedAtMillis` in ascending order (earlier timestamps first) — `.thenComparing` is only ever consulted when the primary comparator returns zero.

`sorted(...)` must see the entire stream before it can produce any output, since sorting requires knowing every element up front. Internally, it compares pairs of players using the combined comparator: comparing `Alice` (score 99) and `Carol` (score 42), the reversed score comparator alone decides `Alice` comes first (higher score) — the tiebreaker is never consulted for this pair, since the scores already differ.

Comparing `Alice` (99, 2000) and `Bob` (99, 1000): the reversed score comparator sees equal scores (`99 == 99`), returns `0`, so `.thenComparing` is consulted — it compares `2000` vs `1000` ascending, so `Bob` (`1000`, earlier) sorts before `Alice` (`2000`, later). Similarly, comparing `Bob` (1000) and `Dave` (1500): tied on score, tiebreaker compares timestamps, `Bob` (earlier) sorts before `Dave`. Comparing `Dave` (1500) and `Alice` (2000): tied on score, tiebreaker puts `Dave` (earlier) before `Alice`.

```
Score comparison (reversed, high first):  {Alice,Bob,Dave}=99  >  Carol=42
Within the {Alice,Bob,Dave} tie, thenComparing(submittedAtMillis) ascending:
   Bob(1000) < Dave(1500) < Alice(2000)

Final order: Bob, Dave, Alice, Carol
```

The fully sorted result is `Bob, Dave, Alice, Carol` — the three tied-score players ordered by submission speed (fastest first), with `Carol`'s lower score placing her last regardless of her earlier `500` timestamp, since the primary key (score) always takes precedence over the tiebreaker.

## 7. Gotchas & takeaways

> Calling `.sorted()` (no arguments) on a stream of a type that doesn't implement `Comparable` throws `ClassCastException` at runtime, not a compile error, since the check happens when elements are actually compared during the terminal operation. For custom types without natural ordering (most `record`s and plain classes), always supply an explicit `Comparator` via `sorted(Comparator)`.

- `sorted()` uses natural ordering (`Comparable`); `sorted(Comparator)` uses an explicit rule and works on any type.
- `Comparator.comparing(keyExtractor)` builds a comparator from a field or derived key; `.reversed()` flips its direction; `.thenComparing(...)` adds a tiebreaker consulted only when the earlier comparator(s) report equality.
- Sorting is a **stateful** intermediate operation — unlike `filter`/`map`, it must consume the entire stream before producing its first output element, since any element could affect any other element's final position.
- Java's sort is stable: elements that compare as exactly equal keep their original relative order, which is why an explicit `thenComparing` tiebreaker matters whenever tie order should follow a real rule rather than incidental input order.
- For descending order on a natural-order type, `Comparator.reverseOrder()` (or `.sorted(Comparator.naturalOrder().reversed())`) is a shorter alternative to `sorted(Comparator.comparing(x -> x).reversed())`.
