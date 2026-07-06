---
card: java
gi: 230
slug: object-class-inheritance-root
title: Object class & inheritance root
---

## 1. What it is

Every class in Java, whether you write `extends` explicitly or not, ultimately inherits from `java.lang.Object`. If a class declares no superclass at all, the compiler silently inserts `extends Object` for you — there is exactly one root at the top of every inheritance hierarchy in the entire language, and it is `Object`.

```java
class Animal { } // implicitly: class Animal extends Object { }

public class ObjectRootDemo {
    public static void main(String[] args) {
        Animal a = new Animal();
        System.out.println(a instanceof Object); // true — every object IS-A Object
        System.out.println(a.getClass().getSuperclass()); // class java.lang.Object
    }
}
```

`Animal` never mentions `Object` anywhere in its source code, yet `a instanceof Object` is `true` and `Animal`'s superclass genuinely is `Object` — this is not a special case, it is how every single class in Java works, including classes you write yourself.

## 2. Why & when

`Object` being the universal root matters because it guarantees every reference in Java shares a small, common set of behaviours, no matter what type it is.

- **A shared baseline of methods** — `toString()`, `equals(Object)`, `hashCode()`, `getClass()`, and the threading methods `wait()`/`notify()`/`notifyAll()` (all covered in upcoming topics) are defined once on `Object` and inherited by literally everything, so any object anywhere can be printed, compared, or hashed without extra work.
- **Uniform storage and collections** — generic containers, reflection, and APIs that need to hold "any kind of object" (like the pre-generics `Object[]` arrays or `Object` parameters) rely on the fact that absolutely any value (aside from primitives) can be treated as an `Object`.
- **A common upcasting target** — since every class IS-A `Object`, you can always widen a reference to `Object` when you genuinely don't care about its specific type, and every object supports being asked basic questions like "what class are you?" via `getClass()`.

You rarely write `extends Object` explicitly (it would be redundant, since it happens automatically), but understanding that it always happens explains why methods like `toString()` are always available to override, even on a brand new class with no explicit superclass.

## 3. Core concept

```java
class Book { }        // extends Object, implicitly
class Ebook extends Book { } // extends Book, which extends Object

public class HierarchyDemo {
    public static void main(String[] args) {
        Ebook e = new Ebook();
        Class<?> c = e.getClass();
        while (c != null) {
            System.out.println(c.getName());
            c = c.getSuperclass();
        }
    }
}
```

Walking up `Ebook`'s superclass chain visits `Ebook`, then `Book`, then `java.lang.Object`, then `null` (`Object` has no superclass — it is the root) — every class's chain, no matter how deep, terminates at `Object` in exactly this way.

## 4. Diagram

<svg viewBox="0 0 600 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Object sits at the root of every inheritance hierarchy in Java, with Book extending Object and Ebook extending Book, so Ebook inherits everything Object defines">
  <rect x="8" y="8" width="584" height="204" rx="8" fill="#0d1117"/>

  <rect x="220" y="20" width="160" height="35" rx="6" fill="#1c2430" stroke="#f85149" stroke-width="2"/>
  <text x="300" y="42" fill="#f85149" font-size="10" text-anchor="middle" font-family="sans-serif">java.lang.Object (root)</text>

  <line x1="300" y1="55" x2="300" y2="80" stroke="#8b949e" stroke-width="1.5"/>

  <rect x="220" y="85" width="160" height="35" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="300" y="107" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">Book (implicit extends Object)</text>

  <line x1="300" y1="120" x2="300" y2="145" stroke="#8b949e" stroke-width="1.5"/>

  <rect x="220" y="150" width="160" height="35" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="300" y="172" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">Ebook extends Book</text>

  <text x="300" y="200" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Ebook inherits from Book, which inherits from Object — the chain always ends at Object.</text>
</svg>

Every class chain, however long, terminates at `Object`, which has no superclass of its own.

## 5. Runnable example

Scenario: a small logging utility that accepts "anything" to log, built up to show exactly how relying on `Object` as the universal root makes that possible, then hardened to handle `null` and mixed types safely.

### Level 1 — Basic

```java
public class ObjectRootBasic {
    static void logAnything(Object value) { // Object accepts literally any reference type
        System.out.println("Logged: " + value);
    }

    public static void main(String[] args) {
        logAnything("a string");
        logAnything(42); // autoboxed to Integer, which IS-A Object
        logAnything(new StringBuilder("builder"));
    }
}
```

**How to run:** `java ObjectRootBasic.java`

`logAnything` declares its parameter as `Object`, so it can accept a `String`, an autoboxed `Integer`, a `StringBuilder`, or any other reference type at all — this only works because every one of those classes ultimately extends `Object`.

### Level 2 — Intermediate

Same logger, now printing the runtime class of whatever was passed in, using `getClass()` — a method every object inherits from `Object` with no extra work.

```java
import java.util.List;

public class ObjectRootIntermediate {
    static void logAnything(Object value) {
        if (value == null) {
            System.out.println("Logged: null (no class)");
            return;
        }
        System.out.println("Logged: " + value + " [" + value.getClass().getSimpleName() + "]");
    }

    public static void main(String[] args) {
        logAnything("a string");
        logAnything(42);
        logAnything(List.of(1, 2, 3));
        logAnything(null);
    }
}
```

**How to run:** `java ObjectRootIntermediate.java`

Every non-null argument responds to `getClass()` because it is inherited straight from `Object`; `null` is handled with an explicit guard first, since calling any method on a `null` reference (including one inherited from `Object`) throws `NullPointerException`.

### Level 3 — Advanced

Same logger, now collecting entries into a heterogeneous list and demonstrating what happens when relying purely on `Object`'s default behaviour (before `toString()` is overridden, covered next) versus a type that customizes it.

```java
import java.util.ArrayList;
import java.util.List;

public class ObjectRootAdvanced {
    static class Widget { } // no toString() override — uses Object's default

    static class NamedWidget {
        private final String name;
        NamedWidget(String name) { this.name = name; }
        @Override
        public String toString() { return "NamedWidget(" + name + ")"; } // overrides Object's default
    }

    static List<String> logAll(List<Object> items) {
        List<String> results = new ArrayList<>();
        for (Object item : items) {
            String entry = (item == null) ? "null" : item.toString(); // toString() inherited/overridden from Object
            results.add(entry);
        }
        return results;
    }

    public static void main(String[] args) {
        List<Object> items = new ArrayList<>();
        items.add(new Widget());
        items.add(new NamedWidget("gizmo"));
        items.add("plain string");
        items.add(null);

        for (String entry : logAll(items)) {
            System.out.println(entry);
        }
    }
}
```

**How to run:** `java ObjectRootAdvanced.java`

`Widget` never overrides `toString()`, so it falls back to `Object`'s default (class name plus a hash, e.g. `ObjectRootAdvanced$Widget@1b6d3586`); `NamedWidget` overrides it to produce readable output; `String` already overrides it to return itself — all three flow through the exact same `logAll` method, because all three, and even `null` (handled explicitly), can be stored in a `List<Object>`.

## 6. Walkthrough

Trace `logAll(items)` in `ObjectRootAdvanced.main`, item by item, in list order.

**`items.add(new Widget())`.** A `Widget` is created and stored. Since `Widget` declares no superclass, the compiler treats it as `extends Object`, so it satisfies `List<Object>` directly.

**`logAll` processes `Widget`.** `item.toString()` is called; `Widget` never overrode `toString()`, so the call resolves, via inheritance, to `Object.toString()`, which returns the class name plus `@` plus the object's hash code in hex — something like `ObjectRootAdvanced$Widget@1b6d3586` (the exact hash varies per run).

**`logAll` processes `NamedWidget("gizmo")`.** `item.toString()` is called; dynamic dispatch finds `NamedWidget`'s own override first, which returns `"NamedWidget(gizmo)"` instead of the generic `Object` default.

**`logAll` processes `"plain string"`.** `String` overrides `toString()` to simply return itself, so the result is `"plain string"`.

**`logAll` processes `null`.** The ternary's `item == null` check catches this before any method call would happen, avoiding a `NullPointerException`, and adds the literal text `"null"`.

```
Widget        -> Object.toString() default -> "ObjectRootAdvanced$Widget@<hash>"
NamedWidget   -> overridden toString()      -> "NamedWidget(gizmo)"
String        -> overridden toString()      -> "plain string"
null          -> guarded explicitly         -> "null"
```

**Final output.** Four lines printed in order: the default `Object`-style identifier for `Widget`, `"NamedWidget(gizmo)"`, `"plain string"`, and `"null"` — showing that every type, overridden or not, flows through the same `Object`-typed method uniformly.

## 7. Gotchas & takeaways

> **`Object`'s default `toString()` output (class name + `@` + hex hash code) is not meant to be read by end users** — it exists purely as a fallback so *some* string representation always exists. Any class whose instances are printed or logged for humans should override `toString()` (the next topic) rather than relying on this default.

> **Calling any method — even one inherited from `Object`, like `toString()` or `getClass()` — on a `null` reference throws `NullPointerException`.** `Object` guarantees every non-null reference has these methods; it does nothing to protect against `null` itself, which must always be checked explicitly.

- Every class in Java, with or without an explicit `extends`, ultimately inherits from `java.lang.Object` — there is exactly one root.
- `Object` defines a small set of universal methods (`toString`, `equals`, `hashCode`, `getClass`, `wait`/`notify`/`notifyAll`) available on every object.
- Declaring a parameter or variable as type `Object` lets it accept any reference type, which is what makes generic, "accepts anything" APIs possible.
- `Object`'s own superclass is `null` — it is the one class in Java with no class above it.
