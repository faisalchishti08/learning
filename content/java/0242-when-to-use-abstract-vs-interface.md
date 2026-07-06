---
card: java
gi: 242
slug: when-to-use-abstract-vs-interface
title: When to use abstract vs interface
---

## 1. What it is

Both abstract classes and interfaces (the next several topics cover interfaces in detail) let you define a contract that other types must fulfill, but they differ in a decisive way: a class can extend only *one* abstract (or any) class, but can implement *any number* of interfaces. Abstract classes can hold instance state (fields) and constructors; interfaces traditionally could not (though modern Java allows `default` and `static` methods on interfaces, covered shortly, they still cannot hold instance fields).

```java
abstract class Vehicle {       // single inheritance: a class can extend only ONE class
    int speed;                  // instance state — interfaces cannot have this
    abstract void move();
}

interface Chargeable {          // multiple interfaces can be implemented at once
    void charge();
}

interface Trackable {
    void reportLocation();
}

class ElectricCar extends Vehicle implements Chargeable, Trackable { // one class, multiple interfaces
    @Override void move() { speed = 60; }
    @Override public void charge() { System.out.println("Charging..."); }
    @Override public void reportLocation() { System.out.println("Location reported"); }
}
```

`ElectricCar` extends exactly one class (`Vehicle`, gaining its `speed` field and shared logic) but implements two interfaces (`Chargeable` and `Trackable`) simultaneously — this combination, one superclass plus multiple interfaces, is the standard shape most real Java class hierarchies take.

## 2. Why & when

Choosing between an abstract class and an interface (or a combination of both, as above) comes down to what you need to share and how many "kinds of thing" a class must simultaneously be.

- **Shared state and implementation** — if multiple subclasses need to share actual fields or non-trivial implemented methods (not just a method signature), an abstract class is the natural fit, since interfaces cannot hold instance fields at all.
- **Multiple, independent capabilities** — if a class needs to satisfy several unrelated contracts at once (say, being both `Comparable` and `Serializable`, plus an application-specific `Chargeable`), interfaces are the only option, since Java classes support only single inheritance of classes but unlimited implementation of interfaces.
- **"Is-a" versus "can-do"** — an abstract class typically models a strict "is-a" relationship within one conceptual family (an `ElectricCar` is-a `Vehicle`), while an interface typically models a "can-do" capability that unrelated classes might all share (a `Duck`, a `RemoteControl`, and a `Document` could all be `Comparable`, despite having nothing else in common).

Reach for an abstract class when you have a tight family of related types sharing real state and behaviour and only need single inheritance; reach for an interface (often several, on the same class) when you need to describe independent capabilities that many unrelated types might implement, or when you need something closer to multiple inheritance of behaviour.

## 3. Core concept

```java
abstract class Employee {           // shared STATE: name, hire date, common paycheck logic
    String name;
    Employee(String name) { this.name = name; }
    abstract double calculatePay();
}

interface Manager {                  // a CAPABILITY: not every Employee has direct reports
    void approveTimeOff(Employee e);
}

class TeamLead extends Employee implements Manager { // is-an Employee, AND can-do Manager duties
    TeamLead(String name) { super(name); }
    @Override double calculatePay() { return 8000; }
    @Override public void approveTimeOff(Employee e) {
        System.out.println(name + " approved time off for " + e.name);
    }
}
```

`TeamLead` is fundamentally an `Employee` (sharing `name` and the paycheck contract via the abstract class) but *also* has the `Manager` capability layered on top via an interface — a plain `Employee` who is not a lead simply would not implement `Manager` at all, showing how the two mechanisms combine to express both "what kind of thing this is" and "what it can additionally do."

## 4. Diagram

<svg viewBox="0 0 600 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Abstract class provides shared state and single inheritance, interfaces provide capabilities and can be implemented in any number, a class typically combines one abstract superclass with multiple interfaces">
  <rect x="8" y="8" width="584" height="174" rx="8" fill="#0d1117"/>

  <rect x="30" y="20" width="180" height="35" rx="6" fill="#1c2430" stroke="#f85149" stroke-width="1.5"/>
  <text x="120" y="42" fill="#f85149" font-size="9" text-anchor="middle" font-family="sans-serif">abstract class Employee</text>

  <rect x="230" y="20" width="160" height="35" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="310" y="42" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">interface Manager</text>

  <rect x="410" y="20" width="160" height="35" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="490" y="42" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">interface Trackable</text>

  <line x1="120" y1="55" x2="220" y2="100" stroke="#8b949e" stroke-width="1.5"/>
  <line x1="310" y1="55" x2="240" y2="100" stroke="#8b949e" stroke-width="1.5"/>
  <line x1="490" y1="55" x2="260" y2="100" stroke="#8b949e" stroke-width="1.5"/>

  <rect x="150" y="105" width="180" height="35" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="240" y="127" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">class TeamLead</text>

  <text x="300" y="165" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">One superclass (state + core identity) plus any number of interfaces (added capabilities).</text>
</svg>

A class extends at most one abstract (or other) class, but can implement any number of interfaces at once.

## 5. Runnable example

Scenario: a small HR system where employee types need shared state (via an abstract class) and optional capabilities (via interfaces), evolved from a single hierarchy into one combining both mechanisms deliberately.

### Level 1 — Basic

```java
public class AbstractVsInterfaceBasic {
    abstract static class Employee {
        String name;
        Employee(String name) { this.name = name; }
        abstract double calculatePay();
    }

    static class Developer extends Employee {
        Developer(String name) { super(name); }
        @Override double calculatePay() { return 7000; }
    }

    public static void main(String[] args) {
        Developer d = new Developer("Priya");
        System.out.println(d.name + ": $" + d.calculatePay());
    }
}
```

**How to run:** `java AbstractVsInterfaceBasic.java`

`Developer` extends the single abstract class `Employee`, inheriting shared state (`name`) and fulfilling the abstract contract (`calculatePay`) — a straightforward single-inheritance relationship.

### Level 2 — Intermediate

Same system, now adding an interface capability (`Manager`) that only *some* employees have, layered on top of the shared `Employee` abstract class — demonstrating the "is-a plus can-do" combination directly.

```java
import java.util.List;

public class AbstractVsInterfaceIntermediate {
    abstract static class Employee {
        String name;
        Employee(String name) { this.name = name; }
        abstract double calculatePay();
    }

    interface Manager {
        void approveTimeOff(Employee e);
    }

    static class Developer extends Employee {
        Developer(String name) { super(name); }
        @Override double calculatePay() { return 7000; }
    }

    static class TeamLead extends Employee implements Manager {
        TeamLead(String name) { super(name); }
        @Override double calculatePay() { return 8500; }
        @Override public void approveTimeOff(Employee e) {
            System.out.println(name + " approved time off for " + e.name);
        }
    }

    public static void main(String[] args) {
        Developer dev = new Developer("Priya");
        TeamLead lead = new TeamLead("Morgan");

        List<Employee> staff = List.of(dev, lead);
        for (Employee e : staff) {
            System.out.println(e.name + ": $" + e.calculatePay());
            if (e instanceof Manager m) {   // only some Employees are ALSO Managers
                m.approveTimeOff(dev);
            }
        }
    }
}
```

**How to run:** `java AbstractVsInterfaceIntermediate.java`

`dev instanceof Manager` is `false` (a plain `Developer` never implements `Manager`), while `lead instanceof Manager` is `true` — the `instanceof` pattern-matching check (introduced in modern Java) safely narrows the type and only calls `approveTimeOff` on employees that genuinely have that capability.

### Level 3 — Advanced

Same system, now with a second, independent interface (`Auditable`) demonstrating that a single class can implement multiple unrelated capabilities simultaneously — something impossible to express with abstract-class inheritance alone, since Java forbids extending more than one class.

```java
import java.util.List;

public class AbstractVsInterfaceAdvanced {
    abstract static class Employee {
        String name;
        Employee(String name) { this.name = name; }
        abstract double calculatePay();
    }

    interface Manager {
        void approveTimeOff(Employee e);
    }

    interface Auditable {
        String auditTrail();
    }

    static class Developer extends Employee {
        Developer(String name) { super(name); }
        @Override double calculatePay() { return 7000; }
    }

    // TeamLead implements BOTH interfaces at once -- impossible via class inheritance alone
    static class TeamLead extends Employee implements Manager, Auditable {
        TeamLead(String name) { super(name); }
        @Override double calculatePay() { return 8500; }
        @Override public void approveTimeOff(Employee e) {
            System.out.println(name + " approved time off for " + e.name);
        }
        @Override public String auditTrail() {
            return name + " has manager privileges — logged for compliance";
        }
    }

    public static void main(String[] args) {
        List<Employee> staff = List.of(new Developer("Priya"), new TeamLead("Morgan"));

        for (Employee e : staff) {
            System.out.println(e.name + ": $" + e.calculatePay());
            if (e instanceof Manager m) m.approveTimeOff(staff.get(0));
            if (e instanceof Auditable a) System.out.println(a.auditTrail());
        }
    }
}
```

**How to run:** `java AbstractVsInterfaceAdvanced.java`

`TeamLead` is simultaneously an `Employee` (single inheritance, shared state), a `Manager`, and `Auditable` (two independent interfaces) — expressing "is-a Employee, can-do Manager duties, can-do audit reporting" all on one class, something that would require awkward workarounds if Java only offered class inheritance with no interfaces at all.

## 6. Walkthrough

Trace the loop in `AbstractVsInterfaceAdvanced.main` for each staff member.

**First iteration: `e` is the `Developer("Priya")`.** `e.calculatePay()` dispatches to `Developer.calculatePay()`, returning `7000`; prints `"Priya: $7000.0"`. `e instanceof Manager` is `false` (`Developer` does not implement `Manager`), so the `approveTimeOff` branch is skipped. `e instanceof Auditable` is also `false`, so the audit branch is skipped too.

**Second iteration: `e` is the `TeamLead("Morgan")`.** `e.calculatePay()` dispatches to `TeamLead.calculatePay()`, returning `8500`; prints `"Morgan: $8500.0"`. `e instanceof Manager` is `true` (pattern matching binds `e` to `m` as a `Manager`), so `m.approveTimeOff(staff.get(0))` runs, calling `TeamLead.approveTimeOff` with `e` being `staff.get(0)`, the `Developer` "Priya" — this prints `"Morgan approved time off for Priya"`. `e instanceof Auditable` is `true` too, so `a.auditTrail()` runs, returning `"Morgan has manager privileges — logged for compliance"`, which is printed.

```
Developer("Priya"):
  calculatePay() -> 7000  -> "Priya: $7000.0"
  instanceof Manager?   -> false -> skip
  instanceof Auditable? -> false -> skip

TeamLead("Morgan"):
  calculatePay() -> 8500  -> "Morgan: $8500.0"
  instanceof Manager?   -> true  -> approveTimeOff(Priya) -> "Morgan approved time off for Priya"
  instanceof Auditable? -> true  -> auditTrail() -> "Morgan has manager privileges — logged for compliance"
```

**Final output.**
```
Priya: $7000.0
Morgan: $8500.0
Morgan approved time off for Priya
Morgan has manager privileges — logged for compliance
```

## 7. Gotchas & takeaways

> **A class can extend only one class (abstract or not), but can implement any number of interfaces** — this single-vs-multiple distinction is usually the deciding factor: if you find yourself wanting a class to inherit shared implementation from two unrelated "parent" types, an abstract class cannot do it, but restructuring one or both as interfaces (possibly with `default` methods, covered next) often can.

> **Needing shared instance state (actual fields, not just method contracts) is the strongest signal you need an abstract class, not just interfaces** — interfaces cannot declare instance fields at all (only `static final` constants), so any design requiring subclasses to share and mutate common state must involve an abstract class somewhere in the hierarchy.

- Abstract classes support single inheritance and can hold shared instance state and implemented methods; interfaces support multiple implementation but traditionally hold no instance state.
- Use an abstract class for a tight "is-a" family sharing real state and behaviour; use interfaces for independent "can-do" capabilities that unrelated classes might all share.
- A class combining one abstract superclass with several interfaces is a common, idiomatic pattern: one core identity, plus any number of additional capabilities.
- `instanceof` pattern matching lets code safely check for and use an optional interface capability without assuming every object in a shared collection has it.
