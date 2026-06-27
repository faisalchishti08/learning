---
card: spring-boot
gi: 46
slug: springapplication-class
title: SpringApplication class
---

## 1. What it is

`SpringApplication` is the class that bootstraps a Spring Boot application. Its static `run()` method is the single call that starts everything: it creates the Spring `ApplicationContext`, triggers auto-configuration, starts the embedded web server, and makes the application ready to handle requests.

```java
@SpringBootApplication
public class MyApp {
    public static void main(String[] args) {
        SpringApplication.run(MyApp.class, args);  // one line starts the world
    }
}
```

`SpringApplication` can also be instantiated directly for customisation before the context starts:

```java
SpringApplication app = new SpringApplication(MyApp.class);
app.setBannerMode(Banner.Mode.OFF);
app.setWebApplicationType(WebApplicationType.NONE);
SpringApplication.run(app, args); // or app.run(args)
```

## 2. Why & when

Before Spring Boot, starting a Spring application required setting up a `ClassPathXmlApplicationContext` or `AnnotationConfigApplicationContext`, registering configuration classes, calling `refresh()`, and managing the lifecycle manually. `SpringApplication` hides all of this behind one method call with sensible defaults.

Know `SpringApplication` directly when you need to:
- Customise startup **before** the `ApplicationContext` is created (e.g. set a specific context type, add `ApplicationListener`s, change the banner).
- Register `SpringApplicationRunListener`s for observability hooks.
- Control web application type (`SERVLET`, `REACTIVE`, `NONE`).
- Run integration tests programmatically.

## 3. Core concept

Think of `SpringApplication.run()` as a **launch sequence** with well-defined stages. Each stage can be observed and customised.

The key stages in order:

1. **Determine application type** — SERVLET, REACTIVE, or NONE, based on which classes are on the classpath.
2. **Load `ApplicationContextInitializer`s** — from `spring.factories`, they customise the context before it is refreshed.
3. **Load `ApplicationListener`s** — from `spring.factories`, they react to application events.
4. **Print banner** — the Spring Boot logo (or your custom banner).
5. **Create `ApplicationContext`** — the appropriate context type (`AnnotationConfigServletWebServerApplicationContext` for web, etc.).
6. **Prepare context** — apply `ApplicationContextInitializer`s, load primary sources (`MyApp.class`).
7. **Refresh context** — triggers bean instantiation, auto-configuration, component scanning.
8. **Start embedded server** — Tomcat/Jetty/Undertow starts listening.
9. **Publish `ApplicationReadyEvent`** — the app is ready; `CommandLineRunner`s and `ApplicationRunner`s execute.

## 4. Diagram

<svg viewBox="0 0 660 280" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="SpringApplication.run() launch sequence from main() to ApplicationReadyEvent">
  <!-- Stages as a vertical pipeline -->
  <rect x="20" y="20" width="620" height="40" rx="6" fill="#2d3748" stroke="#8b949e" stroke-width="1.5"/>
  <text x="330" y="46" fill="#e6edf3" font-size="12" font-family="monospace" text-anchor="middle">1. main() → SpringApplication.run(MyApp.class, args)</text>

  <rect x="20" y="70" width="300" height="36" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="170" y="93" fill="#8b949e" font-size="11" font-family="monospace" text-anchor="middle">2. detect app type (SERVLET/REACTIVE/NONE)</text>

  <rect x="340" y="70" width="300" height="36" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="490" y="93" fill="#8b949e" font-size="11" font-family="monospace" text-anchor="middle">3. load listeners + initializers</text>

  <rect x="20" y="116" width="620" height="36" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="330" y="139" fill="#79c0ff" font-size="11" font-family="monospace" text-anchor="middle">4. create ApplicationContext + prepare (load primary source)</text>

  <rect x="20" y="162" width="620" height="36" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="330" y="185" fill="#6db33f" font-size="11" font-family="monospace" text-anchor="middle">5. refresh context → auto-config, scanning, bean creation</text>

  <rect x="20" y="208" width="300" height="36" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="170" y="231" fill="#6db33f" font-size="11" font-family="monospace" text-anchor="middle">6. start embedded server (Tomcat)</text>

  <rect x="340" y="208" width="300" height="36" rx="6" fill="#16202e" stroke="#6db33f" stroke-width="2"/>
  <text x="490" y="231" fill="#e6edf3" font-size="11" font-family="monospace" text-anchor="middle">7. ApplicationReadyEvent → app live!</text>

  <!-- Connecting arrows -->
  <line x1="330" y1="60" x2="330" y2="68" stroke="#8b949e" stroke-width="1.5" marker-end="url(#sp)"/>
  <line x1="330" y1="106" x2="330" y2="114" stroke="#8b949e" stroke-width="1.5" marker-end="url(#sp)"/>
  <line x1="330" y1="152" x2="330" y2="160" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#sp)"/>
  <line x1="330" y1="198" x2="330" y2="206" stroke="#6db33f" stroke-width="2" marker-end="url(#sp)"/>

  <defs>
    <marker id="sp" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/>
    </marker>
  </defs>
</svg>

`SpringApplication.run()` is a seven-stage sequence from a single `main()` call to a fully live application.

## 5. Runnable example

```java
// SpringApplicationDemo.java
// How to run: java SpringApplicationDemo.java  (JDK 17+)
// Simulates the SpringApplication launch sequence and customisation points.

import java.util.*;

public class SpringApplicationDemo {

    // Simulated configuration
    enum WebApplicationType { SERVLET, REACTIVE, NONE }

    static WebApplicationType appType      = WebApplicationType.SERVLET;
    static boolean            showBanner   = true;
    static List<String>       listeners    = new ArrayList<>();
    static List<String>       initializers = new ArrayList<>();
    static Map<String, Object> context     = new LinkedHashMap<>();

    public static void main(String[] args) {
        System.out.println("=== SpringApplication.run() simulation ===\n");

        // ── Customise before run (equivalent to new SpringApplication(...) + setters) ──
        showBanner = false;                            // app.setBannerMode(CONSOLE)
        listeners.add("LoggingApplicationListener");   // added via spring.factories
        listeners.add("BackgroundPreinitializer");
        initializers.add("ContextIdApplicationContextInitializer");

        run("MyApp.class", args);
    }

    static void run(String primarySource, String[] args) {
        stage(1, "determine application type → " + appType);

        stage(2, "load ApplicationListeners from spring.factories:");
        listeners.forEach(l -> System.out.println("      " + l));

        stage(3, "load ApplicationContextInitializers:");
        initializers.forEach(i -> System.out.println("      " + i));

        if (showBanner) {
            System.out.println("\n  :: Spring Boot ::\n");
        } else {
            stage(4, "banner suppressed (setBannerMode(OFF))");
        }

        stage(5, "create ApplicationContext ("
            + (appType == WebApplicationType.SERVLET ? "AnnotationConfigServletWebServerApplicationContext"
               : "AnnotationConfigApplicationContext") + ")");

        stage(6, "prepare context — load primary source: " + primarySource);
        initializers.forEach(i -> System.out.println("      apply initializer: " + i));

        stage(7, "refresh context (auto-config + component scan + bean creation)");
        context.put("myService",       "MyService");
        context.put("dataSource",      "HikariDataSource");
        context.put("dispatcherServlet","DispatcherServlet");
        context.forEach((k, v) -> System.out.println("      bean: " + k + " → " + v));

        if (appType == WebApplicationType.SERVLET) {
            stage(8, "start embedded Tomcat on port 8080");
        }

        stage(9, "publish ApplicationReadyEvent → app is live!");
        System.out.println("\n✅ Started in simulated 1.234s");
    }

    static int stageNum = 0;
    static void stage(int n, String msg) {
        System.out.println("[" + n + "] " + msg);
    }
}
```

**How to run:** `java SpringApplicationDemo.java`

Expected output:
```
=== SpringApplication.run() simulation ===

[1] determine application type → SERVLET
[2] load ApplicationListeners from spring.factories:
      LoggingApplicationListener
      BackgroundPreinitializer
[3] load ApplicationContextInitializers:
      ContextIdApplicationContextInitializer
[4] banner suppressed (setBannerMode(OFF))
[5] create ApplicationContext (AnnotationConfigServletWebServerApplicationContext)
[6] prepare context — load primary source: MyApp.class
      apply initializer: ContextIdApplicationContextInitializer
[7] refresh context (auto-config + component scan + bean creation)
      bean: myService → MyService
      bean: dataSource → HikariDataSource
      bean: dispatcherServlet → DispatcherServlet
[8] start embedded Tomcat on port 8080
[9] publish ApplicationReadyEvent → app is live!

✅ Started in simulated 1.234s
```

## 6. Walkthrough

- Stage 1 shows how `SpringApplication` detects the application type. In real Spring Boot it checks for `DispatcherServlet` (SERVLET), `DispatcherHandler` (REACTIVE), or neither (NONE) on the classpath.
- Stages 2-3 load framework listeners and initializers from `META-INF/spring.factories`. These are the first extension points — they run before the context exists.
- Banner suppression simulates `app.setBannerMode(Banner.Mode.OFF)` — common in production logs or test suites.
- Stage 5 creates the appropriate `ApplicationContext` subtype. For web apps this is `AnnotationConfigServletWebServerApplicationContext`, which includes embedded server management.
- Stage 7 (context refresh) is where the bulk of work happens: component scanning, auto-configuration evaluation, `@Bean` method invocation, dependency injection.
- Stage 9 fires `ApplicationReadyEvent` — this is when `CommandLineRunner` and `ApplicationRunner` beans execute.

## 7. Gotchas & takeaways

> Calling `SpringApplication.run()` multiple times in the same JVM (e.g. in tests) creates multiple `ApplicationContext` instances. Each creates its own embedded server on the default port 8080. Use `server.port=0` in test properties to assign a random port, or use `@SpringBootTest` which manages context lifecycle automatically.

> Registering additional beans or changing configuration **after** `SpringApplication.run()` returns is too late — the context is already refreshed and the server is running. Use `ApplicationContextInitializer` or `@PostConstruct` for startup hooks instead.

- `SpringApplication.run(MyApp.class, args)` is equivalent to `new SpringApplication(MyApp.class).run(args)` — use the second form when you need to customise before startup.
- Customisation methods: `setWebApplicationType()`, `setBannerMode()`, `addListeners()`, `addInitializers()`, `setDefaultProperties()`, `setAdditionalProfiles()`.
- `ApplicationContext` is returned by `run()` — useful in tests or CLI tools that need to look up beans programmatically.
- For background work after startup, implement `CommandLineRunner` or `ApplicationRunner` — Spring calls them once the context is fully refreshed.
- `SpringApplication.exit()` registers a shutdown hook that closes the context cleanly, triggering `@PreDestroy` callbacks and `DisposableBean.destroy()` methods.
