---
card: spring-integration
gi: 76
slug: graphql-support
title: "GraphQL support"
---

## 1. What it is

GraphQL support (`GraphQl.outboundGateway(...)`) lets a flow execute a GraphQL query, mutation, or subscription against a GraphQL service and receive the typed result back as a message, using Spring's `ExecutionGraphQlService` abstraction under the hood. Unlike the HTTP support adapter (card 0054), which sends a message as a generic HTTP request/response, the GraphQL outbound gateway understands GraphQL's request shape (an operation plus variables) and its typed, potentially partial response shape (data plus errors), rather than treating the body as opaque text.

## 2. Why & when

You reach for GraphQL support when the integration point is specifically a GraphQL API and the flow benefits from GraphQL's structured request/response model rather than a raw HTTP call:

- **A downstream or partner service exposes a GraphQL API as its primary interface** — calling it through the GraphQL outbound gateway means the flow works with GraphQL's operation/variables/data/errors structure directly, rather than manually building and parsing JSON bodies the way a raw HTTP outbound gateway would require.
- **A single request needs to fetch exactly the fields required, no more and no less** — GraphQL's field-selection model lets a flow request only what it actually uses from a large, complex downstream schema, avoiding the over-fetching that calling a fixed REST resource often causes.
- **Partial success needs first-class handling** — a GraphQL response can return both `data` (partially populated) and `errors` (per-field failures) in the same response; a flow reading through a GraphQL-aware gateway can inspect both parts explicitly rather than only being able to tell "it worked" or "it failed" the way a plain HTTP status code communicates.

## 3. Core concept

Think of a REST call as ordering a fixed combo meal from a menu — you get exactly what's on the combo, whether you wanted all of it or not. A GraphQL call is like handing the kitchen a custom order form listing precisely which ingredients you want from a large shared pantry (the schema); the kitchen returns exactly those ingredients, and if one particular ingredient couldn't be prepared, it tells you specifically which one failed while still handing over everything else that succeeded — a mix of partial data and specific errors, not an all-or-nothing response.

```java
@Bean
public IntegrationFlow graphQlOutboundFlow(ExecutionGraphQlService graphQlService) {
    return IntegrationFlow.from("productLookupRequests")
        .handle(GraphQl.outboundGateway(graphQlService)
            .query("""
                query($id: ID!) {
                  product(id: $id) { name price stock }
                }
                """)
            .variablesFunction(msg -> Map.of("id", msg.getHeaders().get("productId"))))
        .get();
}
```

Every message on `productLookupRequests` executes the same GraphQL query with a different `id` variable drawn from the message's headers, requesting exactly the three fields the flow needs.

## 4. Diagram

<svg viewBox="0 0 640 160" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A GraphQL outbound gateway sends an operation with variables and receives a response containing both data and per-field errors, unlike a REST call's fixed all-or-nothing response shape" >
  <rect x="20" y="20" width="280" height="120" rx="8" fill="#0d1117" stroke="#8b949e" stroke-width="1.5"/>
  <text x="160" y="12" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">REST call</text>
  <text x="35" y="45" fill="#e6edf3" font-size="8" font-family="monospace">GET /products/42</text>
  <text x="35" y="70" fill="#6db33f" font-size="8" font-family="monospace">200: full fixed shape</text>
  <text x="35" y="90" fill="#8b949e" font-size="8" font-family="monospace">or 4xx/5xx: nothing usable</text>

  <rect x="340" y="20" width="280" height="120" rx="8" fill="#0d1117" stroke="#6db33f" stroke-width="1.5"/>
  <text x="480" y="12" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">GraphQL call</text>
  <text x="355" y="42" fill="#e6edf3" font-size="8" font-family="monospace">query { product(id:42){ name price stock } }</text>
  <text x="355" y="68" fill="#79c0ff" font-size="8" font-family="monospace">data: { name, price, stock: null }</text>
  <text x="355" y="88" fill="#79c0ff" font-size="8" font-family="monospace">errors: [ "stock lookup failed" ]</text>
  <text x="355" y="110" fill="#8b949e" font-size="7" font-family="sans-serif">partial success expressed explicitly</text>
</svg>

GraphQL's response can be partially successful and say exactly which field failed — REST's response is typically all-or-nothing.

## 5. Runnable example

The scenario: fetching product details where one field may fail independently of the others, simulated with a plain in-memory record standing in for a GraphQL response's data/errors split (no real GraphQL server needed to demonstrate the partial-success handling logic), starting with a basic full-success query, then adding handling for a partial failure, then adding a retry specifically for the failed field without re-fetching fields that already succeeded.

### Level 1 — Basic

```java
// GraphQlOutboundDemo.java
import java.util.*;

public class GraphQlOutboundDemo {
    record GraphQlResult(Map<String, Object> data, List<String> errors) {}

    // Stand-in for GraphQl.outboundGateway's execution against a service.
    static GraphQlResult executeProductQuery(String productId) {
        Map<String, Object> data = new LinkedHashMap<>();
        data.put("name", "Widget");
        data.put("price", 19.99);
        data.put("stock", 42);
        return new GraphQlResult(data, List.of());
    }

    public static void main(String[] args) {
        GraphQlResult result = executeProductQuery("42");
        System.out.println("data: " + result.data());
        System.out.println("errors: " + result.errors());
    }
}
```

How to run: `java GraphQlOutboundDemo.java`. Expected output: `data: {name=Widget, price=19.99, stock=42}` then `errors: []` — a fully successful query, every requested field populated.

### Level 2 — Intermediate

```java
// GraphQlOutboundDemo.java
import java.util.*;

public class GraphQlOutboundDemo {
    record GraphQlResult(Map<String, Object> data, List<String> errors) {}

    static GraphQlResult executeProductQuery(String productId, boolean stockServiceDown) {
        Map<String, Object> data = new LinkedHashMap<>();
        data.put("name", "Widget");
        data.put("price", 19.99);
        List<String> errors = new ArrayList<>();
        // Real-world concern: GraphQL resolves each field somewhat independently -- a failure
        // resolving "stock" (a downstream call to inventory) shouldn't prevent "name" and
        // "price" (resolved from a different, healthy source) from still coming back.
        if (stockServiceDown) {
            data.put("stock", null);
            errors.add("field 'stock': inventory service unavailable");
        } else {
            data.put("stock", 42);
        }
        return new GraphQlResult(data, errors);
    }

    public static void main(String[] args) {
        GraphQlResult result = executeProductQuery("42", true);
        System.out.println("data: " + result.data());
        if (!result.errors().isEmpty()) {
            System.out.println("Partial failure detected: " + result.errors());
        } else {
            System.out.println("Fully successful");
        }
    }
}
```

How to run: `java GraphQlOutboundDemo.java`. Expected output: `data: {name=Widget, price=19.99, stock=null}` followed by `Partial failure detected: [field 'stock': inventory service unavailable]` — the flow still has `name` and `price` to work with even though `stock` failed, exactly the partial-success case a REST call's single status code cannot express.

### Level 3 — Advanced

```java
// GraphQlOutboundDemo.java
import java.util.*;

public class GraphQlOutboundDemo {
    record GraphQlResult(Map<String, Object> data, List<String> errors) {}

    static int stockAttempts = 0;

    static GraphQlResult executeProductQuery(String productId, boolean retryingStockOnly) {
        Map<String, Object> data = new LinkedHashMap<>();
        List<String> errors = new ArrayList<>();
        if (!retryingStockOnly) {
            data.put("name", "Widget");
            data.put("price", 19.99);
        }
        stockAttempts++;
        if (stockAttempts < 3) {
            data.put("stock", null);
            errors.add("field 'stock': inventory service unavailable");
        } else {
            data.put("stock", 42); // recovers on the third attempt
        }
        return new GraphQlResult(data, errors);
    }

    // Production concern: retry only the FAILED field, not the whole query -- re-fetching
    // "name" and "price" again would be wasted work since they already succeeded.
    static Map<String, Object> queryWithFieldRetry(String productId, int maxAttempts) {
        GraphQlResult first = executeProductQuery(productId, false);
        Map<String, Object> merged = new LinkedHashMap<>(first.data());

        int attempt = 1;
        while (merged.get("stock") == null && attempt < maxAttempts) {
            System.out.println("Retrying only 'stock' field, attempt " + (attempt + 1));
            GraphQlResult retry = executeProductQuery(productId, true);
            merged.put("stock", retry.data().get("stock"));
            attempt++;
        }
        return merged;
    }

    public static void main(String[] args) {
        Map<String, Object> finalResult = queryWithFieldRetry("42", 5);
        System.out.println("Final merged result: " + finalResult);
    }
}
```

How to run: `java GraphQlOutboundDemo.java`. Expected output: the first query returns `name`/`price` but a null `stock`; two "Retrying only 'stock' field" lines print as the retry loop targets just that field, and by the third attempt `stock` resolves to `42` — the final merged result showing all three fields populated, having wasted no work re-fetching the fields that already succeeded on the first try.

## 6. Walkthrough

Trace a partially-failing product lookup through to a fully-resolved result.

1. **Message arrives**: a request needing product details flows into `productLookupRequests`, carrying a `productId` header.
2. **Query execution**: `GraphQl.outboundGateway` builds the GraphQL operation from its configured query template and the message-derived variables, then executes it via the `ExecutionGraphQlService`.
3. **Field resolution**: the GraphQL service resolves each requested field somewhat independently — `name` and `price` might come from a fast, healthy data source while `stock` requires a call to a separate, currently-struggling inventory service.
4. **Partial response**: the response comes back as `data` (with `name` and `price` populated, `stock` null) plus `errors` (a specific entry naming the `stock` field and what went wrong) — the flow can read both parts distinctly rather than treating the whole call as either a success or a failure.
5. **Selective retry**: rather than re-running the entire query (which would waste the work already done for `name` and `price`), the flow retries specifically the failed field, checking after each attempt whether it has resolved.
6. **Final result**: once every field is populated (or a retry budget is exhausted, in which case the flow proceeds with whatever partial data it has, or routes to an error path), the merged result flows downstream to whatever needs the product details.

```
message -> GraphQl.outboundGateway executes query+variables
  -> response: { data: {name, price, stock:null}, errors: ["stock: ..."] }
    -> merge into result; if stock still null and attempts remain:
         retry query for stock only -> merge again
    -> final result (fully or partially populated) -> downstream
```

## 7. Gotchas & takeaways

> **Gotcha:** a GraphQL response with a non-empty `errors` array can still carry an HTTP status of 200 — treating "200 OK" as equivalent to "fully successful," the way a naive REST-style check would, silently hides partial failures; always inspect the `errors` array explicitly rather than relying on the transport-level status code.

- GraphQL's field-selection model reduces over-fetching, but it shifts responsibility onto the caller to know exactly which fields it needs — changing what a flow depends on later means updating the query template, not just reading a different property off an already-fixed response shape.
- Partial-success responses are a deliberate design feature of GraphQL, not an edge case to special-case rarely — any flow calling a non-trivial GraphQL schema should expect and handle the data/errors split as the normal path, not the exceptional one.
- Retrying only the failed portion of a query (as in Level 3) avoids redundant work, but requires the query to be structured (or split) in a way that makes isolating just the failed field practical — a single deeply nested query where everything depends on everything else may not decompose as cleanly.
- Prefer the plain HTTP adapter (card 0054) when the downstream service is REST, not GraphQL — the GraphQL outbound gateway's value comes specifically from understanding GraphQL's operation and partial-response shape, which doesn't apply to a conventional REST endpoint.
