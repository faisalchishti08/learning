---
card: spring-boot
gi: 2
slug: convention-over-configuration-philosophy
title: Convention over configuration philosophy
---

## 1. What it is

**Convention over configuration** (CoC) is a software design principle that says: *provide sensible defaults so developers only need to specify what's different from the norm.* If you follow the convention, you write no configuration at all. If you deviate, you configure just the deviation.

Spring Boot applies this everywhere:

- Your application starts on **port 8080** by default. Change it only if 8080 doesn't work.
- An in-memory H2 database is auto-configured when H2 is on the classpath. Point to a real database only when you need one.
- Log level is `INFO` by default. Set `DEBUG` only for noisy diagnostic sessions.
- Static files served from `src/main/resources/static`. Move them only if your structure differs.

The convention is the implicit contract. Configuration is the explicit override.

## 2. Why & when

The alternative to CoC is **explicit configuration**: specify everything, even the obvious parts. Early Java EE and early Spring required this — XML files hundreds of lines long that described obvious things like "yes, create a DataSource bean, yes, connect it to this pool, yes, wire it into the persistence layer."

This created problems:
- New developers spent days understanding setup before touching business logic.
- Config files diverged between environments (dev, staging, prod) creating subtle bugs.
- Version upgrades required hunting across config files for incompatibilities.

Convention over configuration matters **most at the start of a project** and **whenever you add a new dependency**. When you add `spring-boot-starter-data-redis`, for example, Spring Boot immediately knows how to configure a Redis connection pool — you only write config if your Redis isn't at `localhost:6379`.

## 3. Core concept

Think of CoC like a new employee starting a job. Company convention says meetings start at 09:00, replies within 24 hours, code reviews need two approvals. The employee follows all of this *automatically* without asking each time. They only need to be told when *their situation* differs — "your team works in UTC+5, so your 09:00 is different."

In Spring Boot, the "company" is the framework and its conventions. Your `application.properties` file is the memo you write only when *your situation* differs.

The mechanism has three layers:

1. **Default values** — built into auto-configuration classes (e.g., `ServerProperties` defaults `server.port` to `8080`).
2. **Property binding** — any `application.properties` or `application.yml` entry overrides the default.
3. **Bean override** — if you declare your own `@Bean` of the same type Spring Boot would auto-configure, yours wins and the auto-configured one is skipped entirely.

Precedence (lowest to highest):
```
defaults → application.properties → environment variables → command-line args
```

Command-line args beat environment variables beat property files beat defaults. This means the same JAR can behave differently in each environment without code changes.

## 4. Diagram

<svg viewBox="0 0 660 240" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Convention over configuration override pyramid showing defaults at the base and command-line args at the top">
  <!-- Pyramid layers, bottom to top -->
  <!-- Layer 1: defaults (widest) -->
  <polygon points="330,220 60,220 120,180 540,180" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="330" y="207" fill="#8b949e" font-size="12" text-anchor="middle" font-family="sans-serif">Spring Boot Defaults (port 8080, H2 DB, INFO log…)</text>

  <!-- Layer 2: application.properties -->
  <polygon points="330,176 120,176 180,136 480,136" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="330" y="162" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">application.properties / application.yml</text>

  <!-- Layer 3: env vars -->
  <polygon points="330,132 180,132 240,92 420,92" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="330" y="118" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">Environment Variables</text>

  <!-- Layer 4: command-line (narrowest, top) -->
  <polygon points="330,88 240,88 300,48 360,48" fill="#6db33f" stroke="#6db33f" stroke-width="1.5"/>
  <text x="330" y="74" fill="#1c2430" font-size="11" font-weight="bold" text-anchor="middle" font-family="sans-serif">CLI args</text>

  <!-- "wins" label -->
  <text x="420" y="68" fill="#6db33f" font-size="11" font-family="sans-serif">← highest priority</text>
  <text x="560" y="207" fill="#8b949e" font-size="11" font-family="sans-serif">← lowest priority</text>
</svg>

Each layer overrides only what it specifies; everything else falls through to the layer below.

## 5. Runnable example

```java
// File: ConventionDemo.java
// Pure Java 17 demo — shows the CoC idea without a Spring dependency.
// Run: java ConventionDemo.java

public class ConventionDemo {

    // Simulates a "configurable server" that uses conventions as defaults
    static class Server {
        private final int port;
        private final String logLevel;
        private final String dbUrl;

        // Convention constructor — sensible defaults
        Server() {
            this(8080, "INFO", "jdbc:h2:mem:testdb");
        }

        // Configuration constructor — caller overrides only what differs
        Server(int port, String logLevel, String dbUrl) {
            this.port = port;
            this.logLevel = logLevel;
            this.dbUrl = dbUrl;
        }

        void describe() {
            System.out.println("port     = " + port);
            System.out.println("logLevel = " + logLevel);
            System.out.println("dbUrl    = " + dbUrl);
        }
    }

    public static void main(String[] args) {
        System.out.println("=== Convention (no config written) ===");
        new Server().describe();

        System.out.println();
        System.out.println("=== Override only what differs ===");
        // Only changed the port; log level and DB are still conventional
        new Server(9090, "INFO", "jdbc:h2:mem:testdb").describe();

        System.out.println();
        System.out.println("=== Full override for production ===");
        new Server(443, "WARN", "jdbc:postgresql://prod-db:5432/myapp").describe();
    }
}
```

**How to run:** `java ConventionDemo.java` (JDK 17+, no dependencies needed).

Expected output:
```
=== Convention (no config written) ===
port     = 8080
logLevel = INFO
dbUrl    = jdbc:h2:mem:testdb

=== Override only what differs ===
port     = 9090
logLevel = INFO
dbUrl    = jdbc:h2:mem:testdb

=== Full override for production ===
port     = 443
logLevel = WARN
dbUrl    = jdbc:postgresql://prod-db:5432/myapp
```

## 6. Walkthrough

- **No-arg `Server()`** — the convention constructor hard-codes the agreed defaults. A developer who follows conventions never calls anything else and writes zero config. This is exactly what Spring Boot's auto-configuration does: it has a "no-arg" path that works for the common case.
- **Three-arg `Server(port, logLevel, dbUrl)`** — the override path. Notice the second example only changed the port, but had to repeat `"INFO"` and the H2 URL — because Java constructors have no named defaults. In Spring Boot, `application.properties` is better: `server.port=9090` changes only the port; everything else stays conventional.
- **Third call** — production overrides every value. Same code, different runtime behaviour. This mirrors how the same Spring Boot JAR runs on dev with H2 and on prod with PostgreSQL — only the config changes, not the binary.

The important lesson: **the convention path is the short path.** You write more code/config only when you diverge. The framework earns its keep by making the common case require nothing.

## 7. Gotchas & takeaways

> **"Convention" doesn't mean "magic you can't see."** Every Spring Boot default is documented, and every auto-configuration class has `@ConditionalOn*` annotations that explain exactly when it fires. Run your app with `--debug` to get a "conditions report" printed to the console showing every auto-config that was applied or skipped and why.

> **CoC only works if you know the conventions.** Spend time with the Spring Boot reference doc's "Common Application Properties" page. Guessing a property name and getting it wrong means the default silently wins — no error. Use the IDE's property completion (Spring Tools 4 or IntelliJ Ultimate) to discover valid keys.

- Convention = default that fires when nothing is specified. Configuration = explicit override.
- The same JAR can run in dev (H2, DEBUG logs, port 8080) and prod (PostgreSQL, WARN logs, port 443) via property files or env vars — no recompile.
- Priority order: CLI args > env vars > application.properties > defaults.
- Start every Spring Boot project by using the defaults; add `application.properties` entries only when a default doesn't fit.
- `--debug` flag prints the auto-configuration conditions report — invaluable when something isn't wiring up as expected.
