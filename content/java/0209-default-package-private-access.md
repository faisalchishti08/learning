---
card: java
gi: 209
slug: default-package-private-access
title: default (package-private) access
---

## 1. What it is

**Package-private** (also called **default access**) is what a field, method, constructor, or class gets when you write **no** access modifier at all — no `public`, `protected`, or `private`. It means the member is accessible only from code within the **same package**; any class outside that package, even a subclass, cannot see it at all (this is the one key difference from `protected`, which *does* extend to subclasses in other packages).

```java
package com.example.orders;

class OrderValidator { // no modifier: package-private — only visible within com.example.orders
    boolean isValid(String orderId) { // also package-private
        return orderId != null && !orderId.isEmpty();
    }
}
```

```java
package com.example.orders; // SAME package

class OrderProcessor {
    void process() {
        OrderValidator v = new OrderValidator(); // legal: same package
        v.isValid("ORD-1");
    }
}
```

```java
package com.example.billing; // a DIFFERENT package

class Invoice {
    void doSomething() {
        // OrderValidator v = new OrderValidator(); // COMPILE ERROR — not visible outside com.example.orders
    }
}
```

`OrderValidator` and its method `isValid` have no access modifier at all — this "absence of a keyword" is itself a distinct, meaningful access level, restricting visibility to only the same package, `com.example.orders`.

## 2. Why & when

Package-private access exists to let related classes within one package collaborate closely and share implementation details, while keeping those same details completely hidden from code outside that package:

- **Package-internal collaboration** — helper classes, internal data structures, or coordination logic that several classes within one package need to share, but that no code outside the package should ever need or be allowed to touch.
- **A natural default for "not yet decided" or "internal only" access** — many classes and methods genuinely have no business being called from outside their own package; package-private is the appropriate level for these, reserving `public` specifically for the deliberate, external interface.
- **Package-private classes complement `public` classes** — a package might expose one or two `public` classes as its external interface, while every supporting class behind them stays package-private, invisible to and unusable by any external code, which keeps the package's internal design free to change without breaking outside dependents.

You leave off the access modifier entirely (getting package-private access) whenever a class or member is genuinely an internal implementation detail meant only for collaborating classes within the same package — the same principle behind favoring `private` within a single class, just applied at the package level instead.

## 3. Core concept

```java
package com.example.shop;

class InventoryTracker { // package-private class
    int stockCount; // package-private field

    void restock(int amount) { // package-private method
        stockCount += amount;
    }
}

public class Warehouse { // public class — the package's actual external interface
    private InventoryTracker tracker = new InventoryTracker(); // can use the package-private class internally

    public void addStock(int amount) {
        tracker.restock(amount); // legal: same package
        System.out.println("Stock now: " + tracker.stockCount);
    }
}
```

`InventoryTracker` is entirely invisible to code outside the `com.example.shop` package — only `Warehouse` (living in the same package) can create and use it, which lets the package's authors freely redesign or remove `InventoryTracker` later without any risk of breaking external code, since external code was never able to reference it in the first place.

## 4. Diagram

<svg viewBox="0 0 600 160" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A package boundary box containing a public Warehouse class and a package private InventoryTracker class, with outside code able to reach only the public class while the package private class remains completely invisible from outside the package boundary">
  <rect x="8" y="8" width="584" height="144" rx="8" fill="#0d1117"/>

  <rect x="180" y="25" width="260" height="110" rx="8" fill="none" stroke="#8b949e" stroke-width="1.5" stroke-dasharray="4,3"/>
  <text x="310" y="18" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">package com.example.shop</text>

  <rect x="200" y="40" width="220" height="35" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="310" y="62" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">public class Warehouse</text>

  <rect x="200" y="95" width="220" height="35" rx="6" fill="#1c2430" stroke="#f85149" stroke-width="1.5"/>
  <text x="310" y="117" fill="#f85149" font-size="10" text-anchor="middle" font-family="sans-serif">class InventoryTracker (package-private)</text>

  <line x1="60" y1="57" x2="200" y2="57" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#dp)"/>
  <text x="60" y="47" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">outside code: OK</text>

  <line x1="60" y1="112" x2="200" y2="112" stroke="#f85149" stroke-width="1.5" stroke-dasharray="3,2"/>
  <text x="60" y="130" fill="#f85149" font-size="9" text-anchor="middle" font-family="sans-serif">outside code: blocked</text>

  <defs><marker id="dp" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker></defs>
</svg>

Package-private members are visible only within the same package, invisible entirely from outside it.

## 5. Runnable example

Scenario: a small reporting system where an internal calculation helper is shared between two classes in the same package, but never exposed externally — starting with a basic package-private helper class, then extending with package-private methods coordinating internal state, then hardening into a public-facing class that hides all these internal collaborators completely from outside code.

Since this example lives entirely within one file for runnability, the "package" boundary is illustrated via comments describing which parts would live in separate files under the same package declaration in a real multi-file project.

### Level 1 — Basic

```java
public class ReportBasic {
    // In a real project, this class would have no "public" and live in its own file,
    // in the same package as ReportGenerator below — package-private, internal-only.
    static class ReportData {
        int recordCount;
    }

    static class ReportGenerator {
        String summarize(ReportData data) {
            return "Report covers " + data.recordCount + " records";
        }
    }

    public static void main(String[] args) {
        ReportData data = new ReportData();
        data.recordCount = 42;

        ReportGenerator generator = new ReportGenerator();
        System.out.println(generator.summarize(data));
    }
}
```

**How to run:** `java ReportBasic.java`

`ReportData` here plays the role of a package-private helper class — in a genuine multi-file project (rather than this single-file illustration), it would have no `public` modifier and would only be usable by other classes declared in that same package, like `ReportGenerator`.

### Level 2 — Intermediate

Same idea, now with package-private methods coordinating shared internal state between two collaborating classes.

```java
public class ReportIntermediate {
    static class ReportData {
        int recordCount;

        void increment() { // package-private in a real multi-file setup
            recordCount++;
        }
    }

    static class ReportGenerator {
        String summarize(ReportData data) {
            return "Report covers " + data.recordCount + " records";
        }

        void addRecord(ReportData data) {
            data.increment(); // calling the (conceptually) package-private method
        }
    }

    public static void main(String[] args) {
        ReportData data = new ReportData();
        ReportGenerator generator = new ReportGenerator();

        generator.addRecord(data);
        generator.addRecord(data);
        generator.addRecord(data);

        System.out.println(generator.summarize(data));
    }
}
```

**How to run:** `java ReportIntermediate.java`

`ReportGenerator.addRecord` calls `data.increment()` — in a real project with `ReportData` and `ReportGenerator` correctly declared package-private (or with only necessary members marked so) and placed in the same package, this collaboration works exactly as shown, while any class in a *different* package would have no way to call `increment()` at all.

### Level 3 — Advanced

Same reporting system, now with a `public` facade class that's the *only* thing external code ever interacts with, completely hiding the internal `ReportData`/`ReportGenerator` collaboration behind one simple, safe public method.

```java
public class ReportAdvanced {
    // Internal collaborators — in a real project, these would be package-private,
    // invisible to any code outside this reporting package.
    static class ReportData {
        int recordCount;
        void increment() { recordCount++; }
    }

    static class ReportGenerator {
        String summarize(ReportData data) {
            return "Report covers " + data.recordCount + " records";
        }
    }

    // The public facade — the ONLY thing external code should ever need to use.
    public static class ReportingService {
        private final ReportData data = new ReportData();
        private final ReportGenerator generator = new ReportGenerator();

        public void recordEvent() {
            data.increment();
        }

        public String getSummary() {
            return generator.summarize(data);
        }
    }

    public static void main(String[] args) {
        ReportingService service = new ReportingService(); // the only class "external" code touches

        service.recordEvent();
        service.recordEvent();
        service.recordEvent();
        service.recordEvent();

        System.out.println(service.getSummary());
    }
}
```

**How to run:** `java ReportAdvanced.java`

`main` (representing external, calling code) only ever interacts with `ReportingService` — the internal `ReportData` and `ReportGenerator` collaboration is entirely hidden behind this public facade; in a genuine multi-package project, marking those two helper classes package-private would make this hiding a compiler-enforced guarantee, not just a convention, ensuring outside code structurally cannot reach past the facade.

## 6. Walkthrough

Trace `ReportAdvanced.main`:

**Construction.** `new ReportingService()` runs its field initializers: `data = new ReportData()` (with `recordCount` defaulting to `0`), and `generator = new ReportGenerator()`.

**Four calls to `recordEvent()`.** Each call runs `data.increment()`, incrementing the *same* shared `data` object's `recordCount` field each time: `0 → 1 → 2 → 3 → 4`.

**`getSummary()`.** Calls `generator.summarize(data)`, which reads `data.recordCount` (now `4`) and returns `"Report covers 4 records"`.

```
service.recordEvent() x4:
  data.recordCount: 0 -> 1 -> 2 -> 3 -> 4

service.getSummary():
  generator.summarize(data) -> "Report covers 4 records"
```

**Final output.** `"Report covers 4 records"` — `main` never directly touched `ReportData` or `ReportGenerator`; it only ever called `ReportingService`'s two `public` methods, exactly as a well-designed package boundary (with internal collaborators kept package-private) would enforce structurally in a real multi-package project.

## 7. Gotchas & takeaways

> **Package-private access is determined by the package declaration, not by folder structure or file location alone** — two classes must have the exact same `package` statement at the top of their files to share package-private access; simply placing files in the same directory without matching `package` declarations does not grant this access.

> **Unlike `protected`, package-private access does NOT extend to subclasses in other packages** — this is the precise distinction between the two: `protected` reaches same-package classes *and* subclasses anywhere, while package-private (default) reaches only same-package classes, subclass or not.

- Package-private (default) access applies when no modifier (`public`, `protected`, `private`) is written at all.
- It restricts visibility to classes within the exact same package — invisible to any code outside that package, including subclasses elsewhere.
- It's the appropriate level for classes and members meant purely for internal collaboration within one package, hidden from all external code.
- A `public` facade class can expose a package's functionality safely while keeping its actual internal collaborators package-private and hidden.
