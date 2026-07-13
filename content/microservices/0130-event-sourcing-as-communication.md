---
card: microservices
gi: 130
slug: event-sourcing-as-communication
title: "Event sourcing (as communication)"
---

## 1. What it is

Event sourcing, viewed as a communication mechanism rather than as a storage technique, is publishing the *complete, ordered log* of every state-changing event an entity has ever undergone — not just the latest snapshot — so that any consumer can reconstruct the entity's full current state (or any past state) purely by replaying that log from the beginning, and any new consumer added later can catch up on the entire history the same way.

## 2. Why & when

[Event-carried state transfer](0129-event-carried-state-transfer.md) gives a consumer the state *at the moment* an event fired, but a consumer that joins the system late, or that needs to know not just the current state but *how it got there* (for an audit trail, a dispute investigation, or rebuilding a derived view after a bug), has no way to recover history from individual state-transfer events alone — once consumed, they're gone unless something retains them. Event sourcing treats the sequence of events itself as the durable, authoritative record: current state is always just "replay the log and apply each event in order," which means the full history is never lost and any number of different projections (read models) can be built from the same underlying log, including ones invented after the fact.

Reach for event sourcing when audit history is a first-class requirement, when multiple different views of the same entity's history need to be derived independently (an operational dashboard and a compliance report, from the same events), or when the ability to rebuild a corrupted or buggy projection by simply replaying history from scratch is valuable. It adds real complexity — don't reach for it as a default for entities with simple CRUD lifecycles and no audit or multi-projection need.

## 3. Core concept

Every state change is appended as an immutable event to that entity's log, never overwritten or deleted; current state is derived, not stored directly, by folding (reducing) the entire ordered sequence of events into a final value.

```java
// state is NEVER stored directly -- only the events are; current state is DERIVED by replay
List<Event> accountHistory = List.of(
    new AccountOpened(balance = 0),
    new Deposited(amount = 100),
    new Withdrawn(amount = 30)
);
double currentBalance = accountHistory.stream()
    .reduce(0.0, (balance, event) -> applyEvent(balance, event), Double::sum); // fold the log into a value
// currentBalance == 70, computed fresh from history, not read from a stored field
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="An append-only event log for one account: AccountOpened, Deposited, Withdrawn; current balance is computed by folding all three events in order, and a NEW consumer added later can replay the same log from the start to arrive at the identical result">
  <rect x="20" y="60" width="130" height="40" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="85" y="85" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">AccountOpened</text>
  <rect x="170" y="60" width="110" height="40" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="225" y="85" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">Deposited(100)</text>
  <rect x="300" y="60" width="110" height="40" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="355" y="85" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">Withdrawn(30)</text>

  <line x1="150" y1="80" x2="168" y2="80" stroke="#8b949e" marker-end="url(#arr16)"/>
  <line x1="280" y1="80" x2="298" y2="80" stroke="#8b949e" marker-end="url(#arr16)"/>

  <rect x="470" y="55" width="140" height="50" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="540" y="78" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">balance = 70</text>
  <text x="540" y="94" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">(folded from log)</text>
  <line x1="410" y1="80" x2="468" y2="80" stroke="#8b949e" marker-end="url(#arr16)"/>

  <text x="220" y="140" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">any new consumer can replay this SAME log from the start to reach the SAME state</text>

  <defs>
    <marker id="arr16" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

State is never stored directly; it is always recomputed by folding the ordered event log.

## 5. Runnable example

Scenario: a bank account's balance tracked first as ordinary mutable state (losing all history), then rebuilt as an event-sourced log where current balance is derived by replay, and finally extended to show two entirely different projections — current balance and a monthly transaction summary — both built from the exact same underlying event log.

### Level 1 — Basic

```java
// File: MutableStateBaseline.java -- ordinary mutable state: history is simply gone.
public class MutableStateBaseline {
    static double balance = 0;

    public static void main(String[] args) {
        balance += 100; // deposit
        balance -= 30;  // withdrawal
        System.out.println("Current balance: " + balance);
        System.out.println("How did we get here? No idea -- the individual events were never kept, only the final number.");
    }
}
```

**How to run:** `javac MutableStateBaseline.java && java MutableStateBaseline` (JDK 17+).

The final balance is correct, but the moment each mutation completes, the information about what specifically happened and in what order is gone — only the ending value survives.

### Level 2 — Intermediate

```java
// File: EventSourcedBalance.java -- the log of events IS the source of truth;
// balance is derived by replaying it, never stored directly.
import java.util.*;

public class EventSourcedBalance {
    sealed interface AccountEvent permits AccountOpened, Deposited, Withdrawn {}
    record AccountOpened(double initialBalance) implements AccountEvent {}
    record Deposited(double amount) implements AccountEvent {}
    record Withdrawn(double amount) implements AccountEvent {}

    static double replay(List<AccountEvent> log) {
        double balance = 0;
        for (AccountEvent event : log) { // fold over the events, in order
            balance = switch (event) {
                case AccountOpened e -> e.initialBalance();
                case Deposited e -> balance + e.amount();
                case Withdrawn e -> balance - e.amount();
            };
        }
        return balance;
    }

    public static void main(String[] args) {
        List<AccountEvent> log = new ArrayList<>();
        log.add(new AccountOpened(0));
        log.add(new Deposited(100));
        log.add(new Withdrawn(30));

        System.out.println("Full event log: " + log);
        System.out.println("Current balance, derived by replaying the log: " + replay(log));
    }
}
```

**How to run:** `javac EventSourcedBalance.java && java EventSourcedBalance` (JDK 17+).

Expected output:
```
Full event log: [AccountOpened[initialBalance=0.0], Deposited[amount=100.0], Withdrawn[amount=30.0]]
Current balance, derived by replaying the log: 70.0
```

Unlike Level 1, the full sequence of what happened is preserved in `log`; `replay` computes the current balance from it, but the history itself — every individual deposit and withdrawal, in order — remains intact and inspectable.

### Level 3 — Advanced

```java
// File: MultipleProjectionsFromOneLog.java -- two DIFFERENT views (current balance,
// and a monthly summary) both built from the EXACT SAME underlying event log.
import java.util.*;

public class MultipleProjectionsFromOneLog {
    sealed interface AccountEvent permits Deposited, Withdrawn {}
    record Deposited(double amount, String month) implements AccountEvent {}
    record Withdrawn(double amount, String month) implements AccountEvent {}

    // projection 1: current balance -- the "operational" view
    static double projectBalance(List<AccountEvent> log) {
        double balance = 0;
        for (AccountEvent e : log) {
            balance += switch (e) {
                case Deposited d -> d.amount();
                case Withdrawn w -> -w.amount();
            };
        }
        return balance;
    }

    // projection 2: monthly summary -- a COMPLETELY different shape of derived data,
    // built by folding the SAME log with different accumulation logic
    static Map<String, Double> projectMonthlyNetFlow(List<AccountEvent> log) {
        Map<String, Double> byMonth = new TreeMap<>();
        for (AccountEvent e : log) {
            String month = (e instanceof Deposited d) ? d.month() : ((Withdrawn) e).month();
            double delta = (e instanceof Deposited d) ? d.amount() : -((Withdrawn) e).amount();
            byMonth.merge(month, delta, Double::sum);
        }
        return byMonth;
    }

    public static void main(String[] args) {
        List<AccountEvent> log = List.of(
            new Deposited(100, "2026-01"),
            new Withdrawn(30, "2026-01"),
            new Deposited(50, "2026-02"),
            new Withdrawn(20, "2026-02")
        );

        System.out.println("Projection 1 (current balance): " + projectBalance(log));
        System.out.println("Projection 2 (monthly net flow): " + projectMonthlyNetFlow(log));
        System.out.println("Both projections came from the IDENTICAL log -- a THIRD projection could be added later with no changes to the log itself.");
    }
}
```

**How to run:** `javac MultipleProjectionsFromOneLog.java && java MultipleProjectionsFromOneLog` (JDK 17+).

Expected output:
```
Projection 1 (current balance): 100.0
Projection 2 (monthly net flow): {2026-01=70.0, 2026-02=30.0}
Both projections came from the IDENTICAL log -- a THIRD projection could be added later with no changes to the log itself.
```

## 6. Walkthrough

1. **Level 1** — `balance += 100` and `balance -= 30` each overwrite the only copy of the account's state; by the time `main` prints the result, there is no way to recover that a deposit happened before the withdrawal, or what either amount was — only the net effect remains.
2. **Level 2, the log as the source of truth** — `log` accumulates `AccountOpened`, `Deposited`, and `Withdrawn` records in the order they occurred; nothing in this design ever mutates or removes an existing entry, only appends new ones.
3. **Level 2, deriving state via replay** — `replay` starts from an implicit zero balance and folds over `log` in order, applying each event's effect via the `switch` expression; the final `balance` value returned is a *computed* result, not something read from a stored field anywhere.
4. **Level 2, what's preserved versus Level 1** — printing `log` itself shows the full ordered history of what happened, something Level 1's design has no way to produce, because Level 1 never kept that information past the moment each mutation applied.
5. **Level 3, one log, two independent folds** — `projectBalance` and `projectMonthlyNetFlow` both iterate the *identical* `log` list but accumulate entirely different result shapes: a single running total for one, a per-month breakdown map for the other.
6. **Level 3, adding the month dimension** — each event now carries a `month` field; `projectMonthlyNetFlow` groups by that field using `byMonth.merge(month, delta, Double::sum)`, building up net inflow/outflow per month, something the balance-only projection has no notion of at all.
7. **Level 3, why this matters for communication** — because both projections are pure functions of the same immutable event log, a consumer that only ever needed `projectBalance` and a *different* consumer that later needs `projectMonthlyNetFlow` can both be built, independently, against the exact same published event stream, without the producer needing to anticipate either projection's specific shape in advance or publish a different event type for each — this is the flexibility event sourcing as a communication style provides that a single "current state" event does not.

## 7. Gotchas & takeaways

> **Gotcha:** an event log that grows without bound eventually makes replaying from the very beginning slow and expensive; real event-sourced systems address this with periodic snapshots (a cached "state as of event #10,000") so replay only needs to start from the most recent snapshot forward, not from event #1 every single time — plan for this from the start rather than retrofitting it once replay time becomes a visible problem.

- Event sourcing as a communication style publishes the full ordered history of an entity's changes, not just its latest state, letting consumers derive current (or historical) state by replaying that log.
- Current state is always computed, never stored directly — the log itself is the single source of truth.
- Any number of different projections (read models) can be derived independently from the same underlying log, including ones designed after the log already exists.
- A new consumer joining the system late can catch up fully by replaying history from the start, something [event-carried state transfer](0129-event-carried-state-transfer.md)'s point-in-time events cannot offer on their own.
- Real systems need periodic snapshots to keep replay time bounded as a log grows — plan for this rather than treating "replay from event one" as viable forever.
