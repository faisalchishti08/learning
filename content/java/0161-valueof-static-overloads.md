---
card: java
gi: 161
slug: valueof-static-overloads
title: valueOf() static overloads
---

## 1. What it is

`String.valueOf(...)` is a family of **static** methods, each overloaded for a different parameter type (`int`, `double`, `boolean`, `char`, `char[]`, `Object`, and more), that converts its argument into its string representation. Being static, it's called on the `String` class itself, not on a string instance — `String.valueOf(42)`, not `someString.valueOf(42)`.

```java
System.out.println(String.valueOf(42));       // "42"
System.out.println(String.valueOf(3.14));      // "3.14"
System.out.println(String.valueOf(true));      // "true"
System.out.println(String.valueOf('x'));       // "x"

Object obj = null;
System.out.println(String.valueOf(obj));       // "null" — does NOT throw, unlike calling obj.toString()
```

The last example highlights `valueOf`'s key safety feature: `String.valueOf(null_reference)` produces the literal text `"null"` instead of throwing a `NullPointerException` — calling `obj.toString()` directly on a `null` reference, by contrast, would throw immediately, since there's no object to invoke a method on.

## 2. Why & when

`valueOf` is the safe, uniform way to convert any value — including a possibly-`null` object — into its string form:

- **Converting primitives to strings explicitly**, as an alternative to `+ ""` concatenation tricks (`42 + ""` also works, but `String.valueOf(42)` is more explicit about intent).
- **Safely converting a possibly-`null` `Object`** — `String.valueOf(obj)` is the standard defensive pattern when `obj.toString()` might throw due to `obj` being `null`.
- **Building generic, type-agnostic code** — a method that needs to convert an arbitrary value (of unknown, possibly-null type) into text can rely on `valueOf`'s `Object` overload to handle any input uniformly.

Internally, `+`-based concatenation with a non-`String` operand already calls something equivalent to `valueOf` behind the scenes — this is precisely why `"Count: " + 42` and `"Count: " + null` both work without throwing, as covered in the earlier concatenation topic.

## 3. Core concept

```java
public class ValueOfDemo {
    public static void main(String[] args) {
        int count = 5;
        double price = 19.99;
        boolean active = true;
        Object maybeNull = null;

        String s1 = String.valueOf(count);
        String s2 = String.valueOf(price);
        String s3 = String.valueOf(active);
        String s4 = String.valueOf(maybeNull);

        System.out.println(s1 + " | " + s2 + " | " + s3 + " | " + s4);
        // "5 | 19.99 | true | null"
    }
}
```

Each call picks the overload matching its argument's compile-time type — `valueOf(int)`, `valueOf(double)`, `valueOf(boolean)`, and `valueOf(Object)` for the last one, which safely handles the `null` reference by returning the text `"null"` rather than throwing.

## 4. Diagram

<svg viewBox="0 0 700 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="ValueOf diagram: calling String dot valueOf on a null Object reference safely returns the text null, while calling dot toString directly on that same null reference throws a NullPointerException instead." >
  <rect x="8" y="8" width="684" height="134" rx="8" fill="#0d1117"/>
  <text x="350" y="22" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Converting a null Object to text — two very different outcomes</text>

  <rect x="60" y="45" width="260" height="30" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="190" y="65" fill="#6db33f" font-size="9" text-anchor="middle" font-family="monospace">String.valueOf(nullObj) -&gt; "null"</text>

  <rect x="380" y="45" width="260" height="30" rx="6" fill="#1c2430" stroke="#f85149" stroke-width="2"/>
  <text x="510" y="65" fill="#f85149" font-size="9" text-anchor="middle" font-family="monospace">nullObj.toString() -&gt; throws!</text>

  <text x="350" y="105" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="sans-serif">valueOf() checks for null internally before delegating to toString() —</text>
  <text x="350" y="120" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="sans-serif">calling toString() directly on a null reference has no such protection.</text>
</svg>

`String.valueOf` guards against `null` before ever calling `toString`; calling `toString` directly offers no such protection.

## 5. Runnable example

Scenario: building a simple audit log line from a mix of typed fields, some of which might legitimately be `null` — starting with basic conversion of known primitive values, then adding an `Object` field that might be `null`, then hardening the log builder into a reusable, fully null-safe utility.

### Level 1 — Basic

```java
public class LogLineBasic {
    public static void main(String[] args) {
        int userId = 42;
        boolean success = true;

        String logLine = "userId=" + String.valueOf(userId) + ", success=" + String.valueOf(success);
        System.out.println(logLine);
    }
}
```

**How to run:** `java LogLineBasic.java`

`String.valueOf(userId)` and `String.valueOf(success)` explicitly convert the `int` and `boolean` values to their string forms before concatenation — functionally this is what `+` would have done automatically anyway, but writing it explicitly makes the conversion step visible and deliberate.

### Level 2 — Intermediate

Same log line, now including an **optional `Object` field** (a session attachment, which might be `null` if none was provided) using the `Object` overload of `valueOf`.

```java
public class LogLineIntermediate {
    public static void main(String[] args) {
        int userId = 42;
        boolean success = true;
        Object attachment = null; // no attachment for this event

        String logLine = "userId=" + String.valueOf(userId)
                        + ", success=" + String.valueOf(success)
                        + ", attachment=" + String.valueOf(attachment);
        System.out.println(logLine);
        // "userId=42, success=true, attachment=null"
    }
}
```

**How to run:** `java LogLineIntermediate.java`

`String.valueOf(attachment)` safely handles the `null` case, producing the text `"null"` in the log line rather than throwing — if the code had instead called `attachment.toString()` directly, this would have thrown a `NullPointerException` and crashed the log-building process entirely, since `attachment` genuinely is `null` here.

### Level 3 — Advanced

Same log builder, now generalized into a reusable method that accepts a variable number of labeled fields (some possibly `null`, of mixed types) and safely converts every one of them using `valueOf`.

```java
public class LogLineAdvanced {

    static String buildLogLine(Object... fields) {
        if (fields.length % 2 != 0) {
            throw new IllegalArgumentException("Fields must be label/value pairs");
        }

        StringBuilder line = new StringBuilder();
        for (int i = 0; i < fields.length; i += 2) {
            if (i > 0) line.append(", ");
            String label = String.valueOf(fields[i]);
            String value = String.valueOf(fields[i + 1]);
            line.append(label).append("=").append(value);
        }
        return line.toString();
    }

    public static void main(String[] args) {
        System.out.println(buildLogLine("userId", 42, "success", true, "attachment", null));
        System.out.println(buildLogLine("event", "logout", "durationMs", 1500L));
    }
}
```

**How to run:** `java LogLineAdvanced.java`

`buildLogLine` accepts `Object... fields` — a varargs array that can hold any mix of types, including `null` — and treats them as alternating label/value pairs. Every single field, regardless of its actual runtime type (`String`, `Integer`, `Boolean`, or `null`), is converted uniformly with `String.valueOf(fields[i])`, which is exactly why `valueOf`'s `Object` overload is so useful here: the method has no idea ahead of time what types it will receive, and `valueOf` handles all of them — including `null` — without any type-specific branching.

## 6. Walkthrough

Trace `buildLogLine("userId", 42, "success", true, "attachment", null)`:

**Validation.** `fields.length` is `6`, which is even, so the guard clause doesn't throw.

**i = 0.** `label = String.valueOf(fields[0])` = `String.valueOf("userId")` = `"userId"` (a `String` argument's `valueOf` overload effectively returns the string itself, or `"null"` if it were `null`). `value = String.valueOf(fields[1])` = `String.valueOf(42)`, but note: since `fields` is `Object[]`, `42` was autoboxed to `Integer` when passed in, so this actually resolves to the `Object` overload, which calls `.toString()` on the boxed `Integer`, producing `"42"`. `line` becomes `"userId=42"`.

**i = 2.** `label = "success"`, `value = String.valueOf(fields[3])` = `String.valueOf(Boolean.TRUE)` = `"true"` (again via the `Object` overload, calling `Boolean`'s `toString()`). `line` becomes `"userId=42, success=true"`.

**i = 4.** `label = "attachment"`, `value = String.valueOf(fields[5])` = `String.valueOf(null)` — this resolves to the `Object` overload with a genuinely `null` argument, which `valueOf` detects internally and returns `"null"` without throwing. `line` becomes `"userId=42, success=true, attachment=null"`.

```
i=0: label="userId"     value=String.valueOf(42)   -> "42"
i=2: label="success"    value=String.valueOf(true) -> "true"
i=4: label="attachment" value=String.valueOf(null) -> "null" (no exception)
final: "userId=42, success=true, attachment=null"
```

**Final output.** The first call prints `"userId=42, success=true, attachment=null"`; the second call, `buildLogLine("event", "logout", "durationMs", 1500L)`, similarly prints `"event=logout, durationMs=1500"` — the `long` value `1500L` is likewise autoboxed to `Long` and converted via `valueOf`'s `Object` overload.

## 7. Gotchas & takeaways

> **`String.valueOf(null)` called directly with a *literal* `null` (not a variable) is ambiguous and may not compile, or may resolve to the `char[]` overload** — the compiler must pick one specific overload for a bare `null` literal, and `valueOf(char[])` is a candidate alongside `valueOf(Object)`, which can produce a `NullPointerException` at runtime (since the `char[]` overload doesn't have the same null-check as the `Object` one) or a compile ambiguity depending on context. In practice, `String.valueOf(someNullableVariable)` (a variable of a known reference type, not a bare literal) avoids this pitfall entirely.

> **`valueOf(Object)` is what makes `null`-safety possible — it checks for `null` internally and returns `"null"` before ever attempting to call `.toString()`.** Calling `.toString()` directly on any reference that might be `null` bypasses this safety net entirely and throws immediately.

- `String.valueOf(...)` is a family of static overloads that convert values of many types into their string form, called on the `String` class itself.
- `String.valueOf(possiblyNullObject)` is the standard, safe way to convert a value to text without risking a `NullPointerException`, unlike calling `.toString()` directly.
- `+`-based concatenation already performs an equivalent conversion automatically for non-`String` operands — `valueOf` makes that same conversion explicit and callable on its own.
- Be cautious with a bare `null` literal passed directly to `valueOf` — prefer passing a typed variable to avoid overload-resolution ambiguity.
