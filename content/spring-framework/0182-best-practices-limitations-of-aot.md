---
card: spring-framework
gi: 182
slug: best-practices-limitations-of-aot
title: "Best practices & limitations of AOT"
---

## 1. What it is

AOT processing is powerful but imposes constraints that don't exist in traditional JVM Spring applications. Understanding these limitations prevents runtime surprises in native images and avoids wasted CI build time.

**Core limitations:**

1. **Closed-world assumption** — `native-image` only includes code reachable from `main()` at build time. `Class.forName(str)` where `str` is determined at runtime, dynamic plugin loading, and scripted bytecode generation (e.g., Groovy closures in `@Configuration`) can fail silently.
2. **Static `@Conditional` evaluation** — conditions are evaluated once at `process-aot` time against the build environment; they cannot change at runtime.
3. **CGLIB proxies replaced by generated subclasses** — Spring AOT generates proxy source code instead of using CGLIB at runtime. Most code is unaffected, but edge cases (casting to a CGLIB-specific type, relying on CGLIB method interceptor ordering) may behave differently.
4. **Limited runtime reflection** — reflection still works in native images when hints are registered, but unregistered reflection fails with `ClassNotFoundException` or `NoSuchMethodException` at runtime, not at build time.
5. **Build time** — `native-image` compilation takes 2–10 minutes; CI pipelines must account for this.

## 2. Why & when

- **Know the limitations before adopting**: evaluate whether your codebase uses heavy dynamic class loading, Groovy/Kotlin-DSL configurations, or third-party libraries without native support.
- **Test early and often**: run `./mvnw -Pnative native:test` in CI from the beginning of native adoption; AOT hint gaps are much cheaper to fix early.
- **Invest in `RuntimeHintsPredicates` tests**: these run in JVM mode (seconds) and catch many native issues without the 10-minute native build.
- **Profile-based deployments**: use the JVM JAR for development/debugging and the native binary for production — both are built from the same source with different Maven profiles.

## 3. Core concept

**What AOT handles automatically:**
- Standard `@Component`, `@Service`, `@Repository`, `@RestController` beans.
- Constructor, setter, and field injection for standard types.
- `@Value` injection for `String`, primitives, `List<String>`.
- Jackson serialisation for types annotated with `@RegisterReflectionForBinding`.
- Spring Security, Spring Data JPA (with their own AOT processors).
- Resources in `src/main/resources`.

**What requires manual hints:**
- `Class.forName(String)` where the name is not a literal.
- `Method.invoke` / `Constructor.newInstance` on arbitrary types.
- JDK dynamic proxies (`Proxy.newProxyInstance`).
- Resources loaded via `getResourceAsStream` from paths computed at runtime.
- Java serialization (`ObjectOutputStream`) for domain objects.
- Third-party libraries that use reflection internally without `RuntimeHintsRegistrar`.

**Best practices summary:**

| Practice | Why |
|---|---|
| `@RegisterReflectionForBinding` on all API DTOs | prevents Jackson binding failures in native |
| `RuntimeHintsRegistrar` for each `Class.forName` usage | explicit is better than discovering the gap in prod |
| `./mvnw -Pnative native:test` in CI | catches hint gaps early (not in prod) |
| `RuntimeHintsPredicates` unit tests | JVM-speed hint verification |
| Constructor injection everywhere | AOT generates supplier directly; field injection needs extra hints |
| No `@ConditionalOnProperty` beans with runtime-only properties | conditions are build-time; prod properties must match AOT-time |
| Keep `@Configuration` classes simple | complex DSL / Groovy closures may not be AOT-compatible |

## 4. Diagram

<svg viewBox="0 0 700 200" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <marker id="bpa" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="bpb" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#e74c3c"/></marker>
  </defs>

  <!-- AOT-safe zone -->
  <rect x="5" y="5" width="320" height="190" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="162" y="24" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif" font-weight="bold">AOT-safe (automatic)</text>

  <text x="20" y="43" fill="#e6edf3" font-size="8" font-family="sans-serif">✓ @Component / @Service / @Repository beans</text>
  <text x="20" y="57" fill="#e6edf3" font-size="8" font-family="sans-serif">✓ Constructor injection</text>
  <text x="20" y="71" fill="#e6edf3" font-size="8" font-family="sans-serif">✓ @Value with String / primitive types</text>
  <text x="20" y="85" fill="#e6edf3" font-size="8" font-family="sans-serif">✓ @RegisterReflectionForBinding DTOs</text>
  <text x="20" y="99" fill="#e6edf3" font-size="8" font-family="sans-serif">✓ Spring AOP @Transactional / @Cacheable</text>
  <text x="20" y="113" fill="#e6edf3" font-size="8" font-family="sans-serif">✓ Spring MVC @RestController / @RequestMapping</text>
  <text x="20" y="127" fill="#e6edf3" font-size="8" font-family="sans-serif">✓ Spring Data repositories (JPA, MongoDB …)</text>
  <text x="20" y="141" fill="#e6edf3" font-size="8" font-family="sans-serif">✓ src/main/resources files</text>
  <text x="20" y="155" fill="#e6edf3" font-size="8" font-family="sans-serif">✓ Autoconfiguration conditions with static properties</text>

  <!-- Needs hints zone -->
  <rect x="340" y="5" width="355" height="190" rx="8" fill="#1c2430" stroke="#e74c3c" stroke-width="2"/>
  <text x="517" y="24" fill="#e74c3c" font-size="11" text-anchor="middle" font-family="sans-serif" font-weight="bold">Needs manual hints</text>

  <text x="355" y="43" fill="#e6edf3" font-size="8" font-family="sans-serif">✗ Class.forName(runtimeString)</text>
  <text x="355" y="57" fill="#e6edf3" font-size="8" font-family="sans-serif">✗ Constructor.newInstance() on dynamic types</text>
  <text x="355" y="71" fill="#e6edf3" font-size="8" font-family="sans-serif">✗ JDK Proxy.newProxyInstance with runtime interfaces</text>
  <text x="355" y="85" fill="#e6edf3" font-size="8" font-family="sans-serif">✗ ObjectOutputStream for domain objects</text>
  <text x="355" y="99" fill="#e6edf3" font-size="8" font-family="sans-serif">✗ ClassLoader.getResourceAsStream(dynamic path)</text>
  <text x="355" y="113" fill="#e6edf3" font-size="8" font-family="sans-serif">✗ Groovy / Kotlin DSL @Configuration</text>
  <text x="355" y="127" fill="#e6edf3" font-size="8" font-family="sans-serif">✗ Field injection in legacy code (weaker hints)</text>
  <text x="355" y="141" fill="#e6edf3" font-size="8" font-family="sans-serif">✗ @ConditionalOnProperty with runtime-only value</text>
  <text x="355" y="155" fill="#e6edf3" font-size="8" font-family="sans-serif">✗ Third-party libs without RuntimeHintsRegistrar</text>
  <text x="355" y="169" fill="#8b949e" font-size="8" font-family="sans-serif">→ add RuntimeHintsRegistrar or check spring.io/native</text>
</svg>

Standard Spring patterns are handled automatically by AOT; any dynamic runtime feature requires explicit hints or an alternative approach.

## 5. Runnable example

The scenario is an **order processing pipeline** that starts with bad AOT patterns and progressively fixes them — the same service evolving from AOT-unsafe to fully native-ready.

### Level 1 — Basic

An AOT-unsafe pattern and its safe replacement: `Class.forName` vs explicit supplier.

```java
// AotBestPracticesBasic.java
import org.springframework.aot.hint.*;
import java.lang.reflect.*;

interface Processor { String process(String input); }
class OrderProcessor   implements Processor { public String process(String i) { return "ORDER:" + i; } }
class InvoiceProcessor implements Processor { public String process(String i) { return "INVOICE:" + i; } }

public class AotBestPracticesBasic {

    // --- UNSAFE: dynamic Class.forName — needs reflection hint in native ---
    static Processor loadUnsafe(String className) throws Exception {
        return (Processor) Class.forName(className)
                                .getDeclaredConstructor()
                                .newInstance();
    }

    // --- SAFE (AOT approach 1): explicit Map of suppliers — no reflection at all ---
    static final java.util.Map<String, java.util.function.Supplier<Processor>> REGISTRY =
        java.util.Map.of(
            "order",   OrderProcessor::new,
            "invoice", InvoiceProcessor::new
        );

    static Processor loadSafe(String type) {
        var supplier = REGISTRY.get(type);
        if (supplier == null) throw new IllegalArgumentException("Unknown type: " + type);
        return supplier.get();
    }

    public static void main(String[] args) throws Exception {
        // Unsafe path (works on JVM; fails in native without hints)
        Processor p1 = loadUnsafe("OrderProcessor");
        System.out.println("Unsafe: " + p1.process("ORD-001"));

        // Safe path (works on JVM and native, no hints needed)
        Processor p2 = loadSafe("order");
        System.out.println("Safe:   " + p2.process("ORD-001"));

        // If you MUST use reflection: register a hint (shown, not needed here)
        var hints = new RuntimeHints();
        hints.reflection().registerType(OrderProcessor.class,
            MemberCategory.INVOKE_PUBLIC_CONSTRUCTORS);
        System.out.println("Reflection hint registered: " +
            hints.reflection().typeHints().count() + " type(s)");
    }
}
```

How to run: `java AotBestPracticesBasic.java`

`Class.forName("OrderProcessor")` works on JVM but fails in a native image unless `OrderProcessor` is registered with a reflection hint. The supplier-map approach (`REGISTRY`) uses direct method references — no reflection, no hint required, and it's also faster. For the cases where you genuinely need dynamic class loading, always pair it with a `RuntimeHintsRegistrar`.

### Level 2 — Intermediate

Fix `@ConditionalOnProperty` with build-time properties; convert field injection to constructor injection; add a `RuntimeHintsPredicates` test.

```java
// AotBestPracticesIntermediate.java
import org.springframework.aot.hint.*;
import org.springframework.aot.hint.predicate.*;
import org.springframework.beans.factory.annotation.*;
import org.springframework.context.annotation.*;
import org.springframework.stereotype.*;
import java.util.*;

// --- DTOs with constructor injection (AOT-friendly) ---
record PaymentRequest(String orderId, double amount, String currency) {}
record PaymentResult(String txId, String status) {}

// --- Service with CONSTRUCTOR injection (AOT generates clean supplier) ---
@Service
class PaymentService {
    private final String currency;     // from @Value — safe for AOT
    private final List<String> gateways;

    // Constructor injection: AOT can express this as a plain supplier call
    @Autowired
    PaymentService(@Value("${payment.currency:USD}") String currency,
                   @Value("${payment.gateways:stripe,paypal}") List<String> gateways) {
        this.currency  = currency;
        this.gateways  = gateways;
    }

    public PaymentResult pay(PaymentRequest req) {
        return new PaymentResult("tx-" + req.orderId(), "OK-" + currency);
    }
    public List<String> availableGateways() { return gateways; }
}

@Configuration
@ComponentScan
class PaymentConfig { }

public class AotBestPracticesIntermediate {
    public static void main(String[] args) {
        System.setProperty("payment.currency", "EUR");
        System.setProperty("payment.gateways", "stripe,adyen");

        var ctx = new AnnotationConfigApplicationContext(PaymentConfig.class);
        var svc = ctx.getBean(PaymentService.class);

        var result = svc.pay(new PaymentRequest("ORD-007", 150.0, "EUR"));
        System.out.println("Payment: " + result);
        System.out.println("Gateways: " + svc.availableGateways());

        // Verify DTO hints using RuntimeHintsPredicates (do this in @SpringBootTest)
        var hints = new RuntimeHints();
        hints.reflection().registerType(PaymentRequest.class,
            MemberCategory.INVOKE_PUBLIC_CONSTRUCTORS,
            MemberCategory.INVOKE_PUBLIC_METHODS);
        hints.reflection().registerType(PaymentResult.class,
            MemberCategory.INVOKE_PUBLIC_CONSTRUCTORS,
            MemberCategory.INVOKE_PUBLIC_METHODS);

        var predicates = RuntimeHintsPredicates.reflection();
        System.out.println("PaymentRequest ctor hinted: " +
            predicates.onConstructor(PaymentRequest.class.getDeclaredConstructors()[0]).test(hints));
        System.out.println("PaymentResult ctor hinted:  " +
            predicates.onConstructor(PaymentResult.class.getDeclaredConstructors()[0]).test(hints));

        ctx.close();
    }
}
```

How to run: `java AotBestPracticesIntermediate.java`

Constructor injection (`@Autowired` on constructor) means AOT can generate `new PaymentService(currency, gateways)` directly in the bean definition supplier — no field-injection reflection needed. `@Value("${payment.currency:USD}")` includes a default (`USD`) which is safe: AOT evaluates the default at build time if the property is absent, avoiding `@ConditionalOnProperty` for simple defaults.

### Level 3 — Advanced

A Spring Boot app with all AOT best practices applied: constructor injection, `@RegisterReflectionForBinding`, `RuntimeHintsRegistrar` for one dynamic path, and a native-test configuration.

```java
// AotBestPracticesAdvanced.java — production-grade AOT Spring Boot app
import org.springframework.aot.hint.*;
import org.springframework.boot.*;
import org.springframework.boot.autoconfigure.*;
import org.springframework.context.annotation.*;
import org.springframework.stereotype.*;
import org.springframework.web.bind.annotation.*;
import java.util.*;
import java.util.concurrent.*;

// ---- DTOs: annotated for binding hints ----
@RegisterReflectionForBinding({OrderDto.class, PaymentDto.class})
record OrderDto(String id, String product, double amount) {}
record PaymentDto(String orderId, String status, String txRef) {}

// ---- Dynamic formatter loaded by name from config ----
interface Formatter { String format(Object obj); }
class JsonFormatter  implements Formatter { public String format(Object o) { return "{json:"  + o + "}"; } }
class PlainFormatter implements Formatter { public String format(Object o) { return "plain:"  + o; } }

// RuntimeHintsRegistrar for dynamic formatter loading
class FormatterHints implements RuntimeHintsRegistrar {
    @Override
    public void registerHints(RuntimeHints hints, ClassLoader cl) {
        hints.reflection().registerType(JsonFormatter.class,
            MemberCategory.INVOKE_PUBLIC_CONSTRUCTORS);
        hints.reflection().registerType(PlainFormatter.class,
            MemberCategory.INVOKE_PUBLIC_CONSTRUCTORS);
        hints.resources().registerPattern("formatters/config.properties");
    }
}

@Service
class OrderProcessingService {
    private final Map<String, Formatter> formatters;

    // Constructor injection — AOT-safe
    OrderProcessingService() throws Exception {
        formatters = new ConcurrentHashMap<>();
        // Dynamic loading: needs hints — registered by FormatterHints
        for (String cls : List.of("JsonFormatter", "PlainFormatter")) {
            formatters.put(cls.replace("Formatter", "").toLowerCase(),
                (Formatter) Class.forName(cls).getDeclaredConstructor().newInstance());
        }
    }

    public PaymentDto process(OrderDto order, String format) {
        Formatter fmt = formatters.getOrDefault(format, formatters.get("plain"));
        String ref = fmt.format(order.id());
        return new PaymentDto(order.id(), "PROCESSED", ref);
    }
}

@RestController
@RequestMapping("/orders")
class OrderController {
    private final OrderProcessingService svc;
    OrderController(OrderProcessingService svc) { this.svc = svc; }

    @PostMapping
    public PaymentDto process(@RequestBody OrderDto order,
                              @RequestParam(defaultValue = "json") String format) {
        return svc.process(order, format);
    }
}

@ImportRuntimeHints(FormatterHints.class)
@SpringBootApplication
public class AotBestPracticesAdvanced {
    public static void main(String[] args) {
        SpringApplication.run(AotBestPracticesAdvanced.class, args);
    }
}
```

How to run: `./mvnw spring-boot:run`, then `curl -XPOST localhost:8080/orders?format=json -H 'Content-Type:application/json' -d '{"id":"ORD-1","product":"Laptop","amount":1200}'`

Every AOT best practice is applied: `@RegisterReflectionForBinding` on DTOs for Jackson, `@ImportRuntimeHints(FormatterHints.class)` for the one dynamic `Class.forName` call, constructor injection everywhere, `@Value` defaults to avoid runtime-only conditionals. The result is a codebase that compiles to a native image with `./mvnw -Pnative native:compile` without additional configuration.

## 6. Walkthrough

Tracing `POST /orders?format=json` in **native mode** to show AOT best practices in action:

**Startup:**
1. Native binary starts; generated `__ApplicationContextInitializer.initialize(context)` runs.
2. `OrderProcessingService` supplier is called: `new OrderProcessingService()`.
3. Inside constructor: `Class.forName("JsonFormatter")` — succeeds because `FormatterHints` registered it.
4. `Class.forName("PlainFormatter")` — succeeds for same reason.
5. `formatters` map populated: `{json=JsonFormatter@..., plain=PlainFormatter@...}`.
6. Spring context ready. < 100ms from launch.

**Request: `POST /orders?format=json` with body `{"id":"ORD-1","product":"Laptop","amount":1200.0}`:**

1. Tomcat receives request; dispatches to `OrderController.process`.
2. Jackson deserialises JSON to `OrderDto("ORD-1","Laptop",1200.0)` — works because `@RegisterReflectionForBinding` hinted `OrderDto`'s constructor and methods.
3. `svc.process(order, "json")` called.
4. `formatters.get("json")` → `JsonFormatter`.
5. `fmt.format("ORD-1")` → `"{json:ORD-1}"`.
6. Returns `PaymentDto("ORD-1", "PROCESSED", "{json:ORD-1}")`.
7. Jackson serialises `PaymentDto` to JSON — works because `@RegisterReflectionForBinding` hinted `PaymentDto`.
8. Response: `{"orderId":"ORD-1","status":"PROCESSED","txRef":"{json:ORD-1}"}`

All reflection used (Jackson deserialisation, `Class.forName`) was covered by hints at build time. No `ClassNotFoundException` at native runtime.

## 7. Gotchas & takeaways

> **Never test AOT correctness only on JVM.** JVM reflection works unconditionally — a service that passes all JVM tests can still fail in native mode if hints are missing. The minimum native test matrix is: (1) `RuntimeHintsPredicates` assertions in unit tests; (2) `./mvnw -Pnative native:test` in CI.

> **`@Conditional` beans with externally injected properties at runtime are a native image anti-pattern.** Replace `@ConditionalOnProperty("feature.x")` with a single bean that reads the property at runtime and branches inside its methods — the bean is always registered, the behaviour varies. This avoids the build-time vs runtime condition mismatch.

- Profile your generated `target/spring-aot/main/sources/` — if a bean is missing from `__BeanDefinitions`, its condition evaluated to `false` at AOT time.
- Prefer constructor injection for all beans: field injection requires `DECLARED_FIELDS` hints; constructor injection generates a plain supplier, no hints needed.
- Use `ClassUtils.isPresent("com.legacy.Foo", classLoader)` inside a `RuntimeHintsRegistrar` to conditionally register hints only when a library is on the classpath.
- Run `native-image-inspect --list-reflection-methods` on your binary to verify which methods are included — useful for diagnosing "method not found" failures without rebuilding.
- `spring.aot.enabled=true` activates AOT mode on a JVM run, loading the generated initialiser; use this in integration tests to validate AOT initialisation without a native build.
