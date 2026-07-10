---
card: spring-framework
gi: 334
slug: content-negotiation
title: "Content negotiation"
---

## 1. What it is

Content negotiation is the mechanism by which Spring MVC decides which representation (JSON, XML, plain text, a custom media type) to send back for a request that could produce more than one, based on what the client asks for — typically via the `Accept` header, but also via a URL path extension or a query parameter, depending on configuration. It's driven by the `produces` attribute on mappings and the set of registered `HttpMessageConverter`s.

```java
@GetMapping(value = "/products/{id}", produces = {MediaType.APPLICATION_JSON_VALUE, MediaType.APPLICATION_XML_VALUE})
public Product get(@PathVariable long id) { ... }
```

## 2. Why & when

A single logical resource (`/products/1`) might need to serve different formats to different consumers: a JavaScript frontend wants JSON, a legacy enterprise integration wants XML, a monitoring tool wants plain text. Content negotiation lets one endpoint serve all of them without branching logic in the handler — the framework picks the right `HttpMessageConverter` based on what's available and what's requested.

Use content negotiation when:
- Your API needs to support multiple response formats for the same resource (JSON + XML being the classic case).
- You're versioning an API by media type (`application/vnd.acme.product.v2+json`) rather than by URL path.
- You want the framework, not manual `if/else` on headers, to decide format — keeping handler methods free of formatting branches.

For APIs that only ever produce JSON, explicit content negotiation configuration is unnecessary — Spring Boot's default (Jackson-based JSON) just works. It becomes relevant the moment more than one representation is genuinely needed.

## 3. Core concept

```
Client request:
  Accept: application/xml, application/json;q=0.8

Server has a handler with:
  produces = {application/json, application/xml}

Negotiation steps:
  1. Parse Accept header into ranked list:
       application/xml       (q=1.0, implicit)
       application/json      (q=0.8)
  2. Intersect with what the handler CAN produce:
       both application/xml and application/json are supported
  3. Pick the highest-ranked mutual match:
       application/xml wins (q=1.0 > q=0.8)
  4. Select the HttpMessageConverter that handles application/xml
       (e.g. Jackson's XML module, or JAXB)
  5. Converter serializes the return value to XML
  6. Response Content-Type: application/xml

If NO mutual match exists:
  -> 406 Not Acceptable
```

Other negotiation strategies exist (path extension `.json`/`.xml`, `?format=` query parameter) but header-based (`Accept`) negotiation is the modern default and generally recommended approach.

## 4. Diagram

<svg viewBox="0 0 720 240" xmlns="http://www.w3.org/2000/svg" font-family="monospace" font-size="12">
  <rect width="720" height="240" fill="#0d1117"/>
  <text x="360" y="22" text-anchor="middle" fill="#8b949e">Accept header negotiated against handler's produces list</text>

  <rect x="20" y="50" width="220" height="70" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="130" y="72" text-anchor="middle" fill="#79c0ff">Request</text>
  <text x="130" y="90" text-anchor="middle" fill="#8b949e" font-size="10">Accept: application/xml,</text>
  <text x="130" y="105" text-anchor="middle" fill="#8b949e" font-size="10">application/json;q=0.8</text>

  <rect x="280" y="50" width="220" height="70" rx="5" fill="#1c2430" stroke="#6db33f"/>
  <text x="390" y="72" text-anchor="middle" fill="#6db33f">Handler produces</text>
  <text x="390" y="90" text-anchor="middle" fill="#8b949e" font-size="10">application/json,</text>
  <text x="390" y="105" text-anchor="middle" fill="#8b949e" font-size="10">application/xml</text>

  <line x1="240" y1="85" x2="280" y2="85" stroke="#8b949e" marker-end="url(#a10)"/>
  <line x1="130" y1="120" x2="270" y2="160" stroke="#8b949e" marker-end="url(#a10)"/>
  <line x1="390" y1="120" x2="330" y2="160" stroke="#8b949e" marker-end="url(#a10)"/>

  <rect x="200" y="160" width="260" height="60" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="330" y="182" text-anchor="middle" fill="#e6edf3" font-size="11">highest mutual q-value wins:</text>
  <text x="330" y="200" text-anchor="middle" fill="#6db33f" font-size="11">application/xml (q=1.0)</text>

  <defs>
    <marker id="a10" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L0,6 L8,3 z" fill="#8b949e"/>
    </marker>
  </defs>
</svg>

*The client's ranked `Accept` preferences are intersected with what the handler can actually produce; the highest-ranked overlap wins.*

## 5. Runnable example

### Level 1 — Basic

A single endpoint that produces JSON by default (Spring Boot's out-of-the-box behavior — no extra configuration):

```java
// ProductController.java
import org.springframework.web.bind.annotation.*;

@RestController
public class ProductController {

    record Product(long id, String name, double price) {}

    @GetMapping("/products/{id}")
    public Product get(@PathVariable long id) {
        return new Product(id, "Drill", 29.99);
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run

curl -H "Accept: application/json" http://localhost:8080/products/1
# {"id":1,"name":"Drill","price":29.99}
# Content-Type: application/json

curl http://localhost:8080/products/1        # no Accept header at all -> defaults to */*
# {"id":1,"name":"Drill","price":29.99}       # still JSON, the only registered converter that matches
```

Even with no explicit `produces` on the mapping, Spring Boot registers Jackson's `MappingJackson2HttpMessageConverter` by default, so JSON is produced for any `Accept` that includes `application/json` or `*/*`.

### Level 2 — Intermediate

Adding XML support alongside JSON, and observing what happens when a client asks for a format the server can't produce:

```xml
<!-- pom.xml addition -->
<dependency>
    <groupId>com.fasterxml.jackson.dataformat</groupId>
    <artifactId>jackson-dataformat-xml</artifactId>
</dependency>
```

```java
// ProductController.java (extended)
import org.springframework.http.MediaType;
import org.springframework.web.bind.annotation.*;

@RestController
public class ProductController {

    record Product(long id, String name, double price) {}

    @GetMapping(value = "/products/{id}",
                produces = {MediaType.APPLICATION_JSON_VALUE, MediaType.APPLICATION_XML_VALUE})
    public Product get(@PathVariable long id) {
        return new Product(id, "Drill", 29.99);
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run

curl -H "Accept: application/xml" http://localhost:8080/products/1
# <Product><id>1</id><name>Drill</name><price>29.99</price></Product>
# Content-Type: application/xml

curl -H "Accept: application/json" http://localhost:8080/products/1
# {"id":1,"name":"Drill","price":29.99}

curl -i -H "Accept: text/csv" http://localhost:8080/products/1
# HTTP/1.1 406 Not Acceptable   (no registered converter produces text/csv)
```

**What changed:** Adding the `jackson-dataformat-xml` dependency auto-registers an XML-capable `HttpMessageConverter`. Listing both media types in `produces` tells Spring this endpoint can genuinely serve either. A request for an unsupported format (`text/csv`) correctly gets `406 Not Acceptable` — the framework refuses to silently substitute a format the client didn't ask for.

### Level 3 — Advanced

Production pattern: explicit content negotiation configuration disabling risky strategies (path-extension negotiation, which can create security issues and ambiguity with resource paths that happen to contain dots), setting a safe default, and a custom media type for API versioning combined with a fallback error response the client can actually parse:

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
            .favorParameter(false)          // disable ?format=xml — avoids cache-poisoning ambiguity
            .ignoreAcceptHeader(false)       // DO use the Accept header (the safe, standard mechanism)
            .defaultContentType(MediaType.APPLICATION_JSON)   // fallback when Accept is */* or absent
            .mediaType("json", MediaType.APPLICATION_JSON)
            .mediaType("xml", MediaType.APPLICATION_XML);
    }
}
```

```java
// ProductController.java (production version)
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.HttpMediaTypeNotAcceptableException;
import org.springframework.web.bind.annotation.*;

@RestController
public class ProductController {

    record Product(long id, String name, double price) {}

    @GetMapping(value = "/products/{id}",
                produces = {"application/vnd.acme.product.v1+json", MediaType.APPLICATION_JSON_VALUE})
    public Product get(@PathVariable long id) {
        return new Product(id, "Drill", 29.99);
    }

    // Give a clear, parseable error instead of a bare 406 with an empty body
    @ExceptionHandler(HttpMediaTypeNotAcceptableException.class)
    public ResponseEntity<?> handleNotAcceptable(HttpMediaTypeNotAcceptableException ex) {
        return ResponseEntity.status(HttpStatus.NOT_ACCEPTABLE)
            .body(java.util.Map.of(
                "error", "unsupported format",
                "supported", java.util.List.of("application/vnd.acme.product.v1+json", "application/json")));
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run

curl -H "Accept: application/vnd.acme.product.v1+json" http://localhost:8080/products/1
# {"id":1,"name":"Drill","price":29.99}
# Content-Type: application/vnd.acme.product.v1+json

curl http://localhost:8080/products/1?format=xml
# {"id":1,"name":"Drill","price":29.99}    <- format param IGNORED (favorParameter(false)); still JSON

curl -i -H "Accept: application/yaml" http://localhost:8080/products/1
# HTTP/1.1 406 Not Acceptable
# {"error":"unsupported format","supported":["application/vnd.acme.product.v1+json","application/json"]}
```

**What changed and why:**
- `favorParameter(false)` disables `?format=xml`-style negotiation — query-parameter-based negotiation can let an attacker manipulate response format via a URL that gets cached or logged differently than the header-based request would, and it conflicts with resources that legitimately need a `format` query parameter for other purposes. Disabling it forces the one clear, standard mechanism: the `Accept` header.
- `defaultContentType(APPLICATION_JSON)` ensures a request with no `Accept` header (or `*/*`) gets a predictable, sane default instead of an ambiguous pick among several registered converters.
- The custom `@ExceptionHandler` for `HttpMediaTypeNotAcceptableException` turns a bare, body-less `406` into a structured, actionable error telling the client exactly what formats are supported — much friendlier for API consumers debugging an integration.

## 6. Walkthrough

**Request: `GET /products/1` with `Accept: application/vnd.acme.product.v1+json` (Level 3 code).**

1. `DispatcherServlet` finds candidate handlers for `/products/1`. `ProductController.get` declares `produces = {"application/vnd.acme.product.v1+json", "application/json"}`.
2. `ContentNegotiationManager` (configured via `WebConfig`) determines the requested media types from the `Accept` header (path-extension and query-parameter strategies are disabled, so only the header is consulted): `[application/vnd.acme.product.v1+json]`.
3. It intersects the requested types with the handler's `produces` list: exact match found on `application/vnd.acme.product.v1+json`.
4. The handler is selected and invoked; returns `Product{1, "Drill", 29.99}`.
5. A `HttpMessageConverter` capable of writing `application/vnd.acme.product.v1+json` is selected (Jackson's JSON converter, configured to also claim vendor `+json` subtypes) and serializes the record.
6. Response:
   ```
   HTTP/1.1 200 OK
   Content-Type: application/vnd.acme.product.v1+json

   {"id":1,"name":"Drill","price":29.99}
   ```

**Request: `GET /products/1` with `Accept: application/yaml` (unsupported format).**

1. Same handler resolution reaches `ProductController.get` as the only candidate for the path.
2. `ContentNegotiationManager` determines the requested type is `application/yaml`.
3. Intersecting with `produces = {vnd.acme.product.v1+json, application/json}` yields **no match**.
4. Spring throws `HttpMediaTypeNotAcceptableException` internally, signaling that no acceptable representation exists.
5. The controller's own `@ExceptionHandler(HttpMediaTypeNotAcceptableException.class)` catches it (rather than letting it fall through to Spring's bare default `406`), builds a structured error map, and returns it wrapped as `406`.
6. Because this response itself needs a `Content-Type`, and `application/yaml` was never acceptable, Spring negotiates the *error* response separately — falling back to the configured default (`application/json`, from `defaultContentType`):
   ```
   HTTP/1.1 406 Not Acceptable
   Content-Type: application/json

   {"error":"unsupported format","supported":["application/vnd.acme.product.v1+json","application/json"]}
   ```

## 7. Gotchas & takeaways

> **`produces` on a `@GetMapping` restricts which requests match that handler at all — not just the output format.** A request whose `Accept` header doesn't overlap with `produces` won't even reach the method; if you have multiple overloaded handlers on the same path split by `produces`, a mismatched `Accept` can produce a confusing `404` (no handler matched) rather than the expected `406`, depending on whether any other handler exists for that path.

> **Enabling both path-extension (`.json`/`.xml`) and parameter (`?format=`) negotiation strategies alongside header-based negotiation creates ambiguity and, historically, security issues** (extension-based negotiation was implicated in several older Spring CVEs around request-mapping confusion). Modern guidance is to rely on the `Accept` header only, as configured in the Level 3 example.

> **A bare `406 Not Acceptable` with no response body leaves API consumers guessing why their request failed.** Pairing content negotiation with an `@ExceptionHandler` for `HttpMediaTypeNotAcceptableException` (or a global one in a `@ControllerAdvice`) turns a dead end into an actionable error message.

- Content negotiation matches the client's ranked `Accept` header against each handler's `produces` list; the highest-ranked mutual match wins.
- Disable path-extension and query-parameter negotiation for production APIs — the `Accept` header is the standard, unambiguous mechanism.
- Always set an explicit `defaultContentType` so requests without an `Accept` header behave predictably.
- Vendor-specific media types (`application/vnd.company.resource.v1+json`) are a legitimate way to version an API by content type instead of by URL path.
