---
card: java
gi: 752
slug: unnamed-classes-instance-main-methods-preview
title: Unnamed classes & instance main methods (preview)
---

## 1. What it is

**Java 21** (JEP 445) previews a radically simplified entry-point syntax aimed at newcomers and small scripts: a source file no longer needs an explicit `class` declaration, `public`, `static`, or a `String[] args` parameter just to run `main`. A file can now simply contain:

```java
void main() {
    System.out.println("Hello, world!");
}
```

The compiler wraps this in an **unnamed class** implicitly, and `main` can be an **instance method** (no `static` required) with no parameters. Being a preview feature, it requires `--enable-preview` at compile and run time.

## 2. Why & when

The traditional Java "Hello, world" — `public class Main { public static void main(String[] args) { System.out.println("Hello, world!"); } }` — packs four concepts (class declaration, access modifier, static methods, and array parameters) into the very first program a newcomer writes, none of which have anything to do with printing text. That's a genuine barrier: someone learning to program has to either accept several unexplained keywords on faith, or get a mini-lecture on OOP and static dispatch before writing a single meaningful line. Unnamed classes and instance main methods target exactly this: they let a first program, a quick script, or a small teaching example skip the ceremony entirely, while still compiling to completely ordinary Java under the hood (the compiler synthesizes the wrapping class and, if needed, the `static` main automatically). This isn't meant to replace the traditional syntax for real applications — multi-class projects, libraries, and anything with more than one file still want an explicit class — but for the "single file, quick task" case (a build script, a one-off data transformation, a classroom exercise) it removes friction that added no value for that use case.

## 3. Core concept

```java
// Entire file: no class, no `public`, no `static`, no String[] args.
void main() {
    int total = 0;
    for (int i = 1; i <= 10; i++) {
        total += i;
    }
    System.out.println("sum 1..10 = " + total);
}
```

**How to run:** `java --enable-preview --source 21 Sum.java` — the compiler implicitly wraps this in an unnamed class and generates whatever entry-point plumbing is needed to launch it.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="An unnamed-class source file is implicitly wrapped by the compiler into an ordinary class with a synthesized entry point, hiding ceremony the traditional syntax exposes directly">
  <rect x="20" y="20" width="280" height="70" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="160" y="45" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">void main() { ... }</text>
  <text x="160" y="65" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">written by the developer</text>
  <text x="160" y="80" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">(entire file contents)</text>

  <line x1="300" y1="55" x2="360" y2="55" stroke="#79c0ff" stroke-width="2" marker-end="url(#arrow752)"/>
  <defs><marker id="arrow752" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#79c0ff"/></marker></defs>

  <rect x="370" y="20" width="260" height="70" rx="8" fill="#0f1620" stroke="#8b949e"/>
  <text x="500" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">class &lt;unnamed&gt; { void main() {...} }</text>
  <text x="500" y="60" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">synthesized by the compiler,</text>
  <text x="500" y="75" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">launched via the JVM's entry protocol</text>

  <text x="320" y="150" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Ordinary Java underneath — the class and static plumbing still exist, just unwritten</text>
</svg>

*The ceremony doesn't disappear — the compiler just writes it for you.*

## 5. Runnable example

Scenario: a tiny word-frequency counter script, growing from the simplified unnamed-class form into a version with helper methods and fields, showing how far the simplified syntax scales before you'd want a real class.

### Level 1 — Basic

```java
void main() {
    String text = "the quick brown fox jumps over the lazy dog the fox runs";
    String[] words = text.split(" ");
    System.out.println("word count: " + words.length);
}
```

**How to run:** `java --enable-preview --source 21 WordCountBasic.java` (JDK 21+; file name should match a reasonable identifier even though no class name is declared).

This is the simplest possible unnamed-class program: no class, no `static`, no `args` — just a `main` method with a body, doing one small task.

### Level 2 — Intermediate

```java
import java.util.*;

void main() {
    String text = "the quick brown fox jumps over the lazy dog the fox runs";
    Map<String, Integer> counts = countWords(text);
    for (var entry : counts.entrySet()) {
        System.out.println(entry.getKey() + ": " + entry.getValue());
    }
}

Map<String, Integer> countWords(String text) {
    Map<String, Integer> counts = new LinkedHashMap<>();
    for (String word : text.split(" ")) {
        counts.merge(word, 1, Integer::sum);
    }
    return counts;
}
```

**How to run:** `java --enable-preview --source 21 WordCountHelper.java`.

The real-world concern added: a second **instance method**, `countWords`, called directly from `main` with no qualification (`this.` is implicit) — showing that the unnamed class can hold multiple methods, not just a single `main`, and that they call each other exactly as instance methods on any ordinary class would.

### Level 3 — Advanced

```java
import java.util.*;

int minimumLength = 3; // an instance field, implicitly part of the unnamed class

void main() {
    String text = "the quick brown fox jumps over the lazy dog the fox runs";
    Map<String, Integer> counts = countWords(text);
    List<Map.Entry<String, Integer>> sorted = new ArrayList<>(counts.entrySet());
    sorted.sort((a, b) -> b.getValue() - a.getValue());

    System.out.println("top words (length >= " + minimumLength + "):");
    for (var entry : sorted) {
        if (entry.getKey().length() >= minimumLength) {
            System.out.println("  " + entry.getKey() + ": " + entry.getValue());
        }
    }
}

Map<String, Integer> countWords(String text) {
    Map<String, Integer> counts = new LinkedHashMap<>();
    for (String word : text.split(" ")) {
        if (word.length() >= minimumLength) { // reads the instance field
            counts.merge(word, 1, Integer::sum);
        }
    }
    return counts;
}
```

**How to run:** `java --enable-preview --source 21 WordCountAdvanced.java`.

This adds the production-flavored hard case (for this simplified-entry-point feature): an **instance field** (`minimumLength`) shared between `main` and `countWords`, demonstrating that the unnamed class behaves like a genuine object instance with real state, not just a bag of static-looking functions — and showing the natural point where a program starts wanting a real class name and a proper constructor instead of leaning on the unnamed-class shortcut.

## 6. Walkthrough

Tracing `WordCountAdvanced`'s execution:

1. The JVM launches the file. Because there's no explicit class, the compiler's synthesized unnamed class is instantiated, and its `main` instance method is invoked — under the hood, this still goes through the same "find and call an entry point" launch protocol every Java program uses, just with the class-creation and method-invocation details filled in automatically instead of written by hand.
2. `main` builds `text`, then calls `countWords(text)`. Because `countWords` is another instance method on the same (unnamed) class, this call implicitly means `this.countWords(text)` — no qualification needed, exactly like calling a sibling method from within any ordinary class's method.
3. Inside `countWords`, the loop splits `text` on spaces and, for each word, checks `word.length() >= minimumLength` — reading the **instance field** `minimumLength` (value `3`), which is accessible because `countWords` runs on the same object instance that owns the field.
4. Words of length 3 or more get counted via `counts.merge(word, 1, Integer::sum)` (adding 1 to the running count, or inserting 1 if the word is new); shorter words like `"the"`... wait, `"the"` has length 3, so it passes the filter too. Only words strictly shorter than 3 characters would be excluded (none appear in this particular sentence).
5. `countWords` returns the populated map to `main`, which copies its entries into a `List`, sorts that list by count descending using a comparator lambda, then iterates the sorted list, printing each word whose length still satisfies `minimumLength` (redundant here since `countWords` already filtered, but shown for clarity of what a real version might separate into distinct concerns).

Expected output (word counts depend on the exact sentence used):
```
top words (length >= 3):
  the: 3
  fox: 2
  quick: 1
  brown: 1
  jumps: 1
  over: 1
  lazy: 1
  dog: 1
  runs: 1
```

## 7. Gotchas & takeaways

> **Gotcha:** this is a **preview** feature, and — like [string templates](0750-string-templates-preview.md) — its exact rules (and even whether the underscore-based unnamed class stays exactly this shape) continued evolving in JDKs after Java 21. Treat unnamed classes as ideal for scratch files, teaching material, and single-file scripts, not as a foundation to build a real multi-file application on while it's still in preview.

- Requires `--enable-preview` at compile and run time.
- `main` can be an instance method (no `static`) taking zero parameters, in addition to still supporting the traditional `public static void main(String[] args)` signature.
- The compiler synthesizes an actual class around unnamed-class code — nothing magic happens at the bytecode level; the ceremony is generated, not eliminated.
- Great fit for quick scripts, first lessons, and single-file utilities; a real multi-class project still wants explicit class names and structure.
- Combine cautiously with [unnamed patterns & variables](0751-unnamed-patterns-variables-preview.md) — both aim at reducing incidental ceremony, but both are Java 21 previews subject to change before finalization.
