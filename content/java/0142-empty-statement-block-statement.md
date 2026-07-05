---
card: java
gi: 142
slug: empty-statement-block-statement
title: Empty statement & block statement
---

## 1. What it is

An **empty statement** is a lone semicolon `;` that does absolutely nothing — it is syntactically a complete statement with zero effect. A **block statement** is the opposite: `{ ... }`, a sequence of zero or more statements grouped together and treated as a single statement wherever Java expects one (for example, as the body of an `if`, loop, or method). Both are legal anywhere a statement is expected, and both are far more consequential than they look.

```java
if (true);  // <-- empty statement! The semicolon IS the entire if-body.
{
    System.out.println("This always runs — it's not actually inside the if above.");
}
```

```java
{
    int x = 5;
    System.out.println(x);
} // a block statement — groups these two statements into one unit
```

The first example is a classic bug: the semicolon right after `if (true)` is itself a complete, empty statement, so the `if` controls *nothing* — the following braced block is a separate, unconditional block statement that always runs.

## 2. Why & when

The **empty statement** is rarely written on purpose, but it is occasionally useful, and understanding it prevents a nasty class of bug:

- **A `for` loop that does all its work in the header** — `for (int i = 0; array[i] != target; i++);` (finding an index by advancing `i` alone) legitimately has an empty body, because everything happens in the update clause.
- **A stand-in label target** — occasionally a labeled empty statement marks a spot to jump to, though this is uncommon in typical code.

The **block statement** is used constantly and for good reason:

- **Grouping multiple statements** so an `if`, loop, or method has more than one line in its body — without braces, `if`/`for`/`while` only control the single statement immediately following them.
- **Scoping** — variables declared inside a block are local to that block and cease to exist once it ends, which keeps helper variables from leaking into surrounding code.
- **Always using braces, even for single-statement bodies**, is a widely recommended style precisely because it prevents the "empty statement after `if`" trap and makes it safe to add a second line later without accidentally leaving it outside the intended scope.

## 3. Core concept

```java
public class EmptyBlockDemo {
    public static void main(String[] args) {
        // The bug: semicolon makes the if-body empty; the print always runs
        int x = 5;
        if (x > 10);
        {
            System.out.println("Printed unconditionally, regardless of x!");
        }

        // The fix: braces attach the block AS the if's actual body
        if (x > 10) {
            System.out.println("This only prints if x > 10");
        } else {
            System.out.println("x is not greater than 10");
        }

        // A block statement also introduces its own scope
        {
            int local = 99;
            System.out.println("local inside block: " + local);
        }
        // System.out.println(local); // would NOT compile — local is out of scope here
    }
}
```

The first `if` is controlled entirely by the trailing `;` — an empty statement — so the braced block after it is an unrelated, unconditional block statement that always executes, regardless of `x`.

## 4. Diagram

<svg viewBox="0 0 700 175" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Empty statement diagram: if condition followed by a semicolon binds the semicolon as the entire if-body, leaving the braced block that follows as a separate, unconditional statement.">
  <rect x="8" y="8" width="684" height="159" rx="8" fill="#0d1117"/>
  <text x="350" y="24" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">if (x &gt; 10);  { print(...); }  — parsed as TWO separate statements</text>

  <rect x="40" y="45" width="220" height="30" rx="6" fill="#1c2430" stroke="#f85149" stroke-width="2"/>
  <text x="150" y="65" fill="#f85149" font-size="9" text-anchor="middle" font-family="monospace">if (x &gt; 10) ;</text>
  <text x="150" y="90" fill="#f85149" font-size="8" text-anchor="middle" font-family="sans-serif">if-statement #1: body is the EMPTY statement</text>

  <rect x="320" y="45" width="320" height="30" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="480" y="65" fill="#6db33f" font-size="9" text-anchor="middle" font-family="monospace">{ println("unconditional"); }</text>
  <text x="480" y="90" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">statement #2: a SEPARATE block, runs no matter what x is</text>

  <text x="350" y="130" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="sans-serif">The compiler sees no error here — this parses as perfectly valid, unintended Java.</text>
  <text x="350" y="145" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="sans-serif">Always writing braces directly after "if (...)" prevents this trap entirely.</text>
</svg>

The semicolon is a full statement on its own — the block after it is never actually "inside" the `if`.

## 5. Runnable example

Scenario: a threshold-checking utility that logs a warning when a value is too high — starting with the buggy empty-statement version (to see the mistake happen), then fixing it with proper braces, then hardening it with a nested block that demonstrates variable scoping working correctly across multiple guarded sections.

### Level 1 — Basic (the bug, shown deliberately)

```java
public class ThresholdBuggy {
    public static void main(String[] args) {
        int value = 3;
        int threshold = 10;

        if (value > threshold);  // <-- semicolon: this IS the entire if-body (does nothing)
        {
            System.out.println("WARNING: value exceeds threshold!"); // runs unconditionally!
        }
    }
}
```

**How to run:** `java ThresholdBuggy.java`

Even though `value` (`3`) does **not** exceed `threshold` (`10`), this prints the warning anyway — because the `if`'s actual body is the empty statement (the `;`), and the braced block after it is a separate, unconditional block statement with no connection to the `if` at all. This is precisely the trap described in parts 1 and 4, shown here producing an incorrect result.

### Level 2 — Intermediate (the fix)

Same threshold check, now with the semicolon removed and braces correctly attached directly to the `if`, so the block genuinely becomes the `if`'s body.

```java
public class ThresholdFixed {
    public static void main(String[] args) {
        int value = 3;
        int threshold = 10;

        if (value > threshold) {
            System.out.println("WARNING: value exceeds threshold!");
        } else {
            System.out.println("Value is within range.");
        }
    }
}
```

**How to run:** `java ThresholdFixed.java`

Removing the stray semicolon and attaching `{ ... }` directly after `if (value > threshold)` makes the block statement the actual, conditional body of the `if` — now the warning correctly prints only when `value` truly exceeds `threshold`, and with `value = 3`, `threshold = 10`, this prints `"Value is within range."` instead.

### Level 3 — Advanced

Same threshold logic, now checking multiple values with a per-value local variable declared inside each iteration's block — demonstrating that a block statement's local variables are genuinely scoped to that block alone, so the same variable name can be reused safely in each pass without conflict.

```java
public class ThresholdAdvanced {
    public static void main(String[] args) {
        int[] values = { 3, 15, 8, 22 };
        int threshold = 10;
        int warningCount = 0;

        for (int value : values) {
            if (value > threshold) {
                String message = "WARNING: " + value + " exceeds threshold " + threshold; // scoped to this block
                System.out.println(message);
                warningCount++;
            } else {
                String message = "OK: " + value + " is within range"; // a DIFFERENT "message", own scope
                System.out.println(message);
            }
        }

        System.out.println("Total warnings: " + warningCount);
    }
}
```

**How to run:** `java ThresholdAdvanced.java`

Both branches declare a local variable named `message` — this compiles cleanly precisely because each `{ ... }` block statement (the `if` body and the `else` body) has its own scope; the `message` in the `if` block and the `message` in the `else` block are two entirely separate variables that never coexist, since only one branch's block executes on any given pass through the loop. `warningCount`, declared *outside* both blocks, persists correctly across all iterations, unlike `message`, which is recreated fresh (or not at all) on each pass.

## 6. Walkthrough

Trace the loop over `{ 3, 15, 8, 22 }` with `threshold = 10`:

**value = 3.** `3 > 10` is `false`, so the `else` block runs: its own local `message` is declared and set to `"OK: 3 is within range"`, printed, then `message` goes out of scope as the block ends.

**value = 15.** `15 > 10` is `true`, so the `if` block runs instead: a *different* local `message` (same name, separate variable, separate block scope) is set to `"WARNING: 15 exceeds threshold 10"`, printed, and `warningCount` becomes `1`.

**value = 8.** `8 > 10` is `false`; `else` block runs, prints `"OK: 8 is within range"`.

**value = 22.** `22 > 10` is `true`; `if` block runs, prints `"WARNING: 22 exceeds threshold 10"`, `warningCount` becomes `2`.

```
value=3:  3>10 false  -> else block: message="OK: 3 is within range"
value=15: 15>10 true  -> if block:   message="WARNING: 15 exceeds threshold 10"  warningCount=1
value=8:  8>10 false  -> else block: message="OK: 8 is within range"
value=22: 22>10 true  -> if block:   message="WARNING: 22 exceeds threshold 10"  warningCount=2
```

**Final output.** After the loop, `warningCount` is `2`, so the program's last line is `"Total warnings: 2"`, following the four per-value lines printed above.

## 7. Gotchas & takeaways

> **A semicolon directly after an `if`, `for`, or `while` header is a legal, silent empty statement — the compiler will not warn you.** `if (condition);` followed by a braced block on the next line is a classic, hard-to-spot bug: the block runs unconditionally, and the `if` accomplishes nothing at all. Many IDEs and linters flag this pattern specifically because it compiles without any error.

> **A block statement's local variables cease to exist the instant the block ends** — you cannot reference a variable declared inside `{ }` from outside those braces, even in the very next line, which is precisely what allows the same variable name to be reused safely in separate blocks (like the two `message` variables above).

- An empty statement (`;`) is a legal, complete, no-op statement — it becomes dangerous specifically when it accidentally attaches itself as the body of an `if`/loop.
- Always attach `{` directly after an `if`/`for`/`while` header (on the same or next line, with no stray `;` in between) to avoid the empty-statement trap entirely.
- A block statement `{ ... }` groups multiple statements into one and introduces its own variable scope — variables declared inside don't leak outside.
- Reusing a variable name in separate, non-overlapping blocks (like an `if` block and its `else` block) is safe and common, precisely because each block's variables are independently scoped.
