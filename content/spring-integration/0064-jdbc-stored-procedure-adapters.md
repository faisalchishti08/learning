---
card: spring-integration
gi: 64
slug: jdbc-stored-procedure-adapters
title: "JDBC & stored procedure adapters"
---

## 1. What it is

JDBC adapters (`Jdbc.inboundAdapter(...)`/`Jdbc.outboundAdapter(...)`/`Jdbc.outboundGateway(...)`) connect a flow to a relational database using plain SQL, while the stored procedure adapters (`Jdbc.storedProcedureOutboundGateway(...)`) invoke a named database procedure or function instead of raw SQL. Inbound, a polling query pulls rows and turns each into a message; outbound, a message's payload is bound as parameters to an INSERT/UPDATE statement or a stored procedure call.

## 2. Why & when

You reach for JDBC or stored-procedure adapters when the database itself is the integration point:

- **A table is being used as a work queue** — rows marked "pending" need to be picked up, processed, and marked "done," a common pattern for polling-based ingestion from a legacy system that only writes to a database.
- **Business logic already lives in a stored procedure** — many enterprises keep validation, calculations, or multi-table updates inside the database as procedures; a stored-procedure adapter lets a flow invoke that logic without re-implementing it in Java.
- **A flow needs to persist its output as a side effect** — writing an audit trail, a processed-message log, or a status update back to a relational table as one step in a longer pipeline.

## 3. Core concept

Think of the inbound JDBC adapter as a diner's number board: an update query first marks certain rows "called" (so no other window serves the same order twice), then a select query picks up exactly those, converting each row into a message the way a called number becomes a customer stepping up to the counter. A stored-procedure gateway is more like handing that order not to a counter clerk who improvises, but to a fixed recipe card in the kitchen (the procedure) that takes named ingredients (parameters) and returns a fixed result.

```java
@Bean
public IntegrationFlow jdbcPollingFlow(DataSource dataSource) {
    return IntegrationFlow.from(
            Jdbc.inboundAdapter(dataSource, "SELECT * FROM orders WHERE status = 'PENDING'")
                .updateSql("UPDATE orders SET status = 'PROCESSING' WHERE id IN (:id)")
                .rowMapper(new OrderRowMapper()),
            e -> e.poller(Pollers.fixedDelay(5_000)))
        .handle((Order order, headers) -> orderService.process(order))
        .get();
}
```

The `updateSql` runs first (claiming rows), then the select query runs, so two overlapping polls never both pick up the same pending order.

## 4. Diagram

<svg viewBox="0 0 640 160" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Inbound JDBC adapter: claim rows with an update, select the claimed rows, emit one message per row; outbound: bind message payload as parameters and execute INSERT or call a stored procedure" >
  <rect x="20" y="20" width="280" height="120" rx="8" fill="#0d1117" stroke="#6db33f" stroke-width="1.5"/>
  <text x="160" y="12" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">Inbound (polling)</text>
  <text x="35" y="42" fill="#e6edf3" font-size="8" font-family="monospace">1. UPDATE ... SET status='PROCESSING'</text>
  <text x="35" y="62" fill="#e6edf3" font-size="8" font-family="monospace">2. SELECT * WHERE status='PROCESSING'</text>
  <text x="35" y="82" fill="#79c0ff" font-size="8" font-family="monospace">3. one Message per row</text>
  <text x="35" y="110" fill="#8b949e" font-size="7" font-family="sans-serif">claim-then-select avoids double pickup</text>

  <rect x="340" y="20" width="280" height="120" rx="8" fill="#0d1117" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="480" y="12" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">Outbound (gateway)</text>
  <text x="355" y="42" fill="#e6edf3" font-size="8" font-family="monospace">Message payload -&gt; bound params</text>
  <text x="355" y="62" fill="#6db33f" font-size="8" font-family="monospace">INSERT / UPDATE statement</text>
  <text x="355" y="82" fill="#6db33f" font-size="8" font-family="monospace">or CALL stored_procedure(?, ?)</text>
  <text x="355" y="110" fill="#8b949e" font-size="7" font-family="sans-serif">gateway can return generated keys/results</text>
</svg>

Inbound claims-then-selects to avoid double delivery; outbound binds message data to SQL or a named procedure.

## 5. Runnable example

The scenario: an order-processing flow polling a table for pending work, simulated with an in-memory table (no real database needed to demonstrate the claim-then-process logic), starting with a plain poll, then adding row claiming to prevent double pickup, then handling a failed process step with a rollback of the claim.

### Level 1 — Basic

```java
// JdbcPollingDemo.java
import java.util.*;

public class JdbcPollingDemo {
    record Order(int id, String status) {}

    static List<Order> selectPending(List<Order> table) {
        return table.stream().filter(o -> o.status().equals("PENDING")).toList();
    }

    public static void main(String[] args) {
        List<Order> table = new ArrayList<>(List.of(new Order(1, "PENDING"), new Order(2, "PENDING")));
        for (Order o : selectPending(table)) {
            System.out.println("Processing order " + o.id());
        }
    }
}
```

How to run: `java JdbcPollingDemo.java`. Expected output: `Processing order 1` then `Processing order 2` — a bare select with no claiming step yet.

### Level 2 — Intermediate

```java
// JdbcPollingDemo.java
import java.util.*;

public class JdbcPollingDemo {
    static class Order {
        final int id; String status;
        Order(int id, String status) { this.id = id; this.status = status; }
    }

    // Real-world concern: two overlapping polls must not both pick up the same row.
    // The update-then-select pattern claims rows atomically before processing them.
    static synchronized List<Order> claimPending(List<Order> table) {
        List<Order> claimed = new ArrayList<>();
        for (Order o : table) {
            if (o.status.equals("PENDING")) {
                o.status = "PROCESSING"; // the "UPDATE ... SET status='PROCESSING'" step
                claimed.add(o);
            }
        }
        return claimed;
    }

    public static void main(String[] args) {
        List<Order> table = new ArrayList<>(List.of(new Order(1, "PENDING"), new Order(2, "PENDING")));

        List<Order> firstPoll = claimPending(table);
        List<Order> secondPoll = claimPending(table); // simulates an overlapping poll

        System.out.println("First poll claimed: " + firstPoll.size());
        System.out.println("Second poll claimed: " + secondPoll.size());
    }
}
```

How to run: `java JdbcPollingDemo.java`. Expected output: `First poll claimed: 2` then `Second poll claimed: 0` — the claiming update means a second, overlapping poll finds nothing left in `PENDING` status, avoiding duplicate processing.

### Level 3 — Advanced

```java
// JdbcPollingDemo.java
import java.util.*;

public class JdbcPollingDemo {
    static class Order {
        final int id; String status;
        Order(int id, String status) { this.id = id; this.status = status; }
    }

    static class ProcessingFailedException extends RuntimeException {
        ProcessingFailedException(String msg) { super(msg); }
    }

    static synchronized List<Order> claimPending(List<Order> table) {
        List<Order> claimed = new ArrayList<>();
        for (Order o : table) {
            if (o.status.equals("PENDING")) { o.status = "PROCESSING"; claimed.add(o); }
        }
        return claimed;
    }

    static void process(Order o) {
        if (o.id == 2) throw new ProcessingFailedException("payment gateway timeout");
        o.status = "DONE";
    }

    public static void main(String[] args) {
        List<Order> table = new ArrayList<>(List.of(
            new Order(1, "PENDING"), new Order(2, "PENDING"), new Order(3, "PENDING")));

        for (Order o : claimPending(table)) {
            try {
                process(o);
                System.out.println("Order " + o.id + " -> " + o.status);
            } catch (ProcessingFailedException ex) {
                // Production concern: a failed downstream step must release the claim so the
                // order is retried on the next poll, instead of being stuck in PROCESSING forever.
                o.status = "PENDING";
                System.out.println("Order " + o.id + " failed (" + ex.getMessage() + "), reverted to " + o.status);
            }
        }
    }
}
```

How to run: `java JdbcPollingDemo.java`. Expected output: order 1 and 3 print `-> DONE`; order 2 prints a failure message and reverts to `PENDING` — the rollback-of-claim pattern a real flow implements with a transactional advice or an explicit compensating update so a failed order isn't silently stuck mid-processing forever.

## 6. Walkthrough

Trace one polling cycle from trigger to final status.

1. **Poller fires**: on the configured interval, `Jdbc.inboundAdapter`'s poller executes the `updateSql` first — `UPDATE orders SET status = 'PROCESSING' WHERE status = 'PENDING'` — claiming a batch of rows atomically inside a transaction.
2. **Select claimed rows**: it then runs the main select — `SELECT * FROM orders WHERE status = 'PROCESSING'` (or by returned IDs) — retrieving exactly the rows just claimed.
3. **Row mapping**: each JDBC `ResultSet` row is mapped, via the configured `RowMapper`, into a Java object (`Order`), and each object becomes the payload of one outbound `Message`.
4. **Flow processing**: each message flows to the next handler — in the example, `orderService.process(order)` — which may succeed (transition to `DONE`) or fail (requiring the claim to be released back to `PENDING` so a later poll retries it).
5. **Outbound path (separate)**: elsewhere in the same or a different flow, a `Jdbc.outboundAdapter` or `Jdbc.storedProcedureOutboundGateway` takes a message's fields, binds them as SQL parameters or stored-procedure arguments, and executes the write — for instance, calling `CALL finalize_order(?, ?)` with the order ID and final status once processing completes.

```
poller tick
  -> UPDATE status='PROCESSING' WHERE status='PENDING'   (claim)
    -> SELECT WHERE status='PROCESSING'                   (fetch claimed)
      -> RowMapper -> Order object -> Message
        -> orderService.process(order)
           success -> DONE
           failure -> revert to PENDING (retry next poll)
```

## 7. Gotchas & takeaways

> **Gotcha:** without the claim-then-select pattern (a separate `updateSql` run before the select), two application instances polling the same table concurrently will both select the same "pending" rows and process the same order twice — the update must run first and atomically for the claim to actually prevent double pickup.

- Always wrap the claim update and the fetch select in the same transaction (the adapter does this by default) — otherwise a crash between the two leaves rows claimed but never actually retrieved.
- A stored-procedure gateway's parameter binding must match the procedure's declared parameter types exactly; a mismatched type is usually a runtime SQL error, not a compile-time one.
- Polling a table as a queue works, but at high volume it doesn't scale as gracefully as a dedicated message broker — it's the right tool when the data is already relational and volumes are modest, not a wholesale replacement for JMS/AMQP/Kafka adapters.
- Failed processing must have an explicit compensating action (revert the claim, move to a dead-letter status) — otherwise rows stuck in "PROCESSING" after a failure are invisible to the next poll forever.
