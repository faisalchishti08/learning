---
card: microservices
gi: 142
slug: stream-table-duality
title: "Stream-table duality"
---

## 1. What it is

Stream-table duality is the observation that a stream of change events and a table of current state are two views of the exact same information: a table can always be produced by folding (replaying and applying) a stream of changes onto it, and a stream can always be produced by capturing every change made to a table, in order. Neither is more fundamental than the other — they are the same data, viewed either as "everything that happened" or as "what's true right now."

## 2. Why & when

This duality resolves what looks like a conflict between two ways of thinking about data: application code usually wants a table (what is the customer's current balance, right now?), while integration and audit needs usually want a stream (what sequence of deposits and withdrawals produced that balance?). Instead of choosing one and losing the other, understanding the duality means either can be derived from the other at will — this is exactly the mechanism underlying [event sourcing](0130-event-sourcing-as-communication.md) (deriving a table/current-state view from a stream) and change data capture (deriving a stream from a table's changes).

Reach for this mental model whenever a service needs both a "current state" view for normal operation and a "full history" view for audit, replay, or feeding other services — rather than maintaining both separately (and risking them drifting out of sync), derive one from the other and there is only ever one source of truth to keep correct.

## 3. Core concept

Folding a stream of changes, applying each one to an accumulator in order, produces a table (a map from key to current value); conversely, a table can be viewed as a stream by treating every write to it as an emitted change event, in the order the writes occurred.

```java
// STREAM -> TABLE: fold every change, in order, into a running map of current state
Map<String, Double> currentBalances = new HashMap<>();
for (BalanceChange change : changeStream) {
    currentBalances.put(change.accountId(), change.newBalance()); // the LATEST value wins
}

// TABLE -> STREAM: every write to the table IS an event in the stream
void updateBalance(String accountId, double newBalance) {
    currentBalances.put(accountId, newBalance);       // update the "table"
    changeStream.append(new BalanceChange(accountId, newBalance)); // emit the "stream" event, same moment
}
```

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A stream of balance-change events for account A folds into a table showing account A's current balance as 70; the table's own writes, read back in order, reconstruct the identical stream" >
  <rect x="20" y="30" width="130" height="30" rx="4" fill="#1c2430" stroke="#79c0ff"/><text x="85" y="50" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">A: +100</text>
  <rect x="170" y="30" width="130" height="30" rx="4" fill="#1c2430" stroke="#79c0ff"/><text x="235" y="50" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">A: -30</text>
  <rect x="320" y="30" width="130" height="30" rx="4" fill="#1c2430" stroke="#79c0ff"/><text x="385" y="50" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">A: fold -&gt; 70</text>

  <text x="235" y="20" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">STREAM (ordered changes)</text>

  <line x1="235" y1="70" x2="235" y2="100" stroke="#8b949e" marker-end="url(#arr24)"/>
  <line x1="235" y1="100" x2="235" y2="130" stroke="#8b949e" stroke-dasharray="2,2" marker-end="url(#arr25)"/>
  <text x="270" y="115" fill="#8b949e" font-size="7" font-family="sans-serif">fold down / capture up</text>

  <rect x="170" y="140" width="130" height="35" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="235" y="163" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">TABLE: A = 70</text>

  <defs>
    <marker id="arr24" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
    <marker id="arr25" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

The same underlying facts, viewed as an ordered sequence of changes or as a single current snapshot.

## 5. Runnable example

Scenario: an account-balance system that starts by maintaining a table and a stream as two separate, independently updated structures (showing how they can drift out of sync), then derives the table entirely from the stream to guarantee they can never disagree, and finally derives a *second*, differently-shaped table (per-account transaction count) from that same single stream, showing the duality's real payoff — multiple views, one source of truth.

### Level 1 — Basic

```java
// File: SeparateStreamAndTable.java -- maintaining BOTH independently is a trap:
// a bug in one update path can silently desynchronize them.
import java.util.*;

public class SeparateStreamAndTable {
    record BalanceChange(String accountId, double delta) {}

    static List<BalanceChange> changeLog = new ArrayList<>(); // the "stream", updated separately
    static Map<String, Double> balanceTable = new HashMap<>(); // the "table", updated separately

    public static void main(String[] args) {
        applyDeposit("acct-1", 100);
        applyDeposit("acct-1", -30); // withdrawal
        applyDepositButForgetToLogIt("acct-1", 20); // BUG: updates the table but NOT the stream

        System.out.println("Table says balance: " + balanceTable.get("acct-1"));
        double replayedFromLog = changeLog.stream().filter(c -> c.accountId().equals("acct-1")).mapToDouble(BalanceChange::delta).sum();
        System.out.println("Replaying the log gives: " + replayedFromLog + " -- THEY DISAGREE, because the log is now incomplete.");
    }

    static void applyDeposit(String accountId, double delta) {
        balanceTable.merge(accountId, delta, Double::sum);
        changeLog.add(new BalanceChange(accountId, delta));
    }
    static void applyDepositButForgetToLogIt(String accountId, double delta) {
        balanceTable.merge(accountId, delta, Double::sum); // updates the table...
        // ...but a bug means changeLog.add(...) was never called here
    }
}
```

**How to run:** `javac SeparateStreamAndTable.java && java SeparateStreamAndTable` (JDK 17+).

Expected output:
```
Table says balance: 90.0
Replaying the log gives: 70.0 -- THEY DISAGREE, because the log is now incomplete.
```

Maintaining the stream and the table as two independently-updated structures created exactly the risk duality is meant to eliminate: a single missed update leaves them permanently inconsistent with no way to detect it without comparing them directly.

### Level 2 — Intermediate

```java
// File: TableDerivedFromStream.java -- the table is DERIVED from the stream, so they can NEVER disagree.
import java.util.*;

public class TableDerivedFromStream {
    record BalanceChange(String accountId, double delta) {}

    static List<BalanceChange> changeLog = new ArrayList<>(); // the SINGLE source of truth

    static void recordChange(String accountId, double delta) {
        changeLog.add(new BalanceChange(accountId, delta)); // the ONLY place state is ever written
    }

    // the table is COMPUTED, on demand, by folding the log -- never stored or updated independently
    static Map<String, Double> currentBalances() {
        Map<String, Double> table = new HashMap<>();
        for (BalanceChange c : changeLog) table.merge(c.accountId(), c.delta(), Double::sum);
        return table;
    }

    public static void main(String[] args) {
        recordChange("acct-1", 100);
        recordChange("acct-1", -30);
        recordChange("acct-1", 20);

        System.out.println("Derived table: " + currentBalances());
        System.out.println("There is NO separate table to forget to update -- it's IMPOSSIBLE for it to disagree with the log.");
    }
}
```

**How to run:** `javac TableDerivedFromStream.java && java TableDerivedFromStream` (JDK 17+).

Expected output:
```
Derived table: {acct-1=90.0}
There is NO separate table to forget to update -- it's IMPOSSIBLE for it to disagree with the log.
```

Unlike Level 1, `currentBalances()` has no independent state to fall out of sync — it is purely a function of `changeLog`, so its result always exactly reflects the log's content by construction.

### Level 3 — Advanced

```java
// File: MultipleViewsFromOneStream.java -- a SECOND, differently-shaped table (transaction
// counts) derived from the SAME single stream, proving one source of truth serves many views.
import java.util.*;

public class MultipleViewsFromOneStream {
    record BalanceChange(String accountId, double delta) {}

    static List<BalanceChange> changeLog = new ArrayList<>();

    static void recordChange(String accountId, double delta) { changeLog.add(new BalanceChange(accountId, delta)); }

    // view 1: current balance per account
    static Map<String, Double> currentBalances() {
        Map<String, Double> table = new HashMap<>();
        for (BalanceChange c : changeLog) table.merge(c.accountId(), c.delta(), Double::sum);
        return table;
    }

    // view 2: a COMPLETELY different shape -- transaction COUNT per account, derived from the SAME log
    static Map<String, Integer> transactionCounts() {
        Map<String, Integer> table = new HashMap<>();
        for (BalanceChange c : changeLog) table.merge(c.accountId(), 1, Integer::sum);
        return table;
    }

    // view 3: yet another shape -- largest single deposit ever made, per account
    static Map<String, Double> largestDeposit() {
        Map<String, Double> table = new HashMap<>();
        for (BalanceChange c : changeLog) {
            if (c.delta() > 0) table.merge(c.accountId(), c.delta(), Math::max);
        }
        return table;
    }

    public static void main(String[] args) {
        recordChange("acct-1", 100);
        recordChange("acct-1", -30);
        recordChange("acct-1", 20);
        recordChange("acct-2", 50);

        System.out.println("View 1 (current balance):    " + currentBalances());
        System.out.println("View 2 (transaction count):  " + transactionCounts());
        System.out.println("View 3 (largest deposit):    " + largestDeposit());
        System.out.println("All THREE views came from the SAME 4-event log -- adding a 4th view requires ZERO changes to how events are recorded.");
    }
}
```

**How to run:** `javac MultipleViewsFromOneStream.java && java MultipleViewsFromOneStream` (JDK 17+).

Expected output:
```
View 1 (current balance):    {acct-1=90.0, acct-2=50.0}
View 2 (transaction count):  {acct-1=3, acct-2=1}
View 3 (largest deposit):    {acct-1=100.0, acct-2=50.0}
All THREE views came from the SAME 4-event log -- adding a 4th view requires ZERO changes to how events are recorded.
```

## 6. Walkthrough

1. **Level 1** — `applyDeposit` updates both `balanceTable` and `changeLog` together, but `applyDepositButForgetToLogIt` updates only `balanceTable`, modeling a realistic bug (a code path that forgot the second update); the final comparison between `balanceTable.get("acct-1")` and a fresh replay of `changeLog` reveals the resulting, silent disagreement.
2. **Level 2, eliminating the second update path entirely** — `recordChange` is the *only* function that ever writes anything, and it writes only to `changeLog`; there is no `balanceTable` field to independently update at all.
3. **Level 2, the table as a pure function** — `currentBalances()` computes its result fresh from `changeLog` every time it's called, rather than reading a stored value; this makes it structurally impossible for the derived table to disagree with the log, since it *is* the log, just folded into a different shape.
4. **Level 3, a second, unrelated derived view** — `transactionCounts()` folds the identical `changeLog` list but accumulates a count instead of a sum, producing an entirely different kind of table (`{acct-1=3, acct-2=1}`) from the exact same four recorded events.
5. **Level 3, a third view with its own logic** — `largestDeposit()` folds the same log yet again, this time filtering for positive deltas only and tracking a running maximum via `Math::max`, producing a third table shape unrelated to either of the first two.
6. **Level 3, tracing one account's three views** — `acct-1` has three recorded changes (+100, −30, +20): View 1 sums them to 90.0; View 2 counts them as 3 transactions; View 3 finds the largest positive one, 100.0 — three genuinely different, independently useful facts, all derived without needing three separately-maintained, independently-updatable tables.
7. **Level 3, the payoff stated directly** — the final printed line makes explicit what the duality buys: a fourth view (say, average transaction size) could be added by writing one more fold function against `changeLog`, with zero changes needed to `recordChange` or to any of the existing views — the single stream remains the one place facts are ever recorded, and every view is just a different lens on it.

## 7. Gotchas & takeaways

> **Gotcha:** deriving a table by folding a stream from scratch every single call, as these examples do for clarity, does not scale to a long-lived, high-volume log — real systems (materialized views in stream processing frameworks, or event-sourcing snapshots) cache the folded result and update it incrementally as new events arrive, rather than replaying the entire history on every read.

- Stream-table duality means a stream of changes and a table of current state are two views of the same underlying facts — one can always be derived from the other.
- Maintaining both independently, as two separately-updated structures, risks them silently drifting out of sync if any code path updates one but forgets the other.
- Deriving the table by folding the stream (rather than maintaining it separately) makes disagreement structurally impossible, since the table is a pure function of the stream, not independent state.
- Multiple, differently-shaped views can all be derived from the exact same single stream, letting new views be added without touching how events are originally recorded.
- Real systems cache and incrementally update derived views rather than refolding the entire stream on every read, once the stream grows large.
