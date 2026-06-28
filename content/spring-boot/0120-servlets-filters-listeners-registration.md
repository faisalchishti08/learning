---
card: spring-boot
gi: 120
slug: servlets-filters-listeners-registration
title: Servlets, Filters, Listeners registration
---

## 1. What it is

When using an embedded Servlet container, you can't drop a `web.xml` to register Servlets, Filters, or Listeners. Spring Boot provides three registration-bean wrappers instead: `ServletRegistrationBean`, `FilterRegistrationBean`, and `ServletListenerRegistrationBean`. Alternatively, standard annotations (`@WebServlet`, `@WebFilter`, `@WebListener`) work when you add `@ServletComponentScan` to the application class.

## 2. Why & when

Legacy servlets, third-party servlet-based libraries, and servlet filters (logging, authentication, request decoration) all need to be wired into the container at startup. Spring Boot's embedded container is started programmatically, so registration must also be programmatic or annotation-driven — not through `web.xml`.

Use `*RegistrationBean` when you need fine-grained control (URL patterns, filter order, init parameters). Use `@WebServlet` / `@WebFilter` / `@WebListener` + `@ServletComponentScan` for quick registration of classes you own, especially in greenfield code.

## 3. Core concept

`ServletRegistrationBean<T extends Servlet>` wraps a Servlet instance and exposes methods to set URL mappings, load-on-startup order, and init parameters. `FilterRegistrationBean<T extends Filter>` adds URL patterns and servlet name targeting. `ServletListenerRegistrationBean<T extends EventListener>` wraps `HttpSessionListener`, `ServletContextListener`, etc.

All three are Spring `@Bean` definitions — Spring Boot detects them and registers them with the embedded container during startup.

Analogy: these beans are the programmatic equivalent of `<servlet>`, `<filter>`, and `<listener>` stanzas in `web.xml`.

## 4. Diagram

<svg viewBox="0 0 680 230" xmlns="http://www.w3.org/2000/svg">
  <rect x="20" y="90" width="160" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="100" y="120" text-anchor="middle" fill="#6db33f" font-size="12" font-family="sans-serif">Spring @Bean definitions</text>
  <rect x="260" y="50" width="175" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="347" y="75" text-anchor="middle" fill="#79c0ff" font-size="12" font-family="sans-serif">ServletRegistrationBean</text>
  <rect x="260" y="105" width="175" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="347" y="130" text-anchor="middle" fill="#79c0ff" font-size="12" font-family="sans-serif">FilterRegistrationBean</text>
  <rect x="260" y="160" width="175" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="347" y="185" text-anchor="middle" fill="#79c0ff" font-size="12" font-family="sans-serif">ListenerRegistrationBean</text>
  <rect x="510" y="90" width="150" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="585" y="112" text-anchor="middle" fill="#e6edf3" font-size="12" font-family="sans-serif">Embedded</text>
  <text x="585" y="128" text-anchor="middle" fill="#e6edf3" font-size="12" font-family="sans-serif">Servlet Container</text>
  <line x1="182" y1="115" x2="256" y2="72" stroke="#6db33f" stroke-width="1.5" marker-end="url(#fl)"/>
  <line x1="182" y1="115" x2="256" y2="125" stroke="#6db33f" stroke-width="1.5" marker-end="url(#fl)"/>
  <line x1="182" y1="115" x2="256" y2="180" stroke="#6db33f" stroke-width="1.5" marker-end="url(#fl)"/>
  <line x1="437" y1="72" x2="506" y2="108" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#fl2)"/>
  <line x1="437" y1="125" x2="506" y2="115" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#fl2)"/>
  <line x1="437" y1="180" x2="506" y2="125" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#fl2)"/>
  <defs>
    <marker id="fl" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="fl2" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>
</svg>

Spring beans wrap Servlet / Filter / Listener instances and feed them into the embedded container at startup.

## 5. Runnable example

```java
// RegistrationApp.java  —  add to a Spring Boot project with spring-boot-starter-web
import jakarta.servlet.*;
import jakarta.servlet.http.*;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.web.servlet.*;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import java.io.IOException;

@SpringBootApplication
public class RegistrationApp {
    public static void main(String[] args) {
        SpringApplication.run(RegistrationApp.class, args);
    }
}

// A plain Servlet (no Spring MVC involved)
class HelloServlet extends HttpServlet {
    @Override
    protected void doGet(HttpServletRequest req, HttpServletResponse resp)
            throws IOException {
        resp.getWriter().write("Hello from raw Servlet!");
    }
}

// A Filter that logs every request
class LoggingFilter implements Filter {
    @Override
    public void doFilter(ServletRequest req, ServletResponse res, FilterChain chain)
            throws IOException, ServletException {
        System.out.println("REQUEST: " + ((HttpServletRequest) req).getRequestURI());
        chain.doFilter(req, res);
    }
}

// A Listener that logs session creation
class SessionListener implements HttpSessionListener {
    @Override
    public void sessionCreated(HttpSessionEvent se) {
        System.out.println("Session created: " + se.getSession().getId());
    }
}

@Configuration
class WebConfig {

    @Bean
    public ServletRegistrationBean<HelloServlet> helloServlet() {
        return new ServletRegistrationBean<>(new HelloServlet(), "/hello");
    }

    @Bean
    public FilterRegistrationBean<LoggingFilter> loggingFilter() {
        FilterRegistrationBean<LoggingFilter> reg = new FilterRegistrationBean<>(new LoggingFilter());
        reg.addUrlPatterns("/*");   // apply to all paths
        reg.setOrder(1);            // lower = earlier in chain
        return reg;
    }

    @Bean
    public ServletListenerRegistrationBean<SessionListener> sessionListener() {
        return new ServletListenerRegistrationBean<>(new SessionListener());
    }
}
```

**How to run:** start the app, then `curl http://localhost:8080/hello`. The console logs the request; the browser receives "Hello from raw Servlet!".

## 6. Walkthrough

- `HelloServlet` extends `HttpServlet` directly — standard Java EE, no Spring MVC.
- `new ServletRegistrationBean<>(new HelloServlet(), "/hello")` registers the servlet on path `/hello`. The factory constructor is the shortest form; use the setters for more URL patterns or init parameters.
- `LoggingFilter.doFilter(...)` calls `chain.doFilter(req, res)` to pass the request forward — omitting this short-circuits the rest of the chain.
- `FilterRegistrationBean.setOrder(1)` sets the filter's position in the chain. Lower numbers run first. Spring Security's filter is typically at order `-100` to run before application filters.
- `SessionListener` is picked up by `ServletListenerRegistrationBean` — no Spring annotations needed on the listener class itself.
- All three `@Bean` methods live in a `@Configuration` class; Spring Boot detects them and passes them to the embedded container via `ServletContextInitializer`.

## 7. Gotchas & takeaways

> `@WebServlet` / `@WebFilter` / `@WebListener` annotations on their own are **not** scanned by default. You must add `@ServletComponentScan` to your main application class, or use `*RegistrationBean` instead.

> Filter ordering matters. Without an explicit `setOrder`, `FilterRegistrationBean` uses `Integer.MAX_VALUE` — that puts your filter last. Always set order explicitly for anything security or logging related.

- `FilterRegistrationBean` lets you restrict a filter to specific URL patterns or servlet names — useful to exclude `/actuator/**` from certain filters.
- Init parameters set via `FilterRegistrationBean.addInitParameter()` are readable in the filter via `FilterConfig`.
- A `Filter` bean without a `FilterRegistrationBean` wrapper is still registered — but at `LOWEST_PRECEDENCE` order and on `/*`. Wrap it for control.
- `@Order` on the filter class itself does **not** control servlet filter order; only `FilterRegistrationBean.setOrder()` does.
