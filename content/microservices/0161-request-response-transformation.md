---
card: microservices
gi: 161
slug: request-response-transformation
title: "Request/response transformation"
---

## 1. What it is

Request/response transformation is a gateway actively rewriting a request before forwarding it to a backend, or rewriting a backend's response before returning it to the client — adding, removing, or renaming headers, reshaping the body, or adjusting the payload format — rather than passing traffic through unchanged the way a plain [reverse proxy](0159-reverse-proxy-vs-api-gateway.md) does.

## 2. Why & when

Clients and backend services don't always want or need to speak the exact same wire format: a client might send a field name convention the backend doesn't use internally, a backend's internal response might include fields that shouldn't be exposed externally, or an older client version might need a response reshaped to match an API contract the backend has since evolved past. Transformation at the gateway means neither side needs to change to accommodate the other — the backend keeps its own internal representation, the client keeps its own expected contract, and the gateway bridges the difference in exactly one place.

Reach for gateway-level transformation when the mismatch between client-facing and backend-internal representations is a genuine, structural difference — different field naming conventions, a need to strip internal-only fields from a response, or supporting multiple client API versions against one backend version. Avoid using it as a substitute for proper API design between the gateway and backend; excessive transformation logic accumulating at the edge can become its own hard-to-maintain layer of business-adjacent complexity that's arguably better addressed by fixing the underlying API mismatch.

## 3. Core concept

A transformation step sits between receiving a request (or backend response) and forwarding it onward, applying a defined mapping from the incoming shape to the outgoing shape — the gateway inspects and actively rewrites the payload, not just its routing metadata.

```java
// REQUEST transformation: client sends snake_case, backend expects camelCase
JsonNode clientBody = parse(request.body());        // { "order_id": 42, "customer_email": "a@b.com" }
JsonNode backendBody = rename(clientBody, Map.of("order_id", "orderId", "customer_email", "customerEmail"));
forwardTo(backend, backendBody);

// RESPONSE transformation: strip an internal-only field before returning to the client
JsonNode backendResponse = parse(response.body());   // { "orderId": 42, "total": 99.9, "internalWarehouseCode": "WH-7" }
JsonNode clientResponse = removeField(backendResponse, "internalWarehouseCode");
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A client request with snake_case field names is transformed at the gateway into camelCase before reaching the backend; the backend's response, which includes an internal-only field, is transformed at the gateway to strip that field before reaching the client" >
  <rect x="20" y="20" width="150" height="35" rx="4" fill="#1c2430" stroke="#79c0ff"/>
  <text x="95" y="42" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">client: order_id</text>

  <rect x="230" y="20" width="180" height="35" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="42" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">gateway: rename fields</text>

  <rect x="470" y="20" width="150" height="35" rx="4" fill="#1c2430" stroke="#79c0ff"/>
  <text x="545" y="42" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">backend: orderId</text>

  <line x1="170" y1="37" x2="228" y2="37" stroke="#8b949e" marker-end="url(#arr42)"/>
  <line x1="410" y1="37" x2="468" y2="37" stroke="#8b949e" marker-end="url(#arr42)"/>

  <rect x="470" y="110" width="150" height="35" rx="4" fill="#1c2430" stroke="#79c0ff"/>
  <text x="545" y="132" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">backend: +internal field</text>

  <rect x="230" y="110" width="180" height="35" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="132" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">gateway: strip field</text>

  <rect x="20" y="110" width="150" height="35" rx="4" fill="#1c2430" stroke="#79c0ff"/>
  <text x="95" y="132" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">client: clean response</text>

  <line x1="468" y1="127" x2="412" y2="127" stroke="#8b949e" marker-end="url(#arr42)"/>
  <line x1="228" y1="127" x2="172" y2="127" stroke="#8b949e" marker-end="url(#arr42)"/>

  <defs>
    <marker id="arr42" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

The gateway actively reshapes both directions, letting client and backend keep their own preferred formats.

## 5. Runnable example

Scenario: a request/response pair that starts by forcing the client's field naming convention directly onto the backend (showing the coupling that results), introduces gateway-level request and response transformation to decouple the two, and finally adds version-aware response transformation so two different client API versions can both be served correctly from one unchanged backend response shape.

### Level 1 — Basic

```java
// File: NoTransformationForcedCoupling.java -- the backend is forced to accept
// the client's EXACT field naming convention -- no gateway transformation exists.
import java.util.*;

public class NoTransformationForcedCoupling {
    public static void main(String[] args) {
        // client sends snake_case; backend, having NO transformation layer, must accept it AS-IS
        Map<String, Object> clientRequest = Map.of("order_id", 42, "customer_email", "alice@example.com");
        System.out.println("Backend forced to parse client's OWN naming convention directly: " + clientRequest);
        System.out.println("If the backend's internal convention is camelCase, EVERY backend endpoint duplicates this awkward mapping itself, or worse, just adopts snake_case internally to match the client.");
    }
}
```

**How to run:** `javac NoTransformationForcedCoupling.java && java NoTransformationForcedCoupling` (JDK 17+).

### Level 2 — Intermediate

```java
// File: GatewayTransformsBothDirections.java -- the gateway rewrites the REQUEST
// on the way in and the RESPONSE on the way out, decoupling client and backend conventions.
import java.util.*;

public class GatewayTransformsBothDirections {
    static Map<String, Object> renameKeys(Map<String, Object> input, Map<String, String> renameMap) {
        Map<String, Object> output = new LinkedHashMap<>();
        for (var entry : input.entrySet()) {
            String newKey = renameMap.getOrDefault(entry.getKey(), entry.getKey());
            output.put(newKey, entry.getValue());
        }
        return output;
    }

    static Map<String, Object> removeKeys(Map<String, Object> input, Set<String> keysToRemove) {
        Map<String, Object> output = new LinkedHashMap<>(input);
        keysToRemove.forEach(output::remove);
        return output;
    }

    public static void main(String[] args) {
        // REQUEST transformation: client's snake_case -> backend's camelCase
        Map<String, Object> clientRequest = Map.of("order_id", 42, "customer_email", "alice@example.com");
        Map<String, Object> backendRequest = renameKeys(clientRequest, Map.of("order_id", "orderId", "customer_email", "customerEmail"));
        System.out.println("[gateway, request] client sent: " + clientRequest);
        System.out.println("[gateway, request] backend receives: " + backendRequest);

        // RESPONSE transformation: strip an internal-only field before returning to the client
        Map<String, Object> backendResponse = new LinkedHashMap<>(Map.of("orderId", 42, "total", 99.90, "internalWarehouseCode", "WH-7"));
        Map<String, Object> clientResponse = removeKeys(backendResponse, Set.of("internalWarehouseCode"));
        System.out.println("[gateway, response] backend returned: " + backendResponse);
        System.out.println("[gateway, response] client receives: " + clientResponse);
    }
}
```

**How to run:** `javac GatewayTransformsBothDirections.java && java GatewayTransformsBothDirections` (JDK 17+).

Expected output:
```
[gateway, request] client sent: {order_id=42, customer_email=alice@example.com}
[gateway, request] backend receives: {orderId=42, customerEmail=alice@example.com}
[gateway, response] backend returned: {orderId=42, total=99.9, internalWarehouseCode=WH-7}
[gateway, response] client receives: {orderId=42, total=99.9}
```

Neither the client nor the backend had to change its own preferred format — the gateway's transformation step bridged the difference in both directions.

### Level 3 — Advanced

```java
// File: VersionAwareResponseTransformation.java -- ONE backend response shape,
// transformed DIFFERENTLY depending on which client API version made the request.
import java.util.*;

public class VersionAwareResponseTransformation {
    // the backend's response NEVER changes -- it always returns its current, full shape
    static Map<String, Object> currentBackendResponse() {
        Map<String, Object> response = new LinkedHashMap<>();
        response.put("orderId", 42);
        response.put("status", "PLACED");           // v2 clients expect this field name
        response.put("total", 99.90);
        response.put("currency", "USD");             // a field added AFTER v1 clients were built
        return response;
    }

    // v1 clients expect the OLD field name "state" instead of "status", and never heard of "currency"
    static Map<String, Object> transformForV1(Map<String, Object> backendResponse) {
        Map<String, Object> v1Response = new LinkedHashMap<>();
        v1Response.put("orderId", backendResponse.get("orderId"));
        v1Response.put("state", backendResponse.get("status")); // RENAMED for old clients
        v1Response.put("total", backendResponse.get("total"));
        // "currency" INTENTIONALLY omitted -- v1 clients don't know how to handle it
        return v1Response;
    }

    // v2 clients get the CURRENT shape, unchanged
    static Map<String, Object> transformForV2(Map<String, Object> backendResponse) {
        return backendResponse; // no transformation needed -- backend shape already matches v2's contract
    }

    public static void main(String[] args) {
        Map<String, Object> backendResponse = currentBackendResponse();

        Map<String, Object> responseForV1Client = transformForV1(backendResponse);
        Map<String, Object> responseForV2Client = transformForV2(backendResponse);

        System.out.println("Backend's ACTUAL response (unchanged, ONE shape): " + backendResponse);
        System.out.println("What a v1 client receives: " + responseForV1Client);
        System.out.println("What a v2 client receives: " + responseForV2Client);
        System.out.println("The backend never had to maintain TWO response formats -- the gateway's version-aware transformation did that work.");
    }
}
```

**How to run:** `javac VersionAwareResponseTransformation.java && java VersionAwareResponseTransformation` (JDK 17+).

Expected output:
```
Backend's ACTUAL response (unchanged, ONE shape): {orderId=42, status=PLACED, total=99.9, currency=USD}
What a v1 client receives: {orderId=42, state=PLACED, total=99.9}
What a v2 client receives: {orderId=42, status=PLACED, total=99.9, currency=USD}
The backend never had to maintain TWO response formats -- the gateway's version-aware transformation did that work.
```

## 6. Walkthrough

1. **Level 1** — `clientRequest` uses `order_id` and `customer_email` directly, and the printed comment makes explicit the two bad options this forces on the backend: either duplicate an awkward field-mapping step inside every single endpoint, or abandon its own preferred naming convention entirely just to match the client.
2. **Level 2, request transformation** — `renameKeys` builds a new map, substituting each key found in `renameMap` for its backend-preferred equivalent while leaving unlisted keys unchanged; `backendRequest`'s printed content shows `orderId` and `customerEmail` in place of the client's original `order_id` and `customer_email`.
3. **Level 2, response transformation** — `removeKeys` builds a new map excluding any key present in `keysToRemove`; `clientResponse` is missing `internalWarehouseCode`, which was present in `backendResponse`, demonstrating the gateway stripping a field the client should never see.
4. **Level 2, both directions decoupled** — neither `clientRequest`'s original shape nor `backendResponse`'s original shape needed to change to produce the correctly-transformed `backendRequest` and `clientResponse` — the gateway's two transformation functions did all the reconciling work.
5. **Level 3, one backend response, no per-version logic inside the backend** — `currentBackendResponse` always returns the identical, current-shape map regardless of who's asking; the backend has no awareness that different client versions even exist.
6. **Level 3, two distinct transformation functions per version** — `transformForV1` explicitly renames `status` to `state` (matching an older client contract) and omits the newer `currency` field entirely, while `transformForV2` is effectively a pass-through, since the backend's current shape already matches what v2 clients expect.
7. **Level 3, the payoff observed directly** — printing `backendResponse`, `responseForV1Client`, and `responseForV2Client` side by side shows one single backend shape producing two genuinely different client-facing results, entirely through gateway-side transformation logic, meaning the backend was able to evolve its response shape (adding `currency`, renaming internally) without needing to maintain backward-compatible response formats itself — that burden moved to the gateway's transformation layer, in exactly one place.

## 7. Gotchas & takeaways

> **Gotcha:** transformation logic accumulating at the gateway for many client versions, many field-renaming rules, and many stripped-field policies can itself become a substantial, hard-to-test, business-adjacent codebase living outside normal service ownership boundaries — treat gateway transformation as a deliberate, actively-maintained layer with its own tests and ownership, not an informal place to quietly patch over API mismatches indefinitely.

- Request/response transformation lets a gateway actively rewrite payloads in both directions, decoupling the client-facing contract from the backend's own internal representation.
- This avoids forcing either side to adopt the other's naming conventions or exposing internal-only fields externally, bridging the difference in exactly one place.
- Version-aware response transformation lets one backend response shape correctly serve multiple client API versions simultaneously, without the backend itself maintaining multiple response formats.
- Reach for gateway transformation for genuine structural mismatches between client and backend contracts; avoid using it as an informal patch for API design problems that would be better solved directly.
- Transformation logic accumulating unmanaged at the edge becomes its own maintenance burden — it deserves the same ownership and testing discipline as any other significant piece of application logic.
