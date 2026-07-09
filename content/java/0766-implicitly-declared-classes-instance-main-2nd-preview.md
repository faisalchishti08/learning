---
card: java
gi: 766
slug: implicitly-declared-classes-instance-main-2nd-preview
title: Implicitly declared classes & instance main (2nd preview)
---

## 1. What it is

**Java 22** (JEP 463) is the **second preview** of [unnamed classes & instance main methods](0752-unnamed-classes-instance-main-methods-preview.md), continuing from the first preview round in Java 21 — and renamed to **"implicitly declared classes and instance main methods"**, a more precise name reflecting that the compiler-synthesized class isn't literally nameless, it's simply not written by the developer. The core simplification carries forward: a source file can skip `class`, `public`, `static`, and `String[] args` and just write `void main() { ... }`. This round refines the rules for **which `main` method a launcher selects** when a class has several candidate signatures, and clarifies how implicitly declared classes interact with imports and the rest of a source file. As with the first round, it requires `--enable-preview`.

## 2. Why & when

The rename itself signals something about the design's maturation: "unnamed class" suggested the class has no name at all, which invited confusion (does it have a name you could reference from elsewhere? can two files each have an "unnamed class"?). "Implicitly declared class" is more accurate — the class exists, and does have a name, it's just that the *developer* didn't write the declaration; the *compiler* filled it in implicitly. Beyond the naming fix, this round refines a genuinely tricky rule: if a class (implicit or explicit) has multiple methods that could plausibly serve as the program's entry point — an instance `void main()`, an instance `void main(String[] args)`, or a traditional `static void main(String[] args)` — the launcher needs an unambiguous, well-specified rule for which one wins, especially once inheritance is involved (an implicitly declared class implicitly extends `Object`, but could a `main` be inherited from a different explicit superclass in more advanced scenarios?). This round's refinement is specifically about locking down that selection rule before the feature is considered stable enough to finalize.

## 3. Core concept

```java
// Entire file — still no class, public, static, or args needed.
void main() {
    System.out.println("Hello from an implicitly declared class!");
}
```

**How to run:** `java --enable-preview --source 22 Hello.java` — functionally the same simplification as the first preview round, now under its clarified name and with a more precisely specified entry-point selection rule.

## 4. Diagram

<svg viewBox="0 0 640 180" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="The feature is renamed from unnamed classes to implicitly declared classes, better reflecting that the compiler names the class rather than leaving it nameless, alongside a clarified rule for selecting among multiple candidate main methods">
  <rect x="20" y="20" width="280" height="50" rx="8" fill="#1c2430" stroke="#8b949e"/>
  <text x="160" y="50" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Java 21: "unnamed class" (1st preview)</text>

  <line x1="300" y1="45" x2="350" y2="45" stroke="#79c0ff" stroke-width="2" marker-end="url(#arrow766)"/>
  <defs><marker id="arrow766" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#79c0ff"/></marker></defs>

  <rect x="360" y="20" width="260" height="50" rx="8" fill="#0f1620" stroke="#79c0ff"/>
  <text x="490" y="45" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">Java 22: "implicitly declared class"</text>

  <text x="320" y="140" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">The class was always named by the compiler — this round's rename says so accurately, and clarifies main-method selection</text>
</svg>

*A more accurate name, plus a locked-down rule for choosing among multiple candidate entry points.*

## 5. Runnable example

Scenario: a small script that grows to have multiple methods that could plausibly serve as an entry point, demonstrating the clarified selection rule.

### Level 1 — Basic

```java
void main() {
    System.out.println("single main method — unambiguous entry point");
}
```

**How to run:** `java --enable-preview --source 22 SingleMain.java` (JDK 22+).

With only one `main` candidate, there's no ambiguity — the launcher runs it directly, identical to the first preview round's behavior.

### Level 2 — Intermediate

```java
void main() {
    System.out.println("no-args main selected when both are present");
}

void main(String[] args) {
    System.out.println("args main — not selected here since a no-args main also exists");
}
```

**How to run:** `java --enable-preview --source 22 TwoMains.java` (with no command-line arguments; JDK 22+).

The real-world concern added: **two** candidate `main` methods exist in the same implicitly declared class. Java 22's clarified rule specifies exactly which one the launcher picks (an instance no-argument `void main()` is preferred over an instance `void main(String[] args)` when both are present, in this round's specification) — behavior that the first preview round hadn't pinned down with the same precision.

### Level 3 — Advanced

```java
import java.util.*;

// A class field and helper method alongside multiple main candidates,
// showing the full implicitly-declared-class feature set together.
List<String> tasks = new ArrayList<>();

void main(String[] args) {
    for (String arg : args) {
        tasks.add(arg);
    }
    if (tasks.isEmpty()) {
        tasks.add("default-task");
    }
    processAll();
}

void processAll() {
    System.out.println("processing " + tasks.size() + " task(s):");
    for (String task : tasks) {
        System.out.println("  - " + task);
    }
}
```

**How to run:** `java --enable-preview --source 22 TaskRunner.java build test deploy`.

This adds the production-flavored hard case: an implicitly declared class with **instance state** (`tasks`), a `main(String[] args)` that actually uses its `args` parameter (populating `tasks` from command-line arguments, falling back to a default when none are given), and a second **helper instance method** (`processAll`) called from `main` — showing the full shape of what an implicitly declared class supports once you go beyond a trivial one-liner: real state, real argument handling, and real method decomposition, all without ever writing an explicit `class` declaration.

## 6. Walkthrough

Tracing `java --enable-preview --source 22 TaskRunner.java build test deploy`:

1. The launcher parses `TaskRunner.java`, finds no explicit `class` declaration, and synthesizes an implicitly declared class to hold the file's field (`tasks`) and two methods (`main`, `processAll`).
2. It identifies `main(String[] args)` as the sole entry-point candidate (no no-argument `main` exists in this file), instantiates the implicit class, and calls `main` as an instance method on that new object, passing `args = ["build", "test", "deploy"]`.
3. Inside `main`, the `for` loop adds each command-line argument to `tasks` (the instance field), giving `tasks = ["build", "test", "deploy"]`. Since `tasks` isn't empty, the `if` branch adding `"default-task"` is skipped.
4. `processAll()` is called — as an instance method call on the same implicit object, so it can see the same `tasks` field that `main` just populated.
5. Inside `processAll`, it prints the count and then each task, one per line.

Expected output:
```
processing 3 task(s):
  - build
  - test
  - deploy
```

Running the same file with **no** arguments (`java --enable-preview --source 22 TaskRunner.java`) would instead populate `tasks` with just `["default-task"]` via the fallback branch, producing:
```
processing 1 task(s):
  - default-task
```

## 7. Gotchas & takeaways

> **Gotcha:** the rename from "unnamed class" to "implicitly declared class" is more than cosmetic — it signals that the class genuinely exists as a real, named class from the JVM's perspective (useful to know if you ever need to interpret a stack trace from one, which will show a real, if compiler-generated, class name). Don't assume "implicitly declared" means "doesn't really exist as a class" — it's ordinary bytecode with an ordinary (if synthesized) name underneath.

- Second preview round, Java 22 — renamed from "unnamed classes" to "implicitly declared classes," with a clarified rule for selecting among multiple candidate `main` methods.
- When multiple `main` candidates exist, this round specifies precisely which one the launcher selects (an instance no-argument `main()` takes precedence over an instance `main(String[] args)`, when both exist).
- Implicitly declared classes fully support instance fields and multiple instance methods — not just a single trivial `main` — they behave as complete, if compiler-named, classes.
- Still a preview — requires `--enable-preview`, and the exact selection rules continued to be refined; treat this as a Java 22 snapshot of an evolving feature (see [unnamed classes & instance main methods (preview)](0752-unnamed-classes-instance-main-methods-preview.md) for the original Java 21 round's caveats, which still apply).
- Best suited to scripts, quick utilities, and teaching examples; real multi-file applications should still use explicit class declarations for clarity at scale.
