---
card: spring-framework
gi: 344
slug: content-negotiation-view-resolution
title: "Content negotiation view resolution"
---

## 1. What it is

Content negotiation view resolution is the specific mechanism, implemented by `ContentNegotiatingViewResolver`, that lets a single view name resolve to *different* `View` implementations depending on what the client's request asks for. It doesn't render anything itself — it delegates to a list of other `ViewResolver`s to gather every candidate `View` for a given name, then picks the one whose media type best matches the negotiated content type for the request.

```java
@Bean
public ViewResolver contentNegotiatingViewResolver(ContentNegotiationManager manager) {
    ContentNegotiatingViewResolver resolver = new ContentNegotiatingViewResolver();
    resolver.setContentNegotiationManager(manager);
    resolver.setDefaultViews(List.of(new MappingJackson2JsonView(), new MappingJackson2XmlView()));
    return resolver;
}
```

## 2. Why & when

This card looks specifically at the mechanics of *how* the resolver chooses among candidates — building on the general content-negotiation concepts (the `Accept` header, `ContentNegotiationManager`) from the earlier "Content negotiation" card, applied here to server-rendered views rather than `@RestController` JSON responses.

Use `ContentNegotiatingViewResolver` when:
- One logical resource (an invoice, a report, a product page) needs to render as HTML for browsers *and* as structured data (JSON/XML) for programmatic clients, from the exact same controller method and view name.
- You're incrementally adding an API surface to an existing server-rendered application without duplicating controller logic into a parallel `@RestController`.
- You want the resolver to fall back gracefully — HTML by default for browsers, structured formats only when explicitly requested.

## 3. Core concept

```
ContentNegotiatingViewResolver.resolveViewName("invoice", locale):

  1. Determine the list of REQUESTED media types for this request,
     via ContentNegotiationManager (Accept header, by default)
       e.g. Accept: application/json, text/html;q=0.8

  2. Ask each DELEGATE ViewResolver (e.g. ThymeleafViewResolver)
     to resolve "invoice" — collect whatever View(s) they return
     as CANDIDATES, each candidate's media type known via
     view.getContentType()
       Thymeleaf's resolver -> candidate: ThymeleafView (text/html)

  3. Add any explicitly configured DEFAULT VIEWS as further candidates
       MappingJackson2JsonView   (application/json)
       MappingJackson2XmlView    (application/xml)

  4. Score ALL candidates against the requested media types list,
     pick the highest-scoring match:
       application/json (q=1.0, explicit) beats text/html (q=0.8)
       -> MappingJackson2JsonView wins

  5. If NO candidate matches any requested type:
       -> throws HttpMediaTypeNotAcceptableException (406)
```

Because the resolver only *collects and scores* candidates, adding a new representable format is often as simple as adding one more `View` to `setDefaultViews` — no controller or delegate resolver changes needed.

## 4. Diagram

<svg viewBox="0 0 740 240" xmlns="http://www.w3.org/2000/svg" font-family="monospace" font-size="12">
  <rect width="740" height="240" fill="#0d1117"/>
  <text x="370" y="22" text-anchor="middle" fill="#8b949e">ContentNegotiatingViewResolver: collect candidates, score, pick best</text>

  <rect x="20" y="50" width="200" height="130" rx="5" fill="#1c2430" stroke="#8b949e"/>
  <text x="120" y="70" text-anchor="middle" fill="#8b949e" font-size="10">Candidates for "invoice"</text>
  <text x="30" y="95" fill="#6db33f" font-size="10">ThymeleafView</text>
  <text x="30" y="110" fill="#8b949e" font-size="9">text/html</text>
  <text x="30" y="130" fill="#79c0ff" font-size="10">MappingJackson2JsonView</text>
  <text x="30" y="145" fill="#8b949e" font-size="9">application/json</text>
  <text x="30" y="165" fill="#e6edf3" font-size="10">MappingJackson2XmlView</text>
  <text x="30" y="178" fill="#8b949e" font-size="9">application/xml</text>

  <rect x="280" y="50" width="200" height="60" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="380" y="72" text-anchor="middle" fill="#79c0ff" font-size="11">Accept header</text>
  <text x="380" y="90" text-anchor="middle" fill="#8b949e" font-size="10">application/json,</text>
  <text x="380" y="103" text-anchor="middle" fill="#8b949e" font-size="10">text/html;q=0.8</text>

  <line x1="220" y1="130" x2="280" y2="90" stroke="#8b949e" marker-end="url(#a20)"/>
  <line x1="380" y1="110" x2="380" y2="150" stroke="#8b949e" marker-end="url(#a20)"/>

  <rect x="250" y="150" width="260" height="60" rx="5" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="380" y="172" text-anchor="middle" fill="#79c0ff" font-size="11">best match:</text>
  <text x="380" y="190" text-anchor="middle" fill="#e6edf3" font-size="11">MappingJackson2JsonView (q=1.0)</text>

  <defs>
    <marker id="a20" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L0,6 L8,3 z" fill="#8b949e"/>
    </marker>
  </defs>
</svg>

*Every delegate resolver's output and every configured default view become candidates; the highest-scoring one against the request's negotiated media types wins.*

## 5. Runnable example

### Level 1 — Basic

An invoice view resolving to HTML by default, JSON when requested:

```java
// WebConfig.java
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.accept.ContentNegotiationManager;
import org.springframework.web.servlet.ViewResolver;
import org.springframework.web.servlet.view.ContentNegotiatingViewResolver;
import org.springframework.web.servlet.view.json.MappingJackson2JsonView;

import java.util.List;

@Configuration
public class WebConfig {

    @Bean
    public ViewResolver contentNegotiatingViewResolver(ContentNegotiationManager manager) {
        ContentNegotiatingViewResolver resolver = new ContentNegotiatingViewResolver();
        resolver.setContentNegotiationManager(manager);
        resolver.setDefaultViews(List.of(new MappingJackson2JsonView()));
        return resolver;
    }
}
```

```java
// InvoiceController.java
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;

@Controller
public class InvoiceController {

    record Invoice(long id, double total) {}

    @GetMapping("/invoices/{id}")
    public String view(@PathVariable long id, Model model) {
        model.addAttribute("invoice", new Invoice(id, 149.99));
        return "invoice";     // resolved via HTML (Thymeleaf) by default, JSON when negotiated
    }
}
```

`templates/invoice.html`:
```html
<html xmlns:th="http://www.thymeleaf.org">
<body><h1 th:text="'Invoice #' + ${invoice.id}">Invoice</h1></body>
</html>
```

**How to run:**
```bash
./mvnw spring-boot:run

curl -H "Accept: text/html" http://localhost:8080/invoices/1
# <html>...<h1>Invoice #1</h1>...</html>

curl -H "Accept: application/json" http://localhost:8080/invoices/1
# {"invoice":{"id":1,"total":149.99}}
```

The `MappingJackson2JsonView` default view serializes the **entire model map** — here it's `{"invoice": {...}}`, nested under the model attribute name, not the raw `Invoice` object directly. This is a distinct behavior from `@ResponseBody`/`@RestController`, which serializes the returned object itself, not a wrapping model map.

### Level 2 — Intermediate

Explicit media-type-to-view mapping and a `defaultContentType` fallback for ambiguous requests:

```java
// WebConfig.java (extended)
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.MediaType;
import org.springframework.web.accept.ContentNegotiationManager;
import org.springframework.web.servlet.ViewResolver;
import org.springframework.web.servlet.config.annotation.ContentNegotiationConfigurer;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;
import org.springframework.web.servlet.view.ContentNegotiatingViewResolver;
import org.springframework.web.servlet.view.json.MappingJackson2JsonView;
import org.springframework.web.servlet.view.xml.MappingJackson2XmlView;

import java.util.List;

@Configuration
public class WebConfig implements WebMvcConfigurer {

    @Override
    public void configureContentNegotiation(ContentNegotiationConfigurer configurer) {
        configurer
            .favorParameter(false)
            .defaultContentType(MediaType.TEXT_HTML);   // ambiguous/absent Accept -> HTML
    }

    @Bean
    public ViewResolver contentNegotiatingViewResolver(ContentNegotiationManager manager) {
        ContentNegotiatingViewResolver resolver = new ContentNegotiatingViewResolver();
        resolver.setContentNegotiationManager(manager);
        resolver.setDefaultViews(List.of(new MappingJackson2JsonView(), new MappingJackson2XmlView()));
        return resolver;
    }
}
```

```java
// InvoiceController.java — UNCHANGED
```

**How to run:**
```bash
./mvnw spring-boot:run

curl http://localhost:8080/invoices/1
# no Accept header -> defaultContentType(TEXT_HTML) kicks in -> renders HTML

curl -H "Accept: application/xml" http://localhost:8080/invoices/1
# <Map><invoice>...</invoice></Map>-ish XML structure via MappingJackson2XmlView

curl -i -H "Accept: application/pdf" http://localhost:8080/invoices/1
# HTTP/1.1 406 Not Acceptable — no candidate view matches application/pdf
```

**What changed:** `defaultContentType(TEXT_HTML)` gives requests with no (or an unparseable/`*/*`) `Accept` header a predictable fallback, rather than an arbitrary pick among registered views. Adding `MappingJackson2XmlView` to `setDefaultViews` makes XML a third negotiable format with zero controller changes. A request for a genuinely unsupported type (`application/pdf`, not yet wired — see the next card) correctly produces `406`.

### Level 3 — Advanced

Production concern: layering `ContentNegotiatingViewResolver` correctly alongside a dedicated `@RestController` API, and using `useNotAcceptableStatusCode` versus a safer fallback strategy for browser-originated requests with unusual `Accept` headers (some browsers send bizarre wildcard-heavy `Accept` headers that can otherwise trigger unexpected negotiation results):

```java
// WebConfig.java (production version)
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.MediaType;
import org.springframework.web.accept.ContentNegotiationManager;
import org.springframework.web.servlet.config.annotation.ContentNegotiationConfigurer;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;
import org.springframework.web.servlet.view.ContentNegotiatingViewResolver;
import org.springframework.web.servlet.view.json.MappingJackson2JsonView;

import java.util.List;

@Configuration
public class WebConfig implements WebMvcConfigurer {

    @Override
    public void configureContentNegotiation(ContentNegotiationConfigurer configurer) {
        configurer
            .favorParameter(false)
            .defaultContentType(MediaType.TEXT_HTML)   // browsers with weird Accept headers -> safe HTML default
            .mediaType("html", MediaType.TEXT_HTML)
            .mediaType("json", MediaType.APPLICATION_JSON);
    }

    @Bean
    public ContentNegotiatingViewResolver contentNegotiatingViewResolver(ContentNegotiationManager manager) {
        ContentNegotiatingViewResolver resolver = new ContentNegotiatingViewResolver();
        resolver.setContentNegotiationManager(manager);
        resolver.setDefaultViews(List.of(new MappingJackson2JsonView()));
        // If nothing matches, don't 406 for a browser page — fall back to whatever HTML view exists,
        // rather than presenting a confusing blank error for a human visiting in a browser.
        resolver.setUseNotAcceptableStatusCode(false);
        return resolver;
    }
}
```

```java
// InvoiceController.java — server-rendered page (view resolution)
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;

@Controller
public class InvoiceController {

    record Invoice(long id, double total) {}

    @GetMapping("/invoices/{id}")
    public String view(@PathVariable long id, Model model) {
        model.addAttribute("invoice", new Invoice(id, 149.99));
        return "invoice";
    }
}
```

```java
// InvoiceApiController.java — DEDICATED API controller, deliberately SEPARATE
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/invoices")
public class InvoiceApiController {

    record Invoice(long id, double total) {}

    @GetMapping("/{id}")
    public Invoice get(@PathVariable long id) {
        return new Invoice(id, 149.99);   // clean, unwrapped JSON — no model-map nesting
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run

curl -H "Accept: application/json" http://localhost:8080/invoices/1
# {"invoice":{"id":1,"total":149.99}}    <- wrapped in model map, via view resolution

curl http://localhost:8080/api/invoices/1
# {"id":1,"total":149.99}                <- clean, unwrapped, via @RestController
```

**What changed and why:**
- `setUseNotAcceptableStatusCode(false)` changes behavior on a negotiation miss: instead of `406`, the resolver falls back to any view it *can* produce — protecting real browser users (whose `Accept` headers can be surprisingly permissive or malformed) from a confusing blank error page, while API clients hitting the dedicated `@RestController` endpoints get precise, predictable JSON with no such fallback ambiguity.
- The **separate** `InvoiceApiController` under `/api/invoices` exists deliberately alongside content-negotiated view resolution at `/invoices` — for a real API contract, most teams prefer `@RestController`'s clean, unwrapped JSON (`{"id":1,...}`) over `ContentNegotiatingViewResolver`'s model-map-wrapped JSON (`{"invoice":{"id":1,...}}}`), reserving view-resolution-based negotiation for cases where the *same* URL genuinely needs to serve both a browser page and a lightweight secondary format.
- This reflects how most production systems actually use these two mechanisms side by side: `ContentNegotiatingViewResolver` for browser-facing pages with an occasional non-HTML fallback, and dedicated `@RestController`s for anything that's genuinely meant to be a first-class API surface.

## 6. Walkthrough

**Request: `GET /invoices/1` with `Accept: application/json` (Level 3 code, view-resolution path).**

1. `DispatcherServlet` dispatches to `InvoiceController.view(1, model)`. The handler adds `invoice` to the model and returns `"invoice"`.
2. `DispatcherServlet` asks the registered `ContentNegotiatingViewResolver` to resolve `"invoice"`.
3. Internally, the resolver's `ContentNegotiationManager` determines the request's negotiated media types from the `Accept` header: `[application/json]`.
4. It has no explicitly configured delegate `ViewResolver`s in this setup (relying only on autoconfigured ones Spring Boot registers, including Thymeleaf's), so it asks each to resolve `"invoice"` — Thymeleaf's resolver finds `templates/invoice.html`, contributing a `ThymeleafView` candidate (`text/html`).
5. It adds its explicitly configured `defaultViews` — `MappingJackson2JsonView` (`application/json`) — as a further candidate.
6. Scoring: requested `[application/json]` against candidates `[text/html, application/json]` — exact match on `application/json` wins.
7. `MappingJackson2JsonView` is selected and invoked: `view.render(model, request, response)` serializes the **entire model map** (`{"invoice": {"id":1,"total":149.99}}`) to JSON.
8. Response:
   ```
   HTTP/1.1 200 OK
   Content-Type: application/json

   {"invoice":{"id":1,"total":149.99}}
   ```

**Request: `GET /api/invoices/1` (Level 3 code, dedicated `@RestController` path).**

1. `DispatcherServlet` dispatches directly to `InvoiceApiController.get(1)`. Because this class is `@RestController`, there is no view resolution step at all — `ContentNegotiatingViewResolver` is never consulted.
2. The returned `Invoice` record is handed straight to `HttpMessageConverter` selection (the mechanism from the general "Content negotiation" card) — Jackson serializes the `Invoice` object itself, not a wrapping model map.
3. Response:
   ```
   HTTP/1.1 200 OK
   Content-Type: application/json

   {"id":1,"total":149.99}
   ```

The structural difference between these two JSON outputs — wrapped-in-model-map versus clean object — is the single most important practical distinction between `ContentNegotiatingViewResolver`'s JSON fallback and a real `@RestController` JSON endpoint.

## 7. Gotchas & takeaways

> **`ContentNegotiatingViewResolver`'s default JSON/XML views serialize the entire model map, nested under each attribute's name — not a single clean object.** This surprises developers expecting the same output shape as `@RestController`; if a clean, unwrapped JSON contract matters (which it usually does for a real API), use a dedicated `@RestController` instead of relying on this fallback.

> **`setUseNotAcceptableStatusCode(false)` silently falls back to *some* view rather than failing loudly on a genuine negotiation mismatch.** This is the right tradeoff for browser-facing pages but can mask a real client-side bug (a misconfigured `Accept` header) that would otherwise surface as a clear `406` — weigh this tradeoff deliberately rather than disabling it reflexively everywhere.

> **`ContentNegotiatingViewResolver` needs `order` set correctly relative to other registered `ViewResolver`s** — as the highest-priority resolver in most setups (`order = 0` or `Ordered.HIGHEST_PRECEDENCE`), because it needs to see all candidate views from every delegate before making its decision; registering it after another resolver that returns a `View` directly can cause it to never be consulted for some requests.

- `ContentNegotiatingViewResolver` collects candidate `View`s from delegate resolvers plus any explicitly configured default views, then scores them against the request's negotiated media types.
- Its JSON/XML fallback wraps the entire model map — different from `@RestController`'s clean object serialization; use a dedicated REST controller when a clean contract matters.
- Set an explicit `defaultContentType` so ambiguous or missing `Accept` headers behave predictably, especially for browser-originated requests.
- It's common, and often correct, to run content-negotiated view resolution for browser pages alongside a separate, dedicated `@RestController` API for genuine programmatic clients.
