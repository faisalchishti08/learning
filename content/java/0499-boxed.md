---
card: java
gi: 499
slug: boxed
title: boxed()
---

## 1. What it is

`.boxed()` converts a primitive stream (`IntStream`, `LongStream`, `DoubleStream`) into the corresponding object stream (`Stream<Integer>`, `Stream<Long>`, `Stream<Double>`), wrapping each primitive value in its boxed wrapper type. It's the counterpart to `mapToInt`/`mapToLong`/`mapToDouble` (see [[maptoint-maptolong-maptodouble-maptoobj]]), which go the other direction — from objects into primitives.

## 2. Why & when

Primitive streams are efficient but limited: they don't work with generic APIs that expect `Stream<T>`, `Collection<T>`, or `List<T>` — you can't pass an `IntStream` to a method expecting a `List<Integer>`, and you can't call `.collect(Collectors.toList())` directly on an `IntStream` (it has its own, more limited `.toArray()`/`.boxed().collect(...)` path instead). `.boxed()` is the bridge: once you've done your numeric work in the efficient primitive world (`sum`, `average`, `filter` on primitives), `.boxed()` converts the result into a `Stream<Integer>` so it can flow into generic collectors, `List<Integer>` results, or APIs that only understand object types.

You reach for `.boxed()` right before you need to collect primitive stream results into a standard Java collection, or pass them to a generic method that only accepts `Stream<T>`/`List<T>`.

## 3. Core concept

```java
import java.util.*;
import java.util.stream.*;

List<Integer> numbers = IntStream.rangeClosed(1, 5)
        .boxed() // IntStream -> Stream<Integer>
        .toList(); // [1, 2, 3, 4, 5] -- now a proper List<Integer>
```

`.boxed()` wraps each primitive `int`/`long`/`double` into its `Integer`/`Long`/`Double` object equivalent, one-to-one, turning a primitive stream into a plain object stream.

## 4. Diagram

<svg viewBox="0 0 640 120" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="boxed converts a primitive stream into a stream of the corresponding wrapper objects">
  <rect x="8" y="8" width="624" height="104" rx="8" fill="#0d1117"/>
  <rect x="40" y="30" width="130" height="40" rx="6" fill="#1c2430" stroke="#6db33f"/><text x="105" y="55" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">IntStream</text>
  <line x1="170" y1="50" x2="290" y2="50" stroke="#8b949e" stroke-width="2" marker-end="url(#arrowB)"/>
  <text x="230" y="40" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">.boxed()</text>
  <rect x="300" y="30" width="170" height="40" rx="6" fill="#1c2430" stroke="#79c0ff"/><text x="385" y="55" fill="#79c0ff" font-size="12" text-anchor="middle" font-family="sans-serif">Stream&lt;Integer&gt;</text>
  <defs><marker id="arrowB" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
  <text x="20" y="95" fill="#8b949e" font-size="10" font-family="sans-serif">Each primitive int is wrapped into an Integer object, one-to-one.</text>
</svg>

`.boxed()` takes a stream of raw `int` values and produces a stream of `Integer` objects — same values, wrapped.

## 5. Runnable example

Scenario: computing a set of prime numbers within a range and storing them for later use elsewhere in a program — evolved from a plain conversion into a `List<Integer>`, through feeding boxed results into a generic `Map`-building collector, to a version that uses boxed streams with a custom object type requiring full `Stream<T>` generics.

### Level 1 — Basic

```java
import java.util.*;
import java.util.stream.*;

public class BoxedBasic {
    public static void main(String[] args) {
        List<Integer> squares = IntStream.rangeClosed(1, 5)
                .map(n -> n * n)   // still an IntStream
                .boxed()           // now Stream<Integer>
                .toList();

        System.out.println("Squares: " + squares);
    }
}
```

**How to run:** `java BoxedBasic.java`

Expected output:
```
Squares: [1, 4, 9, 16, 25]
```

`IntStream.rangeClosed(1, 5).map(n -> n * n)` stays entirely in the primitive `IntStream` world, computing squares efficiently without boxing. `.boxed()` then converts the final `IntStream` of squares into a `Stream<Integer>`, which `.toList()` can collect into a proper `List<Integer>` — something `IntStream` alone cannot produce directly.

### Level 2 — Intermediate

```java
import java.util.*;
import java.util.stream.*;

public class BoxedToMap {
    public static void main(String[] args) {
        Map<Integer, Integer> numberToSquare = IntStream.rangeClosed(1, 5)
                .boxed() // need Stream<Integer> to use Collectors.toMap, a generic collector
                .collect(Collectors.toMap(n -> n, n -> n * n));

        System.out.println("Map: " + new TreeMap<>(numberToSquare)); // TreeMap just for sorted printing
    }
}
```

**How to run:** `java BoxedToMap.java`

Expected output:
```
Map: {1=1, 2=4, 3=9, 4=16, 5=25}
```

The real-world concern this adds: `Collectors.toMap(...)` is a generic collector that works on `Stream<T>`, not on `IntStream` directly. `.boxed()` bridges `IntStream.rangeClosed(1, 5)` into a `Stream<Integer>` first, so `.collect(Collectors.toMap(...))` — which needs object types for its key/value functions — becomes usable, building a lookup from each number to its square.

### Level 3 — Advanced

```java
import java.util.*;
import java.util.stream.*;

public class BoxedCustomObjects {
    record PrimeCandidate(int value, boolean isPrime) {}

    static boolean isPrime(int n) {
        if (n < 2) return false;
        for (int i = 2; (long) i * i <= n; i++) {
            if (n % i == 0) return false;
        }
        return true;
    }

    public static void main(String[] args) {
        List<PrimeCandidate> results = IntStream.rangeClosed(2, 20)
                .boxed() // need Stream<Integer> to map into a custom record type
                .map(n -> new PrimeCandidate(n, isPrime(n)))
                .toList();

        List<Integer> primes = results.stream()
                .filter(PrimeCandidate::isPrime)
                .map(PrimeCandidate::value)
                .toList();

        System.out.println("Primes from 2 to 20: " + primes);
    }
}
```

**How to run:** `java BoxedCustomObjects.java`

Expected output:
```
Primes from 2 to 20: [2, 3, 5, 7, 11, 13, 17, 19]
```

This adds a step further: not just boxing into `Integer`, but using the boxed `Stream<Integer>` as the entry point into `.map(...)` that builds a **custom object type** (`PrimeCandidate`) per number — something only possible once the stream has left the primitive `IntStream` world, since `IntStream.mapToObj(...)` could do this directly too, but `.boxed().map(...)` reads naturally here as "get plain integers, then turn each into a richer record."

## 6. Walkthrough

Execution starts in `main` of the Level 3 example. `IntStream.rangeClosed(2, 20)` (see [[intstream-range-rangeclosed]]) produces the primitive `int` sequence `2, 3, 4, ..., 20` — nineteen values, inclusive of both ends.

`.boxed()` converts each raw `int` into an `Integer` object: `2` becomes `Integer.valueOf(2)`, `3` becomes `Integer.valueOf(3)`, and so on — the stream is now a `Stream<Integer>` of the same nineteen values, just wrapped.

`.map(n -> new PrimeCandidate(n, isPrime(n)))` runs on each boxed `Integer`: for `n=2`, `isPrime(2)` checks the loop condition `i * i <= n` starting at `i=2` — `2*2=4 <= 2` is `false`, so the loop body never executes and `isPrime` returns `true` (no divisor found up to its square root) — producing `PrimeCandidate(2, true)`. For `n=4`, `isPrime(4)` checks `i=2`: `2*2=4 <= 4` true, `4 % 2 == 0` true, returns `false` — producing `PrimeCandidate(4, false)`. This continues for all nineteen values, building a `List<PrimeCandidate>` of both prime and non-prime entries.

```
n=2  -> isPrime: no divisor found -> true  -> PrimeCandidate(2, true)
n=3  -> isPrime: no divisor found -> true  -> PrimeCandidate(3, true)
n=4  -> isPrime: 4%2==0           -> false -> PrimeCandidate(4, false)
n=5  -> isPrime: no divisor found -> true  -> PrimeCandidate(5, true)
...  (continues through n=20)
```

`results.stream().filter(PrimeCandidate::isPrime)` then keeps only the entries where `isPrime` is `true` — `2, 3, 5, 7, 11, 13, 17, 19` — and `.map(PrimeCandidate::value)` extracts just their `int` values back out as a `Stream<Integer>`. `.toList()` collects the final result: `[2, 3, 5, 7, 11, 13, 17, 19]`, the eight primes between `2` and `20`.

## 7. Gotchas & takeaways

> `.boxed()` has a real cost: every primitive value is wrapped into a heap-allocated object. For very large streams where you only need numeric aggregation (`sum`, `average`, `max`), staying in the primitive stream (`IntStream`, etc.) and avoiding `.boxed()` entirely is significantly more efficient — only box when you genuinely need to interoperate with generic `Stream<T>`/`Collection<T>` APIs.

- `.boxed()` converts a primitive stream (`IntStream`/`LongStream`/`DoubleStream`) into the corresponding object stream (`Stream<Integer>`/`Stream<Long>`/`Stream<Double>`).
- It's the bridge needed before using generic collectors like `Collectors.toMap`, `Collectors.groupingBy`, or building a `List<Integer>` via `.toList()`.
- `IntStream.mapToObj(...)` can sometimes replace `.boxed().map(...)` in one step when the target isn't `Integer` itself but some other derived object.
- Avoid boxing unless you actually need object-stream APIs — primitive streams are more memory- and CPU-efficient for pure numeric work.
- The reverse bridge, converting objects back to primitives, is `mapToInt`/`mapToLong`/`mapToDouble` (see [[maptoint-maptolong-maptodouble-maptoobj]]).
