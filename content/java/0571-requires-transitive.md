---
card: java
gi: 571
slug: requires-transitive
title: requires transitive
---

## 1. What it is

`requires transitive` is a variant of the `requires` directive that not only lets the declaring module use another module's exported packages, but also **passes that access on** to any module that, in turn, requires the declaring module. It propagates a dependency one hop further than plain `requires` would, so consumers don't need to redeclare a dependency your own public API already exposes.

## 2. Why & when

Plain `requires` is deliberately non-transitive: if `app` requires `billing`, and `billing` requires `com.example.core`, `app` cannot use `com.example.core`'s types unless it also declares its own `requires com.example.core` — even if `billing`'s own public methods return `Money` objects from `com.example.core` right in their signatures. That's the right default for *internal* dependencies (implementation details a consumer shouldn't need to know about), but it's the wrong default whenever a dependency's types appear directly in your module's own **public API** — a consumer calling `Invoice getInvoice()` needs to be able to name the `Money` type of one of `Invoice`'s fields, or catch an exception type your API throws, without separately hunting down and declaring every module those types happen to live in. `requires transitive` fixes this: it tells the compiler "any module that requires me also implicitly gets access to this dependency," matching the natural expectation that using a library's public API doesn't require independently rediscovering that library's own dependencies.

## 3. Core concept

```java
module billing {
    requires transitive com.example.core; // billing's API exposes Money types
    exports com.billing.api;
}
```

```java
module app {
    requires billing; // app automatically also gets access to com.example.core's exports
}
```

```java
package com.myapp;
import com.billing.api.Invoice;
import com.example.core.money.Money; // legal WITHOUT app declaring requires com.example.core itself

public class Main {
    Money total(Invoice invoice) { return invoice.amount(); }
}
```

Without the `transitive` keyword on `billing`'s `requires com.example.core`, that last import would fail to compile in `app`, exactly as it did in the plain `requires` topic — `transitive` is what changes that outcome.

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="requires transitive propagates visibility of a dependency one hop further to any module that requires the declaring module">
  <rect x="20" y="50" width="150" height="50" rx="8" fill="#1c2430" stroke="#6db33f"/>
  <text x="95" y="80" fill="#6db33f" font-size="11" text-anchor="middle" font-family="monospace">module app</text>

  <line x1="170" y1="75" x2="260" y2="75" stroke="#79c0ff" stroke-width="2" marker-end="url(#t1)"/>
  <text x="215" y="65" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">requires</text>

  <rect x="260" y="50" width="150" height="50" rx="8" fill="#1c2430" stroke="#79c0ff"/>
  <text x="335" y="80" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="monospace">module billing</text>

  <line x1="410" y1="75" x2="500" y2="75" stroke="#f0883e" stroke-width="2" stroke-dasharray="0" marker-end="url(#t2)"/>
  <text x="455" y="65" fill="#f0883e" font-size="9" text-anchor="middle" font-family="sans-serif">requires transitive</text>

  <rect x="500" y="50" width="120" height="50" rx="8" fill="#1c2430" stroke="#f0883e"/>
  <text x="560" y="80" fill="#f0883e" font-size="10" text-anchor="middle" font-family="monospace">com.example.core</text>

  <path d="M 95 100 Q 340 145 560 100" stroke="#f0883e" stroke-width="1.5" stroke-dasharray="4,3" fill="none" marker-end="url(#t3)"/>
  <text x="340" y="140" fill="#f0883e" font-size="9" text-anchor="middle" font-family="sans-serif">app can ALSO see com.example.core's exports, transitively</text>

  <defs>
    <marker id="t1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
    <marker id="t2" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#f0883e"/></marker>
    <marker id="t3" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#f0883e"/></marker>
  </defs>
</svg>

The dashed arrow is the extra reach `transitive` grants — without it, `app` would only see `billing`'s own exports, not `com.example.core`'s.

## 5. Runnable example

Scenario: the same `billing` module from the plain `requires` topic, whose public `Invoice` API exposes a `Money` type from `com.example.core` — starting with the plain, non-transitive version that forces every consumer to redeclare the dependency, then adding `transitive` to remove that burden, then verifying the difference by attempting to compile a consumer both ways.

### Level 1 — Basic

```java
// File: com.example.core/module-info.java
module com.example.core {
    exports com.example.core.money;
}
```

```java
// File: com.example.core/com/example/core/money/Money.java
package com.example.core.money;

public record Money(long cents, String currency) {
    @Override public String toString() {
        return String.format("%d.%02d %s", cents / 100, cents % 100, currency);
    }
}
```

```java
// File: billing/module-info.java — plain requires, NOT transitive
module billing {
    requires com.example.core;
    exports com.billing.api;
}
```

```java
// File: billing/com/billing/api/Invoice.java — Money appears in the PUBLIC API
package com.billing.api;
import com.example.core.money.Money;

public class Invoice {
    private final Money amount;
    public Invoice(Money amount) { this.amount = amount; }
    public Money amount() { return amount; } // consumers need to name Money to use this
}
```

**How to run:** `javac -d out --module-source-path . $(find com.example.core billing -name "*.java")`

Expected output: compiles cleanly (this level only establishes the library; the consumer comes in Level 2).

`billing`'s public method `amount()` returns a `Money` — a type from `com.example.core`, a module `billing` merely `requires` (not `requires transitive`). This compiles fine for `billing` itself, since `billing`'s own code is allowed to use anything it requires. The consequence only shows up for *consumers* of `billing`, tested next.

### Level 2 — Intermediate

```java
// File: app/module-info.java — only requires billing, NOT com.example.core directly
module app {
    requires billing;
}
```

```java
// File: app/com/myapp/Main.java
package com.myapp;
import com.billing.api.Invoice;
import com.example.core.money.Money;

public class Main {
    public static void main(String[] args) {
        Invoice invoice = new Invoice(new Money(19999, "USD"));
        Money amount = invoice.amount(); // needs to NAME the Money type to hold this
        System.out.println("Amount: " + amount);
    }
}
```

**How to run:** `javac -d out --module-source-path . $(find com.example.core billing app -name "*.java")`

Expected output (compilation fails — this is the intended demonstration):
```
app/com/myapp/Main.java:3: error: package com.example.core.money is not visible
import com.example.core.money.Money;
                       ^
  (package com.example.core.money is declared in module com.example.core, but module app does not read it)
```

The real-world concern this adds: **using `billing`'s own public API is enough to force a consumer to also depend on `com.example.core`**, since `Invoice.amount()`'s return type is `Money`. But `app` never separately declared `requires com.example.core` — it only knows about `billing` — so `javac` rejects the `import com.example.core.money.Money` line, even though `app` needs that type purely to hold the return value of a method it's legitimately calling on `billing`'s own exported class.

### Level 3 — Advanced

```java
// File: billing/module-info.java — add the transitive keyword
module billing {
    requires transitive com.example.core; // propagate visibility to consumers of billing
    exports com.billing.api;
}
```

```java
// File: app/module-info.java — UNCHANGED from Level 2, still only requires billing
module app {
    requires billing;
}
```

```java
// File: app/com/myapp/Main.java — UNCHANGED from Level 2
package com.myapp;
import com.billing.api.Invoice;
import com.example.core.money.Money;

public class Main {
    public static void main(String[] args) {
        Invoice invoice = new Invoice(new Money(19999, "USD"));
        Money amount = invoice.amount();
        System.out.println("Amount: " + amount);
    }
}
```

**How to run:**
```
javac -d out --module-source-path . $(find com.example.core billing app -name "*.java")
java --module-path out -m app/com.myapp.Main
```

Expected output:
```
Amount: 199.99 USD
```

This handles the production-flavoured fix: with **only** `billing`'s `module-info.java` changed (adding the single word `transitive`), and `app`'s `module-info.java` and `Main.java` left completely untouched from the failing Level 2 version, compilation now succeeds — `requires transitive com.example.core` in `billing` automatically extends `com.example.core`'s visibility to any module (like `app`) that requires `billing`, without `app` ever needing its own explicit `requires com.example.core` line.

## 6. Walkthrough

Execution starts with the compilation command in Level 3. `javac` first reads all three `module-info.java` files, building the full module graph: `billing` now declares `requires transitive com.example.core` (not plain `requires`), and `app` declares `requires billing`.

Because of the `transitive` keyword, the compiler treats `app`'s single `requires billing` edge as implicitly also granting a `requires com.example.core` edge — this is exactly what "transitive" means here: the dependency relationship propagates one hop along the `requires` graph, from `billing` to whoever requires `billing`.

```
without transitive:                       with transitive:
app --requires--> billing                  app --requires--> billing
       (app sees ONLY billing's exports)          |
                                            (app ALSO sees com.example.core's
                                             exports, via billing's "transitive"
                                             requires com.example.core)
```

`javac` then compiles `app/com/myapp/Main.java`. `import com.billing.api.Invoice` resolves normally (direct `requires billing`, and `com.billing.api` is exported). `import com.example.core.money.Money` now *also* resolves — not because `app` declared its own `requires com.example.core`, but because `billing`'s `requires transitive com.example.core` makes that dependency visible through `billing` as well.

At runtime, `java --module-path out -m app/com.myapp.Main` launches `Main.main`. `new Invoice(new Money(19999, "USD"))` constructs an `Invoice` wrapping a `Money` record holding `19999` cents and `"USD"`. `invoice.amount()` returns that same `Money` instance. `System.out.println("Amount: " + amount)` calls `Money`'s `toString()`, which formats `19999` cents as `"199.99"` (dividing by 100 for the whole part, taking the remainder for cents, per `Money`'s `String.format("%d.%02d %s", ...)` implementation) followed by the currency code, producing the final printed line `"Amount: 199.99 USD"`.

The key contrast with Level 2 is that **zero lines in `app`'s own module or source code changed** between the failing and passing versions — the fix lived entirely in `billing`'s declaration of how it wants its own dependency to propagate, which is exactly the intended design: a library author decides, once, whether a dependency is an internal implementation detail (plain `requires`) or part of the library's effective public surface (`requires transitive`), and every consumer benefits from that decision automatically.

## 7. Gotchas & takeaways

> The rule of thumb for choosing `transitive`: if a type from the required module appears in your own module's **exported public API** (a public method's parameter or return type, a public field's type, a thrown checked exception type), mark that `requires` as `transitive`. If the dependency is purely an internal implementation detail never exposed through your exported packages' public signatures, leave it as plain `requires` — making everything transitive by default would leak your internal dependency choices onto every consumer, defeating the purpose of having explicit dependency declarations at all.

- `requires transitive` chains further than one hop: if `app` requires `billing`, `billing` requires transitive `core`, and `core` requires transitive `utils`, then `app` also gets implicit access to `utils` — transitivity composes along the whole chain, not just one link.
- The JDK's own platform modules use this extensively — `java.se` (the "full Java SE" aggregator module) is essentially a long list of `requires transitive` declarations for individual platform modules, letting an application `requires java.se` once instead of listing dozens of platform modules individually.
- Marking a `requires` as `transitive` when it shouldn't be (a true implementation detail) accidentally makes your internal dependency part of your public contract — consumers may start directly depending on that transitively-visible module's types, making it a breaking change to ever remove or swap out that internal dependency later.
- `requires transitive` only affects **visibility** (which packages a downstream module can see), not the runtime module *resolution* — the module still has to actually be present on the module path regardless of whether any `requires` edge to it is marked transitive or not.
- IDE and compiler warnings sometimes flag "API leaks" — using a non-`transitive`-required module's type in your own exported public API — precisely because doing so silently breaks compilation for every consumer, exactly as demonstrated in the Level 2 example; treat that warning as a signal to either add `transitive` or to hide the leaking type behind a different, module-local type instead.
