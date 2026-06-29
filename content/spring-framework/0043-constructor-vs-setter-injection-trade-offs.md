---
card: spring-framework
gi: 43
slug: constructor-vs-setter-injection-trade-offs
title: Constructor vs setter injection trade-offs
---

## 1. What it is

**Constructor vs setter injection trade-offs** is a design decision that affects immutability, testability, startup-time failure detection, and how circular dependencies are handled.

Spring supports both. The Spring team recommends:

- **Use constructor injection** for mandatory dependencies.
- **Use setter injection** for optional dependencies.

```java
// Constructor: mandatory, immutable
@Component
public class OrderService {
    private final PaymentGateway gateway;  // final — immutable
    public OrderService(PaymentGateway gateway) {
        this.gateway = Objects.requireNonNull(gateway);
    }
}

// Setter: optional, mutable
@Component
public class ReportService {
    private PdfRenderer renderer;   // optional — null if not available

    @Autowired(required = false)
    public void setRenderer(PdfRenderer renderer) {
        this.renderer = renderer;
    }
}
```

In one sentence: **Constructor injection gives you immutability and fail-fast startup at the cost of circular-dependency flexibility; setter injection gives you optionality and runtime replaceability at the cost of the window between construction and full initialization.**

## 2. Why & when

| Property | Constructor | Setter |
|---|---|---|
| Mandatory deps | Best — startup fails if missing | Possible, but NullPointerException at call-time |
| Optional deps | Awkward — requires `Optional<T>` param | Natural — `required=false`, field stays null |
| Immutability | `final` fields possible | Fields cannot be `final` |
| Testability | Pass mocks directly, no reflection | Need either Spring or reflection to call setter |
| Circular deps | Impossible at startup | Resolves: create both empty, then cross-inject |
| Runtime swap | Impossible | Possible — call setter again |

## 3. Core concept

```
Constructor injection sequence (3 steps merged into 1):
  new OrderService(gateway)
  → field set in constructor body
  → object is complete by the time constructor returns
  → no intermediate state

Setter injection sequence (3 distinct steps):
  new ReportService()        ← step 1: empty object
  setDataLoader(loader)      ← step 2: partially wired
  setRenderer(renderer)      ← step 3: fully wired
  → window between steps 1 and 3 where object is incomplete

Circular dependency:
  A requires B via constructor → Spring must create B first
  B requires A via constructor → Spring must create A first
  → BeanCurrentlyInCreationException

  A requires B via setter      → Spring creates A (empty), B (injecting A), sets B on A
  → works ✓
```

## 4. Diagram

<svg viewBox="0 0 680 205" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Constructor DI: one atomic step, final fields, no window. Setter DI: three steps, non-final, incomplete window exists.">
  <defs>
    <marker id="a43" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="b43" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
    <marker id="c43" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#e06c75"/></marker>
  </defs>

  <!-- Left: Constructor DI timeline -->
  <text x="165" y="20" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">Constructor DI</text>
  <rect x="10" y="30" width="310" height="60" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="165" y="54" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">new OrderService(gateway)</text>
  <text x="165" y="72" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">final field set inside constructor ← one atomic step</text>
  <text x="165" y="108" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">Object fully initialized ✓</text>

  <!-- Right: Setter DI timeline -->
  <text x="510" y="20" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">Setter DI</text>
  <rect x="360" y="30" width="310" height="38" rx="5" fill="#1c2430" stroke="#e06c75" stroke-width="1.5"/>
  <text x="515" y="53" fill="#e06c75" font-size="9" text-anchor="middle" font-family="sans-serif">new ReportService() — fields null</text>

  <rect x="360" y="78" width="310" height="38" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="515" y="101" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">setDataLoader(loader) — partially wired</text>

  <rect x="360" y="126" width="310" height="38" rx="5" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="515" y="149" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">setRenderer(renderer) — fully wired ✓</text>

  <line x1="515" y1="68"  x2="515" y2="75"  stroke="#8b949e" stroke-width="1.5" marker-end="url(#b43)"/>
  <line x1="515" y1="116" x2="515" y2="123" stroke="#8b949e" stroke-width="1.5" marker-end="url(#b43)"/>

  <!-- Incomplete window label -->
  <rect x="362" y="64" width="106" height="62" rx="3" fill="none" stroke="#e06c75" stroke-width="1" stroke-dasharray="3,2"/>
  <text x="415" y="172" fill="#e06c75" font-size="8" text-anchor="middle" font-family="sans-serif">← incomplete window</text>
</svg>

Constructor DI: one atomic step, `final` fields, object is complete at the end of the constructor. Setter DI: three steps with an incomplete window where the object exists but its dependencies are null.

## 5. Runnable example

Scenario: a `PaymentService` that MUST have a `FraudDetector` (mandatory → constructor) and MAY have an `AuditLogger` (optional → setter). Contrast both approaches.

### Level 1 — Basic

Constructor for mandatory + setter for optional in the same class.

```java
// CtorSetterTradeOffDemo.java — run with: java CtorSetterTradeOffDemo.java
import java.util.*;

public class CtorSetterTradeOffDemo {

    interface FraudDetector {
        boolean isFraudulent(String cardNumber, double amount);
    }

    static class RuleBasedFraudDetector implements FraudDetector {
        RuleBasedFraudDetector() { System.out.println("  [BEAN] RuleBasedFraudDetector created"); }
        @Override public boolean isFraudulent(String card, double amount) {
            boolean fraud = amount > 9999 || card.startsWith("STOLEN");
            System.out.printf("  [FRAUD] %s $%.2f → %s%n", card.substring(0,8)+"...", amount, fraud ? "FLAGGED" : "ok");
            return fraud;
        }
    }

    interface AuditLogger {
        void log(String event, String details);
    }

    static class FileAuditLogger implements AuditLogger {
        FileAuditLogger() { System.out.println("  [BEAN] FileAuditLogger created"); }
        @Override public void log(String event, String details) {
            System.out.printf("  [AUDIT] %s | %s%n", event, details);
        }
    }

    static class PaymentService {
        // Constructor-injected: MANDATORY — final, non-null guaranteed
        private final FraudDetector fraudDetector;

        // Setter-injected: OPTIONAL — may be null
        private AuditLogger auditLogger;

        PaymentService(FraudDetector fraudDetector) {
            this.fraudDetector = Objects.requireNonNull(fraudDetector, "FraudDetector is required");
            System.out.println("  [BEAN] PaymentService(FraudDetector) — constructor DI");
        }

        // Setter — optional; @Autowired(required=false) in Spring
        void setAuditLogger(AuditLogger auditLogger) {
            System.out.println("  [SETTER] setAuditLogger → " + auditLogger.getClass().getSimpleName());
            this.auditLogger = auditLogger;
        }

        String pay(String card, double amount) {
            if (fraudDetector.isFraudulent(card, amount)) {
                if (auditLogger != null)
                    auditLogger.log("PAYMENT_BLOCKED", "card=" + card.substring(0,8) + " amt=" + amount);
                return "BLOCKED";
            }
            if (auditLogger != null)
                auditLogger.log("PAYMENT_OK", "card=" + card.substring(0,8) + " amt=" + amount);
            return "APPROVED";
        }
    }

    public static void main(String[] args) {
        System.out.println("=== Wiring: constructor (mandatory) + setter (optional) ===");
        FraudDetector fraud = new RuleBasedFraudDetector();
        AuditLogger   audit = new FileAuditLogger();

        PaymentService svc = new PaymentService(fraud);   // mandatory
        svc.setAuditLogger(audit);                         // optional

        System.out.println("\n=== Payments ===");
        System.out.println("  " + svc.pay("4242424242424242", 99.00));
        System.out.println("  " + svc.pay("STOLEN-1234-5678", 200.00));
        System.out.println("  " + svc.pay("4111111111111111", 15_000.00));

        System.out.println("\n=== Same service without audit logger ===");
        PaymentService svc2 = new PaymentService(fraud);  // no setAuditLogger call
        System.out.println("  " + svc2.pay("4242424242424242", 50.00));  // no audit output
        System.out.println("  auditLogger is null: " + (svc2.auditLogger == null));
    }
}
```

How to run: `java CtorSetterTradeOffDemo.java`

`FraudDetector` is required — `Objects.requireNonNull` in the constructor throws immediately if it is null. `AuditLogger` is optional — `svc2` has no audit logger set and silently skips logging. Both cases work at runtime; the difference is the error detection time.

### Level 2 — Intermediate

Fail-fast comparison: constructor DI fails at startup vs setter DI fails at call-time.

```java
// CtorSetterTradeOffDemo2.java — run with: java CtorSetterTradeOffDemo2.java

public class CtorSetterTradeOffDemo2 {

    interface SearchEngine {
        String search(String query);
    }

    static class ElasticSearchEngine implements SearchEngine {
        @Override public String search(String q) { return "ELASTIC:" + q; }
    }

    // Constructor DI — missing dep fails at creation time
    static class SearchServiceCtor {
        private final SearchEngine engine;
        SearchServiceCtor(SearchEngine engine) {
            this.engine = Objects.requireNonNull(engine, "SearchEngine required");
            System.out.println("  [BEAN] SearchServiceCtor ready — engine injected");
        }
        String search(String q) { return engine.search(q); }
    }

    // Setter DI — missing dep fails at call time (NPE)
    static class SearchServiceSetter {
        private SearchEngine engine;
        SearchServiceSetter() { System.out.println("  [BEAN] SearchServiceSetter created — engine not yet set"); }
        void setEngine(SearchEngine engine) {
            System.out.println("  [SETTER] setEngine → " + engine.getClass().getSimpleName());
            this.engine = engine;
        }
        String search(String q) {
            if (engine == null) throw new IllegalStateException("SearchEngine not injected!");
            return engine.search(q);
        }
    }

    static void tryCreate(String label, Runnable action) {
        try {
            action.run();
            System.out.println("  [" + label + "] created successfully");
        } catch (Exception e) {
            System.out.println("  [" + label + "] FAILED at creation: " + e.getMessage());
        }
    }

    static void trySearch(String label, Object svc) {
        try {
            String result = svc instanceof SearchServiceCtor c ? c.search("spring beans")
                          : ((SearchServiceSetter) svc).search("spring beans");
            System.out.println("  [" + label + "] search result: " + result);
        } catch (Exception e) {
            System.out.println("  [" + label + "] FAILED at call-time: " + e.getMessage());
        }
    }

    public static void main(String[] args) {
        System.out.println("=== Fail-fast comparison ===");

        System.out.println("\n-- Constructor DI: missing dep --");
        tryCreate("ctor-missing",  () -> new SearchServiceCtor(null));

        System.out.println("\n-- Setter DI: missing dep --");
        SearchServiceSetter svcSetter = new SearchServiceSetter();
        tryCreate("setter-missing", () -> { /* no setEngine call */ });
        System.out.println("  [setter-missing] bean created OK — dep not set yet");
        trySearch("setter-missing", svcSetter);  // fails here

        System.out.println("\n-- Constructor DI: dep present --");
        tryCreate("ctor-ok", () -> new SearchServiceCtor(new ElasticSearchEngine()));
        trySearch("ctor-ok", new SearchServiceCtor(new ElasticSearchEngine()));

        System.out.println("\n-- Setter DI: dep present --");
        SearchServiceSetter svc2 = new SearchServiceSetter();
        svc2.setEngine(new ElasticSearchEngine());
        trySearch("setter-ok", svc2);
    }
}
```

How to run: `java CtorSetterTradeOffDemo2.java`

Constructor DI with `null` throws `NullPointerException` during bean creation — container startup fails immediately. Setter DI with no setter call creates the bean without error, then throws `IllegalStateException` at the first call to `search()`. Constructor DI detects the problem earlier.

### Level 3 — Advanced

A complete service graph showing the right choice for each dependency: constructor for required, setter for optional, plus a configuration scenario where setter-injected config can be changed post-construction.

```java
// CtorSetterTradeOffDemo3.java — run with: java CtorSetterTradeOffDemo3.java
import java.util.*;

public class CtorSetterTradeOffDemo3 {

    // --- Collaborators ---

    interface ProductCatalog {
        Optional<Map<String, Object>> findProduct(String id);
    }

    interface PricingStrategy {
        double applyDiscount(double basePrice, String customer);
    }

    interface RecommendationEngine {
        List<String> recommend(String productId, int limit);
    }

    static class InMemoryCatalog implements ProductCatalog {
        private final Map<String, Map<String, Object>> db = new HashMap<>();
        InMemoryCatalog() {
            db.put("P1", Map.of("name", "Laptop",  "price", 999.0));
            db.put("P2", Map.of("name", "Monitor", "price", 449.0));
            db.put("P3", Map.of("name", "Keyboard","price",  79.0));
            System.out.println("  [BEAN] InMemoryCatalog created");
        }
        @Override public Optional<Map<String, Object>> findProduct(String id) {
            return Optional.ofNullable(db.get(id));
        }
    }

    static class StandardPricing implements PricingStrategy {
        StandardPricing() { System.out.println("  [BEAN] StandardPricing created"); }
        @Override public double applyDiscount(double base, String customer) { return base; }
    }

    static class VipPricing implements PricingStrategy {
        VipPricing() { System.out.println("  [BEAN] VipPricing created"); }
        @Override public double applyDiscount(double base, String customer) {
            return base * 0.85;   // 15% VIP discount
        }
    }

    static class CollaboRecommender implements RecommendationEngine {
        CollaboRecommender() { System.out.println("  [BEAN] CollaboRecommender created"); }
        @Override public List<String> recommend(String id, int limit) {
            return switch (id) {
                case "P1" -> List.of("P3", "P2").subList(0, Math.min(limit, 2));
                default   -> List.of();
            };
        }
    }

    // --- Main service ---
    static class ProductService {
        // MANDATORY: constructor injection
        private final ProductCatalog   catalog;
        private final PricingStrategy  pricing;

        // OPTIONAL: setter injection — may be null
        private RecommendationEngine recommender;

        ProductService(ProductCatalog catalog, PricingStrategy pricing) {
            this.catalog = Objects.requireNonNull(catalog);
            this.pricing = Objects.requireNonNull(pricing);
            System.out.println("  [BEAN] ProductService(catalog, pricing) — constructor DI");
        }

        // Optional — @Autowired(required=false)
        void setRecommender(RecommendationEngine recommender) {
            System.out.println("  [SETTER] setRecommender → " + recommender.getClass().getSimpleName());
            this.recommender = recommender;
        }

        // Setter allows runtime swap of pricing strategy (e.g. from standard to VIP)
        void setPricingStrategy(PricingStrategy pricing) {
            System.out.println("  [SETTER] setPricingStrategy → " + pricing.getClass().getSimpleName());
        }

        Map<String, Object> getProductPage(String productId, String customer) {
            Map<String, Object> page = new LinkedHashMap<>();
            var product = catalog.findProduct(productId);
            if (product.isEmpty()) { page.put("error", "product not found"); return page; }

            double base  = (double) product.get().get("price");
            double price = pricing.applyDiscount(base, customer);

            page.put("name",  product.get().get("name"));
            page.put("price", String.format("%.2f", price));
            page.put("discount", price < base ? String.format("%.0f%%", (1 - price/base)*100) : "none");

            if (recommender != null) {
                page.put("recommendations", recommender.recommend(productId, 2));
            }
            return page;
        }
    }

    public static void main(String[] args) {
        System.out.println("=== Wiring strategy ===");
        InMemoryCatalog catalog   = new InMemoryCatalog();
        StandardPricing std       = new StandardPricing();
        VipPricing      vip       = new VipPricing();
        CollaboRecommender recs   = new CollaboRecommender();

        // Construction: catalog + pricing are mandatory → constructor
        ProductService svc = new ProductService(catalog, std);
        // Recommender is optional → setter
        svc.setRecommender(recs);

        System.out.println("\n=== Standard customer ===");
        System.out.println("  " + svc.getProductPage("P1", "standard-customer"));

        System.out.println("\n=== VIP customer (swap pricing via setter) ===");
        // Without re-construction, swap pricing strategy at runtime
        ProductService vipSvc = new ProductService(catalog, vip);
        vipSvc.setRecommender(recs);
        System.out.println("  " + vipSvc.getProductPage("P1", "vip-alice"));

        System.out.println("\n=== No recommender (minimal service) ===");
        ProductService bare = new ProductService(catalog, std);  // no setRecommender call
        Map<String, Object> page = bare.getProductPage("P2", "any");
        System.out.println("  " + page);
        System.out.println("  recommendations key present: " + page.containsKey("recommendations"));
    }
}
```

How to run: `java CtorSetterTradeOffDemo3.java`

`catalog` and `pricing` are constructor-injected (mandatory). `recommender` is setter-injected (optional). `bare` works correctly without a recommender — the page is built without the recommendations section. Two `ProductService` instances use different `PricingStrategy` implementations without duplicating other wiring.

## 6. Walkthrough

**Constructor vs setter decision tree per dependency:**

```
Is the dependency required for the bean to function at all?
  YES → constructor injection
    → field can be final
    → null detected at startup
    → no incomplete window

Is the dependency optional, or can be null?
  YES → setter injection with @Autowired(required=false)
    → field cannot be final
    → bean works with field null
    → null detected at call time (guard with Objects.requireNonNull in @PostConstruct if needed)

Is there a circular dependency between two beans?
  YES → at least one must use setter injection
    → Spring creates both beans first, then cross-injects via setters

Should the dependency be swappable at runtime?
  YES → setter injection
    → call setter again to replace the collaborator
```

## 7. Gotchas & takeaways

> **Spring 4.3+: if a class has exactly one constructor, `@Autowired` is optional and the container uses constructor injection automatically.** This makes constructor injection the default for most `@Component` beans.

> **Constructor injection cannot resolve circular dependencies.** `BeanCurrentlyInCreationException` is thrown at startup. Setter injection is the escape hatch — use it consciously, and treat circular dependencies as a design smell to fix when possible.

- Use `@PostConstruct` to validate optional setter-injected fields that are actually required in some deployments — this gives early failure with a clear message rather than a null-dereference buried in a stack trace.
- In tests, constructor injection is superior: `new OrderService(mockGateway)` passes a mock directly. Setter injection requires calling the setter explicitly or using `ReflectionTestUtils.setField()`.
- Both strategies are fully supported in Spring. The Spring documentation recommends constructor injection as the default, setter injection as the exception.
- Field injection (`@Autowired` directly on a field) is discussed in the next tutorial — it bypasses both constructors and setters entirely.
