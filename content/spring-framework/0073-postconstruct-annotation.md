---
card: spring-framework
gi: 73
slug: postconstruct-annotation
title: "@PostConstruct annotation"
---

## 1. What it is

`@PostConstruct` is a **JSR-250 annotation** (from `jakarta.annotation`) placed on a no-arg method to tell Spring: "call this method after all dependencies have been injected, before the bean becomes available for use." It is the preferred, framework-agnostic init callback in Spring applications.

```java
import jakarta.annotation.PostConstruct;

@Component
public class SearchIndexer {

    @Autowired
    private SearchRepository repository;

    @Value("${search.index.name}")
    private String indexName;

    private long documentCount;

    @PostConstruct
    public void init() {
        // safe to use @Autowired and @Value fields here
        documentCount = repository.count();
        System.out.printf("Index '%s' ready: %d documents indexed%n", indexName, documentCount);
    }
}
```

In one sentence: **`@PostConstruct` marks a method to be called by Spring after all bean dependencies are injected, making it the preferred init hook for application beans — framework-agnostic (JSR-250), fires first among the three init mechanisms.**

## 2. Why & when

Use `@PostConstruct` to:

- **Validate injected configuration** — check `@Value` fields are within valid ranges; throw early if not.
- **Warm a cache** — load hot data into an in-memory map using an injected repository.
- **Establish connections** — open a socket, register with a service registry, subscribe to a topic.
- **Pre-compute derived state** — build an index or sorted structure from injected data that would be wasteful to recompute on every call.

Do NOT do this in the constructor: at constructor time, `@Autowired` fields are not yet set. `@PostConstruct` fires after all injection is complete.

Prefer `@PostConstruct` over `InitializingBean` for application beans — it does not import Spring-specific types.

## 3. Core concept

```
@PostConstruct rules:
  ✓ Method must return void
  ✓ Method must take no arguments
  ✓ Method may throw checked exceptions (wrapped in BeanCreationException)
  ✓ Only ONE @PostConstruct method per class (multiple = unspecified order)
  ✓ Fires after @Autowired injection and after setter injection
  ✓ Fires after @Value fields are resolved
  ✓ Fires before afterPropertiesSet() and before init-method

  Annotation location: requires @Component / @Bean — only Spring-managed beans get called
  On subclass: if Parent defines @PostConstruct and Child extends Parent,
    Parent's @PostConstruct fires too (called in super → child order via reflection)

Order in full lifecycle:
  ① new Bean()
  ② inject @Autowired / @Value / constructor args
  ③ @PostConstruct ← fires HERE
  ④ InitializingBean.afterPropertiesSet()
  ⑤ init-method="..."
  ⑥ bean ready for use
```

## 4. Diagram

<svg viewBox="0 0 680 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="@PostConstruct position and rules">
  <defs>
    <marker id="a73" markerWidth="8" markerHeight="6" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>
  <rect x="5" y="5" width="670" height="188" rx="8" fill="#0d1117" stroke="#8b949e" stroke-width="1.2"/>
  <text x="338" y="22" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">@PostConstruct fires first — after injection, before the other two init mechanisms</text>

  <!-- Step boxes -->
  <rect x="10"  y="35" width="80" height="40" rx="4" fill="#1c2430" stroke="#8b949e"/>
  <text x="50"  y="55" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">① construct</text>
  <text x="50"  y="68" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">new Bean()</text>

  <rect x="105" y="35" width="110" height="40" rx="4" fill="#1c2430" stroke="#8b949e"/>
  <text x="160" y="52" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">② inject</text>
  <text x="160" y="65" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">@Autowired @Value</text>

  <rect x="230" y="35" width="130" height="40" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1.8"/>
  <text x="295" y="52" fill="#6db33f" font-size="8.5" text-anchor="middle" font-family="sans-serif">③ @PostConstruct</text>
  <text x="295" y="65" fill="#6db33f" font-size="7" text-anchor="middle" font-family="sans-serif">← YOU ARE HERE, fires FIRST</text>

  <rect x="375" y="35" width="140" height="40" rx="4" fill="#1c2430" stroke="#8b949e"/>
  <text x="445" y="52" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">④ afterPropertiesSet()</text>
  <text x="445" y="65" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">InitializingBean</text>

  <rect x="530" y="35" width="95" height="40" rx="4" fill="#1c2430" stroke="#8b949e"/>
  <text x="577" y="52" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">⑤ init-method</text>
  <text x="577" y="65" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">XML attr</text>

  <!-- Arrows -->
  <line x1="90"  y1="55" x2="103" y2="55" stroke="#6db33f" stroke-width="1.2" marker-end="url(#a73)"/>
  <line x1="215" y1="55" x2="228" y2="55" stroke="#6db33f" stroke-width="1.2" marker-end="url(#a73)"/>
  <line x1="360" y1="55" x2="373" y2="55" stroke="#6db33f" stroke-width="1.2" marker-end="url(#a73)"/>
  <line x1="515" y1="55" x2="528" y2="55" stroke="#6db33f" stroke-width="1.2" marker-end="url(#a73)"/>

  <!-- Method signature rules -->
  <rect x="10" y="92" width="655" height="92" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="0.8"/>
  <text x="22" y="110" fill="#8b949e" font-size="9" font-family="monospace">@PostConstruct method rules:</text>
  <line x1="12" y1="114" x2="662" y2="114" stroke="#8b949e" stroke-width="0.5"/>
  <text x="22" y="129" fill="#6db33f" font-size="9" font-family="monospace">✓  void myInit()                 — correct</text>
  <text x="22" y="144" fill="#6db33f" font-size="9" font-family="monospace">✓  void init() throws Exception  — checked exception OK</text>
  <text x="22" y="159" fill="#e06c75" font-size="9" font-family="monospace">✗  String init()                 — must return void</text>
  <text x="22" y="174" fill="#e06c75" font-size="9" font-family="monospace">✗  void init(String arg)         — must take no arguments</text>
</svg>

`@PostConstruct` fires immediately after injection — it is the first hook that can safely access `@Autowired` fields and `@Value` properties.

## 5. Runnable example

Scenario: a `ProductCatalog` that loads data from a repository at startup and builds an in-memory search index.

### Level 1 — Basic

`@PostConstruct` loads catalog data after the repository is injected.

```java
// PostConstructDemo.java — run with: java PostConstructDemo.java
import java.util.*;

public class PostConstructDemo {

    // ── simulated @PostConstruct: just a plain annotation marker ─────
    @interface PostConstruct {}

    // ── simulated dependencies ────────────────────────────────────────
    static class ProductRepository {
        List<Map<String, String>> findAll() {
            return List.of(
                Map.of("id", "p1", "name", "Notebook", "category", "stationery"),
                Map.of("id", "p2", "name", "Pen",      "category", "stationery"),
                Map.of("id", "p3", "name", "Backpack",  "category", "bags"),
                Map.of("id", "p4", "name", "Wallet",    "category", "bags")
            );
        }
    }

    static class ProductCatalog {
        // Would be @Autowired in Spring
        private ProductRepository repository;

        // Would be @Value("${catalog.max-size}") in Spring
        private int maxSize;

        // Set by injection (simulating @Autowired / @Value)
        void setRepository(ProductRepository r) { this.repository = r; }
        void setMaxSize(int n)                  { this.maxSize = n;     }

        // @PostConstruct — NOT safe to call in constructor (repository not yet set)
        private final List<Map<String, String>> catalog = new ArrayList<>();

        @PostConstruct
        void init() {
            System.out.println("[PostConstruct] loading catalog — maxSize=" + maxSize);
            List<Map<String, String>> all = repository.findAll();
            catalog.addAll(all.subList(0, Math.min(all.size(), maxSize)));
            System.out.println("[PostConstruct] loaded " + catalog.size() + " products");
        }

        List<Map<String, String>> findByCategory(String cat) {
            return catalog.stream().filter(p -> p.get("category").equals(cat)).toList();
        }
    }

    // ── simulated container ───────────────────────────────────────────
    static ProductCatalog createAndInit() {
        ProductCatalog c = new ProductCatalog();
        c.setRepository(new ProductRepository()); // ② inject
        c.setMaxSize(10);                         // ② inject
        c.init();                                 // ③ @PostConstruct
        return c;
    }

    public static void main(String[] args) {
        ProductCatalog catalog = createAndInit();
        System.out.println();
        System.out.println("[STATIONERY] " + catalog.findByCategory("stationery"));
        System.out.println("[BAGS]       " + catalog.findByCategory("bags"));
    }
}
```

How to run: `java PostConstructDemo.java`

`init()` runs after `setRepository()` and `setMaxSize()` — so `repository.findAll()` and `maxSize` are both available. The catalog is fully populated before `findByCategory()` is ever called.

### Level 2 — Intermediate

`@PostConstruct` for fail-fast config validation and derived state pre-computation.

```java
// PostConstructDemo2.java — run with: java PostConstructDemo2.java
import java.util.*;
import java.util.regex.*;

public class PostConstructDemo2 {

    @interface PostConstruct {}

    static class EmailRouter {
        // injected config
        private String smtpHost;
        private int    smtpPort;
        private String fromDomain;
        private List<String> allowedDomains;

        void setSmtpHost(String v)           { this.smtpHost       = v; }
        void setSmtpPort(int v)              { this.smtpPort        = v; }
        void setFromDomain(String v)         { this.fromDomain      = v; }
        void setAllowedDomains(List<String> v) { this.allowedDomains = v; }

        // derived state — built in @PostConstruct
        private Set<String>     allowedSet;
        private String          senderAddress;
        private static final Pattern DOMAIN_PATTERN =
            Pattern.compile("^[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$");

        @PostConstruct
        void init() {
            System.out.println("[PostConstruct] validating EmailRouter...");

            // Validate
            if (smtpHost == null || smtpHost.isBlank())
                throw new IllegalStateException("smtpHost required");
            if (smtpPort < 1 || smtpPort > 65535)
                throw new IllegalStateException("smtpPort out of range: " + smtpPort);
            if (!DOMAIN_PATTERN.matcher(fromDomain).matches())
                throw new IllegalStateException("invalid fromDomain: " + fromDomain);
            if (allowedDomains == null || allowedDomains.isEmpty())
                throw new IllegalStateException("allowedDomains must not be empty");
            for (String d : allowedDomains)
                if (!DOMAIN_PATTERN.matcher(d).matches())
                    throw new IllegalStateException("invalid allowed domain: " + d);

            // Pre-compute derived state
            allowedSet     = new HashSet<>(allowedDomains);
            senderAddress  = "noreply@" + fromDomain;

            System.out.printf("[PostConstruct] OK — smtp=%s:%d from=%s allowed=%s%n",
                smtpHost, smtpPort, senderAddress, allowedSet);
        }

        String send(String to, String subject) {
            String domain = to.contains("@") ? to.substring(to.indexOf('@') + 1) : "";
            if (!allowedSet.contains(domain))
                return "REJECTED — domain '" + domain + "' not in allowlist";
            return String.format("SENT from=%s to=%s subject='%s' via %s:%d",
                senderAddress, to, subject, smtpHost, smtpPort);
        }
    }

    static EmailRouter createValid() {
        EmailRouter r = new EmailRouter();
        r.setSmtpHost("smtp.company.com");
        r.setSmtpPort(587);
        r.setFromDomain("company.com");
        r.setAllowedDomains(List.of("company.com", "partner.org", "client.io"));
        r.init();
        return r;
    }

    public static void main(String[] args) {
        System.out.println("=== Valid config ===");
        EmailRouter router = createValid();
        System.out.println("[SEND] " + router.send("alice@company.com",   "Welcome"));
        System.out.println("[SEND] " + router.send("bob@partner.org",     "Invoice"));
        System.out.println("[SEND] " + router.send("eve@external.net",    "Spam?"));

        System.out.println("\n=== Invalid SMTP port ===");
        try {
            EmailRouter bad = new EmailRouter();
            bad.setSmtpHost("smtp.company.com");
            bad.setSmtpPort(0);               // invalid
            bad.setFromDomain("company.com");
            bad.setAllowedDomains(List.of("company.com"));
            bad.init();
        } catch (IllegalStateException e) { System.out.println("[FAIL — expected] " + e.getMessage()); }

        System.out.println("\n=== Invalid fromDomain ===");
        try {
            EmailRouter bad = new EmailRouter();
            bad.setSmtpHost("smtp.company.com");
            bad.setSmtpPort(587);
            bad.setFromDomain("not a domain!");  // invalid
            bad.setAllowedDomains(List.of("company.com"));
            bad.init();
        } catch (IllegalStateException e) { System.out.println("[FAIL — expected] " + e.getMessage()); }
    }
}
```

How to run: `java PostConstructDemo2.java`

`init()` validates four independent fields and then pre-computes `allowedSet` (a `HashSet` for O(1) lookups) and `senderAddress` (a computed string). Both derived fields are available immediately when `send()` is first called. Bad config throws at startup, not at first `send()`.

### Level 3 — Advanced

`@PostConstruct` on a bean with inheritance: parent and child both have `@PostConstruct` — both fire (parent first, child second).

```java
// PostConstructDemo3.java — run with: java PostConstructDemo3.java
import java.util.*;
import java.util.concurrent.*;
import java.util.function.*;

public class PostConstructDemo3 {

    @interface PostConstruct {}
    @interface Autowired    {}

    static final List<String> INIT_LOG = new ArrayList<>();

    // ── base bean with its own @PostConstruct ─────────────────────────
    static abstract class BaseMetricsBean {
        protected String serviceName;
        protected final Map<String, Long> counters = new ConcurrentHashMap<>();

        void setServiceName(String n) { this.serviceName = n; }

        // ── parent @PostConstruct ─────────────────────────────────────
        @PostConstruct
        void baseInit() {
            System.out.println("  [BaseMetricsBean.@PostConstruct] registering counters for " + serviceName);
            counters.put("requests",  0L);
            counters.put("errors",    0L);
            counters.put("latency_ms", 0L);
            INIT_LOG.add("BaseMetricsBean.baseInit");
        }

        void increment(String counter) { counters.merge(counter, 1L, Long::sum); }
        Map<String, Long> snapshot()   { return Collections.unmodifiableMap(counters); }
    }

    // ── child bean with its own @PostConstruct ────────────────────────
    static class PaymentService extends BaseMetricsBean {
        private String gatewayUrl;
        private int    timeoutMs;
        private List<String> supportedCurrencies;

        void setGatewayUrl(String v)               { this.gatewayUrl          = v; }
        void setTimeoutMs(int v)                   { this.timeoutMs            = v; }
        void setSupportedCurrencies(List<String> v){ this.supportedCurrencies  = v; }

        private Set<String> currencySet;

        // ── child @PostConstruct (fires AFTER parent's) ───────────────
        @PostConstruct
        void serviceInit() {
            System.out.printf("  [PaymentService.@PostConstruct] gateway=%s timeout=%dms currencies=%s%n",
                gatewayUrl, timeoutMs, supportedCurrencies);

            // validate
            if (gatewayUrl == null || !gatewayUrl.startsWith("https://"))
                throw new IllegalStateException("gatewayUrl must start with https://: " + gatewayUrl);
            if (timeoutMs < 100 || timeoutMs > 30_000)
                throw new IllegalStateException("timeoutMs out of range [100,30000]: " + timeoutMs);
            if (supportedCurrencies == null || supportedCurrencies.isEmpty())
                throw new IllegalStateException("supportedCurrencies must not be empty");

            // build derived state — safe, base counters already set by parent's @PostConstruct
            currencySet = new HashSet<>(supportedCurrencies);
            counters.put("declined", 0L); // add payment-specific counter on top of base counters

            System.out.println("  [PaymentService.@PostConstruct] currencySet=" + currencySet);
            INIT_LOG.add("PaymentService.serviceInit");
        }

        String charge(String currency, double amount) {
            increment("requests");
            if (!currencySet.contains(currency)) {
                increment("errors");
                return "DECLINED — unsupported currency: " + currency;
            }
            increment("latency_ms"); // simplification
            return String.format("CHARGED %.2f %s via %s", amount, currency, gatewayUrl);
        }
    }

    // ── simulated container: calls @PostConstruct methods in declaration order ─
    static PaymentService createBean() throws Exception {
        PaymentService svc = new PaymentService();
        // inject
        svc.setServiceName("payment-service");
        svc.setGatewayUrl("https://payments.example.com/v1/charge");
        svc.setTimeoutMs(5000);
        svc.setSupportedCurrencies(List.of("USD", "EUR", "GBP", "JPY"));

        // Spring calls @PostConstruct methods via reflection — superclass first
        svc.baseInit();    // parent @PostConstruct (Spring fires this first)
        svc.serviceInit(); // child @PostConstruct (Spring fires this second)
        return svc;
    }

    public static void main(String[] args) throws Exception {
        System.out.println("=== Creating PaymentService ===");
        PaymentService svc = createBean();
        System.out.println("[INIT LOG] " + INIT_LOG);

        System.out.println("\n=== Processing payments ===");
        System.out.println("[CHARGE] " + svc.charge("USD", 99.99));
        System.out.println("[CHARGE] " + svc.charge("EUR", 49.00));
        System.out.println("[CHARGE] " + svc.charge("BTC", 0.001));  // unsupported
        System.out.println("[CHARGE] " + svc.charge("GBP", 29.50));

        System.out.println("\n[METRICS] " + svc.snapshot());
    }
}
```

How to run: `java PostConstructDemo3.java`

When a class extends a class that has `@PostConstruct`, Spring fires the parent's `@PostConstruct` first (`baseInit()` registers base counters), then the child's (`serviceInit()` adds payment-specific counters on top). The child's `@PostConstruct` can safely use state set by the parent's. The `INIT_LOG` confirms the order.

## 6. Walkthrough

**Level 3 init sequence in detail:**

```
new PaymentService()                     ← ① constructor

// ② inject (all four setters called by Spring)
svc.setServiceName("payment-service")
svc.setGatewayUrl("https://payments.example.com/v1/charge")
svc.setTimeoutMs(5000)
svc.setSupportedCurrencies([USD,EUR,GBP,JPY])

// ③ @PostConstruct — parent first, child second (Spring uses reflection hierarchy)
svc.baseInit()                           ← BaseMetricsBean.@PostConstruct
  counters = {requests:0, errors:0, latency_ms:0}
  INIT_LOG = ["BaseMetricsBean.baseInit"]

svc.serviceInit()                        ← PaymentService.@PostConstruct
  validates gatewayUrl, timeoutMs, supportedCurrencies
  currencySet = {USD, EUR, GBP, JPY}
  counters.put("declined", 0L)  ← extends base counters ✓
  INIT_LOG = ["BaseMetricsBean.baseInit", "PaymentService.serviceInit"]

// Bean ready
svc.charge("BTC", 0.001)
  → increment("requests")
  → "BTC" not in currencySet → increment("errors") → DECLINED

[METRICS] {requests=4, errors=1, latency_ms=3, declined=0}
```

## 7. Gotchas & takeaways

> **`@PostConstruct` is NOT called if the bean fails to be created (e.g., constructor throws).** The method only fires after a fully constructed, dependency-injected bean — if injection itself fails, `@PostConstruct` never runs.

> **Inheritance: parent `@PostConstruct` fires before child `@PostConstruct`.** Spring discovers `@PostConstruct` via reflection and respects class hierarchy order. If you override the parent's `@PostConstruct` method in a subclass, only the overriding version is called — so don't override it unless you call `super.init()` explicitly.

- The method must be `void` and take no arguments. Spring will throw `IllegalStateException` at startup if the signature is wrong.
- Spring calls at most one `@PostConstruct` method per bean class in the hierarchy (but one per level). Multiple `@PostConstruct` annotations on the same class (different methods) — behaviour is unspecified; avoid it.
- `@PostConstruct` is defined in `jakarta.annotation-api` (Jakarta EE 9+) or `javax.annotation-api` (Jakarta EE 8 / Java EE). For Spring Boot 3+, use `jakarta.annotation.PostConstruct`.
- `@PostConstruct` fires even for `@Configuration` class beans and `@Bean` factory methods on the same class — you can use it to validate `@Configuration` properties.
- Unlike `ApplicationListener<ContextRefreshedEvent>`, `@PostConstruct` fires **before** the full context is refreshed — not all sibling beans are necessarily initialised when your `@PostConstruct` runs. Use `SmartLifecycle.start()` or `ApplicationListener<ContextRefreshedEvent>` for "all beans ready" hooks.
