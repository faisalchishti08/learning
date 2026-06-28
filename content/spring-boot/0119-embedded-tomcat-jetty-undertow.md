---
card: spring-boot
gi: 119
slug: embedded-tomcat-jetty-undertow
title: Embedded Tomcat / Jetty / Undertow
---

## 1. What it is

Spring Boot embeds a Servlet container directly into the application JAR so you run your app with `java -jar app.jar` — no separate server installation required. Three containers are supported out of the box:

- **Tomcat** — the default; mature, widely deployed, excellent ecosystem.
- **Jetty** — lightweight, asynchronous, good fit for many concurrent long-lived connections.
- **Undertow** (from WildFly) — non-blocking at its core, very low memory footprint.

All three expose the same Spring Boot configuration surface; switching is a one-line dependency change.

## 2. Why & when

Traditional Java web apps required a separately managed Tomcat or JBoss instance. Embedding the server in the JAR:

- Eliminates deployment discrepancies between dev and prod.
- Enables `java -jar` deployment to any machine or container image.
- Makes the server a versioned dependency — same controls as any library.

Choose Tomcat unless you have a specific reason. Switch to Jetty or Undertow when you need:

- **Jetty**: WebSocket-heavy workloads or servlet-free deployments.
- **Undertow**: maximum throughput with minimal memory, or you need XNIO-based non-blocking IO throughout.

## 3. Core concept

`spring-boot-starter-web` pulls in `spring-boot-starter-tomcat` transitively. Switching is done by excluding Tomcat and adding the desired alternative:

```xml
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-web</artifactId>
    <exclusions>
        <exclusion>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-tomcat</artifactId>
        </exclusion>
    </exclusions>
</dependency>
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-jetty</artifactId>
</dependency>
```

All containers implement `WebServer` and `ServletWebServerFactory`. Spring Boot's auto-configuration detects which factory is available and starts the right one.

## 4. Diagram

<svg viewBox="0 0 680 230" xmlns="http://www.w3.org/2000/svg">
  <rect x="240" y="10" width="200" height="45" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="340" y="37" text-anchor="middle" fill="#6db33f" font-size="13" font-family="sans-serif">spring-boot-starter-web</text>
  <rect x="60" y="100" width="150" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="135" y="130" text-anchor="middle" fill="#79c0ff" font-size="13" font-family="sans-serif">Tomcat (default)</text>
  <rect x="265" y="100" width="150" height="50" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="340" y="130" text-anchor="middle" fill="#8b949e" font-size="13" font-family="sans-serif">Jetty</text>
  <rect x="470" y="100" width="150" height="50" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="545" y="130" text-anchor="middle" fill="#8b949e" font-size="13" font-family="sans-serif">Undertow</text>
  <line x1="340" y1="57" x2="135" y2="98" stroke="#6db33f" stroke-width="1.5" marker-end="url(#et)"/>
  <line x1="340" y1="57" x2="340" y2="98" stroke="#8b949e" stroke-width="1.5" stroke-dasharray="5,3" marker-end="url(#et2)"/>
  <line x1="340" y1="57" x2="545" y2="98" stroke="#8b949e" stroke-width="1.5" stroke-dasharray="5,3" marker-end="url(#et2)"/>
  <text x="180" y="82" fill="#6db33f" font-size="10" font-family="sans-serif">transitive</text>
  <text x="345" y="82" fill="#8b949e" font-size="10" font-family="sans-serif">swap in</text>
  <rect x="240" y="175" width="200" height="40" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1"/>
  <text x="340" y="199" text-anchor="middle" fill="#e6edf3" font-size="12" font-family="sans-serif">WebServer (common API)</text>
  <line x1="135" y1="152" x2="290" y2="175" stroke="#e6edf3" stroke-width="1" stroke-dasharray="3,3"/>
  <line x1="340" y1="152" x2="340" y2="174" stroke="#e6edf3" stroke-width="1" stroke-dasharray="3,3"/>
  <line x1="545" y1="152" x2="395" y2="175" stroke="#e6edf3" stroke-width="1" stroke-dasharray="3,3"/>
  <defs>
    <marker id="et" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="et2" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

`spring-boot-starter-web` includes Tomcat by default; exclude it and add Jetty or Undertow — all implement the same `WebServer` interface.

## 5. Runnable example

```java
// EmbeddedServerApp.java — shows Tomcat (default) and how to inspect the running server
// Add to any Spring Boot project with spring-boot-starter-web

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.web.embedded.tomcat.TomcatServletWebServerFactory;
import org.springframework.boot.web.server.WebServer;
import org.springframework.boot.web.servlet.context.ServletWebServerApplicationContext;
import org.springframework.context.ApplicationContext;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

@SpringBootApplication
public class EmbeddedServerApp {
    public static void main(String[] args) {
        ApplicationContext ctx = SpringApplication.run(EmbeddedServerApp.class, args);

        // Inspect which container is running
        ServletWebServerApplicationContext webCtx =
                (ServletWebServerApplicationContext) ctx;
        WebServer server = webCtx.getWebServer();
        System.out.println("Container type : " + server.getClass().getSimpleName());
        System.out.println("Listening on   : " + server.getPort());
    }
}

@RestController
class InfoController {

    private final ServletWebServerApplicationContext webCtx;

    InfoController(ServletWebServerApplicationContext webCtx) {
        this.webCtx = webCtx;
    }

    @GetMapping("/server-info")
    public String info() {
        WebServer server = webCtx.getWebServer();
        return "Running on " + server.getClass().getSimpleName()
                + " port " + server.getPort();
    }
}
```

**How to run:** in a Spring Boot project (default is Tomcat), start with `./mvnw spring-boot:run`. The console prints the container type. To switch to Jetty, replace `spring-boot-starter-tomcat` with `spring-boot-starter-jetty` in `pom.xml` — no code change needed.

## 6. Walkthrough

- `SpringApplication.run(...)` returns the `ApplicationContext`. Casting it to `ServletWebServerApplicationContext` gives access to the embedded `WebServer`.
- `webCtx.getWebServer()` returns the live server object — `TomcatWebServer`, `JettyWebServer`, or `UndertowWebServer` depending on which factory bean is present.
- `server.getClass().getSimpleName()` names the container; `server.getPort()` confirms the actual bound port (useful when `server.port=0` is used for random-port tests).
- `InfoController` demonstrates injecting the context into a REST handler — call `/server-info` after startup to see the same info over HTTP.
- Spring Boot's auto-configuration uses `@ConditionalOnClass` to detect which container is on the classpath and registers the matching `*ServletWebServerFactory` bean.

## 7. Gotchas & takeaways

> Never have two container starters on the classpath at the same time — Spring Boot picks the first it finds and the behaviour is undefined. Exclude Tomcat explicitly before adding Jetty or Undertow.

> JSP support requires Tomcat or Jetty; Undertow has no JSP engine. If you need JSP, stay on Tomcat.

- Switching containers requires only a dependency change; all `server.*` properties work identically.
- Undertow uses fewer threads than Tomcat; benchmark your workload before switching in production.
- For reactive apps (`spring-boot-starter-webflux`) the default is Netty, not Tomcat.
- `server.port=0` binds to a random port — useful for integration tests to avoid conflicts.
- The embedded server is not the same as an external WAR deployment; embedded apps run as plain JARs.
