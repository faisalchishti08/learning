---
card: spring-boot
gi: 122
slug: configurableservletwebserverfactory-webserverfactorycustomiz
title: ConfigurableServletWebServerFactory / WebServerFactoryCustomizer
---

## 1. What it is

`ConfigurableServletWebServerFactory` is the interface that all embedded Servlet container factories implement. It exposes methods to set the port, context path, session timeout, SSL config, and more — the common surface shared by Tomcat, Jetty, and Undertow.

`WebServerFactoryCustomizer<T extends WebServerFactory>` is a callback interface you implement to modify a factory just before the container starts. Spring Boot calls every `WebServerFactoryCustomizer` bean automatically; the type parameter `T` restricts which factory you want to target.

## 2. Why & when

Most embedded server tuning is done via `application.properties` (`server.port`, `server.ssl.*`, etc.). But some settings have no property equivalent, or you need to compute them at runtime (e.g., pick a port from an external config service). `WebServerFactoryCustomizer` is the programmatic escape hatch.

Use it when:

- A setting exists on `TomcatServletWebServerFactory` but not in `application.properties`.
- You need to add Tomcat connectors, valves, or protocol handlers.
- You want to share customization logic across multiple environments without duplicating properties files.

## 3. Core concept

The hierarchy:

```
WebServerFactory
  └─ ConfigurableWebServerFactory          (port, ssl, error pages)
       └─ ConfigurableServletWebServerFactory  (context path, session, JSP)
            └─ TomcatServletWebServerFactory   (Tomcat-specific)
               JettyServletWebServerFactory    (Jetty-specific)
               UndertowServletWebServerFactory (Undertow-specific)
```

`WebServerFactoryCustomizer<ConfigurableServletWebServerFactory>` targets all three containers. `WebServerFactoryCustomizer<TomcatServletWebServerFactory>` targets Tomcat only. Spring Boot applies all matching customizers in `@Order` order before calling `factory.getWebServer(...)`.

## 4. Diagram

<svg viewBox="0 0 680 220" xmlns="http://www.w3.org/2000/svg">
  <rect x="20" y="85" width="170" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="105" y="106" text-anchor="middle" fill="#6db33f" font-size="11" font-family="sans-serif">WebServerFactoryCustomizer</text>
  <text x="105" y="122" text-anchor="middle" fill="#8b949e" font-size="11" font-family="sans-serif">beans (your @Beans)</text>
  <rect x="270" y="65" width="190" height="90" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="365" y="90" text-anchor="middle" fill="#79c0ff" font-size="12" font-family="sans-serif">Configurable</text>
  <text x="365" y="107" text-anchor="middle" fill="#79c0ff" font-size="12" font-family="sans-serif">ServletWebServerFactory</text>
  <text x="365" y="130" text-anchor="middle" fill="#8b949e" font-size="10" font-family="sans-serif">Tomcat / Jetty / Undertow</text>
  <text x="365" y="147" text-anchor="middle" fill="#8b949e" font-size="10" font-family="sans-serif">setPort, setContextPath…</text>
  <rect x="530" y="85" width="130" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="595" y="108" text-anchor="middle" fill="#e6edf3" font-size="12" font-family="sans-serif">Embedded</text>
  <text x="595" y="124" text-anchor="middle" fill="#e6edf3" font-size="12" font-family="sans-serif">WebServer</text>
  <line x1="192" y1="110" x2="266" y2="110" stroke="#6db33f" stroke-width="1.5" marker-end="url(#wf)"/>
  <text x="229" y="105" text-anchor="middle" fill="#8b949e" font-size="10" font-family="sans-serif">customize()</text>
  <line x1="462" y1="110" x2="526" y2="110" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#wf2)"/>
  <text x="494" y="105" text-anchor="middle" fill="#8b949e" font-size="10" font-family="sans-serif">start()</text>
  <defs>
    <marker id="wf" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="wf2" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>
</svg>

Customizer beans call `factory.setXxx()` on the factory before `start()` launches the embedded server.

## 5. Runnable example

```java
// FactoryCustomizerApp.java  —  add to a Spring Boot project with spring-boot-starter-web
import org.apache.catalina.connector.Connector;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.web.embedded.tomcat.TomcatServletWebServerFactory;
import org.springframework.boot.web.server.ErrorPage;
import org.springframework.boot.web.servlet.server.ConfigurableServletWebServerFactory;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.HttpStatus;
import org.springframework.boot.web.server.WebServerFactoryCustomizer;

@SpringBootApplication
public class FactoryCustomizerApp {
    public static void main(String[] args) {
        SpringApplication.run(FactoryCustomizerApp.class, args);
    }
}

@Configuration
class ServerCustomizationConfig {

    // Targets ALL Servlet containers (Tomcat, Jetty, Undertow)
    @Bean
    public WebServerFactoryCustomizer<ConfigurableServletWebServerFactory> genericCustomizer() {
        return factory -> {
            factory.setPort(9090);
            factory.setContextPath("/app");
            factory.addErrorPages(new ErrorPage(HttpStatus.NOT_FOUND, "/404.html"));
        };
    }

    // Targets Tomcat ONLY — adds a second HTTP connector on port 9091
    @Bean
    public WebServerFactoryCustomizer<TomcatServletWebServerFactory> tomcatCustomizer() {
        return factory -> {
            Connector connector = new Connector("org.apache.coyote.http11.Http11NioProtocol");
            connector.setPort(9091);
            factory.addAdditionalTomcatConnectors(connector);
        };
    }
}
```

**How to run:** add to a Spring Boot + Tomcat project. Start the app — it listens on port 9090 at context path `/app`. The Tomcat-specific customizer also opens port 9091. Access `http://localhost:9090/app/` to verify.

## 6. Walkthrough

- `WebServerFactoryCustomizer<ConfigurableServletWebServerFactory>` targets `ConfigurableServletWebServerFactory` — the common supertype — so it runs for Tomcat, Jetty, and Undertow alike.
- `factory.setPort(9090)` overrides `server.port` from `application.properties` (properties file wins if both are set — but this approach computes ports at runtime if needed).
- `factory.setContextPath("/app")` prefixes all URL paths. This is equivalent to `server.servlet.context-path=/app`.
- `factory.addErrorPages(new ErrorPage(HttpStatus.NOT_FOUND, "/404.html"))` maps the 404 status to a custom error page — same as `server.error.path` but per-status.
- `WebServerFactoryCustomizer<TomcatServletWebServerFactory>` only fires when the active factory is `TomcatServletWebServerFactory`. `addAdditionalTomcatConnectors` adds a second connector — a Tomcat-specific feature with no generic equivalent.
- Spring Boot orders all `WebServerFactoryCustomizer` beans before the factory's own `@ConfigurationProperties` (`ServerProperties`) are applied, so properties-file values take final precedence.

## 7. Gotchas & takeaways

> `WebServerFactoryCustomizer` is called **before** `application.properties` values are applied to the factory via `ServerProperties`. If you set `factory.setPort(9090)` in a customizer AND `server.port=8080` in properties, properties win. Use customizers only for settings with no property equivalent.

> If you replace the factory bean entirely (declaring a `TomcatServletWebServerFactory` `@Bean`), auto-configuration backs off and your customizers may not run. Prefer customizers over factory replacement.

- Implement `Ordered` or use `@Order` when multiple customizers touch the same property — last one wins.
- `ConfigurableServletWebServerFactory` covers session config, mime types, JSP config, and error pages; `TomcatServletWebServerFactory` adds connectors, valves, and protocol configuration.
- For WebFlux apps the equivalent is `WebServerFactoryCustomizer<ConfigurableReactiveWebServerFactory>`.
