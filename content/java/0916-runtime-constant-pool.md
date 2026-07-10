---
card: java
gi: 916
slug: runtime-constant-pool
title: Runtime constant pool
---

## 1. What it is

Every loaded class has its own **runtime constant pool** — a per-class table, stored in the [method area/metaspace](0912-method-area-metaspace.md), holding the class's literal constants (numeric literals, `String` literals) and symbolic references to other classes, fields, and methods that its bytecode refers to by index rather than by directly-embedded name. Instead of a method's bytecode containing a full class or method name inline every time it's referenced, it contains a small integer index into this pool; the actual name (or, after [resolution](0905-loading-linking-verify-prepare-resolve-initialization.md), a direct reference to the real target) lives in the pool entry at that index. This indirection is what lets a compiled `.class` file's bytecode stay compact and lets the JVM defer resolving symbolic references until they're actually needed.

## 2. Why & when

Understanding the runtime constant pool explains several otherwise-mysterious behaviors: why `String` literals with the same content are automatically shared (`==`-equal) within and across classes via **string interning** — literal `String`s are entries in the constant pool, and the JVM maintains a single shared intern pool ensuring identical literal content maps to the same `String` object — while `String`s built at runtime (via concatenation, `StringBuilder`, etc.) are *not* automatically interned and therefore are separate objects even with identical content; why symbolic references can fail lazily, the first time they're actually used, rather than at class-loading time (that laziness is exactly [resolution](0905-loading-linking-verify-prepare-resolve-initialization.md) deferring the pool-index-to-real-reference lookup); and why `String.intern()` exists as an explicit way to opt a runtime-constructed string into that same shared pool. This matters whenever you're reasoning about `==` versus `.equals()` for strings (a classic Java pitfall), or working with very large numbers of duplicate string values where explicit interning could meaningfully reduce memory usage.

## 3. Core concept

```java
String a = "hello";          // a LITERAL -- an entry in the constant pool, automatically interned
String b = "hello";          // the SAME literal content -- refers to the SAME pooled String object
System.out.println(a == b);  // true -- both point to the identical, shared, pooled instance

String c = new String("hello");     // explicitly creates a NEW object on the heap, NOT pooled automatically
System.out.println(a == c);          // false -- different objects, despite identical content
System.out.println(a == c.intern()); // true -- intern() explicitly looks up (or adds) the pooled equivalent
```

The constant pool is what makes `a == b` true for identical literals — both `"hello"` occurrences in the source compile to the same constant-pool entry, which the JVM resolves to one single, shared `String` instance.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Two string literals with identical content both referencing the same entry in the shared string intern pool, while a string built with new String() creates a separate, unpooled heap object">
  <rect x="20" y="20" width="150" height="35" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="95" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">a = "hello" (literal)</text>
  <rect x="20" y="65" width="150" height="35" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="95" y="87" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">b = "hello" (literal)</text>

  <rect x="240" y="40" width="180" height="40" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="330" y="65" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Intern pool: "hello" (ONE object)</text>

  <line x1="170" y1="37" x2="236" y2="55" stroke="#8b949e" stroke-width="1.5" marker-end="url(#a44)"/>
  <line x1="170" y1="82" x2="236" y2="65" stroke="#8b949e" stroke-width="1.5" marker-end="url(#a44)"/>

  <rect x="440" y="90" width="180" height="40" rx="8" fill="#1c2430" stroke="#f0883e"/>
  <text x="530" y="115" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">c = new String("hello")</text>
  <text x="530" y="145" fill="#f0883e" font-size="9" text-anchor="middle" font-family="sans-serif">separate heap object, NOT pooled</text>
  <defs><marker id="a44" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

*Both literal occurrences resolve to the same shared, pooled object; `new String(...)` deliberately bypasses the pool, creating a distinct heap object even with identical content.*

## 5. Runnable example

Scenario: directly demonstrating string interning behavior, growing from confirming literal-vs-`new` identity differences, to explicit `intern()` usage, to a version demonstrating string concatenation's interaction with compile-time constant folding versus genuine runtime concatenation.

### Level 1 — Basic

```java
public class LiteralVsNewStringIdentity {
    public static void main(String[] args) {
        String a = "hello";
        String b = "hello";
        String c = new String("hello");

        System.out.println("a == b (both literals): " + (a == b));
        System.out.println("a == c (literal vs new String()): " + (a == c));
        System.out.println("a.equals(c) (content comparison): " + a.equals(c));
    }
}
```

**How to run:** `java LiteralVsNewStringIdentity.java` (JDK 17+).

Expected output:
```
a == b (both literals): true
a == c (literal vs new String()): false
a.equals(c) (content comparison): true
```

Both literal occurrences of `"hello"` resolve to the exact same shared, interned `String` object (`a == b` is `true`), while `new String("hello")` deliberately creates a distinct heap object with the same content, so `a == c` is `false` even though `.equals()` correctly reports the content as identical.

### Level 2 — Intermediate

```java
public class ExplicitInterning {
    public static void main(String[] args) {
        String a = "hello";
        String c = new String("hello");

        System.out.println("a == c: " + (a == c) + " (still false -- different objects)");

        String interned = c.intern(); // explicitly looks up (or adds) "hello" in the shared intern pool
        System.out.println("a == interned: " + (a == interned) + " (true -- intern() found the SAME pooled instance)");

        // Demonstrating this at scale: many duplicate, runtime-built strings, deliberately interned
        // to collapse them all down to references to ONE shared object, saving memory.
        String[] duplicates = new String[1000];
        for (int i = 0; i < duplicates.length; i++) {
            duplicates[i] = new String("shared-value").intern(); // force sharing
        }
        boolean allSameObject = true;
        for (String s : duplicates) {
            if (s != duplicates[0]) { allSameObject = false; break; }
        }
        System.out.println("all 1000 interned duplicates share ONE object: " + allSameObject);
    }
}
```

**How to run:** `java ExplicitInterning.java`.

Expected output:
```
a == c: false (still false -- different objects)
a == interned: true (true -- intern() found the SAME pooled instance)
all 1000 interned duplicates share ONE object: true
```

The real-world concern added: `intern()` gives you an explicit mechanism to opt a runtime-constructed `String` into the same shared pool that literals automatically use — the 1000-element demonstration shows this collapsing potentially 1000 separate, duplicate heap objects down to references to a single shared instance, a genuine memory-saving technique for workloads with many repeated string values (e.g., parsing large amounts of data with many repeated field names or category values).

### Level 3 — Advanced

```java
public class CompileTimeConcatenationVsRuntime {
    static final String PREFIX = "hel"; // compile-time constant
    static final String SUFFIX = "lo";   // compile-time constant

    public static void main(String[] args) {
        String a = "hello"; // literal

        // Compile-time constant concatenation: the COMPILER folds this into a single
        // literal ("hello") at COMPILE time, since both operands are compile-time constants --
        // so this behaves EXACTLY like writing "hello" directly, and IS interned automatically.
        String b = PREFIX + SUFFIX;
        System.out.println("a == b (compile-time constant concatenation): " + (a == b));

        // RUNTIME concatenation: even though the RESULT has identical content, this concatenation
        // genuinely happens at runtime (via a non-constant variable), so it produces a NEW,
        // NOT-automatically-interned String object.
        String prefix = "hel";  // a REGULAR (non-final) local variable -- not a compile-time constant
        String runtimeResult = prefix + "lo";
        System.out.println("a == runtimeResult (genuine runtime concatenation): " + (a == runtimeResult));
        System.out.println("a == runtimeResult.intern(): " + (a == runtimeResult.intern()) + " (true, once explicitly interned)");
    }
}
```

**How to run:** `java CompileTimeConcatenationVsRuntime.java`.

Expected output:
```
a == b (compile-time constant concatenation): true
a == runtimeResult (genuine runtime concatenation): false
a == runtimeResult.intern(): true (true, once explicitly interned)
```

This adds the production-flavored hard case: distinguishing compile-time constant folding (where the Java compiler itself computes `PREFIX + SUFFIX` at compile time, since both are `static final` compile-time constants, producing bytecode that references the literal `"hello"` directly — hence automatically interned, just like writing it by hand) from genuine runtime concatenation (where `prefix` is an ordinary, non-final local variable, so the compiler cannot know its value ahead of time, and the `+` operation genuinely executes at runtime, producing a fresh, non-interned `String` object even though its content happens to be identical).

## 6. Walkthrough

Tracing why `a == b` is `true` but `a == runtimeResult` is `false` in `CompileTimeConcatenationVsRuntime.main`:

1. `PREFIX` and `SUFFIX` are both declared `static final` and initialized with literal values — the Java compiler recognizes both as **compile-time constants**, meaning their values are fully known while compiling, not just at runtime.
2. Because `PREFIX + SUFFIX` combines two compile-time constants using the `+` operator, the compiler performs **constant folding**: it computes the concatenation result (`"hello"`) itself, during compilation, and emits bytecode for `b`'s initialization that references the literal `"hello"` directly — functionally indistinguishable from having written `String b = "hello";` by hand.
3. Since this folded literal is, from the constant pool's perspective, the exact same entry as `a`'s literal `"hello"`, both `a` and `b` end up referencing the identical, shared, interned `String` object — hence `a == b` is `true`.
4. `prefix`, in contrast, is declared as an ordinary local variable (not `final`, not treated as a compile-time constant even though it's assigned a literal value) — the compiler cannot fold `prefix + "lo"` at compile time, since in general a non-final local variable's value could theoretically change before this expression executes (even though, in this specific snippet, it happens not to).
5. Because the compiler treats this concatenation as needing to genuinely execute at runtime, it generates bytecode that actually performs the concatenation when the program runs (internally, typically via a `StringBuilder`), producing a **new** `String` object on the heap — this object is not automatically added to the intern pool, even though its content (`"hello"`) is identical to the pooled literal.
6. `a == runtimeResult` is therefore `false`: `a` points to the pooled literal, while `runtimeResult` points to this separate, freshly-created object.
7. `runtimeResult.intern()` explicitly looks up `"hello"` in the shared intern pool (finding the existing entry, since `a`'s literal already put it there) and returns that shared instance — so `a == runtimeResult.intern()` correctly evaluates to `true`, demonstrating `intern()`'s role in explicitly bridging a runtime-constructed string back into the same shared pool that literals and compile-time-constant expressions use automatically.

## 7. Gotchas & takeaways

> **Gotcha:** never use `==` to compare `String` content in application logic — always use `.equals()` (or `.equalsIgnoreCase()`, `Objects.equals()`, etc.) — the interning behavior shown throughout this tutorial means `==` can *appear* to work correctly for simple literal comparisons during testing, only to fail unpredictably in production once the same logical string values start arriving via runtime construction (user input, deserialization, string concatenation) rather than as source-code literals.

- Every class has its own runtime constant pool, storing literal constants and symbolic references its bytecode refers to by index — a compact, indirection-based representation that also enables lazy [resolution](0905-loading-linking-verify-prepare-resolve-initialization.md).
- String literals are automatically interned — identical literal content across the entire program shares one single, pooled `String` object, making `==` comparisons between literals `true`.
- `new String(...)` explicitly creates a distinct, non-pooled heap object even with identical content to an existing literal; `.intern()` explicitly opts a runtime-constructed string into the shared pool.
- Compile-time constant expressions (concatenations of `static final` literal-valued fields) are folded by the compiler into a single literal, and therefore are automatically interned exactly like a hand-written literal — genuine runtime concatenation (involving any non-constant value) is not.
- Always use `.equals()` for `String` content comparison in application logic — reserve `==` for the rare, deliberate case where you specifically need reference identity (which interning can make deceptively easy to get "accidentally right" for literals alone, masking the underlying bug).
