---
card: microservices
gi: 92
slug: grpc-vs-rest-trade-offs
title: "gRPC vs REST trade-offs"
---

## 1. What it is

Choosing between gRPC and REST for a given service boundary is a genuine engineering trade-off, not a strictly-better-or-worse comparison. REST over HTTP/1.1 with JSON favors broad compatibility, human-readability, and tooling ubiquity; gRPC over HTTP/2 with Protobuf favors performance (smaller payloads, multiplexed connections), strongly-typed generated contracts, and native streaming. Neither dominates the other across every dimension — the right choice depends on who's consuming the API and what the interaction actually needs.

## 2. Why & when

A public API consumed by unknown third parties, browsers, or partners with varying tech stacks benefits enormously from REST's near-universal tooling support — any language, `curl`, a browser's dev tools, can inspect and call a REST/JSON endpoint with zero special setup. An internal, high-throughput service-to-service call between two services you control benefits far more from gRPC's compactness and speed, since both sides can regenerate matching client/server code from a shared `.proto` file without needing REST's broader (but here unnecessary) compatibility guarantees.

Choose REST for public APIs, browser-facing APIs (without extra tooling like gRPC-Web), and anywhere debuggability and broad client compatibility matter most. Choose gRPC for internal service-to-service calls where performance genuinely matters, where streaming is needed, or where strongly-typed cross-language contracts are valuable enough to justify the added `.proto`/codegen tooling. Many real systems use both: REST at the public edge, gRPC internally between services — see [API Gateway & Edge](0079-richardson-maturity-model.md)'s broader context for how an edge layer can translate between the two.

## 3. Core concept

The two approaches differ along several independent axes; a real decision weighs which axes matter most for the specific boundary being designed.

```
Axis                    REST/JSON                    gRPC/Protobuf
----                    ---------                    -------------
Payload format          text, self-describing         binary, schema-required
Payload size             larger                        smaller
Browser support           native                        needs gRPC-Web proxy
Human debuggability       curl, browser devtools        needs specialized tooling
Streaming                 not native (needs WebSocket)  native (4 call shapes)
Contract                  loose (OpenAPI optional)      strict (.proto required)
Tooling ubiquity           near-universal                growing, but less universal
```

## 4. Diagram

<svg viewBox="0 0 640 180" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A system uses REST at its public-facing edge for broad compatibility, and gRPC internally between its own services for performance and strong typing">
  <rect x="20" y="20" width="140" height="140" rx="6" fill="#1c2430" stroke="#8b949e"/>
  <text x="90" y="45" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">External clients</text>
  <text x="90" y="65" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">browsers, partners</text>

  <rect x="220" y="20" width="140" height="140" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="290" y="45" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">API Gateway</text>
  <text x="290" y="65" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">REST/JSON facing out</text>

  <rect x="420" y="20" width="200" height="60" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="520" y="45" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">OrderService (gRPC)</text>
  <rect x="420" y="100" width="200" height="60" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="520" y="125" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">InventoryService (gRPC)</text>

  <line x1="160" y1="90" x2="220" y2="90" stroke="#8b949e" stroke-width="1.5"/>
  <line x1="360" y1="70" x2="420" y2="50" stroke="#6db33f" stroke-width="1.5"/>
  <line x1="360" y1="110" x2="420" y2="130" stroke="#6db33f" stroke-width="1.5"/>
</svg>

REST at the public edge; gRPC internally, where both endpoints are under your own control.

## 5. Runnable example

Scenario: an `OrderService` exposed two ways — first purely as REST/JSON to make the format-verbosity difference concrete, then purely as gRPC-style binary/tagged encoding to compare payload size directly, then extended to model a realistic hybrid architecture where an API gateway translates an incoming REST request into an internal gRPC-style call, giving external clients REST while internal services use the more compact protocol.

### Level 1 — Basic

```java
// File: RestOnlyOrderService.java -- expose Order data as REST/JSON --
// self-describing, larger payload.
public class RestOnlyOrderService {
    record Order(int id, String status, double total) {}

    static String toJson(Order order) {
        return "{\"id\":" + order.id() + ",\"status\":\"" + order.status() + "\",\"total\":" + order.total() + "}";
    }

    public static void main(String[] args) {
        Order order = new Order(42, "PLACED", 19.99);
        String json = toJson(order);
        System.out.println("REST/JSON response: " + json);
        System.out.println("Payload size: " + json.getBytes().length + " bytes");
    }
}
```

**How to run:** `javac RestOnlyOrderService.java && java RestOnlyOrderService` (JDK 17+).

Expected output:
```
REST/JSON response: {"id":42,"status":"PLACED","total":19.99}
Payload size: 41 bytes
```

### Level 2 — Intermediate

```java
// File: GrpcOnlyOrderService.java -- the SAME Order, exposed gRPC-style
// (Protobuf-tagged binary) -- schema-based, smaller payload.
import java.util.*;

public class GrpcOnlyOrderService {
    record Order(int id, String status, double total) {}
    static Map<String, Integer> schemaTags = Map.of("id", 1, "status", 2, "total", 3);

    static byte[] toGrpcWire(Order order) {
        String wire = "[" + schemaTags.get("id") + ":" + order.id() + "]"
                + "[" + schemaTags.get("status") + ":" + order.status() + "]"
                + "[" + schemaTags.get("total") + ":" + order.total() + "]";
        return wire.getBytes();
    }

    public static void main(String[] args) {
        Order order = new Order(42, "PLACED", 19.99);
        byte[] wire = toGrpcWire(order);
        System.out.println("gRPC (simulated) response: " + new String(wire));
        System.out.println("Payload size: " + wire.length + " bytes (requires the shared schema to decode)");
    }
}
```

**How to run:** `javac GrpcOnlyOrderService.java && java GrpcOnlyOrderService` (JDK 17+).

Expected output:
```
gRPC (simulated) response: [1:42][2:PLACED][3:19.99]
Payload size: 25 bytes (requires the shared schema to decode)
```

### Level 3 — Advanced

```java
// File: HybridGatewayTranslation.java -- a REALISTIC hybrid: external
// clients call REST/JSON against an API GATEWAY, which translates the
// call into the internal gRPC-style format before forwarding it to
// OrderService -- external simplicity, internal efficiency.
import java.util.*;

public class HybridGatewayTranslation {
    record Order(int id, String status, double total) {}
    static Map<String, Integer> schemaTags = Map.of("id", 1, "status", 2, "total", 3);
    static Map<Integer, Order> internalOrders = Map.of(42, new Order(42, "PLACED", 19.99));

    // INTERNAL service -- speaks only the compact gRPC-style format
    static byte[] orderServiceGetOrder(int id) {
        Order order = internalOrders.get(id);
        String wire = "[" + schemaTags.get("id") + ":" + order.id() + "]"
                + "[" + schemaTags.get("status") + ":" + order.status() + "]"
                + "[" + schemaTags.get("total") + ":" + order.total() + "]";
        return wire.getBytes();
    }

    // API GATEWAY -- speaks REST/JSON to external clients, TRANSLATES to/from the internal format
    static String apiGatewayHandleGetOrder(int id) {
        byte[] internalWire = orderServiceGetOrder(id); // call the INTERNAL gRPC-style service
        String decoded = new String(internalWire);
        // parse the simple tagged format back into named fields (the gateway KNOWS the internal schema)
        String[] parts = decoded.replace("]", "").split("\\[");
        Map<Integer, String> byTag = new HashMap<>();
        for (String p : parts) { if (p.isEmpty()) continue; String[] kv = p.split(":", 2); byTag.put(Integer.parseInt(kv[0]), kv[1]); }
        return "{\"id\":" + byTag.get(1) + ",\"status\":\"" + byTag.get(2) + "\",\"total\":" + byTag.get(3) + "}"; // REST/JSON out
    }

    public static void main(String[] args) {
        System.out.println("External client calls: GET /orders/42 (REST/JSON)");
        String restResponse = apiGatewayHandleGetOrder(42);
        System.out.println("Gateway response to external client: " + restResponse);
        System.out.println("(internally, the gateway called OrderService via the compact gRPC-style wire format)");
    }
}
```

**How to run:** `javac HybridGatewayTranslation.java && java HybridGatewayTranslation` (JDK 17+).

Expected output:
```
External client calls: GET /orders/42 (REST/JSON)
Gateway response to external client: {"id":42,"status":"PLACED","total":19.99}
(internally, the gateway called OrderService via the compact gRPC-style wire format)
```

## 6. Walkthrough

1. **Level 1** — `toJson` builds a self-describing JSON string with every field name spelled out. `main` prints the JSON and its byte length (41 bytes) — this is what a REST-exposed `OrderService` would return directly to any HTTP client, readable by a human or any HTTP-aware tool with zero prior schema knowledge.
2. **Level 2 — the same data, gRPC-style** — `toGrpcWire` uses `schemaTags` (standing in for a shared `.proto` definition) to encode only tag numbers and values, no field names. `main` prints the resulting compact representation (25 bytes) — smaller, but meaningless to a reader (or tool) that doesn't already have the shared schema to decode the numeric tags back into field names.
3. **Level 3 — a realistic hybrid architecture** — `orderServiceGetOrder` represents the *internal* service, speaking only the compact, schema-based format from Level 2. `apiGatewayHandleGetOrder` represents an *API gateway* sitting between external clients and that internal service: it calls `orderServiceGetOrder` to get the compact internal representation, then explicitly parses the tagged wire format back into named fields (using its own knowledge of the shared internal schema — `byTag.get(1)` is `id`, `byTag.get(2)` is `status`, and so on) and reconstructs a REST/JSON response for the external caller.
4. **Tracing `main`'s call** — `main` prints a line simulating an external client's request (`GET /orders/42`), then calls `apiGatewayHandleGetOrder(42)`. Internally, this first calls `orderServiceGetOrder(42)`, which looks up order 42 in `internalOrders` and returns its compact wire encoding — this internal call never touches JSON at all. `apiGatewayHandleGetOrder` then decodes that wire format, rebuilds a `Map<Integer, String>` keyed by tag number, and uses it to construct the final JSON string returned to `main`, which prints it as the gateway's response to the external client.
5. **What this demonstrates about real hybrid systems** — the external caller in this scenario only ever sees REST/JSON — simple, debuggable, broadly compatible — while the actual `OrderService` behind the gateway only ever speaks the more compact, schema-based format internally, benefiting from gRPC's efficiency for calls that happen entirely within the system's own trusted boundary. This is exactly the common real-world pattern: an [API gateway](0079-richardson-maturity-model.md) at the edge translating between an external-facing protocol and internal, performance-optimized service-to-service communication.

## 7. Gotchas & takeaways

> **Gotcha:** picking gRPC purely because it's "faster" for a service boundary that's actually consumed by browsers or arbitrary external partners adds real friction (browsers need a gRPC-Web proxy layer; partners need generated client stubs in their own language) without the payoff being worth it for typical API call volumes. Payload size differences that matter enormously at high internal throughput are often negligible for a public API's actual traffic patterns.

- Neither REST nor gRPC is strictly better — the right choice depends on who consumes the API (broad, uncontrolled external clients favor REST; controlled internal services favor gRPC) and what the interaction needs (simple request/response favors either; genuine streaming favors gRPC).
- A hybrid architecture — REST at the public edge, gRPC internally, translated by an API gateway — is a common, pragmatic pattern that gets the benefits of both without forcing one format's tradeoffs onto every consumer.
- gRPC's payload and speed advantages compound significantly at high internal call volumes; they matter far less for typical external API traffic.
- REST's debuggability (readable payloads, works with `curl` and browser dev tools with zero setup) is a real, ongoing operational benefit that shouldn't be dismissed in the pursuit of raw performance.
- See [RESTful APIs over HTTP](0076-restful-apis-over-http.md) and [gRPC and HTTP/2](0089-grpc-and-http-2.md) for the deeper mechanics behind each side of this comparison.
