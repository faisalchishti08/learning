---
card: java
gi: 349
slug: generic-class-declaration-t
title: Generic class declaration <T>
---

## 1. What it is

A generic class declares one or more type parameters in angle brackets after its name — `class Box<T>` — letting the class work with any specific type while still getting full compile-time type checking, instead of either duplicating the class per type or falling back to unchecked `Object` fields. `T` is a stand-in for "whatever type this particular `Box` is created with"; when you write `Box<String>`, every `T` inside `Box`'s definition behaves as if it had been written `String` for that specific instance.

```java
public class GenericClassDemo {
    static class Box<T> {
        private T contents;
        public void set(T value) { contents = value; }
        public T get() { return contents; }
    }

    public static void main(String[] args) {
        Box<String> stringBox = new Box<>();
        stringBox.set("hello");
        String value = stringBox.get(); // no cast needed -- the compiler already knows this is a String
        System.out.println(value);
    }
}
```

`Box<String>` fixes `T` to `String` for that specific instance — `stringBox.get()` returns a `String` directly, with no cast required, because the compiler tracked the type all the way through.

## 2. Why & when

Before generics (pre-Java 5), a general-purpose reusable container had to store `Object` references, forcing every caller to manually cast the result back to the real type — a cast that compiles fine but can fail at runtime with `ClassCastException` if the wrong type was ever stored. Generic classes move that type checking to compile time, catching type mismatches before the program ever runs.

- **Reusable container and utility classes** — any class whose core logic doesn't depend on the specific type it holds (a box, a stack, a pair, a cache) benefits from being written once, generically, rather than duplicated per type or left unchecked with `Object`.
- **Type-safe APIs** — a generic class's public methods can express exactly what type goes in and comes out, letting the compiler catch mistakes (like trying to put a `String` into a `Box<Integer>`) immediately, rather than discovering the error at runtime.
- **Avoiding repetitive, type-specific boilerplate** — without generics, you'd need a separate `StringBox`, `IntegerBox`, `UserBox`, etc., each with identical logic — the generic version captures that logic exactly once.

The type parameter itself carries no runtime information — due to type erasure (a related but separate topic), all instances of `Box<T>` share the same single `.class` file at runtime, with `T` replaced by `Object` (or its bound) internally; the type-safety benefit is entirely a compile-time guarantee, not something checked while the program is running.

## 3. Core concept

```java
public class GenericClassCore {
    static class Pair<A, B> { // multiple type parameters
        private A first;
        private B second;
        public Pair(A first, B second) { this.first = first; this.second = second; }
        public A getFirst() { return first; }
        public B getSecond() { return second; }
        public String toString() { return "(" + first + ", " + second + ")"; }
    }

    public static void main(String[] args) {
        Pair<String, Integer> nameAge = new Pair<>("Ada", 30);
        System.out.println(nameAge.getFirst() + " is " + nameAge.getSecond() + " years old.");
        System.out.println(nameAge);
    }
}
```

**How to run:** `java GenericClassCore.java`

`Pair<A, B>` declares two independent type parameters, letting `getFirst()` return an `A` (here `String`) and `getSecond()` return a `B` (here `Integer`) — a class can have as many type parameters as it genuinely needs, each tracked independently by the compiler.

## 4. Diagram

<svg viewBox="0 0 600 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="a generic class definition with type parameter T is instantiated with specific concrete types, producing distinct type-checked variants at compile time">
  <rect x="8" y="8" width="584" height="134" rx="8" fill="#0d1117"/>
  <rect x="20" y="30" width="180" height="35" rx="6" fill="#1c2430" stroke="#8b949e"/>
  <text x="110" y="52" fill="#8b949e" font-size="10" text-anchor="middle">class Box&lt;T&gt;</text>

  <text x="235" y="52" fill="#8b949e" font-size="12">→</text>

  <rect x="270" y="30" width="140" height="30" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="340" y="50" fill="#79c0ff" font-size="9" text-anchor="middle">Box&lt;String&gt;</text>
  <rect x="270" y="70" width="140" height="30" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="340" y="90" fill="#6db33f" font-size="9" text-anchor="middle">Box&lt;Integer&gt;</text>

  <text x="20" y="110" fill="#8b949e" font-size="9">Same class definition, compiler enforces a different concrete type per instantiation.</text>
</svg>

## 5. Runnable example

Scenario: a simple generic stack data structure, evolved from a version storing raw `Object` values requiring manual casts, into a type-safe generic version, into a production-style version that adds bounds-aware capacity handling and clear error reporting for misuse.

### Level 1 — Basic

```java
import java.util.ArrayList;
import java.util.List;

public class StackBasic {
    static class ObjectStack { // pre-generics style: everything is Object
        private List<Object> items = new ArrayList<>();
        public void push(Object item) { items.add(item); }
        public Object pop() { return items.remove(items.size() - 1); }
    }

    public static void main(String[] args) {
        ObjectStack stack = new ObjectStack();
        stack.push("hello");
        String value = (String) stack.pop(); // manual cast required, and unchecked at compile time
        System.out.println(value);
    }
}
```

**How to run:** `java StackBasic.java`

The cast `(String) stack.pop()` compiles regardless of what was actually pushed — if some other code had pushed an `Integer` onto this same stack, this exact line would compile fine but throw `ClassCastException` at runtime, since `ObjectStack` has no way to enforce a single consistent element type.

### Level 2 — Intermediate

```java
import java.util.ArrayList;
import java.util.List;

public class StackIntermediate {
    static class Stack<T> { // generic version -- T is fixed per instance
        private List<T> items = new ArrayList<>();
        public void push(T item) { items.add(item); }
        public T pop() { return items.remove(items.size() - 1); }
        public boolean isEmpty() { return items.isEmpty(); }
    }

    public static void main(String[] args) {
        Stack<String> stack = new Stack<>();
        stack.push("hello");
        stack.push("world");
        while (!stack.isEmpty()) {
            String value = stack.pop(); // no cast needed -- compiler already knows it's a String
            System.out.println(value);
        }
    }
}
```

**How to run:** `java StackIntermediate.java`

`Stack<String>` fixes `T` to `String` for this instance — attempting `stack.push(42)` here would now be a **compile-time error**, not a runtime surprise, since the compiler enforces that only `String` values can ever go into this specific stack.

### Level 3 — Advanced

```java
import java.util.ArrayList;
import java.util.EmptyStackException;
import java.util.List;

public class StackAdvanced {
    static class Stack<T> {
        private final List<T> items = new ArrayList<>();
        private final int maxCapacity;

        public Stack(int maxCapacity) { this.maxCapacity = maxCapacity; }

        public void push(T item) {
            if (items.size() >= maxCapacity) {
                throw new IllegalStateException("Stack is full (capacity: " + maxCapacity + ")");
            }
            items.add(item);
        }

        public T pop() {
            if (items.isEmpty()) {
                throw new EmptyStackException();
            }
            return items.remove(items.size() - 1);
        }

        public boolean isEmpty() { return items.isEmpty(); }
        public int size() { return items.size(); }
    }

    public static void main(String[] args) {
        Stack<Integer> stack = new Stack<>(3);
        stack.push(1);
        stack.push(2);
        stack.push(3);
        try {
            stack.push(4); // exceeds capacity
        } catch (IllegalStateException e) {
            System.out.println("Rejected push: " + e.getMessage());
        }

        while (!stack.isEmpty()) System.out.println("Popped: " + stack.pop());

        try {
            stack.pop(); // stack is now empty
        } catch (EmptyStackException e) {
            System.out.println("Rejected pop: stack was empty");
        }
    }
}
```

**How to run:** `java StackAdvanced.java`

The generic type safety (`T` fixed to `Integer` for this instance) combines with real runtime behavioral guarantees — a bounded capacity check on `push` and an empty-stack check on `pop` — showing that generics solve the *type* correctness problem while ordinary validation logic is still needed for *state* correctness (capacity, emptiness), which generics don't and can't address on their own.

## 6. Walkthrough

Execution starts in `main`, which creates `Stack<Integer> stack = new Stack<>(3)` — fixing `T` to `Integer` for this instance and setting `maxCapacity` to 3.

Three `push` calls follow: `push(1)`, `push(2)`, `push(3)`. Each checks `items.size() >= maxCapacity` (0, then 1, then 2 — all less than 3), so each succeeds, adding to the internal `items` list, which now holds `[1, 2, 3]`.

The fourth call, `stack.push(4)`, checks `items.size() >= maxCapacity` — `3 >= 3` is `true` — so it throws `IllegalStateException("Stack is full (capacity: 3)")` before ever adding `4` to the list. The `catch` block in `main` prints `Rejected push: Stack is full (capacity: 3)`.

The `while (!stack.isEmpty())` loop then runs three times, each iteration calling `stack.pop()`. Since `List.remove(items.size() - 1)` removes and returns the *last* element, the pops come off in reverse insertion order: first `3`, then `2`, then `1` — each printed as `Popped: 3`, `Popped: 2`, `Popped: 1`. After the third pop, `items` is empty, so `isEmpty()` returns `true` and the loop ends.

Finally, `main` calls `stack.pop()` one more time inside its own `try` block. This time, `items.isEmpty()` is `true`, so `pop()` throws `EmptyStackException` before attempting to remove anything — the `catch` block prints `Rejected pop: stack was empty`.

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="three pushes succeed, a fourth is rejected for exceeding capacity, three pops return values in reverse order, then a final pop is rejected because the stack is empty">
  <rect x="8" y="8" width="624" height="154" rx="8" fill="#0d1117"/>
  <text x="20" y="30" fill="#6db33f" font-size="10">push(1), push(2), push(3) -&gt; items = [1, 2, 3], all within capacity=3</text>
  <text x="20" y="55" fill="#f85149" font-size="10">push(4) -&gt; size()==capacity -&gt; IllegalStateException, item NOT added</text>
  <text x="20" y="85" fill="#79c0ff" font-size="10">pop() x3 -&gt; removes from the END each time -&gt; prints 3, then 2, then 1 -&gt; items now empty</text>
  <text x="20" y="115" fill="#f85149" font-size="10">pop() again -&gt; items.isEmpty() true -&gt; EmptyStackException, nothing to remove</text>
</svg>

## 7. Gotchas & takeaways

> A type parameter like `T` provides zero runtime type information about itself — you cannot write `new T()`, `T.class`, or `instanceof T` inside a generic class, because due to type erasure, the compiled bytecode has no record of what `T` actually was at any given call site.

- Declare type parameters in angle brackets after the class name (`class Box<T>`); every occurrence of `T` in the class body refers to whatever concrete type the class is instantiated with.
- A generic class can declare multiple independent type parameters (`class Pair<A, B>`), each tracked separately by the compiler.
- Generics move type-checking to compile time, eliminating the need for the caller to manually cast results — and eliminating the runtime `ClassCastException` risk that comes with using raw `Object` for a supposedly single-typed container.
- Generics only enforce *type* correctness at compile time — *behavioral* correctness (capacity limits, emptiness checks, and similar runtime invariants) still needs to be validated with ordinary runtime logic, exactly as in non-generic code.
- Diamond syntax (`new Stack<>(3)`) lets the compiler infer the type argument from context, avoiding the need to repeat it on both sides of an assignment.
