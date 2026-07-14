---
card: microservices
gi: 524
slug: inappropriate-intimacy-leaky-boundaries
title: "Inappropriate intimacy / leaky boundaries"
---

## 1. What it is

**Inappropriate intimacy** (or a **leaky boundary**) is when a service exposes, or a caller depends on, internal implementation details that should have stayed hidden — internal ID formats, internal state machines, internal database structure, or assumptions about how the service does its work internally — instead of communicating purely through a well-defined API contract. The service *looks* encapsulated because it's a separate deployable with its own API, but callers have quietly built assumptions about its internals, so the service can no longer change those internals without breaking callers, even though the API contract itself never changed.

## 2. Why & when

You guard against leaky boundaries because they defeat the purpose of having a service boundary at all, often while looking perfectly correct on the surface:

- **A service boundary's whole value is that internals can change freely as long as the contract holds.** If a caller depends on something the contract doesn't actually promise — an internal ID's numeric format, the exact order fields appear in a JSON response, an internal status value that was never meant to be public, a database-generated timestamp format — the service has lost the freedom to change that internal detail, even though its documented API never promised it.
- **Leaks often happen through the path of least resistance**, not carelessness: it's easier to expose an internal enum directly than to define a stable public one, easier to let an internal database ID leak into a response than to mint a separate public identifier, easier to document "the real current behavior" than to decide what the contract *should* guarantee.
- **The symptom looks like a shared-database problem but happens purely through the API** — no table is shared, but the API return value inadvertently reveals internal structure (nested internal object graphs, implementation-specific error codes, an internal microservice's name in an error message) that callers then depend on, recreating the same brittleness a shared table would.
- **The fix is a deliberate, minimal, explicit contract** — decide exactly what the API promises (field names, types, guaranteed values, stability guarantees), document it, and make sure the implementation is free to change anything not explicitly promised, using a mapping/translation layer between internal representation and public contract if the two would otherwise be tempted to drift together.

## 3. Core concept

Think of a restaurant that lets customers watch the kitchen prepare food through a window, purely so they can enjoy the show — and a regular customer starts timing their own arrival based on watching exactly when the chef starts chopping onions for their specific dish, because that's the visible signal they've learned to rely on. If the kitchen ever changes its prep order (starts the onions later, prepares them in a different station), that customer's carefully-tuned timing breaks — even though the restaurant never promised anything about *when* onions get chopped, only that the dish would eventually arrive. The menu (the API contract) is the actual promise; anything visible through the window that isn't on the menu is an implementation detail the kitchen should be free to change without warning.

Concretely:

1. **A contract should explicitly enumerate what's guaranteed**: field names and types that will be present, value ranges or enums that are stable, ordering guarantees (or explicitly, the lack of them) — everything else is an implementation detail.
2. **Callers should only ever depend on what's explicitly promised**, never on incidental details that happen to be true today — an internal numeric ID's format, an internal service's name appearing in a log or error message, the specific order of fields in a JSON object.
3. **The service side needs a translation layer** between its internal representation (which should change freely, driven by internal needs) and its public contract (which changes rarely, and only deliberately, often behind a version bump) — without this layer, internal changes leak straight through to the API by default.
4. **A leak is often only discovered when the internal thing changes and a caller breaks** — which means guarding against leaks requires deliberately reviewing "what does our API actually promise, versus what does it happen to currently return," not waiting for an incident to reveal the gap.

## 4. Diagram

<svg viewBox="0 0 660 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Leaky boundary: caller depends on internal details never promised by the contract; fixed version: a translation layer exposes only the explicit contract">
  <text x="150" y="20" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif" font-weight="bold">Leaky boundary</text>
  <rect x="20" y="35" width="260" height="34" rx="4" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="150" y="56" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Service internals (DB row, enum, ID format)</text>
  <line x1="150" y1="69" x2="150" y2="100" stroke="#f0883e" stroke-width="2"/>
  <rect x="20" y="100" width="260" height="34" rx="4" fill="#1c2430" stroke="#f0883e" stroke-width="2"/>
  <text x="150" y="121" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Caller depends on internal shape directly</text>
  <text x="150" y="150" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">internal change breaks caller, contract "never changed"</text>

  <text x="510" y="20" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif" font-weight="bold">Fixed: explicit contract</text>
  <rect x="380" y="35" width="260" height="34" rx="4" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="510" y="56" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Service internals (free to change)</text>
  <line x1="510" y1="69" x2="510" y2="85" stroke="#6db33f" stroke-width="2"/>
  <rect x="380" y="85" width="260" height="24" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="510" y="101" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">translation layer</text>
  <rect x="380" y="115" width="260" height="30" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="510" y="134" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">stable public contract</text>
</svg>

Without a translation layer, internal details leak straight into the API by default; a deliberate mapping layer keeps the contract stable while internals evolve freely.

## 5. Runnable example

Scenario: an Order service whose response accidentally exposes an internal database row ID and an internal-only status code. We start with the leaky version, show a caller that (reasonably) starts depending on the leaked details, then handle the fix: a translation layer producing a minimal, explicit, stable contract.

### Level 1 — Basic

```java
// File: LeakyOrderApi.java -- the internal representation is returned
// DIRECTLY as the API response, leaking internal DB ids and status codes.
import java.util.*;

public class LeakyOrderApi {
    // internal representation: whatever the database happens to store
    static class InternalOrderRow {
        long dbAutoIncrementId; // internal primary key, an implementation detail
        int internalStatusCode; // 0=draft, 1=submitted, 2=fulfilled -- internal enum, never meant to be public
        String customerName;
        InternalOrderRow(long id, int status, String name) { dbAutoIncrementId = id; internalStatusCode = status; customerName = name; }
    }

    static InternalOrderRow fetchOrder(long id) {
        return new InternalOrderRow(id, 1, "Alice"); // status 1 = "submitted", an internal detail
    }

    // the API just returns the internal object AS-IS
    static Map<String, Object> getOrderApi(long id) {
        InternalOrderRow row = fetchOrder(id);
        return Map.of("dbAutoIncrementId", row.dbAutoIncrementId, "internalStatusCode", row.internalStatusCode, "customerName", row.customerName);
    }

    public static void main(String[] args) {
        System.out.println(getOrderApi(42));
        System.out.println("Leak: callers now see dbAutoIncrementId and internalStatusCode -- neither was ever meant to be public");
    }
}
```

How to run: `java LeakyOrderApi.java`

`getOrderApi` returns the internal row's fields directly, unfiltered — `dbAutoIncrementId` (a raw database primary key) and `internalStatusCode` (a bare integer meant only for internal logic) both leak straight through, even though nothing in this design ever decided those should be part of the public contract.

### Level 2 — Intermediate

```java
// File: CallerDependsOnLeak.java -- a caller reasonably starts relying
// on the leaked internal details, since that's all the API exposed.
import java.util.*;

public class CallerDependsOnLeak {
    static Map<String, Object> getOrderApi(long id) {
        // same leaky shape as Level 1
        return Map.of("dbAutoIncrementId", id, "internalStatusCode", 1, "customerName", "Alice");
    }

    static boolean isOrderSubmitted(Map<String, Object> orderResponse) {
        // the caller has learned, by observation, that internalStatusCode == 1 means "submitted"
        // nothing in any contract document ever promised this -- it was reverse-engineered from behavior
        return (int) orderResponse.get("internalStatusCode") == 1;
    }

    public static void main(String[] args) {
        Map<String, Object> order = getOrderApi(42);
        System.out.println("Order submitted? " + isOrderSubmitted(order));
        System.out.println("Problem: if Order service ever renumbers its internal status codes (0=submitted, 1=fulfilled), this caller silently breaks.");
    }
}
```

How to run: `java CallerDependsOnLeak.java`

The caller's `isOrderSubmitted` hardcodes the assumption `internalStatusCode == 1` means "submitted," learned purely from observing today's behavior, not from any documented contract. If the Order service's team ever renumbers their internal enum — a change that should be completely invisible outside the service — this caller silently starts misclassifying orders, with no compiler error and no obvious failure at the point of the actual change.

### Level 3 — Advanced

```java
// File: TranslationLayerFix.java -- the FIX: a dedicated translation
// layer maps internal representation to an EXPLICIT, STABLE public
// contract with named enum values instead of bare internal integers.
import java.util.*;

public class TranslationLayerFix {
    static class InternalOrderRow {
        long dbAutoIncrementId;
        int internalStatusCode; // still free to renumber internally
        String customerName;
        InternalOrderRow(long id, int status, String name) { dbAutoIncrementId = id; internalStatusCode = status; customerName = name; }
    }

    // the PUBLIC, explicit, stable contract -- named values, no raw internal IDs
    enum PublicOrderStatus { DRAFT, SUBMITTED, FULFILLED, UNKNOWN }
    record PublicOrderResponse(String orderId, PublicOrderStatus status, String customerName) {}

    static InternalOrderRow fetchOrder(long id) {
        return new InternalOrderRow(id, 1, "Alice");
    }

    // the translation layer: the ONLY place that knows the internal status code mapping
    static PublicOrderStatus translateStatus(int internalCode) {
        return switch (internalCode) {
            case 0 -> PublicOrderStatus.DRAFT;
            case 1 -> PublicOrderStatus.SUBMITTED;
            case 2 -> PublicOrderStatus.FULFILLED;
            default -> PublicOrderStatus.UNKNOWN;
        };
    }

    static PublicOrderResponse getOrderApi(long id) {
        InternalOrderRow row = fetchOrder(id);
        // public order ID is a stable opaque string, NOT the raw database primary key
        String publicOrderId = "ORD-" + Long.toHexString(row.dbAutoIncrementId).toUpperCase();
        return new PublicOrderResponse(publicOrderId, translateStatus(row.internalStatusCode), row.customerName);
    }

    static boolean isOrderSubmitted(PublicOrderResponse response) {
        return response.status() == PublicOrderStatus.SUBMITTED; // depends on the NAMED enum, not a raw integer
    }

    public static void main(String[] args) {
        PublicOrderResponse order = getOrderApi(42);
        System.out.println(order);
        System.out.println("Order submitted? " + isOrderSubmitted(order));
        System.out.println("Fix: renumbering internalStatusCode only requires updating translateStatus -- callers never notice.");
    }
}
```

How to run: `java TranslationLayerFix.java`

`translateStatus` is the single place that knows the mapping from internal integer codes to the stable, named `PublicOrderStatus` enum — if the Order team renumbers their internal codes tomorrow, only this one function's `switch` needs updating; every caller depending on `PublicOrderStatus.SUBMITTED` is completely unaffected. Likewise, `publicOrderId` is derived from the internal ID rather than exposing it directly, so the internal ID scheme (auto-increment integers, UUIDs, anything) can change freely without callers noticing, since they only ever see the derived, stable `"ORD-..."` string.

## 6. Walkthrough

Trace `TranslationLayerFix.main` end to end:

1. **`getOrderApi(42)` is called.** It first calls `fetchOrder(42)`, which returns an `InternalOrderRow` with `dbAutoIncrementId=42`, `internalStatusCode=1`, `customerName="Alice"` — this internal representation never leaves this function.
2. **`getOrderApi` computes `publicOrderId`** by hex-encoding the internal ID and prefixing it (`"ORD-2A"`) — this is a deliberate, one-way derivation; a caller cannot reverse it back into the raw database ID, and the Order team is free to switch to a completely different internal ID scheme (say, UUIDs) as long as they can still derive *some* stable public string from it.
3. **`getOrderApi` calls `translateStatus(1)`.** Inside, the `switch` matches `case 1 -> PublicOrderStatus.SUBMITTED`, returning the named enum value — this is the one place internal-to-public status translation happens.
4. **`getOrderApi` constructs and returns a `PublicOrderResponse("ORD-2A", SUBMITTED, "Alice")`** — this record's shape *is* the contract: three fields, one of which is a named enum with a fixed, documented set of possible values, not a bare integer.
5. **`main` calls `isOrderSubmitted(order)`**, which checks `response.status() == PublicOrderStatus.SUBMITTED` — a comparison against a named, documented enum value, not a magic number reverse-engineered from observed behavior.
6. **The response prints `submitted? true`**, correctly reflecting the order's state, using only fields the contract explicitly promises.

Contrast with Level 2: there, a hypothetical future renumbering of internal status codes (say, swapping which integer means "submitted" versus "fulfilled") would immediately and silently break `isOrderSubmitted`, because it depended on the raw integer directly. Here, that same renumbering only requires updating the one `switch` statement inside `translateStatus` — `PublicOrderStatus.SUBMITTED` as a named value doesn't change, so every caller's code, including `isOrderSubmitted`, keeps working exactly as before, completely unaware that anything internal changed at all.

## 7. Gotchas & takeaways

> **Gotcha:** exposing an internal enum, status code, or ID format "temporarily" or "just for debugging" tends to become permanent the moment any real caller starts depending on it — once a detail is observable, someone will eventually build logic around it, whether or not it was ever documented as part of the contract; treat anything observable through the API as effectively promised unless a translation layer actively prevents it.

- A service boundary only provides real freedom to change internals if there's a deliberate translation layer between internal representation and public contract — without one, internal details leak through by default, not by exception.
- Prefer named, explicit values (enums, well-defined fields) over raw internal codes or IDs in any public API — a named value can be internally remapped freely; a bare integer or raw database ID cannot.
- Leaky boundaries are usually discovered only when an internal change breaks a caller — proactively audit "what does our API actually document versus what does it happen to currently return" rather than waiting for that incident.
- Deriving public identifiers (like the hex-encoded `ORD-` prefix) instead of exposing raw internal IDs directly is a small, cheap habit that prevents an entire class of future coupling on internal ID schemes.
