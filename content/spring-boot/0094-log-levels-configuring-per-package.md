---
card: spring-boot
gi: 94
slug: log-levels-configuring-per-package
title: Log levels & configuring per-package
---

## 1. What it is

Log levels are a hierarchy of verbosity used to filter log output. From most verbose to most critical:

```
TRACE < DEBUG < INFO < WARN < ERROR < OFF
```

Setting a level means "show this level **and everything above it**." Setting `INFO` shows `INFO`, `WARN`, and `ERROR`, but not `DEBUG` or `TRACE`.

In Spring Boot you configure log levels via properties:

```properties
# Root logger — applies to everything not more specifically configured
logging.level.root=WARN

# Per-package or per-class
logging.level.com.example=DEBUG
logging.level.com.example.payment=TRACE
logging.level.org.springframework.web=DEBUG
logging.level.org.hibernate.SQL=DEBUG
logging.level.org.hibernate.orm.jdbc.bind=TRACE
```

The most specific match wins: a class in `com.example.payment` uses `TRACE`; a class in `com.example.cart` uses `DEBUG` (from the `com.example` rule); a Spring class uses `WARN` (from `root`).

## 2. Why & when

Log levels are your primary noise-to-signal knob. In production, `root=WARN` keeps logs quiet and cheap. When debugging an issue, you temporarily raise the level for just the relevant package — not the entire application.

Concrete scenarios:
- **Slow SQL**: set `logging.level.org.hibernate.SQL=DEBUG` to see every query and its bind parameters.
- **Auth failures**: set `logging.level.org.springframework.security=DEBUG` to trace the security filter chain.
- **HTTP requests**: set `logging.level.org.springframework.web.servlet.DispatcherServlet=DEBUG`.
- **Your code only**: set `logging.level.com.example=DEBUG` and `root=WARN` so third-party noise stays silent.

Per-package configuration is vastly more targeted than the all-or-nothing `logging.level.root=DEBUG`, which can produce hundreds of thousands of lines per second from Hibernate, Spring, and Netty internals combined.

## 3. Core concept

Loggers form a tree mirroring the Java package hierarchy. Every logger inherits the effective level of its nearest configured ancestor:

```
root                     WARN    (explicit)
└─ com                   WARN    (inherited)
   └─ example            DEBUG   (explicit)
      ├─ service         DEBUG   (inherited)
      └─ payment         TRACE   (explicit — overrides parent)
         └─ PayService   TRACE   (inherited)
```

Spring Boot also supports the special name `ROOT` in place of `root`. Both are case-insensitive.

At runtime, log levels can be changed via **Spring Boot Actuator** without restarting:
```bash
# Read current level
curl http://localhost:8080/actuator/loggers/com.example

# Change level at runtime
curl -X POST http://localhost:8080/actuator/loggers/com.example \
     -H "Content-Type: application/json" \
     -d '{"configuredLevel":"DEBUG"}'
```

## 4. Diagram

<svg viewBox="0 0 680 280" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Logger hierarchy tree showing level inheritance from root down through packages">
  <rect x="8" y="8" width="664" height="264" rx="12" fill="#161b22" stroke="#30363d" stroke-width="1"/>
  <text x="340" y="33" fill="#e6edf3" font-size="14" text-anchor="middle" font-family="sans-serif" font-weight="bold">Logger Level Hierarchy</text>

  <!-- Root -->
  <rect x="270" y="48" width="140" height="36" rx="5" fill="#1c2430" stroke="#f85149" stroke-width="2"/>
  <text x="340" y="62" fill="#f85149" font-size="10" text-anchor="middle" font-family="monospace">root</text>
  <text x="340" y="77" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="monospace">WARN (explicit)</text>

  <!-- Lines -->
  <defs><marker id="lh" markerWidth="7" markerHeight="7" refX="5" refY="3" orient="auto"><path d="M0,0 L5,3 L0,6 Z" fill="#8b949e"/></marker></defs>
  <line x1="290" y1="84" x2="160" y2="115" stroke="#8b949e" stroke-width="1" marker-end="url(#lh)"/>
  <line x1="340" y1="84" x2="340" y2="115" stroke="#8b949e" stroke-width="1" marker-end="url(#lh)"/>
  <line x1="390" y1="84" x2="520" y2="115" stroke="#8b949e" stroke-width="1" marker-end="url(#lh)"/>

  <!-- org.springframework -->
  <rect x="60" y="117" width="200" height="36" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="160" y="131" fill="#8b949e" font-size="10" text-anchor="middle" font-family="monospace">org.springframework</text>
  <text x="160" y="146" fill="#8b949e" font-size="10" text-anchor="middle" font-family="monospace">WARN (inherited)</text>

  <!-- com.example -->
  <rect x="270" y="117" width="140" height="36" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="340" y="131" fill="#6db33f" font-size="10" text-anchor="middle" font-family="monospace">com.example</text>
  <text x="340" y="146" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="monospace">DEBUG (explicit)</text>

  <!-- org.hibernate -->
  <rect x="420" y="117" width="200" height="36" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="520" y="131" fill="#8b949e" font-size="10" text-anchor="middle" font-family="monospace">org.hibernate</text>
  <text x="520" y="146" fill="#8b949e" font-size="10" text-anchor="middle" font-family="monospace">WARN (inherited)</text>

  <!-- Children of com.example -->
  <line x1="310" y1="153" x2="200" y2="185" stroke="#8b949e" stroke-width="1" marker-end="url(#lh)"/>
  <line x1="370" y1="153" x2="460" y2="185" stroke="#8b949e" stroke-width="1" marker-end="url(#lh)"/>

  <rect x="100" y="187" width="200" height="36" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="200" y="201" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="monospace">com.example.service</text>
  <text x="200" y="216" fill="#6db33f" font-size="10" text-anchor="middle" font-family="monospace">DEBUG (inherited)</text>

  <rect x="350" y="187" width="220" height="36" rx="5" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="460" y="201" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="monospace">com.example.payment</text>
  <text x="460" y="216" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="monospace">TRACE (explicit)</text>

  <!-- Legend -->
  <rect x="20" y="240" width="200" height="24" rx="4" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="120" y="256" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">explicit = set in application.properties; inherited = from parent</text>
</svg>

Most-specific logger wins; others inherit upward. Set `root=WARN`, tune sub-packages as needed.

## 5. Runnable example

```java
// LogLevels.java — run: java LogLevels.java  (JDK 17+)
// Simulates the logger hierarchy and level-inheritance logic.

import java.util.*;

public class LogLevels {

    enum Level { TRACE, DEBUG, INFO, WARN, ERROR, OFF }

    static class Logger {
        final String name;
        Level configured;   // null = inherited
        Logger parent;

        Logger(String name, Level configured, Logger parent) {
            this.name = name;
            this.configured = configured;
            this.parent = parent;
        }

        Level effective() {
            if (configured != null) return configured;
            return (parent != null) ? parent.effective() : Level.WARN;
        }

        boolean isEnabled(Level l) { return l.ordinal() >= effective().ordinal(); }

        void log(Level l, String msg) {
            if (isEnabled(l))
                System.out.printf("[%-5s] [%-35s] %s%n", l, name, msg);
        }
    }

    public static void main(String[] args) {
        // Simulates application.properties:
        //   logging.level.root=WARN
        //   logging.level.com.example=DEBUG
        //   logging.level.com.example.payment=TRACE

        Logger root       = new Logger("root",                   Level.WARN,  null);
        Logger comExample = new Logger("com.example",            Level.DEBUG, root);
        Logger service    = new Logger("com.example.service",    null,        comExample); // inherited
        Logger payment    = new Logger("com.example.payment",    Level.TRACE, comExample);
        Logger orgSpring  = new Logger("org.springframework",    null,        root);       // inherited WARN
        Logger hibernSql  = new Logger("org.hibernate.SQL",      Level.DEBUG, root);       // explicit

        System.out.println("Effective levels:");
        for (Logger l : List.of(root, comExample, service, payment, orgSpring, hibernSql))
            System.out.printf("  %-35s → %s%n", l.name, l.effective());

        System.out.println("\n--- Log output simulation ---");
        service.log(Level.DEBUG, "Entering processCart()");           // DEBUG ≥ DEBUG → printed
        service.log(Level.TRACE, "Internal cart state dump");         // TRACE < DEBUG → suppressed
        payment.log(Level.TRACE, "Entering charge()");                // TRACE ≥ TRACE → printed
        payment.log(Level.INFO,  "Payment of $99 authorised");        // INFO ≥ TRACE → printed
        orgSpring.log(Level.DEBUG, "DispatcherServlet doDispatch");   // DEBUG < WARN → suppressed
        orgSpring.log(Level.WARN,  "Exception mapping failed");       // WARN ≥ WARN → printed
        hibernSql.log(Level.DEBUG, "select * from orders where id=?"); // DEBUG ≥ DEBUG → printed
    }
}
```

**How to run:** `java LogLevels.java`

## 6. Walkthrough

- `effective()` walks up the parent chain until it finds an explicitly configured level, or returns `WARN` at root. This mirrors how Logback's `ch.qos.logback.classic.Logger.getEffectiveLevel()` works.
- `service` has `null` configured level → inherits `DEBUG` from `comExample`. This means adding `logging.level.com.example=DEBUG` automatically enables debug logging for every class in the `com.example` package tree.
- `payment` has `Level.TRACE` explicit — overrides the parent `DEBUG`. This is the "drill down" pattern: set `DEBUG` on the package, `TRACE` only on the sub-package you are actively investigating.
- `orgSpring.log(Level.DEBUG, …)` — `DEBUG < WARN`, so it's suppressed. In production, all Spring framework `DEBUG` chatter is silent. Only `WARN` and `ERROR` from Spring surface.
- `hibernSql.log(Level.DEBUG, …)` — `org.hibernate.SQL` is explicitly set to `DEBUG` (to show queries). Without this, Hibernate's SQL is invisible even when your own code is at `DEBUG`.
- The effective-level printout at the top maps directly to what Actuator's `/actuator/loggers` endpoint shows.

## 7. Gotchas & takeaways

> **`logging.level.root=DEBUG` in production is a performance disaster.** It enables debug logging for Hibernate (every bind parameter), Netty (every network buffer), Spring Security (every filter decision), and every third-party library. You can easily produce millions of log lines per minute. Always set `root=WARN` or `root=INFO` in production.

> **Level changes via Actuator are runtime-only.** They reset to the configured levels on application restart. For permanent changes, update `application.properties` and restart (or push a config update if using Spring Cloud Config).

- Set `logging.level.root=WARN` and only enable `DEBUG` for your own packages (`logging.level.com.yourcompany=DEBUG`).
- `org.hibernate.SQL=DEBUG` shows SQL statements; `org.hibernate.orm.jdbc.bind=TRACE` shows bind parameter values. Both together reveal full query context.
- `org.springframework.web=DEBUG` logs every request mapping and view resolution — useful when troubleshooting 404s or wrong controller routing.
- In tests, add `@TestPropertySource(properties = "logging.level.com.example=DEBUG")` to enable per-test debug output without polluting other test configurations.
- The Actuator `/actuator/loggers` GET endpoint lists every registered logger and its current effective level — indispensable for production diagnosis.
