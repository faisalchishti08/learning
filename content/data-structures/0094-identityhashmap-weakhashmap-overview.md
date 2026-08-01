---
card: data-structures
gi: 94
slug: identityhashmap-weakhashmap-overview
title: 'IdentityHashMap & WeakHashMap (overview)'
---

## 1. What it is

`IdentityHashMap` and `WeakHashMap` are two specialized `java.util.Map` implementations that each break one of `HashMap`'s normal assumptions on purpose. `IdentityHashMap` compares keys by reference identity (`==`) instead of `equals()`. `WeakHashMap` holds its keys with weak references, letting entries disappear automatically once nothing else references the key.

## 2. Why & when

Use `IdentityHashMap` when you specifically need "is this the exact same object," not "is this an equal object" — serialization frameworks that track which objects have already been visited (to detect cycles), for example, where two `equals()`-equal-but-distinct objects must be treated as different keys. Use `WeakHashMap` for caches or metadata maps that should not prevent their keys from being garbage collected — for example, attaching extra data to objects you don't own the lifecycle of, without causing a memory leak.

## 3. Core concept

**`IdentityHashMap` — reference equality, not `equals()`.** A normal `HashMap` uses `key.hashCode()` and `key.equals(other)` to decide if two keys are "the same." `IdentityHashMap` instead uses `System.identityHashCode(key)` and `key == other` — two distinct objects that are `equals()` to each other (like two separate `new String("x")` instances with the same content) are treated as *different* keys, since they are not the same object in memory.

**`WeakHashMap` — keys can be garbage collected.** A normal `HashMap` holds a **strong reference** to every key, which means the key object can never be garbage collected while it remains in the map, even if nothing else in the program references it anymore. `WeakHashMap` holds each key with a **weak reference** instead — once no other strong reference to that key exists anywhere in the program, the garbage collector is free to reclaim it, and the map's entry for it disappears automatically (typically the next time the map is accessed, when Java processes the reference queue internally).

**Why this matters for memory.** Using a normal `HashMap` as a cache keyed by objects you do not control the lifecycle of (like listener callbacks tied to UI components) can silently leak memory — every key you ever inserted stays alive forever, just because the map references it, even after the "real" object should have been discarded. `WeakHashMap` fixes this specific pattern by letting the cache's entries expire naturally alongside their keys.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A WeakHashMap holding a key via a weak reference, so once all other strong references to that key disappear, the garbage collector reclaims it and the map entry vanishes automatically">
  <g font-family="sans-serif" font-size="11">
    <text x="20" y="16" fill="#8b949e">before: some code holds a strong reference AND the WeakHashMap holds a weak reference</text>
    <rect x="20" y="30" width="100" height="26" fill="#161b22" stroke="#79c0ff"/><text x="70" y="47" fill="#e6edf3" text-anchor="middle" font-size="8">other code</text>
    <rect x="280" y="30" width="80" height="26" fill="#0d1117" stroke="#f0883e"/><text x="320" y="47" fill="#e6edf3" text-anchor="middle" font-size="8">key object</text>
    <rect x="20" y="70" width="100" height="26" fill="#161b22" stroke="#8b949e"/><text x="70" y="87" fill="#e6edf3" text-anchor="middle" font-size="8">WeakHashMap</text>
    <line x1="120" y1="43" x2="276" y2="43" stroke="#79c0ff" marker-end="url(#wr1)"/><text x="200" y="35" fill="#79c0ff" font-size="8">strong ref</text>
    <line x1="120" y1="83" x2="276" y2="50" stroke="#f0883e" stroke-dasharray="3,3" marker-end="url(#wr2)"/><text x="200" y="90" fill="#f0883e" font-size="8">weak ref</text>
    <defs>
      <marker id="wr1" markerWidth="8" markerHeight="8" refX="4" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#79c0ff"/></marker>
      <marker id="wr2" markerWidth="8" markerHeight="8" refX="4" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#f0883e"/></marker>
    </defs>
    <text x="320" y="140" fill="#8b949e" text-anchor="middle" font-size="9">after "other code" drops its reference: only the weak ref remains -&gt;</text>
    <text x="320" y="160" fill="#f0883e" text-anchor="middle" font-size="9">GC reclaims the key object -&gt; WeakHashMap's entry for it disappears</text>
  </g>
</svg>

As long as a strong reference exists elsewhere, the key survives; once it is the only reference left, a weak reference cannot keep the object alive, and the garbage collector reclaims it.

## 5. Runnable example

```java
// IdentityAndWeakHashMapDemo.java
import java.util.IdentityHashMap;
import java.util.Map;
import java.util.WeakHashMap;

public class IdentityAndWeakHashMapDemo {

    // Basic: IdentityHashMap treats equals()-equal-but-distinct objects as DIFFERENT keys.
    static void basicLevel() {
        Map<String, Integer> normalMap = new java.util.HashMap<>();
        String key1 = new String("shared"); // deliberately using `new` to force a distinct object
        String key2 = new String("shared"); // equal content, different object
        normalMap.put(key1, 100);
        System.out.println("basic: normal HashMap, key2 (equals()-equal) finds key1's value -> " + normalMap.get(key2));

        Map<String, Integer> identityMap = new IdentityHashMap<>();
        identityMap.put(key1, 100);
        System.out.println("basic: IdentityHashMap, key2 (equals()-equal but NOT the same object) -> " + identityMap.get(key2));
        System.out.println("basic: IdentityHashMap, key1 itself (the exact object) -> " + identityMap.get(key1));
    }

    // Intermediate: IdentityHashMap as a cycle-detector while walking a graph -- the classic real use case.
    static class Node {
        String name;
        java.util.List<Node> neighbors = new java.util.ArrayList<>();
        Node(String name) { this.name = name; }
    }

    static void printGraphSafely(Node start) {
        Map<Node, Boolean> visited = new IdentityHashMap<>(); // identity matters: two DIFFERENT nodes could hold equal names
        java.util.Deque<Node> stack = new java.util.ArrayDeque<>();
        stack.push(start);
        StringBuilder order = new StringBuilder();

        while (!stack.isEmpty()) {
            Node node = stack.pop();
            if (visited.put(node, true) != null) continue; // already visited THIS exact node instance
            order.append(node.name).append(" ");
            for (Node neighbor : node.neighbors) stack.push(neighbor);
        }
        System.out.println("intermediate: safe traversal despite a cycle -> " + order.toString().trim());
    }

    static void intermediateLevel() {
        Node a = new Node("A"), b = new Node("B"), c = new Node("C");
        a.neighbors.add(b);
        b.neighbors.add(c);
        c.neighbors.add(a); // cycle: C points back to A
        printGraphSafely(a);
    }

    // Advanced: WeakHashMap -- an entry disappears once nothing else references its key.
    static void advancedLevel() throws InterruptedException {
        Map<Object, String> weakMap = new WeakHashMap<>();
        Object key = new Object();
        weakMap.put(key, "metadata for key");
        System.out.println("advanced: before releasing the strong reference, size -> " + weakMap.size());

        key = null; // drop the only strong reference to the key object
        System.gc(); // request garbage collection (not guaranteed to run immediately, but very likely to for this demo)
        Thread.sleep(100); // give the collector a brief moment to run

        System.out.println("advanced: after GC, with no strong references left, size -> " + weakMap.size() + " (entry auto-removed, or soon will be)");
    }

    public static void main(String[] args) throws InterruptedException {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

**How to run:** save as `IdentityAndWeakHashMapDemo.java`, then run `java IdentityAndWeakHashMapDemo.java`.

## 6. Walkthrough

1. `basicLevel()` creates two distinct `String` objects with identical content. A normal `HashMap` treats `key2`'s lookup as a hit, since `equals()` says they match. An `IdentityHashMap` treats the same lookup as a miss (`null`), because `key1 != key2` as objects — only looking up the *exact* `key1` reference succeeds.
2. `intermediateLevel()` uses `IdentityHashMap` to safely walk a graph containing a cycle (`A -> B -> C -> A`). Using reference identity for the visited-set is correct here: even if two distinct `Node` objects happened to have equal `name` fields, they are still different nodes that should both be visited — identity, not content equality, is what "already visited this node" actually means.
3. `advancedLevel()` inserts an entry into a `WeakHashMap`, then drops the only strong reference to its key (`key = null`) and requests garbage collection. Once the collector reclaims the now-unreferenced key object, the map's entry for it is automatically removed — `size()` drops back to `0` without any explicit `remove()` call.

## 7. Gotchas & takeaways

> Gotcha: `System.gc()` is only a *request*, not a guarantee — relying on immediate garbage collection in production code (rather than a demo) is unreliable; `WeakHashMap` entries disappear on the collector's own schedule, which could be later than expected, and code should never assume an entry is gone by a specific instant.

- `IdentityHashMap` compares keys by `==` (reference identity), not `equals()` — used for cycle detection and identity-sensitive bookkeeping.
- `WeakHashMap` holds keys weakly, letting entries vanish automatically once their key is no longer referenced elsewhere — useful for caches keyed by objects you don't control the lifecycle of.
- Both intentionally break a `HashMap` assumption most code relies on; use them only when that specific behavior is actually needed.
- Related concepts: [hashCode/equals for correct keys](0093-hashcode-equals-for-correct-keys.md), [Stack vs heap allocation](0011-stack-vs-heap-allocation.md).
