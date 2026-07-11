---
card: spring-security
gi: 6
slug: security-filter-ordering-full-chain
title: "Security filter ordering (full chain)"
---

## 1. What it is

Within one selected `SecurityFilterChain`, Spring Security invokes a specific, carefully-designed sequence of built-in filters — roughly: `SecurityContextHolderFilter` (loads any existing security context) → `CsrfFilter` (validates CSRF tokens) → the authentication filter (`UsernamePasswordAuthenticationFilter`, `BasicAuthenticationFilter`, or similar, depending on configured auth mechanisms) → `ExceptionTranslationFilter` (converts security exceptions into HTTP responses) → `AuthorizationFilter` (the final gate, enforcing access rules) — with this ordering deliberately fixed because each filter's correct operation depends on specific earlier filters having already run.

```
default order (simplified, most-common filters):
  1. SecurityContextHolderFilter    -- establishes/loads the security context for this request
  2. CsrfFilter                     -- validates CSRF token (needs to know if a session already exists)
  3. UsernamePasswordAuthenticationFilter (or other auth filter) -- performs authentication
  4. ExceptionTranslationFilter     -- catches security exceptions, converts to 401/403 responses
  5. AuthorizationFilter            -- the FINAL gate: is this (now-established) identity allowed?
```

```java
// custom filters are inserted at a DELIBERATE position relative to this existing order
http.addFilterBefore(myCustomFilter, UsernamePasswordAuthenticationFilter.class);
```

## 2. Why & when

Each filter in Spring Security's chain has a specific job that depends on state established by filters earlier in the sequence — authorization decisions (made by `AuthorizationFilter`, positioned last) are meaningless without an already-established identity from the authentication filter that ran before it; CSRF validation needs to know about session state that the context-loading filter established even earlier; exception translation needs to sit *after* authentication and *before* authorization so it can correctly catch and convert failures from either stage into the right HTTP response. Understanding this deliberate, dependency-driven ordering — rather than treating the filter chain as an arbitrary list — is essential both for correctly reasoning about *why* a given security behavior occurs, and for correctly inserting any custom filter at the one position where it will actually see the state and produce the effect it needs to.

Reach for understanding the full filter order when:

- Adding a custom filter to the security chain — correctly choosing `addFilterBefore`/`addFilterAfter`/`addFilterAt` relative to a specific existing filter class requires understanding where in the sequence that custom filter's own logic actually needs to run (before authentication, to reject certain requests outright; after authentication but before authorization, to enrich the established identity; and so on).
- Debugging unexpected security behavior — a CSRF failure occurring for a request that shouldn't need CSRF protection, or an authorization check apparently running against an identity that wasn't correctly established, often traces back to a misunderstanding of, or an accidental disruption to, this ordering.
- Understanding why authentication always precedes authorization within the chain, structurally, not just conceptually — `AuthorizationFilter`'s position at (or near) the very end of the chain is a direct, physical embodiment of the authentication-before-authorization principle established in earlier cards.

## 3. Core concept

```
 request enters the chain
        |
        v
 SecurityContextHolderFilter  -- loads/establishes SecurityContext (possibly EMPTY, if not yet authenticated)
        |
        v
 CsrfFilter                   -- validates CSRF token (relies on session state already being known)
        |
        v
 Authentication filter        -- ACTUALLY establishes identity (populates SecurityContext with an Authentication)
        |
        v
 ExceptionTranslationFilter   -- wraps everything AFTER it; catches AuthenticationException/AccessDeniedException
        |                         thrown by LATER filters, converts to 401/403
        v
 AuthorizationFilter          -- the LAST gate: checks the NOW-ESTABLISHED identity against access rules
        |
        v
 (if all passed) -- request FINALLY reaches the controller method
```

Each filter's position reflects a genuine dependency on what must already be true (or already established) by the time that filter runs — this is not an arbitrary or easily-reorderable sequence.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Five ordered filters run in sequence context loading csrf validation authentication exception translation and authorization with each filter depending on state established by the filters before it in the chain">
  <rect x="10" y="60" width="115" height="46" rx="7" fill="#1c2430" stroke="#8b949e" stroke-width="1.1"/>
  <text x="67" y="80" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">SecurityContext</text>
  <text x="67" y="93" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">HolderFilter</text>

  <rect x="135" y="60" width="95" height="46" rx="7" fill="#1c2430" stroke="#8b949e" stroke-width="1.1"/>
  <text x="182" y="87" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">CsrfFilter</text>

  <rect x="240" y="60" width="120" height="46" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="300" y="80" fill="#6db33f" font-size="7.5" text-anchor="middle" font-family="sans-serif">Authentication</text>
  <text x="300" y="93" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">filter</text>

  <rect x="370" y="60" width="130" height="46" rx="7" fill="#1c2430" stroke="#8b949e" stroke-width="1.1"/>
  <text x="435" y="80" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">ExceptionTranslation</text>
  <text x="435" y="93" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">Filter</text>

  <rect x="510" y="60" width="115" height="46" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="567" y="87" fill="#79c0ff" font-size="7.5" text-anchor="middle" font-family="sans-serif">AuthorizationFilter</text>

  <defs><marker id="a6" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
  <line x1="125" y1="83" x2="135" y2="83" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a6)"/>
  <line x1="230" y1="83" x2="240" y2="83" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a6)"/>
  <line x1="360" y1="83" x2="370" y2="83" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a6)"/>
  <line x1="500" y1="83" x2="510" y2="83" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a6)"/>
</svg>

Five filters, five deliberate positions, each depending on state the filters before it have already established.

## 5. Runnable example

The scenario: model the ordered chain directly, with each filter reading and/or writing shared state, showing exactly what would break if two specific filters were swapped. Start with the correctly-ordered chain running end to end, then swap authentication and authorization to show authorization checking against a non-existent identity, then add a custom filter inserted at a correct, deliberate position.

### Level 1 — Basic

The correctly-ordered chain, running end to end against one request.

```java
import java.util.*;
import java.util.function.Function;

public class FilterOrderingLevel1 {
    static class SecurityState {
        boolean contextLoaded = false;
        boolean csrfValid = false;
        String authenticatedUser = null; // null until the authentication filter runs
        boolean authorized = false;
    }

    static Function<SecurityState, Boolean> securityContextFilter = state -> { state.contextLoaded = true; return true; };
    static Function<SecurityState, Boolean> csrfFilter = state -> { state.csrfValid = true; return true; };
    static Function<SecurityState, Boolean> authenticationFilter = state -> { state.authenticatedUser = "alice"; return true; };
    static Function<SecurityState, Boolean> authorizationFilter = state -> {
        // CORRECTLY depends on authenticatedUser already being set by the PREVIOUS filter
        return state.authenticatedUser != null && state.authenticatedUser.equals("alice");
    };

    public static void main(String[] args) {
        List<Function<SecurityState, Boolean>> chain = List.of(
                securityContextFilter, csrfFilter, authenticationFilter, authorizationFilter
        );

        SecurityState state = new SecurityState();
        boolean allPassed = true;
        for (Function<SecurityState, Boolean> filter : chain) {
            if (!filter.apply(state)) { allPassed = false; break; }
        }
        System.out.println("all filters passed? " + allPassed + ", authenticatedUser=" + state.authenticatedUser);
    }
}
```

How to run: `java FilterOrderingLevel1.java`

`authorizationFilter` correctly sees `state.authenticatedUser = "alice"`, because `authenticationFilter` ran before it in the list and already populated that field — this correctly-ordered chain passes end to end.

### Level 2 — Intermediate

Swap authentication and authorization's positions, demonstrating exactly what breaks: authorization now runs *before* any identity has been established.

```java
import java.util.*;
import java.util.function.Function;

public class FilterOrderingLevel2 {
    static class SecurityState {
        String authenticatedUser = null;
    }

    static Function<SecurityState, Boolean> authenticationFilter = state -> { state.authenticatedUser = "alice"; return true; };
    static Function<SecurityState, Boolean> authorizationFilter = state -> {
        System.out.println("authorizationFilter running, authenticatedUser=" + state.authenticatedUser);
        return state.authenticatedUser != null && state.authenticatedUser.equals("alice");
    };

    public static void main(String[] args) {
        // MISORDERED: authorization BEFORE authentication -- structurally invalid
        List<Function<SecurityState, Boolean>> misorderedChain = List.of(authorizationFilter, authenticationFilter);

        SecurityState state = new SecurityState();
        boolean allPassed = true;
        for (Function<SecurityState, Boolean> filter : misorderedChain) {
            if (!filter.apply(state)) { allPassed = false; break; }
        }
        System.out.println("misordered chain -- all passed? " + allPassed + " (authorization ran against a NON-EXISTENT identity)");
    }
}
```

How to run: `java FilterOrderingLevel2.java`

`authorizationFilter` runs first in this misordered chain and sees `state.authenticatedUser = null`, since `authenticationFilter` hasn't run yet — the authorization check correctly (from its own local logic's perspective) fails, but for entirely the wrong reason: not because alice lacks permission, but because the chain's ordering never gave the authorization filter a real identity to evaluate against at all, exactly the structural problem the correct ordering exists to prevent.

### Level 3 — Advanced

Add a custom filter inserted at a deliberate, correct position — after authentication (so it has access to the established identity) but before authorization (so it can enrich that identity before the final access check runs), mirroring a real use case like loading additional user attributes from a database.

```java
import java.util.*;
import java.util.function.Function;

public class FilterOrderingLevel3 {
    static class SecurityState {
        String authenticatedUser = null;
        Set<String> roles = new HashSet<>(); // populated by the CUSTOM filter, not authentication itself
    }

    static Function<SecurityState, Boolean> authenticationFilter = state -> {
        state.authenticatedUser = "alice";
        System.out.println("authenticationFilter: established identity = " + state.authenticatedUser);
        return true;
    };

    // a CUSTOM filter -- correctly positioned AFTER authentication, BEFORE authorization
    static Function<SecurityState, Boolean> customRoleEnrichmentFilter = state -> {
        // depends on authenticatedUser ALREADY being set -- would be useless positioned before authenticationFilter
        if ("alice".equals(state.authenticatedUser)) {
            state.roles.add("ADMIN"); // models loading roles from a database, keyed by the established identity
        }
        System.out.println("customRoleEnrichmentFilter: loaded roles = " + state.roles + " for " + state.authenticatedUser);
        return true;
    };

    static Function<SecurityState, Boolean> authorizationFilter = state -> {
        // depends on roles ALREADY being populated -- would incorrectly deny access if this ran before enrichment
        boolean allowed = state.roles.contains("ADMIN");
        System.out.println("authorizationFilter: checking roles=" + state.roles + ", allowed=" + allowed);
        return allowed;
    };

    public static void main(String[] args) {
        // CORRECT order: authentication -> custom enrichment -> authorization
        List<Function<SecurityState, Boolean>> chain = List.of(
                authenticationFilter, customRoleEnrichmentFilter, authorizationFilter
        );

        SecurityState state = new SecurityState();
        boolean allPassed = true;
        for (Function<SecurityState, Boolean> filter : chain) {
            if (!filter.apply(state)) { allPassed = false; break; }
        }
        System.out.println("final result: " + allPassed);
    }
}
```

How to run: `java FilterOrderingLevel3.java`

`customRoleEnrichmentFilter` correctly sees `state.authenticatedUser = "alice"` (set by the filter before it) and populates `state.roles` accordingly, which `authorizationFilter` (positioned after it) then correctly reads to make its `ADMIN`-role-based decision — this three-filter chain models exactly the kind of deliberate custom-filter placement `addFilterAfter(customFilter, UsernamePasswordAuthenticationFilter.class)` achieves in a real Spring Security configuration: inserting custom logic at the one specific point in the chain where it has access to exactly the state it needs, and produces state the filters after it correctly depend on.

## 6. Walkthrough

Trace the full chain execution in Level 3.

1. `authenticationFilter.apply(state)` runs first — it sets `state.authenticatedUser = "alice"` and prints confirmation, then returns `true`, so the loop continues to the next filter.
2. `customRoleEnrichmentFilter.apply(state)` runs next — it checks `"alice".equals(state.authenticatedUser)`, which is `true` (thanks to the previous filter having already run), so it adds `"ADMIN"` to `state.roles`, prints the loaded roles, and returns `true`.
3. `authorizationFilter.apply(state)` runs last — it checks `state.roles.contains("ADMIN")`, which is now `true` (thanks to the enrichment filter having already populated it), prints the check, and returns `true`.
4. All three filters returned `true`, so `allPassed` remains `true` throughout the loop, and the final `println` confirms `"final result: true"` — the entire chain succeeded, with each filter's correct operation depending directly on the specific filters that ran immediately before it.
5. If `customRoleEnrichmentFilter` had instead been positioned *before* `authenticationFilter` (an incorrect ordering), its check `"alice".equals(state.authenticatedUser)` would evaluate against `null` (since authentication hadn't run yet), never adding `"ADMIN"` to `state.roles`, which would then cause `authorizationFilter`'s later check to incorrectly fail — exactly the same class of structural failure demonstrated explicitly in Level 2's misordered authentication/authorization swap.

```
CORRECT order: authenticationFilter -> customRoleEnrichmentFilter -> authorizationFilter
  authenticationFilter:        sets authenticatedUser="alice"
  customRoleEnrichmentFilter:  reads authenticatedUser="alice" (SET already) -> adds "ADMIN" to roles
  authorizationFilter:         reads roles={ADMIN} (SET already) -> allowed=true

each filter's correctness depends STRUCTURALLY on the filters positioned before it having already run
```

## 7. Gotchas & takeaways

> **Gotcha:** inserting a custom filter using `addFilterBefore`/`addFilterAfter` against the *wrong* reference filter class is a subtle mistake that won't produce a compile error or even necessarily an obvious runtime error — it will simply place the custom filter at the wrong position in the chain, silently causing it to run without state it depends on (if placed too early) or too late to influence a decision it was meant to affect (if placed too late), exactly as Level 2 and the misplaced-enrichment-filter scenario in Level 3's walkthrough both demonstrate. Always position a custom filter based on a clear understanding of exactly what state it needs to read and exactly what later filters need to read from it.

- Spring Security's default filter ordering within one chain is deliberately dependency-driven, not arbitrary — context loading before CSRF validation before authentication before exception translation before authorization, each filter depending on state the filters before it have already established.
- `AuthorizationFilter`'s position at (or near) the end of the chain is the structural, physical embodiment of the authentication-before-authorization principle from earlier cards — authorization simply cannot run correctly before an identity has been established.
- Custom filters must be inserted at a deliberate position relative to Spring Security's existing filters, using `addFilterBefore`/`addFilterAfter`/`addFilterAt`, chosen based on exactly what state the custom filter needs available and exactly what later filters need it to produce.
- Debugging unexpected authorization or authentication behavior often benefits from explicitly tracing through the filter order — confirming which filters actually ran, in what sequence, and what state each one saw, is frequently more revealing than examining the failing filter's logic in isolation.
