---
card: java
gi: 528
slug: side-effects-purity-rules
title: Side-effects & purity rules
---

## 1. What it is

Stream operations are designed around **pure functions**: functions whose output depends only on their input, with no observable side effects (no mutating shared state, no I/O beyond what the operation itself is meant to do). The functions you pass to `filter`, `map`, `reduce`, and most other stream operations should be **stateless** — they should not read or write variables outside their own scope in a way that affects the result. Streams *can* technically run side-effecting lambdas, but doing so — especially with a parallel stream — can produce incorrect, non-deterministic, or simply undefined results.

## 2. Why & when

The stream framework is free to reorder, batch, or parallelize the evaluation of the functions you supply — it makes no promise about exactly when or how many times a given lambda runs, especially for stateless operations under parallel execution. If a lambda depends on or mutates external mutable state (a shared counter, a `List` being appended to from within `map`), the result becomes dependent on unpredictable evaluation order and can differ between runs, between JVMs, or between sequential and parallel execution of the *identical* pipeline. Writing pure, side-effect-free functions for `filter`/`map`/`reduce` is what keeps stream code both correct and safe to parallelize without rewriting the logic.

## 3. Core concept

```java
import java.util.*;
import java.util.stream.*;

List<Integer> numbers = List.of(1, 2, 3, 4, 5);

// UNSAFE: mutating shared state from within map -- works "by accident" on this sequential stream,
// but is not guaranteed and breaks under parallel execution.
List<Integer> unsafeResults = new ArrayList<>();
numbers.stream().map(n -> {
    unsafeResults.add(n * 2); // side effect -- writes to external mutable state
    return n * 2;
}).toList();

// SAFE: the transformation itself produces the result -- no external mutation needed.
List<Integer> safeResults = numbers.stream().map(n -> n * 2).toList();
```

The safe version's `map` lambda is a pure function: given `n`, it always returns `n * 2` and touches nothing else — the unsafe version smuggles a side effect into a place the stream framework doesn't guarantee will run predictably.

## 4. Diagram

<svg viewBox="0 0 640 130" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="a pure lambda's result depends only on its input; an impure lambda mutates shared external state">
  <rect x="8" y="8" width="624" height="114" rx="8" fill="#0d1117"/>
  <rect x="30" y="20" width="180" height="40" rx="6" fill="#1c2430" stroke="#6db33f"/><text x="120" y="45" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">pure: n -&gt; n * 2</text>
  <text x="240" y="45" fill="#6db33f" font-size="10" font-family="sans-serif">safe under parallel execution</text>

  <rect x="30" y="75" width="180" height="40" rx="6" fill="#1c2430" stroke="#f85149"/><text x="120" y="100" fill="#f85149" font-size="11" text-anchor="middle" font-family="sans-serif">impure: n -&gt; { list.add(n); ... }</text>
  <text x="240" y="100" fill="#f85149" font-size="10" font-family="sans-serif">unsafe: shared mutable state</text>
</svg>

The pure lambda's output depends only on its argument; the impure one reaches outside itself to mutate a shared `list`, which is exactly what breaks under unpredictable or parallel evaluation order.

## 5. Runnable example

Scenario: computing a running total and a filtered list from a stream of transaction amounts — evolved from demonstrating a side-effecting bug that happens to work sequentially, through showing it break under parallel execution, to a version using proper stream idioms to achieve the same result purely and safely.

### Level 1 — Basic

```java
import java.util.*;
import java.util.stream.*;

public class SideEffectSequential {
    public static void main(String[] args) {
        List<Integer> amounts = List.of(10, 20, 30, 40, 50);

        // Works "by accident" here because this stream is sequential -- but it's still bad practice.
        List<Integer> doubled = new ArrayList<>();
        amounts.stream().forEach(n -> doubled.add(n * 2));

        System.out.println("Doubled (sequential, order preserved): " + doubled);
    }
}
```

**How to run:** `java SideEffectSequential.java`

Expected output:
```
Doubled (sequential, order preserved): [20, 40, 60, 80, 100]
```

This code happens to produce the correct, ordered result — but only because the stream is sequential, so `forEach` processes elements strictly in order, and `ArrayList.add(...)` from a single thread is safe. Nothing about the stream API *guarantees* this will keep working if the pipeline changes; it works by coincidence of sequential execution, not by design.

### Level 2 — Intermediate

```java
import java.util.*;
import java.util.stream.*;

public class SideEffectParallelBroken {
    public static void main(String[] args) {
        List<Integer> amounts = IntStream.rangeClosed(1, 10_000).boxed().toList();

        // The SAME pattern as before, but now on a parallel stream -- ArrayList is not thread-safe.
        List<Integer> doubled = new ArrayList<>();
        amounts.parallelStream().forEach(n -> doubled.add(n * 2)); // UNSAFE: concurrent writes to ArrayList

        // The size is often wrong (data lost), and could even throw or corrupt internal state.
        System.out.println("Expected size: " + amounts.size());
        System.out.println("Actual size (may be wrong or vary run to run): " + doubled.size());
        System.out.println("Sizes match: " + (doubled.size() == amounts.size()));
    }
}
```

**How to run:** `java SideEffectParallelBroken.java`

Expected output (illustrative — the actual numbers are inherently unpredictable and may even throw an exception on some runs):
```
Expected size: 10000
Actual size (may be wrong or vary run to run): [some number, often less than 10000, varies by run]
Sizes match: false
```

The real-world concern this adds: the exact same side-effecting pattern from Level 1, but now on a `.parallelStream()`. Multiple threads now call `doubled.add(...)` **concurrently**, and `ArrayList` is not thread-safe — concurrent, unsynchronized modifications can silently lose elements, throw `ArrayIndexOutOfBoundsException`, or in rare cases even corrupt the list's internal structure, all without any compile-time warning that anything was wrong. This is precisely the failure mode the purity rule exists to prevent.

### Level 3 — Advanced

```java
import java.util.*;
import java.util.stream.*;

public class PureStreamIdiom {
    public static void main(String[] args) {
        List<Integer> amounts = IntStream.rangeClosed(1, 10_000).boxed().toList();

        // Pure, idiomatic streams: no shared mutable state touched by any lambda.
        List<Integer> doubled = amounts.parallelStream()
                .map(n -> n * 2)   // pure: depends only on n, mutates nothing external
                .toList();         // the stream framework handles safe, correct accumulation internally

        long sum = amounts.parallelStream()
                .mapToLong(n -> n) // pure
                .sum();            // built-in reduction -- correct and safe under parallelism by design

        System.out.println("Doubled size: " + doubled.size());
        System.out.println("Sizes match: " + (doubled.size() == amounts.size()));
        System.out.println("Sum: " + sum);
    }
}
```

**How to run:** `java PureStreamIdiom.java`

Expected output:
```
Doubled size: 10000
Sizes match: true
Sum: 50005000
```

This achieves the exact same goals — a doubled list and a total sum — using purely functional stream operations with no manual mutation anywhere. `.map(n -> n * 2)` is a pure function; `.toList()` handles the actual accumulation internally, using thread-safe mechanisms the stream framework itself is responsible for getting right. `.mapToLong(n -> n).sum()` similarly delegates the accumulation to a built-in, parallel-safe reduction rather than a hand-rolled, side-effecting one. Both correctly and deterministically produce `10000` elements and the exact sum `50005000` (the sum of `1` through `10,000`), regardless of how many threads the parallel execution actually uses.

## 6. Walkthrough

Execution starts in `main` of the Level 3 example. `amounts` is a `List<Integer>` of `1` through `10,000`.

`amounts.parallelStream().map(n -> n * 2).toList()` builds a parallel pipeline. The stream framework splits `amounts` (backed by an `ArrayList`, which splits cheaply — see [[parallel-streams-spliterators]]) into chunks distributed across worker threads. Each thread independently applies `n -> n * 2` to its assigned chunk of numbers — since this lambda is pure (its result depends only on `n`, and it touches no shared state), it's completely safe for many threads to run it concurrently and simultaneously, with zero risk of interference between threads, since none of them read or write anything outside their own local computation.

Once every thread finishes transforming its chunk, `.toList()` (the terminal operation) is responsible for correctly and safely merging all the transformed chunks back into a single, correctly-ordered `List<Integer>` — this merging logic lives inside the well-tested, thread-safe internals of the stream framework itself, not in any code the caller wrote, which is exactly the point: the caller never has to reason about concurrent list mutation, because no caller-supplied lambda ever mutates a shared list directly.

```
amounts (10,000 elements) split across threads (illustrative):
  thread A: chunk [1..2500]   -> map(n->n*2) purely, independently
  thread B: chunk [2501..5000] -> map(n->n*2) purely, independently
  thread C: chunk [5001..7500] -> map(n->n*2) purely, independently
  thread D: chunk [7501..10000]-> map(n->n*2) purely, independently

toList() merges all four chunks' results, IN ORDER, into one final List<Integer> of 10,000 elements.
(No thread ever touches another thread's chunk or any shared mutable structure directly.)
```

`doubled.size()` is `10000`, matching `amounts.size()` exactly — `"Sizes match: true"`. Separately, `amounts.parallelStream().mapToLong(n -> n).sum()` follows the same pure pattern: `mapToLong(n -> n)` is a pure identity-like transformation (just widening `int` to `long`), and `.sum()` is a built-in reduction the stream framework performs correctly across parallel chunks internally — the result, `50005000`, is Gauss's formula for the sum of `1` through `10,000` (`10000 * 10001 / 2 = 50005000`), computed correctly regardless of how the work happened to be distributed across threads.

## 7. Gotchas & takeaways

> A side-effecting lambda that happens to "work" on a sequential stream is not proof of correctness — it's proof that sequential execution masked the underlying design flaw. The moment that same pipeline is switched to `.parallel()` (or even just refactored in a way that changes evaluation order), a previously "working" side-effecting lambda can silently produce wrong results, as demonstrated in Level 2. Treat any lambda passed to a stream operation that mutates external state as a bug waiting to surface, even if current tests pass.

- Stream operation lambdas (`filter`, `map`, `reduce`, and most others) should be pure: their result depends only on their input, with no side effects on shared mutable state.
- A side-effecting lambda may appear to work correctly on a sequential stream purely by coincidence of execution order — this is not a guarantee the stream API makes.
- Parallel streams make impure lambdas' problems concrete and visible: concurrent, unsynchronized mutation of shared state (like an `ArrayList`) from multiple threads can silently lose data, throw exceptions, or corrupt internal structure.
- Prefer built-in stream idioms (`map`/`filter`/`collect`/`reduce`/`sum`) that produce a result directly, over side-effecting patterns (`forEach` with external mutation) that rely on manually managing shared state.
- When a genuine side effect is unavoidable and safe (e.g. a truly independent, thread-safe operation per element, like writing to a `ConcurrentHashMap`), be deliberate and explicit about it — don't rely on an ordinary, non-thread-safe collection working "by accident" under parallel execution.
