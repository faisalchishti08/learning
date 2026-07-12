---
card: microservices
gi: 9
slug: decentralized-data-management
title: Decentralized data management
---

## 1. What it is

**Decentralized data management** is the Lewis & Fowler characteristic that says each service should own and manage its own data, rather than every service reading and writing a single shared database. Other services never reach into a service's storage directly — they go through that service's API. This mirrors decentralized governance's idea (own the implementation, share only the contract), but applied specifically to data: own the storage, share only the API.

## 2. Why & when

A single shared database is simple at first: one schema, one place to look, and cross-entity joins are trivial. Its downside grows with the system: any service touching the shared schema can be broken by another service's migration, changing one table's shape becomes a coordination exercise across every team that reads it, and there is no way to enforce that a piece of data is only ever modified through the business rules of the service that's supposed to own it — any service with a database connection can write directly to any table.

Decentralize data management once services genuinely need to evolve their storage independently — different scaling needs, different consistency requirements, or simply wanting to change a schema without a cross-team migration meeting. The real cost this introduces is consistency: without one shared transaction spanning all the data, keeping duplicated or related data in sync across services becomes an explicit, ongoing design problem (typically solved with events), not something the database engine handles for you automatically.

## 3. Core concept

The rule is simple to state and easy to violate accidentally: **a service's data is private to that service.** Any other service that needs it must ask through the owning service's API — never by querying its database directly, even if that database happens to be technically reachable.

- **Centralized data:** `OrderService` reads a customer's email straight out of a shared `customers` table.
- **Decentralized data:** `OrderService` asks `CustomerService`, "what's this customer's email?" over an API call — `CustomerService`'s database schema could change completely and `OrderService` would never notice, as long as the API contract holds.

The hard part decentralization introduces: if `OrderService` wants to avoid an API call on every single order lookup, it may keep its *own* local copy of the customer's email — which is now a second copy of the same fact, and needs a deliberate mechanism (usually an event) to stay in sync when the original changes.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Centralized data has every service reading and writing one shared database directly; decentralized data has each service own its private data, accessed only through its API, with events keeping duplicated copies in sync">
  <text x="150" y="20" fill="#8b949e" font-size="12" text-anchor="middle" font-family="sans-serif">Shared database</text>
  <rect x="30" y="35" width="90" height="35" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="75" y="57" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">OrderService</text>
  <rect x="150" y="35" width="90" height="35" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="195" y="57" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">CustomerService</text>
  <rect x="70" y="90" width="130" height="35" rx="5" fill="#1c2430" stroke="#f0883e" stroke-width="1.5"/>
  <text x="135" y="112" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">one shared DB</text>
  <line x1="75" y1="70" x2="120" y2="90" stroke="#8b949e" marker-end="url(#a9)"/>
  <line x1="195" y1="70" x2="150" y2="90" stroke="#8b949e" marker-end="url(#a9)"/>

  <text x="500" y="20" fill="#8b949e" font-size="12" text-anchor="middle" font-family="sans-serif">Decentralized data</text>
  <rect x="380" y="35" width="100" height="35" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="430" y="57" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">OrderService</text>
  <rect x="380" y="90" width="100" height="30" rx="5" fill="#1c2430" stroke="#8b949e"/>
  <text x="430" y="110" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">own DB</text>

  <rect x="510" y="35" width="110" height="35" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="565" y="57" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">CustomerService</text>
  <rect x="510" y="90" width="110" height="30" rx="5" fill="#1c2430" stroke="#8b949e"/>
  <text x="565" y="110" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">own DB</text>

  <line x1="480" y1="52" x2="510" y2="52" stroke="#f0883e" stroke-width="1.5" marker-end="url(#a9)"/>
  <text x="495" y="145" fill="#f0883e" font-size="7.5" text-anchor="middle" font-family="sans-serif">API call, no direct DB access</text>
  <defs><marker id="a9" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Shared storage couples every reader to one schema; private storage per service couples readers only to an API.

## 5. Runnable example

Scenario: `OrderService` needing a customer's email, first by reaching directly into a shared data store, then through `CustomerService`'s own API with private storage, then with a local cache kept eventually consistent via events.

### Level 1 — Basic

```java
// File: SharedDatabase.java -- OrderService reads CustomerService's data DIRECTLY
import java.util.*;

public class SharedDatabase {
    // ONE shared "database" both services read and write directly -- no ownership boundary
    static Map<String, String> customerEmails = new HashMap<>(Map.of("cust-1", "alice@example.com"));
    static List<String> orders = new ArrayList<>();

    static void placeOrder(String customerId, String item) {
        String email = customerEmails.get(customerId); // OrderService reaches STRAIGHT into CustomerService's data
        orders.add(item + " for " + email);
        System.out.println("Order placed: " + item + " -> notify " + email);
    }

    public static void main(String[] args) {
        placeOrder("cust-1", "widget");
    }
}
```

**How to run:** `javac SharedDatabase.java && java SharedDatabase` (JDK 17+).

Expected output:
```
Order placed: widget -> notify alice@example.com
```

`placeOrder` reads `customerEmails` directly — a table that conceptually belongs to a "customer" concern, not an "order" concern. If the customer team ever renames or restructures that map, `OrderService`'s code breaks, even though nothing about ordering itself changed.

### Level 2 — Intermediate

```java
// File: PrivateData.java -- CustomerService owns its data PRIVATELY;
// OrderService can only reach it through CustomerService's own API.
import java.util.*;

public class PrivateData {
    static class CustomerService {
        private final Map<String, String> emails = new HashMap<>(Map.of("cust-1", "alice@example.com")); // PRIVATE

        String getEmail(String customerId) { // the ONLY way in -- an explicit API
            return emails.getOrDefault(customerId, "unknown@example.com");
        }
    }

    static class OrderService {
        private final CustomerService customerService; // depends on the API, not the data
        OrderService(CustomerService customerService) { this.customerService = customerService; }

        void placeOrder(String customerId, String item) {
            String email = customerService.getEmail(customerId); // API call, not a direct data reach
            System.out.println("Order placed: " + item + " -> notify " + email);
        }
    }

    public static void main(String[] args) {
        CustomerService customers = new CustomerService();
        OrderService orders = new OrderService(customers);
        orders.placeOrder("cust-1", "widget");
    }
}
```

**How to run:** `javac PrivateData.java && java PrivateData` (JDK 17+).

Expected output:
```
Order placed: widget -> notify alice@example.com
```

`CustomerService.emails` is now `private` — `OrderService` cannot see it at all, only `CustomerService.getEmail(...)`. `CustomerService` could switch its internal storage to a database, a file, or anything else, and `OrderService` would never need to change.

### Level 3 — Advanced

```java
// File: EventualConsistency.java -- OrderService keeps its OWN local copy
// of the email (for speed), kept in sync via an event when it changes.
import java.util.*;

public class EventualConsistency {
    interface CustomerChangedListener { void onCustomerChanged(String customerId, String newEmail); }

    static class CustomerService {
        private final Map<String, String> emails = new HashMap<>(Map.of("cust-1", "alice@example.com"));
        private final List<CustomerChangedListener> listeners = new ArrayList<>();

        void subscribe(CustomerChangedListener listener) { listeners.add(listener); }

        void updateEmail(String customerId, String newEmail) {
            emails.put(customerId, newEmail);
            // publish an event so any service holding a LOCAL COPY can stay in sync
            for (var listener : listeners) listener.onCustomerChanged(customerId, newEmail);
        }
    }

    static class OrderService {
        // a LOCAL, denormalized copy -- avoids an API call on every order, but must be kept in sync
        private final Map<String, String> cachedEmails = new HashMap<>();

        void onCustomerChanged(String customerId, String newEmail) {
            cachedEmails.put(customerId, newEmail); // react to the event, update the local copy
            System.out.println("[OrderService] cache updated for " + customerId + " -> " + newEmail);
        }

        void placeOrder(String customerId, String item) {
            String email = cachedEmails.getOrDefault(customerId, "unknown@example.com");
            System.out.println("Order placed: " + item + " -> notify " + email);
        }
    }

    public static void main(String[] args) {
        CustomerService customers = new CustomerService();
        OrderService orders = new OrderService();
        customers.subscribe(orders::onCustomerChanged);

        customers.updateEmail("cust-1", "alice@example.com"); // initial sync via event
        orders.placeOrder("cust-1", "widget"); // uses the LOCAL cached copy, no API call needed

        customers.updateEmail("cust-1", "alice.new@example.com"); // customer changes their email
        orders.placeOrder("cust-1", "widget"); // cache was updated by the event -- stays correct
    }
}
```

**How to run:** `javac EventualConsistency.java && java EventualConsistency` (JDK 17+).

Expected output:
```
[OrderService] cache updated for cust-1 -> alice@example.com
Order placed: widget -> notify alice@example.com
[OrderService] cache updated for cust-1 -> alice.new@example.com
Order placed: widget -> notify alice.new@example.com
```

The production-flavored hard case: `OrderService` no longer calls `CustomerService` on every `placeOrder` — it reads its own `cachedEmails` map instead, for speed. That copy would go stale the moment `CustomerService.updateEmail` runs, except `OrderService` subscribed to the change event, so its cache updates itself the instant the source of truth changes — this is decentralized data management's central hard problem, duplicated data kept *eventually* consistent through events, rather than *always* consistent through one shared transaction.

## 6. Walkthrough

1. `customers.subscribe(orders::onCustomerChanged)` registers `OrderService`'s cache-update method as a listener on `CustomerService` — this is the explicit sync mechanism decentralized data requires, since there's no shared database transaction to rely on.
2. `customers.updateEmail("cust-1", "alice@example.com")` runs first: it writes to `CustomerService`'s own private `emails` map, then loops over `listeners`, calling `orders.onCustomerChanged("cust-1", "alice@example.com")`.
3. Inside `onCustomerChanged`, `OrderService` writes into its own `cachedEmails` map — its private, local, denormalized copy of a fact that `CustomerService` actually owns.
4. `orders.placeOrder("cust-1", "widget")` reads only from `cachedEmails`, never touching `CustomerService` at all — this is the payoff of caching: no network/API call needed for this read.
5. `customers.updateEmail("cust-1", "alice.new@example.com")` runs later, simulating the customer changing their email in `CustomerService`. The same event fires, and `OrderService`'s cache is updated again — automatically, without `OrderService` polling or re-querying anything.
6. The final `placeOrder` call reads the now-updated `cachedEmails` and correctly prints the new email — proving the two copies of "this customer's email" (the source of truth in `CustomerService`, and the cache in `OrderService`) stayed in sync via the event, not via a shared table.

```
CustomerService.updateEmail("cust-1", newEmail)
        |
        v  (event fired)
OrderService.onCustomerChanged("cust-1", newEmail)
        |
        v
OrderService.cachedEmails updated  -- eventually consistent, not instantly-shared-transaction consistent
```

## 7. Gotchas & takeaways

> **Gotcha:** between the moment `CustomerService.updateEmail` runs and the moment `OrderService`'s event handler finishes, there is a real window where `OrderService`'s cached copy is stale. In this single-threaded example that window is effectively zero, but in a real distributed system with network delivery delay, an order could be placed using a just-outdated email during that window — a genuine tradeoff decentralized data management asks you to accept in exchange for not needing a distributed transaction across every read.

- Decentralized data management means each service owns its own data privately; other services access it only through that service's API, never its storage directly.
- The concrete rule: if another service can query your database table directly, your data isn't decentralized yet, no matter how many separate services you've drawn on a diagram.
- Duplicating data locally as a cache is a common, valid pattern to avoid a network call on every read — but it introduces eventual consistency, which must be handled deliberately, usually with events, rather than assumed away.
- This characteristic pairs directly with [organized around business capabilities](0005-organized-around-business-capabilities.md): the service that owns a business capability is also the service that should own the data behind it.
