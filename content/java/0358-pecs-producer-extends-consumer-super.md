---
card: java
gi: 358
slug: pecs-producer-extends-consumer-super
title: PECS (Producer Extends, Consumer Super)
---

## 1. What it is

PECS — "Producer Extends, Consumer Super" — is the standard mnemonic (popularized by Joshua Bloch's *Effective Java*) for deciding which wildcard form to use on a generic parameter: if the parameter is a **producer** (your code only *reads* values out of it), bound it with `? extends T`; if it's a **consumer** (your code only *writes* values into it), bound it with `? super T`. If a parameter is used as both a producer and a consumer, no wildcard works — it needs an exact, unbounded type parameter instead.

```java
import java.util.List;

public class PecsDemo {
    // source is a PRODUCER (we only read from it) -> extends
    // destination is a CONSUMER (we only write to it) -> super
    static <T> void copy(List<? extends T> source, List<? super T> destination) {
        for (T item : source) {
            destination.add(item);
        }
    }

    public static void main(String[] args) {
        List<Integer> ints = List.of(1, 2, 3);
        List<Number> numbers = new java.util.ArrayList<>();
        copy(ints, numbers);
        System.out.println(numbers);
    }
}
```

`source` is bounded with `extends` because `copy` only ever reads from it; `destination` is bounded with `super` because `copy` only ever writes into it — applying PECS to each parameter independently based on how *that specific parameter* is actually used inside the method.

## 2. Why & when

Deciding between `extends`, `super`, or no wildcard at all is a genuinely common source of confusion when writing generic APIs — PECS gives a simple, mechanical rule that removes the guesswork: look at how the parameter is used in the method body, not at what "feels" more natural, and the correct wildcard follows directly.

- **Designing flexible generic method signatures** — applying PECS to every generic collection parameter independently produces APIs that accept the widest possible range of valid caller types, without sacrificing type safety.
- **Explaining and remembering wildcard choice** — rather than memorizing when to use each wildcard form abstractly, PECS reduces the decision to a concrete question: "does this method only read from this parameter, only write to it, or both?"
- **Matching JDK conventions** — the standard library's own generic APIs (`Collections.copy`, `Collections.max`, and many `Stream` operations) consistently follow PECS, so recognizing the pattern helps you read (and predict) their signatures too.

If a parameter is used as *both* a producer and a consumer within the same method — you read a value out of it and later add a different value back into it, depending on it being one consistent type — neither wildcard works, since each only guarantees one direction (read *or* write) safely; that parameter needs to stay an exact, unbounded type parameter like `List<T>`.

## 3. Core concept

```java
import java.util.List;

public class PecsCore {
    // Producer only -- we read values out, never write in. Use extends.
    static double sum(List<? extends Number> producer) {
        double total = 0;
        for (Number n : producer) total += n.doubleValue();
        return total;
    }

    // Consumer only -- we write values in, never read out. Use super.
    static void fillWithZeros(List<? super Integer> consumer, int count) {
        for (int i = 0; i < count; i++) consumer.add(0);
    }

    // BOTH producer and consumer (reads AND writes the same list) -- no wildcard, use T directly.
    static <T> void replaceFirstWithLast(List<T> both) {
        if (both.size() < 2) return;
        T last = both.get(both.size() - 1); // reading (producer role)
        both.set(0, last);                   // writing (consumer role) -- needs the EXACT type
    }

    public static void main(String[] args) {
        System.out.println("Sum: " + sum(List.of(1, 2, 3)));

        List<Number> zeros = new java.util.ArrayList<>();
        fillWithZeros(zeros, 3);
        System.out.println("Zeros: " + zeros);

        List<String> letters = new java.util.ArrayList<>(List.of("a", "b", "c"));
        replaceFirstWithLast(letters);
        System.out.println("After replace: " + letters);
    }
}
```

**How to run:** `java PecsCore.java`

`replaceFirstWithLast` genuinely both reads (`get`) and writes (`set`) the same list — no wildcard form would let you safely do both, since `extends` forbids meaningful writes and `super` only lets you read back `Object`, so it correctly uses an exact `List<T>` instead.

## 4. Diagram

<svg viewBox="0 0 620 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="PECS decision flow: if a parameter is only read from, use extends; if only written to, use super; if both, use an exact type parameter with no wildcard">
  <rect x="8" y="8" width="604" height="154" rx="8" fill="#0d1117"/>
  <text x="20" y="30" fill="#e6edf3" font-size="11">Does the method only READ from this parameter?</text>
  <text x="40" y="55" fill="#6db33f" font-size="10">YES -&gt; it's a Producer -&gt; use "? extends T"</text>
  <text x="20" y="80" fill="#e6edf3" font-size="11">Does the method only WRITE into this parameter?</text>
  <text x="40" y="105" fill="#79c0ff" font-size="10">YES -&gt; it's a Consumer -&gt; use "? super T"</text>
  <text x="20" y="130" fill="#e6edf3" font-size="11">Does it do BOTH?</text>
  <text x="40" y="150" fill="#f85149" font-size="10">YES -&gt; no wildcard works -&gt; use exact type "T" directly</text>
</svg>

## 5. Runnable example

Scenario: a small collection-merging utility, evolved from one with an overly restrictive exact-type signature, into a PECS-correct wildcard version, into a production-style utility applying PECS across three parameters simultaneously — two producers and one consumer.

### Level 1 — Basic

```java
import java.util.List;
import java.util.ArrayList;

public class MergeBasic {
    static void mergeInto(List<Number> a, List<Number> b, List<Number> destination) { // no wildcards
        for (Number n : a) destination.add(n);
        for (Number n : b) destination.add(n);
    }

    public static void main(String[] args) {
        List<Number> a = List.of(1, 2);
        List<Number> b = List.of(3.5, 4.5);
        List<Number> destination = new ArrayList<>();
        mergeInto(a, b, destination);
        System.out.println(destination);
        // mergeInto(List.of(1, 2), b, destination); // would NOT compile: List<Integer> isn't List<Number>
    }
}
```

**How to run:** `java MergeBasic.java`

Without wildcards, `a` and `b` must be exactly `List<Number>` — a caller with a genuinely more specific `List<Integer>` (which conceptually should work fine as a producer of numbers) is rejected entirely, even though every `Integer` is a `Number`.

### Level 2 — Intermediate

```java
import java.util.List;
import java.util.ArrayList;

public class MergeIntermediate {
    // a and b are producers (read-only) -> extends; destination is a consumer (write-only) -> super
    static void mergeInto(List<? extends Number> a, List<? extends Number> b, List<? super Number> destination) {
        for (Number n : a) destination.add(n);
        for (Number n : b) destination.add(n);
    }

    public static void main(String[] args) {
        List<Integer> ints = List.of(1, 2);
        List<Double> doubles = List.of(3.5, 4.5);
        List<Object> destination = new ArrayList<>();
        mergeInto(ints, doubles, destination);
        System.out.println(destination);
    }
}
```

**How to run:** `java MergeIntermediate.java`

Applying PECS to each parameter independently — `a`/`b` as producers get `? extends Number`, `destination` as a consumer gets `? super Number` — now correctly accepts a `List<Integer>`, a `List<Double>`, and a `List<Object>` destination all at once, which the exact-type version could never do.

### Level 3 — Advanced

```java
import java.util.List;
import java.util.ArrayList;
import java.util.Comparator;

public class MergeAdvanced {
    static void mergeSortedInto(List<? extends Number> a, List<? extends Number> b,
                                 List<? super Number> destination, Comparator<Number> order) {
        List<Number> combined = new ArrayList<>();
        for (Number n : a) combined.add(n);
        for (Number n : b) combined.add(n);
        combined.sort(order); // combined is a genuinely exact List<Number> -- both read and written here
        for (Number n : combined) destination.add(n);
    }

    public static void main(String[] args) {
        List<Integer> ints = List.of(5, 1, 9);
        List<Double> doubles = List.of(3.3, 7.7);
        List<Number> destination = new ArrayList<>();

        mergeSortedInto(ints, doubles, destination, Comparator.comparingDouble(Number::doubleValue));
        System.out.println(destination);
    }
}
```

**How to run:** `java MergeAdvanced.java`

`combined` inside `mergeSortedInto` is deliberately an exact `List<Number>` (not a wildcard), because it's genuinely used as both a producer and a consumer — elements are added into it (consumer role) and then read back out after sorting (producer role) — demonstrating that PECS applies per-role, per-variable: the *parameters* correctly use wildcards since each has one fixed role, while the *local* `combined` list correctly avoids a wildcard since it plays both roles.

## 6. Walkthrough

Execution starts in `main`, which builds `ints` (`List<Integer>`), `doubles` (`List<Double>`), an empty `destination` (`List<Number>`), and a `Comparator<Number>` ordering by `doubleValue()`, then calls `mergeSortedInto(ints, doubles, destination, order)`.

Inside `mergeSortedInto`, `combined` is created as a fresh, empty `List<Number>`. The first loop, `for (Number n : a)`, reads each element of `ints` as a `Number` (upper bound satisfied) and adds it to `combined`: `5`, `1`, `9` are added in that order. The second loop does the same for `b` (`doubles`): `3.3`, `7.7` are added. `combined` now holds `[5, 1, 9, 3.3, 7.7]`, in insertion order.

`combined.sort(order)` sorts this list in place using the provided comparator, which compares by `doubleValue()`: the sorted result is `[1, 3.3, 5, 7.7, 9]`.

The final loop, `for (Number n : combined)`, reads each element of the now-sorted `combined` list and calls `destination.add(n)` — since `destination`'s real type (`List<Number>`) satisfies the lower bound `? super Number`, each addition is safe. After this loop, `destination` contains `[1, 3.3, 5, 7.7, 9]`.

Back in `main`, `destination` is printed as `[1, 3.3, 5, 7.7, 9]`.

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="elements from two producer sources are read into a local exact-type list, sorted there, then written out to the consumer destination">
  <rect x="8" y="8" width="624" height="154" rx="8" fill="#0d1117"/>
  <text x="20" y="30" fill="#79c0ff" font-size="10">read a (Integer producer) -&gt; combined: [5, 1, 9]</text>
  <text x="20" y="52" fill="#79c0ff" font-size="10">read b (Double producer) -&gt; combined: [5, 1, 9, 3.3, 7.7]</text>
  <text x="20" y="82" fill="#e6edf3" font-size="10">combined.sort(order) -&gt; [1, 3.3, 5, 7.7, 9]  (combined is exact List&lt;Number&gt;: both read AND written)</text>
  <text x="20" y="112" fill="#6db33f" font-size="10">write each sorted element into destination (consumer) -&gt; destination: [1, 3.3, 5, 7.7, 9]</text>
</svg>

## 7. Gotchas & takeaways

> Applying PECS to a parameter that's actually used as *both* a producer and a consumer is a mistake, not a valid third option — if you find yourself wanting to both `get()` a meaningful value and `add()` a specific one on the same wildcard-typed parameter, that's the signal the parameter needs an exact type instead, not a sign you picked the wrong wildcard direction.

- Producer (read-only) parameter → `? extends T`; Consumer (write-only) parameter → `? super T` — decide per parameter, based on how that specific parameter is used in the method body.
- A parameter used as both a producer and a consumer cannot use either wildcard safely — it needs to stay an exact type parameter, like `List<T>`.
- PECS is a mnemonic for a mechanical decision process, not a rule to memorize abstractly — trace how each parameter is actually used in the method, and the correct wildcard (or lack of one) follows directly.
- The JDK's own generic method signatures (`Collections.copy`, `Collections.max`, many `Stream`/`Collector` APIs) consistently follow PECS — recognizing the pattern helps you both write and read generic APIs more fluently.
- A local variable (not a parameter) can and often should use an exact type even when the surrounding method's parameters use wildcards, if that local variable itself plays both a producer and consumer role internally, exactly as `combined` does in the advanced example.
