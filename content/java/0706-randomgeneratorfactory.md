---
card: java
gi: 706
slug: randomgeneratorfactory
title: RandomGeneratorFactory
---

## 1. What it is

**`RandomGeneratorFactory<T>`**, added alongside [`RandomGenerator`](0705-enhanced-pseudo-random-generators-randomgenerator-api.md) in **Java 17** (JEP 356), is the API for **discovering, describing, and creating** pseudo-random generator algorithms programmatically. Where `RandomGenerator.of("name")` is a one-shot convenience method, `RandomGeneratorFactory` is the underlying machinery: `RandomGeneratorFactory.all()` streams every algorithm the current JDK registers, `RandomGeneratorFactory.of("name")` returns a reusable factory object for one specific algorithm, and that factory can then stamp out any number of independent generator instances via `.create()` — with or without an explicit seed — or produce a `Stream<RandomGenerator>` of many independent generators at once via `.generators(streamSize)`.

## 2. Why & when

Sometimes you don't want just one random generator — you want to know *what algorithms exist* on this JVM (useful for logging, diagnostics, or letting an application pick the "best" available algorithm for its needs), or you want *many independent generators*, one per worker thread in a parallel simulation, each statistically independent of the others rather than all threads contending over a single shared instance. `RandomGeneratorFactory` supports both: `.all()` gives you every registered algorithm's metadata (name, period length in bits, whether it supports splitting/jumping) so code can select algorithmically rather than hard-coding a name, and `.generators(n)` gives you `n` separate `RandomGenerator` instances in one call, ready to hand out one per thread or one per parallel task. Reach for the factory API specifically when you need to enumerate available algorithms, filter them by a required capability (like being splittable for safe parallel use), or mass-produce multiple independent generator instances.

## 3. Core concept

```java
import java.util.random.RandomGeneratorFactory;

// List every algorithm the JVM knows about
RandomGeneratorFactory.all().forEach(f -> System.out.println(f.name() + " (bits: " + f.stateBits() + ")"));

// Get a reusable factory for one specific algorithm, then create several independent generators
RandomGeneratorFactory<?> factory = RandomGeneratorFactory.of("L64X128MixRandom");
factory.generators(4).forEach(gen -> System.out.println(gen.nextInt(100)));
```

`.all()` enumerates every registered algorithm; `.of(name)` gives a reusable factory that can stamp out as many independent generator instances as needed.

## 4. Diagram

<svg viewBox="0 0 640 210" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="RandomGeneratorFactory.of(name) creates a reusable factory, which can create one generator via create() or many independent generators at once via generators(n)">
  <rect x="20" y="20" width="220" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="130" y="42" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">RandomGeneratorFactory</text>
  <text x="130" y="58" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">.of("L64X128MixRandom")</text>

  <line x1="240" y1="45" x2="330" y2="45" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="285" y="35" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">.create()</text>

  <rect x="330" y="20" width="140" height="50" rx="6" fill="#161b22" stroke="#79c0ff"/>
  <text x="400" y="50" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">1 generator</text>

  <line x1="130" y1="70" x2="130" y2="110" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="185" y="95" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">.generators(4)</text>

  <rect x="30" y="110" width="90" height="35" rx="5" fill="#161b22" stroke="#79c0ff"/>
  <text x="75" y="132" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">gen #1</text>
  <rect x="130" y="110" width="90" height="35" rx="5" fill="#161b22" stroke="#79c0ff"/>
  <text x="175" y="132" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">gen #2</text>
  <rect x="230" y="110" width="90" height="35" rx="5" fill="#161b22" stroke="#79c0ff"/>
  <text x="275" y="132" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">gen #3</text>
  <rect x="330" y="110" width="90" height="35" rx="5" fill="#161b22" stroke="#79c0ff"/>
  <text x="375" y="132" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">gen #4</text>
  <text x="225" y="170" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">4 statistically independent generators, one factory</text>
</svg>

One factory, created once per algorithm name, can stamp out either a single generator or a whole batch of independent ones.

## 5. Runnable example

Scenario: a parallel Monte Carlo–style simulation setup — first listing available algorithms to pick a suitable one, then creating several independent generators from one factory to hand out to separate worker tasks, then a small parallel-stream simulation that uses those independent generators to estimate π via random sampling, demonstrating why independent (not shared) generators matter for correct parallel randomness.

### Level 1 — Basic

```java
// File: ListAlgorithms.java
import java.util.random.RandomGeneratorFactory;

public class ListAlgorithms {
    public static void main(String[] args) {
        RandomGeneratorFactory.all()
                .sorted(java.util.Comparator.comparing(RandomGeneratorFactory::name))
                .forEach(f -> System.out.println(f.name() + " (state bits: " + f.stateBits() + ")"));
    }
}
```

**How to run:**
```
java ListAlgorithms.java
```

Expected output shape (the exact list depends on the JDK build; several dozen algorithm families are typically registered):
```
L128X1024MixRandom (state bits: 1152)
L128X128MixRandom (state bits: 256)
L64X128MixRandom (state bits: 192)
Random (state bits: 48)
SecureRandom (state bits: 0)
Xoshiro256PlusPlus (state bits: 256)
...
```

### Level 2 — Intermediate

```java
// File: IndependentGenerators.java
import java.util.List;
import java.util.random.RandomGenerator;
import java.util.random.RandomGeneratorFactory;

public class IndependentGenerators {
    public static void main(String[] args) {
        RandomGeneratorFactory<RandomGenerator> factory = RandomGeneratorFactory.of("L64X128MixRandom");

        List<RandomGenerator> workers = factory.generators(4).toList();

        for (int i = 0; i < workers.size(); i++) {
            RandomGenerator worker = workers.get(i);
            System.out.println("Worker " + i + " first roll: " + worker.nextInt(1, 7));
        }
    }
}
```

**How to run:**
```
java IndependentGenerators.java
```

Expected output shape (each worker's generator is independently seeded, so their sequences differ):
```
Worker 0 first roll: 3
Worker 1 first roll: 6
Worker 2 first roll: 1
Worker 3 first roll: 4
```

### Level 3 — Advanced

```java
// File: ParallelPiEstimate.java
import java.util.List;
import java.util.random.RandomGenerator;
import java.util.random.RandomGeneratorFactory;
import java.util.stream.IntStream;

public class ParallelPiEstimate {
    static long countPointsInCircle(RandomGenerator rng, int samples) {
        long inside = 0;
        for (int i = 0; i < samples; i++) {
            double x = rng.nextDouble(-1.0, 1.0);
            double y = rng.nextDouble(-1.0, 1.0);
            if (x * x + y * y <= 1.0) inside++;
        }
        return inside;
    }

    public static void main(String[] args) {
        RandomGeneratorFactory<RandomGenerator> factory = RandomGeneratorFactory.of("L64X128MixRandom");
        int workerCount = 4;
        int samplesPerWorker = 250_000;

        List<RandomGenerator> workers = factory.generators(workerCount).toList();

        long totalInside = IntStream.range(0, workerCount)
                .parallel()
                .mapToLong(i -> countPointsInCircle(workers.get(i), samplesPerWorker))
                .sum();

        long totalSamples = (long) workerCount * samplesPerWorker;
        double piEstimate = 4.0 * totalInside / totalSamples;

        System.out.println("Total samples: " + totalSamples);
        System.out.println("Estimated pi:  " + piEstimate);
        System.out.println("Actual pi:     " + Math.PI);
    }
}
```

**How to run:**
```
java ParallelPiEstimate.java
```

Expected output shape (a Monte Carlo estimate converges toward pi as sample count grows, with small random variation between runs):
```
Total samples: 1000000
Estimated pi:  3.141548
Actual pi:     3.141592653589793
```

## 6. Walkthrough

1. `ParallelPiEstimate.main` gets one `RandomGeneratorFactory` for `"L64X128MixRandom"` and calls `.generators(4)` **once**, producing exactly four separate `RandomGenerator` instances — each with its own independent internal state, not four references to the same shared instance.
2. `IntStream.range(0, workerCount).parallel()` runs the four `countPointsInCircle` calls concurrently across the common fork-join pool, one per worker index; because each index maps to its *own* generator from `workers`, no two parallel tasks ever touch the same mutable generator state, avoiding both race conditions and the subtle statistical correlation that would occur if all threads shared one instance.
3. `countPointsInCircle` implements a classic Monte Carlo pi-estimation: for each of `samplesPerWorker` iterations, it samples a random point `(x, y)` uniformly in the square `[-1, 1] × [-1, 1]` via `rng.nextDouble(-1.0, 1.0)`, and checks whether that point falls inside the unit circle (`x² + y² <= 1`).
4. Since the circle's area is `π` and the square's area is `4`, the fraction of sampled points landing inside the circle approximates `π / 4` — so multiplying that fraction by `4` estimates `π` itself; more samples make the estimate converge closer to the true value.
5. `.mapToLong(...).sum()` aggregates each worker's inside-count into `totalInside`, and the final estimate divides that by the combined `totalSamples` across all four workers, then multiplies by `4.0`, printing the result alongside `Math.PI` for comparison.
6. The independence of the four generators (guaranteed by requesting them together via `factory.generators(workerCount)`, rather than four separately-constructed instances that might, in principle, be seeded identically or predictably) is what makes the parallel sampling statistically sound — each worker explores a genuinely distinct portion of the random sample space.

```
factory.generators(4)  -> [gen0, gen1, gen2, gen3]   (independent state each)
                                │
IntStream.range(0,4).parallel().mapToLong(i -> countPointsInCircle(gen[i], 250_000))
                                │
        sum four workers' inside-counts -> totalInside
                                │
        piEstimate = 4 * totalInside / totalSamples
```

## 7. Gotchas & takeaways

> `factory.generators(n)` guarantees the *n* generators it returns are suitable for **independent, concurrent use** — but this guarantee depends on choosing an algorithm designed for it (like the `L*X*MixRandom` family, built on `SplittableGenerator`). Not every algorithm registered via `RandomGeneratorFactory.all()` supports this; check `factory.isSplittable()` (or the corresponding capability method) before relying on parallel independence for an arbitrary algorithm name.
- `RandomGeneratorFactory.all()` returns a `Stream<RandomGeneratorFactory<RandomGenerator>>` describing every algorithm the JVM has registered — useful for diagnostics, logging which algorithm an application picked, or filtering by required properties like state size.
- Prefer `factory.generators(n)` over manually calling `factory.create()` in a loop when you need multiple generators for concurrent use — `.generators(n)` is specifically designed to produce statistically independent instances suitable for that purpose, which repeatedly calling `.create()` with no seed does not strictly guarantee for every algorithm family.
- `RandomGeneratorFactory.of("SecureRandom")` and similar cryptographic algorithms exist in the same enumeration as fast statistical generators — always check an algorithm's intended purpose (statistical simulation vs. cryptographic security) before picking one from `.all()` by name alone.
- See [Enhanced pseudo-random generators (RandomGenerator API)](0705-enhanced-pseudo-random-generators-randomgenerator-api.md) for the simpler, one-shot `RandomGenerator.of(name)` entry point this factory API sits underneath.
- Monte Carlo estimates like the pi-approximation above converge slowly (error shrinks roughly with the square root of sample count) — don't mistake a single run's proximity to the true value for a guarantee; rerunning the same program produces a slightly different estimate each time.
