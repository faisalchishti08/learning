---
card: java
gi: 952
slug: reifiable-vs-non-reifiable-types
title: Reifiable vs non-reifiable types
---

## 1. What it is

A type is **reifiable** if the JVM retains full information about it at runtime — the type is fully known, checkable, and available for operations like `instanceof` or array creation. Primitive types (`int`, `boolean`), non-generic classes and interfaces (`String`, `Runnable`), raw types (`List`, `Map`), and unbounded or otherwise-fully-erasable wildcard parameterizations (`List<?>`) are all reifiable. A type is **non-reifiable** if [type erasure](0359-type-erasure.md) has discarded information about it that would be needed to fully check or represent it at runtime — this covers most parameterized types with a specific, non-wildcard type argument: `List<String>`, `Map<String, Integer>`, and any type variable itself (`T`, `E`). The distinction matters because the compiler forbids or restricts a specific set of operations on non-reifiable types precisely *because* they'd require runtime type information that no longer exists: you cannot write `list instanceof List<String>` (only `list instanceof List<?>` or raw `List`), you cannot create an array of a non-reifiable type directly (`new List<String>[10]` is a compile error), and varargs methods with a non-reifiable element type generate an "unchecked generic array creation" warning, tying directly back to [heap pollution](0951-heap-pollution.md).

## 2. Why & when

Understanding this distinction explains a whole category of otherwise-mysterious compiler restrictions that beginners often encounter as confusing, seemingly-arbitrary errors: "why can't I check `instanceof List<String>`," "why can't I make a generic array," "why does my varargs generic method warn about unchecked array creation." The answer, in every case, is the same: the specific type argument (`String`, in `List<String>`) simply doesn't exist anywhere in the compiled bytecode or at runtime — only the raw `List` does — so any operation that would need to consult that type argument at runtime is either forbidden outright or degraded to checking only the reifiable portion of the type (raw `List`, or `List<?>`, both of which the JVM can actually verify). Recognizing "is this type reifiable?" as the underlying question resolves what would otherwise look like a scattered, unrelated set of generics quirks into one single, coherent rule: only reifiable types can be checked, created as arrays, or otherwise inspected at runtime; everything about a non-reifiable type's specific type argument is a compile-time-only fiction that the compiler enforces through static checking and then discards.

## 3. Core concept

```
REIFIABLE (fully known at runtime):          NON-REIFIABLE (erasure has discarded info):
  int, boolean, double, ...                    List<String>, Map<String,Integer>
  String, Runnable, MyClass (non-generic)      T, E (type variables themselves)
  List, Map (raw types)                        any parameterized type EXCEPT unbounded
  List<?>, Map<?,?> (unbounded wildcards)         wildcards (List<?> IS reifiable --
                                                    "list of something, don't care what"
                                                    needs no specific type info at runtime)

Operations restricted to REIFIABLE types only:
  obj instanceof List<String>     // COMPILE ERROR -- List<String> is non-reifiable
  obj instanceof List<?>          // OK -- List<?> IS reifiable
  new List<String>[10]            // COMPILE ERROR -- can't create array of non-reifiable type
  new List<?>[10]                 // OK (though still often awkward in practice)
```

The single unifying rule: any check or array-creation operation that would need to consult a *specific, erased* type argument at runtime is disallowed — only operations that need nothing more than the reifiable portion (the raw type, or "unknown, don't care" for wildcards) are permitted.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A Venn-style comparison: reifiable types fully retained at runtime versus non-reifiable types whose specific type argument is erased and unavailable" >
  <rect x="20" y="30" width="280" height="110" fill="#1c2430" stroke="#6db33f"/>
  <text x="160" y="50" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">REIFIABLE</text>
  <text x="160" y="70" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">int, String, MyClass</text>
  <text x="160" y="85" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">List, Map (raw)</text>
  <text x="160" y="100" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">List&lt;?&gt;  (unbounded wildcard)</text>
  <text x="160" y="120" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">instanceof OK, array creation OK</text>

  <rect x="340" y="30" width="280" height="110" fill="#1c2430" stroke="#f0883e"/>
  <text x="480" y="50" fill="#f0883e" font-size="10" text-anchor="middle" font-family="sans-serif">NON-REIFIABLE</text>
  <text x="480" y="70" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">List&lt;String&gt;, Map&lt;K,V&gt;</text>
  <text x="480" y="85" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">T, E (type variables)</text>
  <text x="480" y="120" fill="#f0883e" font-size="8" text-anchor="middle" font-family="sans-serif">instanceof: COMPILE ERROR</text>
  <text x="480" y="132" fill="#f0883e" font-size="8" text-anchor="middle" font-family="sans-serif">array creation: COMPILE ERROR</text>
</svg>

*Only reifiable types are fully known at runtime — the compiler forbids instanceof checks and direct array creation for everything else.*

## 5. Runnable example

Scenario: explore the practical boundary between reifiable and non-reifiable types by attempting, then correctly working around, each restricted operation — starting with the basic `instanceof` restriction and its fix, then array-creation restrictions and the standard workaround, then a realistic generic utility that must navigate both restrictions correctly.

### Level 1 — Basic

```java
import java.util.*;

public class ReifiableInstanceofDemo {
    public static void main(String[] args) {
        List<String> strings = List.of("a", "b");
        Object obj = strings;

        // if (obj instanceof List<String>) { }  // COMPILE ERROR -- List<String> is non-reifiable

        if (obj instanceof List<?> list) {         // OK -- List<?> IS reifiable
            System.out.println("it's some kind of List, size=" + list.size());
        }
        if (obj instanceof List rawList) {          // also OK -- raw List is reifiable (with a warning)
            System.out.println("raw check also works, size=" + rawList.size());
        }
    }
}
```

**How to run:** `java ReifiableInstanceofDemo.java` (JDK 17+).

Expected output:
```
it's some kind of List, size=2
raw check also works, size=2
```

`instanceof List<String>` would require the JVM to check, at runtime, that the object is not just a `List` but specifically a `List` whose elements are `String` — information erasure has already discarded; `instanceof List<?>` sidesteps this entirely by only asking "is this some kind of List at all," which is exactly the reifiable, erasure-surviving information the JVM still has.

### Level 2 — Intermediate

```java
import java.util.*;

public class ReifiableArrayCreationDemo {
    @SuppressWarnings("unchecked")
    public static void main(String[] args) {
        // List<String>[] arr = new List<String>[10];  // COMPILE ERROR -- non-reifiable array creation

        List<String>[] arr = (List<String>[]) new List[10]; // standard workaround: create a RAW array,
                                                              // then unchecked-cast it to the generic array type
        arr[0] = List.of("Ada", "Grace");
        arr[1] = List.of("Barbara");

        for (List<String> list : arr) {
            if (list != null) System.out.println(list);
        }
    }
}
```

**How to run:** `java ReifiableArrayCreationDemo.java` (JDK 17+).

Expected output:
```
[Ada, Grace]
[Barbara]
```

The real-world concern added: `new List<String>[10]` is forbidden outright, since arrays need a genuinely reifiable component type to enforce their runtime store-type checks (see [generics & arrays interplay](0953-generics-arrays-interplay.md)) — the standard, JDK-idiomatic workaround is creating a *raw* array (`new List[10]`, which is reifiable) and then performing an explicit unchecked cast to the desired generic array type, accepting the compiler's unchecked warning as the deliberate, manually-verified tradeoff this pattern always requires.

### Level 3 — Advanced

```java
import java.util.*;

public class ReifiableGenericUtility {
    @SuppressWarnings("unchecked")
    static <T> T[] filterByType(Object[] items, Class<T> type) {
        // Class<T> IS reifiable (a Class object always carries full runtime type info) --
        // this is exactly why methods needing runtime type checks accept a Class<T> parameter,
        // sidestepping the non-reifiability of T itself.
        List<T> matched = new ArrayList<>();
        for (Object item : items) {
            if (type.isInstance(item)) {
                matched.add(type.cast(item));
            }
        }
        return matched.toArray((T[]) java.lang.reflect.Array.newInstance(type, matched.size()));
    }

    public static void main(String[] args) {
        Object[] mixed = { "Ada", 42, "Grace", 3.14, "Barbara" };
        String[] names = filterByType(mixed, String.class);
        System.out.println(Arrays.toString(names));
    }
}
```

**How to run:** `java ReifiableGenericUtility.java` (JDK 17+).

Expected output:
```
[Ada, Grace, Barbara]
```

The production-flavored hard case: `T` itself is non-reifiable, so `filterByType` cannot check `item instanceof T` or create a genuine `T[]` array directly — the idiomatic fix is accepting an explicit `Class<T>` parameter (a `Class` object is always fully reifiable, carrying complete runtime type information regardless of any erased generic context) and using its reflective `isInstance`/`cast` methods for the type check, plus `java.lang.reflect.Array.newInstance` to create a properly-typed array at runtime — this "pass the Class token alongside T" pattern is the standard, idiomatic way real generic utility code works around non-reifiability whenever runtime type information is genuinely needed.

## 6. Walkthrough

Tracing `ReifiableGenericUtility.filterByType(mixed, String.class)` end to end:

1. `type` is bound to `String.class` — a `Class<String>` object, which, unlike the generic type parameter `T` it corresponds to, is a genuinely reifiable, ordinary runtime object carrying complete type information (this is the crucial trick: passing the "missing" runtime type information explicitly, as data, rather than trying to recover it from `T` itself, which erasure has already discarded).
2. The method iterates every element of `mixed` (`"Ada"`, `42`, `"Grace"`, `3.14`, `"Barbara"`), calling `type.isInstance(item)` for each — since `type` is a genuine `Class` object, `isInstance` performs a real, fully-informed runtime type check, correctly identifying `"Ada"`, `"Grace"`, and `"Barbara"` as `String` instances, and `42` (an `Integer`) and `3.14` (a `Double`) as not.
3. Each matching element is added to `matched` (an ordinary `ArrayList<T>`, using `type.cast(item)` to perform a checked, safe cast rather than an unchecked one) — after the loop, `matched` contains exactly `["Ada", "Grace", "Barbara"]`.
4. To return a properly-typed `T[]` array (specifically `String[]`, not just `Object[]`), the method uses `java.lang.reflect.Array.newInstance(type, matched.size())` — this reflective call creates a genuine array whose runtime component type is whatever `type` actually is (here, `String`), sidestepping the "cannot create array of non-reifiable type" restriction entirely, since this array's component type is determined dynamically, at runtime, from the reifiable `Class` object, not from the non-reifiable `T` directly.
5. `matched.toArray(...)` fills that correctly-typed array with the matched elements and returns it — the unchecked cast `(T[])` on this call is safe in practice specifically because the array was constructed with the correct runtime component type via reflection, even though the compiler cannot itself verify this and still emits the unchecked warning suppressed at the method level.
6. Back in `main`, `names` is genuinely a `String[]` at runtime (not just statically typed as one) — `Arrays.toString(names)` prints `[Ada, Grace, Barbara]`, confirming the returned array is both correctly filtered and correctly, concretely typed, demonstrating the complete "pass a `Class<T>` token to work around `T`'s non-reifiability" pattern end to end.

## 7. Gotchas & takeaways

> **Gotcha:** an unbounded wildcard type like `List<?>` is reifiable, but a *bounded* wildcard like `List<? extends Number>` is not — the distinction is subtle: "some type, I genuinely don't care what" needs no runtime information and is therefore checkable, while "some type, but it must extend Number" is itself a constraint erasure discards along with everything else about the specific type argument; `instanceof List<? extends Number>` is just as much a compile error as `instanceof List<String>`.

- A type is reifiable if the JVM retains full runtime information about it (primitives, non-generic classes, raw types, and unbounded wildcards); it's non-reifiable if [type erasure](0359-type-erasure.md) has discarded information needed to fully represent or check it (most parameterized types with a specific or bounded type argument, and type variables themselves).
- `instanceof` and direct array creation are restricted to reifiable types, because both operations would otherwise need to consult runtime type information erasure has already discarded.
- The standard workaround for array creation is creating a raw array and performing an explicit, deliberate unchecked cast; the standard workaround for needing runtime type checks on a generic type parameter is accepting an explicit `Class<T>` token parameter alongside it, since `Class` objects are always fully reifiable.
- Recognizing "is this type reifiable?" resolves several seemingly-unrelated generics restrictions (no generic `instanceof`, no generic array creation, unchecked varargs warnings) into one single, coherent underlying rule.
- Unbounded wildcards (`List<?>`) are reifiable; bounded wildcards (`List<? extends Number>`) are not, despite both looking superficially similar.
- See [type erasure](0359-type-erasure.md) for the mechanism that creates the reifiable/non-reifiable distinction in the first place, and [generics & arrays interplay](0953-generics-arrays-interplay.md) for a deeper look at why array creation specifically is so constrained by reifiability.
