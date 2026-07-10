---
card: java
gi: 951
slug: heap-pollution
title: Heap pollution
---

## 1. What it is

Heap pollution is the situation where a variable of a parameterized type ends up referring to an object that is not actually of that parameterized type — a `List<String>` reference, for instance, that actually points to a `List` object secretly holding an `Integer`. This can only happen through an unchecked operation the compiler was forced to allow (typically an unchecked cast, or mixing raw types with generic types), because [type erasure](0359-type-erasure.md) means the JVM itself has no way to verify, at the point of the cast, that the object genuinely matches the claimed type argument. The compiler always warns about this ("unchecked cast" or "unchecked conversion") precisely because it cannot itself guarantee safety here — it's trusting the programmer's assertion, and if that assertion is wrong, the mismatch doesn't fail immediately at the cast; it lies dormant until code elsewhere tries to use the value *as* the claimed type, at which point a `ClassCastException` is thrown at a location that can be confusingly far from the actual mistake.

## 2. Why & when

Heap pollution matters practically whenever you mix raw types with parameterized ones (calling a generic method through a raw-typed reference, which suppresses generic type checking for that call entirely), when you perform an explicit unchecked cast (`(List<String>) someRawList`), or — a subtler and very common case — with varargs methods that have a generic parameter type (`static <T> List<T> listOf(T... items)`), where the varargs mechanism itself creates an array of the erased type behind the scenes, and certain uses of that array can pollute it if handled carelessly, which is exactly why the JDK marks such methods `@SafeVarargs` when (and only when) the implementation has been manually verified not to leak or misuse that internal array. Recognizing the warning ("unchecked cast," "unchecked call," "unchecked generic array creation") is the practical skill here — the compiler is telling you, explicitly, "I cannot verify this is safe; if you're wrong, this will fail later, somewhere else, in a way that will be harder to trace back to this exact line," and the right response is either restructuring the code to avoid the unchecked operation entirely, or, when it's genuinely unavoidable and you've manually verified safety, suppressing the warning narrowly with a comment explaining why it's actually safe.

## 3. Core concept

```
List rawList = new ArrayList();      // raw type -- no generic checking at all
rawList.add("a string");
rawList.add(42);                     // compiler allows this -- rawList has NO type parameter

List<String> polluted = rawList;     // unchecked conversion -- compiler WARNS, but allows it
                                      // 'polluted' now claims List<String>, but rawList
                                      // secretly contains an Integer too -- HEAP POLLUTED

String s = polluted.get(0);          // fine -- happens to be a String
String s2 = polluted.get(1);         // ClassCastException HERE -- far from where the
                                      // actual mistake (rawList.add(42)) happened
```

The defining characteristic of heap pollution: the actual type mismatch is created at one point (an unchecked cast or raw-type mixing), but the failure surfaces later, at a completely different point (wherever the mistyped value is first used as its claimed type) — this gap between cause and symptom is what makes it a notoriously tricky class of bug to trace.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A timeline showing an unchecked cast creating heap pollution at one point in the code, with the resulting ClassCastException surfacing much later at an unrelated point where the value is actually used" >
  <line x1="20" y1="90" x2="620" y2="90" stroke="#8b949e"/>
  <text x="320" y="110" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">time / call sequence -&gt;</text>

  <circle cx="100" cy="70" r="6" fill="#f0883e"/>
  <text x="100" y="50" fill="#f0883e" font-size="9" text-anchor="middle" font-family="sans-serif">Unchecked cast/conversion</text>
  <text x="100" y="63" fill="#f0883e" font-size="8" text-anchor="middle" font-family="sans-serif">(the ACTUAL mistake)</text>

  <circle cx="500" cy="70" r="6" fill="#79c0ff"/>
  <text x="500" y="50" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">ClassCastException thrown</text>
  <text x="500" y="63" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">(where it's finally NOTICED)</text>

  <line x1="106" y1="76" x2="494" y2="76" stroke="#6db33f" stroke-dasharray="4"/>
  <text x="320" y="140" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">The gap between cause and symptom is exactly what makes heap pollution hard to debug</text>
</svg>

*Heap pollution's defining trait: the mistake and its symptom are separated in time and location, unlike most type errors, which the compiler catches immediately.*

## 5. Runnable example

Scenario: reproduce genuine heap pollution end to end and observe the delayed failure directly, then fix it by eliminating the raw-type mixing that caused it, then handle the trickier varargs-based pollution case and understand exactly what `@SafeVarargs` does and doesn't guarantee.

### Level 1 — Basic

```java
import java.util.*;

@SuppressWarnings({"rawtypes", "unchecked"})
public class HeapPollutionBasic {
    static void addRawly(List rawList) {
        rawList.add("a string");
        rawList.add(42); // no compile error -- rawList has no type parameter to check against
    }

    public static void main(String[] args) {
        List<String> strings = new ArrayList<>();
        addRawly(strings); // strings is passed as a raw List here -- pollution begins

        System.out.println(strings.get(0)); // fine
        try {
            String s = strings.get(1); // ClassCastException HERE -- far from addRawly's Integer add
        } catch (ClassCastException e) {
            System.out.println("caught: " + e.getMessage());
        }
    }
}
```

**How to run:** `java HeapPollutionBasic.java` (JDK 17+).

Expected output:
```
a string
caught: class java.lang.Integer cannot be cast to class java.lang.String
```

The actual mistake — adding an `Integer` to what's genuinely meant to be a `List<String>` — happens inside `addRawly`, which accepts a raw `List` and therefore has no compile-time type checking at all; the failure only surfaces later, in `main`, at the point where `get(1)`'s result is implicitly cast to `String` — exactly the cause-and-symptom gap heap pollution is defined by.

### Level 2 — Intermediate

```java
import java.util.*;

public class HeapPollutionFixed {
    // FIXED: genuinely generic, not raw -- the compiler now enforces the type at the call site itself.
    static void addSafely(List<String> list) {
        list.add("a string");
        // list.add(42); // would NOT compile -- this is exactly the safety raw types gave up
    }

    public static void main(String[] args) {
        List<String> strings = new ArrayList<>();
        addSafely(strings);
        System.out.println(strings);
        System.out.println("no unchecked warnings, no possible pollution -- caught at COMPILE time instead");
    }
}
```

**How to run:** `java HeapPollutionFixed.java` (JDK 17+).

Expected output:
```
[a string]
no unchecked warnings, no possible pollution -- caught at COMPILE time instead
```

The real-world concern added: simply changing `addRawly`'s parameter from raw `List` to genuinely generic `List<String>` moves the type mismatch from an eventual, hard-to-trace runtime `ClassCastException` to an immediate, precisely-located compile error (the commented-out `list.add(42)` line) — this is the general fix for heap pollution: eliminate the raw-type/generic-type mixing entirely rather than working around it, whenever that's possible.

### Level 3 — Advanced

```java
import java.util.*;

public class HeapPollutionVarargs {
    // UNSAFE version: this method's varargs array can be polluted from OUTSIDE the method,
    // because the array parameter is exposed and stored, not just read.
    static <T> T[] dangerouslyExpose(T... items) {
        return items; // exposing the internal varargs array is the classic varargs pollution mistake
    }

    // SAFE version: only reads from the varargs array, never exposes or stores it --
    // this is exactly the contract @SafeVarargs asserts you've upheld.
    @SafeVarargs
    static <T> List<T> safeListOf(T... items) {
        List<T> result = new ArrayList<>();
        for (T item : items) result.add(item);
        return result;
    }

    public static void main(String[] args) {
        Object[] exposed = dangerouslyExpose("a", "b"); // T inferred as String, but returned as Object[]
        exposed[0] = 42; // no compile error here! exposed's static type is Object[]
        // The underlying array, however, is actually a String[] (from the varargs call) --
        // this line would throw ArrayStoreException, a DIFFERENT symptom of the same root problem.
        try {
            exposed[0] = 42;
        } catch (ArrayStoreException e) {
            System.out.println("caught: " + e.getClass().getSimpleName() + " -- exposing a varargs array leaks its erased runtime type");
        }

        List<String> safe = safeListOf("x", "y", "z");
        System.out.println("safeListOf result: " + safe);
    }
}
```

**How to run:** `java HeapPollutionVarargs.java` (JDK 17+).

Expected output:
```
caught: ArrayStoreException -- exposing a varargs array leaks its erased runtime type
safeListOf result: [x, y, z]
```

The production-flavored hard case: a generic varargs parameter (`T... items`) is implemented under the hood as an array whose actual runtime component type is determined by the caller's arguments (here, genuinely `String[]`, since both arguments were strings) — `dangerouslyExpose` returns this array typed as `Object[]` (erasure's doing), which lets calling code attempt `exposed[0] = 42` without any compile error, but the array's real, erased-but-still-present runtime type (`String[]`) rejects storing an `Integer` into it, throwing `ArrayStoreException` — a second, related symptom of the same underlying class of problem, and exactly why methods that merely *read* from a generic varargs parameter (like `safeListOf`, which only iterates and copies elements, never exposing or storing the array itself) can be safely marked `@SafeVarargs`, while methods that expose or store the raw array (`dangerouslyExpose`) cannot be made safe at all and should never carry that annotation.

## 6. Walkthrough

Tracing `HeapPollutionVarargs.main` end to end:

1. `dangerouslyExpose("a", "b")` is called — the compiler infers `T = String` for this call, and the varargs mechanism creates an actual array behind the scenes to hold the two `String` arguments; critically, this array's genuine runtime component type is `String[]`, not the generic, erased `Object[]` the method signature suggests.
2. `dangerouslyExpose` simply returns this array as-is — since the method's return type is `T[]`, which erases to `Object[]`, the caller receives a reference statically typed as `Object[]`, even though the actual object underneath is still, genuinely, a `String[]` at runtime (array component types, unlike generic type arguments, are *not* erased — arrays remember their actual element type).
3. Back in `main`, `exposed` is declared as `Object[]` — this static type permits assigning any `Object` (including an `Integer`) into any of its slots, as far as the compiler can tell, so `exposed[0] = 42` compiles without complaint.
4. At runtime, however, the array store operation checks the array's *actual* component type (a check the JVM always performs for array stores, precisely because arrays are covariant and therefore need a runtime safety net that generics' erasure otherwise lacks) — since the real array is a `String[]`, attempting to store an `Integer` into it fails this check, and the JVM throws `ArrayStoreException` rather than silently corrupting the array.
5. This demonstrates a subtly different failure mode from the basic raw-type pollution example: there, the mismatch was caught late, as a `ClassCastException` when *reading* a polluted value back out; here, it's caught immediately, as an `ArrayStoreException`, when *writing* an incompatible value into an array whose true component type was concealed by generic erasure at the method's returned type — both are forms of heap pollution, differing only in which specific operation (a later read versus an immediate write) exposes the underlying type mismatch.
6. `safeListOf("x", "y", "z")` demonstrates the safe alternative: it never exposes or stores its internal varargs array outside the method — it only iterates over it, copying elements into a genuinely fresh, ordinary `ArrayList<T>`, which is why it correctly carries `@SafeVarargs`: this annotation is a promise, verified by the programmer (not the compiler), that the method's own body never performs an operation on its varargs array that could pollute the heap or leak the erased array reference to unsuspecting calling code.

## 7. Gotchas & takeaways

> **Gotcha:** `@SafeVarargs` is a manual assertion by the programmer, not something the compiler verifies for you — applying it to a method that *does* expose or store its varargs array (like `dangerouslyExpose` above) is a lie the compiler will not catch, and doing so defeats the entire purpose of the annotation, silently reintroducing exactly the pollution risk it exists to rule out; only apply it after genuinely confirming the method never leaks the array.

- Heap pollution occurs when a variable of a parameterized type actually refers to an object that doesn't match that type argument, caused by an unchecked cast or by mixing raw types with generics — something the compiler warns about but cannot fully prevent, due to [type erasure](0359-type-erasure.md).
- Its defining, debugging-relevant trait is a gap between cause (the unchecked operation) and symptom (a `ClassCastException` or `ArrayStoreException` at a later, often unrelated point in the code).
- The general fix is eliminating raw-type/generic mixing entirely — converting a raw-typed parameter to a genuinely generic one moves the error from a delayed runtime exception to an immediate, precisely-located compile error.
- Generic varargs methods (`T... items`) create a real array under the hood whose actual runtime component type is determined by the call site, but which the method's own signature exposes only as the erased type — exposing or storing this array outside the method can pollute the heap, while merely reading from it cannot.
- `@SafeVarargs` is a manual, unverified promise that a method's body never exposes or stores its varargs array unsafely — apply it only after confirming this yourself, never reflexively to silence a warning.
- See [type erasure](0359-type-erasure.md) for the underlying mechanism that makes heap pollution possible at all, and [generics & arrays interplay](0953-generics-arrays-interplay.md) for more on why arrays and generics interact this awkwardly in Java.
