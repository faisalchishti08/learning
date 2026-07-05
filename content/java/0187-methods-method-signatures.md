---
card: java
gi: 187
slug: methods-method-signatures
title: Methods & method signatures
---

## 1. What it is

A **method** is a named block of code defined inside a class that performs some behaviour, optionally taking input (**parameters**) and optionally producing output (a **return value**). A method's **signature** is its name plus the number, order, and types of its parameters — `(String, int)` and `(int, String)` are different signatures, even with the same parameter types, because order matters. The signature is what the compiler uses to tell one method apart from another with the same name (a mechanism called overloading, covered in a later topic).

```java
class Calculator {
    int add(int a, int b) {   // signature: add(int, int)
        return a + b;
    }

    double add(double a, double b) { // signature: add(double, double) — a DIFFERENT method, same name
        return a + b;
    }
}
```

The **return type** (`int` vs `double` here) is *not* part of the signature by itself — two methods cannot differ *only* by return type with identical parameter lists; the signature specifically means the name plus the parameter types and order.

## 2. Why & when

Methods exist to organize behaviour into named, reusable, callable units — instead of writing the same logic repeatedly inline wherever it's needed:

- **Reusability** — write the logic once, call it from as many places as needed.
- **Naming intent** — `calculateTotalPrice(items)` communicates *what* the code does far better than the raw arithmetic it contains would on its own, reading naturally at the call site.
- **Encapsulating steps** — breaking a large, complex operation into smaller, named methods makes each piece independently understandable and testable.
- **The signature enables overloading** — because Java distinguishes methods by their full signature (name + parameter types/order), you can define several methods with the same name that behave appropriately for different kinds of input, and the compiler picks the right one automatically based on the arguments used at the call site.

You define a method whenever a piece of logic is used more than once, is complex enough to deserve its own name, or represents a distinct, nameable operation your class or object should support.

## 3. Core concept

```java
class Greeter {
    // signature: greet(String) — one parameter, a String, returns void
    void greet(String name) {
        System.out.println("Hello, " + name + "!");
    }

    // signature: greet(String, String) — two String parameters, returns void
    void greet(String name, String title) {
        System.out.println("Hello, " + title + " " + name + "!");
    }

    // signature: greet() — no parameters, returns a String instead of void
    String greet() {
        return "Hello, stranger!";
    }
}

public class MethodDemo {
    public static void main(String[] args) {
        Greeter g = new Greeter();
        g.greet("Ann");            // matches greet(String)
        g.greet("Bo", "Dr.");       // matches greet(String, String)
        System.out.println(g.greet()); // matches greet() — no arguments
    }
}
```

All three `greet` methods share the same *name* but have distinct *signatures* — the compiler determines which one to call at each call site purely by matching the number and types of the arguments actually supplied, a process called **overload resolution**.

## 4. Diagram

<svg viewBox="0 0 620 160" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Three methods named greet with different parameter lists shown as distinct boxes, with call sites shown routing to the matching signature based on the arguments supplied">
  <rect x="8" y="8" width="604" height="144" rx="8" fill="#0d1117"/>
  <text x="310" y="24" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Same method name, different signatures — matched by argument count/types</text>

  <rect x="30" y="40" width="170" height="40" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="115" y="65" fill="#6db33f" font-size="10" text-anchor="middle" font-family="monospace">greet(String)</text>

  <rect x="225" y="40" width="200" height="40" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="325" y="65" fill="#6db33f" font-size="10" text-anchor="middle" font-family="monospace">greet(String, String)</text>

  <rect x="450" y="40" width="140" height="40" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="520" y="65" fill="#6db33f" font-size="10" text-anchor="middle" font-family="monospace">greet()</text>

  <text x="115" y="105" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">g.greet("Ann")</text>
  <text x="325" y="105" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">g.greet("Bo", "Dr.")</text>
  <text x="520" y="105" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">g.greet()</text>

  <line x1="115" y1="90" x2="115" y2="98" stroke="#79c0ff"/>
  <line x1="325" y1="90" x2="325" y2="98" stroke="#79c0ff"/>
  <line x1="520" y1="90" x2="520" y2="98" stroke="#79c0ff"/>
</svg>

The compiler matches each call site to the one signature whose parameter list fits the arguments supplied.

## 5. Runnable example

Scenario: a simple shipping-cost calculator — starting with one basic method, then extending with an overloaded version that takes an additional parameter, then hardening into several coordinated methods with clear names and well-defined parameters/return types working together.

### Level 1 — Basic

```java
public class ShippingBasic {

    static double shippingCost(double weightKg) {
        return weightKg * 2.5; // $2.50 per kg
    }

    public static void main(String[] args) {
        System.out.println("Cost: $" + shippingCost(4.0));
    }
}
```

**How to run:** `java ShippingBasic.java`

`shippingCost(double)` has the signature `shippingCost(double)` — one parameter, returning a `double` — a single, simple named operation replacing an inline calculation.

### Level 2 — Intermediate

Same idea, now overloaded with a second `shippingCost` method that also factors in a destination-based surcharge, distinguished purely by its different parameter list.

```java
public class ShippingIntermediate {

    static double shippingCost(double weightKg) {
        return weightKg * 2.5;
    }

    static double shippingCost(double weightKg, double surcharge) { // different signature: extra parameter
        return (weightKg * 2.5) + surcharge;
    }

    public static void main(String[] args) {
        System.out.println("Domestic: $" + shippingCost(4.0));
        System.out.println("International: $" + shippingCost(4.0, 15.0));
    }
}
```

**How to run:** `java ShippingIntermediate.java`

`shippingCost(4.0)` matches the one-parameter signature; `shippingCost(4.0, 15.0)` matches the two-parameter signature — the compiler picks the correct overload automatically based purely on how many arguments are supplied at each call site.

### Level 3 — Advanced

Same shipping logic, now split into several small, well-named methods with validated parameters, composed together to build a complete quote — demonstrating how breaking logic into methods with clear signatures makes a larger operation easier to follow and to test independently.

```java
public class ShippingAdvanced {

    static double baseRate(double weightKg) {
        if (weightKg <= 0) {
            throw new IllegalArgumentException("Weight must be positive: " + weightKg);
        }
        return weightKg * 2.5;
    }

    static double internationalSurcharge(boolean isInternational) {
        return isInternational ? 15.0 : 0.0;
    }

    static double totalShippingCost(double weightKg, boolean isInternational) {
        double base = baseRate(weightKg);
        double surcharge = internationalSurcharge(isInternational);
        return base + surcharge;
    }

    public static void main(String[] args) {
        System.out.println("Domestic 4kg: $" + totalShippingCost(4.0, false));
        System.out.println("International 4kg: $" + totalShippingCost(4.0, true));

        try {
            totalShippingCost(-2.0, false);
        } catch (IllegalArgumentException e) {
            System.out.println("Rejected: " + e.getMessage());
        }
    }
}
```

**How to run:** `java ShippingAdvanced.java`

`totalShippingCost` composes two smaller, independently-named methods (`baseRate` and `internationalSurcharge`) rather than inlining all the logic itself — each method has a single clear responsibility and its own signature, making the overall calculation easy to read as a sequence of named steps and each piece easy to test or change independently.

## 6. Walkthrough

Trace `totalShippingCost(4.0, true)` from `ShippingAdvanced.main`:

**Entry.** `totalShippingCost` is called with `weightKg = 4.0`, `isInternational = true`.

**Step 1: `baseRate(4.0)`.** Inside, `weightKg <= 0` is `4.0 <= 0`, false — no exception. Returns `4.0 * 2.5 = 10.0`. Back in `totalShippingCost`, `base = 10.0`.

**Step 2: `internationalSurcharge(true)`.** The ternary `isInternational ? 15.0 : 0.0` evaluates `true`, so it returns `15.0`. Back in `totalShippingCost`, `surcharge = 15.0`.

**Step 3: combine.** `return base + surcharge` is `10.0 + 15.0 = 25.0`.

**Print.** `main` prints `"International 4kg: $25.0"`.

```
totalShippingCost(4.0, true)
  -> baseRate(4.0)                 = 10.0
  -> internationalSurcharge(true)  = 15.0
  -> 10.0 + 15.0 = 25.0
```

**Third call.** `totalShippingCost(-2.0, false)` calls `baseRate(-2.0)` first; inside, `weightKg <= 0` is `-2.0 <= 0`, true — throws `IllegalArgumentException("Weight must be positive: -2.0")` immediately. `internationalSurcharge` is never even called, since the exception propagates straight out of `totalShippingCost` back to `main`'s `try/catch`, which prints `"Rejected: Weight must be positive: -2.0"`.

## 7. Gotchas & takeaways

> **Two methods cannot differ *only* by return type — the signature is name plus parameter types and order, not the return type.** Attempting `int compute(int x) {...}` and `double compute(int x) {...}` in the same class is a compile error ("method already defined"), since both have the identical signature `compute(int)`.

> **Parameter *order* is part of the signature, not just the types present.** `void report(String name, int count)` and `void report(int count, String name)` are two genuinely distinct, valid overloads — but calling one when you meant the other (mixing up argument order) is a common and easy mistake, since both compile without error if the types happen to be assignment-compatible in either position.

- A method's signature is its name plus the number, order, and types of its parameters — not its return type.
- Overloading (multiple methods, same name, different signatures) lets the compiler choose the right method automatically based on the arguments at each call site.
- Breaking a large operation into several small, clearly-named methods (each with its own signature) makes the overall logic easier to read, test, and maintain.
- A method's return type must be consistent with what every `return` statement inside it actually returns, or `void` if it returns nothing.
