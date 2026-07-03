---
card: spring-framework
gi: 100
slug: resource-jsr-250-injection
title: "@Resource (JSR-250) injection"
---

## 1. What it is

`@Resource` is a JSR-250 standard annotation (`javax.annotation.Resource` or `jakarta.annotation.Resource`) that injects a bean **by name first, type second**. Unlike `@Autowired` (which resolves by type then qualifier), `@Resource` looks for a bean whose name matches the annotated field or method name — or the name you specify with `@Resource(name="...")`.

## 2. Why & when

`@Resource` predates Spring's `@Autowired` and was part of the Java EE / Jakarta EE standard. You'll encounter it in:

- Legacy Spring apps that use JSR-250 for portability across containers (Spring, Java EE).
- JNDI resource injection patterns (connection pools, JMS queues, EJBs).
- Codebases that prefer name-based wiring over type-based wiring by convention.

In greenfield Spring apps, prefer `@Autowired` + `@Qualifier` (or constructor injection). Use `@Resource` when you specifically need name-first resolution or when JSR-250 compatibility is required.

**Name resolution order for `@Resource`:**
1. Use the `name` attribute if specified: `@Resource(name="myBean")`.
2. Otherwise use the field name or setter property name as the bean name.
3. If name lookup fails, fall back to type matching (like `@Autowired`).

## 3. Core concept

`@Resource` is processed by `CommonAnnotationBeanPostProcessor`, which Spring registers automatically. It supports:

- **Field injection** — `@Resource private DataSource ds;` → looks for bean named `ds`.
- **Setter injection** — `@Resource public void setDs(DataSource ds)` → looks for bean named `ds`.
- **Explicit name** — `@Resource(name="primaryDataSource")` → looks for bean named `primaryDataSource`.

It does **not** support constructor injection (that's `@Autowired` only).

## 4. Diagram

<svg viewBox="0 0 700 210" xmlns="http://www.w3.org/2000/svg">
  <!-- @Autowired path -->
  <rect x="10" y="40" width="175" height="54" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="97" y="63" fill="#8b949e" font-size="12" text-anchor="middle" font-family="sans-serif">@Autowired</text>
  <text x="97" y="78" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">type → qualifier → name</text>

  <!-- @Resource path -->
  <rect x="10" y="120" width="175" height="54" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="97" y="143" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">@Resource</text>
  <text x="97" y="158" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">name → type fallback</text>

  <!-- Resolution -->
  <rect x="285" y="80" width="165" height="54" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="367" y="103" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">Bean Registry</text>
  <text x="367" y="118" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">name match first</text>

  <!-- Result -->
  <rect x="540" y="80" width="145" height="54" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="612" y="103" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">Inject bean ✓</text>
  <text x="612" y="118" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">by name or type</text>

  <line x1="187" y1="147" x2="282" y2="110" stroke="#6db33f" stroke-width="2" marker-end="url(#a100)"/>
  <line x1="452" y1="107" x2="537" y2="107" stroke="#6db33f" stroke-width="2" marker-end="url(#a100)"/>
  <defs>
    <marker id="a100" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>
  <text x="350" y="190" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">@Resource resolves by name first; @Autowired resolves by type first</text>
</svg>

`@Resource` inverts the `@Autowired` resolution order: name first, type fallback.

## 5. Runnable example

### Level 1 — Basic

Inject a bean by its default name (field name matches bean name).

```java
// ResourceBasic.java
import jakarta.annotation.Resource;
import org.springframework.context.annotation.*;
import org.springframework.stereotype.*;

@Component("mailSender")   // bean name is "mailSender"
class MailSender {
    public void send(String msg) { System.out.println("[MAIL] " + msg); }
}

@Service
class AlertService {
    @Resource   // looks for a bean named "mailSender" — matches the field name
    private MailSender mailSender;

    public void alert(String msg) { mailSender.send(msg); }
}

@Configuration
@ComponentScan
class ResCfg {}

public class ResourceBasic {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(ResCfg.class);
        ctx.getBean(AlertService.class).alert("Server down!");
        ctx.close();
    }
}
```

How to run: `java ResourceBasic.java`

The field is named `mailSender` and the bean is named `mailSender` — `@Resource` matches by name without any qualifier. If you renamed the field to `ms`, injection would fall back to type and find the same bean.

### Level 2 — Intermediate

Disambiguate between two `DataSource` beans using `@Resource(name="...")` — the explicit name bypasses type ambiguity.

```java
// ResourceNamed.java
import jakarta.annotation.Resource;
import org.springframework.context.annotation.*;
import org.springframework.stereotype.*;

interface DataSource { String query(String sql); }

@Component("primaryDataSource")
class PrimaryDataSource implements DataSource {
    public String query(String sql) { return "[PRIMARY] " + sql; }
}

@Component("replicaDataSource")
class ReplicaDataSource implements DataSource {
    public String query(String sql) { return "[REPLICA] " + sql; }
}

@Service
class ReportService {
    @Resource(name = "primaryDataSource")
    private DataSource primary;

    @Resource(name = "replicaDataSource")
    private DataSource replica;

    public void report() {
        System.out.println(primary.query("SELECT * FROM orders"));
        System.out.println(replica.query("SELECT COUNT(*) FROM orders"));
    }
}

@Configuration
@ComponentScan
class NamedCfg {}

public class ResourceNamed {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(NamedCfg.class);
        ctx.getBean(ReportService.class).report();
        ctx.close();
    }
}
```

How to run: `java ResourceNamed.java`

With two `DataSource` implementations, `@Autowired` alone would throw `NoUniqueBeanDefinitionException`. `@Resource(name="...")` sidesteps type resolution entirely — it's a direct name lookup.

### Level 3 — Advanced

Mix `@Resource` with setter injection and show how the name falls back to type when the explicit name is not found.

```java
// ResourceFallback.java
import jakarta.annotation.Resource;
import org.springframework.context.annotation.*;
import org.springframework.stereotype.*;

interface CacheService {
    void put(String k, String v);
    String get(String k);
}

// Bean name is "localCache" by convention (class name, camel-case)
@Component
class LocalCache implements CacheService {
    private final java.util.Map<String,String> store = new java.util.HashMap<>();
    public void put(String k, String v) { store.put(k, v); System.out.println("[CACHE] put " + k); }
    public String get(String k) { return store.getOrDefault(k, null); }
}

@Service
class ProductService {
    private CacheService cache;
    private CacheService secondaryCache;

    // Setter injection — @Resource uses the property name ("cache") as bean name
    @Resource
    public void setCache(CacheService cache) {
        System.out.println("setCache called — resolved by property name 'cache'? No bean named 'cache', falls back to type.");
        this.cache = cache;
    }

    // Explicit name
    @Resource(name = "localCache")
    public void setSecondaryCache(CacheService c) {
        System.out.println("setSecondaryCache called — resolved 'localCache' by name.");
        this.secondaryCache = c;
    }

    public void run() {
        cache.put("p1", "Widget");
        System.out.println("Get p1: " + cache.get("p1"));
        System.out.println("Same bean? " + (cache == secondaryCache));
    }
}

@Configuration
@ComponentScan
class FallbackCfg {}

public class ResourceFallback {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(FallbackCfg.class);
        ctx.getBean(ProductService.class).run();
        ctx.close();
    }
}
```

How to run: `java ResourceFallback.java`

`setCache` property name → bean name `"cache"` → no such bean → falls back to type `CacheService` → `LocalCache`. `setSecondaryCache(name="localCache")` → direct name match. Both resolve to the same singleton. Shows both the name-first path and the type-fallback path in one example.

## 6. Walkthrough

Execution order for the Level 3 example:

1. **Scan** — `LocalCache` and `ProductService` registered. `LocalCache` bean name = `"localCache"` (class name, first letter lower-cased).
2. **`LocalCache` instantiated** — no deps.
3. **`ProductService` instantiated** — `CommonAnnotationBeanPostProcessor` processes `@Resource` annotations.
4. **`setCache` resolver** — property name derived from method `setCache` → `"cache"`. No bean named `"cache"`. Type fallback: find all `CacheService` beans → one: `LocalCache`. Call `setCache(localCache)`.
5. **`setSecondaryCache` resolver** — explicit `name="localCache"`. Bean exists. Call `setSecondaryCache(localCache)`.
6. **`run()` called** — `cache.put("p1", "Widget")`, `cache.get("p1")` → `"Widget"`. `cache == secondaryCache` → `true` (same singleton).

Expected output:
```
setCache called — resolved by property name 'cache'? No bean named 'cache', falls back to type.
setSecondaryCache called — resolved 'localCache' by name.
[CACHE] put p1
Get p1: Widget
Same bean? true
```

## 7. Gotchas & takeaways

> `@Resource` resolves by **name first**. If your field is named `dataSource` and two beans exist of type `DataSource`, Spring won't be confused — it simply looks for a bean named `dataSource`. If that bean exists, it's injected without ambiguity. Only if the name lookup fails does it fall back to type matching (where ambiguity can re-appear).

> `CommonAnnotationBeanPostProcessor` must be registered. It's registered automatically when you use `@Configuration` with annotation processing or `<context:annotation-config/>`. Without it, `@Resource` is silently ignored.

- `@Resource` lives in `jakarta.annotation.Resource` (Spring 6+) or `javax.annotation.Resource` (Spring 5 and earlier).
- Does **not** support constructor injection — use `@Autowired` for that.
- `@Resource` on a field with no `name` attribute uses the **field name** as the bean name.
- `@Resource` on a setter with no `name` attribute uses the **property name** (derived from the method name) as the bean name.
- Prefer `@Autowired` + `@Qualifier` in new Spring-only code; use `@Resource` when JSR-250 portability matters.
