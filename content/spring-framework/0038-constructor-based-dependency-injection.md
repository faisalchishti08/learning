---
card: spring-framework
gi: 38
slug: constructor-based-dependency-injection
title: Constructor-based dependency injection
---

## 1. What it is

**Constructor-based dependency injection (DI)** supplies a bean's dependencies through its constructor. The container creates the bean by invoking a constructor with arguments that are themselves resolved from the container.

```java
@Component
public class OrderService {

    private final PaymentGateway gateway;
    private final InventoryService inventory;

    // Spring sees one constructor — injects both dependencies
    public OrderService(PaymentGateway gateway, InventoryService inventory) {
        this.gateway   = gateway;
        this.inventory = inventory;
    }
}
```

Since Spring Framework 4.3, if a class has exactly one constructor, the `@Autowired` annotation is optional — Spring injects it automatically.

In one sentence: **Constructor-based DI passes a bean's required collaborators as constructor arguments at the moment of creation, ensuring the object is fully initialized and all mandatory dependencies are non-null from the first line of the constructor body.**

## 2. Why & when

Constructor-based DI is preferred when:

- **The dependency is mandatory.** A bean that cannot function without `PaymentGateway` should declare it in the constructor — a missing bean causes a container startup failure, not a silent NPE at runtime.
- **Immutability.** Fields set via constructor can be `final`, preventing accidental re-assignment after creation.
- **Testability.** Constructor injection makes dependencies explicit; unit tests pass mocks directly without needing a container or reflection.
- **Detecting circular dependencies early.** Constructors force all dependencies to be available at creation time — a circular constructor dependency throws `BeanCurrentlyInCreationException` at startup.

Setter injection is appropriate for optional dependencies or when legacy code cannot add a constructor parameter (covered in a later tutorial).

## 3. Core concept

```
OrderService constructor resolution:

  Constructor: OrderService(PaymentGateway, InventoryService)

  Spring resolves each argument by type:
    PaymentGateway   → find bean of type PaymentGateway in context
                        → StripeGateway (implements PaymentGateway)
    InventoryService → find bean of type InventoryService in context
                        → WarehouseInventoryService

  Creation:
    new OrderService(stripeGateway, warehouseInventoryService)

  Lifecycle:
    constructor → @PostConstruct → ready to use

Circular dependency:
  A(B) and B(A) → Spring cannot create A without B and B without A
               → BeanCurrentlyInCreationException at startup
```

## 4. Diagram

<svg viewBox="0 0 680 195" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Constructor DI: container resolves PaymentGateway and InventoryService beans, passes them to OrderService constructor">
  <defs>
    <marker id="a38" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>

  <!-- Two dependency beans -->
  <rect x="10" y="20" width="195" height="56" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="108" y="46" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">StripeGateway</text>
  <text x="108" y="64" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">implements PaymentGateway</text>

  <rect x="10" y="110" width="195" height="56" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="108" y="136" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">WarehouseInventoryService</text>
  <text x="108" y="154" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">implements InventoryService</text>

  <!-- Constructor call box -->
  <rect x="255" y="60" width="225" height="68" rx="6" fill="#0d1117" stroke="#6db33f" stroke-width="1.5"/>
  <text x="368" y="82" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">new OrderService(</text>
  <text x="368" y="98" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">stripeGateway,</text>
  <text x="368" y="114" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">warehouseInventoryService)</text>

  <line x1="205" y1="48"  x2="252" y2="82"  stroke="#6db33f" stroke-width="1.5" marker-end="url(#a38)"/>
  <line x1="205" y1="138" x2="252" y2="112" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a38)"/>

  <!-- OrderService -->
  <rect x="530" y="55" width="140" height="78" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="600" y="82" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">OrderService</text>
  <text x="600" y="100" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">final PaymentGateway</text>
  <text x="600" y="114" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">final InventoryService</text>
  <text x="600" y="128" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">fully initialized ✓</text>

  <line x1="480" y1="94" x2="528" y2="94" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a38)"/>
</svg>

The container resolves each constructor parameter by type, then invokes the constructor once. The resulting bean is immediately fully initialized — all `final` fields are set.

## 5. Runnable example

Scenario: an order processing pipeline. `OrderService` depends on `PaymentGateway` and `InventoryService`. Everything wired via constructor — no setters.

### Level 1 — Basic

Single constructor, two dependencies resolved by type.

```java
// ConstructorDIDemo.java — run with: java ConstructorDIDemo.java
import java.util.*;

public class ConstructorDIDemo {

    // Collaborator 1
    interface PaymentGateway {
        boolean charge(String customer, double amount);
    }

    static class StripeGateway implements PaymentGateway {
        StripeGateway() {
            System.out.println("  [BEAN] StripeGateway created");
        }
        @Override
        public boolean charge(String customer, double amount) {
            System.out.printf("  [STRIPE] charge %s $%.2f%n", customer, amount);
            return true;
        }
    }

    // Collaborator 2
    interface InventoryService {
        boolean reserve(String productId, int qty);
    }

    static class WarehouseInventoryService implements InventoryService {
        private final Map<String, Integer> stock = new HashMap<>();

        WarehouseInventoryService() {
            System.out.println("  [BEAN] WarehouseInventoryService created");
            stock.put("LAPTOP-01", 50);
            stock.put("MOUSE-02",  200);
        }

        @Override
        public boolean reserve(String productId, int qty) {
            int available = stock.getOrDefault(productId, 0);
            if (available < qty) {
                System.out.println("  [WAREHOUSE] insufficient stock: " + productId);
                return false;
            }
            stock.put(productId, available - qty);
            System.out.printf("  [WAREHOUSE] reserved %d × %s (remaining: %d)%n",
                qty, productId, available - qty);
            return true;
        }
    }

    // Bean with constructor-based DI — both fields are final
    static class OrderService {
        private final PaymentGateway  gateway;
        private final InventoryService inventory;

        // Spring resolves args by type
        OrderService(PaymentGateway gateway, InventoryService inventory) {
            this.gateway   = gateway;
            this.inventory = inventory;
            System.out.println("  [BEAN] OrderService created via constructor DI");
        }

        String placeOrder(String customer, String productId, int qty, double price) {
            if (!inventory.reserve(productId, qty)) return "FAILED: out of stock";
            if (!gateway.charge(customer, price * qty)) return "FAILED: payment declined";
            String orderId = "ORD-" + (int)(Math.random() * 9000 + 1000);
            System.out.println("  [ORDER] placed " + orderId);
            return orderId;
        }
    }

    // Minimal container: resolve constructor args by type, then instantiate
    static class Ctx {
        private final Map<Class<?>, Object> byType = new LinkedHashMap<>();
        private final Map<String, Object>   byName = new LinkedHashMap<>();

        void register(String name, Object bean) {
            byName.put(name, bean);
            // Register under all implemented interfaces too
            for (Class<?> iface : bean.getClass().getInterfaces()) {
                byType.put(iface, bean);
            }
            byType.put(bean.getClass(), bean);
        }

        // Constructor DI: resolve each parameter by type, then call constructor
        <T> T createByConstructorDI(Class<T> clazz) throws Exception {
            var ctors = clazz.getDeclaredConstructors();
            if (ctors.length != 1) throw new RuntimeException("Expected exactly one constructor");
            var ctor = ctors[0];
            Object[] args = Arrays.stream(ctor.getParameterTypes())
                .map(pt -> {
                    Object dep = byType.get(pt);
                    if (dep == null) throw new RuntimeException("No bean of type: " + pt.getSimpleName());
                    return dep;
                })
                .toArray();
            @SuppressWarnings("unchecked")
            T bean = (T) ctor.newInstance(args);
            register(clazz.getSimpleName(), bean);
            return bean;
        }

        @SuppressWarnings("unchecked")
        <T> T getBean(String name) { return (T) byName.get(name); }
    }

    public static void main(String[] args) throws Exception {
        Ctx ctx = new Ctx();

        System.out.println("=== Container startup ===");
        ctx.register("paymentGateway",  new StripeGateway());
        ctx.register("inventoryService", new WarehouseInventoryService());
        OrderService orderService = ctx.createByConstructorDI(OrderService.class);

        System.out.println("\n=== Application running ===");
        String order1 = orderService.placeOrder("alice", "LAPTOP-01", 2, 999.00);
        String order2 = orderService.placeOrder("bob",   "MOUSE-02",  5, 25.00);
        String order3 = orderService.placeOrder("carol", "LAPTOP-01", 60, 999.00);  // out of stock
        System.out.println("\n  Results: " + order1 + ", " + order2 + ", " + order3);
    }
}
```

How to run: `java ConstructorDIDemo.java`

`createByConstructorDI(OrderService.class)` reads `OrderService`'s single constructor, resolves `PaymentGateway` and `InventoryService` by type from the container, and calls `new OrderService(stripeGateway, warehouseInventoryService)`. Both fields are `final` — the bean is immutable after construction.

### Level 2 — Intermediate

Constructor DI with multiple beans of the same type — qualifier-style disambiguation.

```java
// ConstructorDIDemo2.java — run with: java ConstructorDIDemo2.java
import java.util.*;
import java.lang.annotation.*;

public class ConstructorDIDemo2 {

    @Retention(RetentionPolicy.RUNTIME)
    @interface Named { String value(); }

    interface Cache {
        void put(String key, String value);
        Optional<String> get(String key);
        int size();
    }

    static class LocalCache implements Cache {
        private final Map<String, String> store = new HashMap<>();
        LocalCache() { System.out.println("  [BEAN] LocalCache created"); }
        @Override public void put(String k, String v) { store.put(k, v); }
        @Override public Optional<String> get(String k) { return Optional.ofNullable(store.get(k)); }
        @Override public int size() { return store.size(); }
    }

    static class RemoteCache implements Cache {
        private final Map<String, String> store = new HashMap<>();
        RemoteCache() { System.out.println("  [BEAN] RemoteCache (simulated Redis) created"); }
        @Override public void put(String k, String v) {
            System.out.println("  [REDIS] SET " + k);
            store.put(k, v);
        }
        @Override public Optional<String> get(String k) {
            System.out.println("  [REDIS] GET " + k);
            return Optional.ofNullable(store.get(k));
        }
        @Override public int size() { return store.size(); }
    }

    // Two Cache dependencies: differentiated by @Named qualifier on constructor params
    static class ProductService {
        private final Cache localCache;
        private final Cache remoteCache;

        ProductService(@Named("local") Cache localCache, @Named("remote") Cache remoteCache) {
            this.localCache  = localCache;
            this.remoteCache = remoteCache;
            System.out.println("  [BEAN] ProductService created (constructor DI with qualifiers)");
        }

        String getProduct(String id) {
            return localCache.get(id).orElseGet(() -> {
                String val = remoteCache.get(id)
                    .orElse("Product{id=" + id + ", name=Unknown}");
                localCache.put(id, val);   // warm local cache
                return val;
            });
        }

        void warmCache(Map<String, String> products) {
            products.forEach(remoteCache::put);
        }

        void printStats() {
            System.out.println("  localCache.size()  = " + localCache.size());
            System.out.println("  remoteCache.size() = " + remoteCache.size());
        }
    }

    // Container supporting qualifier-based resolution
    static class Ctx {
        private final Map<String, Object> byName = new LinkedHashMap<>();
        private final Map<Class<?>, Map<String, Object>> byTypeAndQualifier = new HashMap<>();

        void register(String qualifier, String name, Object bean) {
            byName.put(name, bean);
            for (Class<?> iface : bean.getClass().getInterfaces())
                byTypeAndQualifier.computeIfAbsent(iface, k -> new HashMap<>()).put(qualifier, bean);
            byTypeAndQualifier.computeIfAbsent(bean.getClass(), k -> new HashMap<>()).put(qualifier, bean);
        }

        <T> T createByConstructorDI(Class<T> clazz) throws Exception {
            var ctors = clazz.getDeclaredConstructors();
            if (ctors.length != 1) throw new RuntimeException("Expected exactly one constructor");
            var ctor = ctors[0];
            var paramTypes  = ctor.getParameterTypes();
            var annotations = ctor.getParameterAnnotations();
            Object[] args = new Object[paramTypes.length];
            for (int i = 0; i < paramTypes.length; i++) {
                String qualifier = null;
                for (var ann : annotations[i]) {
                    if (ann instanceof Named n) { qualifier = n.value(); break; }
                }
                Map<String, Object> candidates = byTypeAndQualifier.get(paramTypes[i]);
                if (candidates == null) throw new RuntimeException("No bean: " + paramTypes[i].getSimpleName());
                args[i] = (qualifier != null) ? candidates.get(qualifier) : candidates.values().iterator().next();
                if (args[i] == null) throw new RuntimeException("No bean with qualifier '" + qualifier + "'");
            }
            @SuppressWarnings("unchecked")
            T bean = (T) ctor.newInstance(args);
            register("default", clazz.getSimpleName(), bean);
            return bean;
        }

        @SuppressWarnings("unchecked")
        <T> T getBean(String name) { return (T) byName.get(name); }
    }

    public static void main(String[] args) throws Exception {
        Ctx ctx = new Ctx();

        System.out.println("=== Container startup ===");
        ctx.register("local",  "localCache",  new LocalCache());
        ctx.register("remote", "remoteCache", new RemoteCache());
        ProductService svc = ctx.createByConstructorDI(ProductService.class);

        System.out.println("\n=== Populate remote cache ===");
        svc.warmCache(Map.of(
            "PROD-1", "Product{id=PROD-1, name=Laptop, price=999}",
            "PROD-2", "Product{id=PROD-2, name=Mouse,  price=25}"
        ));

        System.out.println("\n=== Read products (first hit goes to remote) ===");
        System.out.println("  " + svc.getProduct("PROD-1"));
        System.out.println("  " + svc.getProduct("PROD-1"));  // second hit: local cache
        System.out.println("  " + svc.getProduct("PROD-3"));  // miss both → default value

        System.out.println("\n=== Cache stats ===");
        svc.printStats();
    }
}
```

How to run: `java ConstructorDIDemo2.java`

`ProductService` has two `Cache` constructor parameters differentiated by `@Named`. The container reads each parameter's `@Named` annotation and looks up the matching bean by qualifier. Both fields are `final` — no risk of `localCache`/`remoteCache` being swapped after construction.

### Level 3 — Advanced

Constructor DI across a three-layer pipeline with a startup validation step.

```java
// ConstructorDIDemo3.java — run with: java ConstructorDIDemo3.java
import java.util.*;

public class ConstructorDIDemo3 {

    // Layer 1: Repository
    interface ReportRepository {
        List<Map<String, Object>> fetchRawData(String query);
    }

    static class DatabaseReportRepository implements ReportRepository {
        private final String dsn;
        private final List<Map<String, Object>> db;

        DatabaseReportRepository(String dsn) {
            System.out.println("  [BEAN] DatabaseReportRepository(dsn=" + dsn + ")");
            this.dsn = dsn;
            db = List.of(
                Map.of("region", "APAC",  "revenue", 420_000.0, "orders", 1_800),
                Map.of("region", "EMEA",  "revenue", 670_000.0, "orders", 2_400),
                Map.of("region", "AMER",  "revenue", 910_000.0, "orders", 3_200)
            );
        }

        @Override
        public List<Map<String, Object>> fetchRawData(String query) {
            System.out.println("  [DB] query: " + query);
            return db;
        }

        boolean isHealthy() {
            System.out.println("  [DB] health check: connected to " + dsn);
            return !dsn.isBlank();
        }
    }

    // Layer 2: Service
    interface ReportFormatter {
        String format(List<Map<String, Object>> rows, String title);
    }

    static class CsvReportFormatter implements ReportFormatter {
        CsvReportFormatter() {
            System.out.println("  [BEAN] CsvReportFormatter created");
        }
        @Override
        public String format(List<Map<String, Object>> rows, String title) {
            StringBuilder sb = new StringBuilder("# " + title + "\nregion,revenue,orders\n");
            rows.forEach(r -> sb.append(r.get("region")).append(",")
                .append(r.get("revenue")).append(",")
                .append(r.get("orders")).append("\n"));
            return sb.toString();
        }
    }

    // Layer 3: Application bean — depends on both repo and formatter
    static class ReportService {
        private final ReportRepository   repository;
        private final ReportFormatter    formatter;
        private final String             reportTitle;

        // Constructor DI — three dependencies (2 beans + 1 scalar)
        ReportService(ReportRepository repository, ReportFormatter formatter, String reportTitle) {
            System.out.println("  [BEAN] ReportService created (3-arg constructor DI)");
            this.repository  = repository;
            this.formatter   = formatter;
            this.reportTitle = reportTitle;
        }

        // @PostConstruct: validate all deps are healthy
        void init() {
            System.out.println("  [@PostConstruct] ReportService.init() — validating dependencies");
            if (repository instanceof DatabaseReportRepository dbRepo && !dbRepo.isHealthy())
                throw new IllegalStateException("Repository health check failed");
            System.out.println("  [@PostConstruct] All dependencies healthy");
        }

        String generateReport(String query) {
            List<Map<String, Object>> data = repository.fetchRawData(query);
            return formatter.format(data, reportTitle);
        }
    }

    static class Ctx {
        private final Map<Class<?>, Object>  byType = new LinkedHashMap<>();
        private final Map<String, Object>    byName = new LinkedHashMap<>();

        void registerBean(String name, Object bean) {
            byName.put(name, bean);
            for (Class<?> iface : bean.getClass().getInterfaces()) byType.put(iface, bean);
            byType.put(bean.getClass(), bean);
        }

        void registerScalar(Class<?> type, Object value) { byType.put(type, value); }

        <T> T createByConstructorDI(Class<T> clazz, boolean callInit) throws Exception {
            var ctors = clazz.getDeclaredConstructors();
            if (ctors.length != 1) throw new RuntimeException("Exactly one constructor required");
            var ctor  = ctors[0];
            Object[] args = Arrays.stream(ctor.getParameterTypes())
                .map(pt -> { Object d = byType.get(pt);
                    if (d == null) throw new RuntimeException("Missing bean: " + pt.getSimpleName());
                    return d;
                }).toArray();
            @SuppressWarnings("unchecked") T bean = (T) ctor.newInstance(args);
            if (callInit) clazz.getDeclaredMethod("init").invoke(bean);
            registerBean(clazz.getSimpleName(), bean);
            return bean;
        }

        @SuppressWarnings("unchecked")
        <T> T getBean(String name) { return (T) byName.get(name); }
    }

    public static void main(String[] args) throws Exception {
        Ctx ctx = new Ctx();

        System.out.println("=== Container startup ===");
        // Scalar value (like @Value in real Spring)
        ctx.registerScalar(String.class, "Q1 2026 Revenue Report");

        ctx.registerBean("reportRepository", new DatabaseReportRepository("jdbc:postgresql://db:5432/reporting"));
        ctx.registerBean("reportFormatter",  new CsvReportFormatter());
        ReportService svc = ctx.createByConstructorDI(ReportService.class, true);

        System.out.println("\n=== Application running ===");
        String report = svc.generateReport("SELECT * FROM sales WHERE quarter='Q1'");
        System.out.println("  Generated report:\n" + report);

        System.out.println("\n=== Field immutability ===");
        // Cannot do: svc.repository = null; — it's final
        System.out.println("  repository is: " + svc.repository.getClass().getSimpleName());
        System.out.println("  formatter is:  " + svc.formatter.getClass().getSimpleName());
    }
}
```

How to run: `java ConstructorDIDemo3.java`

Three-layer pipeline: `DatabaseReportRepository` → `CsvReportFormatter` → `ReportService`. Constructor takes two interface types plus a `String` scalar. The `init()` method (simulating `@PostConstruct`) runs after construction to validate the injected repository is healthy. All fields are `final`.

## 6. Walkthrough

**Level 3 — startup sequence:**

```
ctx.registerBean("reportRepository", new DatabaseReportRepository("jdbc:..."))
  → byType[ReportRepository.class] = dbRepo
  → byType[DatabaseReportRepository.class] = dbRepo

ctx.registerBean("reportFormatter", new CsvReportFormatter())
  → byType[ReportFormatter.class] = csvFormatter

ctx.registerScalar(String.class, "Q1 2026 Revenue Report")
  → byType[String.class] = "Q1 2026 Revenue Report"

ctx.createByConstructorDI(ReportService.class, callInit=true)
  → ctor = ReportService(ReportRepository, ReportFormatter, String)
  → args[0] = byType[ReportRepository.class] = dbRepo        ✓
  → args[1] = byType[ReportFormatter.class]  = csvFormatter  ✓
  → args[2] = byType[String.class]           = "Q1 2026..."  ✓
  → new ReportService(dbRepo, csvFormatter, "Q1 2026...")
  → svc.init() → dbRepo.isHealthy() = true → OK
```

**`svc.generateReport("...")`:**

```
generateReport("SELECT * FROM sales WHERE quarter='Q1'")
  → repository.fetchRawData("SELECT ...") → [{APAC,420000,1800}, {EMEA,...}, {AMER,...}]
  → formatter.format(rows, "Q1 2026 Revenue Report")
      → "# Q1 2026 Revenue Report\nregion,revenue,orders\n..."
  → return CSV string
```

## 7. Gotchas & takeaways

> **Circular constructor dependencies are detected at startup.** `A(B)` and `B(A)` throw `BeanCurrentlyInCreationException` before any request is served. This is a feature: circular dependencies indicate a design problem that should be restructured, not suppressed.

> **With exactly one constructor, `@Autowired` is not required in Spring 4.3+.** Adding it is harmless but redundant. With multiple constructors, at least one must be annotated.

- `final` fields are the primary benefit of constructor injection: they cannot be null-assigned, swapped, or re-injected after creation.
- Constructor DI supports `@Qualifier`/`@Named` on individual parameters to disambiguate multiple beans of the same type.
- Scalars injected via `@Value("${property}")` count as constructor arguments just like bean references.
- If a constructor dependency is missing, Spring throws `NoSuchBeanDefinitionException` at context startup — fail-fast, not at call-time.
- Constructor injection does NOT support optional dependencies (`@Autowired(required=false)`); use setter injection or `Optional<T>` parameters for optional collaborators.
