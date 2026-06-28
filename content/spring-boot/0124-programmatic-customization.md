---
card: spring-boot
gi: 124
slug: programmatic-customization
title: Programmatic customization
---

## 1. What it is

**Programmatic customization** of the embedded server means using Java code — not `application.properties` — to configure the embedded container. The primary mechanisms are:

1. **`WebServerFactoryCustomizer<F>`** — a Spring Boot callback bean that receives the factory just before startup.
2. **Replacing the factory bean** — declare a `TomcatServletWebServerFactory` (or Jetty/Undertow equivalent) as a `@Bean`; Spring Boot backs off its auto-configured one.

This is the correct approach when you need runtime-computed values, container-specific APIs, or settings that have no `server.*` property equivalent.

## 2. Why & when

Properties files are static. Programmatic customization is needed when:

- Port or context path comes from an external service or environment variable processed at startup.
- You need Tomcat-specific features: additional connectors, custom valves (request logging, RemoteIP), AJP connectors, or Coyote protocol configuration.
- You need Jetty-specific handler configuration or thread pool sizing.
- You need to add SSL certificates fetched from a vault at startup, not read from a file path in properties.

## 3. Core concept

`WebServerFactoryCustomizer<F>` has a single method `customize(F factory)`. Spring Boot discovers all such beans and calls them in `@Order` order. `F` is the factory type you want to target:

- `ConfigurableServletWebServerFactory` → all three containers.
- `TomcatServletWebServerFactory` → Tomcat only.
- `JettyServletWebServerFactory` → Jetty only.

When you need complete control, declare the factory bean yourself. Auto-configuration uses `@ConditionalOnMissingBean(value = ServletWebServerFactory.class)`, so your bean replaces it entirely.

## 4. Diagram

<svg viewBox="0 0 680 230" xmlns="http://www.w3.org/2000/svg">
  <rect x="20" y="90" width="150" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="95" y="118" text-anchor="middle" fill="#6db33f" font-size="12" font-family="sans-serif">Your @Bean</text>
  <rect x="255" y="60" width="190" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="350" y="82" text-anchor="middle" fill="#79c0ff" font-size="12" font-family="sans-serif">WebServerFactoryCustomizer</text>
  <text x="350" y="99" text-anchor="middle" fill="#8b949e" font-size="11" font-family="sans-serif">customize(factory)</text>
  <rect x="255" y="140" width="190" height="50" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="350" y="162" text-anchor="middle" fill="#8b949e" font-size="12" font-family="sans-serif">OR: replace factory bean</text>
  <text x="350" y="178" text-anchor="middle" fill="#8b949e" font-size="11" font-family="sans-serif">TomcatServletWebServerFactory</text>
  <rect x="520" y="90" width="140" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="590" y="112" text-anchor="middle" fill="#e6edf3" font-size="12" font-family="sans-serif">Embedded</text>
  <text x="590" y="128" text-anchor="middle" fill="#e6edf3" font-size="12" font-family="sans-serif">Tomcat / Jetty</text>
  <line x1="172" y1="115" x2="251" y2="90" stroke="#6db33f" stroke-width="1.5" marker-end="url(#pc)"/>
  <line x1="172" y1="115" x2="251" y2="160" stroke="#6db33f" stroke-width="1.5" marker-end="url(#pc)"/>
  <line x1="447" y1="90" x2="516" y2="110" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#pc2)"/>
  <line x1="447" y1="165" x2="516" y2="125" stroke="#8b949e" stroke-width="1.5" marker-end="url(#pc3)"/>
  <defs>
    <marker id="pc" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="pc2" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#79c0ff"/></marker>
    <marker id="pc3" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

Your `@Bean` can use a customizer (preferred, additive) or replace the factory entirely (full control).

## 5. Runnable example

```java
// ProgrammaticCustomApp.java  —  Spring Boot project with spring-boot-starter-web
import org.apache.catalina.valves.AccessLogValve;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.web.embedded.tomcat.TomcatServletWebServerFactory;
import org.springframework.boot.web.server.WebServerFactoryCustomizer;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

@SpringBootApplication
public class ProgrammaticCustomApp {
    public static void main(String[] args) {
        SpringApplication.run(ProgrammaticCustomApp.class, args);
    }
}

@Configuration
class TomcatConfig {

    @Bean
    public WebServerFactoryCustomizer<TomcatServletWebServerFactory> tomcatCustomizer() {
        return factory -> {
            // 1. Change thread pool size programmatically
            factory.addConnectorCustomizers(connector ->
                connector.setMaxPostSize(5 * 1024 * 1024)  // 5 MB max POST body
            );

            // 2. Add an Tomcat AccessLog valve (logs every request to stdout)
            AccessLogValve valve = new AccessLogValve();
            valve.setDirectory(".");
            valve.setPrefix("access_log");
            valve.setSuffix(".txt");
            valve.setPattern("%h %l %u %t \"%r\" %s %b");
            valve.setBuffered(false);
            factory.addEngineValves(valve);

            System.out.println("Tomcat programmatic customization applied.");
        };
    }
}

@RestController
class EchoController {

    @GetMapping("/echo")
    public String echo() {
        return "Server is customized programmatically!";
    }
}
```

**How to run:** in a Spring Boot + Tomcat project, start the app. The console shows the customization message. Hit `http://localhost:8080/echo` and check the `access_log*.txt` file created in your working directory.

## 6. Walkthrough

- `WebServerFactoryCustomizer<TomcatServletWebServerFactory>` ensures this customizer is only invoked when the active factory is Tomcat. If you switch to Jetty, this bean is silently skipped.
- `factory.addConnectorCustomizers(connector -> ...)` gives access to Tomcat's `Connector` object — the lowest-level API, covering anything configurable via server.xml. Here `setMaxPostSize` sets a 5 MB limit on request bodies.
- `AccessLogValve` is a standard Tomcat valve that logs HTTP access in Combined Log Format. Adding it here avoids needing a Tomcat `server.xml` entirely — the embedded server has no XML config.
- `valve.setBuffered(false)` writes access log entries immediately (important for debugging); the default buffers them.
- `factory.addEngineValves(valve)` wires the valve into Tomcat's Engine. Valves run in order around every request, similar to Servlet filters but at the container level.
- The `@Configuration` class and `@Bean` declaration let Spring Boot discover the customizer automatically — no explicit registration needed.

## 7. Gotchas & takeaways

> If you declare a `TomcatServletWebServerFactory` `@Bean` to replace the factory entirely, Spring Boot's `WebServerFactoryCustomizer` beans **may not run** against it — they target the auto-configured factory. Test carefully when mixing both approaches.

> `addConnectorCustomizers` replaces the customization list on each call rather than appending, unless you call the varargs form. Always pass all needed customizers in a single call or accumulate them.

- Prefer `WebServerFactoryCustomizer` over factory replacement — it's additive and doesn't break other customizers.
- Properties (`server.*`) are applied after your customizer; if you set the port in the customizer and also in properties, properties win.
- Tomcat valves are container-level; they run even for requests that result in 404 from Spring MVC. Use them for cross-cutting concerns (rate limiting, access logging, RemoteIP trust).
- For Jetty: `JettyServletWebServerFactory.addServerCustomizers(...)` — same pattern, different API surface.
