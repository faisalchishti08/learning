---
card: spring-framework
gi: 87
slug: multiple-beanpostprocessors-ordering
title: Multiple BeanPostProcessors & ordering
---

## 1. What it is

When multiple `BeanPostProcessor` instances are registered in the same container, Spring applies them **all** to every bean — and the order in which they run matters. Spring determines BPP ordering via three interfaces: `PriorityOrdered` (run first, sorted by `getOrder()`), `Ordered` (run second, sorted by `getOrder()`), and unordered BPPs (run last). Within each tier, lower `getOrder()` values run first. The default ordering constant is `Ordered.LOWEST_PRECEDENCE` (= `Integer.MAX_VALUE`).

```java
import org.springframework.core.PriorityOrdered;
import org.springframework.core.Ordered;

@Component
public class SecurityBPP implements BeanPostProcessor, PriorityOrdered {
    @Override public int getOrder() { return 1; }  // runs very early
    // ...
}

@Component
public class MetricsBPP implements BeanPostProcessor, Ordered {
    @Override public int getOrder() { return 100; } // runs after PriorityOrdered BPPs
    // ...
}

@Component
public class LoggingBPP implements BeanPostProcessor {
    // no Ordered impl → runs last (unordered tier)
    // ...
}
```

In one sentence: **Multiple `BeanPostProcessor` beans run on every bean in a fixed three-tier order — `PriorityOrdered` first, `Ordered` second, unordered last — with lower `getOrder()` values winning within each tier, enabling predictable stacking of proxies and transformations.**

## 2. Why & when

Ordering matters when:

- BPP A wraps a bean in a **security proxy**, and BPP B then wraps the result in a **caching proxy** — the wrapping order determines which advice fires first on each call.
- A **validation BPP** must see the original bean class annotations before an **AOP proxying BPP** replaces the bean with a CGLIB proxy (which may hide those annotations).
- Spring's own AOP infrastructure uses `PriorityOrdered` — your application BPPs should use `Ordered` or unordered so they run after Spring's core processing.

Do NOT implement `PriorityOrdered` for application-level BPPs — that tier is for Spring's internal machinery. Use `Ordered` with a reasonable value (e.g., 100) for most application BPPs.

## 3. Core concept

```
Three-tier BPP ordering:

  Tier 1 — PriorityOrdered (lowest getOrder() first):
    Spring's infrastructure BPPs (AutowiredAnnotationBPP, CommonAnnotationBPP)
    Run BEFORE any @Autowired processing has occurred on other BPPs

  Tier 2 — Ordered (lowest getOrder() first):
    Application BPPs that need to run before others but after Spring infra

  Tier 3 — Unordered (registration order, often non-deterministic):
    Simple BPPs with no ordering requirements

Within each tier: lower getOrder() = runs earlier

Constants:
  Ordered.HIGHEST_PRECEDENCE = Integer.MIN_VALUE   → runs first in tier
  Ordered.LOWEST_PRECEDENCE  = Integer.MAX_VALUE   → runs last in tier

Proxy stacking — order determines call chain at runtime:
  If BPP-A (order 1) wraps bean in ProxyA,
  and BPP-B (order 2) then wraps ProxyA in ProxyB:
    runtime call chain: caller → ProxyB → ProxyA → original bean
    (LAST proxy added = OUTERMOST proxy)

Spring's own BPPs (for reference):
  AutowiredAnnotationBeanPostProcessor  PriorityOrdered, order=Ordered.LOWEST_PRECEDENCE - 2
  CommonAnnotationBeanPostProcessor     PriorityOrdered, order=Ordered.LOWEST_PRECEDENCE - 3
  AbstractAdvisorAutoProxyCreator       Ordered (AOP proxy creator)
```

## 4. Diagram

<svg viewBox="0 0 680 210" xmlns="http://www.w3.org/2000/svg" role="auth" aria-label="Three BPPs in order — proxy stacking creates call chain">
  <defs>
    <marker id="a87" markerWidth="8" markerHeight="6" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="b87" markerWidth="8" markerHeight="6" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>
  <rect x="5" y="5" width="670" height="198" rx="8" fill="#0d1117" stroke="#8b949e" stroke-width="1.2"/>
  <text x="338" y="22" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Three BPPs run in order → last BPP produces outermost proxy</text>

  <!-- Left: BPP processing order (registration order = processing order) -->
  <text x="15" y="42" fill="#8b949e" font-size="8.5" font-family="sans-serif">Processing order →</text>

  <rect x="15"  y="48" width="130" height="45" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1.3"/>
  <text x="80"  y="68" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">BPP-A (order=1)</text>
  <text x="80"  y="82" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">PriorityOrdered</text>

  <line x1="145" y1="70" x2="157" y2="70" stroke="#6db33f" stroke-width="1.2" marker-end="url(#a87)"/>

  <rect x="160" y="48" width="130" height="45" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1.1"/>
  <text x="225" y="68" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">BPP-B (order=10)</text>
  <text x="225" y="82" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">Ordered</text>

  <line x1="290" y1="70" x2="302" y2="70" stroke="#6db33f" stroke-width="1.2" marker-end="url(#a87)"/>

  <rect x="305" y="48" width="130" height="45" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="370" y="68" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">BPP-C (unordered)</text>
  <text x="370" y="82" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">last tier</text>

  <line x1="435" y1="70" x2="447" y2="70" stroke="#6db33f" stroke-width="1.2" marker-end="url(#a87)"/>

  <rect x="450" y="48" width="100" height="45" rx="4" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="500" y="68" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">ProxyC wraps</text>
  <text x="500" y="82" fill="#79c0ff" font-size="7" text-anchor="middle" font-family="sans-serif">ProxyB(ProxyA(bean))</text>

  <!-- Right: runtime call chain (reverse) -->
  <text x="338" y="112" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="sans-serif">Runtime call chain (outermost proxy = LAST one added):</text>

  <rect x="10"  y="120" width="80"  height="28" rx="3" fill="#1c2430" stroke="#8b949e"/>
  <text x="50"  y="138" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">caller</text>
  <line x1="90" y1="134" x2="100" y2="134" stroke="#79c0ff" stroke-width="1.2" marker-end="url(#b87)"/>

  <rect x="103" y="120" width="110" height="28" rx="3" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="158" y="138" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">ProxyC (BPP-C last)</text>
  <line x1="213" y1="134" x2="223" y2="134" stroke="#79c0ff" stroke-width="1.2" marker-end="url(#b87)"/>

  <rect x="226" y="120" width="110" height="28" rx="3" fill="#1c2430" stroke="#6db33f" stroke-width="1.2"/>
  <text x="281" y="138" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">ProxyB (BPP-B)</text>
  <line x1="336" y1="134" x2="346" y2="134" stroke="#6db33f" stroke-width="1.2" marker-end="url(#a87)"/>

  <rect x="349" y="120" width="110" height="28" rx="3" fill="#1c2430" stroke="#6db33f" stroke-width="1.2"/>
  <text x="404" y="138" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">ProxyA (BPP-A)</text>
  <line x1="459" y1="134" x2="469" y2="134" stroke="#6db33f" stroke-width="1.2" marker-end="url(#a87)"/>

  <rect x="472" y="120" width="90"  height="28" rx="3" fill="#1c2430" stroke="#8b949e"/>
  <text x="517" y="138" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">original bean</text>

  <!-- Note -->
  <text x="338" y="172" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="sans-serif">Order: lower getOrder() = earlier processing = INNER proxy at runtime.</text>
  <text x="338" y="186" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="sans-serif">To run FIRST at call time, use HIGHER order (outermost). To read annotations, use lower order.</text>
</svg>

BPP-A (lowest order) processes first and produces the innermost proxy. BPP-C (unordered, last) wraps everything else, making it the outermost proxy at runtime.

## 5. Runnable example

Scenario: three chained BPPs — a security BPP (order 1), a caching BPP (order 10), and a logging BPP (unordered) — each wraps the service in a proxy. We show the processing order and the resulting call chain.

### Level 1 — Basic

Two BPPs with explicit ordering — show they fire in the right order.

```java
// MultiBPPDemo.java — run with: java MultiBPPDemo.java
import java.util.*;

public class MultiBPPDemo {

    interface BeanPostProcessor { Object after(Object bean, String name); }
    interface Ordered            { int getOrder(); }
    interface PriorityOrdered extends Ordered {}

    static final List<String> PROCESSING_LOG = new ArrayList<>();
    static final List<String> CALL_LOG       = new ArrayList<>();

    // ── Simple wrapper proxy ──────────────────────────────────────────
    interface Service { String execute(String input); }

    static class ServiceImpl implements Service {
        @Override public String execute(String input) {
            System.out.println("    [ServiceImpl.execute] " + input);
            return "result:" + input;
        }
    }

    static class WrappedService implements Service {
        private final Service delegate;
        private final String  label;
        WrappedService(Service d, String label) { this.delegate=d; this.label=label; }
        @Override public String execute(String input) {
            System.out.println("  [" + label + ".before] " + input);
            CALL_LOG.add(label + ".before");
            String r = delegate.execute(input);
            System.out.println("  [" + label + ".after]  " + r);
            CALL_LOG.add(label + ".after");
            return r;
        }
    }

    // ── BPP-A: PriorityOrdered, order=1 — runs FIRST in processing ───
    static class SecurityBPP implements BeanPostProcessor, PriorityOrdered {
        @Override public int getOrder() { return 1; }
        @Override public Object after(Object bean, String name) {
            PROCESSING_LOG.add("SecurityBPP.after(" + name + ")");
            System.out.println("[BPP] SecurityBPP wrapping '" + name + "' (PriorityOrdered, order=1)");
            return bean instanceof Service s ? new WrappedService(s, "SecurityProxy") : bean;
        }
    }

    // ── BPP-B: Ordered, order=10 — runs SECOND ───────────────────────
    static class CachingBPP implements BeanPostProcessor, Ordered {
        @Override public int getOrder() { return 10; }
        @Override public Object after(Object bean, String name) {
            PROCESSING_LOG.add("CachingBPP.after(" + name + ")");
            System.out.println("[BPP] CachingBPP wrapping '" + name + "' (Ordered, order=10)");
            return bean instanceof Service s ? new WrappedService(s, "CacheProxy") : bean;
        }
    }

    // ── BPP-C: unordered — runs LAST ─────────────────────────────────
    static class LoggingBPP implements BeanPostProcessor {
        @Override public Object after(Object bean, String name) {
            PROCESSING_LOG.add("LoggingBPP.after(" + name + ")");
            System.out.println("[BPP] LoggingBPP wrapping '" + name + "' (unordered, runs last)");
            return bean instanceof Service s ? new WrappedService(s, "LogProxy") : bean;
        }
    }

    // ── Simulated container: apply BPPs in PriorityOrdered→Ordered→unordered order ──
    static Service createBean(List<BeanPostProcessor> bpps) {
        Service bean = new ServiceImpl();
        for (BeanPostProcessor bpp : bpps)
            bean = (Service) bpp.after(bean, "myService");
        return bean;
    }

    public static void main(String[] args) {
        System.out.println("=== Container: applying BPPs in order ===");
        // Ordered: SecurityBPP (PriorityOrdered, 1), CachingBPP (Ordered, 10), LoggingBPP (unordered)
        List<BeanPostProcessor> bpps = List.of(
            new SecurityBPP(),  // tier 1, order 1 → first
            new CachingBPP(),   // tier 2, order 10 → second
            new LoggingBPP()    // tier 3, unordered → third
        );
        Service service = createBean(bpps);

        System.out.println("\n[PROCESSING ORDER] " + PROCESSING_LOG);
        System.out.println("[OUTER PROXY] " + service.getClass().getSimpleName());

        System.out.println("\n=== Runtime call chain ===");
        CALL_LOG.clear();
        String result = service.execute("test-input");
        System.out.println("[RESULT] " + result);
        System.out.println("[CALL ORDER] " + CALL_LOG);
        System.out.println("[OUTERMOST PROXY = LAST BPP] LogProxy is outermost: " + CALL_LOG.get(0).startsWith("LogProxy"));
    }
}
```

How to run: `java MultiBPPDemo.java`

Processing order: `SecurityBPP` (1st) → `CachingBPP` (2nd) → `LoggingBPP` (3rd). Runtime call chain is reversed: `LogProxy` (outermost, added last) → `CacheProxy` → `SecurityProxy` → `ServiceImpl`. The last BPP to wrap becomes the caller's entry point.

### Level 2 — Intermediate

BPP ordering determines who reads the original class annotations before proxying.

```java
// MultiBPPDemo2.java — run with: java MultiBPPDemo2.java
import java.lang.annotation.*;
import java.util.*;

public class MultiBPPDemo2 {

    interface BPP { Object after(Object bean, String name); }
    interface Ordered { int getOrder(); }

    // ── Custom annotation on original class ───────────────────────────
    @Retention(RetentionPolicy.RUNTIME) @Target(ElementType.TYPE) @interface Auditable { String entity(); }
    @Retention(RetentionPolicy.RUNTIME) @Target(ElementType.TYPE) @interface Transactional {}

    // ── Service with annotations ──────────────────────────────────────
    @Auditable(entity="PRODUCT") @Transactional
    interface ProductRepo { String save(String data); }

    @Auditable(entity="PRODUCT") @Transactional
    static class ProductRepoImpl implements ProductRepo {
        @Override public String save(String data) { System.out.println("    [DB.save] " + data); return "saved:" + data; }
    }

    // ── Wrapper ───────────────────────────────────────────────────────
    static class AnnotationRecord { String name; boolean auditable; boolean transactional; }

    static class AnnotationScanBPP implements BPP, Ordered {
        final List<AnnotationRecord> records = new ArrayList<>();
        @Override public int getOrder() { return 1; }  // runs FIRST — sees original class

        @Override
        public Object after(Object bean, String name) {
            // Read annotations from bean.getClass() — must run before proxying BPP
            AnnotationRecord r = new AnnotationRecord();
            r.name         = name;
            r.auditable    = bean.getClass().isAnnotationPresent(Auditable.class);
            r.transactional = bean.getClass().isAnnotationPresent(Transactional.class);
            records.add(r);
            String entity  = r.auditable ? bean.getClass().getAnnotation(Auditable.class).entity() : "N/A";
            System.out.printf("[BPP-Scan order=1] bean='%s' @Auditable=%s(entity=%s) @Tx=%s%n",
                name, r.auditable, entity, r.transactional);
            return bean; // pass-through — just reads, doesn't modify
        }
    }

    static class TxProxyBPP implements BPP, Ordered {
        @Override public int getOrder() { return 10; }  // runs SECOND — wraps in proxy

        @Override
        public Object after(Object bean, String name) {
            if (bean.getClass().isAnnotationPresent(Transactional.class)) {
                System.out.println("[BPP-Tx   order=10] wrapping '" + name + "' in TxProxy");
                ProductRepo original = (ProductRepo) bean;
                return (ProductRepo) data -> {
                    System.out.println("    [TxProxy] begin transaction");
                    String r = original.save(data);
                    System.out.println("    [TxProxy] commit");
                    return r;
                };
            }
            return bean;
        }
    }

    static class AuditProxyBPP implements BPP {
        // unordered — runs LAST (after TxProxyBPP created a proxy)
        // If this ran FIRST, it would wrap in an audit proxy and then Tx proxy couldn't
        // find @Transactional on the audit proxy class!

        @Override
        public Object after(Object bean, String name) {
            // Must check original class annotation via TxProxy lambda — it wraps repo
            System.out.println("[BPP-Audit unordered] checking '" + name + "' for @Auditable");
            // In a real BPP, you'd use AopProxyUtils.ultimateTargetClass(bean) to get the original
            // For simplicity, we check the name
            if (name.contains("Repo")) {
                System.out.println("[BPP-Audit unordered] wrapping '" + name + "' in AuditProxy");
                ProductRepo delegate = (ProductRepo) bean;
                return (ProductRepo) data -> {
                    System.out.println("    [AuditProxy] logging: save(" + data + ")");
                    String r = delegate.save(data);
                    System.out.println("    [AuditProxy] audit entry written");
                    return r;
                };
            }
            return bean;
        }
    }

    @SuppressWarnings("unchecked")
    static <T> T createBean(T bean, String name, List<BPP> bpps) {
        Object result = bean;
        for (BPP bpp : bpps) result = bpp.after(result, name);
        return (T) result;
    }

    public static void main(String[] args) {
        System.out.println("=== BPPs ordered: Scan(1) → Tx(10) → Audit(unordered) ===");
        AnnotationScanBPP scan  = new AnnotationScanBPP();
        TxProxyBPP        tx    = new TxProxyBPP();
        AuditProxyBPP     audit = new AuditProxyBPP();

        ProductRepo repo = createBean(new ProductRepoImpl(), "productRepo", List.of(scan, tx, audit));

        System.out.println("\n[SCAN RECORDS] ");
        scan.records.forEach(r -> System.out.printf("  %s: auditable=%s tx=%s%n", r.name, r.auditable, r.transactional));

        System.out.println("\n=== Runtime call: caller → AuditProxy → TxProxy → DB ===");
        repo.save("product data");
    }
}
```

How to run: `java MultiBPPDemo2.java`

`AnnotationScanBPP` (order=1) runs first and reads `@Auditable` / `@Transactional` directly from the original `ProductRepoImpl.class`. If it ran after `TxProxyBPP`, it would try to read annotations from the Tx proxy (a lambda), finding nothing. `TxProxyBPP` (order=10) wraps in a transaction proxy. `AuditProxyBPP` (unordered, last) wraps the Tx proxy. Runtime: `AuditProxy` → `TxProxy` → `DB`.

### Level 3 — Advanced

`BeanPostProcessor` ordering with conditional skipping and a shared registry that later BPPs read from earlier BPPs.

```java
// MultiBPPDemo3.java — run with: java MultiBPPDemo3.java
import java.lang.annotation.*;
import java.util.*;
import java.util.concurrent.*;
import java.util.concurrent.atomic.*;

public class MultiBPPDemo3 {

    interface BPP { Object after(Object bean, String name); }
    interface Ordered { int getOrder(); }

    @Retention(RetentionPolicy.RUNTIME) @Target(ElementType.TYPE) @interface Monitored { String namespace() default "default"; }
    @Retention(RetentionPolicy.RUNTIME) @Target(ElementType.TYPE) @interface RateLimit  { int rpm(); }

    interface PaymentGateway { String charge(String amount, String card); }

    @Monitored(namespace="payments") @RateLimit(rpm=100)
    static class StripeGateway implements PaymentGateway {
        @Override public String charge(String amount, String card) {
            System.out.println("    [Stripe.charge] " + amount + " card=*" + card.substring(card.length()-4));
            return "txn_" + (int)(Math.random()*100000);
        }
    }

    // ── Shared metadata registry (earlier BPPs write, later BPPs read) ─
    static class BppRegistry {
        final Map<String, String>  namespaces   = new ConcurrentHashMap<>();
        final Map<String, Integer> rateLimits   = new ConcurrentHashMap<>();
        final Map<String, AtomicLong> callCounts = new ConcurrentHashMap<>();
    }

    // ── BPP-1: read annotations and populate shared registry ─────────
    static class AnnotationRegistryBPP implements BPP, Ordered {
        private final BppRegistry reg;
        AnnotationRegistryBPP(BppRegistry r) { this.reg = r; }
        @Override public int getOrder() { return 1; }
        @Override public Object after(Object bean, String name) {
            Monitored m = bean.getClass().getAnnotation(Monitored.class);
            RateLimit rl = bean.getClass().getAnnotation(RateLimit.class);
            if (m  != null) { reg.namespaces.put(name, m.namespace());  System.out.printf("[BPP-Registry  order=1 ] %s → namespace=%s%n", name, m.namespace()); }
            if (rl != null) { reg.rateLimits.put(name, rl.rpm());       System.out.printf("[BPP-Registry  order=1 ] %s → rateLimit=%d rpm%n", name, rl.rpm()); }
            return bean; // pass-through
        }
    }

    // ── BPP-2: wrap with metrics (reads namespace from registry) ──────
    static class MetricsBPP implements BPP, Ordered {
        private final BppRegistry reg;
        MetricsBPP(BppRegistry r) { this.reg = r; }
        @Override public int getOrder() { return 10; }
        @Override public Object after(Object bean, String name) {
            if (!reg.namespaces.containsKey(name)) return bean;
            String ns = reg.namespaces.get(name);
            System.out.printf("[BPP-Metrics   order=10] wrapping '%s' in MetricsProxy (ns=%s)%n", name, ns);
            reg.callCounts.put(name, new AtomicLong());
            AtomicLong counter = reg.callCounts.get(name);
            PaymentGateway original = (PaymentGateway) bean;
            return (PaymentGateway) (amount, card) -> {
                long n = counter.incrementAndGet();
                System.out.printf("    [Metrics.%s] call#%d charge(%s)%n", ns, n, amount);
                return original.charge(amount, card);
            };
        }
    }

    // ── BPP-3: wrap with rate limiter (reads rpm from registry) ───────
    static class RateLimitBPP implements BPP {
        private final BppRegistry reg;
        RateLimitBPP(BppRegistry r) { this.reg = r; }
        @Override public Object after(Object bean, String name) {
            if (!reg.rateLimits.containsKey(name)) return bean;
            int rpm = reg.rateLimits.get(name);
            System.out.printf("[BPP-RateLimit unordered] wrapping '%s' in RateLimitProxy (max=%d/min)%n", name, rpm);
            AtomicInteger calls = new AtomicInteger();
            long windowStart = System.currentTimeMillis();
            PaymentGateway original = (PaymentGateway) bean;
            return (PaymentGateway) (amount, card) -> {
                long now = System.currentTimeMillis();
                // simple per-minute window (reset every 60s)
                if (now - windowStart > 60_000) calls.set(0);
                int n = calls.incrementAndGet();
                if (n > rpm) throw new IllegalStateException("Rate limit exceeded: " + n + " > " + rpm + "/min");
                System.out.printf("    [RateLimit] call %d/%d per min%n", n, rpm);
                return original.charge(amount, card);
            };
        }
    }

    @SuppressWarnings("unchecked")
    static <T> T createBean(T bean, String name, List<BPP> bpps) {
        Object result = bean;
        for (BPP bpp : bpps) result = bpp.after(result, name);
        return (T) result;
    }

    public static void main(String[] args) {
        BppRegistry reg = new BppRegistry();
        List<BPP> bpps = List.of(
            new AnnotationRegistryBPP(reg),  // order 1 — reads annotations, fills registry
            new MetricsBPP(reg),             // order 10 — reads namespace from registry
            new RateLimitBPP(reg)            // unordered — reads rateLimit from registry, outermost
        );

        System.out.println("=== Container: creating StripeGateway ===");
        PaymentGateway gw = createBean(new StripeGateway(), "stripeGateway", bpps);

        System.out.println("\n[REGISTRY] namespaces=" + reg.namespaces + " rateLimits=" + reg.rateLimits);
        System.out.println("\n=== Runtime: RateLimitProxy → MetricsProxy → StripeGateway ===");
        System.out.println(gw.charge("$99.99", "4242424242424242"));
        System.out.println(gw.charge("$19.99", "5555555555554444"));
        System.out.println(gw.charge("$49.00", "4111111111111111"));

        System.out.println("\n[METRICS] " + reg.callCounts.get("stripeGateway").get() + " calls tracked");
    }
}
```

How to run: `java MultiBPPDemo3.java`

`AnnotationRegistryBPP` (order=1) runs first and populates the shared `BppRegistry` with the bean's `@Monitored` namespace and `@RateLimit` rpm. `MetricsBPP` (order=10) reads the namespace from the registry (works because BPP-1 already wrote it) and wraps in a metrics proxy. `RateLimitBPP` (unordered, last) reads the rate limit and wraps outermost. Runtime call chain: `RateLimitProxy` → `MetricsProxy` → `StripeGateway`.

## 6. Walkthrough

**Level 3 processing → runtime trace:**

```
Container startup — BPPs applied in order:

  AnnotationRegistryBPP.after(new StripeGateway(), "stripeGateway")    order=1
    → reads @Monitored(namespace="payments") → reg.namespaces={stripeGateway:payments}
    → reads @RateLimit(rpm=100)              → reg.rateLimits={stripeGateway:100}
    → return original StripeGateway (no wrapping)

  MetricsBPP.after(StripeGateway, "stripeGateway")                     order=10
    → reg.namespaces.containsKey("stripeGateway") = true → ns="payments"
    → return MetricsProxy(StripeGateway)  ← wraps original

  RateLimitBPP.after(MetricsProxy, "stripeGateway")                    unordered
    → reg.rateLimits.containsKey("stripeGateway") = true → rpm=100
    → return RateLimitProxy(MetricsProxy) ← wraps metrics proxy

gw = RateLimitProxy  (outermost — added last)

gw.charge("$99.99", "...4242"):
  RateLimitProxy: call 1/100 per min → OK
  MetricsProxy:   Metrics.payments call#1 charge($99.99)
  StripeGateway:  charge → txn_XXXXX

[METRICS] 3 calls tracked ✓
```

## 7. Gotchas & takeaways

> **BPP ordering is about PROCESSING order, not runtime invocation order — they are reversed.** Lower-order BPPs produce inner proxies; higher-order BPPs produce outer proxies. If BPP-A (order=1) must fire BEFORE BPP-B (order=10) at runtime (on each method call), then BPP-B must run second in processing (i.e., BPP-B has order=10 and BPP-A has order=1). This is the "last wrapper = outermost caller" rule.

> **A BPP that needs to read class-level annotations must run BEFORE any proxying BPP.** Once a proxy replaces the original bean, `bean.getClass()` returns the proxy class, not the original — and `proxy.getClass().getAnnotation(MyAnnotation.class)` returns `null`. Use a lower `getOrder()` or Spring's `AopProxyUtils.ultimateTargetClass(bean)` to unwrap the target.

- Implement `PriorityOrdered` only for Spring infrastructure-level BPPs. For application BPPs, use `Ordered` with values like 10, 50, 100 to give yourself room to insert more BPPs later.
- If two BPPs have the same `getOrder()` value, their relative order is undefined — use distinct values.
- `BeanPostProcessor.Ordered.HIGHEST_PRECEDENCE` (`Integer.MIN_VALUE`) runs before `PriorityOrdered` beans with lower priorities — use it only if you truly need to run before Spring's core infrastructure.
- In Spring Boot, auto-configured BPPs (from `@ConditionalOn*` auto-configurations) are typically in the `Ordered` tier. Set your application BPPs to `order > 0` to ensure they run after Spring's auto-configured infrastructure processors.
