---
card: spring-boot
gi: 48
slug: lazy-initialization
title: Lazy initialization
---

## 1. What it is

**Lazy initialization** tells Spring Boot to create beans only when they are first needed, rather than creating all beans eagerly at startup. By default Spring Boot creates every singleton bean during context refresh — lazy initialization defers creation to the moment the bean is first injected or requested.

Enable globally:
```properties
spring.main.lazy-initialization=true
```

Or per-bean:
```java
@Service
@Lazy
public class HeavyReportGenerator { ... }
```

## 2. Why & when

Startup time is the main driver. Applications with hundreds of beans can spend seconds constructing and wiring objects that are never used during a typical request (e.g. admin endpoints, batch exporters, rarely-used integrations). Lazy initialization skips all of that until the bean is actually needed.

Use lazy initialization when:
- Startup time is a critical metric (serverless functions, Kubernetes readiness probes, developer inner loops).
- Your app has many beans but only a subset are needed per request path.
- You want to identify unused beans (if a bean is never created, it is never needed).

Do not rely on it as a substitute for good architecture. Lazy beans defer — not eliminate — initialisation cost, and move failures from startup to first use.

## 3. Core concept

Think of a restaurant kitchen. Eager initialization is mise en place — every ingredient is prepped before service starts. Lazy initialization is à la minute — ingredients are prepared only when a dish is ordered. Mise en place makes service fast but prep time is long; à la minute starts faster but the first order of a dish is slower.

Spring Boot lazy initialization rules:
1. A lazy bean is created when its dependency is first requested — through `@Autowired`, `ApplicationContext.getBean()`, or AOP proxy invocation.
2. If a lazy bean has a configuration error (missing dependency, wrong type), the error surfaces on first use rather than at startup — a tradeoff.
3. Singleton lazy beans are created at most once; after first creation they behave identically to eager singletons.
4. `@Lazy` on an injection point (not on the bean class) injects a proxy that defers creation to first method call — useful for optional dependencies.

## 4. Diagram

<svg viewBox="0 0 660 240" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Eager vs lazy bean creation timeline comparison">
  <!-- Timeline bar -->
  <line x1="20" y1="200" x2="640" y2="200" stroke="#8b949e" stroke-width="1.5" marker-end="url(#lt)"/>
  <text x="20" y="220" fill="#8b949e" font-size="10" font-family="sans-serif">startup</text>
  <text x="580" y="220" fill="#8b949e" font-size="10" font-family="sans-serif">request 1</text>

  <!-- Eager row -->
  <text x="20" y="44" fill="#e6edf3" font-size="11" font-family="monospace">Eager (default)</text>
  <rect x="20" y="54" width="340" height="28" rx="4" fill="#6db33f" fill-opacity="0.25" stroke="#6db33f" stroke-width="1.5"/>
  <text x="190" y="73" fill="#6db33f" font-size="10" font-family="monospace" text-anchor="middle">all beans created at startup</text>
  <rect x="370" y="54" width="80" height="28" rx="4" fill="#6db33f" fill-opacity="0.15" stroke="#6db33f" stroke-width="1"/>
  <text x="410" y="73" fill="#6db33f" font-size="10" font-family="monospace" text-anchor="middle">fast req</text>

  <!-- Lazy row -->
  <text x="20" y="114" fill="#e6edf3" font-size="11" font-family="monospace">Lazy (spring.main.lazy-initialization=true)</text>
  <rect x="20" y="124" width="80" height="28" rx="4" fill="#79c0ff" fill-opacity="0.2" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="60" y="143" fill="#79c0ff" font-size="10" font-family="monospace" text-anchor="middle">fast start</text>
  <rect x="370" y="124" width="180" height="28" rx="4" fill="#79c0ff" fill-opacity="0.2" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="460" y="143" fill="#79c0ff" font-size="10" font-family="monospace" text-anchor="middle">beans created on first use</text>

  <!-- Arrows to timeline -->
  <line x1="190" y1="82" x2="190" y2="198" stroke="#6db33f" stroke-width="1" stroke-dasharray="3,3"/>
  <line x1="60" y1="152" x2="60" y2="198" stroke="#79c0ff" stroke-width="1" stroke-dasharray="3,3"/>
  <line x1="460" y1="152" x2="460" y2="198" stroke="#79c0ff" stroke-width="1" stroke-dasharray="3,3"/>

  <defs>
    <marker id="lt" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/>
    </marker>
  </defs>
</svg>

Eager initialization front-loads all cost to startup; lazy defers bean creation to first use, making startup faster at the cost of slower first requests.

## 5. Runnable example

```java
// LazyInitDemo.java
// How to run: java LazyInitDemo.java  (JDK 17+)
// Simulates eager vs lazy bean initialization and shows the timing difference.

import java.util.*;

public class LazyInitDemo {

    // ── Simulated beans ────────────────────────────────────────────
    static class ReportService {
        ReportService() {
            simulate("ReportService initialised (heavy DB schema scan)", 300);
        }
        String report() { return "Report generated"; }
    }

    static class EmailService {
        EmailService() {
            simulate("EmailService initialised (SMTP connection pool)", 200);
        }
        String send(String msg) { return "Sent: " + msg; }
    }

    static class RequestService {
        RequestService() {
            simulate("RequestService initialised", 50);
        }
        String handle() { return "Request handled"; }
    }

    // ── Context simulation ─────────────────────────────────────────
    static Map<String, Object> context = new LinkedHashMap<>();
    static Map<String, java.util.function.Supplier<?>> lazyDefs = new LinkedHashMap<>();

    public static void main(String[] args) throws Exception {
        System.out.println("=== Eager initialization ===");
        long start = System.currentTimeMillis();
        context.put("reportService", new ReportService());
        context.put("emailService",  new EmailService());
        context.put("requestService",new RequestService());
        long startupMs = System.currentTimeMillis() - start;
        System.out.printf("Startup time: %dms%n%n", startupMs);

        System.out.println("Handling request (all beans already initialised):");
        long reqStart = System.currentTimeMillis();
        RequestService rs = (RequestService) context.get("requestService");
        System.out.println("  " + rs.handle());
        System.out.printf("Request time: %dms%n%n%n", System.currentTimeMillis() - reqStart);

        // ── Lazy ──────────────────────────────────────────────────
        System.out.println("=== Lazy initialization ===");
        lazyDefs.put("reportService", ReportService::new);
        lazyDefs.put("emailService",  EmailService::new);
        lazyDefs.put("requestService", RequestService::new);
        context.clear();

        start = System.currentTimeMillis();
        // Startup: just register suppliers, don't create beans
        System.out.println("(beans registered as lazy — none created yet)");
        startupMs = System.currentTimeMillis() - start;
        System.out.printf("Startup time: %dms%n%n", startupMs);

        System.out.println("Handling request (creates RequestService on first use):");
        reqStart = System.currentTimeMillis();
        RequestService lazyRs = (RequestService) getBean("requestService");
        System.out.println("  " + lazyRs.handle());
        System.out.printf("First-request time: %dms (includes bean init)%n", System.currentTimeMillis() - reqStart);
    }

    @SuppressWarnings("unchecked")
    static <T> T getBean(String name) {
        if (!context.containsKey(name) && lazyDefs.containsKey(name)) {
            context.put(name, lazyDefs.get(name).get());
        }
        return (T) context.get(name);
    }

    static void simulate(String msg, int ms) {
        try { Thread.sleep(ms); } catch (InterruptedException e) {}
        System.out.println("  " + msg);
    }
}
```

**How to run:** `java LazyInitDemo.java`

Expected output (timings approximate):
```
=== Eager initialization ===
  ReportService initialised (heavy DB schema scan)
  EmailService initialised (SMTP connection pool)
  RequestService initialised
Startup time: ~555ms

Handling request (all beans already initialised):
  Request handled
Request time: ~0ms


=== Lazy initialization ===
(beans registered as lazy — none created yet)
Startup time: ~0ms

Handling request (creates RequestService on first use)
  RequestService initialised
  Request handled
First-request time: ~55ms (includes bean init)
```

## 6. Walkthrough

- In eager mode, all three constructors run at startup, summing to ~550ms. The request itself is instant because beans are ready.
- In lazy mode, `lazyDefs` stores `Supplier` lambdas instead of instances. Startup records near-zero milliseconds because no constructors run.
- `getBean()` calls the supplier only on first access — simulating Spring's lazy proxy mechanism.
- The first request to `requestService` now includes the 50ms constructor delay. `ReportService` and `EmailService` were never requested so they are never created.
- In a real Spring Boot app, beans that are never requested stay as proxy stubs forever — their constructors never run.

## 7. Gotchas & takeaways

> With global lazy initialization, configuration errors (missing `@Bean`, wrong type, circular dependency) are not caught at startup — they surface as `BeanCreationException` on the first request that triggers the bean. This converts an obvious startup failure into a runtime failure that may be harder to debug.

> Lazy initialization interacts badly with `@EventListener` beans. If a bean that listens for the `ApplicationReadyEvent` is lazy, it won't be created at startup and will miss the event entirely.

- Enable globally: `spring.main.lazy-initialization=true`; override per-bean with `@Lazy(false)` to force eagerness.
- `@Lazy` on an `@Autowired` injection point creates a proxy, not a lazy bean — the real bean is created on first proxy method call, allowing circular dependencies to be broken.
- Actuator's `/actuator/beans` endpoint shows instantiation state; use it to verify which beans were actually created.
- In serverless (AWS Lambda, GCP Cloud Functions): lazy init combined with Spring Native / GraalVM native image gives the fastest cold-start times.
- Test suites that use lazy initialization should still use `@SpringBootTest` with `webEnvironment = NONE` for fast test startup independent of lazy production settings.
