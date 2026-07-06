---
card: java
gi: 295
slug: enumeration-interface
title: Enumeration interface
---

## 1. What it is

`Enumeration` is Java's original, pre-1.2 interface for stepping through a sequence of elements one at a time, defining exactly two methods: `hasMoreElements()` and `nextElement()`. It is the direct ancestor of the modern `Iterator` interface, and legacy classes like `Vector`, `Hashtable`, and `StringTokenizer` still expose it.

```java
import java.util.Enumeration;
import java.util.Vector;

public class EnumerationDemo {
    public static void main(String[] args) {
        Vector<String> names = new Vector<>();
        names.add("Alice");
        names.add("Bob");

        Enumeration<String> e = names.elements();
        while (e.hasMoreElements()) {
            System.out.println(e.nextElement());
        }
    }
}
```

`hasMoreElements()` checks whether another element remains; `nextElement()` returns it and advances — the same two-step pattern as `Iterator`'s `hasNext()`/`next()`, just under older names.

## 2. Why & when

`Enumeration` was Java's answer to "how do I walk through a collection's elements" before the Collections Framework (and `Iterator`) existed in Java 1.2. It solved the immediate need for sequential, read-only traversal.

- **Legacy traversal** — code written against `Vector`, `Hashtable`, or `StringTokenizer` before 1.2 (or maintained since) uses `Enumeration` for iteration.
- **Read-only by design** — unlike `Iterator`, `Enumeration` has no `remove()` method, so it cannot be used to delete elements from the underlying collection while iterating.
- **Interoperability** — `Collections.enumeration(collection)` can wrap a modern collection as an `Enumeration` for passing to old APIs that still expect one, and `Collections.list(enumeration)` converts the other direction.

For new code, always prefer `Iterator` (via the `Iterable` interface and `for-each` loops) — it supports safe removal during iteration and is what virtually every modern API expects. `Enumeration` is worth recognizing when reading legacy code, not for writing new code.

## 3. Core concept

```java
import java.util.Enumeration;
import java.util.Vector;

public class EnumerationCore {
    public static void main(String[] args) {
        Vector<Integer> numbers = new Vector<>();
        for (int i = 1; i <= 3; i++) numbers.add(i);

        Enumeration<Integer> e = numbers.elements();
        int sum = 0;
        while (e.hasMoreElements()) {
            sum += e.nextElement();
        }
        System.out.println("Sum: " + sum);
    }
}
```

Each `nextElement()` call both returns the current element and advances the internal cursor, so the `while (e.hasMoreElements())` loop terminates naturally once the cursor passes the last element — the same pattern every `Enumeration` consumer follows.

## 4. Diagram

<svg viewBox="0 0 600 140" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Enumeration and Iterator both expose a has-more check and a next-element call, but only Iterator adds a remove method">
  <rect x="8" y="8" width="584" height="124" rx="8" fill="#0d1117"/>
  <rect x="30" y="30" width="250" height="80" rx="6" fill="#1c2430" stroke="#8b949e"/>
  <text x="155" y="52" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="monospace">Enumeration</text>
  <text x="155" y="72" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">hasMoreElements()</text>
  <text x="155" y="88" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">nextElement()</text>

  <rect x="320" y="30" width="250" height="80" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="445" y="52" fill="#6db33f" font-size="12" text-anchor="middle" font-family="monospace">Iterator</text>
  <text x="445" y="72" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">hasNext() / next()</text>
  <text x="445" y="88" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">remove()  &lt;- new</text>
</svg>

Same two-step traversal pattern; `Iterator` adds the ability to remove the current element safely.

## 5. Runnable example

Scenario: walking a `Vector` of pending tasks, evolved from a basic `Enumeration` print loop into a comparison showing why `Enumeration` cannot safely remove elements, fixed with `Iterator`.

### Level 1 — Basic

```java
import java.util.Enumeration;
import java.util.Vector;

public class EnumerationBasic {
    public static void main(String[] args) {
        Vector<String> tasks = new Vector<>();
        tasks.add("send report");
        tasks.add("review PR");
        tasks.add("update docs");

        Enumeration<String> e = tasks.elements();
        while (e.hasMoreElements()) {
            System.out.println("Task: " + e.nextElement());
        }
    }
}
```

**How to run:** `java EnumerationBasic.java`

Straightforward read-only traversal, printing each task in order via the legacy `Enumeration` API.

### Level 2 — Intermediate

Same task list, now converting the `Enumeration` to a modern `List` using `Collections.list`, so it can be processed with `Iterator`-based tools like `removeIf`.

```java
import java.util.Collections;
import java.util.Enumeration;
import java.util.List;
import java.util.Vector;

public class EnumerationIntermediate {
    public static void main(String[] args) {
        Vector<String> tasks = new Vector<>();
        tasks.add("send report");
        tasks.add("review PR");
        tasks.add("update docs");

        Enumeration<String> e = tasks.elements();
        List<String> asList = Collections.list(e); // bridges legacy Enumeration to a modern List

        asList.removeIf(task -> task.startsWith("review")); // Iterator-based removal, safe
        System.out.println(asList);
    }
}
```

**How to run:** `java EnumerationIntermediate.java`

`Collections.list(e)` drains the `Enumeration` into a brand-new `ArrayList`, after which `removeIf` (built on `Iterator.remove()` internally) can safely delete matching elements — something impossible on the `Enumeration` itself.

### Level 3 — Advanced

Same task list, now demonstrating precisely why `Enumeration` has no removal method: attempting to remove from the *underlying* `Vector` while an `Enumeration` is mid-traversal corrupts the enumeration's expectations, contrasted with `Iterator`'s safe `remove()` on the same `Vector`.

```java
import java.util.Enumeration;
import java.util.Iterator;
import java.util.Vector;

public class EnumerationAdvanced {
    public static void main(String[] args) {
        Vector<String> tasks = new Vector<>();
        tasks.add("send report");
        tasks.add("review PR");
        tasks.add("update docs");

        // Using Iterator (modern, safe): remove "review PR" while iterating.
        Iterator<String> it = tasks.iterator();
        while (it.hasNext()) {
            String task = it.next();
            if (task.startsWith("review")) {
                it.remove(); // safe: Iterator.remove() updates internal state correctly
            }
        }
        System.out.println("After Iterator-based removal: " + tasks);

        // Enumeration has NO remove() method at all -- the interface simply doesn't offer one,
        // so the only way to "remove while enumerating" would be mutating the Vector directly,
        // which is unsafe and not shown here because Enumeration offers no supported way to do it.
        Enumeration<String> e = tasks.elements();
        System.out.print("Remaining via Enumeration: ");
        while (e.hasMoreElements()) {
            System.out.print(e.nextElement() + " ");
        }
        System.out.println();
    }
}
```

**How to run:** `java EnumerationAdvanced.java`

`Iterator.remove()` is a first-class, safe operation because `Iterator` was designed with mutation-during-traversal in mind; `Enumeration` was not — it exposes no `remove()` at all, forcing any legacy code that needs to filter a collection while walking it to either collect indices to remove afterward, or (as shown here) simply use `Iterator` instead once removal is needed.

## 6. Walkthrough

Trace `EnumerationAdvanced.main` step by step.

**Setup.** `tasks` is populated with three entries: `"send report"`, `"review PR"`, `"update docs"`.

**`Iterator<String> it = tasks.iterator()`.** `Vector` (via its `List` interface) hands back a modern `Iterator` positioned before the first element.

**First `it.next()`.** Returns `"send report"`, advancing the cursor. `task.startsWith("review")` is `false`, so nothing happens.

**Second `it.next()`.** Returns `"review PR"`. `task.startsWith("review")` is `true`, so `it.remove()` is called — this deletes `"review PR"` from the underlying `tasks` `Vector` *and* correctly updates the iterator's internal cursor so the next call to `next()` won't skip or repeat an element.

**Third `it.next()`.** Returns `"update docs"` (the loop correctly reaches this despite the removal above). Not a match, nothing happens. `it.hasNext()` now returns `false`, ending the loop.

**First print.** `tasks` now contains exactly `["send report", "update docs"]` — the removal took effect correctly, with no corruption.

**`Enumeration<String> e = tasks.elements()`.** A fresh `Enumeration` is obtained over the *already-modified* `tasks` `Vector` — it has no knowledge of, or ability to perform, removal; it simply walks whatever `tasks` currently contains.

**The `while (e.hasMoreElements())` loop.** Prints `"send report"` then `"update docs"` — the two remaining tasks, confirming the `Iterator`-based removal from the previous step is reflected here, even though `Enumeration` itself played no part in the removal.

```
tasks initially:      [send report, review PR, update docs]

Iterator walk:
  next() -> "send report"   (no match)
  next() -> "review PR"     (match) -> it.remove()  => tasks: [send report, update docs]
  next() -> "update docs"   (no match)
  hasNext() -> false

Enumeration walk (over the now-modified tasks):
  "send report" "update docs"
```

**Output:**
```
After Iterator-based removal: [send report, update docs]
Remaining via Enumeration: send report update docs 
```

## 7. Gotchas & takeaways

> `Enumeration` has no `remove()` method — this is not an oversight but a deliberate limitation of an interface designed before "safe removal during iteration" was considered a first-class concern. If you need to filter a collection while walking it, use `Iterator` (or `Collection.removeIf`), never `Enumeration`.

> Mutating the underlying `Vector` or `Hashtable` directly (e.g. calling `vector.remove(x)`) while a separate `Enumeration` over it is still in progress is unsafe and can produce inconsistent results — `Enumeration`, unlike `Iterator`, does not reliably detect concurrent structural modification with a `ConcurrentModificationException`, so bugs here can be silent.

- `Enumeration` is the pre-1.2 ancestor of `Iterator`: `hasMoreElements()`/`nextElement()` mirror `hasNext()`/`next()`.
- It has no `remove()` — traversal only, no safe way to delete elements mid-iteration.
- `Collections.list(enumeration)` and `Collections.enumeration(collection)` bridge between old and new APIs in either direction.
- For new code, always use `Iterator` (typically via a `for-each` loop) — it supports safe removal and is what modern APIs expect.
