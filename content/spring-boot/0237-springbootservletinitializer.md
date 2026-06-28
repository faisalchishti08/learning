---
card: spring-boot
gi: 237
slug: springbootservletinitializer
title: SpringBootServletInitializer
---

## 1. What it is

`SpringBootServletInitializer` is an abstract class in Spring Boot that implements the Servlet 3.0 `WebApplicationInitializer` interface. When a servlet container (Tomcat, Jetty, WildFly) deploys a Spring Boot WAR, it scans for `WebApplicationInitializer` implementations and calls `onStartup()`. `SpringBootServletInitializer` overrides `onStartup()` to bootstrap a full `SpringApplication` inside the managed container — no `web.xml` required.

## 2. Why & when

In standalone mode (`java -jar`), your `main()` method starts Spring. In managed WAR deployment, there is no `main()` invocation — the container bootstraps the app. `SpringBootServletInitializer` is the bridge: it plays the role `main()` plays for standalone, but activated by the container's `ServletContainerInitializer` mechanism. Without it, a Spring Boot WAR is just a pile of classes and the container cannot start the application.

## 3. Core concept

`SpringBootServletInitializer` requires one method override:

```java
@Override
protected SpringApplicationBuilder configure(SpringApplicationBuilder builder) {
    return builder.sources(YourApplication.class);
}
```

`builder.sources(...)` registers the primary configuration class — the same one passed to `SpringApplication.run(...)` in `main()`. Spring Boot then proceeds exactly as in standalone mode: loads configuration, creates beans, fires lifecycle events.

The class also:
- Reads `spring.profiles.active` from the servlet context init parameters.
- Sets up the `WebApplicationContext` so MVC components work inside the container's `DispatcherServlet`.

## 4. Diagram

<svg viewBox="0 0 640 270" xmlns="http://www.w3.org/2000/svg" font-family="monospace" font-size="13">
  <rect width="640" height="270" fill="#1c2430" rx="10"/>
  <!-- Container -->
  <rect x="20" y="30" width="200" height="210" rx="8" fill="#2d3748" stroke="#79c0ff" stroke-width="2"/>
  <text x="120" y="58" text-anchor="middle" fill="#79c0ff">Servlet Container</text>
  <text x="120" y="78" text-anchor="middle" fill="#8b949e" font-size="11">(Tomcat / WildFly)</text>
  <rect x="35" y="90" width="170" height="40" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="120" y="115" text-anchor="middle" fill="#e6edf3" font-size="12">Deploys WAR</text>
  <rect x="35" y="140" width="170" height="40" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="120" y="158" text-anchor="middle" fill="#6db33f" font-size="12">Finds WebApplication</text>
  <text x="120" y="174" text-anchor="middle" fill="#6db33f" font-size="12">Initializer impls</text>
  <!-- SpringBootServletInitializer -->
  <rect x="270" y="60" width="340" height="170" rx="8" fill="#2d3748" stroke="#6db33f" stroke-width="2"/>
  <text x="440" y="90" text-anchor="middle" fill="#6db33f">SpringBootServletInitializer</text>
  <rect x="285" y="104" width="310" height="40" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="440" y="129" text-anchor="middle" fill="#8b949e" font-size="12">configure(builder) → builder.sources(App.class)</text>
  <rect x="285" y="152" width="310" height="40" rx="4" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="440" y="177" text-anchor="middle" fill="#79c0ff" font-size="12">SpringApplication bootstraps context</text>
  <text x="440" y="193" text-anchor="middle" fill="#8b949e" font-size="11">(same as main() in standalone mode)</text>
  <!-- Arrow -->
  <line x1="220" y1="160" x2="268" y2="145" stroke="#6db33f" stroke-width="2" marker-end="url(#ab)"/>
  <defs>
    <marker id="ab" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L0,6 L8,3 z" fill="#6db33f"/>
    </marker>
  </defs>
</svg>

_The container calls `onStartup()` → `SpringBootServletInitializer` bootstraps Spring exactly like `main()` does._

## 5. Runnable example

```java
// File: ServletInitializerDemo.java
// How to run: java ServletInitializerDemo.java
// Illustrates the pattern — real deployment requires a Spring Boot WAR project.

public class ServletInitializerDemo {

    // ---- Real project code (in src/main/java) ----
    //
    // @SpringBootApplication
    // public class DemoApplication extends SpringBootServletInitializer {
    //
    //     // Called by the servlet container on WAR deployment
    //     @Override
    //     protected SpringApplicationBuilder configure(SpringApplicationBuilder builder) {
    //         return builder.sources(DemoApplication.class);
    //     }
    //
    //     // Called when running standalone: java -jar myapp.war
    //     public static void main(String[] args) {
    //         SpringApplication.run(DemoApplication.class, args);
    //     }
    // }
    //
    // ---- Variant: separate initializer class ----
    //
    // public class ServletInitializer extends SpringBootServletInitializer {
    //     @Override
    //     protected SpringApplicationBuilder configure(SpringApplicationBuilder builder) {
    //         return builder.sources(DemoApplication.class);
    //     }
    // }

    public static void main(String[] args) {
        System.out.println("SpringBootServletInitializer — how it works:");
        System.out.println();
        System.out.println("1. Container deploys the WAR.");
        System.out.println("2. Servlet 3.0 SPI: container scans for WebApplicationInitializer impls.");
        System.out.println("3. SpringBootServletInitializer.onStartup(servletContext) is called.");
        System.out.println("4. Internally: SpringApplicationBuilder is created,");
        System.out.println("   configure() is called to register your @SpringBootApplication class.");
        System.out.println("5. SpringApplication.run() executes — same path as standalone mode.");
        System.out.println("6. DispatcherServlet is registered in the provided ServletContext.");
        System.out.println();
        System.out.println("Standalone path (java -jar myapp.war):");
        System.out.println("  WarLauncher -> main() -> SpringApplication.run()");
        System.out.println("  (SpringBootServletInitializer.configure() NOT called)");
    }
}
```

**How to run:** `java ServletInitializerDemo.java` — explains both execution paths.

## 6. Walkthrough

1. The container's `ServletContainerInitializer` (provided by Spring's `spring-web` JAR in `META-INF/services/`) calls `onStartup()` with the `ServletContext`.
2. `onStartup()` calls `configure()` — your override registers the primary Spring configuration class via `builder.sources(DemoApplication.class)`.
3. The builder creates a `SpringApplication` and calls `run()`, which processes `@SpringBootApplication`, fires auto-configuration, and creates the `ApplicationContext`.
4. `DispatcherServlet` is registered in the `ServletContext` — from this point, the container routes HTTP requests to Spring MVC normally.
5. The `main()` method is untouched — standalone launches still work via `WarLauncher`.

## 7. Gotchas & takeaways

> `SpringBootServletInitializer` must be on the class discovered by the container's classpath scan. Place it in a package that is scanned, or use the separate `ServletInitializer` convention generated by Spring Initializr.

> `configure()` must return `builder.sources(...)` — returning `builder` without calling `.sources()` results in an empty application context and a startup failure.

> Spring Boot 3 uses Jakarta EE (`jakarta.servlet`), not Java EE (`javax.servlet`). Target container must be Jakarta EE 9+ (Tomcat 10+, WildFly 26+).

- The class is in `spring-boot-starter-web` — no additional dependency needed.
- You can call `builder.sources(A.class, B.class)` to register multiple configuration classes.
- `builder.properties("spring.profiles.active=prod")` from within `configure()` sets profiles for the managed deployment.
- Prefer a separate `ServletInitializer` class (Initializr default) over extending your `@SpringBootApplication` class — keeps responsibilities separate.
