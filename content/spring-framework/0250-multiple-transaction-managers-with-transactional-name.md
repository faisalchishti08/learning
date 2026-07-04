---
card: spring-framework
gi: 250
slug: multiple-transaction-managers-with-transactional-name
title: Multiple transaction managers with @Transactional("name")
---

## 1. What it is

Spring allows multiple `PlatformTransactionManager` beans in the same application context. The `@Transactional` annotation's `transactionManager` attribute (or its alias `value`) selects which TM to use for a specific method:

```java
@Transactional("ordersTM")         // uses the ordersTM bean
public void placeOrder(Order o) { ... }

@Transactional("analyticsWriteTM") // uses a different TM
public void recordEvent(Event e) { ... }
```

Without a qualifier, `@Transactional` resolves the TM by looking for a bean named `"transactionManager"` (the conventional default name).

## 2. Why & when

Multiple TMs are needed when an application writes to more than one persistence technology or database instance:

- **JDBC + MongoDB** — one datasource TM + one Mongo TM.
- **Two databases** — `orders-db` and `analytics-db`, each needing their own `DataSourceTransactionManager`.
- **JDBC write path + read-replica read path** — primary TM for writes, read-only TM routing to a replica.
- **JPA + JMS** — a JPA TM for entity changes, a JMS TM for messaging (each resource manages its own local transaction).

Note: multiple local TMs do NOT provide distributed (XA) atomicity — for cross-resource atomicity you need `JtaTransactionManager`.

## 3. Core concept

`@EnableTransactionManagement` registers `AnnotationTransactionAttributeSource`, which parses `@Transactional`. When it resolves the TM:

1. If `transactionManager = "name"` is specified → look up that bean by name.
2. If blank → look up the bean named `"transactionManager"`.
3. If no bean named `"transactionManager"` and only one `PlatformTransactionManager` exists → use it.
4. If multiple TMs exist with no qualifier → throw `NoUniqueBeanDefinitionException`.

You can also implement `TransactionManagementConfigurer.annotationDrivenTransactionManager()` on a `@Configuration` class to set the default TM explicitly without relying on the conventional name.

## 4. Diagram

<svg viewBox="0 0 700 200" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <marker id="arr" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <polygon points="0 0,8 3,0 6" fill="#6db33f"/>
    </marker>
    <marker id="arr2" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <polygon points="0 0,8 3,0 6" fill="#79c0ff"/>
    </marker>
  </defs>

  <!-- Service -->
  <rect x="10" y="70" width="220" height="60" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="120" y="92" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">@Service OrderService</text>
  <text x="120" y="110" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">@Transactional("ordersTM")</text>
  <text x="120" y="123" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">placeOrder()</text>

  <line x1="232" y1="100" x2="285" y2="75" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>
  <line x1="232" y1="100" x2="285" y2="125" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#arr2)"/>

  <!-- TM1 -->
  <rect x="285" y="40" width="200" height="55" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="385" y="63" fill="#6db33f" font-size="10" text-anchor="middle" font-family="monospace">ordersTM</text>
  <text x="385" y="80" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">DataSourceTransactionManager(ordersDs)</text>

  <!-- TM2 -->
  <rect x="285" y="105" width="200" height="55" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="385" y="128" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="monospace">analyticsWriteTM</text>
  <text x="385" y="145" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">DataSourceTransactionManager(analyticsDs)</text>

  <!-- DBs -->
  <line x1="487" y1="67" x2="540" y2="67" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>
  <rect x="540" y="48" width="140" height="38" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="610" y="71" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">orders-db (PostgreSQL)</text>

  <line x1="487" y1="132" x2="540" y2="132" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#arr2)"/>
  <rect x="540" y="113" width="140" height="38" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="610" y="136" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">analytics-db (MySQL)</text>
</svg>

`@Transactional("ordersTM")` routes to the named TM bean; each TM manages its own datasource independently.

## 5. Runnable example

Scenario: an application with two in-memory H2 databases — **orders** and **analytics** — each with its own `DataSourceTransactionManager`.

### Level 1 — Basic

Two TMs, two datasources, `@Transactional` with explicit name.

```java
// MultiTMDemo.java
import org.springframework.context.annotation.*;
import org.springframework.jdbc.datasource.*;
import org.springframework.jdbc.datasource.embedded.*;
import org.springframework.transaction.*;
import org.springframework.transaction.annotation.*;
import org.springframework.stereotype.*;

@Configuration
@EnableTransactionManagement
@ComponentScan
public class MultiTMDemo {
    @Bean("ordersDs")
    public javax.sql.DataSource ordersDs() {
        return new EmbeddedDatabaseBuilder().setType(EmbeddedDatabaseType.H2)
            .setName("ordersDb")
            .addScript("orders-schema.sql").build();
    }

    @Bean("analyticsDs")
    public javax.sql.DataSource analyticsDs() {
        return new EmbeddedDatabaseBuilder().setType(EmbeddedDatabaseType.H2)
            .setName("analyticsDb")
            .addScript("analytics-schema.sql").build();
    }

    // Named "ordersTM" — used by @Transactional("ordersTM")
    @Bean("ordersTM")
    public PlatformTransactionManager ordersTM(
            @org.springframework.beans.factory.annotation.Qualifier("ordersDs") javax.sql.DataSource ds) {
        return new DataSourceTransactionManager(ds);
    }

    // Named "analyticsTM" — used by @Transactional("analyticsTM")
    @Bean("analyticsTM")
    public PlatformTransactionManager analyticsTM(
            @org.springframework.beans.factory.annotation.Qualifier("analyticsDs") javax.sql.DataSource ds) {
        return new DataSourceTransactionManager(ds);
    }

    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(MultiTMDemo.class);
        ctx.getBean(OrderService.class).placeOrder("ORD-1", "WIDGET", 3);
        ctx.close();
    }
}

@Service
class OrderService {
    private final org.springframework.jdbc.core.JdbcTemplate ordersJdbc;
    private final AnalyticsService analytics;

    OrderService(
        @org.springframework.beans.factory.annotation.Qualifier("ordersDs") javax.sql.DataSource ordersDs,
        AnalyticsService analytics) {
        this.ordersJdbc = new org.springframework.jdbc.core.JdbcTemplate(ordersDs);
        this.analytics = analytics;
    }

    @Transactional("ordersTM")   // uses orders-db TM
    public void placeOrder(String orderId, String item, int qty) {
        ordersJdbc.update("INSERT INTO orders(id,item,qty) VALUES(?,?,?)", orderId, item, qty);
        System.out.println("[ORDERS TX] inserted order " + orderId);
        analytics.record(orderId, item, qty);   // separate TM — its own local tx
    }
}

@Service
class AnalyticsService {
    private final org.springframework.jdbc.core.JdbcTemplate analyticsJdbc;

    AnalyticsService(
        @org.springframework.beans.factory.annotation.Qualifier("analyticsDs") javax.sql.DataSource analyticsDs) {
        this.analyticsJdbc = new org.springframework.jdbc.core.JdbcTemplate(analyticsDs);
    }

    @Transactional("analyticsTM")   // uses analytics-db TM — REQUIRES_NEW effectively
    public void record(String orderId, String item, int qty) {
        analyticsJdbc.update("INSERT INTO events(order_id,item,qty) VALUES(?,?,?)", orderId, item, qty);
        System.out.println("[ANALYTICS TX] recorded event for " + orderId);
    }
}
```

`orders-schema.sql`: `CREATE TABLE orders (id VARCHAR(20) PRIMARY KEY, item VARCHAR(50), qty INT);`
`analytics-schema.sql`: `CREATE TABLE events (id BIGINT AUTO_INCREMENT PRIMARY KEY, order_id VARCHAR(20), item VARCHAR(50), qty INT);`

How to run: `java -cp spring-context.jar:spring-jdbc.jar:h2.jar:. MultiTMDemo.java`

`placeOrder` uses `ordersTM` (orders-db). `record` uses `analyticsTM` (analytics-db). Each operates independently. If `record` fails, only the analytics write rolls back — the order commit is independent (they are different local transactions).

---

### Level 2 — Intermediate

Implementing `TransactionManagementConfigurer` to set a **default TM** and also use a named one.

```java
// MultiTMDemo.java
import org.springframework.context.annotation.*;
import org.springframework.jdbc.datasource.*;
import org.springframework.jdbc.datasource.embedded.*;
import org.springframework.transaction.*;
import org.springframework.transaction.annotation.*;
import org.springframework.stereotype.*;

@Configuration
@EnableTransactionManagement
@ComponentScan
public class MultiTMDemo implements TransactionManagementConfigurer {
    @Bean("ordersDs")
    public javax.sql.DataSource ordersDs() {
        return new EmbeddedDatabaseBuilder().setType(EmbeddedDatabaseType.H2)
            .setName("ordersDb2").addScript("orders-schema.sql").build();
    }
    @Bean("analyticsDs")
    public javax.sql.DataSource analyticsDs() {
        return new EmbeddedDatabaseBuilder().setType(EmbeddedDatabaseType.H2)
            .setName("analyticsDb2").addScript("analytics-schema.sql").build();
    }

    @Bean("ordersTM")
    public PlatformTransactionManager ordersTM(
            @org.springframework.beans.factory.annotation.Qualifier("ordersDs") javax.sql.DataSource ds) {
        return new DataSourceTransactionManager(ds);
    }

    @Bean("analyticsTM")
    public PlatformTransactionManager analyticsTM(
            @org.springframework.beans.factory.annotation.Qualifier("analyticsDs") javax.sql.DataSource ds) {
        return new DataSourceTransactionManager(ds);
    }

    @Override
    public PlatformTransactionManager annotationDrivenTransactionManager() {
        // @Transactional with no qualifier uses ordersTM as the default
        return ordersTM(ordersDs());
    }

    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(MultiTMDemo.class);
        ctx.getBean(OrderService.class).placeOrder("ORD-2", "GADGET", 1);
        ctx.close();
    }
}

@Service
class OrderService {
    private final org.springframework.jdbc.core.JdbcTemplate ordersJdbc;
    private final AnalyticsService analytics;
    OrderService(
        @org.springframework.beans.factory.annotation.Qualifier("ordersDs") javax.sql.DataSource ds,
        AnalyticsService analytics) {
        this.ordersJdbc = new org.springframework.jdbc.core.JdbcTemplate(ds); this.analytics = analytics;
    }

    @Transactional   // no qualifier → uses annotationDrivenTransactionManager() → ordersTM
    public void placeOrder(String orderId, String item, int qty) {
        ordersJdbc.update("INSERT INTO orders(id,item,qty) VALUES(?,?,?)", orderId, item, qty);
        System.out.println("[DEFAULT TM = ordersTM] inserted " + orderId);
        analytics.record(orderId, item, qty);
    }
}

@Service
class AnalyticsService {
    private final org.springframework.jdbc.core.JdbcTemplate analyticsJdbc;
    AnalyticsService(
        @org.springframework.beans.factory.annotation.Qualifier("analyticsDs") javax.sql.DataSource ds) {
        this.analyticsJdbc = new org.springframework.jdbc.core.JdbcTemplate(ds);
    }

    @Transactional("analyticsTM")   // explicit qualifier
    public void record(String orderId, String item, int qty) {
        analyticsJdbc.update("INSERT INTO events(order_id,item,qty) VALUES(?,?,?)", orderId, item, qty);
        System.out.println("[analyticsTM] recorded " + orderId);
    }
}
```

How to run: same classpath

`TransactionManagementConfigurer.annotationDrivenTransactionManager()` returns `ordersTM`. Any `@Transactional` without a qualifier in this context uses `ordersTM`. `AnalyticsService.record()` still explicitly uses `analyticsTM`.

---

### Level 3 — Advanced

Demonstrating **failure isolation** between TMs: analytics rollback does NOT roll back the orders transaction.

```java
// MultiTMDemo.java
import org.springframework.context.annotation.*;
import org.springframework.jdbc.datasource.*;
import org.springframework.jdbc.datasource.embedded.*;
import org.springframework.transaction.*;
import org.springframework.transaction.annotation.*;
import org.springframework.stereotype.*;

@Configuration
@EnableTransactionManagement
@ComponentScan
public class MultiTMDemo implements TransactionManagementConfigurer {
    @Bean("ordersDs") public javax.sql.DataSource ordersDs() {
        return new EmbeddedDatabaseBuilder().setType(EmbeddedDatabaseType.H2)
            .setName("ordersDb3").addScript("orders-schema.sql").build();
    }
    @Bean("analyticsDs") public javax.sql.DataSource analyticsDs() {
        return new EmbeddedDatabaseBuilder().setType(EmbeddedDatabaseType.H2)
            .setName("analyticsDb3").addScript("analytics-schema.sql").build();
    }
    @Bean("ordersTM") public PlatformTransactionManager ordersTM(
            @org.springframework.beans.factory.annotation.Qualifier("ordersDs") javax.sql.DataSource ds) {
        return new DataSourceTransactionManager(ds);
    }
    @Bean("analyticsTM") public PlatformTransactionManager analyticsTM(
            @org.springframework.beans.factory.annotation.Qualifier("analyticsDs") javax.sql.DataSource ds) {
        return new DataSourceTransactionManager(ds);
    }
    @Override public PlatformTransactionManager annotationDrivenTransactionManager() {
        return ordersTM(ordersDs());
    }

    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(MultiTMDemo.class);
        var svc = ctx.getBean(OrderService.class);
        var ordersJdbc = new org.springframework.jdbc.core.JdbcTemplate(
            ctx.getBean(javax.sql.DataSource.class, "ordersDs"));

        // Analytics fails — but order still commits
        try { svc.placeOrderWithFailingAnalytics("ORD-3", "PART", 5); }
        catch (Exception e) { System.out.println("Analytics failed: " + e.getMessage()); }

        var orders = ordersJdbc.queryForList("SELECT id FROM orders", String.class);
        System.out.println("Orders committed (despite analytics failure): " + orders);
        ctx.close();
    }
}

@Service
class OrderService {
    private final org.springframework.jdbc.core.JdbcTemplate ordersJdbc;
    private final AnalyticsService analytics;
    OrderService(
        @org.springframework.beans.factory.annotation.Qualifier("ordersDs") javax.sql.DataSource ds,
        AnalyticsService analytics) {
        this.ordersJdbc = new org.springframework.jdbc.core.JdbcTemplate(ds); this.analytics = analytics;
    }

    @Transactional   // ordersTM
    public void placeOrderWithFailingAnalytics(String orderId, String item, int qty) {
        ordersJdbc.update("INSERT INTO orders(id,item,qty) VALUES(?,?,?)", orderId, item, qty);
        System.out.println("[ORDERS TX] inserted " + orderId);
        try {
            analytics.recordFailing(orderId);   // fails — its own tx rolls back
        } catch (Exception e) {
            System.out.println("[ORDERS TX] analytics failed, continuing order commit");
        }
        // Orders tx commits despite analytics failure (different TMs!)
    }
}

@Service
class AnalyticsService {
    private final org.springframework.jdbc.core.JdbcTemplate analyticsJdbc;
    AnalyticsService(
        @org.springframework.beans.factory.annotation.Qualifier("analyticsDs") javax.sql.DataSource ds) {
        this.analyticsJdbc = new org.springframework.jdbc.core.JdbcTemplate(ds);
    }

    @Transactional("analyticsTM")
    public void recordFailing(String orderId) {
        analyticsJdbc.update("INSERT INTO events(order_id,item,qty) VALUES(?,?,?)", orderId, "FAIL", -1);
        throw new RuntimeException("Analytics DB constraint violation");
    }
}
```

How to run: same classpath

The `analytics` exception is caught inside `placeOrderWithFailingAnalytics`. The analytics transaction rolls back (its own). The orders transaction continues and commits. Final query confirms the order row is present despite the analytics failure.

## 6. Walkthrough

**Level 3 — two independent TM lifecycles:**

```
placeOrderWithFailingAnalytics("ORD-3","PART",5)
  ordersTM.getTransaction()  → conn_orders acquired, autoCommit=false

  INSERT orders [conn_orders]

  analytics.recordFailing("ORD-3")
    analyticsTM.getTransaction()  → conn_analytics acquired, autoCommit=false
    INSERT events [conn_analytics]
    throw RuntimeException
    analyticsTM.rollback()  → conn_analytics.rollback(); conn_analytics released

  catch: "[ORDERS TX] analytics failed, continuing"
  (orders tx still active on conn_orders)

  ordersTM.commit()  → conn_orders.commit(); conn_orders released

SELECT orders → ["ORD-3"]   ← committed ✓
```

## 7. Gotchas & takeaways

> **Two local TMs are NOT atomically coordinated.** If `analytics.record()` commits and the outer `ordersTM` then fails, the analytics event is persisted but the order is not. These are independent local transactions. Use `JtaTransactionManager` + XA datasources for cross-resource atomicity.

> **`@Transactional` with no qualifier throws `NoUniqueBeanDefinitionException` when multiple TMs exist and no `TransactionManagementConfigurer` or `"transactionManager"` bean is defined.** Always either name the default bean `"transactionManager"` or implement `TransactionManagementConfigurer`.

> **REQUIRES_NEW within the same TM works normally.** The qualifier selects the TM; propagation rules apply within each TM independently. Two `@Transactional("ordersTM")` methods calling each other will participate in / suspend the same orders connection.

- Qualifier syntax: `@Transactional("beanName")` — uses the TM with that bean name.
- Default TM resolution: bean named `"transactionManager"` or `TransactionManagementConfigurer`.
- Multiple TMs = independent local transactions per resource — no cross-resource atomicity.
- `JtaTransactionManager` is the only option for cross-resource atomicity (XA / 2PC).
