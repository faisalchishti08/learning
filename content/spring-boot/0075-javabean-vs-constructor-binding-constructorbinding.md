---
card: spring-boot
gi: 75
slug: javabean-vs-constructor-binding-constructorbinding
title: "JavaBean vs constructor binding (@ConstructorBinding)"
---

## 1. What it is

Spring Boot supports two strategies for populating a `@ConfigurationProperties` class:

**JavaBean binding** (the default) creates an instance with the no-arg constructor, then calls setters for each matched property. The resulting object is mutable — any code that holds a reference can modify it after creation.

**Constructor binding** populates the object by passing all values directly to a constructor. The object is fully initialised at creation time and can be made completely immutable — no setters needed. In Spring Boot 3.x, Java **records** work here out of the box because a record's compact constructor is exactly what Spring needs.

In one sentence: **constructor binding lets you make your configuration objects immutable by injecting all property values through the constructor rather than through setters.**

## 2. Why & when

Mutable configuration objects are a liability in multi-threaded applications. If a bean somewhere accidentally calls a setter — or if a test mutates the shared instance to change one value — every other bean that holds a reference silently sees the change. Tracking down that class of bug is painful.

Constructor binding removes the problem entirely:

- **Immutability by design** — no setters means no accidental mutation.
- **`final` fields** — the compiler enforces that every field is assigned exactly once.
- **Records as first-class citizens** — Java records (added in Java 16) naturally express immutable data; Spring Boot 3.x treats them as constructor-binding targets without any extra annotation.
- **Cleaner null-safety** — required fields become constructor parameters; the object cannot exist in a partially-initialised state.

Use constructor binding when:
- Your configuration class represents values that should not change after startup.
- You want to use Java records to reduce boilerplate.
- You're writing library code and want to prevent downstream callers from mutating your configuration object.

Stick with JavaBean binding when:
- The configuration class has optional or computed fields that are tricky to thread through a single constructor.
- You're working with a legacy codebase where setters already exist.
- You want to take advantage of default field values that are set at declaration time.

## 3. Core concept

**JavaBean binding flow:**

1. Spring calls the **no-arg constructor** to create the instance.
2. For each matched property key, Spring calls the corresponding **setter** (`setName(...)`, `setTimeout(...)`).
3. The object is mutable after this point — setters remain callable.

**Constructor binding flow:**

1. Spring inspects the class for a **single constructor** (or a constructor annotated with `@ConstructorBinding` when multiple exist).
2. It matches each **constructor parameter name** against the property namespace.
3. It calls that single constructor with all values resolved. The object is fully initialised and (if you declare `final` fields) immutable.

**Annotation requirements by Spring Boot version:**

| Setup | Spring Boot 2.x | Spring Boot 3.x |
|---|---|---|
| Class with setters | `@ConfigurationProperties` | `@ConfigurationProperties` |
| Immutable class (one constructor) | `@ConstructorBinding` required | `@ConstructorBinding` **optional** (auto-detected) |
| Java record | `@ConstructorBinding` required | No annotation needed |

In Spring Boot 3.x, if a `@ConfigurationProperties` class has **exactly one constructor**, Spring automatically uses constructor binding. `@ConstructorBinding` is still needed to disambiguate when multiple constructors exist.

**Parameter names** — Spring needs access to actual parameter names at runtime, not the synthetic names the JVM generates. The Spring Boot Maven/Gradle plugin always compiles with `-parameters`, so this works without any extra configuration in Boot projects.

## 4. Diagram

<svg viewBox="0 0 680 310" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Comparison of JavaBean binding (uses setters, mutable) vs constructor binding (uses constructor, immutable)">

  <!-- left panel: JavaBean -->
  <rect x="20" y="20" width="295" height="270" rx="10" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="167" y="48" fill="#e6edf3" font-size="13" text-anchor="middle" font-family="sans-serif" font-weight="bold">JavaBean Binding</text>
  <text x="167" y="66" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">(default)</text>

  <!-- step boxes left -->
  <rect x="38" y="80" width="259" height="32" rx="6" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="167" y="100" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="monospace">new AppProps() ← no-arg ctor</text>

  <line x1="167" y1="112" x2="167" y2="128" stroke="#8b949e" stroke-width="1.5" marker-end="url(#c1)"/>

  <rect x="38" y="130" width="259" height="32" rx="6" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="167" y="150" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="monospace">setName("my-service")</text>

  <line x1="167" y1="162" x2="167" y2="178" stroke="#8b949e" stroke-width="1.5" marker-end="url(#c2)"/>

  <rect x="38" y="180" width="259" height="32" rx="6" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="167" y="200" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="monospace">setTimeout(30)</text>

  <text x="167" y="240" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">Result: mutable object</text>
  <text x="167" y="257" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">setters still callable</text>

  <!-- right panel: Constructor binding -->
  <rect x="365" y="20" width="295" height="270" rx="10" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="512" y="48" fill="#e6edf3" font-size="13" text-anchor="middle" font-family="sans-serif" font-weight="bold">Constructor Binding</text>
  <text x="512" y="66" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">(@ConstructorBinding / record)</text>

  <!-- step box right -->
  <rect x="383" y="80" width="259" height="54" rx="6" fill="#0d1117" stroke="#6db33f" stroke-width="1"/>
  <text x="512" y="103" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="monospace">new AppProps(</text>
  <text x="512" y="120" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="monospace">  "my-service", 30)</text>

  <line x1="512" y1="135" x2="512" y2="158" stroke="#6db33f" stroke-width="1.5" marker-end="url(#c3)"/>

  <rect x="383" y="160" width="259" height="32" rx="6" fill="#0d1117" stroke="#6db33f" stroke-width="1"/>
  <text x="512" y="180" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="monospace">final String name = "my-service"</text>

  <text x="512" y="220" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">Result: immutable object</text>
  <text x="512" y="237" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">no setters, fields are final</text>

  <defs>
    <marker id="c1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker>
    <marker id="c2" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker>
    <marker id="c3" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>
</svg>

JavaBean binding calls setters one by one, leaving the object open to further mutation. Constructor binding calls one constructor and produces a closed object.

## 5. Runnable example

```java
// src/main/resources/application.yml
// app:
//   name: demo-service
//   timeout: 15
//   tags:
//     - public
//     - v2

// ---- Option A: Traditional class with @ConstructorBinding (Boot 2.x compatible) ----
package com.example.config;

import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.boot.context.properties.bind.ConstructorBinding;

import java.util.List;

@ConfigurationProperties(prefix = "app")
public class AppPropsConstructor {

    private final String name;
    private final int timeout;
    private final List<String> tags;

    @ConstructorBinding  // explicit in Boot 2.x, optional in Boot 3.x single-ctor case
    public AppPropsConstructor(String name, int timeout, List<String> tags) {
        this.name    = name;
        this.timeout = timeout;
        this.tags    = List.copyOf(tags != null ? tags : List.of());
    }

    public String       getName()    { return name; }
    public int          getTimeout() { return timeout; }
    public List<String> getTags()    { return tags; }
}

// ---- Option B: Java record (Spring Boot 3.x / Java 16+) ----
package com.example.config;

import org.springframework.boot.context.properties.ConfigurationProperties;
import java.util.List;

@ConfigurationProperties(prefix = "app")
public record AppPropsRecord(String name, int timeout, List<String> tags) {}

// ---- Main application ----
package com.example;

import com.example.config.AppPropsRecord;
import org.springframework.boot.CommandLineRunner;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.context.properties.EnableConfigurationProperties;
import org.springframework.context.annotation.Bean;

@SpringBootApplication
@EnableConfigurationProperties(AppPropsRecord.class)
public class ConstructorBindingApp {

    public static void main(String[] args) {
        SpringApplication.run(ConstructorBindingApp.class, args);
    }

    @Bean
    CommandLineRunner run(AppPropsRecord props) {
        return args -> {
            System.out.println("name    = " + props.name());
            System.out.println("timeout = " + props.timeout());
            System.out.println("tags    = " + props.tags());
        };
    }
}
```

**How to run:** create `application.yml` with the block shown in the comment, then run `./mvnw spring-boot:run`. Expected output:

```
name    = demo-service
timeout = 15
tags    = [public, v2]
```

Note that `AppPropsRecord` has no setters — Spring Boot populates it entirely through the record's canonical constructor.

## 6. Walkthrough

- **`AppPropsConstructor`** — declares three `final` fields and one constructor. Because fields are `final`, they can only be set in the constructor, enforcing immutability at compile time.
- **`@ConstructorBinding`** — in Spring Boot 2.x this annotation on the constructor is mandatory to opt into constructor binding. In Spring Boot 3.x with a single constructor it is inferred, but it is still valid and useful for clarity.
- **`List.copyOf(tags != null ? tags : List.of())`** — defensive copy inside the constructor ensures no external reference can mutate the list after the object is created. Without this, the object is immutable in name only if `tags` is a mutable list.
- **`AppPropsRecord`** — a Java record. The record compiler generates a canonical constructor that takes `name`, `timeout`, and `tags` as parameters and assigns them to the corresponding components. Spring Boot 3.x recognises this and uses constructor binding automatically.
- **`@EnableConfigurationProperties(AppPropsRecord.class)`** — since `AppPropsRecord` has no `@Component` annotation, this line on the main class registers it as a configuration properties bean. Alternatively, `@ConfigurationPropertiesScan` would discover it automatically (see tutorial 76).
- **`props.name()`** — record accessor syntax (not `getName()`). Spring Boot has no problem with this; it uses constructor parameters, not accessor method names, for binding.

## 7. Gotchas & takeaways

> When using constructor binding, Spring Boot **cannot inject optional properties** with a default value the same way JavaBean binding can (where you simply initialise the field with a default). To express an optional property, either use `@DefaultValue("fallback")` on the constructor parameter (available since Spring Boot 2.3), or use a `java.util.Optional<T>` parameter type.

> In Spring Boot 2.x, putting `@ConstructorBinding` on the **class** instead of the **constructor** was the required style. In Spring Boot 3.x, the annotation was moved to `org.springframework.boot.context.properties.bind.ConstructorBinding` and should go on the constructor. Using the old class-level placement still compiles but emits a deprecation warning.

- Java records are the most concise constructor-binding target: one line declares the type, and Spring Boot handles everything.
- If a record field is a `List` or `Map`, consider wrapping it in `List.copyOf()` inside a compact constructor to keep true immutability.
- Constructor binding requires Spring to know the parameter **names** at runtime. The Spring Boot build plugins compile with `-parameters` automatically; if you're running outside a Boot project, add that compiler flag manually.
- You cannot mix constructor binding and setter binding in the same class — Spring picks one strategy per class.
- `@DefaultValue("5m")` on a constructor parameter accepts the same flexible format that property files do, including unit suffixes for `Duration` and `DataSize`.
