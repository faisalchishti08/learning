---
card: spring-boot
gi: 273
slug: distributed-transactions-jta-legacy
title: Distributed transactions (JTA) — legacy
---

## 1. What it is

**JTA (Jakarta Transactions API / Java Transaction API)** provides a standardised way to coordinate transactions across multiple transactional resources — typically multiple databases, message queues, or a database + a JMS broker — in a single atomic unit: all succeed together or all roll back.

Spring Boot historically supported JTA via two embedded transaction managers:
- **Atomikos** (`spring-boot-starter-jta-atomikos`) — ships an embedded JTA provider.
- **Bitronix** (`spring-boot-starter-jta-bitronix`) — another embedded JTA provider.

Both were **removed in Spring Boot 3.x** (the starters no longer exist). The "legacy" label in the topic title reflects this: JTA is still a concept and JTA implementations still exist, but Spring Boot 3 dropped its built-in support.

Modern alternatives:
- **Saga pattern** — orchestration or choreography of distributed operations with compensating transactions.
- **Outbox pattern** — database + message broker consistency via the transactional outbox table.
- **Spring Modulith** — coordinates cross-module events within one database transaction.

## 2. Why & when

Understanding JTA is useful for:

- **Maintaining legacy Spring Boot 2.x applications** that still use Atomikos/Bitronix.
- **Migrating to Spring Boot 3.x** where you must replace JTA with an alternative.
- **Designing new systems** where you understand why JTA is avoided in modern microservices.

JTA's 2-phase commit (2PC) protocol guarantees ACID across resources but at significant cost:
- **Performance** — 2PC requires two network round-trips per transaction commit.
- **Availability** — a coordinator failure leaves resources in a "prepared" state requiring manual resolution.
- **Complexity** — all participating resources must implement the XA interface.

Modern microservice architecture avoids spanning transactions across service boundaries instead of using 2PC.

## 3. Core concept

**2-Phase Commit (2PC)** is the protocol JTA uses:

1. **Phase 1 (Prepare)** — the transaction manager asks all participants (DB, JMS broker) "can you commit?" Each participant locks its resources and replies "yes" or "no".
2. **Phase 2 (Commit/Rollback)** — if all replied "yes", the coordinator sends "commit" to all. If any replied "no" or timed out, it sends "rollback" to all.

The risk: if the coordinator crashes between Phase 1 (all prepared) and Phase 2 (commit sent), resources are left locked in limbo until the coordinator recovers.

**The modern alternatives** avoid 2PC:

| Pattern | Guarantees | Tradeoff |
|---|---|---|
| 2PC / JTA | Strong ACID | Slow, fragile, requires XA |
| Saga (orchestration) | Eventual consistency | Must write compensating actions |
| Outbox + relay | At-least-once delivery | Idempotent consumers required |
| Shared DB | ACID within one DB | Tighter coupling |

## 4. Diagram

<svg viewBox="0 0 700 250" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="JTA 2-phase commit protocol with transaction manager coordinating two databases">
  <defs>
    <marker id="arr" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="arrr" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>

  <!-- Transaction Manager -->
  <rect x="265" y="50" width="170" height="60" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="350" y="75" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">Transaction Manager</text>
  <text x="350" y="93" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">JTA (Atomikos / Bitronix)</text>

  <!-- Resources -->
  <rect x="50" y="170" width="140" height="50" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="120" y="193" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Database A (XA)</text>
  <text x="120" y="210" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">orders DB</text>

  <rect x="510" y="170" width="140" height="50" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="580" y="193" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Database B (XA)</text>
  <text x="580" y="210" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">inventory DB</text>

  <!-- Phase 1 arrows -->
  <line x1="280" y1="110" x2="150" y2="168" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#arrr)"/>
  <text x="185" y="140" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">Phase 1: Prepare?</text>

  <line x1="420" y1="110" x2="545" y2="168" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#arrr)"/>
  <text x="510" y="140" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">Phase 1: Prepare?</text>

  <!-- Phase 2 arrows -->
  <line x1="150" y1="168" x2="280" y2="115" stroke="#6db33f" stroke-width="1.5" stroke-dasharray="4" marker-end="url(#arr)"/>
  <text x="200" y="155" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">Yes</text>

  <line x1="545" y1="168" x2="420" y2="115" stroke="#6db33f" stroke-width="1.5" stroke-dasharray="4" marker-end="url(#arr)"/>
  <text x="500" y="155" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">Yes</text>

  <text x="350" y="240" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">2PC guarantees atomicity but requires XA-capable resources and crashes can leave locks</text>
</svg>

The transaction manager coordinates 2PC: both databases must confirm readiness before commit is sent to both.

## 5. Runnable example

```java
// JtaLegacyDemo.java — run with: java JtaLegacyDemo.java
// Explains JTA 2PC, why Spring Boot 3 removed it,
// and shows the modern outbox + saga alternatives.

public class JtaLegacyDemo {

    public static void main(String[] args) {
        System.out.println("=== Distributed Transactions (JTA) — Legacy ===\n");
        printHistoricalContext();
        printWhyRemoved();
        printMigrationStrategies();
        printOutboxPattern();
    }

    static void printHistoricalContext() {
        System.out.println("--- Spring Boot 2.x JTA (now removed) ---");
        System.out.println("""
            // pom.xml (Spring Boot 2.x only — removed in 3.x):
            <dependency>
              <groupId>org.springframework.boot</groupId>
              <artifactId>spring-boot-starter-jta-atomikos</artifactId>
            </dependency>

            // Auto-configured:
            // - AtomikosDataSourceBean (wraps XA DataSource)
            // - AtomikosConnectionFactoryBean (wraps XA JMS ConnectionFactory)
            // - JtaTransactionManager (coordinates 2PC)

            // @Transactional then spans both:
            @Transactional
            public void placeOrder(Order order) {
                orderRepo.save(order);           // DB A (orders)
                inventoryRepo.deduct(order);     // DB B (inventory)
                jmsTemplate.send("queue.orders", order); // JMS
                // If any fails → 2PC rolls back ALL three
            }
            """);
    }

    static void printWhyRemoved() {
        System.out.println("--- Why Spring Boot 3 removed built-in JTA ---");
        System.out.println("""
            1. Atomikos and Bitronix are not maintained as actively as needed
               for Spring Boot's quality bar.
            2. JTA/2PC is incompatible with microservices architecture —
               it creates cross-service coupling via a shared transaction coordinator.
            3. XA drivers for modern databases/brokers (especially cloud-native ones)
               are rare, proprietary, or buggy.
            4. Modern alternatives (Saga, Outbox) handle distributed consistency
               without 2PC and are more resilient to network partitions.

            Spring Boot 3 migration guide recommends:
              - Consolidate into one database if possible (avoid the problem entirely).
              - Use the Outbox pattern for DB + messaging consistency.
              - Use the Saga pattern for cross-service consistency.
              - Or add Atomikos manually (it's a standalone library, not a Boot starter).
            """);
    }

    static void printMigrationStrategies() {
        System.out.println("--- Migration strategies from JTA ---");
        System.out.println("""
            Option A: Consolidate (simplest)
              Use a single database. If you had DB A + DB B, merge them.
              @Transactional now works with one resource manager — no JTA needed.

            Option B: Add Atomikos manually (Spring Boot 3)
              <dependency>
                <groupId>com.atomikos</groupId>
                <artifactId>transactions-spring-boot3-starter</artifactId>
              </dependency>
              Configure AtomikosDataSourceBean beans yourself.

            Option C: Outbox pattern (recommended for DB + messaging)
              See below.

            Option D: Saga pattern (recommended for cross-service)
              Orchestration: central saga orchestrator sends commands,
              each service executes and reports success/failure.
              Each step has a compensating transaction for rollback.
            """);
    }

    static void printOutboxPattern() {
        System.out.println("--- Outbox pattern (DB + messaging without 2PC) ---");
        System.out.println("""
            // All in ONE @Transactional (one DB — no JTA):
            @Transactional
            public void placeOrder(Order order) {
                orderRepo.save(order);             // persist order

                // Write event to outbox table (same DB, same TX):
                outboxRepo.save(new OutboxEvent(
                    "ORDER_PLACED",
                    objectMapper.writeValueAsString(order)
                ));
                // TX commits: order + outbox event atomically saved

                // Separate relay process reads outbox and publishes to Kafka/SQS:
                // SELECT * FROM outbox WHERE published = false;
                // kafka.send("orders", event);
                // UPDATE outbox SET published = true WHERE id = ?;
            }

            // Result: order saved and message published — consistently.
            // Kafka/SQS delivery is at-least-once → consumers must be idempotent.
            """);
    }
}
```

**How to run:** `java JtaLegacyDemo.java`

## 6. Walkthrough

- **2PC vulnerability** — if the transaction coordinator (Atomikos) crashes after sending "prepare" but before sending "commit", both databases are locked in a "prepared" state. They hold locks until the coordinator recovers and replays the log. In a microservices context this can block the entire system.
- **`spring-boot-starter-jta-atomikos` removal** — Spring Boot 3 dropped the starters because maintaining compatibility with Atomikos' changing APIs across Spring Boot releases became untenable. Atomikos publishes its own `transactions-spring-boot3-starter` for projects that need it.
- **Outbox pattern atomicity** — the key insight is that writing to the outbox table is in the *same database transaction* as the business operation. The database guarantees these are atomic. The relay (a scheduled job or Debezium CDC) then publishes from the outbox to Kafka/SQS. The worst case is a duplicate publish (relay runs twice), which consumers handle with idempotency keys.
- **Saga orchestration** — the saga orchestrator maintains state (in a database) of which steps have completed. If step 2 fails, the orchestrator calls compensating transactions for step 1. This is explicit application logic, not database-level 2PC.
- **"Consolidate" option** — if two databases hold related data that frequently needs to be updated together, they should probably be one database. Distributed transaction problems often signal design issues: separate services that are actually tightly coupled.

## 7. Gotchas & takeaways

> **`@Transactional` cannot span two separate `DataSource` beans without JTA.** If you have `@Autowired DataSource ordersDb` and `@Autowired DataSource inventoryDb`, a single `@Transactional` only covers the first datasource that opens a transaction in the call stack. The second datasource participates in a separate, independent transaction — a partial failure leaves inconsistent state.

> **XA drivers are not universally available.** PostgreSQL's XA support works but requires specific connection pool configuration. MySQL's XA is available but historically buggy with certain failure modes. Cloud databases (RDS Aurora, Cloud SQL) may not support XA at all. Check before planning an XA-based architecture.

- The simplest fix for DB+Kafka consistency: outbox pattern — same DB transaction writes the business data and the outbox row.
- Spring Modulith provides `@ApplicationModuleListener` — events published within a transaction are reliably delivered after commit, solving the DB+events consistency problem within a monolith.
- For new projects: design to avoid cross-resource atomic transactions. If you need them, revisit the data model.
- If you absolutely need JTA on Spring Boot 3: use `com.atomikos:transactions-spring-boot3-starter` with manual `AtomikosDataSourceBean` configuration.
