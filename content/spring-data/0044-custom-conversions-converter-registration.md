---
card: spring-data
gi: 44
slug: custom-conversions-converter-registration
title: "Custom conversions (Converter registration)"
---

## 1. What it is

Custom conversions let you register a `Converter<S, T>` (the same interface used throughout this guide's Spring Framework section for type conversion generally) to control exactly how a specific Java type gets stored and read back — for JPA, this most commonly means an `AttributeConverter` (JPA's own, slightly different but conceptually identical converter interface), letting a rich Java type (a value object, an enum with custom serialization, a `Money` type) be persisted as a simple column value without the entity itself needing to know or care about that translation.

```java
@Converter(autoApply = true)
public class MoneyConverter implements AttributeConverter<Money, Long> {
    @Override public Long convertToDatabaseColumn(Money money) { return money.cents(); }
    @Override public Money convertToEntityAttribute(Long cents) { return Money.ofCents(cents); }
}
```

## 2. Why & when

A domain model often wants richer types than a database column naturally supports — a `Money` value object wrapping an amount and currency, an `EmailAddress` type with built-in validation, an enum that needs a specific string representation different from its Java name. Custom conversions let the entity class use these rich types directly as field types, while the actual database column stays a simple, standard type (a `BIGINT`, a `VARCHAR`) — the converter is where the translation between the two lives, in exactly one place, rather than scattered across every place the entity is constructed or read.

Reach for custom conversions specifically when:

- You have a value object (a small, immutable type wrapping one or more primitive values with business meaning — `Money`, `EmailAddress`, `PhoneNumber`) that you want entities to use directly as a field type, without flattening it into separate primitive columns.
- You need an enum to persist as something other than its default representation (JPA's default `ORDINAL`/`STRING` enum handling, or a completely custom string mapping) — a custom converter gives full control.
- You're integrating a third-party or legacy type that doesn't map naturally to any JPA-supported column type, and need to define exactly how it translates to and from a database-representable value.

## 3. Core concept

```
 @Converter(autoApply = true)          -- applies to EVERY field of this Java type,
                                            across every entity, automatically
 public class MoneyConverter implements AttributeConverter<Money, Long> {

     Long convertToDatabaseColumn(Money attribute)
       -- Java object --> database column value (called on WRITE)

     Money convertToEntityAttribute(Long dbData)
       -- database column value --> Java object (called on READ)
 }

 @Entity
 public class Order {
     private Money total;   -- a RICH Java type, stored as a plain BIGINT column
     -- MoneyConverter handles the translation TRANSPARENTLY, both directions
 }

 Without autoApply=true, a converter must be explicitly referenced per field:
   @Convert(converter = MoneyConverter.class)
   private Money total;
```

The converter is invoked automatically by Hibernate at exactly the point a field of the converted type is written to or read from the database — application code never calls it directly.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="AttributeConverter translates between a rich Java field type and a simple database column type, in both directions">
  <rect x="10" y="20" width="190" height="55" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="105" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Money (Java field)</text>
  <text x="105" y="58" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">rich value object</text>

  <rect x="230" y="20" width="200" height="55" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="330" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">MoneyConverter</text>
  <text x="330" y="58" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">convertToDatabaseColumn / ...EntityAttribute</text>

  <rect x="460" y="20" width="170" height="55" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="545" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">BIGINT column</text>
  <text x="545" y="58" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">simple stored value</text>

  <line x1="200" y1="40" x2="225" y2="40" stroke="#8b949e" stroke-width="2" marker-end="url(#a)"/>
  <line x1="430" y1="40" x2="455" y2="40" stroke="#8b949e" stroke-width="2" marker-end="url(#a)"/>
  <line x1="455" y1="58" x2="430" y2="58" stroke="#8b949e" stroke-width="2" marker-end="url(#a)"/>
  <line x1="225" y1="58" x2="200" y2="58" stroke="#8b949e" stroke-width="2" marker-end="url(#a)"/>
  <defs><marker id="a" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

The converter sits at the boundary, translating both directions, invisible to the rest of the entity's code.

## 5. Runnable example

The scenario: an `Order` entity using a `Money` value object, evolving from a basic `AttributeConverter` making it persistable, to a custom enum converter with a non-default string representation, to confirming derived queries against a converted field's underlying database representation work correctly.

### Level 1 — Basic

Define a `Money` value object and an `AttributeConverter` storing it as a plain `long` (cents) column, then confirm round-tripping through save/reload preserves it correctly.

```java
import jakarta.persistence.AttributeConverter;
import jakarta.persistence.Converter;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.ConfigurableApplicationContext;
import org.springframework.data.jpa.repository.JpaRepository;

@SpringBootApplication
public class CustomConversionLevel1 {

    // An immutable value object -- NOT itself a JPA-recognized type.
    public record Money(long cents) {
        public static Money ofCents(long cents) { return new Money(cents); }
        public String format() { return String.format("$%.2f", cents / 100.0); }
    }

    @Converter(autoApply = true)
    public static class MoneyConverter implements AttributeConverter<Money, Long> {
        @Override
        public Long convertToDatabaseColumn(Money attribute) {
            return attribute == null ? null : attribute.cents();
        }
        @Override
        public Money convertToEntityAttribute(Long dbData) {
            return dbData == null ? null : Money.ofCents(dbData);
        }
    }

    @Entity
    public static class Order {
        @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
        private Long id;
        private Money total; // a RICH type, thanks to MoneyConverter with autoApply=true
        protected Order() {}
        public Order(Money total) { this.total = total; }
        public Money getTotal() { return total; }
    }

    public interface OrderRepository extends JpaRepository<Order, Long> {}

    public static void main(String[] args) {
        ConfigurableApplicationContext ctx = SpringApplication.run(CustomConversionLevel1.class,
            "--spring.datasource.url=jdbc:h2:mem:customconv1",
            "--spring.jpa.hibernate.ddl-auto=create-drop");

        OrderRepository repo = ctx.getBean(OrderRepository.class);
        Order saved = repo.save(new Order(Money.ofCents(4999))); // $49.99

        Order reloaded = repo.findById(saved.getId()).orElseThrow();
        System.out.println("reloaded total = " + reloaded.getTotal().format());

        if (reloaded.getTotal().cents() != 4999)
            throw new AssertionError("Expected the Money value to round-trip correctly through the converter");
        System.out.println("AttributeConverter transparently persisted a rich Money value object -- PASS");
        ctx.close();
    }
}
```

How to run: put `spring-boot-starter-data-jpa` and `com.h2database:h2` on the classpath, then `java CustomConversionLevel1.java` on JDK 17+.

`Order.total` is declared as `Money`, not a primitive — Hibernate has no built-in understanding of this type, but `MoneyConverter`, marked `@Converter(autoApply = true)`, is discovered and applied automatically to every `Money`-typed field across the application, translating to and from a plain `Long` (storing cents) at exactly the point of each database read/write. Application code — including `Order`'s own field declaration — never sees the underlying `Long` at all.

### Level 2 — Intermediate

Define a custom enum converter with a non-default string representation, showing full control over the exact stored value rather than relying on JPA's default `ORDINAL`/`STRING` enum handling.

```java
import jakarta.persistence.AttributeConverter;
import jakarta.persistence.Converter;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.ConfigurableApplicationContext;
import org.springframework.data.jpa.repository.JpaRepository;

@SpringBootApplication
public class CustomConversionLevel2 {

    public enum OrderStatus {
        PENDING, SHIPPED, DELIVERED, CANCELLED
    }

    // Stores a SHORT, non-obvious code instead of the enum's Java name --
    // e.g. for a legacy database schema that already uses single-letter codes.
    @Converter(autoApply = true)
    public static class OrderStatusConverter implements AttributeConverter<OrderStatus, String> {
        @Override
        public String convertToDatabaseColumn(OrderStatus attribute) {
            if (attribute == null) return null;
            return switch (attribute) {
                case PENDING -> "P";
                case SHIPPED -> "S";
                case DELIVERED -> "D";
                case CANCELLED -> "C";
            };
        }
        @Override
        public OrderStatus convertToEntityAttribute(String dbData) {
            if (dbData == null) return null;
            return switch (dbData) {
                case "P" -> OrderStatus.PENDING;
                case "S" -> OrderStatus.SHIPPED;
                case "D" -> OrderStatus.DELIVERED;
                case "C" -> OrderStatus.CANCELLED;
                default -> throw new IllegalArgumentException("Unknown status code: " + dbData);
            };
        }
    }

    @Entity
    public static class Order {
        @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
        private Long id;
        private OrderStatus status;
        protected Order() {}
        public Order(OrderStatus status) { this.status = status; }
        public OrderStatus getStatus() { return status; }
    }

    public interface OrderRepository extends JpaRepository<Order, Long> {}

    public static void main(String[] args) {
        ConfigurableApplicationContext ctx = SpringApplication.run(CustomConversionLevel2.class,
            "--spring.datasource.url=jdbc:h2:mem:customconv2",
            "--spring.jpa.hibernate.ddl-auto=create-drop");

        OrderRepository repo = ctx.getBean(OrderRepository.class);
        Order saved = repo.save(new Order(OrderStatus.SHIPPED));

        // Read the RAW stored column value directly, to confirm the custom short code was used.
        jakarta.persistence.EntityManager em = ctx.getBean(jakarta.persistence.EntityManagerFactory.class).createEntityManager();
        Object rawValue = em.createNativeQuery("select status from \"order\" where id = ?1")
            .setParameter(1, saved.getId()).getSingleResult();
        em.close();

        Order reloaded = repo.findById(saved.getId()).orElseThrow();

        System.out.println("raw stored column value = '" + rawValue + "'");
        System.out.println("reloaded enum value = " + reloaded.getStatus());

        if (!"S".equals(rawValue)) throw new AssertionError("Expected the raw stored value to be the custom short code 'S'");
        if (reloaded.getStatus() != OrderStatus.SHIPPED) throw new AssertionError("Expected the reloaded enum to be SHIPPED");

        System.out.println("Custom enum converter used a non-default short code, round-tripping correctly -- PASS");
        ctx.close();
    }
}
```

How to run: same classpath as Level 1, `java CustomConversionLevel2.java`.

`OrderStatusConverter` stores `OrderStatus.SHIPPED` as the single-character string `"S"`, not `"SHIPPED"` (JPA's default `@Enumerated(STRING)` behavior) or `1` (the default `ORDINAL` behavior) — reading the raw column value directly via a native query confirms the actual stored value is genuinely `"S"`, while `reloaded.getStatus()` confirms the round trip back to `OrderStatus.SHIPPED` works correctly through the same converter, applied automatically via `autoApply = true`.

### Level 3 — Advanced

Confirm a derived-query method filtering on a converted field correctly translates the Java-side value through the converter before querying — proving custom conversions integrate transparently with query derivation, not just basic save/load.

```java
import jakarta.persistence.AttributeConverter;
import jakarta.persistence.Converter;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.ConfigurableApplicationContext;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

@SpringBootApplication
public class CustomConversionLevel3 {

    public enum OrderStatus { PENDING, SHIPPED, DELIVERED, CANCELLED }

    @Converter(autoApply = true)
    public static class OrderStatusConverter implements AttributeConverter<OrderStatus, String> {
        @Override
        public String convertToDatabaseColumn(OrderStatus attribute) {
            if (attribute == null) return null;
            return switch (attribute) {
                case PENDING -> "P"; case SHIPPED -> "S"; case DELIVERED -> "D"; case CANCELLED -> "C";
            };
        }
        @Override
        public OrderStatus convertToEntityAttribute(String dbData) {
            if (dbData == null) return null;
            return switch (dbData) {
                case "P" -> OrderStatus.PENDING; case "S" -> OrderStatus.SHIPPED;
                case "D" -> OrderStatus.DELIVERED; case "C" -> OrderStatus.CANCELLED;
                default -> throw new IllegalArgumentException("Unknown status code: " + dbData);
            };
        }
    }

    @Entity
    public static class Order {
        @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
        private Long id;
        private OrderStatus status;
        protected Order() {}
        public Order(OrderStatus status) { this.status = status; }
        public OrderStatus getStatus() { return status; }
    }

    // A DERIVED query filtering on the converted field -- Java-side enum value in,
    // custom short code used in the actual generated SQL, transparently.
    public interface OrderRepository extends JpaRepository<Order, Long> {
        List<Order> findByStatus(OrderStatus status);
    }

    public static void main(String[] args) {
        ConfigurableApplicationContext ctx = SpringApplication.run(CustomConversionLevel3.class,
            "--spring.datasource.url=jdbc:h2:mem:customconv3",
            "--spring.jpa.hibernate.ddl-auto=create-drop");

        OrderRepository repo = ctx.getBean(OrderRepository.class);
        repo.save(new Order(OrderStatus.SHIPPED));
        repo.save(new Order(OrderStatus.SHIPPED));
        repo.save(new Order(OrderStatus.PENDING));

        // Called with the ENUM value -- the converter's translation is entirely transparent.
        List<Order> shipped = repo.findByStatus(OrderStatus.SHIPPED);
        System.out.println("orders with status=SHIPPED found = " + shipped.size());

        if (shipped.size() != 2) throw new AssertionError("Expected 2 shipped orders");
        if (!shipped.stream().allMatch(o -> o.getStatus() == OrderStatus.SHIPPED))
            throw new AssertionError("Expected every result to actually have status SHIPPED");

        System.out.println("Derived query correctly used the converter's short code under the hood -- PASS");
        ctx.close();
    }
}
```

How to run: same classpath as Level 1 and 2, `java CustomConversionLevel3.java`.

`findByStatus(OrderStatus status)` is called with `OrderStatus.SHIPPED` — an ordinary Java enum value — but the actual generated SQL, underneath, filters on the column's stored short-code representation (`WHERE status = 'S'`), since Hibernate applies `OrderStatusConverter`'s `convertToDatabaseColumn` to the query parameter before executing, exactly as it would for a save. This confirms custom conversions integrate fully and transparently with query derivation, not merely with basic save/load — a derived query author never needs to think about the converter at all.

## 6. Walkthrough

Trace `repo.findByStatus(OrderStatus.SHIPPED)` end-to-end.

1. **Query derivation at startup**: `PartTree` parses `findByStatus` into `WHERE status = ?1`, exactly as any other derived query — it has no special awareness that `status` is a converted field; from `PartTree`'s perspective, it's just a property.
2. **Call**: `repo.findByStatus(OrderStatus.SHIPPED)` is invoked with the Java enum value `OrderStatus.SHIPPED` as the argument.
3. **Parameter conversion**: before binding this parameter into the actual SQL query, Hibernate consults the registered `AttributeConverter` for the `status` field's type (`OrderStatus`) — finding `OrderStatusConverter`, it calls `convertToDatabaseColumn(OrderStatus.SHIPPED)`, which returns `"S"`.
4. **SQL execution**: the actual query sent to H2 is `SELECT * FROM "order" WHERE status = 'S'` — the converted, short-code value, not the Java enum's name.
5. **Matching rows found**: the two orders whose `status` column genuinely contains `'S'` (both saved as `OrderStatus.SHIPPED`) match.
6. **Result mapping**: each matching row is converted back into an `Order` entity — for the `status` column specifically, `convertToEntityAttribute("S")` is called, producing `OrderStatus.SHIPPED` again, populating the entity's field.
7. **Return value**: `List<Order>`, each with `status == OrderStatus.SHIPPED`, returned to the caller — who never saw, and never needed to know about, the `"S"` short code used anywhere in the underlying SQL.
8. **Verification**: the program checks both the count (2) and that every returned order genuinely has the expected status, confirming the full round trip — Java enum in, short code in the SQL, Java enum back out — worked correctly through query derivation.

```
 findByStatus(OrderStatus.SHIPPED)
        |
        v
 OrderStatusConverter.convertToDatabaseColumn(SHIPPED) --> "S"
        |
        v
 SQL: WHERE status = 'S'   (the converter's output, not the enum name)
        |
        v
 matching rows --> convertToEntityAttribute("S") --> OrderStatus.SHIPPED  (for each result)
        |
        v
 List<Order>  -- all with status == OrderStatus.SHIPPED
```

## 7. Gotchas & takeaways

> **Gotcha:** `@Converter(autoApply = true)` applies globally to *every* field of the converted Java type across the entire application — if two different entities both have an `OrderStatus`-typed field but need genuinely different stored representations for some reason, `autoApply` can't express that; one of them would need `autoApply = false` on the converter plus an explicit `@Convert(converter = ...)` annotation on the specific field that needs it, while the other field falls back to JPA's default enum handling or a different, explicitly-attached converter.

- `AttributeConverter<X, Y>` translates between a rich Java type `X` (used directly as an entity field type) and a simple, database-representable type `Y` — both directions (`convertToDatabaseColumn`, `convertToEntityAttribute`) are implemented in exactly one place.
- `@Converter(autoApply = true)` applies the converter automatically to every field of the matching Java type across the entire application, with no per-field annotation needed — the more common choice unless a type genuinely needs different handling in different places.
- Custom conversions integrate transparently with every other Spring Data mechanism covered in this section — derived queries, `@Query`, and projections all correctly apply the converter's translation without any special handling required from the developer writing those queries.
- Reach for a custom converter whenever an entity wants to use a rich, meaningful Java type (a value object, a precisely-controlled enum representation) as a field, while keeping the underlying database schema simple — the converter is where that translation lives, once, rather than being duplicated across every place the entity is constructed or inspected.
