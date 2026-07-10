---
card: java
gi: 1049
slug: logging-slf4j-logback-log4j2
title: "Logging (SLF4J + Logback / Log4j2)"
---

## 1. What it is

SLF4J (Simple Logging Facade for Java) is a thin **facade** — application code and libraries call SLF4J's `Logger` interface, and a separate binding, chosen at deployment time, routes those calls to an actual logging implementation like Logback or Log4j2. The point of the facade is decoupling: your code and any library you depend on log against the same SLF4J interface, but only one concrete logging backend needs to actually be configured and running per application, regardless of how many different libraries — each possibly written assuming a different logging framework — are on the classpath together.

## 2. Why & when

Before SLF4J's widespread adoption, different libraries were often written against different concrete logging frameworks directly (one against Log4j, another against `java.util.logging`), and an application using both would need to configure — and often fight to reconcile — multiple separate logging systems simultaneously, each with its own configuration format and output destination. SLF4J solves this by being the one interface every library logs *against*; a single binding at the application's own classpath then decides which actual implementation (Logback, Log4j2) receives every one of those calls, giving one unified place to configure log levels, formats, and output destinations for the entire application, regardless of how many different libraries are logging through it.

Log at the right **level** for the right audience: `ERROR` for something that broke and needs attention, `WARN` for something recoverable but worth noting, `INFO` for significant application lifecycle events (started, stopped, a major operation completed), `DEBUG` for detail useful when actively diagnosing a problem but too noisy for normal operation. Use SLF4J's parameterized logging (`log.info("User {} logged in", userId)`) rather than string concatenation, since it defers the actual string-building cost until the log statement is confirmed to actually be enabled at the configured level — avoiding wasted work formatting a `DEBUG` message that will just be discarded when the application is running at `INFO` level.

## 3. Core concept

```java
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

class OrderService {
    private static final Logger log = LoggerFactory.getLogger(OrderService.class);

    void placeOrder(String orderId, double amount) {
        log.info("Placing order {} for ${}", orderId, amount); // parameterized -- no string concat
        try {
            if (amount <= 0) {
                throw new IllegalArgumentException("amount must be positive");
            }
            log.debug("Order {} validated successfully", orderId);
        } catch (IllegalArgumentException e) {
            log.error("Order {} failed validation: {}", orderId, e.getMessage(), e); // pass the exception itself too
            throw e;
        }
    }
}
```

```xml
<!-- logback.xml: configures WHERE and HOW logs actually get written --
     application code never references Logback directly, only SLF4J -->
<configuration>
    <appender name="STDOUT" class="ch.qos.logback.core.ConsoleAppender">
        <encoder>
            <pattern>%d{HH:mm:ss} [%level] %logger{36} - %msg%n</pattern>
        </encoder>
    </appender>
    <root level="INFO">
        <appender-ref ref="STDOUT"/>
    </root>
</configuration>
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Application code and a third-party library both logging through the same SLF4J Logger interface, routed by a single binding to one configured Logback backend writing to the console">
  <rect x="20" y="20" width="150" height="34" rx="6" fill="#1c2430" stroke="#8b949e"/>
  <text x="95" y="41" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Your application code</text>
  <rect x="20" y="110" width="150" height="34" rx="6" fill="#1c2430" stroke="#8b949e"/>
  <text x="95" y="131" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Third-party library</text>

  <rect x="240" y="65" width="140" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="310" y="90" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">SLF4J Logger</text>

  <rect x="460" y="65" width="150" height="40" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="535" y="90" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Logback (console)</text>

  <line x1="170" y1="37" x2="240" y2="80" stroke="#8b949e" marker-end="url(#a)"/>
  <line x1="170" y1="127" x2="240" y2="95" stroke="#8b949e" marker-end="url(#a)"/>
  <line x1="380" y1="85" x2="460" y2="85" stroke="#8b949e" marker-end="url(#a)"/>
  <defs><marker id="a" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Both your code and any library route logging calls through the same SLF4J interface, resolved to one configured backend.

## 5. Runnable example

Scenario: an order-placement service logging its activity, evolving from ad-hoc `println` output into properly-leveled, parameterized SLF4J logging with a configured backend.

### Level 1 — Basic

```java
// File: OrderServiceBasic.java
public class OrderServiceBasic {
    static void placeOrder(String orderId, double amount) {
        System.out.println("Placing order " + orderId + " for $" + amount); // string concat, always executes
        if (amount <= 0) {
            System.out.println("ERROR: Order " + orderId + " failed validation"); // no real "level" -- just text
            throw new IllegalArgumentException("amount must be positive");
        }
    }

    public static void main(String[] args) {
        placeOrder("order-1", 19.99);
        try {
            placeOrder("order-2", -5.0);
        } catch (IllegalArgumentException e) {
            System.out.println("Caught: " + e.getMessage());
        }
    }
}
```

**How to run:** save as `OrderServiceBasic.java`, then `javac OrderServiceBasic.java && java OrderServiceBasic` (JDK 17+).

Expected output:
```
Placing order order-1 for $19.99
Placing order order-2 for $-5.0
ERROR: Order order-2 failed validation
Caught: amount must be positive
```

Every message is printed unconditionally to standard output — there's no way to selectively quiet the routine "Placing order" messages while keeping error output visible, and every string is built via concatenation regardless of whether anyone is even going to see it.

### Level 2 — Intermediate

```java
// File: src/main/java/OrderServiceIntermediate.java
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class OrderServiceIntermediate {
    private static final Logger log = LoggerFactory.getLogger(OrderServiceIntermediate.class);

    static void placeOrder(String orderId, double amount) {
        log.info("Placing order {} for ${}", orderId, amount); // parameterized, level-tagged
        if (amount <= 0) {
            log.error("Order {} failed validation", orderId);
            throw new IllegalArgumentException("amount must be positive");
        }
    }

    public static void main(String[] args) {
        placeOrder("order-1", 19.99);
        try {
            placeOrder("order-2", -5.0);
        } catch (IllegalArgumentException e) {
            log.warn("Order placement rejected: {}", e.getMessage());
        }
    }
}
```

**How to run:** place in a Maven project with `slf4j-api` and `logback-classic` as dependencies (Logback's SLF4J binding is included transitively via `logback-classic`), then run `mvn compile exec:java -Dexec.mainClass=OrderServiceIntermediate`.

Expected output (default Logback console pattern, timestamps will vary):
```
14:32:01.123 [main] INFO OrderServiceIntermediate - Placing order order-1 for $19.99
14:32:01.125 [main] INFO OrderServiceIntermediate - Placing order order-2 for $-5.0
14:32:01.126 [main] ERROR OrderServiceIntermediate - Order order-2 failed validation
14:32:01.127 [main] WARN OrderServiceIntermediate - Order placement rejected: amount must be positive
```

The real-world concern added: each message now has a genuine severity level (`INFO`, `ERROR`, `WARN`), a timestamp, and the originating class name — all provided automatically by the logging backend's configured format, not manually built into each message string. Levels can later be selectively filtered (e.g., suppressing `INFO` in production while keeping `WARN`/`ERROR` visible) without touching any application code.

### Level 3 — Advanced

```xml
<!-- File: src/main/resources/logback.xml -- configures WHERE logs go and at
     WHAT level, entirely separately from the application code itself -->
<configuration>
    <appender name="STDOUT" class="ch.qos.logback.core.ConsoleAppender">
        <encoder>
            <pattern>%d{HH:mm:ss} [%level] %logger{20} - %msg%n</pattern>
        </encoder>
    </appender>

    <!-- Only show INFO and above by default, but suppress this specific,
         noisy class down to WARN -- a common real-world tuning need. -->
    <logger name="OrderServiceAdvanced" level="WARN"/>

    <root level="INFO">
        <appender-ref ref="STDOUT"/>
    </root>
</configuration>
```

```java
// File: src/main/java/OrderServiceAdvanced.java
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class OrderServiceAdvanced {
    private static final Logger log = LoggerFactory.getLogger(OrderServiceAdvanced.class);

    static void placeOrder(String orderId, double amount) {
        log.info("Placing order {} for ${}", orderId, amount); // SUPPRESSED by logback.xml's per-logger level
        log.debug("Full order details: id={}, amount={}", orderId, amount); // suppressed even more so
        if (amount <= 0) {
            try {
                throw new IllegalArgumentException("amount must be positive");
            } catch (IllegalArgumentException e) {
                // Passing the exception itself (not just its message) lets the
                // backend include the full stack trace in the log output.
                log.error("Order {} failed validation", orderId, e);
                throw e;
            }
        }
    }

    public static void main(String[] args) {
        placeOrder("order-1", 19.99);
        try {
            placeOrder("order-2", -5.0);
        } catch (IllegalArgumentException e) {
            log.warn("Order placement rejected for order-2");
        }
    }
}
```

**How to run:** place `logback.xml` in `src/main/resources/`, add the same dependencies as Level 2, then run `mvn compile exec:java -Dexec.mainClass=OrderServiceAdvanced`.

Expected output (timestamps will vary; notice the `INFO` and `DEBUG` lines from `OrderServiceAdvanced` are completely absent, suppressed by the per-logger `WARN` configuration):
```
14:35:10.201 [main] ERROR OrderServiceAdvanced - Order order-2 failed validation
java.lang.IllegalArgumentException: amount must be positive
	at OrderServiceAdvanced.placeOrder(OrderServiceAdvanced.java:15)
	at OrderServiceAdvanced.main(OrderServiceAdvanced.java:24)
14:35:10.204 [main] WARN OrderServiceAdvanced - Order placement rejected for order-2
```

The production-flavored hard case: `logback.xml`'s `<logger name="OrderServiceAdvanced" level="WARN"/>` selectively raises this one class's minimum log level to `WARN`, silently suppressing both the `INFO` "Placing order" message and the `DEBUG` detail message — with zero changes to the application code itself — while `ERROR` and `WARN` messages still appear, and the `ERROR` call's passed exception produces a full stack trace in the output.

## 6. Walkthrough

Tracing what happens as `placeOrder("order-2", -5.0)` executes and logs in `OrderServiceAdvanced`:

1. `log.info("Placing order {} for ${}", "order-2", -5.0)` is called — before formatting the message string at all, Logback checks whether the `INFO` level is actually enabled for this specific logger. Because `logback.xml` configures `OrderServiceAdvanced`'s logger at `level="WARN"` (overriding the `root` logger's `INFO` default for this one class), `INFO` is *not* enabled here — the message is discarded immediately, and critically, the `{}`-token substitution work is never even performed, since SLF4J's parameterized API defers that cost until the level check passes.
2. `log.debug(...)` is skipped for the same reason — `DEBUG` is an even lower priority than the configured `WARN` threshold.
3. `amount <= 0` evaluates `-5.0 <= 0`, which is `true`, so a `new IllegalArgumentException("amount must be positive")` is thrown and immediately caught by the surrounding `try`/`catch`.
4. `log.error("Order {} failed validation", "order-2", e)` is called — `ERROR` is enabled (it's a higher priority than the configured `WARN` threshold), so this time the message *is* actually built and emitted. Because the final argument, `e`, is a `Throwable` (recognized specially by SLF4J's varargs-based API), Logback appends the full stack trace of the exception to the log output, not just its message.
5. The exception is then rethrown by the `catch` block, propagating out of `placeOrder` up to `main`'s own `try`/`catch`.
6. `main`'s `catch` block calls `log.warn("Order placement rejected for order-2")` — `WARN` meets the configured `WARN` threshold exactly, so this message is emitted too, appearing as the final line of output. The net effect: only `ERROR` and `WARN` messages from `OrderServiceAdvanced` are visible in this run, entirely due to `logback.xml`'s configuration, without a single line of the Java source code needing to change.

## 7. Gotchas & takeaways

> **Gotcha:** string concatenation inside a log call (`log.debug("value: " + expensiveToString())`) defeats SLF4J's lazy-evaluation benefit — the concatenation (and any expensive method call within it) happens unconditionally *before* the log call even runs, regardless of whether `DEBUG` is enabled. Always use the `{}` substitution syntax (`log.debug("value: {}", expensiveToString())`) so the argument evaluation can, in principle, be deferred or skipped when the level check fails.

- SLF4J is a facade: application and library code logs against its `Logger` interface, and a chosen binding (Logback, Log4j2) at the application's own classpath handles the actual output — giving one unified configuration point regardless of how many different libraries are logging through it.
- Log levels (`ERROR`, `WARN`, `INFO`, `DEBUG`, `TRACE`) let output be filtered by severity, configurable per logger (often per class or package) without touching application code.
- Parameterized logging (`log.info("... {}", value)`) defers message formatting until the level check confirms the message will actually be emitted, avoiding wasted work for suppressed log levels.
- Passing a `Throwable` as the final argument to a log call (rather than just its message string) includes the full stack trace in the output — essential for actually diagnosing the root cause of a logged error later.
- Configuration files (`logback.xml`, `log4j2.xml`) control output destination, format, and per-logger level thresholds entirely separately from application code — the same compiled application can log verbosely in one environment and quietly in another purely through configuration.
- Reserve `ERROR` for genuine failures needing attention, `WARN` for recoverable-but-notable situations, `INFO` for significant lifecycle events, and `DEBUG`/`TRACE` for detail only useful while actively diagnosing a specific problem — misusing levels (logging routine operations at `ERROR`, for instance) trains people to ignore genuinely important alerts.
