---
card: java
gi: 775
slug: implicitly-declared-classes-instance-main-3rd-preview
title: Implicitly declared classes & instance main methods (3rd preview)
---

## 1. What it is

**Java 23** (JEP 477) is the **third preview** of [implicitly declared classes and instance main methods](0766-implicitly-declared-classes-instance-main-2nd-preview.md), continuing from Java 21's first preview and Java 22's second. The core model is unchanged: a source file can skip `public class Foo { ... }` entirely and just declare a `main` method — static or instance, with or without `String[] args` — at the top level, and the compiler wraps it in an implicit, unnamed class for you. This round further refines the **method-selection algorithm** that decides which candidate `main` method actually gets launched when a file defines more than one, tightening and clarifying edge cases raised during the second preview's feedback period.

## 2. Why & when

Each preview round of this feature has the same underlying goal: let a first program — or a small script, or a `jshell`-style one-off — be as short as `void main() { System.out.println("Hello, World!"); }`, with none of the `public class`, `static`, or `String[] args` ceremony that exists purely for the sake of larger, multi-file programs. The remaining work across preview rounds has mostly been about precisely specifying what happens in less-common situations: a file with both a static and an instance `main`, a file with `main()` and `main(String[])` side by side, or a `main` method that isn't `public`. Each round narrows the ambiguity so tooling (IDEs, `javac`, `java`) and human readers agree, without fail, on exactly which method a given file launches — refining the specification rather than changing what a typical, single-`main` beginner file looks like.

## 3. Core concept

```java
void main() {
    System.out.println("Hello, World!");
}
```

**How to run:** `java --enable-preview --source 23 Hello.java` — no class declaration, no `public static`, no `String[] args`; just a method, launched directly.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="The launch protocol picks one main method among several candidates using a fixed order of preference, refined across three preview rounds" >
  <rect x="20" y="20" width="600" height="36" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="43" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">java SourceFile.java — which main() runs?</text>

  <rect x="40" y="80" width="170" height="50" rx="8" fill="#0f1620" stroke="#79c0ff"/>
  <text x="125" y="102" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">1. instance main()</text>
  <text x="125" y="118" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">no args, preferred</text>

  <rect x="235" y="80" width="170" height="50" rx="8" fill="#0f1620" stroke="#79c0ff"/>
  <text x="320" y="102" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">2. instance main(String[])</text>
  <text x="320" y="118" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">next preference</text>

  <rect x="430" y="80" width="170" height="50" rx="8" fill="#0f1620" stroke="#79c0ff"/>
  <text x="515" y="102" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">3. static main variants</text>
  <text x="515" y="118" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">last resort</text>

  <text x="320" y="165" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">A file with exactly one main() never hits the ambiguity these rules resolve</text>
</svg>

*Selection order matters only when a file defines more than one plausible entry point.*

## 5. Runnable example

Scenario: a small greeting script, growing from a single instance `main()` into a file with multiple candidate entry points, exercising the launch-selection rule directly.

### Level 1 — Basic

```java
void main() {
    System.out.println("Hello, World!");
}
```

**How to run:** `java --enable-preview --source 23 HelloBasic.java`.

One method, no ambiguity: the compiler generates an implicit unnamed top-level class holding this `main`, and `java` launches it directly.

### Level 2 — Intermediate

```java
import java.util.*;

List<String> greetings = new ArrayList<>();

void main() {
    greetings.add("Hello");
    greetings.add("Hola");
    greetings.add("Bonjour");
    for (String g : greetings) {
        System.out.println(g + ", World!");
    }
}
```

**How to run:** `java --enable-preview --source 23 HelloInstance.java`.

The real-world concern added: an **instance field** (`greetings`) alongside `main` — because `main()` here is an *instance* method (no `static`), the implicit class is instantiated (via its implicit no-arg constructor) before `main` runs, so ordinary instance state works exactly as it would in a hand-written class, without ever writing the class declaration.

### Level 3 — Advanced

```java
import java.util.*;

List<String> greetings = new ArrayList<>();

void main() {
    greetings.add("Hello");
    greet();
}

void main(String[] args) {
    for (String lang : args) {
        greetings.add(switch (lang) {
            case "es" -> "Hola";
            case "fr" -> "Bonjour";
            default -> "Hello";
        });
    }
    greet();
}

void greet() {
    for (String g : greetings) {
        System.out.println(g + ", World!");
    }
}
```

**How to run:** `java --enable-preview --source 23 HelloAmbiguous.java es` (JDK 23+). Try running with and without the `es` command-line argument to see which `main` wins.

This adds the production-flavored hard case: the file defines **both** `void main()` and `void main(String[] args)` as candidate entry points. Per the launch protocol's preference order, the **no-argument** `main()` is selected over `main(String[])` regardless of whether command-line arguments were supplied — so even `java ... HelloAmbiguous.java es` runs the parameterless `main()`, and the `es` argument is silently ignored by the launch step (though it would still be visible to code that explicitly reads `args` some other way, which this file doesn't).

## 6. Walkthrough

Tracing `java --enable-preview --source 23 HelloAmbiguous.java es`:

1. The launcher parses `HelloAmbiguous.java`, finds no top-level class declaration, and wraps the file's top-level members — the `greetings` field and the three methods — in an implicit, unnamed class.
2. It scans that class for candidate main methods: `main()` (instance, no args), `main(String[] args)` (instance, with args), and rules out `greet()` (wrong name, not a candidate at all).
3. Following the launch protocol's fixed preference order, an instance `main()` with **no parameters** is preferred over an instance `main(String[])` when both exist — so `main()` is selected as the entry point, and the `es` command-line argument plays no role in selecting which method runs.
4. The launcher instantiates the implicit class via its implicit no-arg constructor, initializing `greetings` to a new empty `ArrayList`.
5. `main()` runs: it adds `"Hello"` to `greetings` and calls `greet()`.
6. `greet()` iterates `greetings` (just `["Hello"]`) and prints `"Hello, World!"`.
7. `main(String[] args)` — the version that would have processed `es` into `"Hola"` — never runs at all for this launch.

Expected output:
```
Hello, World!
```

(Running the *same file* but calling its `main(String[])` some other way — for instance, from a small test harness that instantiates the implicit class and invokes that overload directly via reflection — would instead produce `Hola, World!`, confirming the method itself works correctly; it's only the **automatic launch selection** that always prefers the no-argument `main()`.)

## 7. Gotchas & takeaways

> **Gotcha:** defining both `main()` and `main(String[] args)` in the same implicitly declared class is legal, but only one of them is ever chosen as the automatic launch entry point — and it's always the no-argument one, per the preference order. If a program genuinely needs to read command-line arguments and also wants the file to auto-launch correctly, it should define only `main(String[] args)`, not both.

- Third preview in Java 23 (JEP 477), continuing from Java 21's first preview and Java 22's [second preview](0766-implicitly-declared-classes-instance-main-2nd-preview.md) — still requires `--enable-preview`.
- Core capability unchanged: a source file needs no `public class` wrapper and no `static`/`String[] args` ceremony for a minimal, single-`main` program.
- This round further refines the **selection order** among multiple candidate `main` methods (instance vs. static, with vs. without `String[] args`) for the less-common case of a file defining more than one.
- Instance `main` methods run against a real instance of the implicit class, constructed via its implicit no-arg constructor — instance fields declared at the top level work normally.
- Still a preview feature intended primarily for small programs, scripts, and learning — larger, multi-file, multi-class programs continue to use ordinary top-level class declarations.
