---
card: java
gi: 1019
slug: prefer-composition
title: Prefer composition
---

## 1. What it is

This is Effective Java's specific warning about a danger [composition over inheritance](0995-composition-over-inheritance.md) only briefly touches on: extending a concrete class that **wasn't designed and documented for inheritance** is fragile in a way that has nothing to do with "is-a" versus "has-a" modeling — it's about **self-use**. A class like `HashSet` internally calls its own methods to implement other methods (its `addAll` might internally call `add` once per element). A subclass that overrides `add` to add extra behavior will find that behavior silently triggered *again* by `HashSet`'s internal `addAll` implementation — a coupling to an undocumented implementation detail that can change in any future JDK release.

## 2. Why & when

The problem isn't just "changing a base class ripples to subclasses" (true of any inheritance) — it's specifically that a subclass overriding one method can't know, without reading the base class's *implementation* (not just its documented contract), whether other base-class methods internally call the one it just overrode. `HashSet.addAll` happening to be implemented in terms of `add` is an implementation detail, not a documented guarantee — a future JDK version is free to reimplement `addAll` without calling `add` at all, silently breaking any subclass relying on that behavior. This is called the **fragile base class problem**, and it's precisely why Effective Java recommends composition — specifically via the **forwarding/wrapper** technique — instead: wrap the class, delegate every method to it explicitly, and add your own behavior only in the wrapper's own methods, which are never subject to the wrapped class's internal call patterns.

Reach for the forwarding-wrapper approach whenever you want to add behavior to a class you don't control (a JDK collection, a third-party library class) and that class wasn't explicitly documented as designed for extension. It's fine to extend a class that *is* explicitly documented for subclassing (its Javadoc states which methods are safe to override and how they're used internally) — that documentation is the class author's promise that the self-use coupling won't silently change underneath you.

## 3. Core concept

```
import java.util.*;

// Fragile: overrides add(), but HashSet's addAll() might call add() internally,
// double-counting every element added via addAll -- an UNDOCUMENTED implementation detail.
class InstrumentedHashSet<E> extends HashSet<E> {
    private int addCount = 0;
    @Override public boolean add(E e) { addCount++; return super.add(e); }
    @Override public boolean addAll(Collection<? extends E> c) { addCount += c.size(); return super.addAll(c); }
    int getAddCount() { return addCount; }
}

// Robust: composition via forwarding. Wraps a Set, delegates everything explicitly,
// and adds instrumentation ONLY in its own add()/addAll() -- no reliance on how
// the wrapped Set implements itself internally.
class InstrumentedSet<E> {
    private final Set<E> wrapped; // HAS-A Set, not IS-A HashSet
    private int addCount = 0;
    InstrumentedSet(Set<E> wrapped) { this.wrapped = wrapped; }
    boolean add(E e) { addCount++; return wrapped.add(e); }
    boolean addAll(Collection<? extends E> c) { addCount += c.size(); return wrapped.addAll(c); }
    int getAddCount() { return addCount; }
    int size() { return wrapped.size(); }
}
```

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="InstrumentedHashSet extending HashSet and being silently double-counted when addAll internally calls the overridden add, versus InstrumentedSet composing a Set and controlling every method itself">
  <text x="150" y="24" fill="#8b949e" font-size="12" text-anchor="middle" font-family="sans-serif">Inheritance: fragile</text>
  <rect x="30" y="40" width="230" height="34" rx="6" fill="#1c2430" stroke="#f0883e"/>
  <text x="145" y="61" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">InstrumentedHashSet extends HashSet</text>
  <rect x="30" y="100" width="230" height="40" rx="6" fill="#1c2430" stroke="#f0883e" stroke-dasharray="4"/>
  <text x="145" y="120" fill="#f0883e" font-size="9" text-anchor="middle" font-family="sans-serif">addAll() secretly calls add()</text>
  <text x="145" y="135" fill="#f0883e" font-size="9" text-anchor="middle" font-family="sans-serif">-&gt; double-counted!</text>

  <text x="480" y="24" fill="#8b949e" font-size="12" text-anchor="middle" font-family="sans-serif">Composition: robust</text>
  <rect x="380" y="40" width="120" height="34" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="440" y="61" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">InstrumentedSet</text>
  <rect x="520" y="40" width="100" height="34" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="570" y="61" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">wrapped Set</text>
  <line x1="500" y1="57" x2="520" y2="57" stroke="#79c0ff" marker-end="url(#a)"/>
  <text x="450" y="110" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">every method forwards explicitly</text>
  <defs><marker id="a" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Inheriting from `HashSet` inherits its undocumented internal call patterns too; composing via a wrapper controls every method call explicitly.

## 5. Runnable example

Scenario: instrumenting a `Set` to count how many elements were added, evolving from a fragile inheritance-based approach that silently double-counts into a robust, forwarding-based composition.

### Level 1 — Basic

```java
// File: PreferCompositionBasic.java
import java.util.HashSet;
import java.util.List;

class InstrumentedHashSet<E> extends HashSet<E> {
    private int addCount = 0;

    @Override
    public boolean add(E e) {
        addCount++;
        return super.add(e);
    }

    @Override
    public boolean addAll(java.util.Collection<? extends E> c) {
        addCount += c.size();
        return super.addAll(c); // HashSet's addAll may ALSO call add() internally per element
    }

    int getAddCount() { return addCount; }
}

public class PreferCompositionBasic {
    public static void main(String[] args) {
        InstrumentedHashSet<String> set = new InstrumentedHashSet<>();
        set.addAll(List.of("a", "b", "c"));
        System.out.println("expected addCount: 3, actual: " + set.getAddCount());
    }
}
```

**How to run:** save as `PreferCompositionBasic.java`, then `javac PreferCompositionBasic.java && java PreferCompositionBasic` (JDK 17+).

Expected output (on JDK implementations where `HashSet.addAll` is implemented by calling `add` once per element):
```
expected addCount: 3, actual: 6
```

The count comes out doubled: `addAll` adds `3` to `addCount` directly, but `HashSet`'s own `addAll` implementation calls `add` once per element internally — and since `add` was overridden to also increment `addCount`, each of the three elements gets counted twice. This behavior depends entirely on `HashSet`'s undocumented internal implementation, which is exactly the fragile base class problem.

### Level 2 — Intermediate

```java
// File: PreferCompositionIntermediate.java
import java.util.Collection;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

class InstrumentedSet<E> {
    private final Set<E> wrapped; // composition: HAS-A Set
    private int addCount = 0;

    InstrumentedSet(Set<E> wrapped) { this.wrapped = wrapped; }

    boolean add(E e) {
        addCount++;
        return wrapped.add(e);
    }

    boolean addAll(Collection<? extends E> c) {
        addCount += c.size();
        return wrapped.addAll(c); // delegates to the wrapped Set's addAll DIRECTLY -- not through our own add()
    }

    int getAddCount() { return addCount; }
    int size() { return wrapped.size(); }
}

public class PreferCompositionIntermediate {
    public static void main(String[] args) {
        InstrumentedSet<String> set = new InstrumentedSet<>(new HashSet<>());
        set.addAll(List.of("a", "b", "c"));
        System.out.println("expected addCount: 3, actual: " + set.getAddCount());
    }
}
```

**How to run:** save as `PreferCompositionIntermediate.java`, then `javac PreferCompositionIntermediate.java && java PreferCompositionIntermediate` (JDK 17+).

Expected output:
```
expected addCount: 3, actual: 3
```

The real-world concern added: `InstrumentedSet.addAll` delegates to `wrapped.addAll(c)` — the *actual* `HashSet`'s `addAll` method — not to `InstrumentedSet`'s own `add` method. Whatever `HashSet` does internally to implement its own `addAll` is irrelevant here, because `InstrumentedSet`'s `add` method is never in that internal call path at all.

### Level 3 — Advanced

```java
// File: PreferCompositionAdvanced.java
import java.util.Collection;
import java.util.HashSet;
import java.util.Iterator;
import java.util.List;
import java.util.Set;
import java.util.TreeSet;

// A general-purpose forwarding wrapper implementing the full Set interface,
// delegating EVERY method explicitly -- this is the real Effective Java
// "forwarding class" idiom, reusable for instrumenting ANY Set implementation.
class ForwardingSet<E> implements Set<E> {
    private final Set<E> wrapped;
    ForwardingSet(Set<E> wrapped) { this.wrapped = wrapped; }

    public int size() { return wrapped.size(); }
    public boolean isEmpty() { return wrapped.isEmpty(); }
    public boolean contains(Object o) { return wrapped.contains(o); }
    public Iterator<E> iterator() { return wrapped.iterator(); }
    public Object[] toArray() { return wrapped.toArray(); }
    public <T> T[] toArray(T[] a) { return wrapped.toArray(a); }
    public boolean add(E e) { return wrapped.add(e); }
    public boolean remove(Object o) { return wrapped.remove(o); }
    public boolean containsAll(Collection<?> c) { return wrapped.containsAll(c); }
    public boolean addAll(Collection<? extends E> c) { return wrapped.addAll(c); }
    public boolean retainAll(Collection<?> c) { return wrapped.retainAll(c); }
    public boolean removeAll(Collection<?> c) { return wrapped.removeAll(c); }
    public void clear() { wrapped.clear(); }
}

// The instrumentation itself: overrides ONLY the two methods it cares about,
// on top of the forwarding wrapper -- works identically over ANY Set implementation.
class InstrumentedSet<E> extends ForwardingSet<E> {
    private int addCount = 0;
    InstrumentedSet(Set<E> wrapped) { super(wrapped); }

    @Override public boolean add(E e) {
        addCount++;
        return super.add(e);
    }
    @Override public boolean addAll(Collection<? extends E> c) {
        addCount += c.size();
        return super.addAll(c);
    }
    int getAddCount() { return addCount; }
}

public class PreferCompositionAdvanced {
    public static void main(String[] args) {
        InstrumentedSet<String> hashBacked = new InstrumentedSet<>(new HashSet<>());
        hashBacked.addAll(List.of("a", "b", "c"));
        System.out.println("HashSet-backed addCount: " + hashBacked.getAddCount());

        // The SAME InstrumentedSet class works over a completely different
        // Set implementation, with no change needed at all.
        InstrumentedSet<String> treeBacked = new InstrumentedSet<>(new TreeSet<>());
        treeBacked.addAll(List.of("x", "y"));
        System.out.println("TreeSet-backed addCount: " + treeBacked.getAddCount());
    }
}
```

**How to run:** save as `PreferCompositionAdvanced.java`, then `javac PreferCompositionAdvanced.java && java PreferCompositionAdvanced` (JDK 17+).

Expected output:
```
HashSet-backed addCount: 3
TreeSet-backed addCount: 2
```

The production-flavored hard case: `InstrumentedSet` now works correctly over *any* `Set` implementation — `HashSet`, `TreeSet`, or any future implementation — because it never depends on that implementation's internal self-use patterns. `ForwardingSet` handles pure delegation; `InstrumentedSet` adds only its own two lines of instrumentation on top.

## 6. Walkthrough

Tracing `treeBacked.addAll(List.of("x", "y"))` in `PreferCompositionAdvanced.main`:

1. `treeBacked` is an `InstrumentedSet` wrapping a `new TreeSet<>()`, with `addCount = 0` initially.
2. `treeBacked.addAll(List.of("x", "y"))` dispatches to `InstrumentedSet.addAll` (it overrides `ForwardingSet.addAll`): `addCount += c.size()` runs first, where `c.size()` is `2`, so `addCount` becomes `2`.
3. `super.addAll(c)` is then called — `super` here refers to `ForwardingSet.addAll`, which runs `wrapped.addAll(c)`, delegating to the actual `TreeSet`'s `addAll` method, which adds `"x"` and `"y"` to the underlying tree structure.
4. Critically, whatever `TreeSet.addAll` does internally — whether it calls `add` once per element, or uses some entirely different bulk-insertion algorithm — never reaches `InstrumentedSet.add` at all, because `ForwardingSet.addAll` calls `wrapped.addAll` directly, not through `InstrumentedSet`'s own `add` method.
5. `treeBacked.getAddCount()` returns `2`, matching the number of elements actually passed to `addAll` — printed as `"TreeSet-backed addCount: 2"`.
6. Compare with `hashBacked`, constructed with a `HashSet` instead: the exact same `InstrumentedSet.addAll` code ran, and it produced the correct count of `3` as well — proving the instrumentation logic is entirely independent of which concrete `Set` implementation sits underneath, unlike the fragile `extends HashSet` version from Level 1, which was silently coupled to `HashSet`'s specific internal implementation.

## 7. Gotchas & takeaways

> **Gotcha:** the fragile base class problem is invisible until the base class's internal implementation actually changes (or, as shown here, simply happens to call another overridden method) — it's not a bug in the subclass's code as written, it's a latent bug waiting for an internal implementation detail, which was never part of any documented contract, to shift underneath it.

- Extending a class not explicitly designed and documented for inheritance couples your subclass to that class's *undocumented internal self-use patterns*, not just its public contract.
- A class is safe to extend when its documentation explicitly specifies which methods are called by which other methods internally (its "self-use" is documented, not just its public behavior) — absent that documentation, assume nothing about internal call patterns.
- The forwarding/wrapper technique (compose the class, delegate every method explicitly, add behavior only in the wrapper's own methods) sidesteps the problem entirely, since the wrapped object's internal calls never route through the wrapper's overridden methods.
- A reusable forwarding class (like `ForwardingSet`) separates pure delegation from the actual behavior being added, letting the "instrumentation" class stay tiny and focused.
- This is a stricter, more specific warning than the general [composition over inheritance](0995-composition-over-inheritance.md) guideline — it applies even when the "is-a" relationship seems perfectly natural (an `InstrumentedHashSet` really is a kind of `HashSet`, semantically), because the danger here is about implementation coupling, not conceptual modeling.
- Don't apply the forwarding-wrapper approach reflexively to every class you extend — classes explicitly documented for extension (with clear self-use documentation) are a legitimate and safe use of inheritance.
