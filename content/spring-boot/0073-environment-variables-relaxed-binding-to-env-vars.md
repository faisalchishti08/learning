---
card: spring-boot
gi: 73
slug: environment-variables-relaxed-binding-to-env-vars
title: Environment variables & relaxed binding to env vars
---

## 1. What it is

Operating-system environment variables are the oldest and most portable way to inject configuration into a process. Every language, every container runtime, and every CI system understands them. Spring Boot reads them automatically — no extra setup required — and exposes them through the same `Environment` abstraction as `application.properties`.

The twist is that env-var names follow **different naming rules** than Spring property keys. A dot (`.`) is illegal in most shells, and hyphens (`-`) are illegal in POSIX variable names. So Spring Boot ships a **relaxed binding** algorithm that translates `SPRING_DATASOURCE_URL` into `spring.datasource.url` and `SPRING_JPA_SHOW__SQL` into `spring.jpa.show-sql`, letting you write container-friendly uppercase names and still hit the same property keys your Java code expects.

In one sentence: **Spring Boot converts environment variables in uppercase + underscore form into the dotted, lowercase property names your application uses.**

## 2. Why & when

Environment variables became the dominant config mechanism for containerised workloads because:

- **Secrets stay out of source control.** You never commit a password to Git if it lives only in an env var injected at runtime.
- **Kubernetes and Docker Compose both speak env vars natively.** A `ConfigMap`, a secret, or an `env:` entry in a Pod spec arrives in the process as a plain env var.
- **Twelve-factor app methodology** (the canonical reference for cloud-native design) mandates env vars for all environment-specific config.
- **No filesystem needed.** Serverless runtimes, Lambda functions, and read-only containers can all inject env vars without mounting any file.

You reach for this mechanism whenever:
- You're packaging the app as a Docker image and different deployments (dev, staging, prod) differ only in a handful of values.
- You're rotating database passwords via an external secrets manager that writes to env vars.
- You're running on a PaaS (Heroku, Railway, Render) where env var injection is the only configuration interface.

## 3. Core concept

Spring's `StandardEnvironment` includes a `SystemEnvironmentPropertySource` that wraps `System.getenv()`. When you look up a property key such as `spring.datasource.url`, Spring also checks a **relaxed-binding** translation of that key against the env-var map.

The translation rules for env vars are:

| Spring property key | Canonical env-var form |
|---|---|
| `server.port` | `SERVER_PORT` |
| `spring.datasource.url` | `SPRING_DATASOURCE_URL` |
| `spring.jpa.show-sql` | `SPRING_JPA_SHOW_SQL` |
| `app.my-service.timeout` | `APP_MY__SERVICE_TIMEOUT` *(double-underscore for a hyphen in the segment)* |

The core rules are:
1. Convert the property key to **UPPER_CASE**.
2. Replace each **dot** (`.`) with a **single underscore** (`_`).
3. Replace each **hyphen** (`-`) inside a segment with a **double underscore** (`__`).

So to map to `app.my-service.retry-count`, the env var is `APP_MY__SERVICE_RETRY__COUNT`.

For `@ConfigurationProperties` classes, Spring applies relaxed binding automatically — the same property bound from a YAML file with `app.myProp: value` is also matched by an env var `APP_MYPROP` or `APP_MY_PROP`.

**Priority:** env vars sit at priority level 3 in Spring's ordered list, above `application.properties` files but below command-line arguments. That means an env var overrides `application.properties` but a `--server.port=9090` flag still wins.

## 4. Diagram

<svg viewBox="0 0 660 280" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Relaxed binding translation pipeline from OS env var to Spring property key">

  <!-- left: env var box -->
  <rect x="20" y="90" width="185" height="100" rx="10" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="112" y="118" fill="#e6edf3" font-size="13" text-anchor="middle" font-family="monospace" font-weight="bold">OS / Container</text>
  <text x="112" y="138" fill="#79c0ff" font-size="12" text-anchor="middle" font-family="monospace">SPRING_DATASOURCE</text>
  <text x="112" y="155" fill="#79c0ff" font-size="12" text-anchor="middle" font-family="monospace">_URL=jdbc:...</text>

  <!-- arrow 1 -->
  <line x1="205" y1="140" x2="270" y2="140" stroke="#6db33f" stroke-width="2" marker-end="url(#a1)"/>
  <text x="237" y="130" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">reads</text>

  <!-- middle: translation box -->
  <rect x="270" y="70" width="175" height="140" rx="10" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="357" y="98" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif" font-weight="bold">Relaxed Binding</text>
  <text x="357" y="116" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">UPPER → lower</text>
  <text x="357" y="133" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">_ → dot</text>
  <text x="357" y="150" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">__ → hyphen</text>
  <text x="357" y="170" fill="#6db33f" font-size="11" text-anchor="middle" font-family="monospace">spring.datasource</text>
  <text x="357" y="187" fill="#6db33f" font-size="11" text-anchor="middle" font-family="monospace">.url</text>

  <!-- arrow 2 -->
  <line x1="445" y1="140" x2="510" y2="140" stroke="#6db33f" stroke-width="2" marker-end="url(#a2)"/>
  <text x="477" y="130" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">binds</text>

  <!-- right: Java config box -->
  <rect x="510" y="90" width="135" height="100" rx="10" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="577" y="118" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif" font-weight="bold">Java field</text>
  <text x="577" y="140" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="monospace">DataSource</text>
  <text x="577" y="157" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="monospace">Props.url</text>

  <!-- bottom note -->
  <text x="330" y="240" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">SystemEnvironmentPropertySource wraps System.getenv()</text>

  <defs>
    <marker id="a1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="a2" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>
</svg>

The relaxed binding engine sits between the raw OS environment and your Java class fields, translating naming conventions so neither side has to change.

## 5. Runnable example

```java
// src/main/java/com/example/config/DatasourceProps.java
package com.example.config;

import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.stereotype.Component;

@Component
@ConfigurationProperties(prefix = "spring.datasource")
public class DatasourceProps {
    private String url;
    private String username;
    private String password;

    // standard getters and setters
    public String getUrl()            { return url; }
    public void setUrl(String url)    { this.url = url; }
    public String getUsername()             { return username; }
    public void setUsername(String username){ this.username = username; }
    public String getPassword()             { return password; }
    public void setPassword(String password){ this.password = password; }
}

// src/main/java/com/example/EnvBindingApp.java
package com.example;

import com.example.config.DatasourceProps;
import org.springframework.boot.CommandLineRunner;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.annotation.Bean;

@SpringBootApplication
public class EnvBindingApp {

    public static void main(String[] args) {
        SpringApplication.run(EnvBindingApp.class, args);
    }

    @Bean
    CommandLineRunner run(DatasourceProps props) {
        return args -> {
            System.out.println("url      = " + props.getUrl());
            System.out.println("username = " + props.getUsername());
        };
    }
}
```

**How to run:** set two environment variables before launching, then start the app normally:

```bash
export SPRING_DATASOURCE_URL=jdbc:h2:mem:testdb
export SPRING_DATASOURCE_USERNAME=sa
./mvnw spring-boot:run
```

Expected output:
```
url      = jdbc:h2:mem:testdb
username = sa
```

No `application.properties` entry is needed — the env vars drive everything.

## 6. Walkthrough

- **`DatasourceProps` class** — annotated with `@ConfigurationProperties(prefix = "spring.datasource")`. Spring will look for any property whose key starts with `spring.datasource` and write it to the matching field via the setter.
- **`setUrl` / `setUsername`** — standard JavaBean setters. Spring calls them during context startup to populate the bound values.
- **`SPRING_DATASOURCE_URL`** — the shell form of `spring.datasource.url`. The relaxed-binding engine translates `SPRING_DATASOURCE_URL` → `spring.datasource.url` at lookup time, so the env var matches the prefix + field name.
- **`SPRING_DATASOURCE_USERNAME`** — similarly maps to `spring.datasource.username`. Note that the Java field name is `username`, not `user-name`, so no double-underscore is needed here.
- **`CommandLineRunner`** — runs after the application context is fully started. By that point all binding is complete, so `props.getUrl()` returns the injected value.
- If neither the env var nor `application.properties` supplies a value, the field stays `null`. You can make this an error with `@Validated` + `@NotNull` on the field (covered in a later tutorial on validation).

## 7. Gotchas & takeaways

> A single underscore (`_`) in an env-var name maps to a **dot**, not a hyphen. If your property key has a hyphen in a segment (e.g., `app.my-service`), you need a **double underscore** (`APP_MY__SERVICE`). Using a single underscore here will not bind correctly, and Spring will silently leave the field at its default — there is no error.

- Env vars take priority over `application.properties` but lose to command-line arguments (`--key=value`).
- Relaxed binding only applies when reading through Spring's `Environment` abstraction or `@ConfigurationProperties`. A raw `System.getenv("spring.datasource.url")` call will return `null` because the OS never stored a key with dots.
- Do not store plaintext production secrets in process-level env vars if your threat model includes other processes on the same host — prefer a secrets manager that injects secrets at startup and then clears them.
- In Kubernetes, `env:` entries from a `ConfigMap` and `envFrom:` entries from a `Secret` arrive identically as env vars; Spring Boot cannot tell them apart, which is usually exactly what you want.
- Spring Boot also logs detected relaxed binding mismatches at `DEBUG` level — enable `logging.level.org.springframework.boot.context.properties=DEBUG` when troubleshooting binding failures.
