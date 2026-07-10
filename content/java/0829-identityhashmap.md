---
card: java
gi: 829
slug: identityhashmap
title: IdentityHashMap
---

## 1. What it is

`IdentityHashMap` is a `Map` implementation that deliberately violates the general `Map` contract: it compares keys (and values, for containment checks) using **reference identity** (`==`) instead of `equals()`, and uses `System.identityHashCode()` instead of `hashCode()` to place entries. Two distinct objects that are `equals()` to each other — even two `String`s with identical characters — are treated as **different** keys by `IdentityHashMap`, as long as they aren't the exact same object in memory. This is the polar opposite of `HashMap`'s value-based equality, and the class exists specifically for algorithms where distinguishing "the same object" from "an equal-looking different object" is the actual requirement.

## 2. Why & when

Ordinary value-based equality (`HashMap`'s default) is wrong for a narrow but real category of problems: tracking which specific object instances have already been visited during a graph or object-graph traversal (to detect cycles or avoid revisiting), or building a serialization/deep-copy mechanism that must preserve the original object graph's exact identity structure — two `equals()`-identical objects at different memory locations must still be treated as two separate nodes, not merged into one. A `HashMap` would incorrectly collapse them if their `equals()`/`hashCode()` happened to match; `IdentityHashMap` never does, because it never calls `equals()`/`hashCode()` at all. Reach for `IdentityHashMap` specifically for these identity-tracking use cases — it is almost never the right general-purpose map, precisely because it silently breaks the assumption most code makes about how map keys behave.

## 3. Core concept

```java
String a = new String("hello"); // deliberately a NEW object, not the interned literal
String b = new String("hello"); // another new, distinct object with the SAME characters

System.out.println(a.equals(b)); // true -- same character sequence
System.out.println(a == b);      // false -- different objects in memory

Map<String, Integer> regularMap = new HashMap<>();
regularMap.put(a, 1);
regularMap.put(b, 2); // equals()-equal to "a" -- OVERWRITES the same entry
System.out.println(regularMap.size()); // 1

Map<String, Integer> identityMap = new IdentityHashMap<>();
identityMap.put(a, 1);
identityMap.put(b, 2); // NOT the same object as "a" -- a SEPARATE entry
System.out.println(identityMap.size()); // 2
```

`IdentityHashMap` treats `a` and `b` as unrelated keys purely because they're different objects, regardless of their `equals()`-equality — the exact opposite of what `HashMap` does with the same two objects.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="HashMap merges two equals-equal but distinct objects into one entry; IdentityHashMap keeps them as two separate entries because it only checks reference identity">
  <rect x="40" y="30" width="250" height="60" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="165" y="55" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">HashMap: equals()-based</text>
  <text x="165" y="75" fill="#3fb950" font-size="10" text-anchor="middle" font-family="sans-serif">two "hello" objects -> 1 entry</text>

  <rect x="350" y="30" width="250" height="60" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="475" y="55" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">IdentityHashMap: ==-based</text>
  <text x="475" y="75" fill="#f0883e" font-size="10" text-anchor="middle" font-family="sans-serif">two "hello" objects -> 2 entries</text>

  <text x="320" y="130" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Same two objects, same character content — the map implementation decides whether they're "the same key"</text>
</svg>

*Whether two equal-looking objects count as one key or two depends entirely on which comparison rule the map uses.*

## 5. Runnable example

Scenario: detecting cycles while traversing an object graph (a common need in custom serialization or deep-copy logic), growing from the value-equality pitfall a `HashMap` would introduce, to a correct identity-based visited-set, to a full cycle-safe deep-copy of a linked structure.

### Level 1 — Basic

```java
import java.util.*;

public class EqualityPitfall {
    public static void main(String[] args) {
        String a = new String("node");
        String b = new String("node"); // equals()-equal to "a", but a DIFFERENT object

        Map<String, Integer> visitedByEquality = new HashMap<>();
        visitedByEquality.put(a, 1);
        visitedByEquality.put(b, 2); // OVERWRITES "a"'s entry, since HashMap sees them as the same key

        System.out.println("HashMap-based visited count: " + visitedByEquality.size());
        System.out.println("-> WRONG if 'a' and 'b' are meant to represent two DIFFERENT graph nodes");
    }
}
```

**How to run:** `java EqualityPitfall.java` (JDK 17+).

Expected output:
```
HashMap-based visited count: 1
-> WRONG if 'a' and 'b' are meant to represent two DIFFERENT graph nodes
```

If `a` and `b` represent two genuinely distinct nodes in an object graph that merely happen to hold equal data, a `HashMap`-based "visited" tracker incorrectly conflates them into a single entry — exactly the bug `IdentityHashMap` exists to avoid.

### Level 2 — Intermediate

```java
import java.util.*;

public class IdentityVisitedSet {
    public static void main(String[] args) {
        String a = new String("node");
        String b = new String("node");

        Map<String, Integer> visitedByIdentity = new IdentityHashMap<>();
        visitedByIdentity.put(a, 1);
        visitedByIdentity.put(b, 2); // a DIFFERENT object -- treated as a separate key

        System.out.println("IdentityHashMap-based visited count: " + visitedByIdentity.size());
        System.out.println("a is present: " + visitedByIdentity.containsKey(a));
        System.out.println("b is present: " + visitedByIdentity.containsKey(b));

        // Even inserting "a" again (the SAME object) correctly updates, not duplicates:
        visitedByIdentity.put(a, 99);
        System.out.println("after re-inserting the SAME 'a' object, size: " + visitedByIdentity.size());
        System.out.println("a's value now: " + visitedByIdentity.get(a));
    }
}
```

**How to run:** `java IdentityVisitedSet.java`.

Expected output:
```
IdentityHashMap-based visited count: 2
a is present: true
b is present: true
after re-inserting the SAME 'a' object, size: 2
a's value now: 99
```

The real-world concern added: confirming both that genuinely distinct objects are correctly kept separate, **and** that re-inserting the exact same object correctly updates in place rather than creating a duplicate — `IdentityHashMap` still behaves like a proper map, just with a different notion of "same key" than usual.

### Level 3 — Advanced

```java
import java.util.*;

public class CycleSafeDeepCopy {
    static class Node {
        String label;
        Node next;
        Node(String label) { this.label = label; }
    }

    static Node deepCopy(Node original, IdentityHashMap<Node, Node> alreadyCopied) {
        if (original == null) return null;

        Node existingCopy = alreadyCopied.get(original);
        if (existingCopy != null) {
            return existingCopy; // already copied this exact node -- reuse it, breaking the cycle
        }

        Node copy = new Node(original.label);
        alreadyCopied.put(original, copy); // register BEFORE recursing, so a cycle back to this node is caught
        copy.next = deepCopy(original.next, alreadyCopied);
        return copy;
    }

    public static void main(String[] args) {
        Node a = new Node("A");
        Node b = new Node("B");
        Node c = new Node("C");
        a.next = b;
        b.next = c;
        c.next = a; // deliberately creates a CYCLE: A -> B -> C -> A

        Node copiedA = deepCopy(a, new IdentityHashMap<>());

        System.out.println("copied chain: " + copiedA.label + " -> " + copiedA.next.label + " -> " + copiedA.next.next.label);
        System.out.println("cycle correctly preserved in the copy: " + (copiedA.next.next.next == copiedA));
        System.out.println("copy is a genuinely separate object from the original: " + (copiedA != a));
    }
}
```

**How to run:** `java CycleSafeDeepCopy.java`.

Expected output:
```
copied chain: A -> B -> C
cycle correctly preserved in the copy: true
copy is a genuinely separate object from the original: true
```

This adds the production-flavored hard case: a genuinely cyclic linked structure (`A -> B -> C -> A`), deep-copied safely using `IdentityHashMap` to track "original node -> its copy" by object identity. A `HashMap` would be the wrong tool here even if `Node` had a value-based `equals()`/`hashCode()` — the tracking needs to key off "this exact original object instance," not "an object that looks like this one," and `deepCopy` would infinite-loop on the cycle without some form of already-visited tracking at all.

## 6. Walkthrough

Tracing `CycleSafeDeepCopy.main`:

1. `a`, `b`, and `c` are linked `A -> B -> C`, and then `c.next = a` closes the cycle, `C -> A`.
2. `deepCopy(a, new IdentityHashMap<>())` is called. `alreadyCopied.get(a)` finds nothing (the map starts empty), so a new `Node` copy of `A` is created and immediately registered: `alreadyCopied.put(a, copyOfA)` — **before** recursing into `a.next`, which is critical for breaking the cycle correctly.
3. The call recurses: `deepCopy(b, alreadyCopied)`. Again, `b` isn't yet in the map, so a copy of `B` is created and registered, then the call recurses into `deepCopy(c, alreadyCopied)`.
4. Similarly, `c` isn't yet registered, so a copy of `C` is created and registered, and the call recurses one more level into `deepCopy(a, alreadyCopied)` — following `c.next`, which points back to the **original** `a` object.
5. This time, `alreadyCopied.get(a)` **does** find an entry — the copy of `A` created back in step 2 — because `IdentityHashMap` correctly recognizes this is the exact same `a` object reference encountered before, regardless of any `equals()`/`hashCode()` considerations. The recursive call returns that existing copy immediately, without creating a new node and without recursing further, breaking the cycle.
6. Each recursive call then finishes assembling its `copy.next` link using the value just returned, and the whole call stack unwinds: `copyOfC.next = copyOfA` (closing the cycle in the copy, correctly), `copyOfB.next = copyOfC`, `copyOfA.next = copyOfB`. The final printed checks confirm the copied chain reads `A -> B -> C`, that following the copy's cycle four steps (`next.next.next`) lands back on `copiedA` itself, and that `copiedA` is a genuinely distinct object from the original `a`.

## 7. Gotchas & takeaways

> **Gotcha:** `IdentityHashMap` violates the general `Map` interface contract on purpose — its documentation explicitly warns that it's meant for specialized algorithms, not general use. Passing an `IdentityHashMap` where code expects ordinary `equals()`-based `Map` semantics (for example, to a method that does `map.containsKey(new SomeEqualButDifferentKey())` expecting value-based lookup) will produce surprising, hard-to-diagnose results.

- `IdentityHashMap` compares keys with `==` (reference identity) and uses `System.identityHashCode()`, not `equals()`/`hashCode()` — the opposite of every other standard `Map` implementation's behavior.
- Two distinct objects that are `equals()`-equal are treated as **different** keys; the exact same object reference is required for a match.
- It's the right tool specifically for identity-based tracking: cycle detection during graph traversal, preserving object-graph identity during deep copies or serialization, or any algorithm where "is this the very same object" (not "is this an equal-looking object") is the actual question.
- It deliberately breaks the general `Map` contract, so it should never be used as a general-purpose map, or passed to code expecting standard value-based `equals()` semantics.
- Register a node in an identity map **before** recursing into its children/neighbors when using this pattern for cycle detection — registering after recursion would never actually catch the cycle.
