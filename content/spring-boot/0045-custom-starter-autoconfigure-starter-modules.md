---
card: spring-boot
gi: 45
slug: custom-starter-autoconfigure-starter-modules
title: Custom starter (autoconfigure + starter modules)
---

## 1. What it is

A **Spring Boot starter** is a pre-packaged dependency descriptor that bundles a library's auto-configuration, required JARs, and transitive dependencies into a single Maven/Gradle dependency. Adding one line to `pom.xml` is all it takes to fully integrate the library.

A production-quality starter is split into two modules:

| Module | Naming convention | Contents |
|---|---|---|
| `acme-spring-boot-autoconfigure` | `*-autoconfigure` | `@AutoConfiguration` class, `@Conditional` logic, `AutoConfiguration.imports` file |
| `acme-spring-boot-starter` | `*-starter` | `pom.xml` only — depends on `autoconfigure` module + the library itself |

The split keeps the autoconfigure logic independent of the starter packaging. Users can depend on just the autoconfigure module if they want finer control.

## 2. Why & when

Without a starter, library consumers must:
1. Add the library JAR.
2. Add the autoconfigure JAR.
3. Register the `@AutoConfiguration` class (or copy-paste bean definitions).
4. Manage version alignment between all these JARs.

A starter collapses all four steps to one dependency declaration. It is the reason `spring-boot-starter-web` in `pom.xml` gives you a complete, working web stack.

Write a custom starter when:
- You publish a shared library used by multiple Spring Boot services.
- You want zero-configuration integration for consumers of your library.
- You maintain an internal platform and want to standardise how services integrate with it.

## 3. Core concept

Think of a starter like a **power strip**. The autoconfigure module is the circuit inside (logic, wiring). The starter module is the outer casing with the plug (packaging, branding). Consumers plug in once and get everything connected. The circuit can also be used standalone for users who want to wire things manually.

The recommended two-module layout:

```
acme-spring-boot-starter/
└── pom.xml                    ← depends on autoconfigure + acme library

acme-spring-boot-autoconfigure/
├── src/main/java/
│   └── com/acme/AcmeAutoConfiguration.java   (@AutoConfiguration class)
└── src/main/resources/
    └── META-INF/spring/
        └── org.springframework.boot.autoconfigure.AutoConfiguration.imports
            → com.acme.AcmeAutoConfiguration
```

Naming rules from the Spring Boot documentation:
- Third-party starters: `acme-spring-boot-starter` (library name first).
- Spring's own starters: `spring-boot-starter-*` (Spring name first).
- Do **not** start your starter with `spring-boot-starter-` — that prefix is reserved for official Spring starters.

## 4. Diagram

<svg viewBox="0 0 660 260" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Custom starter two-module layout: autoconfigure module and starter module consumed by an app">
  <!-- Autoconfigure module -->
  <rect x="20" y="20" width="220" height="180" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="130" y="46" fill="#6db33f" font-size="11" font-family="monospace" text-anchor="middle" font-weight="bold">acme-autoconfigure.jar</text>
  <rect x="36" y="58" width="188" height="40" rx="5" fill="#2d3748" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="130" y="76" fill="#79c0ff" font-size="10" font-family="monospace" text-anchor="middle">AcmeAutoConfiguration.java</text>
  <text x="130" y="92" fill="#8b949e" font-size="9" font-family="monospace" text-anchor="middle">@AutoConfiguration + @Conditional</text>
  <rect x="36" y="108" width="188" height="42" rx="5" fill="#2d3748" stroke="#8b949e" stroke-width="1"/>
  <text x="130" y="126" fill="#8b949e" font-size="9" font-family="monospace" text-anchor="middle">META-INF/spring/</text>
  <text x="130" y="142" fill="#8b949e" font-size="9" font-family="monospace" text-anchor="middle">AutoConfiguration.imports</text>
  <rect x="36" y="162" width="188" height="26" rx="5" fill="#2d3748" stroke="#8b949e" stroke-width="1"/>
  <text x="130" y="180" fill="#8b949e" font-size="9" font-family="monospace" text-anchor="middle">AcmeService.java (library code)</text>

  <!-- Starter module -->
  <rect x="280" y="80" width="140" height="80" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="350" y="104" fill="#79c0ff" font-size="11" font-family="monospace" text-anchor="middle">acme-starter</text>
  <text x="350" y="122" fill="#8b949e" font-size="10" font-family="monospace" text-anchor="middle">pom.xml only</text>
  <text x="350" y="138" fill="#8b949e" font-size="9" font-family="monospace" text-anchor="middle">depends on autoconfigure</text>

  <!-- Consumer app -->
  <rect x="480" y="70" width="160" height="100" rx="8" fill="#16202e" stroke="#6db33f" stroke-width="2"/>
  <text x="560" y="94" fill="#6db33f" font-size="11" font-family="sans-serif" text-anchor="middle" font-weight="bold">Consumer App</text>
  <text x="560" y="116" fill="#e6edf3" font-size="10" font-family="monospace" text-anchor="middle">&lt;dependency&gt;</text>
  <text x="560" y="132" fill="#e6edf3" font-size="10" font-family="monospace" text-anchor="middle">acme-starter</text>
  <text x="560" y="148" fill="#8b949e" font-size="9" font-family="monospace" text-anchor="middle">→ AcmeService @Autowired</text>

  <!-- Arrows -->
  <line x1="240" y1="130" x2="278" y2="130" stroke="#8b949e" stroke-width="1.5" stroke-dasharray="4,3" marker-end="url(#s1)"/>
  <line x1="420" y1="120" x2="478" y2="110" stroke="#6db33f" stroke-width="2" marker-end="url(#s1)"/>

  <defs>
    <marker id="s1" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/>
    </marker>
  </defs>
</svg>

The starter pom pulls in the autoconfigure JAR; the consumer adds one dependency and gets everything.

## 5. Runnable example

```java
// CustomStarterDemo.java
// How to run: java CustomStarterDemo.java  (JDK 17+)
// Simulates the two-module starter layout:
// - AcmeAutoConfiguration (autoconfigure module)
// - acme-starter (packaging — represented by a simple dependency declaration)
// - Consumer app that gets AcmeService for free

import java.lang.annotation.*;
import java.util.*;

// ── annotations (simulated) ───────────────────────────────────────
@Retention(RetentionPolicy.RUNTIME) @interface AutoConfiguration {}
@Retention(RetentionPolicy.RUNTIME) @interface Bean {}
@Retention(RetentionPolicy.RUNTIME) @interface ConditionalOnMissingBean {}

// ── library code (would be in acme-lib.jar) ──────────────────────
class AcmeService {
    private final String apiKey;
    AcmeService(String apiKey) { this.apiKey = apiKey; }
    String process(String data) { return "Processed by Acme [key=" + apiKey + "]: " + data; }
    @Override public String toString() { return "AcmeService(apiKey=" + apiKey + ")"; }
}

// ── autoconfigure module: AcmeAutoConfiguration ───────────────────
@AutoConfiguration
class AcmeAutoConfiguration {
    // In a real app: reads "acme.api-key" from application.properties
    @Bean
    @ConditionalOnMissingBean
    public AcmeService acmeService() {
        return new AcmeService("default-key-from-autoconfigure");
    }
}

// ── minimal Spring context simulation ────────────────────────────
public class CustomStarterDemo {

    static Map<String, Object> context = new LinkedHashMap<>();

    public static void main(String[] args) throws Exception {
        System.out.println("=== acme-spring-boot-starter simulation ===\n");
        System.out.println("Consumer adds: <dependency>acme-spring-boot-starter</dependency>");
        System.out.println("Starter brings in: acme-spring-boot-autoconfigure.jar");
        System.out.println("AutoConfiguration.imports contains: AcmeAutoConfiguration\n");

        // ── Scenario A: No user override — starter provides default ────────
        System.out.println("--- Scenario A: no user bean defined ---");
        applyAutoConfig(AcmeAutoConfiguration.class);
        printContextAndUse();

        // ── Scenario B: User provides own AcmeService — starter backs off ──
        context.clear();
        System.out.println("\n--- Scenario B: user defines own AcmeService ---");
        context.put("acmeService", new AcmeService("prod-key-from-properties"));
        System.out.println("User bean registered: " + context.get("acmeService"));
        applyAutoConfig(AcmeAutoConfiguration.class);
        printContextAndUse();
    }

    static void applyAutoConfig(Class<?> cfg) throws Exception {
        for (var m : cfg.getDeclaredMethods()) {
            if (!m.isAnnotationPresent(Bean.class)) continue;
            String name = m.getName();
            if (m.isAnnotationPresent(ConditionalOnMissingBean.class) && context.containsKey(name)) {
                System.out.println("AutoConfig @ConditionalOnMissingBean: '" + name
                    + "' already exists → backing off");
                continue;
            }
            Object bean = m.invoke(cfg.getDeclaredConstructor().newInstance());
            context.put(name, bean);
            System.out.println("AutoConfig registered '" + name + "' → " + bean);
        }
    }

    static void printContextAndUse() {
        AcmeService svc = (AcmeService) context.get("acmeService");
        System.out.println("Result: " + svc.process("hello world"));
    }
}
```

**How to run:** `java CustomStarterDemo.java`

Expected output:
```
=== acme-spring-boot-starter simulation ===

Consumer adds: <dependency>acme-spring-boot-starter</dependency>
Starter brings in: acme-spring-boot-autoconfigure.jar
AutoConfiguration.imports contains: AcmeAutoConfiguration

--- Scenario A: no user bean defined ---
AutoConfig registered 'acmeService' → AcmeService(apiKey=default-key-from-autoconfigure)
Result: Processed by Acme [key=default-key-from-autoconfigure]: hello world

--- Scenario B: user defines own AcmeService ---
User bean registered: AcmeService(apiKey=prod-key-from-properties)
AutoConfig @ConditionalOnMissingBean: 'acmeService' already exists → backing off
Result: Processed by Acme [key=prod-key-from-properties]: hello world
```

## 6. Walkthrough

- `AcmeService` represents the library's core value — it lives in the library JAR.
- `AcmeAutoConfiguration` is the autoconfigure module. It provides `AcmeService` as a default bean, guarded by `@ConditionalOnMissingBean` so users can supply their own.
- Scenario A: no user-defined `AcmeService` — the auto-configured default is used with the built-in API key.
- Scenario B: a user-defined `AcmeService` is in the context before auto-configuration runs — the `@ConditionalOnMissingBean` guard fires and the auto-config backs off. The user's production key is used instead.
- The `acme-spring-boot-starter` module is not shown as code because it is only a `pom.xml` (or `build.gradle`) declaring its dependency on the autoconfigure module and the library itself.

## 7. Gotchas & takeaways

> Do **not** put your auto-configuration classes in the consumer app's component-scan package. If the autoconfigure class is scanned as a regular `@Configuration`, it loses the ordering guarantees of the auto-configuration phase and may run before user config, preventing overrides.

> The starter module should have **no Java source** — it is purely a POM wrapper. Putting code in the starter confuses the two responsibilities (packaging vs. logic) and makes it harder for advanced users to depend on the autoconfigure module alone.

- Naming: `acme-spring-boot-starter` (not `spring-boot-starter-acme`) for third-party starters.
- The `AutoConfiguration.imports` file must be under `META-INF/spring/` in the autoconfigure JAR — not in the starter JAR.
- Support `@ConfigurationProperties` + `@EnableConfigurationProperties` in your autoconfigure class so users can configure your library via `application.properties`.
- Test with `ApplicationContextRunner` to verify conditions work correctly without starting a full app.
- Use `spring-boot-autoconfigure-processor` (apt plugin) in the autoconfigure module to validate the imports file at build time and generate metadata for IDE auto-complete.
