---
card: java
gi: 1042
slug: debugging-ide-debugger-jdb-breakpoints
title: "Debugging (IDE debugger, jdb, breakpoints)"
---

## 1. What it is

A Java debugger pauses a running program at a chosen **breakpoint** — a specific line of code — and lets you inspect exactly what's happening at that instant: the value of every local variable, the full call stack showing how execution got there, and the ability to step through subsequent lines one at a time, watching values change in real time. IDEs (IntelliJ IDEA, Eclipse, VS Code) provide this through a graphical interface; `jdb` (Java Debugger) is the command-line equivalent, useful when a GUI isn't available (a remote server, a minimal container). Both connect to the JVM through the same underlying mechanism — the Java Debug Wire Protocol (JDWP).

## 2. Why & when

Adding `System.out.println` statements to inspect a bug's cause works, but it requires guessing in advance exactly which variables might matter, re-running the program after every guess, and manually removing the debug prints afterward (or worse, forgetting to). A debugger lets you pause execution *after the bug has already happened* (or right before the suspicious line) and inspect **everything** available at that moment — not just the one variable you thought to print — including variables you didn't know you'd need to check until you were already looking around. Stepping through code line by line, watching the actual control flow and variable state evolve, is often the fastest way to understand *why* a piece of logic produces a wrong result, especially when the wrong branch of an `if`/`else` is being taken for a reason that isn't obvious from reading the source alone.

Reach for a debugger over `println`-based debugging whenever you don't yet know exactly which variable or condition is the problem, or when a bug depends on complex interacting state that's tedious to reconstruct from log output alone. Set a breakpoint at the earliest point you suspect something goes wrong, then step forward from there, inspecting variables at each step, rather than pausing execution far downstream of the actual root cause and having to work backward.

## 3. Core concept

```java
public class OrderTotal {
    static double calculateTotal(double[] prices, double taxRate) {
        double subtotal = 0;
        for (double price : prices) {
            subtotal += price; // <- set a breakpoint HERE to watch subtotal accumulate
        }
        return subtotal * (1 + taxRate);
    }

    public static void main(String[] args) {
        double[] prices = {19.99, 5.50, -2.00}; // a suspicious negative price
        System.out.println(calculateTotal(prices, 0.08));
    }
}
```

```
# jdb equivalent of setting the same breakpoint and stepping:
$ jdb OrderTotal
> stop at OrderTotal:5      # breakpoint at the line "subtotal += price;"
> run
Breakpoint hit: "thread=main", OrderTotal.calculateTotal(), line=5
main[1] print subtotal      # inspect the variable at this exact paused instant
main[1] print price
main[1] next                # step to the next line, then inspect again
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Execution running normally until it hits a breakpoint on a specific line, pausing so the debugger can inspect local variables and the call stack before stepping to the next line">
  <rect x="20" y="70" width="150" height="40" rx="6" fill="#1c2430" stroke="#8b949e"/>
  <text x="95" y="95" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">running normally</text>

  <rect x="220" y="70" width="180" height="40" rx="6" fill="#1c2430" stroke="#f0883e" stroke-width="1.5"/>
  <text x="310" y="95" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">breakpoint hit -- PAUSED</text>

  <rect x="450" y="20" width="170" height="30" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="535" y="40" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">inspect variables</text>
  <rect x="450" y="60" width="170" height="30" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="535" y="80" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">inspect call stack</text>
  <rect x="450" y="100" width="170" height="30" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="535" y="120" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">step to next line</text>

  <line x1="170" y1="90" x2="220" y2="90" stroke="#8b949e" marker-end="url(#a)"/>
  <line x1="400" y1="85" x2="450" y2="35" stroke="#79c0ff" marker-end="url(#a)"/>
  <line x1="400" y1="90" x2="450" y2="75" stroke="#79c0ff" marker-end="url(#a)"/>
  <line x1="400" y1="95" x2="450" y2="115" stroke="#79c0ff" marker-end="url(#a)"/>
  <defs><marker id="a" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

## 5. Runnable example

Scenario: an order total calculator producing an unexpectedly low result, debugged step by step using breakpoints instead of guessing with print statements.

### Level 1 — Basic

```java
// File: OrderTotalBasic.java
public class OrderTotalBasic {
    static double calculateTotal(double[] prices, double taxRate) {
        double subtotal = 0;
        for (double price : prices) {
            subtotal += price;
        }
        return subtotal * (1 + taxRate);
    }

    public static void main(String[] args) {
        double[] prices = {19.99, 5.50, -2.00};
        double total = calculateTotal(prices, 0.08);
        System.out.println("Total: " + total);
    }
}
```

**How to run:** save as `OrderTotalBasic.java`, then `javac OrderTotalBasic.java && java OrderTotalBasic` (JDK 17+).

Expected output:
```
Total: 25.3692
```

This total looks suspiciously low for three items — there's a bug hiding in the input data (a negative price at index 2), but nothing here tells you *where* to look; you'd have to guess which line or variable to inspect.

### Level 2 — Intermediate

```java
// File: OrderTotalIntermediate.java
public class OrderTotalIntermediate {
    static double calculateTotal(double[] prices, double taxRate) {
        double subtotal = 0;
        for (int i = 0; i < prices.length; i++) {
            double price = prices[i];
            // A print statement inserted specifically to inspect this loop --
            // this is the "guess and check" approach a debugger replaces.
            System.out.println("  [debug] index=" + i + " price=" + price + " running subtotal=" + subtotal);
            subtotal += price;
        }
        return subtotal * (1 + taxRate);
    }

    public static void main(String[] args) {
        double[] prices = {19.99, 5.50, -2.00};
        double total = calculateTotal(prices, 0.08);
        System.out.println("Total: " + total);
    }
}
```

**How to run:** save as `OrderTotalIntermediate.java`, then `javac OrderTotalIntermediate.java && java OrderTotalIntermediate` (JDK 17+).

Expected output:
```
  [debug] index=0 price=19.99 running subtotal=0.0
  [debug] index=1 price=5.5 running subtotal=19.99
  [debug] index=2 price=-2.0 running subtotal=25.49
Total: 25.3692
```

The real-world concern added: the debug prints reveal the negative price at `index=2` — but notice this required guessing, in advance, exactly which line and which variables to print, and now these debug lines need to be manually removed (or commented out) once the bug is understood; a debugger achieves the same visibility without permanently modifying the source code at all.

### Level 3 — Advanced

```java
// File: OrderTotalAdvanced.java
public class OrderTotalAdvanced {
    static double calculateTotal(double[] prices, double taxRate) {
        double subtotal = 0;
        for (int i = 0; i < prices.length; i++) {
            double price = prices[i];
            if (price < 0) {
                // SET A BREAKPOINT ON THIS LINE in an IDE (click the gutter next to
                // the line number) or with `jdb`'s `stop at OrderTotalAdvanced:8` --
                // execution pauses here, and you can inspect `i`, `price`, `subtotal`,
                // and even the full `prices` array, all at once, without guessing
                // in advance which variables would matter.
                throw new IllegalArgumentException("negative price at index " + i + ": " + price);
            }
            subtotal += price;
        }
        return subtotal * (1 + taxRate);
    }

    public static void main(String[] args) {
        double[] prices = {19.99, 5.50, -2.00};
        try {
            double total = calculateTotal(prices, 0.08);
            System.out.println("Total: " + total);
        } catch (IllegalArgumentException e) {
            System.out.println("Rejected: " + e.getMessage());
        }
    }
}
```

**How to run:** save as `OrderTotalAdvanced.java`, then `javac OrderTotalAdvanced.java && java OrderTotalAdvanced` (JDK 17+). To debug it interactively instead of just running it, use `jdb OrderTotalAdvanced`, then at the `jdb` prompt: `stop at OrderTotalAdvanced:8`, then `run`, then once the breakpoint hits, `print i`, `print price`, `print subtotal`, and `locals` (to see every local variable at once) — all without modifying the source file.

Expected output (plain `java` run):
```
Rejected: negative price at index 2: -2.0
```

Expected `jdb` session excerpt (interactive; illustrating what inspecting state at the breakpoint looks like):
```
Breakpoint hit: "thread=main", OrderTotalAdvanced.calculateTotal(), line=8
main[1] print i
 i = 2
main[1] print price
 price = -2.0
main[1] print subtotal
 subtotal = 25.49
```

The production-flavored hard case: the validation now fails loudly and explicitly (an `IllegalArgumentException` naming the exact offending index and value) rather than silently producing a wrong total — and a debugger session at the breakpoint on the `throw` line shows every relevant piece of state (`i`, `price`, `subtotal`) simultaneously, at the exact moment the bug condition is detected, with zero source-code modification required to see it.

## 6. Walkthrough

Tracing a `jdb` debugging session against `OrderTotalAdvanced`, breakpoint set at the line containing `throw new IllegalArgumentException(...)`:

1. `jdb OrderTotalAdvanced` starts the JVM under the debugger's control, loading the class but not yet running `main`.
2. `stop at OrderTotalAdvanced:8` registers a breakpoint at line 8 (the `throw` statement) — the JVM will pause execution the instant control reaches this line, rather than executing it immediately.
3. `run` starts actual execution: `main` begins, `prices` is initialized to `{19.99, 5.50, -2.00}`, and `calculateTotal` is called. The `for` loop begins iterating: at `i=0`, `price=19.99`, `price < 0` is `false`, so the loop continues normally (`subtotal` becomes `19.99`); at `i=1`, `price=5.50`, again `false` (`subtotal` becomes `25.49`).
4. At `i=2`, `price=-2.00`, `price < 0` evaluates to `true` — this is the exact moment the breakpoint at line 8 triggers, and the JVM pauses *before* actually executing the `throw` statement, printing `"Breakpoint hit"` along with the current thread and location.
5. At this paused instant, `print i` reports `i = 2`, `print price` reports `price = -2.0`, and `print subtotal` reports `subtotal = 25.49` — all three values are visible simultaneously, in their exact state at the moment the bug condition was detected, without needing to have predicted in advance that all three would be worth inspecting.
6. From here, a real debugging session could continue stepping (`next` or `step`) through the `throw` statement and watch the exception propagate up through `calculateTotal` and into `main`'s `catch` block, observing the exact control-flow path the exception takes — all interactively, with the ability to inspect any additional variable that turns out to matter, unlike a fixed set of `println` statements decided upon before the debugging session even started.

## 7. Gotchas & takeaways

> **Gotcha:** a breakpoint set inside a loop (as in this example) triggers on *every* iteration that reaches it, not just the first — for a loop with many iterations, this can mean repeatedly hitting "continue" many times before reaching the specific iteration you actually care about; a **conditional breakpoint** (supported by most IDEs, expressible as `i == 2` here) pauses only when a specific condition is true, skipping over uninteresting iterations automatically.

- A debugger pauses execution at a breakpoint and exposes every local variable, the call stack, and the ability to step through subsequent lines — all without modifying the source code, unlike `println`-based debugging.
- Set breakpoints at the earliest point you suspect a problem, then step forward, rather than pausing far downstream and working backward from the wrong output.
- `jdb` provides the same core capability (breakpoints, stepping, variable inspection) from the command line, useful when no IDE or GUI is available (a remote server, a minimal container).
- Conditional breakpoints (pausing only when a specified expression is true) avoid the tedium of manually continuing past every uninteresting iteration of a loop or every uninteresting call to a frequently-invoked method.
- Reach for a debugger specifically when you don't yet know which variable or condition is the actual problem — that's exactly the situation where inspecting *everything* available at a pause point beats guessing which values to print in advance.
- Debugging complements, but doesn't replace, [assertions](1027-assertions-assertequals-assertthrows-assertall.md) and [TDD](1034-tdd-basics.md) — a good test suite catches a class of bug before it needs interactive debugging at all, while a debugger remains essential for understanding *why* a specific, already-observed failure happens.
