---
card: java
gi: 557
slug: string-join
title: String.join()
---

## 1. What it is

`String.join(delimiter, elements...)` is a static convenience method on `String` that joins a delimiter-separated sequence of strings — either as varargs or from any `Iterable<CharSequence>` — into one string. It's the simplest possible way to join things, with no brackets, no configuration, just delimiter placement.

## 2. Why & when

Most joins don't need prefixes, suffixes, or an empty-value override — they just need `"a,b,c"` from `["a", "b", "c"]`. Reaching for `new StringJoiner(",")` for that is more ceremony than the job requires; `String.join(",", list)` does it in one call. Use `String.join` for the common case (flat delimited output), and reach for `StringJoiner` directly (or `Collectors.joining` in a stream) when you also need bracketing or an empty-collection message.

## 3. Core concept

```java
String a = String.join(", ", "x", "y", "z");        // varargs form
System.out.println(a); // x, y, z

List<String> names = List.of("Ann", "Bo", "Cy");
String b = String.join(" & ", names);                 // Iterable form
System.out.println(b); // Ann & Bo & Cy
```

There are exactly two overloads: `join(CharSequence delimiter, CharSequence... elements)` and `join(CharSequence delimiter, Iterable<? extends CharSequence> elements)`. Internally, both delegate to a `StringJoiner` with no prefix or suffix.

## 4. Diagram

<svg viewBox="0 0 640 130" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="String.join places the delimiter strictly between elements, never at the ends">
  <rect x="8" y="10" width="624" height="45" rx="6" fill="#0d1117"/>
  <text x="20" y="37" fill="#8b949e" font-size="11" font-family="sans-serif">String.join(", ", "x", "y", "z")</text>

  <rect x="8" y="65" width="624" height="50" rx="8" fill="#1c2430" stroke="#6db33f"/>
  <text x="40" y="97" fill="#e6edf3" font-size="16" font-family="monospace">x</text>
  <text x="65" y="97" fill="#79c0ff" font-size="16" font-family="monospace">, </text>
  <text x="90" y="97" fill="#e6edf3" font-size="16" font-family="monospace">y</text>
  <text x="115" y="97" fill="#79c0ff" font-size="16" font-family="monospace">, </text>
  <text x="140" y="97" fill="#e6edf3" font-size="16" font-family="monospace">z</text>
  <text x="200" y="97" fill="#8b949e" font-size="11" font-family="sans-serif">&lt;- delimiter appears only BETWEEN elements</text>
</svg>

No leading or trailing delimiter is ever produced, regardless of how many elements are joined.

## 5. Runnable example

Scenario: building a breadcrumb navigation string for a website — starting from a flat list of page names, then handling the mix of a fixed "Home" root with dynamic segments, then building nested breadcrumb trails for a multi-level category tree.

### Level 1 — Basic

```java
import java.util.List;

public class BreadcrumbBasic {
    public static void main(String[] args) {
        List<String> pages = List.of("Shop", "Electronics", "Laptops");
        String breadcrumb = String.join(" > ", pages);
        System.out.println(breadcrumb);
    }
}
```

**How to run:** `java BreadcrumbBasic.java`

Expected output:
```
Shop > Electronics > Laptops
```

`String.join(" > ", pages)` takes the `Iterable<String>` overload since `pages` is a `List<String>`. It walks the list once, inserting `" > "` between consecutive elements, and returns the assembled string — no loop, no `StringBuilder`, no trailing-delimiter cleanup required in user code.

### Level 2 — Intermediate

```java
import java.util.List;
import java.util.ArrayList;

public class BreadcrumbWithHome {
    static String buildBreadcrumb(List<String> segments) {
        List<String> full = new ArrayList<>();
        full.add("Home");
        full.addAll(segments);
        return String.join(" > ", full);
    }

    public static void main(String[] args) {
        System.out.println(buildBreadcrumb(List.of("Shop", "Electronics", "Laptops")));
        System.out.println(buildBreadcrumb(List.of())); // just the home page
    }
}
```

**How to run:** `java BreadcrumbWithHome.java`

Expected output:
```
Home > Shop > Electronics > Laptops
Home
```

The real-world concern this adds: a breadcrumb should always start at a fixed "Home" root, even for the home page itself where there are no further segments. `full` is built by prepending `"Home"` before `String.join` ever runs, so the join logic itself stays trivial — the second call proves that joining a single-element list with any delimiter simply returns that one element, with no dangling delimiter.

### Level 3 — Advanced

```java
import java.util.List;
import java.util.ArrayList;
import java.util.Optional;

public class BreadcrumbTree {
    record Category(String name, Optional<Category> parent) {}

    static List<String> pathTo(Category category) {
        List<String> path = new ArrayList<>();
        Optional<Category> current = Optional.of(category);
        while (current.isPresent()) {
            path.add(0, current.get().name()); // prepend so root ends up first
            current = current.get().parent();
        }
        return path;
    }

    static String renderTrail(Category leaf) {
        List<String> segments = new ArrayList<>();
        segments.add("Home");
        segments.addAll(pathTo(leaf));
        return String.join(" > ", segments);
    }

    public static void main(String[] args) {
        Category electronics = new Category("Electronics", Optional.empty());
        Category laptops = new Category("Laptops", Optional.of(electronics));
        Category gamingLaptops = new Category("Gaming Laptops", Optional.of(laptops));

        System.out.println(renderTrail(gamingLaptops));
        System.out.println(renderTrail(electronics));
    }
}
```

**How to run:** `java BreadcrumbTree.java`

Expected output:
```
Home > Electronics > Laptops > Gaming Laptops
Home > Electronics
```

This handles the production-flavoured case where categories form a tree via parent references rather than being handed as a pre-flattened list — `pathTo(...)` walks parent links from leaf to root, builds the segment list in root-to-leaf order, and only then does `String.join` perform the actual formatting, keeping the tree-walking logic and the string-joining logic cleanly separated.

## 6. Walkthrough

Execution starts in `main` of the Level 3 example. Three `Category` records are built: `electronics` (no parent), `laptops` (parent = `electronics`), `gamingLaptops` (parent = `laptops`) — forming a three-level chain.

`renderTrail(gamingLaptops)` is called. `segments` starts as `["Home"]`. `pathTo(gamingLaptops)` is called to compute the category chain:

```
current = gamingLaptops -> path.add(0, "Gaming Laptops") -> path = [Gaming Laptops]
current = laptops       -> path.add(0, "Laptops")        -> path = [Laptops, Gaming Laptops]
current = electronics   -> path.add(0, "Electronics")    -> path = [Electronics, Laptops, Gaming Laptops]
current = empty         -> loop ends
```

Each iteration prepends (`add(0, ...)`) rather than appends, because the walk moves leaf-to-root but the desired output order is root-to-leaf — prepending reverses the walk order for free without a separate `Collections.reverse(...)` call.

`pathTo` returns `[Electronics, Laptops, Gaming Laptops]`. Back in `renderTrail`, `segments.addAll(...)` makes `segments = [Home, Electronics, Laptops, Gaming Laptops]`. `String.join(" > ", segments)` then produces `"Home > Electronics > Laptops > Gaming Laptops"`.

`main` prints that string, then calls `renderTrail(electronics)`. Since `electronics` has no parent, `pathTo` runs its loop exactly once, returning `[Electronics]`; `segments` becomes `[Home, Electronics]`; the joined result is `"Home > Electronics"`.

## 7. Gotchas & takeaways

> `String.join` only accepts `CharSequence` elements (varargs or `Iterable<? extends CharSequence>`). Passing a `List<Integer>` won't compile — you must map to strings first, e.g. `list.stream().map(String::valueOf).collect(Collectors.joining(", "))`, or build a `List<String>` before calling `String.join`.

- `String.join(delimiter, "a", "b", "c")` and `String.join(delimiter, someIterable)` are the only two overloads — no prefix/suffix support.
- Joining an empty collection returns an empty string `""`, not `null` and not the delimiter.
- Joining a single-element collection returns that element unchanged, with no delimiter appended.
- For bracketed output (`[a, b, c]`) or a custom empty-collection message, use `StringJoiner` directly instead.
- In a stream pipeline, prefer `Collectors.joining(delimiter)` over collecting to a `List` first and then calling `String.join` — it avoids the intermediate list.
