---
card: java
gi: 210
slug: private-modifier
title: private modifier
---

## 1. What it is

The `private` modifier is Java's most restrictive access level: a `private` field, method, or constructor is accessible **only from within the exact same class** where it's declared — not from subclasses, not from other classes in the same package, not from anywhere except that one class's own code (including, notably, other instances of that same class, which *can* access each other's private members, since the restriction is per-class, not per-object).

```java
class Wallet {
    private double balance; // only Wallet's own code can read or write this directly

    private void logTransaction(String description) { // only Wallet's own code can call this
        System.out.println("LOG: " + description);
    }

    void deposit(double amount) {
        balance += amount;             // fine: same class
        logTransaction("Deposited " + amount); // fine: same class
    }
}

// Wallet w = new Wallet();
// w.balance = 100; // COMPILE ERROR — balance is private, inaccessible from outside Wallet
```

`balance` and `logTransaction` can only be touched by code written inside the `Wallet` class itself — any other class, even one in the same file or package, has no way to access them directly; only `Wallet`'s own methods, like `deposit`, can read or write `balance` or call `logTransaction`.

## 2. Why & when

`private` exists to hide a class's internal implementation details completely, exposing only the deliberate, curated interface a class chooses to make available:

- **True encapsulation** — a class's internal fields and helper methods are implementation details that should be free to change at any time, as long as the class's public behaviour stays consistent; `private` guarantees no outside code can ever depend on those internals directly.
- **Protecting invariants** — if a field can only be modified through the class's own methods (which can validate before assigning), the class can guarantee its own internal consistency in a way that's impossible if outside code could reach in and set fields directly to arbitrary values.
- **Internal helper methods** — a complex operation is often best broken into several small private helper methods, each handling one piece of the logic, without cluttering or complicating the class's actual public interface with methods that were only ever meant to be called internally.

You mark a field or method `private` by default, and only widen access (`protected`, package-private, or `public`) deliberately, when a genuine need for wider access is identified — this "start restrictive, widen only when needed" habit is the foundation of well-encapsulated class design.

## 3. Core concept

```java
class TemperatureSensor {
    private double celsius; // hidden — cannot be set directly from outside

    void setCelsius(double celsius) { // the ONLY way to change the value from outside
        if (celsius < -273.15) { // validates against absolute zero — impossible if the field were public
            throw new IllegalArgumentException("Below absolute zero: " + celsius);
        }
        this.celsius = celsius;
    }

    double getFahrenheit() { // exposes a DERIVED value, computed from the hidden field
        return celsius * 9.0 / 5.0 + 32.0;
    }
}
```

Because `celsius` is `private`, the *only* way any outside code can change it is through `setCelsius`, which validates every attempt — this guarantee (that `celsius` can never illegally fall below absolute zero) would be impossible to enforce if `celsius` were a `public` field that any code could assign directly, bypassing validation entirely.

## 4. Diagram

<svg viewBox="0 0 600 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A class boundary shown as a locked box containing a private field, with the only path in being through a public validating method, while any outside attempt to reach the private field directly is blocked at the compiler level">
  <rect x="8" y="8" width="584" height="134" rx="8" fill="#0d1117"/>

  <rect x="220" y="25" width="180" height="90" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="310" y="45" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">class TemperatureSensor</text>
  <text x="310" y="70" fill="#f85149" font-size="9" text-anchor="middle" font-family="monospace">private celsius 🔒</text>
  <text x="310" y="90" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="monospace">setCelsius(c) — validates</text>

  <line x1="60" y1="70" x2="220" y2="80" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#pv)"/>
  <text x="60" y="60" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">outside: setCelsius(20)</text>

  <line x1="500" y1="70" x2="400" y2="65" stroke="#f85149" stroke-width="1.5" stroke-dasharray="3,2"/>
  <text x="500" y="55" fill="#f85149" font-size="9" text-anchor="middle" font-family="sans-serif">outside: .celsius = -500 (blocked)</text>

  <defs><marker id="pv" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker></defs>
</svg>

`private` blocks all outside access, forcing every interaction through the class's own validating methods.

## 5. Runnable example

Scenario: a small `Stack`-like data structure protecting its internal array from misuse — starting with a basic private field accessed only through public methods, then extending with private helper methods supporting the public interface, then hardening into a class where private state guarantees an invariant that would be trivial to break if the fields were exposed directly.

### Level 1 — Basic

```java
public class StackBasic {
    static class SimpleStack {
        private int[] items = new int[10];
        private int count = 0;

        void push(int value) {
            items[count] = value;
            count++;
        }

        int pop() {
            count--;
            return items[count];
        }
    }

    public static void main(String[] args) {
        SimpleStack s = new SimpleStack();
        s.push(1);
        s.push(2);
        s.push(3);

        System.out.println(s.pop()); // 3
        System.out.println(s.pop()); // 2
    }
}
```

**How to run:** `java StackBasic.java`

`items` and `count` are both `private` — no code outside `SimpleStack` can read or modify them directly; every interaction must go through `push` and `pop`, which correctly maintain the stack's internal bookkeeping together.

### Level 2 — Intermediate

Same stack, now with a private helper method handling the "stack is full, need to grow" logic, kept entirely out of the public interface.

```java
import java.util.Arrays;

public class StackIntermediate {
    static class SimpleStack {
        private int[] items = new int[2]; // deliberately small, to demonstrate growth
        private int count = 0;

        private void growIfNeeded() { // private: an internal detail, not part of the public interface
            if (count == items.length) {
                items = Arrays.copyOf(items, items.length * 2);
            }
        }

        void push(int value) {
            growIfNeeded();
            items[count] = value;
            count++;
        }

        int pop() {
            count--;
            return items[count];
        }
    }

    public static void main(String[] args) {
        SimpleStack s = new SimpleStack();
        s.push(1);
        s.push(2);
        s.push(3); // triggers growIfNeeded() internally

        System.out.println(s.pop());
        System.out.println(s.pop());
        System.out.println(s.pop());
    }
}
```

**How to run:** `java StackIntermediate.java`

`growIfNeeded` is `private` because it's purely an internal implementation detail of how `push` manages capacity — callers of `push` never need to know or care whether growth happened; they only see the stack correctly accept their value, regardless of the array's current internal size.

### Level 3 — Advanced

Same stack, now demonstrating concretely why keeping `items` and `count` private matters: a guarded `pop()` prevents popping from an empty stack, a guarantee that would be trivially violated if outside code could directly manipulate `count` or `items`.

```java
import java.util.Arrays;

public class StackAdvanced {
    static class SimpleStack {
        private int[] items = new int[2];
        private int count = 0;

        private void growIfNeeded() {
            if (count == items.length) {
                items = Arrays.copyOf(items, items.length * 2);
            }
        }

        void push(int value) {
            growIfNeeded();
            items[count] = value;
            count++;
        }

        int pop() {
            if (count == 0) {
                throw new IllegalStateException("Cannot pop from an empty stack");
            }
            count--;
            return items[count];
        }

        boolean isEmpty() {
            return count == 0;
        }
    }

    public static void main(String[] args) {
        SimpleStack s = new SimpleStack();
        s.push(10);

        System.out.println(s.pop());   // 10
        System.out.println(s.isEmpty()); // true

        try {
            s.pop(); // stack is now empty
        } catch (IllegalStateException e) {
            System.out.println("Rejected: " + e.getMessage());
        }
    }
}
```

**How to run:** `java StackAdvanced.java`

`pop()`'s guard, `if (count == 0)`, is only a *reliable* guarantee because `count` is `private` — no outside code can directly set `count` to some inconsistent value that doesn't match the actual number of elements in `items`, since every modification to `count` happens exclusively inside `push` and `pop`, both of which keep it correctly synchronized with the array's real contents.

## 6. Walkthrough

Trace `StackAdvanced.main`:

**`s.push(10)`.** `growIfNeeded()` checks `count (0) == items.length (2)` — false, no growth needed. `items[0] = 10`. `count++` makes it `1`.

**`s.pop()` (first call).** `count == 0`? `1 == 0` is false — no exception. `count--` makes it `0`. Returns `items[0]`, which is `10`. Prints `10`.

**`s.isEmpty()`.** `count == 0` is `0 == 0`, true. Prints `true`.

**`s.pop()` (second call).** `count == 0`? `0 == 0` is true — the guard fires immediately, throwing `IllegalStateException("Cannot pop from an empty stack")` before `count--` or the array access ever happen.

```
push(10): items[0]=10, count: 0 -> 1
pop():    count==0? no -> count: 1 -> 0, return items[0]=10
isEmpty(): count==0? yes -> true
pop() again: count==0? yes -> throw IllegalStateException, caught in main
```

**Final output.** `10`, then `true`, then `"Rejected: Cannot pop from an empty stack"` — the exception is only reachable, and reliable, because `count` is `private` and can only ever be modified consistently by `push` and `pop` themselves.

## 7. Gotchas & takeaways

> **`private` is per-class, not per-object — two different instances of the same class can freely access each other's private fields and methods**, since the restriction applies to *which class's code* is doing the accessing, not to which specific object owns the data. A method like `boolean isBiggerThan(Wallet other) { return this.balance > other.balance; }` legally reads `other.balance` directly, even though `balance` is `private`, because this code lives inside `Wallet` itself.

> **Making a field `private` is what makes validation in setters and constructors actually *meaningful* — if the field were `public`, any outside code could simply bypass the validating method entirely** and assign an invalid value directly, making all that validation logic pointless. `private` is the mechanism that makes encapsulation (the next topic) actually enforceable, not just a suggestion.

- `private` restricts access to the exact same class only — not subclasses, not the same package, nowhere else.
- It's the appropriate default for internal fields and helper methods that shouldn't be part of a class's public interface.
- `private` fields can only be validated and modified through the class's own methods, which is what makes guaranteed invariants (like "count always matches the array's real contents") possible.
- Access is per-class, not per-object — one instance's methods can freely access another instance's private members, as long as both are the same class.
