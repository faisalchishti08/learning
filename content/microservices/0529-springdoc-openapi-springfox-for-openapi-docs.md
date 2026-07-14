---
card: microservices
gi: 529
slug: springdoc-openapi-springfox-for-openapi-docs
title: "springdoc-openapi / Springfox for OpenAPI docs"
---

## 1. What it is

**springdoc-openapi** is a library that generates an OpenAPI (Swagger) specification for a Spring Boot application automatically, by scanning its `@RestController` classes, request mappings, and DTOs at runtime, and exposing both the raw JSON/YAML spec and an interactive Swagger UI page — all without hand-writing the specification by hand. **Springfox** was the older, widely-used library that did the same job before springdoc-openapi became the standard choice for Spring Boot 3+ (Springfox never gained compatibility with the newer Spring/Jakarta namespace and is now effectively unmaintained), so any current project should reach for springdoc-openapi rather than Springfox.

## 2. Why & when

You add springdoc-openapi whenever a service's API is consumed by other teams, external clients, or generated client SDKs, because hand-maintained documentation drifts from the real implementation almost immediately:

- **A specification generated from the actual code cannot drift silently out of date** the way a hand-written wiki page or Markdown doc can — since the spec is derived from the real `@RestController` methods, `@RequestBody` types, and validation annotations, it reflects exactly what the running application actually accepts and returns.
- **It provides a live, interactive Swagger UI** where any consumer can browse every endpoint, see example request/response bodies, and even execute real requests against a running instance directly from the browser — useful for onboarding a new team, debugging in a shared environment, or letting API consumers self-serve answers instead of asking the owning team directly.
- **It's the foundation for consumer-driven contract testing and client code generation** — tools that generate typed client SDKs in other languages, or contract tests that verify a response's shape, both typically consume the OpenAPI spec springdoc-openapi produces, rather than requiring a separately maintained specification.
- **You reach for it as soon as a service has any external consumer** (another team, a partner, a public API) — for a purely internal service with a single consumer team that reads the source directly, it's still useful, but the return on investment is highest once the API has consumers who can't or won't read the implementation.

## 3. Core concept

Think of a building directory generated automatically from the building's actual door signage and room labels, rather than a separately maintained paper map kept in a drawer somewhere. If a room gets renamed or a new wing is added, the automatically-generated directory reflects it the next time it's regenerated; the paper map, unless someone remembers to update it by hand, silently becomes wrong the moment the building changes. springdoc-openapi is the automatically-generated directory: it reads the actual `@RestController` "signage" on the building (the real, live endpoints) rather than relying on a document a human has to remember to keep synchronized.

Concretely:

1. **Adding the springdoc-openapi dependency to a Spring Boot project** is enough to get a baseline: it scans all `@RestController` beans at startup and derives paths, HTTP methods, and parameter/response types from the actual Java code (method signatures, `@RequestMapping` annotations, `@RequestBody`/`@ResponseBody` types).
2. **The generated spec is exposed as JSON/YAML** at a configurable path (by default `/v3/api-docs`), and as an interactive Swagger UI page (by default `/swagger-ui.html`) — both are live, generated fresh from the running application's actual state, not a stale artifact.
3. **Annotations like `@Operation`, `@Parameter`, and `@Schema`** (from the `io.swagger.v3.oas.annotations` package) let you enrich the auto-derived spec with human-readable descriptions, examples, and constraints beyond what can be inferred purely from types — the generation is automatic, but still fully customizable.
4. **Bean Validation annotations** (`@NotNull`, `@Size`, `@Min`, etc.) on request DTOs are picked up automatically and reflected as constraints in the generated spec, so validation rules that already exist in the code for correctness also show up in the documentation for free, with no duplication.

## 4. Diagram

<svg viewBox="0 0 660 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="springdoc-openapi scans real controller classes at runtime and generates a live OpenAPI spec plus an interactive Swagger UI, instead of a hand-maintained document that can drift out of date">
  <rect x="20" y="30" width="180" height="60" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="110" y="55" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">@RestController classes</text>
  <text x="110" y="72" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">the REAL, running code</text>

  <line x1="200" y1="60" x2="250" y2="60" stroke="#8b949e" marker-end="url(#a4)"/>

  <rect x="260" y="30" width="180" height="60" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="350" y="55" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">springdoc-openapi</text>
  <text x="350" y="72" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">scans at runtime</text>

  <line x1="440" y1="60" x2="490" y2="60" stroke="#8b949e" marker-end="url(#a4)"/>

  <rect x="500" y="10" width="140" height="35" rx="4" fill="#1c2430" stroke="#79c0ff"/>
  <text x="570" y="32" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">/v3/api-docs (JSON)</text>
  <rect x="500" y="55" width="140" height="35" rx="4" fill="#1c2430" stroke="#79c0ff"/>
  <text x="570" y="77" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">/swagger-ui.html</text>

  <text x="330" y="140" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">both regenerate automatically every time the app restarts with new code --</text>
  <text x="330" y="156" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">never a separately maintained document that can silently drift</text>
  <defs><marker id="a4" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#8b949e"/></marker></defs>
</svg>

The spec and UI are derived live from the actual controller code, eliminating the gap between documentation and implementation that hand-written docs suffer from.

## 5. Runnable example

Scenario: documenting a simple Order lookup endpoint. We start with a plain Java model of "generating docs from code structure" to show the underlying idea, then show the real springdoc-openapi annotated controller, then handle the hard case: enriching the generated spec with explicit examples, descriptions, and validation constraints for a non-trivial request body.

### Level 1 — Basic

```java
// File: DocGenerationConcept.java -- models the CORE idea springdoc-openapi
// automates: inspect a method's real signature via reflection and derive
// a description of it, rather than hand-writing that description separately.
import java.lang.reflect.*;

public class DocGenerationConcept {
    static class OrderController {
        public String getOrder(String id) { return "{\"orderId\":\"" + id + "\"}"; }
    }

    public static void main(String[] args) throws Exception {
        Method method = OrderController.class.getMethod("getOrder", String.class);
        System.out.println("Auto-derived doc entry:");
        System.out.println("  method: " + method.getName());
        System.out.println("  parameters: " + java.util.Arrays.toString(method.getParameterTypes()));
        System.out.println("  returns: " + method.getReturnType().getSimpleName());
        System.out.println("(This is the REFLECTION-BASED idea springdoc-openapi automates over real @RestController classes.)");
    }
}
```

How to run: `java DocGenerationConcept.java`

Using `java.lang.reflect.Method`, this reads the controller's real method signature directly from the compiled class, rather than a separately maintained description — exactly the underlying mechanism (Spring's own richer reflection over `@RequestMapping`-annotated methods) that lets springdoc-openapi derive an accurate spec without any hand-written duplication.

### Level 2 — Intermediate

```java
// File: SpringdocRealShape.java -- the REAL Spring Boot shape: a
// @RestController annotated with springdoc-openapi's OpenAPI annotations,
// as it would actually be written and run in a Spring Boot 3.x project.
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import org.springframework.web.bind.annotation.*;

public class SpringdocRealShape {

    @RestController
    @RequestMapping("/orders")
    static class OrderController {

        @Operation(summary = "Fetch an order by ID", description = "Returns the order's current status and total.")
        @ApiResponse(responseCode = "200", description = "Order found")
        @ApiResponse(responseCode = "404", description = "No order with that ID exists")
        @GetMapping("/{id}")
        public String getOrder(@Parameter(description = "The order's public identifier, e.g. ORD-1A2B") @PathVariable String id) {
            return "{\"orderId\":\"" + id + "\",\"status\":\"SUBMITTED\"}";
        }
    }
}
```

How to run: requires `springdoc-openapi-starter-webmvc-ui` (or `-webflux-ui`) on the classpath in a Spring Boot 3.x project; run the application via `mvn spring-boot:run` and visit `http://localhost:8080/swagger-ui.html` to see the generated, interactive documentation.

`@Operation` and `@ApiResponse` enrich the automatically-derived spec entry for this endpoint with human-written descriptions — springdoc-openapi already knows the path (`/orders/{id}`), the HTTP method (`GET`), and the parameter's type (`String`) purely from the Spring annotations already present for routing; the OpenAPI annotations add the descriptive layer on top, without duplicating anything the code already expresses structurally.

### Level 3 — Advanced

```java
// File: SpringdocValidatedRequestBody.java -- a POST endpoint with a
// VALIDATED request body: Bean Validation constraints are picked up
// automatically by springdoc-openapi and reflected in the generated spec,
// with explicit @Schema examples added for clarity.
import io.swagger.v3.oas.annotations.media.Schema;
import io.swagger.v3.oas.annotations.Operation;
import jakarta.validation.Valid;
import jakarta.validation.constraints.*;
import org.springframework.web.bind.annotation.*;

public class SpringdocValidatedRequestBody {

    record CreateOrderRequest(
        @Schema(description = "Customer placing the order", example = "cust-42")
        @NotBlank String customerId,

        @Schema(description = "Quantity of items ordered", example = "3")
        @Min(1) @Max(100) int quantity
    ) {}

    @RestController
    @RequestMapping("/orders")
    static class OrderController {

        @Operation(summary = "Create a new order",
                   description = "Validates the request and creates a new order in SUBMITTED status.")
        @PostMapping
        public String createOrder(@Valid @RequestBody CreateOrderRequest request) {
            return "{\"orderId\":\"ORD-NEW\",\"customerId\":\"" + request.customerId()
                 + "\",\"quantity\":" + request.quantity() + "}";
        }
    }
}
```

How to run: requires `springdoc-openapi-starter-webmvc-ui`, `spring-boot-starter-validation`, and `spring-boot-starter-web`; run via `mvn spring-boot:run` and inspect the generated schema for `CreateOrderRequest` at `/v3/api-docs` (or view it rendered in `/swagger-ui.html`) to see `customerId` marked required and `quantity` constrained to 1-100.

`@NotBlank`, `@Min(1)`, and `@Max(100)` are ordinary Bean Validation annotations already needed for runtime request validation — springdoc-openapi reads these same annotations and reflects them directly in the generated OpenAPI schema as `required` and `minimum`/`maximum` constraints, so the documentation and the actual enforced validation can never disagree, since they're driven by the exact same annotations on the exact same class.

## 6. Walkthrough

Trace what happens when a client sends `POST /orders` with body `{"customerId": "cust-42", "quantity": 150}` against the Level 3 controller, end to end:

1. **Spring MVC routes the request** to `OrderController.createOrder`, and because the parameter is annotated `@Valid @RequestBody CreateOrderRequest`, Spring first deserializes the JSON body into a `CreateOrderRequest` record, then runs Bean Validation against it *before* the method body executes.
2. **Validation checks `quantity = 150` against `@Max(100)`** and fails, since 150 exceeds the maximum — Spring's validation machinery throws a `MethodArgumentNotValidException` before `createOrder`'s body ever runs.
3. **The response returned to the client is an HTTP 400 Bad Request**, with a body describing the validation failure (the exact shape depends on whether [Problem Details / RFC 7807 support](0536-problem-details-rfc-7807-support-in-spring-6.md) is enabled, but conceptually: `{"quantity": "must be less than or equal to 100"}`).
4. **Separately, and independently of any particular request, springdoc-openapi has already generated the spec entry for this endpoint at application startup** — visiting `/v3/api-docs` shows the `CreateOrderRequest` schema listing `quantity` with `"maximum": 100`, derived directly from the same `@Max(100)` annotation that just rejected this request. A client reading the documentation *before* making a request would have seen this constraint and could have avoided sending an invalid `quantity` in the first place.
5. **Now imagine the same request with `quantity = 3` (a valid value).** Validation passes, `createOrder`'s body executes, and it returns `{"orderId": "ORD-NEW", "customerId": "cust-42", "quantity": 3}` with a 200 status — and this successful shape is also exactly what the Swagger UI's "Example Value" panel for this endpoint would show, since springdoc-openapi derives its example directly from the method's actual return type and any `@Schema(example = ...)` annotations present.

The key point: the validation that actually runs and rejects an over-limit request, and the documentation that describes that same limit to API consumers, come from the identical `@Max(100)` annotation — there's no separate "spec" to keep in sync, because the spec is a live reflection of the same code that enforces the behavior.

## 7. Gotchas & takeaways

> **Gotcha:** springdoc-openapi documents what the code's annotations say, not necessarily what the code actually does — if a controller method has business logic that rejects a request for reasons not expressed in an annotation (a manual `if` check inside the method body, for instance), that behavior won't appear in the generated spec at all; keeping validation and business rules expressed as annotations where possible is what keeps the generated docs accurate.

- Prefer springdoc-openapi over Springfox for any Spring Boot 3+ project — Springfox never gained compatibility with the Jakarta namespace and is effectively unmaintained.
- The generated spec and Swagger UI are derived live from the running application, so they can never silently drift the way a separately maintained document can — but only for what's expressed in code and annotations, not for undocumented business logic buried in method bodies.
- Bean Validation annotations (`@NotBlank`, `@Min`, `@Max`, etc.) do double duty automatically: they enforce validation at runtime and populate the generated schema's constraints, with zero duplication between the two.
- `@Operation`, `@Parameter`, and `@Schema` let you add human-readable context (descriptions, examples) on top of the automatically-derived structural spec — use them generously for any endpoint consumed outside your own team, since types alone rarely explain *why* a field exists or what a realistic value looks like.
