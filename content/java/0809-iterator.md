---
card: java
gi: 809
slug: iterator
title: Iterator
---

## 1. What it is

`Iterator<T>` is the object returned by [`Iterable.iterator()`](0800-iterable.md) that actually performs traversal. It has three core methods: `hasNext()` (is there another element?), `next()` (return the next element, advancing position), and `remove()` (remove the element most recently returned by `next()` — the **only** safe way to remove elements from a collection while iterating over it). Unlike a for-each loop, which only reads, working with an `Iterator` explicitly gives direct control over traversal and, critically, the ability to delete elements mid-traversal without corrupting the iteration.

## 2. Why & when

Removing an element from a `List` or `Set` while iterating it with a for-each loop — `for (String s : list) { if (condition) list.remove(s); }` — throws `ConcurrentModificationException`, because the collection detects it was structurally modified outside the iterator's own bookkeeping. `Iterator.remove()` exists specifically to make in-loop removal safe: it updates the iterator's internal state at the same time it removes the element, so the traversal stays consistent. Reach for an explicit `Iterator` (instead of a for-each loop, or instead of `Collection.removeIf`) whenever the removal decision needs more context than a single predicate can express, or when the loop body needs both the current element and manual control over stopping early.

## 3. Core concept

```java
List<String> sessions = new ArrayList<>(List.of("active", "expired", "active", "expired"));

Iterator<String> it = sessions.iterator();
while (it.hasNext()) {
    String status = it.next();
    if (status.equals("expired")) {
        it.remove(); // safe: removes the element just returned by next()
    }
}
// sessions is now ["active", "active"]
```

Compare this to the unsafe version that throws:

```java
for (String status : sessions) {
    if (status.equals("expired")) {
        sessions.remove(status); // throws ConcurrentModificationException
    }
}
```

The for-each loop has its own hidden `Iterator` that the code above never gets a handle to — calling `list.remove()` directly modifies the list without that hidden iterator knowing, and the next `hasNext()`/`next()` call detects the mismatch and throws.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Removing directly from a list during a for-each loop throws ConcurrentModificationException, while Iterator.remove() safely removes the current element">
  <rect x="30" y="20" width="270" height="70" rx="8" fill="#1c2430" stroke="#f85149" stroke-width="1.5"/>
  <text x="165" y="45" fill="#f85149" font-size="11" text-anchor="middle" font-family="sans-serif">for (x : list) list.remove(x)</text>
  <text x="165" y="65" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">throws ConcurrentModificationException</text>

  <rect x="340" y="20" width="270" height="70" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="475" y="45" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">it.next(); it.remove()</text>
  <text x="475" y="65" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">safe — iterator's bookkeeping stays in sync</text>

  <text x="320" y="130" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Both attempt the same goal: remove matching elements while walking the list.</text>
  <text x="320" y="150" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Only the explicit Iterator's own remove() keeps position and modification count consistent.</text>
</svg>

*Direct removal during a for-each loop corrupts the hidden iterator's bookkeeping; `Iterator.remove()` stays safe because it updates that bookkeeping itself.*

## 5. Runnable example

Scenario: cleaning up expired sessions from a list, growing from the exception that direct removal causes, to the safe `Iterator.remove()` fix, to a reusable filtering iterator built as a decorator around any other iterator.

### Level 1 — Basic

```java
import java.util.*;

public class ExpiredSessionsBroken {
    public static void main(String[] args) {
        List<String> sessions = new ArrayList<>(List.of("active", "expired", "active", "expired"));

        try {
            for (String status : sessions) {
                if (status.equals("expired")) {
                    sessions.remove(status); // modifying the list during a for-each loop
                }
            }
        } catch (ConcurrentModificationException e) {
            System.out.println("caught: " + e.getClass().getSimpleName());
        }

        System.out.println("sessions after the failed attempt: " + sessions);
    }
}
```

**How to run:** `java ExpiredSessionsBroken.java` (JDK 17+).

Expected output:
```
caught: ConcurrentModificationException
sessions after the failed attempt: [active, active, expired]
```

The for-each loop's hidden iterator detects that `sessions` was structurally modified (an element removed) by a call that didn't go through the iterator itself, and throws on the next `hasNext()`/`next()` call — leaving the list only partially cleaned (one `"expired"` removed before the exception, one left over).

### Level 2 — Intermediate

```java
import java.util.*;

public class ExpiredSessionsFixed {
    public static void main(String[] args) {
        List<String> sessions = new ArrayList<>(List.of("active", "expired", "active", "expired"));

        Iterator<String> it = sessions.iterator();
        while (it.hasNext()) {
            String status = it.next();
            if (status.equals("expired")) {
                it.remove(); // safe: removes the element most recently returned by next()
            }
        }

        System.out.println("sessions after cleanup: " + sessions);

        // Calling remove() before next(), or twice in a row, is also an error:
        Iterator<String> it2 = sessions.iterator();
        try {
            it2.remove(); // no element has been returned by next() yet
        } catch (IllegalStateException e) {
            System.out.println("caught: " + e.getClass().getSimpleName());
        }
    }
}
```

**How to run:** `java ExpiredSessionsFixed.java`.

Expected output:
```
sessions after cleanup: [active, active]
caught: IllegalStateException
```

The real-world concern added: the actual fix — using the `Iterator` explicitly and calling `it.remove()` right after `it.next()` — plus the boundary case of calling `remove()` without a preceding `next()` call, which `Iterator` also guards against, throwing `IllegalStateException` rather than silently doing nothing or removing the wrong element.

### Level 3 — Advanced

```java
import java.util.*;
import java.util.function.Predicate;

public class FilteringIterator<T> implements Iterator<T> {
    private final Iterator<T> source;
    private final Predicate<T> keepIf;
    private T nextMatch;
    private boolean hasNextMatch;

    public FilteringIterator(Iterator<T> source, Predicate<T> keepIf) {
        this.source = source;
        this.keepIf = keepIf;
        advance();
    }

    private void advance() {
        hasNextMatch = false;
        while (source.hasNext()) {
            T candidate = source.next();
            if (keepIf.test(candidate)) {
                nextMatch = candidate;
                hasNextMatch = true;
                return;
            }
        }
    }

    @Override
    public boolean hasNext() {
        return hasNextMatch;
    }

    @Override
    public T next() {
        if (!hasNextMatch) throw new NoSuchElementException();
        T result = nextMatch;
        advance(); // pre-fetch the next matching element for the following hasNext()/next() call
        return result;
    }

    public static void main(String[] args) {
        List<String> sessions = List.of("active", "expired", "active", "expired", "active");

        FilteringIterator<String> activeOnly = new FilteringIterator<>(sessions.iterator(), s -> s.equals("active"));
        List<String> collected = new ArrayList<>();
        while (activeOnly.hasNext()) {
            collected.add(activeOnly.next());
        }
        System.out.println("active sessions only: " + collected);
    }
}
```

**How to run:** `java FilteringIterator.java`.

Expected output:
```
active sessions only: [active, active, active]
```

This adds the production-flavored hard case: a **custom `Iterator`** implemented as a decorator around another iterator — `FilteringIterator` wraps any `Iterator<T>` and only surfaces elements matching a `Predicate`, pre-fetching the next match inside `advance()` so `hasNext()` can answer truthfully without consuming an extra element from the source. This is the same underlying pattern `Stream.filter()` uses internally, built here from scratch on top of the raw `Iterator` interface.

## 6. Walkthrough

Tracing `FilteringIterator.main`:

1. `new FilteringIterator<>(sessions.iterator(), s -> s.equals("active"))` constructs the wrapper. Its constructor immediately calls `advance()`, which pulls elements from the underlying `sessions.iterator()` one at a time — `"active"` (matches, stop here) — leaving `nextMatch = "active"` and `hasNextMatch = true` before the object is even returned to the caller.
2. The `while (activeOnly.hasNext())` loop begins: `hasNext()` simply returns the pre-computed `hasNextMatch` flag, no work happens there.
3. `activeOnly.next()` returns the pre-fetched `"active"`, then calls `advance()` again to look ahead: the source yields `"expired"` (rejected), then `"active"` (matches) — so `nextMatch` is now the second `"active"`, ready for the next call.
4. This next/advance cycle repeats: the second call to `next()` returns the second `"active"` and pre-fetches past `"expired"` to the third `"active"`; the third call to `next()` returns that third `"active"` and calls `advance()` one final time, which exhausts the source (`hasNext()` on `sessions.iterator()` becomes `false`) and sets `hasNextMatch = false`.
5. The loop's next `hasNext()` check now returns `false`, ending the `while` loop with `collected = ["active", "active", "active"]` — every element matching the predicate, in original relative order, with the two `"expired"` entries filtered out entirely without ever touching the original `sessions` list.

## 7. Gotchas & takeaways

> **Gotcha:** `Iterator.remove()` can only be called **once per call to `next()`**, and only after `next()` has been called at least once — calling it twice in a row, or before any `next()` call, throws `IllegalStateException`. It is not a general-purpose "delete the current element whenever I feel like it" method.

- `Iterator<T>` provides `hasNext()`, `next()`, and (optionally) `remove()` — obtained from any [`Iterable`](0800-iterable.md) via `iterator()`.
- Removing elements directly from a collection during a for-each loop throws `ConcurrentModificationException`; `Iterator.remove()` is the safe alternative because it updates the iterator's own bookkeeping.
- `remove()` acts on "the element most recently returned by `next()`" — call order matters, and calling it out of sequence throws `IllegalStateException`.
- Custom `Iterator` implementations (like a filtering decorator) are a legitimate, reusable way to add traversal behavior without copying the underlying collection.
- For simple removal-by-predicate without needing element-by-element control, `Collection.removeIf(predicate)` is a shorter, equally safe alternative to a manual `Iterator` loop.
