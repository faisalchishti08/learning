# Java Strings

## Overview

Strings are one of the most used types in Java. Unlike primitives, `String` is a class — but it's treated specially by the compiler (literals, `+` operator, string pool). Understanding immutability, the pool, and method behavior prevents common bugs and performance problems.

---

## 1. String Immutability

### What is it

`String` objects **cannot be changed** after creation. Any operation that "modifies" a String actually creates a new String object. The original is untouched.

### Visual Diagram — Immutability

```
String s = "hello";     s ──► [hello]  (in pool)
s = s + " world";       s ──► [hello world]  (NEW object)
                               [hello] still exists in pool until GC

Before:   s ──► "hello"
After:    s ──► "hello world"
                 (new object)
                 
Original "hello" is NOT modified. s just points to a new object.
```

### Example 1 — Immutability Proof

```java
public class StringImmutability {
    public static void main(String[] args) {
        String original = "hello";
        String modified = original.toUpperCase();

        System.out.println(original); // hello (unchanged!)
        System.out.println(modified); // HELLO (new object)
        System.out.println(original == modified); // false (different objects)

        // Every method returns a new String
        String s = "  Java  ";
        String trimmed = s.strip();
        System.out.println(s);       // "  Java  " (unchanged)
        System.out.println(trimmed); // "Java"
    }
}
```

**What this does:** `toUpperCase()`, `strip()`, and all String methods return new String objects. The original remains unchanged. This is why `s.toUpperCase()` without assigning the result does nothing useful.

### Example 2 — Why Immutability Matters

```java
public class ImmutabilityBenefits {
    static String cached = "config-value";

    public static void main(String[] args) {
        // Thread safety: multiple threads can share a String safely
        // because no thread can modify it

        // HashMap key safety: if String were mutable, hashCode could change
        // after insertion, making the key unfindable
        java.util.Map<String, Integer> map = new java.util.HashMap<>();
        String key = "name";
        map.put(key, 42);
        // If key could be mutated here, map.get(key) might fail
        System.out.println(map.get(key)); // 42 — safe because String is immutable

        // Security: passwords passed as Strings can't be changed by called methods
        authenticate("secret123");
        // Caller's string "secret123" is guaranteed unchanged after the call
    }

    static void authenticate(String password) {
        // Can't corrupt the caller's password string
    }
}
```

**What this does:** Immutability makes Strings safe to share across threads, safe as Map keys, and safe for security-sensitive data. These are the reasons Java's designers chose immutability.

> ⚠️ **Pitfall:** `String s = "hello"; s.toUpperCase();` — the result is LOST! You must do `s = s.toUpperCase();`

---

## 2. String Pool and Interning

### What is it

The JVM maintains a **string pool** (part of heap / metaspace) — a cache of String literals. When you write `"hello"` in code, the JVM checks the pool; if `"hello"` already exists, it returns the same object. `new String("hello")` bypasses the pool and always creates a new object.

### Visual Diagram — String Pool

```
Heap:
┌─────────────────────────────────────────────────────┐
│  String Pool                  │  Regular Heap        │
│  ┌───────────────────┐        │  ┌────────────────┐  │
│  │ "hello"  ◄─── a  │        │  │ "hello"  ◄─ c  │  │
│  │ "world"  ◄─── b  │        │  └────────────────┘  │
│  └───────────────────┘        │                      │
└─────────────────────────────────────────────────────┘

String a = "hello";           // from pool
String b = "world";           // from pool
String c = new String("hello"); // new object, NOT from pool
a == b → false  (different objects)
a == a → true   (same object)
a == c → false  (c is outside pool)
a.equals(c) → true  (same content)
```

### Example 1 — Pool Behavior

```java
public class StringPool {
    public static void main(String[] args) {
        String a = "hello";
        String b = "hello";
        String c = new String("hello");
        String d = c.intern(); // puts c into pool, returns pooled reference

        System.out.println(a == b);      // true  — same pooled object
        System.out.println(a == c);      // false — c is NOT pooled
        System.out.println(a.equals(c)); // true  — same content
        System.out.println(a == d);      // true  — d IS the pooled object

        // Concatenated literals are also pooled at compile time:
        String e = "hel" + "lo";         // compiler folds to "hello"
        System.out.println(a == e);      // true

        // Runtime concatenation is NOT pooled:
        String f = "hel";
        String g = f + "lo";             // computed at runtime
        System.out.println(a == g);      // false
    }
}
```

**What this does:** Literal strings and compile-time constant expressions are automatically pooled. Runtime computations create new heap objects. `.intern()` forces a String into the pool and returns the pooled reference.

### Dry Run — == vs equals

```java
String s1 = "Java";
String s2 = "Java";
String s3 = new String("Java");
```

| Expression      | Result | Reason                                         |
|-----------------|--------|------------------------------------------------|
| `s1 == s2`      | true   | both point to same pooled object               |
| `s1 == s3`      | false  | s3 is a new heap object outside pool           |
| `s1.equals(s3)` | true   | compares character content: "Java" == "Java"   |
| `s1.equals(null)` | false | equals handles null without NPE               |
| `null == s1`    | false  | reference comparison, null ≠ any object        |

> ⚠️ **Pitfall:** ALWAYS use `.equals()` to compare String values. `==` only checks if they are the exact same object — not if they have the same content.

---

## 3. String vs StringBuilder vs StringBuffer

### What is it

Three ways to work with character sequences:
- **String** — immutable, thread-safe by nature, every "change" creates new object
- **StringBuilder** — mutable, NOT thread-safe, fast for single-threaded string building
- **StringBuffer** — mutable, thread-safe (all methods synchronized), slower than StringBuilder

### Visual Diagram — When to Use

```
String:        "ABC" ──── immutable ──── safe to share, slow to modify
StringBuilder: [A|B|C|_|_] ──── mutable buffer ──── fast, single-threaded
StringBuffer:  [A|B|C|_|_] ──── mutable buffer + lock ──── thread-safe, slower

Use String:        for values that don't change; method parameters; map keys
Use StringBuilder: when building strings in loops or single-threaded code
Use StringBuffer:  rarely; only when mutable string shared between threads
```

### Example 1 — String Concatenation Performance Problem

```java
public class StringVsBuilder {
    public static void main(String[] args) {
        // BAD: String concatenation in loop
        // Creates 10,000 intermediate String objects!
        long start1 = System.nanoTime();
        String bad = "";
        for (int i = 0; i < 10_000; i++) {
            bad += "x"; // new String object each iteration
        }
        long end1 = System.nanoTime();

        // GOOD: StringBuilder
        long start2 = System.nanoTime();
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < 10_000; i++) {
            sb.append("x"); // modifies internal buffer
        }
        String good = sb.toString();
        long end2 = System.nanoTime();

        System.out.println("String concat: " + (end1 - start1) / 1_000_000 + "ms");
        System.out.println("StringBuilder: " + (end2 - start2) / 1_000_000 + "ms");
        // StringBuilder is typically 100x+ faster for large loops
    }
}
```

**What this does:** Each `+=` on a String creates a new String object. For N iterations, N intermediate objects are created and immediately discarded. StringBuilder uses an internal char array that grows as needed.

### Example 2 — StringBuilder Internal Buffer

```java
public class StringBuilderDetails {
    public static void main(String[] args) {
        StringBuilder sb = new StringBuilder(8); // initial capacity 8
        System.out.println("Capacity: " + sb.capacity()); // 8
        System.out.println("Length: " + sb.length());     // 0

        sb.append("Hello");
        System.out.println("After 'Hello':");
        System.out.println("Capacity: " + sb.capacity()); // still 8
        System.out.println("Length: " + sb.length());     // 5

        sb.append(" World!!");    // length becomes 13, exceeds capacity 8
        System.out.println("After ' World!!':");
        System.out.println("Capacity: " + sb.capacity()); // 18 (grows: 8*2 + 2)
        System.out.println("Length: " + sb.length());     // 13

        System.out.println(sb.toString()); // Hello World!!
    }
}
```

**What this does:** StringBuilder has a capacity (allocated buffer size) and a length (actual content size). When content exceeds capacity, the buffer grows automatically (typically doubles + 2). Pre-sizing with `new StringBuilder(expectedSize)` avoids reallocations.

### Dry Run — StringBuilder append chain

```java
StringBuilder sb = new StringBuilder();
sb.append("Java")
  .append(" ")
  .append("21");
```

| Step | Method call        | Buffer state     | Length |
|------|--------------------|------------------|--------|
| init | `new StringBuilder()`| `[]`            | 0      |
| 1    | `.append("Java")`  | `[Java]`         | 4      |
| 2    | `.append(" ")`     | `[Java ]`        | 5      |
| 3    | `.append("21")`    | `[Java 21]`      | 7      |
| 4    | `.toString()`      | `"Java 21"`      | —      |

---

## 4. Key String Methods

### What is it

String has ~80+ methods. Here are the most important ones with examples.

### Example 1 — Inspection Methods

```java
public class StringInspection {
    public static void main(String[] args) {
        String s = "  Hello, World!  ";

        System.out.println(s.length());             // 18
        System.out.println(s.charAt(7));            // H (index 0-based)
        System.out.println(s.indexOf("o"));         // 6 (first occurrence)
        System.out.println(s.lastIndexOf("o"));     // 10 (last occurrence)
        System.out.println(s.indexOf("xyz"));       // -1 (not found)
        System.out.println(s.contains("World"));    // true
        System.out.println(s.startsWith("  H"));    // true
        System.out.println(s.endsWith("!  "));      // true
        System.out.println(s.isEmpty());            // false
        System.out.println("".isEmpty());           // true
        System.out.println("  ".isEmpty());         // false (not empty — has spaces)
        System.out.println("  ".isBlank());         // true  [Java 11+] — only whitespace
        System.out.println(s.substring(2, 7));      // Hello (index 2 inclusive to 7 exclusive)
        System.out.println(s.substring(9));         // World!  (from 9 to end)
    }
}
```

**What this does:** Core inspection methods. `indexOf` returns -1 if not found. `substring(start, end)` is exclusive of end. `isEmpty()` checks length==0; `isBlank()` [Java 11+] checks all whitespace.

### Example 2 — Transformation Methods

```java
public class StringTransform {
    public static void main(String[] args) {
        String s = "  Hello, World!  ";

        System.out.println(s.toUpperCase());         // "  HELLO, WORLD!  "
        System.out.println(s.toLowerCase());         // "  hello, world!  "
        System.out.println(s.trim());                // "Hello, World!" (removes ASCII whitespace)
        System.out.println(s.strip());               // "Hello, World!" [Java 11+] (Unicode-aware)
        System.out.println(s.stripLeading());        // "Hello, World!  " [Java 11+]
        System.out.println(s.stripTrailing());       // "  Hello, World!" [Java 11+]
        System.out.println(s.replace(",", ";"));     // "  Hello; World!  "
        System.out.println(s.replaceAll("\\s+", "_")); // "__Hello,_World!__" (regex)
        System.out.println(s.replaceFirst("l", "L")); // "  HeLlo, World!  "

        // [Java 11+]
        System.out.println("ha".repeat(3));          // hahaha
        System.out.println("line1\nline2\nline3".lines().count()); // 3

        // [Java 12+]
        System.out.println("hello".indent(2));       // "  hello\n" (adds spaces + newline)
        String transformed = "hello".transform(str -> str.toUpperCase() + "!");
        System.out.println(transformed);             // HELLO!
    }
}
```

**What this does:** `trim()` removes ASCII whitespace (chars ≤ 32). `strip()` is the modern Unicode-aware version. `replaceAll` takes a regex; `replace()` takes a literal string. `transform()` [Java 12+] applies a function to produce a result.

### Example 3 — Splitting and Joining

```java
import java.util.Arrays;

public class SplitJoin {
    public static void main(String[] args) {
        // split
        String csv = "Alice,Bob,Charlie,Dave";
        String[] names = csv.split(",");
        System.out.println(Arrays.toString(names)); // [Alice, Bob, Charlie, Dave]
        System.out.println(names.length);           // 4

        // split with limit
        String[] limited = csv.split(",", 2);       // max 2 parts
        System.out.println(Arrays.toString(limited)); // [Alice, Bob,Charlie,Dave]

        // split on regex
        String data = "one  two   three"; // multiple spaces
        String[] words = data.split("\\s+"); // one or more whitespace
        System.out.println(Arrays.toString(words)); // [one, two, three]

        // join [Java 8+]
        String joined = String.join(", ", "Alice", "Bob", "Charlie");
        System.out.println(joined); // Alice, Bob, Charlie

        String joined2 = String.join("-", names); // from array
        System.out.println(joined2); // Alice-Bob-Charlie-Dave

        // join collection
        java.util.List<String> list = java.util.List.of("a", "b", "c");
        String joined3 = String.join("|", list);
        System.out.println(joined3); // a|b|c
    }
}
```

**What this does:** `split()` takes a regex. Watch out: `split(".")` splits on every char (`.` is regex "any char") — use `split("\\.")` for literal dot. `String.join()` is a static factory that concatenates with a delimiter.

### Example 4 — Comparison and Formatting

```java
public class StringComparison {
    public static void main(String[] args) {
        String a = "Apple";
        String b = "Banana";
        String c = "apple";

        System.out.println(a.equals(b));               // false
        System.out.println(a.equalsIgnoreCase(c));     // true
        System.out.println(a.compareTo(b));            // negative (A < B alphabetically)
        System.out.println(a.compareToIgnoreCase(c));  // 0 (equal ignoring case)

        // Formatting
        String formatted = String.format("Name: %-10s Age: %3d", "Alice", 25);
        System.out.println(formatted); // Name: Alice      Age:  25

        // [Java 15+] formatted() instance method (same as String.format)
        String s = "%-10s: %d".formatted("Score", 100);
        System.out.println(s); // Score     : 100

        // valueOf — converts other types to String
        System.out.println(String.valueOf(42));      // "42"
        System.out.println(String.valueOf(3.14));    // "3.14"
        System.out.println(String.valueOf(true));    // "true"
        System.out.println(String.valueOf(null));    // "null" (safe, no NPE)

        // char array → String
        char[] chars = {'J', 'a', 'v', 'a'};
        System.out.println(new String(chars));       // Java
        System.out.println(String.valueOf(chars));   // Java
    }
}
```

**What this does:** `compareTo` returns negative/zero/positive based on lexicographic ordering. `String.format` uses printf-style formatting. `String.valueOf()` safely converts any type — even null — to String.

---

## 5. StringBuilder Methods

### What is it

StringBuilder provides a mutable string buffer with full editing capability.

### Example 1 — Building and Editing

```java
public class StringBuilderMethods {
    public static void main(String[] args) {
        StringBuilder sb = new StringBuilder("Hello World");

        // Basic operations
        sb.append("!");             // append to end
        sb.insert(5, ",");          // insert at index 5
        System.out.println(sb);     // Hello, World!

        sb.delete(5, 6);            // delete from 5 (inclusive) to 6 (exclusive)
        System.out.println(sb);     // Hello World!

        sb.deleteCharAt(11);        // delete '!'
        System.out.println(sb);     // Hello World

        sb.replace(6, 11, "Java");  // replace "World" with "Java"
        System.out.println(sb);     // Hello Java

        sb.reverse();
        System.out.println(sb);     // avaJ olleH

        // Chaining
        String result = new StringBuilder()
            .append("Java")
            .append(" ")
            .append(21)
            .insert(0, "Hello ")
            .toString();
        System.out.println(result); // Hello Java 21
    }
}
```

**What this does:** All StringBuilder methods return `this`, enabling method chaining. `delete(start, end)` is exclusive of end (same as `substring`). `reverse()` reverses the entire content in-place.

### Dry Run — StringBuilder reverse()

```java
StringBuilder sb = new StringBuilder("Java");
sb.reverse();
```

| Step | Action              | Buffer   |
|------|---------------------|----------|
| Init | Buffer = "Java"     | [J,a,v,a] |
| 1    | Swap index 0 ↔ 3   | [a,a,v,J] |
| 2    | Swap index 1 ↔ 2   | [a,v,a,J] |
| Done | Result              | "avaJ"    |

> ⚠️ **Pitfall:** `StringBuilder` is not thread-safe. If multiple threads share a StringBuilder, use `StringBuffer` or synchronize manually.

---

## 6. Text Blocks [Java 13+]

### What is it

Text blocks let you write multi-line strings naturally without escaping. They strip **incidental whitespace** (leading spaces that are just for code indentation).

### Visual Diagram — Incidental Whitespace

```java
String html = """
              <html>
                  <body>Hello</body>
              </html>
              """;
// The 14 spaces before <html> are "incidental" — stripped by compiler.
// Result: "<html>\n    <body>Hello</body>\n</html>\n"
// The closing """ determines the baseline for stripping.
```

### Example 1 — Basic Text Block

```java
public class TextBlocks {
    public static void main(String[] args) {
        // Classic string — ugly with escapes
        String json = "{\n" +
                      "  \"name\": \"Alice\",\n" +
                      "  \"age\": 30\n" +
                      "}";

        // Text block — clean [Java 13+]
        String jsonBlock = """
                {
                  "name": "Alice",
                  "age": 30
                }
                """;

        System.out.println(json);
        System.out.println(jsonBlock);
        // Same output for both
    }
}
```

**What this does:** Text blocks start with `"""` followed by a newline. The incidental whitespace (indentation that aligns with code) is automatically stripped. No need to escape double quotes.

### Example 2 — Special Escape Sequences in Text Blocks

```java
public class TextBlockEscapes {
    public static void main(String[] args) {
        // \s preserves trailing whitespace (otherwise stripped)
        String padded = """
                col1  \s
                col2  \s
                """;
        // Each line has 2 trailing spaces preserved

        // \ at end of line = line continuation (no newline in result)
        String noNewline = """
                This is a very \
                long line that \
                continues
                """;
        System.out.println(noNewline);
        // This is a very long line that continues

        // SQL example
        String query = """
                SELECT u.name, u.email
                  FROM users u
                 WHERE u.active = true
                   AND u.age > 18
                 ORDER BY u.name
                """;
        System.out.println(query);
    }
}
```

**What this does:** `\s` escape preserves trailing whitespace that would otherwise be stripped. `\` at line end joins lines. These are useful for SQL, HTML, JSON, and YAML literals.

### Example 3 — Text Block with formatted()

```java
public class TextBlockFormatted {
    public static void main(String[] args) {
        String name = "Alice";
        int age = 30;

        // Text blocks don't support direct interpolation
        // Use formatted() [Java 15+] or String.format()
        String message = """
                Dear %s,
                You are %d years old.
                Welcome!
                """.formatted(name, age);
        System.out.println(message);
        // Dear Alice,
        // You are 30 years old.
        // Welcome!
    }
}
```

**What this does:** Text blocks don't have built-in interpolation (no `${}` like Kotlin). Use `.formatted()` as the cleanest option. String templates with `STR.` syntax is in preview in Java 21.

> ⚠️ **Pitfall:** The closing `"""` position determines how much whitespace is stripped. If the closing `"""` is at column 0, NO whitespace is stripped. Typically place it indented with the content.

---

## Quick Reference

```
String:          immutable, thread-safe, in pool when literal
new String("x"): creates new heap object, not pooled
s.intern():      puts into pool, returns pooled reference
==               reference equality (don't use for value comparison!)
.equals()        content equality (always use this)
.equalsIgnoreCase() case-insensitive equality

Key methods:
  length()       charAt(i)      substring(start, end)
  indexOf(str)   contains(str)  startsWith/endsWith(str)
  replace()      replaceAll()   split(regex)
  toUpperCase()  toLowerCase()  trim() / strip() [11+]
  isBlank() [11+] lines() [11+] repeat(n) [11+]
  formatted() [15+]

StringBuilder:   mutable, not thread-safe — use in single-threaded loops
StringBuffer:    mutable, thread-safe — rarely needed today

Text blocks [13+]:
  """ ... """    strips incidental whitespace
  \s             preserve trailing space
  \              line continuation
```
