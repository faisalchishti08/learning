---
card: microservices
gi: 398
slug: owasp-api-security-top-10
title: "OWASP API Security Top 10"
---

## 1. What it is

The **OWASP API Security Top 10** is a periodically updated list, published by the Open Web Application Security Project, ranking the most common and impactful security risks specific to APIs — as distinct from OWASP's older, more general Web Application Top 10. It exists because API-specific architectures (heavy use of object IDs in URLs, machine-to-machine auth, granular per-endpoint permissions) create failure patterns that don't map cleanly onto classic web vulnerabilities, and microservices systems — being almost entirely composed of internal and external APIs — are squarely in its target audience.

## 2. Why & when

Every topic in this Security section maps to one or more items on this list; treating the list as a checklist is a practical way to sanity-check a microservices system's overall posture rather than reasoning about security purely bottom-up:

- **It names failure patterns you'll otherwise rediscover the hard way.** Nearly every serious API breach in the industry falls into one of these categories — you're better off learning them from a maintained public list than from an incident report about your own system.
- **It's a common vocabulary for security reviews.** When a security team says "this endpoint has a BOLA issue," having a shared reference for what that means (and how to check for it) speeds up every conversation.
- **It highlights risks that are easy to introduce specifically in a microservices architecture** — for example, a rich internal API surface between services multiplies the number of places object-level authorization can be forgotten.

You should walk through this list explicitly during design review of any new API, and again whenever an incident or penetration test surfaces a gap — it's a lens for auditing what you've built, not just a list to read once.

## 3. Core concept

Think of the list as a building inspector's checklist: not a guarantee the building is safe, but a set of the specific, well-known ways buildings *actually* fail — faulty wiring, missing fire exits, unstable foundations — checked systematically rather than relying on a general sense that "it looks fine." The current OWASP API Security Top 10 (2023 edition) covers:

1. **API1: Broken Object Level Authorization (BOLA)** — a caller can access or modify an object (an order, a user record) that isn't theirs, by simply changing an ID in the request, because the API checks "is this a valid order ID" but not "does this order belong to this caller." This is exactly the gap closed by fine-grained ownership checks — see [scopes, roles & fine-grained authorization](0395-scopes-roles-fine-grained-authorization.md).
2. **API2: Broken Authentication** — weak, missing, or improperly implemented authentication: predictable tokens, missing rate limits on login (see [rate limiting & throttling](0397-rate-limiting-throttling-as-security-control.md)), or accepting expired/malformed credentials.
3. **API3: Broken Object Property Level Authorization** — even when object-level access is correctly checked, a caller can read or write *specific fields* they shouldn't (e.g., a user updating their own profile can also sneak in `"role": "admin"` in the same request body — "mass assignment").
4. **API4: Unrestricted Resource Consumption** — no limits on request rate, payload size, or expensive query parameters, letting a single caller exhaust cost or capacity; directly addressed by [rate limiting & throttling](0397-rate-limiting-throttling-as-security-control.md).
5. **API5: Broken Function Level Authorization** — a caller can invoke an *administrative* or otherwise privileged operation their role shouldn't permit, often because the check happens in the UI but not the API itself.
6. **API6: Unrestricted Access to Sensitive Business Flows** — automatable abuse of a legitimate business process (e.g., scripted mass account creation, or buying up limited inventory) that isn't technically "broken" auth but is still abuse the API should detect and slow.
7. **API7: Server Side Request Forgery (SSRF)** — the API fetches a URL supplied (directly or indirectly) by the caller, and an attacker points it at an internal-only resource instead of the intended external one; covered in depth in [confused deputy / SSRF concerns at the gateway](0399-confused-deputy-ssrf-concerns-at-gateway.md).
8. **API8: Security Misconfiguration** — verbose error messages leaking stack traces, default credentials left enabled, unnecessary HTTP methods exposed, missing security headers — the broad "didn't lock the doors we thought we locked" category.
9. **API9: Improper Inventory Management** — old, undocumented, or "shadow" API versions still running and reachable, often with weaker security than the current version, forgotten precisely because nobody maintains a full inventory of what's exposed.
10. **API10: Unsafe Consumption of APIs** — trusting data from a *third-party* API without validating it, on the assumption that "it came from a partner integration, so it must be safe" — the same trust-boundary mistake named in [microservices security challenges](0378-microservices-security-challenges-larger-attack-surface.md), just applied to an external dependency instead of an internal one.

## 4. Diagram

<svg viewBox="0 0 640 280" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="The ten OWASP API Security risks grouped by theme: object and function level authorization, authentication and resource abuse, and configuration and supply-chain issues" font-family="sans-serif">
  <rect x="20" y="20" width="190" height="90" rx="8" fill="#1c2430" stroke="#f85149"/>
  <text x="115" y="40" fill="#f85149" font-size="10" text-anchor="middle">Authorization gaps</text>
  <text x="115" y="58" fill="#8b949e" font-size="9" text-anchor="middle">API1 BOLA</text>
  <text x="115" y="73" fill="#8b949e" font-size="9" text-anchor="middle">API3 property-level</text>
  <text x="115" y="88" fill="#8b949e" font-size="9" text-anchor="middle">API5 function-level</text>

  <rect x="230" y="20" width="190" height="90" rx="8" fill="#1c2430" stroke="#f0883e"/>
  <text x="325" y="40" fill="#f0883e" font-size="10" text-anchor="middle">Auth &amp; abuse</text>
  <text x="325" y="58" fill="#8b949e" font-size="9" text-anchor="middle">API2 broken auth</text>
  <text x="325" y="73" fill="#8b949e" font-size="9" text-anchor="middle">API4 resource consumption</text>
  <text x="325" y="88" fill="#8b949e" font-size="9" text-anchor="middle">API6 business flow abuse</text>

  <rect x="440" y="20" width="180" height="90" rx="8" fill="#1c2430" stroke="#79c0ff"/>
  <text x="530" y="40" fill="#79c0ff" font-size="10" text-anchor="middle">Config &amp; supply chain</text>
  <text x="530" y="58" fill="#8b949e" font-size="9" text-anchor="middle">API7 SSRF</text>
  <text x="530" y="73" fill="#8b949e" font-size="9" text-anchor="middle">API8 misconfiguration</text>
  <text x="530" y="88" fill="#8b949e" font-size="9" text-anchor="middle">API9 inventory / API10 consumption</text>

  <rect x="150" y="150" width="340" height="100" rx="8" fill="#1c2430" stroke="#6db33f"/>
  <text x="320" y="175" fill="#e6edf3" font-size="11" text-anchor="middle">Cuts across every topic in this section:</text>
  <text x="320" y="195" fill="#8b949e" font-size="9" text-anchor="middle">object/role checks, rate limiting, gateway design,</text>
  <text x="320" y="212" fill="#8b949e" font-size="9" text-anchor="middle">secrets handling, and third-party trust boundaries</text>
  <text x="320" y="232" fill="#6db33f" font-size="9" text-anchor="middle">use it as a review checklist, not a one-time read</text>
</svg>

The ten risks cluster into authorization gaps, authentication/abuse issues, and configuration or supply-chain problems — each mapping onto specific defenses covered elsewhere in this Security section.

## 5. Runnable example

Scenario: an order-details endpoint. We demonstrate three of the most common OWASP API risks in sequence on the same endpoint — starting vulnerable to Broken Object Level Authorization (API1), then fixing that but introducing Broken Object Property Level Authorization via mass assignment (API3), then fixing both together.

### Level 1 — Basic

```java
// File: BrokenObjectLevelAuth.java -- API1: BOLA. The endpoint fetches an
// order by ID from the request WITHOUT checking that the requesting user
// actually owns it. Any authenticated user can read ANY order just by
// guessing or incrementing an ID.
import java.util.*;

public class BrokenObjectLevelAuth {
    record Order(String orderId, String ownerId, String contents) {}

    static final Map<String, Order> ORDERS = Map.of(
            "order-1", new Order("order-1", "alice", "2x Widget"),
            "order-2", new Order("order-2", "bob", "1x Gadget (contains bob's home address)")
    );

    // 'requestingUser' is authenticated, but never checked against the order's owner.
    static String getOrder(String orderId, String requestingUser) {
        Order order = ORDERS.get(orderId);
        if (order == null) return "404 Not Found";
        return "200 OK -- " + order.contents() + " (fetched by '" + requestingUser + "', owner check: NONE)";
    }

    public static void main(String[] args) {
        System.out.println(getOrder("order-1", "alice"));
        // alice simply requests a DIFFERENT order ID and gets bob's data too.
        System.out.println(getOrder("order-2", "alice"));
    }
}
```

How to run: `java BrokenObjectLevelAuth.java`

`getOrder` authenticates `requestingUser` (that part is assumed already done upstream) but never compares it against `order.ownerId()`. alice fetching `order-2` — which belongs to bob and contains his address — succeeds exactly as if it were her own order. This is API1, Broken Object Level Authorization, in its most literal form: swap the ID, get someone else's data.

### Level 2 — Intermediate

```java
// File: OwnershipFixedButMassAssignment.java -- API1 is now fixed (ownership
// is checked), but the update endpoint introduces API3: Broken Object PROPERTY
// Level Authorization via mass assignment -- the caller's request body is
// blindly applied field-by-field, including fields they should never control.
import java.util.*;

public class OwnershipFixedButMassAssignment {
    static class Order {
        String orderId, ownerId, contents;
        double totalPrice;
        boolean isPaid;
        Order(String id, String owner, String contents, double price, boolean paid) {
            this.orderId = id; this.ownerId = owner; this.contents = contents; this.totalPrice = price; this.isPaid = paid;
        }
    }

    static final Map<String, Order> ORDERS = new HashMap<>();
    static { ORDERS.put("order-1", new Order("order-1", "alice", "2x Widget", 40.00, false)); }

    static String getOrder(String orderId, String requestingUser) {
        Order order = ORDERS.get(orderId);
        if (order == null || !order.ownerId.equals(requestingUser)) return "404 Not Found"; // ownership fixed
        return "200 OK -- " + order.contents + ", total=$" + order.totalPrice + ", paid=" + order.isPaid;
    }

    // The request body is applied field-by-field with NO allow-list -- "mass assignment."
    static String updateOrder(String orderId, String requestingUser, Map<String, Object> requestBody) {
        Order order = ORDERS.get(orderId);
        if (order == null || !order.ownerId.equals(requestingUser)) return "404 Not Found";
        for (var entry : requestBody.entrySet()) {
            switch (entry.getKey()) {
                case "contents" -> order.contents = (String) entry.getValue();
                case "totalPrice" -> order.totalPrice = (Double) entry.getValue(); // customer can set their OWN price!
                case "isPaid" -> order.isPaid = (Boolean) entry.getValue();        // customer can mark it PAID themselves!
            }
        }
        return "200 OK -- order updated";
    }

    public static void main(String[] args) {
        System.out.println(getOrder("order-1", "alice"));
        // alice's "update contents" request also sneaks in totalPrice and isPaid.
        Map<String, Object> maliciousBody = new LinkedHashMap<>();
        maliciousBody.put("contents", "2x Widget");
        maliciousBody.put("totalPrice", 0.01);
        maliciousBody.put("isPaid", true);
        System.out.println(updateOrder("order-1", "alice", maliciousBody));
        System.out.println(getOrder("order-1", "alice"));
    }
}
```

How to run: `java OwnershipFixedButMassAssignment.java`

`getOrder` now correctly checks `order.ownerId.equals(requestingUser)` — API1 is fixed. But `updateOrder` iterates every key in the caller's request body and applies it directly to the `Order` object with no restriction on *which fields* a customer should be allowed to set. alice's request, ostensibly just updating `contents`, also sets `totalPrice` to a penny and `isPaid` to `true` — fields that should only ever be set by internal payment logic, never by the customer directly. The final `getOrder` call shows the order now reflects a paid, one-cent total, purely because the update endpoint trusted the request body's shape completely.

### Level 3 — Advanced

```java
// File: ObjectAndPropertyLevelAuthFixed.java -- BOTH API1 and API3 are fixed:
// ownership is checked (object-level), AND updates go through an explicit
// ALLOW-LIST of caller-writable fields (property-level) -- privileged fields
// like totalPrice and isPaid can only be changed through a separate, internal
// path that isn't reachable from this customer-facing endpoint at all.
import java.util.*;

public class ObjectAndPropertyLevelAuthFixed {
    static class Order {
        final String orderId, ownerId;
        String contents;
        double totalPrice;
        boolean isPaid;
        Order(String id, String owner, String contents, double price, boolean paid) {
            this.orderId = id; this.ownerId = owner; this.contents = contents; this.totalPrice = price; this.isPaid = paid;
        }
    }

    static final Map<String, Order> ORDERS = new HashMap<>();
    static { ORDERS.put("order-1", new Order("order-1", "alice", "2x Widget", 40.00, false)); }

    // Only these fields may EVER be set through the customer-facing update endpoint.
    static final Set<String> CUSTOMER_WRITABLE_FIELDS = Set.of("contents");

    static String updateOrderAsCustomer(String orderId, String requestingUser, Map<String, Object> requestBody) {
        Order order = ORDERS.get(orderId);
        if (order == null || !order.ownerId.equals(requestingUser)) return "404 Not Found"; // object-level check

        List<String> rejectedFields = new ArrayList<>();
        for (String key : requestBody.keySet()) {
            if (!CUSTOMER_WRITABLE_FIELDS.contains(key)) {
                rejectedFields.add(key); // property-level check: refuse anything not explicitly allow-listed
            }
        }
        if (!rejectedFields.isEmpty()) {
            return "400 Bad Request -- fields not permitted for customer update: " + rejectedFields;
        }
        order.contents = (String) requestBody.get("contents");
        return "200 OK -- order contents updated";
    }

    // A SEPARATE, internal-only path -- not exposed to customer requests -- for privileged fields.
    static String markOrderPaidInternal(String orderId, double confirmedPrice) {
        Order order = ORDERS.get(orderId);
        order.totalPrice = confirmedPrice;
        order.isPaid = true;
        return "200 OK -- order marked paid internally, price confirmed by payment processor";
    }

    public static void main(String[] args) {
        Map<String, Object> maliciousBody = new LinkedHashMap<>();
        maliciousBody.put("contents", "2x Widget");
        maliciousBody.put("totalPrice", 0.01);
        maliciousBody.put("isPaid", true);
        System.out.println(updateOrderAsCustomer("order-1", "alice", maliciousBody)); // now rejected

        Map<String, Object> legitimateBody = Map.of("contents", "3x Widget");
        System.out.println(updateOrderAsCustomer("order-1", "alice", legitimateBody)); // succeeds

        System.out.println(markOrderPaidInternal("order-1", 60.00)); // only the payment system calls this
    }
}
```

How to run: `java ObjectAndPropertyLevelAuthFixed.java`

`updateOrderAsCustomer` keeps the object-level ownership check from Level 2, then adds a property-level check: every key in `requestBody` must appear in `CUSTOMER_WRITABLE_FIELDS`, or the entire request is rejected with a `400`, naming exactly which fields weren't permitted. alice's malicious body — trying to sneak in `totalPrice` and `isPaid` alongside a legitimate `contents` change — is now rejected outright, rather than silently applying only the safe field and ignoring the rest (which would hide the attack attempt instead of surfacing it). A legitimate, `contents`-only update still succeeds. `markOrderPaidInternal` demonstrates the correct way to handle privileged fields: a completely separate method (in a real system, a separate internal-only endpoint, callable only by the payment service, not by any customer-facing route) that customers can never reach no matter what their request body contains.

## 6. Walkthrough

Trace `ObjectAndPropertyLevelAuthFixed.main` in order. **First**, `updateOrderAsCustomer("order-1", "alice", maliciousBody)` runs. `ORDERS.get("order-1")` returns the order, and `order.ownerId.equals("alice")` is `true` — the object-level check passes. Next, the loop over `maliciousBody.keySet()` (`"contents"`, `"totalPrice"`, `"isPaid"`) checks each against `CUSTOMER_WRITABLE_FIELDS`, which contains only `"contents"`. `"totalPrice"` and `"isPaid"` are both added to `rejectedFields`. Since `rejectedFields` is non-empty, the method returns `"400 Bad Request -- fields not permitted for customer update: [totalPrice, isPaid]"` — the entire request is refused, and no field is silently applied.

**Next**, `updateOrderAsCustomer("order-1", "alice", legitimateBody)` runs with a body containing only `"contents"`. The object-level check passes as before. The loop finds `"contents"` is in `CUSTOMER_WRITABLE_FIELDS`, so `rejectedFields` stays empty, and `order.contents` is set to `"3x Widget"` — the update succeeds.

**Finally**, `markOrderPaidInternal("order-1", 60.00)` runs — a method with no `requestingUser` parameter at all, because it isn't meant to be reachable from any customer-authenticated request path in the first place; in a real system this would live behind a completely separate, service-to-service-authenticated internal endpoint (see [service-to-service authentication](0391-service-to-service-authentication.md)). It sets `totalPrice` and `isPaid` directly, modeling the payment service confirming a charge succeeded.

```
400 Bad Request -- fields not permitted for customer update: [totalPrice, isPaid]
200 OK -- order contents updated
200 OK -- order marked paid internally, price confirmed by payment processor
```

## 7. Gotchas & takeaways

> Object-level authorization (API1) and property-level authorization (API3) are easy to conflate — fixing one doesn't fix the other. A team that adds an ownership check to every endpoint and declares the BOLA problem solved can still be fully exposed to mass assignment on the very same, now-"fixed" endpoints, exactly as Level 2 demonstrates. Review both independently: does the caller own this object, and separately, is the caller allowed to set *every field* their request body contains?

- The OWASP API Security Top 10 is a maintained, industry-standard checklist specifically for API-shaped systems — use it during design review, not just after an incident.
- API1 (BOLA) and API3 (property-level authorization) are both authorization bugs but require separate fixes: one checks *which object*, the other checks *which fields on that object*.
- An explicit allow-list of caller-writable fields is far safer than a deny-list or blind field-by-field application of a request body — new privileged fields added later are safe by default rather than accidentally exposed.
- Privileged state transitions (marking something paid, changing a role) belong behind separate, internally-authenticated paths — never reachable from a customer-facing update endpoint at all.
- Several list items map directly onto other topics in this section: API4 to [rate limiting & throttling](0397-rate-limiting-throttling-as-security-control.md), API7 to [confused deputy / SSRF concerns at the gateway](0399-confused-deputy-ssrf-concerns-at-gateway.md), and API1/API5 to [scopes, roles & fine-grained authorization](0395-scopes-roles-fine-grained-authorization.md).
