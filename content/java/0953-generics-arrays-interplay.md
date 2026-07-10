---
card: java
gi: 953
slug: generics-arrays-interplay
title: Generics & arrays interplay
---

## 1. What it is

Java's arrays and its generics implement type safety through two fundamentally different, and fundamentally incompatible, strategies. Arrays are **covariant** and **reified**: `String[]` is a subtype of `Object[]`, and every array remembers its actual runtime component type, which the JVM checks on every single element store (`ArrayStoreException` if you try to store the wrong type into an array slot, as seen in [heap pollution](0951-heap-pollution.md)). Generics, by contrast, are **invariant** and **erased**: `List<String>` is *not* a subtype of `List<Object>` (even though `String` is a subtype of `Object`), and the type argument itself is discarded at compile time via [type erasure](0359-type-erasure.md), with no runtime check backing it up at all. These two systems collide directly at the point of creating an array of a generic type — `new List<String>[10]` is a compile error — because doing so would create an array whose runtime component type (needed for array covariance's safety checks) simply doesn't exist, having been erased, defeating the entire mechanism arrays rely on for their own safety.

## 2. Why & when

Understanding why arrays are covariant while generics are invariant explains the practical restriction you hit whenever mixing the two: array covariance exists historically because Java needed it before generics existed at all (to write a single `sort(Object[] array)` method usable on any array type), accepting a runtime safety net (`ArrayStoreException`) as the cost; generics arrived later specifically designed to catch type errors at *compile* time instead, and made the deliberate choice to be invariant precisely to avoid needing (or being able to provide) an equivalent runtime check, since erasure removes the information such a check would need. The direct, practical consequence — you cannot create `new T[]` or `new List<String>[]` — comes up constantly when implementing a generic class backed by an array (a custom generic stack, queue, or buffer), and understanding *why* explains both the standard workaround (create an `Object[]` internally, cast on read) and why that workaround, while common and pragmatic, comes with its own unchecked-cast tradeoff that must be handled carefully to avoid genuine [heap pollution](0951-heap-pollution.md).

## 3. Core concept

```
ARRAYS:                              GENERICS:
  covariant: String[] IS-A Object[]    invariant: List<String> is NOT List<Object>
  reified: remembers actual type       erased: type argument discarded at compile time
  checked at RUNTIME (ArrayStoreEx)    checked at COMPILE time only (no runtime backing)

Why they collide:
  new List<String>[10]
    -> would need a REIFIED component type (List<String>) for array covariance's
       runtime checks to work -- but List<String> is ERASED, so there is nothing
       for the runtime check to actually verify -- COMPILE ERROR, disallowed outright

Standard workaround for a generic class needing array-backed storage:
  private Object[] data;                    // store as raw Object[] internally
  @SuppressWarnings("unchecked")
  T get(int i) { return (T) data[i]; }      // unchecked cast on READ, carefully verified safe
```

The collision is fundamental, not a JDK oversight: reified, checked arrays and erased, unchecked generics are built on genuinely incompatible assumptions about *when* (compile time versus runtime) and *how* (static typing versus a runtime tag) type safety is enforced.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Arrays being covariant and reified with runtime checks, contrasted against generics being invariant and erased with only compile-time checks, showing why creating a generic array is disallowed" >
  <rect x="20" y="30" width="280" height="110" fill="#1c2430" stroke="#79c0ff"/>
  <text x="160" y="50" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">ARRAYS</text>
  <text x="160" y="70" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">covariant: String[] IS Object[]</text>
  <text x="160" y="85" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">REIFIED: remembers actual type</text>
  <text x="160" y="100" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">checked at RUNTIME</text>
  <text x="160" y="120" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">ArrayStoreException as the safety net</text>

  <rect x="340" y="30" width="280" height="110" fill="#1c2430" stroke="#f0883e"/>
  <text x="480" y="50" fill="#f0883e" font-size="10" text-anchor="middle" font-family="sans-serif">GENERICS</text>
  <text x="480" y="70" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">invariant: List&lt;String&gt; NOT List&lt;Object&gt;</text>
  <text x="480" y="85" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">ERASED: type argument discarded</text>
  <text x="480" y="100" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">checked at COMPILE time only</text>
  <text x="480" y="120" fill="#f0883e" font-size="8" text-anchor="middle" font-family="sans-serif">no runtime backing at all</text>
</svg>

*Two incompatible safety strategies — array covariance needs reified types to check at runtime; generics deliberately gave up reification for compile-time-only checking.*

## 5. Runnable example

Scenario: build a small generic, array-backed stack — the canonical case where this incompatibility must be navigated directly — starting with the basic `Object[]`-backed workaround, then adding a realistic resize operation that must handle the array covariance/erasure mismatch correctly, then confirming the implementation is genuinely safe by testing it against the exact heap-pollution failure mode this pattern is designed to avoid.

### Level 1 — Basic

```java
public class GenericArrayStackBasic<T> {
    private Object[] data = new Object[10]; // stored as Object[] -- NOT T[], which cannot be created
    private int size = 0;

    public void push(T item) {
        data[size++] = item;
    }

    @SuppressWarnings("unchecked")
    public T pop() {
        T item = (T) data[--size]; // unchecked cast on READ -- safe here because push() only
        data[size] = null;          // ever stores genuine T values into data
        return item;
    }

    public static void main(String[] args) {
        GenericArrayStackBasic<String> stack = new GenericArrayStackBasic<>();
        stack.push("Ada");
        stack.push("Grace");
        System.out.println(stack.pop());
        System.out.println(stack.pop());
    }
}
```

**How to run:** `java GenericArrayStackBasic.java` (JDK 17+).

Expected output:
```
Grace
Ada
```

`new T[10]` is disallowed (`T` is non-reifiable — see [reifiable vs non-reifiable types](0952-reifiable-vs-non-reifiable-types.md)), so the standard workaround creates a plain `Object[]` internally instead; the class's own `push` method is the *only* thing that ever writes into `data`, and since `push`'s parameter is genuinely typed `T`, every element stored is guaranteed to be a real `T`, making the unchecked cast in `pop` safe in practice, even though the compiler cannot itself prove it.

### Level 2 — Intermediate

```java
import java.util.Arrays;

public class GenericArrayStackResizable<T> {
    private Object[] data = new Object[4];
    private int size = 0;

    public void push(T item) {
        if (size == data.length) {
            data = Arrays.copyOf(data, data.length * 2); // resize: Arrays.copyOf works on Object[] fine
        }
        data[size++] = item;
    }

    @SuppressWarnings("unchecked")
    public T pop() {
        if (size == 0) throw new java.util.NoSuchElementException("stack is empty");
        T item = (T) data[--size];
        data[size] = null;
        return item;
    }

    public int size() { return size; }

    public static void main(String[] args) {
        GenericArrayStackResizable<Integer> stack = new GenericArrayStackResizable<>();
        for (int i = 1; i <= 10; i++) stack.push(i); // forces at least one resize (starts at capacity 4)
        System.out.println("size after pushes: " + stack.size());
        while (stack.size() > 0) {
            System.out.print(stack.pop() + " ");
        }
        System.out.println();
    }
}
```

**How to run:** `java GenericArrayStackResizable.java` (JDK 17+).

Expected output:
```
size after pushes: 10
10 9 8 7 6 5 4 3 2 1
```

The real-world concern added: resizing works cleanly precisely because the internal array is a plain `Object[]`, not a generic array — `Arrays.copyOf` (or manual array copying) works uniformly on `Object[]` regardless of what `T` actually is for any given instantiation of this class, sidestepping entirely the "cannot create `new T[]`" restriction that would otherwise block a straightforward resize implementation.

### Level 3 — Advanced

```java
import java.util.*;

public class GenericArrayStackSafetyCheck<T> {
    private Object[] data = new Object[10];
    private int size = 0;

    public void push(T item) {
        data[size++] = item; // the ONLY write path -- type safety hinges entirely on this being the only one
    }

    @SuppressWarnings("unchecked")
    public T pop() {
        return (T) data[--size];
    }

    // Deliberately unsafe method added ONLY to demonstrate what would break the safety invariant --
    // real production code should never expose the backing array like this.
    Object[] unsafeBackdoor() {
        return data;
    }

    public static void main(String[] args) {
        GenericArrayStackSafetyCheck<String> stack = new GenericArrayStackSafetyCheck<>();
        stack.push("Ada");
        stack.push("Grace");

        // Demonstrating the failure mode this pattern's safety relies on avoiding:
        // index 1 holds "Grace", the item pop() will read FIRST (LIFO) -- corrupting it
        // guarantees the very next pop() call hits the polluted slot immediately.
        stack.unsafeBackdoor()[1] = 42; // bypasses push() entirely -- pollutes the "T=String" stack

        try {
            String popped = stack.pop(); // pop() will try to cast Integer 42 to String
            System.out.println("popped: " + popped);
        } catch (ClassCastException e) {
            System.out.println("caught: " + e.getMessage());
            System.out.println("this is EXACTLY the heap pollution the push()-only-write invariant prevents");
        }
    }
}
```

**How to run:** `java GenericArrayStackSafetyCheck.java` (JDK 17+).

Expected output:
```
caught: class java.lang.Integer cannot be cast to class java.lang.String
this is EXACTLY the heap pollution the push()-only-write invariant prevents
```

The production-flavored hard case: this deliberately demonstrates *why* the `Object[]`-backed workaround's safety is conditional, not automatic — it depends entirely on the invariant that `push` (the only sanctioned write path, always accepting a genuine `T`) is the sole way anything ever enters `data`; the instant that invariant is broken (here, via a deliberately-added backdoor method exposing the raw array), the exact same heap-pollution failure mode from [heap pollution](0951-heap-pollution.md) reappears, confirming that this pattern's safety is a property of the *class's careful implementation*, not something the type system enforces on its own.

## 6. Walkthrough

Tracing `GenericArrayStackSafetyCheck.main` end to end:

1. `stack.push("Ada")` and `stack.push("Grace")` each store their argument (statically guaranteed to be `String`, since `push(T item)` is called on a `GenericArrayStackSafetyCheck<String>` instance) directly into `data[size++]` — after both calls, `data`'s first two slots genuinely hold `String` objects, and `size` is 2.
2. `stack.unsafeBackdoor()` returns the live, actual `data` array reference — not a copy — directly to calling code, completely bypassing the class's own `push` method and its implicit guarantee that only genuine `T` (here, `String`) values are ever stored.
3. `stack.unsafeBackdoor()[1] = 42` writes an `Integer` directly into `data[1]`, overwriting what had been `"Grace"` — critically, this compiles and executes without any error at this point, because `data`'s static type here is `Object[]`, and storing any `Object` (including an `Integer`) into an `Object[]` slot is perfectly legal as far as both the compiler and the array's own runtime store-type check are concerned; the array's own covariance/reification safety net only checks against its *actual* component type, `Object`, which an `Integer` trivially satisfies.
4. `stack.pop()` is called — internally, this executes `(T) data[--size]`, decrementing `size` from 2 to 1 and reading `data[1]`, which is exactly the slot just corrupted with `42` — since `data[1]` is read before `data[0]` (the stack is last-in-first-out, and `"Grace"`, at index 1, was pushed last), this single `pop()` call reaches the polluted slot immediately.
5. The unchecked cast `(T) data[1]` — with `T` erased at runtime to an implicit cast to `String` at the call site in `main` — attempts to cast the `Integer` `42` to `String`, which fails, throwing `ClassCastException` at exactly that point.
6. This confirms the underlying lesson precisely: the `Object[]`-backed generic array pattern's safety depends entirely on every write into the backing array going through a method (like `push`) that statically guarantees a genuine `T` — the moment any code path (however unusual or deliberately contrived) writes into that array without going through such a guarantee, the exact same delayed, hard-to-trace `ClassCastException` symptom from [heap pollution](0951-heap-pollution.md) reappears, because nothing about the array's own type — being just `Object[]` — can enforce the more specific invariant the class's own logic depends on.

## 7. Gotchas & takeaways

> **Gotcha:** because the backing array's true element-level type safety is entirely invisible to the compiler, tracing exactly *which* stored value is unsafe, and exactly when a corrupted slot will surface as a `ClassCastException`, requires manually reasoning about the class's specific read/write order (here, which index a LIFO `pop()` will reach first) — the compiler offers no help here at all, unlike with a genuinely reifiable, checked array.

- Arrays are covariant and reified (checked at runtime via `ArrayStoreException`); generics are invariant and erased (checked only at compile time, with no runtime backing) — these are fundamentally incompatible strategies, which is why `new T[]` and `new List<String>[]` are disallowed outright.
- The standard workaround for a generic class needing array-backed storage is an internal `Object[]`, with an unchecked cast on read — safe only as long as every write path into that array is guaranteed, by the class's own careful implementation, to store genuine `T` values.
- This safety is a property of the implementation, not something the type system enforces — exposing or otherwise bypassing the sanctioned write path (`push`, in the example above) reintroduces the exact heap-pollution failure mode this pattern is meant to avoid.
- `Arrays.copyOf` and similar array-copying utilities work uniformly on the internal `Object[]` regardless of what `T` actually is for a given instantiation, making resize operations straightforward despite the underlying generics/array restriction.
- See [heap pollution](0951-heap-pollution.md) for the general failure mode this pattern must carefully avoid, and [reifiable vs non-reifiable types](0952-reifiable-vs-non-reifiable-types.md) for the precise rule explaining exactly which types can and cannot be used to create arrays directly.
