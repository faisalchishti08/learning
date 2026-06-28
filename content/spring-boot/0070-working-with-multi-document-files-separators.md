---
card: spring-boot
gi: 70
slug: working-with-multi-document-files-separators
title: Working with multi-document files (--- separators)
---

## 1. What it is

A single `application.yml` or `application.properties` file can contain **multiple logical documents**, separated by a special delimiter:

- YAML: three dashes on their own line — `---`
- Properties: three dashes prefixed by a hash — `#---`

Each section separated by `---` (or `#---`) is an independent document. Spring Boot processes them in order, top to bottom. Documents after the first are typically annotated with `spring.config.activate.on-profile` so they only apply under specific profiles — but they can also add unconditional properties.

## 2. Why & when

The alternative to multi-document files is maintaining separate files per profile: `application-dev.yml`, `application-prod.yml`, `application-staging.yml`. That works, but splits related config across many files. When the overrides are small, having them all in one place is easier to reason about.

Multi-document files shine when:

- The **base config is long** but per-profile overrides are a handful of lines.
- You want to **see the full picture** in one file: here is the default log level, and here, a few lines below, is the prod override.
- You are managing config in a single YAML file that tooling (e.g., a Helm chart, an Ansible template) generates for you and profiles let you bake in per-environment tweaks without extra files.

They are less suitable when each profile's config is large and the file would become unwieldy, or when different teams own different profiles and you want separate change histories per file.

## 3. Core concept

Think of it like a **legal document with amendments**. The first section is the base contract everyone agrees on. Each subsequent section, marked with a header (`spring.config.activate.on-profile: prod`), is an amendment that applies only when a given condition is met. The final effective contract is the base plus any matching amendments.

How Spring processes a multi-document file:

1. It reads the file from top to bottom.
2. Document 1 (before the first `---`) is always loaded.
3. Each subsequent document is evaluated: if it has `spring.config.activate.on-profile`, the document is only merged if the active profile matches.
4. Properties in later documents **override** properties in earlier documents for the same key.
5. Properties not defined in a later document remain as set in an earlier one.

The `#---` separator for `.properties` files was introduced in Spring Boot 2.4 alongside the unified config loading model. Before that, multi-document YAML was the only option.

## 4. Diagram

<svg viewBox="0 0 680 290" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Multi-document YAML: base document plus profile-specific documents merged into effective config">
  <rect width="680" height="290" rx="10" fill="#0d1117"/>

  <!-- application.yml file -->
  <rect x="20" y="15" width="245" height="255" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="143" y="38" fill="#6db33f" font-size="11" font-weight="bold" text-anchor="middle" font-family="sans-serif">application.yml</text>

  <!-- doc 1 -->
  <rect x="35" y="48" width="215" height="65" rx="4" fill="#161b22" stroke="#30363d" stroke-width="1"/>
  <text x="50" y="66" fill="#8b949e" font-size="9" font-family="sans-serif">Document 1 (always loaded)</text>
  <text x="50" y="82" fill="#e6edf3" font-size="10" font-family="monospace">log.level: INFO</text>
  <text x="50" y="98" fill="#e6edf3" font-size="10" font-family="monospace">server.port: 8080</text>

  <!-- separator -->
  <text x="143" y="128" fill="#79c0ff" font-size="13" font-weight="bold" text-anchor="middle" font-family="monospace">---</text>

  <!-- doc 2 -->
  <rect x="35" y="136" width="215" height="72" rx="4" fill="#161b22" stroke="#6db33f" stroke-width="1"/>
  <text x="50" y="154" fill="#6db33f" font-size="9" font-family="sans-serif">Document 2 (on-profile: prod)</text>
  <text x="50" y="170" fill="#e6edf3" font-size="10" font-family="monospace">spring.config.activate</text>
  <text x="50" y="185" fill="#e6edf3" font-size="10" font-family="monospace">  .on-profile: prod</text>
  <text x="50" y="200" fill="#e6edf3" font-size="10" font-family="monospace">log.level: WARN</text>

  <!-- separator -->
  <text x="143" y="222" fill="#79c0ff" font-size="13" font-weight="bold" text-anchor="middle" font-family="monospace">---</text>

  <!-- doc 3 -->
  <rect x="35" y="230" width="215" height="30" rx="4" fill="#161b22" stroke="#8b949e" stroke-width="1"/>
  <text x="50" y="248" fill="#8b949e" font-size="10" font-family="monospace">on-profile: dev → server.port: 9090</text>

  <!-- Profiles active column -->
  <rect x="295" y="15" width="120" height="255" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="355" y="38" fill="#8b949e" font-size="11" font-weight="bold" text-anchor="middle" font-family="sans-serif">Profile active</text>

  <text x="355" y="95" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">none</text>
  <text x="355" y="165" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">prod</text>
  <text x="355" y="245" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">dev</text>

  <!-- Result column -->
  <rect x="445" y="15" width="215" height="255" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="553" y="38" fill="#6db33f" font-size="11" font-weight="bold" text-anchor="middle" font-family="sans-serif">Effective config</text>

  <text x="465" y="60" fill="#8b949e" font-size="10" font-family="sans-serif">Profile: none</text>
  <text x="465" y="77" fill="#e6edf3" font-size="10" font-family="monospace">log.level=INFO</text>
  <text x="465" y="93" fill="#e6edf3" font-size="10" font-family="monospace">server.port=8080</text>

  <line x1="455" y1="105" x2="650" y2="105" stroke="#30363d" stroke-width="1"/>

  <text x="465" y="122" fill="#6db33f" font-size="10" font-family="sans-serif">Profile: prod</text>
  <text x="465" y="139" fill="#e6edf3" font-size="10" font-family="monospace">log.level=WARN    ← overridden</text>
  <text x="465" y="155" fill="#e6edf3" font-size="10" font-family="monospace">server.port=8080  ← unchanged</text>

  <line x1="455" y1="168" x2="650" y2="168" stroke="#30363d" stroke-width="1"/>

  <text x="465" y="185" fill="#79c0ff" font-size="10" font-family="sans-serif">Profile: dev</text>
  <text x="465" y="202" fill="#e6edf3" font-size="10" font-family="monospace">log.level=INFO    ← unchanged</text>
  <text x="465" y="218" fill="#e6edf3" font-size="10" font-family="monospace">server.port=9090  ← overridden</text>

  <!-- Arrows -->
  <line x1="420" y1="90" x2="442" y2="90" stroke="#8b949e" stroke-width="1.2" marker-end="url(#mda)"/>
  <line x1="420" y1="165" x2="442" y2="155" stroke="#6db33f" stroke-width="1.2" marker-end="url(#mdb)"/>
  <line x1="420" y1="245" x2="442" y2="210" stroke="#79c0ff" stroke-width="1.2" marker-end="url(#mdc)"/>

  <defs>
    <marker id="mda" markerWidth="7" markerHeight="7" refX="5" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
    <marker id="mdb" markerWidth="7" markerHeight="7" refX="5" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="mdc" markerWidth="7" markerHeight="7" refX="5" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>
</svg>

Document 1 is the base. Each `---` document that matches the active profile overlays its properties on top. Keys not mentioned in a later document retain their base-document value.

## 5. Runnable example

```java
// File: MultiDocDemo.java
// Spring Boot app — run with: ./gradlew bootRun  OR  mvn spring-boot:run
//
// src/main/resources/application.yml:
//
// # Document 1 — base (always loaded)
// app:
//   mode: development
//   log-level: INFO
//   server-port: 8080
//
// ---
// # Document 2 — production overrides
// spring:
//   config:
//     activate:
//       on-profile: prod
// app:
//   mode: production
//   log-level: WARN
//
// ---
// # Document 3 — staging overrides
// spring:
//   config:
//     activate:
//       on-profile: staging
// app:
//   server-port: 9090

package com.example;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.CommandLineRunner;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication
public class MultiDocDemo implements CommandLineRunner {

    @Value("${app.mode}")
    private String mode;

    @Value("${app.log-level}")
    private String logLevel;

    @Value("${app.server-port}")
    private int serverPort;

    public static void main(String[] args) {
        SpringApplication.run(MultiDocDemo.class, args);
    }

    @Override
    public void run(String... args) {
        System.out.println("Mode       : " + mode);
        System.out.println("Log level  : " + logLevel);
        System.out.println("Server port: " + serverPort);
    }
}
```

**How to run:**
- No profile: `./gradlew bootRun` → `mode=development`, `log-level=INFO`, `server-port=8080`
- Prod profile: `./gradlew bootRun --args='--spring.profiles.active=prod'` → `mode=production`, `log-level=WARN`, `server-port=8080`
- Staging profile: `./gradlew bootRun --args='--spring.profiles.active=staging'` → `mode=development`, `log-level=INFO`, `server-port=9090`

## 6. Walkthrough

- **Document 1** (no `spring.config.activate`) is loaded unconditionally. It establishes the defaults: `app.mode=development`, `app.log-level=INFO`, `app.server-port=8080`.
- **`---`** on its own line is the YAML multi-document separator. Spring Boot's config parser treats each document independently rather than merging them as a single YAML map.
- **Document 2** has `spring.config.activate.on-profile: prod`. Boot checks the active profiles; if `prod` is not in the list, this document is skipped. If `prod` is active, `app.mode` and `app.log-level` are overridden. `app.server-port` is not redefined here, so it stays at `8080` from Document 1.
- **Document 3** activates on the `staging` profile and overrides only `app.server-port`. `app.mode` and `app.log-level` are not touched, so they keep their Document 1 values.
- **`@Value("${app.log-level}")`** — the bean receives whichever value ended up in the Environment after all matching documents were merged. No Java code needs to know about profiles; the configuration layer handles it.
- **`.properties` equivalent** — replace `---` with `#---` and write each document block in `key=value` format. The behaviour is identical.

## 7. Gotchas & takeaways

> `spring.config.activate.on-profile` **cannot be set in Document 1** (the first document, before any `---`). Trying to activate the first document on a profile has no effect — it is always loaded. Only documents after a separator can use activation conditions.

> Putting the `spring.config.activate.on-profile` key in the wrong indentation level in YAML is a silent bug. It must be at `spring.config.activate.on-profile`, not `spring.profiles` (the old, deprecated key). The old key still works in Boot 2.x but was removed from 3.x.

- The `#---` separator for `.properties` files was added in Spring Boot 2.4. Files with it will not parse correctly on Boot 2.3 or earlier.
- Documents are processed top-to-bottom; a property defined in Document 3 takes precedence over the same property in Document 2 when both profiles are active simultaneously.
- Multi-document files work with `spring.config.import` too: an imported file can itself contain `---` separators.
- Keep Document 1 as a complete, runnable base config. If the app cannot start without a specific profile being active, something is wrong with the design.
- Multi-document files reduce file count but can become long. Split into separate profile files once a profile's overrides exceed ~20 lines.
