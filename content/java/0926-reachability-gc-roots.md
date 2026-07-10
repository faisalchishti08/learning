---
card: java
gi: 926
slug: reachability-gc-roots
title: Reachability & GC roots
---

## 1. What it is

**Reachability** is the sole criterion the garbage collector uses to decide whether an object is still "alive" (must be kept) or is garbage (can be reclaimed): an object is reachable if there's a chain of references leading to it starting from a **GC root** — a fixed set of starting points the collector always treats as inherently alive, without needing anything else to reference them. GC roots include: local variables and parameters currently on any thread's [stack](0913-jvm-stacks-stack-frames.md), active `Thread` objects themselves, static fields of loaded classes, JNI references held by native code, and a few other JVM-internal special cases. The collector's core algorithm, at its heart, is simply: starting from every GC root, trace every reference transitively, and mark everything reached as alive — anything left unmarked afterward is unreachable, and therefore garbage.

## 2. Why & when

Understanding reachability precisely is the foundation for correctly predicting whether a given object will be collected, and for correctly diagnosing memory leaks in Java, which — since there's no manual `free()`/`delete` — always take the specific form of "something unreachable was expected, but a lingering reference chain from some GC root kept it reachable instead." This matters directly whenever debugging unexpectedly high memory usage: the question is never "did I forget to release this object," but always "what GC-root-rooted reference chain is still keeping this object reachable that shouldn't be" — a static field holding a collection that's never cleared, a listener registered with a long-lived object and never unregistered, a `ThreadLocal` set on a pooled thread and never removed (see [`ThreadLocal` memory leaks](0899-threadlocal-memory-leaks.md) for exactly this pattern). Heap-dump analysis tools work by constructing exactly this reachability graph and letting you trace the actual path from a GC root to a specific object you didn't expect to still be alive.

## 3. Core concept

```java
class Node { Node next; Object data; }

static Node cache; // a STATIC FIELD -- itself a GC root's direct target, always reachable

void demo() {
    Node local = new Node(); // LOCAL VARIABLE on the stack -- a GC root while this method runs
    local.data = new byte[1_000_000]; // reachable via: stack (GC root) -> local -> data

    cache = local; // NOW ALSO reachable via: static field (GC root) -> cache -> the SAME object

    // local goes out of scope when demo() returns -- but `cache` still references
    // the same object, so it remains reachable (and therefore NOT garbage) regardless.
}
```

An object is garbage the instant *every* chain of references from *every* GC root to it is broken — not merely when one particular reference (like a local variable) goes out of scope, if another reachable path to the same object still exists.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="GC roots -- thread stacks, static fields, active threads -- each pointing into a web of interconnected objects; anything reachable by tracing from a root is alive, anything left unreached is garbage">
  <text x="160" y="20" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">GC roots</text>
  <rect x="20" y="30" width="120" height="30" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="80" y="50" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">thread stack</text>
  <rect x="20" y="70" width="120" height="30" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="80" y="90" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">static field</text>

  <rect x="220" y="30" width="90" height="30" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="265" y="50" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Object A</text>
  <rect x="220" y="70" width="90" height="30" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="265" y="90" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Object B</text>
  <rect x="380" y="50" width="90" height="30" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="425" y="70" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Object C</text>

  <rect x="220" y="130" width="90" height="30" rx="6" fill="#1c2430" stroke="#f85149" stroke-dasharray="3"/>
  <text x="265" y="150" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Object D (garbage)</text>

  <line x1="140" y1="45" x2="220" y2="45" stroke="#8b949e" stroke-width="1.5" marker-end="url(#a53)"/>
  <line x1="140" y1="85" x2="220" y2="85" stroke="#8b949e" stroke-width="1.5" marker-end="url(#a53)"/>
  <line x1="310" y1="55" x2="380" y2="60" stroke="#8b949e" stroke-width="1.5" marker-end="url(#a53)"/>
  <text x="330" y="170" fill="#f85149" font-size="10" text-anchor="middle" font-family="sans-serif">Object D has NO path from any GC root -- unreachable, therefore garbage.</text>
  <defs><marker id="a53" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

*Reachability is purely about tracing paths from GC roots — an object with no such path, no matter how recently it was created or how large it is, is immediately eligible for collection.*

## 5. Runnable example

Scenario: directly demonstrating reachability's effect via `WeakReference`, growing from a basic local-variable-scope demonstration, to a case where a static field keeps an object reachable despite a local variable going out of scope, to a realistic "leak" pattern where an unexpected reference chain keeps something alive far longer than intended.

### Level 1 — Basic

```java
import java.lang.ref.*;

public class BasicReachability {
    static WeakReference<Object> tracker;

    static void createAndDrop() {
        Object local = new Object(); // reachable via the STACK (a GC root) while this method runs
        tracker = new WeakReference<>(local);
    } // `local` goes out of scope HERE -- no more references to it from any GC root

    public static void main(String[] args) throws InterruptedException {
        createAndDrop();
        System.gc();
        Thread.sleep(200);
        System.out.println("object still reachable after createAndDrop() returned? " + (tracker.get() != null));
    }
}
```

**How to run:** `java BasicReachability.java` (JDK 17+).

Expected output:
```
object still reachable after createAndDrop() returned? false
```

Once `createAndDrop()` returns, its local variable `local` — the only strong reference the object ever had — is gone from any thread's stack; with no remaining path from any GC root, the object becomes unreachable and is collected.

### Level 2 — Intermediate

```java
import java.lang.ref.*;

public class StaticFieldKeepsAlive {
    static Object cache; // a STATIC FIELD -- itself always reachable from a GC root
    static WeakReference<Object> tracker;

    static void createAndRetain() {
        Object local = new Object();
        tracker = new WeakReference<>(local);
        cache = local; // NOW also reachable via: static field -> cache -> the SAME object
    }

    public static void main(String[] args) throws InterruptedException {
        createAndRetain();
        System.gc();
        Thread.sleep(200);
        System.out.println("object still reachable (via static field) after method returned? " + (tracker.get() != null));

        cache = null; // remove the LAST remaining reachable path
        System.gc();
        Thread.sleep(200);
        System.out.println("object still reachable after clearing the static field too? " + (tracker.get() != null));
    }
}
```

**How to run:** `java StaticFieldKeepsAlive.java` (JDK 17+).

Expected output:
```
object still reachable (via static field) after method returned? true
object still reachable after clearing the static field too? false
```

The real-world concern added: even though `local`'s own stack-based reachability ends when `createAndRetain()` returns (exactly as in Level 1), the *same object* is also reachable via `cache`, a static field — since static fields are always reachable (a class, once loaded, is itself effectively a permanent GC root for its own static state), the object stays alive via this second path, and is only actually collected once `cache` itself is cleared, removing the last remaining path from any GC root.

### Level 3 — Advanced

```java
import java.lang.ref.*;
import java.util.*;

public class RealisticLeakPattern {
    // Simulates a long-lived, framework-level event bus that OUTLIVES individual "sessions"
    static List<Runnable> eventListeners = new ArrayList<>();

    static class UserSession {
        final byte[] sessionData = new byte[5_000_000]; // ~5MB of session-specific data
        void registerActivityListener() {
            // THE LEAK: registers a lambda that CAPTURES `this`, into a registry that
            // outlives the session's own intended lifetime.
            eventListeners.add(() -> System.out.println("activity for session with data length " + sessionData.length));
        }
    }

    public static void main(String[] args) throws InterruptedException {
        WeakReference<UserSession> sessionTracker;
        {
            UserSession session = new UserSession();
            session.registerActivityListener(); // registers a listener that keeps `session` reachable
            sessionTracker = new WeakReference<>(session);
        } // `session` (the local variable) goes out of scope HERE

        System.gc();
        Thread.sleep(200);
        System.out.println("session still reachable despite going out of scope? " + (sessionTracker.get() != null));
        System.out.println("(true -- eventListeners, a STATIC field, transitively still references it");
        System.out.println(" via the registered lambda, which captured `this`)");

        eventListeners.clear(); // the actual fix: remove the listener, breaking the last reachable path
        System.gc();
        Thread.sleep(200);
        System.out.println("session reachable after clearing eventListeners? " + (sessionTracker.get() != null));
    }
}
```

**How to run:** `java RealisticLeakPattern.java` (JDK 17+).

Expected output:
```
session still reachable despite going out of scope? true
(true -- eventListeners, a STATIC field, transitively still references it
 via the registered lambda, which captured `this`)
session reachable after clearing eventListeners? false
```

This adds the production-flavored hard case: a `UserSession` object whose only intended reference (a local variable) goes out of scope, yet remains reachable because it registered a lambda callback — capturing `this` — into a static, long-lived registry (`eventListeners`) that was never cleared. This is exactly the shape most real Java memory leaks take: not a missing `free()` call (Java has none), but an unexpected, still-live reference chain rooted in something genuinely long-lived (here, a `static` field, itself always reachable) that nobody remembered to break.

## 6. Walkthrough

Tracing why `sessionTracker.get()` returns non-null even after `session` goes out of scope:

1. `UserSession session = new UserSession();` creates the object; at this point, it's reachable via exactly one path: the local variable `session`, itself reachable because it's on `main`'s current stack frame (a GC root while `main` is executing).
2. `session.registerActivityListener()` adds a lambda to `eventListeners` — since this lambda's body references `sessionData` (an instance field), the lambda implicitly captures a reference to `session` itself (its enclosing instance) in order to access that field when eventually invoked.
3. `eventListeners` is a `static` field — meaning it's directly reachable from a GC root (the loaded `RealisticLeakPattern` class's own static state, which the JVM always treats as reachable for as long as the class remains loaded) — so everything `eventListeners` transitively references, including the newly-added lambda and, through it, `session`, is now *also* reachable via this second, independent path.
4. When the block containing `UserSession session = new UserSession();` ends, `session`'s scope as a local variable ends too — but this only removes *one* of the two reachable paths to the object; the path through `eventListeners` remains entirely intact and unaffected.
5. `System.gc()` traces reachability from every GC root, including `eventListeners` (via the loaded class's static state) — following that path leads to the lambda, and through the lambda's captured reference, to the `UserSession` object itself — so it's found reachable and is *not* collected, exactly matching `sessionTracker.get()` returning non-null.
6. Only once `eventListeners.clear()` actually removes the lambda (and hence its captured reference to `session`) does the last remaining path from any GC root to this object disappear — the subsequent `System.gc()` now finds it genuinely unreachable, and it's finally collected, matching `sessionTracker.get()` correctly returning `null`.

## 7. Gotchas & takeaways

> **Gotcha:** lambdas and inner (non-static) classes silently capture a reference to their enclosing instance whenever they reference any of that instance's fields or methods — this is easy to overlook, and is exactly the mechanism that let `UserSession` leak through `eventListeners` in the advanced example; a lambda registered with a long-lived collection can keep an entire "logically finished" object graph alive far longer than intended, purely through this implicit capture.

- Reachability — a traceable chain of references from some GC root — is the *sole* criterion for whether an object is alive; there is no other notion of "in use" in Java's memory model.
- GC roots include local variables/parameters on any thread's stack, active `Thread` objects, static fields of loaded classes, and JNI references held by native code.
- An object remains alive as long as *any* reachable path exists from *any* GC root, even if some other path (like a local variable that went out of scope) has been broken — all paths must be severed before an object becomes garbage.
- Java memory leaks always take the form of "an unexpected, still-live reference chain from some GC root keeps an object reachable longer than intended" — a static field, a long-lived listener registry, an un-cleared `ThreadLocal` (see [`ThreadLocal` memory leaks](0899-threadlocal-memory-leaks.md)) are the most common culprits.
- Lambdas and non-static inner classes implicitly capture a reference to their enclosing instance whenever they access its members — a subtle but common source of exactly this kind of unintended, prolonged reachability.
