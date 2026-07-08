---
card: java
gi: 478
slug: instance-method-of-arbitrary-object-class-instancemethod
title: 'Instance method of arbitrary object (Class::instanceMethod)'
---

## 1. What it is

A method reference written `ClassName::instanceMethod` — a class name, not a specific object — is shorthand for a lambda where the **first parameter becomes the receiver** the method is called on, and any remaining parameters are forwarded as the method's own arguments. `String::toUpperCase` means `s -> s.toUpperCase()`: the lambda's one parameter, `s`, becomes the object `toUpperCase()` is called *on*, not an argument passed *to* it. This is a genuinely different mechanism from the previous topic's `object::instanceMethod`, even though the syntax looks similar.

## 2. Why & when

This form exists for exactly the situation `Stream.map`, `Comparator`, and similar APIs need constantly: "call this instance method on each element I'm given," where "each element" varies with every invocation, not a single fixed object captured up front. `list.stream().map(String::toUpperCase)` needs a *different* receiver for every element in the stream — the previous topic's bound form (`someString::toUpperCase`) couldn't do this at all, since it's permanently bound to one specific string.

You reach for `ClassName::instanceMethod` whenever a lambda's whole job is "call this instance method on my first parameter," most commonly inside `Stream.map`/`filter`/`sorted` and similar operations processing a sequence of objects one at a time: `String::toUpperCase`, `String::isEmpty`, `Object::toString`. The distinguishing test: if the lambda you'd otherwise write is `x -> x.someMethod(...)` — where `x`, the lambda's own parameter, is the receiver — this form applies; if instead it's `x -> someFixedObject.someMethod(x)`, you need the bound form from the previous topic instead.

## 3. Core concept

```java
import java.util.*;
import java.util.stream.*;

// String::toUpperCase means: s -> s.toUpperCase() -- 's' is the RECEIVER, not an argument.
Function<String, String> upper = String::toUpperCase;
System.out.println(upper.apply("hello")); // "HELLO"

// With TWO parameters: String::compareTo means (a, b) -> a.compareTo(b)
// -- the FIRST parameter is the receiver, the SECOND is forwarded as compareTo's argument.
Comparator<String> natural = String::compareTo;
System.out.println(natural.compare("apple", "banana")); // negative: "apple" < "banana"

List<String> words = List.of("Hello", "World");
List<String> upperWords = words.stream().map(String::toUpperCase).collect(Collectors.toList());
```

The receiver is supplied fresh on every call, from whatever element is currently being processed — unlike the bound form, where the receiver is fixed once and shared across all calls.

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="With Class colon colon instanceMethod, the first parameter passed to the lambda becomes the receiver the method is called on, and it varies on every call">
  <rect x="8" y="8" width="624" height="134" rx="8" fill="#0d1117"/>
  <text x="20" y="28" fill="#8b949e" font-size="11" font-family="sans-serif">String::toUpperCase  ==  s -&gt; s.toUpperCase()</text>
  <rect x="20" y="40" width="90" height="30" rx="4" fill="#1c2430" stroke="#79c0ff"/><text x="65" y="60" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="monospace">"hello"</text>
  <text x="130" y="60" fill="#8b949e" font-size="10" font-family="sans-serif">-&gt; becomes RECEIVER -&gt;</text>
  <rect x="280" y="40" width="140" height="30" rx="4" fill="#1c2430" stroke="#6db33f"/><text x="350" y="60" fill="#6db33f" font-size="10" text-anchor="middle" font-family="monospace">"hello".toUpperCase()</text>

  <text x="20" y="100" fill="#8b949e" font-size="11" font-family="sans-serif">Each stream element supplies a DIFFERENT receiver -- unlike a bound reference's fixed one.</text>
  <rect x="20" y="110" width="90" height="26" rx="4" fill="#1c2430" stroke="#79c0ff"/><text x="65" y="128" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="monospace">"Hello"</text>
  <rect x="130" y="110" width="90" height="26" rx="4" fill="#1c2430" stroke="#79c0ff"/><text x="175" y="128" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="monospace">"World"</text>
</svg>

The parameter itself becomes the receiver — a fresh one arrives with every call, not a fixed object captured once.

## 5. Runnable example

Scenario: cleaning and comparing a list of usernames — evolved from a single-parameter unbound reference used with `Stream.map`, through a two-parameter unbound reference used as a `Comparator` (first parameter is the receiver, second is the argument), to combining an unbound reference with a bound one in the same pipeline to highlight the difference between them.

### Level 1 — Basic

```java
import java.util.*;
import java.util.stream.*;

public class UnboundMethodRefBasic {
    public static void main(String[] args) {
        List<String> usernames = List.of("  Alice  ", "  BOB  ", "  charlie  ");

        // String::trim: s -> s.trim() -- each element becomes its own receiver.
        List<String> trimmed = usernames.stream()
                .map(String::trim)
                .collect(Collectors.toList());

        System.out.println(trimmed);
    }
}
```

**How to run:** `java UnboundMethodRefBasic.java`

Expected output:
```
[Alice, BOB, charlie]
```

`String::trim` is unbound — there's no single fixed string it belongs to. Each element `map` passes in becomes the receiver for its own `trim()` call: `"  Alice  ".trim()`, `"  BOB  ".trim()`, `"  charlie  ".trim()`, each independently.

### Level 2 — Intermediate

```java
import java.util.*;
import java.util.stream.*;

public class UnboundMethodRefComparator {
    public static void main(String[] args) {
        List<String> usernames = new ArrayList<>(List.of("charlie", "alice", "bob"));

        // String::compareToIgnoreCase, as a Comparator<String>:
        // (a, b) -> a.compareToIgnoreCase(b) -- 'a' is the receiver, 'b' is the argument.
        usernames.sort(String::compareToIgnoreCase);

        System.out.println(usernames);
    }
}
```

**How to run:** `java UnboundMethodRefComparator.java`

Expected output:
```
[alice, bob, charlie]
```

The real-world concern this adds: with **two** parameters expected (`Comparator<String>.compare(String, String)`), `String::compareToIgnoreCase` maps the **first** parameter to the receiver and the **second** to `compareToIgnoreCase`'s own argument — `(a, b) -> a.compareToIgnoreCase(b)`. This is the same "first parameter becomes receiver" rule as the single-parameter case, just with one extra forwarded argument.

### Level 3 — Advanced

```java
import java.util.*;
import java.util.function.*;
import java.util.stream.*;

public class UnboundVsBoundComparison {
    public static void main(String[] args) {
        List<String> usernames = List.of("  Alice  ", "  bob  ", "  Charlie  ");
        String bannedName = "alice"; // a FIXED value to compare every element against

        // UNBOUND: String::trim -- each element is its OWN receiver, varies per call.
        Function<String, String> cleaner = String::trim;

        // BOUND: bannedName::equalsIgnoreCase -- bannedName is a FIXED receiver, same every call.
        Predicate<String> isBanned = bannedName::equalsIgnoreCase;

        for (String raw : usernames) {
            String cleaned = cleaner.apply(raw);
            System.out.println(cleaned + " banned: " + isBanned.test(cleaned));
        }
    }
}
```

**How to run:** `java UnboundVsBoundComparison.java`

Expected output:
```
Alice banned: true
bob banned: false
Charlie banned: false
```

This contrasts both forms directly in one program: `cleaner` (`String::trim`, unbound) takes a *different* receiver — whichever string is passed in — on every call, exactly as in the earlier examples. `isBanned` (`bannedName::equalsIgnoreCase`, bound, from the previous topic) always calls `equalsIgnoreCase` **on** the same fixed `bannedName` string, comparing it against whatever argument is passed — the receiver never changes across all three loop iterations, only the argument does.

## 6. Walkthrough

Execution starts in `main` of the Level 3 example. `usernames` holds three raw, padded strings. `bannedName` is the fixed string `"alice"`. `cleaner` is the unbound reference `String::trim`; `isBanned` is the bound reference `bannedName::equalsIgnoreCase`.

The loop processes `"  Alice  "` first. `cleaner.apply(raw)` calls `String::trim` with `raw` as the receiver: `"  Alice  ".trim()` produces `"Alice"`. `isBanned.test("Alice")` calls `bannedName.equalsIgnoreCase("Alice")` — here `bannedName` (`"alice"`) is the fixed receiver, and `"Alice"` (the loop's cleaned value) is the forwarded argument. `"alice".equalsIgnoreCase("Alice")` compares the two strings ignoring case, and since they're identical except for the leading letter's case, this returns `true`.

The loop then processes `"  bob  "`: `cleaner.apply(raw)` trims it to `"bob"`. `isBanned.test("bob")` calls `bannedName.equalsIgnoreCase("bob")`, i.e. `"alice".equalsIgnoreCase("bob")`, which is `false` — the two strings are simply different.

Finally, `"  Charlie  "` trims to `"Charlie"`. `isBanned.test("Charlie")` calls `"alice".equalsIgnoreCase("Charlie")`, also `false`.

```
receiver (fixed): "alice"
argument (varies): "Alice", "bob", "Charlie"
"alice".equalsIgnoreCase("Alice")   -> true
"alice".equalsIgnoreCase("bob")     -> false
"alice".equalsIgnoreCase("Charlie") -> false
```

Only the first username is flagged as banned, since it's the only cleaned value that matches `"alice"` case-insensitively. Notice that `isBanned`'s receiver (`bannedName`, `"alice"`) never changes across all three loop iterations — only the argument passed to `equalsIgnoreCase` does — which is exactly the bound-reference behavior the example contrasts with `cleaner`'s unbound, per-element-receiver behavior, where `String::trim`'s receiver is a *different* string on every call.

## 7. Gotchas & takeaways

> Confusing `object::instanceMethod` (bound, fixed receiver) with `ClassName::instanceMethod` (unbound, receiver is the first parameter) is one of the most common method-reference mistakes — they can look deceptively similar in code review, especially when a variable name and a class name are easy to mix up visually. The reliable test: if what precedes `::` is a specific variable holding one object, it's bound; if it's a type name, the first parameter becomes the receiver instead.
>
> The `equalsIgnoreCase` prefix example above is also a reminder to verify assumptions about a method's actual semantics (whole-string equality, not prefix matching) rather than trust a variable's name — `bannedPrefix` here does not perform prefix matching at all, which is exactly the kind of mismatch worth catching with a test before relying on it.

- `ClassName::instanceMethod` supplies the receiver from the lambda's **first** parameter — `s -> s.someMethod(...)` — with any remaining parameters forwarded as that method's own arguments.
- This is the form `Stream.map`, `Stream.filter`, and `List.sort` reach for constantly, since each element supplies its own receiver rather than sharing one fixed object.
- A two-parameter target (like `Comparator<T>.compare(T, T)`) maps its first parameter to the receiver and its second to the referenced method's own argument — `String::compareTo` becomes `(a, b) -> a.compareTo(b)`.
- Distinguish this clearly from the bound form (`object::instanceMethod`, previous topic): unbound gets a fresh receiver every call; bound always uses the same, fixed receiver captured when the reference was created.
- When in doubt about what a method reference actually does, expand it back into the equivalent explicit lambda mentally (or in a comment) — it removes any ambiguity about which parameter plays which role.
