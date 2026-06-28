---
card: spring-boot
gi: 91
slug: default-logging-logback-via-commons-logging
title: Default logging (Logback via Commons Logging)
---

## 1. What it is

Spring Boot ships with **Logback** as its default logging implementation, wired in automatically through the `spring-boot-starter-logging` dependency that every starter transitively includes. You never need to configure it for basic use — add a starter, get logging.

The layering works like this:
- **Application code** calls the **SLF4J API** (Simple Logging Façade for Java), a vendor-neutral interface: `LoggerFactory.getLogger(MyClass.class)`.
- **Spring Framework** internally still uses **Commons Logging** (the original Spring logging API), but `spring-jcl` — the minimal Commons Logging re-implementation bundled with Spring 5 — bridges those calls to SLF4J at zero cost.
- **SLF4J** routes all calls to the **Logback** backend, which formats and outputs the messages.

Result: your code uses SLF4J; Spring's own code uses Commons Logging; both end up at the same Logback backend. You configure one logging system for everything.

## 2. Why & when

Spring Boot chose SLF4J + Logback because:
- SLF4J is the de facto standard façade — almost every library logs through it.
- Logback is fast, well-maintained, and was written by the original Log4j author as a direct successor.
- The SLF4J bridge pattern means older libraries that use Commons Logging, Log4j 1.x, or `java.util.logging` can all be funnelled into Logback with simple bridge JARs.

You benefit from this setup the moment you include any Spring Boot starter. You don't need to add `logback-classic` or an SLF4J binding manually — they are already on the classpath. The only reason to touch this default is if you need to switch to Log4j2 (covered in a later topic) or need a library that conflicts with Logback.

## 3. Core concept

```
Your code:        Logger log = LoggerFactory.getLogger(MyClass.class);
                               ↓ SLF4J API
Spring internals: LogFactory.getLog(Spring.class)
                               ↓ spring-jcl → SLF4J bridge
Both reach:       Logback backend
                  ├─ ConsoleAppender  → stdout
                  └─ (optional) FileAppender → log file
```

Logback is configured by Spring Boot's `base.xml` and `defaults.xml` files bundled inside `spring-boot-autoconfigure.jar`. These defaults produce the familiar console output format with colour support, timestamps, thread, log level, logger name, and message.

The `spring-boot-starter-logging` meta-dependency pulls in:
- `logback-classic` (includes `logback-core`)
- `slf4j-api`
- `log4j-to-slf4j` (bridges Log4j 2 API to SLF4J)
- `jul-to-slf4j` (bridges `java.util.logging` to SLF4J)

## 4. Diagram

<svg viewBox="0 0 680 280" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Logging stack: application code and Spring internals both funnel through SLF4J to the Logback backend">
  <rect x="8" y="8" width="664" height="264" rx="12" fill="#161b22" stroke="#30363d" stroke-width="1"/>
  <text x="340" y="33" fill="#e6edf3" font-size="14" text-anchor="middle" font-family="sans-serif" font-weight="bold">Spring Boot Default Logging Stack</text>

  <!-- App code box -->
  <rect x="40" y="50" width="230" height="44" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="155" y="69" fill="#6db33f" font-size="11" text-anchor="middle" font-family="monospace">Your code</text>
  <text x="155" y="86" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="monospace">LoggerFactory.getLogger(…)</text>

  <!-- Spring internals box -->
  <rect x="410" y="50" width="230" height="44" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="525" y="69" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="monospace">Spring internals</text>
  <text x="525" y="86" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="monospace">LogFactory.getLog(…) → spring-jcl</text>

  <!-- SLF4J -->
  <defs><marker id="dl" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker></defs>
  <line x1="155" y1="95" x2="290" y2="118" stroke="#8b949e" stroke-width="1.5" marker-end="url(#dl)"/>
  <line x1="525" y1="95" x2="390" y2="118" stroke="#8b949e" stroke-width="1.5" marker-end="url(#dl)"/>

  <rect x="200" y="120" width="280" height="40" rx="6" fill="#1c2430" stroke="#f0883e" stroke-width="2"/>
  <text x="340" y="136" fill="#f0883e" font-size="11" text-anchor="middle" font-family="monospace" font-weight="bold">SLF4J API</text>
  <text x="340" y="152" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">vendor-neutral façade</text>

  <!-- Arrow down -->
  <line x1="340" y1="161" x2="340" y2="178" stroke="#8b949e" stroke-width="1.5" marker-end="url(#dl)"/>

  <!-- Logback -->
  <rect x="150" y="180" width="380" height="50" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="340" y="200" fill="#6db33f" font-size="12" text-anchor="middle" font-family="monospace" font-weight="bold">Logback backend</text>
  <text x="250" y="220" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">ConsoleAppender → stdout</text>
  <text x="450" y="220" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">(optional FileAppender)</text>

  <!-- Label -->
  <text x="340" y="256" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">auto-configured by spring-boot-starter-logging — no setup required</text>
</svg>

All logging paths converge at Logback; you configure one system for the entire application.

## 5. Runnable example

```java
// DefaultLogging.java — run: java DefaultLogging.java  (JDK 17+, no Spring needed)
// Demonstrates SLF4J API usage and shows the abstraction layer.
// In a real Spring Boot app, Logback is auto-configured; here we print the concept.

public class DefaultLogging {

    // In a real Spring Boot project:
    //   import org.slf4j.Logger;
    //   import org.slf4j.LoggerFactory;
    //   private static final Logger log = LoggerFactory.getLogger(DefaultLogging.class);

    // Simulated logger to show the concept without adding dependencies
    static class SimLogger {
        private final String name;
        SimLogger(Class<?> clazz) { this.name = clazz.getSimpleName(); }

        void trace(String msg) { print("TRACE", msg); }
        void debug(String msg) { print("DEBUG", msg); }
        void info(String msg)  { print("INFO ", msg); }
        void warn(String msg)  { print("WARN ", msg); }
        void error(String msg) { print("ERROR", msg); }
        void info(String msg, Object... args) {
            // SLF4J-style {} parameter substitution
            for (Object a : args) msg = msg.replaceFirst("\\{}", String.valueOf(a));
            print("INFO ", msg);
        }
        private void print(String level, String msg) {
            System.out.printf("2026-06-28 10:00:00.000  %s %5d --- [main] %-40s : %s%n",
                level, ProcessHandle.current().pid(), name, msg);
        }
    }

    static final SimLogger log = new SimLogger(DefaultLogging.class);

    public static void main(String[] args) {
        // SLF4J parameterised logging — {} tokens, no string concat
        log.info("Application started");
        log.info("Processing order {} for customer {}", "ORD-42", "alice");
        log.debug("Debug detail: internal state = {}", "ready");
        log.warn("Slow response from external service");

        try {
            throw new IllegalStateException("database timeout");
        } catch (Exception e) {
            log.error("Failed to connect: " + e.getMessage());
        }

        System.out.println();
        System.out.println("Key points about Spring Boot default logging:");
        System.out.println("  • spring-boot-starter-logging is on the classpath automatically");
        System.out.println("  • LoggerFactory.getLogger(YourClass.class) — that is all you need");
        System.out.println("  • Use {} parameters, not string concatenation (deferred toString)");
        System.out.println("  • Default level for root logger: INFO");
        System.out.println("  • Spring Boot's own DEBUG output suppressed unless logging.level set");
    }
}
```

**How to run:** `java DefaultLogging.java`

In a real Spring Boot project, add `org.slf4j:slf4j-api` to your imports and let the starter provide the implementation — Logback is already there.

## 6. Walkthrough

- `SimLogger` mimics the SLF4J `Logger` interface — the real one lives in `slf4j-api.jar` and is implemented by Logback's `ch.qos.logback.classic.Logger`.
- The log format (`2026-06-28 10:00:00.000 INFO 12345 --- [main] DefaultLogging`) is Spring Boot's default Logback pattern from `defaults.xml`. Fields left-to-right: timestamp, level, PID, separator `---`, thread name, logger name (right-padded to 40 chars), colon, message.
- `log.info("Processing order {} for customer {}", "ORD-42", "alice")` — the `{}` parameter syntax defers `toString()` until the log level is active. If `INFO` is off, the string is never built. Never use `+` concatenation in log calls.
- `log.debug(…)` — in the default Spring Boot setup, `DEBUG` is below the root logger threshold (`INFO`), so this line produces no output unless `logging.level.root=DEBUG` is set.
- `log.error("Failed to connect: " + e.getMessage())` — string concatenation here is actually fine for `error` (almost always enabled), but habit says use `{}` regardless.

## 7. Gotchas & takeaways

> **Never add `logback-classic` or `slf4j-api` as direct dependencies in a Spring Boot project.** They are already on the classpath via `spring-boot-starter-logging`. Adding explicit versions can create version conflicts or duplicate bindings, producing SLF4J's dreaded "multiple bindings" warning.

> **`System.out.println` bypasses the logging system entirely.** It produces output that has no timestamp, no level, no correlation ID, and cannot be silenced by a log-level setting. Use the SLF4J logger, not `System.out`.

- `LoggerFactory.getLogger(MyClass.class)` — always pass the class, never a string, so refactoring tools update the name automatically.
- Use `{}` parameters instead of string concatenation in every log call, including `error`.
- Spring Boot's default root log level is `INFO`. Spring's own infrastructure logs at `DEBUG` and `TRACE` — enable those levels only when diagnosing framework issues.
- The logger name in the output is the fully qualified class name truncated — keep class names concise for readable logs.
- Switching implementations (to Log4j2) is a single dependency swap — because all code uses SLF4J, no application code needs to change.
