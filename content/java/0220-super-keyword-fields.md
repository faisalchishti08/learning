---
card: java
gi: 220
slug: super-keyword-fields
title: super keyword (fields)
---

## 1. What it is

`super` is a reference, usable inside a subclass, that lets you explicitly access the superclass's version of something — this topic covers `super.fieldName`, used specifically to access a superclass field when the subclass has declared its **own** field with the same name, which **hides** (shadows) the inherited one rather than overriding it (fields don't support overriding the way methods do; they only support hiding).

```java
class Animal {
    String type = "Generic Animal";
}

class Dog extends Animal {
    String type = "Dog"; // hides Animal's 'type' field — this is a NEW, separate field, not an override

    void printBoth() {
        System.out.println(type);       // "Dog" — this class's own field
        System.out.println(super.type); // "Generic Animal" — explicitly reaching the superclass's field
    }
}
```

`Dog` actually has **two** separate `type` fields in memory simultaneously — its own (`"Dog"`) and the inherited one from `Animal` (`"Generic Animal"`) — plain `type` refers to `Dog`'s own field, while `super.type` explicitly reaches past it to the hidden, inherited one.

## 2. Why & when

`super.field` exists specifically to resolve the ambiguity created when a subclass declares a field with the same name as one it inherits — a situation less common than method overriding, but one Java must still define clear behaviour for:

- **Field hiding is different from method overriding** — unlike methods, fields are resolved based on the reference's **declared (compile-time) type**, not the object's actual runtime type; this makes field hiding behave quite differently from the dynamic dispatch that methods use, and is a common source of confusion.
- **`super.field` provides explicit access to the hidden field** — when a subclass genuinely needs both its own field and the inherited one (as in the `printBoth()` example), `super.field` is the only way to reach the superclass's version once it's been hidden by a same-named subclass field.
- **In practice, field hiding is generally discouraged** — because it can be so confusing, well-designed class hierarchies typically avoid giving a subclass field the exact same name as an inherited one; this topic exists mainly so you can recognize and correctly reason about the behaviour if you encounter it in existing code.

You use `super.field` specifically in the rare case where a subclass has deliberately hidden an inherited field and genuinely needs to access both versions — otherwise, avoiding same-named fields between superclass and subclass in the first place is the simpler, clearer design choice.

## 3. Core concept

```java
class Vehicle {
    int maxSpeed = 120;
}

class SportsCar extends Vehicle {
    int maxSpeed = 250; // hides Vehicle's maxSpeed — NOT an override, just a separate field

    void compare() {
        System.out.println("SportsCar's own: " + maxSpeed);       // 250
        System.out.println("Vehicle's (via super): " + super.maxSpeed); // 120
    }
}

Vehicle v = new SportsCar();
System.out.println(v.maxSpeed); // 120! — field access uses the REFERENCE's declared type, not the object's actual type
```

`v.maxSpeed` prints `120`, **not** `250`, even though `v` actually refers to a `SportsCar` object — this is the crucial difference from method calls: field access is resolved based on the *declared type* of the reference (`Vehicle` here) at compile time, never based on the object's actual runtime type, which is precisely why field hiding is considered confusing and best avoided in real class designs.

## 4. Diagram

<svg viewBox="0 0 600 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A SportsCar object holding two separate maxSpeed fields in memory, one inherited from Vehicle valued at 120 and one of its own valued at 250, with a Vehicle typed reference to this object reading the Vehicle field while a SportsCar typed reference reads its own field">
  <rect x="8" y="8" width="584" height="154" rx="8" fill="#0d1117"/>
  <text x="300" y="24" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">one SportsCar object, TWO separate maxSpeed fields in memory</text>

  <rect x="180" y="40" width="240" height="80" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="300" y="60" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">SportsCar object</text>
  <text x="300" y="82" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">Vehicle's maxSpeed = 120</text>
  <text x="300" y="100" fill="#6db33f" font-size="9" text-anchor="middle" font-family="monospace">SportsCar's maxSpeed = 250</text>

  <text x="130" y="145" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Vehicle v = ...; v.maxSpeed -&gt; 120</text>
  <text x="470" y="145" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">SportsCar s = ...; s.maxSpeed -&gt; 250</text>
</svg>

Field access is decided by the reference's declared type, not the object's actual type — the opposite of method dispatch.

## 5. Runnable example

Scenario: a small configuration hierarchy where a subclass deliberately hides a default value — starting with a basic demonstration of field hiding and `super.field`, then extending to show the declared-type resolution rule concretely, then hardening into a case explaining why avoiding field hiding entirely is generally the better design choice.

### Level 1 — Basic

```java
public class HidingBasic {
    static class Config {
        int timeout = 30;
    }

    static class FastConfig extends Config {
        int timeout = 5; // hides Config's timeout

        void showBoth() {
            System.out.println("FastConfig timeout: " + timeout);
            System.out.println("Config's original timeout: " + super.timeout);
        }
    }

    public static void main(String[] args) {
        FastConfig fc = new FastConfig();
        fc.showBoth();
    }
}
```

**How to run:** `java HidingBasic.java`

`FastConfig` declares its own `timeout` field, hiding `Config`'s — `showBoth()` demonstrates that both values genuinely coexist in memory, accessible separately as `timeout` (this class's own) and `super.timeout` (the hidden, inherited one).

### Level 2 — Intermediate

Same setup, now demonstrating the declared-type resolution rule directly: a `Config`-typed reference to a `FastConfig` object reads the *hidden*, superclass field, not the subclass's own.

```java
public class HidingIntermediate {
    static class Config {
        int timeout = 30;
    }

    static class FastConfig extends Config {
        int timeout = 5;
    }

    public static void main(String[] args) {
        FastConfig fc = new FastConfig();
        Config c = fc; // same object, different DECLARED reference type

        System.out.println("Via FastConfig reference: " + fc.timeout); // 5
        System.out.println("Via Config reference: " + c.timeout);       // 30 — surprising, but correct!
    }
}
```

**How to run:** `java HidingIntermediate.java`

`fc` and `c` refer to the exact same object, yet `fc.timeout` and `c.timeout` print different values — `5` versus `30` — because field access resolves based on each reference's own *declared* type at compile time, completely independent of the object's actual runtime type; this is precisely why field hiding is considered a design hazard, since it can produce genuinely surprising results depending purely on how a variable happens to be typed.

### Level 3 — Advanced

Same configuration idea, now demonstrating the recommended alternative: instead of hiding a field, a subclass should generally override a **method** that reads the field, since methods (unlike fields) *do* dispatch based on the object's actual runtime type, avoiding this entire class of confusion.

```java
public class HidingAdvanced {
    static class Config {
        protected int timeout = 30;

        int getTimeout() { // a METHOD wrapping the field — this DOES dispatch correctly
            return timeout;
        }
    }

    static class FastConfig extends Config {
        FastConfig() {
            this.timeout = 5; // just REASSIGNS the inherited field — no hiding, no second field
        }
        // no field hiding, no method override needed — getTimeout() already reads the right value
    }

    public static void main(String[] args) {
        FastConfig fc = new FastConfig();
        Config c = fc; // same object, different declared reference type

        System.out.println("Via FastConfig reference: " + fc.getTimeout()); // 5
        System.out.println("Via Config reference: " + c.getTimeout());       // 5 — consistent!
    }
}
```

**How to run:** `java HidingAdvanced.java`

By having `FastConfig` simply *reassign* the single inherited `timeout` field (rather than declaring a new one with the same name) and exposing it through `getTimeout()`, both `fc.getTimeout()` and `c.getTimeout()` consistently return `5` — since method calls dispatch based on the object's actual type, and there's only ever one `timeout` field involved, eliminating the surprising inconsistency field hiding would have introduced.

## 6. Walkthrough

Trace `HidingIntermediate.main`, contrasting `fc.timeout` and `c.timeout`:

**Construction.** `new FastConfig()` creates one object holding **two** `timeout` fields internally: `Config`'s own (defaulting to `30` via its field initializer) and `FastConfig`'s own (defaulting to `5` via its field initializer) — both exist simultaneously in the same object's memory, since field hiding doesn't replace the inherited field, it just adds a second one alongside it.

**`fc.timeout`.** `fc` is declared as `FastConfig`. The compiler resolves `fc.timeout` at compile time to mean "the `timeout` field as seen from a `FastConfig`-typed reference" — this is `FastConfig`'s own field, `5`.

**`Config c = fc;`.** `c` now refers to the exact same object as `fc`, but `c`'s *declared type* is `Config`.

**`c.timeout`.** The compiler resolves `c.timeout` at compile time to mean "the `timeout` field as seen from a `Config`-typed reference" — this is `Config`'s own (hidden, but still present) field, `30`, completely regardless of the fact that the actual object is a `FastConfig`.

```
one FastConfig object contains: Config's timeout=30, FastConfig's timeout=5 (two separate fields)

fc (declared FastConfig) .timeout -> resolved at compile time to FastConfig's field -> 5
c  (declared Config)     .timeout -> resolved at compile time to Config's field     -> 30
```

**Final output.** `"Via FastConfig reference: 5"` then `"Via Config reference: 30"` — both lines read from the *same* underlying object, yet produce different results purely because of each reference variable's own declared type, a direct demonstration of why field access does not participate in dynamic dispatch the way method calls do.

## 7. Gotchas & takeaways

> **Field access is resolved by the reference's declared (compile-time) type, never by the object's actual runtime type — this is the exact opposite of how method calls (dynamic dispatch, a later topic) behave.** This asymmetry is one of the most surprising and commonly-misunderstood aspects of Java for programmers still building their mental model of inheritance.

> **The strongly preferred practice is to avoid field hiding entirely** — if a subclass needs to change or provide a different value for something conceptually inherited, reassign the *same* field (as `FastConfig` does in the advanced example) rather than declaring a new field with an identical name, and expose access through methods, which dispatch correctly and predictably.

- `super.field` explicitly accesses a hidden superclass field from within a subclass that has declared its own field with the same name.
- Field hiding creates two genuinely separate fields coexisting in the same object — it does not override or replace the inherited one.
- Field access resolves based on the reference's declared type at compile time, unlike method calls, which resolve based on the object's actual runtime type.
- Avoid field hiding in your own designs; prefer reassigning the same inherited field and exposing values through methods, which behave consistently regardless of reference type.
