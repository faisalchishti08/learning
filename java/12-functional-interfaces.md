# Java Functional Interfaces

## Overview

Functional interfaces are the foundation of Java's functional programming support. A functional interface has exactly **one abstract method** (SAM — Single Abstract Method). This makes them compatible with lambda expressions and method references. Java 8 introduced `java.util.function` with a rich set of built-in functional interfaces covering nearly every use case.

---

## 1. @FunctionalInterface

### What is it

An interface with exactly one abstract method. The `@FunctionalInterface` annotation is optional but recommended — it makes the compiler verify that the interface remains functional (has exactly one SAM). Default, static, and private methods don't count toward the SAM limit.

### Visual Diagram

```
Functional Interface = exactly 1 abstract method

@FunctionalInterface
interface MyFunc {
    int apply(int x);           ← the ONE abstract method (SAM)

    default MyFunc andThen(...) { ... }  ← default: OK, doesn't count
    static MyFunc identity() { ... }     ← static: OK, doesn't count
}

NOT functional (2 abstract methods):
interface Bad {
    void doA();
    void doB();   ← compiler error with @FunctionalInterface
}
```

### Example 1 — Custom Functional Interface

```java
@FunctionalInterface
interface Transformer {
    String transform(String input);

    // default method OK
    default Transformer andThen(Transformer after) {
        return s -> after.transform(this.transform(s));
    }
}

public class FunctionalInterfaceDemo {
    public static void main(String[] args) {
        // Lambda implements the SAM
        Transformer upper = s -> s.toUpperCase();
        Transformer exclaim = s -> s + "!";

        System.out.println(upper.transform("hello"));          // HELLO
        System.out.println(upper.andThen(exclaim).transform("hello")); // HELLO!

        // Method reference implements the SAM
        Transformer trim = String::strip;
        System.out.println(trim.transform("  hi  "));  // hi
    }
}
```

**What this does:** Any lambda or method reference that matches the SAM signature can be assigned to the functional interface. The `andThen` default method shows composition.

### Example 2 — Object Methods Don't Break SAM

```java
@FunctionalInterface
interface Processor<T> {
    T process(T input);  // the SAM

    // These are NOT abstract — don't count:
    default Processor<T> compose(Processor<T> before) {
        return t -> this.process(before.process(t));
    }

    // toString, equals, hashCode from Object — also don't count
}
```

**What this does:** Methods overriding `Object` public methods (`equals`, `hashCode`, `toString`) don't count toward the SAM requirement, so they can be declared in functional interfaces.

> ⚠️ **Pitfall:** Adding `@FunctionalInterface` to an interface with 2+ abstract methods causes a compile error — that's the whole point. Use it to catch accidental interface evolution that breaks lambda compatibility.

---

## 2. Predicate\<T\>

### What is it

Represents a boolean-valued function of one argument. Use it for filtering, testing conditions.

**Abstract method:** `boolean test(T t)`

### Composition methods: `and(Predicate)`, `or(Predicate)`, `negate()`, `Predicate.not(pred)` [Java 11+]

### Example 1 — Basic Predicate

```java
import java.util.function.*;
import java.util.*;
import java.util.stream.*;

public class PredicateDemo {
    public static void main(String[] args) {
        Predicate<Integer> isEven = n -> n % 2 == 0;
        Predicate<Integer> isPositive = n -> n > 0;

        System.out.println(isEven.test(4));     // true
        System.out.println(isEven.test(7));     // false

        // Composition
        Predicate<Integer> isEvenAndPositive = isEven.and(isPositive);
        Predicate<Integer> isEvenOrPositive  = isEven.or(isPositive);
        Predicate<Integer> isOdd = isEven.negate();

        System.out.println(isEvenAndPositive.test(4));  // true
        System.out.println(isEvenAndPositive.test(-4)); // false (negative)
        System.out.println(isOdd.test(5));              // true

        // Predicate.not [Java 11+]
        Predicate<String> isBlank = String::isBlank;
        List<String> strings = Arrays.asList("hello", "", "  ", "world");
        List<String> nonBlanks = strings.stream()
            .filter(Predicate.not(String::isBlank))
            .collect(Collectors.toList());
        System.out.println(nonBlanks); // [hello, world]
    }
}
```

**What this does:** `Predicate` is typically used with `Stream.filter()`, `Collection.removeIf()`, and conditional logic. Composition with `and/or/negate` builds complex conditions from simple ones.

### Dry Run — Predicate Composition

```java
Predicate<Integer> p = n -> n > 0;        // positive
Predicate<Integer> q = n -> n % 2 == 0;   // even
Predicate<Integer> pAndQ = p.and(q);

pAndQ.test(4):
  Step 1: p.test(4) → 4 > 0 → true
  Step 2: (p is true) → evaluate q.test(4) → 4 % 2 == 0 → true
  Result: true && true = true

pAndQ.test(-4):
  Step 1: p.test(-4) → -4 > 0 → false
  Step 2: (p is false) → SHORT-CIRCUIT, q never evaluated
  Result: false
```

---

## 3. Function\<T, R\>

### What is it

Represents a function from T to R. Maps an input to an output.

**Abstract method:** `R apply(T t)`

**Composition methods:** `andThen(Function after)` — this → after, `compose(Function before)` — before → this, `Function.identity()` — returns input unchanged

### Example 1 — Function and Composition

```java
import java.util.function.*;

public class FunctionDemo {
    public static void main(String[] args) {
        Function<String, Integer> strLen = String::length;
        Function<Integer, String> intToStr = n -> "Number: " + n;

        System.out.println(strLen.apply("hello")); // 5
        System.out.println(intToStr.apply(42));    // Number: 42

        // andThen: apply strLen THEN intToStr
        Function<String, String> combined = strLen.andThen(intToStr);
        System.out.println(combined.apply("hello")); // Number: 5

        // compose: apply strLen AFTER... wait, compose(before)
        // f.compose(g) = f(g(x))
        Function<Integer, Integer> times2 = x -> x * 2;
        Function<Integer, Integer> plus3  = x -> x + 3;
        Function<Integer, Integer> times2ThenPlus3 = plus3.compose(times2);
        // compose: apply times2 first, then plus3
        System.out.println(times2ThenPlus3.apply(5)); // (5*2)+3 = 13

        // andThen: same as compose but reversed order
        Function<Integer, Integer> andThenVersion = times2.andThen(plus3);
        System.out.println(andThenVersion.apply(5)); // same: 13

        // identity
        Function<String, String> identity = Function.identity();
        System.out.println(identity.apply("test")); // test
    }
}
```

**What this does:** `andThen(g)` means: apply `this`, then apply `g` to the result. `compose(g)` means: apply `g` first, then apply `this`. They're the mirror of each other. `Function.identity()` is useful as a no-op placeholder.

### Dry Run — andThen vs compose

```
f = x * 2     g = x + 10

f.andThen(g).apply(5):
  Step 1: f(5) = 5 * 2 = 10
  Step 2: g(10) = 10 + 10 = 20
  Result: 20

f.compose(g).apply(5):
  Step 1: g(5) = 5 + 10 = 15
  Step 2: f(15) = 15 * 2 = 30
  Result: 30
```

---

## 4. BiFunction\<T, U, R\>

### What is it

Function with two input parameters. `BiFunction<T,U,R>`: takes T and U, returns R.

**Abstract method:** `R apply(T t, U u)`

### Example 1 — BiFunction Usage

```java
import java.util.function.*;

public class BiFunctionDemo {
    public static void main(String[] args) {
        BiFunction<String, Integer, String> repeat = (s, n) -> s.repeat(n);
        System.out.println(repeat.apply("ha", 3)); // hahaha

        // andThen
        BiFunction<Integer, Integer, Integer> add = (a, b) -> a + b;
        Function<Integer, String> toStr = n -> "Sum=" + n;
        BiFunction<Integer, Integer, String> addAndFormat = add.andThen(toStr);
        System.out.println(addAndFormat.apply(3, 4)); // Sum=7

        // Map.replaceAll uses BiFunction<K,V,V>
        java.util.Map<String, Integer> scores = new java.util.HashMap<>();
        scores.put("Alice", 80); scores.put("Bob", 90);
        scores.replaceAll((name, score) -> score + 5); // bonus
        System.out.println(scores); // {Alice=85, Bob=95}
    }
}
```

**What this does:** `BiFunction` is used when you need to combine two inputs. `Map.replaceAll()` takes a `BiFunction<K,V,V>` to transform all values. `BiFunction` only has `andThen()` (no `compose` — that would need a BiFunction for the inner function).

---

## 5. Consumer\<T\> and BiConsumer\<T,U\>

### What is it

Represents an operation that accepts input and returns no result (void). Used for side effects.

**Abstract methods:** `Consumer`: `void accept(T t)`, `BiConsumer`: `void accept(T t, U u)`

**Composition:** `andThen(Consumer after)` — run this, then run after

### Example 1 — Consumer Chaining

```java
import java.util.function.*;
import java.util.*;

public class ConsumerDemo {
    public static void main(String[] args) {
        Consumer<String> print = System.out::println;
        Consumer<String> printUpper = s -> System.out.println(s.toUpperCase());

        // andThen chains consumers
        Consumer<String> both = print.andThen(printUpper);
        both.accept("hello");
        // hello
        // HELLO

        // forEach takes Consumer
        List<String> names = List.of("Alice", "Bob", "Charlie");
        names.forEach(n -> System.out.println("Hello, " + n));

        // BiConsumer
        BiConsumer<String, Integer> printWithScore =
            (name, score) -> System.out.printf("%s: %d%n", name, score);
        printWithScore.accept("Alice", 95);  // Alice: 95

        // Map.forEach uses BiConsumer<K,V>
        Map<String, Integer> map = Map.of("a", 1, "b", 2);
        map.forEach((k, v) -> System.out.println(k + "=" + v));
    }
}
```

**What this does:** `Consumer` is the right type when you want to perform a side effect but don't return a value. `forEach` on Iterable and Map takes Consumer/BiConsumer.

---

## 6. Supplier\<T\>

### What is it

Takes no input, produces a value. Used for lazy evaluation and factory patterns.

**Abstract method:** `T get()`

### Example 1 — Lazy Evaluation with Supplier

```java
import java.util.function.*;
import java.util.*;

public class SupplierDemo {
    static String expensiveOperation() {
        System.out.println("Computing...");
        return "result";
    }

    public static void main(String[] args) {
        // Eager: computed immediately even if not needed
        String eager = expensiveOperation(); // "Computing..." prints now

        // Lazy: computation deferred until get() called
        Supplier<String> lazy = () -> expensiveOperation();
        System.out.println("Before get()");
        String val = lazy.get();  // "Computing..." prints here
        System.out.println(val);  // result

        // Optional.orElseGet uses Supplier (lazy)
        Optional<String> opt = Optional.empty();
        String result = opt.orElseGet(() -> expensiveOperation()); // only computed when needed

        // vs orElse (eager — always computes):
        // opt.orElse(expensiveOperation()); // computes even if opt is present!

        // Factory pattern
        Supplier<List<String>> listFactory = ArrayList::new;
        List<String> list1 = listFactory.get();
        List<String> list2 = listFactory.get(); // different instances
        System.out.println(list1 == list2); // false
    }
}
```

**What this does:** `Supplier` defers computation until `get()` is called. Critical difference: `Optional.orElse(expr)` evaluates `expr` eagerly; `Optional.orElseGet(supplier)` evaluates lazily — only if Optional is empty.

> ⚠️ **Pitfall:** `Optional.orElse(expensiveCall())` always evaluates `expensiveCall()` — even if the Optional has a value! Use `orElseGet(() -> expensiveCall())` for expensive defaults.

---

## 7. UnaryOperator\<T\> and BinaryOperator\<T\>

### What is it

Specializations of Function/BiFunction where input and output types are the same.

```
UnaryOperator<T> extends Function<T,T>
BinaryOperator<T> extends BiFunction<T,T,T>
```

### Example 1 — Operators in Practice

```java
import java.util.function.*;
import java.util.*;

public class OperatorDemo {
    public static void main(String[] args) {
        // UnaryOperator: same type in and out
        UnaryOperator<String> trim = String::strip;
        UnaryOperator<Integer> negate = x -> -x;
        UnaryOperator<Integer> doubled = x -> x * 2;

        // List.replaceAll uses UnaryOperator
        List<String> words = new ArrayList<>(Arrays.asList("  hello  ", " world ", "  java  "));
        words.replaceAll(String::strip);
        System.out.println(words); // [hello, world, java]

        // BinaryOperator: two same-type inputs → same type output
        BinaryOperator<Integer> add = Integer::sum;
        BinaryOperator<Integer> max = BinaryOperator.maxBy(Comparator.naturalOrder());
        BinaryOperator<String> concat = (a, b) -> a + b;

        System.out.println(add.apply(3, 4));         // 7
        System.out.println(max.apply(10, 7));         // 10
        System.out.println(concat.apply("foo", "bar")); // foobar

        // Stream.reduce uses BinaryOperator
        List<Integer> nums = List.of(1, 2, 3, 4, 5);
        int sum = nums.stream().reduce(0, Integer::sum);
        System.out.println(sum); // 15
    }
}
```

**What this does:** `UnaryOperator` and `BinaryOperator` are cleaner alternatives to `Function<T,T>` and `BiFunction<T,T,T>` when types match. `List.replaceAll` uses `UnaryOperator`; `Stream.reduce` uses `BinaryOperator`.

---

## 8. Primitive Specializations

### What is it

To avoid boxing overhead, Java provides specializations for `int`, `long`, and `double`:

```
IntPredicate, LongPredicate, DoublePredicate
IntFunction<R>, LongFunction<R>, DoubleFunction<R>
IntUnaryOperator, LongUnaryOperator, DoubleUnaryOperator
IntBinaryOperator, LongBinaryOperator, DoubleBinaryOperator
IntConsumer, LongConsumer, DoubleConsumer
IntSupplier, LongSupplier, DoubleSupplier
ToIntFunction<T>, ToLongFunction<T>, ToDoubleFunction<T>
IntToDoubleFunction, IntToLongFunction, etc.
```

### Example 1 — Primitive vs Boxed Performance

```java
import java.util.function.*;
import java.util.stream.*;

public class PrimitiveSpecialization {
    public static void main(String[] args) {
        // Boxed: involves Integer boxing/unboxing
        Function<Integer, Integer> boxedDouble = n -> n * 2;

        // Primitive: no boxing
        IntUnaryOperator primitiveDouble = n -> n * 2;

        System.out.println(boxedDouble.apply(5));   // 10
        System.out.println(primitiveDouble.applyAsInt(5)); // 10

        // IntStream vs Stream<Integer>
        long sum1 = IntStream.rangeClosed(1, 1_000_000).sum();       // no boxing
        long sum2 = Stream.iterate(1, n -> n + 1)
            .limit(1_000_000)
            .mapToInt(Integer::intValue)
            .sum();

        System.out.println(sum1); // 500000500000
        System.out.println(sum2); // same result

        // ToIntFunction: convert T to int (primitive)
        ToIntFunction<String> strLen = String::length;
        System.out.println(strLen.applyAsInt("hello")); // 5
    }
}
```

**What this does:** Primitive specializations exist because autoboxing `int → Integer` for each stream element is expensive at scale. `IntStream`, `LongStream`, `DoubleStream` avoid this overhead.

---

## Quick Reference

```
Core functional interfaces:

Interface                  Method              Use case
─────────────────────────────────────────────────────────
Predicate<T>               test(T) → bool      filter, test
BiPredicate<T,U>           test(T,U) → bool    two-arg filter
Function<T,R>              apply(T) → R        transform
BiFunction<T,U,R>          apply(T,U) → R      combine two inputs
UnaryOperator<T>           apply(T) → T        transform same type
BinaryOperator<T>          apply(T,T) → T      combine same types
Consumer<T>                accept(T) → void    side effects
BiConsumer<T,U>            accept(T,U) → void  two-arg side effects
Supplier<T>                get() → T           produce value lazily
Runnable                   run() → void        no-arg no-return
Callable<T>                call() → T          no-arg, returns T, throws

Composition:
  Predicate: and(), or(), negate(), Predicate.not() [11+]
  Function:  andThen() (this→after), compose() (before→this)
  Consumer:  andThen()

Key pitfalls:
  orElse(expr)    → expr ALWAYS evaluated (eager)
  orElseGet(sup)  → supplier evaluated ONLY if empty (lazy)
  @FunctionalInterface → compile-time guard, use it
```
