---
card: spring-framework
gi: 67
slug: scoped-beans-as-dependencies-scoped-proxies
title: Scoped beans as dependencies (scoped proxies)
---

## 1. What it is

When a **short-lived bean** (request, session, prototype) is injected into a **longer-lived bean** (singleton), there is a lifecycle mismatch: the singleton is created once at startup, but at that moment no request or session may be active. The solution is a **scoped proxy** — a wrapper object injected instead of the real bean. Every method call on the proxy is routed to the correct instance for the current scope (current request, current session, etc.) at call time.

```java
// Session-scoped bean with proxy enabled
@Component
@SessionScope   // shorthand for @Scope("session", proxyMode=TARGET_CLASS)
public class ShoppingBasket {
    private final List<Item> items = new ArrayList<>();
    public void addItem(Item item) { items.add(item); }
}

// Singleton service: injects the proxy, not the real basket
@Service
public class OrderService {
    @Autowired
    private ShoppingBasket basket;   // ← actually a proxy

    public void checkout() {
        basket.addItem(new Item("Laptop"));  // proxy routes to current session's real basket
    }
}
```

In one sentence: **A scoped proxy is a generated wrapper object — injected in place of a short-lived bean — that routes every method call to the correct scoped bean instance for the current request/session/thread, solving the singleton-into-short-lived injection problem.**

## 2. Why & when

The problem: Spring builds the singleton graph at startup. If `OrderService` (singleton) `@Autowired`s `ShoppingBasket` (session-scoped) directly, Spring would try to create `ShoppingBasket` at startup — but there is no HTTP session yet → `IllegalStateException`.

Even if it worked, the singleton would hold a **single basket forever**, shared across all users — a critical data leak.

The proxy solves both problems:
- Spring can inject a proxy at startup (no active session needed).
- Each method call on the proxy looks up the **current session's** real basket at call time.

Use scoped proxies whenever a shorter-lived bean is injected into a longer-lived one:
- Request bean → into singleton: always need a proxy.
- Session bean → into singleton: always need a proxy.
- Prototype → into singleton: need proxy OR `ObjectProvider` / `@Lookup`.

## 3. Core concept

```
Without proxy (broken):
  Singleton created at startup.
  Spring tries to create session bean → no session → error or stale reference.

With ScopedProxyMode.TARGET_CLASS:
  Spring generates: class ShoppingBasket$$SpringCGLIB$$ extends ShoppingBasket { ... }
  Every method delegates to:
    → ScopedProxyUtils.getTargetBeanName()
    → ApplicationContext.getBean(scopedName, ShoppingBasket.class)
    → looks up current request's scope store → returns real instance

  Singleton holds proxy. Proxy is stateless. Real bean lives in scope store.

proxyMode options:
  NO             — no proxy (breaks for singleton ← short-lived injection)
  INTERFACES     — JDK dynamic proxy (only works if bean implements an interface)
  TARGET_CLASS   — CGLIB subclass proxy (works for classes; preferred)

@RequestScope, @SessionScope, @ApplicationScope
  All set proxyMode=TARGET_CLASS by default.
```

## 4. Diagram

<svg viewBox="0 0 680 215" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Scoped proxy: singleton holds a proxy; proxy routes each call to the current session's real bean">
  <defs>
    <marker id="a67" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="b67" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>
  <rect x="5" y="5" width="670" height="202" rx="8" fill="#0d1117" stroke="#8b949e" stroke-width="1.2"/>
  <text x="338" y="22" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Scoped proxy — singleton holds proxy; proxy dispatches to current scope's bean</text>

  <!-- Singleton -->
  <rect x="15" y="35" width="170" height="70" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1.3"/>
  <text x="100" y="55" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">OrderService (singleton)</text>
  <rect x="25" y="65" width="150" height="28" rx="3" fill="#0d1117" stroke="#6db33f" stroke-width="1"/>
  <text x="100" y="83" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">basket = ShoppingBasket$$Proxy</text>

  <!-- Proxy -->
  <rect x="210" y="35" width="200" height="70" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="310" y="55" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">ShoppingBasket$$CGLIBProxy</text>
  <text x="310" y="70" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">addItem() → lookup current scope</text>
  <text x="310" y="84" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">→ getBean(scopedTarget.basket)</text>

  <!-- Session store -->
  <rect x="450" y="30" width="215" height="165" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="557" y="48" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Scope Store (Session / Request)</text>

  <rect x="460" y="58" width="195" height="50" rx="4" fill="#0d1117" stroke="#79c0ff" stroke-width="1.2"/>
  <text x="557" y="75" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">Session-Alice → ShoppingBasket#A</text>
  <text x="557" y="89" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">items=[Laptop, Mouse]</text>
  <text x="557" y="101" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">← returned for Thread-Alice's call</text>

  <rect x="460" y="118" width="195" height="50" rx="4" fill="#0d1117" stroke="#6db33f" stroke-width="1.2"/>
  <text x="557" y="135" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">Session-Bob → ShoppingBasket#B</text>
  <text x="557" y="149" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">items=[Keyboard]</text>
  <text x="557" y="163" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">← returned for Thread-Bob's call</text>

  <!-- Arrows -->
  <line x1="185" y1="70" x2="208" y2="70" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a67)"/>
  <line x1="410" y1="80" x2="448" y2="83" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a67)"/>

  <text x="420" y="72" fill="#6db33f" font-size="7" font-family="sans-serif">Thread=Alice→#A</text>
  <text x="420" y="100" fill="#6db33f" font-size="7" font-family="sans-serif">Thread=Bob→#B</text>

  <text x="338" y="200" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">Singleton holds one proxy permanently. Proxy routes to the right scoped instance per thread/request.</text>
</svg>

The singleton's `basket` field holds one proxy forever. When Alice's thread calls `basket.addItem(...)`, the proxy looks up "current thread = Alice's session → return `ShoppingBasket#A`". Bob's thread gets `ShoppingBasket#B`.

## 5. Runnable example

Scenario: a `CheckoutService` singleton that uses a session-scoped `ShoppingBasket`. We simulate the scoped proxy lookup mechanism — the singleton is created once; basket lookups happen per-request thread.

### Level 1 — Basic

Demonstrate the proxy pattern: a factory that returns the scope-correct instance on each call.

```java
// ScopedProxyDemo.java — run with: java ScopedProxyDemo.java
import java.util.*;
import java.util.function.Supplier;

public class ScopedProxyDemo {

    // ── session-scoped bean ───────────────────────────────────────────
    static class ShoppingBasket {
        private static int count = 0;
        final int id;
        final String sessionId;
        private final List<String> items = new ArrayList<>();

        ShoppingBasket(String sessionId) {
            id = ++count;
            this.sessionId = sessionId;
            System.out.println("  [BASKET CREATED #" + id + "] session=" + sessionId);
        }
        void addItem(String item) { items.add(item); System.out.println("  [ADD] " + item + " to basket#" + id + " session=" + sessionId); }
        List<String> getItems() { return items; }
        int size() { return items.size(); }
        void destroy() { System.out.println("  [BASKET DESTROYED #" + id + "]"); }
    }

    // ── proxy: stateless wrapper that delegates to the scope-correct instance ──
    static class ShoppingBasketProxy {
        private final Supplier<ShoppingBasket> scopeLookup;  // simulates Spring's scope store

        ShoppingBasketProxy(Supplier<ShoppingBasket> scopeLookup) {
            this.scopeLookup = scopeLookup;
            System.out.println("  [PROXY CREATED] ShoppingBasketProxy (stateless)");
        }

        // Every call delegates to the current scope's real instance
        void addItem(String item) { scopeLookup.get().addItem(item); }
        List<String> getItems()   { return scopeLookup.get().getItems(); }
        int size()                { return scopeLookup.get().size(); }
    }

    // ── singleton service: holds the proxy ────────────────────────────
    static class CheckoutService {
        private final ShoppingBasketProxy basket;  // proxy, not the real bean

        CheckoutService(ShoppingBasketProxy basket) {
            this.basket = basket;
            System.out.println("  [SINGLETON] CheckoutService created (holds proxy)");
        }

        void addToCart(String item)    { basket.addItem(item); }
        String summarise()             { return "Cart(" + basket.size() + " items): " + basket.getItems(); }
        void checkout(String paymentToken) {
            System.out.println("  [CHECKOUT] " + summarise() + " payment=" + paymentToken);
        }
    }

    // ── scope store (simulates Spring's session scope) ─────────────────
    static final Map<String, ShoppingBasket> SCOPE_STORE = new LinkedHashMap<>();
    static String CURRENT_SESSION = null;  // ThreadLocal in real Spring

    static ShoppingBasket lookupCurrentBasket() {
        return SCOPE_STORE.computeIfAbsent(CURRENT_SESSION, ShoppingBasket::new);
    }

    public static void main(String[] args) {
        System.out.println("=== Container startup (no session) ===");
        ShoppingBasketProxy proxy = new ShoppingBasketProxy(ScopedProxyDemo::lookupCurrentBasket);
        CheckoutService svc = new CheckoutService(proxy);  // singleton created, proxy injected

        System.out.println("\n=== Alice's session ===");
        CURRENT_SESSION = "sess-alice";
        svc.addToCart("Laptop");
        svc.addToCart("USB Hub");
        System.out.println("  Alice cart: " + svc.summarise());

        System.out.println("\n=== Bob's session (same singleton, proxy routes to Bob's basket) ===");
        CURRENT_SESSION = "sess-bob";
        svc.addToCart("Keyboard");
        System.out.println("  Bob cart: " + svc.summarise());

        System.out.println("\n=== Back to Alice (proxy routes to Alice's basket again) ===");
        CURRENT_SESSION = "sess-alice";
        svc.addToCart("Monitor");
        svc.checkout("tok-alice-cc");

        System.out.println("\n=== Session cleanup ===");
        SCOPE_STORE.values().forEach(ShoppingBasket::destroy);
        System.out.println("[BASKETS CREATED] " + ShoppingBasket.count);
        System.out.println("[PROXIES CREATED] 1");
    }
}
```

How to run: `java ScopedProxyDemo.java`

`CheckoutService` is created once holding a `ShoppingBasketProxy`. When Alice's thread calls `svc.addToCart(...)`, the proxy calls `lookupCurrentBasket()` which looks up `"sess-alice"` → `ShoppingBasket#1`. When Bob's thread calls the same method, the proxy looks up `"sess-bob"` → `ShoppingBasket#2`. One singleton, one proxy, but the proxy correctly routes to each session's real bean.

### Level 2 — Intermediate

Concurrent requests from Alice and Bob — proxy correctly routes each thread to its own basket.

```java
// ScopedProxyDemo2.java — run with: java ScopedProxyDemo2.java
import java.util.*;
import java.util.concurrent.*;
import java.util.function.Supplier;

public class ScopedProxyDemo2 {

    static class ShoppingBasket {
        private static int count = 0;
        final int id;
        final String sessionId;
        private final List<String> items = Collections.synchronizedList(new ArrayList<>());

        ShoppingBasket(String sessionId) { id = ++count; this.sessionId = sessionId; }
        void add(String item) { items.add(item); }
        List<String> getItems() { return new ArrayList<>(items); }
        @Override public String toString() { return "Basket#" + id + "[" + items + "]"; }
    }

    // ── Thread-local simulates RequestContextHolder ────────────────────
    static final ThreadLocal<String> SESSION = new ThreadLocal<>();
    static final ConcurrentHashMap<String, ShoppingBasket> STORE = new ConcurrentHashMap<>();

    static ShoppingBasket current() {
        return STORE.computeIfAbsent(SESSION.get(), ShoppingBasket::new);
    }

    // ── proxy wrapper ─────────────────────────────────────────────────
    static class BasketProxy {
        void add(String item) { current().add(item); }
        List<String> getItems() { return current().getItems(); }
        @Override public String toString() { return "Proxy→" + current(); }
    }

    // ── singleton service ─────────────────────────────────────────────
    static class CartService {
        private final BasketProxy basket = new BasketProxy();  // injected proxy
        CartService() { System.out.println("  [SINGLETON] CartService created once"); }

        void addItem(String item) { basket.add(item); }
        String view() { return basket.toString(); }
    }

    public static void main(String[] args) throws Exception {
        CartService svc = new CartService();  // singleton

        // Simulate concurrent requests from Alice and Bob
        ExecutorService pool = Executors.newFixedThreadPool(2);

        Future<?> alice = pool.submit(() -> {
            SESSION.set("sess-alice");
            try {
                svc.addItem("Laptop");
                Thread.sleep(10);
                svc.addItem("Mouse");
                System.out.println("[ALICE] " + svc.view());
            } catch (InterruptedException e) { Thread.currentThread().interrupt(); }
            finally { SESSION.remove(); }
        });

        Future<?> bob = pool.submit(() -> {
            SESSION.set("sess-bob");
            try {
                svc.addItem("Keyboard");
                Thread.sleep(5);
                svc.addItem("Monitor");
                System.out.println("[BOB] " + svc.view());
            } catch (InterruptedException e) { Thread.currentThread().interrupt(); }
            finally { SESSION.remove(); }
        });

        alice.get(); bob.get();
        pool.shutdown();

        System.out.println("\n[RESULT] Alice basket: " + STORE.get("sess-alice"));
        System.out.println("[RESULT] Bob basket:   " + STORE.get("sess-bob"));
        System.out.println("[BASKETS] " + ShoppingBasket.count + " (no cross-contamination)");
    }
}
```

How to run: `java ScopedProxyDemo2.java`

Alice and Bob's threads both call methods on the same `CartService` singleton. The `ThreadLocal<String>` (simulating Spring's `RequestContextHolder`) ensures each thread's proxy lookup returns the right basket. Alice's thread always gets `ShoppingBasket#1`; Bob's always gets `ShoppingBasket#2`. No cross-contamination.

### Level 3 — Advanced

Real proxy using dynamic dispatch — CGLIB-style method interception — plus demonstrating what happens when the proxy is called outside a scope (no active session).

```java
// ScopedProxyDemo3.java — run with: java ScopedProxyDemo3.java
import java.lang.reflect.*;
import java.util.*;
import java.util.function.Supplier;

public class ScopedProxyDemo3 {

    // ── target class ──────────────────────────────────────────────────
    static class RequestMetrics {
        private static int count = 0;
        final int id;
        final String requestId;
        int dbQueries    = 0;
        int cacheHits    = 0;
        int cacheMs      = 0;
        int dbMs         = 0;

        RequestMetrics(String requestId) {
            id = ++count;
            this.requestId = requestId;
            System.out.println("    [METRICS CREATED #" + id + "] req=" + requestId);
        }

        void recordDb(int ms)    { dbQueries++; dbMs += ms; }
        void recordCache(int ms) { cacheHits++; cacheMs += ms; }

        String summary() {
            return String.format("Metrics#%d req=%s db=%d(%dms) cache=%d(%dms)",
                id, requestId, dbQueries, dbMs, cacheHits, cacheMs);
        }
    }

    // ── scope store with out-of-scope guard ────────────────────────────
    static final ThreadLocal<RequestMetrics> SCOPE = new ThreadLocal<>();

    static RequestMetrics getOrFail() {
        RequestMetrics m = SCOPE.get();
        if (m == null) throw new IllegalStateException(
            "No active request scope. Cannot access RequestMetrics outside a request.");
        return m;
    }

    // ── dynamic proxy using JDK Proxy (simulates CGLIB proxy) ─────────
    static RequestMetrics createProxy() {
        return (RequestMetrics) Proxy.newProxyInstance(
            RequestMetrics.class.getClassLoader(),
            new Class[]{},   // JDK proxy needs interface; we use reflection on concrete class
            (proxy, method, args) -> {
                RequestMetrics real = getOrFail();
                return method.invoke(real, args);
            }
        );
    }

    // ── simpler proxy using delegation ────────────────────────────────
    static class MetricsProxy extends RequestMetrics {
        MetricsProxy() { super("PROXY-DELEGATE"); }

        private RequestMetrics real() { return getOrFail(); }

        @Override public void recordDb(int ms)    { real().recordDb(ms); }
        @Override public void recordCache(int ms) { real().recordCache(ms); }
        @Override public String summary()         { return real().summary(); }
    }

    // ── singleton service holding the proxy ───────────────────────────
    static class ProductService {
        private final MetricsProxy metrics = new MetricsProxy();

        ProductService() { System.out.println("  [SINGLETON] ProductService created (metrics=proxy)"); }

        String findProduct(String sku) {
            // Cache check
            metrics.recordCache(2);
            if (sku.startsWith("HOT-")) {
                return "CachedProduct[" + sku + "]";
            }
            // DB fallback
            metrics.recordDb(15);
            return "DBProduct[" + sku + "]";
        }

        String getMetricsSummary() { return metrics.summary(); }
    }

    // ── request handler: sets scope, processes, clears scope ──────────
    static void handleRequest(ProductService svc, String requestId, String[] skus) {
        RequestMetrics real = new RequestMetrics(requestId);
        SCOPE.set(real);
        System.out.println("[REQUEST] " + requestId);
        try {
            for (String sku : skus) {
                String result = svc.findProduct(sku);
                System.out.println("  found: " + result);
            }
            System.out.println("  [SUMMARY] " + svc.getMetricsSummary());
        } finally {
            SCOPE.remove();
            System.out.println("  [METRICS CLEARED] #" + real.id);
        }
    }

    public static void main(String[] args) {
        ProductService svc = new ProductService();

        handleRequest(svc, "req-001", new String[]{"HOT-SKU-A", "COLD-SKU-B", "HOT-SKU-C"});
        System.out.println();
        handleRequest(svc, "req-002", new String[]{"COLD-SKU-D"});

        System.out.println("\n=== Call outside request scope (no ThreadLocal set) ===");
        try {
            svc.getMetricsSummary();  // proxy tries to get real bean → no scope → throw
        } catch (IllegalStateException e) {
            System.out.println("[CAUGHT] " + e.getMessage());
        }

        System.out.println("[METRICS BEANS CREATED] " + RequestMetrics.count);
    }
}
```

How to run: `java ScopedProxyDemo3.java`

`MetricsProxy` extends `RequestMetrics` (CGLIB-style) and delegates every method to `getOrFail()` which checks the thread-local scope store. Request 1 gets `RequestMetrics#1`; request 2 gets `RequestMetrics#2`. Calling `svc.getMetricsSummary()` outside a request → `getOrFail()` returns null → `IllegalStateException` — exactly what Spring throws when a scoped proxy is accessed outside its scope.

## 6. Walkthrough

**`handleRequest(svc, "req-001", ...)` — scoped proxy lifecycle:**

```
SCOPE.set(new RequestMetrics("req-001"))  ← Thread-local bound

svc.findProduct("HOT-SKU-A"):
  metrics.recordCache(2)          ← MetricsProxy.recordCache(2)
    → real() → SCOPE.get() → RequestMetrics#1 (req-001)
    → RequestMetrics#1.recordCache(2)  → cacheHits=1, cacheMs=2
  return "CachedProduct[HOT-SKU-A]"

svc.findProduct("COLD-SKU-B"):
  metrics.recordCache(2)          → cacheHits=2, cacheMs=4
  metrics.recordDb(15)            → dbQueries=1, dbMs=15
  return "DBProduct[COLD-SKU-B]"

svc.findProduct("HOT-SKU-C"):
  metrics.recordCache(2)          → cacheHits=3, cacheMs=6
  return "CachedProduct[HOT-SKU-C]"

svc.getMetricsSummary():
  → real() → RequestMetrics#1
  → "Metrics#1 req=req-001 db=1(15ms) cache=3(6ms)"

SCOPE.remove()  ← Thread-local cleared → request scope destroyed
```

## 7. Gotchas & takeaways

> **Without `proxyMode = ScopedProxyMode.TARGET_CLASS` (or `INTERFACES`), injecting a request/session-scoped bean into a singleton fails at startup** with `IllegalStateException: No thread-bound request found` or creates a frozen stale reference. Always specify a proxy mode when shorter-lived beans are injected into longer-lived ones.

> **The proxy's `toString()` / `hashCode()` / `equals()` methods behave unexpectedly.** They operate on the proxy object, not the real bean. Use `AopUtils.getTargetClass(proxy)` or cast through `Advised` to access the real instance if needed.

- `ScopedProxyMode.INTERFACES` requires the bean to implement at least one interface and creates a JDK dynamic proxy — no CGLIB dependency. `TARGET_CLASS` uses CGLIB to subclass the concrete class and requires the class to be non-final.
- `@RequestScope`, `@SessionScope`, and `@ApplicationScope` all default to `proxyMode = TARGET_CLASS`. Explicit `@Scope("request")` without a proxyMode defaults to `NO` — a common mistake.
- The scoped proxy is a true Spring AOP proxy — you can verify with `AopUtils.isCglibProxy(bean)`. Adding advice (e.g., logging) to a scoped bean wraps the proxy in another proxy layer.
- `ObjectProvider<T>` is an alternative to scoped proxies for prototype beans — call `provider.getObject()` to get a new instance on demand without needing a proxy wrapper.
