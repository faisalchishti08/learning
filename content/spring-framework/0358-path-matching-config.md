---
card: spring-framework
gi: 358
slug: path-matching-config
title: "Path matching config"
---

## 1. What it is

`configurePathMatch` is a `WebMvcConfigurer` override that controls how Spring MVC matches incoming request URLs against `@RequestMapping` patterns — trailing-slash handling, case sensitivity, and the underlying pattern-matching strategy (`PathPattern`, the modern, faster parser used by default since Spring 5.3).

```java
@Override
public void configurePathMatch(PathMatchConfigurer configurer) {
    configurer.setUseTrailingSlashMatch(false);
}
```

## 2. Why & when

Spring MVC's default path-matching behavior is sensible for most applications, but a few settings matter enough to be worth understanding and occasionally adjusting:

- **Trailing slash matching**: historically, Spring MVC treated `/products` and `/products/` as equivalent by default. Since Spring 6 / Spring Boot 3, this default changed to **not** match them as equivalent — `useTrailingSlashMatch` now defaults to `false`. Understanding this matters when upgrading an older application, where routes and tests may have implicitly relied on the old, more lenient behavior.
- **Case sensitivity**: by default, path matching is case-sensitive (`/Products` and `/products` are different routes) — occasionally a legacy integration or a specific API contract requires case-insensitive matching, though this is generally discouraged for new APIs since it can create ambiguity and is inconsistent with REST URL conventions.
- Custom path-matching needs when integrating with reverse proxies or gateways that rewrite paths in ways that interact with Spring's pattern matching in non-obvious ways.

## 3. Core concept

```
setUseTrailingSlashMatch(boolean):

  true (Spring Framework 5.x and earlier default):
    @GetMapping("/products") matches BOTH:
      GET /products
      GET /products/          <- ALSO matches, same handler

  false (Spring Framework 6.x / Spring Boot 3+ default):
    @GetMapping("/products") matches ONLY:
      GET /products
    GET /products/  -> 404 (unless a SEPARATE mapping exists for it)

This default change is one of the most common "my app behaves
differently after upgrading to Spring Boot 3" surprises — routes,
tests, and even hardcoded links with/without a trailing slash that
worked interchangeably before may now diverge.

PathPatternParser (the modern default matching engine):
  faster than the legacy AntPathMatcher
  slightly different edge-case semantics for wildcard patterns
  used automatically unless explicitly configured otherwise
```

## 4. Diagram

<svg viewBox="0 0 720 200" xmlns="http://www.w3.org/2000/svg" font-family="monospace" font-size="12">
  <rect width="720" height="200" fill="#0d1117"/>
  <text x="360" y="22" text-anchor="middle" fill="#8b949e">Trailing slash matching: old default vs current default</text>

  <rect x="20" y="50" width="320" height="110" rx="5" fill="#1c2430" stroke="#8b949e"/>
  <text x="180" y="72" text-anchor="middle" fill="#8b949e" font-size="11">useTrailingSlashMatch(true)</text>
  <text x="180" y="92" text-anchor="middle" fill="#8b949e" font-size="9">(legacy default, Spring 5.x)</text>
  <text x="35" y="115" fill="#6db33f" font-size="10">GET /products   -&gt; matches</text>
  <text x="35" y="135" fill="#6db33f" font-size="10">GET /products/  -&gt; ALSO matches</text>

  <rect x="380" y="50" width="320" height="110" rx="5" fill="#1c2430" stroke="#6db33f"/>
  <text x="540" y="72" text-anchor="middle" fill="#6db33f" font-size="11">useTrailingSlashMatch(false)</text>
  <text x="540" y="92" text-anchor="middle" fill="#8b949e" font-size="9">(current default, Spring 6+ / Boot 3+)</text>
  <text x="395" y="115" fill="#6db33f" font-size="10">GET /products   -&gt; matches</text>
  <text x="395" y="135" fill="#e6edf3" font-size="10">GET /products/  -&gt; 404</text>

  <defs>
    <marker id="a34" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L0,6 L8,3 z" fill="#8b949e"/>
    </marker>
  </defs>
</svg>

*The trailing-slash default flipped between Spring Framework generations — a common source of post-upgrade route breakage.*

## 5. Runnable example

### Level 1 — Basic

Observing current default behavior (strict, no trailing-slash equivalence) and explicitly registering both variants when both are genuinely needed:

```java
// ProductController.java
import org.springframework.web.bind.annotation.*;

@RestController
public class ProductController {

    @GetMapping({"/products", "/products/"})   // explicit BOTH patterns, since they no longer auto-match
    public String list() {
        return "[]";
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run

curl -i http://localhost:8080/products
# HTTP/1.1 200 OK

curl -i http://localhost:8080/products/
# HTTP/1.1 200 OK      <- matches too, but ONLY because BOTH patterns were explicitly listed
```

On current Spring Boot versions, `@GetMapping("/products")` alone would **not** match `/products/` — the example explicitly lists both patterns in the mapping's array to restore that equivalence deliberately, rather than relying on framework-level lenient matching.

### Level 2 — Intermediate

Explicitly re-enabling legacy trailing-slash matching application-wide (useful when migrating an older application with many existing routes/links that assume the old behavior, as a temporary compatibility measure):

```java
// WebConfig.java
import org.springframework.context.annotation.Configuration;
import org.springframework.web.servlet.config.annotation.PathMatchConfigurer;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;

@Configuration
public class WebConfig implements WebMvcConfigurer {
    @Override
    public void configurePathMatch(PathMatchConfigurer configurer) {
        configurer.setUseTrailingSlashMatch(true);   // restores the PRE-Spring-6 lenient behavior
    }
}
```

```java
// ProductController.java (unchanged from before the config override)
import org.springframework.web.bind.annotation.*;

@RestController
public class ProductController {
    @GetMapping("/products")   // single pattern, no explicit trailing-slash variant needed
    public String list() { return "[]"; }
}
```

**How to run:**
```bash
./mvnw spring-boot:run

curl -i http://localhost:8080/products
# HTTP/1.1 200 OK

curl -i http://localhost:8080/products/
# HTTP/1.1 200 OK      <- matches AGAIN, now via the application-wide configuration
```

**What changed:** With `setUseTrailingSlashMatch(true)` applied globally, every `@RequestMapping`-family pattern in the application regains the old lenient behavior — no need to list both variants explicitly on each mapping, as in Level 1. This is a pragmatic option for a large legacy codebase during migration, though new applications should generally embrace the stricter, current default rather than reverting it.

### Level 3 — Advanced

Production concern: understanding that re-enabling lenient trailing-slash matching has implications for **redirect and canonical-URL correctness**, and the recommended alternative — explicit redirect from the trailing-slash variant to the canonical, non-trailing-slash URL, which is friendlier to SEO and caching than silently matching both as identical:

```java
// WebConfig.java (production version) — deliberately does NOT re-enable lenient matching
import org.springframework.context.annotation.Configuration;
import org.springframework.web.servlet.config.annotation.ViewControllerRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;

@Configuration
public class WebConfig implements WebMvcConfigurer {
    // configurePathMatch NOT overridden — keep the strict, current default.
    // Trailing-slash variants of specific, known routes are handled via EXPLICIT
    // redirects instead, which is more correct than silent equivalence:
    // a redirect tells clients and search engines definitively "the canonical
    // URL is the non-slash one," rather than leaving two URLs serving
    // IDENTICAL content indefinitely (a minor SEO/caching anti-pattern, since
    // it can be seen as duplicate content by crawlers and split caching by URL).

    @Override
    public void addViewControllers(ViewControllerRegistry registry) {
        registry.addRedirectViewController("/products/", "/products");
    }
}
```

```java
// ProductController.java (production version)
import org.springframework.web.bind.annotation.*;

@RestController
public class ProductController {
    @GetMapping("/products")   // the ONE canonical URL — no trailing-slash variant registered here
    public String list() { return "[]"; }
}
```

**How to run:**
```bash
./mvnw spring-boot:run

curl -i http://localhost:8080/products
# HTTP/1.1 200 OK

curl -i http://localhost:8080/products/
# HTTP/1.1 302 Found
# Location: /products
```

**What changed and why:**
- Rather than making `/products` and `/products/` silently equivalent (which the old lenient default did, and which `setUseTrailingSlashMatch(true)` would restore), the production configuration keeps the strict current default and instead **redirects** the trailing-slash variant to the canonical URL.
- This is more correct for real-world concerns: search engines treat `/products` and `/products/` as potentially distinct URLs unless told otherwise, and a `301`/`302` redirect explicitly declares one canonical form — silent dual-matching leaves this ambiguous and can dilute SEO ranking signals or cause caching layers to store the "same" content under two separate cache keys.
- This pattern (explicit redirect per known trailing-slash variant, rather than blanket lenient matching) scales cleanly: you only add a redirect for routes that actually need one, rather than reintroducing ambiguity across the entire application's URL space.

## 6. Walkthrough

**Request: `GET /products/` (Level 3 code, strict matching + explicit redirect).**

1. `DispatcherServlet` consults its `HandlerMapping` chain. `RequestMappingHandlerMapping` checks `/products/` against all registered `@RequestMapping` patterns — `ProductController.list()` is mapped to `/products` (no trailing slash), and because `useTrailingSlashMatch` is at its strict current default (`false`), `/products/` does **not** match this pattern.
2. `RequestMappingHandlerMapping` declines. `SimpleUrlHandlerMapping` (backing view controllers, registered via `addViewControllers`) is checked next — it finds the explicitly registered redirect: `addRedirectViewController("/products/", "/products")` maps exactly this path.
3. The resolved handler is a `RedirectView` pointing at `/products`. `DispatcherServlet` invokes it directly — no controller method executes, no model is built.
4. `RedirectView.render(...)` writes a redirect response:
   ```
   HTTP/1.1 302 Found
   Location: /products
   ```
5. A real browser (or any HTTP client following redirects) automatically issues a **new** `GET /products` request as a result.

**That follow-up request: `GET /products`.**

1. `DispatcherServlet` again consults `RequestMappingHandlerMapping` — this time, `/products` matches `ProductController.list()`'s pattern exactly.
2. `list()` executes, returns `"[]"`.
3. Response:
   ```
   HTTP/1.1 200 OK
   Content-Type: application/json

   []
   ```

The end-to-end effect (two round-trips total) is functionally similar to what lenient trailing-slash matching would have achieved in one round-trip — but with an explicit, crawlable, cache-friendly signal about which URL is canonical, rather than two URLs silently serving identical content forever.

## 7. Gotchas & takeaways

> **Upgrading from Spring Framework 5.x / Spring Boot 2.x to Spring Framework 6.x / Spring Boot 3.x silently flips the trailing-slash matching default** — any application that had routes, hardcoded links, or client integrations relying on `/path` and `/path/` being interchangeable can experience new `404`s immediately after upgrading, with no code change on the application's own routes. This is one of the most common "what broke after the Spring Boot 3 upgrade" issues.

> **Re-enabling `setUseTrailingSlashMatch(true)` application-wide is a blunt instrument** — it silently restores dual-URL equivalence everywhere, reintroducing the SEO/caching ambiguity concerns explained in the Level 3 example, across the *entire* application rather than just the specific routes that genuinely need backward compatibility. Prefer explicit per-route redirects for a more precise, intentional fix during migration.

> **Case-sensitive path matching (the default) means `/Products` and `/products` are entirely different routes** — a typo in a hardcoded link's capitalization produces a silent `404` rather than the "probably meant the same thing" leniency some other web frameworks provide. This is deliberate and generally considered a feature (URLs *should* be treated as case-sensitive identifiers per the URL specification), but it's worth knowing explicitly when debugging an unexpected `404`.

- The trailing-slash matching default changed between Spring Framework generations — Spring 6+/Boot 3+ defaults to strict (no automatic equivalence), a common post-upgrade surprise.
- Prefer explicit per-route redirects from a trailing-slash variant to the canonical URL over blanket-restoring lenient matching, for better SEO and caching correctness.
- Path matching is case-sensitive by default — a capitalization mismatch in a route or link produces a silent `404`, not a fuzzy match.
- When migrating a legacy application, `setUseTrailingSlashMatch(true)` is a valid temporary compatibility measure, but plan to move toward explicit, canonical URLs over time.
