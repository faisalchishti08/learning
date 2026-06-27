---
card: spring-boot
gi: 1
slug: what-spring-boot-is-its-goals
title: What Spring Boot is & its goals
---

## 1. What it is

**Spring Boot** is an opinionated layer on top of the Spring Framework that lets you create a production-ready Spring application with almost no boilerplate setup. You write your business logic; Spring Boot handles the infrastructure.

Its three headline goals are:

1. **Eliminate configuration drudgery.** You should not need to write 100 lines of XML or Java config just to start a web server.
2. **Remove dependency management headaches.** Spring Boot ships curated sets of compatible library versions so you don't fight version conflicts.
3. **Make the application self-contained.** The output is a single executable JAR (sometimes called a "fat JAR" or "uber JAR") with an embedded web server inside — you run it with `java -jar app.jar`, no Tomcat installation required.

Think of Spring Boot as a car with everything pre-configured — engine, transmission, fuel injection all tuned — versus the Spring Framework, which gives you all the individual parts and lets you assemble them yourself.

## 2. Why & when

Before Spring Boot (pre-2014), setting up a Spring web application meant:

- A separate Tomcat/JBoss server installed and configured on every machine.
- An XML file (`applicationContext.xml`, `web.xml`) with dozens of lines specifying which beans to create and how to wire them.
- Manually ensuring that every library version was compatible with every other.

Spring Boot was created to fix all three. Use it when:

- You're starting a **new Spring-based service** (REST API, web app, batch job, messaging consumer).
- You want **fast feedback** — a new project goes from `spring init` to `hello world` in under two minutes.
- You want **consistent, reproducible builds** across developer machines and CI servers.

You might stay closer to raw Spring Framework only if you have an existing, highly customised application or if you need to avoid the opinionated defaults entirely (rare).

## 3. Core concept

Spring Boot's machinery rests on three pillars that work together:

**Starter dependencies** — `spring-boot-starter-web`, `spring-boot-starter-data-jpa`, etc. Each starter is a bundle of compatible libraries. Add one dependency → get everything needed for that capability.

**Auto-configuration** — `@SpringBootApplication` triggers a scan of the classpath. If Spring Boot sees `spring-boot-starter-web` on the classpath, it automatically registers an embedded Tomcat, a `DispatcherServlet`, Jackson JSON converters, and more — without you declaring any of it.

**Executable JAR** — `mvn package` (or `./gradlew bootJar`) produces a single file that contains your application class files, all dependency JARs, and a launcher that knows how to start the embedded server. `java -jar app.jar` and you're live.

The assembly line: write code → add starters → auto-config wires everything → package into executable JAR → ship.

## 4. Diagram

<svg viewBox="0 0 680 260" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Spring Boot architecture showing starters, auto-config, and executable JAR layers">
  <!-- Background panels -->
  <rect x="20" y="20" width="200" height="220" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="120" y="46" fill="#6db33f" font-size="13" font-weight="bold" text-anchor="middle" font-family="sans-serif">Starter Dependencies</text>
  <rect x="36" y="56" width="168" height="30" rx="5" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="120" y="76" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">spring-boot-starter-web</text>
  <rect x="36" y="94" width="168" height="30" rx="5" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="120" y="114" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">spring-boot-starter-data-jpa</text>
  <rect x="36" y="132" width="168" height="30" rx="5" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="120" y="152" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">spring-boot-starter-test</text>
  <text x="120" y="200" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">curated version-compatible</text>
  <text x="120" y="216" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">dependency bundles</text>

  <!-- Arrow 1 -->
  <line x1="224" y1="130" x2="264" y2="130" stroke="#6db33f" stroke-width="2" marker-end="url(#arr1)"/>

  <!-- Auto-config box -->
  <rect x="268" y="60" width="180" height="140" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="358" y="86" fill="#79c0ff" font-size="13" font-weight="bold" text-anchor="middle" font-family="sans-serif">Auto-Configuration</text>
  <text x="358" y="110" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">@SpringBootApplication</text>
  <text x="358" y="130" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">scans classpath</text>
  <text x="358" y="148" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">registers beans</text>
  <text x="358" y="166" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">wires everything</text>
  <text x="358" y="186" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">automatically</text>

  <!-- Arrow 2 -->
  <line x1="452" y1="130" x2="492" y2="130" stroke="#6db33f" stroke-width="2" marker-end="url(#arr2)"/>

  <!-- Executable JAR box -->
  <rect x="496" y="60" width="164" height="140" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="578" y="86" fill="#6db33f" font-size="13" font-weight="bold" text-anchor="middle" font-family="sans-serif">Executable JAR</text>
  <text x="578" y="110" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">app.jar</text>
  <text x="578" y="132" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">your code +</text>
  <text x="578" y="148" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">all dependencies +</text>
  <text x="578" y="164" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">embedded server</text>
  <text x="578" y="186" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">java -jar app.jar</text>

  <defs>
    <marker id="arr1" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="arr2" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>
</svg>

Starters supply compatible libraries → Auto-configuration wires them at startup → the result is packaged as a single self-contained executable JAR.

## 5. Runnable example

The minimal Spring Boot web application — the "hello world" of the framework.

```java
// File: HelloApplication.java
// Spring Boot snippet — requires a project from start.spring.io
// with dependency: Spring Web

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

@SpringBootApplication          // (1) turns on auto-config, component scan, config support
@RestController                 // (2) this class handles HTTP requests directly
public class HelloApplication {

    public static void main(String[] args) {
        SpringApplication.run(HelloApplication.class, args);  // (3) launch embedded Tomcat
    }

    @GetMapping("/")            // (4) respond to GET /
    public String hello() {
        return "Hello from Spring Boot!";
    }
}
```

**How to run:**
1. Go to [start.spring.io](https://start.spring.io), choose Java 17+, add dependency **Spring Web**, download and unzip.
2. Replace the generated main class with the code above.
3. `./mvnw spring-boot:run` (Mac/Linux) or `mvnw.cmd spring-boot:run` (Windows).
4. Open `http://localhost:8080` — you'll see `Hello from Spring Boot!`.

No Tomcat installation, no `web.xml`, no XML bean config.

## 6. Walkthrough

- **`@SpringBootApplication`** — a convenience annotation that combines three others: `@Configuration` (this class declares beans), `@EnableAutoConfiguration` (let Spring Boot guess and configure things), and `@ComponentScan` (find other `@Component`-annotated classes in the same package). This single annotation kicks off the entire boot sequence.
- **`@RestController`** — marks the class as a web controller whose methods return data directly as the HTTP response body (not a view name). It merges `@Controller` and `@ResponseBody`.
- **`SpringApplication.run(...)`** — this is where Spring Boot actually starts: it creates the `ApplicationContext`, triggers auto-configuration (which detects `spring-boot-starter-web` on the classpath and starts embedded Tomcat on port 8080), then publishes lifecycle events so all beans are initialised before the first request arrives.
- **`@GetMapping("/")`** — registers this method as the handler for `GET /`. Spring's `DispatcherServlet` (auto-configured) routes matching requests to it.
- The returned `String` is automatically written as the HTTP response body with `Content-Type: text/plain`.

The whole cycle — from classpath scan to first HTTP response — completes in a few seconds, with zero XML.

## 7. Gotchas & takeaways

> **Spring Boot is not a separate product from Spring.** It's a starter kit and auto-configuration layer on top of Spring Framework. Every bean, every annotation, every feature is still pure Spring underneath — Boot just wires it up for you. Understanding this prevents the confusion of "does Spring Boot replace Spring?"

> **"Opinionated" doesn't mean "inflexible."** Every default can be overridden. Spring Boot reads `application.properties` / `application.yml`, and any bean you explicitly declare takes precedence over the auto-configured one. You can always eject from a default.

- Spring Boot = Spring Framework + auto-config + starter POMs + embedded server support.
- The single main entry point (`SpringApplication.run`) starts the embedded server — no servlet container needed separately.
- Fat JARs let you `scp app.jar` to a server and run it with `java -jar` — simpler deployment than WAR files.
- Auto-configuration fires only for libraries that are on the classpath; unused features don't start.
- The Spring Initializr at start.spring.io is the fastest way to scaffold a correct project structure.
