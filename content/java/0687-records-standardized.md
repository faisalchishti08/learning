---
card: java
gi: 687
slug: records-standardized
title: Records — standardized
---

## 1. What it is

**Records**, previewed in Java 14 and again in Java 15, became a **standard, permanent language feature** in **Java 16** (JEP 395). No syntax changed from the second preview — `record Point(int x, int y) {}` still generates private final fields, accessors (`x()`, `y()`), a canonical constructor, and value-based `equals`/`hashCode`/`toString` — but from Java 16 onward, none of it requires `--enable-preview`. Records are now a fully committed part of the language, safe to depend on in production code and libraries without any preview-flag caveat.

## 2. Why & when

Two preview rounds (Java 14 and 15) gave the JDK team real-world feedback to refine subtler behavior — local records, interactions with annotations, and how records relate to sealed types — before locking the final design in permanently. Standardization matters practically: preview features carry a risk that details could still change release to release, so cautious teams and library maintainers often wait for a feature to become standard before adopting it broadly, especially in published APIs where a preview-era behavior change could break consumers. From Java 16 onward, that caution is no longer necessary for records — reach for them, without reservation, anywhere you're modeling a simple, immutable aggregate of values: a `Point`, a `Range`, a DTO, a `Map` key, or a variant in a `sealed` hierarchy.

## 3. Core concept

```java
// Java 14: record (preview) — needs --enable-preview --release 14
// Java 15: record (2nd preview) — needs --enable-preview --release 15
// Java 16 onward: standard language feature, no preview flag at all
record Point(int x, int y) {}

public class Demo {
    public static void main(String[] args) {
        Point p = new Point(3, 4);
        System.out.println(p);              // Point[x=3, y=4]
        System.out.println(p.x() + p.y());   // 7
    }
}
```

The exact same declaration that required special compiler flags in Java 14 and 15 now compiles and runs with a plain `javac`/`java` invocation.

## 4. Diagram

<svg viewBox="0 0 620 160" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Records timeline: preview in Java 14, second preview in Java 15, standardized as permanent language syntax in Java 16">
  <line x1="40" y1="80" x2="580" y2="80" stroke="#8b949e" stroke-width="2"/>

  <circle cx="100" cy="80" r="8" fill="#f0883e"/>
  <text x="100" y="55" fill="#f0883e" font-size="11" text-anchor="middle" font-family="sans-serif">Java 14</text>
  <text x="100" y="105" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">preview</text>

  <circle cx="340" cy="80" r="8" fill="#f0883e"/>
  <text x="340" y="55" fill="#f0883e" font-size="11" text-anchor="middle" font-family="sans-serif">Java 15</text>
  <text x="340" y="105" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">2nd preview</text>

  <circle cx="520" cy="80" r="8" fill="#6db33f"/>
  <text x="520" y="55" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">Java 16</text>
  <text x="520" y="105" fill="#3fb950" font-size="9" text-anchor="middle" font-family="sans-serif">standard, no flag needed</text>
</svg>

Two preview rounds validated the design before it became a permanent, always-available part of the language.

## 5. Runnable example

Scenario: an inventory `Item` record — first a plain standard record, then adding validation via a compact constructor and a derived method, then combining it with a sealed hierarchy of "stock event" records to model a small append-only event log, all compiled with no preview flags at all.

### Level 1 — Basic

```java
// File: ItemBasic.java
public class ItemBasic {
    record Item(String sku, double price) {}

    public static void main(String[] args) {
        Item item = new Item("SKU-001", 19.99);
        System.out.println(item);
        System.out.println("SKU: " + item.sku() + ", price: " + item.price());
    }
}
```

**How to run:** `java ItemBasic.java` (no preview flags needed, JDK 16+)

Expected output:
```
Item[sku=SKU-001, price=19.99]
SKU: SKU-001, price: 19.99
```

### Level 2 — Intermediate

```java
// File: ItemValidated.java
public class ItemValidated {
    record Item(String sku, double price, int quantity) {
        Item {
            if (price < 0) throw new IllegalArgumentException("price cannot be negative");
            if (quantity < 0) throw new IllegalArgumentException("quantity cannot be negative");
        }

        double totalValue() {
            return price * quantity;
        }
    }

    public static void main(String[] args) {
        Item item = new Item("SKU-001", 19.99, 5);
        System.out.printf("Total value of %s: $%.2f%n", item.sku(), item.totalValue());

        try {
            new Item("SKU-002", -5.0, 3);
        } catch (IllegalArgumentException e) {
            System.out.println("Rejected: " + e.getMessage());
        }
    }
}
```

**How to run:** `java ItemValidated.java`

Expected output:
```
Total value of SKU-001: $99.95
Rejected: price cannot be negative
```

### Level 3 — Advanced

```java
// File: StockEventLog.java
import java.util.ArrayList;
import java.util.List;

public class StockEventLog {
    sealed interface StockEvent permits Received, Sold, Adjusted {}
    record Received(String sku, int quantity) implements StockEvent {}
    record Sold(String sku, int quantity) implements StockEvent {}
    record Adjusted(String sku, int delta, String reason) implements StockEvent {}

    static int applyEvent(int currentQuantity, StockEvent event) {
        if (event instanceof Received r) return currentQuantity + r.quantity();
        if (event instanceof Sold s) return currentQuantity - s.quantity();
        if (event instanceof Adjusted a) return currentQuantity + a.delta();
        throw new IllegalStateException("unreachable: sealed to Received, Sold, Adjusted");
    }

    public static void main(String[] args) {
        List<StockEvent> events = new ArrayList<>();
        events.add(new Received("SKU-001", 100));
        events.add(new Sold("SKU-001", 30));
        events.add(new Adjusted("SKU-001", -2, "damaged in transit"));
        events.add(new Sold("SKU-001", 10));

        int quantity = 0;
        for (StockEvent event : events) {
            quantity = applyEvent(quantity, event);
            System.out.println(event + " -> running quantity: " + quantity);
        }
    }
}
```

**How to run:** `java StockEventLog.java`

Expected output:
```
Received[sku=SKU-001, quantity=100] -> running quantity: 100
Sold[sku=SKU-001, quantity=30] -> running quantity: 70
Adjusted[sku=SKU-001, delta=-2, reason=damaged in transit] -> running quantity: 68
Sold[sku=SKU-001, quantity=10] -> running quantity: 58
```

Level 3 combines standardized records with a [sealed interface](0678-sealed-classes-preview.md) (itself still in its second preview during Java 16 — see the next tutorial) to model an append-only event log: each `StockEvent` variant is a compact, immutable record, and `applyEvent` folds each event into a running `quantity`, exactly the kind of small, closed-set data modeling records and sealed types are built to support together.

## 6. Walkthrough

1. `main` builds a `List<StockEvent>` and appends four events in order: a `Received` of 100 units, a `Sold` of 30, an `Adjusted` of −2 (damage), and a final `Sold` of 10.
2. The loop iterates `events` in insertion order, calling `applyEvent(quantity, event)` for each and immediately reassigning `quantity` to its return value — this threading of state through successive calls is what makes the log "append-only but foldable" into a current running total.
3. Inside `applyEvent`, an `instanceof` chain (pattern-matching `instanceof`, standardized the same release — see [Pattern matching for instanceof — standardized](0688-pattern-matching-for-instanceof-standardized.md)) checks the event's concrete record type and extracts its fields directly via the record's generated accessors (`r.quantity()`, `s.quantity()`, `a.delta()`).
4. For the first event, `currentQuantity` starts at `0` and `Received("SKU-001", 100)` adds its `quantity()` (100), producing `100`.
5. For the second event, `Sold("SKU-001", 30)` subtracts its `quantity()` (30) from the running total, producing `70`.
6. For the third event, `Adjusted("SKU-001", -2, "damaged in transit")` adds its `delta()` (`-2`, already negative) to the running total, producing `68` — the `reason` field isn't used in the arithmetic but is preserved in the record and printed via its auto-generated `toString()`.
7. For the fourth event, another `Sold` subtracts `10`, producing the final `58`.
8. After each `applyEvent` call, `main` prints the event's default `toString()` representation (e.g. `Sold[sku=SKU-001, quantity=10]`) alongside the updated running quantity, giving a readable trace of the entire event log's effect step by step.

```
quantity=0
  + Received(100)  -> 100
  - Sold(30)       -> 70
  + Adjusted(-2)   -> 68
  - Sold(10)       -> 58
```

## 7. Gotchas & takeaways

> Standardization in Java 16 changed **nothing about records' runtime behavior or syntax** compared to the Java 15 second preview — the only difference is that `--enable-preview` is no longer required. Code written against the Java 15 preview should compile unchanged on Java 16+ once the preview flags are simply removed.

- Records remain implicitly `final` and cannot extend another class, though they can implement interfaces — this is unchanged from the preview era.
- The compact canonical constructor (`Item { ... }`, no repeated parameter list) remains the idiomatic place for validation logic, running before the implicit field assignments.
- Records pair especially well with `sealed` hierarchies (see [Sealed classes (2nd preview)](0689-sealed-classes-2nd-preview.md)) to model closed sets of immutable data variants — exactly the pattern `StockEvent` demonstrates here.
- Local records (declared inside a method body) remain supported, unchanged from their Java 15 second-preview refinement.
- Because records generate `equals`/`hashCode` from all components, records containing mutable fields (arrays, mutable collections) can still have their apparent equality shift if that mutable state changes later — records give you concise immutable-style declarations, not automatic deep immutability of whatever types their components happen to be.
