---
card: spring-framework
gi: 206
slug: why-aop-cross-cutting-concerns
title: Why AOP — cross-cutting concerns
---

## 1. What it is

**Aspect-Oriented Programming (AOP)** is a programming paradigm that separates *cross-cutting concerns* — behaviour that cuts across many modules without belonging to any single one — from the core business logic. Examples: logging, security checks, transaction management, performance metrics, audit trails.

Without AOP, every service method that needs logging must explicitly call the logger. AOP lets you write that logging code *once*, in a separate module (an **aspect**), and apply it to hundreds of methods via a declarative rule.

## 2. Why & when

Object-Oriented Programming organises code by *things* (classes, objects). Cross-cutting concerns don't fit neatly into any one class because they touch everything:

```
UserService.register()   → needs: logging + transaction + security check
OrderService.place()     → needs: logging + transaction + security check
PaymentService.charge()  → needs: logging + transaction + security check
```

Without AOP, you repeat the same boilerplate in every method. With AOP, you declare the concern once and let the framework weave it into the call sites.

Use AOP when:
- The same infrastructure code (logging, timing, auditing) must appear in many unrelated classes.
- You want to enforce policies (security, retry) without touching business code.
- You need to add behaviour to third-party code you cannot modify.

Do **not** use AOP for core business logic — the indirection makes it harder to trace and debug.

## 3. Core concept

Think of a city's water pipes. Every building in the city needs water — but you don't run dedicated pipes through each building's walls. Instead, a shared main line (the cross-cutting concern) reaches every building through a uniform connection point. AOP is the main line; the buildings are your service classes; the connection points are method invocations.

Three flavours of cross-cutting concerns:

| Concern | Without AOP | With AOP |
|---------|-------------|----------|
| Logging | `log.info(...)` in every method | `@Before("execution(* com.example..*(..))")` logs once |
| Transactions | `txManager.begin()` / `commit()` / `rollback()` everywhere | `@Transactional` + one aspect |
| Security | `if (!user.hasRole(...)) throw` in every method | `@PreAuthorize("hasRole(...)")` + one aspect |

## 4. Diagram

<svg viewBox="0 0 640 220" xmlns="http://www.w3.org/2000/svg">
  <!-- Three services (columns) -->
  <rect x="40"  y="40" width="110" height="140" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="95"  y="65" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">UserService</text>
  <rect x="50"  y="80" width="90" height="28" rx="4" fill="#0d1117" stroke="#6db33f" stroke-width="1"/>
  <text x="95"  y="98" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">register()</text>
  <rect x="50"  y="116" width="90" height="28" rx="4" fill="#0d1117" stroke="#6db33f" stroke-width="1"/>
  <text x="95"  y="134" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">update()</text>

  <rect x="265" y="40" width="110" height="140" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="65" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">OrderService</text>
  <rect x="275" y="80" width="90" height="28" rx="4" fill="#0d1117" stroke="#6db33f" stroke-width="1"/>
  <text x="320" y="98" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">place()</text>
  <rect x="275" y="116" width="90" height="28" rx="4" fill="#0d1117" stroke="#6db33f" stroke-width="1"/>
  <text x="320" y="134" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">cancel()</text>

  <rect x="490" y="40" width="110" height="140" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="545" y="65" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">PaymentService</text>
  <rect x="500" y="80" width="90" height="28" rx="4" fill="#0d1117" stroke="#6db33f" stroke-width="1"/>
  <text x="545" y="98" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">charge()</text>
  <rect x="500" y="116" width="90" height="28" rx="4" fill="#0d1117" stroke="#6db33f" stroke-width="1"/>
  <text x="545" y="134" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">refund()</text>

  <!-- Cross-cutting bar (logging) -->
  <rect x="30" y="190" width="590" height="22" rx="5" fill="#79c0ff" opacity="0.18"/>
  <text x="320" y="206" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">Logging Aspect — cuts across all service methods</text>
</svg>

The logging aspect is one horizontal strip that cuts across all three services — neither service knows about it.

## 5. Runnable example

Scenario: a **service timer** — first manually scattering timing code, then using a Spring AOP aspect to centralise it, then adding conditional filtering by annotation.

### Level 1 — Basic

Timing code duplicated in every method — the problem AOP solves.

```java
// AopWhyDemo.java
public class AopWhyDemo {
    public static void main(String[] args) throws Exception {
        var svc = new OrderService();
        svc.place("order-1");
        svc.cancel("order-1");
    }
}

class OrderService {
    void place(String id) throws InterruptedException {
        long t0 = System.currentTimeMillis();
        // ... business logic ...
        Thread.sleep(120);
        System.out.println("placed " + id);
        System.out.println("place() took " + (System.currentTimeMillis() - t0) + " ms");
    }

    void cancel(String id) throws InterruptedException {
        long t0 = System.currentTimeMillis();
        // ... business logic ...
        Thread.sleep(60);
        System.out.println("cancelled " + id);
        System.out.println("cancel() took " + (System.currentTimeMillis() - t0) + " ms");
    }
}
```

How to run: `java AopWhyDemo.java`

Timing code is copy-pasted into every method. Add 50 methods → 50 copies to maintain. If you change the format, you touch 50 places.

---

### Level 2 — Intermediate

Extract the timing into a Spring AOP `@Around` advice that wraps every method in `OrderService` automatically.

```java
// AopWhyDemo.java
import org.springframework.context.annotation.*;
import org.springframework.stereotype.*;
import org.aspectj.lang.ProceedingJoinPoint;
import org.aspectj.lang.annotation.*;

@Configuration
@EnableAspectJAutoProxy
@ComponentScan
public class AopWhyDemo {
    public static void main(String[] args) throws Exception {
        var ctx = new AnnotationConfigApplicationContext(AopWhyDemo.class);
        var svc = ctx.getBean(OrderService.class);
        svc.place("order-1");
        svc.cancel("order-1");
        ctx.close();
    }
}

@Service
class OrderService {
    public void place(String id) throws InterruptedException {
        Thread.sleep(120);
        System.out.println("placed " + id);
    }
    public void cancel(String id) throws InterruptedException {
        Thread.sleep(60);
        System.out.println("cancelled " + id);
    }
}

@Aspect
@Component
class TimingAspect {
    @Around("execution(* OrderService.*(..))")
    public Object time(ProceedingJoinPoint pjp) throws Throwable {
        long t0 = System.currentTimeMillis();
        Object result = pjp.proceed();
        System.out.printf("%s() took %d ms%n",
            pjp.getSignature().getName(),
            System.currentTimeMillis() - t0);
        return result;
    }
}
```

How to run: `java -cp spring-context.jar:spring-aop.jar:aspectjweaver.jar:. AopWhyDemo.java`

`TimingAspect` contains the timing code once. Spring weaves it into every `OrderService` method via a proxy. `OrderService` has zero timing code.

---

### Level 3 — Advanced

Apply the aspect only to methods annotated with `@Timed` — a custom marker annotation — giving fine-grained control over which methods are measured.

```java
// AopWhyDemo.java
import org.springframework.context.annotation.*;
import org.springframework.stereotype.*;
import org.aspectj.lang.ProceedingJoinPoint;
import org.aspectj.lang.annotation.*;
import java.lang.annotation.*;

@Retention(RetentionPolicy.RUNTIME) @Target(ElementType.METHOD)
@interface Timed {}

@Configuration
@EnableAspectJAutoProxy
@ComponentScan
public class AopWhyDemo {
    public static void main(String[] args) throws Exception {
        var ctx = new AnnotationConfigApplicationContext(AopWhyDemo.class);
        var svc = ctx.getBean(OrderService.class);
        svc.place("order-1");    // @Timed — will be measured
        svc.cancel("order-1");   // not @Timed — no timing output
        svc.ship("order-1");     // @Timed — will be measured
        ctx.close();
    }
}

@Service
class OrderService {
    @Timed public void place(String id) throws InterruptedException {
        Thread.sleep(100); System.out.println("placed " + id);
    }
    public void cancel(String id) throws InterruptedException {
        Thread.sleep(50); System.out.println("cancelled " + id);
    }
    @Timed public void ship(String id) throws InterruptedException {
        Thread.sleep(80); System.out.println("shipped " + id);
    }
}

@Aspect
@Component
class TimingAspect {
    @Around("@annotation(Timed)")
    public Object time(ProceedingJoinPoint pjp) throws Throwable {
        long t0 = System.currentTimeMillis();
        Object result = pjp.proceed();
        System.out.printf("[TIMED] %s() = %d ms%n",
            pjp.getSignature().getName(),
            System.currentTimeMillis() - t0);
        return result;
    }
}
```

How to run: same classpath

`@annotation(Timed)` in the pointcut restricts the aspect to only methods bearing `@Timed`. `cancel()` runs without any timing overhead. This pattern avoids measuring every method in the codebase and gives per-method opt-in control.

## 6. Walkthrough

**Proxy creation:** When `AnnotationConfigApplicationContext` starts and sees `@EnableAspectJAutoProxy`, it registers `AnnotationAwareAspectJAutoProxyCreator` as a `BeanPostProcessor`. After creating `OrderService`, the post-processor checks whether any `@Aspect` bean has a matching pointcut. It finds `TimingAspect.time()` matches `@annotation(Timed)`, so it wraps the `OrderService` bean in a CGLIB proxy.

**Call flow for `svc.place("order-1")`:**
1. `svc` is the proxy, not the real `OrderService`.
2. Proxy intercepts the call, looks up the advice chain for `place`.
3. Finds `TimingAspect.time()` (an `@Around`).
4. Calls `TimingAspect.time(pjp)` — `pjp` is the join point for `OrderService.place`.
5. `time()` records `t0`, then calls `pjp.proceed()`.
6. `pjp.proceed()` invokes the real `OrderService.place("order-1")` — prints "placed order-1".
7. Control returns to `time()`, which computes elapsed time and prints it.
8. `time()` returns the result to the proxy, which returns it to the caller.

**Call flow for `svc.cancel("order-1")` (no `@Timed`):**
- Proxy checks advice chain for `cancel` — no match.
- Proxy calls the real `cancel()` directly. No timing code runs.

**State change table:**
| Step | In proxy | In advice | In real method |
|------|----------|-----------|----------------|
| `svc.place()` | intercept | `t0 = now` | sleeping 100 ms |
| after `pjp.proceed()` | — | compute elapsed | done |
| print | — | `[TIMED] place() = 103 ms` | — |

**Expected output:**
```
placed order-1
[TIMED] place() = 103 ms
cancelled order-1
shipped order-1
[TIMED] ship() = 82 ms
```

## 7. Gotchas & takeaways

> **AOP only intercepts calls through the proxy.** If `OrderService.place()` calls `this.cancel()` internally, the proxy is bypassed — `@Timed` on `cancel()` has no effect for that internal call. Always inject the bean and call through it.

> **AOP adds indirection — use it for infrastructure, not business logic.** When a bug spans "did the aspect run?", "did the method run?", "in what order?" it is hard to debug. Keep aspects narrow and mechanical.

- Cross-cutting concerns are not a design smell — they are a separate, legitimate concern. AOP gives them a proper home.
- Spring AOP is proxy-based and applies only to Spring-managed beans. It cannot intercept calls to `new OrderService()` directly.
- The three classic cross-cutting concerns in Spring: `@Transactional` (transactions), `@Cacheable` (caching), `@PreAuthorize` (security) — all implemented via AOP.
- AOP is "declarative" — you say *what* to intercept, not *how* to wire it. The framework resolves the wiring.
