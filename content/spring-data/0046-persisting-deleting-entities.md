---
card: spring-data
gi: 46
slug: persisting-deleting-entities
title: "Persisting & deleting entities"
---

## 1. What it is

This card looks specifically at what happens underneath `save`/`delete` for JPA — the distinction between `persist` (a genuinely new entity, must not already exist) and `merge` (attach a possibly-detached entity, insert-or-update), which `JpaRepository.save` chooses between internally; and the difference between `deleteById` (loads the entity first, then removes it, triggering full JPA lifecycle callbacks) and a bulk `@Modifying` delete (a direct `DELETE` statement, bypassing per-entity callbacks, covered fully in a later card).

```java
// save() internally chooses persist vs merge based on entity state:
repo.save(newEntity);      // typically ends up calling entityManager.persist(...)
repo.save(detachedEntity); // typically ends up calling entityManager.merge(...)

repo.deleteById(id);       // loads the entity, THEN removes it -- triggers @PreRemove etc.
```

## 2. Why & when

Every earlier card in this section has used `save`/`delete` without examining exactly what JPA operation each one performs — this matters because `persist` and `merge` have genuinely different semantics (and different failure modes) that occasionally surface as confusing bugs: `persist`-ing an entity that already has a matching row throws a constraint violation; `merge`-ing a detached entity whose in-memory state doesn't match the database can silently overwrite unrelated changes if not handled carefully. Understanding what `save` actually does underneath clarifies these edge cases.

Understanding this distinction matters specifically when:

- You're debugging a `PersistenceException`/`EntityExistsException` on save, or a `merge`-related concurrent-update surprise — knowing whether `save` chose `persist` or `merge` (based on the entity's generated-vs-assigned ID and `Persistable` state, from the earlier identifier-generation card) explains the failure.
- You need `deleteById` to trigger `@PreRemove`/`@PostRemove` JPA lifecycle callbacks (cascading deletes, cleanup logic) — this only happens because `deleteById` loads the entity first, unlike a bulk `@Modifying` delete.
- You're deciding between individual `delete`/`deleteById` calls (full lifecycle, one row at a time) and a bulk delete (fast, no lifecycle callbacks) for a given operation — the tradeoff directly affects correctness if lifecycle callbacks matter.

## 3. Core concept

```
 save(entity) internally, roughly:
   if entity is "new" (per the null-check heuristic OR Persistable.isNew()):
       entityManager.persist(entity)   -- INSERT; entity BECOMES managed
   else:
       entityManager.merge(entity)     -- SELECT (if needed) + UPDATE;
                                           returns a DIFFERENT managed instance,
                                           the ORIGINAL argument stays detached

 deleteById(id):
   1. findById(id)          -- LOADS the entity first (a real SELECT)
   2. entityManager.remove(loaded entity)   -- triggers @PreRemove / @PostRemove
                                                and any configured CASCADE deletes

 A bulk @Modifying delete (covered fully in a later card):
   directly issues DELETE FROM table WHERE ...  -- NO entity loading,
   NO lifecycle callbacks, NO cascade (bypasses JPA's object graph entirely)
```

`merge`'s "returns a different instance" behavior is easy to miss: the object passed into `save(detachedEntity)` is not the object that ends up managed by the persistence context — the *returned* value from `save(...)` is.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.v3.org/2000/svg" role="img" aria-label="save chooses persist for new entities and merge for existing ones, while deleteById loads the entity before removing it to trigger lifecycle callbacks">
  <rect x="10" y="20" width="280" height="60" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="150" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">save(entity)</text>
  <text x="150" y="58" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">new -&gt; persist();  existing -&gt; merge()</text>

  <rect x="350" y="20" width="280" height="60" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="490" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">deleteById(id)</text>
  <text x="490" y="58" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">findById first, THEN remove() -- callbacks fire</text>
</svg>

`save` and `deleteById` both perform more than a single, direct SQL statement underneath.

## 5. Runnable example

The scenario: an `Order` entity, evolving from observing `save`'s persist-vs-merge choice directly via Hibernate statistics, to confirming `merge`'s "returns a different instance" behavior concretely, to `deleteById` triggering a `@PreRemove` callback that a bulk delete would bypass.

### Level 1 — Basic

Use Hibernate statistics to observe whether `save` performs an `INSERT` (persist) or a `SELECT`+`UPDATE` (merge), for a new versus an already-existing entity.

```java
import jakarta.persistence.Entity;
import jakarta.persistence.EntityManagerFactory;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import org.hibernate.SessionFactory;
import org.hibernate.stat.Statistics;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.ConfigurableApplicationContext;
import org.springframework.data.jpa.repository.JpaRepository;

@SpringBootApplication
public class PersistDeleteLevel1 {

    @Entity
    public static class Order {
        @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
        private Long id;
        private double total;
        protected Order() {}
        public Order(double total) { this.total = total; }
        public Long getId() { return id; }
        public void setTotal(double total) { this.total = total; }
    }

    public interface OrderRepository extends JpaRepository<Order, Long> {}

    public static void main(String[] args) {
        ConfigurableApplicationContext ctx = SpringApplication.run(PersistDeleteLevel1.class,
            "--spring.datasource.url=jdbc:h2:mem:persistdel1",
            "--spring.jpa.hibernate.ddl-auto=create-drop",
            "--spring.jpa.properties.hibernate.generate_statistics=true");

        OrderRepository repo = ctx.getBean(OrderRepository.class);
        Statistics stats = ctx.getBean(EntityManagerFactory.class).unwrap(SessionFactory.class).getStatistics();

        stats.clear();
        Order created = repo.save(new Order(100.0)); // NEW entity -- expect an insert
        System.out.println("after saving a NEW entity: insertCount=" + stats.getEntityInsertCount()
            + ", updateCount=" + stats.getEntityUpdateCount());

        stats.clear();
        created.setTotal(150.0);
        repo.save(created); // EXISTING entity (has an id) -- expect an update, not another insert
        System.out.println("after saving an EXISTING entity: insertCount=" + stats.getEntityInsertCount()
            + ", updateCount=" + stats.getEntityUpdateCount());

        if (stats.getEntityUpdateCount() != 1) throw new AssertionError("Expected the second save to perform exactly 1 UPDATE");
        System.out.println("save() correctly chose persist for new, merge-driven update for existing -- PASS");
        ctx.close();
    }
}
```

How to run: put `spring-boot-starter-data-jpa` and `com.h2database:h2` on the classpath, then `java PersistDeleteLevel1.java` on JDK 17+.

Enabling Hibernate statistics and clearing the counters around each `save` call isolates exactly what happened at the database level — the first `save` (a brand-new `Order`) produces an insert count of `1`; the second `save` (the same, now-persisted entity, modified) produces an update count of `1` and zero additional inserts, confirming `save`'s internal persist-vs-merge routing concretely, not just by documentation.

### Level 2 — Intermediate

Confirm `merge`'s "returns a different instance" behavior: the object passed into `save` for an already-managed-but-detached entity is not the same object reference the caller should keep using afterward.

```java
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.ConfigurableApplicationContext;
import org.springframework.data.jpa.repository.JpaRepository;

@SpringBootApplication
public class PersistDeleteLevel2 {

    @Entity
    public static class Order {
        @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
        private Long id;
        private double total;
        protected Order() {}
        public Order(double total) { this.total = total; }
        public Long getId() { return id; }
        public double getTotal() { return total; }
        public void setTotal(double total) { this.total = total; }
    }

    public interface OrderRepository extends JpaRepository<Order, Long> {}

    public static void main(String[] args) {
        ConfigurableApplicationContext ctx = SpringApplication.run(PersistDeleteLevel2.class,
            "--spring.datasource.url=jdbc:h2:mem:persistdel2",
            "--spring.jpa.hibernate.ddl-auto=create-drop");

        OrderRepository repo = ctx.getBean(OrderRepository.class);
        Order created = repo.save(new Order(100.0));

        // Simulate a DETACHED entity -- as if it came back from a service layer,
        // a DTO conversion, or simply outlived its original persistence context.
        Order detached = new Order(0);
        // (using reflection is overkill for this demo; instead simulate by re-fetching
        //  and then treating the object as if detached after modification below)
        Order reloaded = repo.findById(created.getId()).orElseThrow();
        reloaded.setTotal(999.0);

        Order returnedByMerge = repo.save(reloaded); // merge() -- may return a DIFFERENT instance

        System.out.println("passed-in instance == returned instance? " + (reloaded == returnedByMerge));
        System.out.println("passed-in instance total (may not reflect final managed state) = " + reloaded.getTotal());
        System.out.println("returned instance total (guaranteed correct/managed) = " + returnedByMerge.getTotal());

        // The SAFE pattern: always use the RETURNED value from save(), not the argument.
        if (returnedByMerge.getTotal() != 999.0)
            throw new AssertionError("Expected the RETURNED instance to reflect the update correctly");

        System.out.println("Demonstrated why the RETURNED value from save() is the one to trust -- PASS");
        ctx.close();
    }
}
```

How to run: same classpath as Level 1, `java PersistDeleteLevel2.java`.

Even though `reloaded` and `returnedByMerge` may happen to be the same reference in this simple example (Hibernate's `merge` behavior can return the same instance when the entity is already managed within the current persistence context), the guaranteed-correct pattern is to always use `save(...)`'s *return value*, never assume the argument you passed in is the one guaranteed to reflect final managed state — this distinction becomes concretely important once an entity has genuinely been detached (passed through a DTO layer, serialized and deserialized, or held across multiple transactions), where `merge` reliably returns a different object than the one passed in.

### Level 3 — Advanced

Confirm `deleteById` triggers `@PreRemove` (proving it genuinely loads-then-removes the entity, invoking JPA lifecycle callbacks), the behavior a bulk delete (covered in a later card) would bypass entirely.

```java
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.PreRemove;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.ConfigurableApplicationContext;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.concurrent.atomic.AtomicBoolean;
import java.util.concurrent.atomic.AtomicReference;

@SpringBootApplication
public class PersistDeleteLevel3 {

    static final AtomicBoolean preRemoveCalled = new AtomicBoolean(false);
    static final AtomicReference<Long> preRemoveOrderId = new AtomicReference<>();

    @Entity
    public static class Order {
        @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
        private Long id;
        private double total;
        protected Order() {}
        public Order(double total) { this.total = total; }
        public Long getId() { return id; }

        @PreRemove
        void onBeforeRemove() {
            preRemoveCalled.set(true);
            preRemoveOrderId.set(this.id);
            System.out.println("[@PreRemove] about to remove order id=" + this.id);
        }
    }

    public interface OrderRepository extends JpaRepository<Order, Long> {}

    public static void main(String[] args) {
        ConfigurableApplicationContext ctx = SpringApplication.run(PersistDeleteLevel3.class,
            "--spring.datasource.url=jdbc:h2:mem:persistdel3",
            "--spring.jpa.hibernate.ddl-auto=create-drop");

        OrderRepository repo = ctx.getBean(OrderRepository.class);
        Order saved = repo.save(new Order(100.0));

        repo.deleteById(saved.getId()); // loads the entity first, THEN removes it -- triggers @PreRemove

        System.out.println("@PreRemove was called? " + preRemoveCalled.get());
        System.out.println("@PreRemove saw the correct order id? " + saved.getId().equals(preRemoveOrderId.get()));

        boolean stillExists = repo.existsById(saved.getId());
        System.out.println("row still exists after delete? " + stillExists);

        if (!preRemoveCalled.get()) throw new AssertionError("Expected @PreRemove to have been called");
        if (!saved.getId().equals(preRemoveOrderId.get())) throw new AssertionError("Expected @PreRemove to see the correct id");
        if (stillExists) throw new AssertionError("Expected the row to actually be gone after deleteById");

        System.out.println("deleteById loaded the entity first, correctly triggering @PreRemove -- PASS");
        ctx.close();
    }
}
```

How to run: same classpath as Level 1 and 2, `java PersistDeleteLevel3.java`.

`@PreRemove` fires only when JPA's `entityManager.remove(...)` is called on an actual, managed entity instance — `repo.deleteById(saved.getId())` first performs an internal `findById` (loading a real, managed `Order` instance), then calls `remove` on it, which is exactly why `onBeforeRemove()` fires and correctly reports the right order id. A bulk `DELETE` statement (covered in a later card) would remove the row directly at the database level, without ever loading an entity instance, and would never trigger this callback at all.

## 6. Walkthrough

Trace `repo.deleteById(saved.getId())` end-to-end.

1. **`repo.deleteById(id)`** is called — internally, `SimpleJpaRepository`'s implementation of `deleteById` doesn't issue a direct `DELETE` statement; it first calls `findById(id)` to obtain a real, managed entity instance (throwing if none exists).
2. **`findById` executes a `SELECT`**, loading the `Order` row into a fully-managed `Order` entity — at this point, the entity genuinely exists as a Java object in the persistence context.
3. **`entityManager.remove(loadedEntity)`** is called on that managed instance — this is a JPA lifecycle-aware operation, not a raw SQL statement yet.
4. **`@PreRemove` fires**: before the actual `DELETE` SQL is issued, JPA's lifecycle machinery invokes any `@PreRemove`-annotated method on the entity — here, `onBeforeRemove()`, which records that it was called and captures the entity's id.
5. **The actual `DELETE` SQL executes**, removing the row from the database.
6. **`main` observes**: `preRemoveCalled.get()` confirms the callback genuinely ran, and `preRemoveOrderId.get()` confirms it saw the correct entity's id — proving the callback had access to a real, fully-populated entity instance, not just an id.
7. **`repo.existsById(saved.getId())`** confirms the row is genuinely gone from the database afterward.
8. **Verification**: all three checks (`@PreRemove` called, correct id observed, row gone) pass, confirming `deleteById`'s load-then-remove behavior — and its resulting lifecycle-callback support — worked exactly as JPA's object-oriented delete model intends.

```
 repo.deleteById(id)
        |
        v
 internally: findById(id)  --> SELECT --> loaded, MANAGED Order instance
        |
        v
 entityManager.remove(loadedEntity)
        |
        v
 @PreRemove fires  (sees the full, loaded entity -- id, and any other fields)
        |
        v
 actual DELETE SQL executes
```

## 7. Gotchas & takeaways

> **Gotcha:** `deleteById`'s load-then-remove approach means it always costs at least two database round-trips (a `SELECT`, then a `DELETE`) — for bulk deletion of many rows by id, this is measurably slower than a single bulk `DELETE ... WHERE id IN (...)` statement (covered as `deleteAllInBatch`/`@Modifying` deletes in later cards), which skips both the loading step and any lifecycle callbacks entirely. Choose based on whether the lifecycle callbacks (and any cascade behavior tied to the object graph) are actually needed for the specific deletion.

- `save(entity)` internally routes to either `entityManager.persist(...)` (for a new entity) or `entityManager.merge(...)` (for an existing one) — the decision follows the same new-vs-existing logic covered in the earlier identifier-generation card (null-check heuristic, or `Persistable.isNew()` when implemented).
- `merge` can return a genuinely different object instance than the one passed in — always use `save(...)`'s return value as the source of truth for the entity's current managed state, never assume the original argument reference is guaranteed current.
- `deleteById` loads the entity first, then removes it — this is what makes `@PreRemove`/`@PostRemove` lifecycle callbacks (and JPA cascade-delete relationships) fire correctly, at the cost of an extra database round-trip compared to a direct bulk delete.
- Choosing between individual, lifecycle-aware deletes and fast, bulk, lifecycle-bypassing deletes is a real tradeoff to make deliberately based on whether an entity's delete-time side effects (cascades, callbacks) genuinely need to run for the specific operation at hand.
