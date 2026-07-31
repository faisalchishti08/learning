---
card: data-structures
gi: 33
slug: string-immutability-in-java
title: String immutability in Java
---

## 1. What it is

**Immutability** means once a `String` object is created, its contents can never change. Every method that looks like it "modifies" a string — `toUpperCase()`, `replace()`, `concat()`, `substring()` — actually returns a **brand-new** `String` object, leaving the original untouched. `s.toUpperCase()` does nothing to `s` itself unless you reassign it: `s = s.toUpperCase();`.

## 2. Why & when

Immutability matters for three concrete reasons: strings are safe to share across threads without synchronization (nothing can mutate them out from under you), they are safe to use as `HashMap` keys (their `hashCode()` never changes after creation, so their bucket never becomes wrong), and the JVM can safely cache and reuse identical string literals (the string pool). Understanding immutability also prevents a very common beginner bug: calling `s.trim()` or `s.replace(...)` and expecting `s` itself to have changed.

## 3. Core concept

**Every "mutating" method returns a new object.** `String result = original.toUpperCase();` — `original` is completely unchanged after this line; only `result` holds the uppercase value. If you forget to capture the return value, the operation's effect is silently lost.

**Why immutability enables safe caching (the string pool).** Because a `String`'s value can never change after creation, the JVM can let multiple variables share the exact same object for identical literals without any risk — no code can ever "surprise" another reference by mutating the shared value. This is exactly what [String pool & interning](0034-string-pool-interning.md) exploits.

**Why immutability makes strings safe `HashMap` keys.** [equals() & hashCode() contract](0014-equals-hashcode-contract.md) requires that an object's hash code never change after it is placed in a hash-based collection — otherwise it becomes unfindable in its original bucket. Because a `String`'s characters can never change, its `hashCode()` is guaranteed stable forever, making it a naturally safe key type.

**Immutability does not mean "no object is ever created."** Building up a string through repeated concatenation in a loop still creates many intermediate objects — immutability is about existing objects never changing, not about avoiding new allocations. That specific performance cost is covered in [Concatenation cost & why StringBuilder](0036-concatenation-cost-why-stringbuilder.md).

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Calling toUpperCase on a string creates a new object; the original reference still points at the unchanged original string">
  <g font-family="sans-serif" font-size="12">
    <rect x="40" y="30" width="140" height="30" fill="#161b22" stroke="#79c0ff"/><text x="110" y="50" fill="#e6edf3" text-anchor="middle" font-size="10">original -&gt; "hello"</text>
    <rect x="40" y="90" width="140" height="30" fill="none" stroke="#8b949e" stroke-dasharray="2,2"/><text x="110" y="110" fill="#8b949e" text-anchor="middle" font-size="10">"hello" (unchanged)</text>
    <line x1="110" y1="60" x2="110" y2="85" stroke="#79c0ff" marker-end="url(#a7)"/>
    <defs><marker id="a7" markerWidth="8" markerHeight="8" refX="4" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#79c0ff"/></marker></defs>

    <text x="360" y="20" fill="#8b949e">result = original.toUpperCase();</text>
    <rect x="360" y="30" width="140" height="30" fill="#161b22" stroke="#3fb950"/><text x="430" y="50" fill="#e6edf3" text-anchor="middle" font-size="10">result -&gt; new object</text>
    <rect x="360" y="90" width="140" height="30" fill="#0d1117" stroke="#3fb950"/><text x="430" y="110" fill="#e6edf3" text-anchor="middle" font-size="10">"HELLO" (brand new)</text>
    <line x1="430" y1="60" x2="430" y2="85" stroke="#3fb950" marker-end="url(#a8)"/>
    <defs><marker id="a8" markerWidth="8" markerHeight="8" refX="4" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#3fb950"/></marker></defs>
    <text x="320" y="150" fill="#79c0ff" text-anchor="middle">"mutating" methods always create a new String; the original is never touched</text>
  </g>
</svg>

`toUpperCase()` allocates an entirely new `"HELLO"` object. The `original` reference still points at the untouched `"hello"`.

## 5. Runnable example

```java
// StringImmutability.java
public class StringImmutability {

    // Basic: "mutating" methods actually return new objects, leaving the original untouched.
    static void basicLevel() {
        String original = "hello";
        String upper = original.toUpperCase();
        System.out.println("basic: original -> " + original); // still "hello"
        System.out.println("basic: upper -> " + upper);       // new object, "HELLO"
        System.out.println("basic: original == upper -> " + (original == upper)); // false: different objects
    }

    // Intermediate: the classic bug -- calling a method without reassigning the result does nothing visible.
    static void intermediateLevel() {
        String s = "  padded  ";
        s.trim(); // BUG: return value discarded, s is unchanged
        System.out.println("intermediate: after s.trim() (discarded) -> [" + s + "]");

        s = s.trim(); // correct: reassign to capture the new trimmed object
        System.out.println("intermediate: after s = s.trim() -> [" + s + "]");
    }

    // Advanced: immutability makes String hashCode() stable forever, safe as a HashMap key.
    static void advancedLevel() {
        String key = "user:42";
        int hashBefore = key.hashCode();
        // No operation exists that can change key's characters -- immutability guarantees this:
        int hashAfter = key.hashCode();
        System.out.println("advanced: hashCode stable -> " + (hashBefore == hashAfter));

        java.util.Map<String, String> map = new java.util.HashMap<>();
        map.put(key, "Alice");
        System.out.println("advanced: safe lookup later -> " + map.get("user:42"));
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

**How to run:** save as `StringImmutability.java`, then run `java StringImmutability.java`.

## 6. Walkthrough

1. `basicLevel()` calls `original.toUpperCase()` and stores the result in `upper`. Printing `original` afterward still shows `"hello"` — the method never touched it. `original == upper` is `false`, confirming they are two distinct objects.
2. `intermediateLevel()` calls `s.trim()` without capturing the return value — a common mistake. Printing `s` afterward shows it is still padded, since the trimmed result was created and immediately discarded.
3. Reassigning with `s = s.trim();` correctly updates `s` to point at the new, trimmed `String` object — this is the only way to make the change "stick."
4. `advancedLevel()` reads `key.hashCode()` twice. Because no Java operation can ever alter `key`'s characters after creation, both reads are guaranteed identical — this stability is exactly what lets `key` be safely used and later found again as a `HashMap` key.

## 7. Gotchas & takeaways

> Gotcha: `String` methods that appear to mutate (`trim()`, `replace()`, `toLowerCase()`, `concat()`, `substring()`) always return a new object and silently do nothing to the original if you forget to reassign the result — no compiler warning, no runtime error, just a value that quietly does not change.

- Every `String` "mutation" method returns a brand-new object; the original string can never be changed after creation.
- Forgetting to reassign the return value (`s.trim();` instead of `s = s.trim();`) is a silent no-op bug, not an error.
- Immutability guarantees a stable `hashCode()` forever, which is why `String` is a safe, common choice for `HashMap`/`HashSet` keys.
- Related concepts: [String pool & interning](0034-string-pool-interning.md), [equals() & hashCode() contract](0014-equals-hashcode-contract.md).
