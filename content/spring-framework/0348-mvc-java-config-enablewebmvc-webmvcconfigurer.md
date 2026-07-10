---
card: spring-framework
gi: 348
slug: mvc-java-config-enablewebmvc-webmvcconfigurer
title: "MVC Java config (@EnableWebMvc / WebMvcConfigurer)"
---

## 1. What it is

`@EnableWebMvc` activates Spring MVC's full Java-based configuration mode in a plain (non-Boot) Spring application, registering the core infrastructure beans (`RequestMappingHandlerMapping`, `HttpMessageConverters`, etc.) that make `@Controller`/`@RestController` work. `WebMvcConfigurer` is an interface with default (no-op) methods you override to customize that infrastructure — CORS, interceptors, view resolvers, message converters, static resource handling, content negotiation — all in Java, replacing what used to require verbose XML configuration.

```java
@Configuration
public class WebConfig implements WebMvcConfigurer {

    @Override
    public void addInterceptors(InterceptorRegistry registry) {
        registry.addInterceptor(new LoggingInterceptor());
    }

    @Override
    public void addCorsMappings(CorsRegistry registry) {
        registry.addMapping("/api/**").allowedOrigins("https://app.example.com");
    }
}
```

## 2. Why & when

In a **Spring Boot** application, you almost never write `@EnableWebMvc` yourself — Spring Boot's autoconfiguration already activates equivalent MVC infrastructure automatically, and explicitly adding `@EnableWebMvc` actually **disables** that autoconfiguration, forcing you to configure everything Boot would otherwise have set up sensibly by default (a common and confusing mistake for newcomers). In Boot, you implement `WebMvcConfigurer` directly — without `@EnableWebMvc` — to *customize* Boot's autoconfigured MVC setup incrementally, not replace it.

In a **plain Spring MVC** application (no Boot, deployed as a traditional WAR with manual `DispatcherServlet` registration), `@EnableWebMvc` is required to activate MVC's Java-config-based setup at all — this is the pre-Boot way of bootstrapping Spring MVC.

Use `WebMvcConfigurer` overrides for:
- Registering `HandlerInterceptor`s (cross-cutting request/response logic, like the earlier logging/CORS examples).
- Customizing static resource handling (cache headers, resource locations).
- Adding custom `HttpMessageConverter`s or formatters.
- Fine-tuning content negotiation (seen in earlier cards).
- Configuring path matching behavior (trailing slash handling, case sensitivity).

## 3. Core concept

```
Plain Spring MVC (no Boot):
  @EnableWebMvc                     <- REQUIRED, activates MVC infrastructure
  @Configuration
  class WebConfig implements WebMvcConfigurer { ... }
                                        overrides CUSTOMIZE the infrastructure
                                        @EnableWebMvc just activated

Spring Boot application:
  (NO @EnableWebMvc anywhere)        <- Boot's autoconfiguration already
                                          activates equivalent infrastructure
  @Configuration
  class WebConfig implements WebMvcConfigurer { ... }
                                        overrides CUSTOMIZE Boot's
                                        autoconfigured infrastructure

  Adding @EnableWebMvc to a Boot app:
    -> DISABLES WebMvcAutoConfiguration entirely
    -> you must now configure EVERYTHING yourself
    -> classic "why did my static resources / default converters
       / view resolvers stop working" bug report

WebMvcConfigurer methods (a representative subset):
  addInterceptors(InterceptorRegistry)
  addCorsMappings(CorsRegistry)
  configureContentNegotiation(ContentNegotiationConfigurer)
  addResourceHandlers(ResourceHandlerRegistry)
  extendMessageConverters(List<HttpMessageConverter<?>>)
  configurePathMatch(PathMatchConfigurer)
```

## 4. Diagram

<svg viewBox="0 0 740 220" xmlns="http://www.w3.org/2000/svg" font-family="monospace" font-size="12">
  <rect width="740" height="220" fill="#0d1117"/>
  <text x="370" y="22" text-anchor="middle" fill="#8b949e">@EnableWebMvc in plain Spring MVC vs Spring Boot</text>

  <rect x="20" y="50" width="330" height="140" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="185" y="72" text-anchor="middle" fill="#79c0ff">Plain Spring MVC</text>
  <text x="35" y="97" fill="#6db33f" font-size="10">@EnableWebMvc  ← REQUIRED</text>
  <text x="35" y="117" fill="#8b949e" font-size="10">activates handler mapping,</text>
  <text x="35" y="133" fill="#8b949e" font-size="10">converters, view resolution</text>
  <text x="35" y="155" fill="#8b949e" font-size="10">WebMvcConfigurer customizes it</text>

  <rect x="390" y="50" width="330" height="140" rx="5" fill="#1c2430" stroke="#6db33f"/>
  <text x="555" y="72" text-anchor="middle" fill="#6db33f">Spring Boot</text>
  <text x="405" y="97" fill="#e6edf3" font-size="10">NO @EnableWebMvc needed</text>
  <text x="405" y="117" fill="#8b949e" font-size="10">WebMvcAutoConfiguration already</text>
  <text x="405" y="133" fill="#8b949e" font-size="10">activates sensible defaults</text>
  <text x="405" y="155" fill="#8b949e" font-size="10">WebMvcConfigurer customizes THAT</text>
  <text x="405" y="175" fill="#e6edf3" font-size="9">(adding @EnableWebMvc here DISABLES autoconfig!)</text>

  <defs>
    <marker id="a24" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L0,6 L8,3 z" fill="#8b949e"/>
    </marker>
  </defs>
</svg>

*In Spring Boot, `WebMvcConfigurer` customizes autoconfigured infrastructure; `@EnableWebMvc` would replace, not extend, it.*

## 5. Runnable example

### Level 1 — Basic

A Spring Boot application customizing MVC behavior via `WebMvcConfigurer`, with no `@EnableWebMvc`:

```java
// WebConfig.java
import org.springframework.context.annotation.Configuration;
import org.springframework.web.servlet.config.annotation.CorsRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;

@Configuration
public class WebConfig implements WebMvcConfigurer {

    @Override
    public void addCorsMappings(CorsRegistry registry) {
        registry.addMapping("/api/**")
            .allowedOrigins("http://localhost:3000")
            .allowedMethods("GET", "POST");
    }
}
```

```java
// ProductController.java
import org.springframework.web.bind.annotation.*;

@RestController
public class ProductController {
    @GetMapping("/api/products")
    public String list() { return "[]"; }
}
```

**How to run:**
```bash
./mvnw spring-boot:run

curl -i -H "Origin: http://localhost:3000" http://localhost:8080/api/products
# Access-Control-Allow-Origin: http://localhost:3000

curl http://localhost:8080/api/products
# []                      <- Boot's autoconfigured JSON converter still works fine,
#                            because we never disabled WebMvcAutoConfiguration
```

`WebConfig` only overrides `addCorsMappings` — every other piece of MVC infrastructure (message converters, view resolvers, static resource handling) continues to come from Spring Boot's `WebMvcAutoConfiguration`, untouched.

### Level 2 — Intermediate

Multiple `WebMvcConfigurer` overrides working together — interceptor registration, static resource caching, and path matching — still with no `@EnableWebMvc`:

```java
// LoggingInterceptor.java
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.web.servlet.HandlerInterceptor;

public class LoggingInterceptor implements HandlerInterceptor {
    private static final Logger log = LoggerFactory.getLogger(LoggingInterceptor.class);

    @Override
    public boolean preHandle(HttpServletRequest request, HttpServletResponse response, Object handler) {
        log.info("{} {}", request.getMethod(), request.getRequestURI());
        return true;   // continue processing
    }
}
```

```java
// WebConfig.java (extended)
import org.springframework.context.annotation.Configuration;
import org.springframework.web.servlet.config.annotation.*;

import java.time.Duration;

@Configuration
public class WebConfig implements WebMvcConfigurer {

    @Override
    public void addInterceptors(InterceptorRegistry registry) {
        registry.addInterceptor(new LoggingInterceptor()).addPathPatterns("/api/**");
    }

    @Override
    public void addResourceHandlers(ResourceHandlerRegistry registry) {
        registry.addResourceHandler("/static/**")
            .addResourceLocations("classpath:/static/")
            .setCacheControl(org.springframework.http.CacheControl.maxAge(Duration.ofDays(30)));
    }

    @Override
    public void configurePathMatch(PathMatchConfigurer configurer) {
        configurer.setUseTrailingSlashMatch(false);   // "/products/" and "/products" treated as DIFFERENT
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run

curl http://localhost:8080/api/products
# server log: "GET /api/products"   <- interceptor fired

curl -i http://localhost:8080/static/logo.png
# Cache-Control: max-age=2592000

curl -i http://localhost:8080/products/
# 404 Not Found     <- trailing slash no longer auto-matches, since setUseTrailingSlashMatch(false)
```

**What changed:** Three independent `WebMvcConfigurer` overrides layer on top of each other and on top of Boot's defaults — none of them required disabling or replacing the framework's baseline behavior. Every override is additive/customizing, which is exactly the intended usage pattern in a Boot application.

### Level 3 — Advanced

The plain (non-Boot) Spring MVC scenario where `@EnableWebMvc` is genuinely required, alongside the common "accidentally added `@EnableWebMvc` to a Boot app" failure mode shown explicitly so it's recognizable when encountered:

```java
// AppConfig.java — a PLAIN Spring MVC app (WAR deployment, NO Spring Boot)
import org.springframework.context.annotation.ComponentScan;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.servlet.config.annotation.EnableWebMvc;
import org.springframework.web.servlet.config.annotation.ViewResolverRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;

@Configuration
@EnableWebMvc                    // REQUIRED here — this app has no Spring Boot autoconfiguration at all
@ComponentScan(basePackages = "com.example.app")
public class AppConfig implements WebMvcConfigurer {

    @Override
    public void configureViewResolvers(ViewResolverRegistry registry) {
        registry.jsp("/WEB-INF/jsp/", ".jsp");   // must be configured explicitly — nothing autoconfigured
    }
}
```

```java
// WebAppInitializer.java — replaces web.xml, registers DispatcherServlet manually
import org.springframework.web.servlet.support.AbstractAnnotationConfigDispatcherServletInitializer;

public class WebAppInitializer extends AbstractAnnotationConfigDispatcherServletInitializer {
    @Override
    protected Class<?>[] getRootConfigClasses() { return null; }

    @Override
    protected Class<?>[] getServletConfigClasses() { return new Class[]{ AppConfig.class }; }

    @Override
    protected String[] getServletMappings() { return new String[]{ "/" }; }
}
```

```java
// --- CONTRAST: the mistake, shown explicitly, NOT to be copied into a real Boot app ---
// A Spring Boot application's main config, incorrectly adding @EnableWebMvc:
//
// @SpringBootApplication
// @EnableWebMvc                 // MISTAKE: disables WebMvcAutoConfiguration entirely!
// public class DemoApplication { ... }
//
// Symptom: static resources under /static or /public stop being served,
// default Jackson message converter disappears unless manually re-registered,
// default error page handling changes — a cascade of "it worked before I added this" bugs.
```

**How to run (the correct, plain Spring MVC WAR setup):**
```bash
mvn clean package
# deploy target/app.war to an external Tomcat

curl http://localhost:8080/app/products/1
# renders /WEB-INF/jsp/product-detail.jsp — because we explicitly configured
# JSP view resolution ourselves; nothing here is autoconfigured
```

**What changed and why:**
- This is a genuinely different deployment model — no `spring-boot-starter-*` dependencies, no autoconfiguration, no embedded server. `@EnableWebMvc` here does real, necessary work: it's what turns on `RequestMappingHandlerMapping` and friends at all.
- `configureViewResolvers` had to be written explicitly — in a Boot app, an equivalent setup happens automatically via `spring.mvc.view.prefix`/`suffix` properties (see the JSP card) with no `WebMvcConfigurer` override needed.
- The commented-out "mistake" block demonstrates the single most common `@EnableWebMvc`-related bug report: someone copies boilerplate from an older, pre-Boot tutorial into a Spring Boot project, and Boot's carefully tuned autoconfiguration silently switches off.

## 6. Walkthrough

**Startup: Spring Boot application WITHOUT `@EnableWebMvc` (Level 1/2 code).**

1. `@SpringBootApplication` triggers Spring Boot's autoconfiguration mechanism, which scans for conditions under which `WebMvcAutoConfiguration` should activate — finding `spring-webmvc` and a servlet environment on the classpath, it activates, registering `RequestMappingHandlerMapping`, default `HttpMessageConverter`s (including Jackson's JSON converter), a default `ViewResolver` chain, static resource handlers for `/static`, `/public`, etc.
2. Any `@Configuration` class implementing `WebMvcConfigurer` (here, `WebConfig`) is detected by Spring's component scanning. Because `WebMvcAutoConfiguration` is specifically designed to **delegate** certain configuration steps to any `WebMvcConfigurer` beans it finds (via `DelegatingWebMvcConfiguration`, which Boot's autoconfiguration composes with), `WebConfig.addCorsMappings(...)` and `addInterceptors(...)` are invoked during this same startup sequence, layering their customizations on top of the autoconfigured baseline.
3. Application starts fully configured: default JSON serialization still works (from autoconfiguration, untouched), CORS is now configured for `/api/**` (from the override), the logging interceptor is registered for `/api/**` (from the override).

**Startup: Plain Spring MVC WAR WITH `@EnableWebMvc` (Level 3 code).**

1. The servlet container loads `WebAppInitializer`, which programmatically registers `DispatcherServlet`, configured with `AppConfig` as its servlet-level Spring configuration — this replaces the legacy `web.xml` + `dispatcher-servlet.xml` bootstrap entirely.
2. `AppConfig` is processed. `@EnableWebMvc` imports `DelegatingWebMvcConfiguration`, which registers the full baseline MVC infrastructure — `RequestMappingHandlerMapping`, message converters, argument resolvers — from scratch, since there is no autoconfiguration doing this implicitly in a non-Boot application.
3. Because `AppConfig` also `implements WebMvcConfigurer`, its own `configureViewResolvers` override is picked up by the same delegation mechanism `@EnableWebMvc` sets up, registering the JSP-based view resolver explicitly (no equivalent autoconfigured default exists to fall back on here).
4. A request for `/products/1` is dispatched to a matching `@Controller` method, which returns a view name resolved via the explicitly configured JSP resolver — rendering succeeds only because every piece of this pipeline was explicitly wired, either by `@EnableWebMvc`'s baseline or by the `WebMvcConfigurer` overrides.

## 7. Gotchas & takeaways

> **Adding `@EnableWebMvc` to a Spring Boot application disables `WebMvcAutoConfiguration` entirely** — this is arguably the single most common Spring MVC configuration mistake among developers transitioning from pre-Boot tutorials or documentation. The fix is simply to remove `@EnableWebMvc` and implement `WebMvcConfigurer` directly; Boot's autoconfiguration already does everything `@EnableWebMvc` would, tuned with sensible defaults.

> **`WebMvcConfigurer` methods are *additive* customization hooks, not replacements** — implementing `addInterceptors` doesn't remove any other autoconfigured behavior, it only adds your interceptor(s) to whatever chain already exists. This additive nature is precisely what makes it safe to use in a Boot application without the `@EnableWebMvc` disabling side effect.

> **If you see Spring Boot autoconfiguration behaving unexpectedly (static resources stop being served, JSON responses stop working, error pages look different), check for a stray `@EnableWebMvc` annotation first** — it's a fast, common diagnosis for a whole class of "everything about MVC suddenly changed" bug reports.

- `@EnableWebMvc` activates Spring MVC's Java-config infrastructure from scratch — required in plain (non-Boot) Spring MVC, and actively harmful in a Spring Boot application.
- `WebMvcConfigurer` is the customization interface either way — in Boot, its overrides layer on top of autoconfiguration; in plain Spring MVC, they layer on top of what `@EnableWebMvc` establishes.
- When debugging unexpected MVC behavior in a Boot application, check for an accidental `@EnableWebMvc` before anything else.
- Prefer configuring Boot's autoconfigured MVC via `WebMvcConfigurer` overrides and `application.properties`/`.yml` settings rather than reaching for `@EnableWebMvc`-era, pre-Boot configuration patterns.
