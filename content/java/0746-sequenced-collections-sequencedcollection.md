---
card: java
gi: 746
slug: sequenced-collections-sequencedcollection
title: Sequenced collections (SequencedCollection)
---

## 1. What it is

**Java 21** (JEP 431) adds `SequencedCollection<E>`, a new interface that sits between `Collection` and the existing ordered types (`List`, `Deque`, `LinkedHashSet`). It represents any collection with a **well-defined encounter order** — a first element and a last element — and provides a uniform set of operations for that: `addFirst`/`addLast`, `getFirst`/`getLast`, `removeFirst`/`removeLast`, and `reversed()` (a live, reversed view of the same collection). Before this, `List` had `get(0)`/`get(size()-1)`, `Deque` had its own first/last methods with different names, and there was no common supertype expressing "this collection has an order" at all — each type reinvented the same idea with different method names or none.

## 2. Why & when

If you've ever written `list.get(list.size() - 1)` to get the last element, or reached for `Collections.reverse(list)` when you only wanted to **read** a collection backwards (not mutate it), you've felt the gap `SequencedCollection` fills. Ordered collections have always shared the concept of "first" and "last," but the JDK's type hierarchy never captured that shared concept as an interface — so generic code that wanted to work with "any ordered collection's first and last elements" had no common type to program against, and reversing a list for read-only iteration meant either a full copy or manual index math. `SequencedCollection` retrofits a common interface onto `List`, `Deque`, and `LinkedHashSet` (via [SequencedSet](0747-sequencedset-sequencedmap.md)) so code can express "give me the first," "give me the last," or "give me this backwards" the same way regardless of which concrete ordered collection it's holding.

## 3. Core concept

```java
import java.util.*;

List<String> tasks = new ArrayList<>(List.of("build", "test", "deploy"));

String first = tasks.getFirst();       // "build" — no more list.get(0)
String last = tasks.getLast();         // "deploy" — no more list.get(list.size()-1)
tasks.addLast("notify");               // append, expressed uniformly
List<String> backwards = tasks.reversed(); // live view: [notify, deploy, test, build]
```

`reversed()` returns a **view**, not a copy — changes to `tasks` are visible through `backwards`, and vice versa, just like `Collections.unmodifiableList` views work today.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="SequencedCollection sits above List, Deque, and LinkedHashSet-backed SequencedSet, giving all of them the same getFirst, getLast, and reversed operations">
  <rect x="230" y="20" width="180" height="40" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="45" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">SequencedCollection&lt;E&gt;</text>

  <line x1="270" y1="60" x2="120" y2="100" stroke="#8b949e"/>
  <line x1="320" y1="60" x2="320" y2="100" stroke="#8b949e"/>
  <line x1="370" y1="60" x2="520" y2="100" stroke="#8b949e"/>

  <rect x="40" y="100" width="160" height="36" rx="6" fill="#0f1620" stroke="#79c0ff"/>
  <text x="120" y="123" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">List (ArrayList, ...)</text>
  <rect x="240" y="100" width="160" height="36" rx="6" fill="#0f1620" stroke="#79c0ff"/>
  <text x="320" y="123" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">Deque (ArrayDeque, ...)</text>
  <rect x="440" y="100" width="160" height="36" rx="6" fill="#0f1620" stroke="#79c0ff"/>
  <text x="520" y="123" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">SequencedSet</text>

  <text x="320" y="170" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">getFirst / getLast / addFirst / addLast / removeFirst / removeLast / reversed()</text>
</svg>

*One shared interface unifies "first/last" operations across every ordered collection type.*

## 5. Runnable example

Scenario: a simple undo/redo-style task queue, growing from index-based access into full use of `SequencedCollection` operations.

### Level 1 — Basic

```java
import java.util.*;

public class TaskQueueBasic {
    public static void main(String[] args) {
        List<String> tasks = new ArrayList<>(List.of("build", "test", "deploy"));

        String first = tasks.get(0);
        String last = tasks.get(tasks.size() - 1);
        System.out.println("first=" + first + " last=" + last);

        tasks.add(0, "checkout"); // insert at front the old, error-prone way
        System.out.println(tasks);
    }
}
```

**How to run:** `java TaskQueueBasic.java` (JDK 21+, but this part works on any JDK).

This is the pre-Java-21 style: `get(0)`, `get(size() - 1)`, and `add(0, ...)` all rely on index arithmetic that's easy to get wrong (an off-by-one on an empty list throws `IndexOutOfBoundsException`).

### Level 2 — Intermediate

```java
import java.util.*;

public class TaskQueueSequenced {
    public static void main(String[] args) {
        List<String> tasks = new ArrayList<>(List.of("build", "test", "deploy"));

        String first = tasks.getFirst();
        String last = tasks.getLast();
        System.out.println("first=" + first + " last=" + last);

        tasks.addFirst("checkout");
        tasks.addLast("notify");
        System.out.println(tasks);

        List<String> reversedView = tasks.reversed();
        System.out.println("reversed view: " + reversedView);
    }
}
```

**How to run:** `java TaskQueueSequenced.java`.

The real-world concern added: `getFirst`/`getLast`/`addFirst`/`addLast` replace index arithmetic with intent-revealing names that work the same way regardless of the concrete collection type, and `reversed()` gives a **read-ready backwards view** without manually reversing or copying anything.

### Level 3 — Advanced

```java
import java.util.*;

public class TaskQueueAdvanced {
    static void printMostRecentFirst(SequencedCollection<String> log) {
        for (String entry : log.reversed()) {
            System.out.println("  " + entry);
        }
    }

    public static void main(String[] args) {
        Deque<String> auditLog = new ArrayDeque<>();
        auditLog.addLast("checkout");
        auditLog.addLast("build");
        auditLog.addLast("test");
        auditLog.addLast("deploy");

        System.out.println("most recent entries first:");
        printMostRecentFirst(auditLog);

        // live view: mutating the reversed view mutates the underlying deque
        SequencedCollection<String> reversedLog = auditLog.reversed();
        reversedLog.removeFirst(); // removes "deploy" — the LAST element of auditLog
        System.out.println("after removing most-recent entry: " + auditLog);

        auditLog.removeFirst(); // removes "checkout" — the FIRST element again
        System.out.println("after removing oldest entry: " + auditLog);
    }
}
```

**How to run:** `java TaskQueueAdvanced.java`.

This adds the production-flavored hard case: writing `printMostRecentFirst` against the **`SequencedCollection` interface itself** (not `List` or `Deque`), so it works with any sequenced collection passed in — here an `ArrayDeque` — and demonstrating that `reversed()` is a genuinely **live, mutable view**: removing from the reversed view removes from the *end* of the original, not a copy.

## 6. Walkthrough

Tracing `TaskQueueAdvanced.main`:

1. `main` builds an `ArrayDeque<String>` and appends four entries in order via `addLast`, giving `auditLog = [checkout, build, test, deploy]`.
2. `printMostRecentFirst(auditLog)` is called. The parameter type is `SequencedCollection<String>`, and `ArrayDeque` implements `Deque`, which extends `SequencedCollection` — so the call is valid without any cast or adapter.
3. Inside the method, `log.reversed()` produces a view iterating `[deploy, test, build, checkout]` — the reverse encounter order of `auditLog` — and the `for` loop prints each entry with an indent.
4. Back in `main`, `auditLog.reversed()` is called again, this time stored in `reversedLog`. This is the **same kind of view**, not a snapshot: it stays backed by `auditLog`.
5. `reversedLog.removeFirst()` removes the first element **of the reversed view**, which is `"deploy"` — the *last* element of `auditLog`. Because the view is live, this mutation is applied to the underlying deque: `auditLog` becomes `[checkout, build, test]`.
6. `auditLog.removeFirst()` then removes `auditLog`'s own first element, `"checkout"`, leaving `[build, test]`.

Expected output:
```
most recent entries first:
  deploy
  test
  build
  checkout
after removing most-recent entry: [checkout, build, test]
after removing oldest entry: [build, test]
```

## 7. Gotchas & takeaways

> **Gotcha:** `reversed()` is a **view**, not a copy — calling `.reversed()` twice in a row gets you back a view equivalent to the original, but holding onto a `reversed()` view after making unrelated structural changes to the source collection can be confusing if you forget it's live. Treat it like any other view (e.g. `Collections.unmodifiableList`): convenient for read-through or targeted first/last mutation, but not a snapshot for later comparison.

- `SequencedCollection` unifies `getFirst`/`getLast`/`addFirst`/`addLast`/`removeFirst`/`removeLast`/`reversed()` across `List`, `Deque`, and sequenced sets.
- Prefer `getFirst()`/`getLast()` over `get(0)`/`get(size()-1)` — same behavior, but they throw a clearer, purpose-built exception on an empty collection and read as intent rather than index math.
- `reversed()` gives a live view for read-only backwards iteration without copying or calling `Collections.reverse` (which mutates in place).
- Write utility methods against `SequencedCollection` (or [SequencedMap](0747-sequencedset-sequencedmap.md)) when the operation only needs first/last semantics, so callers can pass any conforming collection type.
- Existing types didn't need new classes to get this — `ArrayList`, `LinkedList`, `ArrayDeque`, and `LinkedHashSet` all retrofit `SequencedCollection` (or the relevant sequenced interface) automatically.
