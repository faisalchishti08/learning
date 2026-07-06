---
card: java
gi: 355
slug: wildcard
title: Wildcard ?
---

## 1. What it is

The wildcard `?` represents an unknown type at a *usage* site — `List<?>` means "a list of some specific type, we just don't know (or care) which one" — as distinct from a type parameter like `T`, which is a *named* stand-in declared at a class or method. A wildcard is useful precisely because generics are invariant: `List<String>` is not a subtype of `List<Object>`, even though `String` is a subtype of `Object`, so a method wanting to accept "a list of anything" can't simply use `List<Object>` — it needs `List<?>` instead.

```java
import java.util.List;

public class WildcardDemo {
    static void printAll(List<?> list) { // accepts a List of ANY type
        for (Object item : list) {
            System.out.println(item);
        }
    }

    public static void main(String[] args) {
        printAll(List.of("a", "b", "c"));
        printAll(List.of(1, 2, 3));
    }
}
```

`printAll(List<?> list)` accepts `List<String>`, `List<Integer>`, or a list of any other type — something `printAll(List<Object> list)` could not do, since `List<String>` is simply not assignable to a parameter typed `List<Object>`.

## 2. Why & when

Generics are invariant by design, for good reason: if `List<String>` were treated as a subtype of `List<Object>`, you could add an `Integer` to it through the `List<Object>` reference, silently corrupting a list that's actually supposed to contain only `String`s. Wildcards give you a type-safe way to write methods that work across many different specific type arguments, without opening that hole.

- **Accepting a collection of any type when the method only reads from it** — a method that just iterates and prints, counts, or inspects elements generically doesn't need to know the exact type, only that it's *some* list.
- **Writing flexible APIs that work across related generic types** — a method parameter typed `List<?>` accepts `List<String>`, `List<Integer>`, and everything else, whereas a specific type parameter would only accept one.
- **Signaling "I don't care what this is" as opposed to "this is a specific but flexible type"** — using `?` instead of a declared type parameter like `<T>` communicates that the method genuinely has no need to refer to the element type anywhere in its signature or body.

Because `List<?>` means "a list of some *specific but unknown* type," you cannot add anything to it (except `null`) — the compiler has no way to verify that whatever you're adding matches the list's actual, hidden element type, so it conservatively forbids any addition beyond `null`, which is safe regardless of the unknown type.

## 3. Core concept

```java
import java.util.List;
import java.util.ArrayList;

public class WildcardCore {
    static int countElements(List<?> list) { // read-only access -- fine with a wildcard
        return list.size();
    }

    static void tryToAdd(List<?> list) {
        // list.add("hello"); // would NOT compile -- compiler can't verify the actual element type
        list.add(null); // the ONE thing always safe to add to a List<?>, regardless of its real type
    }

    public static void main(String[] args) {
        List<String> strings = new ArrayList<>(List.of("a", "b"));
        System.out.println("Count: " + countElements(strings));
        tryToAdd(strings);
        System.out.println("After tryToAdd: " + strings);
    }
}
```

**How to run:** `java WildcardCore.java`

`countElements` only reads (`list.size()`), which is always safe regardless of the actual element type; `tryToAdd` demonstrates that `list.add(null)` is the sole exception to "you can't add to a `List<?>`," since `null` is a valid value for *any* reference type.

## 4. Diagram

<svg viewBox="0 0 600 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="a wildcard parameter accepts a List of any specific type, unlike a fixed-type parameter which only accepts that one exact type">
  <rect x="8" y="8" width="584" height="134" rx="8" fill="#0d1117"/>
  <rect x="20" y="30" width="220" height="35" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="130" y="52" fill="#79c0ff" font-size="10" text-anchor="middle">printAll(List&lt;?&gt; list)</text>

  <text x="270" y="50" fill="#8b949e" font-size="10">accepts:</text>
  <rect x="330" y="15" width="120" height="25" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="390" y="32" fill="#6db33f" font-size="9" text-anchor="middle">List&lt;String&gt;</text>
  <rect x="330" y="45" width="120" height="25" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="390" y="62" fill="#6db33f" font-size="9" text-anchor="middle">List&lt;Integer&gt;</text>
  <rect x="330" y="75" width="120" height="25" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="390" y="92" fill="#6db33f" font-size="9" text-anchor="middle">List&lt;anything&gt;</text>
</svg>

## 5. Runnable example

Scenario: a small utility for describing collections, evolved from methods hardcoded to one specific type, into a wildcard-based version working across any collection type, into a production-style utility demonstrating exactly what a wildcard permits and forbids.

### Level 1 — Basic

```java
import java.util.List;

public class DescribeBasic {
    static String describe(List<String> list) { // works ONLY for List<String>
        return "List of " + list.size() + " string(s): " + list;
    }

    public static void main(String[] args) {
        System.out.println(describe(List.of("a", "b", "c")));
        // System.out.println(describe(List.of(1, 2, 3))); // would NOT compile -- wrong element type
    }
}
```

**How to run:** `java DescribeBasic.java`

This method genuinely only cares about the list's size and contents for printing, but its signature unnecessarily restricts it to `List<String>` specifically — a `List<Integer>` describing the exact same operation would need a completely separate, duplicated method.

### Level 2 — Intermediate

```java
import java.util.List;

public class DescribeIntermediate {
    static String describe(List<?> list) { // wildcard -- works for ANY list type
        return "List of " + list.size() + " element(s): " + list;
    }

    public static void main(String[] args) {
        System.out.println(describe(List.of("a", "b", "c")));
        System.out.println(describe(List.of(1, 2, 3)));
        System.out.println(describe(List.of()));
    }
}
```

**How to run:** `java DescribeIntermediate.java`

Switching the parameter to `List<?>` lets the single `describe` method work identically across `List<String>`, `List<Integer>`, and an empty list — the method body never needed to know the specific element type in the first place, since it only calls `size()` and relies on the list's own `toString()`.

### Level 3 — Advanced

```java
import java.util.List;
import java.util.ArrayList;

public class DescribeAdvanced {
    static String describe(List<?> list) {
        if (list.isEmpty()) return "Empty list.";
        Object first = list.get(0); // reading is always fine -- returns as Object
        return "List of " + list.size() + " element(s), first is a "
                + first.getClass().getSimpleName() + ": " + list;
    }

    static void clearAndNullify(List<?> list) {
        list.clear();       // removing everything is always safe, regardless of element type
        // list.add("x");   // still would NOT compile -- can't add a specific value
        list.add(null);     // still the one safe addition
    }

    public static void main(String[] args) {
        System.out.println(describe(List.of("a", "b", "c")));
        System.out.println(describe(List.of(1, 2, 3)));
        System.out.println(describe(List.of()));

        List<String> mutable = new ArrayList<>(List.of("x", "y"));
        clearAndNullify(mutable);
        System.out.println("After clearAndNullify: " + mutable);
    }
}
```

**How to run:** `java DescribeAdvanced.java`

`describe` now also reads an individual element (`list.get(0)`, always returned as `Object`, since the real type is unknown) to report its runtime class, and `clearAndNullify` demonstrates that removal operations (`clear()`) are always safe on a `List<?>` — only *adding* a specific non-null value is restricted, since the compiler can't verify it matches the list's hidden actual element type.

## 6. Walkthrough

Execution starts in `main`, which calls `describe(List.of("a", "b", "c"))` first.

Inside `describe`, `list.isEmpty()` is `false`, so the early-return is skipped. `list.get(0)` returns the first element as `Object` (since the compiler only knows this is "some list of an unknown type") — the actual runtime object is a `String`, `"a"`. `first.getClass().getSimpleName()` reports `"String"`. The method returns `"List of 3 element(s), first is a String: [a, b, c]"`, which is printed.

`main` then calls `describe(List.of(1, 2, 3))`. The same logic runs: `list.get(0)` returns `Integer` `1` (boxed) as `Object`; `getClass().getSimpleName()` reports `"Integer"`. The result: `"List of 3 element(s), first is a Integer: [1, 2, 3]"`.

`main` calls `describe(List.of())` next: `list.isEmpty()` is `true` this time, so the method returns immediately with `"Empty list."`, never reaching `list.get(0)` — calling `get(0)` on an empty list would have thrown `IndexOutOfBoundsException`, which this early check avoids.

Finally, `main` creates a genuinely mutable `List<String> mutable = new ArrayList<>(List.of("x", "y"))` and calls `clearAndNullify(mutable)`. Inside, `list.clear()` removes both elements — this is permitted because removing elements never requires the compiler to verify a *new* value's type against the list's hidden element type. `list.add(null)` then adds a single `null` — this is the one addition permitted on a `List<?>`, since `null` is trivially compatible with any reference type. Back in `main`, `mutable` (now `[null]`) is printed as `After clearAndNullify: [null]`.

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="describe reads elements safely regardless of type via Object, with an empty-list guard before any indexed access; clearAndNullify shows that removal and null-insertion are safe on a wildcard list but adding a real value is not">
  <rect x="8" y="8" width="624" height="154" rx="8" fill="#0d1117"/>
  <text x="20" y="30" fill="#79c0ff" font-size="10">describe(["a","b","c"]): not empty -&gt; get(0) as Object -&gt; "String" -&gt; full description printed</text>
  <text x="20" y="55" fill="#79c0ff" font-size="10">describe([1,2,3]): not empty -&gt; get(0) as Object -&gt; "Integer" -&gt; full description printed</text>
  <text x="20" y="80" fill="#f85149" font-size="10">describe([]): isEmpty() true -&gt; returns early, get(0) never called (would have thrown otherwise)</text>
  <text x="20" y="110" fill="#6db33f" font-size="10">clearAndNullify(["x","y"]): clear() removes all (always safe) -&gt; add(null) (the one safe addition)</text>
  <text x="20" y="132" fill="#8b949e" font-size="10">  result: mutable list now contains [null] -- adding any non-null value would not compile</text>
</svg>

## 7. Gotchas & takeaways

> `List<?>` is not the same as `List<Object>` — the former means "a list of some specific but unknown type" (and forbids adding anything but `null`), while the latter genuinely is a list whose element type *is* `Object`, and freely accepts adding any object at all; confusing the two is a common source of "why won't this compile" confusion.

- A wildcard (`?`) represents an unknown type at a usage site; a type parameter (`T`) is a named stand-in declared at a class or method — they solve related but different problems.
- Reading from a `List<?>` (iterating, `get`, `size`) is always safe and returns elements typed as `Object`, since the compiler doesn't know (and doesn't need to know) the real element type for read-only access.
- Writing to a `List<?>` is restricted to `null` — adding any other specific value is rejected at compile time, since the compiler can't verify it matches the list's actual, hidden element type.
- Removal operations (`clear()`, `remove(index)`) are always safe on a `List<?>`, since they don't require introducing any new value whose type would need to be checked.
- Prefer `List<?>` over a raw `List` (no type parameter at all) whenever a method needs to accept "a list of any type" — the wildcard version keeps full compile-time type safety, while a raw type discards it entirely.
