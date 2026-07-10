---
card: spring-framework
gi: 412
slug: spring-mvc-test-mocks-mockhttpservletrequest-etc
title: "Spring MVC Test mocks (MockHttpServletRequest, etc.)"
---

## 1. What it is

Spring MVC Test provides mock implementations of the Servlet API — `MockHttpServletRequest`, `MockHttpServletResponse`, `MockHttpSession`, `MockFilterChain` — along with `MockMvc`, a fluent façade that drives a `DispatcherServlet` against those mocks. This lets you test a `@RestController`'s full request-handling pipeline (routing, argument binding, validation, serialization) without starting a real HTTP server or opening a real socket.

```java
mockMvc.perform(get("/products/{id}", 42))
        .andExpect(status().isOk())
        .andExpect(jsonPath("$.name").value("Laptop"));
```

## 2. Why & when

Testing a controller by starting a real embedded server (Tomcat/Netty) and firing real HTTP requests at it works, but it's slow to start up and — more importantly — tests infrastructure concerns (port binding, real socket I/O) you usually don't need to re-verify for every single controller test. `MockMvc` gets you almost all the same confidence — that routing, `@RequestBody` binding, validation, and JSON serialization actually work — without ever opening a real network connection, because the mock Servlet objects simulate the request/response contract in memory while the real `DispatcherServlet` and your real controller code run exactly as they would in production.

Reach for `MockMvc`-based tests when:

- You want to verify a controller's full request-handling behavior (path matching, parameter binding, validation errors, response status/body/headers) without the overhead of a real server.
- You're testing security rules, content negotiation, or exception-handling behavior that depends on the Servlet request/response contract, not just the controller method's return value in isolation.
- You want tests fast enough to run in the hundreds without a real server's startup cost dominating the test suite's runtime.

For end-to-end confidence that a real deployed server behaves correctly (real serialization over an actual socket, real client library behavior), pair `MockMvc` tests with a smaller number of full `@SpringBootTest(webEnvironment = RANDOM_PORT)` tests that do start a real server — the two approaches complement rather than replace each other.

## 3. Core concept

```
  mockMvc.perform(get("/products/42"))
        |
        v
  MockHttpServletRequest built (method=GET, uri=/products/42)
        |
        v
  Real DispatcherServlet.service(mockRequest, mockResponse)
        |
        | routes, binds arguments, invokes your REAL @RestController method
        v
  Your real controller code runs, unchanged
        |
        v
  MockHttpServletResponse populated (status, headers, body)
        |
        v
  ResultActions -- .andExpect(status().isOk())
                    .andExpect(jsonPath("$.name").value("Laptop"))
```

Everything above the mock request/response objects is completely real: the same `DispatcherServlet`, the same argument resolvers, the same message converters, the same controller code that would run in production — only the transport (a real socket vs. an in-memory mock) differs.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="MockMvc drives a real DispatcherServlet and controller against mock Servlet request and response objects">
  <rect x="10" y="70" width="150" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="85" y="99" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">MockMvc.perform</text>

  <rect x="230" y="70" width="180" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="92" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">real DispatcherServlet</text>
  <text x="320" y="108" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">+ real @RestController</text>

  <rect x="480" y="70" width="150" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="555" y="99" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">andExpect(...)</text>

  <line x1="160" y1="95" x2="225" y2="95" stroke="#3fb950" stroke-width="2" marker-end="url(#a)"/>
  <line x1="410" y1="95" x2="475" y2="95" stroke="#3fb950" stroke-width="2" marker-end="url(#a)"/>
  <text x="320" y="150" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">no real socket, no real server port</text>
  <defs><marker id="a" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#3fb950"/></marker></defs>
</svg>

The middle box is completely real application code — only the outer request/response transport is mocked.

## 5. Runnable example

### Level 1 — Basic

Build a standalone `MockMvc` (not backed by a full Spring context, just the controller under test) and verify a simple GET endpoint's status and body.

```java
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;
import org.springframework.web.bind.annotation.*;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

public class MvcTestBasic {

    record Product(long id, String name) {}

    @RestController
    static class ProductController {
        @GetMapping("/products/{id}")
        Product get(@PathVariable long id) {
            return new Product(id, "Laptop");
        }
    }

    public static void main(String[] args) throws Exception {
        MockMvc mockMvc = MockMvcBuilders.standaloneSetup(new ProductController()).build();

        mockMvc.perform(get("/products/42"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.id").value(42))
                .andExpect(jsonPath("$.name").value("Laptop"));

        System.out.println("GET /products/42 returned 200 with expected body -- PASS");
    }
}
```

How to run: add `spring-test`, `spring-webmvc`, Jackson, and `jakarta.servlet-api` to the classpath, then `java MvcTestBasic.java`.

`MockMvcBuilders.standaloneSetup(new ProductController())` builds a minimal `MockMvc` around just this one controller instance, without loading a full Spring `ApplicationContext` — fast, but it means dependencies the controller needs would have to be constructed manually (fine here, since `ProductController` has none). `mockMvc.perform(get(...))` drives a real `DispatcherServlet` against a `MockHttpServletRequest` built from the given URI; `andExpect(jsonPath(...))` parses the response body as JSON and asserts on a specific field via a JSONPath expression.

### Level 2 — Intermediate

Test a `POST` endpoint with a JSON request body, validation, and error-status assertions — covering both the success and the validation-failure paths through the same controller.

```java
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Positive;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.*;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

public class MvcTestIntermediate {

    record NewProduct(@NotBlank String name, @Positive double price) {}
    record Product(long id, String name, double price) {}

    @RestController
    @Validated
    static class ProductController {
        @PostMapping(value = "/products", consumes = MediaType.APPLICATION_JSON_VALUE)
        Product create(@jakarta.validation.Valid @org.springframework.web.bind.annotation.RequestBody NewProduct request) {
            return new Product(1, request.name(), request.price());
        }
    }

    public static void main(String[] args) throws Exception {
        MockMvc mockMvc = MockMvcBuilders.standaloneSetup(new ProductController()).build();

        // Valid request
        mockMvc.perform(post("/products")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"name\":\"Laptop\",\"price\":999.99}"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.name").value("Laptop"))
                .andExpect(jsonPath("$.price").value(999.99));
        System.out.println("Valid POST -- PASS");

        // Invalid request: blank name should trigger a 400
        mockMvc.perform(post("/products")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"name\":\"\",\"price\":999.99}"))
                .andExpect(status().isBadRequest());
        System.out.println("Invalid POST (blank name) correctly returned 400 -- PASS");
    }
}
```

How to run: same dependencies as Level 1, plus `jakarta.validation:jakarta.validation-api` and a validator implementation (`org.hibernate.validator:hibernate-validator`); then `java MvcTestIntermediate.java`.

`.content("{...}")` supplies a raw JSON string as the request body, exercising the same `@RequestBody` deserialization path a real client's request would go through. Because `@Valid` triggers Spring's validation machinery on `NewProduct`, a blank `name` (violating `@NotBlank`) causes the framework to short-circuit before the controller method body even runs, returning `400 Bad Request` automatically — the test verifies this framework-level behavior, not anything the controller method explicitly coded.

### Level 3 — Advanced

A context-backed `MockMvc` (built from a real `@Configuration`, not a standalone controller instance) testing a controller with a real dependency, a custom exception handler, and request headers/security-relevant assertions — closer to how a full application's controller test typically looks.

```java
import org.springframework.context.annotation.*;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.context.WebApplicationContext;
import org.springframework.web.context.support.AnnotationConfigWebApplicationContext;
import org.springframework.mock.web.MockServletContext;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

public class MvcTestAdvanced {

    record Product(long id, String name) {}

    interface ProductRepository {
        Product findById(long id);
    }

    static class ProductNotFoundException extends RuntimeException {
        ProductNotFoundException(long id) { super("Product not found: " + id); }
    }

    @RestController
    static class ProductController {
        private final ProductRepository repository;
        ProductController(ProductRepository repository) { this.repository = repository; }

        @GetMapping("/products/{id}")
        Product get(@PathVariable long id) {
            Product product = repository.findById(id);
            if (product == null) throw new ProductNotFoundException(id);
            return product;
        }
    }

    @RestControllerAdvice
    static class ErrorHandler {
        @ExceptionHandler(ProductNotFoundException.class)
        @ResponseStatus(HttpStatus.NOT_FOUND)
        java.util.Map<String, String> handleNotFound(ProductNotFoundException e) {
            return java.util.Map.of("error", e.getMessage());
        }
    }

    @Configuration
    @org.springframework.web.servlet.config.annotation.EnableWebMvc
    static class WebConfig {
        @Bean
        ProductRepository productRepository() {
            return id -> id == 1 ? new Product(1, "Laptop") : null;
        }

        @Bean
        ProductController productController(ProductRepository repository) {
            return new ProductController(repository);
        }

        @Bean
        ErrorHandler errorHandler() { return new ErrorHandler(); }
    }

    public static void main(String[] args) throws Exception {
        AnnotationConfigWebApplicationContext context = new AnnotationConfigWebApplicationContext();
        context.register(WebConfig.class);
        context.setServletContext(new MockServletContext());
        context.refresh();

        MockMvc mockMvc = MockMvcBuilders.webAppContextSetup((WebApplicationContext) context).build();

        mockMvc.perform(get("/products/1").accept(MediaType.APPLICATION_JSON))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.name").value("Laptop"));
        System.out.println("GET /products/1 -- PASS");

        mockMvc.perform(get("/products/999").accept(MediaType.APPLICATION_JSON))
                .andExpect(status().isNotFound())
                .andExpect(jsonPath("$.error").value("Product not found: 999"));
        System.out.println("GET /products/999 correctly returned 404 with error body -- PASS");

        context.close();
    }
}
```

How to run: add `spring-webmvc`, `spring-test`, Jackson, and `jakarta.servlet-api` to the classpath, then `java MvcTestAdvanced.java`.

`MockMvcBuilders.webAppContextSetup(context)` builds `MockMvc` from a real `WebApplicationContext`, meaning `@RestControllerAdvice`-based exception handling, real bean wiring (the `ProductRepository` bean genuinely injected into `ProductController`), and any other web-layer configuration behave exactly as they would in a fully deployed application — closer to true integration testing of the whole web layer than the standalone setup in Levels 1–2. The 404 test verifies not just a status code but the exact error body the `@RestControllerAdvice` produces, confirming the whole exception-to-response translation pipeline works end to end.

## 6. Walkthrough

Trace the `GET /products/999` call in `MvcTestAdvanced.main`:

1. **Mock request built.** `get("/products/999").accept(MediaType.APPLICATION_JSON)` builds a `MockHttpServletRequest` describing a `GET` request to that path with an `Accept: application/json` header.
2. **Dispatch.** `mockMvc.perform(...)` hands this mock request (and a fresh `MockHttpServletResponse`) to the real `DispatcherServlet` created from the `WebApplicationContext`.
3. **Routing.** The `DispatcherServlet` matches `/products/999` against `@GetMapping("/products/{id}")`, extracting `id = 999` as a path variable.
4. **Controller invocation.** The real `ProductController.get(999)` method runs, calling `repository.findById(999)` — the real `ProductRepository` bean (the lambda returning `null` for any id other than 1) returns `null`.
5. **Exception thrown.** Since `product` is `null`, `get` throws `new ProductNotFoundException(999)`.
6. **Exception handling.** The `DispatcherServlet`'s exception-resolution mechanism finds the `@RestControllerAdvice`-annotated `ErrorHandler`'s `@ExceptionHandler(ProductNotFoundException.class)` method, invokes it with the thrown exception, and uses its `@ResponseStatus(HttpStatus.NOT_FOUND)` to set the response status, with the returned `Map` serialized as the JSON response body.
7. **Response populated.** The `MockHttpServletResponse` now has status `404` and body `{"error":"Product not found: 999"}` — exactly what a real client would receive over a real socket, but captured here entirely in memory.
8. **Assertions.** `andExpect(status().isNotFound())` and `andExpect(jsonPath("$.error").value(...))` inspect that mock response and confirm both the status code and the JSON body's `error` field match expectations — if either the routing, the exception handler, or the JSON serialization were broken, one of these assertions would fail with a clear message pointing at exactly what differed from expectation.

```
GET /products/999
   -> DispatcherServlet routes to ProductController.get(999)
   -> repository.findById(999) -> null
   -> throw ProductNotFoundException
   -> @RestControllerAdvice.handleNotFound -> 404 + {"error": "..."}
   -> MockHttpServletResponse populated
   -> andExpect(status().isNotFound())
   -> andExpect(jsonPath("$.error").value(...))
```

## 7. Gotchas & takeaways

> Gotcha: a standalone `MockMvcBuilders.standaloneSetup(...)` test (Levels 1–2) only ever sees the controller instance(s) you explicitly pass in — any `@ControllerAdvice`, interceptor, or filter registered elsewhere in a real application's configuration won't automatically apply unless you also explicitly add it to the standalone setup. If a real request would go through a security filter or a global exception handler, a standalone `MockMvc` test can pass while the same request would behave differently against a real, fully-configured application — use `webAppContextSetup(...)` (Level 3) when that full-configuration behavior matters to what you're testing.

- `MockMvc` runs your real `DispatcherServlet` and real controller code against in-memory mock Servlet objects — you get near-production confidence in routing, binding, and serialization without a real server's startup cost.
- Use standalone setup for fast, narrowly-scoped controller tests where you don't need the rest of the web configuration; use `webAppContextSetup` when exception handlers, interceptors, or security configuration are part of what you're verifying.
- `jsonPath(...)` assertions let you check specific fields of a JSON response without manually parsing it, and they produce clear failure messages pointing at exactly which field didn't match.
- Pair `MockMvc` tests (fast, in-memory) with a smaller number of full `@SpringBootTest(webEnvironment = RANDOM_PORT)` tests that exercise a real running server, for end-to-end confidence that the mock transport didn't hide a real-server-only issue.
