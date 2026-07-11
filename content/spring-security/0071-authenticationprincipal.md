---
card: spring-security
gi: 71
slug: authenticationprincipal
title: "@AuthenticationPrincipal"
---

## 1. What it is

`@AuthenticationPrincipal` is the parameter annotation that injects the current `Authentication`'s principal directly into a controller (or any Spring-managed) method parameter, saving the boilerplate of manually calling `SecurityContextHolder.getContext().getAuthentication().getPrincipal()` and casting the result — it optionally accepts a SpEL expression to extract a specific nested property, and works with any custom `UserDetails` implementation, not just the built-in type.

```java
@GetMapping("/account")
public Account getAccount(@AuthenticationPrincipal CustomUserDetails principal) {
    return accountService.findByUsername(principal.getUsername());
}

@GetMapping("/account/email")
public String getEmail(@AuthenticationPrincipal(expression = "email") CustomUserDetails principal) {
    return principal.getEmail(); // or, equivalently: @AuthenticationPrincipal String email
}
```

## 2. Why & when

Every controller method needing to know "who is making this request" would otherwise repeat the identical, slightly awkward boilerplate — reach into `SecurityContextHolder`, call `getAuthentication()`, call `getPrincipal()`, cast it to the application's actual `UserDetails` implementation — purely to extract information the framework already has readily available at exactly the point a controller method is invoked. `@AuthenticationPrincipal` eliminates this repetition entirely, letting a controller simply declare a parameter of the expected principal type and have Spring Security resolve and inject it automatically, with the SpEL `expression` attribute additionally allowing extraction of just one specific nested field when that's all a given method actually needs.

Reach for `@AuthenticationPrincipal` when:

- Any controller method (or other Spring MVC-managed handler) needs access to the current authenticated user's details — this is the standard, idiomatic way to obtain that, in preference to manually querying `SecurityContextHolder` directly.
- Only one specific field of the principal is actually needed — `@AuthenticationPrincipal(expression = "email")` (or the shorthand `@AuthenticationPrincipal String email` when the parameter name matches a property name) avoids injecting the entire principal object just to immediately extract one field from it.
- Testing controller methods using this annotation — `@WithMockUser` or `@WithUserDetails` (Spring Security's test support annotations) populate `SecurityContextHolder` appropriately so `@AuthenticationPrincipal`-annotated parameters resolve correctly in a test context without needing a real authentication flow.

## 3. Core concept

```
 @AuthenticationPrincipal CustomUserDetails principal
   -- Spring MVC's argument resolver mechanism recognizes THIS annotation specifically
   -- resolves it by calling: SecurityContextHolder.getContext().getAuthentication().getPrincipal()
   -- CASTS the result to the DECLARED parameter type (CustomUserDetails)
   -- INJECTS it directly as the method's argument -- no manual retrieval code needed AT ALL

 @AuthenticationPrincipal(expression = "email") String email
   -- resolves the principal FIRST (as above), THEN evaluates the SpEL expression "email" AGAINST it
   -- effectively: principal.getEmail()  -- injecting JUST that one field's value directly
```

The argument resolver does the retrieval-and-casting work exactly once per request, for every parameter needing it.

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A controller method parameter annotated AuthenticationPrincipal is automatically resolved by Spring MVC's argument resolver mechanism which retrieves the current Authentication's principal from SecurityContextHolder casts it to the declared type and injects it directly eliminating manual boilerplate retrieval code">
  <rect x="15" y="55" width="180" height="42" rx="7" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="105" y="73" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">SecurityContextHolder</text>
  <text x="105" y="86" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">.getContext().getAuthentication()</text>

  <rect x="230" y="55" width="180" height="42" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="1.4"/>
  <text x="320" y="73" fill="#79c0ff" font-size="7.5" text-anchor="middle" font-family="sans-serif">argument resolver</text>
  <text x="320" y="86" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">retrieves + casts principal</text>

  <rect x="445" y="55" width="180" height="42" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="535" y="73" fill="#6db33f" font-size="7.5" text-anchor="middle" font-family="sans-serif">injected directly</text>
  <text x="535" y="86" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">as the method's parameter</text>

  <defs><marker id="a71" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
  <line x1="195" y1="76" x2="230" y2="76" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a71)"/>
  <line x1="410" y1="76" x2="445" y2="76" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a71)"/>
</svg>

Retrieval and casting collapsed into one automatic step, invisible to the controller method itself.

## 5. Runnable example

The scenario: implement the argument-resolution mechanism faithfully, then add the SpEL `expression` attribute for extracting a single field, then apply it in a realistic multi-method controller, confirming each method gets exactly the principal-derived data it declares.

### Level 1 — Basic

The core resolution mechanism: retrieve the current principal and inject it, cast to its actual type.

```java
import java.util.*;

public class AuthenticationPrincipalLevel1 {
    record CustomUserDetails(String username, String email, Set<String> authorities) {}
    record Authentication(Object principal) {}

    static Authentication currentAuthentication; // models SecurityContextHolder's current state

    // models the argument RESOLVER's core behavior
    @SuppressWarnings("unchecked")
    static <T> T resolveAuthenticationPrincipal() {
        return (T) currentAuthentication.principal();
    }

    // models: public Account getAccount(@AuthenticationPrincipal CustomUserDetails principal)
    static String getAccount() {
        CustomUserDetails principal = resolveAuthenticationPrincipal();
        return "account data for " + principal.username();
    }

    public static void main(String[] args) {
        currentAuthentication = new Authentication(new CustomUserDetails("alice", "alice@example.com", Set.of("ROLE_USER")));

        System.out.println(getAccount());
    }
}
```

How to run: `java AuthenticationPrincipalLevel1.java`

`resolveAuthenticationPrincipal` reads directly from `currentAuthentication.principal()` and casts it to whatever type is expected — `getAccount` never touches `SecurityContextHolder`-style retrieval logic itself at all, receiving the already-resolved, correctly-typed `principal` object as if it were simply a normal method parameter.

### Level 2 — Intermediate

Add the SpEL `expression` attribute, resolving a single nested field rather than the whole principal object.

```java
import java.util.*;
import java.util.function.Function;

public class AuthenticationPrincipalLevel2 {
    record CustomUserDetails(String username, String email, Set<String> authorities) {}
    record Authentication(Object principal) {}

    static Authentication currentAuthentication;

    @SuppressWarnings("unchecked")
    static <T> T resolvePrincipal() { return (T) currentAuthentication.principal(); }

    // models @AuthenticationPrincipal(expression = "email") -- resolves principal, THEN applies the expression to it
    static <R> R resolvePrincipalExpression(Function<CustomUserDetails, R> expression) {
        CustomUserDetails principal = resolvePrincipal();
        return expression.apply(principal);
    }

    // models: public String getEmail(@AuthenticationPrincipal(expression = "email") String email)
    static String getEmail() {
        return resolvePrincipalExpression(CustomUserDetails::email);
    }

    // models: public Set<String> getAuthorities(@AuthenticationPrincipal(expression = "authorities") Set<String> authorities)
    static Set<String> getAuthorities() {
        return resolvePrincipalExpression(CustomUserDetails::authorities);
    }

    public static void main(String[] args) {
        currentAuthentication = new Authentication(new CustomUserDetails("alice", "alice@example.com", Set.of("ROLE_USER", "ROLE_ADMIN")));

        System.out.println("resolved email: " + getEmail());
        System.out.println("resolved authorities: " + getAuthorities());
    }
}
```

How to run: `java AuthenticationPrincipalLevel2.java`

Both `getEmail` and `getAuthorities` resolve the *same* full principal object internally via `resolvePrincipal`, but each then applies a different expression (modeled as a `Function` reference to the specific field accessor) to extract just the one value it actually needs — exactly mirroring how `@AuthenticationPrincipal(expression = "email")` and `@AuthenticationPrincipal(expression = "authorities")` would each inject a different single field from the identical underlying principal.

### Level 3 — Advanced

Apply the mechanism across a realistic multi-method controller, confirming each method receives exactly its declared shape of principal-derived data, and demonstrate the annotation working correctly across multiple different requests with different authenticated users.

```java
import java.util.*;
import java.util.function.Function;

public class AuthenticationPrincipalLevel3 {
    record CustomUserDetails(String username, String email, Set<String> authorities) {}
    record Authentication(Object principal) {}

    static Authentication currentAuthentication;

    @SuppressWarnings("unchecked")
    static <T> T resolvePrincipal() { return (T) currentAuthentication.principal(); }

    static <R> R resolvePrincipalExpression(Function<CustomUserDetails, R> expression) {
        return expression.apply(resolvePrincipal());
    }

    // three DIFFERENT "controller methods," each declaring a different injected shape
    static String getFullAccountSummary() {
        CustomUserDetails principal = resolvePrincipal(); // the WHOLE principal
        return "summary for " + principal.username() + " (" + principal.email() + "), roles=" + principal.authorities();
    }

    static String getWelcomeMessage() {
        String username = resolvePrincipalExpression(CustomUserDetails::username); // just ONE field
        return "Welcome, " + username + "!";
    }

    static boolean isAdmin() {
        Set<String> authorities = resolvePrincipalExpression(CustomUserDetails::authorities); // a DIFFERENT single field
        return authorities.contains("ROLE_ADMIN");
    }

    static void simulateRequest(CustomUserDetails principal) {
        currentAuthentication = new Authentication(principal); // models a NEW request's SecurityContext being populated
        System.out.println(getFullAccountSummary());
        System.out.println(getWelcomeMessage());
        System.out.println("is admin? " + isAdmin());
        System.out.println();
    }

    public static void main(String[] args) {
        simulateRequest(new CustomUserDetails("alice", "alice@example.com", Set.of("ROLE_USER", "ROLE_ADMIN")));
        simulateRequest(new CustomUserDetails("bob", "bob@example.com", Set.of("ROLE_USER")));
    }
}
```

How to run: `java AuthenticationPrincipalLevel3.java`

Each of the three "controller methods" independently resolves exactly the shape of data it declares — the full principal, a single username field, or a single authorities field — and calling `simulateRequest` with two different users produces correctly different results for each, exactly as two different real HTTP requests from alice and bob would each see their own, correctly-resolved principal data.

## 6. Walkthrough

Trace `simulateRequest(new CustomUserDetails("bob", "bob@example.com", Set.of("ROLE_USER")))` from Level 3.

1. `currentAuthentication = new Authentication(principal)` sets the "current request's" authentication to wrap bob's `CustomUserDetails` — this models the moment `SecurityContextHolder` is populated for an incoming request, before any controller method runs.
2. `getFullAccountSummary()` calls `resolvePrincipal()`, which casts `currentAuthentication.principal()` to `CustomUserDetails`, correctly resolving to bob's object; it then builds and returns `"summary for bob (bob@example.com), roles=[ROLE_USER]"`.
3. `getWelcomeMessage()` calls `resolvePrincipalExpression(CustomUserDetails::username)`, which internally resolves the same underlying principal (bob's object again) and applies the `username` accessor to it, yielding `"bob"`; the method returns `"Welcome, bob!"`.
4. `isAdmin()` calls `resolvePrincipalExpression(CustomUserDetails::authorities)`, again resolving bob's principal and applying the `authorities` accessor, yielding `{"ROLE_USER"}`; `.contains("ROLE_ADMIN")` checks this set and finds it absent, so `isAdmin()` returns `false`.
5. All three methods independently and correctly derived their own specific view of bob's data from the identical underlying `currentAuthentication` state — none of them needed to know anything about how the others resolved their own data, exactly mirroring how three separate `@AuthenticationPrincipal`-annotated controller method parameters, for three separate endpoints, would each resolve correctly and independently for the same incoming request's authenticated user.

```
simulateRequest(bob's CustomUserDetails):
  currentAuthentication = Authentication(bob's principal)

  getFullAccountSummary() -> resolvePrincipal() -> bob's FULL object -> "summary for bob (bob@example.com), roles=[ROLE_USER]"
  getWelcomeMessage()      -> resolvePrincipalExpression(username)   -> "bob" -> "Welcome, bob!"
  isAdmin()                -> resolvePrincipalExpression(authorities) -> {ROLE_USER} -> contains ROLE_ADMIN? false
```

## 7. Gotchas & takeaways

> **Gotcha:** declaring `@AuthenticationPrincipal` with a type that doesn't actually match the real runtime type of the current principal (expecting a custom `UserDetails` subclass when the actual authentication mechanism in use produces a different type, such as an OAuth2 `OidcUser`) results in a `ClassCastException` at resolution time — always confirm which concrete principal type a given authentication mechanism actually produces before declaring the expected type in a controller method's parameter.

- `@AuthenticationPrincipal` eliminates the repetitive boilerplate of manually retrieving and casting the current principal from `SecurityContextHolder`, injecting it directly as a resolved, correctly-typed method parameter.
- The `expression` attribute (or the shorthand form where the parameter name matches a property name) extracts just one specific field from the principal, avoiding injecting the whole object when only one piece of it is actually needed.
- This is the idiomatic, standard way to access the current user's details in a controller method — preferred over manually querying `SecurityContextHolder` directly in application code.
- The declared parameter type must genuinely match the actual runtime type the active authentication mechanism produces, or resolution fails with a cast exception — this is worth confirming explicitly when working with less common authentication mechanisms (OAuth2, SAML) that may produce a different principal shape than a typical `UserDetails` implementation.
