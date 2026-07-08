---
card: java
gi: 468
slug: function-t-r
title: Function<T,R>
---

## 1. What it is

`Function<T, R>`, in `java.util.function`, is the general-purpose functional interface for "take one input of type `T`, produce one output of type `R`." Its single abstract method is `R apply(T t)`. It is the most commonly used of the built-in functional interfaces, since a huge amount of everyday logic — transforming, mapping, converting — fits this exact one-in-one-out shape.

## 2. Why & when

Before `java.util.function` existed, if you wanted to pass around "a transformation from `A` to `B`" as a value, you had to invent your own interface for it, or reach for a library like Guava that had already invented one. `Function<T, R>` is the JDK's standard, universally recognized answer to that need — any API that wants to accept "a way to transform one thing into another" can simply take a `Function<T, R>` parameter, and any caller anywhere can supply one via a lambda or method reference, with no custom interface required on either side.

You reach for `Function<T, R>` constantly: `Stream.map(Function<T, R>)` to transform each stream element, `Map.computeIfAbsent(key, Function<K, V>)` to compute a missing value, or simply as a parameter type on your own methods when you want the caller to supply a transformation rather than hard-coding one. `Function` also provides two useful `default` methods, `andThen` and `compose`, for chaining two functions together into a single pipeline.

## 3. Core concept

```java
import java.util.function.*;

Function<String, Integer> length = s -> s.length();
int result = length.apply("hello"); // 5

// andThen: run this function, THEN feed its result into the next one
Function<String, Integer> lengthPlusOne = length.andThen(n -> n + 1);
System.out.println(lengthPlusOne.apply("hello")); // 6

// compose: run the OTHER function first, then this one
Function<Integer, Integer> addOne = n -> n + 1;
Function<Integer, Integer> addOneThenDouble = addOne.andThen(n -> n * 2);
System.out.println(addOneThenDouble.apply(5)); // (5+1)*2 = 12
```

`apply` is the one method every `Function` must implement; `andThen`/`compose` are `default` methods built on top of `apply`, letting you combine functions without writing a new lambda for the combination by hand.

## 4. Diagram

<svg viewBox="0 0 640 140" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A Function takes one input of type T and produces one output of type R via apply">
  <rect x="8" y="8" width="624" height="124" rx="8" fill="#0d1117"/>
  <rect x="30" y="45" width="120" height="50" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="90" y="75" fill="#79c0ff" font-size="12" text-anchor="middle" font-family="monospace">T input</text>

  <rect x="260" y="35" width="150" height="70" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="335" y="60" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">Function&lt;T,R&gt;</text>
  <text x="335" y="80" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="monospace">apply(t)</text>

  <rect x="490" y="45" width="120" height="50" rx="6" fill="#1c2430" stroke="#f0883e"/>
  <text x="550" y="75" fill="#f0883e" font-size="12" text-anchor="middle" font-family="monospace">R output</text>

  <line x1="150" y1="70" x2="255" y2="70" stroke="#8b949e" stroke-width="2" marker-end="url(#a1)"/>
  <line x1="410" y1="70" x2="485" y2="70" stroke="#8b949e" stroke-width="2" marker-end="url(#a1)"/>
  <defs><marker id="a1" markerWidth="9" markerHeight="9" refX="4" refY="7" orient="auto"><path d="M0,0 L8,0 L4,7 Z" fill="#8b949e"/></marker></defs>
</svg>

One input in, one output out — the entire contract of `Function<T, R>`.

## 5. Runnable example

Scenario: a text-processing pipeline that converts a raw name into a display label — evolved from a single `Function` used directly, through chaining several functions together with `andThen`, to using `Function` as a genuine parameter type so callers can plug in their own transformation.

### Level 1 — Basic

```java
import java.util.function.*;

public class FunctionBasic {
    public static void main(String[] args) {
        Function<String, Integer> wordCount = text -> text.trim().split("\\s+").length;

        System.out.println(wordCount.apply("hello there world"));
        System.out.println(wordCount.apply("  just   one  "));
    }
}
```

**How to run:** `java FunctionBasic.java`

Expected output:
```
3
2
```

`wordCount.apply(text)` runs the lambda's body once per call: `text.trim()` removes leading/trailing whitespace, `.split("\\s+")` splits on runs of whitespace, and `.length` counts the resulting pieces. `Function<String, Integer>` here means "takes a `String`, returns an `Integer`" — exactly what `wordCount` does.

### Level 2 — Intermediate

```java
import java.util.function.*;

public class FunctionChaining {
    public static void main(String[] args) {
        Function<String, String> trim = String::trim;
        Function<String, String> lowercase = String::toLowerCase;
        Function<String, String> capitalize = s -> s.isEmpty() ? s : s.substring(0, 1).toUpperCase() + s.substring(1);

        // andThen chains functions left to right: trim, THEN lowercase, THEN capitalize.
        Function<String, String> normalize = trim.andThen(lowercase).andThen(capitalize);

        System.out.println("[" + normalize.apply("  ALICE  ") + "]");
        System.out.println("[" + normalize.apply("  bOB") + "]");
    }
}
```

**How to run:** `java FunctionChaining.java`

Expected output:
```
[Alice]
[Bob]
```

The real-world concern this adds: rather than writing one large lambda doing trim-then-lowercase-then-capitalize all at once, three small, individually testable `Function` values are combined with `andThen` into a single pipeline — each stage stays simple and reusable on its own, while `normalize` reads as a clear, linear sequence of transformations.

### Level 3 — Advanced

```java
import java.util.function.*;
import java.util.*;

public class FunctionAsParameter {
    // Accepting a Function<T, R> as a parameter lets the CALLER supply the transformation --
    // this method knows nothing about label formatting, only that it needs SOME String -> String function.
    static List<String> renderAll(List<String> rawNames, Function<String, String> formatter) {
        List<String> rendered = new ArrayList<>();
        for (String name : rawNames) {
            rendered.add(formatter.apply(name));
        }
        return rendered;
    }

    public static void main(String[] args) {
        List<String> rawNames = List.of("alice", "BOB", "  charlie  ");

        Function<String, String> asDisplayName = raw -> {
            String trimmed = raw.trim().toLowerCase();
            return trimmed.substring(0, 1).toUpperCase() + trimmed.substring(1);
        };

        Function<String, String> asShoutingTag = raw -> "[" + raw.trim().toUpperCase() + "]";

        System.out.println(renderAll(rawNames, asDisplayName));
        System.out.println(renderAll(rawNames, asShoutingTag));
    }
}
```

**How to run:** `java FunctionAsParameter.java`

Expected output:
```
[Alice, Bob, Charlie]
[[ALICE], [BOB], [CHARLIE]]
```

`renderAll` is written once, with no knowledge of *how* a name should be formatted — it simply calls `formatter.apply(name)` for each element and collects the results. Calling it with two different `Function<String, String>` values produces two completely different renderings of the same input list, without `renderAll` itself changing at all — the classic payoff of accepting behaviour as a parameter.

## 6. Walkthrough

Execution starts in `main` of the Level 3 example. `rawNames` holds three entries: `"alice"`, `"BOB"`, and `"  charlie  "`.

The first call, `renderAll(rawNames, asDisplayName)`, passes `asDisplayName` as the `formatter` argument. Inside `renderAll`, the `for` loop iterates over `rawNames` in order, calling `formatter.apply(name)` on each: for `"alice"`, `asDisplayName`'s body lower-cases (already lower-case) and capitalizes the first letter, producing `"Alice"`; for `"BOB"`, trimming and lower-casing gives `"bob"`, then capitalizing the first letter gives `"Bob"`; for `"  charlie  "`, trimming removes the surrounding spaces and lower-casing (already lower-case) gives `"charlie"`, capitalized to `"Charlie"`. Each result is appended to `rendered`, producing `["Alice", "Bob", "Charlie"]`, which `main` prints.

```
"alice"        --asDisplayName--> trim+lower="alice"   --> capitalize --> "Alice"
"BOB"          --asDisplayName--> trim+lower="bob"     --> capitalize --> "Bob"
"  charlie  "  --asDisplayName--> trim+lower="charlie" --> capitalize --> "Charlie"
```

The second call, `renderAll(rawNames, asShoutingTag)`, runs the exact same `renderAll` method body, but with `formatter` now bound to `asShoutingTag` instead. For each of the same three raw names, `asShoutingTag`'s body trims, upper-cases, and wraps the result in square brackets: `"alice"` becomes `"[ALICE]"`, `"BOB"` becomes `"[BOB]"`, `"  charlie  "` becomes `"[CHARLIE]"`. These are collected into a second list, `["[ALICE]", "[BOB]", "[CHARLIE]"]`, which `main` prints as the second line.

Nothing about `renderAll`'s own code changed between the two calls — only the `Function<String, String>` value passed in changed, and that alone was enough to produce entirely different output from the same input data.

## 7. Gotchas & takeaways

> `Function<T, R>` boxes primitive types — a `Function<Integer, Integer>` involves autoboxing/unboxing on every call, which has real (if usually small) overhead in tight loops. If you're working purely with `int`s or `double`s at high volume, prefer the primitive-specialized variants (`IntUnaryOperator`, `ToIntFunction<T>`, `IntFunction<R>`, and similar) that avoid boxing entirely — `Function<T, R>` is the general-purpose tool, not always the fastest one for primitive-heavy code.

- `Function<T, R>` represents "one input, one output" — its single abstract method is `R apply(T t)`.
- `andThen` chains a second function to run *after* this one, feeding this function's output into the next; `compose` chains a function to run *before* this one.
- Accepting a `Function<T, R>` as a method parameter is the standard way to let a caller supply a transformation without your method needing to know what that transformation actually does.
- `Stream.map(Function<T, R>)` is one of the most common places `Function` appears in everyday code — transforming each element of a stream into something else.
- For heavy primitive (`int`, `long`, `double`) use, prefer the specialized primitive variants of `Function` over boxing everything through `Integer`/`Long`/`Double`.
