---
card: spring-framework
gi: 254
slug: consistent-exception-hierarchy-dataaccessexception
title: Consistent exception hierarchy (DataAccessException)
---

## 1. What it is

`DataAccessException` is Spring's root unchecked exception for all data-access errors. Every Spring data-access template — `JdbcTemplate`, JPA repositories, `MongoTemplate`, `RedisTemplate` — wraps technology-specific exceptions (JDBC `SQLException`, JPA `PersistenceException`, MongoDB `MongoException`) into a consistent `DataAccessException` subclass hierarchy.

```java
// Without Spring:
try { stmt.executeUpdate(...); }
catch (SQLException e) { /* vendor-specific error code check */ }

// With Spring JdbcTemplate:
try { jdbcTemplate.update(...); }
catch (DuplicateKeyException e) { /* same class regardless of database vendor */ }
```

The hierarchy is organized by the nature of the problem, not by which library threw it.

## 2. Why & when

`SQLException` carries a vendor-specific error code and a SQL State string — handling it portably requires mapping dozens of vendor codes per database. JPA's `PersistenceException` is similarly opaque.

Spring's exception translation solves this by:
1. Mapping vendor error codes to semantic exception subclasses.
2. Making those subclasses unchecked (extend `RuntimeException`) — no forced `try/catch`.
3. Providing the same hierarchy for JDBC, JPA, MongoDB, Redis, Cassandra, etc.

Result: `DuplicateKeyException` means "duplicate key" whether you use PostgreSQL, MySQL, H2, or Oracle — no vendor-specific code check needed.

## 3. Core concept

Key exception classes in the hierarchy:

```
DataAccessException (RuntimeException)
├── NonTransientDataAccessException    — error won't succeed on retry
│   ├── DataIntegrityViolationException
│   │   └── DuplicateKeyException
│   ├── BadSqlGrammarException
│   ├── TypeMismatchDataAccessException
│   └── PermissionDeniedDataAccessException
├── TransientDataAccessException       — error may succeed on retry
│   ├── TransientDataAccessResourceException
│   ├── ConcurrencyFailureException
│   │   └── CannotAcquireLockException
│   └── QueryTimeoutException
├── RecoverableDataAccessException     — partial recovery possible
└── UncategorizedDataAccessException   — unmapped error
```

The translation is done by `SQLExceptionTranslator` (for JDBC) — most commonly `SQLErrorCodeSQLExceptionTranslator`, which uses the `sql-error-codes.xml` bundled in `spring-jdbc.jar` to map vendor codes. `@Repository`-annotated classes trigger exception translation via `PersistenceExceptionTranslationPostProcessor`.

## 4. Diagram

<svg viewBox="0 0 700 240" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <marker id="arr" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <polygon points="0 0,8 3,0 6" fill="#6db33f"/>
    </marker>
  </defs>

  <!-- Vendor exceptions -->
  <rect x="10" y="90" width="180" height="110" rx="7" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="100" y="112" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Vendor Exceptions</text>
  <line x1="20" y1="120" x2="180" y2="120" stroke="#8b949e" stroke-width="0.5"/>
  <text x="100" y="138" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">JDBC: SQLException</text>
  <text x="100" y="155" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">JPA: PersistenceException</text>
  <text x="100" y="172" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">Mongo: MongoException</text>
  <text x="100" y="189" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">Redis: RedisException</text>

  <!-- Translator -->
  <line x1="192" y1="145" x2="248" y2="145" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>
  <rect x="248" y="120" width="110" height="50" rx="6" fill="#0d1117" stroke="#6db33f" stroke-width="1.5"/>
  <text x="303" y="142" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">Exception</text>
  <text x="303" y="157" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">Translator</text>

  <line x1="360" y1="145" x2="415" y2="145" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>

  <!-- DAE hierarchy -->
  <rect x="415" y="20" width="270" height="200" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="550" y="42" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">DataAccessException</text>
  <line x1="425" y1="52" x2="675" y2="52" stroke="#8b949e" stroke-width="0.5"/>
  <text x="550" y="70" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">DuplicateKeyException</text>
  <text x="550" y="87" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">DataIntegrityViolationException</text>
  <text x="550" y="104" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">BadSqlGrammarException</text>
  <text x="550" y="121" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">CannotAcquireLockException</text>
  <text x="550" y="138" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">QueryTimeoutException</text>
  <text x="550" y="155" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">TransientDataAccessException</text>
  <text x="550" y="172" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">UncategorizedDataAccessException</text>
  <text x="550" y="205" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">same hierarchy — all backends</text>
</svg>

Vendor-specific exceptions are translated to the consistent `DataAccessException` hierarchy regardless of backend.

## 5. Runnable example

Scenario: a **`UserRepository`** — demonstrating `DuplicateKeyException`, `BadSqlGrammarException`, and catching by the hierarchy root.

### Level 1 — Basic

Catching `DuplicateKeyException` — works the same on any JDBC database.

```java
// DataAccessExceptionDemo.java
import org.springframework.context.annotation.*;
import org.springframework.jdbc.datasource.*;
import org.springframework.jdbc.datasource.embedded.*;
import org.springframework.jdbc.core.*;
import org.springframework.dao.*;

@Configuration
public class DataAccessExceptionDemo {
    @Bean public javax.sql.DataSource dataSource() {
        return new EmbeddedDatabaseBuilder().setType(EmbeddedDatabaseType.H2)
            .addScript("users-schema.sql").build();
    }
    @Bean public JdbcTemplate jdbcTemplate(javax.sql.DataSource ds) {
        return new JdbcTemplate(ds);
    }

    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(DataAccessExceptionDemo.class);
        JdbcTemplate jdbc = ctx.getBean(JdbcTemplate.class);

        // First insert — succeeds
        jdbc.update("INSERT INTO users(email) VALUES(?)", "alice@example.com");
        System.out.println("Inserted alice");

        // Duplicate insert — throws DuplicateKeyException (not vendor SQLException)
        try {
            jdbc.update("INSERT INTO users(email) VALUES(?)", "alice@example.com");
        } catch (DuplicateKeyException e) {
            System.out.println("DuplicateKeyException caught: " + e.getMessage().lines().findFirst().orElse(""));
            System.out.println("No vendor-specific error code check needed — same class on any DB");
        }
        ctx.close();
    }
}
```

`users-schema.sql`: `CREATE TABLE users (id BIGINT AUTO_INCREMENT PRIMARY KEY, email VARCHAR(100) UNIQUE);`

How to run: `java -cp spring-context.jar:spring-jdbc.jar:h2.jar:. DataAccessExceptionDemo.java`

`DuplicateKeyException` is thrown regardless of whether the underlying database is H2, PostgreSQL, MySQL, or Oracle. Spring's `SQLErrorCodeSQLExceptionTranslator` maps the vendor-specific error code to this class. The catch block is portable.

---

### Level 2 — Intermediate

Catching `BadSqlGrammarException` (syntax error) vs `DataIntegrityViolationException` (constraint), and printing the root cause.

```java
// DataAccessExceptionDemo.java
import org.springframework.context.annotation.*;
import org.springframework.jdbc.datasource.*;
import org.springframework.jdbc.datasource.embedded.*;
import org.springframework.jdbc.core.*;
import org.springframework.dao.*;

@Configuration
public class DataAccessExceptionDemo {
    @Bean public javax.sql.DataSource dataSource() {
        return new EmbeddedDatabaseBuilder().setType(EmbeddedDatabaseType.H2)
            .addScript("users-schema.sql").build();
    }
    @Bean public JdbcTemplate jdbcTemplate(javax.sql.DataSource ds) {
        return new JdbcTemplate(ds);
    }

    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(DataAccessExceptionDemo.class);
        JdbcTemplate jdbc = ctx.getBean(JdbcTemplate.class);
        jdbc.update("INSERT INTO users(email) VALUES(?)", "bob@example.com");

        // SQL syntax error
        try {
            jdbc.queryForList("SELEKT * FROM users");   // typo
        } catch (BadSqlGrammarException e) {
            System.out.println("BadSqlGrammarException: " + e.getMessage().lines().findFirst().orElse(""));
            System.out.println("Root cause type: " + e.getCause().getClass().getSimpleName());
        }

        // NOT NULL violation
        try {
            jdbc.update("INSERT INTO users(email) VALUES(null)");   // email is NOT NULL via UNIQUE
        } catch (DataIntegrityViolationException e) {
            System.out.println("DataIntegrityViolationException: " + e.getMessage().lines().findFirst().orElse(""));
        }

        // Catch by root: DataAccessException handles any data-access error
        try {
            jdbc.update("INSERT INTO users(email) VALUES(?)", "bob@example.com");
        } catch (DataAccessException e) {
            System.out.println("DataAccessException (root) caught: " + e.getClass().getSimpleName());
        }
        ctx.close();
    }
}
```

How to run: same classpath

Three different error types — SQL syntax, constraint, and duplicate key — all caught through the `DataAccessException` hierarchy. The `getCause()` method returns the original `java.sql.SQLException` with the vendor-specific error code, useful for logging.

---

### Level 3 — Advanced

Demonstrating the `TransientDataAccessException` subhierarchy and building retry logic around it.

```java
// DataAccessExceptionDemo.java
import org.springframework.context.annotation.*;
import org.springframework.jdbc.datasource.*;
import org.springframework.jdbc.datasource.embedded.*;
import org.springframework.jdbc.core.*;
import org.springframework.dao.*;
import org.springframework.dao.support.*;

@Configuration
public class DataAccessExceptionDemo {
    @Bean public javax.sql.DataSource dataSource() {
        return new EmbeddedDatabaseBuilder().setType(EmbeddedDatabaseType.H2)
            .addScript("users-schema.sql").build();
    }
    @Bean public JdbcTemplate jdbcTemplate(javax.sql.DataSource ds) {
        return new JdbcTemplate(ds);
    }
    @Bean public org.springframework.jdbc.support.SQLErrorCodeSQLExceptionTranslator translator(
            javax.sql.DataSource ds) {
        return new org.springframework.jdbc.support.SQLErrorCodeSQLExceptionTranslator(ds);
    }

    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(DataAccessExceptionDemo.class);
        JdbcTemplate jdbc = ctx.getBean(JdbcTemplate.class);

        // Demonstrate hierarchy check for retry logic
        jdbc.update("INSERT INTO users(email) VALUES(?)", "carol@example.com");

        // Successful insert
        saveWithRetry(jdbc, "dave@example.com", 3);

        // Simulate a TransientDataAccessException to demonstrate retry
        System.out.println("\nDemonstrating exception hierarchy:");
        DataAccessException dup = new DuplicateKeyException("test");
        DataAccessException transient_ = new CannotAcquireLockException("test");
        System.out.println("DuplicateKeyException is NonTransient: "
            + (dup instanceof NonTransientDataAccessException));
        System.out.println("CannotAcquireLockException is Transient: "
            + (transient_ instanceof TransientDataAccessException));

        ctx.close();
    }

    static void saveWithRetry(JdbcTemplate jdbc, String email, int maxAttempts) {
        for (int attempt = 1; attempt <= maxAttempts; attempt++) {
            try {
                jdbc.update("INSERT INTO users(email) VALUES(?)", email);
                System.out.println("Saved " + email + " on attempt " + attempt);
                return;
            } catch (TransientDataAccessException e) {
                // transient: deadlock, lock timeout — safe to retry
                System.out.println("Attempt " + attempt + " transient failure: " + e.getClass().getSimpleName());
                if (attempt == maxAttempts) throw e;
            } catch (NonTransientDataAccessException e) {
                // non-transient: duplicate key, bad SQL — no point retrying
                System.out.println("Non-transient failure — not retrying: " + e.getClass().getSimpleName());
                throw e;
            }
        }
    }
}
```

How to run: same classpath

`TransientDataAccessException` signals errors that are safe to retry (deadlocks, lock timeouts, transient network issues). `NonTransientDataAccessException` signals permanent failures (constraint violations, bad SQL). The retry helper uses the hierarchy to decide whether to retry — no vendor-specific code checks.

## 6. Walkthrough

**Translation path for H2 duplicate-key error:**

```
JdbcTemplate.update("INSERT users (alice@example.com)")
  → PreparedStatement.executeUpdate()
    → H2 throws: org.h2.jdbc.JdbcSQLIntegrityConstraintViolationException
       errorCode=23505, SQLState="23505"

  → JdbcTemplate.translateException("PreparedStatementCallback", sql, ex):
      SQLErrorCodeSQLExceptionTranslator.doTranslate(task, sql, ex):
        → load sql-error-codes.xml from classpath
        → find H2 section:
             errorCodes: duplicateKey=23505
        → errorCode 23505 → matches "duplicateKey" → return new DuplicateKeyException(msg, ex)

  → DuplicateKeyException propagates to caller
```

**Hierarchy for retry decision:**

```
DataAccessException (root, RuntimeException)
  ├── NonTransientDataAccessException
  │   └── DuplicateKeyException  ← no retry
  └── TransientDataAccessException
      └── CannotAcquireLockException  ← retry safe

catch (TransientDataAccessException) → retry
catch (NonTransientDataAccessException) → do not retry
```

## 7. Gotchas & takeaways

> **`UncategorizedDataAccessException` means Spring could not map the error.** If the database returns an error code that isn't in `sql-error-codes.xml` (e.g., a custom error code from a stored procedure), Spring wraps it in `UncategorizedSQLException`. Extract the root cause for logging and consider adding a custom `SQLExceptionTranslator`.

> **`DataAccessException` is unchecked but carries the root cause.** Use `e.getCause()` to get the original `SQLException`, `PersistenceException`, etc., with the vendor error code. This is useful for diagnostics.

> **Exception translation is NOT automatic unless you use Spring's templates or annotate with `@Repository`.** If you call JDBC directly without `JdbcTemplate`, or use JPA without `@Repository` + `PersistenceExceptionTranslationPostProcessor`, vendor exceptions are NOT translated.

- `DataAccessException` — unchecked root; no forced `try/catch`.
- `DuplicateKeyException` — the go-to catch for unique constraint violations, portable across databases.
- `TransientDataAccessException` — safe-to-retry class; use for deadlock/lock-timeout retry logic.
- `NonTransientDataAccessException` — permanent failure; do not retry.
- `e.getCause()` — get the original vendor exception for diagnostics when needed.
