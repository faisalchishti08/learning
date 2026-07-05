---
card: spring-framework
gi: 306
slug: uri-patterns-path-variables-pathvariable
title: "URI patterns & path variables (@PathVariable)"
---

## 1. What it is

**URI patterns** are the path templates registered on handler methods; they may contain:

- **Literal segments** — `/api/users`
- **Path variables** — `{id}` captures a single segment value
- **Wildcards** — `*` (one segment), `**` / `{*rest}` (multiple segments)
- **Regex constraints** — `{id:[0-9]+}` (only digits)

`@PathVariable` is the annotation that binds a captured segment to a method parameter:

```java
@GetMapping("/users/{id}")
public User getUser(@PathVariable long id) { ... }
// GET /users/42 → id = 42
```

Spring converts the captured string to the parameter type automatically using registered `ConversionService` converters.

---

## 2. Why & when

Path variables are the standard REST pattern for **resource identity** in URLs:

- `/users/{id}` — unique user
- `/orders/{orderId}/items/{itemId}` — nested resources
- `/files/{*path}` — arbitrary sub-path (download, tree browsing)

Use `@PathVariable` instead of `@RequestParam` when the identifier is part of the resource's URL structure (not an optional filter).

---

## 3. Core concept

```
Pattern:  /api/{version}/users/{id:[0-9]+}/{*extra}

Request:  /api/v2/users/42/profile/settings

Match result:
  version = "v2"
  id      = "42"   (validates: all digits)
  extra   = "profile/settings"   ({*extra} captures remainder with slashes)

Mapped to:
  @GetMapping("/api/{version}/users/{id:[0-9]+}/{*extra}")
  String handler(@PathVariable String version,
                 @PathVariable long id,
                 @PathVariable String extra) { ... }
```

---

## 4. Diagram

<svg viewBox="0 0 740 270" xmlns="http://www.w3.org/2000/svg" font-family="monospace" font-size="12">
  <rect width="740" height="270" fill="#0d1117"/>

  <!-- URL bar -->
  <rect x="10" y="20" width="720" height="36" rx="5" fill="#1c2430" stroke="#8b949e"/>
  <text x="370" y="40" text-anchor="middle" fill="#e6edf3">/api/v2/users/42/profile/settings</text>
  <text x="370" y="52" text-anchor="middle" fill="#8b949e" font-size="10">incoming request path</text>

  <!-- segment breakdown -->
  <rect x="10" y="80" width="50" height="30" rx="3" fill="#0d1117" stroke="#8b949e"/>
  <text x="35" y="99" text-anchor="middle" fill="#8b949e" font-size="11">api</text>

  <rect x="68" y="80" width="60" height="30" rx="3" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="98" y="99" text-anchor="middle" fill="#6db33f" font-size="11">v2</text>
  <text x="98" y="118" text-anchor="middle" fill="#6db33f" font-size="10">{version}</text>

  <rect x="136" y="80" width="60" height="30" rx="3" fill="#0d1117" stroke="#8b949e"/>
  <text x="166" y="99" text-anchor="middle" fill="#8b949e" font-size="11">users</text>

  <rect x="204" y="80" width="60" height="30" rx="3" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="234" y="99" text-anchor="middle" fill="#6db33f" font-size="11">42</text>
  <text x="234" y="118" text-anchor="middle" fill="#6db33f" font-size="10">{id:[0-9]+}</text>

  <rect x="272" y="80" width="170" height="30" rx="3" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="357" y="99" text-anchor="middle" fill="#79c0ff" font-size="11">profile/settings</text>
  <text x="357" y="118" text-anchor="middle" fill="#79c0ff" font-size="10">{*extra} — captures remainder with slashes</text>

  <!-- binding arrows -->
  <line x1="98" y1="110" x2="98" y2="160" stroke="#6db33f" stroke-dasharray="3,2" marker-end="url(#apv5)"/>
  <line x1="234" y1="110" x2="234" y2="160" stroke="#6db33f" stroke-dasharray="3,2" marker-end="url(#apv5)"/>
  <line x1="357" y1="118" x2="357" y2="160" stroke="#79c0ff" stroke-dasharray="3,2" marker-end="url(#apv5)"/>

  <!-- parameters row -->
  <rect x="20" y="160" width="155" height="40" rx="5" fill="#1c2430" stroke="#6db33f"/>
  <text x="97" y="176" text-anchor="middle" fill="#6db33f">@PathVariable</text>
  <text x="97" y="190" text-anchor="middle" fill="#8b949e" font-size="10">String version = "v2"</text>

  <rect x="185" y="160" width="145" height="40" rx="5" fill="#1c2430" stroke="#6db33f"/>
  <text x="257" y="176" text-anchor="middle" fill="#6db33f">@PathVariable</text>
  <text x="257" y="190" text-anchor="middle" fill="#8b949e" font-size="10">long id = 42</text>

  <rect x="340" y="160" width="200" height="40" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="440" y="176" text-anchor="middle" fill="#79c0ff">@PathVariable</text>
  <text x="440" y="190" text-anchor="middle" fill="#8b949e" font-size="10">String extra = "profile/settings"</text>

  <!-- caption -->
  <text x="370" y="245" text-anchor="middle" fill="#8b949e" font-size="11">Regex constraints validate at routing; {*var} captures slashes; type conversion is automatic</text>

  <defs>
    <marker id="apv5" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L0,6 L8,3 z" fill="#6db33f"/>
    </marker>
  </defs>
</svg>

*Literal segments narrow the match; captured segments bind to parameters with automatic type conversion.*

---

## 5. Runnable example

### Level 1 — Basic

Simple path variable — get a user by numeric ID:

```java
// UserController.java
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import java.util.Map;

@RestController
@RequestMapping("/api/users")
public class UserController {

    private final Map<Long, String> users = Map.of(1L, "Alice", 2L, "Bob");

    @GetMapping("/{id}")
    public ResponseEntity<String> getUser(@PathVariable long id) {
        String name = users.get(id);
        return name != null ? ResponseEntity.ok(name) : ResponseEntity.notFound().build();
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run

curl http://localhost:8080/api/users/1
# Alice

curl http://localhost:8080/api/users/99
# 404 Not Found
```

`@PathVariable long id` — Spring extracts the `{id}` segment string and converts it to `long` via `ConversionService`.  If the segment is not a valid `long` (e.g. `/api/users/abc`), Spring returns `400 Bad Request` before the method is called.

---

### Level 2 — Intermediate

Same user scenario — now with **regex constraints** to validate format at routing, and **nested resource** path (`/users/{userId}/orders/{orderId}`):

```java
// OrderController.java
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/users/{userId:[0-9]+}/orders")
public class OrderController {

    // GET /api/users/1/orders/ORD-42
    // Pattern: ORD- followed by one or more digits
    @GetMapping("/{orderId:ORD-[0-9]+}")
    public ResponseEntity<String> getOrder(
            @PathVariable long userId,
            @PathVariable String orderId) {
        return ResponseEntity.ok(
                "Order " + orderId + " for user " + userId);
    }

    // GET /api/users/1/orders — list all orders for user
    @GetMapping
    public String listOrders(@PathVariable long userId) {
        return "[\"ORD-1\",\"ORD-2\"]";
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run

curl http://localhost:8080/api/users/1/orders/ORD-42
# Order ORD-42 for user 1

curl http://localhost:8080/api/users/1/orders/INVALID
# 404 Not Found  (regex ORD-[0-9]+ did not match "INVALID")

curl http://localhost:8080/api/users/abc/orders
# 404 Not Found  (regex [0-9]+ did not match "abc")
```

**What changed:** `{userId:[0-9]+}` on the class-level mapping validates the user ID as all-digits before any method is tried — non-numeric user IDs get a 404 at routing.  `{orderId:ORD-[0-9]+}` enforces an order ID format.  Spring compares regex-constrained patterns against literal patterns with specificity scoring — a literal `/users/me` still beats `/users/{id:[0-9]+}` for the URL `/users/me`.

---

### Level 3 — Advanced

Production scenario: a **file-tree browser** endpoint using `{*path}` to capture the entire sub-path with slashes, with path-traversal prevention:

```java
// FileController.java
import org.springframework.core.io.*;
import org.springframework.http.*;
import org.springframework.web.bind.annotation.*;
import java.nio.file.*;

@RestController
@RequestMapping("/files")
public class FileController {

    private final Path root = Paths.get("/var/app/files").toAbsolutePath().normalize();

    // GET /files/reports/2024/jan.csv
    // GET /files/images/logo.png
    @GetMapping("/{*filePath}")
    public ResponseEntity<Resource> download(@PathVariable String filePath) {
        // filePath = "/reports/2024/jan.csv" (leading slash included with {*filePath})
        // Strip leading slash and normalize to prevent path traversal
        Path resolved = root.resolve(filePath.startsWith("/") ? filePath.substring(1) : filePath)
                           .normalize();

        // Security: reject any path that escapes the root
        if (!resolved.startsWith(root)) {
            return ResponseEntity.badRequest().build();
        }

        if (!Files.exists(resolved) || Files.isDirectory(resolved)) {
            return ResponseEntity.notFound().build();
        }

        Resource resource = new FileSystemResource(resolved);
        String contentType = guessContentType(resolved.getFileName().toString());
        return ResponseEntity.ok()
                .contentType(MediaType.parseMediaType(contentType))
                .header(HttpHeaders.CONTENT_DISPOSITION,
                        "attachment; filename=\"" + resolved.getFileName() + "\"")
                .body(resource);
    }

    private String guessContentType(String name) {
        if (name.endsWith(".csv"))  return "text/csv";
        if (name.endsWith(".pdf"))  return "application/pdf";
        if (name.endsWith(".png"))  return "image/png";
        if (name.endsWith(".json")) return "application/json";
        return "application/octet-stream";
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run

# Download a file
curl -OJ http://localhost:8080/files/reports/2024/jan.csv

# Path traversal attempt — rejected:
curl -i http://localhost:8080/files/%2F..%2F..%2Fetc%2Fpasswd
# HTTP/1.1 400 Bad Request
```

**What changed and why:**
- `{*filePath}` captures everything after `/files/` including slashes — `/reports/2024/jan.csv` as a single string.
- `{*filePath}` includes the leading slash in the captured value; stripping it before `root.resolve()` is necessary.
- `resolved.startsWith(root)` after `normalize()` is the canonical path-traversal check — it catches `/../` sequences even after URL decoding.
- `Content-Disposition: attachment; filename="..."` forces the browser to download rather than display the file inline.

<svg viewBox="0 0 700 200" xmlns="http://www.w3.org/2000/svg" font-family="monospace" font-size="11">
  <rect width="700" height="200" fill="#0d1117"/>
  <!-- path traversal check -->
  <rect x="10" y="40" width="150" height="36" rx="4" fill="#1c2430" stroke="#79c0ff"/>
  <text x="85" y="57" text-anchor="middle" fill="#79c0ff">{*filePath}</text>
  <text x="85" y="71" text-anchor="middle" fill="#8b949e" font-size="10">"/reports/2024/jan.csv"</text>
  <line x1="160" y1="58" x2="195" y2="58" stroke="#8b949e" marker-end="url(#apf)"/>
  <rect x="195" y="40" width="150" height="36" rx="4" fill="#1c2430" stroke="#6db33f"/>
  <text x="270" y="57" text-anchor="middle" fill="#6db33f">root.resolve(path)</text>
  <text x="270" y="71" text-anchor="middle" fill="#8b949e" font-size="10">.normalize()</text>
  <line x1="345" y1="58" x2="380" y2="58" stroke="#8b949e" marker-end="url(#apf)"/>
  <rect x="380" y="40" width="150" height="36" rx="4" fill="#1c2430" stroke="#6db33f"/>
  <text x="455" y="57" text-anchor="middle" fill="#6db33f">startsWith(root)?</text>
  <!-- yes -->
  <line x1="530" y1="58" x2="565" y2="58" stroke="#6db33f" marker-end="url(#apf)"/>
  <text x="547" y="52" fill="#6db33f" font-size="10">yes</text>
  <rect x="565" y="40" width="100" height="36" rx="4" fill="#1c2430" stroke="#8b949e"/>
  <text x="615" y="61" text-anchor="middle" fill="#8b949e">serve file</text>
  <!-- no -->
  <line x1="455" y1="76" x2="455" y2="120" stroke="#e74c3c" marker-end="url(#apf2)"/>
  <text x="465" y="105" fill="#e74c3c" font-size="10">no</text>
  <rect x="380" y="120" width="150" height="36" rx="4" fill="#1c2430" stroke="#e74c3c"/>
  <text x="455" y="140" text-anchor="middle" fill="#e74c3c">400 Bad Request</text>
  <text x="350" y="180" text-anchor="middle" fill="#8b949e" font-size="10">normalize() collapses ../ before startsWith() check — canonical path traversal prevention</text>
  <defs>
    <marker id="apf" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L0,6 L8,3 z" fill="#6db33f"/></marker>
    <marker id="apf2" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L0,6 L8,3 z" fill="#e74c3c"/></marker>
  </defs>
</svg>

---

## 6. Walkthrough

**Startup:**

1. `@GetMapping("/{*filePath}")` → `RequestMappingInfo{path=/files/{*filePath}, method=GET}`.
2. `PathPatternParser` parses `"/{*filePath}"` into a `WildcardTheRestPathElement` that matches zero or more segments (including slashes).

**Per-request: `GET /files/reports/2024/jan.csv`:**

3. `DispatcherServlet` calls `HandlerMapping.getHandler()`.
4. Pattern `/files/{*filePath}` matches. `filePath` captures `"/reports/2024/jan.csv"` (with leading slash — this is the `{*var}` behaviour).
5. `HandlerAdapter` resolves `@PathVariable String filePath` from `URI_TEMPLATE_VARIABLES_ATTRIBUTE`.
6. `download("/reports/2024/jan.csv")` executes:
   a. Strips leading `/` → `"reports/2024/jan.csv"`.
   b. `root.resolve("reports/2024/jan.csv")` → `/var/app/files/reports/2024/jan.csv`.
   c. `normalize()` — no change (no `..`).
   d. `startsWith(root)` → `true` — safe to proceed.
   e. `Files.exists(resolved)` → `true`; not a directory.
   f. Returns `ResponseEntity` with `FileSystemResource`.
7. `ResourceHttpMessageConverter` streams the file to the response.

**Path traversal attempt: `GET /files/%2F..%2F..%2Fetc%2Fpasswd`:**

After URL decoding (by the container): filePath = `"/../../../etc/passwd"`.
`root.resolve("../../etc/passwd").normalize()` → `/etc/passwd`.
`startsWith(root)` → `false` → `400 Bad Request`. File never touched.

---

## 7. Gotchas & takeaways

> **`{*var}` captures the leading slash.**  `/files/{*path}` matching `/files/a/b` gives `path = "/a/b"`, not `"a/b"`.  Always strip the leading `/` before passing to `Path.resolve()`.

> **Regex patterns with `:` in the variable name must escape the colon in some tools.**  `{id:[0-9]+}` works correctly in annotations, but hand-crafting URLs for curl or HTTP clients requires proper encoding.

> **`@PathVariable` without `name` uses the parameter name at runtime.**  With `-parameters` compiler flag (enabled by Spring Boot's build), the parameter name is available in bytecode.  Without it, you must use `@PathVariable("id")` explicitly.

- `{var}` captures one segment (no slashes); `{*var}` captures the remainder including slashes.
- `{var:regex}` validates format at routing — invalid format → 404 (no handler match), not 400.
- Path variables are type-converted automatically; non-convertible values → 400 `MethodArgumentTypeMismatchException`.
- Regex specificity: `{id:[0-9]+}` scores higher than `{id}` for the same segment position.
- Always `normalize()` + `startsWith(root)` when using path variables to serve files — never trust user-supplied paths.
