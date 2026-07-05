---
card: java
gi: 86
slug: string-literals
title: String literals
---

## 1. What it is

A `String` literal is a sequence of characters enclosed in double quotes: `"Hello"`. It produces a `String` object whose content is the text between the quotes, with any escape sequences resolved. Unlike primitive literals, `String` literals are objects — instances of `java.lang.String` — but the JVM handles them specially: all identical string literals in the same program share a single object via the **string pool** (interning).

```java
String greeting = "Hello, World!";
String empty    = "";              // valid — zero-length string
String escaped  = "Line1\nLine2"; // contains a newline character
String path     = "C:\\Users\\Alice";  // contains two backslashes
```

`String` is not a primitive type, but it gets special syntax (double-quote literals) and special compiler treatment (constant folding, concatenation with `+`).

## 2. Why & when

String literals are used everywhere — messages, keys, configuration values, SQL fragments, format strings. Understanding the string pool matters for:
- **Performance** — all `"foo"` literals across your entire application share one object; no heap allocation per use.
- **Identity vs equality** — two `String` variables from literals are `==` equal (same pooled object), but `new String("foo")` creates a fresh object and `==` returns `false`. Always use `.equals()` for string comparison.
- **Compile-time constants** — `"foo" + "bar"` is folded to `"foobar"` by the compiler; these constant expressions are also interned.
- **Text blocks** (Java 15+) — `"""..."""` for multi-line literals.

## 3. Core concept

```java
// ---- Basic literals ----
String s1 = "hello";
String s2 = "hello";  // same pooled object as s1
String s3 = new String("hello");  // new object, NOT pooled

System.out.println(s1 == s2);          // true  — same pool entry
System.out.println(s1 == s3);          // false — s3 is a different object
System.out.println(s1.equals(s3));     // true  — same content

// ---- Interning ----
String s4 = s3.intern();
System.out.println(s1 == s4);          // true  — intern() returns the pooled instance

// ---- Compile-time constant folding ----
String a = "hello";
String b = "hel" + "lo";   // constant expression — compiler folds to "hello"
System.out.println(a == b); // true — same pool entry (both are "hello")

String c = "hel";
String d = c + "lo";        // c is a variable — NOT folded at compile time
System.out.println(a == d); // false — d is a new object at runtime

// ---- String immutability ----
String original = "hello";
String upper    = original.toUpperCase();
System.out.println(original);  // hello — unchanged
System.out.println(upper);     // HELLO — new object

// ---- Escape sequences in String literals ----
String tab       = "col1\tcol2\tcol3";
String multiline = "line1\nline2\nline3";
String json      = "{\"name\":\"Alice\",\"age\":30}";
System.out.println(tab);
System.out.println(multiline);
System.out.println(json);

// ---- Text block (Java 15+) ----
String html = """
        <html>
          <body>Hello</body>
        </html>
        """;
System.out.println(html);   // indentation removed up to the closing """

// ---- Concatenation with + ----
String name = "Alice";
int    age  = 30;
String line = "Name: " + name + ", Age: " + age;  // int auto-converted to string
System.out.println(line);
```

## 4. Diagram

<svg viewBox="0 0 700 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="String literal internment: literal pool vs heap, identity ==  vs equality .equals(), compile-time folding vs runtime concatenation">
  <rect x="8" y="8" width="684" height="174" rx="8" fill="#0d1117"/>

  <text x="350" y="25" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">String literal pool vs heap — identity vs equality</text>

  <!-- Pool box -->
  <rect x="16" y="32" width="240" height="134" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="136" y="49" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">String Pool (interned)</text>
  <line x1="26" y1="55" x2="246" y2="55" stroke="#8b949e" stroke-width="0.5"/>
  <rect x="30" y="62" width="190" height="22" rx="3" fill="#0d1117" stroke="#6db33f" stroke-width="0.8"/>
  <text x="125" y="77" fill="#6db33f" font-family="monospace" font-size="9" text-anchor="middle">"hello"</text>
  <rect x="30" y="90" width="190" height="22" rx="3" fill="#0d1117" stroke="#6db33f" stroke-width="0.8"/>
  <text x="125" y="105" fill="#6db33f" font-family="monospace" font-size="9" text-anchor="middle">"world"</text>
  <text x="136" y="130" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">Shared — no allocation per use</text>
  <text x="136" y="143" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">s1 == s2 ↓ both point here</text>
  <text x="136" y="157" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">always use .equals() for content</text>

  <!-- Heap box -->
  <rect x="268" y="32" width="230" height="134" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="383" y="49" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Heap (new String / runtime concat)</text>
  <line x1="278" y1="55" x2="488" y2="55" stroke="#8b949e" stroke-width="0.5"/>
  <rect x="282" y="62" width="200" height="22" rx="3" fill="#0d1117" stroke="#8b949e" stroke-width="0.8"/>
  <text x="382" y="77" fill="#8b949e" font-family="monospace" font-size="9" text-anchor="middle">new String("hello")  ← s3</text>
  <rect x="282" y="90" width="200" height="22" rx="3" fill="#0d1117" stroke="#8b949e" stroke-width="0.8"/>
  <text x="382" y="105" fill="#8b949e" font-family="monospace" font-size="9" text-anchor="middle">c + "lo"  ← d (runtime)</text>
  <text x="383" y="130" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">s1 == s3 → false (different objects)</text>
  <text x="383" y="143" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">s1.equals(s3) → true (same content)</text>
  <text x="383" y="157" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">s3.intern() → pool entry</text>

  <!-- Constant folding box -->
  <rect x="510" y="32" width="174" height="134" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="597" y="49" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">Compile-time folding</text>
  <line x1="520" y1="55" x2="674" y2="55" stroke="#8b949e" stroke-width="0.5"/>
  <text x="520" y="70" fill="#e6edf3" font-size="7.5" font-family="monospace">"hel"+"lo" → "hello"</text>
  <text x="520" y="83" fill="#8b949e" font-size="7.5" font-family="sans-serif">(compile time — pooled)</text>
  <text x="520" y="100" fill="#e6edf3" font-size="7.5" font-family="monospace">c + "lo" → runtime</text>
  <text x="520" y="113" fill="#8b949e" font-size="7.5" font-family="sans-serif">(c is variable — heap)</text>
  <text x="520" y="130" fill="#6db33f" font-size="7.5" font-family="monospace">final String c = "hel";</text>
  <text x="520" y="143" fill="#6db33f" font-size="7.5" font-family="sans-serif">final → constant → pooled</text>
  <text x="520" y="157" fill="#8b949e" font-size="7" font-family="sans-serif">always use .equals() to be safe</text>
</svg>

String literals are pooled; `==` tests object identity (only reliable for pool entries), while `.equals()` tests content and is always the correct choice for comparing strings.

## 5. Runnable example

Scenario: a user-profile cache — stores user names and their display tags as strings, growing from simple string operations, to demonstrating the pool/heap distinction and equality traps, to a full cache that interns frequently reused strings.

### Level 1 — Basic

```java
public class StringLiteralsBasic {
    public static void main(String[] args) {
        String name  = "Alice";
        String role  = "admin";
        String empty = "";

        // String operations
        System.out.println(name.length());              // 5
        System.out.println(name.toUpperCase());          // ALICE
        System.out.println(name.startsWith("Al"));      // true
        System.out.println(name.contains("ice"));       // true
        System.out.println(name + " [" + role + "]");   // Alice [admin]
        System.out.println(empty.isEmpty());            // true

        // String formatting
        String profile = String.format("%-10s  role=%-8s", name, role);
        System.out.println(profile);

        // String is immutable — operations return new objects
        String original = "  hello  ";
        String trimmed  = original.trim();
        System.out.println("[" + original + "]");   // [  hello  ]
        System.out.println("[" + trimmed  + "]");   // [hello]
        System.out.println(original == trimmed);    // false (different object)
    }
}
```

**How to run:** `java StringLiteralsBasic.java`

All `String` methods (`toUpperCase`, `trim`, `startsWith`, etc.) return new `String` objects — they never modify the original. This immutability is fundamental to the string pool working safely: if strings could be mutated, sharing one pool instance would corrupt all references to it. `String.format` behaves like `printf` but returns a `String` instead of printing it.

### Level 2 — Intermediate

Same profile cache: demonstrate the `==` vs `.equals()` trap, compile-time constant folding, and `intern()`.

```java
public class StringLiteralsIntermediate {
    public static void main(String[] args) {
        // Literal strings are pooled — == works here (but don't rely on it)
        String a = "Alice";
        String b = "Alice";
        System.out.println("literal == literal : " + (a == b));         // true
        System.out.println("literal .equals    : " + a.equals(b));      // true

        // new String bypasses the pool
        String c = new String("Alice");
        System.out.println("literal == new     : " + (a == c));         // false
        System.out.println("literal .equals new: " + a.equals(c));      // true

        // Runtime concatenation bypasses the pool
        String first = "Al";
        String last  = "ice";
        String d = first + last;       // runtime concatenation → heap object
        System.out.println("literal == runtime : " + (a == d));         // false
        System.out.println("literal .equals rt : " + a.equals(d));      // true

        // Compile-time folding — both are "Alice" constant
        String e = "Al" + "ice";   // compiler folds to "Alice" → pooled
        System.out.println("literal == fold    : " + (a == e));         // true

        // Intern brings heap string back to pool
        String f = d.intern();
        System.out.println("literal == intern  : " + (a == f));         // true

        // Null safety
        String maybeNull = null;
        System.out.println("\n" + "Alice".equals(maybeNull));  // false — safe
        // maybeNull.equals("Alice");  // NPE!
    }
}
```

**How to run:** `java StringLiteralsIntermediate.java`

`"Al" + "ice"` is a compile-time constant expression — both operands are `String` literals — so the compiler folds it to the single literal `"Alice"`, which is pooled and `==` equal to `a`. By contrast, `first + last` cannot be folded because `first` is a non-final variable; the concatenation happens at runtime and produces a new heap object. `"Alice".equals(maybeNull)` is the safe pattern: putting the known non-null string on the left prevents a `NullPointerException` when the right side might be null.

### Level 3 — Advanced

Same system: use `String.intern()` in a profile store to reduce memory for repeated country codes and role strings, measure the heap saving, and show text-block usage for a multi-line JSON template.

```java
import java.util.*;

public class StringLiteralsAdvanced {

    record Profile(String name, String country, String role) {}

    // Intern frequently repeated strings to reduce heap duplication
    static String intern(String s) {
        return s == null ? null : s.intern();
    }

    public static void main(String[] args) {
        // Simulate loading 1 000 profiles where country and role repeat
        List<Profile> profiles = new ArrayList<>();
        String[] countries = {"US", "UK", "FR", "DE"};
        String[] roles     = {"admin", "user", "moderator"};

        Random rng = new Random(42);
        for (int i = 0; i < 1_000; i++) {
            String name    = "User" + i;
            String country = intern(countries[rng.nextInt(countries.length)]);
            String role    = intern(roles[rng.nextInt(roles.length)]);
            profiles.add(new Profile(name, country, role));
        }

        // All "US" strings are the same pooled object
        long usCount = profiles.stream()
            .filter(p -> p.country() == "US")   // identity compare — safe because interned
            .count();
        System.out.println("US profiles (identity compare on interned): " + usCount);

        // Verify: same object reference for identical interned strings
        String c1 = intern("US");
        String c2 = intern("US");
        System.out.println("interned == interned: " + (c1 == c2));   // true

        // Text block: multi-line JSON template (Java 15+)
        String template = """
                {
                  "name": "%s",
                  "country": "%s",
                  "role": "%s"
                }
                """;

        Profile p = profiles.get(0);
        String json = template.formatted(p.name(), p.country(), p.role());
        System.out.println(json);
    }
}
```

**How to run:** `java StringLiteralsAdvanced.java`

After `intern()`, all `"US"` strings across the list point to the same pooled object, making `p.country() == "US"` (identity comparison) safe and correct — though `.equals()` remains the recommended practice for clarity. The text block `"""..."""` strips the common leading indentation (determined by the least-indented line) and includes a trailing newline if the closing `"""` is on its own line. `.formatted(...)` is equivalent to `String.format(template, ...)` but called as a method on the template string.

## 6. Walkthrough

Execution trace through `StringLiteralsAdvanced.main`:

**Profile creation loop.** For each iteration, `new String("User" + i)` builds a unique name. `countries[rng.nextInt(4)]` returns one of `{"US","UK","FR","DE"}` — all string literals, already pooled. `intern(...)` calls `.intern()` on them, which is effectively a no-op here because they are already pool entries. For 1 000 profiles with 4 country codes, all `"US"` fields point to the single pooled `"US"` object.

**Identity count.** `p.country() == "US"` compares references. Because `p.country()` was interned (and `"US"` in the lambda is a literal — also pooled), they reference the same object. The count matches the number of US profiles.

**Text block.** The compiler strips the common indentation prefix (8 spaces, determined by the closing `"""`'s alignment). The resulting template string has no leading spaces on each line. `.formatted(name, country, role)` substitutes `%s` placeholders. The text block includes a final newline because the closing `"""` is on a new line.

```
String pool after intern("US"):
  Pool entry: "US"
  profiles[0].country ──→ "US" (pool)
  profiles[3].country ──→ "US" (same pool entry)
  "US" literal in lambda ──→ "US" (same pool entry)
  == comparison: all true

Text block indentation stripping:
  Source:
    """
            {           ← 12 spaces
              "name"    ← 14 spaces
            }           ← 12 spaces
            """         ← 16 spaces (determines strip width = 16)
  → strip 16 leading spaces per line
  Result: "{\n  \"name\": ...\n}\n"
```

## 7. Gotchas & takeaways

> **Never use `==` to compare strings.** `==` tests object identity. String literals from the pool happen to be `==` equal, but `new String(...)`, runtime concatenation, method return values, and strings read from files or databases are heap objects, so `==` will return `false` even when the content is identical. Always use `.equals()`.

> **`"literal".equals(variable)` not `variable.equals("literal")`.** Placing the known non-null string on the left prevents `NullPointerException` when the variable might be `null`.

- String literals are pooled (interned) by the JVM; all uses of the same literal share one object.
- Compile-time constant expressions involving only string literals are also folded and pooled.
- `new String("foo")` creates a non-pooled heap object; use `.intern()` to retrieve the pool entry.
- Always use `.equals()` (or `equalsIgnoreCase`, `compareTo`) for string comparison, not `==`.
- `String` is immutable — all transformation methods return new objects; the original is unchanged.
- Text blocks (`"""..."""`, Java 15+) strip common leading indentation and handle embedded newlines without escape sequences.
- `String.format` / `.formatted()` produce formatted strings; `printf` prints them.
