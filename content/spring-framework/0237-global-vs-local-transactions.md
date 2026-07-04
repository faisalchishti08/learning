---
card: spring-framework
gi: 237
slug: global-vs-local-transactions
title: Global vs local transactions
---

## 1. What it is

A **local transaction** is managed by a single resource — typically a JDBC `Connection` or an JPA `EntityManager`. It can only span operations on that one database. A **global transaction** (also called a distributed transaction or JTA transaction) is managed by a **transaction manager** that coordinates multiple resources — two databases, a database and a JMS queue, etc. — using the **two-phase commit (2PC)** protocol.

```
Local:   TM = DataSource connection.commit()
Global:  TM = JTA UserTransaction → coordinates DB1 + MQ1 via XA
```

Spring's `PlatformTransactionManager` abstraction works for both: swap the implementation bean to switch from local to global.

## 2. Why & when

| | Local | Global (JTA) |
|---|---|---|
| Resources spanned | 1 | Multiple (DB + DB, DB + MQ, …) |
| Coordinator | The database | JTA Transaction Manager (Atomikos, Narayana, app server) |
| Performance | Low overhead | Higher overhead (XA protocol, network round-trips) |
| Failure recovery | Simple | Durable log + recovery manager |
| JDBC driver requirement | Standard | XA-capable `javax.sql.XADataSource` |
| Use when | Single-DB apps (99% of apps) | Cross-resource atomicity required |

Most applications never need JTA. The moment you need "debit DB and enqueue MQ atomically", you need JTA — or an alternative pattern like the outbox pattern.

## 3. Core concept

**Local transaction** lifecycle:

1. `DataSourceTransactionManager.getTransaction()` borrows a single `Connection`, sets `autoCommit=false`.
2. All repository calls use the same `Connection` (thread-bound).
3. `commit()` / `rollback()` calls `connection.commit()` / `rollback()`.

**Global/JTA transaction** lifecycle:

1. `JtaTransactionManager.getTransaction()` calls `UserTransaction.begin()` on the JTA TM.
2. JTA TM generates a global transaction ID (XID).
3. Each participating resource (XA datasource, XA connection factory) enlists with the XTA TM when first used in the transaction.
4. On commit, the JTA TM runs **2PC**: Phase 1 — each resource votes (`prepare`); Phase 2 — if all voted YES, all commit (`commit`); if any voted NO, all rollback.

Spring's `JtaTransactionManager` delegates to the container's or embedded JTA provider's `UserTransaction`.

## 4. Diagram

<svg viewBox="0 0 700 240" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <marker id="arr" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <polygon points="0 0,8 3,0 6" fill="#6db33f"/>
    </marker>
    <marker id="arr2" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <polygon points="0 0,8 3,0 6" fill="#79c0ff"/>
    </marker>
  </defs>

  <!-- Local TX -->
  <text x="160" y="22" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">Local Transaction</text>
  <rect x="40" y="35" width="130" height="40" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="105" y="59" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">DataSourceTM</text>
  <line x1="172" y1="55" x2="225" y2="55" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>
  <rect x="225" y="35" width="90" height="40" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="270" y="52" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Single DB</text>
  <text x="270" y="66" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">1 connection</text>

  <!-- Global TX -->
  <text x="500" y="22" fill="#79c0ff" font-size="12" text-anchor="middle" font-family="sans-serif">Global (JTA) Transaction</text>
  <rect x="380" y="35" width="120" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="440" y="59" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">JtaTransactionManager</text>

  <!-- JTA to resources -->
  <line x1="502" y1="45" x2="560" y2="30" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#arr2)"/>
  <line x1="502" y1="65" x2="560" y2="90" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#arr2)"/>
  <line x1="502" y1="55" x2="560" y2="145" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#arr2)"/>

  <rect x="560" y="10" width="120" height="35" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="620" y="32" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">XA Database A</text>

  <rect x="560" y="72" width="120" height="35" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="620" y="94" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">XA Database B</text>

  <rect x="560" y="127" width="120" height="35" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="620" y="149" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">XA JMS Queue</text>

  <!-- 2PC label -->
  <rect x="380" y="100" width="170" height="40" rx="5" fill="#0d1117" stroke="#6db33f" stroke-width="1"/>
  <text x="465" y="118" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">2PC: prepare → vote → commit</text>
  <text x="465" y="133" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">or rollback all on failure</text>
</svg>

Local: one DB, one connection. Global: JTA coordinates multiple XA resources via two-phase commit.

## 5. Runnable example

Scenario: a **`PaymentProcessor`** that debits a bank account — first as a local JDBC transaction, then simulating a global transaction with two datasources using Atomikos.

### Level 1 — Basic

Local JDBC transaction: `DataSourceTransactionManager` + single H2 database.

```java
// GlobalLocalTxDemo.java
import org.springframework.context.annotation.*;
import org.springframework.jdbc.datasource.*;
import org.springframework.jdbc.datasource.embedded.*;
import org.springframework.transaction.*;
import org.springframework.transaction.annotation.*;
import org.springframework.stereotype.*;

@Configuration
@EnableTransactionManagement
@ComponentScan
public class GlobalLocalTxDemo {
    @Bean
    public javax.sql.DataSource dataSource() {
        return new EmbeddedDatabaseBuilder()
            .setType(EmbeddedDatabaseType.H2)
            .addScript("payments-schema.sql")
            .build();
    }

    @Bean
    public PlatformTransactionManager transactionManager(javax.sql.DataSource ds) {
        return new DataSourceTransactionManager(ds);   // LOCAL transaction
    }

    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(GlobalLocalTxDemo.class);
        var svc = ctx.getBean(PaymentProcessor.class);
        svc.process("ACC-1", "ACC-2", 500.0);
        ctx.close();
    }
}

@Service
class PaymentProcessor {
    private final org.springframework.jdbc.core.JdbcTemplate jdbc;
    PaymentProcessor(javax.sql.DataSource ds) { this.jdbc = new org.springframework.jdbc.core.JdbcTemplate(ds); }

    @Transactional
    public void process(String from, String to, double amount) {
        jdbc.update("UPDATE accounts SET balance = balance - ? WHERE id = ?", amount, from);
        jdbc.update("UPDATE accounts SET balance = balance + ? WHERE id = ?", amount, to);
        System.out.printf("LOCAL TX: transferred $%.2f from %s to %s%n", amount, from, to);
    }
}
```

`payments-schema.sql`:
```sql
CREATE TABLE accounts (id VARCHAR(10) PRIMARY KEY, balance DECIMAL(10,2));
INSERT INTO accounts VALUES ('ACC-1', 2000.00), ('ACC-2', 300.00);
```

How to run: `java -cp spring-context.jar:spring-jdbc.jar:h2.jar:. GlobalLocalTxDemo.java`

Single `Connection` obtained from H2 pool. Both updates run inside `autoCommit=false`. On commit, H2 commits atomically. No external coordinator needed.

---

### Level 2 — Intermediate

**Simulated global scenario**: two independent datasources, demonstrating the atomicity failure of using local transactions across two resources.

```java
// GlobalLocalTxDemo.java
import org.springframework.context.annotation.*;
import org.springframework.jdbc.datasource.*;
import org.springframework.jdbc.datasource.embedded.*;
import org.springframework.transaction.*;
import org.springframework.transaction.annotation.*;
import org.springframework.stereotype.*;

@Configuration
@EnableTransactionManagement
@ComponentScan
public class GlobalLocalTxDemo {
    @Bean(name = "accountsDs")
    public javax.sql.DataSource accountsDs() {
        return new EmbeddedDatabaseBuilder().setType(EmbeddedDatabaseType.H2)
            .setName("accounts")
            .addScript("accounts-schema.sql").build();
    }

    @Bean(name = "auditDs")
    public javax.sql.DataSource auditDs() {
        return new EmbeddedDatabaseBuilder().setType(EmbeddedDatabaseType.H2)
            .setName("audit")
            .addScript("audit-schema.sql").build();
    }

    // Only one TM is primary — the audit write is NOT in the same transaction
    @Bean
    public PlatformTransactionManager transactionManager(
            @org.springframework.beans.factory.annotation.Qualifier("accountsDs") javax.sql.DataSource ds) {
        return new DataSourceTransactionManager(ds);
    }

    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(GlobalLocalTxDemo.class);
        ctx.getBean(PaymentProcessor.class).process("ACC-1", 250.0);
        ctx.close();
    }
}

@Service
class PaymentProcessor {
    private final org.springframework.jdbc.core.JdbcTemplate accounts;
    private final org.springframework.jdbc.core.JdbcTemplate audit;

    PaymentProcessor(
        @org.springframework.beans.factory.annotation.Qualifier("accountsDs") javax.sql.DataSource accountsDs,
        @org.springframework.beans.factory.annotation.Qualifier("auditDs") javax.sql.DataSource auditDs) {
        this.accounts = new org.springframework.jdbc.core.JdbcTemplate(accountsDs);
        this.audit    = new org.springframework.jdbc.core.JdbcTemplate(auditDs);
    }

    @Transactional   // covers accountsDs only — auditDs has its own auto-committed connection
    public void process(String accountId, double amount) {
        accounts.update("UPDATE accounts SET balance = balance - ? WHERE id = ?", amount, accountId);
        audit.update("INSERT INTO audit_log(account, amount, ts) VALUES(?,?,NOW())", accountId, amount);
        System.out.println("WARNING: audit and accounts are in SEPARATE local transactions!");
        System.out.println("A crash here could debit accounts but lose the audit record.");
    }
}
```

`accounts-schema.sql`: `CREATE TABLE accounts (id VARCHAR(10) PRIMARY KEY, balance DECIMAL(10,2)); INSERT INTO accounts VALUES ('ACC-1',1000.00);`
`audit-schema.sql`: `CREATE TABLE audit_log (account VARCHAR(10), amount DECIMAL(10,2), ts TIMESTAMP);`

How to run: same classpath

This shows the **global transaction problem**: the accounts update is in `@Transactional` (covered by the primary TM), but the audit insert uses a different datasource with its own auto-committed connection. If the accounts commit fails after the audit insert, the two databases are inconsistent. JTA would prevent this.

---

### Level 3 — Advanced

**Outbox pattern as a practical alternative to JTA** — write both the business record and the audit event to the same local database atomically, then let a separate process relay the event.

```java
// GlobalLocalTxDemo.java
import org.springframework.context.annotation.*;
import org.springframework.jdbc.datasource.*;
import org.springframework.jdbc.datasource.embedded.*;
import org.springframework.transaction.*;
import org.springframework.transaction.annotation.*;
import org.springframework.stereotype.*;

@Configuration
@EnableTransactionManagement
@ComponentScan
public class GlobalLocalTxDemo {
    @Bean
    public javax.sql.DataSource dataSource() {
        return new EmbeddedDatabaseBuilder().setType(EmbeddedDatabaseType.H2)
            .addScript("outbox-schema.sql").build();
    }

    @Bean
    public PlatformTransactionManager transactionManager(javax.sql.DataSource ds) {
        return new DataSourceTransactionManager(ds);
    }

    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(GlobalLocalTxDemo.class);
        var svc = ctx.getBean(PaymentProcessor.class);
        svc.process("ACC-1", "ACC-2", 750.0);
        // Simulate the outbox relay
        ctx.getBean(OutboxRelay.class).relay();
        ctx.close();
    }
}

@Service
class PaymentProcessor {
    private final org.springframework.jdbc.core.JdbcTemplate jdbc;
    PaymentProcessor(javax.sql.DataSource ds) { this.jdbc = new org.springframework.jdbc.core.JdbcTemplate(ds); }

    @Transactional
    public void process(String from, String to, double amount) {
        // Both writes are in the SAME local transaction — atomic without JTA
        jdbc.update("UPDATE accounts SET balance = balance - ? WHERE id = ?", amount, from);
        jdbc.update("UPDATE accounts SET balance = balance + ? WHERE id = ?", amount, to);
        jdbc.update("INSERT INTO outbox(payload, processed) VALUES(?,false)",
            String.format("{\"from\":\"%s\",\"to\":\"%s\",\"amount\":%.2f}", from, to, amount));
        System.out.printf("TX committed: debit %s, credit %s, outbox entry written%n", from, to);
    }
}

@Service
class OutboxRelay {
    private final org.springframework.jdbc.core.JdbcTemplate jdbc;
    OutboxRelay(javax.sql.DataSource ds) { this.jdbc = new org.springframework.jdbc.core.JdbcTemplate(ds); }

    @Transactional
    public void relay() {
        var rows = jdbc.queryForList("SELECT id, payload FROM outbox WHERE processed = false");
        for (var row : rows) {
            System.out.println("[OUTBOX RELAY] publishing: " + row.get("payload"));
            // In production: send to Kafka/SQS/RabbitMQ here
            jdbc.update("UPDATE outbox SET processed = true WHERE id = ?", row.get("id"));
        }
    }
}
```

`outbox-schema.sql`:
```sql
CREATE TABLE accounts (id VARCHAR(10) PRIMARY KEY, balance DECIMAL(10,2));
CREATE TABLE outbox   (id BIGINT AUTO_INCREMENT PRIMARY KEY, payload VARCHAR(512), processed BOOLEAN);
INSERT INTO accounts VALUES ('ACC-1', 5000.00), ('ACC-2', 100.00);
```

How to run: same classpath

The outbox pattern achieves the same safety guarantee as JTA for event publishing: the business update and the event record are committed atomically (one local transaction, one DB). A relay process then publishes the event separately. If the relay fails, the record stays in the outbox and can be retried.

## 6. Walkthrough

**2PC lifecycle (global/JTA, conceptual):**

```
UserTransaction.begin()
  → JTA TM creates global XID

jdbc1.update(...)     → XAConnection1 enlisted: XID assigned
jdbc2.update(...)     → XAConnection2 enlisted: XID assigned
queueSend(...)        → XASession enlisted: XID assigned

UserTransaction.commit()
  ── Phase 1 (prepare) ──
    XAConnection1.prepare()  → "YES" (writes prepare log)
    XAConnection2.prepare()  → "YES"
    XASession.prepare()      → "YES"
  ── Phase 2 (commit) ──
    XAConnection1.commit()
    XAConnection2.commit()
    XASession.commit()
    JTA TM removes log entry
```

If any resource returns "NO" in Phase 1, the JTA TM calls `rollback()` on all enlisted resources.

**Outbox relay flow (Level 3):**

```
PaymentProcessor.process("ACC-1","ACC-2",750.0)
  tx1 opens
  → UPDATE accounts ACC-1 balance -750
  → UPDATE accounts ACC-2 balance +750
  → INSERT outbox payload="{...}" processed=false
  tx1 commits (all 3 writes atomic)

OutboxRelay.relay()
  tx2 opens
  → SELECT outbox WHERE processed=false → [{id:1, payload:...}]
  → [OUTBOX RELAY] publishing: {"from":"ACC-1","to":"ACC-2","amount":750.00}
  → UPDATE outbox SET processed=true WHERE id=1
  tx2 commits
```

## 7. Gotchas & takeaways

> **Local transactions cannot span two datasources atomically.** If your `@Transactional` method writes to two different `DataSource` beans, each write has its own connection and its own commit. A failure between the two commits leaves data inconsistent. This is not a Spring limitation — it's fundamental to relational databases.

> **JTA is heavy.** Beyond the XA driver requirement (not all JDBC drivers support XA), JTA requires a transaction log (durable storage), a recovery process, and adds network round-trips. Consider the outbox pattern, saga pattern, or eventual consistency before reaching for JTA.

- `DataSourceTransactionManager` = local, single datasource — 99% of apps.
- `JtaTransactionManager` = global, multi-resource, requires XA datasources and a JTA provider (Atomikos, Narayana, Jakarta EE container).
- The outbox pattern achieves cross-resource atomicity (DB + MQ) without JTA by writing to the same local DB first.
- Spring's `PlatformTransactionManager` abstraction means your business logic doesn't change when switching from local to global — only the `@Bean` declaration changes.
