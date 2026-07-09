---
card: java
gi: 484
slug: stream-iterate
title: Stream.iterate()
---

## 1. What it is

`Stream.iterate(...)` builds an infinite (or bounded) stream by repeatedly applying a function to the previous element, starting from a `seed`. The classic two-argument form is `Stream.iterate(seed, next)`: it produces `seed`, `next.apply(seed)`, `next.apply(next.apply(seed))`, and so on forever. Java 9 added a three-argument overload, `Stream.iterate(seed, hasNext, next)`, which stops once `hasNext` returns `false` — no separate `.limit(...)` call required.

## 2. Why & when

Sometimes the data you want to stream isn't sitting in a collection at all — it's a *sequence* defined by a rule: the next power of two, the next Fibonacci number, the next date a week later. `Stream.iterate` lets you describe that rule once (how to get from one element to the next) and let the stream machinery generate as many elements as you need, lazily, only computing each one when it's actually consumed.

You reach for it when your data is generative rather than stored — counters, arithmetic/geometric progressions, recursive sequences, or a chain of transformations applied repeatedly until some condition holds. Because the two-argument form is infinite by default, it's almost always paired with `.limit(n)` to cap it, unless you use the three-argument, condition-based overload instead.

## 3. Core concept

```java
import java.util.stream.*;

// Two-argument form: infinite -- MUST be limited
Stream<Integer> powersOfTwo = Stream.iterate(1, n -> n * 2).limit(5); // 1, 2, 4, 8, 16

// Three-argument form (Java 9+): self-limiting via a condition
Stream<Integer> upToHundred = Stream.iterate(1, n -> n <= 100, n -> n * 2); // 1, 2, 4, ..., 64
```

Each element is produced by applying `next` to the *previous* element — the sequence is entirely determined by the seed and the function, computed lazily one step at a time as the stream is consumed.

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Stream.iterate repeatedly applies a function to the previous value, starting from a seed">
  <rect x="8" y="8" width="624" height="134" rx="8" fill="#0d1117"/>
  <rect x="20" y="55" width="70" height="34" rx="4" fill="#1c2430" stroke="#6db33f"/><text x="55" y="77" fill="#6db33f" font-size="12" text-anchor="middle" font-family="monospace">seed=1</text>
  <text x="115" y="77" fill="#8b949e" font-size="13" font-family="sans-serif">-&gt;</text>
  <rect x="135" y="55" width="60" height="34" rx="4" fill="#1c2430" stroke="#79c0ff"/><text x="165" y="77" fill="#79c0ff" font-size="12" text-anchor="middle" font-family="monospace">2</text>
  <text x="205" y="77" fill="#8b949e" font-size="13" font-family="sans-serif">-&gt;</text>
  <rect x="225" y="55" width="60" height="34" rx="4" fill="#1c2430" stroke="#79c0ff"/><text x="255" y="77" fill="#79c0ff" font-size="12" text-anchor="middle" font-family="monospace">4</text>
  <text x="295" y="77" fill="#8b949e" font-size="13" font-family="sans-serif">-&gt;</text>
  <rect x="315" y="55" width="60" height="34" rx="4" fill="#1c2430" stroke="#79c0ff"/><text x="345" y="77" fill="#79c0ff" font-size="12" text-anchor="middle" font-family="monospace">8</text>
  <text x="385" y="77" fill="#8b949e" font-size="13" font-family="sans-serif">-&gt;</text>
  <rect x="405" y="55" width="60" height="34" rx="4" fill="#1c2430" stroke="#79c0ff"/><text x="435" y="77" fill="#79c0ff" font-size="12" text-anchor="middle" font-family="monospace">...</text>
  <text x="20" y="120" fill="#8b949e" font-size="10" font-family="sans-serif">next = n -&gt; n * 2. Each new element comes from applying "next" to the one before it.</text>
</svg>

Each arrow is one application of the `next` function to the previous element, starting from the seed.

## 5. Runnable example

Scenario: generating a sequence of retry-delay values for a network client — evolved from a plain doubling sequence, through a self-limiting condition-based version, to a version that carries extra state (attempt number) alongside the delay using a record.

### Level 1 — Basic

```java
import java.util.stream.*;

public class IterateBasic {
    public static void main(String[] args) {
        Stream.iterate(1, n -> n * 2)
                .limit(5)
                .forEach(delay -> System.out.println("Retry delay: " + delay + "s"));
    }
}
```

**How to run:** `java IterateBasic.java`

Expected output:
```
Retry delay: 1s
Retry delay: 2s
Retry delay: 4s
Retry delay: 8s
Retry delay: 16s
```

`Stream.iterate(1, n -> n * 2)` starts at `1` and repeatedly doubles: `1, 2, 4, 8, 16, 32, ...` forever. Because this form never stops on its own, `.limit(5)` caps it to the first five elements before `.forEach` prints each one.

### Level 2 — Intermediate

```java
import java.util.stream.*;

public class IterateCapped {
    static final int MAX_DELAY = 30;

    public static void main(String[] args) {
        // Three-argument form: stop once the delay would exceed MAX_DELAY -- no .limit() needed.
        Stream.iterate(1, delay -> delay <= MAX_DELAY, delay -> delay * 2)
                .forEach(delay -> System.out.println("Retry delay: " + delay + "s"));
    }
}
```

**How to run:** `java IterateCapped.java`

Expected output:
```
Retry delay: 1s
Retry delay: 2s
Retry delay: 4s
Retry delay: 8s
Retry delay: 16s
```

The real-world concern this adds: instead of guessing a fixed `.limit(5)`, the stream now stops itself once the *condition* (`delay <= MAX_DELAY`) becomes false — a real retry policy would define "stop" in terms of a business rule (a maximum delay cap) rather than a hardcoded element count, which could silently under- or over-generate if the growth rate ever changed.

### Level 3 — Advanced

```java
import java.util.stream.*;

public class IterateAttempts {
    record RetryAttempt(int attemptNumber, int delaySeconds) {}

    static final int MAX_DELAY = 30;

    public static void main(String[] args) {
        RetryAttempt seed = new RetryAttempt(1, 1);

        Stream.iterate(
                seed,
                attempt -> attempt.delaySeconds() <= MAX_DELAY,
                attempt -> new RetryAttempt(attempt.attemptNumber() + 1, attempt.delaySeconds() * 2)
        ).forEach(attempt -> System.out.println(
                "Attempt #" + attempt.attemptNumber() + " -> wait " + attempt.delaySeconds() + "s"));
    }
}
```

**How to run:** `java IterateAttempts.java`

Expected output:
```
Attempt #1 -> wait 1s
Attempt #2 -> wait 2s
Attempt #3 -> wait 4s
Attempt #4 -> wait 8s
Attempt #5 -> wait 16s
```

The seed and `next` function now carry a small `record` (`RetryAttempt`) instead of a bare `int`, bundling the attempt number together with the delay so downstream code has both pieces of context without needing a separate counter — a common pattern once a generated sequence needs to track more than one piece of state per step.

## 6. Walkthrough

Execution starts in `main` of the Level 3 example. `seed` is created as `RetryAttempt(1, 1)` — attempt one, one-second delay.

`Stream.iterate(seed, hasNext, next)` is called. Internally, the stream first yields `seed` itself, `RetryAttempt(1, 1)`. Before yielding it, the pipeline (via `.forEach`) checks `hasNext` on it: `attempt.delaySeconds() <= MAX_DELAY` is `1 <= 30`, `true`, so it's kept and printed: `"Attempt #1 -> wait 1s"`.

Next, `next` is applied to that element: `new RetryAttempt(1 + 1, 1 * 2)` produces `RetryAttempt(2, 2)`. `hasNext` checks `2 <= 30`, `true` — printed: `"Attempt #2 -> wait 2s"`.

This repeats: `next` transforms `RetryAttempt(2, 2)` into `RetryAttempt(3, 4)` (`3 <= 30` passes, printed), then `RetryAttempt(3, 4)` into `RetryAttempt(4, 8)` (`4 <= 30` passes, printed), then `RetryAttempt(4, 8)` into `RetryAttempt(5, 16)` (`5`th attempt, `16 <= 30` passes, printed).

```
seed (1,1) --hasNext:1<=30 true--> print "#1 -> 1s" --next--> (2,2)
(2,2) --hasNext:2<=30 true--> print "#2 -> 2s" --next--> (3,4)
(3,4) --hasNext:4<=30 true--> print "#3 -> 4s" --next--> (4,8)
(4,8) --hasNext:8<=30 true--> print "#4 -> 8s" --next--> (5,16)
(5,16)--hasNext:16<=30 true--> print "#5 -> 16s" --next--> (6,32)
(6,32)--hasNext:32<=30 FALSE--> stream stops, nothing printed for attempt #6
```

`next` is then applied one more time, producing `RetryAttempt(6, 32)`. This time `hasNext` checks `32 <= 30`, which is `false` — the stream stops *before* yielding this element, so `"Attempt #6"` is never printed. The pipeline terminates cleanly with exactly five lines of output.

## 7. Gotchas & takeaways

> The two-argument form, `Stream.iterate(seed, next)`, is **infinite** — if you forget `.limit(n)` (or a short-circuiting operation like `.findFirst()`), a terminal operation like `.forEach()` or `.count()` will run forever (or until memory/time runs out). Always pair the two-argument form with a limiting operation, or prefer the three-argument, condition-based overload instead.

- `Stream.iterate(seed, next)` generates an infinite sequence by repeatedly applying `next` to the previous element — always limit it.
- `Stream.iterate(seed, hasNext, next)` (Java 9+) stops on its own once `hasNext` returns `false`, checked *before* each element is emitted, including the seed.
- The generated sequence is lazy: elements are computed one at a time as they're consumed, not all upfront.
- The seed and elements don't have to be primitives — bundling multiple pieces of state into a small `record` is a natural way to carry richer per-step data through the sequence.
- Prefer the three-argument overload when the stopping rule is a genuine business condition, since it keeps the "when to stop" logic next to the generation logic instead of a separate, easy-to-get-wrong `.limit(n)` count.
