---
card: java
gi: 702
slug: sealed-permits-non-sealed-keywords
title: sealed / permits / non-sealed keywords
---

## 1. What it is

Sealed types are built from three **contextual keywords**, none of which are reserved words (existing code with variables or methods named `sealed`, `permits`, or `non-sealed` still compiles): **`sealed`** marks a class or interface as having a restricted, known set of subtypes; **`permits`** lists exactly which classes or interfaces are allowed to extend or implement it; and **`non-sealed`** is applied to a *direct subtype* of a sealed type to deliberately reopen that one branch of the hierarchy, allowing it to be extended by arbitrary, unknown further subclasses. Every direct permitted subtype of a sealed type must be declared as exactly one of `final`, `sealed`, or `non-sealed` — there is no fourth option, and leaving the modifier off is a compile error.

## 2. Why & when

Sealing a type answers "what are all my direct subtypes?" — but real hierarchies sometimes need one branch to stay open for extension while the rest stays closed. `non-sealed` exists for exactly that case: you might seal a `PaymentMethod` interface to `CreditCard`, `PayPal`, and `ExternalPlugin`, where the first two are `final` (a closed, known implementation) but `ExternalPlugin` is `non-sealed` — reopening just that one branch so third-party plugin code can supply its own further subclasses, without giving up the exhaustiveness guarantee for the two built-in variants. Reach for `sealed`/`permits` when you want a closed, compiler-checked hierarchy; add `non-sealed` on one specific subtype only when that particular branch genuinely needs to stay open to unknown future extension, and understand that doing so means any exhaustive `instanceof` or `switch` over the hierarchy can no longer assume that branch's subtypes are fully known.

## 3. Core concept

```java
sealed interface PaymentMethod permits CreditCard, PayPal, ExternalPlugin {}

final class CreditCard implements PaymentMethod {}       // closed: no further subclasses
final class PayPal implements PaymentMethod {}            // closed: no further subclasses
non-sealed class ExternalPlugin implements PaymentMethod {} // reopened: anyone may extend this
```

`CreditCard` and `PayPal` are permanently closed leaves of the hierarchy; `ExternalPlugin` deliberately hands extensibility back to any third-party subclass.

## 4. Diagram

<svg viewBox="0 0 640 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A sealed PaymentMethod interface permits CreditCard and PayPal as closed final leaves, and ExternalPlugin as a non-sealed branch open to arbitrary further subclasses">
  <rect x="230" y="15" width="180" height="45" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="34" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">sealed PaymentMethod</text>
  <text x="320" y="50" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">permits CreditCard, PayPal, ExternalPlugin</text>

  <line x1="280" y1="60" x2="120" y2="110" stroke="#79c0ff" stroke-width="1.5"/>
  <line x1="320" y1="60" x2="320" y2="110" stroke="#79c0ff" stroke-width="1.5"/>
  <line x1="360" y1="60" x2="520" y2="110" stroke="#79c0ff" stroke-width="1.5"/>

  <rect x="50" y="110" width="140" height="40" rx="6" fill="#161b22" stroke="#79c0ff"/>
  <text x="120" y="134" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">final CreditCard</text>

  <rect x="250" y="110" width="140" height="40" rx="6" fill="#161b22" stroke="#79c0ff"/>
  <text x="320" y="134" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">final PayPal</text>

  <rect x="450" y="110" width="140" height="40" rx="6" fill="#161b22" stroke="#f0883e"/>
  <text x="520" y="134" fill="#f0883e" font-size="10" text-anchor="middle" font-family="sans-serif">non-sealed ExternalPlugin</text>

  <line x1="520" y1="150" x2="520" y2="180" stroke="#f0883e" stroke-width="1.5" stroke-dasharray="4,3"/>
  <text x="520" y="198" fill="#f0883e" font-size="9" text-anchor="middle" font-family="sans-serif">any 3rd-party subclass allowed here</text>
</svg>

Two branches stay permanently closed; one branch is deliberately reopened for unknown future extension.

## 5. Runnable example

Scenario: a `PaymentMethod` hierarchy for a checkout system — first the basic sealed hierarchy where every direct subtype is `final`, then reopening one branch with `non-sealed` so external plugin code can supply its own payment method implementations, then a third-party module extending that reopened branch and a dispatcher that handles the known types explicitly while falling back generically for the open one.

### Level 1 — Basic

```java
// File: PaymentBasic.java
public class PaymentBasic {
    sealed interface PaymentMethod permits CreditCard, PayPal {}
    record CreditCard(String last4) implements PaymentMethod {}
    record PayPal(String email) implements PaymentMethod {}

    static String describe(PaymentMethod method) {
        if (method instanceof CreditCard c) return "Card ending in " + c.last4();
        if (method instanceof PayPal p) return "PayPal account " + p.email();
        throw new IllegalStateException("unreachable: sealed to CreditCard, PayPal");
    }

    public static void main(String[] args) {
        System.out.println(describe(new CreditCard("4242")));
        System.out.println(describe(new PayPal("user@example.com")));
    }
}
```

**How to run:**
```
java PaymentBasic.java
```

Expected output:
```
Card ending in 4242
PayPal account user@example.com
```

### Level 2 — Intermediate

```java
// File: PaymentWithPlugin.java
public class PaymentWithPlugin {
    sealed interface PaymentMethod permits CreditCard, PayPal, ExternalPlugin {}
    record CreditCard(String last4) implements PaymentMethod {}
    record PayPal(String email) implements PaymentMethod {}
    non-sealed interface ExternalPlugin extends PaymentMethod {
        String pluginName();
    }

    static String describe(PaymentMethod method) {
        if (method instanceof CreditCard c) return "Card ending in " + c.last4();
        if (method instanceof PayPal p) return "PayPal account " + p.email();
        if (method instanceof ExternalPlugin plugin) return "Plugin payment via " + plugin.pluginName();
        throw new IllegalStateException("unreachable: sealed to CreditCard, PayPal, ExternalPlugin");
    }

    // A third-party implementation the sealed hierarchy could never have named in advance.
    record CryptoWallet(String walletAddress) implements ExternalPlugin {
        public String pluginName() { return "CryptoWallet"; }
    }

    public static void main(String[] args) {
        PaymentMethod[] methods = {
                new CreditCard("4242"),
                new PayPal("user@example.com"),
                new CryptoWallet("0xABCDEF")
        };
        for (PaymentMethod m : methods) {
            System.out.println(describe(m));
        }
    }
}
```

**How to run:**
```
java PaymentWithPlugin.java
```

Expected output:
```
Card ending in 4242
PayPal account user@example.com
Plugin payment via CryptoWallet
```

`ExternalPlugin` is declared `non-sealed`, so `CryptoWallet` — a type the original `PaymentMethod` hierarchy never named — is free to implement it. `describe`'s `instanceof ExternalPlugin` branch handles *any* current or future plugin generically, in exchange for giving up the ability to exhaustively enumerate every concrete type that could reach that branch.

### Level 3 — Advanced

```java
// File: PaymentHierarchyReport.java
import java.lang.reflect.Modifier;

public class PaymentHierarchyReport {
    sealed interface PaymentMethod permits CreditCard, PayPal, ExternalPlugin {}
    record CreditCard(String last4) implements PaymentMethod {}
    record PayPal(String email) implements PaymentMethod {}
    non-sealed interface ExternalPlugin extends PaymentMethod {
        String pluginName();
    }
    record CryptoWallet(String walletAddress) implements ExternalPlugin {
        public String pluginName() { return "CryptoWallet"; }
    }

    static String classify(Class<?> type) {
        if (type.isSealed()) return "sealed (closed, permits " + type.getPermittedSubclasses().length + ")";
        if (Modifier.isFinal(type.getModifiers())) return "final (closed leaf)";
        return "non-sealed (open to further extension)";
    }

    public static void main(String[] args) {
        for (Class<?> type : new Class<?>[]{ PaymentMethod.class, CreditCard.class, PayPal.class, ExternalPlugin.class }) {
            System.out.println(type.getSimpleName() + " -> " + classify(type));
        }
    }
}
```

**How to run:**
```
java PaymentHierarchyReport.java
```

Expected output:
```
PaymentMethod -> sealed (closed, permits 3)
CreditCard -> final (closed leaf)
PayPal -> final (closed leaf)
ExternalPlugin -> non-sealed (open to further extension)
```

## 6. Walkthrough

1. `main` builds an array mixing the two closed record types with `CryptoWallet`, a completely separate type declared later in the same file that implements `ExternalPlugin` — a type `PaymentMethod`'s original `permits` clause never mentions by name, since it only had to name `ExternalPlugin` itself.
2. `describe`'s `instanceof` chain checks `CreditCard`, then `PayPal`, then falls to a broader `instanceof ExternalPlugin` check — this last branch matches `CryptoWallet` (and would match any other class implementing `ExternalPlugin`) because Java's `instanceof` follows the actual implements/extends chain at runtime, regardless of how many hops away the checked type is.
3. In `PaymentHierarchyReport`, `classify` inspects each `Class` object: `PaymentMethod.class.isSealed()` is `true` with three permitted subclasses; `CreditCard.class` and `PayPal.class` are plain `final` classes (not sealed themselves — they're leaves with no further permitted subtypes); `ExternalPlugin.class` is neither sealed nor final, so it falls through to the `non-sealed` branch.
4. This three-way classification — `sealed`, `final`, or effectively `non-sealed` — mirrors exactly the three legal modifiers a direct permitted subtype of a sealed type must choose from; `classify` reconstructs which one applies to a given `Class` purely through reflection, without reading source code.
5. The takeaway made concrete here: sealing a hierarchy is not all-or-nothing. `PaymentMethod` is fully closed at its own level (exactly three permitted subtypes, no more, no less), while deliberately handing back open extensibility to exactly one of those three branches via `non-sealed` — a targeted trade-off, not a hierarchy-wide one.

```
PaymentMethod (sealed) ──permits──► CreditCard (final)
                                  ├─► PayPal (final)
                                  └─► ExternalPlugin (non-sealed)
                                          └─► CryptoWallet (unknown to PaymentMethod's permits clause)
```

## 7. Gotchas & takeaways

> `sealed`, `permits`, and `non-sealed` are **contextual keywords**, not reserved words — a local variable, field, or method literally named `sealed` still compiles fine outside a type-declaration position. The compiler only interprets them specially where the grammar expects a class/interface modifier or a `permits` clause.
- Every **direct** permitted subtype of a sealed type must be exactly one of `final`, `sealed`, or `non-sealed` — omitting the modifier is a compile-time error, not a default to "open."
- `non-sealed` only reopens the *specific subtype* it's applied to — it does not affect sibling branches, and it does not make the original sealed type itself any less closed at its own level.
- A `record` implementing a sealed interface never needs an explicit `final` — records are implicitly `final`, satisfying the requirement automatically, as seen throughout this hierarchy's `CreditCard` and `PayPal`.
- Widening a hierarchy back open with `non-sealed` is a one-way trade: any code doing an exhaustive `instanceof`/`switch` over that branch can no longer assume its subtypes are fully enumerable, so use it deliberately, only where genuine external extensibility is required.
- See [sealed classes & interfaces — standardized](0701-sealed-classes-interfaces-standardized.md) for the broader feature history and reflection APIs (`Class.isSealed()`, `Class.getPermittedSubclasses()`) used to introspect a hierarchy built from these three keywords.
