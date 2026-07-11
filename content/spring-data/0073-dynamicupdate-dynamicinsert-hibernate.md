---
card: spring-data
gi: 73
slug: dynamicupdate-dynamicinsert-hibernate
title: "@DynamicUpdate / @DynamicInsert (Hibernate)"
---

## 1. What it is

By default, Hibernate generates one fixed `INSERT`/`UPDATE` statement per entity at startup, listing *every* mapped column every time — even columns that weren't changed, or that are `null` on insert. `@DynamicUpdate` and `@DynamicInsert` tell Hibernate to instead build the SQL statement at runtime, including only the columns that actually changed (for update) or actually have a non-null value (for insert).

```java
@Entity
@DynamicUpdate
@DynamicInsert
class Order {
    String status; double total; String notes; // notes often null
}
```

## 2. Why & when

The persistence-context card explained that dirty checking detects *which* fields changed — `@DynamicUpdate` is what makes the generated SQL actually reflect that, instead of writing every column regardless. For most entities, the fixed statement is fine (it's prepared once, reused efficiently) — these annotations exist for the specific cases where the fixed approach causes real problems.

Reach for `@DynamicUpdate`/`@DynamicInsert` specifically when:

- An entity has many columns and updates typically touch only one or two of them — a fixed `UPDATE` still writes all columns, which can matter for tables with database-level triggers or audit logs firing on any column write, even unchanged ones.
- An entity has several nullable columns, and rows are frequently inserted with many of them absent — `@DynamicInsert` skips assigning `NULL` explicitly for absent fields, letting the database's own column defaults apply instead (a fixed `INSERT` would override any default with an explicit `NULL`).
- You're optimizing for a high-concurrency table where minimizing the "surface area" of each write (fewer columns touched) reduces lock contention or replication payload size.

## 3. Core concept

```
 Without @DynamicUpdate:
   order.status = "SHIPPED";  -- only `status` actually changed
   -- UPDATE orders SET status=?, total=?, notes=?, customer_id=?, ... WHERE id=?
   -- EVERY mapped column listed, even unchanged ones

 With @DynamicUpdate:
   order.status = "SHIPPED";  -- only `status` actually changed
   -- UPDATE orders SET status=? WHERE id=?
   -- ONLY the changed column listed

 With @DynamicInsert, inserting a row where `notes` is null:
   -- Without: INSERT INTO orders (status, total, notes, ...) VALUES (?, ?, NULL, ...)
   -- With:    INSERT INTO orders (status, total, ...) VALUES (?, ?, ...)  -- notes omitted, DB default applies
```

Both annotations shrink the generated SQL down to only the columns that are actually relevant to the specific insert or update happening.

## 4. Diagram

<svg viewBox="0 0 640 160" xmlns="http://www.v3.org/2000/svg" role="img" aria-label="DynamicUpdate narrows the generated UPDATE statement to only the columns that actually changed">
  <rect x="20" y="20" width="280" height="55" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="160" y="42" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">fixed UPDATE (default)</text>
  <text x="160" y="58" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">SET status,total,notes,customer_id...</text>

  <rect x="340" y="20" width="280" height="55" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="480" y="42" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">@DynamicUpdate</text>
  <text x="480" y="58" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">SET status  -- only changed column</text>

  <rect x="20" y="100" width="600" height="40" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.3"/>
  <text x="320" y="125" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">only order.status was mutated -- rest of the entity untouched</text>

  <line x1="320" y1="100" x2="160" y2="80" stroke="#8b949e" stroke-width="1.3" marker-end="url(#du)"/>
  <line x1="320" y1="100" x2="480" y2="80" stroke="#8b949e" stroke-width="1.3" marker-end="url(#du)"/>
  <defs><marker id="du" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

The same single-field mutation produces a full-column `UPDATE` by default, or a narrow, changed-columns-only `UPDATE` with `@DynamicUpdate`.

## 5. Runnable example

The scenario: updating and inserting orders with several columns, evolving from the fixed-statement baseline listing every column, to a dynamic-update version listing only changed columns, to a dynamic-insert version that also omits absent optional fields.

### Level 1 — Basic

Model the default fixed-statement behavior: every mapped column is listed in the generated SQL, regardless of what actually changed.

```java
import java.util.*;

class Order {
    long id; String status; double total; String notes;
    Order(long id, String status, double total, String notes) {
        this.id = id; this.status = status; this.total = total; this.notes = notes;
    }
}

public class DynamicSqlLevel1 {
    // Simulates Hibernate's DEFAULT (fixed) UPDATE statement generation: every column, always.
    static String generateFixedUpdate(Order order) {
        return "UPDATE orders SET status=" + q(order.status) + ", total=" + order.total
             + ", notes=" + q(order.notes) + " WHERE id=" + order.id;
    }
    static String q(String s) { return s == null ? "NULL" : "'" + s + "'"; }

    public static void main(String[] args) {
        Order order = new Order(1, "PENDING", 100.0, null);
        order.status = "SHIPPED"; // ONLY status actually changed

        String sql = generateFixedUpdate(order);
        System.out.println("Generated SQL: " + sql); // lists status, total, AND notes -- even though only status changed
    }
}
```

How to run: `java DynamicSqlLevel1.java`

Even though only `status` was mutated, the generated `UPDATE` lists `total` and `notes` too — this is Hibernate's default, fixed-statement behavior: one prepared statement template per entity, reused for every update regardless of which fields actually changed.

### Level 2 — Intermediate

Add a dynamic-update variant that tracks which fields actually changed (via a snapshot comparison, matching the persistence context's dirty-checking mechanism) and only includes those in the generated SQL.

```java
import java.util.*;

class Order {
    long id; String status; double total; String notes;
    Order(long id, String status, double total, String notes) {
        this.id = id; this.status = status; this.total = total; this.notes = notes;
    }
    Order copy() { return new Order(id, status, total, notes); }
}

public class DynamicSqlLevel2 {
    // @DynamicUpdate: only include columns whose value differs from the loaded snapshot.
    static String generateDynamicUpdate(Order current, Order snapshot) {
        List<String> setClauses = new ArrayList<>();
        if (!Objects.equals(current.status, snapshot.status)) setClauses.add("status=" + q(current.status));
        if (current.total != snapshot.total) setClauses.add("total=" + current.total);
        if (!Objects.equals(current.notes, snapshot.notes)) setClauses.add("notes=" + q(current.notes));
        return "UPDATE orders SET " + String.join(", ", setClauses) + " WHERE id=" + current.id;
    }
    static String q(String s) { return s == null ? "NULL" : "'" + s + "'"; }

    public static void main(String[] args) {
        Order order = new Order(1, "PENDING", 100.0, null);
        Order snapshot = order.copy(); // taken when the entity became managed (as in the persistence-context card)

        order.status = "SHIPPED"; // only this field changes

        String sql = generateDynamicUpdate(order, snapshot);
        System.out.println("Generated SQL: " + sql); // ONLY status listed now
    }
}
```

How to run: `java DynamicSqlLevel2.java`

`generateDynamicUpdate` compares each field against the `snapshot` (taken when the entity was loaded) and only adds a `SET` clause for fields that actually differ — this time the generated SQL is just `UPDATE orders SET status='SHIPPED' WHERE id=1`, matching exactly what `@DynamicUpdate` produces by leaning on the same dirty-checking comparison Hibernate already performs internally.

### Level 3 — Advanced

Add a dynamic-insert variant alongside the dynamic-update one, omitting columns with a `null`/absent value from the generated `INSERT` so the database's own column defaults can apply, and compare both against their fixed-statement equivalents.

```java
import java.util.*;

class Order {
    long id; String status; double total; String notes;
    Order(long id, String status, double total, String notes) {
        this.id = id; this.status = status; this.total = total; this.notes = notes;
    }
    Order copy() { return new Order(id, status, total, notes); }
}

public class DynamicSqlLevel3 {
    static String q(String s) { return s == null ? "NULL" : "'" + s + "'"; }

    static String fixedInsert(Order o) {
        return "INSERT INTO orders (id, status, total, notes) VALUES ("
             + o.id + ", " + q(o.status) + ", " + o.total + ", " + q(o.notes) + ")";
    }

    // @DynamicInsert: omit columns whose value is null, letting the database's own DEFAULT apply.
    static String dynamicInsert(Order o) {
        List<String> cols = new ArrayList<>(); List<String> vals = new ArrayList<>();
        cols.add("id"); vals.add(String.valueOf(o.id));
        if (o.status != null) { cols.add("status"); vals.add(q(o.status)); }
        cols.add("total"); vals.add(String.valueOf(o.total)); // primitive double, never "absent"
        if (o.notes != null) { cols.add("notes"); vals.add(q(o.notes)); } // omitted entirely when null
        return "INSERT INTO orders (" + String.join(", ", cols) + ") VALUES (" + String.join(", ", vals) + ")";
    }

    static String dynamicUpdate(Order current, Order snapshot) {
        List<String> sets = new ArrayList<>();
        if (!Objects.equals(current.status, snapshot.status)) sets.add("status=" + q(current.status));
        if (current.total != snapshot.total) sets.add("total=" + current.total);
        if (!Objects.equals(current.notes, snapshot.notes)) sets.add("notes=" + q(current.notes));
        return sets.isEmpty() ? "(no changes -- no UPDATE issued)"
                              : "UPDATE orders SET " + String.join(", ", sets) + " WHERE id=" + current.id;
    }

    public static void main(String[] args) {
        Order newOrder = new Order(2, "PENDING", 50.0, null); // notes absent -- should use DB default
        System.out.println("Fixed insert:   " + fixedInsert(newOrder));
        System.out.println("Dynamic insert: " + dynamicInsert(newOrder));

        Order existing = new Order(1, "PENDING", 100.0, "gift wrap");
        Order snapshot = existing.copy();
        existing.total = 120.0; // only total changes this time
        System.out.println("Dynamic update: " + dynamicUpdate(existing, snapshot));

        Order untouched = new Order(3, "SHIPPED", 75.0, null);
        Order sameSnapshot = untouched.copy(); // nothing mutated at all
        System.out.println("No-op update:   " + dynamicUpdate(untouched, sameSnapshot));
    }
}
```

How to run: `java DynamicSqlLevel3.java`

The fixed insert explicitly writes `NULL` for `notes`; the dynamic insert omits the `notes` column entirely, letting any database-level `DEFAULT` on that column take effect instead of being overridden by an explicit `NULL`. The dynamic update for `existing` lists only `total`, and the no-op case for `untouched` (nothing changed) correctly produces no `UPDATE` at all — matching how Hibernate skips issuing any SQL when dirty checking finds no differences.

## 6. Walkthrough

Execution starts in `main` for Level 3. First, `newOrder` is created with `notes = null`. `fixedInsert(newOrder)` builds an `INSERT` listing all four columns, including `notes=NULL` explicitly. `dynamicInsert(newOrder)` builds the column/value lists conditionally: `id`, `status` ("PENDING", non-null so included), and `total` are always added, but the `notes` check (`if (o.notes != null)`) is skipped since `notes` is `null` — so the final SQL never mentions `notes` at all, letting a database column default (if one exists) apply instead of being overwritten by an explicit `NULL`.

Next, `existing` is created and `snapshot` captures its state before mutation. `existing.total` is changed from `100.0` to `120.0`, leaving `status` and `notes` untouched. `dynamicUpdate(existing, snapshot)` compares each field: `status` matches the snapshot (no clause added), `total` differs (`120.0 != 100.0`, clause added), `notes` matches (no clause added) — producing `UPDATE orders SET total=120.0 WHERE id=1`.

Finally, `untouched` and `sameSnapshot` are identical (`sameSnapshot` was copied from `untouched` with no mutation in between). `dynamicUpdate` finds every field equal to its snapshot counterpart, so `sets` stays empty, and the method returns the "no changes" message — mirroring how Hibernate, with `@DynamicUpdate` and nothing actually dirty, skips issuing any `UPDATE` statement at all for that entity during commit.

```
newOrder (notes=null):     fixed INSERT includes "notes=NULL"; dynamic INSERT omits notes column entirely
existing (total changed):  dynamic UPDATE -> "SET total=120.0" only
untouched (nothing changed): dynamic UPDATE -> no SQL issued
```

In a real Hibernate-backed entity annotated `@DynamicUpdate @DynamicInsert`, this same logic runs automatically at flush/commit time: Hibernate compares the managed entity against its loaded snapshot (as covered in the persistence-context card) to build the `UPDATE`'s column list dynamically, and inspects each field's current value at insert time to decide whether to include it in the `INSERT`'s column list — application code never builds SQL strings itself; it's purely a change in what Hibernate generates internally for the same `save()`/`flush()` calls used throughout every earlier JPA card in this section.

## 7. Gotchas & takeaways

> Gotcha: `@DynamicUpdate`/`@DynamicInsert` add a per-write cost (building the SQL string dynamically, rather than reusing one prepared statement) — for very high-throughput entities where every column typically changes together anyway, this can be a net loss; the annotations are a targeted optimization, not a universal default.

- Hibernate's default is a *fixed* statement per entity, listing every mapped column on every insert/update — simple and fast to prepare once, reused forever.
- `@DynamicUpdate` narrows the generated `UPDATE` to only the columns that changed since the entity was loaded, based on the same dirty-checking snapshot comparison used elsewhere in JPA.
- `@DynamicInsert` narrows the generated `INSERT` to only columns with a non-null/non-default value, letting database-level column defaults apply for the rest.
- Reach for these only when many columns, frequent partial updates, or `NULL`-overriding-a-default problems make the fixed-statement approach actually costly — not as a blanket default on every entity.
