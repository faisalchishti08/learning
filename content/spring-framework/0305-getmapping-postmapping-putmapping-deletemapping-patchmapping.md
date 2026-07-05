---
card: spring-framework
gi: 305
slug: getmapping-postmapping-putmapping-deletemapping-patchmapping
title: "@GetMapping/@PostMapping/@PutMapping/@DeleteMapping/@PatchMapping"
---

## 1. What it is

`@GetMapping`, `@PostMapping`, `@PutMapping`, `@DeleteMapping`, and `@PatchMapping` are **composed annotations** — each is `@RequestMapping` with the `method` attribute pre-set to the corresponding `RequestMethod` enum value.

```java
@GetMapping("/users")     // ≡ @RequestMapping(method=GET,    value="/users")
@PostMapping("/users")    // ≡ @RequestMapping(method=POST,   value="/users")
@PutMapping("/users/{id}")// ≡ @RequestMapping(method=PUT,    value="/users/{id}")
@DeleteMapping("/users/{id}")// ≡ @RequestMapping(method=DELETE, value="/users/{id}")
@PatchMapping("/users/{id}") // ≡ @RequestMapping(method=PATCH,  value="/users/{id}")
```

They accept the same attributes as `@RequestMapping` except `method` (already fixed): `value`/`path`, `produces`, `consumes`, `params`, `headers`, and `name`.

---

## 2. Why & when

Use the composed shortcuts in almost every case — they are:

- **Shorter** — `@GetMapping("/users")` vs `@RequestMapping(value="/users", method=RequestMethod.GET)`.
- **Safer** — you cannot accidentally omit the HTTP method; it is baked in.
- **Self-documenting** — the method name tells you the HTTP verb immediately.

Use the full `@RequestMapping` only when you need `method = {GET, HEAD}` (multiple methods) or when building a meta-annotation that composes conditions from two or more of these shortcuts.

---

## 3. Core concept

```
REST resource pattern — standard HTTP verbs on /api/items:

  GET    /api/items       → list all
  POST   /api/items       → create new
  GET    /api/items/{id}  → read one
  PUT    /api/items/{id}  → replace (full update)
  PATCH  /api/items/{id}  → partial update
  DELETE /api/items/{id}  → remove

Each verb maps to a dedicated method via the corresponding composed annotation.
All five share the same URL pattern ("/api/items" or "/api/items/{id}");
the HTTP method is the only differentiator.
```

---

## 4. Diagram

<svg viewBox="0 0 740 320" xmlns="http://www.w3.org/2000/svg" font-family="monospace" font-size="12">
  <rect width="740" height="320" fill="#0d1117"/>

  <!-- Client -->
  <rect x="10" y="140" width="80" height="40" rx="5" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="50" y="163" text-anchor="middle" fill="#79c0ff">Client</text>

  <!-- arrows for each verb -->
  <line x1="90" y1="145" x2="195" y2="60" stroke="#6db33f" stroke-width="1" marker-end="url(#apv)"/>
  <text x="130" y="85" fill="#6db33f" font-size="11">GET</text>

  <line x1="90" y1="150" x2="195" y2="120" stroke="#79c0ff" stroke-width="1" marker-end="url(#apv2)"/>
  <text x="130" y="132" fill="#79c0ff" font-size="11">POST</text>

  <line x1="90" y1="160" x2="195" y2="180" stroke="#e6edf3" stroke-width="1" marker-end="url(#apv3)"/>
  <text x="130" y="175" fill="#e6edf3" font-size="11">PUT</text>

  <line x1="90" y1="170" x2="195" y2="240" stroke="#8b949e" stroke-width="1" marker-end="url(#apv4)"/>
  <text x="130" y="220" fill="#8b949e" font-size="11">DELETE</text>

  <line x1="90" y1="165" x2="195" y2="300" stroke="#8b949e" stroke-width="1" marker-end="url(#apv4)"/>
  <text x="130" y="290" fill="#8b949e" font-size="11">PATCH</text>

  <!-- method boxes -->
  <rect x="195" y="40" width="200" height="36" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="295" y="57" text-anchor="middle" fill="#6db33f">@GetMapping("/items/{id}")</text>
  <text x="295" y="70" text-anchor="middle" fill="#8b949e" font-size="10">getItem(@PathVariable)</text>

  <rect x="195" y="100" width="200" height="36" rx="5" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="295" y="117" text-anchor="middle" fill="#79c0ff">@PostMapping("/items")</text>
  <text x="295" y="130" text-anchor="middle" fill="#8b949e" font-size="10">createItem(@RequestBody)</text>

  <rect x="195" y="160" width="200" height="36" rx="5" fill="#1c2430" stroke="#e6edf3" stroke-width="1"/>
  <text x="295" y="177" text-anchor="middle" fill="#e6edf3">@PutMapping("/items/{id}")</text>
  <text x="295" y="190" text-anchor="middle" fill="#8b949e" font-size="10">replaceItem(@PathVariable, @RequestBody)</text>

  <rect x="195" y="220" width="200" height="36" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="295" y="237" text-anchor="middle" fill="#8b949e">@DeleteMapping("/items/{id}")</text>
  <text x="295" y="250" text-anchor="middle" fill="#8b949e" font-size="10">deleteItem(@PathVariable)</text>

  <rect x="195" y="280" width="200" height="36" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="295" y="297" text-anchor="middle" fill="#8b949e">@PatchMapping("/items/{id}")</text>
  <text x="295" y="310" text-anchor="middle" fill="#8b949e" font-size="10">patchItem(@PathVariable, @RequestBody)</text>

  <!-- right side dispatch -->
  <rect x="430" y="140" width="130" height="40" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1"/>
  <text x="495" y="162" text-anchor="middle" fill="#6db33f">ItemService</text>
  <line x1="395" y1="138" x2="428" y2="155" stroke="#8b949e" marker-end="url(#apv)"/>
  <line x1="395" y1="155" x2="428" y2="158" stroke="#8b949e" marker-end="url(#apv)"/>
  <line x1="395" y1="178" x2="428" y2="162" stroke="#8b949e" marker-end="url(#apv)"/>

  <!-- caption -->
  <text x="370" y="300" text-anchor="middle" fill="#8b949e" font-size="10">Each HTTP verb dispatches to exactly one method — no if-else on method inside controller</text>

  <defs>
    <marker id="apv" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L0,6 L8,3 z" fill="#6db33f"/></marker>
    <marker id="apv2" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L0,6 L8,3 z" fill="#79c0ff"/></marker>
    <marker id="apv3" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L0,6 L8,3 z" fill="#e6edf3"/></marker>
    <marker id="apv4" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L0,6 L8,3 z" fill="#8b949e"/></marker>
  </defs>
</svg>

*Each HTTP verb maps to exactly one handler method — no branching inside the method based on `request.getMethod()`.*

---

## 5. Runnable example

### Level 1 — Basic

A full CRUD controller for a `Task` resource:

```java
// TaskController.java
import org.springframework.http.*;
import org.springframework.web.bind.annotation.*;
import java.util.*;

@RestController
@RequestMapping("/api/tasks")
public class TaskController {

    private final Map<Long, String> tasks = new LinkedHashMap<>(Map.of(1L, "Buy groceries", 2L, "Write tests"));

    @GetMapping
    public Collection<String> list() { return tasks.values(); }

    @GetMapping("/{id}")
    public ResponseEntity<String> get(@PathVariable Long id) {
        String task = tasks.get(id);
        return task != null ? ResponseEntity.ok(task) : ResponseEntity.notFound().build();
    }

    @PostMapping
    public ResponseEntity<String> create(@RequestBody String name) {
        long id = tasks.size() + 1;
        tasks.put(id, name);
        return ResponseEntity.status(201)
                .header(HttpHeaders.LOCATION, "/api/tasks/" + id)
                .body(name);
    }

    @PutMapping("/{id}")
    public ResponseEntity<String> replace(@PathVariable Long id, @RequestBody String name) {
        if (!tasks.containsKey(id)) return ResponseEntity.notFound().build();
        tasks.put(id, name);
        return ResponseEntity.ok(name);
    }

    @DeleteMapping("/{id}")
    public ResponseEntity<Void> delete(@PathVariable Long id) {
        return tasks.remove(id) != null
                ? ResponseEntity.noContent().build()
                : ResponseEntity.notFound().build();
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run

curl http://localhost:8080/api/tasks
# ["Buy groceries","Write tests"]

curl -X POST -H "Content-Type: application/json" \
     -d '"Deploy app"' http://localhost:8080/api/tasks
# 201 Created  Location: /api/tasks/3

curl -X PUT -H "Content-Type: application/json" \
     -d '"Deploy to prod"' http://localhost:8080/api/tasks/3
# 200 "Deploy to prod"

curl -X DELETE http://localhost:8080/api/tasks/3
# 204 No Content
```

Each HTTP verb routes to a dedicated method — no `switch (method)` logic inside the controller.  `@DeleteMapping` returns `204 No Content` (standard for successful deletion with no body).  `@PostMapping` returns `201 Created` with a `Location` header pointing to the new resource.

---

### Level 2 — Intermediate

Same Task CRUD — now adding `@PatchMapping` for partial updates and `consumes`/`produces` constraints for strict content negotiation:

```java
// TaskController.java (extended)
import org.springframework.http.*;
import org.springframework.web.bind.annotation.*;
import java.util.*;

@RestController
@RequestMapping(value = "/api/tasks", produces = MediaType.APPLICATION_JSON_VALUE)
public class TaskController {

    private final Map<Long, Task> tasks = new LinkedHashMap<>(Map.of(
            1L, new Task("Buy groceries", false),
            2L, new Task("Write tests", false)));

    @GetMapping
    public Collection<Task> list() { return tasks.values(); }

    @GetMapping("/{id}")
    public ResponseEntity<Task> get(@PathVariable Long id) {
        Task t = tasks.get(id);
        return t != null ? ResponseEntity.ok(t) : ResponseEntity.notFound().build();
    }

    @PostMapping(consumes = MediaType.APPLICATION_JSON_VALUE)
    public ResponseEntity<Task> create(@RequestBody Task task) {
        long id = tasks.size() + 1;
        tasks.put(id, task);
        return ResponseEntity.status(201).header("Location", "/api/tasks/" + id).body(task);
    }

    @PutMapping(value = "/{id}", consumes = MediaType.APPLICATION_JSON_VALUE)
    public ResponseEntity<Task> replace(@PathVariable Long id, @RequestBody Task task) {
        if (!tasks.containsKey(id)) return ResponseEntity.notFound().build();
        tasks.put(id, task);
        return ResponseEntity.ok(task);
    }

    // PATCH — partial update: only fields present in the request body are updated
    @PatchMapping(value = "/{id}", consumes = "application/merge-patch+json")
    public ResponseEntity<Task> patch(@PathVariable Long id, @RequestBody Map<String, Object> patch) {
        Task existing = tasks.get(id);
        if (existing == null) return ResponseEntity.notFound().build();
        if (patch.containsKey("name"))      existing.setName((String) patch.get("name"));
        if (patch.containsKey("completed")) existing.setCompleted((Boolean) patch.get("completed"));
        return ResponseEntity.ok(existing);
    }

    @DeleteMapping("/{id}")
    public ResponseEntity<Void> delete(@PathVariable Long id) {
        return tasks.remove(id) != null ? ResponseEntity.noContent().build() : ResponseEntity.notFound().build();
    }

    static class Task {
        private String name;
        private boolean completed;
        Task(String name, boolean completed) { this.name=name; this.completed=completed; }
        public String getName() { return name; }
        public boolean isCompleted() { return completed; }
        public void setName(String n) { this.name=n; }
        public void setCompleted(boolean c) { this.completed=c; }
    }
}
```

**How to run:**
```bash
curl -X PATCH -H "Content-Type: application/merge-patch+json" \
     -d '{"completed":true}' http://localhost:8080/api/tasks/1
# {"name":"Buy groceries","completed":true}

curl -X PUT -H "Content-Type: application/json" \
     -d '{"name":"Read a book","completed":false}' http://localhost:8080/api/tasks/1
# {"name":"Read a book","completed":false}
```

**What changed:** `@PatchMapping` uses `consumes = "application/merge-patch+json"` (RFC 7396) — the handler only matches PATCH requests with that specific content type, separating it from a regular `application/json` PUT.  PATCH applies only the provided fields; PUT replaces the entire resource.

---

### Level 3 — Advanced

Production scenario: a Task controller with **idempotency keys** on POST (to prevent duplicate creation on retry), **conditional PUT** using `If-Match` ETags, and a soft-delete PATCH:

```java
// TaskController.java (production)
import org.springframework.http.*;
import org.springframework.web.bind.annotation.*;
import java.util.*;
import java.util.concurrent.ConcurrentHashMap;

@RestController
@RequestMapping(value = "/api/tasks", produces = MediaType.APPLICATION_JSON_VALUE)
public class TaskController {

    private final Map<Long, Task> tasks = new ConcurrentHashMap<>();
    private final Map<String, Long> idempotencyKeys = new ConcurrentHashMap<>();
    private long nextId = 1;

    @PostMapping(consumes = MediaType.APPLICATION_JSON_VALUE)
    public ResponseEntity<Task> create(
            @RequestBody Task task,
            @RequestHeader(value = "Idempotency-Key", required = false) String idempotencyKey) {

        // If this idempotency key was already processed, return the previously created resource
        if (idempotencyKey != null && idempotencyKeys.containsKey(idempotencyKey)) {
            Long existingId = idempotencyKeys.get(idempotencyKey);
            return ResponseEntity.status(200).body(tasks.get(existingId));
        }

        long id = nextId++;
        task.setId(id);
        tasks.put(id, task);
        if (idempotencyKey != null) idempotencyKeys.put(idempotencyKey, id);

        return ResponseEntity.status(201)
                .header(HttpHeaders.LOCATION, "/api/tasks/" + id)
                .eTag("\"v" + id + "\"")
                .body(task);
    }

    @PutMapping(value = "/{id}", consumes = MediaType.APPLICATION_JSON_VALUE)
    public ResponseEntity<Task> conditionalReplace(
            @PathVariable Long id,
            @RequestBody Task update,
            @RequestHeader(value = "If-Match", required = false) String ifMatch) {

        Task existing = tasks.get(id);
        if (existing == null) return ResponseEntity.notFound().build();

        String currentETag = "\"v" + existing.getVersion() + "\"";
        if (ifMatch != null && !ifMatch.equals(currentETag)) {
            return ResponseEntity.status(HttpStatus.PRECONDITION_FAILED).build(); // 412
        }

        existing.setName(update.getName());
        existing.setCompleted(update.isCompleted());
        existing.incrementVersion();

        return ResponseEntity.ok().eTag("\"v" + existing.getVersion() + "\"").body(existing);
    }

    // Soft-delete via PATCH — sets deleted=true rather than removing from store
    @PatchMapping("/{id}/archive")
    public ResponseEntity<Task> archive(@PathVariable Long id) {
        Task task = tasks.get(id);
        if (task == null) return ResponseEntity.notFound().build();
        task.setDeleted(true);
        return ResponseEntity.ok(task);
    }

    static class Task {
        private long id; private String name; private boolean completed;
        private boolean deleted; private int version = 1;
        Task() {}
        // getters/setters elided for brevity
        public long getId() { return id; } public void setId(long i) { id=i; }
        public String getName() { return name; } public void setName(String n) { name=n; }
        public boolean isCompleted() { return completed; } public void setCompleted(boolean c) { completed=c; }
        public boolean isDeleted() { return deleted; } public void setDeleted(boolean d) { deleted=d; }
        public int getVersion() { return version; }
        public void incrementVersion() { version++; }
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run

# Create with idempotency key
curl -i -X POST -H "Content-Type: application/json" \
     -H "Idempotency-Key: req-abc-123" \
     -d '{"name":"Ship feature","completed":false}' http://localhost:8080/api/tasks
# 201 Created  ETag: "v1"

# Retry same request — idempotent: returns 200 with same body
curl -i -X POST -H "Content-Type: application/json" \
     -H "Idempotency-Key: req-abc-123" \
     -d '{"name":"Ship feature","completed":false}' http://localhost:8080/api/tasks
# 200 OK (not 201 — previously processed)

# Conditional PUT — succeeds when ETag matches
curl -i -X PUT -H "Content-Type: application/json" \
     -H "If-Match: \"v1\"" \
     -d '{"name":"Ship feature","completed":true}' http://localhost:8080/api/tasks/1
# 200 OK  ETag: "v2"

# Conditional PUT — fails when ETag stale (concurrent update)
curl -i -X PUT -H "Content-Type: application/json" \
     -H "If-Match: \"v1\"" \
     -d '{"name":"...","completed":true}' http://localhost:8080/api/tasks/1
# 412 Precondition Failed

# Soft delete
curl -X PATCH http://localhost:8080/api/tasks/1/archive
# {"id":1,"name":"Ship feature","completed":true,"deleted":true,"version":2}
```

**What changed and why:**
- Idempotency keys make `POST` safe to retry — a critical property for mobile clients on flaky networks.
- `If-Match` + `ETag` on `PUT` implements optimistic locking — two concurrent editors can't silently overwrite each other.
- `@PatchMapping("/{id}/archive")` is a named-operation PATCH — a clean pattern for soft operations that aren't full resource replacements.

<svg viewBox="0 0 700 200" xmlns="http://www.w3.org/2000/svg" font-family="monospace" font-size="11">
  <rect width="700" height="200" fill="#0d1117"/>
  <!-- etag flow -->
  <rect x="10" y="40" width="120" height="30" rx="4" fill="#1c2430" stroke="#79c0ff"/>
  <text x="70" y="59" text-anchor="middle" fill="#79c0ff">PUT + If-Match: v1</text>
  <line x1="130" y1="55" x2="165" y2="55" stroke="#8b949e" marker-end="url(#apw)"/>
  <rect x="165" y="40" width="150" height="30" rx="4" fill="#1c2430" stroke="#6db33f"/>
  <text x="240" y="59" text-anchor="middle" fill="#6db33f">If-Match == ETag?</text>
  <!-- yes -->
  <line x1="315" y1="55" x2="350" y2="55" stroke="#6db33f" marker-end="url(#apw)"/>
  <text x="332" y="50" text-anchor="middle" fill="#6db33f" font-size="10">yes</text>
  <rect x="350" y="40" width="130" height="30" rx="4" fill="#1c2430" stroke="#6db33f"/>
  <text x="415" y="59" text-anchor="middle" fill="#6db33f">update + new ETag</text>
  <!-- no -->
  <line x1="240" y1="70" x2="240" y2="110" stroke="#e74c3c" marker-end="url(#apw2)"/>
  <text x="250" y="95" text-anchor="middle" fill="#e74c3c" font-size="10">no</text>
  <rect x="165" y="110" width="150" height="30" rx="4" fill="#1c2430" stroke="#e74c3c"/>
  <text x="240" y="129" text-anchor="middle" fill="#e74c3c">412 Precondition Failed</text>
  <text x="350" y="170" text-anchor="middle" fill="#8b949e" font-size="10">Optimistic locking via ETag prevents concurrent overwrites without DB transactions</text>
  <defs>
    <marker id="apw" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L0,6 L8,3 z" fill="#6db33f"/></marker>
    <marker id="apw2" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L0,6 L8,3 z" fill="#e74c3c"/></marker>
  </defs>
</svg>

---

## 6. Walkthrough

**Startup:**

1. `@RestController` + class-level `@RequestMapping("/api/tasks")` registered.
2. Each composed annotation (`@GetMapping`, `@PostMapping`, etc.) is unwrapped to `@RequestMapping` with the specific method pinned.
3. Five `RequestMappingInfo` objects stored in the handler mapping registry.

**Per-request: `PUT /api/tasks/1` with `If-Match: "v1"`:**

4. `HandlerMapping` matches `@PutMapping("/{id}")` — method `PUT`, path `/api/tasks/1`. Wins over GET/POST/PATCH (different method).
5. `HandlerAdapter` resolves arguments:
   - `@PathVariable Long id` → `1L`
   - `@RequestBody Task update` → deserialized from JSON body
   - `@RequestHeader("If-Match") String ifMatch` → `"\"v1\""`
6. `conditionalReplace(1L, update, "\"v1\"")` executes.
7. Fetches `existing` (version=1). Computes `currentETag = "\"v1\""`. Matches `ifMatch` → continues.
8. Updates `existing.name`, `existing.completed`, increments version to 2.
9. Returns `ResponseEntity.ok().eTag("\"v2\"").body(existing)`.
10. Response: `200 OK  ETag: "v2"  Body: {updated task}`.

**Concurrent conflict path:**

After step 8 above, a second client sends `PUT /api/tasks/1` with `If-Match: "v1"`.  Step 7 computes `currentETag = "\"v2\""`. `"\"v1\""` ≠ `"\"v2\""` → returns `412 Precondition Failed`. No data is changed.

---

## 7. Gotchas & takeaways

> **`@PutMapping` is idempotent; `@PostMapping` is not.**  PUT to the same URL with the same body must always produce the same server state.  POST is not required to be idempotent — repeated calls may create duplicate resources.  Use idempotency keys on POST when clients may retry.

> **`@PatchMapping` has no built-in semantics for partial update.**  It just binds the PATCH body to whatever you declare.  You must implement the partial-update logic yourself (merge patch, JSON Patch, or a simple field-present check).

> **`produces = "application/json"` at class level applies to ALL methods in that controller.**  If one method needs to produce `text/plain`, override it at the method level with its own `produces` attribute.

- The five composed annotations cover 90% of REST API design — use them instead of `@RequestMapping` for clarity.
- `DELETE` should return `204 No Content` on success and `404 Not Found` if the resource doesn't exist.
- `PUT` replaces the full resource; `PATCH` applies a partial update — use `consumes = "application/merge-patch+json"` to advertise RFC 7396 semantics.
- ETags + `If-Match` implement optimistic locking without database-level locking.
