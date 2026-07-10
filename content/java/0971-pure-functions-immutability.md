---
card: java
gi: 971
slug: pure-functions-immutability
title: Pure functions & immutability
---

## 1. What it is

A pure function is one whose output depends *only* on its input arguments, with no reliance on or modification of any external, mutable state — calling it twice with the same arguments always produces the same result, and calling it produces no observable side effect (no field mutation, no I/O, no changing a shared collection) beyond returning its value. Immutability is the closely related, supporting property that an object, once constructed, can never have its observable state changed — every field effectively final, with no setter and no mutating method. These two ideas reinforce each other directly: a function operating only on immutable data structures has a much easier time staying pure, since there's no mutable shared state left for it to accidentally read from or write to, and Java's own [records](0954-record-components-canonical-constructor.md), `List.of`/`Map.of`, and the `Stream` API's design all lean specifically into this combination.

## 2. Why & when

Pure functions and immutable data matter most anywhere correctness under concurrency or reasoning-about-code-in-isolation is valuable: a pure function is inherently thread-safe with zero synchronization needed (since there's no shared mutable state to race over), trivially testable (no setup of external state, no mocking required — just call it with inputs and check the output), and safely cacheable or memoizable (since the same input always yields the same output). Java's `Stream` API is explicitly designed around this discipline — the lambda passed to `map`, `filter`, or `reduce` is expected to be a pure, stateless function specifically because streams may execute those lambdas in parallel or in an unspecified order, and a lambda that mutates shared state or depends on external mutable state can produce genuinely incorrect, non-deterministic results under those conditions, a subtlety examined directly in the advanced example below. It's not that impure functions or mutable state are always wrong — a program ultimately needs *some* mutation and I/O to do anything useful — but confining that impurity to as small and explicit a surface as possible, and keeping the bulk of your logic pure and operating over immutable data, produces code that is dramatically easier to test, parallelize, and reason about correctly.

## 3. Core concept

```
// IMPURE: depends on and mutates external state
int total = 0;
void addToTotal(int x) {
    total += x;   // reads AND writes external mutable state -- not pure
}

// PURE: same inputs ALWAYS produce the same output, no external state touched
int add(int a, int b) {
    return a + b;   // depends ONLY on its arguments, mutates nothing
}

// IMMUTABLE data + PURE function together:
record Point(int x, int y) {}
Point translate(Point p, int dx, int dy) {
    return new Point(p.x() + dx, p.y() + dy);   // returns a NEW Point -- never mutates p
}
```

Purity and immutability compound: a pure function operating on immutable data has no mutable state anywhere in the picture to accidentally race, mutate unexpectedly, or reason incorrectly about — every call is a self-contained, independently-verifiable computation.

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="An impure function reading and writing shared mutable state, contrasted with a pure function that only reads its arguments and returns a new value with no external state touched" >
  <rect x="20" y="30" width="280" height="90" fill="#1c2430" stroke="#f0883e"/>
  <text x="160" y="48" fill="#f0883e" font-size="10" text-anchor="middle" font-family="sans-serif">Impure: addToTotal(x)</text>
  <text x="160" y="70" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">reads shared 'total'</text>
  <text x="160" y="85" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">WRITES shared 'total'</text>
  <text x="160" y="105" fill="#f0883e" font-size="8" text-anchor="middle" font-family="sans-serif">result depends on call HISTORY</text>

  <rect x="340" y="30" width="280" height="90" fill="#1c2430" stroke="#6db33f"/>
  <text x="480" y="48" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">Pure: add(a, b)</text>
  <text x="480" y="70" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">reads ONLY a, b</text>
  <text x="480" y="85" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">touches NOTHING external</text>
  <text x="480" y="105" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">result depends ONLY on a, b</text>
</svg>

*A pure function's result depends only on its arguments; an impure function's result can depend on hidden, external, mutable state.*

## 5. Runnable example

Scenario: compute running statistics over a data stream, evolving from a basic impure, mutable-accumulator version, to a pure, immutable-record-based version, to a more advanced case demonstrating exactly why purity matters once parallel streams enter the picture.

### Level 1 — Basic

```java
import java.util.*;

public class PureFunctionsImpureBaseline {
    static int total = 0; // SHARED, mutable state

    static void addToTotal(int x) {
        total += x; // IMPURE: mutates external state, no return value even needed
    }

    public static void main(String[] args) {
        List<Integer> values = List.of(1, 2, 3, 4, 5);
        for (int v : values) {
            addToTotal(v);
        }
        System.out.println("total: " + total);
    }
}
```

**How to run:** `java PureFunctionsImpureBaseline.java` (JDK 17+).

Expected output:
```
total: 15
```

`addToTotal` is impure: it depends on and mutates the shared `total` field rather than taking all its needed state as arguments and returning a new value — calling it twice with the same argument produces *different* results each time (since `total` keeps accumulating), which is the defining symptom of impurity.

### Level 2 — Intermediate

```java
import java.util.*;

public class PureFunctionsPureVersion {
    static int add(int a, int b) {
        return a + b; // PURE: same inputs always produce the same output, nothing external touched
    }

    public static void main(String[] args) {
        List<Integer> values = List.of(1, 2, 3, 4, 5);
        int total = values.stream().reduce(0, PureFunctionsPureVersion::add);
        System.out.println("total: " + total);

        // Demonstrating purity directly: calling add with the same arguments
        // ALWAYS gives the same result, regardless of how many times or in what order:
        System.out.println(add(3, 4));
        System.out.println(add(3, 4));
        System.out.println(add(3, 4));
    }
}
```

**How to run:** `java PureFunctionsPureVersion.java` (JDK 17+).

Expected output:
```
total: 15
7
7
7
```

The real-world concern added: `add` is genuinely pure — `add(3, 4)` returns `7` every single time, in any order, with no dependency on prior calls — and `Stream.reduce` is built specifically around combining values with a pure, associative function like this one; the total is computed by repeatedly combining the running accumulator with each new value, with no shared mutable field anywhere in the computation.

### Level 3 — Advanced

```java
import java.util.*;
import java.util.stream.*;
import java.util.concurrent.atomic.*;

public class PureFunctionsParallelPitfall {
    public static void main(String[] args) {
        List<Integer> values = IntStream.rangeClosed(1, 100_000).boxed().toList();

        // IMPURE approach: mutating shared state from within a parallel stream's lambda.
        // This is a well-known correctness bug -- NOT just a style preference.
        int[] impureTotal = {0}; // a 1-element array used to fake a "mutable capture"
        values.parallelStream().forEach(v -> impureTotal[0] += v); // RACE CONDITION
        System.out.println("impure parallel total (WRONG, non-deterministic): " + impureTotal[0]);

        // PURE approach: reduce with a pure, associative combining function --
        // safe under parallel execution, because there is no shared mutable state at all.
        int pureTotal = values.parallelStream().reduce(0, Integer::sum);
        System.out.println("pure parallel total (correct, always 5000050000... truncated to int): " + pureTotal);
    }
}
```

**How to run:** `java PureFunctionsParallelPitfall.java` (JDK 17+; run it several times to observe the impure version's result vary).

Expected output shape (illustrative — the impure total will likely be wrong and may vary between runs):
```
impure parallel total (WRONG, non-deterministic): 4998231  (or some other WRONG, possibly different, number each run)
pure parallel total (correct, always 5000050000... truncated to int): 705082704
```

The production-flavored hard case: `values.parallelStream().forEach(v -> impureTotal[0] += v)` runs the lambda concurrently across multiple threads, and `+=` on the shared array element is not atomic — multiple threads can read the same current value, add their own contribution, and write back, silently overwriting each other's updates (a classic race condition), producing a wrong and non-reproducible total; `reduce(0, Integer::sum)`, by contrast, uses a pure, associative combining function with no shared mutable state whatsoever, so the parallel stream can safely split the work across threads and combine partial results correctly, producing the exact same, correct total every single time, regardless of how many threads are involved or how the work happens to be split.

## 6. Walkthrough

Tracing why `values.parallelStream().forEach(v -> impureTotal[0] += v)` produces an incorrect, non-deterministic result:

1. `parallelStream()` splits the 100,000-element list into multiple chunks, distributing them across several threads (typically as many as the common `ForkJoinPool`'s parallelism level, often matching available CPU cores) to process concurrently — this is the entire point of a parallel stream: doing the per-element work simultaneously rather than sequentially.
2. Each thread, processing its own chunk, executes the lambda `v -> impureTotal[0] += v` for each of its assigned elements — but `impureTotal[0] += v` is not one atomic operation; it actually expands to three separate steps: read the current value of `impureTotal[0]`, add `v` to it, and write the new sum back into `impureTotal[0]`.
3. Because multiple threads are executing these three steps concurrently against the *same* shared array element, a race condition is possible: Thread A reads `impureTotal[0]` as, say, `1000`; before Thread A writes back its updated value, Thread B also reads `impureTotal[0]` as `1000` (not yet aware of Thread A's pending update); both threads then compute and write back their own updated sums, but whichever writes second simply overwrites the first thread's update entirely, silently discarding one thread's contribution to the total.
4. This lost-update pattern can happen an unpredictable number of times across the full run, depending on the exact, non-deterministic timing of how threads happen to interleave — which is precisely why the resulting `impureTotal[0]` is both *wrong* (some contributions were silently lost) and *non-deterministic* (a different, unpredictable number of updates may be lost on each separate run of the program).
5. `values.parallelStream().reduce(0, Integer::sum)`, by contrast, works fundamentally differently under the hood: because `Integer::sum` is pure (its result depends only on its two arguments, and it touches no shared state), the stream framework can safely compute independent partial sums for each chunk *in complete isolation*, on separate threads, with genuinely no shared mutable state for any two threads to race over.
6. Once every chunk's partial sum is computed independently, the framework combines those partial results — again using the same pure `Integer::sum` function — into the final total; because every step in this entire process only ever combines values via a pure function, with no shared mutable state read or written concurrently by multiple threads, the final result is both correct and perfectly reproducible, regardless of how the work happened to be split or interleaved across threads.

## 7. Gotchas & takeaways

> **Gotcha:** the compile-time restriction that a lambda can only capture "effectively final" local variables (see [capturing variables & effectively final](0463-capturing-variables-effectively-final.md)) is specifically designed to nudge you away from exactly the impure, mutable-capture pattern shown in the array-hack above — using a single-element array to work around that restriction (as the deliberately-broken example does) is a well-known but genuinely unsafe anti-pattern under parallel execution; if you ever find yourself reaching for that trick to make a lambda "mutate" something, that's usually a strong signal to restructure the logic around `reduce`, `collect`, or another built-in, pure-function-oriented stream operation instead.

- A pure function's output depends only on its arguments, with no reliance on or mutation of external state — calling it repeatedly with the same inputs always produces the same result, with no observable side effects.
- Immutability (data that cannot be changed after construction) and purity reinforce each other: pure functions operating over immutable data leave no shared mutable state anywhere for concurrent code to race over or reason incorrectly about.
- Java's `Stream` API is explicitly designed around this discipline — lambdas passed to `map`, `filter`, and especially `reduce` are expected to be pure, since streams may execute them in parallel or in an unspecified order.
- Mutating shared state from within a parallel stream's lambda is a genuine, well-documented correctness bug (a race condition), not just a style concern — it can silently produce wrong, non-reproducible results.
- `reduce` and similar built-in stream operations, used with a genuinely pure combining function, let the stream framework safely parallelize work with no shared mutable state and therefore no race conditions at all.
- See [higher-order functions](0973-higher-order-functions.md) for how pure functions compose as first-class values passed to and returned from other functions, and [function composition & currying](0972-function-composition-currying.md) for building larger pure functions out of smaller ones.
