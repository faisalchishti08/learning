---
card: java
gi: 380
slug: annotation-elements-default-values
title: Annotation elements & default values
---

## 1. What it is

An annotation can declare **elements** — method-like declarations inside the `@interface` body that act as named parameters you fill in when applying the annotation, like `@Reminder(priority = "HIGH", assignee = "sam")`. Each element can optionally specify a **default value** with `default ...`, making it optional to supply when the annotation is used. An element named `value` gets special treatment: if it's the *only* element being set, you can omit the name entirely (`@Reminder("fix this")` instead of `@Reminder(value = "fix this")`).

## 2. Why & when

A bare marker annotation (`@Reminder` with no elements, as in [[declaring-custom-annotations]]) can only say "this thing is marked" — it can't carry any further detail. Elements let an annotation carry structured data alongside that marking: which priority a `@Reminder` is, what role a `@RequiresRole` demands, what column name a `@Column` maps to. This is what makes annotations genuinely expressive rather than just binary flags.

Default values matter because most real annotations have some elements that are almost always the same, and a few that vary — giving the common ones sensible defaults means callers only need to specify what's actually different for their use case, keeping the common case terse (`@Column` with no arguments, meaning "use the field's own name") while still allowing full customization (`@Column(name = "user_email")`) when needed.

## 3. Core concept

```java
import java.lang.annotation.*;
import java.lang.reflect.Method;

public class AnnotationElementsDemo {
    @Retention(RetentionPolicy.RUNTIME)
    @interface Reminder {
        String value();                 // required element, "value" gets special shorthand syntax
        String priority() default "LOW"; // optional -- defaults to "LOW" if not specified
    }

    static class Report {
        @Reminder("Add currency formatting")               // shorthand: sets 'value' only
        void generateSummary() { }

        @Reminder(value = "Fix crash on empty input", priority = "HIGH") // both elements set explicitly
        void generateChart() { }
    }

    public static void main(String[] args) throws Exception {
        for (Method m : Report.class.getDeclaredMethods()) {
            Reminder reminder = m.getAnnotation(Reminder.class);
            if (reminder != null) {
                System.out.println(m.getName() + ": [" + reminder.priority() + "] " + reminder.value());
            }
        }
    }
}
```

**How to run:** `java AnnotationElementsDemo.java`

`value()` has no `default`, so it's required on every use; because it's named `value`, `@Reminder("Add currency formatting")` can omit the element name entirely. `priority()` has `default "LOW"`, so `generateSummary`'s `@Reminder` — which never mentions `priority` — reads back as `"LOW"` via reflection, while `generateChart`'s explicit `priority = "HIGH"` overrides that default.

## 4. Diagram

<svg viewBox="0 0 640 160" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="an annotation element without a default is required at every use site; one with a default may be omitted, falling back to the declared default value">
  <rect x="8" y="8" width="624" height="144" rx="8" fill="#0d1117"/>
  <text x="20" y="30" fill="#e6edf3" font-size="11">@interface Reminder { String value(); String priority() default "LOW"; }</text>

  <rect x="30" y="50" width="270" height="45" rx="6" fill="#1c2430" stroke="#f85149"/>
  <text x="165" y="72" fill="#f85149" font-size="10" text-anchor="middle">@Reminder("Add formatting")</text>
  <text x="165" y="87" fill="#8b949e" font-size="9" text-anchor="middle">priority defaults to "LOW"</text>

  <rect x="330" y="50" width="270" height="45" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="465" y="72" fill="#6db33f" font-size="10" text-anchor="middle">@Reminder(value="Fix crash", priority="HIGH")</text>
  <text x="465" y="87" fill="#8b949e" font-size="9" text-anchor="middle">explicit override</text>

  <text x="20" y="130" fill="#8b949e" font-size="10">"value" is the one element name allowed to be omitted from the call when it's the only one set.</text>
</svg>

## 5. Runnable example

Scenario: a custom `@RateLimit` annotation for API methods, evolved from a bare marker with no configurability, through adding elements with sensible defaults, to a version whose defaulted elements drive real, varying behaviour when read by a simple reflective enforcer.

### Level 1 — Basic

```java
import java.lang.annotation.*;

public class RateLimitBareMarker {
    @Retention(RetentionPolicy.RUNTIME)
    @interface RateLimit { // no elements at all -- can only say "this is rate-limited", nothing more
    }

    static class Api {
        @RateLimit
        void search() { System.out.println("Searching..."); }
    }

    public static void main(String[] args) {
        System.out.println("Marked, but no configurable limit value exists yet.");
    }
}
```

**How to run:** `java RateLimitBareMarker.java`

`@RateLimit` can flag a method, but it can't express *how much* to limit it by — every rate-limited method would need to be treated identically, which is rarely what a real rate limiter needs.

### Level 2 — Intermediate

```java
import java.lang.annotation.*;

public class RateLimitWithElements {
    @Retention(RetentionPolicy.RUNTIME)
    @interface RateLimit {
        int requestsPerMinute() default 60; // sensible default for most endpoints
        String scope() default "PER_USER";  // most limits are per-user by default
    }

    static class Api {
        @RateLimit // uses both defaults: 60/min, PER_USER
        void search() { System.out.println("Searching..."); }

        @RateLimit(requestsPerMinute = 5) // overrides just the one element that differs
        void sendPasswordReset() { System.out.println("Sending reset email..."); }
    }

    public static void main(String[] args) {
        System.out.println("Elements declared with defaults; reading them comes next.");
    }
}
```

**How to run:** `java RateLimitWithElements.java`

`search()` uses `@RateLimit` with no arguments at all, relying entirely on both defaults. `sendPasswordReset()` overrides only `requestsPerMinute`, leaving `scope` at its default `"PER_USER"` — each call site only specifies what's actually different from the common case.

### Level 3 — Advanced

```java
import java.lang.annotation.*;
import java.lang.reflect.Method;
import java.util.HashMap;
import java.util.Map;

public class RateLimitEnforced {
    @Retention(RetentionPolicy.RUNTIME)
    @interface RateLimit {
        int requestsPerMinute() default 60;
        String scope() default "PER_USER";
    }

    static class Api {
        @RateLimit
        void search() { System.out.println("Searching..."); }

        @RateLimit(requestsPerMinute = 5)
        void sendPasswordReset() { System.out.println("Sending reset email..."); }

        @RateLimit(requestsPerMinute = 1000, scope = "GLOBAL")
        void healthCheck() { System.out.println("OK"); }
    }

    static final Map<String, Integer> callCounts = new HashMap<>();

    static void invokeWithLimit(Api api, Method m) throws Exception {
        RateLimit limit = m.getAnnotation(RateLimit.class);
        String key = m.getName();
        int count = callCounts.merge(key, 1, Integer::sum);

        if (count > limit.requestsPerMinute()) {
            System.out.println("BLOCKED " + key + " (limit " + limit.requestsPerMinute()
                    + "/min, scope=" + limit.scope() + ")");
            return;
        }
        m.invoke(api);
    }

    public static void main(String[] args) throws Exception {
        Api api = new Api();
        Method resetMethod = Api.class.getDeclaredMethod("sendPasswordReset");

        for (int i = 1; i <= 6; i++) {
            invokeWithLimit(api, resetMethod); // sendPasswordReset allows only 5 per minute
        }
    }
}
```

**How to run:** `java RateLimitEnforced.java`

`invokeWithLimit` reads `requestsPerMinute()` and `scope()` straight off the annotation via reflection and uses them to make a real runtime decision — this is exactly how a genuine rate-limiting framework works, except a real one would track time windows instead of this simplified running counter, and it demonstrates why elements with sensible defaults matter: `healthCheck`'s much higher limit and `GLOBAL` scope required only two words of configuration at its call site, not a rewrite of the enforcement logic.

## 6. Walkthrough

Execution starts in `main`. `resetMethod` is looked up via reflection as `sendPasswordReset`, whose `@RateLimit(requestsPerMinute = 5)` sets `requestsPerMinute` to `5` and leaves `scope` at its default, `"PER_USER"`.

The loop runs `invokeWithLimit(api, resetMethod)` six times, `i` from `1` to `6`. Each call: `limit = m.getAnnotation(RateLimit.class)` retrieves the same annotation instance every time. `key = "sendPasswordReset"`. `callCounts.merge(key, 1, Integer::sum)` increments the counter for this key and returns the new total — `1` on the first call, `2` on the second, and so on up to `6` on the sixth.

For `count` values `1` through `5`: `count > limit.requestsPerMinute()` is `1 > 5`, `2 > 5`, ..., `5 > 5` — all `false` (note `5 > 5` is false, so the fifth call still passes). Each of these five calls proceeds to `m.invoke(api)`, which calls `sendPasswordReset()`, printing `Sending reset email...` each time.

On the sixth call, `count` is `6`. `6 > 5` is `true`, so the method is blocked: `m.invoke(api)` is never reached, and instead it prints `BLOCKED sendPasswordReset (limit 5/min, scope=PER_USER)`.

Expected output:
```
Sending reset email...
Sending reset email...
Sending reset email...
Sending reset email...
Sending reset email...
BLOCKED sendPasswordReset (limit 5/min, scope=PER_USER)
```

## 7. Gotchas & takeaways

> Annotation element types are restricted to primitives, `String`, `Class`, enums, other annotations, and arrays of those — you cannot declare an element of an arbitrary object type (like a `List` or a custom non-annotation class). This restriction exists because element values must be resolvable as compile-time constants.

- An element is declared like an abstract method inside `@interface { }`: `Type name();` for required, `Type name() default value;` for optional with a fallback.
- An element specifically named `value` gets special shorthand syntax: `@Reminder("text")` is equivalent to `@Reminder(value = "text")`, but only works when it's the sole element being set.
- Reading element values back via reflection (`annotationInstance.elementName()`) always returns the actual value used, or the declared default if the element was omitted at the call site.
- Giving common elements a sensible `default` keeps the typical, common-case usage terse, while still allowing full per-call-site customization when a specific case needs to differ.
- This is exactly the mechanism real frameworks use — Spring's `@RequestMapping(value = "/users", method = RequestMethod.GET)` and JPA's `@Column(name = "user_email", nullable = false)` are ordinary annotations with elements and defaults, read via reflection by the framework at startup or request time.
