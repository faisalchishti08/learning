---
card: spring-framework
gi: 224
slug: advice-ordering-order
title: "Advice ordering (@Order)"
---

## 1. What it is

When multiple aspects contain advice that match the same join point, Spring AOP applies them in a defined order. You control this order by annotating aspect classes with `@Order(n)` (from `org.springframework.core.annotation`) or by implementing `org.springframework.core.Ordered`.

Lower numeric values = higher priority = outermost position in the advice chain. Unordered aspects have undefined relative order — which can cause non-deterministic behaviour in production.

```java
@Aspect @Component @Order(1)   class SecurityAspect  { ... } // outermost
@Aspect @Component @Order(2)   class TransactionAspect { ... }
@Aspect @Component @Order(100) class LoggingAspect   { ... } // innermost
```

## 2. Why & when

Order matters when aspects depend on each other. Classic examples:

- **Security before transaction** — check authorisation first; if denied, don't open a transaction.
- **Logging inside timing** — the timer wraps everything; logging is inner.
- **Retry wraps transaction** — retry logic must encompass the entire transactional attempt.

Without explicit `@Order`, advice from different aspects fires in an unspecified order (JVM-dependent, often alphabetical by class name, but never guaranteed). For two aspects that both match a critical method, undefined order is a bug waiting to happen.

## 3. Core concept

Think of aspect advice as nested Russian dolls (matryoshkas). The outermost doll (`@Order(1)`) is the first to enter and the last to exit. The innermost doll is closest to the real method.

For `@Around`:
- Lower order → enters first (before real method), exits last (after real method).

For `@Before`:
- Lower order → runs first.

For `@After`, `@AfterReturning`, `@AfterThrowing`:
- Lower order → runs *last* (because on the exit path, advice unwinds in reverse).

```
Execution order (enter):  @Order(1) → @Order(2) → @Order(3) → method
Unwind order (exit):      method → @Order(3) → @Order(2) → @Order(1)
```

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg">
  <!-- Nested boxes representing aspect order -->
  <!-- Order(1) - outermost -->
  <rect x="15" y="15" width="610" height="170" rx="10" fill="#1c2430" stroke="#e06c75" stroke-width="2"/>
  <text x="50" y="38" fill="#e06c75" font-size="11" font-family="sans-serif">@Order(1) SecurityAspect — enters FIRST, exits LAST</text>

  <!-- Order(2) -->
  <rect x="35" y="48" width="570" height="115" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="70" y="68" fill="#79c0ff" font-size="11" font-family="sans-serif">@Order(2) TransactionAspect — enters 2nd, exits 2nd-to-last</text>

  <!-- Order(100) -->
  <rect x="55" y="80" width="530" height="65" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="90" y="100" fill="#6db33f" font-size="11" font-family="sans-serif">@Order(100) LoggingAspect — enters LAST, exits 1st</text>

  <!-- Real method -->
  <rect x="230" y="110" width="180" height="30" rx="5" fill="#0d1117" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="129" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Real method</text>
</svg>

Lower `@Order` = outer shell. Each aspect's `@Around.enter` runs top-to-bottom; `@Around.exit` and `@After` run bottom-to-top.

## 5. Runnable example

Scenario: a **checkout service** — first showing undefined order, then adding `@Order`, then verifying the retry-wraps-transaction pattern.

### Level 1 — Basic

Two aspects without `@Order` — order is undefined (often alphabetical).

```java
// OrderDemo.java
import org.springframework.context.annotation.*;
import org.springframework.stereotype.*;
import org.aspectj.lang.*;
import org.aspectj.lang.annotation.*;

@Configuration
@EnableAspectJAutoProxy
@ComponentScan
public class OrderDemo {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(OrderDemo.class);
        ctx.getBean(CheckoutService.class).checkout("cart-1");
        ctx.close();
    }
}

@Service
class CheckoutService {
    public void checkout(String cartId) {
        System.out.println("Checkout: " + cartId);
    }
}

@Aspect @Component
class AlphaAspect {
    @Before("execution(* CheckoutService.*(..))")
    public void alpha() { System.out.println("[AlphaAspect] before"); }
}

@Aspect @Component
class BetaAspect {
    @Before("execution(* CheckoutService.*(..))")
    public void beta() { System.out.println("[BetaAspect] before"); }
}
```

How to run: `java -cp spring-context.jar:spring-aop.jar:aspectjweaver.jar:. OrderDemo.java`

Order is undefined — may be alphabetical (AlphaAspect before BetaAspect), but never rely on this.

---

### Level 2 — Intermediate

Add `@Order` to make security check outer and logging inner.

```java
// OrderDemo.java
import org.springframework.context.annotation.*;
import org.springframework.stereotype.*;
import org.springframework.core.annotation.Order;
import org.aspectj.lang.*;
import org.aspectj.lang.annotation.*;

@Configuration
@EnableAspectJAutoProxy
@ComponentScan
public class OrderDemo {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(OrderDemo.class);
        var svc = ctx.getBean(CheckoutService.class);

        System.out.println("--- authorised ---");
        OrderDemo.user = "admin";
        svc.checkout("cart-1");

        System.out.println("--- unauthorised ---");
        OrderDemo.user = "guest";
        try { svc.checkout("cart-2"); } catch (SecurityException e) {
            System.out.println("Blocked: " + e.getMessage());
        }
        ctx.close();
    }
    static String user = "admin";
}

@Service
class CheckoutService {
    public void checkout(String cartId) {
        System.out.println("Checkout: " + cartId);
    }
}

@Aspect @Component @Order(1)   // OUTER
class SecurityAspect {
    @Around("execution(* CheckoutService.*(..))")
    public Object check(ProceedingJoinPoint pjp) throws Throwable {
        System.out.println("[SECURITY] enter (order=1)");
        if (!"admin".equals(OrderDemo.user)) throw new SecurityException("Access denied for: " + OrderDemo.user);
        Object r = pjp.proceed();
        System.out.println("[SECURITY] exit");
        return r;
    }
}

@Aspect @Component @Order(100) // INNER
class LoggingAspect {
    @Around("execution(* CheckoutService.*(..))")
    public Object log(ProceedingJoinPoint pjp) throws Throwable {
        System.out.println("[LOGGING] enter (order=100)");
        Object r = pjp.proceed();
        System.out.println("[LOGGING] exit");
        return r;
    }
}
```

How to run: same classpath

Security (`@Order(1)`) enters first. On the unauthorised call, it throws before `LoggingAspect` is even reached — the inner aspect never runs. On the authorised call the order is Security enter → Logging enter → method → Logging exit → Security exit.

---

### Level 3 — Advanced

Retry (outer) wraps Transaction (inner): retry must encompass the full transactional attempt.

```java
// OrderDemo.java
import org.springframework.context.annotation.*;
import org.springframework.stereotype.*;
import org.springframework.core.annotation.Order;
import org.aspectj.lang.*;
import org.aspectj.lang.annotation.*;
import java.lang.annotation.*;
import java.util.concurrent.atomic.*;

@Retention(RetentionPolicy.RUNTIME) @Target(ElementType.METHOD)
@interface Retryable { int times() default 3; }

@Configuration
@EnableAspectJAutoProxy
@ComponentScan
public class OrderDemo {
    public static void main(String[] args) throws Throwable {
        var ctx = new AnnotationConfigApplicationContext(OrderDemo.class);
        var svc = ctx.getBean(CheckoutService.class);

        System.out.println("=== flaky checkout (succeeds on 3rd try) ===");
        svc.checkout("cart-X");
        ctx.close();
    }
}

@Service
class CheckoutService {
    private final AtomicInteger attempts = new AtomicInteger();
    @Retryable(times = 3)
    public void checkout(String cartId) {
        int n = attempts.incrementAndGet();
        System.out.println("[METHOD] attempt " + n);
        if (n < 3) throw new RuntimeException("DB transient error on attempt " + n);
        System.out.println("[METHOD] succeeded: " + cartId);
    }
}

@Aspect @Component @Order(1)   // OUTER — retry must encompass the transaction
class RetryAspect {
    @Around("@annotation(r)")
    public Object retry(ProceedingJoinPoint pjp, Retryable r) throws Throwable {
        Throwable last = null;
        for (int i = 1; i <= r.times(); i++) {
            try {
                System.out.println("[RETRY] attempt " + i + "/" + r.times());
                return pjp.proceed();
            } catch (RuntimeException ex) { last = ex; System.out.println("[RETRY] failed: " + ex.getMessage()); }
        }
        throw last;
    }
}

@Aspect @Component @Order(2)   // INNER — simulated transaction boundary
class TxAspect {
    @Around("@annotation(Retryable)")
    public Object tx(ProceedingJoinPoint pjp) throws Throwable {
        System.out.println("  [TX] begin");
        try {
            Object r = pjp.proceed();
            System.out.println("  [TX] commit");
            return r;
        } catch (RuntimeException ex) {
            System.out.println("  [TX] rollback");
            throw ex;
        }
    }
}
```

How to run: same classpath

Retry (`@Order(1)`) is outer. Each retry attempt starts a new `[TX] begin` … `[TX] commit/rollback` cycle because the transaction (`@Order(2)`) is inside the retry loop. If they were swapped, retries would happen inside one transaction — potentially useless.

## 6. Walkthrough

**Advice chain construction (Level 3):**
1. Spring sorts aspect beans by `@Order` value: `RetryAspect(1)` < `TxAspect(2)`.
2. For `checkout`, both aspects' `@Around` match.
3. Chain: `RetryAspect.retry` → `TxAspect.tx` → real `checkout`.

**Execution flow — attempt 1 (fails):**
- `[RETRY] attempt 1/3` (RetryAspect enters).
- `[TX] begin` (TxAspect enters).
- `[METHOD] attempt 1` — throws `RuntimeException`.
- `[TX] rollback` (TxAspect catches, rethrows).
- `[RETRY] failed` (RetryAspect catches, loops).

**Execution flow — attempt 3 (succeeds):**
- `[RETRY] attempt 3/3`.
- `[TX] begin`.
- `[METHOD] attempt 3, succeeded`.
- Returns.
- `[TX] commit`.
- Returns from retry → caller gets void.

**Why order matters here:**
If `@Order` were reversed (TxAspect outer, RetryAspect inner), attempt 1 would: begin transaction → (retry loop 1,2,3 all fail) → transaction rolls back once. The retry would happen *inside* one transaction, so even if the retry succeeded, the transaction might have already been marked for rollback. The correct model is retry outside, transaction inside.

**Expected output:**
```
=== flaky checkout (succeeds on 3rd try) ===
[RETRY] attempt 1/3
  [TX] begin
[METHOD] attempt 1
  [TX] rollback
[RETRY] failed: DB transient error on attempt 1
[RETRY] attempt 2/3
  [TX] begin
[METHOD] attempt 2
  [TX] rollback
[RETRY] failed: DB transient error on attempt 2
[RETRY] attempt 3/3
  [TX] begin
[METHOD] attempt 3
[METHOD] succeeded: cart-X
  [TX] commit
```

## 7. Gotchas & takeaways

> **`@After` and `@AfterReturning` run in reverse order of entry.** `@Order(1)` aspect's `@After` runs LAST (outermost exits last), not first. This is the matryoshka unwinding. For cleanup in `@After`, low-order aspects should be prepared to run their cleanup after high-order aspects have already cleaned up.

> **`@Order` applies to the aspect class, not to individual advice methods.** All advice in the same `@Aspect` class shares the same order relative to other aspect classes. To order individual advice methods within a class, use `@Order` on a sub-aspect or split into separate classes.

- `@Order(Integer.MAX_VALUE)` is the default — unordered aspects run last (innermost).
- `@Order(Integer.MIN_VALUE)` makes an aspect the absolute outermost.
- `Ordered.HIGHEST_PRECEDENCE` = `Integer.MIN_VALUE`; `Ordered.LOWEST_PRECEDENCE` = `Integer.MAX_VALUE`.
- Spring's `@Transactional` uses `@Order(Integer.MAX_VALUE - 2)` and `@Cacheable` uses a similar low-priority order — be aware when adding custom aspects that interact with these.
