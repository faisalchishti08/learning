---
card: java
gi: 393
slug: static-imports
title: Static imports
---

## 1. What it is

A **static import** (`import static SomeClass.someMember;`), introduced in Java 5, lets you reference a class's `static` members — fields and methods — directly by their plain name, without prefixing them with the class name every time. Instead of writing `Math.sqrt(x)` and `Math.PI` throughout a file, a static import (`import static java.lang.Math.sqrt; import static java.lang.Math.PI;`) lets you write simply `sqrt(x)` and `PI`. You can also static-import everything from a class at once with a wildcard: `import static java.lang.Math.*;`.

## 2. Why & when

Some classes are essentially collections of constants and utility functions meant to be used as if they were part of the language itself — `Math`, `Objects`, or a project's own `Constants` class. Repeating the class name prefix (`Math.max(Math.min(a, b), c)`) adds visual noise without adding real information, especially in code (mathematical formulas, unit test assertions) that already reads naturally as a sequence of function calls. Static imports remove that prefix where it's genuinely just clutter.

The trade-off is that static imports remove an explicit signal of *where* a name comes from — reading `assertEquals(expected, actual)` without an import statement visible nearby, you can't immediately tell if `assertEquals` is a local method or came from `org.junit.jupiter.api.Assertions`. Because of this, static imports are best reserved for very well-known, narrowly-scoped utility methods (test assertion libraries, `Math` functions, a project's own well-understood constants) — overusing them broadly, especially with wildcard imports of unfamiliar classes, makes code genuinely harder to read, not easier.

## 3. Core concept

```java
import static java.lang.Math.sqrt;
import static java.lang.Math.pow;

public class StaticImportDemo {
    public static void main(String[] args) {
        double a = 3, b = 4;
        double hypotenuse = sqrt(pow(a, 2) + pow(b, 2)); // no "Math." prefix needed anywhere
        System.out.println("Hypotenuse: " + hypotenuse);
    }
}
```

**How to run:** `java StaticImportDemo.java`

`import static java.lang.Math.sqrt;` and `import static java.lang.Math.pow;` bring those two specific static methods into scope by their plain names. `sqrt(pow(a, 2) + pow(b, 2))` reads almost like ordinary mathematical notation — the Pythagorean theorem — with no `Math.` prefix cluttering the formula.

## 4. Diagram

<svg viewBox="0 0 640 140" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="a static import brings a specific static member into scope under its plain name, removing the need to prefix it with the declaring class each time it is used">
  <rect x="8" y="8" width="624" height="124" rx="8" fill="#0d1117"/>
  <text x="20" y="30" fill="#e6edf3" font-size="11">import static java.lang.Math.sqrt;</text>

  <rect x="30" y="45" width="260" height="35" rx="6" fill="#1c2430" stroke="#8b949e"/>
  <text x="160" y="67" fill="#8b949e" font-size="10" text-anchor="middle">Math.sqrt(x) -- without import</text>

  <rect x="330" y="45" width="260" height="35" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="460" y="67" fill="#6db33f" font-size="10" text-anchor="middle">sqrt(x) -- with static import</text>

  <text x="20" y="110" fill="#8b949e" font-size="10">Same method, same behavior -- the import only affects how it's written, not what it does.</text>
</svg>

## 5. Runnable example

Scenario: a small set of unit-style assertions, evolved from a version with fully-qualified assertion calls, through static-importing the assertion methods (mirroring how real test frameworks like JUnit are conventionally used), to a version showing the readability cost of an *overused*, unfamiliar wildcard static import.

### Level 1 — Basic

```java
public class AssertionsQualified {
    static void assertEquals(Object expected, Object actual) {
        if (!expected.equals(actual)) {
            throw new AssertionError("Expected " + expected + " but got " + actual);
        }
    }

    public static void main(String[] args) {
        AssertionsQualified.assertEquals(4, 2 + 2); // fully qualified, even within its own class
        System.out.println("Assertion passed.");
    }
}
```

**How to run:** `java AssertionsQualified.java`

Even calling `assertEquals` from within its own defining class doesn't require the `AssertionsQualified.` prefix in ordinary Java — this example writes it out explicitly only to make the contrast with the next levels clearer; the real motivating case for static imports is calling a method that genuinely lives in a *different* class.

### Level 2 — Intermediate

```java
public class AssertHelpers {
    static void assertEquals(Object expected, Object actual) {
        if (!expected.equals(actual)) {
            throw new AssertionError("Expected " + expected + " but got " + actual);
        }
    }

    static void assertTrue(boolean condition) {
        if (!condition) {
            throw new AssertionError("Expected condition to be true");
        }
    }
}
```

```java
import static AssertHelpers.assertEquals;
import static AssertHelpers.assertTrue;

public class CalculatorTest {
    static int add(int a, int b) { return a + b; }

    public static void main(String[] args) {
        assertEquals(4, add(2, 2));   // no "AssertHelpers." prefix -- reads like a real test framework
        assertTrue(add(2, 2) == 4);
        System.out.println("All assertions passed.");
    }
}
```

**How to run:** save both classes in separate files (`AssertHelpers.java` and `CalculatorTest.java`) in the same directory, then `java CalculatorTest.java`

Static-importing `assertEquals` and `assertTrue` from a separate `AssertHelpers` class lets `CalculatorTest` read almost exactly like code using a real test framework such as JUnit (`import static org.junit.jupiter.api.Assertions.assertEquals;`) — this specific, narrow use of static imports (well-known, purpose-built assertion methods) is exactly the pattern the feature is best suited for.

### Level 3 — Advanced

```java
import static java.lang.Math.*; // wildcard static import -- convenient here, but a double-edged sword

public class GeometryOverused {
    public static void main(String[] args) {
        double radius = 5;
        double circleArea = PI * pow(radius, 2); // PI and pow both from Math -- clear enough in context
        System.out.println("Circle area: " + circleArea);

        // Contrast: imagine this file ALSO had "import static SomeObscureLibrary.*;"
        // A reader encountering an unfamiliar bare name like process(x) would have NO
        // easy way to tell, just from this file, which of potentially several
        // wildcard-imported classes it actually came from -- this is the real cost
        // of overusing static imports, especially wildcard ones, on unfamiliar classes.
        System.out.println("min(3, 7) = " + min(3, 7)); // still clearly Math, since Math is well-known
    }
}
```

**How to run:** `java GeometryOverused.java`

`import static java.lang.Math.*;` is a reasonably safe wildcard static import specifically because `Math` is a small, extremely well-known standard class — every Java developer recognises `PI`, `pow`, and `min` as `Math` members on sight. The comment illustrates the real risk: wildcard-importing an *unfamiliar* or large custom utility class would leave a reader unable to tell, just by looking at a bare method call, which class it actually came from — a genuine readability cost that outweighs the minor convenience for anything less universally recognisable than `Math`.

## 6. Walkthrough

Execution starts in `main` (Level 2's `CalculatorTest`). `assertEquals(4, add(2, 2))` is evaluated: first, `add(2, 2)` runs — a local static method in `CalculatorTest` itself, returning `4`. Then `assertEquals(4, 4)` is called; because of `import static AssertHelpers.assertEquals;`, this bare name resolves to `AssertHelpers.assertEquals(Object, Object)`. Inside it, `4.equals(4)` (both autoboxed to `Integer`) is `true`, so `!expected.equals(actual)` is `false`, and the method returns normally without throwing.

`assertTrue(add(2, 2) == 4)` runs next: `add(2, 2)` returns `4` again, `4 == 4` is `true`, so `assertTrue(true)` is called — resolved via `import static AssertHelpers.assertTrue;` to `AssertHelpers.assertTrue(boolean)`. Inside, `!condition` is `!true`, which is `false`, so the method returns normally without throwing.

Since neither assertion threw an `AssertionError`, execution reaches `System.out.println("All assertions passed.")`, which prints that message.

If either assertion had failed instead — say, if `add` had a bug and returned the wrong value — the corresponding `AssertionError` would propagate up out of `main` (since nothing here catches it), terminating the program with a stack trace, exactly like a failing test in a real test framework.

Expected output:
```
All assertions passed.
```

## 7. Gotchas & takeaways

> Static imports remove the visual cue of which class a name comes from — this is a real trade-off, not a free convenience. Reserve them for extremely well-known, narrowly-purposed classes (`Math`, test assertion libraries, a small, well-understood project constants class); avoid wildcard-importing large or unfamiliar utility classes, since it makes code genuinely harder for a reader to trace.

- `import static ClassName.memberName;` brings one specific static member into scope under its plain name; `import static ClassName.*;` brings in every static member of that class at once.
- The feature exists to remove genuinely unnecessary visual clutter from code that reads naturally as a sequence of well-known utility calls — mathematical formulas, and test assertions being the two most common, well-accepted use cases.
- The cost is losing an explicit "this comes from that class" signal at the call site — a real readability trade-off that's worth it only when the imported names are widely and immediately recognisable.
- Prefer specific static imports (`import static Math.sqrt;`) over wildcard ones (`import static Math.*;`) when only a couple of members are actually used, keeping the import list itself a clear inventory of what's been brought into scope.
- IDEs typically warn about or flag unused static imports and can auto-organize them — leaning on that tooling helps keep static imports from silently accumulating clutter of their own over time.
