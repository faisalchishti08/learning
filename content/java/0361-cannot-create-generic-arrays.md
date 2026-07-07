---
card: java
gi: 361
slug: cannot-create-generic-arrays
title: Cannot create generic arrays
---

## 1. What it is

Java does not let you write `new T[10]` or `new List<String>[10]` — creating an array of a generic type (a type parameter, or a parameterized type like `List<String>`) is a compile error. You can declare a *reference* of that array type, but you cannot instantiate it directly with `new`. This restriction exists because of **type erasure**: at runtime, arrays remember their element type, but generics do not, and mixing the two would let unsafe code slip past the compiler and corrupt memory silently.

## 2. Why & when

Arrays in Java are **reified** — they know their component type at runtime and enforce it. If you create a `String[]`, storing an `Integer` into it throws an `ArrayStoreException` at the exact moment of the bad write, protecting you immediately.

Generics, by contrast, are **erased** — `List<String>` and `List<Integer>` are the same class at runtime, `List`. There is no way for the JVM to check "is this a `List<String>`?" because that information doesn't exist after compilation.

If Java allowed `new List<String>[3]`, you could assign it to a `List<?>[]` reference, insert a `List<Integer>` into one slot (arrays allow covariant writes, checked at runtime by component type — but there is no real component type here to check), and get a silent, undetected `ClassCastException` far away from where the real mistake happened. Forbidding generic array creation closes that hole at compile time, before the unsafe state can ever exist.

You run into this whenever you try to back a generic class with a plain array (a common temptation when implementing a generic stack or buffer), or when you want an array of a parameterized type like `List<String>[]`.

## 3. Core concept

```java
import java.util.List;
import java.util.ArrayList;

public class NoGenericArrays {
    public static void main(String[] args) {
        // List<String>[] bad = new List<String>[3]; // compile error: generic array creation

        Object[] boxes = new Object[3]; // legal: raw Object array
        boxes[0] = new ArrayList<String>();
        @SuppressWarnings("unchecked")
        List<String> first = (List<String>) boxes[0]; // unavoidable unchecked cast
        first.add("hello");
        System.out.println(first);
    }
}
```

**How to run:** `java NoGenericArrays.java`

The commented line is what the compiler rejects outright — `generic array creation`. The workaround shown, creating an `Object[]` and casting each element back, is the standard escape hatch: it moves the unsafe step to one clearly-marked, unchecked cast instead of hiding it inside array semantics the JVM can't verify.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="arrays remember their element type at runtime, generics are erased to a single raw type, so combining them would let a mismatched write go undetected">
  <rect x="8" y="8" width="624" height="154" rx="8" fill="#0d1117"/>
  <rect x="30" y="30" width="240" height="50" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="150" y="60" fill="#6db33f" font-size="11" text-anchor="middle">String[] — reified, checks type on write</text>

  <rect x="370" y="30" width="240" height="50" rx="6" fill="#1c2430" stroke="#f85149"/>
  <text x="490" y="60" fill="#f85149" font-size="11" text-anchor="middle">List&lt;String&gt; — erased to List at runtime</text>

  <text x="20" y="115" fill="#8b949e" font-size="10">new List&lt;String&gt;[3] would need array-style runtime checks on an erased type -- impossible, so the compiler bans it.</text>
  <text x="20" y="140" fill="#e6edf3" font-size="10">Workaround: allocate Object[], cast each element back with a single, explicit @SuppressWarnings("unchecked").</text>
</svg>

## 5. Runnable example

Scenario: building a tiny generic fixed-size stack, evolved from a naive attempt that hits the compile error, through the standard `Object[]` workaround, to a production-style version that validates the cast is at least sane.

### Level 1 — Basic

```java
public class StackAttempt {
    public static void main(String[] args) {
        // The naive, tempting approach that does NOT compile:
        // T[] items = new T[capacity]; // error: generic array creation
        System.out.println("See comment: new T[capacity] fails to compile.");
    }
}
```

**How to run:** `java StackAttempt.java`

This demonstrates the wall every generic-collection author hits first: you cannot simply back a generic class with `T[]`. The rest of the levels show the accepted way around it.

### Level 2 — Intermediate

```java
public class GenericStack<T> {
    private final Object[] items; // backing array is raw Object, not T[]
    private int size = 0;

    public GenericStack(int capacity) {
        items = new Object[capacity]; // legal: Object[] is a real, reifiable array type
    }

    public void push(T item) {
        items[size++] = item;
    }

    @SuppressWarnings("unchecked")
    public T pop() {
        T item = (T) items[--size]; // one unavoidable unchecked cast, confined here
        items[size] = null; // avoid holding a stale reference
        return item;
    }

    public static void main(String[] args) {
        GenericStack<String> stack = new GenericStack<>(3);
        stack.push("a");
        stack.push("b");
        System.out.println(stack.pop());
        System.out.println(stack.pop());
    }
}
```

**How to run:** `java GenericStack.java`

The backing store is declared as `Object[]`, not `T[]` — legal because `Object[]` is a real, reifiable array type. `push` stores into it directly; `pop` casts back to `T` with a single `@SuppressWarnings("unchecked")`, confining the one unsafe operation the whole class needs to exactly one line.

### Level 3 — Advanced

```java
import java.util.EmptyStackException;

public class GenericStackSafe<T> {
    private final Object[] items;
    private int size = 0;

    public GenericStackSafe(int capacity) {
        if (capacity <= 0) throw new IllegalArgumentException("capacity must be positive");
        items = new Object[capacity];
    }

    public void push(T item) {
        if (size == items.length) throw new IllegalStateException("stack is full");
        items[size++] = item;
    }

    @SuppressWarnings("unchecked")
    public T pop() {
        if (size == 0) throw new EmptyStackException();
        T item = (T) items[--size];
        items[size] = null;
        return item;
    }

    public static void main(String[] args) {
        GenericStackSafe<String> stack = new GenericStackSafe<>(2);
        stack.push("x");
        stack.push("y");
        System.out.println(stack.pop());
        System.out.println(stack.pop());
        try {
            stack.pop();
        } catch (EmptyStackException e) {
            System.out.println("Caught: stack was empty");
        }
    }
}
```

**How to run:** `java GenericStackSafe.java`

This adds the production-flavoured edges every real stack needs: rejecting a non-positive capacity in the constructor, refusing to `push` past capacity, and throwing `EmptyStackException` instead of an `ArrayIndexOutOfBoundsException` when `pop` is called on empty — all layered around the same core `Object[]` workaround from Level 2.

## 6. Walkthrough

Execution starts in `main`. `new GenericStackSafe<>(2)` runs the constructor: `capacity` is `2`, passes the positivity check, and `items = new Object[2]` allocates a plain two-slot `Object` array — this is legal precisely because `Object[]` is a reifiable array type, unlike `T[]`.

`stack.push("x")` checks `size == items.length` (`0 == 2`, false), then stores `"x"` at `items[0]` and increments `size` to `1`. `stack.push("y")` similarly stores `"y"` at `items[1]`, `size` becomes `2`.

`stack.pop()` is called: `size == 0` is false, so it proceeds. `(T) items[--size]` first decrements `size` to `1`, reads `items[1]` (`"y"`), and casts it to `T` (erased to `Object` at runtime, so this cast is actually a no-op bytecode-wise but the compiler treats it as an unchecked cast to `T`). It clears `items[1]` to `null` to avoid a memory leak, then returns `"y"`, which is printed.

The second `stack.pop()` follows the same path, returning `"x"` (`items[0]`), setting `size` to `0`.

The third `stack.pop()` call now finds `size == 0` true, so it throws `EmptyStackException` immediately instead of touching the array — the `catch` block catches it and prints `Caught: stack was empty`.

Expected output:
```
y
x
Caught: stack was empty
```

## 7. Gotchas & takeaways

> `new T[n]` and `new List<String>[n]` are flatly rejected by the compiler with "generic array creation" — there is no legal syntax that creates them directly. The standard workaround is always an `Object[]` backing array plus a confined, explicit unchecked cast.

- Type erasure removes generic type information at runtime; reified arrays need that information to enforce element types, so the two features cannot mix safely.
- The accepted pattern for generic collections is: back the class with `Object[]`, and cast individual elements back to `T` with a single, clearly-marked `@SuppressWarnings("unchecked")`.
- This is exactly why `ArrayList<T>` internally uses `Object[]`, not `T[]` — you're reproducing what the JDK's own collection classes do.
- Prefer using an existing generic collection (`ArrayList`, `ArrayDeque`) over hand-rolling an array-backed generic class, unless you have a specific reason (like this teaching example) to build one yourself.
- If you truly need a real, reified array of a specific type at runtime, `java.lang.reflect.Array.newInstance(Class, int)` can create one — but it needs an explicit `Class` object, since the type parameter alone doesn't carry enough information at runtime.
