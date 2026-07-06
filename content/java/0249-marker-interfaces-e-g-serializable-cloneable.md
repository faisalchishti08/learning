---
card: java
gi: 249
slug: marker-interfaces-e-g-serializable-cloneable
title: Marker interfaces (e.g. Serializable, Cloneable)
---

## 1. What it is

A marker interface is an interface with no methods or constants at all — an entirely empty body. It exists purely as a "flag" a class can attach to itself via `implements`, so that other code can check `instanceof SomeMarkerInterface` to detect an opt-in decision, without the interface itself imposing any method contract. `Cloneable` (seen earlier, gating `Object.clone()`'s behaviour) and `Serializable` (marking a class as eligible for Java's built-in object serialization) are the two most common JDK examples.

```java
interface Auditable { } // a marker interface: completely empty body

class Transaction implements Auditable { // opts in to being "audit-eligible" — no methods required
    double amount;
    Transaction(double amount) { this.amount = amount; }
}

public class MarkerDemo {
    public static void main(String[] args) {
        Transaction t = new Transaction(100.0);
        System.out.println(t instanceof Auditable); // true — the flag is checkable at runtime
    }
}
```

`Auditable` declares nothing at all — no methods, no constants — yet `Transaction implements Auditable` still compiles and gives `t instanceof Auditable` a meaningful, checkable answer at runtime; the interface's only purpose is to be present or absent, functioning as type-level metadata rather than a behavioural contract.

## 2. Why & when

Marker interfaces exist to let code make runtime decisions based on whether a class has opted into some behaviour, without requiring that class to implement any specific method.

- **Opt-in flags for framework or JDK behaviour** — `Cloneable` doesn't require any method, but its mere presence changes what `Object.clone()` does for that class (throwing `CloneNotSupportedException` if absent); `Serializable` similarly signals to Java's serialization machinery, "this class's instances are safe and intended to be converted to a byte stream," without declaring any method for that class to implement.
- **Type-safe categorization without behaviour** — sometimes you just need to group classes by a shared property (say, "this class's instances are safe to cache") for `instanceof`-based dispatch elsewhere in your code, and a marker interface achieves this cleanly, using the type system itself as the flag.
- **A lightweight alternative to annotations for some use cases** — before annotations (like `@Deprecated`) became common in Java 5, marker interfaces were the primary way to attach this kind of metadata to a class; today, annotations are often preferred for pure metadata, but marker interfaces remain useful specifically because they participate in the type system (checkable via `instanceof`, usable in generic bounds), which annotations alone cannot do as directly.

Use a marker interface when you need a class-level flag that participates in the type system itself — checkable with `instanceof`, usable as a generic type bound, or as a parameter type restricting what can be passed — and reach for annotations instead when you only need descriptive metadata that does not need to interact with types or overload resolution.

## 3. Core concept

```java
interface Cacheable { } // marker: no methods

class ExpensiveResult implements Cacheable {
    String data;
    ExpensiveResult(String data) { this.data = data; }
}

class Cache {
    void store(Object obj) {
        if (obj instanceof Cacheable) { // the marker interface gates behaviour here
            System.out.println("Caching: " + obj);
        } else {
            System.out.println("Not cacheable, skipping: " + obj);
        }
    }
}
```

`Cache.store` uses `instanceof Cacheable` to decide, at runtime, whether an object is eligible for caching — `Cacheable` itself never dictates *how* anything should behave, it simply exists to be detected, letting `Cache` treat marked and unmarked objects differently without either kind needing to implement any particular method.

## 4. Diagram

<svg viewBox="0 0 600 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A marker interface has an empty body and functions purely as a runtime checkable flag attached to a class via implements, with no methods required">
  <rect x="8" y="8" width="584" height="134" rx="8" fill="#0d1117"/>

  <rect x="60" y="20" width="180" height="35" rx="6" fill="#1c2430" stroke="#f85149" stroke-width="2"/>
  <text x="150" y="42" fill="#f85149" font-size="10" text-anchor="middle" font-family="monospace">interface Cacheable { }</text>

  <line x1="150" y1="55" x2="150" y2="75" stroke="#8b949e" stroke-width="1.5"/>
  <text x="200" y="72" fill="#8b949e" font-size="8" font-family="sans-serif">implements</text>

  <rect x="60" y="80" width="180" height="35" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="150" y="102" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">class ExpensiveResult</text>

  <rect x="350" y="45" width="220" height="45" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="460" y="63" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">if (obj instanceof Cacheable)</text>
  <text x="460" y="79" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">runtime flag check, no method call</text>

  <text x="300" y="130" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">The interface has zero methods — it exists purely to be detected.</text>
</svg>

A marker interface has no methods; its sole purpose is to be detectable at runtime via `instanceof`.

## 5. Runnable example

Scenario: a small object-processing pipeline that treats objects differently based on marker interfaces, evolved from one marker into two combined, then applied to a realistic filtering routine over a mixed list.

### Level 1 — Basic

```java
import java.util.List;

public class MarkerInterfaceBasic {
    interface Cacheable { }

    static class Report implements Cacheable {
        String title;
        Report(String title) { this.title = title; }
        @Override public String toString() { return "Report(" + title + ")"; }
    }

    static class TempData { // does NOT implement Cacheable
        @Override public String toString() { return "TempData"; }
    }

    public static void main(String[] args) {
        List<Object> items = List.of(new Report("Q1"), new TempData());
        for (Object item : items) {
            System.out.println(item + " cacheable? " + (item instanceof Cacheable));
        }
    }
}
```

**How to run:** `java MarkerInterfaceBasic.java`

`Report` implements `Cacheable`, `TempData` does not — the `instanceof Cacheable` check correctly distinguishes them at runtime, purely based on which classes opted into the empty marker interface.

### Level 2 — Intermediate

Same idea, now with a `Cache` class that only stores objects marked `Cacheable`, demonstrating the marker interface actually gating real behaviour, not just being printed for inspection.

```java
import java.util.ArrayList;
import java.util.List;

public class MarkerInterfaceIntermediate {
    interface Cacheable { }

    static class Report implements Cacheable {
        String title;
        Report(String title) { this.title = title; }
        @Override public String toString() { return "Report(" + title + ")"; }
    }

    static class TempData {
        @Override public String toString() { return "TempData"; }
    }

    static class Cache {
        List<Object> stored = new ArrayList<>();

        void offer(Object obj) {
            if (obj instanceof Cacheable) {
                stored.add(obj);
                System.out.println("Cached: " + obj);
            } else {
                System.out.println("Rejected (not Cacheable): " + obj);
            }
        }
    }

    public static void main(String[] args) {
        Cache cache = new Cache();
        cache.offer(new Report("Q1"));
        cache.offer(new TempData());
        cache.offer(new Report("Q2"));

        System.out.println("Total cached: " + cache.stored.size()); // 2
    }
}
```

**How to run:** `java MarkerInterfaceIntermediate.java`

`Cache.offer` uses the marker interface to actually decide behaviour: `Report` instances get added to `stored`, while `TempData` instances are rejected entirely — the empty `Cacheable` interface is doing real, functional work despite declaring no methods whatsoever.

### Level 3 — Advanced

Same cache system, now with a second, independent marker interface, `Sensitive`, used to redact certain objects from logging even while they remain cacheable — demonstrating multiple marker interfaces combined to express orthogonal, independent flags on the same object.

```java
import java.util.ArrayList;
import java.util.List;

public class MarkerInterfaceAdvanced {
    interface Cacheable { }
    interface Sensitive { } // a SECOND, independent marker interface

    static class Report implements Cacheable {
        String title;
        Report(String title) { this.title = title; }
        @Override public String toString() { return "Report(" + title + ")"; }
    }

    static class CreditCardInfo implements Cacheable, Sensitive { // implements BOTH markers
        String last4;
        CreditCardInfo(String last4) { this.last4 = last4; }
        @Override public String toString() { return "CreditCardInfo(**** " + last4 + ")"; }
    }

    static class Cache {
        List<Object> stored = new ArrayList<>();

        void offer(Object obj) {
            if (!(obj instanceof Cacheable)) {
                System.out.println("Rejected (not Cacheable): " + obj);
                return;
            }
            stored.add(obj);
            String logLine = (obj instanceof Sensitive) ? "[REDACTED]" : obj.toString();
            System.out.println("Cached: " + logLine);
        }
    }

    public static void main(String[] args) {
        Cache cache = new Cache();
        cache.offer(new Report("Q1"));
        cache.offer(new CreditCardInfo("4242"));

        System.out.println("Total cached: " + cache.stored.size()); // 2 — both were cacheable
        System.out.println("Actual stored content: " + cache.stored); // full data still stored internally
    }
}
```

**How to run:** `java MarkerInterfaceAdvanced.java`

`CreditCardInfo` implements both `Cacheable` and `Sensitive` simultaneously, so `Cache.offer` accepts it for storage (since it is `Cacheable`) but redacts it in the log line (since it is also `Sensitive`) — two independent marker interfaces combine to express two orthogonal facts about the same object, neither of which required a single method to be written.

## 6. Walkthrough

Trace both `cache.offer(...)` calls in `MarkerInterfaceAdvanced.main`.

**`cache.offer(new Report("Q1"))`.** `obj instanceof Cacheable` is `true` (`Report implements Cacheable`), so the early-return `if` is skipped. `stored.add(obj)` adds the `Report` to the list. `obj instanceof Sensitive` is `false` (`Report` does not implement `Sensitive`), so `logLine` is set to `obj.toString()`, which is `"Report(Q1)"`. Prints `"Cached: Report(Q1)"`.

**`cache.offer(new CreditCardInfo("4242"))`.** `obj instanceof Cacheable` is `true` (`CreditCardInfo` implements both markers, including `Cacheable`), so the early-return is skipped. `stored.add(obj)` adds it. `obj instanceof Sensitive` is `true` this time, so `logLine` is set to the literal string `"[REDACTED]"`, regardless of the object's actual `toString()`. Prints `"Cached: [REDACTED]"` — the sensitive data never appears in this log line.

**`cache.stored.size()`.** Both objects were added (both are `Cacheable`), so the size is `2`.

**`cache.stored`.** Printing the list calls `toString()` on each element via `List`'s own `toString()` implementation — this bypasses the `Cache.offer` redaction logic entirely (that redaction only applied to the *log line* printed during `offer`, not to the object's own `toString()`), so this line shows the *real*, unredacted `CreditCardInfo` data, illustrating that the marker interface only gates whatever logic explicitly checks for it — it does not automatically protect the data everywhere.

```
offer(Report("Q1")):
  instanceof Cacheable -> true -> stored.add
  instanceof Sensitive -> false -> logLine = obj.toString() = "Report(Q1)"
  prints "Cached: Report(Q1)"

offer(CreditCardInfo("4242")):
  instanceof Cacheable -> true -> stored.add
  instanceof Sensitive -> true -> logLine = "[REDACTED]"
  prints "Cached: [REDACTED]"

stored.size() -> 2
stored (direct toString(), bypasses offer's redaction) -> shows real CreditCardInfo(**** 4242) data
```

**Final output.**
```
Cached: Report(Q1)
Cached: [REDACTED]
Total cached: 2
Actual stored content: [Report(Q1), CreditCardInfo(**** 4242)]
```
This final line is a deliberate reminder: the `Sensitive` marker only affects behaviour where code explicitly checks for it (here, only inside `offer`'s log line) — it provides no automatic protection anywhere else, which is a real limitation of the marker-interface pattern worth noting.

## 7. Gotchas & takeaways

> **A marker interface provides no compiler-enforced behaviour at all — it only enables `instanceof` checks that *your own code* must remember to perform.** As the final print in the advanced example shows, printing `cache.stored` directly bypassed the redaction logic entirely, because nothing about implementing `Sensitive` automatically redacts anything anywhere; every piece of code that should respect the marker must explicitly check for it, which is a real design responsibility, not something the marker interface guarantees on its own.

> **Modern Java code increasingly prefers annotations (like a custom `@Cacheable`) over marker interfaces for pure metadata**, since annotations can carry additional data (parameters) and don't affect a class's type hierarchy at all; marker interfaces remain the right choice specifically when the flag needs to participate in the type system itself (via `instanceof`, generic bounds, or method parameter types), which annotations cannot do without separate reflection-based checking.

- A marker interface has no methods or constants; it exists purely to be detected via `instanceof`, acting as a class-level, type-system-integrated flag.
- `Cloneable` and `Serializable` are the classic JDK examples, gating `Object.clone()`'s behaviour and Java's built-in serialization respectively.
- Multiple independent marker interfaces can be implemented on the same class to express several orthogonal facts about it simultaneously.
- A marker interface enforces nothing on its own — every piece of code that should respect the marker must explicitly check for it via `instanceof`.
