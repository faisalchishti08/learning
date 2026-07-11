---
card: spring-data
gi: 79
slug: id-table-column-mappedcollection
title: "@Id, @Table, @Column, @MappedCollection"
---

## 1. What it is

The previous card explained Spring Data JDBC's *default* mapping conventions; this card covers the four annotations used to override those defaults explicitly: `@Id` marks the primary-key field, `@Table` overrides the table name, `@Column` overrides a single column's name, and `@MappedCollection` overrides both the foreign-key column name and (for ordered lists) the key/index column for a child collection.

```java
@Table("customer_orders")
class Order {
    @Id Long id;
    @Column("order_status") String status;
    @MappedCollection(idColumn = "order_id", keyColumn = "item_index")
    List<LineItem> lineItems;
}
```

## 2. Why & when

The mapping-convention card explained what names get inferred by default; these four annotations are how you correct that inference when it doesn't match an existing schema, without switching naming strategies globally. They're the fine-grained, per-field/per-class equivalent of the naming-strategies card's application-wide override.

Reach for these annotations specifically when:

- The default convention produces a name that doesn't match an existing table/column (e.g., a legacy table named `customer_orders` rather than the convention-derived `order`) — `@Table`/`@Column` fix individual mismatches without a custom naming strategy.
- A child collection's foreign-key column has a different name than the parent entity's default table name would imply, or the collection is a `List` (not a `Set`) and needs an explicit index column to preserve element order — `@MappedCollection`'s `idColumn`/`keyColumn` attributes handle both.
- `@Id` is required whenever the primary-key field isn't literally named `id` (or even when it is, it's good practice to be explicit) — Spring Data JDBC needs to know unambiguously which field identifies the aggregate root for insert-vs-update decisions.

## 3. Core concept

```
 @Table("customer_orders")                       overrides default table name "order" -> "customer_orders"
 class Order {
     @Id Long id;                                  marks the primary key explicitly
     @Column("order_status") String status;        overrides default column name "status" -> "order_status"
     @MappedCollection(idColumn = "order_id",       overrides default FK column name "order" -> "order_id"
                        keyColumn = "item_index")   AND adds an explicit index column for List ordering
     List<LineItem> lineItems;
 }
```

Each annotation targets one specific naming decision the default convention would otherwise make automatically — `@Table` for the class, `@Column` for a field, `@MappedCollection` for a child collection's linkage.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.v3.org/2000/svg" role="img" aria-label="Four annotations each override one specific default naming decision in the entity-to-table mapping">
  <rect x="20" y="15" width="600" height="45" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="320" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="monospace">@Table("customer_orders") class Order { @Id Long id; @Column("order_status") String status; ... }</text>

  <rect x="20" y="80" width="180" height="45" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.3"/>
  <text x="110" y="107" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">@Table -&gt; table name</text>

  <rect x="220" y="80" width="180" height="45" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.3"/>
  <text x="310" y="107" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">@Id -&gt; primary key field</text>

  <rect x="420" y="80" width="200" height="45" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.3"/>
  <text x="520" y="107" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">@Column -&gt; one column's name</text>

  <rect x="220" y="140" width="280" height="45" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.3"/>
  <text x="360" y="160" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">@MappedCollection -&gt; FK column</text>
  <text x="360" y="175" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">+ optional index/key column</text>
</svg>

Each annotation is scoped to exactly one naming decision, letting you override just the mismatched piece without touching everything else.

## 5. Runnable example

The scenario: mapping an order onto a legacy schema with different names than the defaults, evolving from applying `@Table`/`@Id`/`@Column` individually, to adding `@MappedCollection` for a child collection's foreign key, to preserving list order with an explicit key column.

### Level 1 — Basic

Model `@Table`, `@Id`, and `@Column` overrides directly, comparing the default-convention name against the annotated override for each.

```java
import java.util.*;

// Simulated annotation metadata, since this is a single-file example with no real annotation processing.
record TableOverride(String defaultName, String overrideName) {
    String resolved() { return overrideName != null ? overrideName : defaultName; }
}

public class MappedLevel1 {
    public static void main(String[] args) {
        // @Table("customer_orders") class Order { ... }
        TableOverride tableMapping = new TableOverride("order", "customer_orders");
        System.out.println("Table: default=\"" + tableMapping.defaultName() + "\", resolved=\"" + tableMapping.resolved() + "\"");

        // @Id Long id;  -- explicitly marks the primary key (matters most when the field ISN'T named "id")
        TableOverride idMapping = new TableOverride("order_pk", "id"); // e.g., legacy PK column was "order_pk"... but @Id just marks WHICH field is the key
        System.out.println("Primary key field marked explicitly via @Id (field name unaffected by this annotation itself)");

        // @Column("order_status") String status;
        TableOverride statusMapping = new TableOverride("status", "order_status");
        System.out.println("Column: default=\"" + statusMapping.defaultName() + "\", resolved=\"" + statusMapping.resolved() + "\"");
    }
}
```

How to run: `java MappedLevel1.java`

`@Table("customer_orders")` and `@Column("order_status")` each override exactly one default-convention name — the resolved table becomes `customer_orders` instead of the convention-derived `order`, and the resolved column becomes `order_status` instead of `status`, while every other field on the entity keeps using the default convention untouched.

### Level 2 — Intermediate

Add `@MappedCollection`'s `idColumn` override for a child collection's foreign key, showing the default versus the explicit override.

```java
import java.util.*;

record TableOverride(String defaultName, String overrideName) {
    String resolved() { return overrideName != null ? overrideName : defaultName; }
}

public class MappedLevel2 {
    public static void main(String[] args) {
        String parentTable = "customer_orders"; // from @Table override

        // Default convention: child table's FK column would be named after the parent's DEFAULT table name ("order"),
        // but the actual legacy schema names it "order_ref" instead.
        TableOverride fkMapping = new TableOverride("order", "order_ref");

        System.out.println("Parent table: " + parentTable);
        System.out.println("Child (line_item) FK column: default=\"" + fkMapping.defaultName()
            + "\", resolved (via @MappedCollection(idColumn=\"order_ref\"))=\"" + fkMapping.resolved() + "\"");

        // Simulate the actual INSERT this produces for a line item belonging to order id=1.
        System.out.println("INSERT INTO line_item (" + fkMapping.resolved() + ", description) VALUES (1, 'Widget');");
    }
}
```

How to run: `java MappedLevel2.java`

Without `@MappedCollection(idColumn = "order_ref")`, Spring Data JDBC would expect the child table's foreign-key column to be named `order` (derived from the parent's *default* table name convention) — but since the actual legacy table calls it `order_ref`, the explicit override is required for the generated `INSERT`/`SELECT` statements to target the right column.

### Level 3 — Advanced

Add `keyColumn` for preserving `List` element order — without it, a `List<LineItem>` has no guaranteed ordering when reloaded from the database, since SQL tables have no inherent row order.

```java
import java.util.*;

class LineItem { String description; LineItem(String d) { description = d; } }

public class MappedLevel3 {
    // Simulates: @MappedCollection(idColumn = "order_ref", keyColumn = "item_index") List<LineItem> lineItems;
    static void insertLineItemsWithKeyColumn(long orderId, List<LineItem> items) {
        for (int index = 0; index < items.size(); index++) {
            LineItem item = items.get(index);
            System.out.println("INSERT INTO line_item (order_ref, item_index, description) VALUES ("
                + orderId + ", " + index + ", '" + item.description + "');");
        }
    }

    // Without keyColumn: order is NOT guaranteed to be preserved when re-read from the database.
    static void insertLineItemsWithoutKeyColumn(long orderId, List<LineItem> items) {
        for (LineItem item : items) {
            System.out.println("INSERT INTO line_item (order_ref, description) VALUES ("
                + orderId + ", '" + item.description + "');  -- no index column, order not guaranteed on reload");
        }
    }

    public static void main(String[] args) {
        List<LineItem> items = List.of(new LineItem("Widget"), new LineItem("Gadget"), new LineItem("Sprocket"));

        System.out.println("WITHOUT keyColumn (order not preserved on reload):");
        insertLineItemsWithoutKeyColumn(1, items);

        System.out.println();
        System.out.println("WITH keyColumn (order preserved via explicit item_index):");
        insertLineItemsWithKeyColumn(1, items);
    }
}
```

How to run: `java MappedLevel3.java`

The `keyColumn`-based version explicitly stores each `LineItem`'s position (`0`, `1`, `2`) in an `item_index` column — when Spring Data JDBC reloads this `List<LineItem>` later, it can `ORDER BY item_index` to reconstruct the exact original order. Without `keyColumn`, the rows have no ordering column at all, so the list's order after a reload depends entirely on whatever order the database happens to return rows in — not guaranteed to match the order the items were originally inserted.

## 6. Walkthrough

Execution starts in `main` for Level 3. First, `items` is built as an ordered list: `["Widget", "Gadget", "Sprocket"]`, in that specific order.

`insertLineItemsWithoutKeyColumn(1, items)` runs first: it loops over `items` in order and prints an `INSERT` for each, but none of the printed statements include any column recording *which position* each item held — a `SELECT * FROM line_item WHERE order_ref = 1` issued later has no column to `ORDER BY` that would reliably reconstruct `["Widget", "Gadget", "Sprocket"]` specifically, as opposed to any other ordering of the same three rows.

`insertLineItemsWithKeyColumn(1, items)` then runs: this time the loop uses an explicit `index` variable (via `for (int index = 0; index < items.size(); index++)`), incrementing from `0`. Each `INSERT` now includes `item_index` explicitly: `0` for `"Widget"`, `1` for `"Gadget"`, `2` for `"Sprocket"`. A later `SELECT * FROM line_item WHERE order_ref = 1 ORDER BY item_index` would deterministically reconstruct the original list order, regardless of the physical row order in storage.

```
items = ["Widget", "Gadget", "Sprocket"]  (List, order matters)

without keyColumn: INSERT (order_ref, description) x3   -- no ordering info stored
with keyColumn:     INSERT (order_ref, item_index, description) x3
                       item_index: 0="Widget", 1="Gadget", 2="Sprocket"
                       -> SELECT ... ORDER BY item_index reconstructs the exact original order
```

In a real Spring Data JDBC application, declaring `@MappedCollection(idColumn = "order_ref", keyColumn = "item_index") List<LineItem> lineItems` causes every `orderRepository.save(order)` call to populate both the `order_ref` foreign key and the `item_index` position for each line item, and every subsequent `orderRepository.findById(...)` to issue a `SELECT ... ORDER BY item_index` when reconstructing the `List<LineItem>` — guaranteeing the reloaded list matches the order it was saved in. Omitting `keyColumn` (fine for a `Set<LineItem>`, where order genuinely doesn't matter) on a `List` risks silently reordering the collection across a save/reload cycle.

## 7. Gotchas & takeaways

> Gotcha: using a `List<T>` for a child collection without a `keyColumn` doesn't cause an error — it silently works, but the reloaded order is not guaranteed to match what was saved; this is an easy mistake to miss until a subtle bug surfaces (e.g., line items appearing in the wrong sequence on an invoice) much later.

- `@Table`/`@Column` override the default table/column-name convention for a class or single field, respectively.
- `@Id` explicitly marks the primary-key field — required whenever it isn't literally named `id`, and good practice even when it is.
- `@MappedCollection(idColumn = ...)` overrides a child collection's foreign-key column name when it doesn't match the parent's default table-name convention.
- `@MappedCollection(..., keyColumn = ...)` adds an explicit position column, required to reliably preserve `List` ordering across a save/reload cycle — not needed for `Set`, where order is irrelevant.
