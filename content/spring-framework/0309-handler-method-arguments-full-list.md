---
card: spring-framework
gi: 309
slug: handler-method-arguments-full-list
title: "Handler method arguments (full list)"
---

## 1. What it is

A **handler method** is any method annotated with `@RequestMapping` (or a composed shortcut). Spring MVC automatically resolves the method's parameters — you declare what you need and Spring injects the right value before calling your method.

The full set of supported argument types (grouped by category):

**Request data**
- `@PathVariable` — URI template variable
- `@RequestParam` — query-string or form parameter
- `@RequestHeader` — request header value
- `@CookieValue` — cookie value
- `@RequestBody` — deserialised request body
- `@RequestPart` — multipart form field
- `@ModelAttribute` — form-bound model object

**Request metadata**
- `HttpServletRequest` / `HttpServletResponse` — raw servlet objects
- `HttpMethod` — the HTTP method
- `WebRequest` / `NativeWebRequest` — framework wrapper
- `HttpSession` — the HTTP session
- `Principal` — authenticated principal
- `Locale` — resolved locale
- `TimeZone` / `ZoneId` — resolved time zone
- `InputStream` / `Reader` — raw request body stream
- `OutputStream` / `Writer` — raw response body stream
- `UriComponentsBuilder` — for building redirect URLs

**Model & binding**
- `Model` / `ModelMap` — the view model
- `RedirectAttributes` — model attributes for redirect
- `BindingResult` — validation result for `@ModelAttribute` or `@RequestBody`
- `SessionStatus` — to signal session completion
- `@SessionAttribute` — session attribute

**Special**
- `@RequestAttribute` — request-scoped attribute (set by interceptors/filters)
- `Errors` — alias for `BindingResult`
- `Map<String,?>` — view model (same as `Model`)

---

## 2. Why & when

Spring's argument resolution removes all the boilerplate of parsing `request.getParameter()`, deserialising JSON, or pulling values from the session. Declare exactly what you need — Spring wires it in.

Knowing the full list lets you:
- Pick the right argument type for the job (e.g. `BindingResult` instead of catching `MethodArgumentNotValidException`).
- Avoid pulling in `HttpServletRequest` when `@PathVariable` + `@RequestParam` would be cleaner.
- Use `UriComponentsBuilder` for building redirect URIs rather than string concatenation.

---

## 3. Core concept

```
Handler method signature (Spring resolves each parameter independently):

@PostMapping("/users")
public ResponseEntity<UserDto> createUser(
    @RequestHeader("X-Tenant-ID") String tenantId,   // ← header resolver
    @RequestBody @Valid CreateUserRequest body,        // ← body resolver + @Valid
    BindingResult errors,                             // ← MUST follow @Valid argument
    UriComponentsBuilder uriBuilder,                  // ← injected by framework
    Principal principal                               // ← from SecurityContext
) { ... }

Resolution order: Spring iterates registered HandlerMethodArgumentResolver
implementations in priority order. First one that supports the parameter wins.
```

---

## 4. Diagram

<svg viewBox="0 0 740 310" xmlns="http://www.w3.org/2000/svg" font-family="monospace" font-size="11">
  <rect width="740" height="310" fill="#0d1117"/>

  <!-- request -->
  <rect x="10" y="130" width="120" height="50" rx="5" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="70" y="150" text-anchor="middle" fill="#79c0ff">HTTP Request</text>
  <text x="70" y="164" text-anchor="middle" fill="#8b949e" font-size="10">POST /users</text>
  <text x="70" y="177" text-anchor="middle" fill="#8b949e" font-size="10">JSON body</text>

  <line x1="130" y1="155" x2="165" y2="155" stroke="#8b949e" marker-end="url(#aarg)"/>

  <!-- resolver chain -->
  <rect x="165" y="50" width="340" height="210" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1"/>
  <text x="335" y="72" text-anchor="middle" fill="#6db33f" font-weight="bold">HandlerMethodArgumentResolver chain</text>
  <rect x="175" y="80" width="320" height="22" rx="3" fill="#0d1117" stroke="#6db33f"/>
  <text x="335" y="95" text-anchor="middle" fill="#6db33f" font-size="10">PathVariableMethodArgumentResolver (@PathVariable)</text>
  <rect x="175" y="106" width="320" height="22" rx="3" fill="#0d1117" stroke="#6db33f"/>
  <text x="335" y="121" text-anchor="middle" fill="#6db33f" font-size="10">RequestParamMethodArgumentResolver (@RequestParam)</text>
  <rect x="175" y="132" width="320" height="22" rx="3" fill="#0d1117" stroke="#6db33f"/>
  <text x="335" y="147" text-anchor="middle" fill="#6db33f" font-size="10">RequestHeaderMethodArgumentResolver (@RequestHeader)</text>
  <rect x="175" y="158" width="320" height="22" rx="3" fill="#0d1117" stroke="#6db33f"/>
  <text x="335" y="173" text-anchor="middle" fill="#6db33f" font-size="10">RequestResponseBodyMethodProcessor (@RequestBody)</text>
  <rect x="175" y="184" width="320" height="22" rx="3" fill="#0d1117" stroke="#8b949e"/>
  <text x="335" y="199" text-anchor="middle" fill="#8b949e" font-size="10">ModelAttributeMethodProcessor (@ModelAttribute)</text>
  <rect x="175" y="210" width="320" height="22" rx="3" fill="#0d1117" stroke="#8b949e"/>
  <text x="335" y="225" text-anchor="middle" fill="#8b949e" font-size="10">HttpServletRequest / Principal / Locale / …</text>
  <rect x="175" y="236" width="320" height="16" rx="3" fill="#0d1117" stroke="#8b949e"/>
  <text x="335" y="248" text-anchor="middle" fill="#8b949e" font-size="10">… 30+ total resolvers</text>

  <!-- arrow to method -->
  <line x1="505" y1="155" x2="545" y2="155" stroke="#6db33f" marker-end="url(#aarg)"/>

  <!-- controller method -->
  <rect x="545" y="100" width="185" height="110" rx="5" fill="#1c2430" stroke="#79c0ff" stroke-width="1"/>
  <text x="637" y="118" text-anchor="middle" fill="#79c0ff">createUser(</text>
  <text x="637" y="133" text-anchor="middle" fill="#8b949e" font-size="10">tenantId="ACME",</text>
  <text x="637" y="147" text-anchor="middle" fill="#8b949e" font-size="10">body={name:"Alice"},</text>
  <text x="637" y="161" text-anchor="middle" fill="#8b949e" font-size="10">errors=BindingResult,</text>
  <text x="637" y="175" text-anchor="middle" fill="#8b949e" font-size="10">uriBuilder=...,</text>
  <text x="637" y="189" text-anchor="middle" fill="#8b949e" font-size="10">principal=alice</text>
  <text x="637" y="203" text-anchor="middle" fill="#8b949e" font-size="10">)</text>

  <text x="370" y="285" text-anchor="middle" fill="#8b949e" font-size="11">Each parameter resolved independently by its matching resolver — order of parameters doesn't matter</text>

  <defs>
    <marker id="aarg" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L0,6 L8,3 z" fill="#8b949e"/>
    </marker>
  </defs>
</svg>

*Each resolver handles one type of parameter; Spring picks the right resolver for each argument independently.*

---

## 5. Runnable example

### Level 1 — Basic

A handler method using the most common argument types:

```java
// UserController.java
import org.springframework.http.*;
import org.springframework.web.bind.annotation.*;
import java.util.Locale;
import java.security.Principal;

@RestController
@RequestMapping("/api/users")
public class UserController {

    @GetMapping("/{id}")
    public ResponseEntity<String> getUser(
            @PathVariable long id,                         // URI segment
            @RequestParam(defaultValue = "false") boolean verbose,  // query param
            @RequestHeader(value = "Accept-Language",
                           required = false) String lang, // header (optional)
            Locale locale,                                 // resolved locale
            Principal principal) {                        // authenticated user (null if anonymous)

        String who = principal != null ? principal.getName() : "anonymous";
        String response = String.format(
                "id=%d verbose=%b lang=%s locale=%s requestedBy=%s",
                id, verbose, lang, locale, who);
        return ResponseEntity.ok(response);
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run

curl -H "Accept-Language: fr" "http://localhost:8080/api/users/1?verbose=true"
# id=1 verbose=true lang=fr locale=fr requestedBy=anonymous
```

Spring resolves each parameter from a different source: `@PathVariable` from the URI template, `@RequestParam` from the query string (with a default when absent), `@RequestHeader` from the HTTP header, `Locale` from `LocaleContextHolder`, and `Principal` from the security context. No `HttpServletRequest` needed.

---

### Level 2 — Intermediate

Same user endpoint — now adding `@RequestBody` with validation, `BindingResult`, and `UriComponentsBuilder` for redirect:

```java
// UserController.java (extended)
import jakarta.validation.Valid;
import jakarta.validation.constraints.*;
import org.springframework.http.*;
import org.springframework.validation.BindingResult;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.util.UriComponentsBuilder;
import java.util.Map;

@RestController
@RequestMapping("/api/users")
public class UserController {

    @PostMapping(consumes = MediaType.APPLICATION_JSON_VALUE)
    public ResponseEntity<?> createUser(
            @RequestBody @Valid CreateRequest body,  // deserialise + validate
            BindingResult errors,                   // MUST follow the @Valid arg
            UriComponentsBuilder uriBuilder) {     // framework-injected builder

        if (errors.hasErrors()) {
            Map<String, String> fieldErrors = new java.util.LinkedHashMap<>();
            errors.getFieldErrors().forEach(fe ->
                    fieldErrors.put(fe.getField(), fe.getDefaultMessage()));
            return ResponseEntity.badRequest().body(fieldErrors);
        }

        long newId = 42L;
        // Build the Location URI from the request's base URL — portable across deployments
        var location = uriBuilder.path("/api/users/{id}").buildAndExpand(newId).toUri();
        return ResponseEntity.created(location).body(Map.of("id", newId, "name", body.name()));
    }

    record CreateRequest(
        @NotBlank @Size(max = 100) String name,
        @Email String email
    ) {}
}
```

**How to run:**
```bash
./mvnw spring-boot:run

# Valid request
curl -i -X POST -H "Content-Type: application/json" \
     -d '{"name":"Alice","email":"alice@example.com"}' \
     http://localhost:8080/api/users
# 201 Created  Location: http://localhost:8080/api/users/42

# Invalid request
curl -X POST -H "Content-Type: application/json" \
     -d '{"name":"","email":"bad"}' http://localhost:8080/api/users
# {"name":"must not be blank","email":"must be a well-formed email address"}
```

**What changed:** `BindingResult` must immediately follow the `@Valid`-annotated argument — Spring populates it instead of throwing `MethodArgumentNotValidException`. `UriComponentsBuilder` is injected with the current request's base URL, so `Location` headers work correctly behind a proxy without hardcoding hostnames.

---

### Level 3 — Advanced

Production scenario: handler combining `@RequestAttribute` (set by an interceptor), `@SessionAttribute`, `@CookieValue`, raw `InputStream` for streaming upload, and `RedirectAttributes` for flash messages:

```java
// OrderController.java
import jakarta.servlet.http.HttpSession;
import org.springframework.http.*;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.servlet.mvc.support.RedirectAttributes;
import java.io.*;

@Controller
@RequestMapping("/orders")
public class OrderController {

    // Interceptor sets "correlationId" before this method runs
    @PostMapping("/upload")
    public String uploadOrder(
            @RequestAttribute("correlationId") String correlationId,  // from interceptor
            @SessionAttribute(name = "cartId", required = false) String cartId, // from session
            @CookieValue(name = "preferredFormat",
                         defaultValue = "json") String format,     // from cookie
            InputStream requestBody,                                 // raw stream for large file
            RedirectAttributes redirectAttrs) throws IOException {  // for flash message on redirect

        // Stream the body directly to storage (no heap buffering)
        long bytes = requestBody.transferTo(OutputStream.nullOutputStream());

        redirectAttrs.addFlashAttribute("message",
                "Upload complete: " + bytes + " bytes [corr=" + correlationId +
                " cart=" + cartId + " format=" + format + "]");
        return "redirect:/orders";
    }

    @GetMapping
    public String listOrders(
            @ModelAttribute("message") String flashMessage,  // consumed from flash scope
            org.springframework.ui.Model model) {
        model.addAttribute("flash", flashMessage);
        return "orders/list";
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run

# Upload — session/cookie/interceptor all feed arguments
curl -c cookies.txt -b cookies.txt \
     -X POST -H "Content-Type: application/octet-stream" \
     --data-binary @order.json \
     http://localhost:8080/orders/upload
# 302 → /orders

# List page shows flash message
curl -c cookies.txt -b cookies.txt http://localhost:8080/orders
# "Upload complete: 1024 bytes [corr=abc123 cart=CART-7 format=json]"
```

**What changed and why:**
- `@RequestAttribute("correlationId")` reads a value placed by a `HandlerInterceptor.preHandle()` — decouples the interceptor from the controller signature.
- `@SessionAttribute` reads from the HTTP session without injecting `HttpSession` directly — cleaner and testable.
- `@CookieValue` with `defaultValue` reads the browser cookie safely — no `NullPointerException` when cookie is absent.
- `InputStream requestBody` bypasses `@RequestBody` deserialization entirely — Spring gives the raw servlet input stream, ideal for streaming large uploads without loading into heap.
- `RedirectAttributes.addFlashAttribute()` stores data in the session for exactly one subsequent request (flash scope), then removes it — safe POST/Redirect/GET pattern with no URL-encoded state.

<svg viewBox="0 0 700 200" xmlns="http://www.w3.org/2000/svg" font-family="monospace" font-size="11">
  <rect width="700" height="200" fill="#0d1117"/>
  <!-- sources -->
  <rect x="10" y="30" width="120" height="24" rx="3" fill="#1c2430" stroke="#8b949e"/>
  <text x="70" y="46" text-anchor="middle" fill="#8b949e">Interceptor attr</text>
  <rect x="10" y="62" width="120" height="24" rx="3" fill="#1c2430" stroke="#8b949e"/>
  <text x="70" y="78" text-anchor="middle" fill="#8b949e">HTTP Session</text>
  <rect x="10" y="94" width="120" height="24" rx="3" fill="#1c2430" stroke="#8b949e"/>
  <text x="70" y="110" text-anchor="middle" fill="#8b949e">Cookie</text>
  <rect x="10" y="126" width="120" height="24" rx="3" fill="#1c2430" stroke="#8b949e"/>
  <text x="70" y="142" text-anchor="middle" fill="#8b949e">Raw InputStream</text>
  <!-- arrows -->
  <line x1="130" y1="42" x2="205" y2="85" stroke="#6db33f" stroke-dasharray="3,2" marker-end="url(#aarg2)"/>
  <line x1="130" y1="74" x2="205" y2="90" stroke="#6db33f" stroke-dasharray="3,2" marker-end="url(#aarg2)"/>
  <line x1="130" y1="106" x2="205" y2="96" stroke="#6db33f" stroke-dasharray="3,2" marker-end="url(#aarg2)"/>
  <line x1="130" y1="138" x2="205" y2="102" stroke="#6db33f" stroke-dasharray="3,2" marker-end="url(#aarg2)"/>
  <!-- method box -->
  <rect x="205" y="60" width="200" height="60" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="305" y="80" text-anchor="middle" fill="#6db33f">uploadOrder(</text>
  <text x="305" y="95" text-anchor="middle" fill="#8b949e" font-size="10">correlationId, cartId,</text>
  <text x="305" y="108" text-anchor="middle" fill="#8b949e" font-size="10">format, body, redirectAttrs)</text>
  <!-- redirect -->
  <line x1="405" y1="90" x2="450" y2="90" stroke="#8b949e" marker-end="url(#aarg2)"/>
  <rect x="450" y="70" width="120" height="40" rx="3" fill="#1c2430" stroke="#79c0ff"/>
  <text x="510" y="88" text-anchor="middle" fill="#79c0ff">302 → /orders</text>
  <text x="510" y="102" text-anchor="middle" fill="#8b949e" font-size="10">flash in session</text>
  <text x="350" y="170" text-anchor="middle" fill="#8b949e" font-size="10">Each argument sourced independently — no HttpServletRequest boilerplate</text>
  <defs><marker id="aarg2" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L0,6 L8,3 z" fill="#6db33f"/></marker></defs>
</svg>

---

## 6. Walkthrough

**Startup:**

1. `RequestMappingHandlerAdapter` collects all registered `HandlerMethodArgumentResolver` implementations — 30+ in a default Spring Boot app.
2. For each handler method, Spring inspects parameter annotations and types; at first invocation it selects the resolver for each parameter and caches the selection.

**Per-request: `POST /orders/upload`:**

3. `HandlerInterceptor.preHandle()` runs first: sets `req.setAttribute("correlationId", "abc123")`.
4. `HandlerAdapter.invokeHandlerMethod()` starts resolving arguments in order:
   - `@RequestAttribute("correlationId")` → `RequestAttributeMethodArgumentResolver` reads `req.getAttribute("correlationId")` → `"abc123"`.
   - `@SessionAttribute("cartId")` → `SessionAttributeMethodArgumentResolver` reads `req.getSession().getAttribute("cartId")` → `"CART-7"` (or null if absent).
   - `@CookieValue("preferredFormat")` → `ServletCookieValueMethodArgumentResolver` finds cookie `preferredFormat=json` → `"json"`. Default `"json"` used if absent.
   - `InputStream requestBody` → `RequestParamMethodArgumentResolver` detects `InputStream.class` → returns `req.getInputStream()`.
   - `RedirectAttributes redirectAttrs` → `RedirectAttributesMethodArgumentResolver` creates a `RedirectAttributesModelMap`.
5. `uploadOrder("abc123","CART-7","json", inputStream, redirectAttrs)` executes.
6. `inputStream.transferTo(nullOutputStream())` streams body without heap allocation.
7. `redirectAttrs.addFlashAttribute("message", "Upload complete: 1024 bytes [...]")`.
8. Returns `"redirect:/orders"` → `DispatcherServlet` sends `302 Location: /orders` and stores flash attributes in session.

**Per-request: `GET /orders` (after redirect):**

9. `DispatcherServlet` checks session for flash attributes; finds `{message: "Upload complete:..."}`.
10. Merges into the model before calling `listOrders`.
11. `@ModelAttribute("message") String flashMessage` bound from model → `"Upload complete: 1024 bytes [...]"`.
12. Flash attribute removed from session.

---

## 7. Gotchas & takeaways

> **`BindingResult` must immediately follow the `@Valid`-annotated parameter.**  If there's any other parameter between them, Spring throws `IllegalStateException` at startup.  The binding result belongs to the validated object directly preceding it.

> **`InputStream` / `Reader` as a parameter bypasses `@RequestBody` — you can only read the request body once.**  Once `InputStream` is read, it is exhausted; `@RequestBody` on another parameter in the same method will read an empty stream.  Never mix raw stream arguments with `@RequestBody`.

> **`Principal` is `null` for unauthenticated requests** (when Spring Security is not enforcing authentication).  Always null-check `Principal` or use `@AuthenticationPrincipal` from Spring Security for typed principal access.

- Spring resolves each parameter independently — order of parameters in the method signature does not matter (except `BindingResult` immediately after `@Valid`).
- Use `@RequestAttribute` to receive data set by interceptors — cleaner than injecting `HttpServletRequest`.
- `UriComponentsBuilder` builds proxy-aware URLs; never hardcode host:port in `Location` headers.
- `RedirectAttributes.addFlashAttribute()` stores data for exactly one redirect — cleared automatically after the redirect target reads it.
- `InputStream` is ideal for large uploads; `@RequestBody` is ideal for small JSON payloads that need deserialization.
