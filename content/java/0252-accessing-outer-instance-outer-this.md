---
card: java
gi: 252
slug: accessing-outer-instance-outer-this
title: Accessing outer instance (Outer.this)
---

## 1. What it is

`Outer.this` is the explicit syntax an inner class uses to refer to the specific enclosing instance it is bound to, where `Outer` is the enclosing class's name. It is needed whenever an inner class must unambiguously reach the enclosing instance itself (not just one of its members) — for example, to pass that enclosing instance as an argument, or to access an enclosing member that the inner class's own member shadows (as the previous topic demonstrated).

```java
class Building {
    String address;
    Building(String address) { this.address = address; }

    class Room {
        String name;
        Room(String name) { this.name = name; }

        Building getBuilding() {
            return Building.this; // the specific Building instance this Room belongs to
        }
    }
}

public class OuterThisDemo {
    public static void main(String[] args) {
        Building building = new Building("123 Main St");
        Building.Room room = building.new Room("Lobby");

        System.out.println(room.getBuilding() == building); // true — same object
        System.out.println(room.getBuilding().address);       // "123 Main St"
    }
}
```

`Building.this` inside `Room` refers to the exact `Building` instance that created this particular `Room` — `room.getBuilding() == building` confirms it is genuinely the *same object*, not a copy or a new instance, demonstrating that every inner class instance carries a real, retrievable reference to its enclosing instance.

## 2. Why & when

`Outer.this` becomes necessary specifically in situations where an unqualified reference would be ambiguous or where the enclosing instance itself (not just one of its fields) needs to be obtained.

- **Disambiguating shadowed names** — as the previous topic showed, when an inner class field or parameter shares a name with an enclosing field, unqualified references resolve to the closest scope (the inner class's own); `Outer.this.fieldName` is required to reach the enclosing version explicitly.
- **Passing the enclosing instance itself somewhere** — code outside the inner class sometimes needs the actual enclosing object, not just data derived from it (for example, registering the enclosing instance as a listener, or returning it from a getter, as `getBuilding()` does above).
- **Working with multiple levels of nesting** — if an inner class is itself nested inside another inner class, `Outer.this` (using the specific enclosing class's name at whichever level is needed) lets code reach exactly the right level of enclosing instance, skipping past intermediate levels if necessary.

Use `Outer.this` whenever an unqualified reference inside an inner class would either be ambiguous (due to shadowing) or when you need the enclosing instance itself, as an object, rather than just one of its members — for the common case with no naming conflicts and no need for the instance itself, plain unqualified access to enclosing members remains simpler and is entirely sufficient.

## 3. Core concept

```java
class Company {
    String name;
    Company(String name) { this.name = name; }

    class Employee {
        String name; // SHADOWS Company.name
        Employee(String name) { this.name = name; }

        void printBoth() {
            System.out.println("Employee name: " + this.name);              // this: the Employee itself
            System.out.println("Company name: " + Company.this.name);        // Company.this: the enclosing Company
        }
    }
}
```

Both `Employee` and `Company` have a field called `name`; inside `Employee`, `this.name` (or plain `name`) refers to the `Employee`'s own field, while `Company.this.name` explicitly reaches past that shadowing to the enclosing `Company` instance's `name` — the two are entirely distinct fields on two entirely distinct objects, disambiguated purely by which qualifier is used.

## 4. Diagram

<svg viewBox="0 0 600 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Inside an inner class, plain this refers to the inner instance itself, while Outer dot this explicitly refers to the specific enclosing instance, resolving any ambiguity between shadowed members">
  <rect x="8" y="8" width="584" height="154" rx="8" fill="#0d1117"/>

  <rect x="60" y="30" width="200" height="45" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="160" y="50" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">Company instance</text>
  <text x="160" y="66" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">name = "Acme"</text>

  <rect x="340" y="30" width="200" height="45" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="440" y="50" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">Employee instance</text>
  <text x="440" y="66" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">name = "Alex"</text>

  <line x1="260" y1="52" x2="340" y2="52" stroke="#8b949e" stroke-width="1.5"/>

  <rect x="130" y="100" width="150" height="30" rx="6" fill="#1c2430" stroke="#f85149" stroke-width="1.5"/>
  <text x="205" y="120" fill="#f85149" font-size="9" text-anchor="middle" font-family="monospace">this.name -&gt; "Alex"</text>

  <rect x="320" y="100" width="220" height="30" rx="6" fill="#1c2430" stroke="#f85149" stroke-width="1.5"/>
  <text x="430" y="120" fill="#f85149" font-size="9" text-anchor="middle" font-family="monospace">Company.this.name -&gt; "Acme"</text>

  <text x="300" y="150" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Same field name, two different objects — the qualifier picks which one you mean.</text>
</svg>

`this` refers to the inner instance itself; `Outer.this` explicitly refers to the enclosing instance.

## 5. Runnable example

Scenario: an organizational structure where departments contain employees, evolved from simple outer-instance retrieval into a working shadowed-name disambiguation, then hardened into a case using `Outer.this` to register the enclosing instance with an external collection.

### Level 1 — Basic

```java
public class OuterThisBasic {
    static class Department {
        String name;
        Department(String name) { this.name = name; }

        class Employee {
            Department getDepartment() {
                return Department.this; // the specific Department this Employee belongs to
            }
        }
    }

    public static void main(String[] args) {
        Department dept = new Department("Engineering");
        Department.Employee emp = dept.new Employee();

        System.out.println(emp.getDepartment() == dept);        // true
        System.out.println(emp.getDepartment().name);            // "Engineering"
    }
}
```

**How to run:** `java OuterThisBasic.java`

`Department.this` inside `Employee` unambiguously returns the exact `Department` instance that created this `Employee`, confirmed by the reference equality check `emp.getDepartment() == dept`.

### Level 2 — Intermediate

Same structure, now with a shadowed field name (`name` exists on both `Department` and `Employee`), demonstrating exactly how `Outer.this` resolves the ambiguity that an unqualified reference cannot.

```java
public class OuterThisIntermediate {
    static class Department {
        String name;
        Department(String name) { this.name = name; }

        class Employee {
            String name; // shadows Department.name
            Employee(String name) { this.name = name; }

            void printBoth() {
                System.out.println("Employee: " + this.name);
                System.out.println("Department: " + Department.this.name);
            }
        }
    }

    public static void main(String[] args) {
        Department dept = new Department("Engineering");
        Department.Employee emp = dept.new Employee("Priya");
        emp.printBoth();
    }
}
```

**How to run:** `java OuterThisIntermediate.java`

`this.name` inside `printBoth` resolves to `Employee`'s own field (`"Priya"`), while `Department.this.name` reaches past the shadowing entirely to `Department`'s field (`"Engineering"`) — without the explicit `Department.this` qualifier, there would be no way to access the enclosing `name` from inside `Employee` at all, since the unqualified name always resolves to the nearest enclosing scope.

### Level 3 — Advanced

Same organizational structure, now with `Employee` registering the enclosing `Department` instance (via `Department.this`) as a listener in an external notification system — demonstrating a realistic case where the enclosing instance itself, not just one of its fields, must be passed elsewhere.

```java
import java.util.ArrayList;
import java.util.List;

public class OuterThisAdvanced {
    interface Notifiable {
        void notify(String message);
    }

    static class Department implements Notifiable {
        String name;
        List<String> notifications = new ArrayList<>();

        Department(String name) { this.name = name; }

        @Override
        public void notify(String message) {
            notifications.add(message);
            System.out.println(name + " received: " + message);
        }

        class Employee {
            String name;
            NotificationHub hub;

            Employee(String name, NotificationHub hub) {
                this.name = name;
                this.hub = hub;
                hub.register(Department.this); // passes the ENCLOSING Department instance itself, not just its name
            }

            void raiseAlert(String message) {
                hub.broadcast(this.name + ": " + message);
            }
        }
    }

    static class NotificationHub {
        List<Notifiable> subscribers = new ArrayList<>();
        void register(Notifiable n) { subscribers.add(n); }
        void broadcast(String message) {
            for (Notifiable n : subscribers) n.notify(message);
        }
    }

    public static void main(String[] args) {
        NotificationHub hub = new NotificationHub();
        Department engineering = new Department("Engineering");
        Department.Employee priya = engineering.new Employee("Priya", hub);

        priya.raiseAlert("Server down!");

        System.out.println("Engineering notifications logged: " + engineering.notifications.size()); // 1
    }
}
```

**How to run:** `java OuterThisAdvanced.java`

`hub.register(Department.this)` inside `Employee`'s constructor passes the *actual enclosing `Department` instance* (here, `engineering`) to the `NotificationHub`, not merely some data copied from it — later, when `priya.raiseAlert(...)` triggers `hub.broadcast(...)`, the hub calls `notify` directly on that same registered `Department` object, which is why `engineering.notifications` ends up containing the broadcast message.

## 6. Walkthrough

Trace `main` in `OuterThisAdvanced` from construction through the final print.

**`new Department("Engineering")`.** Creates `engineering` with `name = "Engineering"` and an empty `notifications` list.

**`engineering.new Employee("Priya", hub)`.** Creates an `Employee` bound to `engineering`, with `this.name = "Priya"` and `this.hub = hub`. Inside the constructor, `hub.register(Department.this)` runs: `Department.this` resolves to `engineering` (the specific `Department` instance this `Employee` belongs to), so `hub.subscribers` gains `engineering` as an entry. Note that `engineering` was registered as a `Notifiable` — legal because `Department implements Notifiable`.

**`priya.raiseAlert("Server down!")`.** Calls `hub.broadcast("Priya: Server down!")` (using `this.name`, `Employee`'s own field, concatenated with the message).

**`hub.broadcast(...)`.** Iterates over `subscribers` (containing just `engineering`), calling `n.notify("Priya: Server down!")` on each — here, `n` is `engineering`, so this dispatches to `Department.notify`. Inside it, `notifications.add(...)` appends the message to `engineering.notifications`, and it prints `"Engineering received: Priya: Server down!"`.

**Final print.** `engineering.notifications.size()` is now `1` (the one message just added). Prints `"Engineering notifications logged: 1"`.

```
new Department("Engineering") -> engineering.name="Engineering", notifications=[]

new Employee("Priya", hub) inside engineering:
  hub.register(Department.this) -> Department.this resolves to engineering -> hub.subscribers = [engineering]

priya.raiseAlert("Server down!") -> hub.broadcast("Priya: Server down!")
hub.broadcast: for n in [engineering]: n.notify("Priya: Server down!")
  -> engineering.notify(...): notifications.add(...) -> prints "Engineering received: Priya: Server down!"

engineering.notifications.size() -> 1
```

**Final output.**
```
Engineering received: Priya: Server down!
Engineering notifications logged: 1
```

## 7. Gotchas & takeaways

> **`Outer.this` requires the enclosing class's actual name, not a generic keyword** — there is no single universal "outer" keyword; you must write the specific class name, as in `Department.this` or `Building.this`, matching the exact enclosing class the inner class is nested within. For multiple levels of nesting, each level uses its own class name to reach that specific level.

> **Passing `Outer.this` to external code shares the real, live enclosing instance, not a snapshot** — as the advanced example showed, `hub.register(Department.this)` registers the actual, mutable `Department` object; any later changes to that `Department`'s state are visible through the reference the hub holds, since it is the exact same object, not a copy.

- `Outer.this` explicitly refers to the specific enclosing instance an inner class instance is bound to, using the enclosing class's actual name as the qualifier.
- It resolves ambiguity when an inner class's own member shadows one with the same name on the enclosing class.
- It also lets code obtain or pass along the enclosing instance itself, not just data derived from it, which matters for registering the enclosing object with external systems.
- Each level of a multiply-nested class hierarchy uses its own specific class name with `.this` to reach exactly that level's enclosing instance.
