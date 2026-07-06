---
card: java
gi: 244
slug: implements-keyword
title: implements keyword
---

## 1. What it is

The `implements` keyword is how a class declares that it fulfills an interface's contract, appearing in the class declaration after any `extends` clause (a class can `extends` at most one class, but `implements` any number of interfaces, separated by commas). Using `implements` obligates the class to provide a concrete, `public` body for every abstract method the interface declares.

```java
interface Flyable {
    void fly();
}

class Bird implements Flyable { // implements: fulfills the Flyable contract
    @Override
    public void fly() { System.out.println("Flapping wings"); }
}

class Airplane extends Vehicle implements Flyable { // extends ONE class, implements interfaces too
    @Override
    public void fly() { System.out.println("Using jet engines"); }
}

class Vehicle { } // a plain superclass, unrelated to Flyable
```

`Bird` uses `implements Flyable` on its own; `Airplane` combines `extends Vehicle` (a single class) with `implements Flyable` (an interface) on the same declaration — `extends` always comes first when both appear together, and only one class may follow it, while any number of interfaces may follow `implements`.

## 2. Why & when

`implements` is the mechanism that actually connects a concrete class to an interface's contract, and understanding exactly how it interacts with class inheritance matters for building correct hierarchies.

- **Fulfilling a contract, not inheriting implementation** — unlike `extends` from a class (which can bring along real field values and method bodies), `implements` on a classic interface brings along only method *signatures* that must be filled in; there is nothing to inherit except the requirement itself (default methods, covered soon, add a partial exception to this).
- **Combining with `extends` for "is-a plus can-do"** — as the previous "abstract vs interface" topic covered, a class routinely both extends a superclass and implements one or more interfaces at once, expressing both its core identity and its additional capabilities in a single declaration.
- **Multiple interfaces on the same line** — `implements InterfaceA, InterfaceB, InterfaceC` lets one class satisfy several independent contracts simultaneously, something `extends` alone could never achieve since Java forbids extending more than one class.

Use `implements` any time a class needs to satisfy an interface's contract, whether standing alone or combined with `extends`; remember the ordering rule (`extends` before `implements`, if both are present) and that every interface method needs a `public` implementation somewhere in the class (either directly, or inherited from a superclass that already implements it).

## 3. Core concept

```java
interface Comparable2<T> {   // (illustrative name to avoid clashing with java.lang.Comparable)
    int compareVal(T other);
}

interface Describable {
    String describe();
}

class Money implements Comparable2<Money>, Describable { // TWO interfaces implemented at once
    long cents;
    Money(long cents) { this.cents = cents; }

    @Override
    public int compareVal(Money other) { return Long.compare(this.cents, other.cents); }

    @Override
    public String describe() { return "$" + (cents / 100.0); }
}
```

`Money` lists both interfaces after `implements`, separated by a comma, and provides a `public` implementation for each interface's method — `compareVal` for `Comparable2<Money>` and `describe` for `Describable` — satisfying both contracts on one class simultaneously, with no ambiguity about which method belongs to which interface since their names and signatures differ.

## 4. Diagram

<svg viewBox="0 0 600 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A class declaration can combine at most one extends clause with any number of comma separated implements interfaces, extends always comes first">
  <rect x="8" y="8" width="584" height="154" rx="8" fill="#0d1117"/>

  <rect x="30" y="20" width="540" height="40" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="300" y="45" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="monospace">class Airplane extends Vehicle implements Flyable, Trackable {</text>

  <rect x="130" y="80" width="150" height="30" rx="6" fill="#1c2430" stroke="#f85149" stroke-width="1.5"/>
  <text x="205" y="100" fill="#f85149" font-size="9" text-anchor="middle" font-family="sans-serif">extends Vehicle (ONE class)</text>

  <rect x="310" y="80" width="260" height="30" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="440" y="100" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">implements Flyable, Trackable (any number)</text>

  <text x="300" y="140" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">extends must come first and allows only one class; implements follows and allows any number of interfaces.</text>
</svg>

`extends` (one class, if any) always precedes `implements` (any number of interfaces) in a class declaration.

## 5. Runnable example

Scenario: a delivery-tracking system where vehicles both extend a shared base class and implement interfaces for independent capabilities, evolved step by step to combine multiple interfaces on one class.

### Level 1 — Basic

```java
public class ImplementsBasic {
    interface Trackable {
        String getLocation();
    }

    static class Vehicle {
        String id;
        Vehicle(String id) { this.id = id; }
    }

    static class DeliveryTruck extends Vehicle implements Trackable {
        DeliveryTruck(String id) { super(id); }
        @Override
        public String getLocation() { return "Warehouse District"; }
    }

    public static void main(String[] args) {
        DeliveryTruck truck = new DeliveryTruck("T-100");
        System.out.println(truck.id + " is at " + truck.getLocation());
    }
}
```

**How to run:** `java ImplementsBasic.java`

`DeliveryTruck extends Vehicle implements Trackable` combines both mechanisms on one declaration: `id` is inherited from `Vehicle` (a real field, via class inheritance), and `getLocation()` fulfills the `Trackable` interface contract.

### Level 2 — Intermediate

Same delivery system, now with a second interface, `Chargeable`, implemented alongside `Trackable` on the same class — demonstrating multiple interfaces combined with a single superclass.

```java
public class ImplementsIntermediate {
    interface Trackable {
        String getLocation();
    }

    interface Chargeable {
        double chargeFee(double distanceKm);
    }

    static class Vehicle {
        String id;
        Vehicle(String id) { this.id = id; }
    }

    static class DeliveryTruck extends Vehicle implements Trackable, Chargeable {
        DeliveryTruck(String id) { super(id); }
        @Override
        public String getLocation() { return "Warehouse District"; }
        @Override
        public double chargeFee(double distanceKm) { return distanceKm * 1.5; } // flat per-km rate
    }

    public static void main(String[] args) {
        DeliveryTruck truck = new DeliveryTruck("T-100");
        System.out.println(truck.id + " at " + truck.getLocation());
        System.out.println("Fee for 40km: $" + truck.chargeFee(40));
    }
}
```

**How to run:** `java ImplementsIntermediate.java`

`implements Trackable, Chargeable` (comma-separated, after the single `extends Vehicle`) requires `DeliveryTruck` to implement both `getLocation()` and `chargeFee(double)`, which it does — a single class now satisfies three roles at once: it is-a `Vehicle`, can-be tracked, and can-be charged.

### Level 3 — Advanced

Same system, now with a second concrete vehicle type implementing only one of the two interfaces, and a processing routine that safely checks capabilities at runtime with `instanceof` — showing how `implements` enables genuinely mixed capability sets across a fleet.

```java
import java.util.List;

public class ImplementsAdvanced {
    interface Trackable {
        String getLocation();
    }

    interface Chargeable {
        double chargeFee(double distanceKm);
    }

    static class Vehicle {
        String id;
        Vehicle(String id) { this.id = id; }
    }

    static class DeliveryTruck extends Vehicle implements Trackable, Chargeable {
        DeliveryTruck(String id) { super(id); }
        @Override
        public String getLocation() { return "Warehouse District"; }
        @Override
        public double chargeFee(double distanceKm) { return distanceKm * 1.5; }
    }

    static class Bicycle extends Vehicle implements Trackable { // Trackable ONLY, no Chargeable
        Bicycle(String id) { super(id); }
        @Override
        public String getLocation() { return "Bike Lane 4"; }
    }

    public static void main(String[] args) {
        List<Vehicle> fleet = List.of(new DeliveryTruck("T-100"), new Bicycle("B-7"));

        for (Vehicle v : fleet) {
            StringBuilder report = new StringBuilder(v.id);
            if (v instanceof Trackable t) {
                report.append(" @ ").append(t.getLocation());
            }
            if (v instanceof Chargeable c) {
                report.append(" | fee for 40km: $").append(c.chargeFee(40));
            } else {
                report.append(" | not chargeable");
            }
            System.out.println(report);
        }
    }
}
```

**How to run:** `java ImplementsAdvanced.java`

`DeliveryTruck` satisfies both `Trackable` and `Chargeable`, while `Bicycle` satisfies only `Trackable` — the loop uses `instanceof` pattern matching to safely check each capability independently before using it, so mixing vehicles with different combinations of interfaces in the same `List<Vehicle>` works correctly without any type-specific branching logic.

## 6. Walkthrough

Trace the loop in `ImplementsAdvanced.main` for each vehicle in `fleet`.

**First iteration: `v` is `DeliveryTruck("T-100")`.** `report` starts as `"T-100"`. `v instanceof Trackable t` is `true` (`DeliveryTruck implements Trackable`), binding `t`; `t.getLocation()` dispatches to `DeliveryTruck.getLocation()`, returning `"Warehouse District"`, so `report` becomes `"T-100 @ Warehouse District"`. `v instanceof Chargeable c` is also `true` (`DeliveryTruck implements Chargeable` too), binding `c`; `c.chargeFee(40)` dispatches to `DeliveryTruck.chargeFee`, computing `40 * 1.5 = 60.0`, so `report` becomes `"T-100 @ Warehouse District | fee for 40km: $60.0"`.

**Second iteration: `v` is `Bicycle("B-7")`.** `report` starts as `"B-7"`. `v instanceof Trackable t` is `true` (`Bicycle implements Trackable`); `t.getLocation()` dispatches to `Bicycle.getLocation()`, returning `"Bike Lane 4"`, so `report` becomes `"B-7 @ Bike Lane 4"`. `v instanceof Chargeable c` is `false` (`Bicycle` never implements `Chargeable`), so the `else` branch runs, appending `" | not chargeable"` — `report` becomes `"B-7 @ Bike Lane 4 | not chargeable"`.

```
DeliveryTruck("T-100"):
  instanceof Trackable  -> true  -> getLocation() -> "Warehouse District"
  instanceof Chargeable -> true  -> chargeFee(40) -> 40*1.5 = 60.0
  report: "T-100 @ Warehouse District | fee for 40km: $60.0"

Bicycle("B-7"):
  instanceof Trackable  -> true  -> getLocation() -> "Bike Lane 4"
  instanceof Chargeable -> false -> "not chargeable"
  report: "B-7 @ Bike Lane 4 | not chargeable"
```

**Final output.**
```
T-100 @ Warehouse District | fee for 40km: $60.0
B-7 @ Bike Lane 4 | not chargeable
```

## 7. Gotchas & takeaways

> **`extends` must appear before `implements` in a class declaration, and only one class may follow `extends`, while any number of interfaces (comma-separated) may follow `implements`.** Writing `class X implements Flyable extends Vehicle` (reversed order) is a syntax error — the compiler requires the exact order `class X extends Y implements A, B, C`.

> **Every abstract method from every implemented interface must eventually have a concrete, `public` implementation somewhere in the class** — if a class implements multiple interfaces that happen to declare methods with the same name and signature, one implementation satisfies both; but if any interface method is left unimplemented, the class itself must be declared `abstract`, exactly as with abstract classes.

- `implements` connects a concrete class to one or more interface contracts; `extends` (at most one class) may appear before it in the same declaration.
- Multiple interfaces are separated by commas after `implements`, allowing one class to satisfy several independent capabilities at once.
- Every interface method needs a concrete `public` implementation in the class (or an inherited one), or the class must be declared `abstract`.
- Combining `extends` and `implements` is idiomatic: one class typically has a single core identity (via `extends`) plus any number of additional capabilities (via `implements`).
