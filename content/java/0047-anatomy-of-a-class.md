---
card: java
gi: 47
slug: anatomy-of-a-class
title: Anatomy of a class
---

## 1. What it is

A **Java class** is the fundamental building block of every Java program. A class file contains the blueprint — fields (data) and methods (behaviour) — from which the JVM creates object instances at runtime.

Every piece of Java code lives inside a class. A minimal runnable program is a single class with a `main` method. A large application has hundreds of classes, each modelling one concept.

```java
public class BankAccount {           // class declaration
    private double balance;          // field
    private final String owner;      // field (immutable)

    public BankAccount(String owner, double initial) {  // constructor
        this.owner = owner;
        this.balance = initial;
    }

    public void deposit(double amount) {  // method
        balance += amount;
    }

    public double getBalance() {          // method
        return balance;
    }
}
```

## 2. Why & when

Understanding class anatomy matters because:
- **Every Java feature maps onto a class element.** Generics are on type declarations. Annotations go on fields, methods, or the class itself. Access modifiers control visibility from other classes.
- **The compiler enforces class structure.** A field accessed before assignment, a missing constructor call, a return type mismatch — all compile errors. Knowing where each element belongs eliminates confusion.
- **Java is a class-based language.** Unlike scripting languages where code can float at file scope, every statement in Java lives inside a class member.

## 3. Core concept

```
[access] [modifiers] class <ClassName> [extends <Parent>] [implements <I1>, <I2>] {
    // -- Fields (instance state) --
    [access] [static] [final] <Type> fieldName [= initialValue];

    // -- Static initialiser (runs once when class loads) --
    static { ... }

    // -- Instance initialiser (runs before each constructor) --
    { ... }

    // -- Constructors --
    [access] <ClassName>([params]) [throws <Exception>] { ... }

    // -- Methods --
    [access] [static] [final] [synchronized] <returnType> methodName([params]) { ... }

    // -- Nested classes (inner, static nested, local, anonymous) --
    [static] class Inner { ... }
}
```

Key elements explained:

| Element | Keyword(s) | Purpose |
|---------|-----------|---------|
| Access modifier | `public` `protected` `private` (none=package) | Controls who can see this member |
| `static` | `static` | Belongs to the class, not an instance |
| `final` | `final` on class = no subclassing; on field = immutable reference; on method = no override |
| Field | `<Type> name` | State stored per instance (or per class if static) |
| Constructor | `<ClassName>(...)` | Initialises a new instance; called by `new` |
| Method | `<return> name(...)` | Behaviour; `void` = no return |
| `this` | `this` | Reference to the current instance |
| `super` | `super` | Reference to parent class constructor/method |

## 4. Diagram

<svg viewBox="0 0 700 250" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Anatomy of a Java class showing its major structural sections">
  <rect x="8" y="8" width="684" height="234" rx="8" fill="#0d1117"/>

  <!-- Class border -->
  <rect x="20" y="20" width="655" height="210" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>

  <!-- Class declaration -->
  <rect x="20" y="20" width="655" height="30" rx="6" fill="#6db33f" fill-opacity="0.2"/>
  <text x="40" y="40" fill="#6db33f" font-size="10" font-family="monospace">public class BankAccount extends Object implements Serializable {</text>

  <!-- Fields section -->
  <rect x="35" y="58" width="250" height="55" rx="4" fill="#0d1117" stroke="#79c0ff" stroke-width="1"/>
  <text x="50" y="73" fill="#79c0ff" font-size="9" font-family="monospace">// Fields</text>
  <text x="50" y="87" fill="#e6edf3" font-size="9" font-family="monospace">private double balance;</text>
  <text x="50" y="101" fill="#e6edf3" font-size="9" font-family="monospace">private final String owner;</text>

  <!-- Static block -->
  <rect x="300" y="58" width="180" height="55" rx="4" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="315" y="73" fill="#8b949e" font-size="9" font-family="monospace">// Static init</text>
  <text x="315" y="87" fill="#e6edf3" font-size="9" font-family="monospace">static {</text>
  <text x="315" y="101" fill="#8b949e" font-size="9" font-family="monospace">  // runs once on load</text>

  <!-- Nested class indicator -->
  <rect x="495" y="58" width="165" height="55" rx="4" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="510" y="73" fill="#8b949e" font-size="9" font-family="monospace">// Nested types</text>
  <text x="510" y="87" fill="#8b949e" font-size="9" font-family="monospace">static class Builder { }</text>
  <text x="510" y="101" fill="#8b949e" font-size="9" font-family="monospace">enum Status { OPEN }</text>

  <!-- Constructor -->
  <rect x="35" y="125" width="300" height="50" rx="4" fill="#0d1117" stroke="#6db33f" stroke-width="1.5"/>
  <text x="50" y="140" fill="#6db33f" font-size="9" font-family="monospace">// Constructor</text>
  <text x="50" y="154" fill="#e6edf3" font-size="9" font-family="monospace">public BankAccount(String owner, double init) {</text>
  <text x="50" y="166" fill="#8b949e" font-size="8" font-family="monospace">  this.owner = owner; this.balance = init;</text>

  <!-- Methods -->
  <rect x="348" y="125" width="312" height="50" rx="4" fill="#0d1117" stroke="#6db33f" stroke-width="1.5"/>
  <text x="363" y="140" fill="#6db33f" font-size="9" font-family="monospace">// Methods</text>
  <text x="363" y="154" fill="#e6edf3" font-size="9" font-family="monospace">public void deposit(double amount) { ... }</text>
  <text x="363" y="166" fill="#e6edf3" font-size="9" font-family="monospace">public double getBalance() { ... }</text>

  <!-- Closing brace -->
  <text x="40" y="222" fill="#6db33f" font-size="10" font-family="monospace">}   // end class BankAccount</text>

  <!-- Labels -->
  <text x="160" y="56"  fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">instance state</text>
  <text x="390" y="56"  fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">class-level init</text>
  <text x="578" y="56"  fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">nested types</text>
  <text x="185" y="123" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">initialises instances</text>
  <text x="504" y="123" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">behaviour</text>
</svg>

A Java class declaration wraps four regions: fields (state), constructors (initialisation), methods (behaviour), and nested types (supporting structures).

## 5. Runnable example

Scenario: a bank account system that starts with a simple balance holder, evolves to enforce business rules, and finally becomes a production-grade account with validation, audit, and thread safety.

### Level 1 — Basic

```java
// BankAccountBasic.java — minimal class anatomy
public class BankAccountBasic {

    // --- Fields ---
    private double balance;
    private final String owner;
    private int transactionCount;

    // --- Constructor ---
    public BankAccountBasic(String owner, double initialBalance) {
        if (initialBalance < 0) throw new IllegalArgumentException("Initial balance cannot be negative");
        this.owner   = owner;
        this.balance = initialBalance;
    }

    // --- Methods ---
    public void deposit(double amount) {
        if (amount <= 0) throw new IllegalArgumentException("Deposit must be positive");
        balance += amount;
        transactionCount++;
    }

    public void withdraw(double amount) {
        if (amount <= 0) throw new IllegalArgumentException("Withdrawal must be positive");
        if (amount > balance) throw new IllegalStateException("Insufficient funds");
        balance -= amount;
        transactionCount++;
    }

    public double getBalance()      { return balance; }
    public String getOwner()        { return owner; }
    public int getTransactionCount(){ return transactionCount; }

    @Override
    public String toString() {
        return String.format("BankAccount[owner=%s, balance=%.2f, txns=%d]",
            owner, balance, transactionCount);
    }

    // --- Entry point (in same class for demo) ---
    public static void main(String[] args) {
        BankAccountBasic account = new BankAccountBasic("Alice", 1000.00);
        System.out.println("Created: " + account);

        account.deposit(500.00);
        System.out.println("After deposit 500: " + account);

        account.withdraw(200.00);
        System.out.println("After withdraw 200: " + account);

        // Test guard
        try {
            account.withdraw(5000.00);
        } catch (IllegalStateException e) {
            System.out.println("Caught: " + e.getMessage());
        }

        System.out.println("Final: " + account);
    }
}
```

**How to run:** `java BankAccountBasic.java`

Expected output:
```
Created: BankAccount[owner=Alice, balance=1000.00, txns=0]
After deposit 500: BankAccount[owner=Alice, balance=1500.00, txns=1]
After withdraw 200: BankAccount[owner=Alice, balance=1300.00, txns=2]
Caught: Insufficient funds
Final: BankAccount[owner=Alice, balance=1300.00, txns=2]
```

Every element of a class is present: a `final` field (immutable owner), a mutable field (balance), a constructor, instance methods, argument validation, and `@Override` on `toString()`.

### Level 2 — Intermediate

Same bank account extended with a `static` counter for total accounts opened (class-level state), a static factory method, `equals`/`hashCode`, and a nested `Transaction` record.

```java
// BankAccountIntermediate.java — static members, nested type, equals/hashCode
import java.util.*;

public class BankAccountIntermediate {

    // --- Class-level state (static field) ---
    private static int totalAccountsOpened = 0;

    // --- Nested record type (part of the class) ---
    record Transaction(String type, double amount, double balanceAfter) {
        @Override public String toString() {
            return String.format("[%s] %.2f → balance=%.2f", type, amount, balanceAfter);
        }
    }

    // --- Instance fields ---
    private final String id;        // immutable
    private final String owner;     // immutable
    private double balance;
    private final List<Transaction> history = new ArrayList<>();

    // --- Static initialiser ---
    static {
        System.out.println("BankAccountIntermediate class loaded.");
    }

    // --- Private constructor (force use of factory) ---
    private BankAccountIntermediate(String owner, double initial) {
        this.id = "ACC-" + (++totalAccountsOpened);
        this.owner = owner;
        this.balance = initial;
        history.add(new Transaction("OPEN", initial, initial));
    }

    // --- Static factory method ---
    public static BankAccountIntermediate open(String owner, double initial) {
        if (initial < 0) throw new IllegalArgumentException("Initial balance cannot be negative");
        return new BankAccountIntermediate(owner, initial);
    }

    // --- Methods ---
    public void deposit(double amount) {
        if (amount <= 0) throw new IllegalArgumentException("Deposit must be positive");
        balance += amount;
        history.add(new Transaction("DEPOSIT", amount, balance));
    }

    public void withdraw(double amount) {
        if (amount <= 0) throw new IllegalArgumentException("Withdrawal must be positive");
        if (amount > balance) throw new IllegalStateException("Insufficient funds");
        balance -= amount;
        history.add(new Transaction("WITHDRAWAL", amount, balance));
    }

    public double   getBalance() { return balance; }
    public String   getId()      { return id; }
    public String   getOwner()   { return owner; }
    public List<Transaction> getHistory() { return Collections.unmodifiableList(history); }

    public static int getTotalAccountsOpened() { return totalAccountsOpened; }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (!(o instanceof BankAccountIntermediate that)) return false;
        return id.equals(that.id);
    }

    @Override public int hashCode() { return id.hashCode(); }

    @Override
    public String toString() {
        return String.format("BankAccount[id=%s, owner=%s, balance=%.2f]", id, owner, balance);
    }

    public static void main(String[] args) {
        System.out.println("Total accounts (before open): " + getTotalAccountsOpened());

        var alice = BankAccountIntermediate.open("Alice", 1000.00);
        var bob   = BankAccountIntermediate.open("Bob", 500.00);
        System.out.println("Total accounts: " + getTotalAccountsOpened());

        alice.deposit(300.00);
        alice.withdraw(150.00);
        bob.deposit(200.00);

        System.out.println("\n" + alice);
        System.out.println("Alice history:");
        alice.getHistory().forEach(t -> System.out.println("  " + t));

        System.out.println("\n" + bob);
        System.out.println("Bob history:");
        bob.getHistory().forEach(t -> System.out.println("  " + t));

        System.out.println("\nAlice equals Alice: " + alice.equals(alice));
        System.out.println("Alice equals Bob:   " + alice.equals(bob));
    }
}
```

**How to run:** `java BankAccountIntermediate.java`

`static` field `totalAccountsOpened` is shared across all instances — it counts how many accounts have ever been created. The `static {}` initialiser block runs once when the class is first loaded by the JVM (before any object is created). The nested `Transaction` record is a supporting type scoped to `BankAccountIntermediate`.

### Level 3 — Advanced

Same account grown to be thread-safe with `synchronized` methods, implements `Comparable` for sorting, uses `volatile` for the static counter, and demonstrates the full class feature set in one coherent banking example.

```java
// BankAccountAdvanced.java — thread-safe, Comparable, volatile, annotations
import java.util.*;
import java.util.concurrent.*;
import java.util.concurrent.atomic.*;

public class BankAccountAdvanced implements Comparable<BankAccountAdvanced> {

    // --- Class-level: atomic counter (thread-safe alternative to volatile++) ---
    private static final AtomicInteger totalOpened = new AtomicInteger(0);

    // --- Nested enum (part of the class namespace) ---
    public enum Status { ACTIVE, FROZEN, CLOSED }

    // --- Nested record ---
    public record Transaction(String type, double amount, double balanceAfter, long epochMs) {
        @Override public String toString() {
            return String.format("[%s] %.2f → %.2f @ %d", type, amount, balanceAfter, epochMs);
        }
    }

    // --- Immutable fields ---
    private final String id;
    private final String owner;
    private final long   openedAt;

    // --- Mutable fields ---
    private volatile Status status = Status.ACTIVE;     // volatile: visible across threads
    private double balance;                             // guarded by 'this' (synchronized)
    private final List<Transaction> history = new CopyOnWriteArrayList<>();

    // --- Private constructor + static factory ---
    private BankAccountAdvanced(String owner, double initial) {
        this.id       = String.format("ACC-%04d", totalOpened.incrementAndGet());
        this.owner    = owner;
        this.balance  = initial;
        this.openedAt = System.currentTimeMillis();
        history.add(new Transaction("OPEN", initial, initial, openedAt));
    }

    public static BankAccountAdvanced open(String owner, double initial) {
        if (owner == null || owner.isBlank()) throw new IllegalArgumentException("Owner required");
        if (initial < 0) throw new IllegalArgumentException("Initial balance cannot be negative");
        return new BankAccountAdvanced(owner, initial);
    }

    // --- Synchronized methods (thread-safe) ---
    public synchronized void deposit(double amount) {
        requireActive();
        if (amount <= 0) throw new IllegalArgumentException("Deposit must be positive");
        balance += amount;
        history.add(new Transaction("DEPOSIT", amount, balance, System.currentTimeMillis()));
    }

    public synchronized void withdraw(double amount) {
        requireActive();
        if (amount <= 0) throw new IllegalArgumentException("Withdrawal must be positive");
        if (amount > balance) throw new IllegalStateException("Insufficient funds: need " + amount + ", have " + balance);
        balance -= amount;
        history.add(new Transaction("WITHDRAWAL", amount, balance, System.currentTimeMillis()));
    }

    public synchronized void freeze() {
        status = Status.FROZEN;
        history.add(new Transaction("FREEZE", 0, balance, System.currentTimeMillis()));
    }

    public synchronized void close() {
        withdraw(balance); // zero the balance first
        status = Status.CLOSED;
        history.add(new Transaction("CLOSE", 0, 0, System.currentTimeMillis()));
    }

    private void requireActive() {
        if (status != Status.ACTIVE)
            throw new IllegalStateException("Account is " + status);
    }

    // --- Getters ---
    public synchronized double getBalance() { return balance; }
    public String getId()                    { return id; }
    public String getOwner()                 { return owner; }
    public Status getStatus()                { return status; }
    public List<Transaction> getHistory()    { return Collections.unmodifiableList(history); }
    public static int getTotalOpened()       { return totalOpened.get(); }

    // --- Comparable: sort by balance descending ---
    @Override public int compareTo(BankAccountAdvanced other) {
        return Double.compare(other.balance, this.balance); // descending
    }

    @Override public boolean equals(Object o) {
        if (this == o) return true;
        if (!(o instanceof BankAccountAdvanced a)) return false;
        return id.equals(a.id);
    }
    @Override public int hashCode() { return id.hashCode(); }

    @Override
    public String toString() {
        return String.format("Account[%s, owner=%s, balance=%.2f, status=%s]",
            id, owner, balance, status);
    }

    public static void main(String[] args) throws Exception {
        // Create two accounts
        var alice = BankAccountAdvanced.open("Alice", 2000.00);
        var bob   = BankAccountAdvanced.open("Bob", 500.00);
        System.out.printf("Opened %d accounts%n%n", getTotalOpened());

        // Concurrent deposits from multiple threads
        ExecutorService pool = Executors.newFixedThreadPool(4);
        for (int i = 0; i < 10; i++) {
            final int idx = i;
            pool.submit(() -> alice.deposit(100.0 * (idx + 1)));
        }
        pool.shutdown();
        pool.awaitTermination(5, TimeUnit.SECONDS);

        bob.deposit(1500.00);
        bob.withdraw(300.00);

        // Sort accounts by balance (uses Comparable)
        List<BankAccountAdvanced> accounts = new ArrayList<>(List.of(alice, bob));
        Collections.sort(accounts);
        System.out.println("Accounts sorted by balance (descending):");
        accounts.forEach(System.out::println);

        System.out.println("\nAlice history (last 3):");
        List<Transaction> hist = alice.getHistory();
        hist.subList(Math.max(0, hist.size() - 3), hist.size())
            .forEach(t -> System.out.println("  " + t));

        // Status transitions
        bob.freeze();
        System.out.println("\nBob status: " + bob.getStatus());
        try { bob.deposit(100); } catch (IllegalStateException e) {
            System.out.println("Blocked deposit: " + e.getMessage());
        }
    }
}
```

**How to run:** `java BankAccountAdvanced.java`

Ten concurrent threads deposit into Alice's account. `synchronized` on `deposit` ensures no two threads modify `balance` simultaneously — each invocation holds the intrinsic lock on `this`. `volatile Status status` ensures all threads see the latest freeze/close status without synchronization on reads. `Comparable` lets `Collections.sort` rank accounts by balance.

## 6. Walkthrough

Execution trace in `BankAccountAdvanced.main`:

**Class loading.** When `BankAccountAdvanced` is first referenced by the JVM, the class loader loads the bytecode. Static fields are initialised: `totalOpened = new AtomicInteger(0)`. No `static {}` block here — the `AtomicInteger` field initialiser handles it.

**`open("Alice", 2000.00)`.** The private constructor runs: `totalOpened.incrementAndGet()` → 1. `id = "ACC-0001"`. `balance = 2000.0`. `history` gets the first `OPEN` transaction. The JVM allocates a new `BankAccountAdvanced` object on the heap and returns its reference.

**Concurrent deposits.** Ten `Executors.newFixedThreadPool(4)` tasks each call `alice.deposit(amount)`. `synchronized` acquires the intrinsic monitor on `alice` (the object). If two threads call `deposit` simultaneously, the second blocks at the `synchronized` keyword until the first releases the monitor. Each `deposit` call: `balance += amount` (safe under lock), `history.add(...)` (CopyOnWriteArrayList is thread-safe by itself).

**State after concurrent deposits.** Total deposited = 100+200+...+1000 = 5500. Plus initial 2000 → Alice's balance = 7500. The exact order of history entries depends on thread scheduling, but the final balance is deterministic because each `+=` is atomic under the lock.

**`Collections.sort(accounts)`.** Calls `alice.compareTo(bob)` → `Double.compare(bob.balance, alice.balance)`. Since Alice > Bob, Bob comes after Alice in descending order. Result: `[Alice, Bob]`.

**Freeze and blocked deposit.** `bob.freeze()` sets `status = Status.FROZEN`. The next `bob.deposit(100)` call acquires the lock, then calls `requireActive()` which sees `status != ACTIVE` and throws `IllegalStateException("Account is FROZEN")`. The exception propagates out of the synchronized block (lock released automatically via `monitorexit` in bytecode).

## 7. Gotchas & takeaways

> **`final` on a field means the reference is immutable, not the object it points to.** `private final List<Transaction> history = new ArrayList<>()` — you cannot reassign `history` to a different list, but you can still call `history.add(...)`. For a truly immutable collection, use `List.of(...)` or `Collections.unmodifiableList(...)`.

> **`synchronized` on methods locks on `this`.** Two `synchronized` methods in the same class cannot run concurrently on the same instance — they share the same lock. But `synchronized` on a `static` method locks on the `Class` object, not an instance. These are different locks, so a static synchronized method and an instance synchronized method can run concurrently.

- Every Java statement lives inside a class member — no floating code at file scope.
- `static` = belongs to the class; accessible without an instance; shared across all instances.
- `final` field = must be assigned in the constructor (or field initialiser), never again.
- `private` constructor + `static` factory = factory method pattern; lets you name the construction action.
- `@Override` tells the compiler "I intend to override a parent method" — it will error if no matching parent method exists, catching typos like `tostring()` vs `toString()`.
- `implements Comparable<T>` enables natural ordering for `Collections.sort`, `TreeMap`, `PriorityQueue`.
