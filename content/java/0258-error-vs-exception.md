---
card: java
gi: 258
slug: error-vs-exception
title: Error vs Exception
---

## 1. What it is

`Error` and `Exception` are the two direct subclasses of `Throwable` (the previous topic), and they represent fundamentally different categories of failure. An `Exception` represents a condition a well-written program might reasonably anticipate and recover from (invalid input, a missing file, a network timeout); an `Error` represents a serious problem, usually at the level of the JVM or the underlying system itself, that application code generally cannot and should not attempt to recover from.

```java
public class ErrorVsExceptionDemo {
    public static void main(String[] args) {
        try {
            throw new IllegalStateException("recoverable business logic failure");
        } catch (Exception e) {
            System.out.println("Caught and handled: " + e.getMessage());
        }

        try {
            recurse(0); // will eventually throw StackOverflowError
        } catch (StackOverflowError e) {
            System.out.println("Caught an Error (unusual, generally discouraged): " + e.getClass().getSimpleName());
        }
    }

    static void recurse(int depth) { recurse(depth + 1); } // never terminates, exhausts the call stack
}
```

`IllegalStateException` is caught and handled normally, representing a typical recoverable failure; `StackOverflowError` is also technically catchable (since `catch (Error)` or `catch (StackOverflowError e)` works, just like any other `Throwable`), but catching it is unusual and generally discouraged, since it signals the JVM itself has run out of a fundamental resource (stack space) — a state from which meaningful recovery is rarely possible.

## 2. Why & when

The distinction between `Error` and `Exception` exists to communicate, through the type system itself, whether a failure is something application code is expected to handle.

- **`Exception` signals "this is a normal part of doing business"** — invalid user input, a file that doesn't exist, a network call that times out: these are conditions a robust application anticipates and handles gracefully, often with a specific recovery path (retry, show an error message, use a default value).
- **`Error` signals "something is fundamentally wrong with the runtime environment"** — `OutOfMemoryError` (the JVM has exhausted available memory), `StackOverflowError` (unbounded recursion has exhausted the call stack), and `LinkageError` (a class file is incompatible or missing at runtime) all indicate problems at a level where the application's own logic generally cannot meaningfully continue.
- **Catching `Error` is rarely the right response** — since an `Error` usually reflects an unstable JVM state, attempting to "handle" it and continue normal execution can often make things worse (for instance, catching `OutOfMemoryError` and continuing to allocate more memory); the conventional wisdom is to let `Error`s propagate and crash (or be logged and shut down cleanly), rather than trying to recover from them in application logic.

Design your own code to throw `Exception` (checked or unchecked, per the next couple of topics) for conditions you expect calling code might handle; never design a class to throw `Error` yourself (this is reserved for the JVM and truly exceptional platform-level failures), and generally avoid writing `catch (Error e)` or `catch (Throwable t)` in application code, except in narrow, deliberate cases like top-level logging before a controlled shutdown.

## 3. Core concept

```java
public class ErrorVsExceptionCore {
    static int divide(int a, int b) {
        if (b == 0) throw new ArithmeticException("division by zero"); // Exception: recoverable, expected
        return a / b;
    }

    static void triggerOutOfMemory() {
        // Error: NOT something this method should try to prevent or recover from internally
        int[] huge = new int[Integer.MAX_VALUE]; // may throw OutOfMemoryError depending on available heap
    }
}
```

`divide` throws a plain `ArithmeticException` (an `Exception`) for a condition it can anticipate (division by zero) and that calling code can reasonably catch and handle; `triggerOutOfMemory`, by contrast, does nothing special to "throw" an `Error` deliberately — an `OutOfMemoryError`, if it occurs, comes from the JVM itself running out of a fundamental resource, not from application logic choosing to signal a normal, expected failure.

## 4. Diagram

<svg viewBox="0 0 600 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Exception represents recoverable conditions application code should catch and handle, Error represents serious JVM or system level problems application code should generally not attempt to catch and recover from">
  <rect x="8" y="8" width="584" height="154" rx="8" fill="#0d1117"/>

  <rect x="40" y="30" width="240" height="90" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="160" y="52" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">Exception</text>
  <text x="160" y="72" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">invalid input, missing file,</text>
  <text x="160" y="86" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">network timeout</text>
  <text x="160" y="104" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Catch and handle it</text>

  <rect x="320" y="30" width="240" height="90" rx="8" fill="#1c2430" stroke="#f85149" stroke-width="2"/>
  <text x="440" y="52" fill="#f85149" font-size="11" text-anchor="middle" font-family="sans-serif">Error</text>
  <text x="440" y="72" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">OutOfMemoryError,</text>
  <text x="440" y="86" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">StackOverflowError</text>
  <text x="440" y="104" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Usually let it propagate</text>

  <text x="300" y="145" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Same Throwable family, opposite intended response from application code.</text>
</svg>

`Exception` invites recovery; `Error` generally signals a problem application code should not try to recover from.

## 5. Runnable example

Scenario: a data-processing routine that must distinguish recoverable input problems from a genuinely catastrophic runtime failure, evolved from simple exception handling into a demonstration of an actual `StackOverflowError` and why catching it is different from catching an ordinary `Exception`.

### Level 1 — Basic

```java
public class ErrorVsExceptionBasic {
    static int processValue(String input) {
        if (input == null || input.isBlank()) {
            throw new IllegalArgumentException("value must not be blank"); // Exception: expected, recoverable
        }
        return Integer.parseInt(input);
    }

    public static void main(String[] args) {
        try {
            System.out.println(processValue(""));
        } catch (Exception e) {
            System.out.println("Handled recoverable failure: " + e.getMessage());
        }
    }
}
```

**How to run:** `java ErrorVsExceptionBasic.java`

`processValue("")` throws `IllegalArgumentException`, a normal, expected `Exception` — the program catches it, logs a friendly message, and continues running normally, exactly the kind of graceful recovery `Exception` is designed to support.

### Level 2 — Intermediate

Same idea, now demonstrating a genuine `StackOverflowError` triggered by unbounded recursion, caught (unusually) just to inspect it — highlighting the qualitative difference in what this kind of failure represents compared to the `Exception` case above.

```java
public class ErrorVsExceptionIntermediate {
    static int processValue(String input) {
        if (input == null || input.isBlank()) {
            throw new IllegalArgumentException("value must not be blank");
        }
        return Integer.parseInt(input);
    }

    static int countDown(int n) {
        if (n <= 0) return 0;
        return 1 + countDown(n); // BUG: never decreases -- infinite recursion, will overflow the stack
    }

    public static void main(String[] args) {
        try {
            System.out.println(processValue(""));
        } catch (Exception e) {
            System.out.println("Handled recoverable failure: " + e.getMessage());
        }

        try {
            countDown(5); // triggers unbounded recursion due to the bug above
        } catch (StackOverflowError e) {
            System.out.println("Caught a serious Error: " + e.getClass().getSimpleName()
                + " (the program's logic is fundamentally broken here, not just facing bad input)");
        }
    }
}
```

**How to run:** `java ErrorVsExceptionIntermediate.java`

`countDown` has a genuine bug (it calls itself with the same `n`, never decreasing toward the base case), so it recurses until the JVM's call stack is exhausted, throwing `StackOverflowError` — unlike the `IllegalArgumentException` case, this isn't "bad input" the caller provided; it's a defect in the program's own logic, which is precisely the qualitative difference `Error` is meant to signal.

### Level 3 — Advanced

Same routine, now demonstrating the recommended real-world pattern: catch specific `Exception` types for recovery, but let `Error`s propagate uncaught (shown by removing the `StackOverflowError` catch and instead documenting why), while still safely reporting on overall success versus failure counts.

```java
public class ErrorVsExceptionAdvanced {
    static int processValue(String input) {
        if (input == null || input.isBlank()) {
            throw new IllegalArgumentException("value must not be blank");
        }
        return Integer.parseInt(input);
    }

    public static void main(String[] args) {
        String[] inputs = { "10", "", "abc", "20" };
        int successCount = 0;
        int failureCount = 0;

        for (String input : inputs) {
            try {
                int result = processValue(input);
                System.out.println("Processed: " + result);
                successCount++;
            } catch (Exception e) { // catches ONLY Exception subtypes -- recoverable, per-item failures
                System.out.println("Skipped invalid input '" + input + "': " + e.getMessage());
                failureCount++;
            }
            // Deliberately NOT catching Error here: if something like OutOfMemoryError occurred,
            // letting it propagate and crash (or be handled at a much higher level, e.g. logging
            // infrastructure) is the correct response -- this loop should not pretend to "recover"
            // from a JVM-level catastrophe on a per-item basis.
        }

        System.out.println("Successes: " + successCount + ", Failures: " + failureCount);
    }
}
```

**How to run:** `java ErrorVsExceptionAdvanced.java`

The loop only catches `Exception`, deliberately leaving any hypothetical `Error` (like `OutOfMemoryError`) completely uncaught — this is the idiomatic, production-quality pattern: handle per-item recoverable failures gracefully and keep processing the rest of the batch, but never pretend a JVM-level catastrophe can be gracefully handled on a per-item basis; if one occurred, the whole program should be allowed to fail loudly rather than silently continue in a possibly-corrupted state.

## 6. Walkthrough

Trace the loop in `ErrorVsExceptionAdvanced.main` over all four inputs.

**`input = "10"`.** `processValue("10")`: not blank, `Integer.parseInt("10")` returns `10`. No exception. Prints `"Processed: 10"`. `successCount` becomes `1`.

**`input = ""`.** `processValue("")`: `input.isBlank()` is `true`, so `IllegalArgumentException("value must not be blank")` is thrown. The `catch (Exception e)` clause catches it (since `IllegalArgumentException` is an `Exception` subclass). Prints `"Skipped invalid input '': value must not be blank"`. `failureCount` becomes `1`.

**`input = "abc"`.** `processValue("abc")`: not blank, `Integer.parseInt("abc")` throws `NumberFormatException` (itself a subclass of `IllegalArgumentException`, itself a subclass of `RuntimeException`, itself a subclass of `Exception`). The `catch (Exception e)` clause catches it. Prints `"Skipped invalid input 'abc': For input string: \"abc\""`. `failureCount` becomes `2`.

**`input = "20"`.** `processValue("20")`: not blank, `Integer.parseInt("20")` returns `20`. No exception. Prints `"Processed: 20"`. `successCount` becomes `2`.

**After the loop.** `successCount` is `2`, `failureCount` is `2`. Prints `"Successes: 2, Failures: 2"`.

```
"10"  -> parses fine        -> "Processed: 10"       successCount=1
""    -> IllegalArgumentException (blank)  -> caught -> failureCount=1
"abc" -> NumberFormatException (not numeric) -> caught -> failureCount=2
"20"  -> parses fine        -> "Processed: 20"       successCount=2

Final: successCount=2, failureCount=2
```

**Final output.**
```
Processed: 10
Skipped invalid input '': value must not be blank
Skipped invalid input 'abc': For input string: "abc"
Processed: 20
Successes: 2, Failures: 2
```
Throughout this entire run, no `Error` was ever thrown or caught — the loop's design deliberately handles only `Exception`, exactly as recommended, leaving the door open for a genuine `Error` to propagate and terminate the program if the runtime environment itself were ever in serious trouble.

## 7. Gotchas & takeaways

> **Catching `Throwable` or `Error` broadly (`catch (Throwable t)` or `catch (Error e)`) in ordinary application code is a well-known anti-pattern** — it can silently swallow serious JVM-level problems (like `OutOfMemoryError`) that the program has no real way to recover from, potentially masking a catastrophic failure and leaving the application running in a corrupted or unpredictable state. Reserve such broad catches for very specific, deliberate infrastructure code (like a top-level logging handler that then rethrows or triggers a clean shutdown).

> **Never design your own application code to throw `Error` or any of its subclasses** — `Error` is conventionally reserved for the JVM itself (and a small number of very low-level libraries) to signal truly exceptional platform conditions; application logic signaling its own failures should always throw an `Exception` (checked or unchecked, as the next two topics detail), never a custom `Error` subclass.

- `Exception` represents conditions application code can reasonably anticipate and recover from; `Error` represents serious, usually JVM- or system-level problems that application code generally should not try to recover from.
- Both extend `Throwable` directly and are technically catchable, but catching `Error` is unusual and generally discouraged outside of narrow, deliberate infrastructure code.
- Design your own thrown failures as `Exception` subtypes; never invent custom `Error` subclasses for ordinary application-level failures.
- A well-designed catch block typically catches `Exception` (or a more specific subtype) explicitly, deliberately leaving `Error`s uncaught so they can propagate and signal a genuine, unrecoverable problem.
