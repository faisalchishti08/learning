---
card: spring-data
gi: 171
slug: custom-conversions
title: "Custom conversions"
---

## 1. What it is

Custom conversions in Spring Data Neo4j let you register a `GenericConverter` (or a `@ConvertWith` annotation) that controls exactly how a Java field is stored as a Neo4j property, and how it's read back — needed whenever the natural Java type isn't one Neo4j's driver understands natively. This closes out the Spring Data Neo4j section, and mirrors the custom conversion support seen for MongoDB and Cassandra earlier in this course.

```java
@Node
class Customer {
    @Id String id;

    @ConvertWith(converter = MoneyConverter.class)
    Money lifetimeSpend;
}
```

## 2. Why & when

Neo4j's property values are limited to a fixed set of primitive-ish types — strings, numbers, booleans, temporal types, and lists of those. A rich domain type like `Money` (an amount plus a currency) or a custom `enum` with non-trivial serialization has no native representation, and without help, Spring Data Neo4j doesn't know how to store or reconstruct it.

Reach for custom conversions when:

- A field's type isn't one of Neo4j's supported property types, and there's a natural encoding into one that is (a `Money` object into a string like `"49.99 USD"`).
- The default enum or date handling isn't the representation you want stored (e.g. storing an enum as its ordinal instead of its name, or vice versa).
- The same conversion logic is needed consistently across many entities, so it belongs in one registered converter rather than repeated field-by-field mapping code.

## 3. Core concept

```
 class Money { BigDecimal amount; String currency; }     -- not a Neo4j-native property type

 write path:   Money  --[MoneyConverter]-->  String "49.99 USD"  --> stored as node property
 read path:    String "49.99 USD"  --[MoneyConverter]-->  Money  --> reconstructed field value

 @ConvertWith(converter = MoneyConverter.class)
 Money lifetimeSpend;
```

A converter is a two-way function: one direction for writing (Java type to Neo4j-storable type) and one for reading (Neo4j-storable type back to the Java type) — the same round-trip shape as custom converters in the MongoDB and Cassandra sections.

## 4. Diagram

<svg viewBox="0 0 640 160" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A Money object converts to a stored string on write, and the string converts back to a Money object on read">
  <rect x="20" y="30" width="160" height="45" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="100" y="57" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Money(49.99, USD)</text>

  <line x1="180" y1="52" x2="260" y2="52" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#a7)"/>
  <text x="220" y="42" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">write</text>

  <rect x="270" y="30" width="160" height="45" rx="8" fill="#6db33f30" stroke="#6db33f" stroke-width="1.5"/>
  <text x="350" y="57" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="monospace">"49.99 USD"</text>

  <line x1="430" y1="65" x2="350" y2="105" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#a7)"/>
  <text x="420" y="95" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">read</text>

  <rect x="20" y="105" width="160" height="45" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="100" y="132" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Money(49.99, USD)</text>
  <line x1="270" y1="127" x2="190" y2="127" stroke="#8b949e" stroke-width="1" stroke-dasharray="3,2"/>

  <defs><marker id="a7" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker></defs>
</svg>

The converter round-trips: `Money` to a storable string on write, and the same string back to `Money` on read.

## 5. Runnable example

The scenario: persisting a customer's lifetime spend as a `Money` value object, evolving from a naive approach that stores raw fields and loses type safety, to a proper two-way `MoneyConverter`, to a converter registered across an entire `Neo4jConversions` bean so it applies consistently to every entity using `Money`, not just one.

### Level 1 — Basic

Show the naive baseline: flattening `Money` into two raw primitive fields on the entity itself, losing the value object entirely.

```java
import java.math.*;

public class CustomConversionsLevel1 {
    public static void main(String[] args) {
        Customer amara = new Customer("c1", "Amara");
        amara.lifetimeSpendAmount = new BigDecimal("49.99"); // Money's fields, flattened by hand
        amara.lifetimeSpendCurrency = "USD";

        System.out.println("Stored as: " + amara.lifetimeSpendAmount + " " + amara.lifetimeSpendCurrency);
        // No Money object anywhere -- every caller has to remember to keep these two fields in sync.
    }
}

class Customer {
    String id, name;
    BigDecimal lifetimeSpendAmount;
    String lifetimeSpendCurrency;
    Customer(String id, String name) { this.id = id; this.name = name; }
}
```

How to run: `java CustomConversionsLevel1.java`

Flattening `Money` into two separate fields on `Customer` works, but throws away the value object — every piece of code touching lifetime spend now has to juggle an amount and a currency separately, instead of one cohesive `Money` type.

### Level 2 — Intermediate

Introduce a proper `Money` value object and a two-way `MoneyConverter` that stores it as a single string property and reconstructs it on read.

```java
import java.math.*;
import java.util.*;

public class CustomConversionsLevel2 {
    public static void main(String[] args) {
        MoneyConverter converter = new MoneyConverter();
        Customer amara = new Customer("c1", "Amara", new Money(new BigDecimal("49.99"), "USD"));

        String storedValue = converter.write(amara.lifetimeSpend); // write path
        System.out.println("Stored property value: " + storedValue);

        Money reconstructed = converter.read(storedValue); // read path
        System.out.println("Reconstructed: " + reconstructed.amount + " " + reconstructed.currency);
    }
}

class Money {
    BigDecimal amount; String currency;
    Money(BigDecimal amount, String currency) { this.amount = amount; this.currency = currency; }
}

class Customer {
    String id, name; Money lifetimeSpend;
    Customer(String id, String name, Money lifetimeSpend) { this.id = id; this.name = name; this.lifetimeSpend = lifetimeSpend; }
}

// Stands in for a Spring Data Neo4j GenericConverter pair (Money -> String, String -> Money).
class MoneyConverter {
    String write(Money money) { return money.amount.toPlainString() + " " + money.currency; }
    Money read(String stored) {
        String[] parts = stored.split(" ");
        return new Money(new BigDecimal(parts[0]), parts[1]);
    }
}
```

How to run: `java CustomConversionsLevel2.java`

`write` turns `Money(49.99, USD)` into the single storable string `"49.99 USD"`; `read` parses that string back into an equivalent `Money` object — `Customer.lifetimeSpend` stays a proper `Money` value object throughout application code, and only the converter needs to know about the string encoding used at the storage layer.

### Level 3 — Advanced

Register the converter globally through a `Neo4jConversions` bean, so it applies automatically to *every* `Money`-typed field across every entity — not just one hand-wired call site — plus handle the malformed-data edge case a real converter must guard against.

```java
import java.math.*;
import java.util.*;

public class CustomConversionsLevel3 {
    public static void main(String[] args) {
        Neo4jConversions conversions = new Neo4jConversions();
        conversions.register(Money.class, new MoneyConverter());

        Customer amara = new Customer("c1", "Amara", new Money(new BigDecimal("49.99"), "USD"));
        Order order = new Order("o1", new Money(new BigDecimal("129.50"), "EUR"));

        // The SAME registered converter applies to both entities' Money fields automatically.
        System.out.println("Customer stored: " + conversions.write(amara.lifetimeSpend));
        System.out.println("Order stored: " + conversions.write(order.total));

        try {
            conversions.read(Money.class, "not-a-valid-money-string");
        } catch (IllegalArgumentException e) {
            System.out.println("Guarded against malformed data: " + e.getMessage());
        }
    }
}

class Money {
    BigDecimal amount; String currency;
    Money(BigDecimal amount, String currency) { this.amount = amount; this.currency = currency; }
}

class Customer {
    String id, name; Money lifetimeSpend;
    Customer(String id, String name, Money lifetimeSpend) { this.id = id; this.name = name; this.lifetimeSpend = lifetimeSpend; }
}

class Order {
    String id; Money total;
    Order(String id, Money total) { this.id = id; this.total = total; }
}

class MoneyConverter {
    String write(Money money) { return money.amount.toPlainString() + " " + money.currency; }
    Money read(String stored) {
        String[] parts = stored.split(" ");
        if (parts.length != 2) {
            throw new IllegalArgumentException("Expected '<amount> <currency>', got: " + stored);
        }
        return new Money(new BigDecimal(parts[0]), parts[1]);
    }
}

// Stands in for a Spring Data Neo4jConversions bean, holding converters keyed by the type they handle.
class Neo4jConversions {
    private final Map<Class<?>, MoneyConverter> converters = new HashMap<>();
    void register(Class<?> type, MoneyConverter converter) { converters.put(type, converter); }
    String write(Money money) { return converters.get(Money.class).write(money); }
    Money read(Class<?> type, String stored) { return converters.get(type).read(stored); }
}
```

How to run: `java CustomConversionsLevel3.java`

`Neo4jConversions` holds converters keyed by the Java type they handle — registering `MoneyConverter` once makes it apply to `Customer.lifetimeSpend` *and* `Order.total` automatically, since both are `Money`-typed fields, and `read` now validates its input, throwing a clear error on malformed stored data instead of an obscure `ArrayIndexOutOfBoundsException`.

## 6. Walkthrough

Execution starts in `main` for Level 3. A `MoneyConverter` is registered once against the `Money` type in a shared `Neo4jConversions` instance. Two entities, `Customer` and `Order`, each hold an independent `Money`-typed field, and both convert through the same registered converter without either entity needing its own conversion logic.

`conversions.write(amara.lifetimeSpend)` and `conversions.write(order.total)` both resolve to the *same* `MoneyConverter` instance internally, producing:

```
Customer stored: 49.99 USD
Order stored: 129.50 EUR
```

The final call deliberately feeds `"not-a-valid-money-string"` into `read`, which doesn't split into exactly two parts — `MoneyConverter.read` catches that explicitly and throws a descriptive `IllegalArgumentException` rather than letting a downstream `ArrayIndexOutOfBoundsException` or `NumberFormatException` leak out with a confusing message:

```
Guarded against malformed data: Expected '<amount> <currency>', got: not-a-valid-money-string
```

In a real Spring Data Neo4j application, this validation matters more than it might seem: the stored property value could have been written by an older version of the converter, edited directly in the Neo4j Browser, or corrupted by a manual Cypher `SET` statement — the read path is the last line of defense against bad data reaching application code as a half-built object.

## 7. Gotchas & takeaways

> Gotcha: a converter registered for `Money` applies to *every* `Money`-typed field across *every* entity — this is the point, but it also means changing the stored string format later is a breaking change for every entity using it, not a localized one; plan the storage format for a custom converter with some care up front.

> Gotcha: forgetting to register a converter for a custom value-object field doesn't fail loudly and immediately in all cases — depending on the type, Spring Data Neo4j may attempt (and fail) to map it as if it were a nested `@Node`, producing a confusing mapping exception far from the actual missing-converter root cause.

- Custom conversions are needed whenever a Java field's type has no native Neo4j property representation — a value object, a specially-encoded enum, or similar.
- A converter is two-way: one direction for writing (Java to storable), one for reading (storable back to Java) — both must agree on the same encoding.
- Registering a converter once, keyed by type, applies it consistently across every entity using that type — avoiding duplicated, potentially inconsistent, field-by-field conversion logic.
- A converter's read path should validate its input defensively, since stored data can outlive or predate the exact converter version that wrote it.
