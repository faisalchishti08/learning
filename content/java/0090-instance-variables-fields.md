---
card: java
gi: 90
slug: instance-variables-fields
title: Instance variables (fields)
---

## 1. What it is

An instance variable (also called an instance field) is a variable declared inside a class body but outside any method. Each object created from the class gets its own independent copy of every instance field. Instance fields are initialised to their zero-like default when the object is created, and can be explicitly initialised at the declaration site or inside a constructor.

```java
class BankAccount {
    String owner;          // default: null
    double balance;        // default: 0.0
    boolean frozen = false; // explicit default at declaration
    final String id;       // final field — must be assigned in constructor

    BankAccount(String owner, String id) {
        this.owner = owner;
        this.id    = id;
    }
}
```

## 2. Why & when

Instance fields hold the **state** of an object — the data that distinguishes one instance from another. They are the right place for:
- Values that vary per object (`name`, `balance`, `id`).
- Objects that an instance owns or delegates to (`engine` in a `Car`).
- Cached computed values that belong to one specific instance.

Avoid putting values in instance fields when they are the same for every object (use `static` constants) or when they are only needed during one method call (use local variables).

## 3. Core concept

```java
public class InstanceFields {

    // ---- Instance fields ----
    String  name;              // default: null
    int     age;               // default: 0
    double  salary;            // default: 0.0
    boolean active = true;     // explicit initializer at declaration
    final   String id;         // final — assigned once in constructor

    // ---- Instance initializer block (rare) ----
    {
        salary = 50_000.0;     // runs before constructor body
    }

    InstanceFields(String name, int age, String id) {
        this.name = name;
        this.age  = age;
        this.id   = id;        // final field assigned in constructor
    }

    @Override
    public String toString() {
        return String.format("Employee{id=%s, name=%s, age=%d, salary=%.0f, active=%b}",
            id, name, age, salary, active);
    }

    public static void main(String[] args) {
        InstanceFields alice = new InstanceFields("Alice", 30, "E001");
        InstanceFields bob   = new InstanceFields("Bob",   25, "E002");

        System.out.println(alice);
        System.out.println(bob);

        // Each object has its own copy of fields
        alice.salary = 60_000.0;
        System.out.println("Alice salary: " + alice.salary);  // 60000
        System.out.println("Bob   salary: " + bob.salary);    // 50000 — unchanged

        // final field cannot be reassigned
        // alice.id = "X";   // compile error

        // Access via this
        alice.printInfo();
        bob.printInfo();
    }

    void printInfo() {
        // 'this' refers to the current instance
        System.out.printf("[%s] age=%d, active=%b%n", this.name, this.age, this.active);
    }
}
```

## 4. Diagram

<svg viewBox="0 0 700 180" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Instance fields: two BankAccount objects each with their own independent copy of fields owner/balance/id; class blueprint on left, two heap objects on right">
  <rect x="8" y="8" width="684" height="164" rx="8" fill="#0d1117"/>

  <!-- Class blueprint -->
  <rect x="16" y="18" width="200" height="138" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="116" y="36" fill="#6db33f" font-size="9" text-anchor="middle" font-family="monospace">class BankAccount</text>
  <text x="116" y="50" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">blueprint (class in memory)</text>
  <line x1="26" y1="56" x2="206" y2="56" stroke="#8b949e" stroke-width="0.5"/>
  <text x="26" y="70" fill="#e6edf3" font-size="7.5" font-family="monospace">  String owner</text>
  <text x="26" y="83" fill="#e6edf3" font-size="7.5" font-family="monospace">  double balance</text>
  <text x="26" y="96" fill="#e6edf3" font-size="7.5" font-family="monospace">  boolean frozen</text>
  <text x="26" y="109" fill="#e6edf3" font-size="7.5" font-family="monospace">  final String id</text>
  <line x1="26" y1="116" x2="206" y2="116" stroke="#8b949e" stroke-width="0.5"/>
  <text x="26" y="130" fill="#8b949e" font-size="7.5" font-family="monospace">  deposit(amount)</text>
  <text x="26" y="143" fill="#8b949e" font-size="7.5" font-family="monospace">  getBalance()</text>

  <!-- Arrow to instances -->
  <line x1="216" y1="87" x2="256" y2="60"  stroke="#8b949e" stroke-width="1" stroke-dasharray="4"/>
  <line x1="216" y1="87" x2="256" y2="130" stroke="#8b949e" stroke-width="1" stroke-dasharray="4"/>
  <text x="232" y="90" fill="#8b949e" font-size="7" font-family="sans-serif">new</text>

  <!-- Object 1 -->
  <rect x="258" y="18" width="194" height="138" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="355" y="36" fill="#79c0ff" font-size="8.5" text-anchor="middle" font-family="monospace">account1 (heap)</text>
  <line x1="268" y1="42" x2="442" y2="42" stroke="#8b949e" stroke-width="0.5"/>
  <text x="268" y="57" fill="#e6edf3" font-size="8" font-family="monospace">owner   = "Alice"</text>
  <text x="268" y="71" fill="#e6edf3" font-size="8" font-family="monospace">balance = 1500.00</text>
  <text x="268" y="85" fill="#e6edf3" font-size="8" font-family="monospace">frozen  = false</text>
  <text x="268" y="99" fill="#e6edf3" font-size="8" font-family="monospace">id      = "ACC001"</text>

  <!-- Object 2 -->
  <rect x="464" y="18" width="210" height="138" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="569" y="36" fill="#79c0ff" font-size="8.5" text-anchor="middle" font-family="monospace">account2 (heap)</text>
  <line x1="474" y1="42" x2="664" y2="42" stroke="#8b949e" stroke-width="0.5"/>
  <text x="474" y="57" fill="#e6edf3" font-size="8" font-family="monospace">owner   = "Bob"</text>
  <text x="474" y="71" fill="#e6edf3" font-size="8" font-family="monospace">balance = 250.00</text>
  <text x="474" y="85" fill="#e6edf3" font-size="8" font-family="monospace">frozen  = true</text>
  <text x="474" y="99" fill="#e6edf3" font-size="8" font-family="monospace">id      = "ACC002"</text>
  <text x="474" y="126" fill="#8b949e" font-size="7.5" font-family="sans-serif">Independent copies —</text>
  <text x="474" y="139" fill="#8b949e" font-size="7.5" font-family="sans-serif">changing one doesn't affect other</text>
</svg>

The class acts as a blueprint; each `new BankAccount(...)` allocates a separate heap object with its own independent copy of every instance field.

## 5. Runnable example

Scenario: a bank account system — each account object holds its own balance and transaction history. The example grows from basic field access, to demonstrating independent per-instance state, to a full account with encapsulated mutable fields and a `final` immutable ID.

### Level 1 — Basic

```java
public class InstanceFieldsBasic {

    static class BankAccount {
        String owner;          // instance field
        double balance;        // default 0.0
        int    transactions;   // default 0
        final  String id;

        BankAccount(String id, String owner, double initialBalance) {
            this.id      = id;
            this.owner   = owner;
            this.balance = initialBalance;
        }

        void deposit(double amount) {
            balance += amount;
            transactions++;
        }
    }

    public static void main(String[] args) {
        BankAccount alice = new BankAccount("ACC001", "Alice", 1000.0);
        BankAccount bob   = new BankAccount("ACC002", "Bob",    250.0);

        alice.deposit(500.0);
        alice.deposit(200.0);
        bob.deposit(100.0);

        System.out.printf("%-6s %-6s  $%8.2f  %d txns%n",
            alice.id, alice.owner, alice.balance, alice.transactions);
        System.out.printf("%-6s %-6s  $%8.2f  %d txns%n",
            bob.id, bob.owner, bob.balance, bob.transactions);

        System.out.println("\nAlice and Bob have independent balances: "
            + (alice.balance != bob.balance));
    }
}
```

**How to run:** `java InstanceFieldsBasic.java`

`alice.balance` and `bob.balance` are independent copies — depositing into Alice's account does not affect Bob's. `final String id` is assigned once in the constructor and cannot be changed afterwards. `transactions` counts deposits independently for each account.

### Level 2 — Intermediate

Same account system: add encapsulation (`private` fields, public methods), an instance initializer block, and a `toString` override.

```java
public class InstanceFieldsIntermediate {

    static class BankAccount {
        private final String id;
        private final String owner;
        private double balance;
        private boolean frozen;
        private int    txCount;

        // Instance initializer runs before constructor body
        {
            this.frozen  = false;
            this.txCount = 0;
        }

        BankAccount(String id, String owner, double initialBalance) {
            if (initialBalance < 0)
                throw new IllegalArgumentException("Initial balance cannot be negative");
            this.id      = id;
            this.owner   = owner;
            this.balance = initialBalance;
        }

        boolean deposit(double amount) {
            if (frozen || amount <= 0) return false;
            balance += amount;
            txCount++;
            return true;
        }

        boolean withdraw(double amount) {
            if (frozen || amount <= 0 || amount > balance) return false;
            balance -= amount;
            txCount++;
            return true;
        }

        void freeze()   { frozen = true; }
        void unfreeze() { frozen = false; }

        double  getBalance()  { return balance; }
        boolean isFrozen()    { return frozen; }
        int     getTxCount()  { return txCount; }

        @Override public String toString() {
            return String.format("Account{id=%s, owner=%s, balance=%.2f, frozen=%b, txns=%d}",
                id, owner, balance, frozen, txCount);
        }
    }

    public static void main(String[] args) {
        BankAccount acc = new BankAccount("ACC001", "Alice", 1_000.0);
        System.out.println("Initial: " + acc);

        acc.deposit(300.0);
        acc.withdraw(150.0);
        System.out.println("After 2 txns: " + acc);

        acc.freeze();
        System.out.println("Frozen deposit success: " + acc.deposit(100.0));  // false
        System.out.println("After freeze attempt: " + acc);

        acc.unfreeze();
        acc.deposit(50.0);
        System.out.println("After unfreeze+deposit: " + acc);
    }
}
```

**How to run:** `java InstanceFieldsIntermediate.java`

The instance initializer `{ frozen = false; txCount = 0; }` runs before any constructor body, useful when multiple constructors share common setup code. `private` fields are only accessible through the class's own methods — callers cannot accidentally corrupt `balance` by writing `acc.balance = -1`. `final String id` ensures the account's identity never changes for the lifetime of the object.

### Level 3 — Advanced

Same system: add a transfer operation that acts on two account objects, show how each object's fields are modified independently, and track a shared transaction log using a `static` field (contrast with instance fields).

```java
import java.util.ArrayList;
import java.util.List;

public class InstanceFieldsAdvanced {

    static class BankAccount {
        private final String    id;
        private final String    owner;
        private double          balance;
        private boolean         frozen;
        private int             txCount;

        // Static field — shared across ALL instances (contrast with instance fields)
        private static final List<String> AUDIT_LOG = new ArrayList<>();

        BankAccount(String id, String owner, double init) {
            this.id = id; this.owner = owner; this.balance = init;
        }

        boolean transfer(BankAccount target, double amount) {
            if (frozen || target.frozen) return false;
            if (amount <= 0 || amount > balance) return false;
            this.balance   -= amount;
            target.balance += amount;
            this.txCount++;
            target.txCount++;
            AUDIT_LOG.add(String.format("%s → %s : $%.2f", this.id, target.id, amount));
            return true;
        }

        void freeze()          { frozen = true; }
        double getBalance()    { return balance; }
        int    getTxCount()    { return txCount; }
        String getId()         { return id; }

        @Override public String toString() {
            return String.format("%-7s %-6s $%8.2f  txns=%-2d frozen=%b",
                id, owner, balance, txCount, frozen);
        }
    }

    public static void main(String[] args) {
        var alice = new BankAccount("ACC001", "Alice",  2_000.0);
        var bob   = new BankAccount("ACC002", "Bob",      500.0);
        var carol = new BankAccount("ACC003", "Carol",  1_200.0);

        alice.transfer(bob, 300.0);
        carol.transfer(alice, 150.0);
        bob.freeze();
        carol.transfer(bob, 100.0);   // fails — bob is frozen

        System.out.println("=== Account balances ===");
        for (var acc : List.of(alice, bob, carol)) {
            System.out.println("  " + acc);
        }

        System.out.println("\n=== Audit log (static — shared) ===");
        BankAccount.AUDIT_LOG.forEach(entry -> System.out.println("  " + entry));
        System.out.println("Log size: " + BankAccount.AUDIT_LOG.size());
    }
}
```

**How to run:** `java InstanceFieldsAdvanced.java`

`transfer` operates on two distinct objects: `this.balance -= amount` modifies the calling account's own `balance` field (an instance field), while `target.balance += amount` modifies the target's own `balance` field. Each field update is completely independent — they share no memory. By contrast, `AUDIT_LOG` is a `static` field — it is shared across all `BankAccount` instances. Both successful transfers append to the same log regardless of which account's `transfer` method was called.

## 6. Walkthrough

Execution trace through `InstanceFieldsAdvanced.main`:

**Object creation.** `new BankAccount("ACC001", "Alice", 2000.0)` allocates a heap object. Its fields are: `id="ACC001"`, `owner="Alice"`, `balance=2000.0`, `frozen=false`, `txCount=0`. Similarly for `bob` and `carol`.

**`alice.transfer(bob, 300.0)`.** Inside `transfer`: `this` = alice object, `target` = bob object. Guard checks: `alice.frozen = false`, `bob.frozen = false`, `300.0 <= 0` = false, `300.0 > alice.balance=2000.0` = false — all pass. `alice.balance = 2000 − 300 = 1700`. `bob.balance = 500 + 300 = 800`. Both `txCount` increment. `"ACC001 → ACC002 : $300.00"` appended to `AUDIT_LOG`.

**`bob.freeze()`.** Sets `bob.frozen = true`. `carol.transfer(bob, 100.0)`: the guard `target.frozen` is true → returns `false`. No balance changes, no log entry.

**Audit log.** `AUDIT_LOG` is a `static` field — only one instance exists regardless of how many `BankAccount` objects exist. Both successful transfers wrote to it. The third transfer failed and wrote nothing.

```
After all operations:
  alice: balance=1700+150=1850  txns=2
  bob:   balance=800             txns=1  frozen
  carol: balance=1200-150=1050   txns=1

AUDIT_LOG (static, shared):
  "ACC001 → ACC002 : $300.00"
  "ACC003 → ACC001 : $150.00"
```

## 7. Gotchas & takeaways

> **Instance fields are not thread-safe by default.** If two threads call `deposit` on the same account simultaneously, both may read the same `balance` and write back different sums, losing one deposit. Use `synchronized`, `AtomicDouble`, or immutable value objects to protect shared mutable state.

> **`final` instance fields must be assigned exactly once — either at declaration, in an instance initializer, or in every constructor.** A `final` field that is not assigned in all constructors is a compile error.

- Instance fields store per-object state; each `new` call produces a completely independent set of field values.
- Fields are zero-initialised by the JVM before any constructor or initializer runs.
- Declare fields `private` by default; expose them through methods to maintain invariants.
- `final` fields communicate immutability of identity — use them for IDs and other values that should never change.
- Instance initializer blocks `{ }` run before the constructor body and are shared across constructors.
- Distinguish instance fields (per-object) from `static` fields (per-class, shared across all instances).
