---
card: java
gi: 843
slug: collections-unmodifiable-views
title: Collections.unmodifiable* views
---

## 1. What it is

`Collections.unmodifiableList(list)`, `unmodifiableSet(set)`, `unmodifiableMap(map)`, and their siblings return a **wrapper view** around an existing collection — any attempt to mutate the wrapper (`add`, `remove`, `put`, `clear`, and the rest) throws `UnsupportedOperationException` immediately. Critically, this is a *view*, not a copy: the wrapper delegates every read operation straight through to the original, backing collection, which means if the **original** collection is mutated directly (through the reference that created it, not through the wrapper), those changes are immediately visible through the "unmodifiable" wrapper too. The wrapper only blocks mutation attempted *through itself* — it provides no protection at all against the underlying data changing via some other reference to the same collection.

## 2. Why & when

A common API design goal is exposing a collection to callers for reading without letting them mutate it — a method returning an internal list of registered listeners, say, that callers should be able to inspect but never directly modify. `Collections.unmodifiableList(...)` accomplishes exactly that boundary cheaply (it's just a thin wrapper object, no copying of elements), which is why it's a common pattern for API return values. The critical thing to understand is that it protects against mutation **through the returned reference**, not against the underlying data changing at all — if the class internally still holds and mutates the original list, callers holding the "unmodifiable" view will see those changes appear, which can be surprising if the intent was actually to freeze the data at the moment it was returned. For that stronger guarantee — a truly frozen, independent snapshot — an explicit defensive copy (or `List.copyOf(...)`, introduced in Java 10, which does both the copy and the immutability in one call) is the correct tool instead.

## 3. Core concept

```java
List<String> internal = new ArrayList<>(List.of("logger", "metrics"));
List<String> exposedView = Collections.unmodifiableList(internal);

try {
    exposedView.add("audit"); // mutating THROUGH the wrapper -- blocked
} catch (UnsupportedOperationException e) {
    System.out.println("blocked, as expected");
}

internal.add("audit"); // mutating the ORIGINAL list directly -- NOT blocked at all
System.out.println(exposedView); // [logger, metrics, audit] -- the "unmodifiable" view sees the change too!
```

`exposedView` never becomes truly immutable data — it's only a promise that *this particular reference* can't be used to mutate anything; the underlying `internal` list remains as mutable as ever through its own reference.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="An unmodifiable view blocks mutation attempted through itself, but mutating the original backing collection directly is still visible through the view">
  <rect x="240" y="15" width="160" height="45" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="42" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">original ArrayList</text>

  <line x1="280" y1="60" x2="160" y2="100" stroke="#f85149" stroke-width="1.5" marker-end="url(#a843r)"/>
  <text x="180" y="85" fill="#f85149" font-size="9" font-family="sans-serif">direct mutation: allowed</text>

  <line x1="360" y1="60" x2="480" y2="100" stroke="#8b949e" stroke-width="1.5"/>
  <text x="470" y="85" fill="#8b949e" font-size="9" font-family="sans-serif">reads delegate through</text>

  <rect x="60" y="105" width="200" height="40" rx="6" fill="#1c2430" stroke="#f85149"/>
  <text x="160" y="130" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">internal.add(x) -- WORKS</text>

  <rect x="380" y="105" width="200" height="40" rx="6" fill="#1c2430" stroke="#3fb950"/>
  <text x="480" y="130" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">view.add(x) -- THROWS</text>

  <defs><marker id="a843r" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#f85149"/></marker></defs>
</svg>

*The wrapper blocks mutation only through itself — the original collection remains fully mutable through its own reference.*

## 5. Runnable example

Scenario: an API exposing a read-only view of internal state, growing from basic mutation-blocking behavior, through the "it's just a view" surprise when the backing list changes underneath it, to the correct defensive-copy pattern for a genuinely frozen snapshot.

### Level 1 — Basic

```java
import java.util.*;

public class UnmodifiableBasic {
    public static void main(String[] args) {
        List<String> internal = new ArrayList<>(List.of("logger", "metrics"));
        List<String> exposed = Collections.unmodifiableList(internal);

        System.out.println("exposed view: " + exposed);

        try {
            exposed.add("audit");
        } catch (UnsupportedOperationException e) {
            System.out.println("caught: cannot mutate through the unmodifiable view");
        }
    }
}
```

**How to run:** `java UnmodifiableBasic.java` (JDK 17+).

Expected output:
```
exposed view: [logger, metrics]
caught: cannot mutate through the unmodifiable view
```

`exposed.add(...)` fails immediately and predictably — the basic mutation-blocking behavior works exactly as expected here.

### Level 2 — Intermediate

```java
import java.util.*;

public class UnmodifiableViewSurprise {
    public static void main(String[] args) {
        List<String> internal = new ArrayList<>(List.of("logger", "metrics"));
        List<String> exposed = Collections.unmodifiableList(internal);

        System.out.println("exposed view, before internal mutation: " + exposed);

        internal.add("audit"); // mutating the ORIGINAL list directly, not through "exposed"

        System.out.println("exposed view, AFTER internal mutation (it changed too!): " + exposed);
        System.out.println("-> 'unmodifiable' only means 'not mutable THROUGH THIS REFERENCE', not 'frozen data'");
    }
}
```

**How to run:** `java UnmodifiableViewSurprise.java`.

Expected output:
```
exposed view, before internal mutation: [logger, metrics]
exposed view, AFTER internal mutation (it changed too!): [logger, metrics, audit]
-> 'unmodifiable' only means 'not mutable THROUGH THIS REFERENCE', not 'frozen data'
```

The real-world concern added: proving directly that `Collections.unmodifiableList` provides **no protection whatsoever** against the underlying collection changing via a different reference — a caller holding `exposed` might reasonably (but incorrectly) assume the data is frozen at the moment they received it, when in fact it's a live window onto whatever the internal list currently contains.

### Level 3 — Advanced

```java
import java.util.*;

public class DefensiveCopyVsView {

    static class ListenerRegistry {
        private final List<String> listeners = new ArrayList<>();

        void register(String listener) {
            listeners.add(listener);
        }

        // WEAKER guarantee: an unmodifiable VIEW -- callers see future internal changes.
        List<String> viewListeners() {
            return Collections.unmodifiableList(listeners);
        }

        // STRONGER guarantee: a genuinely frozen SNAPSHOT -- immune to future internal changes.
        List<String> snapshotListeners() {
            return List.copyOf(listeners); // Java 10+: copies AND makes immutable in one call
        }
    }

    public static void main(String[] args) {
        ListenerRegistry registry = new ListenerRegistry();
        registry.register("logger");

        List<String> view = registry.viewListeners();
        List<String> snapshot = registry.snapshotListeners();

        registry.register("metrics"); // internal state changes AFTER both were obtained

        System.out.println("live view (reflects the new registration): " + view);
        System.out.println("frozen snapshot (does NOT reflect it): " + snapshot);
    }
}
```

**How to run:** `java DefensiveCopyVsView.java`.

Expected output:
```
live view (reflects the new registration): [logger, metrics]
frozen snapshot (does NOT reflect it): [logger]
```

This adds the production-flavored hard case: contrasting the two available guarantees side by side in a realistic API design. `viewListeners()` returns a cheap wrapper that always reflects the registry's *current* internal state — appropriate when callers genuinely want a live, read-only window. `snapshotListeners()` uses `List.copyOf(...)` (Java 10+) to copy the elements into a brand-new, independently immutable list at the moment it's called — appropriate when callers need a guaranteed-frozen point-in-time view, immune to whatever the registry does afterward. Choosing the wrong one for the API's actual intent is a subtle, easy-to-miss design bug.

## 6. Walkthrough

Tracing `DefensiveCopyVsView.main`:

1. `registry.register("logger")` adds one listener to the registry's internal `listeners` list.
2. `view = registry.viewListeners()` returns `Collections.unmodifiableList(listeners)` — a wrapper object that, internally, still holds a reference to the exact same `listeners` list the registry itself uses. No copying happens here at all.
3. `snapshot = registry.snapshotListeners()` returns `List.copyOf(listeners)` — this call **does** copy every current element of `listeners` into a brand-new, separate, genuinely immutable list object. From this point forward, `snapshot` has no connection whatsoever to the registry's internal `listeners` list.
4. `registry.register("metrics")` adds a second listener directly to the registry's internal `listeners` list — the same list object `view` wraps, but entirely unrelated to the independent copy `snapshot` holds.
5. Printing `view` shows `[logger, metrics]` — both listeners — because `view` is a thin wrapper delegating reads straight through to the registry's `listeners` list, which now contains both entries.
6. Printing `snapshot` shows only `[logger]` — the state of `listeners` at the exact moment `List.copyOf(listeners)` was called, before `"metrics"` was ever registered — because `snapshot` is a fully independent copy, structurally disconnected from any future changes to the registry's internal list.

## 7. Gotchas & takeaways

> **Gotcha:** `Collections.unmodifiableList` (and its `Set`/`Map`/`Collection` siblings) creates a **view**, not a copy — it protects only against mutation attempted through the wrapper reference itself, and provides zero protection against the backing collection changing via any other reference that still holds it. Assuming "unmodifiable" means "frozen" is a common and consequential misunderstanding.

- `Collections.unmodifiableList/Set/Map(...)` wraps an existing collection, throwing `UnsupportedOperationException` on any mutation attempted through the wrapper itself.
- These wrappers are thin views, not copies — changes to the underlying collection via any other reference remain fully visible through the wrapper.
- For a genuinely frozen, independent snapshot immune to future changes in the source, use an explicit defensive copy, or `List.copyOf(...)`/`Set.copyOf(...)`/`Map.copyOf(...)` (Java 10+), which combine copying and immutability in one call.
- Choosing between an unmodifiable view (cheap, always reflects current state) and a frozen copy (costs an O(n) copy, immune to future changes) should match the actual intent of the API — get this wrong and callers either see surprising live updates or pay an unnecessary copy cost.
- `List.of(...)`/`Set.of(...)`/`Map.of(...)` (Java 9+) create genuinely immutable collections directly from literal elements, distinct from both the view-wrapping and copy-then-freeze patterns described here.
