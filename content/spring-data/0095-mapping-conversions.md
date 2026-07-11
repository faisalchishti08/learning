---
card: spring-data
gi: 95
slug: mapping-conversions
title: "Mapping & conversions"
---

## 1. What it is

Spring Data R2DBC's entity-to-table mapping follows the same convention-based algorithm as Spring Data JDBC (from the earlier section) — table/column naming conventions, `@Id`/`@Table`/`@Column` overrides — and it supports custom conversions the same way (a `Converter<S, T>` pair registered for types with no natural column mapping). The main practical difference is which types the underlying R2DBC driver natively supports, since drivers vary more here than the mature JDBC ecosystem does.

```java
class Order {
    @Id Long id;
    @Column("order_status") String status;  // same annotation-driven overrides as Spring Data JDBC
}
// Custom conversions registered via R2dbcCustomConversions, mirroring JdbcCustomConversions
```

## 2. Why & when

Everything the earlier JDBC-section cards on mapping conventions, `@Id`/`@Table`/`@Column`, and custom conversions taught carries over almost unchanged to R2DBC — this card exists to confirm that transfer explicitly and flag the one place it doesn't: driver-level type support varies more between R2DBC drivers (Postgres, MySQL, H2, ...) than between JDBC drivers, since R2DBC is a younger, less uniformly-implemented specification.

Reach for an explicit understanding of R2DBC mapping specifically when:

- You're moving code (or knowledge) from Spring Data JDBC to R2DBC and want to know exactly what carries over unchanged — the answer is: almost the entire mapping and conversion model.
- A field's type isn't supported natively by your specific R2DBC driver (more likely here than with JDBC) — a custom conversion, registered via `R2dbcCustomConversions`, is the fix, exactly mirroring `JdbcCustomConversions`.
- You're debugging a "cannot convert" or "unsupported type" error at query time — this is often a driver-level type-support gap specific to R2DBC, not a mapping-convention mistake.

## 3. Core concept

```
 Table/column naming:     SAME convention as Spring Data JDBC (camelCase -> snake_case, etc.)
 @Id/@Table/@Column:       SAME annotations, SAME meaning, SAME overrides
 Custom conversions:       SAME Converter<S,T> pair pattern, registered via R2dbcCustomConversions
                            instead of JdbcCustomConversions

 DIFFERENCE: R2DBC driver type support is less uniform than JDBC's
   -- a type natively supported by the Postgres R2DBC driver might need
      a custom conversion for the MySQL or H2 R2DBC driver, even for the SAME Java type
```

Almost everything about entity mapping is shared with Spring Data JDBC — the meaningful difference is that driver-level type support gaps are more common and more driver-specific in the R2DBC ecosystem.

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.v3.org/2000/svg" role="img" aria-label="Mapping conventions and custom conversions transfer directly from Spring Data JDBC, while driver type support varies by R2DBC driver">
  <rect x="20" y="20" width="280" height="100" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="160" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Shared with Spring Data JDBC</text>
  <text x="35" y="65" fill="#8b949e" font-size="8.5" font-family="sans-serif">naming conventions</text>
  <text x="35" y="82" fill="#8b949e" font-size="8.5" font-family="sans-serif">@Id/@Table/@Column</text>
  <text x="35" y="99" fill="#8b949e" font-size="8.5" font-family="sans-serif">Converter&lt;S,T&gt; pair pattern</text>

  <rect x="340" y="20" width="280" height="100" rx="8" fill="#1c2430" stroke="#f85149" stroke-width="1.5"/>
  <text x="480" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">R2DBC-specific difference</text>
  <text x="355" y="65" fill="#8b949e" font-size="8.5" font-family="sans-serif">driver type support VARIES</text>
  <text x="355" y="82" fill="#8b949e" font-size="8.5" font-family="sans-serif">by driver (Postgres/MySQL/H2/...)</text>
  <text x="355" y="99" fill="#8b949e" font-size="8.5" font-family="sans-serif">more custom conversions often needed</text>
</svg>

Most of the mapping model transfers directly; the practical gap is driver-specific type support, which needs more frequent custom conversions.

## 5. Runnable example

The scenario: mapping an order with a status enum, evolving from applying the same naming/annotation conventions from the JDBC section unchanged, to a custom conversion pair (mirroring the JDBC custom-conversions card exactly), to handling a driver-specific type-support gap that forces a conversion where one driver might not have needed it.

### Level 1 — Basic

Confirm the naming/annotation conventions transfer directly — this is deliberately almost identical to the JDBC mapping card's Level 1.

```java
import java.util.*;

public class MappingConversionsLevel1 {
    static String toSnakeCase(String name) {
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < name.length(); i++) {
            char c = name.charAt(i);
            if (Character.isUpperCase(c)) { if (i > 0) sb.append('_'); sb.append(Character.toLowerCase(c)); }
            else sb.append(c);
        }
        return sb.toString();
    }

    record FieldMapping(String javaField, String explicitOverride) {
        String resolvedColumn() { return explicitOverride != null ? toSnakeCase(explicitOverride) : toSnakeCase(javaField); }
    }

    public static void main(String[] args) {
        // class Order { @Id Long id; @Column("order_status") String status; double totalAmount; }
        List<FieldMapping> fields = List.of(
            new FieldMapping("id", null),
            new FieldMapping("status", "order_status"), // @Column override
            new FieldMapping("totalAmount", null)
        );
        for (FieldMapping f : fields) System.out.println(f.javaField() + " -> " + f.resolvedColumn());
    }
}
```

How to run: `java MappingConversionsLevel1.java`

`totalAmount` resolves to `total_amount` (default convention) and `status` resolves to `order_status` (explicit `@Column` override, still passed through the same snake_case physical-naming step) — identical behavior to the Spring Data JDBC naming-strategies and `@Id`/`@Table`/`@Column` cards, confirming the mapping convention transfers unchanged.

### Level 2 — Intermediate

Register a custom conversion pair for an enum type, mirroring the JDBC section's custom-conversions card exactly, but registered via the R2DBC-specific class name.

```java
import java.util.*;

enum OrderStatus { PENDING, SHIPPED, CANCELLED }

// Converter<OrderStatus, String>
class OrderStatusToStringConverter { String convert(OrderStatus s) { return s.name(); } }
// Converter<String, OrderStatus>
class StringToOrderStatusConverter { OrderStatus convert(String s) { return OrderStatus.valueOf(s); } }

public class MappingConversionsLevel2 {
    public static void main(String[] args) {
        // R2dbcCustomConversions customConversions() {
        //     return new R2dbcCustomConversions(List.of(
        //         new OrderStatusToStringConverter(), new StringToOrderStatusConverter()));
        // }
        OrderStatusToStringConverter toColumn = new OrderStatusToStringConverter();
        StringToOrderStatusConverter fromColumn = new StringToOrderStatusConverter();

        OrderStatus status = OrderStatus.SHIPPED;
        String columnValue = toColumn.convert(status);
        System.out.println("Write path: " + status + " -> \"" + columnValue + "\"");

        OrderStatus reconstructed = fromColumn.convert(columnValue);
        System.out.println("Read path: \"" + columnValue + "\" -> " + reconstructed);
        System.out.println("Round-trip successful? " + (status == reconstructed));
    }
}
```

How to run: `java MappingConversionsLevel2.java`

This is functionally identical to the JDBC custom-conversions card's converter-pair pattern — the only real difference in a genuine Spring Boot application is registering the pair via `R2dbcCustomConversions` instead of `JdbcCustomConversions`, since the two modules share the conceptual conversion mechanism but wire it into their respective, separate infrastructure.

### Level 3 — Advanced

Model a driver-specific type-support gap: a Java `java.time.Year` field that one simulated driver supports natively but another doesn't, requiring a conversion only for the less-capable driver.

```java
import java.time.Year;
import java.util.*;

interface Driver {
    boolean supportsNatively(Class<?> type);
    String describe();
}

class PostgresLikeDriver implements Driver {
    public boolean supportsNatively(Class<?> type) { return true; } // hypothetically supports Year directly
    public String describe() { return "Postgres-like driver"; }
}

class MySqlLikeDriver implements Driver {
    public boolean supportsNatively(Class<?> type) { return type != Year.class; } // does NOT support Year natively
    public String describe() { return "MySQL-like driver"; }
}

// Converter<Year, Integer> / Converter<Integer, Year> -- needed ONLY for drivers lacking native Year support
class YearToIntegerConverter { Integer convert(Year y) { return y.getValue(); } }
class IntegerToYearConverter { Year convert(Integer i) { return Year.of(i); } }

public class MappingConversionsLevel3 {
    static Object writeYearColumn(Driver driver, Year year) {
        if (driver.supportsNatively(Year.class)) {
            System.out.println("  [" + driver.describe() + "] native support -- no conversion needed, writing Year directly");
            return year;
        } else {
            System.out.println("  [" + driver.describe() + "] NO native support -- applying YearToIntegerConverter");
            return new YearToIntegerConverter().convert(year);
        }
    }

    public static void main(String[] args) {
        Year foundingYear = Year.of(2010);

        Object postgresValue = writeYearColumn(new PostgresLikeDriver(), foundingYear);
        System.out.println("  Postgres-like column value: " + postgresValue + " (" + postgresValue.getClass().getSimpleName() + ")");

        Object mysqlValue = writeYearColumn(new MySqlLikeDriver(), foundingYear);
        System.out.println("  MySQL-like column value: " + mysqlValue + " (" + mysqlValue.getClass().getSimpleName() + ")");
    }
}
```

How to run: `java MappingConversionsLevel3.java`

The exact same `Year` value produces a `Year`-typed column value for the Postgres-like driver (native support, no conversion applied) but an `Integer`-typed value for the MySQL-like driver (no native support, `YearToIntegerConverter` applied) — the same Java field, the same entity, needs a custom conversion registered for one target database's R2DBC driver but not another's, exactly the driver-variability this card's concept section describes.

## 6. Walkthrough

Execution starts in `main` for Level 3. First, `foundingYear` is set to `Year.of(2010)`.

`writeYearColumn(new PostgresLikeDriver(), foundingYear)` runs: `driver.supportsNatively(Year.class)` returns `true` for `PostgresLikeDriver` (by this example's simplified design), so the method prints "native support -- no conversion needed" and returns `year` itself, unconverted — the column value stays a `Year` object.

`writeYearColumn(new MySqlLikeDriver(), foundingYear)` runs next, with the *same* `foundingYear` value: `driver.supportsNatively(Year.class)` returns `false` for `MySqlLikeDriver` (since its `supportsNatively` explicitly excludes `Year.class`), so the method takes the other branch, prints "NO native support -- applying YearToIntegerConverter", and returns `new YearToIntegerConverter().convert(year)` — extracting the plain `int` value `2010` wrapped as an `Integer`.

The two printed column-value lines confirm the difference: `Postgres-like column value: 2010 (Year)` versus `MySQL-like column value: 2010 (Integer)` — identical underlying data, but a genuinely different Java type reaching the database driver depending on which one is in use.

```
foundingYear = Year.of(2010)

writeYearColumn(PostgresLikeDriver, foundingYear):
  supportsNatively(Year) == true  -> no conversion -> column value: Year(2010)

writeYearColumn(MySqlLikeDriver, foundingYear):
  supportsNatively(Year) == false -> YearToIntegerConverter applied -> column value: Integer(2010)
```

In a real Spring Data R2DBC application, whether a `Year`-typed (or any less-common-typed) field needs a registered `R2dbcCustomConversions` pair depends entirely on which R2DBC driver the application uses — the Postgres R2DBC driver might handle a given Java type natively, while the MySQL or MSSQL driver requires an explicit converter for the exact same field on the exact same entity class. This is the practical, day-to-day consequence of R2DBC's younger, less uniformly-implemented driver ecosystem compared to the long-maturity JDBC drivers used by the earlier Spring Data JDBC section — the mapping and conversion *mechanism* is identical, but *when* you actually need to reach for it varies by database.

## 7. Gotchas & takeaways

> Gotcha: a custom conversion written and tested against one R2DBC driver (say, Postgres) may turn out to be entirely unnecessary — or, worse, may conflict with that *other* driver's own native handling — if the application later switches databases; always verify custom conversions against the specific R2DBC driver actually in use, not assume conversions are portable across drivers the way they mostly are across JDBC drivers.

- Spring Data R2DBC's mapping conventions and `@Id`/`@Table`/`@Column` annotations work identically to Spring Data JDBC — this knowledge transfers directly.
- Custom conversions follow the same `Converter<S, T>` pair pattern, registered via `R2dbcCustomConversions` instead of `JdbcCustomConversions`.
- The meaningful practical difference is driver-level type support: R2DBC drivers vary more in what they handle natively than mature JDBC drivers do, so custom conversions are needed more often and more driver-specifically.
- Always verify type support against the specific R2DBC driver in use — a conversion unnecessary for one database's driver may be required for another's, even for the identical Java field.
