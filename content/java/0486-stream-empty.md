---
card: java
gi: 486
slug: stream-empty
title: Stream.empty()
---

## 1. What it is

`Stream.empty()` returns a `Stream<T>` with zero elements — a valid, fully-formed stream that simply has nothing to iterate over. It's the streams equivalent of `Collections.emptyList()`: a ready-made "nothing here" value instead of `null`, so code that expects a `Stream<T>` never has to special-case a missing one.

## 2. Why & when

Methods that return a `Stream<T>` often have a code path where there's genuinely nothing to return — an optional piece of data wasn't present, a lookup found no match, or a recursive/conditional branch has no elements to contribute. Returning `null` in that case forces every caller to null-check before using the result, which defeats half the point of streams being chainable. `Stream.empty()` gives you a real, safe, zero-element stream instead, so callers can keep calling `.filter(...)`, `.map(...)`, `.collect(...)` without any special handling.

You reach for it most often inside a method that conditionally returns a stream (`return hasData ? buildStream() : Stream.empty();`), or with `flatMap` when a mapping function sometimes has nothing to contribute for a given input element.

## 3. Core concept

```java
import java.util.stream.*;

Stream<String> nothing = Stream.empty(); // zero elements
long count = nothing.count(); // 0

// Typical use: a method that may have nothing to return
Stream<String> tags(Optional<String> raw) {
    return raw.isPresent() ? Stream.of(raw.get().split(",")) : Stream.empty();
}
```

`Stream.empty()` is a valid, terminal-operation-ready stream — it behaves exactly like any other stream, just with nothing flowing through it.

## 4. Diagram

<svg viewBox="0 0 640 120" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Stream.empty produces a valid stream with zero elements, instead of returning null">
  <rect x="8" y="8" width="624" height="104" rx="8" fill="#0d1117"/>
  <rect x="40" y="35" width="200" height="50" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="140" y="65" fill="#6db33f" font-size="13" text-anchor="middle" font-family="monospace">Stream.empty()</text>
  <text x="270" y="65" fill="#8b949e" font-size="14" font-family="sans-serif">-&gt;</text>
  <rect x="310" y="35" width="260" height="50" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-dasharray="4,3"/>
  <text x="440" y="65" fill="#79c0ff" font-size="12" text-anchor="middle" font-family="sans-serif">(empty -- 0 elements, still a valid Stream)</text>
</svg>

The dashed box has no elements inside, but it's a real `Stream<T>` — safe to chain further operations on.

## 5. Runnable example

Scenario: fetching a user's saved search tags, which may or may not exist — evolved from a plain conditional empty-stream return, through `flatMap`-based aggregation across several users, to a version that reports which users contributed zero tags without ever null-checking.

### Level 1 — Basic

```java
import java.util.*;
import java.util.stream.*;

public class EmptyBasic {
    static Stream<String> tagsFor(Optional<String> rawTags) {
        return rawTags.isPresent() ? Stream.of(rawTags.get().split(",")) : Stream.empty();
    }

    public static void main(String[] args) {
        long count = tagsFor(Optional.empty()).count();
        System.out.println("Tag count: " + count);
    }
}
```

**How to run:** `java EmptyBasic.java`

Expected output:
```
Tag count: 0
```

`tagsFor(Optional.empty())` has no raw tag string to split, so instead of returning `null` (which would crash the moment `.count()` was called on it), it returns `Stream.empty()` — a real, zero-element stream that `.count()` safely reports as `0`.

### Level 2 — Intermediate

```java
import java.util.*;
import java.util.stream.*;

public class EmptyFlatMap {
    static Stream<String> tagsFor(Optional<String> rawTags) {
        return rawTags.isPresent() ? Stream.of(rawTags.get().split(",")) : Stream.empty();
    }

    public static void main(String[] args) {
        List<Optional<String>> userTags = List.of(
                Optional.of("java,streams"),
                Optional.empty(),
                Optional.of("records"),
                Optional.empty()
        );

        List<String> allTags = userTags.stream()
                .flatMap(EmptyFlatMap::tagsFor) // users with no tags contribute nothing -- no crash, no special case
                .toList();

        System.out.println("All tags: " + allTags);
    }
}
```

**How to run:** `java EmptyFlatMap.java`

Expected output:
```
All tags: [java, streams, records]
```

The real-world concern this adds: aggregating tags across *multiple* users. `flatMap(EmptyFlatMap::tagsFor)` calls `tagsFor` once per user; for the two users with `Optional.empty()`, `tagsFor` returns `Stream.empty()`, which `flatMap` simply contributes zero elements from — no `if (tags != null)` guard needed anywhere in the pipeline, unlike what would be required if `tagsFor` could return `null`.

### Level 3 — Advanced

```java
import java.util.*;
import java.util.stream.*;

public class EmptyReport {
    record User(String name, Optional<String> rawTags) {}

    static Stream<String> tagsFor(Optional<String> rawTags) {
        return rawTags.isPresent() ? Stream.of(rawTags.get().split(",")) : Stream.empty();
    }

    public static void main(String[] args) {
        List<User> users = List.of(
                new User("alice", Optional.of("java,streams")),
                new User("bob", Optional.empty()),
                new User("carol", Optional.of("records"))
        );

        for (User user : users) {
            List<String> tags = tagsFor(user.rawTags()).toList();
            String status = tags.isEmpty() ? "(no tags)" : String.join(", ", tags);
            System.out.println(user.name() + ": " + status);
        }

        long usersWithNoTags = users.stream()
                .filter(user -> tagsFor(user.rawTags()).findAny().isEmpty())
                .count();
        System.out.println("Users with no tags: " + usersWithNoTags);
    }
}
```

**How to run:** `java EmptyReport.java`

Expected output:
```
alice: java, streams
bob: (no tags)
carol: records
Users with no tags: 1
```

This adds a reporting layer that distinguishes "had tags" from "had none" per user, and separately counts how many users contributed nothing — all built entirely on `Stream.empty()` behaving like any other stream: `.findAny().isEmpty()` on an empty stream correctly returns `true` with no special-casing.

## 6. Walkthrough

Execution starts in `main` of the Level 3 example. `users` is built with three entries: `alice` (has tags), `bob` (`Optional.empty()`), `carol` (has tags).

The `for` loop processes each user in order. For `alice`: `tagsFor(Optional.of("java,streams"))` sees the `Optional` is present, so it calls `.get()` to get `"java,streams"`, splits it into `{"java", "streams"}`, and wraps it with `Stream.of(...)`. `.toList()` collects it to `["java", "streams"]`; since it's not empty, `status` becomes `"java, streams"`, and `"alice: java, streams"` prints.

For `bob`: `tagsFor(Optional.empty())` sees the `Optional` is absent, so it returns `Stream.empty()` directly — no splitting attempted, no `null` involved. `.toList()` on that empty stream yields `[]`; since `tags.isEmpty()` is `true`, `status` becomes `"(no tags)"`, and `"bob: (no tags)"` prints.

For `carol`: same path as `alice` — `"carol: records"` prints.

```
alice -> Optional present -> Stream.of(["java","streams"]) -> toList() -> ["java","streams"] -> "java, streams"
bob   -> Optional empty   -> Stream.empty()                 -> toList() -> []                 -> "(no tags)"
carol -> Optional present -> Stream.of(["records"])         -> toList() -> ["records"]         -> "records"
```

After the loop, `users.stream().filter(user -> tagsFor(user.rawTags()).findAny().isEmpty())` re-checks each user: for `alice`, `tagsFor(...).findAny()` finds `"java"` as *a* present element, so `.isEmpty()` on that `Optional<String>` is `false` — `alice` is filtered out. For `bob`, `tagsFor(...)` is `Stream.empty()`, so `.findAny()` correctly returns an empty `Optional`, and `.isEmpty()` is `true` — `bob` passes the filter. For `carol`, same as `alice` — filtered out. The count of users passing the filter is `1`, printed as `"Users with no tags: 1"`.

## 7. Gotchas & takeaways

> `Stream.empty()` is not the same as a stream that *becomes* empty after filtering — both behave identically to downstream operations, but conflating "empty from the start" with "filtered down to nothing" can make debugging confusing. What matters is that both are safe: no terminal operation on an empty stream throws just because it's empty (`.count()` is `0`, `.findAny()` is an empty `Optional`, `.toList()` is `[]`).

- `Stream.empty()` returns a genuine, fully-usable `Stream<T>` with zero elements — never return `null` where a `Stream<T>` is expected.
- It's the natural return value for a conditional branch in a stream-returning method that has nothing to contribute.
- Combined with `flatMap`, it lets some input elements silently contribute zero output elements, with no null-checks anywhere in the pipeline.
- Terminal operations behave predictably on an empty stream: `.count()` is `0`, `.findAny()`/`.findFirst()` return an empty `Optional`, `.toList()`/`.collect(...)` return an empty collection.
- Type inference usually determines `T` from context (`Stream.empty()` assigned to a `Stream<String>` variable); when it can't, an explicit type witness like `Stream.<String>empty()` may be needed.
