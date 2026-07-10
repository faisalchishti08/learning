---
card: java
gi: 1020
slug: minimize-mutability-accessibility
title: Minimize mutability & accessibility
---

## 1. What it is

Two closely related defensive design habits: **minimize mutability** (make fields `final` and provide no setters unless a field genuinely needs to change after construction) and **minimize accessibility** (make every field, method, and class as `private` as it can possibly be, widening access only when there's a real reason). Both rules point the same direction — expose the smallest possible surface, by default, and only widen it (to mutable, or to more visible) when a concrete requirement demands it.

## 2. Why & when

Every mutable field is a place state can unexpectedly change out from under code that assumed it wouldn't — a public, non-final field can be reassigned from literally anywhere, breaking any invariant the class was trying to maintain, and making the class unsafe to share across threads without external synchronization. Every accessible member (a `public` field, a package-private class exposed unnecessarily) is a promise: other code is now free to depend on it, and that dependency can never be safely removed or changed later without breaking that other code. Minimizing both isn't about being overly cautious for its own sake — it's about keeping every future change local and safe, because nothing outside the class ever had access to break.

Apply "minimize mutability" by default to every field: make it `final` unless you have a specific, identified reason it needs to be reassigned after construction. Apply "minimize accessibility" by default to every member: start `private`, and only widen to package-private, `protected`, or `public` when something outside the class genuinely needs that access — and even then, prefer the narrowest level that still works.

## 3. Core concept

```
// Violates both rules: everything public and mutable by default
public class BankAccount {
    public double balance;       // mutable AND public -- anyone can set it to anything
    public String accountNumber; // no reason for this to ever change after creation
}

// Follows both rules: private by default, mutable only where genuinely necessary
public class BankAccount {
    private final String accountNumber; // never changes after construction -- final
    private double balance;             // DOES need to change (deposits/withdrawals) -- but private

    public BankAccount(String accountNumber, double initialBalance) {
        this.accountNumber = accountNumber;
        this.balance = initialBalance;
    }

    public double getBalance() { return balance; } // read access exposed deliberately
    public void deposit(double amount) {            // the ONLY way balance can change
        if (amount <= 0) throw new IllegalArgumentException("deposit must be positive");
        balance += amount;
    }
}
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A fully public, mutable BankAccount reachable and modifiable from anywhere versus a mostly private BankAccount exposing only a controlled deposit method and a read-only balance getter">
  <text x="150" y="24" fill="#8b949e" font-size="12" text-anchor="middle" font-family="sans-serif">Wide open</text>
  <rect x="30" y="40" width="230" height="70" rx="8" fill="#1c2430" stroke="#f0883e"/>
  <text x="145" y="65" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">public double balance;</text>
  <text x="145" y="85" fill="#f0883e" font-size="9" text-anchor="middle" font-family="sans-serif">anyone, anywhere, can set it</text>

  <text x="480" y="24" fill="#8b949e" font-size="12" text-anchor="middle" font-family="sans-serif">Minimal surface</text>
  <rect x="360" y="30" width="240" height="30" rx="6" fill="#1c2430" stroke="#8b949e"/>
  <text x="480" y="50" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">private double balance;</text>
  <rect x="360" y="70" width="240" height="30" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="480" y="90" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">public void deposit(amount)</text>
  <rect x="360" y="110" width="240" height="30" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="480" y="130" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">public double getBalance()</text>
</svg>

The field itself stays private; every change is routed through one controlled, validating method.

## 5. Runnable example

Scenario: a bank account balance, evolving from wide-open public mutable state into a properly encapsulated design where change only happens through validated, controlled entry points.

### Level 1 — Basic

```java
// File: MinimizeBasic.java
class BankAccount {
    public double balance; // fully public and mutable -- no protection at all
}

public class MinimizeBasic {
    public static void main(String[] args) {
        BankAccount account = new BankAccount();
        account.balance = 100.0;

        account.balance = -500.0; // nothing stops this -- an invalid, nonsensical balance
        System.out.println("balance: " + account.balance);
    }
}
```

**How to run:** save as `MinimizeBasic.java`, then `javac MinimizeBasic.java && java MinimizeBasic` (JDK 17+).

Expected output:
```
balance: -500.0
```

Any code anywhere in the program can set `balance` to any value, including nonsensical ones — there's no way to enforce that a balance is never set directly to something invalid, since the field itself is the only interface.

### Level 2 — Intermediate

```java
// File: MinimizeIntermediate.java
class BankAccount {
    private double balance; // private -- only this class can touch it directly

    BankAccount(double initialBalance) {
        this.balance = initialBalance;
    }

    double getBalance() { return balance; }

    void deposit(double amount) {
        if (amount <= 0) throw new IllegalArgumentException("deposit must be positive");
        balance += amount;
    }
}

public class MinimizeIntermediate {
    public static void main(String[] args) {
        BankAccount account = new BankAccount(100.0);
        account.deposit(50.0);
        System.out.println("balance: " + account.getBalance());

        try {
            account.deposit(-500.0); // now rejected, instead of silently corrupting state
        } catch (IllegalArgumentException e) {
            System.out.println("deposit rejected: " + e.getMessage());
        }
    }
}
```

**How to run:** save as `MinimizeIntermediate.java`, then `javac MinimizeIntermediate.java && java MinimizeIntermediate` (JDK 17+).

Expected output:
```
balance: 150.0
deposit: 150.0
deposit rejected: deposit must be positive
```

The real-world concern added: `balance` is `private`, reachable only through `deposit`, which validates the amount before applying it. There's no longer any way to directly assign an invalid balance from outside the class.

### Level 3 — Advanced

```java
// File: MinimizeAdvanced.java
class InsufficientFundsException extends RuntimeException {
    InsufficientFundsException(String message) { super(message); }
}

class BankAccount {
    private final String accountNumber; // never changes after construction -- final
    private double balance;             // the ONE field that legitimately needs to mutate

    BankAccount(String accountNumber, double initialBalance) {
        if (initialBalance < 0) throw new IllegalArgumentException("initial balance cannot be negative");
        this.accountNumber = accountNumber;
        this.balance = initialBalance;
    }

    String getAccountNumber() { return accountNumber; } // read-only -- no setter exists at all
    double getBalance() { return balance; }

    void deposit(double amount) {
        if (amount <= 0) throw new IllegalArgumentException("deposit must be positive");
        balance += amount;
    }

    // withdraw is package-private on purpose: only trusted code in this package
    // (e.g. a transaction coordinator) should be able to call it directly;
    // external callers go through transferTo, which enforces additional rules.
    void withdraw(double amount) {
        if (amount <= 0) throw new IllegalArgumentException("withdrawal must be positive");
        if (amount > balance) throw new InsufficientFundsException("insufficient funds");
        balance -= amount;
    }

    public void transferTo(BankAccount other, double amount) {
        this.withdraw(amount);
        other.deposit(amount);
    }
}

public class MinimizeAdvanced {
    public static void main(String[] args) {
        BankAccount alice = new BankAccount("ACC-001", 200.0);
        BankAccount bob = new BankAccount("ACC-002", 50.0);

        alice.transferTo(bob, 75.0);
        System.out.println("alice: " + alice.getBalance());
        System.out.println("bob: " + bob.getBalance());

        try {
            alice.transferTo(bob, 1000.0);
        } catch (InsufficientFundsException e) {
            System.out.println("transfer failed: " + e.getMessage());
        }
    }
}
```

**How to run:** save as `MinimizeAdvanced.java`, then `javac MinimizeAdvanced.java && java MinimizeAdvanced` (JDK 17+).

Expected output:
```
alice: 125.0
bob: 125.0
transfer failed: insufficient funds
```

The production-flavored hard case: `accountNumber` is `final` (genuinely immutable — it should never change), `balance` is the one field that legitimately mutates, `withdraw` is deliberately package-private rather than `public` (limiting direct access to trusted code within the same package), and `transferTo` is the sole `public` entry point that coordinates a withdrawal and a deposit as one operation, enforcing the insufficient-funds rule along the way.

## 6. Walkthrough

Tracing `alice.transferTo(bob, 1000.0)` in `MinimizeAdvanced.main`:

1. `transferTo` is called on `alice` with `other = bob` and `amount = 1000.0`.
2. Inside, `this.withdraw(1000.0)` runs — `this` refers to `alice`. Since `withdraw` is package-private (not `public`), it's only reachable from code inside the same package, but `transferTo` (which *is* `public`) is calling it internally, which is allowed since `transferTo` is a method of the same class.
3. Inside `withdraw`, `amount > balance` evaluates `1000.0 > 125.0` (alice's balance after the earlier successful `75.0` transfer) — `true` — so `throw new InsufficientFundsException("insufficient funds")` executes immediately.
4. That exception propagates up out of `withdraw`, out of `transferTo` (neither method catches it), and out to `main`'s `try` block, where `catch (InsufficientFundsException e)` catches it and prints `"transfer failed: insufficient funds"`.
5. Critically, because the exception was thrown *before* `other.deposit(amount)` was ever reached inside `transferTo`, `bob`'s balance is completely untouched by this failed transfer attempt — the operation failed atomically, without partially applying.
6. Note that no code outside `BankAccount` could have called `alice.withdraw(1000.0)` directly even if it wanted to bypass `transferTo`'s coordination — `withdraw`'s package-private accessibility is exactly what keeps that path unavailable to arbitrary external callers, forcing everyone through the validated `transferTo` entry point instead.

## 7. Gotchas & takeaways

> **Gotcha:** a `private` field with a `public` getter that returns a mutable object (a `List`, a `Date`, an array) hasn't actually minimized accessibility at all — the field's *reference* is protected, but the mutable object it points to is fully exposed to whoever calls the getter. See [immutability & defensive copies](1016-immutability-defensive-copies.md) for how to close that specific gap.

- Minimize mutability: make fields `final` by default; only allow reassignment after construction for fields with an identified, ongoing need to change.
- Minimize accessibility: start every field, method, and class as `private`; widen only when something outside genuinely needs that access, and prefer the narrowest level (package-private, then `protected`, then `public`) that satisfies the real requirement.
- Every widened access point is a permanent commitment — once external code depends on a `public` member, removing or changing it becomes a breaking change; a `private` member can be freely changed at any time since nothing outside could have depended on it.
- Package-private methods (like `withdraw` here) are a useful middle ground: accessible to trusted code within the same package (like a transaction coordinator), but not exposed to arbitrary external callers.
- These two habits reinforce [SOLID — Single Responsibility](0989-solid-single-responsibility.md) and [Law of Demeter](0996-law-of-demeter.md): a class with a small, controlled, mostly-immutable surface is naturally easier to reason about and harder to misuse from outside.
- Don't make everything `private` reflexively when a class's entire purpose is to expose data (a simple data-transfer record, for instance) — the goal is the narrowest access that still serves the class's genuine purpose, not accessibility restriction as an end in itself.
