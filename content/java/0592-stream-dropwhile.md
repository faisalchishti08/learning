---
card: java
gi: 592
slug: stream-dropwhile
title: Stream.dropWhile
---

## 1. What it is

`Stream.dropWhile` is a Java 9 intermediate stream operation that discards leading elements from a stream as long as a given predicate evaluates to `true`. The moment the predicate returns `false` for an element, that element and every subsequent element are retained in the output stream — the predicate is never evaluated again after the first `false`. It is the logical complement of `Stream.takeWhile`: where `takeWhile` keeps elements while the predicate holds, `dropWhile` discards them while the predicate holds.

## 2. Why & when

Ordered streams (lists, arrays, sorted data) frequently contain a prefix of elements you want to skip based on a condition — all log entries before a certain timestamp, all numbers below a threshold in a sorted list, all leading whitespace tokens in a parsed input. Before Java 9, skipping a prefix based on a condition required either a manual loop with a boolean flag (messy, stateful) or a combination of `Stream.skip` and index arithmetic (fragile, only works when you know the exact count). `dropWhile` expresses the intent directly: "discard the leading elements that satisfy this condition, then keep everything else," in a single declarative call that composes cleanly with the rest of the stream pipeline.

## 3. Core concept

```java
List<Integer> numbers = List.of(1, 3, 5, 2, 4, 6);
List<Integer> result = numbers.stream()
    .dropWhile(n -> n % 2 != 0)  // drop leading odd numbers
    .toList();
// result = [2, 4, 6]
```

The predicate `n -> n % 2 != 0` is `true` for 1, 3, and 5 — all three are dropped. The first element where the predicate returns `false` is 2 (even). From 2 onward, everything is kept regardless of whether the predicate would return `true` or `false` for later elements. The key behavioural rule: `dropWhile` is **short-circuiting on the predicate becoming false** — it evaluates the predicate sequentially and stops evaluating entirely once it fails once.

## 4. Diagram

<svg viewBox="0 0 640 180" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="dropWhile drops leading elements while the predicate is true, then passes through everything else">
  <rect x="20" y="10" width="600" height="160" rx="8" fill="#1c2430" stroke="#6db33f"/>

  <text x="30" y="35" fill="#e6edf3" font-size="11" font-family="sans-serif">Input stream: [1, 3, 5, 2, 4, 6]</text>

  <rect x="30" y="48" width="80" height="30" rx="4" fill="#f85149" stroke="#f85149"/>
  <text x="70" y="68" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="monospace">1 ✕</text>
  <rect x="120" y="48" width="80" height="30" rx="4" fill="#f85149" stroke="#f85149"/>
  <text x="160" y="68" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="monospace">3 ✕</text>
  <rect x="210" y="48" width="80" height="30" rx="4" fill="#f85149" stroke="#f85149"/>
  <text x="250" y="68" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="monospace">5 ✕</text>
  <rect x="300" y="48" width="80" height="30" rx="4" fill="#6db33f" stroke="#6db33f"/>
  <text x="340" y="68" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="monospace">2 ✓</text>
  <rect x="390" y="48" width="80" height="30" rx="4" fill="#6db33f" stroke="#6db33f"/>
  <text x="430" y="68" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="monospace">4 ✓</text>
  <rect x="480" y="48" width="80" height="30" rx="4" fill="#6db33f" stroke="#6db33f"/>
  <text x="520" y="68" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="monospace">6 ✓</text>

  <text x="30" y="105" fill="#8b949e" font-size="10" font-family="sans-serif">predicate: n % 2 != 0</text>
  <text x="30" y="120" fill="#8b949e" font-size="10" font-family="sans-serif">Drops while true → first false at element 2 → keeps 2, 4, 6</text>

  <text x="30" y="152" fill="#e6edf3" font-size="11" font-family="sans-serif">Output stream: [2, 4, 6]</text>
</svg>

Leading odd numbers are dropped; the first even number and everything after it passes through, regardless of parity.

## 5. Runnable example

Scenario: a log-processing pipeline that filters a time-ordered list of log entries — starting with three complexity levels: basic prefix-dropping on a sorted numeric stream, extending to real-world log filtering where logs before a given timestamp are discarded, and finally handling edge cases with an empty stream, a stream where no element satisfies the predicate, and a stream where all elements satisfy it.

### Level 1 — Basic

```java
// File: DropWhileDemo.java
import java.util.List;
import java.util.stream.Collectors;

public class DropWhileDemo {
    public static void main(String[] args) {
        List<Integer> numbers = List.of(1, 3, 5, 2, 4, 6);
        List<Integer> result = numbers.stream()
            .dropWhile(n -> n % 2 != 0)
            .collect(Collectors.toList());

        System.out.println("Input:  " + numbers);
        System.out.println("Output: " + result);
    }
}
```

**How to run:** `java DropWhileDemo.java`

Expected output:
```
Input:  [1, 3, 5, 2, 4, 6]
Output: [2, 4, 6]
```

The simplest possible use: a sorted list where leading odd numbers are the "prefix to drop." `dropWhile(n -> n % 2 != 0)` discards 1, 3, and 5; once it hits 2 (even), it stops dropping and lets 2, 4, and 6 through untouched.

### Level 2 — Intermediate

```java
// File: LogDropWhile.java
import java.time.LocalTime;
import java.util.List;
import java.util.stream.Collectors;

public class LogDropWhile {
    record LogEntry(LocalTime time, String message) {}

    public static void main(String[] args) {
        List<LogEntry> logs = List.of(
            new LogEntry(LocalTime.of(8, 15), "Server starting"),
            new LogEntry(LocalTime.of(8, 16), "Loading config"),
            new LogEntry(LocalTime.of(8, 30), "Ready"),
            new LogEntry(LocalTime.of(8, 31), "Request received"),
            new LogEntry(LocalTime.of(8, 32), "Processed"),
            new LogEntry(LocalTime.of(8, 33), "Response sent")
        );

        LocalTime cutOff = LocalTime.of(8, 30);
        List<LogEntry> afterCutoff = logs.stream()
            .dropWhile(entry -> entry.time().isBefore(cutOff))
            .collect(Collectors.toList());

        System.out.println("Logs from 08:30 onwards:");
        afterCutoff.forEach(e -> System.out.println("  " + e.time() + " — " + e.message()));
    }
}
```

**How to run:** `java LogDropWhile.java`

Expected output:
```
Logs from 08:30 onwards:
  08:30 — Ready
  08:31 — Request received
  08:32 — Processed
  08:33 — Response sent
```

The real-world concern added: log entries are real objects with a timestamp field, not just integers. The predicate `entry.time().isBefore(cutOff)` evaluates each entry's timestamp against a cutoff (`08:30`). Everything before `08:30` is dropped; `08:30` itself is the first element where the predicate returns `false`, so it and everything after it are kept. This pattern — "drop all events before a given point in an ordered stream" — is the most common production use of `dropWhile`.

### Level 3 — Advanced

```java
// File: DropWhileEdgeCases.java
import java.util.List;
import java.util.stream.Collectors;
import java.util.stream.Stream;

public class DropWhileEdgeCases {
    public static void main(String[] args) {
        System.out.println("=== Case 1: no element satisfies predicate (first element passes)");
        List<Integer> case1 = Stream.of(2, 4, 6, 8)
            .dropWhile(n -> n % 2 != 0)  // 2 is even → predicate false immediately
            .collect(Collectors.toList());
        System.out.println("Input:  [2, 4, 6, 8]");
        System.out.println("Output: " + case1);

        System.out.println("\n=== Case 2: all elements satisfy predicate (nothing left)");
        List<Integer> case2 = Stream.of(1, 3, 5, 7)
            .dropWhile(n -> n % 2 != 0)  // all are odd → predicate never fails
            .collect(Collectors.toList());
        System.out.println("Input:  [1, 3, 5, 7]");
        System.out.println("Output: " + case2);

        System.out.println("\n=== Case 3: empty stream");
        List<Integer> case3 = Stream.<Integer>empty()
            .dropWhile(n -> n % 2 != 0)
            .collect(Collectors.toList());
        System.out.println("Input:  []");
        System.out.println("Output: " + case3);

        System.out.println("\n=== Case 4: unordered stream (parallel)");
        List<Integer> unordered = List.of(3, 1, 4, 1, 5, 9, 2, 6);
        List<Integer> case4 = unordered.parallelStream()
            .dropWhile(n -> n < 5)
            .collect(Collectors.toList());
        System.out.println("Input:  " + unordered);
        System.out.println("Output: " + case4 + " (may vary — unordered result)");
    }
}
```

**How to run:** `java DropWhileEdgeCases.java`

Expected output (Case 4 output may vary for unordered/parallel):

```
=== Case 1: no element satisfies predicate (first element passes)
Input:  [2, 4, 6, 8]
Output: [2, 4, 6, 8]

=== Case 2: all elements satisfy predicate (nothing left)
Input:  [1, 3, 5, 7]
Output: []

=== Case 3: empty stream
Input:  []
Output: []

=== Case 4: unordered stream (parallel)
Input:  [3, 1, 4, 1, 5, 9, 2, 6]
Output: [9, 2, 6] (may vary — unordered result)
```

This handles production-flavoured edge cases: (1) when the very first element already fails the predicate, nothing is dropped; (2) when every element satisfies the predicate, the entire stream is dropped, yielding an empty stream; (3) an empty stream input yields an empty stream output — no exception, no special handling needed; (4) when the stream is unordered (e.g. from `parallelStream()` or a `Set`), `dropWhile` is free to drop any subset of elements matching the predicate, not necessarily a contiguous prefix — the result is nondeterministic and should only be relied upon when the encounter order is well-defined.

## 6. Walkthrough

Tracing the Level 2 log-processing example from `main` to output:

Execution begins in `LogDropWhile.main`. A `List<LogEntry>` of six time-ordered log entries is created. The local variable `cutOff` is set to `LocalTime.of(8, 30)`.

`logs.stream()` creates a sequential stream over the list, preserving the insertion order (the logs are already time-ordered). `.dropWhile(entry -> entry.time().isBefore(cutOff))` attaches the `dropWhile` operation.

**How the stream pipeline evaluates** — Java streams are lazy: no work happens until the terminal operation `.collect(Collectors.toList())` is called. When the terminal operation triggers consumption, the stream begins pulling elements one at a time:

- **First pull**: element at index 0 — `LogEntry[08:15, "Server starting"]`. The pipeline asks `dropWhile` whether to drop it. `dropWhile` evaluates the predicate on this element: `entry.time().isBefore(LocalTime.of(8,30))` → `08:15.isBefore(08:30)` → `true`. The predicate returned `true`, so `dropWhile` discards this element and signals the upstream source (the list) to provide the next element.

- **Second pull**: element at index 1 — `LogEntry[08:16, "Loading config"]`. Predicate: `08:16.isBefore(08:30)` → `true`. Dropped. Signal for next.

- **Third pull**: element at index 2 — `LogEntry[08:30, "Ready"]`. Predicate: `08:30.isBefore(08:30)` → `false`. This is the turning point. `dropWhile` records internally that the predicate has failed for the first time. From this moment forward, it stops evaluating the predicate entirely and enters "pass-through" mode. This element (`08:30, "Ready"`) is sent downstream to the collector.

- **Fourth through sixth pulls**: elements at indices 3–5 — `08:31 "Request received"`, `08:32 "Processed"`, `08:33 "Response sent"`. Since `dropWhile` is now in pass-through mode, these are forwarded directly downstream without any predicate evaluation. The collector receives each one and accumulates them.

When the upstream source is exhausted (six elements produced), the stream pipeline terminates and `.collect(Collectors.toList())` returns the accumulated `List` containing the four entries from `08:30` onwards.

Back in `main`, `afterCutoff` is that list. The `System.out.println("Logs from 08:30 onwards:")` prints the header, then `afterCutoff.forEach(...)` iterates the four entries and prints each with its time and message.

```
                         ┌──────────────────────────┐
  logs.stream()          │       dropWhile           │        collect(toList())
  ──────────────────────►│  predicate: time < 08:30  │───────────────────────►
                         │                           │
  [08:15, 08:16,         │  08:15 → true → DROP     │
   08:30, 08:31,         │  08:16 → true → DROP     │
   08:32, 08:33]         │  08:30 → false → KEEP ───┤  [08:30, 08:31,
                         │  08:31 → pass-through ───┤   08:32, 08:33]
                         │  08:32 → pass-through ───┤
                         │  08:33 → pass-through ───┤
                         └──────────────────────────┘
```

## 7. Gotchas & takeaways

> `dropWhile` on an unordered stream (e.g. from a `HashSet` or a `parallelStream()`) is nondeterministic — it drops elements matching the predicate wherever they happen to appear, not necessarily a contiguous prefix. If you need predictable prefix-dropping behaviour, ensure the stream is ordered (by using a list source or calling `.sorted()` first).

- `dropWhile` is a **stateful intermediate operation** — it must remember whether the predicate has already failed, which means it carries a small amount of internal state across element evaluations, unlike stateless operations like `map` or `filter`.
- The predicate is evaluated **only on the leading elements** and stops being evaluated forever once it returns `false` once. This makes `dropWhile` more efficient than `filter` for prefix-discarding scenarios — `filter` would evaluate every element, while `dropWhile` evaluates only the prefix.
- Together with `takeWhile`, `dropWhile` forms a complementary pair: `takeWhile` keeps the prefix, `dropWhile` discards it. You can split a stream into two parts with a single predicate: the taken prefix (via `takeWhile`) and the dropped remainder (via `dropWhile`), though this requires consuming the stream twice or collecting it first.
- `dropWhile` never throws an exception for an empty stream — it simply produces an empty stream, which is consistent with the general stream principle that operations on empty streams produce empty streams.
- For null-unfriendly predicates, wrap with care — if the stream contains `null` elements and the predicate dereferences them, a `NullPointerException` will be thrown at evaluation time. 