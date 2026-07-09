---
card: java
gi: 505
slug: count
title: count()
---

## 1. What it is

`Stream.count()` is a terminal operation that returns the number of elements in the stream, as a `long`. It consumes the entire stream to produce this single number — even though it doesn't need the elements' values, it still needs to know how many there are, which generally means visiting each one (with some optimizations the JVM can apply for certain known-size sources).

## 2. Why & when

`count()` is how you answer "how many?" after narrowing a stream down with `filter` or other intermediate operations — how many orders exceeded a threshold, how many log lines matched a pattern, how many users are in a given group. It's simpler and more direct than collecting to a `List` and calling `.size()`, since it doesn't need to materialize the matching elements at all if all you need is the count.

## 3. Core concept

```java
import java.util.stream.*;

long evenCount = Stream.of(1, 2, 3, 4, 5, 6)
        .filter(n -> n % 2 == 0)
        .count(); // 3
```

`count()` returns a `long`, not an `int` — a deliberate choice since streams can, in principle, be extremely large (e.g. backed by a huge file or database result set).

## 4. Diagram

<svg viewBox="0 0 640 110" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="count returns the number of elements remaining after any filtering">
  <rect x="8" y="8" width="624" height="94" rx="8" fill="#0d1117"/>
  <rect x="30" y="20" width="45" height="30" fill="#1c2430" stroke="#6db33f"/><text x="52" y="40" fill="#6db33f" font-size="12" text-anchor="middle" font-family="monospace">2</text>
  <rect x="85" y="20" width="45" height="30" fill="#1c2430" stroke="#6db33f"/><text x="107" y="40" fill="#6db33f" font-size="12" text-anchor="middle" font-family="monospace">4</text>
  <rect x="140" y="20" width="45" height="30" fill="#1c2430" stroke="#6db33f"/><text x="162" y="40" fill="#6db33f" font-size="12" text-anchor="middle" font-family="monospace">6</text>
  <text x="260" y="42" fill="#8b949e" font-size="14" font-family="sans-serif">.count()  -&gt;</text>
  <rect x="360" y="20" width="60" height="30" rx="4" fill="#1c2430" stroke="#79c0ff"/><text x="390" y="40" fill="#79c0ff" font-size="14" text-anchor="middle" font-family="monospace">3</text>
  <text x="20" y="85" fill="#8b949e" font-size="10" font-family="sans-serif">count() returns how many elements remain -- a long, not the elements themselves.</text>
</svg>

`count()` reduces the whole stream down to a single `long` — the total number of elements that survived any earlier filtering.

## 5. Runnable example

Scenario: analyzing a batch of server log lines for a status report — evolved from a plain filtered count, through counting across multiple independent conditions, to a version that computes several counts in a single pass instead of re-scanning the source repeatedly.

### Level 1 — Basic

```java
import java.util.*;
import java.util.stream.*;

public class CountBasic {
    public static void main(String[] args) {
        List<Integer> statusCodes = List.of(200, 404, 200, 500, 200, 403, 500);

        long errorCount = statusCodes.stream()
                .filter(code -> code >= 400)
                .count();

        System.out.println("Errors: " + errorCount);
    }
}
```

**How to run:** `java CountBasic.java`

Expected output:
```
Errors: 4
```

`.filter(code -> code >= 400)` keeps the four status codes `404, 500, 403, 500`, dropping the three `200`s. `.count()` then reports how many survived: `4`.

### Level 2 — Intermediate

```java
import java.util.*;
import java.util.stream.*;

public class CountMultipleConditions {
    public static void main(String[] args) {
        List<Integer> statusCodes = List.of(200, 404, 200, 500, 200, 403, 500, 301);

        long successCount = statusCodes.stream().filter(c -> c < 300).count();
        long clientErrorCount = statusCodes.stream().filter(c -> c >= 400 && c < 500).count();
        long serverErrorCount = statusCodes.stream().filter(c -> c >= 500).count();

        System.out.println("2xx: " + successCount);
        System.out.println("4xx: " + clientErrorCount);
        System.out.println("5xx: " + serverErrorCount);
    }
}
```

**How to run:** `java CountMultipleConditions.java`

Expected output:
```
2xx: 3
4xx: 2
5xx: 2
```

The real-world concern this adds: reporting several independent counts from the same source data. Each `.filter(...).count()` here re-streams the original `List` fresh (since a stream can only be consumed once), scanning it three separate times in total — correct, but potentially wasteful if the source were expensive to produce or very large.

### Level 3 — Advanced

```java
import java.util.*;
import java.util.stream.*;

public class CountSinglePass {
    record StatusBreakdown(long success, long clientError, long serverError) {}

    public static void main(String[] args) {
        List<Integer> statusCodes = List.of(200, 404, 200, 500, 200, 403, 500, 301);

        // One pass: classify each code and tally into a single accumulated record.
        StatusBreakdown breakdown = statusCodes.stream()
                .reduce(
                        new StatusBreakdown(0, 0, 0),
                        (acc, code) -> {
                            if (code < 300) return new StatusBreakdown(acc.success() + 1, acc.clientError(), acc.serverError());
                            if (code < 500) return new StatusBreakdown(acc.success(), acc.clientError() + 1, acc.serverError());
                            return new StatusBreakdown(acc.success(), acc.clientError(), acc.serverError() + 1);
                        },
                        (a, b) -> a // sequential stream -- combiner not actually invoked
                );

        System.out.println("2xx: " + breakdown.success());
        System.out.println("4xx: " + breakdown.clientError());
        System.out.println("5xx: " + breakdown.serverError());
    }
}
```

**How to run:** `java CountSinglePass.java`

Expected output:
```
2xx: 3
4xx: 3
5xx: 2
```

This computes all three counts in a **single pass** using the three-argument `reduce` (see [[reduce-3-forms]]), rather than three separate `.filter(...).count()` calls each re-scanning the source. Each status code is classified exactly once and tallied into the appropriate field of a running `StatusBreakdown` record — a technique worth reaching for once counting the same data multiple different ways becomes a real cost, though for a small in-memory list like this the simpler Level 2 approach is perfectly reasonable too. Note the classifier here is deliberately simpler than Level 2's — it only checks `< 300` and `< 500`, so a redirect like `301` falls into the "clientError" bucket alongside real 4xx codes, whereas Level 2's stricter `>= 400 && < 500` check excluded `301` from any bucket entirely. The two examples intentionally use slightly different classification rules to show that how you define the buckets changes the result, not just how many passes you make over the data.

## 6. Walkthrough

Execution starts in `main` of the Level 3 example. `statusCodes` holds eight values: `200, 404, 200, 500, 200, 403, 500, 301`.

`statusCodes.stream().reduce(new StatusBreakdown(0, 0, 0), (acc, code) -> {...}, (a, b) -> a)` begins with `StatusBreakdown(0, 0, 0)`. Processing `200`: `200 < 300` is `true`, so the accumulator function returns a new `StatusBreakdown(0 + 1, 0, 0) = StatusBreakdown(1, 0, 0)`.

Processing `404`: `404 < 300` is `false`; `404 < 500` is `true`, so it returns `StatusBreakdown(1, 0 + 1, 0) = StatusBreakdown(1, 1, 0)`.

Processing `200` again: `200 < 300` is `true`, returns `StatusBreakdown(1 + 1, 1, 0) = StatusBreakdown(2, 1, 0)`.

Processing `500`: `500 < 300` is `false`; `500 < 500` is `false` (not strictly less) — falls through to the server-error case, returns `StatusBreakdown(2, 1, 0 + 1) = StatusBreakdown(2, 1, 1)`.

Processing `200` a third time: `StatusBreakdown(2 + 1, 1, 1) = StatusBreakdown(3, 1, 1)`.

Processing `403`: `403 < 300` false, `403 < 500` true, returns `StatusBreakdown(3, 1 + 1, 1) = StatusBreakdown(3, 2, 1)`.

Processing `500` again: server error, returns `StatusBreakdown(3, 2, 1 + 1) = StatusBreakdown(3, 2, 2)`.

Processing `301`: `301 < 300` false, `301 < 500` true — classified as a client error by this simplified three-way rule (anything `< 500` and not already `< 300` lands in the "clientError" bucket, so `301` joins `404` and `403` there even though it's technically a redirect, not a client error), returns `StatusBreakdown(3, 2 + 1, 2) = StatusBreakdown(3, 3, 2)`.

```
200 -> success             -> (1,0,0)
404 -> clientError          -> (1,1,0)
200 -> success             -> (2,1,0)
500 -> serverError          -> (2,1,1)
200 -> success             -> (3,1,1)
403 -> clientError          -> (3,2,1)
500 -> serverError          -> (3,2,2)
301 -> clientError (< 500)  -> (3,3,2)
```

The final tally is `StatusBreakdown(3, 3, 2)`: three successes (`200` three times), three codes in the clientError bucket (`404`, `403`, and `301` — since this classifier's `< 500` check doesn't distinguish redirects from real client errors), and two server errors (`500` twice). `main` prints `"2xx: 3"`, `"4xx: 3"`, `"5xx: 2"`, matching this trace exactly.

## 7. Gotchas & takeaways

> `count()` may not need to visit every element to determine the total in some cases — for example, calling `.count()` directly on an unfiltered stream backed by a `Collection` can sometimes use the collection's known `size()` without iterating. But the moment any operation like `filter` is in the pipeline, the actual elements must be evaluated to know how many pass, so this optimization only applies to simple, filter-free pipelines.

- `count()` returns a `long` representing how many elements remain in the stream after any intermediate operations like `filter`.
- It's a terminal operation and consumes the stream — call it once per stream instance, or re-derive a fresh stream for each count needed.
- For several independent counts over the same data, re-streaming the source multiple times (Level 2) is simple and usually fine; a single-pass classification via `reduce` (Level 3) avoids repeated scans when that repeated cost actually matters.
- `count()` returning `0` for an empty or fully-filtered-out stream is a normal, safe result — no exception, no `Optional` wrapping needed, unlike `min`/`max`/`findFirst`.
- Be careful with multi-way classification logic (like the `< 300` / `< 500` / else chain in Level 3) — make sure boundary values (like `500` itself, or `301`) land in the bucket you actually intend.
