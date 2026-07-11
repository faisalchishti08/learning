---
card: spring-security
gi: 15
slug: handling-security-exceptions-exceptiontranslationfilter
title: "Handling security exceptions (ExceptionTranslationFilter)"
---

## 1. What it is

`ExceptionTranslationFilter` is the filter (positioned late in the chain, just before `AuthorizationFilter`) that wraps the rest of the filter chain in a try/catch and translates the two kinds of security exceptions it catches — `AuthenticationException` and `AccessDeniedException` — into an actual HTTP response, by delegating to `AuthenticationEntryPoint` or `AccessDeniedHandler` respectively. Without this filter, a thrown security exception would simply propagate up as an unhandled server error; with it, the exception becomes a well-formed `401` or `403` response.

```java
// conceptually, what ExceptionTranslationFilter does around the rest of the chain
try {
    chain.doFilter(request, response);
} catch (AccessDeniedException ex) {
    accessDeniedHandler.handle(request, response, ex);
} catch (AuthenticationException ex) {
    authenticationEntryPoint.commence(request, response, ex);
}
```

## 2. Why & when

Security decisions are made deep inside the filter chain — an authentication filter deciding credentials are invalid, or `AuthorizationFilter` deciding an authenticated user lacks a required role — but neither of those components should also need to know how to render an HTTP response for every possible client type. `ExceptionTranslationFilter` exists as the single seam between "a security decision was made" and "a response was produced," catching both exception types in one place and routing each to the correct pluggable handler, so every other filter and every `AuthenticationProvider` can simply `throw` and trust that the exception will be turned into a sensible response somewhere upstream.

Reach for understanding `ExceptionTranslationFilter` when:

- Debugging why a security exception thrown deep in a custom filter or `AuthenticationProvider` results in a specific HTTP response — the answer is always "it propagated up until `ExceptionTranslationFilter` caught it and delegated to whichever handler is registered."
- Customizing what happens on authentication failure versus authorization failure — the two cases are handled by genuinely different interfaces (`AuthenticationEntryPoint` for the former, `AccessDeniedHandler` for the latter), both configured through this one filter.
- Reasoning about why this filter's *position* in the chain matters — it must wrap every filter whose exceptions it is meant to catch, meaning it needs to sit early enough to surround `AuthorizationFilter` and any authentication filters, but the request still needs to reach it in the first place.

## 3. Core concept

```
 ExceptionTranslationFilter wraps ALL the filters positioned AFTER it in a try/catch:

   try {
       (SecurityContextHolderFilter, CsrfFilter, auth filter, AuthorizationFilter, ...)
   } catch (AccessDeniedException ade) {
       -- an AUTHENTICATED principal lacked a required permission
       accessDeniedHandler.handle(request, response, ade)
   } catch (AuthenticationException ae) {
       -- NO principal was established, or credentials were invalid
       authenticationEntryPoint.commence(request, response, ae)
   }
```

The exception's *type* alone determines which handler runs — `AccessDeniedException` always means "known identity, insufficient permission"; `AuthenticationException` always means "no valid identity was established."

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="ExceptionTranslationFilter wraps the rest of the filter chain in a try catch an AccessDeniedException is routed to AccessDeniedHandler while an AuthenticationException is routed to AuthenticationEntryPoint">
  <rect x="180" y="15" width="280" height="120" rx="10" fill="none" stroke="#8b949e" stroke-width="1" stroke-dasharray="4,3"/>
  <text x="320" y="30" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">try { rest of chain }</text>

  <rect x="200" y="45" width="110" height="40" rx="7" fill="#1c2430" stroke="#8b949e" stroke-width="1.1"/>
  <text x="255" y="69" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">auth filter</text>

  <rect x="330" y="45" width="110" height="40" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="1.3"/>
  <text x="385" y="69" fill="#79c0ff" font-size="7" text-anchor="middle" font-family="sans-serif">AuthorizationFilter</text>

  <rect x="10" y="150" width="230" height="42" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="1.3"/>
  <text x="125" y="175" fill="#6db33f" font-size="7.5" text-anchor="middle" font-family="sans-serif">AuthenticationEntryPoint.commence</text>

  <rect x="400" y="150" width="230" height="42" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="1.3"/>
  <text x="515" y="175" fill="#6db33f" font-size="7.5" text-anchor="middle" font-family="sans-serif">AccessDeniedHandler.handle</text>

  <defs><marker id="a15" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
  <line x1="255" y1="85" x2="125" y2="150" stroke="#8b949e" stroke-width="1.1" marker-end="url(#a15)"/>
  <text x="150" y="115" fill="#8b949e" font-size="6.5" font-family="sans-serif">AuthenticationException</text>
  <line x1="385" y1="85" x2="515" y2="150" stroke="#8b949e" stroke-width="1.1" marker-end="url(#a15)"/>
  <text x="440" y="115" fill="#8b949e" font-size="6.5" font-family="sans-serif">AccessDeniedException</text>
</svg>

One catch block, two exception types, two entirely separate handler interfaces.

## 5. Runnable example

The scenario: model the filter's try/catch dispatch directly, routing two exception types thrown by "downstream filters" to two different handlers. Start with the basic dispatch for one exception type, then add both types and their separate handlers, then add a realistic scenario where the *same* underlying request produces different exceptions depending on whether a principal was already established.

### Level 1 — Basic

A minimal translator that catches one custom exception type and delegates to a handler.

```java
import java.util.function.Supplier;

public class ExceptionTranslationLevel1 {
    static class AuthenticationException extends RuntimeException {
        AuthenticationException(String msg) { super(msg); }
    }

    interface AuthenticationEntryPoint {
        String commence(AuthenticationException ex);
    }

    static String translate(Supplier<String> restOfChain, AuthenticationEntryPoint entryPoint) {
        try {
            return restOfChain.get();
        } catch (AuthenticationException ex) {
            return entryPoint.commence(ex);
        }
    }

    public static void main(String[] args) {
        AuthenticationEntryPoint entryPoint = ex -> "401 Unauthorized: " + ex.getMessage();

        Supplier<String> failingChain = () -> { throw new AuthenticationException("no credentials supplied"); };
        System.out.println(translate(failingChain, entryPoint));
    }
}
```

How to run: `java ExceptionTranslationLevel1.java`

`translate` calls `restOfChain.get()` inside a try block; when it throws `AuthenticationException`, the catch block delegates to `entryPoint.commence`, converting the raw exception into a formatted response string.

### Level 2 — Intermediate

Add the second exception type (`AccessDeniedException`) and its own handler, so both security-exception categories are routed correctly.

```java
import java.util.function.Supplier;

public class ExceptionTranslationLevel2 {
    static class AuthenticationException extends RuntimeException {
        AuthenticationException(String msg) { super(msg); }
    }
    static class AccessDeniedException extends RuntimeException {
        AccessDeniedException(String msg) { super(msg); }
    }

    interface AuthenticationEntryPoint { String commence(AuthenticationException ex); }
    interface AccessDeniedHandler { String handle(AccessDeniedException ex); }

    static String translate(Supplier<String> restOfChain, AuthenticationEntryPoint entryPoint, AccessDeniedHandler deniedHandler) {
        try {
            return restOfChain.get();
        } catch (AccessDeniedException ex) {
            return deniedHandler.handle(ex); // checked FIRST -- AccessDeniedException is not a subtype here, order is deliberate
        } catch (AuthenticationException ex) {
            return entryPoint.commence(ex);
        }
    }

    public static void main(String[] args) {
        AuthenticationEntryPoint entryPoint = ex -> "401 Unauthorized: " + ex.getMessage();
        AccessDeniedHandler deniedHandler = ex -> "403 Forbidden: " + ex.getMessage();

        Supplier<String> noIdentity = () -> { throw new AuthenticationException("no credentials supplied"); };
        Supplier<String> knownButForbidden = () -> { throw new AccessDeniedException("requires ROLE_ADMIN"); };

        System.out.println(translate(noIdentity, entryPoint, deniedHandler));
        System.out.println(translate(knownButForbidden, entryPoint, deniedHandler));
    }
}
```

How to run: `java ExceptionTranslationLevel2.java`

The two exception types now route to two entirely different handlers producing different status codes (`401` vs. `403`) — `AccessDeniedException` always implies a principal already exists but lacks permission, while `AuthenticationException` always implies no valid principal was ever established.

### Level 3 — Advanced

Model a realistic scenario: `AuthorizationFilter` itself decides which exception to throw, based on whether `SecurityContextHolder` already has an authenticated principal — reproducing the real logic that determines `401` versus `403` for the exact same denied resource.

```java
import java.util.function.Supplier;

public class ExceptionTranslationLevel3 {
    static class AuthenticationException extends RuntimeException {
        AuthenticationException(String msg) { super(msg); }
    }
    static class AccessDeniedException extends RuntimeException {
        AccessDeniedException(String msg) { super(msg); }
    }

    interface AuthenticationEntryPoint { String commence(AuthenticationException ex); }
    interface AccessDeniedHandler { String handle(AccessDeniedException ex); }

    record SecurityContext(String principal, java.util.Set<String> roles) {}

    // models AuthorizationFilter's real decision: no principal -> AuthenticationException; principal but missing role -> AccessDeniedException
    static void authorizationFilter(SecurityContext context, String requiredRole) {
        if (context.principal() == null) {
            throw new AuthenticationException("no authenticated principal for this request");
        }
        if (!context.roles().contains(requiredRole)) {
            throw new AccessDeniedException("principal '" + context.principal() + "' lacks " + requiredRole);
        }
        System.out.println("access granted to " + context.principal());
    }

    static String translate(Runnable restOfChain, AuthenticationEntryPoint entryPoint, AccessDeniedHandler deniedHandler) {
        try {
            restOfChain.run();
            return "200 OK";
        } catch (AccessDeniedException ex) {
            return deniedHandler.handle(ex);
        } catch (AuthenticationException ex) {
            return entryPoint.commence(ex);
        }
    }

    public static void main(String[] args) {
        AuthenticationEntryPoint entryPoint = ex -> "401 Unauthorized: " + ex.getMessage();
        AccessDeniedHandler deniedHandler = ex -> "403 Forbidden: " + ex.getMessage();

        SecurityContext anonymous = new SecurityContext(null, java.util.Set.of());
        SecurityContext regularUser = new SecurityContext("bob", java.util.Set.of("ROLE_USER"));
        SecurityContext admin = new SecurityContext("alice", java.util.Set.of("ROLE_ADMIN"));

        for (SecurityContext ctx : java.util.List.of(anonymous, regularUser, admin)) {
            String result = translate(() -> authorizationFilter(ctx, "ROLE_ADMIN"), entryPoint, deniedHandler);
            System.out.println((ctx.principal() == null ? "anonymous" : ctx.principal()) + " -> " + result);
        }
    }
}
```

How to run: `java ExceptionTranslationLevel3.java`

The same protected resource (`requiredRole = "ROLE_ADMIN"`) produces three different outcomes depending purely on `SecurityContext` state: no principal produces `401`, an authenticated-but-insufficiently-privileged principal produces `403`, and a correctly-privileged principal produces `200 OK` — exactly the decision tree `AuthorizationFilter` and `ExceptionTranslationFilter` implement together in a real Spring Security application.

## 6. Walkthrough

Trace Level 3's loop for its three `SecurityContext` values.

1. For `anonymous` (`principal = null`), `translate` calls `restOfChain.run()`, which invokes `authorizationFilter(anonymous, "ROLE_ADMIN")`; inside, `context.principal() == null` is `true`, so it throws `AuthenticationException("no authenticated principal for this request")` immediately, before ever checking roles.
2. Back in `translate`, the thrown exception is caught by the `catch (AuthenticationException ex)` block (the `AccessDeniedException` catch is checked first but doesn't match, since these are unrelated exception types here), and `entryPoint.commence(ex)` runs, returning `"401 Unauthorized: no authenticated principal for this request"`.
3. For `regularUser` (`principal = "bob"`, `roles = {ROLE_USER}`), `authorizationFilter` finds `context.principal() != null`, so it skips the `AuthenticationException` branch, then checks `context.roles().contains("ROLE_ADMIN")`, which is `false` since bob only has `ROLE_USER` — it throws `AccessDeniedException("principal 'bob' lacks ROLE_ADMIN")`.
4. `translate` catches this as `AccessDeniedException` and calls `deniedHandler.handle(ex)`, returning `"403 Forbidden: principal 'bob' lacks ROLE_ADMIN"` — note this is a *different* status code from step 2, even though both requests were ultimately denied, because bob has a real, established identity.
5. For `admin` (`principal = "alice"`, `roles = {ROLE_ADMIN}`), both checks in `authorizationFilter` pass without throwing: it prints `"access granted to alice"` and returns normally, so `translate`'s try block completes without hitting any catch clause, returning `"200 OK"`.

```
anonymous (no principal)        -> AuthenticationException -> AuthenticationEntryPoint -> 401
bob (principal, wrong role)     -> AccessDeniedException   -> AccessDeniedHandler      -> 403
alice (principal, correct role) -> (no exception)          -> (falls through)          -> 200
```

## 7. Gotchas & takeaways

> **Gotcha:** confusing `401` and `403` in application logic (or in a custom `AuthorizationFilter`-like check) by throwing the wrong exception type is a common mistake — a check that simply returns "false" without distinguishing "no identity" from "known identity, wrong permission" ends up conflating both into the same status code, which is misleading to API clients trying to decide whether to prompt for login (appropriate for `401`) or show a "you don't have access" message (appropriate for `403`).

- `ExceptionTranslationFilter` is the single seam translating thrown security exceptions into HTTP responses — every filter and `AuthenticationProvider` upstream of it can simply `throw` and trust the translation happens correctly further up the chain.
- `AuthenticationException` (no valid identity) and `AccessDeniedException` (valid identity, insufficient permission) are routed to two entirely different, independently configurable handlers — `AuthenticationEntryPoint` and `AccessDeniedHandler` respectively.
- This filter's position in the chain is deliberate: it must sit early enough to wrap every filter whose exceptions it needs to catch, including `AuthorizationFilter` near the very end.
- When debugging an unexpected `401` versus `403`, checking whether `SecurityContextHolder` already held a principal at the point of failure is usually the fastest way to determine which branch actually fired.
