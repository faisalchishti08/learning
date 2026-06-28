---
card: spring-boot
gi: 61
slug: externalized-configuration-overview
title: Externalized configuration overview
---

## 1. What it is

**Externalized configuration** is the practice of keeping all environment-specific values — database URLs, server ports, feature flags, API keys — *outside* your compiled application artifact and supplying them at runtime through files, environment variables, or command-line arguments.

Spring Boot has first-class support for this. You write `${db.url}` in your code; Spring Boot resolves the actual value from wherever it was supplied — a local `application.properties`, a Kubernetes `ConfigMap`, a CI environment variable — without you changing a line of source code.

The core promise: **one JAR, many environments.**

## 2. Why & when

Before externalized configuration, teams either:

- Hard-coded values — changing an IP address meant a new build and deploy.
- Maintained separate source branches per environment — merging nightmares, drift, and secrets in version control.

Externalized config solves all of that:

- **Same artifact in every environment.** Build once, promote through dev → staging → prod by changing only config, not code.
- **Secrets stay out of source control.** DB passwords live in environment variables or a secrets manager, not in `git blame`.
- **Faster iteration.** A support engineer can flip a flag or point at a different DB without touching Java.
- **12-Factor App compliance.** Factor III ("Config") explicitly requires this separation.

You use it from day one on every real project. Even a toy app benefits: the server port, log level, and any third-party URL are all environment-specific.

## 3. Core concept

Think of your application as a **vending machine**. The vending machine's logic (dispense item, take money) never changes. But the *prices* are written on a card slotted into the front panel. Swap the card, and the machine charges differently — no factory visit required. Externalized config is that swappable card.

Spring Boot assembles a unified **`Environment`** object at startup by consulting multiple **property sources** in a fixed priority order:

```
CLI arguments              ← highest priority
SPRING_APPLICATION_JSON
OS environment variables
application.properties
@PropertySource annotations
Default values             ← lowest priority
```

Every `${key}` expression in your `@Value` annotation or `@ConfigurationProperties` class is resolved against this merged view. If the same key appears in two sources, the higher-priority source wins. Lower-priority sources fill in values that higher sources omit — they complement each other rather than replacing each other wholesale.

This layered design lets you:

- Keep sensible defaults in `application.properties` (checked into git).
- Override just the DB URL via an environment variable in production.
- Do a one-off port change with a CLI flag during local testing — without touching any file.

## 4. Diagram

<svg viewBox="0 0 680 320" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Layered property sources feeding into the Spring Environment">
  <defs>
    <marker id="arr61" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto">
      <path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/>
    </marker>
  </defs>

  <!-- Source layers (left column) -->
  <rect x="20" y="20"  width="220" height="38" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="130" y="44" fill="#e6edf3" font-size="13" text-anchor="middle" font-family="sans-serif">CLI args  --server.port=9090</text>

  <rect x="20" y="72"  width="220" height="38" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="130" y="96" fill="#e6edf3" font-size="13" text-anchor="middle" font-family="sans-serif">SPRING_APPLICATION_JSON</text>

  <rect x="20" y="124" width="220" height="38" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="130" y="148" fill="#e6edf3" font-size="13" text-anchor="middle" font-family="sans-serif">OS env vars  DB_URL=...</text>

  <rect x="20" y="176" width="220" height="38" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="130" y="200" fill="#e6edf3" font-size="13" text-anchor="middle" font-family="sans-serif">application.properties / .yml</text>

  <rect x="20" y="228" width="220" height="38" rx="7" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="130" y="252" fill="#8b949e" font-size="13" text-anchor="middle" font-family="sans-serif">@PropertySource / defaults</text>

  <!-- Priority label -->
  <text x="130" y="285" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">▲ higher priority</text>
  <text x="130" y="300" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">▼ lower priority</text>

  <!-- Arrows to Environment -->
  <line x1="244" y1="39"  x2="380" y2="160" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr61)"/>
  <line x1="244" y1="91"  x2="380" y2="160" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr61)"/>
  <line x1="244" y1="143" x2="380" y2="160" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr61)"/>
  <line x1="244" y1="195" x2="380" y2="160" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr61)"/>
  <line x1="244" y1="247" x2="380" y2="160" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr61)"/>

  <!-- Environment box -->
  <rect x="380" y="120" width="160" height="80" rx="10" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="460" y="155" fill="#6db33f" font-size="14" font-weight="bold" text-anchor="middle" font-family="sans-serif">Environment</text>
  <text x="460" y="175" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">(merged view)</text>

  <!-- Arrow to App -->
  <line x1="544" y1="160" x2="630" y2="160" stroke="#79c0ff" stroke-width="2" marker-end="url(#arr61)"/>
  <rect x="630" y="135" width="40" height="50" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="650" y="165" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">App</text>
</svg>

*All property sources are merged into one `Environment` object. The app reads from there — it never knows which source provided each value.*

## 5. Runnable example

```java
// ExternalConfigDemo.java
// Run: java ExternalConfigDemo.java
// Then try: SERVER_PORT=9090 java ExternalConfigDemo.java
// Or:       java ExternalConfigDemo.java --server.port=9091

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.core.env.Environment;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

@SpringBootApplication
@RestController
public class ExternalConfigDemo {

    private final Environment env;

    public ExternalConfigDemo(Environment env) {
        this.env = env;
    }

    // Visit http://localhost:<port>/config after startup
    @GetMapping("/config")
    public String showConfig() {
        return "server.port = " + env.getProperty("server.port")
             + " | spring.application.name = "
             + env.getProperty("spring.application.name", "(not set)");
    }

    public static void main(String[] args) {
        SpringApplication.run(ExternalConfigDemo.class, args);
    }
}
```

`src/main/resources/application.properties`:
```properties
server.port=8080
spring.application.name=demo
```

**How to run:** standard Spring Boot Maven/Gradle project. Run `./mvnw spring-boot:run`, then visit `http://localhost:8080/config`. Change the port without touching code: `SERVER_PORT=9090 ./mvnw spring-boot:run` (env var) or `./mvnw spring-boot:run -Dspring-boot.run.arguments=--server.port=9091` (CLI arg).

## 6. Walkthrough

1. `application.properties` sets `server.port=8080` — the baseline default that lives in source control.
2. When `SERVER_PORT=9090` is set in the shell, Spring Boot's relaxed-binding maps the env var name to `server.port` and the env var wins (higher precedence than the file).
3. `Environment env` is injected by Spring's DI system. It represents the fully merged property view — the app asks `env.getProperty("server.port")` and gets whichever source provided the value.
4. The `/config` endpoint exposes both values so you can verify which source won without restarting.
5. `getProperty("spring.application.name", "(not set)")` shows the two-arg form: the second argument is a **default** returned when no source defines the key — this is how you express "optional config with a sensible fallback."

## 7. Gotchas & takeaways

> Never hard-code environment-specific values in Java source. The moment you do, you need a new build for every environment. Use `${my.key}` and supply the value externally.

> Environment variable names follow a relaxed-binding convention: `SERVER_PORT` maps to `server.port`, `SPRING_DATASOURCE_URL` maps to `spring.datasource.url`. Upper-case with underscores is the shell-safe form of dot-separated property names.

- Spring Boot builds a single `Environment` from many property sources; your code reads from it transparently.
- Sources have a strict priority order — CLI args beat env vars beat files beat defaults.
- A lower-priority source fills in keys the higher source omits. They stack, they don't replace.
- Keeping defaults in `application.properties` (in git) is good practice — it documents all knobs the app supports.
- Secrets (passwords, API keys) should never live in files committed to git; use env vars or a secrets manager instead.
