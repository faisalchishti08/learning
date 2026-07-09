---
card: java
gi: 507
slug: findfirst-findany
title: findFirst() / findAny()
---

## 1. What it is

`Stream.findFirst()` and `Stream.findAny()` are short-circuiting terminal operations that return a single element from the stream, wrapped in `Optional<T>` — empty if the stream had no elements (or none matched, when used after a `filter`). `findFirst()` always returns the *first* element in the stream's encounter order. `findAny()` returns *some* element with no ordering guarantee — for a sequential stream it typically behaves the same as `findFirst()`, but for a **parallel** stream it may return whichever matching element is found first by whichever thread gets there first, which can be faster since no thread needs to coordinate about which one is "the first."

## 2. Why & when

You reach for `findFirst()`/`findAny()` whenever you need just one result — the first user matching a condition, any available worker from a pool, a single example satisfying a rule — rather than every match. Combined with `filter`, they're a direct, short-circuiting way to search: "find the first order over $1000" stops scanning the moment it finds one, rather than filtering the entire stream and then taking the first element of the result.

The choice between them matters specifically for parallel streams: `findFirst()` guarantees encounter-order correctness but may require extra coordination between threads to determine which result truly comes first; `findAny()` has no such requirement and can be more efficient in parallel, at the cost of non-determinism about *which* matching element you get back.

## 3. Core concept

```java
import java.util.*;
import java.util.stream.*;

List<Integer> numbers = List.of(3, 7, 12, 18, 25);

Optional<Integer> firstEven = numbers.stream()
        .filter(n -> n % 2 == 0)
        .findFirst(); // Optional[12] -- always the first match in order

Optional<Integer> anyEven = numbers.parallelStream()
        .filter(n -> n % 2 == 0)
        .findAny(); // Optional[12] or Optional[18] -- either is valid in parallel
```

Both stop scanning as soon as a qualifying element is found, wrap it in `Optional`, and never examine the rest of the stream — `findFirst` guarantees which one, `findAny` doesn't (though it often happens to match on a sequential stream).

## 4. Diagram

<svg viewBox="0 0 640 120" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="findFirst always returns the first match; findAny may return any match, especially in parallel">
  <rect x="8" y="8" width="624" height="104" rx="8" fill="#0d1117"/>
  <rect x="30" y="20" width="45" height="30" fill="#1c2430" stroke="#8b949e"/><text x="52" y="40" fill="#8b949e" font-size="12" text-anchor="middle" font-family="monospace">3</text>
  <rect x="85" y="20" width="45" height="30" fill="#1c2430" stroke="#8b949e"/><text x="107" y="40" fill="#8b949e" font-size="12" text-anchor="middle" font-family="monospace">7</text>
  <rect x="140" y="20" width="45" height="30" fill="#1c2430" stroke="#6db33f" stroke-width="2.5"/><text x="162" y="40" fill="#6db33f" font-size="12" text-anchor="middle" font-family="monospace">12</text>
  <rect x="195" y="20" width="45" height="30" fill="#1c2430" stroke="#79c0ff"/><text x="217" y="40" fill="#79c0ff" font-size="12" text-anchor="middle" font-family="monospace">18</text>
  <rect x="250" y="20" width="45" height="30" fill="#1c2430" stroke="#8b949e"/><text x="272" y="40" fill="#8b949e" font-size="12" text-anchor="middle" font-family="monospace">25</text>
  <text x="20" y="75" fill="#6db33f" font-size="10" font-family="sans-serif">findFirst(): always 12 (first even, in order)</text>
  <text x="20" y="95" fill="#79c0ff" font-size="10" font-family="sans-serif">findAny() on a parallel stream: could return 12 OR 18</text>
</svg>

`findFirst` is pinned to encounter order; `findAny` is free to return whichever qualifying element is discovered first, which matters once parallel execution is involved.

## 5. Runnable example

Scenario: locating a specific user account in a directory lookup — evolved from a plain sequential `findFirst`, through demonstrating `findAny`'s relaxed guarantee on a parallel stream, to a version showing the practical performance trade-off between the two on a larger search.

### Level 1 — Basic

```java
import java.util.*;
import java.util.stream.*;

public class FindFirstBasic {
    record User(String username, boolean active) {}

    public static void main(String[] args) {
        List<User> users = List.of(
                new User("alice", false),
                new User("bob", true),
                new User("carol", true)
        );

        Optional<User> firstActive = users.stream()
                .filter(User::active)
                .findFirst();

        firstActive.ifPresentOrElse(
                u -> System.out.println("First active user: " + u.username()),
                () -> System.out.println("No active users found")
        );
    }
}
```

**How to run:** `java FindFirstBasic.java`

Expected output:
```
First active user: bob
```

`.filter(User::active)` keeps `bob` and `carol` (both active), dropping `alice`. `.findFirst()` returns the first one in encounter order — `bob` — wrapped in `Optional`, without needing to check whether `carol` also matches, since the answer is already determined by the time `bob` is found.

### Level 2 — Intermediate

```java
import java.util.*;
import java.util.stream.*;

public class FindAnyParallel {
    record User(String username, boolean active) {}

    public static void main(String[] args) {
        List<User> users = List.of(
                new User("alice", false),
                new User("bob", true),
                new User("carol", true),
                new User("dave", true)
        );

        // On a sequential stream, findAny() commonly behaves like findFirst() -- but that's not guaranteed.
        Optional<User> anyActive = users.stream()
                .filter(User::active)
                .findAny();

        System.out.println("Some active user: " + anyActive.map(User::username).orElse("none"));

        // On a parallel stream, findAny() may legitimately return any of bob/carol/dave.
        Optional<User> anyActiveParallel = users.parallelStream()
                .filter(User::active)
                .findAny();

        System.out.println("Some active user (parallel): " + anyActiveParallel.map(User::username).orElse("none"));
    }
}
```

**How to run:** `java FindAnyParallel.java`

Expected output (the parallel line's exact name may vary run to run):
```
Some active user: bob
Some active user (parallel): bob
```

The real-world concern this adds: `findAny()` doesn't promise which element you get, only that it's *a* match. On the sequential stream, it happens to return `bob` (the same as `findFirst()` would) because there's no parallelism to reorder anything. On `parallelStream()`, `findAny()` is explicitly free to return `bob`, `carol`, or `dave` — whichever the runtime discovers first — even though this particular run may still show `bob` for such a small list.

### Level 3 — Advanced

```java
import java.util.*;
import java.util.stream.*;

public class FindFirstVsAnyPerformance {
    public static void main(String[] args) {
        List<Integer> bigList = IntStream.rangeClosed(1, 5_000_000).boxed().toList();

        long t1 = System.nanoTime();
        Optional<Integer> first = bigList.parallelStream()
                .filter(n -> n > 4_000_000)
                .findFirst(); // must coordinate to guarantee encounter-order correctness
        long t2 = System.nanoTime();

        Optional<Integer> any = bigList.parallelStream()
                .filter(n -> n > 4_000_000)
                .findAny(); // free to return whichever qualifying element surfaces first
        long t3 = System.nanoTime();

        System.out.println("findFirst found: " + first.isPresent());
        System.out.println("findAny found: " + any.isPresent());
        System.out.println("Both completed: " + (t2 > t1 && t3 > t2));
    }
}
```

**How to run:** `java FindFirstVsAnyPerformance.java`

Expected output:
```
findFirst found: true
findAny found: true
Both completed: true
```

This demonstrates the practical trade-off at scale: on a five-million-element parallel stream, `findFirst()` must ensure whatever it returns is genuinely the lowest-indexed match (requiring coordination across worker threads about ordering), while `findAny()` has no such obligation and can return as soon as *any* thread finds a qualifying element — often faster in practice for large parallel searches where the specific match found doesn't matter, only that a match exists. (Exact nanosecond timings aren't printed here since they vary by machine; the key point is both correctly find a result.)

## 6. Walkthrough

Execution starts in `main` of the Level 3 example. `bigList` is built as a `List<Integer>` of five million sequential integers, `1` through `5,000,000`.

`bigList.parallelStream()` creates a parallel stream, which the JVM's common `ForkJoinPool` splits into chunks distributed across available CPU cores. `.filter(n -> n > 4_000_000)` is applied to each chunk independently and in parallel — different threads evaluate different portions of the five million numbers simultaneously, each keeping only the values greater than four million.

`.findFirst()` is the terminal operation for the first search. Because `findFirst()` must return the element with the lowest original index among all matches, the parallel machinery needs to coordinate: even if a thread processing a *later* chunk (say, numbers 4,500,000–5,000,000) finds a match instantly, it cannot report success until it's confirmed no *earlier* chunk (say, numbers 4,000,001–4,500,000) has already found a lower-indexed match — this coordination is the extra cost `findFirst()` pays for its ordering guarantee.

```
parallelStream() splits bigList across threads (illustrative):
  thread A: chunk [1 .. 1,666,666]
  thread B: chunk [1,666,667 .. 3,333,333]
  thread C: chunk [3,333,334 .. 5,000,000]

findFirst(): must confirm the match from thread C (e.g. 4,000,001) isn't
             preceded by an earlier-indexed match -- coordinates across threads.

findAny():   returns as soon as any thread reports a match --
             no coordination needed about which one is "first".
```

`.findFirst()` eventually returns `Optional.of(4_000_001)` — the true lowest-indexed value greater than four million, found by scanning in a way that respects overall encounter order despite parallel execution. `.findAny()`, run separately afterward, also finds a match (likely also `4_000_001` in practice for this particular filter, since it's the very first qualifying value encountered by whichever thread processes that region, but this is not guaranteed by the API's contract).

`first.isPresent()` and `any.isPresent()` are both `true`, printed accordingly. `t2 > t1 && t3 > t2` simply confirms the three timestamps were captured in increasing order (proving both searches actually ran to completion), printed as `"Both completed: true"` — a stand-in for the real point, which is that `findAny()` is permitted more freedom than `findFirst()` and can therefore be implemented more efficiently in a parallel context.

## 7. Gotchas & takeaways

> On a **sequential** stream, `findFirst()` and `findAny()` behave identically in practice — both return the first element in encounter order, since there's no parallelism to introduce ambiguity. The difference only becomes observable (and only becomes a real choice worth making deliberately) once `.parallel()`/`.parallelStream()` is involved.

- `findFirst()` guarantees the first element in encounter order; `findAny()` makes no such guarantee, though it often matches `findFirst()` on sequential streams.
- Both are short-circuiting: they stop scanning as soon as a qualifying element is found, without necessarily examining the rest of the stream.
- Prefer `findAny()` over `findFirst()` on parallel streams when *which specific* matching element you get doesn't matter — it avoids the extra coordination overhead `findFirst()` needs to guarantee ordering.
- Prefer `findFirst()` whenever the specific, deterministic "first" element matters to your logic, even on a parallel stream, since correctness should come before the potential performance gain.
- Both return `Optional<T>`, so always handle the empty case (no elements, or none matched a preceding filter) via `.isPresent()`, `.orElse(...)`, `.ifPresentOrElse(...)`, or similar — never assume a match was found.
