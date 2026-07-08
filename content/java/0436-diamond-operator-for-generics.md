---
card: java
gi: 436
slug: diamond-operator-for-generics
title: Diamond operator <> for generics
---

## 1. What it is

The diamond operator, added in Java 7, lets you write `<>` (empty angle brackets) on the right-hand side of a generic object creation, instead of repeating the full type argument. `List<String> names = new ArrayList<>();` — the compiler infers that the `ArrayList` being created should be `ArrayList<String>`, by looking at the declared type on the left (`List<String>`), so you don't have to write `new ArrayList<String>()` in full.

## 2. Why & when

Before Java 7, generic type arguments had to be repeated on both sides of an assignment: `List<String> names = new ArrayList<String>();` — the `<String>` appears twice, purely because Java's generics don't (pre-diamond) infer the constructor's type argument from context. For simple cases this is just mildly annoying, but for deeply nested generic types — `Map<String, List<Integer>> data = new HashMap<String, List<Integer>>();` — the redundancy becomes genuinely hard to read and easy to get subtly wrong (a typo in one copy but not the other).

The diamond operator removes this redundancy entirely: the compiler already knows the target type from the left-hand side (or a method parameter type, or a return type), so there's no ambiguity in inferring what `<>` should mean. You use it any time you're constructing a generic object where the type argument is already determinable from context — which, in practice, is nearly always.

## 3. Core concept

```java
import java.util.*;

// Before Java 7 (still valid, just verbose):
List<String> names = new ArrayList<String>();

// With the diamond operator (Java 7+):
List<String> namesShort = new ArrayList<>(); // <String> is inferred from the declared type on the left

// The benefit compounds with nested generics:
Map<String, List<Integer>> scores = new HashMap<>(); // vs. new HashMap<String, List<Integer>>()
```

The diamond isn't "no type argument" — it's "infer the type argument from context." The compiler still performs full generic type checking; it just doesn't require you to spell out what it can already determine.

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="The compiler infers the diamond's type argument from the declared variable type on the left-hand side of the assignment">
  <rect x="8" y="8" width="624" height="134" rx="8" fill="#0d1117"/>
  <text x="20" y="30" fill="#79c0ff" font-size="13" font-family="monospace">Map&lt;String, List&lt;Integer&gt;&gt; scores = new HashMap&lt;&gt;();</text>
  <line x1="30" y1="45" x2="140" y2="80" stroke="#6db33f" stroke-width="1.5" marker-end="url(adi1)"/>
  <line x1="560" y1="45" x2="480" y2="80" stroke="#6db33f" stroke-width="1.5" marker-end="url(adi1)"/>
  <text x="320" y="100" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">compiler infers &lt;&gt; = &lt;String, List&lt;Integer&gt;&gt; from the LEFT side</text>
  <text x="320" y="130" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Full type checking still happens -- the diamond just avoids re-typing what's already known.</text>
  <defs><marker id="adi1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker></defs>
</svg>

The diamond's type argument is inferred from context, not omitted — the compiler still fully type-checks the result.

## 5. Runnable example

Scenario: building up a small player-scores tracker — the same data structures, evolved from a single generic `List`, through a nested `Map<String, List<Integer>>`, to using the diamond operator with an anonymous class body — a capability added later, in Java 9, after the diamond operator's initial Java 7 introduction.

### Level 1 — Basic

```java
import java.util.*;

public class DiamondBasic {
    public static void main(String[] args) {
        // Before Java 7: List<String> names = new ArrayList<String>(); -- type repeated on both sides
        List<String> names = new ArrayList<>(); // diamond infers <String> from the declared type
        names.add("Alice");
        names.add("Bob");
        System.out.println(names);
    }
}
```

**How to run:** `java DiamondBasic.java`

`new ArrayList<>()` infers `<String>` from the declared type `List<String>` on the left — the compiler still fully type-checks `names.add("Alice")` as if `<String>` had been spelled out explicitly.

### Level 2 — Intermediate

```java
import java.util.*;

public class DiamondNested {
    public static void main(String[] args) {
        // Nested generics get noticeably worse without the diamond -- would be
        // new LinkedHashMap<String, List<Integer>>() repeated in full without it
        Map<String, List<Integer>> scoresByPlayer = new LinkedHashMap<>();

        scoresByPlayer.put("alice", new ArrayList<>(List.of(90, 85, 88)));
        scoresByPlayer.put("bob", new ArrayList<>(List.of(75, 80)));

        for (var entry : scoresByPlayer.entrySet()) {
            System.out.println(entry.getKey() + ": " + entry.getValue());
        }
    }
}
```

**How to run:** `java DiamondNested.java`

Without the diamond, the declaration would need `new LinkedHashMap<String, List<Integer>>()` — repeating a nested generic type in full. The diamond keeps the constructor call clean regardless of how deeply nested the generic type is, and `new ArrayList<>(List.of(90, 85, 88))` shows the same inference working for a constructor argument, not just an empty constructor.

### Level 3 — Advanced

```java
import java.util.*;

public class DiamondAnonymous {
    public static void main(String[] args) {
        // Since Java 9, the diamond can even be used with an anonymous class body --
        // this was NOT allowed from Java 7 through 8, where you had to spell out the type argument.
        Comparator<String> byLength = new Comparator<>() {
            @Override
            public int compare(String a, String b) {
                return Integer.compare(a.length(), b.length());
            }
        };

        List<String> words = new ArrayList<>(List.of("banana", "fig", "cherry", "kiwi"));
        words.sort(byLength);
        System.out.println(words);
    }
}
```

**How to run:** `java DiamondAnonymous.java`

`new Comparator<>() { ... }` combines the diamond with an anonymous class body — a combination that wasn't allowed in Java 7 or 8 (the compiler couldn't infer the type argument through an anonymous subclass's body at the time) and was specifically added in Java 9. On any modern JDK, this compiles and runs without issue.

## 6. Walkthrough

Execution starts in `main` of the Level 3 example. `new Comparator<>() { ... }` creates an anonymous class implementing `Comparator<String>` — the diamond's `<>` is resolved to `<String>` by the compiler, inferred from the declared type `Comparator<String> byLength` on the left, even though the object being constructed has an anonymous class body rather than a plain constructor call. Inside that body, `compare(String a, String b)` is overridden to return `Integer.compare(a.length(), b.length())` — a standard comparator pattern: negative if `a` is shorter, positive if longer, zero if equal length.

`words` is created as `new ArrayList<>(List.of("banana", "fig", "cherry", "kiwi"))` — again using the diamond, this time with a constructor argument (`List.of(...)`) rather than an empty parameter list; the type argument `<String>` is still inferred correctly from the declared `List<String> words`.

`words.sort(byLength)` sorts the list in place using the custom comparator. Java's sort is stable, so elements that compare equal (`"banana"` and `"cherry"`, both length 6) retain their relative order from the original list. Comparing lengths: `"banana"` = 6, `"fig"` = 3, `"cherry"` = 6, `"kiwi"` = 4. Sorted ascending by length: `"fig"` (3), `"kiwi"` (4), then `"banana"` and `"cherry"` (both 6, in their original relative order — `"banana"` appeared before `"cherry"` in the source list, so it stays first among the tied pair).

Expected output:
```
[fig, kiwi, banana, cherry]
```

## 7. Gotchas & takeaways

> Using the diamond with an **anonymous class body** (`new SomeInterface<>() { ... }`) only compiles on **Java 9 and later** — attempting it on Java 7 or 8 produces a compile error, since the compiler at that time couldn't infer the type argument through an anonymous subclass. If you ever see legacy code spelling out `new Comparator<String>() { ... }` in full instead of using `<>`, it's very likely written for (or copied from) a Java 7/8 codebase where the shorter form wasn't available.

- The diamond operator (`<>`) infers a generic constructor call's type argument from context — typically the declared variable type on the left-hand side of an assignment.
- It eliminates redundant, error-prone repetition of type arguments, and the benefit compounds significantly with deeply nested generic types.
- Full generic type checking still happens exactly as if the type argument had been written out explicitly — the diamond is a notational shortcut, not a relaxation of type safety.
- Diamond usage with an anonymous class body specifically requires Java 9 or later; it wasn't supported when the diamond operator was first introduced in Java 7.
- Prefer the diamond in all new code where the type argument is inferable from context — there's essentially no reason to write out a redundant type argument on the right-hand side of a generic construction on a modern JDK.
