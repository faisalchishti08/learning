---
card: spring-boot
gi: 107
slug: static-content-serving
title: Static content serving
---

## 1. What it is

Spring Boot automatically serves static files (HTML, CSS, JavaScript, images, fonts) from four classpath locations, checked in this order:

```
/META-INF/resources/
/resources/
/public/
/static/          ← most commonly used
```

A file at `src/main/resources/static/css/style.css` is served at `http://localhost:8080/css/style.css` — no controller, no configuration needed. Any file in any of the four locations is directly accessible at a URL path matching its location within that directory.

Spring Boot also supports serving from a custom filesystem path using `spring.web.resources.static-locations`.

## 2. Why & when

Static resource serving is how you deliver the front-end assets of a server-rendered web application or a single-page application (SPA) whose JavaScript bundle is bundled into the JAR at build time.

Use built-in static resource serving when:
- You have a Thymeleaf/FreeMarker server-rendered app and need to serve CSS, images, and JS alongside templates.
- You build a React/Vue/Angular SPA and output the bundle into `src/main/resources/static/` during the Maven/Gradle build.
- You serve a `favicon.ico` or `robots.txt`.

Do not use it when:
- Files change frequently and you want to serve from disk without rebuilding the JAR (use `spring.web.resources.static-locations=file:/var/www/static/`).
- You need CDN-level caching, range requests, or content negotiation — put a CDN in front.

## 3. Core concept

Spring Boot registers a `ResourceHttpRequestHandler` mapped to `/**` (after your controllers) via `WebMvcAutoConfiguration.addResourceHandlers()`.

Key configuration properties:
```properties
# Add more source directories
spring.web.resources.static-locations=classpath:/static/,classpath:/public/,file:/opt/myapp/static/

# Enable HTTP cache headers (fingerprinted resources)
spring.web.resources.cache.period=3600          # seconds
spring.web.resources.cache.use-last-modified=true

# Enable the resource chain (adds versioning/gzip)
spring.web.resources.chain.enabled=true
spring.web.resources.chain.strategy.content.enabled=true
spring.web.resources.chain.strategy.content.paths=/**

# Override the handler mapping path (default /**)
spring.mvc.static-path-pattern=/assets/**
```

The `content` strategy appends a content hash to resource URLs (`/css/style-a1b2c3d4.css`), enabling far-future caching. The `Thymeleaf` integration's `@{/css/style.css}` URL expression resolves the versioned URL automatically.

## 4. Diagram

<svg viewBox="0 0 680 260" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Static resource serving: request for /css/style.css goes through DispatcherServlet, no controller matches, ResourceHttpRequestHandler serves the file from /static/">
  <rect x="8" y="8" width="664" height="244" rx="12" fill="#161b22" stroke="#30363d" stroke-width="1"/>
  <text x="340" y="33" fill="#e6edf3" font-size="14" text-anchor="middle" font-family="sans-serif" font-weight="bold">Static Resource Serving Path</text>

  <!-- HTTP request -->
  <rect x="20" y="55" width="140" height="36" rx="5" fill="#1c2430" stroke="#f0883e" stroke-width="1.5"/>
  <text x="90" y="69" fill="#f0883e" font-size="9" text-anchor="middle" font-family="monospace">GET /css/style.css</text>
  <text x="90" y="83" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">browser request</text>

  <defs><marker id="sc" markerWidth="7" markerHeight="7" refX="5" refY="3" orient="auto"><path d="M0,0 L5,3 L0,6 Z" fill="#8b949e"/></marker></defs>
  <line x1="162" y1="73" x2="190" y2="73" stroke="#8b949e" stroke-width="1.5" marker-end="url(#sc)"/>

  <!-- DispatcherServlet -->
  <rect x="192" y="55" width="150" height="36" rx="5" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="267" y="69" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">DispatcherServlet</text>
  <text x="267" y="83" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">checks handler mappings</text>

  <line x1="344" y1="73" x2="370" y2="73" stroke="#8b949e" stroke-width="1.5" marker-end="url(#sc)"/>

  <!-- Controller lookup (miss) -->
  <rect x="372" y="45" width="130" height="36" rx="5" fill="#1c2430" stroke="#f85149" stroke-width="1"/>
  <text x="437" y="59" fill="#f85149" font-size="9" text-anchor="middle" font-family="sans-serif">@Controllers</text>
  <text x="437" y="73" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">no match for /css/*</text>

  <line x1="437" y1="82" x2="437" y2="100" stroke="#8b949e" stroke-width="1" stroke-dasharray="3 2" marker-end="url(#sc)"/>

  <!-- Resource handler -->
  <rect x="372" y="103" width="130" height="36" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="437" y="117" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">ResourceHttpRequestHandler</text>
  <text x="437" y="131" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">mapped to /**</text>

  <line x1="437" y1="140" x2="437" y2="160" stroke="#8b949e" stroke-width="1.5" marker-end="url(#sc)"/>

  <!-- Classpath locations -->
  <rect x="280" y="163" width="320" height="60" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="440" y="180" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">Classpath search order</text>
  <text x="440" y="194" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="monospace">/META-INF/resources/ → /resources/ → /public/ → /static/</text>
  <text x="440" y="208" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">finds static/css/style.css → serves with Cache-Control headers</text>

  <!-- Default locations box -->
  <rect x="20" y="163" width="250" height="68" rx="6" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="145" y="180" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif" font-weight="bold">src/main/resources layout</text>
  <text x="35"  y="196" fill="#e6edf3" font-size="8" font-family="monospace">├── static/</text>
  <text x="35"  y="209" fill="#e6edf3" font-size="8" font-family="monospace">│   ├── css/style.css  ← served at /css/style.css</text>
  <text x="35"  y="222" fill="#e6edf3" font-size="8" font-family="monospace">│   └── js/app.js      ← served at /js/app.js</text>
</svg>

`ResourceHttpRequestHandler` is tried last; it finds files in `/static` and serves them directly.

## 5. Runnable example

```java
// StaticContentServing.java — run: java StaticContentServing.java  (JDK 17+)
// Simulates how Spring Boot's resource handler selects and serves a static file.

import java.util.*;

public class StaticContentServing {

    // Simulated classpath resource locations (in search order)
    static final List<String> LOCATIONS = List.of(
        "/META-INF/resources",
        "/resources",
        "/public",
        "/static"
    );

    // Simulated files on classpath
    static final Set<String> CLASSPATH_FILES = Set.of(
        "/static/css/style.css",
        "/static/js/app.js",
        "/static/index.html",
        "/static/favicon.ico",
        "/public/robots.txt",
        "/META-INF/resources/webjars/jquery/3.7.1/jquery.min.js"
    );

    static Optional<String> findResource(String requestPath) {
        for (String location : LOCATIONS) {
            String candidate = location + requestPath;
            if (CLASSPATH_FILES.contains(candidate)) return Optional.of(candidate);
        }
        return Optional.empty();
    }

    static void serveRequest(String requestPath, boolean hasController) {
        System.out.printf("GET %s%n", requestPath);
        if (hasController) {
            System.out.println("  → @Controller matched → handled by controller");
            return;
        }
        System.out.println("  → no @Controller match → ResourceHttpRequestHandler");
        Optional<String> resource = findResource(requestPath);
        if (resource.isPresent()) {
            System.out.println("  → found: " + resource.get());
            System.out.println("  → response: 200 OK, Cache-Control: max-age=0");
        } else {
            System.out.println("  → not found → 404 Not Found");
        }
        System.out.println();
    }

    public static void main(String[] args) {
        System.out.println("=== Static resource serving simulation ===\n");
        serveRequest("/css/style.css", false);        // served from /static/
        serveRequest("/js/app.js", false);            // served from /static/
        serveRequest("/robots.txt", false);           // served from /public/
        serveRequest("/webjars/jquery/3.7.1/jquery.min.js", false); // from META-INF
        serveRequest("/api/orders", true);            // controller handles it
        serveRequest("/missing.png", false);          // 404

        System.out.println("=== Key properties ===");
        System.out.println("spring.mvc.static-path-pattern=/assets/**");
        System.out.println("  → serves /assets/css/style.css from /static/css/style.css");
        System.out.println("spring.web.resources.cache.period=31536000");
        System.out.println("  → Cache-Control: max-age=31536000 (1 year)");
        System.out.println("spring.web.resources.static-locations=classpath:/static/,file:/opt/www/");
        System.out.println("  → also serves from OS filesystem path");
    }
}
```

**How to run:** `java StaticContentServing.java`

## 6. Walkthrough

- `LOCATIONS` mirrors Spring Boot's `ResourceProperties.CLASSPATH_RESOURCE_LOCATIONS` constant. The order matters: `/META-INF/resources/` is checked first, allowing libraries (e.g. WebJars) to bundle resources inside their JARs that appear at the front of the search path.
- `findResource("/css/style.css")` iterates locations and tries `/META-INF/resources/css/style.css`, `/resources/css/style.css`, `/public/css/style.css`, and finally `/static/css/style.css` — which exists. Returns that path.
- `serveRequest("/api/orders", true)` — the controller flag represents `DispatcherServlet` finding a `@Controller` that handles the path. Static resource handling only fires when no other handler claims the path.
- `serveRequest("/robots.txt", false)` finds the file in `/public/` — it doesn't have to be in `/static/`.
- `serveRequest("/webjars/jquery/…", false)` — WebJars (CSS/JS libraries packaged as JARs) put their assets under `META-INF/resources/webjars/`. Adding a WebJar dependency to `pom.xml` makes those assets auto-available at `/webjars/**` URLs — no extraction required.

## 7. Gotchas & takeaways

> **Files in `/static` are publicly accessible without authentication.** If you put a sensitive file there (a report, a key file, an admin template), it's served to anyone who guesses the URL. Spring Security's resource exemptions are applied at the HTTP layer but static files bypass most controller-level security. Keep secrets out of `src/main/resources/static/`.

> **`spring.mvc.static-path-pattern` changes the URL prefix, not the directory structure.** Setting it to `/assets/**` means `GET /assets/css/style.css` serves `src/main/resources/static/css/style.css`. The URL prefix changes; the file path within the resource directory stays the same.

- Use `/static/` for your own assets and `/public/` or `/resources/` for assets you want to keep conceptually separate (e.g. third-party files you're not versioning).
- WebJars (`org.webjars:jquery`) auto-serve their files at `/webjars/**` — no controller or property needed.
- For far-future caching, enable `spring.web.resources.chain.strategy.content.enabled=true` — assets get URL-fingerprinted and can be cached with `max-age=31536000`.
- In a Spring Boot test, `@SpringBootTest` includes the static resource handler; use `MockMvc.perform(get("/css/style.css"))` to test that a file is served.
- If you add `spring.mvc.static-path-pattern=/ui/**` and forget to update your HTML links, all assets will 404. Use Thymeleaf's `@{…}` URL expressions — they use the resolver and automatically apply the correct prefix.
