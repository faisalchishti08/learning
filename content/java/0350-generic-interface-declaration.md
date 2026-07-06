---
card: java
gi: 350
slug: generic-interface-declaration
title: Generic interface declaration
---

## 1. What it is

A generic interface declares one or more type parameters in angle brackets after its name, exactly like a generic class — `interface Repository<T>` — letting any implementing class fix the type parameter to something concrete (`class UserRepository implements Repository<User>`) or, itself, stay generic and pass the type parameter along (`class CachingRepository<T> implements Repository<T>`). The interface's method signatures use the type parameter, so every implementer commits to a specific, compiler-checked type for that contract.

```java
public class GenericInterfaceDemo {
    interface Container<T> {
        void put(T item);
        T get();
    }

    static class StringContainer implements Container<String> { // fixes T to String
        private String value;
        public void put(String item) { value = item; }
        public String get() { return value; }
    }

    public static void main(String[] args) {
        Container<String> c = new StringContainer();
        c.put("hello");
        System.out.println(c.get());
    }
}
```

`StringContainer implements Container<String>` commits this specific class to always working with `String` — its `put`/`get` methods are effectively `put(String)`/`get(): String`, checked by the compiler against the interface's contract.

## 2. Why & when

Interfaces describe a contract independent of any one concrete implementation; making that contract generic lets many different implementations share the exact same method signatures while each working with its own specific type — a `Repository<User>`, a `Repository<Order>`, and a `Repository<Product>` all honor the identical `Repository<T>` contract, letting code that depends only on the interface work uniformly across all of them.

- **Defining reusable abstractions over varying data types** — a generic `Repository<T>`, `Converter<A, B>`, or `Comparator<T>`-style interface describes behavior that's identical in shape but different in the specific type each implementation handles.
- **Enabling polymorphism across type-parameterized implementations** — code written against `Repository<T>` can accept any implementation, regardless of which concrete type `T` that implementation was built for, as long as the caller's own type matches.
- **Standard library patterns** — many core JDK interfaces are generic for exactly this reason: `Comparable<T>`, `Comparator<T>`, `Iterable<T>`, `List<T>` are all generic interfaces, each letting many different types implement the same well-defined contract.

A class implementing a generic interface must either supply a concrete type argument (fixing the type parameter for that class specifically) or itself remain generic, re-declaring the same type parameter and passing it through — there's no way to implement a generic interface without deciding, at the implementing class's own declaration, how that type parameter is handled.

## 3. Core concept

```java
public class GenericInterfaceCore {
    interface Converter<A, B> {
        B convert(A input);
    }

    static class IntToStringConverter implements Converter<Integer, String> {
        public String convert(Integer input) { return "Number: " + input; }
    }

    static class UppercaseConverter implements Converter<String, String> {
        public String convert(String input) { return input.toUpperCase(); }
    }

    public static void main(String[] args) {
        Converter<Integer, String> c1 = new IntToStringConverter();
        Converter<String, String> c2 = new UppercaseConverter();
        System.out.println(c1.convert(42));
        System.out.println(c2.convert("hello"));
    }
}
```

**How to run:** `java GenericInterfaceCore.java`

`Converter<A, B>` describes a general shape — "something that turns an `A` into a `B`" — and each implementer fixes both type parameters to whatever specific conversion it performs, while callers can hold any `Converter<A, B>` reference uniformly regardless of which implementation is behind it.

## 4. Diagram

<svg viewBox="0 0 620 160" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="a generic interface is implemented by multiple classes, each fixing the type parameter to a different concrete type while honoring the same method contract">
  <rect x="8" y="8" width="604" height="144" rx="8" fill="#0d1117"/>
  <rect x="220" y="25" width="180" height="35" rx="6" fill="#1c2430" stroke="#8b949e"/>
  <text x="310" y="47" fill="#8b949e" font-size="10" text-anchor="middle">interface Container&lt;T&gt;</text>

  <rect x="20" y="95" width="180" height="35" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="110" y="117" fill="#79c0ff" font-size="9" text-anchor="middle">implements Container&lt;String&gt;</text>

  <rect x="420" y="95" width="180" height="35" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="510" y="117" fill="#6db33f" font-size="9" text-anchor="middle">implements Container&lt;Integer&gt;</text>

  <text x="150" y="80" fill="#8b949e" font-size="10">↙</text>
  <text x="470" y="80" fill="#8b949e" font-size="10">↘</text>
</svg>

## 5. Runnable example

Scenario: a small event-handling framework, evolved from a single non-generic handler interface tied to one event type, into a generic version usable across multiple event types, into a production-style dispatcher registering multiple typed handlers behind a single generic contract.

### Level 1 — Basic

```java
public class HandlerBasic {
    interface OrderHandler { // NOT generic -- tied to one specific type
        void handle(String orderId);
    }

    static class LoggingOrderHandler implements OrderHandler {
        public void handle(String orderId) { System.out.println("Logging order: " + orderId); }
    }

    public static void main(String[] args) {
        OrderHandler handler = new LoggingOrderHandler();
        handler.handle("ORD-1001");
    }
}
```

**How to run:** `java HandlerBasic.java`

This handler contract is hardcoded to `String` order IDs — if the application later needed to handle a different event type (say, a `PaymentEvent` object instead of a plain `String`), an entirely separate, differently-named interface would be needed, duplicating the same shape.

### Level 2 — Intermediate

```java
public class HandlerIntermediate {
    interface Handler<T> { // now generic -- reusable across event types
        void handle(T event);
    }

    record OrderEvent(String orderId) {}
    record PaymentEvent(String paymentId, double amount) {}

    static class OrderLoggingHandler implements Handler<OrderEvent> {
        public void handle(OrderEvent event) { System.out.println("Order event: " + event.orderId()); }
    }

    static class PaymentLoggingHandler implements Handler<PaymentEvent> {
        public void handle(PaymentEvent event) {
            System.out.println("Payment event: " + event.paymentId() + " for $" + event.amount());
        }
    }

    public static void main(String[] args) {
        Handler<OrderEvent> orderHandler = new OrderLoggingHandler();
        Handler<PaymentEvent> paymentHandler = new PaymentLoggingHandler();
        orderHandler.handle(new OrderEvent("ORD-1001"));
        paymentHandler.handle(new PaymentEvent("PAY-77", 49.99));
    }
}
```

**How to run:** `java HandlerIntermediate.java`

The same `Handler<T>` interface now serves both `OrderEvent` and `PaymentEvent` handling, each implementer fixing `T` to its own event type — no duplicated interface definitions are needed as new event types are added.

### Level 3 — Advanced

```java
import java.util.HashMap;
import java.util.Map;

public class HandlerAdvanced {
    interface Handler<T> { void handle(T event); }

    record OrderEvent(String orderId) {}
    record PaymentEvent(String paymentId, double amount) {}

    static class OrderLoggingHandler implements Handler<OrderEvent> {
        public void handle(OrderEvent event) { System.out.println("Order event: " + event.orderId()); }
    }

    static class PaymentLoggingHandler implements Handler<PaymentEvent> {
        public void handle(PaymentEvent event) {
            System.out.println("Payment event: " + event.paymentId() + " for $" + event.amount());
        }
    }

    static class EventDispatcher {
        private final Map<Class<?>, Handler<Object>> handlers = new HashMap<>();

        @SuppressWarnings("unchecked")
        <T> void register(Class<T> eventType, Handler<T> handler) {
            handlers.put(eventType, (Handler<Object>) handler); // erasure makes this cast necessary
        }

        void dispatch(Object event) {
            Handler<Object> handler = handlers.get(event.getClass());
            if (handler != null) handler.handle(event);
            else System.out.println("No handler registered for " + event.getClass().getSimpleName());
        }
    }

    public static void main(String[] args) {
        EventDispatcher dispatcher = new EventDispatcher();
        dispatcher.register(OrderEvent.class, new OrderLoggingHandler());
        dispatcher.register(PaymentEvent.class, new PaymentLoggingHandler());

        dispatcher.dispatch(new OrderEvent("ORD-1001"));
        dispatcher.dispatch(new PaymentEvent("PAY-77", 49.99));
        dispatcher.dispatch("an unregistered event type");
    }
}
```

**How to run:** `java HandlerAdvanced.java`

`EventDispatcher` stores handlers keyed by their event's `Class` object, letting `dispatch` route any object to the correct registered `Handler<T>` at runtime by its actual type — the `@SuppressWarnings("unchecked")` cast in `register` is required because type erasure means the map's value type (`Handler<Object>`) can't actually verify at runtime that a given `Handler<T>` truly matches its registered `Class<T>` key, so this correctness is guaranteed only by `register`'s own generic method signature, not by any runtime check.

## 6. Walkthrough

Execution starts in `main`, which creates an `EventDispatcher` and registers two handlers: `register(OrderEvent.class, new OrderLoggingHandler())` and `register(PaymentEvent.class, new PaymentLoggingHandler())`.

Inside `register`, each call stores its handler in the `handlers` map, keyed by the exact `Class` object passed in (`OrderEvent.class` or `PaymentEvent.class`), with the handler itself cast to `Handler<Object>` — this cast is unchecked at compile time (hence the suppressed warning) but is actually safe here because `register`'s own generic signature (`<T> void register(Class<T> eventType, Handler<T> handler)`) guarantees the caller can only ever pass a `Handler<T>` matching the same `T` as the `Class<T>` key.

`main` then calls `dispatcher.dispatch(new OrderEvent("ORD-1001"))`. Inside `dispatch`, `event.getClass()` returns `OrderEvent.class` (the object's actual runtime type), and `handlers.get(OrderEvent.class)` finds the previously-registered `OrderLoggingHandler`, cast (already, from registration) to `Handler<Object>`. Since it's non-null, `handler.handle(event)` is called, running `OrderLoggingHandler`'s `handle` method, which prints `Order event: ORD-1001`.

`dispatcher.dispatch(new PaymentEvent("PAY-77", 49.99))` follows the identical path: `event.getClass()` returns `PaymentEvent.class`, the map lookup finds `PaymentLoggingHandler`, and its `handle` method prints `Payment event: PAY-77 for $49.99`.

Finally, `dispatcher.dispatch("an unregistered event type")` passes a plain `String`. `event.getClass()` returns `String.class`, which was never registered in `handlers` — `handlers.get(String.class)` returns `null`. The `if (handler != null)` check fails, so the `else` branch runs, printing `No handler registered for String`.

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="each dispatch call looks up a handler by the event's runtime class, routing to the matching registered handler or reporting no match found">
  <rect x="8" y="8" width="624" height="154" rx="8" fill="#0d1117"/>
  <text x="20" y="30" fill="#e6edf3" font-size="10">register(OrderEvent.class, orderHandler), register(PaymentEvent.class, paymentHandler)</text>
  <text x="20" y="55" fill="#6db33f" font-size="10">dispatch(OrderEvent) -&gt; getClass()==OrderEvent.class -&gt; found -&gt; "Order event: ORD-1001"</text>
  <text x="20" y="80" fill="#6db33f" font-size="10">dispatch(PaymentEvent) -&gt; getClass()==PaymentEvent.class -&gt; found -&gt; "Payment event: PAY-77 for $49.99"</text>
  <text x="20" y="105" fill="#f85149" font-size="10">dispatch("a String") -&gt; getClass()==String.class -&gt; NOT found -&gt; "No handler registered for String"</text>
</svg>

## 7. Gotchas & takeaways

> Storing handlers of different concrete type parameters (`Handler<OrderEvent>`, `Handler<PaymentEvent>`) together in one collection requires erasing them to a common type (`Handler<Object>`) with an unchecked cast — the correctness of matching each handler to its right event type then relies entirely on the surrounding code (like keying by `Class` object) being written correctly, since the compiler can no longer verify it.

- A generic interface's implementers must either supply a concrete type argument (`implements Container<String>`) or remain generic themselves and pass the type parameter through (`class Foo<T> implements Container<T>`).
- Many core JDK interfaces are generic for the same reason application code often benefits from it: `Comparable<T>`, `Iterable<T>`, and `List<T>` all describe a contract shape shared across many different concrete types.
- Code written against a generic interface type can work uniformly with any implementation, regardless of what concrete type parameter that implementation uses — this is the core polymorphism benefit generics add on top of ordinary interfaces.
- Combining a generic interface with `Class<T>`-keyed collections (as in the advanced example) is a common pattern for type-safe dispatch, though it typically requires at least one unchecked cast due to type erasure.
- `@SuppressWarnings("unchecked")` should be applied to the narrowest possible scope and only when you've manually verified the underlying assumption is actually safe — it silences the compiler's warning, not the underlying risk.
