---
card: java
gi: 110
slug: pre-post-decrement
title: Pre/post decrement --
---

## 1. What it is

`--` decreases a variable's value by exactly `1`, mirroring `++` in every respect except direction. **Pre-decrement** (`--x`) decrements first and the expression evaluates to the new (smaller) value; **post-decrement** (`x--`) evaluates to the old value first, and the decrement takes effect immediately after. As with `++`, the distinction only matters when the expression's value is consumed somewhere else in the same statement.

```java
int a = 5;
int b = --a;   // a becomes 4 first, then b is assigned that new value: b == 4, a == 4
int c = 5;
int d = c--;   // d is assigned the OLD value 5 first, then c becomes 4: d == 5, c == 4
```

One extra hazard `--` introduces beyond `++`: decrementing toward and past zero is a very common source of off-by-one bugs in countdown loops and stack/queue "pop" operations, since the boundary condition (`== 0` versus `> 0`) is easy to get backward.

## 2. Why & when

`--` is the standard idiom for countdown loops (`for (int i = n; i > 0; i--)`), and for "consume one and step backward" patterns:

- Draining a resource pool: `remainingPermits--` after handing one out.
- Reverse iteration: `array[--i]` decrements the index first, then accesses the new position — useful when processing a collection from the end backward.
- Popping from a manually managed stack (an array with a `size` field): `stack[--size]` decrements `size` first, then returns the element that is now the new "top."

You must be careful with the boundary: a loop like `while (count-- > 0)` executes its body exactly `count` times (for the original, positive value of `count`) but leaves `count` at `-1` after the loop, not `0` — because the comparison uses the *old* value, but the decrement to `-1` still happens once more inside the final failing check.

## 3. Core concept

```java
public class DecrementDemo {
    public static void main(String[] args) {
        int a = 5;
        int preResult = --a;     // a becomes 4, THEN preResult is assigned 4
        System.out.println("a=" + a + ", preResult=" + preResult);   // a=4, preResult=4

        int c = 5;
        int postResult = c--;    // postResult is assigned 5 (OLD value), THEN c becomes 4
        System.out.println("c=" + c + ", postResult=" + postResult); // c=4, postResult=5

        // Reverse array traversal using pre-decrement
        int[] data = { 10, 20, 30 };
        int i = data.length;
        while (i > 0) {
            System.out.println("data[--i] = " + data[--i]);  // decrements i first, then indexes
        }

        // The countdown-past-zero trap
        int countdown = 3;
        while (countdown-- > 0) {
            System.out.println("Firing! countdown now: " + countdown);  // 2, 1, 0
        }
        System.out.println("Final countdown value: " + countdown);        // -1, not 0!
    }
}
```

## 4. Diagram

<svg viewBox="0 0 700 165" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Post-decrement countdown loop diagram: countdown starts at 3, the loop condition countdown-- greater than 0 checks the old value then decrements, running the body for values 2, 1, 0, and leaving countdown at negative 1 after the loop ends.">
  <rect x="8" y="8" width="684" height="149" rx="8" fill="#0d1117"/>
  <text x="350" y="24" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">while (countdown-- &gt; 0) — the check uses the OLD value, but the decrement still happens</text>

  <rect x="20" y="36" width="150" height="46" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="95" y="54" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="monospace">check: 3 &gt; 0? yes</text>
  <text x="95" y="72" fill="#6db33f" font-size="8" text-anchor="middle" font-family="monospace">countdown → 2, body runs</text>

  <rect x="185" y="36" width="150" height="46" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="260" y="54" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="monospace">check: 2 &gt; 0? yes</text>
  <text x="260" y="72" fill="#6db33f" font-size="8" text-anchor="middle" font-family="monospace">countdown → 1, body runs</text>

  <rect x="350" y="36" width="150" height="46" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="425" y="54" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="monospace">check: 1 &gt; 0? yes</text>
  <text x="425" y="72" fill="#6db33f" font-size="8" text-anchor="middle" font-family="monospace">countdown → 0, body runs</text>

  <rect x="515" y="36" width="150" height="46" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="590" y="54" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="monospace">check: 0 &gt; 0? NO</text>
  <text x="590" y="72" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="monospace">countdown → -1, loop ends</text>

  <text x="350" y="110" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Body ran 3 times (for values 2, 1, 0) — but countdown ends at -1, not 0</text>
</svg>

Even the final, failing check in a `post-decrement > 0` loop still performs its decrement — the loop variable overshoots by one past the exit boundary.

## 5. Runnable example

Scenario: a game's "lives remaining" system where a player loses a life on failure and the game ends at zero — a natural place for the countdown-past-zero pattern to bite, followed by a hardened version and a reverse-array replay feature.

### Level 1 — Basic

```java
public class LivesBasic {
    public static void main(String[] args) {
        int lives = 3;

        while (lives-- > 0) {
            System.out.println("Attempt failed. Lives remaining: " + lives);
        }
        System.out.println("Game over. Final lives value: " + lives);  // -1, surprising if you expected 0
    }
}
```

**How to run:** `java LivesBasic.java`

`lives-- > 0` checks the *current* value of `lives` (starting at `3`) against `0`, and only after that comparison does `lives` actually decrement. So the loop runs for `lives` values `3, 2, 1` (each passing the `> 0` check before decrementing), printing the *post-decrement* values `2, 1, 0`. The final check happens when `lives` is `0`: `0 > 0` is `false`, so the loop stops — but the decrement inside that final, failing check has *already happened*, leaving `lives` at `-1`. A reader expecting `lives` to land cleanly on `0` after the loop is surprised.

### Level 2 — Intermediate

Same lives system, now fixed to keep `lives` at a sensible non-negative value after the loop, and adding a proper "game over" check that treats `0` (not `-1`) as the boundary.

```java
public class LivesIntermediate {

    static boolean attemptFailed(int attempt) {
        return attempt % 2 == 0;  // simulate: even-numbered attempts fail, for demonstration
    }

    public static void main(String[] args) {
        int lives = 3;
        int attempt = 0;

        // Use pre-decrement OR a separate check so `lives` never goes below 0 unexpectedly
        while (lives > 0) {
            attempt++;
            if (attemptFailed(attempt)) {
                lives--;   // decrement as its own statement — no ambiguity about ordering
                System.out.println("Attempt " + attempt + " failed. Lives remaining: " + lives);
            } else {
                System.out.println("Attempt " + attempt + " succeeded.");
            }
        }
        System.out.println("Game over. Final lives value: " + lives);  // exactly 0
    }
}
```

**How to run:** `java LivesIntermediate.java`

The loop condition is now `lives > 0` (checking the value directly, with no embedded decrement), and `lives--` is its own separate statement executed only when a failure actually occurs. This decouples "should the loop continue" from "should we decrement," which removes the ambiguity entirely: the loop exits exactly when `lives` reaches `0`, and it never goes negative, because the decrement only ever happens while `lives > 0` was true at the top of that iteration.

### Level 3 — Advanced

Same game, now replaying the sequence of failed attempts in reverse order using pre-decrement array indexing (`history[--index]`), and demonstrating the equivalent countdown trap for an array-backed stack's `pop` operation, fixed with an explicit empty check.

```java
import java.util.*;

public class LivesAdvanced {

    static int[] stack = new int[10];
    static int stackSize = 0;

    static void push(int value) {
        stack[stackSize++] = value;  // post-increment: store at current size, THEN grow size
    }

    static int pop() {
        if (stackSize == 0) {
            throw new NoSuchElementException("Cannot pop from an empty stack");
        }
        return stack[--stackSize];   // pre-decrement: shrink size FIRST, then return the new top element
    }

    public static void main(String[] args) {
        List<Integer> failedAttempts = new ArrayList<>();
        int lives = 3;
        int attempt = 0;

        while (lives > 0) {
            attempt++;
            boolean failed = (attempt % 2 == 0);
            if (failed) {
                lives--;
                failedAttempts.add(attempt);
                push(attempt);   // record on the stack too, for a "replay in reverse" feature
            }
        }
        System.out.println("Game over after " + attempt + " attempts.");

        // Replay failures in reverse chronological order using pre-decrement indexing
        System.out.println("Replay (most recent failure first):");
        for (int i = failedAttempts.size(); i > 0; ) {
            System.out.println("  Attempt #" + failedAttempts.get(--i));
        }

        // Pop everything off the stack, demonstrating the guarded pop
        System.out.println("Popping stack:");
        while (stackSize > 0) {
            System.out.println("  Popped: " + pop());
        }

        try {
            pop();   // now empty — guarded pop throws instead of using a corrupted --stackSize
        } catch (NoSuchElementException e) {
            System.out.println("Correctly rejected: " + e.getMessage());
        }
    }
}
```

**How to run:** `java LivesAdvanced.java`

`stack[stackSize++] = value` in `push` uses post-increment: the new value is stored at the *current* `stackSize` (the next free slot), and only afterward does `stackSize` grow to reflect the new element — this is the standard "append, then grow" pattern. `stack[--stackSize]` in `pop` uses pre-decrement for the mirror-image reason: `stackSize` must shrink *first* so that it points at the index of the *last actual element* (since `stackSize` normally points one past the last element, matching `push`'s convention), and only then is that index read and returned. The `if (stackSize == 0)` guard in `pop` is essential: without it, `stack[--stackSize]` on an empty stack would decrement `stackSize` to `-1` and then attempt `stack[-1]`, throwing `ArrayIndexOutOfBoundsException` — a confusing, low-level error compared to the clear, intentional `NoSuchElementException` the guard produces instead. The reverse-replay loop `for (int i = failedAttempts.size(); i > 0; )` similarly uses `--i` inside the body (via `get(--i)`) to decrement first and then index, visiting indices `size-1, size-2, ..., 0` — the last element first.

## 6. Walkthrough

Trace `pop()` being called on a stack containing two elements, where `stackSize == 2`:

**Guard check.** `stackSize == 0`? No, `stackSize` is `2`, so the exception is not thrown and execution proceeds to the return statement.

**Pre-decrement.** `--stackSize` decrements `stackSize` from `2` to `1` *before* anything else happens, and the expression `--stackSize` itself evaluates to `1` (the new value).

**Array access.** `stack[1]` reads the element at index `1`, which is the element that was most recently pushed (since `push` had stored it at index `1` when `stackSize` was `1` at the time of that push, then incremented `stackSize` to `2` afterward).

**Return.** That element's value is returned to the caller. `stackSize` remains at its new value, `1`, correctly reflecting that one element remains.

```
Before pop(): stackSize = 2, stack = [A, B, _, _, ...]
                                       0  1

pop():
  guard: stackSize == 0? no
  --stackSize: stackSize becomes 1, expression value = 1
  stack[1] = B  -> return B

After pop(): stackSize = 1, stack = [A, B, _, _, ...]  (B still physically present, but "size" says only A counts)
```

**Why pre-decrement, specifically.** If `pop` used `stack[stackSize--]` (post-decrement) instead, it would read `stack[2]` first — an uninitialized or stale slot one past the actual last element — and only shrink `stackSize` afterward, returning the wrong (or garbage) value. The pre-decrement form is required precisely because `stackSize` conventionally points one past the last valid element, matching how `push`'s post-increment left it.

## 7. Gotchas & takeaways

> **`while (count-- > 0)` leaves `count` at `-1` after the loop, not `0`.** The final, failing check still executes the decrement even though the comparison fails. If you need `count` to land exactly at `0`, check `count > 0` as a plain condition and decrement as a separate statement inside the body.

> **Array-backed stack/queue implementations conventionally pair post-increment `push` with pre-decrement `pop`.** This is because the size field points one past the last valid element — `push` must store first then grow, and `pop` must shrink first then read, to stay consistent with that convention. Always guard `pop` against an empty collection before decrementing, or you will index at `-1`.

- Pre-decrement (`--x`): decrement happens first, expression evaluates to the new value.
- Post-decrement (`x--`): expression evaluates to the old value first, decrement happens as a side effect immediately after.
- Embedding `--` (or `++`) directly inside a loop condition is idiomatic but easily overshoots the boundary by one — separate the check from the decrement when the exact final value matters.
- The classic array-stack pairing is `stack[size++] = value` for push and `stack[--size]` for pop, always guarded by an emptiness check before popping.
