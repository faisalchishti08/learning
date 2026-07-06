---
card: java
gi: 221
slug: super-constructor-call
title: super(...) constructor call
---

## 1. What it is

`super(...)` calls the **superclass's constructor** directly from a subclass constructor, and — like `this(...)` for constructor chaining — must be the very first statement in the subclass constructor. If a subclass constructor doesn't explicitly write `super(...)`, Java automatically inserts an implicit call to the superclass's **no-argument** constructor as the first statement; if the superclass has no no-argument constructor available, the subclass **must** write an explicit `super(...)` call matching one of the superclass's actual constructors, or the code fails to compile.

```java
class Animal {
    String name;
    Animal(String name) { // no no-argument constructor exists
        this.name = name;
        System.out.println("Animal constructor: " + name);
    }
}

class Dog extends Animal {
    Dog(String name) {
        super(name); // REQUIRED — Animal has no no-arg constructor to call implicitly
        System.out.println("Dog constructor");
    }
}

new Dog("Rex");
// prints: "Animal constructor: Rex" then "Dog constructor"
```

`super(name)` explicitly invokes `Animal(String)`, passing `name` along — this must happen before anything else in `Dog`'s constructor body, and it's what actually sets `this.name` (inherited from `Animal`), since `Dog` itself never assigns `name` directly.

## 2. Why & when

`super(...)` exists to guarantee that a subclass's inherited state is properly set up by the class that actually owns and understands it, before the subclass adds anything of its own:

- **Delegating initialization to the class that owns the data** — a superclass's fields are often best initialized by the superclass's own constructor, which may validate or compute values in ways the subclass shouldn't need to duplicate.
- **Enforced ordering** — requiring `super(...)` to be the first statement guarantees the superclass is fully constructed before the subclass's own constructor body runs, consistent with the superclass-first construction order covered in earlier topics.
- **Passing subclass-specific information upward** — a subclass constructor often receives more parameters than the superclass needs; `super(...)` lets the subclass forward exactly the subset of information the superclass's constructor requires, while keeping the rest for its own use.

You write an explicit `super(...)` call whenever the superclass has no accessible no-argument constructor (forcing the explicit call), or whenever you specifically want the superclass's *other* constructor (not the no-argument one) to run — otherwise, Java's implicit no-argument `super()` call happens automatically and invisibly.

## 3. Core concept

```java
class Person {
    String name;
    int age;

    Person(String name, int age) {
        this.name = name;
        this.age = age;
    }
}

class Student extends Person {
    String school;

    Student(String name, int age, String school) {
        super(name, age); // forwards name and age up to Person's constructor
        this.school = school; // Student handles its own additional field
    }
}

Student s = new Student("Ann", 20, "State University");
System.out.println(s.name + ", " + s.age + ", " + s.school);
```

`Student`'s constructor receives three parameters but only forwards two (`name`, `age`) to `super(...)`, since those are the only ones `Person`'s constructor actually needs — `school` is handled entirely by `Student` itself, after the `super(...)` call has already ensured `name` and `age` are properly set up.

## 4. Diagram

<svg viewBox="0 0 600 160" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A Student constructor call passing three arguments, with two of them forwarded upward through super to Person's constructor which sets name and age, and the third handled directly by Student's own constructor body for the school field">
  <rect x="8" y="8" width="584" height="144" rx="8" fill="#0d1117"/>

  <rect x="30" y="30" width="220" height="45" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="140" y="55" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="monospace">new Student("Ann", 20, "State U")</text>

  <line x1="250" y1="52" x2="330" y2="52" stroke="#8b949e" stroke-width="1.5" marker-end="url(#sc)"/>
  <text x="290" y="45" fill="#8b949e" font-size="9" font-family="sans-serif">super(name, age)</text>

  <rect x="330" y="30" width="240" height="45" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="450" y="55" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">Person("Ann", 20) sets name, age</text>

  <text x="140" y="110" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">back in Student's own constructor body:</text>
  <text x="140" y="128" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="monospace">this.school = "State U"</text>

  <defs><marker id="sc" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

`super(...)` forwards exactly the arguments the superclass constructor needs; the subclass handles the rest itself.

## 5. Runnable example

Scenario: a small e-commerce order hierarchy — starting with a basic required `super(...)` call, then extending with a subclass forwarding a subset of its own parameters, then hardening into a multi-level hierarchy where `super(...)` chains through several levels correctly.

### Level 1 — Basic

```java
public class SuperCtorBasic {
    static class Order {
        String orderId;
        Order(String orderId) {
            this.orderId = orderId;
            System.out.println("Order created: " + orderId);
        }
    }

    static class OnlineOrder extends Order {
        OnlineOrder(String orderId) {
            super(orderId); // required — Order has no no-arg constructor
            System.out.println("OnlineOrder created");
        }
    }

    public static void main(String[] args) {
        new OnlineOrder("ORD-001");
    }
}
```

**How to run:** `java SuperCtorBasic.java`

`super(orderId)` is required here since `Order` declares only a one-argument constructor, with no no-argument version the compiler could implicitly call instead — omitting `super(orderId)` entirely would be a compile error.

### Level 2 — Intermediate

Same order system, now with `OnlineOrder` accepting an additional parameter of its own, forwarding only what `Order`'s constructor needs while keeping the rest for itself.

```java
public class SuperCtorIntermediate {
    static class Order {
        String orderId;
        Order(String orderId) {
            this.orderId = orderId;
        }
    }

    static class OnlineOrder extends Order {
        String shippingAddress;

        OnlineOrder(String orderId, String shippingAddress) {
            super(orderId); // forwards only orderId
            this.shippingAddress = shippingAddress; // handled here, not passed to super
        }
    }

    public static void main(String[] args) {
        OnlineOrder o = new OnlineOrder("ORD-002", "123 Main St");
        System.out.println(o.orderId + " ships to " + o.shippingAddress);
    }
}
```

**How to run:** `java SuperCtorIntermediate.java`

`OnlineOrder`'s constructor receives two parameters but forwards only `orderId` through `super(orderId)` — `shippingAddress` is a detail specific to `OnlineOrder` that `Order`'s constructor doesn't need or know about, so it's assigned directly in `OnlineOrder`'s own constructor body, after the `super(...)` call.

### Level 3 — Advanced

Same order system, now extended to three levels — `Order`, `OnlineOrder`, `ExpressOnlineOrder` — demonstrating `super(...)` chaining correctly through each level, with each class forwarding exactly what the next level up needs.

```java
public class SuperCtorAdvanced {
    static class Order {
        String orderId;
        Order(String orderId) {
            this.orderId = orderId;
            System.out.println("1. Order constructor: " + orderId);
        }
    }

    static class OnlineOrder extends Order {
        String shippingAddress;
        OnlineOrder(String orderId, String shippingAddress) {
            super(orderId);
            this.shippingAddress = shippingAddress;
            System.out.println("2. OnlineOrder constructor: " + shippingAddress);
        }
    }

    static class ExpressOnlineOrder extends OnlineOrder {
        boolean nextDayDelivery;
        ExpressOnlineOrder(String orderId, String shippingAddress, boolean nextDayDelivery) {
            super(orderId, shippingAddress); // forwards to OnlineOrder, which forwards further to Order
            this.nextDayDelivery = nextDayDelivery;
            System.out.println("3. ExpressOnlineOrder constructor: nextDay=" + nextDayDelivery);
        }
    }

    public static void main(String[] args) {
        ExpressOnlineOrder e = new ExpressOnlineOrder("ORD-003", "456 Oak Ave", true);
        System.out.println(e.orderId + ", " + e.shippingAddress + ", nextDay=" + e.nextDayDelivery);
    }
}
```

**How to run:** `java SuperCtorAdvanced.java`

`ExpressOnlineOrder`'s constructor calls `super(orderId, shippingAddress)`, invoking `OnlineOrder`'s constructor, which itself calls `super(orderId)`, invoking `Order`'s constructor — three constructors run in strict sequence, from the topmost ancestor down, each one's `super(...)` call forwarding exactly the arguments the next level up actually requires.

## 6. Walkthrough

Trace `new ExpressOnlineOrder("ORD-003", "456 Oak Ave", true)`:

**`ExpressOnlineOrder`'s constructor begins.** Its very first statement is `super(orderId, shippingAddress)`, i.e., `super("ORD-003", "456 Oak Ave")` — this must happen before anything else, so no println from `ExpressOnlineOrder` itself has printed yet.

**Delegates to `OnlineOrder`'s constructor.** Its first statement is `super(orderId)`, i.e., `super("ORD-003")` — again, this happens before anything else in `OnlineOrder`'s own body.

**Delegates to `Order`'s constructor.** `this.orderId = "ORD-003"`. Prints `"1. Order constructor: ORD-003"`. `Order`'s constructor finishes and returns control to `OnlineOrder`'s constructor.

**Back in `OnlineOrder`'s constructor.** `this.shippingAddress = "456 Oak Ave"`. Prints `"2. OnlineOrder constructor: 456 Oak Ave"`. Finishes, returns control to `ExpressOnlineOrder`'s constructor.

**Back in `ExpressOnlineOrder`'s constructor.** `this.nextDayDelivery = true`. Prints `"3. ExpressOnlineOrder constructor: nextDay=true"`.

```
new ExpressOnlineOrder("ORD-003", "456 Oak Ave", true)
  -> super("ORD-003", "456 Oak Ave") delegates to OnlineOrder
     -> super("ORD-003") delegates to Order
        this.orderId = "ORD-003"
        print "1. Order constructor: ORD-003"
     this.shippingAddress = "456 Oak Ave"
     print "2. OnlineOrder constructor: 456 Oak Ave"
  this.nextDayDelivery = true
  print "3. ExpressOnlineOrder constructor: nextDay=true"
```

**Final output.** Four lines total: the three numbered constructor messages in strict top-down order, followed by `"ORD-003, 456 Oak Ave, nextDay=true"` from `main`'s final print — demonstrating that all three ancestor levels' state ends up correctly and completely initialized on the single resulting `ExpressOnlineOrder` object.

## 7. Gotchas & takeaways

> **`super(...)` must be the very first statement in a constructor — nothing, not even a simple validation check, can precede it.** This mirrors the identical rule for `this(...)` constructor chaining (covered in an earlier topic); if you need logic to run before delegating to the superclass, it generally needs to be restructured as a static helper method call passed as one of the `super(...)` arguments themselves.

> **If a superclass has no no-argument constructor and a subclass fails to write an explicit `super(...)` call, the code simply does not compile.** This is a common and clear compiler error for anyone new to Java inheritance — the fix is always to add an explicit `super(...)` call matching one of the superclass's actual constructor signatures.

- `super(...)` explicitly calls a superclass constructor, and must be the first statement in the subclass constructor.
- Without an explicit `super(...)`, Java implicitly inserts a call to the superclass's no-argument constructor — if none exists, an explicit `super(...)` call becomes mandatory.
- A subclass constructor typically forwards only the subset of its parameters that the superclass constructor actually needs, handling any additional parameters itself afterward.
- In a multi-level hierarchy, `super(...)` calls chain upward through every level, running each ancestor's constructor fully before returning control back down, level by level.
