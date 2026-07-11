---
card: spring-data
gi: 67
slug: queryhints
title: "@QueryHints"
---

## 1. What it is

`@QueryHints` on a repository method attaches vendor- or JPA-provider-specific hints to the generated query — instructions that don't change *what* rows come back, but change *how* the query engine handles them internally. The most common example is marking a query's results read-only, so Hibernate skips storing them in the persistence context for dirty checking.

```java
@QueryHints(@QueryHint(name = "org.hibernate.readOnly", value = "true"))
List<Order> findByStatus(String status);
```

## 2. Why & when

The persistence context card explained that every managed entity gets a snapshot for dirty checking, and the locking card explained pessimistic/optimistic concurrency controls — both add per-entity bookkeeping overhead. `@QueryHints` is how you tell the JPA provider to skip that bookkeeping for a specific query when you know the results will never be modified, trading away update capability for lower memory use and less CPU spent on snapshotting.

Reach for `@QueryHints` specifically when:

- A query is purely for display/reporting (e.g., a dashboard list) and the returned entities will never be mutated — `org.hibernate.readOnly` skips snapshot-taking, reducing persistence-context memory overhead.
- You want to cap how long a query is allowed to run — a timeout hint (e.g., `jakarta.persistence.query.timeout`) protects against a runaway query on a large table.
- You're using a query cache and want a specific query's results cached — a caching hint tells the provider to store and reuse the result set for identical future calls.

## 3. Core concept

```
 Without @QueryHints:
   findByStatus("SHIPPED") -> each Order becomes MANAGED
                            -> snapshot taken for EACH one (dirty-checking overhead)

 With @QueryHints(readOnly=true):
   findByStatus("SHIPPED") -> each Order returned, but NOT tracked for dirty checking
                            -> no snapshot taken -> less memory, faster for read-only workloads
                            -> mutating a field on the result has NO effect at commit
```

Query hints don't change the returned rows — they change the bookkeeping cost the persistence context pays for tracking them afterward.

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.v3.org/2000/svg" role="img" aria-label="A read-only query hint skips snapshot-taking, avoiding dirty-check overhead for entities that will never be modified">
  <rect x="20" y="20" width="200" height="50" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="120" y="42" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">findByStatus("SHIPPED")</text>
  <text x="120" y="58" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="sans-serif">no hint</text>

  <rect x="420" y="20" width="200" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="520" y="42" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">findByStatus("SHIPPED")</text>
  <text x="520" y="58" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="sans-serif">@QueryHints readOnly=true</text>

  <rect x="20" y="95" width="200" height="40" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.2"/>
  <text x="120" y="120" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">managed + snapshot per row</text>

  <rect x="420" y="95" width="200" height="40" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.2"/>
  <text x="520" y="120" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">returned, no snapshot taken</text>

  <line x1="120" y1="70" x2="120" y2="90" stroke="#8b949e" stroke-width="1.3" marker-end="url(#qh)"/>
  <line x1="520" y1="70" x2="520" y2="90" stroke="#8b949e" stroke-width="1.3" marker-end="url(#qh)"/>
  <defs><marker id="qh" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Both queries return identical rows; the read-only hint just skips the persistence context's per-row bookkeeping.

## 5. Runnable example

The scenario: a dashboard endpoint listing orders by status, evolving from a default query that tracks every result for dirty checking, to a read-only hinted version that skips it, to a timeout hint guarding against a slow query.

### Level 1 — Basic

Model the default (no hint) behavior: every returned entity is registered in a simulated persistence context, with a snapshot taken.

```java
import java.util.*;
import java.util.stream.*;

class Order {
    long id; double total; String status;
    Order(long id, double total, String status) { this.id = id; this.total = total; this.status = status; }
}

class PersistenceContext {
    static int snapshotsTaken = 0;
    static void register(Order o) {
        snapshotsTaken++; // every managed entity gets a snapshot for dirty checking
    }
}

public class QueryHintsLevel1 {
    // Simulates: List<Order> findByStatus(String status);  -- no @QueryHints
    static List<Order> findByStatus(List<Order> all, String status) {
        return all.stream().filter(o -> o.status.equals(status))
            .peek(PersistenceContext::register) // each result becomes managed, snapshot taken
            .collect(Collectors.toList());
    }

    public static void main(String[] args) {
        List<Order> orders = List.of(
            new Order(1, 50, "SHIPPED"), new Order(2, 150, "SHIPPED"), new Order(3, 200, "PENDING")
        );
        List<Order> found = findByStatus(orders, "SHIPPED");
        System.out.println("Found: " + found.size() + " orders");
        System.out.println("Snapshots taken (dirty-check overhead): " + PersistenceContext.snapshotsTaken);
    }
}
```

How to run: `java QueryHintsLevel1.java`

`snapshotsTaken` reaches 2 — one per returned order — mirroring how, with no `@QueryHints`, every entity a repository method returns becomes managed and gets a dirty-checking snapshot, even if the caller only ever reads it and never modifies it.

### Level 2 — Intermediate

Add the read-only hinted version, skipping snapshot registration entirely, and compare the overhead against Level 1's default path.

```java
import java.util.*;
import java.util.stream.*;

class Order {
    long id; double total; String status;
    Order(long id, double total, String status) { this.id = id; this.total = total; this.status = status; }
}

class PersistenceContext {
    static int snapshotsTaken = 0;
    static void register(Order o) { snapshotsTaken++; }
}

public class QueryHintsLevel2 {
    static List<Order> findByStatusDefault(List<Order> all, String status) {
        return all.stream().filter(o -> o.status.equals(status))
            .peek(PersistenceContext::register)
            .collect(Collectors.toList());
    }

    // @QueryHints(@QueryHint(name = "org.hibernate.readOnly", value = "true"))
    // List<Order> findByStatusReadOnly(String status);
    static List<Order> findByStatusReadOnly(List<Order> all, String status) {
        return all.stream().filter(o -> o.status.equals(status))
            // no PersistenceContext.register(...) call -- readOnly skips snapshot-taking entirely
            .collect(Collectors.toList());
    }

    public static void main(String[] args) {
        List<Order> orders = List.of(
            new Order(1, 50, "SHIPPED"), new Order(2, 150, "SHIPPED"), new Order(3, 200, "PENDING")
        );

        PersistenceContext.snapshotsTaken = 0;
        findByStatusDefault(orders, "SHIPPED");
        System.out.println("Default: snapshots taken = " + PersistenceContext.snapshotsTaken);

        PersistenceContext.snapshotsTaken = 0;
        List<Order> readOnly = findByStatusReadOnly(orders, "SHIPPED");
        System.out.println("Read-only: snapshots taken = " + PersistenceContext.snapshotsTaken
            + " (still returned " + readOnly.size() + " orders)");
    }
}
```

How to run: `java QueryHintsLevel2.java`

Both methods return the same 2 matching orders, but `findByStatusReadOnly` never calls `PersistenceContext.register`, so its snapshot count stays 0 — the rows are identical, only the bookkeeping cost differs, exactly matching what `org.hibernate.readOnly=true` does in a real Hibernate-backed repository.

### Level 3 — Advanced

Add a timeout hint that aborts a query taking too long — simulated with a time budget check — alongside the read-only hint, showing multiple `@QueryHint`s combined on one method.

```java
import java.util.*;
import java.util.stream.*;

class Order {
    long id; double total; String status;
    Order(long id, double total, String status) { this.id = id; this.total = total; this.status = status; }
}

class QueryTimeoutException extends RuntimeException {
    QueryTimeoutException(String msg) { super(msg); }
}

public class QueryHintsLevel3 {
    // @QueryHints({
    //     @QueryHint(name = "org.hibernate.readOnly", value = "true"),
    //     @QueryHint(name = "jakarta.persistence.query.timeout", value = "100") // ms
    // })
    static List<Order> findByStatusReadOnlyWithTimeout(List<Order> all, String status, long timeoutMillis) {
        long start = System.nanoTime();
        List<Order> result = new ArrayList<>();
        for (Order o : all) {
            // Simulate per-row work that might exceed the timeout on a large/slow table.
            if ((System.nanoTime() - start) / 1_000_000 > timeoutMillis) {
                throw new QueryTimeoutException("Query exceeded timeout of " + timeoutMillis + "ms");
            }
            if (o.status.equals(status)) result.add(o); // no snapshot registration: read-only
        }
        return result;
    }

    public static void main(String[] args) {
        List<Order> orders = List.of(
            new Order(1, 50, "SHIPPED"), new Order(2, 150, "SHIPPED"), new Order(3, 200, "PENDING")
        );

        // Generous timeout: succeeds normally.
        List<Order> ok = findByStatusReadOnlyWithTimeout(orders, "SHIPPED", 5000);
        System.out.println("Succeeded within timeout: " + ok.size() + " orders");

        // Simulate a pathological case: a huge dataset with a tiny timeout budget.
        List<Order> hugeDataset = new ArrayList<>();
        for (int i = 0; i < 50_000_000; i++) hugeDataset.add(new Order(i, 1, "SHIPPED"));
        try {
            findByStatusReadOnlyWithTimeout(hugeDataset, "SHIPPED", 1); // 1ms budget -- will be exceeded
        } catch (QueryTimeoutException e) {
            System.out.println("Caught: " + e.getMessage());
        }
    }
}
```

How to run: `java QueryHintsLevel3.java`

The first call finishes well within its 5-second budget. The second call, iterating over 50 million rows with only a 1-millisecond budget, throws `QueryTimeoutException` partway through — standing in for how `jakarta.persistence.query.timeout` causes a real database driver to abort a runaway query server-side and surface a timeout exception back to the application, rather than letting it run unbounded.

## 6. Walkthrough

Execution starts in `main` for Level 3. First, `findByStatusReadOnlyWithTimeout(orders, "SHIPPED", 5000)` runs against the small 3-order list — the elapsed-time check on every iteration never comes close to 5000ms, so the loop completes normally, filtering down to the 2 `SHIPPED` orders and returning them without ever registering a snapshot (the read-only hint's effect). "Succeeded within timeout: 2 orders" is printed.

Next, a 50-million-row `hugeDataset` is built, and `findByStatusReadOnlyWithTimeout(hugeDataset, "SHIPPED", 1)` is called with a deliberately tiny 1-millisecond budget. As the loop iterates, the elapsed-time check (`(System.nanoTime() - start) / 1_000_000 > timeoutMillis`) quickly becomes `true` — almost certainly within the first few thousand iterations — and `QueryTimeoutException` is thrown, unwinding out of the method entirely. The `catch` block in `main` catches it and prints "Caught: Query exceeded timeout of 1ms".

```
small dataset, 5000ms budget  -> loop completes -> 2 orders returned, no timeout
huge dataset, 1ms budget      -> elapsed check trips mid-loop -> QueryTimeoutException thrown -> caught
```

In a real Spring Data JPA repository, `@QueryHints({@QueryHint(name="org.hibernate.readOnly", value="true"), @QueryHint(name="jakarta.persistence.query.timeout", value="100")})` on a method attaches both hints to the same generated query: Hibernate skips dirty-check snapshotting for every returned `Order` (the read-only hint), and the JDBC driver aborts the query server-side if it runs past 100 milliseconds (the timeout hint), surfacing as a `QueryTimeoutException` that propagates up through the repository call — protecting the application from an unexpectedly slow query on a table that's grown far larger than expected.

## 7. Gotchas & takeaways

> Gotcha: hint *names* (like `"org.hibernate.readOnly"`) are provider-specific strings, not type-checked constants — a typo in the hint name is silently ignored by JPA rather than causing a compile or even a runtime error, so a mistyped hint quietly does nothing.

- `@QueryHints` attaches provider-specific instructions to a query without changing which rows come back.
- `readOnly=true` skips persistence-context snapshot-tracking for the returned entities — a real win for pure read/reporting queries, but mutations on the result are silently never persisted.
- A timeout hint bounds how long a query is allowed to run, protecting against runaway queries on unexpectedly large tables.
- Multiple hints can be combined on one method via `@QueryHints({...})`, each controlling an independent aspect of query execution.
