---
card: java
gi: 485
slug: stream-generate
title: Stream.generate()
---

## 1. What it is

`Stream.generate(supplier)` builds an infinite stream where every element comes from calling a `Supplier<T>` — a zero-argument function — over and over. Unlike `Stream.iterate`, each call to the supplier is independent: it doesn't receive the previous element as input, so the sequence it produces doesn't have to follow any arithmetic pattern at all. It's commonly used with a stateful or random supplier, always paired with `.limit(n)` since it never stops on its own.

## 2. Why & when

Some sequences aren't defined by "take the last value and transform it" (that's `Stream.iterate`'s job) — they're defined by "call this thing again and produce a new value," where the new value might depend on external state, randomness, or a side effect rather than the previous stream element. Think: random numbers, UUIDs, the current timestamp, reading the next line from some external source, or a fixed constant repeated many times.

You reach for `Stream.generate` when you need a stream of "produce me another one" values with no dependency between consecutive elements — most commonly random data generation, test fixtures, or default/constant values repeated a known number of times.

## 3. Core concept

```java
import java.util.stream.*;
import java.util.function.*;

// Constant repeated 3 times
Stream.generate(() -> "x").limit(3); // "x", "x", "x"

// Each call is independent -- no relation to the previous element
Supplier<Double> randomSupplier = Math::random;
Stream.generate(randomSupplier).limit(5); // 5 unrelated random doubles
```

Every element is the result of a fresh call to `supplier.get()` — the stream itself carries no memory of what came before.

## 4. Diagram

<svg viewBox="0 0 640 140" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Stream.generate calls a supplier repeatedly, with each call independent of the last">
  <rect x="8" y="8" width="624" height="124" rx="8" fill="#0d1117"/>
  <rect x="250" y="20" width="140" height="34" rx="4" fill="#1c2430" stroke="#6db33f"/><text x="320" y="42" fill="#6db33f" font-size="12" text-anchor="middle" font-family="monospace">supplier.get()</text>
  <line x1="320" y1="54" x2="320" y2="70" stroke="#8b949e" stroke-width="1.5"/>
  <rect x="40" y="80" width="90" height="34" rx="4" fill="#1c2430" stroke="#79c0ff"/><text x="85" y="102" fill="#79c0ff" font-size="12" text-anchor="middle" font-family="monospace">call #1</text>
  <rect x="150" y="80" width="90" height="34" rx="4" fill="#1c2430" stroke="#79c0ff"/><text x="195" y="102" fill="#79c0ff" font-size="12" text-anchor="middle" font-family="monospace">call #2</text>
  <rect x="260" y="80" width="90" height="34" rx="4" fill="#1c2430" stroke="#79c0ff"/><text x="305" y="102" fill="#79c0ff" font-size="12" text-anchor="middle" font-family="monospace">call #3</text>
  <rect x="370" y="80" width="90" height="34" rx="4" fill="#1c2430" stroke="#79c0ff"/><text x="415" y="102" fill="#79c0ff" font-size="12" text-anchor="middle" font-family="monospace">call #4</text>
  <text x="20" y="122" fill="#8b949e" font-size="10" font-family="sans-serif">Each call is independent -- no element feeds into the next, unlike Stream.iterate.</text>
</svg>

Every element comes from an independent invocation of the same supplier — there's no chain from one value to the next.

## 5. Runnable example

Scenario: generating test-user records for a fixture set — evolved from a repeated constant value, through independent random IDs, to a stateful supplier that produces sequential, deterministic IDs (a common alternative to pure randomness when tests need reproducibility).

### Level 1 — Basic

```java
import java.util.stream.*;

public class GenerateBasic {
    public static void main(String[] args) {
        Stream.generate(() -> "guest")
                .limit(3)
                .forEach(System.out::println);
    }
}
```

**How to run:** `java GenerateBasic.java`

Expected output:
```
guest
guest
guest
```

`Stream.generate(() -> "guest")` calls the supplier lambda three times (because of `.limit(3)`); since the lambda always returns the same literal, every element is identical. This is the simplest possible use: repeating a constant a fixed number of times.

### Level 2 — Intermediate

```java
import java.util.stream.*;
import java.util.concurrent.ThreadLocalRandom;

public class GenerateRandomIds {
    public static void main(String[] args) {
        Stream.generate(() -> "user-" + ThreadLocalRandom.current().nextInt(1000, 9999))
                .limit(4)
                .forEach(System.out::println);
    }
}
```

**How to run:** `java GenerateRandomIds.java`

Expected output (values vary each run — this is randomness):
```
user-4821
user-2093
user-7765
user-1140
```

The real-world concern this adds: each call to the supplier now genuinely produces a *different*, unrelated value — a random ID — rather than a fixed constant. `ThreadLocalRandom.current()` is used instead of a shared `Random` instance because it's safe to call repeatedly without synchronization overhead, which matters since the supplier lambda is invoked once per generated element.

### Level 3 — Advanced

```java
import java.util.concurrent.atomic.AtomicInteger;
import java.util.stream.*;

public class GenerateSequentialIds {
    public static void main(String[] args) {
        AtomicInteger counter = new AtomicInteger(1000);

        // Stateful supplier: each call mutates shared state to produce a deterministic, unique value.
        Stream.generate(() -> "user-" + counter.getAndIncrement())
                .limit(4)
                .forEach(System.out::println);

        System.out.println("Next available id would be: user-" + counter.get());
    }
}
```

**How to run:** `java GenerateSequentialIds.java`

Expected output:
```
user-1000
user-1001
user-1002
user-1003
Next available id would be: user-1004
```

This adds a *stateful* supplier: `counter` is captured by the lambda and mutated (`getAndIncrement()`) on every call, so — unlike the purely random Level 2 — the output is now deterministic and reproducible across runs, while each element is still distinct. `AtomicInteger` is used (rather than a plain `int`) because it gives a safe, single atomic read-and-increment operation, which matters if this pattern were ever used with a parallel stream.

## 6. Walkthrough

Execution starts in `main` of the Level 3 example. `counter` is created holding `1000`.

`Stream.generate(() -> "user-" + counter.getAndIncrement())` sets up a lazy, infinite stream — no supplier calls happen yet, since streams are lazy until a terminal operation runs.

`.limit(4)` marks the stream to stop after four elements. `.forEach(System.out::println)` is the terminal operation that actually drives the pipeline.

On the first pull, the supplier lambda runs: `counter.getAndIncrement()` reads `1000` and atomically sets the counter to `1001`, so the lambda returns `"user-1000"`. `.forEach` prints it: `user-1000`.

On the second pull, the supplier runs again: `getAndIncrement()` reads `1001`, sets the counter to `1002`, returns `"user-1001"` — printed.

This repeats for the third pull (`counter` `1002 -> 1003`, prints `user-1002`) and the fourth pull (`counter` `1003 -> 1004`, prints `user-1003`). After the fourth element, `.limit(4)` stops the pipeline — the supplier is never called a fifth time.

```
call 1: counter 1000->1001, yields "user-1000" -> printed
call 2: counter 1001->1002, yields "user-1001" -> printed
call 3: counter 1002->1003, yields "user-1002" -> printed
call 4: counter 1003->1004, yields "user-1003" -> printed  [limit(4) reached, stream stops]
```

Finally, `System.out.println("Next available id would be: user-" + counter.get())` reads the counter's final value, `1004`, confirming exactly four increments happened — one per generated element, and no more.

## 7. Gotchas & takeaways

> `Stream.generate` is **infinite by design** — exactly like the two-argument `Stream.iterate`, forgetting `.limit(n)` (or another short-circuiting operation) means a terminal operation will never complete. There is no self-limiting overload for `Stream.generate` the way there is for `Stream.iterate`, so the limit must always be supplied explicitly.

- `Stream.generate(supplier)` produces elements by calling a zero-argument `Supplier<T>` repeatedly; each call is independent of the others.
- Unlike `Stream.iterate`, there's no built-in relationship between consecutive elements — the supplier decides everything, including whether to use shared/mutable state.
- Always pair it with `.limit(n)` (or another short-circuiting terminal operation) since it has no self-stopping form.
- A stateless supplier (a random-number generator, a constant) is the common case; a stateful supplier (an `AtomicInteger` counter) is used when you need deterministic, unique values instead of pure randomness.
- Prefer `ThreadLocalRandom.current()` over a shared `Random` instance inside a generator supplier to avoid contention if the stream is ever processed in parallel.
