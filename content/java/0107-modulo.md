---
card: java
gi: 107
slug: modulo
title: Modulo %
---

## 1. What it is

The `%` operator computes the remainder of dividing its left operand by its right operand. For integer types, Java defines it precisely so that `(a / b) * b + (a % b) == a` always holds — because `/` truncates toward zero, `%` correspondingly always has the same sign as the dividend `a` (the left operand), regardless of the sign of `b`. Unlike some languages, Java also defines `%` for floating-point types (`float`/`double`), where it computes the IEEE remainder of the division.

```java
System.out.println(7 % 3);     // 1
System.out.println(-7 % 3);    // -1  (sign follows the dividend, -7)
System.out.println(7 % -3);    // 1   (sign still follows the dividend, 7)
System.out.println(-7 % -3);   // -1

System.out.println(7.5 % 2.0); // 1.5 — modulo works on doubles too

try {
    System.out.println(5 % 0);  // throws, just like integer division by zero
} catch (ArithmeticException e) {
    System.out.println("int 5 % 0 throws: " + e.getMessage());
}
System.out.println(5.0 % 0.0);  // NaN, does not throw
```

`%` is often called "remainder" rather than "modulo" in strict mathematical terminology, precisely because true mathematical modulo is always non-negative for a positive modulus — Java's `%` is not that; it is the C-style remainder operator.

## 2. Why & when

`%` is the standard tool for:

- Checking divisibility / parity: `n % 2 == 0` for even numbers.
- Cycling through a fixed range: `index = (index + 1) % arraySize` to wrap an array index (works correctly *only* when `index` stays non-negative).
- Extracting digits: `number % 10` gives the last decimal digit.
- Splitting a duration into units: `totalSeconds % 60` for seconds-within-a-minute.

The main danger is assuming `%` always returns a non-negative value when the dividend can be negative — cycling logic that computes `(currentIndex - 1) % size` to move "backward" will produce a negative result when `currentIndex` is `0`, breaking any code that uses the result directly as an array index. `Math.floorMod` is the fix when true wraparound semantics are needed (see also [Division / (integer vs float)](0106-division-integer-vs-float.md)).

## 3. Core concept

```java
public class ModuloDemo {
    public static void main(String[] args) {
        // Basic remainder
        System.out.println("7 % 3   = " + (7 % 3));      // 1
        System.out.println("-7 % 3  = " + (-7 % 3));      // -1 (sign of dividend)
        System.out.println("7 % -3  = " + (7 % -3));      // 1  (sign of dividend, not divisor)

        // Even/odd check
        int n = 42;
        System.out.println(n + " is " + (n % 2 == 0 ? "even" : "odd"));

        // Digit extraction
        int number = 4527;
        System.out.println("Last digit of " + number + ": " + (number % 10));

        // Time splitting
        int totalSeconds = 3725;
        int hours = totalSeconds / 3600;
        int minutes = (totalSeconds % 3600) / 60;
        int seconds = totalSeconds % 60;
        System.out.printf("%d seconds = %dh %dm %ds%n", totalSeconds, hours, minutes, seconds);

        // Modulo on doubles
        System.out.println("7.5 % 2.0 = " + (7.5 % 2.0));  // 1.5
    }
}
```

## 4. Diagram

<svg viewBox="0 0 700 175" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Modulo sign diagram: negative 7 mod 3 gives negative 1 because the sign follows the dividend, not the divisor. Math.floorMod of negative 7 and 3 gives 2, always non-negative when the modulus is positive.">
  <rect x="8" y="8" width="684" height="159" rx="8" fill="#0d1117"/>
  <text x="350" y="24" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">% follows the sign of the DIVIDEND (left operand), not the divisor</text>

  <rect x="16" y="34" width="320" height="116" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="176" y="50" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="sans-serif">-7 % 3  (Java remainder)</text>
  <text x="30" y="72" fill="#e6edf3" font-size="8" font-family="monospace">-7 / 3 truncates to -2</text>
  <text x="30" y="90" fill="#79c0ff" font-size="9" font-family="monospace">-7 - (-2*3) = -1</text>
  <text x="30" y="112" fill="#6db33f" font-size="7.5" font-family="sans-serif">Result is negative because</text>
  <text x="30" y="126" fill="#6db33f" font-size="7.5" font-family="sans-serif">the dividend (-7) is negative.</text>

  <rect x="352" y="34" width="332" height="116" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="518" y="50" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="sans-serif">Math.floorMod(-7, 3)</text>
  <text x="366" y="72" fill="#e6edf3" font-size="8" font-family="monospace">-7 / 3 floors to -3</text>
  <text x="366" y="90" fill="#79c0ff" font-size="9" font-family="monospace">-7 - (-3*3) = 2</text>
  <text x="366" y="112" fill="#6db33f" font-size="7.5" font-family="sans-serif">Always non-negative when</text>
  <text x="366" y="126" fill="#6db33f" font-size="7.5" font-family="sans-serif">the modulus (3) is positive.</text>
</svg>

Java's `%` and `Math.floorMod` can disagree on sign for negative dividends — pick the one whose semantics your use case actually needs.

## 5. Runnable example

Scenario: a circular playlist player that advances to the next or previous track, wrapping around at the ends — a natural place where `%`'s sign behavior with negative numbers causes a real bug.

### Level 1 — Basic

```java
public class ModuloBasic {
    public static void main(String[] args) {
        String[] tracks = { "Intro", "Verse", "Chorus", "Bridge", "Outro" };
        int current = 0;

        // Advancing forward works fine with plain %
        for (int i = 0; i < 7; i++) {
            current = (current + 1) % tracks.length;
            System.out.println("Now playing: " + tracks[current]);
        }
    }
}
```

**How to run:** `java ModuloBasic.java`

Advancing forward with `(current + 1) % tracks.length` always keeps `current` non-negative, since `current + 1` never goes below `1` and the dividend stays positive — `%` behaves exactly like a true wraparound here, cycling `0,1,2,3,4,0,1,...` correctly.

### Level 2 — Intermediate

Same player, now adding a "previous track" button — which naively uses the same `%` pattern and breaks the moment the player wraps past index `0`.

```java
public class ModuloIntermediate {
    public static void main(String[] args) {
        String[] tracks = { "Intro", "Verse", "Chorus", "Bridge", "Outro" };
        int current = 0;

        // BUG: going "previous" from index 0 produces a negative index
        int buggyPrevious = (current - 1) % tracks.length;   // (0 - 1) % 5 = -1
        System.out.println("Buggy previous index: " + buggyPrevious);
        try {
            System.out.println(tracks[buggyPrevious]);   // ArrayIndexOutOfBoundsException
        } catch (ArrayIndexOutOfBoundsException e) {
            System.out.println("Crashed: " + e.getMessage());
        }

        // FIX: add tracks.length before taking % to keep the value non-negative
        int fixedPrevious = (current - 1 + tracks.length) % tracks.length;
        System.out.println("Fixed previous track: " + tracks[fixedPrevious]);
    }
}
```

**How to run:** `java ModuloIntermediate.java`

`(current - 1) % tracks.length` computes `(0 - 1) % 5 = -1 % 5`, and since `%`'s sign follows the dividend (`-1`, which is negative), the result is `-1` — a negative array index, which throws `ArrayIndexOutOfBoundsException` the moment it's used to index into `tracks`. The fix adds `tracks.length` before taking the modulo: `(0 - 1 + 5) % 5 = 4 % 5 = 4`, landing correctly on `"Outro"`, the last track — this trick works because adding any positive multiple of the modulus does not change the mathematical remainder, but it does guarantee the dividend passed to `%` stays non-negative for these specific small ranges.

### Level 3 — Advanced

Same player, now using `Math.floorMod` as the general, always-correct solution (instead of the "add length first" trick, which can itself still go wrong for larger negative offsets), and handling a "jump by N tracks" feature that could move backward by more than one full lap.

```java
public class ModuloAdvanced {

    static int wrapIndex(int index, int length) {
        // Math.floorMod always returns a value in [0, length) for positive length,
        // regardless of how negative `index` is — no manual "+ length" trick needed.
        return Math.floorMod(index, length);
    }

    public static void main(String[] args) {
        String[] tracks = { "Intro", "Verse", "Chorus", "Bridge", "Outro" };
        int current = 0;

        // Jump backward by 13 tracks (e.g., a "rewind 13" button, larger than one lap)
        int jumpBack = 13;
        int naiveAttempt = (current - jumpBack + tracks.length) % tracks.length;
        // This "+ length" trick only guarantees non-negativity if jumpBack <= length;
        // for jumpBack=13 > length=5, current - jumpBack + length is still very negative.
        System.out.println("Naive '+length' trick with big jump: " + naiveAttempt); // still negative!

        int correctIndex = wrapIndex(current - jumpBack, tracks.length);
        System.out.println("Correct wrapped index: " + correctIndex);
        System.out.println("Track: " + tracks[correctIndex]);

        // Demonstrate over a full cycle of offsets to show floorMod always lands in range
        for (int offset = -12; offset <= 12; offset += 6) {
            int idx = wrapIndex(current + offset, tracks.length);
            System.out.println("offset " + offset + " -> index " + idx + " (" + tracks[idx] + ")");
        }
    }
}
```

**How to run:** `java ModuloAdvanced.java`

The naive `"+ length"` trick assumes the negative dividend is at most one modulus-length below zero, so adding `length` once is enough to make it non-negative — but jumping back by `13` on a 5-track list means `current - jumpBack = -13`, and `-13 + 5 = -8` is still negative, so the naive `%` still produces a negative, unusable index. `Math.floorMod(index, length)` has no such limitation: it mathematically computes the floor of `index / length` (rounding toward negative infinity, not zero) and derives the remainder from that, which guarantees a result in `[0, length)` for *any* negative dividend, no matter how large in magnitude. The final loop demonstrates this by cycling through offsets from `-12` to `12`, confirming every single one lands inside the valid track range.

## 6. Walkthrough

Trace `wrapIndex(current - jumpBack, tracks.length)` for `current = 0, jumpBack = 13, tracks.length = 5`:

**Compute the dividend.** `current - jumpBack = 0 - 13 = -13`.

**`Math.floorMod(-13, 5)`.** Conceptually, this first computes the floor of `-13 / 5 = -2.6`, rounding toward negative infinity to get `-3` (not `-2`, which is what truncating division would give). Then it computes `-13 - (-3 * 5) = -13 + 15 = 2`.

**Result.** `2` is returned, which correctly indexes `tracks[2] = "Chorus"` — verify by counting backward from index `0`: one full lap backward (5 steps) returns to `0`, so `13` steps backward is equivalent to `13 mod 5 = 3` steps backward from `0`, landing on index `0 - 3 = -3`, which wraps to `5 - 3 = 2`. Both reasoning paths agree.

```
current=0, jumpBack=13, length=5
dividend = 0 - 13 = -13

floorMod(-13, 5):
  floor(-13/5) = floor(-2.6) = -3      (rounds toward -infinity, unlike truncating / which gives -2)
  -13 - (-3 * 5) = -13 + 15 = 2        <- always in [0, 5)

Sanity check: 13 steps back = 2 full laps (10 steps) + 3 extra steps back from index 0
  index 0 -> back 3 -> wraps to index 2 ("Chorus")   ✓ matches
```

**Final output.** The program first prints the naive attempt's still-negative result to make the limitation concrete, then the correct `floorMod`-based index and its track name, followed by the demonstration loop showing every tested offset landing inside `[0, 5)`.

## 7. Gotchas & takeaways

> **Java's `%` follows the sign of the dividend, not the divisor, and can return a negative result.** `-7 % 3` is `-1`, not `2`. Never assume `%` gives a non-negative "true modulo" result when the left operand can be negative.

> **The "add the length before `%`" trick only works if the negative offset is within one modulus-length of zero.** For larger backward jumps, it can still leave a negative result — use `Math.floorMod`, which is correct for any magnitude.

- `%` satisfies `(a / b) * b + (a % b) == a`, consistent with `/`'s truncation-toward-zero — this is "remainder," not strict mathematical "modulo."
- Use `%` for well-known non-negative cases (checking parity, extracting digits, splitting positive durations) where the dividend is guaranteed non-negative.
- Use `Math.floorMod` whenever the dividend can be negative and you need a guaranteed non-negative result in `[0, modulus)`, such as wrapping array indices or circular buffers.
- Integer `%` by zero throws `ArithmeticException`, just like integer `/`; floating-point `%` by zero produces `NaN` instead.
