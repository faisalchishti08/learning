---
card: spring-framework
gi: 363
slug: mvc-http-2-considerations
title: "MVC HTTP/2 considerations"
---

## 1. What it is

HTTP/2 is a binary, multiplexed transport protocol — a major revision of how HTTP messages travel over the wire, though the request/response semantics Spring MVC works with (methods, headers, status codes, bodies) remain unchanged. Spring MVC itself is largely transport-agnostic (it doesn't know or care whether HTTP/1.1 or HTTP/2 delivered a request), but a few application-level practices that made sense under HTTP/1.1's constraints become unnecessary or even counterproductive under HTTP/2, and enabling it requires configuration at the embedded server level, not in Spring MVC itself.

```yaml
# application.yml — enabling HTTP/2 on embedded Tomcat (requires TLS)
server:
  http2:
    enabled: true
  ssl:
    enabled: true
    key-store: classpath:keystore.p12
    key-store-password: changeit
```

## 2. Why & when

HTTP/1.1 has a well-known limitation: browsers open only a small number of parallel TCP connections per origin (historically 6), and each connection can only have one request in flight at a time (head-of-line blocking at the HTTP layer). This drove a whole ecosystem of HTTP/1.1-era performance techniques: **domain sharding** (spreading assets across multiple subdomains to get more parallel connections), **asset concatenation/bundling** (combining many small files into fewer large ones to reduce the number of separate requests), and **image spriting** (combining many small images into one large image, sliced via CSS).

HTTP/2 multiplexes many requests over a **single** TCP connection, largely eliminating the original motivation for these techniques — and in some cases, they now actively work *against* HTTP/2's strengths (e.g. bundling defeats HTTP/2's efficient per-resource caching, since a single changed line invalidates the *entire* bundle rather than just one small file). Understanding this matters when:

- Modernizing a legacy application's asset-delivery strategy that was built around HTTP/1.1-era assumptions.
- Configuring the embedded server (Tomcat, Jetty, Undertow) to actually enable HTTP/2, since Spring Boot doesn't turn it on by default and it requires TLS in virtually all real-world deployments (browsers only support HTTP/2 over TLS via ALPN negotiation, even though the spec technically allows cleartext HTTP/2).
- Understanding that Spring MVC's own request/response handling code requires **no changes** to work correctly over HTTP/2 — the protocol upgrade happens entirely below the servlet API abstraction layer.

## 3. Core concept

```
HTTP/1.1 (per-origin connection limits, one request in flight per connection):

  Browser -> [conn 1: GET /style.css]      (blocks other requests on THIS connection)
  Browser -> [conn 2: GET /script.js]      (needs a SEPARATE connection for parallelism)
  Browser -> [conn 3: GET /logo.png]
  ... limited to ~6 parallel connections per origin

  Mitigations (now often UNNECESSARY under HTTP/2):
    - bundle many small JS/CSS files into ONE large file (fewer requests needed)
    - shard assets across multiple subdomains (more connections allowed)
    - inline small images as data URIs (skip a request entirely)

HTTP/2 (single connection, MULTIPLEXED streams):

  Browser -> [ONE connection]
               stream 1: GET /style.css   ─┐
               stream 3: GET /script.js    ├─ all IN FLIGHT SIMULTANEOUSLY,
               stream 5: GET /logo.png    ─┘  interleaved over ONE TCP connection

  Bundling now often HURTS: one small CSS change invalidates
  the WHOLE bundle's cache, instead of just one small file's

Spring MVC's role: NONE of this affects @Controller code, argument
resolution, or response handling — it's entirely a TRANSPORT-LAYER
concern, configured at the embedded server, invisible to handler code.
```

## 4. Diagram

<svg viewBox="0 0 740 230" xmlns="http://www.w3.org/2000/svg" font-family="monospace" font-size="12">
  <rect width="740" height="230" fill="#0d1117"/>
  <text x="370" y="22" text-anchor="middle" fill="#8b949e">HTTP/1.1 multiple connections vs HTTP/2 multiplexed streams</text>

  <rect x="20" y="50" width="320" height="150" rx="5" fill="#1c2430" stroke="#8b949e"/>
  <text x="180" y="70" text-anchor="middle" fill="#8b949e" font-size="10">HTTP/1.1</text>
  <text x="35" y="95" fill="#8b949e" font-size="9">conn 1: -- style.css --&gt;</text>
  <text x="35" y="115" fill="#8b949e" font-size="9">conn 2: -- script.js --&gt;</text>
  <text x="35" y="135" fill="#8b949e" font-size="9">conn 3: -- logo.png --&gt;</text>
  <text x="35" y="160" fill="#8b949e" font-size="9">3 separate TCP connections</text>
  <text x="35" y="178" fill="#8b949e" font-size="9">needed for parallelism</text>

  <rect x="390" y="50" width="330" height="150" rx="5" fill="#1c2430" stroke="#6db33f"/>
  <text x="555" y="70" text-anchor="middle" fill="#6db33f" font-size="10">HTTP/2</text>
  <text x="405" y="95" fill="#8b949e" font-size="9">ONE connection, multiplexed streams:</text>
  <text x="405" y="115" fill="#6db33f" font-size="9">stream 1: style.css</text>
  <text x="405" y="133" fill="#6db33f" font-size="9">stream 3: script.js</text>
  <text x="405" y="151" fill="#6db33f" font-size="9">stream 5: logo.png</text>
  <text x="405" y="175" fill="#8b949e" font-size="9">all interleaved, ONE connection</text>

  <defs>
    <marker id="a39" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L0,6 L8,3 z" fill="#8b949e"/>
    </marker>
  </defs>
</svg>

*HTTP/2 multiplexes many logical streams over a single TCP connection, removing the original motivation for HTTP/1.1-era bundling/sharding tricks.*

## 5. Runnable example

### Level 1 — Basic

Enabling HTTP/2 on embedded Tomcat with a self-signed certificate for local testing, and confirming Spring MVC's controller code needs zero changes:

```yaml
# application.yml
server:
  port: 8443
  http2:
    enabled: true
  ssl:
    enabled: true
    key-store: classpath:keystore.p12
    key-store-password: changeit
    key-store-type: PKCS12
```

```bash
# Generate a local self-signed certificate for testing
keytool -genkeypair -alias tomcat -keyalg RSA -keysize 2048 -storetype PKCS12 \
  -keystore src/main/resources/keystore.p12 -validity 365 -dname "CN=localhost"
```

```java
// ProductController.java — completely ordinary, HTTP-version-agnostic code
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

curl -k --http2 -I https://localhost:8443/products/1
# HTTP/2 200
# content-type: application/json

curl -k --http1.1 -I https://localhost:8443/products/1
# HTTP/1.1 200        <- the SAME endpoint, same code, still perfectly serves HTTP/1.1 clients
```

`ProductController` required zero changes to work over HTTP/2 — the protocol negotiation (via TLS's ALPN extension) happens entirely at the connection layer, below anything Spring MVC's `@Controller` code interacts with. The server transparently serves both protocol versions to whichever clients request them.

### Level 2 — Intermediate

Demonstrating the practical shift away from HTTP/1.1-era asset bundling — serving several small, individually cacheable files instead of one large bundle, and observing that this is now a reasonable (often preferable) strategy under HTTP/2:

```java
// WebConfig.java
import org.springframework.context.annotation.Configuration;
import org.springframework.http.CacheControl;
import org.springframework.web.servlet.config.annotation.ResourceHandlerRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;
import org.springframework.web.servlet.resource.VersionResourceResolver;

import java.time.Duration;

@Configuration
public class WebConfig implements WebMvcConfigurer {
    @Override
    public void addResourceHandlers(ResourceHandlerRegistry registry) {
        // Several SEPARATE, individually versioned/cacheable files — a deliberate choice
        // that would have been a performance ANTI-PATTERN under HTTP/1.1 (too many
        // separate requests), but is entirely reasonable under HTTP/2's multiplexing.
        registry.addResourceHandler("/assets/**")
            .addResourceLocations("classpath:/static/assets/")
            .setCacheControl(CacheControl.maxAge(Duration.ofDays(365)).immutable())
            .resourceChain(true)
            .addResolver(new VersionResourceResolver().addContentVersionStrategy("/**"));
    }
}
```

`templates/home.html`:
```html
<html xmlns:th="http://www.thymeleaf.org">
<head>
  <!-- Several SEPARATE stylesheets — each independently cacheable and versioned.
       Editing button-styles.css invalidates ONLY that file's hash, not a giant bundle. -->
  <link rel="stylesheet" th:href="@{/assets/layout.css}">
  <link rel="stylesheet" th:href="@{/assets/typography.css}">
  <link rel="stylesheet" th:href="@{/assets/button-styles.css}">
</head>
<body><h1>Home</h1></body>
</html>
```

**How to run:**
```bash
./mvnw spring-boot:run

curl -k --http2 https://localhost:8443/
# <link href="/assets/layout-a1b2.css">
# <link href="/assets/typography-c3d4.css">
# <link href="/assets/button-styles-e5f6.css">
# three separate, independently versioned/cached files — served efficiently over ONE
# multiplexed HTTP/2 connection, no separate-connection penalty as there would have
# been under HTTP/1.1
```

**What changed:** Rather than bundling `layout.css` + `typography.css` + `button-styles.css` into one large `app.css` (the HTTP/1.1-era default best practice, to minimize request count), each file remains separate. Under HTTP/2, the browser fetches all three over the same multiplexed connection with negligible per-request overhead, and — the real payoff — editing `button-styles.css` only invalidates *that* file's version-hashed URL and cache entry, leaving `layout.css`'s and `typography.css`'s long-lived caches completely untouched.

### Level 3 — Advanced

Production concern: correctly configuring the embedded server for HTTP/2 behind a reverse proxy/load balancer (a very common real-world topology, where the proxy — not the Spring Boot application itself — often terminates the client-facing TLS/HTTP2 connection), and understanding what changes versus a direct-to-application HTTP/2 setup:

```yaml
# application.yml — application behind a reverse proxy that terminates client TLS
# In THIS topology, the proxy speaks HTTP/2 to BROWSERS, but often speaks plain
# HTTP/1.1 to the application internally (a common, simpler configuration) —
# so the application itself does NOT need server.http2.enabled at all.
server:
  port: 8080
  forward-headers-strategy: framework   # tells Spring Boot to trust and process X-Forwarded-* headers
```

```java
// WebConfig.java — ForwardedHeaderFilter is handled automatically via forward-headers-strategy,
// no manual filter registration needed when set to "framework"
import org.springframework.web.bind.annotation.*;

@RestController
public class ProductController {

    @GetMapping("/products/{id}")
    public String get(@PathVariable long id) {
        // Redirect/URL-building code here correctly reflects the CLIENT-FACING
        // https:// scheme and hostname, even though the application itself only
        // ever sees plain HTTP/1.1 connections from the proxy.
        return "Drill";
    }
}
```

**Reverse proxy config (nginx example, illustrative):**
```nginx
server {
    listen 443 ssl http2;               # proxy speaks HTTP/2 + TLS to BROWSERS
    ssl_certificate     /etc/ssl/cert.pem;
    ssl_certificate_key /etc/ssl/key.pem;

    location / {
        proxy_pass http://app-internal:8080;   # plain HTTP/1.1 to the Spring Boot app
        proxy_set_header X-Forwarded-Proto https;
        proxy_set_header X-Forwarded-Host $host;
    }
}
```

**How to run:**
```bash
# Client connects to the PROXY over HTTP/2 + TLS:
curl --http2 -I https://shop.example.com/products/1
# HTTP/2 200

# The proxy internally forwards to the Spring Boot app over plain HTTP/1.1 —
# the application itself never directly negotiates HTTP/2 at all in this topology.
```

**What changed and why:**
- `forward-headers-strategy: framework` is the key setting for this topology — it tells Spring Boot to automatically apply `ForwardedHeaderFilter`-equivalent processing, trusting the proxy's `X-Forwarded-*` headers so that any URL-building code in the application (redirects, absolute links) correctly reflects `https://shop.example.com`, even though the actual TCP connection reaching the application is plain HTTP/1.1 from the internal proxy.
- This is an extremely common production topology: the reverse proxy/load balancer (nginx, an AWS ALB, a CDN edge) handles the complexity of TLS termination and HTTP/2 negotiation with real browsers, while the application itself runs a simpler, plain HTTP/1.1 configuration internally — there's no requirement that the Spring Boot application itself terminate HTTP/2 for the *overall* system to benefit from HTTP/2's client-facing performance improvements.
- This demonstrates that "does my application use HTTP/2" is often the wrong question in production — the more relevant question is "does the client-facing edge of my system speak HTTP/2," which frequently is a proxy/CDN concern entirely separate from the application server's own configuration.

## 6. Walkthrough

**Request: a browser fetching `https://shop.example.com/products/1` (Level 3 topology — proxy terminates HTTP/2, forwards HTTP/1.1 internally).**

1. The browser establishes a TLS connection to the reverse proxy (nginx), negotiating HTTP/2 via ALPN during the TLS handshake — this negotiation happens entirely between the browser and the proxy; the Spring Boot application is not a party to it at all.
2. The browser sends its request as an HTTP/2 stream over this connection: `GET /products/1`.
3. nginx receives and decodes the HTTP/2 stream, then re-issues the request as a plain HTTP/1.1 request to the internal application (`proxy_pass http://app-internal:8080`), adding `X-Forwarded-Proto: https` and `X-Forwarded-Host: shop.example.com` headers to communicate the original client-facing connection details.
4. The Spring Boot application (embedded Tomcat, listening on plain HTTP/1.1 port `8080`) receives this internal request. Because `forward-headers-strategy: framework` is configured, Spring Boot's request-forwarding-aware infrastructure processes the `X-Forwarded-*` headers automatically.
5. `DispatcherServlet` dispatches to `ProductController.get(1)` exactly as it would for any other request — nothing about the handler method's execution differs based on the original client's protocol version.
6. `get(1)` returns `"Drill"`. Because of the forwarded-header processing from step 4, if this handler needed to build an absolute URL (a redirect, a `Location` header), it would correctly produce `https://shop.example.com/...`, not `http://app-internal:8080/...`.
7. The response travels back to nginx over the internal HTTP/1.1 connection, which re-encodes it as an HTTP/2 stream and sends it to the browser over the original HTTP/2 connection.
8. The browser receives the response over HTTP/2, exactly as it would for any HTTP/2-served content — with the entire internal HTTP/1.1 hop between proxy and application completely invisible to it.

## 7. Gotchas & takeaways

> **HTTP/2 (per the spec) technically allows cleartext operation, but virtually no browser supports it — real-world HTTP/2 deployments require TLS.** Attempting to enable `server.http2.enabled: true` without also configuring TLS (`server.ssl.enabled: true`) produces a server that starts but that browsers will simply refuse to speak HTTP/2 to, silently falling back to HTTP/1.1 with no obvious error.

> **Bundling/concatenating assets is not universally "wrong" under HTTP/2 — it depends on change frequency and cache-invalidation granularity.** A bundle of assets that change together, infrequently, can still be a reasonable choice; the anti-pattern specifically is bundling *unrelated*, *independently-changing* assets purely to reduce request count, since HTTP/2 removes the request-count penalty that justified that specific tradeoff.

> **In a reverse-proxy topology, forgetting `forward-headers-strategy` (or the equivalent manual `ForwardedHeaderFilter` registration) means the application misinterprets its own connection details** — redirects and absolute URLs can end up pointing at the internal proxy-to-application address instead of the client-facing one, a bug that's easy to miss in local development (no proxy involved) and only surfaces in the deployed topology.

- Spring MVC's `@Controller` code requires zero changes to work correctly over HTTP/2 — protocol negotiation happens entirely below the servlet API, typically via TLS's ALPN extension.
- HTTP/2's multiplexing removes the original motivation for HTTP/1.1-era asset bundling, domain sharding, and image spriting — prefer smaller, independently cacheable/versioned resources where practical.
- Real-world HTTP/2 requires TLS; enabling `server.http2.enabled` without TLS configuration produces a server browsers will silently ignore for HTTP/2 purposes.
- In reverse-proxy topologies, the application itself often doesn't need to speak HTTP/2 at all — `forward-headers-strategy: framework` (or an equivalent `ForwardedHeaderFilter`) ensures the application correctly reflects the client-facing connection details regardless.
