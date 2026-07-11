---
card: spring-data
gi: 190
slug: oql-queries
title: "OQL queries"
---

## 1. What it is

OQL (Object Query Language) is Geode's SQL-like query language for filtering and projecting data stored in Regions — syntactically close to SQL's `SELECT ... FROM ... WHERE`, but operating over Java objects held in a Region rather than rows in a relational table. Spring Data Geode lets OQL power both `@Query`-annotated repository methods and direct `GemfireTemplate` queries.

```java
@Query("SELECT * FROM /customers c WHERE c.city = $1")
List<Customer> findByCity(String city);
```

## 2. Why & when

`GemfireTemplate.get(key)` (previous card) is a direct key-based lookup — fast, but only useful when the key is already known. OQL is what makes a Region queryable by *content*, the same escape hatch pattern `@Query` provided for every other store module in this course, adapted to Geode's `/regionName` path syntax and in-memory execution model.

Reach for OQL when:

- A lookup needs to filter on properties of the stored objects, not just fetch by known key.
- The query needs SQL-like expressiveness — comparisons, `AND`/`OR`, `IN`, ordering — over data held in a Region.
- You want to run the same kind of ad hoc exploratory query against an in-memory grid that you'd run against a relational database, without pulling all data out of the grid into application code first.

## 3. Core concept

```
 Region "/customers" holds Customer objects, keyed by id

 OQL: SELECT * FROM /customers c WHERE c.city = 'Lagos'
   -> scans (or uses an index on) the customers Region
   -> evaluates c.city = 'Lagos' against each stored Customer
   -> returns matching Customer objects

 template.get("c1")                      -- direct key lookup, no OQL involved
 template.query("SELECT * FROM /customers c WHERE c.city = 'Lagos'")  -- OQL, content-based
```

OQL's `FROM /regionName` syntax names the Region being queried the way SQL's `FROM tableName` names a table — the rest of the syntax (`WHERE`, comparisons, projections) reads similarly to SQL.

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="An OQL SELECT statement is evaluated against every object in a Region, returning those matching the WHERE clause">
  <rect x="20" y="20" width="600" height="35" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="320" y="42" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="monospace">SELECT * FROM /customers c WHERE c.city = 'Lagos'</text>

  <rect x="60" y="90" width="150" height="40" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="135" y="115" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Amara, Lagos</text>

  <rect x="240" y="90" width="150" height="40" rx="6" fill="#6db33f30" stroke="#6db33f" stroke-width="1.5"/>
  <text x="315" y="115" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Bilal, Abuja</text>

  <rect x="420" y="90" width="150" height="40" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="495" y="115" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Chidi, Lagos</text>
</svg>

Each stored object in the Region is checked against the `WHERE` clause; only matches (Lagos customers, highlighted differently here to show the filter concept) are returned.

## 5. Runnable example

The scenario: querying customer data stored in a Region, evolving from a direct key-based lookup that can't filter by content, to a simple OQL `WHERE` filter, to a query with a projection and an `ORDER BY` — production-flavored OQL, returning shaped, sorted results rather than full raw objects.

### Level 1 — Basic

Show the key-based lookup limitation — the problem OQL solves.

```java
import java.util.*;

public class OqlLevel1 {
    public static void main(String[] args) {
        Region region = new Region();
        region.put("c1", new Customer("c1", "Amara", "Lagos"));
        region.put("c2", new Customer("c2", "Bilal", "Abuja"));

        Customer byKey = region.get("c1"); // works ONLY if the key is already known
        System.out.println("By key: " + byKey.name);
        // No way to ask "give me every customer in Lagos" without knowing every key up front.
    }
}

class Customer {
    String id, name, city;
    Customer(String id, String name, String city) { this.id = id; this.name = name; this.city = city; }
}

class Region {
    private final Map<String, Customer> data = new HashMap<>();
    void put(String key, Customer value) { data.put(key, value); }
    Customer get(String key) { return data.get(key); }
    Collection<Customer> values() { return data.values(); }
}
```

How to run: `java OqlLevel1.java`

`get(key)` only works when the caller already knows exactly which key to ask for — there's no way to ask "find every customer in Lagos" through this API at all, which is exactly the gap OQL closes.

### Level 2 — Intermediate

Add an OQL-style `WHERE` filter, evaluated against every object in the Region.

```java
import java.util.*;
import java.util.stream.*;

public class OqlLevel2 {
    public static void main(String[] args) {
        Region region = new Region();
        region.put("c1", new Customer("c1", "Amara", "Lagos"));
        region.put("c2", new Customer("c2", "Bilal", "Abuja"));
        region.put("c3", new Customer("c3", "Chidi", "Lagos"));

        // OQL: SELECT * FROM /customers c WHERE c.city = 'Lagos'
        List<Customer> lagosCustomers = region.query(c -> c.city.equals("Lagos"));
        for (Customer c : lagosCustomers) System.out.println("Lagos customer: " + c.name);
    }
}

class Customer {
    String id, name, city;
    Customer(String id, String name, String city) { this.id = id; this.name = name; this.city = city; }
}

class Region {
    private final Map<String, Customer> data = new HashMap<>();
    void put(String key, Customer value) { data.put(key, value); }
    // Stands in for GemfireTemplate.query(oqlString) -- here a Java predicate stands in for the parsed WHERE clause.
    List<Customer> query(java.util.function.Predicate<Customer> whereClause) {
        return data.values().stream().filter(whereClause).collect(Collectors.toList());
    }
}
```

How to run: `java OqlLevel2.java`

`region.query(c -> c.city.equals("Lagos"))` mirrors what `SELECT * FROM /customers c WHERE c.city = 'Lagos'` does in real OQL: evaluate a condition against every object in the Region, returning only the matches — content-based querying, not key-based lookup.

### Level 3 — Advanced

Add a projection and ordering — `SELECT c.name FROM /customers c WHERE c.city = 'Lagos' ORDER BY c.name` — returning shaped, sorted results rather than full raw objects.

```java
import java.util.*;
import java.util.function.*;
import java.util.stream.*;

public class OqlLevel3 {
    public static void main(String[] args) {
        Region region = new Region();
        region.put("c1", new Customer("c1", "Chidi", "Lagos"));
        region.put("c2", new Customer("c2", "Bilal", "Abuja"));
        region.put("c3", new Customer("c3", "Amara", "Lagos"));

        // OQL: SELECT c.name FROM /customers c WHERE c.city = 'Lagos' ORDER BY c.name
        List<String> names = region.queryProjected(
            c -> c.city.equals("Lagos"),           // WHERE
            c -> c.name,                             // SELECT projection
            Comparator.naturalOrder()                // ORDER BY
        );
        System.out.println("Lagos customer names, sorted: " + names);
    }
}

class Customer {
    String id, name, city;
    Customer(String id, String name, String city) { this.id = id; this.name = name; this.city = city; }
}

class Region {
    private final Map<String, Customer> data = new HashMap<>();
    void put(String key, Customer value) { data.put(key, value); }

    // Stands in for an OQL query with a WHERE clause, a projection, and an ORDER BY.
    <T extends Comparable<T>> List<T> queryProjected(
            Predicate<Customer> whereClause, Function<Customer, T> projection, Comparator<T> order) {
        return data.values().stream()
            .filter(whereClause)
            .map(projection)
            .sorted(order)
            .collect(Collectors.toList());
    }
}
```

How to run: `java OqlLevel3.java`

`queryProjected` composes three independent OQL concerns — filtering (`WHERE`), projecting (`SELECT c.name` instead of the full object), and ordering (`ORDER BY`) — the same way real OQL syntax composes them in one statement, but here each is passed as an independent Java function for clarity.

## 6. Walkthrough

Execution starts in `main` for Level 3. Three customers are stored, two in Lagos (`Chidi`, `Amara`), one in Abuja (`Bilal`). `region.queryProjected(...)` runs the combined filter/project/sort operation.

Internally, the stream pipeline first filters down to the two Lagos customers, then maps each surviving `Customer` object down to just its `name` string (discarding `id` and `city` entirely — the projection), then sorts the resulting `String`s alphabetically:

```
Lagos customer names, sorted: [Amara, Chidi]
```

In a real Geode deployment, this exact filter-project-sort pipeline is what the OQL engine performs when it executes `SELECT c.name FROM /customers c WHERE c.city = 'Lagos' ORDER BY c.name` — critically, if the Region has an index defined on `city`, Geode can use it to avoid scanning every stored object, the same way a database index avoids a full table scan; without one, the query falls back to evaluating the `WHERE` clause against every object in the Region, exactly like the naive `filter` call shown here.

## 7. Gotchas & takeaways

> Gotcha: OQL queries without a supporting index on the filtered field(s) require Geode to evaluate the `WHERE` clause against *every* object currently held in the Region — for a Region holding millions of entries, an unindexed OQL query can be dramatically slower than a key-based `get`, which is why indexing frequently-queried fields matters even more in an in-memory grid than it might seem to, given everything is "already in memory."

> Gotcha: OQL's `FROM /regionName` path syntax is easy to mistype or mismatch against the actual configured Region name (from the previous card) — a query against a non-existent or misspelled region path typically fails at query time with a region-not-found error, rather than at compile time, since OQL strings (like most `@Query` strings in this course) aren't checked until they run.

- OQL is Geode's SQL-like query language, letting Regions be queried by content instead of only by key, the same escape-hatch role `@Query` plays for every other store module in this course.
- Filtering, projection, and ordering compose in one OQL statement, the same way they compose in SQL — returning shaped, sorted results rather than always full raw objects.
- Unindexed OQL queries scan every object in the Region — indexing matters for query performance in an in-memory grid just as much as it does in a disk-backed database.
- OQL query strings are only validated at execution time, so region-path typos or malformed syntax surface as runtime errors, not compile-time ones.
