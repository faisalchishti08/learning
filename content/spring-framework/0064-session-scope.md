---
card: spring-framework
gi: 64
slug: session-scope
title: session scope
---

## 1. What it is

**Session scope** creates one bean instance per HTTP session. The same instance is reused across multiple requests from the same client (same browser/session cookie) and destroyed when the session expires or is invalidated. It lives longer than a request-scoped bean but shorter than an application-scoped bean.

```java
@Component
@Scope(value = WebApplicationContext.SCOPE_SESSION,
       proxyMode = ScopedProxyMode.TARGET_CLASS)
public class UserPreferences {
    private String language = "en";
    private String theme    = "light";
    // Per-session: same user across multiple page loads sees the same preferences
}

// Shortcut (Spring 4.3+):
@Component
@SessionScope
public class ShoppingBasket {
    private final List<Item> items = new ArrayList<>();
}
```

In one sentence: **A session-scoped bean is created once per HTTP session and reused for every request within that session, making it ideal for user state that must persist across multiple requests (shopping basket, user preferences, login context).**

## 2. Why & when

Use session scope for:

- **Shopping basket** — items added across multiple page views must persist until checkout.
- **User preferences** — language, theme, timezone selected in a settings page.
- **Multi-step wizard state** — a user works through a checkout form across several pages.
- **Cached user profile** — load once at login, available through the session.

Do NOT use for:

- Data shared across users — session beans are per-user by definition.
- Short-lived per-request data — use request scope.
- Application-wide configuration — use application scope or singletons.

Session scope requires an active `HttpSession` — it fails in batch jobs, CLI tools, or test contexts without a mock session.

## 3. Core concept

```
HttpSession lifecycle:
  Session created: first request from a new browser (JSESSIONID cookie set).
  Session destroyed: timeout (e.g. 30 min idle) or session.invalidate().

Session-scoped bean lifecycle:
  Created: when first accessed within a session.
  Reused: for every subsequent request in the SAME session.
  Destroyed: when the session is destroyed → @PreDestroy called.

Concurrent requests within one session:
  Multiple browser tabs can send requests on the same session simultaneously.
  Session-scoped beans are NOT automatically thread-safe — use synchronization
  or design for single-threaded access within a session.

Injecting into a singleton:
  → requires proxyMode = ScopedProxyMode.TARGET_CLASS
  The singleton holds a scoped proxy; each method call routes to the correct
  session's real instance via RequestContextHolder.
```

## 4. Diagram

<svg viewBox="0 0 660 215" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Session scope: one bean per HTTP session, persists across multiple requests">
  <defs>
    <marker id="a64" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="b64" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>
  <rect x="5" y="5" width="650" height="202" rx="8" fill="#0d1117" stroke="#8b949e" stroke-width="1.2"/>
  <text x="330" y="22" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Session scope — one instance per HTTP session</text>

  <!-- Session A (Alice) -->
  <rect x="15" y="32" width="295" height="160" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="162" y="50" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">Session A  (Alice — JSESSIONID=AAA)</text>

  <rect x="25" y="58" width="275" height="30" rx="3" fill="#0d1117" stroke="#6db33f" stroke-width="1"/>
  <text x="162" y="77" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">ShoppingBasket#A — items=[Laptop]</text>

  <text x="162" y="104" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">Request 1: GET /cart → basket.getItems()</text>
  <text x="162" y="118" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">Request 2: POST /add → basket.add(Mouse)</text>
  <text x="162" y="132" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">Request 3: GET /cart → [Laptop, Mouse]</text>
  <text x="162" y="148" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">Request 4: POST /checkout → basket.clear()</text>
  <text x="162" y="168" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">Session timeout → ShoppingBasket#A destroyed</text>

  <!-- Session B (Bob) -->
  <rect x="340" y="32" width="305" height="160" rx="5" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="492" y="50" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">Session B  (Bob — JSESSIONID=BBB)</text>

  <rect x="350" y="58" width="285" height="30" rx="3" fill="#0d1117" stroke="#79c0ff" stroke-width="1"/>
  <text x="492" y="77" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">ShoppingBasket#B — items=[]</text>

  <text x="492" y="104" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">Request 1: GET /cart → [] (empty)</text>
  <text x="492" y="118" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">Request 2: POST /add → basket.add(Keyboard)</text>
  <text x="492" y="132" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">Bob's basket has [Keyboard], not [Laptop]</text>
  <text x="492" y="168" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">Independent — Alice's items never visible here</text>

  <text x="330" y="202" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">Basket#A and Basket#B are separate objects. Requests within each session reuse their basket.</text>
</svg>

Alice and Bob each have their own `ShoppingBasket` instance. Alice's basket state persists across her requests; Bob's basket is entirely independent.

## 5. Runnable example

Scenario: a `ShoppingBasket` that persists across multiple requests within the same session and is discarded when the session ends.

### Level 1 — Basic

One session → one basket instance reused across requests.

```java
// SessionScopeDemo.java — run with: java SessionScopeDemo.java
import java.util.*;

public class SessionScopeDemo {

    // ── session-scoped bean ───────────────────────────────────────────
    static class ShoppingBasket {
        private static int count = 0;
        final int id;
        final String sessionId;
        private final List<String> items = new ArrayList<>();
        private double total = 0.0;

        ShoppingBasket(String sessionId) {
            id = ++count;
            this.sessionId = sessionId;
            System.out.println("  [SESSION BEAN CREATED #" + id + "] session=" + sessionId);
        }

        void add(String item, double price) {
            items.add(item);
            total += price;
            System.out.println("  [ADD] " + item + " $" + price
                + " → total=$" + String.format("%.2f", total));
        }

        void remove(String item) {
            items.remove(item);
            System.out.println("  [REMOVE] " + item);
        }

        List<String> getItems() { return Collections.unmodifiableList(items); }
        double getTotal()       { return total; }
        int getId()             { return id; }

        void destroy() {
            System.out.println("  [SESSION BEAN DESTROYED #" + id + "] session=" + sessionId);
        }
    }

    // ── session registry: maps sessionId → basket (simulates HttpSession) ─
    static class SessionRegistry {
        private final Map<String, ShoppingBasket> sessions = new LinkedHashMap<>();

        ShoppingBasket getBasket(String sessionId) {
            return sessions.computeIfAbsent(sessionId, id -> new ShoppingBasket(id));
        }

        void invalidate(String sessionId) {
            ShoppingBasket basket = sessions.remove(sessionId);
            if (basket != null) basket.destroy();
        }
    }

    // ── simulated requests ─────────────────────────────────────────────
    static void request(SessionRegistry registry, String session, String action, Object... args) {
        ShoppingBasket basket = registry.getBasket(session);
        System.out.println("[REQUEST] session=" + session + " basket#=" + basket.getId()
            + " action=" + action);
        switch (action) {
            case "add"    -> basket.add((String) args[0], (double) args[1]);
            case "remove" -> basket.remove((String) args[0]);
            case "view"   -> System.out.println("  [VIEW] items=" + basket.getItems()
                + " total=$" + String.format("%.2f", basket.getTotal()));
        }
    }

    public static void main(String[] args) {
        SessionRegistry registry = new SessionRegistry();

        System.out.println("=== Alice's session ===");
        request(registry, "sess-alice", "add", "Laptop Pro", 1299.99);
        request(registry, "sess-alice", "add", "USB-C Hub",    49.99);
        request(registry, "sess-alice", "view");
        request(registry, "sess-alice", "remove", "USB-C Hub");
        request(registry, "sess-alice", "view");

        System.out.println("\n=== Bob's session (separate basket) ===");
        request(registry, "sess-bob", "add", "Wireless Mouse", 39.99);
        request(registry, "sess-bob", "view");

        System.out.println("\n=== Back to Alice — basket persisted ===");
        request(registry, "sess-alice", "add", "Monitor", 399.99);
        request(registry, "sess-alice", "view");

        System.out.println("\n=== Session timeout / logout ===");
        registry.invalidate("sess-alice");
        registry.invalidate("sess-bob");
        System.out.println("Total baskets ever created: " + ShoppingBasket.count);
    }
}
```

How to run: `java SessionScopeDemo.java`

Two sessions → two `ShoppingBasket` instances. Each time `sess-alice` makes a request, the same `basket#1` is returned — items accumulate across requests. When `registry.invalidate("sess-alice")` is called (equivalent to `session.invalidate()` or timeout), `destroy()` is called and the basket is removed.

### Level 2 — Intermediate

Multi-step wizard: a session-scoped bean collects form data across three separate page requests before final submission.

```java
// SessionScopeDemo2.java — run with: java SessionScopeDemo2.java
import java.util.*;

public class SessionScopeDemo2 {

    // ── session-scoped wizard state ────────────────────────────────────
    static class CheckoutWizard {
        private static int count = 0;
        final int id;

        // Step data accumulated across requests
        String name, email;
        String address, city, postalCode;
        String cardLast4;
        String promoCode;

        CheckoutWizard(String sessionId) {
            id = ++count;
            System.out.println("  [WIZARD CREATED #" + id + "] session=" + sessionId);
        }

        // Step 1: shipping info
        void setShipping(String name, String email, String address, String city, String postalCode) {
            this.name = name; this.email = email;
            this.address = address; this.city = city; this.postalCode = postalCode;
            System.out.println("  [STEP 1] shipping set: " + name + " → " + address + ", " + city);
        }

        // Step 2: payment
        void setPayment(String cardLast4) {
            this.cardLast4 = cardLast4;
            System.out.println("  [STEP 2] payment set: card ending " + cardLast4);
        }

        // Step 3: optional promo
        void setPromo(String code) {
            this.promoCode = code;
            System.out.println("  [STEP 3] promo set: " + code);
        }

        boolean isComplete() {
            return name != null && email != null && address != null && cardLast4 != null;
        }

        Map<String, String> toOrderPayload() {
            Map<String, String> m = new LinkedHashMap<>();
            m.put("customer", name);
            m.put("email",    email);
            m.put("address",  address + ", " + city + " " + postalCode);
            m.put("card",     "****" + cardLast4);
            if (promoCode != null) m.put("promo", promoCode);
            return m;
        }

        void destroy() {
            System.out.println("  [WIZARD DESTROYED #" + id + "]");
        }
    }

    static class SessionRegistry {
        private final Map<String, CheckoutWizard> sessions = new HashMap<>();
        CheckoutWizard getWizard(String sessionId) {
            return sessions.computeIfAbsent(sessionId, id -> new CheckoutWizard(id));
        }
        void invalidate(String sessionId) {
            CheckoutWizard w = sessions.remove(sessionId);
            if (w != null) w.destroy();
        }
    }

    static void request(SessionRegistry r, String sess, String page, String... params) {
        CheckoutWizard w = r.getWizard(sess);
        System.out.println("[REQUEST] " + page + " session=" + sess + " wizard#=" + w.id);
        switch (page) {
            case "POST /checkout/shipping" ->
                w.setShipping(params[0], params[1], params[2], params[3], params[4]);
            case "POST /checkout/payment" ->
                w.setPayment(params[0]);
            case "POST /checkout/promo" ->
                w.setPromo(params[0]);
            case "POST /checkout/confirm" -> {
                if (!w.isComplete()) {
                    System.out.println("  [400 BAD REQUEST] wizard incomplete");
                } else {
                    System.out.println("  [201 CREATED] Order placed! payload=" + w.toOrderPayload());
                    r.invalidate(sess);  // session ends after order
                }
            }
        }
    }

    public static void main(String[] args) {
        SessionRegistry registry = new SessionRegistry();

        System.out.println("=== Alice — completes checkout across 4 requests ===");
        request(registry, "sess-alice", "POST /checkout/shipping",
            "Alice Smith", "alice@example.com", "123 Main St", "Springfield", "12345");
        request(registry, "sess-alice", "POST /checkout/payment", "4242");
        request(registry, "sess-alice", "POST /checkout/promo",   "SAVE10");
        request(registry, "sess-alice", "POST /checkout/confirm");

        System.out.println("\n=== Bob — tries to confirm without completing steps ===");
        request(registry, "sess-bob", "POST /checkout/confirm");  // missing steps
        request(registry, "sess-bob", "POST /checkout/shipping",
            "Bob Jones", "bob@example.com", "456 Oak Ave", "Portland", "97201");
        request(registry, "sess-bob", "POST /checkout/payment", "1234");
        request(registry, "sess-bob", "POST /checkout/confirm");
    }
}
```

How to run: `java SessionScopeDemo2.java`

Alice's checkout spans 4 separate HTTP requests. The `CheckoutWizard` session bean accumulates each step's data and `toOrderPayload()` assembles the complete order at confirmation. Bob's attempt to confirm early fails because his wizard is incomplete — the state check (`isComplete()`) uses the same session bean that has been accumulating (or not) across his requests.

### Level 3 — Advanced

Concurrent requests on the same session (two browser tabs), session bean thread-safety concern, and session-invalidation cleanup.

```java
// SessionScopeDemo3.java — run with: java SessionScopeDemo3.java
import java.util.*;
import java.util.concurrent.*;
import java.util.concurrent.atomic.*;

public class SessionScopeDemo3 {

    // ── session-scoped bean: thread-safe for concurrent tab access ─────
    static class UserSession {
        private static final AtomicInteger seq = new AtomicInteger();
        final int    id;
        final String sessionId;

        private final String  userId;
        private final long    loginTimeMs;
        // ConcurrentHashMap: thread-safe for concurrent tab access
        private final ConcurrentHashMap<String, Object> attributes = new ConcurrentHashMap<>();
        private final List<String>                       pageHistory = new CopyOnWriteArrayList<>();
        private final AtomicInteger                      requestCount = new AtomicInteger();

        UserSession(String sessionId, String userId) {
            this.id          = seq.incrementAndGet();
            this.sessionId   = sessionId;
            this.userId      = userId;
            this.loginTimeMs = System.currentTimeMillis();
            System.out.printf("  [SESSION CREATED #%d] userId=%s session=%s%n", id, userId, sessionId);
        }

        void recordPageView(String path) {
            int n = requestCount.incrementAndGet();
            pageHistory.add(path);
            System.out.printf("  [PAGE VIEW #%d] %s userId=%s session=%d%n",
                n, path, userId, id);
        }

        void setAttribute(String key, Object value) { attributes.put(key, value); }
        Object getAttribute(String key) { return attributes.get(key); }

        void destroy() {
            long durationSec = (System.currentTimeMillis() - loginTimeMs) / 1000;
            System.out.printf("  [SESSION DESTROYED #%d] userId=%s requests=%d duration=%ds pages=%s%n",
                id, userId, requestCount.get(), durationSec, pageHistory);
        }
    }

    static class SessionRegistry {
        private final ConcurrentHashMap<String, UserSession> sessions = new ConcurrentHashMap<>();

        UserSession getOrCreate(String sessionId, String userId) {
            return sessions.computeIfAbsent(sessionId, id -> new UserSession(id, userId));
        }
        UserSession get(String sessionId) { return sessions.get(sessionId); }
        void invalidate(String sessionId) {
            UserSession s = sessions.remove(sessionId);
            if (s != null) s.destroy();
        }
    }

    public static void main(String[] args) throws Exception {
        SessionRegistry registry = new SessionRegistry();

        // Login (creates session)
        System.out.println("=== Login ===");
        registry.getOrCreate("sess-alice", "alice");
        registry.getOrCreate("sess-bob",   "bob");

        // Simulate two browser tabs for Alice (concurrent requests on same session)
        System.out.println("\n=== Concurrent requests: Alice opens 2 tabs ===");
        ExecutorService pool = Executors.newFixedThreadPool(4);
        List<Future<?>> futures = new ArrayList<>();

        String[] alicePages = {"/dashboard", "/orders", "/profile", "/settings", "/cart"};
        String[] bobPages   = {"/dashboard", "/products"};

        // Alice: 5 concurrent page loads (tabs)
        for (String page : alicePages) {
            futures.add(pool.submit(() -> {
                UserSession sess = registry.get("sess-alice");
                sess.recordPageView(page);
                // Simulate setting a session attribute (thread-safe ConcurrentHashMap)
                sess.setAttribute("lastVisited", page);
            }));
        }

        // Bob: 2 concurrent page loads
        for (String page : bobPages) {
            futures.add(pool.submit(() -> {
                UserSession sess = registry.get("sess-bob");
                sess.recordPageView(page);
            }));
        }

        for (Future<?> f : futures) f.get();
        pool.shutdown();

        // Sequential requests after concurrent ones
        System.out.println("\n=== Sequential requests ===");
        registry.get("sess-alice").recordPageView("/checkout");
        registry.get("sess-bob").recordPageView("/cart");

        System.out.println("\n=== Session summary ===");
        UserSession alice = registry.get("sess-alice");
        System.out.println("  Alice lastVisited=" + alice.getAttribute("lastVisited")
            + " totalPages=" + alice.requestCount);
        System.out.println("  Bob   totalPages=" + registry.get("sess-bob").requestCount);

        System.out.println("\n=== Logout / session invalidation ===");
        registry.invalidate("sess-alice");
        registry.invalidate("sess-bob");
        System.out.println("Sessions destroyed: " + UserSession.seq.get());
    }
}
```

How to run: `java SessionScopeDemo3.java`

Alice opens 5 concurrent requests (multiple browser tabs all on the same `JSESSIONID`). The session bean's `ConcurrentHashMap` and `CopyOnWriteArrayList` make concurrent access thread-safe. When sessions are invalidated, `destroy()` prints a full summary (total requests, duration, page history). Bob's session is entirely separate.

## 6. Walkthrough

**Session lifecycle — Alice's flow:**

```
Login:
  registry.getOrCreate("sess-alice", "alice")
  → new UserSession(id=1, userId="alice")
  → [SESSION CREATED #1] userId=alice

Concurrent tab requests (5 threads):
  Thread-1: sess.recordPageView("/dashboard")
    requestCount.incrementAndGet() → 1 (atomic)
    pageHistory.add("/dashboard")
  Thread-2: sess.recordPageView("/orders")
    requestCount.incrementAndGet() → 2 (atomic, no race)
    pageHistory.add("/orders")
  ... (3 more threads) ...
  All 5 threads modify the SAME UserSession#1 (same session bean)
  ConcurrentHashMap.put("lastVisited", page) → last writer wins (acceptable)

Sequential request:
  sess.recordPageView("/checkout")
    requestCount = 6
    pageHistory has 6 entries

Logout:
  registry.invalidate("sess-alice")
  → UserSession#1.destroy()
  → [SESSION DESTROYED #1] userId=alice requests=6 duration=Xs pages=[/dashboard, /orders, ...]
  → registry.remove("sess-alice")
```

**Why thread-safety matters in session scope:**

```
Without ConcurrentHashMap / AtomicInteger:
  Thread-1: requestCount = 3 (read)
  Thread-2: requestCount = 3 (read — stale!)
  Thread-1: requestCount = 4 (write)
  Thread-2: requestCount = 4 (write — lost Thread-1's increment!)
  Result: 4 instead of 5 — data race.

With AtomicInteger.incrementAndGet():
  All increments are atomic — no lost updates.
```

## 7. Gotchas & takeaways

> **Session beans are not automatically thread-safe.** Two browser tabs from the same user can fire concurrent requests on the same `JSESSIONID` → same session bean. If the bean holds mutable state, use `AtomicInteger`, `ConcurrentHashMap`, `CopyOnWriteArrayList`, or `synchronized` blocks to protect it.

> **Session scope requires a `proxyMode` when injected into a singleton.** Without `ScopedProxyMode.TARGET_CLASS`, Spring tries to create the session bean at startup (when no session exists), throwing `IllegalStateException`. The proxy defers bean lookup to each method call time, when a session is active.

- Spring calls `@PreDestroy` on session-scoped beans when the `HttpSession` is invalidated or times out — if the bean implements `HttpSessionBindingListener`, Spring calls `valueUnbound()` instead.
- In a clustered environment (multiple server nodes), session-scoped beans are not automatically replicated. Use sticky sessions or a distributed session store (Spring Session + Redis) to persist session beans across nodes.
- `@SessionScope` (Spring Boot shortcut) sets `scope="session"` and `proxyMode=TARGET_CLASS` automatically — prefer it over the verbose annotation form.
- Unlike request-scoped beans, session-scoped beans survive across multiple request/response cycles — any data stored in them persists until the session ends.
