---
card: java
gi: 172
slug: iterating-arrays-with-for
title: Iterating arrays with for
---

## 1. What it is

**Iterating with `for`** means visiting every element of an array one at a time, in order, using a loop. Java offers two flavours: the classic **indexed `for`** (`for (int i = 0; i < array.length; i++)`), which gives you both the index and the value, and the **enhanced `for` (for-each)** (`for (Type element : array)`), which gives you just the value, in order, with no index variable to manage.

```java
int[] nums = { 10, 20, 30 };

for (int i = 0; i < nums.length; i++) {
    System.out.println("index " + i + " = " + nums[i]); // classic form: has the index
}

for (int n : nums) {
    System.out.println("value = " + n); // for-each: no index, just the value
}
```

Both loops visit `10`, `20`, `30` in the same order — the difference is purely whether you need the index (classic) or only the value (for-each).

## 2. Why & when

Looping is how almost every array is actually *used* — arrays exist to hold multiple values, and processing "all of them" (summing, printing, searching, transforming) requires visiting each one:

- **Classic indexed `for`** is needed whenever you need the **position** itself — comparing neighbouring elements, writing into a second array at the same index, or stopping partway through based on the index.
- **Enhanced `for` (for-each)** is preferred whenever you only need each **value** and won't modify the array or need its index — it's shorter, and it eliminates an entire category of bugs (off-by-one errors, forgetting to increment `i`).
- You cannot use for-each to **modify** the array's elements — `for (int n : nums) { n = n * 2; }` only changes the local copy `n`, not `nums` itself, since primitives are copied by value; use the classic form when the loop needs to write back into the array.

## 3. Core concept

```java
public class LoopFormsDemo {
    public static void main(String[] args) {
        int[] nums = { 1, 2, 3, 4 };

        // Classic form: can both read AND write, has the index
        for (int i = 0; i < nums.length; i++) {
            nums[i] = nums[i] * 10; // modifies the array in place
        }
        System.out.println(java.util.Arrays.toString(nums)); // [10, 20, 30, 40]

        // For-each: read-only view of each value, no index
        int sum = 0;
        for (int n : nums) {
            sum += n; // reading is fine; n itself is just a local copy
        }
        System.out.println(sum); // 100
    }
}
```

The classic loop is the only one of the two that can write `nums[i] = ...` back into the array, because it has direct index-based access — the for-each loop's `n` is a fresh local variable on each iteration, disconnected from the array's storage.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Comparison of classic indexed for loop which tracks i from 0 to length minus 1 and can write back into the array, versus enhanced for each loop which walks values directly with no index and is read only">
  <rect x="8" y="8" width="300" height="150" rx="8" fill="#0d1117"/>
  <text x="158" y="26" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">Classic: for (int i = 0; i &lt; len; i++)</text>
  <text x="20" y="50" fill="#e6edf3" font-size="10" font-family="monospace">i=0 -&gt; nums[0] (read/write)</text>
  <text x="20" y="70" fill="#e6edf3" font-size="10" font-family="monospace">i=1 -&gt; nums[1] (read/write)</text>
  <text x="20" y="90" fill="#e6edf3" font-size="10" font-family="monospace">i=2 -&gt; nums[2] (read/write)</text>
  <text x="20" y="120" fill="#8b949e" font-size="9" font-family="sans-serif">has the index; can modify array</text>

  <rect x="332" y="8" width="300" height="150" rx="8" fill="#0d1117"/>
  <text x="482" y="26" fill="#79c0ff" font-size="12" text-anchor="middle" font-family="sans-serif">For-each: for (int n : nums)</text>
  <text x="344" y="50" fill="#e6edf3" font-size="10" font-family="monospace">n = nums[0] (read-only copy)</text>
  <text x="344" y="70" fill="#e6edf3" font-size="10" font-family="monospace">n = nums[1] (read-only copy)</text>
  <text x="344" y="90" fill="#e6edf3" font-size="10" font-family="monospace">n = nums[2] (read-only copy)</text>
  <text x="344" y="120" fill="#8b949e" font-size="9" font-family="sans-serif">no index; cannot modify array</text>
</svg>

Choose the classic form when the index or write access is needed; choose for-each for simple, read-only passes.

## 5. Runnable example

Scenario: processing a week's daily step counts — starting with a basic print-all loop, then extending to find the maximum using the index-free for-each form, then hardening into a classic indexed loop that normalizes (doubles) every value in place, something for-each cannot do.

### Level 1 — Basic

```java
public class StepsBasic {
    public static void main(String[] args) {
        int[] dailySteps = { 8200, 6400, 10500, 3000, 9100, 12000, 7600 };

        for (int steps : dailySteps) {
            System.out.println(steps + " steps");
        }
    }
}
```

**How to run:** `java StepsBasic.java`

The for-each loop `for (int steps : dailySteps)` visits every value in order, printing each on its own line — no index variable is declared or needed since only the values matter here.

### Level 2 — Intermediate

Same data, now finding the maximum using for-each — still read-only, so for-each remains a good fit.

```java
public class StepsIntermediate {
    public static void main(String[] args) {
        int[] dailySteps = { 8200, 6400, 10500, 3000, 9100, 12000, 7600 };

        int max = dailySteps[0];
        for (int steps : dailySteps) {
            if (steps > max) {
                max = steps;
            }
        }
        System.out.println("Best day: " + max + " steps");
    }
}
```

**How to run:** `java StepsIntermediate.java`

`max` starts at `dailySteps[0]` (the first value) before the loop, then each subsequent value is compared against it — this is still purely a read of every element, so for-each remains the natural, simplest choice.

### Level 3 — Advanced

Same weekly data, now applying a 10% goal-adjustment to every day's step count **in place** — this requires writing back into the array by index, which for-each cannot do, so the classic indexed form is required.

```java
public class StepsAdvanced {
    public static void main(String[] args) {
        int[] dailySteps = { 8200, 6400, 10500, 3000, 9100, 12000, 7600 };

        for (int i = 0; i < dailySteps.length; i++) {
            dailySteps[i] = (int) (dailySteps[i] * 1.10); // adjust goal upward by 10%, written back by index
        }

        int total = 0;
        for (int i = 0; i < dailySteps.length; i++) {
            System.out.println("Day " + i + " adjusted goal: " + dailySteps[i]);
            total += dailySteps[i];
        }
        System.out.println("Weekly total: " + total);
    }
}
```

**How to run:** `java StepsAdvanced.java`

`dailySteps[i] = (int) (dailySteps[i] * 1.10)` reads the current value at index `i`, multiplies it, and writes the result back to that same index — only possible because the classic loop tracks `i` explicitly; a for-each loop's `steps` variable would be a disconnected local copy, and reassigning it would have no effect on `dailySteps`.

## 6. Walkthrough

Trace `StepsAdvanced.main` for the first two days of `dailySteps = { 8200, 6400, 10500, 3000, 9100, 12000, 7600 }`:

**First loop, i=0.** `dailySteps[0] * 1.10` is `8200 * 1.10 = 9020.0`. Cast to `int`, this is `9020`. Written back: `dailySteps[0] = 9020`.

**First loop, i=1.** `dailySteps[1] * 1.10` is `6400 * 1.10 = 7040.0`, cast to `7040`. `dailySteps[1] = 7040`.

**...continues for i=2 through i=6**, each index read, multiplied, cast, and written back before `i` increments and the loop condition `i < dailySteps.length` (`7`) is re-checked; the loop ends once `i` reaches `7`.

**Second loop.** Now `dailySteps` holds the adjusted values. This loop both prints each `"Day i adjusted goal: value"` line and accumulates `total`.

```
i: 0   1   2    3    4   5     6
before: 8200 6400 10500 3000 9100 12000 7600
*1.10:  9020 7040 11550 3300 10010 13200 8360
```

**Final output.** Seven `"Day N adjusted goal: ..."` lines matching the bottom row above, followed by `"Weekly total: 62480"` (the sum of all seven adjusted values).

## 7. Gotchas & takeaways

> **For-each cannot modify the array.** `for (int n : nums) { n++; }` only increments the loop's local copy `n` — `nums` itself is completely unchanged after the loop. This is one of the most common "why didn't my array change" bugs for beginners moving from classic to enhanced `for`.

> **Classic `for` loops are vulnerable to off-by-one errors** — using `i <= array.length` (instead of `<`) reaches one index past the end and throws `ArrayIndexOutOfBoundsException`. For-each avoids this entire class of bug by construction, since there's no index to get wrong.

- Use for-each (`for (Type x : array)`) for simple, read-only passes over every element — it's shorter and safer.
- Use the classic indexed `for` when you need the index itself, need to write back into the array, or need to skip/stop at a computed position.
- For-each's loop variable is a copy; assigning to it never affects the original array.
- Both forms visit elements strictly in index order, from `0` to `length - 1`.
