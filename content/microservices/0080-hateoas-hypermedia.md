---
card: microservices
gi: 80
slug: hateoas-hypermedia
title: "HATEOAS / hypermedia"
---

## 1. What it is

HATEOAS — Hypermedia As The Engine Of Application State — is the [Richardson Maturity Model](0079-richardson-maturity-model.md)'s Level 3: API responses include not just data, but **links** describing the actions currently available on that resource, given its current state. A client navigates the API the way a person navigates a website by clicking links, rather than by having every possible URI template hard-coded in advance. If a resource's response doesn't include a `cancel` link, the client should not attempt to cancel it — the server, not client-side assumptions, is the single source of truth for what's currently possible.

## 2. Why & when

Without hypermedia, a client's knowledge of "what can I do with this resource, and when" lives entirely in the client's own code — often as a set of hard-coded URI templates and business-rule assumptions ("orders can be cancelled unless already shipped") duplicated from the server's actual logic. When the server's rules change, every client needs updating in lockstep, or risks calling an action that's no longer valid and getting an error back. HATEOAS moves that knowledge to a single place — the server — and clients that genuinely follow links instead of hard-coding them stay correct automatically as server-side business rules evolve.

This benefit matters most when an API has many independent, evolving clients you don't control directly — public APIs, or APIs consumed by third parties. It matters much less for tightly coupled, internally-developed service-to-service calls where both sides deploy together, which is why most microservices systems reasonably stop at Level 2 and skip HATEOAS. Reach for it specifically when client/server evolution needs to be decoupled.

## 3. Core concept

The set of links in a response is computed from the resource's current state; a client that only follows present links, and never assumes an absent one, automatically respects whatever business rules the server currently enforces.

```
Order (status=PLACED)     -> links: [self, cancel, ship]
Order (status=SHIPPED)    -> links: [self, track]        <- cancel/ship are GONE, track appeared
Order (status=DELIVERED)  -> links: [self]                <- terminal state, nothing left to do
```

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Three order states each show a different set of hypermedia links available, and a client following only the links present automatically adapts as the order moves through its lifecycle">
  <rect x="20" y="60" width="170" height="70" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="105" y="82" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">status: PLACED</text>
  <text x="105" y="100" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">links: self, cancel, ship</text>

  <rect x="235" y="60" width="170" height="70" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="320" y="82" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">status: SHIPPED</text>
  <text x="320" y="100" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">links: self, track</text>

  <rect x="450" y="60" width="170" height="70" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="535" y="82" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">status: DELIVERED</text>
  <text x="535" y="100" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">links: self</text>

  <line x1="190" y1="95" x2="235" y2="95" stroke="#8b949e" stroke-width="1.5" marker-end="url(#a80)"/>
  <line x1="405" y1="95" x2="450" y2="95" stroke="#8b949e" stroke-width="1.5" marker-end="url(#a80)"/>
  <defs><marker id="a80" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#8b949e"/></marker></defs>
</svg>

Each state offers a different set of links; the client's available actions shrink and grow with the resource's lifecycle.

## 5. Runnable example

Scenario: an order lifecycle client, first hard-coding which actions are available at each status (client-side business rules, prone to drifting from the server), then fixed to follow server-provided hypermedia links instead, then extended to trace an order through its full lifecycle purely by following links, never hard-coding a URI.

### Level 1 — Basic

```java
// File: HardCodedClientRules.java -- the CLIENT hard-codes which actions
// are valid for which status -- duplicating logic that really belongs
// on the server, and prone to drifting out of sync with it.
import java.util.*;

public class HardCodedClientRules {
    static boolean clientThinksCancelIsAllowed(String status) {
        return status.equals("PLACED"); // the client is GUESSING the server's rule
    }

    public static void main(String[] args) {
        String status = "SHIPPED"; // imagine the server's real rule ALSO now allows cancel-with-recall here
        if (clientThinksCancelIsAllowed(status)) {
            System.out.println("Client attempts cancel...");
        } else {
            System.out.println("Client refuses to attempt cancel (status=" + status + ") -- but the server might actually allow it now!");
        }
    }
}
```

**How to run:** `javac HardCodedClientRules.java && java HardCodedClientRules` (JDK 17+).

Expected output:
```
Client refuses to attempt cancel (status=SHIPPED) -- but the server might actually allow it now!
```

The client's hard-coded rule may be stale the moment the server's real business rule changes — the client has no way to know without a code update and redeploy.

### Level 2 — Intermediate

```java
// File: FollowingHypermediaLinks.java -- the SERVER computes available
// links; the client simply checks whether a link is PRESENT, never
// hard-coding its own copy of the business rule.
import java.util.*;

public class FollowingHypermediaLinks {
    record Link(String rel, String href) {}
    record OrderResource(int id, String status, List<Link> links) {
        Optional<Link> findLink(String rel) { return links.stream().filter(l -> l.rel().equals(rel)).findFirst(); }
    }

    static OrderResource fetchOrder(int id, String status) { // simulates a GET response FROM THE SERVER
        List<Link> links = new ArrayList<>();
        links.add(new Link("self", "/orders/" + id));
        if (status.equals("PLACED")) links.add(new Link("cancel", "/orders/" + id + "/cancel"));
        if (status.equals("SHIPPED")) links.add(new Link("cancel", "/orders/" + id + "/cancel")); // server NOW allows it here too
        return new OrderResource(id, status, links);
    }

    public static void main(String[] args) {
        OrderResource order = fetchOrder(42, "SHIPPED");
        Optional<Link> cancelLink = order.findLink("cancel");
        if (cancelLink.isPresent()) {
            System.out.println("Client found cancel link: " + cancelLink.get().href() + " -- attempting cancel");
        } else {
            System.out.println("No cancel link present -- client correctly does not attempt it");
        }
    }
}
```

**How to run:** `javac FollowingHypermediaLinks.java && java FollowingHypermediaLinks` (JDK 17+).

Expected output:
```
Client found cancel link: /orders/42/cancel -- attempting cancel
```

Note the client's code is *identical in shape* to what it would be if the server's rule had never changed — it just checks whether `cancel` is present. When the server started allowing cancellation from `SHIPPED` too, this client picked that up automatically, with no client code change at all.

### Level 3 — Advanced

```java
// File: FullLifecycleViaLinks.java -- trace an order through its FULL
// lifecycle by following links returned at each step -- the client NEVER
// hard-codes a single URI template; it only ever follows what's given.
import java.util.*;

public class FullLifecycleViaLinks {
    record Link(String rel, String href) {}
    record OrderResource(int id, String status, List<Link> links) {
        Optional<Link> findLink(String rel) { return links.stream().filter(l -> l.rel().equals(rel)).findFirst(); }
    }

    static Map<Integer, String> serverState = new HashMap<>(Map.of(42, "PLACED"));

    static OrderResource get(int id) {
        String status = serverState.get(id);
        List<Link> links = new ArrayList<>();
        links.add(new Link("self", "/orders/" + id));
        switch (status) {
            case "PLACED" -> links.add(new Link("ship", "/orders/" + id + "/ship"));
            case "SHIPPED" -> links.add(new Link("deliver", "/orders/" + id + "/deliver"));
            case "DELIVERED" -> { /* terminal state -- no further action links */ }
        }
        return new OrderResource(id, status, links);
    }

    static OrderResource follow(Link link) { // simulates the HTTP call the link's href represents
        if (link.href().endsWith("/ship")) serverState.put(42, "SHIPPED");
        if (link.href().endsWith("/deliver")) serverState.put(42, "DELIVERED");
        return get(42);
    }

    public static void main(String[] args) {
        OrderResource order = get(42);
        System.out.println("status=" + order.status() + " links=" + order.links().stream().map(Link::rel).toList());

        while (true) {
            // the client picks the FIRST action link that isn't "self" -- it never hard-codes which
            Optional<Link> next = order.links().stream().filter(l -> !l.rel().equals("self")).findFirst();
            if (next.isEmpty()) break;
            System.out.println("Following link: " + next.get().rel() + " -> " + next.get().href());
            order = follow(next.get());
            System.out.println("status=" + order.status() + " links=" + order.links().stream().map(Link::rel).toList());
        }
        System.out.println("No further actions available -- lifecycle complete.");
    }
}
```

**How to run:** `javac FullLifecycleViaLinks.java && java FullLifecycleViaLinks` (JDK 17+).

Expected output:
```
status=PLACED links=[self, ship]
Following link: ship -> /orders/42/ship
status=SHIPPED links=[self, deliver]
Following link: deliver -> /orders/42/deliver
status=DELIVERED links=[self]
No further actions available -- lifecycle complete.
```

## 6. Walkthrough

1. **Level 1** — `clientThinksCancelIsAllowed` hard-codes `status.equals("PLACED")` as its understanding of the server's business rule. `main` sets `status` to `"SHIPPED"` and, based on this stale, client-side assumption, refuses to attempt cancellation — even in a scenario where the server's *real* rule (illustrated only in the comment) might now permit it. The client has no mechanism to discover that discrepancy short of a code change.
2. **Level 2 — following a link instead of guessing** — `fetchOrder` (standing in for the server) now computes the `cancel` link based on its own current rule, which explicitly includes `"SHIPPED"` as well as `"PLACED"`. The client's logic, `order.findLink("cancel")`, contains no business rule of its own at all — it just asks "is this link present?" `main` calls it for a `SHIPPED` order and finds the `cancel` link present, correctly attempting the action this time — with zero client code change from what Level 1's client *should* have looked like if it had never hard-coded the rule in the first place.
3. **Level 3 — a full lifecycle traversal** — `get` computes a *different* single action link depending on `serverState`'s current status: `ship` while `PLACED`, `deliver` while `SHIPPED`, and no action link at all once `DELIVERED`. `follow` simulates actually calling a link's `href`, mutating `serverState` accordingly, then re-fetches the resource to get the new representation.
4. **Tracing the `while` loop** — `main` starts by fetching order 42, printing `status=PLACED links=[self, ship]`. The loop finds the first non-`self` link — `ship` — prints which link it's following, calls `follow`, which sets `serverState.get(42)` to `"SHIPPED"` and re-fetches, printing `status=SHIPPED links=[self, deliver]`. The loop repeats: finds `deliver`, follows it, `serverState` becomes `"DELIVERED"`, and the re-fetched resource now has only `[self]` — no action link. The loop's `next` computation finds nothing but `self`, so `next.isEmpty()` is `true`, the loop breaks, and the final "lifecycle complete" line prints.
5. **What makes this genuinely link-driven** — at no point does `main`'s loop contain the string `"/ship"` or `"/deliver"`, nor any conditional on the specific status value — it only ever asks "what's the first non-self link available right now?" and follows it. If the server's business rules changed tomorrow — say, an intermediate `"PACKED"` status with its own link were introduced between `PLACED` and `SHIPPED` — this exact client loop would still correctly traverse the new lifecycle, because it never assumed a fixed sequence of states in the first place.

## 7. Gotchas & takeaways

> **Gotcha:** HATEOAS only delivers its benefit if clients actually implement link-following logic instead of quietly hard-coding the URI templates they observe in example responses — a client that reads `/orders/42/cancel` once and bakes that template into its own code has silently reverted to Level 2 behavior while still technically consuming a Level 3 API.

- HATEOAS moves "what actions are currently valid on this resource" from client-side assumptions into the server's response itself, computed fresh from the resource's real current state.
- A client that only ever follows links present in the response, and never assumes one that's absent, stays correct automatically as the server's business rules evolve — no client redeploy needed.
- The benefit is largest for APIs with many independently-evolving clients you don't control; for tightly coupled, co-deployed service-to-service calls, the added complexity often isn't worth it, and Level 2 is the pragmatic choice.
- This is the top of the [Richardson Maturity Model](0079-richardson-maturity-model.md) — understand it as an available tool for specific situations, not a mandatory target for every API.
- Real Spring applications implement this with Spring HATEOAS, which provides `EntityModel`/`Link` types matching exactly the `OrderResource`/`Link` shape modeled here.
