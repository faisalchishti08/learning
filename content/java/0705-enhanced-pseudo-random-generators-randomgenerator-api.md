---
card: java
gi: 705
slug: enhanced-pseudo-random-generators-randomgenerator-api
title: Enhanced pseudo-random generators (RandomGenerator API)
---

## 1. What it is

**Java 17** introduced the **`RandomGenerator`** interface (JEP 356), a new, unified API for pseudo-random number generation that sits above `java.util.Random`, `SecureRandom`, and `SplittableRandom`, and adds several new, modern **random number generation algorithms** the JDK ships out of the box. Before this, `java.util.Random` (from Java 1.0) was the base class nearly everything else extended, but it wasn't designed as an extensible interface, made assumptions that constrained newer algorithm families, and offered no uniform way to discover which algorithms were available or to create one by name. `RandomGenerator` fixes this: it's an interface (not tied to `Random`'s specific implementation), existing classes were retrofitted to implement it, and new algorithm implementations (like `Xoshiro256PlusPlus` and the `L64X128MixRandom` family) were added alongside it.

## 2. Why & when

`java.util.Random`'s internal algorithm (a 48-bit linear congruential generator) is fast and fine for casual use, but it has known statistical weaknesses for more demanding purposes: its period is relatively short, and its output has detectable structure that makes it unsuitable for Monte Carlo simulations, certain games, or scientific computing that needs a longer-period, more statistically robust generator. Rather than pick one "best" algorithm and force everyone onto it, JEP 356 defined a common interface so code can request a generator **by algorithm name** (`RandomGenerator.of("Xoshiro256PlusPlus")`) without needing to `new` a specific concrete class, and added interface refinements (`JumpableGenerator`, `SplittableGenerator`, `LeapableGenerator`) describing which capabilities a given algorithm supports for parallel and distributed use. Reach for `RandomGenerator.of(...)` instead of `new Random(...)` whenever you want a specific, named algorithm with well-documented statistical properties, or when writing generic code that shouldn't hard-code assumptions about which concrete random-number class it's using.

## 3. Core concept

```java
import java.util.random.RandomGenerator;

RandomGenerator rng = RandomGenerator.of("Xoshiro256PlusPlus");
int roll = rng.nextInt(1, 7);          // uniform int in [1, 7)
double sample = rng.nextDouble();       // uniform double in [0.0, 1.0)

rng.ints(5, 1, 101).forEach(System.out::println); // a stream of 5 random ints in [1, 101)
```

`RandomGenerator.of(algorithmName)` looks up and instantiates a named algorithm — the exact same interface (`nextInt`, `nextDouble`, `.ints()`, ...) works no matter which one you pick.

## 4. Diagram

<svg viewBox="0 0 640 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="RandomGenerator is an interface implemented by java.util.Random, SecureRandom, SplittableRandom, and new algorithm classes like Xoshiro256PlusPlus and L64X128MixRandom, all accessible through one common API">
  <rect x="220" y="15" width="200" height="40" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="40" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">RandomGenerator</text>

  <line x1="260" y1="55" x2="120" y2="110" stroke="#79c0ff" stroke-width="1.5"/>
  <line x1="300" y1="55" x2="260" y2="110" stroke="#79c0ff" stroke-width="1.5"/>
  <line x1="340" y1="55" x2="420" y2="110" stroke="#79c0ff" stroke-width="1.5"/>
  <line x1="380" y1="55" x2="540" y2="110" stroke="#79c0ff" stroke-width="1.5"/>

  <rect x="50" y="110" width="140" height="40" rx="6" fill="#161b22" stroke="#79c0ff"/>
  <text x="120" y="134" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">java.util.Random</text>

  <rect x="200" y="110" width="120" height="40" rx="6" fill="#161b22" stroke="#79c0ff"/>
  <text x="260" y="134" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">SecureRandom</text>

  <rect x="340" y="110" width="160" height="40" rx="6" fill="#161b22" stroke="#79c0ff"/>
  <text x="420" y="134" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">Xoshiro256PlusPlus</text>

  <rect x="460" y="110" width="160" height="40" rx="6" fill="#161b22" stroke="#79c0ff"/>
  <text x="540" y="134" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">L64X128MixRandom</text>

  <text x="320" y="185" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">All accessed uniformly via RandomGenerator.of("algorithm-name")</text>
</svg>

Old and new random-number algorithms alike are reachable through the same interface, chosen by algorithm name.

## 5. Runnable example

Scenario: a dice-rolling and sampling utility — first the basic use of a named algorithm to roll a die and sample doubles, then comparing several named algorithms side by side to show they share one interface despite different underlying algorithms, then a small statistical sanity check that generates a large sample and verifies its distribution roughly matches what uniform randomness should produce.

### Level 1 — Basic

```java
// File: DiceRollerBasic.java
import java.util.random.RandomGenerator;

public class DiceRollerBasic {
    public static void main(String[] args) {
        RandomGenerator rng = RandomGenerator.of("Xoshiro256PlusPlus");

        System.out.println("Algorithm: " + rng.getClass().getSimpleName());
        for (int roll = 1; roll <= 5; roll++) {
            int die = rng.nextInt(1, 7); // uniform int in [1, 7): a standard six-sided die
            System.out.println("Roll " + roll + ": " + die);
        }
    }
}
```

**How to run:**
```
java DiceRollerBasic.java
```

Expected output shape (values vary by run since no seed was fixed):
```
Algorithm: Xoshiro256PlusPlus
Roll 1: 4
Roll 2: 1
Roll 3: 6
Roll 4: 3
Roll 5: 5
```

### Level 2 — Intermediate

```java
// File: CompareAlgorithms.java
import java.util.random.RandomGenerator;

public class CompareAlgorithms {
    public static void main(String[] args) {
        String[] algorithms = { "Random", "Xoshiro256PlusPlus", "L64X128MixRandom" };

        for (String name : algorithms) {
            RandomGenerator rng = RandomGenerator.of(name);
            int[] rolls = rng.ints(5, 1, 7).toArray(); // 5 dice rolls in [1, 7)
            System.out.println(name + ": " + java.util.Arrays.toString(rolls));
        }
    }
}
```

**How to run:**
```
java CompareAlgorithms.java
```

Expected output shape (each algorithm produces different-looking output through the exact same calling code):
```
Random: [2, 6, 1, 4, 3]
Xoshiro256PlusPlus: [5, 1, 6, 2, 4]
L64X128MixRandom: [3, 3, 6, 1, 5]
```

Every algorithm is reached through the identical `RandomGenerator.of(name)` and `.ints(count, origin, bound)` calls — swapping the algorithm name is the only change needed to try a different generator, with no code depending on any algorithm-specific class.

### Level 3 — Advanced

```java
// File: DistributionSanityCheck.java
import java.util.random.RandomGenerator;
import java.util.HashMap;
import java.util.Map;

public class DistributionSanityCheck {
    public static void main(String[] args) {
        RandomGenerator rng = RandomGenerator.of("Xoshiro256PlusPlus");
        int sampleSize = 60_000;
        int sides = 6;

        Map<Integer, Integer> counts = new HashMap<>();
        rng.ints(sampleSize, 1, sides + 1).forEach(roll -> counts.merge(roll, 1, Integer::sum));

        double expectedPerFace = (double) sampleSize / sides;
        System.out.println("Sample size: " + sampleSize + ", expected per face: " + expectedPerFace);

        boolean allWithinTolerance = true;
        for (int face = 1; face <= sides; face++) {
            int actual = counts.getOrDefault(face, 0);
            double deviationPct = 100.0 * Math.abs(actual - expectedPerFace) / expectedPerFace;
            boolean withinTolerance = deviationPct < 5.0; // generous tolerance for a demo
            allWithinTolerance &= withinTolerance;
            System.out.printf("Face %d: %d rolls (%.1f%% deviation) %s%n",
                    face, actual, deviationPct, withinTolerance ? "OK" : "SUSPICIOUS");
        }
        System.out.println(allWithinTolerance
                ? "Distribution looks uniform, as expected."
                : "Distribution deviates more than expected — investigate.");
    }
}
```

**How to run:**
```
java DistributionSanityCheck.java
```

Expected output shape (a well-behaved generator keeps every face within a few percent of the expected count):
```
Sample size: 60000, expected per face: 10000.0
Face 1: 10042 rolls (0.4% deviation) OK
Face 2: 9978 rolls (0.2% deviation) OK
Face 3: 10015 rolls (0.1% deviation) OK
Face 4: 9931 rolls (0.7% deviation) OK
Face 5: 10061 rolls (0.6% deviation) OK
Face 6: 9973 rolls (0.3% deviation) OK
Distribution looks uniform, as expected.
```

## 6. Walkthrough

1. `DistributionSanityCheck.main` creates one `RandomGenerator` via `RandomGenerator.of("Xoshiro256PlusPlus")` and generates `60_000` simulated die rolls in a single call: `rng.ints(sampleSize, 1, sides + 1)` returns an `IntStream` of exactly `sampleSize` uniformly distributed integers in `[1, sides]`.
2. `.forEach(roll -> counts.merge(roll, 1, Integer::sum))` tallies how many times each face (1 through 6) appeared, using `Map.merge` to either insert a fresh count of `1` for a face seen for the first time, or add `1` to its existing count.
3. `expectedPerFace` is the theoretical expectation under perfect uniformity: `60,000 / 6 = 10,000` rolls per face.
4. The loop over `face` from `1` to `6` computes each face's actual count, the percentage deviation from the expected count, and flags any face whose deviation exceeds a generous 5% tolerance (chosen loosely for a demonstration; real statistical testing would use a proper chi-squared test rather than an ad-hoc percentage threshold).
5. `allWithinTolerance` accumulates whether every single face stayed within tolerance; the final message reports whether the whole distribution looked uniform, which for any correctly implemented `RandomGenerator` algorithm over 60,000 samples should essentially always be `true` — a large sample size is what keeps random sampling noise well below the 5% tolerance band.
6. This is the practical value of the algorithm being swappable at Level 2: the exact same distribution check could be re-run against `"L64X128MixRandom"` or any other algorithm name with a one-line change, letting you empirically compare different generators' statistical behavior without rewriting any calling code.

```
RandomGenerator.of("Xoshiro256PlusPlus")
        .ints(60000, 1, 7)            -> stream of 60,000 rolls in [1,6]
              │
        tally counts per face (HashMap.merge)
              │
        compare each face's count to expected (10,000) within 5% tolerance
              │
        print per-face report + overall verdict
```

## 7. Gotchas & takeaways

> `RandomGenerator.of(...)` is **not cryptographically secure** for any of the general-purpose algorithms shown here (`Random`, `Xoshiro256PlusPlus`, `L64X128MixRandom`) — for security-sensitive randomness (tokens, keys, nonces), use `RandomGenerator.of("SecureRandom")` or `java.security.SecureRandom` directly, never a fast statistical generator chosen for simulation quality.
- `RandomGenerator` is an **interface**, not a class — existing types like `java.util.Random`, `SecureRandom`, and `SplittableRandom` were retrofitted to implement it, so existing code that already uses `new Random()` can be gradually migrated to the interface type without discarding it.
- `RandomGenerator.of(algorithmName)` throws if the name doesn't match a registered algorithm — algorithm names are matched by exact string, and the full list of built-in algorithms is discoverable via `RandomGeneratorFactory.all()`, covered in [RandomGeneratorFactory](0706-randomgeneratorfactory.md).
- Different algorithms have different trade-offs (period length, statistical quality, speed, memory footprint, and support for parallel-safe splitting/jumping) — picking one isn't purely a style choice, and the JDK's documentation for each named algorithm class describes its specific properties.
- A single-percentage-deviation check (as used here) is a useful smoke test, not a rigorous randomness certification — real statistical validation of a PRNG uses dedicated test suites (like TestU01 or dieharder), not ad-hoc tolerance bands.
- Because `.ints()`, `.longs()`, and `.doubles()` return standard `Stream` types, all of `java.util.stream`'s operations (filtering, mapping, collecting) work directly on generated random values without any extra glue code.
