---
card: java
gi: 1002
slug: adapter
title: Adapter
---

## 1. What it is

The **Adapter** pattern converts the interface of an existing class into another interface that calling code expects, letting classes with incompatible interfaces work together without modifying either one. It's the software equivalent of a physical power-plug adapter: it doesn't change the wall socket or the appliance, it just sits between them, translating one shape into the other.

## 2. Why & when

You often can't (or shouldn't) modify a third-party library's class or a legacy class to match the interface your new code expects — the library is external, or the legacy class is used elsewhere and changing it risks breaking other callers. Adapter lets you write one small wrapper class that implements the interface your code needs, translating each call into whatever the wrapped class actually understands, so both the old class and the new interface stay untouched.

Reach for Adapter whenever you need to plug an existing class (often from a library you don't control) into code that expects a different interface — integrating a third-party payment SDK behind your own `PaymentGateway` interface, or making a legacy `XmlReportGenerator` usable wherever your codebase expects a `ReportGenerator`. It's unnecessary when you control both sides and can simply change one of the interfaces to match the other directly.

## 3. Core concept

```
// The interface your code expects:
interface PaymentGateway { void charge(double amountInDollars); }

// A third-party class with an incompatible interface you can't change:
class LegacyStripeClient {
    void makeChargeInCents(long amountInCents) { /* ... */ }
}

// Adapter: implements the expected interface, translates to the legacy call
class StripeAdapter implements PaymentGateway {
    private final LegacyStripeClient client;
    StripeAdapter(LegacyStripeClient client) { this.client = client; }

    public void charge(double amountInDollars) {
        long cents = Math.round(amountInDollars * 100);
        client.makeChargeInCents(cents); // translates units AND method name
    }
}

// Calling code only ever sees PaymentGateway -- LegacyStripeClient stays hidden
PaymentGateway gateway = new StripeAdapter(new LegacyStripeClient());
gateway.charge(19.99);
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Calling code depends on PaymentGateway, which StripeAdapter implements by translating calls into the incompatible LegacyStripeClient interface">
  <rect x="20" y="60" width="140" height="40" rx="6" fill="#1c2430" stroke="#8b949e"/>
  <text x="90" y="85" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Calling code</text>

  <rect x="220" y="60" width="150" height="40" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="295" y="85" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">StripeAdapter</text>

  <rect x="440" y="60" width="180" height="40" rx="6" fill="#1c2430" stroke="#f0883e"/>
  <text x="530" y="85" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">LegacyStripeClient</text>

  <line x1="160" y1="80" x2="220" y2="80" stroke="#8b949e" marker-end="url(#a)"/>
  <text x="190" y="70" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">charge($)</text>
  <line x1="370" y1="80" x2="440" y2="80" stroke="#f0883e" marker-end="url(#a)"/>
  <text x="405" y="70" fill="#f0883e" font-size="8" text-anchor="middle" font-family="sans-serif">makeChargeInCents()</text>
  <defs><marker id="a" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

`StripeAdapter` sits between the expected interface and the incompatible legacy class, translating each call across the boundary.

## 5. Runnable example

Scenario: integrating a legacy payment client with a mismatched interface, evolving from directly calling the incompatible class into a clean adapter that lets calling code depend only on the interface it expects.

### Level 1 — Basic

```java
// File: AdapterBasic.java
class LegacyStripeClient {
    void makeChargeInCents(long amountInCents) {
        System.out.println("Charging " + amountInCents + " cents via legacy Stripe client");
    }
}

public class AdapterBasic {
    public static void main(String[] args) {
        LegacyStripeClient client = new LegacyStripeClient();
        double amountInDollars = 19.99;

        // Calling code has to know the legacy unit (cents) and method name directly.
        client.makeChargeInCents(Math.round(amountInDollars * 100));
    }
}
```

**How to run:** save as `AdapterBasic.java`, then `javac AdapterBasic.java && java AdapterBasic` (JDK 17+).

Expected output:
```
Charging 1999 cents via legacy Stripe client
```

Every caller that wants to charge a customer needs to know the legacy client's exact method name and that it expects cents, not dollars — that knowledge is duplicated wherever a charge happens.

### Level 2 — Intermediate

```java
// File: AdapterIntermediate.java
interface PaymentGateway {
    void charge(double amountInDollars);
}

class LegacyStripeClient {
    void makeChargeInCents(long amountInCents) {
        System.out.println("Charging " + amountInCents + " cents via legacy Stripe client");
    }
}

class StripeAdapter implements PaymentGateway {
    private final LegacyStripeClient client;
    StripeAdapter(LegacyStripeClient client) { this.client = client; }

    public void charge(double amountInDollars) {
        long cents = Math.round(amountInDollars * 100);
        client.makeChargeInCents(cents);
    }
}

public class AdapterIntermediate {
    static void checkout(PaymentGateway gateway, double amount) {
        gateway.charge(amount);
    }

    public static void main(String[] args) {
        PaymentGateway gateway = new StripeAdapter(new LegacyStripeClient());
        checkout(gateway, 19.99);
    }
}
```

**How to run:** save as `AdapterIntermediate.java`, then `javac AdapterIntermediate.java && java AdapterIntermediate` (JDK 17+).

Expected output:
```
Charging 1999 cents via legacy Stripe client
```

The real-world concern added: `checkout` depends only on `PaymentGateway.charge(double)` — it has no idea `LegacyStripeClient` or its cents-based method even exist. The unit conversion and method-name translation live in exactly one place, `StripeAdapter`.

### Level 3 — Advanced

```java
// File: AdapterAdvanced.java
interface PaymentGateway {
    void charge(double amountInDollars);
}

class LegacyStripeClient {
    void makeChargeInCents(long amountInCents) {
        if (amountInCents <= 0) throw new IllegalArgumentException("amount must be positive");
        System.out.println("Charging " + amountInCents + " cents via legacy Stripe client");
    }
}

// A second, entirely different payment provider with its OWN incompatible interface.
class PayPalSdk {
    void submitPayment(String amountAsDecimalString) {
        System.out.println("Submitting PayPal payment of $" + amountAsDecimalString);
    }
}

class StripeAdapter implements PaymentGateway {
    private final LegacyStripeClient client;
    StripeAdapter(LegacyStripeClient client) { this.client = client; }

    public void charge(double amountInDollars) {
        if (amountInDollars <= 0) {
            throw new IllegalArgumentException("charge amount must be positive: " + amountInDollars);
        }
        client.makeChargeInCents(Math.round(amountInDollars * 100));
    }
}

// A second adapter for a second, unrelated SDK -- checkout code below never changes.
class PayPalAdapter implements PaymentGateway {
    private final PayPalSdk sdk;
    PayPalAdapter(PayPalSdk sdk) { this.sdk = sdk; }

    public void charge(double amountInDollars) {
        sdk.submitPayment(String.format("%.2f", amountInDollars));
    }
}

public class AdapterAdvanced {
    static void checkout(PaymentGateway gateway, double amount) {
        gateway.charge(amount);
    }

    public static void main(String[] args) {
        checkout(new StripeAdapter(new LegacyStripeClient()), 19.99);
        checkout(new PayPalAdapter(new PayPalSdk()), 25.50);
    }
}
```

**How to run:** save as `AdapterAdvanced.java`, then `javac AdapterAdvanced.java && java AdapterAdvanced` (JDK 17+).

Expected output:
```
Charging 1999 cents via legacy Stripe client
Submitting PayPal payment of $25.50
```

The production-flavored hard case: two completely unrelated SDKs (`LegacyStripeClient` and `PayPalSdk`), each with its own incompatible interface, both get adapted to the same `PaymentGateway` contract — `checkout` calls either one identically, with zero knowledge of cents, decimal-string formatting, or either SDK's actual method names.

## 6. Walkthrough

Tracing `checkout(new PayPalAdapter(new PayPalSdk()), 25.50)` in `AdapterAdvanced.main`:

1. `new PayPalSdk()` constructs the third-party SDK object, with its own method `submitPayment(String)` that takes a decimal-formatted string, not a `double`.
2. `new PayPalAdapter(sdk)` wraps it, implementing `PaymentGateway`'s `charge(double)` method.
3. `checkout(gateway, 25.50)` calls `gateway.charge(25.50)` — dispatching, via the `PaymentGateway` interface, to `PayPalAdapter.charge`.
4. Inside `PayPalAdapter.charge`, `String.format("%.2f", 25.50)` converts the `double` into the exact string format `PayPalSdk` expects: `"25.50"`.
5. `sdk.submitPayment("25.50")` is called, printing `"Submitting PayPal payment of $25.50"`.
6. Compare with the `StripeAdapter` call just above it: `checkout` called `gateway.charge(19.99)` identically, but that time it dispatched to `StripeAdapter.charge`, which converted dollars to a `long` cents value (`1999`) and called `client.makeChargeInCents(1999)` instead — a completely different translation, entirely hidden from `checkout`.

## 7. Gotchas & takeaways

> **Gotcha:** an adapter should only translate the *interface* (method names, parameter shapes, units) — it shouldn't quietly add new business logic of its own. If `StripeAdapter.charge` started applying a discount before charging, that logic no longer belongs in an adapter; it belongs in the business logic that calls the gateway.

- Adapter converts an existing class's interface into the interface calling code expects, without modifying either side.
- It's the standard way to integrate a third-party library or legacy class behind an interface your own codebase already depends on.
- Each adapter typically handles one translation concern: renaming methods, converting units, reshaping parameters — keep it thin.
- Multiple unrelated classes can each get their own adapter implementing the same target interface, letting calling code treat them all identically.
- Don't reach for Adapter when you control both interfaces and can simply align them directly — it's specifically for bridging incompatible interfaces you can't (or shouldn't) change.
- Adapter and [Facade](1004-facade.md) both add a layer in front of existing code, but Adapter's goal is interface *compatibility* while Facade's goal is interface *simplification* — see Facade's entry for the distinction.
