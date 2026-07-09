---
card: java
gi: 587
slug: diamond-with-anonymous-classes
title: Diamond with anonymous classes
---

## 1. What it is

Since Java 9, the **diamond operator** (`<>`, introduced in Java 7 for type-inferred generic instantiation) can be used when creating an **anonymous class**, not just a plain `new ArrayList<>()`-style instantiation. `new Comparator<String>() { ... }` could not previously be shortened to `new Comparator<>() { ... }`; Java 9 lifted that restriction, letting type inference work for anonymous class bodies too, as long as the inferred type isn't itself denotable in a way the compiler can't express.

## 2. Why & when

Java 7's diamond operator let `List<String> names = new ArrayList<>();` infer `ArrayList<String>` from the left-hand side, avoiding the redundant `new ArrayList<String>()`. But this didn't originally extend to anonymous classes — `Comparator<String> byLength = new Comparator<String>() { ... }` still required the explicit type argument, because inferring the type parameter for an anonymous class's *body* was a harder compiler problem (the anonymous class itself is a genuinely new, unnamed type, and its inferred type parameters needed to interact correctly with that). Java 9 solved this specific inference problem, so the same redundancy-elimination diamond operator now works for anonymous classes too — one less place where a type had to be spelled out twice.

## 3. Core concept

```java
import java.util.*;

Comparator<String> byLength = new Comparator<String>() { // Java 7/8: explicit type argument required
    public int compare(String a, String b) { return a.length() - b.length(); }
};

Comparator<String> byLengthModern = new Comparator<>() { // Java 9+: diamond works here too
    public int compare(String a, String b) { return a.length() - b.length(); }
};
```

Both compile to functionally identical anonymous classes; the second form simply lets the compiler infer `Comparator<String>` from the declared variable type (`Comparator<String> byLengthModern = ...`), the same way it always inferred `ArrayList<String>` for `new ArrayList<>()`.

## 4. Diagram

<svg viewBox="0 0 640 130" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="The diamond operator now works for anonymous class creation, inferring the type argument from context">
  <text x="20" y="25" fill="#8b949e" font-size="11" font-family="sans-serif">Java 7/8 — type argument repeated:</text>
  <rect x="20" y="35" width="600" height="30" rx="6" fill="#1c2430" stroke="#f85149"/>
  <text x="320" y="55" fill="#f85149" font-size="10" text-anchor="middle" font-family="monospace">Comparator&lt;String&gt; c = new Comparator&lt;String&gt;() { ... };</text>

  <text x="20" y="95" fill="#8b949e" font-size="11" font-family="sans-serif">Java 9+ — diamond infers it:</text>
  <rect x="20" y="105" width="600" height="20" rx="6" fill="#1c2430" stroke="#6db33f"/>
</svg>

The compiler already knew `String` from the declared variable type — the diamond operator just stops making you repeat it for anonymous classes too.

## 5. Runnable example

Scenario: building a small event-handling registry using anonymous class implementations of a callback interface — starting with the pre-Java-9 explicit-type-argument style, then simplifying with the diamond operator, then using it with a more complex generic interface where the inferred type argument itself involves multiple type parameters.

### Level 1 — Basic

```java
import java.util.*;

public class DiamondOldStyle {
    interface EventHandler<T> {
        void handle(T event);
    }

    public static void main(String[] args) {
        EventHandler<String> logger = new EventHandler<String>() { // explicit type argument
            public void handle(String event) {
                System.out.println("Handled: " + event);
            }
        };

        logger.handle("user-login");
    }
}
```

**How to run:** `java DiamondOldStyle.java`

Expected output:
```
Handled: user-login
```

`new EventHandler<String>() { ... }` repeats `String` even though the variable it's assigned to, `EventHandler<String> logger`, already declares that exact type argument on its left-hand side — genuinely redundant, but this was the only legal syntax before Java 9.

### Level 2 — Intermediate

```java
import java.util.*;

public class DiamondModern {
    interface EventHandler<T> {
        void handle(T event);
    }

    public static void main(String[] args) {
        EventHandler<String> logger = new EventHandler<>() { // Java 9+: diamond infers <String>
            public void handle(String event) {
                System.out.println("Handled: " + event);
            }
        };

        logger.handle("user-login");
    }
}
```

**How to run:** `java DiamondModern.java`

Expected output:
```
Handled: user-login
```

The real-world concern this adds: `new EventHandler<>() { ... }` — the diamond operator, now legal on an anonymous class creation — lets the compiler infer `<String>` from the declared type of `logger` (`EventHandler<String>`), exactly the same inference the diamond operator has always performed for non-anonymous generic instantiation. The anonymous class body still implements `handle(String event)` with the concrete, inferred type — the compiler resolves `T` to `String` for the purposes of type-checking that method's signature, identical to Level 1's explicit form.

### Level 3 — Advanced

```java
import java.util.*;
import java.util.function.*;

public class DiamondMultiParam {
    interface Transformer<IN, OUT> {
        OUT transform(IN input);
    }

    static <IN, OUT> OUT applyTransformer(IN input, Transformer<IN, OUT> transformer) {
        return transformer.transform(input);
    }

    public static void main(String[] args) {
        Transformer<String, Integer> lengthOf = new Transformer<>() { // TWO type parameters, both inferred
            public Integer transform(String input) {
                return input.length();
            }
        };

        int result = applyTransformer("hello world", lengthOf);
        System.out.println("Length: " + result);

        // Diamond also works when the anonymous class is created directly as a method argument,
        // as long as target-type inference from the parameter type can determine both IN and OUT.
        Integer directResult = applyTransformer("diamond operator", new Transformer<>() {
            public Integer transform(String input) {
                return input.split(" ").length;
            }
        });
        System.out.println("Word count: " + directResult);
    }
}
```

**How to run:** `java DiamondMultiParam.java`

Expected output:
```
Length: 11
Word count: 2
```

This handles the production-flavoured case of a **multi-type-parameter generic interface** (`Transformer<IN, OUT>`, two type parameters, not one) used both in a variable declaration and directly as a method argument. `new Transformer<>() { ... }` infers *both* `IN=String` and `OUT=Integer` from context — in the first case from the declared `Transformer<String, Integer> lengthOf`, in the second case from `applyTransformer`'s own generic signature (`applyTransformer(String, Transformer<String, ?>)`, inferred from the string literal argument), demonstrating the diamond operator's inference working through a full generic method call, not just a simple variable assignment.

## 6. Walkthrough

Execution starts in `main` of the Level 3 example. `Transformer<String, Integer> lengthOf = new Transformer<>() { ... }` is evaluated first. The compiler sees the declared type `Transformer<String, Integer>` on the left-hand side and infers that the diamond `<>` on the right should be filled in as `<String, Integer>` — so the anonymous class effectively implements `Transformer<String, Integer>`, meaning its `transform` method must accept a `String` and return an `Integer`, matching the anonymous class body's actual `public Integer transform(String input) { ... }` declaration.

`applyTransformer("hello world", lengthOf)` is called. Inside `applyTransformer<IN, OUT>`, `IN` and `OUT` are inferred from the call site as `String` and `Integer` respectively (matching `lengthOf`'s actual type). `transformer.transform(input)` calls `lengthOf`'s `transform("hello world")`, which returns `"hello world".length()`, i.e., `11`. `applyTransformer` returns `11`, `result` is `11`, and `main` prints `"Length: 11"`.

```
Second call's inference chain:

applyTransformer("diamond operator", new Transformer<>() { ... })
  |
  applyTransformer's own signature: <IN, OUT> OUT applyTransformer(IN input, Transformer<IN, OUT> transformer)
  |
  first argument "diamond operator" is a String -> IN is inferred as String
  |
  second argument's diamond <> must therefore be Transformer<String, ?> -> the anonymous class's
  transform(String input) method confirms OUT is Integer (its return type) -> full inference: <String, Integer>
```

The second call, `applyTransformer("diamond operator", new Transformer<>() { public Integer transform(String input) { return input.split(" ").length; } })`, demonstrates diamond inference working through a full method-call context rather than a simple variable declaration: the compiler infers `IN=String` from the first argument's type, which constrains the anonymous class's diamond to `Transformer<String, ?>`; combined with the anonymous class body's own `transform` method returning `Integer`, the compiler resolves the complete type as `Transformer<String, Integer>`, satisfying `applyTransformer`'s generic signature with `OUT=Integer`.

Inside that anonymous class's `transform("diamond operator")`, `input.split(" ")` splits the string on spaces, producing `["diamond", "operator"]` (a 2-element array), and `.length` (the array field, not a method) is `2`. `applyTransformer` returns `2`, `directResult` is `2`, and `main` prints `"Word count: 2"`.

## 7. Gotchas & takeaways

> The diamond operator on an anonymous class only works when the type argument can be **fully inferred from context** — if the anonymous class body itself references its own type parameter in a way that creates an ambiguous or under-constrained inference (uncommon, but possible with more elaborate generic bounds), the compiler falls back to requiring the explicit type argument, exactly as it always has for non-anonymous diamond usage in similarly ambiguous cases.

- This is purely a syntax simplification — the anonymous class created with `new Interface<>() { ... }` is exactly the same kind of anonymous class, with exactly the same runtime behavior, as one created with the fully-spelled-out `new Interface<ExplicitType>() { ... }`; nothing about class loading, method resolution, or performance changes.
- The diamond operator was already legal for non-anonymous generic instantiation since Java 7 (`new ArrayList<>()`); this Java 9 change specifically closes the gap for the anonymous-class case, which had been a longstanding, minor asymmetry in the language.
- Anonymous classes created with the diamond operator still cannot use `<>` if the anonymous class needs to add members (fields, additional methods) beyond what the implemented interface or extended class declares in a way that depends on the erased, non-generic raw type — this is a narrow edge case rarely encountered in typical code.
- IDEs commonly flag `new SomeInterface<ExplicitType>() { ... }` with a suggestion to simplify to `new SomeInterface<>() { ... }` once a project's minimum supported Java version reaches 9 or later — a safe, purely cosmetic refactor with no behavioral change.
- This feature composes normally with all the usual generic-inference rules: bounded type parameters, wildcards, and multi-parameter generics (as in the Level 3 example) are all handled by the same inference algorithm that's always driven `<>` for ordinary object creation, just now extended to also apply when an anonymous class body follows the `<>`.
