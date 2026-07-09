---
card: java
gi: 504
slug: min-max
title: min() / max()
---

## 1. What it is

`Stream.min(Comparator)` and `Stream.max(Comparator)` are terminal operations that find the smallest or largest element of a stream, according to the given `Comparator`, and return it wrapped in an `Optional<T>` — empty if the stream had no elements. Unlike `sorted()`, which arranges the whole stream, `min`/`max` only need to find one element, and can do so in a single pass without buffering everything.

## 2. Why & when

`min`/`max` are how you find "the smallest" or "the largest" element by some rule — the cheapest item, the oldest record, the highest score. They're more direct and efficient than `sorted(comparator).findFirst()` for this specific purpose, since they don't need to fully order the stream, just track the best candidate seen so far as they scan through. Both take an explicit `Comparator`, since — like `sorted(Comparator)` — the stream's element type may not have a natural ordering, or you may want to compare by something other than natural order.

## 3. Core concept

```java
import java.util.*;
import java.util.stream.*;

record Player(String name, int score) {}

List<Player> players = List.of(new Player("Alice", 42), new Player("Bob", 99));

Optional<Player> topPlayer = players.stream()
        .max(Comparator.comparing(Player::score)); // Optional[Player(Bob, 99)]

Optional<Integer> smallest = Stream.of(5, 2, 8, 1).min(Comparator.naturalOrder()); // Optional[1]
```

Both `min` and `max` scan the stream once, keeping track of the best element seen so far according to the comparator, and return it wrapped in `Optional` to account for a possibly-empty stream.

## 4. Diagram

<svg viewBox="0 0 640 120" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="max scans a stream once and returns the largest element according to a comparator">
  <rect x="8" y="8" width="624" height="104" rx="8" fill="#0d1117"/>
  <rect x="30" y="20" width="50" height="30" fill="#1c2430" stroke="#79c0ff"/><text x="55" y="40" fill="#79c0ff" font-size="12" text-anchor="middle" font-family="monospace">42</text>
  <rect x="90" y="20" width="50" height="30" fill="#1c2430" stroke="#6db33f" stroke-width="2.5"/><text x="115" y="40" fill="#6db33f" font-size="12" text-anchor="middle" font-family="monospace">99</text>
  <rect x="150" y="20" width="50" height="30" fill="#1c2430" stroke="#79c0ff"/><text x="175" y="40" fill="#79c0ff" font-size="12" text-anchor="middle" font-family="monospace">17</text>
  <rect x="210" y="20" width="50" height="30" fill="#1c2430" stroke="#79c0ff"/><text x="235" y="40" fill="#79c0ff" font-size="12" text-anchor="middle" font-family="monospace">65</text>
  <text x="130" y="75" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">max() finds 99 in one pass -- no full sort needed</text>
</svg>

`max` (highlighted in green) is found by scanning once and comparing each element against the best candidate so far — the stream never needs to be fully sorted.

## 5. Runnable example

Scenario: finding notable data points in a stream of temperature readings — evolved from a basic natural-order min/max, through comparator-based min/max on a custom object field, to a version that finds both extremes and computes the range in a single pass without scanning the data twice.

### Level 1 — Basic

```java
import java.util.*;
import java.util.stream.*;

public class MinMaxBasic {
    public static void main(String[] args) {
        List<Integer> temperatures = List.of(68, 72, 55, 90, 61);

        Optional<Integer> coldest = temperatures.stream().min(Comparator.naturalOrder());
        Optional<Integer> hottest = temperatures.stream().max(Comparator.naturalOrder());

        System.out.println("Coldest: " + coldest.orElse(null));
        System.out.println("Hottest: " + hottest.orElse(null));
    }
}
```

**How to run:** `java MinMaxBasic.java`

Expected output:
```
Coldest: 55
Hottest: 90
```

`Comparator.naturalOrder()` uses `Integer`'s built-in numeric ordering. `.min(...)` scans the five temperatures and returns `55` (the lowest); `.max(...)` scans and returns `90` (the highest) — each call is a separate pass over a fresh stream, since a stream can only be consumed once.

### Level 2 — Intermediate

```java
import java.util.*;
import java.util.stream.*;

public class MinMaxComparator {
    record Reading(String station, int temperature) {}

    public static void main(String[] args) {
        List<Reading> readings = List.of(
                new Reading("A", 68),
                new Reading("B", 90),
                new Reading("C", 55)
        );

        Optional<Reading> hottest = readings.stream()
                .max(Comparator.comparing(Reading::temperature));

        hottest.ifPresent(r -> System.out.println(r.station() + " recorded the highest: " + r.temperature()));
    }
}
```

**How to run:** `java MinMaxComparator.java`

Expected output:
```
B recorded the highest: 90
```

The real-world concern this adds: `Reading` has no natural order, so `Comparator.comparing(Reading::temperature)` builds an explicit comparator that orders readings by their `temperature` field. `.max(...)` then finds the *whole* `Reading` object with the highest temperature — not just the number — so the result retains which station recorded it.

### Level 3 — Advanced

```java
import java.util.*;
import java.util.stream.*;

public class MinMaxSinglePass {
    record Reading(String station, int temperature) {}
    record Range(Optional<Reading> coldest, Optional<Reading> hottest) {}

    public static void main(String[] args) {
        List<Reading> readings = List.of(
                new Reading("A", 68),
                new Reading("B", 90),
                new Reading("C", 55),
                new Reading("D", 61)
        );

        Comparator<Reading> byTemp = Comparator.comparing(Reading::temperature);

        // Single pass: track both running min and max together, instead of streaming the list twice.
        Range range = readings.stream()
                .reduce(
                        new Range(Optional.empty(), Optional.empty()),
                        (acc, reading) -> new Range(
                                acc.coldest().isEmpty() || byTemp.compare(reading, acc.coldest().get()) < 0
                                        ? Optional.of(reading) : acc.coldest(),
                                acc.hottest().isEmpty() || byTemp.compare(reading, acc.hottest().get()) > 0
                                        ? Optional.of(reading) : acc.hottest()),
                        (r1, r2) -> r1 // sequential stream -- combiner not actually invoked
                );

        range.coldest().ifPresent(r -> System.out.println("Coldest: " + r.station() + " at " + r.temperature()));
        range.hottest().ifPresent(r -> System.out.println("Hottest: " + r.station() + " at " + r.temperature()));
    }
}
```

**How to run:** `java MinMaxSinglePass.java`

Expected output:
```
Coldest: C at 55
Hottest: B at 90
```

This computes both the minimum and maximum in a **single pass** using the three-argument `reduce` (see [[reduce-3-forms]]), rather than calling `.min(...)` and `.max(...)` separately (which would each independently scan the whole stream — fine for small data, but wasteful for a very large or expensive-to-recompute source). The accumulator tracks both a running `coldest` and `hottest` `Optional<Reading>` together, updating each independently as every element is visited exactly once.

## 6. Walkthrough

Execution starts in `main` of the Level 3 example. Four readings are defined: `A=68`, `B=90`, `C=55`, `D=61`.

`readings.stream().reduce(new Range(Optional.empty(), Optional.empty()), (acc, reading) -> ..., (r1, r2) -> r1)` begins with `Range(empty, empty)`. Processing `A` (68): `acc.coldest().isEmpty()` is `true` (nothing recorded yet), so the new coldest becomes `Optional.of(A)`; similarly `acc.hottest().isEmpty()` is `true`, so the new hottest becomes `Optional.of(A)`. Running state: `Range(A, A)`.

Processing `B` (90): `acc.coldest()` is `A` (68) — not empty, so compare `byTemp.compare(B, A)`, i.e. `90` vs `68`, which is positive (`B` is *not* colder), so coldest stays `A`. `acc.hottest()` is `A` (68) — compare `byTemp.compare(B, A)` is positive (`B` is hotter), so hottest becomes `B`. Running state: `Range(A, B)`.

Processing `C` (55): compare `byTemp.compare(C, A)`, i.e. `55` vs `68`, which is negative (`C` is colder), so coldest becomes `C`. Compare `byTemp.compare(C, B)`, i.e. `55` vs `90`, negative (`C` is not hotter), so hottest stays `B`. Running state: `Range(C, B)`.

Processing `D` (61): compare `byTemp.compare(D, C)`, i.e. `61` vs `55`, positive (`D` is not colder than `C`), so coldest stays `C`. Compare `byTemp.compare(D, B)`, i.e. `61` vs `90`, negative (`D` is not hotter than `B`), so hottest stays `B`. Final state: `Range(C, B)`.

```
start:        Range(empty, empty)
+ A(68):      coldest=A (first), hottest=A (first)          -> Range(A, A)
+ B(90):      90 vs 68 not colder; 90 vs 68 IS hotter        -> Range(A, B)
+ C(55):      55 vs 68 IS colder; 55 vs 90 not hotter         -> Range(C, B)
+ D(61):      61 vs 55 not colder; 61 vs 90 not hotter        -> Range(C, B)  (unchanged)
```

The final `range` is `Range(Optional.of(C), Optional.of(B))` — `C` (55) is the coldest, `B` (90) is the hottest, found in one pass through the four readings rather than two separate scans. `main` prints `"Coldest: C at 55"` and `"Hottest: B at 90"`.

## 7. Gotchas & takeaways

> `.min(...)` and `.max(...)` both consume the entire stream they're called on — you cannot call `.min(...)` and then `.max(...)` on the *same* stream instance, since the first call exhausts it. Level 1 works around this by calling `.stream()` twice from the source `List` to get two fresh streams; a truly single-pass computation of both requires combining the logic into one traversal, as shown in Level 3.

- `min(comparator)`/`max(comparator)` find the smallest/largest element in a single pass, returning `Optional<T>` to handle the empty-stream case.
- Both require an explicit `Comparator` — there's no no-argument overload, since not every type has a natural order and the "best" element depends on the ordering rule chosen.
- For types with natural ordering, `Comparator.naturalOrder()` (ascending) or `Comparator.reverseOrder()` (descending) are convenient built-in comparators.
- `min`/`max` are more efficient than `sorted(comparator).findFirst()`/`.reduce(...)` for finding a single extreme, since they don't need to fully order the stream.
- A stream can only be consumed once — computing both a minimum and a maximum requires either two separate stream instances (simple, two passes) or combining both computations into one `reduce` call (more code, one pass) as shown in Level 3.
