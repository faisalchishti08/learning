---
card: java
gi: 996
slug: law-of-demeter
title: Law of Demeter
---

## 1. What it is

The **Law of Demeter (LoD)**, also called the "principle of least knowledge," says a method should only talk to its **immediate friends**: its own fields, its parameters, objects it creates itself, and its direct component objects — not the internal objects *those* objects happen to hold. The informal version is "don't talk to strangers," or "only use one dot" — code like `customer.getWallet().getCash().subtract(amount)` chains through three levels of someone else's internals, and every one of those `.get...()` calls is a "stranger" the calling code shouldn't need to know exists.

## 2. Why & when

A long chain like `order.getCustomer().getAddress().getCity().toUpperCase()` couples the calling code to the *entire shape* of `Customer`, `Address`, and every step in between — if `Address` is ever refactored to store `city` differently, every caller with a chain like this breaks, even though logically they only cared about "the customer's city," not how it's nested. LoD exists to keep that shape private: each object exposes behavior ("tell the wallet to pay this amount") instead of exposing its internals for others to reach through ("give me the wallet so I can reach into its cash").

Apply LoD when you see a chain of two or more `.` method calls drilling into another object's internal structure. The fix is usually to add a method on the outer object that does the work itself, delegating internally — "tell, don't ask." It's not a hard rule against ever calling a method on a returned object (a fluent builder chain like `.append(...).append(...)` is fine, since each call returns the *same* kind of object, not a nested stranger) — it specifically targets reaching through one object to manipulate another one's internals.

## 3. Core concept

```
// Violates LoD: reaches through Customer -> Wallet -> Cash, three strangers deep
void chargeCustomer(Customer customer, double amount) {
    customer.getWallet().getCash().subtract(amount); // knows Wallet's and Cash's internals
}

// Follows LoD: "tell" the customer to pay -- it hides HOW that happens internally
class Customer {
    private Wallet wallet;
    void pay(double amount) { wallet.charge(amount); } // Customer's own business
}
class Wallet {
    private double cash;
    void charge(double amount) { cash -= amount; } // Wallet's own business
}
void chargeCustomer(Customer customer, double amount) {
    customer.pay(amount); // one dot: talking only to an immediate friend
}
```

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Calling code reaching through Customer into Wallet into Cash versus calling code telling Customer to pay while Customer delegates internally to Wallet">
  <text x="150" y="24" fill="#8b949e" font-size="12" text-anchor="middle" font-family="sans-serif">Before: reaching through</text>
  <rect x="20" y="40" width="110" height="40" rx="6" fill="#1c2430" stroke="#8b949e"/>
  <text x="75" y="65" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Caller</text>
  <rect x="150" y="40" width="110" height="40" rx="6" fill="#1c2430" stroke="#f0883e"/>
  <text x="205" y="65" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Customer</text>
  <rect x="280" y="40" width="110" height="40" rx="6" fill="#1c2430" stroke="#f0883e"/>
  <text x="335" y="65" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Wallet</text>
  <line x1="130" y1="60" x2="150" y2="60" stroke="#f0883e" marker-end="url(#a)"/>
  <line x1="260" y1="60" x2="280" y2="60" stroke="#f0883e" marker-end="url(#a)"/>
  <text x="205" y="30" fill="#f0883e" font-size="9" text-anchor="middle" font-family="sans-serif">.getWallet().getCash()...</text>

  <text x="490" y="24" fill="#8b949e" font-size="12" text-anchor="middle" font-family="sans-serif">After: tell, don't ask</text>
  <rect x="400" y="100" width="100" height="40" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="450" y="125" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Caller</text>
  <rect x="520" y="100" width="100" height="40" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="570" y="125" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Customer</text>
  <line x1="500" y1="120" x2="520" y2="120" stroke="#6db33f" marker-end="url(#a)"/>
  <text x="450" y="90" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">.pay(amount) -- one dot</text>
  <defs><marker id="a" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

The caller talks only to `Customer`; `Customer` handles reaching into its own `Wallet` internally.

## 5. Runnable example

Scenario: charging a customer's wallet for a purchase, evolving from a long chain that reaches through nested internals into "tell, don't ask" delegation that hides each object's internal shape from the outside.

### Level 1 — Basic

```java
// File: LodBasic.java
class Cash {
    private double amount;
    Cash(double amount) { this.amount = amount; }
    double getAmount() { return amount; }
    void setAmount(double amount) { this.amount = amount; }
}
class Wallet {
    private Cash cash;
    Wallet(Cash cash) { this.cash = cash; }
    Cash getCash() { return cash; }
}
class Customer {
    private Wallet wallet;
    Customer(Wallet wallet) { this.wallet = wallet; }
    Wallet getWallet() { return wallet; }
}

public class LodBasic {
    static void chargeCustomer(Customer customer, double amount) {
        // Reaches through Customer -> Wallet -> Cash: three strangers deep.
        Cash cash = customer.getWallet().getCash();
        cash.setAmount(cash.getAmount() - amount);
    }

    public static void main(String[] args) {
        Customer customer = new Customer(new Wallet(new Cash(100.0)));
        chargeCustomer(customer, 30.0);
        System.out.println("remaining: " + customer.getWallet().getCash().getAmount());
    }
}
```

**How to run:** save as `LodBasic.java`, then `javac LodBasic.java && java LodBasic` (JDK 17+).

Expected output:
```
remaining: 70.0
```

`chargeCustomer` knows that a `Customer` has a `Wallet`, that a `Wallet` has `Cash`, and that `Cash` exposes `getAmount`/`setAmount` — if `Wallet` ever switches to holding cash in cents as an `int`, this method (and every other caller doing the same chain) breaks.

### Level 2 — Intermediate

```java
// File: LodIntermediate.java
class Cash {
    private double amount;
    Cash(double amount) { this.amount = amount; }
    void subtract(double amount) { this.amount -= amount; }
    double getAmount() { return amount; }
}
class Wallet {
    private final Cash cash;
    Wallet(Cash cash) { this.cash = cash; }
    void charge(double amount) { cash.subtract(amount); } // Wallet handles its OWN cash
    double balance() { return cash.getAmount(); }
}
class Customer {
    private final Wallet wallet;
    Customer(Wallet wallet) { this.wallet = wallet; }
    void pay(double amount) { wallet.charge(amount); } // Customer handles its OWN wallet
    double walletBalance() { return wallet.balance(); }
}

public class LodIntermediate {
    static void chargeCustomer(Customer customer, double amount) {
        customer.pay(amount); // one dot -- talking only to an immediate friend
    }

    public static void main(String[] args) {
        Customer customer = new Customer(new Wallet(new Cash(100.0)));
        chargeCustomer(customer, 30.0);
        System.out.println("remaining: " + customer.walletBalance());
    }
}
```

**How to run:** save as `LodIntermediate.java`, then `javac LodIntermediate.java && java LodIntermediate` (JDK 17+).

Expected output:
```
remaining: 70.0
```

The real-world concern added: `chargeCustomer` no longer knows that `Wallet` or `Cash` even exist — it only calls `customer.pay(amount)`. Each object handles its own internals: `Customer` delegates to `Wallet`, `Wallet` delegates to `Cash`. A change to how `Cash` stores its amount never reaches `chargeCustomer`.

### Level 3 — Advanced

```java
// File: LodAdvanced.java
class InsufficientFundsException extends RuntimeException {
    InsufficientFundsException(String message) { super(message); }
}

class Cash {
    private double amount;
    Cash(double amount) { this.amount = amount; }
    void subtract(double amount) {
        if (amount > this.amount) {
            throw new InsufficientFundsException("cannot subtract " + amount + " from " + this.amount);
        }
        this.amount -= amount;
    }
    double getAmount() { return amount; }
}

class Wallet {
    private final Cash cash;
    Wallet(Cash cash) { this.cash = cash; }
    void charge(double amount) { cash.subtract(amount); }
    double balance() { return cash.getAmount(); }
}

class Customer {
    private final String name;
    private final Wallet wallet;
    Customer(String name, Wallet wallet) { this.name = name; this.wallet = wallet; }

    // Customer adds ITS OWN behavior on top (a friendly error message),
    // still never exposing wallet or cash to the outside.
    void pay(double amount) {
        try {
            wallet.charge(amount);
        } catch (InsufficientFundsException e) {
            throw new InsufficientFundsException(name + " has insufficient funds: " + e.getMessage());
        }
    }

    double walletBalance() { return wallet.balance(); }
}

public class LodAdvanced {
    static void chargeCustomer(Customer customer, double amount) {
        customer.pay(amount); // still just one dot, regardless of what's inside Customer
    }

    public static void main(String[] args) {
        Customer customer = new Customer("Ana", new Wallet(new Cash(100.0)));
        chargeCustomer(customer, 30.0);
        System.out.println("remaining: " + customer.walletBalance());

        try {
            chargeCustomer(customer, 1000.0);
        } catch (InsufficientFundsException e) {
            System.out.println("charge failed: " + e.getMessage());
        }
    }
}
```

**How to run:** save as `LodAdvanced.java`, then `javac LodAdvanced.java && java LodAdvanced` (JDK 17+).

Expected output:
```
remaining: 70.0
charge failed: Ana has insufficient funds: cannot subtract 1000.0 from 70.0
```

The production-flavored hard case: an error path (insufficient funds) now flows up through three layers (`Cash` throws, `Wallet` propagates, `Customer` catches and re-wraps with context), and `chargeCustomer` at the very top still only ever calls `customer.pay(amount)` — none of that added complexity leaked into the calling code's knowledge of the object graph.

## 6. Walkthrough

Tracing `chargeCustomer(customer, 1000.0)` in `LodAdvanced.main`:

1. `chargeCustomer` calls `customer.pay(1000.0)` — its only interaction with `customer` is this single, one-dot call.
2. Inside `Customer.pay`, a `try` block calls `wallet.charge(1000.0)` — `Customer` is the only class that knows it delegates to a `Wallet`.
3. Inside `Wallet.charge`, `cash.subtract(1000.0)` is called — `Wallet` is the only class that knows it delegates to `Cash`.
4. Inside `Cash.subtract`, the check `amount > this.amount` evaluates `1000.0 > 70.0` (the balance remaining after the first successful charge), which is `true`, so a new `InsufficientFundsException("cannot subtract 1000.0 from 70.0")` is thrown.
5. That exception propagates up out of `Wallet.charge` (no `catch` there) to `Customer.pay`'s `catch (InsufficientFundsException e)` block, which throws a *new* exception wrapping the original message with the customer's name: `"Ana has insufficient funds: cannot subtract 1000.0 from 70.0"`.
6. That new exception propagates out of `customer.pay(1000.0)`, out of `chargeCustomer`, and is caught by `main`'s own `try`/`catch`, which prints `"charge failed: Ana has insufficient funds: cannot subtract 1000.0 from 70.0"`. At no point did `chargeCustomer` or `main` need to know that a `Wallet` or `Cash` object was involved in producing that message.

## 7. Gotchas & takeaways

> **Gotcha:** the Law of Demeter is about **method chains that reach into another object's internal structure**, not about method chaining in general. A fluent builder like `new StringBuilder().append("a").append("b")` is fine — each `append` call returns the *same* `StringBuilder`, not a different, nested stranger object.

- LoD ("don't talk to strangers"): a method should only call methods on its own fields, its parameters, objects it creates, or its direct collaborators — not on objects those collaborators expose.
- The visible symptom is a chain like `a.getB().getC().doSomething()` — each `.get...()` after the first reaches one level deeper into a stranger's internals.
- The fix is usually "tell, don't ask": add a method to the outer object (`Customer.pay`) that does the work by delegating internally, instead of exposing internals for the caller to manipulate directly.
- Following LoD makes refactoring safer — changing how `Wallet` stores its `Cash` internally never has to ripple out to every caller of `Customer`.
- Don't confuse it with fluent method chaining on the same object/type — that's a different pattern and isn't what LoD restricts.
- LoD and [SOLID — Single Responsibility](0989-solid-single-responsibility.md) reinforce each other: an object that hides its internals and exposes behavior tends naturally to have one clear responsibility for that behavior.
