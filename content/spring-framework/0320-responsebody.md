---
card: spring-framework
gi: 320
slug: responsebody
title: "@ResponseBody"
---

## 1. What it is

`@ResponseBody` tells Spring MVC to write the return value of a handler method directly to the HTTP response body using an `HttpMessageConverter`, instead of interpreting it as a view name:

```java
@Controller
public class ProductController {

    @GetMapping("/products/{id}")
    @ResponseBody                          // return value → response body
    public Product getProduct(@PathVariable long id) {
        return new Product(id, "Drill", 29.99);   // serialized to JSON by Jackson
    }
}
```

`@RestController` is `@Controller + @ResponseBody` at the class level — every handler method in the class implicitly has `@ResponseBody`.

---

## 2. Why & when

Use `@ResponseBody` when:
- Building REST API endpoints that return JSON, XML, or other data (not HTML templates).
- Mixing view-rendering handlers and data-returning handlers in the same `@Controller` — annotate individual methods rather than using `@RestController`.
- Returning raw strings, byte arrays, or streaming data from a traditional MVC controller.

Use `@RestController` when the entire controller is a REST API. Use `@ResponseBody` per-method only when the class has a mix of view-rendering and REST methods (rare but valid).

---

## 3. Core concept

```
@GetMapping("/products/{id}")
@ResponseBody
public Product getProduct(@PathVariable long id)

  Handler executes → returns Product{id=1, name="Drill", price=29.99}

  Return value handler: RequestResponseBodyMethodProcessor
    iterates HttpMessageConverter chain
    finds MappingJackson2HttpMessageConverter.canWrite(Product, application/json) = true
      (because Accept: application/json or Accept: */* + Jackson on classpath)
    calls ObjectMapper.writeValue(response.getOutputStream(), product)

  Response:
    HTTP/1.1 200 OK
    Content-Type: application/json
    {"id":1,"name":"Drill","price":29.99}

Without @ResponseBody (in @Controller):
  Spring interprets "Drill" as view name "Drill" → ViewResolver tries to find Drill.html
```

---

## 4. Diagram

<svg viewBox="0 0 740 240" xmlns="http://www.w3.org/2000/svg" font-family="monospace" font-size="12">
  <rect width="740" height="240" fill="#0d1117"/>

  <!-- controller return -->
  <rect x="10" y="50" width="180" height="60" rx="5" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="100" y="70" text-anchor="middle" fill="#79c0ff">Handler returns</text>
  <text x="100" y="86" text-anchor="middle" fill="#e6edf3" font-size="11">Product{id=1,"Drill",29.99}</text>
  <text x="100" y="100" text-anchor="middle" fill="#8b949e" font-size="10">@ResponseBody present</text>

  <line x1="190" y1="80" x2="225" y2="80" stroke="#8b949e" marker-end="url(#arrb)"/>

  <!-- return value handler -->
  <rect x="225" y="30" width="220" height="100" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="335" y="50" text-anchor="middle" fill="#6db33f">RequestResponseBody</text>
  <text x="335" y="65" text-anchor="middle" fill="#6db33f">MethodProcessor</text>
  <text x="235" y="84" fill="#8b949e" font-size="10">iterates HttpMessageConverter chain</text>
  <text x="235" y="99" fill="#8b949e" font-size="10">Accept: application/json → Jackson ✓</text>
  <text x="235" y="114" fill="#8b949e" font-size="10">ObjectMapper.writeValue(stream, obj)</text>

  <!-- no @ResponseBody path (dashed) -->
  <rect x="225" y="150" width="220" height="50" rx="5" fill="#1c2430" stroke="#8b949e" stroke-dasharray="3,2"/>
  <text x="335" y="168" text-anchor="middle" fill="#8b949e">Without @ResponseBody</text>
  <text x="335" y="184" text-anchor="middle" fill="#8b949e" font-size="10">"Drill" → ViewResolver → Drill.html</text>
  <line x1="190" y1="100" x2="225" y2="170" stroke="#8b949e" stroke-dasharray="3,2"/>

  <line x1="445" y1="80" x2="480" y2="80" stroke="#8b949e" marker-end="url(#arrb)"/>

  <!-- response -->
  <rect x="480" y="40" width="240" height="80" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1"/>
  <text x="600" y="60" text-anchor="middle" fill="#6db33f">HTTP Response</text>
  <text x="490" y="78" fill="#8b949e" font-size="10">200 OK</text>
  <text x="490" y="93" fill="#8b949e" font-size="10">Content-Type: application/json</text>
  <text x="490" y="108" fill="#e6edf3" font-size="11">{"id":1,"name":"Drill","price":29.99}</text>

  <text x="370" y="225" text-anchor="middle" fill="#8b949e" font-size="11">@ResponseBody bypasses ViewResolver; converter selected by Accept header + canWrite()</text>

  <defs>
    <marker id="arrb" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L0,6 L8,3 z" fill="#8b949e"/>
    </marker>
  </defs>
</svg>

*Without `@ResponseBody`, string returns are treated as view names; with it, they are written to the response body.*

---

## 5. Runnable example

### Level 1 — Basic

A mixed `@Controller` where one endpoint renders HTML and another returns JSON via `@ResponseBody`:

```java
// ProductController.java
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.*;

@Controller
@RequestMapping("/products")
public class ProductController {

    record Product(long id, String name, double price) {}

    // Renders HTML template
    @GetMapping
    public String list(Model model) {
        model.addAttribute("products", java.util.List.of(
                new Product(1, "Drill", 29.99),
                new Product(2, "Hammer", 14.99)));
        return "products/list";  // → templates/products/list.html
    }

    // Returns JSON directly
    @GetMapping("/{id}")
    @ResponseBody
    public Product getOne(@PathVariable long id) {
        return new Product(id, "Drill", 29.99);
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run

# JSON endpoint
curl -H "Accept: application/json" http://localhost:8080/products/1
# {"id":1,"name":"Drill","price":29.99}

# HTML endpoint (requires template engine; returns view name without @ResponseBody)
curl http://localhost:8080/products
# renders HTML list
```

`@ResponseBody` on `getOne()` routes the return value through Jackson. Without it, `Product{...}` would be coerced to a string and treated as a view name, causing `TemplateInputException`.

---

### Level 2 — Intermediate

Same product API — adding content negotiation: JSON by default, XML when `Accept: application/xml`:

```java
// ProductController.java (extended)
import jakarta.xml.bind.annotation.*;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.*;

@Controller
@RequestMapping("/products")
public class ProductController {

    @XmlRootElement(name = "product")
    @XmlAccessorType(XmlAccessType.FIELD)
    public static class Product {
        public long id;
        public String name;
        public double price;
        Product() {}
        Product(long id, String name, double price) { this.id = id; this.name = name; this.price = price; }
    }

    @GetMapping(value = "/{id}",
                produces = {MediaType.APPLICATION_JSON_VALUE, MediaType.APPLICATION_XML_VALUE})
    @ResponseBody
    public Product getOne(@PathVariable long id) {
        return new Product(id, "Drill", 29.99);
    }
}
```

Add JAXB to `pom.xml`:
```xml
<dependency>
    <groupId>org.glassfish.jaxb</groupId>
    <artifactId>jaxb-runtime</artifactId>
</dependency>
```

**How to run:**
```bash
./mvnw spring-boot:run

# JSON (default)
curl -H "Accept: application/json" http://localhost:8080/products/1
# {"id":1,"name":"Drill","price":29.99}

# XML
curl -H "Accept: application/xml" http://localhost:8080/products/1
# <?xml version="1.0"?><product><id>1</id><name>Drill</name><price>29.99</price></product>

# Not acceptable
curl -H "Accept: text/plain" http://localhost:8080/products/1
# 406 Not Acceptable
```

**What changed:** `produces` restricts which media types this handler serves. `@ResponseBody` routes through `Jaxb2RootElementHttpMessageConverter` when `Accept: application/xml` is negotiated, and through Jackson for JSON. 406 is returned when the client's `Accept` doesn't match `produces`.

---

### Level 3 — Advanced

Production scenario: `@Controller` with a mix of server-side rendered pages and REST endpoints, plus `@ResponseBody` on an SSE streaming endpoint and a binary download:

```java
// ProductController.java (production mix)
import org.springframework.http.*;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;
import java.io.*;
import java.util.*;
import java.util.concurrent.*;

@Controller
@RequestMapping("/products")
public class ProductController {

    private final List<SseEmitter> listeners = new CopyOnWriteArrayList<>();

    // Renders Thymeleaf page
    @GetMapping
    public String list(Model model) {
        model.addAttribute("count", 2);
        return "products/list";
    }

    // REST JSON API
    @GetMapping("/{id}")
    @ResponseBody
    public Map<String, Object> getOne(@PathVariable long id) {
        return Map.of("id", id, "name", "Drill", "price", 29.99);
    }

    // SSE stream of product events
    @GetMapping(value = "/events", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
    @ResponseBody
    public SseEmitter stream() {
        SseEmitter emitter = new SseEmitter(30_000L);
        listeners.add(emitter);
        emitter.onCompletion(() -> listeners.remove(emitter));
        emitter.onTimeout(() -> listeners.remove(emitter));
        return emitter;
    }

    // Binary CSV export — byte[] with ResponseBody sets Content-Type
    @GetMapping(value = "/export.csv", produces = "text/csv")
    @ResponseBody
    public byte[] export() {
        String csv = "id,name,price\n1,Drill,29.99\n2,Hammer,14.99\n";
        return csv.getBytes();
    }

    // Simulate product event (called by POST /products/emit)
    @PostMapping("/emit")
    @ResponseBody
    public String emitEvent(@RequestParam String msg) {
        listeners.forEach(emitter -> {
            try { emitter.send(msg); }
            catch (IOException e) { listeners.remove(emitter); }
        });
        return "sent to " + listeners.size() + " listeners";
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run

# JSON API
curl http://localhost:8080/products/1
# {"id":1,"name":"Drill","price":29.99}

# SSE stream (keep this open in one terminal)
curl -N -H "Accept: text/event-stream" http://localhost:8080/products/events &

# Emit an event to all SSE subscribers
curl -X POST "http://localhost:8080/products/emit?msg=product.updated"
# data:product.updated  ← appears in SSE subscriber terminal

# Binary CSV download
curl http://localhost:8080/products/export.csv
# id,name,price
# 1,Drill,29.99
# 2,Hammer,14.99
```

**What changed and why:**
- `SseEmitter` returned with `@ResponseBody` writes the `text/event-stream` response incrementally — Spring keeps the connection open until `emitter.complete()` or timeout.
- `byte[]` return with `produces = "text/csv"` uses `ByteArrayHttpMessageConverter` — Spring sets `Content-Type: text/csv` and writes the bytes directly.
- The page-rendering `list()` method has no `@ResponseBody` — returns `"products/list"` as a view name, resolved by Thymeleaf.
- All REST methods have `@ResponseBody`; one page endpoint does not — a legitimate mixed `@Controller` pattern.

<svg viewBox="0 0 700 190" xmlns="http://www.w3.org/2000/svg" font-family="monospace" font-size="11">
  <rect width="700" height="190" fill="#0d1117"/>
  <text x="350" y="20" text-anchor="middle" fill="#8b949e">Mixed @Controller — @ResponseBody per method</text>

  <!-- list() -->
  <rect x="20" y="35" width="155" height="45" rx="4" fill="#1c2430" stroke="#8b949e"/>
  <text x="97" y="55" text-anchor="middle" fill="#8b949e">GET /products</text>
  <text x="97" y="70" text-anchor="middle" fill="#8b949e" font-size="10">no @ResponseBody → ViewResolver</text>

  <!-- getOne() -->
  <rect x="190" y="35" width="155" height="45" rx="4" fill="#1c2430" stroke="#6db33f"/>
  <text x="267" y="55" text-anchor="middle" fill="#6db33f">GET /products/{id}</text>
  <text x="267" y="70" text-anchor="middle" fill="#6db33f" font-size="10">@ResponseBody → JSON</text>

  <!-- SSE -->
  <rect x="360" y="35" width="155" height="45" rx="4" fill="#1c2430" stroke="#79c0ff"/>
  <text x="437" y="55" text-anchor="middle" fill="#79c0ff">GET /products/events</text>
  <text x="437" y="70" text-anchor="middle" fill="#79c0ff" font-size="10">@ResponseBody → SSE stream</text>

  <!-- CSV -->
  <rect x="530" y="35" width="155" height="45" rx="4" fill="#1c2430" stroke="#6db33f"/>
  <text x="607" y="55" text-anchor="middle" fill="#6db33f">GET /export.csv</text>
  <text x="607" y="70" text-anchor="middle" fill="#6db33f" font-size="10">@ResponseBody → byte[]</text>

  <!-- converters row -->
  <rect x="190" y="110" width="155" height="30" rx="3" fill="#1c2430" stroke="#6db33f"/>
  <text x="267" y="129" text-anchor="middle" fill="#6db33f" font-size="10">MappingJackson2</text>

  <rect x="360" y="110" width="155" height="30" rx="3" fill="#1c2430" stroke="#79c0ff"/>
  <text x="437" y="129" text-anchor="middle" fill="#79c0ff" font-size="10">SseEmitter (streaming)</text>

  <rect x="530" y="110" width="155" height="30" rx="3" fill="#1c2430" stroke="#6db33f"/>
  <text x="607" y="129" text-anchor="middle" fill="#6db33f" font-size="10">ByteArrayConverter</text>

  <line x1="267" y1="80" x2="267" y2="110" stroke="#6db33f" stroke-dasharray="2,2"/>
  <line x1="437" y1="80" x2="437" y2="110" stroke="#79c0ff" stroke-dasharray="2,2"/>
  <line x1="607" y1="80" x2="607" y2="110" stroke="#6db33f" stroke-dasharray="2,2"/>
  <text x="350" y="170" text-anchor="middle" fill="#8b949e" font-size="10">Same @Controller; @ResponseBody selects converter; no @ResponseBody goes to ViewResolver</text>
</svg>

---

## 6. Walkthrough

**Per-request: `GET /products/1` with `Accept: application/json`:**

1. `DispatcherServlet` routes to `getOne(1)`.
2. Handler executes → returns `Map{id:1, name:"Drill", price:29.99}`.
3. `RequestResponseBodyMethodProcessor.handleReturnValue()` triggered (because `@ResponseBody` present).
4. Iterates `HttpMessageConverter` chain, checking `canWrite(Map.class, application/json)`.
5. `MappingJackson2HttpMessageConverter.canWrite(...)` → true.
6. `objectMapper.writeValue(response.getOutputStream(), returnValue)`.
7. Response `Content-Type` set to `application/json`.
8. Response committed: `200 OK`, JSON body.

**Without `@ResponseBody` on the same method:**

Step 3: `ViewNameMethodReturnValueHandler` handles the return value, coerces `Map` to its `toString()` → tries to resolve that as a view name → `TemplateInputException: template not found`.

---

## 7. Gotchas & takeaways

> **`@RestController` = `@Controller + @ResponseBody` at the class level.** All methods in a `@RestController` have `@ResponseBody` implicitly — you cannot opt individual methods out to render views.

> **`void` or `null` return with `@ResponseBody` writes an empty body.** The response is committed with the status code and no body. Use `ResponseEntity` if you need to set headers or status alongside an empty body.

> **Content negotiation uses `Accept` header first, then `produces` narrowing.** If `Accept: */*` and no `produces` constraint, the first converter that can write the type wins — typically Jackson for POJOs.

- `@ResponseBody` → `RequestResponseBodyMethodProcessor` → `HttpMessageConverter.canWrite()` → serialize.
- `@RestController` = shortcut; `@ResponseBody` per method for mixed controllers.
- Converter selected by `Accept` header + `canWrite(returnType, mediaType)`.
- `SseEmitter` and `byte[]` work with `@ResponseBody` — correct converter chosen by type and `produces`.
- No `@ResponseBody` on a `String` return → ViewResolver treats it as a template name.
