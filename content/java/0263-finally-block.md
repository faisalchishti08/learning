---
card: java
gi: 263
slug: finally-block
title: finally block
---

## 1. What it is

A `finally` block follows a `try` (and any `catch` clauses) and always runs, no matter what happens inside the `try` block: whether it completes normally, throws an exception that gets caught, throws an exception that doesn't get caught, or even executes a `return` statement. It is the one place in Java guaranteed to execute for cleanup logic, regardless of how the preceding code exits.

```java
public class FinallyBlockDemo {
    public static void main(String[] args) {
        try {
            System.out.println("Trying...");
            throw new RuntimeException("something went wrong");
        } catch (RuntimeException e) {
            System.out.println("Caught: " + e.getMessage());
        } finally {
            System.out.println("Finally always runs, no matter what");
        }
        System.out.println("After the whole try/catch/finally construct");
    }
}
```

All three sections run in order: `"Trying..."` prints, the exception is thrown and caught, `"Caught: something went wrong"` prints, and then — critically — `"Finally always runs, no matter what"` prints as well, before execution finally continues to the line after the entire `try`/`catch`/`finally` construct.

## 2. Why & when

The `finally` block exists to guarantee cleanup code runs regardless of how the preceding logic exits, which matters most for releasing resources that must never be left open or held, even when something goes wrong.

- **Guaranteed resource cleanup** — closing a file handle, a network connection, or a database cursor must happen whether the operation succeeded, failed with a caught exception, or failed with an exception that propagates further; `finally` is the traditional mechanism for ensuring this (though `try-with-resources`, covered in a dedicated topic, is now generally preferred for objects implementing `AutoCloseable`).
- **Running even when an exception is not caught** — if a `try` block's exception is *not* caught by any `catch` clause present, the `finally` block still runs before the exception continues propagating up the call stack; this is the key detail distinguishing `finally` from ordinary code placed after a `try`/`catch`, which would never run in that scenario.
- **Running even through a `return`** — a `return` statement inside a `try` or `catch` block does not immediately exit the method; the `finally` block still executes first, and can even (in unusual, generally discouraged cases) override the return value, which is explored as a gotcha below.

Use a `finally` block for cleanup logic that absolutely must happen regardless of success or failure — releasing locks, closing manually-managed resources, resetting shared state — understanding that it is the one section of code you can rely on to execute even in the presence of uncaught exceptions or early returns.

## 3. Core concept

```java
public class FinallyCore {
    static int riskyOperation(boolean shouldFail) {
        try {
            if (shouldFail) throw new RuntimeException("failure!");
            return 1; // a normal return from inside try
        } finally {
            System.out.println("Cleanup always runs, success or failure"); // ALWAYS executes
        }
    }

    public static void main(String[] args) {
        try {
            System.out.println("Result: " + riskyOperation(false));
        } catch (RuntimeException e) {
            System.out.println("Never reached for this call");
        }

        try {
            System.out.println("Result: " + riskyOperation(true));
        } catch (RuntimeException e) {
            System.out.println("Caught after cleanup: " + e.getMessage());
        }
    }
}
```

The `finally` block inside `riskyOperation` prints its cleanup message in *both* calls — once when the method returns normally (`shouldFail = false`), and again when it throws (`shouldFail = true`) — in the failing case, the `finally` block runs *before* the exception continues propagating out of `riskyOperation` to be caught in `main`.

## 4. Diagram

<svg viewBox="0 0 600 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A finally block runs after try and any catch, regardless of whether the try succeeded, threw a caught exception, threw an uncaught exception, or returned early, before control finally leaves the whole construct">
  <rect x="8" y="8" width="584" height="174" rx="8" fill="#0d1117"/>

  <rect x="40" y="20" width="150" height="35" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="115" y="42" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">try succeeds</text>

  <rect x="40" y="65" width="150" height="35" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="115" y="87" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">try throws, caught</text>

  <rect x="40" y="110" width="150" height="35" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="115" y="132" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">try throws, uncaught</text>

  <line x1="190" y1="37" x2="330" y2="90" stroke="#8b949e" stroke-width="1.5"/>
  <line x1="190" y1="82" x2="330" y2="90" stroke="#8b949e" stroke-width="1.5"/>
  <line x1="190" y1="127" x2="330" y2="90" stroke="#8b949e" stroke-width="1.5"/>

  <rect x="330" y="65" width="230" height="50" rx="6" fill="#1c2430" stroke="#f85149" stroke-width="2"/>
  <text x="445" y="90" fill="#f85149" font-size="10" text-anchor="middle" font-family="sans-serif">finally — ALWAYS runs</text>
  <text x="445" y="106" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">then original outcome resumes</text>

  <text x="300" y="150" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Every path through try/catch converges on finally before the construct truly exits.</text>
</svg>

Every possible outcome of a `try` block converges on the `finally` block before the construct finally exits.

## 5. Runnable example

Scenario: a simulated resource handle that must always be released, evolved from a basic guaranteed cleanup into a case showing `finally` running even with an uncaught exception, then hardened into a demonstration of the notorious `finally`-overriding-`return` pitfall (shown as something to avoid, not to imitate).

### Level 1 — Basic

```java
public class FinallyBasic {
    static class Resource {
        boolean open = true;
        void use() { System.out.println("Using the resource"); }
        void close() { open = false; System.out.println("Resource closed"); }
    }

    public static void main(String[] args) {
        Resource resource = new Resource();
        try {
            resource.use();
        } finally {
            resource.close(); // guaranteed to run, releasing the resource
        }
        System.out.println("Resource still open? " + resource.open);
    }
}
```

**How to run:** `java FinallyBasic.java`

`resource.close()` inside `finally` runs immediately after `use()` completes, guaranteeing the resource is released before the program continues — here nothing failed, but the guarantee holds regardless.

### Level 2 — Intermediate

Same resource idea, now with an operation that fails, demonstrating that `finally` still runs the cleanup even when the exception is never caught at all — it propagates out of `main` after the `finally` block has already executed.

```java
public class FinallyIntermediate {
    static class Resource {
        boolean open = true;
        void use(boolean shouldFail) {
            if (shouldFail) throw new RuntimeException("operation failed mid-use");
            System.out.println("Using the resource successfully");
        }
        void close() { open = false; System.out.println("Resource closed"); }
    }

    public static void main(String[] args) {
        Resource resource = new Resource();
        try {
            resource.use(true); // will throw
        } finally {
            resource.close(); // STILL runs, even though the exception below is never caught in this program
        }
        System.out.println("This line never runs — the exception propagates past it");
    }
}
```

**How to run:** `java FinallyIntermediate.java`

`resource.close()` prints `"Resource closed"` *before* the uncaught `RuntimeException` terminates the program with a printed stack trace — the final `System.out.println` never runs, but the cleanup in `finally` unquestionably did, demonstrating that `finally` runs even when no `catch` clause is present at all to handle the exception.

### Level 3 — Advanced

Same resource idea, now demonstrating the classic, discouraged pitfall where a `return` inside a `finally` block silently overrides a `return` from the `try` block — shown deliberately as an anti-pattern to recognize and avoid, followed by the corrected version.

```java
public class FinallyAdvanced {
    // ANTI-PATTERN: a return inside finally silently discards the try block's return value and any exception
    static int brokenOperation() {
        try {
            System.out.println("Attempting operation...");
            throw new RuntimeException("this exception will be SWALLOWED"); // never actually propagates!
        } finally {
            return -1; // this return WINS, silently discarding the exception above entirely
        }
    }

    // CORRECT: finally only performs cleanup, never returns or throws on its own
    static int correctOperation() {
        try {
            System.out.println("Attempting operation...");
            throw new RuntimeException("this exception propagates normally");
        } finally {
            System.out.println("Cleanup runs, but does not interfere with the exception");
        }
    }

    public static void main(String[] args) {
        System.out.println("Broken operation result: " + brokenOperation()); // -1, exception silently lost

        try {
            correctOperation();
        } catch (RuntimeException e) {
            System.out.println("Correctly caught: " + e.getMessage());
        }
    }
}
```

**How to run:** `java FinallyAdvanced.java`

In `brokenOperation`, the `RuntimeException` thrown inside `try` is in the process of propagating when the `finally` block executes its own `return -1;` — this `return` inside `finally` takes over completely, discarding the pending exception entirely and silently returning `-1` instead, which is why `brokenOperation()` never actually throws, despite clearly containing a `throw` statement; `correctOperation`, which only performs side-effecting cleanup in `finally` without a `return` or `throw` of its own, lets the original exception propagate normally, as expected.

## 6. Walkthrough

Trace both calls in `FinallyAdvanced.main`.

**`brokenOperation()`.** Prints `"Attempting operation..."`. `throw new RuntimeException(...)` begins propagating — but before the exception can actually leave the method, Java must first run the `finally` block (since one is present). Inside `finally`, `return -1;` executes — and because a `return` inside `finally` unconditionally takes over, it discards the pending exception entirely and immediately returns `-1` as the method's result. The exception is gone forever; nothing about it is logged, caught, or otherwise observable anywhere. `main` prints `"Broken operation result: -1"`.

**`correctOperation()`.** Prints `"Attempting operation..."`. `throw new RuntimeException(...)` begins propagating. The `finally` block runs: it prints `"Cleanup runs, but does not interfere with the exception"`, but performs no `return` or `throw` of its own. Because `finally` completes normally (without overriding anything), the original pending exception is allowed to continue propagating out of `correctOperation`, exactly as it would without a `finally` block at all. Back in `main`, the `catch (RuntimeException e)` clause catches it: prints `"Correctly caught: this exception propagates normally"`.

```
brokenOperation():
  throws RuntimeException("swallowed") -> begins propagating
  finally: return -1 -> OVERRIDES the pending exception -> exception is discarded, method returns -1

correctOperation():
  throws RuntimeException("propagates normally") -> begins propagating
  finally: prints cleanup message, no return/throw -> does NOT interfere
  -> original exception continues propagating -> caught in main
```

**Final output.**
```
Attempting operation...
Broken operation result: -1
Attempting operation...
Cleanup runs, but does not interfere with the exception
Correctly caught: this exception propagates normally
```
Notice that `brokenOperation`'s exception message never appears anywhere in the output at all — it was silently discarded the moment `finally` executed its own `return`, which is exactly why this pattern is considered a serious pitfall: real failures can vanish without a trace.

## 7. Gotchas & takeaways

> **A `return` (or `throw`) statement inside a `finally` block unconditionally overrides any pending `return` value or in-flight exception from the `try`/`catch` block, silently discarding it** — as `brokenOperation` demonstrated, an exception that was actively propagating can be completely swallowed without a trace, replaced by whatever the `finally` block returns instead. Never put a `return` or `throw` inside a `finally` block; reserve `finally` strictly for side-effecting cleanup code (closing resources, releasing locks) that does not alter control flow.

> **`finally` runs even if the `try` or `catch` block contains a `return` statement** — the `return`'s value is computed and "remembered," the `finally` block runs in full, and only then does the method actually return that remembered value (unless `finally` itself overrides it, as just described) — this is why `resource.close()` in the basic example is guaranteed to run even in methods that return a value directly from inside `try`.

- A `finally` block always runs after `try` (and any `catch`), regardless of whether the `try` succeeded, threw a caught exception, threw an uncaught exception, or executed a `return`.
- It is the standard place for guaranteed cleanup logic (closing resources, releasing locks) that must happen no matter how the preceding code exits.
- `finally` runs even when no `catch` clause handles the exception at all — cleanup happens before the exception continues propagating up the call stack.
- Never place a `return` or `throw` inside a `finally` block — doing so silently overrides and discards any pending return value or in-flight exception from the `try`/`catch`, a serious and well-known pitfall.
