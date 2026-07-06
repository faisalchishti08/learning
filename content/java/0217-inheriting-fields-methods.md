---
card: java
gi: 217
slug: inheriting-fields-methods
title: Inheriting fields & methods
---

## 1. What it is

When a class `extends` another, it automatically inherits every field and method from its superclass that isn't `private` — this happens without the subclass writing any code to "ask for" that inheritance; the members simply become part of the subclass, usable exactly as if they'd been declared there directly. Access modifiers determine which inherited members a subclass can actually see and use: `public` and `protected` members are always inherited and accessible; package-private members are inherited only if the subclass is in the same package; `private` members are technically part of the object's memory layout but are completely inaccessible to the subclass's own code.

```java
class Animal {
    public String name;
    protected int age;
    String species; // package-private
    private String secretId; // private — NOT accessible from Dog, even though Dog IS an Animal

    void breathe() {
        System.out.println(name + " is breathing");
    }
}

class Dog extends Animal {
    void describe() {
        System.out.println(name + ", age " + age + ", species " + species); // all accessible
        // System.out.println(secretId); // COMPILE ERROR — private, not accessible even from a subclass
    }
}
```

`Dog` can freely use `name`, `age`, and `species` (assuming same-package access for the package-private `species`), and can call `breathe()` — all inherited automatically — but `secretId` remains completely off-limits to `Dog`'s own code, since `private` access is restricted to the exact declaring class, with no exception for subclasses.

## 2. Why & when

Automatic inheritance of accessible members is the mechanism that makes the "is-a" relationship (established by `extends`, covered in the previous topic) actually useful in practice:

- **Immediate reuse with zero extra code** — a subclass gets everything its superclass offers (that it's permitted to see) the instant it's declared, with no explicit "import" or copying step required.
- **Consistent behaviour across the hierarchy** — every subclass automatically shares the superclass's fields and methods, ensuring related classes behave consistently for whatever they don't specifically choose to override or add.
- **Understanding what's actually inherited versus hidden** — knowing precisely which members a subclass can and cannot see (based on access modifiers) is essential to correctly predicting what code in a subclass can and cannot do.

You rely on this automatic inheritance whenever designing a class hierarchy — deliberately choosing each member's access level (`public`, `protected`, package-private, or `private`) based on exactly how much of it should be visible and usable by subclasses versus kept as a truly internal implementation detail.

## 3. Core concept

```java
class Employee {
    protected String name;
    protected double baseSalary;

    Employee(String name, double baseSalary) {
        this.name = name;
        this.baseSalary = baseSalary;
    }

    double calculatePay() {
        return baseSalary;
    }
}

class Manager extends Employee {
    Manager(String name, double baseSalary) {
        super(name, baseSalary);
    }
    // Manager inherits calculatePay() AS-IS, without redefining it
}

Manager m = new Manager("Ann", 5000);
System.out.println(m.calculatePay()); // 5000.0 — inherited, unmodified
System.out.println(m.name);            // Ann — inherited field, directly accessible (protected)
```

`Manager` never defines its own `calculatePay()` — it simply inherits `Employee`'s version unchanged, and calling `m.calculatePay()` runs exactly that inherited implementation; this demonstrates that a subclass isn't *required* to override anything it inherits — inheriting as-is is a perfectly normal, common outcome.

## 4. Diagram

<svg viewBox="0 0 600 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="An Employee superclass with public protected package private and private members, and a Manager subclass showing which of those members it can actually see and use, with private specifically blocked off even though Manager extends Employee">
  <rect x="8" y="8" width="584" height="154" rx="8" fill="#0d1117"/>

  <rect x="30" y="20" width="220" height="120" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="140" y="40" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">class Employee</text>
  <text x="140" y="60" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="monospace">protected name ✓</text>
  <text x="140" y="78" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="monospace">protected baseSalary ✓</text>
  <text x="140" y="96" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="monospace">calculatePay() ✓</text>
  <text x="140" y="114" fill="#f85149" font-size="9" text-anchor="middle" font-family="monospace">private secretId ✗</text>

  <line x1="250" y1="80" x2="330" y2="80" stroke="#8b949e" stroke-width="1.5" marker-end="url(#ih)"/>
  <text x="290" y="70" fill="#8b949e" font-size="9" font-family="sans-serif">extends</text>

  <rect x="340" y="45" width="220" height="70" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="450" y="65" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">class Manager</text>
  <text x="450" y="85" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">sees name, baseSalary,</text>
  <text x="450" y="100" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">calculatePay() — NOT secretId</text>

  <defs><marker id="ih" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

A subclass automatically inherits every non-private member; `private` members remain invisible even across the `extends` relationship.

## 5. Runnable example

Scenario: a small vehicle rental system — starting with basic field and method inheritance, then extending with a subclass that adds new behaviour while still using inherited members, then hardening into a case demonstrating precisely which members are and aren't reachable across an inheritance boundary.

### Level 1 — Basic

```java
public class RentalBasic {
    static class Vehicle {
        protected String licensePlate;
        protected double dailyRate;

        Vehicle(String licensePlate, double dailyRate) {
            this.licensePlate = licensePlate;
            this.dailyRate = dailyRate;
        }

        double costForDays(int days) {
            return dailyRate * days;
        }
    }

    static class Car extends Vehicle {
        Car(String licensePlate, double dailyRate) {
            super(licensePlate, dailyRate);
        }
    }

    public static void main(String[] args) {
        Car c = new Car("ABC-123", 45.0);
        System.out.println(c.licensePlate + ": $" + c.costForDays(3)); // inherited field and method
    }
}
```

**How to run:** `java RentalBasic.java`

`Car` inherits `licensePlate`, `dailyRate`, and `costForDays(int)` entirely unchanged from `Vehicle` — it adds nothing new here, demonstrating the simplest form of inheritance: full reuse, with the subclass existing mainly to establish the "is-a" relationship and its own constructor.

### Level 2 — Intermediate

Same rental system, now with `Car` adding a genuinely new field and method, while still freely using the inherited `costForDays`.

```java
public class RentalIntermediate {
    static class Vehicle {
        protected String licensePlate;
        protected double dailyRate;

        Vehicle(String licensePlate, double dailyRate) {
            this.licensePlate = licensePlate;
            this.dailyRate = dailyRate;
        }

        double costForDays(int days) {
            return dailyRate * days;
        }
    }

    static class Car extends Vehicle {
        int numberOfSeats; // new field

        Car(String licensePlate, double dailyRate, int numberOfSeats) {
            super(licensePlate, dailyRate);
            this.numberOfSeats = numberOfSeats;
        }

        double costForDaysWithInsurance(int days) { // new method, uses the INHERITED method internally
            return costForDays(days) + (days * 10.0); // $10/day insurance surcharge
        }
    }

    public static void main(String[] args) {
        Car c = new Car("ABC-123", 45.0, 5);
        System.out.println("Base cost: $" + c.costForDays(3));
        System.out.println("With insurance: $" + c.costForDaysWithInsurance(3));
    }
}
```

**How to run:** `java RentalIntermediate.java`

`costForDaysWithInsurance` calls the inherited `costForDays(days)` directly, as though it were `Car`'s own method — this is exactly how inherited methods are meant to be used: as building blocks a subclass can freely combine with its own new logic.

### Level 3 — Advanced

Same rental system, now with a `private` field in `Vehicle` demonstrating concretely that even a direct subclass cannot access it, requiring an inherited method as the only path to that data.

```java
public class RentalAdvanced {
    static class Vehicle {
        protected String licensePlate;
        protected double dailyRate;
        private String internalTrackingId; // private — NOT accessible from Car, even though Car extends Vehicle

        Vehicle(String licensePlate, double dailyRate, String internalTrackingId) {
            this.licensePlate = licensePlate;
            this.dailyRate = dailyRate;
            this.internalTrackingId = internalTrackingId;
        }

        double costForDays(int days) {
            return dailyRate * days;
        }

        String getTrackingId() { // the ONLY way Car (or anyone else) can reach internalTrackingId
            return internalTrackingId;
        }
    }

    static class Car extends Vehicle {
        int numberOfSeats;

        Car(String licensePlate, double dailyRate, int numberOfSeats, String internalTrackingId) {
            super(licensePlate, dailyRate, internalTrackingId);
            this.numberOfSeats = numberOfSeats;
        }

        void printFullDetails() {
            System.out.println(licensePlate + ", seats=" + numberOfSeats);
            System.out.println("Tracking: " + getTrackingId()); // must go through the inherited getter
            // System.out.println(internalTrackingId); // would NOT compile — private, invisible to Car
        }
    }

    public static void main(String[] args) {
        Car c = new Car("ABC-123", 45.0, 5, "TRACK-9981");
        c.printFullDetails();
    }
}
```

**How to run:** `java RentalAdvanced.java`

`Car.printFullDetails()` can read `licensePlate` and `numberOfSeats` directly, but must go through the inherited `getTrackingId()` method to reach `internalTrackingId` — direct access (`internalTrackingId`, uncommented) would fail to compile, since `private` fields are invisible to subclasses regardless of the "is-a" relationship `extends` establishes.

## 6. Walkthrough

Trace `c.printFullDetails()` from `RentalAdvanced.main`, where `c = new Car("ABC-123", 45.0, 5, "TRACK-9981")`:

**Construction.** `Car`'s constructor calls `super(licensePlate, dailyRate, internalTrackingId)`, running `Vehicle`'s constructor: `this.licensePlate = "ABC-123"`, `this.dailyRate = 45.0`, `this.internalTrackingId = "TRACK-9981"` (this last one, `private`, only settable from within `Vehicle`'s own constructor code). Back in `Car`'s constructor: `this.numberOfSeats = 5`.

**First print.** `licensePlate + ", seats=" + numberOfSeats` reads both directly — `licensePlate` is `protected` (inherited, visible), `numberOfSeats` is `Car`'s own field. Prints `"ABC-123, seats=5"`.

**Second print.** `getTrackingId()` is called — this method is defined in `Vehicle`, inherited by `Car`. *Inside* `getTrackingId()`'s body (which executes as part of `Vehicle`'s own code), `internalTrackingId` is fully accessible, since the method itself belongs to the class that declared the private field. It returns `"TRACK-9981"`. Back in `Car`, this returned value is printed: `"Tracking: TRACK-9981"`.

```
construction: licensePlate="ABC-123", dailyRate=45.0, internalTrackingId="TRACK-9981" (private), numberOfSeats=5

printFullDetails():
  licensePlate, numberOfSeats -> read directly (protected/own field) -> "ABC-123, seats=5"
  getTrackingId() -> runs INSIDE Vehicle's own code, which CAN see internalTrackingId -> returns "TRACK-9981"
  -> "Tracking: TRACK-9981"
```

**Final output.** `"ABC-123, seats=5"` then `"Tracking: TRACK-9981"` — `Car` never touches `internalTrackingId` directly anywhere in its own code; it only ever sees the *result* of calling the inherited getter, which is the only sanctioned path to that private data.

## 7. Gotchas & takeaways

> **A `private` field is technically still part of every subclass instance's memory (it was set by the superclass's constructor, and exists in every object), but it is completely inaccessible to the subclass's own code, by name, anywhere.** The only way a subclass can interact with such a field is indirectly, through an inherited non-private method (like `getTrackingId()`) that the superclass chose to expose.

> **"Inheriting a method" doesn't mean the subclass must do anything with it — using an inherited member exactly as-is (as `Vehicle`'s `costForDays` is used unchanged by `Car` in the basic example) is a completely normal, common outcome**, not something that needs to be explicitly declared or repeated in the subclass's own code.

- A subclass automatically inherits every `public`, `protected`, and (same-package) package-private member from its superclass — no extra code is needed to gain this access.
- `private` members are never directly accessible from a subclass, even though the "is-a" relationship holds — only inherited non-private methods can indirectly expose their effects.
- An inherited method can be used as-is, without being overridden, and can also be called from within the subclass's own new methods as a building block.
- Carefully choosing each member's access level when designing a superclass directly determines what its future subclasses will and won't be able to use.
