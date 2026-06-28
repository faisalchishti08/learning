---
card: spring-boot
gi: 64
slug: json-application-properties-spring-application-json
title: JSON application properties (SPRING_APPLICATION_JSON)
---

## 1. What it is

`SPRING_APPLICATION_JSON` is an environment variable (or JVM system property) whose value is a **JSON object**. Spring Boot parses that JSON at startup and flattens every key-value pair into the `Environment`, as if each key had been set individually.

```bash
SPRING_APPLICATION_JSON='{"server":{"port":9090},"app":{"name":"shop"}}' \
  java -jar app.jar
```

The two JSON keys map to `server.port=9090` and `app.name=shop` — exactly the same properties you would write in `application.properties`, but delivered as a single blob of JSON.

It sits at source #10 in Spring Boot's precedence list — above config files and OS env vars, but below CLI args.

## 2. Why & when

Setting many individual environment variables can be awkward or error-prone in some environments:

- **Kubernetes** ConfigMaps and Secrets are often mounted as files, but if you need env vars you must list each one in `env:` or `envFrom:`. A single `SPRING_APPLICATION_JSON` variable carries dozens of properties in one declaration.
- **CI/CD platforms** (GitHub Actions, CircleCI, Jenkins) often let you define a single "secret" variable more easily than several. Packing all overrides into one JSON blob is one declaration vs. ten.
- **Platforms with character restrictions.** Some PaaS providers have limits on env var names (no dots, only uppercase letters). `SPRING_APPLICATION_JSON` is a single, well-named variable that works everywhere.

Use it when the *number* of properties makes individual env vars unwieldy, or when the deployment platform makes individual property env vars hard to manage.

Avoid it when:
- You only need to override one or two values — individual env vars are clearer.
- The JSON blob would contain secrets visible in platform logs — store those in a secrets manager instead.
- Your team is not comfortable reading JSON in shell commands.

## 3. Core concept

Think of `SPRING_APPLICATION_JSON` as a **packing list** in a single envelope. Instead of mailing 20 separate sticky notes, you slip one sheet of paper with all 20 items written on it. The recipient (Spring Boot) opens the envelope, reads the list, and acts as if they received 20 separate sticky notes.

**How it works internally:**

1. At startup, Spring Boot's `EnvironmentPostProcessor` scans for `SPRING_APPLICATION_JSON` in both system properties and OS env vars.
2. It parses the value as a JSON object using Jackson's `ObjectMapper`.
3. It flattens the JSON using dot-notation: `{"server":{"port":9090}}` → `server.port=9090`.
4. The resulting flat map is wrapped in a `MapPropertySource` and inserted at position #10 in the `Environment` source list.

**Flattening rules:**

| JSON | Flattened property |
|---|---|
| `{"a": 1}` | `a=1` |
| `{"a": {"b": 2}}` | `a.b=2` |
| `{"list": ["x","y"]}` | `list[0]=x`, `list[1]=y` |
| `{"a": {"b": {"c": 3}}}` | `a.b.c=3` |

The JSON equivalent of the `application.properties` `spring.datasource.url=…` is `{"spring":{"datasource":{"url":"…"}}}`.

## 4. Diagram

<svg viewBox="0 0 680 280" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="SPRING_APPLICATION_JSON parsed and flattened into the Environment">
  <defs>
    <marker id="arr64" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto">
      <path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/>
    </marker>
    <marker id="arr64b" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto">
      <path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/>
    </marker>
  </defs>

  <!-- Env var box -->
  <rect x="20" y="40" width="260" height="90" rx="8" fill="#0d1117" stroke="#6db33f" stroke-width="1.5"/>
  <text x="36" y="62" fill="#8b949e" font-size="11" font-family="monospace">SPRING_APPLICATION_JSON=</text>
  <text x="36" y="80" fill="#6db33f" font-size="12" font-family="monospace">{"server":{"port":9090},</text>
  <text x="36" y="98" fill="#6db33f" font-size="12" font-family="monospace"> "db":{"url":"jdbc:..."},</text>
  <text x="36" y="116" fill="#6db33f" font-size="12" font-family="monospace"> "feature":{"x":true}}</text>

  <!-- Arrow to parser -->
  <line x1="284" y1="85" x2="355" y2="85" stroke="#6db33f" stroke-width="2" marker-end="url(#arr64)"/>

  <!-- Parser box -->
  <rect x="359" y="58" width="160" height="54" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="439" y="80" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">JSON flatten</text>
  <text x="439" y="98" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">(ObjectMapper)</text>

  <!-- Arrow to flat props -->
  <line x1="439" y1="115" x2="439" y2="155" stroke="#79c0ff" stroke-width="2" marker-end="url(#arr64b)"/>

  <!-- Flattened properties -->
  <rect x="300" y="158" width="320" height="90" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="316" y="178" fill="#79c0ff" font-size="12" font-family="monospace">server.port       = 9090</text>
  <text x="316" y="196" fill="#79c0ff" font-size="12" font-family="monospace">db.url            = jdbc:...</text>
  <text x="316" y="214" fill="#79c0ff" font-size="12" font-family="monospace">feature.x         = true</text>
  <text x="316" y="238" fill="#8b949e" font-size="11" font-family="sans-serif">MapPropertySource  (priority #10)</text>

  <!-- Source priority ladder hint -->
  <text x="36" y="185" fill="#8b949e" font-size="11" font-family="sans-serif">Priority order (prod):</text>
  <text x="36" y="203" fill="#6db33f" font-size="11" font-family="sans-serif">CLI args  (#11)</text>
  <text x="36" y="219" fill="#e6edf3" font-size="11" font-family="sans-serif">SAJ      (#10)  ← here</text>
  <text x="36" y="235" fill="#8b949e" font-size="11" font-family="sans-serif">env vars  (#5)</text>
  <text x="36" y="251" fill="#8b949e" font-size="11" font-family="sans-serif">app.props (#3)</text>
</svg>

*The JSON blob is parsed once at startup, flattened to dot-notation keys, and added to the `Environment` at priority #10 — above individual env vars but below CLI args.*

## 5. Runnable example

```java
// SpringAppJsonDemo.java — Spring Boot 3.x project

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

@SpringBootApplication
@RestController
public class SpringAppJsonDemo {

    @Value("${server.port}")
    private int port;

    @Value("${app.name:unknown}")
    private String appName;

    @Value("${feature.dark-mode:false}")
    private boolean darkMode;

    @GetMapping("/info")
    public String info() {
        return String.format("port=%d  app=%s  darkMode=%b", port, appName, darkMode);
    }

    public static void main(String[] args) {
        SpringApplication.run(SpringAppJsonDemo.class, args);
    }
}
```

`src/main/resources/application.properties`:
```properties
server.port=8080
app.name=default-app
feature.dark-mode=false
```

**How to run:**

```bash
# 1. Default — file values
./mvnw spring-boot:run
# http://localhost:8080/info => port=8080  app=default-app  darkMode=false

# 2. Override with SPRING_APPLICATION_JSON
export SPRING_APPLICATION_JSON='{"server":{"port":9090},"app":{"name":"shop"},"feature":{"dark-mode":true}}'
./mvnw spring-boot:run
# http://localhost:9090/info => port=9090  app=shop  darkMode=true

# 3. As a JVM system property (useful in Docker CMD without shell)
java -Dspring.application.json='{"server":{"port":9091},"app":{"name":"api"}}' \
     -jar target/*.jar
# http://localhost:9091/info => port=9091  app=api  darkMode=false
```

## 6. Walkthrough

1. `application.properties` provides three defaults that live in source control.
2. In run 2, `SPRING_APPLICATION_JSON` is set in the shell. Spring Boot's `EnvironmentPostProcessor` reads it before any `@Value` injection happens.
3. Jackson parses `{"server":{"port":9090},...}` and the post-processor flattens it: `server.port=9090`, `app.name=shop`, `feature.dark-mode=true`.
4. These three flattened keys form a `MapPropertySource` inserted at position #10 — above the env-var source (#5) and above config files (#3). All three file defaults are overridden.
5. In run 3, the JSON is passed as `spring.application.json` (the JVM system property name — note: dotted, not underscored). This is source #6 (JVM system properties). Spring Boot reads *that* and still creates a `MapPropertySource` at position #10. The end result is the same as the env-var form.
6. `feature.dark-mode` uses a hyphenated key. YAML/properties and `@Value` both handle hyphens fine; the JSON key `"dark-mode"` maps correctly to the property key `feature.dark-mode`.

## 7. Gotchas & takeaways

> The JSON value must be a **JSON object** (`{…}`), not a string, array, or number. `SPRING_APPLICATION_JSON="my-string"` will fail to parse and Spring Boot will log a warning, then ignore the variable entirely.

> If your JSON string contains shell-special characters (double quotes, `$`, backticks), wrap the whole value in **single quotes** in bash, or escape carefully. A mis-quoted value silently becomes an invalid JSON fragment and is ignored.

- `SPRING_APPLICATION_JSON` (env var, ALL_CAPS with underscores) and `spring.application.json` (JVM system property, dotted lowercase) are two names for the same feature — pick the one that fits your deployment tool.
- Priority is #10: above individual env vars (#5) and config files (#3), but below CLI args (#11).
- Nested JSON objects flatten to dot-notation: `{"a":{"b":1}}` → `a.b=1`.
- JSON arrays flatten to indexed notation: `{"hosts":["a","b"]}` → `hosts[0]=a`, `hosts[1]=b`.
- One good use: in Kubernetes, set the entire override block as a single Secret/ConfigMap value mapped to `SPRING_APPLICATION_JSON` rather than exploding it into dozens of individual env var entries.
- Values set this way show up in `/actuator/env` under the source name `spring.application.json`.
