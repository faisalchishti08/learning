---
card: spring-data
gi: 174
slug: spring-data-keyvalue-in-memory-map-based
title: "Spring Data KeyValue (in-memory, Map-based)"
---

## 1. What it is

Spring Data KeyValue is a lightweight, `Map`-backed implementation of the Spring Data repository abstraction — no external database at all, just a `ConcurrentHashMap` (or a pluggable alternative) underneath a full `KeyValueRepository`. It's the same generated-method-name experience as every other module in this course, minus the network round trip and the infrastructure dependency.

```java
interface CustomerRepository extends KeyValueRepository<Customer, String> {
    List<Customer> findByCity(String city);
}
```

## 2. Why & when

Every other module covered so far talks to a real external store. Spring Data KeyValue exists for the cases where that's overkill: fast unit and integration tests that shouldn't need a running database, prototypes where the storage engine isn't decided yet, or genuinely small, single-instance applications with modest data that don't need persistence beyond the JVM's lifetime.

Reach for Spring Data KeyValue when:

- Writing tests for repository-consuming code, where spinning up a real MongoDB or Redis instance is unnecessary overhead — swap in a `KeyValueRepository` and get the same interface with in-memory storage.
- Prototyping a domain model's repository interfaces before committing to a specific backing store.
- Building a genuinely small, ephemeral, single-process component where a real database would be pure ceremony.

## 3. Core concept

```
 interface CustomerRepository extends KeyValueRepository<Customer, String> { }

 save(customer)      -> map.put(id, customer)           -- no network call, no serialization
 findById(id)         -> map.get(id)
 findByCity(city)      -> map.values().stream().filter(...)   -- in-process query, derived same as any module

 Swap the backing implementation later (Mongo, JPA, Redis) WITHOUT changing calling code,
 as long as it still implements the same repository interface.
```

The repository interface calling code sees is identical whether it's backed by a `Map` or a real database — the KeyValue module is a genuine implementation of the same abstraction, not a mock.

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="The same repository interface can be backed by an in-memory Map or a real external database, interchangeably">
  <rect x="220" y="20" width="200" height="40" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="320" y="45" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">CustomerRepository</text>

  <line x1="270" y1="60" x2="180" y2="95" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a9)"/>
  <line x1="370" y1="60" x2="460" y2="95" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a9)"/>

  <rect x="60" y="100" width="220" height="40" rx="8" fill="#6db33f30" stroke="#6db33f" stroke-width="1.5"/>
  <text x="170" y="125" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">KeyValue (in-memory Map)</text>

  <rect x="360" y="100" width="220" height="40" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="470" y="125" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">MongoDB / JPA / Redis...</text>

  <defs><marker id="a9" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Calling code depends only on the repository interface; the backing implementation is an interchangeable detail.

## 5. Runnable example

The scenario: a `CustomerRepository` used by a service layer, evolving from direct in-memory `Map` usage, to a proper `KeyValueRepository`-shaped abstraction with derived queries, to swapping the backing store between an in-memory map and a JPA-style implementation without touching the service layer at all.

### Level 1 — Basic

Model the bare `Map`-backed repository, the foundation the KeyValue module builds on.

```java
import java.util.*;

public class KeyValueLevel1 {
    public static void main(String[] args) {
        CustomerRepository repo = new InMemoryCustomerRepository();
        repo.save(new Customer("c1", "Amara", "Lagos"));
        repo.save(new Customer("c2", "Bilal", "Abuja"));

        Optional<Customer> found = repo.findById("c1");
        System.out.println("Found: " + found.map(c -> c.name).orElse("none"));
    }
}

class Customer {
    String id, name, city;
    Customer(String id, String name, String city) { this.id = id; this.name = name; this.city = city; }
}

interface CustomerRepository {
    Customer save(Customer c);
    Optional<Customer> findById(String id);
}

// Stands in for a Spring Data KeyValueRepository, backed by a plain in-memory map.
class InMemoryCustomerRepository implements CustomerRepository {
    private final Map<String, Customer> store = new HashMap<>();
    public Customer save(Customer c) { store.put(c.id, c); return c; }
    public Optional<Customer> findById(String id) { return Optional.ofNullable(store.get(id)); }
}
```

How to run: `java KeyValueLevel1.java`

`InMemoryCustomerRepository` implements the same `save`/`findById` contract any other repository would — the storage detail (a `HashMap`) is invisible to anything calling through the interface.

### Level 2 — Intermediate

Add a derived query method, showing the KeyValue module supports the same derivation vocabulary as every other Spring Data module, just evaluated in-process rather than compiled to a remote query language.

```java
import java.util.*;
import java.util.stream.*;

public class KeyValueLevel2 {
    public static void main(String[] args) {
        CustomerRepository repo = new InMemoryCustomerRepository();
        repo.save(new Customer("c1", "Amara", "Lagos"));
        repo.save(new Customer("c2", "Bilal", "Lagos"));
        repo.save(new Customer("c3", "Chidi", "Abuja"));

        List<Customer> lagosCustomers = repo.findByCity("Lagos"); // derived, evaluated in-process
        for (Customer c : lagosCustomers) System.out.println("In Lagos: " + c.name);
    }
}

class Customer {
    String id, name, city;
    Customer(String id, String name, String city) { this.id = id; this.name = name; this.city = city; }
}

interface CustomerRepository {
    Customer save(Customer c);
    List<Customer> findByCity(String city);
}

class InMemoryCustomerRepository implements CustomerRepository {
    private final Map<String, Customer> store = new HashMap<>();
    public Customer save(Customer c) { store.put(c.id, c); return c; }
    public List<Customer> findByCity(String city) {
        // KeyValueRepository derives this the same way any other module does, but evaluates
        // it as an in-process predicate over the Map's values rather than a compiled remote query.
        return store.values().stream().filter(c -> c.city.equals(city)).collect(Collectors.toList());
    }
}
```

How to run: `java KeyValueLevel2.java`

`findByCity` behaves identically from the caller's perspective to a derived method on `MongoRepository` or `JpaRepository` — same method-naming rules, same return type — the difference is entirely in how the module evaluates the filter internally.

### Level 3 — Advanced

Swap the backing repository implementation between the in-memory version and a second implementation modeling a real persistent store, with a shared service layer that never changes.

```java
import java.util.*;
import java.util.stream.*;

public class KeyValueLevel3 {
    public static void main(String[] args) {
        System.out.println("--- Using in-memory KeyValue repository (e.g. for a fast test) ---");
        runWith(new InMemoryCustomerRepository());

        System.out.println("--- Using JPA-style repository (e.g. for production) ---");
        runWith(new JpaStyleCustomerRepository());
    }

    // Service layer depends ONLY on the CustomerRepository interface -- unaware which implementation it got.
    static void runWith(CustomerRepository repo) {
        CustomerService service = new CustomerService(repo);
        service.registerCustomer("c1", "Amara", "Lagos");
        service.registerCustomer("c2", "Bilal", "Lagos");
        System.out.println("Lagos customers: " + service.customersInCity("Lagos").size());
    }
}

class Customer {
    String id, name, city;
    Customer(String id, String name, String city) { this.id = id; this.name = name; this.city = city; }
}

interface CustomerRepository {
    Customer save(Customer c);
    List<Customer> findByCity(String city);
}

class InMemoryCustomerRepository implements CustomerRepository {
    private final Map<String, Customer> store = new HashMap<>();
    public Customer save(Customer c) { store.put(c.id, c); return c; }
    public List<Customer> findByCity(String city) {
        return store.values().stream().filter(c -> c.city.equals(city)).collect(Collectors.toList());
    }
}

// A second implementation of the SAME interface -- stands in for a real JPA/Mongo-backed repository.
class JpaStyleCustomerRepository implements CustomerRepository {
    private final List<Customer> table = new ArrayList<>(); // stands in for a real backing table
    public Customer save(Customer c) { table.add(c); return c; }
    public List<Customer> findByCity(String city) {
        return table.stream().filter(c -> c.city.equals(city)).collect(Collectors.toList());
    }
}

class CustomerService {
    private final CustomerRepository repo;
    CustomerService(CustomerRepository repo) { this.repo = repo; }
    void registerCustomer(String id, String name, String city) { repo.save(new Customer(id, name, city)); }
    List<Customer> customersInCity(String city) { return repo.findByCity(city); }
}
```

How to run: `java KeyValueLevel3.java`

`CustomerService` is written once, against the `CustomerRepository` interface, and works unchanged whether it's handed `InMemoryCustomerRepository` (fast, in-process, ideal for tests) or `JpaStyleCustomerRepository` (stands in for a real persistent store) — exactly the substitutability Spring Data's repository abstraction is designed to provide, with the KeyValue module as its simplest possible concrete implementation.

## 6. Walkthrough

Execution starts in `main` for Level 3. `runWith` is called twice, once per repository implementation. Each call constructs a fresh `CustomerService` wrapping the given repository, registers two customers, and asks for the Lagos ones — the service code inside `runWith` never branches on which implementation it received.

```
--- Using in-memory KeyValue repository (e.g. for a fast test) ---
Lagos customers: 2
--- Using JPA-style repository (e.g. for production) ---
Lagos customers: 2
```

Both runs produce the same result because both implementations satisfy the same `CustomerRepository` contract — `service.registerCustomer` calls `repo.save`, and `service.customersInCity` calls `repo.findByCity`, with the actual storage mechanism (a `HashMap` keyed by id, versus a flat `ArrayList` scanned linearly) completely invisible above the repository interface boundary.

## 7. Gotchas & takeaways

> Gotcha: Spring Data KeyValue's default in-memory storage does not survive a JVM restart and offers no built-in replication or persistence — reaching for it in production for anything beyond genuinely disposable or cache-like data risks silent, total data loss on restart or crash.

> Gotcha: derived queries against a KeyValue repository are evaluated with an in-process, typically linear scan over the backing map — there's no query planner or index by default, so a KeyValue-backed repository that grows large can become a performance bottleneck in ways a properly indexed real database wouldn't.

- Spring Data KeyValue implements the same repository abstraction as every other Spring Data module in this course, backed by an in-memory `Map` instead of an external store.
- It's most valuable for fast tests, prototypes, and small ephemeral components — not as a general-purpose production data store.
- Calling code that depends only on the repository interface can be swapped between a KeyValue-backed implementation and a real database implementation without any changes.
- Without an external database, there's no persistence across restarts and no query optimization beyond a linear scan — know the trade-off before reaching for it outside tests and prototypes.
