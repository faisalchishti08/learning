---
card: spring-boot
gi: 15
slug: creating-a-first-hello-world-app
title: Creating a first 'Hello World' app
---

## 1. What it is

A **Hello World Spring Boot application** is the minimal working web service: a `@SpringBootApplication` main class and one `@RestController` with a single endpoint. It is the "muscle memory" of Spring Boot — a pattern you'll type hundreds of times, and the starting point for every feature you'll ever add.

The complete application is five meaningful lines of Java:

```java
@SpringBootApplication
@RestController
public class App {
    public static void main(String[] args) { SpringApplication.run(App.class, args); }
    @GetMapping("/") public String hello() { return "Hello, World!"; }
}
```

When this runs, embedded Tomcat starts on port 8080, and `GET /` returns `Hello, World!` as plain text.

## 2. Why & when

A Hello World app demonstrates several Spring Boot fundamentals simultaneously: auto-configuration fires (embedded Tomcat starts), component scanning finds the controller, the dispatcher servlet routes the request, and the Jackson converter serialises the response — all from two annotations and five lines.

Build it first when:
- Learning Spring Boot (always start here before adding complexity).
- Verifying your JDK and build tool setup after installation.
- Proving connectivity before adding a database or message broker.
- Creating a new microservice skeleton to iterate on.

## 3. Core concept

The layers involved in serving `GET /`:

1. **`SpringApplication.run`** — bootstraps the `ApplicationContext`, triggers auto-configuration, starts the embedded Tomcat, and parks the main thread in the server's accept loop.
2. **Component scan** — `@SpringBootApplication` includes `@ComponentScan`; it finds `App.class` (annotated `@RestController`) and registers it as a bean.
3. **`DispatcherServlet`** — auto-configured (by `WebMvcAutoConfiguration`) as the front controller. All requests arrive here first.
4. **Handler mapping** — `RequestMappingHandlerMapping` scans all beans for `@GetMapping`/`@RequestMapping` and builds a routing table. `GET /` → `App#hello()`.
5. **Method invocation** — `hello()` is called, returns `"Hello, World!"`.
6. **Message conversion** — `StringHttpMessageConverter` writes the `String` as a `text/plain` response body.

The full project structure from the Initializr:

```
src/
  main/
    java/com/example/demo/
      DemoApplication.java     ← the 5-line app
    resources/
      application.properties   ← (empty, ready for config)
  test/
    java/com/example/demo/
      DemoApplicationTests.java ← context-loads smoke test
pom.xml (or build.gradle.kts)
```

## 4. Diagram

<svg viewBox="0 0 660 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Request flow for Hello World: browser GET slash flows through DispatcherServlet to hello() method and back">
  <!-- Browser -->
  <rect x="20" y="80" width="120" height="60" rx="7" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="80" y="105" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">Browser</text>
  <text x="80" y="123" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">GET /</text>

  <!-- Arrow -->
  <line x1="140" y1="110" x2="180" y2="110" stroke="#3fb950" stroke-width="2" marker-end="url(#hwArr)"/>

  <!-- Embedded Tomcat -->
  <rect x="180" y="60" width="140" height="100" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="250" y="82" fill="#6db33f" font-size="11" font-weight="bold" text-anchor="middle" font-family="sans-serif">Embedded Tomcat</text>
  <rect x="196" y="90" width="108" height="24" rx="4" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="250" y="107" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">DispatcherServlet</text>
  <rect x="196" y="122" width="108" height="24" rx="4" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="250" y="139" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Handler Mapping</text>

  <!-- Arrow -->
  <line x1="320" y1="110" x2="360" y2="110" stroke="#3fb950" stroke-width="2" marker-end="url(#hwArr2)"/>
  <text x="340" y="103" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">GET /</text>

  <!-- Controller -->
  <rect x="360" y="70" width="180" height="80" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="450" y="94" fill="#79c0ff" font-size="12" font-weight="bold" text-anchor="middle" font-family="sans-serif">@RestController</text>
  <text x="450" y="114" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">App#hello()</text>
  <text x="450" y="134" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">returns "Hello, World!"</text>

  <!-- Response arrow -->
  <line x1="360" y1="132" x2="140" y2="132" stroke="#79c0ff" stroke-width="2" marker-end="url(#hwArr3)"/>
  <text x="250" y="150" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">200 OK: "Hello, World!"</text>

  <defs>
    <marker id="hwArr"  markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#3fb950"/></marker>
    <marker id="hwArr2" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#3fb950"/></marker>
    <marker id="hwArr3" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>
</svg>

Every Spring Boot web request follows this exact path: browser → Tomcat → DispatcherServlet → @RequestMapping handler → response.

## 5. Runnable example

```java
// File: HelloWorldApp.java
// Minimal Spring Boot Hello World — requires a project from start.spring.io
// with dependency: Spring Web (spring-boot-starter-web)
//
// How to run:
//   1. Go to start.spring.io, add "Spring Web", download and unzip.
//   2. Replace the generated Application class with this file.
//   3. ./mvnw spring-boot:run
//   4. Open http://localhost:8080/ → "Hello, World!"
//   5. Open http://localhost:8080/greet/Alice → "Hello, Alice!"

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RestController;

@SpringBootApplication   // auto-config + component scan + configuration
@RestController          // registers this class as a request handler
public class HelloWorldApp {

    public static void main(String[] args) {
        SpringApplication.run(HelloWorldApp.class, args);
    }

    @GetMapping("/")
    public String hello() {
        return "Hello, World!";
    }

    @GetMapping("/greet/{name}")
    public String greet(@PathVariable String name) {
        return "Hello, " + name + "!";
    }
}
```

**How to run:**
1. Generate a project at start.spring.io with dependency **Spring Web**.
2. Replace the generated main class with the code above.
3. `./mvnw spring-boot:run`
4. `curl http://localhost:8080/` → `Hello, World!`
5. `curl http://localhost:8080/greet/Alice` → `Hello, Alice!`

## 6. Walkthrough

- **`@SpringBootApplication`** — the entry point annotation. Expands to `@Configuration + @EnableAutoConfiguration + @ComponentScan`. The `@EnableAutoConfiguration` part triggers the classpath scan that finds `spring-boot-starter-web`, after which Tomcat is started, `DispatcherServlet` is registered, and Jackson is configured.
- **`@RestController`** — marks this class as a Spring MVC controller whose methods return data directly in the response body. Without it, Spring would look for a view template (Thymeleaf, FreeMarker) instead of writing the `String` directly.
- **`SpringApplication.run(HelloWorldApp.class, args)`** — this one line starts the entire Spring Boot machinery. It creates the `ApplicationContext`, applies auto-configuration, binds to port 8080, and blocks the main thread in Tomcat's accept loop until the process is killed.
- **`@GetMapping("/")`** — shorthand for `@RequestMapping(method = RequestMethod.GET, value = "/")`. Registers this method to handle `GET` requests to the root path.
- **`@GetMapping("/greet/{name}")` + `@PathVariable`** — `{name}` is a URI template variable. Spring extracts the value from the path and injects it as the `name` parameter. `GET /greet/Alice` → `name = "Alice"`.
- The returned `String` is converted to the HTTP response body by `StringHttpMessageConverter` (auto-configured) with `Content-Type: text/plain`.

## 7. Gotchas & takeaways

> **Port 8080 might already be in use.** If you see `Address already in use: 8080` at startup, either stop the other process or change the port in `application.properties`: `server.port=9090`. Using `server.port=0` picks a random available port (useful in tests).

> **`@SpringBootApplication` and `@RestController` on the same class is valid but atypical.** In production code, the main class usually has only `@SpringBootApplication`, and controllers live in separate files under the same package. Combining them here is intentional minimal-code pedagogy, not recommended practice.

- Five lines is all you need to start a working Spring Boot web application.
- Always run `./mvnw spring-boot:run` (not `java -jar`) during development — it picks up classpath changes faster.
- `GET /` returning a `String` sets `Content-Type: text/plain`. Return a POJO and it becomes `application/json` via Jackson.
- `@PathVariable` extracts URL segments; `@RequestParam` extracts query string parameters (`?name=Alice`).
- The context-loads smoke test (`@SpringBootTest`) is generated automatically and should be the first test you run after creating the project.
