---
card: java
gi: 359
slug: type-erasure
title: Type erasure
---

## 1. What it is

Type erasure is the mechanism by which Java implements generics: type parameters exist only at compile time, for the compiler's own type-checking purposes, and are then completely removed ("erased") from the actual compiled bytecode. `List<String>` and `List<Integer>` compile down to the exact same runtime class, `List` (with type parameters replaced by their bound, or `Object` if unbounded) — there is no way, at runtime, to ask a `List` object what type parameter it was created with, because that information simply doesn't exist anymore by then.

```java
import java.util.List;
import java.util.ArrayList;

public class ErasureDemo {
    public static void main(String[] args) {
        List<String> strings = new ArrayList<>();
        List<Integer> integers = new ArrayList<>();

        System.out.println(strings.getClass() == integers.getClass()); // true -- same runtime class!
        System.out.println(strings.getClass().getName());
    }
}
```

`strings.getClass() == integers.getClass()` prints `true` — despite being declared with different type parameters, both `ArrayList<String>` and `ArrayList<Integer>` are, at runtime, the exact same `java.util.ArrayList` class, with no trace of `String` or `Integer` anywhere in the compiled class itself.

## 2. Why & when

Generics were added to Java in version 5, years after the language and its bytecode format were already established and widely deployed — erasure was chosen specifically to keep new generic code binary-compatible with the vast amount of existing, non-generic code and already-compiled `.class` files (a goal called "migration compatibility"), at the cost of type parameters having no runtime presence at all.

- **Understanding what's actually possible with generics** — knowing that type parameters vanish at runtime explains directly why certain things you might expect to work (creating an array of a generic type, checking `instanceof List<String>`, calling `new T()`) simply cannot, no matter how you try to write them.
- **Debugging confusing generics-related compiler errors and warnings** — "unchecked cast" and "unchecked conversion" warnings exist precisely because the compiler can enforce type safety only up to the point where erasure happens; past that point, it has to trust you.
- **Explaining backward compatibility** — erasure is why code written before generics existed (using raw types) still compiles and runs correctly alongside modern generic code, since at the bytecode level, there was never a difference to begin with.

Because erasure removes type parameters entirely, certain operations are permanently impossible with a plain type parameter `T`: you cannot write `new T()` (no way to know what constructor to call at runtime), cannot write `new T[10]` (array creation needs a real runtime type), and cannot write `if (obj instanceof T)` (there's no `T` left at runtime to check against) — these are not arbitrary restrictions, they are direct, unavoidable consequences of how erasure works.

## 3. Core concept

```java
import java.util.List;
import java.util.ArrayList;
import java.lang.reflect.Method;

public class ErasureCore {
    public static void main(String[] args) throws Exception {
        List<String> list = new ArrayList<>();
        list.add("hello");

        // The compiled method signature itself, inspected via reflection, shows the ERASED type:
        Method addMethod = list.getClass().getMethod("add", Object.class); // NOT add(String)!
        System.out.println("Erased method signature: " + addMethod);

        // Demonstrating erasure's practical effect: this compiles due to erasure + an unchecked cast,
        // and only fails LATER, when the wrongly-typed value is actually retrieved and used as a String.
        @SuppressWarnings({"unchecked", "rawtypes"})
        List rawList = list; // deliberately using a raw type to bypass compile-time checks
        rawList.add(42); // compiles! erasure means there's no runtime check preventing this

        try {
            for (String s : list) System.out.println(s); // fails when it reaches the Integer
        } catch (ClassCastException e) {
            System.out.println("ClassCastException at the point of use: " + e.getMessage());
        }
    }
}
```

**How to run:** `java ErasureCore.java`

`list.getClass().getMethod("add", Object.class)` finds the method — proof that, at the bytecode level, `List<String>.add` really is just `add(Object)` — and the raw-typed `rawList.add(42)` compiles and runs without any immediate error, because erasure means the runtime `ArrayList` object genuinely has no memory of ever being restricted to `String`; the mismatch only surfaces later, at the exact point where the `Integer` is read back out and treated as a `String`.

## 4. Diagram

<svg viewBox="0 0 620 160" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="the compiler checks generic types at compile time and inserts casts, but erases all type parameter information before producing bytecode, leaving one shared runtime class per raw type">
  <rect x="8" y="8" width="604" height="144" rx="8" fill="#0d1117"/>
  <text x="20" y="30" fill="#e6edf3" font-size="10">Source code: List&lt;String&gt; list, List&lt;Integer&gt; other</text>
  <text x="20" y="55" fill="#79c0ff" font-size="10">Compile time: full type-checking, generic type info tracked, casts auto-inserted</text>
  <text x="300" y="55" fill="#8b949e" font-size="12">→ erasure →</text>
  <text x="20" y="90" fill="#f85149" font-size="10">Runtime (.class bytecode): both are simply java.util.List / ArrayList</text>
  <text x="20" y="115" fill="#8b949e" font-size="9">No String or Integer type information exists anywhere in the compiled class at runtime.</text>
</svg>

## 5. Runnable example

Scenario: a small generic container demonstrating erasure's practical limits, evolved from an attempt that naively tries operations erasure forbids, into working code that avoids them, into a production-style workaround using a `Class<T>` token to recover the runtime type information erasure otherwise discards.

### Level 1 — Basic

```java
public class ErasureBasic<T> {
    // The following would NOT compile, each for a reason directly caused by erasure:
    // T instance = new T();                 // no runtime type to construct
    // T[] array = new T[10];                // no runtime type for the array's component type
    // boolean check = (obj instanceof T);    // no runtime T to check against

    private T value;
    public void set(T value) { this.value = value; }
    public T get() { return value; }

    public static void main(String[] args) {
        ErasureBasic<String> box = new ErasureBasic<>();
        box.set("hello");
        System.out.println(box.get());
    }
}
```

**How to run:** `java ErasureBasic.java`

The commented-out lines represent the classic beginner attempts that erasure directly forbids — none of them can work, because by the time this code actually runs, there is no `T` left anywhere in the compiled class for the JVM to construct, allocate an array of, or check against.

### Level 2 — Intermediate

```java
import java.lang.reflect.Array;

public class ErasureIntermediate<T> {
    private final Class<T> type; // a "type token" -- captures what erasure would otherwise discard
    private T value;

    public ErasureIntermediate(Class<T> type) { this.type = type; }

    public void set(T value) { this.value = value; }
    public T get() { return value; }

    @SuppressWarnings("unchecked")
    public T[] createArray(int size) {
        return (T[]) Array.newInstance(type, size); // works BECAUSE we captured the real Class<T>
    }

    public static void main(String[] args) {
        ErasureIntermediate<String> box = new ErasureIntermediate<>(String.class);
        box.set("hello");
        String[] array = box.createArray(3);
        System.out.println("Array length: " + array.length + ", type: " + array.getClass().getSimpleName());
    }
}
```

**How to run:** `java ErasureIntermediate.java`

Passing an explicit `Class<T> type` argument (a "type token") lets `createArray` do what a bare `new T[size]` never could — `Array.newInstance(type, size)` uses ordinary reflection with the real, explicitly-provided `Class` object to create a correctly-typed array at runtime, sidestepping erasure by supplying the missing type information manually.

### Level 3 — Advanced

```java
import java.lang.reflect.Array;
import java.util.ArrayList;
import java.util.List;

public class ErasureAdvanced<T> {
    private final Class<T> type;
    private final List<T> items = new ArrayList<>();

    public ErasureAdvanced(Class<T> type) { this.type = type; }

    public void add(T item) { items.add(item); }

    @SuppressWarnings("unchecked")
    public T[] toArray() {
        T[] array = (T[]) Array.newInstance(type, items.size());
        for (int i = 0; i < items.size(); i++) array[i] = items.get(i);
        return array;
    }

    public boolean isInstance(Object obj) {
        return type.isInstance(obj); // a genuine runtime type check, made possible by the captured Class<T>
    }

    public static void main(String[] args) {
        ErasureAdvanced<String> collector = new ErasureAdvanced<>(String.class);
        collector.add("one");
        collector.add("two");
        collector.add("three");

        String[] result = collector.toArray();
        System.out.println("Typed array: " + java.util.Arrays.toString(result));
        System.out.println("Is 'x' a match? " + collector.isInstance("x"));
        System.out.println("Is 42 a match? " + collector.isInstance(42));
    }
}
```

**How to run:** `java ErasureAdvanced.java`

`isInstance` is the workaround for the `instanceof T` restriction: since `T` itself has no runtime presence, the class instead stores a real `Class<T> type` object at construction time and delegates the actual runtime check to `type.isInstance(obj)`, which genuinely does have runtime type information available, having been explicitly supplied by the caller rather than inferred from an erased type parameter.

## 6. Walkthrough

Execution starts in `main`, which creates `collector = new ErasureAdvanced<>(String.class)` — this explicitly passes the real `Class` object for `String` into the constructor, which is stored as `type`; this is the crucial step that recovers the information erasure would otherwise have discarded.

Three `add` calls follow: `"one"`, `"two"`, `"three"` are each appended to the internal `items` list (an ordinary `ArrayList<T>`, itself also subject to erasure, but that's fine since `items` is only ever used internally as a `List`, never needing to produce a real `T[]` array on its own).

`collector.toArray()` is called: `Array.newInstance(type, items.size())` — using ordinary reflection with the genuinely real `type` (`String.class`) — creates an actual `String[3]` array at runtime (something `new T[3]` alone could never do). The loop then copies each element from `items` into this new array. The method returns this correctly-typed `String[]`, cast (unchecked, but actually safe here since we know `type` really is `String.class`) to `T[]`.

Back in `main`, `result` is printed via `Arrays.toString`, showing `[one, two, three]`.

`collector.isInstance("x")` calls `type.isInstance("x")` — `type` is `String.class`, and `"x"` genuinely is a `String`, so this returns `true`. `collector.isInstance(42)` calls `type.isInstance(42)` — `42` (boxed as `Integer`) is not a `String`, so this returns `false`. Both results are printed.

<svg viewBox="0 0 640 160" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="a real Class object captured at construction time provides everything erasure would normally remove: array creation and instanceof-style checking both become possible again">
  <rect x="8" y="8" width="624" height="144" rx="8" fill="#0d1117"/>
  <text x="20" y="30" fill="#79c0ff" font-size="10">new ErasureAdvanced&lt;&gt;(String.class) -&gt; type field captures the REAL Class&lt;String&gt; object</text>
  <text x="20" y="55" fill="#6db33f" font-size="10">toArray(): Array.newInstance(type, size) -&gt; genuine String[3] created via reflection, not "new T[]"</text>
  <text x="20" y="85" fill="#6db33f" font-size="10">isInstance("x"): type.isInstance("x") -&gt; true  (delegates to the real Class object, not "instanceof T")</text>
  <text x="20" y="107" fill="#f85149" font-size="10">isInstance(42):  type.isInstance(42)  -&gt; false</text>
  <text x="20" y="135" fill="#8b949e" font-size="10">Everything erasure removes about T is recovered here ONLY because the caller supplied Class&lt;T&gt; explicitly.</text>
</svg>

## 7. Gotchas & takeaways

> "Unchecked cast" and "unchecked conversion" compiler warnings are the visible symptom of erasure's fundamental limit — the compiler is telling you it can no longer verify type correctness past a certain point, and is trusting your code to be right; suppressing the warning doesn't make the underlying risk disappear, it just silences the compiler's honest admission of what it can't check.

- Type erasure removes all generic type parameter information from compiled bytecode — `List<String>` and `List<Integer>` are the exact same runtime class, with type parameters replaced by their bound (or `Object`, if unbounded).
- Erasure directly forbids `new T()`, `new T[]`, and `instanceof T` inside generic code with a bare, unqualified type parameter — these aren't arbitrary rules, they're the mechanical consequence of `T` having no representation at runtime.
- A "type token" — explicitly passing a `Class<T>` object alongside the type parameter — is the standard workaround for recovering runtime type information erasure would otherwise discard, enabling genuine array creation and runtime type checks.
- Erasure exists primarily for backward (migration) compatibility, letting generic and pre-generic (raw-typed) code interoperate at the bytecode level without any special casing.
- Generics are, from erasure's perspective, purely a compile-time discipline — all the actual type safety benefit happens during compilation; by the time code runs, the JVM enforces nothing about generic type parameters that wasn't already checked (or explicitly bypassed) beforehand.
