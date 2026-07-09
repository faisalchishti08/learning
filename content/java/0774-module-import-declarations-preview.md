---
card: java
gi: 774
slug: module-import-declarations-preview
title: Module import declarations (preview)
---

## 1. What it is

**Java 23** (JEP 476) previews a new import form: `import module java.base;` imports **every package exported by a module**, in one line, instead of naming each package individually. Where you'd otherwise write `import java.util.*; import java.util.stream.*; import java.io.*; ...` line after line, `import module java.base;` (or any other module you depend on, like `java.sql`) brings in all of that module's exported packages at once. It's a preview feature: it requires `--enable-preview` to compile and run, and it works alongside — not instead of — ordinary single-package and single-type imports.

## 2. Why & when

Java's [module system](0568-module-concept-motivation.md) organizes the platform (and your own code, if modularized) into modules that each export a set of packages, but importing from those packages still meant listing every package you touch, one `import` line at a time — tedious for small programs, scripts, and examples that legitimately want broad access to a module's surface (say, most of `java.base` for a text-processing script). JEP 476 is aimed squarely at that convenience gap, and it pairs naturally with [implicitly declared classes and instance `main` methods](0766-implicitly-declared-classes-instance-main-2nd-preview.md) — the other Java-as-a-scripting-language feature — where the whole point is minimizing setup ceremony for small, self-contained programs. It's not meant to replace precise, single-package imports in larger applications, where importing exactly what you use keeps dependencies legible; it's meant for the case where a program genuinely wants "everything `java.base` (or `java.sql`, or `java.net.http`) offers," without transcribing that list by hand.

## 3. Core concept

```java
import module java.base; // brings in java.util.*, java.io.*, java.util.stream.*, and more

void main() {
    List<String> names = List.of("Grace", "Ada", "Linus");
    List<String> sorted = names.stream().sorted().toList();
    System.out.println(sorted);
}
```

No `import java.util.List;` or `import java.util.stream.*;` needed — `java.base`'s exported packages, including `java.util` and `java.util.stream`, are all in scope from the one `import module` line.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Import module java.base brings every exported package of the java.base module into scope in one declaration, instead of one import per package">
  <rect x="20" y="20" width="600" height="40" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="45" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">import module java.base;</text>

  <rect x="40" y="90" width="130" height="40" rx="6" fill="#0f1620" stroke="#79c0ff"/>
  <text x="105" y="115" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">java.util.*</text>

  <rect x="190" y="90" width="130" height="40" rx="6" fill="#0f1620" stroke="#79c0ff"/>
  <text x="255" y="115" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">java.io.*</text>

  <rect x="340" y="90" width="130" height="40" rx="6" fill="#0f1620" stroke="#79c0ff"/>
  <text x="405" y="115" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">java.util.stream.*</text>

  <rect x="490" y="90" width="130" height="40" rx="6" fill="#0f1620" stroke="#79c0ff"/>
  <text x="555" y="115" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">...and more</text>

  <text x="320" y="170" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">One declaration replaces one import line per exported package</text>
</svg>

*A single module import expands to every package that module exports.*

## 5. Runnable example

Scenario: a small script that reads lines of text, filters and sorts them, and writes a summary — growing from many precise package imports into a single module import, then into a script that reaches across two modules.

### Level 1 — Basic

```java
import java.util.*;
import java.util.stream.*;

void main() {
    List<String> words = List.of("banana", "apple", "cherry");
    List<String> sorted = words.stream().sorted().toList();
    System.out.println(sorted);
}
```

**How to run:** `java --enable-preview --source 23 WordsBasic.java` (JDK 23+; save as `WordsBasic.java`, matching [implicitly declared classes](0766-implicitly-declared-classes-instance-main-2nd-preview.md) style with no explicit class or `String[] args`).

Two separate `import` lines bring in `java.util` (for `List`) and `java.util.stream` (for the `Stream` API) — precise, but two lines for two packages from the same module.

### Level 2 — Intermediate

```java
import module java.base;

void main() {
    List<String> words = List.of("banana", "apple", "cherry");
    List<String> sorted = words.stream().sorted().toList();
    System.out.println(sorted);

    Map<Integer, List<String>> byLength = sorted.stream()
        .collect(Collectors.groupingBy(String::length));
    System.out.println(byLength);
}
```

**How to run:** `java --enable-preview --source 23 WordsModule.java`.

The real-world concern added: the program grows to also use `Map`, `Collectors`, and `String::length` — types and packages spanning `java.util` and `java.util.stream` — but only **one** `import module java.base;` line is needed, since every one of those types lives in a package `java.base` exports; adding more `java.base` functionality later requires no new import at all.

### Level 3 — Advanced

```java
import module java.base;
import module java.net.http;

void main() throws Exception {
    List<String> words = List.of("banana", "apple", "cherry", "date");
    Map<Integer, List<String>> byLength = words.stream()
        .collect(Collectors.groupingBy(String::length));
    System.out.println("grouped: " + byLength);

    HttpClient client = HttpClient.newHttpClient();
    HttpRequest request = HttpRequest.newBuilder(URI.create("https://example.com"))
        .GET()
        .build();
    HttpResponse<String> response = client.send(request, HttpResponse.BodyHandlers.ofString());
    System.out.println("status: " + response.statusCode());
}
```

**How to run:** `java --enable-preview --source 23 WordsAndHttp.java` (requires network access to `example.com`; JDK 23+).

This adds the production-flavored hard case: importing **two different modules** (`java.base` and `java.net.http`) side by side — `HttpClient`, `HttpRequest`, `HttpResponse`, and `URI` all come from `java.net.http`'s exported packages, while `Map`, `List`, and `Collectors` still come from `java.base` — showing that module imports compose just like package imports do, each contributing its own set of exported packages to the compilation unit's scope.

## 6. Walkthrough

Tracing `WordsAndHttp.main`:

1. The compiler processes the two `import module` declarations first, expanding `import module java.base;` into every package `java.base` exports (`java.util`, `java.util.stream`, `java.net`, `java.io`, and many more) and `import module java.net.http;` into `java.net.http`'s exported packages — all as if each individual package had been imported with its own `import pkg.*;` line.
2. `main` builds `words`, a `List<String>` of four fruit names — `List` resolves from `java.util`, reached via the `java.base` module import.
3. `words.stream().collect(Collectors.groupingBy(String::length))` groups the words by their length into a `Map<Integer, List<String>>` — `Stream`, `Collectors`, and `Map` all resolve the same way, with no explicit `import java.util.stream.Collectors;` line anywhere in the file.
4. The grouped map prints first, showing each length bucket and its matching words.
5. `HttpClient.newHttpClient()` creates an HTTP client — `HttpClient` resolves from `java.net.http`, reached via the *second* module import; without it, this line wouldn't compile even though `java.base`'s import is also present, since `java.net.http` is a separate module.
6. `HttpRequest.newBuilder(URI.create(...))...build()` constructs a `GET` request to `https://example.com` — `URI` here resolves from `java.net`, one of `java.base`'s exported packages, so a single request-building expression pulls types from *both* imported modules at once.
7. `client.send(request, HttpResponse.BodyHandlers.ofString())` sends the request synchronously and blocks for the response; `response.statusCode()` reads the HTTP status code from the returned `HttpResponse<String>`.

Expected output (network-dependent, but typically):
```
grouped: {4=[date], 5=[apple], 6=[banana, cherry]}
status: 200
```

## 7. Gotchas & takeaways

> **Gotcha:** `import module M` only brings in packages that module `M` **exports**, not every package physically inside it — internal, non-exported packages stay inaccessible, exactly as the module system has always intended. A module import is convenience over the *public* surface of a module, not a way to bypass module encapsulation.

- Preview in Java 23 (JEP 476) — requires `--enable-preview`; syntax is `import module <module-name>;`.
- Expands to importing every package the named module exports — equivalent to writing one `import pkg.*;` per exported package.
- Composes with ordinary package/type imports and with imports of other modules in the same file.
- If two imported modules export a type with the same simple name, that name becomes ambiguous and must be disambiguated with a regular, explicit single-type import — module imports don't silently pick a winner.
- Pairs naturally with [implicitly declared classes and instance `main` methods](0766-implicitly-declared-classes-instance-main-2nd-preview.md) for minimal-ceremony scripts, though it works equally well in ordinary classes.
