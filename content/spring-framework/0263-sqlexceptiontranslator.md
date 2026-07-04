---
card: spring-framework
gi: 263
slug: sqlexceptiontranslator
title: SQLExceptionTranslator
---

## 1. What it is

`SQLExceptionTranslator` is the interface Spring uses to convert a raw `java.sql.SQLException` — with its database-vendor-specific error code — into a meaningful, vendor-neutral `DataAccessException` subclass.

```java
// Without Spring: every caller must handle vendor-specific codes
} catch (SQLException e) {
    if ("23505".equals(e.getSQLState())) {  // PostgreSQL: unique violation
        throw new DuplicateKeyException(...);
    }
    // what about MySQL? Oracle? H2?
}

// With Spring: JdbcTemplate translates automatically
} catch (DuplicateKeyException e) {
    // same class regardless of database vendor
}
```

The default implementation is `SQLErrorCodeSQLExceptionTranslator`, which looks up error codes in `sql-error-codes.xml` (bundled in `spring-jdbc.jar`) keyed by database product name.

## 2. Why & when

`JdbcTemplate` applies translation automatically on every operation — you normally never call the translator directly. Understanding it matters when:

- You want to **customise the mapping** for your specific application (e.g., map a business-constraint violation to a domain exception).
- You debug an unexpectedly generic `DataAccessException` and want to know why it didn't get a more specific subtype.
- You add a new database or JDBC driver whose error codes aren't in the default `sql-error-codes.xml`.
- You write a `@Repository` class that uses plain JDBC (not `JdbcTemplate`) and want the same translation.

## 3. Core concept

Translation hierarchy:

```
SQLExceptionTranslator               (interface)
  └── AbstractFallbackSQLExceptionTranslator
        ├── SQLErrorCodeSQLExceptionTranslator  ← default; uses sql-error-codes.xml
        ├── SQLStateSQLExceptionTranslator       ← fallback; uses XOPEN/SQL-92 SQL state codes
        └── SQLExceptionSubclassTranslator       ← uses JDBC 4.x exception subclasses
```

`SQLErrorCodeSQLExceptionTranslator` tries in order:

1. Check the custom translator (if configured via `setCustomTranslator()`).
2. Look up `exception.getErrorCode()` in the vendor's section of `sql-error-codes.xml`.
3. Fall back to `SQLStateSQLExceptionTranslator` if no error code matches.

Key `DataAccessException` subclasses produced:

| `DataAccessException` subclass | Typical cause |
|---|---|
| `DuplicateKeyException` | Unique constraint violation |
| `DataIntegrityViolationException` | FK violation, NOT NULL violation |
| `BadSqlGrammarException` | Syntax error, unknown table |
| `QueryTimeoutException` | Statement timeout exceeded |
| `CannotAcquireLockException` | Lock timeout / deadlock |
| `DataRetrievalFailureException` | Row expected but not found |

## 4. Diagram

<svg viewBox="0 0 700 230" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <marker id="arr" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <polygon points="0 0,8 3,0 6" fill="#6db33f"/>
    </marker>
    <marker id="arr2" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <polygon points="0 0,8 3,0 6" fill="#79c0ff"/>
    </marker>
  </defs>

  <!-- SQLException -->
  <rect x="10" y="90" width="130" height="50" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="75" y="111" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="monospace">SQLException</text>
  <text x="75" y="126" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">errorCode=23505</text>

  <line x1="142" y1="115" x2="195" y2="115" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>

  <!-- Translator box -->
  <rect x="195" y="45" width="250" height="140" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="320" y="67" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">SQLErrorCodeSQLExceptionTranslator</text>
  <line x1="205" y1="73" x2="435" y2="73" stroke="#8b949e" stroke-width="0.5"/>
  <text x="320" y="92" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">1. custom translator?</text>
  <text x="320" y="108" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">2. lookup errorCode in sql-error-codes.xml</text>
  <text x="320" y="124" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">   H2 section: 23505 → DuplicateKeyException</text>
  <text x="320" y="140" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">3. fallback: SQLStateSQLExceptionTranslator</text>
  <text x="320" y="156" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">4. last resort: UncategorizedSQLException</text>
  <text x="320" y="173" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="monospace">original SQLException preserved as cause</text>

  <line x1="447" y1="115" x2="500" y2="115" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>

  <!-- DataAccessException -->
  <rect x="500" y="90" width="175" height="50" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="587" y="111" fill="#6db33f" font-size="9" text-anchor="middle" font-family="monospace">DuplicateKeyException</text>
  <text x="587" y="126" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">extends DataAccessException</text>
</svg>

`JdbcTemplate` catches every `SQLException`, passes it to the translator, and rethrows the mapped `DataAccessException`.

## 5. Runnable example

Scenario: an **order system** — demonstrate how Spring translates constraint violations, add a custom translator for a domain-specific error code, and verify translation manually.

### Level 1 — Basic

Observe automatic translation of a unique-constraint violation.

```java
// SqlTranslatorDemo.java
import org.springframework.dao.*;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.jdbc.datasource.embedded.*;
import javax.sql.DataSource;

public class SqlTranslatorDemo {

    static DataSource buildDs() {
        return new EmbeddedDatabaseBuilder()
            .setType(EmbeddedDatabaseType.H2)
            .addScript("classpath:orders-schema.sql")
            .build();
    }

    public static void main(String[] args) {
        JdbcTemplate jdbc = new JdbcTemplate(buildDs());

        // Insert two orders
        jdbc.update("INSERT INTO orders(ref,amount) VALUES(?,?)", "ORD-001", 99.0);
        jdbc.update("INSERT INTO orders(ref,amount) VALUES(?,?)", "ORD-002", 49.0);
        System.out.println("Inserted 2 orders OK");

        // Duplicate ref — unique constraint violation
        try {
            jdbc.update("INSERT INTO orders(ref,amount) VALUES(?,?)", "ORD-001", 11.0);
        } catch (DuplicateKeyException e) {
            System.out.println("Caught: " + e.getClass().getSimpleName());
            System.out.println("Message: " + e.getMessage().split("\n")[0]);
        }

        // Null violation — DataIntegrityViolationException
        try {
            jdbc.update("INSERT INTO orders(ref,amount) VALUES(?,?)", null, 5.0);
        } catch (DataIntegrityViolationException e) {
            System.out.println("Caught: " + e.getClass().getSimpleName());
        }
    }
}
```

`orders-schema.sql`:
```sql
CREATE TABLE orders (
  id     BIGINT AUTO_INCREMENT PRIMARY KEY,
  ref    VARCHAR(50) NOT NULL UNIQUE,
  amount DOUBLE      NOT NULL
);
```

How to run: `java -cp spring-context.jar:spring-jdbc.jar:h2.jar:. SqlTranslatorDemo.java`

H2 throws `SQLException` with error code `23505` (unique violation) and `23502` (NOT NULL violation). `JdbcTemplate` catches these and `SQLErrorCodeSQLExceptionTranslator` translates them to `DuplicateKeyException` and `DataIntegrityViolationException` — both are unchecked, both extend `DataAccessException`.

---

### Level 2 — Intermediate

Invoke the translator directly and inspect the hierarchy.

```java
// SqlTranslatorDemo.java
import org.springframework.dao.*;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.jdbc.datasource.*;
import org.springframework.jdbc.datasource.embedded.*;
import org.springframework.jdbc.support.*;
import javax.sql.DataSource;
import java.sql.SQLException;

public class SqlTranslatorDemo {

    static DataSource buildDs() {
        return new EmbeddedDatabaseBuilder()
            .setType(EmbeddedDatabaseType.H2)
            .addScript("classpath:orders-schema.sql")
            .build();
    }

    public static void main(String[] args) {
        DataSource ds = buildDs();
        JdbcTemplate jdbc = new JdbcTemplate(ds);

        jdbc.update("INSERT INTO orders(ref,amount) VALUES(?,?)", "ORD-100", 50.0);

        // Get the same translator JdbcTemplate uses internally
        SQLErrorCodeSQLExceptionTranslator translator =
            new SQLErrorCodeSQLExceptionTranslator(ds);

        // Simulate a duplicate-key SQLException manually
        SQLException duplicateSex = new SQLException(
            "Unique index violation", "23505", 23505);
        DataAccessException dax = translator.translate("test task", "INSERT ...", duplicateSex);
        System.out.println("Translated: " + dax.getClass().getSimpleName());
        // → DuplicateKeyException

        // Simulate a syntax-error SQLException
        SQLException syntaxEx = new SQLException(
            "Syntax error near 'SLECT'", "42000", 42000);
        DataAccessException syntaxDax = translator.translate("test", "SLECT * FROM orders", syntaxEx);
        System.out.println("Translated: " + syntaxDax.getClass().getSimpleName());
        // → BadSqlGrammarException

        // Original cause is preserved
        System.out.println("Original SQL state: "
            + ((BadSqlGrammarException)syntaxDax).getSQLException().getSQLState());

        // Demonstrate exception hierarchy
        try {
            jdbc.update("INSERT INTO orders(ref,amount) VALUES(?,?)", "ORD-100", 10.0);
        } catch (DataAccessException e) {
            System.out.println("Is DataAccessException: " + (e instanceof DataAccessException));
            System.out.println("Is DuplicateKeyException: " + (e instanceof DuplicateKeyException));
            System.out.println("Is DataIntegrityViolation: " + (e instanceof DataIntegrityViolationException));
        }
    }
}
```

How to run: same classpath

`SQLErrorCodeSQLExceptionTranslator.translate(task, sql, sqlEx)` is exactly what `JdbcTemplate` calls internally. Constructing it with a `DataSource` lets it detect the database product name and load the matching section from `sql-error-codes.xml`. The original `SQLException` is always set as `getCause()` on the resulting `DataAccessException`.

---

### Level 3 — Advanced

Custom `SQLExceptionTranslator` that maps a domain-specific check-constraint violation to a domain exception.

```java
// SqlTranslatorDemo.java
import org.springframework.dao.*;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.jdbc.datasource.embedded.*;
import org.springframework.jdbc.support.*;
import javax.sql.DataSource;
import java.sql.SQLException;

// Domain-specific exception
class NegativeAmountException extends DataIntegrityViolationException {
    NegativeAmountException(String msg, Throwable cause) { super(msg, cause); }
}

public class SqlTranslatorDemo {

    static DataSource buildDs() {
        return new EmbeddedDatabaseBuilder()
            .setType(EmbeddedDatabaseType.H2)
            .addScript("classpath:orders-schema2.sql")  // adds CHECK constraint
            .build();
    }

    public static void main(String[] args) {
        DataSource ds = buildDs();
        JdbcTemplate jdbc = new JdbcTemplate(ds);

        // Custom translator that wraps standard translation with domain logic
        SQLExceptionTranslator baseTranslator = new SQLErrorCodeSQLExceptionTranslator(ds);
        SQLExceptionTranslator customTranslator = (task, sql, ex) -> {
            // H2 check-constraint violation: error code 23514
            if (ex.getErrorCode() == 23514 && ex.getMessage().contains("AMOUNT")) {
                return new NegativeAmountException(
                    "Order amount must be positive (check constraint violated)", ex);
            }
            // Fall back to standard translation for everything else
            return baseTranslator.translate(task, sql, ex);
        };

        // Wire custom translator into JdbcTemplate
        jdbc.setExceptionTranslator(customTranslator);

        // Normal insert succeeds
        jdbc.update("INSERT INTO orders(ref,amount) VALUES(?,?)", "ORD-200", 75.0);
        System.out.println("ORD-200 inserted OK");

        // Negative amount — triggers custom translation
        try {
            jdbc.update("INSERT INTO orders(ref,amount) VALUES(?,?)", "ORD-BAD", -5.0);
        } catch (NegativeAmountException e) {
            System.out.println("Caught domain exception: " + e.getClass().getSimpleName());
            System.out.println("Message: " + e.getMessage());
        }

        // Duplicate key still uses standard translation
        jdbc.update("INSERT INTO orders(ref,amount) VALUES(?,?)", "ORD-300", 10.0);
        try {
            jdbc.update("INSERT INTO orders(ref,amount) VALUES(?,?)", "ORD-300", 10.0);
        } catch (DuplicateKeyException e) {
            System.out.println("Standard translation still works: " + e.getClass().getSimpleName());
        }
    }
}
```

`orders-schema2.sql`:
```sql
CREATE TABLE orders (
  id     BIGINT AUTO_INCREMENT PRIMARY KEY,
  ref    VARCHAR(50) NOT NULL UNIQUE,
  amount DOUBLE      NOT NULL,
  CONSTRAINT chk_amount CHECK (amount > 0)
);
```

How to run: same classpath

`jdbc.setExceptionTranslator(customTranslator)` replaces `JdbcTemplate`'s default translator. The custom lambda checks the H2 error code and message first — if it matches the domain rule, return a domain exception; otherwise fall through to the standard translator. This approach keeps domain meaning in the exception hierarchy without spreading error-code parsing across callers.

## 6. Walkthrough

**Level 3 execution — custom translator for check-constraint violation:**

1. **`jdbc.update("INSERT INTO orders(ref,amount) VALUES(?,?)","ORD-BAD",-5.0)`**: `JdbcTemplate` acquires a connection, prepares the statement, binds `["ORD-BAD", -5.0]`, calls `ps.executeUpdate()`.
2. **H2 rejects the row**: `amount > 0` check constraint fails. H2 throws `java.sql.SQLException` with `errorCode=23514`, `SQLState="23514"`, message containing `"Check constraint violation: AMOUNT"`.
3. **`JdbcTemplate` catches `SQLException`** in its `execute()` method's catch block.
4. **`jdbc.getExceptionTranslator()`** returns the custom translator lambda.
5. **Custom lambda runs**: checks `ex.getErrorCode() == 23514` → true; `ex.getMessage().contains("AMOUNT")` → true → creates `NegativeAmountException("Order amount must be positive...", ex)`.
6. **`JdbcTemplate` rethrows** the `NegativeAmountException` (it's a `DataAccessException`, so no wrapping needed).
7. **Caller catches `NegativeAmountException`** — domain exception, not raw SQL error.

```
JDBC call:
  SQL: INSERT INTO orders(ref,amount) VALUES(?,?)
  Params: ["ORD-BAD", -5.0]
  DB response: SQLException(errorCode=23514, "Check constraint violation: AMOUNT")

Translation:
  customTranslator.translate("update", sql, sqlEx)
    → errorCode==23514 && msg contains "AMOUNT" → true
    → return new NegativeAmountException(...)

JdbcTemplate:
  throw NegativeAmountException (unchecked)
```

## 7. Gotchas & takeaways

> **Custom translators must handle null returns.** If your custom translator returns `null` for an unrecognised exception, `JdbcTemplate` will throw a `NullPointerException`. Always fall back to the standard translator or return an `UncategorizedSQLException`.

> **Error codes are database-product-specific.** H2's `23505` for duplicate keys; PostgreSQL uses `23505` too (SQL state), but MySQL uses vendor code `1062`. The `sql-error-codes.xml` file has sections for each DB — if you switch databases, the translation still works because the XML is keyed by product name detected at runtime.

- `JdbcTemplate` translates every `SQLException` automatically — you rarely call the translator yourself.
- `SQLErrorCodeSQLExceptionTranslator` uses `sql-error-codes.xml` bundled in `spring-jdbc.jar`.
- The original `SQLException` (with its vendor code) is always preserved as `getCause()`.
- `jdbc.setExceptionTranslator(custom)` replaces the default — always fall back for unrecognised codes.
- For `@Repository` classes, `PersistenceExceptionTranslationPostProcessor` applies the same translation outside of `JdbcTemplate`.
