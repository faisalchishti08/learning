---
card: java
gi: 490
slug: filter
title: filter()
---

## 1. What it is

`Stream.filter(predicate)` returns a new stream containing only the elements of the source stream for which the given `Predicate<T>` returns `true`. It's an **intermediate** operation — lazy, and it doesn't run until a terminal operation (like `.count()`, `.toList()`, `.forEach()`) drives the pipeline. Elements that don't match the predicate are simply dropped; nothing is mutated.

## 2. Why & when

`filter` is the streams equivalent of an `if` check inside a loop that only does something when a condition holds — but expressed declaratively as part of a pipeline instead of imperative control flow. You reach for it any time you want to keep only some elements of a stream based on a condition: active users, orders above a threshold, valid inputs, non-null values. It's almost always the first step in a longer pipeline, narrowing the data down before `map`, `sorted`, or a terminal collection operation runs.

## 3. Core concept

```java
import java.util.stream.*;

List<Integer> evens = Stream.of(1, 2, 3, 4, 5, 6)
        .filter(n -> n % 2 == 0)
        .toList(); // [2, 4, 6]
```

`filter` takes a `Predicate<T>` — a function from `T` to `boolean` — and keeps only the elements where it returns `true`. Elements are evaluated one at a time, lazily, as the pipeline is driven by whatever terminal operation follows.

## 4. Diagram

<svg viewBox="0 0 640 130" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="filter keeps only elements matching a predicate, dropping the rest">
  <rect x="8" y="8" width="624" height="114" rx="8" fill="#0d1117"/>
  <rect x="30" y="20" width="50" height="30" fill="#1c2430" stroke="#79c0ff"/><text x="55" y="40" fill="#79c0ff" font-size="12" text-anchor="middle" font-family="monospace">1</text>
  <rect x="90" y="20" width="50" height="30" fill="#1c2430" stroke="#79c0ff"/><text x="115" y="40" fill="#79c0ff" font-size="12" text-anchor="middle" font-family="monospace">2</text>
  <rect x="150" y="20" width="50" height="30" fill="#1c2430" stroke="#79c0ff"/><text x="175" y="40" fill="#79c0ff" font-size="12" text-anchor="middle" font-family="monospace">3</text>
  <rect x="210" y="20" width="50" height="30" fill="#1c2430" stroke="#79c0ff"/><text x="235" y="40" fill="#79c0ff" font-size="12" text-anchor="middle" font-family="monospace">4</text>
  <text x="140" y="70" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">filter(n -&gt; n % 2 == 0)</text>
  <line x1="140" y1="52" x2="140" y2="85" stroke="#8b949e" stroke-width="1.5" marker-end="url(#arrowF)"/>
  <rect x="90" y="90" width="50" height="30" fill="#1c2430" stroke="#6db33f"/><text x="115" y="110" fill="#6db33f" font-size="12" text-anchor="middle" font-family="monospace">2</text>
  <rect x="150" y="90" width="50" height="30" fill="#1c2430" stroke="#6db33f"/><text x="175" y="110" fill="#6db33f" font-size="12" text-anchor="middle" font-family="monospace">4</text>
  <defs><marker id="arrowF" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Only elements where the predicate returns `true` survive into the resulting stream — `1` and `3` are dropped.

## 5. Runnable example

Scenario: screening job applicants against eligibility rules — evolved from a single-condition filter, through combining multiple conditions, to a version driven by a dynamic, composable set of rules.

### Level 1 — Basic

```java
import java.util.*;
import java.util.stream.*;

public class FilterBasic {
    record Applicant(String name, int yearsExperience) {}

    public static void main(String[] args) {
        List<Applicant> applicants = List.of(
                new Applicant("Alice", 5),
                new Applicant("Bob", 1),
                new Applicant("Carol", 3)
        );

        List<String> eligible = applicants.stream()
                .filter(a -> a.yearsExperience() >= 3)
                .map(Applicant::name)
                .toList();

        System.out.println("Eligible: " + eligible);
    }
}
```

**How to run:** `java FilterBasic.java`

Expected output:
```
Eligible: [Alice, Carol]
```

`.filter(a -> a.yearsExperience() >= 3)` keeps only applicants with at least three years of experience — `Bob` (one year) is dropped, `Alice` (five) and `Carol` (three) survive. `.map(Applicant::name)` then extracts just their names.

### Level 2 — Intermediate

```java
import java.util.*;
import java.util.stream.*;

public class FilterCombined {
    record Applicant(String name, int yearsExperience, boolean hasReferences) {}

    public static void main(String[] args) {
        List<Applicant> applicants = List.of(
                new Applicant("Alice", 5, true),
                new Applicant("Bob", 1, true),
                new Applicant("Carol", 3, false),
                new Applicant("Dave", 4, true)
        );

        List<String> eligible = applicants.stream()
                .filter(a -> a.yearsExperience() >= 3)
                .filter(Applicant::hasReferences) // second filter -- both conditions must hold
                .map(Applicant::name)
                .toList();

        System.out.println("Eligible: " + eligible);
    }
}
```

**How to run:** `java FilterCombined.java`

Expected output:
```
Eligible: [Alice, Dave]
```

The real-world concern this adds: eligibility now depends on *two* independent conditions. Chaining two `.filter(...)` calls applies both as an implicit AND — `Carol` has enough experience (`3` years) but fails the second filter (no references), so she's excluded even though she passed the first.

### Level 3 — Advanced

```java
import java.util.*;
import java.util.function.*;
import java.util.stream.*;

public class FilterComposableRules {
    record Applicant(String name, int yearsExperience, boolean hasReferences, int age) {}

    public static void main(String[] args) {
        List<Applicant> applicants = List.of(
                new Applicant("Alice", 5, true, 29),
                new Applicant("Bob", 1, true, 22),
                new Applicant("Carol", 3, false, 31),
                new Applicant("Dave", 4, true, 17)
        );

        List<Predicate<Applicant>> rules = List.of(
                a -> a.yearsExperience() >= 3,
                Applicant::hasReferences,
                a -> a.age() >= 18
        );

        // Combine a dynamic list of rules into one predicate that requires ALL of them to hold.
        Predicate<Applicant> allRules = rules.stream().reduce(Predicate::and).orElse(a -> true);

        List<String> eligible = applicants.stream()
                .filter(allRules)
                .map(Applicant::name)
                .toList();

        System.out.println("Eligible: " + eligible);
    }
}
```

**How to run:** `java FilterComposableRules.java`

Expected output:
```
Eligible: [Alice]
```

This adds a *dynamic* rule set: instead of hardcoding two chained `.filter()` calls, the eligibility rules live in a `List<Predicate<Applicant>>` and are folded into a single combined predicate with `.reduce(Predicate::and)` — so adding, removing, or loading rules from configuration doesn't require touching the filtering code itself. `Dave` is now excluded by the new age rule (`17 < 18`) alongside `Bob` (experience) and `Carol` (references).

## 6. Walkthrough

Execution starts in `main` of the Level 3 example. `rules` is built as a list of three independent `Predicate<Applicant>` values: minimum experience, having references, and minimum age.

`rules.stream().reduce(Predicate::and)` combines them: starting with the first predicate (`yearsExperience() >= 3`), `Predicate::and` combines it with the second (`hasReferences`) to form a predicate that requires both; that combined predicate is then combined with the third (`age() >= 18`) to form one predicate requiring all three. The result is wrapped in an `Optional<Predicate<Applicant>>` (since `reduce` without an identity value can't guarantee a result if the list were empty); `.orElse(a -> true)` supplies a fallback that accepts everyone if there were no rules at all — not triggered here since `rules` has three entries.

`applicants.stream().filter(allRules)` then evaluates `allRules` against each applicant, in order. For `Alice` (5 years, references, age 29): `5 >= 3` true, `hasReferences` true, `29 >= 18` true — all three hold, so `allRules` returns `true` and `Alice` is kept.

For `Bob` (1 year, references, age 22): `1 >= 3` is `false` — since `Predicate::and` short-circuits, the remaining checks aren't evaluated, `allRules` returns `false`, `Bob` is dropped.

For `Carol` (3 years, no references, age 31): `3 >= 3` true, but `hasReferences` is `false` — `allRules` returns `false`, `Carol` is dropped.

For `Dave` (4 years, references, age 17): `4 >= 3` true, `hasReferences` true, but `17 >= 18` is `false` — `allRules` returns `false`, `Dave` is dropped.

```
Alice: exp>=3 T, refs T, age>=18 T  -> ALL true  -> kept
Bob:   exp>=3 F (short-circuits)    -> false     -> dropped
Carol: exp>=3 T, refs F             -> false     -> dropped
Dave:  exp>=3 T, refs T, age>=18 F  -> false     -> dropped
```

Only `Alice` survives `.filter(allRules)`; `.map(Applicant::name)` extracts `"Alice"`, giving the final `eligible` list `["Alice"]`.

## 7. Gotchas & takeaways

> `filter` is lazy and does nothing on its own — a pipeline that ends with `.filter(...)` and no terminal operation never actually evaluates the predicate against anything. Always follow a filter chain with a terminal operation (`.toList()`, `.forEach()`, `.count()`, etc.) to actually drive the pipeline.

- `filter(predicate)` keeps only elements where the predicate returns `true`; it's an intermediate, lazy operation.
- Chaining multiple `.filter(...)` calls is equivalent to combining their conditions with logical AND.
- `Predicate::and`/`Predicate::or`/`Predicate::negate` let you compose predicates programmatically, which is especially useful when the set of conditions is dynamic (e.g. loaded from configuration) rather than fixed in code.
- `.reduce(Predicate::and)` over a `List<Predicate<T>>` combines a dynamic list of rules into one — remember it returns `Optional<Predicate<T>>`, since an empty list has no predicate to return.
- Order `.filter(...)` calls with the cheapest or most-eliminating condition first when practical — later filters (and any subsequent `.map`) never run on elements already dropped.
