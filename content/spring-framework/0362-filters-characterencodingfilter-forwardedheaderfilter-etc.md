---
card: spring-framework
gi: 362
slug: filters-characterencodingfilter-forwardedheaderfilter-etc
title: "Filters (CharacterEncodingFilter, ForwardedHeaderFilter, etc.)"
---

## 1. What it is

Spring provides several ready-made `jakarta.servlet.Filter` implementations that solve common, cross-cutting HTTP concerns before a request ever reaches `DispatcherServlet` (or after the response leaves it) — `CharacterEncodingFilter` (ensures consistent request/response text encoding), `ForwardedHeaderFilter` (correctly interprets `X-Forwarded-*` headers from a reverse proxy), `HiddenHttpMethodFilter` (lets HTML forms simulate `PUT`/`DELETE`), and others. You register them as regular servlet filters, either via Spring Boot's `FilterRegistrationBean` or (in a plain servlet environment) `web.xml`/`WebApplicationInitializer`.

```java
@Bean
public FilterRegistrationBean<CharacterEncodingFilter> characterEncodingFilter() {
    CharacterEncodingFilter filter = new CharacterEncodingFilter();
    filter.setEncoding("UTF-8");
    filter.setForceEncoding(true);
    FilterRegistrationBean<CharacterEncodingFilter> registration = new FilterRegistrationBean<>(filter);
    registration.addUrlPatterns("/*");
    return registration;
}
```

## 2. Why & when

Filters (as opposed to `HandlerInterceptor`s, covered in an earlier card) run at the servlet container level — before Spring MVC has even identified a handler, and for *every* request matching their URL pattern, including static resources and requests that never reach a `@Controller` at all. This makes them the right tool for concerns that must apply universally and early, rather than only to matched MVC routes.

Use these built-in filters when:
- **`CharacterEncodingFilter`**: request bodies (especially form submissions) arrive with inconsistent or missing character encoding, causing garbled non-ASCII text (accented characters, non-Latin scripts) unless explicitly forced to UTF-8.
- **`ForwardedHeaderFilter`**: the application runs behind a reverse proxy or load balancer that terminates TLS and forwards plain HTTP internally, using `X-Forwarded-Proto`/`X-Forwarded-Host`/`X-Forwarded-For` headers to communicate the original client-facing details — without this filter, Spring MVC's URL-building (redirects, `HttpServletRequest.getRequestURL()`) would incorrectly reflect the internal (proxy-to-app) connection details instead of what the client actually saw.
- **`HiddenHttpMethodFilter`**: an HTML form (which only supports `GET`/`POST` natively) needs to simulate a `PUT`/`DELETE`/`PATCH` request via a hidden `_method` form field.

## 3. Core concept

```
Filter chain position, relative to DispatcherServlet:

  Request
     |
     v
  [Filter 1] -> [Filter 2] -> [Filter N] -> DispatcherServlet -> Controller
     |             |              |                                  |
     |             |              |                                  v
     <-------------<--------------<---------------------------- Response
                    (filters can also process the RESPONSE on the way back)

CharacterEncodingFilter:
  request.setCharacterEncoding("UTF-8")  <- BEFORE any parameter parsing occurs
  (must run early — parameters are parsed lazily on first access,
   using WHATEVER encoding is set at that moment)

ForwardedHeaderFilter:
  reads X-Forwarded-Proto: https, X-Forwarded-Host: app.example.com
  WRAPS the request/response so that request.getScheme(), .getServerName(),
  redirect URL building, etc. all reflect the ORIGINAL client-facing values,
  not the internal proxy-to-app connection's actual scheme/host

HiddenHttpMethodFilter:
  <form method="post"><input type="hidden" name="_method" value="DELETE">
  filter INTERCEPTS the POST, reads "_method", WRAPS the request so
  DispatcherServlet sees it as if it were an actual DELETE request
```

## 4. Diagram

<svg viewBox="0 0 740 220" xmlns="http://www.w3.org/2000/svg" font-family="monospace" font-size="12">
  <rect width="740" height="220" fill="#0d1117"/>
  <text x="370" y="22" text-anchor="middle" fill="#8b949e">Filters run before DispatcherServlet, for every matching request</text>

  <rect x="20" y="50" width="160" height="50" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="100" y="80" text-anchor="middle" fill="#79c0ff" font-size="10">Incoming request</text>

  <line x1="180" y1="75" x2="230" y2="75" stroke="#8b949e" marker-end="url(#a38)"/>
  <rect x="230" y="50" width="150" height="50" rx="5" fill="#1c2430" stroke="#6db33f"/>
  <text x="305" y="80" text-anchor="middle" fill="#6db33f" font-size="9">CharacterEncodingFilter</text>

  <line x1="380" y1="75" x2="420" y2="75" stroke="#8b949e" marker-end="url(#a38)"/>
  <rect x="420" y="50" width="150" height="50" rx="5" fill="#1c2430" stroke="#6db33f"/>
  <text x="495" y="80" text-anchor="middle" fill="#6db33f" font-size="9">ForwardedHeaderFilter</text>

  <line x1="570" y1="75" x2="620" y2="75" stroke="#8b949e" marker-end="url(#a38)"/>
  <rect x="620" y="50" width="100" height="50" rx="5" fill="#1c2430" stroke="#8b949e"/>
  <text x="670" y="80" text-anchor="middle" fill="#e6edf3" font-size="9">Dispatcher-Servlet</text>

  <text x="370" y="140" text-anchor="middle" fill="#8b949e" font-size="10">Every filter runs BEFORE any @Controller code, for EVERY matching URL — including static assets</text>

  <defs>
    <marker id="a38" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L0,6 L8,3 z" fill="#8b949e"/>
    </marker>
  </defs>
</svg>

*Filters chain in registration order, running before `DispatcherServlet` sees the request at all.*

## 5. Runnable example

### Level 1 — Basic

`CharacterEncodingFilter` forcing consistent UTF-8 handling for form submissions:

```java
// FilterConfig.java
import org.springframework.boot.web.servlet.FilterRegistrationBean;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.filter.CharacterEncodingFilter;

@Configuration
public class FilterConfig {

    @Bean
    public FilterRegistrationBean<CharacterEncodingFilter> characterEncodingFilter() {
        CharacterEncodingFilter filter = new CharacterEncodingFilter();
        filter.setEncoding("UTF-8");
        filter.setForceEncoding(true);   // force UTF-8 even if the client specified something else

        FilterRegistrationBean<CharacterEncodingFilter> registration = new FilterRegistrationBean<>(filter);
        registration.addUrlPatterns("/*");
        registration.setOrder(0);   // run FIRST, before parameters are ever parsed
        return registration;
    }
}
```

```java
// ProductController.java
import org.springframework.web.bind.annotation.*;

@RestController
public class ProductController {

    @PostMapping("/products")
    public String create(@RequestParam String name) {
        return "Received: " + name;
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run

curl -X POST http://localhost:8080/products --data-urlencode "name=Café Münster"
# Received: Café Münster       <- correctly decoded, thanks to forced UTF-8
```

Without the filter (or with `setForceEncoding(false)` and no explicit encoding from the client), a form field containing accented characters could arrive garbled — the filter guarantees the encoding is set to UTF-8 *before* Spring MVC's parameter-parsing machinery ever reads the request body, which matters because encoding must be set before the first access to request parameters, not after.

### Level 2 — Intermediate

`ForwardedHeaderFilter` correctly reflecting the client-facing URL when the application runs behind a reverse proxy that terminates TLS:

```java
// FilterConfig.java (extended)
import org.springframework.boot.web.servlet.FilterRegistrationBean;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.filter.CharacterEncodingFilter;
import org.springframework.web.filter.ForwardedHeaderFilter;

@Configuration
public class FilterConfig {

    @Bean
    public FilterRegistrationBean<CharacterEncodingFilter> characterEncodingFilter() {
        CharacterEncodingFilter filter = new CharacterEncodingFilter();
        filter.setEncoding("UTF-8");
        filter.setForceEncoding(true);
        FilterRegistrationBean<CharacterEncodingFilter> registration = new FilterRegistrationBean<>(filter);
        registration.setOrder(0);
        return registration;
    }

    @Bean
    public FilterRegistrationBean<ForwardedHeaderFilter> forwardedHeaderFilter() {
        FilterRegistrationBean<ForwardedHeaderFilter> registration =
            new FilterRegistrationBean<>(new ForwardedHeaderFilter());
        registration.setOrder(1);   // AFTER encoding, but early — before URL-building code runs
        return registration;
    }
}
```

```java
// ProductController.java (extended)
import org.springframework.web.bind.annotation.*;

import java.net.URI;

@RestController
public class ProductController {

    @PostMapping("/products")
    public String create(@RequestParam String name) {
        // Building an absolute URL for a Location-style header — WITHOUT ForwardedHeaderFilter,
        // this would reflect the internal proxy connection (e.g. http://app-internal:8080),
        // not the actual client-facing address.
        return "Created at: " + URI.create("https://shop.example.com/products/1");   // illustrative
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run

curl -X POST http://localhost:8080/products \
     -H "X-Forwarded-Proto: https" \
     -H "X-Forwarded-Host: shop.example.com" \
     --data-urlencode "name=Drill"
# request.getScheme() now correctly reports "https", request.getServerName() reports "shop.example.com" —
# any Spring-generated redirect or absolute URL built from the request reflects the CLIENT-FACING address
```

**What changed:** `ForwardedHeaderFilter` inspects `X-Forwarded-Proto`/`X-Forwarded-Host`/`X-Forwarded-Port` (headers a well-configured reverse proxy sets to describe the original client connection) and wraps the request so that `HttpServletRequest.getScheme()`, `.getServerName()`, and Spring's own URL-building utilities (used internally for redirects, `UriComponentsBuilder.fromCurrentRequest()`, etc.) all reflect the client's actual view of the connection, not the internal, proxy-to-application hop's plain-HTTP details.

### Level 3 — Advanced

Production concern: correct filter ordering when combining multiple built-in filters, and the security implications of trusting `X-Forwarded-*` headers only from a genuinely trusted reverse proxy — since blindly trusting these headers from an untrusted client would allow request spoofing:

```java
// FilterConfig.java (production version)
import org.springframework.boot.web.servlet.FilterRegistrationBean;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.filter.CharacterEncodingFilter;
import org.springframework.web.filter.ForwardedHeaderFilter;
import org.springframework.web.filter.HiddenHttpMethodFilter;

@Configuration
public class FilterConfig {

    @Bean
    public FilterRegistrationBean<CharacterEncodingFilter> characterEncodingFilter() {
        CharacterEncodingFilter filter = new CharacterEncodingFilter();
        filter.setEncoding("UTF-8");
        filter.setForceEncoding(true);
        FilterRegistrationBean<CharacterEncodingFilter> registration = new FilterRegistrationBean<>(filter);
        registration.setOrder(0);   // MUST run before anything reads request parameters
        return registration;
    }

    @Bean
    public FilterRegistrationBean<ForwardedHeaderFilter> forwardedHeaderFilter() {
        // SECURITY NOTE: this filter TRUSTS whatever X-Forwarded-* headers arrive at this filter.
        // It must ONLY be enabled when the application sits behind a reverse proxy/load balancer
        // that is configured to STRIP any client-supplied X-Forwarded-* headers and set its own —
        // otherwise, a malicious client could directly send X-Forwarded-Proto: https or a spoofed
        // X-Forwarded-Host to manipulate redirect URLs or bypass scheme-based security checks.
        FilterRegistrationBean<ForwardedHeaderFilter> registration =
            new FilterRegistrationBean<>(new ForwardedHeaderFilter());
        registration.setOrder(1);
        return registration;
    }

    @Bean
    public FilterRegistrationBean<HiddenHttpMethodFilter> hiddenHttpMethodFilter() {
        // Order matters: this must run AFTER CharacterEncodingFilter (needs correctly-decoded
        // parameters to read "_method") but its exact position relative to ForwardedHeaderFilter
        // doesn't matter, since they address unrelated concerns.
        FilterRegistrationBean<HiddenHttpMethodFilter> registration =
            new FilterRegistrationBean<>(new HiddenHttpMethodFilter());
        registration.setOrder(2);
        return registration;
    }
}
```

```java
// ProductController.java (production version)
import org.springframework.web.bind.annotation.*;

@RestController
public class ProductController {

    @DeleteMapping("/products/{id}")
    public String delete(@PathVariable long id) {
        return "Deleted " + id;
    }
}
```

`templates/product-detail.html` (an HTML form using the hidden-method trick, since browsers can't natively submit DELETE):
```html
<form method="post" action="/products/1">
    <input type="hidden" name="_method" value="DELETE">
    <button type="submit">Delete Product</button>
</form>
```

**How to run:**
```bash
./mvnw spring-boot:run

curl -X POST http://localhost:8080/products/1 -d "_method=DELETE"
# Deleted 1     <- the POST was transparently reinterpreted as a DELETE by the filter
```

**What changed and why:**
- Explicit `setOrder(...)` values on each `FilterRegistrationBean` guarantee a deterministic filter chain order — `CharacterEncodingFilter` must run first (parameter decoding must be correct before anything reads `_method` or any other parameter), `HiddenHttpMethodFilter` needs correctly-decoded parameters to function, and `ForwardedHeaderFilter`'s position relative to the other two is independent but should still be early, before any application logic depends on request scheme/host.
- The security-note comment on `ForwardedHeaderFilter` addresses a genuinely important production concern: this filter must only be active when a **trusted** reverse proxy sits in front of the application and is configured to overwrite (not merely append to) any client-supplied `X-Forwarded-*` headers — otherwise, a direct, un-proxied request from a malicious client could spoof these headers to manipulate scheme-based logic (e.g. a security check that only enforces certain rules for `https` requests, tricked into thinking a plain-HTTP direct connection is actually `https` via a forged header).
- `HiddenHttpMethodFilter` enables genuine `DELETE`/`PUT`/`PATCH` semantics from plain HTML forms, which the HTML specification itself restricts to `GET`/`POST` only — the filter bridges this gap by wrapping the request so `DispatcherServlet` and all downstream code see the "real" intended HTTP method.

## 6. Walkthrough

**Request: browser form `POST /products/1` with body `_method=DELETE` (Level 3 code).**

1. The servlet container receives the raw `POST` request and begins passing it through the registered filter chain, in `order` sequence: `CharacterEncodingFilter` (order 0) first.
2. `CharacterEncodingFilter.doFilter` calls `request.setCharacterEncoding("UTF-8")` (with `forceEncoding=true`, overriding any client-declared encoding) — this must happen before any code reads request parameters, since the servlet API only respects the encoding set *before* the first parameter access.
3. The filter chain proceeds to `ForwardedHeaderFilter` (order 1) — in this specific request, no `X-Forwarded-*` headers are present, so it passes the request through essentially unchanged (its wrapping logic only activates when those headers exist).
4. The chain proceeds to `HiddenHttpMethodFilter` (order 2). It reads the request parameter `_method` — now correctly decoded thanks to step 2 — finds the value `"DELETE"`. Because the original method is `POST` and a `_method` parameter is present, this filter creates a **wrapped** `HttpServletRequest` whose `getMethod()` returns `"DELETE"` instead of the original `"POST"`.
5. This wrapped request (reporting `DELETE`) is passed to the next element in the chain — ultimately, `DispatcherServlet`.
6. `DispatcherServlet` asks `RequestMappingHandlerMapping` to match the request. Because the wrapped request reports method `DELETE`, it matches `ProductController.delete(long id)` — mapped via `@DeleteMapping("/products/{id}")` — exactly as if the client had sent a genuine `DELETE` request.
7. `delete(1)` executes normally, returns `"Deleted 1"`.
8. Response:
   ```
   HTTP/1.1 200 OK
   Content-Type: text/plain;charset=UTF-8

   Deleted 1
   ```

The entire method-override mechanism happens transparently in the filter layer — `ProductController` itself has no idea the original wire-level request was a `POST`; it only ever sees the wrapped request reporting `DELETE`.

## 7. Gotchas & takeaways

> **`CharacterEncodingFilter` must be registered with a low `order` value (running early) — if any code reads a request parameter before this filter sets the encoding, the encoding is already "locked in" (typically to the platform default or whatever the client declared) and setting it afterward has no effect.** This is a subtle but common source of "why doesn't my encoding fix work" confusion.

> **`ForwardedHeaderFilter` should never be enabled in an application directly exposed to untrusted clients without a properly configured, header-stripping reverse proxy in front of it** — otherwise, any client can forge `X-Forwarded-Proto`/`X-Forwarded-Host` headers to manipulate how the application perceives its own connection scheme and hostname, potentially bypassing scheme-dependent security logic.

> **`HiddenHttpMethodFilter` only recognizes `PUT`, `DELETE`, and `PATCH` as override targets from an original `POST`** — it cannot, for instance, turn a `GET` into anything else, since `GET` requests don't carry a body from which to read the `_method` parameter in the standard case.

- Filters run before `DispatcherServlet`, for every matching request, including ones that never reach a `@Controller` — the right layer for concerns that must apply universally and early.
- `CharacterEncodingFilter` must run before any parameter access; register it with the lowest `order` value in the chain.
- `ForwardedHeaderFilter` correctly reflects a reverse proxy's client-facing scheme/host, but must only be trusted behind a proxy that strips client-supplied `X-Forwarded-*` headers.
- `HiddenHttpMethodFilter` lets HTML forms simulate `PUT`/`DELETE`/`PATCH` via a hidden `_method` field, since browsers only natively support `GET`/`POST` form submissions.
