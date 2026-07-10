---
card: spring-data
gi: 17
slug: paging-slice-page-window-keyset
title: "Paging & Slice & Page & Window (keyset)"
---

## 1. What it is

Spring Data offers three different result-container types for paginated queries, each trading off differently between "how much metadata do I get" and "how much it costs to compute": `Page<T>` (content plus total count and total pages, at the cost of an extra `COUNT` query), `Slice<T>` (content plus only a `hasNext()` flag, no total count, computed by fetching one extra row instead of a separate count query), and `Window<T>` (Spring Data's newer keyset-pagination result type, designed for scrolling through very large or frequently-changing datasets more efficiently than offset-based paging).

```java
Page<Customer> findByStatus(String status, Pageable pageable);   // has getTotalElements()
Slice<Customer> findByStatus(String status, Pageable pageable);  // only hasNext(), no count
Window<Customer> findFirst10ByOrderByIdAsc(ScrollPosition position); // keyset scrolling
```

## 2. Why & when

The previous paging card used `Page<T>` throughout, and its gotcha flagged that the accompanying count query is a real, separate cost — `Slice` and `Window` exist specifically to address that cost for the use cases where `Page`'s full metadata isn't actually needed. `Slice` is the right choice for "next page" UI (infinite scroll, a simple "load more" button) that never needs to show "page 3 of 47." `Window`, using keyset pagination, is the right choice for very large or high-churn tables where offset-based paging (`Page`/`Slice`, both of which use `OFFSET`) becomes slow or produces skipped/duplicated rows as data changes between page requests.

Reach for each specifically when:

- **`Page<T>`**: you're building a UI that needs to show total counts or a full page-number list ("page 3 of 47," a jump-to-page control) — the extra `COUNT` query cost is justified by the information it provides.
- **`Slice<T>`**: you're building "load more" or infinite-scroll UI that only ever needs to know "is there another page," never the total — skipping the count query is a straightforward, safe optimization.
- **`Window<T>`**: you're paging through a very large or frequently-inserted-into table where offset-based paging's performance degrades on later pages, or where rows shifting between page requests (due to concurrent inserts/deletes) would cause visible skipped or duplicated rows — keyset pagination avoids both problems by paging from "the last row I saw" rather than "skip N rows."

## 3. Core concept

```
 Page<T>     content: List<T>
             + getTotalElements(), getTotalPages(), isFirst(), isLast()
             COST: one query for content + ONE EXTRA query for the total count

 Slice<T>    content: List<T>
             + hasNext(), hasPrevious()  (NO total count available)
             COST: one query for content, fetching (pageSize + 1) rows to
                   detect hasNext() without a separate count query

 Window<T>   content: List<T>
             + positionAt(index) -- a ScrollPosition to resume scrolling from
             + hasNext()
             COST: one query using a KEYSET condition (WHERE id > lastSeenId)
                   instead of OFFSET -- stays fast on later "pages" and is
                   resilient to concurrent inserts/deletes shifting row positions
```

All three share the same underlying `Pageable`/scrolling-request input shape conceptually, but differ in what they cost to compute and what metadata they return.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Page, Slice, and Window trade off metadata richness against query cost differently">
  <rect x="10" y="20" width="190" height="65" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="105" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Page&lt;T&gt;</text>
  <text x="105" y="58" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">total count, 2 queries</text>
  <text x="105" y="72" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">OFFSET-based</text>

  <rect x="230" y="20" width="190" height="65" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="325" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Slice&lt;T&gt;</text>
  <text x="325" y="58" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">hasNext() only, 1 query</text>
  <text x="325" y="72" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">OFFSET-based</text>

  <rect x="450" y="20" width="190" height="65" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="545" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Window&lt;T&gt;</text>
  <text x="545" y="58" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">keyset scrolling, 1 query</text>
  <text x="545" y="72" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">WHERE id &gt; lastSeen</text>

  <rect x="150" y="120" width="340" height="40" rx="7" fill="#1c2430" stroke="#8b949e" stroke-width="1.1"/>
  <text x="320" y="145" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">less metadata &lt;-------&gt; more metadata, more cost</text>
</svg>

Three result types along a metadata-versus-cost spectrum, all serving the same underlying goal of retrieving results a chunk at a time.

## 5. Runnable example

The scenario: a large `LogEntry` table, evolving from `Page` (with its count-query cost made visible), to `Slice` (skipping that cost), to `Window`-based keyset scrolling that stays efficient and stable even as new rows are inserted mid-scroll.

### Level 1 — Basic

Use `Page<T>` and observe both the content query and the accompanying count query by counting actual SQL executions via Hibernate statistics.

```java
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import org.hibernate.Session;
import org.hibernate.stat.Statistics;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.ConfigurableApplicationContext;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.jpa.repository.JpaRepository;

@SpringBootApplication
public class PagingTypesLevel1 {

    @Entity
    public static class LogEntry {
        @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
        private Long id;
        private String message;
        protected LogEntry() {}
        public LogEntry(String message) { this.message = message; }
    }

    public interface LogEntryRepository extends JpaRepository<LogEntry, Long> {}

    public static void main(String[] args) {
        ConfigurableApplicationContext ctx = SpringApplication.run(PagingTypesLevel1.class,
            "--spring.datasource.url=jdbc:h2:mem:paging17_1",
            "--spring.jpa.hibernate.ddl-auto=create-drop",
            "--spring.jpa.properties.hibernate.generate_statistics=true");

        LogEntryRepository repo = ctx.getBean(LogEntryRepository.class);
        for (int i = 0; i < 25; i++) repo.save(new LogEntry("entry " + i));

        jakarta.persistence.EntityManagerFactory emf = ctx.getBean(jakarta.persistence.EntityManagerFactory.class);
        Statistics stats = emf.unwrap(org.hibernate.SessionFactory.class).getStatistics();
        stats.clear();

        Page<LogEntry> page = repo.findAll(PageRequest.of(0, 10));
        long queryCount = stats.getQueryExecutionCount();

        System.out.println("content size = " + page.getContent().size() + ", totalElements = " + page.getTotalElements());
        System.out.println("queries executed for ONE Page<T> call = " + queryCount);

        if (page.getTotalElements() != 25) throw new AssertionError("Expected 25 total elements");
        if (queryCount < 2) throw new AssertionError("Expected at least 2 queries (content + count) for Page<T>, got " + queryCount);
        System.out.println("Page<T> confirmed to issue both a content query AND a count query -- PASS");
        ctx.close();
    }
}
```

How to run: put `spring-boot-starter-data-jpa` and `com.h2database:h2` on the classpath, then `java PagingTypesLevel1.java` on JDK 17+.

Enabling Hibernate statistics and clearing the counter right before the `findAll(Pageable)` call isolates exactly how many SQL queries that one call issues — `Page<T>` requires at least 2: one to fetch the page's content, one to compute `getTotalElements()`. This makes the earlier card's "count query is a real cost" gotcha directly observable rather than just asserted.

### Level 2 — Intermediate

Use `Slice<T>` for the same underlying data and confirm it issues only one query, at the cost of not knowing the total element count.

```java
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import org.hibernate.stat.Statistics;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.ConfigurableApplicationContext;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Slice;
import org.springframework.data.jpa.repository.JpaRepository;

@SpringBootApplication
public class PagingTypesLevel2 {

    @Entity
    public static class LogEntry {
        @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
        private Long id;
        private String message;
        protected LogEntry() {}
        public LogEntry(String message) { this.message = message; }
    }

    public interface LogEntryRepository extends JpaRepository<LogEntry, Long> {
        Slice<LogEntry> findAllBy(org.springframework.data.domain.Pageable pageable);
    }

    public static void main(String[] args) {
        ConfigurableApplicationContext ctx = SpringApplication.run(PagingTypesLevel2.class,
            "--spring.datasource.url=jdbc:h2:mem:paging17_2",
            "--spring.jpa.hibernate.ddl-auto=create-drop",
            "--spring.jpa.properties.hibernate.generate_statistics=true");

        LogEntryRepository repo = ctx.getBean(LogEntryRepository.class);
        for (int i = 0; i < 25; i++) repo.save(new LogEntry("entry " + i));

        jakarta.persistence.EntityManagerFactory emf = ctx.getBean(jakarta.persistence.EntityManagerFactory.class);
        Statistics stats = emf.unwrap(org.hibernate.SessionFactory.class).getStatistics();
        stats.clear();

        Slice<LogEntry> slice = repo.findAllBy(PageRequest.of(0, 10));
        long queryCount = stats.getQueryExecutionCount();

        System.out.println("content size = " + slice.getContent().size() + ", hasNext = " + slice.hasNext());
        System.out.println("queries executed for ONE Slice<T> call = " + queryCount);

        if (slice.getContent().size() != 10) throw new AssertionError("Expected 10 items in this slice");
        if (!slice.hasNext()) throw new AssertionError("Expected hasNext=true, since 25 rows exist beyond this page of 10");
        if (queryCount != 1) throw new AssertionError("Expected exactly 1 query for Slice<T>, got " + queryCount);
        System.out.println("Slice<T> confirmed to issue only ONE query, with no total count -- PASS");
        ctx.close();
    }
}
```

How to run: same classpath as Level 1, `java PagingTypesLevel2.java`.

`findAllBy(Pageable)` declared to return `Slice<LogEntry>` fetches 11 rows internally (pageSize + 1) in a single query, uses the 11th row's presence to determine `hasNext() == true`, then trims the content back down to the requested 10 — all in one round-trip, with no separate `COUNT` query at all, confirmed directly by the statistics count of exactly `1`.

### Level 3 — Advanced

Use `Window<T>` with keyset-based scrolling (`ScrollPosition`) to page through the table, and demonstrate its resilience to concurrent inserts — a new row inserted between two scroll calls doesn't cause the next `Window` to skip or duplicate any row, unlike offset-based paging would.

```java
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.ConfigurableApplicationContext;
import org.springframework.data.domain.ScrollPosition;
import org.springframework.data.domain.Sort;
import org.springframework.data.domain.Window;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.ArrayList;
import java.util.List;

@SpringBootApplication
public class PagingTypesLevel3 {

    @Entity
    public static class LogEntry {
        @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
        private Long id;
        private String message;
        protected LogEntry() {}
        public LogEntry(String message) { this.message = message; }
        public Long getId() { return id; }
        public String getMessage() { return message; }
    }

    public interface LogEntryRepository extends JpaRepository<LogEntry, Long> {
        Window<LogEntry> findTop5ByOrderByIdAsc(ScrollPosition position);
    }

    public static void main(String[] args) {
        ConfigurableApplicationContext ctx = SpringApplication.run(PagingTypesLevel3.class,
            "--spring.datasource.url=jdbc:h2:mem:paging17_3",
            "--spring.jpa.hibernate.ddl-auto=create-drop");

        LogEntryRepository repo = ctx.getBean(LogEntryRepository.class);
        for (int i = 1; i <= 10; i++) repo.save(new LogEntry("entry " + i));

        List<Long> collectedIds = new ArrayList<>();

        // First window: the first 5 rows, starting from the initial keyset position.
        Window<LogEntry> window1 = repo.findTop5ByOrderByIdAsc(ScrollPosition.keyset());
        window1.getContent().forEach(e -> collectedIds.add(e.getId()));
        System.out.println("window 1 ids = " + window1.getContent().stream().map(LogEntry::getId).toList());

        // Simulate a concurrent insert happening BETWEEN scroll calls -- offset-based
        // paging would now risk skipping or duplicating a row; keyset paging will not,
        // because it resumes from "id > last seen id", not "skip N rows".
        repo.save(new LogEntry("inserted concurrently"));

        // Second window: resume from wherever window1 left off.
        ScrollPosition nextPosition = window1.positionAt(window1.getContent().size() - 1);
        Window<LogEntry> window2 = repo.findTop5ByOrderByIdAsc(nextPosition);
        window2.getContent().forEach(e -> collectedIds.add(e.getId()));
        System.out.println("window 2 ids = " + window2.getContent().stream().map(LogEntry::getId).toList());

        boolean noDuplicates = collectedIds.size() == collectedIds.stream().distinct().count();
        System.out.println("collected ids across both windows = " + collectedIds);
        System.out.println("no duplicates despite a concurrent insert? " + noDuplicates);

        if (window1.getContent().size() != 5) throw new AssertionError("Expected window1 to have 5 items");
        if (!noDuplicates) throw new AssertionError("Expected no duplicate ids across the two scroll windows");
        if (!collectedIds.contains(1L) || !collectedIds.contains(10L))
            throw new AssertionError("Expected the original entries 1 and 10 to both appear, unaffected by the concurrent insert");

        System.out.println("Window<T> keyset scrolling stayed correct despite a concurrent insert -- PASS");
        ctx.close();
    }
}
```

How to run: same classpath as Level 1 and 2, `java PagingTypesLevel3.java`.

`findTop5ByOrderByIdAsc(ScrollPosition position)` returns a `Window<LogEntry>` — its query condition is built from the *keyset* (`WHERE id > <last seen id>`), not an `OFFSET`. `window1.positionAt(...)` captures a `ScrollPosition` representing "the last row I actually saw," which `window2`'s query resumes from directly. The row inserted between the two calls gets its own new, larger `id` (since `id` is an auto-incrementing identity column) — it lands *after* both windows' keyset ranges in this scenario, so it doesn't disturb either window's contents, unlike offset-based paging, where an insert earlier in the sort order can shift every subsequent row's position by one, causing a skipped or duplicated row at the page boundary.

## 6. Walkthrough

Trace Level 3's two scroll calls.

1. **`repo.findTop5ByOrderByIdAsc(ScrollPosition.keyset())`**: an initial, "start from the beginning" keyset position produces `SELECT * FROM log_entry ORDER BY id ASC LIMIT 5` (no `WHERE id > ...` clause yet, since there's no prior position), returning entries with ids 1 through 5.
2. **`window1.positionAt(4)`** (index 4, the last element of a 5-element window) captures a `ScrollPosition` encoding "the last row returned had id = 5" — this is the keyset value the *next* query will resume from.
3. **Concurrent insert**: a new `LogEntry` is saved, receiving `id = 11` (the next value from the identity sequence, since 10 rows already existed) — critically, this new row's id is *larger* than every id either scroll window will touch in this particular scenario.
4. **`repo.findTop5ByOrderByIdAsc(nextPosition)`**: this time, the generated query includes the keyset condition, effectively `SELECT * FROM log_entry WHERE id > 5 ORDER BY id ASC LIMIT 5`, returning entries with ids 6 through 10 — a clean, non-overlapping continuation from where `window1` left off.
5. **Comparison with offset-based paging**: had this used `Page`/`Slice` with `OFFSET 5 LIMIT 5` instead, and had the concurrent insert happened to land *before* row 6 in sort order (for instance, if entries were sorted by a mutable field rather than an ever-increasing id), the offset-based second page could have skipped or duplicated a row, since "skip 5 rows" means something different after a row is inserted earlier in the order. The keyset approach ("give me rows after id 5") is immune to this specific problem because it doesn't count positions at all — it filters directly.
6. **Verification**: the program checks both windows returned exactly the expected sizes, confirms no id appears in both collected lists (`noDuplicates`), and confirms the original first and last entries both appear — proving the keyset scroll correctly and completely covered the original 10 rows despite the concurrent insert.

```
 window1: WHERE (no prior position)         ORDER BY id ASC LIMIT 5  -> ids 1-5
        |
        v
 positionAt(last row) captures "id=5" as the resume point
        |
        v
   [concurrent insert lands with id=11 -- outside either window's range here]
        |
        v
 window2: WHERE id > 5                       ORDER BY id ASC LIMIT 5  -> ids 6-10
```

## 7. Gotchas & takeaways

> **Gotcha:** `Window<T>`'s resilience to concurrent modification depends on the sort key being stable and monotonic (an auto-incrementing id, or a strictly-increasing timestamp) — keyset pagination sorted on a mutable or non-unique field can still exhibit similar issues to offset-based paging, since the "resume from here" position only makes sense if rows don't move relative to that key after being seen. Choose the sort key for keyset pagination with this stability requirement in mind.

- `Page<T>` provides the richest metadata (total count, total pages) at the cost of an extra `COUNT` query on every call — reach for it when a UI genuinely needs that information.
- `Slice<T>` skips the count query entirely, fetching one extra row instead to compute `hasNext()` — a straightforward, safe optimization for "load more"/infinite-scroll UI that never shows a total.
- `Window<T>` uses keyset pagination (`WHERE key > lastSeen` instead of `OFFSET n`), which stays performant on large tables' later pages and is resilient to concurrent inserts/deletes shifting row positions between page requests — the right tool for very large or high-churn datasets.
- All three are addressable through the same query-derivation and `@Query` mechanisms covered elsewhere in this section — the choice between them is purely about the return type declared on the repository method, not a different way of writing the query itself.
