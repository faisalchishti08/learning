---
card: spring-framework
gi: 6
slug: jdk-17-baseline-spring-6
title: JDK 17+ baseline (Spring 6)
---

## 1. What it is

**Spring Framework 6.0** (released November 2022) requires **JDK 17 as the minimum Java version**. You cannot build or run a Spring 6.x application on JDK 8, 11, or any version below 17.

Spring Boot 3.x is built on Spring Framework 6.x and therefore carries the same JDK 17 requirement. Spring Boot 3.1+ also benefits from JDK 21 features (virtual threads via Project Loom), but 17 is the hard minimum.

Key JDK 17 language features Spring 6 actively uses and encourages:

| Feature | JDK | How Spring uses it |
|---|---|---|
| Records | 16 (stable) | `@ConfigurationProperties`, DTO, value objects |
| Sealed classes/interfaces | 17 (stable) | Type-safe discriminated unions |
| Pattern matching `instanceof` | 16 (stable) | Internal Spring code, recommended in user code |
| Text blocks | 15 (stable) | SQL, JSON literals in tests/config |
| `switch` expressions | 14 (stable) | Concise dispatch in services |
| `NullPointerException` messages | 14 | Clearer NPE diagnostics |
| Strong encapsulation (JPMS) | 9–17 | Spring 6 no longer needs `--add-opens` hacks |

## 2. Why & when

**Why JDK 17?** JDK 17 is an LTS (Long-Term Support) release — Oracle and all major vendors (Azul, Amazon Corretto, Red Hat, Microsoft) provide extended support through at least 2029. Spring tied its major version cycle to LTS releases: Spring 5.x→JDK 8 LTS, Spring 6.x→JDK 17 LTS.

Additionally, JDK 17 closes the module-system "illegal access" loopholes that Spring 5.x relied on for reflection tricks. Spring 6.x was rewritten to work within the JDK 17 module system's stricter encapsulation without requiring `--add-opens` flags.

**Impact on you:** if your application or any of its dependencies still target JDK 8 or 11 bytecode, they can still *run* on JDK 17 (JDK is backwards compatible at the bytecode level), but you must compile and run with JDK 17+. The most common blocker is a transitive library that uses internal JDK APIs (`sun.misc.Unsafe`, etc.) — those break under JDK 17's stricter encapsulation.

## 3. Core concept

Three JDK 17 features matter most for Spring 6 application code:

**Records** — immutable data carriers with no boilerplate. Spring 6 supports `@ConfigurationProperties` bound to records (constructor binding):

```java
@ConfigurationProperties("app")
record AppConfig(String name, int port, Duration timeout) {}
// Bound from: app.name=order-service, app.port=8080, app.timeout=30s
```

**Sealed interfaces** — restrict which classes can implement an interface, enabling exhaustive `switch` expressions:

```java
sealed interface PaymentResult permits Success, Failure, Pending {}
record Success(String ref)     implements PaymentResult {}
record Failure(String reason)  implements PaymentResult {}
record Pending(String jobId)   implements PaymentResult {}

// Compiler knows all cases — no default needed:
String message = switch (result) {
    case Success(var r) -> "Paid: " + r;
    case Failure(var e) -> "Failed: " + e;
    case Pending(var j) -> "Waiting: " + j;
};
```

**Pattern matching `instanceof`** — eliminates explicit casts:

```java
// Old (Spring 5 / JDK 8 style):
if (event instanceof OrderPlaced) {
    OrderPlaced op = (OrderPlaced) event;
    ...
}

// New (JDK 16+ / Spring 6 style):
if (event instanceof OrderPlaced op) {
    // op is already cast
}
```

## 4. Diagram

<svg viewBox="0 0 700 230" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="JDK version progression showing Spring version alignment: Spring 5 on JDK 8-11, Spring 6 on JDK 17-21">
  <defs>
    <marker id="va" markerWidth="7" markerHeight="7" refX="5" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>

  <!-- Axis -->
  <line x1="30" y1="115" x2="670" y2="115" stroke="#8b949e" stroke-width="1.5" marker-end="url(#va)"/>

  <!-- JDK versions -->
  <circle cx="70"  cy="115" r="5" fill="#8b949e"/>
  <text x="70"  y="133" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">JDK 8</text>
  <text x="70"  y="143" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">LTS '14</text>

  <circle cx="200" cy="115" r="5" fill="#8b949e"/>
  <text x="200" y="133" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">JDK 11</text>
  <text x="200" y="143" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">LTS '18</text>

  <circle cx="380" cy="115" r="7" fill="#6db33f"/>
  <text x="380" y="133" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif" font-weight="bold">JDK 17</text>
  <text x="380" y="143" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">LTS '21 (Spring 6 min)</text>

  <circle cx="560" cy="115" r="6" fill="#6db33f"/>
  <text x="560" y="133" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">JDK 21</text>
  <text x="560" y="143" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">LTS '23 (Loom)</text>

  <!-- Spring 5 band -->
  <rect x="40" y="50" width="260" height="45" rx="5" fill="#1c2430" stroke="#f0883e" stroke-width="1.5"/>
  <text x="170" y="70" fill="#f0883e" font-size="11" text-anchor="middle" font-family="sans-serif" font-weight="bold">Spring Framework 5.x</text>
  <text x="170" y="86" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">JDK 8–17 (supports all)</text>

  <!-- Spring 6 band -->
  <rect x="330" y="50" width="260" height="45" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="460" y="70" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif" font-weight="bold">Spring Framework 6.x</text>
  <text x="460" y="86" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">JDK 17+ required (21 for Loom)</text>

  <!-- Features callouts -->
  <text x="380" y="175" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Records · Sealed types · Pattern matching · Text blocks · switch expressions</text>
  <text x="380" y="192" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">JDK 17 = stable LTS with all features Spring 6 depends on</text>
  <text x="380" y="210" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">JDK 21 adds virtual threads — Spring 6.1 / Boot 3.2 enables them automatically</text>
</svg>

Spring 6 is anchored to JDK 17's stable features; Spring 6.1 optionally uses JDK 21's virtual threads.

## 5. Runnable example

A payment processing service showing JDK 17 features that Spring 6 actively uses — the same scenario grows from basic to advanced.

### Level 1 — Basic

Records as value objects and text blocks for readable test data.

```java
// Jdk17FeaturesDemo.java — run with: java Jdk17FeaturesDemo.java (JDK 17+)

public class Jdk17FeaturesDemo {

    // Record: immutable value object, no boilerplate (JDK 16+)
    // In Spring 6: @ConfigurationProperties can bind to records
    record PaymentRequest(String orderId, double amount, String currency) {}

    // Record: response DTO
    record PaymentResponse(String transactionId, String status, double amount) {}

    // Simple payment processor
    static PaymentResponse process(PaymentRequest req) {
        if (req.amount() <= 0)
            throw new IllegalArgumentException("Amount must be positive");
        String txId = "TXN-" + req.orderId().toUpperCase() + "-" + (int)(req.amount() * 100);
        return new PaymentResponse(txId, "APPROVED", req.amount());
    }

    public static void main(String[] args) {
        // Text block (JDK 15+) — readable JSON without escape clutter
        String requestJson = """
            {
              "orderId": "ord-42",
              "amount": 149.99,
              "currency": "USD"
            }
            """;

        System.out.println("=== JDK 17 Features — Level 1: Records + Text Blocks ===\n");
        System.out.println("Request JSON (text block):");
        System.out.println(requestJson);

        PaymentRequest req = new PaymentRequest("ord-42", 149.99, "USD");
        System.out.println("Bound to record: " + req);  // auto-generated toString

        PaymentResponse resp = process(req);
        System.out.println("Response record: " + resp);

        // Records are immutable and final — no accidental mutation
        System.out.println("\norderId component: " + req.orderId());    // accessor
        System.out.println("amount component:  " + req.amount());
    }
}
```

How to run: `java Jdk17FeaturesDemo.java` (JDK 17+)

Records eliminate the `class + constructor + getters + equals + hashCode + toString` boilerplate. Spring 6's `@ConfigurationProperties` binds to records via constructor injection — same principle.

### Level 2 — Intermediate

Add sealed interfaces and `switch` expressions for exhaustive result handling.

```java
// Jdk17FeaturesV2.java — run with: java Jdk17FeaturesV2.java (JDK 17+)

public class Jdk17FeaturesV2 {

    record PaymentRequest(String orderId, double amount, String currency) {}

    // Sealed interface: exactly three outcomes possible — compiler enforces exhaustiveness
    sealed interface PaymentResult permits PaymentResult.Approved,
                                           PaymentResult.Declined, PaymentResult.Pending {
        record Approved(String txId, double amount) implements PaymentResult {}
        record Declined(String reason, String code) implements PaymentResult {}
        record Pending(String jobId, String eta)   implements PaymentResult {}
    }

    static PaymentResult processPayment(PaymentRequest req) {
        if (req.amount() <= 0)
            return new PaymentResult.Declined("Invalid amount", "ERR_AMT");
        if (req.amount() > 10_000)
            return new PaymentResult.Pending("JOB-" + req.orderId(), "2–5 business days");
        return new PaymentResult.Approved(
            "TXN-" + req.orderId().toUpperCase(),
            req.amount());
    }

    // Pattern matching instanceof (JDK 16+) — used in Spring's internal event handling
    static void logResult(Object result) {
        if (result instanceof PaymentResult.Approved a)
            System.out.println("  [LOG] Approved txId=" + a.txId() + " amount=" + a.amount());
        else if (result instanceof PaymentResult.Declined d)
            System.out.println("  [LOG] Declined code=" + d.code() + " reason=" + d.reason());
        else if (result instanceof PaymentResult.Pending p)
            System.out.println("  [LOG] Pending jobId=" + p.jobId() + " eta=" + p.eta());
    }

    public static void main(String[] args) {
        System.out.println("=== JDK 17 Features — Level 2: Sealed + Switch + Pattern Matching ===\n");

        var requests = java.util.List.of(
            new PaymentRequest("ord-1",  149.99,   "USD"),
            new PaymentRequest("ord-2",  -5.00,    "USD"),
            new PaymentRequest("ord-3",  15_000.0, "USD")
        );

        for (PaymentRequest req : requests) {
            PaymentResult result = processPayment(req);
            System.out.println("Request: " + req);

            // switch expression on sealed type — compiler requires all cases covered
            String httpStatus = switch (result) {
                case PaymentResult.Approved a  -> "200 OK (txId=" + a.txId() + ")";
                case PaymentResult.Declined d  -> "402 Payment Required (" + d.code() + ")";
                case PaymentResult.Pending  p  -> "202 Accepted (job=" + p.jobId() + ")";
            };
            System.out.println("HTTP response: " + httpStatus);
            logResult(result);
            System.out.println();
        }
    }
}
```

How to run: `java Jdk17FeaturesV2.java` (JDK 17+)

The `switch` expression on `PaymentResult` has no `default` branch — the compiler knows all three cases are covered because the sealed interface limits subclasses. If someone adds a fourth case (`Cancelled`) without updating the switch, the code fails to compile.

### Level 3 — Advanced

Add Spring 6's `@ConfigurationProperties` record binding pattern, `NullPointerException` diagnostic messages, and a complete controller dispatch using all JDK 17 features.

```java
// Jdk17FeaturesV3.java — run with: java Jdk17FeaturesV3.java (JDK 17+)

import java.util.*;
import java.time.Duration;

public class Jdk17FeaturesV3 {

    // @ConfigurationProperties bound to a record (Spring 6 feature)
    // In real Spring: @ConfigurationProperties("payment")
    // application.properties:
    //   payment.gateway-url=https://pay.example.com
    //   payment.timeout=30s
    //   payment.max-amount=50000
    record PaymentConfig(String gatewayUrl, Duration timeout, double maxAmount) {
        static PaymentConfig fromProperties(Map<String, String> props) {
            return new PaymentConfig(
                props.getOrDefault("payment.gateway-url", "https://pay.example.com"),
                Duration.parse("PT" + props.getOrDefault("payment.timeout", "30S").toUpperCase()),
                Double.parseDouble(props.getOrDefault("payment.max-amount", "10000"))
            );
        }
    }

    record PaymentRequest(String orderId, double amount, String currency) {}

    sealed interface PaymentResult permits PaymentResult.Approved,
                                           PaymentResult.Declined, PaymentResult.Pending {
        record Approved(String txId, double amount) implements PaymentResult {}
        record Declined(String reason, String code) implements PaymentResult {}
        record Pending(String jobId, String eta)   implements PaymentResult {}
    }

    static class PaymentService {
        private final PaymentConfig config;

        PaymentService(PaymentConfig config) { this.config = config; }

        PaymentResult process(PaymentRequest req) {
            Objects.requireNonNull(req.orderId(), "orderId must not be null");  // JDK 14 NPE msg
            if (req.amount() <= 0)
                return new PaymentResult.Declined("Invalid amount", "ERR_AMT");
            if (req.amount() > config.maxAmount())
                return new PaymentResult.Pending(
                    "JOB-" + req.orderId().toUpperCase(),
                    config.timeout().toSeconds() + "s estimated");
            return new PaymentResult.Approved(
                "TXN-" + req.orderId().toUpperCase(),
                req.amount());
        }
    }

    // Simulated @RestController
    record HttpResponse(int status, String body) {
        @Override public String toString() { return "HTTP " + status + " | " + body; }
    }

    static class PaymentController {
        private final PaymentService service;
        PaymentController(PaymentService svc) { this.service = svc; }

        HttpResponse handlePost(PaymentRequest req) {
            PaymentResult result = service.process(req);
            return switch (result) {
                case PaymentResult.Approved a ->
                    new HttpResponse(200, "Approved: txId=" + a.txId() + " amount=$" + a.amount());
                case PaymentResult.Declined d ->
                    new HttpResponse(402, "Declined: " + d.reason() + " [" + d.code() + "]");
                case PaymentResult.Pending p ->
                    new HttpResponse(202, "Pending: job=" + p.jobId() + " eta=" + p.eta());
            };
        }
    }

    public static void main(String[] args) {
        System.out.println("=== JDK 17 Features — Level 3: Full Spring 6 pattern ===\n");

        // Simulated application.properties (Spring 6 @ConfigurationProperties record binding)
        Map<String, String> props = Map.of(
            "payment.gateway-url", "https://pay.example.com/v2",
            "payment.timeout",     "45S",
            "payment.max-amount",  "25000"
        );
        PaymentConfig config = PaymentConfig.fromProperties(props);
        System.out.println("Config (from application.properties):");
        System.out.println("  gateway:    " + config.gatewayUrl());
        System.out.println("  timeout:    " + config.timeout());
        System.out.println("  maxAmount:  " + config.maxAmount());

        PaymentService svc = new PaymentService(config);
        PaymentController ctrl = new PaymentController(svc);

        System.out.println("\n--- Requests ---");
        List<PaymentRequest> requests = List.of(
            new PaymentRequest("ord-1",   149.99,  "USD"),
            new PaymentRequest("ord-2",   -10.0,   "USD"),
            new PaymentRequest("ord-3",  30_000.0, "USD")
        );
        for (PaymentRequest req : requests) {
            System.out.println("POST /payments " + req + " → " + ctrl.handlePost(req));
        }

        System.out.println("\n--- NPE diagnostic (JDK 14+ helpful message) ---");
        try {
            new PaymentRequest(null, 50.0, "USD");
            svc.process(new PaymentRequest(null, 50.0, "USD"));
        } catch (NullPointerException e) {
            System.out.println("NPE: " + e.getMessage());  // "orderId must not be null"
        }

        System.out.println("\n--- JDK 17 feature checklist ---");
        System.out.println("  Records:            PaymentConfig, PaymentRequest, PaymentResult.*");
        System.out.println("  Sealed interfaces:  PaymentResult (Approved|Declined|Pending)");
        System.out.println("  Pattern matching:   switch(result) with deconstruction patterns");
        System.out.println("  Text blocks:        (used in config JSON literals in real Spring tests)");
        System.out.println("  switch expressions: exhaustive, no default needed for sealed types");
    }
}
```

How to run: `java Jdk17FeaturesV3.java` (JDK 17+)

`PaymentConfig.fromProperties` mirrors exactly what Spring 6's `@ConfigurationProperties` record binding does: read property strings, convert via registered `ConversionService`, pass all values to the record's canonical constructor in one call — no setters, no mutable state.

## 6. Walkthrough

**Startup (Level 3):**
1. `PaymentConfig.fromProperties(props)` reads three properties and constructs an immutable record. Spring 6 does this via `@EnableConfigurationProperties` + `@ConfigurationProperties("payment")` on the record.
2. `PaymentService(config)` receives the config record via constructor injection. No setter needed — the config is final.
3. `PaymentController(svc)` receives the service.

**POST /payments ord-1, $149.99:**
- `ctrl.handlePost(req)` calls `service.process(req)`.
- `Objects.requireNonNull(req.orderId(), ...)` passes (orderId is "ord-1").
- `req.amount() > config.maxAmount()` → `149.99 > 25000` → false.
- `req.amount() <= 0` → false.
- Returns `PaymentResult.Approved("TXN-ORD-1", 149.99)`.
- `switch(result)` matches `Approved a` → `HttpResponse(200, "Approved: txId=TXN-ORD-1 amount=$149.99")`.

**POST /payments ord-3, $30,000:**
- `req.amount() > config.maxAmount()` → `30000 > 25000` → true.
- Returns `PaymentResult.Pending("JOB-ORD-3", "45s estimated")`.
- `switch(result)` matches `Pending p` → `HttpResponse(202, "Pending: job=JOB-ORD-3 eta=45s estimated")`.

**NPE diagnostic test:**
- `Objects.requireNonNull(null, "orderId must not be null")` throws `NullPointerException` with message `"orderId must not be null"`. In JDK 14+, even implicit NPEs produce helpful messages like `"Cannot invoke 'String.length()' because 'req.orderId()' is null"`.

## 7. Gotchas & takeaways

> **Records cannot extend other classes and cannot be extended.** They implicitly extend `java.lang.Record`. You cannot use records as JPA `@Entity` classes — JPA requires a no-arg constructor and mutable fields. Use records as DTOs (request/response bodies, config properties, projections) and keep `@Entity` classes as regular mutable POJOs.

> **Sealed interfaces work for exhaustive `switch` only in the same compilation unit or if all subclasses are `final`.** If you define a `sealed interface` in module A and the permitted classes in module B, the `switch` exhaustiveness check requires all classes to be on the same module-path. In typical Spring apps everything is in one module so this is rarely a problem.

- Spring 6 `@ConfigurationProperties` on records requires all properties to be constructor parameters — no optional fields with default values unless you use `@DefaultValue` on the constructor parameter.
- `NullPointerException` messages in JDK 14+ are enabled by default (`-XX:+ShowCodeDetailsInExceptionMessages` was default-on from JDK 14). You no longer need to decode which dereference caused the NPE.
- Text blocks strip consistent leading whitespace. The closing `"""` position controls indentation — if you indent it less, more whitespace is preserved.
- Pattern-matching `switch` with deconstruction patterns (e.g., `case Approved(var txId, var amount)`) requires JDK 21+. JDK 17 supports the `case Type varName` form shown here.
- Spring 6.1 + JDK 21 enables virtual threads automatically for `@Async` and `@Transactional` when you set `spring.threads.virtual.enabled=true`. No code changes needed.
