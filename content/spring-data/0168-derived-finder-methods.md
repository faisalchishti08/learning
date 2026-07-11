---
card: spring-data
gi: 168
slug: derived-finder-methods
title: "Derived finder methods"
---

## 1. What it is

Derived finder methods let a Neo4j repository method name — `findByName`, `findByCityAndAgeGreaterThan`, `findByProductsName` — get parsed into a Cypher query automatically, with no `@Query` annotation needed. This is the same derivation mechanism seen for `MongoRepository`, `JpaRepository`, and `CassandraRepository` throughout this course, extended here to traverse relationships.

```java
interface CustomerRepository extends Neo4jRepository<Customer, String> {
    List<Customer> findByCity(String city);
    List<Customer> findByProductsName(String productName); // traverses BOUGHT -> Product.name
}
```

## 2. Why & when

Most repository methods are simple property or relationship-property lookups, and writing Cypher by hand for each one is unnecessary ceremony. Derived methods cover that common case, reserving `@Query`/Cypher-DSL for genuinely irregular traversals.

Reach for derived finder methods when:

- The query filters on one or more of an entity's direct properties (`findByCity`, `findByNameAndCity`).
- The query filters on a property of a *directly related* node reached through exactly one `@Relationship` field (`findByProductsName` — traverses from `Customer` through `products` to `Product.name`).
- The condition is a standard keyword Spring Data already understands — `GreaterThan`, `Containing`, `OrderBy`, `In` — rather than something needing custom logic.

## 3. Core concept

```
 findByCity(String city)
   -> MATCH (c:Customer {city: $city}) RETURN c

 findByProductsName(String productName)
   -> MATCH (c:Customer)-[:BOUGHT]->(p:Product {name: $productName}) RETURN c
        ^ relationship field name        ^ nested property, traversed automatically

 findByCityAndProductsNameContaining(String city, String fragment)
   -> MATCH (c:Customer {city: $city})-[:BOUGHT]->(p:Product) WHERE p.name CONTAINS $fragment RETURN c
```

`products` in the method name is the Java field name of the `@Relationship`-mapped list — Spring Data recognizes it and inserts the corresponding relationship pattern automatically, one hop at a time.

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A derived method name is parsed into property filters and relationship traversal segments">
  <rect x="20" y="20" width="600" height="35" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="320" y="42" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="monospace">findByCityAndProductsNameContaining(city, fragment)</text>

  <rect x="30" y="90" width="180" height="40" rx="6" fill="#6db33f30" stroke="#6db33f" stroke-width="1.5"/>
  <text x="120" y="114" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">City -&gt; own property</text>

  <rect x="230" y="90" width="180" height="40" rx="6" fill="#6db33f30" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="114" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">Products -&gt; relationship hop</text>

  <rect x="430" y="90" width="180" height="40" rx="6" fill="#6db33f30" stroke="#6db33f" stroke-width="1.5"/>
  <text x="520" y="114" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">NameContaining -&gt; CONTAINS</text>
</svg>

Each segment of the method name maps to a distinct piece of the generated Cypher: a property filter, a relationship hop, or a comparison keyword.

## 5. Runnable example

The scenario: deriving customer lookups by name and shopping activity, evolving from a single-property derived method, to a relationship-traversing derived method, to a combined method mixing an own-property filter, a relationship hop, and a comparison keyword — the full derivation vocabulary at once.

### Level 1 — Basic

Model a single own-property derived method against an in-memory stand-in.

```java
import java.util.*;
import java.util.stream.*;

public class DerivedFinderLevel1 {
    public static void main(String[] args) {
        CustomerRepository repo = new CustomerRepositoryImpl();
        repo.save(new Customer("c1", "Amara", "Lagos"));
        repo.save(new Customer("c2", "Bilal", "Lagos"));
        repo.save(new Customer("c3", "Chidi", "Abuja"));

        List<Customer> lagosCustomers = repo.findByCity("Lagos"); // derived from own property
        for (Customer c : lagosCustomers) System.out.println("In Lagos: " + c.name);
    }
}

class Customer {
    String id, name, city;
    Customer(String id, String name, String city) { this.id = id; this.name = name; this.city = city; }
}

interface CustomerRepository {
    Customer save(Customer c);
    List<Customer> findByCity(String city); // derived: MATCH (c:Customer {city: $city}) RETURN c
}

class CustomerRepositoryImpl implements CustomerRepository {
    private final Map<String, Customer> nodes = new HashMap<>();
    public Customer save(Customer c) { nodes.put(c.id, c); return c; }
    public List<Customer> findByCity(String city) {
        return nodes.values().stream().filter(c -> c.city.equals(city)).collect(Collectors.toList());
    }
}
```

How to run: `java DerivedFinderLevel1.java`

`findByCity` is derived from the `city` property alone, generating a single-node `MATCH` with a property filter — no relationship involved yet.

### Level 2 — Intermediate

Add a relationship-traversing derived method — `findByProductsName` — which walks the `products` field's `BOUGHT` relationship out to `Product.name`.

```java
import java.util.*;
import java.util.stream.*;

public class DerivedFinderLevel2 {
    public static void main(String[] args) {
        CustomerRepository repo = new CustomerRepositoryImpl();
        Customer amara = new Customer("c1", "Amara", "Lagos");
        amara.products.add(new Product("kettle"));
        repo.save(amara);

        Customer bilal = new Customer("c2", "Bilal", "Lagos");
        bilal.products.add(new Product("teapot"));
        repo.save(bilal);

        List<Customer> kettleBuyers = repo.findByProductsName("kettle"); // derived, traverses relationship
        for (Customer c : kettleBuyers) System.out.println("Bought kettle: " + c.name);
    }
}

class Customer {
    String id, name, city;
    List<Product> products = new ArrayList<>(); // @Relationship(type = "BOUGHT")
    Customer(String id, String name, String city) { this.id = id; this.name = name; this.city = city; }
}
class Product { String name; Product(String name) { this.name = name; } }

interface CustomerRepository {
    Customer save(Customer c);
    // derived: MATCH (c:Customer)-[:BOUGHT]->(p:Product {name: $productName}) RETURN c
    List<Customer> findByProductsName(String productName);
}

class CustomerRepositoryImpl implements CustomerRepository {
    private final Map<String, Customer> nodes = new HashMap<>();
    public Customer save(Customer c) { nodes.put(c.id, c); return c; }
    public List<Customer> findByProductsName(String productName) {
        return nodes.values().stream()
            .filter(c -> c.products.stream().anyMatch(p -> p.name.equals(productName)))
            .collect(Collectors.toList());
    }
}
```

How to run: `java DerivedFinderLevel2.java`

`findByProductsName` is derived by recognizing `products` as the `@Relationship`-mapped field name, and `Name` as a property on the target `Product` node — Spring Data inserts the `-[:BOUGHT]->(p:Product)` hop into the generated Cypher automatically, without a single line of query code written by hand.

### Level 3 — Advanced

Combine an own-property filter, a relationship traversal, and a comparison keyword in one derived method — `findByCityAndProductsNameContaining` — the full vocabulary working together.

```java
import java.util.*;
import java.util.stream.*;

public class DerivedFinderLevel3 {
    public static void main(String[] args) {
        CustomerRepository repo = new CustomerRepositoryImpl();

        Customer amara = new Customer("c1", "Amara", "Lagos");
        amara.products.add(new Product("kettle"));
        repo.save(amara);

        Customer bilal = new Customer("c2", "Bilal", "Lagos");
        bilal.products.add(new Product("teapot"));
        repo.save(bilal);

        Customer chidi = new Customer("c3", "Chidi", "Abuja");
        chidi.products.add(new Product("kettle"));
        repo.save(chidi);

        // derived: city filter + relationship hop + CONTAINS keyword, all in one method name
        List<Customer> matches = repo.findByCityAndProductsNameContaining("Lagos", "ket");
        for (Customer c : matches) System.out.println("Matched: " + c.name);
    }
}

class Customer {
    String id, name, city;
    List<Product> products = new ArrayList<>();
    Customer(String id, String name, String city) { this.id = id; this.name = name; this.city = city; }
}
class Product { String name; Product(String name) { this.name = name; } }

interface CustomerRepository {
    Customer save(Customer c);
    List<Customer> findByCityAndProductsNameContaining(String city, String fragment);
}

class CustomerRepositoryImpl implements CustomerRepository {
    private final Map<String, Customer> nodes = new HashMap<>();
    public Customer save(Customer c) { nodes.put(c.id, c); return c; }
    public List<Customer> findByCityAndProductsNameContaining(String city, String fragment) {
        return nodes.values().stream()
            .filter(c -> c.city.equals(city))
            .filter(c -> c.products.stream().anyMatch(p -> p.name.contains(fragment)))
            .collect(Collectors.toList());
    }
}
```

How to run: `java DerivedFinderLevel3.java`

Only `Amara` matches: she's in `Lagos` *and* one of her products (`kettle`) contains `ket`. `Bilal` is in `Lagos` but bought `teapot`, which doesn't contain `ket`; `Chidi` bought a `kettle` but lives in `Abuja`. Spring Data parses `CityAnd` as a plain `AND`-joined property filter, and `ProductsNameContaining` as a relationship hop followed by a `CONTAINS` comparison — all from the method name alone.

## 6. Walkthrough

Execution starts in `main` for Level 3. Three customers are saved, each with one product. `repo.findByCityAndProductsNameContaining("Lagos", "ket")` runs the combined derived filter.

The (simulated) Cypher this derives to is:

```
MATCH (c:Customer {city: $city})-[:BOUGHT]->(p:Product)
WHERE p.name CONTAINS $fragment
RETURN c
```

With `city = "Lagos"` and `fragment = "ket"` bound as parameters, Neo4j's engine matches the `Customer` node's `city` property first, then follows its `BOUGHT` edges to check each connected `Product.name` for the substring. Only `Amara`'s pattern satisfies both conditions:

```
Matched: Amara
```

Data changes shape once here: the input is two scalar strings (`"Lagos"`, `"ket"`); Neo4j's traversal produces matching `(c)-[:BOUGHT]->(p)` paths internally; the final `RETURN c` collapses each matching path back down to just the `Customer` node, discarding the `Product` node it matched through — the caller gets `Customer` objects out, with no visibility into *which* product triggered the match, unless the query explicitly returned `p` too.

## 7. Gotchas & takeaways

> Gotcha: derived methods traversing more than one relationship hop deep (`findByProductsSupplierCountry`, say) get harder to read and can silently generate an expensive multi-hop `MATCH` — past one hop, switching to `@Query` or the Cypher-DSL usually produces clearer, more intentional Cypher.

> Gotcha: a derived method returning `Customer` after filtering through a relationship (as in Level 3) does not tell you *which* related node matched — if the caller needs to know that `kettle` specifically was the match, the method needs to return a projection or the query needs to explicitly select the related node too.

- Derived methods parse property filters, relationship hops (via the mapped field name), and comparison keywords straight from the method name — the same mechanism used across every Spring Data module in this course, now extended with relationship-hop recognition.
- One-hop relationship derivation (`findByProductsName`) is readable and safe; multi-hop derivation usually isn't worth the readability cost compared to `@Query` or the Cypher-DSL.
- A derived method returns the *root* entity type by default, even when the filter traversed through a related node — use a projection when the related node's data is also needed in the result.
- Keywords like `Containing`, `GreaterThan`, `OrderBy`, and `And`/`Or` compose the same way here as they do for JPA and MongoDB repositories earlier in this course.
