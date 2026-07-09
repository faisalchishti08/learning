---
card: java
gi: 520
slug: collectingandthen
title: collectingAndThen()
---

## 1. What it is

`Collectors.collectingAndThen(downstream, finisher)` wraps another collector and applies an extra transformation to its result once collection is complete. `downstream` does the actual collecting (into a `List`, `Map`, whatever); `finisher` is a `Function` that takes that finished result and turns it into something else — most commonly, wrapping a mutable collection in an unmodifiable view, but it can be any final post-processing step.

## 2. Why & when

Some collectors, like `Collectors.toList()`'s underlying `Collectors.toList()` collector (before the `.toList()` shorthand existed) or `Collectors.toMap(...)`, produce a mutable result by default. If you need that result to be unmodifiable, or need any other transformation applied right at the end of collection (extracting a single field, wrapping in a custom type, validating), `collectingAndThen` lets you express that as part of the collector itself, so it composes cleanly wherever a `Collector` is expected — including as a `groupingBy` downstream, where you can't simply call a method on the finished result afterward without an extra manual step.

## 3. Core concept

```java
import java.util.*;
import java.util.stream.*;

List<String> unmodifiable = Stream.of("a", "b", "c")
        .collect(Collectors.collectingAndThen(
                Collectors.toList(),
                Collections::unmodifiableList));

// As a groupingBy downstream -- each group's list becomes unmodifiable
Map<Boolean, List<Integer>> evenOdd = Stream.of(1, 2, 3, 4)
        .collect(Collectors.groupingBy(
                n -> n % 2 == 0,
                Collectors.collectingAndThen(Collectors.toList(), Collections::unmodifiableList)));
```

`collectingAndThen` collects normally with `downstream`, then runs `finisher` exactly once on the finished result — turning a `List<T>` into an unmodifiable view here, but the finisher can produce any type.

## 4. Diagram

<svg viewBox="0 0 640 120" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="collectingAndThen applies a final transformation after a downstream collector finishes">
  <rect x="8" y="8" width="624" height="104" rx="8" fill="#0d1117"/>
  <rect x="30" y="35" width="140" height="40" rx="6" fill="#1c2430" stroke="#79c0ff"/><text x="100" y="60" fill="#79c0ff" font-size="12" text-anchor="middle" font-family="sans-serif">toList()</text>
  <line x1="170" y1="55" x2="270" y2="55" stroke="#8b949e" stroke-width="2" marker-end="url(#arrowCAT)"/>
  <text x="220" y="45" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">finisher</text>
  <rect x="280" y="35" width="220" height="40" rx="6" fill="#1c2430" stroke="#6db33f"/><text x="390" y="60" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">Collections.unmodifiableList(...)</text>
  <defs><marker id="arrowCAT" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

The downstream collector produces its normal result first; the finisher function then runs once, transforming that result into the final output.

## 5. Runnable example

Scenario: building a read-only registry of validated configuration entries — evolved from a plain unmodifiable-list wrap, through using `collectingAndThen` as a `groupingBy` downstream, to a version that validates the collected result and fails fast if it's invalid.

### Level 1 — Basic

```java
import java.util.*;
import java.util.stream.*;

public class CollectingAndThenBasic {
    public static void main(String[] args) {
        List<String> configKeys = Stream.of("timeout", "retries", "host")
                .collect(Collectors.collectingAndThen(
                        Collectors.toList(),
                        Collections::unmodifiableList));

        System.out.println("Config keys: " + configKeys);

        try {
            configKeys.add("port");
        } catch (UnsupportedOperationException e) {
            System.out.println("Cannot modify: registry is read-only");
        }
    }
}
```

**How to run:** `java CollectingAndThenBasic.java`

Expected output:
```
Config keys: [timeout, retries, host]
Cannot modify: registry is read-only
```

`Collectors.toList()` first collects the three keys into a normal, mutable `ArrayList`. `Collections::unmodifiableList` then wraps that list in an unmodifiable view — attempting `.add(...)` on the result throws `UnsupportedOperationException`, confirming the registry can't be accidentally mutated after construction.

### Level 2 — Intermediate

```java
import java.util.*;
import java.util.stream.*;

public class CollectingAndThenGrouped {
    record ConfigEntry(String environment, String key) {}

    public static void main(String[] args) {
        List<ConfigEntry> entries = List.of(
                new ConfigEntry("prod", "timeout"),
                new ConfigEntry("prod", "retries"),
                new ConfigEntry("dev", "debug")
        );

        // Each environment's key list is made unmodifiable as part of the same groupingBy pass.
        Map<String, List<String>> keysByEnv = entries.stream()
                .collect(Collectors.groupingBy(
                        ConfigEntry::environment,
                        Collectors.collectingAndThen(
                                Collectors.mapping(ConfigEntry::key, Collectors.toList()),
                                Collections::unmodifiableList)));

        List<String> prodKeys = keysByEnv.get("prod");
        System.out.println("Prod keys: " + prodKeys);
        try {
            prodKeys.add("hacked");
        } catch (UnsupportedOperationException e) {
            System.out.println("Prod config is protected from modification");
        }
    }
}
```

**How to run:** `java CollectingAndThenGrouped.java`

Expected output:
```
Prod keys: [timeout, retries]
Prod config is protected from modification
```

The real-world concern this adds: using `collectingAndThen` as a `groupingBy` downstream, combined with `mapping` (see [[mapping]] and [[groupingby-with-downstream]]) — each environment's group of keys is both extracted (via `mapping`) and made unmodifiable (via `collectingAndThen`), all within the single grouping pass, so every group in the resulting map is independently protected from mutation.

### Level 3 — Advanced

```java
import java.util.*;
import java.util.stream.*;

public class CollectingAndThenValidated {
    record ConfigEntry(String key, String value) {}

    static List<ConfigEntry> requireNonEmpty(List<ConfigEntry> entries) {
        if (entries.isEmpty()) {
            throw new IllegalStateException("Configuration must have at least one entry");
        }
        return List.copyOf(entries); // defensively unmodifiable, distinct from the mutable working list
    }

    public static void main(String[] args) {
        List<ConfigEntry> rawEntries = List.of(
                new ConfigEntry("timeout", "30"),
                new ConfigEntry("retries", "3")
        );

        List<ConfigEntry> validatedConfig = rawEntries.stream()
                .filter(e -> !e.value().isBlank())
                .collect(Collectors.collectingAndThen(Collectors.toList(), CollectingAndThenValidated::requireNonEmpty));

        System.out.println("Validated config has " + validatedConfig.size() + " entries");

        // Now demonstrate the failure path with an empty source.
        try {
            List.<ConfigEntry>of().stream()
                    .filter(e -> !e.value().isBlank())
                    .collect(Collectors.collectingAndThen(Collectors.toList(), CollectingAndThenValidated::requireNonEmpty));
        } catch (IllegalStateException e) {
            System.out.println("Validation failed as expected: " + e.getMessage());
        }
    }
}
```

**How to run:** `java CollectingAndThenValidated.java`

Expected output:
```
Validated config has 2 entries
Validation failed as expected: Configuration must have at least one entry
```

This uses `collectingAndThen`'s finisher for genuine **validation**, not just wrapping: `requireNonEmpty` checks that the collected list isn't empty, throwing `IllegalStateException` if it is, and otherwise returns a defensively-copied unmodifiable list via `List.copyOf(...)`. This fails fast at the point of collection if the final configuration would be invalid, rather than letting an empty, silently-broken configuration propagate further into the program.

## 6. Walkthrough

Execution starts in `main` of the Level 3 example. `rawEntries` holds two valid config entries.

For the first collection, `rawEntries.stream().filter(e -> !e.value().isBlank())` keeps both entries (`"30"` and `"3"` are non-blank). `.collect(Collectors.collectingAndThen(Collectors.toList(), CollectingAndThenValidated::requireNonEmpty))` first runs the inner `Collectors.toList()`, producing a mutable `List<ConfigEntry>` with both entries. Then the finisher, `requireNonEmpty`, is called with that list: `entries.isEmpty()` is `false` (it has two entries), so no exception is thrown, and `List.copyOf(entries)` returns a defensively-copied, unmodifiable list with the same two entries. `validatedConfig.size()` is `2`, printed as `"Validated config has 2 entries"`.

For the second scenario, `List.<ConfigEntry>of()` starts with zero entries. `.filter(...)` has nothing to filter — the stream stays empty. `.collect(...)` runs `Collectors.toList()`, producing an empty `List<ConfigEntry>`. The finisher, `requireNonEmpty`, is called with this empty list: `entries.isEmpty()` is `true`, so `IllegalStateException("Configuration must have at least one entry")` is thrown immediately, before `List.copyOf(...)` is ever reached.

```
Path 1: rawEntries (2 valid) -> filter keeps both -> toList() -> [entry1, entry2]
        -> requireNonEmpty: isEmpty() false -> List.copyOf(...) -> validated, 2 entries

Path 2: empty source -> filter keeps nothing -> toList() -> []
        -> requireNonEmpty: isEmpty() true -> THROWS IllegalStateException
```

The `try`/`catch` block around the second collection catches this exception, and `e.getMessage()` retrieves the exact message set inside `requireNonEmpty`, printed as `"Validation failed as expected: Configuration must have at least one entry"` — demonstrating that `collectingAndThen`'s finisher runs as an integral part of the collection process, capable of rejecting an invalid result outright rather than merely transforming a valid one.

## 7. Gotchas & takeaways

> The `finisher` function in `collectingAndThen` runs exactly **once**, after the downstream collector has fully finished accumulating — it operates on the complete result, not incrementally on each element as it's added. This makes it well-suited for final validation or wrapping, but not for per-element processing (that's what the downstream collector itself, or a preceding `filter`/`map` in the pipeline, is for).

- `Collectors.collectingAndThen(downstream, finisher)` applies a final transformation to a collector's result after collection completes.
- The most common use is wrapping a mutable collection (`Collectors.toList()`'s result) in an unmodifiable view via `Collections::unmodifiableList` or similar.
- It composes cleanly as a `groupingBy` downstream, letting each group's collected result be transformed or validated independently within the same single pass.
- The finisher can do more than wrap — it can validate the collected result and throw if it's invalid, catching problems at the point of collection rather than letting bad data propagate.
- Since Java 16's `.toList()` already returns an unmodifiable list directly, `collectingAndThen(Collectors.toList(), Collections::unmodifiableList)` is now largely redundant for that specific case — but the pattern remains valuable for validation, custom wrapping, or any other post-collection transformation `.toList()` alone doesn't provide.
