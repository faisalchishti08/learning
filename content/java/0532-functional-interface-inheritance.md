---
card: java
gi: 532
slug: functional-interface-inheritance
title: Functional interface inheritance
---

## 1. What it is

A **functional interface** is an interface with exactly one *abstract* method — the single method a lambda expression implements. Default and static methods don't count toward that limit, so a functional interface can have any number of them alongside its one abstract method. Functional interface inheritance covers what happens when one functional interface extends another: the abstract method can be narrowed (its return type made more specific, a technique called covariant return typing) or left as-is, but the "exactly one abstract method" rule must still hold in the end for `@FunctionalInterface` to apply.

## 2. Why & when

Understanding this matters once you start building small hierarchies of functional interfaces — a common pattern when a general-purpose interface (like `Function<T, R>`) needs a more specific variant for a particular use case. Extending a functional interface lets the more specific version inherit default methods and structure from the general one while still remaining usable as a lambda target, as long as it still resolves to exactly one abstract method after inheritance.

## 3. Core concept

```java
@FunctionalInterface
interface Transformer<T> {
    T transform(T input);

    default Transformer<T> andThenLog(String label) {
        return input -> {
            T result = transform(input);
            System.out.println(label + ": " + input + " -> " + result);
            return result;
        };
    }
}

@FunctionalInterface
interface StringTransformer extends Transformer<String> {
    // No new abstract method declared -- inherits exactly one abstract method: transform(String).
    // Still a valid functional interface, still usable as a lambda target.
}

StringTransformer upper = s -> s.toUpperCase();
```

`StringTransformer` extends `Transformer<String>` without adding any new abstract method — it inherits `transform(String)` as its sole abstract method, so it remains a valid, lambda-compatible functional interface.

## 4. Diagram

<svg viewBox="0 0 640 130" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="a functional interface extending another inherits its single abstract method, remaining lambda-compatible">
  <rect x="8" y="8" width="624" height="114" rx="8" fill="#0d1117"/>
  <rect x="30" y="20" width="220" height="50" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="140" y="40" fill="#79c0ff" font-size="12" text-anchor="middle" font-family="sans-serif">Transformer&lt;T&gt;</text>
  <text x="140" y="58" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">transform(T) -- 1 abstract method</text>
  <line x1="140" y1="70" x2="140" y2="95" stroke="#8b949e" stroke-width="1.5" marker-end="url(#arrowFI)"/>
  <rect x="30" y="95" width="220" height="0" fill="none"/>
  <text x="140" y="105" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">StringTransformer extends Transformer&lt;String&gt;</text>
  <text x="140" y="118" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">still exactly 1 abstract method -- still @FunctionalInterface</text>
  <defs><marker id="arrowFI" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

The child interface inherits the parent's single abstract method without adding a new one, so it remains valid as a lambda target.

## 5. Runnable example

Scenario: building a small hierarchy of specialized processing interfaces on top of a generic one — evolved from a basic extension preserving lambda-compatibility, through adding default methods inherited down the hierarchy, to a version demonstrating what breaks the functional interface contract when a second abstract method sneaks in.

### Level 1 — Basic

```java
public class FunctionalInheritanceBasic {
    @FunctionalInterface
    interface Transformer<T> {
        T transform(T input);
    }

    @FunctionalInterface
    interface StringTransformer extends Transformer<String> {
        // Inherits transform(String) as its sole abstract method -- no new one added.
    }

    public static void main(String[] args) {
        StringTransformer shout = s -> s.toUpperCase() + "!";

        System.out.println(shout.transform("hello"));
    }
}
```

**How to run:** `java FunctionalInheritanceBasic.java`

Expected output:
```
HELLO!
```

`StringTransformer` extends `Transformer<String>` but declares no new abstract method — it still has exactly one, `transform(String)`, inherited from `Transformer`. This means a lambda (`s -> s.toUpperCase() + "!"`) can still target `StringTransformer` directly, exactly as it could target `Transformer<String>`.

### Level 2 — Intermediate

```java
public class FunctionalInheritanceDefaults {
    @FunctionalInterface
    interface Transformer<T> {
        T transform(T input);

        default Transformer<T> logged(String label) {
            return input -> {
                T result = transform(input);
                System.out.println(label + ": " + input + " -> " + result);
                return result;
            };
        }
    }

    @FunctionalInterface
    interface StringTransformer extends Transformer<String> {
        // Adds its own default method, on top of inheriting Transformer's default AND abstract method.
        default StringTransformer trimmed() {
            return input -> transform(input.trim());
        }
    }

    public static void main(String[] args) {
        StringTransformer shout = s -> s.toUpperCase() + "!";

        Transformer<String> traced = shout.logged("shout"); // uses the INHERITED default method
        traced.transform("hello");

        StringTransformer trimmedShout = shout.trimmed(); // uses StringTransformer's OWN default method
        System.out.println(trimmedShout.transform("  hi  "));
    }
}
```

**How to run:** `java FunctionalInheritanceDefaults.java`

Expected output:
```
shout: hello -> HELLO!
HI!
```

The real-world concern this adds: `StringTransformer` gains **both** `Transformer`'s inherited default method (`logged(...)`) *and* its own newly-declared default method (`trimmed()`), while still being a valid functional interface with exactly one abstract method. `shout.logged("shout")` calls the inherited default, tracing the transformation; `shout.trimmed()` calls `StringTransformer`'s own default, which itself calls the abstract `transform(...)` method internally.

### Level 3 — Advanced

```java
public class FunctionalInheritanceBroken {
    @FunctionalInterface
    interface Transformer<T> {
        T transform(T input);
    }

    // NOT a valid functional interface -- adds a SECOND abstract method.
    interface ValidatingTransformer<T> extends Transformer<T> {
        T transform(T input); // inherited abstract method
        boolean isValid(T input); // a SECOND abstract method -- breaks the single-abstract-method rule
    }

    // @FunctionalInterface on ValidatingTransformer would cause a COMPILE ERROR here:
    // "Unexpected @FunctionalInterface annotation; ValidatingTransformer is not a functional interface"

    // Fix: implement it with a full class instead of a lambda, since it now needs TWO methods provided.
    static class BoundedIntTransformer implements ValidatingTransformer<Integer> {
        @Override public Integer transform(Integer input) { return input * 2; }
        @Override public boolean isValid(Integer input) { return input != null && input >= 0; }
    }

    public static void main(String[] args) {
        BoundedIntTransformer bounded = new BoundedIntTransformer();

        System.out.println("isValid(5): " + bounded.isValid(5));
        System.out.println("transform(5): " + bounded.transform(5));
        System.out.println("isValid(-3): " + bounded.isValid(-3));
    }
}
```

**How to run:** `java FunctionalInheritanceBroken.java`

Expected output:
```
isValid(5): true
transform(5): 10
isValid(-3): false
```

This demonstrates what breaks the functional interface contract: `ValidatingTransformer` adds `isValid(T)` as a **second** abstract method alongside the inherited `transform(T)` — meaning it can no longer be marked `@FunctionalInterface` (doing so would be a compile error) and, critically, a plain lambda can no longer implement it, since a lambda can only ever provide exactly one method's worth of logic. `BoundedIntTransformer` implements it the traditional way instead, as a full class providing both required methods.

## 6. Walkthrough

Execution starts in `main` of the Level 3 example. `bounded` is created as a `BoundedIntTransformer` instance.

`bounded.isValid(5)` calls `BoundedIntTransformer`'s implementation of `isValid`: `5 != null && 5 >= 0` — both `true`, so it returns `true`, printed as `"isValid(5): true"`.

`bounded.transform(5)` calls `BoundedIntTransformer`'s implementation of `transform`: `5 * 2 = 10`, returned and printed as `"transform(5): 10"`.

`bounded.isValid(-3)` calls `isValid` again: `-3 != null` is `true`, but `-3 >= 0` is `false` — the `&&` makes the overall result `false`, printed as `"isValid(-3): false"`.

```
ValidatingTransformer<T> requires BOTH:
  transform(T) -- inherited from Transformer<T>
  isValid(T)   -- newly declared, second abstract method

BoundedIntTransformer implements class-style, providing BOTH:
  transform(5)  -> 5 * 2 = 10
  isValid(5)    -> 5>=0 true  -> true
  isValid(-3)   -> -3>=0 false -> false
```

Because `ValidatingTransformer` has two abstract methods, no single lambda expression could ever have implemented it directly — Java requires a lambda's target type to have exactly one abstract method, so that the lambda's body unambiguously corresponds to that one method. `BoundedIntTransformer`, written as a full class, sidesteps this entirely by explicitly providing both required method implementations, which is the correct approach whenever an interface genuinely needs more than one abstract method.

## 7. Gotchas & takeaways

> Adding *any* new abstract method to an interface that extends a functional interface immediately disqualifies it from being a functional interface itself — even a single additional abstract method is one too many. If you find yourself wanting to add a second piece of required behavior to a functional interface, that's a signal the interface's role has grown beyond "a single operation a lambda can express," and a full class-based implementation (or splitting into two separate functional interfaces) is the more appropriate design.

- A functional interface has exactly one abstract method; default and static methods don't count toward that limit.
- An interface extending a functional interface, if it declares no *new* abstract method, remains a valid functional interface — still usable as a lambda target.
- Both the parent's and child's default methods are inherited together when extending a functional interface, letting a hierarchy of related default behaviors build up over specialized interfaces.
- Adding a second abstract method to an extending interface breaks the functional interface contract — `@FunctionalInterface` would then cause a compile error, and no lambda could implement it.
- `@FunctionalInterface` is optional but strongly recommended on any interface intended to be a lambda target — it causes the compiler to verify the single-abstract-method rule explicitly, catching accidental violations (like an added second abstract method) at compile time rather than as a confusing later error.
