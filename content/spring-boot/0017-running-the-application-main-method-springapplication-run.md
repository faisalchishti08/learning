---
card: spring-boot
gi: 17
slug: running-the-application-main-method-springapplication-run
title: Running the application (main method / SpringApplication.run)
---

## 1. What it is

`SpringApplication.run(App.class, args)` is the single line that starts a Spring Boot application. It is called from a standard Java `public static void main(String[] args)` method — making a Spring Boot app a regular Java program that any JVM can launch.

```java
public static void main(String[] args) {
    SpringApplication.run(MyApp.class, args);
}
```

Behind this one line, `SpringApplication` orchestrates: environment setup, `ApplicationContext` creation, auto-configuration, bean instantiation, embedded server start, and application event publishing — in a specific, predictable order.

## 2. Why & when

Before Spring Boot, launching a Spring web application required deploying a WAR to an external servlet container. There was no "run from `main`." Spring Boot changed this by making the embedded server a bean in the `ApplicationContext` — so starting the context starts the server, and starting the context is as simple as calling `main`.

Understand `SpringApplication.run` when:
- **Debugging startup failures** — the startup log lines correspond to phases of `SpringApplication.run`. Knowing the sequence helps pinpoint where startup breaks.
- **Customising startup** — need to set a banner, disable web, change the `ApplicationContext` type, or add application listeners? You configure `SpringApplication` before calling `run`.
- **Testing** — `@SpringBootTest` calls the same `run` path (minus the server port binding by default).

## 3. Core concept

`SpringApplication.run` proceeds through these phases (order matters):

1. **Prepare environment** — loads `application.properties`, environment variables, command-line args, profiles (`--spring.profiles.active=prod`).
2. **Print banner** — prints the Spring Boot ASCII art banner (configurable or suppressible).
3. **Create `ApplicationContext`** — for a servlet app, creates `AnnotationConfigServletWebServerApplicationContext`. For reactive, creates the WebFlux equivalent.
4. **Prepare context** — calls `BeanDefinitionLoader` to register beans from the primary source (`MyApp.class`) and any `@Import`ed configs.
5. **Refresh context** — the core `AbstractApplicationContext.refresh()` call: runs bean factory post-processors (including auto-configuration), instantiates all singleton beans, starts the embedded server.
6. **After refresh** — calls `ApplicationRunner` and `CommandLineRunner` beans (hooks to run code after startup).
7. **Return** — returns the `ConfigurableApplicationContext`. The main thread blocks inside Tomcat's accept loop.

Customising before `run`:

```java
var app = new SpringApplication(MyApp.class);
app.setBannerMode(Banner.Mode.OFF);           // silent startup
app.setWebApplicationType(WebApplicationType.NONE); // no web server
ConfigurableApplicationContext ctx = app.run(args);
```

## 4. Diagram

<svg viewBox="0 0 660 280" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="SpringApplication.run startup sequence from main method through environment, context creation, refresh, and runners">
  <!-- main() -->
  <rect x="260" y="14" width="140" height="32" rx="6" fill="#6db33f" stroke="#6db33f" stroke-width="1.5"/>
  <text x="330" y="35" fill="#1c2430" font-size="12" font-weight="bold" text-anchor="middle" font-family="sans-serif">main() — run()</text>

  <line x1="330" y1="46" x2="330" y2="62" stroke="#8b949e" stroke-width="1.5" marker-end="url(#runArr)"/>

  <!-- Step boxes -->
  <!-- 1 -->
  <rect x="80" y="62" width="500" height="28" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="330" y="81" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">1. Prepare environment (properties, env vars, profiles, CLI args)</text>
  <line x1="330" y1="90" x2="330" y2="102" stroke="#8b949e" stroke-width="1.5" marker-end="url(#runArr2)"/>

  <!-- 2 -->
  <rect x="80" y="102" width="500" height="28" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="330" y="121" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">2. Print banner</text>
  <line x1="330" y1="130" x2="330" y2="142" stroke="#8b949e" stroke-width="1.5" marker-end="url(#runArr3)"/>

  <!-- 3 -->
  <rect x="80" y="142" width="500" height="28" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="330" y="161" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">3. Create ApplicationContext (servlet / reactive / none)</text>
  <line x1="330" y1="170" x2="330" y2="182" stroke="#8b949e" stroke-width="1.5" marker-end="url(#runArr4)"/>

  <!-- 4 -->
  <rect x="80" y="182" width="500" height="28" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="330" y="201" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">4. Refresh context (auto-config, bean init, embedded server start)</text>
  <line x1="330" y1="210" x2="330" y2="222" stroke="#8b949e" stroke-width="1.5" marker-end="url(#runArr5)"/>

  <!-- 5 -->
  <rect x="80" y="222" width="500" height="28" rx="5" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="330" y="241" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">5. Run ApplicationRunner / CommandLineRunner beans</text>
  <line x1="330" y1="250" x2="330" y2="262" stroke="#6db33f" stroke-width="1.5" marker-end="url(#runArr6)"/>

  <!-- Done -->
  <rect x="220" y="262" width="220" height="16" rx="5" fill="#6db33f"/>
  <text x="330" y="274" fill="#1c2430" font-size="10" font-weight="bold" text-anchor="middle" font-family="sans-serif">App running — main thread blocked in Tomcat</text>

  <defs>
    <marker id="runArr"  markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker>
    <marker id="runArr2" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker>
    <marker id="runArr3" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker>
    <marker id="runArr4" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker>
    <marker id="runArr5" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker>
    <marker id="runArr6" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>
</svg>

Startup is linear: each phase builds on the previous. A failure in phase 4 (context refresh) typically means a missing bean or a misconfigured auto-configuration.

## 5. Runnable example

```java
// File: SpringRunDemo.java
// Demonstrates SpringApplication.run startup options in pure Java.
// Run: java SpringRunDemo.java

public class SpringRunDemo {

    // Simulates the SpringApplication builder pattern
    static class SpringApplication {
        private final Class<?> source;
        private boolean bannerEnabled = true;
        private String webType = "SERVLET";

        SpringApplication(Class<?> source) { this.source = source; }

        SpringApplication bannerMode(boolean enabled) {
            this.bannerEnabled = enabled; return this;
        }

        SpringApplication webApplicationType(String type) {
            this.webType = type; return this;
        }

        void run(String... args) {
            System.out.println("[SpringApplication] Starting " + source.getSimpleName());
            System.out.println("[1] Preparing environment...");
            System.out.println("    active profiles: "
                + (args.length > 0 ? args[0] : "default"));

            if (bannerEnabled) {
                System.out.println("[2] Banner: Spring Boot");
            }

            System.out.println("[3] Creating ApplicationContext (type=" + webType + ")");

            System.out.println("[4] Refreshing context...");
            System.out.println("    Running auto-configuration");
            if ("SERVLET".equals(webType)) {
                System.out.println("    Starting embedded Tomcat on port 8080");
            } else if ("NONE".equals(webType)) {
                System.out.println("    No web server (webType=NONE)");
            }

            System.out.println("[5] Running ApplicationRunner / CommandLineRunner beans");
            System.out.println("[√] Started in 1.234 s");
        }
    }

    // A minimal main class annotated with @SpringBootApplication (simulated)
    static class MyApp { }

    public static void main(String[] args) {
        System.out.println("=== Default (web app with banner) ===");
        new SpringApplication(MyApp.class).run("prod");

        System.out.println();
        System.out.println("=== Customised (no banner, no web server) ===");
        new SpringApplication(MyApp.class)
            .bannerMode(false)
            .webApplicationType("NONE")
            .run("dev");
    }
}
```

**How to run:** `java SpringRunDemo.java` (JDK 17+, no dependencies needed).

Expected output:
```
=== Default (web app with banner) ===
[SpringApplication] Starting MyApp
[1] Preparing environment...
    active profiles: prod
[2] Banner: Spring Boot
[3] Creating ApplicationContext (type=SERVLET)
[4] Refreshing context...
    Running auto-configuration
    Starting embedded Tomcat on port 8080
[5] Running ApplicationRunner / CommandLineRunner beans
[√] Started in 1.234 s

=== Customised (no banner, no web server) ===
[SpringApplication] Starting MyApp
[1] Preparing environment...
    active profiles: dev
[3] Creating ApplicationContext (type=NONE)
[4] Refreshing context...
    Running auto-configuration
    No web server (webType=NONE)
[5] Running ApplicationRunner / CommandLineRunner beans
[√] Started in 1.234 s
```

## 6. Walkthrough

- **`SpringApplication(source)`** — stores the primary source class. In real Spring Boot, this is the class annotated with `@SpringBootApplication`; it's the root of the component scan and the `@Configuration` source.
- **`bannerMode(false)`** — suppresses the ASCII art banner. Useful in production where logs go to structured output (JSON) and ASCII art is noise. In real Spring Boot: `app.setBannerMode(Banner.Mode.OFF)`.
- **`webApplicationType("NONE")`** — tells Spring Boot not to start any web server. Useful for batch jobs, command-line tools, or test slices. In real Spring Boot: `app.setWebApplicationType(WebApplicationType.NONE)`.
- **Profiles from args** — real `SpringApplication.run(args)` scans `args` for `--spring.profiles.active=prod`. Setting the active profile determines which `application-prod.properties` file loads.
- **`[4] Refreshing context`** — this is where 90% of startup time is spent. All singleton beans are instantiated, `@PostConstruct` methods run, embedded Tomcat binds to the port. A `BeanCreationException` here is the most common startup failure.
- **`ApplicationRunner` / `CommandLineRunner`** — `@Bean` methods returning these interfaces run after the context is refreshed and the server is ready. Use them for database seeding, health checks, or startup validation.

## 7. Gotchas & takeaways

> **`SpringApplication.run` returns a `ConfigurableApplicationContext`.** Most tutorials ignore the return value, but it's useful: `ctx.getBean(MyService.class)` retrieves a bean programmatically, and `ctx.close()` shuts the app down cleanly. In tests, `@SpringBootTest` manages this for you.

> **The startup log lines are timestamped.** If startup is slow, the log shows exactly which bean instantiation or `@PostConstruct` is taking time. Look for lines with large gaps between the timestamp and the next line — that's where to investigate.

- `SpringApplication.run(App.class, args)` is the single entry point; it handles environment, context, auto-config, and server start.
- Customise via `new SpringApplication(App.class)` builder before calling `run`.
- Pass `--server.port=9090` or `--spring.profiles.active=prod` as CLI args; they arrive in the `args` parameter and override `application.properties`.
- `WebApplicationType.NONE` starts no server — ideal for batch jobs and CLI tools.
- `CommandLineRunner` or `ApplicationRunner` beans run after startup is complete — the right place for initialisation logic.
