---
card: spring-data
gi: 83
slug: custom-conversions
title: "Custom conversions"
---

## 1. What it is

A custom conversion is a pair of `Converter<S, T>` beans (registered via `JdbcCustomConversions`) that tell Spring Data JDBC how to translate a Java field's type into a JDBC-compatible column type on the way to the database, and back again on the way out — needed whenever a field's type has no automatic mapping to a SQL column type.

```java
class MoneyToBigDecimalConverter implements Converter<Money, BigDecimal> {
    public BigDecimal convert(Money source) { return source.amount(); }
}
class BigDecimalToMoneyConverter implements Converter<BigDecimal, Money> {
    public Money convert(BigDecimal source) { return new Money(source, "USD"); }
}
// registered together as a pair via JdbcCustomConversions
```

## 2. Why & when

Every mapping-related card so far (mapping conventions, `@Embedded`, `@MappedCollection`) assumed each field's type already corresponds naturally to a column type (strings, numbers, booleans). Custom conversions are for the cases where it doesn't — a rich domain type like a custom `Money` class, an enum you want stored as a specific string representation, or a `java.time` type needing a non-default column representation.

Reach for a custom conversion specifically when:

- A field's Java type has no built-in mapping to any SQL column type — e.g., a value object wrapping a `BigDecimal` and a currency code, which needs to be decomposed (or serialized) into something a column can actually hold.
- The default mapping of a supported type doesn't match what you need — e.g., storing an enum as its ordinal integer instead of its name string, or storing a `LocalDate` in a nonstandard format.
- You're integrating with an existing schema where a column's stored representation doesn't match Spring Data JDBC's default assumption for that Java type at all.

## 3. Core concept

```
 Java-side:  class Order { Money total; }      class Money { BigDecimal amount; String currency; }
 DB-side:    orders.total  -- a single NUMERIC column (no room for a currency code)

 Writing (Java -> DB):  MoneyToBigDecimalConverter.convert(money) -> BigDecimal   -- amount only, currency ASSUMED
 Reading (DB -> Java):  BigDecimalToMoneyConverter.convert(bigDecimal) -> Money    -- reconstructs Money, currency defaulted

 Both converters registered together via:
   JdbcCustomConversions customConversions() {
       return new JdbcCustomConversions(List.of(new MoneyToBigDecimalConverter(), new BigDecimalToMoneyConverter()));
   }
```

Every custom conversion needs both directions registered as a pair — one for writing to the database, one for reading back.

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.v3.org/2000/svg" role="img" aria-label="A Money value object converts to a BigDecimal column on write, and back to Money on read, via a registered converter pair">
  <rect x="20" y="20" width="200" height="45" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="120" y="47" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">Money{amount,currency}</text>

  <rect x="440" y="20" width="180" height="45" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="530" y="47" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">NUMERIC column</text>

  <rect x="240" y="15" width="180" height="30" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.3"/>
  <text x="330" y="34" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">MoneyToBigDecimal</text>

  <rect x="240" y="60" width="180" height="30" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.3"/>
  <text x="330" y="79" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">BigDecimalToMoney</text>

  <line x1="220" y1="35" x2="435" y2="35" stroke="#8b949e" stroke-width="1.3" marker-end="url(#cc)"/>
  <line x1="435" y1="70" x2="220" y2="70" stroke="#8b949e" stroke-width="1.3" marker-end="url(#cc)"/>
  <defs><marker id="cc" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Writing flows through one converter to a database-friendly type; reading flows back through its paired counterpart to reconstruct the rich domain object.

## 5. Runnable example

The scenario: storing an order's total as a rich `Money` value object, evolving from the problem (no direct column type for it), to a registered converter pair handling both directions, to a second conversion for an enum stored as a custom string code rather than its default name.

### Level 1 — Basic

Show the problem directly: a `Money` field has no natural column representation, so naive persistence code has to hand-roll the conversion inline, ad hoc, every time it's needed.

```java
import java.math.BigDecimal;
import java.util.*;

class Money { BigDecimal amount; String currency; Money(BigDecimal amount, String currency) { this.amount = amount; this.currency = currency; } }
class Order { long id; Money total; Order(long id, Money total) { this.id = id; this.total = total; } }

public class ConversionLevel1 {
    public static void main(String[] args) {
        Order order = new Order(1, new Money(new BigDecimal("99.99"), "USD"));

        // Without a registered converter, this ad hoc conversion has to be repeated everywhere Money is persisted.
        BigDecimal columnValue = order.total.amount; // currency is simply DROPPED -- no column for it
        System.out.println("Column value written: " + columnValue + " (currency '" + order.total.currency + "' is LOST)");

        // Reading back: reconstructing Money requires guessing/hardcoding the currency, since it wasn't stored.
        Money reconstructed = new Money(columnValue, "USD"); // hardcoded guess
        System.out.println("Reconstructed: " + reconstructed.amount + " " + reconstructed.currency);
    }
}
```

How to run: `java ConversionLevel1.java`

The currency is silently dropped when writing (`columnValue` is just the `BigDecimal` amount), and reconstructing `Money` on read requires hardcoding a currency guess — this ad hoc, scattered conversion logic is exactly what a registered `Converter` pair centralizes and makes consistent.

### Level 2 — Intermediate

Introduce a proper converter pair, applied consistently through a small persistence layer, matching `JdbcCustomConversions`.

```java
import java.math.BigDecimal;
import java.util.*;

class Money { BigDecimal amount; String currency; Money(BigDecimal amount, String currency) { this.amount = amount; this.currency = currency; }
    public String toString() { return amount + " " + currency; } }

// Converter<Money, BigDecimal>
interface ToColumnConverter<S, T> { T convert(S source); }
// Converter<BigDecimal, Money>
interface FromColumnConverter<S, T> { T convert(S source); }

class MoneyToBigDecimalConverter implements ToColumnConverter<Money, BigDecimal> {
    public BigDecimal convert(Money source) { return source.amount; } // only the amount fits in the column
}
class BigDecimalToMoneyConverter implements FromColumnConverter<BigDecimal, Money> {
    public Money convert(BigDecimal source) { return new Money(source, "USD"); } // fixed default currency, by design
}

class Order { long id; Money total; Order(long id, Money total) { this.id = id; this.total = total; } }

// Stands in for the persistence layer consistently applying the registered converter pair.
class OrderRepository {
    private final Map<Long, BigDecimal> columnStorage = new HashMap<>(); // simulates the actual DB column
    private final MoneyToBigDecimalConverter toColumn = new MoneyToBigDecimalConverter();
    private final BigDecimalToMoneyConverter fromColumn = new BigDecimalToMoneyConverter();

    void save(Order order) {
        columnStorage.put(order.id, toColumn.convert(order.total)); // ALWAYS goes through the registered converter
    }
    Order findById(long id) {
        return new Order(id, fromColumn.convert(columnStorage.get(id))); // ALWAYS goes through the paired converter
    }
}

public class ConversionLevel2 {
    public static void main(String[] args) {
        OrderRepository repo = new OrderRepository();
        repo.save(new Order(1, new Money(new BigDecimal("99.99"), "USD")));

        Order found = repo.findById(1L);
        System.out.println("Reloaded total: " + found.total);
    }
}
```

How to run: `java ConversionLevel2.java`

`OrderRepository.save`/`findById` never manually pull `.amount` or construct a `Money` inline — every conversion goes through the same registered `toColumn`/`fromColumn` converter pair, guaranteeing consistent behavior everywhere `Money` is persisted, instead of the scattered ad hoc logic from Level 1.

### Level 3 — Advanced

Add a second, independent conversion for an enum stored as a custom short code (not its default name), showing that multiple converter pairs coexist and each handles its own type entirely independently.

```java
import java.math.BigDecimal;
import java.util.*;

class Money { BigDecimal amount; String currency; Money(BigDecimal amount, String currency) { this.amount = amount; this.currency = currency; }
    public String toString() { return amount + " " + currency; } }

enum OrderStatus { PENDING, SHIPPED, CANCELLED }

class MoneyToBigDecimalConverter { BigDecimal convert(Money m) { return m.amount; } }
class BigDecimalToMoneyConverter { Money convert(BigDecimal b) { return new Money(b, "USD"); } }

// A SEPARATE converter pair for an entirely different type: OrderStatus <-> a short DB code, not its enum name.
class OrderStatusToCodeConverter {
    String convert(OrderStatus status) {
        return switch (status) { case PENDING -> "P"; case SHIPPED -> "S"; case CANCELLED -> "C"; };
    }
}
class CodeToOrderStatusConverter {
    OrderStatus convert(String code) {
        return switch (code) { case "P" -> OrderStatus.PENDING; case "S" -> OrderStatus.SHIPPED; case "C" -> OrderStatus.CANCELLED;
            default -> throw new IllegalArgumentException("Unknown status code: " + code); };
    }
}

class Order { long id; Money total; OrderStatus status; Order(long id, Money total, OrderStatus status) { this.id = id; this.total = total; this.status = status; } }

class OrderRepository {
    record Row(BigDecimal total, String statusCode) {}
    private final Map<Long, Row> columnStorage = new HashMap<>();
    private final MoneyToBigDecimalConverter moneyOut = new MoneyToBigDecimalConverter();
    private final BigDecimalToMoneyConverter moneyIn = new BigDecimalToMoneyConverter();
    private final OrderStatusToCodeConverter statusOut = new OrderStatusToCodeConverter();
    private final CodeToOrderStatusConverter statusIn = new CodeToOrderStatusConverter();

    void save(Order order) {
        Row row = new Row(moneyOut.convert(order.total), statusOut.convert(order.status));
        System.out.println("  INSERT/UPDATE orders SET total=" + row.total() + ", status='" + row.statusCode() + "'");
        columnStorage.put(order.id, row);
    }

    Order findById(long id) {
        Row row = columnStorage.get(id);
        return new Order(id, moneyIn.convert(row.total()), statusIn.convert(row.statusCode()));
    }
}

public class ConversionLevel3 {
    public static void main(String[] args) {
        OrderRepository repo = new OrderRepository();
        repo.save(new Order(1, new Money(new BigDecimal("149.50"), "USD"), OrderStatus.SHIPPED));

        Order found = repo.findById(1L);
        System.out.println("Reloaded: total=" + found.total + ", status=" + found.status);
    }
}
```

How to run: `java ConversionLevel3.java`

`Money`/`BigDecimal` and `OrderStatus`/`String` are converted by two entirely independent, unrelated converter pairs — each handles exactly one type mapping, and both are applied together (but separately) inside `save`/`findById`. The printed SQL shows `status='S'` (the short code), not `"SHIPPED"` — confirming the custom enum-to-code conversion took effect — while `found.status` correctly prints back as `SHIPPED` after round-tripping through both converters.

## 6. Walkthrough

Execution starts in `main` for Level 3. First, `repo.save(new Order(1, new Money(149.50, "USD"), OrderStatus.SHIPPED))` runs. Inside `save`, `moneyOut.convert(order.total)` extracts just the `BigDecimal` amount (`149.50`) from the `Money` object, and independently, `statusOut.convert(order.status)` maps `OrderStatus.SHIPPED` to the string `"S"` via the `switch` expression. Both converted values are bundled into a `Row` and printed as the simulated `INSERT`/`UPDATE` statement — showing `total=149.50, status='S'`, confirming neither the currency nor the enum's full name ever reaches the "database."

Next, `repo.findById(1L)` runs. It retrieves the stored `Row` (`total=149.50, statusCode="S"`), then applies the reverse converters: `moneyIn.convert(149.50)` reconstructs a `Money` object with the hardcoded default currency `"USD"`, and `statusIn.convert("S")` maps the code back to `OrderStatus.SHIPPED` via its own `switch` expression. Both reconstructed values are combined into a new `Order` object and returned.

The final printed line, "Reloaded: total=149.50 USD, status=SHIPPED", confirms both independent round-trips succeeded — `Money` and `OrderStatus` each went through their own converter pair, and neither pair had any awareness of or dependency on the other.

```
save(Order(total=Money(149.50,USD), status=SHIPPED)):
   moneyOut.convert(Money)   -> BigDecimal(149.50)
   statusOut.convert(SHIPPED) -> "S"
   -> Row(149.50, "S") stored

findById(1):
   Row(149.50, "S") retrieved
   moneyIn.convert(149.50)  -> Money(149.50, "USD")   (currency defaulted, not stored)
   statusIn.convert("S")    -> OrderStatus.SHIPPED
   -> Order(total=149.50 USD, status=SHIPPED)
```

In a real Spring Data JDBC application, both converter pairs would be registered together in one `JdbcCustomConversions` bean: `new JdbcCustomConversions(List.of(new MoneyToBigDecimalConverter(), new BigDecimalToMoneyConverter(), new OrderStatusToCodeConverter(), new CodeToOrderStatusConverter()))`. From that point on, every `orderRepository.save(order)`/`findById(...)` call automatically applies the correct converter for each field's type, transparently to application code — the repository interface's method signatures never change; only what happens to each field's value on the way to and from the database differs.

## 7. Gotchas & takeaways

> Gotcha: registering only one direction of a converter pair (e.g., `MoneyToBigDecimalConverter` but forgetting `BigDecimalToMoneyConverter`) lets `save()` work fine but causes `findById()`/query methods to fail at runtime with a "no converter found" error — the two directions must always be registered together.

- A custom conversion is always a *pair* of converters: one for writing the Java type to a column-compatible type, one for reading it back.
- Reach for custom conversions when a field's type has no natural column mapping, or when the default mapping for a supported type doesn't match what's needed (like an enum stored as a custom code instead of its name).
- Multiple converter pairs coexist independently — each handles exactly one type mapping, with no interaction between them.
- Centralizing conversion logic in registered converters (rather than scattering ad hoc conversion code through repository methods) guarantees consistent behavior everywhere that type is persisted.
