---
card: java
gi: 180
slug: java-util-arrays-copyof-copyofrange
title: java.util.Arrays.copyOf() / copyOfRange()
---

## 1. What it is

`java.util.Arrays.copyOf()` creates a **new array** containing a copy of an existing array's elements, optionally at a different length; `Arrays.copyOfRange()` creates a new array from a specific sub-range `[fromIndex, toIndex)` of an existing array. Both return a brand-new array object, leaving the original completely untouched — unlike `Arrays.sort` or `Arrays.fill`, which modify their input in place.

```java
int[] original = { 1, 2, 3, 4, 5 };

int[] same = java.util.Arrays.copyOf(original, 5);   // exact copy, same length
int[] shorter = java.util.Arrays.copyOf(original, 3); // truncated: {1, 2, 3}
int[] longer = java.util.Arrays.copyOf(original, 7);  // padded: {1, 2, 3, 4, 5, 0, 0}

int[] middle = java.util.Arrays.copyOfRange(original, 1, 4); // {2, 3, 4}, index 4 excluded
```

`copyOf(array, newLength)` truncates if `newLength` is smaller than the original, or pads the extra slots with the type's default value (`0`, `false`, `null`) if `newLength` is larger — it never throws for either case, unlike a manual index-based copy might.

## 2. Why & when

Because arrays have a fixed size once created, "resizing" an array always actually means creating a new one and copying the relevant data across — `copyOf` and `copyOfRange` are the standard library's efficient, well-tested way to do exactly that:

- **Growing a "full" array** — when an array-backed structure runs out of room, allocate a bigger array with `copyOf` and copy the existing data across before adding more (this is literally how `ArrayList` grows its internal array under the hood).
- **Extracting a slice** — `copyOfRange` pulls out a contiguous portion of an array (like "the first 10 results" or "everything after the header") without disturbing the original.
- **Defensive copying** — returning a *copy* of an internal array from a method, rather than the original reference, so callers can't accidentally (or maliciously) mutate your internal state.

Use `copyOf`/`copyOfRange` whenever you need array data in a **new**, independent array — as opposed to `Arrays.sort` or `Arrays.fill`, which intentionally mutate the array you already have.

## 3. Core concept

```java
public class CopyDemo {
    public static void main(String[] args) {
        int[] original = { 10, 20, 30, 40, 50 };

        int[] copy = java.util.Arrays.copyOf(original, original.length);
        copy[0] = 999; // modifying the copy...

        System.out.println(java.util.Arrays.toString(original)); // [10, 20, 30, 40, 50] — unaffected
        System.out.println(java.util.Arrays.toString(copy));     // [999, 20, 30, 40, 50]

        int[] slice = java.util.Arrays.copyOfRange(original, 1, 3); // indices 1,2 only
        System.out.println(java.util.Arrays.toString(slice)); // [20, 30]
    }
}
```

Because `copyOf` allocates a genuinely **new** array, mutating `copy` has no effect whatsoever on `original` — this is the key distinguishing behaviour from something like simply assigning `int[] copy = original;`, which would make `copy` and `original` refer to the exact same array object.

## 4. Diagram

<svg viewBox="0 0 620 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="An original array of five elements, copied into a new independent array of the same length via copyOf, a shorter truncated copy, a longer padded copy, and a middle slice via copyOfRange">
  <rect x="8" y="8" width="604" height="174" rx="8" fill="#0d1117"/>
  <text x="310" y="24" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">original = {10, 20, 30, 40, 50}</text>

  <rect x="180" y="35" width="40" height="26" fill="#1c2430" stroke="#6db33f"/><text x="200" y="53" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="monospace">10</text>
  <rect x="220" y="35" width="40" height="26" fill="#1c2430" stroke="#6db33f"/><text x="240" y="53" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="monospace">20</text>
  <rect x="260" y="35" width="40" height="26" fill="#1c2430" stroke="#6db33f"/><text x="280" y="53" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="monospace">30</text>
  <rect x="300" y="35" width="40" height="26" fill="#1c2430" stroke="#6db33f"/><text x="320" y="53" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="monospace">40</text>
  <rect x="340" y="35" width="40" height="26" fill="#1c2430" stroke="#6db33f"/><text x="360" y="53" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="monospace">50</text>

  <text x="60" y="95" fill="#79c0ff" font-size="10" font-family="sans-serif">copyOf(original, 3):</text>
  <rect x="220" y="82" width="40" height="26" fill="#1c2430" stroke="#79c0ff"/><text x="240" y="100" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="monospace">10</text>
  <rect x="260" y="82" width="40" height="26" fill="#1c2430" stroke="#79c0ff"/><text x="280" y="100" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="monospace">20</text>
  <rect x="300" y="82" width="40" height="26" fill="#1c2430" stroke="#79c0ff"/><text x="320" y="100" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="monospace">30</text>
  <text x="420" y="100" fill="#8b949e" font-size="9" font-family="sans-serif">truncated</text>

  <text x="60" y="135" fill="#79c0ff" font-size="10" font-family="sans-serif">copyOf(original, 7):</text>
  <rect x="220" y="122" width="40" height="26" fill="#1c2430" stroke="#79c0ff"/><text x="240" y="140" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="monospace">10</text>
  <rect x="260" y="122" width="40" height="26" fill="#1c2430" stroke="#79c0ff"/><text x="280" y="140" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="monospace">...</text>
  <rect x="300" y="122" width="40" height="26" fill="#1c2430" stroke="#79c0ff"/><text x="320" y="140" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="monospace">50</text>
  <rect x="340" y="122" width="40" height="26" fill="#1c2430" stroke="#f85149" stroke-dasharray="2,2"/><text x="360" y="140" fill="#f85149" font-size="9" text-anchor="middle" font-family="monospace">0</text>
  <rect x="380" y="122" width="40" height="26" fill="#1c2430" stroke="#f85149" stroke-dasharray="2,2"/><text x="400" y="140" fill="#f85149" font-size="9" text-anchor="middle" font-family="monospace">0</text>
  <text x="480" y="140" fill="#8b949e" font-size="9" font-family="sans-serif">padded with 0</text>

  <text x="60" y="175" fill="#79c0ff" font-size="10" font-family="sans-serif">copyOfRange(original, 1, 3):</text>
  <rect x="300" y="162" width="40" height="26" fill="#1c2430" stroke="#79c0ff"/><text x="320" y="180" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="monospace">20</text>
  <rect x="340" y="162" width="40" height="26" fill="#1c2430" stroke="#79c0ff"/><text x="360" y="180" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="monospace">30</text>
</svg>

Each call to `copyOf`/`copyOfRange` allocates an independent new array; the original is never touched.

## 5. Runnable example

Scenario: managing a small append-only log buffer backed by a fixed-size array — starting with a basic copy that's independent of the original, then extending to grow the buffer via `copyOf` when it fills up, then hardening into a full append operation that also supports extracting the "most recent N entries" via `copyOfRange`.

### Level 1 — Basic

```java
public class LogBufferBasic {
    public static void main(String[] args) {
        String[] original = { "start", "connect", "auth" };

        String[] snapshot = java.util.Arrays.copyOf(original, original.length);
        snapshot[0] = "MODIFIED"; // changing the copy...

        System.out.println("Original: " + java.util.Arrays.toString(original)); // unaffected
        System.out.println("Snapshot: " + java.util.Arrays.toString(snapshot));
    }
}
```

**How to run:** `java LogBufferBasic.java`

`Arrays.copyOf(original, original.length)` allocates a completely new `String[]` with the same contents; changing `snapshot[0]` afterward has no effect on `original`, since they are now two independent array objects.

### Level 2 — Intermediate

Same log idea, now growing a fixed-size buffer with `copyOf` once it becomes full — the standard technique behind resizable, array-backed collections.

```java
public class LogBufferIntermediate {
    public static void main(String[] args) {
        String[] logs = new String[3];
        logs[0] = "start"; logs[1] = "connect"; logs[2] = "auth";

        System.out.println("Full at capacity 3: " + java.util.Arrays.toString(logs));

        logs = java.util.Arrays.copyOf(logs, logs.length * 2); // grow to capacity 6
        logs[3] = "handshake"; // now there's room for a new entry

        System.out.println("Grown to capacity 6: " + java.util.Arrays.toString(logs));
    }
}
```

**How to run:** `java LogBufferIntermediate.java`

`logs = Arrays.copyOf(logs, logs.length * 2)` reassigns `logs` to point at a brand-new, larger array containing the original 3 entries followed by 3 `null`-padded slots — the variable `logs` now refers to a different array object than it did before this line, which is exactly what "growing" an array means in Java.

### Level 3 — Advanced

Same buffer, now as a small class that appends entries (growing the backing array via `copyOf` whenever it fills up) and can return the most recent N entries via `copyOfRange`.

```java
import java.util.Arrays;

public class LogBufferAdvanced {
    private String[] entries = new String[2];
    private int count = 0;

    void append(String entry) {
        if (count == entries.length) {
            entries = Arrays.copyOf(entries, entries.length * 2); // double capacity when full
        }
        entries[count] = entry;
        count++;
    }

    String[] recent(int n) {
        int from = Math.max(0, count - n); // don't go before index 0 if n > count
        return Arrays.copyOfRange(entries, from, count); // only the used portion, never the unused padding
    }

    public static void main(String[] args) {
        LogBufferAdvanced buffer = new LogBufferAdvanced();
        buffer.append("start");
        buffer.append("connect");
        buffer.append("auth");   // triggers a grow: capacity 2 -> 4
        buffer.append("handshake");
        buffer.append("ready");  // triggers another grow: capacity 4 -> 8

        System.out.println("Last 3: " + Arrays.toString(buffer.recent(3)));
        System.out.println("Last 10 (more than exist): " + Arrays.toString(buffer.recent(10)));
    }
}
```

**How to run:** `java LogBufferAdvanced.java`

`recent(n)` uses `copyOfRange(entries, from, count)` — stopping at `count`, not `entries.length` — which is essential since `entries` may have unused, still-`null` padding slots beyond `count` after growing; `Math.max(0, count - n)` prevents `from` from going negative when more entries are requested than actually exist.

## 6. Walkthrough

Trace `buffer.append("auth")` (the third append, which triggers the first grow) and then `buffer.recent(3)` at the end:

**`append("auth")`.** At this point `entries.length` is `2` and `count` is `2` (after "start" and "connect"), so `count == entries.length` is true. `entries = Arrays.copyOf(entries, 4)` allocates a new 4-slot array: `["start", "connect", null, null]`. Then `entries[2] = "auth"` fills the next slot, and `count` becomes `3`.

**Subsequent appends.** `"handshake"` fits in slot 3 without growing (`count` becomes `4`). Appending `"ready"` finds `count == entries.length` (`4 == 4`) again, growing to capacity `8`: `["start","connect","auth","handshake",null,null,null,null]`, then placing `"ready"` at index `4`, making `count = 5`.

**`recent(3)`.** `from = Math.max(0, 5 - 3) = 2`. `Arrays.copyOfRange(entries, 2, 5)` copies indices `2, 3, 4` — `"auth"`, `"handshake"`, `"ready"` — into a new 3-element array, deliberately stopping before the still-`null` padding at indices `5` through `7`.

**`recent(10)`.** `from = Math.max(0, 5 - 10) = Math.max(0, -5) = 0`. `Arrays.copyOfRange(entries, 0, 5)` copies indices `0` through `4` — all 5 real entries, correctly excluding the 3 unused padding slots even though 10 entries were requested.

```
entries (capacity 8, count 5): [start, connect, auth, handshake, ready, null, null, null]
recent(3):  from = max(0, 5-3) = 2  -> copyOfRange(2,5) -> [auth, handshake, ready]
recent(10): from = max(0, 5-10)= 0  -> copyOfRange(0,5) -> [start, connect, auth, handshake, ready]
```

## 7. Gotchas & takeaways

> **`copyOf` and `copyOfRange` always return a new array — they never modify their input.** This is the opposite of `Arrays.sort` and `Arrays.fill`, which mutate in place; mixing up which category a given `Arrays` method falls into is a common source of "why didn't my array change" (or "why did my original array change") confusion.

> **After growing a backing array with `copyOf`, always track the "used length" (like `count` in Level 3) separately from `entries.length`.** The array's capacity and how much of it is actually meaningful data are two different numbers once padding is involved — using `entries.length` where `count` was intended will include stale `null`/`0` padding in results.

- `Arrays.copyOf(array, newLength)` returns a new array: truncated if smaller, zero/`null`-padded if larger.
- `Arrays.copyOfRange(array, from, to)` returns a new array containing only `[from, to)` — `to` is exclusive.
- Both methods leave the original array completely untouched — use them whenever you need independent, new array data.
- When a backing array has been over-allocated (grown), track the actual "used" count separately, and use it (not `.length`) as the boundary for range copies.
