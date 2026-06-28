---
card: spring-boot
gi: 199
slug: loggers-endpoint-runtime-log-level-changes
title: Loggers endpoint (runtime log-level changes)
---

## 1. What it is

The `/actuator/loggers` endpoint lets you **read and change the log level of any logger at runtime** — no restart, no redeploy. A `GET` request lists all loggers and their current levels. A `POST` request changes a specific logger's level immediately. When you're done debugging, `POST` again to reset. Spring Boot wires this endpoint for Logback and Log4j 2 automatically when `starter-actuator` is present.

## 2. Why & when

The classic debugging dilemma: production is misbehaving, but `INFO` logs don't show enough detail. Redeploying with `DEBUG` takes time and triggers rolling restarts. With the loggers endpoint you can:
1. `POST /actuator/loggers/com.example.payments` `{"configuredLevel":"DEBUG"}` — see debug logs immediately.
2. Reproduce the issue.
3. `POST /actuator/loggers/com.example.payments` `{"configuredLevel":"INFO"}` — reset.

This is the most practically useful Actuator endpoint for incident response.

## 3. Core concept

`GET /actuator/loggers` returns:
```json
{
  "levels": ["TRACE","DEBUG","INFO","WARN","ERROR","FATAL","OFF"],
  "loggers": {
    "ROOT": { "configuredLevel": "INFO", "effectiveLevel": "INFO" },
    "com.example": { "configuredLevel": null, "effectiveLevel": "INFO" },
    "com.example.payments": { "configuredLevel": "DEBUG", "effectiveLevel": "DEBUG" }
  }
}
```

`GET /actuator/loggers/{name}` — single logger details.

`POST /actuator/loggers/{name}` with body `{"configuredLevel": "DEBUG"}` — changes the level.

`POST /actuator/loggers/{name}` with body `{"configuredLevel": null}` — resets to inherited level (inherits from parent logger).

Key concepts:
- **`configuredLevel`**: explicitly set level (null = not set, inherits).
- **`effectiveLevel`**: the level actually used (configured level or nearest ancestor's level).
- Changes are **live immediately** — no bean refresh, no restart.
- Changes are **not persistent** — a restart resets all loggers to `logback-spring.xml` configuration.

## 4. Diagram

<svg viewBox="0 0 680 195" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Ops engineer POSTs log level change to /actuator/loggers; Logback applies it immediately; GET confirms new level">
  <!-- Ops -->
  <rect x="10" y="75" width="110" height="50" rx="8" fill="#0d1117" stroke="#8b949e" stroke-width="1.5"/>
  <text x="65" y="97" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif" font-weight="bold">Ops / Dev</text>
  <text x="65" y="113" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">curl / Grafana</text>

  <!-- POST arrow -->
  <line x1="123" y1="88" x2="218" y2="88" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#lga)"/>
  <text x="170" y="81" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">POST {level:DEBUG}</text>

  <!-- GET arrow -->
  <line x1="123" y1="115" x2="218" y2="115" stroke="#6db33f" stroke-width="1.5" marker-end="url(#lgb)"/>
  <text x="170" y="128" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">GET → {effectiveLevel:DEBUG}</text>

  <!-- Actuator -->
  <rect x="223" y="58" width="155" height="82" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="300" y="78" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif" font-weight="bold">/actuator/loggers</text>
  <text x="300" y="95" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">LoggersEndpoint</text>
  <text x="300" y="111" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">calls setLogLevel()</text>
  <text x="300" y="126" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">on LoggingSystem</text>

  <!-- Arrow to Logback -->
  <line x1="381" y1="100" x2="444" y2="100" stroke="#6db33f" stroke-width="2" marker-end="url(#lgb)"/>

  <!-- Logback -->
  <rect x="449" y="62" width="145" height="75" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="521" y="82" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif" font-weight="bold">Logback</text>
  <text x="521" y="98" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">Logger hierarchy</text>
  <text x="521" y="113" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">com.example.payments</text>
  <text x="521" y="127" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">level=DEBUG (live)</text>

  <!-- App logs -->
  <line x1="596" y1="100" x2="650" y2="100" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#lga)"/>
  <rect x="654" y="80" width="20" height="40" rx="4" fill="#1c2430" stroke="#79c0ff" stroke-width="1"/>
  <text x="664" y="104" fill="#79c0ff" font-size="7" text-anchor="middle" font-family="sans-serif" writing-mode="tb">DEBUG logs</text>

  <text x="340" y="177" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Level change is immediate; survives until next restart (not persistent)</text>

  <defs>
    <marker id="lga" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#79c0ff"/></marker>
    <marker id="lgb" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>
</svg>

POST changes the Logback logger level in the live JVM; GET confirms the new effective level.

## 5. Runnable example

```java
// LoggersEndpointDemo.java — simulates runtime log-level management
// How to run: java LoggersEndpointDemo.java  (JDK 17+, no dependencies)
// Real Spring Boot: POST /actuator/loggers/{name} with {"configuredLevel":"DEBUG"}

import java.util.*;

public class LoggersEndpointDemo {

    enum Level { TRACE, DEBUG, INFO, WARN, ERROR, OFF }

    // Simulates Logback's logger hierarchy
    static final Map<String, Level> configuredLevels = new LinkedHashMap<>();

    static {
        configuredLevels.put("ROOT", Level.INFO);
        // sub-loggers start with null (inherit from parent)
    }

    // Find effective level by walking up the hierarchy
    static Level effectiveLevel(String loggerName) {
        Level explicit = configuredLevels.get(loggerName);
        if (explicit != null) return explicit;
        // Walk up: com.example.payments → com.example → ROOT
        int dot = loggerName.lastIndexOf('.');
        if (dot > 0) return effectiveLevel(loggerName.substring(0, dot));
        return configuredLevels.get("ROOT");
    }

    // GET /actuator/loggers
    static void getLoggers(List<String> loggerNames) {
        System.out.println("\nGET /actuator/loggers");
        System.out.printf("  %-35s %-14s %s%n", "Logger", "Configured", "Effective");
        System.out.println("  " + "-".repeat(65));
        for (String name : loggerNames) {
            Level configured = configuredLevels.get(name);
            Level effective  = effectiveLevel(name);
            System.out.printf("  %-35s %-14s %s%n", name,
                    configured != null ? configured : "(inherited)", effective);
        }
    }

    // POST /actuator/loggers/{name}
    static void setLevel(String loggerName, Level level) {
        System.out.printf("%nPOST /actuator/loggers/%s%n  body: {\"configuredLevel\":\"%s\"}%n",
                loggerName, level);
        if (level == null) {
            configuredLevels.remove(loggerName);
            System.out.println("  => Level reset (will inherit from parent)");
        } else {
            configuredLevels.put(loggerName, level);
            System.out.println("  => 204 No Content (applied immediately)");
        }
    }

    // Simulate log output at various levels
    static void simulateLog(String logger, String message, Level logLevel) {
        Level eff = effectiveLevel(logger);
        boolean wouldLog = logLevel.ordinal() >= eff.ordinal();
        System.out.printf("  [%s] %s: %s  %s%n",
                logLevel, logger.replaceAll("com\\.example\\.", ""), message,
                wouldLog ? "✓ logged" : "✗ suppressed");
    }

    public static void main(String[] args) {
        System.out.println("=== Loggers Endpoint (Runtime Log-level Changes) Demo ===");

        List<String> allLoggers = List.of(
            "ROOT", "com.example", "com.example.payments", "com.example.orders",
            "org.hibernate.SQL", "org.springframework.web"
        );

        getLoggers(allLoggers);

        System.out.println("\n--- Before debug: simulate log output ---");
        simulateLog("com.example.payments", "Processing payment #P99", Level.DEBUG);
        simulateLog("com.example.payments", "Payment failed!", Level.ERROR);

        // Enable DEBUG for payments package
        setLevel("com.example.payments", Level.DEBUG);
        getLoggers(allLoggers);

        System.out.println("\n--- After enabling DEBUG for payments ---");
        simulateLog("com.example.payments", "Processing payment #P99", Level.DEBUG);
        simulateLog("com.example.payments", "Payment gateway response: {status:declined}", Level.DEBUG);
        simulateLog("com.example.payments", "Payment failed!", Level.ERROR);

        // Enable SQL logging for query debugging
        setLevel("org.hibernate.SQL", Level.DEBUG);
        System.out.println("\n--- After enabling Hibernate SQL logging ---");
        simulateLog("org.hibernate.SQL", "select p.* from payments p where p.id=?", Level.DEBUG);

        // Reset payments logger
        setLevel("com.example.payments", null);
        System.out.println("\n--- After resetting payments logger ---");
        simulateLog("com.example.payments", "Processing payment #P100", Level.DEBUG);

        System.out.println("\n--- curl commands ---");
        System.out.println("# List all loggers");
        System.out.println("curl http://localhost:8080/actuator/loggers");
        System.out.println("# Enable DEBUG for a package");
        System.out.println("curl -X POST -H 'Content-Type: application/json' \\");
        System.out.println("     -d '{\"configuredLevel\":\"DEBUG\"}' \\");
        System.out.println("     http://localhost:8080/actuator/loggers/com.example.payments");
        System.out.println("# Reset (inherit from parent)");
        System.out.println("curl -X POST -H 'Content-Type: application/json' \\");
        System.out.println("     -d '{\"configuredLevel\":null}' \\");
        System.out.println("     http://localhost:8080/actuator/loggers/com.example.payments");
    }
}
```

**How to run:** `java LoggersEndpointDemo.java`

## 6. Walkthrough

- **`effectiveLevel`** walks up the dotted logger hierarchy — `com.example.payments` inherits from `com.example` which inherits from `ROOT`. This mirrors how Logback's logger hierarchy works.
- **Before enabling DEBUG**: `DEBUG` log at `com.example.payments` is suppressed (effective level is `INFO` from `ROOT`).
- **`setLevel("com.example.payments", DEBUG)`**: immediately changes the effective level for that package. The `com.example.payments.DEBUG` log now appears; `com.example.orders` is unaffected.
- **`org.hibernate.SQL` DEBUG**: enables Hibernate SQL logging — invaluable for "why is this query slow?" debugging. Remember to reset it — SQL debug logging is extremely verbose.
- **Reset with `null`**: removes the explicit level, reverting to parent inheritance. `com.example.payments` goes back to `INFO`.
- The `curl` commands at the end are the real commands used in production incident response.

## 7. Gotchas & takeaways

> `POST /actuator/loggers` changes are **not persistent**. A pod restart or rolling update resets all log levels to the values in `logback-spring.xml`. For persistent changes, update the configuration file and redeploy.

> Enabling `DEBUG` or `TRACE` on a high-traffic package (`org.hibernate`, `org.springframework`) can produce **millions of log lines per second**, overwhelming log aggregation systems (Elasticsearch, Loki) and causing disk pressure. Always reset after debugging.

- Expose the endpoint: `management.endpoints.web.exposure.include=loggers`.
- Secure it: `POST /actuator/loggers` is a write operation — require an `ACTUATOR` or `ADMIN` role via `SecurityFilterChain`.
- `GET /actuator/loggers/{name}` returns just that logger: `{"configuredLevel": "DEBUG", "effectiveLevel": "DEBUG"}`.
- Logback, Log4j 2, and JUL (java.util.logging) are all supported. The endpoint delegates to Spring Boot's `LoggingSystem` abstraction.
- Automate: in CI, you can hit this endpoint to enable verbose logging during integration tests, then reset after.
