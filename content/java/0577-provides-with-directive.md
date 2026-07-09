---
card: java
gi: 577
slug: provides-with-directive
title: provides … with directive
---

## 1. What it is

The `provides ... with ...` directive is the producer-side counterpart to `uses`: it declares that a module supplies a concrete implementation of a service interface, registering it with the module system so that any module's `ServiceLoader.load(...)` call for that interface will discover and instantiate it. `provides com.example.spi.PaymentProvider with com.stripe.StripeProvider;` means "when anyone asks for `PaymentProvider` implementations, include `StripeProvider`."

## 2. Why & when

`uses` alone only declares that a module *wants* to discover implementations — it says nothing about where those implementations actually come from. `provides ... with ...` is how a separate module says "I am one of those implementations, and here's my concrete class." This is the mechanism that makes plugin architectures, pluggable algorithm registries, and swappable backend implementations work without the consuming code ever hard-coding a specific class name: a payment-processing application can `uses PaymentProvider` and work correctly whether zero, one, or five separate provider modules (Stripe, PayPal, a test double, a regional processor) happen to be present on the module path at any given deployment, entirely without recompiling or modifying the consumer.

## 3. Core concept

```java
module stripe.impl {
    requires payment.spi;
    provides com.payment.spi.PaymentProvider with com.stripe.impl.StripeProvider;
}
```

```java
package com.stripe.impl;
import com.payment.spi.PaymentProvider;

public class StripeProvider implements PaymentProvider {
    public StripeProvider() {} // no-arg constructor required — ServiceLoader instantiates it reflectively

    public String process(int amountCents) {
        return "Charged $" + (amountCents / 100.0) + " via Stripe";
    }
}
```

The interface name after `provides` and the implementing class after `with` must be fully qualified. A single module can declare multiple `provides ... with ...` lines (for different service interfaces), and can even list multiple implementation classes for the same interface, comma-separated, in one `with` clause.

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="provides with registers a concrete class as an implementation of a service interface, discoverable via ServiceLoader">
  <rect x="20" y="20" width="220" height="50" rx="8" fill="#1c2430" stroke="#79c0ff"/>
  <text x="130" y="42" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">module stripe.impl</text>
  <text x="130" y="60" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">provides PaymentProvider</text>

  <line x1="240" y1="45" x2="330" y2="45" stroke="#6db33f" stroke-width="2" marker-end="url(#p1)"/>
  <text x="285" y="35" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">with</text>

  <rect x="330" y="20" width="220" height="50" rx="8" fill="#1c2430" stroke="#6db33f"/>
  <text x="440" y="42" fill="#6db33f" font-size="11" text-anchor="middle" font-family="monospace">StripeProvider</text>
  <text x="440" y="60" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">implements PaymentProvider</text>

  <text x="20" y="110" fill="#8b949e" font-size="10" font-family="sans-serif">ServiceLoader.load(PaymentProvider.class), called from ANY module that "uses" it,</text>
  <text x="20" y="125" fill="#8b949e" font-size="10" font-family="sans-serif">discovers and instantiates StripeProvider automatically — no consumer code names it directly.</text>

  <defs>
    <marker id="p1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>
</svg>

The provider module registers itself once; every consumer's `ServiceLoader.load(...)` call picks it up automatically.

## 5. Runnable example

Scenario: a simple discount-calculation plugin system — starting with a single provider registered via `provides ... with ...` and consumed generically, then adding a second, competing provider implementation from the same module registered via one `provides` line listing two classes, then building a small "best discount wins" consumer that picks among all discovered providers without naming any of them.

### Level 1 — Basic

```java
// File: discount.spi/module-info.java
module discount.spi {
    exports com.discount.spi;
}
```

```java
// File: discount.spi/com/discount/spi/DiscountRule.java
package com.discount.spi;

public interface DiscountRule {
    String name();
    double discountPercent(double orderTotal);
}
```

```java
// File: discount.seasonal/module-info.java
module discount.seasonal {
    requires discount.spi;
    provides com.discount.spi.DiscountRule with com.discount.seasonal.WinterSaleRule;
}
```

```java
// File: discount.seasonal/com/discount/seasonal/WinterSaleRule.java
package com.discount.seasonal;
import com.discount.spi.DiscountRule;

public class WinterSaleRule implements DiscountRule {
    public String name() { return "winter-sale"; }
    public double discountPercent(double orderTotal) { return 10.0; }
}
```

```java
// File: app/module-info.java
module app {
    requires discount.spi;
    requires discount.seasonal;
    uses com.discount.spi.DiscountRule;
}
```

```java
// File: app/com/myapp/Main.java
package com.myapp;
import com.discount.spi.DiscountRule;
import java.util.ServiceLoader;

public class Main {
    public static void main(String[] args) {
        for (DiscountRule rule : ServiceLoader.load(DiscountRule.class)) {
            System.out.println(rule.name() + ": " + rule.discountPercent(100.0) + "%");
        }
    }
}
```

**How to run:** `javac -d out --module-source-path . $(find discount.spi discount.seasonal app -name "*.java") && java --module-path out -m app/com.myapp.Main`

Expected output:
```
winter-sale: 10.0%
```

`discount.seasonal`'s `provides com.discount.spi.DiscountRule with com.discount.seasonal.WinterSaleRule;` registers `WinterSaleRule` as an implementation of `DiscountRule`. `app`'s `ServiceLoader.load(DiscountRule.class)` call, from its `uses` declaration, discovers it automatically and instantiates it via its (implicit, public, no-argument) constructor — `Main.java` never names `WinterSaleRule` anywhere.

### Level 2 — Intermediate

```java
// File: discount.seasonal/module-info.java — ONE provides line, TWO implementation classes
module discount.seasonal {
    requires discount.spi;
    provides com.discount.spi.DiscountRule
        with com.discount.seasonal.WinterSaleRule, com.discount.seasonal.LoyaltyRule;
}
```

```java
// File: discount.seasonal/com/discount/seasonal/LoyaltyRule.java
package com.discount.seasonal;
import com.discount.spi.DiscountRule;

public class LoyaltyRule implements DiscountRule {
    public String name() { return "loyalty"; }
    public double discountPercent(double orderTotal) { return 5.0; }
}
```

**How to run:** `javac -d out --module-source-path . $(find discount.spi discount.seasonal app -name "*.java") && java --module-path out -m app/com.myapp.Main`

Expected output (both providers found; order follows declaration order in the `with` clause for a single module's `provides` line):
```
winter-sale: 10.0%
loyalty: 5.0%
```

The real-world concern this adds: **one module supplying multiple independent implementations** of the same service interface, all registered in a single `provides ... with ...` directive (comma-separated class list). `app`'s `module-info.java` and `Main.java` are completely unchanged from Level 1 — the second provider is discovered automatically purely because `discount.seasonal` now registers two classes instead of one.

### Level 3 — Advanced

```java
// File: discount.vip/module-info.java — a SECOND, independent provider module
module discount.vip {
    requires discount.spi;
    provides com.discount.spi.DiscountRule with com.discount.vip.VipRule;
}
```

```java
// File: discount.vip/com/discount/vip/VipRule.java
package com.discount.vip;
import com.discount.spi.DiscountRule;

public class VipRule implements DiscountRule {
    public String name() { return "vip"; }
    public double discountPercent(double orderTotal) { return 20.0; }
}
```

```java
// File: app/module-info.java — add requires discount.vip
module app {
    requires discount.spi;
    requires discount.seasonal;
    requires discount.vip;
    uses com.discount.spi.DiscountRule;
}
```

```java
// File: app/com/myapp/Main.java — pick the BEST discount among all discovered providers
package com.myapp;
import com.discount.spi.DiscountRule;
import java.util.ServiceLoader;
import java.util.Comparator;
import java.util.Optional;

public class Main {
    public static void main(String[] args) {
        double orderTotal = 100.0;

        Optional<DiscountRule> best = ServiceLoader.load(DiscountRule.class).stream()
            .map(ServiceLoader.Provider::get)
            .max(Comparator.comparingDouble(rule -> rule.discountPercent(orderTotal)));

        best.ifPresentOrElse(
            rule -> System.out.println("Best discount: " + rule.name() + " (" + rule.discountPercent(orderTotal) + "%)"),
            () -> System.out.println("No discount rules available")
        );
    }
}
```

**How to run:** `javac -d out --module-source-path . $(find discount.spi discount.seasonal discount.vip app -name "*.java") && java --module-path out -m app/com.myapp.Main`

Expected output:
```
Best discount: vip (20.0%)
```

This handles the production-flavoured case of **combining providers from multiple, entirely independent modules** and choosing among them programmatically, rather than just printing every one. `ServiceLoader.load(...).stream()` (the `Stream`-based API, an alternative to the classic `Iterable` form used in earlier levels) lazily wraps each discovered provider, `.map(ServiceLoader.Provider::get)` instantiates each one, and `.max(Comparator...)` picks the single best discount across all three registered rules (`winter-sale` 10%, `loyalty` 5%, `vip` 20%) — again, without `Main.java` naming any implementation class directly.

## 6. Walkthrough

Execution starts with the compilation and launch commands in Level 3, building four modules together: `discount.spi` (the interface), `discount.seasonal` (providing two implementations, `WinterSaleRule` and `LoyaltyRule`), `discount.vip` (providing one, `VipRule`), and `app` (the consumer, requiring all three provider-side modules and declaring `uses DiscountRule`).

At runtime, `Main.main` sets `orderTotal = 100.0` and calls `ServiceLoader.load(DiscountRule.class).stream()`. This returns a lazy `Stream<ServiceLoader.Provider<DiscountRule>>` — at this point, no implementation classes have been instantiated yet, only *located*.

```
ServiceLoader discovers, across the module graph:

discount.seasonal -> provides DiscountRule with WinterSaleRule, LoyaltyRule  (2 providers)
discount.vip       -> provides DiscountRule with VipRule                     (1 provider)

Total: 3 provider registrations found, from 2 independent modules.
```

`.map(ServiceLoader.Provider::get)` triggers actual instantiation as the stream is consumed: each `Provider` object's `.get()` method calls the corresponding implementation class's no-argument constructor, producing a `WinterSaleRule` instance, a `LoyaltyRule` instance, and a `VipRule` instance — three separate `DiscountRule` objects, one per registered class, regardless of which module registered them.

`.max(Comparator.comparingDouble(rule -> rule.discountPercent(orderTotal)))` evaluates `discountPercent(100.0)` for each: `WinterSaleRule` returns `10.0`, `LoyaltyRule` returns `5.0`, `VipRule` returns `20.0`. `Comparator.comparingDouble(...)` orders by that computed value, and `.max(...)` selects the single instance with the highest — `VipRule`, at `20.0`.

The `Optional<DiscountRule> best` now holds the `VipRule` instance. `best.ifPresentOrElse(...)` runs the first lambda (since a value is present), printing `"Best discount: vip (20.0%)"` — `rule.name()` returns `"vip"` and `rule.discountPercent(orderTotal)` is recomputed (a second call, cheap for this simple example) for the print statement.

At no point in this entire flow does `Main.java` reference `WinterSaleRule`, `LoyaltyRule`, or `VipRule` by name — the `provides ... with ...` directives in three separate, independently compiled modules are entirely responsible for making these three classes discoverable, and `ServiceLoader` handles instantiating and surfacing all of them uniformly through the shared `DiscountRule` interface.

## 7. Gotchas & takeaways

> The class named after `with` **must implement or extend** the interface/class named after `provides` (`javac` checks and rejects mismatches at compile time), and it **must have a public, no-argument constructor** — otherwise `ServiceLoader` cannot instantiate it reflectively at runtime, and attempting to do so throws `ServiceConfigurationError` (a runtime failure, not a compile-time one, since the constructor requirement isn't checked by `javac`).

- A single module can have multiple separate `provides ... with ...` lines for entirely different service interfaces — there's no limit on how many services one module can be a provider for.
- Listing multiple implementation classes in one `with` clause (`provides X with A, B;`, as in Level 2) versus using separate `provides` lines for the same interface across different modules (as in Level 3) are both valid and commonly combined — the module system doesn't distinguish between them at discovery time; both approaches simply register more providers for `ServiceLoader.load(...)` to find.
- `ServiceLoader.load(...)` returns providers lazily — instantiation happens as the iterator/stream is actually consumed, not the moment `load(...)` is called, which matters if a provider's constructor has meaningful side effects or if only a subset of discovered providers will actually be used.
- A provider module does **not** need to declare `uses` for the interface it provides — `uses` is only for modules that will call `ServiceLoader.load(...)` themselves; a pure provider module only needs `provides ... with ...` and whatever `requires` it needs to compile against the interface.
- If a provider's implementation class isn't `public` (or lacks a `public` no-argument constructor), `javac` still compiles the `provides` line successfully as long as the class *type-checks* as implementing the interface — the constructor-accessibility problem only surfaces as a runtime `ServiceConfigurationError` the first time `ServiceLoader` actually tries to instantiate it, making this a worthwhile thing to test explicitly rather than assume from a clean compile.
