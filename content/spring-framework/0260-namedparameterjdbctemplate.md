---
card: spring-framework
gi: 260
slug: namedparameterjdbctemplate
title: NamedParameterJdbcTemplate
---

## 1. What it is

`NamedParameterJdbcTemplate` wraps `JdbcTemplate` and replaces positional `?` placeholders with **named placeholders** — `:paramName` — in SQL strings. Parameters are bound by name via a `Map<String, Object>` or a `SqlParameterSource` rather than by position.

```java
// positional — error-prone with 4+ params
jdbc.update("INSERT INTO users(name,age,dept,role) VALUES(?,?,?,?)", "Alice", 30, "Eng", "Dev");

// named — readable and safe to reorder
namedJdbc.update(
    "INSERT INTO users(name,age,dept,role) VALUES(:name,:age,:dept,:role)",
    Map.of("name","Alice","age",30,"dept","Eng","role","Dev")
);
```

The class lives in `org.springframework.jdbc.core.namedparam`.

## 2. Why & when

With positional `?` parameters, adding or reordering a column in an INSERT requires counting and reordering every argument — one slip silently inserts the wrong value in the wrong column. Named parameters eliminate that class of bug.

Use `NamedParameterJdbcTemplate` when:
- SQL has **three or more parameters** (readability pays off immediately).
- Parameters come from a **Map or domain object** (`BeanPropertySqlParameterSource`).
- SQL is **re-used across methods** with different subsets of the same parameter map.
- You write **`IN (:ids)` clauses** with a collection — only this template handles that expansion automatically.

Keep plain `JdbcTemplate` for DDL, scalar queries, or code where all params fit on one line.

## 3. Core concept

`NamedParameterJdbcTemplate` delegates all real work to an internal `JdbcTemplate`:

1. **Parse SQL** — scan for `:paramName` tokens, replace each with `?`, record name→index mapping.
2. **Bind** — walk the index map; pull each value out of the `SqlParameterSource` by name and call the appropriate `PreparedStatement.setXxx()`.
3. **Execute** — hand the rewritten SQL and bound `PreparedStatement` to the underlying `JdbcTemplate`.

Two `SqlParameterSource` implementations:

| Class | Use |
|---|---|
| `MapSqlParameterSource` | Fluent builder from a `Map`; supports chaining `.addValue("k", v)`. |
| `BeanPropertySqlParameterSource` | Wraps a Java bean; reads property getters as param values by name. |

`IN` clause expansion: pass a `List` as a value and `NamedParameterUtils.substituteNamedParameters` expands `:ids` → `(?,?,?)` automatically.

## 4. Diagram

<svg viewBox="0 0 700 220" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <marker id="arr" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <polygon points="0 0,8 3,0 6" fill="#6db33f"/>
    </marker>
  </defs>

  <!-- Your code -->
  <rect x="10" y="85" width="130" height="50" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="75" y="107" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Your Code</text>
  <text x="75" y="122" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">sql + Map/Source</text>

  <line x1="142" y1="110" x2="195" y2="110" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>

  <!-- NP template -->
  <rect x="195" y="40" width="200" height="140" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="295" y="62" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">NamedParameterJdbcTemplate</text>
  <line x1="205" y1="70" x2="385" y2="70" stroke="#8b949e" stroke-width="0.5"/>
  <text x="295" y="90" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">1. parse :name → ?</text>
  <text x="295" y="108" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">2. build name→index map</text>
  <text x="295" y="126" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">3. bind values by name</text>
  <text x="295" y="144" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">4. delegate to JdbcTemplate</text>
  <text x="295" y="162" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="monospace">expands IN (:list) → (?,?,?)</text>

  <line x1="397" y1="110" x2="450" y2="110" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>

  <!-- JdbcTemplate -->
  <rect x="450" y="85" width="120" height="50" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="510" y="107" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">JdbcTemplate</text>
  <text x="510" y="122" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">+ DataSource</text>

  <!-- result -->
  <line x1="510" y1="195" x2="510" y2="138" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>
  <text x="530" y="198" fill="#8b949e" font-size="8" font-family="sans-serif">result</text>
</svg>

Named SQL is parsed once; `?`-rewritten SQL is handed to the underlying `JdbcTemplate` for execution.

## 5. Runnable example

Scenario: an **employee directory** — insert employees, query by department, and find by a list of IDs, using named parameters throughout.

### Level 1 — Basic

Named parameters in INSERT and SELECT with `MapSqlParameterSource`.

```java
// NamedParamDemo.java
import org.springframework.jdbc.core.namedparam.*;
import org.springframework.jdbc.datasource.embedded.*;
import javax.sql.DataSource;
import java.util.List;
import java.util.Map;

public class NamedParamDemo {

    static DataSource buildDs() {
        return new EmbeddedDatabaseBuilder()
            .setType(EmbeddedDatabaseType.H2)
            .addScript("classpath:emp-schema.sql")
            .build();
    }

    public static void main(String[] args) {
        var nj = new NamedParameterJdbcTemplate(buildDs());

        // INSERT with named params — order in SQL doesn't have to match Map key order
        String insert = "INSERT INTO employees(name, dept, salary) VALUES(:name,:dept,:salary)";
        nj.update(insert, Map.of("name", "Alice", "dept", "Engineering", "salary", 95000));
        nj.update(insert, Map.of("name", "Bob",   "dept", "Engineering", "salary", 88000));
        nj.update(insert, Map.of("name", "Carol",  "dept", "Marketing",   "salary", 72000));

        // SELECT with one named param
        String q = "SELECT name FROM employees WHERE dept = :dept ORDER BY name";
        List<String> eng = nj.queryForList(q, Map.of("dept", "Engineering"), String.class);
        System.out.println("Engineering: " + eng);   // [Alice, Bob]

        // Scalar aggregate
        Integer count = nj.queryForObject(
            "SELECT COUNT(*) FROM employees WHERE salary >= :min",
            Map.of("min", 80000), Integer.class);
        System.out.println("Earners >= 80k: " + count);  // 2
    }
}
```

`emp-schema.sql`: `CREATE TABLE employees (id BIGINT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(100), dept VARCHAR(80), salary INT);`

How to run: `java -cp spring-context.jar:spring-jdbc.jar:h2.jar:. NamedParamDemo.java`

`NamedParameterJdbcTemplate` accepts a plain `Map<String, ?>` directly — it wraps it in a `MapSqlParameterSource` internally. Named parameters make it obvious which value maps to which column even with many parameters.

---

### Level 2 — Intermediate

`BeanPropertySqlParameterSource` — bind directly from a Java record.

```java
// NamedParamDemo.java
import org.springframework.jdbc.core.namedparam.*;
import org.springframework.jdbc.datasource.embedded.*;
import javax.sql.DataSource;
import java.util.List;
import java.util.Map;

record Employee(long id, String name, String dept, int salary) {}

public class NamedParamDemo {

    static DataSource buildDs() {
        return new EmbeddedDatabaseBuilder()
            .setType(EmbeddedDatabaseType.H2)
            .addScript("classpath:emp-schema.sql")
            .build();
    }

    public static void main(String[] args) {
        var nj = new NamedParameterJdbcTemplate(buildDs());

        // BeanPropertySqlParameterSource reads record accessors as named params
        String insert = "INSERT INTO employees(name,dept,salary) VALUES(:name,:dept,:salary)";
        for (var e : List.of(
                new Employee(0,"Diana","Engineering",102000),
                new Employee(0,"Eve","Design",79000),
                new Employee(0,"Frank","Engineering",91000))) {
            nj.update(insert, new BeanPropertySqlParameterSource(e));
        }

        // IN clause — pass a List; Spring expands :ids → (?,?,?)
        List<Integer> ids = List.of(1, 3);
        String inQ = "SELECT name FROM employees WHERE id IN (:ids) ORDER BY id";
        List<String> names = nj.queryForList(inQ, Map.of("ids", ids), String.class);
        System.out.println("IDs 1,3: " + names);  // [Diana, Frank]

        // MapSqlParameterSource — fluent builder, useful for complex queries
        var params = new MapSqlParameterSource()
            .addValue("dept", "Engineering")
            .addValue("minSalary", 95000);
        List<String> seniors = nj.queryForList(
            "SELECT name FROM employees WHERE dept=:dept AND salary>=:minSalary",
            params, String.class);
        System.out.println("Senior Engineering: " + seniors);
    }
}
```

How to run: same classpath

`BeanPropertySqlParameterSource(employee)` uses reflection to call `employee.name()`, `employee.dept()`, `employee.salary()` and expose them as named parameters `:name`, `:dept`, `:salary`. The `IN (:ids)` syntax works only with `NamedParameterJdbcTemplate` — plain `JdbcTemplate` cannot expand a collection.

---

### Level 3 — Advanced

Batch named-parameter inserts with `SqlParameterSource[]` + full `RowMapper` mapping.

```java
// NamedParamDemo.java
import org.springframework.jdbc.core.*;
import org.springframework.jdbc.core.namedparam.*;
import org.springframework.jdbc.datasource.embedded.*;
import javax.sql.DataSource;
import java.util.*;

record Employee(long id, String name, String dept, int salary) {}

public class NamedParamDemo {

    static final RowMapper<Employee> EMP_MAPPER = (rs, n) -> new Employee(
        rs.getLong("id"), rs.getString("name"),
        rs.getString("dept"), rs.getInt("salary"));

    static DataSource buildDs() {
        return new EmbeddedDatabaseBuilder()
            .setType(EmbeddedDatabaseType.H2)
            .addScript("classpath:emp-schema.sql")
            .build();
    }

    public static void main(String[] args) {
        var nj = new NamedParameterJdbcTemplate(buildDs());

        // Batch insert via SqlParameterSource[]
        List<Employee> batch = List.of(
            new Employee(0,"Grace","HR",65000),
            new Employee(0,"Heidi","Engineering",98000),
            new Employee(0,"Ivan","Marketing",71000),
            new Employee(0,"Judy","Design",82000),
            new Employee(0,"Ken","HR",67000)
        );
        SqlParameterSource[] sources = batch.stream()
            .map(BeanPropertySqlParameterSource::new)
            .toArray(SqlParameterSource[]::new);

        int[] counts = nj.batchUpdate(
            "INSERT INTO employees(name,dept,salary) VALUES(:name,:dept,:salary)", sources);
        System.out.println("Batch inserted: " + counts.length + " rows");

        // Multi-condition query with IN + range
        var params = new MapSqlParameterSource()
            .addValue("depts", List.of("Engineering", "Design"))
            .addValue("minSal", 80000);
        List<Employee> result = nj.query(
            "SELECT * FROM employees WHERE dept IN (:depts) AND salary >= :minSal ORDER BY salary DESC",
            params, EMP_MAPPER);
        System.out.println("Senior Engineering/Design:");
        result.forEach(e -> System.out.printf("  %-10s %-12s $%,d%n", e.name(), e.dept(), e.salary()));

        // UPDATE — raise salaries 5% for a dept
        int updated = nj.update(
            "UPDATE employees SET salary = ROUND(salary * 1.05) WHERE dept = :dept",
            Map.of("dept", "Engineering"));
        System.out.println("Raised salaries for " + updated + " Engineering employees");
    }
}
```

How to run: same classpath

`batchUpdate(sql, SqlParameterSource[])` is the named-parameter counterpart of `JdbcTemplate.batchUpdate(sql, List<Object[]>)` — it sends all rows in one batch but binds by name from each source. The `IN (:depts)` expansion works with `List.of("Engineering","Design")` — Spring rewrites it to `IN (?,?)` and binds both values.

## 6. Walkthrough

**Level 3 execution order — batch insert then IN-clause query:**

1. **`batchUpdate` call**: `nj.batchUpdate(sql, sources)` is called with 5 `BeanPropertySqlParameterSource` items.
2. **SQL parsing**: `NamedParameterUtils.parseSqlStatement(sql)` scans `:name`, `:dept`, `:salary`, builds `ParsedSql` with index positions `[1,2,3]` and rewrites to `INSERT INTO employees(name,dept,salary) VALUES(?,?,?)`.
3. **Batch execution**: for each `SqlParameterSource` in `sources`, values are extracted by name — `source.getValue("name")` → `"Grace"`, etc. — and bound to the `PreparedStatement` in position order.
4. **DB round-trip**: all 5 bind→execute cycles run inside one JDBC batch; H2 inserts 5 rows. `counts[i]` = 1 for each.
5. **IN-clause query**: `nj.query(sql, params, EMP_MAPPER)` is called. `params` contains `depts=["Engineering","Design"]` and `minSal=80000`.
6. **Expansion**: `NamedParameterUtils.substituteNamedParameters` detects that `:depts` value is a `Collection`, rewrites to `WHERE dept IN (?,?) AND salary >= ?`, binds `"Engineering"`, `"Design"`, `80000`.
7. **`JdbcTemplate.query`**: underlying `JdbcTemplate` runs the rewritten SQL. H2 returns rows for Heidi (Engineering, 98000) and Judy (Design, 82000).
8. **RowMapper**: `EMP_MAPPER.mapRow(rs, n)` is called per row → `List<Employee>` returned.
9. **UPDATE**: `:dept` → `"Engineering"`, updates Heidi and any others. `update()` returns affected row count.

**Request/response trace:**

```
JDBC batch — INSERT
  SQL sent to DB: INSERT INTO employees(name,dept,salary) VALUES(?,?,?) [×5]
  DB response:    update-count=[1,1,1,1,1]

JDBC query — SELECT with IN expansion
  SQL sent to DB: SELECT * FROM employees
                  WHERE dept IN (?,?) AND salary >= ?
                  ORDER BY salary DESC
  Params:         ["Engineering","Design", 80000]
  DB response:    2 rows → Heidi(98000), Judy(82000)
```

## 7. Gotchas & takeaways

> **`IN (:list)` only works with `NamedParameterJdbcTemplate`.** If you pass a `Collection` as a positional `?` argument to plain `JdbcTemplate`, JDBC will throw a type-mismatch error. Always use named parameters for `IN` clauses.

> **`BeanPropertySqlParameterSource` reads Java bean conventions.** A Java record exposes `name()` not `getName()`, but Spring handles both. Watch out: a property named `type` may conflict with JDBC type resolution — use `MapSqlParameterSource` and rename the key in that case.

- Named `:param` replaces positional `?` — readable at scale, immune to reordering bugs.
- `Map<String,?>` is the quickest way to pass params; `BeanPropertySqlParameterSource` eliminates boilerplate for domain objects.
- `IN (:collection)` is automatically expanded to the right number of `?` placeholders.
- `batchUpdate(sql, SqlParameterSource[])` gives named-param batch inserts.
- `NamedParameterJdbcTemplate` holds a `JdbcTemplate` internally — call `getJdbcTemplate()` when you need to mix named and positional operations.
