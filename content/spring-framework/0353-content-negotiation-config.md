---
card: spring-framework
gi: 353
slug: content-negotiation-config
title: "Content negotiation config"
---

## 1. What it is

Content negotiation config is the `WebMvcConfigurer.configureContentNegotiation(ContentNegotiationConfigurer)` override that centrally controls how Spring MVC determines a request's target media type — which negotiation strategies are active (`Accept` header, path extension, query parameter), what the fallback default is, and how short media-type aliases (`json`, `xml`) map to full `MediaType` values. This card focuses specifically on the configuration surface itself, consolidating and formalizing the negotiation behavior touched on in earlier content-negotiation cards.

```java
@Override
public void configureContentNegotiation(ContentNegotiationConfigurer configurer) {
    configurer
        .favorParameter(false)
        .ignoreAcceptHeader(false)
        .defaultContentType(MediaType.APPLICATION_JSON)
        .mediaType("json", MediaType.APPLICATION_JSON)
        .mediaType("xml", MediaType.APPLICATION_XML);
}
```

## 2. Why & when

Spring Boot's default content negotiation configuration (`Accept` header only, no path-extension or parameter-based strategies) is safe and correct for the overwhelming majority of applications — you often need zero explicit configuration here. Reach for this configuration when:

- You need a **non-default fallback** behavior — e.g. a public API that should default to JSON when no `Accept` header is present, rather than Spring's built-in fallback logic.
- You're supporting a **specific alias-based negotiation** for a legacy client integration (some older clients or tooling send `?format=json` instead of a proper `Accept` header) — though this should be adopted cautiously given its security tradeoffs (see gotchas).
- You need to register custom, non-standard media types (`application/vnd.company.resource.v1+json`) as short aliases for convenient use elsewhere in `produces`/`consumes` attributes.

## 3. Core concept

```
ContentNegotiationConfigurer options:

  favorParameter(boolean)
    enable/disable "?format=json"-style negotiation (default: false, recommended)

  parameterName(String)
    customize the parameter name if favorParameter is enabled (default: "format")

  ignoreAcceptHeader(boolean)
    if true, the Accept header is IGNORED entirely for negotiation
    (default: false — Accept header IS used, this is almost always what you want)

  defaultContentType(MediaType...)
    fallback type(s) when no strategy produces a result
    (e.g. no Accept header, or Accept: */*)

  mediaType(String extension, MediaType type)
    register a short alias, usable in @RequestMapping(produces=...)
    string forms elsewhere, and (if favorPathExtension were enabled,
    which it is NOT by default in modern Spring) path extensions

  useRegisteredExtensionsOnly(boolean)
    if path-extension negotiation is somehow enabled, restrict it
    to ONLY explicitly registered extensions (safety measure)

Precedence when multiple strategies are enabled (evaluated in this order):
  1. Path extension (DISABLED by default, discouraged — see gotchas)
  2. Query parameter (DISABLED by default)
  3. Accept header (ENABLED by default — the standard, recommended strategy)
  4. defaultContentType fallback
```

## 4. Diagram

<svg viewBox="0 0 720 210" xmlns="http://www.w3.org/2000/svg" font-family="monospace" font-size="12">
  <rect width="720" height="210" fill="#0d1117"/>
  <text x="360" y="22" text-anchor="middle" fill="#8b949e">Negotiation strategy precedence and defaults</text>

  <rect x="20" y="50" width="200" height="40" rx="4" fill="#1c2430" stroke="#e6edf3" stroke-dasharray="3,3"/>
  <text x="120" y="75" text-anchor="middle" fill="#e6edf3" font-size="10">1. Path extension (off by default)</text>

  <rect x="20" y="95" width="200" height="40" rx="4" fill="#1c2430" stroke="#e6edf3" stroke-dasharray="3,3"/>
  <text x="120" y="120" text-anchor="middle" fill="#e6edf3" font-size="10">2. Query param (off by default)</text>

  <rect x="20" y="140" width="200" height="40" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="120" y="165" text-anchor="middle" fill="#6db33f" font-size="10">3. Accept header (ON by default)</text>

  <rect x="260" y="95" width="200" height="40" rx="4" fill="#1c2430" stroke="#79c0ff"/>
  <text x="360" y="120" text-anchor="middle" fill="#79c0ff" font-size="10">4. defaultContentType fallback</text>

  <line x1="220" y1="160" x2="260" y2="115" stroke="#8b949e" marker-end="url(#a29)"/>
  <text x="500" y="118" fill="#8b949e" font-size="10">used only if</text>
  <text x="500" y="132" fill="#8b949e" font-size="10">no Accept match</text>

  <defs>
    <marker id="a29" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L0,6 L8,3 z" fill="#8b949e"/>
    </marker>
  </defs>
</svg>

*Modern Spring MVC defaults to `Accept`-header-only negotiation, with a configurable fallback for ambiguous requests.*

## 5. Runnable example

### Level 1 — Basic

Explicit defaults matching what Spring Boot already does implicitly — useful as a starting template to customize from:

```java
// WebConfig.java
import org.springframework.context.annotation.Configuration;
import org.springframework.http.MediaType;
import org.springframework.web.servlet.config.annotation.ContentNegotiationConfigurer;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;

@Configuration
public class WebConfig implements WebMvcConfigurer {
    @Override
    public void configureContentNegotiation(ContentNegotiationConfigurer configurer) {
        configurer
            .favorParameter(false)
            .ignoreAcceptHeader(false)
            .defaultContentType(MediaType.APPLICATION_JSON);
    }
}
```

```java
// ProductController.java
import org.springframework.web.bind.annotation.*;

@RestController
public class ProductController {

    record Product(long id, String name) {}

    @GetMapping("/products/{id}")
    public Product get(@PathVariable long id) {
        return new Product(id, "Drill");
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run

curl http://localhost:8080/products/1
# {"id":1,"name":"Drill"}      <- no Accept header, defaultContentType(JSON) kicks in

curl -H "Accept: application/json" http://localhost:8080/products/1
# {"id":1,"name":"Drill"}
```

This configuration produces identical behavior to Spring Boot's implicit defaults — its value here is making the negotiation strategy explicit and easy to find/modify, rather than relying on undocumented default assumptions.

### Level 2 — Intermediate

Registering XML support alongside JSON, with custom media type aliases usable elsewhere in `produces` attributes:

```xml
<!-- pom.xml addition -->
<dependency>
    <groupId>com.fasterxml.jackson.dataformat</groupId>
    <artifactId>jackson-dataformat-xml</artifactId>
</dependency>
```

```java
// WebConfig.java (extended)
import org.springframework.context.annotation.Configuration;
import org.springframework.http.MediaType;
import org.springframework.web.servlet.config.annotation.ContentNegotiationConfigurer;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;

@Configuration
public class WebConfig implements WebMvcConfigurer {
    @Override
    public void configureContentNegotiation(ContentNegotiationConfigurer configurer) {
        configurer
            .favorParameter(false)
            .defaultContentType(MediaType.APPLICATION_JSON)
            .mediaType("json", MediaType.APPLICATION_JSON)
            .mediaType("xml", MediaType.APPLICATION_XML);
    }
}
```

```java
// ProductController.java (extended) — "json"/"xml" aliases usable in produces
import org.springframework.web.bind.annotation.*;

@RestController
public class ProductController {

    record Product(long id, String name) {}

    @GetMapping(value = "/products/{id}", produces = {"application/json", "application/xml"})
    public Product get(@PathVariable long id) {
        return new Product(id, "Drill");
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run

curl -H "Accept: application/xml" http://localhost:8080/products/1
# <Product><id>1</id><name>Drill</name></Product>

curl -H "Accept: application/json" http://localhost:8080/products/1
# {"id":1,"name":"Drill"}

curl -i -H "Accept: application/yaml" http://localhost:8080/products/1
# HTTP/1.1 406 Not Acceptable
```

**What changed:** The registered `mediaType("json", ...)`/`mediaType("xml", ...)` aliases mostly matter for *legacy* path-extension negotiation (`.json`/`.xml` URL suffixes) — which remains explicitly disabled here (no `favorPathExtension` call, and it's off by default in current Spring versions) — but registering them is still good practice for consistency and for any custom infrastructure code that queries the `ContentNegotiationManager` for known types by short name.

### Level 3 — Advanced

Production concern: understanding exactly why path-extension and parameter-based negotiation are discouraged, with a concrete demonstration of the security-relevant ambiguity they can introduce, alongside the recommended safe configuration:

```java
// WebConfig.java (production version)
import org.springframework.context.annotation.Configuration;
import org.springframework.http.MediaType;
import org.springframework.web.servlet.config.annotation.ContentNegotiationConfigurer;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;

@Configuration
public class WebConfig implements WebMvcConfigurer {
    @Override
    public void configureContentNegotiation(ContentNegotiationConfigurer configurer) {
        configurer
            // Explicitly confirm both risky strategies are OFF — defensive, self-documenting configuration
            // even though these are already the framework defaults in modern Spring versions.
            .favorParameter(false)
            .ignoreAcceptHeader(false)
            .defaultContentType(MediaType.APPLICATION_JSON)
            .mediaType("json", MediaType.APPLICATION_JSON)
            .mediaType("xml", MediaType.APPLICATION_XML);
    }
}
```

```java
// SecurityAwareProductController.java — demonstrates WHY path-extension negotiation was risky historically
import org.springframework.web.bind.annotation.*;

@RestController
public class SecurityAwareProductController {

    record Product(long id, String name) {}

    // If path-extension negotiation were enabled (it is NOT here), a URL like
    // "/products/1.xml" could historically be interpreted as a NEGOTIATION SUFFIX
    // rather than a literal part of the path — occasionally colliding with security
    // rules written against exact path patterns (e.g. a rule protecting "/products/1"
    // that a suffixed variant could, in older Spring versions, be used to route around).
    // Modern Spring MVC disables this by default specifically because of this history.
    @GetMapping(value = "/products/{id}", produces = {"application/json", "application/xml"})
    public Product get(@PathVariable long id) {
        return new Product(id, "Drill");
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run

curl http://localhost:8080/products/1.xml
# 400 Bad Request or 404 — "1.xml" is treated as a LITERAL path variable value attempting
# long parsing, NOT as "id=1, format=xml", because path-extension negotiation is disabled

curl -H "Accept: application/xml" http://localhost:8080/products/1
# <Product><id>1</id><name>Drill</name></Product>   <- the SAFE, standard way to request XML
```

**What changed and why:**
- Explicitly setting `favorParameter(false)` and never enabling path-extension negotiation (there is no `favorPathExtension` call at all, matching modern Spring's removal of that option by default) documents the security-conscious choice directly in code, rather than relying silently on framework defaults that a future maintainer might not know to preserve.
- The comment on `SecurityAwareProductController` explains the historical reasoning: path-extension-based content negotiation was implicated in several real-world Spring Security bypass techniques in older Spring MVC versions, where a request path's apparent "resource path" for security-rule matching purposes could diverge from the path actually used for handler dispatch once a negotiation suffix was stripped. This is precisely why the Accept-header-only strategy became, and remains, the recommended default.
- `/products/1.xml` now fails to parse as a valid `long` path variable (since `"1.xml"` isn't a valid number) rather than being silently reinterpreted as `id=1` with an XML format hint — a deliberately "loud failure" over a "silently magical but historically risky" one.

## 6. Walkthrough

**Request: `GET /products/1` with `Accept: application/xml` (Level 3 code).**

1. `DispatcherServlet` matches the request path `/products/1` to `SecurityAwareProductController.get(1)` — path matching happens purely on the literal URL, with no extension-stripping logic involved, since path-extension negotiation is disabled.
2. Before invoking the handler, content negotiation determines the target media type by consulting the `ContentNegotiationManager`, configured with strategies in this precedence: path extension (skipped, disabled), query parameter (skipped, disabled), `Accept` header (active) — reads `application/xml`.
3. The handler's `produces = {"application/json", "application/xml"}` is checked against the negotiated type `application/xml` — a match.
4. `get(1)` executes, returns `Product{1, "Drill"}`.
5. An XML-capable `HttpMessageConverter` (registered because `jackson-dataformat-xml` is on the classpath) serializes the record.
6. Response:
   ```
   HTTP/1.1 200 OK
   Content-Type: application/xml

   <Product><id>1</id><name>Drill</name></Product>
   ```

**Request: `GET /products/1.xml` (attempting the historical path-extension pattern, now correctly rejected).**

1. `DispatcherServlet` attempts to match `/products/1.xml` against the registered pattern `/products/{id}`. Because path-extension stripping is disabled, the entire segment `"1.xml"` is treated as the literal value for `{id}` — no suffix is stripped off first.
2. Spring attempts to bind the path variable: `@PathVariable long id` requires the string `"1.xml"` to convert to a `long` via the standard `String → long` converter.
3. `"1.xml"` is not a valid `long` literal — the built-in converter throws a `TypeMismatchException`/`MethodArgumentTypeMismatchException`.
4. Because no `@ExceptionHandler` is registered for this specific exception in this simplified example, Spring's default handling (or Boot's default error page) produces a client error response:
   ```
   HTTP/1.1 400 Bad Request
   ```
5. This "loud failure" is the desired outcome from a security-hygiene perspective: there's no silent, magic reinterpretation of the URL's meaning based on a suffix — the client gets clear feedback that `/products/1.xml` isn't a valid request, and must instead use the `Accept` header as shown in the prior walkthrough.

## 7. Gotchas & takeaways

> **Path-extension-based content negotiation (`.json`/`.xml` URL suffixes) is disabled by default in modern Spring MVC specifically because of historical security concerns** — it could create ambiguity between the "path used for security rule matching" and "path used for handler dispatch" in some configurations. Do not re-enable it unless you have a very specific, well-understood legacy integration requirement, and even then, pair it with `useRegisteredExtensionsOnly(true)` to limit the attack surface.

> **`?format=xml`-style query-parameter negotiation, if enabled via `favorParameter(true)`, means the response format can be influenced by a value that's easily cached, logged, bookmarked, or shared differently than the resource's "real" identity** — a URL with `?format=json` and one without can represent the "same" resource with different `Content-Type`s, which can confuse caching layers (proxies, CDNs) that key purely on the URL.

> **`defaultContentType` only applies when no other negotiation strategy produces a usable result** — it does not override an explicit, valid `Accept` header the client actually sent. Don't expect it to force a specific format on every request; it's purely a fallback for ambiguous or missing `Accept` headers.

- `configureContentNegotiation` centralizes which negotiation strategies are active and what the fallback format is — most applications only need to set `defaultContentType`.
- The `Accept` header is the standard, recommended, and (in modern Spring MVC) default negotiation strategy; path-extension and query-parameter strategies are both disabled by default for good, security-relevant reasons.
- Register custom media type aliases via `mediaType(...)` for use in `produces`/`consumes` attributes, even without enabling the negotiation strategies that would otherwise consume them via URL suffixes/parameters.
- When in doubt, leave content negotiation configuration at Spring Boot's defaults — only override it when you have a specific, well-understood requirement.
