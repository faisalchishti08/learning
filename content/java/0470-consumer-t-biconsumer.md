---
card: java
gi: 470
slug: consumer-t-biconsumer
title: Consumer<T> / BiConsumer
---

## 1. What it is

`Consumer<T>` is the functional interface for "take one input of type `T`, do something with it, produce nothing back." Its single abstract method is `void accept(T t)`. `BiConsumer<T, U>` is its two-argument sibling: `void accept(T t, U u)`. Where `Function<T, R>` is about *transforming* a value into a new one, `Consumer` is purely about a **side effect** — printing, storing, mutating, sending — with no return value at all.

## 2. Why & when

Plenty of operations genuinely have no result to return — printing something, adding an item to a collection, updating a field, sending a notification. `Consumer<T>` gives that shape of behaviour the same first-class, pass-around-as-a-value treatment `Function` gives transformations, without forcing you to invent a return type that doesn't mean anything (returning `void` isn't possible from a lambda targeting `Function`, since `Function.apply` must return something). `BiConsumer<T, U>` exists for the same reason `BiFunction` does: some side effects genuinely need two related inputs together, like a key and a value.

You reach for `Consumer<T>` constantly: `Iterable.forEach(Consumer<T>)`/`Stream.forEach(Consumer<T>)` to do something with each element, `Optional.ifPresent(Consumer<T>)` to act on a value only if it exists, or as a parameter type on your own methods when a caller needs to supply "what to do with this," not "what to compute from this." `BiConsumer` shows up most often with `Map.forEach(BiConsumer<K, V>)`, iterating key/value pairs together.

## 3. Core concept

```java
import java.util.function.*;
import java.util.*;

Consumer<String> print = s -> System.out.println("Got: " + s);
print.accept("hello"); // "Got: hello" -- no return value at all

// andThen: run this Consumer's side effect, THEN run another one, in sequence
Consumer<String> printTwice = print.andThen(s -> System.out.println("Again: " + s));
printTwice.accept("hi");

BiConsumer<String, Integer> logEntry = (name, count) -> System.out.println(name + " x" + count);
logEntry.accept("apples", 3); // "apples x3"
```

`accept` runs the side effect and returns nothing (`void`) — this is the defining difference from `Function`, whose `apply` always produces a result.

## 4. Diagram

<svg viewBox="0 0 640 140" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A Consumer takes one input and performs a side effect, producing no return value at all">
  <rect x="8" y="8" width="624" height="124" rx="8" fill="#0d1117"/>
  <rect x="60" y="45" width="120" height="50" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="120" y="75" fill="#79c0ff" font-size="12" text-anchor="middle" font-family="monospace">T input</text>

  <rect x="290" y="35" width="150" height="70" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="365" y="60" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">Consumer&lt;T&gt;</text>
  <text x="365" y="80" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="monospace">accept(t)</text>

  <line x1="180" y1="70" x2="285" y2="70" stroke="#8b949e" stroke-width="2" marker-end="url(#a1)"/>
  <text x="500" y="70" fill="#f85149" font-size="11" text-anchor="middle" font-family="sans-serif">no output --</text>
  <text x="500" y="86" fill="#f85149" font-size="11" text-anchor="middle" font-family="sans-serif">side effect only</text>
  <defs><marker id="a1" markerWidth="9" markerHeight="9" refX="4" refY="7" orient="auto"><path d="M0,0 L8,0 L4,7 Z" fill="#8b949e"/></marker></defs>
</svg>

Input flows in; nothing flows back out except whatever side effect the `Consumer` performs.

## 5. Runnable example

Scenario: logging shopping cart activity — evolved from a single `Consumer` printing an item, through chaining several `Consumer`s together with `andThen` for multiple side effects per item, to a `BiConsumer` iterating a `Map` of item names to quantities.

### Level 1 — Basic

```java
import java.util.function.*;
import java.util.*;

public class ConsumerBasic {
    public static void main(String[] args) {
        List<String> cart = List.of("apples", "bread", "milk");

        Consumer<String> printItem = item -> System.out.println("In cart: " + item);

        cart.forEach(printItem);
    }
}
```

**How to run:** `java ConsumerBasic.java`

Expected output:
```
In cart: apples
In cart: bread
In cart: milk
```

`cart.forEach(printItem)` calls `printItem.accept(item)` once per element of `cart`, in order — each call runs the lambda's side effect (printing) and produces no value at all, exactly matching `Consumer<String>.accept(String)`'s `void` return type.

### Level 2 — Intermediate

```java
import java.util.function.*;
import java.util.*;

public class ConsumerChaining {
    public static void main(String[] args) {
        List<Double> totals = new ArrayList<>();

        Consumer<Double> printPrice = price -> System.out.println("Price: $" + price);
        Consumer<Double> recordTotal = totals::add; // method reference: List::add as a Consumer

        // andThen runs BOTH side effects, in sequence, for each accept() call.
        Consumer<Double> printAndRecord = printPrice.andThen(recordTotal);

        printAndRecord.accept(9.99);
        printAndRecord.accept(4.50);

        double sum = totals.stream().mapToDouble(Double::doubleValue).sum();
        System.out.println("Running total: " + sum);
    }
}
```

**How to run:** `java ConsumerChaining.java`

Expected output:
```
Price: $9.99
Price: $4.5
Running total: 14.49
```

The real-world concern this adds: a single item often needs **multiple** independent side effects — printing it and also recording it — and `andThen` composes two `Consumer`s into one that performs both, in order, on every `accept` call, without needing a combined lambda written by hand.

### Level 3 — Advanced

```java
import java.util.function.*;
import java.util.*;

public class BiConsumerMapIteration {
    public static void main(String[] args) {
        Map<String, Integer> cart = new LinkedHashMap<>();
        cart.put("apples", 3);
        cart.put("bread", 1);
        cart.put("milk", 2);

        int[] totalItems = { 0 }; // array trick: a mutable "holder" a BiConsumer lambda can update

        BiConsumer<String, Integer> logAndCount = (item, quantity) -> {
            System.out.println(item + " x" + quantity);
            totalItems[0] += quantity;
        };

        cart.forEach(logAndCount);

        System.out.println("Total items: " + totalItems[0]);
    }
}
```

**How to run:** `java BiConsumerMapIteration.java`

Expected output:
```
apples x3
bread x1
milk x2
Total items: 6
```

`Map.forEach(BiConsumer<K, V>)` calls `logAndCount.accept(key, value)` once per entry, in this case in insertion order (because `cart` is a `LinkedHashMap`). `totalItems` is a one-element `int[]` used as a mutable holder: a plain `int` local couldn't be reassigned inside the lambda (it wouldn't be effectively final), but mutating an *array element* the lambda captures a reference to is a well-known workaround, similar in spirit to the field-holder pattern from the effectively-final topic.

## 6. Walkthrough

Execution starts in `main` of the Level 3 example. `cart` is a `LinkedHashMap` with three entries, inserted in the order `"apples" -> 3`, `"bread" -> 1`, `"milk" -> 2`. `totalItems` is created as a one-element array holding `0`.

`cart.forEach(logAndCount)` iterates the map's entries in insertion order (guaranteed by `LinkedHashMap`), calling `logAndCount.accept(key, value)` once per entry.

For the first entry, `logAndCount.accept("apples", 3)` runs: `System.out.println("apples x3")` prints the first line, then `totalItems[0] += quantity` updates the array's single element from `0` to `0 + 3 = 3`.

For the second entry, `logAndCount.accept("bread", 1)` runs: prints `"bread x1"`, then `totalItems[0]` becomes `3 + 1 = 4`.

For the third entry, `logAndCount.accept("milk", 2)` runs: prints `"milk x2"`, then `totalItems[0]` becomes `4 + 2 = 6`.

```
accept("apples", 3) --> print "apples x3" --> totalItems[0]: 0 -> 3
accept("bread", 1)  --> print "bread x1"  --> totalItems[0]: 3 -> 4
accept("milk", 2)   --> print "milk x2"   --> totalItems[0]: 4 -> 6
```

After `forEach` completes, `System.out.println("Total items: " + totalItems[0])` reads the final accumulated value, `6`, and prints the last line — the sum of all three quantities, accumulated purely through the `BiConsumer`'s side effects across three separate `accept` calls.

## 7. Gotchas & takeaways

> `Consumer.andThen` runs both consumers **on the same input**, in sequence — it does not pass the first consumer's "result" to the second, because a `Consumer` has no result at all. This is a different chaining shape from `Function.andThen`, which genuinely pipes one function's output into the next. Confusing the two is an easy mistake if you're used to `Function`'s chaining semantics.

- `Consumer<T>` represents "one input, no output, a side effect" — its single abstract method is `void accept(T t)`.
- `BiConsumer<T, U>` is the two-argument version — `void accept(T t, U u)` — most commonly seen with `Map.forEach(BiConsumer<K, V>)`.
- `andThen` chains multiple `Consumer`s to all run, in sequence, on the same input — useful when one value needs several independent side effects performed on it.
- `Iterable.forEach`/`Stream.forEach`/`Optional.ifPresent` are the most common places `Consumer` appears in everyday code.
- Since a `Consumer`'s lambda body typically needs to mutate something external to produce any visible effect at all, watch for the effectively-final restriction on captured variables — a one-element array or a mutable holder object's field are the standard workarounds for accumulating results across multiple `accept` calls.
