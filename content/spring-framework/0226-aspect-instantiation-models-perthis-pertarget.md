---
card: spring-framework
gi: 226
slug: aspect-instantiation-models-perthis-pertarget
title: "Aspect instantiation models (perthis, pertarget)"
---

## 1. What it is

By default, Spring AOP creates one instance of each aspect bean — a **singleton** shared across all join point invocations. Aspect instantiation models change this: `perthis` and `pertarget` create **one aspect instance per proxied bean** instead of one shared instance. This allows each aspect instance to maintain per-bean state.

```java
@Aspect("perthis(execution(* com.example.service.*.*(..)))")
@Component
public class PerBeanAspect { ... }
```

The expression in `perthis(…)` or `pertarget(…)` is the pointcut that determines which beans participate. Each proxied bean matching the pointcut gets its own dedicated aspect instance.

## 2. Why & when

The singleton model is sufficient for stateless aspects (logging, security checks). But when you need **per-bean state** in the aspect, you need `perthis`/`pertarget`:

- **Per-bean call counting** — track how many times each service has been called, separately.
- **Per-bean rate limiting** — each bean has its own token bucket.
- **Per-bean accumulated context** — build up a request log per service instance.

The singleton aspect's fields are shared across all beans and all threads — if you add a mutable counter, it is shared. With `perthis`, each bean has its own aspect instance with its own fields.

Note: `@Scope(ConfigurableBeanFactory.SCOPE_PROTOTYPE)` on the aspect class is **not** the right solution — prototypes are created per call to `getBean`, not per proxied bean. Use `perthis`/`pertarget` instead.

## 3. Core concept

`perthis` creates a new aspect instance per **proxy object** (the AOP proxy). `pertarget` creates one per **target object** (the real bean). In practice they are equivalent for most Spring AOP setups because there is one proxy per target bean.

Difference:
- `perthis` — bound to the proxy; if the same target is wrapped by two different proxies, each proxy gets its own aspect instance.
- `pertarget` — bound to the target; both proxies sharing a target would share an aspect instance.

The instantiation model syntax replaces the default singleton pattern:

```java
@Aspect("perthis(servicePointcut())")
```

Spring's `AnnotationAwareAspectJAutoProxyCreator` detects the `perthis`/`pertarget` declaration and creates/caches aspect instances per bean. The aspect class must still be declared as a Spring bean (`@Component`) so Spring can manage the per-bean instances.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg">
  <!-- Singleton model (left) -->
  <rect x="15" y="20" width="270" height="165" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="150" y="42" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">Singleton (default)</text>

  <rect x="100" y="55" width="110" height="35" rx="5" fill="#0d1117" stroke="#6db33f" stroke-width="1.5"/>
  <text x="155" y="77" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">One aspect instance</text>

  <line x1="75" y1="108" x2="100" y2="73" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a)"/>
  <line x1="155" y1="90" x2="155" y2="108" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a)"/>
  <line x1="235" y1="108" x2="210" y2="73" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a)"/>

  <rect x="25" y="108" width="90" height="35" rx="5" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="70" y="129" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Bean A proxy</text>
  <rect x="115" y="108" width="80" height="35" rx="5" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="155" y="129" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Bean B proxy</text>
  <rect x="195" y="108" width="80" height="35" rx="5" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="235" y="129" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Bean C proxy</text>

  <text x="150" y="166" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">shared state — not per-bean</text>

  <!-- perthis model (right) -->
  <rect x="355" y="20" width="270" height="165" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="490" y="42" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">perthis — one instance per proxy</text>

  <rect x="370" y="55" width="80" height="35" rx="5" fill="#0d1117" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="410" y="77" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">Aspect for A</text>
  <rect x="450" y="55" width="80" height="35" rx="5" fill="#0d1117" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="490" y="77" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">Aspect for B</text>
  <rect x="530" y="55" width="80" height="35" rx="5" fill="#0d1117" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="570" y="77" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">Aspect for C</text>

  <line x1="410" y1="90" x2="410" y2="108" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#a2)"/>
  <line x1="490" y1="90" x2="490" y2="108" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#a2)"/>
  <line x1="570" y1="90" x2="570" y2="108" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#a2)"/>

  <rect x="365" y="108" width="80" height="35" rx="5" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="405" y="129" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Bean A proxy</text>
  <rect x="450" y="108" width="80" height="35" rx="5" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="490" y="129" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Bean B proxy</text>
  <rect x="535" y="108" width="80" height="35" rx="5" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="575" y="129" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Bean C proxy</text>

  <text x="490" y="166" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">isolated state — per-bean</text>

  <defs>
    <marker id="a"  markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto"><polygon points="0 0,8 3,0 6" fill="#6db33f"/></marker>
    <marker id="a2" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto"><polygon points="0 0,8 3,0 6" fill="#79c0ff"/></marker>
  </defs>
</svg>

Singleton: all beans share one aspect instance. `perthis`: each proxied bean has its own dedicated aspect instance.

## 5. Runnable example

Scenario: a **call counter** that tracks how many times each service bean has been called — impossible with a singleton aspect, straightforward with `perthis`.

### Level 1 — Basic

Singleton aspect problem: counter is shared across all beans.

```java
// PerBeanDemo.java
import org.springframework.context.annotation.*;
import org.springframework.stereotype.*;
import org.aspectj.lang.annotation.*;

@Configuration
@EnableAspectJAutoProxy
@ComponentScan
public class PerBeanDemo {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(PerBeanDemo.class);
        ctx.getBean(StockService.class).getPrice("AAPL");
        ctx.getBean(StockService.class).getPrice("GOOG");
        ctx.getBean(NewsService.class).getHeadlines();
        System.out.println("Counter (wrong — shared): "
            + ctx.getBean(CallCounterAspect.class).count);
        ctx.close();
    }
}

@Service class StockService { public String getPrice(String s)  { System.out.println("price: " + s); return "100"; } }
@Service class NewsService  { public String getHeadlines()      { System.out.println("headlines"); return "news"; } }

@Aspect
@Component
class CallCounterAspect {
    int count = 0; // shared across ALL beans — wrong for per-bean tracking

    @Before("execution(* StockService.*(..)) || execution(* NewsService.*(..))")
    public void count() { count++; }
}
```

How to run: `java -cp spring-context.jar:spring-aop.jar:aspectjweaver.jar:. PerBeanDemo.java`

Counter shows 3 — total across both beans, not per-bean.

---

### Level 2 — Intermediate

Use `perthis` — each bean gets its own aspect instance with its own counter.

```java
// PerBeanDemo.java
import org.springframework.context.annotation.*;
import org.springframework.stereotype.*;
import org.aspectj.lang.*;
import org.aspectj.lang.annotation.*;

@Configuration
@EnableAspectJAutoProxy
@ComponentScan
public class PerBeanDemo {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(PerBeanDemo.class);
        var stocks = ctx.getBean(StockService.class);
        var news   = ctx.getBean(NewsService.class);

        stocks.getPrice("AAPL");
        stocks.getPrice("GOOG");
        stocks.getPrice("MSFT");
        news.getHeadlines();
        news.getHeadlines();

        // Each proxy has its own aspect instance — retrieve via AopUtils
        System.out.println("Stock calls: " + getCounter(stocks));
        System.out.println("News calls:  " + getCounter(news));
        ctx.close();
    }

    static int getCounter(Object proxy) {
        // The aspect instance is stored on the proxy's Advised object
        var advised = (org.springframework.aop.framework.Advised) proxy;
        try {
            for (var advisor : advised.getAdvisors()) {
                if (advisor.getAdvice() instanceof PerBeanCounterAspect a) return a.count;
            }
        } catch (Exception ignored) {}
        return -1;
    }
}

@Service class StockService { public String getPrice(String s) { System.out.println("price: " + s); return "100"; } }
@Service class NewsService  { public String getHeadlines()     { System.out.println("news"); return "x"; } }

// perthis: one instance per proxy for all classes matching the pointcut
@Aspect("perthis(execution(* StockService.*(..)) || execution(* NewsService.*(..)))")
@Component
class PerBeanCounterAspect {
    int count = 0;

    @Before("execution(* StockService.*(..)) || execution(* NewsService.*(..))")
    public void countCall() { count++; }
}
```

How to run: same classpath

`StockService` proxy has its own `PerBeanCounterAspect` with count=3. `NewsService` proxy has its own with count=2. The counters are independent.

---

### Level 3 — Advanced

`pertarget` variant — one aspect per target bean. Demonstrate per-target rate limiting with a configurable limit injected via `@Value`.

```java
// PerBeanDemo.java
import org.springframework.context.annotation.*;
import org.springframework.stereotype.*;
import org.aspectj.lang.*;
import org.aspectj.lang.annotation.*;

@Configuration
@EnableAspectJAutoProxy
@ComponentScan
public class PerBeanDemo {
    public static void main(String[] args) throws Exception {
        var ctx = new AnnotationConfigApplicationContext(PerBeanDemo.class);
        var svc = ctx.getBean(StockService.class);

        System.out.println("Firing 7 calls (limit=5):");
        for (int i = 1; i <= 7; i++) {
            try {
                svc.getPrice("TICK");
            } catch (IllegalStateException e) {
                System.out.println("  Call " + i + " BLOCKED: " + e.getMessage());
            }
        }
        ctx.close();
    }
}

@Service
class StockService {
    public String getPrice(String ticker) {
        System.out.println("  price: " + ticker);
        return "100";
    }
}

// pertarget: one instance per TARGET bean (not per proxy)
@Aspect("pertarget(execution(* StockService.*(..)))")
@Component
class PerTargetRateLimitAspect {
    private int calls = 0;
    private static final int LIMIT = 5;

    @Before("execution(* StockService.*(..))")
    public void check() {
        if (++calls > LIMIT) {
            throw new IllegalStateException("Rate limit exceeded: " + calls + "/" + LIMIT);
        }
        System.out.println("  [RATE] call " + calls + "/" + LIMIT);
    }
}
```

How to run: same classpath

`pertarget` creates one aspect instance per target `StockService` bean. The `calls` counter is per-bean and per-thread-safe only in single-threaded use; in production, use `AtomicInteger`. Calls 6 and 7 are blocked.

## 6. Walkthrough

**`perthis` instantiation mechanics (Level 2):**
1. At startup, Spring registers `PerBeanCounterAspect` not as a singleton but with `perthis` scope.
2. When creating the proxy for `StockService`, Spring checks: does this proxy match `execution(* StockService.*(..)) || execution(* NewsService.*(..))`? Yes.
3. Spring creates a new `PerBeanCounterAspect` instance specifically for `StockService`'s proxy.
4. This instance is stored in the proxy's `Advised` advisor list.
5. Same process for `NewsService` → separate `PerBeanCounterAspect` instance.
6. When `stocks.getPrice("AAPL")` fires, the proxy looks up *its own* `PerBeanCounterAspect` → increments its own counter.

**`perthis` vs `pertarget` (Level 3):**
- `perthis`: aspect instance is keyed to the proxy object. Two proxies wrapping the same target → two aspect instances.
- `pertarget`: aspect instance is keyed to the target object. Two proxies wrapping the same target → one shared aspect instance.
- For typical Spring apps (one proxy per bean), they are equivalent.

**State isolation verification:**
```
stocks.getPrice × 3 → StockAspect.count = 3
news.getHeadlines × 2 → NewsAspect.count = 2
(These are completely separate objects)
```

## 7. Gotchas & takeaways

> **`perthis`/`pertarget` aspects are NOT singletons and cannot be retrieved via `ctx.getBean(MyAspect.class)`.** The context holds a per-proxy instance, not a shared one. You must reach in through the proxy's `Advised` interface to access the per-bean instance.

> **`perthis`/`pertarget` aspects must still be `@Component` (or declared as `@Bean`).** Spring uses the bean definition as a template to create per-proxy instances. Without it, Spring cannot instantiate the aspect at all.

- Per-bean aspect state is not thread-safe by default — if multiple threads call the same bean concurrently, they share the same aspect instance. Use `AtomicInteger` or `ConcurrentHashMap` for per-bean state.
- The `perthis(…)` expression is not a normal `@Pointcut` — it uses the same syntax but it selects *which beans participate in per-instance creation*, not which join points receive advice.
- `perthis` and `pertarget` are rare. Prefer `@DeclareParents` (introduction) for per-bean state — it is more explicit and testable.
- Per-bean aspects increase memory usage: N beans × aspect instance size. Use with care in large application contexts.
