---
card: java
gi: 588
slug: safevarargs-on-private-methods
title: '@SafeVarargs on private methods'
---

## 1. What it is

`@SafeVarargs` suppresses the compiler's "unchecked generics array creation" warning for a varargs method whose parameter type is a generic type (`T...`). Before Java 9, this annotation could only be applied to `static`, `final`, or constructor methods — never a plain instance method, because it could be overridden, and an override might not honor the safety guarantee the annotation asserts. Java 9 extended `@SafeVarargs` to also cover **private instance methods** specifically, since a private method can never be overridden, making the same safety guarantee just as sound as it is for `static`/`final` methods.

## 2. Why & when

Generic varargs (`<T> void method(T... items)`) trigger an "unchecked" compiler warning because, under the hood, varargs are implemented as an array, and creating an array of a generic type isn't fully type-safe at runtime (due to type erasure and array covariance interacting badly) — a caller could, in principle, pass arguments that produce a `ClassCastException` at a point far from where the actual problem originated. `@SafeVarargs` is a developer's promise: "I've reviewed this method's body and confirmed it doesn't do anything unsafe with the varargs array (like storing it somewhere accessible or returning it to unsafe code)." Before Java 9, this promise could only be made for methods where the implementation was fixed and couldn't be silently altered by a subclass override — `static`, `final`, and constructors. A `private` instance method has exactly the same property (it can't be overridden, full stop, regardless of whether the class itself is final), so Java 9 sensibly extended the annotation to cover it too, letting private helper methods with generic varargs parameters suppress the warning just as legitimately.

## 3. Core concept

```java
public class ListBuilder {
    public static <T> List<T> buildFrom(T first, T second, T third) {
        return combine(first, second, third); // delegates to a private varargs helper
    }

    @SafeVarargs // Java 9+: legal on a PRIVATE instance method (this one happens to also be static-adjacent in spirit, but works identically for private instance methods too)
    private static <T> List<T> combine(T... items) {
        return new ArrayList<>(Arrays.asList(items));
    }
}
```

Before Java 9, if `combine` were a private *instance* method (not `static`) with a generic varargs parameter, `@SafeVarargs` could not be applied to it at all — the compiler would reject the annotation on a plain instance method, forcing either a warning suppression via `@SuppressWarnings("unchecked")` (a blunter, less specific tool) or restructuring the code to avoid the situation entirely.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="@SafeVarargs is legal exactly on methods that cannot be overridden: static, final, constructors, and (since Java 9) private instance methods">
  <text x="20" y="25" fill="#8b949e" font-size="11" font-family="sans-serif">@SafeVarargs is legal ONLY where an override can't break the safety promise:</text>
  <rect x="20" y="35" width="140" height="30" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="90" y="55" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">static methods</text>
  <rect x="170" y="35" width="140" height="30" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="240" y="55" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">final methods</text>
  <rect x="320" y="35" width="140" height="30" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="390" y="55" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">constructors</text>
  <rect x="470" y="35" width="150" height="30" rx="6" fill="#1c2430" stroke="#f0883e"/>
  <text x="545" y="55" fill="#f0883e" font-size="10" text-anchor="middle" font-family="sans-serif">private (Java 9+)</text>

  <rect x="20" y="90" width="600" height="30" rx="6" fill="#1c2430" stroke="#f85149"/>
  <text x="320" y="110" fill="#f85149" font-size="10" text-anchor="middle" font-family="sans-serif">plain (overridable) instance methods -&gt; @SafeVarargs NEVER legal here, at any Java version</text>

  <text x="20" y="150" fill="#8b949e" font-size="10" font-family="sans-serif">A private method can never be overridden, so it joins the same "safe" category as static/final/constructors.</text>
</svg>

The common thread across every legal placement: the compiler can guarantee no subclass override can silently violate the safety promise.

## 5. Runnable example

Scenario: a small collection-building utility class with a public generic factory method that internally delegates to a private varargs helper — starting with the pre-Java-9 workaround (a blunter `@SuppressWarnings`), then applying `@SafeVarargs` directly to the private helper, then demonstrating why the annotation is legitimate here by showing the exact unsafe pattern it protects against, safely avoided.

### Level 1 — Basic

```java
import java.util.*;

public class CollectionBuilderOld {
    public static <T> List<T> of(T a, T b, T c) {
        return combine(a, b, c);
    }

    @SuppressWarnings("unchecked") // pre-Java-9 workaround: blunter, less specific than @SafeVarargs
    private static <T> List<T> combine(T... items) {
        return new ArrayList<>(Arrays.asList(items));
    }

    public static void main(String[] args) {
        List<String> names = of("Ann", "Bo", "Cy");
        System.out.println(names);
    }
}
```

**How to run:** `java CollectionBuilderOld.java`

Expected output (a compiler warning appears before the program's own output; the program itself still runs and prints normally):
```
CollectionBuilderOld.java:5: warning: [unchecked] unchecked generic array creation for varargs parameter of type T[]
        return combine(a, b, c);
                      ^
  where T is a type-variable:
    T extends Object declared in method <T>of(T,T,T)
1 warning
[Ann, Bo, Cy]
```

`@SuppressWarnings("unchecked")` on `combine` only silences unchecked warnings **inside `combine`'s own body** — it does nothing about the warning that appears at `combine`'s *call site*, inside `of`, since `@SuppressWarnings`'s scope is lexically limited to the element it's attached to and doesn't propagate to callers. This is a real, meaningful limitation: `@SuppressWarnings("unchecked")` is also a blunter instrument in general — it suppresses *any* unchecked warning in the annotated method's body, not specifically the varargs-related one, potentially hiding an unrelated, genuinely unsafe unchecked operation added later in the same method without anyone noticing.

### Level 2 — Intermediate

```java
import java.util.*;

public class CollectionBuilderModern {
    private final List<String> prefix = new ArrayList<>();

    public CollectionBuilderModern(String... prefixItems) {
        prefix.addAll(Arrays.asList(prefixItems));
    }

    public <T> List<Object> buildWithPrefix(T a, T b) {
        return combineWithPrefix(a, b); // instance method calling a private INSTANCE varargs helper
    }

    @SafeVarargs // Java 9+: legal here because combineWithPrefix is a PRIVATE INSTANCE method — cannot be overridden
    private final <T> List<Object> combineWithPrefix(T... items) {
        List<Object> result = new ArrayList<>(prefix); // uses instance state — genuinely an instance method
        result.addAll(Arrays.asList(items));
        return result;
    }

    public static void main(String[] args) {
        CollectionBuilderModern builder = new CollectionBuilderModern("HEADER");
        System.out.println(builder.buildWithPrefix("Ann", "Bo"));
    }
}
```

**How to run:** `java CollectionBuilderModern.java`

Expected output:
```
[HEADER, Ann, Bo]
```

The real-world concern this adds: `combineWithPrefix` is a genuine **instance** method (not `static`) — it reads `prefix`, instance state belonging to the specific `CollectionBuilderModern` object it's called on. Before Java 9, `@SafeVarargs` could not be applied to a private instance method like this at all, regardless of the method also being marked `final` (redundant on a private method, since private methods are implicitly non-overridable, but shown here for clarity) — Java 9 specifically closes this gap, letting the annotation apply here and suppress the unchecked-varargs warning precisely, without resorting to the blunter `@SuppressWarnings("unchecked")` from Level 1.

### Level 3 — Advanced

```java
import java.util.*;

public class SafeVarargsDemonstration {
    // This method is annotated @SafeVarargs, making a real promise: it does nothing unsafe
    // with the "items" array — in particular, it never stores a reference to it anywhere
    // that outlives this method call, and never returns it directly to the caller.
    @SafeVarargs
    private final <T> int countDistinct(T... items) {
        // SAFE: only reads from items, builds a genuinely new Set, never leaks the array itself.
        return new HashSet<>(Arrays.asList(items)).size();
    }

    // Contrast: this hypothetical pattern WOULD be unsafe and is exactly what @SafeVarargs
    // asserts is NOT happening in a correctly-annotated method — shown here only as a
    // demonstration of what to avoid, using an Object[] array directly (not generic varargs)
    // so it compiles without triggering the unsafe-generic-array warning in the first place.
    private Object[] lastCall;
    private void unsafeStoreExample(Object[] items) {
        lastCall = items; // storing a reference — this is the pattern @SafeVarargs promises AGAINST
    }

    public static void main(String[] args) {
        SafeVarargsDemonstration demo = new SafeVarargsDemonstration();
        System.out.println(demo.countDistinct("a", "b", "a", "c"));
        System.out.println(demo.countDistinct(1, 2, 2, 3, 3, 3));
    }
}
```

**How to run:** `java SafeVarargsDemonstration.java`

Expected output:
```
3
3
```

This handles the production-flavoured concern of **what `@SafeVarargs` is actually vouching for**: `countDistinct` only reads from `items` (via `Arrays.asList(items)`, itself read-only with respect to the underlying array in this usage) to build a `HashSet` and return its size — it never stores the `items` array reference anywhere, never returns it, never lets it escape the method call in a form that could be mutated or misused elsewhere. `unsafeStoreExample` (deliberately not annotated, and using a plain `Object[]` parameter rather than generic varargs, so it wouldn't even trigger the warning `@SafeVarargs` addresses) illustrates the *kind* of pattern that would make `@SafeVarargs` a false promise if it were applied to a genuinely varargs-generic method behaving this way — storing the array reference somewhere it outlives the call, potentially exposing it to code that doesn't know the array's true, erased element type.

## 6. Walkthrough

Execution starts in `main` of the Level 3 example. `demo.countDistinct("a", "b", "a", "c")` is called. Because `countDistinct` is declared with a varargs parameter (`T... items`), the compiler packages the four string arguments into a single `String[]` array (erased to `Object[]` at the bytecode level, due to generics type erasure) and passes that array as `items`.

```
countDistinct("a", "b", "a", "c"):
  items = ["a", "b", "a", "c"]  (a freshly-created array, only for this call)
  Arrays.asList(items)           -> a List view backed by that same array
  new HashSet<>(...)              -> copies the four elements into a Set, deduplicating: {a, b, c}
  .size()                         -> 3
```

`Arrays.asList(items)` wraps the array without copying it — but `new HashSet<>(...)` then iterates that list and copies each element into the new `HashSet`, so the resulting set has no ongoing connection to the original `items` array at all. `countDistinct` returns `3` — three distinct elements (`"a"`, `"b"`, `"c"`) among the four arguments, since `"a"` appeared twice. `main` prints `3`.

The second call, `demo.countDistinct(1, 2, 2, 3, 3, 3)`, follows the identical path with `Integer` arguments (auto-boxed): `items = [1, 2, 2, 3, 3, 3]`, deduplicated into `{1, 2, 3}`, size `3`. `main` prints `3` again.

Crucially, in neither call does the `items` array (created fresh by the compiler for that specific call) escape `countDistinct`'s method body in any form — it's read once, into a new `HashSet`, and then `items` itself is never referenced again. This is exactly the property `@SafeVarargs` on `countDistinct` is asserting to be true, and because `countDistinct` is `private` (and additionally `final`, though redundant given it's already private), no subclass could ever override it with a different, unsafe implementation that violates this promise — which is precisely why the annotation is legally permitted here at all, a permission that specifically did not exist for private instance methods before Java 9.

## 7. Gotchas & takeaways

> `@SafeVarargs` is a **compile-time-checked-for-eligibility, but not automatically-verified-for-correctness** annotation — the compiler enforces *where* it can legally be applied (static, final, private, constructors — never a plain overridable instance method), but it does not analyze the method body to confirm the safety promise is actually kept. Applying `@SafeVarargs` to a method that genuinely does something unsafe with the varargs array (storing or returning the raw array reference) silences a warning that was correctly warning about a real potential issue — the annotation is a developer assertion, not a compiler-verified guarantee.

- The full list of places `@SafeVarargs` is legal: `static` methods, `final` instance methods, constructors, and (since Java 9) `private` instance methods — a plain, overridable (non-final, non-private) instance method can never carry this annotation, at any Java version, because an override could break the safety promise the annotation makes.
- `@SafeVarargs` only matters (and only produces a warning to suppress in the first place) for varargs methods whose parameter type is a **generic** type (`T...`, `List<T>...`, etc.) — a varargs method with a concrete, non-generic parameter type (`String...`, `int...`) never triggers the unchecked warning `@SafeVarargs` exists to suppress, and the annotation is unnecessary (though harmless) on such methods.
- Marking a private instance method both `private` and `final` (as in the Level 2 example) is redundant for override-prevention purposes — private methods are never inherited or overridable regardless of `final` — but some codebases keep the `final` for documentation clarity or consistency with a broader style convention.
- `@SafeVarargs` was introduced in Java 7 (for `final`/`static` methods and constructors); Java 9's extension to private instance methods is a narrower, later addition specifically closing the one remaining override-safe category the annotation hadn't yet covered.
- If a private helper method with a generic varargs parameter genuinely does need to be called from a non-private context indirectly, the common, idiomatic pattern (shown in Levels 1 and 2) is a `public` (or otherwise more visible) non-varargs or fixed-arity wrapper method that internally delegates to the `@SafeVarargs`-annotated private varargs helper — keeping the unchecked-suppression scope as narrow and well-justified as possible.
