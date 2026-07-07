---
card: java
gi: 362
slug: cannot-use-primitives-as-type-args
title: Cannot use primitives as type args
---

## 1. What it is

You cannot write `List<int>`, `Map<int, String>`, or any other generic type parameterized with a primitive (`int`, `double`, `boolean`, `char`, etc.). Type arguments must always be **reference types** — a class, an interface, an array type, or another generic type. To store primitives in a generic container, Java automatically substitutes the corresponding **wrapper class** (`int` → `Integer`, `double` → `Double`) through **autoboxing**, but you must write the wrapper name yourself in the type argument.

## 2. Why & when

Generics work by **erasure**: at compile time, `List<T>` becomes plain `List` internally, and every `T` is replaced with its bound (`Object` if unbounded). That erasure process only makes sense for reference types, because it relies on being able to store *any* type argument as an `Object` reference internally. Primitives are not objects — an `int` is a raw 32-bit value with no object header, no reference, nothing a generic erased-to-`Object` field could hold directly.

This matters constantly in everyday code: every time you write `List<Integer>` instead of the tempting-but-illegal `List<int>`, you're working around this rule. It also explains why a `List<Integer>` is measurably slower and more memory-hungry than a raw `int[]` — each element is a separate heap-allocated `Integer` object (with autoboxing/unboxing overhead on every access), not a packed primitive value. When performance on large primitive collections genuinely matters, specialized libraries with primitive-specialized collections (or plain arrays) avoid this cost, since generics itself offers no way out of it.

## 3. Core concept

```java
import java.util.List;
import java.util.ArrayList;

public class NoPrimitiveArgs {
    public static void main(String[] args) {
        // List<int> nums = new ArrayList<>(); // compile error: unexpected type

        List<Integer> nums = new ArrayList<>(); // wrapper class instead
        nums.add(1); // autoboxing: int 1 -> Integer.valueOf(1)
        nums.add(2);
        int first = nums.get(0); // auto-unboxing: Integer -> int
        System.out.println(first + nums.get(1));
    }
}
```

**How to run:** `java NoPrimitiveArgs.java`

`List<int>` is rejected outright by the compiler; `List<Integer>` is the only legal spelling. `nums.add(1)` silently boxes the literal `int 1` into an `Integer` object before storing it, and `int first = nums.get(0)` silently unboxes it back — the compiler inserts these conversions for you so the code reads almost like it holds primitives directly, even though it never actually does.

## 4. Diagram

<svg viewBox="0 0 640 160" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="a primitive int cannot be a generic type argument, so autoboxing converts it to an Integer object on the way into a generic collection, and unboxes it back on the way out">
  <rect x="8" y="8" width="624" height="144" rx="8" fill="#0d1117"/>
  <rect x="30" y="30" width="150" height="45" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="105" y="57" fill="#79c0ff" font-size="12" text-anchor="middle">int 42 (primitive)</text>

  <text x="200" y="47" fill="#8b949e" font-size="10">autobox -&gt;</text>

  <rect x="250" y="30" width="180" height="45" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="340" y="57" fill="#6db33f" font-size="12" text-anchor="middle">Integer.valueOf(42)</text>

  <text x="450" y="47" fill="#8b949e" font-size="10">stored in-&gt;</text>

  <rect x="500" y="30" width="110" height="45" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="555" y="57" fill="#6db33f" font-size="12" text-anchor="middle">List&lt;Integer&gt;</text>

  <text x="20" y="115" fill="#e6edf3" font-size="10">List&lt;int&gt; is illegal -- generics erase to Object internally, and a primitive isn't an object.</text>
  <text x="20" y="138" fill="#8b949e" font-size="10">get(0) reverses the trip: Integer is auto-unboxed back to int when assigned to a primitive variable.</text>
</svg>

## 5. Runnable example

Scenario: summing a list of numbers, evolved from a naive boxed version, through a version that reveals boxing's hidden costs, to a version that switches to a primitive array for the performance-sensitive path.

### Level 1 — Basic

```java
import java.util.List;
import java.util.ArrayList;

public class SumBasic {
    public static void main(String[] args) {
        List<Integer> numbers = new ArrayList<>(); // must use Integer, not int
        numbers.add(10);
        numbers.add(20);
        numbers.add(30);

        int total = 0;
        for (int n : numbers) { // each element auto-unboxed here
            total += n;
        }
        System.out.println("Total: " + total);
    }
}
```

**How to run:** `java SumBasic.java`

This is the everyday pattern: a `List<Integer>` holding boxed values, summed with an ordinary `int` accumulator. Each `n` in the loop is auto-unboxed from `Integer` to `int` before the addition — invisible in the source, but a real object-to-primitive conversion running underneath.

### Level 2 — Intermediate

```java
import java.util.List;
import java.util.ArrayList;

public class SumIntermediate {
    public static void main(String[] args) {
        List<Integer> numbers = new ArrayList<>();
        for (int i = 0; i < 5; i++) {
            numbers.add(i * 100); // 5 separate Integer objects boxed and stored
        }

        Integer total = 0; // boxed accumulator -- a common but costly mistake
        for (Integer n : numbers) {
            total = total + n; // unboxes both, adds as int, reboxes into a NEW Integer each time
        }
        System.out.println("Total: " + total + " (" + numbers.size() + " elements)");
    }
}
```

**How to run:** `java SumIntermediate.java`

Using `Integer total` instead of `int total` looks harmless but is a real-world trap: `total = total + n` unboxes both operands, computes the sum as a primitive `int`, then autoboxes the result into a brand-new `Integer` object every single iteration — five extra throwaway objects here, potentially millions in a hot loop over a large list.

### Level 3 — Advanced

```java
import java.util.List;
import java.util.ArrayList;

public class SumAdvanced {
    static long sumBoxed(List<Integer> numbers) {
        long total = 0; // primitive accumulator -- no repeated boxing of the running total
        for (int n : numbers) { // still one unbox per element, but no reboxing of the sum
            total += n;
        }
        return total;
    }

    static long sumPrimitiveArray(int[] numbers) {
        long total = 0;
        for (int n : numbers) { // no boxing at all -- numbers holds real ints
            total += n;
        }
        return total;
    }

    public static void main(String[] args) {
        int size = 1000;
        List<Integer> boxedList = new ArrayList<>(size);
        int[] primitiveArray = new int[size];
        for (int i = 0; i < size; i++) {
            boxedList.add(i);       // size boxed Integer objects allocated
            primitiveArray[i] = i;  // no allocation, just raw ints
        }

        System.out.println("Boxed sum: " + sumBoxed(boxedList));
        System.out.println("Primitive sum: " + sumPrimitiveArray(primitiveArray));
    }
}
```

**How to run:** `java SumAdvanced.java`

This contrasts the generic, boxed path (`List<Integer>`, unavoidable since generics forbid primitive type arguments) with a plain `int[]` path that never boxes anything. `sumBoxed` fixes the Level 2 mistake by using a primitive `long total`, but still pays one unboxing cost per element because the source is a `List<Integer>`; `sumPrimitiveArray` pays no boxing cost anywhere, since arrays — unlike generics — support primitives natively.

## 6. Walkthrough

Execution starts in `main`. The loop `for (int i = 0; i < size; i++)` runs 1000 times: each iteration calls `boxedList.add(i)`, which autoboxes the primitive `int i` into a new `Integer` object (`Integer.valueOf(i)`, cached for small values but freshly allocated once `i` exceeds the cache range) before storing it — so the list ends up holding 1000 separate `Integer` objects on the heap. The same iteration also does `primitiveArray[i] = i`, which just writes a raw 4-byte value into the array's contiguous memory — no object, no boxing.

`sumBoxed(boxedList)` is called next. Inside, `for (int n : numbers)` iterates the `List<Integer>`; on each step, the `Integer` element is auto-unboxed to the primitive `int n` before `total += n` runs. `total` itself is declared `long`, a primitive, so the running sum is never reboxed — only the per-element read pays an unboxing cost, not the accumulator. After 1000 iterations, `total` holds the correct sum and is returned.

`sumPrimitiveArray(primitiveArray)` runs the same logic, but `numbers` is already `int[]` — `for (int n : numbers)` just copies raw values, no boxing or unboxing anywhere in the loop.

Both calls print the same numeric result, since they're summing the same values (`0 + 1 + ... + 999`), but the boxed path allocated 1000 extra `Integer` objects along the way and the primitive path allocated none.

Expected output:
```
Boxed sum: 499500
Primitive sum: 499500
```

## 7. Gotchas & takeaways

> `Integer total = 0; total = total + n;` inside a loop looks identical to using a primitive `int`, but silently unboxes and reboxes on every iteration, allocating a new `Integer` object each time — always prefer a primitive accumulator (`int` or `long`) even when iterating over a boxed collection.

- Generic type arguments must be reference types; `List<int>` is illegal, `List<Integer>` is the only legal spelling for holding integers generically.
- Autoboxing/auto-unboxing make boxed and primitive code look nearly identical in source, but every crossing between `int` and `Integer` is a real runtime conversion with real cost.
- Small `Integer` values (roughly -128 to 127) are cached and reused by `Integer.valueOf`, so `==` comparisons can misleadingly appear to work for small numbers and fail for larger ones — always use `.equals()` or unbox before comparing boxed numbers.
- When summing or accumulating over a boxed collection, keep the accumulator itself as a primitive type to avoid repeated, unnecessary reboxing of the running total.
- For genuinely performance-critical code operating on large numeric datasets, prefer primitive arrays (or a primitive-specialized collection library) over `List<Integer>`, since generics offers no native way to avoid the boxing overhead.
