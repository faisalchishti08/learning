---
card: java
gi: 68
slug: boolean-true-false
title: boolean (true/false)
---

## 1. What it is

`boolean` is Java's primitive type for logical truth values. It has exactly two possible values: `true` and `false`. Every conditional expression — `if`, `while`, `for`, `? :` — requires a `boolean`. There is no implicit "truthiness" from other types.

```java
boolean isPaid     = true;
boolean isShipped  = false;
boolean result     = isPaid && !isShipped;   // true

// Only boolean expressions in conditions — no implicit truthiness:
// if (1) { }        // ✗ compile error — not boolean
// if ("yes") { }    // ✗ compile error — not boolean
if (isPaid) { }      // ✓
```

The boxed wrapper class is `Boolean` (capital B), which allows `null` as a third state and integrates with generics.

## 2. Why & when

`boolean` is the type of all conditions and flags. It appears:
- As the result of comparison operators (`==`, `!=`, `<`, `>`, `<=`, `>=`).
- As the result of logical operators (`&&`, `||`, `!`, `^`).
- As fields representing state (`isPaid`, `isActive`, `hasChildren`).
- As method return types for predicates (`isEmpty()`, `contains()`, `matches()`).
- In `Predicate<T>` functional interfaces (which return `boolean`).

## 3. Core concept

```java
// ---- Declaration and default values ----
boolean flag;         // local: compile error if used uninitialised
class Foo {
    boolean field;    // instance field: initialised to false
    static boolean staticField;  // static field: initialised to false
}

// ---- Logical operators ----
boolean a = true, b = false;
System.out.println(a && b);   // false  — AND: both must be true
System.out.println(a || b);   // true   — OR: at least one true
System.out.println(!a);       // false  — NOT: invert
System.out.println(a ^ b);    // true   — XOR: exactly one true

// Short-circuit evaluation:
int i = 0;
boolean r = (i != 0) && (10 / i > 0);   // second part NOT evaluated (i==0 would /0)
boolean s = (i == 0) || (10 / i > 0);   // second part NOT evaluated (already true)

// Non-short-circuit (evaluates both sides always):
boolean t = (i != 0) & (10 / i > 0);    // single & — evaluates both → ArithmeticException!

// ---- Boxing: boolean → Boolean ----
Boolean boxed = Boolean.TRUE;            // cached singleton
Boolean boxed2 = Boolean.valueOf(true);  // preferred — returns cached instance
Boolean boxed3 = true;                   // autoboxing

// Unboxing NPE trap:
Boolean nullable = null;
// boolean x = nullable;   ← NullPointerException at runtime (unboxing null)

// ---- Comparison ----
boolean x = true;
boolean y = true;
System.out.println(x == y);              // true — primitive comparison, always safe
System.out.println(Boolean.TRUE == Boolean.TRUE);  // true — same cached instance
// Don't use .equals() on primitives; use == for boolean always.

// ---- Return from condition ----
// Anti-pattern:
boolean isAdult(int age) {
    if (age >= 18) return true;
    else return false;
}
// Better:
boolean isAdult2(int age) { return age >= 18; }

// ---- Predicate functional interface ----
java.util.function.Predicate<String> isLong = s -> s.length() > 5;
System.out.println(isLong.test("hello"));   // false
System.out.println(isLong.test("hello world"));  // true
```

## 4. Diagram

<svg viewBox="0 0 700 185" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="boolean type: two values true/false, logical operators &&/||/!/^, Boolean wrapper with null risk">
  <rect x="8" y="8" width="684" height="169" rx="8" fill="#0d1117"/>

  <!-- boolean primitive -->
  <rect x="16" y="20" width="180" height="140" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="106" y="38" fill="#6db33f" font-size="10" text-anchor="middle" font-family="monospace">boolean</text>
  <text x="106" y="52" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">primitive type</text>
  <line x1="26" y1="58" x2="186" y2="58" stroke="#8b949e" stroke-width="0.5"/>
  <text x="106" y="73" fill="#6db33f" font-size="14" text-anchor="middle" font-family="monospace">true  false</text>
  <text x="106" y="90" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">Only two values</text>
  <text x="26" y="107" fill="#e6edf3" font-size="7.5" font-family="monospace">default (field): false</text>
  <text x="26" y="120" fill="#e6edf3" font-size="7.5" font-family="monospace">size: JVM-dependent</text>
  <text x="26" y="133" fill="#e6edf3" font-size="7.5" font-family="monospace">no truthiness</text>
  <text x="26" y="146" fill="#8b949e" font-size="7" font-family="monospace">boolean[] → byte[]</text>

  <!-- operators -->
  <rect x="208" y="20" width="175" height="140" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="295" y="38" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">Logical operators</text>
  <line x1="218" y1="44" x2="373" y2="44" stroke="#8b949e" stroke-width="0.5"/>
  <text x="218" y="58" fill="#e6edf3" font-size="8" font-family="monospace">a &amp;&amp; b  — AND</text>
  <text x="218" y="72" fill="#e6edf3" font-size="8" font-family="monospace">a || b  — OR</text>
  <text x="218" y="86" fill="#e6edf3" font-size="8" font-family="monospace">!a     — NOT</text>
  <text x="218" y="100" fill="#e6edf3" font-size="8" font-family="monospace">a ^ b  — XOR</text>
  <line x1="218" y1="108" x2="373" y2="108" stroke="#8b949e" stroke-width="0.5"/>
  <text x="218" y="120" fill="#6db33f" font-size="7.5" font-family="monospace">&amp;&amp; || short-circuit</text>
  <text x="218" y="132" fill="#8b949e" font-size="7" font-family="monospace">&amp;  |  evaluate both</text>
  <text x="218" y="144" fill="#8b949e" font-size="7" font-family="monospace">(non-short-circuit)</text>

  <!-- Boolean wrapper -->
  <rect x="395" y="20" width="180" height="140" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="485" y="38" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="monospace">Boolean</text>
  <text x="485" y="52" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">wrapper class</text>
  <line x1="405" y1="58" x2="565" y2="58" stroke="#8b949e" stroke-width="0.5"/>
  <text x="405" y="72" fill="#e6edf3" font-size="7.5" font-family="monospace">Boolean.TRUE  (cached)</text>
  <text x="405" y="85" fill="#e6edf3" font-size="7.5" font-family="monospace">Boolean.FALSE (cached)</text>
  <text x="405" y="98" fill="#e6edf3" font-size="7.5" font-family="monospace">Boolean.valueOf(true)</text>
  <text x="405" y="111" fill="#e6edf3" font-size="7.5" font-family="monospace">null possible ← risk</text>
  <line x1="405" y1="118" x2="565" y2="118" stroke="#8b949e" stroke-width="0.5"/>
  <text x="405" y="130" fill="#8b949e" font-size="7" font-family="monospace">NPE: Boolean b = null;</text>
  <text x="405" y="143" fill="#8b949e" font-size="7" font-family="monospace">boolean x = b; // unbox NPE</text>

  <!-- condition constraint -->
  <rect x="587" y="20" width="103" height="140" rx="6" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="638" y="36" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">In conditions</text>
  <text x="638" y="50" fill="#6db33f" font-size="7.5" text-anchor="middle" font-family="monospace">if (bool) ✓</text>
  <text x="638" y="65" fill="#8b949e" font-size="7" text-anchor="middle" font-family="monospace">if (1) ✗</text>
  <text x="638" y="78" fill="#8b949e" font-size="7" text-anchor="middle" font-family="monospace">if (obj) ✗</text>
  <text x="638" y="91" fill="#8b949e" font-size="7" text-anchor="middle" font-family="monospace">if (null) ✗</text>
  <text x="638" y="108" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">Only boolean</text>
  <text x="638" y="120" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">expressions</text>
  <text x="638" y="132" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">are valid.</text>
</svg>

`boolean` has exactly two values and no implicit truthiness — only explicit boolean expressions are valid in conditions.

## 5. Runnable example

Scenario: an order eligibility checker — determines whether an order qualifies for various promotions using boolean logic, growing from simple flag checks to short-circuit evaluation and `Predicate` composition.

### Level 1 — Basic

```java
public class BooleanBasic {
    public static void main(String[] args) {
        System.out.println("=== boolean demo ===\n");

        double amount    = 299.99;
        boolean isPaid   = true;
        boolean isNew    = false;
        boolean hasPromo = true;

        // Basic logical operators
        System.out.println("isPaid:      " + isPaid);
        System.out.println("isNew:       " + isNew);
        System.out.println("hasPromo:    " + hasPromo);

        boolean eligibleForDiscount = isPaid && hasPromo;
        boolean needsAction         = !isPaid || isNew;
        boolean exclusiveOffer      = isPaid ^ isNew;   // exactly one true

        System.out.println("\neligibleForDiscount (isPaid && hasPromo): " + eligibleForDiscount);
        System.out.println("needsAction  (!isPaid || isNew):          " + needsAction);
        System.out.println("exclusiveOffer (isPaid ^ isNew):          " + exclusiveOffer);

        // Returning boolean directly — avoid if/else with return true/false
        System.out.println("\nqualifies(): " + qualifies(amount, isPaid));

        // Default value of boolean field
        BooleanBasic obj = new BooleanBasic();
        System.out.println("Unset field default: " + obj.unsetFlag);
    }

    boolean unsetFlag;   // default: false

    static boolean qualifies(double amount, boolean paid) {
        return paid && amount >= 100.0;   // not: if(paid&&amount>=100) return true; else return false;
    }
}
```

**How to run:** `java BooleanBasic.java`

`qualifies` returns the expression directly — `paid && amount >= 100.0` already produces a `boolean`. Wrapping it in `if (...) return true; else return false;` is redundant and adds noise.

### Level 2 — Intermediate

Same eligibility checker: demonstrate short-circuit evaluation saving an expensive call, Boolean wrapper NPE trap, and method reference as `Predicate<Order>`.

```java
import java.util.*;
import java.util.function.*;

public class BooleanIntermediate {

    record Order(String id, double amount, boolean paid, String region) {}

    static int callCount = 0;

    static boolean expensiveCheck(Order o) {
        callCount++;   // count how often this runs
        return o.amount() > 100.0;
    }

    public static void main(String[] args) {
        System.out.println("=== Intermediate boolean: short-circuit + Predicate ===\n");

        var orders = List.of(
            new Order("ORD-001", 299.99, true,  "EU"),
            new Order("ORD-002",  50.00, false, "US"),
            new Order("ORD-003", 150.00, true,  "EU"),
            new Order("ORD-004",  10.00, true,  "APAC")
        );

        // 1. Short-circuit: expensiveCheck only called when isPaid is true
        System.out.println("[ Short-circuit && ]");
        callCount = 0;
        for (Order o : orders) {
            boolean eligible = o.paid() && expensiveCheck(o);  // expensiveCheck skipped if !paid
            System.out.printf("  %-8s paid=%-5b  eligible=%b%n", o.id(), o.paid(), eligible);
        }
        System.out.println("  expensiveCheck called " + callCount + " times (not 4)");

        // 2. Boolean wrapper NPE trap
        System.out.println("\n[ Boolean wrapper NPE trap ]");
        Boolean nullableFlag = null;
        try {
            boolean unwrapped = nullableFlag;  // autoboxing → NPE
        } catch (NullPointerException e) {
            System.out.println("  NPE: unboxing null Boolean → NullPointerException");
        }
        // Safe check:
        boolean safe = Boolean.TRUE.equals(nullableFlag);  // false, no NPE
        System.out.println("  Boolean.TRUE.equals(null) = " + safe);

        // 3. Predicate<Order> — boolean-returning functional interface
        System.out.println("\n[ Predicate composition ]");
        Predicate<Order> isPaid      = Order::paid;
        Predicate<Order> isEU        = o -> "EU".equals(o.region());
        Predicate<Order> isHighValue = o -> o.amount() > 100.0;

        Predicate<Order> eligibleForEuPromo = isPaid.and(isEU).and(isHighValue);

        System.out.println("EU promo eligible orders:");
        orders.stream()
              .filter(eligibleForEuPromo)
              .forEach(o -> System.out.printf("  %s (£%.2f)%n", o.id(), o.amount()));
    }
}
```

**How to run:** `java BooleanIntermediate.java`

`o.paid() && expensiveCheck(o)` — if `o.paid()` is `false`, Java does not evaluate `expensiveCheck(o)` at all (short-circuit). This matters when the right-hand side has side effects or is expensive: here only 3 out of 4 orders are paid, so `expensiveCheck` is called 3 times, not 4.

### Level 3 — Advanced

Same order system: build a rule engine using `Predicate` combinators, demonstrate non-short-circuit operators (`&`, `|`) and their appropriate use (checking all conditions), and measure boolean performance with `boolean[]` vs `Boolean[]`.

```java
import java.util.*;
import java.util.function.*;
import java.util.stream.*;

public class BooleanAdvanced {

    record Order(String id, double amount, boolean paid,
                 boolean verified, String region) {}

    // Rule engine: named predicates combined with Predicate API
    record Rule(String name, Predicate<Order> predicate) {}

    public static void main(String[] args) {
        System.out.println("=== Advanced boolean: rule engine ===\n");

        var orders = List.of(
            new Order("ORD-001", 299.99, true,  true,  "EU"),
            new Order("ORD-002",  50.00, true,  false, "US"),
            new Order("ORD-003", 150.00, false, true,  "EU"),
            new Order("ORD-004", 800.00, true,  true,  "APAC")
        );

        // Named rules as Predicates
        List<Rule> rules = List.of(
            new Rule("paid",       Order::paid),
            new Rule("verified",   Order::verified),
            new Rule("highValue",  o -> o.amount() >= 200.0),
            new Rule("euRegion",   o -> "EU".equals(o.region()))
        );

        // Evaluate all rules for each order (using non-short-circuit & to always eval all)
        System.out.println("[ Rule evaluation matrix ]");
        System.out.printf("  %-10s", "Order");
        rules.forEach(r -> System.out.printf("  %-12s", r.name()));
        System.out.printf("  %s%n", "ALL-PASS");
        System.out.println("  " + "-".repeat(72));

        for (Order o : orders) {
            System.out.printf("  %-10s", o.id());
            boolean allPass = true;
            for (Rule r : rules) {
                boolean result = r.predicate().test(o);
                allPass = allPass & result;   // non-short-circuit: evaluate ALL rules
                System.out.printf("  %-12s", result ? "✓" : "✗ (" + r.name() + ")");
            }
            System.out.printf("  %b%n", allPass);
        }

        // Combine all rules into a single Predicate
        Predicate<Order> allRules = rules.stream()
            .map(Rule::predicate)
            .reduce(Predicate::and)
            .orElse(o -> true);

        System.out.println("\n[ Orders passing all rules ]");
        orders.stream()
              .filter(allRules)
              .forEach(o -> System.out.printf("  %s £%.2f%n", o.id(), o.amount()));

        // Boolean[] vs boolean[] — boxing overhead
        System.out.println("\n[ boolean[] vs Boolean[] ]");
        int n = 1_000_000;
        boolean[] primitiveArr = new boolean[n];
        Boolean[] boxedArr     = new Boolean[n];
        Arrays.fill(primitiveArr, true);
        Arrays.fill(boxedArr, Boolean.TRUE);

        long t1 = System.nanoTime();
        long trueCount1 = 0;
        for (boolean b : primitiveArr) if (b) trueCount1++;
        long t2 = System.nanoTime();
        long trueCount2 = 0;
        for (Boolean b : boxedArr) if (b) trueCount2++;   // unboxing on each access
        long t3 = System.nanoTime();

        System.out.printf("  boolean[%d]: %,d ns%n", n, t2 - t1);
        System.out.printf("  Boolean[%d]: %,d ns  (unboxing overhead)%n", n, t3 - t2);
        System.out.println("  (boolean[] is faster — no heap allocation per element)");
    }
}
```

**How to run:** `java BooleanAdvanced.java`

Using non-short-circuit `&` in the rule matrix (`allPass = allPass & result`) ensures every rule is evaluated for every order even after one fails — necessary when we want to display the full rule-by-rule breakdown. Using `&&` would skip remaining rule evaluations after the first failure, producing incorrect output for the matrix.

## 6. Walkthrough

Execution trace in `BooleanAdvanced.main`:

**Rule evaluation matrix.** For each `Order`, each `Rule.predicate().test(o)` is called in sequence. `allPass = allPass & result` uses the non-short-circuit `&` operator: even if `allPass` becomes `false` on the first failing rule, the remaining rules are still evaluated (their results printed). With `&&`, Java would skip further evaluations once `allPass` is `false`.

**`Predicate.reduce(Predicate::and)`.** `rules.stream().map(Rule::predicate)` produces a `Stream<Predicate<Order>>`. `.reduce(Predicate::and)` combines them left-to-right: `p1.and(p2).and(p3).and(p4)`. The result is a single `Predicate<Order>` that is `true` only if all four individual predicates are true. The stream `filter` then uses short-circuit — it stops evaluating sub-predicates once one fails.

**`boolean[]` vs `Boolean[]`.** Each `Boolean` object in `boxedArr` is a heap-allocated reference (though `Boolean.TRUE` and `Boolean.FALSE` are cached singletons, so `Arrays.fill(boxedArr, Boolean.TRUE)` fills with the same reference). The loop `for (Boolean b : boxedArr) if (b)` unboxes each `Boolean` to `boolean` on access. `boolean[]` stores raw bits — no object references, no heap indirection, faster iteration by cache locality.

## 7. Gotchas & takeaways

> **Unboxing a `null` Boolean throws `NullPointerException`.** `Boolean flag = null; if (flag) { }` compiles fine but throws at runtime. Use `Boolean.TRUE.equals(flag)` for null-safe comparison, or `Objects.equals(flag, Boolean.TRUE)`.

> **`&` and `|` on booleans are non-short-circuit — they always evaluate both sides.** Use `&&` and `||` unless you have a specific reason to force evaluation of both sides (e.g., recording all failures in a rule matrix). The non-short-circuit form can cause `ArithmeticException` or `NullPointerException` on the right-hand side even when the left-hand side already determines the result.

- `boolean` has exactly two values: `true` and `false`. No truthiness from other types.
- `&&` / `||` short-circuit — the right operand is not evaluated if the left determines the result.
- `&` / `|` on booleans are non-short-circuit — both sides always evaluated.
- Instance/static fields of type `boolean` default to `false`; local variables must be initialised before use.
- Return conditions directly: `return age >= 18;` not `if (age >= 18) return true; else return false;`.
- `Boolean` (boxed) can be `null` — unboxing `null` throws `NPE`.
- `Predicate<T>` is the functional interface for `boolean`-valued functions; compose with `.and()`, `.or()`, `.negate()`.
