---
card: microservices
gi: 513
slug: stateless-services-for-scaling
title: "Stateless services for scaling"
---

## 1. What it is

A **stateless service** holds no request-specific or session-specific data in its own memory between requests — every request carries (or can retrieve from an external store) everything the service needs to handle it, so **any** instance can handle **any** request, with no requirement that a specific client's requests keep landing on the specific instance that handled their previous request. This is the property that makes [horizontal scaling](0512-horizontal-vs-vertical-scaling.md) actually work correctly, not just technically possible.

## 2. Why & when

You design services to be stateless because statefulness directly breaks the assumptions horizontal scaling and load balancing depend on:

- **A load balancer distributing requests across instances assumes any instance can handle any request.** If an instance holds state a specific request depends on (a shopping cart built up in that instance's memory, a partially-completed multi-step workflow), routing that request to a *different* instance produces incorrect behavior — the new instance simply doesn't have the state it needs.
- **"Sticky sessions" (routing a client's requests to the same instance every time) are a workaround, not a real fix**, and they undermine several benefits of horizontal scaling — an instance holding many clients' sticky state becomes harder to scale down gracefully, and losing that one instance loses every client's state that was stuck to it.
- **A stateless instance can be freely started, stopped, or replaced at any moment** without any coordination or data loss concern — this is exactly the flexibility a [rolling deployment](0450-rolling-deployment.md) or autoscaler needs to add and remove instances dynamically.
- **You design for statelessness from the very beginning of any service meant to scale horizontally** — retrofitting statelessness onto a service that's already accumulated in-memory state as a core part of its design is a substantial rework, not a quick fix.

## 3. Core concept

Think of a bank teller window versus a personal assistant who remembers your specific ongoing situation: at a stateless bank teller window, you can walk up to *any* available teller and hand them your account number and request — they look up everything they need on the spot and handle it correctly, regardless of which teller you saw last time. A stateful personal assistant, by contrast, only works correctly if you always go back to the *same* assistant, since only they remember the context of your ongoing situation — losing that one assistant means losing that context entirely.

Concretely, building a stateless service means:

1. **Session data lives externally**, not in the service's own process memory — a distributed cache or a database stores session state, keyed by a session identifier the client presents on each request, so any instance can look it up regardless of which instance handled the previous request.
2. **Each request is self-contained** — it carries (via an auth token, a session ID, or the request body itself) everything the handling instance needs, rather than depending on the instance remembering something from an earlier interaction.
3. **In-memory caches are treated as disposable, not authoritative** — a [local cache](0502-local-vs-distributed-cache.md) can still exist for performance, but the service's *correctness* never depends on that specific cache entry being present on the specific instance handling a given request.
4. **No instance is "special"** — any instance can be added, removed, or restarted at any time without special coordination, data migration, or client-visible disruption, because no instance holds anything uniquely necessary that another instance couldn't also access.

## 4. Diagram

<svg viewBox="0 0 660 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A stateless service lets a load balancer route a client's consecutive requests to different instances, each retrieving session state from an external store, with correct results either way">
  <rect x="20" y="30" width="150" height="45" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="95" y="57" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">client</text>

  <rect x="220" y="20" width="130" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="285" y="45" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">instance A</text>

  <rect x="220" y="80" width="130" height="40" rx="6" fill="#1c2430" stroke="#f0883e" stroke-width="1.5"/>
  <text x="285" y="105" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">instance B</text>

  <rect x="420" y="45" width="180" height="50" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="510" y="75" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">external session store</text>

  <line x1="170" y1="45" x2="220" y2="40" stroke="#8b949e" marker-end="url(#a1)"/>
  <text x="195" y="30" fill="#8b949e" font-size="7" font-family="sans-serif">request 1</text>
  <line x1="170" y1="55" x2="220" y2="100" stroke="#8b949e" marker-end="url(#a1)"/>
  <text x="195" y="115" fill="#8b949e" font-size="7" font-family="sans-serif">request 2</text>

  <line x1="350" y1="40" x2="420" y2="60" stroke="#6db33f" marker-end="url(#a1)"/>
  <line x1="350" y1="100" x2="420" y2="80" stroke="#6db33f" marker-end="url(#a1)"/>

  <defs>
    <marker id="a1" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#8b949e"/></marker>
  </defs>
</svg>

Two consecutive requests from the same client, routed to different instances, both correctly retrieve the same session state from the shared external store.

## 5. Runnable example

Scenario: a request handler tracking a shopping cart across requests. We start with a stateful, broken version demonstrating the problem, extend it to a stateless version storing state externally, then handle the hard case: a client's requests genuinely landing on different instances in sequence, correctly handled only by the stateless design.

### Level 1 — Basic

```java
// File: StatefulServiceBroken.java -- models the PROBLEM: an instance
// holding session state IN ITS OWN MEMORY. A request landing on a
// DIFFERENT instance than the one that built up the state FAILS.
import java.util.*;

public class StatefulServiceBroken {
    static class ServiceInstance {
        String name;
        Map<String, List<String>> inMemoryCarts = new HashMap<>(); // state lives HERE, only

        ServiceInstance(String name) { this.name = name; }

        void addToCart(String sessionId, String item) {
            inMemoryCarts.computeIfAbsent(sessionId, k -> new ArrayList<>()).add(item);
            System.out.println("[" + name + "] added '" + item + "' to session " + sessionId + "'s cart (stored LOCALLY)");
        }

        List<String> getCart(String sessionId) {
            List<String> cart = inMemoryCarts.get(sessionId);
            if (cart == null) {
                System.out.println("[" + name + "] NO cart found for session " + sessionId + " -- this instance never saw the earlier request");
                return List.of();
            }
            return cart;
        }
    }

    public static void main(String[] args) {
        ServiceInstance instanceA = new ServiceInstance("instance-A");
        ServiceInstance instanceB = new ServiceInstance("instance-B");

        String sessionId = "session-42";
        instanceA.addToCart(sessionId, "widget"); // load balancer sends request 1 to instance A

        List<String> cart = instanceB.getCart(sessionId); // load balancer sends request 2 to instance B
        System.out.println("[client] cart contents: " + cart + " -- WRONG, should show 'widget'!");
    }
}
```

How to run: `java StatefulServiceBroken.java`

`inMemoryCarts` lives entirely inside each `ServiceInstance` object's own memory — `instanceA.addToCart` writes only into `instanceA`'s own map, and when the second request happens to land on `instanceB` (simulating a load balancer routing decision), `instanceB.getCart` finds nothing at all, since `instanceB` never saw the earlier request and has no access to `instanceA`'s private in-memory state.

### Level 2 — Intermediate

```java
// File: StatelessServiceFixed.java -- the SAME cart operations, now
// STATELESS: session data lives in a SHARED, EXTERNAL store, not in any
// individual instance's own memory -- ANY instance can correctly handle
// ANY request for ANY session.
import java.util.*;

public class StatelessServiceFixed {
    // The SHARED external store -- NOT owned by any single instance.
    static Map<String, List<String>> sharedSessionStore = new HashMap<>();

    static class ServiceInstance {
        String name;
        ServiceInstance(String name) { this.name = name; }

        void addToCart(String sessionId, String item) {
            sharedSessionStore.computeIfAbsent(sessionId, k -> new ArrayList<>()).add(item);
            System.out.println("[" + name + "] added '" + item + "' to session " + sessionId + "'s cart (stored in SHARED store)");
        }

        List<String> getCart(String sessionId) {
            return sharedSessionStore.getOrDefault(sessionId, List.of());
        }
    }

    public static void main(String[] args) {
        ServiceInstance instanceA = new ServiceInstance("instance-A");
        ServiceInstance instanceB = new ServiceInstance("instance-B");

        String sessionId = "session-42";
        instanceA.addToCart(sessionId, "widget"); // request 1 -> instance A

        List<String> cart = instanceB.getCart(sessionId); // request 2 -> instance B, a DIFFERENT instance
        System.out.println("[client] cart contents: " + cart + " -- CORRECT, regardless of which instance handled which request");
    }
}
```

How to run: `java StatelessServiceFixed.java`

`sharedSessionStore` is a single map accessible to *both* `ServiceInstance` objects equally — neither instance owns it privately. `instanceA.addToCart` and `instanceB.getCart` both read and write the same underlying data, so the second request correctly finds the cart contents the first request created, entirely independent of which specific instance happened to handle each request.

### Level 3 — Advanced

```java
// File: StatelessServiceRandomRouting.java -- the SAME stateless design,
// now handling the PRODUCTION-FLAVORED hard case CORRECTLY: a client's
// requests are routed to RANDOMLY DIFFERENT instances across a MULTI-STEP
// workflow (add item, add another item, checkout), simulating a REAL
// load balancer's behavior -- and the workflow completes correctly
// regardless of the random routing, because NOTHING depends on instance
// affinity.
import java.util.*;

public class StatelessServiceRandomRouting {
    static Map<String, List<String>> sharedSessionStore = new HashMap<>();
    static List<String> allInstanceNames = List.of("instance-A", "instance-B", "instance-C");
    static Random random = new Random(7); // fixed seed for reproducible demo output

    static String pickRandomInstance() {
        return allInstanceNames.get(random.nextInt(allInstanceNames.size()));
    }

    static void addToCart(String instanceName, String sessionId, String item) {
        sharedSessionStore.computeIfAbsent(sessionId, k -> new ArrayList<>()).add(item);
        System.out.println("[load balancer -> " + instanceName + "] added '" + item + "'");
    }

    static List<String> checkout(String instanceName, String sessionId) {
        List<String> cart = sharedSessionStore.getOrDefault(sessionId, List.of());
        System.out.println("[load balancer -> " + instanceName + "] checking out cart: " + cart);
        return cart;
    }

    public static void main(String[] args) {
        String sessionId = "session-99";

        System.out.println("--- a 3-step workflow, EACH step routed to a RANDOMLY different instance ---");
        addToCart(pickRandomInstance(), sessionId, "widget");
        addToCart(pickRandomInstance(), sessionId, "gadget");
        List<String> finalCart = checkout(pickRandomInstance(), sessionId);

        System.out.println();
        System.out.println("[result] final cart: " + finalCart + " -- CORRECT and COMPLETE, despite each step hitting a different, randomly-chosen instance");
    }
}
```

How to run: `java StatelessServiceRandomRouting.java`

`pickRandomInstance` is called independently before each of the three workflow steps, simulating a real load balancer that has no reason to route a client's consecutive requests to the same instance. Because `addToCart` and `checkout` both operate exclusively on `sharedSessionStore` — never on any instance-specific state — the workflow completes correctly and the final cart contains both items, regardless of the fact that all three steps almost certainly landed on three different, randomly-selected instance names.

## 6. Walkthrough

Trace `StatelessServiceRandomRouting.main` in order. **First**, `pickRandomInstance()` is called and returns some instance name (determined by the fixed random seed) — `addToCart` runs with that instance name purely as a label for the log line, and its actual logic writes `"widget"` into `sharedSessionStore` under `"session-99"`, with no dependency on which instance name was passed in.

**Next**, `pickRandomInstance()` is called again, independently, likely returning a *different* instance name than the first call (since it's a fresh random draw each time) — `addToCart` runs again, appending `"gadget"` to the *same* `sharedSessionStore` entry for `"session-99"`, since the key used for storage (`sessionId`) has nothing to do with which instance is nominally "handling" the call.

**Then**, `pickRandomInstance()` is called a third time for the checkout step, again potentially yielding yet another different instance name — `checkout` reads `sharedSessionStore.getOrDefault("session-99", List.of())`, retrieving the full, accumulated list built by both prior steps.

**After that**, because all three operations read and wrote the identical shared data structure, keyed only by `sessionId` and never by any instance-specific identifier, the `cart` variable inside `checkout` correctly contains both `"widget"` and `"gadget"` — the complete, correct result of the whole workflow.

**Finally**, `main` prints the final cart contents, confirming both items are present and correctly accumulated — demonstrating that a genuinely stateless design produces correct results even under a load-balancing pattern that actively works against any assumption of instance affinity, which is exactly the scenario a real production load balancer creates routinely and unpredictably.

```
--- a 3-step workflow, EACH step routed to a RANDOMLY different instance ---
[load balancer -> instance-C] added 'widget'
[load balancer -> instance-A] added 'gadget'
[load balancer -> instance-B] checking out cart: [widget, gadget]

[result] final cart: [widget, gadget] -- CORRECT and COMPLETE, despite each step hitting a different, randomly-chosen instance
```

## 7. Gotchas & takeaways

> "Sticky sessions" (configuring a load balancer to always route a given client to the same instance) can mask a stateful design's correctness problems in testing and small-scale deployment, without actually fixing the underlying issue — the moment that one sticky instance restarts, scales down, or crashes, every client stuck to it loses their state entirely, and the illusion of statelessness working correctly collapses at exactly the worst possible moment.
- Statelessness is what makes [horizontal scaling](0512-horizontal-vs-vertical-scaling.md) genuinely correct, not just technically possible — a stateful service can still technically run multiple instances, but only a stateless one can have a load balancer route requests among them with correct results guaranteed.
- Externalizing state doesn't mean giving up performance — a stateless service can still use a fast [local cache](0502-local-vs-distributed-cache.md) as a non-authoritative optimization, as long as correctness never actually depends on that specific cache entry being present on the specific instance handling a given request.
- This principle directly enables [rolling deployments](0450-rolling-deployment.md) and elastic autoscaling — an orchestrator freely adding, removing, or replacing instances only works smoothly when no instance holds anything uniquely necessary that would be lost in the process.
- [Externalizing session state](0514-externalizing-session-state.md) specifically addresses the most common source of accidental statefulness in web applications — user session data — and is usually the first, most impactful step toward making an existing stateful service genuinely stateless.
