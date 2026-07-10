---
card: spring-data
gi: 22
slug: streaming-query-results-stream-t
title: "Streaming query results (Stream<T>)"
---

## 1. What it is

Declaring a repository method's return type as `Stream<T>` instead of `List<T>` changes how results are delivered: rather than the JPA provider loading every matching row into memory as a fully-materialized `List` before returning, a `Stream<T>`-returning method keeps a database cursor open and hands rows to the caller one at a time as the stream is consumed — letting an application process a result set far larger than would comfortably fit in memory all at once.

```java
@Query("select o from Order o where o.status = :status")
Stream<Order> streamAllByStatus(@Param("status") String status);

// Must be called within a transaction, and the Stream must be closed:
try (Stream<Order> orders = repo.streamAllByStatus("archived")) {
    orders.forEach(this::processOrder);
}
```

## 2. Why & when

`List<T>`-returning methods fully materialize every matching row in memory before the method returns — fine for a hundred rows, a real problem for a batch job processing millions. `Stream<T>` exists specifically to let a repository method process an unbounded or very large result set incrementally, backed by a database cursor rather than an in-memory collection, keeping peak memory usage roughly constant regardless of how many rows actually match.

Reach for `Stream<T>` specifically when:

- You're writing a batch-processing job — a nightly export, a data migration, a report generator — that needs to process every row matching some criteria, potentially millions of them, without loading them all into memory at once.
- You want to combine a query result with Java's `Stream` API (`.map`, `.filter`, `.collect`) directly on the repository's output, processing results lazily as they're read from the database rather than after a full `List` has already been built.
- You're processing rows where each one triggers meaningful I/O or computation (writing to a file, calling an external service) and want that work to begin as soon as the first row arrives, rather than waiting for the entire result set to load first.

## 3. Core concept

```
 List<T> findByStatus(String status);
        |
        v
   JPA provider executes the query, materializes EVERY matching row into a
   List<T> BEFORE the method returns -- full memory cost paid upfront

 Stream<T> findByStatus(String status);   -- REQUIRES a surrounding transaction
        |
        v
   JPA provider opens a database CURSOR and returns a Stream wrapping it
        |
        v
   rows are fetched from the database ONE AT A TIME as the Stream is consumed
   (via .forEach, .collect, a for-each over an iterator, etc.)
        |
        v
   the Stream (and its underlying cursor/resources) MUST be closed --
   normally via try-with-resources -- or the database connection/cursor leaks
```

A `Stream<T>`-returning method needs an active transaction for its whole consumption lifetime (the cursor stays open against a live connection), and the returned `Stream` must be explicitly closed — two requirements a `List<T>`-returning method never has, since `List` is already fully materialized and disconnected from the database by the time it's returned.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="List materializes all rows upfront in memory; Stream keeps a cursor open and delivers rows one at a time as consumed">
  <rect x="10" y="20" width="280" height="65" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="150" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">List&lt;Order&gt; findByStatus(...)</text>
  <text x="150" y="58" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">ALL rows loaded into memory</text>
  <text x="150" y="72" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">before the method returns</text>

  <rect x="350" y="20" width="280" height="65" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="490" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Stream&lt;Order&gt; streamByStatus(...)</text>
  <text x="490" y="58" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">DB cursor stays open; rows</text>
  <text x="490" y="72" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">delivered one at a time as consumed</text>

  <rect x="150" y="115" width="340" height="35" rx="7" fill="#1c2430" stroke="#8b949e" stroke-width="1.1"/>
  <text x="320" y="137" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">Stream needs an active @Transactional + try-with-resources</text>
</svg>

`List<T>` pays full memory cost upfront; `Stream<T>` trades that for a cursor-lifetime dependency on an active transaction.

## 5. Runnable example

The scenario: a large `LogEntry` table processed in a batch job, evolving from a basic `Stream<T>` consumption with proper resource closing, to processing with `Stream` operators (`filter`/`map`), to a demonstration of the transaction requirement — showing what actually happens if the stream is consumed outside its required transactional scope.

### Level 1 — Basic

Declare a `Stream<T>`-returning method, consume it within `try-with-resources` inside a `@Transactional` method, and confirm every row is visited.

```java
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.ConfigurableApplicationContext;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.stereotype.Component;
import org.springframework.transaction.annotation.Transactional;

import java.util.concurrent.atomic.AtomicInteger;
import java.util.stream.Stream;

@SpringBootApplication
public class StreamingLevel1 {

    @Entity
    public static class LogEntry {
        @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
        private Long id;
        private String message;
        protected LogEntry() {}
        public LogEntry(String message) { this.message = message; }
        public String getMessage() { return message; }
    }

    public interface LogEntryRepository extends JpaRepository<LogEntry, Long> {
        @Query("select l from LogEntry l")
        Stream<LogEntry> streamAll();
    }

    @Component
    public static class LogProcessor {
        private final LogEntryRepository repo;
        public LogProcessor(LogEntryRepository repo) { this.repo = repo; }

        @Transactional(readOnly = true) // required: the cursor needs an active transaction
        public int processAll() {
            AtomicInteger processedCount = new AtomicInteger();
            try (Stream<LogEntry> stream = repo.streamAll()) {
                stream.forEach(entry -> {
                    processedCount.incrementAndGet();
                    // real processing would happen here, one row at a time
                });
            } // the try-with-resources closes the Stream (and its DB cursor) here
            return processedCount.get();
        }
    }

    public static void main(String[] args) {
        ConfigurableApplicationContext ctx = SpringApplication.run(StreamingLevel1.class,
            "--spring.datasource.url=jdbc:h2:mem:stream1",
            "--spring.jpa.hibernate.ddl-auto=create-drop");

        LogEntryRepository repo = ctx.getBean(LogEntryRepository.class);
        for (int i = 0; i < 100; i++) repo.save(new LogEntry("entry " + i));

        LogProcessor processor = ctx.getBean(LogProcessor.class);
        int processed = processor.processAll();
        System.out.println("processed " + processed + " log entries via Stream<T>");

        if (processed != 100) throw new AssertionError("Expected to process exactly 100 entries");
        System.out.println("Stream<T> consumed within try-with-resources inside a transaction -- PASS");
        ctx.close();
    }
}
```

How to run: put `spring-boot-starter-data-jpa` and `com.h2database:h2` on the classpath, then `java StreamingLevel1.java` on JDK 17+.

`@Transactional(readOnly = true)` keeps a database transaction open for the entire `processAll()` call — required, since the `Stream<LogEntry>` returned by `streamAll()` is backed by a live database cursor that needs an active connection/transaction to keep fetching rows as the stream is consumed. `try (Stream<LogEntry> stream = repo.streamAll())` ensures the stream (and its cursor) is closed once processing finishes, whether it completes normally or an exception is thrown partway through.

### Level 2 — Intermediate

Chain `Stream` operators (`filter`, `map`) directly onto the repository's returned stream, processing and transforming rows lazily as they're read from the database.

```java
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.ConfigurableApplicationContext;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.stereotype.Component;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.stream.Collectors;
import java.util.stream.Stream;

@SpringBootApplication
public class StreamingLevel2 {

    @Entity
    public static class Transaction {
        @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
        private Long id;
        private double amount;
        protected Transaction() {}
        public Transaction(double amount) { this.amount = amount; }
        public double getAmount() { return amount; }
    }

    public interface TransactionRepository extends JpaRepository<Transaction, Long> {
        @Query("select t from Transaction t")
        Stream<Transaction> streamAll();
    }

    @Component
    public static class TransactionSummarizer {
        private final TransactionRepository repo;
        public TransactionSummarizer(TransactionRepository repo) { this.repo = repo; }

        @Transactional(readOnly = true)
        public List<String> summarizeLargeTransactions(double threshold) {
            try (Stream<Transaction> stream = repo.streamAll()) {
                return stream
                    .filter(t -> t.getAmount() > threshold) // lazily filters as rows arrive
                    .map(t -> "TXN-" + t.getId() + ": $" + t.getAmount())
                    .collect(Collectors.toList()); // terminal operation -- triggers actual consumption
            }
        }
    }

    public static void main(String[] args) {
        ConfigurableApplicationContext ctx = SpringApplication.run(StreamingLevel2.class,
            "--spring.datasource.url=jdbc:h2:mem:stream2",
            "--spring.jpa.hibernate.ddl-auto=create-drop");

        TransactionRepository repo = ctx.getBean(TransactionRepository.class);
        repo.save(new Transaction(50.0));
        repo.save(new Transaction(500.0));
        repo.save(new Transaction(25.0));
        repo.save(new Transaction(1000.0));

        TransactionSummarizer summarizer = ctx.getBean(TransactionSummarizer.class);
        List<String> largeOnes = summarizer.summarizeLargeTransactions(100.0);
        System.out.println("large transactions: " + largeOnes);

        if (largeOnes.size() != 2) throw new AssertionError("Expected exactly 2 transactions over 100.0");
        System.out.println("Stream operators (filter/map/collect) chained onto the DB-backed Stream -- PASS");
        ctx.close();
    }
}
```

How to run: same classpath as Level 1, `java StreamingLevel2.java`.

`stream.filter(...).map(...).collect(...)` chains standard `Stream` API operations directly onto the cursor-backed stream — `filter` and `map` are lazy, evaluated row-by-row as the underlying cursor advances, and `collect(Collectors.toList())` is the terminal operation that actually drives consumption of the entire stream, gathering the transformed, filtered results into a final `List<String>`.

### Level 3 — Advanced

Demonstrate the transaction requirement's consequence directly: attempt to consume a `Stream<T>` outside its originating transaction's scope, and observe the failure — proving the requirement is enforced, not just documented advice.

```java
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.ConfigurableApplicationContext;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.stereotype.Component;
import org.springframework.transaction.annotation.Transactional;

import java.util.stream.Stream;

@SpringBootApplication
public class StreamingLevel3 {

    @Entity
    public static class LogEntry {
        @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
        private Long id;
        private String message;
        protected LogEntry() {}
        public LogEntry(String message) { this.message = message; }
    }

    public interface LogEntryRepository extends JpaRepository<LogEntry, Long> {
        @Query("select l from LogEntry l")
        Stream<LogEntry> streamAll();
    }

    @Component
    public static class LeakyProcessor {
        private final LogEntryRepository repo;
        public LeakyProcessor(LogEntryRepository repo) { this.repo = repo; }

        // Returns the Stream itself OUTSIDE the transaction it was created in --
        // a common mistake. The @Transactional boundary ends when this method returns.
        @Transactional(readOnly = true)
        public Stream<LogEntry> getStreamIncorrectly() {
            return repo.streamAll(); // the transaction backing this cursor ends right after this method returns
        }

        @Transactional(readOnly = true)
        public int processCorrectly() {
            try (Stream<LogEntry> stream = repo.streamAll()) {
                return (int) stream.count(); // consumed WITHIN the same transactional method -- correct
            }
        }
    }

    public static void main(String[] args) {
        ConfigurableApplicationContext ctx = SpringApplication.run(StreamingLevel3.class,
            "--spring.datasource.url=jdbc:h2:mem:stream3",
            "--spring.jpa.hibernate.ddl-auto=create-drop");

        LogEntryRepository repo = ctx.getBean(LogEntryRepository.class);
        for (int i = 0; i < 20; i++) repo.save(new LogEntry("entry " + i));

        LeakyProcessor processor = ctx.getBean(LeakyProcessor.class);

        boolean failedWhenUsedOutsideTransaction = false;
        try (Stream<LogEntry> leakedStream = processor.getStreamIncorrectly()) {
            // The transaction that opened this cursor already ended when getStreamIncorrectly() returned.
            long count = leakedStream.count(); // attempting to consume it now typically fails
            System.out.println("this line should not normally be reached successfully: count=" + count);
        } catch (Exception expected) {
            failedWhenUsedOutsideTransaction = true;
            System.out.println("consuming the stream outside its transaction failed as expected: "
                + expected.getClass().getSimpleName());
        }

        int correctCount = processor.processCorrectly();
        System.out.println("correctly-scoped stream count = " + correctCount);

        if (!failedWhenUsedOutsideTransaction)
            throw new AssertionError("Expected consuming the Stream outside its transaction to fail");
        if (correctCount != 20) throw new AssertionError("Expected the correctly-scoped stream to count all 20 entries");

        System.out.println("Transaction-scope requirement confirmed: leaked stream failed, correctly-scoped one worked -- PASS");
        ctx.close();
    }
}
```

How to run: put `spring-boot-starter-data-jpa` and `com.h2database:h2` on the classpath, then `java StreamingLevel3.java` on JDK 17+. Expect a caught exception to print, followed by `PASS` — the failure is the correct, intended outcome for this specific test.

`getStreamIncorrectly()` returns the raw `Stream<LogEntry>` from inside a `@Transactional` method — but the moment that method returns, Spring's transaction interceptor commits (or, for `readOnly = true`, simply ends) the transaction, closing the underlying database cursor's connection. The caller in `main` then tries to consume that now-orphaned stream, which typically throws (a `JDBCConnectionException`, `IllegalStateException`, or similar, depending on the exact JPA provider and connection pool behavior) because the cursor's connection is no longer valid. `processCorrectly()`, by contrast, both creates and fully consumes the stream within the same transactional method boundary, which is why it succeeds.

## 6. Walkthrough

Trace both processor methods in Level 3.

1. **`processor.getStreamIncorrectly()` call begins**: Spring's `@Transactional` interceptor starts a new transaction around this method's execution.
2. **`repo.streamAll()`** opens a database cursor within that transaction, returning a `Stream<LogEntry>` backed by it.
3. **The method returns** this stream directly to the caller — critically, at the exact moment the method returns, the `@Transactional` interceptor's advice runs its "after method" logic, ending the transaction and, with it, invalidating the cursor's underlying database resources.
4. **Back in `main`**, the `try (Stream<LogEntry> leakedStream = ...)` block holds a reference to a stream whose backing transaction has already ended.
5. **`leakedStream.count()`** attempts to actually consume the stream — this is the point where the invalidated cursor/connection state surfaces as a real failure, since there's no longer a valid transaction or connection for the JPA provider to fetch rows through.
6. **The `catch` block** catches this failure, confirming the transaction-scope requirement is genuinely enforced, not merely documented as advisory.
7. **`processor.processCorrectly()` call**: a fresh `@Transactional` method both creates the stream (`repo.streamAll()`) and fully consumes it (`stream.count()`) within the same method body, so the transaction remains active for the stream's entire lifetime — this succeeds, correctly counting all 20 rows.
8. **Verification**: the program confirms the incorrect usage failed and the correct usage succeeded with the expected count, demonstrating both halves of the requirement concretely.

```
 getStreamIncorrectly()  [@Transactional]
        |
        +-- repo.streamAll() opens cursor
        |
        +-- method RETURNS --> transaction ENDS --> cursor invalidated
        |
        v
 caller tries leakedStream.count()  --> FAILS (cursor/connection no longer valid)

 processCorrectly()  [@Transactional]
        |
        +-- repo.streamAll() opens cursor
        +-- stream.count() consumes it FULLY, still inside the same transaction
        |
        v
 method returns a plain int, transaction ends AFTER consumption completed  --> SUCCEEDS
```

## 7. Gotchas & takeaways

> **Gotcha:** returning a `Stream<T>` from a `@Transactional` method to code outside that method — exactly the mistake Level 3 demonstrates deliberately — is a common and easy-to-make error, since it compiles perfectly fine and the failure only surfaces at runtime, when the stream is actually consumed. The stream must always be both created and fully consumed within the same transactional scope; never let one "escape" the method that opened it.

- `Stream<T>` trades `List<T>`'s "everything loaded upfront" memory cost for a live database cursor that must stay within an active transaction for its entire consumption lifetime.
- Always wrap `Stream<T>`-returning repository calls in `try-with-resources` to guarantee the underlying cursor and its database resources are released, whether consumption completes normally or throws partway through.
- Standard `Stream` API operators (`filter`, `map`, `collect`, and the rest) work directly on the returned stream, evaluated lazily row-by-row as the cursor advances — no separate collection step is needed before applying them.
- `Stream<T>` earns its keep specifically for very large or memory-sensitive result sets — for the common case of a bounded, reasonably-sized result, `List<T>` remains simpler, with none of `Stream<T>`'s transaction-scoping and explicit-closing requirements.
