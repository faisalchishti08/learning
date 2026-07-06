---
card: java
gi: 345
slug: assert-keyword-assertions
title: assert keyword & assertions
---

## 1. What it is

The `assert` keyword declares a condition that is expected to always be true at that point in the code — `assert condition;` throws an `AssertionError` if `condition` is `false`, or `assert condition : message;` includes a custom message in the thrown error. Critically, assertions are **disabled by default** at runtime — the JVM must be started with the `-ea` (enable assertions) flag for `assert` statements to actually be checked at all; without it, every `assert` statement is silently skipped, as if it weren't there.

```java
public class AssertDemo {
    public static void main(String[] args) {
        int result = compute(5);
        assert result > 0 : "compute() should never return a non-positive value, got " + result;
        System.out.println("Result: " + result);
    }

    static int compute(int input) {
        return input * 2;
    }
}
```

**How to run with assertions enabled:** `java -ea AssertDemo.java` — without `-ea`, the `assert` line is simply skipped regardless of what `compute()` returns.

## 2. Why & when

Assertions exist to document and check internal invariants — conditions that should be impossible to violate if the code is correct — as a debugging and development-time safety net, distinct from normal exception handling for conditions that *can* legitimately occur (like invalid user input, which should be checked unconditionally, not via `assert`).

- **Checking internal invariants during development** — a private helper method's precondition, a loop invariant, or a postcondition that should always hold if the surrounding logic is correct.
- **Documenting assumptions in code** — an `assert` statement doubles as executable documentation: "at this point, this condition must be true," which is more precise and more likely to be kept up to date than a comment saying the same thing.
- **Catching logic bugs early during testing** — running tests with `-ea` enabled surfaces violated invariants immediately, rather than letting a corrupted state silently propagate further before eventually causing a harder-to-diagnose failure.

Because assertions are off by default in production (`java` without `-ea`), **never** use `assert` to validate anything that must always be checked — argument validation for public APIs, user input, or any condition where skipping the check would be a real security or correctness problem. Use ordinary `if` checks and exceptions (like `IllegalArgumentException`) for those; reserve `assert` strictly for internal invariants that should be impossible to violate in correct code.

## 3. Core concept

```java
public class AssertCore {
    public static void main(String[] args) {
        System.out.println("Assertions enabled? " + isAssertionsEnabled());
        int[] data = {5, 3, 8, 1};
        int max = findMax(data);
        assert max == 8 : "Expected max to be 8, got " + max;
        System.out.println("Max: " + max);
    }

    static boolean isAssertionsEnabled() {
        boolean enabled = false;
        assert enabled = true; // side-effecting assert -- only "runs" if assertions are enabled
        return enabled;
    }

    static int findMax(int[] data) {
        int max = data[0];
        for (int value : data) if (value > max) max = value;
        return max;
    }
}
```

**How to run:** `java -ea AssertCore.java` (also try without `-ea` to see the difference)

The `isAssertionsEnabled()` trick exploits the fact that the `assert` statement's expression is only evaluated when assertions are active — with `-ea`, the assignment `enabled = true` actually executes as a side effect of evaluating the assert condition; without `-ea`, that line never runs at all and `enabled` stays `false`.

## 4. Diagram

<svg viewBox="0 0 600 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="assert statements are entirely skipped unless the JVM is started with -ea; with -ea, a false condition throws AssertionError">
  <rect x="8" y="8" width="584" height="134" rx="8" fill="#0d1117"/>
  <rect x="20" y="30" width="260" height="40" rx="6" fill="#1c2430" stroke="#8b949e"/>
  <text x="150" y="55" fill="#8b949e" font-size="10" text-anchor="middle">java Program (no -ea)</text>
  <text x="20" y="90" fill="#8b949e" font-size="9">assert statements are completely skipped, as if absent</text>

  <rect x="320" y="30" width="260" height="40" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="450" y="55" fill="#6db33f" font-size="10" text-anchor="middle">java -ea Program</text>
  <text x="320" y="90" fill="#8b949e" font-size="9">condition checked; false -&gt; AssertionError thrown</text>
</svg>

## 5. Runnable example

Scenario: a small binary search helper, evolved from one with no invariant checking, into one asserting its preconditions and postconditions with `assert`, into a production-style version that clearly separates assertion-checked internal invariants from always-enforced public-input validation.

### Level 1 — Basic

```java
public class BinarySearchBasic {
    public static void main(String[] args) {
        int[] sorted = {1, 3, 5, 7, 9, 11};
        System.out.println("Index of 7: " + search(sorted, 7));
        System.out.println("Index of 4: " + search(sorted, 4));
    }

    static int search(int[] array, int target) {
        int lo = 0, hi = array.length - 1;
        while (lo <= hi) {
            int mid = (lo + hi) / 2;
            if (array[mid] == target) return mid;
            else if (array[mid] < target) lo = mid + 1;
            else hi = mid - 1;
        }
        return -1;
    }
}
```

**How to run:** `java BinarySearchBasic.java`

This has no internal checks at all — if the caller passed an unsorted array (violating binary search's fundamental precondition), the method would silently return wrong or misleading results with no indication anything was wrong.

### Level 2 — Intermediate

```java
public class BinarySearchIntermediate {
    public static void main(String[] args) {
        int[] sorted = {1, 3, 5, 7, 9, 11};
        System.out.println("Index of 7: " + search(sorted, 7));
        System.out.println("Index of 4: " + search(sorted, 4));
    }

    static int search(int[] array, int target) {
        assert isSorted(array) : "search() requires a sorted array, got " + java.util.Arrays.toString(array);

        int lo = 0, hi = array.length - 1;
        while (lo <= hi) {
            int mid = (lo + hi) / 2;
            assert mid >= lo && mid <= hi : "mid must stay within [lo, hi]"; // loop invariant
            if (array[mid] == target) return mid;
            else if (array[mid] < target) lo = mid + 1;
            else hi = mid - 1;
        }
        return -1;
    }

    static boolean isSorted(int[] array) {
        for (int i = 1; i < array.length; i++) if (array[i] < array[i - 1]) return false;
        return true;
    }
}
```

**How to run:** `java -ea BinarySearchIntermediate.java`

The precondition (`isSorted`) and loop invariant (`mid` staying in bounds) are now checked when assertions are enabled — running with `-ea` against a genuinely unsorted array would immediately throw `AssertionError` with a clear diagnostic message, instead of silently returning a wrong answer.

### Level 3 — Advanced

```java
public class BinarySearchAdvanced {
    public static void main(String[] args) {
        int[] sorted = {1, 3, 5, 7, 9, 11};
        System.out.println("Index of 7: " + search(sorted, 7));

        try {
            search(null, 7); // this MUST be checked unconditionally, not via assert
        } catch (NullPointerException e) {
            System.out.println("Correctly rejected null array: " + e.getMessage());
        }
    }

    static int search(int[] array, int target) {
        // Public-input validation: ALWAYS enforced, regardless of -ea, using a real exception.
        if (array == null) throw new NullPointerException("array must not be null");

        // Internal invariant: only checked when assertions are enabled, since a correct
        // caller of this codebase should never be able to violate it.
        assert isSorted(array) : "search() requires a sorted array, got " + java.util.Arrays.toString(array);

        int lo = 0, hi = array.length - 1;
        while (lo <= hi) {
            int mid = lo + (hi - lo) / 2; // avoids potential overflow of (lo + hi) for huge arrays
            assert mid >= lo && mid <= hi : "mid must stay within [lo, hi]";
            if (array[mid] == target) return mid;
            else if (array[mid] < target) lo = mid + 1;
            else hi = mid - 1;
        }
        return -1;
    }

    static boolean isSorted(int[] array) {
        for (int i = 1; i < array.length; i++) if (array[i] < array[i - 1]) return false;
        return true;
    }
}
```

**How to run:** `java -ea BinarySearchAdvanced.java`

This version draws a clear, deliberate line: a `null` array is a condition that absolutely must be checked *regardless* of whether assertions are enabled (an ordinary `if`/`throw`), while the sortedness precondition and the loop invariant — genuine internal correctness assumptions this specific algorithm relies on — are expressed as `assert` statements, which only add overhead during development/testing and vanish entirely (no runtime cost at all) in a default production run.

## 6. Walkthrough

Execution starts in `main`, which first calls `search(sorted, 7)` on the valid, sorted array.

Inside `search`, `array == null` is `false`, so the unconditional null check passes without effect. If run with `-ea`, `assert isSorted(array)` evaluates `isSorted(sorted)`, which returns `true` (the array genuinely is sorted), so this assertion passes silently and execution continues; without `-ea`, this entire line is skipped and never evaluated at all.

The `while` loop begins with `lo=0`, `hi=5`. First iteration: `mid = 0 + (5-0)/2 = 2`; if `-ea` is active, `assert mid >= lo && mid <= hi` checks `2 >= 0 && 2 <= 5`, true, passes silently. `array[2]` is `5`, less than the target `7`, so `lo` becomes `3`. Second iteration: `mid = 3 + (5-3)/2 = 4`; `array[4]` is `9`, greater than `7`, so `hi` becomes `3`. Third iteration: `mid = 3 + (3-3)/2 = 3`; `array[3]` is `7`, matching the target — `search` returns `3` immediately. `main` prints `Index of 7: 3`.

`main` then calls `search(null, 7)` inside a `try` block. This time, `array == null` is `true` — this check runs *unconditionally*, regardless of `-ea` — so `search` immediately throws `NullPointerException("array must not be null")` before ever reaching the `assert isSorted(...)` line or any loop logic. The `catch` block in `main` catches this exception and prints the confirmation message.

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="valid input passes the unconditional null check, then optionally the sortedness assertion, then the loop with an invariant checked each iteration when assertions are enabled; null input is rejected unconditionally before any assertion is reached">
  <rect x="8" y="8" width="624" height="154" rx="8" fill="#0d1117"/>
  <text x="20" y="30" fill="#79c0ff" font-size="10">search(sorted, 7): null-check passes (always) -&gt; assert isSorted (only if -ea) -&gt; loop -&gt; returns 3</text>
  <text x="20" y="55" fill="#8b949e" font-size="10">  each loop iteration: mid computed -&gt; assert bounds check (only if -ea) -&gt; compare -&gt; narrow range</text>
  <text x="20" y="90" fill="#f85149" font-size="10">search(null, 7): null-check FAILS -&gt; NullPointerException thrown immediately</text>
  <text x="20" y="112" fill="#f85149" font-size="10">  (this check runs regardless of -ea -- assertions are never involved in rejecting null)</text>
</svg>

## 7. Gotchas & takeaways

> Never rely on `assert` to enforce a condition that must always hold in production — since assertions are disabled by default (no `-ea` flag), any validation expressed only as an `assert` is silently skipped in a normal `java` run, which is a real security and correctness hazard if used for input validation.

- Assertions are off by default; they must be explicitly enabled with `-ea` (or `-enableassertions`) for `assert` statements to have any effect at all.
- Use `assert` only for internal invariants that should be logically impossible to violate in correct code — use ordinary `if`/`throw` for anything that must always be checked, including all public-API input validation.
- `assert condition : message;` — the message expression is only evaluated if the assertion actually fails, so it's safe to include potentially expensive diagnostic detail there.
- Because assertions can be entirely compiled out of the runtime execution path (when disabled), never put code with necessary side effects inside an `assert` expression — if assertions are off, that code simply never runs.
- Enable assertions during development and testing (`-ea`) to catch violated invariants immediately; the default disabled state in production keeps assertion-checking overhead at zero.
