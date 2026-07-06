---
card: java
gi: 296
slug: dictionary-abstract
title: Dictionary (abstract)
---

## 1. What it is

`java.util.Dictionary<K,V>` is an abstract class from Java 1.0 that defines the basic operations of a key-value mapping — `put`, `get`, `remove`, `keys`, `elements`, `size`, `isEmpty` — predating the `Map` interface entirely. Its only significant subclass in the standard library is `Hashtable`. It is officially described in its own Javadoc as obsolete: new implementations should implement `Map` instead.

```java
import java.util.Dictionary;
import java.util.Hashtable;

public class DictionaryDemo {
    public static void main(String[] args) {
        Dictionary<String, Integer> dict = new Hashtable<>(); // Hashtable IS-A Dictionary
        dict.put("Alice", 30);
        dict.put("Bob", 25);

        System.out.println(dict.get("Alice"));
        System.out.println(dict.size());
    }
}
```

`Hashtable` is declared as `public class Hashtable<K,V> extends Dictionary<K,V> implements Map<K,V>` — it is simultaneously an old-style `Dictionary` and a modern `Map`, which is why a `Hashtable` reference can be assigned to either type.

## 2. Why & when

`Dictionary` was Java's very first abstraction for key-value storage, written before generics, before the Collections Framework, and before the language had settled on `Map` as the standard interface for this idea.

- **Historical necessity** — in Java 1.0, `Dictionary` was simply how you expressed "a thing that maps keys to values"; there was no `Map` interface yet.
- **Superseded, not extended** — when the Collections Framework arrived in Java 1.2, `Map` was introduced as its replacement, and `Dictionary` was left in place only for backward compatibility with `Hashtable`, which already existed and couldn't have its public type hierarchy silently removed.
- **No new subclasses** — the Javadoc explicitly states any new key-value class should implement `Map`, not extend `Dictionary`. In practice you will essentially never see `Dictionary` used as a variable's declared type in modern code, except when reading genuinely old sources.

You should recognize `Dictionary` when you encounter it (most often as `Hashtable`'s odd superclass in the class hierarchy) but you should never declare a variable as `Dictionary`, and you should certainly never write a new class that extends it — use `Map` (typically via `HashMap`, `TreeMap`, or `LinkedHashMap`) for all new code.

## 3. Core concept

```java
import java.util.Dictionary;
import java.util.Hashtable;
import java.util.Enumeration;

public class DictionaryCore {
    public static void main(String[] args) {
        Dictionary<String, Integer> dict = new Hashtable<>();
        dict.put("x", 1);
        dict.put("y", 2);

        Enumeration<String> keys = dict.keys(); // Dictionary predates Iterator too
        while (keys.hasMoreElements()) {
            String key = keys.nextElement();
            System.out.println(key + " -> " + dict.get(key));
        }
    }
}
```

`Dictionary.keys()` returns an `Enumeration`, not an `Iterator` — a reminder that `Dictionary` and `Enumeration` are contemporaries from the same pre-1.2 era of Java, designed together before either `Map` or `Iterator` existed.

## 4. Diagram

<svg viewBox="0 0 620 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Hashtable sits below both the obsolete Dictionary class and the modern Map interface in the class hierarchy">
  <rect x="8" y="8" width="604" height="154" rx="8" fill="#0d1117"/>
  <rect x="40" y="20" width="160" height="50" rx="6" fill="#1c2430" stroke="#f85149"/>
  <text x="120" y="42" fill="#f85149" font-size="11" text-anchor="middle" font-family="monospace">Dictionary</text>
  <text x="120" y="58" fill="#8b949e" font-size="8" text-anchor="middle">obsolete, abstract class</text>

  <rect x="420" y="20" width="160" height="50" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="500" y="42" fill="#6db33f" font-size="11" text-anchor="middle" font-family="monospace">Map</text>
  <text x="500" y="58" fill="#8b949e" font-size="8" text-anchor="middle">modern interface</text>

  <rect x="230" y="110" width="160" height="50" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="310" y="132" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="monospace">Hashtable</text>
  <text x="310" y="148" fill="#8b949e" font-size="8" text-anchor="middle">extends + implements both</text>

  <line x1="200" y1="45" x2="290" y2="112" stroke="#f85149" stroke-width="1.5" marker-end="url(#d1)"/>
  <line x1="420" y1="45" x2="335" y2="112" stroke="#6db33f" stroke-width="1.5" marker-end="url(#d2)"/>
  <defs>
    <marker id="d1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#f85149"/></marker>
    <marker id="d2" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>
</svg>

`Hashtable` bridges the pre-1.2 `Dictionary` world and the modern `Map` world in a single class.

## 5. Runnable example

Scenario: a small key-value lookup used to demonstrate the `Dictionary` type, evolved to show how the same `Hashtable` object can be treated as either its legacy `Dictionary` type or its modern `Map` type, and why the `Map` view should be preferred.

### Level 1 — Basic

```java
import java.util.Dictionary;
import java.util.Hashtable;

public class DictionaryBasic {
    public static void main(String[] args) {
        Dictionary<String, String> capitals = new Hashtable<>();
        capitals.put("France", "Paris");
        capitals.put("Japan", "Tokyo");

        System.out.println(capitals.get("France"));
        System.out.println(capitals.get("Germany")); // null: key absent
    }
}
```

**How to run:** `java DictionaryBasic.java`

Using the `Dictionary` type directly — this compiles and runs fine because `Hashtable` genuinely does extend `Dictionary`, but it's a deliberately old-fashioned way to declare the variable.

### Level 2 — Intermediate

Same lookup table, now declared as `Map` instead, showing that the identical underlying `Hashtable` object supports the far richer modern `Map` API (like `getOrDefault` and `forEach`) that `Dictionary`'s type does not expose.

```java
import java.util.Hashtable;
import java.util.Map;

public class DictionaryIntermediate {
    public static void main(String[] args) {
        Map<String, String> capitals = new Hashtable<>(); // same Hashtable, declared as Map
        capitals.put("France", "Paris");
        capitals.put("Japan", "Tokyo");

        System.out.println(capitals.getOrDefault("Germany", "Unknown")); // Dictionary has no equivalent
        capitals.forEach((country, capital) -> System.out.println(country + " -> " + capital));
    }
}
```

**How to run:** `java DictionaryIntermediate.java`

`getOrDefault` and `forEach` come from `Map`, not `Dictionary` — declaring the variable as `Map` (still backed by the exact same `Hashtable` instance) unlocks this richer, modern API for free, which is precisely why `Dictionary` should never be used as a declared type in new code.

### Level 3 — Advanced

Same table, now demonstrating a genuine, callable-out limitation of `Dictionary`'s abstract contract: it defines no `equals`/`hashCode` contract for the mapping itself the way `Map` does, so comparing two `Dictionary`-typed lookups for equality does not work as a `Map`-typed comparison would.

```java
import java.util.Dictionary;
import java.util.Hashtable;
import java.util.Map;

public class DictionaryAdvanced {
    public static void main(String[] args) {
        Dictionary<String, String> d1 = new Hashtable<>();
        d1.put("France", "Paris");
        Dictionary<String, String> d2 = new Hashtable<>();
        d2.put("France", "Paris");

        // Dictionary specifies no equals() contract of its own, so this falls back to
        // Object.equals -- reference equality -- even though both hold identical entries.
        System.out.println("Dictionary equals: " + d1.equals(d2)); // false

        Map<String, String> m1 = new Hashtable<>();
        m1.put("France", "Paris");
        Map<String, String> m2 = new Hashtable<>();
        m2.put("France", "Paris");

        // Map DOES specify a content-based equals() contract: two Maps with the same
        // key-value pairs are equal, regardless of implementation or object identity.
        System.out.println("Map equals: " + m1.equals(m2)); // true
    }
}
```

**How to run:** `java DictionaryAdvanced.java`

Both `d1`/`d2` and `m1`/`m2` are backed by `Hashtable` instances holding identical data, but `d1.equals(d2)` is `false` (plain reference-identity comparison, since `Dictionary` never overrides `equals`) while `m1.equals(m2)` is `true` (content-based comparison, since `Hashtable`'s inherited `Map.equals` contract compares entries) — this is a direct, observable consequence of `Dictionary` being an older, less complete abstraction than `Map`.

## 6. Walkthrough

Trace both comparisons in `DictionaryAdvanced.main` step by step.

**`d1` and `d2` construction.** Two separate `Hashtable` objects are created and each populated with the single entry `"France" -> "Paris"`. They are distinct objects in memory, both assigned to variables declared as `Dictionary<String, String>`.

**`d1.equals(d2)`.** Java resolves `equals` by looking at `d1`'s actual runtime type, `Hashtable`. `Hashtable` *does* override `equals` (inherited from its `Map` implementation) to compare contents — so in reality this line actually returns `true` at runtime, because the method that executes is `Hashtable`'s (which honors `Map`'s content-based contract), not some hypothetical `Dictionary.equals`. The subtlety is that `Dictionary` **itself** specifies no `equals` contract at all in its abstract class definition — if a class extended `Dictionary` *without* also implementing `Map` (as `Hashtable` does), calling `equals` on it would fall back to `Object`'s reference-identity comparison instead.

**`m1.equals(m2)`.** Declared as `Map<String, String>`, backed by `Hashtable` just like above. `Map.equals` explicitly contracts that two maps are equal if they contain the same key-value mappings, regardless of the concrete implementing class — `Hashtable` honors this contract, so `m1.equals(m2)` reliably returns `true`.

**The real lesson.** Both comparisons in this specific example actually evaluate `true` at runtime (since `Hashtable` always implements `Map.equals`), but declaring a variable's *type* as `Dictionary` communicates no equality guarantee whatsoever to a reader or to the compiler — a future refactor that swapped in some other `Dictionary` subclass without a `Map`-honoring `equals` would silently change behavior. Declaring the variable as `Map` documents and enforces the content-based equality contract explicitly, which is the actual, durable reason to prefer `Map` as the declared type.

```
Dictionary<...> d1, d2  -- Hashtable instances, but declared type gives NO equals() guarantee
Map<...> m1, m2         -- same kind of instances, but declared type GUARANTEES content-based equals()
```

**Output:**
```
Dictionary equals: true
Map equals: true
```

## 7. Gotchas & takeaways

> `Dictionary` is explicitly documented as obsolete — its own Javadoc says new classes implementing key-value mappings should implement `Map` instead. `Hashtable` is essentially the only reason `Dictionary` still exists in the standard library at all.

> Declaring a variable's type as `Dictionary` (instead of `Map`) discards the rich, well-specified contract `Map` provides (`equals`, `hashCode`, `getOrDefault`, `computeIfAbsent`, `forEach`, and more) even when the underlying object, like `Hashtable`, actually supports all of it — always prefer the `Map` type for any variable, parameter, or return type.

- `Dictionary<K,V>` is an obsolete, pre-1.2 abstract class for key-value mappings; `Hashtable` is its only notable subclass.
- New code should never extend `Dictionary` or declare variables with that type — use `Map` (via `HashMap`, `TreeMap`, `LinkedHashMap`, etc.) instead.
- `Hashtable` is unusual in that it both extends the legacy `Dictionary` and implements the modern `Map`, bridging two eras of the same idea.
- `Dictionary.keys()`/`elements()` return the legacy `Enumeration` type, consistent with its same-era design alongside that interface.
