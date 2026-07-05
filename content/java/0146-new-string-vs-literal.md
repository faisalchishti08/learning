---
card: java
gi: 146
slug: new-string-vs-literal
title: new String() vs literal
---

## 1. What it is

A **string literal** (`"text"`) is looked up in (and, if new, added to) the JVM's string pool automatically — identical literal text anywhere in the program shares one object. `new String("text")`, by contrast, always allocates a **brand-new object on the heap**, copying the characters from the literal argument, regardless of whether an identical string already exists in the pool. The two produce strings with identical *content* but different *identity*.

```java
String a = "hello";
String b = "hello";
String c = new String("hello");

System.out.println(a == b);           // true  — both are the SAME pooled object
System.out.println(a == c);           // false — c is a DIFFERENT object, despite equal content
System.out.println(a.equals(c));      // true  — content is identical either way
```

`new String("hello")` is, in effect, "take the pooled `"hello"` and make me my own private copy of it" — useful in only a small number of specific situations, and easy to reach for unnecessarily.

## 2. Why & when

In the vast majority of code, **plain literals are the right choice** — they're simpler, they benefit from pooling, and there is essentially never a correctness reason to prefer `new String("text")` over `"text"` for ordinary string constants:

- **Default: always use literals** (`"text"`) for constant strings — they're pooled automatically and read more simply.
- **`new String(...)` exists mainly for interoperability**, such as constructing a `String` from a `char[]` or `byte[]` (`new String(charArray)`, `new String(bytes, StandardCharsets.UTF_8)`) — those constructors genuinely need `new` because there's no literal syntax for "build a string from this array."
- **A rare, deliberate use of `new String("text")`** is forcing a distinct object identity when you specifically want to demonstrate or test something about `==` vs `.equals()` — outside of teaching or testing, this is almost never a real production need.

The core takeaway is negative: `new String("literal text")` (constructing from an existing literal) offers no benefit over the literal itself, costs an extra unnecessary object, and is widely flagged by linters and style guides as an anti-pattern.

## 3. Core concept

```java
public class NewVsLiteralDemo {
    public static void main(String[] args) {
        // Plain literals: pooled automatically, identical objects
        String x = "cat";
        String y = "cat";
        System.out.println("x == y: " + (x == y)); // true

        // new String(literal): unnecessary — creates a redundant separate object
        String z = new String("cat");
        System.out.println("x == z: " + (x == z)); // false
        System.out.println("x.equals(z): " + x.equals(z)); // true

        // A legitimate use of new String(...): building from a char[] (no literal syntax exists for this)
        char[] letters = { 'd', 'o', 'g' };
        String fromChars = new String(letters);
        System.out.println("fromChars: " + fromChars); // "dog"
    }
}
```

`z` is functionally equivalent in content to `x` and `y`, but is a wasted, separate heap allocation — there was no reason to write `new String("cat")` instead of simply `"cat"`. `fromChars`, however, is a legitimate use: there is no literal syntax for "the string made of these characters," so `new String(char[])` is the correct, necessary tool.

## 4. Diagram

<svg viewBox="0 0 700 175" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="New String versus literal diagram: two literal declarations share one pooled object, while a new String constructed from a literal creates a redundant separate heap object with identical but distinct content." >
  <rect x="8" y="8" width="684" height="159" rx="8" fill="#0d1117"/>
  <text x="350" y="24" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">"cat" (literal) vs. new String("cat")</text>

  <rect x="220" y="45" width="180" height="34" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="310" y="66" fill="#6db33f" font-size="9" text-anchor="middle" font-family="monospace">POOL: "cat"</text>

  <path d="M 130 100 L 260 80" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#a)"/>
  <text x="120" y="112" fill="#79c0ff" font-size="8.5" font-family="monospace">x = "cat"</text>

  <path d="M 130 130 L 280 80" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#a)"/>
  <text x="120" y="140" fill="#79c0ff" font-size="8.5" font-family="monospace">y = "cat"</text>

  <rect x="480" y="90" width="180" height="34" rx="6" fill="#1c2430" stroke="#f85149" stroke-width="1.5" stroke-dasharray="3,2"/>
  <text x="570" y="111" fill="#f85149" font-size="9" text-anchor="middle" font-family="monospace">HEAP: "cat" (z)</text>
  <text x="570" y="140" fill="#f85149" font-size="8" text-anchor="middle" font-family="sans-serif">redundant extra object</text>

  <path d="M 400 62 L 470 100" stroke="#8b949e" stroke-width="1" stroke-dasharray="2,2"/>
  <text x="440" y="80" fill="#8b949e" font-size="7.5" font-family="sans-serif">(copied from, not shared)</text>
</svg>

`x` and `y` share the one pooled object; `z` is a separate, redundant copy that exists only because `new` was used unnecessarily.

## 5. Runnable example

Scenario: parsing a fixed-width record format where each field is extracted as raw characters — starting with a basic legitimate use of `new String(char[])`, then adding a case that mistakenly uses `new String("literal")` for a constant, then hardening the parser to only use `new String(...)` where actually necessary (from arrays), using literals everywhere else.

### Level 1 — Basic

```java
public class FieldParseBasic {
    public static void main(String[] args) {
        char[] record = { 'A', 'L', 'I', 'C', 'E', '0', '3', '0' }; // name(5) + age(3), fixed-width

        char[] nameChars = new char[5];
        System.arraycopy(record, 0, nameChars, 0, 5);
        String name = new String(nameChars); // legitimate: building a String from a char[]

        System.out.println("Name: " + name);
    }
}
```

**How to run:** `java FieldParseBasic.java`

`new String(nameChars)` is necessary here: `nameChars` is a `char[]`, not a string literal, and there is no literal syntax that could produce a `String` directly from an array's contents — this is exactly the case where `new String(...)` is the right, in fact the *only*, tool.

### Level 2 — Intermediate (showing the unnecessary version, then fixing it)

Same parser, now also extracting the age field — first written with an unnecessary `new String("literal")` for a constant label (a mistake), then corrected to use a plain literal instead.

```java
public class FieldParseIntermediate {
    public static void main(String[] args) {
        char[] record = { 'A', 'L', 'I', 'C', 'E', '0', '3', '0' };

        char[] nameChars = new char[5];
        System.arraycopy(record, 0, nameChars, 0, 5);
        String name = new String(nameChars); // legitimate: from a char[]

        char[] ageChars = new char[3];
        System.arraycopy(record, 5, ageChars, 0, 3);
        String ageText = new String(ageChars); // also legitimate: from a char[]
        int age = Integer.parseInt(ageText);

        String label = new String("Parsed record"); // UNNECESSARY — should just be a literal
        // Better: String label = "Parsed record";

        System.out.println(label + " -> Name: " + name + ", Age: " + age);
    }
}
```

**How to run:** `java FieldParseIntermediate.java`

`label` demonstrates the anti-pattern directly: `"Parsed record"` is already a complete literal, so wrapping it in `new String(...)` creates a needless second copy on the heap with no benefit whatsoever — it doesn't change the program's output at all, only wastes an allocation. `name` and `ageText`, in contrast, are genuinely necessary uses of `new String(char[])`, since neither originates from literal text.

### Level 3 — Advanced

Same fixed-width parser, now cleaned up to use `new String(...)` **only** where genuinely required (constructing from `char[]` data extracted from the record), with every constant string in the program written as a plain literal — a small parser that correctly demonstrates the distinction throughout.

```java
public class FieldParseAdvanced {

    record ParsedField(String name, int age) {}

    static ParsedField parse(char[] record) {
        if (record.length != 8) {
            throw new IllegalArgumentException("Invalid record length: " + record.length); // literal, not new String(...)
        }

        char[] nameChars = new char[5];
        System.arraycopy(record, 0, nameChars, 0, 5);
        String name = new String(nameChars); // necessary: built from a char[]

        char[] ageChars = new char[3];
        System.arraycopy(record, 5, ageChars, 0, 3);
        int age = Integer.parseInt(new String(ageChars)); // necessary: built from a char[], used immediately

        return new ParsedField(name, age);
    }

    public static void main(String[] args) {
        char[][] records = {
            { 'A', 'L', 'I', 'C', 'E', '0', '3', '0' },
            { 'B', 'O', 'B', ' ', ' ', '0', '2', '5' }
        };

        for (char[] record : records) {
            ParsedField field = parse(record);
            System.out.println("Name: [" + field.name() + "], Age: " + field.age());
        }
    }
}
```

**How to run:** `java FieldParseAdvanced.java`

Every `new String(...)` call in this version is constructing from a `char[]` — `nameChars` or `ageChars` — which is the one situation where `new` is actually required, since neither array is literal text. Every other string in the program (the exception message, the print labels `"Name: ["`, `", Age: "`) is a plain literal, exactly as it should be, with no unnecessary heap allocations anywhere.

## 6. Walkthrough

Trace `parse(new char[]{ 'B', 'O', 'B', ' ', ' ', '0', '2', '5' })`:

**Length check.** `record.length` is `8`, matching the expected length, so the guard clause does not throw.

**Name extraction.** `nameChars = new char[5]`; `System.arraycopy(record, 0, nameChars, 0, 5)` copies the first 5 characters (`'B'`, `'O'`, `'B'`, `' '`, `' '`) into `nameChars`. `new String(nameChars)` then builds a genuine new `String` object, `"BOB  "` (with two trailing spaces), from those raw characters — there is no way to write this as a literal, since the characters came from a computed array slice, not fixed source text.

**Age extraction.** `ageChars = new char[3]`; `System.arraycopy(record, 5, ageChars, 0, 3)` copies the last 3 characters (`'0'`, `'2'`, `'5'`). `new String(ageChars)` builds `"025"`, and `Integer.parseInt("025")` parses it to the `int` `25` (leading zero is fine for `parseInt`).

```
record = {B,O,B,' ',' ',0,2,5}
nameChars = {B,O,B,' ',' '}  -> new String(nameChars) = "BOB  "
ageChars  = {0,2,5}          -> new String(ageChars)  = "025"  -> parseInt -> 25
result: ParsedField(name="BOB  ", age=25)
```

**Final output.** `main` prints `"Name: [ALICE], Age: 30"` for the first record and `"Name: [BOB  ], Age: 25"` for the second — the trailing spaces in `"BOB  "` are visible inside the brackets, showing exactly what characters were copied from the fixed-width field, unpadded.

## 7. Gotchas & takeaways

> **`new String("literal text")` is never necessary and is widely considered an anti-pattern** — it creates a redundant heap object with identical content to the pooled literal, defeating the pool's memory-saving purpose for no benefit. Static analysis tools (and many style guides) flag this pattern specifically.

> **`new String(char[])` and `new String(byte[], Charset)` are genuinely necessary and idiomatic** — these construct a `String` from data that has no literal representation. Don't let "avoid `new String(...)` for literals" become "never use the `String` constructor at all" — the constructor exists precisely for these array-based cases.

- Prefer plain literals (`"text"`) for any fixed, constant string — they're automatically pooled and simpler to read.
- Reserve `new String(...)` for building a string from a `char[]` or `byte[]`, where no literal syntax is available.
- `new String("already a literal")` creates a functionally redundant object — identical content, wasted allocation, no correctness benefit.
- Regardless of how a string was constructed, always compare its *content* with `.equals()`, never object identity with `==`.
