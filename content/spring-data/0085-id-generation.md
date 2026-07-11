---
card: spring-data
gi: 85
slug: id-generation
title: "ID generation"
---

## 1. What it is

Spring Data JDBC decides between insert and update purely by checking whether an aggregate root's `@Id` field is `null` (as the `JdbcAggregateTemplate` card showed) — which means ID generation strategy matters more directly here than in JPA: the ID is typically either database-generated (an auto-increment/identity column, left `null` until after insert) or a `@Version`-like pre-assigned value your own code supplies before calling `save`.

```java
class Order {
    @Id Long id; // null on a new instance -- database assigns it via an IDENTITY/auto-increment column
    String status;
}
// After save(): order.id is populated with the database-generated value
```

## 2. Why & when

The `JdbcAggregateTemplate` card explained that a `null` ID means insert and a non-null ID means update — this card is about exactly how that ID gets populated in the first place, and the consequences of getting it wrong. Unlike JPA (which supports several `@GeneratedValue` strategies with more configuration flexibility), Spring Data JDBC's simpler model makes this one decision — is the ID database-generated or application-assigned — more load-bearing.

Reach for an explicit understanding of ID generation specifically when:

- You're defining a new aggregate root and need to decide whether its primary key should be an auto-incrementing database column (simplest, works well with the null-means-insert convention) or a value your application assigns itself (e.g., a UUID generated in code).
- You're debugging a save that unexpectedly performs an `UPDATE` instead of an `INSERT` (or vice versa) — this is almost always an ID-generation mismatch: an application-assigned ID makes every new instance look "existing" to the null-check.
- You need globally unique, application-assigned IDs (e.g., UUIDs, for merging data from multiple sources) rather than per-table auto-increment — this requires an explicit strategy, since the ID can no longer be `null`-checked to distinguish new from existing.

## 3. Core concept

```
 Database-generated (IDENTITY column):
   new Order(null, "PENDING")   -- id is null
   save() -> INSERT (id omitted) -> DB assigns id=42 -> Spring Data JDBC reads it back -> order.id = 42

 Application-assigned (e.g., UUID):
   new Order(UUID.randomUUID(), "PENDING")  -- id is ALREADY non-null!
   save() -> Spring Data JDBC sees non-null id -> treats as UPDATE -- WRONG, this is actually new!
   -- must implement Persistable<ID> to override "is this new?" with its own logic, not just a null check
```

An application-assigned, non-null ID on a brand-new aggregate breaks the default null-check convention — a `Persistable<ID>` override is required to correctly signal "this is new" despite having an ID already.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.v3.org/2000/svg" role="img" aria-label="A database-generated ID stays null until after insert, while an application-assigned ID requires Persistable to correctly signal newness">
  <rect x="20" y="15" width="280" height="65" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="160" y="37" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">Database-generated ID</text>
  <text x="160" y="55" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="sans-serif">id=null before save</text>
  <text x="160" y="70" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="sans-serif">null-check correctly implies INSERT</text>

  <rect x="340" y="15" width="280" height="65" rx="8" fill="#1c2430" stroke="#f85149" stroke-width="1.5"/>
  <text x="480" y="37" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">Application-assigned ID</text>
  <text x="480" y="55" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="sans-serif">id=UUID already set, even though NEW</text>
  <text x="480" y="70" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="sans-serif">null-check WRONGLY implies UPDATE</text>

  <rect x="150" y="110" width="340" height="45" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="320" y="132" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">implement Persistable&lt;ID&gt;.isNew()</text>
  <text x="320" y="147" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">to override the default null-check</text>

  <line x1="480" y1="80" x2="360" y2="105" stroke="#8b949e" stroke-width="1.3" marker-end="url(#ig)"/>
  <defs><marker id="ig" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Database-generated IDs work naturally with the null-check convention; application-assigned IDs need `Persistable` to correctly declare their own newness.

## 5. Runnable example

The scenario: saving new orders, evolving from the default database-generated-ID path working correctly, to the same null-check convention breaking with a pre-assigned UUID, to a `Persistable`-based fix restoring correct insert-vs-update behavior.

### Level 1 — Basic

Model the database-generated ID path: a new order starts with `id = null`, and the "database" assigns an ID during save.

```java
import java.util.*;

class Order { Long id; String status; Order(Long id, String status) { this.id = id; this.status = status; } }

class OrderRepository {
    Map<Long, Order> db = new HashMap<>();
    private long nextId = 1;

    Order save(Order order) {
        boolean isNew = order.id == null; // default Spring Data JDBC convention
        if (isNew) {
            order.id = nextId++; // database "assigns" the id -- IDENTITY/auto-increment column
            System.out.println("  INSERT (id was null) -> db-assigned id=" + order.id);
        } else {
            System.out.println("  UPDATE (id=" + order.id + " already present)");
        }
        db.put(order.id, order);
        return order;
    }
}

public class IdGenLevel1 {
    public static void main(String[] args) {
        OrderRepository repo = new OrderRepository();

        Order order = repo.save(new Order(null, "PENDING")); // new -- id starts null
        System.out.println("After save, id is now: " + order.id);
    }
}
```

How to run: `java IdGenLevel1.java`

`order.id` starts `null`, correctly triggers the insert path, and ends up populated with the database-assigned value (`1`) — this is the straightforward, default-friendly case: a database-generated ID naturally starts `null` on every genuinely new instance.

### Level 2 — Intermediate

Introduce an application-assigned UUID and show the null-check convention breaking: a brand-new order, because its ID is pre-assigned, is mistakenly treated as an update.

```java
import java.util.*;

class Order { UUID id; String status; Order(UUID id, String status) { this.id = id; this.status = status; } }

class OrderRepository {
    Map<UUID, Order> db = new HashMap<>();

    Order save(Order order) {
        boolean isNew = order.id == null; // SAME default convention as Level 1
        if (isNew) {
            order.id = UUID.randomUUID();
            System.out.println("  INSERT (id was null)");
        } else {
            System.out.println("  UPDATE (id=" + order.id + " already present) -- but is this ACTUALLY an update?!");
        }
        db.put(order.id, order);
        return order;
    }
}

public class IdGenLevel2 {
    public static void main(String[] args) {
        OrderRepository repo = new OrderRepository();

        UUID applicationAssignedId = UUID.randomUUID(); // assigned by OUR code, before save is ever called
        Order order = new Order(applicationAssignedId, "PENDING"); // this order is BRAND NEW, but its id is non-null!

        repo.save(order); // WRONGLY treated as an update, even though this row has never existed
        System.out.println("Was this really an update? The row didn't exist in db before this call!");
    }
}
```

How to run: `java IdGenLevel2.java`

Even though `order` has never been saved before, the null-check sees a non-null `id` (assigned by application code before `save` was ever called) and incorrectly takes the "UPDATE" branch — in a real database, this would generate an `UPDATE ... WHERE id = ?` that affects zero rows, since no row with that ID exists yet, silently failing to persist the new order at all.

### Level 3 — Advanced

Fix the problem with a `Persistable`-style override: the entity itself tracks whether it's new independently of its ID being set, restoring correct insert-vs-update behavior for application-assigned IDs.

```java
import java.util.*;

// Stands in for org.springframework.data.domain.Persistable<UUID>
interface Persistable { UUID getId(); boolean isNew(); }

class Order implements Persistable {
    UUID id; String status;
    private final boolean isNewFlag; // set explicitly at construction time, independent of id being null or not

    // Factory for a genuinely NEW order: id is assigned NOW, but isNew is explicitly true.
    static Order createNew(String status) {
        return new Order(UUID.randomUUID(), status, true);
    }
    // Factory for reconstructing an EXISTING order (e.g., from a query result): isNew is explicitly false.
    static Order existing(UUID id, String status) {
        return new Order(id, status, false);
    }
    private Order(UUID id, String status, boolean isNewFlag) { this.id = id; this.status = status; this.isNewFlag = isNewFlag; }

    public UUID getId() { return id; }
    public boolean isNew() { return isNewFlag; } // overrides the default null-check entirely
}

class OrderRepository {
    Map<UUID, Order> db = new HashMap<>();

    Order save(Order order) {
        // Spring Data JDBC checks Persistable.isNew() INSTEAD of a plain null-check, when the entity implements it.
        if (order.isNew()) {
            System.out.println("  INSERT (Persistable.isNew() == true) -- id=" + order.getId() + " assigned by application code");
        } else {
            System.out.println("  UPDATE (Persistable.isNew() == false) -- id=" + order.getId() + " must already exist");
        }
        db.put(order.getId(), order);
        return order;
    }
}

public class IdGenLevel3 {
    public static void main(String[] args) {
        OrderRepository repo = new OrderRepository();

        Order brandNew = Order.createNew("PENDING"); // has a non-null UUID, but correctly reports isNew()=true
        repo.save(brandNew); // correctly INSERTs, despite the non-null id

        Order reloaded = Order.existing(brandNew.id, "PENDING"); // simulates a later query result
        reloaded.status = "SHIPPED"; // conceptually mutated after reloading
        repo.save(reloaded); // correctly UPDATEs, because isNew() is explicitly false this time
    }
}
```

How to run: `java IdGenLevel3.java`

`Order.createNew(...)` assigns a UUID immediately but explicitly marks `isNewFlag = true`, so `save()` correctly takes the insert path despite `id` being non-null. `Order.existing(...)` (standing in for an entity reconstructed from a query result) explicitly marks `isNewFlag = false`, so a later `save()` on it correctly takes the update path — `Persistable.isNew()` decouples "is this new" from "does this have an ID," fixing exactly the problem Level 2 demonstrated.

## 6. Walkthrough

Execution starts in `main` for Level 3. First, `Order.createNew("PENDING")` is called: it generates a fresh `UUID.randomUUID()` for `id` and passes `true` explicitly for `isNewFlag` — `brandNew.id` is non-null, but `brandNew.isNew()` correctly returns `true` regardless.

`repo.save(brandNew)` runs: instead of checking `order.getId() == null` (which would be `false`, and wrongly imply "update"), it calls `order.isNew()`, which returns `true` — so the insert branch runs, printing "INSERT ... id assigned by application code" and storing the order under its UUID key.

Next, `Order.existing(brandNew.id, "PENDING")` is called, standing in for how a real query result would be reconstructed — passing the *same* UUID (as if freshly loaded from the database) but with `isNewFlag` explicitly `false` this time. `reloaded.status` is set to `"SHIPPED"`, simulating an in-memory mutation after loading.

`repo.save(reloaded)` runs: `reloaded.isNew()` returns `false`, so the update branch executes, printing "UPDATE ... id must already exist" — correctly treating this as a modification of the already-persisted row from the first save, not a duplicate insert attempt.

```
Order.createNew("PENDING")   -> id=<uuid>, isNew()=true   -> save() -> INSERT branch (correct!)
Order.existing(<same uuid>, "PENDING") -> isNew()=false     -> save() -> UPDATE branch (correct!)
```

In a real Spring Data JDBC application, an aggregate root using application-assigned IDs (UUIDs, or IDs copied in from another system) should implement `Persistable<ID>` and override `isNew()` with logic independent of whether the ID field is set — often backed by a transient boolean flag (as modeled here) or a check against a `@CreatedDate`/version field. Without this override, `JdbcAggregateTemplate`'s default null-check would misclassify every application-assigned-ID entity as "already existing," causing every attempted insert to silently become a no-op `UPDATE` against a nonexistent row.

## 7. Gotchas & takeaways

> Gotcha: the symptom of this ID-generation mismatch is often *not* an exception — an `UPDATE ... WHERE id = ?` that matches zero rows typically just succeeds silently with zero rows affected, meaning a new entity can appear to save without error while never actually being persisted at all, a bug that's easy to miss until data is later queried and found missing.

- Spring Data JDBC's default insert-vs-update decision is a plain `null` check on the `@Id` field — this works naturally for database-generated (auto-increment/identity) IDs.
- Application-assigned, non-null IDs (like UUIDs generated in code) break that default convention, since a brand-new entity's ID is never `null`.
- `Persistable<ID>`'s `isNew()` method lets an entity declare its own newness explicitly, independent of whether its ID happens to be set.
- A silently-failing "phantom" update (zero rows affected, no exception) is the classic symptom of this mismatch — always implement `Persistable` when using application-assigned IDs.
