---
card: system-design
gi: 206
slug: resource-modeling-naming
title: Resource modeling & naming
---

## 1. What it is

**Resource modeling** is deciding what "nouns" your API exposes — `orders`, `customers`, `invoices` — and how they relate to each other. **Naming** is the discipline of turning those nouns into consistent, predictable URL paths, like `/customers/{id}/orders`, so that anyone reading the URL can guess what it returns without reading documentation.

## 2. Why & when

An API whose paths mix verbs and nouns inconsistently (`/getOrder`, `/orders/create`, `/order-list`) forces every consumer to memorize each endpoint individually — nothing about one path predicts the shape of another. Modeling the API around resources (nouns) and using HTTP methods (GET, POST, PUT, DELETE) as the verbs fixes this: once a consumer learns the pattern `/resource` and `/resource/{id}`, they can predict most of the API without reading the docs.

Do this at the start of designing any REST API — resource modeling is the first decision that shapes everything else (versioning, pagination, error handling all sit on top of it). It applies less directly to RPC-style APIs like [gRPC](0213-grpc-streaming-apis.md), which model actions rather than resources by design.

## 3. Core concept

- **Nouns, not verbs, in the path.** `/orders`, not `/getOrders` or `/createOrder`. The action comes from the HTTP method: `GET /orders` reads, `POST /orders` creates.
- **Collections and single resources.** `/orders` is a **collection** (a list of orders); `/orders/{id}` is a **single resource** (one specific order). This pair is the basic building block of almost every REST API.
- **Nesting reflects ownership, not just relation.** `/customers/{id}/orders` says "orders that belong to this customer." Only nest when the child resource cannot meaningfully exist without the parent — do not nest everything just because two resources are related.
- **Plural, lowercase, hyphenated.** `/order-items`, not `/OrderItem` or `/order_item`. Consistency here means a consumer never has to guess the exact casing or separator for a new endpoint.
- **Actions that are not naturally resource-shaped.** Some operations genuinely are not CRUD on a resource — "cancel this order." Model them as a sub-resource or a clear verb-suffixed endpoint (`POST /orders/{id}/cancel`), used sparingly, rather than forcing every action into `PUT`.

## 4. Diagram

```
  GOOD (resource-modeled, predictable)         BAD (verb-based, inconsistent)

  GET    /orders             list orders       GET  /getAllOrders
  POST   /orders             create order       POST /createNewOrder
  GET    /orders/{id}        read one order      GET  /order?id=5
  PUT    /orders/{id}        replace one order    POST /updateOrder
  DELETE /orders/{id}        delete one order      GET  /removeOrder?id=5

  GET  /customers/{id}/orders   orders owned by this customer
                                 (nesting shows ownership)

  POST /orders/{id}/cancel      an action that is not plain CRUD,
                                 modeled as a sub-resource action
```
*Caption: the left side lets you predict every new endpoint from the pattern already established. The right side requires memorizing each one individually.*

## 5. Runnable example

This models the *decision process* of resource modeling — routing requests to handlers based on resource + HTTP method — since the naming pattern itself is not runnable in isolation.

**Level 1 — Basic.** A router matching `METHOD /resource` and `METHOD /resource/{id}` patterns to handlers.

**Level 2 — Intermediate.** Add a nested resource (`/customers/{id}/orders`) to show ownership modeling.

**Level 3 — Advanced.** Add a non-CRUD action modeled as a sub-resource (`/orders/{id}/cancel`), and show why it is preferable to overloading `PUT`.

```java
// ResourceModelingDemo.java
import java.util.*;
import java.util.regex.*;

public class ResourceModelingDemo {

    record Route(String method, Pattern pattern, String description) {}

    static class Router {
        List<Route> routes = new ArrayList<>();

        void register(String method, String pathPattern, String description) {
            // Convert "/orders/{id}" into a regex that captures the id segment.
            String regex = "^" + pathPattern.replaceAll("\\{[^}]+}", "([^/]+)") + "$";
            routes.add(new Route(method, Pattern.compile(regex), description));
        }

        String dispatch(String method, String path) {
            for (Route route : routes) {
                if (!route.method().equals(method)) continue;
                Matcher m = route.pattern().matcher(path);
                if (m.matches()) {
                    List<String> params = new ArrayList<>();
                    for (int i = 1; i <= m.groupCount(); i++) params.add(m.group(i));
                    return route.description() + (params.isEmpty() ? "" : " (params: " + params + ")");
                }
            }
            return "404 Not Found: " + method + " " + path;
        }
    }

    public static void main(String[] args) {
        Router router = new Router();

        System.out.println("Level 1 - collection + single-resource routes:");
        router.register("GET", "/orders", "list orders");
        router.register("POST", "/orders", "create order");
        router.register("GET", "/orders/{id}", "read one order");
        router.register("PUT", "/orders/{id}", "replace one order");
        router.register("DELETE", "/orders/{id}", "delete one order");

        System.out.println("  " + router.dispatch("GET", "/orders"));
        System.out.println("  " + router.dispatch("GET", "/orders/501"));
        System.out.println("  " + router.dispatch("DELETE", "/orders/501"));

        System.out.println("\nLevel 2 - nested resource shows ownership:");
        router.register("GET", "/customers/{id}/orders", "list orders owned by this customer");
        System.out.println("  " + router.dispatch("GET", "/customers/77/orders"));

        System.out.println("\nLevel 3 - non-CRUD action modeled as a sub-resource, not an overloaded PUT:");
        router.register("POST", "/orders/{id}/cancel", "cancel this specific order (an action, not a field replace)");
        System.out.println("  " + router.dispatch("POST", "/orders/501/cancel"));

        System.out.println("\n  compare to the anti-pattern: overloading PUT /orders/501 with a 'status' field");
        System.out.println("  to mean cancellation hides the action inside a generic update -");
        System.out.println("  a client reading the route table alone cannot tell what PUT will do.");
    }
}
```

**How to run:** `java ResourceModelingDemo.java` (JDK 17+, single file, no dependencies).

## 6. Walkthrough

1. **Level 1:** `router.register(...)` is called five times, each adding one `Route` — a method, a compiled path pattern, and a description. `register` converts `"/orders/{id}"` into a regex that captures the `{id}` segment as a group, so `/orders/501` matches with `"501"` captured.
2. `router.dispatch("GET", "/orders")` scans the routes for a `GET` route whose pattern matches `"/orders"` exactly — it finds the collection route and returns `"list orders"`, with no captured parameters. `dispatch("GET", "/orders/501")` matches the single-resource pattern instead, capturing `"501"` as a parameter.
3. **Level 2:** the new route `GET /customers/{id}/orders` captures the customer's ID and returns orders scoped to that customer. `dispatch("GET", "/customers/77/orders")` matches this pattern, printing `"list orders owned by this customer (params: [77])"` — the nesting in the path itself communicates that these orders belong to customer 77, without needing a query parameter to say so.
4. **Level 3:** `POST /orders/{id}/cancel` is registered as its own route — a sub-resource representing the *action* of cancelling, not a generic field update. `dispatch("POST", "/orders/501/cancel")` matches it directly.
5. The comment printed afterward makes the contrast explicit: if cancellation were instead done via `PUT /orders/501` with a `status: "cancelled"` field buried in the request body, the route table alone (what this router prints) would give no hint that this specific `PUT` call causes cancellation — you would have to read every field of every possible request body to know. Modeling it as its own path keeps the API's behavior visible from the routing layer alone.

## 7. Gotchas & takeaways

> **Gotcha:** over-nesting is a common mistake — `/customers/{cid}/orders/{oid}/items/{iid}/discounts/{did}` is technically resource-modeled but unusable. If a resource can be looked up on its own (an item has a globally unique ID), give it a top-level path (`/items/{iid}`) and use nesting only for genuinely dependent creation/listing.

- Pick nouns for your resources before writing a single endpoint — the naming pattern should be decided once, up front, and applied consistently everywhere after.
- Use HTTP methods for the verb; reserve action-suffixed paths (`/orders/{id}/cancel`) for genuine actions that do not fit CRUD, and use them sparingly.
- Consistency matters more than any single "correct" choice — plural vs singular, hyphen vs underscore — pick one convention and never deviate within the same API.
- Good resource modeling is what makes every later API-design decision easier: [pagination](0209-pagination-filtering-sorting.md), [versioning](0208-versioning-strategies.md), and [error contracts](0211-error-contracts-problem-json.md) all assume a consistent resource shape to attach to.
