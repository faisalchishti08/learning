---
card: java
gi: 139
slug: continue-statement
title: continue statement
---

## 1. What it is

The `continue` statement immediately skips the **rest of the current iteration** of the innermost enclosing loop and jumps straight to the next iteration — for a `for` loop, that means running the update expression and then re-checking the condition; for `while`/`do-while`, it means jumping straight to the condition check. Unlike `break`, `continue` does not exit the loop; the loop keeps going, it just skips ahead within the current pass.

```java
for (int i = 0; i < 6; i++) {
    if (i % 2 != 0) {
        continue; // skip odd numbers — jump straight to i++ and the next condition check
    }
    System.out.println("Even: " + i);
}
// prints: Even: 0, Even: 2, Even: 4
```

When `i` is odd, `continue` skips the `System.out.println` entirely for that pass, but the loop itself continues running — `i++` still happens, and the loop still checks `i < 6` again.

## 2. Why & when

`continue` is the right tool whenever you want to **skip uninteresting or invalid iterations** without abandoning the whole loop, and without wrapping the rest of the loop body in a big `if (isInteresting) { ... }` block:

- **Filtering while iterating** — process only elements that meet some criterion, skip the rest, without extra nesting.
- **Skipping invalid or malformed entries** — e.g., skip a `null` or negative value in a dataset and move on to the next one, rather than special-casing it deep inside the body.
- **Reducing nesting** — an early `continue` for the "not interesting" case often reads more clearly than one giant `if` wrapping the entire remaining body.

`continue` is not for "stop the loop" — that's what `break` is for. Confusing the two is a common beginner mistake: `continue` skips *one* iteration and keeps looping; `break` exits the loop *entirely*.

## 3. Core concept

```java
public class ContinueDemo {
    public static void main(String[] args) {
        String[] names = { "Alice", "", "Bob", null, "Carol" };

        for (String name : names) {
            if (name == null || name.isEmpty()) {
                continue; // skip invalid entries, don't stop processing the rest
            }
            System.out.println("Processing: " + name);
        }
    }
}
```

When `name` is `""` or `null`, `continue` skips the `System.out.println` for that entry and moves straight to the next element of `names` — the loop never stops, it just doesn't do anything for the entries that don't qualify.

## 4. Diagram

<svg viewBox="0 0 700 175" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Continue statement diagram: iterating a list, an invalid entry triggers continue which skips straight to the next iteration, while a valid entry is processed normally, and the loop as a whole keeps running either way.">
  <rect x="8" y="8" width="684" height="159" rx="8" fill="#0d1117"/>
  <text x="350" y="24" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">for (String name : names) — continue skips ONLY the current pass, loop keeps going</text>

  <rect x="30" y="45" width="90" height="28" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="75" y="64" fill="#6db33f" font-size="9" text-anchor="middle" font-family="monospace">"Alice"</text>
  <rect x="140" y="45" width="90" height="28" rx="4" fill="#1c2430" stroke="#f85149" stroke-width="1.5"/>
  <text x="185" y="64" fill="#f85149" font-size="9" text-anchor="middle" font-family="monospace">"" (empty)</text>
  <rect x="250" y="45" width="90" height="28" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="295" y="64" fill="#6db33f" font-size="9" text-anchor="middle" font-family="monospace">"Bob"</text>
  <rect x="360" y="45" width="90" height="28" rx="4" fill="#1c2430" stroke="#f85149" stroke-width="1.5"/>
  <text x="405" y="64" fill="#f85149" font-size="9" text-anchor="middle" font-family="monospace">null</text>
  <rect x="470" y="45" width="90" height="28" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="515" y="64" fill="#6db33f" font-size="9" text-anchor="middle" font-family="monospace">"Carol"</text>

  <text x="75" y="90" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">printed</text>
  <text x="185" y="90" fill="#f85149" font-size="8" text-anchor="middle" font-family="sans-serif">continue (skip)</text>
  <text x="295" y="90" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">printed</text>
  <text x="405" y="90" fill="#f85149" font-size="8" text-anchor="middle" font-family="sans-serif">continue (skip)</text>
  <text x="515" y="90" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">printed</text>

  <text x="350" y="125" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="sans-serif">Every element is still visited — continue skips only the println for invalid ones,</text>
  <text x="350" y="140" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="sans-serif">unlike break, which would have stopped the whole loop at the first invalid entry.</text>
</svg>

`continue` skips work for one element but the loop still visits every remaining element.

## 5. Runnable example

Scenario: summing only the valid entries in a batch of sensor readings, where some readings are error codes that must be skipped — starting basic, then adding a running count of how many were skipped, then hardening it to distinguish two different kinds of invalid readings while still processing everything else.

### Level 1 — Basic

```java
public class SensorSumBasic {
    public static void main(String[] args) {
        int[] readings = { 22, -1, 25, -1, 19 }; // -1 marks a sensor error, not a real reading
        int sum = 0;

        for (int reading : readings) {
            if (reading == -1) {
                continue; // skip error readings, keep summing the rest
            }
            sum += reading;
        }

        System.out.println("Sum of valid readings: " + sum);
    }
}
```

**How to run:** `java SensorSumBasic.java`

Each `-1` triggers `continue`, which skips `sum += reading` for that element only — the loop moves straight on to the next reading rather than stopping. The final sum (`22 + 25 + 19 = 66`) correctly excludes both error codes, without the loop ever being interrupted.

### Level 2 — Intermediate

Same sensor batch, now also **counting** how many readings were skipped, alongside the sum — a natural addition since we're already identifying which entries get `continue`d.

```java
public class SensorSumIntermediate {
    public static void main(String[] args) {
        int[] readings = { 22, -1, 25, -1, 19, -1 };
        int sum = 0;
        int skipped = 0;

        for (int reading : readings) {
            if (reading == -1) {
                skipped++;
                continue;
            }
            sum += reading;
        }

        System.out.println("Sum: " + sum + ", valid readings: " + (readings.length - skipped) + ", skipped: " + skipped);
    }
}
```

**How to run:** `java SensorSumIntermediate.java`

`skipped++` runs *before* `continue`, since `continue` only skips the code *after* it in the current iteration — anything before the `continue` statement itself still executes normally. This is an important distinction: `continue` doesn't prevent the beginning of an iteration from running, only the remainder of it from the point `continue` is reached.

### Level 3 — Advanced

Same sensor processing, now distinguishing a hard sensor error (`-1`) from an **out-of-range** reading (anything above a plausible maximum, which should be logged as a warning but still skipped) — both are skipped via `continue`, but reported differently, and the loop uses an index-based `for` so it can reference the reading's position in the warning message.

```java
public class SensorSumAdvanced {
    public static void main(String[] args) {
        int[] readings = { 22, -1, 25, 999, 19, -1, 21 };
        final int maxPlausible = 100;
        int sum = 0;
        int validCount = 0;

        for (int i = 0; i < readings.length; i++) {
            int reading = readings[i];

            if (reading == -1) {
                System.out.println("Skipping sensor error at index " + i);
                continue;
            }
            if (reading > maxPlausible) {
                System.out.println("Skipping implausible reading " + reading + " at index " + i);
                continue;
            }

            sum += reading;
            validCount++;
        }

        double average = validCount == 0 ? 0.0 : (double) sum / validCount;
        System.out.println("Valid readings: " + validCount + ", sum: " + sum + ", average: " + average);
    }
}
```

**How to run:** `java SensorSumAdvanced.java`

Two separate `if` checks each end in their own `continue` — one for `-1` sensor errors, one for implausibly large readings — and each prints a distinct message before skipping, so the two failure modes remain distinguishable in the output even though both ultimately just move on to the next reading. Only readings that pass *both* checks reach `sum += reading; validCount++;`, and `validCount` (rather than `readings.length`) is used to compute the average, since it accurately reflects how many readings actually contributed to `sum`.

## 6. Walkthrough

Trace the loop over `{ 22, -1, 25, 999, 19, -1, 21 }`:

**i = 0.** `reading = 22`. Neither check matches; falls through to `sum += 22` (`sum = 22`), `validCount = 1`.

**i = 1.** `reading = -1`. First check matches: prints `"Skipping sensor error at index 1"`, then `continue` — jumps straight to the `for` loop's update (`i++`), skipping the second check and the summing entirely for this pass.

**i = 2.** `reading = 25`. Neither check matches; `sum += 25` (`sum = 47`), `validCount = 2`.

**i = 3.** `reading = 999`. First check (`== -1`) doesn't match, but the second (`> 100`) does: prints `"Skipping implausible reading 999 at index 3"`, then `continue`.

**i = 4.** `reading = 19`. Neither check matches; `sum += 19` (`sum = 66`), `validCount = 3`.

**i = 5.** `reading = -1`. First check matches again: prints the sensor-error message, `continue`.

**i = 6.** `reading = 21`. Neither check matches; `sum += 21` (`sum = 87`), `validCount = 4`.

```
i=0: 22   -> valid   sum=22  validCount=1
i=1: -1   -> SKIP (sensor error)
i=2: 25   -> valid   sum=47  validCount=2
i=3: 999  -> SKIP (implausible)
i=4: 19   -> valid   sum=66  validCount=3
i=5: -1   -> SKIP (sensor error)
i=6: 21   -> valid   sum=87  validCount=4
```

**Final output.** After the loop, `validCount = 4`, `sum = 87`, and `average = 87 / 4 = 21.75`. The program prints `"Valid readings: 4, sum: 87, average: 21.75"`, alongside the four skip messages printed as they occurred during the loop.

## 7. Gotchas & takeaways

> **`continue` in a `for` loop still runs the update expression before re-checking the condition** — it does not skip `i++`. If you mistakenly believe `continue` skips the update too, you can accidentally write an infinite loop by relying on the update to eventually terminate it while `continue` bypasses code that *would* have updated some other variable the condition also depends on.

> **`continue`, like `break`, only affects the single innermost enclosing loop.** Inside nested loops, a bare `continue` in the inner loop skips only the rest of the *inner* loop's current pass — it has no effect on the outer loop's iteration. Skipping an outer loop's iteration from inside a nested inner loop requires a **labeled continue** (covered in the next topic).

- `continue` skips the remainder of the current iteration only; the loop keeps running afterward — it is not a form of `break`.
- Code written *before* a `continue` statement in the same iteration still executes normally; only the code *after* it is skipped.
- Use `continue` to filter out or skip invalid/uninteresting elements while processing the rest, often reducing nested `if` blocks.
- In a `for` loop, `continue` still triggers the update expression (e.g., `i++`) before the condition is re-checked — it does not bypass loop bookkeeping.
