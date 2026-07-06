---
card: java
gi: 276
slug: parseint-parsedouble-valueof
title: parseInt / parseDouble / valueOf
---

## 1. What it is

Each wrapper class provides static methods for converting text into numbers: `parseXxx(String)` (like `Integer.parseInt` and `Double.parseDouble`) returns a plain *primitive* value, while `valueOf(String)` returns a *wrapper object* (internally calling the corresponding `parseXxx` method and then boxing the result). Both throw `NumberFormatException` if the given string isn't validly formatted for that type.

```java
public class ParseValueOfDemo {
    public static void main(String[] args) {
        int primitiveInt = Integer.parseInt("42");        // returns a primitive int
        Integer wrapperInt = Integer.valueOf("42");        // returns an Integer object

        double primitiveDouble = Double.parseDouble("3.14"); // returns a primitive double
        Double wrapperDouble = Double.valueOf("3.14");        // returns a Double object

        System.out.println(primitiveInt + " " + wrapperInt);
        System.out.println(primitiveDouble + " " + wrapperDouble);
    }
}
```

`Integer.parseInt("42")` gives you a plain `int` you can use directly in arithmetic without any unboxing step; `Integer.valueOf("42")` gives you an `Integer` object instead — useful when you specifically need a wrapper (for a generic collection, or to allow a `null` result elsewhere in your code), but requiring an unboxing step before ordinary arithmetic.

## 2. Why & when

Choosing between `parseXxx` and `valueOf` (and understanding what each actually returns) matters for writing code that's both correct and avoids unnecessary boxing overhead.

- **`parseXxx` when you need a primitive** — if the parsed value will immediately be used in arithmetic, stored in a primitive field, or otherwise never needs to be a wrapper object, `parseInt`/`parseDouble`/etc. avoid the (small, but real) overhead of creating a wrapper object you don't actually need.
- **`valueOf` when you need a wrapper object** — if the result needs to go into a generic collection (`List<Integer>`), be compared with `equals()` against another wrapper, or potentially be `null` somewhere downstream in your code's logic, `valueOf` gives you that wrapper object directly, without an extra explicit boxing step.
- **Both throw the same `NumberFormatException` for invalid input** — since `valueOf` internally calls the corresponding `parseXxx` method before boxing the result, both methods fail identically (same exception type, same triggering conditions) for text that isn't a validly formatted number — the choice between them is purely about what type of result you need, not about differing validation behaviour.

Use `parseXxx` as the default choice for converting text to a number you intend to use as a primitive (the vast majority of everyday parsing code); reach for `valueOf` specifically when you need the result as a wrapper object for a generic collection or similar reference-type context — understanding that `valueOf` is really just `parseXxx` plus autoboxing clarifies that there's no meaningful behavioural difference beyond the returned type.

## 3. Core concept

```java
public class ParseValueOfCore {
    public static void main(String[] args) {
        try {
            int result = Integer.parseInt("not-a-number");
        } catch (NumberFormatException e) {
            System.out.println("parseInt failed: " + e.getMessage());
        }

        try {
            Integer result = Integer.valueOf("not-a-number");
        } catch (NumberFormatException e) {
            System.out.println("valueOf failed: " + e.getMessage()); // SAME exception, SAME message
        }
    }
}
```

Both `parseInt` and `valueOf` throw the exact same `NumberFormatException`, with the exact same message, for the exact same invalid input — this confirms directly that `valueOf`'s validation logic is identical to `parseInt`'s (since it calls it internally), and the only real difference between the two methods is whether you get back a primitive or a wrapper object.

## 4. Diagram

<svg viewBox="0 0 600 160" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="parseInt returns a plain primitive int directly, valueOf calls parseInt internally and then boxes the result into an Integer object, both throw the identical NumberFormatException for invalid text">
  <rect x="8" y="8" width="584" height="144" rx="8" fill="#0d1117"/>

  <rect x="40" y="20" width="240" height="35" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="160" y="42" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="monospace">Integer.parseInt("42") -&gt; int</text>

  <rect x="320" y="20" width="240" height="35" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="440" y="42" fill="#6db33f" font-size="9" text-anchor="middle" font-family="monospace">Integer.valueOf("42") -&gt; Integer</text>

  <line x1="440" y1="55" x2="440" y2="75" stroke="#8b949e" stroke-width="1.5"/>
  <text x="440" y="72" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">internally: parseInt + box</text>

  <text x="300" y="120" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Both throw the IDENTICAL NumberFormatException for invalid text —</text>
  <text x="300" y="138" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">the only difference is the return type: primitive vs. wrapper object.</text>
</svg>

`valueOf` internally calls `parseXxx` and boxes the result; both share identical validation and failure behaviour.

## 5. Runnable example

Scenario: a CSV-style data parser reading numeric fields, evolved from basic primitive parsing into a version using `valueOf` for a generic collection, then hardened with robust validation and clear error reporting for malformed rows.

### Level 1 — Basic

```java
public class ParseValueOfBasic {
    public static void main(String[] args) {
        String[] fields = { "10", "20", "30" };
        int total = 0;
        for (String field : fields) {
            total += Integer.parseInt(field); // primitive result, used directly in arithmetic
        }
        System.out.println("Total: " + total);
    }
}
```

**How to run:** `java ParseValueOfBasic.java`

`Integer.parseInt(field)` returns a plain `int`, ready to use directly in the running sum — no wrapper object or unboxing step is needed at all, since the result is used purely as a primitive.

### Level 2 — Intermediate

Same idea, now collecting parsed values into a `List<Integer>` (which requires wrapper objects), using `Integer.valueOf` to obtain them directly.

```java
import java.util.ArrayList;
import java.util.List;

public class ParseValueOfIntermediate {
    public static void main(String[] args) {
        String[] fields = { "10", "20", "30" };
        List<Integer> values = new ArrayList<>();
        for (String field : fields) {
            values.add(Integer.valueOf(field)); // wrapper object, ready for the generic List
        }

        int total = 0;
        for (Integer value : values) {
            total += value; // auto-unboxed here for the addition
        }
        System.out.println("Values: " + values);
        System.out.println("Total: " + total);
    }
}
```

**How to run:** `java ParseValueOfIntermediate.java`

`Integer.valueOf(field)` produces an `Integer` object directly, suitable for `values.add(...)` (since `List<Integer>` requires wrapper objects, not primitives) — later, each `Integer` is auto-unboxed back into a primitive `int` for the summation, demonstrating both methods' typical, complementary use cases in one small program.

### Level 3 — Advanced

Same field-parsing idea, now handling a full row of mixed, possibly malformed data with `Double.parseDouble` and robust per-field error reporting, distinguishing genuinely missing fields (empty strings) from malformed ones (non-numeric text).

```java
import java.util.ArrayList;
import java.util.List;

public class ParseValueOfAdvanced {
    static Double parseFieldSafely(String field, int columnIndex, List<String> errors) {
        if (field == null || field.isBlank()) {
            errors.add("Column " + columnIndex + ": missing value");
            return null; // represents "no value" -- only possible because we're using the wrapper Double
        }
        try {
            return Double.valueOf(field.trim()); // wrapper object, may legitimately be null elsewhere
        } catch (NumberFormatException e) {
            errors.add("Column " + columnIndex + ": invalid number '" + field + "'");
            return null;
        }
    }

    public static void main(String[] args) {
        String[] row = { "19.99", "", "abc", "5.50" };
        List<String> errors = new ArrayList<>();
        List<Double> parsed = new ArrayList<>();

        for (int i = 0; i < row.length; i++) {
            parsed.add(parseFieldSafely(row[i], i, errors));
        }

        double total = 0;
        int validCount = 0;
        for (Double value : parsed) {
            if (value != null) { // must check for null before auto-unboxing, or risk NullPointerException
                total += value;
                validCount++;
            }
        }

        System.out.println("Valid values summed: " + total + " (from " + validCount + " of " + row.length + " fields)");
        System.out.println("Errors encountered:");
        for (String error : errors) System.out.println("  " + error);
    }
}
```

**How to run:** `java ParseValueOfAdvanced.java`

`parseFieldSafely` returns a `Double` (the wrapper), specifically so it can return `null` to represent "this field could not be parsed," which a primitive `double` could never express directly — the main loop then explicitly checks `value != null` before summing, exactly like the `Integer` example from the wrapper-classes topic, avoiding a `NullPointerException` from auto-unboxing a `null` reference.

## 6. Walkthrough

Trace `main` in `ParseValueOfAdvanced` field by field.

**`i = 0`, `row[0] = "19.99"`.** `parseFieldSafely("19.99", 0, errors)`: not `null` or blank. `Double.valueOf("19.99".trim())` succeeds, returning a `Double` wrapping `19.99`. No error added. `parsed` gains this value at index `0`.

**`i = 1`, `row[1] = ""`.** `parseFieldSafely("", 1, errors)`: `field.isBlank()` is `true`, so `errors.add("Column 1: missing value")` runs, and the method returns `null`. `parsed` gains `null` at index `1`.

**`i = 2`, `row[2] = "abc"`.** `parseFieldSafely("abc", 2, errors)`: not blank. `Double.valueOf("abc")` throws `NumberFormatException` internally (via its own call to `Double.parseDouble`). Caught: `errors.add("Column 2: invalid number 'abc'")` runs, and the method returns `null`. `parsed` gains `null` at index `2`.

**`i = 3`, `row[3] = "5.50"`.** `parseFieldSafely("5.50", 3, errors)`: not blank, `Double.valueOf("5.50")` succeeds, returning a `Double` wrapping `5.5`. No error. `parsed` gains this value at index `3`.

**Summing loop over `parsed = [19.99, null, null, 5.5]`.** For `19.99`: not `null`, `total += 19.99` makes `total = 19.99`, `validCount = 1`. For `null` (index 1): skipped, avoiding an unboxing `NullPointerException`. For `null` (index 2): skipped. For `5.5`: not `null`, `total += 5.5` makes `total = 25.49`, `validCount = 2`.

**Printing results.** `"Valid values summed: 25.49 (from 2 of 4 fields)"`, followed by the two accumulated error messages.

```
row = ["19.99", "", "abc", "5.50"]

parseFieldSafely("19.99", 0): valid -> Double 19.99, no error
parseFieldSafely("", 1):      blank -> null, error "Column 1: missing value"
parseFieldSafely("abc", 2):   NumberFormatException -> null, error "Column 2: invalid number 'abc'"
parseFieldSafely("5.50", 3):  valid -> Double 5.5, no error

parsed = [19.99, null, null, 5.5]
sum loop: 19.99 (count=1) -> skip null -> skip null -> +5.5 (count=2) -> total=25.49
```

**Final output.**
```
Valid values summed: 25.49 (from 2 of 4 fields)
Errors encountered:
  Column 1: missing value
  Column 2: invalid number 'abc'
```

## 7. Gotchas & takeaways

> **`Integer.valueOf` (and the other wrapper `valueOf` methods) may return a cached, shared object for small values, exactly as the wrapper-classes topic covered** — this has no effect on correctness (since `equals()` always compares value correctly), but it's worth remembering that `Integer.valueOf("100") == Integer.valueOf("100")` can legitimately be `true` due to caching, while the same comparison for larger values would be `false` — never rely on `==` to compare the results of `valueOf`, regardless of this caching detail.

> **Both `parseXxx` and `valueOf` throw `NumberFormatException` (a `RuntimeException`, unchecked) for malformed input — always validate untrusted text before parsing, or wrap the call in a `try`/`catch`, rather than assuming the input is always well-formed.** A blank string, `null` (which `parseInt` explicitly rejects with a `NumberFormatException`, not a `NullPointerException`, worth noting), or non-numeric text will all trigger this exception identically.

- `parseXxx(String)` (like `Integer.parseInt`, `Double.parseDouble`) returns a plain primitive value; `valueOf(String)` returns a wrapper object, internally calling the corresponding `parseXxx` method and boxing the result.
- Both throw the identical `NumberFormatException` for the same malformed input — the only real difference between them is the returned type, primitive versus wrapper object.
- Use `parseXxx` for values you'll use as primitives; use `valueOf` when you specifically need a wrapper object, such as for a generic collection or to represent a potentially-`null` result.
- A `null` wrapper result (representing "no value" or "could not be parsed") must be explicitly checked before use in any primitive context, to avoid a `NullPointerException` during auto-unboxing.
