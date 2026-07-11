---
card: spring-data
gi: 81
slug: query-methods-query-native-sql
title: "Query methods & @Query (native SQL)"
---

## 1. What it is

Spring Data JDBC supports the same derived-query-method naming convention (`findByStatus`, `findByStatusAndTotalGreaterThan`) as every other Spring Data module, translating method names into `WHERE` clauses automatically. For anything a derived name can't express, `@Query` takes a **native SQL** string directly — there's no JPQL/HQL equivalent here, since Spring Data JDBC has no query-translation layer between Java and the database.

```java
interface OrderRepository extends CrudRepository<Order, Long> {
    List<Order> findByStatus(String status); // derived, same convention as JPA

    @Query("SELECT * FROM orders WHERE total > :minTotal ORDER BY total DESC")
    List<Order> findExpensiveOrders(@Param("minTotal") double minTotal); // NATIVE SQL, not JPQL
}
```

## 2. Why & when

Every earlier JPA card's `@Query` examples used JPQL — a database-agnostic query language translated into SQL by the JPA provider. Spring Data JDBC has no such translation layer at all: `@Query` strings here are the actual SQL sent to the database, verbatim. This card is about that distinction, and about when the derived-method convention (shared across all of Spring Data) suffices versus when you need to drop to raw SQL.

Reach for `@Query` with native SQL on Spring Data JDBC specifically when:

- The query needs a SQL feature or syntax that's specific to your database (a vendor function, a `WITH` clause, database-specific date arithmetic) — since there's no JPQL abstraction layer to get in the way, you write exactly the SQL your database understands.
- A derived method name would be unreasonably long or can't express the condition at all (e.g., a multi-table join not modeled as an aggregate relationship) — write the `SELECT` directly instead.
- You're migrating existing hand-written SQL into a repository method — the SQL itself typically needs zero translation, since it's already what Spring Data JDBC executes verbatim.

## 3. Core concept

```
 Derived method (works IDENTICALLY to JPA's derivation):
   List<Order> findByStatus(String status);
   -> SELECT * FROM orders WHERE status = ?

 @Query on Spring Data JPA:                      @Query on Spring Data JDBC:
   @Query("SELECT o FROM Order o WHERE ...")       @Query("SELECT * FROM orders WHERE ...")
   -- JPQL: entity/field names, translated          -- NATIVE SQL: table/column names, sent AS-IS
      to SQL by the JPA provider                       to the database, no translation at all
```

The derived-query mechanism is shared with the rest of Spring Data; `@Query` diverges sharply from JPA because there is no query-language translation step — the string you write is the SQL that runs.

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.v3.org/2000/svg" role="img" aria-label="A derived method name is translated into SQL by Spring Data JDBC, while an at-Query string is sent to the database verbatim">
  <rect x="20" y="20" width="280" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="160" y="42" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">findByStatus(status)</text>
  <text x="160" y="58" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">method name -&gt; translated to SQL</text>

  <rect x="340" y="20" width="280" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="480" y="42" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">@Query("SELECT * FROM ...")</text>
  <text x="480" y="58" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">sent to the database VERBATIM</text>

  <rect x="150" y="100" width="340" height="35" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.3"/>
  <text x="320" y="122" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">JDBC driver -&gt; database</text>

  <line x1="160" y1="70" x2="260" y2="95" stroke="#8b949e" stroke-width="1.3" marker-end="url(#nq)"/>
  <line x1="480" y1="70" x2="400" y2="95" stroke="#8b949e" stroke-width="1.3" marker-end="url(#nq)"/>
  <defs><marker id="nq" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Both paths ultimately produce SQL sent to the database — one via automatic derivation, the other written by hand and sent unchanged.

## 5. Runnable example

The scenario: querying orders by status and total, evolving from a derived-method-only baseline, to a native-SQL `@Query` for a condition derivation can't express well, to a native query using a database-specific feature (a window function) no derived method could ever produce.

### Level 1 — Basic

Model the derived-query path, matching the exact same mechanism used throughout every earlier Spring Data card.

```java
import java.util.*;
import java.util.stream.*;

class Order { long id; String status; double total; Order(long id, String status, double total) { this.id = id; this.status = status; this.total = total; } }

interface OrderRepository {
    List<Order> findByStatus(String status); // derived from the method name
}

class JdbcOrderRepository implements OrderRepository {
    private final List<Order> db;
    JdbcOrderRepository(List<Order> db) { this.db = db; }

    public List<Order> findByStatus(String status) {
        System.out.println("  SQL (derived): SELECT * FROM orders WHERE status = '" + status + "'");
        return db.stream().filter(o -> o.status.equals(status)).collect(Collectors.toList());
    }
}

public class QueryLevel1 {
    public static void main(String[] args) {
        List<Order> orders = List.of(new Order(1, "SHIPPED", 50), new Order(2, "PENDING", 150));
        OrderRepository repo = new JdbcOrderRepository(orders);

        List<Order> shipped = repo.findByStatus("SHIPPED");
        System.out.println("Found " + shipped.size() + " shipped order(s)");
    }
}
```

How to run: `java QueryLevel1.java`

`findByStatus` works exactly as it would on a Spring Data JPA repository — the method-name derivation mechanism is shared Spring Data Commons infrastructure, entirely independent of which module (JPA, JDBC, MongoDB, ...) implements the actual query execution underneath.

### Level 2 — Intermediate

Add a native-SQL `@Query` method for a condition that would produce an unwieldy derived name, and confirm the SQL string is used verbatim.

```java
import java.util.*;
import java.util.stream.*;

class Order { long id; String status; double total; Order(long id, String status, double total) { this.id = id; this.status = status; this.total = total; } }

interface OrderRepository {
    List<Order> findByStatus(String status);
    List<Order> findExpensiveOrders(double minTotal); // backed by @Query, not derivation
}

class JdbcOrderRepository implements OrderRepository {
    private final List<Order> db;
    JdbcOrderRepository(List<Order> db) { this.db = db; }

    public List<Order> findByStatus(String status) {
        return db.stream().filter(o -> o.status.equals(status)).collect(Collectors.toList());
    }

    // @Query("SELECT * FROM orders WHERE total > :minTotal ORDER BY total DESC")
    public List<Order> findExpensiveOrders(double minTotal) {
        String sql = "SELECT * FROM orders WHERE total > " + minTotal + " ORDER BY total DESC";
        System.out.println("  SQL (native, sent verbatim): " + sql);
        return db.stream()
            .filter(o -> o.total > minTotal)
            .sorted(Comparator.comparingDouble((Order o) -> o.total).reversed())
            .collect(Collectors.toList());
    }
}

public class QueryLevel2 {
    public static void main(String[] args) {
        List<Order> orders = List.of(new Order(1, "SHIPPED", 50), new Order(2, "PENDING", 300), new Order(3, "SHIPPED", 150));
        OrderRepository repo = new JdbcOrderRepository(orders);

        List<Order> expensive = repo.findExpensiveOrders(100);
        System.out.println("Expensive orders (total > 100): " + expensive.size());
    }
}
```

How to run: `java QueryLevel2.java`

`findExpensiveOrders` prints the exact SQL string that would be sent to the database — there's no intermediate query language to translate; the string in `@Query` (here reconstructed inline) *is* the SQL, matching the real behavior where `@Query` on Spring Data JDBC bypasses derivation entirely and passes native SQL straight to the JDBC driver.

### Level 3 — Advanced

Add a query using a database-specific window function — something a derived method name could never express, since it has no equivalent in Spring Data's method-naming vocabulary at all.

```java
import java.util.*;
import java.util.stream.*;

class Order { long id; String status; double total; int rankWithinStatus; Order(long id, String status, double total) { this.id = id; this.status = status; this.total = total; } }

interface OrderRepository {
    List<Order> findTopOrderPerStatusByWindowFunction();
}

class JdbcOrderRepository implements OrderRepository {
    private final List<Order> db;
    JdbcOrderRepository(List<Order> db) { this.db = db; }

    // @Query("""
    //     SELECT *, RANK() OVER (PARTITION BY status ORDER BY total DESC) AS rank_within_status
    //     FROM orders
    //     """)
    // -- a window function: NO derived method name could ever express this; @Query with native SQL is the only way.
    public List<Order> findTopOrderPerStatusByWindowFunction() {
        System.out.println("  SQL (native, window function): SELECT *, RANK() OVER (PARTITION BY status ORDER BY total DESC) ...");

        Map<String, List<Order>> byStatus = db.stream().collect(Collectors.groupingBy(o -> o.status));
        List<Order> result = new ArrayList<>();
        for (List<Order> group : byStatus.values()) {
            group.sort(Comparator.comparingDouble((Order o) -> o.total).reversed());
            for (int i = 0; i < group.size(); i++) {
                group.get(i).rankWithinStatus = i + 1; // simulates RANK() OVER (PARTITION BY status ORDER BY total DESC)
            }
            result.addAll(group);
        }
        return result;
    }
}

public class QueryLevel3 {
    public static void main(String[] args) {
        List<Order> orders = new ArrayList<>(List.of(
            new Order(1, "SHIPPED", 50), new Order(2, "SHIPPED", 300),
            new Order(3, "PENDING", 80), new Order(4, "PENDING", 200)
        ));
        OrderRepository repo = new JdbcOrderRepository(orders);

        List<Order> ranked = repo.findTopOrderPerStatusByWindowFunction();
        for (Order o : ranked) {
            System.out.println("Order " + o.id + " (status=" + o.status + ", total=" + o.total + ") rank=" + o.rankWithinStatus);
        }
    }
}
```

How to run: `java QueryLevel3.java`

No derived method name (`findByStatus...`, `findByTotalGreaterThan...`) has any vocabulary for "rank within a partition" — this requires a genuine SQL window function, which only `@Query` with native SQL can express on Spring Data JDBC. The simulated ranking groups orders by `status`, sorts each group by `total` descending, and assigns `1`, `2`, ... within each group, exactly matching what `RANK() OVER (PARTITION BY status ORDER BY total DESC)` computes in real SQL.

## 6. Walkthrough

Execution starts in `main` for Level 3. First, four orders are created: two `SHIPPED` (totals 50 and 300) and two `PENDING` (totals 80 and 200).

`repo.findTopOrderPerStatusByWindowFunction()` runs. Inside, `db.stream().collect(Collectors.groupingBy(o -> o.status))` partitions the orders into two groups: `SHIPPED -> [order1(50), order2(300)]` and `PENDING -> [order3(80), order4(200)]` — mirroring the SQL window function's `PARTITION BY status` clause.

For the `SHIPPED` group, `group.sort(...)` orders it descending by `total`, producing `[order2(300), order1(50)]`; the inner loop then assigns `rankWithinStatus = 1` to `order2` and `rankWithinStatus = 2` to `order1` — mirroring `ORDER BY total DESC` combined with `RANK()`'s numbering within the partition. The same happens for the `PENDING` group: sorted to `[order4(200), order3(80)]`, ranks `1` and `2` respectively.

Both groups' results are appended into `result`, and the final loop in `main` prints each order with its status, total, and computed rank — confirming `order2` (SHIPPED, 300) is rank 1 within its status group, `order1` (SHIPPED, 50) is rank 2, `order4` (PENDING, 200) is rank 1, and `order3` (PENDING, 80) is rank 2.

```
groupBy(status): SHIPPED=[order1(50), order2(300)]   PENDING=[order3(80), order4(200)]

sort each group by total DESC, assign rank 1..N within the group:
  SHIPPED: order2(300)->rank1, order1(50)->rank2
  PENDING: order4(200)->rank1, order3(80)->rank2
```

In a real Spring Data JDBC application, `@Query("SELECT *, RANK() OVER (PARTITION BY status ORDER BY total DESC) AS rank_within_status FROM orders")` sends that exact SQL string to the database (assuming the database supports window functions, as PostgreSQL and modern MySQL/H2 do) — the database engine itself computes the ranking, and Spring Data JDBC simply maps each returned row (including the extra `rank_within_status` column) back into an `Order` object with a matching field. This is the sharpest contrast with JPQL: there is no abstraction layer translating a portable query language into vendor SQL — you write exactly the SQL your specific database understands, and it runs exactly as written.

## 7. Gotchas & takeaways

> Gotcha: because `@Query` on Spring Data JDBC is native SQL with zero abstraction, a query using vendor-specific syntax (like a particular window-function dialect, or a database-specific date function) will not necessarily run unchanged against a different database — unlike JPQL, which is at least nominally portable across JPA providers and databases.

- Derived query methods (`findByStatus`, etc.) work identically across every Spring Data module, including JDBC — this mechanism is shared Spring Data Commons infrastructure.
- `@Query` on Spring Data JDBC takes *native SQL*, not JPQL — the string is sent to the database exactly as written, with no translation layer in between.
- Reach for native `@Query` when a condition can't be reasonably expressed as a derived method name, or when a SQL feature (window functions, CTEs, vendor-specific functions) has no derived-method equivalent at all.
- Native SQL trades portability for directness — a query tuned for one database's SQL dialect may need rewriting to run against a different one.
