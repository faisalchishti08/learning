---
card: java
gi: 477
slug: instance-method-of-particular-object-obj-method
title: 'Instance method of particular object (obj::method)'
---

## 1. What it is

A method reference written `object::instanceMethod`, where `object` is a specific, already-existing variable, is shorthand for a lambda that calls that instance method **on that specific object**, forwarding the lambda's own parameters as the method's arguments. `myList::add` means the same thing as `x -> myList.add(x)` — the receiver (`myList`) is fixed and captured at the moment the reference is created, exactly the way a lambda would capture it.

## 2. Why & when

This form is the natural counterpart to `this::methodName` (covered in the topic on `this` in lambdas) — but generalized to *any* specific object, not just the enclosing instance. Whenever you already have a particular object in hand and want to hand off "call this method on that object" as a piece of behavior — a callback, an accumulator, an event handler — this method reference form expresses it directly, without the ceremony of a full lambda wrapping a single delegating call.

You reach for `object::instanceMethod` whenever a lambda's whole job is "call one method on one specific, already-known object" — registering a particular listener object's handler method, using an existing `List`'s `add` method as a `Consumer`, or passing an already-constructed logger's `log` method somewhere that expects a `Consumer<String>`. The receiver object is fixed at reference-creation time; if you need the receiver to vary per call, you need the different form covered in the next topic — an instance method reference on an *arbitrary* object of a class, not one specific object.

## 3. Core concept

```java
import java.util.*;
import java.util.function.*;

List<String> results = new ArrayList<>();

// results::add is shorthand for: item -> results.add(item)
// The RECEIVER (results) is fixed -- captured once, at the moment the reference is made.
Consumer<String> collector = results::add;

collector.accept("first");
collector.accept("second");
System.out.println(results); // [first, second]
```

`results::add` captures `results` as the fixed receiver — every call through `collector` adds to that same list, exactly as if `results` had been captured by an equivalent lambda.

## 4. Diagram

<svg viewBox="0 0 640 130" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="An instance method reference on a particular object fixes that object as the receiver, forwarding the lambda parameters as arguments to a method call on it">
  <rect x="8" y="8" width="624" height="114" rx="8" fill="#0d1117"/>
  <rect x="20" y="30" width="280" height="34" rx="4" fill="#1c2430" stroke="#f85149"/>
  <text x="160" y="52" fill="#f85149" font-size="11" text-anchor="middle" font-family="monospace">item -&gt; results.add(item)</text>

  <text x="320" y="52" fill="#8b949e" font-size="14" font-family="sans-serif">==</text>

  <rect x="360" y="30" width="260" height="34" rx="4" fill="#1c2430" stroke="#6db33f"/>
  <text x="490" y="52" fill="#6db33f" font-size="11" text-anchor="middle" font-family="monospace">results::add</text>

  <text x="20" y="95" fill="#8b949e" font-size="10" font-family="sans-serif">"results" is captured as the fixed receiver -- every call goes to that SAME object.</text>
</svg>

`results` is fixed the moment the reference is written — the same object receives every call made through it.

## 5. Runnable example

Scenario: routing messages to a specific logger — evolved from a bound method reference used directly as a `Consumer`, through multiple objects each supplying their own bound reference to prove the receiver stays fixed per reference, to a bound reference used as a `Supplier`, capturing an object whose method takes no arguments.

### Level 1 — Basic

```java
import java.util.*;
import java.util.function.*;

public class BoundMethodRefBasic {
    public static void main(String[] args) {
        List<String> log = new ArrayList<>();

        Consumer<String> record = log::add; // bound to THIS specific 'log' list

        record.accept("started");
        record.accept("processing");
        record.accept("done");

        System.out.println(log);
    }
}
```

**How to run:** `java BoundMethodRefBasic.java`

Expected output:
```
[started, processing, done]
```

`log::add` captures `log` as the fixed receiver at the moment it's written — every call to `record.accept(...)` invokes `log.add(...)` on that exact list, adding to it in order.

### Level 2 — Intermediate

```java
import java.util.*;
import java.util.function.*;

public class BoundMethodRefMultipleReceivers {
    static class Logger {
        private final String tag;
        private final List<String> entries = new ArrayList<>();

        Logger(String tag) { this.tag = tag; }

        void log(String message) {
            entries.add("[" + tag + "] " + message);
        }

        void printAll() {
            entries.forEach(System.out::println);
        }
    }

    public static void main(String[] args) {
        Logger appLogger = new Logger("APP");
        Logger dbLogger = new Logger("DB");

        // Each Consumer is bound to a DIFFERENT Logger instance -- fixed at creation, not shared.
        Consumer<String> appLog = appLogger::log;
        Consumer<String> dbLog = dbLogger::log;

        appLog.accept("server started");
        dbLog.accept("connection opened");
        appLog.accept("request handled");

        appLogger.printAll();
        dbLogger.printAll();
    }
}
```

**How to run:** `java BoundMethodRefMultipleReceivers.java`

Expected output:
```
[APP] server started
[APP] request handled
[DB] connection opened
```

The real-world concern this shows: `appLogger::log` and `dbLogger::log` are two entirely separate method references, each bound to its own `Logger` instance — calling through `appLog` never touches `dbLogger`'s entries, and vice versa, exactly as if each were an explicit lambda capturing its own distinct receiver (`message -> appLogger.log(message)` versus `message -> dbLogger.log(message)`).

### Level 3 — Advanced

```java
import java.util.*;
import java.util.function.*;

public class BoundMethodRefSupplier {
    static class Counter {
        private int value = 0;
        int next() { return ++value; }
    }

    public static void main(String[] args) {
        Counter ticketCounter = new Counter();

        // Supplier<Integer>: takes NO parameters, so counter::next (no-arg instance method)
        // fits perfectly -- bound to this specific Counter instance.
        Supplier<Integer> nextTicket = ticketCounter::next;

        List<Integer> issuedTickets = new ArrayList<>();
        for (int i = 0; i < 5; i++) {
            issuedTickets.add(nextTicket.get());
        }

        System.out.println(issuedTickets);
    }
}
```

**How to run:** `java BoundMethodRefSupplier.java`

Expected output:
```
[1, 2, 3, 4, 5]
```

`ticketCounter::next` is bound to the one `Counter` instance `ticketCounter`, and matches `Supplier<Integer>`'s shape (no parameters, one return value) exactly, since `next()` takes no arguments. Each call to `nextTicket.get()` invokes `ticketCounter.next()` on that same, single instance — so the counter's internal `value` field genuinely increments across calls, exactly as calling `ticketCounter.next()` directly five times would.

## 6. Walkthrough

Execution starts in `main` of the Level 3 example. `ticketCounter` is created, with its `value` field starting at `0`. `nextTicket` is assigned `ticketCounter::next`, a `Supplier<Integer>` bound to this one `Counter` instance. `issuedTickets` starts as an empty list.

The `for` loop runs five times, calling `nextTicket.get()` on each iteration. Each call invokes `ticketCounter.next()` — since the method reference is bound to the same `ticketCounter` object every time, this is genuinely the same instance's state being mutated across all five calls, not five independent counters.

On the first call, `next()` runs `++value`, incrementing `value` from `0` to `1` and returning `1`; that's added to `issuedTickets`. On the second call, `value` goes from `1` to `2`, returning `2`. This continues: third call returns `3`, fourth returns `4`, fifth returns `5`.

```
call 1: value 0 -> 1, returns 1
call 2: value 1 -> 2, returns 2
call 3: value 2 -> 3, returns 3
call 4: value 3 -> 4, returns 4
call 5: value 4 -> 5, returns 5
```

After the loop, `issuedTickets` holds `[1, 2, 3, 4, 5]`, which `main` prints — proof that all five calls shared and mutated the same underlying `Counter` state, exactly the behavior expected from a method reference bound to one specific, fixed object.

## 7. Gotchas & takeaways

> `object::instanceMethod` captures the **object reference**, not a snapshot of its current state — later mutations to that object (like `ticketCounter`'s internal `value` incrementing) are fully visible through every future call made via the bound reference, since all calls genuinely go through the same live object. This is different from capturing a primitive local variable, which captures an unchanging value; capturing an object reference captures "which object," and that object's own mutable state remains fully live and shared.

- `object::instanceMethod` is shorthand for a lambda that calls that method on that specific, already-existing object, forwarding the lambda's own parameters as arguments — the receiver is fixed at the moment the reference is created.
- This is the general form of the `this::methodName` pattern seen in the "this in lambdas" topic — `this::method` is just this same mechanism with the enclosing instance as the bound object.
- Different bound references to the same method on different object instances remain fully independent — each captures its own distinct receiver.
- If the target functional interface's method takes no parameters (like `Supplier.get()`), a no-argument instance method on the bound object fits directly, since there's nothing to forward beyond invoking the method on the fixed receiver.
- Because the receiver is genuinely a live, shared reference, any mutable state on the bound object remains visible and shared across every call made through the reference — this is a feature, not a bug, but worth being deliberate about when the bound object is mutable.
