---
card: microservices
gi: 77
slug: resource-modeling-uris
title: "Resource modeling & URIs"
---

## 1. What it is

Resource modeling is the design step of deciding what the *nouns* in a RESTful API are — orders, customers, shipments — and how their URIs express both individual resources and relationships between them. A well-modeled API uses plural nouns for collections (`/orders`), a path segment for a specific item within that collection (`/orders/42`), and nesting to express ownership or containment (`/orders/42/items`), while deliberately avoiding verbs in the URI itself, since the HTTP verb already carries the action (see [RESTful APIs over HTTP](0076-restful-apis-over-http.md)).

## 2. Why & when

A URI scheme that mixes verbs into the path (`/getOrder?id=42`, `/deleteOrder/42`) duplicates information the HTTP verb already provides, and produces an API where every endpoint needs its own bespoke documentation to understand. A well-modeled, noun-based URI scheme is instead largely self-describing and predictable: once a client knows `/orders/42` returns an order, `/orders/42/items` returning that order's line items is exactly what any RESTful-API-literate developer would expect, without needing to look it up. This predictability compounds across a whole API — a consistent resource model means new endpoints require far less onboarding for every consumer.

Invest time in resource modeling at the start of designing any service's public API — retrofitting a consistent noun-based scheme onto an API that's already shipped a verb-heavy, ad-hoc URI scheme means a breaking change for every existing client.

## 3. Core concept

Collections are plural nouns; a specific item is identified by appending its id; nested resources express ownership by nesting further path segments — the verb never appears in the URI.

```
/orders                 -> the collection of all orders
/orders/42               -> one specific order
/orders/42/items         -> the collection of items belonging to order 42
/orders/42/items/7       -> one specific item within order 42

WRONG:  /getOrder/42, /deleteOrderItem?orderId=42&itemId=7   <- verbs baked into the URI
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A tree diagram showing the orders collection containing order 42, which in turn contains an items collection with item 7 nested inside">
  <rect x="20" y="60" width="100" height="40" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="70" y="84" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">/orders</text>

  <rect x="200" y="60" width="110" height="40" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="255" y="84" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">/orders/42</text>

  <rect x="390" y="60" width="130" height="40" rx="5" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="455" y="84" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">/orders/42/items</text>

  <rect x="390" y="120" width="160" height="40" rx="5" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="470" y="144" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">/orders/42/items/7</text>

  <line x1="120" y1="80" x2="200" y2="80" stroke="#8b949e" stroke-width="1.5"/>
  <line x1="310" y1="80" x2="390" y2="80" stroke="#8b949e" stroke-width="1.5"/>
  <line x1="455" y1="100" x2="470" y2="120" stroke="#8b949e" stroke-width="1.5"/>
</svg>

Nesting expresses containment: items belong to a specific order, and one item belongs to that items collection.

## 5. Runnable example

Scenario: an order-and-items API, first with a verb-and-query-parameter URI scheme, then remodeled to a clean noun-based, nested scheme, then extended to correctly distinguish a collection URI from an item URI when routing.

### Level 1 — Basic

```java
// File: VerbBasedUris.java -- URIs bake the ACTION into the path/query,
// duplicating what the HTTP verb should already express.
import java.util.*;

public class VerbBasedUris {
    public static void main(String[] args) {
        List<String> uris = List.of(
            "/getOrder?id=42",
            "/deleteOrder?id=42",
            "/getOrderItem?orderId=42&itemId=7",
            "/createOrderItem?orderId=42"
        );
        for (String uri : uris) System.out.println(uri);
    }
}
```

**How to run:** `javac VerbBasedUris.java && java VerbBasedUris` (JDK 17+).

Expected output:
```
/getOrder?id=42
/deleteOrder?id=42
/getOrderItem?orderId=42&itemId=7
/createOrderItem?orderId=42
```

Each of these four operations needs its own name memorized — nothing about the URI shape itself hints at how the four relate to each other as one resource hierarchy.

### Level 2 — Intermediate

```java
// File: NounBasedUris.java -- SAME four operations, remodeled as a
// resource hierarchy: verbs come from the HTTP method (modeled here as a
// paired string), never from the path.
import java.util.*;

public class NounBasedUris {
    record ApiCall(String method, String uri) {}

    public static void main(String[] args) {
        List<ApiCall> calls = List.of(
            new ApiCall("GET", "/orders/42"),
            new ApiCall("DELETE", "/orders/42"),
            new ApiCall("GET", "/orders/42/items/7"),
            new ApiCall("POST", "/orders/42/items")
        );
        for (ApiCall c : calls) System.out.println(c.method() + " " + c.uri());
    }
}
```

**How to run:** `javac NounBasedUris.java && java NounBasedUris` (JDK 17+).

Expected output:
```
GET /orders/42
DELETE /orders/42
GET /orders/42/items/7
POST /orders/42/items
```

The URI shape alone now tells a reader the resource hierarchy — items belong to orders — while the verb (a separate field, matching how HTTP separates method from path) says what to do with it.

### Level 3 — Advanced

```java
// File: RoutingCollectionVsItem.java -- a router that correctly
// distinguishes a COLLECTION uri (/orders/42/items) from an ITEM uri
// (/orders/42/items/7) by segment count -- a common real-world routing need.
import java.util.*;

public class RoutingCollectionVsItem {
    static String describe(String uri) {
        String[] segments = uri.split("/");
        // segments[0] is empty (leading slash); count meaningful segments
        List<String> parts = new ArrayList<>();
        for (String s : segments) if (!s.isEmpty()) parts.add(s);

        if (parts.size() == 2 && parts.get(0).equals("orders")) {
            return "single order resource, id=" + parts.get(1);
        }
        if (parts.size() == 3 && parts.get(0).equals("orders") && parts.get(2).equals("items")) {
            return "items COLLECTION for order " + parts.get(1);
        }
        if (parts.size() == 4 && parts.get(0).equals("orders") && parts.get(2).equals("items")) {
            return "single item resource, order=" + parts.get(1) + " item=" + parts.get(3);
        }
        return "unrecognized resource path";
    }

    public static void main(String[] args) {
        List<String> uris = List.of("/orders/42", "/orders/42/items", "/orders/42/items/7", "/orders/42/shipping/label");
        for (String uri : uris) System.out.println(uri + " -> " + describe(uri));
    }
}
```

**How to run:** `javac RoutingCollectionVsItem.java && java RoutingCollectionVsItem` (JDK 17+).

Expected output:
```
/orders/42 -> single order resource, id=42
/orders/42/items -> items COLLECTION for order 42
/orders/42/items/7 -> single item resource, order=42 item=7
/orders/42/shipping/label -> unrecognized resource path
```

## 6. Walkthrough

1. **Level 1** — four strings encode four distinct operations entirely through their name and query parameters — `getOrder`, `deleteOrder`, `getOrderItem`, `createOrderItem`. Nothing about `/getOrderItem?orderId=42&itemId=7`'s shape tells a reader that items belong to orders; that relationship exists only in the endpoint's name, memorized separately.
2. **Level 2 — remodeling as a resource hierarchy** — `ApiCall` pairs an HTTP method with a noun-based, nested URI. `GET /orders/42` reads one order; `DELETE /orders/42` removes it — same resource, different verb. `GET /orders/42/items/7` and `POST /orders/42/items` both live under `/orders/42/items`, with the trailing `/7` present only when addressing one specific item — exactly mirroring the [core concept](#3-core-concept)'s collection-vs-item distinction.
3. **Level 3 — routing on the resulting shape** — `describe` splits a URI into non-empty segments and inspects both the segment *count* and specific segment values to classify the path. Two segments (`orders`, `42`) means a single order resource. Three segments ending in `items` means the items *collection* for that order — the request would return a list. Four segments ending in an id after `items` means one specific item within that collection.
4. **Tracing the four sample calls** — `/orders/42` has 2 parts, matches the first branch, and returns `"single order resource, id=42"`. `/orders/42/items` has 3 parts with the last being `"items"`, matching the second branch, returning the collection description. `/orders/42/items/7` has 4 parts with the third being `"items"`, matching the third branch and correctly extracting both `order=42` and `item=7`. `/orders/42/shipping/label` has 4 parts, but its third segment is `"shipping"`, not `"items"` — it matches none of the specific branches and falls through to `"unrecognized resource path"`, demonstrating that the routing logic is genuinely checking the resource *shape*, not just counting segments blindly.
5. **Why this distinction matters in a real service** — a real Spring `@RestController` uses `@GetMapping("/orders/{id}/items")` versus `@GetMapping("/orders/{id}/items/{itemId}")` to achieve exactly this same collection-vs-item routing, and getting the resource model right up front (as this exercise does deliberately) is what makes those mapping annotations read naturally instead of needing awkward disambiguation logic bolted on later.

## 7. Gotchas & takeaways

> **Gotcha:** a URI that looks noun-based but still smuggles an action into a path segment — `/orders/42/cancel` — is a common, pragmatic compromise (not every state change maps cleanly to a REST verb), but it should be a deliberate, minority exception, not the general pattern. Overusing action-suffixed URIs erodes the predictability a resource-based model is meant to provide.

- Collections are plural nouns (`/orders`); a specific item appends its identifier (`/orders/42`); nesting expresses ownership (`/orders/42/items`).
- The HTTP verb, not the URI path, is what expresses the action — see [HTTP verbs & status code semantics](0078-http-verbs-status-code-semantics.md).
- A consistent, predictable resource model reduces the documentation and onboarding burden for every consumer of the API, since the URI shape itself communicates the relationship between resources.
- Design the resource model before the API ships — changing URI shapes afterward is a breaking change for every existing client.
- Segment count and structure (as `RoutingCollectionVsItem` shows) is exactly what real web frameworks use under the hood to route collection requests differently from single-item requests.
