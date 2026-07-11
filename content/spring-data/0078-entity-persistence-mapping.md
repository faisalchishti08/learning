---
card: spring-data
gi: 78
slug: entity-persistence-mapping
title: "Entity persistence & mapping"
---

## 1. What it is

Spring Data JDBC maps entities to tables using a much simpler algorithm than JPA's: by default, an entity's class name maps to a table (via the naming strategy from an earlier card), each constructor parameter or field maps to a column of the same name, and nested objects/collections map to separate tables linked by a foreign key back to the parent — all inferred by convention, with no annotation required for the common case.

```java
class Order {                    // maps to table "order" (or "orders", by naming strategy)
    @Id Long id;                  // maps to column "id"
    String status;                 // maps to column "status"
    List<LineItem> lineItems;      // maps to a SEPARATE "line_item" table, linked by an "order" FK column
}
```

## 2. Why & when

The aggregates philosophy card established the conceptual model; this card is about the concrete, convention-based algorithm that turns a plain Java class into actual tables and columns without annotations. Understanding this mapping algorithm matters because Spring Data JDBC has no schema-generation tool of its own (unlike Hibernate's `ddl-auto`) — you write the DDL yourself, so knowing exactly what table/column names and relationships the entity implies is essential to writing a schema that matches.

Reach for an explicit understanding of this mapping specifically when:

- You're writing the SQL schema (`CREATE TABLE`) by hand and need to know exactly what table and column names Spring Data JDBC will expect for a given entity.
- You have a `List<X>`/`Set<X>` field and need to know how the child table's foreign key back to the parent is named and populated — this is inferred, not something you write explicitly in the child entity.
- A save or query fails with a "column not found" or "table not found" error, and you need to reason through what name the mapping convention actually produced.

## 3. Core concept

```
 class Order {
     @Id Long id;
     String status;
     List<LineItem> lineItems;
 }
 class LineItem {
     String description;
     // NO explicit foreign key field needed here -- Spring Data JDBC manages it
 }

 Maps to:
   CREATE TABLE "order"     (id BIGINT PRIMARY KEY, status VARCHAR)
   CREATE TABLE line_item   (order BIGINT REFERENCES "order"(id), description VARCHAR)
                              ^^^^^ implicit FK column, named after the PARENT entity/table
```

A collection field on the parent produces a separate child table whose foreign-key column is named after the parent, entirely inferred — no explicit key field is declared on the child class itself.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.v3.org/2000/svg" role="img" aria-label="An Order entity with a List of LineItem maps to two tables linked by an implicit foreign key column">
  <rect x="30" y="20" width="220" height="70" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="140" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">table "order"</text>
  <text x="140" y="62" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="monospace">id (PK), status</text>
  <text x="140" y="78" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">from: class Order</text>

  <rect x="390" y="20" width="220" height="90" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="500" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">table "line_item"</text>
  <text x="500" y="62" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="monospace">order (FK), description</text>
  <text x="500" y="80" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">from: List&lt;LineItem&gt; lineItems</text>
  <text x="500" y="96" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">FK column implicitly named "order"</text>

  <line x1="250" y1="55" x2="385" y2="55" stroke="#8b949e" stroke-width="1.3" marker-end="url(#ep)"/>
  <text x="320" y="48" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">1-to-many</text>
  <defs><marker id="ep" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

A single Java class with a collection field implies two tables and one foreign-key relationship — all by convention, no explicit key field written.

## 5. Runnable example

The scenario: mapping an `Order`/`LineItem` aggregate onto tables, evolving from computing the default table/column names, to modeling the parent/child split with its implicit foreign key, to a full simulated schema generator that prints the DDL a real setup would require.

### Level 1 — Basic

Model the default table/column name inference for a simple flat entity (no nested collection yet).

```java
import java.util.*;

public class MappingLevel1 {
    // Simplified default naming: class/field names lowercased, camelCase -> snake_case (as in the naming-strategies card).
    static String toSnakeCase(String name) {
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < name.length(); i++) {
            char c = name.charAt(i);
            if (Character.isUpperCase(c)) { if (i > 0) sb.append('_'); sb.append(Character.toLowerCase(c)); }
            else sb.append(c);
        }
        return sb.toString();
    }

    record FieldMapping(String javaField, String columnName) {}

    public static void main(String[] args) {
        String className = "Order";
        String tableName = toSnakeCase(className);

        List<String> fields = List.of("id", "status", "totalAmount");
        List<FieldMapping> mappings = fields.stream()
            .map(f -> new FieldMapping(f, toSnakeCase(f)))
            .toList();

        System.out.println("class " + className + " -> table \"" + tableName + "\"");
        for (FieldMapping m : mappings) System.out.println("  " + m.javaField() + " -> column \"" + m.columnName() + "\"");
    }
}
```

How to run: `java MappingLevel1.java`

`totalAmount` becomes `total_amount` and `Order` becomes `order` — this is the same camelCase-to-snake_case convention from the naming-strategies card, applied identically here because Spring Data JDBC uses the same underlying naming-strategy mechanism as the rest of Spring Data for simple, flat fields.

### Level 2 — Intermediate

Add a nested `List<LineItem>` field and model the implicit child-table/foreign-key relationship it produces.

```java
import java.util.*;

public class MappingLevel2 {
    static String toSnakeCase(String name) {
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < name.length(); i++) {
            char c = name.charAt(i);
            if (Character.isUpperCase(c)) { if (i > 0) sb.append('_'); sb.append(Character.toLowerCase(c)); }
            else sb.append(c);
        }
        return sb.toString();
    }

    record TableMapping(String tableName, List<String> columns, String foreignKeyToParent) {}

    // Simulates mapping: class Order { @Id Long id; String status; List<LineItem> lineItems; }
    //                     class LineItem { String description; }
    public static void main(String[] args) {
        String parentClass = "Order";
        String parentTable = toSnakeCase(parentClass);
        TableMapping parentMapping = new TableMapping(parentTable, List.of("id", "status"), null);

        String childClass = "LineItem";
        String childTable = toSnakeCase(childClass);
        // The FK column in the child table is named after the PARENT entity, implicitly -- not declared in LineItem itself.
        TableMapping childMapping = new TableMapping(childTable, List.of("description"), parentTable);

        System.out.println("Parent table \"" + parentMapping.tableName() + "\": columns " + parentMapping.columns());
        System.out.println("Child table \"" + childMapping.tableName() + "\": columns " + childMapping.columns()
            + " + implicit FK column \"" + childMapping.foreignKeyToParent() + "\"");
    }
}
```

How to run: `java MappingLevel2.java`

`LineItem` itself declares only `description` — nowhere in the Java class is there a field for the foreign key back to `Order`. Spring Data JDBC infers that the `line_item` table needs an `order` column (named after the parent) purely from `Order.lineItems` being a `List<LineItem>` field — the relationship, and its column name, comes entirely from the parent's field declaration.

### Level 3 — Advanced

Generate the actual `CREATE TABLE` DDL a real schema would need for this mapping, and simulate an insert showing how a saved aggregate's rows land in both tables with the FK correctly populated.

```java
import java.util.*;

public class MappingLevel3 {
    static String toSnakeCase(String name) {
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < name.length(); i++) {
            char c = name.charAt(i);
            if (Character.isUpperCase(c)) { if (i > 0) sb.append('_'); sb.append(Character.toLowerCase(c)); }
            else sb.append(c);
        }
        return sb.toString();
    }

    static void printDdl() {
        System.out.println("CREATE TABLE " + toSnakeCase("Order") + " (");
        System.out.println("    id BIGINT PRIMARY KEY,");
        System.out.println("    status VARCHAR(50)");
        System.out.println(");");
        System.out.println("CREATE TABLE " + toSnakeCase("LineItem") + " (");
        System.out.println("    " + toSnakeCase("Order") + " BIGINT REFERENCES " + toSnakeCase("Order") + "(id),  -- implicit FK");
        System.out.println("    description VARCHAR(255)");
        System.out.println(");");
    }

    // Simulates what orderRepository.save(order) inserts into BOTH tables.
    static void simulateSave(long orderId, String status, List<String> lineItemDescriptions) {
        System.out.println("INSERT INTO " + toSnakeCase("Order") + " (id, status) VALUES (" + orderId + ", '" + status + "');");
        for (String desc : lineItemDescriptions) {
            System.out.println("INSERT INTO " + toSnakeCase("LineItem") + " (" + toSnakeCase("Order") + ", description) VALUES ("
                + orderId + ", '" + desc + "');"); // FK column populated automatically from the parent's id
        }
    }

    public static void main(String[] args) {
        System.out.println("-- Schema (write this by hand -- Spring Data JDBC has no auto-DDL):");
        printDdl();

        System.out.println();
        System.out.println("-- Effect of orderRepository.save(new Order(1, \"PENDING\", [Widget, Gadget])):");
        simulateSave(1, "PENDING", List.of("Widget", "Gadget"));
    }
}
```

How to run: `java MappingLevel3.java`

The generated DDL shows exactly two tables, with `line_item.order` as the implicit foreign key column — this is the schema a developer must actually write by hand for Spring Data JDBC (there is no `ddl-auto` equivalent). The simulated save then shows one `INSERT` into `order` and one `INSERT` per line item into `line_item`, each correctly populating the `order` foreign-key column with the parent's ID — exactly the delete-then-reinsert-of-children mechanics the aggregates-philosophy card described, expressed here as concrete SQL.

## 6. Walkthrough

Execution starts in `main` for Level 3. First, `printDdl()` runs: it prints `CREATE TABLE order (...)` with `id` and `status` columns (derived from `Order`'s fields), followed by `CREATE TABLE line_item (...)` with an `order` column (the implicit foreign key, named via `toSnakeCase("Order")`) and a `description` column (from `LineItem`'s own field) — this is the schema that must exist in the actual database *before* any repository code can run, since Spring Data JDBC never generates or alters schema itself.

Next, `simulateSave(1, "PENDING", List.of("Widget", "Gadget"))` runs, standing in for `orderRepository.save(...)`. It first prints an `INSERT INTO order (id, status) VALUES (1, 'PENDING')` — the aggregate root's own row. Then it loops over the two line-item descriptions, printing one `INSERT INTO line_item (order, description) VALUES (1, 'Widget')` and one `INSERT INTO line_item (order, description) VALUES (1, 'Gadget')` — each explicitly carrying `1` (the parent order's ID) in the `order` column, linking each child row back to its parent.

```
class Order { id, status, List<LineItem> lineItems }  --maps to-->  order table + line_item table (FK: "order")
class LineItem { description }                        --maps to-->  line_item.description column

save(Order(1, "PENDING", [Widget, Gadget]))
  -> INSERT INTO order (id, status) VALUES (1, 'PENDING')
  -> INSERT INTO line_item (order, description) VALUES (1, 'Widget')
  -> INSERT INTO line_item (order, description) VALUES (1, 'Gadget')
```

In a real Spring Data JDBC application, this exact mapping algorithm runs the first time `orderRepository.save(order)` is called: Spring Data JDBC inspects `Order`'s class structure (via reflection over its constructor/fields), determines `line_item` needs an `order` foreign-key column because `Order` declares a `List<LineItem> lineItems` field, and generates the `INSERT` statements accordingly — the developer's only responsibility is to have already created matching tables (`order`, `line_item`) with compatible column names and types in the actual database schema, typically via a migration tool like Flyway or Liquibase run before the application starts.

## 7. Gotchas & takeaways

> Gotcha: because Spring Data JDBC has no schema-generation tool, a mismatch between the entity's implied mapping (table/column/foreign-key names) and the actual database schema fails at query/save time with a SQL-level error (e.g., "column not found") rather than at application startup — there's no early validation step comparing the entity model against the schema the way some JPA setups perform.

- Table and column names follow the same naming-strategy convention as the rest of Spring Data (camelCase to snake_case by default).
- A `List<X>`/`Set<X>` field on the parent implies a separate child table, linked back by a foreign-key column named after the *parent* entity — this column is never explicitly declared on the child class.
- Spring Data JDBC has no `ddl-auto`/schema-generation feature — the schema must be created by hand (or via a migration tool) to match what the entity mapping expects.
- When debugging a "table/column not found" error, work out what name the mapping convention actually produces before assuming the entity's Java-side structure is wrong.
