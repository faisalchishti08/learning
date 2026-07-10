---
card: java
gi: 1047
slug: spring-boot
title: Spring Boot
---

## 1. What it is

Spring Boot is a layer built on top of the core Spring container ([Spring Core & DI container](1046-spring-core-di-container.md)) that eliminates most of the manual configuration a "plain" Spring application requires: **auto-configuration** inspects what's on your classpath and configures sensible defaults automatically (add `spring-boot-starter-web` as a dependency, and an embedded web server, a `DispatcherServlet`, and JSON serialization are all wired up without you writing any configuration for them), and an embedded server (Tomcat by default) means `java -jar myapp.jar` starts a fully running web application — no separate application server to install or deploy to.

## 2. Why & when

Configuring a "plain" Spring web application by hand means explicitly declaring beans for a `DispatcherServlet`, a view resolver, a JSON message converter, and dozens of other infrastructure pieces most applications configure identically every time — genuinely useful flexibility for unusual setups, but repetitive boilerplate for the overwhelming majority of ordinary applications. Spring Boot's auto-configuration inspects your classpath and active configuration and provides working defaults for all of this automatically — you get a fully functional web server by adding one dependency and writing your actual business logic, with the option to override any specific default (via `application.properties` or your own bean definitions) exactly when your application genuinely needs something different.

Reach for Spring Boot as the default choice for essentially any new Spring application — the auto-configuration and embedded-server model removes an enormous amount of setup that "plain" Spring requires, and overriding a specific default when needed is straightforward rather than requiring you to configure everything from scratch. "Plain" Spring (configuring the container directly, as in [Spring Core & DI container](1046-spring-core-di-container.md)) remains relevant mainly for understanding what Spring Boot is actually automating underneath, or for genuinely unusual deployment models an embedded server doesn't fit.

## 3. Core concept

```java
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

@SpringBootApplication // combines @Configuration, @ComponentScan, and @EnableAutoConfiguration
public class MyApplication {
    public static void main(String[] args) {
        SpringApplication.run(MyApplication.class, args); // starts an embedded web server too
    }
}

@RestController
class GreetingController {
    @GetMapping("/hello")
    String hello() {
        return "Hello from Spring Boot!"; // auto-configured JSON/text serialization handles the response
    }
}
```

```xml
<!-- pom.xml: one starter dependency pulls in a working embedded web server,
     JSON support, and Spring MVC -- no manual servlet/server configuration needed -->
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-web</artifactId>
</dependency>
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Adding the spring-boot-starter-web dependency triggers auto-configuration that wires up an embedded Tomcat server, DispatcherServlet, and JSON conversion, all without explicit configuration code">
  <rect x="30" y="60" width="200" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="130" y="90" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">spring-boot-starter-web</text>

  <rect x="280" y="20" width="150" height="30" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="355" y="40" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">embedded Tomcat</text>
  <rect x="280" y="60" width="150" height="30" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="355" y="80" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">DispatcherServlet</text>
  <rect x="280" y="100" width="150" height="30" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="355" y="120" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">JSON conversion</text>

  <line x1="230" y1="80" x2="280" y2="35" stroke="#8b949e" marker-end="url(#a)"/>
  <line x1="230" y1="85" x2="280" y2="75" stroke="#8b949e" marker-end="url(#a)"/>
  <line x1="230" y1="90" x2="280" y2="115" stroke="#8b949e" marker-end="url(#a)"/>
  <defs><marker id="a" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

One starter dependency triggers auto-configuration for several infrastructure pieces, none of which need explicit configuration code.

## 5. Runnable example

Scenario: a small REST endpoint, evolving from Spring Boot's minimal defaults into a properly configured, overridden application demonstrating auto-configuration versus explicit customization.

### Level 1 — Basic

```java
// File: src/main/java/com/example/MyApplication.java
package com.example;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

@SpringBootApplication
public class MyApplication {
    public static void main(String[] args) {
        SpringApplication.run(MyApplication.class, args);
    }
}

@RestController
class GreetingController {
    @GetMapping("/hello")
    String hello() {
        return "Hello from Spring Boot!";
    }
}
```

**How to run:** place in a Maven project generated via [start.spring.io](https://start.spring.io) with the "Spring Web" dependency (or add `spring-boot-starter-web` and `spring-boot-starter-parent` manually), then run `mvn spring-boot:run`, and in a separate terminal, `curl http://localhost:8080/hello`.

Expected output (from the `curl` command):
```
Hello from Spring Boot!
```

Notice `application.properties` doesn't even need to exist — the embedded server started on the default port `8080`, `DispatcherServlet` routed `GET /hello` to `GreetingController.hello`, and the returned `String` was written directly as the response body, all from auto-configuration triggered purely by having `spring-boot-starter-web` on the classpath.

### Level 2 — Intermediate

```properties
# File: src/main/resources/application.properties
# Overriding a specific auto-configured default -- the port, in this case --
# without needing to write any Java configuration code for it.
server.port=9090
```

```java
// File: src/main/java/com/example/MyApplication.java (unchanged from Level 1)
package com.example;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

@SpringBootApplication
public class MyApplication {
    public static void main(String[] args) {
        SpringApplication.run(MyApplication.class, args);
    }
}

@RestController
class GreetingController {
    @GetMapping("/hello")
    String hello() {
        return "Hello from Spring Boot!";
    }
}
```

**How to run:** add the `application.properties` file shown, run `mvn spring-boot:run`, then `curl http://localhost:9090/hello`.

Expected output:
```
Hello from Spring Boot!
```

The real-world concern added: a single line in `application.properties` overrides the default embedded server port from `8080` to `9090` — no Java code was written to reconfigure the server; Spring Boot's auto-configuration reads this property and applies it automatically, demonstrating the "convention with easy override" model.

### Level 3 — Advanced

```java
// File: src/main/java/com/example/GreetingController.java
package com.example;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
class GreetingController {
    @GetMapping("/hello")
    Greeting hello(@RequestParam(defaultValue = "World") String name) {
        // Returning a plain Java object (not a String) -- auto-configured JSON
        // conversion (Jackson, on the classpath via spring-boot-starter-web)
        // serializes this into a JSON response body automatically.
        return new Greeting("Hello, " + name + "!");
    }

    record Greeting(String message) {}
}
```

```properties
# File: src/main/resources/application.properties
server.port=9090
spring.application.name=greeting-service
```

```java
// File: src/main/java/com/example/MyApplication.java
package com.example;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication
public class MyApplication {
    public static void main(String[] args) {
        SpringApplication.run(MyApplication.class, args);
    }
}
```

**How to run:** with the files above, run `mvn spring-boot:run`, then `curl http://localhost:9090/hello` and `curl http://localhost:9090/hello?name=Ana`.

Expected output (from `curl http://localhost:9090/hello`):
```
{"message":"Hello, World!"}
```

Expected output (from `curl http://localhost:9090/hello?name=Ana`):
```
{"message":"Hello, Ana!"}
```

The production-flavored hard case: `hello` now returns a `Greeting` record instead of a plain `String` — Spring Boot's auto-configured Jackson integration automatically serializes it to JSON, with zero explicit configuration for JSON conversion anywhere in the code. `@RequestParam(defaultValue = "World")` demonstrates request-parameter binding with a fallback, and the response `Content-Type` header is set to `application/json` automatically as well, all inferred from the return type and auto-configured infrastructure.

## 6. Walkthrough

Tracing what happens when `curl http://localhost:9090/hello?name=Ana` hits the running application:

1. The embedded Tomcat server (started automatically by `SpringApplication.run`, listening on port `9090` per the overridden `server.port` property) receives the incoming HTTP `GET` request for `/hello?name=Ana`.
2. Spring's auto-configured `DispatcherServlet` receives the request and consults its routing table (built from scanning `@RestController`/`@GetMapping` annotations at startup) to find that `/hello` maps to `GreetingController.hello`.
3. Before invoking the method, Spring resolves its parameter: `@RequestParam(defaultValue = "World") String name` looks for a query parameter named `name` in the request — since the URL includes `?name=Ana`, it binds `name = "Ana"` (had the query parameter been absent, it would have used the default value, `"World"`, exactly as demonstrated by the first `curl` call).
4. `hello("Ana")` executes: `new Greeting("Hello, Ana!")` constructs a record instance wrapping the message string, which is returned from the method.
5. Since `GreetingController` is annotated `@RestController` (rather than plain `@Controller`), Spring treats the returned `Greeting` object as the response body directly, rather than as a view name to resolve — the auto-configured Jackson `ObjectMapper` (present because `spring-boot-starter-web` pulled it in transitively) serializes the `Greeting` record's `message` component into the JSON structure `{"message":"Hello, Ana!"}`.
6. `DispatcherServlet` writes this JSON as the HTTP response body, sets the `Content-Type` header to `application/json` (inferred automatically from the fact that Jackson was used to produce the body), and Tomcat sends the complete response back to the `curl` client, which prints the JSON exactly as received.

## 7. Gotchas & takeaways

> **Gotcha:** auto-configuration is convenient but can obscure exactly *why* a given piece of infrastructure exists in your running application — Spring Boot provides `--debug` (or the `spring-boot-starter-actuator`'s `/actuator/conditions` endpoint) specifically to show which auto-configurations were applied (and which were skipped, and why), useful when a default doesn't behave as expected and you need to understand what's actually configured.

- Spring Boot's auto-configuration inspects the classpath and active configuration to wire up sensible defaults automatically, based purely on which starter dependencies are present.
- `@SpringBootApplication` is shorthand combining `@Configuration`, `@ComponentScan`, and `@EnableAutoConfiguration` — the single annotation that enables Spring Boot's convention-driven behavior.
- `application.properties` (or `application.yml`) is the standard way to override specific auto-configured defaults (server port, application name, and hundreds of other properties) without writing Java configuration code.
- Returning a plain object from a `@RestController` method (rather than a `String`) triggers auto-configured JSON serialization via Jackson, present on the classpath through `spring-boot-starter-web`.
- The embedded server model (Tomcat by default) means a Spring Boot application is a self-contained, directly-runnable JAR — no separate application server installation or deployment step required.
- Spring Boot's auto-configuration builds directly on top of the same underlying container mechanics from [Spring Core & DI container](1046-spring-core-di-container.md) — beans are still discovered, constructed, and wired the same way; Spring Boot just pre-registers a large set of sensible ones automatically based on your classpath.
