---
card: java
gi: 1003
slug: decorator
title: Decorator
---

## 1. What it is

The **Decorator** pattern attaches new behavior to an object dynamically by wrapping it in another object that implements the same interface. The decorator holds a reference to the wrapped object, delegates to it, and adds its own behavior before or after that delegation. Multiple decorators can be stacked, each adding one more layer of behavior — like nesting envelopes, where each envelope adds a stamp, a wax seal, or a "fragile" sticker without changing what's inside.

## 2. Why & when

Adding every possible combination of behavior as a subclass explodes combinatorially — a `Coffee` that might or might not have milk, sugar, or whipped cream needs `CoffeeWithMilk`, `CoffeeWithMilkAndSugar`, `CoffeeWithMilkAndSugarAndCream`, and so on for every combination. Decorator avoids this by making each add-on a separate wrapper class implementing the same interface as the thing it wraps — you compose exactly the combination you need at runtime by nesting wrappers, instead of needing a pre-built subclass for every combination in advance.

Reach for Decorator when you need to add optional, stackable behavior to an object — logging, caching, compression, or in the classic example, condiments on a drink — and the set of combinations would otherwise require a subclass per combination. It's unnecessary when there's only one or two fixed variations; a couple of subclasses or an `if` branch is simpler there.

## 3. Core concept

```
interface Coffee { double cost(); String description(); }

class SimpleCoffee implements Coffee {
    public double cost() { return 2.0; }
    public String description() { return "Coffee"; }
}

// Each decorator WRAPS a Coffee and implements the SAME interface
abstract class CoffeeDecorator implements Coffee {
    protected final Coffee wrapped;
    CoffeeDecorator(Coffee wrapped) { this.wrapped = wrapped; }
}

class MilkDecorator extends CoffeeDecorator {
    MilkDecorator(Coffee wrapped) { super(wrapped); }
    public double cost() { return wrapped.cost() + 0.5; }
    public String description() { return wrapped.description() + " + Milk"; }
}

// Stack decorators to compose exactly the combination needed:
Coffee order = new MilkDecorator(new SimpleCoffee());
System.out.println(order.description() + " = $" + order.cost()); // "Coffee + Milk = $2.5"
```

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A SimpleCoffee wrapped by a MilkDecorator wrapped by a SugarDecorator, each layer adding cost and description while delegating to the layer inside">
  <rect x="30" y="40" width="150" height="60" rx="8" fill="#1c2430" stroke="#8b949e"/>
  <text x="105" y="75" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">SimpleCoffee</text>

  <rect x="220" y="30" width="180" height="80" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="310" y="52" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">MilkDecorator</text>
  <text x="310" y="98" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">wraps ^</text>

  <rect x="440" y="10" width="180" height="120" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="530" y="32" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">SugarDecorator</text>
  <text x="530" y="118" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">wraps ^</text>
</svg>

Each decorator wraps the one before it, adding its own cost and description while delegating everything else inward.

## 5. Runnable example

Scenario: a coffee shop's ordering system, evolving from a combinatorial subclass explosion into stackable decorators that compose any combination of add-ons at runtime.

### Level 1 — Basic

```java
// File: DecoratorBasic.java
interface Coffee {
    double cost();
    String description();
}

class SimpleCoffee implements Coffee {
    public double cost() { return 2.0; }
    public String description() { return "Coffee"; }
}

// One subclass per fixed combination -- doesn't scale as add-ons multiply.
class CoffeeWithMilk implements Coffee {
    public double cost() { return 2.5; }
    public String description() { return "Coffee + Milk"; }
}

public class DecoratorBasic {
    public static void main(String[] args) {
        Coffee plain = new SimpleCoffee();
        Coffee withMilk = new CoffeeWithMilk();
        System.out.println(plain.description() + " = $" + plain.cost());
        System.out.println(withMilk.description() + " = $" + withMilk.cost());
    }
}
```

**How to run:** save as `DecoratorBasic.java`, then `javac DecoratorBasic.java && java DecoratorBasic` (JDK 17+).

Expected output:
```
Coffee = $2.0
Coffee + Milk = $2.5
```

Adding sugar as another option means a `CoffeeWithSugar` class, then `CoffeeWithMilkAndSugar` for the combination — every new add-on multiplies the number of subclasses needed to cover every combination.

### Level 2 — Intermediate

```java
// File: DecoratorIntermediate.java
interface Coffee {
    double cost();
    String description();
}

class SimpleCoffee implements Coffee {
    public double cost() { return 2.0; }
    public String description() { return "Coffee"; }
}

abstract class CoffeeDecorator implements Coffee {
    protected final Coffee wrapped;
    CoffeeDecorator(Coffee wrapped) { this.wrapped = wrapped; }
}

class MilkDecorator extends CoffeeDecorator {
    MilkDecorator(Coffee wrapped) { super(wrapped); }
    public double cost() { return wrapped.cost() + 0.5; }
    public String description() { return wrapped.description() + " + Milk"; }
}

class SugarDecorator extends CoffeeDecorator {
    SugarDecorator(Coffee wrapped) { super(wrapped); }
    public double cost() { return wrapped.cost() + 0.25; }
    public String description() { return wrapped.description() + " + Sugar"; }
}

public class DecoratorIntermediate {
    public static void main(String[] args) {
        Coffee order = new SugarDecorator(new MilkDecorator(new SimpleCoffee()));
        System.out.println(order.description() + " = $" + order.cost());
    }
}
```

**How to run:** save as `DecoratorIntermediate.java`, then `javac DecoratorIntermediate.java && java DecoratorIntermediate` (JDK 17+).

Expected output:
```
Coffee + Milk + Sugar = $2.75
```

The real-world concern added: `Milk` and `Sugar` are now separate, stackable wrapper classes instead of separate combination subclasses. Any combination — milk only, sugar only, both, or neither — is just a different way of nesting the wrappers, with no new class needed per combination.

### Level 3 — Advanced

```java
// File: DecoratorAdvanced.java
import java.util.function.UnaryOperator;

interface Coffee {
    double cost();
    String description();
}

class SimpleCoffee implements Coffee {
    public double cost() { return 2.0; }
    public String description() { return "Coffee"; }
}

abstract class CoffeeDecorator implements Coffee {
    protected final Coffee wrapped;
    CoffeeDecorator(Coffee wrapped) { this.wrapped = wrapped; }
}

class MilkDecorator extends CoffeeDecorator {
    MilkDecorator(Coffee wrapped) { super(wrapped); }
    public double cost() { return wrapped.cost() + 0.5; }
    public String description() { return wrapped.description() + " + Milk"; }
}

class SugarDecorator extends CoffeeDecorator {
    SugarDecorator(Coffee wrapped) { super(wrapped); }
    public double cost() { return wrapped.cost() + 0.25; }
    public String description() { return wrapped.description() + " + Sugar"; }
}

class WhippedCreamDecorator extends CoffeeDecorator {
    WhippedCreamDecorator(Coffee wrapped) { super(wrapped); }
    public double cost() { return wrapped.cost() + 0.75; }
    public String description() { return wrapped.description() + " + Whipped Cream"; }
}

public class DecoratorAdvanced {
    // A little builder-style helper that applies a LIST of decorators dynamically,
    // reading the customer's order as data instead of hardcoding the nesting.
    static Coffee buildOrder(String... addOns) {
        Coffee coffee = new SimpleCoffee();
        for (String addOn : addOns) {
            UnaryOperator<Coffee> decorator = switch (addOn) {
                case "MILK" -> MilkDecorator::new;
                case "SUGAR" -> SugarDecorator::new;
                case "CREAM" -> WhippedCreamDecorator::new;
                default -> throw new IllegalArgumentException("unknown add-on: " + addOn);
            };
            coffee = decorator.apply(coffee);
        }
        return coffee;
    }

    public static void main(String[] args) {
        Coffee order = buildOrder("MILK", "SUGAR", "CREAM");
        System.out.println(order.description() + " = $" + order.cost());

        Coffee simpleOrder = buildOrder("SUGAR");
        System.out.println(simpleOrder.description() + " = $" + simpleOrder.cost());
    }
}
```

**How to run:** save as `DecoratorAdvanced.java`, then `javac DecoratorAdvanced.java && java DecoratorAdvanced` (JDK 17+).

Expected output:
```
Coffee + Milk + Sugar + Whipped Cream = $3.5
Coffee + Sugar = $2.25
```

The production-flavored hard case: `buildOrder` composes decorators dynamically from a runtime list of add-on names — a customer's order (data, potentially from user input) drives which decorators get stacked and in what order, without any hardcoded nesting expression, and without adding a single new decorator class for any combination.

## 6. Walkthrough

Tracing `buildOrder("MILK", "SUGAR", "CREAM")` and the subsequent `order.cost()` call:

1. `coffee` starts as a plain `new SimpleCoffee()`.
2. The loop's first iteration processes `"MILK"`: the switch resolves `MilkDecorator::new` as a constructor reference, and `decorator.apply(coffee)` calls `new MilkDecorator(coffee)`, wrapping the `SimpleCoffee`. `coffee` is reassigned to this new `MilkDecorator` instance.
3. The second iteration processes `"SUGAR"`: `SugarDecorator::new` is resolved, and `new SugarDecorator(coffee)` wraps the current `MilkDecorator`-wrapped coffee. `coffee` is now a `SugarDecorator` wrapping a `MilkDecorator` wrapping a `SimpleCoffee`.
4. The third iteration processes `"CREAM"`: `new WhippedCreamDecorator(coffee)` wraps the whole chain built so far. `coffee` is finally returned as this outermost `WhippedCreamDecorator`.
5. `order.cost()` calls `WhippedCreamDecorator.cost()`, which computes `wrapped.cost() + 0.75` — but first it must resolve `wrapped.cost()`, which is the `SugarDecorator`'s `cost()`, which itself needs `wrapped.cost()` from the `MilkDecorator`, which needs `wrapped.cost()` from the innermost `SimpleCoffee`: `2.0`.
6. The costs resolve back outward: `SimpleCoffee` gives `2.0`, `MilkDecorator` adds `0.5` to get `2.5`, `SugarDecorator` adds `0.25` to get `2.75`, and `WhippedCreamDecorator` adds `0.75` to get the final `3.5` — printed alongside the description, which is built the same way, working outward from `"Coffee"` to the fully-decorated string.

## 7. Gotchas & takeaways

> **Gotcha:** decorator order matters if the add-ons aren't purely additive — here, cost and description happen to be commutative (order doesn't change the total), but a decorator that applies a percentage discount or a multiplier would produce a different result depending on where in the stack it's applied, so don't assume decorator order is always irrelevant.

- Decorator wraps an object in another object implementing the same interface, adding behavior by delegating to the wrapped object and layering its own logic around that call.
- It avoids the combinatorial subclass explosion of needing one class per combination of optional behaviors.
- Each decorator should stay focused on adding exactly one behavior (single responsibility), and decorators can be stacked in any combination, in code or driven by runtime data.
- Building the stack dynamically from a list (as in Level 3) turns "hardcoded nesting" into "data-driven composition," letting the exact combination be decided at runtime.
- Don't reach for Decorator when only one or two fixed variations are ever needed — plain subclasses or an `if` are simpler there.
- Decorator and [composition over inheritance](0995-composition-over-inheritance.md) are closely related: a decorator is itself a form of composition, holding a reference to the object it enhances rather than inheriting from it.
