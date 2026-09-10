---
card: system-design
gi: 207
slug: richardson-maturity-model
title: Richardson maturity model
---

## 1. What it is

The **Richardson maturity model** ranks how "RESTful" an API is on four levels, numbered 0 to 3. Level 0 is a single endpoint that does everything through one generic call (like a classic RPC or SOAP call); level 3 is a fully resource-oriented API that uses proper URLs, proper HTTP verbs, and includes links to related actions in every response (called **HATEOAS** — Hypermedia As The Engine Of Application State).

## 2. Why & when

Many APIs call themselves "REST" while only reaching level 1 or 2 of this model — they use resource URLs and HTTP verbs correctly, but the response is just raw data with no indication of what the client can do next. The Richardson model gives you a shared vocabulary to say precisely how far an API has actually adopted REST's ideas, instead of a binary "is it REST or not."

Use this model as a design checklist when building a new API: level 2 (resources + HTTP verbs) is the practical target for the large majority of APIs, and is what most people mean by "REST" in everyday use. Level 3 (HATEOAS) adds real value for APIs whose available actions change based on server-side state (e.g. "cancel" only appears as a link if the order is still cancellable) but adds real client complexity, so treat it as a deliberate choice, not a default.

## 3. Core concept

- **Level 0 — The Swamp of POX.** One URL, one HTTP method (usually `POST`), and the actual operation is described inside the request body (e.g. `{"action": "getOrder", "id": 5}`). This is RPC wearing HTTP as transport only.
- **Level 1 — Resources.** Multiple URLs now exist, one per resource (`/orders/5`, `/customers/7`), but every request might still use the same HTTP method (often `POST`) regardless of the actual operation.
- **Level 2 — HTTP verbs.** URLs represent resources *and* the HTTP method carries real meaning: `GET` reads, `POST` creates, `PUT` replaces, `DELETE` removes. Status codes are used correctly (`404` for missing, `201` for created). This is where [resource modeling](0206-resource-modeling-naming.md) and proper verb usage land you, and it is what most production "REST APIs" actually are.
- **Level 3 — Hypermedia controls (HATEOAS).** Every response includes links describing what the client can do next, given the current state — a shipped order's response includes a `track` link but no `cancel` link; a pending order's response includes `cancel` but not `track`. The client discovers valid next actions from the response itself, not from separately memorized documentation.
- **Why level 3 is rare in practice.** It requires the client to parse and follow links dynamically instead of hardcoding URL templates, which is a real engineering cost most teams do not take on unless the workflow genuinely benefits from state-driven discoverability.

## 4. Diagram

```
  LEVEL 0                LEVEL 1              LEVEL 2                LEVEL 3
  one URL,                per-resource URL,    URL + HTTP verb        + links describing
  one verb,               but one verb still   both carry meaning     valid next actions
  action in body

  POST /api               POST /orders/5       GET    /orders/5       GET /orders/5
  {action:"getOrder",     POST /customers/7    PUT    /orders/5       {
   id:5}                  (still all POST)     DELETE /orders/5         "status":"PENDING",
                                                (verb matches intent)    "links": [
                                                                           {"rel":"cancel",
                                                                            "href":"/orders/5/cancel"}
                                                                         ]
                                                                        }
                                                                        (no "track" link -
                                                                         not shippable yet)
```
*Caption: each level adds one specific thing the previous level lacked — separate URLs, then verb meaning, then discoverable next actions embedded in the response itself.*

## 5. Runnable example

**Level 1 — Basic.** A level-0-style single endpoint where the action is described entirely in the request body.

**Level 2 — Intermediate.** The same operations exposed as level-2 REST: separate URLs, real HTTP verbs.

**Level 3 — Advanced.** A level-3 response that includes hypermedia links, and the links change based on the resource's current state.

```java
// RichardsonMaturityDemo.java
import java.util.*;

public class RichardsonMaturityDemo {

    record Order(String id, String status) {}

    // ---------- Level 0 (for contrast): one endpoint, action inside the body ----------
    static String level0SingleEndpoint(String action, Map<String, String> body) {
        return switch (action) {
            case "getOrder" -> "{id: \"" + body.get("id") + "\", status: \"SHIPPED\"}";
            case "cancelOrder" -> "{id: \"" + body.get("id") + "\", status: \"CANCELLED\"}";
            default -> "{error: \"unknown action\"}";
        };
    }

    // ---------- Level 2: proper resource URLs + HTTP verbs ----------
    static Map<String, Order> orders = new HashMap<>(Map.of(
        "5", new Order("5", "PENDING"),
        "6", new Order("6", "SHIPPED")
    ));

    static String getOrder(String id) {
        Order o = orders.get(id);
        return o == null ? "404 Not Found" : "200 OK {id: \"" + o.id() + "\", status: \"" + o.status() + "\"}";
    }
    static String cancelOrder(String id) {
        Order o = orders.get(id);
        if (o == null) return "404 Not Found";
        if (!o.status().equals("PENDING")) return "409 Conflict: cannot cancel a " + o.status() + " order";
        orders.put(id, new Order(id, "CANCELLED"));
        return "200 OK {id: \"" + id + "\", status: \"CANCELLED\"}";
    }

    // ---------- Level 3: HATEOAS - links depend on current state ----------
    static String getOrderWithLinks(String id) {
        Order o = orders.get(id);
        if (o == null) return "404 Not Found";
        List<String> links = new ArrayList<>();
        links.add("{\"rel\":\"self\",\"href\":\"/orders/" + id + "\"}");
        if (o.status().equals("PENDING")) {
            links.add("{\"rel\":\"cancel\",\"href\":\"/orders/" + id + "/cancel\"}");
        }
        if (o.status().equals("SHIPPED")) {
            links.add("{\"rel\":\"track\",\"href\":\"/orders/" + id + "/tracking\"}");
        }
        return "200 OK {id: \"" + id + "\", status: \"" + o.status() + "\", links: " + links + "}";
    }

    public static void main(String[] args) {
        System.out.println("Level 0 style (for contrast) - one endpoint, action in the body:");
        System.out.println("  " + level0SingleEndpoint("getOrder", Map.of("id", "5")));

        System.out.println("\nLevel 2 - resource URL + HTTP verb carries the meaning:");
        System.out.println("  GET /orders/5    -> " + getOrder("5"));
        System.out.println("  POST /orders/5/cancel -> " + cancelOrder("5"));
        System.out.println("  POST /orders/6/cancel -> " + cancelOrder("6")); // already shipped, cannot cancel

        System.out.println("\nLevel 3 - HATEOAS: links change based on the resource's current state:");
        System.out.println("  GET /orders/6 (SHIPPED)  -> " + getOrderWithLinks("6"));
        orders.put("7", new Order("7", "PENDING"));
        System.out.println("  GET /orders/7 (PENDING)  -> " + getOrderWithLinks("7"));
    }
}
```

**How to run:** `java RichardsonMaturityDemo.java` (JDK 17+, single file, no dependencies).

## 6. Walkthrough

1. **Level 0:** `level0SingleEndpoint("getOrder", Map.of("id", "5"))` shows the shape of a level-0 API — one function-like call where the `action` field, not the URL or HTTP method, determines what happens. There is only one conceptual "endpoint" here.
2. **Level 2:** `getOrder("5")` and `cancelOrder("5")` correspond to `GET /orders/5` and `POST /orders/5/cancel` — different URLs, and the operation is now clear from the verb and path alone, not from a body field. `cancelOrder("5")` succeeds because order 5's status is `"PENDING"`.
3. **`cancelOrder("6")` is called next**, but order 6's status is `"SHIPPED"`. The method checks `!o.status().equals("PENDING")` and returns `"409 Conflict"` — this is level 2 behaving correctly: the server enforces the business rule, but a client that only has the URL pattern memorized has no way to know in advance that cancelling order 6 will fail.
4. **Level 3:** `getOrderWithLinks("6")` builds a `links` list. Because order 6's status is `"SHIPPED"`, the code's `if (o.status().equals("PENDING"))` branch is skipped, so no `"cancel"` link is added — but the `if (o.status().equals("SHIPPED"))` branch adds a `"track"` link instead.
5. **`getOrderWithLinks("7")` runs next**, on a freshly created `PENDING` order. This time the `"cancel"` link is included and the `"track"` link is not — the exact same code, given a resource in a different state, produces different available actions in its response. A level-3 client would read these links at runtime and know cancellation is possible for order 7 but not order 6, without hardcoding that business rule on the client side at all.

## 7. Gotchas & takeaways

> **Gotcha:** many APIs described as "fully RESTful" only reach level 2 — HATEOAS (level 3) is genuinely rare in production, because it requires clients to follow links dynamically instead of hardcoding URL templates, which most client codebases are not built to do.

- Level 2 (resources + real HTTP verbs + correct status codes) is the practical, industry-standard target — treat it as the default goal for a new API.
- Only invest in level 3 when the client genuinely benefits from discovering valid next actions dynamically, such as a workflow UI that should not need a hardcoded rulebook of "when is cancel allowed."
- The model is a diagnostic tool, not a certification — use it to identify precisely what your API is missing, rather than as a pass/fail label.
- Building [error contracts](0211-error-contracts-problem-json.md) and consistent [resource modeling](0206-resource-modeling-naming.md) are what get you to level 2 reliably; HATEOAS links are the one additional ingredient level 3 requires.
