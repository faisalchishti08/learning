---
card: java
gi: 789
slug: simple-source-files-instance-main-methods-4th-preview
title: Simple source files & instance main methods (4th preview)
---

## 1. What it is

**Java 24** (JEP 495) is the **fourth preview** of [implicitly declared classes and instance main methods](0775-implicitly-declared-classes-instance-main-3rd-preview.md) — renamed this round to **"Simple Source Files and Instance Main Methods"** to better describe what it actually does. Alongside continuing the no-`public class`, no-`static`, no-`String[] args` simplification, this round adds `java.lang.IO`: a small set of static convenience methods — `IO.println(...)`, `IO.print(...)`, `IO.readln(...)` — that are **automatically accessible** in a simple source file with no import at all, giving beginner programs an even shorter path to console output and input than `System.out.println`.

## 2. Why & when

Three preview rounds had already stripped away the class-declaration and `main`-signature ceremony, but `System.out.println(...)` remained: correct, familiar to experienced developers, but still four extra tokens (`System`, `.out`, `.println`) longer than the concept it expresses ("print this"), and a `System.out`/`System.in` split that offers no symmetry for reading input back. The renamed feature's fourth round tackles that last piece of ceremony directly: `IO.println("Hello, World!")` and `IO.readln("Name: ")` read as close to plain English as Java syntax allows, without needing a `System.out`/`System.in` distinction or an import — because in a simple source file, `java.lang.IO`'s methods are simply *there*, the same way `String` or `Math` always have been. This isn't meant to replace `System.out`/`System.in` in larger programs, but it completes the "as short as possible, as approachable as possible" goal this whole feature has pursued across four rounds, aimed squarely at a learner's very first program and small interactive scripts.

## 3. Core concept

```java
void main() {
    IO.println("Hello, World!"); // no import, no System.out — just IO
}
```

**How to run:** `java --enable-preview --source 24 Hello.java` — the shortest a runnable, output-producing Java program has ever been.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Four rounds of preview progressively remove ceremony: no class declaration, no static main signature, and now no System.out prefix for simple console output" >
  <rect x="20" y="20" width="180" height="45" rx="6" fill="#0f1620" stroke="#8b949e"/>
  <text x="110" y="47" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="monospace">public class Hello {</text>

  <rect x="220" y="20" width="180" height="45" rx="6" fill="#0f1620" stroke="#79c0ff"/>
  <text x="310" y="47" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="monospace">void main() { ... }</text>

  <rect x="420" y="20" width="200" height="45" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="520" y="47" fill="#6db33f" font-size="9" text-anchor="middle" font-family="monospace">IO.println(...)</text>

  <rect x="20" y="90" width="180" height="30" rx="6" fill="#0f1620" stroke="#8b949e"/>
  <text x="110" y="110" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">traditional ceremony</text>

  <rect x="420" y="90" width="200" height="30" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="520" y="110" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">4th preview, Java 24</text>

  <text x="320" y="165" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Each preview round removed one more layer of required ceremony</text>
</svg>

*`IO` closes the gap between "shortest legal Java" and "what a beginner would naturally try to type."*

## 5. Runnable example

Scenario: a simple interactive greeting script, growing from `IO.println` output into `IO.readln` input, then into a small program combining both with ordinary control flow.

### Level 1 — Basic

```java
void main() {
    IO.println("Hello, World!");
}
```

**How to run:** `java --enable-preview --source 24 HelloIO.java` (JDK 24+).

`IO.println` needs no import and no `System.out` prefix — it's simply available, the same way top-level `main` itself needs no enclosing class declaration.

### Level 2 — Intermediate

```java
void main() {
    String name = IO.readln("What's your name? ");
    IO.println("Hello, " + name + "!");
}
```

**How to run:** `java --enable-preview --source 24 GreetIO.java`, then type a name and press Enter when prompted.

The real-world concern added: `IO.readln(prompt)` prints the prompt and reads a line of input from the console in one call, returning it as a `String` — the input-side counterpart to `IO.println`, giving a genuinely interactive script with no `Scanner`, no `System.in`, and no `BufferedReader` boilerplate.

### Level 3 — Advanced

```java
import java.util.*;

void main() {
    List<String> items = new ArrayList<>();

    while (true) {
        String input = IO.readln("Add an item (or press Enter to finish): ");
        if (input.isBlank()) break;
        items.add(input);
    }

    IO.println("---");
    if (items.isEmpty()) {
        IO.println("No items added.");
    } else {
        for (int i = 0; i < items.size(); i++) {
            IO.println((i + 1) + ". " + items.get(i));
        }
        IO.println("Total: " + items.size() + " item(s).");
    }
}
```

**How to run:** `java --enable-preview --source 24 ShoppingListIO.java`, entering a few items and then pressing Enter on an empty line to finish.

This adds the production-flavored hard case: a genuine **interactive loop** — repeatedly prompting with `IO.readln`, accumulating results in an ordinary `ArrayList`, and using `IO.println` for a formatted summary — showing that `IO` composes completely normally with regular control flow, collections, and imports; it removes ceremony around console I/O specifically, without limiting what the rest of the program can do.

## 6. Walkthrough

Tracing `ShoppingListIO.main` for a session where the user enters "milk", "eggs", then an empty line:

1. `main` creates an empty `ArrayList<String>` called `items`.
2. The `while (true)` loop calls `IO.readln("Add an item (or press Enter to finish): ")`, which prints the prompt to the console (without a trailing newline) and blocks waiting for a line of input.
3. The user types `milk` and presses Enter; `IO.readln` returns `"milk"`. Since `"milk".isBlank()` is `false`, it's added to `items`, and the loop repeats.
4. The same happens for `"eggs"` — prompted, read, added.
5. On the third prompt, the user presses Enter with no text; `IO.readln` returns an empty string, `"".isBlank()` is `true`, and `break` exits the loop.
6. `main` prints a separator line, checks that `items` is non-empty, then loops with an index to print each item as a numbered line (`"1. milk"`, `"2. eggs"`), followed by a total count.

Expected console session (user input shown after the prompts):
```
Add an item (or press Enter to finish): milk
Add an item (or press Enter to finish): eggs
Add an item (or press Enter to finish): 
---
1. milk
2. eggs
Total: 2 item(s).
```

## 7. Gotchas & takeaways

> **Gotcha:** `IO`'s automatic availability is specific to **simple source files** using this feature's implicit top-level structure — a traditionally declared `public class Foo { ... }` file does not get `IO` for free and would need `import java.lang.IO;` explicitly (assuming the class is compiled targeting a JDK where `IO` exists at all, since it's still preview API). Don't expect `IO.println(...)` to "just work" the moment you paste it into an ordinary, fully-declared class without the matching import and preview flags.

- Fourth preview in Java 24 (JEP 495), **renamed** from "Implicitly Declared Classes and Instance Main Methods" to "Simple Source Files and Instance Main Methods" — still requires `--enable-preview`.
- New in this round: `java.lang.IO`, with `println`, `print`, and `readln` static methods, automatically available with no import in a simple source file.
- `IO.readln(prompt)` combines printing a prompt and reading a line of console input into a single call, returning the input as a `String`.
- The core simplification from earlier rounds — no class declaration, no `static`, no `String[] args` required — is unchanged; `IO` is an addition, not a replacement for anything.
- Still aimed at small scripts and first programs; `System.out`/`System.in` remain the right choice for larger, conventionally structured applications.
