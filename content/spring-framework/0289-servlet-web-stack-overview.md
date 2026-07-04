---
card: spring-framework
gi: 289
slug: servlet-web-stack-overview
title: Servlet Web Stack Overview
---

## 1. What it is

Spring Framework 5+ ships **two parallel web stacks**:

| Stack | Module | I/O model | Thread model |
|---|---|---|---|
| **Servlet** (Spring MVC) | `spring-webmvc` | Blocking (Servlet API) | 1 thread per request |
| **Reactive** (Spring WebFlux) | `spring-webflux` | Non-blocking (Reactor) | Event loop (Netty/Undertow) |

The **Servlet web stack** is built on the Java Servlet API (`jakarta.servlet`). It runs in any Servlet 5+ container (Tomcat, Jetty, Undertow) or can be embedded. `DispatcherServlet` is the central front controller that routes requests to `@Controller`/`@RestController` handlers.

```
HTTP request
  → Tomcat/Jetty (Servlet container)
  → DispatcherServlet (front controller)
  → HandlerMapping → finds @RequestMapping method
  → HandlerAdapter → invokes @Controller method
  → ViewResolver / @ResponseBody → builds HTTP response
```

## 2. Why & when

The Servlet stack is the right choice for:
- Most enterprise applications that don't need reactive throughput.
- Codebases already using Spring MVC, Spring Security, Spring Data JPA, or any JDBC/JPA dependency (these are blocking by nature).
- Teams comfortable with the thread-per-request model and blocking I/O.

Choose Spring WebFlux when:
- You need streaming / server-sent events at scale.
- Your data access is fully reactive (R2DBC, MongoDB reactive, Redis reactive).
- You need non-blocking I/O throughout the stack.

Mixing them: the two stacks are separate. You can run `spring-webmvc` and `spring-webflux` in the same app but not on the same port. Spring Boot auto-selects the active stack based on what's on the classpath.

## 3. Core concept

The Servlet web stack layers:

```
Browser / REST client
      │ HTTP
      ▼
┌─────────────────────────────────────────┐
│  Servlet Container (Tomcat / Jetty)     │
│  Receives TCP connection                │
│  Decodes HTTP → HttpServletRequest      │
└───────────────────┬─────────────────────┘
                    │ forward to registered Servlet
                    ▼
┌─────────────────────────────────────────┐
│  DispatcherServlet                      │
│  1. HandlerMapping → picks Handler      │
│  2. HandlerAdapter → invokes Handler    │
│  3. HandlerInterceptors (pre/post)      │
│  4. ViewResolver (or @ResponseBody)     │
└───────────────────┬─────────────────────┘
                    │
                    ▼
             @Controller / @RestController
             (your application code)
```

Key extension points:
- `HandlerMapping` — maps URL patterns to handlers.
- `HandlerAdapter` — invokes the handler (dispatches `@RequestMapping` methods).
- `ViewResolver` — resolves logical view names to view implementations.
- `HandlerExceptionResolver` — handles exceptions thrown from handlers.
- `HandlerInterceptor` — pre/post processing around handler invocation.
- `MessageConverter` — converts request body / response body to/from Java objects.

## 4. Diagram

<svg viewBox="0 0 700 215" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <marker id="arr" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <polygon points="0 0,8 3,0 6" fill="#6db33f"/>
    </marker>
  </defs>

  <!-- Client -->
  <rect x="10" y="90" width="80" height="35" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="50" y="112" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Client</text>
  <line x1="92" y1="107" x2="125" y2="107" stroke="#8b949e" stroke-width="1.5" marker-end="url(#arr)"/>

  <!-- Tomcat -->
  <rect x="127" y="70" width="120" height="75" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="187" y="92" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Servlet Container</text>
  <text x="187" y="106" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">Tomcat / Jetty</text>
  <line x1="137" y1="112" x2="237" y2="112" stroke="#8b949e" stroke-width="0.5"/>
  <text x="187" y="128" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">HttpServletRequest</text>
  <text x="187" y="140" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">HttpServletResponse</text>

  <line x1="249" y1="107" x2="282" y2="107" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>

  <!-- DispatcherServlet -->
  <rect x="284" y="50" width="195" height="115" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="381" y="72" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">DispatcherServlet</text>
  <line x1="294" y1="78" x2="469" y2="78" stroke="#8b949e" stroke-width="0.5"/>
  <text x="381" y="96" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">HandlerMapping</text>
  <text x="381" y="110" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">HandlerAdapter</text>
  <text x="381" y="124" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">ViewResolver</text>
  <text x="381" y="138" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">HandlerExceptionResolver</text>
  <text x="381" y="152" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">MessageConverter</text>

  <line x1="481" y1="107" x2="514" y2="107" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>

  <!-- Controller -->
  <rect x="516" y="78" width="165" height="60" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="598" y="100" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">@RestController</text>
  <text x="598" y="115" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">@GetMapping("/items")</text>
  <text x="598" y="129" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">return List&lt;Item&gt;</text>
</svg>

## 5. Runnable example

Scenario: a **product catalog REST API** — build a minimal Servlet-stack web app at three complexity levels.

### Level 1 — Basic

Minimal Spring MVC `@RestController` with embedded setup.

```java
// ServletWebStackDemo.java
import org.springframework.context.annotation.*;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.servlet.config.annotation.*;
import java.util.*;

record Product(long id, String name, double price) {}

@RestController
@RequestMapping("/api/products")
class ProductController {
    private final Map<Long,Product> store = new LinkedHashMap<>();
    private long seq = 1;

    @GetMapping
    public List<Product> list() {
        return new ArrayList<>(store.values());
    }

    @GetMapping("/{id}")
    public ResponseEntity<Product> get(@PathVariable long id) {
        Product p = store.get(id);
        return p != null ? ResponseEntity.ok(p) : ResponseEntity.notFound().build();
    }

    @PostMapping
    public Product create(@RequestBody Product req) {
        long id = seq++;
        Product p = new Product(id, req.name(), req.price());
        store.put(id, p);
        return p;
    }
}

@Configuration @EnableWebMvc @ComponentScan
class WebCfg {}

public class ServletWebStackDemo {
    public static void main(String[] args) {
        System.out.println("Servlet web stack anatomy:");
        System.out.println("  HTTP request arrives at Servlet container (Tomcat)");
        System.out.println("  Container dispatches to DispatcherServlet (configured as URL='/')");
        System.out.println("  DispatcherServlet → HandlerMapping finds ProductController.list()");
        System.out.println("  HandlerAdapter invokes list() → returns List<Product>");
        System.out.println("  MappingJackson2HttpMessageConverter serialises → JSON response");
        System.out.println();
        System.out.println("Deploy as WAR or embed Tomcat to serve live requests.");
        System.out.println("See 0290-dispatcherservlet-front-controller for full wiring.");
    }
}
```

How to run: `java -cp spring-webmvc.jar:spring-context.jar:jackson-databind.jar:jakarta.servlet-api.jar:. ServletWebStackDemo.java`

The Servlet web stack: container creates `HttpServletRequest` → `DispatcherServlet` dispatches to `@RequestMapping` handler → `@ResponseBody` on `@RestController` sends the return value through a `MessageConverter` → JSON written to the response stream.

---

### Level 2 — Intermediate

`HandlerInterceptor` for request logging + timing.

```java
// ServletWebStackDemo.java
import jakarta.servlet.http.*;
import org.springframework.context.annotation.*;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.servlet.*;
import org.springframework.web.servlet.config.annotation.*;
import java.util.*;

// (Product and ProductController same as Level 1)

class TimingInterceptor implements HandlerInterceptor {
    @Override
    public boolean preHandle(HttpServletRequest req, HttpServletResponse res, Object handler) {
        req.setAttribute("startTime", System.currentTimeMillis());
        System.out.println("[Interceptor] PRE  " + req.getMethod() + " " + req.getRequestURI());
        return true;  // continue processing
    }

    @Override
    public void afterCompletion(HttpServletRequest req, HttpServletResponse res,
                                Object handler, Exception ex) {
        long elapsed = System.currentTimeMillis() - (long) req.getAttribute("startTime");
        System.out.println("[Interceptor] POST " + req.getRequestURI() + " " + elapsed + "ms");
    }
}

@Configuration @EnableWebMvc @ComponentScan
class WebCfg2 implements WebMvcConfigurer {
    @Override
    public void addInterceptors(InterceptorRegistry registry) {
        registry.addInterceptor(new TimingInterceptor())
                .addPathPatterns("/api/**");  // only intercept /api/* paths
    }
}

public class ServletWebStackDemo {
    public static void main(String[] args) {
        System.out.println("HandlerInterceptor positions in DispatcherServlet pipeline:");
        System.out.println("  preHandle()       → before handler method");
        System.out.println("  postHandle()      → after handler method, before view render");
        System.out.println("  afterCompletion() → after full response committed");
    }
}
```

How to run: same classpath

`HandlerInterceptor` hooks into the `DispatcherServlet` pipeline at three points: `preHandle` (can abort), `postHandle` (model manipulation), `afterCompletion` (cleanup). `WebMvcConfigurer.addInterceptors()` registers interceptors with optional path patterns.

---

### Level 3 — Advanced

`HandlerExceptionResolver` + global `@ControllerAdvice`.

```java
// ServletWebStackDemo.java
import org.springframework.context.annotation.*;
import org.springframework.http.*;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.servlet.config.annotation.*;
import java.util.*;

class ProductNotFoundException extends RuntimeException {
    ProductNotFoundException(long id){ super("Product not found: " + id); }
}

@RestControllerAdvice      // global exception handler for @RestController beans
class GlobalExceptionHandler {
    @ExceptionHandler(ProductNotFoundException.class)
    public ResponseEntity<Map<String,String>> handleNotFound(ProductNotFoundException e) {
        return ResponseEntity.status(HttpStatus.NOT_FOUND)
            .body(Map.of("error", e.getMessage()));
    }

    @ExceptionHandler(IllegalArgumentException.class)
    public ResponseEntity<Map<String,String>> handleBadRequest(IllegalArgumentException e) {
        return ResponseEntity.badRequest().body(Map.of("error", e.getMessage()));
    }
}

@RestController @RequestMapping("/api/v2/products")
class ProductControllerV2 {
    private final Map<Long,Product> store = new LinkedHashMap<>(
        Map.of(1L, new Product(1L,"Widget",49.99), 2L, new Product(2L,"Gadget",99.00))
    );

    @GetMapping("/{id}")
    public Product get(@PathVariable long id) {
        Product p = store.get(id);
        if (p == null) throw new ProductNotFoundException(id);  // → 404
        return p;
    }

    @PostMapping
    public Product create(@RequestBody Product req) {
        if (req.name() == null || req.name().isBlank())
            throw new IllegalArgumentException("name is required");  // → 400
        long id = store.size() + 1;
        Product p = new Product(id, req.name(), req.price());
        store.put(id, p);
        return p;
    }
}

// @Configuration @EnableWebMvc @ComponentScan class WebCfg3 { }

public class ServletWebStackDemo {
    public static void main(String[] args) {
        System.out.println("@RestControllerAdvice is detected by DispatcherServlet's");
        System.out.println("ExceptionHandlerExceptionResolver and applied to all @RestControllers.");
        System.out.println("No try/catch in controllers — exception handling is centralised.");
    }
}
```

How to run: same classpath + deploy to servlet container

`@RestControllerAdvice` + `@ExceptionHandler` hooks into `DispatcherServlet`'s `ExceptionHandlerExceptionResolver`. Exceptions thrown from any `@RestController` are caught, translated to structured JSON error bodies, and the correct HTTP status code is set — all in one place.

## 6. Walkthrough

**Level 2 — `GET /api/products/{id}` with interceptor:**

1. HTTP `GET /api/products/1` arrives at Tomcat → decodes to `HttpServletRequest`.
2. Tomcat dispatches to `DispatcherServlet` (mapped to `/`).
3. `DispatcherServlet` → `HandlerMapping` (`RequestMappingHandlerMapping`) → finds `ProductController.get()`.
4. `TimingInterceptor.preHandle()` called → sets `startTime` attribute → returns `true` (continue).
5. `HandlerAdapter` (`RequestMappingHandlerAdapter`) invokes `ProductController.get(1L)`.
   - Spring resolves `@PathVariable id` from request URI.
   - Method returns `ResponseEntity.ok(product)`.
6. `TimingInterceptor.postHandle()` called (between handler return and view rendering — not relevant for REST).
7. `MappingJackson2HttpMessageConverter` serializes `Product` → JSON → writes to `HttpServletResponse`.
8. `TimingInterceptor.afterCompletion()` called → logs elapsed time.

## 7. Gotchas & takeaways

> **`spring-webmvc` and `spring-webflux` cannot share an application context.** Both define `DispatcherServlet` / `DispatcherHandler` beans; having both on the classpath causes Spring Boot to pick one. In plain Spring, carefully manage which `@Configuration` classes are loaded.

> **`HandlerInterceptor.preHandle()` returning `false` stops the pipeline.** The response is committed by the interceptor or left empty. Always write a response before returning `false`, otherwise the client receives an empty 200.

> **`@RestControllerAdvice` applies to all controllers in the context** unless scoped with `basePackages` or `assignableTypes`. For large applications, scope it to prevent accidental exception swallowing.

- Servlet web stack: `Servlet container → DispatcherServlet → HandlerMapping → HandlerAdapter → Handler`.
- `HandlerInterceptor`: three hooks (`preHandle`, `postHandle`, `afterCompletion`).
- `@ControllerAdvice` / `@RestControllerAdvice`: global exception handler via `@ExceptionHandler`.
- Thread model: one Servlet thread per request — blocking I/O is fine; avoid blocking on reactive streams here.
- Use Spring WebFlux (reactive stack) for non-blocking I/O; Spring MVC (servlet stack) for the rest.
