---
card: spring-framework
gi: 220
slug: after-finally-advice
title: "@After (finally) advice"
---

## 1. What it is

`@After` is an AOP advice type that runs *after* a matched method exits — regardless of whether it returned normally or threw an exception. It is the AOP equivalent of Java's `finally` block. It does not receive the return value and does not receive the thrown exception — it only knows the method signature and arguments.

```java
@After("execution(* OrderService.*(..))")
public void afterEvery(JoinPoint jp) {
    System.out.println("Method finished: " + jp.getSignature().getName());
}
```

## 2. Why & when

Use `@After` when you need to run cleanup or bookkeeping code that must happen whether the method succeeded or failed:

- **Resource release**: mark a resource as available regardless of success/failure.
- **Lock release**: release an advisory lock after a method finishes.
- **Span end**: finish a distributed tracing span (you want a span regardless of whether the call succeeded).
- **Context cleanup**: clear a thread-local after the method exits.

If you need the return value on success, use `@AfterReturning`. If you need the exception on failure, use `@AfterThrowing`. If you need both, use `@Around`. Use `@After` when you genuinely need to fire on *both* outcomes.

## 3. Core concept

Java's `finally` block is to a try/catch as `@After` is to `@AfterReturning`/`@AfterThrowing`. Like `finally`, `@After`:
- Always runs.
- Cannot change the return value or suppress exceptions.
- Cannot receive the return value or exception (unlike `@AfterReturning`/`@AfterThrowing`).

```java
// Java equivalent of what @After does:
try {
    Object result = method.invoke(target, args); // the real method
    runAfterReturningAdvice(result);
    return result;
} catch (Throwable t) {
    runAfterThrowingAdvice(t);
    throw t;
} finally {
    runAfterAdvice();  // @After — always
}
```

Execution order when all advice types match the same join point:
`@Around` (enter) → `@Before` → method → `@Around` (exit) → `@AfterReturning` OR `@AfterThrowing` → **`@After`**.

## 4. Diagram

<svg viewBox="0 0 640 185" xmlns="http://www.w3.org/2000/svg">
  <line x1="15" y1="88" x2="620" y2="88" stroke="#8b949e" stroke-width="1" stroke-dasharray="4 2"/>

  <!-- Method -->
  <rect x="15" y="60" width="130" height="55" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="80" y="83" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Real method</text>

  <!-- Normal return path -->
  <line x1="145" y1="75" x2="215" y2="75" stroke="#6db33f" stroke-width="1.5" marker-end="url(#ag)"/>
  <text x="180" y="68" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">returns</text>
  <rect x="215" y="55" width="135" height="40" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1"/>
  <text x="283" y="79" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">@AfterReturning</text>
  <line x1="350" y1="75" x2="415" y2="110" stroke="#6db33f" stroke-width="1.5" marker-end="url(#ag)"/>

  <!-- Exception path -->
  <line x1="145" y1="100" x2="215" y2="120" stroke="#e06c75" stroke-width="1.5" marker-end="url(#ae)"/>
  <text x="178" y="125" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">throws</text>
  <rect x="215" y="110" width="135" height="40" rx="5" fill="#1c2430" stroke="#e06c75" stroke-width="1"/>
  <text x="283" y="134" fill="#e06c75" font-size="10" text-anchor="middle" font-family="sans-serif">@AfterThrowing</text>
  <line x1="350" y1="130" x2="415" y2="120" stroke="#e06c75" stroke-width="1.5" marker-end="url(#ae)"/>

  <!-- @After (always) -->
  <rect x="415" y="90" width="145" height="50" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="488" y="112" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">@After (finally)</text>
  <text x="488" y="128" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">always runs</text>
  <line x1="560" y1="115" x2="605" y2="115" stroke="#6db33f" stroke-width="1.5" marker-end="url(#ag)"/>

  <defs>
    <marker id="ag" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto"><polygon points="0 0,8 3,0 6" fill="#6db33f"/></marker>
    <marker id="ae" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto"><polygon points="0 0,8 3,0 6" fill="#e06c75"/></marker>
  </defs>
</svg>

Both the normal return path and the exception path converge at `@After`.

## 5. Runnable example

Scenario: a **distributed lock service** — first just showing `@After` always firing, then using it to reliably release a lock, then combining all advice types to see execution order.

### Level 1 — Basic

`@After` fires after both normal returns and exceptions.

```java
// AfterDemo.java
import org.springframework.context.annotation.*;
import org.springframework.stereotype.*;
import org.aspectj.lang.*;
import org.aspectj.lang.annotation.*;

@Configuration
@EnableAspectJAutoProxy
@ComponentScan
public class AfterDemo {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(AfterDemo.class);
        var svc = ctx.getBean(LockService.class);

        System.out.println("--- normal ---");
        svc.doWork("task-1");

        System.out.println("--- exception ---");
        try { svc.doWork("fail"); } catch (Exception e) {
            System.out.println("Caller caught: " + e.getMessage());
        }
        ctx.close();
    }
}

@Service
class LockService {
    public void doWork(String task) {
        if (task.equals("fail")) throw new RuntimeException("Work failed: " + task);
        System.out.println("Work done: " + task);
    }
}

@Aspect
@Component
class FinallyAspect {
    @After("execution(* LockService.*(..))")
    public void always(JoinPoint jp) {
        System.out.println("[AFTER/finally] " + jp.getSignature().getName()
            + " finished (success or failure)");
    }
}
```

How to run: `java -cp spring-context.jar:spring-aop.jar:aspectjweaver.jar:. AfterDemo.java`

`[AFTER/finally]` appears both after the successful `doWork("task-1")` and after the failing `doWork("fail")`. The exception still propagates to the caller.

---

### Level 2 — Intermediate

Use `@After` as a lock release — critical to release whether or not the work succeeded.

```java
// AfterDemo.java
import org.springframework.context.annotation.*;
import org.springframework.stereotype.*;
import org.aspectj.lang.*;
import org.aspectj.lang.annotation.*;
import java.lang.annotation.*;
import java.util.*;
import java.util.concurrent.*;

@Retention(RetentionPolicy.RUNTIME) @Target(ElementType.METHOD)
@interface WithLock { String value(); }

@Configuration
@EnableAspectJAutoProxy
@ComponentScan
public class AfterDemo {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(AfterDemo.class);
        var svc = ctx.getBean(InventoryService.class);
        var locks = ctx.getBean(LockRegistry.class);

        System.out.println("--- acquire + succeed ---");
        svc.update("item-1", 10);
        System.out.println("Locks held: " + locks.held());

        System.out.println("--- acquire + fail ---");
        try { svc.update("item-2", -1); } catch (Exception e) {
            System.out.println("Caller: " + e.getMessage());
        }
        System.out.println("Locks held: " + locks.held());
        ctx.close();
    }
}

@Service
class InventoryService {
    @WithLock("inventory")
    public void update(String item, int qty) {
        System.out.println("Updating " + item + " qty=" + qty);
        if (qty < 0) throw new IllegalArgumentException("Negative qty");
    }
}

@Component
class LockRegistry {
    private final Set<String> locks = ConcurrentHashMap.newKeySet();
    public void acquire(String name) { locks.add(name); System.out.println("[LOCK] Acquired: " + name); }
    public void release(String name) { locks.remove(name); System.out.println("[LOCK] Released: " + name); }
    public Set<String> held() { return Collections.unmodifiableSet(locks); }
}

@Aspect
@Component
class LockAspect {
    @org.springframework.beans.factory.annotation.Autowired
    private LockRegistry registry;

    @Before("@annotation(withLock)")
    public void acquire(WithLock withLock) {
        registry.acquire(withLock.value());
    }

    @After("@annotation(withLock)")
    public void release(WithLock withLock) {
        registry.release(withLock.value());
    }
}
```

How to run: same classpath

After both the successful `update("item-1", 10)` and the failing `update("item-2", -1)`, `Locks held: []` confirms the lock was released in both cases. Without `@After` (using `@AfterReturning` instead), a failed call would leak the lock.

---

### Level 3 — Advanced

Show the full execution order: `@Before` → method → `@AfterReturning` XOR `@AfterThrowing` → `@After`.

```java
// AfterDemo.java
import org.springframework.context.annotation.*;
import org.springframework.stereotype.*;
import org.aspectj.lang.*;
import org.aspectj.lang.annotation.*;

@Configuration
@EnableAspectJAutoProxy
@ComponentScan
public class AfterDemo {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(AfterDemo.class);
        var svc = ctx.getBean(PaymentService.class);

        System.out.println("=== normal return ===");
        svc.charge(50.0);

        System.out.println("=== exception ===");
        try { svc.charge(-1.0); } catch (Exception e) {
            System.out.println("Caller caught: " + e.getMessage());
        }
        ctx.close();
    }
}

@Service
class PaymentService {
    public double charge(double amount) {
        if (amount < 0) throw new IllegalArgumentException("Negative amount: " + amount);
        System.out.println("Charged $" + amount);
        return amount * 1.1; // with fee
    }
}

@Aspect
@Component
class OrderAspect {
    @Pointcut("execution(* PaymentService.*(..))")
    public void payment() {}

    @Before("payment()")
    public void before()           { System.out.println("  [BEFORE]"); }

    @AfterReturning(pointcut = "payment()", returning = "rv")
    public void afterReturn(Object rv) { System.out.println("  [AFTER_RETURNING] result=" + rv); }

    @AfterThrowing(pointcut = "payment()", throwing = "ex")
    public void afterThrow(Throwable ex) { System.out.println("  [AFTER_THROWING] " + ex.getMessage()); }

    @After("payment()")
    public void after()            { System.out.println("  [AFTER/finally]"); }
}
```

How to run: same classpath

The execution order becomes visible: on success `[BEFORE]` → method → `[AFTER_RETURNING]` → `[AFTER/finally]`. On failure `[BEFORE]` → method throws → `[AFTER_THROWING]` → `[AFTER/finally]`.

## 6. Walkthrough

**`svc.charge(50.0)` — success path:**
1. Proxy intercepts.
2. `[BEFORE]` advice runs.
3. Real `PaymentService.charge(50.0)` runs → returns `55.0`.
4. Spring's advice chain: `@AfterReturning` fires with `rv = 55.0` → prints `[AFTER_RETURNING]`.
5. `@AfterThrowing` is skipped (no exception).
6. `@After` fires (always) → prints `[AFTER/finally]`.
7. Return `55.0` to caller.

**`svc.charge(-1.0)` — exception path:**
1. Proxy intercepts.
2. `[BEFORE]` runs.
3. Real `charge(-1.0)` throws `IllegalArgumentException`.
4. Spring's advice chain: `@AfterReturning` is skipped (exception path).
5. `@AfterThrowing` fires → prints `[AFTER_THROWING]`.
6. `@After` fires (always) → prints `[AFTER/finally]`.
7. Exception propagates to caller.

**Lock release correctness (Level 2):**
- `@Before` acquires lock, `@After` releases it.
- Regardless of whether `update()` succeeds or throws, `@After` fires → lock is released.
- If you had used `@AfterReturning` for release: on exception, release would be skipped → lock leak.

**Expected output (Level 3 normal path):**
```
=== normal return ===
  [BEFORE]
Charged $50.0
  [AFTER_RETURNING] result=55.0
  [AFTER/finally]
```

## 7. Gotchas & takeaways

> **`@After` cannot receive the return value or exception.** It only has `JoinPoint`. For success results use `@AfterReturning`; for exceptions use `@AfterThrowing`. `@After` is for unconditional cleanup only.

> **`@After` runs even when `@Before` threw.** If a `@Before` advice throws, the real method is skipped, but `@After` still fires. Be careful with `@After` cleanup that assumes the method ran.

- Classic `@After` use case: releasing a resource — database connection, distributed lock, MDC context, thread-local.
- Execution order: `@AfterReturning` / `@AfterThrowing` → `@After` (same aspect). `@After` is literally the last in the chain.
- `@After` is equivalent to `try { ... } finally { ... }` — always fires, even if an earlier advice threw.
- To observe both the return value AND the exception, use `@Around` with a try/catch/finally block around `pjp.proceed()`.
