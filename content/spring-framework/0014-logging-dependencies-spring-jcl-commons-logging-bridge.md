---
card: spring-framework
gi: 14
slug: logging-dependencies-spring-jcl-commons-logging-bridge
title: Logging dependencies (spring-jcl / commons-logging bridge)
---

## 1. What it is

Spring Framework uses a **thin logging bridge** rather than a concrete logging framework. Starting with Spring 5.0, the bridge is `spring-jcl` (Spring's own Commons Logging fork, bundled inside `spring-core`). It intercepts all Spring's internal log calls and routes them to whichever SLF4J-compatible backend is on the classpath at runtime.

**How it works:**

```
Spring internal code
  → Log log = LogFactory.getLog(BeanFactory.class);
       (spring-jcl / commons-logging API)
  → spring-jcl detects: SLF4J API on classpath?
  → yes → delegates to SLF4J
       → SLF4J finds: Logback on classpath? Log4j2? java.util.logging?
  → concrete log appenders write to file / console
```

Before Spring 5, applications needed to exclude `commons-logging` (which Spring used to depend on directly) and add the `jcl-over-slf4j` bridge. Spring 5+ ships its own `spring-jcl` inside `spring-core`, eliminating that step.

In Spring Boot, logging is fully auto-configured. `spring-boot-starter-logging` (included in every starter) pulls in:
- `logback-classic` (the default backend)
- `log4j-to-slf4j` (routes Log4j 2 API calls to SLF4J)
- `jul-to-slf4j` (routes `java.util.logging` calls to SLF4J)

## 2. Why & when

Java's logging ecosystem is famously fragmented: SLF4J API, Logback, Log4j 2, `java.util.logging`, Commons Logging. Spring must not hardcode a logging framework because:

1. Your project may have a corporate-mandated logger.
2. A library that forces its logger onto you creates "logger wars" — two backends fighting for control.
3. Some frameworks (Log4j 1.x, legacy Commons Logging) have known security vulnerabilities (Log4Shell / CVE-2021-44228).

The bridge pattern means Spring always speaks SLF4J, and you choose the backend:

| Backend | How to use with Spring Boot |
|---|---|
| **Logback** (default) | Nothing to do — included by `spring-boot-starter-logging` |
| **Log4j 2** | Exclude `spring-boot-starter-logging`, add `spring-boot-starter-log4j2` |
| **java.util.logging** | Exclude `spring-boot-starter-logging`, add `jul-to-slf4j` |

When NOT using Spring Boot, you add `slf4j-api` + your preferred backend, and Spring's `spring-jcl` routes to SLF4J automatically.

## 3. Core concept

The logging bridge chain has four layers:

```
1. Application / Spring code
       calls: LogFactory.getLog(Cls) or Logger log = LoggerFactory.getLogger(Cls)
                             │
2. spring-jcl (inside spring-core)
       Commons Logging API — detects SLF4J on classpath and delegates
                             │
3. SLF4J API (slf4j-api.jar)
       Logging facade — routes to whatever binding is present
                             │
4. Backend binding (ONE of):
   logback-classic.jar   → Logback  (fast, flexible, default in Boot)
   log4j-slf4j2-impl.jar → Log4j 2 (async, high-throughput)
   slf4j-jdk14.jar       → java.util.logging
```

**Key rule:** only ONE backend binding can be active at a time. If two are on the classpath, SLF4J prints a warning and picks one — usually the first found, unpredictably. Maven/Gradle dependency exclusions are how you enforce one backend.

**Logging levels** (in order of severity):
`TRACE < DEBUG < INFO < WARN < ERROR`

Spring Boot's default: `INFO` level for everything except package-specific overrides in `application.properties`:
```properties
logging.level.root=INFO
logging.level.org.springframework.web=DEBUG
logging.level.com.example.myapp=TRACE
```

## 4. Diagram

<svg viewBox="0 0 700 260" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Logging bridge chain from Spring code through spring-jcl and SLF4J to Logback or Log4j 2 backend">
  <defs>
    <marker id="la" markerWidth="7" markerHeight="7" refX="5" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>

  <!-- Layer 1: Code -->
  <rect x="220" y="10" width="260" height="40" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="350" y="35" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Spring / Your Application Code</text>

  <!-- Layer 2: spring-jcl -->
  <rect x="220" y="70" width="260" height="40" rx="5" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="350" y="88" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif" font-weight="bold">spring-jcl (inside spring-core)</text>
  <text x="350" y="104" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Commons Logging bridge — detects SLF4J</text>

  <!-- Layer 3: SLF4J -->
  <rect x="220" y="130" width="260" height="40" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="350" y="148" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif" font-weight="bold">SLF4J API (slf4j-api.jar)</text>
  <text x="350" y="164" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Logging facade — routes to one backend</text>

  <!-- Layer 4: Backends -->
  <rect x="30"  y="195" width="180" height="45" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="120" y="213" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif" font-weight="bold">Logback</text>
  <text x="120" y="229" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Default (Boot starter-logging)</text>

  <rect x="260" y="195" width="180" height="45" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="350" y="213" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Log4j 2</text>
  <text x="350" y="229" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">starter-log4j2 alternative</text>

  <rect x="490" y="195" width="180" height="45" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="580" y="213" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">java.util.logging</text>
  <text x="580" y="229" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">via jul-to-slf4j bridge</text>

  <!-- Arrows -->
  <line x1="350" y1="50" x2="350" y2="68" stroke="#8b949e" stroke-width="1.5" marker-end="url(#la)"/>
  <line x1="350" y1="110" x2="350" y2="128" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#la)"/>
  <line x1="310" y1="170" x2="175" y2="193" stroke="#6db33f" stroke-width="1.5" marker-end="url(#la)"/>
  <line x1="350" y1="170" x2="350" y2="193" stroke="#6db33f" stroke-width="1.5" marker-end="url(#la)"/>
  <line x1="390" y1="170" x2="525" y2="193" stroke="#6db33f" stroke-width="1.5" marker-end="url(#la)"/>

  <text x="350" y="252" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Only ONE backend active at runtime — multiple backends cause unpredictable behaviour</text>
</svg>

Spring speaks to `spring-jcl`; `spring-jcl` speaks SLF4J; SLF4J speaks to one backend.

## 5. Runnable example

A product audit service demonstrating logging configuration and the bridge chain at each level.

### Level 1 — Basic

SLF4J API usage and log level filtering — what every Spring service's logging looks like.

```java
// LoggingDemo.java — run with: java LoggingDemo.java
// Demonstrates SLF4J API patterns that Spring Boot pre-configures for you.
// (Without the SLF4J JAR this shows the pattern as a simulation)

import java.util.*;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;

public class LoggingDemo {

    // Simulates SLF4J Logger behaviour (in Spring: import org.slf4j.Logger, LoggerFactory)
    enum Level { TRACE, DEBUG, INFO, WARN, ERROR }

    static class Logger {
        private final String name;
        private Level threshold;

        Logger(String name, Level threshold) { this.name = name; this.threshold = threshold; }

        private void log(Level level, String msg, Object... args) {
            if (level.ordinal() < threshold.ordinal()) return;
            String formatted = msg;
            for (Object a : args) formatted = formatted.replaceFirst("\\{}", String.valueOf(a));
            System.out.printf("[%s] %-5s %s - %s%n",
                LocalDateTime.now().format(DateTimeFormatter.ofPattern("HH:mm:ss.SSS")),
                level, name, formatted);
        }

        void trace(String msg, Object... a) { log(Level.TRACE, msg, a); }
        void debug(String msg, Object... a) { log(Level.DEBUG, msg, a); }
        void info (String msg, Object... a) { log(Level.INFO,  msg, a); }
        void warn (String msg, Object... a) { log(Level.WARN,  msg, a); }
        void error(String msg, Object... a) { log(Level.ERROR, msg, a); }
    }

    static class LoggerFactory {
        private static final Map<String, Level> LEVELS = Map.of(
            "com.example.product", Level.DEBUG,   // logging.level.com.example.product=DEBUG
            "root",                Level.INFO      // logging.level.root=INFO
        );
        static Logger getLogger(Class<?> cls) {
            String pkg = cls.getName().contains(".") ? cls.getName().substring(0, cls.getName().lastIndexOf('.')) : "root";
            Level level = LEVELS.entrySet().stream()
                .filter(e -> pkg.startsWith(e.getKey()))
                .map(Map.Entry::getValue)
                .findFirst()
                .orElse(Level.INFO);
            return new Logger(cls.getSimpleName(), level);
        }
    }

    record Product(int id, String name, double price) {}

    static class ProductService {
        private static final Logger log = LoggerFactory.getLogger(ProductService.class);
        private final Map<Integer, Product> store = new HashMap<>(Map.of(
            1, new Product(1, "Laptop",  1299.99),
            2, new Product(2, "Monitor",  449.99)
        ));

        Optional<Product> findById(int id) {
            log.debug("findById called with id={}", id);
            Optional<Product> result = Optional.ofNullable(store.get(id));
            if (result.isEmpty()) log.warn("Product not found: id={}", id);
            else log.debug("Found product: {}", result.get());
            return result;
        }

        Product create(Product p) {
            log.info("Creating product: name={}, price={}", p.name(), p.price());
            store.put(p.id(), p);
            return p;
        }
    }

    public static void main(String[] args) {
        System.out.println("=== Logging Demo — Level 1: SLF4J API ===\n");

        ProductService svc = new ProductService();
        svc.findById(1);
        svc.findById(99);   // triggers WARN
        svc.create(new Product(3, "Keyboard", 89.99));

        System.out.println("\nNote: TRACE would not appear even for this package (threshold=DEBUG)");
        System.out.println("      Root logger at INFO suppresses DEBUG for other packages");
    }
}
```

How to run: `java LoggingDemo.java`

`log.debug("findById called with id={}", id)` uses SLF4J's `{}` substitution syntax — the value is interpolated lazily. If the DEBUG level is disabled, the string is never assembled, avoiding needless `"findById called with id=" + id` string concatenation. In Spring Boot this pattern is configured via `logging.level.*` in `application.properties`.

### Level 2 — Intermediate

Switching backends and structured logging — the two most common production concerns.

```java
// LoggingDemoV2.java — run with: java LoggingDemoV2.java
// Shows backend switching and structured logging (JSON log output for ELK / Splunk).

import java.util.*;

public class LoggingDemoV2 {

    // In a real Spring Boot project, switch backends in pom.xml:
    /*
    <!-- Exclude default Logback -->
    <dependency>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter</artifactId>
        <exclusions>
            <exclusion>
                <groupId>org.springframework.boot</groupId>
                <artifactId>spring-boot-starter-logging</artifactId>
            </exclusion>
        </exclusions>
    </dependency>
    <!-- Add Log4j 2 instead -->
    <dependency>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-log4j2</artifactId>
    </dependency>
    */

    // Simulated structured log entry (JSON — used by ELK, Loki, Splunk)
    record LogEntry(String level, String logger, String message,
                    String traceId, Map<String, Object> context) {
        String toJson() {
            StringBuilder sb = new StringBuilder("{");
            sb.append("\"level\":\"").append(level).append("\",");
            sb.append("\"logger\":\"").append(logger).append("\",");
            sb.append("\"message\":\"").append(message).append("\",");
            sb.append("\"traceId\":\"").append(traceId).append("\"");
            context.forEach((k, v) ->
                sb.append(",\"").append(k).append("\":\"").append(v).append("\""));
            sb.append("}");
            return sb.toString();
        }
    }

    // Structured logger (mirrors Logback's JSON layout / Log4j2's JsonLayout)
    static class StructuredLogger {
        private final String name;
        private final String traceId;

        StructuredLogger(String name, String traceId) {
            this.name = name; this.traceId = traceId;
        }

        void log(String level, String message, Map<String, Object> ctx) {
            System.out.println(new LogEntry(level, name, message, traceId, ctx).toJson());
        }
        void info(String msg, Map<String, Object> ctx) { log("INFO", msg, ctx); }
        void warn(String msg, Map<String, Object> ctx) { log("WARN", msg, ctx); }
        void error(String msg, Throwable ex, Map<String, Object> ctx) {
            Map<String, Object> full = new LinkedHashMap<>(ctx);
            full.put("exception", ex.getClass().getSimpleName() + ": " + ex.getMessage());
            log("ERROR", msg, full);
        }
    }

    record Order(int id, String customer, double amount) {}

    public static void main(String[] args) {
        System.out.println("=== Logging Demo — Level 2: Backends + Structured Logging ===\n");

        System.out.println("--- application.properties for Log4j 2 switch ---");
        System.out.println("# (also exclude spring-boot-starter-logging in pom.xml)");
        System.out.println("logging.config=classpath:log4j2.xml");
        System.out.println();

        System.out.println("--- Structured JSON logging (ELK / Loki / Splunk) ---");
        System.out.println("# application.properties with Logback JSON layout:");
        System.out.println("logging.structured.format.console=ecs  # Boot 3.4+");
        System.out.println();

        // Simulate structured log output
        StructuredLogger log = new StructuredLogger("OrderService", "abc-123-def");

        Order order = new Order(42, "alice@example.com", 149.99);

        log.info("Order received",
            Map.of("orderId", order.id(), "customer", order.customer(), "amount", order.amount()));

        log.warn("Payment gateway slow",
            Map.of("orderId", order.id(), "latencyMs", 2850, "threshold", 2000));

        log.error("Payment failed",
            new RuntimeException("Timeout after 3000ms"),
            Map.of("orderId", order.id(), "gateway", "stripe", "attempt", 3));

        System.out.println("\n--- Parsing these JSON lines in Kibana/Grafana Loki ---");
        System.out.println("query: {app='product-service'} | json | level='WARN'");
        System.out.println("  → returns the payment-gateway-slow entry");
        System.out.println("query: {app='product-service'} | json | traceId='abc-123-def'");
        System.out.println("  → returns ALL three log lines correlated by trace ID");
    }
}
```

How to run: `java LoggingDemoV2.java`

Structured JSON logging is the standard for cloud-native deployments: each log line is valid JSON, Kibana/Grafana can filter by field (`level`, `orderId`, `traceId`) without regex. In Spring Boot 3.4+ you enable it with `logging.structured.format.console=ecs`. The trace ID (from Micrometer Tracing) correlates all log lines for one HTTP request across all services.

### Level 3 — Advanced

MDC (Mapped Diagnostic Context), asynchronous logging, and a Spring Boot logging configuration that matches production requirements.

```java
// LoggingDemoV3.java — run with: java LoggingDemoV3.java
// MDC correlation, async logging, production configuration.

import java.util.*;
import java.util.concurrent.*;

public class LoggingDemoV3 {

    // MDC (Mapped Diagnostic Context) — thread-local key-value pairs
    // In real Spring / SLF4J: import org.slf4j.MDC;
    static final ThreadLocal<Map<String, String>> MDC_STORE = ThreadLocal.withInitial(HashMap::new);

    static class MDC {
        static void put(String key, String value) { MDC_STORE.get().put(key, value); }
        static String get(String key) { return MDC_STORE.get().get(key); }
        static void remove(String key) { MDC_STORE.get().remove(key); }
        static void clear() { MDC_STORE.get().clear(); }
        static Map<String, String> getCopyOfContextMap() { return Map.copyOf(MDC_STORE.get()); }
    }

    static class Logger {
        private final String name;
        Logger(String name) { this.name = name; }

        void info(String msg) {
            Map<String, String> mdc = MDC.getCopyOfContextMap();
            String context = mdc.isEmpty() ? "" : " " + mdc;
            System.out.printf("[INFO]  %-25s %s%s%n", name, msg, context);
        }
        void warn(String msg) {
            Map<String, String> mdc = MDC.getCopyOfContextMap();
            String context = mdc.isEmpty() ? "" : " " + mdc;
            System.out.printf("[WARN]  %-25s %s%s%n", name, msg, context);
        }
        void error(String msg) {
            Map<String, String> mdc = MDC.getCopyOfContextMap();
            String context = mdc.isEmpty() ? "" : " " + mdc;
            System.out.printf("[ERROR] %-25s %s%s%n", name, msg, context);
        }
    }

    static class RequestFilter {
        static final Logger log = new Logger("RequestFilter");

        static void processRequest(String requestId, String user, Runnable handler) {
            // @param requestId = X-Request-ID header; user = authenticated principal
            MDC.put("requestId", requestId);
            MDC.put("user",      user);
            try {
                log.info("Request started");
                handler.run();
                log.info("Request completed");
            } finally {
                MDC.clear();  // IMPORTANT: always clear MDC after request
            }
        }
    }

    static class OrderService {
        static final Logger log = new Logger("OrderService");

        void processOrder(int orderId) {
            log.info("Processing order " + orderId);
            if (orderId == 99) {
                log.error("Order validation failed: " + orderId);
                throw new RuntimeException("Validation error");
            }
            log.info("Order processed: " + orderId);
        }
    }

    public static void main(String[] args) throws Exception {
        System.out.println("=== Logging Demo — Level 3: MDC + Async + Config ===\n");

        OrderService svc = new OrderService();

        System.out.println("--- Request 1 (success) ---");
        RequestFilter.processRequest("req-abc-001", "alice", () -> {
            svc.processOrder(42);
        });

        System.out.println("\n--- Request 2 (error) ---");
        RequestFilter.processRequest("req-abc-002", "bob", () -> {
            try { svc.processOrder(99); }
            catch (RuntimeException e) { /* handled by error filter */ }
        });

        System.out.println("\n--- Async logging (Log4j 2 AsyncAppender) ---");
        System.out.println("In log4j2.xml:");
        System.out.println("  <AsyncLogger name='com.example' level='DEBUG' additivity='false'>");
        System.out.println("    <AppenderRef ref='Console'/>");
        System.out.println("  </AsyncLogger>");
        System.out.println("  Async logging: log calls return immediately; LMAX Disruptor queues them");
        System.out.println("  Typical throughput: 10–50x faster than synchronous logging");

        System.out.println("\n--- Production application.properties ---");
        System.out.println("  # Root level: INFO (avoids debug spam from framework internals)");
        System.out.println("  logging.level.root=INFO");
        System.out.println("  # Your app: DEBUG for troubleshooting, INFO for production");
        System.out.println("  logging.level.com.example=INFO");
        System.out.println("  # Spring MVC: DEBUG shows request mapping and handler selection");
        System.out.println("  logging.level.org.springframework.web.servlet=WARN");
        System.out.println("  # Hibernate SQL: WARN hides SQL; DEBUG shows every query");
        System.out.println("  logging.level.org.hibernate.SQL=WARN");
        System.out.println("  # Structured output (Boot 3.4+)");
        System.out.println("  logging.structured.format.console=ecs");
        System.out.println("  logging.file.name=/var/log/app/product-service.log");
        System.out.println("  # Rolling policy");
        System.out.println("  logging.logback.rollingpolicy.max-file-size=100MB");
        System.out.println("  logging.logback.rollingpolicy.max-history=30");

        System.out.println("\n--- Virtual thread MDC caveat (JDK 21 + Boot 3.2) ---");
        System.out.println("  MDC is ThreadLocal — works fine with platform threads");
        System.out.println("  With virtual threads: use Logback's ContextMapAdapter or");
        System.out.println("  Micrometer Tracing's ObservationHandler to propagate context");
        System.out.println("  across virtual thread boundaries automatically");
    }
}
```

How to run: `java LoggingDemoV3.java`

MDC keys (`requestId`, `user`) appear automatically in every log line within the request, even when `OrderService` doesn't know about the request context. In Logback they appear via `%X{requestId}` in the pattern or automatically in JSON layout. `MDC.clear()` in the `finally` block is critical — if omitted, the next request processed by the same thread inherits the previous request's context.

## 6. Walkthrough

**Level 1 — log level filtering:**
`LoggerFactory.getLogger(ProductService.class)` → package `com.example.product` matches → threshold `DEBUG`. `log.debug("findById called with id={}", id)` → `DEBUG.ordinal()=1 >= TRACE.ordinal()=0` → printed. `log.trace(...)` → `TRACE.ordinal()=0 < DEBUG.ordinal()=1` → suppressed.

`svc.findById(99)` → `store.get(99)` returns `null` → `Optional.empty()` → `log.warn("Product not found: id={}", 99)` → WARN always prints (above DEBUG threshold).

**Level 2 — structured JSON:**
`log.info("Order received", Map.of(...))` → `LogEntry("INFO", "OrderService", "Order received", "abc-123-def", {...})` → `.toJson()` produces `{"level":"INFO","logger":"OrderService","message":"Order received","traceId":"abc-123-def","orderId":"42",...}`. Each line is independently parseable JSON. Kibana/Loki can filter by any field without regex.

**Level 3 — MDC propagation:**
1. `RequestFilter.processRequest("req-abc-001", "alice", handler)` → `MDC.put("requestId", "req-abc-001")`, `MDC.put("user", "alice")`.
2. `log.info("Request started")` → reads `MDC.getCopyOfContextMap()` = `{requestId=req-abc-001, user=alice}` → appends to log line.
3. `svc.processOrder(42)` runs on the same thread → inherits MDC context → `OrderService` log lines also show `{requestId=req-abc-001, user=alice}`.
4. `finally { MDC.clear(); }` — thread returns to pool; next request starts with empty MDC.

Without `MDC.clear()`, thread pool reuse causes stale context leakage: request 3's log would show `{requestId=req-abc-001, user=alice}` even though it's a different user.

## 7. Gotchas & takeaways

> **Two SLF4J backends on the classpath = random, unpredictable logging.** If you add Log4j 2 without excluding Logback, SLF4J logs a warning: `SLF4J: Class path contains multiple SLF4J providers.` The first one found in classpath order wins — which is non-deterministic. Always use `mvn dependency:tree | grep slf4j` to verify only one backend binding is present.

> **`MDC.clear()` is not called automatically.** If your code runs inside a thread pool (Tomcat, `@Async`, virtual threads) and you set MDC keys without clearing them, the keys survive to the next request on that thread. Use a `Filter` (Servlet) or `WebMvcConfigurer` interceptor to clear MDC in a `finally` block or `afterCompletion`.

- Spring Boot's default Logback configuration includes a console appender with pattern `%d{yyyy-MM-dd HH:mm:ss.SSS} %-5level --- [%.15t] %-40.40logger{39} : %msg%n`.
- `spring.output.ansi.enabled=ALWAYS` enables colour-coded log levels in terminals that support ANSI codes.
- `logging.level.org.springframework.security=DEBUG` shows every security decision (authentication, authorisation, filter chain) — helpful for debugging but very verbose; never leave at DEBUG in production.
- Log4j 2 (not Log4j 1.x) is the only Log4j version compatible with Spring Boot 3.x. Log4j 1.x reached end-of-life in 2015 and is vulnerable to multiple CVEs. Never use it.
- `spring-jcl` is inside `spring-core.jar` — it cannot be excluded. It always bridges Spring's internal logging to SLF4J. You only need to ensure one SLF4J backend is present.
