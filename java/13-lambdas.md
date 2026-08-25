# Java Lambdas

## Overview

Lambdas are anonymous functions — a concise way to implement functional interfaces without the boilerplate of anonymous inner classes. Introduced in Java 8, they enable functional programming patterns in Java and are the backbone of streams, comparators, and event handling.

---

## 1. Lambda Syntax

### What is it

A lambda expression provides an inline implementation of a functional interface's single abstract method. It has three parts: parameters, arrow `->`, and body.

### Visual Diagram — Syntax Forms

```
(parameters) -> expression          // single expression, implicit return
(parameters) -> { statements; }     // block body, explicit return required

Examples:
  () -> 42                          // no params, returns int
  x -> x * 2                        // one param (parens optional), returns int
  (x, y) -> x + y                   // two params
  (int x, int y) -> x + y           // explicit types (optional)
  (x, y) -> { int sum = x+y; return sum; }  // block body
  x -> { System.out.println(x); }   // void return, no return statement needed
```

### Example 1 — All Lambda Forms

```java
import java.util.function.*;
import java.util.*;

public class LambdaSyntax {
    public static void main(String[] args) {
        // No parameters
        Runnable r = () -> System.out.println("Hello");
        r.run(); // Hello

        // One parameter — parens optional
        Consumer<String> print1 = s -> System.out.println(s);
        Consumer<String> print2 = (s) -> System.out.println(s); // same
        print1.accept("World");

        // Two parameters
        BiFunction<Integer, Integer, Integer> add = (a, b) -> a + b;
        System.out.println(add.apply(3, 4)); // 7

        // Block body — explicit return
        Function<Integer, String> classify = n -> {
            if (n > 0) return "positive";
            if (n < 0) return "negative";
            return "zero";
        };
        System.out.println(classify.apply(-5)); // negative

        // Type inference — types inferred from target type
        Comparator<String> byLength = (s1, s2) -> s1.length() - s2.length();
        List<String> words = new ArrayList<>(Arrays.asList("banana", "kiwi", "fig", "apple"));
        words.sort(byLength);
        System.out.println(words); // [fig, kiwi, apple, banana]
    }
}
```

**What this does:** The compiler infers parameter types from the target functional interface. Single-param lambdas can omit parentheses. Block bodies need explicit `return`. Single-expression bodies return implicitly.

### Example 2 — Lambdas Replace Anonymous Classes

```java
import java.util.*;

public class LambdaVsAnonymous {
    public static void main(String[] args) {
        // Pre-Java 8: anonymous class
        Comparator<String> oldWay = new Comparator<String>() {
            @Override
            public int compare(String s1, String s2) {
                return s1.compareTo(s2);
            }
        };

        // Java 8+: lambda (same behavior)
        Comparator<String> newWay = (s1, s2) -> s1.compareTo(s2);

        // Even better: method reference
        Comparator<String> bestWay = String::compareTo;

        List<String> list = new ArrayList<>(Arrays.asList("c", "a", "b"));
        list.sort(bestWay);
        System.out.println(list); // [a, b, c]
    }
}
```

**What this does:** Lambda reduces anonymous class boilerplate from 6 lines to 1. All three versions are functionally identical. Method reference is even cleaner when the lambda just delegates.

---

## 2. Variable Capture and Effectively Final

### What is it

Lambdas can **capture** (access) variables from their enclosing scope. Local variables must be **effectively final** (assigned exactly once, never changed). Instance fields and static fields have no restriction.

### Visual Diagram — What Lambdas Can Capture

```
class Outer {
    static int staticField = 1;   ← can access and MODIFY freely
    int instanceField = 2;         ← can access and MODIFY freely

    void method() {
        int localVar = 3;          ← can access ONLY if effectively final
        int[] mutableRef = {4};    ← can access; ref is final, array contents mutable

        Runnable r = () -> {
            System.out.println(staticField);   // OK
            System.out.println(instanceField); // OK (accessed via Outer.this)
            System.out.println(localVar);      // OK — effectively final
            // localVar++;                     // COMPILE ERROR — modifies local
            mutableRef[0]++;                   // OK — ref is final, modifying contents
        };
    }
}
```

### Example 1 — Effectively Final

```java
public class EffectivelyFinal {
    private int instanceCount = 0;

    public void demo() {
        int x = 10;           // effectively final (never reassigned)
        String name = "Alice"; // effectively final

        Runnable r1 = () -> System.out.println(x + " " + name); // OK
        r1.run(); // 10 Alice

        // x = 20;  // would make x non-final → compile error on lambda above

        // Instance fields: no restriction
        Runnable r2 = () -> {
            instanceCount++;        // OK — instance field, not local
            System.out.println(instanceCount);
        };
        r2.run(); // 1
        r2.run(); // 2
    }

    public static void main(String[] args) {
        new EffectivelyFinal().demo();
    }
}
```

**What this does:** `x` and `name` are effectively final because they're never reassigned after initialization. The lambda captures a copy of the local variable's value (or reference). Instance fields are accessed through the enclosing `this` reference, which is captured.

### Example 2 — Workaround for "Mutable" Capture

```java
import java.util.function.*;

public class MutableCapture {
    public static void main(String[] args) {
        // Can't increment a captured int directly
        // int count = 0;
        // Runnable r = () -> count++;  // COMPILE ERROR

        // Workaround 1: single-element array (reference is final, contents mutable)
        int[] count = {0};
        Runnable increment = () -> count[0]++;
        increment.run();
        increment.run();
        System.out.println(count[0]); // 2

        // Workaround 2: AtomicInteger (thread-safe)
        java.util.concurrent.atomic.AtomicInteger atomicCount = new java.util.concurrent.atomic.AtomicInteger(0);
        Runnable atomicIncrement = () -> atomicCount.incrementAndGet();
        atomicIncrement.run();
        atomicIncrement.run();
        System.out.println(atomicCount.get()); // 2

        // Workaround 3: use instance field (if in a class)
    }
}
```

**What this does:** The effectively-final restriction exists for thread safety and closure correctness. Workarounds exist but should be used carefully — `AtomicInteger` is the thread-safe option; array workaround is not thread-safe.

> ⚠️ **Pitfall:** Using array workaround `int[] count = {0}` in parallel streams is a data race. Use `AtomicInteger` or proper collectors for concurrent counting.

---

## 3. Lambda vs Anonymous Class

### Key Differences

```
Feature              | Lambda                     | Anonymous Class
---------------------|----------------------------|---------------------------
this keyword         | enclosing class's this     | the anonymous class instance
Can have fields      | NO                         | YES
Can capture locals   | effectively final only     | effectively final only
Serializable         | with caution               | if implements Serializable
Can extend classes   | NO (only functional iface) | YES
Multiple methods     | NO (only SAM)              | YES (any interface/class)
Performance          | slightly faster (no class) | creates class file
```

### Example 1 — this Semantics Differ

```java
public class ThisSemantics {
    String name = "Outer";

    void demo() {
        // Anonymous class: this refers to the anonymous class
        Runnable anonymous = new Runnable() {
            String name = "Anonymous";
            @Override
            public void run() {
                System.out.println(this.name);         // Anonymous
                System.out.println(ThisSemantics.this.name); // Outer (qualified)
            }
        };

        // Lambda: this refers to enclosing ThisSemantics instance
        Runnable lambda = () -> {
            System.out.println(this.name);  // Outer (lambda has no own this)
        };

        anonymous.run(); // Anonymous
        lambda.run();    // Outer
    }

    public static void main(String[] args) {
        new ThisSemantics().demo();
    }
}
```

**What this does:** This is the most important semantic difference. In a lambda, `this` refers to the enclosing instance. In an anonymous class, `this` refers to the anonymous class itself. Bugs arise when expecting `this` to mean the outer class inside an anonymous class.

---

## 4. Method References — All 4 Types

### What is it

Method references are a shorthand for lambdas that simply call an existing method. Four forms exist.

### Visual Diagram — 4 Types

```
Type 1 — Static method reference:
  ClassName::staticMethod
  lambda: (args) -> ClassName.staticMethod(args)
  e.g.: Integer::parseInt  =  s -> Integer.parseInt(s)

Type 2 — Instance method of particular object:
  instance::instanceMethod
  lambda: (args) -> instance.instanceMethod(args)
  e.g.: System.out::println  =  x -> System.out.println(x)
        myObj::process        =  s -> myObj.process(s)

Type 3 — Instance method of arbitrary object (of a particular type):
  ClassName::instanceMethod
  lambda: (obj, args) -> obj.instanceMethod(args)   ← first param becomes receiver!
  e.g.: String::toUpperCase  =  s -> s.toUpperCase()
        String::compareTo    =  (s1,s2) -> s1.compareTo(s2)

Type 4 — Constructor reference:
  ClassName::new
  lambda: (args) -> new ClassName(args)
  e.g.: ArrayList::new       =  () -> new ArrayList<>()
        Person::new           =  (name,age) -> new Person(name,age)
```

### Example 1 — All 4 Types Demonstrated

```java
import java.util.*;
import java.util.function.*;
import java.util.stream.*;

public class MethodReferences {
    record Person(String name, int age) {}

    static int compareByAge(Person a, Person b) {
        return Integer.compare(a.age(), b.age());
    }

    public static void main(String[] args) {
        // Type 1: Static method reference
        Function<String, Integer> parseInt = Integer::parseInt;  // ClassName::staticMethod
        System.out.println(parseInt.apply("42")); // 42

        // Type 2: Instance method of particular object
        String prefix = "Hello, ";
        Function<String, String> greet = prefix::concat;  // instance::method
        System.out.println(greet.apply("Alice")); // Hello, Alice

        // Type 3: Instance method of arbitrary object
        Function<String, String> upper = String::toUpperCase;  // ClassName::instanceMethod
        Comparator<String> compare = String::compareTo;        // first arg becomes receiver
        List<String> words = new ArrayList<>(Arrays.asList("banana", "apple", "cherry"));
        words.sort(String::compareTo);
        System.out.println(words); // [apple, banana, cherry]

        // Type 4: Constructor reference
        Supplier<ArrayList<String>> listMaker = ArrayList::new;
        Function<String, Person> personFactory = name -> new Person(name, 0);
        // With matching constructor:
        BiFunction<String, Integer, Person> personFactory2 = Person::new;
        Person p = personFactory2.apply("Bob", 30);
        System.out.println(p); // Person[name=Bob, age=30]

        // Practical: collect using constructor reference
        List<String> names = List.of("Charlie", "Alice", "Bob");
        List<String> sorted = names.stream()
            .sorted(String::compareTo)   // Type 3
            .collect(Collectors.toCollection(ArrayList::new));  // Type 4
        System.out.println(sorted); // [Alice, Bob, Charlie]
    }
}
```

**What this does:** Method references are pure syntactic sugar — each can always be rewritten as a lambda. Use them when the lambda body is just a method call with no additional logic.

### Dry Run — Type 3 (Instance of Arbitrary Object)

```
String::toUpperCase used as Function<String, String>:

Function<String, String> f = String::toUpperCase;
f.apply("hello"):
  → calls "hello".toUpperCase()
  → returns "HELLO"

The lambda equivalent: s -> s.toUpperCase()
The first parameter 's' becomes the receiver of the method call.

Comparator<String> c = String::compareTo;
c.compare("apple", "banana"):
  → calls "apple".compareTo("banana")
  → first parameter is the receiver, second is the argument
```

### Example 2 — Method References in Stream Pipelines

```java
import java.util.*;
import java.util.stream.*;

public class MethodRefStreams {
    record Product(String name, double price) {}

    public static void main(String[] args) {
        List<Product> products = List.of(
            new Product("Apple", 1.50),
            new Product("Banana", 0.75),
            new Product("Cherry", 3.00)
        );

        // Static: Double::sum as BinaryOperator in reduce
        double total = products.stream()
            .mapToDouble(Product::price)   // Type 3: instance of arbitrary Product
            .sum();
        System.out.println("Total: " + total); // 5.25

        // Collect names using stream
        List<String> names = products.stream()
            .map(Product::name)            // Type 3: p -> p.name()
            .map(String::toUpperCase)      // Type 3: s -> s.toUpperCase()
            .sorted(String::compareTo)     // Type 3: comparator
            .collect(Collectors.toList());
        System.out.println(names); // [APPLE, BANANA, CHERRY]

        // Type 2: particular instance
        List<String> log = new ArrayList<>();
        products.stream()
            .map(Product::name)
            .forEach(log::add);            // Type 2: log.add(element)
        System.out.println(log); // [Apple, Banana, Cherry]
    }
}
```

**What this does:** Method references make stream pipelines read like English. `Product::price` reads as "get price from a product". Chaining them makes the pipeline intent obvious.

> ⚠️ **Pitfall:** Type 3 vs Type 2 confusion. `String::toLowerCase` (Type 3) takes the String as first arg (receiver). `myString::toLowerCase` (Type 2) always uses that specific string instance.

---

## 5. Lambda Scope Rules

### Example 1 — Lambda in Different Contexts

```java
import java.util.*;
import java.util.function.*;

public class LambdaScope {
    static int staticVar = 100;
    int instanceVar = 200;

    List<Supplier<Integer>> createSuppliers() {
        List<Supplier<Integer>> suppliers = new ArrayList<>();

        for (int i = 0; i < 3; i++) {
            final int captured = i;  // effectively final copy for each iteration
            suppliers.add(() -> captured); // captures 0, 1, 2
        }

        return suppliers;
    }

    void demonstrate() {
        int x = 50; // effectively final

        // Lambda accesses outer context
        Runnable r = () -> {
            System.out.println(staticVar);   // 100
            System.out.println(instanceVar); // 200 (via LambdaScope.this)
            System.out.println(x);           // 50 (captured copy)
        };
        r.run();

        // Each lambda in createSuppliers captures its own 'i' copy
        List<Supplier<Integer>> sups = createSuppliers();
        System.out.println(sups.get(0).get()); // 0
        System.out.println(sups.get(1).get()); // 1
        System.out.println(sups.get(2).get()); // 2
    }

    public static void main(String[] args) {
        new LambdaScope().demonstrate();
    }
}
```

**What this does:** Each loop iteration needs its own `final` copy of `i` — that's why `final int captured = i` is inside the loop. If you used `i` directly in a Java 7 loop, it wouldn't be effectively final. This is a classic closure-in-a-loop pattern.

---

## Quick Reference

```
Lambda syntax:
  () -> expr                     no params
  x -> expr                      one param, no parens needed
  (x, y) -> expr                 two params
  (x, y) -> { stmts; return v; } block body, explicit return

Method reference types:
  ClassName::staticMethod        Type 1 — static
  instance::method               Type 2 — bound instance
  ClassName::instanceMethod      Type 3 — unbound (first arg = receiver)
  ClassName::new                 Type 4 — constructor

Variable capture rules:
  Local variables:     must be effectively final (never reassigned)
  Instance fields:     freely accessible (via Outer.this)
  Static fields:       freely accessible

this in lambda:     enclosing class's this
this in anonymous:  the anonymous class instance

Workaround for mutable counter: int[] arr = {0}; or AtomicInteger
```
