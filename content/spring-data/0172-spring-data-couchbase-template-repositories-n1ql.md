---
card: spring-data
gi: 172
slug: spring-data-couchbase-template-repositories-n1ql
title: "Spring Data Couchbase (template, repositories, N1QL)"
---

## 1. What it is

Spring Data Couchbase brings the familiar template-plus-repository pattern to Couchbase — a distributed JSON document database with a built-in caching tier. `CouchbaseTemplate` is the low-level API, `CouchbaseRepository` is the generated-method-name layer on top of it, and N1QL ("Nickel", Couchbase's SQL-like query language for JSON documents) is what powers both `@Query` and derived queries underneath.

```java
@Autowired CouchbaseTemplate couchbaseTemplate;

Customer customer = couchbaseTemplate.findById(Customer.class).one(customerId);
couchbaseTemplate.upsertById(Customer.class).one(new Customer("c1", "Amara"));
```

## 2. Why & when

This card opens a new section covering several smaller Spring Data store modules that each get lighter treatment than MongoDB, Redis, or Neo4j did — Couchbase, LDAP, KeyValue, and Envers, plus Spring Data JPA's QueryDSL integration. Couchbase is a document database like MongoDB, but built around key-value access as a first-class operation *and* full document queries, with N1QL letting you write SQL-shaped queries directly against JSON documents.

Reach for `CouchbaseTemplate`/`CouchbaseRepository` when:

- The application already uses Couchbase for its combined key-value-cache-plus-document-store model, and needs Spring Data's repository abstraction over it.
- A lookup is a simple key-based fetch — Couchbase's `findById` is extremely fast, closer to Redis's `GET` than a full document query.
- A query needs to filter across document fields — that's where N1QL and `@Query` come in, the same escape-hatch pattern seen throughout this course.

## 3. Core concept

```
 interface CustomerRepository extends CouchbaseRepository<Customer, String> {
     List<Customer> findByCity(String city);   -- derived, compiles to N1QL under the hood
 }

 findByCity("Lagos")
   -> N1QL: SELECT * FROM `customers` WHERE city = $1

 couchbaseTemplate.findById(Customer.class).one(id)   -- direct key-value fetch, no N1QL involved
```

Key-based lookups skip N1QL entirely and go straight to Couchbase's key-value engine; any query filtering on document *content* compiles to N1QL.

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A key-based lookup goes directly to the key-value engine while a content query compiles to N1QL first">
  <rect x="20" y="20" width="270" height="45" rx="8" fill="#6db33f30" stroke="#6db33f" stroke-width="1.5"/>
  <text x="155" y="47" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">findById(id) -&gt; key-value engine</text>

  <rect x="350" y="20" width="270" height="45" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="485" y="47" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">findByCity(city) -&gt; N1QL query</text>

  <rect x="180" y="100" width="280" height="40" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="320" y="125" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Couchbase document store</text>

  <line x1="155" y1="65" x2="280" y2="95" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a8)"/>
  <line x1="485" y1="65" x2="360" y2="95" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a8)"/>
  <defs><marker id="a8" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Both access paths reach the same underlying document store, through different Couchbase engines.

## 5. Runnable example

The scenario: storing and querying customer documents, evolving from a direct key-value `findById`, to a derived-method N1QL query filtering by city, to a hand-written `@Query` N1QL statement using an aggregate function no derivation can express.

### Level 1 — Basic

Model the direct key-value lookup path against an in-memory stand-in.

```java
import java.util.*;

public class CouchbaseLevel1 {
    public static void main(String[] args) {
        CouchbaseTemplate template = new CouchbaseTemplate();
        template.upsert(new Customer("c1", "Amara", "Lagos"));
        template.upsert(new Customer("c2", "Bilal", "Abuja"));

        Customer found = template.findById("c1");
        System.out.println("Key-value fetch: " + found.name + " (" + found.city + ")");
    }
}

class Customer {
    String id, name, city;
    Customer(String id, String name, String city) { this.id = id; this.name = name; this.city = city; }
}

// Stands in for org.springframework.data.couchbase.core.CouchbaseTemplate.
class CouchbaseTemplate {
    private final Map<String, Customer> documents = new HashMap<>();
    void upsert(Customer c) { documents.put(c.id, c); }
    Customer findById(String id) { return documents.get(id); } // key-value engine, no N1QL involved
}
```

How to run: `java CouchbaseLevel1.java`

`findById` is a direct key-value fetch — Couchbase resolves it without ever invoking its N1QL query engine, which is why key-based access on Couchbase (like on Redis) is typically the fastest read path available.

### Level 2 — Intermediate

Add a derived repository method that filters by document content, compiling to N1QL under the hood.

```java
import java.util.*;
import java.util.stream.*;

public class CouchbaseLevel2 {
    public static void main(String[] args) {
        CustomerRepository repo = new CustomerRepositoryImpl();
        repo.save(new Customer("c1", "Amara", "Lagos"));
        repo.save(new Customer("c2", "Bilal", "Lagos"));
        repo.save(new Customer("c3", "Chidi", "Abuja"));

        List<Customer> lagosCustomers = repo.findByCity("Lagos"); // derived -> N1QL WHERE city = $1
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

// Stands in for the Spring Data-generated N1QL-backed implementation of a CouchbaseRepository.
class CustomerRepositoryImpl implements CustomerRepository {
    private final Map<String, Customer> documents = new HashMap<>();
    public Customer save(Customer c) { documents.put(c.id, c); return c; }
    public List<Customer> findByCity(String city) {
        // Simulated N1QL: SELECT * FROM `customers` WHERE city = $1
        return documents.values().stream().filter(c -> c.city.equals(city)).collect(Collectors.toList());
    }
}
```

How to run: `java CouchbaseLevel2.java`

`findByCity` is parsed the same way derived methods are parsed for MongoDB or JPA elsewhere in this course, except the generated query text is N1QL — SQL-shaped syntax operating over JSON documents instead of relational rows.

### Level 3 — Advanced

Add a hand-written `@Query` N1QL statement computing an aggregate — average lifetime spend per city — something no derived method name can express.

```java
import java.util.*;
import java.util.stream.*;

public class CouchbaseLevel3 {
    public static void main(String[] args) {
        CustomerRepository repo = new CustomerRepositoryImpl();
        repo.save(new Customer("c1", "Amara", "Lagos", 250.0));
        repo.save(new Customer("c2", "Bilal", "Lagos", 150.0));
        repo.save(new Customer("c3", "Chidi", "Abuja", 400.0));

        // @Query("#{#n1ql.selectEntity} WHERE city = $1 GROUP BY city")  -- illustrative shape
        List<CitySpend> spendByCity = repo.averageSpendByCity();
        for (CitySpend s : spendByCity) System.out.println(s.city() + ": avg=" + s.averageSpend());
    }
}

class Customer {
    String id, name, city; double lifetimeSpend;
    Customer(String id, String name, String city, double lifetimeSpend) {
        this.id = id; this.name = name; this.city = city; this.lifetimeSpend = lifetimeSpend;
    }
}

record CitySpend(String city, double averageSpend) {}

interface CustomerRepository {
    Customer save(Customer c);
    List<CitySpend> averageSpendByCity();
}

// Stands in for a hand-written N1QL @Query with a GROUP BY aggregate.
class CustomerRepositoryImpl implements CustomerRepository {
    private final Map<String, Customer> documents = new HashMap<>();
    public Customer save(Customer c) { documents.put(c.id, c); return c; }
    public List<CitySpend> averageSpendByCity() {
        // Simulated N1QL: SELECT city, AVG(lifetimeSpend) AS averageSpend FROM `customers` GROUP BY city
        Map<String, List<Customer>> byCity = documents.values().stream()
            .collect(Collectors.groupingBy(c -> c.city));
        return byCity.entrySet().stream()
            .map(e -> new CitySpend(e.getKey(), e.getValue().stream().mapToDouble(c -> c.lifetimeSpend).average().orElse(0)))
            .collect(Collectors.toList());
    }
}
```

How to run: `java CouchbaseLevel3.java`

`averageSpendByCity` runs a `GROUP BY`-shaped N1QL query — no derived method name expresses "group and average" cleanly, so it needs a hand-written `@Query`, exactly the pattern established for `@Query` in the MongoDB, Cassandra, and Neo4j sections earlier in this course, just with N1QL as the query language this time.

## 6. Walkthrough

Execution starts in `main` for Level 3. Three customers are saved, two in Lagos with spends of 250.0 and 150.0, one in Abuja with 400.0. `repo.averageSpendByCity()` runs the (simulated) grouping N1QL query.

The request, conceptually, is the N1QL statement `SELECT city, AVG(lifetimeSpend) AS averageSpend FROM customers GROUP BY city` sent to Couchbase's query engine. The engine groups documents by `city`, averages `lifetimeSpend` within each group, and returns one row per group:

```
Lagos: avg=200.0
Abuja: avg=400.0
```

Each result row maps into a `CitySpend` record — a projection, not a full `Customer` entity — since the query only asked for two aggregated fields, the same "shape only what's needed" principle covered in the Neo4j projections card earlier applies here too, just via N1QL's own `GROUP BY`/aggregate syntax instead of Cypher's.

## 7. Gotchas & takeaways

> Gotcha: Couchbase's key-value fetch path (`findById`) and its N1QL query path are genuinely different engines under the hood — a workload that's mostly key-based lookups (like a session cache) should lean on `findById`, not a derived method that quietly compiles to a full N1QL query for what's really a simple key lookup.

> Gotcha: N1QL queries typically require a secondary index on any field used in a `WHERE` or `GROUP BY` clause to perform well — without one, Couchbase falls back to a full document scan, which defeats the purpose of using a query language over a document store at scale.

- `CouchbaseTemplate`/`CouchbaseRepository` follow the same template-plus-repository pattern as every other Spring Data module in this course, layered over Couchbase's key-value-plus-document engine.
- Key-based access (`findById`) bypasses N1QL entirely and is the fastest read path — reach for it whenever the access pattern really is "fetch by known key."
- N1QL powers both derived queries and `@Query`, giving SQL-shaped syntax over JSON documents, including aggregates that no derived method name can express.
- Secondary indexes matter for N1QL query performance the same way they do for any content-filtering query in this course's other document and wide-column stores.
