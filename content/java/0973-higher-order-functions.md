---
card: java
gi: 973
slug: higher-order-functions
title: Higher-order functions
---

## 1. What it is

A higher-order function is a function that either accepts another function as an argument, returns a function as its result, or both — treating functions as ordinary values, exactly like numbers or strings, rather than as a fundamentally different kind of thing that can only ever be *called*, never passed around. In Java, this is implemented through functional interfaces (`Function<T, R>`, `Predicate<T>`, `Consumer<T>`, `Supplier<T>`, `BiFunction<T, U, R>`, and others in `java.util.function`), each describing a specific "shape" of function (how many arguments, what return type), with lambda expressions or method references supplying the actual, concrete implementations. `Stream.map`, `Stream.filter`, and `Collections.sort` (with a `Comparator`) are all higher-order functions from the JDK itself — each one accepts a function as a parameter, using it to customize its own behavior without needing to know, at compile time, exactly what that behavior will be.

## 2. Why & when

Higher-order functions matter because they let you factor out and parameterize *behavior* the same way ordinary parameters let you factor out and parameterize *data* — instead of writing a separate, nearly-identical method for "filter a list keeping only even numbers" and another for "filter a list keeping only strings longer than five characters," you write one generic `filter` method taking a `Predicate<T>` as a parameter, and supply the specific condition as an argument at the call site. This is the foundation the entire `Stream` API is built on: `map`, `filter`, `reduce`, `forEach`, and `sorted` are all higher-order functions, each accepting a lambda that supplies the specific per-element logic while the method itself handles the surrounding iteration, short-circuiting, or accumulation machinery. Reach for a higher-order function whenever you notice several methods sharing an identical structure but differing only in one small piece of behavior in the middle — that varying piece is exactly what should become a function parameter, turning several near-duplicate methods into one flexible, reusable one.

## 3. Core concept

```java
// A higher-order function: accepts a Predicate<T> as a parameter, using it to
// customize which elements are kept -- the CALLER supplies the specific behavior.
static <T> List<T> filter(List<T> items, Predicate<T> condition) {
    List<T> result = new ArrayList<>();
    for (T item : items) {
        if (condition.test(item)) {   // delegate the DECISION to the passed-in function
            result.add(item);
        }
    }
    return result;
}

filter(numbers, n -> n % 2 == 0);         // "keep evens" -- behavior supplied at the call site
filter(words, w -> w.length() > 5);       // "keep long words" -- SAME filter method, different behavior

// A higher-order function that RETURNS a function:
static Predicate<Integer> greaterThan(int threshold) {
    return n -> n > threshold;   // returns a NEW function, customized by 'threshold'
}
Predicate<Integer> isAdult = greaterThan(17);
```

The same `filter` method serves any condition imaginable, because the condition itself — the varying piece of behavior — is passed in as an ordinary argument, exactly the way ordinary parameters let one method serve many different pieces of data.

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="One generic filter method accepting different Predicate functions as arguments, each customizing its filtering behavior without requiring a separate method per condition" >
  <rect x="220" y="20" width="200" height="40" fill="#1c2430" stroke="#6db33f"/>
  <text x="320" y="45" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">filter(items, condition)</text>

  <rect x="40" y="90" width="160" height="35" fill="#1c2430" stroke="#79c0ff"/>
  <text x="120" y="112" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">n -&gt; n % 2 == 0</text>

  <rect x="240" y="90" width="160" height="35" fill="#1c2430" stroke="#f0883e"/>
  <text x="320" y="112" fill="#f0883e" font-size="9" text-anchor="middle" font-family="sans-serif">w -&gt; w.length() &gt; 5</text>

  <rect x="440" y="90" width="160" height="35" fill="#1c2430" stroke="#e6edf3"/>
  <text x="520" y="112" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">...any condition...</text>

  <line x1="120" y1="90" x2="280" y2="60" stroke="#8b949e"/>
  <line x1="320" y1="90" x2="320" y2="60" stroke="#8b949e"/>
  <line x1="520" y1="90" x2="360" y2="60" stroke="#8b949e"/>
</svg>

*One higher-order function serves unlimited different behaviors, each supplied as an ordinary function-typed argument at the call site.*

## 5. Runnable example

Scenario: build a small, reusable data-processing toolkit using higher-order functions, evolving from a basic generic filter, to a realistic combination of multiple functional-interface parameters working together, to a more advanced case where a function itself returns a customized function.

### Level 1 — Basic

```java
import java.util.*;
import java.util.function.*;

public class HigherOrderBasic {
    static <T> List<T> filter(List<T> items, Predicate<T> condition) {
        List<T> result = new ArrayList<>();
        for (T item : items) {
            if (condition.test(item)) {
                result.add(item);
            }
        }
        return result;
    }

    public static void main(String[] args) {
        List<Integer> numbers = List.of(1, 2, 3, 4, 5, 6, 7, 8, 9, 10);
        System.out.println(filter(numbers, n -> n % 2 == 0));
        System.out.println(filter(numbers, n -> n > 7));
    }
}
```

**How to run:** `java HigherOrderBasic.java` (JDK 17+).

Expected output:
```
[2, 4, 6, 8, 10]
[8, 9, 10]
```

`filter` is a single, generic higher-order function accepting a `Predicate<T>` — the exact filtering logic ("is even," "is greater than 7") is supplied as a different lambda at each call site, with `filter` itself unchanged and unaware, at compile time, of which specific condition it will ever be given.

### Level 2 — Intermediate

```java
import java.util.*;
import java.util.function.*;

public class HigherOrderMultipleParams {
    static <T, R> List<R> transformAndFilter(List<T> items, Function<T, R> transform, Predicate<R> keep) {
        List<R> result = new ArrayList<>();
        for (T item : items) {
            R transformed = transform.apply(item);
            if (keep.test(transformed)) {
                result.add(transformed);
            }
        }
        return result;
    }

    public static void main(String[] args) {
        List<String> words = List.of("apple", "kiwi", "banana", "fig", "watermelon");

        List<Integer> lengths = transformAndFilter(
            words,
            String::length,           // transform: word -> its length
            len -> len > 4             // keep: only lengths greater than 4
        );

        System.out.println(lengths);
    }
}
```

**How to run:** `java HigherOrderMultipleParams.java` (JDK 17+).

Expected output:
```
[5, 6, 10]
```

The real-world concern added: `transformAndFilter` accepts *two* function parameters simultaneously (`Function<T, R>` for transforming each element, `Predicate<R>` for deciding whether to keep the transformed result) — this composes two separate behaviors (mapping and filtering) into one reusable, generic method, letting the caller independently customize both the transformation and the filtering criterion at each call site.

### Level 3 — Advanced

```java
import java.util.*;
import java.util.function.*;

public class HigherOrderReturningFunctions {
    // Returns a customized VALIDATOR function -- a higher-order function that
    // itself RETURNS a function, parameterized by the arguments given here.
    static Predicate<String> lengthValidator(int min, int max) {
        return s -> s.length() >= min && s.length() <= max;
    }

    // Combines two Predicates into a new, single Predicate -- another
    // higher-order function, this time accepting AND returning functions.
    static <T> Predicate<T> both(Predicate<T> first, Predicate<T> second) {
        return value -> first.test(value) && second.test(value);
    }

    public static void main(String[] args) {
        Predicate<String> usernameLength = lengthValidator(3, 20);
        Predicate<String> noSpaces = s -> !s.contains(" ");
        Predicate<String> validUsername = both(usernameLength, noSpaces);

        for (String candidate : List.of("ab", "alice", "bob smith", "a".repeat(25))) {
            System.out.println("\"" + candidate + "\" valid: " + validUsername.test(candidate));
        }
    }
}
```

**How to run:** `java HigherOrderReturningFunctions.java` (JDK 17+).

Expected output:
```
"ab" valid: false
"alice" valid: true
"bob smith" valid: false
"aaaaaaaaaaaaaaaaaaaaaaaaa" valid: false
```

The production-flavored hard case: `lengthValidator` is a higher-order function that *returns* a customized `Predicate` (parameterized by `min`/`max`), and `both` is a higher-order function that *accepts two* `Predicate`s and *returns* a new, combined one — chaining these together (`both(usernameLength, noSpaces)`) builds a single, reusable `validUsername` function entirely out of smaller, independently-defined and independently-testable pieces, without writing a single monolithic validation method mixing every rule together directly.

## 6. Walkthrough

Tracing `validUsername.test("bob smith")` end to end from `HigherOrderReturningFunctions.main`:

1. `lengthValidator(3, 20)` was called earlier, returning a `Predicate<String>` whose body is `s -> s.length() >= 3 && s.length() <= 20` — this lambda has captured `min = 3` and `max = 20` from `lengthValidator`'s parameters, and this returned function is bound to `usernameLength`.
2. `both(usernameLength, noSpaces)` was then called, returning a *new* `Predicate<String>` whose body is `value -> first.test(value) && second.test(value)`, with `first` captured as `usernameLength` and `second` captured as `noSpaces` — this composed predicate is bound to `validUsername`.
3. `validUsername.test("bob smith")` invokes this composed predicate's body: `first.test("bob smith") && second.test("bob smith")`.
4. `first.test("bob smith")` calls `usernameLength`'s own body: `"bob smith".length() >= 3 && "bob smith".length() <= 20` — `"bob smith"` has length `9`, so this evaluates `9 >= 3` (true) `&&` `9 <= 20` (true), overall `true`.
5. Because the first operand of `both`'s `&&` was `true`, Java's short-circuit evaluation proceeds to evaluate the second operand: `second.test("bob smith")` calls `noSpaces`'s body, `!s.contains(" ")` — since `"bob smith"` does contain a space, `contains(" ")` is `true`, so `!true` is `false`.
6. The overall expression `true && false` evaluates to `false`, so `validUsername.test("bob smith")` returns `false`, which is printed as `"bob smith" valid: false` — demonstrating that the final composed function's behavior is exactly the logical combination of its two independently-defined, independently-testable component functions, built up through two separate applications of higher-order functions (`lengthValidator` returning a customized predicate, `both` combining two predicates into one) without ever writing a single function containing all the validation logic directly.

## 7. Gotchas & takeaways

> **Gotcha:** a functional interface like `Predicate<T>` or `Function<T, R>` is still an ordinary object at runtime — each lambda expression creates an actual object implementing that interface, capturing whatever local variables it references; composing many higher-order functions together (as with `both`) creates a small chain of these wrapper objects, which is usually negligible overhead but worth being aware of if you're composing functions inside an extremely hot, performance-critical loop, where the extra indirection and object allocation could matter more than it would in ordinary application code.

- A higher-order function accepts a function as a parameter, returns a function as its result, or both — treating behavior itself as an ordinary, passable value, exactly the way ordinary parameters treat data.
- Java expresses this through functional interfaces (`Function`, `Predicate`, `Consumer`, `Supplier`, `BiFunction`, and others), with lambda expressions or method references supplying concrete implementations at each call site.
- `Stream`'s `map`, `filter`, `reduce`, and similar methods are all higher-order functions from the JDK itself, each customized by whatever function is supplied to it.
- Reach for a higher-order function whenever several methods share an identical structure but differ only in one piece of behavior — that varying piece should become a function-typed parameter, collapsing several near-duplicate methods into one flexible, reusable one.
- Functions that return functions (like `lengthValidator`) and functions that combine other functions into a new one (like `both`) let you build complex behavior compositionally, out of small, independently-testable pieces.
- See [function composition & currying](0972-function-composition-currying.md) for the specific composition and partial-application techniques this general concept directly enables, and [pure functions & immutability](0971-pure-functions-immutability.md) for the discipline that keeps higher-order-function-based code safe and predictable, especially under parallel execution.
