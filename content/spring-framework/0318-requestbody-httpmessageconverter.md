---
card: spring-framework
gi: 318
slug: requestbody-httpmessageconverter
title: "@RequestBody & HttpMessageConverter"
---

## 1. What it is

`@RequestBody` reads the HTTP request body and binds it to a method parameter by delegating to a chain of `HttpMessageConverter` implementations. The converter is chosen by matching the request's `Content-Type` header to what each converter `canRead()`:

```java
@PostMapping("/products")
public Product create(@RequestBody @Valid ProductRequest req) { ... }
// Content-Type: application/json → MappingJackson2HttpMessageConverter
// Content-Type: application/xml  → Jaxb2RootElementHttpMessageConverter
```

Spring auto-registers converters based on classpath presence (Jackson, JAXB, etc.). You can add custom converters or override Jackson's `ObjectMapper` via `WebMvcConfigurer.extendMessageConverters()`.

---

## 2. Why & when

Use `@RequestBody` for:
- REST API endpoints receiving JSON or XML payloads.
- Any endpoint where the client sends a structured body (`Content-Type: application/json`).
- Binary uploads where a custom converter reads raw bytes or streams.

Do **not** use `@RequestBody` for HTML form submissions (`application/x-www-form-urlencoded`) — use `@ModelAttribute` instead. `@RequestBody` reads the body stream once; mixing it with form parameter resolution is not supported.

---

## 3. Core concept

```
POST /products
Content-Type: application/json
{"name":"Drill","price":29.99}

  ↓
DispatcherServlet → HandlerAdapter
  → finds parameter annotated @RequestBody
  → iterates HttpMessageConverter chain:
      ByteArrayHttpMessageConverter   — canRead(byte[], application/octet-stream)? No
      StringHttpMessageConverter      — canRead(String, text/plain)?               No (JSON body)
      MappingJackson2HttpMessageConverter
                                      — canRead(ProductRequest, application/json)? YES
        → ObjectMapper.readValue(body, ProductRequest.class)
        → returns ProductRequest{name="Drill", price=29.99}
  → @Valid runs Bean Validation
  → method receives ProductRequest instance
```

---

## 4. Diagram

<svg viewBox="0 0 740 260" xmlns="http://www.w3.org/2000/svg" font-family="monospace" font-size="12">
  <rect width="740" height="260" fill="#0d1117"/>

  <!-- request -->
  <rect x="10" y="40" width="180" height="60" rx="5" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="100" y="60" text-anchor="middle" fill="#79c0ff">HTTP Request</text>
  <text x="100" y="76" text-anchor="middle" fill="#8b949e" font-size="10">Content-Type: application/json</text>
  <text x="100" y="90" text-anchor="middle" fill="#8b949e" font-size="10">{"name":"Drill","price":29.99}</text>

  <line x1="190" y1="70" x2="225" y2="70" stroke="#8b949e" marker-end="url(#arb)"/>

  <!-- converter chain -->
  <rect x="225" y="20" width="240" height="120" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="345" y="40" text-anchor="middle" fill="#6db33f">HttpMessageConverter chain</text>
  <text x="235" y="60" fill="#8b949e" font-size="10">ByteArrayHttpMessageConverter   ✗</text>
  <text x="235" y="76" fill="#8b949e" font-size="10">StringHttpMessageConverter      ✗</text>
  <text x="235" y="92" fill="#8b949e" font-size="10">ResourceHttpMessageConverter    ✗</text>
  <text x="235" y="108" fill="#6db33f" font-size="10">MappingJackson2HttpMessageConverter ✓</text>
  <text x="235" y="124" fill="#8b949e" font-size="10">  → ObjectMapper.readValue()</text>

  <line x1="465" y1="80" x2="500" y2="80" stroke="#8b949e" marker-end="url(#arb)"/>

  <!-- bound object -->
  <rect x="500" y="40" width="220" height="80" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1"/>
  <text x="610" y="60" text-anchor="middle" fill="#6db33f">ProductRequest</text>
  <text x="510" y="78" fill="#e6edf3" font-size="11">name  = "Drill"</text>
  <text x="510" y="94" fill="#e6edf3" font-size="11">price = 29.99</text>
  <text x="510" y="110" fill="#8b949e" font-size="10">@Valid → ConstraintViolation if invalid</text>

  <!-- validation error -->
  <rect x="340" y="170" width="220" height="50" rx="5" fill="#1c2430" stroke="#e74c3c" stroke-dasharray="3,2"/>
  <text x="450" y="190" text-anchor="middle" fill="#e74c3c">@Valid fails</text>
  <text x="450" y="206" text-anchor="middle" fill="#8b949e" font-size="10">MethodArgumentNotValidException → 400</text>

  <text x="370" y="250" text-anchor="middle" fill="#8b949e" font-size="11">Converter chosen by canRead(Class, MediaType) — first match wins; missing converter → 415</text>

  <defs>
    <marker id="arb" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L0,6 L8,3 z" fill="#8b949e"/>
    </marker>
  </defs>
</svg>

*`HttpMessageConverter.canRead()` checks both the target type and the `Content-Type` — first match in the chain wins.*

---

## 5. Runnable example

### Level 1 — Basic

A product creation endpoint that reads JSON via `@RequestBody`:

```java
// ProductController.java
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/products")
public class ProductController {

    record ProductRequest(String name, double price) {}
    record ProductResponse(long id, String name, double price) {}

    @PostMapping
    public ProductResponse create(@RequestBody ProductRequest req) {
        long id = System.currentTimeMillis() % 100000;
        return new ProductResponse(id, req.name(), req.price());
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run

curl -X POST http://localhost:8080/products \
     -H "Content-Type: application/json" \
     -d '{"name":"Drill","price":29.99}'
# {"id":12345,"name":"Drill","price":29.99}

# Missing Content-Type header → 415 Unsupported Media Type
curl -X POST http://localhost:8080/products -d '{"name":"Drill","price":29.99}'
```

`MappingJackson2HttpMessageConverter` matches `application/json` and deserialises the body. Without `Content-Type: application/json`, Spring cannot select a converter and returns 415.

---

### Level 2 — Intermediate

Same product scenario — adding Bean Validation, `@ExceptionHandler` for 400 responses, and a custom deserializer:

```java
// ProductController.java (extended)
import jakarta.validation.*;
import jakarta.validation.constraints.*;
import org.springframework.http.*;
import org.springframework.validation.FieldError;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.*;
import java.util.*;

@RestController
@RequestMapping("/products")
public class ProductController {

    record ProductRequest(
            @NotBlank String name,
            @Positive double price,
            @Size(max = 200) String description) {}

    record ProductResponse(long id, String name, double price) {}

    @PostMapping
    public ResponseEntity<ProductResponse> create(@RequestBody @Valid ProductRequest req) {
        long id = System.currentTimeMillis() % 100000;
        return ResponseEntity.status(HttpStatus.CREATED)
                .body(new ProductResponse(id, req.name(), req.price()));
    }

    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<Map<String, String>> handleValidation(
            MethodArgumentNotValidException ex) {
        Map<String, String> errors = new LinkedHashMap<>();
        for (FieldError fe : ex.getBindingResult().getFieldErrors()) {
            errors.put(fe.getField(), fe.getDefaultMessage());
        }
        return ResponseEntity.badRequest().body(errors);
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run

# Valid request → 201 Created
curl -X POST http://localhost:8080/products \
     -H "Content-Type: application/json" \
     -d '{"name":"Drill","price":29.99,"description":"Cordless"}'
# HTTP/1.1 201 Created  {"id":...,"name":"Drill","price":29.99}

# Invalid request → 400 with field errors
curl -X POST http://localhost:8080/products \
     -H "Content-Type: application/json" \
     -d '{"name":"","price":-5}'
# {"name":"must not be blank","price":"must be greater than 0"}
```

**What changed:** `@Valid` triggers JSR-303 validation after deserialization. A blank name or negative price throws `MethodArgumentNotValidException`, caught by `@ExceptionHandler` to return a structured 400 body.

---

### Level 3 — Advanced

Production scenario: custom `HttpMessageConverter` for a proprietary binary format, plus Jackson `ObjectMapper` customization for strict unknown-field handling:

```java
// BinaryProductConverter.java
import org.springframework.http.*;
import org.springframework.http.converter.AbstractHttpMessageConverter;
import java.io.*;
import java.nio.ByteBuffer;

public class BinaryProductConverter extends AbstractHttpMessageConverter<ProductData> {

    static final MediaType BINARY_TYPE = new MediaType("application", "x-product-binary");

    public BinaryProductConverter() {
        super(BINARY_TYPE);
    }

    @Override
    protected boolean supports(Class<?> clazz) { return ProductData.class.isAssignableFrom(clazz); }

    @Override
    protected ProductData readInternal(Class<? extends ProductData> clazz,
                                       HttpInputMessage inputMessage) throws IOException {
        byte[] bytes = inputMessage.getBody().readAllBytes();
        ByteBuffer buf = ByteBuffer.wrap(bytes);
        long id = buf.getLong();
        int nameLen = buf.getInt();
        byte[] nameBytes = new byte[nameLen];
        buf.get(nameBytes);
        double price = buf.getDouble();
        return new ProductData(id, new String(nameBytes), price);
    }

    @Override
    protected void writeInternal(ProductData data, HttpOutputMessage outputMessage)
            throws IOException {
        byte[] nameBytes = data.name().getBytes();
        ByteBuffer buf = ByteBuffer.allocate(8 + 4 + nameBytes.length + 8);
        buf.putLong(data.id()).putInt(nameBytes.length).put(nameBytes).putDouble(data.price());
        outputMessage.getBody().write(buf.array());
    }
}

// WebConfig.java
import com.fasterxml.jackson.databind.*;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.converter.HttpMessageConverter;
import org.springframework.http.converter.json.MappingJackson2HttpMessageConverter;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;
import java.util.List;

@Configuration
public class WebConfig implements WebMvcConfigurer {

    @Override
    public void extendMessageConverters(List<HttpMessageConverter<?>> converters) {
        // Add binary converter before default converters
        converters.add(0, new BinaryProductConverter());

        // Harden Jackson: fail on unknown fields
        converters.stream()
                .filter(c -> c instanceof MappingJackson2HttpMessageConverter)
                .map(c -> (MappingJackson2HttpMessageConverter) c)
                .findFirst()
                .ifPresent(c -> c.getObjectMapper()
                        .configure(DeserializationFeature.FAIL_ON_UNKNOWN_PROPERTIES, true));
    }
}

record ProductData(long id, String name, double price) {}

@RestController
@RequestMapping("/products")
class ProductApiController {

    @PostMapping(consumes = "application/x-product-binary",
                 produces = "application/x-product-binary")
    public ProductData createBinary(@RequestBody ProductData data) {
        return new ProductData(data.id() == 0 ? System.nanoTime() % 1000000 : data.id(),
                data.name(), data.price());
    }

    @PostMapping(consumes = "application/json", produces = "application/json")
    public ProductData createJson(@RequestBody ProductData data) {
        return new ProductData(System.nanoTime() % 1000000, data.name(), data.price());
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run

# JSON endpoint (standard)
curl -X POST http://localhost:8080/products \
     -H "Content-Type: application/json" \
     -H "Accept: application/json" \
     -d '{"id":0,"name":"Drill","price":29.99}'

# JSON with unknown field → 400 (FAIL_ON_UNKNOWN_PROPERTIES=true)
curl -X POST http://localhost:8080/products \
     -H "Content-Type: application/json" \
     -d '{"id":0,"name":"Drill","price":29.99,"unknown":"field"}'
```

**What changed and why:**
- `BinaryProductConverter` extends `AbstractHttpMessageConverter` — `readInternal` parses raw `ByteBuffer`, `writeInternal` serializes back. Registered via `extendMessageConverters`.
- `converters.add(0, ...)` inserts the binary converter before Jackson so it gets priority for `application/x-product-binary`.
- `FAIL_ON_UNKNOWN_PROPERTIES = true` on the shared `ObjectMapper` causes strict unknown-field rejection — prevents silent data loss when clients send unexpected fields (useful in versioned APIs where field drift should fail loudly).

<svg viewBox="0 0 700 180" xmlns="http://www.w3.org/2000/svg" font-family="monospace" font-size="11">
  <rect width="700" height="180" fill="#0d1117"/>
  <text x="350" y="20" text-anchor="middle" fill="#8b949e">extendMessageConverters — insertion order matters</text>

  <rect x="20" y="35" width="150" height="28" rx="4" fill="#1c2430" stroke="#6db33f"/>
  <text x="95" y="53" text-anchor="middle" fill="#6db33f">[0] BinaryConverter</text>
  <text x="95" y="68" text-anchor="middle" fill="#8b949e" font-size="10">application/x-product-binary</text>

  <rect x="190" y="35" width="150" height="28" rx="4" fill="#1c2430" stroke="#79c0ff"/>
  <text x="265" y="53" text-anchor="middle" fill="#79c0ff">[1] JacksonConverter</text>
  <text x="265" y="68" text-anchor="middle" fill="#8b949e" font-size="10">application/json</text>

  <rect x="360" y="35" width="150" height="28" rx="4" fill="#1c2430" stroke="#8b949e"/>
  <text x="435" y="53" text-anchor="middle" fill="#8b949e">[2] StringConverter</text>
  <text x="435" y="68" text-anchor="middle" fill="#8b949e" font-size="10">text/*</text>

  <rect x="530" y="35" width="150" height="28" rx="4" fill="#1c2430" stroke="#8b949e"/>
  <text x="605" y="53" text-anchor="middle" fill="#8b949e">[3] ByteArrayConverter</text>
  <text x="605" y="68" text-anchor="middle" fill="#8b949e" font-size="10">*/*</text>

  <text x="350" y="110" text-anchor="middle" fill="#8b949e">Content-Type: application/x-product-binary → [0] wins; application/json → [1] wins</text>
  <text x="350" y="130" text-anchor="middle" fill="#8b949e" font-size="10">No matching converter → 415 Unsupported Media Type</text>
  <text x="350" y="150" text-anchor="middle" fill="#8b949e" font-size="10">extendMessageConverters() appends by default; add(0,...) inserts at front</text>
</svg>

---

## 6. Walkthrough

**Per-request: `POST /products` with `Content-Type: application/json`:**

1. `DispatcherServlet` routes to `ProductApiController.createJson()`.
2. `RequestResponseBodyMethodProcessor` (argument resolver for `@RequestBody`) iterates converter chain.
3. For each converter: `converter.canRead(ProductData.class, MediaType.APPLICATION_JSON)`.
4. `BinaryProductConverter.canRead(...)` → false (only handles `application/x-product-binary`).
5. `MappingJackson2HttpMessageConverter.canRead(...)` → true.
6. `converter.read(ProductData.class, inputMessage)` → `ObjectMapper.readValue(stream, ProductData.class)`.
7. If `FAIL_ON_UNKNOWN_PROPERTIES=true` and JSON has extra fields → `HttpMessageNotReadableException` → 400.
8. `@Valid` annotation absent here; if present, JSR-303 runs and may throw `MethodArgumentNotValidException`.
9. `createJson(productData)` executes with bound `ProductData`.
10. Return value handled by `RequestResponseBodyMethodProcessor` (also a return value handler) — serializes back to JSON via the same Jackson converter.

**State at each layer:**

| Layer | Data |
|---|---|
| Request | `POST /products`, body=`{"id":0,"name":"Drill","price":29.99}` |
| Converter selection | Jackson matches `application/json` |
| Deserialization | `ProductData(0, "Drill", 29.99)` |
| Controller | returns `ProductData(id, "Drill", 29.99)` |
| Serialization | Jackson writes `{"id":...,"name":"Drill","price":29.99}` |
| Response | `200 OK`, `Content-Type: application/json` |

---

## 7. Gotchas & takeaways

> **`@RequestBody` reads the stream once.** After the converter calls `getBody()`, the stream is exhausted. Wrapping the request in `ContentCachingRequestWrapper` lets you re-read it for logging — but the original `@RequestBody` binding must still happen before the wrapper tries to cache.

> **Missing `Content-Type` returns 415, not 400.** The converter chain cannot select a reader without knowing the media type. Always send `Content-Type` on requests with a body.

> **`FAIL_ON_UNKNOWN_PROPERTIES = false` (Jackson default) silently drops unknown fields.** This is safe for consumers but hides client bugs. In strict APIs, set `true` to surface drift early.

- `@RequestBody` → `HttpMessageConverter.canRead(type, mediaType)` — first match wins.
- Default converters: JSON (Jackson), XML (JAXB), plain text, byte arrays.
- Add converters via `WebMvcConfigurer.extendMessageConverters()` — `add(0,...)` for highest priority.
- Combine with `@Valid` for deserialization + validation in one step; bind `BindingResult` to avoid exceptions.
- Content-Type mismatch → 415; deserialization failure → 400 `HttpMessageNotReadableException`.
