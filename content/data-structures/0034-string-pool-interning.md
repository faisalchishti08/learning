---
card: data-structures
gi: 34
slug: string-pool-interning
title: String pool & interning
---

## 1. What it is

The **string pool** (also called the string intern pool) is a special area of JVM memory that caches unique `String` literal values, so identical literals can share a single object instead of each allocating a new one. **Interning** is the process of looking a string up in this pool (adding it if not already present) and getting back the shared, canonical reference. `String.intern()` performs this explicitly.

## 2. Why & when

String literals appear constantly in code — method names, keys, constant text — and many programs repeat the same literal many times. The string pool exploits `String` immutability (covered in [String immutability in Java](0033-string-immutability-in-java.md)) to safely deduplicate these repeated values, saving memory. This matters when reasoning about `==` versus `.equals()` for strings, a frequent source of subtle bugs.

## 3. Core concept

**Literals are automatically pooled; `new String(...)` is not.** `String a = "hello";` and `String b = "hello";` both resolve to the *same* pooled object — the compiler recognizes identical literals and reuses them. But `String c = new String("hello");` explicitly forces a brand-new object on the heap, deliberately bypassing the pool, even though its content is identical.

**Why pooling is only safe because strings are immutable.** If strings could change after creation, sharing one object across many variables would be dangerous — mutating it through one reference would corrupt every other "unrelated" variable pointing at the same pooled object. Immutability removes that risk entirely.

**`intern()` explicitly pools a string built at runtime.** A string built via concatenation, `substring`, or `new String(...)` is not automatically pooled. Calling `.intern()` on it looks up (or adds) the equivalent value in the pool and returns that shared reference, making `==` comparison with a literal succeed afterward.

**`==` compares references; `.equals()` compares content — always prefer `.equals()`.** Pooling can make `==` "accidentally" work for literals, exactly like `Integer` caching for small values (see [Autoboxing / unboxing & its cost](0012-autoboxing-unboxing-its-cost.md)) — this is a trap, not a guarantee, since it silently breaks for strings built at runtime.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Two literal string variables sharing one pooled object, versus a new String() creating a separate heap object with the same content">
  <g font-family="sans-serif" font-size="11">
    <text x="150" y="16" fill="#8b949e" text-anchor="middle">a = "hi"; b = "hi";</text>
    <rect x="60" y="26" width="70" height="26" fill="#161b22" stroke="#79c0ff"/><text x="95" y="44" fill="#e6edf3" text-anchor="middle" font-size="10">a</text>
    <rect x="150" y="26" width="70" height="26" fill="#161b22" stroke="#79c0ff"/><text x="185" y="44" fill="#e6edf3" text-anchor="middle" font-size="10">b</text>
    <rect x="100" y="80" width="80" height="30" fill="#0d1117" stroke="#3fb950"/><text x="140" y="100" fill="#e6edf3" text-anchor="middle" font-size="10">"hi" (pooled)</text>
    <line x1="95" y1="52" x2="135" y2="78" stroke="#79c0ff" marker-end="url(#a9)"/>
    <line x1="185" y1="52" x2="150" y2="78" stroke="#79c0ff" marker-end="url(#a9)"/>
    <defs><marker id="a9" markerWidth="8" markerHeight="8" refX="4" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#79c0ff"/></marker></defs>
    <text x="140" y="135" fill="#79c0ff" text-anchor="middle" font-size="10">a == b -&gt; true (same object)</text>

    <text x="480" y="16" fill="#8b949e" text-anchor="middle">c = new String("hi");</text>
    <rect x="440" y="26" width="80" height="26" fill="#161b22" stroke="#f0883e"/><text x="480" y="44" fill="#e6edf3" text-anchor="middle" font-size="10">c</text>
    <rect x="440" y="80" width="80" height="30" fill="none" stroke="#f0883e"/><text x="480" y="100" fill="#e6edf3" text-anchor="middle" font-size="10">"hi" (own object)</text>
    <line x1="480" y1="52" x2="480" y2="78" stroke="#f0883e" marker-end="url(#a10)"/>
    <defs><marker id="a10" markerWidth="8" markerHeight="8" refX="4" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#f0883e"/></marker></defs>
    <text x="480" y="135" fill="#79c0ff" text-anchor="middle" font-size="10">a == c -&gt; false (different object, same content)</text>
  </g>
</svg>

`a` and `b`, both literals, share one pooled object. `c`, built with `new String(...)`, gets its own separate object even though its content matches.

## 5. Runnable example

```java
// StringPoolInterning.java
public class StringPoolInterning {

    // Basic: identical literals share the same pooled object.
    static void basicLevel() {
        String a = "hello";
        String b = "hello";
        System.out.println("basic: a == b -> " + (a == b)); // true: same pooled object
        System.out.println("basic: a.equals(b) -> " + a.equals(b)); // true either way
    }

    // Intermediate: new String(...) deliberately bypasses the pool.
    static void intermediateLevel() {
        String a = "hello";
        String c = new String("hello"); // explicit new object, NOT pooled automatically
        System.out.println("intermediate: a == c -> " + (a == c));         // false: different objects
        System.out.println("intermediate: a.equals(c) -> " + a.equals(c)); // true: same content
    }

    // Advanced: intern() explicitly pools a runtime-built string, making == succeed afterward.
    static void advancedLevel() {
        String runtimeBuilt = new String("wo") + new String("rld"); // built via concatenation, not pooled
        String literal = "world";

        System.out.println("advanced: runtimeBuilt == literal (before intern) -> " + (runtimeBuilt == literal)); // false

        String interned = runtimeBuilt.intern(); // looks up (or adds) "world" in the pool
        System.out.println("advanced: interned == literal (after intern) -> " + (interned == literal)); // true
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

**How to run:** save as `StringPoolInterning.java`, then run `java StringPoolInterning.java`.

## 6. Walkthrough

1. `basicLevel()` declares `a` and `b` as the identical literal `"hello"`. The compiler recognizes the literal and reuses the same pooled object for both, so `a == b` is `true`.
2. `intermediateLevel()` creates `c` with `new String("hello")`, forcing a fresh heap object even though its content matches `a`. `a == c` is `false` (different objects), but `a.equals(c)` is `true` (same content) — the correct comparison to use.
3. `advancedLevel()` builds `runtimeBuilt` by concatenating two `new String(...)` values at runtime — this result is a fresh, non-pooled object, so `runtimeBuilt == literal` is `false` even though both hold `"world"`.
4. Calling `runtimeBuilt.intern()` looks up `"world"` in the pool. Since the literal `"world"` used elsewhere in the program already put that value in the pool, `intern()` returns that same shared reference — so `interned == literal` becomes `true`.

## 7. Gotchas & takeaways

> Gotcha: `==` "working" for string literals is a pooling side effect, not a language guarantee about string equality — the moment a string is built at runtime (concatenation, `substring`, `new String(...)`, reading from user input or a file), `==` silently starts comparing distinct objects. Always use `.equals()` for string content comparison, never `==`.

- The string pool caches literal values so identical literals share one object automatically; `new String(...)` deliberately opts out of this sharing.
- Pooling is only safe because `String` is immutable — no reference can ever change the shared value out from under another reference.
- `.intern()` explicitly adds (or looks up) a runtime-built string in the pool, letting `==` succeed against a matching literal afterward.
- Related concepts: [String immutability in Java](0033-string-immutability-in-java.md), [Autoboxing / unboxing & its cost](0012-autoboxing-unboxing-its-cost.md) (the same == vs .equals() trap for Integer caching).
