---
card: spring-framework
gi: 31
slug: naming-beans
title: Naming beans
---

## 1. What it is

Every bean in the Spring container has at least one **name** — a string identifier used to retrieve the bean from the context and to resolve dependencies by name.

Spring assigns names through several mechanisms:

| Declaration | Default name | Custom name |
|---|---|---|
| `@Component` on `OrderService` | `"orderService"` (camelCase class name) | `@Component("orders")` |
| `@Bean` method `public OrderService orderService()` | `"orderService"` (method name) | `@Bean("orders")` |
| XML `<bean class="OrderService">` | generated ID like `"#0"` | `id="orders"` |

A bean can have multiple names — one primary name plus zero or more **aliases**.

In one sentence: **A bean name is the string key the container uses to store and retrieve a bean definition; Spring derives it automatically from the class or method name unless you provide one explicitly.**

## 2. Why & when

Names matter in three situations:

1. **Manual lookup.** `ctx.getBean("orderService")` retrieves by name — wrong name → `NoSuchBeanDefinitionException`.
2. **By-name injection.** When two beans of the same type exist, Spring falls back to matching the injection point's variable name against bean names: `OrderService primaryOrderService` injects the bean named `"primaryOrderService"`.
3. **Aliases in configuration.** A single bean can be referenced by many names — useful when different teams or modules use different naming conventions for the same bean.

For everyday code, the default naming rules are sufficient. Override names when:
- The class name is ambiguous.
- You need a shorter, more expressive name.
- You are integrating with a legacy system that expects a specific bean name.

## 3. Core concept

Spring's default naming algorithm:

```
@Component on class → lowerCamelCase of class name
  OrderService     → "orderService"
  HTMLParser       → "HTMLParser"  (leading acronym preserved)
  URLValidator     → "URLValidator"

@Bean method → method name (exact)
  public OrderService myOrderService() → "myOrderService"

XML <bean id="..."> → id attribute (exact)
XML <bean> (no id) → fully-qualified classname + "#0"
```

All names go into the same flat namespace per `ApplicationContext`. Names must be unique; duplicate names (overriding) require explicit opt-in since Spring 5.3.

You can retrieve a bean by any of its aliases:
```java
ctx.getBean("orders")   // primary name
ctx.getBean("order-svc") // alias
```

Both return the same singleton instance.

## 4. Diagram

<svg viewBox="0 0 680 210" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Bean naming: @Component, @Bean, XML each produce a name stored in registry; aliases map to same instance">
  <defs>
    <marker id="a31" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>

  <!-- Sources -->
  <rect x="10" y="15" width="180" height="40" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="100" y="40" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">@Component class OrderService → "orderService"</text>

  <rect x="10" y="68" width="180" height="40" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="100" y="88" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">@Bean myOrderSvc() → "myOrderSvc"</text>

  <rect x="10" y="121" width="180" height="40" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="100" y="141" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">&lt;bean id="orders"/&gt; → "orders"</text>

  <!-- Name registry -->
  <rect x="262" y="50" width="170" height="96" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="347" y="74" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">Bean Name Registry</text>
  <text x="347" y="92" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">"orderService"  → BeanDef</text>
  <text x="347" y="108" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">"myOrderSvc"    → BeanDef</text>
  <text x="347" y="124" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">"orders"        → BeanDef</text>

  <line x1="190" y1="35"  x2="260" y2="80"  stroke="#8b949e" stroke-width="1.5" marker-end="url(#a31)"/>
  <line x1="190" y1="88"  x2="260" y2="97"  stroke="#8b949e" stroke-width="1.5" marker-end="url(#a31)"/>
  <line x1="190" y1="141" x2="260" y2="115" stroke="#8b949e" stroke-width="1.5" marker-end="url(#a31)"/>

  <!-- Alias -->
  <rect x="490" y="50" width="180" height="60" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="580" y="72" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">Alias map</text>
  <text x="580" y="88" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">"order-svc" → "orders"</text>
  <text x="580" y="104" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">"billing-orders" → "orders"</text>

  <line x1="432" y1="97" x2="488" y2="80" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a31)"/>

  <text x="340" y="180" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">All names share one flat namespace per context — must be unique (overriding requires opt-in)</text>
</svg>

Each declaration produces a name in the registry. Aliases point back to the primary name. All names and aliases must be unique.

## 5. Runnable example

Scenario: a product catalog with a `PricingService`. We show default naming, custom naming, and collision handling across three levels.

### Level 1 — Basic

Default names: how the container derives them from class and method names.

```java
// NamingDemo.java — run with: java NamingDemo.java
import java.util.*;

public class NamingDemo {

    record Product(int id, String name, double price) {}

    // Default name from class: "pricingService"
    static class PricingService {
        double price(Product p, int qty) { return p.price() * qty; }
    }

    // Default name from class: "catalogRepository"
    static class CatalogRepository {
        private final List<Product> products = new ArrayList<>(List.of(
            new Product(1, "Laptop", 1299.00),
            new Product(2, "Monitor", 449.00)
        ));
        List<Product> findAll() { return Collections.unmodifiableList(products); }
        Optional<Product> findById(int id) { return products.stream().filter(p -> p.id() == id).findFirst(); }
    }

    // Default name from class: "catalogService"
    static class CatalogService {
        private final PricingService pricing;
        private final CatalogRepository repo;
        CatalogService(PricingService pricing, CatalogRepository repo) {
            this.pricing = pricing; this.repo = repo;
        }
        void quote(int productId, int qty) {
            repo.findById(productId).ifPresent(p ->
                System.out.printf("  Quote: %s x%d = $%.2f%n", p.name(), qty, pricing.price(p, qty)));
        }
    }

    // Container with name-based lookup
    static class NamedContainer {
        private final Map<String, Object> beans = new LinkedHashMap<>();

        void register(String name, Object bean) {
            beans.put(name, bean);
            System.out.println("  [CTX] Bean '" + name + "' → " + bean.getClass().getSimpleName());
        }

        // Default name: lowerCamelCase of class name
        void registerDefault(Object bean) {
            String raw = bean.getClass().getSimpleName();
            String name = Character.toLowerCase(raw.charAt(0)) + raw.substring(1);
            register(name, bean);
        }

        @SuppressWarnings("unchecked")
        <T> T getBean(String name) {
            Object b = beans.get(name);
            if (b == null) throw new RuntimeException("NoSuchBeanDefinitionException: '" + name + "'");
            return (T) b;
        }
    }

    public static void main(String[] args) {
        NamedContainer ctx = new NamedContainer();

        System.out.println("=== Default naming (lowerCamelCase of class) ===");
        PricingService    pricing = new PricingService();
        CatalogRepository repo    = new CatalogRepository();
        ctx.registerDefault(pricing);
        ctx.registerDefault(repo);
        ctx.registerDefault(new CatalogService(pricing, repo));

        System.out.println("\n=== Lookup by name ===");
        ctx.getBean(CatalogService.class.getSimpleName().substring(0, 1).toLowerCase()
            + CatalogService.class.getSimpleName().substring(1));
        CatalogService svc = ctx.getBean("catalogService");
        svc.quote(1, 3);
        svc.quote(2, 2);

        System.out.println("\n=== Wrong name throws ===");
        try { ctx.getBean("CatalogService"); }  // capital C — wrong!
        catch (RuntimeException e) { System.out.println("  " + e.getMessage()); }
    }
}
```

How to run: `java NamingDemo.java`

Default name is `lowerCamelCase` of the class name. `"CatalogService"` (capital C) throws — Spring names are case-sensitive. This catches a very common beginner bug: `getBean("CatalogService")` fails while `getBean("catalogService")` succeeds.

### Level 2 — Intermediate

Custom names via `@Component("orders")` and `@Bean("pricing")` — override the default.

```java
// NamingDemo2.java — run with: java NamingDemo2.java
import java.lang.annotation.*;
import java.util.*;

public class NamingDemo2 {

    @Retention(RetentionPolicy.RUNTIME) @interface Component { String value() default ""; }
    @Retention(RetentionPolicy.RUNTIME) @interface Bean      { String[] value() default {}; }

    record Product(int id, String name, double price) {}

    @Component("catalog")          // custom name — not "catalogRepository"
    static class CatalogRepository {
        private final List<Product> store = new ArrayList<>(List.of(
            new Product(1, "Laptop", 1299.00),
            new Product(2, "Monitor", 449.00)
        ));
        List<Product> findAll() { return Collections.unmodifiableList(store); }
    }

    @Component("pricing")          // custom name
    static class PricingService {
        double apply(Product p, int qty, double discount) {
            return p.price() * qty * (1 - discount);
        }
    }

    // No custom name → defaults to "catalogFacade"
    static class CatalogFacade {
        private final CatalogRepository repo;
        private final PricingService    pricing;
        CatalogFacade(CatalogRepository r, PricingService p) { repo = r; pricing = p; }
        void showPrices(double discount) {
            System.out.printf("  === Catalog (%.0f%% off) ===%n", discount * 100);
            repo.findAll().forEach(p ->
                System.out.printf("  %-10s $%.2f%n", p.name(), pricing.apply(p, 1, discount)));
        }
    }

    static class AnnotationCtx {
        private final Map<String, Object> beans = new LinkedHashMap<>();

        void register(String name, Object bean) {
            beans.put(name, bean);
            System.out.println("  [CTX] '" + name + "' → " + bean.getClass().getSimpleName());
        }

        void scanClass(Object bean) {
            Component ann = bean.getClass().getAnnotation(Component.class);
            String name = (ann != null && !ann.value().isEmpty()) ? ann.value()
                : defaultName(bean.getClass().getSimpleName());
            register(name, bean);
        }

        String defaultName(String simple) {
            return Character.toLowerCase(simple.charAt(0)) + simple.substring(1);
        }

        @SuppressWarnings("unchecked")
        <T> T getBean(String name) { return (T) beans.get(name); }
    }

    public static void main(String[] args) {
        AnnotationCtx ctx = new AnnotationCtx();

        System.out.println("=== Register with custom and default names ===");
        CatalogRepository repo    = new CatalogRepository();
        PricingService    pricing = new PricingService();
        ctx.scanClass(repo);      // → "catalog" (custom)
        ctx.scanClass(pricing);   // → "pricing" (custom)
        ctx.register("catalogFacade", new CatalogFacade(repo, pricing));  // default

        System.out.println("\n=== Lookup by custom names ===");
        CatalogFacade facade = ctx.getBean("catalogFacade");
        facade.showPrices(0.0);
        System.out.println();
        facade.showPrices(0.20);

        System.out.println("\n=== Custom name works, class name does NOT ===");
        System.out.println("  getBean(\"catalog\")   → " + ctx.getBean("catalog").getClass().getSimpleName());
        try { ctx.getBean("catalogRepository"); }
        catch (Exception e) { System.out.println("  getBean(\"catalogRepository\") → null (wrong name)"); }
    }
}
```

How to run: `java NamingDemo2.java`

`@Component("catalog")` registers the bean as `"catalog"`, not `"catalogRepository"`. Trying `getBean("catalogRepository")` fails. This is a common pitfall when renaming bean names via annotations — dependent code that looked up by the old name breaks.

### Level 3 — Advanced

Name collision detection and bean name override strategy — what happens when two definitions claim the same name.

```java
// NamingDemo3.java — run with: java NamingDemo3.java
import java.util.*;
import java.util.function.*;

public class NamingDemo3 {

    record Product(int id, String name, double price) {}

    interface PricingStrategy { double compute(Product p, int qty); }

    // Two implementations — can't both be "pricingStrategy" without conflict
    static class RetailPricing implements PricingStrategy {
        public double compute(Product p, int qty) { return p.price() * qty; }
        public String toString() { return "RetailPricing"; }
    }

    static class WholesalePricing implements PricingStrategy {
        public double compute(Product p, int qty) { return p.price() * qty * 0.85; }
        public String toString() { return "WholesalePricing"; }
    }

    static class CatalogService {
        private final PricingStrategy strategy;
        CatalogService(PricingStrategy strategy) { this.strategy = strategy; }
        void quote(Product p, int qty) {
            System.out.printf("  [%s] %s x%d = $%.2f%n",
                strategy, p.name(), qty, strategy.compute(p, qty));
        }
    }

    static class OverrideAwareCtx {
        private final Map<String, Object>    beans         = new LinkedHashMap<>();
        private final boolean                allowOverride;

        OverrideAwareCtx(boolean allowOverride) { this.allowOverride = allowOverride; }

        void register(String name, Supplier<Object> factory) {
            if (beans.containsKey(name)) {
                if (!allowOverride) throw new RuntimeException(
                    "BeanDefinitionOverrideException: '" + name + "' is already defined");
                System.out.println("  [OVERRIDE] Replacing '" + name + "'");
            }
            beans.put(name, factory.get());
            System.out.println("  [CTX] '" + name + "' → " + beans.get(name));
        }

        @SuppressWarnings("unchecked")
        <T> T getBean(String name) { return (T) beans.get(name); }
    }

    public static void main(String[] args) {
        Product laptop  = new Product(1, "Laptop",  1299.00);
        Product monitor = new Product(2, "Monitor",  449.00);

        System.out.println("=== Scenario A: Override DISABLED (Spring 5.3+ default) ===");
        OverrideAwareCtx strict = new OverrideAwareCtx(false);
        strict.register("pricingStrategy", RetailPricing::new);
        try {
            strict.register("pricingStrategy", WholesalePricing::new);  // CONFLICT
        } catch (RuntimeException e) {
            System.out.println("  CAUGHT: " + e.getMessage());
        }
        System.out.println("  Active strategy: " + strict.getBean("pricingStrategy"));

        System.out.println("\n=== Scenario B: Override ENABLED (legacy behaviour) ===");
        OverrideAwareCtx override = new OverrideAwareCtx(true);
        override.register("pricingStrategy", RetailPricing::new);
        // Production config overrides with wholesale strategy
        override.register("pricingStrategy", WholesalePricing::new);

        PricingStrategy strategy = override.getBean("pricingStrategy");
        CatalogService svc = new CatalogService(strategy);
        System.out.println("\n  === Quotes (wholesale pricing) ===");
        svc.quote(laptop,  3);
        svc.quote(monitor, 5);

        System.out.println("\n=== Scenario C: Unique names — no conflict ===");
        OverrideAwareCtx dual = new OverrideAwareCtx(false);
        dual.register("retailPricing",    RetailPricing::new);
        dual.register("wholesalePricing", WholesalePricing::new);
        System.out.println("  Both beans exist:");
        System.out.println("  retailPricing    → " + dual.getBean("retailPricing"));
        System.out.println("  wholesalePricing → " + dual.getBean("wholesalePricing"));
    }
}
```

How to run: `java NamingDemo3.java`

Scenario A: duplicate name throws immediately — the default since Spring 5.3. Scenario B: override enabled — second registration wins. Scenario C: unique names for both strategies — the clean design that avoids conflict. Spring Boot sets `spring.main.allow-bean-definition-overriding=false` by default.

## 6. Walkthrough

**Level 3 — bean name collision scenarios:**

**Scenario A — strict mode:**
```
register("pricingStrategy", RetailPricing::new)
  → beans has no "pricingStrategy" → add → beans["pricingStrategy"] = RetailPricing

register("pricingStrategy", WholesalePricing::new)
  → beans already has "pricingStrategy"
  → allowOverride == false
  → throw RuntimeException("BeanDefinitionOverrideException: 'pricingStrategy'...")

getBean("pricingStrategy") → RetailPricing (still there, override was rejected)
```

**Scenario B — override mode:**
```
register("pricingStrategy", RetailPricing::new)   → beans = {pricingStrategy: Retail}
register("pricingStrategy", WholesalePricing::new) → [OVERRIDE] → beans = {pricingStrategy: Wholesale}

CatalogService.quote(laptop, 3)
  → strategy.compute(Product(Laptop, 1299.00), 3)
      → 1299.00 * 3 * 0.85 = 3312.45
  → "[WholesalePricing] Laptop x3 = $3312.45"
```

**Data flow from name to bean:**

| Lookup | Registry check | Result |
|---|---|---|
| `getBean("pricingStrategy")` | `beans["pricingStrategy"]` → `WholesalePricing` | singleton returned |
| `getBean("CatalogService")` | `beans["CatalogService"]` → null | exception |
| `getBean("catalogService")` | `beans["catalogService"]` → if registered | singleton returned |

## 7. Gotchas & takeaways

> **Bean names are case-sensitive.** `"orderService"` and `"OrderService"` are different names. The container's default naming uses `lowerCamelCase` — always use that form when looking up by name.

> **`@Bean` method name IS the primary bean name.** `public OrderService myOrderService()` registers the bean as `"myOrderService"`, not `"OrderService"`. If you inject by type AND there is only one bean of that type, the name does not matter. It matters when you inject by name (via `@Qualifier`) or call `getBean(String)`.

- Prefer type-based injection (`@Autowired`) over name-based (`getBean(String)`) — names are fragile and do not survive refactoring.
- `@Qualifier("pricing")` on an injection point selects the bean named `"pricing"` when multiple beans of the same type exist.
- In Spring Boot, `spring.main.allow-bean-definition-overriding=true` re-enables override behaviour — use with care and document why the override is intentional.
- `ctx.getBeanDefinitionNames()` returns all registered names — useful for debugging which beans are actually in the context.
- Multi-module apps: prefix bean names to avoid collision (`billing_orderService` vs `shipping_orderService`) or use `@Qualifier` to disambiguate.
