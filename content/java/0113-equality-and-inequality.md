---
card: java
gi: 113
slug: equality-and-inequality
title: Equality == and inequality !=
---

## 1. What it is

`==` and `!=` compare their operands and produce a `boolean`, but their meaning depends entirely on whether the operands are primitives or references. For primitives, `==` compares the actual numeric (or `boolean`) *values*. For reference types (objects, arrays, boxed wrappers like `Integer`), `==` compares whether both operands refer to the *exact same object in memory* (identity), not whether the objects have equivalent content. To compare object *content* for equality, you must use the `.equals()` method instead.

```java
int a = 5, b = 5;
System.out.println(a == b);   // true — same numeric value

String s1 = new String("hi");
String s2 = new String("hi");
System.out.println(s1 == s2);        // false — two different String objects, even with equal content
System.out.println(s1.equals(s2));    // true — .equals() compares content

Integer boxed1 = 200, boxed2 = 200;
System.out.println(boxed1 == boxed2);  // false! outside the cached range, these are different objects
```

## 2. Why & when

`==` versus `.equals()` is one of the most common sources of bugs for developers new to Java (or coming from languages where `==` compares content by default):

- Comparing `String`s for content should almost always use `.equals()`, never `==` — string literals are interned and may coincidentally compare equal with `==`, but strings built with `new String(...)` or from user input generally will not, making `==` unreliable.
- Comparing boxed numeric wrappers (`Integer`, `Long`, etc.) with `==` works *by accident* for small values (Java caches boxed `Integer` objects from `-128` to `127`) but breaks for larger values — this is a notorious interview-question gotcha.
- `==` is the *correct* choice when you deliberately want identity comparison — e.g., checking if two references point to the exact same singleton instance, or comparing `enum` values (enum constants are guaranteed to be singletons, so `==` is idiomatic and safe for them).

## 3. Core concept

```java
public class EqualityDemo {
    public static void main(String[] args) {
        // Primitives: == compares value
        int x = 10, y = 10;
        System.out.println("x == y: " + (x == y));   // true

        // Strings: == compares identity, .equals() compares content
        String literal1 = "hello";
        String literal2 = "hello";
        System.out.println("literal1 == literal2: " + (literal1 == literal2));  // true (interned, same object)

        String newStr1 = new String("hello");
        String newStr2 = new String("hello");
        System.out.println("newStr1 == newStr2: " + (newStr1 == newStr2));        // false (different objects)
        System.out.println("newStr1.equals(newStr2): " + newStr1.equals(newStr2)); // true (same content)

        // Boxed Integer caching gotcha
        Integer small1 = 100, small2 = 100;
        Integer big1 = 200, big2 = 200;
        System.out.println("small1 == small2 (cached): " + (small1 == small2));   // true, by accident of caching
        System.out.println("big1 == big2 (not cached):  " + (big1 == big2));       // false! same value, different objects

        // The safe way to compare boxed types
        System.out.println("big1.equals(big2): " + big1.equals(big2));             // true, always correct

        // enum: == is correct and idiomatic
        enum Status { ACTIVE, INACTIVE }
        Status s1 = Status.ACTIVE;
        Status s2 = Status.ACTIVE;
        System.out.println("s1 == s2: " + (s1 == s2));   // true — enum constants are singletons
    }
}
```

## 4. Diagram

<svg viewBox="0 0 700 195" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Equality diagram: two Integer objects with value 200, both outside the cached range negative 128 to 127, are separate boxes in memory, so double equals compares their addresses and returns false, while dot equals compares their contents and returns true.">
  <rect x="8" y="8" width="684" height="179" rx="8" fill="#0d1117"/>
  <text x="350" y="24" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Integer big1 = 200, big2 = 200;  (outside the -128..127 cache range)</text>

  <rect x="60" y="44" width="90" height="30" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="105" y="64" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="monospace">big1</text>
  <rect x="230" y="44" width="90" height="30" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="275" y="64" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="monospace">big2</text>

  <rect x="40" y="96" width="130" height="40" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="105" y="120" fill="#6db33f" font-size="10" text-anchor="middle" font-family="monospace">Integer(200)</text>
  <rect x="210" y="96" width="130" height="40" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="275" y="120" fill="#6db33f" font-size="10" text-anchor="middle" font-family="monospace">Integer(200)</text>
  <line x1="105" y1="74" x2="105" y2="96" stroke="#79c0ff" stroke-width="1.5"/>
  <line x1="275" y1="74" x2="275" y2="96" stroke="#79c0ff" stroke-width="1.5"/>

  <text x="180" y="160" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">big1 == big2  →  false  (different boxes)</text>
  <text x="180" y="178" fill="#6db33f" font-size="9" text-anchor="middle" font-family="monospace">big1.equals(big2)  →  true  (same content)</text>
</svg>

Two separate `Integer` objects holding the same value compare unequal with `==` but equal with `.equals()`.

## 5. Runnable example

Scenario: a simple user-lookup cache that compares user IDs — first with the classic `==`-on-boxed-Integer bug, then fixed, then extended to a custom class needing a proper `.equals()` override.

### Level 1 — Basic

```java
import java.util.*;

public class EqualityBasic {
    public static void main(String[] args) {
        List<Integer> activeUserIds = List.of(42, 500, 1200);

        Integer searchId1 = 42;    // within cache range (-128..127)
        Integer searchId2 = 500;   // outside cache range

        // Manually simulating a naive "contains" check using == instead of .equals()
        boolean found1 = false, found2 = false;
        for (Integer id : activeUserIds) {
            if (id == searchId1) found1 = true;   // works, but only by luck (both in cache range)
            if (id == searchId2) found2 = true;    // BUG: likely false even if 500 is in the list
        }
        System.out.println("Found 42 (via ==):  " + found1);
        System.out.println("Found 500 (via ==): " + found2);   // probably false — wrong!
    }
}
```

**How to run:** `java EqualityBasic.java`

`id == searchId1` happens to work for `42` because both the boxed `42` from the list (auto-boxed from an `int` literal within the compiler-guaranteed cache range of `-128` to `127`) and the `searchId1 = 42` variable are likely backed by the *same* cached `Integer` object — `Integer.valueOf(42)` always returns the identical cached instance for values in that range. `500` is outside the cache range, so `Integer.valueOf(500)` creates a *new* object every time it's called, meaning the `500` inside the list and `searchId2`'s `500` are almost certainly different objects, making `id == searchId2` `false` even though the "real" values match — a classic, hard-to-spot bug that only manifests for certain numeric ranges.

### Level 2 — Intermediate

Same lookup, now correctly using `.equals()` (or, better, the collection's own built-in `contains`, which already uses `.equals()` internally), demonstrating the fix works uniformly regardless of the value's magnitude.

```java
import java.util.*;

public class EqualityIntermediate {
    public static void main(String[] args) {
        List<Integer> activeUserIds = List.of(42, 500, 1200);

        Integer searchId1 = 42;
        Integer searchId2 = 500;

        // Correct manual check: .equals() compares content, unaffected by caching
        boolean found1 = false, found2 = false;
        for (Integer id : activeUserIds) {
            if (id.equals(searchId1)) found1 = true;
            if (id.equals(searchId2)) found2 = true;
        }
        System.out.println("Found 42 (via equals):  " + found1);   // true
        System.out.println("Found 500 (via equals): " + found2);    // true — correct now, regardless of caching

        // Even better: let the collection's own contains() do the right thing
        System.out.println("contains(500) built-in: " + activeUserIds.contains(searchId2));  // true
    }
}
```

**How to run:** `java EqualityIntermediate.java`

`id.equals(searchId1)` calls `Integer.equals`, which unboxes both operands and compares their `int` values directly — this is correct and consistent regardless of whether the `Integer` objects happen to be cached or not, because it never relies on object identity. `List.contains` internally iterates and calls `.equals()` on each element for you, which is why it is generally preferable to write manual `.equals()`-based loops only when you need custom logic — for a plain membership check, the built-in method is simpler and already correct.

### Level 3 — Advanced

Same user-lookup system, now with a custom `User` class that needs its own `.equals()` override to support meaningful content-based comparison (e.g., in a `HashSet` or when checking "is this the same user record"), following the standard `equals`/`hashCode` contract.

```java
import java.util.*;

public class EqualityAdvanced {

    static class User {
        final int id;
        final String name;

        User(int id, String name) { this.id = id; this.name = name; }

        @Override
        public boolean equals(Object other) {
            if (this == other) return true;               // identity shortcut: same object is always equal to itself
            if (!(other instanceof User)) return false;     // must be a User to be equal
            User that = (User) other;
            return this.id == that.id && this.name.equals(that.name);  // compare all meaningful fields
        }

        @Override
        public int hashCode() {
            return Objects.hash(id, name);   // MUST be overridden alongside equals, or HashSet/HashMap break
        }

        @Override
        public String toString() { return "User(" + id + ", " + name + ")"; }
    }

    public static void main(String[] args) {
        User u1 = new User(1, "Alice");
        User u2 = new User(1, "Alice");   // same content, DIFFERENT object

        System.out.println("u1 == u2:       " + (u1 == u2));         // false — different objects
        System.out.println("u1.equals(u2):  " + u1.equals(u2));       // true — content matches, thanks to the override

        // Without overriding equals/hashCode, a HashSet would treat u1 and u2 as distinct entries.
        // With the override, the set correctly recognizes them as duplicates.
        Set<User> users = new HashSet<>();
        users.add(u1);
        users.add(u2);
        System.out.println("HashSet size (should be 1, not 2): " + users.size());

        // Demonstrating why hashCode must be consistent with equals
        System.out.println("u1.hashCode() == u2.hashCode(): " + (u1.hashCode() == u2.hashCode()));
    }
}
```

**How to run:** `java EqualityAdvanced.java`

By default, a class inherits `Object.equals`, which is defined purely in terms of `==` (reference identity) — without the override, `u1.equals(u2)` would be `false` even though both `User` objects represent "the same" logical user. The overridden `equals` first checks `this == other` as a fast path (an object is always equal to itself), then verifies the type, then compares every field that defines logical equality. `hashCode` is overridden alongside it because Java's contract requires that equal objects (per `.equals()`) must produce the same `hashCode()` — `HashSet` and `HashMap` use `hashCode()` to decide which bucket to look in *before* calling `.equals()` to confirm a match, so if two "equal" objects had different hash codes, the set could store both as if they were distinct, silently violating the "no duplicates" guarantee a `Set` is supposed to provide.

## 6. Walkthrough

Trace `users.add(u2)` given `users` already contains `u1` (both `User(1, "Alice")` but different objects):

**Compute `u2`'s hash code.** `HashSet.add` first calls `u2.hashCode()`, which (via `Objects.hash(id, name)`) computes a hash based on `id=1` and `name="Alice"`. Because `u1` has the identical `id` and `name`, `u1.hashCode()` produces the *same* value.

**Locate the bucket.** The `HashSet` (backed internally by a `HashMap`) uses that hash value to find which internal bucket `u2` would belong in — since the hash codes match, `u2` is directed to the *same* bucket where `u1` was already stored.

**Check for an existing equal element.** Within that bucket, `HashSet.add` calls `.equals()` between the candidate (`u2`) and each existing entry (`u1`). `u2.equals(u1)` runs the overridden logic: `id == id` (`1 == 1`, true) and `name.equals(name)` (`"Alice".equals("Alice")`, true) — overall `true`.

**Reject the duplicate.** Because an equal element (`u1`) was already found in that bucket, `HashSet.add` does *not* insert `u2` — the set's size remains `1`.

```
u2.hashCode() -----> matches u1.hashCode() -----> same bucket
                                                        |
                                                        v
                                    bucket contains u1; check u2.equals(u1)?
                                                        |
                                                       yes
                                                        |
                                                        v
                                          u2 rejected as a duplicate; size stays 1
```

**If `hashCode` had not been overridden.** `u1` and `u2` would inherit `Object.hashCode()`, which is typically derived from the object's memory address/identity and would very likely differ between the two distinct objects — `u2` would land in a *different* bucket from `u1`, `HashSet.add` would never even attempt to compare it against `u1` with `.equals()`, and both objects would be stored, making the set's size `2` despite `u1.equals(u2)` being `true`. This is exactly why the contract requires overriding both together.

## 7. Gotchas & takeaways

> **`==` on boxed wrapper types (`Integer`, `Long`, etc.) compares object identity, and Java only guarantees caching (and therefore `==` "working by accident") for small values, typically `-128` to `127` for `Integer`.** Always use `.equals()` (or unbox to a primitive first) to compare boxed numeric values reliably.

> **Overriding `equals()` without also overriding `hashCode()` (or vice versa) breaks hash-based collections (`HashSet`, `HashMap`).** The contract requires that equal objects produce equal hash codes — violating it can cause silent duplicate entries or failed lookups.

- `==` compares primitive values directly, but compares reference-type operands by identity (same object), not content.
- Use `.equals()` to compare the *content* of objects, including `String`s and boxed wrapper types.
- `==` is correct and idiomatic for `enum` comparisons, since enum constants are guaranteed singletons, and for deliberate identity checks (e.g., "is this the exact same cached instance").
- When overriding `equals()` on a custom class, always override `hashCode()` too, keeping both consistent with the same set of fields.
