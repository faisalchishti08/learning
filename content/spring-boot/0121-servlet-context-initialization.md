---
card: spring-boot
gi: 121
slug: servlet-context-initialization
title: Servlet context initialization
---

## 1. What it is

**Servlet context initialization** is the phase where the embedded Servlet container sets up the `ServletContext` before any request is handled. Spring Boot uses `ServletContextInitializer` — an interface with a single `onStartup(ServletContext)` method — to run code at this exact moment. Spring's own `DispatcherServlet` registration and every `*RegistrationBean` implement this interface. You implement it too when you need to interact with the raw `ServletContext` at startup.

## 2. Why & when

Some libraries require direct `ServletContext` access at startup: registering attributes, programmatic multipart configuration, or adding Servlet 3.0-style initializers. Spring Boot's embedded container doesn't use `web.xml`, so `ServletContainerInitializer` (the Servlet spec mechanism) isn't reliably invoked. `ServletContextInitializer` fills that gap in a Spring-Boot-idiomatic way.

Use it when:

- A third-party library expects `ServletContext` setup in `contextInitialized`.
- You need to set `ServletContext` attributes available to all servlets and filters.
- You need programmatic multipart config (`servlet.getRegistration("dispatcherServlet").setMultipartConfig(...)`).

## 3. Core concept

During startup, `SpringApplication` creates an embedded `WebServer` and passes every `ServletContextInitializer` bean to it. The container calls each `initializer.onStartup(servletContext)` in order, then opens the port.

```
SpringApplication starts
  ↓
EmbeddedWebServer.start()
  ↓
For each ServletContextInitializer bean → onStartup(servletContext)
  ↓
Port opens, requests accepted
```

This is different from `ApplicationListener<ContextRefreshedEvent>`: that fires after the Spring context is ready but not necessarily inside the Servlet lifecycle. `onStartup` fires *inside* the Servlet container startup, with a live `ServletContext`.

## 4. Diagram

<svg viewBox="0 0 680 210" xmlns="http://www.w3.org/2000/svg">
  <rect x="20" y="80" width="150" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="95" y="110" text-anchor="middle" fill="#6db33f" font-size="12" font-family="sans-serif">Spring Boot starts</text>
  <rect x="250" y="80" width="180" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="340" y="103" text-anchor="middle" fill="#79c0ff" font-size="12" font-family="sans-serif">Each</text>
  <text x="340" y="120" text-anchor="middle" fill="#79c0ff" font-size="11" font-family="sans-serif">ServletContextInitializer</text>
  <rect x="510" y="60" width="150" height="40" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="585" y="84" text-anchor="middle" fill="#e6edf3" font-size="11" font-family="sans-serif">DispatcherServlet reg</text>
  <rect x="510" y="112" width="150" height="40" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="585" y="136" text-anchor="middle" fill="#e6edf3" font-size="11" font-family="sans-serif">Your initializer</text>
  <rect x="510" y="164" width="150" height="40" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="585" y="188" text-anchor="middle" fill="#e6edf3" font-size="11" font-family="sans-serif">*RegistrationBeans</text>
  <line x1="172" y1="105" x2="246" y2="105" stroke="#6db33f" stroke-width="1.5" marker-end="url(#sc)"/>
  <line x1="432" y1="95" x2="506" y2="82" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#sc2)"/>
  <line x1="432" y1="105" x2="506" y2="132" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#sc2)"/>
  <line x1="432" y1="115" x2="506" y2="184" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#sc2)"/>
  <defs>
    <marker id="sc" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="sc2" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>
</svg>

Spring Boot iterates all `ServletContextInitializer` beans, calling `onStartup` on each before the port opens.

## 5. Runnable example

```java
// ServletContextInitApp.java  —  add to a Spring Boot project with spring-boot-starter-web
import jakarta.servlet.ServletContext;
import jakarta.servlet.ServletException;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.web.servlet.ServletContextInitializer;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

@SpringBootApplication
public class ServletContextInitApp {
    public static void main(String[] args) {
        SpringApplication.run(ServletContextInitApp.class, args);
    }
}

@Configuration
class InitConfig {

    @Bean
    public ServletContextInitializer appInitializer() {
        return new ServletContextInitializer() {
            @Override
            public void onStartup(ServletContext servletContext) throws ServletException {
                // Store app-wide metadata as a ServletContext attribute
                servletContext.setAttribute("APP_VERSION", "2.5.0");
                servletContext.setAttribute("STARTUP_TIME", System.currentTimeMillis());
                System.out.println("ServletContext initialized — version 2.5.0 registered");
            }
        };
    }
}

@RestController
class VersionController {

    private final jakarta.servlet.ServletContext ctx;

    VersionController(jakarta.servlet.ServletContext ctx) {
        this.ctx = ctx;
    }

    @GetMapping("/version")
    public String version() {
        return "Version: " + ctx.getAttribute("APP_VERSION")
                + ", started at: " + ctx.getAttribute("STARTUP_TIME");
    }
}
```

**How to run:** start the app — you'll see the initializer log on startup. Then `curl http://localhost:8080/version` to read the attributes set by the initializer.

## 6. Walkthrough

- `@Bean public ServletContextInitializer appInitializer()` declares the initializer as a Spring bean. Spring Boot's `EmbeddedWebApplicationContext` collects all `ServletContextInitializer` beans and passes them to the embedded container.
- `onStartup(ServletContext servletContext)` is called by the container before the first request. `servletContext.setAttribute(...)` stores values accessible to any servlet, filter, or Spring component that can see the `ServletContext`.
- `VersionController` injects `ServletContext` directly — Spring Boot auto-configures a `ServletContext` bean in the `WebApplicationContext`, so it can be constructor-injected like any other bean.
- `ctx.getAttribute("APP_VERSION")` retrieves what the initializer stored. This is a simple way to share startup-computed values (config paths, feature flags, resolved versions) across the entire web layer.
- The `System.currentTimeMillis()` startup time demonstrates that `onStartup` runs before any HTTP traffic — safe to compute expensive startup values here.

## 7. Gotchas & takeaways

> `ServletContextInitializer` is a Spring Boot interface, not the Servlet spec's `ServletContainerInitializer`. The two look similar but behave differently: the Servlet spec one is SPI-discovered via `META-INF/services` and isn't reliably called in embedded containers.

> Ordering matters if multiple initializers share the same `ServletContext` key. Implement `Ordered` or annotate with `@Order` to control sequence.

- `*RegistrationBean` classes already implement `ServletContextInitializer`; you don't need a separate bean to register servlets/filters.
- Attributes set on `ServletContext` are accessible from JSPs, servlet contexts, and Spring's `WebApplicationContext`.
- Don't confuse with `ApplicationContextInitializer` — that runs before the `ApplicationContext` is refreshed, not inside the Servlet lifecycle.
- Lambda form works: `return ctx -> ctx.setAttribute("KEY", value);` — `ServletContextInitializer` is a functional interface.
