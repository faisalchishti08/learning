---
card: spring-data
gi: 158
slug: schema-management
title: "Schema management"
---

## 1. What it is

`CassandraAdminTemplate` (and `@Table`/`@UserDefinedType`'s ability to auto-generate CQL DDL via `SchemaAction`) manages Cassandra's schema lifecycle — creating keyspaces, tables, and user-defined types from annotated entity classes, similar in purpose to the `IndexOperations` covered for Elasticsearch, but adapted to Cassandra's stricter, more consequential table-design decisions from earlier cards in this section.

```java
@Bean
SessionFactoryFactoryBean sessionFactory(CqlSession session, CassandraConverter converter) {
    SessionFactoryFactoryBean factory = new SessionFactoryFactoryBean();
    factory.setSession(session);
    factory.setConverter(converter);
    factory.setSchemaAction(SchemaAction.CREATE_IF_NOT_EXISTS); // auto-creates tables matching @Table entities
    return factory;
}
```

## 2. Why & when

Every earlier card in this section assumed the `orders` table (and any UDTs it used) already existed with the correct partition/clustering key structure. Someone — or something — has to actually run the `CREATE TABLE`/`CREATE TYPE` statements that establish that structure, and because Cassandra's key design is so consequential (as the composite-key card established), schema management in Cassandra carries more weight than in a schema-flexible store like MongoDB.

Reach for explicit schema management when:

- Setting up a new keyspace or table for the first time — development environments commonly use `SchemaAction.CREATE_IF_NOT_EXISTS` to auto-generate tables from annotated entities, saving hand-written DDL during early iteration.
- Running a production deployment, where schema changes are typically handled by an explicit, reviewed migration process (a CQL migration tool, or manually-run DDL scripts) rather than automatic generation — precisely because a table's key structure is so hard to change after data exists, unlike a MongoDB collection's flexible schema.
- Adding a new column to an existing table (Cassandra supports this via `ALTER TABLE ... ADD`, similar to a relational database) — a lower-stakes schema change than altering a primary key, which generally requires creating an entirely new table.

## 3. Core concept

```
 SchemaAction.NONE                  -- schema managed entirely outside the application (typical for production)
 SchemaAction.CREATE_IF_NOT_EXISTS  -- auto-creates missing tables/types from @Table/@UserDefinedType entities
 SchemaAction.RECREATE               -- DROPS and recreates -- destructive, development/testing ONLY

 @Table("orders")
 class Order { @PrimaryKey String orderId; ... }
        |
        v (with CREATE_IF_NOT_EXISTS)
 CREATE TABLE IF NOT EXISTS orders (order_id text PRIMARY KEY, ...);

 Adding a new column LATER:  ALTER TABLE orders ADD new_field text;   -- supported, low-risk
 Changing the PARTITION KEY: requires a NEW table entirely             -- not an ALTER TABLE operation
```

`SchemaAction` controls how much automatic schema management the application performs — ranging from none at all to fully automatic creation, with `RECREATE` being explicitly destructive and appropriate only outside production.

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Three SchemaAction levels range from no automatic management to safe creation to destructive recreation">
  <rect x="20" y="20" width="180" height="55" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.3"/>
  <text x="110" y="45" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">NONE</text>
  <text x="110" y="60" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">production default</text>

  <rect x="230" y="20" width="180" height="55" rx="8" fill="#3fb95022" stroke="#3fb950" stroke-width="1.5"/>
  <text x="320" y="45" fill="#3fb950" font-size="9.5" text-anchor="middle" font-family="sans-serif">CREATE_IF_NOT_EXISTS</text>
  <text x="320" y="60" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">safe, dev-friendly</text>

  <rect x="440" y="20" width="180" height="55" rx="8" fill="#f8514922" stroke="#f85149" stroke-width="1.5"/>
  <text x="530" y="45" fill="#f85149" font-size="9.5" text-anchor="middle" font-family="sans-serif">RECREATE</text>
  <text x="530" y="60" fill="#f85149" font-size="7.5" text-anchor="middle" font-family="sans-serif">DESTRUCTIVE -- drops data</text>

  <text x="320" y="115" fill="#8b949e" font-size="9.5" text-anchor="middle" font-family="sans-serif">increasing automation, increasing risk -- choose deliberately per environment</text>
</svg>

Each `SchemaAction` level trades convenience for risk differently — appropriate choice depends heavily on the environment.

## 5. Runnable example

The scenario: managing a table's schema lifecycle, evolving from a basic create-if-not-exists check, to adding a new column via `ALTER TABLE` (a safe, supported schema change), to the correct approach for changing a table's key structure — creating a new table rather than attempting to alter the existing one, echoing the earlier index-management-style migration pattern from the Elasticsearch section.

### Level 1 — Basic

Model `CREATE_IF_NOT_EXISTS`: create a table only if it doesn't already exist, safe to run repeatedly.

```java
import java.util.*;

public class SchemaLevel1 {
    public static void main(String[] args) {
        CassandraSchemaManager schema = new CassandraSchemaManager();

        applySchema(schema); // first run -- table doesn't exist yet, gets created
        applySchema(schema); // second run -- SAFE, table already exists, nothing happens
    }

    // Mirrors SchemaAction.CREATE_IF_NOT_EXISTS being applied at application startup.
    static void applySchema(CassandraSchemaManager schema) {
        if (schema.tableExists("orders")) {
            System.out.println("Table 'orders' already exists -- skipping creation.");
            return;
        }
        schema.createTable("orders");
        System.out.println("Table 'orders' created.");
    }
}

class CassandraSchemaManager {
    private final Set<String> existingTables = new HashSet<>();
    boolean tableExists(String name) { return existingTables.contains(name); }
    void createTable(String name) { existingTables.add(name); }
}
```

How to run: `java SchemaLevel1.java`

`applySchema` checks `tableExists` before creating, exactly matching `SchemaAction.CREATE_IF_NOT_EXISTS`'s idempotent behavior — safe to run on every application startup, since the second call recognizes the table already exists and does nothing further.

### Level 2 — Intermediate

Model `ALTER TABLE ... ADD`: a supported, low-risk schema change that adds a new column without touching existing data or the table's key structure.

```java
import java.util.*;

public class SchemaLevel2 {
    public static void main(String[] args) {
        CassandraSchemaManager schema = new CassandraSchemaManager();
        schema.createTable("orders", List.of("order_id", "status", "total"));
        schema.insertRow("orders", Map.of("order_id", "1", "status", "PENDING", "total", "50.0"));

        System.out.println("Columns before ALTER: " + schema.columnsFor("orders"));

        // ALTER TABLE orders ADD priority text; -- adds a new column, existing rows get a NULL value for it.
        schema.addColumn("orders", "priority");
        System.out.println("Columns after ALTER: " + schema.columnsFor("orders"));

        Map<String, String> existingRow = schema.selectRow("orders", "1");
        System.out.println("Existing row's new column value: " + existingRow.getOrDefault("priority", "null (not backfilled)"));
    }
}

class CassandraSchemaManager {
    private final Map<String, List<String>> tableColumns = new HashMap<>();
    private final Map<String, Map<String, Map<String, String>>> tableData = new HashMap<>(); // table -> rowKey -> row

    void createTable(String name, List<String> columns) {
        tableColumns.put(name, new ArrayList<>(columns));
        tableData.put(name, new HashMap<>());
    }
    void insertRow(String table, Map<String, String> row) { tableData.get(table).put(row.get("order_id"), row); }
    List<String> columnsFor(String table) { return tableColumns.get(table); }

    // Adding a column is SAFE -- existing rows are simply treated as having no value for it, no rewrite needed.
    void addColumn(String table, String columnName) { tableColumns.get(table).add(columnName); }

    Map<String, String> selectRow(String table, String key) { return tableData.get(table).get(key); }
}
```

How to run: `java SchemaLevel2.java`

`addColumn` mirrors `ALTER TABLE orders ADD priority text` — the column list grows to include `"priority"`, but the existing row (inserted before the `ALTER`) simply has no value for it, since Cassandra doesn't rewrite existing rows when a column is added. This is a safe, low-risk schema change precisely because it doesn't touch the table's partition or clustering key at all.

### Level 3 — Advanced

Model the correct approach for a key-structure change: since Cassandra can't `ALTER` a primary key, create a new, correctly-keyed table and migrate data into it — mirroring the reindex-and-swap pattern from the earlier Elasticsearch index-management card, applied to Cassandra's schema instead.

```java
import java.util.*;

public class SchemaLevel3 {
    public static void main(String[] args) {
        CassandraSchemaManager schema = new CassandraSchemaManager();

        // Original table: keyed by order_id ONLY -- can't efficiently answer "all orders for a customer."
        schema.createTable("orders_by_id", List.of("order_id", "customer_id", "status"));
        schema.insertRow("orders_by_id", Map.of("order_id", "1", "customer_id", "customer-A", "status", "PENDING"));
        schema.insertRow("orders_by_id", Map.of("order_id", "2", "customer_id", "customer-A", "status", "SHIPPED"));
        schema.insertRow("orders_by_id", Map.of("order_id", "3", "customer_id", "customer-B", "status", "DELIVERED"));

        System.out.println("Need to query 'all orders for a customer' efficiently -- but customer_id isn't the partition key.");
        System.out.println("Cassandra does NOT support ALTER TABLE to change the partition key -- creating a new table instead.");

        // New table, DIFFERENT key structure: partitioned by customer_id -- designed for the NEW access pattern.
        schema.createTable("orders_by_customer", List.of("customer_id", "order_id", "status"));

        // Migrate: read every row from the OLD table, write it into the NEW table -- an application-level ETL,
        // since Cassandra has no built-in "reindex" the way Elasticsearch does.
        int migrated = 0;
        for (Map<String, String> row : schema.allRows("orders_by_id")) {
            schema.insertRow("orders_by_customer", row);
            migrated++;
        }
        System.out.println("Migrated " + migrated + " rows from 'orders_by_id' to 'orders_by_customer'.");

        List<Map<String, String>> customerAOrders = schema.selectByField("orders_by_customer", "customer_id", "customer-A");
        System.out.println("customer-A's orders, now efficiently queryable: " + customerAOrders.size());
    }
}

class CassandraSchemaManager {
    private final Map<String, List<String>> tableColumns = new HashMap<>();
    private final Map<String, List<Map<String, String>>> tableRows = new HashMap<>();

    void createTable(String name, List<String> columns) {
        tableColumns.put(name, new ArrayList<>(columns));
        tableRows.put(name, new ArrayList<>());
    }
    void insertRow(String table, Map<String, String> row) { tableRows.get(table).add(row); }
    List<Map<String, String>> allRows(String table) { return tableRows.get(table); }
    List<Map<String, String>> selectByField(String table, String field, String value) {
        List<Map<String, String>> results = new ArrayList<>();
        for (Map<String, String> row : tableRows.get(table)) if (value.equals(row.get(field))) results.add(row);
        return results;
    }
}
```

How to run: `java SchemaLevel3.java`

Rather than attempting (and failing) to `ALTER` `orders_by_id`'s partition key, a brand-new table, `orders_by_customer`, is created with `customer_id` as its intended partition key, and every row from the old table is read and re-inserted into the new one — an application-level migration, since Cassandra has no built-in equivalent to Elasticsearch's `_reindex` API. Once migrated, querying `orders_by_customer` by `customer_id` is efficient, exactly matching the "model a new table per access pattern" discipline established throughout this section.

## 6. Walkthrough

Execution starts in `main` for Level 3. `orders_by_id` is created and populated with three rows, two belonging to `customer-A` and one to `customer-B`.

After printing the explanatory messages, `orders_by_customer` is created with the same logical columns but a different intended key role for `customer_id`. The `for` loop iterates `schema.allRows("orders_by_id")` — all three previously inserted rows — and calls `schema.insertRow("orders_by_customer", row)` for each one, copying the row data verbatim into the new table. `migrated` is incremented once per row, ending at `3`.

`schema.selectByField("orders_by_customer", "customer_id", "customer-A")` then scans `orders_by_customer`'s rows (in this simplified model, a linear scan, since the example doesn't implement true partition-based storage) looking for `customer_id = "customer-A"` — it finds the two matching rows migrated from the original table.

```
Need to query 'all orders for a customer' efficiently -- but customer_id isn't the partition key.
Cassandra does NOT support ALTER TABLE to change the partition key -- creating a new table instead.
Migrated 3 rows from 'orders_by_id' to 'orders_by_customer'.
customer-A's orders, now efficiently queryable: 2
```

In a real Cassandra migration, this data copy would typically be performed with a dedicated ETL tool (Spark, DSBulk, or a custom batch job reading from the old table and writing to the new one) rather than a simple in-memory loop, since production tables can hold far more data than fits comfortably in application memory at once — but the structural approach is identical: read every row from the old table, transform if needed, write into the new, correctly-keyed table, and only then switch the application to query the new table.

## 7. Gotchas & takeaways

> Gotcha: `SchemaAction.RECREATE` drops and recreates every managed table on application startup — an easy way to accidentally destroy production data if this setting is left enabled outside a development or testing environment. Always confirm `SchemaAction` is set appropriately per environment before deploying.

> Gotcha: unlike Elasticsearch's `_reindex` API (which runs server-side), migrating data into a new Cassandra table with a different key structure is an application-level operation with no built-in tooling to make it atomic or resumable — a migration interrupted partway through leaves the new table partially populated, and the application needs its own tracking (a checkpoint, a "last migrated id") to resume correctly rather than restarting from scratch or duplicating already-migrated rows.

- `SchemaAction` controls how much automatic schema management the application performs, ranging from `NONE` (fully external) to `CREATE_IF_NOT_EXISTS` (safe, additive) to `RECREATE` (destructive — development only).
- Adding a new column via `ALTER TABLE ... ADD` is safe and doesn't require rewriting existing rows, since they simply lack a value for the new column until explicitly updated.
- Changing a table's partition or clustering key structure is not supported via `ALTER TABLE` — it requires creating a new table and migrating data into it, mirroring the same reindex-and-swap discipline seen in the earlier Elasticsearch index-management card.
- Cassandra has no built-in server-side reindex tooling — migrating data between differently-keyed tables is an application-level (or external tool-driven) responsibility, and should be designed to be resumable for large datasets.
