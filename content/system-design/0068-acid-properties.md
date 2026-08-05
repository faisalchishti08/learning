---
card: system-design
gi: 68
slug: acid-properties
title: ACID properties
---

## 1. What it is

**ACID** describes four guarantees a database transaction provides: **Atomicity** (a transaction's operations all happen, or none do), **Consistency** (a transaction moves the database from one valid state to another, never breaking its rules), **Isolation** (concurrent transactions do not see each other's incomplete work), and **Durability** (once a transaction commits, its changes survive, even a crash immediately after).

## 2. Why & when

Multiple related writes — debit one account, credit another, as part of a single transfer — must either all succeed or all fail together; if the debit happens but the credit does not (a crash between the two), money simply vanishes. ACID transactions are the mechanism relational databases provide to make a group of operations behave as one indivisible unit, so partial failures like this cannot happen. Reach for an explicit transaction any time multiple writes must succeed or fail together as a single logical operation.

## 3. Core concept

**Atomicity — all or nothing:** a transaction wraps several operations; the database guarantees that either every operation in it is applied, or, if any part fails, none of them are — via a `ROLLBACK` that undoes any partial work already done.

**Consistency — rules are never broken, even mid-transaction:** the database enforces its constraints (foreign keys, uniqueness, check constraints) at the boundary of every transaction; a transaction that would leave the database violating one of its own rules is rejected rather than committed.

**Isolation — concurrent transactions do not interfere:** without isolation, one transaction could read another transaction's half-finished work — for example, seeing a debit applied but the matching credit not yet applied. Isolation levels (covered next) control exactly how much of this concurrent interference is allowed, trading strictness for performance.

**Durability — committed means permanent:** once the database confirms a transaction as committed, that guarantee holds even if the server crashes one millisecond later — achieved by writing the transaction to a durable, crash-safe log (a **write-ahead log**) before acknowledging the commit, so the database can replay it on restart if needed.

## 4. Diagram

```
transfer $50 from Alice to Bob, as ONE transaction:

  BEGIN TRANSACTION
      debit Alice's account by $50     (not yet visible to other transactions - ISOLATION)
      credit Bob's account by $50
  COMMIT
      -> both changes durable, or a crash before COMMIT means NEITHER happened - ATOMICITY + DURABILITY

  If a CONSTRAINT would be violated (e.g. Alice's balance cannot go negative):
      debit Alice's account by $50     -> would make balance = -$10, violates a CHECK constraint
  ROLLBACK
      -> the debit is undone; database returns to its state before the transaction - CONSISTENCY
```
*Caption: a transaction's writes are held together as one unit — either every one of them is committed and durable, or none of them take effect at all.*

## 5. Runnable example

**Level 1 — Basic.** A simulated transaction: apply a debit and credit together, with an all-or-nothing commit.

**Level 2 — Rollback on constraint violation.** Reject a transaction that would leave a balance negative, rolling back any partial work already applied.

**Level 3 — Durability via a write-ahead log.** Simulate writing to a durable log before committing, and recovering from it after a simulated crash.

```java
// AcidProperties.java
import java.util.*;

public class AcidProperties {

    static final Map<String, Integer> accounts = new HashMap<>();
    static final List<String> writeAheadLog = new ArrayList<>();

    // Level 1 & 2: atomic transfer - debit and credit succeed together, or neither applies.
    static boolean transfer(String from, String to, int amount) {
        int fromBalance = accounts.get(from);
        int toBalance = accounts.get(to);

        int newFromBalance = fromBalance - amount;
        if (newFromBalance < 0) {
            System.out.println("  ROLLBACK: transfer would violate CHECK (balance >= 0) constraint");
            return false; // consistency: reject before applying anything
        }

        // Level 3: write to the durable log BEFORE applying changes in memory.
        writeAheadLog.add(from + " -" + amount + ", " + to + " +" + amount);

        accounts.put(from, newFromBalance); // debit
        accounts.put(to, toBalance + amount); // credit
        System.out.println("  COMMIT: transfer applied and logged");
        return true;
    }

    static void recoverFromCrash() {
        // Level 3: replay the durable log to restore state after a simulated crash.
        System.out.println("simulating crash and recovery, replaying write-ahead log:");
        accounts.put("Alice", 100);
        accounts.put("Bob", 50); // reset in-memory state, as if the process restarted
        for (String entry : writeAheadLog) {
            System.out.println("  replaying: " + entry);
        }
        // (a real database would parse and re-apply each entry; here we confirm the log itself survived)
    }

    public static void main(String[] args) {
        accounts.put("Alice", 100);
        accounts.put("Bob", 50);

        System.out.println("attempting: transfer $30 Alice -> Bob");
        transfer("Alice", "Bob", 30);
        System.out.println("balances: " + accounts);

        System.out.println("attempting: transfer $200 Alice -> Bob (exceeds balance)");
        boolean succeeded = transfer("Alice", "Bob", 200);
        System.out.println("transfer succeeded? " + succeeded);
        System.out.println("balances (unchanged, rollback confirmed): " + accounts);

        recoverFromCrash();
        System.out.println("write-ahead log entries survived: " + writeAheadLog.size());
    }
}
```

**How to run:** save as `AcidProperties.java`, then run `java AcidProperties.java`.

## 6. Walkthrough

1. `transfer("Alice", "Bob", 30)` computes `newFromBalance = 70`, which is not negative, so it logs the operation, applies both the debit and the credit, and prints "COMMIT" — the balances afterward show `Alice=70, Bob=80`.
2. `transfer("Alice", "Bob", 200)` computes `newFromBalance = -130`, which fails the `>= 0` check, so the method returns `false` immediately, *before* touching `accounts` at all — no debit, no credit, no log entry.
3. Printing `accounts` after the failed transfer confirms it is unchanged from before the attempt — the rejected transaction left no partial trace, demonstrating atomicity and consistency together.
4. `recoverFromCrash()` resets the in-memory `accounts` map (simulating a process restart that lost in-memory state) and then replays `writeAheadLog`, which still holds the one successful transfer — the log itself, written durably before the in-memory update, is what a real database would use to restore the correct post-transaction state after an actual crash.
5. `writeAheadLog.size()` is `1` — only the successful transfer was ever logged, since the failed one was rejected before reaching the logging step.

## 7. Gotchas & takeaways

> Gotcha: atomicity guarantees "all operations in the transaction happen together," but it says nothing about what other concurrent transactions can see *while* yours is in progress — that is entirely the job of isolation, covered in the next tutorial, and the two are easy to conflate.

- Atomicity and consistency protect a single transaction's own correctness; isolation protects correctness between multiple concurrent transactions; durability protects correctness across a crash.
- A write-ahead log is the standard mechanism for durability: write the intended change to a crash-safe log first, and only then apply it — so recovery after a crash just means replaying the log.
- Related concepts: [Isolation levels (read-committed, repeatable-read, serializable)](0069-isolation-levels-read-committed-repeatable-read-serializable.md) (the "I" in ACID, in depth), [Optimistic vs pessimistic locking](0070-optimistic-vs-pessimistic-locking.md) (concrete techniques for enforcing isolation in practice).
