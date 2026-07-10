---
card: java
gi: 972
slug: function-composition-currying
title: Function composition & currying
---

## 1. What it is

Function composition is combining two functions so that one's output feeds directly into the other's input, producing a single new function — Java's `Function<T, R>` interface provides this directly via two default methods, `andThen` (apply this function, then the other, on the result) and `compose` (apply the other function first, then this one) — `f.andThen(g)` and `g.compose(f)` both produce the same combined function, `x -> g(f(x))`, differing only in which side of the expression you find more natural to read for a given case. Currying is a related but distinct technique: transforming a function that takes multiple arguments into a chain of functions, each taking exactly one argument and returning another function — in Java, this is expressed with nested lambdas, where a function like `(a, b) -> a + b` (taking two arguments at once) becomes `a -> b -> a + b` (a function of `a` that *returns* a function of `b`), letting you supply arguments one at a time and get back a specialized, partially-applied function after supplying just the first.

## 2. Why & when

Composition matters whenever you're building a data-processing pipeline out of small, independently-testable, reusable steps — rather than writing one large function mixing validation, transformation, and formatting together, you write three small pure functions and compose them into the final pipeline, keeping each piece independently understandable and testable in isolation. Currying is most useful for creating specialized, partially-configured functions from a more general one — a curried `multiplier = a -> b -> a * b` lets you write `Function<Integer, Integer> triple = multiplier.apply(3);` once, and reuse `triple` repeatedly wherever you need "multiply by 3 specifically," without needing to repeat the `3` at every call site or write a separate, dedicated `tripleValue` method by hand. Both techniques matter most in code that treats functions as ordinary values to be built, combined, stored, and passed around — exactly what [higher-order functions](0973-higher-order-functions.md) formalizes as its own topic, and what streams and functional interfaces throughout the JDK are built around.

## 3. Core concept

```java
Function<Integer, Integer> addOne = x -> x + 1;
Function<Integer, Integer> doubleIt = x -> x * 2;

// COMPOSITION: combine two functions into one
Function<Integer, Integer> addThenDouble = addOne.andThen(doubleIt); // (x+1)*2
Function<Integer, Integer> doubleThenAdd = addOne.compose(doubleIt); // (x*2)+1

addThenDouble.apply(3);  // (3+1)*2 = 8
doubleThenAdd.apply(3);  // (3*2)+1 = 7

// CURRYING: a two-argument function expressed as a chain of one-argument functions
Function<Integer, Function<Integer, Integer>> multiplier = a -> b -> a * b;

Function<Integer, Integer> triple = multiplier.apply(3); // PARTIALLY APPLIED -- "a" is fixed at 3
triple.apply(4);   // 3 * 4 = 12
triple.apply(10);  // 3 * 10 = 30 -- reuse the specialized function repeatedly
```

`andThen`/`compose` combine two already-complete, single-argument functions into a new one; currying restructures a *multi-argument* function into a chain of single-argument functions, enabling partial application — supplying some arguments now and the rest later.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Composition chaining addOne into doubleIt via andThen, versus currying a two-argument multiply function into a chain that produces a reusable, partially-applied triple function" >
  <text x="160" y="16" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Composition (andThen)</text>
  <rect x="20" y="30" width="90" height="30" fill="#1c2430" stroke="#79c0ff"/>
  <text x="65" y="49" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">addOne</text>
  <rect x="130" y="30" width="90" height="30" fill="#1c2430" stroke="#6db33f"/>
  <text x="175" y="49" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">doubleIt</text>
  <line x1="110" y1="45" x2="130" y2="45" stroke="#8b949e" marker-end="url(#a)"/>
  <text x="145" y="80" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">3 -&gt; 4 -&gt; 8</text>

  <text x="490" y="16" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Currying + partial application</text>
  <rect x="380" y="30" width="90" height="30" fill="#1c2430" stroke="#f0883e"/>
  <text x="425" y="49" fill="#f0883e" font-size="9" text-anchor="middle" font-family="sans-serif">a -&gt; (b -&gt; a*b)</text>
  <rect x="380" y="70" width="90" height="30" fill="#1c2430" stroke="#e6edf3"/>
  <text x="425" y="89" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">triple = apply(3)</text>
  <rect x="490" y="70" width="90" height="30" fill="#1c2430" stroke="#e6edf3"/>
  <text x="535" y="89" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">triple(4)=12</text>
  <line x1="425" y1="60" x2="425" y2="70" stroke="#8b949e" marker-end="url(#a)"/>
  <line x1="470" y1="85" x2="490" y2="85" stroke="#8b949e" marker-end="url(#a)"/>
</svg>

*Composition chains complete functions together; currying restructures a multi-argument function so arguments can be supplied one at a time, yielding reusable, partially-applied functions.*

## 5. Runnable example

Scenario: build a small text-processing pipeline, evolving from basic composition of two transformation steps, to a realistic multi-step composed pipeline, to a more advanced case using currying to produce reusable, partially-configured validation functions.

### Level 1 — Basic

```java
import java.util.function.*;

public class CompositionBasic {
    public static void main(String[] args) {
        Function<String, String> trim = String::trim;
        Function<String, String> upper = String::toUpperCase;

        Function<String, String> trimThenUpper = trim.andThen(upper);

        System.out.println(trimThenUpper.apply("  hello world  "));
    }
}
```

**How to run:** `java CompositionBasic.java` (JDK 17+).

Expected output:
```
HELLO WORLD
```

`trim.andThen(upper)` produces a single combined function: apply `trim` first, then feed its result into `upper` — `"  hello world  "` is trimmed to `"hello world"`, then uppercased to `"HELLO WORLD"`, all through one composed function rather than two separate, manually-sequenced calls.

### Level 2 — Intermediate

```java
import java.util.function.*;

public class CompositionPipeline {
    public static void main(String[] args) {
        Function<String, String> trim = String::trim;
        Function<String, String> collapseSpaces = s -> s.replaceAll("\\s+", " ");
        Function<String, String> titleCase = s -> {
            String[] words = s.split(" ");
            StringBuilder sb = new StringBuilder();
            for (String w : words) {
                if (!w.isEmpty()) {
                    sb.append(Character.toUpperCase(w.charAt(0))).append(w.substring(1).toLowerCase()).append(" ");
                }
            }
            return sb.toString().trim();
        };

        Function<String, String> pipeline = trim.andThen(collapseSpaces).andThen(titleCase);

        System.out.println(pipeline.apply("  hello    WORLD   from   JAVA  "));
    }
}
```

**How to run:** `java CompositionPipeline.java` (JDK 17+).

Expected output:
```
Hello World From Java
```

The real-world concern added: three independent, individually-testable pure functions (`trim`, `collapseSpaces`, `titleCase`) are chained via repeated `andThen` calls into one readable pipeline, applied left to right — each function's role stays focused and simple, and the overall pipeline's behavior is just the composition of each step's own well-defined behavior, in order.

### Level 3 — Advanced

```java
import java.util.function.*;

public class CurryingValidators {
    public static void main(String[] args) {
        // Curried: a function of (min) that returns a function of (value)
        Function<Integer, Function<Integer, Boolean>> atLeast = min -> value -> value >= min;

        // Partially applying "atLeast" with specific minimums produces REUSABLE, named validators.
        Function<Integer, Boolean> isAdult = atLeast.apply(18);
        Function<Integer, Boolean> isSenior = atLeast.apply(65);

        int[] ages = {12, 18, 40, 65, 70};
        for (int age : ages) {
            System.out.println(age + ": adult=" + isAdult.apply(age) + ", senior=" + isSenior.apply(age));
        }
    }
}
```

**How to run:** `java CurryingValidators.java` (JDK 17+).

Expected output:
```
12: adult=false, senior=false
18: adult=true, senior=false
40: adult=true, senior=false
65: adult=true, senior=true
70: adult=true, senior=true
```

The production-flavored hard case: `atLeast` is curried — instead of taking `(min, value)` as two arguments at once, it takes `min` first and returns a specialized function of `value` — partially applying it once with `18` and once with `65` produces two genuinely reusable, independently-named validator functions (`isAdult`, `isSenior`), each callable repeatedly across the entire `ages` array without ever needing to repeat the threshold value at each call site, demonstrating currying's core practical benefit: producing specialized functions from a single general template.

## 6. Walkthrough

Tracing `atLeast.apply(18)` and its subsequent use end to end from `CurryingValidators.main`:

1. `atLeast` is declared as `Function<Integer, Function<Integer, Boolean>>` — a function that, given an `Integer`, returns *another function*, one that itself takes an `Integer` and returns a `Boolean`; this nested-function-returning-a-function shape is exactly what currying means in practice.
2. `atLeast.apply(18)` invokes the outer function with `min = 18` — its body, `value -> value >= min`, is a lambda expression that captures `min` (bound to `18`) from its enclosing scope and returns *this specific lambda* as the result; `isAdult` is now bound to this returned function, which has `min` permanently fixed at `18` from this point onward.
3. Similarly, `atLeast.apply(65)` invokes the outer function again, this time with `min = 65`, producing an entirely separate lambda (a distinct object) with `min` fixed at `65`, bound to `isSenior` — `isAdult` and `isSenior` are two independent, specialized functions, each carrying its own captured `min` value.
4. The loop iterates over `ages`; for the first value, `12`, `isAdult.apply(12)` evaluates the captured lambda's body, `value >= min`, substituting `value = 12` and the captured `min = 18`, giving `12 >= 18`, which is `false`.
5. `isSenior.apply(12)` similarly evaluates `12 >= 65` (using `isSenior`'s own captured `min = 65`), also `false` — both results are printed together for age `12`.
6. This process repeats for each subsequent age in the array — for `65`, `isAdult.apply(65)` evaluates `65 >= 18` (`true`), and `isSenior.apply(65)` evaluates `65 >= 65` (`true`), both printed as `true` — demonstrating that `isAdult` and `isSenior`, despite being created from the exact same curried `atLeast` template, behave as genuinely independent, differently-configured functions, each remembering its own specific threshold from the moment it was partially applied.

## 7. Gotchas & takeaways

> **Gotcha:** chaining many `andThen`/`compose` calls into a very long pipeline can become hard to debug, since a failure deep inside the chain (an exception thrown by one of the composed functions) reports a stack trace pointing into the internal machinery of `Function`'s default methods, not a clearly-named step in your pipeline; for long or complex pipelines, consider naming and testing each intermediate function independently (as the pipeline example does with `trim`, `collapseSpaces`, `titleCase`) rather than inlining everything as anonymous lambdas directly inside the chain, so a failure is easier to localize.

- `Function.andThen(other)` composes two functions so `other` runs on the first function's result; `Function.compose(other)` runs `other` first, feeding its result into the original function — both produce a new, single combined function.
- Currying restructures a multi-argument operation into a chain of single-argument functions, each returning the next function in the chain, expressed in Java as nested lambdas.
- Partial application — supplying a curried function's first argument and keeping the resulting specialized function around for reuse — is currying's main practical payoff, producing focused, reusable, independently-configured functions from one general template.
- Composition is best used to build readable pipelines out of small, independently-testable pure functions, rather than one large function mixing several concerns together.
- Very long composition chains can make debugging harder, since a failure's stack trace points into `Function`'s internal machinery rather than a clearly-named pipeline step — naming and testing intermediate functions separately mitigates this.
- See [higher-order functions](0973-higher-order-functions.md) for the broader concept of treating functions as ordinary values (passed to, returned from, and stored alongside other functions) that composition and currying both build directly on.
