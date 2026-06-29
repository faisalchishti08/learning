---
card: spring-framework
gi: 22
slug: classpathxmlapplicationcontext
title: ClassPathXmlApplicationContext
---

## 1. What it is

`ClassPathXmlApplicationContext` is the `ApplicationContext` implementation that loads bean definitions from one or more XML files on the **classpath** — the same search path Java uses to find `.class` files.

You pass it one or more resource paths:

```java
ApplicationContext ctx =
    new ClassPathXmlApplicationContext("applicationContext.xml");
// or multiple files merged into one context:
ApplicationContext ctx2 =
    new ClassPathXmlApplicationContext("app-beans.xml", "data-source.xml");
```

The classpath prefix is implicit. You can make it explicit with `classpath:applicationContext.xml` or use a subdirectory: `"config/beans.xml"`.

In one sentence: **`ClassPathXmlApplicationContext` bootstraps a full Spring `ApplicationContext` by reading XML bean definitions from classpath resources — the classic pre-annotations way to start a Spring app.**

## 2. Why & when

`ClassPathXmlApplicationContext` was the standard Spring container bootstrap from Spring 1.x through Spring 3.x. You encounter it today in:

- **Legacy applications** that predate annotation config.
- **Integration tests** that need to load a specific XML configuration subset.
- **Tutorials and documentation** that demonstrate Spring's earliest configuration model.

For new applications, prefer `AnnotationConfigApplicationContext` (Java config) or let Spring Boot handle bootstrap. Use `ClassPathXmlApplicationContext` when:
- You are maintaining an existing XML-configured app.
- A third-party library ships a Spring XML config file you need to import.
- You want to demonstrate or learn the XML configuration model.

## 3. Core concept

`ClassPathXmlApplicationContext` extends `AbstractXmlApplicationContext` which extends `AbstractRefreshableApplicationContext` which extends `AbstractApplicationContext`. The key steps during construction:

```
new ClassPathXmlApplicationContext("beans.xml")
  1. Set resource paths (["classpath:beans.xml"])
  2. Call refresh()
     a. prepareRefresh()          — clear stale state
     b. obtainFreshBeanFactory()  — read XML → build BeanDefinitions
     c. prepareBeanFactory()      — add standard post-processors
     d. postProcessBeanFactory()  — sub-class hook
     e. invokeBeanFactoryPostProcessors() — @PropertySource, @Import, etc.
     f. registerBeanPostProcessors()      — @Autowired processor, AOP, etc.
     g. initMessageSource()
     h. initApplicationEventMulticaster()
     i. onRefresh()
     j. registerListeners()
     k. finishBeanFactoryInitialization() — instantiate all singletons
     l. finishRefresh()           — publish ContextRefreshedEvent
```

The XML is parsed in step 2b. By step 2k, all singleton beans exist in memory, all dependencies are injected, and all `@PostConstruct` methods have run.

## 4. Diagram

<svg viewBox="0 0 680 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="ClassPathXmlApplicationContext loading beans.xml from classpath, parsing to BeanDefinitions, then instantiating singletons">
  <defs>
    <marker id="a22" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>

  <!-- Classpath resource -->
  <rect x="10" y="80" width="140" height="56" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="80" y="103" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">beans.xml</text>
  <text x="80" y="121" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">classpath resource</text>

  <!-- CPXAC -->
  <rect x="220" y="60" width="180" height="90" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="310" y="85" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">ClassPathXml</text>
  <text x="310" y="101" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">ApplicationContext</text>
  <text x="310" y="118" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">XmlBeanDefinitionReader</text>
  <text x="310" y="133" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">→ BeanDefinitions</text>

  <line x1="150" y1="108" x2="218" y2="108" stroke="#8b949e" stroke-width="1.5" marker-end="url(#a22)"/>
  <text x="184" y="102" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">parse</text>

  <!-- refresh() box -->
  <rect x="220" y="168" width="180" height="34" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1"/>
  <text x="310" y="190" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">refresh() — eager singleton init</text>

  <line x1="310" y1="150" x2="310" y2="166" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a22)"/>

  <!-- Singleton beans -->
  <rect x="480" y="60" width="185" height="90" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="572" y="85" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">Singleton Beans</text>
  <text x="572" y="103" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">orderService</text>
  <text x="572" y="117" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">emailService</text>
  <text x="572" y="131" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">dataSource (etc.)</text>

  <line x1="400" y1="108" x2="478" y2="108" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a22)"/>
  <text x="439" y="102" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">instantiate</text>

  <text x="340" y="210" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Constructor call triggers parse → BeanDefinitions → refresh() → all singletons ready</text>
</svg>

Passing the XML path to the constructor triggers `refresh()` automatically. After the constructor returns, all singleton beans are alive and wired.

## 5. Runnable example

Scenario: a bookstore `CatalogService` that depends on a `PriceCalculator`. We show XML-style metadata loading through three levels: a flat registry, a parent-child context split, and runtime bean replacement.

### Level 1 — Basic

One XML-like config, one context, basic bean lookup — mirrors what `ClassPathXmlApplicationContext("beans.xml")` does.

```java
// CpxacDemo.java — run with: java CpxacDemo.java
import java.util.*;

public class CpxacDemo {

    record Book(String isbn, String title, double basePrice) {}

    interface PriceCalculator {
        double calculate(Book book, int quantity);
    }

    static class StandardPriceCalculator implements PriceCalculator {
        public double calculate(Book book, int quantity) {
            return book.basePrice() * quantity;
        }
    }

    static class CatalogService {
        private final PriceCalculator calculator;
        CatalogService(PriceCalculator calculator) { this.calculator = calculator; }

        void quote(Book book, int qty) {
            double total = calculator.calculate(book, qty);
            System.out.printf("  Quote: %s x%d = $%.2f%n", book.title(), qty, total);
        }
    }

    // --- Simulates ClassPathXmlApplicationContext("beans.xml") ---
    static class XmlAppContext {
        private final Map<String, Object> beans = new LinkedHashMap<>();

        // Simulates loading <bean> elements from beans.xml
        void loadXml() {
            System.out.println("[XML] Parsing beans.xml from classpath...");
            PriceCalculator calc = new StandardPriceCalculator();
            beans.put("priceCalculator", calc);
            beans.put("catalogService",  new CatalogService(calc));
            System.out.println("[XML] Loaded: " + beans.keySet());
            System.out.println("[REFRESH] All singletons instantiated.\n");
        }

        @SuppressWarnings("unchecked")
        <T> T getBean(String name) { return (T) beans.get(name); }
    }

    public static void main(String[] args) {
        XmlAppContext ctx = new XmlAppContext();
        ctx.loadXml();  // mirrors: new ClassPathXmlApplicationContext("beans.xml")

        CatalogService catalog = ctx.getBean("catalogService");
        Book java = new Book("978-0-13-468599-1", "Effective Java", 45.00);
        Book spring = new Book("978-1-61-729586-8", "Spring in Action", 49.99);

        catalog.quote(java,   2);
        catalog.quote(spring, 1);
    }
}
```

How to run: `java CpxacDemo.java`

After `loadXml()` (which mirrors the `ClassPathXmlApplicationContext` constructor), all beans exist. `getBean("catalogService")` returns the singleton — no additional creation happens.

### Level 2 — Intermediate

Multiple XML files: a base context (`base-beans.xml`) and an override file (`discount-beans.xml`) that replaces the pricing strategy — simulating `new ClassPathXmlApplicationContext("base-beans.xml", "discount-beans.xml")`.

```java
// CpxacDemo2.java — run with: java CpxacDemo2.java
import java.util.*;
import java.util.function.*;

public class CpxacDemo2 {

    record Book(String isbn, String title, double basePrice) {}

    interface PriceCalculator { double calculate(Book book, int quantity); }

    static class StandardPriceCalculator implements PriceCalculator {
        public double calculate(Book book, int qty) { return book.basePrice() * qty; }
    }

    static class DiscountPriceCalculator implements PriceCalculator {
        private final double discountPct;
        DiscountPriceCalculator(double pct) { this.discountPct = pct; }
        public double calculate(Book book, int qty) {
            return book.basePrice() * qty * (1 - discountPct);
        }
    }

    static class CatalogService {
        private final PriceCalculator calculator;
        CatalogService(PriceCalculator calculator) { this.calculator = calculator; }
        void quote(Book b, int qty) {
            System.out.printf("  Quote: %s x%d = $%.2f%n", b.title(), qty, calculator.calculate(b, qty));
        }
    }

    // Each "xml file" is a Map of bean definitions
    static class MultiFileXmlContext {
        private final Map<String, Supplier<Object>> defs  = new LinkedHashMap<>();
        private final Map<String, Object>           beans = new LinkedHashMap<>();

        void loadFile(String filename, Map<String, Supplier<Object>> fileDefs) {
            System.out.println("[XML] Loading " + filename + "...");
            // Later file overrides earlier definition for same name (Spring behaviour)
            defs.putAll(fileDefs);
            System.out.println("  Defined: " + fileDefs.keySet());
        }

        void refresh() {
            System.out.println("[REFRESH] Instantiating all singletons from merged definitions...");
            for (var e : defs.entrySet()) {
                beans.put(e.getKey(), e.getValue().get());
                System.out.println("  Ready: " + e.getKey());
            }
            System.out.println();
        }

        @SuppressWarnings("unchecked")
        <T> T getBean(String name) { return (T) beans.get(name); }
    }

    public static void main(String[] args) {
        MultiFileXmlContext ctx = new MultiFileXmlContext();

        // --- base-beans.xml ---
        PriceCalculator standard = new StandardPriceCalculator();
        ctx.loadFile("base-beans.xml", Map.of(
            "priceCalculator", () -> standard,
            "catalogService",  () -> new CatalogService(standard)
        ));

        // --- discount-beans.xml (overrides priceCalculator) ---
        PriceCalculator discount = new DiscountPriceCalculator(0.20); // 20% off
        ctx.loadFile("discount-beans.xml", new LinkedHashMap<>(Map.of(
            "priceCalculator", () -> discount,
            "catalogService",  () -> new CatalogService(discount)  // re-wired to discount
        )));

        ctx.refresh();  // merges both files, later file wins on duplicates

        System.out.println("=== Catalog with 20% discount ===");
        CatalogService catalog = ctx.getBean("catalogService");
        Book java = new Book("978-0-13-468599-1", "Effective Java",    45.00);
        Book spring = new Book("978-1-61-729586-8", "Spring in Action", 49.99);
        catalog.quote(java,   3);
        catalog.quote(spring, 2);
    }
}
```

How to run: `java CpxacDemo2.java`

When Spring merges multiple XML files, a bean defined in a later file **replaces** the same-named bean from an earlier file. This is how environment-specific overrides work: `base-beans.xml` has defaults, `production-beans.xml` overrides datasource / pricing / etc. The last file wins.

### Level 3 — Advanced

Add a parent-child context split: a parent context holds shared infrastructure (pricing, config), and a child context holds request-scoped beans (catalog session). Child beans can see parent beans; parent beans cannot see child beans.

```java
// CpxacDemo3.java — run with: java CpxacDemo3.java
import java.util.*;
import java.util.function.*;

public class CpxacDemo3 {

    record Book(String isbn, String title, double basePrice) {}

    interface PriceCalculator { double calculate(Book b, int qty); }

    static class DiscountPriceCalculator implements PriceCalculator {
        private final double pct;
        DiscountPriceCalculator(double pct) { this.pct = pct; }
        public double calculate(Book b, int qty) {
            double total = b.basePrice() * qty * (1 - pct);
            System.out.printf("    Pricing: %s x%d base=$%.2f disc=%.0f%% → $%.2f%n",
                b.title(), qty, b.basePrice() * qty, pct * 100, total);
            return total;
        }
    }

    // Shared across all sessions — lives in PARENT context
    static class CatalogRepository {
        private final List<Book> inventory = new ArrayList<>(List.of(
            new Book("978-0-13-468599-1", "Effective Java",     45.00),
            new Book("978-1-61-729586-8", "Spring in Action",   49.99),
            new Book("978-0-59-651798-8", "Clean Code",         35.00)
        ));
        List<Book> findAll() { return Collections.unmodifiableList(inventory); }
    }

    // Per-session (child context) — holds a shopping cart
    static class CatalogSession {
        private final CatalogRepository repo;
        private final PriceCalculator   calculator;
        private final List<String>      cart = new ArrayList<>();

        CatalogSession(CatalogRepository repo, PriceCalculator calc) {
            this.repo = repo; this.calculator = calc;
        }

        void addToCart(String isbn) {
            repo.findAll().stream()
                .filter(b -> b.isbn().equals(isbn)).findFirst()
                .ifPresent(b -> { cart.add(isbn); System.out.println("  Added to cart: " + b.title()); });
        }

        double checkout() {
            double total = 0;
            System.out.println("  === Checkout ===");
            for (String isbn : cart) {
                Book b = repo.findAll().stream().filter(x -> x.isbn().equals(isbn)).findFirst().get();
                total += calculator.calculate(b, 1);
            }
            return total;
        }
    }

    // Hierarchical context simulation
    static class HierarchicalContext {
        private final Map<String, Object> beans  = new LinkedHashMap<>();
        private final HierarchicalContext parent;

        HierarchicalContext(HierarchicalContext parent) { this.parent = parent; }

        void register(String name, Object bean) {
            beans.put(name, bean);
            System.out.println("  [CTX:" + (parent == null ? "parent" : "child") + "] registered: " + name);
        }

        @SuppressWarnings("unchecked")
        <T> T getBean(String name) {
            if (beans.containsKey(name)) return (T) beans.get(name);
            if (parent != null)           return parent.getBean(name);  // delegate to parent
            throw new RuntimeException("No bean: " + name);
        }
    }

    public static void main(String[] args) {
        System.out.println("=== Parent context (shared infrastructure) ===");
        HierarchicalContext parentCtx = new HierarchicalContext(null);
        CatalogRepository repo = new CatalogRepository();
        PriceCalculator calc   = new DiscountPriceCalculator(0.15);  // 15% student discount
        parentCtx.register("catalogRepository", repo);
        parentCtx.register("priceCalculator",   calc);

        System.out.println("\n=== Child context (session for alice) ===");
        HierarchicalContext aliceCtx = new HierarchicalContext(parentCtx);
        // Child re-uses parent's repo and calculator via parent lookup
        aliceCtx.register("catalogSession",
            new CatalogSession(
                aliceCtx.getBean("catalogRepository"),
                aliceCtx.getBean("priceCalculator")
            )
        );

        System.out.println("\n=== Alice's session ===");
        CatalogSession aliceSession = aliceCtx.getBean("catalogSession");
        aliceSession.addToCart("978-0-13-468599-1");  // Effective Java
        aliceSession.addToCart("978-0-59-51798-8");   // Clean Code (isbn typo — skipped)
        aliceSession.addToCart("978-1-61-729586-8");  // Spring in Action
        System.out.printf("  Total: $%.2f%n", aliceSession.checkout());

        System.out.println("\n--- Parent cannot see child beans ---");
        try { parentCtx.getBean("catalogSession"); }
        catch (RuntimeException e) { System.out.println("  Expected: " + e.getMessage()); }
    }
}
```

How to run: `java CpxacDemo3.java`

Parent context holds shared infrastructure (repository, pricing). Child context holds session-scoped beans. `aliceCtx.getBean("catalogRepository")` delegates up to `parentCtx`. `parentCtx.getBean("catalogSession")` throws — parent cannot see child beans. This is the Spring MVC pattern: one root `ClassPathXmlApplicationContext` for services/repositories, one child context (per dispatcher) for controllers.

## 6. Walkthrough

**Level 3 execution — context hierarchy:**

1. `parentCtx` created (no parent). `repo` and `calc` registered.
2. `aliceCtx` created with `parentCtx` as parent.
3. `aliceCtx.getBean("catalogRepository")` — not in `aliceCtx.beans` → delegates to `parentCtx` → found.
4. `aliceCtx.getBean("priceCalculator")` — same delegation.
5. `CatalogSession` constructed with the looked-up parent beans and registered in `aliceCtx`.

**`aliceSession.addToCart("978-0-13-468599-1")`:**
```
addToCart("978-0-13-468599-1")
  → repo.findAll() → 3 books
  → filter isbn → Book("978-0-13-468599-1", "Effective Java", 45.00)
  → cart.add(isbn)
  → "Added to cart: Effective Java"
```

**`aliceSession.checkout()`:**
```
checkout()
  → for each isbn in cart:
      isbn="978-0-13-468599-1" → Book("Effective Java", 45.00)
        → calc.calculate(book, 1)
            → 45.00 * 1 * (1 - 0.15) = 38.25
      isbn="978-1-61-729586-8" → Book("Spring in Action", 49.99)
        → calc.calculate(book, 1)
            → 49.99 * 0.85 = 42.49
  → total = 38.25 + 42.49 = 80.74
```

**Data flow through layers:**

| Layer | Input | Output |
|---|---|---|
| `aliceCtx.getBean(...)` | bean name | delegates to `parentCtx` → returns shared singleton |
| `repo.findAll()` | none | immutable list of 3 books |
| `DiscountPriceCalculator.calculate` | book + qty | `basePrice * qty * 0.85` |
| `aliceSession.checkout()` | cart item list | total dollar amount |

## 7. Gotchas & takeaways

> **`ClassPathXmlApplicationContext` calls `refresh()` in its constructor** — the context is fully initialized by the time the constructor returns. If `refresh()` fails (missing bean, circular dep, bad XML), the constructor throws and no context is returned.

> **Classpath resource resolution uses the thread's context class loader.** In OSGi, web containers, or multi-classloader environments the classpath may not include the directory you expect. Use `classpath*:` prefix to search across all classloader roots: `new ClassPathXmlApplicationContext("classpath*:beans/*.xml")`.

- Use `classpath:` (single location) for exact file lookup and `classpath*:` (all locations) when multiple JARs may contribute the same filename.
- To suppress refresh in the constructor (for testing), use `new ClassPathXmlApplicationContext(configLocations, false, null)` then configure the context and call `refresh()` manually.
- Spring MVC uses a parent (root) `ClassPathXmlApplicationContext` for service/repository beans and a child `XmlWebApplicationContext` for web/controller beans — the parent-child hierarchy prevents controllers from contaminating the service layer.
- In test code, use `@ContextConfiguration("classpath:test-beans.xml")` instead of constructing `ClassPathXmlApplicationContext` directly; Spring caches the test context between tests.
- `close()` the context when done to trigger `@PreDestroy` and `DisposableBean.destroy()` callbacks; in a Spring Boot app this happens automatically on JVM shutdown.
