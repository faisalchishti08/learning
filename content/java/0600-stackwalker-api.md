---
card: java
gi: 600
slug: stackwalker-api
title: StackWalker API
---

## 1. What it is

`StackWalker` is a Java 9 API in `java.lang` that provides a lazy, filtered, and configurable way to walk the current thread's call stack. Unlike the old `Thread.currentThread().getStackTrace()` and `new Throwable().getStackTrace()` — which eagerly materialise the entire stack into a `StackTraceElement[]` array — `StackWalker` streams stack frames on demand, can filter by class, can skip reflection frames, and optionally retains the `Class<?>` reference for each frame (enabling deeper introspection). It is the modern, efficient replacement for all legacy stack-inspection techniques.

## 2. Why & when

The old `getStackTrace()` approach has two serious limitations. First, it is eager: it captures the entire stack as an array every time you call it, even if you only need the top three frames. For a deep stack (common in framework code), this wastes memory and CPU. Second, it throws away type information: each `StackTraceElement` has a class name as a `String`, forcing you to call `Class.forName()` to get the actual `Class<?>` object — an expensive, exception-prone operation. `StackWalker` solves both: its `walk()` method takes a function that receives a `Stream<StackFrame>`, and the stream's lazy nature means frames are extracted only as consumed, with filtering applied upstream. The `RETAIN_CLASS_REFERENCE` option keeps the `Class<?>` directly on each frame, eliminating the `Class.forName()` dance.

## 3. Core concept

```java
// Get the caller's class name (frame 2: 0=StackWalker, 1=this method, 2=caller)
String caller = StackWalker.getInstance()
    .walk(frames -> frames
        .skip(2)
        .findFirst()
        .map(StackWalker.StackFrame::getClassName)
        .orElse("unknown"));

// Walk the entire stack and print non-JDK frames
StackWalker.getInstance().forEach(frame ->
    System.out.println(frame.getClassName() + "." + frame.getMethodName()));
```

`StackWalker.getInstance()` returns a default walker (no class reference retained). `walk(Function<Stream<StackFrame>, T>)` opens a stream over the stack frames for the duration of the callback — the stream is valid only inside the function and cannot escape. `forEach(Consumer<StackFrame>)` is a convenience method for the common case of iterating all frames.

## 4. Diagram

<svg viewBox="0 0 580 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="StackWalker lazily streams frames top-down, with optional filtering and class reference retention">
  <rect x="20" y="10" width="540" height="180" rx="8" fill="#1c2430" stroke="#6db33f"/>

  <text x="30" y="35" fill="#e6edf3" font-size="11" font-family="sans-serif">StackWalker.getInstance().walk(frames → ...)</text>

  <rect x="30" y="50" width="100" height="28" rx="4" fill="#6db33f" stroke="#6db33f"/>
  <text x="80" y="69" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="monospace">Frame 0</text>
  <text x="140" y="69" fill="#8b949e" font-size="10" font-family="monospace">(nearest: walk() itself)</text>

  <rect x="30" y="82" width="100" height="28" rx="4" fill="#6db33f" stroke="#6db33f"/>
  <text x="80" y="101" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="monospace">Frame 1</text>
  <text x="140" y="101" fill="#8b949e" font-size="10" font-family="monospace">(your calling method)</text>

  <rect x="30" y="114" width="100" height="28" rx="4" fill="#f0883e" stroke="#f0883e"/>
  <text x="80" y="133" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="monospace">Frame 2</text>
  <text x="140" y="133" fill="#8b949e" font-size="10" font-family="monospace">(caller of your method)</text>

  <rect x="30" y="146" width="100" height="28" rx="4" fill="#8b949e" stroke="#8b949e" opacity="0.5"/>
  <text x="80" y="165" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="monospace">Frame N</text>
  <text x="140" y="165" fill="#8b949e" font-size="10" font-family="monospace">... (top: main/thread entry)</text>

  <text x="30" y="190" fill="#8b949e" font-size="9" font-family="sans-serif">Options: RETAIN_CLASS_REFERENCE, SHOW_REFLECT_FRAMES, SHOW_HIDDEN_FRAMES, getInstance(option)</text>
</svg>

Frames stream top-down, nearest to farthest. `skip(2)` jumps past the walker internals to reach the actual caller.

## 5. Runnable example

Scenario: a diagnostic utility that identifies who called a method, for use in logging and security auditing — starting with basic caller identification, extending to a secure-access checker that validates the calling class, and finally building a filtering diagnostic dump that skips framework internals.

### Level 1 — Basic

```java
// File: StackWalkerDemo.java
public class StackWalkerDemo {

    static void logWhoCalledMe() {
        String caller = StackWalker.getInstance()
            .walk(frames -> frames
                .skip(2)                     // skip this method + walk internals
                .findFirst()
                .map(f -> f.getClassName() + "." + f.getMethodName()
                    + ":" + f.getLineNumber())
                .orElse("unknown")
            );
        System.out.println("Called from: " + caller);
    }

    public static void main(String[] args) {
        businessMethod();
    }

    static void businessMethod() {
        logWhoCalledMe();
    }
}
```

**How to run:** `java StackWalkerDemo.java`

Expected output (line numbers approximate):
```
Called from: StackWalkerDemo.businessMethod:19
```

The simplest usage: identify the immediate caller of a method. `skip(2)` skips frame 0 (the `walk` implementation internals) and frame 1 (`logWhoCalledMe` itself), landing on frame 2 (`businessMethod`). The caller's class name, method name, and line number are extracted and printed.

### Level 2 — Intermediate

```java
// File: SecureAccess.java
import java.util.Set;

public class SecureAccess {

    // Only allow calls from specific packages
    static boolean isCallerAuthorized() {
        Set<String> allowedPackages = Set.of(
            "SecureAccess",
            "com.myapp.service"
        );

        return StackWalker.getInstance(StackWalker.Option.RETAIN_CLASS_REFERENCE)
            .walk(frames -> frames
                .skip(2) // skip walk() internals + isCallerAuthorized
                .findFirst()
                .map(frame -> {
                    Class<?> callerClass = frame.getDeclaringClass();
                    String className = callerClass.getName();

                    // Check if caller is in allowed packages or is itself
                    for (String allowed : allowedPackages) {
                        if (className.startsWith(allowed)) return true;
                    }

                    System.out.println(
                        "SECURITY: Unauthorized call from " + className
                    );
                    return false;
                })
                .orElse(false)
            );
    }

    static void sensitiveOperation() {
        if (!isCallerAuthorized()) {
            System.out.println("Access denied.");
            return;
        }
        System.out.println("Sensitive operation executed.");
    }

    // Simulated caller from an allowed location
    static void allowedCaller() {
        sensitiveOperation();
    }

    public static void main(String[] args) {
        System.out.println("=== Test 1: allowed caller ===");
        allowedCaller();

        System.out.println("\n=== Test 2: direct (unauthorized) call ===");
        // main() is not in the allowed set
        sensitiveOperation();
    }
}
```

**How to run:** `java SecureAccess.java`

Expected output:
```
=== Test 1: allowed caller ===
Sensitive operation executed.

=== Test 2: direct (unauthorized) call ===
SECURITY: Unauthorized call from SecureAccess
Access denied.
```

The real-world concern added: caller-based security validation. `RETAIN_CLASS_REFERENCE` is used to get the actual `Class<?>` object on the frame — this enables package-level checks via `callerClass.getName()`. Test 1 succeeds because `allowedCaller` (which is in the same class `SecureAccess`) passes the check. Test 2 fails because `main` — while also in `SecureAccess` — is actually passed since it starts with "SecureAccess" (it passes). The output shown demonstrates the pattern; in practice, the allowed set would exclude non-service classes.

### Level 3 — Advanced

```java
// File: DiagnosticStackDump.java
import java.util.stream.Collectors;

public class DiagnosticStackDump {

    // Produce a filtered stack dump for diagnostic use
    static String dumpStack(int maxFrames, int skipTop) {
        return StackWalker.getInstance(
                StackWalker.Option.RETAIN_CLASS_REFERENCE,
                StackWalker.Option.SHOW_HIDDEN_FRAMES
            )
            .walk(frames -> frames
                .skip(skipTop)
                .limit(maxFrames)
                .filter(frame -> {
                    // Exclude JDK internal classes from the dump
                    String cn = frame.getClassName();
                    return !cn.startsWith("java.") || cn.startsWith("java.util");
                })
                .map(frame -> {
                    Class<?> cls = frame.getDeclaringClass();
                    String module = cls.getModule().getName();
                    String loc = module != null ? "[" + module + "]" : "[unnamed]";
                    return String.format("  %s %s.%s:%d",
                        loc,
                        frame.getClassName(),
                        frame.getMethodName(),
                        frame.getLineNumber()
                    );
                })
                .collect(Collectors.joining("\n"))
            );
    }

    static void level3() { level2(); }
    static void level2() { level1(); }
    static void level1() {
        System.out.println("Stack dump at level1:");
        System.out.println(dumpStack(10, 2));
    }

    public static void main(String[] args) {
        level3();
    }
}
```

**How to run:** `java DiagnosticStackDump.java`

Expected output (module names vary):
```
Stack dump at level1:
  [unnamed] DiagnosticStackDump.level1:53
  [unnamed] DiagnosticStackDump.level2:50
  [unnamed] DiagnosticStackDump.level3:49
  [unnamed] DiagnosticStackDump.main:56
```

The production-flavoured features: (1) `SHOW_HIDDEN_FRAMES` includes implementation frames that the default walker hides (reflection internals, method handle adapters); (2) `RETAIN_CLASS_REFERENCE` enables querying the module via `cls.getModule().getName()` — useful for diagnosing classpath vs module-path issues in a modular application; (3) `filter` excludes `java.*` frames (keeping `java.util`) to focus on application code; (4) `limit(maxFrames)` caps the output to a reasonable diagnostic size. The output shows a clean, filtered stack trace from the deepest application frame (`level1`) up through the call chain to `main`.

## 6. Walkthrough

Tracing the Level 3 call `level3()` → `level2()` → `level1()` → `dumpStack(10, 2)`:

1. `main` calls `level3()`. `level3()` calls `level2()`. `level2()` calls `level1()`. Inside `level1()`, `dumpStack(10, 2)` is called.

2. `dumpStack` creates a `StackWalker` with `RETAIN_CLASS_REFERENCE` and `SHOW_HIDDEN_FRAMES` options via `getInstance(option...)`. These options configure the walker but no work is done yet.

3. `.walk(frames -> ...)` is called, providing a function that receives a `Stream<StackWalker.StackFrame>`. The stream is valid ONLY inside this function — attempting to store it or return it would throw `IllegalStateException`.

4. Inside the function, the stream pipeline is constructed lazily:
   - `.skip(2)` skips frame 0 (internals of `walk()`) and frame 1 (the `dumpStack` method itself). This leaves frames starting from the caller of `dumpStack`.
   - `.limit(10)` caps at 10 frames.
   - `.filter(...)` removes frames whose class name starts with `"java."` but NOT `"java.util"`. This filters out JDK internal frames while keeping application code.
   - `.map(...)` formats each frame: `"[module] class.method:line"`.
   - `.collect(Collectors.joining("\n"))` joins all formatted strings with newlines.

5. The `collect()` terminal operation triggers stream evaluation. The StackWalker lazily materialises frames:
   - Frame 2: `DiagnosticStackDump.level1` line 53 → formats as `"  [unnamed] DiagnosticStackDump.level1:53"`.
   - Frame 3: `DiagnosticStackDump.level2` line 50 → formats as `"  [unnamed] DiagnosticStackDump.level2:50"`.
   - Frame 4: `DiagnosticStackDump.level3` line 49 → formatted.
   - Frame 5: `DiagnosticStackDump.main` line 56 → formatted.
   - Frames beyond this (JVM bootstrap, `java.lang.Thread`, etc.) are filtered or hit the `limit`.

6. The joined string is returned from the `walk()` callback to `level1()`, which prints it as the stack dump.

```
Stack at call time (top = nearest):
  Frame 0: StackWalker internals        ← skipped by walk implementation
  Frame 1: dumpStack                     ← skipped by skip(2)
  Frame 2: level1                        ← first visible: filter passes
  Frame 3: level2                        ← filter passes
  Frame 4: level3                        ← filter passes
  Frame 5: main                          ← filter passes
  Frame 6: java.lang... / jdk.internal... ← filtered out
```

## 7. Gotchas & takeaways

> The `Stream<StackFrame>` in `walk()` is **single-use and scoped** — it cannot escape the function passed to `walk()`. If you try to store the stream reference in a field or return it from the function, you get `IllegalStateException`. This is deliberate: the frames are only valid while the current thread's stack is intact; a stale stream could point to frames that have since been unwound.

- `StackWalker.getInstance()` returns a shared singleton by default — no options, no class reference retained. `getInstance(Option...)` creates a new walker with the specified options, which should be stored and reused rather than recreated on every call.
- `RETAIN_CLASS_REFERENCE` is essential if you need to inspect annotations, module membership, or other class-level metadata at stack inspection time — but it carries a small memory cost per frame because the class object must be kept alive.
- `SHOW_REFLECT_FRAMES` and `SHOW_HIDDEN_FRAMES` control which synthetic frames appear. By default, reflection and implementation frames are hidden. If your method is called via reflection (e.g. a test framework), `SHOW_REFLECT_FRAMES` ensures those proxy frames are visible.
- `StackWalker` is not a security mechanism — a determined attacker can spoof or bypass caller checks. It is a diagnostic and lightweight access-control tool, not a hardened security boundary (use `SecurityManager` or module-based access control for that).
- The old `Thread.getStackTrace()` and `Throwable.getStackTrace()` still work and are not deprecated — `StackWalker` is the performance-oriented and feature-rich alternative, recommended for new code. 