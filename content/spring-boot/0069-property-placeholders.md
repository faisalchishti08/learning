---
card: spring-boot
gi: 69
slug: property-placeholders
title: Property placeholders (${...})
---

## 1. What it is

The `${some.key}` notation written inside a property *value* is Spring's **property interpolation syntax**. When Spring resolves the property, it substitutes `${some.key}` with the value that `some.key` holds in the Environment. You can supply a fallback with a colon: `${some.key:default}` — if `some.key` is not defined, `default` is used instead.

These `${...}` tokens work in `.properties` files, YAML, `@Value` annotations, and XML bean definitions. They are resolved by Spring's `PropertySourcesPlaceholderConfigurer`, which runs early in the application context lifecycle.

## 2. Why & when

Without `${...}` references you repeat yourself constantly:

```properties
app.host=payments.internal
app.port=8443
app.base-url=https://payments.internal:8443/api   # ← host/port duplicated
app.health-url=https://payments.internal:8443/health
```

Change the host in one place and you must hunt down every URL. With `${...}` references:

```properties
app.host=payments.internal
app.port=8443
app.base-url=https://${app.host}:${app.port}/api
app.health-url=https://${app.host}:${app.port}/health
```

Now changing `app.host` cascades everywhere. Use `${...}` expressions whenever:

- A value is the **composition** of two or more other values (hosts, ports, paths).
- You want a **computed default** that still can be overridden — `${server.port:8080}` says "use whatever port is set, or 8080 if none is."
- You want to **cross-reference** an environment variable: `${HOME}` resolves to the OS-level `$HOME` because Spring maps environment variables into the `Environment`.

## 3. Core concept

Think of `${...}` tokens like **variable interpolation** in a shell script (`${MY_VAR}`). Spring's `Environment` is the lookup table: it holds properties from all sources (application.properties, env vars, system properties, command-line args). When it resolves `${some.key}`, it searches the table in priority order and substitutes the first match.

Three patterns to know:

| Syntax | Meaning |
|--------|---------|
| `${key}` | Required. Throws if `key` is absent. |
| `${key:default}` | Optional. Uses `default` string if `key` absent. |
| `${key:${other.key}}` | Nested. Falls back to another expression. |

Resolution is **recursive**: if `app.host=${SERVER_HOST}` and `SERVER_HOST=prod.example.com`, then `app.base-url=https://${app.host}/api` resolves to `https://prod.example.com/api` in two hops.

Spring uses `${}` for property interpolation and `#{}` for SpEL (Spring Expression Language) expressions. The two look similar but are distinct. Property tokens resolve at binding time; SpEL is evaluated at runtime.

## 4. Diagram

<svg viewBox="0 0 680 260" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Property substitution: ${app.host} expands through the Environment lookup table">
  <rect width="680" height="260" rx="10" fill="#0d1117"/>

  <!-- application.properties box -->
  <rect x="20" y="20" width="230" height="140" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="135" y="44" fill="#6db33f" font-size="11" font-weight="bold" text-anchor="middle" font-family="sans-serif">application.properties</text>
  <text x="40" y="66" fill="#e6edf3" font-size="10" font-family="monospace">app.host=payments.internal</text>
  <text x="40" y="84" fill="#e6edf3" font-size="10" font-family="monospace">app.port=8443</text>
  <text x="40" y="102" fill="#79c0ff" font-size="10" font-family="monospace">app.url=https://</text>
  <text x="40" y="118" fill="#79c0ff" font-size="10" font-family="monospace">  ${app.host}:${app.port}</text>
  <text x="40" y="134" fill="#8b949e" font-size="10" font-family="monospace">app.timeout=${timeout:30}</text>
  <text x="40" y="152" fill="#8b949e" font-size="10" font-family="monospace">  (default=30 if not set)</text>

  <!-- Arrow resolve -->
  <line x1="255" y1="90" x2="320" y2="90" stroke="#6db33f" stroke-width="2" marker-end="url(#pa)"/>
  <text x="287" y="83" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">resolve</text>

  <!-- Environment lookup -->
  <rect x="325" y="20" width="200" height="140" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="425" y="44" fill="#79c0ff" font-size="11" font-weight="bold" text-anchor="middle" font-family="sans-serif">Environment</text>
  <text x="425" y="62" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">(ordered property sources)</text>
  <text x="345" y="82" fill="#e6edf3" font-size="10" font-family="monospace">app.host → payments.internal</text>
  <text x="345" y="98" fill="#e6edf3" font-size="10" font-family="monospace">app.port → 8443</text>
  <text x="345" y="114" fill="#8b949e" font-size="10" font-family="monospace">timeout → (absent)</text>
  <text x="345" y="138" fill="#8b949e" font-size="9" font-family="sans-serif">└ uses default: 30</text>

  <!-- Arrow to result -->
  <line x1="529" y1="90" x2="590" y2="90" stroke="#6db33f" stroke-width="2" marker-end="url(#pb)"/>

  <!-- Result box -->
  <rect x="595" y="55" width="65" height="70" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="628" y="78" fill="#6db33f" font-size="9" font-weight="bold" text-anchor="middle" font-family="sans-serif">Resolved</text>
  <text x="628" y="96" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="monospace">https://</text>
  <text x="628" y="110" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="monospace">payments</text>
  <text x="628" y="124" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="monospace">:8443</text>

  <!-- legend row -->
  <rect x="20" y="185" width="640" height="52" rx="6" fill="#161b22" stroke="#30363d" stroke-width="1"/>
  <text x="40" y="208" fill="#e6edf3" font-size="11" font-family="monospace">${key}        — required; throws if absent</text>
  <text x="40" y="228" fill="#e6edf3" font-size="11" font-family="monospace">${key:default} — uses "default" string when key is absent</text>

  <defs>
    <marker id="pa" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="pb" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>
</svg>

Spring walks the Environment's ordered property sources, substituting each `${...}` token. Resolution is recursive: a token can itself resolve via another key in the Environment.

## 5. Runnable example

```java
// File: PlaceholderDemo.java
// JDK 17+, Spring Boot — run with ./gradlew bootRun or mvn spring-boot:run
//
// src/main/resources/application.properties:
//   app.host=payments.internal
//   app.port=8443
//   app.base-url=https://${app.host}:${app.port}/api
//   app.health-url=https://${app.host}:${app.port}/health
//   app.connect-timeout=${CONNECT_TIMEOUT:5000}
//   app.greeting=Hello from ${app.host} on port ${app.port}!

package com.example;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.CommandLineRunner;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication
public class PlaceholderDemo implements CommandLineRunner {

    @Value("${app.host}")
    private String host;

    @Value("${app.port}")
    private int port;

    // Composed from two property references
    @Value("${app.base-url}")
    private String baseUrl;

    @Value("${app.health-url}")
    private String healthUrl;

    // Defaults to 5000 unless env var CONNECT_TIMEOUT is set
    @Value("${app.connect-timeout}")
    private int connectTimeout;

    // A full sentence assembled from property references
    @Value("${app.greeting}")
    private String greeting;

    public static void main(String[] args) {
        SpringApplication.run(PlaceholderDemo.class, args);
    }

    @Override
    public void run(String... args) {
        System.out.println("host           : " + host);
        System.out.println("port           : " + port);
        System.out.println("base-url       : " + baseUrl);
        System.out.println("health-url     : " + healthUrl);
        System.out.println("connect-timeout: " + connectTimeout + "ms");
        System.out.println("greeting       : " + greeting);
    }
}
```

**How to run:**
1. Add `application.properties` with the content shown in the comment block above.
2. Run `./gradlew bootRun`. Observe that `app.base-url` and `app.health-url` both expand using `app.host` and `app.port`.
3. Override at runtime: `CONNECT_TIMEOUT=1000 ./gradlew bootRun` — the default of 5000 is replaced by 1000.
4. Try `--app.host=staging.internal` on the command line — all composed URLs automatically update.

## 6. Walkthrough

- **`app.base-url=https://${app.host}:${app.port}/api`** — Spring's `PropertySourcesPlaceholderConfigurer` scans every property value for `${...}` tokens and replaces them using the `Environment`. Both tokens here resolve from the same `application.properties`, demonstrating intra-file references.
- **`@Value("${app.base-url}")`** — by the time `@Value` is injected, the expression has already been resolved to `https://payments.internal:8443/api`. The bean receives the final string.
- **`app.connect-timeout=${CONNECT_TIMEOUT:5000}`** — `CONNECT_TIMEOUT` is an OS environment variable. Spring's `Environment` includes OS env vars in its property sources, so this resolves to the env var if set, or `5000` if not. The `:5000` is the default.
- **`@Value("${app.port}")`** with `private int port` — Spring coerces the string `"8443"` to `int` automatically. The substitution mechanism delivers a `String`; type conversion happens afterwards via Spring's `ConversionService`.
- **`app.greeting=Hello from ${app.host} on port ${app.port}!`** — multiple tokens in one value are each resolved independently and concatenated. This is the simplest form of template composition.
- **Overriding on command line** — passing `--app.host=staging.internal` puts that value into the command-line property source, which has higher priority than `application.properties`. Both `app.base-url` and `app.health-url` pick up the new host automatically because they reference `${app.host}`, not the literal string.

## 7. Gotchas & takeaways

> If you use `${key}` without a default and `key` is absent from the Environment, Spring throws `IllegalArgumentException: Could not resolve '${key}'` during context refresh — **before your application code runs**. Always add a default (`${key:fallback}`) for any property that might legitimately be absent in some environments.

> Do not confuse `${}` (property interpolation) with `#{}` (SpEL expression). `${server.port}` looks up a property; `#{T(java.lang.Math).PI}` evaluates a Java expression. They can even be combined: `@Value("#{'${app.host}'.toUpperCase()}")` — but keep it simple and only reach for SpEL when you genuinely need expression logic.

- `${...}` tokens eliminate copy-paste duplication: define `host` and `port` once, compose everything else.
- Environment variables are first-class property sources, so `${MY_ENV_VAR:default}` is a clean way to read container environment without any extra code.
- Token resolution is **eager** — it happens at context startup, not on first bean access. A typo in a key name surfaces immediately, not in production at runtime.
- Relaxed binding applies to `@ConfigurationProperties` but not to raw `@Value` — `${app.connect-timeout}` must match the exact key, while `@ConfigurationProperties` would also accept `APP_CONNECT_TIMEOUT` or `app.connectTimeout`.
- Circular references (`a=${b}`, `b=${a}`) cause a stack overflow at startup — Spring does not detect the cycle before attempting resolution.
