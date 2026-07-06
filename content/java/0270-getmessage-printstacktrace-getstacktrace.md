---
card: java
gi: 270
slug: getmessage-printstacktrace-getstacktrace
title: getMessage() / printStackTrace() / getStackTrace()
---

## 1. What it is

`getMessage()`, `printStackTrace()`, and `getStackTrace()` are three methods inherited from `Throwable` for inspecting an exception after it's been caught. `getMessage()` returns the descriptive string passed to the exception's constructor; `printStackTrace()` prints a full, human-readable trace of exactly where the exception was created and the chain of method calls that led there, straight to the console; `getStackTrace()` returns that same trace as a programmatically inspectable array of `StackTraceElement` objects, rather than printed text.

```java
public class InspectionDemo {
    static void level3() { throw new RuntimeException("something broke"); }
    static void level2() { level3(); }
    static void level1() { level2(); }

    public static void main(String[] args) {
        try {
            level1();
        } catch (RuntimeException e) {
            System.out.println("Message: " + e.getMessage());
            System.out.println("First frame: " + e.getStackTrace()[0]);
            e.printStackTrace(); // prints the FULL trace to standard error
        }
    }
}
```

`e.getMessage()` returns exactly `"something broke"`, the string passed to the constructor; `e.getStackTrace()[0]` gives the innermost frame — where the exception was actually created, inside `level3` — as a `StackTraceElement`; `e.printStackTrace()` prints the entire call chain (`level3` called from `level2`, called from `level1`, called from `main`) directly to the console, formatted for human reading.

## 2. Why & when

These three methods serve different, complementary purposes when responding to or diagnosing a caught exception.

- **`getMessage()` for a short, human-readable summary** — this is what you typically show in a user-facing error message or a concise log line, since it's just the descriptive text without any of the call-chain detail.
- **`printStackTrace()` for full diagnostic output during development and in logs** — it shows exactly where the exception originated, the full sequence of method calls that led there, and, if the exception is chained (the previous topic), the entire "Caused by:" sequence for every underlying cause — invaluable for debugging, though typically directed to a log file rather than shown directly to end users.
- **`getStackTrace()` for programmatic inspection** — when you need to examine the trace's contents in code (say, to check which class or method the exception originated in, for custom logging or monitoring logic), `getStackTrace()` gives you the same data as an array you can iterate over and inspect, rather than pre-formatted text.

Use `getMessage()` for concise summaries meant for humans (users or short log lines); use `printStackTrace()` (or, more commonly in production systems, a logging framework that captures the same information) for full diagnostic detail during development or in application logs; reach for `getStackTrace()` specifically when your code needs to programmatically inspect or filter trace information, rather than just display it.

## 3. Core concept

```java
public class InspectionCore {
    public static void main(String[] args) {
        try {
            Object obj = null;
            obj.toString(); // throws NullPointerException
        } catch (NullPointerException e) {
            StackTraceElement[] trace = e.getStackTrace();
            System.out.println("Exception occurred in method: " + trace[0].getMethodName());
            System.out.println("At line: " + trace[0].getLineNumber());
            System.out.println("In class: " + trace[0].getClassName());
        }
    }
}
```

Each `StackTraceElement` in the array returned by `getStackTrace()` exposes structured accessors — `getMethodName()`, `getLineNumber()`, `getClassName()`, and more — letting code extract exactly the piece of trace information it needs, rather than parsing that information out of `printStackTrace()`'s formatted text output.

## 4. Diagram

<svg viewBox="0 0 600 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="getMessage returns a short descriptive string, printStackTrace prints the full call chain to the console, getStackTrace returns the same information as an inspectable array of StackTraceElement objects">
  <rect x="8" y="8" width="584" height="174" rx="8" fill="#0d1117"/>

  <rect x="30" y="20" width="170" height="60" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="115" y="42" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">getMessage()</text>
  <text x="115" y="60" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">short descriptive String</text>

  <rect x="215" y="20" width="170" height="60" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="300" y="42" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">printStackTrace()</text>
  <text x="300" y="60" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">prints full trace to console</text>

  <rect x="400" y="20" width="170" height="60" rx="6" fill="#1c2430" stroke="#f85149" stroke-width="1.5"/>
  <text x="485" y="42" fill="#f85149" font-size="10" text-anchor="middle" font-family="sans-serif">getStackTrace()</text>
  <text x="485" y="60" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">returns inspectable array</text>

  <text x="300" y="120" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Same underlying trace data, three different ways to access it —</text>
  <text x="300" y="138" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">a short message, printed human-readable text, or a structured array for code to inspect.</text>
</svg>

Three different views onto the same exception data: a short message, printed diagnostic text, and an inspectable array.

## 5. Runnable example

Scenario: an error-reporting utility that formats caught exceptions differently depending on the audience, evolved from simple message display into full diagnostic logging, then hardened with programmatic stack trace inspection used to build a custom, filtered error report.

### Level 1 — Basic

```java
public class InspectionBasic {
    static void riskyOperation() {
        throw new IllegalStateException("operation could not complete");
    }

    public static void main(String[] args) {
        try {
            riskyOperation();
        } catch (IllegalStateException e) {
            System.out.println("User-facing message: " + e.getMessage());
        }
    }
}
```

**How to run:** `java InspectionBasic.java`

`e.getMessage()` gives exactly the descriptive text needed for a short, user-facing summary — no trace details, just the message itself.

### Level 2 — Intermediate

Same operation, now with `printStackTrace()` used alongside `getMessage()`, demonstrating the difference between a short summary and the full diagnostic detail.

```java
public class InspectionIntermediate {
    static void level2() {
        throw new IllegalStateException("operation could not complete");
    }
    static void level1() { level2(); }

    public static void main(String[] args) {
        try {
            level1();
        } catch (IllegalStateException e) {
            System.out.println("=== User-facing summary ===");
            System.out.println(e.getMessage());

            System.out.println("=== Full diagnostic trace (would go to logs) ===");
            e.printStackTrace();
        }
    }
}
```

**How to run:** `java InspectionIntermediate.java`

`e.getMessage()` prints just the short text; `e.printStackTrace()` (writing to standard error, which typically still appears in the terminal alongside standard output) prints the full call chain: `level2` (where the exception was thrown), called from `level1`, called from `main`, each with its exact line number — far more detail than a user-facing message would ever need, but exactly what's useful for debugging.

### Level 3 — Advanced

Same system, now using `getStackTrace()` to build a custom, filtered error report that extracts only the application's own code from the trace (skipping any JDK-internal frames, in this simplified illustration), demonstrating programmatic trace inspection for building tailored diagnostics.

```java
public class InspectionAdvanced {
    static void processPayment() {
        validateAmount(-50); // will fail inside this nested call
    }

    static void validateAmount(int amount) {
        if (amount < 0) throw new IllegalArgumentException("amount cannot be negative: " + amount);
    }

    static String buildCustomReport(Throwable e) {
        StringBuilder report = new StringBuilder();
        report.append("ERROR: ").append(e.getMessage()).append("\n");
        report.append("Trace:\n");

        StackTraceElement[] trace = e.getStackTrace();
        for (int i = 0; i < trace.length; i++) {
            StackTraceElement frame = trace[i];
            report.append("  #").append(i)
                  .append(" ").append(frame.getClassName())
                  .append(".").append(frame.getMethodName())
                  .append(" (line ").append(frame.getLineNumber()).append(")\n");
        }
        return report.toString();
    }

    public static void main(String[] args) {
        try {
            processPayment();
        } catch (IllegalArgumentException e) {
            System.out.print(buildCustomReport(e));
        }
    }
}
```

**How to run:** `java InspectionAdvanced.java`

`buildCustomReport` iterates over the array returned by `getStackTrace()`, extracting each frame's class name, method name, and line number to build a custom-formatted report — this demonstrates the real power of `getStackTrace()` over `printStackTrace()`: full programmatic control over exactly how the trace data is formatted, filtered, or transformed, rather than being limited to the JDK's default printed format.

## 6. Walkthrough

Trace `main` in `InspectionAdvanced` from the initial call through the final report.

**`processPayment()`.** Calls `validateAmount(-50)`.

**`validateAmount(-50)`.** `amount < 0` is `true` (`-50 < 0`), so `IllegalArgumentException("amount cannot be negative: -50")` is thrown. At the moment of construction, the JVM automatically captures the current call stack: the innermost frame is `validateAmount` itself (where `new IllegalArgumentException` was executed), followed by `processPayment` (which called `validateAmount`), followed by `main` (which called `processPayment`).

**The exception propagates up to `main`'s `catch (IllegalArgumentException e)` clause**, which calls `buildCustomReport(e)`.

**Inside `buildCustomReport`.** `report` starts with `"ERROR: amount cannot be negative: -50\n"` followed by `"Trace:\n"`. `e.getStackTrace()` returns the array of three (or more, depending on the JVM) `StackTraceElement`s captured earlier. The loop iterates: for `i = 0`, `frame` is the `validateAmount` frame — appends `"  #0 InspectionAdvanced.validateAmount (line N)\n"` (with `N` being the actual source line where the `throw` statement is). For `i = 1`, `frame` is the `processPayment` frame — appends `"  #1 InspectionAdvanced.processPayment (line M)\n"`. For `i = 2`, `frame` is the `main` frame — appends `"  #2 InspectionAdvanced.main (line K)\n"`. The loop continues for any further frames the JVM captured (which in this simple example would be none beyond `main`, since nothing calls `main` from within the observed program).

**`buildCustomReport` returns the complete `report` string**, which `main` prints with `System.out.print(...)`.

```
processPayment() -> validateAmount(-50)
validateAmount(-50): -50 < 0 -> throws IllegalArgumentException("amount cannot be negative: -50")
  stack captured at throw time: [validateAmount, processPayment, main]

buildCustomReport(e):
  "ERROR: amount cannot be negative: -50"
  "Trace:"
  frame 0: validateAmount (line ...)
  frame 1: processPayment (line ...)
  frame 2: main (line ...)
```

**Final output** (exact line numbers depend on the source file's formatting, but the structure is):
```
ERROR: amount cannot be negative: -50
Trace:
  #0 InspectionAdvanced.validateAmount (line 6)
  #1 InspectionAdvanced.processPayment (line 3)
  #2 InspectionAdvanced.main (line 30)
```

## 7. Gotchas & takeaways

> **`printStackTrace()` writes to standard error (`System.err`) by default, not standard output (`System.out`)** — in a terminal, both typically appear interleaved together, so this distinction is easy to overlook, but it matters when output is redirected: `java MyProgram > output.txt` would capture `System.out.println` output but *not* `printStackTrace()`'s output, which would still appear on the terminal (or need `2>` redirection separately). This is precisely why production systems typically use a dedicated logging framework rather than raw `printStackTrace()` calls, to ensure diagnostic output is captured reliably regardless of how the process's output streams are configured.

> **The stack trace is captured at the moment the exception object is *constructed* (via `new`), not when it is *thrown*** — if you construct an exception object and hold onto it before throwing it later (an unusual but occasionally seen pattern), its stack trace reflects where `new` was called, not where `throw` eventually executes; keeping construction and throwing together (`throw new SomeException(...)`, as in every example here) avoids this potential confusion entirely.

- `getMessage()` returns the short, descriptive string passed to the exception's constructor — suitable for concise, human-readable summaries.
- `printStackTrace()` prints the complete call chain (and any chained causes) directly to standard error, formatted for human reading — the standard tool for development-time and log-file diagnostics.
- `getStackTrace()` returns the same trace data as an array of `StackTraceElement` objects, each exposing class name, method name, and line number, enabling fully programmatic inspection or custom formatting.
- The stack trace is captured when the exception object is constructed (`new`), not when it is thrown — keeping construction and `throw` together avoids any confusion about which call site the trace reflects.
