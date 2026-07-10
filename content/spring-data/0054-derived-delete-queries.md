---
card: spring-data
gi: 54
slug: derived-delete-queries
title: "Derived delete queries"
---

## 1. What it is

Derived delete queries use the `deleteBy`/`removeBy` verb prefix (mentioned briefly in the Commons section's query-derivation card) instead of `findBy` — `deleteByStatus(String status)` deletes every matching row, following the exact same property-matching and keyword grammar as any other derived query. Unlike the earlier card's `deleteById` (which loads-then-removes one entity, triggering full lifecycle callbacks), a derived delete query's actual JPA execution strategy varies by return type: a `void`/`long` return performs a genuine bulk `DELETE` statement, while a `List<T>`-returning variant loads each matching entity individually first (to return them) and removes each one, triggering lifecycle callbacks per entity.

```java
long deleteByStatus(String status);          // BULK delete -- fast, no lifecycle callbacks
List<Order> deleteByStatusAndReturn(String status); // loads each first, deletes individually, RETURNS them
```

## 2. Why & when

This return-type-dependent behavior is easy to miss and important to understand: choosing `long`/`int`/`void` versus a collection return type for a derived delete method isn't just a matter of "what data do I want back" — it fundamentally changes *how* the deletion executes at the JPA level, with real consequences for lifecycle callbacks, performance, and cascade behavior.

Reach for derived delete queries specifically when:

- You want a simple, name-driven bulk deletion (`deleteByStatus`, `deleteByCreatedAtBefore`) without writing a `@Modifying` `@Query` by hand — the derivation grammar covers deletion the same way it covers selection.
- You need the deleted entities' data returned to the caller (for logging, for cascading application-level cleanup) — declaring a collection return type triggers the load-then-delete-individually path, giving you that data at the cost of individual-row overhead.
- You're choosing between a fast bulk delete (no lifecycle callbacks, no returned data) and a slower, individually-processed delete (full lifecycle callbacks, returned data) — the return type is exactly the lever that controls this choice.

## 3. Core concept

```
 void deleteByStatus(String status);
 long deleteByStatus(String status);
        |
        v
 EXECUTES as a genuine BULK DELETE:
   DELETE FROM order WHERE status = ?
   -- ONE statement, NO entity loading, NO lifecycle callbacks (@PreRemove etc.),
      NO cascade behavior through the JPA object graph -- exactly like a
      @Modifying bulk delete, just derived from the method name instead

 List<Order> deleteByStatus(String status);
        |
        v
 EXECUTES as LOAD-THEN-DELETE-EACH:
   1. SELECT * FROM order WHERE status = ?     (loads matching entities)
   2. for EACH loaded entity: entityManager.remove(entity)
      -- triggers @PreRemove/@PostRemove PER entity, respects cascades
   3. returns the List<Order> of what was deleted
```

The return type isn't just a data-shape decision — for derived delete methods specifically, it determines the underlying execution strategy and its consequences.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.v3.org/2000/svg" role="img" aria-label="A long-returning derived delete performs one bulk DELETE, while a List-returning one loads and removes each entity individually">
  <rect x="10" y="20" width="280" height="60" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="150" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">long deleteByStatus(status)</text>
  <text x="150" y="58" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">1 bulk DELETE, no callbacks</text>

  <rect x="350" y="20" width="280" height="60" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="490" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">List&lt;Order&gt; deleteByStatus(status)</text>
  <text x="490" y="58" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">load + remove EACH, callbacks fire</text>
</svg>

The same method-name grammar, executed two fundamentally different ways based purely on the declared return type.

## 5. Runnable example

The scenario: a `LogEntry` cleanup job, evolving from a fast bulk derived delete, to the collection-returning variant confirming per-entity `@PreRemove` firing, to comparing both approaches' query counts directly.

### Level 1 — Basic

Use `long deleteByStatus(...)` for a fast bulk delete, confirming the returned count and the resulting row removal.

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

@SpringBootApplication
public class DerivedDeleteLevel1 {

    @Entity
    public static class LogEntry {
        @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
        private Long id;
        private String level;
        protected LogEntry() {}
        public LogEntry(String level) { this.level = level; }
    }

    public interface LogEntryRepository extends JpaRepository<LogEntry, Long> {
        @Transactional
        long deleteByLevel(String level);
    }

    public static void main(String[] args) {
        ConfigurableApplicationContext ctx = SpringApplication.run(DerivedDeleteLevel1.class,
            "--spring.datasource.url=jdbc:h2:mem:derivdel1",
            "--spring.jpa.hibernate.ddl-auto=create-drop");

        LogEntryRepository repo = ctx.getBean(LogEntryRepository.class);
        repo.save(new LogEntry("DEBUG"));
        repo.save(new LogEntry("DEBUG"));
        repo.save(new LogEntry("ERROR"));

        long deletedCount = repo.deleteByLevel("DEBUG");
        System.out.println("deleted count = " + deletedCount);
        System.out.println("remaining total = " + repo.count());

        if (deletedCount != 2) throw new AssertionError("Expected 2 DEBUG entries deleted");
        if (repo.count() != 1) throw new AssertionError("Expected exactly 1 entry (ERROR) remaining");
        System.out.println("long-returning derived delete performed a fast bulk deletion -- PASS");
        ctx.close();
    }
}
```

How to run: put `spring-boot-starter-data-jpa` and `com.h2database:h2` on the classpath, then `java DerivedDeleteLevel1.java` on JDK 17+.

`deleteByLevel(String level)` returning `long` derives to a bulk `DELETE FROM log_entry WHERE level = ?`, executed as a single SQL statement — the returned `long` correctly reports the number of rows affected, exactly like `@Modifying`'s `int`/`long` return from the previous card.

### Level 2 — Intermediate

Use a `List<LogEntry>`-returning derived delete method and confirm `@PreRemove` fires for each deleted entity individually — the load-then-remove-each execution path.

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
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.concurrent.atomic.AtomicInteger;

@SpringBootApplication
public class DerivedDeleteLevel2 {

    static final AtomicInteger preRemoveCallCount = new AtomicInteger();

    @Entity
    public static class LogEntry {
        @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
        private Long id;
        private String level;
        private String message;
        protected LogEntry() {}
        public LogEntry(String level, String message) { this.level = level; this.message = message; }
        public String getMessage() { return message; }

        @PreRemove
        void onRemove() {
            preRemoveCallCount.incrementAndGet();
        }
    }

    public interface LogEntryRepository extends JpaRepository<LogEntry, Long> {
        @Transactional
        List<LogEntry> deleteByLevelAndReturn(String level); // NOTE: standard convention is just deleteByLevel;
                                                                // renamed here to coexist clearly in this example
    }

    public static void main(String[] args) {
        ConfigurableApplicationContext ctx = SpringApplication.run(DerivedDeleteLevel2.class,
            "--spring.datasource.url=jdbc:h2:mem:derivdel2",
            "--spring.jpa.hibernate.ddl-auto=create-drop");

        LogEntryRepository repo = ctx.getBean(LogEntryRepository.class);
        repo.save(new LogEntry("DEBUG", "starting up"));
        repo.save(new LogEntry("DEBUG", "connecting to db"));
        repo.save(new LogEntry("ERROR", "connection failed"));

        List<LogEntry> deleted = repo.deleteByLevelAndReturn("DEBUG");
        System.out.println("deleted entries: " + deleted.stream().map(LogEntry::getMessage).toList());
        System.out.println("@PreRemove call count = " + preRemoveCallCount.get());

        if (deleted.size() != 2) throw new AssertionError("Expected 2 deleted entries returned");
        if (preRemoveCallCount.get() != 2) throw new AssertionError("Expected @PreRemove to fire once PER deleted entity");
        System.out.println("List-returning derived delete loaded and removed each entity individually -- PASS");
        ctx.close();
    }
}
```

How to run: same classpath as Level 1, `java DerivedDeleteLevel2.java`.

`deleteByLevelAndReturn(String level)` returning `List<LogEntry>` executes as load-then-remove-each: it first `SELECT`s the matching rows into real `LogEntry` instances, then calls `entityManager.remove(...)` on each one individually — `@PreRemove`'s call count reaching exactly `2` (one per deleted entity) directly confirms this per-entity execution path, in contrast to Level 1's single, callback-free bulk statement.

### Level 3 — Advanced

Directly compare both return-type variants' query counts side by side, making the performance/behavior tradeoff concrete rather than asserted.

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
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

@SpringBootApplication
public class DerivedDeleteLevel3 {

    @Entity
    public static class LogEntry {
        @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
        private Long id;
        private String level;
        protected LogEntry() {}
        public LogEntry(String level) { this.level = level; }
    }

    public interface LogEntryRepository extends JpaRepository<LogEntry, Long> {
        @Transactional
        long deleteByLevel(String level); // BULK path

        @Transactional
        List<LogEntry> removeByLevel(String level); // LOAD-THEN-REMOVE-EACH path (different keyword, same semantics)
    }

    public static void main(String[] args) {
        ConfigurableApplicationContext ctx = SpringApplication.run(DerivedDeleteLevel3.class,
            "--spring.datasource.url=jdbc:h2:mem:derivdel3",
            "--spring.jpa.hibernate.ddl-auto=create-drop",
            "--spring.jpa.properties.hibernate.generate_statistics=true");

        LogEntryRepository repo = ctx.getBean(LogEntryRepository.class);
        Statistics stats = ctx.getBean(EntityManagerFactory.class).unwrap(SessionFactory.class).getStatistics();

        // Scenario A: bulk delete of 5 rows.
        for (int i = 0; i < 5; i++) repo.save(new LogEntry("DEBUG"));
        stats.clear();
        long bulkDeleted = repo.deleteByLevel("DEBUG");
        long bulkQueryCount = stats.getQueryExecutionCount();

        // Scenario B: load-then-remove-each delete of 5 rows.
        for (int i = 0; i < 5; i++) repo.save(new LogEntry("DEBUG"));
        stats.clear();
        List<LogEntry> individuallyDeleted = repo.removeByLevel("DEBUG");
        long individualQueryCount = stats.getQueryExecutionCount();

        System.out.println("bulk delete (5 rows): " + bulkDeleted + " deleted, " + bulkQueryCount + " queries");
        System.out.println("individual delete (5 rows): " + individuallyDeleted.size() + " deleted, " + individualQueryCount + " queries");

        if (bulkQueryCount != 1) throw new AssertionError("Expected exactly 1 query for the bulk delete of 5 rows");
        if (individualQueryCount < 6)
            throw new AssertionError("Expected AT LEAST 6 queries for load-then-remove-each of 5 rows (1 select + 5 deletes), got " + individualQueryCount);

        System.out.println("Confirmed: bulk delete = 1 query; individual delete = 1 select + N deletes -- PASS");
        ctx.close();
    }
}
```

How to run: same classpath as Level 1 and 2, `java DerivedDeleteLevel3.java`.

Deleting the same 5 rows two different ways produces starkly different query counts: `deleteByLevel` (returning `long`) executes in exactly `1` query, a single bulk `DELETE`; `removeByLevel` (returning `List<LogEntry>`) executes in at least `6` queries — one `SELECT` to load the 5 matching rows, plus one `DELETE` per individually-removed entity — directly quantifying the performance cost of choosing the collection-returning variant.

## 6. Walkthrough

Trace both scenarios in Level 3.

1. **Scenario A setup**: 5 `LogEntry` rows with `level = "DEBUG"` are saved.
2. **`repo.deleteByLevel("DEBUG")`**: `PartTree` resolves this as a bulk-delete-returning-count method (return type `long`) — Spring Data JPA generates and executes a single `DELETE FROM log_entry WHERE level = ?` statement, with the database itself reporting `5` as the affected-row count, which becomes the method's return value.
3. **Scenario A query count**: exactly `1`, since the entire operation was one SQL statement with no entity loading involved at all.
4. **Scenario B setup**: 5 fresh `LogEntry` rows with `level = "DEBUG"` are saved (a new batch, since Scenario A already deleted the first 5).
5. **`repo.removeByLevel("DEBUG")`**: because the return type is `List<LogEntry>` (a collection of the entity type, not a count), `PartTree` resolves this as a load-then-remove-each method — it first executes `SELECT * FROM log_entry WHERE level = ?` (query 1), materializing 5 `LogEntry` instances, then calls `entityManager.remove(...)` on each one individually, producing 5 separate `DELETE` statements (queries 2 through 6).
6. **Scenario B query count**: at least `6` (1 select + 5 deletes) — directly measured via the same Hibernate statistics mechanism used throughout this section, confirming the load-then-remove-each execution path genuinely costs more database round-trips than the bulk path.
7. **Verification**: the program checks both scenarios' exact query counts against their expected minimums, confirming the return-type-driven behavior difference is real and measurable, not merely a documented claim.

```
 deleteByLevel("DEBUG")  [returns long]
        |
        v
 1 query:  DELETE FROM log_entry WHERE level='DEBUG'   -->  5 rows affected

 removeByLevel("DEBUG")  [returns List<LogEntry>]
        |
        v
 query 1: SELECT * FROM log_entry WHERE level='DEBUG'   -->  5 rows loaded
 query 2-6: DELETE FROM log_entry WHERE id=?  (once PER loaded row)
```

## 7. Gotchas & takeaways

> **Gotcha:** it's easy to accidentally choose the collection-returning variant purely out of habit (matching the "return what was affected" pattern used for `find` methods) without realizing it triggers a meaningfully more expensive execution path — for a large deletion where the returned data isn't actually needed, always prefer `void`/`long`/`int` as the return type to get the fast, bulk-delete path.

- Derived delete methods (`deleteBy`/`removeBy`) follow the identical property-matching and keyword grammar as `findBy` methods, but their JPA execution strategy depends entirely on the declared return type.
- `void`/`long`/`int` return types trigger a genuine bulk `DELETE` statement — fast, single-query, but with no lifecycle callbacks and no returned entity data.
- A collection return type (`List<T>`, and similar) triggers a load-then-remove-each execution path — slower (a `SELECT` plus one `DELETE` per matched row), but returns the actual deleted entities and correctly fires `@PreRemove`/`@PostRemove` lifecycle callbacks for each one.
- All `@Transactional`-requiring rules from the `@Modifying`/deletion cards apply equally here — derived delete methods need a genuine, writable transaction to execute their underlying `DELETE` statement(s).
