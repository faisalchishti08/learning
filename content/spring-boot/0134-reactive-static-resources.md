---
card: spring-boot
gi: 134
slug: reactive-static-resources
title: Reactive static resources
---

## 1. What it is

Spring WebFlux can serve static files (HTML, CSS, JS, images) just like Spring MVC does — without blocking any thread. Spring Boot auto-configures a `RouterFunction`-based static resource handler for WebFlux that serves files from `classpath:/static/`, `classpath:/public/`, `classpath:/resources/`, and `classpath:/META-INF/resources/`. The configuration mirrors the Spring MVC static-resource support but is built on reactive primitives (`Flux<DataBuffer>`, `ResourceWebHandler`).

## 2. Why & when

A WebFlux app still needs to serve HTML, images, JavaScript, or a single-page app's `index.html`. Static resources are served from the classpath (packaged in the JAR) or a filesystem directory.

Use reactive static resources when:

- Your WebFlux app serves a frontend (SPA, admin UI) alongside its API.
- You have a small microservice that also needs a simple HTML status page.
- You want `Cache-Control` headers and `ETag` support for browser caching without a separate CDN or reverse proxy.

For high-traffic frontends, delegate static resource serving to NGINX or a CDN and keep the Spring Boot app for API calls only.

## 3. Core concept

`WebFluxAutoConfiguration` registers a `RouterFunction` that maps `/**` to `ResourceWebHandler`. The handler reads files from the configured locations using `ResourceLoader`, wraps them in a `Flux<DataBuffer>`, and streams the bytes to the client without loading the full file into memory at once.

Default locations (highest to lowest priority):

1. `classpath:/META-INF/resources/`
2. `classpath:/resources/`
3. `classpath:/static/`
4. `classpath:/public/`

Custom locations and URL patterns are configured via `spring.web.resources.static-locations` and `spring.mvc.static-path-pattern` (applies to both MVC and WebFlux).

## 4. Diagram

<svg viewBox="0 0 680 210" xmlns="http://www.w3.org/2000/svg">
  <rect x="20" y="80" width="130" height="60" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="85" y="107" text-anchor="middle" fill="#6db33f" font-size="12" font-family="sans-serif">GET /logo.png</text>
  <rect x="225" y="80" width="175" height="60" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="312" y="107" text-anchor="middle" fill="#79c0ff" font-size="12" font-family="sans-serif">ResourceWebHandler</text>
  <text x="312" y="124" text-anchor="middle" fill="#8b949e" font-size="11" font-family="sans-serif">matches static locations</text>
  <rect x="475" y="60" width="185" height="40" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="562" y="84" text-anchor="middle" fill="#8b949e" font-size="11" font-family="sans-serif">classpath:/static/</text>
  <rect x="475" y="115" width="185" height="40" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="562" y="139" text-anchor="middle" fill="#8b949e" font-size="11" font-family="sans-serif">classpath:/public/</text>
  <line x1="152" y1="110" x2="221" y2="110" stroke="#6db33f" stroke-width="1.5" marker-end="url(#sr)"/>
  <line x1="402" y1="100" x2="471" y2="80" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#sr2)"/>
  <line x1="402" y1="120" x2="471" y2="135" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#sr2)"/>
  <defs>
    <marker id="sr" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="sr2" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>
</svg>

`GET /logo.png` is matched by `ResourceWebHandler`, which looks up the file in configured classpath locations and streams it reactively.

## 5. Runnable example

```java
// StaticResourceApp.java  —  Spring Boot project with spring-boot-starter-webflux
// Place an index.html in src/main/resources/static/
// Place an image at  src/main/resources/static/images/logo.svg

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.core.io.ClassPathResource;
import org.springframework.web.reactive.function.server.RouterFunction;
import org.springframework.web.reactive.function.server.RouterFunctions;
import org.springframework.web.reactive.function.server.ServerResponse;

@SpringBootApplication
public class StaticResourceApp {
    public static void main(String[] args) {
        SpringApplication.run(StaticResourceApp.class, args);
    }
}

@Configuration
class StaticConfig {

    // Serve files from an additional filesystem directory (dev-time assets)
    @Bean
    public RouterFunction<ServerResponse> extraStaticResources() {
        return RouterFunctions.resources(
                "/docs/**",
                new ClassPathResource("docs/")   // classpath:/docs/
        );
    }
}

// src/main/resources/static/index.html (create this file):
// <!DOCTYPE html>
// <html>
// <body><h1>Hello from reactive static resources!</h1></body>
// </html>
```

**How to run:** create `src/main/resources/static/index.html` with the HTML above, start the app, then:
- `curl http://localhost:8080/index.html` — serves the static HTML.
- `curl http://localhost:8080/` — Spring Boot forwards `/` to `index.html` automatically when `spring.web.resources.add-mappings=true` (default).

## 6. Walkthrough

- `WebFluxAutoConfiguration` registers `ResourceWebHandler` for `/**` backed by `classpath:/static/`, `classpath:/public/`, etc. This happens automatically — no bean needed.
- `RouterFunctions.resources("/docs/**", new ClassPathResource("docs/"))` demonstrates adding a custom location. Files in `classpath:/docs/` are served under the `/docs/` URL prefix.
- `ClassPathResource("docs/")` points to `src/main/resources/docs/` in the project. You can also use `new FileSystemResource("/var/www/html/")` for a filesystem path.
- When `index.html` is requested, `ResourceWebHandler` opens it as a `Resource`, reads its bytes reactively as a `Flux<DataBuffer>`, and writes them to the response without materialising the whole file in memory.
- `Cache-Control` and `ETag` support is on by default. Spring computes a fingerprint from the file's last-modified time and adds `ETag` and `Last-Modified` headers. Browsers can cache resources and send conditional requests (`If-None-Match`).
- `spring.web.resources.cache.period=3600s` sets a `Cache-Control: max-age=3600` on all static responses.

## 7. Gotchas & takeaways

> Setting `spring.web.resources.add-mappings=false` disables the auto-configured static resource handler entirely — useful when you want to handle all routes manually, but you lose static file serving.

> Static resource serving in WebFlux shares the Reactor Netty event loop — file reads should be non-blocking. For large files on NIO-capable filesystems this is fine; for network-mounted filesystems or very slow storage, consider offloading with `Schedulers.boundedElastic()`.

- `src/main/resources/static/` in a Maven project is on the classpath, so files there are served by default.
- Use `spring.web.resources.static-locations` to override or add to the default locations list.
- `spring.web.resources.chain.strategy.content.enabled=true` enables content-based URL fingerprinting (adds a hash to the URL for cache-busting).
- WebFlux doesn't support `ResourceHttpRequestHandler` (Spring MVC); the WebFlux equivalent is `ResourceWebHandler`, and the auto-configured `RouterFunction` wraps it.
