---
card: java
gi: 949
slug: wildcard-capture
title: Wildcard capture
---

## 1. What it is

Wildcard capture is the compiler's technique for handling a method call on a wildcard-typed reference (`List<?>`, `List<? extends Number>`) when the method itself needs to refer to the *specific, unknown* type the wildcard stands for — even though the caller never named it. When you write `List<?> list`, the compiler doesn't know what concrete type the `?` represents, only that *some* consistent type exists; internally, whenever it needs to reason about operations that require knowing that type is consistent across multiple uses (like calling a generic helper method that takes and returns the same type), it "captures" the wildcard into a fresh, synthetic type variable (informally often written `CAP#1`) representing "whatever that unknown type actually is," and uses that captured variable to type-check the rest of the expression. This is why a helper method with a genuine type parameter (`static <T> void swap(List<T> list, int i, int j)`) can be called on a `List<?>` and have the compiler correctly infer and enforce that both elements being swapped share the same captured type, even though neither the caller nor the wildcard type itself ever names it explicitly.

## 2. Why & when

Wildcard capture matters specifically when you're writing a generic helper method meant to operate on a wildcard-typed parameter in a way that needs to preserve "this is the same type used consistently" across multiple operations — the canonical textbook example is swapping two elements in a `List<?>`: you cannot write `list.set(i, list.get(j))` directly against a `List<?>`, because the compiler, looking only at the wildcard, cannot prove that whatever `list.get(j)` returns is safe to pass to `list.set(i, ...)` (the `?` could, as far as the compiler can locally tell at that call, be a different unknown type on each use). The standard fix is exactly what the JDK's own `Collections.swap` does: delegate to a private generic helper method whose type parameter captures the wildcard's specific type once, letting the compiler then verify that a `get` and a matching `set` against that same captured type are safe — this "capture helper" pattern is the idiomatic solution whenever you hit a "capture of ?" compiler error while trying to write to a wildcard-typed structure.

## 3. Core concept

```
List<?> list = ...;

list.set(0, list.get(1));   // COMPILE ERROR: capture of ? --
                             // compiler can't prove get(1)'s result type
                             // is safe to pass to set(0, ...) on this SAME wildcard

// Fix: delegate to a generic helper -- this is what Collections.swap actually does
static void swap(List<?> list, int i, int j) {
    swapHelper(list, i, j);   // capture happens HERE: the wildcard's unknown type
}                             // is captured into T for this one call

static <T> void swapHelper(List<T> list, int i, int j) {
    T tmp = list.get(i);      // list.get(i) and list.set(i, tmp) both operate
    list.set(i, list.get(j)); // on the SAME captured T -- now provably safe
    list.set(j, tmp);
}
```

The outer `swap` method's parameter stays `List<?>` (accepting any wildcard-typed list from a caller), while the inner `swapHelper`'s genuine type parameter `T` is what actually gets bound to the captured type for the duration of that one call — this two-method split is the idiomatic capture-helper pattern.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A wildcard List of question mark being captured into a fresh type variable T when passed to a generic helper method, allowing get and set to be verified as using the same consistent type" >
  <rect x="20" y="30" width="180" height="40" fill="#1c2430" stroke="#f0883e"/>
  <text x="110" y="54" fill="#f0883e" font-size="10" text-anchor="middle" font-family="sans-serif">List&lt;?&gt; (unknown type)</text>

  <rect x="240" y="30" width="160" height="40" fill="#1c2430" stroke="#6db33f"/>
  <text x="320" y="49" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">CAPTURE</text>
  <text x="320" y="62" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">wildcard -&gt; fresh T</text>

  <rect x="440" y="30" width="180" height="40" fill="#1c2430" stroke="#79c0ff"/>
  <text x="530" y="49" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">swapHelper(List&lt;T&gt;)</text>
  <text x="530" y="62" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">get(i): T, set(i, T): OK</text>

  <line x1="200" y1="50" x2="240" y2="50" stroke="#8b949e" marker-end="url(#a)"/>
  <line x1="400" y1="50" x2="440" y2="50" stroke="#8b949e" marker-end="url(#a)"/>

  <text x="320" y="120" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Once captured, T is a single, CONSISTENT (if still unknown) type for the</text>
  <text x="320" y="135" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">duration of this call -- letting get() and set() be checked against each other</text>
</svg>

*Capture converts an anonymous wildcard into a concrete-but-unnamed type variable, letting the compiler verify that operations against it are mutually consistent.*

## 5. Runnable example

Scenario: build a small generic list-manipulation utility that runs into, and then resolves, exactly the capture problem — starting with a basic direct attempt that fails to compile, then applying the standard capture-helper fix, then extending it to a bounded-wildcard case where capture must also respect the bound.

### Level 1 — Basic

```java
import java.util.*;

public class WildcardCaptureFailure {
    // This method deliberately shows the COMPILE ERROR you get without capture --
    // kept as a comment since it must not actually compile.
    /*
    static void swapDirect(List<?> list, int i, int j) {
        list.set(i, list.get(j)); // COMPILE ERROR: capture of ? -- cannot prove type safety
    }
    */

    public static void main(String[] args) {
        System.out.println("see the commented-out swapDirect method above --");
        System.out.println("attempting to compile it directly produces: incompatible types: capture#1 of ?");
    }
}
```

**How to run:** `java WildcardCaptureFailure.java` (JDK 17+; this compiles and runs fine as-is, since the problematic method is commented out — uncommenting it demonstrates the actual compile error).

Expected output:
```
see the commented-out swapDirect method above --
attempting to compile it directly produces: incompatible types: capture#1 of ?
```

This establishes the actual problem concretely: a direct `list.set(i, list.get(j))` against a `List<?>` parameter fails to compile, because the compiler cannot locally prove that the element type returned by `get` on this wildcard is safe to pass to `set` on that same wildcard, even though logically it obviously is.

### Level 2 — Intermediate

```java
import java.util.*;

public class WildcardCaptureFixed {
    static void swap(List<?> list, int i, int j) {
        swapHelper(list, i, j); // the wildcard's unknown type is CAPTURED here, into T
    }

    private static <T> void swapHelper(List<T> list, int i, int j) {
        T tmp = list.get(i);
        list.set(i, list.get(j));
        list.set(j, tmp);
    }

    public static void main(String[] args) {
        List<String> names = new ArrayList<>(List.of("Ada", "Grace", "Barbara"));
        swap(names, 0, 2);
        System.out.println(names);
    }
}
```

**How to run:** `java WildcardCaptureFixed.java` (JDK 17+).

Expected output:
```
[Barbara, Grace, Ada]
```

The real-world concern added: `swap` still accepts the flexible, caller-friendly `List<?>` (any list, regardless of its element type, can be passed in), while delegating to `swapHelper<T>` internally captures the wildcard's unknown type into a genuine, provably-consistent `T` for the duration of that call — letting `get(i)`, `get(j)`, and both `set` calls be verified against the same captured type, exactly resolving the compile error from Level 1 without sacrificing the outer method's flexible wildcard signature.

### Level 3 — Advanced

```java
import java.util.*;

public class WildcardCaptureBounded {
    static double sumAndDoubleFirst(List<? extends Number> list) {
        return sumAndDoubleFirstHelper(list);
    }

    // Capturing a BOUNDED wildcard: T is captured as "whatever specific subtype
    // of Number this list actually holds" -- the bound (Number) is preserved
    // through capture, so .doubleValue() remains callable on T.
    private static <T extends Number> double sumAndDoubleFirstHelper(List<T> list) {
        double sum = 0;
        for (T value : list) {
            sum += value.doubleValue();
        }
        return sum;
    }

    public static void main(String[] args) {
        List<Integer> ints = List.of(1, 2, 3);
        List<Double> doubles = List.of(1.5, 2.5);

        System.out.println("sum of ints: " + sumAndDoubleFirst(ints));
        System.out.println("sum of doubles: " + sumAndDoubleFirst(doubles));
    }
}
```

**How to run:** `java WildcardCaptureBounded.java` (JDK 17+).

Expected output:
```
sum of ints: 6.0
sum of doubles: 4.0
```

The production-flavored hard case: `List<? extends Number>` accepts *any* list of *any* specific `Number` subtype (`Integer`, `Double`, or any other), and capturing it into `T extends Number` preserves the bound through the capture — meaning `value.doubleValue()` remains a legal call inside the helper, since whatever `T` actually turns out to be for a given call, it's guaranteed to extend `Number` and therefore have a `doubleValue()` method; this demonstrates that capture isn't just about resolving an unnamed wildcard into some stand-in name, it specifically carries the wildcard's bound along with it, preserving exactly the operations that bound guarantees are safe.

## 6. Walkthrough

Tracing `WildcardCaptureBounded.main`'s call `sumAndDoubleFirst(ints)` end to end, where `ints` is a `List<Integer>`:

1. `sumAndDoubleFirst` is declared to accept `List<? extends Number>` — a caller can pass any list whose element type is `Number` or some subtype of it, without the caller needing to know or care what `sumAndDoubleFirst` does internally; here, `ints` (a `List<Integer>`) is a valid argument, since `Integer extends Number`.
2. Inside `sumAndDoubleFirst`, the call `sumAndDoubleFirstHelper(list)` is where capture actually occurs: the compiler looks at `list`'s declared type, `List<? extends Number>`, and — because `sumAndDoubleFirstHelper` is declared with its own genuine type parameter `<T extends Number>` — captures the wildcard's specific-but-unknown-from-here type into `T`, which for this particular call happens to really be `Integer` underneath (though the code inside the helper never needs to know that specifically; it only relies on `T extends Number`).
3. Inside `sumAndDoubleFirstHelper`, the enhanced-for loop `for (T value : list)` iterates each element, statically typed as `T` (captured, bound by `Number`) — this is why `value.doubleValue()` type-checks: the compiler knows, from the bound alone, that whatever concrete type `T` is, it has a `doubleValue()` method, since every subtype of `Number` is required to provide one.
4. Each element's `doubleValue()` is called and accumulated into `sum` — for `ints = [1, 2, 3]`, this means `1.doubleValue() + 2.doubleValue() + 3.doubleValue()` (via autoboxed `Integer.doubleValue()`), accumulating to `6.0`.
5. `sumAndDoubleFirstHelper` returns the accumulated `double`, which `sumAndDoubleFirst` returns unchanged up to `main`, which prints `sum of ints: 6.0` — and the entire process repeats independently for the second call, `sumAndDoubleFirst(doubles)`, where this time capture resolves `T` to `Double` instead, producing `4.0` from `1.5 + 2.5`.
6. Neither call site ever explicitly names the captured type — the compiler's capture mechanism resolves it silently and correctly for each call independently, which is exactly what makes the single `sumAndDoubleFirst(List<? extends Number>)` signature usable uniformly across genuinely different concrete list types, while still preserving full compile-time type safety inside the helper.

## 7. Gotchas & takeaways

> **Gotcha:** the "capture of ?" compiler error can be confusing to read on first encounter, since it references a synthetic, unnamed type (`capture#1 of ?`) that never appears anywhere in your source code — recognizing this specific error message as "you're trying to write to (or otherwise treat as consistent) a wildcard-typed structure without a capture helper" is the key to knowing the fix is a private generic helper method, not a deeper type-system misunderstanding.

- Wildcard capture is the compiler's mechanism for converting an anonymous `?` into a fresh, consistent (if still unnamed) type variable whenever a method call needs to reason about that wildcard's type being used the same way in multiple places.
- A direct attempt to both read and write a `List<?>` in a way that requires them to be the same type (like `list.set(i, list.get(j))`) fails to compile with a "capture of ?" error, because the compiler cannot locally prove consistency.
- The standard fix is the capture-helper pattern: an outer method keeps the flexible `List<?>` signature, delegating to a private, genuinely generic helper method whose type parameter captures the wildcard for that one call — exactly what `Collections.swap` does internally in the JDK.
- A bounded wildcard's bound (`? extends Number`) is preserved through capture, so operations the bound guarantees (like `doubleValue()`) remain legal to call on the captured type inside the helper.
- See [recursive type bounds (T extends Comparable\<T\>)](0948-recursive-type-bounds-t-extends-comparable-t.md) for a related bounded-type-parameter pattern, and [super type tokens (TypeReference pattern)](0950-super-type-tokens-typereference-pattern.md) for a different technique addressing a related but distinct generics limitation — recovering type information that erasure would otherwise discard entirely.
