---
card: microservices
gi: 208
slug: sticky-sessions-session-affinity
title: "Sticky sessions / session affinity"
---

## 1. What it is

Sticky sessions (session affinity) is a load balancer deliberately routing all requests from the same client session to the same backend instance, breaking the usual assumption that any instance can handle any request — typically implemented by inspecting a session cookie or client identifier and consistently mapping it to one specific instance for the session's duration.

## 2. Why & when

A service that keeps session state in the memory of the specific instance that first handled a client (rather than in a shared, external store like Redis) requires every subsequent request from that same client to land on that same instance, or the session data simply won't be there — sticky sessions is the load-balancing mechanism that makes this work despite otherwise ordinary balancing logic that would happily route requests anywhere. This is fundamentally a compensating mechanism for services that haven't externalized their session state, not a feature to reach for by default.

Use sticky sessions only when a service genuinely keeps client-specific state in local, per-instance memory and externalizing that state (to a shared cache or database) isn't immediately feasible. Prefer designing services to be stateless, with session data in a shared external store, whenever possible — that approach makes every instance interchangeable, sidesteps sticky sessions' downsides entirely, and is the standard recommended pattern for horizontally scalable services.

## 3. Core concept

The balancer computes a consistent mapping from a session identifier (a cookie value, a client IP, or another stable per-client key) to a specific instance, and reuses that same instance for every subsequent request bearing the same identifier, only choosing a new instance if the originally-assigned one becomes unavailable.

```java
Map<String, String> sessionToInstance = new HashMap<>(); // sessionId -> assigned instance

String routeRequest(String sessionId) {
    if (sessionToInstance.containsKey(sessionId) && isHealthy(sessionToInstance.get(sessionId))) {
        return sessionToInstance.get(sessionId); // STICKY: same instance as last time
    }
    String chosen = normalLoadBalancer.choose(); // first time, or the sticky instance died
    sessionToInstance.put(sessionId, chosen);
    return chosen;
}
```

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Session abc123's first request is routed to instance B and recorded; every subsequent request carrying session abc123 is routed back to instance B specifically, while a different session, xyz789, is independently mapped to instance A" >
  <rect x="20" y="20" width="140" height="30" rx="4" fill="#1c2430" stroke="#79c0ff"/><text x="90" y="40" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">session: abc123</text>
  <rect x="20" y="90" width="140" height="30" rx="4" fill="#1c2430" stroke="#79c0ff"/><text x="90" y="110" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">session: xyz789</text>

  <rect x="300" y="20" width="120" height="30" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/><text x="360" y="40" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">Instance B</text>
  <rect x="300" y="90" width="120" height="30" rx="4" fill="#1c2430" stroke="#79c0ff"/><text x="360" y="110" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">Instance A</text>

  <line x1="160" y1="35" x2="298" y2="35" stroke="#8b949e" marker-end="url(#arr88)"/>
  <line x1="160" y1="105" x2="298" y2="105" stroke="#8b949e" marker-end="url(#arr88)"/>
  <text x="230" y="25" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">always -&gt; B</text>
  <text x="230" y="125" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">always -&gt; A</text>

  <defs>
    <marker id="arr88" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

Each session's requests are consistently pinned to the same instance, regardless of what the balancer's normal algorithm would otherwise select.

## 5. Runnable example

Scenario: a shopping-cart service keeping cart state in local instance memory that starts without sticky sessions and demonstrates the resulting data loss, adds sticky-session routing so a client's requests consistently reach the same instance, and finally demonstrates the necessary failure-handling behavior when a sticky instance becomes unavailable, showing the trade-off explicitly: session data loss on that specific instance's failure, contrasted with what an externalized session store would have avoided entirely.

### Level 1 — Basic

```java
// File: NoStickySessionsDataLoss.java -- NO session affinity; the SAME client's
// requests bounce between instances, and LOCAL-memory cart state is LOST each time.
import java.util.*;

public class NoStickySessionsDataLoss {
    static Map<String, List<String>> instanceLocalCartState = new HashMap<>(Map.of("A", new ArrayList<>(), "B", new ArrayList<>()));
    static List<String> instances = List.of("A", "B");
    static int index = 0;

    static String handleAddToCart(String sessionId, String item) {
        String chosen = instances.get(index++ % instances.size()); // round-robin -- NO session awareness
        instanceLocalCartState.get(chosen).add(item);
        return chosen;
    }

    public static void main(String[] args) {
        String sessionId = "session-abc123";
        System.out.println("add 'widget' -> instance " + handleAddToCart(sessionId, "widget"));
        System.out.println("add 'gadget' -> instance " + handleAddToCart(sessionId, "gadget"));

        System.out.println("\nInstance A's cart state: " + instanceLocalCartState.get("A"));
        System.out.println("Instance B's cart state: " + instanceLocalCartState.get("B"));
        System.out.println("The SAME session's cart is SPLIT across TWO instances -- neither has the FULL cart!");
    }
}
```

**How to run:** `javac NoStickySessionsDataLoss.java && java NoStickySessionsDataLoss` (JDK 17+).

### Level 2 — Intermediate

```java
// File: StickySessionRouting.java -- the SAME session ALWAYS lands on the SAME
// instance -- local-memory cart state stays CONSISTENT for that session.
import java.util.*;

public class StickySessionRouting {
    static Map<String, List<String>> instanceLocalCartState = new HashMap<>(Map.of("A", new ArrayList<>(), "B", new ArrayList<>()));
    static List<String> instances = List.of("A", "B");
    static Map<String, String> sessionToInstance = new HashMap<>(); // STICKY mapping
    static int index = 0;

    static String handleAddToCart(String sessionId, String item) {
        String chosen = sessionToInstance.computeIfAbsent(sessionId, id -> instances.get(index++ % instances.size())); // STICKY
        instanceLocalCartState.get(chosen).add(item);
        return chosen;
    }

    public static void main(String[] args) {
        String sessionId = "session-abc123";
        System.out.println("add 'widget' -> instance " + handleAddToCart(sessionId, "widget"));
        System.out.println("add 'gadget' -> instance " + handleAddToCart(sessionId, "gadget"));
        System.out.println("add 'gizmo' -> instance " + handleAddToCart(sessionId, "gizmo"));

        System.out.println("\nInstance A's cart state: " + instanceLocalCartState.get("A"));
        System.out.println("Instance B's cart state: " + instanceLocalCartState.get("B"));
        System.out.println("ALL THREE items landed on the SAME instance -- the FULL cart is consistently there.");
    }
}
```

**How to run:** `javac StickySessionRouting.java && java StickySessionRouting` (JDK 17+).

Expected output:
```
add 'widget' -> instance A
add 'gadget' -> instance A
add 'gizmo' -> instance A

Instance A's cart state: [widget, gadget, gizmo]
Instance B's cart state: []
ALL THREE items landed on the SAME instance -- the FULL cart is consistently there.
```

### Level 3 — Advanced

```java
// File: StickyInstanceFailureExposesTheTradeoff.java -- when the STICKY
// instance DIES, its LOCAL cart state is GONE -- exposing sticky sessions'
// fundamental fragility, the exact problem an EXTERNAL session store avoids.
import java.util.*;

public class StickyInstanceFailureExposesTheTradeoff {
    static Map<String, List<String>> instanceLocalCartState = new HashMap<>(Map.of("A", new ArrayList<>(), "B", new ArrayList<>()));
    static Set<String> healthyInstances = new HashSet<>(Set.of("A", "B"));
    static List<String> instances = List.of("A", "B");
    static Map<String, String> sessionToInstance = new HashMap<>();
    static int index = 0;

    static String handleAddToCart(String sessionId, String item) {
        String sticky = sessionToInstance.get(sessionId);
        if (sticky != null && healthyInstances.contains(sticky)) {
            instanceLocalCartState.get(sticky).add(item);
            return sticky;
        }
        // sticky instance is GONE (or first request) -- must pick a NEW one, LOSING any prior local state
        String chosen = instances.stream().filter(healthyInstances::contains).findFirst().orElseThrow();
        sessionToInstance.put(sessionId, chosen);
        instanceLocalCartState.get(chosen).add(item);
        return chosen;
    }

    public static void main(String[] args) {
        String sessionId = "session-abc123";
        System.out.println("add 'widget' -> " + handleAddToCart(sessionId, "widget"));
        System.out.println("add 'gadget' -> " + handleAddToCart(sessionId, "gadget"));
        System.out.println("Cart before failure: " + instanceLocalCartState.get(sessionToInstance.get(sessionId)));

        System.out.println("\n*** Instance A CRASHES ***");
        healthyInstances.remove("A");

        System.out.println("add 'gizmo' -> " + handleAddToCart(sessionId, "gizmo") + " (re-routed to a DIFFERENT, healthy instance)");
        System.out.println("New instance's cart: " + instanceLocalCartState.get(sessionToInstance.get(sessionId)));
        System.out.println("\n'widget' and 'gadget' are GONE FOREVER -- they lived ONLY in instance A's local memory. An EXTERNAL session store (Redis, etc.) would NOT have lost this.");
    }
}
```

**How to run:** `javac StickyInstanceFailureExposesTheTradeoff.java && java StickyInstanceFailureExposesTheTradeoff` (JDK 17+).

Expected output:
```
add 'widget' -> A
add 'gadget' -> A
Cart before failure: [widget, gadget]

*** Instance A CRASHES ***
add 'gizmo' -> B (re-routed to a DIFFERENT, healthy instance)
New instance's cart: [gizmo]

'widget' and 'gadget' are GONE FOREVER -- they lived ONLY in instance A's local memory. An EXTERNAL session store (Redis, etc.) would NOT have lost this.
```

## 6. Walkthrough

1. **Level 1** — `handleAddToCart` always computes `chosen` via `instances.get(index++ % instances.size())`, entirely ignoring `sessionId`; the two calls with the identical session land on `A` then `B`, splitting the cart's contents across two instances that have no shared memory.
2. **Level 1, the resulting data fragmentation** — printing each instance's local state shows `widget` on one and `gadget` on the other, confirming that no single instance ever holds the complete, correct cart for this session — a direct, observable bug caused by round-robin balancing applied to a stateful, non-externalized service.
3. **Level 2, the sticky mapping** — `sessionToInstance.computeIfAbsent(sessionId, ...)` looks up an existing mapping for `sessionId`, and only computes (and stores) a new instance assignment if none exists yet; every subsequent call with the same `sessionId` reuses the stored value instead of recomputing.
4. **Level 2, the consistent result** — all three items land on instance `A` (whichever the first call happened to assign), and the printed state confirms the complete, correct three-item cart is entirely present on that single instance, directly resolving Level 1's fragmentation.
5. **Level 3, checking the sticky instance's health** — `handleAddToCart` now checks `healthyInstances.contains(sticky)` before trusting the existing mapping; if the previously-assigned instance is no longer healthy, the code falls through to selecting a new instance instead.
6. **Level 3, the crash and its consequence** — after `healthyInstances.remove("A")` simulates instance `A` crashing, the next call for the same session finds its sticky mapping (`A`) no longer healthy, so it selects `B` instead and records the new mapping — but crucially, `instanceLocalCartState.get("A")` (still holding `["widget", "gadget"]` in memory on the now-crashed instance) is unreachable and effectively lost from the application's perspective.
7. **Level 3, the trade-off stated explicitly** — the final printed comment names the core limitation directly: sticky sessions provide consistency *as long as the sticky instance stays healthy*, but offer no protection against that specific instance's failure taking its locally-held session state down with it — this is precisely the failure mode an externalized session store (session data written to Redis or a database, readable by any instance) avoids entirely, since any instance picking up the session after a failure would find the same, complete state regardless of which instance originally handled it.

## 7. Gotchas & takeaways

> **Gotcha:** sticky sessions also undermine even load distribution over time — a long-lived, active session pins its traffic to one specific instance for the session's entire duration, and if a disproportionate number of long, active sessions happen to be assigned to the same instance (by chance, or because that instance came online earlier and accumulated more sessions), that instance can become persistently more loaded than others despite an otherwise-fair initial assignment algorithm; sticky sessions and perfectly even load distribution are, to some degree, structurally in tension with each other.

- Sticky sessions route all requests from the same client session to the same backend instance, compensating for services that keep client-specific state in local, per-instance memory rather than an external store.
- Without sticky sessions, a stateful, non-externalized service will fragment or lose session data as requests bounce between instances under normal load-balancing.
- Sticky sessions provide consistency only as long as the assigned instance stays healthy — that instance's failure still loses whatever session state lived exclusively in its local memory.
- Externalizing session state to a shared store (Redis, a database) avoids this fragility entirely, making every instance interchangeable and is the generally preferred, more robust design for horizontally scalable services.
- Sticky sessions can undermine even load distribution over time, since long-lived sessions remain pinned to one instance for their full duration, creating a structural tension with perfectly balanced traffic.
