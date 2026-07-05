---
card: java
gi: 182
slug: system-arraycopy
title: System.arraycopy()
---

## 1. What it is

`System.arraycopy()` is a native, highly-optimized method for copying a range of elements from one array into another (or into a different position within the *same* array). Its signature is `System.arraycopy(src, srcPos, dest, destPos, length)`: copy `length` elements from `src` starting at index `srcPos`, into `dest` starting at index `destPos`. It is the low-level primitive that `Arrays.copyOf` and `Arrays.copyOfRange` are themselves built on top of.

```java
int[] source = { 1, 2, 3, 4, 5 };
int[] destination = new int[5];

System.arraycopy(source, 1, destination, 0, 3); // copy 3 elements starting at source[1] into destination starting at [0]
System.out.println(java.util.Arrays.toString(destination)); // [2, 3, 4, 0, 0]
```

Unlike `Arrays.copyOf`, `System.arraycopy` does **not** create a new array — `destination` must already exist and have enough room; `arraycopy` only fills part (or all) of it.

## 2. Why & when

`System.arraycopy` exists as a fast, low-level building block for any operation that needs to move array data around:

- **Shifting elements** — inserting into or removing from the middle of an array requires shifting everything after the gap; `arraycopy` does this shift in one call instead of a manual loop.
- **Copying into a pre-allocated destination** — when you already have a destination array (perhaps passed in by a caller) and just need to fill part of it.
- **Same-array overlapping copies** — `arraycopy` correctly handles the case where `src` and `dest` are the **same array** and the source/destination ranges overlap, something a naive hand-written copy loop can get wrong depending on which direction it iterates.

It's rarely called directly in everyday application code — `Arrays.copyOf`/`copyOfRange` or `ArrayList` cover most common needs — but it's essential to understand it both because those higher-level methods use it internally, and because writing your own array-shifting logic (like inserting into a sorted array) still benefits from calling it directly.

## 3. Core concept

```java
public class ArraycopyDemo {
    public static void main(String[] args) {
        int[] data = { 10, 20, 30, 40, 50 };

        // Shift elements left by one position within the SAME array, overwriting index 0
        System.arraycopy(data, 1, data, 0, 4);
        System.out.println(java.util.Arrays.toString(data)); // [20, 30, 40, 50, 50] — last slot duplicated, needs fixing
    }
}
```

Copying `data` onto itself, shifted by one position, correctly handles the overlap between source and destination ranges — `arraycopy` guarantees correct behaviour here (as if the source were read entirely before any writing began), which a naive forward-iterating loop copying element-by-element would get wrong, overwriting values it hasn't read yet.

## 4. Diagram

<svg viewBox="0 0 620 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="System dot arraycopy taking three elements starting at source index one and placing them starting at destination index zero, shown as an arrow moving a contiguous block of values into a new array">
  <rect x="8" y="8" width="604" height="134" rx="8" fill="#0d1117"/>
  <text x="310" y="24" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">System.arraycopy(source, 1, destination, 0, 3)</text>

  <text x="30" y="55" fill="#8b949e" font-size="10" font-family="sans-serif">source:</text>
  <rect x="90" y="40" width="40" height="28" fill="#1c2430" stroke="#6db33f"/><text x="110" y="59" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="monospace">1</text>
  <rect x="130" y="40" width="40" height="28" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/><text x="150" y="59" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="monospace">2</text>
  <rect x="170" y="40" width="40" height="28" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/><text x="190" y="59" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="monospace">3</text>
  <rect x="210" y="40" width="40" height="28" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/><text x="230" y="59" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="monospace">4</text>
  <rect x="250" y="40" width="40" height="28" fill="#1c2430" stroke="#6db33f"/><text x="270" y="59" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="monospace">5</text>
  <text x="150" y="30" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">srcPos=1, length=3</text>

  <text x="300" y="95" fill="#79c0ff" font-size="14" text-anchor="middle" font-family="sans-serif">↓ copied ↓</text>

  <text x="30" y="125" fill="#8b949e" font-size="10" font-family="sans-serif">destination:</text>
  <rect x="130" y="105" width="40" height="28" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/><text x="150" y="124" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="monospace">2</text>
  <rect x="170" y="105" width="40" height="28" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/><text x="190" y="124" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="monospace">3</text>
  <rect x="210" y="105" width="40" height="28" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/><text x="230" y="124" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="monospace">4</text>
  <rect x="250" y="105" width="40" height="28" fill="#1c2430" stroke="#6db33f"/><text x="270" y="124" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="monospace">0</text>
  <rect x="290" y="105" width="40" height="28" fill="#1c2430" stroke="#6db33f"/><text x="310" y="124" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="monospace">0</text>
  <text x="150" y="98" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">destPos=0</text>
</svg>

`arraycopy` moves a contiguous block of `length` elements from one position to another, in one call.

## 5. Runnable example

Scenario: managing a fixed-capacity task queue backed by an array — starting with a basic copy into a fresh array, then extending to remove the front element by shifting everything left, then hardening into an insert-at-position operation that shifts elements right to make room, handling the overlap correctly.

### Level 1 — Basic

```java
public class TaskQueueBasic {
    public static void main(String[] args) {
        String[] tasks = { "build", "test", "deploy", "monitor" };
        String[] backup = new String[tasks.length];

        System.arraycopy(tasks, 0, backup, 0, tasks.length); // full copy into a pre-existing array

        System.out.println(java.util.Arrays.toString(backup));
    }
}
```

**How to run:** `java TaskQueueBasic.java`

`System.arraycopy(tasks, 0, backup, 0, tasks.length)` copies every element of `tasks` into the already-allocated `backup` array — unlike `Arrays.copyOf`, no new array is created here; `backup` had to already exist with sufficient length.

### Level 2 — Intermediate

Same task queue, now removing the front task by shifting every remaining element one position to the left, using the same array as both source and destination.

```java
public class TaskQueueIntermediate {
    public static void main(String[] args) {
        String[] tasks = { "build", "test", "deploy", "monitor" };

        System.out.println("Removing: " + tasks[0]);

        System.arraycopy(tasks, 1, tasks, 0, tasks.length - 1); // shift everything left by one
        tasks[tasks.length - 1] = null; // clear the now-duplicated last slot

        System.out.println(java.util.Arrays.toString(tasks));
    }
}
```

**How to run:** `java TaskQueueIntermediate.java`

`System.arraycopy(tasks, 1, tasks, 0, tasks.length - 1)` copies indices `1..3` (`"test"`, `"deploy"`, `"monitor"`) into indices `0..2` — since `src` and `dest` are the *same* array and the ranges overlap, `arraycopy` guarantees this works correctly (as if reading the whole source first), leaving the old last element duplicated at the end until it's explicitly cleared with `tasks[tasks.length - 1] = null`.

### Level 3 — Advanced

Same queue, now inserting a new task at a specific position by first shifting elements right to open a gap, then writing the new value into that gap — the reverse direction of the removal above, into a larger destination array.

```java
import java.util.Arrays;

public class TaskQueueAdvanced {

    static String[] insertAt(String[] tasks, int position, String newTask) {
        String[] expanded = new String[tasks.length + 1];
        System.arraycopy(tasks, 0, expanded, 0, position);                    // elements before the gap, unchanged
        expanded[position] = newTask;                                         // the new element
        System.arraycopy(tasks, position, expanded, position + 1,             // elements from the gap onward, shifted right
                          tasks.length - position);
        return expanded;
    }

    public static void main(String[] args) {
        String[] tasks = { "build", "test", "deploy" };

        String[] updated = insertAt(tasks, 1, "lint"); // insert "lint" between "build" and "test"

        System.out.println(Arrays.toString(updated));
    }
}
```

**How to run:** `java TaskQueueAdvanced.java`

Two separate `arraycopy` calls handle the two halves independently: the first preserves everything before the insertion point unchanged, and the second moves everything from the insertion point onward one slot further right in the new, larger array — together they open up exactly one free slot at `position` for `newTask`, without ever needing a manual element-by-element shifting loop.

## 6. Walkthrough

Trace `insertAt({"build", "test", "deploy"}, 1, "lint")`:

**Allocation.** `expanded = new String[4]` (one longer than `tasks`), all slots initially `null`.

**First copy.** `System.arraycopy(tasks, 0, expanded, 0, 1)` copies just index `0` (`"build"`) into `expanded[0]`. `position` is `1`, so only 1 element precedes the gap.

**Insert.** `expanded[1] = "lint"` places the new task directly into the now-open gap.

**Second copy.** `System.arraycopy(tasks, 1, expanded, 2, 2)` copies indices `1` and `2` from `tasks` (`"test"`, `"deploy"`) into `expanded[2]` and `expanded[3]` — `tasks.length - position` is `3 - 1 = 2` elements, correctly matching the remaining two tasks.

```
tasks:    [build, test, deploy]
position = 1

expanded before: [_, _, _, _]
copy tasks[0..0] -> expanded[0]:      [build, _, _, _]
expanded[1] = "lint":                 [build, lint, _, _]
copy tasks[1..2] -> expanded[2..3]:   [build, lint, test, deploy]
```

**Final output.** `Arrays.toString(updated)` prints `"[build, lint, test, deploy]"` — the new task correctly inserted at index `1`, with all original tasks preserved in their relative order around it.

## 7. Gotchas & takeaways

> **`System.arraycopy` never allocates a new array — `dest` must already exist and have room for `destPos + length` elements**, or it throws `ArrayIndexOutOfBoundsException`. If you need a brand-new, appropriately-sized array, allocate it explicitly first (as in `insertAt` above) or use `Arrays.copyOf` instead.

> **`arraycopy` correctly handles overlapping same-array copies** (as in the left-shift removal example), behaving as if the entire source range were read before any destination write happened. A hand-rolled loop copying forward index-by-index would incorrectly overwrite not-yet-read source elements when shifting left onto a lower destination offset that overlaps the source range.

- `System.arraycopy(src, srcPos, dest, destPos, length)` copies `length` elements between existing arrays (or within the same array).
- Unlike `Arrays.copyOf`, it never creates a new array — the destination must already be allocated with enough room.
- It's the underlying primitive that `Arrays.copyOf` and `Arrays.copyOfRange` are implemented with.
- Correctly handles overlapping ranges within the same array, unlike a naive manual copy loop might.
