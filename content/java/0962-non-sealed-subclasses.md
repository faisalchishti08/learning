---
card: java
gi: 962
slug: non-sealed-subclasses
title: non-sealed subclasses
---

## 1. What it is

`non-sealed` is a modifier applied to a class or interface that is itself a permitted subtype of some sealed type, explicitly declaring "the closure stops here — from this point in the hierarchy downward, ordinary, unrestricted subclassing is allowed again." It's one of exactly three required choices (alongside `final` and `sealed`) that every class named in a sealed type's `permits` clause must make, and it's the one that deliberately reintroduces openness into an otherwise-closed hierarchy at a specific, chosen point — rather than the whole hierarchy being either "fully closed everywhere" or "not sealed at all," `non-sealed` lets you seal only the *part* of the hierarchy you actually want fixed, while leaving one particular branch open to arbitrary future extension.

## 2. Why & when

`non-sealed` matters for hierarchies that are genuinely a mix of "these specific cases are fixed and complete" and "but this one category is meant to be extensible by design" — for instance, a sealed `PaymentMethod` hierarchy with fixed `CreditCard` and `BankTransfer` variants, but a `non-sealed CustomPaymentMethod` branch specifically intended for third-party plugins or future, not-yet-designed payment integrations to extend freely. It's also the necessary escape hatch for gradually migrating an existing, already-widely-subclassed type into a partially-sealed design: if some existing subclass is used and extended by external code you don't control (or don't want to break), marking that one branch `non-sealed` preserves its existing extensibility while still letting you seal the rest of the hierarchy around it. The tradeoff to understand clearly: any branch marked `non-sealed` gives up the exhaustiveness-checking benefit sealing otherwise provides — a `switch` handling a sealed type whose hierarchy includes a `non-sealed` branch cannot know all the branch's possible concrete subtypes, so it must still include a `default` (or an unconditional final case) to handle whatever unknown subtype of that branch might appear.

## 3. Core concept

```
sealed interface PaymentMethod permits CreditCard, BankTransfer, CustomPaymentMethod {}

record CreditCard(String number) implements PaymentMethod {}      // final (implicitly, as a record)
record BankTransfer(String iban) implements PaymentMethod {}       // final (implicitly, as a record)

non-sealed interface CustomPaymentMethod extends PaymentMethod {}  // REOPENED -- anyone can implement this

// Anywhere else, even in a completely different module:
class CryptoPayment implements CustomPaymentMethod { ... }  // perfectly legal -- CustomPaymentMethod is open

switch (paymentMethod) {
    case CreditCard cc -> ...;
    case BankTransfer bt -> ...;
    case CustomPaymentMethod cpm -> ...;   // must handle the WHOLE open-ended branch generically --
                                            // cannot enumerate its possible concrete subtypes
    // no exhaustiveness benefit for the CustomPaymentMethod branch specifically
}
```

The `non-sealed` branch trades away compiler-verified exhaustiveness for exactly the flexibility unsealed types always had — the rest of the hierarchy retains full sealing benefits, since the openness is deliberately scoped to just that one branch.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A sealed PaymentMethod hierarchy with CreditCard and BankTransfer closed as final records, and CustomPaymentMethod marked non-sealed and open to unlimited external extension" >
  <rect x="220" y="10" width="200" height="30" fill="#1c2430" stroke="#6db33f"/>
  <text x="320" y="29" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">sealed interface PaymentMethod</text>

  <rect x="40" y="70" width="140" height="30" fill="#1c2430" stroke="#79c0ff"/>
  <text x="110" y="89" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">record CreditCard (final)</text>

  <rect x="200" y="70" width="150" height="30" fill="#1c2430" stroke="#79c0ff"/>
  <text x="275" y="89" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">record BankTransfer (final)</text>

  <rect x="400" y="70" width="220" height="30" fill="#1c2430" stroke="#f0883e"/>
  <text x="510" y="89" fill="#f0883e" font-size="9" text-anchor="middle" font-family="sans-serif">non-sealed CustomPaymentMethod</text>

  <rect x="440" y="120" width="80" height="30" fill="none" stroke="#8b949e" stroke-dasharray="3"/>
  <text x="480" y="139" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">CryptoPayment</text>
  <rect x="530" y="120" width="80" height="30" fill="none" stroke="#8b949e" stroke-dasharray="3"/>
  <text x="570" y="139" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">...anything else...</text>

  <line x1="320" y1="40" x2="110" y2="70" stroke="#8b949e"/>
  <line x1="320" y1="40" x2="275" y2="70" stroke="#8b949e"/>
  <line x1="320" y1="40" x2="510" y2="70" stroke="#8b949e"/>
  <line x1="480" y1="100" x2="480" y2="120" stroke="#8b949e" stroke-dasharray="3"/>
  <line x1="570" y1="100" x2="570" y2="120" stroke="#8b949e" stroke-dasharray="3"/>
</svg>

*Two branches remain fully closed and exhaustively checkable; the non-sealed branch is deliberately open to unlimited, unenumerable future extension.*

## 5. Runnable example

Scenario: model a payment-method hierarchy that's mostly fixed but intentionally extensible for custom integrations, evolving from a basic sealed-plus-non-sealed setup, to a realistic case where an external, separately-compiled class extends the open branch, to a more advanced case demonstrating exactly how `switch` handling must change to accommodate the non-sealed branch's inherent unpredictability.

### Level 1 — Basic

```java
public class NonSealedBasic {
    sealed interface PaymentMethod permits CreditCard, CustomPaymentMethod {}
    record CreditCard(String last4) implements PaymentMethod {}
    non-sealed interface CustomPaymentMethod extends PaymentMethod {}

    static class GiftCard implements CustomPaymentMethod {
        String code;
        GiftCard(String code) { this.code = code; }
    }

    public static void main(String[] args) {
        PaymentMethod pm1 = new CreditCard("1234");
        PaymentMethod pm2 = new GiftCard("GC-9999"); // freely extends the OPEN branch

        System.out.println(pm1 instanceof CreditCard);
        System.out.println(pm2 instanceof CustomPaymentMethod);
    }
}
```

**How to run:** `java NonSealedBasic.java` (JDK 17+).

Expected output:
```
true
true
```

`CreditCard` remains fully closed (implicitly `final`, as a record), while `CustomPaymentMethod` is explicitly marked `non-sealed`, letting `GiftCard` — an entirely ordinary class, not named anywhere in `PaymentMethod`'s `permits` clause — freely implement it, exactly because that specific branch was deliberately reopened.

### Level 2 — Intermediate

```java
public class NonSealedExternalExtension {
    sealed interface Notification permits EmailNotification, CustomNotification {}
    record EmailNotification(String address, String subject) implements Notification {}
    non-sealed interface CustomNotification extends Notification {
        String describe();
    }

    // Simulates a THIRD-PARTY class, defined entirely independently, in a
    // different conceptual module, with no knowledge of Notification's internals
    // beyond the CustomNotification interface contract it chooses to implement.
    static class SlackNotification implements CustomNotification {
        String channel;
        SlackNotification(String channel) { this.channel = channel; }
        public String describe() { return "Slack message to #" + channel; }
    }

    static void send(Notification notification) {
        if (notification instanceof EmailNotification(String addr, String subj)) {
            System.out.println("Sending email to " + addr + ": " + subj);
        } else if (notification instanceof CustomNotification custom) {
            System.out.println("Sending custom notification: " + custom.describe());
        }
    }

    public static void main(String[] args) {
        send(new EmailNotification("team@example.com", "Deploy complete"));
        send(new SlackNotification("deploys"));
    }
}
```

**How to run:** `java NonSealedExternalExtension.java` (JDK 17+).

Expected output:
```
Sending email to team@example.com: Deploy complete
Sending custom notification: Slack message to #deploys
```

The real-world concern added: `SlackNotification` represents exactly the scenario `non-sealed` is designed for — code that could plausibly live in a completely separate module or be contributed by an entirely different team, extending the deliberately-open `CustomNotification` branch without needing to touch, or even know the internal design of, the sealed `Notification` hierarchy's fixed branches; `send`'s handling of `CustomNotification` must stay generic (calling only the interface's own `describe()` contract), since it cannot possibly know every concrete implementer in advance.

### Level 3 — Advanced

```java
public class NonSealedSwitchHandling {
    sealed interface Shape permits Circle, Square, CustomShape {}
    record Circle(double radius) implements Shape {}
    record Square(double side) implements Shape {}
    non-sealed interface CustomShape extends Shape {
        double area();
    }

    record Hexagon(double side) implements CustomShape {
        public double area() { return (3 * Math.sqrt(3) / 2) * side * side; }
    }

    static double area(Shape shape) {
        return switch (shape) {
            case Circle c -> Math.PI * c.radius() * c.radius();
            case Square s -> s.side() * s.side();
            case CustomShape cs -> cs.area(); // MUST be handled generically -- no exhaustiveness
                                               // possible for this branch's concrete subtypes
            // no default needed: Circle + Square + CustomShape together DO exhaust Shape,
            // even though CustomShape itself has unenumerable concrete implementers
        };
    }

    public static void main(String[] args) {
        System.out.printf("circle: %.2f%n", area(new Circle(2.0)));
        System.out.printf("square: %.2f%n", area(new Square(3.0)));
        System.out.printf("hexagon: %.2f%n", area(new Hexagon(4.0)));
    }
}
```

**How to run:** `java NonSealedSwitchHandling.java` (JDK 17+).

Expected output:
```
circle: 12.57
square: 9.00
hexagon: 41.57
```

The production-flavored hard case: the `switch` remains exhaustive over `Shape` itself — every direct permitted subtype (`Circle`, `Square`, `CustomShape`) is covered, so no `default` is needed at that level — but the `CustomShape` case must be written generically, dispatching to the interface's own `area()` method, precisely because the compiler cannot enumerate `CustomShape`'s own possible concrete implementers (like the later-added `Hexagon`); this demonstrates the precise, subtle boundary of exhaustiveness with a `non-sealed` branch present: exhaustive at the sealed type's own direct-subtype level, necessarily generic within any `non-sealed` branch itself.

## 6. Walkthrough

Tracing `area(new Hexagon(4.0))` end to end from `NonSealedSwitchHandling.main`:

1. `Hexagon` implements `CustomShape`, which is declared `non-sealed` and extends the sealed `Shape` — so a `Hexagon` instance is simultaneously a `CustomShape` and, transitively, a `Shape`, even though `Hexagon` itself is never named anywhere in `Shape`'s own `permits` clause (only `CustomShape` is, and `CustomShape` deliberately permits any implementer at all).
2. `area` is called with this `Hexagon` instance, statically typed as `Shape` at the call site — the `switch` begins evaluating its case labels in order against the object's actual runtime type.
3. The `case Circle c` and `case Square s` labels are checked first and both fail to match, since a `Hexagon` is neither of those specific record types.
4. The `case CustomShape cs` label is checked next — since `Hexagon` does implement `CustomShape`, this label matches, binding `cs` to the `Hexagon` instance, but only with the *static* type `CustomShape` (the pattern's declared type), not `Hexagon` specifically, since the `switch` has no way to enumerate or name every possible `CustomShape` implementer individually.
5. `cs.area()` is called — since `cs`'s actual runtime type is `Hexagon`, this is an ordinary virtual method dispatch that resolves to `Hexagon.area()`'s specific implementation, computing `(3 * √3 / 2) * 4² = (3 * 1.732 / 2) * 16 ≈ 41.57`.
6. This value is returned from the `switch` expression and printed as `hexagon: 41.57` — confirming that even though the compiler could never have known about `Hexagon` specifically when `Shape`'s hierarchy was originally sealed (or even when `NonSealedSwitchHandling`'s `switch` was originally written), the `non-sealed CustomShape` branch's own interface contract (`area()`) is exactly what makes handling any future, unknown implementer correctly possible — completing the exhaustiveness picture at the `Shape` level, while deliberately deferring to ordinary polymorphism within the open `CustomShape` branch itself.

## 7. Gotchas & takeaways

> **Gotcha:** marking a branch `non-sealed` is a one-way design decision that's easy to underestimate the scope of — once external code (in a different module, or maintained by a different team) starts implementing that branch, you can no longer freely change or remove members from that branch's interface contract without potentially breaking those external implementers, exactly the same binary/source compatibility concern any ordinary public, extensible interface carries; sealing the rest of a hierarchy doesn't reduce this concern for the specific branch you've chosen to leave open.

- `non-sealed` is one of the three required continuations (alongside `final` and `sealed`) for any class or interface named in a sealed type's `permits` clause — it deliberately reopens that specific branch to unrestricted, ordinary subclassing.
- Use it for hierarchies that are a genuine mix of "these specific cases are fixed" and "but this one category is meant to be extensible" — third-party plugins, custom integrations, or a migration path for an already-widely-subclassed existing type.
- A `non-sealed` branch gives up exhaustiveness checking for its own possible concrete subtypes — a `switch` handling it must dispatch generically (typically via the branch's own interface methods), even though the `switch` can still be exhaustive at the sealed type's own top level.
- Reopening a branch is effectively a one-way, ordinary-interface-compatibility commitment for that specific branch — changing its contract later can break external implementers exactly as it would for any conventional, unsealed public interface.
- See [sealed / permits clauses](0961-sealed-permits-clauses.md) for the full mechanics of sealed hierarchies this modifier operates within, and [exhaustiveness in switch](0964-exhaustiveness-in-switch.md) for precisely how a `non-sealed` branch affects what the compiler can and cannot verify about a `switch`'s completeness.
