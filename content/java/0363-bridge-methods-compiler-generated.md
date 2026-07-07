---
card: java
gi: 363
slug: bridge-methods-compiler-generated
title: Bridge methods (compiler-generated)
---

## 1. What it is

A **bridge method** is an extra method the compiler silently inserts into a class file when generics and inheritance interact in a way that erasure would otherwise break. You never write a bridge method yourself — `javac` generates it automatically, gives it the same name as your real method but with erased (typically `Object`-based) parameter or return types, and marks it `synthetic` and `bridge` in the bytecode. It exists purely to keep polymorphism working correctly after type erasure has flattened away the generic type information.

## 2. Why & when

Erasure means that at runtime, `class IntBox extends Box<Integer>` overriding `void set(Integer value)` actually needs to override `void set(Object value)` in bytecode, because `Box<T>`'s erased form declares `set(Object)`. If `IntBox` only had `set(Integer)` in its bytecode, it would **not** actually override the erased `Box.set(Object)` method — it would be a completely separate overload, and calling `set` on a `Box<Integer>` reference pointed at an `IntBox` instance would invoke the wrong method (or fail), breaking the fundamental guarantee that overriding works polymorphically.

To prevent this, the compiler generates a synthetic `set(Object value)` bridge method inside `IntBox` that casts `value` to `Integer` and delegates to your real `set(Integer value)`. This happens automatically any time you override a generic superclass or interface method with a more specific type argument — you will encounter it (usually invisibly) whenever you extend a generic class or implement a generic interface with a concrete type parameter, and occasionally visibly, when reflection enumerates a class's methods and an unexpected extra method shows up.

## 3. Core concept

```java
public class BridgeDemo {
    static class Box<T> {
        void set(T value) {
            System.out.println("Box.set: " + value);
        }
    }

    static class IntBox extends Box<Integer> {
        @Override
        void set(Integer value) { // real method you wrote
            System.out.println("IntBox.set: " + value);
        }
    }

    public static void main(String[] args) throws Exception {
        for (var m : IntBox.class.getDeclaredMethods()) {
            System.out.println(m.getName() + "(" + m.getParameterTypes()[0].getSimpleName()
                    + ") synthetic=" + m.isSynthetic());
        }
    }
}
```

**How to run:** `java BridgeDemo.java`

`IntBox.class.getDeclaredMethods()` reveals **two** `set` methods, even though you only wrote one: your real `set(Integer)`, and a compiler-generated `set(Object)` bridge with `isSynthetic() == true`. The bridge exists solely so that a `Box<Integer>` reference can correctly dispatch to `IntBox`'s override at runtime.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="calling set through an erased Box reference invokes the synthetic bridge method set(Object), which casts and delegates to the real set(Integer) method">
  <rect x="8" y="8" width="624" height="174" rx="8" fill="#0d1117"/>
  <text x="20" y="30" fill="#e6edf3" font-size="11">Box&lt;Integer&gt; ref = new IntBox();  ref.set(5);</text>

  <rect x="30" y="50" width="220" height="45" rx="6" fill="#1c2430" stroke="#f85149"/>
  <text x="140" y="78" fill="#f85149" font-size="11" text-anchor="middle">set(Object value) -- bridge</text>

  <text x="270" y="78" fill="#8b949e" font-size="10">casts, delegates -&gt;</text>

  <rect x="400" y="50" width="220" height="45" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="510" y="78" fill="#6db33f" font-size="11" text-anchor="middle">set(Integer value) -- your code</text>

  <text x="20" y="130" fill="#8b949e" font-size="10">Erasure makes Box.set(T) become set(Object) in bytecode. Without the bridge, IntBox.set(Integer)</text>
  <text x="20" y="150" fill="#8b949e" font-size="10">would be a distinct overload, not a real override, and polymorphic dispatch through the erased type would break.</text>
</svg>

## 5. Runnable example

Scenario: a `Comparable`-style ranking type, evolved from an unbridged mismatch you can reason about, through observing the compiler's bridge with reflection, to a case where a bridge silently fixes real polymorphic dispatch through a superclass reference.

### Level 1 — Basic

```java
public class RankBasic {
    static class Ranked<T extends Comparable<T>> {
        T value;
        Ranked(T value) { this.value = value; }

        int compareTo(T other) {
            return value.compareTo(other);
        }
    }

    public static void main(String[] args) {
        Ranked<Integer> r = new Ranked<>(10);
        System.out.println(r.compareTo(5)); // ordinary generic call, no subclassing yet
    }
}
```

**How to run:** `java RankBasic.java`

No overriding happens yet, so no bridge is generated — this just establishes the baseline generic class the next levels will extend.

### Level 2 — Intermediate

```java
import java.util.Arrays;

public class RankIntermediate {
    static class Ranked<T extends Comparable<T>> {
        T value;
        Ranked(T value) { this.value = value; }
        int compareTo(T other) { return value.compareTo(other); }
    }

    static class RankedInt extends Ranked<Integer> {
        RankedInt(Integer value) { super(value); }

        @Override
        int compareTo(Integer other) { // overrides the erased compareTo(Object) via a bridge
            System.out.println("RankedInt.compareTo called with " + other);
            return super.compareTo(other);
        }
    }

    public static void main(String[] args) throws Exception {
        for (var m : Arrays.stream(RankedInt.class.getDeclaredMethods())
                .sorted((a, b) -> a.toString().compareTo(b.toString())).toList()) {
            System.out.println(m.getName() + "(" + m.getParameterTypes()[0].getSimpleName()
                    + ") synthetic=" + m.isSynthetic());
        }
    }
}
```

**How to run:** `java RankIntermediate.java`

Reflecting over `RankedInt` reveals the compiler-generated `compareTo(Object)` bridge alongside your real `compareTo(Integer)` — proof the compiler had to insert an extra method just to keep the override valid after erasure.

### Level 3 — Advanced

```java
public class RankAdvanced {
    static class Ranked<T extends Comparable<T>> {
        T value;
        Ranked(T value) { this.value = value; }
        int compareTo(T other) { return value.compareTo(other); }
    }

    static class RankedInt extends Ranked<Integer> {
        RankedInt(Integer value) { super(value); }
        @Override
        int compareTo(Integer other) {
            System.out.println("RankedInt.compareTo(" + other + ") on value=" + value);
            return super.compareTo(other);
        }
    }

    @SuppressWarnings("unchecked")
    public static void main(String[] args) {
        Ranked<Integer> ref = new RankedInt(10); // erased superclass reference
        int result = ref.compareTo(5); // dispatches through the bridge at runtime, not directly
        System.out.println("Result: " + result);
    }
}
```

**How to run:** `java RankAdvanced.java`

Calling `compareTo` through the **superclass-typed** reference `ref` is exactly the scenario bridges exist for: at the bytecode level, this call targets `compareTo(Object)`, which only resolves to `RankedInt`'s overridden logic *because* the compiler generated a bridge method to receive that call and forward it to `compareTo(Integer)` — without it, this line would silently call `Ranked`'s original logic instead of `RankedInt`'s override.

## 6. Walkthrough

Execution starts in `main`. `new RankedInt(10)` runs `RankedInt`'s constructor, which calls `super(value)`, setting `Ranked.value` to `10`. The result is assigned to `ref`, declared as `Ranked<Integer>` — an erased-to-`Ranked` reference at runtime, but the actual object is a `RankedInt`.

`ref.compareTo(5)` is where the bridge matters. Because `ref`'s static type is `Ranked<Integer>`, and erasure turns `Ranked<T>.compareTo(T)` into `compareTo(Object)` in bytecode, the call at this call site is compiled to invoke `compareTo(Object)`. The JVM looks up the actual runtime class of the object (`RankedInt`) for that method signature and finds the **synthetic bridge** `compareTo(Object)` that the compiler generated inside `RankedInt`. That bridge casts its `Object` parameter to `Integer` and calls the real `compareTo(Integer other)` you wrote.

Inside your real `compareTo(Integer other)`: it prints `RankedInt.compareTo(5) on value=10`, then calls `super.compareTo(other)`, which runs `Ranked`'s original logic: `value.compareTo(other)`, i.e., `Integer.valueOf(10).compareTo(5)`, which returns a positive number (`1`) since `10 > 5`.

That `1` is returned back up through the real method, then through the bridge, and finally assigned to `result` in `main`, which prints `Result: 1`.

Expected output:
```
RankedInt.compareTo(5) on value=10
Result: 1
```

## 7. Gotchas & takeaways

> If you use reflection to enumerate a class's methods (`getDeclaredMethods()`) and see more overloads than you wrote — especially ones taking `Object` where you expected a specific type — check `Method.isSynthetic()` before assuming it's a real, hand-written overload; it's very likely a compiler-generated bridge.

- Bridge methods are inserted automatically whenever a subclass overrides a generic superclass or interface method with a more specific type parameter — you don't write them and rarely need to think about them.
- They exist because type erasure turns generic method signatures into their erased (often `Object`-based) form in bytecode, and without a bridge, an "override" written with the specific type would actually be a separate overload, breaking polymorphic dispatch.
- Reflection code that iterates `getDeclaredMethods()` should generally filter out `isSynthetic()` methods to avoid double-counting or misinterpreting bridges as real API methods.
- You can observe bridges directly with `javap -p -c` on a compiled `.class` file — look for methods marked `bridge, synthetic` in the output.
- Bridges are a compiler implementation detail that makes erasure-based generics coexist correctly with normal method overriding — understanding them mostly matters for debugging reflection-heavy code or reading decompiled bytecode, not for everyday application logic.
