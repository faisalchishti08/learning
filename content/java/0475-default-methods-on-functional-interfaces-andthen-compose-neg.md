---
card: java
gi: 475
slug: default-methods-on-functional-interfaces-andthen-compose-neg
title: Default methods on functional interfaces (andThen, compose, negate, and, or)
---

## 1. What it is

The functional interfaces in `java.util.function` come with a handful of `default` methods — `andThen` and `compose` on `Function`; `negate`, `and`, and `or` on `Predicate` — that let you **combine** existing lambdas into new ones, without writing the combined logic by hand. Because they're `default` methods (methods with a body, defined right on the interface), they don't count against the "exactly one abstract method" rule for functional interfaces, so every implementation — lambda or otherwise — gets them for free.

## 2. Why & when

Without these combinators, combining two behaviors would mean writing a brand-new lambda that manually calls both — `x -> g.apply(f.apply(x))` instead of `f.andThen(g)`, or `x -> p1.test(x) && p2.test(x)` instead of `p1.and(p2)`. That manual version works, but it hides the *structure* of what's happening (chaining, negating, combining) behind ordinary-looking code, and it has to be rewritten every time you want a similar combination. The default methods make combination a named, reusable operation: `f.andThen(g)` says "do `f`, then `g`" as clearly as English.

You reach for these methods whenever you have two or more lambdas that logically build on each other: transformation pipelines (`andThen`/`compose` on `Function`), multi-part validation (`and`/`or`/`negate` on `Predicate`), or multi-step side effects (`andThen` on `Consumer`, covered in its own topic). They're most valuable when each individual piece is meaningful on its own and worth keeping separately named and testable, rather than folded into one large, harder-to-read lambda.

## 3. Core concept

```java
import java.util.function.*;

Function<Integer, Integer> doubleIt = n -> n * 2;
Function<Integer, Integer> addTen = n -> n + 10;

// andThen: apply THIS function, then feed the result into the argument function
Function<Integer, Integer> doubleThenAddTen = doubleIt.andThen(addTen);
System.out.println(doubleThenAddTen.apply(5)); // (5*2)+10 = 20

// compose: apply the ARGUMENT function first, then this one
Function<Integer, Integer> addTenThenDouble = doubleIt.compose(addTen);
System.out.println(addTenThenDouble.apply(5)); // (5+10)*2 = 30

Predicate<Integer> isPositive = n -> n > 0;
Predicate<Integer> isEven = n -> n % 2 == 0;
System.out.println(isPositive.and(isEven).test(4));      // true
System.out.println(isPositive.negate().test(4));         // false
System.out.println(isPositive.or(isEven).test(-4));      // true: -4 is even, even though not positive
```

`andThen` and `compose` differ only in **order**: `f.andThen(g)` runs `f` first, `g` second; `f.compose(g)` runs `g` first, `f` second — the same two functions, opposite pipeline direction.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="andThen runs this function first then the argument; compose runs the argument first then this function -- opposite pipeline directions for the same two functions">
  <rect x="8" y="8" width="624" height="154" rx="8" fill="#0d1117"/>
  <text x="20" y="30" fill="#6db33f" font-size="11" font-family="sans-serif">doubleIt.andThen(addTen)</text>
  <rect x="20" y="40" width="130" height="30" rx="4" fill="#1c2430" stroke="#6db33f"/><text x="85" y="60" fill="#6db33f" font-size="9" text-anchor="middle" font-family="monospace">doubleIt (this)</text>
  <line x1="150" y1="55" x2="195" y2="55" stroke="#8b949e" stroke-width="2" marker-end="url(#a1)"/>
  <rect x="200" y="40" width="130" height="30" rx="4" fill="#1c2430" stroke="#6db33f"/><text x="265" y="60" fill="#6db33f" font-size="9" text-anchor="middle" font-family="monospace">addTen (arg)</text>

  <text x="20" y="105" fill="#79c0ff" font-size="11" font-family="sans-serif">doubleIt.compose(addTen)</text>
  <rect x="20" y="115" width="130" height="30" rx="4" fill="#1c2430" stroke="#79c0ff"/><text x="85" y="135" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="monospace">addTen (arg)</text>
  <line x1="150" y1="130" x2="195" y2="130" stroke="#8b949e" stroke-width="2" marker-end="url(#a1)"/>
  <rect x="200" y="115" width="130" height="30" rx="4" fill="#1c2430" stroke="#79c0ff"/><text x="265" y="135" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="monospace">doubleIt (this)</text>

  <defs><marker id="a1" markerWidth="9" markerHeight="9" refX="4" refY="7" orient="auto"><path d="M0,0 L8,0 L4,7 Z" fill="#8b949e"/></marker></defs>
</svg>

Same two functions, opposite order — `andThen` reads left-to-right in the order you wrote it; `compose` reads inside-out, like nested function calls.

## 5. Runnable example

Scenario: a text-cleaning pipeline for user-submitted tags — evolved from `andThen` chaining several transformations in sequence, through `compose` producing a genuinely different result from the same two functions in the opposite order, to combining `Predicate`s with `and`/`or`/`negate` to validate the cleaned tags.

### Level 1 — Basic

```java
import java.util.function.*;

public class DefaultMethodsAndThen {
    public static void main(String[] args) {
        Function<String, String> trim = String::trim;
        Function<String, String> lowercase = String::toLowerCase;
        Function<String, String> removeSpaces = s -> s.replace(" ", "-");

        Function<String, String> cleanTag = trim.andThen(lowercase).andThen(removeSpaces);

        System.out.println(cleanTag.apply("  Java Tutorials  "));
    }
}
```

**How to run:** `java DefaultMethodsAndThen.java`

Expected output:
```
java-tutorials
```

`trim.andThen(lowercase).andThen(removeSpaces)` builds a single `Function<String, String>` that runs all three steps in the exact order written: trim first, then lower-case, then replace spaces with hyphens — each `andThen` call feeds the previous function's result into the next.

### Level 2 — Intermediate

```java
import java.util.function.*;

public class DefaultMethodsCompose {
    public static void main(String[] args) {
        Function<Integer, Integer> doubleIt = n -> n * 2;
        Function<Integer, Integer> addTen = n -> n + 10;

        // Same two functions, OPPOSITE order -- andThen vs compose give genuinely different results.
        Function<Integer, Integer> doubleThenAddTen = doubleIt.andThen(addTen);
        Function<Integer, Integer> addTenThenDouble = doubleIt.compose(addTen);

        System.out.println("andThen:  " + doubleThenAddTen.apply(5));
        System.out.println("compose:  " + addTenThenDouble.apply(5));
    }
}
```

**How to run:** `java DefaultMethodsCompose.java`

Expected output:
```
andThen:  20
compose:  30
```

The real-world concern this shows: `doubleIt.andThen(addTen)` computes `(5 * 2) + 10 = 20` (double, then add ten), while `doubleIt.compose(addTen)` computes `(5 + 10) * 2 = 30` (add ten, then double) — the exact same two functions, `doubleIt` and `addTen`, produce genuinely different results purely because `andThen` and `compose` chain them in opposite order. Getting this backward is a common and easy mistake; always double-check which direction you actually need.

### Level 3 — Advanced

```java
import java.util.function.*;
import java.util.*;

public class DefaultMethodsPredicateValidation {
    public static void main(String[] args) {
        Function<String, String> cleanTag = ((Function<String, String>) String::trim)
                .andThen(String::toLowerCase)
                .andThen(s -> s.replace(" ", "-"));

        Predicate<String> notEmpty = s -> !s.isEmpty();
        Predicate<String> notTooLong = s -> s.length() <= 20;
        Predicate<String> noDigits = s -> s.chars().noneMatch(Character::isDigit);

        // Combine three independent conditions into one, using and() -- reads like the actual rule.
        Predicate<String> isValidTag = notEmpty.and(notTooLong).and(noDigits);

        String[] rawTags = { "  Java Basics  ", "  ", "  this tag has way too many characters in it  ", "  v2 syntax  " };

        for (String raw : rawTags) {
            String cleaned = cleanTag.apply(raw);
            System.out.println("\"" + cleaned + "\" valid: " + isValidTag.test(cleaned));
        }
    }
}
```

**How to run:** `java DefaultMethodsPredicateValidation.java`

Expected output:
```
"java-basics" valid: true
"" valid: false
"this-tag-has-way-too-many-characters-in-it" valid: false
"v2-syntax" valid: false
```

This combines both kinds of combinators in one pipeline: `cleanTag` is built with `Function.andThen` (a transformation pipeline), and `isValidTag` is built with `Predicate.and` (a validation pipeline) — each condition (`notEmpty`, `notTooLong`, `noDigits`) stays independently readable, while `isValidTag` itself reads almost exactly like the rule it enforces: "not empty, and not too long, and has no digits."

## 6. Walkthrough

Execution starts in `main` of the Level 3 example. `cleanTag` and `isValidTag` are built once, before the loop. `rawTags` holds four test strings.

The loop processes each raw tag in order. For `"  Java Basics  "`: `cleanTag.apply(raw)` runs `trim` (removing surrounding spaces, giving `"Java Basics"`), then `toLowerCase` (giving `"java basics"`), then the space-replacement lambda (giving `"java-basics"`). `isValidTag.test("java-basics")` then evaluates `notEmpty.and(notTooLong).and(noDigits)`: `notEmpty` is `true` (non-empty), `notTooLong` is `true` (11 characters, under 20), `noDigits` is `true` (no digit characters) — all three `and`-chained conditions pass, so `isValidTag` returns `true`.

For `"  "`: `cleanTag.apply` trims to `""`, lower-cases to `""`, and space-replacement leaves it `""`. `isValidTag.test("")`: `notEmpty` is `false` immediately — `and` short-circuits here (Java's `&&`-based `and` implementation doesn't evaluate the rest once one condition fails), so `isValidTag` returns `false` without even checking `notTooLong` or `noDigits`.

For the long tag: after cleaning, the trimmed, lower-cased, hyphenated result is 43 characters long. `notEmpty` passes, but `notTooLong` (`length() <= 20`) fails at 43 characters, so `and` short-circuits again and `isValidTag` returns `false`.

For `"  v2 syntax  "`: cleaning produces `"v2-syntax"`. `notEmpty` passes, `notTooLong` passes (9 characters), but `noDigits` fails — `'2'` is a digit character in the cleaned string — so `isValidTag` returns `false`.

```
"  Java Basics  "  --cleanTag--> "java-basics"   --isValidTag--> notEmpty&notTooLong&noDigits all true --> true
"  "               --cleanTag--> ""              --isValidTag--> notEmpty false, short-circuit         --> false
long tag           --cleanTag--> 43 chars         --isValidTag--> notTooLong false, short-circuit       --> false
"  v2 syntax  "    --cleanTag--> "v2-syntax"      --isValidTag--> noDigits false ('2')                  --> false
```

Each iteration prints the cleaned tag and whether it's valid, matching this trace exactly.

## 7. Gotchas & takeaways

> `Predicate.and`/`or` short-circuit exactly like Java's `&&`/`||` operators — the second predicate is never evaluated if the first already determines the result. This matters if the second predicate has a side effect, or if it would throw an exception on certain inputs that the first predicate is specifically designed to filter out first (a common, deliberate pattern: `notNull.and(value -> value.someMethod())`, where `notNull` guards against a `NullPointerException` the second predicate would otherwise throw).

- `Function.andThen(after)` runs the original function first, then feeds its result into `after`; `Function.compose(before)` runs `before` first, then feeds its result into the original — opposite chaining directions for the same two functions.
- `Predicate.and`/`or`/`negate` combine boolean conditions declaratively, short-circuiting exactly like `&&`/`||`, letting you build complex validation out of small, independently named and testable pieces.
- These are all `default` methods — they come free on every `Function`/`Predicate` implementation, lambda or otherwise, and don't count toward a functional interface's single-abstract-method requirement.
- Watch the difference between `andThen` and `compose` carefully — they use the exact same two functions but produce different pipelines, and picking the wrong one is a subtle, easy-to-miss bug.
- Building small, named, reusable functions/predicates and combining them with these default methods is generally more readable and more testable than writing one large lambda that mixes several concerns together.
