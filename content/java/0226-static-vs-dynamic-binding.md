---
card: java
gi: 226
slug: static-vs-dynamic-binding
title: Static vs dynamic binding
---

## 1. What it is

**Binding** is the process of connecting a method call (or field access) in your code to the actual code that runs. **Static binding** happens at compile time, based purely on the reference's declared type — this applies to fields, `static` methods, `private` methods, and `final` methods, none of which can be overridden or hidden in a way that depends on the runtime object. **Dynamic binding** happens at runtime, based on the object's actual type — this applies to ordinary (overridable) instance methods, which is exactly what makes dynamic dispatch (the previous topic) possible.

```java
class Animal {
    static String category() { return "Animal category"; } // static: STATIC binding
    String sound() { return "..."; }                          // instance, overridable: DYNAMIC binding
}

class Dog extends Animal {
    static String category() { return "Dog category"; } // hides Animal's static method
    @Override
    String sound() { return "Woof"; }                     // overrides Animal's instance method
}

Animal a = new Dog();
System.out.println(a.category()); // "Animal category" — STATIC binding: decided by a's DECLARED type
System.out.println(a.sound());     // "Woof" — DYNAMIC binding: decided by a's ACTUAL type
```

`a.category()` prints `"Animal category"`, not `"Dog category"`, even though `a` actually refers to a `Dog` — because `static` methods use static binding, resolved at compile time from `a`'s declared type (`Animal`); `a.sound()` prints `"Woof"`, correctly reflecting the actual `Dog` object, because instance methods use dynamic binding.

## 2. Why & when

Understanding which binding applies to which kind of member is essential for correctly predicting a program's behaviour, especially in situations involving both static and dynamic elements together:

- **Static binding is fast and predictable but "declared-type-blind"** — the compiler can resolve the call target immediately, without needing any runtime type information, but this means the result never adapts based on what the object actually is at runtime.
- **Dynamic binding enables polymorphism** — it's slightly more work for the JVM (a lookup based on the actual object's type at the moment of the call), but it's what allows overridden methods to behave correctly and flexibly across an entire class hierarchy.
- **Fields, `static` methods, and `private`/`final` methods are ineligible for dynamic binding** because none of them can be genuinely overridden (only hidden, in the case of fields and `static` methods, or not customizable at all, in the case of `private`/`final`) — static binding is the only sensible choice for members that can never vary polymorphically.

You need this distinction to correctly reason about any code mixing static and dynamic elements — particularly to avoid the common surprise of a `static` method or a field "not behaving polymorphically" the way an instance method would.

## 3. Core concept

```java
class Base {
    int value = 10;                        // field: STATIC binding
    static String label() { return "Base"; } // static method: STATIC binding
    String describe() { return "Base instance"; } // instance method: DYNAMIC binding
}

class Derived extends Base {
    int value = 20;                          // hides Base's value
    static String label() { return "Derived"; } // hides Base's label()
    @Override
    String describe() { return "Derived instance"; } // overrides Base's describe()
}

Base b = new Derived();
System.out.println(b.value);      // 10 — static binding, from Base (b's declared type)
System.out.println(b.label());    // "Base" — static binding, from Base
System.out.println(b.describe()); // "Derived instance" — dynamic binding, from the ACTUAL Derived object
```

All three access the same `b` reference, yet `value` and `label()` both resolve statically to `Base`'s versions, while `describe()` resolves dynamically to `Derived`'s override — this side-by-side contrast is the clearest illustration of the two binding modes coexisting in the exact same object.

## 4. Diagram

<svg viewBox="0 0 600 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Three accesses through the same Base typed reference to an actual Derived object: field access and static method call both resolved statically using the declared Base type, while the instance method call is resolved dynamically using the actual Derived type">
  <rect x="8" y="8" width="584" height="154" rx="8" fill="#0d1117"/>
  <text x="300" y="24" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Base b = new Derived();</text>

  <rect x="20" y="40" width="170" height="50" rx="6" fill="#1c2430" stroke="#f85149" stroke-width="1.5"/>
  <text x="105" y="60" fill="#f85149" font-size="9" text-anchor="middle" font-family="monospace">b.value -&gt; 10</text>
  <text x="105" y="78" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">static binding (declared type)</text>

  <rect x="215" y="40" width="170" height="50" rx="6" fill="#f85149" fill-opacity="0.15" stroke="#f85149" stroke-width="1.5"/>
  <text x="300" y="60" fill="#f85149" font-size="9" text-anchor="middle" font-family="monospace">b.label() -&gt; "Base"</text>
  <text x="300" y="78" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">static binding (declared type)</text>

  <rect x="410" y="40" width="170" height="50" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="495" y="60" fill="#6db33f" font-size="9" text-anchor="middle" font-family="monospace">b.describe() -&gt; "Derived..."</text>
  <text x="495" y="78" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">DYNAMIC binding (actual type)</text>

  <text x="300" y="120" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Fields and static methods: resolved by declared type, at compile time.</text>
  <text x="300" y="140" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Overridable instance methods: resolved by actual type, at runtime.</text>
</svg>

Fields and static methods bind statically; overridable instance methods bind dynamically — even through the same reference.

## 5. Runnable example

Scenario: a small reporting utility mixing static configuration with instance-specific formatting — starting with a basic contrast between a field and an overridden method, then extending to a static method alongside them, then hardening into a case demonstrating why relying on static binding for something meant to vary per-subclass is a common design mistake.

### Level 1 — Basic

```java
public class BindingBasic {
    static class Report {
        String header = "Generic Report";
        String render() { return "Rendering: " + header; }
    }

    static class SalesReport extends Report {
        String header = "Sales Report"; // hides Report's header
        @Override
        String render() { return "Rendering (sales-specific): " + header; }
    }

    public static void main(String[] args) {
        Report r = new SalesReport();
        System.out.println(r.header);  // "Generic Report" — static binding
        System.out.println(r.render()); // "Rendering (sales-specific): Sales Report" — dynamic binding
    }
}
```

**How to run:** `java BindingBasic.java`

`r.header` resolves statically to `Report`'s own field (`"Generic Report"`), since fields don't use dynamic binding; `r.render()` resolves dynamically to `SalesReport`'s override, which — crucially — reads `header` from *within* `SalesReport`'s own code, where `header` correctly refers to `SalesReport`'s own hidden field (`"Sales Report"`), demonstrating how the two binding modes can produce seemingly inconsistent-looking (but individually correct) results.

### Level 2 — Intermediate

Same idea, now adding a `static` method alongside the field and instance method, for a complete three-way comparison.

```java
public class BindingIntermediate {
    static class Report {
        String header = "Generic Report";
        static String reportType() { return "Generic"; }
        String render() { return "Rendering: " + header; }
    }

    static class SalesReport extends Report {
        String header = "Sales Report";
        static String reportType() { return "Sales"; }
        @Override
        String render() { return "Rendering (sales-specific): " + header; }
    }

    public static void main(String[] args) {
        Report r = new SalesReport();
        System.out.println("Field: " + r.header);            // static binding -> "Generic Report"
        System.out.println("Static method: " + r.reportType()); // static binding -> "Generic"
        System.out.println("Instance method: " + r.render());   // dynamic binding -> sales-specific
    }
}
```

**How to run:** `java BindingIntermediate.java`

Both `r.header` and `r.reportType()` resolve statically, from `r`'s *declared* type `Report`, giving `"Generic Report"` and `"Generic"` respectively — despite `r` actually holding a `SalesReport` object; only `r.render()` (an ordinary, overridable instance method) uses dynamic binding, correctly producing the sales-specific result.

### Level 3 — Advanced

Same reporting system, now demonstrating a concrete design mistake: relying on a `static` method for something that was intended to vary per-subclass, and how this silently breaks compared to using an instance method instead.

```java
import java.util.List;

public class BindingAdvanced {
    static class Report {
        static String reportType() { return "Generic"; } // MISTAKE: intended to vary, but static binding prevents it
        String reportTypeInstance() { return "Generic"; } // CORRECT alternative: instance method, dynamically bound
    }

    static class SalesReport extends Report {
        static String reportType() { return "Sales"; } // hides, does NOT override — a trap
        @Override
        String reportTypeInstance() { return "Sales"; } // genuinely overrides
    }

    static void printTypeViaStaticMethod(Report r) {
        System.out.println("Via static method: " + r.reportType()); // ALWAYS "Generic" — static binding, regardless of r's actual type
    }

    static void printTypeViaInstanceMethod(Report r) {
        System.out.println("Via instance method: " + r.reportTypeInstance()); // correctly varies per actual type
    }

    public static void main(String[] args) {
        List<Report> reports = List.of(new Report(), new SalesReport());

        for (Report r : reports) {
            printTypeViaStaticMethod(r);
            printTypeViaInstanceMethod(r);
        }
    }
}
```

**How to run:** `java BindingAdvanced.java`

`printTypeViaStaticMethod` always prints `"Generic"`, regardless of whether the actual object is a `Report` or a `SalesReport`, because `r.reportType()` is bound statically to the parameter's declared type `Report`; `printTypeViaInstanceMethod` correctly varies between `"Generic"` and `"Sales"`, since `reportTypeInstance()` is an ordinary overridable method, dynamically bound to each object's genuine runtime type.

## 6. Walkthrough

Trace the loop in `BindingAdvanced.main` for `reports = [Report(), SalesReport()]`:

**First iteration, `r` is a plain `Report`.** `printTypeViaStaticMethod(r)` calls `r.reportType()` — statically bound to `Report.reportType()`, since the parameter `r` inside this method is declared `Report`. Returns `"Generic"`. Prints `"Via static method: Generic"`. `printTypeViaInstanceMethod(r)` calls `r.reportTypeInstance()` — dynamically bound to the actual object's type, which really is `Report` here, so `Report.reportTypeInstance()` runs, returning `"Generic"`. Prints `"Via instance method: Generic"`.

**Second iteration, `r` is a `SalesReport`.** `printTypeViaStaticMethod(r)` calls `r.reportType()` — **still** statically bound to `Report.reportType()` (the parameter's declared type inside `printTypeViaStaticMethod` is `Report`, unaffected by what object is actually passed), so it *still* returns `"Generic"`, even though the object is genuinely a `SalesReport`. Prints `"Via static method: Generic"` — the same result as before, which is exactly the bug this design mistake causes. `printTypeViaInstanceMethod(r)` calls `r.reportTypeInstance()` — dynamically bound, correctly resolving to `SalesReport`'s override this time, returning `"Sales"`. Prints `"Via instance method: Sales"`.

```
Report() instance:
  static method call -> "Generic" (correct, since it IS a Report)
  instance method call -> "Generic" (correct)

SalesReport() instance:
  static method call -> "Generic" (WRONG-feeling — static binding ignores the actual SalesReport type)
  instance method call -> "Sales" (correct — dynamic binding uses the actual type)
```

**Final output.** Four lines total: `"Via static method: Generic"`, `"Via instance method: Generic"`, `"Via static method: Generic"`, `"Via instance method: Sales"` — the repeated `"Generic"` from the static method call on the second, actually-`SalesReport` object is the exact, concrete demonstration of why relying on `static` methods for behaviour meant to vary polymorphically is a design mistake.

## 7. Gotchas & takeaways

> **A `static` method "hiding" a same-named superclass `static` method is fundamentally different from overriding — it never participates in dynamic dispatch, no matter how the calling code is structured.** If a piece of behaviour is genuinely meant to vary per subclass, it must be an ordinary (non-`static`) method; using `static` for this purpose is a common mistake that silently produces the superclass's version whenever accessed through a supertype-typed reference or parameter.

> **`final` and `private` instance methods also use static binding, not dynamic binding, since neither can be overridden at all** — calling a `final` or `private` method always runs exactly the version defined in the class doing the calling, with no possibility of a subclass altering that behaviour, which is precisely the guarantee `final` (an earlier topic) is meant to provide.

- Static binding (fields, `static` methods, `private`/`final` methods) resolves at compile time, based on the reference's declared type.
- Dynamic binding (ordinary overridable instance methods) resolves at runtime, based on the object's actual type.
- A `static` method that appears to "override" a superclass's same-named `static` method actually only hides it — it never participates in dynamic dispatch.
- Behaviour genuinely meant to vary across subclasses must be implemented as an ordinary, non-`static`, overridable instance method to benefit from dynamic binding.
