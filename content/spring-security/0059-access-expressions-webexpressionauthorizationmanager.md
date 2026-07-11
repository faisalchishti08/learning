---
card: spring-security
gi: 59
slug: access-expressions-webexpressionauthorizationmanager
title: "Access expressions & WebExpressionAuthorizationManager"
---

## 1. What it is

`WebExpressionAuthorizationManager` is the `AuthorizationManager` implementation that evaluates a Spring Expression Language (SpEL) string against the current request, exposing built-in variables like `authentication` (the current `Authentication`), `request` (the `HttpServletRequest`), and functions like `hasRole(...)`/`hasAuthority(...)` directly inside the expression — reached via `.access(new WebExpressionAuthorizationManager("..."))` when a rule needs logic beyond what the fluent `hasRole`/`hasAuthority` convenience methods alone can express.

```java
http.authorizeHttpRequests(auth -> auth
        .requestMatchers("/api/orders/**").access(new WebExpressionAuthorizationManager(
                "hasRole('ADMIN') or (hasRole('USER') and request.method == 'GET')"))
        .requestMatchers("/internal/**").access(new WebExpressionAuthorizationManager(
                "hasIpAddress('10.0.0.0/8')"))
);
```

## 2. Why & when

`hasRole`/`hasAuthority`/`hasAnyRole` each express exactly one kind of check, and combining several of them with boolean logic (this role *or* that authority, but only for a specific HTTP method, or only from a specific IP range) isn't directly expressible through the fluent DSL's chained method calls alone — a SpEL expression string, evaluated by `WebExpressionAuthorizationManager`, fills this gap by letting arbitrary boolean logic reference the request's own properties (method, remote address) alongside the usual authority checks, all in one self-contained expression string.

Reach for `WebExpressionAuthorizationManager` (an access expression) when:

- Combining multiple conditions with boolean logic (`and`/`or`/`not`) that the fluent DSL's separate rule methods can't express as a single composed condition.
- Referencing request properties directly — the HTTP method, the remote IP address (via `hasIpAddress(...)`), or a custom request attribute — as part of the access decision, not just the caller's authorities.
- Prefer a custom `AuthorizationManager` (from the earlier card) instead when the logic is complex enough that a SpEL string becomes hard to read or test — expressions are best suited to conditions that remain reasonably short and legible as a single line; anything more elaborate is usually clearer as compiled Java code.

## 3. Core concept

```
 WebExpressionAuthorizationManager("hasRole('ADMIN') or (hasRole('USER') and request.method == 'GET')")

 evaluated PER REQUEST, with these variables/functions available inside the expression:
   authentication          -- the current Authentication object
   request                 -- the current HttpServletRequest (request.method, request.remoteAddr, ...)
   hasRole('X')             -- SAME check as the fluent hasRole("X") DSL method
   hasAuthority('X')         -- SAME check as the fluent hasAuthority("X") DSL method
   hasAnyRole('X','Y')       -- SAME check as the fluent method
   hasIpAddress('10.0.0.0/8') -- checks request.remoteAddr against a CIDR range
   permitAll / denyAll       -- literal TRUE / FALSE
```

The expression string is parsed once and evaluated fresh for every incoming request against that request's own specific `authentication` and `request` values.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A SpEL expression string combining hasRole ADMIN or hasRole USER and request method equals GET is evaluated per request against the current authentication and request object producing a single boolean granted or denied decision">
  <rect x="15" y="55" width="300" height="60" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="165" y="78" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">"hasRole('ADMIN') or</text>
  <text x="165" y="91" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">(hasRole('USER') and request.method=='GET')"</text>

  <rect x="360" y="55" width="130" height="60" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.4"/>
  <text x="425" y="80" fill="#79c0ff" font-size="7.5" text-anchor="middle" font-family="sans-serif">SpEL</text>
  <text x="425" y="93" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">evaluator</text>

  <rect x="530" y="55" width="95" height="60" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="577" y="90" fill="#6db33f" font-size="7.5" text-anchor="middle" font-family="sans-serif">true/false</text>

  <defs><marker id="a59" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
  <line x1="315" y1="85" x2="360" y2="85" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a59)"/>
  <line x1="490" y1="85" x2="530" y2="85" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a59)"/>
</svg>

One expression string, re-evaluated per request against that request's own authentication and method.

## 5. Runnable example

The scenario: implement a small SpEL-style expression evaluator supporting the core functions and operators, run it against several requests to show combined role/method logic in action, then add IP-based matching for an internal-network-only rule.

### Level 1 — Basic

A minimal expression-style check combining `hasRole` and a request-method condition, evaluated as plain Java (standing in for a real SpEL parser).

```java
import java.util.*;

public class AccessExpressionsLevel1 {
    record Request(String method, Set<String> authorities) {}

    static boolean hasRole(Request request, String role) { return request.authorities().contains("ROLE_" + role); }

    // models: "hasRole('ADMIN') or (hasRole('USER') and request.method == 'GET')"
    static boolean evaluateExpression(Request request) {
        return hasRole(request, "ADMIN") || (hasRole(request, "USER") && request.method().equals("GET"));
    }

    public static void main(String[] args) {
        Request adminPost = new Request("POST", Set.of("ROLE_ADMIN"));
        Request userGet = new Request("GET", Set.of("ROLE_USER"));
        Request userPost = new Request("POST", Set.of("ROLE_USER"));

        System.out.println("admin POST: " + evaluateExpression(adminPost));
        System.out.println("regular user GET: " + evaluateExpression(userGet));
        System.out.println("regular user POST: " + evaluateExpression(userPost));
    }
}
```

How to run: `java AccessExpressionsLevel1.java`

An admin is granted regardless of HTTP method (the `hasRole(request, "ADMIN")` half alone suffices); a regular user is granted only for `GET` requests, since the second half of the `||` additionally requires `request.method().equals("GET")` — a `POST` from the same regular user is correctly denied, since neither half of the combined condition is satisfied.

### Level 2 — Intermediate

Add IP-range matching, modeling `hasIpAddress(...)` for an internal-network-only access rule.

```java
import java.util.*;

public class AccessExpressionsLevel2 {
    record Request(String remoteAddress, Set<String> authorities) {}

    static boolean hasRole(Request request, String role) { return request.authorities().contains("ROLE_" + role); }

    // simplified CIDR check: only supports the common /8 case for clarity, comparing the first IP octet
    static boolean hasIpAddress(Request request, String cidr) {
        String[] parts = cidr.split("/");
        String networkAddress = parts[0];
        int prefixLength = Integer.parseInt(parts[1]);
        if (prefixLength != 8) throw new UnsupportedOperationException("this simplified check only supports /8");
        String networkFirstOctet = networkAddress.split("\\.")[0];
        String requestFirstOctet = request.remoteAddress().split("\\.")[0];
        return networkFirstOctet.equals(requestFirstOctet);
    }

    // models: "hasIpAddress('10.0.0.0/8')"
    static boolean evaluateExpression(Request request) {
        return hasIpAddress(request, "10.0.0.0/8");
    }

    public static void main(String[] args) {
        Request internalRequest = new Request("10.5.3.12", Set.of());
        Request externalRequest = new Request("203.0.113.50", Set.of());

        System.out.println("internal (10.x.x.x): " + evaluateExpression(internalRequest));
        System.out.println("external (203.x.x.x): " + evaluateExpression(externalRequest));
    }
}
```

How to run: `java AccessExpressionsLevel2.java`

`hasIpAddress` compares the request's remote address's first octet against the CIDR network's first octet — `10.5.3.12` matches `10.0.0.0/8`'s range (both start with `10`), while `203.0.113.50` does not, correctly distinguishing internal from external traffic purely by source address, entirely independent of any authority the caller might hold.

### Level 3 — Advanced

Combine role-based, method-based, and IP-based conditions into one realistic multi-part expression, evaluated against several genuinely different request profiles.

```java
import java.util.*;

public class AccessExpressionsLevel3 {
    record Request(String method, String remoteAddress, Set<String> authorities) {}

    static boolean hasRole(Request r, String role) { return r.authorities().contains("ROLE_" + role); }

    static boolean hasIpAddress(Request r, String cidr) {
        String networkFirstOctet = cidr.split("/")[0].split("\\.")[0];
        String requestFirstOctet = r.remoteAddress().split("\\.")[0];
        return networkFirstOctet.equals(requestFirstOctet);
    }

    // models: "hasRole('ADMIN') or (hasIpAddress('10.0.0.0/8') and request.method == 'GET')"
    static boolean evaluateExpression(Request r) {
        return hasRole(r, "ADMIN") || (hasIpAddress(r, "10.0.0.0/8") && r.method().equals("GET"));
    }

    public static void main(String[] args) {
        Request externalAdmin = new Request("DELETE", "203.0.113.50", Set.of("ROLE_ADMIN"));
        Request internalReaderGet = new Request("GET", "10.5.3.12", Set.of());
        Request internalReaderPost = new Request("POST", "10.5.3.12", Set.of());
        Request externalAnonymousGet = new Request("GET", "203.0.113.50", Set.of());

        for (Request r : List.of(externalAdmin, internalReaderGet, internalReaderPost, externalAnonymousGet)) {
            System.out.println(r.method() + " from " + r.remoteAddress() + " (" + r.authorities() + "): "
                    + evaluateExpression(r));
        }
    }
}
```

How to run: `java AccessExpressionsLevel3.java`

`externalAdmin` is granted purely via the `ROLE_ADMIN` half, regardless of both method and IP; `internalReaderGet` is granted via the second half, since it's both from the internal network *and* a `GET`; `internalReaderPost` is denied, since despite being internal, it's a `POST`, failing the method condition; `externalAnonymousGet` is denied, since despite being a `GET`, it's from an external IP, failing the network condition — four requests, four different combinations of the same three underlying conditions, each producing the logically correct outcome.

## 6. Walkthrough

Trace `evaluateExpression(internalReaderPost)` from Level 3.

1. `hasRole(internalReaderPost, "ADMIN")` checks whether `internalReaderPost.authorities()` (an empty set) contains `"ROLE_ADMIN"` — it does not, so this returns `false`.
2. Because the left side of the `||` returned `false`, Java evaluates the right side: `hasIpAddress(internalReaderPost, "10.0.0.0/8") && internalReaderPost.method().equals("GET")`.
3. `hasIpAddress` extracts `"10.0.0.0/8"`'s network first octet (`"10"`) and `internalReaderPost.remoteAddress()`'s first octet (from `"10.5.3.12"`, that's `"10"`) — these are equal, so `hasIpAddress` returns `true`.
4. Since the left side of this inner `&&` is `true`, Java evaluates the right side: `internalReaderPost.method().equals("GET")` checks `"POST".equals("GET")`, which is `false`.
5. The inner `&&` is `true && false`, i.e. `false`; the outer `||` is `false || false`, i.e. `false` — `evaluateExpression` returns `false`, correctly denying this request: it's genuinely from the internal network, but the `POST` method fails the second condition's method requirement, and it holds no `ROLE_ADMIN` authority to satisfy the first condition instead.

```
internalReaderPost: method=POST, remoteAddress=10.5.3.12, authorities={}
  hasRole(ADMIN)                        -> false (no ROLE_ADMIN authority)
  hasIpAddress(10.0.0.0/8)              -> true  (10.x matches 10.0.0.0/8)
  request.method == 'GET'               -> false (it's POST, not GET)
  (true && false) = false; (false || false) = false -> DENIED
```

## 7. Gotchas & takeaways

> **Gotcha:** SpEL expression strings are not type-checked or validated at compile time the way regular Java code is — a typo in a function name (`hasRolle` instead of `hasRole`) or a malformed boolean expression typically only surfaces as a runtime error (or, worse, an always-false or always-true condition) the first time that specific rule is actually evaluated against a real request, potentially well after the application has been deployed. Write integration tests specifically exercising each access expression's branches to catch this class of mistake early.

- `WebExpressionAuthorizationManager` evaluates a SpEL string against the current request, giving access to `hasRole`/`hasAuthority`/`hasAnyRole`, request properties (`request.method`, `request.remoteAddr`), and `hasIpAddress(...)` all within one composable boolean expression.
- Reach for an access expression specifically when combining multiple conditions with boolean logic that the fluent DSL's separate, chained rule methods can't express as one condition.
- For conditions complex enough that the SpEL string becomes hard to read, prefer a custom `AuthorizationManager` (from the earlier card) implemented as compiled, testable Java code instead.
- Because expression strings aren't compile-time checked, dedicated tests exercising each branch of a nontrivial access expression are the practical safeguard against silent typos or logic errors.
