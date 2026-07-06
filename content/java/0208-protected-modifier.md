---
card: java
gi: 208
slug: protected-modifier
title: protected modifier
---

## 1. What it is

The `protected` modifier grants access to a field, method, or constructor from three places: (1) any class in the **same package**, (2) any **subclass**, even one in a *different* package, and (3) of course the class itself. It sits between `public` (accessible everywhere) and the package-private default (accessible only within the same package) — specifically designed to let a class share implementation details with its subclasses without exposing them to the entire world.

```java
package com.example.animals;

public class Animal {
    protected String sound = "..."; // accessible: same package, OR any subclass anywhere

    protected void makeSound() {
        System.out.println(sound);
    }
}
```

```java
package com.example.farm; // a DIFFERENT package

public class Dog extends Animal { // subclass, in a different package
    void bark() {
        sound = "Woof"; // legal: protected members are accessible from subclasses, even across packages
        makeSound();
    }
}
```

`Dog`, despite living in an entirely different package (`com.example.farm` versus `Animal`'s `com.example.animals`), can still access `sound` and `makeSound()` because it's a *subclass* of `Animal` — this cross-package subclass access is the specific capability `protected` adds beyond package-private access.

## 2. Why & when

`protected` exists specifically for the needs of inheritance: giving subclasses access to implementation details their superclass wants to share with them, without exposing those same details to unrelated code:

- **Sharing state or behaviour with subclasses** — a base class might have fields or helper methods that only make sense for subclasses to use directly while extending or customizing behaviour, but that outside, unrelated code should never touch.
- **Framework and library design** — many frameworks expose `protected` methods specifically meant to be overridden or called by subclasses that extend the framework's base classes, while keeping those same methods invisible to code that merely *uses* the framework without extending it.
- **A middle ground, not a default** — `protected` is more permissive than package-private and less permissive than `public`; it should be chosen deliberately when subclass access (potentially across packages) is genuinely the intended use case, not as a vague "somewhat open" default.

You reach for `protected` specifically when designing a class meant to be extended, and some of its fields or methods are meant for subclasses' use during that extension — as opposed to genuinely private implementation details (which should stay `private`) or a fully public interface (which should be `public`).

## 3. Core concept

```java
class Shape {
    protected double area; // subclasses can access and set this directly

    protected void recalculate() { // subclasses can call, or override, this
        System.out.println("Recalculating area: " + area);
    }
}

class Circle extends Shape {
    double radius;

    Circle(double radius) {
        this.radius = radius;
        this.area = Math.PI * radius * radius; // accessing the protected field directly, from a subclass
        recalculate(); // calling the protected method, inherited from Shape
    }
}
```

`Circle`, as a subclass of `Shape`, can read and write `area` directly and call `recalculate()` — both are `protected` in `Shape`, granting exactly this subclass access, which would not be available to some unrelated class that merely held a `Shape` reference without extending it.

## 4. Diagram

<svg viewBox="0 0 600 160" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A protected field and method in a base class accessible from a subclass even in a different package, and from other classes in the same package, but not accessible from an unrelated class in a different package that does not extend the base class">
  <rect x="8" y="8" width="584" height="144" rx="8" fill="#0d1117"/>

  <rect x="230" y="20" width="160" height="45" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="310" y="42" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">protected area, recalculate()</text>
  <text x="310" y="57" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">in class Shape</text>

  <line x1="270" y1="65" x2="150" y2="105" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#pr)"/>
  <text x="120" y="120" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">subclass (any package): OK</text>

  <line x1="350" y1="65" x2="470" y2="105" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#pr)"/>
  <text x="500" y="120" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">same package: OK</text>

  <line x1="330" y1="65" x2="330" y2="105" stroke="#f85149" stroke-width="1.5" stroke-dasharray="3,2"/>
  <text x="330" y="120" fill="#f85149" font-size="9" text-anchor="middle" font-family="sans-serif">unrelated class, diff package: NO</text>

  <defs><marker id="pr" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker></defs>
</svg>

`protected` reaches subclasses (any package) and same-package classes, but not unrelated classes elsewhere.

## 5. Runnable example

Scenario: a small `Employee` base class meant to be extended by different employee types — starting with a basic protected field used by a subclass, then extending with a protected helper method subclasses can call, then hardening into a case where subclasses override a protected method to customize shared behaviour.

### Level 1 — Basic

```java
public class EmployeeBasic {
    static class Employee {
        protected double baseSalary;

        Employee(double baseSalary) {
            this.baseSalary = baseSalary;
        }
    }

    static class Manager extends Employee {
        Manager(double baseSalary) {
            super(baseSalary);
        }

        double totalCompensation() {
            return baseSalary + 5000; // accessing the protected field directly, inherited from Employee
        }
    }

    public static void main(String[] args) {
        Manager m = new Manager(60000);
        System.out.println("Total: $" + m.totalCompensation());
    }
}
```

**How to run:** `java EmployeeBasic.java`

`Manager.totalCompensation()` reads `baseSalary` directly, without needing any getter — this is legal specifically because `baseSalary` is `protected` in `Employee`, and `Manager` is a subclass of it.

### Level 2 — Intermediate

Same hierarchy, now with a `protected` helper method in `Employee` that subclasses call directly as part of their own logic.

```java
public class EmployeeIntermediate {
    static class Employee {
        protected double baseSalary;

        Employee(double baseSalary) {
            this.baseSalary = baseSalary;
        }

        protected double applyBonus(double percentage) {
            return baseSalary * (1 + percentage);
        }
    }

    static class Manager extends Employee {
        Manager(double baseSalary) {
            super(baseSalary);
        }

        double totalCompensation() {
            return applyBonus(0.10); // calling the protected method inherited from Employee
        }
    }

    public static void main(String[] args) {
        Manager m = new Manager(60000);
        System.out.println("Total: $" + m.totalCompensation());
    }
}
```

**How to run:** `java EmployeeIntermediate.java`

`Manager` calls `applyBonus(0.10)` directly, as if it were its own method — this works because `applyBonus` is `protected` in `Employee`, granting `Manager` (its subclass) the ability to call it exactly as though it were locally defined, despite actually being inherited.

### Level 3 — Advanced

Same hierarchy, now with a `protected` method that different subclasses **override** to customize how bonuses are calculated for their specific employee type, demonstrating `protected`'s role in supporting genuine customization through inheritance.

```java
public class EmployeeAdvanced {
    static class Employee {
        protected double baseSalary;

        Employee(double baseSalary) {
            this.baseSalary = baseSalary;
        }

        protected double bonusRate() { // meant to be overridden by subclasses
            return 0.05; // default bonus rate
        }

        double totalCompensation() {
            return baseSalary * (1 + bonusRate());
        }
    }

    static class Manager extends Employee {
        Manager(double baseSalary) { super(baseSalary); }

        @Override
        protected double bonusRate() { // customized for managers
            return 0.15;
        }
    }

    static class Intern extends Employee {
        Intern(double baseSalary) { super(baseSalary); }

        @Override
        protected double bonusRate() { // customized for interns
            return 0.0;
        }
    }

    public static void main(String[] args) {
        Employee[] staff = { new Employee(50000), new Manager(60000), new Intern(30000) };

        for (Employee e : staff) {
            System.out.println(e.getClass().getSimpleName() + ": $" + e.totalCompensation());
        }
    }
}
```

**How to run:** `java EmployeeAdvanced.java`

Each subclass overrides the `protected bonusRate()` method to supply its own rate, while `totalCompensation()` (defined once, in `Employee`) calls `bonusRate()` without knowing or caring which specific override actually runs — this is dynamic dispatch (covered fully in later inheritance topics), and `protected` is precisely what allows each subclass to participate in customizing this shared calculation.

## 6. Walkthrough

Trace the loop in `EmployeeAdvanced.main` for all three `staff` entries:

**Plain `Employee(50000)`.** `totalCompensation()` calls `bonusRate()` — since this object is a plain `Employee` (no override applies), the base `Employee.bonusRate()` runs, returning `0.05`. Result: `50000 * 1.05 = 52500.0`. Prints `"Employee: $52500.0"`.

**`Manager(60000)`.** `totalCompensation()` calls `bonusRate()` — since this object is actually a `Manager`, the overridden `Manager.bonusRate()` runs instead, returning `0.15`. Result: `60000 * 1.15 = 69000.0`. Prints `"Manager: $69000.0"`.

**`Intern(30000)`.** `totalCompensation()` calls `bonusRate()` — the overridden `Intern.bonusRate()` runs, returning `0.0`. Result: `30000 * 1.0 = 30000.0`. Prints `"Intern: $30000.0"`.

```
Employee(50000): bonusRate() = 0.05 (base)    -> 50000 * 1.05 = 52500.0
Manager(60000):  bonusRate() = 0.15 (override) -> 60000 * 1.15 = 69000.0
Intern(30000):   bonusRate() = 0.0  (override) -> 30000 * 1.0  = 30000.0
```

**Final output.** Three lines: `"Employee: $52500.0"`, `"Manager: $69000.0"`, `"Intern: $30000.0"` — each subclass's `protected` override of `bonusRate()` correctly customizes the shared `totalCompensation()` logic defined once in the base `Employee` class.

## 7. Gotchas & takeaways

> **`protected` access from a subclass in a *different* package only applies to accessing members through `this` or an inherited context — not through an arbitrary reference of the superclass type.** A `Manager` in a different package can access `this.baseSalary` (inherited), but cannot access `someOtherEmployee.baseSalary` for an arbitrary `Employee` reference that isn't `this` or a subclass instance being constructed — a subtle rule that trips up many Java learners.

> **Within the *same* package, `protected` behaves exactly like package-private access** — the cross-package subclass privilege is the only thing `protected` adds beyond package-private; if all your classes live in one package, `protected` and package-private are effectively equivalent in practice.

- `protected` grants access to the same package, any subclass (even across packages), and the class itself.
- It's the right choice specifically for fields or methods meant to support subclasses extending or customizing a class's behaviour.
- Subclasses can call or override `protected` methods and read or write `protected` fields as if they were their own, even across package boundaries.
- Cross-package `protected` access from a subclass is restricted to accessing inherited members through `this`, not through arbitrary superclass-typed references.
