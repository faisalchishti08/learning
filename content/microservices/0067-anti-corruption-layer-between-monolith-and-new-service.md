---
card: microservices
gi: 67
slug: anti-corruption-layer-between-monolith-and-new-service
title: "Anti-corruption layer between monolith and new service"
---

## 1. What it is

This is a specific, very common application of the general [anti-corruption layer](0057-anti-corruption-layer-acl.md) pattern: a translation layer placed between a legacy monolith and a newly extracted microservice, so the new service's clean domain model never has to bend to fit the monolith's old, often messy or inconsistent data shapes — and, just as importantly, so the monolith's aging model doesn't leak into and permanently constrain the new service's design.

## 2. Why & when

During incremental monolith decomposition, a freshly extracted service almost always still needs to exchange data with the monolith — the monolith might hold data the new service needs to read, or the new service might need to write results back. Without a translation layer, the natural shortcut is for the new service to just adopt the monolith's existing field names, id formats, and status enums directly. That shortcut is exactly how legacy quirks — a `status` field that's really three overloaded booleans jammed into one string, or a customer id format inherited from a system retired a decade ago — end up baked permanently into the brand-new service's domain model, defeating much of the point of extracting it in the first place.

Place an anti-corruption layer at this seam whenever a new service must integrate with the monolith during (or after) [incremental decomposition](0066-decomposing-a-monolith-incrementally.md), specifically to keep the new service's domain model clean and translate the monolith's legacy shapes at the boundary, not throughout the new service's internals.

## 3. Core concept

All translation logic lives in one place, at the boundary; the new service's core domain model never imports or references a monolith-shaped type.

```
Monolith                    ACL (translation only)              New Service's domain model
---------                   -----------------------              ---------------------------
legacyStatus: "A"    ---->  translate("A") = ACTIVE   ---->      OrderStatus.ACTIVE (clean enum)
custId: "CUST-000042" --->  strip legacy prefix        ---->     customerId: 42 (clean, typed)
```

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="An anti-corruption layer sits between the monolith and the new OrderService, translating legacy field shapes into the new service's clean domain model">
  <rect x="20" y="70" width="150" height="60" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="95" y="95" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Monolith</text>
  <text x="95" y="112" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">legacy shapes: "A", "CUST-000042"</text>

  <rect x="245" y="65" width="150" height="70" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="90" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Anti-Corruption</text>
  <text x="320" y="105" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Layer</text>
  <text x="320" y="122" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">translation only</text>

  <rect x="470" y="70" width="150" height="60" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="545" y="95" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">New OrderService</text>
  <text x="545" y="112" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">clean domain: ACTIVE, 42</text>

  <line x1="170" y1="100" x2="245" y2="100" stroke="#8b949e" stroke-width="1.5"/>
  <line x1="395" y1="100" x2="470" y2="100" stroke="#6db33f" stroke-width="1.5"/>
</svg>

The ACL is the only place legacy shapes and clean shapes ever meet.

## 5. Runnable example

Scenario: a new `OrderService` needs order data from the monolith, first naively adopting the monolith's raw legacy shapes directly, then fixed by introducing an anti-corruption layer to translate at the boundary, then extended to also translate a legacy write back to the monolith.

### Level 1 — Basic

```java
// File: NoAcl.java -- the new service adopts the monolith's raw, messy
// shapes DIRECTLY -- legacy status codes and prefixed ids leak straight
// into the new service's own domain logic.
import java.util.*;

public class NoAcl {
    // simulates a raw record as the monolith's legacy database returns it
    record MonolithOrderRow(String legacyStatus, String custId) {}

    static class OrderService {
        void printSummary(MonolithOrderRow row) {
            // business logic now has to know the LEGACY encoding directly -- corruption has leaked in
            String meaning = row.legacyStatus().equals("A") ? "active"
                            : row.legacyStatus().equals("C") ? "cancelled" : "unknown";
            System.out.println("Order for " + row.custId() + " is " + meaning);
        }
    }

    public static void main(String[] args) {
        new OrderService().printSummary(new MonolithOrderRow("A", "CUST-000042"));
    }
}
```

**How to run:** `javac NoAcl.java && java NoAcl` (JDK 17+).

Expected output:
```
Order for CUST-000042 is active
```

`OrderService`'s own logic now has to understand what `"A"` and `"C"` mean, and prints the raw, prefixed `CUST-000042` id verbatim — the legacy encoding has corrupted the new service's domain logic.

### Level 2 — Intermediate

```java
// File: WithAcl.java -- introduce the anti-corruption layer: it is the
// ONLY place that knows about legacy status codes and id prefixes.
// OrderService now works entirely with a clean domain model.
import java.util.*;

public class WithAcl {
    record MonolithOrderRow(String legacyStatus, String custId) {}

    enum OrderStatus { ACTIVE, CANCELLED, UNKNOWN } // clean domain type

    record Order(int customerId, OrderStatus status) {} // clean domain model

    static class MonolithOrderAcl { // the anti-corruption layer
        Order translate(MonolithOrderRow row) {
            OrderStatus status = switch (row.legacyStatus()) {
                case "A" -> OrderStatus.ACTIVE;
                case "C" -> OrderStatus.CANCELLED;
                default -> OrderStatus.UNKNOWN;
            };
            int customerId = Integer.parseInt(row.custId().replace("CUST-", ""));
            return new Order(customerId, status);
        }
    }

    static class OrderService {
        void printSummary(Order order) { // knows NOTHING about legacy shapes
            System.out.println("Order for customer " + order.customerId() + " is " + order.status());
        }
    }

    public static void main(String[] args) {
        MonolithOrderAcl acl = new MonolithOrderAcl();
        Order order = acl.translate(new MonolithOrderRow("A", "CUST-000042"));
        new OrderService().printSummary(order);
    }
}
```

**How to run:** `javac WithAcl.java && java WithAcl` (JDK 17+).

Expected output:
```
Order for customer 42 is ACTIVE
```

`OrderService.printSummary` now takes a clean `Order` with a typed `OrderStatus` enum and an `int customerId` — it never sees `"A"` or `"CUST-000042"` at all. Every bit of legacy-format knowledge is isolated inside `MonolithOrderAcl`.

### Level 3 — Advanced

```java
// File: BidirectionalAcl.java -- extend the ACL to also translate the
// OTHER direction: the clean domain model back into the legacy shape,
// for when the new service must write a result back into the monolith.
// Also guard against an unrecognized legacy status instead of silently
// mapping it to UNKNOWN.
import java.util.*;

public class BidirectionalAcl {
    record MonolithOrderRow(String legacyStatus, String custId) {}
    enum OrderStatus { ACTIVE, CANCELLED }
    record Order(int customerId, OrderStatus status) {}

    static class UnrecognizedLegacyStatusException extends RuntimeException {
        UnrecognizedLegacyStatusException(String code) { super("unrecognized legacy status: " + code); }
    }

    static class MonolithOrderAcl {
        Order fromLegacy(MonolithOrderRow row) {
            OrderStatus status = switch (row.legacyStatus()) {
                case "A" -> OrderStatus.ACTIVE;
                case "C" -> OrderStatus.CANCELLED;
                default -> throw new UnrecognizedLegacyStatusException(row.legacyStatus());
            };
            int customerId = Integer.parseInt(row.custId().replace("CUST-", ""));
            return new Order(customerId, status);
        }

        MonolithOrderRow toLegacy(Order order) { // the REVERSE translation, for writing back
            String legacyStatus = order.status() == OrderStatus.ACTIVE ? "A" : "C";
            String custId = "CUST-" + String.format("%06d", order.customerId());
            return new MonolithOrderRow(legacyStatus, custId);
        }
    }

    public static void main(String[] args) {
        MonolithOrderAcl acl = new MonolithOrderAcl();

        Order order = acl.fromLegacy(new MonolithOrderRow("A", "CUST-000042"));
        System.out.println("Translated in: customer " + order.customerId() + ", " + order.status());

        Order cancelled = new Order(order.customerId(), OrderStatus.CANCELLED);
        MonolithOrderRow written = acl.toLegacy(cancelled);
        System.out.println("Translated out: legacyStatus=" + written.legacyStatus() + ", custId=" + written.custId());

        try {
            acl.fromLegacy(new MonolithOrderRow("X", "CUST-000099"));
        } catch (UnrecognizedLegacyStatusException e) {
            System.out.println("Guarded: " + e.getMessage());
        }
    }
}
```

**How to run:** `javac BidirectionalAcl.java && java BidirectionalAcl` (JDK 17+).

Expected output:
```
Translated in: customer 42, ACTIVE
Translated out: legacyStatus=C, custId=CUST-000042
Guarded: unrecognized legacy status: X
```

## 6. Walkthrough

1. **Level 1** — `OrderService.printSummary` receives the monolith's `MonolithOrderRow` directly and has to embed a ternary chain decoding `"A"`/`"C"` right inside its own business logic, and prints the raw `CUST-000042` id unchanged. Every future piece of `OrderService` logic that needs order status now risks re-implementing that same legacy decoding, and the new service's domain model is, in effect, just the monolith's model wearing a different class name.
2. **Level 2 — the ACL is introduced** — `MonolithOrderAcl.translate` becomes the single place that understands `"A"` means `OrderStatus.ACTIVE`, `"C"` means `OrderStatus.CANCELLED`, and that a `CUST-` prefix needs stripping to get a clean integer id. `main` calls `acl.translate(row)` first, producing a clean `Order`, and only *then* passes that clean `Order` into `OrderService.printSummary`, which now operates purely on the `OrderStatus` enum and an `int` — it has no idea the source data ever looked like `"A"`/`CUST-000042`.
3. **Level 3 — bidirectional and guarded** — `fromLegacy` is the same inbound translation as Level 2, renamed to make the direction explicit now that a `toLegacy` counterpart exists. `main` first calls `fromLegacy` on the sample row, producing an `Order` for customer 42 in `ACTIVE` status, printed directly. It then constructs a new `Order` for the same customer but with `CANCELLED` status (simulating a decision made inside the new service) and passes it to `toLegacy`, which reverses the translation: `CANCELLED` becomes `"C"`, and `42` is re-formatted back into the monolith's zero-padded `CUST-000042` shape — this is the write path, used when the new service needs to persist a result back into the monolith's own storage or API.
4. **Guard against unrecognized input** — the last call in `main` passes a row with `legacyStatus` `"X"`, which matches neither `"A"` nor `"C"`. Instead of Level 2's silent fallback to an `UNKNOWN` status (which could quietly propagate bad data deeper into the new service), `fromLegacy` now throws `UnrecognizedLegacyStatusException`, caught by `main` and printed as a `Guarded:` line — surfacing the legacy data problem loudly at the translation boundary, exactly where it's cheapest and clearest to fix, rather than passing a mystery status further downstream.
5. **What stays isolated** — across all three calls in Level 3's `main`, `MonolithOrderRow` (the legacy shape) and `Order`/`OrderStatus` (the clean shape) never mix outside `MonolithOrderAcl`. Any other class in the new service that needs order data works only with `Order` and never needs to know the monolith's encoding exists at all.

## 7. Gotchas & takeaways

> **Gotcha:** an anti-corruption layer that only translates *inbound* data (monolith to new service) but lets the new service write directly back to the monolith in its raw legacy format is only half a boundary — legacy shapes still leak in through the write path. Translate both directions, as `toLegacy` does here, whenever the new service needs to write back.

- The ACL is the single seam where legacy and clean shapes are allowed to meet — everywhere else in the new service should only ever see the clean domain model.
- Treat an unrecognized legacy value as a hard error at the boundary (as `fromLegacy` does for `"X"`), not a silent default — silent defaults hide real data problems until they surface much further downstream, and harder to diagnose.
- This pattern is a specific case of the general [anti-corruption layer](0057-anti-corruption-layer-acl.md) concept, applied specifically at the monolith/new-service seam during [incremental decomposition](0066-decomposing-a-monolith-incrementally.md).
- Keep translation logic centralized in one class (or a small, cohesive set of classes) — scattering ad-hoc translation snippets across the new service recreates the exact problem the ACL exists to prevent.
- An ACL is meant to be temporary scaffolding around the monolith seam specifically, not a permanent architectural layer — as the monolith's role shrinks (see [decomposing a monolith incrementally](0066-decomposing-a-monolith-incrementally.md)), the amount of translation logic needed should shrink with it.
