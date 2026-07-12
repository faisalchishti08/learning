---
card: microservices
gi: 84
slug: request-response-payload-design-dtos
title: "Request/response payload design (DTOs)"
---

## 1. What it is

A DTO (Data Transfer Object) is a plain object whose only job is to define the shape of data crossing a service boundary — a request body or response body — kept deliberately separate from the internal domain model (see [entities and value objects](0053-entities-and-value-objects.md)) used inside the service. `OrderRequestDto` and `OrderResponseDto` are not the same class as the internal `Order` aggregate, even if their fields overlap heavily today; they're separate types precisely so each can change for its own reasons.

## 2. Why & when

Returning an internal domain entity directly from an API endpoint couples the API's public contract to the service's internal implementation details — a field renamed for an internal refactor, or a new field added purely for internal bookkeeping, silently becomes a breaking (or at least surprising) change for every external consumer. It also risks leaking data that should never cross the service boundary at all — an internal `passwordHash` field or an `internalRiskScore` accidentally serialized into a public API response because it happened to be a field on the entity being returned. DTOs establish a deliberate translation point: the API's shape is designed and versioned on its own terms, independent of whatever the internal model happens to look like today.

Use dedicated DTOs for any service boundary where the internal model and the public contract have — or are likely to develop — different reasons to change: nearly every microservice's public REST API. For truly internal, throwaway code with no external consumers, the extra translation layer may not be worth the ceremony, but any endpoint another team or another service calls should have this separation.

## 3. Core concept

The DTO is a narrow, explicit view of the domain model, built or interpreted through a translation step — internal fields never leak through by accident, because nothing crosses the boundary except what the DTO's fields explicitly name.

```
Order (internal domain entity)          OrderResponseDto (public API shape)
--------------------------------        -------------------------------------
id: Long                                 id: String
customerId: Long                         customerName: String    <- looked up, not just copied
status: OrderStatus                      status: String
internalRiskScore: double                (not present -- deliberately excluded)
passwordHashOfCreator: String            (not present -- would be a serious leak)
```

## 4. Diagram

<svg viewBox="0 0 640 180" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="An internal Order entity is translated through a mapping step into a narrower OrderResponseDto that excludes internal-only fields before crossing the API boundary">
  <rect x="20" y="30" width="220" height="120" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="130" y="52" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Order (internal entity)</text>
  <text x="130" y="75" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">id, customerId, status,</text>
  <text x="130" y="90" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">internalRiskScore,</text>
  <text x="130" y="105" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">passwordHashOfCreator</text>

  <rect x="290" y="65" width="80" height="45" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="330" y="90" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">mapper</text>

  <rect x="410" y="30" width="210" height="120" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="515" y="52" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">OrderResponseDto</text>
  <text x="515" y="75" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">id, customerName, status</text>
  <text x="515" y="95" fill="#79c0ff" font-size="7" text-anchor="middle" font-family="sans-serif">(internal fields excluded)</text>

  <line x1="240" y1="90" x2="290" y2="90" stroke="#8b949e" stroke-width="1.5"/>
  <line x1="370" y1="90" x2="410" y2="90" stroke="#8b949e" stroke-width="1.5"/>
</svg>

The mapper is the single, deliberate translation point; nothing crosses the boundary except what it explicitly copies over.

## 5. Runnable example

Scenario: an order endpoint, first returning the internal entity directly (leaking an internal-only field), then fixed with a dedicated DTO and an explicit mapper, then extended so the internal model can change shape (renaming and restructuring a field) without breaking the DTO's stable public contract at all.

### Level 1 — Basic

```java
// File: LeakyDirectReturn.java -- the API returns the INTERNAL entity
// directly -- every internal field, including sensitive ones, is exposed.
import java.util.*;

public class LeakyDirectReturn {
    static class Order { // internal domain entity
        long id;
        long customerId;
        String status;
        double internalRiskScore; // NEVER meant to leave the service
        Order(long id, long customerId, String status, double internalRiskScore) {
            this.id = id; this.customerId = customerId; this.status = status; this.internalRiskScore = internalRiskScore;
        }
        public String toString() {
            return "Order{id=" + id + ", customerId=" + customerId + ", status=" + status + ", internalRiskScore=" + internalRiskScore + "}";
        }
    }

    static Order getOrder(long id) {
        return new Order(id, 999, "PLACED", 0.87); // returned AS-IS to the API caller
    }

    public static void main(String[] args) {
        System.out.println("API response body: " + getOrder(42));
    }
}
```

**How to run:** `javac LeakyDirectReturn.java && java LeakyDirectReturn` (JDK 17+).

Expected output:
```
API response body: Order{id=42, customerId=999, status=PLACED, internalRiskScore=0.87}
```

`internalRiskScore` — an internal fraud-scoring detail with no business being in a public API response — is serialized straight into the output, purely because it happens to be a field on the entity being returned.

### Level 2 — Intermediate

```java
// File: WithDedicatedDto.java -- introduce a NARROW response DTO and an
// explicit mapper -- only fields the mapper copies can ever appear
// in the API response.
import java.util.*;

public class WithDedicatedDto {
    static class Order { // internal entity, unchanged
        long id;
        long customerId;
        String status;
        double internalRiskScore;
        Order(long id, long customerId, String status, double internalRiskScore) {
            this.id = id; this.customerId = customerId; this.status = status; this.internalRiskScore = internalRiskScore;
        }
    }

    record OrderResponseDto(String id, long customerId, String status) { // deliberately narrower than Order
        public String toString() {
            return "OrderResponseDto{id=" + id + ", customerId=" + customerId + ", status=" + status + "}";
        }
    }

    static OrderResponseDto toDto(Order order) { // the ONLY place translation happens
        return new OrderResponseDto("ORD-" + order.id, order.customerId, order.status);
    }

    static Order fetchOrder(long id) {
        return new Order(id, 999, "PLACED", 0.87);
    }

    public static void main(String[] args) {
        Order internal = fetchOrder(42);
        OrderResponseDto response = toDto(internal);
        System.out.println("API response body: " + response);
    }
}
```

**How to run:** `javac WithDedicatedDto.java && java WithDedicatedDto` (JDK 17+).

Expected output:
```
API response body: OrderResponseDto{id=ORD-42, customerId=999, status=PLACED}
```

`internalRiskScore` never appears — `toDto` simply never copies it, so it structurally cannot leak, regardless of what other fields get added to `Order` in the future.

### Level 3 — Advanced

```java
// File: StableDtoThroughInternalRefactor.java -- the internal Order
// model is now RESTRUCTURED (customerId replaced by a nested Customer
// object, status becomes an enum) -- but the DTO's PUBLIC SHAPE stays
// stable, because only the mapper needs to change.
import java.util.*;

public class StableDtoThroughInternalRefactor {
    enum OrderStatus { PLACED, SHIPPED } // internal refactor: status is now a real enum, not a string

    record Customer(long id, String name) {} // internal refactor: a nested object, not a flat id

    static class Order { // internal entity -- SHAPE HAS CHANGED from Level 2
        long id;
        Customer customer;      // was: long customerId
        OrderStatus status;     // was: String status
        double internalRiskScore;
        Order(long id, Customer customer, OrderStatus status, double internalRiskScore) {
            this.id = id; this.customer = customer; this.status = status; this.internalRiskScore = internalRiskScore;
        }
    }

    record OrderResponseDto(String id, long customerId, String status) { // UNCHANGED public shape
        public String toString() {
            return "OrderResponseDto{id=" + id + ", customerId=" + customerId + ", status=" + status + "}";
        }
    }

    static OrderResponseDto toDto(Order order) { // ONLY this mapper needed to change
        return new OrderResponseDto("ORD-" + order.id, order.customer.id(), order.status.name());
    }

    static Order fetchOrder(long id) {
        return new Order(id, new Customer(999, "Jane Doe"), OrderStatus.PLACED, 0.87);
    }

    public static void main(String[] args) {
        Order internal = fetchOrder(42);
        OrderResponseDto response = toDto(internal);
        System.out.println("API response body: " + response);
        System.out.println("(internal model restructured: customerId -> nested Customer, status -> enum -- API contract UNCHANGED)");
    }
}
```

**How to run:** `javac StableDtoThroughInternalRefactor.java && java StableDtoThroughInternalRefactor` (JDK 17+).

Expected output:
```
API response body: OrderResponseDto{id=ORD-42, customerId=999, status=PLACED}
```

## 6. Walkthrough

1. **Level 1** — `getOrder` constructs and returns an `Order` directly. `main` prints its `toString()` output as if it were the API response body, and `internalRiskScore=0.87` appears in it — a real leak, since nothing about the API's *intended* contract ever meant to expose fraud-scoring internals.
2. **Level 2 — a narrow, explicit DTO** — `OrderResponseDto` declares only `id`, `customerId`, and `status` — no `internalRiskScore` field exists on it at all. `toDto` is the single translation point: it reads from `Order` and constructs an `OrderResponseDto`, explicitly choosing which fields to copy (and reformatting `id` into a prefixed string, `"ORD-" + order.id`, along the way — a small transformation the DTO layer is exactly the right place to make). `main` calls `fetchOrder` then `toDto`, and the printed response shows only the three intended fields — `internalRiskScore` structurally cannot appear, because `toDto` never reads or copies it.
3. **Level 3 — the internal model changes shape, the DTO doesn't** — `Order` is restructured: `customerId` (a flat `long`) becomes `customer` (a nested `Customer` record with its own `id` and `name`), and `status` (a `String`) becomes a real `OrderStatus` enum. This is a realistic internal refactor — the kind of change a domain model legitimately goes through as understanding deepens (see [entities and value objects](0053-entities-and-value-objects.md)).
4. **What had to change, and what didn't** — `OrderResponseDto`'s declaration is untouched from Level 2 — still `id`, `customerId`, `status`, in the same types. Only `toDto`'s *implementation* changed: it now reads `order.customer.id()` instead of `order.customerId`, and calls `.name()` on the `OrderStatus` enum to get back a `String` for the DTO's `status` field. `main` calls `fetchOrder` (now constructing the new `Order` shape) and `toDto`, and the printed API response body is **identical** to Level 2's output — `OrderResponseDto{id=ORD-42, customerId=999, status=PLACED}` — even though the internal entity's structure underneath changed substantially.
5. **Why this is the whole point of the DTO layer** — any external consumer of this API — another service, a frontend, a third-party integration — observed *zero* change across this internal refactor. If the API had instead returned `Order` directly (as in Level 1), restructuring `customerId` into a nested `Customer` object would have been a breaking change to the JSON shape every consumer receives, forcing coordinated updates everywhere at once. The DTO and its mapper absorbed the entire internal change, leaving the public contract stable.

## 7. Gotchas & takeaways

> **Gotcha:** it's tempting to skip the DTO layer "for now" on a new endpoint, planning to add it later once the API has external consumers — but by then, the internal entity's shape has often already been serialized directly into client expectations, making the DTO's introduction itself a breaking change. Introduce the DTO from the start, even when the DTO and the entity look identical on day one.

- A DTO's job is to define a *deliberate, stable* public contract, independent of whatever the internal domain model happens to look like right now.
- The mapper (`toDto`) is the single, explicit translation point — nothing crosses the service boundary except what it deliberately copies, which is exactly what prevents accidental leaks of internal-only fields.
- An internal model can be freely refactored — fields renamed, restructured, or replaced — without breaking external consumers, as long as only the mapper (not the DTO's public shape) needs to change.
- Keep request DTOs separate from response DTOs even when their fields overlap today — a create request and a read response often diverge in exactly the fields that matter (e.g., a request DTO has no `id` yet; a response DTO always does).
- See [JSON / Protobuf / Avro serialization](0085-json-protobuf-avro-serialization.md) for how a DTO's fields actually get encoded onto the wire once its shape is settled.
