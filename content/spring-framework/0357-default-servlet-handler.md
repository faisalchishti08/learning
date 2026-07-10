---
card: spring-framework
gi: 357
slug: default-servlet-handler
title: "Default servlet handler"
---

## 1. What it is

`configureDefaultServletHandling` is a `WebMvcConfigurer` override that registers a `DefaultServletHttpRequestHandler`, which forwards any request `DispatcherServlet` can't match to any other handler (no `@RequestMapping`, no resource handler, no view controller) back to the servlet container's own built-in "default servlet" — the one that would have handled all static content if Spring MVC's `DispatcherServlet` weren't mapped to `/`.

```java
@Override
public void configureDefaultServletHandling(DefaultServletHandlerConfigurer configurer) {
    configurer.enable();
}
```

## 2. Why & when

This matters specifically when `DispatcherServlet` is mapped to `/` (the root path, catching *every* request) in a traditional WAR deployment on an external servlet container (Tomcat, WebLogic, etc.) — a common configuration for legacy or non-Boot Spring MVC applications. In that setup, if a request doesn't match any Spring-registered handler (controller, resource handler, view controller), Spring MVC would otherwise return a `404` itself, even for a file that genuinely exists in the WAR's static content directory but wasn't explicitly registered via `addResourceHandlers`.

Enabling the default servlet handler creates a safety-net fallback: unmatched requests are forwarded to the container's native static-file-serving mechanism instead of failing outright. This is largely a **legacy, non-Boot concern** — Spring Boot's embedded server model and autoconfigured resource handling make this fallback unnecessary in the vast majority of modern applications, since Boot already wires up sensible static resource handling and doesn't have a separate "container default servlet" to fall back to in the same way.

## 3. Core concept

```
DispatcherServlet mapped to "/" (catches EVERYTHING):

  Request for /images/photo.jpg
        |
        v
  DispatcherServlet checks its HandlerMapping chain:
    RequestMappingHandlerMapping   -> no @RequestMapping matches
    SimpleUrlHandlerMapping (resources) -> no addResourceHandlers pattern matches
        |
        v
  WITHOUT default servlet handling enabled:
    -> 404, even though /images/photo.jpg might genuinely
       exist as a static file the container COULD serve

  WITH configureDefaultServletHandling().enable():
    a DefaultServletHttpRequestHandler is registered as the
    LOWEST-PRIORITY handler in the chain — if NOTHING else matches,
    it forwards the request to the CONTAINER's own default servlet
    (e.g. Tomcat's "default" servlet, which serves from the WAR's
    document root using RequestDispatcher.forward)
```

## 4. Diagram

<svg viewBox="0 0 720 210" xmlns="http://www.w3.org/2000/svg" font-family="monospace" font-size="12">
  <rect width="720" height="210" fill="#0d1117"/>
  <text x="360" y="22" text-anchor="middle" fill="#8b949e">Fallback chain when DispatcherServlet owns the root path "/"</text>

  <rect x="20" y="50" width="200" height="40" rx="4" fill="#1c2430" stroke="#6db33f"/>
  <text x="120" y="75" text-anchor="middle" fill="#6db33f" font-size="10">1. RequestMappingHandlerMapping</text>

  <rect x="20" y="95" width="200" height="40" rx="4" fill="#1c2430" stroke="#79c0ff"/>
  <text x="120" y="120" text-anchor="middle" fill="#79c0ff" font-size="10">2. Resource handlers</text>

  <rect x="20" y="140" width="200" height="40" rx="4" fill="#1c2430" stroke="#e6edf3" stroke-dasharray="3,3"/>
  <text x="120" y="165" text-anchor="middle" fill="#e6edf3" font-size="10">3. DefaultServletHttpRequestHandler</text>

  <line x1="220" y1="160" x2="300" y2="160" stroke="#8b949e" marker-end="url(#a33)"/>

  <rect x="300" y="140" width="380" height="40" rx="4" fill="#1c2430" stroke="#8b949e"/>
  <text x="490" y="165" text-anchor="middle" fill="#8b949e" font-size="10">forwarded to the servlet container's OWN default servlet</text>

  <text x="360" y="30" fill="none"/>
  <text x="120" y="200" text-anchor="middle" fill="#8b949e" font-size="9">checked in priority order — only reached if 1 and 2 both decline</text>

  <defs>
    <marker id="a33" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L0,6 L8,3 z" fill="#8b949e"/>
    </marker>
  </defs>
</svg>

*The default servlet handler is the last-resort fallback, checked only after every Spring-registered handler has declined.*

## 5. Runnable example

### Level 1 — Basic

A traditional WAR deployment (non-Boot) with `DispatcherServlet` mapped to `/`, enabling the fallback so files under the WAR's `webapp` root remain reachable:

```java
// WebConfig.java
import org.springframework.context.annotation.ComponentScan;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.servlet.config.annotation.DefaultServletHandlerConfigurer;
import org.springframework.web.servlet.config.annotation.EnableWebMvc;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;

@Configuration
@EnableWebMvc
@ComponentScan(basePackages = "com.example.app")
public class WebConfig implements WebMvcConfigurer {
    @Override
    public void configureDefaultServletHandling(DefaultServletHandlerConfigurer configurer) {
        configurer.enable();
    }
}
```

```java
// WebAppInitializer.java
import org.springframework.web.servlet.support.AbstractAnnotationConfigDispatcherServletInitializer;

public class WebAppInitializer extends AbstractAnnotationConfigDispatcherServletInitializer {
    @Override protected Class<?>[] getRootConfigClasses() { return null; }
    @Override protected Class<?>[] getServletConfigClasses() { return new Class[]{ WebConfig.class }; }
    @Override protected String[] getServletMappings() { return new String[]{ "/" }; }   // catches EVERYTHING
}
```

Place a static file at `src/main/webapp/downloads/manual.pdf` (outside any Spring-registered resource handler pattern).

**How to run:**
```bash
mvn clean package
# deploy target/app.war to Tomcat

curl -i http://localhost:8080/app/downloads/manual.pdf
# HTTP/1.1 200 OK          <- served via the CONTAINER's default servlet, not Spring MVC at all
# Content-Type: application/pdf
```

Without `configureDefaultServletHandling().enable()`, this exact request would return `404` from `DispatcherServlet` itself — no handler mapping claims `/downloads/manual.pdf`, and there's no fallback to the container's own static-file-serving capability.

### Level 2 — Intermediate

Contrasting behavior with and without the fallback enabled, demonstrating exactly what breaks:

```java
// WebConfig.java (two variants for comparison)

// VARIANT A: fallback DISABLED (or configureDefaultServletHandling never overridden)
@Configuration
@EnableWebMvc
class WebConfigNoFallback implements WebMvcConfigurer {
    // configureDefaultServletHandling NOT overridden — default is a no-op, fallback stays off
}

// VARIANT B: fallback ENABLED
@Configuration
@EnableWebMvc
class WebConfigWithFallback implements WebMvcConfigurer {
    @Override
    public void configureDefaultServletHandling(DefaultServletHandlerConfigurer configurer) {
        configurer.enable();
    }
}
```

**How to run (conceptual — deploy each variant separately to compare):**
```bash
# VARIANT A deployed:
curl -i http://localhost:8080/app/downloads/manual.pdf
# HTTP/1.1 404 Not Found     <- DispatcherServlet itself returns 404, container never gets a chance

# VARIANT B deployed:
curl -i http://localhost:8080/app/downloads/manual.pdf
# HTTP/1.1 200 OK            <- forwarded to and served by the container's default servlet
```

**What changed:** The only difference between the two variants is whether `configureDefaultServletHandling` registers the fallback handler. This single toggle is the entire difference between "any file not explicitly known to Spring MVC is unreachable" and "unmatched requests get one more chance via the container's native static file serving."

### Level 3 — Advanced

Production concern: understanding this configuration is essentially unnecessary in Spring Boot (embedded server model), and correctly diagnosing when a "why is my static file 404ing" issue is actually this missing configuration versus a Spring Boot-specific resource handler misconfiguration — since the fix differs completely depending on which deployment model is in play:

```java
// --- Traditional WAR / external container (the ONLY scenario where this card's config matters) ---
// WebConfig.java
import org.springframework.context.annotation.ComponentScan;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.servlet.config.annotation.*;

@Configuration
@EnableWebMvc
@ComponentScan(basePackages = "com.example.app")
public class WebConfig implements WebMvcConfigurer {

    @Override
    public void configureDefaultServletHandling(DefaultServletHandlerConfigurer configurer) {
        configurer.enable();
    }

    // Even WITH the default-servlet fallback enabled, it's still best practice to
    // explicitly register resource handlers for KNOWN asset directories — the fallback
    // is a safety net for edge cases, not a replacement for deliberate configuration.
    @Override
    public void addResourceHandlers(ResourceHandlerRegistry registry) {
        registry.addResourceHandler("/assets/**").addResourceLocations("/assets/");
    }
}

// --- Spring Boot / embedded server (this card's configuration is IRRELEVANT here) ---
// No configureDefaultServletHandling override needed or meaningful — Boot's embedded
// Tomcat/Jetty/Undertow has no separate "container default servlet" in the same sense,
// and WebMvcAutoConfiguration already wires up static resource handling for
// classpath:/static/, classpath:/public/, etc. If a static file 404s in a Boot app,
// the fix is almost always addResourceHandlers or verifying the file's classpath location —
// NOT configureDefaultServletHandling, which has no meaningful effect in this deployment model.
```

**How to run:**
```bash
# Traditional WAR deployment:
curl http://localhost:8080/app/legacy-file.txt
# 200 OK — served via the enabled default-servlet fallback

# Spring Boot embedded deployment — the CORRECT fix for an equivalent missing-file problem
# is verifying classpath:/static/ contents or addResourceHandlers, NOT this configuration:
curl http://localhost:8080/legacy-file.txt
# 404 — because classpath:/static/legacy-file.txt doesn't exist; adding
# configureDefaultServletHandling here would have NO effect on this outcome
```

**What changed and why:**
- The WAR-deployment `WebConfig` demonstrates the historically correct pairing: default-servlet fallback enabled as a safety net, *plus* explicit resource handlers for deliberately-organized asset directories — the fallback catches genuinely unanticipated static files, while explicit resource handlers give predictable, cache-controlled behavior for known assets.
- The Boot-deployment comment block exists specifically to prevent a real-world debugging mistake: encountering a `404` for a static file in a Spring Boot application and reaching for `configureDefaultServletHandling` (because that's the answer for a *different* deployment model) instead of the actually-relevant fix (`addResourceHandlers`, or simply placing the file under `src/main/resources/static/`).
- This distinction is exactly why understanding *which* deployment model an application uses is the first diagnostic step before touching any static-resource-related configuration.

## 6. Walkthrough

**Request: `GET /app/downloads/manual.pdf` (Level 1/3 WAR deployment, fallback enabled).**

1. The servlet container (Tomcat) receives the request. Because `DispatcherServlet` is mapped to `/` (from `getServletMappings()` returning `["/"]`), the container routes the request to `DispatcherServlet` first, rather than directly to its own default servlet.
2. `DispatcherServlet` consults its `HandlerMapping` chain in priority order. `RequestMappingHandlerMapping` is checked — no `@RequestMapping`/`@GetMapping` anywhere matches `/downloads/manual.pdf`, so it declines.
3. `SimpleUrlHandlerMapping` (backing any `addResourceHandlers` registrations) is checked next — in this configuration, only `/assets/**` was explicitly registered, and `/downloads/manual.pdf` doesn't match that pattern, so it also declines.
4. The lowest-priority mapping — the one registered by `configureDefaultServletHandling().enable()` — is checked last. It's configured to match essentially any remaining unmatched request, so it claims this one, resolving to a `DefaultServletHttpRequestHandler`.
5. `DefaultServletHttpRequestHandler.handleRequest(request, response)` executes: it performs a `RequestDispatcher.forward(request, response)` internally, redirecting request handling to the servlet container's own registered "default" servlet (in Tomcat, this is literally a servlet named `"default"` that serves static files from the WAR's document root by convention).
6. Tomcat's default servlet locates `manual.pdf` under the WAR's `webapp/downloads/` directory (the same physical location the file was placed in the project source, now packaged into the deployed WAR), reads its bytes, and writes the response — entirely outside Spring MVC's own code path from this point forward.
7. Response:
   ```
   HTTP/1.1 200 OK
   Content-Type: application/pdf

   (binary PDF bytes, served by Tomcat's own static file mechanism)
   ```

**Same request in a Spring Boot embedded deployment (no equivalent "container default servlet" concept applies) — contrast:**

1. The embedded server (say, embedded Tomcat) still routes to `DispatcherServlet` for the request. `RequestMappingHandlerMapping` declines (same reasoning). Boot's autoconfigured `SimpleUrlHandlerMapping` for `classpath:/static/**` (and similar conventional locations) is checked — if `manual.pdf` isn't present under any of those classpath locations, it also declines.
2. There is no third, "container default servlet" fallback layer in the same sense here — the embedded server doesn't have a separately-addressable static-file-serving servlet the way an external Tomcat instance configured for WAR deployment does; static resource serving in Boot is *entirely* mediated through Spring MVC's own resource handler mechanism.
3. With no handler claiming the request, `DispatcherServlet` returns `404` directly — the fix in this deployment model is ensuring the file is placed under a classpath location Boot's autoconfiguration (or an explicit `addResourceHandlers` registration) actually covers, not enabling `configureDefaultServletHandling`.

## 7. Gotchas & takeaways

> **`configureDefaultServletHandling` has little to no practical effect in a standard Spring Boot application** using the embedded server model — this is purely a WAR-deployment-on-external-container concern. Applying this card's guidance to a Boot application's static-file `404` is the wrong diagnostic path; look at `addResourceHandlers` and the file's actual classpath location instead.

> **Enabling the default servlet fallback in a WAR deployment can inadvertently expose files you didn't intend to serve** — anything under the WAR's static document root becomes reachable via the fallback, not just deliberately organized asset directories. Combine it with careful WAR packaging (don't include files you don't want served) rather than relying on it as an access-control mechanism.

> **The fallback only activates for requests that fail to match EVERY higher-priority `HandlerMapping` first** — if you're debugging why a request unexpectedly reaches the default servlet instead of your intended controller, check for a typo or overly narrow pattern in the relevant `@RequestMapping`/resource handler registration before assuming the fallback itself is misbehaving.

- `configureDefaultServletHandling().enable()` registers a lowest-priority fallback that forwards unmatched requests to the servlet container's own native static-file-serving mechanism.
- This is relevant almost exclusively to traditional WAR deployments on an external servlet container with `DispatcherServlet` mapped to `/` — it's largely irrelevant to Spring Boot's embedded-server model.
- In Spring Boot, diagnose static-file `404`s via `addResourceHandlers` and classpath resource locations, not this configuration.
- The fallback is a safety net, not a replacement for deliberately configured, cache-controlled resource handlers for known asset directories.
