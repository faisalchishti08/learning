---
card: spring-boot
gi: 50
slug: customizing-springapplication-builders-setters
title: Customizing SpringApplication (builders, setters)
---

## 1. What it is

**Customising `SpringApplication`** means configuring the application bootstrapper before the `ApplicationContext` is created. Instead of calling the one-liner `SpringApplication.run(MyApp.class, args)`, you instantiate `SpringApplication`, call setter methods to configure it, then call `run()`.

```java
public static void main(String[] args) {
    SpringApplication app = new SpringApplication(MyApp.class);
    app.setBannerMode(Banner.Mode.OFF);
    app.setWebApplicationType(WebApplicationType.NONE);
    app.setLazyInitialization(true);
    app.setDefaultProperties(Map.of("server.port", "9090"));
    app.run(args);
}
```

This gives access to configuration that cannot be done through `application.properties` because it must be set before the context — and therefore before properties are loaded.

## 2. Why & when

`application.properties` is loaded as part of context preparation (stage 6 of the launch sequence). Settings that affect context creation itself must be set earlier — on the `SpringApplication` instance directly.

Common customisations:
- **`setWebApplicationType`** — force NONE for a CLI tool that has web JARs on the classpath but should not start a server.
- **`setLazyInitialization`** — enable lazy init for faster test or development startup.
- **`setDefaultProperties`** — provide fallback property values that can be overridden by `application.properties` or environment variables.
- **`addListeners`** / **`addInitializers`** — register `ApplicationListener`s and `ApplicationContextInitializer`s before the context exists.
- **`setBannerMode`** — suppress the banner in tests or CI.
- **`setAdditionalProfiles`** — activate profiles programmatically.

## 3. Core concept

Think of `SpringApplication` as a **configuration form** you fill out before handing it to the launch crew. The static `SpringApplication.run()` shortcut hands over a blank form. Using an instance lets you pre-fill fields: "no web server", "lazy beans", "use port 9090 as default" — before the launch crew (the `ApplicationContext`) does any work.

Key setter categories:

| Setter | Purpose |
|---|---|
| `setBannerMode(Mode)` | `CONSOLE`, `LOG`, `OFF` |
| `setWebApplicationType(type)` | `SERVLET`, `REACTIVE`, `NONE` |
| `setLazyInitialization(bool)` | defer bean creation |
| `setDefaultProperties(Map)` | low-priority property defaults |
| `setAdditionalProfiles(String...)` | activate Spring profiles |
| `addListeners(ApplicationListener...)` | register startup event listeners |
| `addInitializers(ApplicationContextInitializer...)` | add context initialisers |
| `setHeadless(bool)` | AWT headless mode (affects image processing) |
| `setLogStartupInfo(bool)` | suppress "Started XxxApp in N seconds" log line |

`setDefaultProperties()` accepts a `Map<String, Object>` and populates a property source with the **lowest** priority — any value in `application.properties` or environment overrides it.

## 4. Diagram

<svg viewBox="0 0 660 240" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="SpringApplication customisation setters applied before context creation">
  <!-- SpringApplication instance box -->
  <rect x="20" y="20" width="280" height="200" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="160" y="46" fill="#6db33f" font-size="12" font-family="monospace" font-weight="bold" text-anchor="middle">new SpringApplication(MyApp.class)</text>

  <rect x="36" y="58" width="248" height="26" rx="5" fill="#2d3748" stroke="#79c0ff" stroke-width="1"/>
  <text x="160" y="76" fill="#79c0ff" font-size="10" font-family="monospace" text-anchor="middle">.setBannerMode(OFF)</text>

  <rect x="36" y="92" width="248" height="26" rx="5" fill="#2d3748" stroke="#79c0ff" stroke-width="1"/>
  <text x="160" y="110" fill="#79c0ff" font-size="10" font-family="monospace" text-anchor="middle">.setWebApplicationType(NONE)</text>

  <rect x="36" y="126" width="248" height="26" rx="5" fill="#2d3748" stroke="#79c0ff" stroke-width="1"/>
  <text x="160" y="144" fill="#79c0ff" font-size="10" font-family="monospace" text-anchor="middle">.setLazyInitialization(true)</text>

  <rect x="36" y="160" width="248" height="26" rx="5" fill="#2d3748" stroke="#79c0ff" stroke-width="1"/>
  <text x="160" y="178" fill="#79c0ff" font-size="10" font-family="monospace" text-anchor="middle">.setDefaultProperties(Map.of(…))</text>

  <text x="160" y="210" fill="#6db33f" font-size="11" font-family="monospace" text-anchor="middle">.run(args)  →</text>

  <!-- Arrow -->
  <line x1="302" y1="120" x2="358" y2="120" stroke="#6db33f" stroke-width="2" marker-end="url(#cs)"/>

  <!-- Context box -->
  <rect x="360" y="60" width="270" height="120" rx="8" fill="#16202e" stroke="#6db33f" stroke-width="2"/>
  <text x="495" y="84" fill="#6db33f" font-size="12" font-family="sans-serif" font-weight="bold" text-anchor="middle">ApplicationContext</text>
  <text x="495" y="108" fill="#8b949e" font-size="10" font-family="monospace" text-anchor="middle">no banner, no web server</text>
  <text x="495" y="126" fill="#8b949e" font-size="10" font-family="monospace" text-anchor="middle">lazy beans, port default = 9090</text>
  <text x="495" y="146" fill="#8b949e" font-size="10" font-family="monospace" text-anchor="middle">all set before context refresh</text>

  <defs>
    <marker id="cs" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/>
    </marker>
  </defs>
</svg>

Setters configure the `SpringApplication` before `run()` is called; everything they control takes effect before — or during — context creation.

## 5. Runnable example

```java
// CustomizeSpringApplicationDemo.java
// How to run: java CustomizeSpringApplicationDemo.java  (JDK 17+)
// Simulates SpringApplication customisation via setters, showing what each
// setter changes before the context is created.

import java.util.*;

public class CustomizeSpringApplicationDemo {

    enum BannerMode  { CONSOLE, LOG, OFF }
    enum WebAppType  { SERVLET, REACTIVE, NONE }

    // ── SpringApplication simulation ──────────────────────────────
    static class SpringApplication {
        private BannerMode  bannerMode           = BannerMode.CONSOLE;
        private WebAppType  webApplicationType   = WebAppType.SERVLET;
        private boolean     lazyInitialization   = false;
        private boolean     logStartupInfo       = true;
        private Map<String, Object> defaultProps = new LinkedHashMap<>();
        private List<String>        profiles     = new ArrayList<>();

        void setBannerMode(BannerMode m)                 { this.bannerMode = m; }
        void setWebApplicationType(WebAppType t)         { this.webApplicationType = t; }
        void setLazyInitialization(boolean lazy)         { this.lazyInitialization = lazy; }
        void setLogStartupInfo(boolean log)              { this.logStartupInfo = log; }
        void setDefaultProperties(Map<String, Object> p){ this.defaultProps.putAll(p); }
        void setAdditionalProfiles(String... p)          { profiles.addAll(Arrays.asList(p)); }

        void run(String[] args) {
            System.out.println("=== SpringApplication.run() ===");
            System.out.println("  banner-mode      : " + bannerMode);
            System.out.println("  web-app-type     : " + webApplicationType);
            System.out.println("  lazy-init        : " + lazyInitialization);
            System.out.println("  log-startup-info : " + logStartupInfo);
            System.out.println("  default-props    : " + defaultProps);
            System.out.println("  profiles         : " + profiles);
            System.out.println();

            if (bannerMode == BannerMode.CONSOLE)
                System.out.println("  :: Spring Boot ::");

            if (webApplicationType == WebAppType.NONE)
                System.out.println("  [web server NOT started — WebApplicationType.NONE]");
            else
                System.out.println("  [starting embedded " + webApplicationType + " server]");

            if (logStartupInfo)
                System.out.println("  Started MyApp in 0.123 seconds");
        }
    }

    public static void main(String[] args) {
        System.out.println("--- Scenario A: CLI tool (no web server, minimal output) ---\n");
        SpringApplication cliApp = new SpringApplication();
        cliApp.setBannerMode(BannerMode.OFF);
        cliApp.setWebApplicationType(WebAppType.NONE);
        cliApp.setLogStartupInfo(false);
        cliApp.setDefaultProperties(Map.of("spring.application.name", "cli-tool"));
        cliApp.run(args);

        System.out.println("--- Scenario B: Web app with lazy init and extra profile ---\n");
        SpringApplication webApp = new SpringApplication();
        webApp.setLazyInitialization(true);
        webApp.setAdditionalProfiles("metrics", "audit");
        webApp.setDefaultProperties(Map.of("server.port", "9090"));
        webApp.run(args);
    }
}
```

**How to run:** `java CustomizeSpringApplicationDemo.java`

Expected output:
```
--- Scenario A: CLI tool (no web server, minimal output) ---

=== SpringApplication.run() ===
  banner-mode      : OFF
  web-app-type     : NONE
  lazy-init        : false
  log-startup-info : false
  default-props    : {spring.application.name=cli-tool}
  profiles         : []

  [web server NOT started — WebApplicationType.NONE]

--- Scenario B: Web app with lazy init and extra profile ---

=== SpringApplication.run() ===
  banner-mode      : CONSOLE
  web-app-type     : SERVLET
  lazy-init        : true
  log-startup-info : true
  default-props    : {server.port=9090}
  profiles         : [metrics, audit]

  :: Spring Boot ::
  [starting embedded SERVLET server]
  Started MyApp in 0.123 seconds
```

## 6. Walkthrough

- Scenario A simulates a batch CLI tool. `setWebApplicationType(NONE)` prevents Tomcat from starting even though `spring-webmvc` might be on the classpath (a common situation when the web module is an indirect dependency).
- `setLogStartupInfo(false)` suppresses the "Started XxxApp in N seconds" log line — useful when the app is embedded in a shell script and extra output is unwanted.
- `setDefaultProperties` provides `spring.application.name=cli-tool` as the lowest-priority property — any value in `application.properties` overrides it.
- Scenario B shows `setLazyInitialization(true)` and `setAdditionalProfiles("metrics", "audit")`. Both are equivalent to `spring.main.lazy-initialization=true` and `spring.profiles.active=metrics,audit` in `application.properties`, but are set programmatically before any properties file is loaded.

## 7. Gotchas & takeaways

> `setDefaultProperties()` sets a **low-priority** property source — it is overridden by `application.properties`, environment variables, and system properties. Do not use it for values you want to enforce; use it only for sensible fallback defaults.

> `setWebApplicationType(WebApplicationType.NONE)` is not the same as excluding the web auto-configuration. The web beans may still be registered (if Spring MVC is on the classpath and not excluded). `NONE` simply prevents the embedded server from starting — no port is opened. If you want no web beans at all, also exclude `DispatcherServletAutoConfiguration`.

- Prefer `application.properties` / `@ConfigurationProperties` for values that can change per environment. Use setters only for settings that must be locked in before context creation.
- Setters are idiomatic; the fluent `SpringApplicationBuilder` (next tutorial) is more concise for multi-setter configurations.
- `addListeners(new MyListener())` pre-registers a listener that catches events before `@EventListener` beans (which require the context to exist).
- `setHeadless(false)` is needed when running on a headless server that uses Swing/AWT components (uncommon but real in legacy enterprise apps).
