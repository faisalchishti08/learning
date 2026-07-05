---
card: java
gi: 183
slug: covariance-of-arrays-arraystoreexception
title: Covariance of arrays & ArrayStoreException
---

## 1. What it is

**Array covariance** is a Java rule stating that if `Sub` is a subtype of `Super`, then `Sub[]` is treated as a subtype of `Super[]` — meaning a `Sub[]` reference can be assigned to a variable of type `Super[]`. This is convenient, but it comes with a runtime safety net called **`ArrayStoreException`**: if code then tries to store an element into that array that isn't actually compatible with its *real*, original element type, the JVM throws `ArrayStoreException` at the moment of the write, since the compiler alone cannot catch this mistake.

```java
Object[] objects = new String[3]; // legal: String[] is-a Object[] (covariance)
objects[0] = "safe";               // fine — a String fits in a String[] underneath

objects[1] = 42; // COMPILES (Object[] accepts any Object) but THROWS ArrayStoreException at runtime
                  // because the array is really a String[] underneath, and Integer isn't a String
```

The compiler only sees the *declared* type, `Object[]`, and happily allows storing an `Integer` into it — it's only at runtime, when the JVM checks the array's *actual* underlying type, that the mismatch is caught.

## 2. Why & when

This behaviour is a deliberate, if imperfect, design trade-off from early Java (predating generics), made to support certain APIs that needed to operate generically over arrays of different types:

- **`Object[]` parameters accepting any array type** — some pre-generics APIs (like parts of `java.util.Arrays` and reflection) are written to take `Object[]` so they can operate on arrays of *any* reference type, relying on covariance to accept a `String[]`, `Integer[]`, etc.
- **The safety net exists because compile-time checking isn't enough** — without `ArrayStoreException`, storing a value of the wrong type into a covariant array reference would silently corrupt memory; the runtime check preserves type safety at the cost of moving the error from compile time to runtime.
- **Generics deliberately do NOT have this problem** — a `List<String>` cannot be assigned to a `List<Object>` variable at all (a compile error), which is one reason modern code prefers generic collections over arrays when flexibility across types is needed, since a `List` catches the mistake at compile time instead of at runtime.

You need to be aware of this whenever you pass an array by its more general (supertype) type — knowing that a seemingly-valid assignment can still blow up later, at the specific line that performs an incompatible write.

## 3. Core concept

```java
public class CovarianceDemo {
    public static void main(String[] args) {
        String[] strings = { "a", "b", "c" };

        Object[] asObjects = strings; // legal — covariance: String[] is-a Object[]

        System.out.println(asObjects[0]); // fine — reading is always safe

        try {
            asObjects[1] = 100; // compiles (Object[] accepts any Object)... but throws at runtime
        } catch (ArrayStoreException e) {
            System.out.println("Caught: " + e.getMessage()); // java.lang.Integer
        }
    }
}
```

Reading through the wider `Object[]` reference is always completely safe — `asObjects[0]` just retrieves whatever `String` is really stored there; it's specifically **writing** an incompatible type through the wider reference that triggers the runtime check and throws.

## 4. Diagram

<svg viewBox="0 0 620 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A String array assigned to an Object array reference, showing that reading through the wider reference is safe, but writing an Integer through it throws ArrayStoreException because the real underlying array is still a String array">
  <rect x="8" y="8" width="604" height="154" rx="8" fill="#0d1117"/>
  <text x="310" y="24" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Object[] asObjects = strings;  (strings is really a String[] underneath)</text>

  <rect x="230" y="40" width="160" height="30" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="310" y="60" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="monospace">real array: String[3]</text>

  <line x1="310" y1="70" x2="310" y2="90" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="310" y="103" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">viewed through Object[] reference</text>

  <text x="60" y="135" fill="#6db33f" font-size="11" font-family="monospace">asObjects[0]        (read)   -&gt; OK, always safe</text>
  <text x="60" y="155" fill="#f85149" font-size="11" font-family="monospace">asObjects[1] = 100  (write)  -&gt; ArrayStoreException (real array is String[])</text>
</svg>

The array's real, underlying type never changes — only writes that violate it are rejected, and only at runtime.

## 5. Runnable example

Scenario: a utility method that logs the contents of "any array of objects" — starting with a basic covariant assignment, then extending to a method parameter accepting `Object[]` to work generically, then hardening into a method that defensively catches `ArrayStoreException` when a caller tries to write an incompatible value through it.

### Level 1 — Basic

```java
public class CovarianceBasic {
    public static void main(String[] args) {
        Integer[] numbers = { 1, 2, 3 };
        Object[] asObjects = numbers; // legal: Integer[] is-a Object[]

        System.out.println("First element: " + asObjects[0]);
        System.out.println("Same array? " + (asObjects == numbers)); // true — no copy was made
    }
}
```

**How to run:** `java CovarianceBasic.java`

`asObjects == numbers` prints `true` because covariant assignment does **not** create a copy — `asObjects` is simply a second reference to the exact same array object, just viewed through a wider, more general declared type.

### Level 2 — Intermediate

Same idea, now with a method parameter typed `Object[]` so it can log elements from an array of any reference type — demonstrating the intended, safe use case for covariance.

```java
public class CovarianceIntermediate {

    static void logAll(Object[] items) {
        for (Object item : items) {
            System.out.println("Logged: " + item);
        }
    }

    public static void main(String[] args) {
        String[] words = { "alpha", "beta" };
        Integer[] numbers = { 10, 20 };

        logAll(words);   // String[] accepted via covariance
        logAll(numbers);  // Integer[] accepted the same way
    }
}
```

**How to run:** `java CovarianceIntermediate.java`

`logAll` only ever *reads* from `items`, never writes into it — this is exactly the safe pattern covariance was designed for: one method body works for arrays of any reference type, with no risk of `ArrayStoreException` since nothing is ever stored back into the array.

### Level 3 — Advanced

Same idea, now with a method that *does* write into its `Object[]` parameter (resetting every slot to a given value), catching `ArrayStoreException` defensively since the caller's real array type is unknown to the method body.

```java
public class CovarianceAdvanced {

    static void resetAll(Object[] items, Object resetValue) {
        for (int i = 0; i < items.length; i++) {
            try {
                items[i] = resetValue; // may fail if resetValue's type doesn't match the array's REAL type
            } catch (ArrayStoreException e) {
                System.out.println("Cannot store " + resetValue.getClass().getSimpleName()
                        + " into this array's real element type: " + e.getMessage());
                return; // stop; further attempts would fail identically
            }
        }
        System.out.println("Reset complete.");
    }

    public static void main(String[] args) {
        String[] words = { "alpha", "beta", "gamma" };

        resetAll(words, "reset");  // String into String[] underneath -- fine
        System.out.println(java.util.Arrays.toString(words));

        resetAll(words, 999);      // Integer into a REAL String[] -- throws, caught inside resetAll
    }
}
```

**How to run:** `java CovarianceAdvanced.java`

`resetAll(words, 999)` compiles cleanly since the parameter type is `Object[]` and `999` autoboxes to `Integer`, a valid `Object` — but at runtime, the first attempted write (`items[0] = 999`) discovers that the array's real underlying type is `String[]`, which cannot hold an `Integer`, and throws `ArrayStoreException`, caught and reported inside `resetAll` itself.

## 6. Walkthrough

Trace both calls to `resetAll` in `CovarianceAdvanced.main`:

**First call: `resetAll(words, "reset")`.** `words` is a real `String[]`, passed as `Object[] items`. The loop runs `i` from `0` to `2`: each `items[i] = "reset"` succeeds, since `"reset"` is a genuine `String`, compatible with the array's real element type. After the loop, prints `"Reset complete."` `words` is now `["reset", "reset", "reset"]`.

**Second call: `resetAll(words, 999)`.** `words` is still really a `String[]` (now holding `"reset"` three times from the previous call). The loop begins: `i = 0`, `items[0] = 999` attempts to store an `Integer` into a slot of a real `String[]`. The JVM's runtime type check fails, and `ArrayStoreException` is thrown immediately — before any other slot is touched.

**Catch and report.** The `catch (ArrayStoreException e)` block inside `resetAll` catches this, prints a message naming `resetValue`'s class (`Integer`) and the exception's message (typically `"java.lang.Integer"`), then `return`s early — the loop never reaches `i = 1` or `i = 2`.

```
call 1: resetAll(words, "reset")
  words is really String[]; "reset" is a String -> every write succeeds -> "Reset complete."

call 2: resetAll(words, 999)
  words is still really String[]; 999 autoboxes to Integer
  items[0] = 999 -> ArrayStoreException (Integer incompatible with real String[] type)
  caught inside resetAll -> prints message, returns early (i never reaches 1 or 2)
```

## 7. Gotchas & takeaways

> **Array covariance means the compiler cannot catch a type mismatch that the JVM discovers only at runtime, at the exact moment of an incompatible write.** Code that compiles cleanly can still throw `ArrayStoreException` in production if a caller passes an array of a narrower type than the parameter's declared type suggests, and later code tries to write an incompatible value into it.

> **Generic collections (`List<T>`) intentionally do not have this problem** — `List<String>` cannot be assigned to a `List<Object>` variable at all, a compile-time error rather than a deferred runtime one. This is a key reason modern Java code favours generic collections over raw arrays when working with heterogeneous or uncertain element types.

- Covariance lets a `Sub[]` be assigned to a `Super[]`-typed variable or parameter, without copying — both references point at the same underlying array.
- Reading through the wider reference is always safe; writing an incompatible value throws `ArrayStoreException` at that exact line, at runtime.
- This is safe and idiomatic when a method only *reads* from an `Object[]`-typed parameter (like the logging example).
- Prefer generics (`List<T>`) over covariant arrays when a method needs to both accept and write into a collection of an uncertain, caller-determined type, since generics catch the mismatch at compile time instead.
