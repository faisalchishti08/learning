---
card: spring-data
gi: 98
slug: drivers-postgres-mysql-mssql-h2-mariadb
title: "Drivers (Postgres, MySQL, MSSQL, H2, MariaDB)"
---

## 1. What it is

An R2DBC driver is a database-specific implementation of the R2DBC SPI (Service Provider Interface) — separate artifacts exist for Postgres (`r2dbc-postgresql`), MySQL (`r2dbc-mysql` or `dev.miku:r2dbc-mysql`), MSSQL (`r2dbc-mssql`), H2 (`r2dbc-h2`), and MariaDB (`r2dbc-mariadb`), each translating the same portable R2DBC API calls into that specific database's actual wire protocol, and each with its own quirks in type support and connection-string format.

```java
// application.properties, selecting a driver purely by connection URL scheme:
// spring.r2dbc.url=r2dbc:postgresql://localhost:5432/mydb
// spring.r2dbc.url=r2dbc:mysql://localhost:3306/mydb
// spring.r2dbc.url=r2dbc:h2:mem:///testdb
```

## 2. Why & when

The mapping-and-conversions card already flagged that R2DBC driver type support varies more than JDBC's — this card is about the drivers themselves: which one to add as a dependency, how connection URLs differ by scheme, and what to expect in terms of relative maturity, since not every R2DBC driver has the same depth of feature support or community adoption as the corresponding JDBC driver for the same database.

Reach for understanding driver differences specifically when:

- You're setting up a new Spring Data R2DBC project and need to pick and configure the correct driver dependency and connection URL scheme for your target database.
- You're debugging a connection or type-mapping issue and need to know whether it's a general R2DBC/Spring Data concept issue or something specific to your chosen driver's maturity/feature gaps.
- You're evaluating a database choice for a new reactive project and want to factor in R2DBC driver maturity as one input, since it varies meaningfully by database (Postgres and H2 tend to have the most mature, widely-used R2DBC drivers; some others are comparatively newer or less actively maintained).

## 3. Core concept

```
 Same portable Spring Data R2DBC code:
   ReactiveCrudRepository<Order, Long>, R2dbcEntityTemplate, Criteria, DatabaseClient

 Driver-specific pieces, swapped via configuration + a dependency change:
   spring.r2dbc.url=r2dbc:postgresql://host:5432/db   +  r2dbc-postgresql dependency
   spring.r2dbc.url=r2dbc:mysql://host:3306/db         +  r2dbc-mysql dependency
   spring.r2dbc.url=r2dbc:mssql://host:1433/db          +  r2dbc-mssql dependency
   spring.r2dbc.url=r2dbc:h2:mem:///testdb              +  r2dbc-h2 dependency (great for tests)
   spring.r2dbc.url=r2dbc:mariadb://host:3306/db        +  r2dbc-mariadb dependency
```

The application code stays identical across databases; only the connection URL scheme and the driver dependency on the classpath change.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.v3.org/2000/svg" role="img" aria-label="The same Spring Data R2DBC application code routes through different drivers to different databases based on the connection URL scheme">
  <rect x="200" y="10" width="240" height="45" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="320" y="37" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">same Spring Data R2DBC code</text>

  <rect x="20" y="90" width="140" height="40" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.3"/>
  <text x="90" y="113" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">r2dbc-postgresql</text>

  <rect x="180" y="90" width="140" height="40" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.3"/>
  <text x="250" y="113" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">r2dbc-mysql</text>

  <rect x="340" y="90" width="140" height="40" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.3"/>
  <text x="410" y="113" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">r2dbc-h2</text>

  <rect x="500" y="90" width="120" height="40" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.3"/>
  <text x="560" y="113" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">r2dbc-mssql</text>

  <line x1="260" y1="55" x2="110" y2="85" stroke="#8b949e" stroke-width="1.2" marker-end="url(#dr)"/>
  <line x1="300" y1="55" x2="250" y2="85" stroke="#8b949e" stroke-width="1.2" marker-end="url(#dr)"/>
  <line x1="340" y1="55" x2="400" y2="85" stroke="#8b949e" stroke-width="1.2" marker-end="url(#dr)"/>
  <line x1="380" y1="55" x2="550" y2="85" stroke="#8b949e" stroke-width="1.2" marker-end="url(#dr)"/>
  <defs><marker id="dr" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

The same application code is portable across databases — only the driver dependency and connection URL scheme need to change per target database.

## 5. Runnable example

The scenario: configuring an application to target different databases, evolving from a single hard-coded driver choice, to a configuration-driven driver selector supporting several databases, to a small compatibility-check helper that flags known driver-specific type-support gaps before runtime.

### Level 1 — Basic

Model choosing a single driver via its connection URL scheme, standing in for one line in `application.properties`.

```java
import java.util.*;

public class DriversLevel1 {
    record R2dbcConfig(String urlScheme, String driverDependency) {}

    public static void main(String[] args) {
        // spring.r2dbc.url=r2dbc:postgresql://localhost:5432/mydb
        R2dbcConfig config = new R2dbcConfig("r2dbc:postgresql://localhost:5432/mydb", "io.r2dbc:r2dbc-postgresql");

        System.out.println("Connection URL: " + config.urlScheme());
        System.out.println("Required dependency: " + config.driverDependency());
    }
}
```

How to run: `java DriversLevel1.java`

`R2dbcConfig` bundles the connection URL scheme with the dependency it requires — in a real project, this is exactly the pair of decisions made once at setup time: a `spring.r2dbc.url` property, and a matching driver artifact added to the build file.

### Level 2 — Intermediate

Build a small driver-selection function supporting several databases, mapping a database name to its scheme and dependency, matching the concept section's full list.

```java
import java.util.*;

public class DriversLevel2 {
    record R2dbcConfig(String urlScheme, String driverDependency) {}

    static R2dbcConfig configFor(String database, String host, String dbName) {
        return switch (database) {
            case "postgres" -> new R2dbcConfig("r2dbc:postgresql://" + host + ":5432/" + dbName, "io.r2dbc:r2dbc-postgresql");
            case "mysql" -> new R2dbcConfig("r2dbc:mysql://" + host + ":3306/" + dbName, "dev.miku:r2dbc-mysql");
            case "mssql" -> new R2dbcConfig("r2dbc:mssql://" + host + ":1433/" + dbName, "io.r2dbc:r2dbc-mssql");
            case "h2" -> new R2dbcConfig("r2dbc:h2:mem:///" + dbName, "io.r2dbc:r2dbc-h2");
            case "mariadb" -> new R2dbcConfig("r2dbc:mariadb://" + host + ":3306/" + dbName, "org.mariadb:r2dbc-mariadb");
            default -> throw new IllegalArgumentException("Unknown database: " + database);
        };
    }

    public static void main(String[] args) {
        for (String db : List.of("postgres", "mysql", "h2")) {
            R2dbcConfig config = configFor(db, "localhost", "mydb");
            System.out.println(db + " -> " + config.urlScheme() + "  (needs " + config.driverDependency() + ")");
        }
    }
}
```

How to run: `java DriversLevel2.java`

`configFor` mechanically encodes the concept section's table — each database maps to its own connection URL scheme and driver dependency; the application's own repository/entity code stays completely unaffected by which branch of this `switch` was chosen, since it only ever depends on the portable Spring Data R2DBC API.

### Level 3 — Advanced

Add a compatibility-check helper flagging known driver-specific type-support gaps (mirroring the mapping-and-conversions card's `Year` example) before an application actually starts, so mismatches are caught early rather than surfacing as a runtime error mid-query.

```java
import java.util.*;

public class DriversLevel3 {
    record R2dbcConfig(String urlScheme, String driverDependency, Set<String> knownUnsupportedTypes) {}

    static R2dbcConfig configFor(String database) {
        return switch (database) {
            case "postgres" -> new R2dbcConfig("r2dbc:postgresql://...", "io.r2dbc:r2dbc-postgresql", Set.of());
            case "mysql" -> new R2dbcConfig("r2dbc:mysql://...", "dev.miku:r2dbc-mysql", Set.of("java.time.Year", "java.util.UUID"));
            case "h2" -> new R2dbcConfig("r2dbc:h2:mem:///...", "io.r2dbc:r2dbc-h2", Set.of());
            default -> throw new IllegalArgumentException("Unknown database: " + database);
        };
    }

    // Checks whether an entity's field types are all natively supported by the chosen driver,
    // flagging any that would need a custom conversion (per the mapping-and-conversions card).
    static List<String> checkCompatibility(R2dbcConfig config, Map<String, String> entityFieldTypes) {
        List<String> warnings = new ArrayList<>();
        for (Map.Entry<String, String> field : entityFieldTypes.entrySet()) {
            if (config.knownUnsupportedTypes().contains(field.getValue())) {
                warnings.add("Field '" + field.getKey() + "' of type " + field.getValue()
                    + " is NOT natively supported by this driver -- register a custom conversion");
            }
        }
        return warnings;
    }

    public static void main(String[] args) {
        Map<String, String> orderFields = Map.of(
            "id", "java.lang.Long",
            "foundingYear", "java.time.Year",
            "externalRef", "java.util.UUID"
        );

        for (String db : List.of("postgres", "mysql")) {
            R2dbcConfig config = configFor(db);
            List<String> warnings = checkCompatibility(config, orderFields);
            System.out.println("Checking " + db + ":");
            if (warnings.isEmpty()) System.out.println("  All field types natively supported.");
            else warnings.forEach(w -> System.out.println("  WARNING: " + w));
        }
    }
}
```

How to run: `java DriversLevel3.java`

For `postgres` (with an empty `knownUnsupportedTypes` set in this simplified model), `checkCompatibility` reports no warnings. For `mysql` (which this example flags as lacking native support for `java.time.Year` and `java.util.UUID`), both `foundingYear` and `externalRef` produce warnings — surfacing exactly the kind of driver-specific gap the mapping-and-conversions card described, but here caught by an explicit compatibility check rather than discovered as a runtime "unsupported type" error.

## 6. Walkthrough

Execution starts in `main` for Level 3. First, `orderFields` is built, describing three fields on a hypothetical `Order` entity and their Java types: `id` (`Long`), `foundingYear` (`Year`), `externalRef` (`UUID`).

The loop iterates over `["postgres", "mysql"]`. For `"postgres"`, `configFor("postgres")` returns a config with an empty `knownUnsupportedTypes` set. `checkCompatibility(config, orderFields)` iterates over all three fields, and since none of their types appear in the (empty) unsupported set, `warnings` stays empty — the printed output shows "All field types natively supported."

For `"mysql"`, `configFor("mysql")` returns a config whose `knownUnsupportedTypes` includes `"java.time.Year"` and `"java.util.UUID"`. `checkCompatibility` again iterates over all three fields: `id`'s type (`"java.lang.Long"`) isn't in the unsupported set, so no warning; `foundingYear`'s type (`"java.time.Year"`) *is* in the set, so a warning is added; `externalRef`'s type (`"java.util.UUID"`) *is* also in the set, so a second warning is added. The printed output shows both warnings, each naming the specific field and type that would need a custom conversion registered.

```
checkCompatibility(postgres, orderFields):
  id(Long) -> not unsupported        foundingYear(Year) -> not unsupported (postgres set is empty)
  externalRef(UUID) -> not unsupported
  -> no warnings

checkCompatibility(mysql, orderFields):
  id(Long) -> not unsupported         foundingYear(Year) -> UNSUPPORTED -> warning
  externalRef(UUID) -> UNSUPPORTED -> warning
  -> 2 warnings
```

In a real project, this kind of compatibility check isn't something Spring Data R2DBC runs automatically — it's a useful pattern to build (or a check to perform manually against a specific driver's documentation) before committing to a particular database and entity design, since discovering a type-support gap only when a query throws an "unsupported type" error at runtime is a much more expensive way to learn the same information the compatibility check surfaces up front.

## 7. Gotchas & takeaways

> Gotcha: R2DBC driver maturity and feature completeness vary significantly by database — Postgres and H2 tend to have the most mature, widely-used R2DBC drivers, while some other databases' R2DBC drivers are comparatively newer, less feature-complete, or less actively maintained than their long-established JDBC counterparts; this is a genuine factor to weigh when choosing a database for a new reactive project, not just an implementation detail.

- Each database requires its own R2DBC driver dependency and connection URL scheme (`r2dbc:postgresql://`, `r2dbc:mysql://`, `r2dbc:h2:mem://`, etc.) — application code built on Spring Data R2DBC's portable API stays unchanged across all of them.
- H2's R2DBC driver, with its in-memory mode (`r2dbc:h2:mem:///testdb`), is a common choice for fast, dependency-free reactive integration tests.
- R2DBC driver maturity and type-support completeness vary more by database than mature JDBC drivers typically do — factor this in when choosing a database for a reactive project.
- Checking a driver's type-support gaps up front (or building an explicit compatibility check) is cheaper than discovering them as a runtime "unsupported type" error.
