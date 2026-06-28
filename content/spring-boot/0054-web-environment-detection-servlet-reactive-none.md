---
card: spring-boot
gi: 54
slug: web-environment-detection-servlet-reactive-none
title: Web environment detection (SERVLET/REACTIVE/NONE)
---

## 1. What it is

**Web environment detection** is the mechanism by which Spring Boot automatically determines what kind of `ApplicationContext` to create based on the classes available on the classpath. The result is one of three `WebApplicationType` values:

| Type | When | ApplicationContext created |
|---|---|---|
| `SERVLET` | `spring-webmvc` (or `spring-web`) on classpath | `AnnotationConfigServletWebServerApplicationContext` |
| `REACTIVE` | `spring-webflux` on classpath, no `spring-webmvc` | `AnnotationConfigReactiveWebServerApplicationContext` |
| `NONE` | Neither web framework on classpath | `AnnotationConfigApplicationContext` |

Detection happens before the `ApplicationContext` is created. You can override the detected type:
```java
SpringApplication.run(MyApp.class, args);                    // auto-detect
// or
new SpringApplication(MyApp.class)
    .setWebApplicationType(WebApplicationType.NONE)           // force override
    .run(args);
// or in application.properties:
// spring.main.web-application-type=none
```

## 2. Why & when

Spring Boot aims to be a single binary for web apps, reactive apps, batch jobs, and CLI tools. Without auto-detection, you'd need to choose and configure the right `ApplicationContext` manually. Auto-detection picks the correct context type for your dependency mix.

Understand this when:
- You have web JARs on the classpath (from indirect dependencies) but are writing a batch job — force `NONE` to avoid starting a server.
- You are migrating from MVC to WebFlux — understanding the detection order prevents accidentally getting the wrong context type when both JARs are present.
- You write integration tests and want `WebApplicationType.NONE` for fast, server-less tests.
- Your auto-configured context type is wrong and you need to know how to override it.

## 3. Core concept

`SpringApplication` runs detection in `WebApplicationType.deduceFromClasspath()`. The logic:

1. If `WEBFLUX_INDICATOR_CLASS` (`org.springframework.web.reactive.DispatcherHandler`) is on the classpath **and** `WEBMVC_INDICATOR_CLASS` (`org.springframework.web.servlet.DispatcherServlet`) is NOT — → `REACTIVE`.
2. If any servlet indicator class is on the classpath — → `SERVLET`.
3. Otherwise — → `NONE`.

Key point: if both `spring-webmvc` and `spring-webflux` are on the classpath, Spring Boot picks **`SERVLET`** (rule 2 fires before rule 1 can exclusively match). WebFlux is only chosen when MVC is absent.

The detected type then determines:
- Which `ApplicationContext` class is instantiated.
- Whether an embedded server (Tomcat / Netty) is started.
- Which auto-configurations are activated (servlet vs. reactive).

## 4. Diagram

<svg viewBox="0 0 660 240" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="WebApplicationType detection decision tree based on classpath classes">
  <!-- Decision tree -->
  <rect x="220" y="20" width="220" height="40" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="330" y="45" fill="#6db33f" font-size="11" font-family="monospace" text-anchor="middle">deduceFromClasspath()</text>

  <!-- Q1: servlet indicator? -->
  <rect x="220" y="80" width="220" height="40" rx="6" fill="#2d3748" stroke="#8b949e" stroke-width="1.5"/>
  <text x="330" y="105" fill="#e6edf3" font-size="11" font-family="monospace" text-anchor="middle">DispatcherServlet on classpath?</text>

  <!-- Q2: only webflux? -->
  <rect x="20" y="150" width="220" height="40" rx="6" fill="#2d3748" stroke="#8b949e" stroke-width="1.5"/>
  <text x="130" y="175" fill="#e6edf3" font-size="11" font-family="monospace" text-anchor="middle">DispatcherHandler only?</text>

  <!-- SERVLET result -->
  <rect x="430" y="150" width="200" height="40" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="530" y="175" fill="#6db33f" font-size="11" font-family="monospace" text-anchor="middle">SERVLET → Tomcat</text>

  <!-- REACTIVE result -->
  <rect x="20" y="210" width="200" height="24" rx="5" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="120" y="227" fill="#79c0ff" font-size="10" font-family="monospace" text-anchor="middle">REACTIVE → Netty</text>

  <!-- NONE result -->
  <rect x="240" y="210" width="160" height="24" rx="5" fill="#2d3748" stroke="#8b949e" stroke-width="1.5"/>
  <text x="320" y="227" fill="#8b949e" font-size="10" font-family="monospace" text-anchor="middle">NONE → no server</text>

  <!-- Arrows -->
  <line x1="330" y1="60" x2="330" y2="78" stroke="#6db33f" stroke-width="1.5" marker-end="url(#wd)"/>
  <line x1="330" y1="120" x2="530" y2="148" stroke="#6db33f" stroke-width="2" marker-end="url(#wd)"/>
  <text x="430" y="138" fill="#6db33f" font-size="10" font-family="sans-serif" text-anchor="middle">YES</text>
  <line x1="330" y1="120" x2="130" y2="148" stroke="#8b949e" stroke-width="1.5" marker-end="url(#wd)"/>
  <text x="220" y="138" fill="#8b949e" font-size="10" font-family="sans-serif" text-anchor="middle">NO</text>
  <line x1="80" y1="190" x2="80" y2="208" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#wd)"/>
  <text x="56" y="204" fill="#79c0ff" font-size="10" font-family="sans-serif">YES</text>
  <line x1="180" y1="190" x2="320" y2="208" stroke="#8b949e" stroke-width="1.5" marker-end="url(#wd)"/>
  <text x="270" y="204" fill="#8b949e" font-size="10" font-family="sans-serif">NO</text>

  <defs>
    <marker id="wd" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/>
    </marker>
  </defs>
</svg>

`DispatcherServlet` presence → `SERVLET`; only `DispatcherHandler` → `REACTIVE`; neither → `NONE`.

## 5. Runnable example

```java
// WebTypeDetectionDemo.java
// How to run: java WebTypeDetectionDemo.java  (JDK 17+)
// Simulates Spring Boot's WebApplicationType.deduceFromClasspath() logic.

import java.util.*;

public class WebTypeDetectionDemo {

    enum WebApplicationType { SERVLET, REACTIVE, NONE }

    // Indicator class names Spring Boot checks
    static final String SERVLET_INDICATOR  = "org.springframework.web.servlet.DispatcherServlet";
    static final String REACTIVE_INDICATOR = "org.springframework.web.reactive.DispatcherHandler";

    static WebApplicationType deduce(Set<String> classpath) {
        boolean hasServlet  = classpath.contains(SERVLET_INDICATOR);
        boolean hasReactive = classpath.contains(REACTIVE_INDICATOR);

        if (hasServlet) return WebApplicationType.SERVLET;   // servlet wins if both present
        if (hasReactive) return WebApplicationType.REACTIVE;
        return WebApplicationType.NONE;
    }

    static String contextType(WebApplicationType type) {
        return switch (type) {
            case SERVLET  -> "AnnotationConfigServletWebServerApplicationContext (Tomcat starts)";
            case REACTIVE -> "AnnotationConfigReactiveWebServerApplicationContext (Netty starts)";
            case NONE     -> "AnnotationConfigApplicationContext (no embedded server)";
        };
    }

    public static void main(String[] args) {
        record Scenario(String name, Set<String> classpath) {}

        List<Scenario> scenarios = List.of(
            new Scenario("spring-webmvc only",
                Set.of(SERVLET_INDICATOR)),
            new Scenario("spring-webflux only",
                Set.of(REACTIVE_INDICATOR)),
            new Scenario("both MVC + WebFlux (e.g. mixed project)",
                Set.of(SERVLET_INDICATOR, REACTIVE_INDICATOR)),
            new Scenario("batch / CLI (no web framework)",
                Set.of("org.springframework.batch.core.Job"))
        );

        System.out.println("=== WebApplicationType detection ===\n");
        for (Scenario s : scenarios) {
            WebApplicationType detected = deduce(s.classpath());
            System.out.println("Scenario: " + s.name());
            System.out.println("  Detected type: " + detected);
            System.out.println("  Context class: " + contextType(detected));
            System.out.println();
        }

        System.out.println("Override via: spring.main.web-application-type=none");
        System.out.println("   or: new SpringApplication().setWebApplicationType(NONE)");
    }
}
```

**How to run:** `java WebTypeDetectionDemo.java`

Expected output:
```
=== WebApplicationType detection ===

Scenario: spring-webmvc only
  Detected type: SERVLET
  Context class: AnnotationConfigServletWebServerApplicationContext (Tomcat starts)

Scenario: spring-webflux only
  Detected type: REACTIVE
  Context class: AnnotationConfigReactiveWebServerApplicationContext (Netty starts)

Scenario: both MVC + WebFlux (e.g. mixed project)
  Detected type: SERVLET
  Context class: AnnotationConfigServletWebServerApplicationContext (Tomcat starts)

Scenario: batch / CLI (no web framework)
  Detected type: NONE
  Context class: AnnotationConfigApplicationContext (no embedded server)

Override via: spring.main.web-application-type=none
   or: new SpringApplication().setWebApplicationType(NONE)
```

## 6. Walkthrough

- `deduce()` mirrors `WebApplicationType.deduceFromClasspath()` in Spring Boot source. The order of checks is critical: servlet check comes first.
- When both MVC and WebFlux are on the classpath, `SERVLET` wins — the servlet check is unconditional. This is often surprising but intentional; Spring Boot treats MVC as the higher-priority web framework.
- The batch/CLI scenario has no web indicator → `NONE`. The correct `ApplicationContext` is a plain `AnnotationConfigApplicationContext` with no embedded server.
- `contextType()` maps the enum to the actual Spring class name, showing what `SpringApplication` instantiates based on detection.
- The note at the bottom shows both override mechanisms: property file (environment-level) and code-level (builder/setter).

## 7. Gotchas & takeaways

> Having `spring-webmvc` as a transitive dependency of a non-web library is a common source of surprise. The detection sees `DispatcherServlet` and starts Tomcat, even though your batch job never needs a server. Force `NONE` explicitly in this case.

> Reactive applications (`REACTIVE` type) use `spring-webflux` but the detection also checks for the absence of `spring-webmvc`. A migration project that adds WebFlux while MVC is still present will remain on the SERVLET stack until MVC is removed.

- Override with `spring.main.web-application-type=none|servlet|reactive` in `application.properties` (or environment variable `SPRING_MAIN_WEB_APPLICATION_TYPE=none`).
- `WebApplicationType.NONE` is the fastest startup — no server, no servlet context, no reactive runtime initialised.
- In tests: `@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.NONE)` sets `NONE` for the test context, regardless of the app's detected type.
- Spring Boot Actuator's endpoint group and `/actuator/info` response can reveal `web-application-type` at runtime if you expose the `info` endpoint.
