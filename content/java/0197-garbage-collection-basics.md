---
card: java
gi: 197
slug: garbage-collection-basics
title: Garbage collection basics
---

## 1. What it is

**Garbage collection (GC)** is the JVM's automatic process for reclaiming memory occupied by objects that are no longer **reachable** — meaning no live reference chain leads to them from anywhere the running program could still access (local variables on the call stack, static fields, or objects those in turn reference). Unlike languages that require manually freeing memory, Java never requires you to explicitly destroy an object; once nothing refers to it anymore, it becomes eligible for collection, and the garbage collector reclaims its memory automatically, at a time of its own choosing.

```java
class Big {
    int[] data = new int[1_000_000];
}

Big b = new Big();
// ... the Big object is reachable via 'b' here ...

b = null; // no more references to the original Big object anywhere
// the original object is now eligible for garbage collection
// (exactly WHEN it's actually collected is decided by the JVM, not this line)
```

Setting `b = null` doesn't destroy the object immediately — it simply removes the *only remaining reference* to it, making it eligible; the actual reclaiming of its memory happens later, whenever the garbage collector decides to run, invisibly to your code.

## 2. Why & when

Automatic garbage collection exists to eliminate an entire category of serious bugs that plague languages requiring manual memory management:

- **No manual `free()`/`delete` calls** — you never explicitly deallocate memory, which eliminates "use-after-free" bugs (accessing memory that's already been freed) and "double-free" bugs (freeing the same memory twice), both common, serious sources of crashes and security vulnerabilities in languages like C.
- **Automatic detection of reachability** — the garbage collector traces from a set of known "roots" (local variables currently on the stack, static fields, active thread state) through every reference, and anything it *cannot* reach this way is garbage, safe to reclaim.
- **You still need to be mindful of references you no longer need** — holding onto a reference longer than necessary (in a long-lived collection, a static field, or a listener that's never unregistered) keeps an object artificially reachable, preventing collection even though the object is logically "done" — this is how memory leaks happen in Java, despite there being no manual memory management at all.

You don't explicitly trigger garbage collection in ordinary code (though `System.gc()` exists as a *hint*, not a guarantee, that the JVM should run a collection soon); what you *do* control is how long references to objects are kept alive, which directly determines how soon those objects become eligible for collection.

## 3. Core concept

```java
public class GCDemo {
    static class Resource {
        String name;
        Resource(String name) { this.name = name; }

        @Override
        protected void finalize() { // deprecated in modern Java; shown here for illustration only
            System.out.println(name + " is being garbage collected");
        }
    }

    public static void main(String[] args) {
        Resource r = new Resource("Buffer A");
        System.out.println(r.name + " created and reachable");

        r = null; // Buffer A now has zero reachable references

        System.gc(); // a REQUEST, not a guarantee, that GC runs now
        System.out.println("Requested garbage collection");
    }
}
```

Setting `r = null` makes the original `Resource` object unreachable (assuming nothing else refers to it), and `System.gc()` merely *asks* the JVM to consider running a collection soon — it's not guaranteed to run immediately, or even at all before the program exits, which is part of why relying on `finalize()`-style cleanup (deprecated, and covered fully in the next topic) is fragile.

## 4. Diagram

<svg viewBox="0 0 600 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A set of GC roots including local variables and static fields with arrows tracing reachable objects, and one separate object with no incoming arrows from any root, marked as unreachable and eligible for collection">
  <rect x="8" y="8" width="584" height="154" rx="8" fill="#0d1117"/>
  <text x="300" y="24" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">GC roots trace reachability; anything unreached is eligible for collection</text>

  <rect x="30" y="45" width="90" height="30" rx="5" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="75" y="65" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">GC root</text>

  <line x1="120" y1="60" x2="200" y2="60" stroke="#6db33f" stroke-width="1.5" marker-end="url(#gc)"/>
  <rect x="200" y="45" width="100" height="30" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="250" y="65" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">reachable obj</text>

  <line x1="300" y1="60" x2="380" y2="60" stroke="#6db33f" stroke-width="1.5" marker-end="url(#gc)"/>
  <rect x="380" y="45" width="100" height="30" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="430" y="65" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">reachable obj</text>

  <rect x="200" y="110" width="140" height="30" rx="5" fill="#1c2430" stroke="#f85149" stroke-width="1.5" stroke-dasharray="3,2"/>
  <text x="270" y="130" fill="#f85149" font-size="9" text-anchor="middle" font-family="sans-serif">unreachable — eligible for GC</text>

  <defs><marker id="gc" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker></defs>
</svg>

Objects with no path from any GC root are unreachable, and their memory becomes eligible for automatic reclamation.

## 5. Runnable example

Scenario: a simple event log system holding recent entries — starting with basic reachability demonstrated through a nulled reference, then extending to show how a collection can accidentally keep objects reachable far longer than intended, then hardening into a bounded structure that deliberately releases old references to allow timely garbage collection.

### Level 1 — Basic

```java
public class LogBasic {
    static class Entry {
        String text;
        Entry(String text) { this.text = text; }
    }

    public static void main(String[] args) {
        Entry e = new Entry("Server started");
        System.out.println("Created: " + e.text);

        e = null; // the Entry object is now unreachable (nothing else refers to it)
        System.out.println("Reference cleared; object is now eligible for garbage collection");
    }
}
```

**How to run:** `java LogBasic.java`

After `e = null`, no variable anywhere in the program still refers to the original `Entry` object — it becomes eligible for garbage collection; exactly when the JVM actually reclaims its memory is left entirely up to the garbage collector, and typically isn't something well-behaved Java code needs to worry about or wait for.

### Level 2 — Intermediate

Same log idea, now demonstrating an unbounded list that accidentally keeps *every* entry reachable forever, unintentionally preventing garbage collection of old entries that are logically no longer needed.

```java
import java.util.ArrayList;
import java.util.List;

public class LogIntermediate {
    static class Entry {
        String text;
        Entry(String text) { this.text = text; }
    }

    public static void main(String[] args) {
        List<Entry> allEntries = new ArrayList<>(); // grows forever — a classic memory-leak shape

        for (int i = 0; i < 5; i++) {
            allEntries.add(new Entry("Event " + i));
        }

        System.out.println("Total entries retained: " + allEntries.size());
        // every single Entry ever added remains reachable via allEntries, forever,
        // even if only the most recent few are actually still useful
    }
}
```

**How to run:** `java LogIntermediate.java`

Every `Entry` added to `allEntries` remains reachable through that list for as long as `allEntries` itself is reachable — in a long-running program that keeps appending without ever removing old entries, this list (and every object inside it) would grow without bound, which is precisely the shape of a real-world Java memory leak, despite there being no manual memory management involved at all.

### Level 3 — Advanced

Same log, now hardened into a bounded structure that explicitly discards references to old entries once a capacity limit is reached, allowing the garbage collector to reclaim them promptly instead of retaining every entry forever.

```java
import java.util.LinkedList;

public class LogAdvanced {
    static class Entry {
        String text;
        Entry(String text) { this.text = text; }
    }

    static class BoundedLog {
        private final int capacity;
        private final LinkedList<Entry> entries = new LinkedList<>();

        BoundedLog(int capacity) {
            this.capacity = capacity;
        }

        void add(Entry entry) {
            entries.addLast(entry);
            if (entries.size() > capacity) {
                entries.removeFirst(); // drop the reference to the oldest entry — it becomes eligible for GC
            }
        }

        int size() {
            return entries.size();
        }
    }

    public static void main(String[] args) {
        BoundedLog log = new BoundedLog(3);

        for (int i = 0; i < 10; i++) {
            log.add(new Entry("Event " + i));
            System.out.println("After adding Event " + i + ", log size: " + log.size());
        }
    }
}
```

**How to run:** `java LogAdvanced.java`

`entries.removeFirst()` deliberately drops the `BoundedLog`'s own reference to the oldest `Entry` the moment the log exceeds its capacity — if nothing else in the program still holds a reference to that specific `Entry` object, it immediately becomes eligible for garbage collection, keeping the log's actual memory footprint bounded no matter how many events are added over the program's lifetime.

## 6. Walkthrough

Trace `LogAdvanced.main`'s loop for the addition of `"Event 3"` (the fourth entry, where `capacity = 3` first gets exceeded):

**State before.** `entries` already holds `[Event 0, Event 1, Event 2]` (3 entries, at capacity).

**`log.add(new Entry("Event 3"))`.** A new `Entry` object is created and `entries.addLast(entry)` appends it: `entries` becomes `[Event 0, Event 1, Event 2, Event 3]`, now 4 entries — one over capacity.

**Capacity check.** `entries.size() > capacity` is `4 > 3`, true. `entries.removeFirst()` removes and discards the `BoundedLog`'s reference to `Event 0` (the oldest). `entries` becomes `[Event 1, Event 2, Event 3]`, back to 3.

**Reachability.** Assuming nothing else in the program (no other list, no other variable) still refers to the `Event 0` object, it is now completely unreachable — eligible for garbage collection, even though the program is still running and hasn't finished its loop.

```
before: entries = [Event0, Event1, Event2]           (size 3, at capacity)
add Event3: entries = [Event0, Event1, Event2, Event3] (size 4, over capacity)
size() > capacity? 4 > 3 -> true -> removeFirst()
after: entries = [Event1, Event2, Event3]              (size 3, Event0 now unreachable)
```

**Full run.** For 10 total additions (`Event 0` through `Event 9`) with `capacity = 3`, the log's size prints as `1, 2, 3, 3, 3, 3, 3, 3, 3, 3` — growing to the capacity, then staying fixed there for every subsequent addition, while each displaced oldest entry becomes eligible for collection one at a time.

## 7. Gotchas & takeaways

> **`System.gc()` is only a request, never a guarantee — the JVM is free to ignore it entirely, and relying on it for correctness (rather than as a rare debugging aid) is a mistake.** Real Java code should never depend on garbage collection happening at any particular time; if deterministic cleanup is genuinely required (closing a file, releasing a network connection), use `try`-with-resources and the `AutoCloseable` interface instead, not garbage collection.

> **Holding a reference longer than necessary — in a growing collection, a static field, or an unregistered listener — is the primary cause of memory leaks in Java, despite there being no manual memory management at all.** The fix is always the same: explicitly remove or null out references to objects once they're genuinely no longer needed, exactly as `removeFirst()` does above.

- An object becomes eligible for garbage collection the moment nothing reachable (from the stack, static fields, or other reachable objects) still refers to it.
- The JVM decides when to actually run garbage collection; your code never explicitly frees memory.
- `System.gc()` is a hint, not a command — it does not force an immediate collection.
- Memory leaks in Java happen when references are kept alive longer than needed, most commonly in ever-growing collections; explicitly discarding old references (as a bounded structure does) keeps memory use in check.
