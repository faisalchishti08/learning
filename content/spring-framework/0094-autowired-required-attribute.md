---
card: spring-framework
gi: 94
slug: autowired-required-attribute
title: "@Autowired required attribute"
---

## 1. What it is

`@Autowired` has a `required` attribute (default `true`) that controls whether Spring **fails at startup** if no matching bean is found. Setting `required = false` makes the injection point optional: if the bean is absent, Spring leaves the field as `null` (or skips calling the setter/method) without throwing an exception.

```java
@Autowired(required = false)
private MetricsService metrics; // null if no MetricsService bean exists
```

## 2. Why & when

Not every dependency is mandatory. Common scenarios for `required = false`:

- **Optional integrations** — a metrics or tracing service that may or may not be in the classpath.
- **Feature flags** — a bean that exists only when a certain profile or condition is active.
- **Plugin architecture** — an extension point that's useful when present but the core works without it.

In modern Spring code, the cleaner alternatives are `Optional<T>` injection or `ObjectProvider<T>` (covered next). `required = false` is the direct, older form.

## 3. Core concept

`AutowiredAnnotationBeanPostProcessor` checks `required` during injection:

- `required = true` (default): if no bean matches the type (and qualifier), throw `NoSuchBeanDefinitionException` at startup.
- `required = false`: if no bean matches, skip the injection point silently. The field stays at its default Java value (`null` for objects, `0`/`false` for primitives).

For **constructor** injection, `required` on the constructor annotation covers all parameters. For individual parameters, use `@Autowired` on each parameter combined with `@Nullable` or use `Optional<T>`.

> If the field is a primitive type and `required = false`, Spring can't inject `null`, so it simply skips the setter call — the field retains its initial value.

## 4. Diagram

<svg viewBox="0 0 700 220" xmlns="http://www.w3.org/2000/svg">
  <!-- Required=true path -->
  <rect x="10" y="40" width="160" height="44" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="90" y="63" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">@Autowired</text>
  <text x="90" y="78" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">required=true (default)</text>

  <rect x="10" y="130" width="160" height="44" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="90" y="153" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">@Autowired</text>
  <text x="90" y="168" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">required=false</text>

  <!-- Decision diamond -->
  <polygon points="280,80 350,50 420,80 350,110" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="350" y="77" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">Bean</text>
  <text x="350" y="91" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">exists?</text>

  <!-- Found path -->
  <rect x="500" y="40" width="170" height="44" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="585" y="63" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">Inject bean ✓</text>
  <text x="585" y="78" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">both required values</text>

  <!-- Not found — required=true -->
  <rect x="500" y="120" width="170" height="44" rx="8" fill="#1c2430" stroke="#ff7b72" stroke-width="1.5"/>
  <text x="585" y="143" fill="#ff7b72" font-size="12" text-anchor="middle" font-family="sans-serif">required=true → throw</text>
  <text x="585" y="158" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">NoSuchBeanDefinitionEx</text>

  <!-- Not found — required=false -->
  <rect x="500" y="180" width="170" height="30" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="585" y="199" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">required=false → skip (null)</text>

  <line x1="172" y1="62" x2="278" y2="72" stroke="#e6edf3" stroke-width="1.5" marker-end="url(#a94)"/>
  <line x1="172" y1="152" x2="278" y2="92" stroke="#e6edf3" stroke-width="1.5" marker-end="url(#a94)"/>
  <line x1="422" y1="65" x2="497" y2="62" stroke="#6db33f" stroke-width="1.5" marker-end="url(#b94)"/>
  <line x1="350" y1="111" x2="350" y2="135" stroke="#ff7b72" stroke-width="1.5"/>
  <line x1="350" y1="135" x2="497" y2="140" stroke="#ff7b72" stroke-width="1.5" marker-end="url(#c94)"/>
  <line x1="350" y1="135" x2="497" y2="195" stroke="#8b949e" stroke-width="1.5" marker-end="url(#d94)"/>
  <text x="290" y="148" fill="#ff7b72" font-size="10" font-family="sans-serif">true</text>
  <text x="290" y="175" fill="#8b949e" font-size="10" font-family="sans-serif">false</text>
  <text x="430" y="55" fill="#6db33f" font-size="10" font-family="sans-serif">yes</text>
  <defs>
    <marker id="a94" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#e6edf3"/></marker>
    <marker id="b94" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="c94" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#ff7b72"/></marker>
    <marker id="d94" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

`required = true` throws on missing beans; `required = false` silently skips injection.

## 5. Runnable example

### Level 1 — Basic

A service with an optional metrics dependency using `required = false`.

```java
// RequiredAttrBasic.java
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.*;
import org.springframework.stereotype.*;

// Not registered as a bean — intentionally absent
class MetricsService {
    public void record(String event) { System.out.println("[METRICS] " + event); }
}

@Service
class OrderService {
    @Autowired(required = false)
    private MetricsService metrics; // will be null — MetricsService is not in context

    public void placeOrder(String item) {
        System.out.println("Order placed: " + item);
        if (metrics != null) metrics.record("order.placed");
        else System.out.println("(metrics not available)");
    }
}

@Configuration
@ComponentScan
class ReqCfg {}

public class RequiredAttrBasic {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(ReqCfg.class);
        ctx.getBean(OrderService.class).placeOrder("Widget");
        ctx.close();
    }
}
```

How to run: `java RequiredAttrBasic.java`

`MetricsService` is not registered, so `metrics` stays `null`. The null guard in `placeOrder` prevents `NullPointerException`. Without `required = false` this would throw at startup.

### Level 2 — Intermediate

Toggle the optional bean via a `@Profile` to show the difference between "bean present" and "bean absent" runs.

```java
// RequiredAttrProfile.java
import org.springframework.beans.factory.annotation.*;
import org.springframework.context.annotation.*;
import org.springframework.stereotype.*;

interface NotificationService {
    void notify(String msg);
}

@Service
@Profile("email")   // only active when profile "email" is set
class EmailNotification implements NotificationService {
    public void notify(String msg) { System.out.println("[EMAIL] " + msg); }
}

@Service
class AlertService {
    @Autowired(required = false)
    private NotificationService notifier;

    public void alert(String msg) {
        System.out.println("Alert: " + msg);
        if (notifier != null) notifier.notify(msg);
        else System.out.println("(no notifier configured — silent mode)");
    }
}

@Configuration
@ComponentScan
class ProfileCfg {}

public class RequiredAttrProfile {
    public static void main(String[] args) {
        // Run without profile — notifier absent
        System.out.println("=== No profile ===");
        var ctx1 = new AnnotationConfigApplicationContext();
        ctx1.register(ProfileCfg.class);
        ctx1.refresh();
        ctx1.getBean(AlertService.class).alert("Disk 90% full");
        ctx1.close();

        // Run with "email" profile — notifier present
        System.out.println("\n=== email profile ===");
        var ctx2 = new AnnotationConfigApplicationContext();
        ctx2.getEnvironment().setActiveProfiles("email");
        ctx2.register(ProfileCfg.class);
        ctx2.refresh();
        ctx2.getBean(AlertService.class).alert("Disk 90% full");
        ctx2.close();
    }
}
```

How to run: `java RequiredAttrProfile.java`

First context: no profile active → `EmailNotification` not registered → `notifier = null` → silent mode. Second context: `email` profile active → `EmailNotification` registered → `notifier` injected → email notification fires.

### Level 3 — Advanced

A production-grade service with multiple optional integrations, defensive null-handling, and a `hasCapability` check method to let callers discover available features at runtime.

```java
// RequiredAttrAdvanced.java
import org.springframework.beans.factory.annotation.*;
import org.springframework.context.annotation.*;
import org.springframework.stereotype.*;
import java.util.ArrayList;
import java.util.List;

interface CacheService { void put(String k, Object v); Object get(String k); }
interface TracingService { void startSpan(String name); void endSpan(); }
interface AuditService  { void audit(String action, String user); }

// Only cache is registered — tracing and audit are absent
@Component
class LocalCache implements CacheService {
    private final java.util.Map<String, Object> store = new java.util.HashMap<>();
    public void put(String k, Object v) { store.put(k, v); System.out.println("[CACHE] put " + k); }
    public Object get(String k) { System.out.println("[CACHE] get " + k); return store.get(k); }
}

@Service
class ProductCatalogService {
    @Autowired(required = false) private CacheService   cache;
    @Autowired(required = false) private TracingService tracing;
    @Autowired(required = false) private AuditService   audit;

    public List<String> capabilities() {
        var caps = new ArrayList<String>();
        if (cache   != null) caps.add("CACHE");
        if (tracing != null) caps.add("TRACING");
        if (audit   != null) caps.add("AUDIT");
        return caps;
    }

    public String getProduct(String id, String user) {
        if (tracing != null) tracing.startSpan("getProduct");
        if (cache != null) {
            Object cached = cache.get(id);
            if (cached != null) {
                if (tracing != null) tracing.endSpan();
                return (String) cached;
            }
        }
        String product = "Product[" + id + "]";   // simulate DB fetch
        System.out.println("DB fetch: " + product);
        if (cache  != null) cache.put(id, product);
        if (audit  != null) audit.audit("READ", user);
        if (tracing!= null) tracing.endSpan();
        return product;
    }
}

@Configuration
@ComponentScan
class AdvCfg {}

public class RequiredAttrAdvanced {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(AdvCfg.class);
        var svc = ctx.getBean(ProductCatalogService.class);
        System.out.println("Capabilities: " + svc.capabilities());
        System.out.println(svc.getProduct("P-001", "alice"));  // DB fetch + cache put
        System.out.println(svc.getProduct("P-001", "bob"));    // cache hit
        ctx.close();
    }
}
```

How to run: `java RequiredAttrAdvanced.java`

Only `CacheService` is in the context; `TracingService` and `AuditService` are absent. The `capabilities()` method dynamically reports what's available. Null guards make the code safe regardless of which optional services are present.

## 6. Walkthrough

Execution order for the Level 3 example:

1. **Context starts, component scan runs** — finds `LocalCache` and `ProductCatalogService`.
2. **`LocalCache` instantiated** — no deps, straightforward.
3. **`ProductCatalogService` instantiated** — `AutowiredAnnotationBeanPostProcessor` inspects its three `@Autowired(required = false)` fields.
4. **`cache` resolution** — Spring finds `LocalCache` implements `CacheService`. Injects it. `cache != null`.
5. **`tracing` resolution** — no bean implements `TracingService`. Because `required = false`, injection is skipped. `tracing = null`.
6. **`audit` resolution** — no bean implements `AuditService`. Skipped. `audit = null`.
7. **`capabilities()` called** — returns `[CACHE]` only.
8. **First `getProduct("P-001", "alice")`** — `tracing` check skipped (null). `cache.get("P-001")` → `null` (empty cache). DB fetch runs. `cache.put("P-001", "Product[P-001]")`. Audit skipped.
9. **Second `getProduct("P-001", "bob")`** — `cache.get("P-001")` → `"Product[P-001]"`. Returns immediately without DB fetch.

Expected output:
```
Capabilities: [CACHE]
[CACHE] get P-001
DB fetch: Product[P-001]
[CACHE] put P-001
[CACHE] get P-001
Product[P-001]
```

## 7. Gotchas & takeaways

> With `required = false`, the injected field **stays `null`** if the bean is absent. You must null-check before every use, or you'll get a `NullPointerException` at runtime — which is exactly the kind of silent failure `@Required` was designed to prevent. Use `Optional<T>` or `ObjectProvider<T>` instead for a cleaner API.

> `@Autowired(required = false)` on a **constructor** means "if all constructor parameters can be resolved, call this constructor; otherwise skip". For single-parameter-optional scenarios, use `Optional<T>` as the parameter type instead.

- `required = false` is the oldest optional-injection form; prefer `Optional<T>` field injection or `ObjectProvider<T>` in modern code.
- A bean that's present in some environments and absent in others is best controlled with `@ConditionalOnBean`, `@Profile`, or `@Conditional` — not with null-guard boilerplate everywhere.
- For primitive types with `required = false`, Spring skips the setter call — the field keeps its declared initialiser value.
- If you use `@Autowired(required = false)` on a field, document why with a comment so the null-check logic is understandable months later.
