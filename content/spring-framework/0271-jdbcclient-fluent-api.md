---
card: spring-framework
gi: 271
slug: jdbcclient-fluent-api
title: JdbcClient (fluent API)
---

## 1. What it is

`JdbcClient` is a **fluent, unified SQL client** introduced in Spring Framework 6.1. It combines the positional-parameter convenience of `JdbcTemplate` with the named-parameter power of `NamedParameterJdbcTemplate` into a single, chainable API:

```java
// Old style: two separate template classes
namedJdbc.queryForList(
    "SELECT name FROM users WHERE role = :role",
    Map.of("role","ADMIN"), String.class);

// New style: one client, fluent chain
List<String> names = jdbcClient.sql("SELECT name FROM users WHERE role = :role")
    .param("role", "ADMIN")
    .query(String.class)
    .list();
```

`JdbcClient` wraps an underlying `JdbcTemplate` or `NamedParameterJdbcTemplate` — it delegates all real work to them. Create it via `JdbcClient.create(dataSource)` or `JdbcClient.create(jdbcTemplate)`.

## 2. Why & when

`JdbcClient` is the **recommended JDBC API** as of Spring 6.1 for new code. It replaces the common pattern of injecting both `JdbcTemplate` and `NamedParameterJdbcTemplate`:

- Fewer imports and less boilerplate — one class handles everything.
- Named and positional parameters unified in one chain.
- Terminal methods (`list()`, `single()`, `optional()`, `rowsAffected()`) make intent clear.
- `query(Class<T>)` uses built-in type mapping for scalars; `query(RowMapper<T>)` for complex types.

Use `JdbcClient` for all new Spring 6.1+ code. Keep `JdbcTemplate` directly when you need `batchUpdate`, `execute(DDL)`, or callbacks like `ResultSetExtractor` — `JdbcClient` doesn't expose those yet.

## 3. Core concept

`JdbcClient` fluent chain structure:

```
JdbcClient.create(ds)          ← build client
  .sql("SELECT ... WHERE :x")  ← set SQL
  .param("x", value)           ← bind named param
  .param(index, value)         ← OR positional (1-based)
  .params(map)                 ← OR bulk named
  .params(values...)           ← OR positional varargs

Termination — query:
  .query(RowMapper<T>)         → StatementSpec.MappedQuerySpec<T>
  .query(Class<T>)             → StatementSpec.MappedQuerySpec<T>   (scalars + beans)

MappedQuerySpec<T> methods:
  .list()     → List<T>
  .single()   → T               (exactly 1 row; throws on 0 or 2+)
  .optional() → Optional<T>     (0 or 1 row; throws on 2+)
  .set()      → Set<T>
  .stream()   → Stream<T>       (must be closed!)

Termination — update/insert/delete:
  .update()   → int             (rows affected)
```

## 4. Diagram

<svg viewBox="0 0 700 200" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <marker id="arr" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <polygon points="0 0,8 3,0 6" fill="#6db33f"/>
    </marker>
  </defs>

  <!-- JdbcClient -->
  <rect x="10" y="60" width="130" height="80" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="75" y="84" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">JdbcClient</text>
  <line x1="20" y1="90" x2="130" y2="90" stroke="#8b949e" stroke-width="0.5"/>
  <text x="75" y="108" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">.sql()</text>
  <text x="75" y="122" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">.param()</text>
  <text x="75" y="136" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">.query() / .update()</text>

  <line x1="142" y1="100" x2="195" y2="100" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>

  <!-- Internals -->
  <rect x="197" y="40" width="200" height="120" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="297" y="62" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Internal Delegation</text>
  <line x1="207" y1="68" x2="387" y2="68" stroke="#8b949e" stroke-width="0.5"/>
  <text x="297" y="86" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">named params → NP JdbcTemplate</text>
  <text x="297" y="102" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">positional params → JdbcTemplate</text>
  <text x="297" y="118" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">scalar types → built-in mapping</text>
  <text x="297" y="134" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">bean types → BeanPropertyRowMapper</text>
  <text x="297" y="150" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">custom → your RowMapper</text>

  <line x1="399" y1="100" x2="452" y2="100" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>

  <!-- Results -->
  <rect x="454" y="50" width="200" height="100" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="554" y="72" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">Result Terminals</text>
  <line x1="464" y1="78" x2="644" y2="78" stroke="#8b949e" stroke-width="0.5"/>
  <text x="554" y="95" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">.list()     → List&lt;T&gt;</text>
  <text x="554" y="111" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">.single()   → T</text>
  <text x="554" y="127" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">.optional() → Optional&lt;T&gt;</text>
  <text x="554" y="143" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">.stream()   → Stream&lt;T&gt;</text>
</svg>

`JdbcClient` chains build a query or update spec, then a terminal method executes it via the underlying `JdbcTemplate` / `NamedParameterJdbcTemplate`.

## 5. Runnable example

Scenario: a **customer management** system — create, query, update, and delete customers using the fluent `JdbcClient` API.

### Level 1 — Basic

Named parameters in SELECT and INSERT via `JdbcClient`.

```java
// JdbcClientDemo.java
import org.springframework.jdbc.core.simple.JdbcClient;
import org.springframework.jdbc.datasource.embedded.*;
import javax.sql.DataSource;
import java.util.List;
import java.util.Optional;

record Customer(long id, String name, String email, String tier) {}

public class JdbcClientDemo {

    static DataSource buildDs() {
        return new EmbeddedDatabaseBuilder()
            .setType(EmbeddedDatabaseType.H2)
            .addScript("classpath:customer-schema.sql")
            .build();
    }

    public static void main(String[] args) {
        JdbcClient client = JdbcClient.create(buildDs());

        // INSERT — named params, .update() returns rows affected
        int rows = client.sql("INSERT INTO customers(name,email,tier) VALUES(:name,:email,:tier)")
            .param("name", "Alice")
            .param("email", "alice@example.com")
            .param("tier", "Gold")
            .update();
        System.out.println("Inserted: " + rows + " row(s)");

        client.sql("INSERT INTO customers(name,email,tier) VALUES(:name,:email,:tier)")
            .params(java.util.Map.of("name","Bob","email","bob@example.com","tier","Silver"))
            .update();
        client.sql("INSERT INTO customers(name,email,tier) VALUES(:name,:email,:tier)")
            .param("name","Carol").param("email","carol@example.com").param("tier","Gold")
            .update();

        // SELECT list — .query(Class<T>) for scalar column
        List<String> names = client.sql("SELECT name FROM customers ORDER BY name")
            .query(String.class)
            .list();
        System.out.println("Names: " + names);

        // SELECT with predicate — named param
        List<String> gold = client.sql("SELECT name FROM customers WHERE tier = :tier ORDER BY name")
            .param("tier", "Gold")
            .query(String.class)
            .list();
        System.out.println("Gold tier: " + gold);

        // COUNT — .single() for exactly one scalar result
        Integer count = client.sql("SELECT COUNT(*) FROM customers")
            .query(Integer.class)
            .single();
        System.out.println("Total customers: " + count);
    }
}
```

`customer-schema.sql`:
```sql
CREATE TABLE customers (
  id    BIGINT AUTO_INCREMENT PRIMARY KEY,
  name  VARCHAR(100) NOT NULL,
  email VARCHAR(200) UNIQUE,
  tier  VARCHAR(30)
);
```

How to run: `java -cp spring-context.jar:spring-jdbc.jar:h2.jar:. JdbcClientDemo.java`

`.param("key", value)` adds a named parameter; `.params(Map)` adds several at once. `.query(String.class)` uses Spring's built-in type mapping for scalar columns. `.list()` collects all rows; `.single()` asserts exactly one row and throws otherwise.

---

### Level 2 — Intermediate

`query(RowMapper<T>)` for domain objects + `optional()` + positional params.

```java
// JdbcClientDemo.java
import org.springframework.jdbc.core.simple.JdbcClient;
import org.springframework.jdbc.core.*;
import org.springframework.jdbc.datasource.embedded.*;
import javax.sql.DataSource;
import java.util.List;
import java.util.Optional;

record Customer(long id, String name, String email, String tier) {}

public class JdbcClientDemo {

    static final RowMapper<Customer> CUST_MAPPER = (rs, n) -> new Customer(
        rs.getLong("id"), rs.getString("name"),
        rs.getString("email"), rs.getString("tier"));

    static DataSource buildDs() {
        return new EmbeddedDatabaseBuilder()
            .setType(EmbeddedDatabaseType.H2)
            .addScript("classpath:customer-schema.sql")
            .addScript("classpath:customer-data.sql")
            .build();
    }

    public static void main(String[] args) {
        JdbcClient client = JdbcClient.create(buildDs());

        // query(RowMapper) → MappedQuerySpec<Customer>
        List<Customer> all = client.sql("SELECT * FROM customers ORDER BY name")
            .query(CUST_MAPPER)
            .list();
        System.out.println("All customers:");
        all.forEach(c -> System.out.printf("  [%d] %-10s %-25s %s%n",
            c.id(), c.name(), c.email(), c.tier()));

        // optional() — safe "find by id"
        Optional<Customer> found = client.sql("SELECT * FROM customers WHERE id = :id")
            .param("id", 1L)
            .query(CUST_MAPPER)
            .optional();
        found.ifPresentOrElse(
            c -> System.out.println("Found: " + c.name()),
            ()  -> System.out.println("Not found"));

        Optional<Customer> missing = client.sql("SELECT * FROM customers WHERE id = :id")
            .param("id", 999L)
            .query(CUST_MAPPER)
            .optional();
        System.out.println("Missing: " + missing.isEmpty());  // true

        // Positional params (1-based index)
        List<Customer> goldSilver = client.sql("SELECT * FROM customers WHERE tier IN (?,?) ORDER BY tier,name")
            .param(1, "Gold")
            .param(2, "Silver")
            .query(CUST_MAPPER)
            .list();
        System.out.println("Gold+Silver count: " + goldSilver.size());

        // UPDATE
        int updated = client.sql("UPDATE customers SET tier = :newTier WHERE tier = :oldTier")
            .param("newTier", "Platinum")
            .param("oldTier", "Gold")
            .update();
        System.out.println("Promoted to Platinum: " + updated);
    }
}
```

`customer-data.sql`:
```sql
INSERT INTO customers(name,email,tier) VALUES('Alice','alice@example.com','Gold');
INSERT INTO customers(name,email,tier) VALUES('Bob','bob@example.com','Silver');
INSERT INTO customers(name,email,tier) VALUES('Carol','carol@example.com','Gold');
INSERT INTO customers(name,email,tier) VALUES('Dave','dave@example.com','Bronze');
```

How to run: same classpath

`.optional()` returns `Optional<T>` — it handles the "might not exist" case without try/catch around `EmptyResultDataAccessException`. Positional params use `1`-based integer index in `.param(index, value)` — useful when the SQL uses `?` placeholders.

---

### Level 3 — Advanced

`BeanPropertyRowMapper` shorthand + `stream()` for large result processing + bulk inserts.

```java
// JdbcClientDemo.java
import org.springframework.jdbc.core.*;
import org.springframework.jdbc.core.simple.JdbcClient;
import org.springframework.jdbc.datasource.embedded.*;
import org.springframework.jdbc.support.GeneratedKeyHolder;
import javax.sql.DataSource;
import java.util.*;
import java.util.stream.*;

public class Customer {
    private long id; private String name, email, tier;
    public Customer(){}
    public long getId(){return id;} public void setId(long i){id=i;}
    public String getName(){return name;} public void setName(String n){name=n;}
    public String getEmail(){return email;} public void setEmail(String e){email=e;}
    public String getTier(){return tier;} public void setTier(String t){tier=t;}
    public String toString(){return "Customer["+id+","+name+","+tier+"]";}
}

public class JdbcClientDemo {

    static DataSource buildDs() {
        return new EmbeddedDatabaseBuilder()
            .setType(EmbeddedDatabaseType.H2)
            .addScript("classpath:customer-schema.sql")
            .build();
    }

    public static void main(String[] args) {
        DataSource ds = buildDs();
        JdbcClient client = JdbcClient.create(ds);

        // Bulk insert — loop with fluent chain
        List<String[]> rows = List.of(
            new String[]{"Alice","alice@example.com","Gold"},
            new String[]{"Bob","bob@example.com","Silver"},
            new String[]{"Carol","carol@example.com","Gold"},
            new String[]{"Dave","dave@example.com","Bronze"},
            new String[]{"Eve","eve@example.com","Platinum"}
        );
        for (String[] r : rows) {
            client.sql("INSERT INTO customers(name,email,tier) VALUES(:name,:email,:tier)")
                .param("name",r[0]).param("email",r[1]).param("tier",r[2]).update();
        }

        // Insert with generated key retrieval
        var keyHolder = new GeneratedKeyHolder();
        client.sql("INSERT INTO customers(name,email,tier) VALUES(:name,:email,:tier)")
            .param("name","Frank").param("email","frank@example.com").param("tier","Silver")
            .update(keyHolder);
        System.out.println("Frank's id: " + keyHolder.getKey().longValue());

        // BeanPropertyRowMapper shorthand via query(Class) on a JavaBean
        // Spring 6.1+ can map a bean class via query(Customer.class) using BeanPropertyRowMapper
        List<Customer> golds = client.sql("SELECT * FROM customers WHERE tier = :tier ORDER BY name")
            .param("tier","Gold")
            .query(Customer.class)   // Spring uses BeanPropertyRowMapper for bean types
            .list();
        System.out.println("Gold customers: " + golds);

        // stream() — process large result sets without materialising the full list
        long highValueCount;
        try (Stream<Customer> stream = client.sql("SELECT * FROM customers ORDER BY id")
                .query(Customer.class).stream()) {
            highValueCount = stream
                .filter(c -> List.of("Gold","Platinum").contains(c.getTier()))
                .count();
        }
        System.out.println("Gold+Platinum count via stream: " + highValueCount);

        // Aggregation via fluent chain
        Map<String,Long> byTier = new LinkedHashMap<>();
        client.sql("SELECT tier, COUNT(*) cnt FROM customers GROUP BY tier ORDER BY tier")
            .query((rs, n) -> Map.entry(rs.getString("tier"), rs.getLong("cnt")))
            .list()
            .forEach(e -> byTier.put(e.getKey(), e.getValue()));
        System.out.println("By tier: " + byTier);
    }
}
```

How to run: same classpath

`.update(keyHolder)` binds the `GeneratedKeyHolder` to capture the auto-generated primary key. `query(Customer.class)` on a non-scalar type uses `BeanPropertyRowMapper` — Spring detects that `Customer.class` is not a scalar type and falls back to convention-based mapping. `.stream()` returns a lazy `Stream<T>` backed by the live `ResultSet` — **always close it** via `try-with-resources` or risk connection leaks.

## 6. Walkthrough

**Level 2 — `.optional()` for "find by id" (execution order):**

1. **`client.sql("SELECT * FROM customers WHERE id = :id").param("id", 1L).query(CUST_MAPPER).optional()`**: builds a `StatementSpec` and a `MappedQuerySpec<Customer>`.
2. **Terminal `.optional()` called**: delegates to the underlying `NamedParameterJdbcTemplate` (because `:id` is a named param).
3. **SQL parsing**: `:id` → `?`, index map `{id: 1}`.
4. **Connection + PreparedStatement**: `DataSourceUtils.getConnection(ds)`, `con.prepareStatement("SELECT * FROM customers WHERE id = ?")`.
5. **Bind**: `ps.setLong(1, 1L)`.
6. **Execute**: `ps.executeQuery()` — H2 returns a `ResultSet` with 1 row (id=1, Alice).
7. **Map**: `CUST_MAPPER.mapRow(rs, 1)` → `Customer(1,"Alice","alice@example.com","Gold")`.
8. **Collect**: `MappedQuerySpec.optional()` wraps the list in `Optional.of(customer)`.
9. **Return** `Optional<Customer>[Customer(1,...)]`.

For `id=999`:
- Step 6: `ResultSet` is empty.
- Step 8: list is empty → `Optional.empty()`.

```
id=1:
  SQL:    SELECT * FROM customers WHERE id = ?
  Params: [1]
  DB:     1 row → {id=1,name=Alice,email=...,tier=Gold}
  Result: Optional[Customer(1,Alice,...)]

id=999:
  SQL:    SELECT * FROM customers WHERE id = ?
  Params: [999]
  DB:     0 rows
  Result: Optional.empty
```

## 7. Gotchas & takeaways

> **Always close `stream()` results.** `JdbcClient.query(...).stream()` keeps a `ResultSet` and `Connection` open. Use `try-with-resources` — forgetting to close leaks the connection back to the pool.

> **`.single()` throws `EmptyResultDataAccessException` on zero rows** and `IncorrectResultSizeDataAccessException` on 2+ rows. Use `.optional()` for "might not exist" and `.list()` when you expect multiple rows. Never use `.single()` for a "find by id" query unless you're certain the row exists.

> **`query(SomeBean.class)` uses `BeanPropertyRowMapper` — it's reflective and does not validate missing columns.** Extra result columns are silently ignored; missing columns leave properties at their zero/null default. For production hot-paths, define an explicit `RowMapper<T>` for type safety and performance.

- `JdbcClient` is the recommended unified API for Spring 6.1+ — handles both named and positional params.
- `.param("key", val)` for named; `.param(index, val)` for positional.
- Terminal methods: `.list()`, `.single()`, `.optional()`, `.stream()` (must close), `.update()`.
- `.update(keyHolder)` captures generated keys.
- `stream()` is lazy — keeps a live connection; always wrap in `try-with-resources`.
