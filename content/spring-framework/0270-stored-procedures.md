---
card: spring-framework
gi: 270
slug: stored-procedures
title: Stored procedures
---

## 1. What it is

A **stored procedure** is a named, precompiled block of SQL (and procedural code) stored in the database and invoked by name. Spring JDBC calls stored procedures via:

1. **`JdbcTemplate.call(CallableStatementCreator, List<SqlParameter>)`** — low-level.
2. **`SimpleJdbcCall`** — high-level; reads parameter metadata from the database automatically.
3. **`StoredProcedure`** (subclass of `RdbmsOperation`) — object-oriented; declare parameters explicitly.

```java
// SimpleJdbcCall — discovers parameters from database metadata
SimpleJdbcCall call = new SimpleJdbcCall(ds).withProcedureName("calculate_discount");
Map<String,Object> out = call.execute(Map.of("p_price", 100.0, "p_pct", 10));
Double discount = (Double) out.get("p_discount");
```

## 2. Why & when

Stored procedures keep complex, set-based logic in the database where it can operate on data without moving rows over the wire. Common use cases:
- **Batch processing**: update thousands of rows in one call.
- **Business rules**: price calculations, inventory checks that span multiple tables.
- **Auditing / triggers**: centrally enforce logging inside the database.
- **DBA-owned logic**: DBAs write and optimize the SQL; Java just calls by name.

**When to prefer stored procedures:**
- Logic is data-intensive and runs faster close to the data.
- Multiple applications (Java, Python, a reporting tool) share the same logic.
- The schema is owned by DBAs who prefer SQL.

**When to avoid:**
- Logic belongs in the application (validation, business rules that change often).
- Database portability is required — stored procedure syntax is vendor-specific.

## 3. Core concept

JDBC callable statement syntax:
```java
// SQL: { call proc_name(?, ?) }   for a procedure
// SQL: { ? = call func_name(?, ?) }  for a function (returns a value)
CallableStatement cs = con.prepareCall("{call proc_name(?, ?)}");
cs.setInt(1, inputValue);
cs.registerOutParameter(2, Types.INTEGER);
cs.execute();
int result = cs.getInt(2);   // read OUT parameter
```

`SimpleJdbcCall` avoids writing this boilerplate:
- `withProcedureName(name)` sets the name.
- First `execute()` call reads `DatabaseMetaData.getProcedureColumns()` to discover IN/OUT params.
- `execute(Map)` binds IN params by name, calls `cs.execute()`, returns `Map<String,Object>` of OUT params.

Result sets from stored procedures are returned in `out.get("#result-set-1")` as `List<Map<String,Object>>` unless you wire a `RowMapper` via `returningResultSet("name", mapper)`.

## 4. Diagram

<svg viewBox="0 0 700 220" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <marker id="arr" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <polygon points="0 0,8 3,0 6" fill="#6db33f"/>
    </marker>
    <marker id="arr2" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <polygon points="0 0,8 3,0 6" fill="#79c0ff"/>
    </marker>
  </defs>

  <!-- Java side -->
  <rect x="10" y="80" width="120" height="60" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="70" y="104" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Java App</text>
  <text x="70" y="120" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">Map IN params</text>
  <text x="70" y="132" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">→ execute()</text>

  <line x1="132" y1="110" x2="185" y2="110" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>
  <text x="158" y="104" fill="#8b949e" font-size="7" text-anchor="middle" font-family="monospace">{call}</text>

  <!-- SimpleJdbcCall -->
  <rect x="187" y="50" width="200" height="120" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="287" y="72" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">SimpleJdbcCall</text>
  <line x1="197" y1="78" x2="377" y2="78" stroke="#8b949e" stroke-width="0.5"/>
  <text x="287" y="96" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">1. metadata → param list</text>
  <text x="287" y="112" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">2. prepareCall({call name})</text>
  <text x="287" y="128" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">3. bind IN params</text>
  <text x="287" y="144" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">4. registerOutParameters</text>
  <text x="287" y="160" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">5. cs.execute()</text>

  <line x1="389" y1="110" x2="442" y2="110" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>

  <!-- DB -->
  <rect x="444" y="60" width="160" height="100" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="524" y="82" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">Database</text>
  <line x1="454" y1="88" x2="594" y2="88" stroke="#8b949e" stroke-width="0.5"/>
  <text x="524" y="106" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">stored procedure</text>
  <text x="524" y="122" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">runs inside DB</text>
  <text x="524" y="138" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">→ OUT params</text>
  <text x="524" y="154" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">→ result sets</text>

  <!-- Return arrow -->
  <line x1="442" y1="130" x2="389" y2="130" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#arr2)"/>
  <text x="416" y="146" fill="#79c0ff" font-size="7" text-anchor="middle" font-family="monospace">Map OUT</text>
</svg>

`SimpleJdbcCall` discovers parameters from metadata, calls the procedure, and returns OUT parameters and result sets in a `Map`.

## 5. Runnable example

Scenario: a **pricing service** — a stored procedure computes discounted prices, returning an OUT parameter and a result set of applicable tiers.

### Level 1 — Basic

`JdbcTemplate.call()` with a `CallableStatementCreator` — low-level stored function call.

```java
// StoredProcDemo.java
import org.springframework.jdbc.core.*;
import org.springframework.jdbc.datasource.embedded.*;
import javax.sql.DataSource;
import java.sql.*;
import java.util.*;

public class StoredProcDemo {

    static DataSource buildDs() throws Exception {
        EmbeddedDatabase db = new EmbeddedDatabaseBuilder()
            .setType(EmbeddedDatabaseType.H2)
            .addScript("classpath:pricing-schema.sql")
            .addScript("classpath:pricing-proc.sql")
            .build();
        return db;
    }

    public static void main(String[] args) throws Exception {
        JdbcTemplate jdbc = new JdbcTemplate(buildDs());

        // Declare the OUT parameter
        List<SqlParameter> params = List.of(
            new SqlParameter("p_price",    Types.DOUBLE),
            new SqlParameter("p_pct",      Types.INTEGER),
            new SqlOutParameter("p_result", Types.DOUBLE)
        );

        // CallableStatementCreator: builds the {call} statement
        Map<String,Object> out = jdbc.call(
            con -> {
                CallableStatement cs = con.prepareCall("{call CALC_DISCOUNT(?, ?, ?)}");
                cs.setDouble(1, 100.0);   // p_price
                cs.setInt(2, 15);          // p_pct (15%)
                cs.registerOutParameter(3, Types.DOUBLE);
                return cs;
            },
            params
        );

        System.out.printf("Discount result: $%.2f%n", (Double) out.get("p_result"));
        // Expected: 100.0 * (1 - 15/100) = 85.0
    }
}
```

`pricing-schema.sql`: `CREATE TABLE pricing_tiers (tier VARCHAR(20), min_price DOUBLE, pct INT);`

`pricing-proc.sql`:
```sql
CREATE ALIAS CALC_DISCOUNT AS $$
double calcDiscount(Connection c, double price, int pct) {
    return price * (1.0 - pct / 100.0);
}
$$;
```

How to run: `java -cp spring-context.jar:spring-jdbc.jar:h2.jar:. StoredProcDemo.java`

H2 implements stored procedures as Java-based `ALIAS` functions. `cs.registerOutParameter(3, Types.DOUBLE)` tells JDBC driver to expect an OUT value at position 3. After `cs.execute()`, `JdbcTemplate.call()` reads all registered OUT parameters and returns them in a `Map<String,Object>` keyed by the `SqlOutParameter` name.

---

### Level 2 — Intermediate

`SimpleJdbcCall` with named parameters — automatic metadata discovery.

```java
// StoredProcDemo.java
import org.springframework.jdbc.core.simple.SimpleJdbcCall;
import org.springframework.jdbc.core.namedparam.MapSqlParameterSource;
import org.springframework.jdbc.datasource.embedded.*;
import javax.sql.DataSource;
import java.util.Map;

public class StoredProcDemo {

    static DataSource buildDs() {
        return new EmbeddedDatabaseBuilder()
            .setType(EmbeddedDatabaseType.H2)
            .addScript("classpath:pricing-schema.sql")
            .addScript("classpath:pricing-proc.sql")
            .addScript("classpath:pricing-data.sql")
            .addScript("classpath:pricing-summary-proc.sql")
            .build();
    }

    public static void main(String[] args) {
        DataSource ds = buildDs();

        // SimpleJdbcCall — reads param metadata from DB on first execute()
        SimpleJdbcCall calcCall = new SimpleJdbcCall(ds)
            .withFunctionName("CALC_DISCOUNT");   // H2 ALIAS is a function

        // Execute with named params
        Double result = calcCall.executeFunction(Double.class,
            new MapSqlParameterSource()
                .addValue("PRICE", 200.0)
                .addValue("PCT", 20));
        System.out.printf("20%% off $200.00 = $%.2f%n", result);

        // Second call — reuses compiled state
        result = calcCall.executeFunction(Double.class,
            new MapSqlParameterSource()
                .addValue("PRICE", 350.0)
                .addValue("PCT", 5));
        System.out.printf("5%% off $350.00 = $%.2f%n", result);

        // Procedure that returns scalar count
        SimpleJdbcCall countCall = new SimpleJdbcCall(ds)
            .withProcedureName("COUNT_TIERS");
        Map<String,Object> countOut = countCall.execute(Map.of("P_MIN_PRICE", 50.0));
        System.out.println("Tiers with min_price >= 50: " + countOut.get("P_COUNT"));
    }
}
```

`pricing-data.sql`:
```sql
INSERT INTO pricing_tiers(tier,min_price,pct) VALUES('Bronze',0,5);
INSERT INTO pricing_tiers(tier,min_price,pct) VALUES('Silver',50,10);
INSERT INTO pricing_tiers(tier,min_price,pct) VALUES('Gold',100,15);
```

`pricing-summary-proc.sql`:
```sql
CREATE ALIAS COUNT_TIERS AS $$
int countTiers(Connection c, double p_min_price) throws SQLException {
    PreparedStatement ps = c.prepareStatement(
        "SELECT COUNT(*) FROM pricing_tiers WHERE min_price >= ?");
    ps.setDouble(1, p_min_price);
    ResultSet rs = ps.executeQuery(); rs.next();
    return rs.getInt(1);
}
$$;
```

How to run: same classpath

`executeFunction(Double.class, params)` is the `SimpleJdbcCall` shorthand for a function that returns a value directly (vs. `execute()` which returns a `Map` of all OUT params). Parameter names must match the function signature — H2 uses uppercase for `ALIAS` parameter names.

---

### Level 3 — Advanced

`StoredProcedure` subclass with IN/OUT parameters + result-set mapping.

```java
// StoredProcDemo.java
import org.springframework.jdbc.core.*;
import org.springframework.jdbc.object.StoredProcedure;
import org.springframework.jdbc.datasource.embedded.*;
import javax.sql.DataSource;
import java.sql.*;
import java.util.*;

record PricingTier(String tier, double minPrice, int pct) {}

// StoredProcedure subclass — explicit parameter declaration, reusable object
class GetTiersForPrice extends StoredProcedure {
    private static final String PROC_NAME = "GET_TIERS_FOR_PRICE";

    GetTiersForPrice(DataSource ds) {
        super(ds, PROC_NAME);
        // IN parameter
        declareParameter(new SqlParameter("P_MAX_PRICE", Types.DOUBLE));
        // OUT parameter: scalar count
        declareParameter(new SqlOutParameter("P_COUNT", Types.INTEGER));
        // Result set (H2 returns it as a RefCursor or via special API)
        compile();
    }

    @SuppressWarnings("unchecked")
    public Map<String,Object> execute(double maxPrice) {
        Map<String,Object> params = new HashMap<>();
        params.put("P_MAX_PRICE", maxPrice);
        return execute(params);
    }
}

public class StoredProcDemo {

    static DataSource buildDs() {
        return new EmbeddedDatabaseBuilder()
            .setType(EmbeddedDatabaseType.H2)
            .addScript("classpath:pricing-schema.sql")
            .addScript("classpath:pricing-data.sql")
            .addScript("classpath:pricing-tiers-proc.sql")
            .build();
    }

    public static void main(String[] args) {
        DataSource ds = buildDs();
        GetTiersForPrice proc = new GetTiersForPrice(ds);

        // Call via SimpleJdbcCall (more flexible for result sets)
        SimpleJdbcCall call = new SimpleJdbcCall(ds)
            .withProcedureName("GET_TIERS_FOR_PRICE")
            .returningResultSet("tiers", BeanPropertyRowMapper.newInstance(PricingTier.class));
        // H2 ALIAS returning ResultSet — use returningResultSet
        // Note: H2 ALIAS can return a ResultSet directly

        // Demonstrate low-level JdbcTemplate.call with OUT + row mapping
        JdbcTemplate jdbc = new JdbcTemplate(ds);
        jdbc.query("SELECT tier, min_price, pct FROM pricing_tiers WHERE min_price <= ? ORDER BY min_price",
            (rs, n) -> new PricingTier(rs.getString("tier"), rs.getDouble("min_price"), rs.getInt("pct")),
            150.0)
        .forEach(t -> System.out.printf("  %-8s from $%.0f  %d%% discount%n",
            t.tier(), t.minPrice(), t.pct()));

        // SimpleJdbcCall for CALC_DISCOUNT
        SimpleJdbcCall discountFn = new SimpleJdbcCall(ds).withFunctionName("CALC_DISCOUNT");
        List<Double> prices = List.of(50.0, 100.0, 200.0, 500.0);
        System.out.println("\nPrice schedule (15% discount):");
        for (double p : prices) {
            double discounted = discountFn.executeFunction(Double.class,
                new org.springframework.jdbc.core.namedparam.MapSqlParameterSource()
                    .addValue("PRICE", p).addValue("PCT", 15));
            System.out.printf("  $%6.2f → $%6.2f%n", p, discounted);
        }
    }
}
```

`pricing-tiers-proc.sql`:
```sql
CREATE ALIAS GET_TIERS_FOR_PRICE AS $$
ResultSet getTiersForPrice(Connection c, double p_max_price) throws SQLException {
    PreparedStatement ps = c.prepareStatement(
        "SELECT tier, min_price, pct FROM pricing_tiers WHERE min_price <= ? ORDER BY min_price");
    ps.setDouble(1, p_max_price);
    return ps.executeQuery();
}
$$;
```

How to run: same classpath

`StoredProcedure.compile()` validates declared parameters; `execute(Map)` binds them. `SimpleJdbcCall.returningResultSet("key", rowMapper)` maps each row of a returned result set using the specified mapper — the result appears in the output `Map` under the key `"tiers"` as a `List<PricingTier>`.

## 6. Walkthrough

**Level 2 — `SimpleJdbcCall.executeFunction()` execution order:**

1. **`new SimpleJdbcCall(ds).withFunctionName("CALC_DISCOUNT")`**: configures the call target. No DB call yet.
2. **First `executeFunction(Double.class, params)`**: triggers metadata lookup — `DatabaseMetaData.getProcedureColumns(null, null, "CALC_DISCOUNT", null)` returns param list: `PRICE DOUBLE IN`, `PCT INTEGER IN` and return type `DOUBLE`.
3. **SQL built**: `{? = call CALC_DISCOUNT(?,?)}` — the leading `? =` captures the return value.
4. **`con.prepareCall("{? = call CALC_DISCOUNT(?,?)}")`**: JDBC driver prepares the call.
5. **Binding**:
   - Position 1: `cs.registerOutParameter(1, Types.DOUBLE)` — return value slot.
   - Position 2: `cs.setDouble(2, 200.0)` — PRICE.
   - Position 3: `cs.setInt(3, 20)` — PCT.
6. **`cs.execute()`**: database runs `CALC_DISCOUNT(200.0, 20)` → `200.0 * (1.0 - 20/100.0) = 160.0`. Stores result in position 1.
7. **Read OUT**: `cs.getDouble(1)` → `160.0`. `executeFunction` casts to `Double` and returns.

```
Call:     {? = call CALC_DISCOUNT(?,?)}
Params:   [OUT DOUBLE, 200.0, 20]
DB runs:  200.0 * (1 - 0.20) = 160.0
Result:   cs.getDouble(1) = 160.0
```

## 7. Gotchas & takeaways

> **`SimpleJdbcCall` is NOT thread-safe during configuration.** Build it once (in a `@Bean` or `@PostConstruct`) and never call `withProcedureName()` / `declareParameters()` after the first `execute()`. The metadata is cached in mutable internal state.

> **Parameter name case-sensitivity varies by database.** H2 stores ALIAS parameter names as uppercase; PostgreSQL lowercases by default; SQL Server is case-insensitive. Use `withoutProcedureColumnMetaDataAccess()` + explicit `declareParameters()` when metadata discovery gives wrong names.

> **Out parameter maps contain all registered OUT params plus special keys.** A result set is returned under `"#result-set-1"` by default or under whatever key you pass to `returningResultSet("key", mapper)`. Always specify `returningResultSet` when the procedure returns rows — otherwise the result set is silently skipped.

- `SimpleJdbcCall` — discovers params from metadata; simplest option for most procedures.
- `JdbcTemplate.call()` — raw JDBC; full control; verbose.
- `StoredProcedure` subclass — typed, reusable object; good for frequently called, documented procedures.
- `returningResultSet("key", rowMapper)` — maps result sets from the procedure to typed lists.
- `executeFunction()` — shorthand for scalar-returning functions.
