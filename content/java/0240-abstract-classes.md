---
card: java
gi: 240
slug: abstract-classes
title: Abstract classes
---

## 1. What it is

An `abstract` class is a class that cannot be instantiated directly with `new` — it exists only to be extended. It can mix fully implemented methods with `abstract` methods (declared with no body at all, just a signature ending in a semicolon), and any concrete (non-abstract) subclass must provide implementations for every inherited abstract method before it can be instantiated.

```java
abstract class Shape {
    abstract double area(); // no body — every concrete subclass MUST implement this

    void describe() { // ordinary, fully implemented method — inherited as-is
        System.out.println("This shape has area: " + area());
    }
}

class Circle extends Shape {
    double radius;
    Circle(double radius) { this.radius = radius; }

    @Override
    double area() { return Math.PI * radius * radius; } // required implementation
}

public class AbstractDemo {
    public static void main(String[] args) {
        // Shape s = new Shape(); // COMPILE ERROR if uncommented — cannot instantiate an abstract class
        Circle c = new Circle(2.0);
        c.describe(); // "This shape has area: 12.566..."
    }
}
```

`Shape` cannot be instantiated on its own (`new Shape()` is a compile error), but `Circle`, which supplies a concrete `area()`, can be — `describe()` is inherited unchanged from `Shape` and works correctly because it calls `area()` polymorphically, resolving at runtime to `Circle`'s implementation.

## 2. Why & when

Abstract classes exist to capture "this concept only makes sense in terms of its subclasses" while still sharing real, common code between them.

- **Modeling incomplete concepts** — "a shape" isn't a concrete thing you can draw or measure on its own; only specific shapes (circles, squares) are. An abstract class expresses that: it defines what every shape *must* provide (`area()`), without pretending "a generic shape" is something you should be able to create.
- **Sharing real implementation, not just a contract** — unlike an interface with only abstract methods (though interfaces can have default methods too, covered in dedicated topics), an abstract class can hold state (instance fields) and fully implemented methods that every subclass inherits for free, avoiding duplicated code across subclasses.
- **Forcing subclasses to fill in the specifics** — declaring a method `abstract` is a compile-time guarantee that every concrete subclass supplies its own meaningful implementation; forgetting to override it is a compile error, not a runtime surprise.

Reach for an abstract class when you have a family of related types that share common state or behaviour, but where each concrete type must supply its own version of one or more operations — and where you also want the flexibility of instance fields and constructors, which plain interfaces traditionally do not provide as directly.

## 3. Core concept

```java
abstract class Employee {
    String name;
    Employee(String name) { this.name = name; } // abstract classes CAN have constructors

    abstract double calculatePay(); // must be implemented by every concrete subclass

    void printPaycheck() { // shared, concrete behaviour, inherited by all subclasses
        System.out.println(name + "'s pay: $" + calculatePay());
    }
}

class SalariedEmployee extends Employee {
    double annualSalary;
    SalariedEmployee(String name, double annualSalary) {
        super(name); // abstract class constructors ARE called via super(), just like any other superclass
        this.annualSalary = annualSalary;
    }

    @Override
    double calculatePay() { return annualSalary / 12; }
}
```

`Employee`'s constructor runs via `super(name)` even though `Employee` itself can never be instantiated directly — a constructor's job is to initialize the *portion* of the object it's responsible for, and that still happens even when the class as a whole is abstract; `printPaycheck()` calls `calculatePay()` polymorphically, so it works correctly for any concrete subclass without needing to know which one.

## 4. Diagram

<svg viewBox="0 0 600 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="An abstract Employee class defines an abstract calculatePay method with no body and a concrete printPaycheck method, two concrete subclasses each supply their own calculatePay implementation">
  <rect x="8" y="8" width="584" height="184" rx="8" fill="#0d1117"/>

  <rect x="190" y="20" width="220" height="60" rx="6" fill="#1c2430" stroke="#f85149" stroke-width="2"/>
  <text x="300" y="38" fill="#f85149" font-size="10" text-anchor="middle" font-family="sans-serif">abstract class Employee</text>
  <text x="300" y="54" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">abstract calculatePay() — no body</text>
  <text x="300" y="68" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">printPaycheck() — concrete, shared</text>

  <line x1="220" y1="80" x2="130" y2="115" stroke="#8b949e" stroke-width="1.5"/>
  <line x1="380" y1="80" x2="470" y2="115" stroke="#8b949e" stroke-width="1.5"/>

  <rect x="40" y="120" width="180" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="130" y="138" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">SalariedEmployee</text>
  <text x="130" y="152" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">implements calculatePay()</text>

  <rect x="380" y="120" width="180" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="470" y="138" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">HourlyEmployee</text>
  <text x="470" y="152" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">implements calculatePay()</text>

  <text x="300" y="185" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Only the concrete subclasses (blue) can be instantiated — Employee itself (red) never can.</text>
</svg>

An abstract superclass provides shared, concrete behaviour and defines a contract; only its concrete subclasses can be instantiated.

## 5. Runnable example

Scenario: a payroll system with different employee pay types, evolved from a basic abstract class into a working polymorphic paycheck printer, then hardened with validation and a case showing exactly why forgetting an abstract method is caught at compile time.

### Level 1 — Basic

```java
public class AbstractBasic {
    abstract static class Employee {
        String name;
        Employee(String name) { this.name = name; }
        abstract double calculatePay();
    }

    static class SalariedEmployee extends Employee {
        double annualSalary;
        SalariedEmployee(String name, double annualSalary) {
            super(name);
            this.annualSalary = annualSalary;
        }
        @Override
        double calculatePay() { return annualSalary / 12; }
    }

    public static void main(String[] args) {
        SalariedEmployee e = new SalariedEmployee("Alex", 60000);
        System.out.println(e.name + ": $" + e.calculatePay()); // Alex: $5000.0
    }
}
```

**How to run:** `java AbstractBasic.java`

`SalariedEmployee` supplies a concrete `calculatePay()`, satisfying `Employee`'s requirement, so it can be instantiated with `new` even though `Employee` itself cannot.

### Level 2 — Intermediate

Same payroll system, now with a second concrete subclass and a shared, concrete `printPaycheck()` method on `Employee` used polymorphically across a list of mixed employee types.

```java
import java.util.List;

public class AbstractIntermediate {
    abstract static class Employee {
        String name;
        Employee(String name) { this.name = name; }
        abstract double calculatePay();

        void printPaycheck() { // shared, concrete — inherited by every subclass
            System.out.println(name + "'s pay: $" + calculatePay());
        }
    }

    static class SalariedEmployee extends Employee {
        double annualSalary;
        SalariedEmployee(String name, double annualSalary) { super(name); this.annualSalary = annualSalary; }
        @Override
        double calculatePay() { return annualSalary / 12; }
    }

    static class HourlyEmployee extends Employee {
        double hourlyRate;
        int hoursWorked;
        HourlyEmployee(String name, double hourlyRate, int hoursWorked) {
            super(name);
            this.hourlyRate = hourlyRate;
            this.hoursWorked = hoursWorked;
        }
        @Override
        double calculatePay() { return hourlyRate * hoursWorked; }
    }

    public static void main(String[] args) {
        List<Employee> staff = List.of(
            new SalariedEmployee("Alex", 60000),
            new HourlyEmployee("Sam", 25.0, 160)
        );

        for (Employee e : staff) {
            e.printPaycheck(); // resolves calculatePay() polymorphically per actual subclass
        }
    }
}
```

**How to run:** `java AbstractIntermediate.java`

`staff` holds a mix of `SalariedEmployee` and `HourlyEmployee` objects, both treated uniformly as `Employee`; calling `printPaycheck()` on each runs `Employee`'s one shared implementation, but the `calculatePay()` call inside it resolves, via dynamic dispatch, to whichever concrete subclass's version matches the object's actual runtime type.

### Level 3 — Advanced

Same payroll system, now with input validation inside the abstract class's constructor (shared by every subclass automatically) and a `ContractEmployee` subclass demonstrating that forgetting to implement an abstract method is caught at compile time, not runtime.

```java
import java.util.List;

public class AbstractAdvanced {
    abstract static class Employee {
        String name;

        Employee(String name) {
            if (name == null || name.isBlank()) {
                throw new IllegalArgumentException("name must not be blank"); // shared validation, every subclass benefits
            }
            this.name = name;
        }

        abstract double calculatePay();

        void printPaycheck() {
            double pay = calculatePay();
            if (pay < 0) {
                throw new IllegalStateException(name + " has negative pay: " + pay); // shared safety check
            }
            System.out.println(name + "'s pay: $" + String.format("%.2f", pay));
        }
    }

    static class SalariedEmployee extends Employee {
        double annualSalary;
        SalariedEmployee(String name, double annualSalary) { super(name); this.annualSalary = annualSalary; }
        @Override
        double calculatePay() { return annualSalary / 12; }
    }

    static class HourlyEmployee extends Employee {
        double hourlyRate;
        int hoursWorked;
        HourlyEmployee(String name, double hourlyRate, int hoursWorked) {
            super(name);
            this.hourlyRate = hourlyRate;
            this.hoursWorked = hoursWorked;
        }
        @Override
        double calculatePay() { return hourlyRate * hoursWorked; }
    }

    // Uncommenting this WITHOUT overriding calculatePay() is a COMPILE ERROR:
    // static class BrokenEmployee extends Employee {
    //     BrokenEmployee(String name) { super(name); }
    //     // missing calculatePay() override -> "BrokenEmployee is not abstract and does not override
    //     // abstract method calculatePay() in Employee"
    // }

    public static void main(String[] args) {
        List<Employee> staff = List.of(
            new SalariedEmployee("Alex", 60000),
            new HourlyEmployee("Sam", 25.0, 160)
        );

        for (Employee e : staff) {
            e.printPaycheck();
        }

        try {
            new SalariedEmployee("", 50000); // triggers the shared constructor validation
        } catch (IllegalArgumentException ex) {
            System.out.println("Caught: " + ex.getMessage());
        }
    }
}
```

**How to run:** `java AbstractAdvanced.java`

The commented-out `BrokenEmployee` class illustrates a real compiler guarantee: any concrete (non-abstract) subclass of `Employee` that fails to override `calculatePay()` fails to compile, with a message naming exactly which abstract method is missing — this is checked before the program ever runs, unlike a runtime `NullPointerException` or similar that would only surface when that specific code path executed.

## 6. Walkthrough

Trace `main` in `AbstractAdvanced` from the first loop iteration through the final `catch` block.

**Building `staff`.** `new SalariedEmployee("Alex", 60000)` calls `super("Alex")`, running `Employee`'s constructor: `"Alex".isBlank()` is `false`, so validation passes, and `name` is set. Then `annualSalary` is set to `60000`. Similarly, `new HourlyEmployee("Sam", 25.0, 160)` validates `"Sam"` successfully and sets its own fields.

**First loop iteration: `staff.get(0).printPaycheck()`.** The actual object is a `SalariedEmployee`. `printPaycheck()` (defined once, on `Employee`, inherited unchanged) calls `calculatePay()` — dynamic dispatch resolves this to `SalariedEmployee.calculatePay()`, returning `60000 / 12 = 5000.0`. Back in `printPaycheck()`, `pay < 0` is `false`, so the safety check passes, and it prints `"Alex's pay: $5000.00"` (formatted to two decimal places).

**Second loop iteration: `staff.get(1).printPaycheck()`.** The actual object is `HourlyEmployee`. `calculatePay()` resolves to `HourlyEmployee.calculatePay()`, returning `25.0 * 160 = 4000.0`. `printPaycheck()` prints `"Sam's pay: $4000.00"`.

**`new SalariedEmployee("", 50000)`.** `super("")` runs `Employee`'s constructor: `"".isBlank()` is `true`, so the validation condition `name == null || name.isBlank()` is `true`, and `IllegalArgumentException("name must not be blank")` is thrown immediately — the `SalariedEmployee` object is never fully constructed, and `annualSalary` is never even assigned.

**The `catch` block.** Catches the `IllegalArgumentException`, reads its message via `ex.getMessage()`, and prints `"Caught: name must not be blank"`.

```
new SalariedEmployee("Alex", 60000) -> Employee(name) validates "Alex" OK -> annualSalary=60000
new HourlyEmployee("Sam", 25.0, 160) -> Employee(name) validates "Sam" OK -> hourlyRate=25.0, hoursWorked=160

staff[0].printPaycheck() -> calculatePay() dispatches to SalariedEmployee -> 60000/12=5000.0 -> prints "$5000.00"
staff[1].printPaycheck() -> calculatePay() dispatches to HourlyEmployee   -> 25.0*160=4000.0 -> prints "$4000.00"

new SalariedEmployee("", 50000) -> Employee(name) validates "" -> isBlank() true -> throws IllegalArgumentException
  -> caught -> prints "Caught: name must not be blank"
```

**Final output.**
```
Alex's pay: $5000.00
Sam's pay: $4000.00
Caught: name must not be blank
```

## 7. Gotchas & takeaways

> **An abstract class's constructor still runs, even though the class itself can never be instantiated directly** — every concrete subclass's constructor must call it (explicitly via `super(...)`, or implicitly if a no-argument version exists), and any validation or field initialization inside it applies to every subclass automatically, exactly as `Employee`'s blank-name check did for both `SalariedEmployee` and `HourlyEmployee`.

> **Forgetting to implement an abstract method is a compile-time error, not a runtime one** — this is one of the strongest practical reasons to prefer an abstract class (or interface) with abstract methods over, say, a base class with methods that just do nothing or return a stub value: the compiler actively prevents you from shipping an incomplete subclass, rather than letting a missing implementation surface as a bug much later.

- An `abstract` class cannot be instantiated with `new`; only its concrete (fully-implementing) subclasses can be.
- It can freely mix `abstract` methods (no body, must be overridden) with ordinary, fully implemented methods that every subclass inherits and shares.
- Abstract classes can have constructors, instance fields, and validation logic, all of which run for every subclass via `super(...)`.
- A concrete subclass that fails to override even one inherited abstract method fails to compile, catching incomplete implementations before the program ever runs.
