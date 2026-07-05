---
card: java
gi: 169
slug: accessing-modifying-elements
title: Accessing & modifying elements
---

## 1. What it is

**Accessing and modifying array elements** means reading or writing a single value stored inside an array using its **index** — the position of that value, counted from `0`. The syntax is `array[index]` for reading and `array[index] = value` for writing. Because indices start at `0`, the first element is `array[0]` and the last element of an array of length `n` is `array[n - 1]`, not `array[n]`.

```java
int[] scores = { 10, 20, 30 };
int first = scores[0];   // reads 10
scores[1] = 99;          // writes 99 into slot index 1
System.out.println(scores[1]); // 99
```

Both reading (`scores[0]`) and writing (`scores[1] = 99`) use the same `[index]` syntax; whether it's a read or a write depends purely on whether the bracket expression sits on the left or right side of `=`.

## 2. Why & when

Direct indexed access is the single most fundamental array operation — every algorithm that works with arrays (searching, sorting, summing, transforming) ultimately reduces to reading and writing individual elements by index:

- **Random access in constant time** — unlike a linked list, an array lets you jump straight to element `500` without walking through elements `0` to `499` first, because the array's memory layout lets the index be turned directly into a memory address.
- **In-place updates** — modifying `array[i] = newValue` changes the array itself, with no need to build a new array, which matters for performance when working with large datasets.
- **Building blocks for loops** — virtually every `for` loop over an array (see the next topic) is just repeated indexed access with a changing index variable.

You reach for direct indexing whenever you know exactly *which* position you need — the third element, the last element, the element matching a computed offset — as opposed to searching for a value by content, which needs a loop or a library method.

## 3. Core concept

```java
public class AccessDemo {
    public static void main(String[] args) {
        int[] temperatures = { 68, 72, 75, 70 };

        System.out.println(temperatures[0]); // 68 — first element
        System.out.println(temperatures[3]); // 70 — last element (length 4, so index 3)

        temperatures[2] = 80; // overwrite the third element
        System.out.println(temperatures[2]); // 80

        int lastIndex = temperatures.length - 1;
        System.out.println(temperatures[lastIndex]); // 70 — safe way to reach the last element
    }
}
```

`temperatures.length - 1` is the idiomatic, safe way to reference the last element regardless of the array's actual size — hard-coding `temperatures[3]` works only as long as the array stays at exactly 4 elements, while `length - 1` keeps working if the array grows or shrinks.

## 4. Diagram

<svg viewBox="0 0 640 140" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="An array of four temperature values with indices 0 through 3 labelled beneath each box, showing index 2 being both read and overwritten">
  <rect x="8" y="8" width="624" height="124" rx="8" fill="#0d1117"/>
  <text x="320" y="24" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">int[] temperatures = { 68, 72, 75, 70 };</text>

  <rect x="140" y="40" width="80" height="40" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="180" y="65" fill="#e6edf3" font-size="14" text-anchor="middle" font-family="monospace">68</text>
  <text x="180" y="96" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">[0]</text>

  <rect x="220" y="40" width="80" height="40" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="260" y="65" fill="#e6edf3" font-size="14" text-anchor="middle" font-family="monospace">72</text>
  <text x="260" y="96" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">[1]</text>

  <rect x="300" y="40" width="80" height="40" rx="4" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="340" y="65" fill="#79c0ff" font-size="14" text-anchor="middle" font-family="monospace">75 → 80</text>
  <text x="340" y="96" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">[2]</text>

  <rect x="380" y="40" width="80" height="40" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="420" y="65" fill="#e6edf3" font-size="14" text-anchor="middle" font-family="monospace">70</text>
  <text x="420" y="96" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">[3] (last, length-1)</text>

  <text x="340" y="118" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">temperatures[2] = 80; overwrites index 2 in place</text>
</svg>

Reading and writing use the identical `array[index]` syntax; only the position relative to `=` decides which one happens.

## 5. Runnable example

Scenario: tracking a small classroom's quiz scores — starting with plain reads and writes, then extending to compute a class average, then hardening it to safely handle a possibly-invalid index supplied by a user.

### Level 1 — Basic

```java
public class QuizScoresBasic {
    public static void main(String[] args) {
        int[] scores = { 85, 90, 78, 92 };

        System.out.println("First student: " + scores[0]);
        System.out.println("Last student: " + scores[scores.length - 1]);

        scores[1] = 95; // student at index 1 retakes the quiz
        System.out.println("Updated second student: " + scores[1]);
    }
}
```

**How to run:** `java QuizScoresBasic.java`

`scores[0]` and `scores[scores.length - 1]` read the first and last elements; `scores[1] = 95` overwrites the second student's score in place — the array itself changes, no new array is created.

### Level 2 — Intermediate

Same quiz scores, now computing the class average by reading every element via indexed access in a loop.

```java
public class QuizScoresIntermediate {
    public static void main(String[] args) {
        int[] scores = { 85, 90, 78, 92 };

        int sum = 0;
        for (int i = 0; i < scores.length; i++) {
            sum += scores[i]; // read each element by index
        }
        double average = (double) sum / scores.length;

        System.out.println("Class average: " + average);

        scores[2] = scores[2] + 5; // bonus 5 points added to the third student, read-then-write
        System.out.println("After curve, third student: " + scores[2]);
    }
}
```

**How to run:** `java QuizScoresIntermediate.java`

`scores[2] = scores[2] + 5` demonstrates that the right-hand side is fully evaluated (reading the current value) before the assignment (writing the new value) happens — a read and a write combined in one statement, which is how "curving" or incrementing a single element is normally done.

### Level 3 — Advanced

Same scenario, now hardened against an invalid, user-supplied index using an explicit bounds check rather than letting the program crash.

```java
public class QuizScoresAdvanced {

    static int safeGet(int[] scores, int index) {
        if (index < 0 || index >= scores.length) {
            System.out.println("Invalid index " + index + " (valid range 0.." + (scores.length - 1) + ")");
            return -1; // sentinel meaning "no such student"
        }
        return scores[index];
    }

    public static void main(String[] args) {
        int[] scores = { 85, 90, 78, 92 };

        int[] requestedIndices = { 1, 3, 7, -1 };
        for (int index : requestedIndices) {
            int result = safeGet(scores, index);
            if (result != -1) {
                System.out.println("Score at index " + index + " is " + result);
            }
        }
    }
}
```

**How to run:** `java QuizScoresAdvanced.java`

`safeGet` checks `index < 0 || index >= scores.length` *before* touching the array, so an out-of-range index (like `7` or `-1`) is reported cleanly instead of crashing the program — this manual bounds check is exactly what the JVM does internally on every array access, just made explicit and recoverable here instead of throwing.

## 6. Walkthrough

Trace `QuizScoresAdvanced.main` for `requestedIndices = { 1, 3, 7, -1 }`:

**Index 1.** `safeGet(scores, 1)` checks `1 < 0` (false) and `1 >= 4` (false), so the guard doesn't fire. `return scores[1]` returns `90`. `main` prints `"Score at index 1 is 90"`.

**Index 3.** Same checks both false (`3` is the valid last index, since `scores.length - 1 == 3`). Returns `scores[3] == 92`. Prints `"Score at index 3 is 92"`.

**Index 7.** `7 < 0` is false, but `7 >= 4` is true — the guard fires, printing `"Invalid index 7 (valid range 0..3)"` and returning `-1`. Back in `main`, `result == -1`, so the second print is skipped.

**Index -1.** `-1 < 0` is true immediately — the guard fires, printing `"Invalid index -1 (valid range 0..3)"` and returning `-1`. Again the second print is skipped.

```
requestedIndices: [ 1, 3, 7, -1 ]
  1 -> valid  -> scores[1] = 90 -> print "Score at index 1 is 90"
  3 -> valid  -> scores[3] = 92 -> print "Score at index 3 is 92"
  7 -> invalid -> print "Invalid index 7 ..." -> no score line
 -1 -> invalid -> print "Invalid index -1 ..." -> no score line
```

Final console output is exactly the four `println` calls executed above, in that order — two "Score at index" lines and two "Invalid index" lines, interleaved in the order the indices were processed.

## 7. Gotchas & takeaways

> **The first element is always index `0`, and the last element of a length-`n` array is index `n - 1`, never `n`.** Writing `array[array.length]` reaches one slot past the end and throws `ArrayIndexOutOfBoundsException` (covered in a later topic) — a classic off-by-one mistake.

> **`scores[i] = scores[i] + 5` is a read followed by a write, not an atomic operation.** In single-threaded code this is harmless, but if multiple threads modified the same array element concurrently without synchronization, the read-then-write pattern could lose updates.

- `array[index]` reads; `array[index] = value` writes — same syntax, different side of `=`.
- Always use `array.length - 1` for "the last element" instead of a hard-coded number, so the code keeps working if the array's size changes.
- Reading and writing are both constant-time operations — the JVM computes the exact memory address from the index directly, with no searching involved.
- Validate an index before use (`index >= 0 && index < array.length`) whenever it comes from outside the program, such as user input.
