---
card: java
gi: 744
slug: null-handling-in-switch-case-null
title: Null handling in switch (case null)
---

## 1. What it is

Classic Java `switch` **always threw `NullPointerException`** if the selector expression was `null` — there was no way to handle `null` as a case. Java 21's pattern-matching switch adds an explicit `case null` label, so a switch can now match `null` deliberately, right alongside its other cases: `case null -> "no value"`. This closes a long-standing gap: pattern-matching switches often operate over reference types (`String`, records, sealed interfaces) where `null` is a real, expected value that deserves its own branch instead of an automatic crash.

## 2. Why & when

Once switch expressions started matching on types and patterns instead of just constants, the old blanket "null always throws" rule became an awkward special case: if you wanted to handle a possibly-null `Shape` or `String`, you had to write a separate `if (x == null) { ... } else { switch (x) { ... } }` guard *before* the switch, splitting null-handling logic away from the rest of the dispatch even though conceptually it's just another case. `case null` folds that guard back into the switch itself, so all the cases — including the null case — live together and can be reasoned about as one complete, ordered set of possibilities. It also composes with `case null, default ->`, a shorthand meaning "treat null the same way as everything else not otherwise matched," for the common case where null should just fall into the default handling rather than get special treatment.

## 3. Core concept

```java
static String describe(String input) {
    return switch (input) {
        case null -> "no input provided";
        case "" -> "empty input";
        case String s -> "input: " + s;
    };
}
```

Without `case null`, calling `describe(null)` would throw `NullPointerException` before any case is even considered; with it, `null` becomes just another explicitly handled possibility.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Without case null, a null selector throws NullPointerException before any case runs; with case null, null becomes an explicit, orderable case">
  <rect x="20" y="20" width="280" height="70" rx="8" fill="#1c2430" stroke="#8b949e"/>
  <text x="160" y="45" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Classic switch</text>
  <text x="160" y="65" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">switch(null) -&gt; NullPointerException</text>
  <text x="160" y="80" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">(thrown before any case is tried)</text>

  <rect x="340" y="20" width="280" height="70" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="480" y="45" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">Pattern-matching switch</text>
  <text x="480" y="65" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">case null -&gt; "no input provided"</text>
  <text x="480" y="80" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">(handled like any other case)</text>

  <text x="320" y="150" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">case null must appear explicitly — it is never silently included in default</text>
</svg>

*`case null` turns an automatic crash into an explicit, ordered branch of the switch.*

## 5. Runnable example

Scenario: parsing an optional configuration value that may legitimately be absent (`null`), blank, or present — growing from a null-check guard to a fully integrated switch.

### Level 1 — Basic

```java
public class ConfigNullGuard {
    static String resolve(String rawValue) {
        if (rawValue == null) {
            return "using default";
        }
        switch (rawValue) {
            case "" -> { return "blank value, using default"; }
            default -> { return "using configured value: " + rawValue; }
        }
    }

    public static void main(String[] args) {
        System.out.println(resolve(null));
        System.out.println(resolve(""));
        System.out.println(resolve("production"));
    }
}
```

**How to run:** `java ConfigNullGuard.java` (JDK 21+).

This is the pre-`case null` style: a separate `if (rawValue == null)` guard has to run *before* the switch, because passing `null` straight into `switch (rawValue)` would throw `NullPointerException`.

### Level 2 — Intermediate

```java
public class ConfigCaseNull {
    static String resolve(String rawValue) {
        return switch (rawValue) {
            case null -> "using default";
            case "" -> "blank value, using default";
            case String s -> "using configured value: " + s;
        };
    }

    public static void main(String[] args) {
        System.out.println(resolve(null));
        System.out.println(resolve(""));
        System.out.println(resolve("production"));
    }
}
```

**How to run:** `java ConfigCaseNull.java`.

The real-world concern added: the null check moves **inside** the switch as `case null`, so all three possibilities — absent, blank, present — are handled uniformly as ordered cases of one expression, with no separate guard clause needed before it.

### Level 3 — Advanced

```java
public class ConfigAdvanced {
    sealed interface ConfigSource permits FileSource, EnvSource {}
    record FileSource(String path) implements ConfigSource {}
    record EnvSource(String varName) implements ConfigSource {}

    static String resolve(String rawValue, ConfigSource fallback) {
        String result = switch (rawValue) {
            case null, default -> null; // treat blank and null the same for now
        };
        if (result != null) return result;

        return switch (fallback) {
            case FileSource(var path) when path.isBlank() -> "no file path configured";
            case FileSource(var path) -> "reading from file: " + path;
            case EnvSource(var name) -> "reading from env var: " + name.toUpperCase();
        };
    }

    public static void main(String[] args) {
        System.out.println(resolve(null, new FileSource("/etc/app/config.yml")));
        System.out.println(resolve(null, new FileSource("")));
        System.out.println(resolve(null, new EnvSource("app_env")));
        System.out.println(resolve("production", new EnvSource("app_env")));
    }
}
```

**How to run:** `java ConfigAdvanced.java`.

This adds the production-flavored hard case: `case null, default` combines null-handling with the default fallback in one label (meaning "if it's null, or anything else not separately cased, do this"), and a **second switch** over a sealed `ConfigSource` hierarchy runs only when the primary value is absent — chaining two pattern-matching switches to resolve configuration from several possible sources in priority order.

## 6. Walkthrough

Tracing `ConfigAdvanced.main`'s second call, `resolve(null, new FileSource(""))`:

1. `resolve` first evaluates `switch (rawValue)` where `rawValue` is `null`. The single case label `case null, default -> null` matches **any** value of `rawValue`, including `null` — it always returns `null` here (this switch stands in for a real "was an override explicitly provided" check).
2. `result` is `null`, so the `if (result != null) return result;` guard is skipped, and control falls through to the second switch, `switch (fallback)`.
3. `fallback` is `new FileSource("")`. The first case, `FileSource(var path) when path.isBlank()`, matches: the pattern destructures `path = ""`, and the guard `path.isBlank()` evaluates `true` (empty string is blank). This case wins, producing `"no file path configured"`.
4. That string is returned from the second switch, which is also `resolve`'s return value.

For the third call, `resolve(null, new EnvSource("app_env"))`: the first switch again returns `null` for `result`. The second switch tests `fallback` against `FileSource` patterns first — no match, since `fallback` is an `EnvSource` — then matches `EnvSource(var name)`, destructuring `name = "app_env"`, and returns `"reading from env var: " + "app_env".toUpperCase()`.

Expected output:
```
reading from file: /etc/app/config.yml
no file path configured
reading from env var: APP_ENV
reading from env var: APP_ENV
```

(The fourth call passes `rawValue = "production"`, but because the first switch's single case is `case null, default`, it matches regardless of `rawValue`'s actual content in this simplified example, so the output is identical to the third call — a reminder that `default` truly means "everything not otherwise cased," including non-null values, unless narrower cases are added above it.)

## 7. Gotchas & takeaways

> **Gotcha:** `case null` is never implicitly included in a plain `default` case — a switch with only `case String s -> ...` and `default -> ...` (no explicit `case null`) still throws `NullPointerException` for a `null` selector. You must write `case null` explicitly, or `case null, default` if null should share the default's handling.

- `case null` must appear as its own label (or combined via `case null, default`); it is the only way to avoid `NullPointerException` on a null selector in a pattern-matching switch.
- Put `case null` wherever it makes sense in the ordering — typically first, so null-handling is the first thing a reader sees.
- `case null, default` is shorthand for "null falls through to the same handling as everything else" — use it when null genuinely isn't special.
- This only applies to switches over reference types; a switch over a primitive `int`/`char`/etc. can never see `null` and doesn't need this.
- Combine with [exhaustiveness checking](0745-exhaustiveness-checking-in-switch.md): once a switch's selector type includes the possibility of null, the compiler requires you to address it — either with `case null` or by ensuring a `default`/unconditional pattern case is present.
