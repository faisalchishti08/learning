---
card: java
gi: 560
slug: comparator-improvements-comparing-thencomparing-reversed
title: Comparator improvements (comparing, thenComparing, reversed)
---

## 1. What it is

Java 8 added default and static methods to the `Comparator` interface — `Comparator.comparing(keyExtractor)`, `.thenComparing(...)` for tie-breaking on a secondary key, and `.reversed()` for flipping the order — letting you build multi-key comparators by chaining small, readable pieces instead of writing a single hand-rolled `compare` method full of nested `if` statements.

## 2. Why & when

Before Java 8, sorting a list of people by last name, then first name, then age required an anonymous `Comparator<Person>` with manually nested comparisons: compare last names, if equal compare first names, if still equal compare ages. That code is easy to get wrong (forgetting a tie-break, inverted logic) and tedious to read. `Comparator.comparing(...).thenComparing(...).thenComparing(...)` expresses exactly the same logic declaratively, one key at a time, and reads in the same order you'd describe the sort verbally: "by last name, then first name, then age." Reach for this any time you sort by more than one field, or need ascending/descending on a specific field.

## 3. Core concept

```java
record Person(String lastName, String firstName, int age) {}

Comparator<Person> byName = Comparator
    .comparing(Person::lastName)
    .thenComparing(Person::firstName);

Comparator<Person> byNameThenAgeDesc = byName.thenComparing(Comparator.comparingInt(Person::age).reversed());

people.sort(byNameThenAgeDesc);
```

`comparing(keyExtractor)` builds a `Comparator` from a function that extracts a `Comparable` key. `thenComparing(...)` is only consulted when the previous comparator considers two elements equal — it's a tie-breaker, not a replacement. `.reversed()` flips any comparator's result, ascending to descending or vice versa.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="thenComparing only runs when the previous comparator reports a tie">
  <rect x="20" y="10" width="200" height="40" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="120" y="35" fill="#6db33f" font-size="11" text-anchor="middle" font-family="monospace">comparing(lastName)</text>

  <line x1="220" y1="30" x2="270" y2="30" stroke="#8b949e" stroke-width="1.5" marker-end="url(#d1)"/>
  <text x="245" y="20" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">tie?</text>

  <rect x="270" y="10" width="220" height="40" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="380" y="35" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="monospace">thenComparing(firstName)</text>

  <line x1="490" y1="30" x2="540" y2="30" stroke="#8b949e" stroke-width="1.5" marker-end="url(#d2)"/>
  <text x="515" y="20" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">tie?</text>

  <rect x="20" y="90" width="600" height="34" rx="6" fill="#0d1117"/>
  <text x="30" y="112" fill="#e6edf3" font-size="10" font-family="sans-serif">Smith,Anna beats Smith,Bob because "Anna" &lt; "Bob" — lastName tied, firstName decided it.</text>
  <rect x="20" y="130" width="600" height="34" rx="6" fill="#0d1117"/>
  <text x="30" y="152" fill="#e6edf3" font-size="10" font-family="sans-serif">Jones,Carl beats Smith,Anna outright — lastName alone already decided it, no tie-break needed.</text>

  <defs>
    <marker id="d1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker>
    <marker id="d2" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

Each `thenComparing` step is skipped entirely whenever an earlier step already found a difference.

## 5. Runnable example

Scenario: sorting a leaderboard of game players — starting with a single-key sort by score, then adding a tie-break by name, then building a full multi-key comparator mixing ascending and descending directions across three fields.

### Level 1 — Basic

```java
import java.util.*;

public class LeaderboardBasic {
    record Player(String name, int score) {}

    public static void main(String[] args) {
        List<Player> players = new ArrayList<>(List.of(
            new Player("Ravi", 87),
            new Player("Mona", 95),
            new Player("Cy", 95),
            new Player("Deb", 60)
        ));

        players.sort(Comparator.comparingInt(Player::score).reversed());
        players.forEach(p -> System.out.println(p.name() + ": " + p.score()));
    }
}
```

**How to run:** `java LeaderboardBasic.java`

Expected output:
```
Mona: 95
Cy: 95
Ravi: 87
Deb: 60
```

`Comparator.comparingInt(Player::score)` builds an ascending-by-score comparator; `.reversed()` flips it to descending. `players.sort(...)` reorders the list in place using that comparator. Mona and Cy both score 95 and are tied — with only one sort key, their *relative* order is whatever a stable sort preserves from the original list order (Mona was listed before Cy in the source list, and `List.sort` is guaranteed stable, so Mona stays before Cy in the output).

### Level 2 — Intermediate

```java
import java.util.*;

public class LeaderboardTieBreak {
    record Player(String name, int score) {}

    public static void main(String[] args) {
        List<Player> players = new ArrayList<>(List.of(
            new Player("Ravi", 87),
            new Player("Mona", 95),
            new Player("Cy", 95),
            new Player("Deb", 60)
        ));

        Comparator<Player> byScoreThenName = Comparator
            .comparingInt(Player::score).reversed()
            .thenComparing(Player::name);

        players.sort(byScoreThenName);
        players.forEach(p -> System.out.println(p.name() + ": " + p.score()));
    }
}
```

**How to run:** `java LeaderboardTieBreak.java`

Expected output:
```
Cy: 95
Mona: 95
Ravi: 87
Deb: 60
```

The real-world concern this adds: an explicit, deterministic tie-break instead of relying on incoming list order (which is fragile — it would silently change if the input order changed). `.thenComparing(Player::name)` only activates when scores are equal: Cy and Mona both have 95, so their tie is broken alphabetically by name (`"Cy"` < `"Mona"`), placing Cy first — independent of which one appeared first in the original list.

### Level 3 — Advanced

```java
import java.util.*;

public class LeaderboardMultiKey {
    record Player(String team, String name, int score, int level) {}

    public static void main(String[] args) {
        List<Player> players = new ArrayList<>(List.of(
            new Player("Red",  "Ravi", 87, 4),
            new Player("Blue", "Mona", 95, 6),
            new Player("Blue", "Cy",   95, 3),
            new Player("Red",  "Deb",  87, 7)
        ));

        // Team ascending (alphabetical), then score descending (best first),
        // then level descending as a final tie-break.
        Comparator<Player> ranking = Comparator
            .comparing(Player::team)
            .thenComparing(Comparator.comparingInt(Player::score).reversed())
            .thenComparing(Comparator.comparingInt(Player::level).reversed());

        players.sort(ranking);
        players.forEach(p ->
            System.out.println(p.team() + " | " + p.name() + " | score=" + p.score() + " | level=" + p.level()));
    }
}
```

**How to run:** `java LeaderboardMultiKey.java`

Expected output:
```
Blue | Mona | score=95 | level=6
Blue | Cy | score=95 | level=3
Red | Deb | score=87 | level=7
Red | Ravi | score=87 | level=4
```

This handles the production-flavoured case of ranking across **three keys with mixed directions**: team ascending (grouping alphabetically), score descending within a team (best performers first), and level descending as a final tie-break when both team and score match. Each `.thenComparing(...)` step wraps its own `.reversed()` independently, so ascending and descending directions can be mixed freely within a single comparator chain.

## 6. Walkthrough

Execution starts in `main` of the Level 3 example. `players` holds four records across two teams: Blue (Mona 95/6, Cy 95/3) and Red (Ravi 87/4, Deb 87/7).

`ranking` is built as a three-step chain. `players.sort(ranking)` invokes a stable sort that, for each pairwise comparison, evaluates the chain step by step until a non-zero result is found:

```
compare(Mona, Cy):    team "Blue"=="Blue" (tie) -> score 95==95 (tie) -> level 6 vs 3, reversed -> 6 wins (Mona first)
compare(Ravi, Deb):   team "Red"=="Red" (tie)   -> score 87==87 (tie) -> level 4 vs 7, reversed -> 7 wins (Deb first)
compare(Blue*, Red*): team "Blue" vs "Red" (alphabetical) -> "Blue" < "Red" -> Blue group sorts first
```

Tracing the first comparison in detail: `Comparator.comparing(Player::team)` compares `"Blue"` to `"Blue"` — equal, so control passes to the next link in the chain. `Comparator.comparingInt(Player::score).reversed()` compares `95` to `95` — also equal (reversing a tie is still a tie), so control passes to the final link. `Comparator.comparingInt(Player::level).reversed()` compares `6` to `3`; since this comparator is reversed, a *higher* level counts as "less than" for sort-order purposes, so Mona (level 6) sorts before Cy (level 3).

The same logic applies within the Red team: scores tie at 87, so the reversed level comparison decides — Deb's level 7 beats Ravi's level 4, placing Deb first.

Between the two teams, the very first comparator step (`team`) already produces a non-zero result (`"Blue"` < `"Red"`), so neither the score nor level comparators are even consulted for any Blue-vs-Red pair — the chain short-circuits at the first deciding key, exactly like the diagram in part 4 illustrates.

The final printed order groups all Blue players before all Red players, with Mona before Cy inside Blue, and Deb before Ravi inside Red — reflecting all three keys applied in priority order.

## 7. Gotchas & takeaways

> `.reversed()` reverses **that specific comparator's** result, not the whole chain built so far unless you call it on the fully-chained comparator. `Comparator.comparing(Player::team).thenComparing(Player::score).reversed()` reverses the *entire* combined ordering (team and score both flip), which is usually not what's intended — to reverse only the score while keeping team ascending, reverse the score comparator individually before chaining it in, as done in the Level 3 example.

- `thenComparing(...)` is a pure tie-breaker: it is never consulted if an earlier comparator in the chain already found a difference.
- `Comparator.comparing(Person::lastName)` requires the extracted key type to implement `Comparable` (e.g., `String`, `Integer`); for primitives, use `comparingInt`, `comparingLong`, or `comparingDouble` to avoid unnecessary boxing.
- `List.sort(...)` and `Collections.sort(...)` are guaranteed **stable** — elements that compare equal keep their original relative order, which is why an explicit tie-break (rather than relying on incoming order) is important whenever the caller's input order shouldn't matter to correctness.
- `Comparator.naturalOrder()` and `.reverseOrder()` exist as ready-made comparators for `Comparable` types when no key extraction is needed.
- `thenComparing` has overloads accepting either a key extractor (`thenComparing(Player::name)`) or a full `Comparator` (`thenComparing(someComparator)`) — use the latter when you need `.reversed()` on that specific step.
