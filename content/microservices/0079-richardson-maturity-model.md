---
card: microservices
gi: 79
slug: richardson-maturity-model
title: "Richardson Maturity Model"
---

## 1. What it is

The Richardson Maturity Model, proposed by Leonard Richardson, is a four-level scale (0 through 3) for measuring how "RESTful" an HTTP API actually is, since many APIs call themselves REST while only loosely following its principles. **Level 0** is a single URI, single HTTP verb (usually `POST`), and a custom action encoded in the body — essentially RPC-over-HTTP wearing REST's clothing. **Level 1** introduces separate URIs per resource, but still uses one verb for everything. **Level 2** adds proper use of HTTP verbs and status codes for each resource. **Level 3** adds [HATEOAS](0080-hateoas-hypermedia.md) — responses include hypermedia links describing what the client can do next.

## 2. Why & when

Most production microservices APIs, in practice, target Level 2: distinct URIs per resource, correct verb and status code usage — the sweet spot that gets most of REST's practical benefits (predictability, tooling compatibility, correct retry semantics) without the added complexity of Level 3's hypermedia-driven navigation, which few HTTP client libraries handle automatically anyway. Understanding the model is valuable less as a target to maximize and more as a diagnostic: it gives a name to the gap between "an API that uses JSON over HTTP" (Level 0 or 1) and "an API that's actually using HTTP's own semantics" (Level 2), which is usually where the real payoff of calling something RESTful actually lives.

Use the model to evaluate an existing or proposed API design: is it stuck at Level 0/1 (one URI, one verb, custom action codes) when it could get real benefit from moving to Level 2? Reach for Level 3 specifically when clients genuinely benefit from discovering available actions dynamically (rare in service-to-service microservices communication, more common in APIs consumed by varied third-party clients).

## 3. Core concept

Each level adds one more REST principle on top of the previous level; most services stop deliberately at Level 2.

```
Level 0: POST /api  { "action": "getOrder", "id": 42 }        -- one URI, one verb, custom actions
Level 1: GET  /orders/42                                       -- resource URIs, but still one verb style
Level 2: GET/POST/PUT/DELETE on /orders, /orders/42            -- real verbs + real status codes
Level 3: Level 2 response body ALSO includes hypermedia links  -- HATEOAS
         { "id": 42, "links": [{"rel":"cancel","href":"/orders/42/cancel"}] }
```

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Four stacked bars representing Richardson Maturity Model levels 0 through 3, each adding one more REST principle on top of the previous level">
  <rect x="20" y="150" width="600" height="30" rx="4" fill="#1c2430" stroke="#8b949e"/>
  <text x="30" y="170" fill="#e6edf3" font-size="8" font-family="sans-serif">Level 0: single URI, single verb, custom actions in body (RPC-over-HTTP)</text>

  <rect x="20" y="110" width="600" height="30" rx="4" fill="#1c2430" stroke="#8b949e"/>
  <text x="30" y="130" fill="#e6edf3" font-size="8" font-family="sans-serif">Level 1: + resource-based URIs (still one verb style)</text>

  <rect x="20" y="70" width="600" height="30" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="30" y="90" fill="#e6edf3" font-size="8" font-family="sans-serif">Level 2: + real HTTP verbs + real status codes  &lt;- most services target this</text>

  <rect x="20" y="30" width="600" height="30" rx="4" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="30" y="50" fill="#e6edf3" font-size="8" font-family="sans-serif">Level 3: + HATEOAS hypermedia links describing available next actions</text>
</svg>

Each level is strictly additive; most production services deliberately stop at Level 2.

## 5. Runnable example

Scenario: model the same "get an order, then cancel it" interaction at three of the four maturity levels — Level 0 (RPC-style), Level 2 (proper REST), and Level 3 (adding HATEOAS links) — to make the practical differences concrete.

### Level 1 — Basic

```java
// File: MaturityLevel0.java -- ONE endpoint, ONE verb (POST), a custom
// "action" field in the body decides what actually happens.
import java.util.*;

public class MaturityLevel0 {
    static Map<Integer, String> orders = new HashMap<>(Map.of(42, "PLACED"));

    static String call(String action, int id) {
        if (action.equals("getOrder")) return "{\"id\":" + id + ",\"status\":\"" + orders.get(id) + "\"}";
        if (action.equals("cancelOrder")) { orders.put(id, "CANCELLED"); return "{\"result\":\"ok\"}"; }
        return "{\"error\":\"unknown action\"}";
    }

    public static void main(String[] args) {
        System.out.println("POST /api " + call("getOrder", 42));
        System.out.println("POST /api " + call("cancelOrder", 42));
    }
}
```

**How to run:** `javac MaturityLevel0.java && java MaturityLevel0` (JDK 17+).

Expected output:
```
POST /api {"id":42,"status":"PLACED"}
POST /api {"result":"ok"}
```

Every operation goes through the same URI and the same verb; the `action` string in the body is doing all the real work — an HTTP-aware tool can tell nothing about what this call does just from the method and path.

### Level 2 — Intermediate

```java
// File: MaturityLevel2.java -- Level 2: distinct resource URIs, real
// HTTP verbs (GET to read, POST to a sub-resource action to cancel),
// real status codes.
import java.util.*;

public class MaturityLevel2 {
    record HttpResponse(int status, String body) {}
    static Map<Integer, String> orders = new HashMap<>(Map.of(42, "PLACED"));

    static HttpResponse get(int id) {
        if (!orders.containsKey(id)) return new HttpResponse(404, "{\"error\":\"not found\"}");
        return new HttpResponse(200, "{\"id\":" + id + ",\"status\":\"" + orders.get(id) + "\"}");
    }

    static HttpResponse cancel(int id) {
        if (!orders.containsKey(id)) return new HttpResponse(404, "{\"error\":\"not found\"}");
        orders.put(id, "CANCELLED");
        return new HttpResponse(200, "{\"id\":" + id + ",\"status\":\"CANCELLED\"}");
    }

    public static void main(String[] args) {
        HttpResponse r1 = get(42);
        System.out.println("GET /orders/42 -> " + r1.status() + " " + r1.body());
        HttpResponse r2 = cancel(42);
        System.out.println("POST /orders/42/cancel -> " + r2.status() + " " + r2.body());
    }
}
```

**How to run:** `javac MaturityLevel2.java && java MaturityLevel2` (JDK 17+).

Expected output:
```
GET /orders/42 -> 200 {"id":42,"status":"PLACED"}
POST /orders/42/cancel -> 200 {"id":42,"status":"CANCELLED"}
```

### Level 3 — Advanced

```java
// File: MaturityLevel3Hateoas.java -- Level 3: the response body now
// includes HYPERMEDIA LINKS describing what actions are available NEXT,
// given the resource's current state -- a PLACED order can be cancelled;
// a CANCELLED order cannot be cancelled again, so that link disappears.
import java.util.*;

public class MaturityLevel3Hateoas {
    record Link(String rel, String href) {}
    record OrderRepresentation(int id, String status, List<Link> links) {}

    static Map<Integer, String> orders = new HashMap<>(Map.of(42, "PLACED"));

    static OrderRepresentation get(int id) {
        String status = orders.get(id);
        List<Link> links = new ArrayList<>();
        links.add(new Link("self", "/orders/" + id));
        if (status.equals("PLACED")) {
            links.add(new Link("cancel", "/orders/" + id + "/cancel")); // only available while PLACED
        }
        return new OrderRepresentation(id, status, links);
    }

    static OrderRepresentation cancel(int id) {
        orders.put(id, "CANCELLED");
        return get(id); // re-fetch: the cancel link will now be ABSENT
    }

    public static void main(String[] args) {
        OrderRepresentation before = get(42);
        System.out.println("Before cancel: status=" + before.status() + ", available actions=" + before.links());

        OrderRepresentation after = cancel(42);
        System.out.println("After cancel:  status=" + after.status() + ", available actions=" + after.links());
    }
}
```

**How to run:** `javac MaturityLevel3Hateoas.java && java MaturityLevel3Hateoas` (JDK 17+).

Expected output:
```
Before cancel: status=PLACED, available actions=[Link[rel=self, href=/orders/42], Link[rel=cancel, href=/orders/42/cancel]]
After cancel:  status=CANCELLED, available actions=[Link[rel=self, href=/orders/42]]
```

## 6. Walkthrough

1. **Level 1 (maturity Level 0)** — every interaction goes through `call(action, id)`, with `POST /api` as the only URI/verb pair that ever appears. `main` calls it twice with different `action` strings, and the printed output shows both calls sharing the identical `POST /api` prefix — the only thing distinguishing "read an order" from "cancel an order" is a string buried inside the request body.
2. **Level 2 (maturity Level 2)** — `get` and `cancel` are now genuinely separate operations, reachable via distinct URIs and verbs (`GET /orders/42` vs. `POST /orders/42/cancel`), and each returns a real HTTP status code (`200` on success, `404` if the order doesn't exist). `main` calls both in sequence, printing the verb, path, status, and body for each — an HTTP-aware tool watching this traffic could now correctly infer "a read happened, then a state-changing action happened" purely from the verbs and paths, without parsing any body.
3. **Level 3 (maturity Level 3, HATEOAS)** — `OrderRepresentation` now carries a `links` list alongside `id` and `status`. `get` always includes a `self` link, and *conditionally* includes a `cancel` link only when `status` is `"PLACED"` — the representation itself is telling the client what it's currently allowed to do next, rather than the client needing to already know, out of band, that `/orders/{id}/cancel` exists and is currently valid to call.
4. **Tracing `main`'s two calls** — `get(42)` runs first: `orders.get(42)` is `"PLACED"`, so the `if` branch adds the `cancel` link, and the printed line shows both `self` and `cancel` links present. `cancel(42)` then sets the order's status to `"CANCELLED"` and calls `get(42)` again internally to build the response representation; this time, `status.equals("PLACED")` is `false`, so the `cancel` link is *not* added — the printed line for "After cancel" shows only the `self` link remaining.
5. **What changed between the two `get` calls, concretely** — the exact same method, `get`, produced a representation with two links the first time and one link the second time, purely because the underlying resource's state changed. This is HATEOAS's central idea: a client that only ever follows the links present in the response, rather than hard-coding "call `/orders/{id}/cancel` after every order," would automatically stop attempting to cancel an already-cancelled order, because the server simply stopped offering that link.

## 7. Gotchas & takeaways

> **Gotcha:** treating Richardson Maturity Level 3 as a mandatory target for every API is a common overcorrection — HATEOAS adds real client-side complexity (clients need logic to discover and follow links dynamically, rather than hard-coding URI templates), and most HTTP client tooling doesn't do this automatically. For internal service-to-service communication where both sides are developed together, Level 2 is usually the pragmatic, sufficient target.

- The model is a diagnostic scale, not a mandatory ladder to climb to the top of — most production microservices deliberately target Level 2 and stop there.
- Level 0 (one URI, one verb, action-in-body) forfeits nearly all of HTTP's own semantics and tooling compatibility — it's REST in name only.
- Level 2 (real verbs, real status codes, resource-based URIs) is where most of REST's practical payoff — predictable retries, tooling compatibility, cacheability — actually comes from.
- Level 3 (HATEOAS) is valuable specifically when clients need to discover valid next actions dynamically based on a resource's current state — see [HATEOAS / hypermedia](0080-hateoas-hypermedia.md) for a deeper treatment.
- Use the model to evaluate a proposed or existing API's design against a common, named vocabulary — "this is Level 1, and moving to Level 2 would let our retry infrastructure work correctly" is a concrete, actionable design conversation.
