---
card: spring-data
gi: 4
slug: crudrepository
title: "CrudRepository"
---

## 1. What it is

`CrudRepository<T, ID>` is Spring Data's standard, ready-to-use interface for full create-read-update-delete operations — it extends `Repository<T, ID>` and adds the methods almost every data-access layer needs: `save`, `saveAll`, `findById`, `existsById`, `findAll`, `count`, `deleteById`, `delete`, `deleteAll`, and a few more. Extending it is the single most common way to get a working repository in Spring Data, since it covers the vast majority of what an entity's data-access layer actually requires without declaring a single method yourself.

```java
public interface CustomerRepository extends CrudRepository<Customer, Long> {}
// save, findById, findAll, deleteById, count, existsById -- all already available
```

## 2. Why & when

The previous two cards established that `Repository<T, ID>` is an empty marker and that you *can* hand-pick exactly which methods to declare. `CrudRepository` exists because, most of the time, you don't want to hand-pick — you want the standard set that every CRUD-style data-access layer needs, without retyping the same method signatures on every repository interface in an application.

Reach for `CrudRepository` specifically when:

- You need standard create/read/update/delete operations for an entity and don't have a specific reason to restrict the exposed surface (as the read-only example in an earlier card did).
- You're prototyping or building a straightforward CRUD-style feature — a typical admin panel, a simple resource API — where the full CRUD contract matches what the feature actually needs.
- You want the shortest path to a working repository — `extends CrudRepository<T, ID>` plus zero additional method declarations is often all a simple entity's repository needs.

For relational databases specifically, `JpaRepository` (a store-specific interface covered in a later card) extends `CrudRepository` and adds JPA-specific conveniences (batch operations, `flush()`, `Example`-based queries) — many real applications extend `JpaRepository` directly rather than `CrudRepository`, but understanding `CrudRepository`'s contract first makes clear exactly what's inherited versus what's JPA-specific.

## 3. Core concept

```
 public interface CrudRepository<T, ID> extends Repository<T, ID> {
     <S extends T> S save(S entity);
     <S extends T> Iterable<S> saveAll(Iterable<S> entities);
     Optional<T> findById(ID id);
     boolean existsById(ID id);
     Iterable<T> findAll();
     Iterable<T> findAllById(Iterable<ID> ids);
     long count();
     void deleteById(ID id);
     void delete(T entity);
     void deleteAllById(Iterable<? extends ID> ids);
     void deleteAll(Iterable<? extends T> entities);
     void deleteAll();
 }
```

`save` doubles as both insert and update: if the entity's ID is null (or, for JPA, not yet persisted), it inserts; if the ID already exists in the store, the underlying implementation typically performs an update — the exact "is this new or existing" decision is store-specific, but the single `save` method covers both cases uniformly.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="CrudRepository extends Repository and adds the standard save, find, count, and delete method family">
  <rect x="230" y="20" width="180" height="45" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="320" y="47" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Repository&lt;T, ID&gt;</text>

  <rect x="150" y="100" width="340" height="70" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="125" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">CrudRepository&lt;T, ID&gt;</text>
  <text x="320" y="142" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">save, findById, existsById, findAll,</text>
  <text x="320" y="157" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">count, deleteById, delete, deleteAll</text>

  <line x1="320" y1="65" x2="320" y2="95" stroke="#8b949e" stroke-width="1.5" marker-end="url(#a)"/>
  <defs><marker id="a" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

`CrudRepository` is the standard, most commonly extended layer between the empty root and store-specific interfaces.

## 5. Runnable example

The scenario: a `Task` management repository, evolving from basic save/find/delete, to batch operations (`saveAll`, `deleteAllById`), to a full lifecycle demonstrating `save`'s dual insert-or-update behavior alongside `existsById` and `count`.

### Level 1 — Basic

Extend `CrudRepository` with zero extra methods and exercise `save`, `findById`, and `deleteById`.

```java
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.ConfigurableApplicationContext;
import org.springframework.data.repository.CrudRepository;

import java.util.Optional;

@SpringBootApplication
public class CrudRepositoryLevel1 {

    @Entity
    public static class Task {
        @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
        private Long id;
        private String title;
        private boolean done;
        protected Task() {}
        public Task(String title) { this.title = title; this.done = false; }
        public Long getId() { return id; }
        public String getTitle() { return title; }
        public boolean isDone() { return done; }
    }

    public interface TaskRepository extends CrudRepository<Task, Long> {}

    public static void main(String[] args) {
        ConfigurableApplicationContext ctx = SpringApplication.run(CrudRepositoryLevel1.class,
            "--spring.datasource.url=jdbc:h2:mem:crud1",
            "--spring.jpa.hibernate.ddl-auto=create-drop");

        TaskRepository repo = ctx.getBean(TaskRepository.class);

        Task saved = repo.save(new Task("Write report"));
        System.out.println("saved id = " + saved.getId());

        Optional<Task> found = repo.findById(saved.getId());
        System.out.println("found = " + found.map(Task::getTitle).orElse("MISSING"));

        repo.deleteById(saved.getId());
        boolean stillThere = repo.findById(saved.getId()).isPresent();
        System.out.println("still there after delete? " + stillThere);

        if (found.isEmpty()) throw new AssertionError("Expected to find the saved task");
        if (stillThere) throw new AssertionError("Expected the task to be gone after deleteById");
        System.out.println("save/findById/deleteById all worked with zero declared methods -- PASS");
        ctx.close();
    }
}
```

How to run: put `spring-boot-starter-data-jpa` and `com.h2database:h2` on the classpath, then `java CrudRepositoryLevel1.java` on JDK 17+.

`TaskRepository extends CrudRepository<Task, Long>` declares no methods of its own — `save`, `findById`, and `deleteById` all come directly from `CrudRepository`'s inherited contract, implemented automatically by Spring Data JPA's generic `SimpleJpaRepository`.

### Level 2 — Intermediate

Use `saveAll` and `deleteAllById` for batch operations, and `count`/`existsById` for cheap existence and size checks — the parts of `CrudRepository`'s contract beyond the single-entity basics.

```java
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.ConfigurableApplicationContext;
import org.springframework.data.repository.CrudRepository;

import java.util.List;

@SpringBootApplication
public class CrudRepositoryLevel2 {

    @Entity
    public static class Task {
        @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
        private Long id;
        private String title;
        protected Task() {}
        public Task(String title) { this.title = title; }
        public Long getId() { return id; }
        public String getTitle() { return title; }
    }

    public interface TaskRepository extends CrudRepository<Task, Long> {}

    public static void main(String[] args) {
        ConfigurableApplicationContext ctx = SpringApplication.run(CrudRepositoryLevel2.class,
            "--spring.datasource.url=jdbc:h2:mem:crud2",
            "--spring.jpa.hibernate.ddl-auto=create-drop");

        TaskRepository repo = ctx.getBean(TaskRepository.class);

        Iterable<Task> saved = repo.saveAll(List.of(
            new Task("Write report"), new Task("Review PR"), new Task("Deploy release")));
        List<Long> ids = java.util.stream.StreamSupport.stream(saved.spliterator(), false)
            .map(Task::getId).toList();
        System.out.println("saved " + ids.size() + " tasks, ids = " + ids);
        System.out.println("count() = " + repo.count());

        repo.deleteAllById(ids.subList(0, 2)); // delete the first two
        System.out.println("count() after deleting 2 = " + repo.count());
        System.out.println("existsById(ids.get(2)) = " + repo.existsById(ids.get(2)));
        System.out.println("existsById(ids.get(0)) = " + repo.existsById(ids.get(0)));

        if (repo.count() != 1) throw new AssertionError("Expected exactly 1 task remaining");
        if (!repo.existsById(ids.get(2))) throw new AssertionError("Expected the third task to still exist");
        if (repo.existsById(ids.get(0))) throw new AssertionError("Expected the first task to be gone");

        System.out.println("saveAll + deleteAllById + count + existsById all worked -- PASS");
        ctx.close();
    }
}
```

How to run: same classpath as Level 1, `java CrudRepositoryLevel2.java`.

`saveAll(List.of(...))` persists three tasks in one call, returning an `Iterable<Task>` with each entity's generated ID populated. `deleteAllById(ids.subList(0, 2))` removes the first two by ID in a batch, and the subsequent `count()`/`existsById` calls confirm exactly the expected one task remains — `CrudRepository`'s batch methods exist specifically to avoid looping over single-entity `save`/`deleteById` calls when working with multiple entities at once.

### Level 3 — Advanced

Demonstrate `save`'s dual insert-or-update behavior explicitly: saving a *new* entity inserts it, while saving an entity object that already carries an existing ID updates the matching row instead — the behavior that makes `save` a single method covering both cases.

```java
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.ConfigurableApplicationContext;
import org.springframework.data.repository.CrudRepository;

import java.util.Optional;

@SpringBootApplication
public class CrudRepositoryLevel3 {

    @Entity
    public static class Task {
        @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
        private Long id;
        private String title;
        private boolean done;
        protected Task() {}
        public Task(String title) { this.title = title; this.done = false; }
        public Task(Long id, String title, boolean done) { this.id = id; this.title = title; this.done = done; }
        public Long getId() { return id; }
        public String getTitle() { return title; }
        public boolean isDone() { return done; }
    }

    public interface TaskRepository extends CrudRepository<Task, Long> {}

    public static void main(String[] args) {
        ConfigurableApplicationContext ctx = SpringApplication.run(CrudRepositoryLevel3.class,
            "--spring.datasource.url=jdbc:h2:mem:crud3",
            "--spring.jpa.hibernate.ddl-auto=create-drop");

        TaskRepository repo = ctx.getBean(TaskRepository.class);

        // 1. Insert: a brand-new entity, id is null before save.
        Task created = repo.save(new Task("Write report"));
        System.out.println("after insert: id=" + created.getId() + ", done=" + created.isDone());
        long countAfterInsert = repo.count();

        // 2. Update: construct a Task carrying the SAME id as an already-persisted row.
        Task updatePayload = new Task(created.getId(), "Write report", true); // now marked done
        Task updated = repo.save(updatePayload);
        long countAfterUpdate = repo.count();

        System.out.println("after update: id=" + updated.getId() + ", done=" + updated.isDone());
        System.out.println("count after insert = " + countAfterInsert + ", count after update = " + countAfterUpdate);

        Optional<Task> reloaded = repo.findById(created.getId());
        System.out.println("reloaded from DB: done=" + reloaded.map(Task::isDone).orElse(null));

        if (countAfterInsert != 1) throw new AssertionError("Expected exactly 1 row after the insert");
        if (countAfterUpdate != 1) throw new AssertionError("save() with an existing id should UPDATE, not insert a second row");
        if (reloaded.isEmpty() || !reloaded.get().isDone())
            throw new AssertionError("Expected the reloaded task to reflect the update (done=true)");

        System.out.println("save() correctly distinguished insert vs. update by identifier -- PASS");
        ctx.close();
    }
}
```

How to run: same classpath as Level 1 and 2, `java CrudRepositoryLevel3.java`.

The first `save` call passes a `Task` with a `null` id, so Hibernate performs an `INSERT`, and the generated id is populated on return. The second `save` call passes a *new* `Task` object, but one explicitly constructed with the `id` of the already-persisted row — Hibernate recognizes this as an existing entity (based on the identifier, not object identity) and performs an `UPDATE` instead of a second `INSERT`. `count()` staying at `1` after the second `save`, combined with the reloaded entity showing `done=true`, is the concrete proof that `save` correctly routed to an update rather than creating a duplicate row.

## 6. Walkthrough

Trace Level 3's two `save` calls in detail.

1. **First `save(new Task("Write report"))`**: the `Task` passed in has `id = null` (never set). Hibernate, via `SimpleJpaRepository.save`, checks the entity's ID field — `null` means "new," so it issues an `INSERT INTO task (title, done) VALUES (?, ?)`, then reads back the database-generated identifier (from the `IDENTITY` strategy) and sets it on the returned `Task` instance.
2. **`count()` after insert**: queries `SELECT COUNT(*) FROM task`, returning `1`.
3. **Constructing the update payload**: `new Task(created.getId(), "Write report", true)` builds an entirely new Java object — not the same object reference as `created` — but one carrying the *same* database identifier.
4. **Second `save(updatePayload)`**: Hibernate again checks the ID field — this time it's non-null. `SimpleJpaRepository`'s save logic (for JPA, roughly: call `entityManager.merge(entity)` when the ID is present) treats this as an existing entity and issues an `UPDATE task SET title = ?, done = ? WHERE id = ?` rather than a second insert.
5. **`count()` after update**: still `1`, confirming no new row was created — the update replaced the existing row's data rather than adding to it.
6. **`findById(created.getId())`**: reloads directly from the database (not from any in-memory cache the example relies on), returning a `Task` with `done = true`, proving the update actually persisted, not just returned a modified in-memory object.
7. **Assertions**: the program checks the insert count, the update count, and the reloaded entity's `done` flag, printing `PASS` only if `save`'s dual behavior held at every step.

```
 save(new Task(null-id, "Write report"))
        |
        v
 id == null -> INSERT -> id generated -> count = 1

 save(new Task(existing-id, "Write report", done=true))
        |
        v
 id != null -> UPDATE existing row -> count stays 1 -> row now has done=true
```

## 7. Gotchas & takeaways

> **Gotcha:** `save`'s insert-vs-update decision for JPA is based on whether the entity's ID is null (for generated IDs) or, for manually-assigned IDs, whether Hibernate believes the entity is "new" — assigning an ID yourself to a brand-new entity (rather than letting `@GeneratedValue` populate it) can confuse this detection, causing an unexpected `UPDATE` (which silently does nothing, since no row with that ID exists yet) instead of the intended `INSERT`. When using manually-assigned IDs, Spring Data JPA typically needs the entity to implement `Persistable<ID>` to disambiguate correctly.

- `CrudRepository<T, ID>` is the standard full-CRUD contract most Spring Data repositories extend — `save`, `findById`, `existsById`, `findAll`, `count`, `deleteById`, and their batch counterparts, all inherited with zero declared methods.
- `save` genuinely serves double duty as both insert and update — there's no separate `update` method; the store-specific implementation determines which operation actually happens based on the entity's identifier state.
- Batch methods (`saveAll`, `deleteAllById`, `findAllById`) exist to avoid looping over the single-entity equivalents, and are typically more efficient at the database level as well.
- `findAll()` on plain `CrudRepository` returns `Iterable<T>`, not `List<T>` — the next card, on `ListCrudRepository`, covers the variant that returns `List<T>` directly for the common case where a `List` is more convenient than an `Iterable`.
