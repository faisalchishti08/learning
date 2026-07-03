---
card: spring-framework
gi: 171
slug: ternary-elvis-and-safe-navigation-operators
title: "Ternary, Elvis, and safe-navigation operators"
---

## 1. What it is

SpEL provides three concise operators for handling conditional logic and null safety:

- **Ternary** `condition ? trueValue : falseValue` — standard three-way conditional.
- **Elvis** `expression ?: default` — returns `expression` if not null/false/empty, otherwise `default`. Named for the `?:` resemblance to Elvis's hair.
- **Safe navigation** `obj?.property` — returns `null` instead of throwing `NullPointerException` when `obj` is `null`.

```java
parser.parseExpression("name != null ? name : 'Anonymous'").getValue(ctx); // ternary
parser.parseExpression("name ?: 'Anonymous'").getValue(ctx);               // Elvis (shorter)
parser.parseExpression("order?.customer?.address?.city").getValue(ctx);    // safe nav
```

## 2. Why & when

- **`@Value` defaults** — `@Value("#{config.timeout ?: 5000}")` provides a fallback when the property is null.
- **Deep graph traversal** — `order?.customer?.address?.city` safely navigates a chain that may have null segments, returning `null` rather than throwing.
- **Conditional configuration** — `@Value("#{env.isDev() ? 'debug' : 'info'}")` selects between two values based on runtime state.
- **Nullable bean properties** — `@Value("#{@optionalBean?.getResult() ?: 'default'}")` handles an optional bean that may not be present.
- **Collection default** — `config.roles ?: {'user', 'guest'}` falls back to an inline list when roles is null or empty.

## 3. Core concept

| Operator | Form | Null/falsy handling |
|---|---|---|
| Ternary | `a ? b : c` | explicit condition required |
| Elvis | `a ?: b` | returns `a` if truthy, else `b` |
| Safe nav | `a?.b` | returns `null` if `a` is null |
| Safe nav + method | `a?.method()` | returns `null` if `a` is null |
| Safe nav + index | `a?.[n]` | returns `null` if `a` is null |
| Chained safe nav | `a?.b?.c?.d` | first null short-circuits the chain |

**Elvis truthy rules** — Elvis returns the fallback when the expression evaluates to `null`, `false`, `0`, `""`, or an empty collection. Specifically:
- `null ?: 'x'` → `'x'`
- `false ?: 'x'` → `'x'`
- `'' ?: 'x'` → `'x'` (empty string)
- `0 ?: 'x'` → `'x'`
- `'value' ?: 'x'` → `'value'`
- `true ?: 'x'` → `true`

## 4. Diagram

<svg viewBox="0 0 700 180" xmlns="http://www.w3.org/2000/svg">
  <!-- Ternary -->
  <rect x="10" y="15" width="210" height="155" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="115" y="35"  fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">Ternary  a ? b : c</text>
  <line x1="18" y1="43" x2="212" y2="43" stroke="#6db33f" stroke-width="1" opacity="0.4"/>
  <text x="115" y="57"  fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">evaluate a (Boolean)</text>
  <text x="115" y="71"  fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">true  → return b</text>
  <text x="115" y="85"  fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">false → return c</text>
  <text x="115" y="102" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">age &gt;= 18 ? 'adult' : 'minor'</text>
  <text x="115" y="116" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">b and c can be any SpEL</text>
  <text x="115" y="135" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">only one branch evaluated</text>
  <text x="115" y="149" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">(short-circuit)</text>

  <!-- Elvis -->
  <rect x="240" y="15" width="210" height="155" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="345" y="35"  fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">Elvis  a ?: b</text>
  <line x1="248" y1="43" x2="442" y2="43" stroke="#79c0ff" stroke-width="1" opacity="0.4"/>
  <text x="345" y="57"  fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">evaluate a</text>
  <text x="345" y="71"  fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">truthy → return a</text>
  <text x="345" y="85"  fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">falsy  → return b</text>
  <text x="345" y="102" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">name ?: 'Anonymous'</text>
  <text x="345" y="116" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">0 ?: 99  → 99</text>
  <text x="345" y="130" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">'' ?: 'x' → 'x'</text>
  <text x="345" y="149" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">shorthand: null/false/0/"" → fallback</text>

  <!-- Safe nav -->
  <rect x="470" y="15" width="220" height="155" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="580" y="35"  fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">Safe nav  a?.b</text>
  <line x1="478" y1="43" x2="682" y2="43" stroke="#6db33f" stroke-width="1" opacity="0.4"/>
  <text x="580" y="57"  fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">evaluate a</text>
  <text x="580" y="71"  fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">null  → return null (no NPE)</text>
  <text x="580" y="85"  fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">!null → navigate to .b</text>
  <text x="580" y="102" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">a?.b?.c?.d</text>
  <text x="580" y="116" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">a?.method()</text>
  <text x="580" y="130" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">a?.[idx]</text>
  <text x="580" y="149" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">first null short-circuits chain</text>
</svg>

Ternary requires explicit boolean; Elvis handles null/falsy implicitly; safe nav short-circuits on null.

## 5. Runnable example

### Level 1 — Basic

All three operators in isolation.

```java
// SpelNullHandlingBasic.java
import org.springframework.expression.*;
import org.springframework.expression.spel.standard.*;
import org.springframework.expression.spel.support.*;

public class SpelNullHandlingBasic {
    public static void main(String[] args) {
        var parser = new SpelExpressionParser();
        var ctx = new StandardEvaluationContext();

        // Ternary
        ctx.setVariable("age", 20);
        System.out.println(parser.parseExpression("#age >= 18 ? 'adult' : 'minor'").getValue(ctx)); // adult
        ctx.setVariable("age", 15);
        System.out.println(parser.parseExpression("#age >= 18 ? 'adult' : 'minor'").getValue(ctx)); // minor

        ctx.setVariable("score", 85);
        System.out.println(parser.parseExpression(
            "#score >= 90 ? 'A' : (#score >= 80 ? 'B' : 'C')").getValue(ctx)); // B (nested ternary)

        // Elvis
        ctx.setVariable("name", null);
        System.out.println(parser.parseExpression("#name ?: 'Anonymous'").getValue(ctx));    // Anonymous
        ctx.setVariable("name", "Alice");
        System.out.println(parser.parseExpression("#name ?: 'Anonymous'").getValue(ctx));    // Alice
        ctx.setVariable("count", 0);
        System.out.println(parser.parseExpression("#count ?: 'none'").getValue(ctx));        // none (0 is falsy)
        ctx.setVariable("flag", false);
        System.out.println(parser.parseExpression("#flag ?: 'default'").getValue(ctx));      // default (false is falsy)

        // Safe navigation
        ctx.setVariable("obj", null);
        System.out.println(parser.parseExpression("#obj?.toString()").getValue(ctx));         // null (no NPE)
        ctx.setVariable("obj", "hello");
        System.out.println(parser.parseExpression("#obj?.toUpperCase()").getValue(ctx));      // HELLO

        // Combining Elvis + safe nav
        ctx.setVariable("obj", null);
        System.out.println(parser.parseExpression("#obj?.toUpperCase() ?: 'NONE'").getValue(ctx)); // NONE
    }
}
```

How to run: `java SpelNullHandlingBasic.java`

`0 ?: 'none'` returns `'none'` — zero is falsy in SpEL Elvis. `#obj?.toString()` returns `null` when `#obj` is null. Combining safe nav and Elvis: `#obj?.prop ?: 'default'` safely navigates then provides a fallback.

### Level 2 — Intermediate

Deep object graph with safe navigation; Elvis for config fallback; ternary in collection projection.

```java
// SpelNullHandlingIntermediate.java
import org.springframework.expression.*;
import org.springframework.expression.spel.standard.*;
import org.springframework.expression.spel.support.*;
import java.util.*;

class GeoAddress { public String city; public String country;
    GeoAddress(String c, String co) { this.city = c; this.country = co; }
    public String getCity()    { return city; }
    public String getCountry() { return country; }
}
class Profile { public String displayName; public GeoAddress location;
    Profile(String d, GeoAddress l) { this.displayName = d; this.location = l; }
    public String getDisplayName()  { return displayName; }
    public GeoAddress getLocation() { return location; }
}
class Account { public String email; public Profile profile; public Integer credits;
    Account(String e, Profile p, Integer c) { this.email = e; this.profile = p; this.credits = c; }
    public String getEmail()     { return email; }
    public Profile getProfile()  { return profile; }
    public Integer getCredits()  { return credits; }
}

public class SpelNullHandlingIntermediate {
    public static void main(String[] args) {
        var parser = new SpelExpressionParser();
        var ctx = new StandardEvaluationContext();

        // Full account
        Account full = new Account("alice@ex.com",
            new Profile("Alice Smith", new GeoAddress("Boston", "US")), 500);
        ctx.setRootObject(full);

        System.out.println(parser.parseExpression("profile?.location?.city").getValue(ctx));  // Boston
        System.out.println(parser.parseExpression("profile?.displayName ?: 'Guest'").getValue(ctx)); // Alice Smith
        System.out.println(parser.parseExpression("credits ?: 0").getValue(ctx, Integer.class)); // 500

        // Account with null profile
        Account noProfile = new Account("bob@ex.com", null, null);
        ctx.setRootObject(noProfile);

        System.out.println(parser.parseExpression("profile?.location?.city").getValue(ctx));  // null
        System.out.println(parser.parseExpression("profile?.displayName ?: 'Guest'").getValue(ctx)); // Guest
        System.out.println(parser.parseExpression("credits ?: 0").getValue(ctx, Integer.class)); // 0

        // Account with profile but no location
        Account noLoc = new Account("carol@ex.com", new Profile("Carol", null), 200);
        ctx.setRootObject(noLoc);
        System.out.println(parser.parseExpression("profile?.location?.city ?: 'Unknown'").getValue(ctx)); // Unknown

        // Collection: ternary in projection
        List<Account> accounts = List.of(full, noProfile, noLoc);
        ctx.setRootObject(accounts);
        System.out.println(parser.parseExpression(
            "![email + ' (' + (profile?.displayName ?: 'N/A') + ')']").getValue(ctx, List.class));
        // [alice@ex.com (Alice Smith), bob@ex.com (N/A), carol@ex.com (Carol)]
    }
}
```

How to run: `java SpelNullHandlingIntermediate.java`

`profile?.location?.city` — if `profile` is null, `?.` returns null before attempting `location`. The chain short-circuits: `null?.city` → `null`. `credits ?: 0` provides a numeric default when `credits` is null.

### Level 3 — Advanced

`@Value` with Elvis fallbacks; optional bean reference with safe nav; null-coalescing chains.

```java
// SpelNullHandlingAdvanced.java
import org.springframework.beans.factory.annotation.*;
import org.springframework.context.annotation.*;
import org.springframework.expression.*;
import org.springframework.expression.spel.standard.*;
import org.springframework.expression.spel.support.*;

@Configuration
class NullCfg {
    @Bean("optConfig")
    public OptionalConfig optConfig() {
        return new OptionalConfig(null, 0, "");   // all blank/null/zero
    }
}

class OptionalConfig {
    private String apiKey;
    private int timeout;
    private String region;

    OptionalConfig(String apiKey, int timeout, String region) {
        this.apiKey = apiKey; this.timeout = timeout; this.region = region;
    }
    public String getApiKey()  { return apiKey; }
    public int getTimeout()    { return timeout; }
    public String getRegion()  { return region; }
}

@org.springframework.stereotype.Component
class ResolvedConfig {
    // Elvis: fallback when bean property is null/zero/blank
    @Value("#{@optConfig.apiKey ?: 'default-key'}")
    private String apiKey;

    @Value("#{@optConfig.timeout ?: 30000}")
    private int timeout;

    @Value("#{@optConfig.region ?: 'us-east-1'}")
    private String region;

    // Safe nav on environment (may be absent via profile)
    @Value("#{systemEnvironment['CUSTOM_HOST']?.trim() ?: 'localhost'}")
    private String host;

    // Chained fallback: try bean, then env, then literal
    @Value("#{@optConfig.apiKey ?: systemEnvironment['API_KEY'] ?: 'fallback-key'}")
    private String resolvedKey;

    public void print() {
        System.out.println("apiKey:      " + apiKey);
        System.out.println("timeout:     " + timeout);
        System.out.println("region:      " + region);
        System.out.println("host:        " + host);
        System.out.println("resolvedKey: " + resolvedKey);
    }
}

public class SpelNullHandlingAdvanced {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(NullCfg.class, ResolvedConfig.class);
        ctx.getBean(ResolvedConfig.class).print();

        // Runtime chained Elvis
        var parser = new SpelExpressionParser();
        var evalCtx = new StandardEvaluationContext();
        evalCtx.setVariable("a", null);
        evalCtx.setVariable("b", null);
        evalCtx.setVariable("c", "found");
        System.out.println(parser.parseExpression("#a ?: #b ?: #c ?: 'last'").getValue(evalCtx)); // found

        ctx.close();
    }
}
```

How to run: `java SpelNullHandlingAdvanced.java`

`@optConfig.apiKey ?: 'default-key'` falls back to `'default-key'` because `apiKey` is null. `systemEnvironment['CUSTOM_HOST']?.trim() ?: 'localhost'` — safe nav on `?.trim()` guards against the env var being null before calling `trim()`. `#a ?: #b ?: #c ?: 'last'` chains Elvis — each `?:` evaluates only when the preceding value is falsy.

## 6. Walkthrough

Execution for `"profile?.location?.city ?: 'Unknown'"` when `profile != null` but `profile.location == null`:

1. `profile` evaluates to `Profile{displayName="Carol", location=null}` — not null → continue.
2. `?.location` — safe nav: `profile` is not null → navigate to `.location` → `null`.
3. `?.city` — safe nav: current value is `null` → return `null` without navigating.
4. The full `profile?.location?.city` = `null`.
5. Elvis `?: 'Unknown'`: `null` is falsy → return `'Unknown'`.
6. Result: `"Unknown"`.

## 7. Gotchas & takeaways

> **Elvis treats `0` and `""` as falsy.** `count ?: 99` returns `99` when `count = 0`, not `0`. If zero is a valid meaningful value, use explicit null check: `count != null ? count : 99` instead of Elvis.

> Safe navigation `?.` returns `null` if ANY step is null. `a?.b?.c` where `b` exists but `b.c` is null returns `null` normally — both "b is null" and "b.c is null" produce the same `null` result. You cannot distinguish which step was null without breaking the chain.

- Nested ternary `a ? b : (c ? d : e)` works in SpEL; parentheses are required to control evaluation order. SpEL evaluates right-associatively by default, so `a ? b : c ? d : e` → `a ? b : (c ? d : e)`.
- `?.` works with method calls (`obj?.method()`), property access (`obj?.property`), and indexing (`obj?.[key]`). It does NOT prevent `NullPointerException` inside the method itself — if `method()` throws NPE internally, that exception propagates.
- In `@Value`, `#{null}` injects a literal null. Combined with Elvis: `@Value("#{beanProp ?: #{null}}")` is redundant — if `beanProp` is already null, Elvis returns null; just use `@Value("#{beanProp}")`.
