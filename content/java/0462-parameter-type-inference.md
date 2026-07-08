---
card: java
gi: 462
slug: parameter-type-inference
title: Parameter type inference
---

## 1. What it is

Lambda parameters normally don't need explicit type declarations — the compiler infers each parameter's type from the **target functional interface**, the context the lambda is being assigned to or passed into. `(a, b) -> a.compareTo(b)` and `(String a, String b) -> a.compareTo(b)` mean exactly the same thing when the target is `Comparator<String>`; the compiler already knows, from `Comparator<String>.compare(String, String)`, that `a` and `b` must both be `String`.

## 2. Why & when

Explicit types on lambda parameters are redundant in the overwhelming majority of cases, because the functional interface a lambda implements already fixes every parameter's type — writing it again is pure repetition, exactly the kind of boilerplate `var` was later introduced to cut for local variables. Type inference lets a lambda stay as short as the logic it expresses: `(a, b) -> a.compareTo(b)` instead of `(String a, String b) -> a.compareTo(b)`.

You rely on inference by default — it's simply the normal, idiomatic way to write a lambda. You reach for explicit types only in the rare case where inference genuinely cannot determine a type (an ambiguous overload where two functional interfaces could both match) or where writing the type improves clarity for an unusually complex generic signature. In everyday code, adding explicit types to lambda parameters is almost always unnecessary noise.

## 3. Core concept

```java
import java.util.function.*;

// Inferred: compiler knows from BiFunction<Integer, Integer, Integer> that a and b are Integer
BiFunction<Integer, Integer, Integer> add = (a, b) -> a + b;

// Explicit: legal, but redundant -- says nothing inference didn't already know
BiFunction<Integer, Integer, Integer> addExplicit = (Integer a, Integer b) -> a + b;

// Java 11+: "var" lambda parameters -- explicit-ish, but still inferred, mainly useful for annotations
BiFunction<Integer, Integer, Integer> addVar = (var a, var b) -> a + b;
```

All three lines produce an identical `BiFunction<Integer, Integer, Integer>` — the type information exists in exactly one place either way, in the variable's declared type, and the lambda parameters simply pick it up.

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="The target functional interface's method signature supplies the parameter types the compiler infers for the lambda">
  <rect x="8" y="8" width="624" height="134" rx="8" fill="#0d1117"/>
  <rect x="30" y="30" width="260" height="50" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="160" y="55" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="monospace">BiFunction&lt;Integer,Integer,Integer&gt;</text>
  <text x="160" y="70" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">apply(Integer,Integer)</text>

  <line x1="160" y1="80" x2="160" y2="105" stroke="#8b949e" stroke-width="2" marker-end="url(#a1)"/>
  <text x="200" y="98" fill="#8b949e" font-size="10" font-family="sans-serif">infers</text>

  <rect x="30" y="105" width="260" height="34" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="160" y="127" fill="#6db33f" font-size="12" text-anchor="middle" font-family="monospace">(a, b) -&gt; a + b</text>

  <defs><marker id="a1" markerWidth="9" markerHeight="9" refX="4" refY="7" orient="auto"><path d="M0,0 L8,0 L4,7 Z" fill="#8b949e"/></marker></defs>
</svg>

`a` and `b` are `Integer` because `apply`'s parameters are `Integer` — the lambda never has to say so itself.

## 5. Runnable example

Scenario: a small pricing calculator — evolved from a fully-inferred two-argument lambda, through the explicitly-typed equivalent shown side by side to prove they're identical, to a case where inference alone is ambiguous and an explicit type is genuinely required to resolve it.

### Level 1 — Basic

```java
import java.util.function.*;

public class InferenceBasic {
    public static void main(String[] args) {
        BiFunction<Double, Double, Double> applyDiscount = (price, rate) -> price - (price * rate);

        double result = applyDiscount.apply(100.0, 0.2);
        System.out.println("Price after 20% discount: " + result);
    }
}
```

**How to run:** `java InferenceBasic.java`

Expected output:
```
Price after 20% discount: 80.0
```

`(price, rate) -> price - (price * rate)` never declares that `price` and `rate` are `Double` — the compiler infers both from `BiFunction<Double, Double, Double>.apply(Double, Double)`, the method this lambda is implementing.

### Level 2 — Intermediate

```java
import java.util.function.*;

public class InferenceExplicitComparison {
    public static void main(String[] args) {
        // Inferred form
        BiFunction<Double, Double, Double> inferred = (price, rate) -> price - (price * rate);

        // Explicit form -- legal, identical behaviour, just more to read
        BiFunction<Double, Double, Double> explicit = (Double price, Double rate) -> price - (price * rate);

        double a = inferred.apply(200.0, 0.1);
        double b = explicit.apply(200.0, 0.1);

        System.out.println("Inferred result: " + a);
        System.out.println("Explicit result: " + b);
        System.out.println("Same result: " + (a == b));
    }
}
```

**How to run:** `java InferenceExplicitComparison.java`

Expected output:
```
Inferred result: 180.0
Explicit result: 180.0
Same result: true
```

The real-world concern demonstrated here: explicit types compile and run identically to inferred ones — there is no behavioural difference, only a verbosity difference. This confirms that leaving types out is a pure readability win with zero functional cost.

### Level 3 — Advanced

```java
import java.util.function.*;

public class InferenceAmbiguousOverload {
    // Two overloads of process -- one takes a Function, one takes a BiFunction.
    // A lambda with an unspecified single vs. two-parameter shape is unambiguous by ARITY,
    // but if a generic method's target type itself can't be pinned down, explicit types resolve it.
    static <T, R> R process(T input, Function<T, R> f) {
        return f.apply(input);
    }

    static <T, U, R> R process(T a, U b, BiFunction<T, U, R> f) {
        return f.apply(a, b);
    }

    public static void main(String[] args) {
        // Unambiguous: one argument before the lambda selects the Function overload by arity.
        String upper = process("hello", s -> s.toUpperCase());
        System.out.println(upper);

        // Unambiguous: two arguments before the lambda selects the BiFunction overload by arity.
        int sum = process(3, 4, (Integer a, Integer b) -> a + b);
        System.out.println(sum);
    }
}
```

**How to run:** `java InferenceAmbiguousOverload.java`

Expected output:
```
HELLO
7
```

Here, the lambda parameter types are inferred by matching the **number of arguments already supplied** (`"hello"` alone selects the one-`Function`-argument overload; `3, 4` selects the two-argument `BiFunction` overload) — this is how the compiler resolves which overload, and therefore which functional interface, a given lambda's parameters should be inferred against. The `(Integer a, Integer b)` explicit typing on the second lambda is written here only for clarity in a generic context; the compiler would infer `Integer` from `process`'s type parameter `T` bound to `int` (autoboxed) either way.

## 6. Walkthrough

Execution starts in `main` of the Level 3 example. The first call is `process("hello", s -> s.toUpperCase())`.

The compiler first resolves **which overload** of `process` applies: two arguments are passed (`"hello"` and the lambda), and the first `process` overload — `process(T input, Function<T, R> f)` — also takes exactly two arguments (one value, one function), matching arity. The second overload takes three arguments, so it's ruled out immediately. With the first overload selected, its second parameter type is `Function<T, R>`, and `T` is inferred as `String` from the first argument (`"hello"`) — so the lambda `s -> s.toUpperCase()` is now known to implement `Function<String, R>.apply(String)`, meaning `s` is inferred as `String`.

Inside `process`, `f.apply(input)` calls the lambda with `input = "hello"`. `s.toUpperCase()` evaluates to `"HELLO"`, which becomes both the lambda's result and `process`'s return value — printed as the first output line.

The second call, `process(3, 4, (Integer a, Integer b) -> a + b)`, supplies three arguments, selecting the second `process` overload — `process(T a, U b, BiFunction<T, U, R> f)` — by arity. `T` and `U` are both inferred as `Integer` (autoboxed from the `int` literals `3` and `4`), so the lambda implements `BiFunction<Integer, Integer, R>.apply(Integer, Integer)`. Here the parameter types were written explicitly (`Integer a, Integer b`) purely for readability in this more generic context — inference would have arrived at the identical types without them.

Inside `process`, `f.apply(a, b)` calls the lambda with `a = 3, b = 4`, computing `a + b = 7`, which is returned and printed as the second output line.

```
process("hello", lambda)   --2 args--> Function overload --> T=String  --> s inferred String
process(3, 4, lambda)      --3 args--> BiFunction overload --> T=U=Integer --> a,b inferred Integer
```

## 7. Gotchas & takeaways

> Type inference for lambda parameters works from **one direction only**: the target type flows *into* the lambda, never the other way around. A lambda alone, with no context (`var x = (a, b) -> a + b;`), cannot be inferred — the compiler needs to already know what functional interface it's implementing before it can work out the parameter types. This is why lambdas are always written in a context that supplies a target type (a variable declaration, a method argument, a return statement).

- Lambda parameter types are inferred from the target functional interface's abstract method signature — you almost never need to write them explicitly.
- Explicit types (`(String a, String b) -> ...`) are legal and behave identically, but are redundant in the vast majority of real code.
- You must be consistent within one parameter list: either type *all* parameters explicitly or type *none* of them — `(String a, b) -> ...` (mixing explicit and inferred in the same lambda) does not compile.
- Overload resolution among multiple functional-interface-accepting methods is typically settled by argument count (arity) before parameter types are even inferred.
- If inference genuinely can't resolve an ambiguous case, the compiler error will say so directly — that's the signal to add explicit types, not a habit to apply everywhere out of caution.
