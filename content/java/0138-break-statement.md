---
card: java
gi: 138
slug: break-statement
title: break statement
---

## 1. What it is

The `break` statement immediately exits the innermost enclosing loop (`for`, `while`, `do-while`) or `switch` statement, transferring control to the very next statement after that loop's or switch's closing brace. It skips any remaining iterations entirely — there is no "finish the current pass, then stop"; `break` stops execution the instant it runs.

```java
for (int i = 0; i < 10; i++) {
    if (i == 3) {
        break; // exits the loop entirely — i never reaches 4
    }
    System.out.println("i = " + i);
}
System.out.println("Loop exited");
// prints: i = 0, i = 1, i = 2, Loop exited
```

Note that `3` itself never gets printed — `break` fires before the `System.out.println` for that iteration is reached.

## 2. Why & when

`break` is used whenever you need to stop looping as soon as some condition is satisfied, rather than running through every remaining iteration pointlessly:

- **Searching** — once the target element is found in an array or list, there's no need to keep scanning; `break` stops the scan immediately.
- **Early exit on a special value** — reading input or data until a sentinel ("quit", `-1`, `null`) appears.
- **Guarding against unnecessary work** — stopping a loop the moment further iterations can't change the outcome, which both improves performance and makes intent explicit.

Without `break`, achieving the same effect requires folding the "should I stop?" logic into the loop's own condition, which can make a loop's header far more convoluted than a simple `if (found) break;` in the body. `break` also serves double duty inside a `switch` (see the earlier fall-through topic) — the two uses share the keyword but apply to different enclosing constructs.

## 3. Core concept

```java
public class BreakDemo {
    public static void main(String[] args) {
        int[] numbers = { 4, 8, 15, 16, 23, 42 };
        int target = 16;
        int foundIndex = -1;

        for (int i = 0; i < numbers.length; i++) {
            if (numbers[i] == target) {
                foundIndex = i;
                break; // no point scanning the rest once we've found it
            }
        }

        if (foundIndex >= 0) {
            System.out.println("Found " + target + " at index " + foundIndex);
        } else {
            System.out.println(target + " not found");
        }
    }
}
```

As soon as `numbers[i] == target` is `true` (at `i = 3`), `break` fires — the loop never checks `numbers[4]` or `numbers[5]`, even though the loop's own header (`i < numbers.length`) would otherwise have allowed it to continue.

## 4. Diagram

<svg viewBox="0 0 700 175" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Break statement diagram: a loop scans elements one by one; when the target is found, break fires immediately, skipping all remaining iterations and jumping straight past the loop's closing brace.">
  <rect x="8" y="8" width="684" height="159" rx="8" fill="#0d1117"/>
  <text x="350" y="24" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Searching {4, 8, 15, 16, 23, 42} for 16 — break fires at index 3</text>

  <rect x="30" y="45" width="70" height="26" rx="4" fill="#1c2430" stroke="#8b949e"/>
  <text x="65" y="62" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">4</text>
  <rect x="110" y="45" width="70" height="26" rx="4" fill="#1c2430" stroke="#8b949e"/>
  <text x="145" y="62" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">8</text>
  <rect x="190" y="45" width="70" height="26" rx="4" fill="#1c2430" stroke="#8b949e"/>
  <text x="225" y="62" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">15</text>
  <rect x="270" y="45" width="70" height="26" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="2.5"/>
  <text x="305" y="62" fill="#6db33f" font-size="9" text-anchor="middle" font-family="monospace">16 ✓</text>
  <rect x="350" y="45" width="70" height="26" rx="4" fill="#1c2430" stroke="#f85149" stroke-dasharray="3,2"/>
  <text x="385" y="62" fill="#f85149" font-size="9" text-anchor="middle" font-family="monospace">23</text>
  <rect x="430" y="45" width="70" height="26" rx="4" fill="#1c2430" stroke="#f85149" stroke-dasharray="3,2"/>
  <text x="465" y="62" fill="#f85149" font-size="9" text-anchor="middle" font-family="monospace">42</text>

  <text x="65" y="90" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">scanned</text>
  <text x="145" y="90" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">scanned</text>
  <text x="225" y="90" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">scanned</text>
  <text x="305" y="90" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">match! break</text>
  <text x="385" y="90" fill="#f85149" font-size="8" text-anchor="middle" font-family="sans-serif">never checked</text>
  <text x="465" y="90" fill="#f85149" font-size="8" text-anchor="middle" font-family="sans-serif">never checked</text>

  <text x="350" y="130" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="sans-serif">break exits immediately — index 4 and 5 are skipped entirely, not merely "fast-forwarded through."</text>
</svg>

`break` cuts the loop off at the exact point the condition is met — nothing after it in the loop runs again.

## 5. Runnable example

Scenario: scanning a list of transactions to find the first one that exceeds a fraud threshold — starting with a basic linear search that breaks on the first match, then reporting the match's details, then extending it to also break out early on a hard data-integrity error, distinct from an ordinary "not found."

### Level 1 — Basic

```java
public class FraudScanBasic {
    public static void main(String[] args) {
        int[] amounts = { 50, 120, 75, 9800, 30 };
        int threshold = 5000;

        for (int i = 0; i < amounts.length; i++) {
            if (amounts[i] > threshold) {
                System.out.println("Suspicious amount found: " + amounts[i]);
                break;
            }
        }
        System.out.println("Scan complete.");
    }
}
```

**How to run:** `java FraudScanBasic.java`

The loop checks each amount in order; once `amounts[3] = 9800` exceeds `threshold`, it prints the match and `break`s immediately — `amounts[4] = 30` is never even examined, since there is no need to keep scanning once a suspicious transaction has been found.

### Level 2 — Intermediate

Same scan, now recording the index and value of the match (rather than just printing it inline), so the caller can report exactly where the suspicious transaction was found — useful once this logic needs to feed into something beyond a println.

```java
public class FraudScanIntermediate {
    public static void main(String[] args) {
        int[] amounts = { 50, 120, 75, 9800, 30, 15000 };
        int threshold = 5000;
        int foundIndex = -1;
        int foundAmount = -1;

        for (int i = 0; i < amounts.length; i++) {
            if (amounts[i] > threshold) {
                foundIndex = i;
                foundAmount = amounts[i];
                break; // stop at the FIRST suspicious transaction, ignore the later 15000
            }
        }

        if (foundIndex >= 0) {
            System.out.println("First suspicious transaction: $" + foundAmount + " at index " + foundIndex);
        } else {
            System.out.println("No suspicious transactions found.");
        }
    }
}
```

**How to run:** `java FraudScanIntermediate.java`

Even though `amounts[5] = 15000` is even more suspicious than `amounts[3] = 9800`, the loop stops at the *first* match and never sees it — this is a direct, intended consequence of `break`: "stop at the first hit," not "find the worst hit." If finding the largest suspicious value were the actual goal, the loop would need to keep scanning without breaking, tracking a running maximum instead.

### Level 3 — Advanced

Same fraud scan, now also breaking early on a **data-integrity error** (a negative amount, which should never occur and indicates corrupted input) — distinct from the normal "threshold exceeded" break, and reported differently to the caller.

```java
public class FraudScanAdvanced {

    enum ScanResult { CLEAN, SUSPICIOUS, CORRUPTED_DATA }

    static ScanResult scan(int[] amounts, int threshold) {
        for (int i = 0; i < amounts.length; i++) {
            if (amounts[i] < 0) {
                System.out.println("Corrupted record at index " + i + ": " + amounts[i]);
                return ScanResult.CORRUPTED_DATA; // stop immediately — don't trust anything after this
            }
            if (amounts[i] > threshold) {
                System.out.println("Suspicious amount at index " + i + ": " + amounts[i]);
                return ScanResult.SUSPICIOUS;
            }
        }
        return ScanResult.CLEAN;
    }

    public static void main(String[] args) {
        System.out.println(scan(new int[]{ 50, 120, 9800, 30 }, 5000));
        System.out.println(scan(new int[]{ 50, 120, -5, 30 }, 5000));
        System.out.println(scan(new int[]{ 50, 120, 75, 30 }, 5000));
    }
}
```

**How to run:** `java FraudScanAdvanced.java`

Here `return` plays the same "stop scanning right now" role that `break` played in the earlier levels, but exits the whole method rather than just the loop — appropriate since each of the three outcomes (`CLEAN`, `SUSPICIOUS`, `CORRUPTED_DATA`) should immediately end the scan and hand a distinct result back to the caller. This mirrors the `break`-vs-`return` distinction from the infinite-loop topic: use `break` to exit a loop while more code still follows it in the same method; use `return` when the method itself is done the moment the condition is met.

## 6. Walkthrough

Trace `scan(new int[]{ 50, 120, -5, 30 }, 5000)`:

**Index 0.** `amounts[0] = 50`. Not negative, not over threshold — no exit condition met, loop continues.

**Index 1.** `amounts[1] = 120`. Same — neither condition met, continues.

**Index 2.** `amounts[2] = -5`. The first check, `amounts[i] < 0`, is now `true`. The method prints `"Corrupted record at index 2: -5"` and immediately `return`s `ScanResult.CORRUPTED_DATA` — execution leaves the loop and the method in one step. Index 3 (`30`) is never examined at all.

```
i=0: 50 -> not negative, not over threshold -> continue
i=1: 120 -> not negative, not over threshold -> continue
i=2: -5 -> NEGATIVE! print corrupted-record message -> return CORRUPTED_DATA (index 3 skipped)
```

**Final output.** The three calls in `main` print `SUSPICIOUS` (matches at index 2 with `9800`), `CORRUPTED_DATA` (as traced above), and `CLEAN` (no amount in the third array is negative or over `5000`, so the loop runs to completion and falls through to `return ScanResult.CLEAN;` after the `for` loop).

## 7. Gotchas & takeaways

> **`break` only exits the single innermost loop or switch it's directly inside** — inside nested loops, a plain `break` in the inner loop does *not* also exit the outer loop. Escaping multiple nested loops at once requires a **labeled break** (covered in the next topic), not a bare `break`.

> **`break` inside a loop that's inside a `switch` (or vice versa) only breaks the innermost of the two** — a `break` written inside a `case` body that is itself inside a `for` loop exits the `switch`, not the loop, and a `break` written directly in the loop body (outside any switch) exits the loop. Which one fires depends entirely on which construct's braces you're lexically inside.

- `break` exits the nearest enclosing loop or `switch` immediately — no remaining code in that iteration or case runs.
- Use `break` to stop searching or looping the moment further work is provably pointless (e.g., the first match is all you need).
- If you need the largest/best/all matches rather than the first, don't `break` — keep scanning and track the best result seen so far.
- When a method should stop entirely (not just exit a loop) the moment a condition is met, `return` is usually clearer than `break`, especially when multiple distinct outcomes are possible.
