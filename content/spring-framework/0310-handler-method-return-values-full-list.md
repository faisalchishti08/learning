---
card: spring-framework
gi: 310
slug: handler-method-return-values-full-list
title: "Handler method return values (full list)"
---

## 1. What it is

Spring MVC's `HandlerMethodReturnValueHandler` chain processes whatever a controller method returns and turns it into an HTTP response. The full set of supported return types:

**View-based (controller returns a view name or object)**
- `String` — logical view name (e.g. `"users/list"`)
- `ModelAndView` — view name + model in one object
- `View` — a concrete `View` implementation
- `void` — response written directly (via `HttpServletResponse`), or `null` view name

**Body-writing (serialised to response body)**
- `@ResponseBody` + any Object — serialised via `HttpMessageConverter`
- `ResponseEntity<T>` — full control over status + headers + body
- `HttpEntity<T>` — headers + body (no status code; inherits 200)
- `ResponseBodyEmitter` / `SseEmitter` — streaming responses (Server-Sent Events)
- `StreamingResponseBody` — low-level async streaming

**Async**
- `Callable<T>` — executed on a separate thread pool
- `CompletableFuture<T>` / `ListenableFuture<T>` — non-blocking async
- `DeferredResult<T>` — resolved from any thread (e.g. after DB callback)
- Reactive types: `Mono<T>` / `Flux<T>` (with `spring-webflux` on classpath)

**Redirect**
- `"redirect:/path"` — 302 redirect
- `"forward:/path"` — server-side forward

**Special**
- `HttpHeaders` — response with headers only, no body

---

## 2. Why & when

Choose the return type that matches what you actually need:

| Need | Use |
|---|---|
| HTML page | `String` (view name) |
| JSON/XML body with full control | `ResponseEntity<T>` |
| Simple JSON/XML | `@ResponseBody` Object |
| Streaming events | `SseEmitter` |
| Async without blocking servlet thread | `Callable` or `DeferredResult` |
| Redirect | `"redirect:/..."` |

`ResponseEntity<T>` is the most versatile — it sets status code, headers, and body in one return. Use plain `@ResponseBody` Object when 200 OK with default headers is always the right response.

---

## 3. Core concept

```
Handler returns → HandlerMethodReturnValueHandler chain:

  ViewNameMethodReturnValueHandler      handles: String (view name)
  ModelAndViewMethodReturnValueHandler  handles: ModelAndView
  ResponseBodyEmitterReturnValueHandler handles: ResponseBodyEmitter, SseEmitter
  HttpEntityMethodProcessor             handles: ResponseEntity, HttpEntity
  RequestResponseBodyMethodProcessor    handles: @ResponseBody Object
  ViewMethodReturnValueHandler          handles: View
  CallableMethodReturnValueHandler      handles: Callable
  DeferredResultMethodReturnValueHandler handles: DeferredResult
  … 20+ total handlers

First handler that supports the return type processes it and writes the response.
```

---

## 4. Diagram

<svg viewBox="0 0 740 300" xmlns="http://www.w3.org/2000/svg" font-family="monospace" font-size="12">
  <rect width="740" height="300" fill="#0d1117"/>

  <!-- controller -->
  <rect x="10" y="130" width="120" height="40" rx="5" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="70" y="148" text-anchor="middle" fill="#79c0ff">Controller</text>
  <text x="70" y="163" text-anchor="middle" fill="#8b949e" font-size="10">returns value</text>

  <line x1="130" y1="150" x2="170" y2="150" stroke="#8b949e" marker-end="url(#arv)"/>

  <!-- return value handler chain -->
  <rect x="170" y="50" width="310" height="200" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1"/>
  <text x="325" y="70" text-anchor="middle" fill="#6db33f" font-weight="bold">ReturnValueHandler chain</text>
  <rect x="180" y="78" width="290" height="20" rx="3" fill="#0d1117" stroke="#6db33f"/>
  <text x="325" y="92" text-anchor="middle" fill="#6db33f" font-size="10">ViewNameHandler → String "users/list"</text>
  <rect x="180" y="102" width="290" height="20" rx="3" fill="#0d1117" stroke="#6db33f"/>
  <text x="325" y="116" text-anchor="middle" fill="#6db33f" font-size="10">HttpEntityProcessor → ResponseEntity&lt;T&gt;</text>
  <rect x="180" y="126" width="290" height="20" rx="3" fill="#0d1117" stroke="#6db33f"/>
  <text x="325" y="140" text-anchor="middle" fill="#6db33f" font-size="10">@ResponseBody → Object via MessageConverter</text>
  <rect x="180" y="150" width="290" height="20" rx="3" fill="#0d1117" stroke="#8b949e"/>
  <text x="325" y="164" text-anchor="middle" fill="#8b949e" font-size="10">SseEmitter / StreamingResponseBody</text>
  <rect x="180" y="174" width="290" height="20" rx="3" fill="#0d1117" stroke="#8b949e"/>
  <text x="325" y="188" text-anchor="middle" fill="#8b949e" font-size="10">Callable / DeferredResult / CompletableFuture</text>
  <rect x="180" y="198" width="290" height="20" rx="3" fill="#0d1117" stroke="#8b949e"/>
  <text x="325" y="212" text-anchor="middle" fill="#8b949e" font-size="10">ModelAndView / View / void … 20+ total</text>

  <!-- output paths -->
  <line x1="480" y1="100" x2="530" y2="80" stroke="#6db33f" stroke-dasharray="3,2" marker-end="url(#arv)"/>
  <rect x="530" y="60" width="190" height="28" rx="3" fill="#1c2430" stroke="#6db33f"/>
  <text x="625" y="78" text-anchor="middle" fill="#6db33f" font-size="10">→ ViewResolver → HTML response</text>

  <line x1="480" y1="130" x2="530" y2="130" stroke="#6db33f" stroke-dasharray="3,2" marker-end="url(#arv)"/>
  <rect x="530" y="116" width="190" height="28" rx="3" fill="#1c2430" stroke="#6db33f"/>
  <text x="625" y="134" text-anchor="middle" fill="#6db33f" font-size="10">→ status + headers + JSON body</text>

  <line x1="480" y1="155" x2="530" y2="165" stroke="#8b949e" stroke-dasharray="3,2" marker-end="url(#arv)"/>
  <rect x="530" y="152" width="190" height="28" rx="3" fill="#1c2430" stroke="#8b949e"/>
  <text x="625" y="170" text-anchor="middle" fill="#8b949e" font-size="10">→ streaming / async response</text>

  <text x="370" y="270" text-anchor="middle" fill="#8b949e" font-size="11">First matching handler processes the return value — handlers are checked in registration order</text>

  <defs>
    <marker id="arv" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L0,6 L8,3 z" fill="#8b949e"/>
    </marker>
  </defs>
</svg>

*Different return types wire to different handlers — pick the type that expresses your intent precisely.*

---

## 5. Runnable example

### Level 1 — Basic

Three methods showing the most common return types:

```java
// ProductController.java
import org.springframework.http.*;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.*;
import java.util.Map;

@Controller
@RequestMapping("/products")
public class ProductController {

    // String → view name → HTML via ThymeleafViewResolver
    @GetMapping("/{id}")
    public String detail(@PathVariable long id, Model model) {
        model.addAttribute("name", "Widget #" + id);
        return "products/detail"; // logical view name
    }

    // ResponseEntity → full control over status + headers + JSON body
    @GetMapping(value = "/{id}/json", produces = MediaType.APPLICATION_JSON_VALUE)
    @ResponseBody
    public ResponseEntity<Map<String, Object>> detailJson(@PathVariable long id) {
        return ResponseEntity.ok()
                .header("X-Product-Id", String.valueOf(id))
                .body(Map.of("id", id, "name", "Widget #" + id));
    }

    // void — writes response directly; no view, no body return
    @GetMapping("/{id}/download")
    public void download(@PathVariable long id,
                         jakarta.servlet.http.HttpServletResponse response) throws Exception {
        response.setContentType("text/plain");
        response.getWriter().write("Product data for " + id);
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run

curl http://localhost:8080/products/1/json
# {"id":1,"name":"Widget #1"}
# Header: X-Product-Id: 1

curl http://localhost:8080/products/1/download
# Product data for 1
```

`String` → `ViewNameMethodReturnValueHandler` passes it to `ViewResolver`. `ResponseEntity<Map<...>>` → `HttpEntityMethodProcessor` sets status 200, copies headers, and hands the body to `MappingJackson2HttpMessageConverter`. `void` with `HttpServletResponse` parameter → handler assumes the response was written manually.

---

### Level 2 — Intermediate

Same product scenario — adding `ModelAndView` for combined model+view in one return, and `"redirect:"` for the POST/Redirect/GET pattern:

```java
// ProductController.java (extended)
import org.springframework.web.servlet.ModelAndView;
import org.springframework.web.servlet.mvc.support.RedirectAttributes;

@Controller
@RequestMapping("/products")
public class ProductController {

    // ModelAndView — model and view name in one return
    @GetMapping("/{id}/full")
    public ModelAndView fullDetail(@PathVariable long id) {
        ModelAndView mav = new ModelAndView("products/full-detail");
        mav.addObject("id", id);
        mav.addObject("name", "Widget #" + id);
        mav.addObject("stock", 42);
        return mav;
    }

    // POST → redirect (PRG pattern) with flash message
    @PostMapping
    public String create(@RequestParam String name, RedirectAttributes attrs) {
        long newId = 99L; // simulate save
        attrs.addFlashAttribute("successMsg", "Created: " + name);
        return "redirect:/products/" + newId + "/full";
    }

    // ResponseEntity with 201 + Location header
    @PostMapping(value = "/api", consumes = MediaType.APPLICATION_JSON_VALUE,
                 produces = MediaType.APPLICATION_JSON_VALUE)
    @ResponseBody
    public ResponseEntity<Map<String, Object>> createApi(
            @RequestBody Map<String, Object> body,
            org.springframework.web.util.UriComponentsBuilder uriBuilder) {
        long newId = 99L;
        var location = uriBuilder.path("/products/{id}/json").buildAndExpand(newId).toUri();
        return ResponseEntity.created(location).body(Map.of("id", newId, "name", body.get("name")));
    }
}
```

**How to run:**
```bash
curl http://localhost:8080/products/1/full
# renders products/full-detail.html with id, name, stock

curl -X POST -d "name=Gadget" http://localhost:8080/products
# 302 → /products/99/full  (flash: "Created: Gadget")

curl -X POST -H "Content-Type: application/json" \
     -d '{"name":"Gadget"}' http://localhost:8080/products/api
# 201 Created  Location: http://localhost:8080/products/99/json
# {"id":99,"name":"Gadget"}
```

**What changed:** `ModelAndView` lets you set the model in one object without injecting `Model` as a parameter — useful when the view name or model is computed dynamically. `"redirect:/..."` triggers `302`; flash attributes survive the redirect via session. `ResponseEntity.created(uri)` is the idiomatic way to return `201 Created` with a `Location` header.

---

### Level 3 — Advanced

Production scenario: `SseEmitter` for Server-Sent Events (real-time stock price stream) and `DeferredResult` for long-polling:

```java
// PriceController.java
import org.springframework.http.*;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.context.request.async.DeferredResult;
import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;
import java.util.Map;
import java.util.concurrent.*;

@RestController
@RequestMapping("/api/prices")
public class PriceController {

    // Server-Sent Events — push price updates to client
    @GetMapping(value = "/stream", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
    public SseEmitter streamPrices() {
        SseEmitter emitter = new SseEmitter(30_000L); // 30 s timeout

        CompletableFuture.runAsync(() -> {
            try {
                for (int i = 0; i < 5; i++) {
                    double price = 100.0 + ThreadLocalRandom.current().nextDouble(-5, 5);
                    emitter.send(SseEmitter.event()
                            .id(String.valueOf(i))
                            .name("price")
                            .data(Map.of("symbol", "WIDG", "price", String.format("%.2f", price))));
                    Thread.sleep(500);
                }
                emitter.complete();
            } catch (Exception e) {
                emitter.completeWithError(e);
            }
        });

        return emitter; // servlet thread released immediately
    }

    // Long-polling — resolves when price changes (simulated after 1 s)
    @GetMapping("/poll")
    public DeferredResult<ResponseEntity<Map<String, Object>>> pollPrice() {
        DeferredResult<ResponseEntity<Map<String, Object>>> result = new DeferredResult<>(5_000L,
                ResponseEntity.status(HttpStatus.NO_CONTENT).build()); // timeout → 204

        CompletableFuture.delayedExecutor(1, TimeUnit.SECONDS).execute(() ->
                result.setResult(ResponseEntity.ok(Map.of("symbol", "WIDG", "price", "102.50"))));

        return result; // servlet thread released immediately
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run

# SSE stream — receive 5 price events then done
curl -N http://localhost:8080/api/prices/stream
# id:0
# event:price
# data:{"symbol":"WIDG","price":"101.23"}
#
# id:1
# event:price
# data:{"symbol":"WIDG","price":"99.87"}
# … (5 events then connection closes)

# Long-poll — waits up to 5 s for a price update
curl http://localhost:8080/api/prices/poll
# {"symbol":"WIDG","price":"102.50"}  (after ~1 s)
```

**What changed and why:**
- `SseEmitter` returns immediately, releasing the servlet thread. A background thread sends events via `emitter.send()`. The client keeps the connection open and receives events as they arrive — no polling needed.
- `DeferredResult` similarly releases the servlet thread. The result is set from a background thread (here a delayed executor, in production from a message queue callback). If not resolved within 5 s, the timeout result (`204 No Content`) is sent automatically.
- `produces = MediaType.TEXT_EVENT_STREAM_VALUE` tells browsers and proxies this is an SSE stream — required for the `EventSource` API to work.

<svg viewBox="0 0 700 190" xmlns="http://www.w3.org/2000/svg" font-family="monospace" font-size="11">
  <rect width="700" height="190" fill="#0d1117"/>
  <!-- SseEmitter flow -->
  <rect x="10" y="30" width="100" height="30" rx="4" fill="#1c2430" stroke="#79c0ff"/>
  <text x="60" y="49" text-anchor="middle" fill="#79c0ff">GET /stream</text>
  <line x1="110" y1="45" x2="145" y2="45" stroke="#8b949e" marker-end="url(#arv2)"/>
  <rect x="145" y="30" width="130" height="30" rx="4" fill="#1c2430" stroke="#6db33f"/>
  <text x="210" y="49" text-anchor="middle" fill="#6db33f">SseEmitter created</text>
  <line x1="275" y1="45" x2="310" y2="45" stroke="#8b949e" marker-end="url(#arv2)"/>
  <rect x="310" y="30" width="130" height="30" rx="4" fill="#1c2430" stroke="#6db33f"/>
  <text x="375" y="48" text-anchor="middle" fill="#6db33f">servlet thread</text>
  <text x="375" y="62" text-anchor="middle" fill="#6db33f">released immediately</text>
  <!-- async push -->
  <rect x="145" y="90" width="130" height="30" rx="4" fill="#1c2430" stroke="#8b949e"/>
  <text x="210" y="109" text-anchor="middle" fill="#8b949e">background thread</text>
  <line x1="210" y1="60" x2="210" y2="90" stroke="#8b949e" stroke-dasharray="3,2"/>
  <line x1="275" y1="105" x2="310" y2="105" stroke="#8b949e" marker-end="url(#arv2)"/>
  <rect x="310" y="90" width="130" height="30" rx="4" fill="#1c2430" stroke="#8b949e"/>
  <text x="375" y="109" text-anchor="middle" fill="#8b949e">emitter.send(event)</text>
  <line x1="440" y1="105" x2="475" y2="105" stroke="#8b949e" marker-end="url(#arv2)"/>
  <rect x="475" y="90" width="100" height="30" rx="4" fill="#1c2430" stroke="#79c0ff"/>
  <text x="525" y="109" text-anchor="middle" fill="#79c0ff">client receives</text>
  <text x="350" y="165" text-anchor="middle" fill="#8b949e" font-size="10">Servlet thread released after return — background thread pushes events asynchronously</text>
  <defs><marker id="arv2" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L0,6 L8,3 z" fill="#8b949e"/></marker></defs>
</svg>

---

## 6. Walkthrough

**Per-request: `GET /api/prices/stream`:**

1. `DispatcherServlet.doDispatch()` calls `streamPrices()`.
2. `SseEmitter` is constructed with a 30 s timeout.
3. `CompletableFuture.runAsync()` submits the price-sending loop to the ForkJoinPool — does not block.
4. `streamPrices()` returns the `SseEmitter` immediately.
5. `ResponseBodyEmitterReturnValueHandler` detects the `SseEmitter` return type.
6. It sets `Content-Type: text/event-stream`, writes headers, and registers the emitter with the servlet's async context — the servlet thread is released to the pool.
7. The background thread runs the loop: calls `emitter.send(event)` 5 times with 500 ms pauses. Each `send()` writes an SSE frame to the open response stream.
8. After 5 events: `emitter.complete()` — the async context is finalized, connection closed.

**Per-request: `GET /api/prices/poll`:**

1. `DeferredResult` created with 5 s timeout; timeout result is `204 No Content`.
2. `DelayedExecutor` schedules `result.setResult(...)` after 1 s.
3. `pollPrice()` returns the `DeferredResult` immediately.
4. `DeferredResultMethodReturnValueHandler` registers the result with the servlet's async context; servlet thread released.
5. After 1 s: delayed executor calls `result.setResult(ResponseEntity.ok(...))`.
6. Spring's async support writes `200 OK` + JSON body to the response and closes the connection.

**State changes:**

| Stage | Servlet thread | Response |
|---|---|---|
| Method returns | released | headers sent (chunked) |
| Background sends | free for other requests | SSE frames / body written |
| complete() / setResult() | (unused) | connection closed |

---

## 7. Gotchas & takeaways

> **`void` return does not mean "no response" — it means "response already written."**  If you return `void` without writing anything to `HttpServletResponse`, the client receives an empty `200 OK`. Intentional in controllers that call `response.sendRedirect()` or stream bytes themselves.

> **`SseEmitter` and `DeferredResult` release the servlet thread — but you need async support enabled.**  Add `spring.mvc.async.request-timeout` and ensure your servlet container has async enabled (default in Spring Boot's embedded Tomcat).  Without `asyncSupported=true`, returning an `SseEmitter` throws `IllegalStateException`.

> **`ResponseEntity` with `null` body still sends the status code and headers.**  `ResponseEntity.noContent().build()` sends `204` with no body — correct for DELETE. Don't return `ResponseEntity.ok(null)` expecting an empty body; it may try to serialize `null` and throw `HttpMessageConversionException`.

- `String` → view name when returned from `@Controller`; plain text body when returned from `@RestController` (because `@ResponseBody` is implicit).
- `ResponseEntity<T>` gives full control: status + headers + body in one object.
- `SseEmitter` = push events from server; `DeferredResult` = resolve once from any thread; both release the servlet thread immediately.
- `ModelAndView` is the old-school way to combine model + view — `Model` parameter + String return is cleaner in modern code.
- `"redirect:/path"` → `302`; `"redirect:{uri}"` with `RedirectAttributes` → flash attributes survive the redirect.
