---
card: spring-boot
gi: 62
slug: property-source-order-precedence-full-list
title: Property source order/precedence (full list)
---

## 1. What it is

Spring Boot consults **17 property sources** in a fixed order when resolving any configuration key. The source that appears earliest in the list wins if multiple sources define the same key. Every source further down the list only fills in keys that no earlier source already provided.

This ordering is documented in the [Spring Boot reference](https://docs.spring.io/spring-boot/docs/current/reference/html/features.html#features.external-config) and is guaranteed stable between minor releases. Knowing it precisely lets you predict — and control — which value an app will actually use in any environment.

## 2. Why & when

Without a defined precedence, two common needs would collide:

- A **developer** wants to set sensible defaults that ship with the code.
- An **ops engineer** wants to override those defaults at deploy time without touching source.
- A **QA tester** wants a one-off override for a single test run without changing any file.

The ordered list serves all three: defaults sit at the bottom, file-based config sits in the middle, and runtime overrides (CLI, env vars) sit at the top. Each persona operates at their natural level without breaking the others.

You need to understand this list whenever:

- A property value surprises you and you don't know which source is "winning."
- You want to know where to put a new config value so it can be overridden by ops but not by accident.
- You are debugging a production incident where a value is different from what the committed file says.

## 3. Core concept

Think of the 17 sources as a **stack of transparency sheets** on an overhead projector. You lay them down from lowest priority (bottom) to highest priority (top). Wherever the top sheet has ink, that ink shows. Wherever it's transparent, the next sheet below shows through. The final projected image is what your app sees.

The sources fall into four broad groups:

| Group | Examples | Typical use |
|---|---|---|
| **Runtime overrides** | CLI args, `SPRING_APPLICATION_JSON` | Ops / CI quick changes |
| **Process environment** | OS env vars, JVM system properties | Container / systemd config |
| **Config files** | `application.properties`, profile-specific files | Developer defaults |
| **Code-level** | `@PropertySource`, `SpringApplication.setDefaultProperties` | Library defaults, tests |

The full ordered list (1 = highest priority):

1. Default properties set via `SpringApplication.setDefaultProperties(…)`  ← actually the *lowest* priority; listed first so overrides can beat it
   *(Note: Spring Boot's docs number from lowest to highest — the list below follows that convention so the numbering matches the official docs.)*

**Official order — lower number = lower priority, higher number = higher priority:**

| # | Source |
|---|---|
| 1 | Default properties (`SpringApplication.setDefaultProperties`) |
| 2 | `@PropertySource` annotations on `@Configuration` classes |
| 3 | Config data (`application.properties` / `application.yml` and their profile variants) |
| 4 | `RandomValuePropertySource` — `random.*` properties |
| 5 | OS environment variables |
| 6 | Java System properties (`System.getProperties()`) |
| 7 | JNDI attributes from `java:comp/env` |
| 8 | `ServletContext` init parameters |
| 9 | `ServletConfig` init parameters |
| 10 | Properties from `SPRING_APPLICATION_JSON` (env var or system property) |
| 11 | Command-line arguments (`--key=value`) |
| 12 | `properties` attribute on `@SpringBootTest` |
| 13 | `@DynamicPropertySource` in tests |
| 14 | `@TestPropertySource` annotations in tests |
| 15 | Devtools global settings (`~/.spring-boot-devtools.properties`) |

Within group 3 (config data), there is an internal sub-ordering:
- Profile-specific files inside a JAR beat the base file inside the JAR.
- Files outside the JAR beat files inside the JAR.
- Profile-specific files outside the JAR beat everything else in that group.

## 4. Diagram

<svg viewBox="0 0 680 380" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Property source precedence stack from lowest to highest priority">
  <defs>
    <marker id="arr62" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto">
      <path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/>
    </marker>
  </defs>

  <!-- Stack bars — drawn bottom to top, visually top = highest priority -->
  <!-- defaults (lowest) -->
  <rect x="40" y="320" width="400" height="28" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="50" y="339" fill="#8b949e" font-size="12" font-family="sans-serif">1  Default properties  (setDefaultProperties)</text>

  <!-- @PropertySource -->
  <rect x="40" y="288" width="400" height="28" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="50" y="307" fill="#8b949e" font-size="12" font-family="sans-serif">2  @PropertySource annotations</text>

  <!-- Config files -->
  <rect x="40" y="256" width="400" height="28" rx="5" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="50" y="275" fill="#79c0ff" font-size="12" font-family="sans-serif">3  application.properties / .yml  (+ profile variants)</text>

  <!-- OS env vars -->
  <rect x="40" y="224" width="400" height="28" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="50" y="243" fill="#e6edf3" font-size="12" font-family="sans-serif">5  OS environment variables</text>

  <!-- JVM system props -->
  <rect x="40" y="192" width="400" height="28" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="50" y="211" fill="#e6edf3" font-size="12" font-family="sans-serif">6  JVM system properties  (-Dkey=value)</text>

  <!-- SPRING_APPLICATION_JSON -->
  <rect x="40" y="160" width="400" height="28" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="50" y="179" fill="#e6edf3" font-size="12" font-family="sans-serif">10 SPRING_APPLICATION_JSON</text>

  <!-- CLI args -->
  <rect x="40" y="128" width="400" height="28" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="50" y="147" fill="#6db33f" font-size="12" font-weight="bold" font-family="sans-serif">11 CLI args  --key=value  ← highest (in production)</text>

  <!-- Test sources -->
  <rect x="40" y="80" width="400" height="44" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1.2" stroke-dasharray="5,3"/>
  <text x="50" y="97"  fill="#8b949e" font-size="11" font-family="sans-serif">12-14 Test-only sources</text>
  <text x="50" y="115" fill="#8b949e" font-size="11" font-family="sans-serif">(@SpringBootTest props, @DynamicPropertySource, @TestPropertySource)</text>

  <!-- Devtools -->
  <rect x="40" y="44" width="400" height="28" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1.2" stroke-dasharray="5,3"/>
  <text x="50" y="63" fill="#8b949e" font-size="11" font-family="sans-serif">15 Devtools global settings (~/.spring-boot-devtools.properties)</text>

  <!-- Priority arrow -->
  <line x1="460" y1="340" x2="460" y2="30" stroke="#6db33f" stroke-width="2" marker-end="url(#arr62)"/>
  <text x="475" y="340" fill="#8b949e" font-size="11" font-family="sans-serif" writing-mode="tb">lower priority</text>
  <text x="475" y="110" fill="#6db33f" font-size="11" font-family="sans-serif" writing-mode="tb">higher priority</text>
</svg>

*Each bar is a property source. When the same key appears in multiple bars, the highest bar wins. Sources below it fill in keys the higher source left unset.*

## 5. Runnable example

```java
// PrecedenceDemo.java — Spring Boot 3.x Maven project
// Demonstrates CLI arg beating env var beating application.properties

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

@SpringBootApplication
@RestController
public class PrecedenceDemo {

    // Resolved at startup from whichever source wins
    @Value("${demo.greeting:Hello (default)}")
    private String greeting;

    @GetMapping("/greeting")
    public String greeting() {
        return greeting;
    }

    public static void main(String[] args) {
        SpringApplication.run(PrecedenceDemo.class, args);
    }
}
```

`src/main/resources/application.properties`:
```properties
demo.greeting=Hello from properties file
```

**How to run — three experiments, one endpoint:**

```bash
# Experiment 1: file wins (no override)
./mvnw spring-boot:run
# GET /greeting => "Hello from properties file"

# Experiment 2: env var beats file
DEMO_GREETING="Hello from env var" ./mvnw spring-boot:run
# GET /greeting => "Hello from env var"

# Experiment 3: CLI arg beats env var
DEMO_GREETING="Hello from env var" \
  ./mvnw spring-boot:run -Dspring-boot.run.arguments=--demo.greeting="Hello from CLI"
# GET /greeting => "Hello from CLI"
```

## 6. Walkthrough

1. `@Value("${demo.greeting:Hello (default)}")` — the `:Hello (default)` part is a **Spring EL inline default**. It is used only if *no* property source (at any priority) defines `demo.greeting`. It sits even below source #1 in the table.
2. In Experiment 1 the only source defining `demo.greeting` is `application.properties` (source #3). That value resolves.
3. In Experiment 2 `DEMO_GREETING` (relaxed-binding maps the underscored env-var name to `demo.greeting`) comes from source #5 (OS env vars). Source #5 > source #3, so the env var wins.
4. In Experiment 3 `--demo.greeting=…` is a CLI argument (source #11). Source #11 > source #5 > source #3, so the CLI arg wins.
5. Each experiment uses the **same JAR and the same file** — only the external inputs change. This is the whole point of the precedence system.

## 7. Gotchas & takeaways

> Spring Boot's official docs list sources from **lowest to highest** (1 = lowest). Many people read the list and assume 1 = highest, which is the opposite of the truth. When in doubt, remember: CLI args always win in production.

> `@PropertySource` (source #2) is processed **after** config files in the sense that config data (source #3) beats it. A common surprise: you annotate a class with `@PropertySource("classpath:custom.properties")` and find it can't override `application.properties`. That's by design — `@PropertySource` is meant for *library defaults*, not user overrides.

- The full official precedence has 15 distinct sources; test-only sources (12-15) only apply during `@SpringBootTest`.
- Within config data (source #3), profile-specific files outside the JAR beat everything else in that group.
- Relaxed binding means env vars use `_` where property names use `.` and `UPPER_CASE` is equivalent to `lower.case`.
- To debug which source won for a key, hit the `/actuator/env` endpoint (add `spring-boot-starter-actuator` and expose the endpoint) — it shows each property and its originating source.
- Never rely on implicit knowledge of the order in code reviews. Link to this list or add a comment explaining why a given override mechanism was chosen.
