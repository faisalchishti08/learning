---
card: spring-framework
gi: 294
slug: servlet-config-web-xml-webapplicationinitializer
title: "Servlet Config: web.xml vs WebApplicationInitializer"
---

## 1. What it is

There are two ways to configure a Spring MVC application for deployment in a Servlet container (Tomcat, Jetty, Undertow):

**`web.xml`** (legacy): an XML file at `WEB-INF/web.xml`, processed by the Servlet container at startup. Declares servlets, filters, listeners, and their URL mappings.

**`WebApplicationInitializer`** (modern, Java-code): a Java interface detected by `SpringServletContainerInitializer` (via `ServletContainerInitializer` SPI). Lets you replace `web.xml` entirely with Java configuration.

```java
// web.xml equivalent in Java:
public class MyWebAppInit extends AbstractAnnotationConfigDispatcherServletInitializer {
    @Override protected Class<?>[] getRootConfigClasses() { return new Class[]{RootConfig.class}; }
    @Override protected Class<?>[] getServletConfigClasses() { return new Class[]{WebConfig.class}; }
    @Override protected String[] getServletMappings() { return new String[]{"/"}; }
}
```

Spring Boot embeds the container and calls `onStartup()` programmatically — no `web.xml` needed at all.

## 2. Why & when

`web.xml` is required for very old (Servlet 2.5) containers that don't support `ServletContainerInitializer`. For everything Servlet 3.0+, `WebApplicationInitializer` is the idiomatic choice:
- Type-safe — no XML string errors.
- Refactorable — IDE refactoring renames config class references.
- Conditionally composable — Java `if` statements replace XML profiles.
- Testable — the `onStartup()` method is plain Java, unit-testable in isolation.

Convenience hierarchy:
- `WebApplicationInitializer` — raw interface; `onStartup(ServletContext)` called by Spring.
- `AbstractDispatcherServletInitializer` — provides `registerDispatcherServlet()`, `registerContextLoaderListener()`.
- `AbstractAnnotationConfigDispatcherServletInitializer` — further simplified; just override three methods.

## 3. Core concept

**`web.xml` structure:**

```xml
<web-app>
  <!-- Root context -->
  <listener>
    <listener-class>org.springframework.web.context.ContextLoaderListener</listener-class>
  </listener>
  <context-param>
    <param-name>contextClass</param-name>
    <param-value>org.springframework.web.context.support.AnnotationConfigWebApplicationContext</param-value>
  </context-param>
  <context-param>
    <param-name>contextConfigLocation</param-name>
    <param-value>com.example.RootConfig</param-value>
  </context-param>

  <!-- Servlet context -->
  <servlet>
    <servlet-name>dispatcher</servlet-name>
    <servlet-class>org.springframework.web.servlet.DispatcherServlet</servlet-class>
    <init-param>
      <param-name>contextClass</param-name>
      <param-value>org.springframework.web.context.support.AnnotationConfigWebApplicationContext</param-value>
    </init-param>
    <init-param>
      <param-name>contextConfigLocation</param-name>
      <param-value>com.example.WebConfig</param-value>
    </init-param>
    <load-on-startup>1</load-on-startup>
  </servlet>
  <servlet-mapping>
    <servlet-name>dispatcher</servlet-name>
    <url-pattern>/</url-pattern>
  </servlet-mapping>
</web-app>
```

**`WebApplicationInitializer` equivalent:**

```java
class AppInit implements WebApplicationInitializer {
    @Override
    public void onStartup(ServletContext sc) {
        // Root context
        var root = new AnnotationConfigWebApplicationContext();
        root.register(RootConfig.class);
        sc.addListener(new ContextLoaderListener(root));

        // Servlet context + DispatcherServlet
        var servlet = new AnnotationConfigWebApplicationContext();
        servlet.register(WebConfig.class);
        var ds = new DispatcherServlet(servlet);
        var reg = sc.addServlet("dispatcher", ds);
        reg.setLoadOnStartup(1);
        reg.addMapping("/");
    }
}
```

The SPI wiring: `META-INF/services/javax.servlet.ServletContainerInitializer` lists `SpringServletContainerInitializer`. The container calls `SpringServletContainerInitializer.onStartup()`, which finds all `WebApplicationInitializer` implementations on the classpath and calls `onStartup(sc)` on each.

## 4. Diagram

<svg viewBox="0 0 700 195" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <marker id="arr" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <polygon points="0 0,8 3,0 6" fill="#6db33f"/>
    </marker>
  </defs>

  <!-- Container -->
  <rect x="10" y="70" width="130" height="55" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="75" y="92" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Servlet Container</text>
  <text x="75" y="106" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">Tomcat / Jetty</text>
  <text x="75" y="118" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">startup</text>

  <!-- web.xml -->
  <line x1="142" y1="90" x2="195" y2="70" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>
  <rect x="197" y="45" width="155" height="55" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="274" y="67" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">web.xml</text>
  <text x="274" y="81" fill="#8b949e" font-size="7" text-anchor="middle" font-family="monospace">ContextLoaderListener</text>
  <text x="274" y="93" fill="#8b949e" font-size="7" text-anchor="middle" font-family="monospace">DispatcherServlet</text>

  <!-- WebApplicationInitializer -->
  <line x1="142" y1="107" x2="195" y2="122" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>
  <rect x="197" y="110" width="155" height="55" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="274" y="132" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">WebApplicationInitializer</text>
  <text x="274" y="146" fill="#8b949e" font-size="7" text-anchor="middle" font-family="monospace">detected via SCI</text>
  <text x="274" y="158" fill="#8b949e" font-size="7" text-anchor="middle" font-family="monospace">onStartup(ServletContext)</text>

  <line x1="354" y1="90" x2="407" y2="97" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>
  <line x1="354" y1="137" x2="407" y2="113" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>

  <!-- Result -->
  <rect x="409" y="65" width="270" height="75" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="544" y="87" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">DispatcherServlet registered</text>
  <line x1="419" y1="93" x2="669" y2="93" stroke="#8b949e" stroke-width="0.5"/>
  <text x="544" y="111" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">Root context (services/repos)</text>
  <text x="544" y="127" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">Servlet context (controllers)</text>
</svg>

## 5. Runnable example

Scenario: a **catalog service** — configure DispatcherServlet three ways.

### Level 1 — Basic

`AbstractAnnotationConfigDispatcherServletInitializer` — minimal boilerplate.

```java
// ServletConfigDemo.java
import org.springframework.context.annotation.*;
import org.springframework.stereotype.Service;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.servlet.config.annotation.*;
import org.springframework.web.servlet.support.AbstractAnnotationConfigDispatcherServletInitializer;
import java.util.*;

// Root context beans
@Service
class CatalogService {
    public List<String> items() { return List.of("Widget","Gadget","Sensor"); }
}
@Configuration @ComponentScan(basePackageClasses=CatalogService.class)
class RootConfig {}

// Servlet context beans
@RestController @RequestMapping("/catalog")
class CatalogController {
    private final CatalogService svc;
    CatalogController(CatalogService s){ svc=s; }
    @GetMapping public List<String> list() { return svc.items(); }
}
@Configuration @EnableWebMvc @ComponentScan(basePackageClasses=CatalogController.class)
class WebConfig {}

// Replaces web.xml entirely
public class ServletConfigDemo
        extends AbstractAnnotationConfigDispatcherServletInitializer {

    @Override protected Class<?>[] getRootConfigClasses()    { return new Class[]{RootConfig.class}; }
    @Override protected Class<?>[] getServletConfigClasses() { return new Class[]{WebConfig.class}; }
    @Override protected String[]   getServletMappings()      { return new String[]{"/"}; }

    public static void main(String[] args) {
        System.out.println("AbstractAnnotationConfigDispatcherServletInitializer:");
        System.out.println("  getRootConfigClasses() → loaded by ContextLoaderListener");
        System.out.println("  getServletConfigClasses() → loaded by DispatcherServlet");
        System.out.println("  getServletMappings() → URL patterns for DispatcherServlet");
        System.out.println("  Detected by SpringServletContainerInitializer at container startup.");
    }
}
```

How to run: `java -cp spring-webmvc.jar:spring-context.jar:spring-web.jar:jackson-databind.jar:jakarta.servlet-api.jar:. ServletConfigDemo.java`

`AbstractAnnotationConfigDispatcherServletInitializer` handles all the boilerplate: creates `AnnotationConfigWebApplicationContext` for root and servlet, registers config classes, sets up `ContextLoaderListener` and `DispatcherServlet`, maps the servlet to `getServletMappings()` patterns.

---

### Level 2 — Intermediate

Add a `Filter` and customise `DispatcherServlet` options.

```java
// ServletConfigDemo.java
import jakarta.servlet.*;
import jakarta.servlet.http.*;
import org.springframework.context.annotation.*;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.filter.CharacterEncodingFilter;
import org.springframework.web.servlet.*;
import org.springframework.web.servlet.config.annotation.*;
import org.springframework.web.servlet.support.AbstractAnnotationConfigDispatcherServletInitializer;

// (RootConfig, CatalogService same as Level 1)

@Configuration @EnableWebMvc @ComponentScan(basePackageClasses=CatalogController.class)
class WebConfig2 {}

class RequestLoggingFilter implements Filter {
    @Override public void doFilter(ServletRequest req, ServletResponse res, FilterChain chain)
            throws Exception {
        System.out.println("[Filter] " + ((HttpServletRequest)req).getMethod()
            + " " + ((HttpServletRequest)req).getRequestURI());
        chain.doFilter(req, res);
    }
}

public class ServletConfigDemo
        extends AbstractAnnotationConfigDispatcherServletInitializer {
    @Override protected Class<?>[] getRootConfigClasses()    { return new Class[]{RootConfig.class}; }
    @Override protected Class<?>[] getServletConfigClasses() { return new Class[]{WebConfig2.class}; }
    @Override protected String[]   getServletMappings()      { return new String[]{"/"}; }

    // Register filters — applied to ALL requests
    @Override protected Filter[] getServletFilters() {
        var encoding = new CharacterEncodingFilter("UTF-8", true);
        return new Filter[]{ encoding, new RequestLoggingFilter() };
    }

    // Customise DispatcherServlet
    @Override protected void customizeRegistration(ServletRegistration.Dynamic reg) {
        reg.setInitParameter("throwExceptionIfNoHandlerFound", "true");
        reg.setAsyncSupported(true);
        reg.setMultipartConfig(new MultipartConfigElement("/tmp", 10 * 1024 * 1024, -1L, 0));
    }

    public static void main(String[] args) {
        System.out.println("Extended AbstractAnnotationConfigDispatcherServletInitializer:");
        System.out.println("  getServletFilters() → CharacterEncodingFilter + RequestLoggingFilter");
        System.out.println("  customizeRegistration() → throwException if no handler, async, multipart");
    }
}
```

How to run: same classpath + deploy

`getServletFilters()` — filters are registered and mapped to `/*` in the same order as returned. `customizeRegistration()` gives access to the raw `ServletRegistration.Dynamic` to set init params, async support, and multipart config. `throwExceptionIfNoHandlerFound=true` makes `DispatcherServlet` throw `NoHandlerFoundException` for unmatched URLs (useful with `@ExceptionHandler`).

---

### Level 3 — Advanced

Raw `WebApplicationInitializer` — maximum control; multiple filters, multi-servlet.

```java
// ServletConfigDemo.java
import jakarta.servlet.*;
import org.springframework.context.annotation.*;
import org.springframework.web.*;
import org.springframework.web.context.*;
import org.springframework.web.context.support.AnnotationConfigWebApplicationContext;
import org.springframework.web.filter.*;
import org.springframework.web.servlet.DispatcherServlet;
import org.springframework.web.servlet.config.annotation.*;
import org.springframework.web.bind.annotation.*;

// (RootConfig, CatalogService same as Level 1)
@Configuration @EnableWebMvc @ComponentScan(basePackageClasses=CatalogController.class)
class WebConfigV1 {}

@RestController @RequestMapping("/v2/catalog")
class CatalogControllerV2 {
    @GetMapping public String list() { return "[{\"name\":\"WidgetV2\"}]"; }
}
@Configuration @EnableWebMvc @ComponentScan(basePackageClasses=CatalogControllerV2.class)
class WebConfigV2 {}

public class ServletConfigDemo implements WebApplicationInitializer {
    @Override
    public void onStartup(ServletContext sc) throws ServletException {
        // Root context
        var root = new AnnotationConfigWebApplicationContext(); root.register(RootConfig.class);
        sc.addListener(new ContextLoaderListener(root));

        // Global filter (before any servlet)
        var encFilter = sc.addFilter("encoding", new CharacterEncodingFilter("UTF-8", true));
        encFilter.addMappingForUrlPatterns(null, false, "/*");

        // API v1 dispatcher
        var v1Ctx = new AnnotationConfigWebApplicationContext(); v1Ctx.register(WebConfigV1.class);
        var v1Reg = sc.addServlet("v1", new DispatcherServlet(v1Ctx));
        v1Reg.setLoadOnStartup(1); v1Reg.addMapping("/v1/*");

        // API v2 dispatcher
        var v2Ctx = new AnnotationConfigWebApplicationContext(); v2Ctx.register(WebConfigV2.class);
        var v2Reg = sc.addServlet("v2", new DispatcherServlet(v2Ctx));
        v2Reg.setLoadOnStartup(2); v2Reg.addMapping("/v2/*");
    }

    public static void main(String[] args) {
        System.out.println("Raw WebApplicationInitializer:");
        System.out.println("  Full control: multiple servlets, filters, listeners");
        System.out.println("  onStartup() called by SpringServletContainerInitializer at container boot");
    }
}
```

How to run: same classpath + deploy

Raw `WebApplicationInitializer.onStartup()` gives complete control: register any number of servlets, filters, and listeners via `ServletContext` API — exactly what `web.xml` could do but in type-safe Java.

## 6. Walkthrough

**Level 1 — container startup sequence:**

1. Tomcat scans WARs for `META-INF/services/jakarta.servlet.ServletContainerInitializer`.
2. Finds `SpringServletContainerInitializer` (Spring ships this file).
3. Tomcat calls `SpringServletContainerInitializer.onStartup(webAppInitializerClasses, sc)`.
4. Spring finds all `WebApplicationInitializer` implementations on classpath → finds `ServletConfigDemo`.
5. `ServletConfigDemo.onStartup(sc)` called (via `AbstractAnnotationConfigDispatcherServletInitializer`).
6. Root context created with `RootConfig.class`, wrapped in `ContextLoaderListener`, registered.
7. `ContextLoaderListener.contextInitialized()` fires → root context refreshed → `CatalogService` bean created.
8. `DispatcherServlet` created with servlet context, mapped to `/`, `loadOnStartup=1`.
9. First request arrives → `DispatcherServlet.init()` → servlet context refreshed → `CatalogController` created, wired with `CatalogService` from root.

## 7. Gotchas & takeaways

> **`web.xml` and `WebApplicationInitializer` can coexist** in the same WAR. The container processes `web.xml` first, then calls `SpringServletContainerInitializer`. Avoid registering the same servlet in both — you'll get two instances.

> **Spring Boot doesn't use either.** Boot embeds the container and calls `onStartup()` programmatically in `TomcatStarter` / `JettyEmbeddedWebAppContext`. No `web.xml` file needed. `WebApplicationInitializer` implementations are NOT picked up in an embedded container unless explicitly registered.

> **`getServletFilters()` in `AbstractAnnotationConfigDispatcherServletInitializer` maps filters to `/*`** by `isAsyncSupported()`. If your filter doesn't support async, set `isAsyncSupported()` to return `false`. Async-incompatible filters on async requests will cause warnings.

- `AbstractAnnotationConfigDispatcherServletInitializer` = simplest; three-method override.
- `WebApplicationInitializer` = raw; full control over servlet, filter, listener registration.
- `web.xml` = legacy; still required for Servlet 2.5 containers.
- `getServletFilters()` — global filter registration; `customizeRegistration()` — `DispatcherServlet` options.
- Spring Boot: no `web.xml` / `WebApplicationInitializer` — embedded container wired by Boot.
