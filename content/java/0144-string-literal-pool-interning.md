---
card: java
gi: 144
slug: string-literal-pool-interning
title: String literal pool & interning
---

## 1. What it is

The **string literal pool** (sometimes called the "intern pool") is a special area the JVM maintains where it stores exactly one copy of each distinct string literal text that appears in the compiled code. When you write a string literal like `"hello"`, the JVM checks the pool first: if an identical string is already there, your variable is made to reference that *existing* object instead of creating a new one. Strings created with `new String(...)`, by contrast, always create a fresh object on the heap, bypassing the pool entirely — unless you explicitly call `.intern()` on it.

```java
String a = "hello";
String b = "hello";
String c = new String("hello");

System.out.println(a == b); // true  — both literals share the SAME pooled object
System.out.println(a == c); // false — c is a separate object on the heap, even though the text is identical
System.out.println(a.equals(c)); // true — equals() compares CONTENT, not object identity
```

This is exactly why `String`'s immutability (previous topic) matters so much: sharing one object across many variables is only safe because none of them can ever modify it.

## 2. Why & when

The literal pool exists purely as a **memory and performance optimization**, made possible by immutability:

- **Deduplication** — if the same literal text ("OK", "true", common error messages) appears hundreds of times across a large codebase, the JVM stores it once and reuses it, rather than allocating hundreds of identical objects.
- **Fast equality for pooled strings** — since identical literals share one object, `==` happens to work for comparing literal-only strings, though relying on this is a well-known trap (see part 7).
- **`.intern()` for manual deduplication** — if you build many strings at runtime (e.g., parsing a file full of repeated words) and want to deduplicate them the same way literals are, calling `.intern()` explicitly adds a string to the pool (or returns the existing pooled copy if already present).

None of this changes how you should compare strings for equality in ordinary code: **always use `.equals()`**, never `==`, regardless of whether pooling is involved — pooling is an implementation detail of memory management, not a substitute for proper content comparison.

## 3. Core concept

```java
public class PoolDemo {
    public static void main(String[] args) {
        String lit1 = "cat";
        String lit2 = "cat";
        String heap1 = new String("cat");
        String heap2 = new String("cat");
        String interned = heap1.intern();

        System.out.println("lit1 == lit2:        " + (lit1 == lit2));         // true (same pooled object)
        System.out.println("lit1 == heap1:       " + (lit1 == heap1));        // false (heap1 is separate)
        System.out.println("heap1 == heap2:      " + (heap1 == heap2));       // false (two separate heap objects)
        System.out.println("lit1 == interned:    " + (lit1 == interned));     // true (intern() returns the pooled object)
        System.out.println("lit1.equals(heap1):  " + (lit1.equals(heap1)));   // true (same content either way)
    }
}
```

`heap1` and `heap2` are two entirely separate objects even though both were constructed from the identical text `"cat"` — `new String(...)` never consults the pool automatically. Calling `.intern()` on `heap1`, however, returns the pool's existing `"cat"` object (the same one `lit1` already references), which is why `lit1 == interned` is `true`.

## 4. Diagram

<svg viewBox="0 0 700 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="String pool diagram: string literals sharing identical text refer to one shared object in the string pool, while strings created with new always get their own separate object on the heap, even with identical content." >
  <rect x="8" y="8" width="684" height="184" rx="8" fill="#0d1117"/>
  <text x="350" y="24" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">String pool vs. heap — same text, different object identity</text>

  <rect x="230" y="45" width="240" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="350" y="65" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">STRING POOL</text>
  <text x="350" y="83" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="monospace">"cat" (ONE shared object)</text>

  <path d="M 100 105 L 320 95" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#a)"/>
  <text x="100" y="115" fill="#79c0ff" font-size="8.5" font-family="monospace">lit1</text>

  <path d="M 130 130 L 340 96" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#a)"/>
  <text x="130" y="140" fill="#79c0ff" font-size="8.5" font-family="monospace">lit2</text>

  <path d="M 160 150 L 360 96" stroke="#6db33f" stroke-width="1.5" stroke-dasharray="3,2" marker-end="url(#a)"/>
  <text x="160" y="160" fill="#6db33f" font-size="8.5" font-family="monospace">heap1.intern()</text>

  <rect x="530" y="45" width="130" height="34" rx="6" fill="#1c2430" stroke="#f85149" stroke-width="1.5"/>
  <text x="595" y="66" fill="#f85149" font-size="9" text-anchor="middle" font-family="monospace">"cat" (heap1)</text>
  <path d="M 560 105 L 590 79" stroke="#f85149" stroke-width="1.5" marker-end="url(#b)"/>
  <text x="540" y="115" fill="#f85149" font-size="8.5" font-family="monospace">heap1</text>

  <rect x="530" y="110" width="130" height="34" rx="6" fill="#1c2430" stroke="#f85149" stroke-width="1.5"/>
  <text x="595" y="131" fill="#f85149" font-size="9" text-anchor="middle" font-family="monospace">"cat" (heap2)</text>
  <path d="M 560 150 L 590 144" stroke="#f85149" stroke-width="1.5" marker-end="url(#b)"/>
  <text x="540" y="165" fill="#f85149" font-size="8.5" font-family="monospace">heap2</text>

  <text x="350" y="185" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="sans-serif">lit1, lit2, and heap1.intern() all point at ONE pooled object; heap1 and heap2 are two DIFFERENT objects.</text>
  <defs>
    <marker id="a" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
    <marker id="b" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#f85149"/></marker>
  </defs>
</svg>

Literals share one pooled object automatically; `new String(...)` always creates a separate one unless later `.intern()`ed.

## 5. Runnable example

Scenario: checking whether a user-submitted "role" string matches an expected value — starting with a version that uses `==` and works by accident (because both sides happen to be literals), then breaking it realistically by introducing a heap-allocated string (simulating input read at runtime), then fixing and hardening it with proper `.equals()` comparison plus a defensive null-safe check.

### Level 1 — Basic (works, but for the wrong reason)

```java
public class RoleCheckBasic {
    public static void main(String[] args) {
        String expectedRole = "admin";
        String userRole = "admin"; // a literal — happens to share the pool with expectedRole

        if (userRole == expectedRole) {
            System.out.println("Access granted.");
        } else {
            System.out.println("Access denied.");
        }
    }
}
```

**How to run:** `java RoleCheckBasic.java`

This prints `"Access granted."` — but only because both `userRole` and `expectedRole` are string literals with identical text, so the pool makes `==` happen to return `true`. This code is fragile: it works here by coincidence of how literals are pooled, not because `==` is actually the correct way to compare string content.

### Level 2 — Intermediate (the bug surfaces)

Same role check, now simulating `userRole` as it would realistically arrive at runtime — built via `new String(...)` (standing in for input read from a file, network, or `Scanner`, none of which come from the literal pool) — exposing exactly why `==` was never safe.

```java
public class RoleCheckIntermediate {
    public static void main(String[] args) {
        String expectedRole = "admin";
        String userRole = new String("admin"); // simulates role text read from external input at runtime

        if (userRole == expectedRole) {
            System.out.println("Access granted.");
        } else {
            System.out.println("Access denied."); // <-- WRONG! Same text, but == compares object identity
        }

        if (userRole.equals(expectedRole)) {
            System.out.println("equals() correctly says: match.");
        }
    }
}
```

**How to run:** `java RoleCheckIntermediate.java`

Now `userRole` is a separate heap object (never consulting the pool), so `userRole == expectedRole` is `false` even though both strings contain the identical text `"admin"` — this incorrectly denies access to a legitimate admin. The second check, `userRole.equals(expectedRole)`, correctly reports a match, because `.equals()` compares actual character content, not object identity.

### Level 3 — Advanced

Same role check, now using `.equals()` properly, guarded against a `null` `userRole` (which a real input-parsing path could plausibly produce), and additionally demonstrating `.intern()` explicitly to show how runtime-built strings can be deliberately pooled if that optimization is ever genuinely needed.

```java
public class RoleCheckAdvanced {

    static boolean hasRole(String userRole, String expectedRole) {
        return expectedRole.equals(userRole); // constant on the left: avoids a NullPointerException if userRole is null
    }

    public static void main(String[] args) {
        String expectedRole = "admin";

        String[] incomingRoles = { new String("admin"), new String("guest"), null };

        for (String role : incomingRoles) {
            System.out.println("role=" + role + " -> hasRole: " + hasRole(role, expectedRole));
        }

        // Demonstrating explicit interning of a runtime-built string
        String runtimeBuilt = new String("admin");
        String internedVersion = runtimeBuilt.intern();
        System.out.println("runtimeBuilt == expectedRole:   " + (runtimeBuilt == expectedRole));
        System.out.println("internedVersion == expectedRole: " + (internedVersion == expectedRole));
    }
}
```

**How to run:** `java RoleCheckAdvanced.java`

`hasRole` calls `expectedRole.equals(userRole)` with the known-non-null constant `expectedRole` as the receiver, rather than `userRole.equals(expectedRole)` — this is a standard defensive idiom, since if `userRole` were `null`, calling `.equals()` *on* it would throw a `NullPointerException`, but `String.equals()` safely returns `false` when its *argument* is `null`. The final two lines show that `runtimeBuilt` (built with `new`) is `!=` the literal `expectedRole`, but calling `.intern()` on it returns the exact pooled object, making `internedVersion == expectedRole` `true` — proving `.intern()` genuinely merges a runtime string into the same pool literals use.

## 6. Walkthrough

Trace the loop over `incomingRoles = { new String("admin"), new String("guest"), null }` in `RoleCheckAdvanced`:

**role = new String("admin").** `hasRole(role, "admin")` is called; inside, `expectedRole.equals(userRole)` runs as `"admin".equals(<the heap "admin" object>)`. `.equals()` compares content character-by-character (not identity), finds them equal, and returns `true`. Prints `role=admin -> hasRole: true`.

**role = new String("guest").** `expectedRole.equals(userRole)` becomes `"admin".equals("guest")`, which compares content and correctly returns `false`. Prints `role=guest -> hasRole: false`.

**role = null.** `hasRole(null, "admin")` calls `expectedRole.equals(userRole)`, i.e., `"admin".equals(null)`. Because `expectedRole` (a real, non-null string) is the receiver and `null` is merely the *argument*, `String.equals()`'s own implementation checks for this and simply returns `false` — no exception is thrown. Prints `role=null -> hasRole: false`.

```
role=new String("admin"): "admin".equals(heap-"admin") -> content matches -> true
role=new String("guest"): "admin".equals(heap-"guest") -> content differs -> false
role=null:                "admin".equals(null)         -> equals() defends against null arg -> false (no exception)
```

If `hasRole` had instead called `userRole.equals(expectedRole)` (receiver and argument swapped), the third call would have thrown a `NullPointerException` the moment `userRole` was `null`, since you cannot invoke `.equals()` (or any method) on a `null` reference.

**Final two lines.** `runtimeBuilt` is a fresh heap object built with `new String("admin")`, so `runtimeBuilt == expectedRole` prints `false`. `runtimeBuilt.intern()` looks up `"admin"` in the pool, finds the object `expectedRole` already refers to, and returns that same reference — so `internedVersion == expectedRole` prints `true`.

## 7. Gotchas & takeaways

> **Never use `==` to compare `String` content — use `.equals()` (or `.equalsIgnoreCase()`) every time, with no exceptions.** `==` compares object identity, and whether two equal-content strings happen to be the *same* object depends entirely on pooling details (whether both came from literals, whether one was explicitly `.intern()`ed) that are easy to get wrong and that can change between how test code and production code happen to construct their strings.

> **Put a known non-null constant on the left side of `.equals()` when comparing against a possibly-`null` variable** (`"admin".equals(userRole)`, not `userRole.equals("admin")`) — this avoids a `NullPointerException` if the variable turns out to be `null`, since `String.equals()` safely returns `false` for a `null` argument but cannot be called at all on a `null` receiver.

- String literals with identical text automatically share one object from the JVM's string pool; `new String(...)` always creates a distinct heap object, bypassing the pool.
- `.intern()` explicitly adds a runtime-built string to the pool (or returns the existing pooled copy), making `==` comparisons against literals succeed afterward — but this is rarely needed in ordinary application code.
- Pooling is a memory optimization made possible entirely by immutability; it is not a content-comparison mechanism and should never be relied upon as one.
- `.equals()` compares actual character content and is always the correct choice for checking whether two strings represent "the same text," regardless of how either one was created.
