---
card: spring-security
gi: 56
slug: authorizehttprequests-dsl
title: "authorizeHttpRequests DSL"
---

## 1. What it is

`authorizeHttpRequests` is the `HttpSecurity` DSL method (introduced in the earlier lambda-DSL and HttpSecurity cards) that builds the ordered list of URL-to-`AuthorizationManager` mappings enforced by `AuthorizationFilter` — each `requestMatchers(...)` call paired with an access rule (`.permitAll()`, `.authenticated()`, `.hasRole(...)`, `.access(customManager)`) registers one entry, evaluated top to bottom for every incoming request, with the first matching entry's rule determining the outcome.

```java
http.authorizeHttpRequests(auth -> auth
        .requestMatchers("/public/**").permitAll()
        .requestMatchers("/admin/**").hasRole("ADMIN")
        .requestMatchers(HttpMethod.POST, "/api/orders").hasAuthority("SCOPE_orders:write")
        .anyRequest().authenticated()
);
```

## 2. Why & when

URL-based access control needs to express two things clearly and unambiguously: which requests a rule applies to, and what that rule requires — `authorizeHttpRequests` separates these cleanly into a matcher (`requestMatchers`, or the shorthand path-string overload) and a rule (`.permitAll()`, `.hasRole(...)`, and friends), with each `requestMatchers(...).ruleMethod()` pair becoming one ordered entry. This is the single, centralized place URL-based authorization is declared for an entire `SecurityFilterChain`, making it possible to review an application's complete access policy for one chain by reading this one DSL block top to bottom.

Reach for `authorizeHttpRequests` (and choosing the right rule method) when:

- `.permitAll()` for genuinely public endpoints that need no authentication at all, but should still pass through the rest of the security chain (contrast with `WebSecurityCustomizer`'s `ignoring()`, from an earlier card, which bypasses the chain entirely).
- `.hasRole("ADMIN")` / `.hasAuthority("SCOPE_orders:write")` (the next card covers the distinction) for role- or authority-scoped access to a specific path prefix.
- `.access(customAuthorizationManager)` when a rule needs logic beyond what the built-in convenience methods express — plugging in a custom `AuthorizationManager` (from the previous card) directly.
- `.anyRequest()` as the final, catch-all entry — almost always present, and almost always the *last* entry, since it matches literally everything and would otherwise shadow every more-specific rule listed after it.

## 3. Core concept

```
 authorizeHttpRequests(auth -> auth
     .requestMatchers(matcher1).rule1()
     .requestMatchers(matcher2).rule2()
     .anyRequest().rule3()
 )

 AuthorizationFilter, for EVERY incoming request:
   check matcher1 -- does this request match? YES -> apply rule1, STOP (rule2/rule3 never checked)
                                                NO  -> continue to matcher2
   check matcher2 -- does this request match? YES -> apply rule2, STOP
                                                NO  -> continue
   anyRequest() -- ALWAYS matches -- apply rule3 (the CATCH-ALL, must be registered LAST)
```

Entries are evaluated strictly in registration order, and the first match wins — exactly like the multiple-filter-chains card's own ordering logic, but for individual rules within one chain.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A request is checked against an ordered list of matcher and rule pairs the first matching entry determines the access decision with a catch all anyRequest entry registered last to handle everything not matched by a more specific rule above it">
  <rect x="15" y="15" width="300" height="34" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.2"/>
  <text x="165" y="36" fill="#79c0ff" font-size="7" text-anchor="middle" font-family="sans-serif">requestMatchers(&quot;/public/**&quot;).permitAll()</text>

  <rect x="15" y="60" width="300" height="34" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.2"/>
  <text x="165" y="81" fill="#79c0ff" font-size="7" text-anchor="middle" font-family="sans-serif">requestMatchers(&quot;/admin/**&quot;).hasRole(&quot;ADMIN&quot;)</text>

  <rect x="15" y="105" width="300" height="34" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.4"/>
  <text x="165" y="126" fill="#6db33f" font-size="7" text-anchor="middle" font-family="sans-serif">anyRequest().authenticated()  [CATCH-ALL, LAST]</text>

  <rect x="380" y="60" width="230" height="46" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.3"/>
  <text x="495" y="80" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">first match wins</text>
  <text x="495" y="93" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">remaining entries skipped</text>

  <defs><marker id="a56" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
  <line x1="315" y1="32" x2="380" y2="75" stroke="#8b949e" stroke-width="1" marker-end="url(#a56)"/>
  <line x1="315" y1="77" x2="380" y2="83" stroke="#8b949e" stroke-width="1" marker-end="url(#a56)"/>
  <line x1="315" y1="122" x2="380" y2="90" stroke="#8b949e" stroke-width="1" marker-end="url(#a56)"/>
</svg>

Three entries, one winner per request — determined purely by which is checked first and actually matches.

## 5. Runnable example

The scenario: model the ordered matcher/rule list directly and demonstrate first-match-wins evaluation, then show the consequence of a misordered catch-all shadowing a more specific rule, then add a method-specific matcher (distinguishing `GET` from `POST` on the same path) for a realistic REST API policy.

### Level 1 — Basic

An ordered list of matcher/rule pairs evaluated top to bottom.

```java
import java.util.*;
import java.util.function.Predicate;

public class AuthorizeHttpRequestsLevel1 {
    record Request(String path, Set<String> authorities) {}
    record Entry(Predicate<Request> matcher, Predicate<Request> rule, String description) {}

    static String evaluate(Request request, List<Entry> entries) {
        for (Entry entry : entries) {
            if (entry.matcher().test(request)) {
                return entry.rule().test(request) ? "GRANTED (" + entry.description() + ")" : "DENIED (" + entry.description() + ")";
            }
        }
        return "DENIED (no matching rule -- deny by default)";
    }

    public static void main(String[] args) {
        List<Entry> entries = List.of(
                new Entry(r -> r.path().startsWith("/public/"), r -> true, "permitAll /public/**"),
                new Entry(r -> r.path().startsWith("/admin/"), r -> r.authorities().contains("ROLE_ADMIN"), "hasRole ADMIN /admin/**"),
                new Entry(r -> true, r -> !r.authorities().isEmpty(), "anyRequest authenticated")
        );

        System.out.println(evaluate(new Request("/public/info", Set.of()), entries));
        System.out.println(evaluate(new Request("/admin/reports", Set.of("ROLE_USER")), entries));
        System.out.println(evaluate(new Request("/account", Set.of("ROLE_USER")), entries));
    }
}
```

How to run: `java AuthorizeHttpRequestsLevel1.java`

`/public/info` matches the first entry and is granted unconditionally; `/admin/reports` matches the second entry and is denied since the caller lacks `ROLE_ADMIN`; `/account` matches neither specific entry and falls to the catch-all, which is granted since the caller has some authority at all (representing "authenticated").

### Level 2 — Intermediate

Demonstrate the consequence of a misordered catch-all placed before a more specific rule, shadowing it entirely.

```java
import java.util.*;
import java.util.function.Predicate;

public class AuthorizeHttpRequestsLevel2 {
    record Request(String path, Set<String> authorities) {}
    record Entry(Predicate<Request> matcher, Predicate<Request> rule, String description) {}

    static String evaluate(Request request, List<Entry> entries) {
        for (Entry entry : entries) {
            if (entry.matcher().test(request)) {
                return entry.rule().test(request) ? "GRANTED (" + entry.description() + ")" : "DENIED (" + entry.description() + ")";
            }
        }
        return "DENIED (no matching rule)";
    }

    public static void main(String[] args) {
        Predicate<Request> isAdminPath = r -> r.path().startsWith("/admin/");
        Predicate<Request> hasAdminRole = r -> r.authorities().contains("ROLE_ADMIN");
        Predicate<Request> catchAll = r -> true;
        Predicate<Request> isAuthenticated = r -> !r.authorities().isEmpty();

        List<Entry> correctOrder = List.of(
                new Entry(isAdminPath, hasAdminRole, "hasRole ADMIN"),
                new Entry(catchAll, isAuthenticated, "anyRequest authenticated")
        );

        List<Entry> misorderedCatchAllFirst = List.of(
                new Entry(catchAll, isAuthenticated, "anyRequest authenticated"), // WRONG: registered FIRST
                new Entry(isAdminPath, hasAdminRole, "hasRole ADMIN") // NEVER REACHED
        );

        Request regularUserRequestingAdmin = new Request("/admin/reports", Set.of("ROLE_USER")); // NOT an admin

        System.out.println("correct order:      " + evaluate(regularUserRequestingAdmin, correctOrder));
        System.out.println("misordered (WRONG): " + evaluate(regularUserRequestingAdmin, misorderedCatchAllFirst));
    }
}
```

How to run: `java AuthorizeHttpRequestsLevel2.java`

With the correct order, the regular user requesting `/admin/reports` is correctly denied by the `hasRole ADMIN` rule; with the catch-all mistakenly registered first, the *same* request matches the catch-all's `r -> true` matcher immediately, and since `isAuthenticated` is satisfied (the user has some authority), it's incorrectly *granted* — the entire `/admin/**` restriction is silently bypassed because the catch-all shadowed it.

### Level 3 — Advanced

Add HTTP-method-specific matching, distinguishing read (`GET`) from write (`POST`) access to the same path prefix — a realistic REST API access policy.

```java
import java.util.*;
import java.util.function.Predicate;

public class AuthorizeHttpRequestsLevel3 {
    record Request(String method, String path, Set<String> authorities) {}
    record Entry(Predicate<Request> matcher, Predicate<Request> rule, String description) {}

    static Predicate<Request> pathAndMethod(String method, String pathPrefix) {
        return r -> r.method().equals(method) && r.path().startsWith(pathPrefix);
    }

    static String evaluate(Request request, List<Entry> entries) {
        for (Entry entry : entries) {
            if (entry.matcher().test(request)) {
                return entry.rule().test(request) ? "GRANTED (" + entry.description() + ")" : "DENIED (" + entry.description() + ")";
            }
        }
        return "DENIED (no matching rule)";
    }

    public static void main(String[] args) {
        List<Entry> entries = List.of(
                new Entry(pathAndMethod("GET", "/api/orders"), r -> r.authorities().contains("SCOPE_orders:read"), "GET /api/orders needs orders:read"),
                new Entry(pathAndMethod("POST", "/api/orders"), r -> r.authorities().contains("SCOPE_orders:write"), "POST /api/orders needs orders:write"),
                new Entry(r -> true, r -> !r.authorities().isEmpty(), "anyRequest authenticated")
        );

        Request readOnlyClient = new Request("GET", "/api/orders", Set.of("SCOPE_orders:read"));
        Request writeAttemptByReadOnlyClient = new Request("POST", "/api/orders", Set.of("SCOPE_orders:read")); // read-only, tries to WRITE

        System.out.println(evaluate(readOnlyClient, entries));
        System.out.println(evaluate(writeAttemptByReadOnlyClient, entries));
    }
}
```

How to run: `java AuthorizeHttpRequestsLevel3.java`

`pathAndMethod` matches on *both* the HTTP method and the path, so `GET /api/orders` and `POST /api/orders` are governed by two entirely separate entries, each requiring a different scope — a client holding only `SCOPE_orders:read` is correctly granted for the `GET` request but denied for the `POST` request, demonstrating fine-grained, method-aware access control on the identical URL path.

## 6. Walkthrough

Trace `evaluate(writeAttemptByReadOnlyClient, entries)` from Level 3.

1. The loop begins with the first entry: `pathAndMethod("GET", "/api/orders").test(writeAttemptByReadOnlyClient)` checks `r.method().equals("GET") && r.path().startsWith("/api/orders")` — since `writeAttemptByReadOnlyClient.method()` is `"POST"`, not `"GET"`, the first half of the `&&` is `false`, so the whole matcher returns `false`; this entry doesn't match, and the loop continues.
2. The second entry is checked: `pathAndMethod("POST", "/api/orders").test(writeAttemptByReadOnlyClient)` checks `r.method().equals("POST") && r.path().startsWith("/api/orders")` — both conditions are `true` this time, so the matcher returns `true`; this entry matches, and the loop's `if` block executes.
3. `entry.rule().test(writeAttemptByReadOnlyClient)` runs the rule for this entry: `r.authorities().contains("SCOPE_orders:write")` — `writeAttemptByReadOnlyClient`'s authorities are `{"SCOPE_orders:read"}`, which does not contain `"SCOPE_orders:write"`, so this returns `false`.
4. Since the rule returned `false`, `evaluate` returns `"DENIED (POST /api/orders needs orders:write)"` — the loop never reaches the third, catch-all entry at all, since the second entry already matched and produced a final result.
5. This confirms the read-only client is correctly blocked from writing, purely by the second entry's scope requirement — the request's `path` alone (`/api/orders`) was identical to the earlier successful `GET` request; only the `method` field differed, and that difference alone routed it to an entirely different entry with a different, unmet requirement.

```
writeAttemptByReadOnlyClient: method=POST, path=/api/orders, authorities={SCOPE_orders:read}
  entry 1 (GET /api/orders):  matcher fails (method mismatch) -> skip
  entry 2 (POST /api/orders): matcher matches -> rule checks SCOPE_orders:write -> NOT present -> DENIED
  (entry 3, catch-all, NEVER reached)
```

## 7. Gotchas & takeaways

> **Gotcha:** `anyRequest()` (or any broad catch-all matcher) registered before a more specific rule silently shadows that specific rule entirely, as Level 2 demonstrates — Spring Security actually throws an `IllegalStateException` at startup if `anyRequest()` is followed by *any* further `requestMatchers(...)` calls in the real DSL, specifically to catch this class of misconfiguration early, but no such protection exists for two `requestMatchers(...)` calls registered in the wrong relative order among themselves.

- `authorizeHttpRequests` builds an ordered list of matcher/rule pairs, evaluated top to bottom, with the first matching entry determining the request's access outcome.
- Order matters critically: register more specific matchers before broader ones, and always place `anyRequest()` last, since it matches everything and would otherwise shadow every rule after it.
- HTTP-method-aware matchers (`requestMatchers(HttpMethod.POST, "/api/orders")`) allow fine-grained, per-verb access policies on the same URL path, a common and important pattern for REST APIs distinguishing read from write access.
- A request matching no registered rule at all is denied by default — this fail-closed behavior is deliberate and should be preserved by always ending the DSL block with an explicit, appropriately-scoped catch-all rule.
