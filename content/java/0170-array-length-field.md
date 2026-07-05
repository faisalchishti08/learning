---
card: java
gi: 170
slug: array-length-field
title: array.length field
---

## 1. What it is

Every Java array has a public **`length` field** — written `array.length`, with no parentheses — that holds the number of elements the array can store. It is fixed the moment the array is created and never changes for that array object, even if some of its elements are later modified or set to zero or `null`.

```java
int[] a = new int[5];
System.out.println(a.length); // 5 — fixed at creation, regardless of the values inside

String[] names = { "Ann", "Bo", "Cy" };
System.out.println(names.length); // 3
```

`length` is a **field**, not a method — a common beginner mistake is writing `array.length()` (with parentheses), which only works for `String` and other objects that define a `length()` *method*; arrays use the plain field `array.length`.

## 2. Why & when

`length` exists because arrays in Java are fixed-size from the moment they're created — there's no way to ask "how many elements are actually here" other than storing that count somewhere, and Java stores it directly on the array object itself so it's always available without extra bookkeeping:

- **Loop bounds** — nearly every `for` loop over an array uses `i < array.length` as its stopping condition, so the loop automatically adapts if the array's size changes.
- **Bounds checking** — before accessing `array[i]`, checking `i < array.length` prevents `ArrayIndexOutOfBoundsException`.
- **Generic, size-agnostic code** — a method that takes `int[] data` as a parameter has no other built-in way to know how many elements were passed, since the array itself carries that information.

You use `.length` any time code needs to know "how big is this array," which in practice is almost every time an array is processed.

## 3. Core concept

```java
public class LengthDemo {
    public static void main(String[] args) {
        int[] empty = new int[0];       // valid: a zero-length array is legal
        int[] five = new int[5];
        int[] fromLiteral = { 10, 20, 30 };

        System.out.println(empty.length);       // 0
        System.out.println(five.length);         // 5, even though every slot is still 0
        System.out.println(fromLiteral.length);  // 3

        five[0] = 100; // modifying an element does not change length
        System.out.println(five.length); // still 5
    }
}
```

`length` reflects the array's **capacity**, fixed at creation time by either `new Type[n]` or by the number of values listed in an initializer — it has nothing to do with how many of those slots hold "meaningful" data, since every slot always holds *some* value (a default or an assigned one).

## 4. Diagram

<svg viewBox="0 0 640 130" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="An array of five integer slots with a length field of five shown pointing at the whole array, fixed at creation regardless of the values inside">
  <rect x="8" y="8" width="624" height="114" rx="8" fill="#0d1117"/>
  <text x="320" y="24" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">int[] five = new int[5];</text>

  <rect x="160" y="40" width="50" height="36" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <rect x="210" y="40" width="50" height="36" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <rect x="260" y="40" width="50" height="36" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <rect x="310" y="40" width="50" height="36" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <rect x="360" y="40" width="50" height="36" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="185" y="63" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="monospace">0</text>
  <text x="235" y="63" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="monospace">0</text>
  <text x="285" y="63" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="monospace">0</text>
  <text x="335" y="63" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="monospace">0</text>
  <text x="385" y="63" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="monospace">0</text>

  <line x1="260" y1="90" x2="260" y2="100" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="260" y="112" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">five.length == 5 (fixed, counts all 5 boxes)</text>
</svg>

`length` counts the boxes themselves, not what's written inside them — it stays 5 no matter what values are stored.

## 5. Runnable example

Scenario: processing a variable-size batch of sensor readings — starting with a basic size report, then extending to a size-adaptive loop, then hardening into a method that validates and compares the lengths of two related arrays.

### Level 1 — Basic

```java
public class SensorBatchBasic {
    public static void main(String[] args) {
        double[] readings = { 21.5, 22.0, 21.8, 23.1 };
        System.out.println("Batch size: " + readings.length);
    }
}
```

**How to run:** `java SensorBatchBasic.java`

`readings.length` reports `4`, the number of values listed in the initializer — a direct, no-loop way to learn an array's size.

### Level 2 — Intermediate

Same batch, now using `.length` as the loop bound so the summing logic works for a batch of any size, not just four readings.

```java
public class SensorBatchIntermediate {
    public static void main(String[] args) {
        double[] readings = { 21.5, 22.0, 21.8, 23.1, 20.9 };

        double sum = 0;
        for (int i = 0; i < readings.length; i++) {
            sum += readings[i];
        }
        double average = sum / readings.length;

        System.out.println("Batch size: " + readings.length);
        System.out.println("Average: " + average);
    }
}
```

**How to run:** `java SensorBatchIntermediate.java`

Adding a fifth reading to the array required **no change** to the loop or the average calculation — both `i < readings.length` and `sum / readings.length` automatically adapt to the array's actual size, which is the whole point of relying on `.length` instead of a hard-coded count.

### Level 3 — Advanced

Same scenario, now validating that two related arrays (readings and their timestamps) have matching lengths before processing them together, since mismatched lengths would silently misalign data.

```java
public class SensorBatchAdvanced {

    static void printReadings(double[] readings, long[] timestamps) {
        if (readings.length != timestamps.length) {
            throw new IllegalArgumentException(
                "Mismatched arrays: " + readings.length + " readings but " + timestamps.length + " timestamps");
        }
        for (int i = 0; i < readings.length; i++) {
            System.out.println("t=" + timestamps[i] + "s -> " + readings[i] + "°C");
        }
    }

    public static void main(String[] args) {
        double[] readings = { 21.5, 22.0, 21.8 };
        long[] goodTimestamps = { 0, 60, 120 };
        long[] badTimestamps = { 0, 60 }; // deliberately one short

        printReadings(readings, goodTimestamps);

        try {
            printReadings(readings, badTimestamps);
        } catch (IllegalArgumentException e) {
            System.out.println("Rejected: " + e.getMessage());
        }
    }
}
```

**How to run:** `java SensorBatchAdvanced.java`

`readings.length != timestamps.length` is checked *before* the loop runs, catching a length mismatch as one clear error rather than letting the loop either throw `ArrayIndexOutOfBoundsException` partway through or, worse, silently ignore trailing readings that have no matching timestamp.

## 6. Walkthrough

Trace `SensorBatchAdvanced.main` for the second call, `printReadings(readings, badTimestamps)`:

**Length comparison.** `readings.length` is `3`; `badTimestamps.length` is `2`. Since `3 != 2`, the guard condition is true.

**Exception thrown.** `IllegalArgumentException("Mismatched arrays: 3 readings but 2 timestamps")` is thrown immediately — the `for` loop inside `printReadings` never even begins, so no partial, misaligned output is produced.

**Caught in `main`.** The `try/catch` in `main` catches the exception and prints `"Rejected: Mismatched arrays: 3 readings but 2 timestamps"`.

```
readings.length     = 3
badTimestamps.length = 2
3 != 2 -> throw IllegalArgumentException before any looping happens
caught in main -> print "Rejected: ..."
```

**Contrast with the first call.** `printReadings(readings, goodTimestamps)` passed the length check (`3 == 3`) and printed three lines, one per index from `0` to `2`, pairing each reading with its matching timestamp: `"t=0s -> 21.5°C"`, `"t=60s -> 22.0°C"`, `"t=120s -> 21.8°C"`.

## 7. Gotchas & takeaways

> **`array.length` is a field, not a method** — write `array.length`, never `array.length()`. Confusingly, `String` *does* have a `length()` method (with parentheses), so switching between strings and arrays in the same file is a common source of this exact mistake.

> **`length` never shrinks or grows after creation**, even if you overwrite every element or the array is "logically empty" from your program's point of view. If you need a collection whose size changes over time, use a resizable structure like `java.util.ArrayList` instead of a plain array.

- `array.length` gives the fixed number of slots, set once at creation time by `new Type[n]` or by an initializer's value count.
- Use `.length` (not a hard-coded number) as the loop bound so code automatically adapts to the array's actual size.
- Modifying element values never changes `.length` — it only reflects capacity, not "how many are actually meaningful."
- Before processing two arrays together element-by-element, check that their `.length` values match to avoid misalignment or an out-of-bounds crash.
