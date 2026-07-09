---
card: java
gi: 489
slug: stream-concat
title: Stream.concat()
---

## 1. What it is

`Stream.concat(streamA, streamB)` returns a new stream whose elements are all of `streamA`'s elements followed by all of `streamB`'s elements — it joins two streams end to end into one, lazily, without merging or sorting anything. It's a `static` method, so it's called as `Stream.concat(a, b)`, not `a.concat(b)`.

## 2. Why & when

Sometimes the data you want to process comes from two separate sources that need to be treated as one sequence: two different collections, a "required" set and an "optional" set, results from two independent queries. `Stream.concat` lets you combine them into a single pipeline without first collecting both into a shared `List` — you get one continuous stream, in order, first source then second.

You reach for it when you have exactly two streams to join. For combining more than two, `Stream.concat` can be nested (`Stream.concat(a, Stream.concat(b, c))`), but that gets unwieldy quickly — for three or more, `Stream.of(a, b, c).flatMap(s -> s)` is usually the cleaner approach.

## 3. Core concept

```java
import java.util.stream.*;

Stream<String> first = Stream.of("a", "b");
Stream<String> second = Stream.of("c", "d");

List<String> combined = Stream.concat(first, second).toList(); // ["a", "b", "c", "d"]
```

The result preserves order: everything from the first stream comes before everything from the second — `concat` does not interleave, deduplicate, or sort.

## 4. Diagram

<svg viewBox="0 0 640 130" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Stream.concat joins two streams end to end, first stream's elements followed by second's">
  <rect x="8" y="8" width="624" height="114" rx="8" fill="#0d1117"/>
  <rect x="30" y="20" width="60" height="30" fill="#1c2430" stroke="#79c0ff"/><text x="60" y="40" fill="#79c0ff" font-size="12" text-anchor="middle" font-family="monospace">a</text>
  <rect x="95" y="20" width="60" height="30" fill="#1c2430" stroke="#79c0ff"/><text x="125" y="40" fill="#79c0ff" font-size="12" text-anchor="middle" font-family="monospace">b</text>
  <text x="20" y="15" fill="#8b949e" font-size="10" font-family="sans-serif">streamA</text>
  <rect x="30" y="70" width="60" height="30" fill="#1c2430" stroke="#6db33f"/><text x="60" y="90" fill="#6db33f" font-size="12" text-anchor="middle" font-family="monospace">c</text>
  <rect x="95" y="70" width="60" height="30" fill="#1c2430" stroke="#6db33f"/><text x="125" y="90" fill="#6db33f" font-size="12" text-anchor="middle" font-family="monospace">d</text>
  <text x="20" y="65" fill="#8b949e" font-size="10" font-family="sans-serif">streamB</text>
  <text x="180" y="55" fill="#8b949e" font-size="14" font-family="sans-serif">-&gt;</text>
  <rect x="230" y="40" width="60" height="30" fill="#1c2430" stroke="#79c0ff"/><text x="260" y="60" fill="#79c0ff" font-size="12" text-anchor="middle" font-family="monospace">a</text>
  <rect x="295" y="40" width="60" height="30" fill="#1c2430" stroke="#79c0ff"/><text x="325" y="60" fill="#79c0ff" font-size="12" text-anchor="middle" font-family="monospace">b</text>
  <rect x="360" y="40" width="60" height="30" fill="#1c2430" stroke="#6db33f"/><text x="390" y="60" fill="#6db33f" font-size="12" text-anchor="middle" font-family="monospace">c</text>
  <rect x="425" y="40" width="60" height="30" fill="#1c2430" stroke="#6db33f"/><text x="455" y="60" fill="#6db33f" font-size="12" text-anchor="middle" font-family="monospace">d</text>
  <text x="20" y="112" fill="#8b949e" font-size="10" font-family="sans-serif">Order preserved: all of A, then all of B -- no interleaving or sorting.</text>
</svg>

`Stream.concat` places every element of the first stream before every element of the second, preserving each source's internal order.

## 5. Runnable example

Scenario: merging a "required" and an "optional" feature-flag list for a service startup check — evolved from a plain two-source concat, through joining results from two different data origins with a shared shape, to a version that concatenates a variable, dynamic list of sources safely.

### Level 1 — Basic

```java
import java.util.stream.*;

public class ConcatBasic {
    public static void main(String[] args) {
        Stream<String> required = Stream.of("db", "cache");
        Stream<String> optional = Stream.of("metrics", "tracing");

        Stream.concat(required, optional)
                .forEach(flag -> System.out.println("Checking flag: " + flag));
    }
}
```

**How to run:** `java ConcatBasic.java`

Expected output:
```
Checking flag: db
Checking flag: cache
Checking flag: metrics
Checking flag: tracing
```

`Stream.concat(required, optional)` produces one stream that visits all of `required`'s elements first (`"db"`, `"cache"`), then all of `optional`'s (`"metrics"`, `"tracing"`) — in that exact order, with no reordering.

### Level 2 — Intermediate

```java
import java.util.*;
import java.util.stream.*;

public class ConcatTwoSources {
    record Flag(String name, boolean required) {}

    public static void main(String[] args) {
        List<String> requiredNames = List.of("db", "cache");
        List<String> optionalNames = List.of("metrics", "tracing");

        Stream<Flag> requiredFlags = requiredNames.stream().map(name -> new Flag(name, true));
        Stream<Flag> optionalFlags = optionalNames.stream().map(name -> new Flag(name, false));

        List<Flag> allFlags = Stream.concat(requiredFlags, optionalFlags).toList();
        allFlags.forEach(flag -> System.out.println(flag.name() + " (required=" + flag.required() + ")"));
    }
}
```

**How to run:** `java ConcatTwoSources.java`

Expected output:
```
db (required=true)
cache (required=true)
metrics (required=false)
tracing (required=false)
```

The real-world concern this adds: the two sources aren't raw strings anymore but each get mapped into a shared `Flag` record carrying context about *which* source they came from (`required` flag), before being concatenated — a common pattern when combining two differently-sourced lists into one uniformly-typed stream for further processing.

### Level 3 — Advanced

```java
import java.util.*;
import java.util.stream.*;

public class ConcatManySources {
    record Flag(String name, boolean required) {}

    static Stream<Flag> toFlagStream(List<String> names, boolean required) {
        return names.stream().map(name -> new Flag(name, required));
    }

    public static void main(String[] args) {
        List<List<String>> sources = List.of(
                List.of("db", "cache"),
                List.of("metrics", "tracing"),
                List.of(), // an empty source -- must not break the chain
                List.of("beta-ui")
        );

        // Fold a variable number of sources together using concat via reduce, since concat
        // itself only ever joins exactly two streams at a time.
        Stream<Flag> combined = sources.stream()
                .map(names -> toFlagStream(names, names == sources.get(0)))
                .reduce(Stream.empty(), Stream::concat);

        long total = combined.peek(flag -> System.out.println("Loaded: " + flag.name())).count();
        System.out.println("Total flags: " + total);
    }
}
```

**How to run:** `java ConcatManySources.java`

Expected output:
```
Loaded: db
Loaded: cache
Loaded: metrics
Loaded: tracing
Loaded: beta-ui
Total flags: 5
```

This handles a *variable* number of sources (including an empty one) by folding them together with `.reduce(Stream.empty(), Stream::concat)` — starting from `Stream.empty()` (see [[stream-empty]]) as the identity value and repeatedly concatenating each source's stream onto the accumulated result. The empty third source contributes nothing, exactly as `Stream.empty()` is designed to, without any special-casing needed in the reduction.

## 6. Walkthrough

Execution starts in `main` of the Level 3 example. `sources` holds four lists: two-element, two-element, an *empty* list, and a one-element list.

`sources.stream().map(names -> toFlagStream(names, names == sources.get(0)))` converts each `List<String>` into a `Stream<Flag>` via `toFlagStream`. (The `required` flag logic here is simplified for the example — only the first source is marked required.)

`.reduce(Stream.empty(), Stream::concat)` then folds these four `Stream<Flag>` values into one. The reduction starts with the identity value `Stream.empty()` — a valid, zero-element stream. It combines that with the first source's stream via `Stream.concat(Stream.empty(), flagStream1)`, producing a stream equivalent to `flagStream1` alone (concatenating anything after an empty stream just yields that anything). That result is then concatenated with the second source's stream, then the third (the empty list, which itself produces an empty `Stream<Flag>` — contributing nothing, so the accumulated stream is unchanged), then the fourth.

```
acc = Stream.empty()
acc = concat(acc, flags[db,cache])       -> effectively [db, cache]
acc = concat(acc, flags[metrics,tracing])-> [db, cache, metrics, tracing]
acc = concat(acc, flags[])               -> [db, cache, metrics, tracing]   (unchanged -- empty source)
acc = concat(acc, flags[beta-ui])        -> [db, cache, metrics, tracing, beta-ui]
```

The final `combined` stream, when consumed by `.peek(...).count()`, visits all five `Flag` elements in that exact order, printing `"Loaded: ..."` for each one via `.peek` (a side-effecting operation used here purely to observe the elements) before `.count()` reports the total, `5`.

## 7. Gotchas & takeaways

> `Stream.concat` only ever joins **two** streams. For combining more than two, either nest calls (`Stream.concat(a, Stream.concat(b, c))`) or, more cleanly for a dynamic number of sources, fold with `.reduce(Stream.empty(), Stream::concat)` as shown in Level 3, or use `Stream.of(a, b, c).flatMap(s -> s)`.

- `Stream.concat(a, b)` joins two streams end to end: every element of `a`, in order, followed by every element of `b`, in order — no merging, sorting, or deduplication.
- Both input streams are consumed as `concat`'s result is consumed — neither is materialized into a collection first.
- For a fixed, small number of sources, nested `concat` calls work; for a dynamic list of sources, folding with `Stream.empty()` as the identity via `.reduce(...)` scales cleanly, including correctly handling empty sources.
- Since each source stream is single-use, don't try to reuse `first`/`second` after passing them to `Stream.concat` — they're consumed once `concat`'s result is consumed.
- For deeply nested concatenations, consider `Stream.of(s1, s2, s3, ...).flatMap(s -> s)` instead, which reads more clearly for three or more sources than repeated pairwise `concat` calls.
