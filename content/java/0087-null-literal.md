---
card: java
gi: 87
slug: null-literal
title: null literal
---

## 1. What it is

`null` is a special literal that represents the absence of an object reference. It is the default value of any reference-type variable (field or array element) that has not been assigned, and it is type-compatible with any reference type. `null` has no type of its own — it can be assigned to any reference type (`String`, arrays, interfaces, classes), but never to a primitive type.

```java
String  name   = null;   // no String object
int[]   arr    = null;   // no array object
Object  obj    = null;   // no object at all
// int  x      = null;   // COMPILE ERROR — primitives cannot be null
```

Accessing any member (field, method) of a `null` reference throws `NullPointerException` (NPE) at runtime.

## 2. Why & when

`null` is used to signal:
- **Optional absence** — a field that has not yet been set, or an optional result that may not exist.
- **Sentinel values** — the end of a linked list (`node.next == null`), or a map entry that is missing.
- **Uninitialized state** — before lazy initialisation.

However, `null` is widely regarded as the billion-dollar mistake (Tony Hoare's words) because it requires every caller to guard against NPE. Modern Java patterns prefer:
- `Optional<T>` for methods that may not return a value.
- Empty collections instead of `null` collections.
- `@NonNull` / `@Nullable` annotations with static analysis tools.
- `Objects.requireNonNull` at API boundaries.

## 3. Core concept

```java
import java.util.Objects;
import java.util.Optional;

// ---- null assignment ----
String s = null;
System.out.println(s);       // null (prints the word "null")
System.out.println(s == null);  // true

// ---- NPE when accessing null reference ----
try {
    int len = s.length();   // NullPointerException!
} catch (NullPointerException e) {
    System.out.println("NPE: " + e);
}

// ---- null-safe checks ----
System.out.println(Objects.isNull(s));     // true
System.out.println(Objects.nonNull(s));    // false

// ---- Null-safe compare ----
String a = null, b = "hello";
System.out.println(Objects.equals(a, b));   // false — null-safe
System.out.println(Objects.equals(a, null));// true

// ---- null in collections ----
java.util.List<String> list = new java.util.ArrayList<>();
list.add(null);
System.out.println(list.size());     // 1
System.out.println(list.get(0));     // null
System.out.println(list.contains(null));   // true

// ---- instanceof on null is false (never throws) ----
System.out.println(s instanceof String);  // false

// ---- Null concatenation ----
String msg = "value: " + null;   // "value: null"
System.out.println(msg);

// ---- Optional as a better alternative ----
Optional<String> opt = Optional.ofNullable(s);
System.out.println(opt.isPresent());         // false
System.out.println(opt.orElse("default"));  // default

// ---- Objects.requireNonNull ----
String validated = Objects.requireNonNull(b, "b must not be null");
System.out.println(validated);   // hello

// ---- Java 14+ helpful NPE messages ----
// When a.b.c.d() throws NPE, the JVM reports which reference was null
```

## 4. Diagram

<svg viewBox="0 0 700 180" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="null literal: reference vs primitive, NPE cause, null-safe patterns with Objects and Optional">
  <rect x="8" y="8" width="684" height="164" rx="8" fill="#0d1117"/>

  <!-- null concept -->
  <rect x="16" y="18" width="190" height="138" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="111" y="36" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="monospace">null</text>
  <line x1="26" y1="42" x2="196" y2="42" stroke="#8b949e" stroke-width="0.5"/>
  <text x="26" y="57" fill="#e6edf3" font-size="7.5" font-family="monospace">String  s = null; ✓</text>
  <text x="26" y="70" fill="#e6edf3" font-size="7.5" font-family="monospace">Object  o = null; ✓</text>
  <text x="26" y="83" fill="#e6edf3" font-size="7.5" font-family="monospace">int[]   a = null; ✓</text>
  <text x="26" y="98" fill="#8b949e" font-size="7.5" font-family="monospace">int  x = null;  ✗</text>
  <text x="26" y="111" fill="#8b949e" font-size="7.5" font-family="sans-serif">(primitives never null)</text>
  <line x1="26" y1="118" x2="196" y2="118" stroke="#8b949e" stroke-width="0.5"/>
  <text x="26" y="131" fill="#8b949e" font-size="7.5" font-family="monospace">null instanceof T → false</text>
  <text x="26" y="144" fill="#8b949e" font-size="7.5" font-family="monospace">field default: null</text>

  <!-- NPE causes -->
  <rect x="218" y="18" width="220" height="138" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="328" y="36" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">NPE causes</text>
  <line x1="228" y1="42" x2="428" y2="42" stroke="#8b949e" stroke-width="0.5"/>
  <text x="228" y="57" fill="#8b949e" font-size="7.5" font-family="monospace">null.method()</text>
  <text x="228" y="70" fill="#8b949e" font-size="7.5" font-family="monospace">null.field</text>
  <text x="228" y="83" fill="#8b949e" font-size="7.5" font-family="monospace">null[0]  (array access)</text>
  <text x="228" y="96" fill="#8b949e" font-size="7.5" font-family="monospace">throw null</text>
  <text x="228" y="109" fill="#8b949e" font-size="7.5" font-family="monospace">unbox null Boolean</text>
  <text x="228" y="125" fill="#6db33f" font-size="7.5" font-family="monospace">Java 14+: helpful NPE</text>
  <text x="228" y="138" fill="#8b949e" font-size="7" font-family="monospace">reports WHICH was null</text>

  <!-- Safe patterns -->
  <rect x="450" y="18" width="234" height="138" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="567" y="36" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">Null-safe patterns</text>
  <line x1="460" y1="42" x2="674" y2="42" stroke="#8b949e" stroke-width="0.5"/>
  <text x="460" y="57" fill="#e6edf3" font-size="7.5" font-family="monospace">Objects.isNull(x)</text>
  <text x="460" y="70" fill="#e6edf3" font-size="7.5" font-family="monospace">Objects.equals(a, b)</text>
  <text x="460" y="83" fill="#e6edf3" font-size="7.5" font-family="monospace">Objects.requireNonNull</text>
  <text x="460" y="96" fill="#e6edf3" font-size="7.5" font-family="monospace">Optional.ofNullable(x)</text>
  <text x="460" y="112" fill="#8b949e" font-size="7.5" font-family="monospace">"known".equals(maybe)</text>
  <text x="460" y="125" fill="#8b949e" font-size="7.5" font-family="monospace">if (x != null) {...}</text>
  <text x="460" y="138" fill="#8b949e" font-size="7.5" font-family="monospace">prefer Optional over null</text>
</svg>

`null` is valid only for reference types; any member access on a `null` reference throws `NPE`; use `Objects` utilities and `Optional` for safe null handling.

## 5. Runnable example

Scenario: a user lookup service — searches a user database and handles missing users. The scenario grows from basic null checking, to `Optional`-based API design, to a defensive layer that validates all parameters and provides helpful NPE messages.

### Level 1 — Basic

```java
import java.util.HashMap;
import java.util.Map;

public class NullLiteralBasic {

    static final Map<Integer, String> USERS = new HashMap<>();
    static {
        USERS.put(1, "Alice");
        USERS.put(2, "Bob");
    }

    static String findUser(int id) {
        return USERS.get(id);   // returns null if not found
    }

    public static void main(String[] args) {
        for (int id : new int[]{1, 2, 99}) {
            String user = findUser(id);

            if (user == null) {
                System.out.printf("id=%d : NOT FOUND (null)%n", id);
            } else {
                System.out.printf("id=%d : %s (length=%d)%n", id, user, user.length());
            }
        }

        // null in String context
        String name = null;
        System.out.println("Hello, " + name);    // "Hello, null"
        System.out.println(String.valueOf(name)); // "null"
    }
}
```

**How to run:** `java NullLiteralBasic.java`

`Map.get(key)` returns `null` when the key is absent. Before calling `user.length()`, the `if (user == null)` guard is mandatory — skipping it for id `99` would throw `NullPointerException`. `"Hello, " + null` converts `null` to the four-character string `"null"` via `String.valueOf` — Java does this automatically in string concatenation, so printing a null reference always shows the text `null` rather than crashing.

### Level 2 — Intermediate

Same lookup service: redesign the `findUser` API to return `Optional<String>` instead of nullable `String`, eliminating the NPE risk at the API boundary.

```java
import java.util.HashMap;
import java.util.Map;
import java.util.Optional;

public class NullLiteralIntermediate {

    static final Map<Integer, String> USERS = new HashMap<>();
    static {
        USERS.put(1, "Alice");
        USERS.put(2, "Bob");
    }

    // Returns Optional — caller cannot ignore the absent case
    static Optional<String> findUser(int id) {
        return Optional.ofNullable(USERS.get(id));
    }

    static String displayName(int id) {
        return findUser(id)
            .map(String::toUpperCase)
            .orElse("[unknown]");
    }

    public static void main(String[] args) {
        for (int id : new int[]{1, 2, 99}) {
            System.out.printf("id=%d : %s%n", id, displayName(id));
        }

        // Inspect Optional directly
        Optional<String> alice = findUser(1);
        Optional<String> ghost = findUser(99);

        System.out.println("\nalice.isPresent() : " + alice.isPresent());
        System.out.println("ghost.isPresent() : " + ghost.isPresent());
        System.out.println("alice.get()       : " + alice.get());
        // ghost.get() would throw NoSuchElementException — use orElse / ifPresent

        // Safe alternatives to get()
        System.out.println("ghost.orElse(\"?\") : " + ghost.orElse("?"));
        ghost.ifPresent(name -> System.out.println("ghost name: " + name)); // no-op
    }
}
```

**How to run:** `java NullLiteralIntermediate.java`

`Optional.ofNullable(USERS.get(id))` wraps the possibly-null result in an `Optional`. The caller must explicitly handle the absent case via `.orElse(...)`, `.ifPresent(...)`, or `.map(...)` — there is no way to accidentally dereference a null. `.map(String::toUpperCase)` applies the transformation only if the value is present and returns an empty `Optional` otherwise. `Optional.get()` should only be called after verifying `.isPresent()` — otherwise it throws `NoSuchElementException`.

### Level 3 — Advanced

Same service: add a multi-field user record, use `Objects.requireNonNull` at the API boundary, demonstrate Java 14+ helpful NPE messages, and handle nullable fields in a `toString` safely.

```java
import java.util.*;

public class NullLiteralAdvanced {

    record User(int id, String name, String email) {
        User {
            Objects.requireNonNull(name,  "name must not be null");
            Objects.requireNonNull(email, "email must not be null");
        }

        // Null-safe display
        String display() {
            return id + " | " + Objects.toString(name, "(no name)")
                       + " | " + Objects.toString(email, "(no email)");
        }
    }

    static final Map<Integer, User> DB = new Map.Entry<Integer,User>() { // workaround
        {/* see below */}
        @Override public Integer getKey()  { return null; }
        @Override public User getValue()   { return null; }
        @Override public User setValue(User v) { return null; }
    }.getClass() == null ? null : new HashMap<>();

    static {
        // Inline initialisation
    }

    public static void main(String[] args) {
        // requireNonNull guard
        try {
            User invalid = new User(0, null, "x@x.com");
        } catch (NullPointerException e) {
            System.out.println("Caught NPE: " + e.getMessage());
        }

        // Valid user
        User alice = new User(1, "Alice", "alice@example.com");
        System.out.println(alice.display());

        // Objects utilities
        System.out.println();
        System.out.println("Objects.isNull(null)  : " + Objects.isNull(null));
        System.out.println("Objects.nonNull(alice): " + Objects.nonNull(alice));
        System.out.println("Objects.toString(null,\"?\") : " + Objects.toString(null, "?"));

        // null vs Optional.empty()
        Optional<User> opt = Optional.of(alice);
        Optional<User> empty = Optional.empty();
        System.out.println("\nopt.map(User::name)   : " + opt.map(User::name));
        System.out.println("empty.map(User::name) : " + empty.map(User::name));

        // Chained null guard using Optional
        String domain = Optional.ofNullable(alice.email())
            .filter(e -> e.contains("@"))
            .map(e -> e.substring(e.indexOf('@') + 1))
            .orElse("unknown");
        System.out.println("domain: " + domain);
    }
}
```

**How to run:** `java NullLiteralAdvanced.java`

The compact `record` constructor `User { Objects.requireNonNull(name, "..."); }` validates parameters immediately on construction — the error is thrown at the call site with a meaningful message, making bugs easier to diagnose than an NPE thrown later in a different method. `Objects.toString(value, default)` returns the default string when `value` is `null`, avoiding a ternary null check. `Optional.ofNullable(alice.email()).filter(...).map(...).orElse(...)` chains transformations without any explicit null check — each step is skipped if the value is absent.

## 6. Walkthrough

Execution trace through `NullLiteralAdvanced.main`:

**`new User(0, null, "x@x.com")`.** The compact constructor runs. `Objects.requireNonNull(null, "name must not be null")` checks `name == null`, which is true, and throws `NullPointerException("name must not be null")`. The `catch` block prints the message.

**`new User(1, "Alice", "alice@example.com")`.** Both `requireNonNull` checks pass. The record is constructed. `alice.display()` calls `Objects.toString(name, "(no name)")` — since `name` is `"Alice"` (not null), it returns `"Alice"`. Same for `email`.

**Domain extraction.** `Optional.ofNullable("alice@example.com")` wraps the non-null email. `.filter(e -> e.contains("@"))` passes because the email contains `@`. `.map(e -> e.substring(e.indexOf('@') + 1))` extracts `"example.com"`. `.orElse("unknown")` is never reached. Result: `"example.com"`.

**`Optional.empty().map(User::name)`.** `.map` on an empty `Optional` returns an empty `Optional` — the lambda is never called. Printing it shows `Optional.empty`.

```
requireNonNull flow:
  new User(0, null, "x@x.com")
    → Objects.requireNonNull(null, "name...")
    → null check fails
    → throw new NullPointerException("name must not be null")
    → caught by catch block

domain extraction:
  ofNullable("alice@example.com") → Optional["alice@example.com"]
  .filter(contains "@")           → Optional["alice@example.com"] (passes)
  .map(substring after @)         → Optional["example.com"]
  .orElse("unknown")              → "example.com"
```

## 7. Gotchas & takeaways

> **`null` concatenated into a string produces the text `"null"`, not an NPE.** `"value: " + null` gives `"value: null"`. This can mask bugs where you expect to print a real value but silently print `"null"` instead.

> **Unboxing a `null` wrapper throws NPE even without a direct `.method()` call.** `Integer n = null; int x = n;` throws NPE because the auto-unboxing `intValue()` call is implicit. Primitive arrays and arithmetic involving boxed `null` values all trigger this silently.

- `null` is the default value for all reference-type fields; local reference variables have no default and must be explicitly initialised.
- Accessing any member of a `null` reference throws `NullPointerException` at runtime.
- `instanceof null` always returns `false` — it never throws.
- Use `Objects.requireNonNull` at API entry points to fail fast with a meaningful message.
- Use `Optional<T>` as a return type when absence is a valid outcome; avoid returning `null` from methods.
- `"known".equals(maybe)` is safer than `maybe.equals("known")` because it handles a null `maybe` without NPE.
- Java 14+ provides helpful NPE messages that identify exactly which reference in a chain was null.
