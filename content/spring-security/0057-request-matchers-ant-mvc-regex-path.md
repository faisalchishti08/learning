---
card: spring-security
gi: 57
slug: request-matchers-ant-mvc-regex-path
title: "Request matchers (Ant, MVC, regex, path)"
---

## 1. What it is

`requestMatchers(...)` accepts several different matcher styles for deciding which requests a rule applies to — the modern unified `PathPatternRequestMatcher` (Ant-style wildcards like `/admin/**`, now the default and recommended choice, matched using the same `PathPattern` parser Spring MVC's own routing uses), the legacy `AntPathRequestMatcher` (the older, separate Ant-pattern implementation these replaced), `RegexRequestMatcher` for patterns Ant-style syntax can't express, and plain `HttpMethod`-plus-path overloads for the common case of matching a specific verb and path together.

```java
http.authorizeHttpRequests(auth -> auth
        .requestMatchers("/admin/**").hasRole("ADMIN")                     // Ant-style, the modern default
        .requestMatchers(RegexRequestMatcher.regexMatcher("^/api/v[0-9]+/.*$")).authenticated() // regex, for what Ant can't express
        .requestMatchers(HttpMethod.DELETE, "/api/orders/**").hasAuthority("SCOPE_orders:delete") // method + path
        .anyRequest().denyAll()
);
```

## 2. Why & when

Ant-style path patterns (`/admin/**`, `/users/{id}/profile`) cover the overwhelming majority of real routing needs with simple, readable syntax, and are matched using the exact same `PathPattern` engine Spring MVC itself uses for `@RequestMapping`, which is precisely why this is now the recommended default — it guarantees the security matcher and the actual MVC routing agree on what a given URL matches, eliminating a historical class of bugs where an older, separately-implemented Ant matcher and MVC's own routing could disagree on edge cases (trailing slashes, matrix variables) and create an exploitable gap between "what the security rule thinks this URL means" and "what the controller actually does with it."

Reach for each matcher style specifically when:

- Plain string patterns (`requestMatchers("/admin/**")`) for the common case — these now use `PathPatternRequestMatcher` under the hood, Spring Security's current recommended default.
- `RegexRequestMatcher` only for the rare pattern Ant-style syntax genuinely cannot express — matching a numeric API version segment with a specific digit count, or a complex alternation — since regex patterns are harder to read and reason about than Ant patterns for anyone unfamiliar with the specific expression.
- `requestMatchers(HttpMethod.X, "/path")` whenever a rule needs to apply to one specific HTTP verb on a path rather than every verb (as demonstrated in the previous card's `authorizeHttpRequests` example) — omitting the method matches all verbs.
- Avoid the legacy `AntPathRequestMatcher` and `MvcRequestMatcher` in new code entirely — both are effectively superseded by the current default `PathPatternRequestMatcher`, which unifies what those two previously-separate matchers did differently.

## 3. Core concept

```
 requestMatchers("/admin/**")
   -> PathPatternRequestMatcher (the MODERN default)
   -> uses the SAME PathPattern parser Spring MVC's @RequestMapping uses
   -> "/admin/**" matches: /admin, /admin/reports, /admin/reports/2024, ... (any depth after /admin)

 requestMatchers(RegexRequestMatcher.regexMatcher("^/api/v[0-9]+/.*$"))
   -> full regular-expression matching
   -> matches: /api/v1/orders, /api/v42/users, ... (but NOT /api/vX/orders -- "X" isn't a digit)

 requestMatchers(HttpMethod.POST, "/api/orders")
   -> matches ONLY POST requests to exactly this path (or its own Ant-pattern rules, if a wildcard path is given)
   -> a GET to the IDENTICAL path is a COMPLETELY SEPARATE match, governed by a DIFFERENT registered entry (or none)
```

Different syntaxes for the same underlying job: deciding, precisely and unambiguously, which requests a given rule covers.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Three different matcher styles Ant style wildcard patterns regular expressions and HTTP method plus path pairs all feed into the same requestMatchers registration each producing a matcher tested against every incoming request in the authorizeHttpRequests chain">
  <rect x="15" y="20" width="180" height="40" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="1.3"/>
  <text x="105" y="38" fill="#79c0ff" font-size="7.5" text-anchor="middle" font-family="sans-serif">Ant-style: /admin/**</text>
  <text x="105" y="51" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">(modern default)</text>

  <rect x="15" y="70" width="180" height="40" rx="7" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="105" y="88" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">regex: ^/api/v[0-9]+/.*$</text>
  <text x="105" y="101" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">(rare, complex patterns)</text>

  <rect x="15" y="120" width="180" height="40" rx="7" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="105" y="138" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">HttpMethod.POST + path</text>
  <text x="105" y="151" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">(verb-specific matching)</text>

  <rect x="290" y="65" width="180" height="46" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="380" y="85" fill="#6db33f" font-size="7.5" text-anchor="middle" font-family="sans-serif">requestMatchers(...)</text>
  <text x="380" y="98" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">registered in authorizeHttpRequests</text>

  <defs><marker id="a57" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
  <line x1="195" y1="40" x2="290" y2="80" stroke="#8b949e" stroke-width="1" marker-end="url(#a57)"/>
  <line x1="195" y1="90" x2="290" y2="88" stroke="#8b949e" stroke-width="1" marker-end="url(#a57)"/>
  <line x1="195" y1="140" x2="290" y2="96" stroke="#8b949e" stroke-width="1" marker-end="url(#a57)"/>
</svg>

Three syntaxes, one registration point — each ultimately producing a matcher tested identically against every request.

## 5. Runnable example

The scenario: implement a simplified Ant-pattern matcher (supporting `**` and `*` wildcards, the two most common), then a regex-based matcher for a case Ant syntax can't express cleanly, then combine method-aware matching with both styles for a realistic API access policy.

### Level 1 — Basic

A simplified Ant-style matcher supporting `**` (any depth) and `*` (single segment) wildcards.

```java
import java.util.*;

public class RequestMatchersLevel1 {
    static boolean antMatches(String pattern, String path) {
        // convert the Ant pattern into a regex: ** -> .*, * -> [^/]*
        String regex = pattern
                .replace(".", "\\.")
                .replace("**", "@@DOUBLESTAR@@")
                .replace("*", "[^/]*")
                .replace("@@DOUBLESTAR@@", ".*");
        return path.matches(regex);
    }

    public static void main(String[] args) {
        String pattern = "/admin/**";
        for (String path : List.of("/admin", "/admin/reports", "/admin/reports/2024/q1", "/adminx")) {
            System.out.println(path + " matches '" + pattern + "'? " + antMatches(pattern, path));
        }
    }
}
```

How to run: `java RequestMatchersLevel1.java`

`/admin`, `/admin/reports`, and `/admin/reports/2024/q1` all match `/admin/**` (the `**` wildcard spans any depth after the prefix), while `/adminx` does not, since it isn't actually under the `/admin/` path segment at all — it merely shares a text prefix, which Ant-style matching correctly distinguishes from a true path-segment match.

### Level 2 — Intermediate

Add a regex matcher for a pattern Ant syntax cannot express cleanly: an API version segment that must be purely numeric.

```java
import java.util.*;
import java.util.regex.Pattern;

public class RequestMatchersLevel2 {
    static boolean antMatches(String pattern, String path) {
        String regex = pattern.replace(".", "\\.").replace("**", "@@DS@@").replace("*", "[^/]*").replace("@@DS@@", ".*");
        return path.matches(regex);
    }

    static boolean regexMatches(String regexPattern, String path) {
        return Pattern.matches(regexPattern, path);
    }

    public static void main(String[] args) {
        // Ant-style CANNOT distinguish "v1" (valid numeric version) from "vX" (an invalid, non-numeric segment) --
        // /api/v*/orders would match BOTH, since * matches any single segment regardless of its content
        System.out.println("Ant '/api/v*/orders' matches '/api/v1/orders'?  " + antMatches("/api/v*/orders", "/api/v1/orders"));
        System.out.println("Ant '/api/v*/orders' matches '/api/vX/orders'?  " + antMatches("/api/v*/orders", "/api/vX/orders")
                + "  (WRONGLY matches -- Ant syntax can't require digits-only)");

        // regex CAN express this precisely: v followed by ONE OR MORE DIGITS specifically
        String versionRegex = "^/api/v[0-9]+/orders$";
        System.out.println("regex matches '/api/v1/orders'?  " + regexMatches(versionRegex, "/api/v1/orders"));
        System.out.println("regex matches '/api/vX/orders'?  " + regexMatches(versionRegex, "/api/vX/orders")
                + "  (CORRECTLY rejected -- regex expresses the digits-only requirement)");
    }
}
```

How to run: `java RequestMatchersLevel2.java`

The Ant pattern `/api/v*/orders` matches `/api/vX/orders` just as readily as `/api/v1/orders`, since `*` matches any single path segment regardless of its actual content; the regex pattern `^/api/v[0-9]+/orders$` correctly distinguishes them, since `[0-9]+` specifically requires one or more digit characters — exactly the kind of content-aware constraint Ant-style wildcard syntax cannot express.

### Level 3 — Advanced

Combine method-aware matching with both Ant and regex styles into one realistic, multi-entry API access policy.

```java
import java.util.*;
import java.util.function.Predicate;
import java.util.regex.Pattern;

public class RequestMatchersLevel3 {
    record Request(String method, String path, Set<String> authorities) {}
    record Entry(Predicate<Request> matcher, Predicate<Request> rule, String description) {}

    static boolean antMatches(String pattern, String path) {
        String regex = pattern.replace(".", "\\.").replace("**", "@@DS@@").replace("*", "[^/]*").replace("@@DS@@", ".*");
        return path.matches(regex);
    }

    static Predicate<Request> antMatcher(String method, String pattern) {
        return r -> r.method().equals(method) && antMatches(pattern, r.path());
    }

    static Predicate<Request> regexMatcher(String method, String regexPattern) {
        return r -> r.method().equals(method) && Pattern.matches(regexPattern, r.path());
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
                new Entry(regexMatcher("GET", "^/api/v[0-9]+/orders$"), r -> r.authorities().contains("SCOPE_read"), "versioned GET orders (regex)"),
                new Entry(antMatcher("DELETE", "/api/**"), r -> r.authorities().contains("ROLE_ADMIN"), "any DELETE under /api/** needs ADMIN")
        );

        Request validVersionedGet = new Request("GET", "/api/v2/orders", Set.of("SCOPE_read"));
        Request invalidVersionSegment = new Request("GET", "/api/vX/orders", Set.of("SCOPE_read"));
        Request deleteAttempt = new Request("DELETE", "/api/v2/orders/42", Set.of("SCOPE_read")); // NOT an admin

        System.out.println(evaluate(validVersionedGet, entries));
        System.out.println(evaluate(invalidVersionSegment, entries));
        System.out.println(evaluate(deleteAttempt, entries));
    }
}
```

How to run: `java RequestMatchersLevel3.java`

`validVersionedGet` matches the regex-based entry and is granted (correct scope present); `invalidVersionSegment`'s non-numeric `vX` segment fails the regex matcher's digit requirement, falling through to "no matching rule" and being denied by default; `deleteAttempt` matches the second, Ant-based entry (any `DELETE` under `/api/**`) and is denied, since the caller lacks `ROLE_ADMIN` — three genuinely different outcomes, each governed by the matcher style best suited to expressing its specific condition.

## 6. Walkthrough

Trace `evaluate(invalidVersionSegment, entries)` from Level 3.

1. The loop checks the first entry: `regexMatcher("GET", "^/api/v[0-9]+/orders$").test(invalidVersionSegment)` first checks `r.method().equals("GET")`, which is `true` (the request's method is `"GET"`); then it checks `Pattern.matches("^/api/v[0-9]+/orders$", "/api/vX/orders")` — the regex requires `v` followed by one or more digits (`[0-9]+`), but the path has `vX` (a literal `X`, not a digit) in that position, so this match fails, and the overall predicate returns `false`.
2. Since the first entry's matcher returned `false`, the loop continues to the second entry: `antMatcher("DELETE", "/api/**").test(invalidVersionSegment)` first checks `r.method().equals("DELETE")` — but `invalidVersionSegment.method()` is `"GET"`, not `"DELETE"`, so this is `false` immediately, and the whole `&&` expression short-circuits to `false` without even evaluating the Ant-pattern comparison.
3. Both entries' matchers returned `false`, so the `for` loop completes without ever finding a match, and `evaluate` reaches its final line, returning `"DENIED (no matching rule)"`.
4. This demonstrates the fail-closed default from the previous card applying here too: a request that doesn't match *any* registered entry — not because it was explicitly checked and rejected by a rule, but because no entry's matcher even accepted it — is still denied, which is the safe, secure-by-default behavior for any well-formed `authorizeHttpRequests` configuration.

```
invalidVersionSegment: GET /api/vX/orders
  entry 1 (regex, GET /api/v[0-9]+/orders): method OK, but "vX" fails digit requirement -> matcher=false
  entry 2 (Ant, DELETE /api/**):             method mismatch (GET != DELETE) -> matcher=false
  -> no entry matched -> DENIED (no matching rule) -- fail-closed default
```

## 7. Gotchas & takeaways

> **Gotcha:** mixing the legacy `AntPathRequestMatcher`/`MvcRequestMatcher` classes with the modern default `PathPatternRequestMatcher` in the same application (say, during an incremental migration) risks subtle disagreements between what the security rule considers a match and what Spring MVC's own routing considers a match for the exact same URL, precisely the class of bug the unified `PathPatternRequestMatcher` was introduced to eliminate — prefer migrating consistently to the modern default rather than mixing matcher implementations.

- `requestMatchers`'s plain string overload now uses `PathPatternRequestMatcher`, sharing the same underlying pattern engine as Spring MVC's own routing — the current recommended default for essentially all path-based matching needs.
- Regex matchers are reserved for the relatively rare case where Ant-style wildcard syntax cannot express a needed constraint, such as requiring a path segment to contain only digits.
- Method-aware matching (pairing an `HttpMethod` with a path) lets the same URL be governed by entirely different rules depending on the HTTP verb, essential for REST APIs distinguishing read from write access.
- A request matching no registered matcher at all is denied by default, not silently allowed — this fail-closed behavior should be understood and relied upon as the correct, safe default, not treated as a surprising edge case.
