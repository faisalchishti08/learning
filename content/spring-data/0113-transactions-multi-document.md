---
card: spring-data
gi: 113
slug: transactions-multi-document
title: "Transactions (multi-document)"
---

## 1. What it is

A **multi-document transaction** lets several writes across one or more MongoDB collections succeed or fail **together**, as a single atomic unit — exactly like a relational transaction. Spring Data MongoDB exposes this through `MongoTransactionManager` combined with the familiar `@Transactional` annotation, or programmatically via `mongoTemplate.inTransaction(session -> ...)`.

```java
@Transactional
public void transferFunds(String fromId, String toId, double amount) {
    accountRepository.debit(fromId, amount);
    accountRepository.credit(toId, amount); // if THIS fails, the debit above is rolled back too
}
```

## 2. Why & when

MongoDB has always guaranteed atomicity for a **single** document write — one `updateOne` call either fully applies or doesn't happen at all. Multi-document transactions extend that guarantee across **multiple** documents, and even multiple collections, which matters whenever an operation needs "all of this or none of this" semantics that a single document can't express on its own.

Reach for a multi-document transaction when:

- Moving a value between two documents — debiting one account and crediting another must not be allowed to happen only halfway, or money is created or destroyed.
- Writing to two related collections that must stay consistent — creating an `Order` document and a matching `Invoice` document, where one existing without the other is a bug.
- Performing a read-then-write sequence that must see a consistent snapshot and not be interleaved with another transaction's writes to the same documents.

Multi-document transactions require a replica set (or sharded cluster) just like change streams, and they carry a real performance cost — MongoDB's document model is designed so that a well-shaped schema (embedding related data in one document) often avoids needing a multi-document transaction at all. Reach for one when embedding genuinely doesn't fit, not as a default habit.

## 3. Core concept

```
 WITHOUT a transaction:
   debit(A, 100)   -- succeeds, committed immediately
   credit(B, 100)  -- fails (network blip) -- A's debit is now PERMANENT and unmatched -- money vanished

 WITH a transaction:
   session.startTransaction()
     debit(A, 100)    -- staged, not yet visible to other readers
     credit(B, 100)   -- fails
   session.abortTransaction()  -- BOTH writes are undone, as if neither happened
```

The transaction turns "two separate atomic writes" into "one atomic unit" — either both apply, or the collection ends up exactly as if neither write was attempted.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A transaction wraps a debit and a credit write so both commit together or both roll back together">
  <rect x="20" y="20" width="600" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="50" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">session.startTransaction()</text>

  <rect x="60" y="90" width="220" height="45" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="170" y="117" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">debit(accountA, 100)</text>

  <rect x="360" y="90" width="220" height="45" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="470" y="117" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">credit(accountB, 100)</text>

  <rect x="20" y="150" width="290" height="35" rx="6" fill="#3fb95022" stroke="#3fb950" stroke-width="1.3"/>
  <text x="165" y="172" fill="#3fb950" font-size="10" text-anchor="middle" font-family="sans-serif">both succeed -&gt; commitTransaction()</text>

  <rect x="330" y="150" width="290" height="35" rx="6" fill="#f8514922" stroke="#f85149" stroke-width="1.3"/>
  <text x="475" y="172" fill="#f85149" font-size="10" text-anchor="middle" font-family="sans-serif">either fails -&gt; abortTransaction()</text>
</svg>

Both writes are staged inside the same transaction; only a full commit makes either one durable and visible.

## 5. Runnable example

The scenario: transferring money between two accounts, evolving from an unsafe two-step write that can lose money on partial failure, to a transaction that rolls back cleanly, to a version that retries on the transient errors MongoDB's drivers explicitly recommend retrying.

### Level 1 — Basic

Show the problem: two independent, non-transactional writes, where a failure between them leaves data inconsistent.

```java
import java.util.*;

public class TransactionsLevel1 {
    public static void main(String[] args) {
        AccountsCollection accounts = new AccountsCollection();
        accounts.docs.put("A", new Account("A", 500));
        accounts.docs.put("B", new Account("B", 100));

        try {
            accounts.debit("A", 100);              // this write is ALREADY permanent
            accounts.credit("B", 100, true);        // this one fails
        } catch (RuntimeException e) {
            System.out.println("Credit failed: " + e.getMessage());
        }

        System.out.println("A balance: " + accounts.docs.get("A").balance + " (debited, but B never got it!)");
        System.out.println("B balance: " + accounts.docs.get("B").balance);
    }
}

class Account { String id; double balance; Account(String id, double balance) { this.id = id; this.balance = balance; } }

// Stands in for a MongoTemplate/repository with NO transaction wrapping these two calls.
class AccountsCollection {
    Map<String, Account> docs = new HashMap<>();
    void debit(String id, double amount) { docs.get(id).balance -= amount; } // committed the instant it runs
    void credit(String id, double amount, boolean simulateFailure) {
        if (simulateFailure) throw new RuntimeException("network blip during credit");
        docs.get(id).balance += amount;
    }
}
```

How to run: `java TransactionsLevel1.java`

`debit` and `credit` are two separate, independently committed writes. When `credit` fails, `debit` has already happened and cannot be undone — `$100` has effectively vanished from the system. This is exactly the failure mode multi-document transactions exist to prevent.

### Level 2 — Intermediate

Wrap both writes in a transaction: on any failure, everything staged during the transaction is rolled back, leaving both accounts untouched.

```java
import java.util.*;

public class TransactionsLevel2 {
    static void transferFunds(AccountsCollection accounts, String from, String to, double amount, boolean simulateFailure) {
        try {
            accounts.debit(from, amount);
            accounts.credit(to, amount, simulateFailure);
            accounts.commitTransaction(); // BOTH writes become visible together
        } catch (RuntimeException e) {
            accounts.abortTransaction();   // NEITHER write becomes visible
            System.out.println("Transaction aborted: " + e.getMessage());
        }
    }

    public static void main(String[] args) {
        AccountsCollection accounts = new AccountsCollection();
        accounts.docs.put("A", new Account("A", 500));
        accounts.docs.put("B", new Account("B", 100));

        transferFunds(accounts, "A", "B", 100, true); // fails -- both writes rolled back

        System.out.println("A balance: " + accounts.docs.get("A").balance + " (unchanged)");
        System.out.println("B balance: " + accounts.docs.get("B").balance + " (unchanged)");
    }
}

class Account { String id; double balance; Account(String id, double balance) { this.id = id; this.balance = balance; } }

// Stands in for a MongoTemplate/repository call wrapped by @Transactional / MongoTransactionManager.
class AccountsCollection {
    Map<String, Account> docs = new HashMap<>();
    Map<String, Double> stagedChanges = new HashMap<>(); // writes staged, not yet applied to `docs`

    void debit(String id, double amount) { stagedChanges.merge(id, -amount, Double::sum); }
    void credit(String id, double amount, boolean simulateFailure) {
        if (simulateFailure) throw new RuntimeException("network blip during credit");
        stagedChanges.merge(id, amount, Double::sum);
    }

    void commitTransaction() { // session.commitTransaction()
        for (var entry : stagedChanges.entrySet()) docs.get(entry.getKey()).balance += entry.getValue();
        stagedChanges.clear();
    }
    void abortTransaction() { stagedChanges.clear(); } // session.abortTransaction() -- discards ALL staged writes
}
```

How to run: `java TransactionsLevel2.java`

`debit` and `credit` now only stage changes in `stagedChanges`; nothing touches the real `docs` map until `commitTransaction()` runs. Because `credit` throws, `abortTransaction()` discards the staged debit too — both balances stay exactly as they started, unlike Level 1 where the debit had already leaked through.

### Level 3 — Advanced

Add retry logic for **transient transaction errors** — MongoDB's drivers attach a `TransientTransactionError` label to certain failures (like a replica set election happening mid-transaction) and explicitly recommend retrying the whole transaction when one occurs.

```java
import java.util.*;
import java.util.function.*;

public class TransactionsLevel3 {
    // Mirrors MongoDB's documented "withTransaction" retry loop for TransientTransactionError.
    static void transferWithRetry(AccountsCollection accounts, String from, String to, double amount) {
        int maxAttempts = 5;
        for (int attempt = 1; attempt <= maxAttempts; attempt++) {
            try {
                accounts.debit(from, amount);
                accounts.credit(to, amount);
                accounts.commitTransaction();
                System.out.println("Committed on attempt " + attempt);
                return;
            } catch (TransientTransactionError e) {
                accounts.abortTransaction();
                System.out.println("Attempt " + attempt + " hit a transient error (" + e.getMessage() + "), retrying...");
            }
        }
        throw new IllegalStateException("transaction failed after " + maxAttempts + " attempts");
    }

    public static void main(String[] args) {
        AccountsCollection accounts = new AccountsCollection();
        accounts.docs.put("A", new Account("A", 500));
        accounts.docs.put("B", new Account("B", 100));

        transferWithRetry(accounts, "A", "B", 100);

        System.out.println("A balance: " + accounts.docs.get("A").balance);
        System.out.println("B balance: " + accounts.docs.get("B").balance);
    }
}

class Account { String id; double balance; Account(String id, double balance) { this.id = id; this.balance = balance; } }

class TransientTransactionError extends RuntimeException { // carries the "TransientTransactionError" label
    TransientTransactionError(String msg) { super(msg); }
}

class AccountsCollection {
    Map<String, Account> docs = new HashMap<>();
    Map<String, Double> stagedChanges = new HashMap<>();
    int attemptCount = 0;

    void debit(String id, double amount) { stagedChanges.merge(id, -amount, Double::sum); }
    void credit(String id, double amount) {
        attemptCount++;
        if (attemptCount < 3) throw new TransientTransactionError("replica set election in progress"); // fails twice, then succeeds
        stagedChanges.merge(id, amount, Double::sum);
    }
    void commitTransaction() {
        for (var entry : stagedChanges.entrySet()) docs.get(entry.getKey()).balance += entry.getValue();
        stagedChanges.clear();
    }
    void abortTransaction() { stagedChanges.clear(); }
}
```

How to run: `java TransactionsLevel3.java`

`credit` is rigged to throw a `TransientTransactionError` on its first two attempts, standing in for a real, transient MongoDB failure (like a brief replica set election). `transferWithRetry` catches exactly that error type, aborts the partial transaction, and retries the **entire** transfer from scratch — it does not try to resume mid-transaction, because a transient error means the whole transaction was never actually applied. On the third attempt it succeeds and commits.

## 6. Walkthrough

Execution starts in `main` for Level 3, seeding accounts `A` (balance `500`) and `B` (balance `100`), then calling `transferWithRetry(accounts, "A", "B", 100)`.

Attempt `1`: `debit("A", 100)` stages `-100` for `A`. `credit("B", 100)` increments `attemptCount` to `1`, which is `< 3`, so it throws `TransientTransactionError`. The `catch` block calls `abortTransaction()`, discarding the staged debit, and prints a retry message.

Attempt `2`: the same sequence runs again — `debit` re-stages `-100` for `A`, `credit` increments `attemptCount` to `2`, still `< 3`, throws again, and the transaction is aborted a second time.

Attempt `3`: `debit` stages `-100` again, and this time `credit` increments `attemptCount` to `3`, which is no longer `< 3`, so it stages `+100` for `B` instead of throwing. `commitTransaction()` then applies both staged changes to the real `docs` map in one step — `A.balance` becomes `400`, `B.balance` becomes `200` — and the method returns.

```
Attempt 1 hit a transient error (replica set election in progress), retrying...
Attempt 2 hit a transient error (replica set election in progress), retrying...
Committed on attempt 3
A balance: 400.0
B balance: 200.0
```

In real Spring Data MongoDB, this retry pattern is exactly what MongoDB's own driver-level `ClientSession.withTransaction(...)` helper implements internally, and `@Transactional` methods backed by `MongoTransactionManager` can be configured with a retry-aware wrapper for the same reason: a `TransientTransactionError` means the transaction as a whole never committed, so the only correct recovery is re-running the whole block, not patching up individual statements.

## 7. Gotchas & takeaways

> Gotcha: on a `TransientTransactionError`, retry the **entire transaction body from the top**, never just the statement that failed — a partially-applied transaction was aborted in full, so resuming mid-way would silently skip earlier writes.

> Gotcha: multi-document transactions need a replica set and have real overhead (holding locks, WiredTiger snapshot bookkeeping) — a schema that embeds related data into a single document to avoid needing a transaction at all is usually the better MongoDB-native design when it fits the access pattern.

- Wrap operations that must succeed or fail together in a transaction (`@Transactional` + `MongoTransactionManager`, or `mongoTemplate.inTransaction(...)`), not as separate independent writes.
- A failed transaction rolls back everything staged inside it — the collections end up exactly as if the transaction had never started.
- Errors tagged `TransientTransactionError` are expected and retryable; the standard pattern is retry-the-whole-transaction with a bounded attempt count.
- Prefer embedding related data in one document over a multi-document transaction whenever the access pattern allows it — it is usually simpler and faster.
