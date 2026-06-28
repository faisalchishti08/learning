---
card: spring-boot
gi: 78
slug: merging-complex-types-lists-maps
title: Merging complex types (lists, maps)
---

## 1. What it is

When Spring Boot binds `@ConfigurationProperties` and multiple property sources define the same key, a priority rule determines the winner. For **scalar values** (strings, numbers, booleans) the rule is simple: the highest-priority source wins, period. For **collections**, the rule depends on the type:

- **Lists** are **not merged**. The highest-priority source that defines the list wins entirely, replacing the lower-priority definition.
- **Maps** are **merged key-by-key**. Every source contributes its entries; for any key that appears in multiple sources, the highest-priority source's value wins — but keys present only in a lower-priority source are still included.

This asymmetry surprises almost every Spring developer at least once. Understanding it upfront saves hours of debugging.

In one sentence: **when multiple property sources define the same property, lists replace each other wholesale while maps are merged entry-by-entry, with higher-priority sources winning any conflicts.**

## 2. Why & when

The distinction exists because of how lists and maps are semantically different:

- A **list** expresses an **ordered sequence** where the meaning depends on all items and their order. Merging two independently-defined sequences would produce an undefined ordering that likely satisfies neither source's intent. Spring treats the list as an atomic unit: either you want this list, or you want that one.
- A **map** expresses a **set of named overrides**. Each key is independent, so it is natural and useful to let different sources contribute different keys. A profile-specific config that adds one extra entry to a map should not need to repeat all the base entries.

You encounter this when:
- An `application.yml` defines base list values (allowed origins, enabled features) and you try to extend them in `application-prod.yml`.
- You use environment variables to add individual map entries without rewriting the entire map.
- A `@TestPropertySource` in a test defines only a few overrides and you observe unexpected interactions with the main config.

## 3. Core concept

**Priority order reminder (highest to lowest):**

1. Command-line arguments
2. `@TestPropertySource` (tests only)
3. Environment variables
4. `application-{profile}.yml` (active profiles, in reverse order)
5. `application.yml`

**List replacement in detail:**

Suppose `application.yml` defines:

```yaml
app:
  allowed-origins:
    - https://app.example.com
    - https://api.example.com
```

And `application-prod.yml` defines:

```yaml
app:
  allowed-origins:
    - https://prod.example.com
```

When the `prod` profile is active, `app.allowed-origins` will be `[https://prod.example.com]` — the base list is gone entirely. You cannot "add one more origin" via a profile; you must restate the full list.

**Map merging in detail:**

Suppose `application.yml` defines:

```yaml
app:
  headers:
    x-request-id: generate
    x-api-version: "1"
```

And `application-prod.yml` defines:

```yaml
app:
  headers:
    x-api-version: "2"
    x-strict-transport: "max-age=31536000"
```

When `prod` is active, the merged result is:

```
app.headers.x-request-id        = generate          (from base yml)
app.headers.x-api-version       = 2                 (prod wins the conflict)
app.headers.x-strict-transport  = max-age=31536000  (only in prod, included)
```

**Workaround for list merging:**

If you need to "add" to a list across property sources, the only clean options are:

1. Define the entire merged list in the higher-priority source — repeat all values.
2. Switch from `List<String>` to `Map<String, String>` where the key is an arbitrary label and the value is the actual entry.
3. Use a `@Bean` that programmatically combines values from multiple injected fields.

## 4. Diagram

<svg viewBox="0 0 680 340" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="List replacement vs map merging across two property sources">

  <!-- === LEFT: List replacement === -->
  <text x="165" y="22" fill="#e6edf3" font-size="13" text-anchor="middle" font-family="sans-serif" font-weight="bold">List (NOT merged)</text>

  <!-- base source -->
  <rect x="20" y="34" width="145" height="85" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="92" y="56" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">application.yml</text>
  <text x="92" y="74" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="monospace">- https://app.ex</text>
  <text x="92" y="90" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="monospace">- https://api.ex</text>
  <text x="92" y="108" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">(base, lower priority)</text>

  <!-- prod source -->
  <rect x="175" y="34" width="145" height="85" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="247" y="56" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">application-prod.yml</text>
  <text x="247" y="74" fill="#6db33f" font-size="10" text-anchor="middle" font-family="monospace">- https://prod.ex</text>
  <text x="247" y="95" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">(prod, higher priority)</text>

  <!-- Arrow down -->
  <line x1="165" y1="120" x2="165" y2="155" stroke="#6db33f" stroke-width="2" marker-end="url(#f1)"/>
  <text x="185" y="142" fill="#8b949e" font-size="10" font-family="sans-serif">wins entirely</text>

  <!-- result box left -->
  <rect x="60" y="160" width="210" height="60" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="165" y="184" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Result</text>
  <text x="165" y="204" fill="#6db33f" font-size="11" text-anchor="middle" font-family="monospace">[ https://prod.ex ]</text>

  <!-- X over base -->
  <line x1="20" y1="34" x2="165" y2="119" stroke="#e6473a" stroke-width="1.5" opacity="0.6"/>
  <line x1="165" y1="34" x2="20" y2="119" stroke="#e6473a" stroke-width="1.5" opacity="0.6"/>
  <text x="92" y="148" fill="#e6473a" font-size="10" text-anchor="middle" font-family="sans-serif">base list discarded</text>

  <!-- === RIGHT: Map merging === -->
  <text x="510" y="22" fill="#e6edf3" font-size="13" text-anchor="middle" font-family="sans-serif" font-weight="bold">Map (merged key-by-key)</text>

  <!-- base map source -->
  <rect x="355" y="34" width="155" height="100" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="432" y="56" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">application.yml</text>
  <text x="432" y="74" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="monospace">x-req-id: generate</text>
  <text x="432" y="90" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="monospace">x-version: "1"</text>
  <text x="432" y="108" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">(base)</text>

  <!-- prod map source -->
  <rect x="520" y="34" width="155" height="100" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="597" y="56" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">application-prod.yml</text>
  <text x="597" y="74" fill="#6db33f" font-size="10" text-anchor="middle" font-family="monospace">x-version: "2"</text>
  <text x="597" y="90" fill="#6db33f" font-size="10" text-anchor="middle" font-family="monospace">x-strict-ts: yes</text>
  <text x="597" y="108" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">(prod)</text>

  <!-- Arrows down -->
  <line x1="432" y1="134" x2="465" y2="168" stroke="#8b949e" stroke-width="1.5" marker-end="url(#f2)"/>
  <line x1="597" y1="134" x2="565" y2="168" stroke="#6db33f" stroke-width="1.5" marker-end="url(#f3)"/>

  <!-- Merged result box -->
  <rect x="380" y="170" width="260" height="100" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="510" y="192" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Merged result</text>
  <text x="510" y="210" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="monospace">x-req-id   = generate  ← base</text>
  <text x="510" y="228" fill="#6db33f" font-size="10" text-anchor="middle" font-family="monospace">x-version  = "2"       ← prod wins</text>
  <text x="510" y="246" fill="#6db33f" font-size="10" text-anchor="middle" font-family="monospace">x-strict-ts = yes      ← prod only</text>

  <defs>
    <marker id="f1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="f2" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker>
    <marker id="f3" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>
</svg>

The prod profile's list completely replaces the base list (left). The prod profile's map entries are merged with the base map; only the conflicting key picks the higher-priority value (right).

## 5. Runnable example

```java
// src/main/resources/application.yml
// app:
//   allowed-origins:
//     - https://dev.example.com
//     - https://localhost:3000
//   headers:
//     x-request-id: generate
//     x-api-version: "1"

// src/main/resources/application-prod.yml
// app:
//   allowed-origins:
//     - https://prod.example.com
//   headers:
//     x-api-version: "2"
//     x-strict-transport: "max-age=31536000"

// src/main/java/com/example/config/AppConfig.java
package com.example.config;

import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.stereotype.Component;

import java.util.List;
import java.util.Map;

@Component
@ConfigurationProperties(prefix = "app")
public class AppConfig {

    private List<String>        allowedOrigins;
    private Map<String, String> headers;

    public List<String>        getAllowedOrigins()                         { return allowedOrigins; }
    public void                setAllowedOrigins(List<String> v)          { this.allowedOrigins = v; }
    public Map<String, String> getHeaders()                               { return headers; }
    public void                setHeaders(Map<String, String> headers)    { this.headers = headers; }
}

// src/main/java/com/example/MergeApp.java
package com.example;

import com.example.config.AppConfig;
import org.springframework.boot.CommandLineRunner;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.annotation.Bean;

@SpringBootApplication
public class MergeApp {

    public static void main(String[] args) {
        SpringApplication.run(MergeApp.class, args);
    }

    @Bean
    CommandLineRunner run(AppConfig cfg) {
        return args -> {
            System.out.println("=== allowedOrigins (list) ===");
            cfg.getAllowedOrigins().forEach(o -> System.out.println("  " + o));

            System.out.println("=== headers (map) ===");
            cfg.getHeaders().forEach((k, v) -> System.out.println("  " + k + " = " + v));
        };
    }
}
```

**How to run — without the prod profile (base only):**

```bash
./mvnw spring-boot:run
```

Expected:
```
=== allowedOrigins (list) ===
  https://dev.example.com
  https://localhost:3000
=== headers (map) ===
  x-request-id = generate
  x-api-version = 1
```

**How to run — with the prod profile (observe list replacement and map merging):**

```bash
./mvnw spring-boot:run -Dspring-boot.run.profiles=prod
```

Expected:
```
=== allowedOrigins (list) ===
  https://prod.example.com
=== headers (map) ===
  x-request-id = generate
  x-api-version = 2
  x-strict-transport = max-age=31536000
```

The list went from two items to one; the map gained one entry and updated another.

## 6. Walkthrough

- **`application.yml`** — defines the base configuration: two allowed origins and two headers.
- **`application-prod.yml`** — active only when the `prod` profile is enabled. It defines one allowed origin and two headers (one overlapping, one new).
- **`private List<String> allowedOrigins`** — when `prod` is active, Spring finds the key `app.allowed-origins` in `application-prod.yml` (higher priority) and uses that list in full. The base list from `application.yml` is completely discarded.
- **`private Map<String, String> headers`** — Spring merges the two maps. It starts with the base map (`x-request-id`, `x-api-version=1`) and then applies the prod map's entries. For `x-api-version`, prod wins (value becomes `"2"`). The new key `x-strict-transport` is added. The base-only key `x-request-id` survives because prod did not define it at all.
- **`-Dspring-boot.run.profiles=prod`** — activates the `prod` profile for the Maven plugin. The equivalent programmatic option is `spring.profiles.active=prod` in `application.properties`.
- **Ordering within a profile** — when multiple profiles are active, the last one in the `spring.profiles.active` list has the highest priority for property sources.

## 7. Gotchas & takeaways

> **There is no "additive list" mode in Spring Boot's property binding.** If `application.yml` has a list with five items and `application-prod.yml` has a list with one item, the prod list wins and you get exactly one item — the five base items are gone. This is the single most common source of configuration surprises in profile-based setups. Always write the full intended list in the highest-priority source.

> **Map keys are literal — they are not subject to relaxed binding.** If `application.yml` defines `app.headers.x-request-id` and `application-prod.yml` defines `app.headers.xRequestId`, Spring treats these as two different keys and the map will contain both. Only the structural prefix (`app.headers`) is relaxed; the map key itself (`x-request-id` vs `xRequestId`) is taken verbatim.

- If you need to add values to a list across profiles without rewriting the whole list, consider modelling the data as a `Map<String, String>` where the keys are arbitrary labels and the values are the real entries.
- You can override individual list elements using index notation in `application.properties`: `app.allowed-origins[0]=https://prod.example.com` — but this is fragile (index-based) and should be avoided in favour of fully defining the list in the higher-priority source.
- Command-line arguments also follow the replacement rule for lists: `--app.allowed-origins=https://only.example.com` replaces the full list with one item.
- The map-merging behaviour also applies when the same map key is set in two different property sources of the same priority level (e.g., two `application.yml` files on the classpath). Spring processes them in load order and the later source wins conflicting keys.
- When writing integration tests, be aware that `@TestPropertySource(properties = "app.headers.new-key=test")` merges into the existing map but `@TestPropertySource(properties = "app.allowed-origins=test-origin")` replaces the entire list.
