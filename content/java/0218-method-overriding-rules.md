---
card: java
gi: 218
slug: method-overriding-rules
title: Method overriding rules
---

## 1. What it is

**Method overriding** is when a subclass provides its own implementation of a method that's already defined in its superclass, with the exact same signature (name, parameter types, and order). Java enforces several strict rules for a valid override: the method name and parameter list must match exactly; the return type must be the same or a covariant (more specific) subtype (covered in a later topic); the overriding method cannot throw broader checked exceptions than the original; and the access level cannot be more restrictive than the overridden method's (though it can be *less* restrictive).

```java
class Animal {
    protected String makeSound() {
        return "...";
    }
}

class Dog extends Animal {
    @Override
    public String makeSound() { // valid: same signature, WIDER access (protected -> public) is allowed
        return "Woof";
    }
}
```

`Dog.makeSound()` widens access from `protected` to `public` — this is legal, since a subclass is allowed to make an inherited method *more* accessible, never *less*; the reverse (narrowing `public` down to `protected` in a subclass) would be a compile error, since it would break the guarantee that anything callable on the superclass reference is still callable the same way on a subclass reference.

## 2. Why & when

Overriding exists to let a subclass customize inherited behaviour while preserving the superclass's overall contract — the guarantee that any code using a superclass reference can rely on consistent behaviour, however it's actually implemented underneath:

- **Customizing behaviour per subclass** — different subclasses commonly need to do the "same conceptual thing" differently (every animal makes *a* sound, but the specific sound varies), and overriding is precisely the mechanism for this.
- **The signature-matching rule preserves substitutability** — if an override could have a completely different parameter list, it would actually be an unrelated overload (not an override at all), breaking the expectation that a subclass can always be used wherever its superclass is expected (a principle later topics on polymorphism build on directly).
- **The exception and access rules protect calling code** — a caller that only knows about the superclass's declared checked exceptions or access level must be able to trust that any subclass's override won't surprise it with a broader exception it didn't handle, or suddenly-restricted access it didn't expect.

You override a method whenever a subclass needs to provide behaviour genuinely different from (but conceptually consistent with) its superclass's version — as opposed to adding an entirely new method, which is appropriate when the subclass needs capability the superclass's contract never promised at all.

## 3. Core concept

```java
class Shape {
    double area() {
        return 0.0;
    }
}

class Circle extends Shape {
    double radius;
    Circle(double radius) { this.radius = radius; }

    @Override
    double area() { // same name, same (empty) parameter list, same return type — valid override
        return Math.PI * radius * radius;
    }
}

class Square extends Shape {
    double side;
    Square(double side) { this.side = side; }

    @Override
    double area() { // a DIFFERENT implementation, same signature
        return side * side;
    }
}
```

Both `Circle` and `Square` override `area()` with the exact same signature (`double area()`, no parameters) but genuinely different logic — each subclass's override replaces `Shape`'s generic `return 0.0;` with a calculation specific to that shape, while any code expecting a `Shape` can call `.area()` on either without knowing or caring which specific override actually runs.

## 4. Diagram

<svg viewBox="0 0 600 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A base area method in Shape overridden differently by Circle and Square, each keeping the exact same method signature while providing distinct implementations, illustrating the core overriding rule that the signature must match exactly">
  <rect x="8" y="8" width="584" height="154" rx="8" fill="#0d1117"/>

  <rect x="220" y="20" width="160" height="40" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="300" y="45" fill="#6db33f" font-size="10" text-anchor="middle" font-family="monospace">Shape.area() -&gt; 0.0</text>

  <line x1="260" y1="60" x2="150" y2="90" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#ov)"/>
  <line x1="340" y1="60" x2="450" y2="90" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#ov)"/>

  <rect x="60" y="95" width="180" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="150" y="120" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="monospace">Circle.area() -&gt; πr²</text>

  <rect x="360" y="95" width="180" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="450" y="120" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="monospace">Square.area() -&gt; side²</text>

  <text x="300" y="155" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Same signature (double area(), no parameters), different implementations.</text>

  <defs><marker id="ov" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker></defs>
</svg>

Overriding requires an identical signature; only the implementation body differs between superclass and subclass.

## 5. Runnable example

Scenario: a small payment processing system with different payment method types — starting with basic overriding of a shared method, then extending with multiple subclasses each overriding differently, then hardening into a case demonstrating the access-widening rule and the checked-exception restriction rule together.

### Level 1 — Basic

```java
public class OverrideBasic {
    static class Payment {
        double process(double amount) {
            System.out.println("Generic processing of $" + amount);
            return amount;
        }
    }

    static class CreditCardPayment extends Payment {
        @Override
        double process(double amount) { // same signature, customized behaviour
            double fee = amount * 0.03;
            System.out.println("Credit card processing of $" + amount + " (fee: $" + fee + ")");
            return amount + fee;
        }
    }

    public static void main(String[] args) {
        Payment p = new CreditCardPayment();
        double total = p.process(100.0);
        System.out.println("Total charged: $" + total);
    }
}
```

**How to run:** `java OverrideBasic.java`

`CreditCardPayment.process(double)` has the exact same signature as `Payment.process(double)`, but adds a fee calculation — calling `p.process(100.0)` (where `p` is declared as `Payment` but actually holds a `CreditCardPayment`) runs the overridden version, not the original.

### Level 2 — Intermediate

Same system, now with a second payment type overriding differently, demonstrating multiple distinct overrides of the same inherited method.

```java
public class OverrideIntermediate {
    static class Payment {
        double process(double amount) {
            return amount;
        }
    }

    static class CreditCardPayment extends Payment {
        @Override
        double process(double amount) {
            return amount * 1.03; // 3% fee
        }
    }

    static class BankTransferPayment extends Payment {
        @Override
        double process(double amount) {
            return amount + 0.50; // flat fee
        }
    }

    public static void main(String[] args) {
        Payment[] payments = { new CreditCardPayment(), new BankTransferPayment() };

        for (Payment p : payments) {
            System.out.println(p.getClass().getSimpleName() + ": $" + p.process(100.0));
        }
    }
}
```

**How to run:** `java OverrideIntermediate.java`

Both subclasses override `process(double)` with the identical signature but genuinely different fee logic — the loop calls `p.process(100.0)` uniformly, and each iteration correctly runs whichever specific override matches that object's actual type.

### Level 3 — Advanced

Same system, now demonstrating two of the stricter overriding rules directly: widening access from `protected` to `public`, and the restriction against throwing a broader checked exception than the original method declared.

```java
public class OverrideAdvanced {
    static class Payment {
        protected double process(double amount) throws IllegalStateException { // declares a specific unchecked exception type (for illustration)
            return amount;
        }
    }

    static class CreditCardPayment extends Payment {
        @Override
        public double process(double amount) { // WIDENING access: protected -> public is legal
            if (amount <= 0) {
                throw new IllegalStateException("Amount must be positive: " + amount);
            }
            return amount * 1.03;
        }
        // Note: overriding methods may NOT declare broader CHECKED exceptions than the original;
        // IllegalStateException here is unchecked, so this rule mainly matters for checked exceptions,
        // which this illustrative example keeps simple by not introducing any.
    }

    public static void main(String[] args) {
        Payment p = new CreditCardPayment();
        System.out.println("Charged: $" + p.process(100.0));

        try {
            p.process(-5.0);
        } catch (IllegalStateException e) {
            System.out.println("Rejected: " + e.getMessage());
        }
    }
}
```

**How to run:** `java OverrideAdvanced.java`

`CreditCardPayment.process` widens its access modifier from `protected` (in `Payment`) to `public` — entirely legal, since this only makes the method *more* accessible, never less; if the override had instead attempted to narrow access (say, down to package-private), the compiler would reject it immediately, since that would break the substitutability guarantee that a `Payment` reference's `process` method is always callable the way `Payment` declares it.

## 6. Walkthrough

Trace both calls in `OverrideAdvanced.main`:

**`p.process(100.0)`.** `p` is declared as `Payment` but actually references a `CreditCardPayment` object — the overridden version runs. `amount <= 0` is `100.0 <= 0`, false — no exception. Returns `100.0 * 1.03 = 103.0`. Prints `"Charged: $103.0"`.

**`p.process(-5.0)`.** Same overridden method runs. `amount <= 0` is `-5.0 <= 0`, true — the guard fires, throwing `IllegalStateException("Amount must be positive: -5.0")` before any fee calculation happens.

**Caught in `main`.** The `try/catch` catches this, printing `"Rejected: Amount must be positive: -5.0"`.

```
p.process(100.0): amount<=0? no  -> 100.0 * 1.03 = 103.0 -> "Charged: $103.0"
p.process(-5.0):  amount<=0? yes -> throw IllegalStateException -> caught, "Rejected: Amount must be positive: -5.0"
```

**Final output.** `"Charged: $103.0"` then `"Rejected: Amount must be positive: -5.0"` — both calls dispatch to the exact same overridden `process` implementation, since `p`'s actual runtime type is `CreditCardPayment` in both cases, regardless of `p`'s declared type being the more general `Payment`.

## 7. Gotchas & takeaways

> **An overriding method's parameter list must match the overridden method's exactly — even a small difference (a different parameter type, or an extra parameter) makes it a completely separate *overload* instead of an override**, silently failing to actually replace the inherited behaviour the author likely intended to customize. The `@Override` annotation (covered in the next topic) is specifically designed to catch this exact mistake at compile time.

> **A subclass override can only widen access, never narrow it** (`protected` to `public` is fine; `public` to `protected` is a compile error) — this asymmetry exists specifically to preserve the guarantee that any code holding a superclass-typed reference can always call that method exactly as the superclass declared it, no matter which actual subclass the reference points to.

- A valid override requires an exactly matching method signature: same name, same parameter types and order.
- The return type must match or be a covariant subtype; access can only widen, never narrow, compared to the overridden method.
- An overriding method cannot declare broader checked exceptions than the method it overrides.
- A signature mismatch silently creates an unrelated overload instead of an override — a common, easy-to-miss bug this topic's rules exist to prevent.
