---
card: spring-data
gi: 89
slug: mybatis-integration
title: "MyBatis integration"
---

## 1. What it is

MyBatis is a persistence framework built around hand-written SQL mapped to Java objects via XML or annotation-based "mapper" definitions — a different philosophy entirely from both JPA (object-graph-first, SQL generated) and Spring Data JDBC (aggregate-oriented, SQL still generated, just more simply). Spring Data JDBC doesn't integrate with MyBatis directly, but a custom repository implementation (the same `<Repository>Impl` pattern used earlier) can delegate specific methods to a MyBatis `SqlSessionTemplate`, letting the two coexist in one application.

```java
interface OrderRepositoryCustom { List<OrderReportRow> runComplexReport(String status); }

class OrderRepositoryImpl implements OrderRepositoryCustom {
    @Autowired SqlSessionTemplate sqlSession;
    public List<OrderReportRow> runComplexReport(String status) {
        return sqlSession.selectList("com.example.mapper.OrderMapper.complexReport", status);
    }
}
```

## 2. Why & when

Every query mechanism covered in this section — derived methods, native `@Query`, `JdbcAggregateTemplate` — is Spring Data JDBC's own way of getting SQL executed. MyBatis is a genuinely separate persistence tool with its own strengths: hand-written, highly-tunable SQL with rich mapping control (nested result maps, dynamic SQL via `<if>`/`<choose>` XML tags), often preferred for complex reporting queries or when a team already has a large body of existing MyBatis mapper XML.

Reach for MyBatis integration alongside Spring Data JDBC specifically when:

- A specific query is complex enough (dynamic conditions, complex result-set shaping, deeply nested joins) that MyBatis's dynamic SQL and result-mapping features are a better fit than a native `@Query` string.
- Your organization already has a substantial investment in MyBatis mapper XML (e.g., migrating an existing MyBatis-based application incrementally onto Spring Data JDBC repositories) and wants to reuse that SQL rather than rewrite it.
- You want Spring Data JDBC's aggregate-oriented `CrudRepository` model for straightforward operations, but need an escape hatch to MyBatis specifically for one or two genuinely complex queries — the custom-implementation pattern lets both coexist on the same repository interface.

## 3. Core concept

```
 interface OrderRepository extends CrudRepository<Order, Long>,     -- Spring Data JDBC: simple CRUD
                                    OrderRepositoryCustom { }        -- MyBatis-backed: complex queries

 class OrderRepositoryImpl implements OrderRepositoryCustom {
     @Autowired SqlSessionTemplate sqlSession;   -- MyBatis's own execution mechanism
     public List<OrderReportRow> runComplexReport(String status) {
         return sqlSession.selectList("...OrderMapper.complexReport", status);  -- MyBatis mapper XML/annotation
     }
 }

 orderRepository.save(order)              -> Spring Data JDBC (JdbcAggregateTemplate)
 orderRepository.runComplexReport(status) -> MyBatis (SqlSessionTemplate + mapper XML)
 -- BOTH on the SAME repository interface, calling code doesn't need to know which is which
```

The same custom-implementation seam used for hand-written `EntityManager`/`JdbcAggregateTemplate` logic works equally well for delegating to an entirely different persistence framework.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.v3.org/2000/svg" role="img" aria-label="One repository interface routes simple operations to Spring Data JDBC and complex ones to a MyBatis-backed custom implementation">
  <rect x="220" y="10" width="200" height="45" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="320" y="37" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">OrderRepository</text>

  <rect x="30" y="95" width="230" height="55" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="145" y="117" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">save(), findById()</text>
  <text x="145" y="133" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">-&gt; Spring Data JDBC (simple CRUD)</text>

  <rect x="380" y="95" width="230" height="55" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="495" y="117" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">runComplexReport(status)</text>
  <text x="495" y="133" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">-&gt; MyBatis mapper XML</text>

  <line x1="280" y1="55" x2="170" y2="90" stroke="#8b949e" stroke-width="1.3" marker-end="url(#mb)"/>
  <line x1="360" y1="55" x2="470" y2="90" stroke="#8b949e" stroke-width="1.3" marker-end="url(#mb)"/>
  <defs><marker id="mb" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

One repository interface presents a unified API; underneath, simple methods use Spring Data JDBC while complex ones delegate to MyBatis.

## 5. Runnable example

The scenario: an order repository needing both simple CRUD and a complex, dynamically-built report query, evolving from Spring Data JDBC handling everything (showing where it strains), to a MyBatis-style dynamic query handling the complex case, to both coexisting on one repository interface.

### Level 1 — Basic

Show where a Spring Data JDBC-only approach starts to strain: a report query with several optional filter conditions, forcing a long chain of manual condition-building (or a very complex derived method name).

```java
import java.util.*;
import java.util.stream.*;

class Order { long id; String status; double total; String region; Order(long id, String status, double total, String region) { this.id = id; this.status = status; this.total = total; this.region = region; } }

public class MyBatisLevel1 {
    // Every optional-filter combination handled manually -- gets unwieldy fast as more filters are added.
    static List<Order> complexReport(List<Order> data, String status, Double minTotal, String region) {
        return data.stream()
            .filter(o -> status == null || o.status.equals(status))
            .filter(o -> minTotal == null || o.total >= minTotal)
            .filter(o -> region == null || o.region.equals(region))
            .collect(Collectors.toList());
    }

    public static void main(String[] args) {
        List<Order> orders = List.of(
            new Order(1, "SHIPPED", 50, "US"), new Order(2, "SHIPPED", 150, "EU"), new Order(3, "PENDING", 200, "US")
        );

        List<Order> result = complexReport(orders, "SHIPPED", 100.0, null);
        System.out.println("Filtered: " + result.size() + " order(s)");
        System.out.println("This pattern gets unwieldy fast as more optional filters and joins are added.");
    }
}
```

How to run: `java MyBatisLevel1.java`

Each optional filter needs its own `null`-guarded condition, chained manually — this works for three filters, but a real reporting query with a dozen optional conditions, several joins, and conditional column selection becomes genuinely hard to express and maintain this way, which is exactly the gap MyBatis's dynamic SQL is designed to fill.

### Level 2 — Intermediate

Model the same query as MyBatis-style dynamic SQL would express it — building the `WHERE` clause conditionally, closer to how a MyBatis mapper's `<where>`/`<if>` tags work.

```java
import java.util.*;
import java.util.stream.*;

class Order { long id; String status; double total; String region; Order(long id, String status, double total, String region) { this.id = id; this.status = status; this.total = total; this.region = region; } }

public class MyBatisLevel2 {
    // Simulates a MyBatis mapper's <where>/<if> dynamic SQL: build the WHERE clause TEXT conditionally.
    static String buildDynamicWhere(String status, Double minTotal, String region) {
        List<String> conditions = new ArrayList<>();
        if (status != null) conditions.add("status = '" + status + "'");
        if (minTotal != null) conditions.add("total >= " + minTotal);
        if (region != null) conditions.add("region = '" + region + "'");
        return conditions.isEmpty() ? "" : "WHERE " + String.join(" AND ", conditions);
    }

    static List<Order> complexReport(List<Order> data, String status, Double minTotal, String region) {
        String whereClause = buildDynamicWhere(status, minTotal, region);
        System.out.println("  SQL: SELECT * FROM orders " + whereClause);
        return data.stream()
            .filter(o -> status == null || o.status.equals(status))
            .filter(o -> minTotal == null || o.total >= minTotal)
            .filter(o -> region == null || o.region.equals(region))
            .collect(Collectors.toList());
    }

    public static void main(String[] args) {
        List<Order> orders = List.of(
            new Order(1, "SHIPPED", 50, "US"), new Order(2, "SHIPPED", 150, "EU"), new Order(3, "PENDING", 200, "US")
        );

        List<Order> result = complexReport(orders, "SHIPPED", 100.0, null);
        System.out.println("Filtered: " + result.size() + " order(s)");
    }
}
```

How to run: `java MyBatisLevel2.java`

`buildDynamicWhere` mirrors what a MyBatis mapper's `<where>`/`<if test="status != null">` XML tags generate at runtime: a `WHERE` clause assembled from only the conditions that actually have a value, printed here as `WHERE status = 'SHIPPED' AND total >= 100.0` — MyBatis handles this same conditional SQL-building declaratively in XML, rather than requiring hand-written Java string-building logic.

### Level 3 — Advanced

Combine both: a repository interface exposing simple CRUD (via a Spring Data JDBC-style path) and a complex report method (via a MyBatis-style custom implementation), matching the full integration pattern.

```java
import java.util.*;
import java.util.stream.*;

class Order { long id; String status; double total; String region; Order(long id, String status, double total, String region) { this.id = id; this.status = status; this.total = total; this.region = region; } }
record OrderReportRow(long id, String status, double total) {}

interface OrderRepositoryCustom { List<OrderReportRow> runComplexReport(String status, Double minTotal, String region); }

// class OrderRepositoryImpl implements OrderRepositoryCustom { @Autowired SqlSessionTemplate sqlSession; ... }
class OrderRepositoryImpl implements OrderRepositoryCustom {
    private final List<Order> data; // stands in for MyBatis's SqlSessionTemplate + mapper XML
    OrderRepositoryImpl(List<Order> data) { this.data = data; }

    public List<OrderReportRow> runComplexReport(String status, Double minTotal, String region) {
        List<String> conditions = new ArrayList<>();
        if (status != null) conditions.add("status = '" + status + "'");
        if (minTotal != null) conditions.add("total >= " + minTotal);
        if (region != null) conditions.add("region = '" + region + "'");
        String where = conditions.isEmpty() ? "" : "WHERE " + String.join(" AND ", conditions);
        System.out.println("  [MyBatis mapper] SELECT id, status, total FROM orders " + where);

        return data.stream()
            .filter(o -> status == null || o.status.equals(status))
            .filter(o -> minTotal == null || o.total >= minTotal)
            .filter(o -> region == null || o.region.equals(region))
            .map(o -> new OrderReportRow(o.id, o.status, o.total))
            .collect(Collectors.toList());
    }
}

// interface OrderRepository extends CrudRepository<Order, Long>, OrderRepositoryCustom { }
class OrderRepository implements OrderRepositoryCustom {
    private final Map<Long, Order> db = new HashMap<>();
    private final OrderRepositoryCustom custom;
    OrderRepository(List<Order> seedData) {
        for (Order o : seedData) db.put(o.id, o);
        this.custom = new OrderRepositoryImpl(seedData); // MyBatis-backed fragment
    }

    // Simple CRUD -- Spring Data JDBC style.
    Order save(Order order) { System.out.println("  [Spring Data JDBC] INSERT/UPDATE orders ..."); db.put(order.id, order); return order; }
    Optional<Order> findById(long id) { return Optional.ofNullable(db.get(id)); }

    // Complex report -- delegates to the MyBatis-backed custom fragment.
    public List<OrderReportRow> runComplexReport(String status, Double minTotal, String region) {
        return custom.runComplexReport(status, minTotal, region);
    }
}

public class MyBatisLevel3 {
    public static void main(String[] args) {
        List<Order> seed = List.of(
            new Order(1, "SHIPPED", 50, "US"), new Order(2, "SHIPPED", 150, "EU"), new Order(3, "PENDING", 200, "US")
        );
        OrderRepository repo = new OrderRepository(seed);

        // Simple operation -- Spring Data JDBC path.
        repo.save(new Order(4, "PENDING", 75, "US"));

        // Complex operation -- MyBatis path, on the SAME repository object.
        List<OrderReportRow> report = repo.runComplexReport("SHIPPED", 100.0, null);
        System.out.println("Report rows: " + report);
    }
}
```

How to run: `java MyBatisLevel3.java`

`repo.save(...)` prints "[Spring Data JDBC]" and `repo.runComplexReport(...)` prints "[MyBatis mapper]" — both are methods on the *same* `repo` object, and application code calling either never needs to know which persistence mechanism handles it underneath, exactly matching how a real `OrderRepository extends CrudRepository<Order, Long>, OrderRepositoryCustom` composes a Spring-Data-JDBC-backed interface with a MyBatis-backed custom fragment into one seamless API.

## 6. Walkthrough

Execution starts in `main` for Level 3. First, `repo` is constructed with three seed orders, and both its Spring-Data-JDBC-style `db` map and its MyBatis-style `OrderRepositoryImpl` fragment are initialized from the same seed data.

`repo.save(new Order(4, "PENDING", 75, "US"))` runs first: this prints "[Spring Data JDBC] INSERT/UPDATE orders ..." and adds the new order directly into `db` — a simple, direct operation with no dynamic SQL or complex condition-building involved, exactly the kind of operation Spring Data JDBC's generated `CrudRepository` methods handle well on their own.

Next, `repo.runComplexReport("SHIPPED", 100.0, null)` runs, delegating to `custom.runComplexReport(...)` on the `OrderRepositoryImpl` fragment. Inside, the `conditions` list collects `"status = 'SHIPPED'"` and `"total >= 100.0"` (since `status` and `minTotal` are non-null, but `region` is `null` and contributes nothing), producing the `WHERE` clause `"WHERE status = 'SHIPPED' AND total >= 100.0"`, which is printed as "[MyBatis mapper] SELECT id, status, total FROM orders WHERE status = 'SHIPPED' AND total >= 100.0". The stream filter then applies the same logic in-memory, matching only order 2 (`SHIPPED`, `total=150`) — order 1 (`SHIPPED`, `total=50`) fails the `total >= 100.0` condition, and order 3/4 fail the `status = 'SHIPPED'` condition. The resulting single-row report is printed.

```
repo.save(order4)                              -> [Spring Data JDBC] INSERT/UPDATE, db updated directly
repo.runComplexReport("SHIPPED", 100.0, null)   -> [MyBatis mapper] dynamic WHERE built -> filters in-memory
                                                    -> matches only order2 (SHIPPED, total=150)
```

In a real Spring Boot application integrating both, `OrderRepository extends CrudRepository<Order, Long>, OrderRepositoryCustom` is one Spring bean, auto-implemented partly by Spring Data JDBC (for `save`/`findById`/derived methods) and partly by the hand-written `OrderRepositoryImpl` (for `runComplexReport`, which internally calls `sqlSessionTemplate.selectList("com.example.mapper.OrderMapper.complexReport", paramsMap)` against a real MyBatis mapper XML file containing `<where>`/`<if>` dynamic SQL tags). A service class autowiring `OrderRepository` calls both kinds of methods identically — the seam between the two persistence mechanisms is invisible from the calling code's perspective, exactly as the custom-implementation pattern is designed to achieve.

## 7. Gotchas & takeaways

> Gotcha: mixing Spring Data JDBC and MyBatis in the same application means two separate connection/transaction-participation mechanisms exist side by side — both need to participate correctly in the same Spring-managed transaction (typically both do, via the shared `DataSource`/`PlatformTransactionManager`), but this is worth verifying explicitly rather than assuming, especially when a single business operation needs both a Spring Data JDBC save and a MyBatis query to succeed or fail together atomically.

- MyBatis is a genuinely separate persistence framework, not a Spring Data JDBC feature — integration happens through the same custom-repository-implementation pattern used for direct `JdbcAggregateTemplate`/`EntityManager` access.
- Reach for MyBatis specifically for complex, dynamically-built queries (many optional filters, complex result mapping) where its `<where>`/`<if>` dynamic SQL is a better fit than hand-built condition strings.
- Both mechanisms can coexist on one repository interface — simple CRUD via Spring Data JDBC, complex queries via a MyBatis-backed custom fragment — invisibly to calling code.
- Verify that both persistence mechanisms correctly participate in the same Spring-managed transaction when a business operation spans both.
