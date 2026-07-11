---
card: spring-security
gi: 69
slug: custom-security-expressions-methodsecurityexpressionhandler
title: "Custom security expressions (MethodSecurityExpressionHandler)"
---

## 1. What it is

`MethodSecurityExpressionHandler` (with `DefaultMethodSecurityExpressionRoot` as the concrete root object it constructs) is the extension point for adding genuinely new functions directly to the SpEL vocabulary itself — rather than delegating to a named bean via `@beanName.method(...)` (the previous card's approach), a custom expression root subclass adds a method that becomes callable *directly* by name inside any `@PreAuthorize` expression, exactly like the built-in `hasRole`/`hasAuthority` functions.

```java
public class CustomMethodSecurityExpressionRoot extends SecurityExpressionRoot
        implements MethodSecurityExpressionOperations {
    public boolean isBusinessHours() {
        LocalTime now = LocalTime.now();
        return !now.isBefore(LocalTime.of(9, 0)) && !now.isAfter(LocalTime.of(17, 0));
    }
    // (constructor and boilerplate delegating to SecurityExpressionRoot omitted for brevity)
}

@PreAuthorize("isBusinessHours() and hasRole('TELLER')") // "isBusinessHours()" reads EXACTLY like a built-in function
public void processWithdrawal(BigDecimal amount) { ... }
```

## 2. Why & when

Delegating to a named bean (`@accountSecurity.isOwner(...)`) works well for one-off, context-specific logic, but a genuinely reusable condition — one that should read naturally alongside `hasRole`/`hasAuthority` across many different `@PreAuthorize` expressions throughout an entire application, without needing to repeat a bean-reference prefix every time — is better served by extending the expression root itself, making the new function a first-class part of the vocabulary every method-security expression in the application can use identically to any built-in one.

Reach for a custom `MethodSecurityExpressionHandler`/expression root when:

- A condition is used repeatedly across many different `@PreAuthorize`/`@PostAuthorize` expressions throughout the application, and repeating `@someBean.check(...)` everywhere is more verbose or less readable than a dedicated function name would be.
- The condition genuinely feels like it belongs alongside `hasRole`/`hasAuthority` conceptually — a time-of-day check, an IP-range check specific to the application's own network topology, a custom multi-tenancy check — rather than being tied to one specific bean's identity.
- For a one-off, context-specific check used in only one or two places, the simpler `@beanName.method(...)` delegation from the previous card remains the more proportionate, lower-ceremony choice — reserve extending the expression root itself for genuinely reusable, vocabulary-level additions.

## 3. Core concept

```
 DEFAULT: DefaultMethodSecurityExpressionRoot provides hasRole, hasAuthority, hasPermission, authentication, ...

 CUSTOM MethodSecurityExpressionHandler:
   overrides createSecurityExpressionRoot(...) to return a CUSTOM root object instead of the default one
   that custom root EXTENDS the default (inheriting everything it already provides)
   AND adds NEW methods of its own (e.g. isBusinessHours())

 the CUSTOM function is then usable EXACTLY like a built-in one, in ANY @PreAuthorize expression:
   @PreAuthorize("isBusinessHours() and hasRole('TELLER')")
        ^^^^^^^^^^^^^^^^^ CUSTOM, added by the expression root subclass
                              ^^^^^^^^^^^^^^ BUILT-IN, inherited from the default root
```

The custom function and the built-in ones are indistinguishable in the expression string — both are just names resolved against the same root object.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A custom MethodSecurityExpressionHandler constructs a custom expression root that extends the default root inheriting hasRole and hasAuthority while adding a new isBusinessHours function both the built in and custom functions are then callable identically from any PreAuthorize expression string">
  <rect x="15" y="20" width="230" height="42" rx="7" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="130" y="38" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">DefaultMethodSecurityExpressionRoot</text>
  <text x="130" y="51" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">hasRole, hasAuthority, ...</text>

  <rect x="15" y="90" width="230" height="46" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.4"/>
  <text x="130" y="110" fill="#79c0ff" font-size="7.5" text-anchor="middle" font-family="sans-serif">CustomMethodSecurityExpressionRoot</text>
  <text x="130" y="123" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">extends the default, ADDS isBusinessHours()</text>

  <rect x="380" y="55" width="230" height="60" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="495" y="78" fill="#6db33f" font-size="7" text-anchor="middle" font-family="sans-serif">@PreAuthorize(</text>
  <text x="495" y="91" fill="#6db33f" font-size="7" text-anchor="middle" font-family="sans-serif">"isBusinessHours() and hasRole('X')")</text>
  <text x="495" y="104" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">both look IDENTICAL in the expression</text>

  <defs><marker id="a69" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
  <line x1="245" y1="41" x2="380" y2="70" stroke="#8b949e" stroke-width="1" marker-end="url(#a69)"/>
  <line x1="245" y1="113" x2="380" y2="90" stroke="#8b949e" stroke-width="1" marker-end="url(#a69)"/>
</svg>

Both built-in and custom functions ultimately resolve against the same expanded root object — indistinguishable at the call site.

## 5. Runnable example

The scenario: implement a custom expression root extending a base root's built-in functions, adding a business-hours check as a first-class function, then use it identically alongside a built-in-style call in one combined expression, then add a second custom function and confirm both coexist correctly.

### Level 1 — Basic

A base root providing `hasRole`, and a custom subclass adding `isBusinessHours()`.

```java
import java.time.LocalTime;
import java.util.*;

public class CustomExpressionsLevel1 {
    record Authentication(Set<String> authorities) {}

    static class DefaultExpressionRoot {
        Authentication authentication;
        DefaultExpressionRoot(Authentication authentication) { this.authentication = authentication; }
        boolean hasRole(String role) { return authentication.authorities().contains("ROLE_" + role); }
    }

    // extends the DEFAULT root, ADDING a new function of its own
    static class CustomExpressionRoot extends DefaultExpressionRoot {
        LocalTime open, close;
        CustomExpressionRoot(Authentication authentication, LocalTime open, LocalTime close) {
            super(authentication);
            this.open = open; this.close = close;
        }
        boolean isBusinessHours() {
            LocalTime now = LocalTime.now();
            return !now.isBefore(open) && !now.isAfter(close);
        }
    }

    public static void main(String[] args) {
        Authentication teller = new Authentication(Set.of("ROLE_TELLER"));
        // WIDE window so this example is reliably "within hours" whenever it's actually run
        CustomExpressionRoot root = new CustomExpressionRoot(teller, LocalTime.of(0, 0), LocalTime.of(23, 59));

        System.out.println("hasRole('TELLER') [inherited from base root]: " + root.hasRole("TELLER"));
        System.out.println("isBusinessHours() [NEW, custom function]: " + root.isBusinessHours());
    }
}
```

How to run: `java CustomExpressionsLevel1.java`

`CustomExpressionRoot extends DefaultExpressionRoot`, inheriting `hasRole` unchanged while adding `isBusinessHours` as a genuinely new method — both are callable on the same `root` instance, exactly mirroring how a real custom `MethodSecurityExpressionRoot` subclass extends the framework's default root.

### Level 2 — Intermediate

Combine both functions in one expression-equivalent check, mirroring `@PreAuthorize("isBusinessHours() and hasRole('TELLER')")`.

```java
import java.time.LocalTime;
import java.util.*;

public class CustomExpressionsLevel2 {
    record Authentication(Set<String> authorities) {}

    static class DefaultExpressionRoot {
        Authentication authentication;
        DefaultExpressionRoot(Authentication authentication) { this.authentication = authentication; }
        boolean hasRole(String role) { return authentication.authorities().contains("ROLE_" + role); }
    }

    static class CustomExpressionRoot extends DefaultExpressionRoot {
        LocalTime open, close;
        CustomExpressionRoot(Authentication authentication, LocalTime open, LocalTime close) {
            super(authentication);
            this.open = open; this.close = close;
        }
        boolean isBusinessHours() {
            LocalTime now = LocalTime.now();
            return !now.isBefore(open) && !now.isAfter(close);
        }
    }

    // models: @PreAuthorize("isBusinessHours() and hasRole('TELLER')")
    static boolean checkExpression(CustomExpressionRoot root) {
        return root.isBusinessHours() && root.hasRole("TELLER");
    }

    public static void main(String[] args) {
        Authentication teller = new Authentication(Set.of("ROLE_TELLER"));
        Authentication manager = new Authentication(Set.of("ROLE_MANAGER")); // NOT a teller

        CustomExpressionRoot withinHoursTellerRoot = new CustomExpressionRoot(teller, LocalTime.of(0, 0), LocalTime.of(23, 59));
        CustomExpressionRoot outsideHoursTellerRoot = new CustomExpressionRoot(teller, LocalTime.of(3, 0), LocalTime.of(3, 1)); // NARROW window, almost certainly "closed" right now
        CustomExpressionRoot withinHoursManagerRoot = new CustomExpressionRoot(manager, LocalTime.of(0, 0), LocalTime.of(23, 59));

        System.out.println("teller, within hours: " + checkExpression(withinHoursTellerRoot));
        System.out.println("teller, outside hours: " + checkExpression(outsideHoursTellerRoot));
        System.out.println("manager (not a teller), within hours: " + checkExpression(withinHoursManagerRoot));
    }
}
```

How to run: `java CustomExpressionsLevel2.java`

`checkExpression` combines the custom `isBusinessHours()` and the inherited `hasRole("TELLER")` with `&&`, exactly mirroring the SpEL expression `"isBusinessHours() and hasRole('TELLER')")` — a teller within the wide-open hours window is granted, the same teller with a narrow, almost-certainly-closed window is denied, and a manager (lacking the teller role entirely) is denied even during business hours.

### Level 3 — Advanced

Add a second custom function (a transaction-limit check depending on a method parameter, mirroring how a real custom root can access whatever context it's given) and combine all three conditions.

```java
import java.time.LocalTime;
import java.math.BigDecimal;
import java.util.*;

public class CustomExpressionsLevel3 {
    record Authentication(Set<String> authorities) {}

    static class DefaultExpressionRoot {
        Authentication authentication;
        DefaultExpressionRoot(Authentication authentication) { this.authentication = authentication; }
        boolean hasRole(String role) { return authentication.authorities().contains("ROLE_" + role); }
    }

    static class CustomExpressionRoot extends DefaultExpressionRoot {
        LocalTime open, close;
        CustomExpressionRoot(Authentication authentication, LocalTime open, LocalTime close) {
            super(authentication);
            this.open = open; this.close = close;
        }
        boolean isBusinessHours() {
            LocalTime now = LocalTime.now();
            return !now.isBefore(open) && !now.isAfter(close);
        }
        // a SECOND custom function, checking a value against a role-dependent limit
        boolean isWithinTransactionLimit(BigDecimal amount) {
            BigDecimal limit = hasRole("SENIOR_TELLER") ? new BigDecimal("50000") : new BigDecimal("5000");
            return amount.compareTo(limit) <= 0;
        }
    }

    // models: @PreAuthorize("isBusinessHours() and hasRole('TELLER') and isWithinTransactionLimit(#amount)")
    static boolean checkExpression(CustomExpressionRoot root, BigDecimal amount) {
        return root.isBusinessHours() && root.hasRole("TELLER") && root.isWithinTransactionLimit(amount);
    }

    public static void main(String[] args) {
        Authentication regularTeller = new Authentication(Set.of("ROLE_TELLER"));
        Authentication seniorTeller = new Authentication(Set.of("ROLE_TELLER", "ROLE_SENIOR_TELLER"));

        CustomExpressionRoot regularRoot = new CustomExpressionRoot(regularTeller, LocalTime.of(0, 0), LocalTime.of(23, 59));
        CustomExpressionRoot seniorRoot = new CustomExpressionRoot(seniorTeller, LocalTime.of(0, 0), LocalTime.of(23, 59));

        System.out.println("regular teller, $3000 withdrawal: " + checkExpression(regularRoot, new BigDecimal("3000")));
        System.out.println("regular teller, $10000 withdrawal: " + checkExpression(regularRoot, new BigDecimal("10000")));
        System.out.println("senior teller, $10000 withdrawal: " + checkExpression(seniorRoot, new BigDecimal("10000")));
    }
}
```

How to run: `java CustomExpressionsLevel3.java`

The regular teller's `$3000` request passes (under their `$5000` limit), but their `$10000` request fails (over it); the senior teller's identical `$10000` request passes, since `isWithinTransactionLimit` checks for `ROLE_SENIOR_TELLER` and applies a higher `$50000` limit instead — two custom functions (`isBusinessHours`, `isWithinTransactionLimit`) and one inherited function (`hasRole`) all combining seamlessly in a single expression-equivalent check.

## 6. Walkthrough

Trace `checkExpression(regularRoot, new BigDecimal("10000"))` from Level 3.

1. `root.isBusinessHours()` checks the current time against the wide `LocalTime.of(0,0)` to `LocalTime.of(23,59)` window — this is `true` for essentially any time the code runs, so this half of the combined `&&` passes.
2. `root.hasRole("TELLER")` checks `regularTeller.authorities()`, which is `{"ROLE_TELLER"}`, for `"ROLE_TELLER"` — present, so this returns `true`.
3. `root.isWithinTransactionLimit(new BigDecimal("10000"))` runs next: inside, `hasRole("SENIOR_TELLER")` checks the same authorities set for `"ROLE_SENIOR_TELLER"` — absent (regular teller only has `ROLE_TELLER`), so `limit` is set to `new BigDecimal("5000")`.
4. `amount.compareTo(limit)` compares `10000` against `5000`; since `10000` is greater than `5000`, `compareTo` returns a positive value, and `<= 0` is `false` — `isWithinTransactionLimit` returns `false`.
5. The overall `&&` chain is `true && true && false`, which is `false` — `checkExpression` returns `false`, correctly denying the regular teller's `$10000` withdrawal request, since it exceeds their applicable limit, even though both the business-hours and role checks passed independently.

```
checkExpression(regularRoot, $10000):
  isBusinessHours()              -> true
  hasRole("TELLER")               -> true
  isWithinTransactionLimit($10000):
    hasRole("SENIOR_TELLER")      -> false -> limit = $5000
    $10000 <= $5000?              -> false
  -> true && true && false -> DENIED
```

## 7. Gotchas & takeaways

> **Gotcha:** a custom `MethodSecurityExpressionRoot` subclass must correctly delegate to (or properly extend) the framework's default root's constructor and internal state — an incomplete or incorrect extension can silently break built-in functions like `hasRole` for every expression in the application, not just the ones using the new custom function, since the custom root *replaces* the default one application-wide once configured.

- Custom `MethodSecurityExpressionHandler`/expression root subclasses add genuinely new, first-class functions to the SpEL vocabulary, callable identically to built-in functions like `hasRole` in any `@PreAuthorize`/`@PostAuthorize` expression.
- Reach for this extension point specifically when a condition is reusable across many expressions throughout the application and reads naturally as part of the core vocabulary, rather than for one-off logic better served by the simpler `@beanName.method(...)` delegation from the previous card.
- A custom expression root can access whatever context it's constructed with (a business-hours window, a role-dependent limit) and can freely call its own other custom functions or the inherited built-in ones as part of computing a result.
- Because the custom root replaces the default one application-wide, correctly extending (not accidentally breaking) the base root's existing behavior is essential — a mistake here can silently affect every expression in the application, not just ones using the new function.
