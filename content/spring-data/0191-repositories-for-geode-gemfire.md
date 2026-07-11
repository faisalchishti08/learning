---
card: spring-data
gi: 191
slug: repositories-for-geode-gemfire
title: "Repositories for Geode/GemFire"
---

## 1. What it is

`GemfireRepository<T, ID>` extends Spring Data's repository abstraction over Geode/GemFire Regions — the same generated-method-name, `@Query`-with-OQL, base-plus-custom-fragment pattern used by every other Spring Data module in this course, now backed by a distributed in-memory grid instead of a disk-backed database.

```java
interface CustomerRepository extends GemfireRepository<Customer, String> {
    List<Customer> findByCity(String city);           // derived, compiles to OQL
    @Query("SELECT * FROM /customers c WHERE c.email = $1")
    Optional<Customer> findByEmail(String email);      // hand-written OQL
}
```

## 2. Why & when

The previous two cards covered `GemfireTemplate` (direct key-value and OQL access) — the low-level API. This final card in the course closes the loop the way every store module has: layering the repository abstraction on top, so routine lookups don't need hand-written OQL, while still allowing `@Query` and custom fragments for anything more specific.

Reach for `GemfireRepository` when:

- Most operations against a Region are standard CRUD or simple property lookups — the same case every derived-method-name pattern in this course was built for.
- You want Geode-backed data access to follow the exact same repository conventions the rest of a Spring Data-based application already uses for its relational, document, or graph stores — one consistent programming model across very different backing stores.
- An operation needs OQL's full expressiveness (a join-like nested query, an aggregate) — reach for `@Query` or a custom fragment, exactly as with every other module.

## 3. Core concept

```
 interface CustomerRepository extends GemfireRepository<Customer, String> {
     List<Customer> findByCity(String city);
 }

 findByCity("Lagos")
   -> derives OQL: SELECT * FROM /customers c WHERE c.city = 'Lagos'
   -> executed against the customers Region via GemfireTemplate underneath

 repository.save(customer)     -> template.put(customer.id, customer)
 repository.findById(id)        -> template.get(id)
```

Every generated repository method ultimately calls through to the same `GemfireTemplate` operations covered in the previous two cards — the repository is a convenience layer, not a different access path.

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A generated repository method and a hand-written OQL query both delegate to the same underlying GemfireTemplate over a Region">
  <rect x="20" y="20" width="270" height="45" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="155" y="47" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">findByCity("Lagos") -- derived</text>

  <rect x="350" y="20" width="270" height="45" rx="8" fill="#6db33f30" stroke="#6db33f" stroke-width="1.5"/>
  <text x="485" y="47" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">@Query OQL -- hand-written</text>

  <rect x="180" y="100" width="280" height="40" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="320" y="125" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">GemfireTemplate / Region</text>

  <line x1="155" y1="65" x2="280" y2="95" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a23)"/>
  <line x1="485" y1="65" x2="360" y2="95" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a23)"/>
  <defs><marker id="a23" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Both derived methods and hand-written OQL queries ultimately delegate to the same underlying template and Region.

## 5. Runnable example

The scenario: a `CustomerRepository` over a Geode-backed Region, evolving from a bare `GemfireTemplate`-only baseline, to a repository with a derived query method compiling to OQL, to a repository combining a derived method, a hand-written `@Query`, and a custom fragment — the complete Spring Data pattern, now applied to an in-memory data grid to close out the course's Spring Data coverage.

### Level 1 — Basic

Model the bare `GemfireTemplate` baseline — the API the repository abstraction is about to simplify.

```java
import java.util.*;
import java.util.stream.*;

public class GemfireRepoLevel1 {
    public static void main(String[] args) {
        GemfireTemplate template = new GemfireTemplate();
        template.put("c1", new Customer("c1", "Amara", "Lagos"));
        template.put("c2", new Customer("c2", "Bilal", "Abuja"));

        // Filtering by content still means manual template-level querying, no repository convenience yet.
        List<Customer> lagosCustomers = template.query(c -> c.city.equals("Lagos"));
        for (Customer c : lagosCustomers) System.out.println("In Lagos: " + c.name);
    }
}

class Customer {
    String id, name, city;
    Customer(String id, String name, String city) { this.id = id; this.name = name; this.city = city; }
}

class GemfireTemplate {
    private final Map<String, Customer> region = new HashMap<>();
    void put(String key, Customer value) { region.put(key, value); }
    Customer get(String key) { return region.get(key); }
    List<Customer> query(java.util.function.Predicate<Customer> whereClause) {
        return region.values().stream().filter(whereClause).collect(Collectors.toList());
    }
}
```

How to run: `java GemfireRepoLevel1.java`

Every content-based lookup requires hand-writing the equivalent of a `WHERE` clause at the call site — no method-name-driven convenience yet, exactly the gap `GemfireRepository`'s derived methods close.

### Level 2 — Intermediate

Add a `GemfireRepository`-style interface with a derived method, compiling method-name derivation to an OQL-equivalent filter automatically.

```java
import java.util.*;
import java.util.stream.*;

public class GemfireRepoLevel2 {
    public static void main(String[] args) {
        CustomerRepository repo = new CustomerRepositoryImpl();
        repo.save(new Customer("c1", "Amara", "Lagos"));
        repo.save(new Customer("c2", "Bilal", "Abuja"));
        repo.save(new Customer("c3", "Chidi", "Lagos"));

        List<Customer> lagosCustomers = repo.findByCity("Lagos"); // derived -> OQL under the hood
        for (Customer c : lagosCustomers) System.out.println("In Lagos: " + c.name);
    }
}

class Customer {
    String id, name, city;
    Customer(String id, String name, String city) { this.id = id; this.name = name; this.city = city; }
}

interface CustomerRepository {
    Customer save(Customer c);
    List<Customer> findByCity(String city); // derived: SELECT * FROM /customers c WHERE c.city = $1
}

// Stands in for the Spring Data-generated OQL-backed implementation of a GemfireRepository.
class CustomerRepositoryImpl implements CustomerRepository {
    private final Map<String, Customer> region = new HashMap<>();
    public Customer save(Customer c) { region.put(c.id, c); return c; }
    public List<Customer> findByCity(String city) {
        return region.values().stream().filter(c -> c.city.equals(city)).collect(Collectors.toList());
    }
}
```

How to run: `java GemfireRepoLevel2.java`

`findByCity` is derived exactly the way every other Spring Data module's derived methods work in this course — the method name alone tells Spring Data Geode to generate the equivalent of `SELECT * FROM /customers c WHERE c.city = $1`, executed via the underlying template.

### Level 3 — Advanced

Combine a derived method, a hand-written `@Query` using OQL for an aggregate, and a custom fragment for an operation neither derivation nor a simple OQL `SELECT` expresses cleanly — the complete pattern from this entire Spring Data course, applied one last time to Geode.

```java
import java.util.*;
import java.util.stream.*;

public class GemfireRepoLevel3 {
    public static void main(String[] args) {
        CustomerRepository repo = new CustomerRepositoryImpl();
        repo.save(new Customer("c1", "Amara", "Lagos", 250.0));
        repo.save(new Customer("c2", "Bilal", "Abuja", 150.0));
        repo.save(new Customer("c3", "Chidi", "Lagos", 400.0));

        System.out.println("Derived findByCity: " + repo.findByCity("Lagos").size());
        System.out.println("@Query totalSpendInCity: " + repo.totalSpendInCity("Lagos"));
        System.out.println("Custom fragment topSpenderInCity: " + repo.topSpenderInCity("Lagos"));
    }
}

class Customer {
    String id, name, city; double lifetimeSpend;
    Customer(String id, String name, String city, double lifetimeSpend) {
        this.id = id; this.name = name; this.city = city; this.lifetimeSpend = lifetimeSpend;
    }
}

// Base generated interface.
interface CustomerRepositoryBase {
    Customer save(Customer c);
    List<Customer> findByCity(String city);                  // derived
    double totalSpendInCity(String city);                     // @Query("SELECT SUM(c.lifetimeSpend) FROM /customers c WHERE c.city = $1")
}
// Custom fragment interface: an operation no derivation or simple OQL SELECT expresses.
interface CustomerRepositoryCustom {
    String topSpenderInCity(String city);
}
interface CustomerRepository extends CustomerRepositoryBase, CustomerRepositoryCustom { }

class CustomerRepositoryImpl implements CustomerRepository {
    private final Map<String, Customer> region = new HashMap<>();

    public Customer save(Customer c) { region.put(c.id, c); return c; }
    public List<Customer> findByCity(String city) {
        return region.values().stream().filter(c -> c.city.equals(city)).collect(Collectors.toList());
    }
    public double totalSpendInCity(String city) {
        return region.values().stream().filter(c -> c.city.equals(city)).mapToDouble(c -> c.lifetimeSpend).sum();
    }
    // Not derivable, not a plain OQL SELECT -- needs a comparison across matched results.
    public String topSpenderInCity(String city) {
        return region.values().stream()
            .filter(c -> c.city.equals(city))
            .max(Comparator.comparingDouble(c -> c.lifetimeSpend))
            .map(c -> c.name)
            .orElse("none");
    }
}
```

How to run: `java GemfireRepoLevel3.java`

`findByCity` (derived), `totalSpendInCity` (hand-written OQL aggregate via `@Query`), and `topSpenderInCity` (a custom fragment doing a comparison across the matched set) each solve a progressively less standard problem — exactly the three-tier escalation (derive, then `@Query`, then custom fragment) that's appeared for every Spring Data module across this entire course, here closing it out over an in-memory data grid.

## 6. Walkthrough

Execution starts in `main` for Level 3. Three customers are saved, two in Lagos with spends of 250.0 and 400.0, one in Abuja with 150.0.

`repo.findByCity("Lagos")` returns both Lagos customers via the derived filter:

```
Derived findByCity: 2
```

`repo.totalSpendInCity("Lagos")` sums `lifetimeSpend` across the same filtered set — mirroring what `SELECT SUM(c.lifetimeSpend) FROM /customers c WHERE c.city = 'Lagos'` would compute via real OQL, executed against the Region:

```
@Query totalSpendInCity: 650.0
```

`repo.topSpenderInCity("Lagos")` performs a `max`-by-comparator reduction across the same filtered set — a genuine comparison across multiple matched results that has no clean single-expression OQL equivalent, so it's implemented as a custom fragment method instead, following the same base-plus-custom-fragment composition pattern this course introduced for Cassandra and used again for Neo4j:

```
Custom fragment topSpenderInCity: Chidi
```

This closes the loop on every store module covered in this course: whether the backing store is a relational database, a document store, a wide-column store, a graph, a key-value cache, or — as here — a distributed in-memory data grid, the same three-tier pattern applies: derive what you can from a method name, escalate to `@Query` for anything with real query-language expressiveness, and drop to a custom fragment for logic that needs to run in application code against the results.

## 7. Gotchas & takeaways

> Gotcha: `GemfireRepository` methods that filter by content ultimately run OQL under the hood — the same indexing concern from the previous card applies here too; a derived method or `@Query` filtering on an unindexed field scans the entire Region, which matters even more for a repository abstraction that makes the underlying OQL easy to forget is even there.

> Gotcha: Geode Regions are fundamentally an in-memory, often cache-oriented store — unlike the disk-backed databases covered throughout most of this course, data in a Region can be evicted or expire based on the Region's configuration, meaning a `GemfireRepository.findById` can legitimately return nothing for a record that logically "exists" in a slower system of record behind the cache but has simply aged out of the grid.

- `GemfireRepository` completes the Spring Data pattern for Geode/GemFire: derived methods for routine lookups, `@Query` with OQL for genuine query-language expressiveness, and custom fragments for logic that needs application code — the exact same three-tier structure used across every store module in this course.
- Every generated repository method ultimately delegates to the same `GemfireTemplate`/Region operations covered in the previous two cards.
- Indexing considerations for OQL-backed derived queries and `@Query` methods are the same as for hand-written OQL — the repository layer doesn't remove the need to think about how a filter is actually evaluated.
- Geode Regions are typically cache-oriented and can evict or expire entries, a meaningfully different persistence guarantee from the disk-backed stores covered through the rest of this course's Spring Data material.
