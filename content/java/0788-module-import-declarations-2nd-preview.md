---
card: java
gi: 788
slug: module-import-declarations-2nd-preview
title: Module import declarations (2nd preview)
---

## 1. What it is

**Java 24** (JEP 494) is the **second preview** of [module import declarations](0774-module-import-declarations-preview.md), carrying forward `import module <name>;` from Java 23's first preview. The core capability — one declaration importing every package a module exports — is unchanged. This round refines the **ambiguity-resolution rules**: when a module import and an ordinary single-type import (or another module import) would bring in two different types with the same simple name, the compiler now applies a clearer, more predictable precedence — an explicit single-type import always wins over anything a module import contributes, and two conflicting module imports produce a clear compile error at the point of use rather than a silent, arbitrary pick.

## 2. Why & when

The first preview established that `import module M` behaves like importing every package `M` exports, but "every package" inevitably raises a question the first round left underspecified: what happens when two different modules you've imported both export a type with the same simple name — say, both exposing a class called `Builder`? The first preview's answer (an error if you actually reference the ambiguous name) was correct but rough at the edges, particularly around how an explicit, deliberate single-type import should interact with a broader module import that happens to also supply a type of the same name. This round tightens exactly that: if you write both `import module big.framework;` and `import specific.pkg.Builder;`, the explicit import should obviously win — you asked for that specific `Builder` by name — and the refined rules make that precedence explicit and predictable rather than leaving it as an edge case the first preview's specification didn't fully pin down.

## 3. Core concept

```java
import module java.base;
import java.util.stream.Collectors; // explicit single-type import

void main() {
    // Collectors resolves to the explicitly imported type, even though
    // "import module java.base" also brings java.util.stream.Collectors into scope —
    // the explicit import wins, unambiguously, per this round's refined rules.
    var grouped = List.of("a", "bb", "ccc").stream()
        .collect(Collectors.groupingBy(String::length));
    System.out.println(grouped);
}
```

Both imports name the same type here, so there's no actual conflict to observe — but the refined rule guarantees the explicit import always takes precedence whenever they *would* disagree.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="When an explicit single-type import and a module import both supply a type of the same simple name, the second preview's refined rules make the explicit import win predictably" >
  <rect x="20" y="20" width="600" height="40" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="45" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">import module M; + import specific.pkg.Type; — same simple name</text>

  <rect x="40" y="90" width="240" height="55" rx="8" fill="#0f1620" stroke="#79c0ff"/>
  <text x="160" y="112" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">import module M;</text>
  <text x="160" y="130" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">broad, contributes many types</text>

  <rect x="360" y="90" width="240" height="55" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="480" y="112" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">import specific.pkg.Type;</text>
  <text x="480" y="130" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">explicit — always wins on conflict</text>

  <text x="320" y="170" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Two conflicting module imports still produce a clear compile error at point of use</text>
</svg>

*Explicit intent always beats implicit breadth when a name is ambiguous.*

## 5. Runnable example

Scenario: a small script combining broad `java.base` access with one deliberately specific import, growing into a genuine two-module conflict to observe the refined ambiguity rule directly.

### Level 1 — Basic

```java
import module java.base;

void main() {
    List<String> words = List.of("date", "apple", "kiwi");
    List<String> sorted = words.stream().sorted().toList();
    System.out.println(sorted);
}
```

**How to run:** `java --enable-preview --source 24 WordsModuleBasic.java` (JDK 24+).

A single module import brings in everything needed — the same behavior as the first preview, unchanged.

### Level 2 — Intermediate

```java
import module java.base;
import java.util.stream.Collectors;

void main() {
    List<String> words = List.of("date", "apple", "kiwi", "fig", "pear");
    Map<Integer, List<String>> byLength = words.stream()
        .collect(Collectors.groupingBy(String::length));
    System.out.println(byLength);
}
```

**How to run:** `java --enable-preview --source 24 WordsExplicitAndModule.java`.

The real-world concern added: an explicit `import java.util.stream.Collectors;` sits alongside `import module java.base;`, which *also* exports `java.util.stream.Collectors` — under this round's refined rules, the explicit import unambiguously wins, resolving to the exact same type here with no observable conflict, but demonstrating the precedence the first preview left underspecified.

### Level 3 — Advanced

```java
package app;

// Two libraries, each with their own Builder type — a realistic
// module-import collision, deliberately constructed here in one file.
module lib.alpha {
    exports alpha.pkg;
}

module lib.beta {
    exports beta.pkg;
}
```

```java
// alpha/pkg/Builder.java
package alpha.pkg;
public class Builder {
    public String describe() { return "alpha Builder"; }
}
```

```java
// beta/pkg/Builder.java
package beta.pkg;
public class Builder {
    public String describe() { return "beta Builder"; }
}
```

```java
// Main.java
import module lib.alpha;
import module lib.beta;
import alpha.pkg.Builder; // explicit import resolves the conflict

void main() {
    Builder b = new Builder(); // resolves to alpha.pkg.Builder — explicit import wins
    System.out.println(b.describe());
}
```

**How to run:** compile the two library modules and `Main.java` together with `javac --enable-preview --release 24 -d out --module-source-path . $(find . -name '*.java')`, then run with `java --enable-preview -p out -m app/Main` (exact multi-module build commands vary by project layout; the key point is the source structure above, not the precise invocation).

This adds the production-flavored hard case: **two different modules**, each exporting a `Builder` type under the same simple name, both brought in via `import module`. Without the explicit `import alpha.pkg.Builder;`, referencing bare `Builder` would be a genuine, refined-rule-defined compile error (an ambiguous reference, not a silent pick of either); with the explicit import present, it resolves unambiguously to `alpha.pkg.Builder`, exactly as the refined precedence rule specifies.

## 6. Walkthrough

Tracing compilation of `Main.java`:

1. The compiler processes `import module lib.alpha;` and `import module lib.beta;`, expanding each into every package its respective module exports — `alpha.pkg` and `beta.pkg` — bringing both `alpha.pkg.Builder` and `beta.pkg.Builder` into scope under the same simple name, `Builder`.
2. It then processes the explicit `import alpha.pkg.Builder;` — a single-type import naming one specific type precisely.
3. When `main` references bare `Builder` in `new Builder()`, the compiler resolves it using this round's refined precedence: an explicit single-type import always outranks anything contributed by a module import, so `Builder` resolves to `alpha.pkg.Builder` without ambiguity, even though `beta.pkg.Builder` is also nominally in scope via `import module lib.beta;`.
4. `new Builder()` constructs an `alpha.pkg.Builder`, and `b.describe()` calls its method, which returns `"alpha Builder"`.
5. Had the explicit `import alpha.pkg.Builder;` line been omitted, referencing bare `Builder` would instead be a compile-time ambiguity error, since nothing would disambiguate between the two module-imported candidates — the refined rule guarantees this fails loudly at compile time rather than silently picking one.

Expected output:
```
alpha Builder
```

## 7. Gotchas & takeaways

> **Gotcha:** the precedence only resolves conflicts between an **explicit** import and a **module** import — two module imports that both export a same-named type remain genuinely ambiguous at any point that name is actually referenced, and must be disambiguated with an explicit single-type import (or a fully qualified reference) exactly as shown above. Adding more module imports doesn't make an ambiguity "go away" on its own; it can only introduce more of them.

- Second preview in Java 24 (JEP 494) — refines [the first preview](0774-module-import-declarations-preview.md)'s ambiguity rules; still requires `--enable-preview`.
- An explicit single-type import always takes precedence over any type a module import would otherwise contribute under the same simple name.
- Two conflicting module imports still require an explicit disambiguating import (or fully qualified name) at any point the shared simple name is actually used — the compiler reports a clear error rather than guessing.
- The core capability — `import module M` expanding to every package `M` exports — is completely unchanged from the first preview.
- When adopting broad module imports in a codebase that also uses precise, deliberate single-type imports, this round's rules ensure the deliberate ones always win, matching what a reader would expect.
