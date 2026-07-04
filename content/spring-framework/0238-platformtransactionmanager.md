---
card: spring-framework
gi: 238
slug: platformtransactionmanager
title: PlatformTransactionManager
---

## 1. What it is

`PlatformTransactionManager` is Spring's central transaction strategy interface. It defines three methods that every transaction manager — JDBC, JPA, JTA, MongoDB, R2DBC — must implement:

```java
public interface PlatformTransactionManager extends TransactionManager {
    TransactionStatus getTransaction(TransactionDefinition definition) throws TransactionException;
    void commit(TransactionStatus status) throws TransactionException;
    void rollback(TransactionStatus status) throws TransactionException;
}
```

It is the **strategy pattern** applied to transactions: the application code targets the interface; the concrete class provides the technology-specific implementation. All of Spring's declarative transaction support (`@Transactional`, `TransactionTemplate`) delegates to this interface.

## 2. Why & when

Every application that uses Spring transactions must declare exactly one (or occasionally more) `PlatformTransactionManager` bean. You pick the implementation that matches your persistence technology:

| Implementation | When to use |
|---|---|
| `DataSourceTransactionManager` | Spring JDBC / MyBatis on a JDBC `DataSource` |
| `JpaTransactionManager` | Spring Data JPA / Hibernate with `EntityManagerFactory` |
| `JtaTransactionManager` | XA / distributed transactions across multiple resources |
| `R2dbcTransactionManager` | Reactive (WebFlux) + R2DBC |
| `MongoTransactionManager` | MongoDB multi-document transactions |
| `ChainedTransactionManager` *(deprecated)* | Best-effort chaining of non-XA managers |

Declare it as a `@Bean` named `transactionManager` (Spring auto-detects by that name) or supply the bean name to `@Transactional("myTm")`.

## 3. Core concept

`getTransaction(TransactionDefinition)` does more than "open a transaction". It implements the **propagation** logic:

- If `REQUIRED` and a transaction already exists → **reuse it** (return existing `TransactionStatus`).
- If `REQUIRES_NEW` → **suspend** the existing transaction and start a new one.
- If `SUPPORTS` and no existing transaction → run without a transaction.

The concrete implementation acquires the physical resource (a JDBC `Connection`, an `EntityManager`, a Mongo session) and binds it to the current thread via `TransactionSynchronizationManager`. Every subsequent repository call within the same thread reuses the same bound resource.

`commit(status)` and `rollback(status)` release the resource and unbind it from the thread.

## 4. Diagram

<svg viewBox="0 0 680 200" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <marker id="arr" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <polygon points="0 0,8 3,0 6" fill="#6db33f"/>
    </marker>
  </defs>

  <!-- Interface -->
  <rect x="10" y="50" width="220" height="110" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="120" y="73" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">PlatformTransactionManager</text>
  <line x1="20" y1="82" x2="220" y2="82" stroke="#8b949e" stroke-width="0.5"/>
  <text x="120" y="100" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">getTransaction(definition)</text>
  <text x="120" y="118" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">commit(status)</text>
  <text x="120" y="136" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">rollback(status)</text>

  <!-- Arrow to impls -->
  <line x1="232" y1="105" x2="290" y2="105" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>
  <text x="261" y="98" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">implemented by</text>

  <!-- Implementations -->
  <rect x="290" y="20" width="210" height="170" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="395" y="42" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">Concrete Managers</text>
  <line x1="300" y1="50" x2="490" y2="50" stroke="#8b949e" stroke-width="0.5"/>
  <text x="395" y="70" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">DataSourceTransactionManager</text>
  <text x="395" y="88" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">JpaTransactionManager</text>
  <text x="395" y="106" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">JtaTransactionManager</text>
  <text x="395" y="124" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">R2dbcTransactionManager</text>
  <text x="395" y="142" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">MongoTransactionManager</text>
  <text x="395" y="175" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">+ custom implementations</text>

  <!-- Arrow to consumers -->
  <line x1="232" y1="130" x2="540" y2="160" stroke="#6db33f" stroke-width="1" stroke-dasharray="4,3" marker-end="url(#arr)"/>

  <!-- Consumers -->
  <rect x="540" y="130" width="130" height="55" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="605" y="150" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">@Transactional</text>
  <text x="605" y="166" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">TransactionTemplate</text>
  <text x="605" y="178" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">programmatic API</text>
</svg>

`PlatformTransactionManager` is the strategy; concrete managers implement it; `@Transactional` uses it.

## 5. Runnable example

Scenario: a **`SubscriptionService`** — first with `DataSourceTransactionManager`, then with `JpaTransactionManager`, then implementing a custom `PlatformTransactionManager` for learning purposes.

### Level 1 — Basic

`DataSourceTransactionManager` — the simplest common case.

```java
// PlatformTMDemo.java
import org.springframework.context.annotation.*;
import org.springframework.jdbc.datasource.*;
import org.springframework.jdbc.datasource.embedded.*;
import org.springframework.transaction.*;
import org.springframework.transaction.annotation.*;
import org.springframework.stereotype.*;

@Configuration
@EnableTransactionManagement
@ComponentScan
public class PlatformTMDemo {
    @Bean
    public javax.sql.DataSource dataSource() {
        return new EmbeddedDatabaseBuilder()
            .setType(EmbeddedDatabaseType.H2)
            .addScript("subs-schema.sql")
            .build();
    }

    @Bean
    public PlatformTransactionManager transactionManager(javax.sql.DataSource ds) {
        return new DataSourceTransactionManager(ds);
    }

    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(PlatformTMDemo.class);
        ctx.getBean(SubscriptionService.class).subscribe("user@example.com", "PRO");
        ctx.close();
    }
}

@Service
class SubscriptionService {
    private final org.springframework.jdbc.core.JdbcTemplate jdbc;
    SubscriptionService(javax.sql.DataSource ds) {
        this.jdbc = new org.springframework.jdbc.core.JdbcTemplate(ds);
    }

    @Transactional
    public void subscribe(String email, String plan) {
        jdbc.update("INSERT INTO subscriptions(email,plan) VALUES(?,?)", email, plan);
        jdbc.update("INSERT INTO audit_log(msg) VALUES(?)",
            "Subscribed " + email + " to " + plan);
        System.out.println("Subscription committed for " + email);
    }
}
```

`subs-schema.sql`:
```sql
CREATE TABLE subscriptions (id BIGINT AUTO_INCREMENT PRIMARY KEY, email VARCHAR(100), plan VARCHAR(50));
CREATE TABLE audit_log     (id BIGINT AUTO_INCREMENT PRIMARY KEY, msg VARCHAR(255));
```

How to run: `java -cp spring-context.jar:spring-jdbc.jar:h2.jar:. PlatformTMDemo.java`

`DataSourceTransactionManager` binds a single `Connection` to the thread. Both `INSERT` statements share it. On commit, H2 atomically persists both rows.

---

### Level 2 — Intermediate

**`JpaTransactionManager`** — same service, JPA/Hibernate backend. Business logic unchanged.

```java
// PlatformTMDemo.java
import org.springframework.context.annotation.*;
import org.springframework.jdbc.datasource.embedded.*;
import org.springframework.orm.jpa.*;
import org.springframework.transaction.annotation.*;
import org.springframework.stereotype.*;
import jakarta.persistence.*;

@Configuration
@EnableTransactionManagement
@ComponentScan
public class PlatformTMDemo {
    @Bean
    public javax.sql.DataSource dataSource() {
        return new EmbeddedDatabaseBuilder()
            .setType(EmbeddedDatabaseType.H2).build();
    }

    @Bean
    public LocalContainerEntityManagerFactoryBean emf(javax.sql.DataSource ds) {
        var emf = new LocalContainerEntityManagerFactoryBean();
        emf.setDataSource(ds);
        emf.setPackagesToScan("com.example");
        emf.setJpaVendorAdapter(new org.springframework.orm.jpa.vendor.HibernateJpaVendorAdapter());
        var props = new java.util.Properties();
        props.put("hibernate.hbm2ddl.auto", "create-drop");
        props.put("hibernate.dialect", "org.hibernate.dialect.H2Dialect");
        emf.setJpaProperties(props);
        return emf;
    }

    @Bean
    public PlatformTransactionManager transactionManager(EntityManagerFactory emf) {
        return new JpaTransactionManager(emf);    // ← only this line changes vs JDBC version
    }

    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(PlatformTMDemo.class);
        ctx.getBean(SubscriptionService.class).subscribe("jpa@example.com", "ENTERPRISE");
        ctx.close();
    }
}

@Entity
@Table(name = "subscriptions")
class Subscription {
    @Id @GeneratedValue Long id;
    String email;
    String plan;
    Subscription() {}
    Subscription(String email, String plan) { this.email=email; this.plan=plan; }
}

@Service
class SubscriptionService {
    @PersistenceContext EntityManager em;

    @Transactional
    public void subscribe(String email, String plan) {
        em.persist(new Subscription(email, plan));
        System.out.println("JPA subscription committed for " + email);
    }
}
```

How to run: `java -cp spring-context.jar:spring-orm.jar:hibernate-core.jar:jakarta.persistence-api.jar:h2.jar:. PlatformTMDemo.java`

Only the `@Bean transactionManager` changes. The `SubscriptionService` is identical in structure. `JpaTransactionManager` binds an `EntityManager` (Hibernate Session) to the thread instead of a raw `Connection`.

---

### Level 3 — Advanced

**Custom `PlatformTransactionManager`** — a no-op in-memory implementation for testing/understanding the contract.

```java
// PlatformTMDemo.java
import org.springframework.context.annotation.*;
import org.springframework.transaction.*;
import org.springframework.transaction.support.*;
import org.springframework.transaction.annotation.*;
import org.springframework.stereotype.*;

@Configuration
@EnableTransactionManagement
@ComponentScan
public class PlatformTMDemo {
    @Bean
    public PlatformTransactionManager transactionManager() {
        return new InMemoryTransactionManager();
    }

    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(PlatformTMDemo.class);
        ctx.getBean(SubscriptionService.class).subscribe("custom@example.com", "FREE");
        ctx.close();
    }
}

class InMemoryTransactionManager extends AbstractPlatformTransactionManager {
    private final java.util.Deque<String> log = new java.util.ArrayDeque<>();

    @Override
    protected Object doGetTransaction() {
        return new Object();   // transaction object (could hold connection/session)
    }

    @Override
    protected void doBegin(Object transaction, TransactionDefinition definition) {
        log.push("BEGIN[" + definition.getPropagationBehaviorName() + "]");
        System.out.println("[TX] " + log.peek());
    }

    @Override
    protected void doCommit(DefaultTransactionStatus status) {
        System.out.println("[TX] COMMIT");
    }

    @Override
    protected void doRollback(DefaultTransactionStatus status) {
        System.out.println("[TX] ROLLBACK");
    }
}

@Service
class SubscriptionService {
    @Transactional
    public void subscribe(String email, String plan) {
        System.out.println("Processing subscription: " + email + " → " + plan);
        // No actual DB — demonstrates the TM contract
    }
}
```

How to run: `java -cp spring-context.jar:spring-tx.jar:. PlatformTMDemo.java`

`AbstractPlatformTransactionManager` handles the propagation, synchronization, and rollback-on-exception scaffolding. Subclasses only implement `doGetTransaction`, `doBegin`, `doCommit`, `doRollback`. This is how all of Spring's concrete managers are built.

## 6. Walkthrough

**`@Transactional subscribe()` call path (Level 1):**

1. The proxy intercepts `subscriptionService.subscribe(...)`.
2. `TransactionInterceptor.invoke()` calls `txManager.getTransaction(txAttr)`.
3. `DataSourceTransactionManager.doGetTransaction()` creates a `DataSourceTransactionObject`.
4. `doBegin()`: `DataSourceUtils.getConnection(ds)` borrows a connection; sets `autoCommit=false`; binds connection to `TransactionSynchronizationManager` ThreadLocal.
5. `subscribe()` body runs: both `JdbcTemplate.update()` calls pull the thread-bound connection and execute SQL.
6. `subscribe()` returns normally → `TransactionInterceptor` calls `txManager.commit(status)`.
7. `doCommit()`: `connection.commit()` → `connection.setAutoCommit(true)` → release to pool → clear ThreadLocal.

**State trace:**

```
Request:  subscribe("user@example.com", "PRO")
  ↓ proxy intercept
  ↓ getTransaction() → connection bound to ThreadLocal
  ↓ INSERT subscriptions (uses bound connection)
  ↓ INSERT audit_log   (uses SAME bound connection)
  ↓ commit(status)
     → connection.commit()         ← both rows committed atomically
     → connection released to pool
     → ThreadLocal cleared
Response: void
```

**Level 3 — `AbstractPlatformTransactionManager` delegation:**

```
@Transactional subscribe()
  → TransactionInterceptor.invoke()
    → AbstractPlatformTransactionManager.getTransaction()
       → doGetTransaction()  → returns Object (TxObject)
       → doBegin(txObj, def) → prints "[TX] BEGIN[REQUIRED]"
    → subscribe() body
    → commit(status)
       → doCommit(status)    → prints "[TX] COMMIT"
```

## 7. Gotchas & takeaways

> **`JpaTransactionManager` and `DataSourceTransactionManager` must NOT share the same `DataSource` without coordination.** JPA/Hibernate gets connections from the `DataSource` internally; if `DataSourceTransactionManager` also binds a connection to the thread, they will use different connections and be in different transactions. Use `JpaTransactionManager` exclusively with JPA.

> **The bean name `transactionManager` is special.** `@EnableTransactionManagement` auto-detects it. If you name your bean differently (e.g., `"myTm"`), you must use `@Transactional("myTm")` everywhere — or configure `@EnableTransactionManagement(transactionManagerBeanName = "myTm")`.

- `PlatformTransactionManager` is the single point you swap to change the underlying transaction technology.
- All Spring transaction support (`@Transactional`, `TransactionTemplate`, `TransactionCallback`) delegates to this interface.
- `AbstractPlatformTransactionManager` is the base class for all Spring-provided implementations — it handles propagation, synchronization, and rollback-only marking.
- Multiple TMs are valid: declare two `@Bean` methods with different names and reference them in `@Transactional("beanName")`.
