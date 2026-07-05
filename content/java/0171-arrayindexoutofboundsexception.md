---
card: java
gi: 171
slug: arrayindexoutofboundsexception
title: ArrayIndexOutOfBoundsException
---

## 1. What it is

`ArrayIndexOutOfBoundsException` is a **runtime exception** the JVM throws automatically whenever code tries to read or write an array element at an index that is negative or greater than or equal to the array's `length`. It is thrown *by the language itself* — you never need to write code to trigger it deliberately, and you can't disable the check; every single array access is bounds-checked.

```java
int[] a = { 10, 20, 30 };
System.out.println(a[3]); // throws: Index 3 out of bounds for length 3
```

The valid index range for an array of length `n` is `0` through `n - 1` inclusive — `a[3]` on a length-3 array is exactly one past the end, the single most common way this exception gets thrown.

## 2. Why & when

The JVM enforces bounds checking on **every** array access as a core memory-safety guarantee — without it, an out-of-range index could read or corrupt memory belonging to something else entirely, a class of bug ("buffer overflow") that has caused serious security vulnerabilities in languages without automatic bounds checking (like C).

- **It shows up whenever a loop's bounds are wrong** — using `<=` instead of `<` against `.length`, or starting from `1` instead of `0`.
- **It shows up when an index is computed** — from user input, from another array's length, or from arithmetic that can go negative or too large.
- **It's a `RuntimeException`**, meaning the compiler does not force you to catch it — most of the time the right response is to *prevent* it (validate the index before accessing), not to catch it after the fact, though catching is appropriate at a boundary where bad input might legitimately arrive (like the earlier `safeGet` example).

## 3. Core concept

```java
public class OutOfBoundsDemo {
    public static void main(String[] args) {
        int[] a = { 1, 2, 3 };

        try {
            System.out.println(a[3]); // one past the end
        } catch (ArrayIndexOutOfBoundsException e) {
            System.out.println("Caught: " + e.getMessage());
        }

        try {
            System.out.println(a[-1]); // negative index
        } catch (ArrayIndexOutOfBoundsException e) {
            System.out.println("Caught: " + e.getMessage());
        }
    }
}
```

Both a too-large index (`3` on a length-3 array) and a negative index (`-1`) trigger the same exception type — the JVM's bounds check is simply `index < 0 || index >= length`, and either half failing throws.

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="An array of three valid slots at indices 0 1 2, with index 3 shown just past the end triggering an exception, and index minus 1 shown just before the start also triggering an exception">
  <rect x="8" y="8" width="624" height="134" rx="8" fill="#0d1117"/>
  <text x="320" y="22" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">int[] a = { 1, 2, 3 };  valid indices: 0, 1, 2</text>

  <rect x="60" y="60" width="16" height="36" rx="3" fill="#1c2430" stroke="#f85149" stroke-width="1.5" stroke-dasharray="3,2"/>
  <text x="68" y="112" fill="#f85149" font-size="9" text-anchor="middle" font-family="sans-serif">a[-1]</text>

  <rect x="180" y="60" width="60" height="36" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="210" y="82" fill="#e6edf3" font-size="13" text-anchor="middle" font-family="monospace">1</text>
  <text x="210" y="112" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">[0]</text>

  <rect x="240" y="60" width="60" height="36" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="270" y="82" fill="#e6edf3" font-size="13" text-anchor="middle" font-family="monospace">2</text>
  <text x="270" y="112" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">[1]</text>

  <rect x="300" y="60" width="60" height="36" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="330" y="82" fill="#e6edf3" font-size="13" text-anchor="middle" font-family="monospace">3</text>
  <text x="330" y="112" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">[2]</text>

  <rect x="360" y="60" width="60" height="36" rx="4" fill="none" stroke="#f85149" stroke-width="1.5" stroke-dasharray="3,2"/>
  <text x="390" y="112" fill="#f85149" font-size="9" text-anchor="middle" font-family="sans-serif">a[3] — past end</text>
</svg>

Both edges beyond the valid range (`0` to `length - 1`) throw `ArrayIndexOutOfBoundsException`.

## 5. Runnable example

Scenario: reading a fixed-size buffer of the last N page views — starting with an example that crashes on a bad index, then extending to prevent the crash with a bounds check, then hardening into a circular-index approach that never throws regardless of how large or negative the requested offset is.

### Level 1 — Basic

```java
public class PageViewsBasic {
    public static void main(String[] args) {
        String[] lastPages = { "/home", "/about", "/contact" };

        int requested = 5; // deliberately out of range
        System.out.println(lastPages[requested]); // throws ArrayIndexOutOfBoundsException
    }
}
```

**How to run:** `java PageViewsBasic.java`

Running this prints a stack trace ending in `Exception in thread "main" java.lang.ArrayIndexOutOfBoundsException: Index 5 out of bounds for length 3` and the program terminates — this is exactly the bug this topic is about.

### Level 2 — Intermediate

Same scenario, now guarding the access with an explicit bounds check so a bad index is reported instead of crashing the whole program.

```java
public class PageViewsIntermediate {
    public static void main(String[] args) {
        String[] lastPages = { "/home", "/about", "/contact" };

        int[] requests = { 0, 5, 2, -1 };
        for (int requested : requests) {
            if (requested < 0 || requested >= lastPages.length) {
                System.out.println("Index " + requested + " is out of range (0.." + (lastPages.length - 1) + ")");
            } else {
                System.out.println("Page: " + lastPages[requested]);
            }
        }
    }
}
```

**How to run:** `java PageViewsIntermediate.java`

The `if (requested < 0 || requested >= lastPages.length)` guard runs *before* the array access, so invalid requests (`5` and `-1`) print a clear message instead of throwing — the program now keeps running through all four requests instead of dying on the first bad one.

### Level 3 — Advanced

Same scenario, now using modular arithmetic to turn *any* integer, however large or negative, into a valid index — useful for a circular buffer where "index 5" on a 3-element buffer should wrap around rather than be rejected.

```java
public class PageViewsAdvanced {

    static String getCircular(String[] pages, int requested) {
        int size = pages.length;
        int wrapped = ((requested % size) + size) % size; // handles negative requested correctly
        return pages[wrapped];
    }

    public static void main(String[] args) {
        String[] lastPages = { "/home", "/about", "/contact" };

        int[] requests = { 0, 5, 2, -1, -4 };
        for (int requested : requests) {
            System.out.println(requested + " -> " + getCircular(lastPages, requested));
        }
    }
}
```

**How to run:** `java PageViewsAdvanced.java`

`((requested % size) + size) % size` first computes `requested % size`, which in Java can be **negative** when `requested` is negative (e.g. `-1 % 3` is `-1`, not `2`) — adding `size` and taking `% size` again shifts that result back into the valid `0..size-1` range, so every possible `int` maps to a legal index and `ArrayIndexOutOfBoundsException` becomes structurally impossible inside `getCircular`.

## 6. Walkthrough

Trace `getCircular(lastPages, -1)` from `PageViewsAdvanced`:

**Step 1 — plain modulo.** `size` is `3`. `requested % size` is `-1 % 3`. In Java, the result of `%` takes the sign of the *dividend*, so `-1 % 3` is `-1`, not `2` as it would be in some other languages.

**Step 2 — shift into range.** `(-1) + size` is `(-1) + 3 = 2`.

**Step 3 — final modulo.** `2 % 3` is `2` (already in range, unaffected). So `wrapped = 2`.

**Step 4 — access.** `pages[2]` is `"/contact"`, a perfectly valid index — no exception anywhere in this call.

```
requested = -1, size = 3
requested % size        = -1 % 3  = -1
(-1) + size              = -1 + 3 = 2
2 % size                 = 2 % 3  = 2   -> wrapped index
pages[2] = "/contact"
```

**Full run.** For `requests = { 0, 5, 2, -1, -4 }`, the printed lines are: `0 -> /home` (0 wraps to itself), `5 -> /contact` (5 % 3 = 2), `2 -> /contact` (already in range), `-1 -> /contact` (traced above), `-4 -> /about` (`-4 % 3 = -1`, `-1 + 3 = 2`... wait — trace carefully: `-4 % 3` is `-1` in Java, `-1 + 3 = 2`, `2 % 3 = 2`, so `-4 -> /contact` as well, matching `-1`'s result since `-4` and `-1` differ by exactly one multiple of `3`).

## 7. Gotchas & takeaways

> **`ArrayIndexOutOfBoundsException` is unchecked** (a subclass of `RuntimeException`), so the compiler never forces you to catch it or declare `throws`. That makes it easy to forget about until it happens at runtime — the fix is almost always to validate the index *before* accessing the array, not to wrap every access in `try/catch`.

> **Java's `%` operator can return a negative result** when the left operand is negative (`-1 % 3` is `-1`, not `2`). If you need a true mathematical modulo that's always non-negative (for wrapping an index), use the `((x % n) + n) % n` pattern shown in Level 3.

- The valid index range for a length-`n` array is `0` through `n - 1`; both `index < 0` and `index >= n` throw.
- This exception is thrown automatically by the JVM on *every* array access — there's no way to disable the check.
- Prefer preventing the exception with an explicit bounds check over catching it after the fact, except at genuine input boundaries.
- Off-by-one errors (using `<=` instead of `<` in a loop condition against `.length`) are the single most common cause of this exception.
