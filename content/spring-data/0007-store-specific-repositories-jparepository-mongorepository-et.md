---
card: spring-data
gi: 7
slug: store-specific-repositories-jparepository-mongorepository-et
title: "Store-specific repositories (JpaRepository, MongoRepository, etc.)"
---

## 1. What it is

Store-specific repository interfaces — `JpaRepository<T, ID>` for relational databases, `MongoRepository<T, ID>` for MongoDB, `CassandraRepository<T, ID>`, `ElasticsearchRepository<T, ID>`, `Neo4jRepository<T, ID>`, and others — each extend the Commons hierarchy (`ListCrudRepository`, `ListPagingAndSortingRepository`, `QueryByExampleExecutor`) and add operations that make sense only for their particular underlying store. `JpaRepository` adds JPA-flavored batch operations and `flush()`; `MongoRepository` adds Mongo-specific finder conveniences; each module's repository interface is where the shared Commons contract meets the store's actual capabilities.

```java
public interface CustomerRepository extends JpaRepository<Customer, Long> {}
// inherits everything from ListCrudRepository + ListPagingAndSortingRepository,
// PLUS JPA-specific extras: saveAndFlush, deleteAllInBatch, getReferenceById, ...
```

## 2. Why & when

Commons abstractions (`Repository`, `CrudRepository`, `PagingAndSortingRepository`) deliberately stay store-agnostic — they describe operations every reasonable data store can support. But real stores have real differences: a relational database supports `flush()`-then-continue-in-the-same-transaction semantics that make no sense for a document store; MongoDB supports geo-spatial queries a relational database has no native concept of. Store-specific repository interfaces exist to expose exactly those store-specific capabilities, on top of the shared foundation, without polluting the Commons contract with operations only some stores could ever implement.

Reach for a store-specific repository interface (rather than a bare Commons one) specifically when:

- You're building against a specific store — almost every real Spring Data application extends the matching store-specific interface (`JpaRepository` for JPA, `MongoRepository` for MongoDB) rather than `CrudRepository` directly, since it costs nothing and unlocks store-specific extras for free.
- You need a store-specific capability — JPA's `saveAndFlush` (write immediately, don't wait for the transaction to end) or `getReferenceById` (a lazy proxy reference without a query), or MongoDB's native geo-near queries — that the Commons interfaces don't and can't expose.
- You're reading unfamiliar Spring Data code and see a method that isn't part of `CrudRepository`/`PagingAndSortingRepository` — checking which store-specific interface the repository extends usually explains where it came from.

## 3. Core concept

```
                          Repository<T, ID>
                                 |
                     CrudRepository<T, ID>
                                 |
                  PagingAndSortingRepository<T, ID>
                     /                        \
        JpaRepository<T, ID>          MongoRepository<T, ID>
        (relational, via JPA)          (MongoDB documents)
                |                                |
        + saveAndFlush(entity)           + findByLocationNear(point)  (example)
        + deleteAllInBatch()             + <geo/text-search specific methods>
        + getReferenceById(id)
        + flush()
        + findAll(Example<S>)  (from QueryByExampleExecutor, inherited by both)
```

Every store-specific interface inherits the full Commons contract unchanged, then adds only what genuinely makes sense for that store.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="JpaRepository and MongoRepository both extend the shared Commons hierarchy and add their own store-specific methods">
  <rect x="220" y="15" width="200" height="45" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">PagingAndSortingRepository</text>

  <rect x="60" y="110" width="220" height="65" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="170" y="132" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">JpaRepository&lt;T, ID&gt;</text>
  <text x="170" y="148" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">+ saveAndFlush, flush,</text>
  <text x="170" y="162" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">+ getReferenceById</text>

  <rect x="360" y="110" width="220" height="65" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="470" y="132" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">MongoRepository&lt;T, ID&gt;</text>
  <text x="470" y="148" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">+ insert, geo/text-search</text>
  <text x="470" y="162" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">+ Mongo-specific extras</text>

  <line x1="270" y1="60" x2="185" y2="105" stroke="#8b949e" stroke-width="1.5" marker-end="url(#a)"/>
  <line x1="360" y1="60" x2="460" y2="105" stroke="#8b949e" stroke-width="1.5" marker-end="url(#a)"/>
  <defs><marker id="a" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Both interfaces inherit the same shared paging/sorting/CRUD contract, then diverge based on what their store actually supports.

## 5. Runnable example

The scenario: an `Order` repository using `JpaRepository` specifically, evolving from basic inherited CRUD, to `saveAndFlush` (a JPA-specific write-timing control), to `getReferenceById` combined with batch deletion — capabilities that exist only because this repository extends the store-specific interface rather than a bare Commons one.

### Level 1 — Basic

Extend `JpaRepository` and confirm it transparently inherits every Commons-level method (`save`, `findAll` returning `List`, `findAll(Pageable)`) with zero extra declarations.

```java
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.ConfigurableApplicationContext;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

@SpringBootApplication
public class StoreSpecificLevel1 {

    @Entity
    public static class Order {
        @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
        private Long id;
        private double total;
        protected Order() {}
        public Order(double total) { this.total = total; }
        public Long getId() { return id; }
        public double getTotal() { return total; }
    }

    public interface OrderRepository extends JpaRepository<Order, Long> {}

    public static void main(String[] args) {
        ConfigurableApplicationContext ctx = SpringApplication.run(StoreSpecificLevel1.class,
            "--spring.datasource.url=jdbc:h2:mem:store1",
            "--spring.jpa.hibernate.ddl-auto=create-drop");

        OrderRepository repo = ctx.getBean(OrderRepository.class);
        repo.save(new Order(49.99));
        repo.save(new Order(129.50));

        List<Order> all = repo.findAll(); // inherited from ListCrudRepository, via JpaRepository
        System.out.println("findAll() returned List<Order>, size = " + all.size());

        var page = repo.findAll(PageRequest.of(0, 1)); // inherited from PagingAndSortingRepository
        System.out.println("first page size = " + page.getContent().size() + ", total = " + page.getTotalElements());

        if (all.size() != 2) throw new AssertionError("Expected 2 orders");
        if (page.getTotalElements() != 2) throw new AssertionError("Expected total elements = 2");
        System.out.println("JpaRepository transparently inherited the full Commons contract -- PASS");
        ctx.close();
    }
}
```

How to run: put `spring-boot-starter-data-jpa` and `com.h2database:h2` on the classpath, then `java StoreSpecificLevel1.java` on JDK 17+.

`OrderRepository extends JpaRepository<Order, Long>` gets `List<Order> findAll()` (from `ListCrudRepository`) and `Page<Order> findAll(Pageable)` (from `PagingAndSortingRepository`) without declaring either — `JpaRepository` sits at the top of the Commons hierarchy, inheriting everything below it in the chain covered by the previous cards in this section.

### Level 2 — Intermediate

Use `saveAndFlush`, a JPA-specific method with no Commons equivalent — it forces Hibernate to write pending changes to the database *immediately*, rather than waiting for the transaction (or the persistence context's natural flush timing) to do it later.

```java
import jakarta.persistence.Entity;
import jakarta.persistence.EntityManager;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.PersistenceContext;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.ConfigurableApplicationContext;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Component;
import org.springframework.transaction.annotation.Transactional;

@SpringBootApplication
public class StoreSpecificLevel2 {

    @Entity
    public static class Order {
        @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
        private Long id;
        private double total;
        protected Order() {}
        public Order(double total) { this.total = total; }
        public Long getId() { return id; }
    }

    public interface OrderRepository extends JpaRepository<Order, Long> {}

    @Component
    public static class OrderService {
        private final OrderRepository repo;
        @PersistenceContext
        private EntityManager entityManager;

        public OrderService(OrderRepository repo) { this.repo = repo; }

        @Transactional
        public long placeOrderAndCheckRowCountMidTransaction() {
            repo.save(new Order(10.0)); // NOT flushed yet -- still buffered in the persistence context
            long countBeforeFlush = countViaNativeQuery();

            Order flushedOrder = repo.saveAndFlush(new Order(20.0)); // forces an immediate write
            long countAfterFlush = countViaNativeQuery();

            System.out.println("count before saveAndFlush = " + countBeforeFlush);
            System.out.println("count after saveAndFlush  = " + countAfterFlush);
            return countAfterFlush;
        }

        private long countViaNativeQuery() {
            // A native query bypasses Hibernate's first-level cache, seeing only what's
            // actually been written to the database so far.
            return ((Number) entityManager.createNativeQuery("select count(*) from \"order\"").getSingleResult()).longValue();
        }
    }

    public static void main(String[] args) {
        ConfigurableApplicationContext ctx = SpringApplication.run(StoreSpecificLevel2.class,
            "--spring.datasource.url=jdbc:h2:mem:store2",
            "--spring.jpa.hibernate.ddl-auto=create-drop");

        OrderService service = ctx.getBean(OrderService.class);
        long finalCount = service.placeOrderAndCheckRowCountMidTransaction();

        if (finalCount != 2) throw new AssertionError("Expected 2 rows visible after saveAndFlush, got " + finalCount);
        System.out.println("saveAndFlush forced an immediate write visible to a native query -- PASS");
        ctx.close();
    }
}
```

How to run: same classpath as Level 1, `java StoreSpecificLevel2.java`.

`repo.save(new Order(10.0))` inside a `@Transactional` method typically doesn't hit the database immediately — Hibernate buffers it in the persistence context and writes it at the next natural flush point (often at transaction commit, or before a query that needs consistent data). `saveAndFlush` bypasses that buffering deliberately, forcing an immediate `INSERT`, which is why the native-query row count only reaches `2` after the `saveAndFlush` call, not after the plain `save`. This exact timing control has no equivalent in the Commons `CrudRepository` contract — it's meaningful only for JPA's persistence-context model.

### Level 3 — Advanced

Combine `getReferenceById` (a lazy, query-free reference — another JPA-specific method) with `deleteAllInBatch` (an efficient bulk-delete bypassing per-entity lifecycle callbacks) — two more capabilities unique to `JpaRepository`, used together the way a real bulk-cleanup operation would.

```java
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.ConfigurableApplicationContext;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

@SpringBootApplication
public class StoreSpecificLevel3 {

    @Entity
    public static class Order {
        @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
        private Long id;
        private double total;
        private boolean archived;
        protected Order() {}
        public Order(double total, boolean archived) { this.total = total; this.archived = archived; }
        public Long getId() { return id; }
        public double getTotal() { return total; }
        public boolean isArchived() { return archived; }
    }

    public interface OrderRepository extends JpaRepository<Order, Long> {
        List<Order> findByArchivedTrue();
    }

    public static void main(String[] args) {
        ConfigurableApplicationContext ctx = SpringApplication.run(StoreSpecificLevel3.class,
            "--spring.datasource.url=jdbc:h2:mem:store3",
            "--spring.jpa.hibernate.ddl-auto=create-drop");

        OrderRepository repo = ctx.getBean(OrderRepository.class);
        Order active = repo.save(new Order(99.0, false));
        repo.save(new Order(10.0, true));
        repo.save(new Order(20.0, true));
        repo.save(new Order(30.0, true));

        // getReferenceById -- obtains a lazy proxy WITHOUT issuing a SELECT yet.
        Order lazyRef = repo.getReferenceById(active.getId());
        System.out.println("obtained a lazy reference for id=" + lazyRef.getId() + " (no query issued yet)");
        double total = lazyRef.getTotal(); // THIS access triggers the actual SELECT
        System.out.println("accessing getTotal() triggered the lazy load: total=" + total);

        List<Order> toArchiveDelete = repo.findByArchivedTrue();
        System.out.println("archived orders to bulk-delete: " + toArchiveDelete.size());

        repo.deleteAllInBatch(toArchiveDelete); // one efficient DELETE statement, not N individual ones

        long remaining = repo.count();
        System.out.println("remaining orders after batch delete = " + remaining);

        if (total != 99.0) throw new AssertionError("Expected the lazy reference to resolve to total=99.0");
        if (remaining != 1) throw new AssertionError("Expected exactly 1 order (the active one) to remain, got " + remaining);
        System.out.println("getReferenceById lazy loading + deleteAllInBatch bulk delete both worked -- PASS");
        ctx.close();
    }
}
```

How to run: same classpath as Level 1 and 2, `java StoreSpecificLevel3.java`.

`getReferenceById(id)` returns a Hibernate proxy immediately, without querying the database — the proxy only knows the ID until one of its actual data fields (like `getTotal()`) is accessed, at which point Hibernate transparently issues the real `SELECT` to populate it. `deleteAllInBatch(toArchiveDelete)` issues a single efficient `DELETE FROM order WHERE id IN (...)` statement (or equivalent), skipping the per-entity JPA lifecycle callbacks (`@PreRemove`, and similar) that individual `delete()` calls would each trigger — appropriate for bulk cleanup where those callbacks aren't needed.

## 6. Walkthrough

Trace Level 3's `getReferenceById` sequence specifically, since the lazy-loading behavior is easy to misunderstand.

1. **`repo.getReferenceById(active.getId())`** is called. Internally, JPA's `EntityManager.getReference(...)` creates a Hibernate proxy object — a subclass of `Order` generated at runtime — populated with only the `id` field. No SQL is sent to the database at this point.
2. **`System.out.println(...)`** prints the proxy's `id`, accessible without triggering a load (the ID is already known, since it was passed in).
3. **`lazyRef.getTotal()`** is the first access to a *data* field. Hibernate's proxy intercepts this method call, notices the real entity data hasn't been loaded yet, and — at this exact moment — issues a `SELECT * FROM order WHERE id = ?` to populate the real fields, then delegates the `getTotal()` call to the now-loaded data.
4. **`repo.findByArchivedTrue()`** runs a derived query (`WHERE archived = true`), returning the 3 archived orders as a fully-loaded `List<Order>` — no lazy proxies here, since a query result set is always fully materialized.
5. **`repo.deleteAllInBatch(toArchiveDelete)`** issues one bulk `DELETE` statement targeting exactly those 3 rows' IDs — a single database round-trip, rather than 3 separate `DELETE FROM order WHERE id = ?` statements a loop over individual `delete()` calls would produce.
6. **`repo.count()`** queries the remaining row count — `1`, since only the non-archived `active` order (the one whose `total` was lazily loaded in step 3) is left.
7. **Verification**: the program checks the lazily-loaded `total` value and the final remaining count, confirming both JPA-specific mechanisms worked exactly as intended.

```
 getReferenceById(id)  --> Hibernate PROXY, id only, NO query yet
        |
        v
 lazyRef.getTotal()    --> proxy detects missing data --> SELECT issued NOW --> total populated

 findByArchivedTrue()  --> fully-loaded List<Order> (3 rows)
        |
        v
 deleteAllInBatch(...) --> ONE bulk DELETE statement, not 3 individual ones
```

## 7. Gotchas & takeaways

> **Gotcha:** `getReferenceById`'s lazy proxy throws `EntityNotFoundException` (not at the `getReferenceById` call itself, but at the *first field access* that triggers the deferred `SELECT`) if no row with that ID actually exists — because the existence check is deferred along with the load, code that calls `getReferenceById` on a nonexistent ID and never touches a data field will appear to succeed silently, only failing later and less predictably than `findById` would have.

- Store-specific interfaces (`JpaRepository`, `MongoRepository`, and others) extend the full Commons hierarchy this section has built up — `Repository` → `CrudRepository`/`ListCrudRepository` → `PagingAndSortingRepository`/`ListPagingAndSortingRepository` — inheriting everything, then adding store-specific extras.
- JPA-specific additions like `saveAndFlush`, `flush()`, `getReferenceById`, and `deleteAllInBatch` exist because JPA's persistence-context model (buffering, lazy loading, batch operations) has no direct equivalent in a document or key-value store — this is exactly the kind of capability the Commons contract deliberately leaves out.
- Almost every real Spring Data JPA application should extend `JpaRepository` rather than `CrudRepository` or `PagingAndSortingRepository` directly — there's no downside, since it inherits everything those provide and adds genuinely useful extras at no cost.
- The next cards in this section move from "which interface to extend" to "how to define and fine-tune a repository interface" — covering custom method declarations, `@RepositoryDefinition`, and `@NoRepositoryBean` in depth.
