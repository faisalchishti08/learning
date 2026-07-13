---
card: microservices
gi: 311
slug: data-ownership-system-of-record
title: "Data ownership & system of record"
---

## 1. What it is

For any given piece of data, exactly one service is its system of record — the single, authoritative source that is allowed to write it and that all other services must ultimately trust as correct. Every other place that data appears — a [duplicated copy](0308-data-duplication-denormalization-across-services.md) in another service, a [CQRS read model](0314-cqrs-read-models-materialized-views.md), a cache — is a derived view, never a second place data can be independently written from. Data ownership is the explicit design decision of which service that authoritative owner is, for each distinct piece of information in the system.

## 2. Why & when

Without a clearly designated owner, it becomes ambiguous which service's value is "correct" when two services' copies of the same conceptual data disagree — and worse, if more than one service can *write* that data, conflicting writes have no principled way to be resolved, since there's no single authority to defer to. Assigning ownership explicitly (usually, though not always, to the service whose core responsibility the data most naturally belongs to — `CustomerService` owns customer names and addresses, `InventoryService` owns stock counts) makes conflict resolution trivial by construction: the owner's value is always correct, and every other copy is understood to be a potentially-stale derivative that must eventually converge toward it.

Establish ownership explicitly and document it (in a data ownership map, in architecture documentation, in code comments on the owning entity) for every meaningfully important piece of data in the system, before duplication or CQRS read models are introduced — retrofitting ownership onto a system where multiple services already write the "same" data ad hoc is far harder than designing it in from the start. Use this as the governing rule for every decision about where writes are allowed to happen: if a service isn't the system of record for some data, it should never accept a write that changes that data's authoritative value, only relay the write to the actual owner or accept a request that the owner then processes.

## 3. Core concept

Only the owning service exposes a write path for a given piece of data; every other service exposes, at most, a read-only, clearly-labeled derived copy.

```java
// CustomerService: the SYSTEM OF RECORD for customer names/addresses.
@Service
class CustomerService {
    public void updateAddress(String customerId, Address newAddress) {
        customerRepository.save(customerId, newAddress); // the ONLY place this can be authoritatively written
        eventPublisher.publish(new CustomerAddressChangedEvent(customerId, newAddress));
    }
}

// ShippingService: holds a DERIVED, read-only copy -- NEVER writes it
// authoritatively, only updates its local copy in REACTION to the owner's event.
@Service
class ShippingService {
    @EventListener
    void onCustomerAddressChanged(CustomerAddressChangedEvent event) {
        shippingAddressCache.update(event.customerId(), event.newAddress()); // DERIVED update, not authoritative
    }
    // NOTE: ShippingService exposes NO method to change a customer's address directly.
}
```

## 4. Diagram

<svg viewBox="0 0 640 160" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="CustomerService is the single system of record for customer address data, the only service permitted to write it authoritatively; ShippingService and BillingService each hold a derived, read-only copy, updated only in reaction to events published by the owning service, never written independently">
  <rect x="230" y="20" width="180" height="45" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="40" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">CustomerService</text>
  <text x="320" y="55" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">SYSTEM OF RECORD (writes here)</text>

  <line x1="270" y1="65" x2="130" y2="105" stroke="#8b949e" stroke-dasharray="3,3" marker-end="url(#arr311)"/>
  <line x1="370" y1="65" x2="510" y2="105" stroke="#8b949e" stroke-dasharray="3,3" marker-end="url(#arr311)"/>

  <rect x="50" y="110" width="160" height="35" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="130" y="132" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">ShippingService (read-only copy)</text>

  <rect x="430" y="110" width="160" height="35" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="510" y="132" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">BillingService (read-only copy)</text>

  <defs><marker id="arr311" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Only the owning service writes authoritatively; every other service's copy is derived and updated only via events from the owner.

## 5. Runnable example

Scenario: two services independently allowed to write the "same" customer address, producing an unresolvable conflict, extended to a single designated owner with every other service holding only a derived, read-only copy, and finally showing how a write attempted against a non-owning service is correctly redirected/rejected rather than silently accepted.

### Level 1 — Basic

```java
// File: NoDesignatedOwner.java -- BOTH CustomerService and ShippingService
// can independently write "the customer's address" -- there is no
// designated owner, so when they disagree, there is no principled way
// to know which value is correct.
import java.util.*;

public class NoDesignatedOwner {
    static Map<String, String> customerServiceAddresses = new HashMap<>(Map.of("cust-1", "123 Main St"));
    static Map<String, String> shippingServiceAddresses = new HashMap<>(Map.of("cust-1", "123 Main St"));

    static void updateAddressViaCustomerService(String customerId, String newAddress) {
        customerServiceAddresses.put(customerId, newAddress); // writes ITS OWN copy only
    }
    static void updateAddressViaShippingService(String customerId, String newAddress) {
        shippingServiceAddresses.put(customerId, newAddress); // writes ITS OWN copy only, INDEPENDENTLY
    }

    public static void main(String[] args) {
        updateAddressViaCustomerService("cust-1", "456 Oak Ave"); // customer updates via CustomerService's UI
        updateAddressViaShippingService("cust-1", "789 Pine Rd"); // a DIFFERENT update lands via ShippingService's UI

        System.out.println("CustomerService thinks the address is: " + customerServiceAddresses.get("cust-1"));
        System.out.println("ShippingService thinks the address is: " + shippingServiceAddresses.get("cust-1"));
        System.out.println("Which one is CORRECT? There is no principled answer -- neither service is the designated owner.");
    }
}
```

How to run: `java NoDesignatedOwner.java`

Both services accept independent writes to what is conceptually the same fact (a customer's address), and end up disagreeing — `"456 Oak Ave"` versus `"789 Pine Rd"` — with no mechanism to determine which is correct, because neither was ever designated as the authoritative owner. This is exactly the kind of unresolvable conflict that ownership ambiguity produces.

### Level 2 — Intermediate

```java
// File: DesignatedOwnerWithDerivedCopy.java -- CustomerService is the
// EXPLICIT system of record; ShippingService holds a read-only DERIVED
// copy, updated ONLY in reaction to CustomerService's events, never
// written independently.
import java.util.*;

public class DesignatedOwnerWithDerivedCopy {
    static class CustomerService {
        Map<String, String> addresses = new HashMap<>(Map.of("cust-1", "123 Main St")); // AUTHORITATIVE
        List<Runnable> subscribers = new ArrayList<>();

        void updateAddress(String customerId, String newAddress) {
            addresses.put(customerId, newAddress); // the ONLY authoritative write path
            subscribers.forEach(Runnable::run); // notify derived copies
        }
    }

    static class ShippingService {
        Map<String, String> addressCache = new HashMap<>(); // DERIVED, read-only from the OUTSIDE's perspective
        CustomerService customerService;

        ShippingService(CustomerService customerService) {
            this.customerService = customerService;
            customerService.subscribers.add(this::syncFromOwner); // reacts to the OWNER's changes
        }
        void syncFromOwner() { addressCache.putAll(customerService.addresses); } // NEVER writes customerService.addresses directly
        // NOTE: no updateAddress() method exists here -- ShippingService cannot write this data at all.
    }

    public static void main(String[] args) {
        CustomerService customerService = new CustomerService();
        ShippingService shippingService = new ShippingService(customerService);
        shippingService.syncFromOwner(); // initial sync

        customerService.updateAddress("cust-1", "456 Oak Ave"); // the ONLY place this can change

        System.out.println("CustomerService (owner): " + customerService.addresses.get("cust-1"));
        System.out.println("ShippingService (derived copy): " + shippingService.addressCache.get("cust-1")
                + " -- ALWAYS matches the owner, by construction, since it can never diverge via an independent write.");
    }
}
```

How to run: `java DesignatedOwnerWithDerivedCopy.java`

`CustomerService.updateAddress` is the only method anywhere in this program that can change an address's authoritative value. `ShippingService` has no equivalent write method at all — it can only `syncFromOwner`, pulling the current truth from `CustomerService`. After the update, both services report the identical address, `"456 Oak Ave"`, not because they happened to agree, but because `ShippingService`'s value is structurally derived from, and can never diverge independently from, the owner's.

### Level 3 — Advanced

```java
// File: RejectedNonOwnerWrite.java -- demonstrates the CORRECT handling
// when a write request for owned data arrives at a NON-owning service:
// it must be REDIRECTED to (or rejected in favor of) the actual owner,
// never silently accepted and applied locally, which would recreate the
// Level 1 conflict.
import java.util.*;

public class RejectedNonOwnerWrite {
    static class CustomerService {
        Map<String, String> addresses = new HashMap<>(Map.of("cust-1", "123 Main St"));
        void updateAddress(String customerId, String newAddress) { addresses.put(customerId, newAddress); }
    }

    static class ShippingService {
        Map<String, String> addressCache = new HashMap<>(Map.of("cust-1", "123 Main St"));
        CustomerService customerService; // knows WHO the real owner is
        ShippingService(CustomerService customerService) { this.customerService = customerService; }

        // A request arrives at ShippingService asking to change an address --
        // perhaps a UI mistake, or a legitimate need routed to the wrong service.
        String handleAddressUpdateRequest(String customerId, String newAddress) {
            // CORRECT behavior: ShippingService does NOT write its own cache directly.
            // It either forwards the request to the actual owner, or rejects it outright.
            return "REJECTED at ShippingService: address is owned by CustomerService. "
                    + "Forwarding request to the actual owner instead of writing locally.";
        }
    }

    public static void main(String[] args) {
        CustomerService customerService = new CustomerService();
        ShippingService shippingService = new ShippingService(customerService);

        // A misdirected request arrives at ShippingService.
        String result = shippingService.handleAddressUpdateRequest("cust-1", "999 Wrong Blvd");
        System.out.println(result);

        // The CORRECT path: the request is instead forwarded to (or resubmitted
        // against) the actual owner.
        customerService.updateAddress("cust-1", "999 Wrong Blvd");
        System.out.println("After forwarding to the ACTUAL owner: CustomerService.addresses = " + customerService.addresses.get("cust-1"));
        System.out.println("ShippingService's cache is STILL stale until the next event/sync: " + shippingService.addressCache.get("cust-1")
                + " -- correctly stale, NOT incorrectly diverged, since it was never independently written.");
    }
}
```

How to run: `java RejectedNonOwnerWrite.java`

A request to change an address arrives at `ShippingService`, which is *not* the owner. Instead of silently applying it to its own local `addressCache` (which would recreate Level 1's conflict — `ShippingService`'s copy diverging from `CustomerService`'s truth via an independent write), `handleAddressUpdateRequest` explicitly refuses to write locally and describes forwarding the request to the real owner. The actual write then happens through `customerService.updateAddress` — the sole authoritative path. `ShippingService`'s cache is temporarily stale (it hasn't re-synced yet) but critically, it is *stale*, not *wrong* or *diverged* — a state fully understood and expected within the system's ownership model, distinct from the unresolvable disagreement in Level 1.

## 6. Walkthrough

Trace `RejectedNonOwnerWrite.main` in order. **First**, both `customerService.addresses` and `shippingService.addressCache` start with the identical value `"123 Main St"` for `"cust-1"`.

**`shippingService.handleAddressUpdateRequest("cust-1", "999 Wrong Blvd")` is called.** Inside, the method does *not* touch `addressCache` at all — there is no line writing to it. Instead, it returns a descriptive string explaining that this data is owned by `CustomerService` and that the request should be forwarded there. This is the critical design decision made visible: `ShippingService` knows it is not authoritative for this data and structurally refuses to pretend otherwise, even though nothing would have stopped it, mechanically, from just calling `addressCache.put(...)` directly.

**`main` prints this rejection message**, then explicitly performs the "forwarding" by calling `customerService.updateAddress("cust-1", "999 Wrong Blvd")` directly — representing what a real system would do automatically (route the original request to the owning service's API), shown here as an explicit follow-up call for clarity. Inside `updateAddress`, `addresses.put("cust-1", "999 Wrong Blvd")` executes, and this is the only place in the entire program where this specific value is authoritatively established.

**`customerService.addresses.get("cust-1")` is printed**, correctly showing the new value, `"999 Wrong Blvd"` — the owner's value has been updated through its sole legitimate write path.

**`shippingService.addressCache.get("cust-1")` is printed last**, still showing the *old* value, `"123 Main St"` — because no sync event was triggered in this simplified example (unlike Level 2's `subscribers`/`syncFromOwner` mechanism). This staleness is expected and benign: `ShippingService`'s cache will eventually catch up once the next sync or event arrives, and in the meantime, it is honestly out of date rather than silently, permanently diverged the way Level 1's independent write would have produced.

```
handleAddressUpdateRequest() arrives at ShippingService (NON-owner)
        |
        v
NO local write happens -- request is REJECTED/FORWARDED, not silently applied
        |
        v
customerService.updateAddress()   <- the ONLY authoritative write path
        |
        v
CustomerService.addresses updated immediately
ShippingService.addressCache: temporarily STALE (expected), will catch up via the next sync/event
```

## 7. Gotchas & takeaways

> A service that "helpfully" accepts and applies a write for data it doesn't own — even with good intentions, even if it seems harmless in the moment — reintroduces exactly the unresolvable-conflict problem ownership is meant to prevent. The discipline only works if every non-owning service consistently refuses to write authoritative data locally, with no exceptions made for convenience.

- For every meaningfully important piece of data, explicitly designate exactly one owning service before other services begin duplicating or caching it — this single decision is what makes every later consistency question answerable.
- A non-owning service's copy of owned data should always be understood and labeled as *derived* — updated only in reaction to the owner's changes (typically via events), never written to independently.
- A write request for owned data arriving at a non-owning service must be rejected or forwarded to the actual owner, never silently applied locally, even if applying it locally would be mechanically easy to implement.
- Staleness in a derived copy (a temporary lag before the next sync/event) is an expected, benign, and well-understood consequence of this model — it is fundamentally different from and much easier to reason about than an unresolvable conflict between two independently-writable "sources of truth" for the same fact.
