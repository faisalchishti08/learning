---
card: spring-framework
gi: 63
slug: request-scope
title: request scope
---

## 1. What it is

**Request scope** (`scope="request"`) creates a new bean instance for each HTTP request and destroys it when that request completes. The bean lives from `DispatcherServlet` entry to response write — any injection point that asks for the bean during that request gets the same instance. Between requests, different instances exist independently.

```java
@Component
@Scope(value = WebApplicationContext.SCOPE_REQUEST,
       proxyMode = ScopedProxyMode.TARGET_CLASS)  // ← required when injected into singleton
public class RequestContext {
    private String userId;
    private String traceId = UUID.randomUUID().toString();
    // Populated once per request, safe to hold mutable per-request state
}
```

Or with the `@RequestScope` shortcut (Spring 4.3+):

```java
@Component
@RequestScope   // equivalent to @Scope("request") + scoped proxy
public class RequestContext { ... }
```

In one sentence: **A request-scoped bean is instantiated when an HTTP request arrives, shared by all components that participate in that request, and destroyed when the response is sent — giving you a safe per-request state container.**

## 2. Why & when

Use request scope for:

- **Audit / trace context** — `requestId`, `correlationId`, `userId` that must be carried through all layers of a single request without being passed as method parameters.
- **Security context** (when not using `ThreadLocal`) — current user identity, roles, JWT claims.
- **Per-request caches** — avoid hitting the DB twice for the same entity within one request.
- **Request-specific configuration** — locale, timezone, A/B test bucket resolved from the incoming request.

Do not use request scope outside a web context — it only works within a request-response thread that has an active `RequestAttributes` bound to it. Background threads do not have a request scope.

## 3. Core concept

```
HTTP Request lifecycle with request-scoped bean:

  1. HTTP request arrives → DispatcherServlet processes it.
  2. Spring creates a fresh RequestContext bean (or sub-type) for this request.
  3. All beans in the call chain that @Autowired RequestContext get the SAME instance
     (the one for THIS request — not another concurrent request's instance).
  4. Request completes → response written → RequestContext.destroy() called.
     (Next request gets a brand new RequestContext.)

Thread model:
  Thread-1 (Request A): RequestContext@0x1 — userId="alice"
  Thread-2 (Request B): RequestContext@0x2 — userId="bob"
  Both threads exist concurrently; no data leaks between them.

Scoped proxy:
  Singleton that @Autowired a request-scoped bean holds a proxy.
  Every method call on the proxy is delegated to the CURRENT request's real instance.
  Without proxy → singleton holds the first request's instance forever.
```

## 4. Diagram

<svg viewBox="0 0 680 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Request scope: each HTTP request gets its own bean instance, concurrent requests are isolated">
  <defs>
    <marker id="a63" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="b63" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>
  <rect x="5" y="5" width="670" height="210" rx="8" fill="#0d1117" stroke="#8b949e" stroke-width="1.2"/>
  <text x="338" y="22" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Request scope — one instance per HTTP request, concurrent requests isolated</text>

  <!-- Request A -->
  <rect x="15" y="32" width="310" height="165" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="170" y="50" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">HTTP Request A  (Thread-1, user=alice)</text>

  <rect x="25" y="58" width="290" height="35" rx="3" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="170" y="76" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">RequestContext#A — userId="alice" traceId="AAA"</text>

  <text x="170" y="108" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">Controller → Service → Repository</text>
  <text x="170" y="122" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">all see same RequestContext#A</text>

  <rect x="25" y="135" width="290" height="50" rx="3" fill="#0d1117" stroke="#8b949e" stroke-width="0.8"/>
  <text x="170" y="152" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">Controller: ctx.getUserId() → "alice"</text>
  <text x="170" y="165" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">Service:    ctx.getTraceId() → "AAA"</text>
  <text x="170" y="178" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">→ response sent → RequestContext#A destroyed</text>

  <!-- Request B -->
  <rect x="345" y="32" width="318" height="165" rx="5" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="504" y="50" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">HTTP Request B  (Thread-2, user=bob)</text>

  <rect x="355" y="58" width="298" height="35" rx="3" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="504" y="76" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">RequestContext#B — userId="bob" traceId="BBB"</text>

  <text x="504" y="108" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">Controller → Service → Repository</text>
  <text x="504" y="122" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">all see same RequestContext#B</text>

  <rect x="355" y="135" width="298" height="50" rx="3" fill="#0d1117" stroke="#8b949e" stroke-width="0.8"/>
  <text x="504" y="152" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">Controller: ctx.getUserId() → "bob"</text>
  <text x="504" y="165" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">Service:    ctx.getTraceId() → "BBB"</text>
  <text x="504" y="178" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">→ response sent → RequestContext#B destroyed</text>

  <text x="338" y="208" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">Two concurrent requests: completely isolated instances. "alice" never sees "bob"'s data.</text>
</svg>

Two concurrent requests get two separate `RequestContext` instances. Components within each request share their respective instance; instances are never shared across requests.

## 5. Runnable example

Scenario: a `RequestTracer` bean that holds the current HTTP request's trace ID, user ID, and per-request cache. A `ProductService` and `AuditService` both use it — all within the same simulated HTTP request lifecycle.

### Level 1 — Basic

Simulate request scope: one instance per "request", shared across all call-chain participants.

```java
// RequestScopeDemo.java — run with: java RequestScopeDemo.java
import java.util.*;

public class RequestScopeDemo {

    // ── request-scoped bean ───────────────────────────────────────────
    static class RequestTracer {
        private static int count = 0;
        final int    id;
        final String traceId;
        final String userId;

        RequestTracer(String userId) {
            this.id      = ++count;
            this.userId  = userId;
            this.traceId = "TRACE-" + id + "-" + Long.toHexString(System.nanoTime() % 0xFFFF);
            System.out.println("  [REQUEST BEAN CREATED #" + id + "] userId=" + userId
                + " traceId=" + traceId);
        }

        void destroy() {
            System.out.println("  [REQUEST BEAN DESTROYED #" + id + "] traceId=" + traceId);
        }
    }

    // ── stateless singleton service — uses request-scoped bean ─────────
    static class ProductService {
        String findProduct(String sku, RequestTracer tracer) {
            System.out.println("  [PRODUCT] sku=" + sku + " traceId=" + tracer.traceId
                + " user=" + tracer.userId);
            return "Product[" + sku + "]";
        }
    }

    static class AuditService {
        void log(String action, RequestTracer tracer) {
            System.out.println("  [AUDIT] action=" + action + " traceId=" + tracer.traceId
                + " user=" + tracer.userId);
        }
    }

    // ── simulated request lifecycle ────────────────────────────────────
    static void handleRequest(String userId, String sku) {
        System.out.println("[REQUEST BEGIN] GET /products/" + sku + " user=" + userId);
        RequestTracer tracer = new RequestTracer(userId);  // created PER REQUEST
        try {
            ProductService products = new ProductService();
            AuditService   audit    = new AuditService();

            String product = products.findProduct(sku, tracer);
            audit.log("VIEW_PRODUCT sku=" + sku, tracer);
            System.out.println("  [RESPONSE] 200 OK body=" + product);
        } finally {
            tracer.destroy();  // @PreDestroy equivalent — called on request end
        }
        System.out.println("[REQUEST END]");
    }

    public static void main(String[] args) {
        System.out.println("=== Sequential requests ===");
        handleRequest("alice", "SKU-001");
        System.out.println();
        handleRequest("bob",   "SKU-002");
        System.out.println();
        handleRequest("alice", "SKU-003");
        System.out.println();
        System.out.println("[INSTANCES CREATED] " + RequestTracer.count);
        System.out.println("[NOTE] Each request got its own RequestTracer — none shared.");
    }
}
```

How to run: `java RequestScopeDemo.java`

Three requests → three `RequestTracer` instances. Each is created at request start and destroyed at request end. Within one request, `ProductService` and `AuditService` both see the same `tracer` (same `traceId`). Different requests have different `traceId` values — complete isolation.

### Level 2 — Intermediate

Per-request cache: a `UserCacheService` that fetches the user from DB at most once per request, even if multiple components ask for the same user.

```java
// RequestScopeDemo2.java — run with: java RequestScopeDemo2.java
import java.util.*;

public class RequestScopeDemo2 {

    // ── simulated DB ──────────────────────────────────────────────────
    static class UserDatabase {
        private int queryCount = 0;
        Map<String, String> findById(String userId) {
            queryCount++;
            System.out.println("  [DB QUERY #" + queryCount + "] SELECT * FROM users WHERE id='" + userId + "'");
            return Map.of("id", userId, "name", "User " + userId, "role", "USER");
        }
        int getQueryCount() { return queryCount; }
    }

    // ── request-scoped per-request cache ──────────────────────────────
    static class RequestUserCache {
        private static int count = 0;
        final int id;
        private final Map<String, Map<String, String>> cache = new HashMap<>();
        private final UserDatabase db;

        RequestUserCache(UserDatabase db) {
            this.db = db;
            this.id = ++count;
            System.out.println("  [REQUEST CACHE CREATED #" + id + "]");
        }

        Map<String, String> getUser(String userId) {
            if (cache.containsKey(userId)) {
                System.out.println("  [CACHE HIT] userId=" + userId + " (no DB call)");
                return cache.get(userId);
            }
            Map<String, String> user = db.findById(userId);
            cache.put(userId, user);
            System.out.println("  [CACHE MISS] userId=" + userId + " → fetched from DB");
            return user;
        }

        void destroy() {
            System.out.println("  [REQUEST CACHE DESTROYED #" + id + "] cached="
                + cache.size() + " entries");
        }
    }

    // ── stateless singleton services that both need the current user ───
    static class AuthorizationService {
        boolean canAccess(String resource, RequestUserCache userCache, String userId) {
            Map<String,String> user = userCache.getUser(userId);  // may hit cache
            System.out.println("  [AUTHZ] user=" + user.get("name") + " role=" + user.get("role")
                + " resource=" + resource);
            return "USER".equals(user.get("role"));
        }
    }

    static class AuditService {
        void log(String action, RequestUserCache userCache, String userId) {
            Map<String,String> user = userCache.getUser(userId);  // always from cache (2nd call)
            System.out.println("  [AUDIT] action=" + action + " by=" + user.get("name")
                + " tracing via request cache#" + userCache.id);
        }
    }

    // ── request handler ────────────────────────────────────────────────
    static void handleRequest(UserDatabase db, String userId, String resource, String action) {
        System.out.println("[REQUEST] user=" + userId + " resource=" + resource);
        RequestUserCache cache = new RequestUserCache(db);   // fresh per request
        try {
            AuthorizationService authz = new AuthorizationService();
            AuditService         audit = new AuditService();

            boolean allowed = authz.canAccess(resource, cache, userId);
            if (allowed) {
                System.out.println("  [ACCESS] granted → processing " + action);
                audit.log(action, cache, userId);  // user fetched from cache, not DB
            } else {
                System.out.println("  [ACCESS] denied");
            }
        } finally {
            cache.destroy();
        }
        System.out.println("[REQUEST END] total DB queries this request: "
            + db.getQueryCount() + "\n");
    }

    public static void main(String[] args) {
        UserDatabase db = new UserDatabase();

        System.out.println("=== Request 1: user u001 accesses /orders ===");
        handleRequest(db, "u001", "/orders", "VIEW_ORDERS");

        System.out.println("=== Request 2: user u002 accesses /reports ===");
        handleRequest(db, "u002", "/reports", "VIEW_REPORTS");

        System.out.println("=== Request 3: user u001 again (new request, new cache) ===");
        handleRequest(db, "u001", "/orders", "VIEW_ORDERS");

        System.out.println("[TOTAL DB QUERIES] " + db.getQueryCount()
            + " (2 per request due to cache miss on first call, 0 on second within same request)");
    }
}
```

How to run: `java RequestScopeDemo2.java`

Within Request 1, `authz.canAccess()` fetches `u001` from DB (cache miss). `audit.log()` calls `cache.getUser("u001")` again — cache hit, no second DB call. Request 2 gets a fresh `RequestUserCache` — `u002` is a miss again. Request 3: new request, new cache, `u001` is a miss again (cache from Request 1 was destroyed). Total: 3 DB queries across 3 requests, not 6.

### Level 3 — Advanced

Concurrent requests, request isolation proof, and the scoped-proxy pattern for injecting a request-scoped bean into a singleton.

```java
// RequestScopeDemo3.java — run with: java RequestScopeDemo3.java
import java.util.*;
import java.util.concurrent.*;
import java.util.concurrent.atomic.*;

public class RequestScopeDemo3 {

    // ── per-request context (request-scoped bean) ─────────────────────
    static class RequestContext {
        private static final AtomicInteger seq = new AtomicInteger();
        final int    id;
        final String requestId;
        final String userId;
        final long   startNs;
        final List<String> auditTrail = new CopyOnWriteArrayList<>();

        RequestContext(String userId) {
            this.id        = seq.incrementAndGet();
            this.requestId = "req-" + id;
            this.userId    = userId;
            this.startNs   = System.nanoTime();
        }

        void addAudit(String entry) { auditTrail.add(entry); }

        String summary() {
            long ms = (System.nanoTime() - startNs) / 1_000_000;
            return "[" + requestId + "] user=" + userId
                + " durationMs=" + ms + " audits=" + auditTrail;
        }

        void destroy() {
            System.out.println("  [DESTROY] " + summary());
        }
    }

    // ── scoped-proxy simulation: singleton holds a ThreadLocal "proxy" ─
    static class RequestContextHolder {
        private static final ThreadLocal<RequestContext> CURRENT = new ThreadLocal<>();
        static void set(RequestContext ctx) { CURRENT.set(ctx); }
        static RequestContext get()         { return CURRENT.get(); }
        static void clear()                  { CURRENT.remove(); }
    }

    // ── singleton services — access current request's context via proxy ─
    static class ProductService {
        void findProduct(String sku) {
            RequestContext ctx = RequestContextHolder.get();
            ctx.addAudit("ProductService.findProduct sku=" + sku);
            System.out.println("  [PRODUCT] sku=" + sku + " requestId=" + ctx.requestId
                + " user=" + ctx.userId);
        }
    }

    static class OrderService {
        void placeOrder(String sku, int qty) {
            RequestContext ctx = RequestContextHolder.get();
            ctx.addAudit("OrderService.placeOrder sku=" + sku + " qty=" + qty);
            System.out.println("  [ORDER] sku=" + sku + " qty=" + qty
                + " requestId=" + ctx.requestId + " user=" + ctx.userId);
        }
    }

    // ── request dispatcher: creates context per request ────────────────
    static class DispatcherServlet {
        private final ProductService products = new ProductService();  // singleton
        private final OrderService   orders   = new OrderService();    // singleton

        String dispatch(String method, String path, String userId) {
            RequestContext ctx = new RequestContext(userId);
            RequestContextHolder.set(ctx);   // bind to current thread
            try {
                System.out.println("[" + ctx.requestId + "] " + method + " " + path
                    + " user=" + userId);
                if (path.startsWith("/products/")) {
                    String sku = path.substring("/products/".length());
                    products.findProduct(sku);
                    return "200 OK product=" + sku;
                } else if (path.startsWith("/orders")) {
                    String[] parts = path.split("\\?")[1].split("&");
                    String sku = parts[0].split("=")[1];
                    int    qty = Integer.parseInt(parts[1].split("=")[1]);
                    products.findProduct(sku);   // check product first
                    orders.placeOrder(sku, qty);
                    return "201 Created";
                }
                return "404 Not Found";
            } finally {
                ctx.destroy();
                RequestContextHolder.clear();  // unbind — prevents memory leaks
            }
        }
    }

    public static void main(String[] args) throws Exception {
        DispatcherServlet servlet = new DispatcherServlet();

        System.out.println("=== Sequential requests ===");
        servlet.dispatch("GET",  "/products/SKU-001", "alice");
        System.out.println();
        servlet.dispatch("POST", "/orders?sku=SKU-002&qty=3", "bob");
        System.out.println();

        System.out.println("=== Concurrent requests (5 threads) ===");
        ExecutorService pool = Executors.newFixedThreadPool(5);
        List<Future<String>> futures = new ArrayList<>();
        String[] users = {"alice", "bob", "carol", "dave", "eve"};

        for (int i = 0; i < 5; i++) {
            final String user = users[i];
            final int    num  = i;
            futures.add(pool.submit(() ->
                servlet.dispatch("GET", "/products/SKU-00" + (num+1), user)));
        }

        for (Future<String> f : futures) System.out.println("[RESPONSE] " + f.get());
        pool.shutdown();
        pool.awaitTermination(5, TimeUnit.SECONDS);

        System.out.println("\n[TOTAL CONTEXTS] " + RequestContext.seq.get());
        System.out.println("[KEY] Each request: own context, isolated audit trail, no data leaks.");
    }
}
```

How to run: `java RequestScopeDemo3.java`

`ThreadLocal<RequestContext>` simulates Spring's `RequestContextHolder` — in real Spring, this is exactly how request-scoped beans work under the hood. Five concurrent threads each get their own `RequestContext`. `ProductService` and `OrderService` are singletons; they access the per-thread context via `RequestContextHolder.get()` (the equivalent of a scoped proxy). The `finally` block calls `ctx.destroy()` and `RequestContextHolder.clear()` — preventing ThreadLocal memory leaks, exactly what `RequestContextListener` does in a real app.

## 6. Walkthrough

**`dispatch("POST", "/orders?sku=SKU-002&qty=3", "bob")` — step by step:**

```
Request lifecycle:
  1. new RequestContext("bob")
       id=2, requestId="req-2", userId="bob", startNs=now
  2. RequestContextHolder.set(ctx)
       ThreadLocal for current thread = RequestContext#2

  3. path = "/orders?sku=SKU-002&qty=3" → POST handler
     a. products.findProduct("SKU-002"):
          ctx = RequestContextHolder.get() → RequestContext#2 (current thread's)
          ctx.addAudit("ProductService.findProduct sku=SKU-002")
          auditTrail: ["ProductService.findProduct sku=SKU-002"]
          prints: [PRODUCT] sku=SKU-002 requestId=req-2 user=bob

     b. orders.placeOrder("SKU-002", 3):
          ctx = RequestContextHolder.get() → SAME RequestContext#2
          ctx.addAudit("OrderService.placeOrder sku=SKU-002 qty=3")
          auditTrail: ["ProductService.findProduct...", "OrderService.placeOrder..."]
          prints: [ORDER] sku=SKU-002 qty=3 requestId=req-2 user=bob

  4. return "201 Created"

  5. finally:
     ctx.destroy():
       prints: [DESTROY] [req-2] user=bob durationMs=X audits=[...]
     RequestContextHolder.clear()  → ThreadLocal removed
```

**Concurrent isolation proof:**

```
Thread-1 (alice): RequestContextHolder.get() → RequestContext{userId="alice"}
Thread-2 (bob):   RequestContextHolder.get() → RequestContext{userId="bob"}
Thread-3 (carol): RequestContextHolder.get() → RequestContext{userId="carol"}

All five threads run simultaneously — each reads its OWN ThreadLocal value.
No data from alice's context leaks into bob's context.
```

## 7. Gotchas & takeaways

> **Request scope only works inside an active HTTP request.** Calling a request-scoped bean from a `@Scheduled` method, a background thread, or a unit test without a mocked `RequestAttributes` throws `IllegalStateException: No thread-bound request found`. Use `RequestContextHolder.setRequestAttributes()` in tests, or restructure to avoid the dependency.

> **`@RequestScope` without `proxyMode` breaks when the bean is injected into a singleton.** The singleton is created once at startup when no request is active — Spring cannot create the request-scoped bean yet, causing `BeanCreationException`. Always use `proxyMode = ScopedProxyMode.TARGET_CLASS` (or `@RequestScope` which sets it automatically) when a singleton holds a request-scoped reference.

- Spring Boot web apps auto-configure `RequestContextListener` and `RequestContextFilter`, which bind the request to the current thread — this is what makes `RequestContextHolder.currentRequestAttributes()` work inside request-scoped beans.
- In virtual-thread (Project Loom) environments, a "virtual thread per request" model makes `ThreadLocal` semantics equivalent — each request's thread has its own locals.
- Analogous scopes: `session` scope (one bean per HTTP session, destroyed at session timeout), `application` scope (one bean per `ServletContext`, effectively singleton for the app).
- Never store a request-scoped bean reference beyond the current request — the container clears it and the next request's bean will be a different instance.
