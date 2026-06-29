---
card: spring-framework
gi: 33
slug: instantiation-with-a-constructor
title: Instantiation with a constructor
---

## 1. What it is

**Constructor instantiation** is the default and most common way Spring creates a bean: the container calls the class's constructor directly, passing injected dependencies as arguments.

```java
@Service
public class OrderService {
    private final EmailService email;

    // Spring calls this constructor and injects emailService
    public OrderService(EmailService email) {
        this.email = email;
    }
}
```

The container selects the constructor to call based on the `BeanDefinition`:
- **No-arg constructor:** used when no constructor args are configured.
- **Single constructor:** used automatically since Spring 4.3 — no `@Autowired` needed.
- **Multiple constructors:** `@Autowired` or `@Bean` argument binding selects the one to use.

In one sentence: **Constructor instantiation is how Spring creates beans by calling their constructors — either a no-arg constructor for simple beans, or an arg-bearing constructor with dependencies injected as parameters.**

## 2. Why & when

Constructor instantiation is the **recommended** way to create Spring beans because it:
- Makes dependencies explicit (they appear in the constructor signature).
- Allows `final` fields — the class is immutable after construction.
- Makes the bean testable without a Spring context: `new OrderService(new MockEmailService())`.
- Fails at startup if a dependency is missing, rather than failing silently later.

Use constructor injection for all **required** dependencies. If a dependency is optional, use setter injection and mark it `@Autowired(required = false)`.

The only case where no-arg construction is necessary is when Spring uses CGLIB to subclass your bean (e.g., for `@Transactional`): CGLIB requires a no-arg constructor on the proxied class.

## 3. Core concept

The container selects and invokes a constructor during `finishBeanFactoryInitialization()`:

```
finishBeanFactoryInitialization()
  → for each singleton BeanDefinition:
      → SmartInstantiationAwareBeanPostProcessor.determineCandidateConstructors()
          returns the @Autowired constructor (or the sole constructor)
      → ConstructorResolver.autowireConstructor()
          resolve each parameter type → find matching bean → create arg list
      → Constructor.newInstance(args)   ← actual instantiation
      → BeanPostProcessors applied
```

Circular dependency note: if bean A's constructor needs B and B's constructor needs A, Spring throws `BeanCurrentlyInCreationException`. Constructor injection has **no** way to resolve circular deps (unlike setter injection where the container can inject a partially-constructed bean).

## 4. Diagram

<svg viewBox="0 0 680 210" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Constructor instantiation: container resolves constructor parameters by type, calls newInstance, returns fully constructed bean">
  <defs>
    <marker id="a33" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>

  <!-- Container step -->
  <rect x="10" y="20" width="200" height="70" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="110" y="44" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">Container</text>
  <text x="110" y="60" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">resolve constructor params</text>
  <text x="110" y="76" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">by type → find matching beans</text>

  <!-- Deps available -->
  <rect x="10" y="120" width="200" height="56" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="110" y="145" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">EmailService singleton ✓</text>
  <text x="110" y="162" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">AuditLogger singleton ✓</text>

  <line x1="110" y1="90" x2="110" y2="118" stroke="#8b949e" stroke-width="1.5" marker-end="url(#a33)"/>
  <text x="132" y="108" fill="#8b949e" font-size="8" font-family="sans-serif">available deps</text>

  <!-- Constructor call -->
  <rect x="280" y="50" width="200" height="70" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="380" y="74" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">Constructor.newInstance()</text>
  <text x="380" y="90" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">new OrderService(email, audit)</text>

  <line x1="210" y1="55" x2="278" y2="70" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a33)"/>
  <line x1="210" y1="148" x2="278" y2="95" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a33)"/>

  <!-- Ready bean -->
  <rect x="550" y="55" width="120" height="60" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="610" y="80" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">OrderService</text>
  <text x="610" y="97" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">fully constructed</text>

  <line x1="480" y1="85" x2="548" y2="85" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a33)"/>

  <text x="340" y="175" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Container resolves each constructor parameter by type, builds arg list, calls newInstance()</text>
</svg>

The container resolves each constructor parameter type by searching the bean registry, assembles the argument list, and calls `Constructor.newInstance(args)`. The result is a fully constructed bean with all required dependencies injected.

## 5. Runnable example

Scenario: an inventory system with a `WarehouseService` that depends on a `LocationRepository` and a `StockTracker`. We evolve from no-arg to single-arg to multi-arg constructor instantiation.

### Level 1 — Basic

No-arg constructor: the simplest case — Spring calls the default constructor and the bean configures itself.

```java
// CtorInstDemo.java — run with: java CtorInstDemo.java
import java.util.*;

public class CtorInstDemo {

    record StockItem(String sku, int qty) {}

    // No-arg constructor — Spring can instantiate this directly
    static class InventoryStore {
        private final Map<String, Integer> stock = new HashMap<>(Map.of(
            "LAPTOP-001", 42,
            "MONITOR-002", 15,
            "KEYBOARD-003", 78
        ));

        InventoryStore() {
            System.out.println("  [BEAN] InventoryStore() — no-arg constructor called");
        }

        Optional<StockItem> find(String sku) {
            return Optional.ofNullable(stock.get(sku)).map(q -> new StockItem(sku, q));
        }

        void reserve(String sku, int qty) {
            stock.computeIfPresent(sku, (k, v) -> v - qty);
            System.out.println("  [STOCK] Reserved " + qty + "x " + sku);
        }
    }

    // No-arg bean container
    static class NoArgCtx {
        private final Map<Class<?>, Object> beans = new LinkedHashMap<>();

        <T> void register(Class<T> cls) throws Exception {
            // Calls the no-arg constructor — mirrors Spring's default behavior
            T bean = cls.getDeclaredConstructor().newInstance();
            beans.put(cls, bean);
            System.out.println("  [CTX] Created via no-arg ctor: " + cls.getSimpleName());
        }

        @SuppressWarnings("unchecked")
        <T> T getBean(Class<T> type) { return (T) beans.get(type); }
    }

    public static void main(String[] args) throws Exception {
        NoArgCtx ctx = new NoArgCtx();
        ctx.register(InventoryStore.class);

        System.out.println("\n=== Application using the bean ===");
        InventoryStore store = ctx.getBean(InventoryStore.class);
        store.find("LAPTOP-001").ifPresent(i ->
            System.out.println("  Found: " + i.sku() + " qty=" + i.qty()));
        store.reserve("LAPTOP-001", 5);
        store.find("LAPTOP-001").ifPresent(i ->
            System.out.println("  After reserve: " + i.sku() + " qty=" + i.qty()));
    }
}
```

How to run: `java CtorInstDemo.java`

`InventoryStore` needs no external dependencies — its no-arg constructor works. Spring calls `Class.getDeclaredConstructor().newInstance()`. The bean is self-contained; all its data lives inside.

### Level 2 — Intermediate

Single-arg constructor: `WarehouseService` depends on `InventoryStore`. Spring resolves the constructor parameter by type.

```java
// CtorInstDemo2.java — run with: java CtorInstDemo2.java
import java.util.*;
import java.lang.reflect.*;

public class CtorInstDemo2 {

    record StockItem(String sku, int qty) {}
    record Reservation(String orderId, String sku, int qty) {}

    static class InventoryStore {
        private final Map<String, Integer> stock = new HashMap<>(Map.of(
            "LAPTOP-001", 42, "MONITOR-002", 15
        ));
        InventoryStore() { System.out.println("  [BEAN] InventoryStore() — no-arg ctor"); }

        Optional<StockItem> find(String sku) {
            return Optional.ofNullable(stock.get(sku)).map(q -> new StockItem(sku, q));
        }

        boolean reserve(String sku, int qty) {
            Integer current = stock.get(sku);
            if (current == null || current < qty) return false;
            stock.put(sku, current - qty);
            return true;
        }
    }

    // Single-arg constructor — depends on InventoryStore
    static class WarehouseService {
        private final InventoryStore store;
        private final List<Reservation> log = new ArrayList<>();

        WarehouseService(InventoryStore store) {
            this.store = store;
            System.out.println("  [BEAN] WarehouseService(InventoryStore) — 1-arg ctor");
        }

        boolean processReservation(String orderId, String sku, int qty) {
            boolean ok = store.reserve(sku, qty);
            Reservation r = new Reservation(orderId, sku, qty);
            log.add(r);
            System.out.printf("  [WAREHOUSE] Reservation %s: %s x%d → %s%n",
                orderId, sku, qty, ok ? "OK" : "INSUFFICIENT");
            return ok;
        }

        void showLog() {
            System.out.println("  Reservation log (" + log.size() + "):");
            log.forEach(r -> System.out.println("    " + r));
        }
    }

    // Container that resolves single-arg constructors by type
    static class AutoWireCtx {
        private final Map<Class<?>, Object> beans = new LinkedHashMap<>();

        void register(Class<?> cls) throws Exception {
            Constructor<?>[] ctors = cls.getDeclaredConstructors();
            Constructor<?> ctor = ctors[0];  // use first constructor
            Object[] args = Arrays.stream(ctor.getParameterTypes())
                .map(t -> {
                    Object dep = beans.entrySet().stream()
                        .filter(e -> t.isAssignableFrom(e.getKey()))
                        .map(Map.Entry::getValue).findFirst().orElse(null);
                    if (dep == null) throw new RuntimeException(
                        "Unsatisfied dep '" + t.getSimpleName() + "' for " + cls.getSimpleName());
                    return dep;
                }).toArray();
            Object bean = ctor.newInstance(args);
            beans.put(cls, bean);
            System.out.println("  [CTX] Created via " + ctor.getParameterCount() + "-arg ctor: " + cls.getSimpleName());
        }

        @SuppressWarnings("unchecked")
        <T> T getBean(Class<T> type) { return (T) beans.get(type); }
    }

    public static void main(String[] args) throws Exception {
        AutoWireCtx ctx = new AutoWireCtx();

        System.out.println("=== Container startup (order matters: dep before consumer) ===");
        ctx.register(InventoryStore.class);   // no deps — created first
        ctx.register(WarehouseService.class); // depends on InventoryStore

        System.out.println("\n=== Processing reservations ===");
        WarehouseService warehouse = ctx.getBean(WarehouseService.class);
        warehouse.processReservation("ORD-001", "LAPTOP-001", 5);
        warehouse.processReservation("ORD-002", "MONITOR-002", 20);  // insufficient
        warehouse.processReservation("ORD-003", "LAPTOP-001", 3);

        System.out.println();
        warehouse.showLog();
    }
}
```

How to run: `java CtorInstDemo2.java`

`WarehouseService` requires `InventoryStore` — the container finds it in the bean registry by type and passes it as a constructor argument. If `InventoryStore` had not been registered first, the container would throw a "Unsatisfied dep" error at startup.

### Level 3 — Advanced

Multi-arg constructor with type ambiguity: two beans of the same interface type require `@Qualifier`-style name matching.

```java
// CtorInstDemo3.java — run with: java CtorInstDemo3.java
import java.util.*;
import java.lang.annotation.*;
import java.lang.reflect.*;

public class CtorInstDemo3 {

    @Retention(RetentionPolicy.RUNTIME)
    @Target(ElementType.PARAMETER)
    @interface Qualifier { String value(); }

    record StockItem(String sku, int qty) {}

    interface StockRepository {
        Optional<StockItem> find(String sku);
        boolean reserve(String sku, int qty);
        String region();
    }

    static class USStockRepository implements StockRepository {
        private final Map<String, Integer> stock = new HashMap<>(Map.of("LAPTOP-US", 50));
        public Optional<StockItem> find(String s) { return Optional.ofNullable(stock.get(s)).map(q -> new StockItem(s, q)); }
        public boolean reserve(String s, int q) {
            Integer c = stock.get(s);
            if (c == null || c < q) return false;
            stock.put(s, c - q); return true;
        }
        public String region() { return "US"; }
    }

    static class EUStockRepository implements StockRepository {
        private final Map<String, Integer> stock = new HashMap<>(Map.of("LAPTOP-EU", 35));
        public Optional<StockItem> find(String s) { return Optional.ofNullable(stock.get(s)).map(q -> new StockItem(s, q)); }
        public boolean reserve(String s, int q) {
            Integer c = stock.get(s);
            if (c == null || c < q) return false;
            stock.put(s, c - q); return true;
        }
        public String region() { return "EU"; }
    }

    // Two-arg constructor with qualified parameters
    static class GlobalWarehouseService {
        private final StockRepository usRepo;
        private final StockRepository euRepo;

        GlobalWarehouseService(
            @Qualifier("usRepo") StockRepository usRepo,
            @Qualifier("euRepo") StockRepository euRepo) {
            this.usRepo = usRepo;
            this.euRepo = euRepo;
            System.out.println("  [BEAN] GlobalWarehouseService(usRepo, euRepo) — 2-arg ctor");
        }

        void reserve(String region, String sku, int qty) {
            StockRepository repo = region.equals("US") ? usRepo : euRepo;
            boolean ok = repo.reserve(sku, qty);
            System.out.printf("  [GLOBAL] [%s] %s x%d → %s%n", region, sku, qty, ok ? "OK" : "FAIL");
        }

        void showAvailable() {
            List.of(new String[]{"LAPTOP-US","US"}, new String[]{"LAPTOP-EU","EU"}).forEach(pair -> {
                StockRepository r = pair[1].equals("US") ? usRepo : euRepo;
                r.find(pair[0]).ifPresent(i -> System.out.printf("  [%s] %s qty=%d%n", pair[1], i.sku(), i.qty()));
            });
        }
    }

    // Qualifier-aware container
    static class QualifierCtx {
        private final Map<String, Object>  named = new LinkedHashMap<>();
        private final Map<Class<?>, Object> typed = new LinkedHashMap<>();

        void register(String name, Object bean) {
            named.put(name, bean);
            typed.put(bean.getClass(), bean);
            for (Class<?> iface : bean.getClass().getInterfaces()) typed.put(iface, bean);
        }

        void registerByType(Class<?> cls) throws Exception {
            Constructor<?> ctor = cls.getDeclaredConstructors()[0];
            Parameter[] params = ctor.getParameters();
            Object[] args = new Object[params.length];
            for (int i = 0; i < params.length; i++) {
                Qualifier q = params[i].getAnnotation(Qualifier.class);
                if (q != null) {
                    args[i] = named.get(q.value());
                    if (args[i] == null) throw new RuntimeException("No bean named '" + q.value() + "'");
                } else {
                    args[i] = typed.get(params[i].getType());
                    if (args[i] == null) throw new RuntimeException("No bean of type " + params[i].getType());
                }
            }
            Object bean = ctor.newInstance(args);
            named.put(cls.getSimpleName(), bean);
            typed.put(cls, bean);
            System.out.println("  [CTX] Wired " + cls.getSimpleName() + " via " + params.length + "-arg ctor");
        }

        @SuppressWarnings("unchecked")
        <T> T getBean(Class<T> type) { return (T) typed.get(type); }
    }

    public static void main(String[] args) throws Exception {
        QualifierCtx ctx = new QualifierCtx();

        System.out.println("=== Registration ===");
        ctx.register("usRepo", new USStockRepository());
        ctx.register("euRepo", new EUStockRepository());
        ctx.registerByType(GlobalWarehouseService.class);

        System.out.println("\n=== Initial stock ===");
        GlobalWarehouseService gws = ctx.getBean(GlobalWarehouseService.class);
        gws.showAvailable();

        System.out.println("\n=== Reservations ===");
        gws.reserve("US", "LAPTOP-US", 10);
        gws.reserve("EU", "LAPTOP-EU", 40);  // exceeds stock
        gws.reserve("US", "LAPTOP-US", 5);

        System.out.println("\n=== Updated stock ===");
        gws.showAvailable();
    }
}
```

How to run: `java CtorInstDemo3.java`

`GlobalWarehouseService` has two constructor parameters of the same type (`StockRepository`). Without `@Qualifier`, the container cannot distinguish them. `@Qualifier("usRepo")` and `@Qualifier("euRepo")` tell the container which named bean to inject into each position — exactly how Spring resolves ambiguous multi-arg constructors.

## 6. Walkthrough

**Level 3 — multi-arg constructor resolution:**

```
ctx.registerByType(GlobalWarehouseService.class)
  → ctor = GlobalWarehouseService(StockRepository, StockRepository)
  → params = [@Qualifier("usRepo") StockRepository, @Qualifier("euRepo") StockRepository]

  Parameter 0:
    @Qualifier("usRepo") present → named["usRepo"] → USStockRepository ✓

  Parameter 1:
    @Qualifier("euRepo") present → named["euRepo"] → EUStockRepository ✓

  → ctor.newInstance(usRepo, euRepo)
  → "[BEAN] GlobalWarehouseService(usRepo, euRepo) — 2-arg ctor"
```

**`gws.reserve("US", "LAPTOP-US", 10)`:**
```
reserve("US", "LAPTOP-US", 10)
  → repo = usRepo (region == "US")
  → usRepo.reserve("LAPTOP-US", 10)
      → stock["LAPTOP-US"] = 50 - 10 = 40 → true
  → "[GLOBAL] [US] LAPTOP-US x10 → OK"
```

**`gws.reserve("EU", "LAPTOP-EU", 40)`:**
```
reserve("EU", "LAPTOP-EU", 40)
  → repo = euRepo
  → euRepo.reserve("LAPTOP-EU", 40)
      → stock["LAPTOP-EU"] = 35 < 40 → false
  → "[GLOBAL] [EU] LAPTOP-EU x40 → FAIL"
```

**Data flow through constructor injection:**

| Step | Action | Result |
|---|---|---|
| Register `usRepo` | `named["usRepo"] = USStockRepository` | bean available by name |
| Register `euRepo` | `named["euRepo"] = EUStockRepository` | bean available by name |
| Wire `GlobalWarehouseService` | resolve `@Qualifier` → match named beans | fully wired warehouse |
| `reserve("US", ...)` | delegate to `usRepo` | US stock decremented |

## 7. Gotchas & takeaways

> **Constructor injection creates circular dependency deadlocks.** If A's constructor needs B and B's constructor needs A, Spring cannot construct either — it throws `BeanCurrentlyInCreationException`. The only fix is to break the circular dependency by refactoring, or use setter/field injection on one side (which allows a partially-constructed proxy).

> **CGLIB subclass proxies require a no-arg constructor** on the proxied class. If `@Transactional` is on a class and the class has only an arg-bearing constructor, Spring throws at startup. The fix: add a protected no-arg constructor (CGLIB calls it without invoking your `@PostConstruct` logic).

- Spring 4.3+ auto-selects the sole constructor without `@Autowired`. With multiple constructors, mark the intended one with `@Autowired`.
- Constructor arguments are resolved in order at startup — missing or ambiguous types throw early. This is the fail-fast behaviour that makes constructor injection the safe default.
- `@Bean` methods in `@Configuration` classes use the method signature as the constructor spec: `@Bean OrderService orderService(EmailService email)` — Spring injects `email` the same way as a constructor parameter.
- Use `@Primary` on one bean when two of the same type exist and you always want one to win without `@Qualifier` on every injection point.
- Prefer immutable fields (`final`) in constructor-injected beans — they document that the class is stateless after construction and prevent accidental reassignment.
