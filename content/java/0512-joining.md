---
card: java
gi: 512
slug: joining
title: joining()
---

## 1. What it is

`Collectors.joining()` concatenates a stream of `CharSequence` (typically `String`) elements into a single `String`. It has three overloads: `joining()` with no arguments simply concatenates everything with nothing between elements; `joining(delimiter)` inserts the given delimiter between elements; `joining(delimiter, prefix, suffix)` additionally wraps the whole result with a prefix at the start and a suffix at the end.

## 2. Why & when

`joining` is how you turn a stream of strings into one formatted `String`, without manually managing a `StringBuilder`, tracking whether you're on the first element (to avoid a leading delimiter), or handling the empty-stream edge case yourself. It's the direct streams equivalent of `String.join(delimiter, collection)`, but composable as the terminal step of a larger pipeline that filtered, mapped, or sorted first.

## 3. Core concept

```java
import java.util.stream.*;

String noDelim = Stream.of("a", "b", "c").collect(Collectors.joining()); // "abc"

String withDelim = Stream.of("a", "b", "c").collect(Collectors.joining(", ")); // "a, b, c"

String wrapped = Stream.of("a", "b", "c")
        .collect(Collectors.joining(", ", "[", "]")); // "[a, b, c]"
```

`joining` handles delimiter placement (never a leading or trailing stray delimiter) and prefix/suffix wrapping automatically, regardless of how many elements the stream has, including zero.

## 4. Diagram

<svg viewBox="0 0 640 110" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="joining concatenates stream elements into one string with an optional delimiter, prefix, and suffix">
  <rect x="8" y="8" width="624" height="94" rx="8" fill="#0d1117"/>
  <rect x="30" y="20" width="45" height="30" fill="#1c2430" stroke="#79c0ff"/><text x="52" y="40" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="monospace">"a"</text>
  <rect x="85" y="20" width="45" height="30" fill="#1c2430" stroke="#79c0ff"/><text x="107" y="40" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="monospace">"b"</text>
  <rect x="140" y="20" width="45" height="30" fill="#1c2430" stroke="#79c0ff"/><text x="162" y="40" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="monospace">"c"</text>
  <text x="230" y="42" fill="#8b949e" font-size="12" font-family="sans-serif">joining(", ", "[", "]") -&gt;</text>
  <rect x="420" y="20" width="140" height="30" rx="4" fill="#1c2430" stroke="#6db33f"/><text x="490" y="40" fill="#6db33f" font-size="12" text-anchor="middle" font-family="monospace">"[a, b, c]"</text>
</svg>

The delimiter appears only *between* elements, and the prefix/suffix wrap the entire joined result exactly once.

## 5. Runnable example

Scenario: formatting a shipping label's address line for a package — evolved from a plain comma-joined list, through combining `joining` with `map` to format individual fields, to a version that handles missing/blank fields gracefully so the final address doesn't end up with stray delimiters.

### Level 1 — Basic

```java
import java.util.*;
import java.util.stream.*;

public class JoiningBasic {
    public static void main(String[] args) {
        List<String> tags = List.of("fragile", "electronics", "priority");

        String tagLine = tags.stream().collect(Collectors.joining(", "));
        System.out.println("Tags: " + tagLine);
    }
}
```

**How to run:** `java JoiningBasic.java`

Expected output:
```
Tags: fragile, electronics, priority
```

`Collectors.joining(", ")` concatenates the three tags with `", "` placed only *between* them — no leading or trailing comma, regardless of how many elements there are.

### Level 2 — Intermediate

```java
import java.util.*;
import java.util.stream.*;

public class JoiningWithMap {
    record Item(String name, int quantity) {}

    public static void main(String[] args) {
        List<Item> items = List.of(
                new Item("Widget", 3),
                new Item("Gadget", 1),
                new Item("Gizmo", 5)
        );

        String summary = items.stream()
                .map(item -> item.quantity() + "x " + item.name())
                .collect(Collectors.joining(", ", "Package contains: ", "."));

        System.out.println(summary);
    }
}
```

**How to run:** `java JoiningWithMap.java`

Expected output:
```
Package contains: 3x Widget, 1x Gadget, 5x Gizmo.
```

The real-world concern this adds: `joining` only works on `CharSequence` elements, so `.map(...)` runs first to transform each `Item` into a formatted string (`"3x Widget"`, etc.) before `.collect(Collectors.joining(", ", "Package contains: ", "."))` combines them with a delimiter and wraps the whole thing in a prefix and suffix — building a complete, readable sentence directly from structured data.

### Level 3 — Advanced

```java
import java.util.*;
import java.util.stream.*;

public class JoiningAddressLine {
    record Address(String street, String city, String state, String zip, String country) {}

    public static void main(String[] args) {
        // A real address, with some optional fields left blank -- a common real-world messiness.
        Address address = new Address("123 Main St", "Springfield", "", "62704", "");

        String addressLine = Stream.of(address.street(), address.city(), address.state(), address.zip(), address.country())
                .filter(field -> !field.isBlank()) // drop blank fields so we don't get stray ", , "
                .collect(Collectors.joining(", "));

        System.out.println("Shipping to: " + addressLine);
    }
}
```

**How to run:** `java JoiningAddressLine.java`

Expected output:
```
Shipping to: 123 Main St, Springfield, 62704
```

This handles a real-world messiness: not every address field is always populated (`state` and `country` are blank here). Naively joining all five fields would produce `"123 Main St, Springfield, , 62704, "` — awkward stray commas from the blank fields. `.filter(field -> !field.isBlank())` removes empty fields *before* `joining` ever sees them, so the delimiter only ever appears between genuinely present values, producing a clean `"123 Main St, Springfield, 62704"`.

## 6. Walkthrough

Execution starts in `main` of the Level 3 example. `address` is built with `street="123 Main St"`, `city="Springfield"`, `state=""`, `zip="62704"`, `country=""` — two of the five fields are blank.

`Stream.of(address.street(), address.city(), address.state(), address.zip(), address.country())` creates a five-element `Stream<String>` in field order: `"123 Main St"`, `"Springfield"`, `""`, `"62704"`, `""`.

`.filter(field -> !field.isBlank())` evaluates each: `"123 Main St".isBlank()` is `false`, so `!false = true` — kept. `"Springfield".isBlank()` is `false` — kept. `"".isBlank()` is `true`, so `!true = false` — dropped (this is the `state` field). `"62704".isBlank()` is `false` — kept. `"".isBlank()` is `true` — dropped (this is the `country` field).

```
"123 Main St" -> isBlank() false -> KEPT
"Springfield" -> isBlank() false -> KEPT
""  (state)   -> isBlank() true  -> DROPPED
"62704"       -> isBlank() false -> KEPT
""  (country) -> isBlank() true  -> DROPPED

Surviving stream: ["123 Main St", "Springfield", "62704"]
```

After filtering, three fields remain: `"123 Main St"`, `"Springfield"`, `"62704"`. `.collect(Collectors.joining(", "))` concatenates them with `", "` placed only between consecutive elements — since only three elements survived, exactly two delimiters are inserted, producing `"123 Main St, Springfield, 62704"` — no stray commas from the two blank fields that were filtered out beforehand. `main` prints `"Shipping to: 123 Main St, Springfield, 62704"`.

## 7. Gotchas & takeaways

> `Collectors.joining()`, called on an **empty** stream, returns an empty string (`""`) for the no-delimiter and delimiter-only forms — but the three-argument form still includes the prefix and suffix even with zero elements, e.g. `Stream.<String>empty().collect(Collectors.joining(", ", "[", "]"))` produces `"[]"`, not an empty string. Account for this when the joined result might legitimately have nothing to join.

- `Collectors.joining()` concatenates a stream of `CharSequence` elements into one `String`, with optional delimiter, prefix, and suffix.
- The delimiter appears only *between* elements — never leading, never trailing — regardless of how many elements are joined.
- Since `joining` only accepts `CharSequence` elements, non-string data typically needs a `.map(...)` step first to convert each element into its display string.
- Filtering out blank or empty values *before* `joining` (as in Level 3) avoids awkward stray delimiters that a naive join of all fields, including empty ones, would otherwise produce.
- For a stream with zero elements, the prefix/suffix form still applies both wrappers even though nothing is joined between them — the result is `prefix + suffix`, not an empty string.
