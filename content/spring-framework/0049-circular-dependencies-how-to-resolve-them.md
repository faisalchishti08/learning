---
card: spring-framework
gi: 49
slug: circular-dependencies-how-to-resolve-them
title: Circular dependencies — how to resolve them
---

## 1. What it is

A **circular dependency** occurs when bean A depends on bean B, and bean B also depends on bean A (directly or through a chain). Spring cannot satisfy both constructor arguments simultaneously — to create A it needs B, but to create B it needs A.

```
Constructor circular (fails at startup):
  A(B b) and B(A a)
  → Spring tries: create A → needs B → create B → needs A → BeanCurrentlyInCreationException

Setter circular (works):
  A() { } + A.setB(B b)
  B(A a)
  → Spring creates empty A, creates B (injecting the empty A shell),
    then calls A.setB(b) → both fully wired
```

In one sentence: **Circular dependencies happen when two beans each need the other to be created first; Spring detects constructor circulars at startup and throws, while setter/field circulars are resolved using an "early singleton reference" cache.**

## 2. Why & when

Circular dependencies usually indicate a design problem — two classes are too tightly coupled. The recommended fix is to **break the cycle by extracting shared logic** into a third bean that both A and B depend on without depending on each other.

If breaking the cycle is impractical right now, Spring provides escape hatches:

- **Use setter or field injection on one side** — Spring creates the bean first (empty), puts an early reference in the singleton cache, then injects it into the other bean.
- **`@Lazy` on one injection point** — Spring injects a CGLIB proxy instead of the real bean; the real bean is created on first method call.

Circular dependencies are always a warning sign, but they surface legitimately in legacy codebases, plugin architectures, and frameworks where two subsystems must know about each other.

## 3. Core concept

```
Spring's early singleton cache (singletonFactories):

  Problem: A needs B, B needs A (constructor DI both sides)
  → deadlock → BeanCurrentlyInCreationException

  Solution: one side uses setter DI
  Step 1: create A() empty → register A in "earlySingletonObjects" cache
  Step 2: create B(A a)   → find A in early cache → inject early A into B
  Step 3: A is now fully created → call A.setB(b) → wire B into A
  Step 4: Both fully wired ✓

  @Lazy alternative:
  Step 1: create A(B b)  → B not yet created → inject CGLIB proxy for B
  Step 2: create B(A a)  → inject A directly (A exists)
  Step 3: first call to b.someMethod() → proxy fetches real B → delegates
```

## 4. Diagram

<svg viewBox="0 0 680 205" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Circular dependency: constructor DI deadlocks; setter DI breaks the cycle via early singleton cache">
  <defs>
    <marker id="a49" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="b49" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#e06c75"/></marker>
    <marker id="c49" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>

  <!-- Left: Constructor deadlock -->
  <text x="140" y="18" fill="#e06c75" font-size="10" text-anchor="middle" font-family="sans-serif">Constructor circular (FAILS)</text>
  <rect x="10"  y="28" width="100" height="44" rx="5" fill="#1c2430" stroke="#e06c75" stroke-width="1.5"/>
  <text x="60"  y="54" fill="#e06c75" font-size="10" text-anchor="middle" font-family="sans-serif">AuthService(B)</text>
  <rect x="170" y="28" width="100" height="44" rx="5" fill="#1c2430" stroke="#e06c75" stroke-width="1.5"/>
  <text x="220" y="54" fill="#e06c75" font-size="10" text-anchor="middle" font-family="sans-serif">SessionStore(A)</text>
  <path d="M110,44 C140,20 140,20 168,44" stroke="#e06c75" stroke-width="1.5" fill="none" marker-end="url(#b49)"/>
  <path d="M170,60 C140,82 140,82 112,60" stroke="#e06c75" stroke-width="1.5" fill="none" marker-end="url(#b49)"/>
  <text x="140" y="94" fill="#e06c75" font-size="8" text-anchor="middle" font-family="sans-serif">BeanCurrentlyInCreationException</text>

  <!-- Right: Setter resolution -->
  <text x="480" y="18" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">Setter on one side (WORKS)</text>
  <rect x="350" y="28" width="120" height="44" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="410" y="46" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">AuthService()</text>
  <text x="410" y="62" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">setSessionStore(B)</text>
  <rect x="520" y="28" width="120" height="44" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="580" y="54" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">SessionStore(A)</text>

  <!-- Steps -->
  <text x="480" y="100" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">① new AuthService() → early cache</text>
  <text x="480" y="114" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">② new SessionStore(earlyA) ✓</text>
  <text x="480" y="128" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">③ authService.setSessionStore(B) ✓</text>

  <!-- Early cache box -->
  <rect x="350" y="140" width="290" height="34" rx="4" fill="#0d1117" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="495" y="158" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">Early singleton cache: {authService → incomplete A}</text>

  <line x1="410" y1="72" x2="410" y2="137" stroke="#79c0ff" stroke-width="1.2" stroke-dasharray="3,2" marker-end="url(#c49)"/>
  <line x1="495" y1="174" x2="580" y2="74"  stroke="#79c0ff" stroke-width="1.2" stroke-dasharray="3,2" marker-end="url(#c49)"/>
</svg>

Constructor circular: deadlock. Setter on one side: Spring puts an early (incomplete) reference in the cache, creates B injecting the early A, then finishes wiring A.

## 5. Runnable example

Scenario: `AuthService` needs `SessionStore` to look up sessions; `SessionStore` needs `AuthService` to validate tokens before storing. Classic circular dependency.

### Level 1 — Basic

Show the problem, then fix with setter injection on one side.

```java
// CircularDepDemo.java — run with: java CircularDepDemo.java
import java.util.*;

public class CircularDepDemo {

    // --- Beans ---
    static class AuthService {
        private SessionStore sessionStore;  // setter-injected (breaks circle)

        AuthService() { System.out.println("  [1] AuthService() created (empty)"); }

        void setSessionStore(SessionStore s) {
            System.out.println("  [3] AuthService.setSessionStore → wired");
            this.sessionStore = s;
        }

        boolean validateToken(String token) { return token.startsWith("tok-"); }

        String login(String user) {
            String token = "tok-" + user + "-" + (int)(Math.random()*9000+1000);
            sessionStore.store(user, token);
            return token;
        }
    }

    static class SessionStore {
        private final AuthService auth;  // constructor-injected
        private final Map<String, String> sessions = new HashMap<>();

        SessionStore(AuthService auth) {
            System.out.println("  [2] SessionStore(AuthService) created");
            this.auth = auth;
        }

        void store(String user, String token) {
            if (!auth.validateToken(token))
                throw new IllegalArgumentException("Invalid token: " + token);
            sessions.put(token, user);
            System.out.println("  [SESSION] stored: " + user + " → " + token);
        }

        Optional<String> lookup(String token) {
            return Optional.ofNullable(sessions.get(token));
        }
    }

    // Minimal container resolving the circular dependency
    static class Ctx {
        AuthService  auth;
        SessionStore sessions;

        void refresh() {
            System.out.println("=== Container startup ===");
            // 1. Create AuthService (empty — setSessionStore not called yet)
            auth = new AuthService();
            // 2. Create SessionStore injecting the (still-empty) AuthService
            sessions = new SessionStore(auth);
            // 3. Complete AuthService wiring
            auth.setSessionStore(sessions);
            System.out.println("  [CTX] Both beans fully wired ✓");
        }
    }

    public static void main(String[] args) {
        Ctx ctx = new Ctx();
        ctx.refresh();

        System.out.println("\n=== Application running ===");
        String token = ctx.auth.login("alice");
        System.out.println("  alice token: " + token);
        System.out.println("  lookup: " + ctx.sessions.lookup(token));
        System.out.println("  bad token: " + ctx.sessions.lookup("bad-token"));
    }
}
```

How to run: `java CircularDepDemo.java`

`AuthService` is created first (step 1) — its `sessionStore` field is null. `SessionStore` is created second (step 2), receiving the partially-initialized `AuthService` as a constructor argument. Finally (step 3), `setSessionStore` completes `AuthService`'s wiring. By step 3, `SessionStore` exists, so the setter can be called.

### Level 2 — Intermediate

Add a `@Lazy`-style proxy alternative: inject a proxy wrapper that defers the real bean lookup to first use.

```java
// CircularDepDemo2.java — run with: java CircularDepDemo2.java
import java.lang.reflect.*;
import java.util.*;

public class CircularDepDemo2 {

    interface NotificationSender { void send(String user, String message); }
    interface UserPreferences     { Map<String, String> prefs(String user); }

    // NotificationSender needs UserPreferences to look up preferred channel.
    // UserPreferences needs NotificationSender to send a "preferences updated" notification.
    // Solution: @Lazy proxy on UserPreferences injection in NotificationSender.

    static class UserPreferencesService implements UserPreferences {
        private NotificationSender sender;  // setter injection

        UserPreferencesService() { System.out.println("  [1] UserPreferencesService() created"); }

        void setNotificationSender(NotificationSender s) {
            System.out.println("  [3] UserPreferencesService.setNotificationSender wired");
            this.sender = s;
        }

        @Override public Map<String, String> prefs(String user) {
            return Map.of("channel", "email", "theme", "dark", "user", user);
        }

        void updatePrefs(String user, String channel) {
            System.out.println("  [PREFS] updated " + user + " channel=" + channel);
            if (sender != null)
                sender.send(user, "Your notification channel is now: " + channel);
        }
    }

    static class EmailNotificationSender implements NotificationSender {
        private final UserPreferences prefs;  // injected — may be a proxy

        EmailNotificationSender(UserPreferences prefs) {
            System.out.println("  [2] EmailNotificationSender(UserPreferences) created");
            this.prefs = prefs;
        }

        @Override public void send(String user, String msg) {
            String channel = prefs.prefs(user).get("channel");
            System.out.println("  [NOTIFY via " + channel + "] " + user + ": " + msg);
        }
    }

    // @Lazy-style proxy: wraps a Supplier<T>, resolves on first call
    @SuppressWarnings("unchecked")
    static <T> T lazyProxy(Class<T> iface, java.util.function.Supplier<T> supplier) {
        Object[] holder = {null};
        return (T) Proxy.newProxyInstance(
            iface.getClassLoader(), new Class<?>[]{iface},
            (proxy, method, args) -> {
                if (holder[0] == null) {
                    System.out.println("  [@Lazy] proxy first call → resolving real bean");
                    holder[0] = supplier.get();
                }
                return method.invoke(holder[0], args);
            }
        );
    }

    public static void main(String[] args) {
        System.out.println("=== Container startup with @Lazy proxy ===");

        // Hold references to allow forward-reference in lambda
        UserPreferencesService[] prefsRef = {null};

        // 1. Create UserPreferencesService (no deps yet)
        prefsRef[0] = new UserPreferencesService();

        // 2. Create EmailNotificationSender with a LAZY proxy for UserPreferences
        //    The proxy will resolve to prefsRef[0] on first call — not during construction
        UserPreferences lazyPrefs = lazyProxy(UserPreferences.class, () -> prefsRef[0]);
        EmailNotificationSender sender = new EmailNotificationSender(lazyPrefs);

        // 3. Complete UserPreferencesService wiring
        prefsRef[0].setNotificationSender(sender);
        System.out.println("  [CTX] Wiring complete ✓");

        System.out.println("\n=== Application running ===");
        // First call to prefs() triggers proxy resolution
        sender.send("alice", "Welcome!");
        prefsRef[0].updatePrefs("bob", "sms");
    }
}
```

How to run: `java CircularDepDemo2.java`

Instead of setter injection to break the circle, this uses a lazy proxy: `EmailNotificationSender` receives a proxy object at construction time. When `send()` is first called, the proxy resolves to the real `UserPreferencesService`. This mirrors Spring's `@Lazy` injection — no setter needed on the notification sender side.

### Level 3 — Advanced

Best practice: extract the shared concern into a third bean, eliminating the circular dependency entirely.

```java
// CircularDepDemo3.java — run with: java CircularDepDemo3.java
import java.util.*;

public class CircularDepDemo3 {

    // BEFORE: OrderService ←→ InventoryService circular
    // OrderService needs InventoryService to check stock.
    // InventoryService needs OrderService to cancel orders when stock is zero.
    //
    // AFTER: extract StockEventPublisher as a shared dependency.
    // Both depend on it; neither depends on the other.

    // --- Shared component (extracted) ---
    static class StockEventPublisher {
        private final List<String> events = new ArrayList<>();

        StockEventPublisher() { System.out.println("  [1] StockEventPublisher created"); }

        void publish(String event) {
            events.add(event);
            System.out.println("  [EVENT] " + event);
        }

        List<String> getEvents() { return Collections.unmodifiableList(events); }
    }

    // --- OrderService: depends on InventoryService + StockEventPublisher ---
    static class OrderService {
        private final InventoryService  inventory;
        private final StockEventPublisher publisher;

        OrderService(InventoryService inventory, StockEventPublisher publisher) {
            System.out.println("  [3] OrderService(InventoryService, StockEventPublisher) created");
            this.inventory = inventory; this.publisher = publisher;
        }

        String placeOrder(String productId, int qty) {
            if (!inventory.reserve(productId, qty)) {
                publisher.publish("ORDER_FAILED: no stock for " + productId);
                return "FAILED: out of stock";
            }
            String orderId = "ORD-" + productId + "-" + qty;
            publisher.publish("ORDER_PLACED: " + orderId);
            return orderId;
        }
    }

    // --- InventoryService: depends on StockEventPublisher only ---
    static class InventoryService {
        private final Map<String, Integer>  stock      = new HashMap<>();
        private final StockEventPublisher   publisher;

        InventoryService(StockEventPublisher publisher) {
            System.out.println("  [2] InventoryService(StockEventPublisher) created");
            this.publisher = publisher;
            stock.put("LAPTOP", 10); stock.put("MOUSE", 50); stock.put("KEYBOARD", 0);
        }

        boolean reserve(String productId, int qty) {
            int current = stock.getOrDefault(productId, 0);
            if (current < qty) {
                publisher.publish("STOCK_INSUFFICIENT: " + productId + " have=" + current + " need=" + qty);
                return false;
            }
            stock.put(productId, current - qty);
            publisher.publish("STOCK_RESERVED: " + productId + " qty=" + qty + " remaining=" + (current - qty));
            return true;
        }

        int getStock(String productId) { return stock.getOrDefault(productId, 0); }
    }

    public static void main(String[] args) {
        System.out.println("=== Container startup (no circular dependency) ===");
        // Dependency order: StockEventPublisher → InventoryService → OrderService
        StockEventPublisher publisher = new StockEventPublisher();
        InventoryService    inventory = new InventoryService(publisher);
        OrderService        orders    = new OrderService(inventory, publisher);
        System.out.println("  [CTX] All beans wired via constructor DI — no circular dep ✓");

        System.out.println("\n=== Application running ===");
        System.out.println("  " + orders.placeOrder("LAPTOP",   2));
        System.out.println("  " + orders.placeOrder("KEYBOARD", 1));
        System.out.println("  " + orders.placeOrder("LAPTOP",   15));

        System.out.println("\n=== Event log ===");
        publisher.getEvents().forEach(e -> System.out.println("  • " + e));

        System.out.println("\n=== Stock after orders ===");
        System.out.println("  LAPTOP:   " + inventory.getStock("LAPTOP"));
        System.out.println("  KEYBOARD: " + inventory.getStock("KEYBOARD"));

        System.out.println("\n=== Design lesson ===");
        System.out.println("  BEFORE: OrderService ←→ InventoryService (circular)");
        System.out.println("  AFTER:  Both depend on StockEventPublisher; neither depends on the other");
        System.out.println("  Circular deps = design smell: extract the shared concern into a third bean");
    }
}
```

How to run: `java CircularDepDemo3.java`

`StockEventPublisher` is created first. `InventoryService` depends only on the publisher. `OrderService` depends on both `InventoryService` and the publisher — but not on `InventoryService` depending back on `OrderService`. All three constructors are satisfied in order: 1 → 2 → 3. The circular dependency is gone entirely.

## 6. Walkthrough

**Level 3 — creation order and wiring:**

```
new StockEventPublisher()        → id=1, no deps
new InventoryService(publisher)  → id=2, stock pre-loaded
new OrderService(inventory, publisher) → id=3, all deps satisfied

orders.placeOrder("LAPTOP", 2):
  → inventory.reserve("LAPTOP", 2)
      → stock["LAPTOP"] = 10 ≥ 2 ✓
      → publish("STOCK_RESERVED: LAPTOP qty=2 remaining=8")
      → stock["LAPTOP"] = 8
      → return true
  → publish("ORDER_PLACED: ORD-LAPTOP-2")
  → return "ORD-LAPTOP-2"

orders.placeOrder("KEYBOARD", 1):
  → inventory.reserve("KEYBOARD", 1)
      → stock["KEYBOARD"] = 0 < 1 ✗
      → publish("STOCK_INSUFFICIENT: KEYBOARD have=0 need=1")
      → return false
  → publish("ORDER_FAILED: no stock for KEYBOARD")
  → return "FAILED: out of stock"
```

**Event log (in order):**
```
STOCK_RESERVED: LAPTOP qty=2 remaining=8
ORDER_PLACED: ORD-LAPTOP-2
STOCK_INSUFFICIENT: KEYBOARD have=0 need=1
ORDER_FAILED: no stock for KEYBOARD
STOCK_INSUFFICIENT: LAPTOP have=8 need=15
ORDER_FAILED: no stock for LAPTOP
```

## 7. Gotchas & takeaways

> **Spring 6 / Spring Boot 3 no longer silently resolves setter circular dependencies by default.** In older versions, setter-circular worked out of the box. Modern Spring requires explicit opt-in via `spring.main.allow-circular-references=true` in `application.properties` — and it logs a warning. Treat circular deps as errors, not features.

> **`@Lazy` on a constructor parameter injects a CGLIB proxy, not the real bean.** The proxy intercepts every method call and lazily fetches the real bean on first invocation. This adds overhead and can surprise code that checks `instanceof` or uses `equals()` on the injected object.

- Spring 6 detects circular dependencies involving `@Autowired` fields at startup. Pre-Spring 6, field circulars were resolved silently; now they also throw unless opted-in.
- The correct fix for a circular dependency is almost always architectural: extract a shared service, use an event/message bus, or break the cycle by moving one direction of the relationship to a callback or observer pattern.
- `@DependsOn` is for ordering, not for resolving circulars — it only says "create B before A" but does not inject B into A.
- If you must allow circular references in Spring Boot 3, add `spring.main.allow-circular-references=true` — but add a comment and track it for refactoring.
