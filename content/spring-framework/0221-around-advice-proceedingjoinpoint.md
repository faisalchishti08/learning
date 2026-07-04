---
card: spring-framework
gi: 221
slug: around-advice-proceedingjoinpoint
title: "@Around advice & ProceedingJoinPoint"
---

## 1. What it is

`@Around` is the most powerful AOP advice type. It wraps the matched method completely — the advice code runs before *and* after the method, and it controls whether the method runs at all via `ProceedingJoinPoint.proceed()`. The advice can:
- Modify the arguments passed to the method.
- Replace the return value.
- Catch and suppress exceptions.
- Skip the method entirely and return a substitute value.

```java
@Around("execution(* OrderService.*(..))")
public Object wrap(ProceedingJoinPoint pjp) throws Throwable {
    // before
    Object result = pjp.proceed(); // calls the real method
    // after
    return result;
}
```

## 2. Why & when

`@Around` is the right choice when:
- You need to modify arguments before the method runs: `pjp.proceed(newArgs)`.
- You need to modify or replace the return value.
- You need to catch exceptions and either swallow, translate, or retry them.
- You need timing that straddles both before and after (latency measurement).
- You need conditional execution — run the method only if a condition is met.

Use simpler advice (`@Before`, `@AfterReturning`) when possible. `@Around` is powerful but less readable — it hides the method call inside the advice body.

## 3. Core concept

Think of `@Around` as a middleware layer: your advice method *is* the call from the caller's perspective. The real method is buried inside `pjp.proceed()`. You are in charge of calling it — or not.

`ProceedingJoinPoint` extends `JoinPoint` with one key method:
- `proceed()` — calls the real method with the original arguments.
- `proceed(Object[] args)` — calls the real method with *new* arguments.

Rules:
1. The return type of the `@Around` method must be `Object` (or a compatible type) to pass the real return value through.
2. The method **must** declare `throws Throwable` (or a checked supertype) because `proceed()` can throw anything.
3. If you forget to call `pjp.proceed()`, the real method is silently skipped.

## 4. Diagram

<svg viewBox="0 0 640 180" xmlns="http://www.w3.org/2000/svg">
  <!-- Timeline bar -->
  <line x1="15" y1="88" x2="620" y2="88" stroke="#8b949e" stroke-width="1" stroke-dasharray="4 2"/>

  <!-- Caller -->
  <rect x="15" y="62" width="70" height="40" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="50" y="85" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Caller</text>
  <line x1="85" y1="82" x2="120" y2="82" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#a)"/>

  <!-- @Around box — spans whole advice period -->
  <rect x="120" y="40" width="460" height="100" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2.5"/>
  <text x="200" y="62" fill="#6db33f" font-size="12" font-family="sans-serif">@Around advice</text>
  <text x="200" y="78" fill="#8b949e" font-size="10" font-family="sans-serif">// before code</text>

  <!-- pjp.proceed() box -->
  <rect x="280" y="60" width="140" height="55" rx="6" fill="#0d1117" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="350" y="82" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">pjp.proceed()</text>
  <text x="350" y="98" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">real method runs</text>

  <text x="460" y="78" fill="#8b949e" font-size="10" font-family="sans-serif">// after code</text>
  <text x="460" y="94" fill="#8b949e" font-size="10" font-family="sans-serif">return result;</text>

  <!-- Return to caller -->
  <line x1="580" y1="90" x2="610" y2="90" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a)"/>

  <!-- Exception catch arrow -->
  <line x1="350" y1="115" x2="350" y2="155" stroke="#e06c75" stroke-width="1.5" stroke-dasharray="4 2" marker-end="url(#ae)"/>
  <text x="430" y="150" fill="#e06c75" font-size="9" font-family="sans-serif">catch/suppress/translate</text>

  <defs>
    <marker id="a"  markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto"><polygon points="0 0,8 3,0 6" fill="#6db33f"/></marker>
    <marker id="ae" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto"><polygon points="0 0,8 3,0 6" fill="#e06c75"/></marker>
  </defs>
</svg>

The `@Around` advice wraps the entire method call. `pjp.proceed()` is the hinge — everything before it is "before", everything after is "after".

## 5. Runnable example

Scenario: a **payment gateway** — first wrapping for timing, then modifying arguments, then a retry wrapper with exception handling.

### Level 1 — Basic

Wrap a method to measure its execution time.

```java
// AroundDemo.java
import org.springframework.context.annotation.*;
import org.springframework.stereotype.*;
import org.aspectj.lang.*;
import org.aspectj.lang.annotation.*;

@Configuration
@EnableAspectJAutoProxy
@ComponentScan
public class AroundDemo {
    public static void main(String[] args) throws Exception {
        var ctx = new AnnotationConfigApplicationContext(AroundDemo.class);
        ctx.getBean(PaymentGateway.class).charge("card-1", 99.0);
        ctx.close();
    }
}

@Service
class PaymentGateway {
    public String charge(String cardId, double amount) throws InterruptedException {
        Thread.sleep(150); // simulate network call
        System.out.println("Charged " + cardId + " $" + amount);
        return "txn-" + cardId;
    }
}

@Aspect
@Component
class TimingAspect {
    @Around("execution(* PaymentGateway.*(..))")
    public Object time(ProceedingJoinPoint pjp) throws Throwable {
        long t0 = System.currentTimeMillis();
        Object result = pjp.proceed();   // real method runs here
        System.out.printf("[TIMING] %s = %d ms%n",
            pjp.getSignature().getName(), System.currentTimeMillis() - t0);
        return result;
    }
}
```

How to run: `java -cp spring-context.jar:spring-aop.jar:aspectjweaver.jar:. AroundDemo.java`

`pjp.proceed()` calls `PaymentGateway.charge` and returns its result. The advice records start time before, elapsed time after. The `String` result passes through unchanged.

---

### Level 2 — Intermediate

Modify arguments before passing them to the method: normalise the card ID to uppercase.

```java
// AroundDemo.java
import org.springframework.context.annotation.*;
import org.springframework.stereotype.*;
import org.aspectj.lang.*;
import org.aspectj.lang.annotation.*;

@Configuration
@EnableAspectJAutoProxy
@ComponentScan
public class AroundDemo {
    public static void main(String[] args) throws Exception {
        var ctx = new AnnotationConfigApplicationContext(AroundDemo.class);
        ctx.getBean(PaymentGateway.class).charge("card-abc", 50.0);
        ctx.close();
    }
}

@Service
class PaymentGateway {
    public String charge(String cardId, double amount) throws InterruptedException {
        Thread.sleep(50);
        System.out.println("Processing cardId=" + cardId + " amount=" + amount);
        return "txn-" + cardId;
    }
}

@Aspect
@Component
class NormalisationAspect {
    @Around("execution(* PaymentGateway.charge(String, double)) && args(cardId, amount)")
    public Object normalise(ProceedingJoinPoint pjp, String cardId, double amount) throws Throwable {
        // Modify first argument: uppercase
        String normCardId = cardId.toUpperCase();
        System.out.println("[AROUND] normalised cardId: " + cardId + " → " + normCardId);

        // proceed() with new args
        Object result = pjp.proceed(new Object[]{normCardId, amount});
        System.out.println("[AROUND] result: " + result);
        return result;
    }
}
```

How to run: same classpath

`pjp.proceed(new Object[]{normCardId, amount})` passes a new argument array. `PaymentGateway.charge` receives `"CARD-ABC"` instead of `"card-abc"`. The return value is still threaded through unchanged.

---

### Level 3 — Advanced

Retry wrapper: if the method throws a `RuntimeException`, retry up to 3 times before giving up.

```java
// AroundDemo.java
import org.springframework.context.annotation.*;
import org.springframework.stereotype.*;
import org.aspectj.lang.*;
import org.aspectj.lang.annotation.*;
import java.lang.annotation.*;
import java.util.concurrent.atomic.*;

@Retention(RetentionPolicy.RUNTIME) @Target(ElementType.METHOD)
@interface Retryable { int times() default 3; }

@Configuration
@EnableAspectJAutoProxy
@ComponentScan
public class AroundDemo {
    public static void main(String[] args) throws Throwable {
        var ctx = new AnnotationConfigApplicationContext(AroundDemo.class);
        var gw = ctx.getBean(PaymentGateway.class);

        System.out.println("=== eventually succeeds ===");
        System.out.println("Result: " + gw.chargeFlaky("card-X", 10.0));

        System.out.println("=== always fails ===");
        try { gw.chargeAlwaysFails("card-Y", 20.0); }
        catch (RuntimeException e) { System.out.println("Gave up: " + e.getMessage()); }

        ctx.close();
    }
}

@Service
class PaymentGateway {
    private final AtomicInteger flakyCount = new AtomicInteger();

    @Retryable(times = 3)
    public String chargeFlaky(String cardId, double amount) {
        int attempt = flakyCount.incrementAndGet();
        if (attempt < 3) throw new RuntimeException("Network error on attempt " + attempt);
        System.out.println("Succeeded on attempt " + attempt);
        return "txn-" + cardId;
    }

    @Retryable(times = 2)
    public String chargeAlwaysFails(String cardId, double amount) {
        throw new RuntimeException("Gateway down");
    }
}

@Aspect
@Component
class RetryAspect {
    @Around("@annotation(retryable)")
    public Object retry(ProceedingJoinPoint pjp, Retryable retryable) throws Throwable {
        int maxAttempts = retryable.times();
        Throwable lastEx = null;
        for (int attempt = 1; attempt <= maxAttempts; attempt++) {
            try {
                System.out.println("[RETRY] attempt " + attempt + "/" + maxAttempts);
                return pjp.proceed();
            } catch (RuntimeException ex) {
                lastEx = ex;
                System.out.println("[RETRY] failed: " + ex.getMessage());
            }
        }
        throw lastEx; // rethrow after all attempts exhausted
    }
}
```

How to run: same classpath

`pjp.proceed()` is called inside a loop. On each `RuntimeException`, the loop retries. After `maxAttempts` failures, the last exception is re-thrown. For `chargeFlaky`, attempt 3 succeeds and returns the result. For `chargeAlwaysFails`, both attempts fail and the exception propagates.

## 6. Walkthrough

**`gw.chargeFlaky("card-X", 10.0)` execution (Level 3):**
1. Proxy intercepts `chargeFlaky`.
2. `RetryAspect.retry(pjp, @Retryable(times=3))` is called.
3. Attempt 1: `pjp.proceed()` → `chargeFlaky` throws `RuntimeException("Network error on attempt 1")`. Caught. Loop continues.
4. Attempt 2: `pjp.proceed()` → `chargeFlaky` throws `RuntimeException("Network error on attempt 2")`. Caught.
5. Attempt 3: `pjp.proceed()` → `chargeFlaky` runs `flakyCount = 3`, does not throw, prints "Succeeded on attempt 3", returns `"txn-card-X"`.
6. `return pjp.proceed()` in the advice returns `"txn-card-X"` to the caller.

**`pjp.proceed(newArgs)` mechanics (Level 2):**
- Spring's `ReflectiveMethodInvocation.proceed()` is called with the new args array.
- The original argument values stored in the `JoinPoint` are replaced for this invocation only.
- The next invocation of the same proxy method would use the original args again.

**`@Around` vs `@Before`+`@AfterReturning` equivalence:**
`@Around` is strictly more powerful. It can replicate `@Before` (code before `pjp.proceed()`), `@AfterReturning` (inspect result after), and `@AfterThrowing` (catch exception) in one method. However, separate advice types are more readable when you don't need the full power.

**Expected output (Level 3):**
```
=== eventually succeeds ===
[RETRY] attempt 1/3
[RETRY] failed: Network error on attempt 1
[RETRY] attempt 2/3
[RETRY] failed: Network error on attempt 2
[RETRY] attempt 3/3
Succeeded on attempt 3
Result: txn-card-X
=== always fails ===
[RETRY] attempt 1/2
[RETRY] failed: Gateway down
[RETRY] attempt 2/2
[RETRY] failed: Gateway down
Gave up: Gateway down
```

## 7. Gotchas & takeaways

> **Forgetting `pjp.proceed()` silently skips the real method.** If you return a hardcoded value without calling `proceed()`, the method never runs and no exception is thrown — a very subtle bug.

> **`@Around` must return `Object` (not `void`), even for void methods.** Return `null` for void methods: `return pjp.proceed(); // returns null for void`. Returning void from `@Around` causes a compile error.

- `pjp.proceed()` must be called with `throws Throwable` in the advice signature — the compiler enforces this.
- `pjp.proceed(newArgs)` passes a new `Object[]` — the length must match the original method's parameter count exactly.
- `@Around` is the implementation of `@Transactional`, `@Cacheable`, and `@Retryable` (Spring Retry). Understanding `@Around` means understanding how those annotations work under the hood.
- Prefer `@Before`/`@After`/`@AfterReturning` when you only need one side of the method boundary — they are simpler and communicate intent more clearly.
