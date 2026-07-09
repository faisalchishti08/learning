---
card: java
gi: 515
slug: partitioningby
title: partitioningBy()
---

## 1. What it is

`Collectors.partitioningBy(predicate)` is a specialized version of `groupingBy` for exactly one, always-present binary split: it collects a stream into `Map<Boolean, List<T>>`, where key `true` holds every element the predicate accepted and key `false` holds every element it rejected. Unlike `groupingBy`, which only creates keys for values actually seen in the data, `partitioningBy` **always** produces both `true` and `false` keys in the result map, even if one of the two groups ends up empty.

## 2. Why & when

When you need to split a stream into exactly two groups by a yes/no condition — valid versus invalid, passed versus failed, in-stock versus out-of-stock — `partitioningBy` is more direct than `groupingBy(predicate)`, and it guarantees both keys exist in the result, so you never need to defensively check `map.containsKey(true)` or handle a missing key with `getOrDefault`. It also accepts a downstream collector, just like `groupingBy`, for computing an aggregate within each of the two partitions instead of a raw list.

## 3. Core concept

```java
import java.util.*;
import java.util.stream.*;

List<Integer> numbers = List.of(1, 2, 3, 4, 5, 6);

Map<Boolean, List<Integer>> evenOdd = numbers.stream()
        .collect(Collectors.partitioningBy(n -> n % 2 == 0));
// {false=[1, 3, 5], true=[2, 4, 6]} -- both keys always present

Map<Boolean, Long> evenOddCounts = numbers.stream()
        .collect(Collectors.partitioningBy(n -> n % 2 == 0, Collectors.counting()));
// {false=3, true=3}
```

The result always has exactly two entries, keyed by `Boolean.TRUE` and `Boolean.FALSE` — never more, never fewer, regardless of the actual data.

## 4. Diagram

<svg viewBox="0 0 640 130" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="partitioningBy splits a stream into exactly two groups keyed by true and false">
  <rect x="8" y="8" width="624" height="114" rx="8" fill="#0d1117"/>
  <rect x="30" y="20" width="40" height="26" fill="#1c2430" stroke="#79c0ff"/><text x="50" y="38" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="monospace">1</text>
  <rect x="75" y="20" width="40" height="26" fill="#1c2430" stroke="#79c0ff"/><text x="95" y="38" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="monospace">2</text>
  <rect x="120" y="20" width="40" height="26" fill="#1c2430" stroke="#79c0ff"/><text x="140" y="38" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="monospace">3</text>
  <rect x="165" y="20" width="40" height="26" fill="#1c2430" stroke="#79c0ff"/><text x="185" y="38" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="monospace">4</text>
  <text x="110" y="70" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">partitioningBy(n % 2 == 0)</text>
  <line x1="110" y1="55" x2="110" y2="85" stroke="#8b949e" stroke-width="1.5" marker-end="url(#arrowPB)"/>
  <rect x="20" y="90" width="90" height="30" rx="4" fill="#1c2430" stroke="#f85149"/><text x="65" y="110" fill="#f85149" font-size="11" text-anchor="middle" font-family="sans-serif">false: [1,3]</text>
  <rect x="120" y="90" width="90" height="30" rx="4" fill="#1c2430" stroke="#6db33f"/><text x="165" y="110" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">true: [2,4]</text>
  <defs><marker id="arrowPB" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Every element lands in exactly one of two buckets — `true` or `false` — and both buckets are always present in the result, even if empty.

## 5. Runnable example

Scenario: sorting a batch of exam scores into pass/fail groups — evolved from a basic partition, through a downstream-collector partition for pass/fail counts, to a version handling the edge case where one partition is entirely empty.

### Level 1 — Basic

```java
import java.util.*;
import java.util.stream.*;

public class PartitioningByBasic {
    public static void main(String[] args) {
        List<Integer> scores = List.of(85, 42, 90, 55, 78, 30);

        Map<Boolean, List<Integer>> passFail = scores.stream()
                .collect(Collectors.partitioningBy(score -> score >= 60));

        System.out.println("Passed: " + passFail.get(true));
        System.out.println("Failed: " + passFail.get(false));
    }
}
```

**How to run:** `java PartitioningByBasic.java`

Expected output:
```
Passed: [85, 90, 78]
Failed: [42, 55, 30]
```

`Collectors.partitioningBy(score -> score >= 60)` splits the six scores into exactly two groups: `passFail.get(true)` holds every score `60` or above, `passFail.get(false)` holds the rest — both keys are guaranteed present, so `.get(true)`/`.get(false)` never return `null` here.

### Level 2 — Intermediate

```java
import java.util.*;
import java.util.stream.*;

public class PartitioningByDownstream {
    public static void main(String[] args) {
        List<Integer> scores = List.of(85, 42, 90, 55, 78, 30);

        Map<Boolean, Long> passFailCounts = scores.stream()
                .collect(Collectors.partitioningBy(score -> score >= 60, Collectors.counting()));

        System.out.println("Passed: " + passFailCounts.get(true));
        System.out.println("Failed: " + passFailCounts.get(false));
        System.out.println("Pass rate: " + (100.0 * passFailCounts.get(true) / scores.size()) + "%");
    }
}
```

**How to run:** `java PartitioningByDownstream.java`

Expected output:
```
Passed: 3
Failed: 3
Pass rate: 50.0%
```

The real-world concern this adds: often just the *counts* per partition matter, not the raw score lists. `Collectors.counting()` as the downstream collector produces `Map<Boolean, Long>` directly, and the pass rate is computed straight from those counts — no need to call `.size()` on retrieved lists separately.

### Level 3 — Advanced

```java
import java.util.*;
import java.util.stream.*;

public class PartitioningByEmptyGroup {
    public static void main(String[] args) {
        List<Integer> perfectScores = List.of(95, 88, 92, 99, 91); // everyone passed

        Map<Boolean, List<Integer>> passFail = perfectScores.stream()
                .collect(Collectors.partitioningBy(score -> score >= 60));

        List<Integer> failed = passFail.get(false); // guaranteed non-null, even though nobody failed
        System.out.println("Failed list is null? " + (failed == null));
        System.out.println("Failed list is empty? " + failed.isEmpty());
        System.out.println("Failed: " + failed);

        if (failed.isEmpty()) {
            System.out.println("Great news: everyone passed!");
        }
    }
}
```

**How to run:** `java PartitioningByEmptyGroup.java`

Expected output:
```
Failed list is null? false
Failed list is empty? true
Failed: []
```

This demonstrates `partitioningBy`'s key guarantee directly: even though *every single score* in `perfectScores` passes (`score >= 60` for all five), `passFail.get(false)` still returns a genuine, non-null, empty `List<Integer>` — never `null`. This is the specific advantage `partitioningBy` has over `groupingBy(predicate)`, which would only include a `false` key at all if at least one element actually failed the predicate, requiring a defensive `getOrDefault(false, List.of())` to safely handle the all-pass case.

## 6. Walkthrough

Execution starts in `main` of the Level 3 example. `perfectScores` holds five values, all `>= 60`: `95, 88, 92, 99, 91`.

`perfectScores.stream().collect(Collectors.partitioningBy(score -> score >= 60))` processes each score. For every one of the five, `score >= 60` evaluates `true`, so each is added to the `true` partition's list, one at a time: `95` added (`true` list becomes `[95]`), `88` added (`[95, 88]`), `92` added (`[95, 88, 92]`), `99` added (`[95, 88, 92, 99]`), `91` added (`[95, 88, 92, 99, 91]`).

Crucially, `partitioningBy`'s internal implementation initializes **both** the `true` and `false` result lists as empty `ArrayList`s *before* processing any elements — it doesn't wait to lazily create the `false` list only if something actually fails. Since no score in this data ever evaluates the predicate as `false`, the `false` list simply never has anything added to it, but it still exists as a genuine empty list, distinct from being absent (`null`) from the map entirely.

```
partitioningBy initializes: {false=[], true=[]}  (both lists exist from the start)

95 -> predicate true  -> true list: [95]
88 -> predicate true  -> true list: [95, 88]
92 -> predicate true  -> true list: [95, 88, 92]
99 -> predicate true  -> true list: [95, 88, 92, 99]
91 -> predicate true  -> true list: [95, 88, 92, 99, 91]

false list: never touched, remains [] -- still present in the map, not null
```

`passFail.get(false)` retrieves the `false` partition's list — since the key genuinely exists in the map (even though its list is empty), `.get(false)` returns `[]`, not `null`. `failed == null` is `false`, printed as `"Failed list is null? false"`. `failed.isEmpty()` is `true`, printed as `"Failed list is empty? true"`. The subsequent `if (failed.isEmpty())` check works safely without any risk of `NullPointerException`, printing `"Great news: everyone passed!"`.

## 7. Gotchas & takeaways

> `partitioningBy`'s guarantee that both keys always exist is precisely what distinguishes it from `groupingBy(predicate)` — with plain `groupingBy`, if every element evaluates the predicate the same way, only *one* key would appear in the resulting map, and calling `.get(theOtherKey)` on it returns `null` rather than an empty list, risking a `NullPointerException` on subsequent use. Prefer `partitioningBy` specifically when you need this "both branches always present" guarantee for a true/false split.

- `Collectors.partitioningBy(predicate)` always produces exactly two map entries, keyed by `true` and `false`, regardless of whether either partition ends up empty.
- This differs from `groupingBy(predicate)`, which only includes keys that were actually produced by at least one element.
- A downstream collector (like `Collectors.counting()`) works the same way with `partitioningBy` as with `groupingBy`, computing an aggregate within each of the two partitions instead of a raw list.
- Because both keys are guaranteed present, code consuming a `partitioningBy` result can safely use `.get(true)`/`.get(false)` directly, without `getOrDefault` or null-checks.
- Reach for `partitioningBy` specifically for a true/false split; for three or more distinct groups, `groupingBy` with a classifier returning more than two possible values is the appropriate tool instead.
