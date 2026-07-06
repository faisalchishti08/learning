---
card: java
gi: 352
slug: type-parameter-naming-conventions-t-e-k-v-n
title: Type parameter naming conventions (T, E, K, V, N, ?)
---

## 1. What it is

Java has no enforced rule about what letters you use for a generic type parameter — `T`, `Banana`, or `X1` would all compile identically — but the Java community (and the JDK itself) follows a widely-adopted single-letter naming convention that makes generic code instantly readable to anyone familiar with it: `T` for a general Type, `E` for a collection Element, `K`/`V` for a map's Key/Value pair, `N` for a Number, and `R` for a method's Return type, with `?` reserved for wildcards rather than a declared type parameter at all.

```java
import java.util.List;
import java.util.Map;

public class NamingDemo {
    static class Box<T> {} // T: general-purpose type
    interface Repository<E> { void save(E entity); } // E: an "element" this repository manages
    static class Cache<K, V> { V get(K key) { return null; } } // K/V: key and value types

    public static void main(String[] args) {
        List<String> names = List.of("Ada", "Grace"); // JDK's own List<E> uses E internally
        Map<String, Integer> ages = Map.of("Ada", 36); // JDK's own Map<K, V>
        System.out.println(names);
        System.out.println(ages);
    }
}
```

Even though `Box<T>`, `Repository<E>`, and `Cache<K, V>` could have used any letters at all, following the convention (`T` for a plain container, `E` for something a collection-like type manages, `K`/`V` for a key/value pairing) immediately signals each type parameter's intended role to any reader familiar with Java's own libraries.

## 2. Why & when

Generic code can otherwise be genuinely hard to read — a class with type parameters named arbitrarily forces readers to trace through the whole definition to understand what each one represents. Consistent naming conventions let experienced Java developers recognize a type parameter's role at a glance, purely from its letter, before reading any further detail.

- **Matching JDK and community conventions** — the entire Java standard library uses these conventions (`List<E>`, `Map<K, V>`, `Function<T, R>`), so following them keeps your own generic code consistent with everything developers already know.
- **Communicating intent without extra documentation** — seeing `K` and `V` in a class signature immediately suggests "this is some kind of key-value structure," without needing to read a comment explaining it.
- **Distinguishing multiple type parameters clearly** — when a class or method has more than one type parameter, using conventionally distinct letters (rather than, say, `T1` and `T2`) makes each one's role clearer at the declaration site and throughout the body.

The convention is just that — a convention, not a compiler-enforced rule — so nothing stops you from naming a type parameter `Fruit` or `X`; but doing so, especially in code meant to be read or maintained by others familiar with typical Java style, creates friction for no real benefit, since the standard letters already communicate the same information more efficiently.

## 3. Core concept

```java
import java.util.function.Function;

public class NamingCore {
    // Function<T, R> from the JDK: T = input Type, R = Return type
    static <T, R> R apply(T input, Function<T, R> transformer) {
        return transformer.apply(input);
    }

    public static void main(String[] args) {
        String result = apply(42, n -> "Number was: " + n); // T=Integer, R=String
        System.out.println(result);

        Integer length = apply("hello world", String::length); // T=String, R=Integer
        System.out.println(length);
    }
}
```

**How to run:** `java NamingCore.java`

`apply`'s signature reads clearly even before looking at its body: `T` is whatever input type is provided, `R` is whatever result type comes back — exactly matching the same `T`/`R` convention the JDK's own `java.util.function.Function<T, R>` uses.

## 4. Diagram

<svg viewBox="0 0 600 160" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="the standard letter conventions and what each typically represents: T general type, E collection element, K/V map key and value, N number, R return type">
  <rect x="8" y="8" width="584" height="144" rx="8" fill="#0d1117"/>
  <text x="20" y="30" fill="#79c0ff" font-size="11">T</text><text x="45" y="30" fill="#8b949e" font-size="10">— general-purpose Type (Box&lt;T&gt;)</text>
  <text x="20" y="55" fill="#79c0ff" font-size="11">E</text><text x="45" y="55" fill="#8b949e" font-size="10">— collection Element (List&lt;E&gt;)</text>
  <text x="20" y="80" fill="#79c0ff" font-size="11">K, V</text><text x="65" y="80" fill="#8b949e" font-size="10">— map Key and Value (Map&lt;K, V&gt;)</text>
  <text x="20" y="105" fill="#79c0ff" font-size="11">N</text><text x="45" y="105" fill="#8b949e" font-size="10">— a Number type (bounded, e.g. N extends Number)</text>
  <text x="20" y="130" fill="#79c0ff" font-size="11">R</text><text x="45" y="130" fill="#8b949e" font-size="10">— method Return type (Function&lt;T, R&gt;)</text>
</svg>

## 5. Runnable example

Scenario: a small generic in-memory key-value cache, evolved from arbitrarily-named type parameters that obscure the class's purpose, into conventionally-named ones that instantly clarify it, into a production-style cache with a bounded numeric type parameter following the `N` convention for a size-limited numeric statistic.

### Level 1 — Basic

```java
import java.util.HashMap;
import java.util.Map;

public class CacheBasic<A, B> { // poorly named -- what do A and B even represent?
    private final Map<A, B> store = new HashMap<>();

    public void put(A a, B b) { store.put(a, b); }
    public B get(A a) { return store.get(a); }

    public static void main(String[] args) {
        CacheBasic<String, Integer> cache = new CacheBasic<>();
        cache.put("Ada", 36);
        System.out.println(cache.get("Ada"));
    }
}
```

**How to run:** `java CacheBasic.java`

`A` and `B` compile perfectly fine and behave identically to any other letters, but a reader seeing `CacheBasic<A, B>` for the first time has no immediate clue which one is the lookup key and which is the stored value — they'd have to read into the method bodies to figure it out.

### Level 2 — Intermediate

```java
import java.util.HashMap;
import java.util.Map;

public class CacheIntermediate<K, V> { // K/V immediately signals key-value semantics
    private final Map<K, V> store = new HashMap<>();

    public void put(K key, V value) { store.put(key, value); }
    public V get(K key) { return store.get(key); }
    public boolean containsKey(K key) { return store.containsKey(key); }

    public static void main(String[] args) {
        CacheIntermediate<String, Integer> cache = new CacheIntermediate<>();
        cache.put("Ada", 36);
        System.out.println("Contains 'Ada'? " + cache.containsKey("Ada"));
        System.out.println("Value: " + cache.get("Ada"));
    }
}
```

**How to run:** `java CacheIntermediate.java`

Simply renaming the type parameters to `K` and `V` — with no other change to the class's behavior — makes its purpose immediately legible: any Java developer sees `CacheIntermediate<K, V>` and correctly assumes "this is a key-value structure" before reading a single method body.

### Level 3 — Advanced

```java
import java.util.HashMap;
import java.util.Map;

public class CacheAdvanced<K, V> {
    private final Map<K, V> store = new HashMap<>();
    private final int maxSize;

    public CacheAdvanced(int maxSize) { this.maxSize = maxSize; }

    public void put(K key, V value) {
        if (!store.containsKey(key) && store.size() >= maxSize) {
            throw new IllegalStateException("Cache is full (max size: " + maxSize + ")");
        }
        store.put(key, value);
    }

    public V get(K key) { return store.get(key); }

    // A generic method with its OWN type parameter N, following the "Number" convention,
    // bounded to require actual numeric behavior -- independent of this class's own K/V.
    static <N extends Number> double sumIfNumeric(java.util.List<N> values) {
        double sum = 0;
        for (N value : values) sum += value.doubleValue();
        return sum;
    }

    public static void main(String[] args) {
        CacheAdvanced<String, Integer> cache = new CacheAdvanced<>(2);
        cache.put("Ada", 36);
        cache.put("Grace", 85);
        try {
            cache.put("Alan", 41); // exceeds maxSize
        } catch (IllegalStateException e) {
            System.out.println("Rejected: " + e.getMessage());
        }

        double total = sumIfNumeric(java.util.List.of(cache.get("Ada"), cache.get("Grace")));
        System.out.println("Sum of cached ages: " + total);
    }
}
```

**How to run:** `java CacheAdvanced.java`

`sumIfNumeric`'s type parameter `N` (bounded with `extends Number`) is entirely independent of the enclosing class's `K`/`V` — following the `N`-for-Number convention here signals immediately that this method specifically requires a numeric type, distinct from the class's general key-value type parameters, without needing any comment to explain it.

## 6. Walkthrough

Execution starts in `main`, which creates `CacheAdvanced<String, Integer> cache = new CacheAdvanced<>(2)` — fixing `K = String`, `V = Integer`, with `maxSize = 2`.

`cache.put("Ada", 36)`: `store.containsKey("Ada")` is `false` and `store.size()` (0) is less than `maxSize` (2), so the check passes and `"Ada" -> 36` is added. `cache.put("Grace", 85)`: similarly, `store.size()` is now 1, still less than 2, so `"Grace" -> 85` is added — `store` now has 2 entries.

`cache.put("Alan", 41)`: `store.containsKey("Alan")` is `false`, and `store.size()` (2) is `>= maxSize` (2) — the condition is true, so `put` throws `IllegalStateException("Cache is full (max size: 2)")` before adding anything. The `catch` block in `main` prints `Rejected: Cache is full (max size: 2)`.

`main` then calls `cache.get("Ada")` (returns `36`) and `cache.get("Grace")` (returns `85`), passing both into `sumIfNumeric(List.of(36, 85))`. Inside `sumIfNumeric`, the compiler infers `N = Integer` for this call (since `Integer` extends `Number`, satisfying the bound). The loop iterates: `sum += 36.doubleValue()` makes `sum = 36.0`; `sum += 85.doubleValue()` makes `sum = 121.0`. The method returns `121.0`.

Back in `main`, `total` is `121.0`, printed as `Sum of cached ages: 121.0`.

<svg viewBox="0 0 640 160" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="two puts succeed filling the cache to its max size, a third is rejected, then the cached values are summed via a separately-typed generic numeric helper method">
  <rect x="8" y="8" width="624" height="144" rx="8" fill="#0d1117"/>
  <text x="20" y="30" fill="#6db33f" font-size="10">put("Ada",36), put("Grace",85) -&gt; store size reaches maxSize=2</text>
  <text x="20" y="55" fill="#f85149" font-size="10">put("Alan",41) -&gt; size()&gt;=maxSize -&gt; IllegalStateException, rejected</text>
  <text x="20" y="85" fill="#79c0ff" font-size="10">sumIfNumeric([36, 85]) -&gt; N inferred as Integer -&gt; sum = 36.0 + 85.0 = 121.0</text>
  <text x="20" y="115" fill="#8b949e" font-size="10">Cache's K/V type parameters and sumIfNumeric's own N are entirely independent of each other.</text>
</svg>

## 7. Gotchas & takeaways

> Using non-conventional letters (or worse, misleading ones — like naming a map's value type `K`) doesn't break anything at compile time, but it actively works against readers' expectations, since most Java developers have internalized `K`/`V` meaning "key/value" and `E` meaning "element" from years of exposure to the JDK's own generic types.

- `T` for a general type, `E` for a collection element, `K`/`V` for a map's key/value pair, `N` for a number, `R` for a method's return type — these are conventions, not compiler rules, but following them makes generic code far more readable.
- The JDK's own generic types (`List<E>`, `Map<K, V>`, `Function<T, R>`, `Comparable<T>`) establish and reinforce these conventions — matching them keeps your code consistent with code every Java developer already knows.
- When a class or method needs more than the standard handful of letters, it's often a sign the design itself might benefit from fewer type parameters, or from named, more descriptive types instead of many generic placeholders.
- A method's own type parameter (like `<N extends Number>`) is independent of any type parameters the enclosing class declares — the letter chosen for one has no relationship to the letters used for the other, beyond convention guiding both choices sensibly.
- Reserve `?` specifically for wildcards (a topic in its own right) — it is not a declared type parameter and cannot be used the way `T`, `E`, `K`, or `V` are, since a wildcard has no name to refer to within the method or class body.
