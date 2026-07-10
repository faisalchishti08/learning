---
card: spring-framework
gi: 355
slug: static-resources-handling-resourcehttprequesthandler
title: "Static resources handling (ResourceHttpRequestHandler)"
---

## 1. What it is

`ResourceHttpRequestHandler` is the Spring MVC component that serves static files (CSS, JavaScript, images, downloadable assets) directly from configured locations — the classpath, the filesystem, or a URL — without any controller method involved. You register resource handlers via `WebMvcConfigurer.addResourceHandlers(ResourceHandlerRegistry)`, mapping a URL pattern to one or more physical locations.

```java
@Override
public void addResourceHandlers(ResourceHandlerRegistry registry) {
    registry.addResourceHandler("/static/**")
        .addResourceLocations("classpath:/static/")
        .setCacheControl(CacheControl.maxAge(Duration.ofDays(30)));
}
```

## 2. Why & when

Spring Boot autoconfigures a static resource handler for `/**` pointing at `classpath:/static/`, `classpath:/public/`, and a few other conventional locations — most applications serving simple static assets (a logo, a stylesheet) need zero configuration, just placing files in `src/main/resources/static/`. You need explicit configuration when:

- Serving assets from a **non-default location** — an external filesystem directory (uploaded user content, files outside the packaged JAR), rather than the classpath.
- Applying **specific caching rules** per resource type (long cache lifetimes for versioned/hashed assets, short or no caching for frequently-changing files).
- Restricting which URL patterns map to static resources, to avoid accidentally shadowing API routes with the same prefix.
- Serving resources from **multiple locations** with fallback ordering (check an external override directory first, fall back to bundled defaults).

## 3. Core concept

```
addResourceHandlers(ResourceHandlerRegistry):

  registry.addResourceHandler("/static/**")   <- URL PATTERN clients request
      .addResourceLocations(                   <- PHYSICAL location(s), checked in order
          "classpath:/static/",
          "file:/var/app/uploads/")
      .setCacheControl(...)                    <- HTTP caching headers for matched responses

Request: GET /static/logo.png
      |
      v
ResourceHttpRequestHandler matches "/static/**" pattern
      |
      v
Checks locations IN ORDER: classpath:/static/logo.png exists? -> SERVE IT
                            (file:/var/app/uploads/logo.png never checked, since found already)
      |
      v
Response: raw file bytes, Content-Type inferred from extension,
          Cache-Control header from setCacheControl(...)

This bypasses DispatcherServlet's normal @Controller dispatch
entirely for matched URLs — ResourceHttpRequestHandler IS the handler.
```

## 4. Diagram

<svg viewBox="0 0 720 200" xmlns="http://www.w3.org/2000/svg" font-family="monospace" font-size="12">
  <rect width="720" height="200" fill="#0d1117"/>
  <text x="360" y="22" text-anchor="middle" fill="#8b949e">Resource locations checked in order until a match is found</text>

  <rect x="20" y="50" width="200" height="50" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="120" y="80" text-anchor="middle" fill="#79c0ff" font-size="11">GET /static/logo.png</text>

  <line x1="220" y1="75" x2="280" y2="75" stroke="#8b949e" marker-end="url(#a31)"/>

  <rect x="280" y="50" width="180" height="50" rx="5" fill="#1c2430" stroke="#6db33f"/>
  <text x="370" y="72" text-anchor="middle" fill="#6db33f" font-size="10">classpath:/static/</text>
  <text x="370" y="88" text-anchor="middle" fill="#8b949e" font-size="9">checked FIRST ✓ found</text>

  <rect x="280" y="120" width="180" height="50" rx="5" fill="#1c2430" stroke="#8b949e" stroke-dasharray="3,3"/>
  <text x="370" y="142" text-anchor="middle" fill="#8b949e" font-size="10">file:/var/app/uploads/</text>
  <text x="370" y="158" text-anchor="middle" fill="#8b949e" font-size="9">never checked (already found)</text>

  <line x1="460" y1="75" x2="520" y2="75" stroke="#6db33f" marker-end="url(#a31)"/>
  <rect x="520" y="50" width="160" height="50" rx="5" fill="#1c2430" stroke="#8b949e"/>
  <text x="600" y="80" text-anchor="middle" fill="#e6edf3" font-size="10">200 OK, image bytes</text>

  <defs>
    <marker id="a31" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L0,6 L8,3 z" fill="#8b949e"/>
    </marker>
  </defs>
</svg>

*Multiple resource locations act as an ordered fallback chain — the first location containing the requested file wins.*

## 5. Runnable example

### Level 1 — Basic

Serving CSS/JS from the classpath with a long cache lifetime, no explicit configuration beyond what's typical:

```java
// WebConfig.java
import org.springframework.context.annotation.Configuration;
import org.springframework.http.CacheControl;
import org.springframework.web.servlet.config.annotation.ResourceHandlerRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;

import java.time.Duration;

@Configuration
public class WebConfig implements WebMvcConfigurer {
    @Override
    public void addResourceHandlers(ResourceHandlerRegistry registry) {
        registry.addResourceHandler("/assets/**")
            .addResourceLocations("classpath:/static/assets/")
            .setCacheControl(CacheControl.maxAge(Duration.ofDays(30)));
    }
}
```

Place a file at `src/main/resources/static/assets/style.css`.

**How to run:**
```bash
./mvnw spring-boot:run

curl -i http://localhost:8080/assets/style.css
# HTTP/1.1 200 OK
# Content-Type: text/css
# Cache-Control: max-age=2592000
# (file contents)
```

`ResourceHttpRequestHandler` serves `style.css` directly from the packaged classpath resource — no controller code, no manual `InputStream` handling, and the browser is told to cache it for 30 days via the standard `Cache-Control` header.

### Level 2 — Intermediate

Multiple locations with fallback ordering — an external override directory checked before bundled defaults, useful for allowing runtime asset customization without rebuilding the application:

```java
// WebConfig.java (extended)
import org.springframework.context.annotation.Configuration;
import org.springframework.http.CacheControl;
import org.springframework.web.servlet.config.annotation.ResourceHandlerRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;

import java.time.Duration;

@Configuration
public class WebConfig implements WebMvcConfigurer {
    @Override
    public void addResourceHandlers(ResourceHandlerRegistry registry) {
        registry.addResourceHandler("/assets/**")
            .addResourceLocations(
                "file:/etc/acme-app/custom-assets/",   // checked FIRST — allows ops to override without a rebuild
                "classpath:/static/assets/")            // fallback: bundled defaults
            .setCacheControl(CacheControl.maxAge(Duration.ofDays(30)));

        // User-uploaded content — SEPARATE handler, deliberately NOT cached long-term,
        // since these files can change/be replaced at any time.
        registry.addResourceHandler("/uploads/**")
            .addResourceLocations("file:/var/app/uploads/")
            .setCacheControl(CacheControl.noCache());
    }
}
```

**How to run:**
```bash
mkdir -p /tmp/custom-assets && echo "body { background: red; }" > /tmp/custom-assets/style.css
./mvnw spring-boot:run

curl http://localhost:8080/assets/style.css
# body { background: red; }     <- served from the external override location, NOT the bundled default

curl -i http://localhost:8080/uploads/report.pdf
# Cache-Control: no-cache        <- different caching policy for this separate handler
```

**What changed:** Two independent resource handlers now exist — one for versioned static assets (long cache, multiple fallback locations), one for user-uploaded content (no long-term caching, since files there can change). `addResourceLocations` accepts multiple values checked strictly in the order given, letting an ops team drop an override file into `/etc/acme-app/custom-assets/` and have it take precedence without touching the packaged application at all.

### Level 3 — Advanced

Production concern: preventing a common security mistake (a resource handler pattern accidentally shadowing API routes) and combining static resource serving with the `Default servlet handler` fallback (covered fully in the next card) for correct behavior when running on an external servlet container:

```java
// WebConfig.java (production version)
import org.springframework.context.annotation.Configuration;
import org.springframework.http.CacheControl;
import org.springframework.web.servlet.config.annotation.ResourceHandlerRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;

import java.time.Duration;

@Configuration
public class WebConfig implements WebMvcConfigurer {

    @Override
    public void addResourceHandlers(ResourceHandlerRegistry registry) {
        // SCOPED pattern ("/assets/**"), NOT a catch-all ("/**") — a catch-all pattern here
        // would compete with (and potentially shadow, depending on handler-mapping order)
        // every @RestController route in the application, since it's registered as a
        // very-low-priority but still real HandlerMapping.
        registry.addResourceHandler("/assets/**")
            .addResourceLocations("classpath:/static/assets/")
            .setCacheControl(CacheControl.maxAge(Duration.ofDays(30)).cachePublic());
    }
}
```

```java
// ProductController.java — an API route that must NEVER be shadowed by static resource handling
import org.springframework.web.bind.annotation.*;

@RestController
public class ProductController {
    @GetMapping("/products/{id}")     // completely separate URL space from "/assets/**"
    public String get(@PathVariable long id) { return "Drill"; }
}
```

**How to run:**
```bash
./mvnw spring-boot:run

curl http://localhost:8080/assets/logo.png
# served as a static resource

curl http://localhost:8080/products/1
# Drill    <- correctly routed to the @RestController, unaffected by resource handler config,
#            because "/products/**" was never claimed by any resource handler pattern
```

**What changed and why:**
- Using a **scoped** URL pattern (`/assets/**`) rather than a catch-all (`/**`) for custom resource handlers is a deliberate, security- and correctness-relevant choice — Spring MVC's `HandlerMapping` chain is checked in priority order, and while `RequestMappingHandlerMapping` (backing `@RequestMapping`) normally has higher priority than `SimpleUrlHandlerMapping` (backing resource handlers), an overly broad or misconfigured resource pattern can still create confusing overlaps, especially when combined with the `Default servlet handler` fallback covered next. Scoping resource patterns narrowly avoids the ambiguity entirely.
- `.cachePublic()` explicitly marks the resource as cacheable by shared/intermediate caches (CDNs, reverse proxies), not just the requesting browser — appropriate for genuinely public, non-personalized static assets, but something to omit for any resource containing user-specific or sensitive content.
- Keeping the resource handler's pattern and the API controller's mapping in entirely separate URL namespaces (`/assets/**` vs `/products/**`) is the simplest, most robust way to guarantee no interaction between static resource serving and application routing — avoid a shared prefix between the two unless you have a very specific reason and have verified the interaction carefully.

## 6. Walkthrough

**Request: `GET /assets/logo.png` (Level 3 code).**

1. The request arrives at `DispatcherServlet`, which consults its ordered list of `HandlerMapping` implementations to find something willing to handle `/assets/logo.png`.
2. `RequestMappingHandlerMapping` (backing all `@RequestMapping`-family annotations, including `ProductController.get`) is checked first — no `@GetMapping`/`@RequestMapping` anywhere in the application matches the pattern `/assets/logo.png`, so this mapping declines.
3. `SimpleUrlHandlerMapping` (backing the resource handler registered via `addResourceHandlers`) is checked next — it recognizes `/assets/**` as a pattern it owns, and `/assets/logo.png` matches. It returns a `ResourceHttpRequestHandler` as the resolved handler for this request.
4. `DispatcherServlet` invokes `ResourceHttpRequestHandler.handleRequest(request, response)` directly — this bypasses the normal `@Controller`/argument-resolution/return-value-handling pipeline entirely, since resource serving is a specialized, simpler code path.
5. Inside the handler: it checks its configured `addResourceLocations("classpath:/static/assets/")` — resolves `logo.png` against that classpath location, finds the packaged file.
6. It determines the `Content-Type` from the file extension (`.png` → `image/png`), sets the configured `Cache-Control: max-age=2592000, public` header (from `.maxAge(30 days).cachePublic()`), and streams the file's raw bytes as the response body.
7. Response:
   ```
   HTTP/1.1 200 OK
   Content-Type: image/png
   Cache-Control: max-age=2592000, public

   (binary PNG bytes)
   ```

**Request: `GET /products/1` (same application, a real API route).**

1. `DispatcherServlet` again consults its `HandlerMapping`s in order. This time, `RequestMappingHandlerMapping` is checked first and **does** find a match: `ProductController.get(long id)`, mapped via `@GetMapping("/products/{id}")`.
2. Because a match was found at this higher-priority mapping, `SimpleUrlHandlerMapping` (the resource handler) is never even consulted for this request — the two mappings' URL spaces (`/assets/**` vs `/products/**`) don't overlap anyway, but the priority ordering itself is what guarantees `@RequestMapping`-based routes always get first consideration regardless of any resource handler pattern.
3. The request proceeds through the normal controller dispatch pipeline (argument resolution, handler invocation, return value handling) exactly as described in earlier cards, producing `"Drill"` as a plain-text response body.

## 7. Gotchas & takeaways

> **A resource handler pattern that's too broad (`/**`) is registered as a real, if low-priority, `HandlerMapping`** — while `@RequestMapping`-based routes normally take precedence, an overly broad resource pattern combined with certain default-servlet-handling configurations (the next card) can create confusing edge cases where a URL that "looks like" it should hit a controller instead gets treated as a resource lookup that 404s. Always scope resource handler patterns as narrowly as the application's actual asset layout allows.

> **`ResourceHttpRequestHandler` follows the classpath/filesystem locations exactly as configured, in order — it does not implicitly search subdirectories beyond what the URL pattern's wildcard implies.** A location typo (`classpath:/statc/` instead of `classpath:/static/`) produces a silent `404` for every resource under that handler, not a startup error, since the location is only resolved lazily per-request.

> **Serving user-uploaded or otherwise mutable content through a resource handler with a long `Cache-Control` max-age can cause stale content to be served from browser or CDN caches** long after the underlying file has changed — always use a short or `no-cache` policy (as shown for `/uploads/**` in Level 2) for any location whose contents can change without a corresponding URL change.

- `ResourceHttpRequestHandler` (registered via `addResourceHandlers`) serves static files directly, bypassing normal controller dispatch — Spring Boot autoconfigures sensible defaults for `classpath:/static/` and similar conventional locations.
- Multiple `addResourceLocations` values are checked in order, forming a fallback chain — useful for override directories taking precedence over bundled defaults.
- Scope resource handler URL patterns narrowly to avoid overlap with API routes, even though `@RequestMapping`-based handlers take priority by default.
- Set caching policy deliberately per resource type — long cache lifetimes for versioned/immutable assets, short or none for content that can change independently of its URL.
