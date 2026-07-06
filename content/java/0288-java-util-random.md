---
card: java
gi: 288
slug: java-util-random
title: java.util.Random
---

## 1. What it is

`java.util.Random` is a class for generating streams of pseudo-random numbers, offering far more control than the simple `Math.random()` covered earlier: methods for random `int`, `long`, `double`, `boolean`, and `float` values, plus bounded random integers within a specific range. Critically, a `Random` instance can be constructed with an explicit numeric "seed," which makes its entire sequence of "random" values completely deterministic and reproducible — the same seed always produces the exact same sequence.

```java
import java.util.Random;

public class RandomDemo {
    public static void main(String[] args) {
        Random random = new Random(); // seeded from a system-provided source, unpredictable each run

        System.out.println(random.nextInt());        // any int value
        System.out.println(random.nextInt(100));       // an int from 0 (inclusive) to 100 (exclusive)
        System.out.println(random.nextDouble());        // a double from 0.0 (inclusive) to 1.0 (exclusive)
        System.out.println(random.nextBoolean());        // true or false

        Random seeded = new Random(42); // FIXED seed: reproducible sequence
        System.out.println(seeded.nextInt(100)); // same value EVERY time this program runs
    }
}
```

`new Random()` (no arguments) seeds itself unpredictably, so its output differs each time the program runs; `new Random(42)` uses a fixed seed, guaranteeing the exact same sequence of "random" values on every single run — this reproducibility is precisely what makes seeded `Random` instances valuable for testing.

## 2. Why & when

`Random` provides fine-grained control over pseudo-random number generation, and its seeding capability solves a genuinely important problem: making randomized code testable and reproducible.

- **Bounded random values without manual arithmetic** — `nextInt(bound)` directly returns a value in `[0, bound)`, saving you from manually computing `(int) (Math.random() * bound)` (which, done incorrectly, can introduce subtle bias) — `Random`'s bounded methods handle this correctly and are the preferred approach whenever you need a random value within a specific range.
- **Reproducible sequences for testing** — a test that needs deterministic, repeatable "random" behavior (say, testing that a shuffling algorithm behaves correctly) can seed a `Random` instance with a fixed value, guaranteeing the exact same sequence every time the test runs — essential for reliable, non-flaky automated tests involving randomness.
- **Multiple independent random number types** — beyond `nextInt`, `Random` provides `nextLong`, `nextDouble`, `nextFloat`, `nextBoolean`, and `nextGaussian` (a normally-distributed random value), covering the common needs for randomized values of different types and distributions.

Use an unseeded `new Random()` (or `Math.random()`, for simple cases) for genuine, unpredictable randomness in production code (simulations, games, generating random identifiers where predictability would be undesirable); use a seeded `Random` instance specifically in tests or any situation where reproducible, deterministic "randomness" is required for verification purposes.

## 3. Core concept

```java
import java.util.Random;

public class RandomCore {
    static int rollDie(Random random) {
        return random.nextInt(6) + 1; // nextInt(6) gives 0-5, so +1 shifts it to the conventional 1-6 die range
    }

    public static void main(String[] args) {
        Random random = new Random(1); // fixed seed for reproducible demonstration
        for (int i = 0; i < 5; i++) {
            System.out.println("Roll " + (i + 1) + ": " + rollDie(random));
        }
    }
}
```

`random.nextInt(6)` returns a value in `[0, 6)` — that is, `0` through `5` inclusive — and adding `1` shifts this range to the conventional `1` through `6` a physical six-sided die produces; using a fixed seed (`1`) here means this exact program, run repeatedly, always produces the identical sequence of five "dice rolls," which is precisely the reproducibility that makes seeded `Random` so valuable for demonstrations and tests.

## 4. Diagram

<svg viewBox="0 0 600 160" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="An unseeded Random produces a different unpredictable sequence every program run, a Random seeded with a fixed number produces the identical reproducible sequence every single run">
  <rect x="8" y="8" width="584" height="144" rx="8" fill="#0d1117"/>

  <rect x="40" y="20" width="240" height="50" rx="6" fill="#1c2430" stroke="#f85149" stroke-width="1.5"/>
  <text x="160" y="42" fill="#f85149" font-size="9" text-anchor="middle" font-family="monospace">new Random()</text>
  <text x="160" y="58" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">different sequence every run</text>

  <rect x="330" y="20" width="240" height="50" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="450" y="42" fill="#6db33f" font-size="9" text-anchor="middle" font-family="monospace">new Random(42)</text>
  <text x="450" y="58" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">IDENTICAL sequence every run</text>

  <text x="300" y="110" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Same seed, same algorithm -&gt; always the exact same sequence of "random" values.</text>
  <text x="300" y="130" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">This reproducibility is exactly what makes seeded Random valuable for tests.</text>
</svg>

An unseeded `Random` is unpredictable across runs; a seeded one is perfectly reproducible.

## 5. Runnable example

Scenario: a small card-shuffling and dice-rolling utility, evolved from basic bounded randomness into a reproducible test scenario using a fixed seed, then hardened with a demonstration of exactly why seeding matters for verifiable, repeatable test assertions.

### Level 1 — Basic

```java
import java.util.Random;

public class RandomBasic {
    public static void main(String[] args) {
        Random random = new Random();
        int roll = random.nextInt(6) + 1; // 1 through 6
        System.out.println("You rolled: " + roll);
    }
}
```

**How to run:** `java RandomBasic.java`

Each run of this program produces a different result (since `new Random()` is seeded unpredictably) — genuine randomness, appropriate for an actual game or simulation.

### Level 2 — Intermediate

Same dice-rolling idea, now shuffling a small deck of cards using `Collections.shuffle` with an explicit `Random` instance, demonstrating a seeded shuffle producing a reproducible order.

```java
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Random;

public class RandomIntermediate {
    public static void main(String[] args) {
        List<String> deck = new ArrayList<>(List.of("Ace", "King", "Queen", "Jack", "10"));

        Random seededRandom = new Random(7); // fixed seed
        Collections.shuffle(deck, seededRandom);

        System.out.println("Shuffled deck: " + deck); // identical order every time this exact code runs
    }
}
```

**How to run:** `java RandomIntermediate.java` (run it multiple times — the output is always identical)

`Collections.shuffle(deck, seededRandom)` uses the provided `Random` instance's sequence to determine the shuffle order — because `seededRandom` was constructed with the fixed seed `7`, this exact shuffle order is completely reproducible across every single run of the program, unlike calling `Collections.shuffle(deck)` without an explicit `Random` (which would use an unseeded, unpredictable one internally).

### Level 3 — Advanced

Same card-shuffling utility, now demonstrating exactly why seeded randomness matters for testing: a simple "test" verifying the shuffle produces an expected order for a known seed, something impossible to write reliably against unseeded randomness.

```java
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Random;

public class RandomAdvanced {
    static List<String> shuffleDeck(List<String> deck, long seed) {
        List<String> copy = new ArrayList<>(deck); // don't mutate the caller's original list
        Collections.shuffle(copy, new Random(seed));
        return copy;
    }

    // A simple, hand-rolled "test" -- verifies that shuffling with a FIXED seed always
    // produces the SAME result, which is exactly the kind of assertion real automated
    // tests make against code involving randomness.
    static void testShuffleIsReproducible() {
        List<String> original = List.of("A", "B", "C", "D", "E");

        List<String> shuffle1 = shuffleDeck(original, 99);
        List<String> shuffle2 = shuffleDeck(original, 99); // SAME seed

        if (shuffle1.equals(shuffle2)) {
            System.out.println("PASS: same seed produces the same shuffle order: " + shuffle1);
        } else {
            System.out.println("FAIL: same seed produced different orders! " + shuffle1 + " vs " + shuffle2);
        }

        List<String> shuffle3 = shuffleDeck(original, 100); // DIFFERENT seed
        System.out.println("Different seed (100) produces: " + shuffle3
            + (shuffle3.equals(shuffle1) ? " (coincidentally same!)" : " (different, as expected)"));
    }

    public static void main(String[] args) {
        testShuffleIsReproducible();
    }
}
```

**How to run:** `java RandomAdvanced.java`

`shuffleDeck(original, 99)` called twice with the identical seed (`99`) is guaranteed to produce the exact same shuffled order both times, letting `testShuffleIsReproducible` assert `shuffle1.equals(shuffle2)` reliably — this kind of deterministic assertion against "random" behaviour is only possible because of explicit seeding; without it, no test could reliably verify a shuffle's exact output, only weaker properties like "the shuffled list contains the same elements."

## 6. Walkthrough

Trace `testShuffleIsReproducible()` in `RandomAdvanced` step by step.

**`original = List.of("A", "B", "C", "D", "E")`.** An immutable five-element list is created as the baseline deck.

**`shuffleDeck(original, 99)` (first call).** Inside, `copy` is created as a new `ArrayList` containing `["A", "B", "C", "D", "E"]` (a fresh copy, so `original` itself is never mutated). `Collections.shuffle(copy, new Random(99))` uses a `Random` instance seeded with `99` to determine a specific shuffle order — say, hypothetically, this produces `["C", "A", "E", "B", "D"]`. This is returned and assigned to `shuffle1`.

**`shuffleDeck(original, 99)` (second call).** Again, a fresh `copy` is made from `original` (still `["A", "B", "C", "D", "E"]`, unaffected by the previous call). `Collections.shuffle(copy, new Random(99))` uses a **brand-new** `Random` instance, but seeded with the identical value, `99` — since `Random`'s sequence is entirely determined by its seed and its deterministic internal algorithm, this new `Random(99)` produces the *exact same sequence* of values as the previous `Random(99)` did, resulting in the identical shuffle order: `["C", "A", "E", "B", "D"]`. This is assigned to `shuffle2`.

**`shuffle1.equals(shuffle2)`.** Both lists hold the identical elements in the identical order, so `List.equals` (which compares element-by-element in sequence) returns `true`. Prints `"PASS: same seed produces the same shuffle order: [C, A, E, B, D]"` (using the hypothetical order from above; the actual order depends on `Random`'s specific algorithm, but it is always reproducible for a given seed).

**`shuffleDeck(original, 100)`.** A fresh `copy` of `original` is shuffled using `Random(100)` — a *different* seed from `99`, so this produces a genuinely different sequence of "random" choices, resulting (almost certainly) in a different order from `shuffle1` — say, hypothetically, `["D", "C", "A", "B", "E"]`. Assigned to `shuffle3`.

**Final print.** Checks `shuffle3.equals(shuffle1)`: since the two seeds are different, this is (overwhelmingly likely, though not mathematically guaranteed for arbitrary lists) `false`, so it prints the "different, as expected" branch.

```
original = [A, B, C, D, E]  (never mutated, only copied)

shuffleDeck(original, 99) #1: copy shuffled with Random(99) -> hypothetically [C, A, E, B, D] -> shuffle1
shuffleDeck(original, 99) #2: copy shuffled with a NEW Random(99) -> IDENTICAL sequence -> [C, A, E, B, D] -> shuffle2

shuffle1.equals(shuffle2) -> true -> "PASS: ..."

shuffleDeck(original, 100): copy shuffled with Random(100) -> different sequence -> hypothetically [D, C, A, B, E] -> shuffle3
shuffle3.equals(shuffle1) -> false -> "... (different, as expected)"
```

**Illustrative final output** (the exact shuffle orders depend on `Random`'s specific algorithm, but will be identical every time this program is run, for these specific seeds):
```
PASS: same seed produces the same shuffle order: [C, A, E, B, D]
Different seed (100) produces: [D, C, A, B, E] (different, as expected)
```

## 7. Gotchas & takeaways

> **`java.util.Random` is not suitable for security-sensitive purposes (like generating cryptographic keys, session tokens, or passwords)** — its pseudo-random sequence, while statistically well-distributed, is fully predictable if an attacker knows or can guess the seed, and its internal algorithm is a well-documented, linear, easily-reversible one. For any security-sensitive randomness, use `java.security.SecureRandom` instead, which is specifically designed to be cryptographically unpredictable.

> **Two different `Random` instances constructed with the same seed will always produce the exact same sequence of values, for the life of the JVM version and algorithm used** — this determinism is a deliberate, documented guarantee of `Random`'s design, not an implementation accident, which is precisely what makes seeded `Random` instances so valuable for writing reliable, reproducible tests involving randomized behavior.

- `java.util.Random` generates pseudo-random `int`, `long`, `double`, `boolean`, and bounded values, offering more control and correctness than manually deriving bounded values from `Math.random()`.
- A `Random` instance constructed with an explicit seed produces a fully deterministic, reproducible sequence — the same seed always yields the exact same sequence of "random" values.
- Seeded `Random` instances are essential for writing reliable, deterministic automated tests involving randomized logic (like shuffling or sampling), where an unseeded source would make exact-output assertions impossible.
- Never use `java.util.Random` for security-sensitive randomness (keys, tokens, passwords) — use `java.security.SecureRandom` instead, which is specifically designed to resist prediction.
