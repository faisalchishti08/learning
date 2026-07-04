---
card: spring-framework
gi: 219
slug: afterthrowing-advice
title: "@AfterThrowing advice"
---

## 1. What it is

`@AfterThrowing` is an AOP advice type that runs *only* when a matched method exits by throwing an exception. The `throwing` attribute binds the actual exception to a parameter in the advice method, giving you access to it without wrapping every method in try/catch.

```java
@AfterThrowing(pointcut = "execution(* OrderService.*(..)) ", throwing = "ex")
public void onError(JoinPoint jp, Exception ex) {
    System.err.println("[ERROR] " + jp.getSignature().getName() + ": " + ex.getMessage());
}
```

`@AfterThrowing` observes the exception — it does **not** suppress it. The exception still propagates to the caller after the advice runs.

## 2. Why & when

Use `@AfterThrowing` when you need to:
- **Centralise error logging** across all service methods without try/catch in each.
- **Trigger alerts** or metrics on exception — e.g., increment an error counter.
- **Record which method failed and with what arguments** for post-mortem analysis.
- **Type-filter exceptions** — fire advice only for `DataAccessException`, not for `IllegalArgumentException`.

Do NOT use `@AfterThrowing` to swallow or translate exceptions — use `@Around` for that. `@AfterThrowing` cannot suppress the exception.

## 3. Core concept

Think of `@AfterThrowing` as a smoke alarm: it triggers when something goes wrong, records what happened, but does not put out the fire (does not catch the exception). The fire (exception) continues to spread upward.

The `throwing` attribute works the same way as `returning` in `@AfterReturning`:
- The attribute value must match the parameter name.
- The declared parameter type acts as a filter: `Exception ex` fires for any exception; `DataAccessException dae` fires only when a `DataAccessException` (or subclass) is thrown.

```java
@AfterThrowing(pointcut = "serviceLayer()", throwing = "ex")
public void onAny(JoinPoint jp, Throwable ex) { /* any throwable */ }

@AfterThrowing(pointcut = "serviceLayer()", throwing = "dae")
public void onData(JoinPoint jp, org.springframework.dao.DataAccessException dae) {
    /* only DataAccessException */
}
```

## 4. Diagram

<svg viewBox="0 0 640 175" xmlns="http://www.w3.org/2000/svg">
  <line x1="20" y1="85" x2="610" y2="85" stroke="#8b949e" stroke-width="1" stroke-dasharray="4 2"/>

  <!-- Caller -->
  <rect x="20" y="60" width="70" height="40" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="55" y="83" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Caller</text>
  <line x1="90" y1="80" x2="140" y2="80" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#a)"/>

  <!-- Method -->
  <rect x="140" y="55" width="130" height="50" rx="5" fill="#1c2430" stroke="#e06c75" stroke-width="1.5"/>
  <text x="205" y="77" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Real method</text>
  <text x="205" y="93" fill="#e06c75" font-size="10" text-anchor="middle" font-family="sans-serif">throws IOException</text>

  <!-- Exception path to @AfterThrowing -->
  <line x1="205" y1="105" x2="205" y2="140" stroke="#e06c75" stroke-width="1.5" marker-end="url(#ae)"/>
  <line x1="205" y1="140" x2="350" y2="140" stroke="#e06c75" stroke-width="1.5" marker-end="url(#ae)"/>

  <!-- @AfterThrowing -->
  <rect x="350" y="115" width="175" height="50" rx="5" fill="#1c2430" stroke="#e06c75" stroke-width="2"/>
  <text x="438" y="137" fill="#e06c75" font-size="12" text-anchor="middle" font-family="sans-serif">@AfterThrowing</text>
  <text x="438" y="153" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">observes exception</text>

  <!-- Exception continues -->
  <line x1="525" y1="140" x2="590" y2="140" stroke="#e06c75" stroke-width="1.5" marker-end="url(#ae)"/>
  <text x="555" y="133" fill="#e06c75" font-size="9" text-anchor="middle" font-family="sans-serif">rethrown</text>

  <!-- Normal path skips -->
  <rect x="340" y="55" width="155" height="40" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1" stroke-dasharray="4 2"/>
  <text x="418" y="79" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">normal return → skipped</text>

  <defs>
    <marker id="a"  markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto"><polygon points="0 0,8 3,0 6" fill="#79c0ff"/></marker>
    <marker id="ae" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto"><polygon points="0 0,8 3,0 6" fill="#e06c75"/></marker>
  </defs>
</svg>

Exception flows down to `@AfterThrowing`, which observes it, then the exception continues propagating to the caller.

## 5. Runnable example

Scenario: a **file processing service** — first centrally logging all exceptions, then type-filtering to only handle `IOException`, then recording failure metrics.

### Level 1 — Basic

Log any exception thrown by any method in `FileService`.

```java
// AfterThrowingDemo.java
import org.springframework.context.annotation.*;
import org.springframework.stereotype.*;
import org.aspectj.lang.*;
import org.aspectj.lang.annotation.*;
import java.io.*;

@Configuration
@EnableAspectJAutoProxy
@ComponentScan
public class AfterThrowingDemo {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(AfterThrowingDemo.class);
        var svc = ctx.getBean(FileService.class);
        try {
            svc.read("/nonexistent/path");
        } catch (Exception e) {
            System.out.println("Caller caught: " + e.getMessage());
        }
        ctx.close();
    }
}

@Service
class FileService {
    public String read(String path) throws IOException {
        throw new IOException("File not found: " + path);
    }
}

@Aspect
@Component
class ErrorLogAspect {
    @AfterThrowing(
        pointcut = "execution(* FileService.*(..))",
        throwing = "ex")
    public void logError(JoinPoint jp, Throwable ex) {
        System.err.printf("[ERROR] %s threw %s: %s%n",
            jp.getSignature().getName(),
            ex.getClass().getSimpleName(),
            ex.getMessage());
    }
}
```

How to run: `java -cp spring-context.jar:spring-aop.jar:aspectjweaver.jar:. AfterThrowingDemo.java`

`[ERROR]` is printed by the aspect before "Caller caught:" — the advice runs first, then the exception continues to the caller. The exception is NOT swallowed.

---

### Level 2 — Intermediate

Type-filter: only log `IOException`, not `IllegalArgumentException`.

```java
// AfterThrowingDemo.java
import org.springframework.context.annotation.*;
import org.springframework.stereotype.*;
import org.aspectj.lang.*;
import org.aspectj.lang.annotation.*;
import java.io.*;

@Configuration
@EnableAspectJAutoProxy
@ComponentScan
public class AfterThrowingDemo {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(AfterThrowingDemo.class);
        var svc = ctx.getBean(FileService.class);

        System.out.println("--- IOException ---");
        try { svc.read("bad.txt"); } catch (Exception e) { System.out.println("Caller: " + e.getMessage()); }

        System.out.println("--- IllegalArgumentException ---");
        try { svc.write("", "data"); } catch (Exception e) { System.out.println("Caller: " + e.getMessage()); }
        ctx.close();
    }
}

@Service
class FileService {
    public String read(String path) throws IOException {
        throw new IOException("Cannot read: " + path);
    }
    public void write(String path, String content) {
        if (path.isBlank()) throw new IllegalArgumentException("Path cannot be blank");
        System.out.println("Written to " + path);
    }
}

@Aspect
@Component
class IOErrorAspect {
    // throwing declared as IOException — only fires for IOException or subclasses
    @AfterThrowing(pointcut = "execution(* FileService.*(..))", throwing = "ioe")
    public void onIOException(JoinPoint jp, IOException ioe) {
        System.err.println("[IO_ERROR] " + jp.getSignature().getName() + ": " + ioe.getMessage());
    }
}
```

How to run: same as Level 1

`read` throws `IOException` → `[IO_ERROR]` fires. `write` throws `IllegalArgumentException` → the parameter type `IOException` does not match → advice skipped. Caller receives both exceptions normally.

---

### Level 3 — Advanced

Record failure metrics per-method and type, using an injected `FailureRegistry` bean.

```java
// AfterThrowingDemo.java
import org.springframework.context.annotation.*;
import org.springframework.stereotype.*;
import org.aspectj.lang.*;
import org.aspectj.lang.annotation.*;
import java.io.*;
import java.util.*;
import java.util.concurrent.*;
import java.util.concurrent.atomic.*;

@Configuration
@EnableAspectJAutoProxy
@ComponentScan
public class AfterThrowingDemo {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(AfterThrowingDemo.class);
        var svc = ctx.getBean(FileService.class);

        for (String p : new String[]{"a.txt", "b.txt", "c.txt"}) {
            try { svc.read(p); } catch (Exception ignored) {}
        }
        try { svc.write("", "x"); } catch (Exception ignored) {}

        var reg = ctx.getBean(FailureRegistry.class);
        System.out.println("Failure counts: " + reg.summary());
        ctx.close();
    }
}

@Service
class FileService {
    public String read(String path) throws IOException {
        throw new IOException("Cannot read: " + path);
    }
    public void write(String path, String data) {
        if (path.isBlank()) throw new IllegalArgumentException("Blank path");
    }
}

@Component
class FailureRegistry {
    private final Map<String, AtomicInteger> counts = new ConcurrentHashMap<>();
    public void record(String key) { counts.computeIfAbsent(key, k -> new AtomicInteger()).incrementAndGet(); }
    public Map<String, Integer> summary() {
        var m = new LinkedHashMap<String, Integer>();
        counts.forEach((k, v) -> m.put(k, v.get()));
        return m;
    }
}

@Aspect
@Component
class MetricsAspect {
    @org.springframework.beans.factory.annotation.Autowired
    private FailureRegistry registry;

    @AfterThrowing(pointcut = "execution(* FileService.*(..))", throwing = "ex")
    public void recordFailure(JoinPoint jp, Throwable ex) {
        String key = jp.getSignature().getName() + "/" + ex.getClass().getSimpleName();
        registry.record(key);
        System.err.println("[METRIC] failure recorded: " + key);
    }
}
```

How to run: same classpath

Each failure records a key `methodName/ExceptionType` in the `FailureRegistry`. After three `read` failures and one `write` failure, the summary shows `{read/IOException=3, write/IllegalArgumentException=1}`.

## 6. Walkthrough

**`svc.read("a.txt")` execution path (Level 3):**
1. Proxy intercepts `read("a.txt")`.
2. No `@Before` advice → real `FileService.read("a.txt")` is called.
3. Throws `IOException("Cannot read: a.txt")`.
4. Exception propagates back through the proxy's invocation handler.
5. Spring's advice dispatcher checks: are there any `@AfterThrowing` advice for this join point?
6. Finds `MetricsAspect.recordFailure` with `pointcut = "execution(* FileService.*(..))"` → matches.
7. Checks type filter: `Throwable ex` — `IOException` is assignable to `Throwable` → yes.
8. Calls `MetricsAspect.recordFailure(jp, ioException)`.
9. `registry.record("read/IOException")` → counter now 1.
10. Advice returns. Exception continues propagating. Caller's `catch (Exception e)` catches it.

**Why `@AfterThrowing` cannot suppress exceptions:**
Spring's proxy calls the advice in a `finally`-like block but does NOT wrap the method call in a try/catch that could swallow. The exception propagation is built into the proxy's invocation mechanism. To suppress, use `@Around` and catch inside `pjp.proceed()`.

**Type filter mechanics:**
When `throwing = "ioe"` is declared as `IOException ioe`, Spring calls `IOException.class.isInstance(thrownException)`. If false, the advice method is not invoked. This is evaluated per-call, not at startup.

**Expected output (Level 3):**
```
[METRIC] failure recorded: read/IOException  (× 3)
[METRIC] failure recorded: write/IllegalArgumentException
Failure counts: {read/IOException=3, write/IllegalArgumentException=1}
```

## 7. Gotchas & takeaways

> **`@AfterThrowing` does not catch the exception.** It fires, does its work, and the exception continues up the call stack. If you want to catch and handle/rethrow a modified exception, use `@Around` with try/catch around `pjp.proceed()`.

> **The throwing type is a filter, not a cast.** Declaring `DataAccessException dae` does NOT cause a `ClassCastException` when an `IOException` is thrown — the advice simply does not fire. Only exceptions assignable to the declared type trigger the advice.

- Use `Throwable` as the parameter type to catch everything (including `Error`). Use `Exception` to skip `Error`s. Use a specific type to narrow further.
- `@AfterThrowing` fires BEFORE `@After` (finally) — the exception hasn't reached `@After` yet when `@AfterThrowing` runs.
- `throwing` parameter name must exactly match the attribute: `throwing = "ex"` → parameter named `ex`. A mismatch causes `IllegalArgumentException` at startup.
- Avoid expensive blocking operations in `@AfterThrowing` advice — the caller's thread is still waiting while the advice runs.
