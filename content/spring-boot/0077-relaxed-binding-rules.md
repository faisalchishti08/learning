---
card: spring-boot
gi: 77
slug: relaxed-binding-rules
title: Relaxed binding rules
---

## 1. What it is

**Relaxed binding** is the algorithm Spring Boot uses to match a property key from any source — `application.properties`, YAML, env vars, or command-line args — to a field in a `@ConfigurationProperties` class, regardless of whether the key uses dots, hyphens, underscores, camelCase, or uppercase. The rule is: Spring converts all incoming keys to a canonical form and then checks whether the canonical form matches the canonical form of the field name.

In practice, `app.myProp`, `app.my-prop`, `app.my_prop`, `app.MY-PROP`, and `APP_MY_PROP` all bind to a field named `myProp`. You do not need to think about this most of the time — but when a property fails to bind, understanding these rules is the fastest path to a fix.

In one sentence: **Spring Boot's relaxed binding normalises every property key to a single canonical form so the same logical setting can be expressed in any of the common naming styles and still reach the right field.**

## 2. Why & when

Different environments produce property keys in different formats:

- **Java developers** write `application.properties` in kebab-case (`app.my-timeout`) because it is the Spring-recommended style.
- **Windows environments** may use underscore-separated names (`app_my_timeout`) because the system `PATH` variable uses underscores.
- **Docker and Kubernetes** expose env vars in SCREAMING_SNAKE_CASE (`APP_MY_TIMEOUT`) because hyphens are illegal in POSIX variable names.
- **Legacy systems** sometimes use camelCase in property files (`app.myTimeout`).

Without relaxed binding you would need separate code paths or property adapters for each environment. With it, a single `@ConfigurationProperties` class works everywhere, and you can choose whichever naming style your team prefers in each context.

Relaxed binding applies **exclusively to `@ConfigurationProperties`**. It does not apply to `@Value` — `@Value("${app.my-prop}")` will not match a property written as `app.myProp`. This is a deliberate design choice: `@Value` is explicit and exact, `@ConfigurationProperties` is flexible and structural.

## 3. Core concept

Spring Boot defines a **canonical form** for property keys: lowercase, with hyphens separating words. This is sometimes called **kebab-case** or the "relaxed canonical form."

The matching rules:

| Input key style | Example | Maps to canonical |
|---|---|---|
| Kebab-case (recommended) | `app.my-prop` | `app.my-prop` |
| camelCase | `app.myProp` | `app.my-prop` |
| Underscore-separated | `app.my_prop` | `app.my-prop` |
| UPPER_CASE env var (single `_` = dot) | `APP_MY_PROP` | `app.my-prop` |
| UPPER_CASE env var (double `__` = hyphen) | `APP_MY__PROP` | `app.my-prop` *(segment with hyphen)* |

When reading from `application.properties` or YAML, Spring Boot accepts any of the first three styles. When reading from environment variables, Spring applies the additional rules about single vs double underscores (covered in tutorial 73).

**Canonical form of a field name:**

Given a Java field `private String myProp`, Spring derives the canonical key segment by inserting a hyphen before every uppercase letter and converting to lowercase: `myProp` → `my-prop`. The binding succeeds if the canonical form of the incoming key segment matches the canonical form of the field name.

**What relaxed binding does NOT do:**

- It does not reorder segments: `app.timeout.my` will never bind to a field at `app.my.timeout`.
- It does not perform fuzzy or partial matching: `app.myprop` (missing hyphen, all lowercase) will match `myProp` because both canonicalise to `my-prop`, but `app.mypro` (truncated) will not match anything.
- It does not apply to `@Value` annotations.

## 4. Diagram

<svg viewBox="0 0 680 310" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Multiple property key styles all normalising to the same canonical form and binding to the same Java field">

  <!-- Input styles column -->
  <text x="100" y="22" fill="#8b949e" font-size="12" text-anchor="middle" font-family="sans-serif" font-weight="bold">Input (any style)</text>

  <rect x="20" y="34" width="165" height="30" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="102" y="54" fill="#79c0ff" font-size="12" text-anchor="middle" font-family="monospace">app.my-prop</text>

  <rect x="20" y="74" width="165" height="30" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="102" y="94" fill="#79c0ff" font-size="12" text-anchor="middle" font-family="monospace">app.myProp</text>

  <rect x="20" y="114" width="165" height="30" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="102" y="134" fill="#79c0ff" font-size="12" text-anchor="middle" font-family="monospace">app.my_prop</text>

  <rect x="20" y="154" width="165" height="30" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="102" y="174" fill="#79c0ff" font-size="12" text-anchor="middle" font-family="monospace">APP_MY_PROP</text>

  <rect x="20" y="194" width="165" height="30" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="102" y="214" fill="#79c0ff" font-size="12" text-anchor="middle" font-family="monospace">APP_MY__PROP</text>
  <text x="102" y="232" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">(double-underscore = hyphen)</text>

  <!-- Arrows converging -->
  <line x1="185" y1="49" x2="285" y2="155" stroke="#6db33f" stroke-width="1.2" marker-end="url(#e1)"/>
  <line x1="185" y1="89" x2="285" y2="155" stroke="#6db33f" stroke-width="1.2" marker-end="url(#e1)"/>
  <line x1="185" y1="129" x2="285" y2="155" stroke="#6db33f" stroke-width="1.2" marker-end="url(#e1)"/>
  <line x1="185" y1="169" x2="285" y2="155" stroke="#6db33f" stroke-width="1.2" marker-end="url(#e1)"/>
  <line x1="185" y1="209" x2="285" y2="165" stroke="#6db33f" stroke-width="1.2" marker-end="url(#e1)"/>

  <!-- Canonical form box -->
  <rect x="285" y="120" width="145" height="60" rx="10" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="357" y="144" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">Canonical form</text>
  <text x="357" y="165" fill="#6db33f" font-size="13" text-anchor="middle" font-family="monospace">app.my-prop</text>

  <!-- Arrow to Java field -->
  <line x1="430" y1="150" x2="508" y2="150" stroke="#79c0ff" stroke-width="2" marker-end="url(#e2)"/>
  <text x="469" y="142" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">binds to</text>

  <!-- Java field box -->
  <rect x="508" y="110" width="155" height="80" rx="10" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="585" y="136" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">Java field</text>
  <text x="585" y="158" fill="#79c0ff" font-size="12" text-anchor="middle" font-family="monospace">private String</text>
  <text x="585" y="175" fill="#79c0ff" font-size="12" text-anchor="middle" font-family="monospace">myProp;</text>

  <defs>
    <marker id="e1" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="e2" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>
</svg>

Five different input styles all canonicalise to `app.my-prop`, which matches the field `myProp`. Only one canonical form exists; the diversity lives in the input.

## 5. Runnable example

```java
// src/main/resources/application.properties
// (write in whichever style you prefer — all four bind to the same fields)
//
// app.my-service-name=relaxed-demo     <- kebab (recommended)
// app.maxRetries=3                     <- camelCase (also works)
// app.connect_timeout=5000             <- underscore (also works)

// src/main/java/com/example/config/AppSettings.java
package com.example.config;

import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.stereotype.Component;

@Component
@ConfigurationProperties(prefix = "app")
public class AppSettings {

    // Declare fields in camelCase — Spring derives the canonical key automatically
    private String myServiceName;   // matches app.my-service-name, app.myServiceName, APP_MY_SERVICE_NAME, etc.
    private int    maxRetries;      // matches app.max-retries, app.maxRetries, APP_MAX_RETRIES, etc.
    private long   connectTimeout;  // matches app.connect-timeout, app.connectTimeout, APP_CONNECT_TIMEOUT, etc.

    public String getMyServiceName()                      { return myServiceName; }
    public void   setMyServiceName(String myServiceName)  { this.myServiceName = myServiceName; }
    public int    getMaxRetries()                         { return maxRetries; }
    public void   setMaxRetries(int maxRetries)           { this.maxRetries = maxRetries; }
    public long   getConnectTimeout()                     { return connectTimeout; }
    public void   setConnectTimeout(long connectTimeout)  { this.connectTimeout = connectTimeout; }
}

// src/main/java/com/example/RelaxedBindingApp.java
package com.example;

import com.example.config.AppSettings;
import org.springframework.boot.CommandLineRunner;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.annotation.Bean;

@SpringBootApplication
public class RelaxedBindingApp {

    public static void main(String[] args) {
        SpringApplication.run(RelaxedBindingApp.class, args);
    }

    @Bean
    CommandLineRunner run(AppSettings settings) {
        return args -> {
            System.out.println("myServiceName  = " + settings.getMyServiceName());
            System.out.println("maxRetries     = " + settings.getMaxRetries());
            System.out.println("connectTimeout = " + settings.getConnectTimeout() + " ms");
        };
    }
}
```

**How to run:** pick any single style for each property in `application.properties` (all commented lines above are equivalent — use only one per key), then run `./mvnw spring-boot:run`. Expected output:

```
myServiceName  = relaxed-demo
maxRetries     = 3
connectTimeout = 5000 ms
```

To verify env-var binding, skip the properties file and instead set:
```bash
export APP_MY_SERVICE_NAME=env-demo
export APP_MAX_RETRIES=7
export APP_CONNECT_TIMEOUT=9000
./mvnw spring-boot:run
```

## 6. Walkthrough

- **`private String myServiceName`** — the canonical form Spring derives is `my-service-name`. An incoming key of `app.my-service-name`, `app.myServiceName`, or `app.my_service_name` all normalise to `my-service-name` and match this field.
- **`private int maxRetries`** — canonical form is `max-retries`. Spring converts the matched string value `"3"` to the primitive `int` 3 automatically.
- **`private long connectTimeout`** — canonical form is `connect-timeout`. The value `5000` arrives as a string and is converted to `long`.
- **`application.properties` with `app.my-service-name=relaxed-demo`** — kebab-case is the Spring-recommended style for `.properties` and `.yml` files. It is the canonical form itself, so no normalisation is needed.
- **`app.maxRetries=3`** — camelCase in a `.properties` file. Spring normalises `maxRetries` to `max-retries` before matching.
- **`app.connect_timeout=5000`** — underscore-separated. Spring normalises `connect_timeout` to `connect-timeout` before matching.
- **Env vars** — the `APP_MAX_RETRIES=7` line uses SCREAMING_SNAKE_CASE: `APP` maps to prefix `app`, `MAX_RETRIES` maps to segment `max-retries` after lower-casing and replacing `_` with `-`.

## 7. Gotchas & takeaways

> **Relaxed binding only applies to `@ConfigurationProperties`**, not to `@Value`. If you write `@Value("${app.myProp}")` and the property file has `app.my-prop`, Spring will not find the value and the injection will fail (or produce `null` if you used `${app.myProp:}` with a default). There is no relaxed lookup for `@Value` — the key must be exact.

> Writing the same property key in two different styles in the **same** property source (e.g., both `app.myProp=a` and `app.my-prop=b` in the same `application.properties`) is a misconfiguration. Both normalise to the same canonical form, and which one wins is effectively undefined. Spring Boot will log a warning but pick one value arbitrarily. Use a single consistent style per file.

- The Spring team recommends **kebab-case** (`app.my-prop`) for `application.properties` and `application.yml` because it is identical to the canonical form and creates the least ambiguity.
- For environment variables, use **SCREAMING_SNAKE_CASE** with single underscores for dots (`APP_MY_PROP`) and double underscores for hyphens within a segment (`APP_MY__PROP` → `app.my-prop`).
- Relaxed binding does not apply to map keys. If a `@ConfigurationProperties` field is `Map<String, String>`, the map keys are taken literally, with no normalisation — only the structural prefix is relaxed.
- Running `./mvnw spring-boot:run -Ddebug=true` and searching the output for `Binding` will show exactly which property source and key Spring used to populate each field — invaluable for debugging binding failures.
- The IDE annotation processor (add `spring-boot-configuration-processor` as an optional dependency) generates metadata that documents which keys bind to which fields, making autocomplete in `application.yml` accurate even for camelCase field names.
