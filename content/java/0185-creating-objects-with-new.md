---
card: java
gi: 185
slug: creating-objects-with-new
title: Creating objects with new
---

## 1. What it is

The `new` keyword is what actually **creates an object** in Java — it allocates memory for a new instance of a class, initializes its fields to their default values, runs the class's constructor, and returns a **reference** to that freshly-created object. Without `new` (or an equivalent factory mechanism), a class's fields have no storage anywhere; `new` is the step that turns a blueprint into a real, usable thing.

```java
class Dog {
    String name;
    int age;
}

Dog d = new Dog(); // allocates a new Dog object, returns a reference to it, stored in d
d.name = "Rex";
d.age = 3;
```

`new Dog()` does two distinct things at once: it allocates and initializes the object (fields default to `null`/`0`/`false` until assigned), and it calls `Dog`'s constructor (here, the implicit default no-argument constructor, covered in a later topic) — the result is a reference, stored in the variable `d`, pointing at that specific object.

## 2. Why & when

`new` is needed anywhere a program needs an actual, independent instance of a class to work with, as opposed to just the class's *description*:

- **Every object in a running Java program exists because of some `new` call**, somewhere — directly in your code, or indirectly inside a library method you called (like `Arrays.copyOf`, which calls `new` internally).
- **Independent state per instance** — calling `new Dog()` twice produces two completely separate objects, each with its own `name` and `age`, so changing one never affects the other.
- **Just-in-time creation** — objects are created exactly when and where they're needed, rather than existing for the entire lifetime of a program, letting memory be used efficiently as objects are created and later become eligible for garbage collection once unreferenced.

You use `new` any time your program needs a distinct instance of some class to hold and work with its own data — as opposed to calling a `static` method, which operates without needing any particular instance at all.

## 3. Core concept

```java
class Counter {
    int count;
}

public class NewDemo {
    public static void main(String[] args) {
        Counter a = new Counter();
        Counter b = new Counter();

        a.count = 5;
        b.count = 100;

        System.out.println(a.count); // 5 — a and b are completely separate objects
        System.out.println(b.count); // 100

        Counter c = a; // c now refers to the SAME object as a, not a new one
        c.count = 999;
        System.out.println(a.count); // 999 — changing through c also changed what a sees
    }
}
```

`a` and `b`, created by two separate `new` calls, are genuinely independent objects; but `c = a` (no `new` involved) simply copies the *reference* — `c` and `a` end up pointing at the exact same object, so a change made through either variable is visible through both.

## 4. Diagram

<svg viewBox="0 0 600 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Two separate new Counter calls creating two independent objects in memory referenced by variables a and b, and a third variable c assigned from a without new pointing at the same object as a">
  <rect x="8" y="8" width="584" height="154" rx="8" fill="#0d1117"/>

  <text x="70" y="30" fill="#79c0ff" font-size="11" font-family="monospace">a</text>
  <line x1="80" y1="28" x2="140" y2="55" stroke="#79c0ff" stroke-width="1.5"/>
  <rect x="140" y="45" width="90" height="45" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="185" y="72" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="monospace">count: 999</text>

  <text x="70" y="120" fill="#79c0ff" font-size="11" font-family="monospace">c</text>
  <line x1="80" y1="118" x2="140" y2="80" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="100" y="140" fill="#8b949e" font-size="9" font-family="sans-serif">c = a; (no "new" — same object)</text>

  <text x="380" y="30" fill="#79c0ff" font-size="11" font-family="monospace">b</text>
  <line x1="390" y1="28" x2="430" y2="55" stroke="#79c0ff" stroke-width="1.5"/>
  <rect x="430" y="45" width="90" height="45" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="475" y="72" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="monospace">count: 100</text>
  <text x="475" y="115" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">separate object entirely</text>
</svg>

`a` and `c` both point at the same object created by one `new`; `b` is a genuinely separate object from a second `new` call.

## 5. Runnable example

Scenario: managing independent bank account balances — starting with basic object creation and independent state, then extending to create several accounts in a loop, then hardening into a transfer operation that correctly operates on two distinct account objects without ever confusing them.

### Level 1 — Basic

```java
public class AccountBasic {
    static class Account {
        double balance;
    }

    public static void main(String[] args) {
        Account acc1 = new Account();
        Account acc2 = new Account();

        acc1.balance = 100.0;
        acc2.balance = 250.0;

        System.out.println("Account 1: $" + acc1.balance);
        System.out.println("Account 2: $" + acc2.balance);
    }
}
```

**How to run:** `java AccountBasic.java`

Two separate `new Account()` calls create two entirely independent objects — setting `acc1.balance` has no effect whatsoever on `acc2.balance`, since they are different objects in memory.

### Level 2 — Intermediate

Same idea, now creating several accounts programmatically in a loop, demonstrating that each iteration's `new Account()` produces a genuinely distinct object.

```java
public class AccountIntermediate {
    static class Account {
        double balance;
    }

    public static void main(String[] args) {
        Account[] accounts = new Account[3];

        for (int i = 0; i < accounts.length; i++) {
            accounts[i] = new Account(); // a fresh, independent object each time through the loop
            accounts[i].balance = (i + 1) * 100.0;
        }

        for (int i = 0; i < accounts.length; i++) {
            System.out.println("Account " + i + ": $" + accounts[i].balance);
        }
    }
}
```

**How to run:** `java AccountIntermediate.java`

Each loop iteration calls `new Account()` again, producing a brand-new object each time — even though the same line of code runs three times, it creates three genuinely separate `Account` instances, each independently holding its own `balance`.

### Level 3 — Advanced

Same accounts, now with a transfer method that correctly modifies two distinct existing objects (never accidentally creating or confusing them), including a guard against transferring more than the available balance.

```java
public class AccountAdvanced {
    static class Account {
        String owner;
        double balance;
        Account(String owner, double balance) { this.owner = owner; this.balance = balance; }
    }

    static void transfer(Account from, Account to, double amount) {
        if (amount > from.balance) {
            throw new IllegalStateException(
                from.owner + " has insufficient funds: balance " + from.balance + ", requested " + amount);
        }
        from.balance -= amount; // modifies the FROM object
        to.balance += amount;   // modifies the (different) TO object
    }

    public static void main(String[] args) {
        Account alice = new Account("Alice", 500.0);
        Account bob = new Account("Bob", 100.0);

        transfer(alice, bob, 200.0);
        System.out.println("Alice: $" + alice.balance + ", Bob: $" + bob.balance);

        try {
            transfer(alice, bob, 10000.0);
        } catch (IllegalStateException e) {
            System.out.println("Rejected: " + e.getMessage());
        }
    }
}
```

**How to run:** `java AccountAdvanced.java`

`transfer(alice, bob, 200.0)` receives references to two genuinely separate objects and correctly modifies each one's own `balance` field independently (`from.balance -=` and `to.balance +=`) — no `new` happens inside `transfer` at all; it operates purely on the two already-existing objects it was given references to.

## 6. Walkthrough

Trace `AccountAdvanced.main`:

**Construction.** `new Account("Alice", 500.0)` creates one object with `owner = "Alice"`, `balance = 500.0`, referenced by `alice`. `new Account("Bob", 100.0)` creates a second, entirely separate object, referenced by `bob`.

**First transfer.** `transfer(alice, bob, 200.0)`: inside the method, `from` refers to the same object as `alice`, and `to` refers to the same object as `bob` (parameters copy the *reference*, not the object). `amount (200.0) > from.balance (500.0)`? No. So `from.balance -= 200.0` makes `alice`'s balance `300.0`, and `to.balance += 200.0` makes `bob`'s balance `300.0`. Since `from`/`to` are the same objects as `alice`/`bob`, these changes are visible immediately through `alice.balance` and `bob.balance` back in `main`.

**Print.** `"Alice: $300.0, Bob: $300.0"`.

**Second transfer.** `transfer(alice, bob, 10000.0)`: `amount (10000.0) > from.balance (300.0, Alice's current balance)` is `true`, so the guard throws `IllegalStateException("Alice has insufficient funds: balance 300.0, requested 10000.0")` before either balance is touched.

```
Initial: alice.balance=500.0  bob.balance=100.0
transfer(alice, bob, 200.0):
  200.0 > 500.0? no -> alice.balance -= 200.0 -> 300.0
                        bob.balance   += 200.0 -> 300.0
transfer(alice, bob, 10000.0):
  10000.0 > 300.0? yes -> throw, no balances changed
```

**Caught in `main`.** Prints `"Rejected: Alice has insufficient funds: balance 300.0, requested 10000.0"`.

## 7. Gotchas & takeaways

> **Assigning one variable to another (`Account c = a;`) never calls `new` and never copies the object — it only copies the reference.** Both variables end up pointing at the exact same object, so a change made through one is visible through the other. To get a genuinely independent second object, `new` must be called again.

> **Every distinct object needs its own `new` call.** A common beginner mistake is expecting a loop-declared variable to somehow persist a "fresh" object across iterations without calling `new` inside the loop each time — without a `new` per iteration, you'd just keep reassigning the same reference (or reusing whatever the variable pointed at before).

- `new ClassName(...)` allocates a genuinely new object, runs its constructor, and returns a reference to it.
- Each `new` call produces an independent object with its own field values, separate from any other instance of the same class.
- Assigning one object reference to another variable copies only the reference, not the object — both variables then refer to the same object.
- Objects created inside a loop with `new` inside the loop body are each independent; forgetting the `new` per iteration means no new object is actually created.
